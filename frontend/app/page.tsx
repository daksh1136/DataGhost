"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const destinations = [["linkedin", "LinkedIn"], ["github", "GitHub"], ["job_application", "Job application"], ["email", "Email"], ["public_website", "Public website"]] as const;
type Finding = { type: string; value: string; severity: string; reason: string };
type Analysis = { filename: string; destination: string; extracted_text: string; risk_score: number; risk_level: string; findings: Finding[]; adversary_view: Record<"stranger" | "scraper" | "scammer", string[]> };
const tones: Record<string, string> = { LOW: "tone-low", REVIEW: "tone-review", MEDIUM: "tone-medium", HIGH: "tone-high", CRITICAL: "tone-critical" };
const redactionKinds = ["EMAIL", "PHONE", "CARD_NUMBER", "GPS_METADATA", "CAPTURE_TIME", "DEVICE_METADATA"];

function ShieldMark() { return <span className="shield-mark">◈</span>; }

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [destination, setDestination] = useState("github");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [redacting, setRedacting] = useState(false);
  const [error, setError] = useState("");
  const [downloadUrl, setDownloadUrl] = useState("");
  const redactionTypes = useMemo(() => selectedTypes.filter((type) => redactionKinds.includes(type)), [selectedTypes]);

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null); setAnalysis(null); setSelectedTypes([]); setDownloadUrl(""); setError("");
  }
  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return setError("Choose a file before starting the privacy scan.");
    setLoading(true); setError(""); setDownloadUrl("");
    try {
      const body = new FormData(); body.append("file", file); body.append("destination", destination);
      const response = await fetch(`${API_URL}/api/analyze`, { method: "POST", body });
      if (!response.ok) throw new Error("The scan could not be completed. Make sure the backend is running.");
      const result: Analysis = await response.json(); setAnalysis(result); setSelectedTypes(result.findings.map((finding) => finding.type));
    } catch (caught) { setError(caught instanceof Error ? caught.message : "The scan could not be completed."); } finally { setLoading(false); }
  }
  async function redact() {
    if (!file || !redactionTypes.length) return;
    setRedacting(true); setError("");
    try {
      const body = new FormData(); body.append("file", file); redactionTypes.forEach((type) => body.append("types", type));
      const response = await fetch(`${API_URL}/api/redact`, { method: "POST", body });
      if (!response.ok) { const result = await response.json().catch(() => null); throw new Error(result?.detail ?? "Redaction could not be completed for this file."); }
      const result: { download_url: string } = await response.json(); setDownloadUrl(`${API_URL}${result.download_url}`);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Redaction could not be completed."); } finally { setRedacting(false); }
  }
  function toggleType(type: string) { setSelectedTypes((types) => types.includes(type) ? types.filter((item) => item !== type) : [...types, type]); }

  return <main className="shell">
    <nav className="nav"><a className="brand" href="#top"><ShieldMark /> DataGhost</a><span className="status"><i /> Privacy intelligence active</span></nav>
    <section className="hero" id="top"><p className="eyebrow">Pre-share privacy check</p><h1>Know what your files reveal<br /><em>before the internet does.</em></h1><p className="lede">Scan documents and images for exposed personal information, hidden metadata, and privacy risks—before sharing them.</p></section>
    <section className="workspace">
      <form className="scan-card" onSubmit={analyze}>
        <div className="card-heading"><span className="step">01</span><div><h2>Choose a file</h2><p>Images and text files are supported.</p></div></div>
        <label className={`drop-zone ${file ? "selected" : ""}`}><input type="file" accept=".txt,image/*" onChange={chooseFile} /><span className="upload-icon">↑</span><strong>{file ? file.name : "Drop a file here, or browse"}</strong><small>{file ? `${Math.max(1, Math.round(file.size / 1024))} KB ready to scan` : "PNG, JPG, WEBP, TIFF, BMP, or TXT"}</small></label>
        <div className="card-heading destination-heading"><span className="step">02</span><div><h2>Where are you sharing it?</h2><p>Risk changes with the audience.</p></div></div>
        <div className="destinations">{destinations.map(([value, label]) => <button className={destination === value ? "destination active" : "destination"} type="button" key={value} onClick={() => setDestination(value)}>{label}</button>)}</div>
        <button className="scan-button" disabled={loading} type="submit">{loading ? "Scanning file…" : "Scan privacy risk"}<span>→</span></button>{error && <p className="error">{error}</p>}
      </form>
      <aside className="promise-card"><div className="radar"><span /><span /><b>◌</b></div><p className="eyebrow">Your file stays yours</p><h2>Find the invisible exposure.</h2><ul><li>Context-aware risk</li><li>OCR + metadata scan</li><li>Defensive adversary view</li></ul></aside>
    </section>
    {analysis && <section className="results" aria-live="polite">
      <div className="results-head"><div><p className="eyebrow">Analysis complete</p><h2>Privacy report <span>for {analysis.filename}</span></h2></div><span className="destination-label">{destinations.find(([value]) => value === analysis.destination)?.[1]}</span></div>
      <div className="score-grid"><article className={`score-card ${tones[analysis.risk_level]}`}><p>Privacy risk</p><div className="score"><strong>{analysis.risk_score}</strong><span>/ 100</span></div><b>{analysis.risk_level} RISK</b><div className="meter"><i style={{ width: `${analysis.risk_score}%` }} /></div></article><article className="summary-card"><span className="summary-icon">⌁</span><div><p>Found</p><strong>{analysis.findings.length} privacy signal{analysis.findings.length === 1 ? "" : "s"}</strong><small>Review what is visible before sharing.</small></div></article></div>
      <div className="content-grid">
        <article className="panel findings"><div className="panel-title"><div><p className="eyebrow">Detected findings</p><h3>Control what gets shared</h3></div><span>{analysis.findings.length}</span></div>{analysis.findings.length ? <div className="finding-list">{analysis.findings.map((finding, index) => <button className={`finding ${selectedTypes.includes(finding.type) ? "checked" : ""}`} onClick={() => toggleType(finding.type)} type="button" key={`${finding.type}-${index}`}><span className="checkbox">{selectedTypes.includes(finding.type) ? "✓" : ""}</span><span className="finding-copy"><strong>{finding.type.replaceAll("_", " ")}</strong><small>{finding.value} · {finding.reason}</small></span><span className={`badge ${tones[finding.severity]}`}>{finding.severity}</span></button>)}</div> : <div className="empty">No detectable privacy signals found in this file.</div>}</article>
        <article className="panel adversary"><div><p className="eyebrow">Adversary view</p><h3>What could others learn?</h3></div><div className="view-list">{(["stranger", "scraper", "scammer"] as const).map((view) => <div className="view" key={view}><span>{view === "stranger" ? "◉" : view === "scraper" ? "⌘" : "△"}</span><div><b>{view} view</b><p>{analysis.adversary_view[view].length ? analysis.adversary_view[view].join(" ") : "No specific exposure identified."}</p></div></div>)}</div></article>
      </div>
      <section className="redact-card"><div><p className="eyebrow">Smart Redact</p><h3>Make a safer copy</h3><p>Selected sensitive text will be permanently masked in a new downloadable file.</p></div><div className="redact-action">{downloadUrl ? <a className="download-button" href={downloadUrl}>Download sanitized file <span>↓</span></a> : <button className="redact-button" disabled={!redactionTypes.length || redacting} onClick={redact}>{redacting ? "Creating safe copy…" : `Redact ${redactionTypes.length || "selected"} item${redactionTypes.length === 1 ? "" : "s"}`}<span>→</span></button>}<small>{file?.type.startsWith("image/") ? "Image redaction uses OCR text regions." : "Text redaction replaces detected values."}</small></div></section>
    </section>}
    <footer><ShieldMark /> DataGhost <span>•</span> Share with confidence.</footer>
  </main>;
}
