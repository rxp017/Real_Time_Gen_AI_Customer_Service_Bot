# OCR prerequisites

Linux (Debian/Ubuntu), Python 3.11:

```sh
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-tel tesseract-ocr-spa
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/check_ocr.py
python -m pytest -q
python -m ruff check .
```

No environment override is needed. Tesseract uses its system language directory when `.runtime/tessdata` is absent. `python scripts/fetch_tessdata.py` installs the tagged official four-pack resources into that local directory when needed.

Windows: install Tesseract (for example `choco install tesseract -y`), then run `python scripts/fetch_tessdata.py` and `python scripts/check_ocr.py`. PATH is preferred; the standard Windows installation location is a fallback. Explicit runtime OCR executable overrides beat `TESSERACT_CMD`; the environment otherwise beats the config default. An explicitly invalid override fails visibly.

CI installs prerequisites independently on Ubuntu and Windows, runs Ruff and the entire offline suite, and builds/runs the Docker image's OCR check. Only actual completed workflow runs establish hosted-platform verification.
