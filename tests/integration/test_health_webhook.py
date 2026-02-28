"""Integration tests for health endpoints and webhook endpoint."""

import hashlib
import hmac
import json
import os
import pytest


def _handle(method: str, path: str, body: bytes = b"", headers=None, query_params=None):
    """Invoke the API application handle() directly."""
    from civ_arcos import api

    return api.app.handle(
        method,
        path,
        query_params or {},
        body,
        headers or {},
    )


def _make_sig(body: bytes, secret: str) -> str:
    """Compute sha256= signature."""
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


# ---------------------------------------------------------------------------
# Health — liveness
# ---------------------------------------------------------------------------


class TestHealthLive:
    """Tests for GET /api/health/live."""

    def test_returns_200(self):
        """Liveness must always return 200."""
        resp = _handle("GET", "/api/health/live")
        assert resp.status_code == 200

    def test_body_ok(self):
        """Body must contain ``status: ok``."""
        resp = _handle("GET", "/api/health/live")
        data = json.loads(resp.body)
        assert data["status"] == "ok"

    def test_has_correlation_id_header(self):
        """Every response must carry X-Correlation-ID."""
        resp = _handle("GET", "/api/health/live")
        assert "X-Correlation-ID" in resp.headers


# ---------------------------------------------------------------------------
# Health — readiness
# ---------------------------------------------------------------------------


class TestHealthReady:
    """Tests for GET /api/health/ready."""

    def test_returns_2xx(self):
        """Readiness must return 200 or 503 (both are valid operational states)."""
        resp = _handle("GET", "/api/health/ready")
        assert resp.status_code in (200, 503)

    def test_body_has_checks(self):
        """Body must include a ``checks`` key."""
        resp = _handle("GET", "/api/health/ready")
        data = json.loads(resp.body)
        assert "checks" in data
        assert "status" in data

    def test_checks_includes_blockchain(self):
        """``checks`` must include ``blockchain``."""
        resp = _handle("GET", "/api/health/ready")
        data = json.loads(resp.body)
        assert "blockchain" in data["checks"]

    def test_checks_includes_evidence_store(self):
        """``checks`` must include ``evidence_store``."""
        resp = _handle("GET", "/api/health/ready")
        data = json.loads(resp.body)
        assert "evidence_store" in data["checks"]


# ---------------------------------------------------------------------------
# Health — dependencies
# ---------------------------------------------------------------------------


class TestHealthDependencies:
    """Tests for GET /api/health/dependencies."""

    def test_returns_2xx(self):
        """Must return 200 or 503."""
        resp = _handle("GET", "/api/health/dependencies")
        assert resp.status_code in (200, 503)

    def test_body_has_version_and_uptime(self):
        """Body must include version and uptime_seconds."""
        resp = _handle("GET", "/api/health/dependencies")
        data = json.loads(resp.body)
        assert "version" in data
        assert "uptime_seconds" in data

    def test_checks_includes_assurance_cases(self):
        """``checks`` must include ``assurance_cases``."""
        resp = _handle("GET", "/api/health/dependencies")
        data = json.loads(resp.body)
        assert "assurance_cases" in data["checks"]


# ---------------------------------------------------------------------------
# Webhook — POST /api/webhooks/github
# ---------------------------------------------------------------------------


class TestWebhookGitHub:
    """Tests for POST /api/webhooks/github."""

    def _post(self, body: bytes, headers=None):
        """Helper to POST to the webhook endpoint."""
        return _handle("POST", "/api/webhooks/github", body, headers or {})

    def test_no_secret_dev_mode(self, monkeypatch):
        """Without CIV_WEBHOOK_SECRET set, the endpoint accepts all deliveries."""
        monkeypatch.delenv("CIV_WEBHOOK_SECRET", raising=False)
        body = json.dumps({"action": "push"}).encode()
        resp = self._post(body, {"X-GitHub-Event": "push"})
        assert resp.status_code == 202
        data = json.loads(resp.body)
        assert data["received"] is True
        assert data["secret_configured"] is False

    def test_valid_signature_accepted(self, monkeypatch):
        """A correctly signed delivery must be accepted (202)."""
        secret = "test-webhook-secret"
        monkeypatch.setenv("CIV_WEBHOOK_SECRET", secret)
        body = json.dumps({"action": "push"}).encode()
        sig = _make_sig(body, secret)
        resp = self._post(
            body,
            {
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "delivery-test-001",
            },
        )
        assert resp.status_code == 202
        data = json.loads(resp.body)
        assert data["received"] is True
        assert data["secret_configured"] is True

    def test_invalid_signature_rejected(self, monkeypatch):
        """A delivery with a wrong signature must be rejected (401)."""
        monkeypatch.setenv("CIV_WEBHOOK_SECRET", "real-secret")
        body = json.dumps({"action": "push"}).encode()
        wrong_sig = _make_sig(body, "wrong-secret")
        resp = self._post(
            body,
            {
                "X-Hub-Signature-256": wrong_sig,
                "X-GitHub-Event": "push",
            },
        )
        assert resp.status_code == 401

    def test_replay_rejected(self, monkeypatch):
        """A delivery with a previously seen delivery ID must be rejected (409)."""
        monkeypatch.delenv("CIV_WEBHOOK_SECRET", raising=False)
        from civ_arcos.web.webhook import nonce_cache

        delivery_id = "unique-delivery-xyz-replay-test"
        # Ensure clean state.
        with nonce_cache._lock:
            nonce_cache._seen.pop(delivery_id, None)

        body = json.dumps({"action": "push"}).encode()
        headers = {"X-GitHub-Event": "push", "X-GitHub-Delivery": delivery_id}
        # First delivery — accepted.
        resp1 = self._post(body, headers)
        assert resp1.status_code == 202
        # Second delivery — replay.
        resp2 = self._post(body, headers)
        assert resp2.status_code == 409

    def test_event_type_in_response(self, monkeypatch):
        """Response must echo back the event type."""
        monkeypatch.delenv("CIV_WEBHOOK_SECRET", raising=False)
        body = b'{"action":"opened"}'
        resp = self._post(body, {"X-GitHub-Event": "pull_request"})
        data = json.loads(resp.body)
        assert data["event"] == "pull_request"
