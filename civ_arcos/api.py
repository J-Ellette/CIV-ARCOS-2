"""CIV-ARCOS REST API server."""

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from civ_arcos.adapters.github_adapter import GitHubCollector
from civ_arcos.api_routes.admin import (
    register_admin_legacy_routes,
    register_admin_v1_routes,
)
from civ_arcos.api_routes.analysis import (
    register_analysis_legacy_routes,
    register_analysis_v1_routes,
)
from civ_arcos.api_routes.assurance import register_assurance_legacy_routes
from civ_arcos.api_routes.assurance_v1 import register_assurance_v1_routes
from civ_arcos.api_routes.evidence_v1 import register_evidence_v1_routes
from civ_arcos.api_routes.platform import (
    register_platform_legacy_routes,
    register_platform_v1_routes,
)
from civ_arcos.api_routes.plugins import (
    register_plugin_legacy_routes,
    register_plugin_v1_routes,
)
from civ_arcos.core.config import get_config
from civ_arcos.core.plugin_marketplace import PluginSandbox, PluginValidator
from civ_arcos.distributed.blockchain_ledger import BlockchainLedger
from civ_arcos.evidence.collector import EvidenceStore
from civ_arcos.storage.graph import EvidenceGraph
from civ_arcos.web.badges import BadgeGenerator
from civ_arcos.web.framework import Application, Request, Response, create_app
from civ_arcos.web.idempotency import IdempotencyCache, make_request_fingerprint
from civ_arcos.web.webhook import (
    nonce_cache,
    validate_github_signature,
)
from civ_arcos.assurance.templates import TemplateLibrary
from civ_arcos.assurance.visualizer import GSNVisualizer

_start_time = time.time()
app: Application = create_app()
_graph = EvidenceGraph()
_store = EvidenceStore(_graph)
_ledger = BlockchainLedger()
_badges = BadgeGenerator()
_template_library = TemplateLibrary()
_visualizer = GSNVisualizer()
_assurance_cases: Dict[str, Any] = {}
_tenants: List[Dict[str, Any]] = [
    {
        "id": "org_alpha",
        "name": "Org Alpha",
        "plan": "enterprise",
        "created_at": "2025-10-01T00:00:00Z",
    },
    {
        "id": "org_beta",
        "name": "Org Beta",
        "plan": "pro",
        "created_at": "2025-11-15T00:00:00Z",
    },
]
# Mutable settings store (mirrors Config defaults; overridable at runtime)
_settings: Dict[str, Any] = {}
_idempotency_cache = IdempotencyCache(
    ttl_secs=int(os.environ.get("CIV_IDEMPOTENCY_TTL_SECS", "86400"))
)
_plugin_validator = PluginValidator()
_plugin_sandbox = PluginSandbox(
    timeout_secs=float(os.environ.get("CIV_PLUGIN_TIMEOUT_SECS", "2.0"))
)


def _get_dashboard_html() -> bytes:
    """Read and return the dashboard HTML file."""
    candidates = [
        Path(__file__).parent.parent / "civ-arcos-carbon.html",
        Path("civ-arcos-carbon.html"),
    ]
    for p in candidates:
        if p.exists():
            return p.read_bytes()
    return b"<html><body>Dashboard not found</body></html>"


def _idempotency_key(req: Request) -> str:
    """Return the request idempotency key header (if present)."""
    return req.headers.get("Idempotency-Key") or req.headers.get("idempotency-key", "")


def _idempotency_precheck(req: Request) -> Response | None:
    """Return a replay/conflict response for an idempotent request if needed."""
    key = _idempotency_key(req)
    fingerprint = make_request_fingerprint(req.method, req.path, req.body)
    state, cached = _idempotency_cache.lookup(key, fingerprint)
    if state == "hit":
        return cached
    if state == "conflict":
        return Response(
            {"error": "Idempotency key reused with different payload"},
            status_code=409,
        )
    return None


