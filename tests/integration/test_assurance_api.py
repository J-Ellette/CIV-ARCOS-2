"""Integration tests for assurance API routes."""
import json
import pytest

from civ_arcos import api


def handle(method, path, query=None, body=None):
    body_bytes = json.dumps(body).encode() if body else b""
    return api.app.handle(method, path, query or {}, body_bytes, {})


def test_list_templates():
    resp = handle("GET", "/api/assurance/templates")
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert "templates" in data
    assert len(data["templates"]) >= 4


def test_create_assurance_case():
    resp = handle("POST", "/api/assurance/create", body={
        "project_name": "TestProject",
        "project_type": "library",
        "template": "code_quality",
    })
    assert resp.status_code == 201
    data = json.loads(resp.body)
    assert "case_id" in data
    assert data["node_count"] > 0


def test_get_assurance_case():
    # Create first
    resp = handle("POST", "/api/assurance/create", body={
        "project_name": "GetProject",
        "template": "test_coverage",
    })
    case_id = json.loads(resp.body)["case_id"]

    resp2 = handle("GET", f"/api/assurance/{case_id}")
    assert resp2.status_code == 200
    data = json.loads(resp2.body)
    assert data["case_id"] == case_id


def test_get_assurance_case_not_found():
    resp = handle("GET", "/api/assurance/nonexistent-id-xyz")
    assert resp.status_code == 404


def test_visualize_summary():
    resp = handle("POST", "/api/assurance/create", body={
        "project_name": "VizProject",
        "template": "code_quality",
    })
    case_id = json.loads(resp.body)["case_id"]

    resp2 = handle("GET", f"/api/assurance/{case_id}/visualize",
                   query={"format": ["summary"]})
    assert resp2.status_code == 200
    data = json.loads(resp2.body)
    assert "node_count" in data


def test_auto_generate_case():
    resp = handle("POST", "/api/assurance/auto-generate", body={
        "project_name": "AutoProject",
        "project_type": "general",
        "evidence_ids": [],
    })
    assert resp.status_code == 201
    data = json.loads(resp.body)
    assert "case_id" in data
