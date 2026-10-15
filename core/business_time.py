"""Shared business calendar calculations; callers supply Clock timestamps."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from core.config import get_config


class BusinessCalendar:
    def __init__(self) -> None:
        cfg = get_config()
        hours = cfg.get("timings.business_hours")
        self.zone = ZoneInfo(cfg.timezone)
        self.start, self.end = time.fromisoformat(hours["start"]), time.fromisoformat(hours["end"])
        self.days, self.holidays = set(hours["workdays"]), set(cfg.holidays)
        self.horizon = int(cfg.get("support.calendar_search_days"))
        if self.start >= self.end or not self.days or not self.days <= set(range(7)) or self.horizon < 1:
            raise ValueError("Invalid business calendar")

    def interval(self, day: date) -> tuple[datetime, datetime] | None:
        if day.weekday() not in self.days or day.isoformat() in self.holidays:
            return None
        return datetime.combine(day, self.start, self.zone), datetime.combine(day, self.end, self.zone)

    def is_open(self, at: datetime) -> bool:
        local = at.astimezone(self.zone)
        interval = self.interval(local.date())
        return interval is not None and interval[0] <= local < interval[1]

    def next_open(self, at: datetime, next_date: bool = False) -> datetime:
        local = at.astimezone(self.zone)
        for offset in range(int(next_date), self.horizon + 1):
            interval = self.interval(local.date() + timedelta(days=offset))
            if interval and local < interval[1]:
                return max(local, interval[0])
        raise ValueError("No business opening within configured horizon")

    def minutes(self, start: datetime, end: datetime) -> float:
        start, end = start.astimezone(self.zone), end.astimezone(self.zone)
        total = 0.0
        day = start.date()
        while day <= end.date() and end > start:
            interval = self.interval(day)
            if interval:
                total += max(0.0, (min(end, interval[1]) - max(start, interval[0])).total_seconds() / 60)
            day += timedelta(days=1)
        return total

    def add_minutes(self, start: datetime, minutes: float) -> datetime:
        if minutes <= 0:
            raise ValueError("SLA minutes must be positive")
        current = self.next_open(start)
        remaining = minutes
        for _ in range(self.horizon + 1):
            interval = self.interval(current.date())
            if interval is None:
                raise ValueError("Expected working interval")
            available = (interval[1] - current).total_seconds() / 60
            if remaining <= available:
                return current + timedelta(minutes=remaining)
            remaining -= available
            current = self.next_open(interval[1])
        raise ValueError("SLA exceeds configured calendar horizon")