def _idempotency_store(req: Request, response: Response) -> None:
    """Persist an idempotent response when the request includes a key."""
    key = _idempotency_key(req)
    if not key:
        return
    if response.status_code >= 500:
        return
    fingerprint = make_request_fingerprint(req.method, req.path, req.body)
    _idempotency_cache.store(key, fingerprint, response)


# ---------------------------------------------------------------------------
# Modularized API route registration (versioned contracts)
# ---------------------------------------------------------------------------

register_evidence_v1_routes(
    app,
    store=_store,
    ledger=_ledger,
    tenants=_tenants,
    config_provider=get_config,
    idempotency_precheck=_idempotency_precheck,
    idempotency_store=_idempotency_store,
)
register_assurance_v1_routes(
    app,
    assurance_cases=_assurance_cases,
    template_library=_template_library,
    graph=_graph,
    store=_store,
    idempotency_precheck=_idempotency_precheck,
    idempotency_store=_idempotency_store,
)
register_assurance_legacy_routes(
    app,
    assurance_cases=_assurance_cases,
    template_library=_template_library,
    visualizer=_visualizer,
    graph=_graph,
    store=_store,
    idempotency_precheck=_idempotency_precheck,
    idempotency_store=_idempotency_store,
)
register_analysis_legacy_routes(app, _graph)
register_analysis_v1_routes(app, _graph)
register_platform_legacy_routes(
    app,
    store=_store,
    ledger=_ledger,
    assurance_cases=_assurance_cases,
)
register_platform_v1_routes(
    app,
    store=_store,
    ledger=_ledger,
    assurance_cases=_assurance_cases,
)
register_admin_legacy_routes(
    app,
    tenants=_tenants,
    settings_store=_settings,
    config_provider=get_config,
)
register_admin_v1_routes(
    app,
    tenants=_tenants,
    settings_store=_settings,
    config_provider=get_config,
    idempotency_precheck=_idempotency_precheck,
    idempotency_store=_idempotency_store,
)
register_plugin_legacy_routes(
    app,
    validator=_plugin_validator,
    sandbox=_plugin_sandbox,
    idempotency_precheck=_idempotency_precheck,
    idempotency_store=_idempotency_store,
)
register_plugin_v1_routes(
    app,
    validator=_plugin_validator,
    sandbox=_plugin_sandbox,
    idempotency_precheck=_idempotency_precheck,
    idempotency_store=_idempotency_store,
)


@app.route("/", methods=["GET"])
def index(req: Request) -> Response:
    return Response(
        {
            "name": "CIV-ARCOS API",
            "version": "0.1.0",
            "description": "Civilian Assurance-based Risk Computation and Orchestration System",
            "dashboard": "/dashboard",
        }
    )


@app.route("/dashboard", methods=["GET"])
def dashboard(req: Request) -> Response:
    """Serve the main dashboard HTML file."""
    html = _get_dashboard_html()
    return Response(html, content_type="text/html")


