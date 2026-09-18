from io import BytesIO
from pathlib import Path
import os
import re
from uuid import uuid4

import cv2
import numpy as np
import pytesseract
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw

app = FastAPI(title="DataGhost API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

DESTINATIONS = {"linkedin", "github", "job_application", "email", "public_website"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
PII_PATTERNS = {
    "EMAIL": (r"[\w.+-]+@[\w-]+\.[\w.-]+", "MEDIUM", "Email address exposed in the uploaded file"),
    "PHONE": (r"(?<!\d)(?:\+91[-\s]?)?[6-9]\d{9}(?!\d)", "HIGH", "Phone number exposed in the uploaded file"),
    "CARD_NUMBER": (r"(?<!\d)(?:\d[ -]?){15}\d(?!\d)", "CRITICAL", "Card-number-shaped value exposed in the uploaded file"),
}
METADATA_TYPES = {"GPS_METADATA", "CAPTURE_TIME", "DEVICE_METADATA"}
REDACTABLE_TYPES = set(PII_PATTERNS) | METADATA_TYPES

WINDOWS_TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
SANITIZED_DIR = Path(__file__).parent.parent / "temp" / "sanitized"
SANITIZED_DIR.mkdir(parents=True, exist_ok=True)
if WINDOWS_TESSERACT.exists():
    pytesseract.pytesseract.tesseract_cmd = str(WINDOWS_TESSERACT)


def mask_value(kind: str, value: str) -> str:
    if kind == "EMAIL":
        name, domain = value.split("@", 1)
        return f"{name[:1]}***@{domain}"
    return f"***{value[-4:]}"


def find_pii(text: str) -> list[dict[str, str]]:
    findings = []
    for kind, (pattern, severity, reason) in PII_PATTERNS.items():
        for match in re.finditer(pattern, text):
            findings.append(
                {"type": kind, "value": mask_value(kind, match.group()), "severity": severity, "reason": reason}
            )
    return findings


def has_qr_code(content: bytes) -> bool:
    image = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return False
    detected, _ = cv2.QRCodeDetector().detect(image)
    return bool(detected)


def find_metadata(content: bytes) -> list[dict[str, str]]:
    exif = Image.open(BytesIO(content)).getexif()
    if not exif:
        return []

    findings = []
    if exif.get(34853):
        findings.append(
            {
                "type": "GPS_METADATA",
                "value": "GPS location present",
                "severity": "CRITICAL",
                "reason": "Location metadata can reveal where the image was captured",
            }
        )
    if exif.get(306) or exif.get_ifd(34665).get(36867):
        findings.append(
            {
                "type": "CAPTURE_TIME",
                "value": "Capture time present",
                "severity": "REVIEW",
                "reason": "Capture time can reveal personal activity patterns",
            }
        )
    if exif.get(271) or exif.get(272):
        findings.append(
            {
                "type": "DEVICE_METADATA",
                "value": "Device information present",
                "severity": "REVIEW",
                "reason": "Device metadata can identify the camera or phone used",
            }
        )
    return findings


def apply_context(findings: list[dict[str, str]], destination: str) -> None:
    for finding in findings:
        kind = finding["type"]
        if destination == "job_application" and kind in {"EMAIL", "PHONE"}:
            finding["severity"] = "LOW"
            finding["reason"] = "Expected for a job application; include it only when necessary"
        elif destination in {"github", "public_website", "linkedin"} and kind == "EMAIL":
            finding["severity"] = "REVIEW"
            finding["reason"] = "Email address may be harvested from a public destination"


def risk_score(findings: list[dict[str, str]]) -> tuple[int, str]:
    points = {"LOW": 5, "REVIEW": 10, "MEDIUM": 20, "HIGH": 35, "CRITICAL": 50}
    score = min(100, sum(points[finding["severity"]] for finding in findings))
    if score >= 80:
        return score, "CRITICAL"
    if score >= 50:
        return score, "HIGH"
    if score >= 25:
        return score, "MEDIUM"
    return score, "LOW"


def adversary_view(findings: list[dict[str, str]]) -> dict[str, list[str]]:
    views = {"stranger": [], "scraper": [], "scammer": []}
    labels = {"EMAIL": "email address", "PHONE": "phone number", "CARD_NUMBER": "card number"}
    for kind in {finding["type"] for finding in findings}:
        if kind in {"EMAIL", "PHONE", "CARD_NUMBER"}:
            views["stranger"].append(f"A viewer can see an {labels[kind]}" if kind == "EMAIL" else f"A viewer can see a {labels[kind]}")
            views["scraper"].append(f"Automated systems can collect the {labels[kind]}")
        if kind in {"EMAIL", "PHONE", "CARD_NUMBER", "GPS_METADATA", "CAPTURE_TIME"}:
            views["scammer"].append(f"The {labels.get(kind, kind.lower().replace('_', ' '))} can increase social-engineering risk")
        if kind == "QR_CODE":
            views["stranger"].append("A viewer can scan the QR code")
            views["scraper"].append("Automated systems can decode the QR code")
        if kind == "GPS_METADATA":
            views["stranger"].append("A viewer may infer where the image was captured")
        if kind == "DEVICE_METADATA":
            views["scraper"].append("Automated systems can collect device metadata")
    return views


def redact_text(text: str, types: set[str]) -> str:
    for kind, (pattern, _, _) in PII_PATTERNS.items():
        if kind in types:
            text = re.sub(pattern, f"[REDACTED_{kind}]", text)
    return text


def redact_image(content: bytes, types: set[str]) -> tuple[Image.Image, set[str]]:
    image = Image.open(BytesIO(content)).convert("RGB")
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    lines: dict[tuple[int, int, int], list[tuple[int, int, int, str]]] = {}
    for index, token in enumerate(data["text"]):
        token = token.strip()
        if token:
            key = (data["block_num"][index], data["par_num"][index], data["line_num"][index])
            lines.setdefault(key, []).append((index, 0, 0, token))

    boxes: set[int] = set()
    detected_types: set[str] = set()
    for tokens in lines.values():
        position = 0
        positioned = []
        for index, _, _, token in tokens:
            positioned.append((index, position, position + len(token)))
            position += len(token) + 1
        text = " ".join(token[3] for token in tokens)
        for kind, (pattern, _, _) in PII_PATTERNS.items():
            if kind in types:
                for match in re.finditer(pattern, text):
                    detected_types.add(kind)
                    boxes.update(index for index, start, end in positioned if start < match.end() and end > match.start())

    draw = ImageDraw.Draw(image)
    for index in boxes:
        left, top = data["left"][index], data["top"][index]
        right, bottom = left + data["width"][index], top + data["height"][index]
        draw.rectangle((left - 2, top - 2, right + 2, bottom + 2), fill="black")
    return image, detected_types


@app.get("/")
def root():
    return {"name": "DataGhost API", "status": "running"}


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "dataghost-backend", "version": "0.1.0"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...), destination: str = Form(...)):
    if destination not in DESTINATIONS:
        raise HTTPException(
            status_code=422,
            detail=f"destination must be one of: {', '.join(sorted(DESTINATIONS))}",
        )

    content = await file.read()
    suffix = Path(file.filename or "").suffix.lower()
    extracted_text = ""

    if suffix == ".txt":
        extracted_text = content.decode("utf-8", errors="replace")
    elif suffix in IMAGE_SUFFIXES:
        extracted_text = pytesseract.image_to_string(Image.open(BytesIO(content))).strip()

    findings = find_pii(extracted_text)
    if suffix in IMAGE_SUFFIXES and has_qr_code(content):
        findings.append(
            {
                "type": "QR_CODE",
                "value": "QR code detected",
                "severity": "REVIEW",
                "reason": "QR codes can contain shareable identifiers or links",
            }
        )
    if suffix in IMAGE_SUFFIXES:
        findings.extend(find_metadata(content))
    apply_context(findings, destination)
    score, level = risk_score(findings)

    return {
        "filename": file.filename,
        "destination": destination,
        "extracted_text": extracted_text,
        "risk_score": score,
        "risk_level": level,
        "findings": findings,
        "adversary_view": adversary_view(findings),
    }


