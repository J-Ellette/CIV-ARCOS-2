"""Versioned evidence API routes."""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from civ_arcos.adapters.github_adapter import GitHubCollector
from civ_arcos.contracts.v1 import (
    evidence_collection_contract,
    evidence_detail_contract,
    evidence_list_contract,
)
from civ_arcos.distributed.blockchain_ledger import BlockchainLedger
from civ_arcos.evidence.collector import EvidenceStore
from civ_arcos.core.config import Config
from civ_arcos.web.framework import Application, Request, Response


def _parse_optional_string(
    raw_value: Any,
    field_name: str,
) -> tuple[str | None, Response | None]:
    """Validate and normalize an optional string request field."""
    if raw_value is None:
        return None, None
    if not isinstance(raw_value, str):
        return None, Response({"error": f"{field_name} must be a string"}, status_code=400)
    return raw_value.strip(), None


def _parse_required_string(
    raw_value: Any,
    field_name: str,
) -> tuple[str | None, Response | None]:
    """Validate and normalize a required string request field."""
    normalized, error = _parse_optional_string(raw_value, field_name)
    if error is not None:
        return None, error
    if not normalized:
        return None, Response({"error": f"{field_name} is required"}, status_code=400)
    return normalized, None


def _request_tenant_id(req: Request) -> str:
    return (
        req.headers.get("X-Tenant-ID") or req.headers.get("x-tenant-id", "")
    ).strip()


def _tenant_exists(tenants: List[Dict[str, Any]], tenant_id: str) -> bool:
    return any(tenant.get("id") == tenant_id for tenant in tenants)


def register_evidence_v1_routes(
    app: Application,
    store: EvidenceStore,
    ledger: BlockchainLedger,
    tenants: List[Dict[str, Any]],
    config_provider: Callable[[], Config],
    idempotency_precheck: Callable[[Request], Response | None],
    idempotency_store: Callable[[Request, Response], None],
) -> None:
    """Register ``/api/v1/evidence`` endpoints."""

    @app.route("/api/v1/evidence/collect", methods=["POST"])
    def evidence_collect_v1(req: Request) -> Response:
        replay_resp = idempotency_precheck(req)
        if replay_resp is not None:
            return replay_resp

        tenant_id = _request_tenant_id(req)
        if not tenant_id:
            return Response(
                {"error": "X-Tenant-ID header is required"}, status_code=401
            )
        if not _tenant_exists(tenants, tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)

        body = req.json() or {}
        if not isinstance(body, dict):
            return Response({"error": "request body must be an object"}, status_code=400)

        repo_url, repo_error = _parse_required_string(body.get("repo_url"), "repo_url")
        if repo_error is not None:
            return repo_error
        token, token_error = _parse_optional_string(body.get("token"), "token")
        if token_error is not None:
            return token_error
        assert repo_url is not None

        config = config_provider()
        collector = GitHubCollector(token=token or config.github_token or None)
        evidence_list = collector.collect(repo_url=repo_url)

        node_ids = []
        evidence_ids = []
        for evidence in evidence_list:
            evidence.provenance["tenant_id"] = tenant_id
            graph_node_id = store.store_evidence(evidence)
            ledger.add_block(
                {
                    "evidence_id": evidence.id,
                    "checksum": evidence.checksum,
                    "tenant_id": tenant_id,
                }
            )
            node_ids.append(graph_node_id)
            evidence_ids.append(evidence.id)

        response = Response(
            evidence_collection_contract(
                {
                    "collected": len(evidence_list),
                    "node_ids": node_ids,
                    "evidence_ids": evidence_ids,
                    "tenant_id": tenant_id,
                }
            ),
            status_code=201,
        )
        idempotency_store(req, response)
        return response

    @app.route("/api/v1/evidence", methods=["GET"])
    def evidence_list_v1(req: Request) -> Response:
        tenant_id = _request_tenant_id(req)
        requested_tenant_id = req.query("tenant_id", "").strip()
        if requested_tenant_id and not _tenant_exists(tenants, requested_tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)

        if tenant_id:
            if not _tenant_exists(tenants, tenant_id):
                return Response({"error": "Unknown tenant"}, status_code=403)
            if requested_tenant_id and requested_tenant_id != tenant_id:
                return Response(
                    {"error": "Cross-tenant access denied"}, status_code=403
                )
            evidence = store.list_evidence(tenant_id=tenant_id)
            return Response(evidence_list_contract(evidence))

        evidence = store.list_evidence(tenant_id=requested_tenant_id or None)
        return Response(evidence_list_contract(evidence))

    @app.route("/api/v1/evidence/{evidence_id}", methods=["GET"])
    def evidence_get_v1(req: Request, evidence_id: str = "") -> Response:
        tenant_id = _request_tenant_id(req)
        requested_tenant_id = req.query("tenant_id", "").strip()

        if requested_tenant_id and not _tenant_exists(tenants, requested_tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)
        if tenant_id and not _tenant_exists(tenants, tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)
        if tenant_id and requested_tenant_id and requested_tenant_id != tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)

        evidence = store.get_evidence(evidence_id)
        if evidence is None:
            return Response({"error": "Evidence not found"}, status_code=404)
        evidence_tenant = evidence.provenance.get("tenant_id")
        if requested_tenant_id and evidence_tenant and evidence_tenant != requested_tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)
        if tenant_id and evidence_tenant and evidence_tenant != tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)
        return Response(evidence_detail_contract(evidence))
