"""CIV-ARCOS REST API server."""
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict

from civ_arcos.adapters.github_adapter import GitHubCollector
from civ_arcos.core.config import get_config
from civ_arcos.distributed.blockchain_ledger import BlockchainLedger
from civ_arcos.evidence.collector import EvidenceStore
from civ_arcos.storage.graph import EvidenceGraph
from civ_arcos.web.badges import BadgeGenerator
from civ_arcos.web.framework import Application, Request, Response, create_app

_start_time = time.time()
app: Application = create_app()
_graph = EvidenceGraph()
_store = EvidenceStore(_graph)
_ledger = BlockchainLedger()
_badges = BadgeGenerator()


@app.route("/", methods=["GET"])
def index(req: Request) -> Response:
    return Response({
        "name": "CIV-ARCOS API",
        "version": "0.1.0",
        "description": "Civilian Assurance-based Risk Computation and Orchestration System",
    })


@app.route("/api/status", methods=["GET"])
def status(req: Request) -> Response:
    return Response({
        "version": "0.1.0",
        "uptime_seconds": round(time.time() - _start_time, 2),
        "evidence_count": len(_store.list_evidence()),
        "blockchain_length": _ledger.get_chain_length(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/api/evidence/collect", methods=["POST"])
def collect_evidence(req: Request) -> Response:
    body = req.json() or {}
    repo_url = body.get("repo_url", "")
    token = body.get("token")
    config = get_config()
    collector = GitHubCollector(token=token or config.github_token or None)
    evidence_list = collector.collect(repo_url=repo_url)
    node_ids = []
    for ev in evidence_list:
        nid = _store.store_evidence(ev)
        _ledger.add_block({"evidence_id": ev.id, "checksum": ev.checksum})
        node_ids.append(nid)
    return Response({"collected": len(evidence_list), "node_ids": node_ids}, status_code=201)


@app.route("/api/evidence", methods=["GET"])
def list_evidence(req: Request) -> Response:
    evidence = _store.list_evidence()
    return Response([{
        "id": e.id, "type": e.type, "source": e.source,
        "timestamp": e.timestamp, "checksum": e.checksum
    } for e in evidence])


@app.route("/api/evidence/{evidence_id}", methods=["GET"])
def get_evidence(req: Request, evidence_id: str = "") -> Response:
    ev = _store.get_evidence(evidence_id)
    if ev is None:
        return Response({"error": "Evidence not found"}, status_code=404)
    return Response({
        "id": ev.id, "type": ev.type, "source": ev.source,
        "timestamp": ev.timestamp, "data": ev.data,
        "provenance": ev.provenance, "checksum": ev.checksum
    })


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
    data = req.json() or {}
    block = _ledger.add_block(data)
    return Response({
        "index": block.index, "hash": block.hash,
        "timestamp": block.timestamp
    }, status_code=201)


@app.route("/api/blockchain/status", methods=["GET"])
def blockchain_status(req: Request) -> Response:
    return Response({
        "length": _ledger.get_chain_length(),
        "valid": _ledger.validate_chain(),
        "genesis_hash": _ledger.get_block(0).hash if _ledger.get_chain_length() > 0 else None,
    })


def run_server() -> None:
    config = get_config()
    app.run(host=config.host, port=config.port)


if __name__ == "__main__":
    run_server()
