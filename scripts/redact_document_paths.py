"""Remove workstation/runner path identities from documentation without changing results."""

import argparse
import hashlib
import json
import re
from pathlib import Path


def redact(text: str, workspace: Path) -> str:
    root = str(workspace.resolve())
    variants = {root, root.replace("\\", "/"), root.replace("\\", "\\\\")}
    for value in sorted(variants, key=len, reverse=True):
        text = re.sub(re.escape(value), "WORKSPACE", text, flags=re.IGNORECASE)
    parts = workspace.resolve().parts
    for index, part in enumerate(parts[:-1]):
        if part.casefold() == "users":
            username = parts[index + 1]
            text = re.sub(r"\b" + re.escape(username) + r"\b", "LOCAL_USER", text, flags=re.IGNORECASE)
    patterns = [
        (r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+", "USER_HOME"),
        (r"[A-Za-z]:[\\/]+hostedtoolcache[\\/]+windows[\\/]+Python[\\/]+[\d.]+[\\/]+x64", "PYTHON_RUNTIME"),
        (r"[A-Za-z]:[\\/]+Program Files[\\/]+Tesseract-OCR", "TESSERACT_INSTALL"),
        (r"[A-Za-z]:[\\/]+Program Files", "PROGRAM_FILES"),
        (r"[A-Za-z]:[\\/]+ProgramData", "PROGRAM_DATA"),
        (r"[A-Za-z]:[\\/]+a[\\/]", "CI_WORKSPACE/"),
        (r"/home/[^/\s\"']+/work/[^/\s\"']+/[^/\s\"']+", "CI_WORKSPACE"),
        (r"/home/[^/\s\"']+", "USER_HOME"),
        (r"/Users/[^/\s\"']+", "USER_HOME"),
        (r"/opt/hostedtoolcache/Python/[\d.]+/x64", "PYTHON_RUNTIME"),
        (r"/usr/local/lib/python[\d.]+/site-packages", "PYTHON_PACKAGES"),
        (r"/tmp/[^/\s\"']+", "TEMP_DIR"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text.replace("file:///WORKSPACE", "WORKSPACE")


def process(check: bool = False) -> dict:
    workspace = Path.cwd()
    changed = []
    for path in [Path("README.md"), *Path("docs").rglob("*")]:
        if not path.is_file() or path.suffix not in {".md", ".json", ".txt", ".jsonl", ".log"}:
            continue
        if path.as_posix().startswith("docs/tasks/"):
            continue
        data = path.read_bytes()
        text = data.decode("utf-8-sig")
        cleaned = redact(text, workspace)
        if cleaned == text:
            continue
        updated = (b"\xef\xbb\xbf" if data.startswith(b"\xef\xbb\xbf") else b"") + cleaned.encode("utf-8")
        changed.append({"path": path.as_posix(), "before_sha256": hashlib.sha256(data).hexdigest(),
                        "after_sha256": hashlib.sha256(updated).hexdigest()})
        if not check:
            path.write_bytes(updated)
    return {"scope": "Path/user text only. Metrics, verdicts, timestamps and original recorded hashes remain unchanged.", "changed": changed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = process(args.check)
    if not args.check:
        manifest = Path("docs/verification/revision-path-redactions.json")
        previous = json.loads(manifest.read_text()).get("changed", []) if manifest.exists() else []
        rows = {tuple(sorted(row.items())): row for row in [*previous, *report["changed"]]}
        manifest.write_text(json.dumps({**report, "changed": list(rows.values())}, indent=2))
    print(json.dumps({"files": len(report["changed"]), "paths": [row["path"] for row in report["changed"]]}, indent=2))
    if args.check and report["changed"]:
        raise SystemExit(1)
