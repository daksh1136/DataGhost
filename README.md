\# 👻 DataGhost



\### AI-Powered Privacy Guardian



> \*\*See what your files reveal before the internet does.\*\*



DataGhost analyzes files before they are shared online, detects potentially sensitive information, evaluates privacy risk based on the intended sharing destination, and helps users create a safer sanitized copy.



Built for \*\*Aether HackConquest 2026\*\*.



\---



\## 🚨 The Problem



A harmless-looking resume, certificate, screenshot, PDF, or image can expose more information than users realize.



Files may reveal:



\- Email addresses

\- Phone numbers

\- Home addresses

\- Student/document IDs

\- QR codes

\- GPS information

\- Device information

\- EXIF and file metadata

\- Other machine-readable information



Traditional redaction assumes users already know what needs to be hidden.



\*\*DataGhost finds the exposure first.\*\*



\---



\## 💡 How It Works



```text

Upload File

&#x20;   ↓

Choose Sharing Destination

&#x20;   ↓

Privacy Analysis

&#x20;   ↓

Detect Sensitive Information

&#x20;   ↓

Context-Aware Risk Engine

&#x20;   ↓

Privacy Risk Score

&#x20;   ↓

Adversary View

&#x20;   ↓

Smart Redact

&#x20;   ↓

Safer Export

```



\---



\## 🧠 Context-Aware Privacy



Privacy risk depends on \*\*where information is being shared\*\*.



| Information | Public GitHub | Job Application |

|---|---|---|

| Name | Acceptable | Expected |

| Email | Review | Expected |

| Phone | High Risk | Expected |

| Full Address | Critical | Review |



Instead of only asking:



> Does this file contain PII?



DataGhost asks:



> \*\*What does this file expose, where are you sharing it, and what should you protect before you do?\*\*



\---



\## ✨ Core Features



\### 🔍 Privacy Analysis

Detects potentially sensitive information inside uploaded files.



\### 📊 Privacy Risk Score

Produces an explainable risk score and risk level based on detected exposure.



\### 🧠 Context-Aware Risk

Changes privacy assessment according to the intended sharing destination.



\### 👁 Adversary View

Provides defensive exposure analysis through:



\- \*\*Stranger View\*\* — what an ordinary viewer can see

\- \*\*Scraper View\*\* — what automated systems could collect

\- \*\*Scammer View\*\* — information that could increase phishing or social-engineering risk



DataGhost does not perform attacks.



\### 🛡 Smart Redact

Creates a sanitized version of supported files with selected sensitive information masked or removed.



\### 🕵 Deep File Inspection

Designed to analyze visible content as well as OCR text, QR codes and file metadata.



\---



\## 🏗 Architecture



```text

User

&#x20; │

&#x20; ▼

Next.js Frontend

&#x20; │

&#x20; │ POST /api/analyze

&#x20; ▼

FastAPI Backend

&#x20; │

&#x20; ├── File Validation

&#x20; ├── Text Extraction / OCR

&#x20; ├── PII Detection

&#x20; ├── QR Inspection

&#x20; └── Metadata / EXIF

&#x20;         │

&#x20;         ▼

&#x20;  Context Engine

&#x20;         │

&#x20;         ▼

&#x20;     Risk Engine

&#x20;         │

&#x20;   ┌─────┼──────────┐

&#x20;   ▼     ▼          ▼

Findings Score  Adversary View

&#x20;         │

&#x20;         ▼

&#x20;   Smart Redaction

&#x20;         │

&#x20;         ▼

&#x20;   Sanitized Output

```



See \[Architecture Documentation](docs/architecture.md) for more details.



\---



\## 🛠 Tech Stack



\*\*Frontend\*\*

\- Next.js

\- React

\- TypeScript



\*\*Backend\*\*

\- Python

\- FastAPI

\- Uvicorn



\*\*Privacy Intelligence\*\*

\- Text extraction / OCR

\- PII detection

\- Pattern matching

\- Context-aware privacy rules

\- Privacy risk scoring

\- QR / metadata inspection



\---



\## 📁 Project Structure



```text

DataGhost/

├── backend/

│   ├── app/

│   │   └── main.py

│   ├── Dockerfile

│   └── requirements.txt

├── frontend/

│   ├── app/

│   └── package.json

├── docs/

│   ├── architecture.md

│   └── demo-guide.md

├── .env.example

├── .gitignore

└── README.md

```



\---



\## 🚀 Run Locally



\### Backend



```powershell

cd backend



py -m venv .venv

.\\.venv\\Scripts\\Activate.ps1



pip install -r requirements.txt



python -m uvicorn app.main:app --reload --port 8000

```



Backend:



```text

http://127.0.0.1:8000

```



Swagger:



```text

http://127.0.0.1:8000/docs

```



\### Frontend



Open another PowerShell terminal:



```powershell

cd frontend

npm install

npm run dev

```



Open:



```text

http://localhost:3000

```



\---



\## 🧪 Example



Synthetic test document:



```text

Aarav Test

Email: aarav.test@example.com

Phone: +91 9876543210

Student ID: GU-TEST-2026-001

```



Example findings when sharing publicly:



```text

EMAIL → REVIEW

PHONE → HIGH

```



DataGhost masks sensitive values returned to the interface.



\---



\## 🔐 Privacy Principles



DataGhost is designed around:



\- Temporary file processing

\- Masked sensitive values

\- Defensive privacy analysis

\- User-controlled redaction

\- Minimal exposure of detected information



Use synthetic data when testing the prototype rather than real identity documents.



\---



\## 🎬 Hackathon Demo



```text

Upload synthetic document

&#x20;       ↓

Choose Public GitHub

&#x20;       ↓

Analyze Privacy

&#x20;       ↓

Review Exposures

&#x20;       ↓

Privacy Risk Score

&#x20;       ↓

Adversary View

&#x20;       ↓

Change Destination

&#x20;       ↓

Context-Aware Risk Changes

&#x20;       ↓

Smart Redact

&#x20;       ↓

Safer Export

```



See the \[Demo Guide](docs/demo-guide.md).



\---



\## 👥 Team



\*\*Daksh Sharma\*\*  

Backend · Privacy Engine · Integration · Deployment



\*\*Krish\*\*  

Frontend · UI/UX



\*\*Jigyasa Singh\*\*  

Testing · Quality Assurance



\---



\## 🗺 Roadmap



\- Improved address detection

\- Student/document ID detection

\- Enhanced OCR

\- Advanced QR inspection

\- EXIF/GPS inspection

\- PDF and image visual redaction

\- Browser extension

\- Mobile integration

\- Enterprise privacy/DLP integrations



\---



\## ⚠️ Disclaimer



DataGhost is a privacy-assistance prototype. Privacy Risk Scores are indicators designed to help users review potential exposure and are not guarantees of privacy or security.

