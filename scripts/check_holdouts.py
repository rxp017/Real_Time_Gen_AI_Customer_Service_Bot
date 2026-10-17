"""Verify frozen bytes and reject full held-out questions/messages in implementation text."""

import ast
import hashlib
import json
import re
from pathlib import Path

FROZEN = {
    "tests/fixtures/task4/heldout_paraphrases.json": "413e80254b0d25da7269fbcac4dfb2ec8ca86420407301f3ad44eb38001bade9",
    "tests/fixtures/task5/heldout_sentiment.json": "bf58e610a821461b56d38d0d68a3370333b7db5d6ca63cd3f42d0d76dbbd76af",
}


def normalized(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.casefold()))


def check(root: Path = Path(".")) -> dict:
    examples = set()
    for name, expected in FROZEN.items():
        raw = (root / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected, f"Frozen hash changed: {name}"
        assert (root / name).with_suffix(".sha256").read_text().strip() == expected
        payload = json.loads(raw)
        examples.update(normalized(row.get("question", row.get("message", "")))
                        for row in payload.get("cases", payload.get("examples", [])))
    leaks = []
    for directory in ("core", "app", "scripts", "resources", "config", "tests"):
        for path in (root / directory).rglob("*"):
            if not path.is_file() or "fixtures" in path.parts or path.suffix not in {".py", ".json", ".yaml", ".js", ".html"}:
                continue
            text = path.read_text(encoding="utf-8")
            values = [text]
            if path.suffix == ".py":
                values += [n.value for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            if any(example and f" {example} " in f" {normalized(value)} " for value in values for example in examples):
                leaks.append(path.relative_to(root).as_posix())
    assert not leaks, f"Held-out full-text contamination in: {leaks}"
    return {"frozen_hashes": FROZEN, "implementation_contamination": leaks}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
