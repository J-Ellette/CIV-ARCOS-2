"""Webhook security utilities: signature validation and replay protection.

Provides HMAC-SHA256 signature verification (GitHub-style ``X-Hub-Signature-256``
header), timestamp tolerance checks, and an in-memory nonce cache to prevent
replayed deliveries.
"""

import hashlib
import hmac
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Set

# ---------------------------------------------------------------------------
# Signature validation
# ---------------------------------------------------------------------------


def validate_github_signature(
    body: bytes,
    secret: str,
    signature_header: str,
) -> bool:
    """Verify a GitHub-style HMAC-SHA256 webhook signature.

    Parameters
    ----------
    body:
        Raw request body bytes.
    secret:
        Shared webhook secret.
    signature_header:
        Value of the ``X-Hub-Signature-256`` header (format: ``sha256=<hex>``).

    Returns
    -------
    bool
        ``True`` if the computed digest matches the provided signature.
    """
    if not secret or not signature_header:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected_sig = signature_header[len("sha256=") :]
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    computed_sig = mac.hexdigest()
    # Use constant-time comparison to prevent timing attacks.
    return hmac.compare_digest(computed_sig, expected_sig)


# ---------------------------------------------------------------------------
# Timestamp tolerance
# ---------------------------------------------------------------------------


def validate_timestamp(
    timestamp_str: str,
    tolerance_secs: int = 300,
    _now: Optional[float] = None,
) -> bool:
    """Check that a webhook delivery timestamp is within tolerance.

    Parameters
    ----------
    timestamp_str:
        ISO-8601 UTC timestamp string (e.g. ``2026-02-28T16:41:14Z``).
    tolerance_secs:
        Maximum allowed age of the delivery in seconds (default 300 = 5 min).
    _now:
        Override current time (seconds since epoch); used in tests only.

    Returns
    -------
    bool
        ``True`` if the timestamp is recent enough.
    """
    try:
        # Handle both ``Z`` suffix and ``+00:00`` offset.
        ts_str = timestamp_str.replace("Z", "+00:00")
        delivery_ts = datetime.fromisoformat(ts_str).timestamp()
    except (ValueError, TypeError):
        return False
    now = _now if _now is not None else time.time()
    return abs(now - delivery_ts) <= tolerance_secs


# ---------------------------------------------------------------------------
# Nonce / delivery-ID replay cache
# ---------------------------------------------------------------------------


class _NonceCache:
    """Thread-safe in-memory cache for seen delivery IDs.

    Entries expire after ``ttl_secs`` seconds to bound memory growth.  The
    cache is intentionally simple (no external dependency) and suitable for
    single-process deployments.
    """

    def __init__(self, ttl_secs: int = 600) -> None:
        """Initialise the cache.

        Parameters
        ----------
        ttl_secs:
            How long to keep a nonce before it may be evicted (default 10 min).
        """
        self._ttl = ttl_secs
        self._lock = threading.Lock()
        self._seen: Dict[str, float] = {}  # nonce → first-seen epoch

    def is_replay(self, nonce: str) -> bool:
        """Return ``True`` if *nonce* was seen before and has not expired.

        Parameters
        ----------
        nonce:
            Unique delivery identifier (e.g. ``X-GitHub-Delivery`` header).
        """
        self._evict()
        with self._lock:
            return nonce in self._seen

    def record(self, nonce: str) -> None:
        """Record that *nonce* has been processed.

        Parameters
        ----------
        nonce:
            Unique delivery identifier.
        """
        with self._lock:
            self._seen[nonce] = time.time()

    def _evict(self) -> None:
        """Remove expired entries from the cache."""
        cutoff = time.time() - self._ttl
        with self._lock:
            expired: Set[str] = {k for k, v in self._seen.items() if v < cutoff}
            for k in expired:
                del self._seen[k]


# Module-level singleton; the API layer can import this directly.
nonce_cache = _NonceCache()
