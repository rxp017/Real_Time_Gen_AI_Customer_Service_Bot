"""Frozen evaluation text cannot become implementation examples or rules."""

import json
from pathlib import Path

import pytest

from scripts.check_holdouts import FROZEN, check


def test_heldout_hashes_and_no_implementation_contamination():
    assert check()["implementation_contamination"] == []


@pytest.mark.parametrize("target", ["core/prompt.py", "resources/languages/example.json", "config/synonyms.yaml", "data/golden/fewshot.json"])
def test_guard_rejects_heldout_text_in_implementation_or_examples(tmp_path, target):
    for name in FROZEN:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(Path(name).read_bytes())
        destination.with_suffix(".sha256").write_bytes(Path(name).with_suffix(".sha256").read_bytes())
    corpus = json.loads(Path(next(iter(FROZEN))).read_text())
    sample = corpus["cases"][0]["question"]
    destination = tmp_path / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("example = " + repr(sample) if destination.suffix == ".py" else json.dumps({"example": sample}))
    with pytest.raises(AssertionError, match="contamination"):
        check(tmp_path)
