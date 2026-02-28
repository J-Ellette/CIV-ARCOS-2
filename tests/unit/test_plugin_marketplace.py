"""Tests for plugin validator and sandbox runtime isolation."""

from civ_arcos.core.plugin_marketplace import PluginSandbox, PluginValidator


def test_validator_accepts_simple_safe_plugin() -> None:
    """Safe plugin code should validate successfully."""
    code = "def run(x):\n    return x + 1\n"
    validator = PluginValidator()
    result = validator.validate(code)
    assert result.valid is True
    assert result.errors == []
    assert len(result.checksum) == 64


def test_validator_rejects_forbidden_import() -> None:
    """Forbidden imports should be blocked by static validation."""
    code = "import subprocess\n\ndef run():\n    return 1\n"
    validator = PluginValidator()
    result = validator.validate(code)
    assert result.valid is False
    assert any("Forbidden import" in msg for msg in result.errors)


def test_sandbox_executes_function_and_returns_result() -> None:
    """Sandbox should execute plugin function in isolated process."""
    code = "def transform(value):\n    return {'out': value * 2}\n"
    sandbox = PluginSandbox(timeout_secs=2.0)
    result = sandbox.execute(code, function_name="transform", kwargs={"value": 3})
    assert result.success is True
    assert result.result == {"out": 6}
    assert result.timed_out is False


def test_sandbox_reports_missing_function() -> None:
    """Missing function should produce a structured error."""
    code = "def run():\n    return 1\n"
    sandbox = PluginSandbox(timeout_secs=2.0)
    result = sandbox.execute(code, function_name="nope", kwargs={})
    assert result.success is False
    assert "Missing function" in result.error


def test_sandbox_times_out_long_running_plugin() -> None:
    """Long-running plugin code should be interrupted by timeout."""
    code = "import time\n" "def run():\n" "    time.sleep(0.2)\n" "    return 1\n"
    sandbox = PluginSandbox(timeout_secs=0.01)
    result = sandbox.execute(code, function_name="run", kwargs={})
    assert result.success is False
    assert result.timed_out is True
