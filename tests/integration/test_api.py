"""Integration tests for the REST API."""

import json
import pytest
from civ_arcos.web.framework import Application, Request, Response, create_app


def make_request(method="GET", path="/", body=None, query_params=None):
    return Request(
        method=method,
        path=path,
        query_params=query_params or {},
        body=json.dumps(body).encode() if body else b"",
        headers={"Content-Type": "application/json"},
    )


def test_index_route():
    from civ_arcos import api

    resp = api.app.handle("GET", "/", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert "CIV-ARCOS" in data["name"]


def test_status_route():
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/status", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert "uptime_seconds" in data
    assert "version" in data


def test_not_found_route():
    from civ_arcos import api

    resp = api.app.handle("GET", "/no/such/path", {}, b"", {})
    assert resp.status_code == 404


def test_blockchain_status_route():
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/blockchain/status", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert "length" in data
    assert data["valid"] is True


def test_badge_coverage_route():
    from civ_arcos import api

    resp = api.app.handle(
        "GET", "/api/badge/coverage/owner/repo", {"coverage": ["95.0"]}, b"", {}
    )
    assert resp.status_code == 200
    body = resp.body.decode()
    assert "<svg" in body


def test_collect_evidence_mock():
    from civ_arcos import api

    body = json.dumps({"repo_url": "https://github.com/nonexistent/repo"}).encode()
    resp = api.app.handle(
        "POST",
        "/api/evidence/collect",
        {},
        body,
        {"Content-Type": "application/json", "Content-Length": str(len(body))},
    )
    assert resp.status_code == 201
    data = json.loads(resp.body)
    assert "collected" in data


def test_blockchain_add_idempotency_replays_same_response():
    """Repeated POST with same idempotency key should replay first response."""
    from civ_arcos import api

    key = "idem-blockchain-replay-001"
    payload = {"event": "test", "value": 1}
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
        "Idempotency-Key": key,
    }

    first = api.app.handle("POST", "/api/blockchain/add", {}, body, headers)
    second = api.app.handle("POST", "/api/blockchain/add", {}, body, headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert json.loads(first.body) == json.loads(second.body)
    assert second.headers.get("X-Idempotency-Replayed") == "true"


def test_blockchain_add_idempotency_conflict_on_different_payload():
    """Same key with different payload should be rejected with 409."""
    from civ_arcos import api

    key = "idem-blockchain-conflict-001"
    body_one = json.dumps({"event": "a"}).encode()
    body_two = json.dumps({"event": "b"}).encode()
    headers_one = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body_one)),
        "Idempotency-Key": key,
    }
    headers_two = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body_two)),
        "Idempotency-Key": key,
    }

    first = api.app.handle("POST", "/api/blockchain/add", {}, body_one, headers_one)
    second = api.app.handle("POST", "/api/blockchain/add", {}, body_two, headers_two)

    assert first.status_code == 201
    assert second.status_code == 409
    data = json.loads(second.body)
    assert "Idempotency key" in data["error"]


