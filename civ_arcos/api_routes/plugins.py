"""Plugin management routes for legacy and v1 APIs."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable, Dict

from civ_arcos.contracts.v1 import (
    plugin_execution_contract,
    plugin_registration_contract,
    plugin_registry_contract,
    plugin_validation_contract,
)
from civ_arcos.core.plugin_marketplace import (
    PluginManifest,
    PluginRegistry,
    PluginSandbox,
    PluginValidator,
)
from civ_arcos.web.framework import Application, Request, Response


def _validate_payload(
    validator: PluginValidator,
    registry: PluginRegistry,
    code: str,
    manifest_data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate plugin source code and return serialized payload."""
    result = validator.validate(code)

    payload: Dict[str, Any] = {
        "valid": result.valid,
        "checksum": result.checksum,
        "errors": result.errors,
    }

    manifest_data = manifest_data or {}
    if manifest_data:
        manifest = PluginManifest(
            name=str(manifest_data.get("name", "")).strip(),
            version=str(manifest_data.get("version", "")).strip(),
            target_api_version=str(
                manifest_data.get("target_api_version", registry.api_version)
            ).strip(),
            min_core_version=str(
                manifest_data.get("min_core_version", "0.1.0")
            ).strip(),
            max_core_version=(
                str(manifest_data.get("max_core_version", "")).strip() or None
            ),
        )
        compatibility = registry.check_compatibility(manifest)
        payload["manifest"] = asdict(manifest)
        payload["compatibility"] = asdict(compatibility)

    return payload


def _execute_payload(
    validator: PluginValidator,
    registry: PluginRegistry,
    sandbox: PluginSandbox,
    code: str,
    function_name: str,
    kwargs: Dict[str, Any],
    manifest_data: Dict[str, Any] | None = None,
) -> tuple[int, Dict[str, Any]]:
    """Execute plugin code and return status code + structured payload."""
    validation = _validate_payload(validator, registry, code, manifest_data=manifest_data)
    if not validation["valid"]:
        return 400, {
            "error": "Plugin validation failed",
            "validation": validation,
        }
    compatibility = validation.get("compatibility")
    if compatibility and not compatibility.get("compatible", False):
        return 400, {
            "error": "Plugin compatibility check failed",
            "validation": validation,
        }

    outcome = sandbox.execute(code, function_name=function_name, kwargs=kwargs)
    status_code = 200 if outcome.success else 400
    if outcome.timed_out:
        status_code = 408

    return status_code, {
        "success": outcome.success,
        "result": outcome.result,
        "error": outcome.error,
        "timed_out": outcome.timed_out,
        "stdout": outcome.stdout,
        "stderr": outcome.stderr,
        "validation": validation,
    }


def register_plugin_legacy_routes(
    app: Application,
    validator: PluginValidator,
    registry: PluginRegistry,
    sandbox: PluginSandbox,
    idempotency_precheck: Callable[[Request], Response | None],
    idempotency_store: Callable[[Request, Response], None],
) -> None:
    """Register legacy plugin endpoints under ``/api/plugins``."""

    @app.route("/api/plugins/validate", methods=["POST"])
    def plugins_validate(req: Request) -> Response:
        body = req.json() or {}
        code = body.get("code", "")
        manifest = body.get("manifest", {})
        if not isinstance(manifest, dict):
            return Response({"error": "manifest must be an object"}, status_code=400)
        return Response(
            _validate_payload(validator, registry, code, manifest_data=manifest)
        )

    @app.route("/api/plugins/register", methods=["POST"])
    def plugins_register(req: Request) -> Response:
        body = req.json() or {}
        code = body.get("code", "")
        manifest = body.get("manifest", {})

        if not isinstance(manifest, dict):
            return Response({"error": "manifest must be an object"}, status_code=400)
        if not str(manifest.get("name", "")).strip():
            return Response(
                {"error": "manifest.name is required"},
                status_code=400,
            )

        validation = _validate_payload(validator, registry, code, manifest_data=manifest)
        if not validation["valid"]:
            return Response(
                {"error": "Plugin validation failed", "validation": validation},
                status_code=400,
            )
        compatibility = validation.get("compatibility", {})
        if compatibility and not compatibility.get("compatible", False):
            return Response(
                {
                    "error": "Plugin compatibility check failed",
                    "validation": validation,
                },
                status_code=400,
            )

        plugin_manifest = PluginManifest(
            name=str(manifest.get("name", "")).strip(),
            version=str(manifest.get("version", "")).strip(),
            target_api_version=str(
                manifest.get("target_api_version", registry.api_version)
            ).strip(),
            min_core_version=str(manifest.get("min_core_version", "0.1.0")).strip(),
            max_core_version=(str(manifest.get("max_core_version", "")).strip() or None),
        )
        try:
            entry = registry.register(plugin_manifest, checksum=validation["checksum"])
        except ValueError:
            return Response(
                {
                    "error": "Plugin compatibility check failed",
                    "validation": validation,
                },
                status_code=400,
            )
        return Response({"plugin": entry, "validation": validation}, status_code=201)

    @app.route("/api/plugins/registry", methods=["GET"])
    def plugins_registry(req: Request) -> Response:
        return Response(
            {
                "core_version": registry.core_version,
                "api_version": registry.api_version,
                "count": len(registry.list_entries()),
                "plugins": registry.list_entries(),
            }
        )

    @app.route("/api/plugins/execute", methods=["POST"])
    def plugins_execute(req: Request) -> Response:
        replay_resp = idempotency_precheck(req)
        if replay_resp is not None:
            return replay_resp

        body = req.json() or {}
        code = body.get("code", "")
        function_name = body.get("function", "")
        kwargs = body.get("kwargs", {})
        manifest = body.get("manifest", {})

        if not function_name:
            return Response({"error": "function is required"}, status_code=400)
        if not isinstance(kwargs, dict):
            return Response({"error": "kwargs must be an object"}, status_code=400)
        if manifest and not isinstance(manifest, dict):
            return Response({"error": "manifest must be an object"}, status_code=400)

        status_code, payload = _execute_payload(
            validator,
            registry,
            sandbox,
            code,
            function_name,
            kwargs,
            manifest_data=manifest,
        )
        response = Response(payload, status_code=status_code)
        idempotency_store(req, response)
        return response


