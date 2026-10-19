"""Documentation redaction must preserve recorded results and protected task sources."""

import json
from pathlib import Path

from scripts.redact_document_paths import process, redact


def test_document_redaction_preserves_measurements_and_valid_json(tmp_path):
    source = {"windows": r"C:\Users\fixture-user\project\results.txt",
              "linux": "/home/runner/work/project/project/report.txt",
              "accuracy": 0.6, "valid_run": False, "original_hash": "a" * 64,
              "date": "2026-10-19", "container": "/app/data/state.db"}
    cleaned = json.loads(redact(json.dumps(source), tmp_path))
    assert "fixture-user" not in json.dumps(cleaned)
    assert "runner" not in cleaned["linux"]
    assert cleaned["accuracy"] == source["accuracy"]
    assert cleaned["valid_run"] is False
    assert cleaned["original_hash"] == source["original_hash"]
    assert cleaned["date"] == source["date"]
    assert cleaned["container"] == source["container"]


def test_document_redaction_keeps_task_sources(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tasks = Path("docs/tasks")
    tasks.mkdir(parents=True)
    task = tasks / "T4.md"
    task.write_text(r"Required original source C:\Users\fixture-user\source")
    evidence = Path("docs/archive/output.txt")
    evidence.parent.mkdir()
    evidence.write_bytes(b"C:\\Users\\fixture-user\\source\r\n21 passed in 0.35s\r\n")
    before = task.read_bytes()
    report = process()
    assert [row["path"] for row in report["changed"]] == [evidence.as_posix()]
    assert task.read_bytes() == before
    assert evidence.read_bytes() == b"USER_HOME\\source\r\n21 passed in 0.35s\r\n"
    assert process(check=True)["changed"] == []


def test_document_redaction_check_has_no_write_side_effect(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("docs").mkdir()
    target = Path("docs/evidence.json")
    target.write_text(json.dumps({"source": str(tmp_path / "run.txt"), "failures": 10}))
    before = target.read_bytes()
    report = process(check=True)
    assert len(report["changed"]) == 1
    assert target.read_bytes() == before
