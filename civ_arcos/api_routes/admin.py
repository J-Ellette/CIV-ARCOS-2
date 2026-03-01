"""Admin domain routes for tenants and settings."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

from civ_arcos.contracts.v1 import (
    settings_state_contract,
    settings_update_contract,
    tenant_detail_contract,
    tenants_list_contract,
)
from civ_arcos.core.config import Config
from civ_arcos.web.framework import Application, Request, Response

TENANT_SETTINGS_KEY = "__tenant_settings__"


def _parse_required_string(
    raw_value: Any,
    field_name: str,
) -> tuple[str | None, Response | None]:
    """Validate and normalize a required string field from request payload."""
    if not isinstance(raw_value, str):
        return None, Response({"error": f"{field_name} must be a string"}, status_code=400)
    normalized = raw_value.strip()
    if not normalized:
        return None, Response({"error": f"{field_name} is required"}, status_code=400)
    return normalized, None


def _parse_optional_string(
    raw_value: Any,
    field_name: str,
) -> tuple[str | None, Response | None]:
    """Validate and normalize an optional string field from request payload."""
    if raw_value is None:
        return None, None
    if not isinstance(raw_value, str):
        return None, Response({"error": f"{field_name} must be a string"}, status_code=400)
    return raw_value.strip(), None


def _parse_port(
    raw_value: Any,
) -> tuple[int | None, Response | None]:
    """Validate and normalize a TCP port value from request payload."""
    try:
        port = int(raw_value)
    except (TypeError, ValueError):
        return None, Response({"error": "port must be an integer"}, status_code=400)

    if port < 1 or port > 65535:
        return None, Response({"error": "port must be between 1 and 65535"}, status_code=400)
    return port, None


def _request_tenant_id(req: Request) -> str:
    """Return normalized tenant identifier from request headers."""
    return (
        req.headers.get("X-Tenant-ID") or req.headers.get("x-tenant-id", "")
    ).strip()


def _tenant_exists(tenants: List[Dict[str, Any]], tenant_id: str) -> bool:
    """Return ``True`` when tenant ID exists in configured tenant registry."""
    return any(tenant.get("id") == tenant_id for tenant in tenants)


def _find_tenant(
    tenants: List[Dict[str, Any]], tenant_id: str
) -> Dict[str, Any] | None:
    """Return tenant record by ID or ``None`` when not found."""
    return next((tenant for tenant in tenants if tenant.get("id") == tenant_id), None)


def _tenant_settings_bucket(
    settings_store: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Return mutable tenant settings bucket from backing store."""
    bucket = settings_store.get(TENANT_SETTINGS_KEY)
    if isinstance(bucket, dict):
        return bucket
    bucket = {}
    settings_store[TENANT_SETTINGS_KEY] = bucket
    return bucket


def _settings_payload(
    settings_overrides: Dict[str, Any],
    config_provider: Callable[[], Config],
) -> Dict[str, Any]:
    """Build effective settings payload from runtime overrides + base config."""
    config = config_provider()
    return {
        "host": settings_overrides.get("host", config.host),
        "port": settings_overrides.get("port", config.port),
        "db_path": settings_overrides.get("db_path", config.db_path),
        "log_level": settings_overrides.get("log_level", config.log_level),
        "github_token_set": bool(
            settings_overrides.get("github_token") or config.github_token
        ),
    }