@app.route("/api/status", methods=["GET"])
def status(req: Request) -> Response:
    return Response(
        {
            "version": "0.1.0",
            "uptime_seconds": round(time.time() - _start_time, 2),
            "evidence_count": len(_store.list_evidence()),
            "blockchain_length": _ledger.get_chain_length(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# Health endpoints (liveness, readiness, dependency health)
# ---------------------------------------------------------------------------


@app.route("/api/health/live", methods=["GET"])
def health_live(req: Request) -> Response:
    """Liveness probe — always 200 when the process is running."""
    return Response({"status": "ok"})


@app.route("/api/health/ready", methods=["GET"])
def health_ready(req: Request) -> Response:
    """Readiness probe — checks that core subsystems are operational.

    Returns 200 when ready, 503 when one or more subsystems are degraded.
    """
    checks: Dict[str, Any] = {}

    # Blockchain integrity
    try:
        checks["blockchain"] = {
            "status": "ok" if _ledger.validate_chain() else "degraded",
            "length": _ledger.get_chain_length(),
        }
    except Exception as exc:  # noqa: BLE001
        checks["blockchain"] = {"status": "error", "detail": str(exc)}

    # Evidence store
    try:
        _ = _store.list_evidence()
        checks["evidence_store"] = {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        checks["evidence_store"] = {"status": "error", "detail": str(exc)}

    degraded = any(v.get("status") != "ok" for v in checks.values())
    overall = "degraded" if degraded else "ok"
    return Response(
        {"status": overall, "checks": checks}, status_code=503 if degraded else 200
    )


@app.route("/api/health/dependencies", methods=["GET"])
def health_dependencies(req: Request) -> Response:
    """Full dependency health report.

    Extends :func:`health_ready` with additional optional subsystem details
    (assurance cases count, uptime, version).
    """
    checks: Dict[str, Any] = {}

    try:
        checks["blockchain"] = {
            "status": "ok" if _ledger.validate_chain() else "degraded",
            "length": _ledger.get_chain_length(),
        }
    except Exception as exc:  # noqa: BLE001
        checks["blockchain"] = {"status": "error", "detail": str(exc)}

    try:
        ev_count = len(_store.list_evidence())
        checks["evidence_store"] = {"status": "ok", "evidence_count": ev_count}
    except Exception as exc:  # noqa: BLE001
        checks["evidence_store"] = {"status": "error", "detail": str(exc)}

    checks["assurance_cases"] = {
        "status": "ok",
        "count": len(_assurance_cases),
    }

    degraded = any(v.get("status") != "ok" for v in checks.values())
    return Response(
        {
            "status": "degraded" if degraded else "ok",
            "version": "0.1.0",
            "uptime_seconds": round(time.time() - _start_time, 2),
            "checks": checks,
        },
        status_code=503 if degraded else 200,
    )


# ---------------------------------------------------------------------------
# Webhook endpoint (GitHub events with HMAC-SHA256 + replay protection)
# ---------------------------------------------------------------------------


@app.route("/api/webhooks/github", methods=["POST"])
def webhook_github(req: Request) -> Response:
    """Accept a GitHub webhook delivery with signature and replay protection.

    Expected headers:
      - ``X-Hub-Signature-256``: ``sha256=<hex>`` HMAC-SHA256 of the body.
      - ``X-GitHub-Delivery``: UUID delivery ID (replay protection).
      - ``X-GitHub-Event``: Event type (e.g. ``push``, ``pull_request``).

    The shared secret must be set via the ``CIV_WEBHOOK_SECRET`` environment
    variable.  When it is unset, signature validation is skipped and a warning
    is included in the response (useful in development).
    """
    replay_resp = _idempotency_precheck(req)
    if replay_resp is not None:
        return replay_resp

    secret = os.environ.get("CIV_WEBHOOK_SECRET", "")
    sig_header = req.headers.get("X-Hub-Signature-256") or req.headers.get(
        "x-hub-signature-256", ""
    )
    delivery_id = req.headers.get("X-GitHub-Delivery") or req.headers.get(
        "x-github-delivery", ""
    )
    event_type = req.headers.get("X-GitHub-Event") or req.headers.get(
        "x-github-event", "unknown"
    )

    # --- Signature validation ---
    if secret:
        if not validate_github_signature(req.body, secret, sig_header):
            return Response({"error": "Invalid signature"}, status_code=401)
    else:
        # Secret not configured — warn but continue (dev mode).
        pass

    # --- Replay protection ---
    if delivery_id:
        if nonce_cache.is_replay(delivery_id):
            return Response({"error": "Duplicate delivery"}, status_code=409)
        nonce_cache.record(delivery_id)

    # --- Process the event ---
    resp = Response(
        {
            "received": True,
            "event": event_type,
            "delivery_id": delivery_id,
            "secret_configured": bool(secret),
        },
        status_code=202,
    )
    _idempotency_store(req, resp)
    return resp


@app.route("/api/evidence/collect", methods=["POST"])
def collect_evidence(req: Request) -> Response:
    replay_resp = _idempotency_precheck(req)
    if replay_resp is not None:
        return replay_resp

    body = req.json() or {}
    repo_url = body.get("repo_url", "")
    token = body.get("token")
    config = get_config()
    collector = GitHubCollector(token=token or config.github_token or None)
    evidence_list = collector.collect(repo_url=repo_url)
    node_ids = []
    for ev in evidence_list:
        graph_node_id = _store.store_evidence(ev)
        _ledger.add_block({"evidence_id": ev.id, "checksum": ev.checksum})
        node_ids.append(graph_node_id)
    resp = Response(
        {"collected": len(evidence_list), "node_ids": node_ids}, status_code=201
    )
    _idempotency_store(req, resp)
    return resp


@app.route("/api/evidence", methods=["GET"])
def list_evidence(req: Request) -> Response:
    evidence = _store.list_evidence()
    return Response(
        [
            {
                "id": e.id,
                "type": e.type,
                "source": e.source,
                "timestamp": e.timestamp,
                "checksum": e.checksum,
            }
            for e in evidence
        ]
    )


@app.route("/api/evidence/{evidence_id}", methods=["GET"])
def get_evidence(req: Request, evidence_id: str = "") -> Response:
    ev = _store.get_evidence(evidence_id)
    if ev is None:
        return Response({"error": "Evidence not found"}, status_code=404)
    return Response(
        {
            "id": ev.id,
            "type": ev.type,
            "source": ev.source,
            "timestamp": ev.timestamp,
            "data": ev.data,
            "provenance": ev.provenance,
            "checksum": ev.checksum,
        }
    )


@app.route("/api/badge/coverage/{owner}/{repo}", methods=["GET"])
def badge_coverage(req: Request, owner: str = "", repo: str = "") -> Response:
    try:
        pct = float(req.query("coverage", "0"))
    except ValueError:
        pct = 0.0
    svg = _badges.generate_coverage_badge(pct)
    return Response(svg, content_type="image/svg+xml")


@app.route("/api/badge/quality/{owner}/{repo}", methods=["GET"])
def badge_quality(req: Request, owner: str = "", repo: str = "") -> Response:
    try:
        score = float(req.query("score", "0"))
    except ValueError:
        score = 0.0
    svg = _badges.generate_quality_badge(score)
    return Response(svg, content_type="image/svg+xml")


@app.route("/api/badge/security/{owner}/{repo}", methods=["GET"])
def badge_security(req: Request, owner: str = "", repo: str = "") -> Response:
    try:
        vulns = int(req.query("vulns", "0"))
    except ValueError:
        vulns = 0
    svg = _badges.generate_security_badge(vulns)
    return Response(svg, content_type="image/svg+xml")


@app.route("/api/blockchain/add", methods=["POST"])
def blockchain_add(req: Request) -> Response:
    replay_resp = _idempotency_precheck(req)
    if replay_resp is not None:
        return replay_resp

    data = req.json() or {}
    block = _ledger.add_block(data)
    resp = Response(
        {"index": block.index, "hash": block.hash, "timestamp": block.timestamp},
        status_code=201,
    )
    _idempotency_store(req, resp)
    return resp


@app.route("/api/blockchain/status", methods=["GET"])
def blockchain_status(req: Request) -> Response:
    genesis = _ledger.get_block(0)
    return Response(
        {
            "length": _ledger.get_chain_length(),
            "valid": _ledger.validate_chain(),
            "genesis_hash": genesis.hash if genesis is not None else None,
        }
    )


@app.route("/api/blockchain/chain", methods=["GET"])
def blockchain_chain(req: Request) -> Response:
    """Return the most recent N blocks."""
    try:
        limit = int(req.query("limit", "20"))
    except ValueError:
        limit = 20
    length = _ledger.get_chain_length()
    start = max(0, length - limit)
    blocks = []
    for block_index in range(start, length):
        block = _ledger.get_block(block_index)
        if block:
            blocks.append(
                {
                    "index": block.index,
                    "hash": block.hash,
                    "previous_hash": block.previous_hash,
                    "timestamp": block.timestamp,
                    "data": block.data,
                }
            )
    return Response(
        {
            "blocks": list(reversed(blocks)),
            "total": length,
            "valid": _ledger.validate_chain(),
        }
    )


def run_server() -> None:
    config = get_config()
    app.run(host=config.host, port=config.port)


if __name__ == "__main__":
    run_server()