def register_plugin_v1_routes(
    app: Application,
    validator: PluginValidator,
    registry: PluginRegistry,
    sandbox: PluginSandbox,
    idempotency_precheck: Callable[[Request], Response | None],
    idempotency_store: Callable[[Request, Response], None],
) -> None:
    """Register versioned plugin endpoints under ``/api/v1/plugins``."""

    @app.route("/api/v1/plugins/validate", methods=["POST"])
    def plugins_validate_v1(req: Request) -> Response:
        body = req.json() or {}
        code = body.get("code", "")
        manifest = body.get("manifest", {})
        if not isinstance(manifest, dict):
            return Response({"error": "manifest must be an object"}, status_code=400)
        return Response(
            plugin_validation_contract(
                _validate_payload(validator, registry, code, manifest_data=manifest)
            )
        )

    @app.route("/api/v1/plugins/register", methods=["POST"])
    def plugins_register_v1(req: Request) -> Response:
        body = req.json() or {}
        code = body.get("code", "")
        manifest = body.get("manifest", {})

        if not isinstance(manifest, dict):
            return Response({"error": "manifest must be an object"}, status_code=400)
        if not str(manifest.get("name", "")).strip():
            return Response(
                {"error": "manifest.name is required"},
                status_code=400,
            )

        validation = _validate_payload(validator, registry, code, manifest_data=manifest)
        if not validation["valid"]:
            return Response(
                {"error": "Plugin validation failed", "validation": validation},
                status_code=400,
            )
        compatibility = validation.get("compatibility", {})
        if compatibility and not compatibility.get("compatible", False):
            return Response(
                {
                    "error": "Plugin compatibility check failed",
                    "validation": validation,
                },
                status_code=400,
            )

        plugin_manifest = PluginManifest(
            name=str(manifest.get("name", "")).strip(),
            version=str(manifest.get("version", "")).strip(),
            target_api_version=str(
                manifest.get("target_api_version", registry.api_version)
            ).strip(),
            min_core_version=str(manifest.get("min_core_version", "0.1.0")).strip(),
            max_core_version=(str(manifest.get("max_core_version", "")).strip() or None),
        )
        try:
            entry = registry.register(plugin_manifest, checksum=validation["checksum"])
        except ValueError:
            return Response(
                {
                    "error": "Plugin compatibility check failed",
                    "validation": validation,
                },
                status_code=400,
            )

        return Response(
            plugin_registration_contract({"plugin": entry, "validation": validation}),
            status_code=201,
        )

    @app.route("/api/v1/plugins/registry", methods=["GET"])
    def plugins_registry_v1(req: Request) -> Response:
        return Response(
            plugin_registry_contract(
                {
                    "core_version": registry.core_version,
                    "api_version": registry.api_version,
                    "count": len(registry.list_entries()),
                    "plugins": registry.list_entries(),
                }
            )
        )

    @app.route("/api/v1/plugins/execute", methods=["POST"])
    def plugins_execute_v1(req: Request) -> Response:
        replay_resp = idempotency_precheck(req)
        if replay_resp is not None:
            return replay_resp

        body = req.json() or {}
        code = body.get("code", "")
        function_name = body.get("function", "")
        kwargs = body.get("kwargs", {})
        manifest = body.get("manifest", {})

        if not function_name:
            return Response({"error": "function is required"}, status_code=400)
        if not isinstance(kwargs, dict):
            return Response({"error": "kwargs must be an object"}, status_code=400)
        if manifest and not isinstance(manifest, dict):
            return Response({"error": "manifest must be an object"}, status_code=400)

        status_code, payload = _execute_payload(
            validator,
            registry,
            sandbox,
            code,
            function_name,
            kwargs,
            manifest_data=manifest,
        )
        response = Response(plugin_execution_contract(payload), status_code=status_code)
        idempotency_store(req, response)
        return response
