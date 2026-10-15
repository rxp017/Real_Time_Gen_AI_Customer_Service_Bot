"""Pytest configuration and environment fixtures."""

import sys
from pathlib import Path

import pytest

# Ensure repository root is on sys.path
repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


@pytest.fixture(autouse=True)
def isolated_dependencies(monkeypatch):
    from app.chatbot import (
        set_conversation_service,
        set_task4_engine,
        set_update_service,
    )
    from app.upload_api import set_upload_service
    from core.clock import SystemClock, get_clock, set_global_clock
    from core.config import get_config_manager

    previous = get_clock()
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("GOOGLE_MODEL", "")
    set_global_clock(SystemClock())
    get_config_manager(repo_root / "config/default.yaml")
    for role, key in {"public": "public-key-anon", "customer": "customer-key-alice",
                      "support_agent": "support-key-bob", "admin": "admin-key-charlie"}.items():
        monkeypatch.setenv(f"API_KEY_{role.upper()}", key)
    set_update_service(None)
    set_task4_engine(None)
    set_conversation_service(None)
    set_upload_service(None)
    yield
    set_update_service(None)
    set_task4_engine(None)
    set_conversation_service(None)
    set_upload_service(None)
    set_global_clock(previous)
