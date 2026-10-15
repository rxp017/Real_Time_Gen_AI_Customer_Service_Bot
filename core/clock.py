"""Clock abstraction module.

Enforces unified, deterministic time management across the system.
All time-related operations must query Clock rather than calling datetime.now().
Timezone is Asia/Kolkata.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
except (ZoneInfoNotFoundError, KeyError):
    from datetime import timezone
    KOLKATA_TZ = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")


class Clock(ABC):
    """Abstract Clock interface."""

    @abstractmethod
    def now(self) -> datetime:
        """Return the current timezone-aware datetime in Asia/Kolkata."""

    @abstractmethod
    def sleep(self, seconds: float) -> None:
        """Pause execution or advance simulated time."""

    def monotonic(self) -> float:
        """Deterministic elapsed-time source for clock-driven measurements."""
        return self.now().timestamp()


class SystemClock(Clock):
    """Production clock using system time in Asia/Kolkata."""

    def __init__(self, tz: ZoneInfo = KOLKATA_TZ) -> None:
        self.tz = tz

    def now(self) -> datetime:
        return datetime.now(self.tz)

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def monotonic(self) -> float:
        return time.perf_counter()


class FakeClock(Clock):
    """Deterministic, controllable clock for testing and simulation."""

    def __init__(self, initial_time: datetime | str | None = None, tz: ZoneInfo = KOLKATA_TZ) -> None:
        self.tz = tz
        if initial_time is None:
            self._current_time = datetime(2026, 10, 13, 12, 0, 0, tzinfo=self.tz)
        elif isinstance(initial_time, str):
            dt = datetime.fromisoformat(initial_time)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=self.tz)
            else:
                dt = dt.astimezone(self.tz)
            self._current_time = dt
        else:
            if initial_time.tzinfo is None:
                self._current_time = initial_time.replace(tzinfo=self.tz)
            else:
                self._current_time = initial_time.astimezone(self.tz)

    def now(self) -> datetime:
        return self._current_time

    def set(self, new_time: datetime | str) -> None:
        """Set the clock to a specific point in time."""
        if isinstance(new_time, str):
            dt = datetime.fromisoformat(new_time)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=self.tz)
            else:
                dt = dt.astimezone(self.tz)
            self._current_time = dt
        else:
            if new_time.tzinfo is None:
                self._current_time = new_time.replace(tzinfo=self.tz)
            else:
                self._current_time = new_time.astimezone(self.tz)

    def advance(
        self,
        seconds: float = 0,
        minutes: float = 0,
        hours: float = 0,
        days: float = 0,
    ) -> datetime:
        """Advance simulated clock by the specified delta."""
        delta = timedelta(
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )
        self._current_time += delta
        return self._current_time

    def sleep(self, seconds: float) -> None:
        """Simulate sleep by advancing the fake clock."""
        self.advance(seconds=seconds)


# Global clock registry for dependency injection
_GLOBAL_CLOCK: Clock = SystemClock()


def get_clock() -> Clock:
    """Return the currently configured global Clock."""
    return _GLOBAL_CLOCK


def set_global_clock(clock: Clock) -> None:
    """Configure the global Clock instance (e.g. inject FakeClock in tests)."""
    global _GLOBAL_CLOCK
    _GLOBAL_CLOCK = clock