@app.post("/api/redact")
async def redact(file: UploadFile = File(...), types: list[str] | None = Form(None)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix != ".txt" and suffix not in IMAGE_SUFFIXES:
        raise HTTPException(status_code=422, detail="Smart Redaction supports .txt and image files")

    selected_types = set(types or REDACTABLE_TYPES)
    invalid_types = selected_types - REDACTABLE_TYPES
    if invalid_types:
        raise HTTPException(status_code=422, detail=f"Unknown redaction types: {', '.join(sorted(invalid_types))}")

    sanitized_id = uuid4().hex
    content = await file.read()
    output_path = SANITIZED_DIR / f"{sanitized_id}{suffix}"
    if suffix == ".txt":
        output_path.write_text(redact_text(content.decode("utf-8", errors="replace"), selected_types), encoding="utf-8")
        redacted_types = sorted(selected_types & PII_PATTERNS.keys())
    else:
        image, detected_types = redact_image(content, selected_types)
        image.save(output_path)
        redacted_types = sorted(detected_types | (selected_types & METADATA_TYPES))
    return {
        "filename": f"sanitized_{file.filename}",
        "redacted_types": redacted_types,
        "download_url": f"/api/sanitized/{sanitized_id}",
    }


@app.get("/api/sanitized/{sanitized_id}")
def download_sanitized_file(sanitized_id: str):
    if not re.fullmatch(r"[0-9a-f]{32}", sanitized_id):
        raise HTTPException(status_code=404, detail="Sanitized file not found")
    output_path = next(SANITIZED_DIR.glob(f"{sanitized_id}.*"), None)
    if output_path is None:
        raise HTTPException(status_code=404, detail="Sanitized file not found")
    return FileResponse(output_path, filename=f"sanitized_{sanitized_id}{output_path.suffix}")