def test_sync_events_emits_block_added_event():
    """Blockchain add should emit a sync event retrievable via polling API."""
    from civ_arcos import api

    before = api.app.handle("GET", "/api/sync/events", {}, b"", {})
    assert before.status_code == 200
    before_data = json.loads(before.body)
    since_id = before_data["latest_event_id"]

    payload = {"event": "sync-emission", "value": 7}
    body = json.dumps(payload).encode()
    added = api.app.handle(
        "POST",
        "/api/blockchain/add",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert added.status_code == 201

    polled = api.app.handle(
        "GET",
        "/api/sync/events",
        {"since_id": [str(since_id)]},
        b"",
        {},
    )
    assert polled.status_code == 200
    data = json.loads(polled.body)
    assert data["mode"] == "poll"
    assert data["count"] >= 1
    last = data["events"][-1]
    assert last["topic"] == "blockchain.block_added"
    assert last["payload"]["block_index"] == json.loads(added.body)["index"]
    assert data["next_since_id"] >= last["event_id"]


def test_sync_events_idempotent_replay_does_not_emit_duplicate_event():
    """Idempotent replay should not append duplicate blockchain sync events."""
    from civ_arcos import api

    before = api.app.handle("GET", "/api/sync/events", {}, b"", {})
    assert before.status_code == 200
    since_id = json.loads(before.body)["latest_event_id"]

    key = "idem-sync-event-001"
    payload = {"event": "sync-idem", "value": 1}
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
        "Idempotency-Key": key,
    }

    first = api.app.handle("POST", "/api/blockchain/add", {}, body, headers)
    second = api.app.handle("POST", "/api/blockchain/add", {}, body, headers)
    assert first.status_code == 201
    assert second.status_code == 201

    polled = api.app.handle(
        "GET",
        "/api/sync/events",
        {"since_id": [str(since_id)]},
        b"",
        {},
    )
    assert polled.status_code == 200
    events = json.loads(polled.body)["events"]
    block_added = [event for event in events if event["topic"] == "blockchain.block_added"]
    assert len(block_added) == 1


