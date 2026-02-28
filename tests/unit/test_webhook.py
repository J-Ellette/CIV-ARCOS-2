"""Tests for the webhook security utilities."""
import hashlib
import hmac as _hmac
import time
import pytest

from civ_arcos.web.webhook import (
    _NonceCache,
    nonce_cache,
    validate_github_signature,
    validate_timestamp,
)


def _make_sig(body: bytes, secret: str) -> str:
    """Compute the correct sha256= signature for *body* using *secret*."""
    mac = _hmac.new(secret.encode(), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


# ---------------------------------------------------------------------------
# validate_github_signature
# ---------------------------------------------------------------------------

class TestValidateGithubSignature:
    """Unit tests for HMAC-SHA256 signature validation."""

    def test_valid_signature(self):
        """Correct signature must return True."""
        body = b'{"action":"push"}'
        secret = "my-webhook-secret"
        sig = _make_sig(body, secret)
        assert validate_github_signature(body, secret, sig) is True

    def test_wrong_secret(self):
        """Signature computed with a different secret must return False."""
        body = b'{"action":"push"}'
        sig = _make_sig(body, "correct-secret")
        assert validate_github_signature(body, "wrong-secret", sig) is False

    def test_tampered_body(self):
        """Signature valid for original body must fail for modified body."""
        original = b'{"action":"push"}'
        sig = _make_sig(original, "secret")
        tampered = b'{"action":"malicious"}'
        assert validate_github_signature(tampered, "secret", sig) is False

    def test_missing_prefix(self):
        """Signature without the ``sha256=`` prefix must return False."""
        body = b"hello"
        raw_hex = _hmac.new(b"sec", body, hashlib.sha256).hexdigest()
        assert validate_github_signature(body, "sec", raw_hex) is False

    def test_empty_secret(self):
        """An empty secret must return False without raising."""
        assert validate_github_signature(b"body", "", "sha256=abc") is False

    def test_empty_signature(self):
        """An empty signature must return False."""
        assert validate_github_signature(b"body", "secret", "") is False


# ---------------------------------------------------------------------------
# validate_timestamp
# ---------------------------------------------------------------------------

class TestValidateTimestamp:
    """Unit tests for timestamp tolerance checking."""

    def test_fresh_timestamp(self):
        """A timestamp within tolerance must return True."""
        now = time.time()
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 60))
        assert validate_timestamp(ts, tolerance_secs=300, _now=now) is True

    def test_stale_timestamp(self):
        """A timestamp beyond tolerance must return False."""
        now = time.time()
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 600))
        assert validate_timestamp(ts, tolerance_secs=300, _now=now) is False

    def test_future_timestamp_within_tolerance(self):
        """A slightly future timestamp (clock skew) must still be accepted."""
        now = time.time()
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 30))
        assert validate_timestamp(ts, tolerance_secs=300, _now=now) is True

    def test_invalid_timestamp_string(self):
        """An unparseable timestamp string must return False."""
        assert validate_timestamp("not-a-timestamp") is False

    def test_empty_timestamp_string(self):
        """An empty string must return False."""
        assert validate_timestamp("") is False

    def test_z_suffix_accepted(self):
        """ISO-8601 timestamps with ``Z`` suffix must be accepted."""
        now = time.time()
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
        assert validate_timestamp(ts, _now=now) is True


# ---------------------------------------------------------------------------
# _NonceCache
# ---------------------------------------------------------------------------

class TestNonceCache:
    """Unit tests for the in-memory nonce / delivery-ID replay cache."""

    def test_new_nonce_is_not_replay(self):
        """A nonce that has never been seen must not be flagged as a replay."""
        cache = _NonceCache()
        assert cache.is_replay("unique-nonce-001") is False

    def test_recorded_nonce_is_replay(self):
        """After recording, the same nonce must be flagged as a replay."""
        cache = _NonceCache()
        cache.record("delivery-abc")
        assert cache.is_replay("delivery-abc") is True

    def test_different_nonces_are_independent(self):
        """Recording one nonce must not affect another."""
        cache = _NonceCache()
        cache.record("nonce-A")
        assert cache.is_replay("nonce-A") is True
        assert cache.is_replay("nonce-B") is False

    def test_expired_nonce_is_not_replay(self):
        """A nonce that has expired past TTL must not be flagged as a replay."""
        cache = _NonceCache(ttl_secs=1)
        cache.record("old-nonce")
        assert cache.is_replay("old-nonce") is True
        # Simulate TTL expiry by back-dating the entry.
        with cache._lock:
            cache._seen["old-nonce"] = time.time() - 10
        assert cache.is_replay("old-nonce") is False

    def test_module_singleton_exists(self):
        """The module-level nonce_cache singleton must be an _NonceCache."""
        assert isinstance(nonce_cache, _NonceCache)
