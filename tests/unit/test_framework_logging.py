"""Tests for the structured logging / correlation ID middleware."""

import json
import logging
import pytest

from civ_arcos.web.framework import (
    Application,
    Request,
    Response,
    _make_correlation_id,
    _log_request,
    create_app,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _app_with_hello() -> Application:
    """Return a minimal app with a single GET /hello route."""
    app = create_app()

    @app.route("/hello", methods=["GET"])
    def hello(req: Request) -> Response:
        """Return a simple hello payload."""
        return Response({"message": "hello"})

    return app


# ---------------------------------------------------------------------------
# _make_correlation_id
# ---------------------------------------------------------------------------


class TestMakeCorrelationId:
    """Unit tests for _make_correlation_id."""

    def test_returns_string(self):
        """Correlation ID must be a non-empty string."""
        cid = _make_correlation_id()
        assert isinstance(cid, str)
        assert len(cid) > 0

    def test_uniqueness(self):
        """Each call should return a different value."""
        ids = {_make_correlation_id() for _ in range(50)}
        assert len(ids) == 50

    def test_length(self):
        """Correlation IDs should be 16 hex characters."""
        cid = _make_correlation_id()
        assert len(cid) == 16
        assert all(c in "0123456789abcdef" for c in cid)


# ---------------------------------------------------------------------------
# Response headers — X-Correlation-ID
# ---------------------------------------------------------------------------


class TestCorrelationIdHeader:
    """Verify that X-Correlation-ID is added to every response."""

    def test_header_present_on_success(self):
        """A successful response must carry X-Correlation-ID."""
        app = _app_with_hello()
        resp = app.handle("GET", "/hello", {}, b"", {})
        assert resp.status_code == 200
        assert "X-Correlation-ID" in resp.headers
        assert resp.headers["X-Correlation-ID"]  # non-empty

    def test_header_present_on_404(self):
        """A 404 response must also carry X-Correlation-ID."""
        app = _app_with_hello()
        resp = app.handle("GET", "/no-such-route", {}, b"", {})
        assert resp.status_code == 404
        assert "X-Correlation-ID" in resp.headers

    def test_header_propagated_from_request(self):
        """If the caller sends X-Correlation-ID, the same value is echoed back."""
        app = _app_with_hello()
        incoming_id = "abcd1234ef567890"
        resp = app.handle("GET", "/hello", {}, b"", {"X-Correlation-ID": incoming_id})
        assert resp.headers["X-Correlation-ID"] == incoming_id

    def test_header_present_on_error(self):
        """A 500 response (handler raises) must also carry X-Correlation-ID."""
        app = create_app()

        @app.route("/boom", methods=["GET"])
        def boom(req: Request) -> Response:
            """Always raises."""
            raise RuntimeError("intentional boom")

        resp = app.handle("GET", "/boom", {}, b"", {})
        assert resp.status_code == 500
        assert "X-Correlation-ID" in resp.headers

    def test_security_headers_present_on_success(self):
        """A successful response should include secure baseline headers."""
        app = _app_with_hello()
        resp = app.handle("GET", "/hello", {}, b"", {})
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert "default-src 'self'" in resp.headers["Content-Security-Policy"]

    def test_security_headers_present_on_not_found(self):
        """A 404 response should include secure baseline headers."""
        app = _app_with_hello()
        resp = app.handle("GET", "/missing", {}, b"", {})
        assert resp.status_code == 404
        assert resp.headers["Referrer-Policy"] == "no-referrer"


# ---------------------------------------------------------------------------
# Structured request logging
# ---------------------------------------------------------------------------


class TestRequestLogging:
    """Verify that _log_request emits valid JSON to the logger."""

    def test_log_request_is_valid_json(self, caplog):
        """_log_request must emit a JSON line containing the expected fields."""
        with caplog.at_level(logging.INFO, logger="civ_arcos.web"):
            _log_request("testcorr0001", "GET", "/api/status", 200, 12.5)

        assert caplog.records, "Expected at least one log record"
        record_text = caplog.records[-1].getMessage()
        data = json.loads(record_text)
        assert data["correlation_id"] == "testcorr0001"
        assert data["method"] == "GET"
        assert data["path"] == "/api/status"
        assert data["status"] == 200
        assert data["duration_ms"] == 12.5
        assert "ts" in data

    def test_handle_emits_log(self, caplog):
        """Application.handle must log one record per request."""
        app = _app_with_hello()
        with caplog.at_level(logging.INFO, logger="civ_arcos.web"):
            app.handle("GET", "/hello", {}, b"", {})

        assert any("civ_arcos.web" in r.name for r in caplog.records)

    def test_log_includes_status_code(self, caplog):
        """The log record must include the actual response status code."""
        app = _app_with_hello()
        with caplog.at_level(logging.INFO, logger="civ_arcos.web"):
            app.handle("GET", "/missing", {}, b"", {})

        last = caplog.records[-1].getMessage()
        data = json.loads(last)
        assert data["status"] == 404
