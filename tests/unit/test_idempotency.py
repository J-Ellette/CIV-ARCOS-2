"""Unit tests for idempotency utilities."""

from civ_arcos.web.framework import Response
from civ_arcos.web.idempotency import IdempotencyCache, make_request_fingerprint


def test_make_request_fingerprint_is_deterministic() -> None:
    """Fingerprint output must be stable for the same request fields."""
    body = b'{"a":1}'
    f1 = make_request_fingerprint("POST", "/api/blockchain/add", body)
    f2 = make_request_fingerprint("POST", "/api/blockchain/add", body)
    assert f1 == f2


def test_make_request_fingerprint_changes_for_payload() -> None:
    """Fingerprint must change when payload changes."""
    f1 = make_request_fingerprint("POST", "/api/blockchain/add", b'{"a":1}')
    f2 = make_request_fingerprint("POST", "/api/blockchain/add", b'{"a":2}')
    assert f1 != f2


def test_cache_lookup_miss_then_hit() -> None:
    """A stored response must be replayed for the same key + fingerprint."""
    cache = IdempotencyCache()
    key = "idem-001"
    fingerprint = make_request_fingerprint("POST", "/x", b"{}")

    state, replay = cache.lookup(key, fingerprint)
    assert state == "miss"
    assert replay is None

    original = Response({"ok": True}, status_code=201)
    cache.store(key, fingerprint, original)

    state, replay = cache.lookup(key, fingerprint)
    assert state == "hit"
    assert replay is not None
    assert replay.status_code == 201
    assert replay.headers.get("X-Idempotency-Replayed") == "true"


def test_cache_conflict_for_same_key_different_payload() -> None:
    """The same key with a different fingerprint must return conflict."""
    cache = IdempotencyCache()
    key = "idem-002"
    first = make_request_fingerprint("POST", "/x", b'{"n":1}')
    second = make_request_fingerprint("POST", "/x", b'{"n":2}')

    cache.store(key, first, Response({"saved": 1}, status_code=201))
    state, replay = cache.lookup(key, second)
    assert state == "conflict"
    assert replay is None


def test_cache_expires_entries_after_ttl() -> None:
    """Expired cache entries must be treated as misses."""
    cache = IdempotencyCache(ttl_secs=1)
    key = "idem-003"
    fingerprint = make_request_fingerprint("POST", "/x", b"payload")
    cache.store(key, fingerprint, Response({"saved": True}, status_code=201))

    with cache._lock:
        cache._entries[key].created_at -= 10

    state, replay = cache.lookup(key, fingerprint)
    assert state == "miss"
    assert replay is None
