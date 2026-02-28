"""Platform routes for risk, compliance, and analytics domains."""

from __future__ import annotations

from typing import Any, Dict, List

from civ_arcos.contracts.v1 import (
    analytics_trends_contract,
    compliance_status_contract,
    risk_map_contract,
)
from civ_arcos.distributed.blockchain_ledger import BlockchainLedger
from civ_arcos.evidence.collector import EvidenceStore
from civ_arcos.web.framework import Application, Request, Response


def _risk_map_payload(store: EvidenceStore) -> Dict[str, Any]:
    """Compute risk map payload from stored security scan evidence."""
    evidence_list = store.list_evidence()
    risk_items: List[Dict[str, Any]] = []
    for evidence in evidence_list:
        if evidence.type != "security_scan":
            continue
        data = evidence.data or {}
        vulnerability_count = data.get("vulnerability_count", 0)
        score = min(100, vulnerability_count * 10)
        level = (
            "critical"
            if score >= 75
            else "high" if score >= 50 else "medium" if score >= 25 else "low"
        )
        risk_items.append(
            {
                "component": data.get("file", evidence.source),
                "score": score,
                "level": level,
                "vulnerabilities": vulnerability_count,
            }
        )
    risk_items.sort(key=lambda item: item["score"], reverse=True)
    return {"items": risk_items[:20], "total_components": len(risk_items)}


def _compliance_status_payload(store: EvidenceStore) -> Dict[str, Any]:
    """Compute compliance framework status from evidence-derived security scores."""
    security_scores = [
        evidence.data.get("score", 100)
        for evidence in store.list_evidence()
        if evidence.type == "security_score"
    ]
    avg_score = sum(security_scores) / len(security_scores) if security_scores else 85.0
    multipliers = {
        "ISO 27001": 0.78,
        "FedRAMP": 0.91,
        "SOX ITGC": 0.84,
        "NIST 800-53": 0.67,
        "PCI-DSS": 0.73,
    }
    frameworks = []
    for name, multiplier in multipliers.items():
        percentage = round(avg_score * multiplier, 1)
        frameworks.append(
            {
                "framework": name,
                "percentage": percentage,
                "status": "compliant" if percentage >= 80 else "partial",
            }
        )
    return {"frameworks": frameworks}


def _analytics_trends_payload(
    store: EvidenceStore,
    ledger: BlockchainLedger,
    assurance_case_count: int,
) -> Dict[str, Any]:
    """Build analytics summary payload from evidence and platform state."""
    evidence_list = store.list_evidence()
    by_type: Dict[str, int] = {}
    by_source: Dict[str, int] = {}
    for evidence in evidence_list:
        by_type[evidence.type] = by_type.get(evidence.type, 0) + 1
        by_source[evidence.source] = by_source.get(evidence.source, 0) + 1

    security_scores = [
        evidence.data.get("score", 0)
        for evidence in evidence_list
        if evidence.type == "security_score"
    ]
    latest_security_score = security_scores[-1] if security_scores else None

    return {
        "evidence_total": len(evidence_list),
        "blockchain_blocks": ledger.get_chain_length(),
        "assurance_cases": assurance_case_count,
        "by_type": by_type,
        "by_source": by_source,
        "latest_security_score": latest_security_score,
    }


def register_platform_legacy_routes(
    app: Application,
    store: EvidenceStore,
    ledger: BlockchainLedger,
    assurance_cases: Dict[str, Any],
) -> None:
    """Register legacy ``/api`` routes for platform status domains."""

    @app.route("/api/risk/map", methods=["GET"])
    def risk_map(req: Request) -> Response:
        return Response(_risk_map_payload(store))

    @app.route("/api/compliance/status", methods=["GET"])
    def compliance_status(req: Request) -> Response:
        return Response(_compliance_status_payload(store))

    @app.route("/api/analytics/trends", methods=["GET"])
    def analytics_trends(req: Request) -> Response:
        payload = _analytics_trends_payload(
            store,
            ledger,
            assurance_case_count=len(assurance_cases),
        )
        return Response(payload)


def register_platform_v1_routes(
    app: Application,
    store: EvidenceStore,
    ledger: BlockchainLedger,
    assurance_cases: Dict[str, Any],
) -> None:
    """Register versioned ``/api/v1`` platform routes with contracts."""

    @app.route("/api/v1/risk/map", methods=["GET"])
    def risk_map_v1(req: Request) -> Response:
        return Response(risk_map_contract(_risk_map_payload(store)))

    @app.route("/api/v1/compliance/status", methods=["GET"])
    def compliance_status_v1(req: Request) -> Response:
        return Response(compliance_status_contract(_compliance_status_payload(store)))

    @app.route("/api/v1/analytics/trends", methods=["GET"])
    def analytics_trends_v1(req: Request) -> Response:
        payload = _analytics_trends_payload(
            store,
            ledger,
            assurance_case_count=len(assurance_cases),
        )
        return Response(analytics_trends_contract(payload))
