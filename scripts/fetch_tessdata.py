"""Download tagged official OCR language resources for an isolated checkout."""

import argparse
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default=".runtime/tessdata")
    args = parser.parse_args()
    directory = Path(args.directory)
    directory.mkdir(parents=True, exist_ok=True)
    for language in ("eng", "hin", "tel", "spa"):
        destination = directory / f"{language}.traineddata"
        url = f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/{language}.traineddata"
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        if len(data) < 1000:
            raise RuntimeError("Invalid language resource: " + language)
        temporary = destination.with_suffix(".download")
        temporary.write_bytes(data)
        temporary.replace(destination)
        print(f"Installed {language}: {len(data)} bytes")


if __name__ == "__main__":
    main()
