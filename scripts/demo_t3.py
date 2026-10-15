"""Offline ticket lifecycle demonstration with actual shared services and synthetic input."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.audit import AuditLogger
from core.clock import FakeClock, set_global_clock
from core.config import get_config_manager
from core.metrics import MetricsCollector
from core.store import TicketRepository
from core.tickets import TicketService


def main() -> None:
    clock = FakeClock("2026-10-16T17:30:00+05:30")
    set_global_clock(clock)
    cfg = get_config_manager(Path(__file__).resolve().parents[1] / "config/default.yaml")
    cfg.update_runtime_override("holidays", ["2026-10-19"])
    repo = TicketRepository()
    service = TicketService(repo, clock, AuditLogger(), MetricsCollector())
    try:
        draft = service.collect("demo-owner", "demo-session", 1, {"issue": "delivery is late"},
                                {"last_user_request": "My delivery is late"}, [])
        print("Draft:", draft["status"], draft["question"])
        complete = {"customer": "customer-demo", "order": "ORD-4512", "product": "PRD-007",
                    "evidence": "Customer reports a late parcel", "contact": "demo@example.com"}
        ticket = service.collect("demo-owner", "demo-session", 1, complete, {}, [], draft["id"])
        print("Ticket:", ticket["status"], ticket["queue_reason"])
        print("Handoff contact masked:", "demo@example.com" not in ticket["handoff_summary"])
        print("SLA due:", ticket["sla"]["due_at"])
        duplicate = service.collect("demo-owner", "demo-session", 1,
                                    {**complete, "issue": "please my delivery is late"}, {}, [])
        print("Duplicate merged:", duplicate["id"] == ticket["id"], "requests:", len(duplicate["requests"]))
        clock.set("2026-10-20T11:30:00+05:30")
        service.tick()
        warning = next(r for r in service.view() if r["id"] == ticket["id"])
        print("After weekend + Monday holiday:", warning["sla"]["consumed_minutes"], "business minutes")
        print("Warning:", any(e["kind"] == "sla_warning" for e in warning["events"]))
        cfg.update_runtime_override("tickets.agents", [{"id": "demo-agent", "skills": ["delivery"], "available": True, "capacity": 1}])
        service.tick()
        assigned = next(r for r in service.view() if r["id"] == ticket["id"])
        print("Configured demo agent:", assigned["status"], assigned["agent_id"])
        clock.advance(minutes=60)
        service.tick()
        breached = next(r for r in service.view() if r["id"] == ticket["id"])
        print("Breach:", breached["sla"]["breached"], "escalated:", breached["escalated"])
        print("Events:", ", ".join(e["kind"] for e in breached["events"]))
    finally:
        repo.close()


if __name__ == "__main__":
    main()
