from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    def __init__(self, current: datetime) -> None:
        if current.tzinfo is None:
            raise ValueError("clock time must include a timezone")
        self._current = current

    def now(self) -> datetime:
        return self._current

    def advance(self, delta: timedelta) -> None:
        if delta.total_seconds() < 0:
            raise ValueError("clock cannot move backwards")
        self._current += delta
