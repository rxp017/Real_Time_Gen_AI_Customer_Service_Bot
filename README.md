# Customer Service Bot: Controlled Updates and Multilingual Sessions

Based on the mentor's [GEN---AI-course/customer_service_chatbot_LLM](https://github.com/aslin72/GEN---AI-course/tree/main/GEN---AI-course/customer_service_chatbot_LLM). The original FAQ dataset is preserved in `dataset/dataset.csv`; the original bot functions remain under `src/`. This repository adds the shared API and tasks 1-6 around that workspace. The supported API uses the shared policy engine; direct operation of the old Streamlit/GooglePalm chain remains unverified. [Audit and remaining requirement gaps](docs/audit.md).

Task 3 adds structured ticket drafts, weighted priority, skill/capacity routing, business-time SLA warnings and escalation, runtime SLA changes, safe deduplication/grouping and masked handoff summaries. [Ticket API and configuration](docs/task3.md) · [Priority formula](docs/priority.md).

Task 2 adds authenticated uploads, a gate before content decoders, actual Tesseract/PDFium extraction with source regions, message conflict checks, real Gemini image-input support, background jobs/notifications, and Clock-driven byte deletion. [Upload API, install steps and actual evidence](docs/task2.md).

Task 1 is implemented against the shared SQLite/RAG foundation. Antigravity's original completion claim failed the source audit; critical API, grounding, injection, access, and runtime defects were repaired. Task 4's general semantic search remains incomplete.

Task 6 adds resource-driven en/hi/te/es recognition, entity preservation, corrections, multiple requests, and persistent owner-bound sessions. Unknown input asks clarification. See [user setup steps](docs/next_steps.md).

AI Studio configuration now uses live-verified gemini-2.5-flash and four free-tier-eligible model backups. The Google key was preserved, and blank role keys were generated locally. [Fallback design and actual provider evidence](docs/provider_fallback.md). Confirm the project's billing tier is Free; selecting eligible models does not force free billing.

- [Current verification and command output](docs/README.md)
- [Audit findings](docs/verification.md)
- [Task 1 requirements](docs/tasks/T1.md)
- [Task 6 requirements](docs/tasks/T6.md)
- [Task 2 requirements](docs/tasks/T2.md)
- [Requirements trace matrix](docs/RTM.md)
- [Known limits](docs/known_gaps.md)
- [Original training baseline](docs/baseline.md)

## Fresh Windows checkout installation

Run the following from the cloned repository root in PowerShell. This creates an isolated Python 3.11.9 runtime from python.org; it does not require the ignored runtime from the author's machine or change system Python. Network access is required for installation. Existing `.env` files are preserved.

```powershell
New-Item -ItemType Directory -Force .runtime/python311 | Out-Null
Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip -OutFile .runtime/python311.zip
Expand-Archive -LiteralPath .runtime/python311.zip -DestinationPath .runtime/python311 -Force
Set-Content -LiteralPath .runtime/python311/python311._pth -Encoding ascii -Value @('python311.zip', '.', 'import site')
Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile .runtime/get-pip.py
.\.runtime\python311\python.exe .runtime/get-pip.py --no-warn-script-location
.\.runtime\python311\python.exe -m pip install --no-warn-script-location -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
.\.runtime\python311\python.exe --version
.\.runtime\python311\python.exe -m pip check
```

OCR is required for Task 2's extraction and full tests. Install the Windows Tesseract prerequisite if absent, then download the four configured language packs from the official tagged resources:

```powershell
if (-not (Test-Path -LiteralPath 'C:/Program Files/Tesseract-OCR/tesseract.exe')) {
    winget install --id UB-Mannheim.TesseractOCR --source winget --exact --version 5.4.0.20240606 --silent --accept-package-agreements --accept-source-agreements
}
New-Item -ItemType Directory -Force .runtime/tessdata | Out-Null
foreach ($code in @('eng','hin','tel','spa')) {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/$code.traineddata" -OutFile ".runtime/tessdata/$code.traineddata"
}
.\.runtime\python311\python.exe -X utf8 scripts/check_ocr.py
```

Alternatively, use an installed Python 3.11 with `py -3.11 -m venv .venv` and install `requirements.txt` with that environment's interpreter. Substitute it for the portable interpreter in commands below. Run all commands from the repository root. The archived upstream manifest is retained for audit, not used by the supported installer.

## Run locally

For live queries, fill the copied `.env` with your own `GOOGLE_API_KEY`, model and private role keys. Empty credentials permit offline tests and server startup, but do not provide live generation or authenticated management access. Run from the project root:

```powershell
.\.runtime\python311\python.exe -m uvicorn app.chatbot:app --host 127.0.0.1 --port 8000
```

Put complete policy JSON files in data/inbox/. Use the metadata schema shown by data/sample_docs/policy_v2_refund.json. The ingestion API scans this local directory; it accepts no arbitrary server file path.

## Workflow

1. POST /knowledge/ingest with an ingestor/admin x-api-key creates a candidate and reports skipped/quarantined files.
2. POST /knowledge/{version}/quality with an approver/admin key measures ACTIVE and candidate on data/golden/.
3. POST /knowledge/{version}/approve approves a passing candidate.
4. POST /knowledge/{version}/activate with an operator/admin key activates only in the configured window. The worker also activates held approved candidates inside the window.
5. POST /knowledge/{version}/rollback with an operator/admin key atomically restores an eligible snapshot.
6. GET /knowledge or /knowledge/{version} requires view permission and returns status/reports, not document content.

POST /knowledge/schedule configures a daily inbox job. Startup also schedules it when API_KEY_ADMIN is set. Retry offsets are +15/+30/+60 minutes from the first failure, followed by a durable FAILED alert. Default maintenance is Sunday 02:00-04:00 Asia/Kolkata. The worker checks activation health for five minutes and records automatic rollback reasons.

POST /query reads ACTIVE. With an empty store it refuses unsupported questions. The application uses the real configured provider; it never enables FakeLLM by default. The original training source is preserved under src/, and unavailable legacy/provider calls return 503.

Keep the returned session_id and send it on later /query calls. Each response includes per-message language/intent confidence, mixed-language flags, protected entities, request-specific context, clarification state, and session generation/transition. Use the same API key for that session. Sessions expire after configured 30-minute inactivity; returning within configured 24 hours restores a structured summary; later returns start a fresh generation. The window retains at least ten user/assistant messages.

Language support is configured by languages and conversation/thresholds/timings in config/default.yaml, with resources/languages/<code>.json. Add resources and a config entry to enable another language. Untranslated factual answers explicitly report their actual answer_language. This is bounded resource recognition and curated translation, not a general multilingual model.

## Offline verification

```powershell
.\.runtime\python311\python.exe -m pytest -q
.\.runtime\python311\python.exe -m ruff check .
.\.runtime\python311\python.exe scripts/demo_t1.py
.\.runtime\python311\python.exe scripts/demo_t4.py
.\.runtime\python311\python.exe -X utf8 scripts/evaluate_t6.py
.\.runtime\python311\python.exe -X utf8 scripts/check_ocr.py
.\.runtime\python311\python.exe -X utf8 scripts/demo_t2.py
```

The earlier policy/update demos use FakeClock/FakeLLM. Task 2's offline demo runs real local OCR/PDF extraction and explicitly disables vision; its optional manual live-vision script uses the real provider. No demo establishes broad customer-policy or vision accuracy. Alerts and upload notifications are local records; external notification delivery is not configured.
