"""In-memory event stream for distributed sync updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, List


@dataclass
class SyncEvent:
    """A single sync event emitted by platform subsystems."""

    event_id: int
    topic: str
    emitted_at: str
    payload: Dict[str, Any]


class SyncEventStream:
    """Thread-safe in-memory stream for recent synchronization events."""

    def __init__(self, max_events: int = 1000) -> None:
        self._events: List[SyncEvent] = []
        self._next_id = 1
        self._max_events = max(1, max_events)
        self._lock = RLock()

    def emit(self, topic: str, payload: Dict[str, Any]) -> SyncEvent:
        """Emit a new event and return the stored event record."""
        with self._lock:
            event = SyncEvent(
                event_id=self._next_id,
                topic=topic,
                emitted_at=datetime.now(timezone.utc).isoformat(),
                payload=payload,
            )
            self._next_id += 1
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events :]
            return event

    def list_events(self, since_id: int = 0, limit: int = 50) -> List[SyncEvent]:
        """Return events with IDs greater than *since_id* in ascending order."""
        bounded_limit = max(1, min(limit, 500))
        with self._lock:
            events = [event for event in self._events if event.event_id > since_id]
            return events[:bounded_limit]

    def latest_event_id(self) -> int:
        """Return the most recent event id, or 0 when stream is empty."""
        with self._lock:
            if not self._events:
                return 0
            return self._events[-1].event_id
