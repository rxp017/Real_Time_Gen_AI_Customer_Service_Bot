"""Clock-driven inactivity and summary restoration with isolated session state."""

from collections.abc import Generator
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta
from threading import RLock
from typing import Any
from uuid import uuid4
from weakref import WeakValueDictionary

from core.clock import Clock
from core.config import get_config
from core.store import SessionRepository


class SessionManager:
    def __init__(self, repo: SessionRepository, clock: Clock) -> None:
        self.repo, self.clock = repo, clock
        self._registry_lock = RLock()
        self._locks: WeakValueDictionary[str, Any] = WeakValueDictionary()

    def _lock(self, session_id: str) -> Any:
        with self._registry_lock:
            lock = self._locks.get(session_id)
            if lock is None:
                lock = RLock()
                self._locks[session_id] = lock
            return lock

    def _new(self, generation: int) -> dict[str, Any]:
        return {"generation": generation, "status": "ACTIVE", "last_activity": self.clock.now().isoformat(),
                "messages": [], "entities": {}, "superseded": [], "last_intents": [],
                "message_count": 0, "summary": None, "language": None}

    def summarize(self, state: dict[str, Any]) -> dict[str, Any]:
        users = [m for m in state["messages"] if m["role"] == "user"]
        return {"entities": deepcopy(state["entities"]), "superseded": deepcopy(state["superseded"]),
                "last_intents": list(state["last_intents"]), "language": state["language"],
                "message_count": state["message_count"],
                "last_user_request": users[-1]["content"] if users else None}

    def _expire(self, state: dict[str, Any]) -> bool:
        gap = self.clock.now() - datetime.fromisoformat(state["last_activity"])
        limit = timedelta(minutes=float(get_config().get("timings.session_inactivity_timeout_minutes")))
        if state["status"] == "ACTIVE" and gap >= limit:
            state["summary"] = self.summarize(state)
            state["status"] = "EXPIRED"
            state["messages"] = []
            return True
        return False

    @contextmanager
    def conversation(self, session_id: str | None, owner: str) -> Generator[tuple[str, dict[str, Any], str], None, None]:
        cfg = get_config()
        if int(cfg.get("conversation.context_messages")) < 10:
            raise ValueError("Context window must retain at least 10 messages")
        session_id = session_id or uuid4().hex
        if not session_id.strip() or len(session_id) > int(cfg.get("conversation.max_session_id_characters")):
            raise ValueError("Invalid session id")
        with self._lock(session_id):
            loaded = self.repo.load_session(session_id, owner)
            if loaded is None:
                state, revision, transition = self._new(1), None, "NEW"
            else:
                state, revision = loaded
                self._expire(state)
                gap = self.clock.now() - datetime.fromisoformat(state["last_activity"])
                restore_limit = timedelta(hours=float(cfg.get("timings.session_restore_hours")))
                if state["status"] == "EXPIRED" and gap > restore_limit:
                    state, transition = self._new(state["generation"] + 1), "NEW_AFTER_RETENTION"
                elif state["status"] == "EXPIRED":
                    summary = deepcopy(state["summary"])
                    generation = state["generation"]
                    state, transition = self._new(generation), "RESTORED"
                    state.update(entities=summary["entities"], superseded=summary["superseded"],
                                 last_intents=summary["last_intents"], language=summary["language"], summary=summary)
                else:
                    transition = "CONTINUED"
            yield session_id, state, transition
            state["last_activity"] = self.clock.now().isoformat()
            self.repo.save_session(session_id, owner, state, revision)

    def append(self, state: dict[str, Any], role: str, content: str) -> None:
        state["messages"].append({"role": role, "content": content, "at": self.clock.now().isoformat()})
        size = int(get_config().get("conversation.context_messages"))
        state["messages"] = state["messages"][-size:]
        state["message_count"] += 1

    def inspect(self, session_id: str, owner: str) -> dict[str, Any]:
        with self._lock(session_id):
            loaded = self.repo.load_session(session_id, owner)
            if loaded is None:
                raise ValueError("Unknown session")
            state, revision = loaded
            if self._expire(state):
                self.repo.save_session(session_id, owner, state, revision)
            return state

    def expire_idle(self) -> int:
        expired = 0
        for session_id, owner in self.repo.session_owners():
            with self._lock(session_id):
                loaded = self.repo.load_session(session_id, owner)
                if loaded is not None:
                    state, revision = loaded
                    if self._expire(state):
                        self.repo.save_session(session_id, owner, state, revision)
                        expired += 1
        return expired
