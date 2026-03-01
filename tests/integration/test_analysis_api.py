"""Integration tests for analysis API routes."""

import json
import os
import tempfile
import pytest

from civ_arcos import api


def handle(method, path, query=None, body=None):
    body_bytes = json.dumps(body).encode() if body else b""
    return api.app.handle(method, path, query or {}, body_bytes, {})


def test_analysis_static_route_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "mod.py"), "w") as fh:
            fh.write("def foo():\n    return 1\n")
        resp = handle("POST", "/api/analysis/static", body={"source_path": tmpdir})
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert "results" in data
        assert data["file_count"] == 1


def test_analysis_security_route_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "safe.py"), "w") as fh:
            fh.write("x = 1\n")
        resp = handle("POST", "/api/analysis/security", body={"source_path": tmpdir})
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert "score" in data
        assert data["score"]["score"] == 100


def test_analysis_tests_route_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "mod.py"), "w") as fh:
            fh.write("def bar(x):\n    return x * 2\n")
        resp = handle("POST", "/api/analysis/tests", body={"source_path": tmpdir})
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert "results" in data


def test_analysis_tests_route_ai_opt_in_disabled_falls_back(monkeypatch):
    monkeypatch.delenv("CIV_AI_ENABLE", raising=False)
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "mod.py"), "w") as fh:
            fh.write("def bar(x):\n    return x * 2\n")
        resp = handle(
            "POST",
            "/api/analysis/tests",
            body={
                "source_path": tmpdir,
                "use_ai": True,
                "llm_backend": "azure_openai",
            },
        )
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["results"]
        first = data["results"][0]
        assert first["ai_enabled"] is False
        assert first["ai_backend"] == "mock"


def test_analysis_comprehensive_route_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "mod.py"), "w") as fh:
            fh.write("def baz():\n    pass\n")
        resp = handle(
            "POST", "/api/analysis/comprehensive", body={"source_path": tmpdir}
        )
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert "evidence_collected" in data
        assert data["evidence_collected"] >= 1
