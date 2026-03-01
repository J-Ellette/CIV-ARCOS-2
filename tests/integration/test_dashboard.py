"""Integration tests for dashboard route rendering."""


def _handle_dashboard():
    """Invoke the dashboard endpoint through the in-process API app."""
    from civ_arcos import api

    return api.app.handle("GET", "/dashboard", {}, b"", {})


class TestDashboardRoute:
    """Tests for GET /dashboard route behavior."""

    def test_dashboard_route_returns_html(self):
        """Dashboard route should return HTTP 200 with HTML content type."""
        resp = _handle_dashboard()

        assert resp.status_code == 200
        assert resp.content_type == "text/html"

    def test_dashboard_contains_expected_carbon_markers(self):
        """Dashboard HTML should include expected Carbon page markers."""
        resp = _handle_dashboard()
        body = resp.body.decode("utf-8")

        assert "<!DOCTYPE html>" in body
        assert "CIV-ARCOS — Carbon Design System" in body
        assert 'data-carbon-theme="g100"' in body

    def test_dashboard_live_update_hooks_are_present(self):
        """Dashboard HTML should include STEP_08 live-update DOM hooks and logic."""
        resp = _handle_dashboard()
        body = resp.body.decode("utf-8")

        assert "dashboard-risk-blockchain-score" in body
        assert "dashboard-ledger-latest-index" in body
        assert "initDashboardLiveUpdates" in body
        assert "/api/sync/events" in body
