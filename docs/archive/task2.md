# Task 2 uploads

The supported FastAPI application now accepts PNG, JPEG and a conservative PDF subset through `POST /uploads`. It reuses shared SQLite, RBAC, Clock, masked audit, metrics, the prompt-injection detector, structural data boundaries, and LLMClient. The training source and existing chat/query flow remain in place.

## Safety and evidence

`app/upload_api.py:UploadBodyLimit` bounds the entire request before multipart parsing. `core/upload_gate.py` checks file size, declared MIME, extension, magic, PNG chunk CRCs/dimensions/exact expanded pixel length, JPEG framing/dimensions, PDF names/actions, page/object/pixel limits, stream lengths, filters and bounded inflation before content decoding. PDF name escapes, null whitespace and filter comments are checked; unsupported active or complex constructs fail closed. Original names and raw file/customer/OCR content are never logged. Queued bytes have an acceptance SHA-256; workers check it and rerun preflight before decoding.

Tesseract performs real OCR and returns TSV word confidence and pixel boxes. PDFium maps native text to actual character boxes in PDF points and rasterizes pages for OCR fallback/security checks. Native and OCR evidence are both scanned as untrusted data before fields or a model are used. Hidden native PDF instructions and raster-only injected PDF text are rejected. Native PDF lines carry exact-mapping confidence 1, not a claim of document authenticity.

`core/upload_fields.py` extracts only configured explicit source patterns for order ID, date, amount, product information and error code. Every field has value, confidence, source_region; missing values/regions are null with zero confidence. Multiple source values require clarification. Customer text cannot fill a missing document field. Comparison supports configured date/currency normalization, labelled values and bare order/date/currency mentions; conflicting values are shown explicitly. Supported formats/patterns can be edited in config; arbitrary invoice layouts or wording are not guaranteed.

Low image edge variance or low OCR confidence on text-bearing files requests a replacement. Sharp product images without substantive OCR text can still use vision; their missing OCR fields remain null. Product purpose is explicit. The existing Gemini 2.5 Flash adapter now accepts inline image bytes through LLMClient and restricts image fallback to configured vision-capable models. OCR/image text and the customer message are structurally isolated as data. If no usable model/key is configured, the result honestly says `cannot analyse`. Conflicts still ask for clarification in this case.

## API and lifecycle

- `POST /uploads`: multipart `file`, `customer_message`, `purpose` (`invoice` or `product`), `language` (default `en`), plus a private `x-api-key` with `upload:create` permission. Customer/support-agent roles have this permission; admin retains full permissions. Anonymous calls are rejected and audited.
- A fast job returns HTTP 200 with its terminal job state and result. A structural preflight rejection returns 422. Jobs start in queued, then running. Once the Clock budget reaches 30 seconds the API returns HTTP 202 with job id, current state and a background notification while processing continues. Queue/capacity/dependency failures are explicit.
- `GET /uploads/{id}`: the same authenticated owner retrieves state, notifications and the completed result. Other owners receive 404 and a security audit event. Inspect the job `status` and nested `result.status`; completed processing may request clarification/replacement or report a rejection. A job resource response is not a promise that the document passed validation.
- SQLite persists queued/running/done/failed states, result and notifications. Pending jobs recover on startup. Completion notifications and results are delivered by owner-bound polling; no external push/email destination is configured.
- Files live under `.uploads/` as generated identifiers. Expiry is recorded from acceptance using the configured retention (default 24 hours). The Clock-driven application worker purges expired originals and stored customer/result content, before maintenance work, and retrieval also checks expiry. In-flight results cannot resurrect an expired upload. Minimal id/owner/status/expiry tombstones remain. Tests assert actual disk bytes disappear, including through the application worker during a maintenance outage.

Thresholds, formats, roles, languages, native-operation timeouts and retention settings are in `config/default.yaml`. Model selection, field patterns and processing thresholds are reread for requests. Pool size/storage-root changes require restarting the application; accepted files keep their recorded expiry. Native library/CLI timeouts bound their operations; application deadlines and retention use Clock.

## Installed runtime and reproducible OCR check

