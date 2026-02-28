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


def _request_tenant_id(req: Request) -> str:
    """Return normalized tenant identifier from request headers."""
    return (
        req.headers.get("X-Tenant-ID") or req.headers.get("x-tenant-id", "")
    ).strip()


def _tenant_exists(tenants: List[Dict[str, Any]], tenant_id: str) -> bool:
    """Return ``True`` when tenant ID exists in configured tenant registry."""
    return any(tenant.get("id") == tenant_id for tenant in tenants)


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

    @app.route("/api/tenants", methods=["GET"])
    def tenants_list(req: Request) -> Response:
        return Response({"tenants": tenants, "count": len(tenants)})

    @app.route("/api/tenants", methods=["POST"])
    def tenants_create(req: Request) -> Response:
        body = req.json() or {}
        name = body.get("name", "").strip()
        if not name:
            return Response({"error": "name is required"}, status_code=400)
        tenant_id = name.lower().replace(" ", "_")
        tenant = {
            "id": tenant_id,
            "name": name,
            "plan": body.get("plan", "free"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        tenants.append(tenant)
        return Response(tenant, status_code=201)

    @app.route("/api/settings", methods=["GET"])
    def settings_get(req: Request) -> Response:
        return Response(_settings_payload(settings_store, config_provider))

    @app.route("/api/settings", methods=["POST"])
    def settings_update(req: Request) -> Response:
        body = req.json() or {}
        allowed = {"host", "port", "db_path", "log_level", "github_token"}
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
        name = body.get("name", "").strip()
        if not name:
            return Response({"error": "name is required"}, status_code=400)

        tenant_id = name.lower().replace(" ", "_")
        tenant = {
            "id": tenant_id,
            "name": name,
            "plan": body.get("plan", "free"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        tenants.append(tenant)

        response = Response(tenant_detail_contract(tenant), status_code=201)
        idempotency_store(req, response)
        return response

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
        target_tenant_id = (body.get("tenant_id") or actor_tenant_id).strip()
        if target_tenant_id != actor_tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)

        allowed = {"host", "port", "db_path", "log_level", "github_token"}
        updated_keys = []
        tenant_bucket = _tenant_settings_bucket(settings_store)
        tenant_overrides = tenant_bucket.setdefault(target_tenant_id, {})
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
