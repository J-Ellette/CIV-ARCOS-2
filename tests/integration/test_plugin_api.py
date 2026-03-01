"""Integration tests for plugin sandbox API endpoints."""

import json


def _handle(method: str, path: str, body: bytes = b"", headers=None, query=None):
    """Invoke API application handle directly."""
    from civ_arcos import api

    return api.app.handle(method, path, query or {}, body, headers or {})


def test_plugins_validate_accepts_safe_code() -> None:
    """Safe code should pass /api/plugins/validate."""
    payload = {"code": "def run(x):\n    return x + 1\n"}
    body = json.dumps(payload).encode()
    resp = _handle(
        "POST",
        "/api/plugins/validate",
        body,
        {"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["valid"] is True


def test_plugins_validate_rejects_forbidden_import() -> None:
    """Unsafe code should fail validation endpoint."""
    payload = {"code": "import subprocess\n\ndef run():\n    return 1\n"}
    body = json.dumps(payload).encode()
    resp = _handle(
        "POST",
        "/api/plugins/validate",
        body,
        {"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["valid"] is False


def test_plugins_execute_runs_function() -> None:
    """Execute endpoint should return plugin function result."""
    payload = {
        "code": "def triple(value):\n    return value * 3\n",
        "function": "triple",
        "kwargs": {"value": 5},
    }
    body = json.dumps(payload).encode()
    resp = _handle(
        "POST",
        "/api/plugins/execute",
        body,
        {"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["success"] is True
    assert data["result"] == 15


def test_plugins_execute_supports_idempotency_replay() -> None:
    """Same key and payload should replay first execute response."""
    payload = {
        "code": "def value():\n    return 7\n",
        "function": "value",
        "kwargs": {},
    }
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
        "Idempotency-Key": "plugin-execute-idem-001",
    }
    first = _handle("POST", "/api/plugins/execute", body, headers)
    second = _handle("POST", "/api/plugins/execute", body, headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert json.loads(first.body) == json.loads(second.body)
    assert second.headers.get("X-Idempotency-Replayed") == "true"


def test_plugins_execute_timeout_returns_408() -> None:
    """Long-running plugin should return timeout status."""
    payload = {
        "code": "import time\ndef run():\n    time.sleep(3)\n    return 1\n",
        "function": "run",
        "kwargs": {},
    }
    body = json.dumps(payload).encode()
    resp = _handle(
        "POST",
        "/api/plugins/execute",
        body,
        {"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    assert resp.status_code == 408
    data = json.loads(resp.body)
    assert data["timed_out"] is True


def test_plugins_v1_validate_contract_shape() -> None:
    """V1 validate endpoint should return plugin validation contract envelope."""
    payload = {"code": "def run(x):\n    return x + 1\n"}
    body = json.dumps(payload).encode()
    resp = _handle(
        "POST",
        "/api/v1/plugins/validate",
        body,
        {"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "PluginValidation"
    assert data["data"]["valid"] is True


def test_plugins_v1_execute_contract_shape() -> None:
    """V1 execute endpoint should return plugin execution contract envelope."""
    payload = {
        "code": "def plus_two(value):\n    return value + 2\n",
        "function": "plus_two",
        "kwargs": {"value": 9},
    }
    body = json.dumps(payload).encode()
    resp = _handle(
        "POST",
        "/api/v1/plugins/execute",
        body,
        {"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "PluginExecution"
    assert data["data"]["success"] is True
    assert data["data"]["result"] == 11


def test_plugins_register_and_registry_list_with_compatibility() -> None:
    """Compatible plugin registration should persist in registry list endpoints."""
    payload = {
        "code": "def run():\n    return 1\n",
        "manifest": {
            "name": "demo.compat.plugin",
            "version": "1.0.0",
            "target_api_version": "v1",
            "min_core_version": "0.1.0",
            "max_core_version": "0.2.0",
        },
    }
    body = json.dumps(payload).encode()

    registered = _handle(
        "POST",
        "/api/plugins/register",
        body,
        {"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    assert registered.status_code == 201
    reg_data = json.loads(registered.body)
    assert reg_data["plugin"]["manifest"]["name"] == "demo.compat.plugin"
    assert reg_data["validation"]["compatibility"]["compatible"] is True

    listed = _handle("GET", "/api/plugins/registry")
    assert listed.status_code == 200
    list_data = json.loads(listed.body)
    names = [entry["manifest"]["name"] for entry in list_data["plugins"]]
    assert "demo.compat.plugin" in names


def test_plugins_register_rejects_incompatible_version_constraints() -> None:
    """Registration should fail when manifest version constraints are incompatible."""
    payload = {
        "code": "def run():\n    return 1\n",
        "manifest": {
            "name": "demo.incompatible.plugin",
            "version": "1.0.0",
            "target_api_version": "v1",
            "min_core_version": "9.0.0",
        },
    }
    body = json.dumps(payload).encode()

    rejected = _handle(
        "POST",
        "/api/plugins/register",
        body,
        {"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    assert rejected.status_code == 400
    data = json.loads(rejected.body)
    assert "compatibility" in data["validation"]
    assert data["validation"]["compatibility"]["compatible"] is False


def test_plugins_v1_registry_contract_shape() -> None:
    """V1 plugin registry endpoint should return contract envelope payload."""
    resp = _handle("GET", "/api/v1/plugins/registry")
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "PluginRegistry"
    assert "plugins" in data["data"]
