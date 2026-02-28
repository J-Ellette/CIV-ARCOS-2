"""Idempotency key utilities for write endpoints.

This module provides a small, in-memory idempotency cache that allows
request handlers to safely replay responses for retried POST requests.
"""

from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from civ_arcos.web.framework import Response


@dataclass
class IdempotencyEntry:
    """Cached response metadata for a single idempotency key."""

    fingerprint: str
    status_code: int
    content_type: str
    body: bytes
    headers: Dict[str, str]
    created_at: float


class IdempotencyCache:
    """Thread-safe in-memory idempotency cache.

    The cache stores complete HTTP responses for a given idempotency key and
    request fingerprint. If the same key is reused with a different payload,
    a conflict is reported so callers can reject the request.
    """

    def __init__(self, ttl_secs: int = 60 * 60 * 24) -> None:
        self.ttl_secs = ttl_secs
        self._entries: Dict[str, IdempotencyEntry] = {}
        self._lock = threading.Lock()

    def _prune_expired(self, now: Optional[float] = None) -> None:
        """Remove entries older than the configured TTL."""
        ts = now if now is not None else time.time()
        expired = [
            key
            for key, entry in self._entries.items()
            if ts - entry.created_at > self.ttl_secs
        ]
        for key in expired:
            self._entries.pop(key, None)

    def lookup(
        self,
        key: str,
        fingerprint: str,
    ) -> Tuple[str, Optional[Response]]:
        """Find a cached response for *key*.

        Returns
        -------
        tuple[str, Optional[Response]]
            First value is one of:
              - ``"miss"`` when key is not cached.
              - ``"hit"`` when key and fingerprint match.
              - ``"conflict"`` when key exists but fingerprint differs.
        """
        if not key:
            return "miss", None

        with self._lock:
            self._prune_expired()
            entry = self._entries.get(key)
            if entry is None:
                return "miss", None
            if entry.fingerprint != fingerprint:
                return "conflict", None

            replay = Response(
                body=entry.body,
                status_code=entry.status_code,
                content_type=entry.content_type,
                headers=dict(entry.headers),
            )
            replay.headers["X-Idempotency-Replayed"] = "true"
            return "hit", replay

    def store(self, key: str, fingerprint: str, response: Response) -> None:
        """Store a response for *key* and *fingerprint*."""
        if not key:
            return
        with self._lock:
            self._prune_expired()
            self._entries[key] = IdempotencyEntry(
                fingerprint=fingerprint,
                status_code=response.status_code,
                content_type=response.content_type,
                body=response.body,
                headers=dict(response.headers),
                created_at=time.time(),
            )


def make_request_fingerprint(method: str, path: str, body: bytes) -> str:
    """Create a deterministic fingerprint for an HTTP request."""
    hasher = hashlib.sha256()
    hasher.update(method.upper().encode())
    hasher.update(b"\n")
    hasher.update(path.encode())
    hasher.update(b"\n")
    hasher.update(body)
    return hasher.hexdigest()