def register_admin_legacy_routes(
    app: Application,
    tenants: List[Dict[str, Any]],
    settings_store: Dict[str, Any],
    config_provider: Callable[[], Config],
) -> None:
    """Register legacy admin routes under ``/api``."""

    def _tenant_list_payload() -> Dict[str, Any]:
        """Build legacy tenant list payload."""
        return {"tenants": tenants, "count": len(tenants)}

    def _tenant_create_payload(req: Request) -> Response:
        """Create one legacy tenant from request body."""
        body = req.json() or {}
        name, name_error = _parse_required_string(body.get("name"), "name")
        if name_error is not None:
            return name_error
        assert name is not None

        plan, plan_error = _parse_optional_string(body.get("plan"), "plan")
        if plan_error is not None:
            return plan_error
        tenant_id = name.lower().replace(" ", "_")
        tenant = {
            "id": tenant_id,
            "name": name,
            "plan": plan or "free",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        tenants.append(tenant)
        return Response(tenant, status_code=201)

    @app.route("/api/tenants", methods=["GET"])
    def tenants_list(req: Request) -> Response:
        return Response(_tenant_list_payload())

    @app.route("/api/tenants/list", methods=["GET"])
    def tenants_list_alias(req: Request) -> Response:
        return Response(_tenant_list_payload())

    @app.route("/api/tenants", methods=["POST"])
    def tenants_create(req: Request) -> Response:
        return _tenant_create_payload(req)

    @app.route("/api/tenants/create", methods=["POST"])
    def tenants_create_alias(req: Request) -> Response:
        return _tenant_create_payload(req)

    @app.route("/api/tenants/{tenant_id}", methods=["GET"])
    def tenant_detail(req: Request, tenant_id: str = "") -> Response:
        tenant = next((item for item in tenants if item.get("id") == tenant_id), None)
        if tenant is None:
            return Response({"error": "Tenant not found"}, status_code=404)
        return Response(tenant)

    @app.route("/api/settings", methods=["GET"])
    def settings_get(req: Request) -> Response:
        return Response(_settings_payload(settings_store, config_provider))

    @app.route("/api/settings", methods=["POST"])
    def settings_update(req: Request) -> Response:
        body = req.json() or {}
        allowed = {"host", "port", "db_path", "log_level", "github_token"}
        if "port" in body:
            parsed_port, port_error = _parse_port(body.get("port"))
            if port_error is not None:
                return port_error
            assert parsed_port is not None
            body["port"] = parsed_port
        for key in allowed:
            if key in body:
                settings_store[key] = body[key]
        return Response({"updated": True, "keys": list(body.keys())})


def register_admin_v1_routes(
    app: Application,
    tenants: List[Dict[str, Any]],
    settings_store: Dict[str, Any],
    config_provider: Callable[[], Config],
    idempotency_precheck: Callable[[Request], Response | None],
    idempotency_store: Callable[[Request, Response], None],
) -> None:
    """Register versioned admin routes under ``/api/v1``."""

    @app.route("/api/v1/tenants", methods=["GET"])
    def tenants_list_v1(req: Request) -> Response:
        actor_tenant_id = _request_tenant_id(req)
        requested_tenant_id = req.query("tenant_id", "").strip()

        if actor_tenant_id:
            if not _tenant_exists(tenants, actor_tenant_id):
                return Response({"error": "Unknown tenant"}, status_code=403)
            if requested_tenant_id and requested_tenant_id != actor_tenant_id:
                return Response(
                    {"error": "Cross-tenant access denied"}, status_code=403
                )
            scoped_tenant_id = requested_tenant_id or actor_tenant_id
            scoped = [
                tenant for tenant in tenants if tenant.get("id") == scoped_tenant_id
            ]
            return Response(tenants_list_contract(scoped))

        if requested_tenant_id:
            scoped = [
                tenant for tenant in tenants if tenant.get("id") == requested_tenant_id
            ]
            return Response(tenants_list_contract(scoped))

        return Response(tenants_list_contract(tenants))

    @app.route("/api/v1/tenants", methods=["POST"])
    def tenants_create_v1(req: Request) -> Response:
        replay_resp = idempotency_precheck(req)
        if replay_resp is not None:
            return replay_resp

        body = req.json() or {}
        name, name_error = _parse_required_string(body.get("name"), "name")
        if name_error is not None:
            return name_error
        assert name is not None

        plan, plan_error = _parse_optional_string(body.get("plan"), "plan")
        if plan_error is not None:
            return plan_error

        tenant_id = name.lower().replace(" ", "_")
        tenant = {
            "id": tenant_id,
            "name": name,
            "plan": plan or "free",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        tenants.append(tenant)

        response = Response(tenant_detail_contract(tenant), status_code=201)
        idempotency_store(req, response)
        return response

    @app.route("/api/v1/tenants/{tenant_id}", methods=["GET"])
    def tenant_detail_v1(req: Request, tenant_id: str = "") -> Response:
        actor_tenant_id = _request_tenant_id(req)
        if actor_tenant_id:
            if not _tenant_exists(tenants, actor_tenant_id):
                return Response({"error": "Unknown tenant"}, status_code=403)
            if tenant_id != actor_tenant_id:
                return Response(
                    {"error": "Cross-tenant access denied"}, status_code=403
                )

        tenant = _find_tenant(tenants, tenant_id)
        if tenant is None:
            return Response({"error": "Tenant not found"}, status_code=404)
        return Response(tenant_detail_contract(tenant))

    @app.route("/api/v1/settings", methods=["GET"])
    def settings_get_v1(req: Request) -> Response:
        actor_tenant_id = _request_tenant_id(req)
        if not actor_tenant_id:
            return Response(
                {"error": "X-Tenant-ID header is required"}, status_code=401
            )
        if not _tenant_exists(tenants, actor_tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)

        requested_tenant_id = req.query("tenant_id", "").strip() or actor_tenant_id
        if requested_tenant_id != actor_tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)

        tenant_overrides = _tenant_settings_bucket(settings_store).get(
            requested_tenant_id, {}
        )
        payload = _settings_payload(tenant_overrides, config_provider)
        payload["tenant_id"] = requested_tenant_id
        return Response(settings_state_contract(payload))

    @app.route("/api/v1/settings", methods=["POST"])
    def settings_update_v1(req: Request) -> Response:
        replay_resp = idempotency_precheck(req)
        if replay_resp is not None:
            return replay_resp

        actor_tenant_id = _request_tenant_id(req)
        if not actor_tenant_id:
            return Response(
                {"error": "X-Tenant-ID header is required"}, status_code=401
            )
        if not _tenant_exists(tenants, actor_tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)

        body = req.json() or {}
        requested_tenant_id, tenant_error = _parse_optional_string(
            body.get("tenant_id"),
            "tenant_id",
        )
        if tenant_error is not None:
            return tenant_error
        target_tenant_id = requested_tenant_id or actor_tenant_id
        if target_tenant_id != actor_tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)

        allowed = {"host", "port", "db_path", "log_level", "github_token"}
        updated_keys = []
        tenant_bucket = _tenant_settings_bucket(settings_store)
        tenant_overrides = tenant_bucket.setdefault(target_tenant_id, {})
        if "port" in body:
            parsed_port, port_error = _parse_port(body.get("port"))
            if port_error is not None:
                return port_error
            assert parsed_port is not None
            body["port"] = parsed_port
        for key in allowed:
            if key in body:
                tenant_overrides[key] = body[key]
                updated_keys.append(key)

        payload = {
            "updated": True,
            "keys": updated_keys,
            "tenant_id": target_tenant_id,
            "settings": _settings_payload(tenant_overrides, config_provider),
        }
        response = Response(settings_update_contract(payload))
        idempotency_store(req, response)
        return response
