"""Tests for plugin validator, compatibility, and sandbox isolation."""

from civ_arcos.core.plugin_marketplace import (
    PluginManifest,
    PluginRegistry,
    PluginSandbox,
    PluginValidator,
)


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


def test_registry_compatibility_accepts_matching_constraints() -> None:
    """Registry should accept manifests compatible with current core/api."""
    registry = PluginRegistry(core_version="0.1.0", api_version="v1")
    manifest = PluginManifest(
        name="quality.plugin",
        version="1.2.3",
        target_api_version="v1",
        min_core_version="0.1.0",
        max_core_version="0.2.0",
    )
    compatibility = registry.check_compatibility(manifest)
    assert compatibility.compatible is True
    assert compatibility.reasons == []


def test_registry_compatibility_rejects_core_version_mismatch() -> None:
    """Registry should reject manifests requiring a newer core version."""
    registry = PluginRegistry(core_version="0.1.0", api_version="v1")
    manifest = PluginManifest(
        name="future.plugin",
        version="1.0.0",
        target_api_version="v1",
        min_core_version="0.3.0",
    )
    compatibility = registry.check_compatibility(manifest)
    assert compatibility.compatible is False
    assert any("below minimum" in reason for reason in compatibility.reasons)


def test_registry_register_persists_compatible_manifest() -> None:
    """Compatible manifests should be persisted in registry entries."""
    registry = PluginRegistry(core_version="0.1.0", api_version="v1")
    manifest = PluginManifest(
        name="security.plugin",
        version="2.0.0",
        target_api_version="v1",
        min_core_version="0.1.0",
    )
    entry = registry.register(manifest, checksum="abc123")
    assert entry["manifest"]["name"] == "security.plugin"
    assert entry["checksum"] == "abc123"
    assert len(registry.list_entries()) == 1
