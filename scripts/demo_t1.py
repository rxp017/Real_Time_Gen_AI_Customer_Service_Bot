"""Simulate a maintenance day with real SQLite and explicitly offline FakeLLM."""

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.audit import AuditLogger
from core.clock import FakeClock, set_global_clock
from core.llm import FakeLLM
from core.metrics import MetricsCollector
from core.retrieval import PolicyRetrievalEngine
from core.store import AuditLogRepository, SnapshotRepository
from core.updates import UpdateService


def run_demo() -> None:
    admin = "offline-demo-admin"
    os.environ["API_KEY_ADMIN"] = admin
    clock = FakeClock("2026-10-18T00:00:00+05:30")
    set_global_clock(clock)
    work = ROOT / ".verification" / ("demo-t1-" + uuid4().hex)
    work.mkdir(parents=True)
    repo = SnapshotRepository(str(work / "rag.db"))
    PolicyRetrievalEngine(repo).load_fixture_directory(ROOT / "data/sample_docs")
    audit_repo = AuditLogRepository(str(work / "audit.db"))
    service = UpdateService(repo, FakeLLM(), clock, AuditLogger(audit_repo), MetricsCollector(),
                            work / "quarantine", ROOT / "data/golden")
    initial = repo.active_info()["version"]
    print("OFFLINE MAINTENANCE DAY: FakeClock/FakeLLM; real SQLite and measured golden results")
    print(f"00:00 ACTIVE={initial}, golden={service.evaluate(initial)}")
    bad = work / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    clock.set("2026-10-18T00:05:00+05:30")
    quarantine_result = service.ingest([bad], admin)
    print("00:05 quarantine reason=" + quarantine_result["quarantined"][0]["reason"])
    data = json.loads((ROOT / "data/sample_docs/policy_v2_refund.json").read_text())
    data["effective_date"] = "2026-01-02"
    update = work / "refund.json"
    update.write_text(json.dumps(data), encoding="utf-8")
    duplicate = work / "refund_copy.json"
    duplicate.write_text(json.dumps(data, indent=2), encoding="utf-8")
    service.schedule([update, duplicate], admin)
    clock.set("2026-10-18T01:00:00+05:30")
    job = service.tick()
    candidate = job["version"]
    report = repo.snapshot(candidate)["report"]
    print(f"01:00 job={job['status']}, candidate={candidate}, duplicate_count={service.metrics.get_summary()['counters']['update_duplicates']}")
    print("01:00 quality=" + json.dumps(report, sort_keys=True))
    service.approve(candidate, admin)
    clock.set("2026-10-18T01:30:00+05:30")
    try:
        service.activate(candidate, admin)
    except ValueError as exc:
        print(f"01:30 {exc}; ACTIVE={repo.active_info()['version']}")
    clock.set("2026-10-18T02:00:00+05:30")
    service.tick()
    assert repo.active_info()["version"] == candidate
    print(f"02:00 approved candidate activated; ACTIVE={candidate}")
    clock.advance(minutes=3)
    service.llm = FakeLLM(default_response="Unsubstantiated answer")
    service.tick()
    assert repo.active_info()["version"] == initial
    print(f"02:03 scripted health failure; auto-rollback ACTIVE={initial}")
    service.llm = FakeLLM()
    clock.set("2026-10-18T02:10:00+05:30")
    replacement = service.ingest([update], admin)["version"]
    assert service.quality_gate(replacement, admin)["accepted"]
    service.approve(replacement, admin)
    service.activate(replacement, admin)
    print(f"02:10 corrected update activated; ACTIVE={replacement}")
    clock.advance(minutes=5, seconds=1)
    service.llm = FakeLLM(default_response="Unsubstantiated answer")
    service.tick()
    assert repo.active_info()["version"] == replacement
    print(f"02:15:01 health window expired; ACTIVE={replacement}; no automatic rollback")
    service.llm = FakeLLM()
    clock.set("2026-10-18T04:00:00+05:30")
    unchanged = service.ingest([update], admin)
    print(f"04:00 unchanged file skipped={len(unchanged['skipped'])}")
    clock.set("2026-10-18T10:00:00+05:30")
    service.rollback(initial, admin)
    print(f"10:00 manual rollback; ACTIVE={repo.active_info()['version']}")
    clock.set("2026-10-18T23:59:00+05:30")
    service.tick()
    print("23:59 audit events=" + ",".join(e["event_type"] for e in reversed(audit_repo.get_recent(100))))
    print("23:59 metrics=" + json.dumps(service.metrics.get_summary(), sort_keys=True))
    print("DAY COMPLETE: assertions passed; provider behavior is scripted, not a live-provider validation")
    repo.close()
    audit_repo.close()


if __name__ == "__main__":
    run_demo()