Verified on this Windows machine: Python 3.11.9, Tesseract v5.4.0.20240606, Pillow 12.3.0, pypdfium2 5.14.0, python-multipart 0.0.32. Python versions are pinned in requirements.txt. PyMuPDF was removed after Windows application control blocked its native module; PDFium passed actual extraction/rendering checks. No Windows security setting was disabled.

For another Windows machine, from the repository root:

```powershell
winget install --id UB-Mannheim.TesseractOCR --source winget --exact --version 5.4.0.20240606 --silent --accept-package-agreements --accept-source-agreements
New-Item -ItemType Directory -Force .runtime/tessdata | Out-Null
foreach ($code in @('eng','hin','tel','spa')) {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/$code.traineddata" -OutFile ".runtime/tessdata/$code.traineddata"
}
$env:TESSERACT_CMD = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
& $env:TESSERACT_CMD --version
& $env:TESSERACT_CMD --tessdata-dir .runtime/tessdata --list-langs
.\.runtime\python311\python.exe -m pip install -r requirements.txt
.\.runtime\python311\python.exe -X utf8 scripts/check_ocr.py
```

For a normal Python 3.11 virtual environment, substitute its interpreter for the portable runtime path. Set `TESSERACT_CMD` or `uploads.ocr.executable` if the installer uses another location. Traineddata files belong in the configured `uploads.ocr.tessdata_directory`. TSV output is enabled with verified Tesseract parameters, so the local tessdata directory does not need copied CLI output-configuration files.

The Windows installer SHA-256 was verified against winget metadata: `c885fff6998e0608ba4bb8ab51436e1c6775c2bafc2559a19b423e18678b60c9`. Language resources use the official tessdata_fast 4.1.0 tag; actual downloaded hashes are in `verification/task2-language-packs.json`.

Executed command: `.\.runtime\python311\python.exe -X utf8 scripts/check_ocr.py`. Its actual [output](verification/task2-ocr-installation.json) reports version `tesseract v5.4.0.20240606`, available `eng, hin, spa, tel`, and `missing_languages: []`. These English invoice tests do not establish OCR accuracy on other languages.

Primary installation/API references: [Tesseract installation](https://tesseract-ocr.github.io/tessdoc/Installation.html), [Tesseract CLI/TSV](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html), [official language data](https://github.com/tesseract-ocr/tessdata_fast/tree/4.1.0), [PDFium API and thread restrictions](https://pypdfium2.readthedocs.io/en/stable/python_api.html), [Pillow decompression security](https://pillow.readthedocs.io/en/stable/handbook/security.html), [Gemini image input](https://ai.google.dev/gemini-api/docs/image-understanding), [Gemini 2.5 Flash supported inputs](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash).

## Real fixture and provider evidence

`tests/fixtures/task2/` contains actual encoded clean, blurred, mismatched, missing-field, injected, hidden-injected, malformed, scanned-PDF and product files. `scripts/create_t2_fixtures.py` regenerates them. These are synthetic data, not submitted customer invoices. The test suite uses real local Tesseract/PDFium, FakeClock and scripted/mocked provider calls; pytest clears Google credentials so no live-provider request can occur accidentally.

Executed offline command: `.\.runtime\python311\python.exe -X utf8 scripts/demo_t2.py`. [Actual output](verification/task2-demo.json) includes clean extraction, missing nulls, explicit three-field conflicts, replacement requests and injection/active-file rejection. This script explicitly disables vision to demonstrate the honest unavailable branch. No OCR accuracy percentage is claimed.

Separately executed manual command: `.\.runtime\python311\python.exe -X utf8 scripts/check_live_task2_vision.py`. The existing real Gemini key/model returned `status: analysed` in an observed 8300.09519999976 ms including local OCR. Its [actual output](verification/task2-live-vision.json) preserves null order/date/amount/error fields and the model's explicit statement that the text-only fixture depicts no physical product. This proves one real image request/response, not general visual accuracy, invoice authenticity, deployment or field performance.

Full pytest/Ruff evidence and requirement mapping: [RTM](../RTM.md), [current verification](README.md), [pytest output](verification/pytest-task2.txt), [Ruff output](verification/ruff-task2.txt). On this host, the test harness required execution outside the sandbox because Windows blocked asyncio's local socketpair; tests still made no external network requests.
