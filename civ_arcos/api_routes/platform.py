"""Platform routes for risk, compliance, and analytics domains."""

from __future__ import annotations

from typing import Any, Dict, List

from civ_arcos.core.analytics import AnalyticsEngine
from civ_arcos.core.compliance import ComplianceEngine
from civ_arcos.core.compliance_reports import ComplianceReportStore
from civ_arcos.core.quality_metrics_history import QualityMetricsHistory
from civ_arcos.core.report_scheduler import ReportScheduler
from civ_arcos.contracts.v1 import (
    analytics_benchmark_contract,
    analytics_risks_contract,
    analytics_trends_contract,
    compliance_evaluate_all_contract,
    compliance_evaluate_contract,
    compliance_frameworks_contract,
    compliance_report_artifact_contract,
    compliance_report_list_contract,
    compliance_status_contract,
    quality_metrics_forecast_contract,
    quality_metrics_history_contract,
    quality_metrics_record_contract,
    quality_metrics_trends_contract,
    report_schedule_contract,
    report_job_detail_contract,
    report_jobs_list_contract,
    risk_map_contract,
)
from civ_arcos.distributed.blockchain_ledger import BlockchainLedger
from civ_arcos.evidence.collector import EvidenceStore
from civ_arcos.web.framework import Application, Request, Response


