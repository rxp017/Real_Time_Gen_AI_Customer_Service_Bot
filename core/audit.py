"""Structured audit logging module.

Masked by default: all messages and metadata are sanitized through mask_pii
before persistence or output.
"""

import json
import logging
from typing import Any

from core.clock import get_clock
from core.security import mask_pii
from core.store import AuditLogRepository

_std_logger = logging.getLogger("audit")


class AuditLogger:
    """Audit logger enforcing PII masking by default."""

    def __init__(self, repo: AuditLogRepository | None = None) -> None:
        self.repo = repo

    def _mask_object(self, obj: Any) -> Any:
        """Recursively mask PII in strings, lists, and dicts."""
        if isinstance(obj, str):
            return mask_pii(obj)
        elif isinstance(obj, dict):
            sensitive = {"api_key", "password", "secret", "token", "authorization"}
            return {k: "[MASKED_SECRET]" if str(k).lower() in sensitive else self._mask_object(v)
                    for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._mask_object(item) for item in obj]
        return obj

    def log(
        self,
        level: str,
        event_type: str,
        user_role: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a structured, masked audit event."""
        clock = get_clock()
        timestamp = clock.now().isoformat()

        masked_message = mask_pii(message)
        masked_metadata = self._mask_object(metadata or {})

        entry = {
            "timestamp": timestamp,
            "level": level.upper(),
            "event_type": event_type,
            "user_role": user_role,
            "message": masked_message,
            "metadata": masked_metadata,
        }

        if self.repo is not None:
            self.repo.log(
                level=entry["level"],
                event_type=event_type,
                user_role=user_role,
                message=masked_message,
                metadata=masked_metadata,
            )

        # Output JSON line for standard logging streams
        _std_logger.info(json.dumps(entry))
        return entry

    def log_info(self, event_type: str, user_role: str, message: str, **kwargs: Any) -> dict[str, Any]:
        return self.log("INFO", event_type, user_role, message, kwargs)

    def log_warning(self, event_type: str, user_role: str, message: str, **kwargs: Any) -> dict[str, Any]:
        return self.log("WARNING", event_type, user_role, message, kwargs)

    def log_error(self, event_type: str, user_role: str, message: str, **kwargs: Any) -> dict[str, Any]:
        return self.log("ERROR", event_type, user_role, message, kwargs)

    def log_security(self, event_type: str, user_role: str, message: str, **kwargs: Any) -> dict[str, Any]:
        return self.log("SECURITY", event_type, user_role, message, kwargs)


_GLOBAL_AUDIT_LOGGER: AuditLogger | None = None


def set_audit_logger(logger: AuditLogger | None) -> None:
    global _GLOBAL_AUDIT_LOGGER
    _GLOBAL_AUDIT_LOGGER = logger


def get_audit_logger(repo: AuditLogRepository | None = None) -> AuditLogger:
    """Return singleton AuditLogger instance."""
    global _GLOBAL_AUDIT_LOGGER
    if _GLOBAL_AUDIT_LOGGER is None or repo is not None:
        _GLOBAL_AUDIT_LOGGER = AuditLogger(repo)
    return _GLOBAL_AUDIT_LOGGER