def test_assurance_create_idempotency_replays_case_creation():
    """Assurance create should not duplicate work on retried requests."""
    from civ_arcos import api

    key = "idem-assurance-replay-001"
    payload = {
        "project_name": "Idem Project",
        "project_type": "api",
        "template": "comprehensive_quality",
    }
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
        "Idempotency-Key": key,
    }

    first = api.app.handle("POST", "/api/assurance/create", {}, body, headers)
    second = api.app.handle("POST", "/api/assurance/create", {}, body, headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert json.loads(first.body) == json.loads(second.body)
    assert second.headers.get("X-Idempotency-Replayed") == "true"


def test_v1_contract_registry_endpoint():
    """Versioned API should expose discoverable contract metadata."""
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/v1/contracts", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "ContractRegistry"
    assert data["data"]["api_version"] == "v1"
    names = {item["name"] for item in data["data"]["contracts"]}
    assert "EvidenceCollection" in names
    assert "PluginValidation" in names
    assert "PluginExecution" in names
    assert "AssuranceTemplates" in names
    assert "AssuranceAutoGenerate" in names
    assert "AnalysisStatic" in names
    assert "AnalysisSecurity" in names
    assert "AnalysisTests" in names
    assert "AnalysisComprehensive" in names


def test_v1_evidence_list_contract_shape():
    """V1 evidence list endpoint must return contract envelope + data keys."""
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/v1/evidence", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "EvidenceList"
    assert "count" in data["data"]
    assert "items" in data["data"]


def test_v1_evidence_collect_requires_tenant_header():
    """V1 evidence collect must require tenant identity."""
    from civ_arcos import api

    payload = {"repo_url": "https://github.com/nonexistent/repo"}
    body = json.dumps(payload).encode()
    resp = api.app.handle(
        "POST",
        "/api/v1/evidence/collect",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert resp.status_code == 401


def test_v1_evidence_collect_and_cross_tenant_read_denied():
    """Collected tenant evidence should not be readable by another tenant."""
    from civ_arcos import api

    payload = {"repo_url": "https://github.com/nonexistent/repo"}
    alpha_body = json.dumps(payload).encode()

    alpha_collect = api.app.handle(
        "POST",
        "/api/v1/evidence/collect",
        {},
        alpha_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(alpha_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert alpha_collect.status_code == 201
    collect_data = json.loads(alpha_collect.body)
    assert collect_data["contract"]["name"] == "EvidenceCollection"
    evidence_id = collect_data["data"]["evidence_ids"][0]

    denied = api.app.handle(
        "GET",
        f"/api/v1/evidence/{evidence_id}",
        {},
        b"",
        {"X-Tenant-ID": "org_beta"},
    )
    assert denied.status_code == 403

    allowed = api.app.handle(
        "GET",
        f"/api/v1/evidence/{evidence_id}",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert allowed.status_code == 200


def test_v1_evidence_tenant_scoped_listing():
    """V1 evidence list should scope results to caller tenant when provided."""
    from civ_arcos import api

    payload = {"repo_url": "https://github.com/nonexistent/repo"}
    alpha_body = json.dumps(payload).encode()
    beta_body = json.dumps(payload).encode()

    alpha_collect = api.app.handle(
        "POST",
        "/api/v1/evidence/collect",
        {},
        alpha_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(alpha_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    beta_collect = api.app.handle(
        "POST",
        "/api/v1/evidence/collect",
        {},
        beta_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(beta_body)),
            "X-Tenant-ID": "org_beta",
        },
    )
    assert alpha_collect.status_code == 201
    assert beta_collect.status_code == 201

    alpha_list = api.app.handle(
        "GET",
        "/api/v1/evidence",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert alpha_list.status_code == 200
    alpha_items = json.loads(alpha_list.body)["data"]["items"]
    assert alpha_items
    assert all(item.get("tenant_id") == "org_alpha" for item in alpha_items)

    denied_filter = api.app.handle(
        "GET",
        "/api/v1/evidence",
        {"tenant_id": ["org_beta"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert denied_filter.status_code == 403


def test_v1_assurance_create_and_get_contract():
    """V1 assurance create/get should use versioned contract payloads."""
    from civ_arcos import api

    payload = {
        "project_name": "Contracted Project",
        "project_type": "api",
        "template": "comprehensive_quality",
    }
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }

    created = api.app.handle("POST", "/api/v1/assurance/create", {}, body, headers)
    assert created.status_code == 201
    created_data = json.loads(created.body)
    assert created_data["contract"]["name"] == "AssuranceCaseDetail"

    case_id = created_data["data"]["case"]["case_id"]
    fetched = api.app.handle("GET", f"/api/v1/assurance/{case_id}", {}, b"", {})
    assert fetched.status_code == 200
    fetched_data = json.loads(fetched.body)
    assert fetched_data["contract"]["name"] == "AssuranceCaseDetail"
    assert fetched_data["data"]["case"]["case_id"] == case_id


def test_assurance_export_pdf_returns_pdf_bytes():
    """Legacy assurance export should return a PDF artifact for an existing case."""
    from civ_arcos import api

    payload = {
        "project_name": "Export Project",
        "project_type": "api",
        "template": "comprehensive_quality",
    }
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }

    created = api.app.handle("POST", "/api/assurance/create", {}, body, headers)
    assert created.status_code == 201
    case_id = json.loads(created.body)["case_id"]

    exported = api.app.handle(
        "GET",
        f"/api/assurance/{case_id}/export",
        {"format": ["pdf"]},
        b"",
        {},
    )
    assert exported.status_code == 200
    assert exported.content_type == "application/pdf"
    assert exported.body.startswith(b"%PDF-")
    disposition = exported.headers.get("Content-Disposition", "")
    assert case_id in disposition


def test_assurance_export_pdf_missing_case_returns_404():
    """Assurance export should return 404 for unknown assurance cases."""
    from civ_arcos import api

    resp = api.app.handle(
        "GET",
        "/api/assurance/nonexistent-case/export",
        {"format": ["pdf"]},
        b"",
        {},
    )
    assert resp.status_code == 404


def test_legacy_risk_route_still_available():
    """Legacy risk route should remain available during modularization."""
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/risk/map", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert "items" in data
    assert "total_components" in data


def test_v1_risk_map_contract_shape():
    """V1 risk endpoint should return contract envelope."""
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/v1/risk/map", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "RiskMap"
    assert "items" in data["data"]
    assert "total_components" in data["data"]


def test_v1_compliance_status_contract_shape():
    """V1 compliance endpoint should return contract envelope."""
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/v1/compliance/status", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "ComplianceStatus"
    assert "frameworks" in data["data"]


def test_v1_compliance_report_artifact_roundtrip_tenant_scoped():
    """Compliance report artifacts should be create/list/get scoped per tenant."""
    from civ_arcos import api

    created = api.app.handle(
        "POST",
        "/api/v1/compliance/reports",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert created.status_code == 201
    created_data = json.loads(created.body)
    assert created_data["contract"]["name"] == "ComplianceReportArtifact"
    report_id = created_data["data"]["report"]["report_id"]
    assert created_data["data"]["report"]["tenant_id"] == "org_alpha"

    listed = api.app.handle(
        "GET",
        "/api/v1/compliance/reports",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert listed.status_code == 200
    listed_data = json.loads(listed.body)
    assert listed_data["contract"]["name"] == "ComplianceReportList"
    assert any(item["report_id"] == report_id for item in listed_data["data"]["reports"])

    fetched = api.app.handle(
        "GET",
        f"/api/v1/compliance/reports/{report_id}",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert fetched.status_code == 200
    fetched_data = json.loads(fetched.body)
    assert fetched_data["contract"]["name"] == "ComplianceReportArtifact"
    assert fetched_data["data"]["report"]["report_id"] == report_id


def test_v1_compliance_report_requires_tenant_header():
    """Compliance report artifact endpoints should require tenant identity."""
    from civ_arcos import api

    create = api.app.handle("POST", "/api/v1/compliance/reports", {}, b"", {})
    assert create.status_code == 401

    listed = api.app.handle("GET", "/api/v1/compliance/reports", {}, b"", {})
    assert listed.status_code == 401


def test_v1_compliance_report_cross_tenant_access_denied():
    """Tenants should not access compliance report artifacts owned by others."""
    from civ_arcos import api

    created = api.app.handle(
        "POST",
        "/api/v1/compliance/reports",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert created.status_code == 201
    report_id = json.loads(created.body)["data"]["report"]["report_id"]

    denied_get = api.app.handle(
        "GET",
        f"/api/v1/compliance/reports/{report_id}",
        {},
        b"",
        {"X-Tenant-ID": "org_beta"},
    )
    assert denied_get.status_code == 403

    denied_filter = api.app.handle(
        "GET",
        "/api/v1/compliance/reports",
        {"tenant_id": ["org_alpha"]},
        b"",
        {"X-Tenant-ID": "org_beta"},
    )
    assert denied_filter.status_code == 403


def test_v1_analytics_trends_contract_shape():
    """V1 analytics endpoint should return contract envelope."""
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/v1/analytics/trends", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "AnalyticsTrends"
    assert "evidence_total" in data["data"]
    assert "by_type" in data["data"]


def test_legacy_report_schedule_and_metadata_listing():
    """Legacy report schedule endpoint should create and list metadata records."""
    from civ_arcos import api

    payload = {
        "report_type": "executive_summary",
        "frequency": "daily",
        "target": "email:ops@example.com",
    }
    body = json.dumps(payload).encode()

    created = api.app.handle(
        "POST",
        "/api/reports/schedule",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert created.status_code == 201
    created_data = json.loads(created.body)
    job = created_data["job"]
    assert job["report_type"] == "executive_summary"
    assert job["frequency"] == "daily"
    assert job["status"] == "scheduled"
    assert "next_run_at" in job

    listed = api.app.handle("GET", "/api/reports/jobs", {}, b"", {})
    assert listed.status_code == 200
    listed_data = json.loads(listed.body)
    assert any(item["job_id"] == job["job_id"] for item in listed_data["jobs"])

    fetched = api.app.handle("GET", f"/api/reports/jobs/{job['job_id']}", {}, b"", {})
    assert fetched.status_code == 200
    fetched_data = json.loads(fetched.body)
    assert fetched_data["job"]["job_id"] == job["job_id"]


def test_report_schedule_rejects_invalid_frequency():
    """Report scheduling should reject unsupported frequencies."""
    from civ_arcos import api

    payload = {
        "report_type": "executive_summary",
        "frequency": "yearly",
        "target": "console",
    }
    body = json.dumps(payload).encode()

    resp = api.app.handle(
        "POST",
        "/api/reports/schedule",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert resp.status_code == 400


def test_v1_report_schedule_contract_shape():
    """V1 report schedule endpoint should return contract envelope metadata."""
    from civ_arcos import api

    payload = {
        "report_type": "compliance_snapshot",
        "frequency": "weekly",
        "target": "s3://reports-bucket",
    }
    body = json.dumps(payload).encode()

    resp = api.app.handle(
        "POST",
        "/api/v1/reports/schedule",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert resp.status_code == 201
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "ReportSchedule"
    assert data["contract"]["version"] == "v1"
    assert data["data"]["job"]["frequency"] == "weekly"


def test_legacy_quality_metrics_record_and_trends():
    """Quality metrics record and trends endpoints should return deterministic history."""
    from civ_arcos import api

    body_one = json.dumps(
        {
            "score": 71.5,
            "evidence_total": 10,
            "risk_components": 6,
            "source": "pytest",
        }
    ).encode()
    body_two = json.dumps(
        {
            "score": 75.0,
            "evidence_total": 12,
            "risk_components": 5,
            "source": "pytest",
        }
    ).encode()

    headers_one = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body_one)),
    }
    headers_two = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body_two)),
    }

    first = api.app.handle(
        "POST",
        "/api/quality/metrics/record",
        {},
        body_one,
        headers_one,
    )
    second = api.app.handle(
        "POST",
        "/api/quality/metrics/record",
        {},
        body_two,
        headers_two,
    )
    assert first.status_code == 201
    assert second.status_code == 201

    history = api.app.handle(
        "GET",
        "/api/quality/metrics/history",
        {"limit": ["5"]},
        b"",
        {},
    )
    assert history.status_code == 200
    history_data = json.loads(history.body)
    assert history_data["snapshots"]
    assert "snapshot_id" in history_data["snapshots"][0]

    trends = api.app.handle(
        "GET",
        "/api/quality/metrics/trends",
        {"window": ["5"]},
        b"",
        {},
    )
    assert trends.status_code == 200
    trend_data = json.loads(trends.body)
    assert trend_data["count"] >= 2
    assert trend_data["current_score"] is not None
    assert "points" in trend_data


def test_v1_quality_metrics_trends_contract_shape():
    """V1 quality metrics trends endpoint should return contract envelope."""
    from civ_arcos import api

    resp = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/trends",
        {"window": ["5"]},
        b"",
        {},
    )
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "QualityMetricsTrends"
    assert "count" in data["data"]
    assert "points" in data["data"]


def test_legacy_quality_metrics_forecast_is_deterministic():
    """Legacy quality forecast should return deterministic projections."""
    from civ_arcos import api

    records = [
        {"score": 61.0, "evidence_total": 5, "risk_components": 4, "source": "forecast"},
        {"score": 66.0, "evidence_total": 6, "risk_components": 4, "source": "forecast"},
        {"score": 71.0, "evidence_total": 7, "risk_components": 3, "source": "forecast"},
    ]
    for payload in records:
        body = json.dumps(payload).encode()
        resp = api.app.handle(
            "POST",
            "/api/quality/metrics/record",
            {},
            body,
            {
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
            },
        )
        assert resp.status_code == 201

    forecast = api.app.handle(
        "GET",
        "/api/quality/metrics/forecast",
        {"window": ["3"], "horizon": ["2"]},
        b"",
        {},
    )
    assert forecast.status_code == 200
    data = json.loads(forecast.body)
    assert data["count"] >= 3
    assert data["horizon"] == 2
    assert len(data["forecast"]) == 2
    assert data["forecast"][0]["projected_score"] == 76.0
    assert data["forecast"][1]["projected_score"] == 81.0


def test_v1_quality_metrics_forecast_contract_shape():
    """V1 quality forecast endpoint should return contract envelope."""
    from civ_arcos import api

    resp = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/forecast",
        {"window": ["3"], "horizon": ["2"]},
        b"",
        {},
    )
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "QualityMetricsForecast"
    assert "forecast" in data["data"]
    assert "trend_slope" in data["data"]


def test_legacy_tenants_and_settings_routes_available():
    """Legacy tenants/settings endpoints remain available after extraction."""
    from civ_arcos import api

    tenants_resp = api.app.handle("GET", "/api/tenants", {}, b"", {})
    assert tenants_resp.status_code == 200
    tenants_data = json.loads(tenants_resp.body)
    assert "tenants" in tenants_data

    settings_resp = api.app.handle("GET", "/api/settings", {}, b"", {})
    assert settings_resp.status_code == 200
    settings_data = json.loads(settings_resp.body)
    assert "host" in settings_data
    assert "port" in settings_data


def test_v1_tenants_list_and_create_contract_shape():
    """V1 tenants endpoints should return contract envelopes."""
    from civ_arcos import api

    listed = api.app.handle("GET", "/api/v1/tenants", {}, b"", {})
    assert listed.status_code == 200
    listed_data = json.loads(listed.body)
    assert listed_data["contract"]["name"] == "TenantsList"
    assert "tenants" in listed_data["data"]

    payload = {"name": "V1 Tenant", "plan": "pro"}
    body = json.dumps(payload).encode()
    created = api.app.handle(
        "POST",
        "/api/v1/tenants",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert created.status_code == 201
    created_data = json.loads(created.body)
    assert created_data["contract"]["name"] == "TenantDetail"
    assert created_data["data"]["tenant"]["name"] == "V1 Tenant"


def test_v1_settings_get_and_update_contract_shape():
    """V1 settings endpoints should return contract envelopes."""
    from civ_arcos import api

    tenant_headers = {"X-Tenant-ID": "org_alpha"}

    current = api.app.handle("GET", "/api/v1/settings", {}, b"", tenant_headers)
    assert current.status_code == 200
    current_data = json.loads(current.body)
    assert current_data["contract"]["name"] == "SettingsState"
    assert "host" in current_data["data"]
    assert current_data["data"]["tenant_id"] == "org_alpha"

    payload = {"log_level": "DEBUG"}
    body = json.dumps(payload).encode()
    updated = api.app.handle(
        "POST",
        "/api/v1/settings",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert updated.status_code == 200
    updated_data = json.loads(updated.body)
    assert updated_data["contract"]["name"] == "SettingsUpdate"
    assert updated_data["data"]["updated"] is True
    assert "log_level" in updated_data["data"]["keys"]
    assert updated_data["data"]["tenant_id"] == "org_alpha"


def test_v1_settings_require_tenant_header():
    """V1 settings access should reject requests without tenant identity."""
    from civ_arcos import api

    current = api.app.handle("GET", "/api/v1/settings", {}, b"", {})
    assert current.status_code == 401

    payload = {"log_level": "INFO"}
    body = json.dumps(payload).encode()
    updated = api.app.handle(
        "POST",
        "/api/v1/settings",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert updated.status_code == 401


def test_v1_settings_cross_tenant_access_denied():
    """Tenant should not read or write settings for a different tenant."""
    from civ_arcos import api

    read_denied = api.app.handle(
        "GET",
        "/api/v1/settings",
        {"tenant_id": ["org_beta"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert read_denied.status_code == 403

    payload = {"tenant_id": "org_beta", "log_level": "WARNING"}
    body = json.dumps(payload).encode()
    write_denied = api.app.handle(
        "POST",
        "/api/v1/settings",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert write_denied.status_code == 403


def test_v1_settings_tenant_isolation_roundtrip():
    """Per-tenant settings updates must not leak across tenants."""
    from civ_arcos import api

    alpha_body = json.dumps({"log_level": "DEBUG"}).encode()
    beta_body = json.dumps({"log_level": "ERROR"}).encode()

    alpha_update = api.app.handle(
        "POST",
        "/api/v1/settings",
        {},
        alpha_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(alpha_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    beta_update = api.app.handle(
        "POST",
        "/api/v1/settings",
        {},
        beta_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(beta_body)),
            "X-Tenant-ID": "org_beta",
        },
    )
    assert alpha_update.status_code == 200
    assert beta_update.status_code == 200

    alpha_get = api.app.handle(
        "GET",
        "/api/v1/settings",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    beta_get = api.app.handle(
        "GET",
        "/api/v1/settings",
        {},
        b"",
        {"X-Tenant-ID": "org_beta"},
    )
    assert alpha_get.status_code == 200
    assert beta_get.status_code == 200

    alpha_data = json.loads(alpha_get.body)
    beta_data = json.loads(beta_get.body)
    assert alpha_data["data"]["log_level"] == "DEBUG"
    assert beta_data["data"]["log_level"] == "ERROR"


def test_v1_tenants_cross_tenant_filter_denied():
    """Tenant-scoped tenant list should block cross-tenant filter attempts."""
    from civ_arcos import api

    denied = api.app.handle(
        "GET",
        "/api/v1/tenants",
        {"tenant_id": ["org_beta"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert denied.status_code == 403

    allowed = api.app.handle(
        "GET",
        "/api/v1/tenants",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert allowed.status_code == 200
    allowed_data = json.loads(allowed.body)
    assert allowed_data["data"]["count"] == 1
    assert allowed_data["data"]["tenants"][0]["id"] == "org_alpha"


def test_v1_assurance_templates_and_auto_generate_contract_shape():
    """V1 assurance templates/auto-generate should return contract envelopes."""
    from civ_arcos import api

    templates = api.app.handle("GET", "/api/v1/assurance/templates", {}, b"", {})
    assert templates.status_code == 200
    templates_data = json.loads(templates.body)
    assert templates_data["contract"]["name"] == "AssuranceTemplates"
    assert "templates" in templates_data["data"]

    payload = {
        "project_name": "Auto Contracted",
        "project_type": "general",
        "evidence_ids": [],
    }
    body = json.dumps(payload).encode()
    created = api.app.handle(
        "POST",
        "/api/v1/assurance/auto-generate",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert created.status_code == 201
    created_data = json.loads(created.body)
    assert created_data["contract"]["name"] == "AssuranceAutoGenerate"
    assert "case_id" in created_data["data"]["case"]


def test_v1_analysis_contract_shape():
    """V1 analysis endpoints should return versioned contract envelopes."""
    from civ_arcos import api

    source_payload = {"source_path": "civ_arcos"}
    body = json.dumps(source_payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }

    static_resp = api.app.handle("POST", "/api/v1/analysis/static", {}, body, headers)
    assert static_resp.status_code == 200
    static_data = json.loads(static_resp.body)
    assert static_data["contract"]["name"] == "AnalysisStatic"
    assert "results" in static_data["data"]

    security_resp = api.app.handle(
        "POST", "/api/v1/analysis/security", {}, body, headers
    )
    assert security_resp.status_code == 200
    security_data = json.loads(security_resp.body)
    assert security_data["contract"]["name"] == "AnalysisSecurity"
    assert "score" in security_data["data"]

    tests_resp = api.app.handle("POST", "/api/v1/analysis/tests", {}, body, headers)
    assert tests_resp.status_code == 200
    tests_data = json.loads(tests_resp.body)
    assert tests_data["contract"]["name"] == "AnalysisTests"
    assert "results" in tests_data["data"]

    comp_resp = api.app.handle(
        "POST", "/api/v1/analysis/comprehensive", {}, body, headers
    )
    assert comp_resp.status_code == 200
    comp_data = json.loads(comp_resp.body)
    assert comp_data["contract"]["name"] == "AnalysisComprehensive"
    assert "evidence_collected" in comp_data["data"]