def _parse_int_value(
    raw_value: Any,
    field_name: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> tuple[int | None, Response | None]:
    """Parse and validate an integer value for API input handling."""
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return None, Response({"error": f"{field_name} must be an integer"}, status_code=400)

    if minimum is not None and parsed < minimum:
        return (
            None,
            Response(
                {"error": f"{field_name} must be >= {minimum}"},
                status_code=400,
            ),
        )
    if maximum is not None and parsed > maximum:
        return (
            None,
            Response(
                {"error": f"{field_name} must be <= {maximum}"},
                status_code=400,
            ),
        )
    return parsed, None


def _parse_float_value(
    raw_value: Any,
    field_name: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> tuple[float | None, Response | None]:
    """Parse and validate a float value for API input handling."""
    try:
        parsed = float(raw_value)
    except (TypeError, ValueError):
        return None, Response({"error": f"{field_name} must be a number"}, status_code=400)

    if minimum is not None and parsed < minimum:
        return (
            None,
            Response(
                {"error": f"{field_name} must be >= {minimum}"},
                status_code=400,
            ),
        )
    if maximum is not None and parsed > maximum:
        return (
            None,
            Response(
                {"error": f"{field_name} must be <= {maximum}"},
                status_code=400,
            ),
        )
    return parsed, None


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

    compliance_engine = ComplianceEngine()
    analytics_engine = AnalyticsEngine()

    @app.route("/api/risk/map", methods=["GET"])
    def risk_map(req: Request) -> Response:
        return Response(_risk_map_payload(store))

    @app.route("/api/compliance/status", methods=["GET"])
    def compliance_status(req: Request) -> Response:
        return Response(_compliance_status_payload(store))

    @app.route("/api/compliance/frameworks", methods=["GET"])
    def compliance_frameworks(req: Request) -> Response:
        return Response({"frameworks": compliance_engine.list_frameworks()})

    @app.route("/api/compliance/evaluate", methods=["POST"])
    def compliance_evaluate(req: Request) -> Response:
        body = req.json() or {}
        framework = str(body.get("framework", "")).strip()
        if not framework:
            return Response({"error": "framework is required"}, status_code=400)

        evidence = body.get("evidence") or {}
        if not isinstance(evidence, dict):
            return Response({"error": "evidence must be an object"}, status_code=400)

        try:
            result = compliance_engine.evaluate_framework(framework, evidence)
        except ValueError as exc:
            return Response({"error": str(exc)}, status_code=400)
        return Response({"result": result})

    @app.route("/api/compliance/evaluate-all", methods=["POST"])
    def compliance_evaluate_all(req: Request) -> Response:
        body = req.json() or {}
        evidence = body.get("evidence") or {}
        if not isinstance(evidence, dict):
            return Response({"error": "evidence must be an object"}, status_code=400)
        return Response(compliance_engine.evaluate_all(evidence))

    @app.route("/api/analytics/trends", methods=["GET"])
    def analytics_trends(req: Request) -> Response:
        payload = _analytics_trends_payload(
            store,
            ledger,
            assurance_case_count=len(assurance_cases),
        )
        return Response(payload)

    @app.route("/api/analytics/trends", methods=["POST"])
    def analytics_trends_post(req: Request) -> Response:
        body = req.json() or {}
        snapshots = body.get("snapshots") or []
        if not isinstance(snapshots, list):
            return Response({"error": "snapshots must be a list"}, status_code=400)
        return Response(analytics_engine.trend_analysis(snapshots))

    @app.route("/api/analytics/benchmark", methods=["POST"])
    def analytics_benchmark(req: Request) -> Response:
        body = req.json() or {}
        metrics = body.get("metrics") or {}
        if not isinstance(metrics, dict):
            return Response({"error": "metrics must be an object"}, status_code=400)
        industry = str(body.get("industry", "general"))
        return Response(analytics_engine.benchmark_analysis(metrics, industry=industry))

    @app.route("/api/analytics/risks", methods=["POST"])
    def analytics_risks(req: Request) -> Response:
        body = req.json() or {}
        metrics = body.get("metrics") or {}
        if not isinstance(metrics, dict):
            return Response({"error": "metrics must be an object"}, status_code=400)
        return Response(analytics_engine.risk_prediction(metrics))

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

        score, score_error = _parse_float_value(
            body.get("score", max(0, 100 - risk["total_components"] * 2)),
            "score",
            minimum=0.0,
            maximum=100.0,
        )
        if score_error is not None:
            return score_error
        evidence_total, evidence_total_error = _parse_int_value(
            body.get("evidence_total", analytics["evidence_total"]),
            "evidence_total",
            minimum=0,
        )
        if evidence_total_error is not None:
            return evidence_total_error
        risk_components, risk_components_error = _parse_int_value(
            body.get("risk_components", risk["total_components"]),
            "risk_components",
            minimum=0,
        )
        if risk_components_error is not None:
            return risk_components_error
        assert score is not None
        assert evidence_total is not None
        assert risk_components is not None
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
        limit, limit_error = _parse_int_value(req.query("limit", "50"), "limit", minimum=1)
        if limit_error is not None:
            return limit_error
        assert limit is not None
        return Response({"snapshots": quality_metrics_history.list_snapshots(limit)})

    @app.route("/api/quality/metrics/trends", methods=["GET"])
    def quality_metrics_trends(req: Request) -> Response:
        window, window_error = _parse_int_value(req.query("window", "10"), "window", minimum=1)
        if window_error is not None:
            return window_error
        assert window is not None
        return Response(quality_metrics_history.trend_summary(window))

    @app.route("/api/quality/metrics/forecast", methods=["GET"])
    def quality_metrics_forecast(req: Request) -> Response:
        window, window_error = _parse_int_value(req.query("window", "10"), "window", minimum=1)
        if window_error is not None:
            return window_error
        horizon, horizon_error = _parse_int_value(
            req.query("horizon", "3"),
            "horizon",
            minimum=1,
            maximum=12,
        )
        if horizon_error is not None:
            return horizon_error
        assert window is not None
        assert horizon is not None
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

    compliance_engine = ComplianceEngine()
    analytics_engine = AnalyticsEngine()

    def _request_tenant_id(req: Request) -> str:
        return (
            req.headers.get("X-Tenant-ID") or req.headers.get("x-tenant-id", "")
        ).strip()

    def _tenant_exists(tenant_id: str) -> bool:
        return any(tenant.get("id") == tenant_id for tenant in tenants)

    def _enforce_tenant_context(
        req: Request,
        requested_tenant_id: str = "",
    ) -> Response | None:
        actor_tenant_id = _request_tenant_id(req)
        if not actor_tenant_id:
            return None
        if not _tenant_exists(actor_tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)
        if requested_tenant_id and requested_tenant_id != actor_tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)
        return None

    @app.route("/api/v1/risk/map", methods=["GET"])
    def risk_map_v1(req: Request) -> Response:
        denied = _enforce_tenant_context(req, req.query("tenant_id", "").strip())
        if denied is not None:
            return denied
        return Response(risk_map_contract(_risk_map_payload(store)))

    @app.route("/api/v1/compliance/status", methods=["GET"])
    def compliance_status_v1(req: Request) -> Response:
        denied = _enforce_tenant_context(req, req.query("tenant_id", "").strip())
        if denied is not None:
            return denied
        return Response(compliance_status_contract(_compliance_status_payload(store)))

    @app.route("/api/v1/compliance/frameworks", methods=["GET"])
    def compliance_frameworks_v1(req: Request) -> Response:
        denied = _enforce_tenant_context(req, req.query("tenant_id", "").strip())
        if denied is not None:
            return denied
        payload = {"frameworks": compliance_engine.list_frameworks()}
        return Response(compliance_frameworks_contract(payload))

    @app.route("/api/v1/compliance/evaluate", methods=["POST"])
    def compliance_evaluate_v1(req: Request) -> Response:
        body = req.json() or {}
        denied = _enforce_tenant_context(req, str(body.get("tenant_id", "")).strip())
        if denied is not None:
            return denied
        framework = str(body.get("framework", "")).strip()
        if not framework:
            return Response({"error": "framework is required"}, status_code=400)

        evidence = body.get("evidence") or {}
        if not isinstance(evidence, dict):
            return Response({"error": "evidence must be an object"}, status_code=400)

        try:
            result = compliance_engine.evaluate_framework(framework, evidence)
        except ValueError as exc:
            return Response({"error": str(exc)}, status_code=400)
        return Response(compliance_evaluate_contract({"result": result}))

    @app.route("/api/v1/compliance/evaluate-all", methods=["POST"])
    def compliance_evaluate_all_v1(req: Request) -> Response:
        body = req.json() or {}
        denied = _enforce_tenant_context(req, str(body.get("tenant_id", "")).strip())
        if denied is not None:
            return denied
        evidence = body.get("evidence") or {}
        if not isinstance(evidence, dict):
            return Response({"error": "evidence must be an object"}, status_code=400)
        return Response(
            compliance_evaluate_all_contract(compliance_engine.evaluate_all(evidence))
        )

    @app.route("/api/v1/analytics/trends", methods=["GET"])
    def analytics_trends_v1(req: Request) -> Response:
        denied = _enforce_tenant_context(req, req.query("tenant_id", "").strip())
        if denied is not None:
            return denied
        payload = _analytics_trends_payload(
            store,
            ledger,
            assurance_case_count=len(assurance_cases),
        )
        return Response(analytics_trends_contract(payload))

    @app.route("/api/v1/analytics/trends", methods=["POST"])
    def analytics_trends_post_v1(req: Request) -> Response:
        body = req.json() or {}
        denied = _enforce_tenant_context(req, str(body.get("tenant_id", "")).strip())
        if denied is not None:
            return denied
        snapshots = body.get("snapshots") or []
        if not isinstance(snapshots, list):
            return Response({"error": "snapshots must be a list"}, status_code=400)
        return Response(
            analytics_trends_contract(analytics_engine.trend_analysis(snapshots))
        )

    @app.route("/api/v1/analytics/benchmark", methods=["POST"])
    def analytics_benchmark_v1(req: Request) -> Response:
        body = req.json() or {}
        denied = _enforce_tenant_context(req, str(body.get("tenant_id", "")).strip())
        if denied is not None:
            return denied
        metrics = body.get("metrics") or {}
        if not isinstance(metrics, dict):
            return Response({"error": "metrics must be an object"}, status_code=400)
        industry = str(body.get("industry", "general"))
        return Response(
            analytics_benchmark_contract(
                analytics_engine.benchmark_analysis(metrics, industry=industry)
            )
        )

    @app.route("/api/v1/analytics/risks", methods=["POST"])
    def analytics_risks_v1(req: Request) -> Response:
        body = req.json() or {}
        denied = _enforce_tenant_context(req, str(body.get("tenant_id", "")).strip())
        if denied is not None:
            return denied
        metrics = body.get("metrics") or {}
        if not isinstance(metrics, dict):
            return Response({"error": "metrics must be an object"}, status_code=400)
        return Response(
            analytics_risks_contract(analytics_engine.risk_prediction(metrics))
        )

    @app.route("/api/v1/reports/schedule", methods=["POST"])
    def schedule_report_v1(req: Request) -> Response:
        body = req.json() or {}
        requested_tenant_id = str(body.get("tenant_id", "")).strip()
        denied = _enforce_tenant_context(req, requested_tenant_id)
        if denied is not None:
            return denied
        report_type = str(body.get("report_type", "executive_summary"))
        frequency = str(body.get("frequency", "daily"))
        target = str(body.get("target", "console"))
        actor_tenant_id = _request_tenant_id(req)
        job_tenant_id = requested_tenant_id or actor_tenant_id

        try:
            job = report_scheduler.schedule_report(
                report_type=report_type,
                frequency=frequency,
                target=target,
                tenant_id=job_tenant_id,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status_code=400)

        return Response(
            report_schedule_contract({"job": job.__dict__}),
            status_code=201,
        )

    @app.route("/api/v1/reports/jobs", methods=["GET"])
    def list_report_jobs_v1(req: Request) -> Response:
        requested_tenant_id = req.query("tenant_id", "").strip()
        denied = _enforce_tenant_context(req, requested_tenant_id)
        if denied is not None:
            return denied
        actor_tenant_id = _request_tenant_id(req)
        effective_tenant_id = requested_tenant_id or actor_tenant_id or None

        jobs = report_scheduler.list_jobs(tenant_id=effective_tenant_id)
        return Response(report_jobs_list_contract({"count": len(jobs), "jobs": jobs}))

    @app.route("/api/v1/reports/jobs/{job_id}", methods=["GET"])
    def get_report_job_v1(req: Request, job_id: str = "") -> Response:
        requested_tenant_id = req.query("tenant_id", "").strip()
        denied = _enforce_tenant_context(req, requested_tenant_id)
        if denied is not None:
            return denied
        actor_tenant_id = _request_tenant_id(req)
        effective_tenant_id = requested_tenant_id or actor_tenant_id or None

        job = report_scheduler.get_job(job_id, tenant_id=effective_tenant_id)
        if job is None:
            if effective_tenant_id:
                existing_job = report_scheduler.get_job(job_id)
                if existing_job is not None:
                    return Response({"error": "Cross-tenant access denied"}, status_code=403)
            return Response({"error": "Report job not found"}, status_code=404)
        return Response(report_job_detail_contract({"job": job}))

    @app.route("/api/v1/quality/metrics/trends", methods=["GET"])
    def quality_metrics_trends_v1(req: Request) -> Response:
        requested_tenant_id = req.query("tenant_id", "").strip()
        denied = _enforce_tenant_context(req, requested_tenant_id)
        if denied is not None:
            return denied
        actor_tenant_id = _request_tenant_id(req)
        effective_tenant_id = requested_tenant_id or actor_tenant_id or None
        window, window_error = _parse_int_value(req.query("window", "10"), "window", minimum=1)
        if window_error is not None:
            return window_error
        assert window is not None
        return Response(
            quality_metrics_trends_contract(
                quality_metrics_history.trend_summary(
                    window,
                    tenant_id=effective_tenant_id,
                )
            )
        )

    @app.route("/api/v1/quality/metrics/history", methods=["GET"])
    def quality_metrics_history_v1(req: Request) -> Response:
        requested_tenant_id = req.query("tenant_id", "").strip()
        denied = _enforce_tenant_context(req, requested_tenant_id)
        if denied is not None:
            return denied
        actor_tenant_id = _request_tenant_id(req)
        effective_tenant_id = requested_tenant_id or actor_tenant_id or None
        limit, limit_error = _parse_int_value(req.query("limit", "50"), "limit", minimum=1)
        if limit_error is not None:
            return limit_error
        assert limit is not None
        snapshots = quality_metrics_history.list_snapshots(
            limit=limit,
            tenant_id=effective_tenant_id,
        )
        return Response(
            quality_metrics_history_contract(
                {
                    "count": len(snapshots),
                    "snapshots": snapshots,
                }
            )
        )

    @app.route("/api/v1/quality/metrics/record", methods=["POST"])
    def quality_metrics_record_v1(req: Request) -> Response:
        body = req.json() or {}
        requested_tenant_id = str(body.get("tenant_id", "")).strip()
        denied = _enforce_tenant_context(req, requested_tenant_id)
        if denied is not None:
            return denied
        actor_tenant_id = _request_tenant_id(req)
        effective_tenant_id = requested_tenant_id or actor_tenant_id

        analytics = _analytics_trends_payload(
            store,
            ledger,
            assurance_case_count=len(assurance_cases),
        )
        risk = _risk_map_payload(store)

        score, score_error = _parse_float_value(
            body.get("score", max(0, 100 - risk["total_components"] * 2)),
            "score",
            minimum=0.0,
            maximum=100.0,
        )
        if score_error is not None:
            return score_error
        evidence_total, evidence_total_error = _parse_int_value(
            body.get("evidence_total", analytics["evidence_total"]),
            "evidence_total",
            minimum=0,
        )
        if evidence_total_error is not None:
            return evidence_total_error
        risk_components, risk_components_error = _parse_int_value(
            body.get("risk_components", risk["total_components"]),
            "risk_components",
            minimum=0,
        )
        if risk_components_error is not None:
            return risk_components_error
        assert score is not None
        assert evidence_total is not None
        assert risk_components is not None
        source = str(body.get("source", "api_record"))

        snapshot = quality_metrics_history.record_snapshot(
            score=score,
            evidence_total=evidence_total,
            risk_components=risk_components,
            source=source,
            tenant_id=effective_tenant_id,
        )
        return Response(
            quality_metrics_record_contract({"snapshot": snapshot}),
            status_code=201,
        )

    @app.route("/api/v1/quality/metrics/forecast", methods=["GET"])
    def quality_metrics_forecast_v1(req: Request) -> Response:
        requested_tenant_id = req.query("tenant_id", "").strip()
        denied = _enforce_tenant_context(req, requested_tenant_id)
        if denied is not None:
            return denied
        actor_tenant_id = _request_tenant_id(req)
        effective_tenant_id = requested_tenant_id or actor_tenant_id or None
        window, window_error = _parse_int_value(req.query("window", "10"), "window", minimum=1)
        if window_error is not None:
            return window_error
        horizon, horizon_error = _parse_int_value(
            req.query("horizon", "3"),
            "horizon",
            minimum=1,
            maximum=12,
        )
        if horizon_error is not None:
            return horizon_error
        assert window is not None
        assert horizon is not None
        return Response(
            quality_metrics_forecast_contract(
                quality_metrics_history.forecast_summary(
                    window=window,
                    horizon=horizon,
                    tenant_id=effective_tenant_id,
                )
            )
        )

    @app.route("/api/v1/compliance/reports", methods=["POST"])
    def compliance_report_create_v1(req: Request) -> Response:
        body = req.json() or {}
        tenant_id = _request_tenant_id(req)
        if not tenant_id:
            return Response(
                {"error": "X-Tenant-ID header is required"}, status_code=401
            )
        if not _tenant_exists(tenant_id):
            return Response({"error": "Unknown tenant"}, status_code=403)
        requested_tenant = str(body.get("tenant_id", "")).strip()
        if requested_tenant and requested_tenant != tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)

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
        requested_tenant = req.query("tenant_id", "").strip()
        if requested_tenant and requested_tenant != tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)

        report = compliance_report_store.get_report(report_id)
        if report is None:
            return Response({"error": "Compliance report not found"}, status_code=404)
        if report.get("tenant_id") != tenant_id:
            return Response({"error": "Cross-tenant access denied"}, status_code=403)

        return Response(compliance_report_artifact_contract({"report": report}))
