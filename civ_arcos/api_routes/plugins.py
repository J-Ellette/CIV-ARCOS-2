"""Plugin management routes for legacy and v1 APIs."""

from __future__ import annotations

from typing import Any, Callable, Dict

from civ_arcos.contracts.v1 import (
    plugin_execution_contract,
    plugin_validation_contract,
)
from civ_arcos.core.plugin_marketplace import PluginSandbox, PluginValidator
from civ_arcos.web.framework import Application, Request, Response


def _validate_payload(
    validator: PluginValidator,
    code: str,
) -> Dict[str, Any]:
    """Validate plugin source code and return serialized payload."""
    result = validator.validate(code)
    return {
        "valid": result.valid,
        "checksum": result.checksum,
        "errors": result.errors,
    }


def _execute_payload(
    validator: PluginValidator,
    sandbox: PluginSandbox,
    code: str,
    function_name: str,
    kwargs: Dict[str, Any],
) -> tuple[int, Dict[str, Any]]:
    """Execute plugin code and return status code + structured payload."""
    validation = _validate_payload(validator, code)
    if not validation["valid"]:
        return 400, {
            "error": "Plugin validation failed",
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
    sandbox: PluginSandbox,
    idempotency_precheck: Callable[[Request], Response | None],
    idempotency_store: Callable[[Request, Response], None],
) -> None:
    """Register legacy plugin endpoints under ``/api/plugins``."""

    @app.route("/api/plugins/validate", methods=["POST"])
    def plugins_validate(req: Request) -> Response:
        body = req.json() or {}
        code = body.get("code", "")
        return Response(_validate_payload(validator, code))

    @app.route("/api/plugins/execute", methods=["POST"])
    def plugins_execute(req: Request) -> Response:
        replay_resp = idempotency_precheck(req)
        if replay_resp is not None:
            return replay_resp

        body = req.json() or {}
        code = body.get("code", "")
        function_name = body.get("function", "")
        kwargs = body.get("kwargs", {})

        if not function_name:
            return Response({"error": "function is required"}, status_code=400)
        if not isinstance(kwargs, dict):
            return Response({"error": "kwargs must be an object"}, status_code=400)

        status_code, payload = _execute_payload(
            validator,
            sandbox,
            code,
            function_name,
            kwargs,
        )
        response = Response(payload, status_code=status_code)
        idempotency_store(req, response)
        return response


def register_plugin_v1_routes(
    app: Application,
    validator: PluginValidator,
    sandbox: PluginSandbox,
    idempotency_precheck: Callable[[Request], Response | None],
    idempotency_store: Callable[[Request, Response], None],
) -> None:
    """Register versioned plugin endpoints under ``/api/v1/plugins``."""

    @app.route("/api/v1/plugins/validate", methods=["POST"])
    def plugins_validate_v1(req: Request) -> Response:
        body = req.json() or {}
        code = body.get("code", "")
        return Response(plugin_validation_contract(_validate_payload(validator, code)))

    @app.route("/api/v1/plugins/execute", methods=["POST"])
    def plugins_execute_v1(req: Request) -> Response:
        replay_resp = idempotency_precheck(req)
        if replay_resp is not None:
            return replay_resp

        body = req.json() or {}
        code = body.get("code", "")
        function_name = body.get("function", "")
        kwargs = body.get("kwargs", {})

        if not function_name:
            return Response({"error": "function is required"}, status_code=400)
        if not isinstance(kwargs, dict):
            return Response({"error": "kwargs must be an object"}, status_code=400)

        status_code, payload = _execute_payload(
            validator,
            sandbox,
            code,
            function_name,
            kwargs,
        )
        response = Response(plugin_execution_contract(payload), status_code=status_code)
        idempotency_store(req, response)
        return response
