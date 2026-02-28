"""Integration tests for the REST API."""
import json
import pytest
from civ_arcos.web.framework import Application, Request, Response, create_app


def make_request(method="GET", path="/", body=None, query_params=None):
    return Request(
        method=method,
        path=path,
        query_params=query_params or {},
        body=json.dumps(body).encode() if body else b"",
        headers={"Content-Type": "application/json"}
    )


def test_index_route():
    from civ_arcos import api
    req = make_request("GET", "/")
    resp = api.app.handle("GET", "/", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert "CIV-ARCOS" in data["name"]


def test_status_route():
    from civ_arcos import api
    resp = api.app.handle("GET", "/api/status", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert "uptime_seconds" in data
    assert "version" in data


def test_not_found_route():
    from civ_arcos import api
    resp = api.app.handle("GET", "/no/such/path", {}, b"", {})
    assert resp.status_code == 404


def test_blockchain_status_route():
    from civ_arcos import api
    resp = api.app.handle("GET", "/api/blockchain/status", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert "length" in data
    assert data["valid"] is True


def test_badge_coverage_route():
    from civ_arcos import api
    resp = api.app.handle("GET", "/api/badge/coverage/owner/repo",
                          {"coverage": ["95.0"]}, b"", {})
    assert resp.status_code == 200
    body = resp.body.decode()
    assert "<svg" in body


def test_collect_evidence_mock():
    from civ_arcos import api
    body = json.dumps({"repo_url": "https://github.com/nonexistent/repo"}).encode()
    resp = api.app.handle("POST", "/api/evidence/collect", {}, body,
                          {"Content-Type": "application/json",
                           "Content-Length": str(len(body))})
    assert resp.status_code == 201
    data = json.loads(resp.body)
    assert "collected" in data
