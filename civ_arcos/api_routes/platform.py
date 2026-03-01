"""Platform routes for risk, compliance, and analytics domains."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from civ_arcos.core.compliance_reports import ComplianceReportStore
from civ_arcos.core.quality_metrics_history import QualityMetricsHistory
from civ_arcos.core.report_scheduler import ReportScheduler
from civ_arcos.contracts.v1 import (
    analytics_trends_contract,
    compliance_report_artifact_contract,
    compliance_report_list_contract,
    compliance_status_contract,
    quality_metrics_forecast_contract,
    quality_metrics_trends_contract,
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
    report_scheduler: ReportScheduler,
    quality_metrics_history: QualityMetricsHistory,
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

    @app.route("/api/reports/schedule", methods=["POST"])
    def schedule_report(req: Request) -> Response:
        body = req.json() or {}
        report_type = str(body.get("report_type", "executive_summary"))
        frequency = str(body.get("frequency", "daily"))
        target = str(body.get("target", "console"))

        try:
            job = report_scheduler.schedule_report(
                report_type=report_type,
                frequency=frequency,
                target=target,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status_code=400)

        return Response({"job": job.__dict__}, status_code=201)

    @app.route("/api/reports/jobs", methods=["GET"])
    def list_report_jobs(req: Request) -> Response:
        return Response({"jobs": report_scheduler.list_jobs()})

    @app.route("/api/reports/jobs/{job_id}", methods=["GET"])
    def get_report_job(req: Request, job_id: str = "") -> Response:
        job = report_scheduler.get_job(job_id)
        if job is None:
            return Response({"error": "Report job not found"}, status_code=404)
        return Response({"job": job})

    @app.route("/api/quality/metrics/record", methods=["POST"])
    def record_quality_metrics(req: Request) -> Response:
        body = req.json() or {}
        analytics = _analytics_trends_payload(
            store,
            ledger,
            assurance_case_count=len(assurance_cases),
        )
        risk = _risk_map_payload(store)

        score = float(body.get("score", max(0, 100 - risk["total_components"] * 2)))
        evidence_total = int(body.get("evidence_total", analytics["evidence_total"]))
        risk_components = int(body.get("risk_components", risk["total_components"]))
        source = str(body.get("source", "api_record"))

        snapshot = quality_metrics_history.record_snapshot(
            score=score,
            evidence_total=evidence_total,
            risk_components=risk_components,
            source=source,
        )
        return Response({"snapshot": snapshot}, status_code=201)

    @app.route("/api/quality/metrics/history", methods=["GET"])
    def quality_metrics_history_list(req: Request) -> Response:
        limit = int(req.query("limit", "50"))
        return Response({"snapshots": quality_metrics_history.list_snapshots(limit)})

    @app.route("/api/quality/metrics/trends", methods=["GET"])
    def quality_metrics_trends(req: Request) -> Response:
        window = int(req.query("window", "10"))
        return Response(quality_metrics_history.trend_summary(window))

    @app.route("/api/quality/metrics/forecast", methods=["GET"])
    def quality_metrics_forecast(req: Request) -> Response:
        window = int(req.query("window", "10"))
        horizon = int(req.query("horizon", "3"))
        return Response(
            quality_metrics_history.forecast_summary(window=window, horizon=horizon)
        )


def register_platform_v1_routes(
    app: Application,
    store: EvidenceStore,
    ledger: BlockchainLedger,
    assurance_cases: Dict[str, Any],
    report_scheduler: ReportScheduler,
    quality_metrics_history: QualityMetricsHistory,
    compliance_report_store: ComplianceReportStore,
    tenants: List[Dict[str, Any]],
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

    @app.route("/api/v1/reports/schedule", methods=["POST"])
    def schedule_report_v1(req: Request) -> Response:
        body = req.json() or {}
        report_type = str(body.get("report_type", "executive_summary"))
        frequency = str(body.get("frequency", "daily"))
        target = str(body.get("target", "console"))

        try:
            job = report_scheduler.schedule_report(
                report_type=report_type,
                frequency=frequency,
                target=target,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status_code=400)

        return Response(
            {
                "contract": {
                    "name": "ReportSchedule",
                    "version": "v1",
                },
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "data": {"job": job.__dict__},
            },
            status_code=201,
        )

    @app.route("/api/v1/quality/metrics/trends", methods=["GET"])
    def quality_metrics_trends_v1(req: Request) -> Response:
        window = int(req.query("window", "10"))
        return Response(
            quality_metrics_trends_contract(
                quality_metrics_history.trend_summary(window)
            )
        )

    @app.route("/api/v1/quality/metrics/forecast", methods=["GET"])
    def quality_metrics_forecast_v1(req: Request) -> Response:
        window = int(req.query("window", "10"))
        horizon = int(req.query("horizon", "3"))
        return Response(
            quality_metrics_forecast_contract(
                quality_metrics_history.forecast_summary(
                    window=window,
                    horizon=horizon,
                )
            )
        )

    def _request_tenant_id(req: Request) -> str:
        return (
            req.headers.get("X-Tenant-ID") or req.headers.get("x-tenant-id", "")
        ).strip()

    def _tenant_exists(tenant_id: str) -> bool:
        return any(tenant.get("id") == tenant_id for tenant in tenants)

    @app.route("/api/v1/compliance/reports", methods=["POST"])
    def compliance_report_create_v1(req: Request) -> Response:
        tenant_id = _request_tenant_id(req)
        if not tenant_id:
            return Response(
                {"error": "X-Tenant-ID header is required"}, status_code=401
            )
        if not _tenant_exists(tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)

        status_payload = _compliance_status_payload(store)
        report = compliance_report_store.create_report(
            tenant_id=tenant_id,
            frameworks=status_payload["frameworks"],
        )
        return Response(
            compliance_report_artifact_contract({"report": report}),
            status_code=201,
        )

    @app.route("/api/v1/compliance/reports", methods=["GET"])
    def compliance_report_list_v1(req: Request) -> Response:
        tenant_id = _request_tenant_id(req)
        if not tenant_id:
            return Response(
                {"error": "X-Tenant-ID header is required"}, status_code=401
            )
        if not _tenant_exists(tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)

        requested_tenant = req.query("tenant_id", "").strip()
        if requested_tenant and requested_tenant != tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)

        reports = compliance_report_store.list_reports(tenant_id=tenant_id)
        return Response(
            compliance_report_list_contract(
                {
                    "tenant_id": tenant_id,
                    "count": len(reports),
                    "reports": reports,
                }
            )
        )

    @app.route("/api/v1/compliance/reports/{report_id}", methods=["GET"])
    def compliance_report_get_v1(req: Request, report_id: str = "") -> Response:
        tenant_id = _request_tenant_id(req)
        if not tenant_id:
            return Response(
                {"error": "X-Tenant-ID header is required"}, status_code=401
            )
        if not _tenant_exists(tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)

        report = compliance_report_store.get_report(report_id)
        if report is None:
            return Response({"error": "Compliance report not found"}, status_code=404)
        if report.get("tenant_id") != tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)

        return Response(compliance_report_artifact_contract({"report": report}))
