$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force .runtime/python311 | Out-Null
Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip -OutFile .runtime/python311.zip
Expand-Archive -LiteralPath .runtime/python311.zip -DestinationPath .runtime/python311 -Force
Set-Content -LiteralPath .runtime/python311/python311._pth -Encoding ascii -Value @('python311.zip', '.', 'import site')
Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile .runtime/get-pip.py
& ./.runtime/python311/python.exe .runtime/get-pip.py --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw 'Python bootstrap failed' }
& ./.runtime/python311/python.exe -m pip install --no-warn-script-location -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Pinned dependency installation failed' }
& ./.runtime/python311/python.exe scripts/fetch_tessdata.py
if ($LASTEXITCODE -ne 0) { throw 'Language resource installation failed' }
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
& ./.runtime/python311/python.exe -X utf8 scripts/check_ocr.py
if ($LASTEXITCODE -ne 0) { throw 'Tesseract prerequisite check failed; install Tesseract first' }
