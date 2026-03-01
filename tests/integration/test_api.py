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
    block_added = [
        event for event in events if event["topic"] == "blockchain.block_added"
    ]
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
    assert "ReportSchedule" in names


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


def test_step6_v1_evidence_collect_rejects_invalid_payload_shape():
    """V1 evidence collect should return 400 for invalid body shapes/types."""
    from civ_arcos import api

    non_object = json.dumps(["https://github.com/nonexistent/repo"]).encode()
    non_object_resp = api.app.handle(
        "POST",
        "/api/v1/evidence/collect",
        {},
        non_object,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(non_object)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert non_object_resp.status_code == 400

    missing_repo = json.dumps({"token": "abc"}).encode()
    missing_repo_resp = api.app.handle(
        "POST",
        "/api/v1/evidence/collect",
        {},
        missing_repo,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(missing_repo)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert missing_repo_resp.status_code == 400

    bad_token = json.dumps(
        {"repo_url": "https://github.com/nonexistent/repo", "token": 123}
    ).encode()
    bad_token_resp = api.app.handle(
        "POST",
        "/api/v1/evidence/collect",
        {},
        bad_token,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(bad_token)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert bad_token_resp.status_code == 400


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


def test_step6_v1_evidence_unknown_tenant_query_rejected():
    """V1 evidence list/get should reject unknown tenant query filters."""
    from civ_arcos import api

    list_resp = api.app.handle(
        "GET",
        "/api/v1/evidence",
        {"tenant_id": ["tenant_unknown"]},
        b"",
        {},
    )
    assert list_resp.status_code == 403

    get_resp = api.app.handle(
        "GET",
        "/api/v1/evidence/nonexistent",
        {"tenant_id": ["tenant_unknown"]},
        b"",
        {},
    )
    assert get_resp.status_code == 403


def test_step6_v1_evidence_get_query_tenant_mismatch_denied():
    """V1 evidence get should deny tenant_id query mismatch with header context."""
    from civ_arcos import api

    payload = {"repo_url": "https://github.com/nonexistent/repo"}
    body = json.dumps(payload).encode()
    created = api.app.handle(
        "POST",
        "/api/v1/evidence/collect",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert created.status_code == 201
    evidence_id = json.loads(created.body)["data"]["evidence_ids"][0]

    denied = api.app.handle(
        "GET",
        f"/api/v1/evidence/{evidence_id}",
        {"tenant_id": ["org_beta"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert denied.status_code == 403


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


def test_step6_v1_risk_status_reject_unknown_tenant_header():
    """V1 risk/status read endpoints should reject unknown tenant identity context."""
    from civ_arcos import api

    risk = api.app.handle(
        "GET",
        "/api/v1/risk/map",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert risk.status_code == 403

    compliance_status = api.app.handle(
        "GET",
        "/api/v1/compliance/status",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert compliance_status.status_code == 403


def test_step6_v1_risk_status_cross_tenant_mismatch_denied():
    """V1 risk/status should deny tenant_id query mismatches with tenant header."""
    from civ_arcos import api

    risk_denied = api.app.handle(
        "GET",
        "/api/v1/risk/map",
        {"tenant_id": ["org_beta"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert risk_denied.status_code == 403

    status_denied = api.app.handle(
        "GET",
        "/api/v1/compliance/status",
        {"tenant_id": ["org_beta"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert status_denied.status_code == 403

    risk_allowed = api.app.handle(
        "GET",
        "/api/v1/risk/map",
        {"tenant_id": ["org_alpha"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert risk_allowed.status_code == 200


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
    assert any(
        item["report_id"] == report_id for item in listed_data["data"]["reports"]
    )

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


def test_step6_v1_compliance_report_create_body_tenant_mismatch_denied():
    """Compliance report create should deny mismatched body/header tenant context."""
    from civ_arcos import api

    mismatched_body = json.dumps({"tenant_id": "org_beta"}).encode()
    denied = api.app.handle(
        "POST",
        "/api/v1/compliance/reports",
        {},
        mismatched_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(mismatched_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert denied.status_code == 403

    matched_body = json.dumps({"tenant_id": "org_alpha"}).encode()
    allowed = api.app.handle(
        "POST",
        "/api/v1/compliance/reports",
        {},
        matched_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(matched_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert allowed.status_code == 201


def test_step6_v1_compliance_report_get_tenant_query_mismatch_denied():
    """Compliance report get should deny tenant_id query mismatches."""
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

    denied = api.app.handle(
        "GET",
        f"/api/v1/compliance/reports/{report_id}",
        {"tenant_id": ["org_beta"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert denied.status_code == 403

    allowed = api.app.handle(
        "GET",
        f"/api/v1/compliance/reports/{report_id}",
        {"tenant_id": ["org_alpha"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert allowed.status_code == 200


def test_step6_v1_compliance_reports_reject_unknown_tenant_header():
    """Compliance report v1 endpoints should reject unknown tenant identity."""
    from civ_arcos import api

    created = api.app.handle(
        "POST",
        "/api/v1/compliance/reports",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert created.status_code == 403

    listed = api.app.handle(
        "GET",
        "/api/v1/compliance/reports",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert listed.status_code == 403

    fetched = api.app.handle(
        "GET",
        "/api/v1/compliance/reports/rpt_missing",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert fetched.status_code == 403


def test_v1_analytics_trends_contract_shape():
    """V1 analytics endpoint should return contract envelope."""
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/v1/analytics/trends", {}, b"", {})
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "AnalyticsTrends"
    assert "evidence_total" in data["data"]
    assert "by_type" in data["data"]


def test_step6_v1_compliance_frameworks_contract_shape():
    """V1 compliance frameworks endpoint should return contract envelope."""
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/v1/compliance/frameworks", {}, b"", {})

    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "ComplianceFrameworks"
    assert len(data["data"]["frameworks"]) == 5


def test_step6_v1_compliance_evaluate_contract_shape():
    """V1 compliance evaluate endpoint should return contract envelope."""
    from civ_arcos import api

    payload = {
        "framework": "ISO 27001",
        "evidence": {
            "vulnerability_management": True,
            "secure_development": True,
            "change_management": True,
            "event_logging": True,
            "secure_principles": True,
        },
    }
    body = json.dumps(payload).encode()
    resp = api.app.handle(
        "POST",
        "/api/v1/compliance/evaluate",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )

    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "ComplianceEvaluate"
    assert data["data"]["result"]["framework"] == "ISO 27001"


def test_step6_v1_compliance_evaluate_all_contract_shape():
    """V1 compliance evaluate-all endpoint should return contract envelope."""
    from civ_arcos import api

    payload = {
        "evidence": {
            "vulnerability_management": True,
            "secure_development": True,
            "change_management": True,
            "event_logging": True,
            "secure_principles": True,
            "access_controls": True,
            "data_integrity": True,
            "audit_trails": True,
            "audit_controls": True,
            "transmission_security": True,
            "security_testing": True,
            "vulnerability_scanning": True,
            "account_management": True,
            "change_control": True,
            "security_assessment": True,
            "flaw_remediation": True,
            "input_validation": True,
        }
    }
    body = json.dumps(payload).encode()
    resp = api.app.handle(
        "POST",
        "/api/v1/compliance/evaluate-all",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )

    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "ComplianceEvaluateAll"
    assert data["data"]["framework_count"] == 5


def test_step6_v1_analytics_post_endpoints_contract_shape():
    """V1 analytics POST endpoints should return versioned contract envelopes."""
    from civ_arcos import api

    trends_body = json.dumps(
        {
            "snapshots": [
                {
                    "quality_score": 70,
                    "coverage": 68,
                    "vulnerability_count": 12,
                    "technical_debt": 45,
                    "team_productivity": 72,
                },
                {
                    "quality_score": 78,
                    "coverage": 74,
                    "vulnerability_count": 8,
                    "technical_debt": 38,
                    "team_productivity": 76,
                },
            ]
        }
    ).encode()
    trends = api.app.handle(
        "POST",
        "/api/v1/analytics/trends",
        {},
        trends_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(trends_body)),
        },
    )
    assert trends.status_code == 200
    trends_data = json.loads(trends.body)
    assert trends_data["contract"]["name"] == "AnalyticsTrends"

    benchmark_body = json.dumps(
        {
            "industry": "finance",
            "metrics": {
                "quality_score": 80,
                "coverage": 78,
                "vulnerability_count": 6,
                "technical_debt": 30,
                "team_productivity": 72,
            },
        }
    ).encode()
    benchmark = api.app.handle(
        "POST",
        "/api/v1/analytics/benchmark",
        {},
        benchmark_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(benchmark_body)),
        },
    )
    assert benchmark.status_code == 200
    benchmark_data = json.loads(benchmark.body)
    assert benchmark_data["contract"]["name"] == "AnalyticsBenchmark"

    risks_body = json.dumps(
        {
            "metrics": {
                "quality_score": 60,
                "coverage": 55,
                "vulnerability_count": 16,
                "technical_debt": 65,
                "team_productivity": 58,
            }
        }
    ).encode()
    risks = api.app.handle(
        "POST",
        "/api/v1/analytics/risks",
        {},
        risks_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(risks_body)),
        },
    )
    assert risks.status_code == 200
    risks_data = json.loads(risks.body)
    assert risks_data["contract"]["name"] == "AnalyticsRisks"


def test_step6_v1_compliance_analytics_reject_unknown_tenant_header():
    """V1 compliance/analytics should reject unknown tenant identity context."""
    from civ_arcos import api

    frameworks = api.app.handle(
        "GET",
        "/api/v1/compliance/frameworks",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert frameworks.status_code == 403

    benchmark_body = json.dumps(
        {
            "metrics": {
                "quality_score": 80,
                "coverage": 75,
                "vulnerability_count": 7,
                "technical_debt": 35,
                "team_productivity": 72,
            }
        }
    ).encode()
    benchmark = api.app.handle(
        "POST",
        "/api/v1/analytics/benchmark",
        {},
        benchmark_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(benchmark_body)),
            "X-Tenant-ID": "tenant_unknown",
        },
    )
    assert benchmark.status_code == 403


def test_step6_v1_compliance_analytics_cross_tenant_mismatch_denied():
    """V1 compliance/analytics should deny mismatched tenant context."""
    from civ_arcos import api

    frameworks_denied = api.app.handle(
        "GET",
        "/api/v1/compliance/frameworks",
        {"tenant_id": ["org_beta"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert frameworks_denied.status_code == 403

    evaluate_body = json.dumps(
        {
            "tenant_id": "org_beta",
            "framework": "SOX",
            "evidence": {
                "access_controls": True,
                "change_management": True,
                "data_integrity": True,
                "audit_trails": True,
            },
        }
    ).encode()
    evaluate_denied = api.app.handle(
        "POST",
        "/api/v1/compliance/evaluate",
        {},
        evaluate_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(evaluate_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert evaluate_denied.status_code == 403

    risks_body = json.dumps(
        {
            "tenant_id": "org_beta",
            "metrics": {
                "quality_score": 62,
                "coverage": 58,
                "vulnerability_count": 14,
                "technical_debt": 60,
                "team_productivity": 60,
            },
        }
    ).encode()
    risks_denied = api.app.handle(
        "POST",
        "/api/v1/analytics/risks",
        {},
        risks_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(risks_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert risks_denied.status_code == 403


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
    assert data["contract"]["version"] == "1.0"
    assert data["data"]["job"]["frequency"] == "weekly"


def test_step6_v1_report_jobs_list_and_detail_contract_shape():
    """V1 report jobs list/detail endpoints should return contract envelopes."""
    from civ_arcos import api

    schedule_payload = {
        "report_type": "executive_summary",
        "frequency": "daily",
        "target": "console",
    }
    schedule_body = json.dumps(schedule_payload).encode()
    scheduled = api.app.handle(
        "POST",
        "/api/v1/reports/schedule",
        {},
        schedule_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(schedule_body)),
        },
    )
    assert scheduled.status_code == 201
    scheduled_job_id = json.loads(scheduled.body)["data"]["job"]["job_id"]

    listed = api.app.handle("GET", "/api/v1/reports/jobs", {}, b"", {})
    assert listed.status_code == 200
    listed_data = json.loads(listed.body)
    assert listed_data["contract"]["name"] == "ReportJobsList"
    assert listed_data["data"]["count"] >= 1
    assert any(job["job_id"] == scheduled_job_id for job in listed_data["data"]["jobs"])

    detailed = api.app.handle(
        "GET",
        f"/api/v1/reports/jobs/{scheduled_job_id}",
        {},
        b"",
        {},
    )
    assert detailed.status_code == 200
    detail_data = json.loads(detailed.body)
    assert detail_data["contract"]["name"] == "ReportJobDetail"
    assert detail_data["data"]["job"]["job_id"] == scheduled_job_id


def test_step6_v1_report_jobs_reject_unknown_tenant_header():
    """V1 report jobs endpoints should reject unknown tenant identity context."""
    from civ_arcos import api

    listed = api.app.handle(
        "GET",
        "/api/v1/reports/jobs",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert listed.status_code == 403

    detail = api.app.handle(
        "GET",
        "/api/v1/reports/jobs/rpt_missing",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert detail.status_code == 403


def test_step6_v1_report_jobs_cross_tenant_mismatch_denied():
    """V1 report jobs endpoints should deny tenant_id query mismatches."""
    from civ_arcos import api

    listed_denied = api.app.handle(
        "GET",
        "/api/v1/reports/jobs",
        {"tenant_id": ["org_beta"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert listed_denied.status_code == 403

    detail_denied = api.app.handle(
        "GET",
        "/api/v1/reports/jobs/rpt_missing",
        {"tenant_id": ["org_beta"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert detail_denied.status_code == 403

    listed_allowed = api.app.handle(
        "GET",
        "/api/v1/reports/jobs",
        {"tenant_id": ["org_alpha"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert listed_allowed.status_code == 200


def test_step6_v1_report_jobs_tenant_scoped_visibility():
    """V1 report jobs listing should be scoped to the caller tenant context."""
    from civ_arcos import api

    alpha_payload = {
        "report_type": "tenant_alpha_summary",
        "frequency": "daily",
        "target": "console",
    }
    alpha_body = json.dumps(alpha_payload).encode()
    alpha_scheduled = api.app.handle(
        "POST",
        "/api/v1/reports/schedule",
        {},
        alpha_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(alpha_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert alpha_scheduled.status_code == 201
    alpha_job_id = json.loads(alpha_scheduled.body)["data"]["job"]["job_id"]

    beta_payload = {
        "report_type": "tenant_beta_summary",
        "frequency": "daily",
        "target": "console",
    }
    beta_body = json.dumps(beta_payload).encode()
    beta_scheduled = api.app.handle(
        "POST",
        "/api/v1/reports/schedule",
        {},
        beta_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(beta_body)),
            "X-Tenant-ID": "org_beta",
        },
    )
    assert beta_scheduled.status_code == 201
    beta_job_id = json.loads(beta_scheduled.body)["data"]["job"]["job_id"]

    alpha_listed = api.app.handle(
        "GET",
        "/api/v1/reports/jobs",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert alpha_listed.status_code == 200
    alpha_jobs = json.loads(alpha_listed.body)["data"]["jobs"]
    alpha_ids = {job["job_id"] for job in alpha_jobs}
    assert alpha_job_id in alpha_ids
    assert beta_job_id not in alpha_ids

    beta_listed = api.app.handle(
        "GET",
        "/api/v1/reports/jobs",
        {},
        b"",
        {"X-Tenant-ID": "org_beta"},
    )
    assert beta_listed.status_code == 200
    beta_jobs = json.loads(beta_listed.body)["data"]["jobs"]
    beta_ids = {job["job_id"] for job in beta_jobs}
    assert beta_job_id in beta_ids
    assert alpha_job_id not in beta_ids


def test_step6_v1_report_job_detail_cross_tenant_forbidden():
    """V1 report job detail should deny access when job tenant differs."""
    from civ_arcos import api

    payload = {
        "report_type": "tenant_alpha_sensitive",
        "frequency": "daily",
        "target": "console",
    }
    body = json.dumps(payload).encode()
    scheduled = api.app.handle(
        "POST",
        "/api/v1/reports/schedule",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert scheduled.status_code == 201
    job_id = json.loads(scheduled.body)["data"]["job"]["job_id"]

    denied = api.app.handle(
        "GET",
        f"/api/v1/reports/jobs/{job_id}",
        {},
        b"",
        {"X-Tenant-ID": "org_beta"},
    )
    assert denied.status_code == 403

    allowed = api.app.handle(
        "GET",
        f"/api/v1/reports/jobs/{job_id}",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert allowed.status_code == 200


def test_step6_v1_report_schedule_rejects_unknown_tenant_header():
    """V1 report scheduling should reject unknown tenant identity context."""
    from civ_arcos import api

    payload = {
        "report_type": "executive_summary",
        "frequency": "daily",
        "target": "console",
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
            "X-Tenant-ID": "tenant_unknown",
        },
    )
    assert resp.status_code == 403


def test_step6_v1_report_schedule_cross_tenant_mismatch_denied():
    """V1 report scheduling should deny mismatched body/header tenant context."""
    from civ_arcos import api

    payload = {
        "tenant_id": "org_beta",
        "report_type": "executive_summary",
        "frequency": "daily",
        "target": "console",
    }
    body = json.dumps(payload).encode()

    denied = api.app.handle(
        "POST",
        "/api/v1/reports/schedule",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert denied.status_code == 403

    allowed_payload = {
        "tenant_id": "org_alpha",
        "report_type": "executive_summary",
        "frequency": "daily",
        "target": "console",
    }
    allowed_body = json.dumps(allowed_payload).encode()
    allowed = api.app.handle(
        "POST",
        "/api/v1/reports/schedule",
        {},
        allowed_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(allowed_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert allowed.status_code == 201


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


def test_legacy_quality_metrics_invalid_numeric_inputs_return_400():
    """Legacy quality metrics endpoints should return 400 on invalid numbers."""
    from civ_arcos import api

    bad_record = json.dumps(
        {
            "score": "not-a-number",
            "evidence_total": 5,
            "risk_components": 2,
        }
    ).encode()
    record_resp = api.app.handle(
        "POST",
        "/api/quality/metrics/record",
        {},
        bad_record,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(bad_record)),
        },
    )
    assert record_resp.status_code == 400

    history_resp = api.app.handle(
        "GET",
        "/api/quality/metrics/history",
        {"limit": ["0"]},
        b"",
        {},
    )
    assert history_resp.status_code == 400

    forecast_resp = api.app.handle(
        "GET",
        "/api/quality/metrics/forecast",
        {"window": ["3"], "horizon": ["999"]},
        b"",
        {},
    )
    assert forecast_resp.status_code == 400


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


def test_step6_v1_quality_metrics_history_contract_shape():
    """V1 quality metrics history endpoint should return contract envelope."""
    from civ_arcos import api

    resp = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/history",
        {"limit": ["5"]},
        b"",
        {},
    )
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "QualityMetricsHistory"
    assert "count" in data["data"]
    assert "snapshots" in data["data"]


def test_step6_v1_quality_metrics_record_contract_shape():
    """V1 quality metrics record endpoint should return contract envelope."""
    from civ_arcos import api

    payload = {
        "score": 77.5,
        "evidence_total": 14,
        "risk_components": 4,
        "source": "v1_contract_test",
    }
    body = json.dumps(payload).encode()

    resp = api.app.handle(
        "POST",
        "/api/v1/quality/metrics/record",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert resp.status_code == 201
    data = json.loads(resp.body)
    assert data["contract"]["name"] == "QualityMetricsRecord"
    assert "snapshot_id" in data["data"]["snapshot"]


def test_step6_v1_quality_metrics_record_reject_unknown_tenant_header():
    """V1 quality metrics record should reject unknown tenant context."""
    from civ_arcos import api

    payload = {
        "score": 70,
        "evidence_total": 9,
        "risk_components": 3,
        "source": "v1_unknown_tenant",
    }
    body = json.dumps(payload).encode()

    resp = api.app.handle(
        "POST",
        "/api/v1/quality/metrics/record",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "X-Tenant-ID": "tenant_unknown",
        },
    )
    assert resp.status_code == 403


def test_step6_v1_quality_metrics_record_cross_tenant_mismatch_denied():
    """V1 quality record should deny tenant mismatch and allow matching context."""
    from civ_arcos import api

    denied_body = json.dumps(
        {
            "tenant_id": "org_beta",
            "score": 72,
            "evidence_total": 11,
            "risk_components": 4,
            "source": "v1_tenant_mismatch",
        }
    ).encode()
    denied = api.app.handle(
        "POST",
        "/api/v1/quality/metrics/record",
        {},
        denied_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(denied_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert denied.status_code == 403

    allowed_body = json.dumps(
        {
            "tenant_id": "org_alpha",
            "score": 74,
            "evidence_total": 12,
            "risk_components": 4,
            "source": "v1_tenant_match",
        }
    ).encode()
    allowed = api.app.handle(
        "POST",
        "/api/v1/quality/metrics/record",
        {},
        allowed_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(allowed_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert allowed.status_code == 201


def test_legacy_quality_metrics_forecast_is_deterministic():
    """Legacy quality forecast should return deterministic projections."""
    from civ_arcos import api

    records = [
        {
            "score": 61.0,
            "evidence_total": 5,
            "risk_components": 4,
            "source": "forecast",
        },
        {
            "score": 66.0,
            "evidence_total": 6,
            "risk_components": 4,
            "source": "forecast",
        },
        {
            "score": 71.0,
            "evidence_total": 7,
            "risk_components": 3,
            "source": "forecast",
        },
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


def test_step6_v1_quality_metrics_invalid_numeric_inputs_return_400():
    """V1 quality metrics endpoints should return 400 on invalid numbers."""
    from civ_arcos import api

    bad_record = json.dumps(
        {
            "score": 120,
            "evidence_total": 5,
            "risk_components": 2,
            "source": "invalid_numeric",
        }
    ).encode()
    record_resp = api.app.handle(
        "POST",
        "/api/v1/quality/metrics/record",
        {},
        bad_record,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(bad_record)),
        },
    )
    assert record_resp.status_code == 400

    history_resp = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/history",
        {"limit": ["abc"]},
        b"",
        {},
    )
    assert history_resp.status_code == 400

    forecast_resp = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/forecast",
        {"window": ["1"], "horizon": ["0"]},
        b"",
        {},
    )
    assert forecast_resp.status_code == 400


def test_step6_v1_quality_metrics_reject_unknown_tenant_header():
    """V1 quality metrics endpoints should reject unknown tenant context."""
    from civ_arcos import api

    trends = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/trends",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert trends.status_code == 403

    forecast = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/forecast",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert forecast.status_code == 403

    history = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/history",
        {},
        b"",
        {"X-Tenant-ID": "tenant_unknown"},
    )
    assert history.status_code == 403


def test_step6_v1_quality_metrics_cross_tenant_mismatch_denied():
    """V1 quality metrics should deny tenant_id query mismatch with tenant header."""
    from civ_arcos import api

    trends_denied = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/trends",
        {"tenant_id": ["org_beta"], "window": ["5"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert trends_denied.status_code == 403

    forecast_denied = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/forecast",
        {"tenant_id": ["org_beta"], "window": ["3"], "horizon": ["2"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert forecast_denied.status_code == 403

    history_denied = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/history",
        {"tenant_id": ["org_beta"], "limit": ["5"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert history_denied.status_code == 403

    trends_allowed = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/trends",
        {"tenant_id": ["org_alpha"], "window": ["5"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert trends_allowed.status_code == 200

    history_allowed = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/history",
        {"tenant_id": ["org_alpha"], "limit": ["5"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert history_allowed.status_code == 200


def test_step6_v1_quality_metrics_tenant_scoped_trends_and_forecast():
    """V1 quality metrics trends/forecast should scope data to caller tenant."""
    from civ_arcos import api

    alpha_records = [
        {
            "score": 12.0,
            "evidence_total": 5,
            "risk_components": 7,
            "source": "tenant_alpha_scope",
        },
        {
            "score": 14.0,
            "evidence_total": 6,
            "risk_components": 6,
            "source": "tenant_alpha_scope",
        },
    ]
    beta_records = [
        {
            "score": 88.0,
            "evidence_total": 8,
            "risk_components": 2,
            "source": "tenant_beta_scope",
        },
        {
            "score": 91.0,
            "evidence_total": 9,
            "risk_components": 2,
            "source": "tenant_beta_scope",
        },
    ]

    for payload in alpha_records:
        body = json.dumps(payload).encode()
        resp = api.app.handle(
            "POST",
            "/api/v1/quality/metrics/record",
            {},
            body,
            {
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "X-Tenant-ID": "org_alpha",
            },
        )
        assert resp.status_code == 201

    for payload in beta_records:
        body = json.dumps(payload).encode()
        resp = api.app.handle(
            "POST",
            "/api/v1/quality/metrics/record",
            {},
            body,
            {
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "X-Tenant-ID": "org_beta",
            },
        )
        assert resp.status_code == 201

    alpha_trends = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/trends",
        {"window": ["2"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert alpha_trends.status_code == 200
    alpha_trends_data = json.loads(alpha_trends.body)["data"]
    assert alpha_trends_data["count"] == 2
    assert alpha_trends_data["current_score"] == 14.0
    assert all(point.get("tenant_id", "") == "org_alpha" for point in alpha_trends_data["points"])

    beta_forecast = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/forecast",
        {"window": ["2"], "horizon": ["2"]},
        b"",
        {"X-Tenant-ID": "org_beta"},
    )
    assert beta_forecast.status_code == 200
    beta_forecast_data = json.loads(beta_forecast.body)["data"]
    assert beta_forecast_data["count"] == 2
    assert beta_forecast_data["current_score"] == 91.0
    assert all(point.get("tenant_id", "") == "org_beta" for point in beta_forecast_data["points"])


def test_step6_v1_quality_metrics_record_persists_effective_tenant():
    """V1 quality record should persist actor tenant when body tenant is omitted."""
    from civ_arcos import api

    payload = {
        "score": 63.0,
        "evidence_total": 10,
        "risk_components": 4,
        "source": "tenant_capture",
    }
    body = json.dumps(payload).encode()

    resp = api.app.handle(
        "POST",
        "/api/v1/quality/metrics/record",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert resp.status_code == 201
    data = json.loads(resp.body)
    assert data["data"]["snapshot"]["tenant_id"] == "org_alpha"


def test_step6_v1_quality_metrics_history_tenant_scoped_visibility():
    """V1 quality metrics history should be filtered by effective tenant context."""
    from civ_arcos import api

    alpha_body = json.dumps(
        {
            "score": 20.0,
            "evidence_total": 5,
            "risk_components": 8,
            "source": "tenant_alpha_history",
        }
    ).encode()
    alpha_record = api.app.handle(
        "POST",
        "/api/v1/quality/metrics/record",
        {},
        alpha_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(alpha_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert alpha_record.status_code == 201

    beta_body = json.dumps(
        {
            "score": 90.0,
            "evidence_total": 9,
            "risk_components": 2,
            "source": "tenant_beta_history",
        }
    ).encode()
    beta_record = api.app.handle(
        "POST",
        "/api/v1/quality/metrics/record",
        {},
        beta_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(beta_body)),
            "X-Tenant-ID": "org_beta",
        },
    )
    assert beta_record.status_code == 201

    alpha_history = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/history",
        {"limit": ["5"]},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert alpha_history.status_code == 200
    alpha_data = json.loads(alpha_history.body)
    alpha_snapshots = alpha_data["data"]["snapshots"]
    assert alpha_snapshots
    assert all(s.get("tenant_id", "") == "org_alpha" for s in alpha_snapshots)

    beta_history = api.app.handle(
        "GET",
        "/api/v1/quality/metrics/history",
        {"limit": ["5"]},
        b"",
        {"X-Tenant-ID": "org_beta"},
    )
    assert beta_history.status_code == 200
    beta_data = json.loads(beta_history.body)
    beta_snapshots = beta_data["data"]["snapshots"]
    assert beta_snapshots
    assert all(s.get("tenant_id", "") == "org_beta" for s in beta_snapshots)


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


def test_step6_tenant_endpoint_aliases_and_detail_route():
    """Step 6 tenant list/create aliases and tenant detail should work."""
    from civ_arcos import api

    listed = api.app.handle("GET", "/api/tenants/list", {}, b"", {})
    assert listed.status_code == 200
    listed_data = json.loads(listed.body)
    assert "tenants" in listed_data

    payload = {"name": "Alias Tenant", "plan": "enterprise"}
    body = json.dumps(payload).encode()
    created = api.app.handle(
        "POST",
        "/api/tenants/create",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert created.status_code == 201
    created_data = json.loads(created.body)
    tenant_id = created_data["id"]

    fetched = api.app.handle("GET", f"/api/tenants/{tenant_id}", {}, b"", {})
    assert fetched.status_code == 200
    fetched_data = json.loads(fetched.body)
    assert fetched_data["id"] == tenant_id


def test_step6_tenant_detail_returns_not_found_for_unknown_tenant():
    """Unknown tenant detail lookups should return 404."""
    from civ_arcos import api

    missing = api.app.handle("GET", "/api/tenants/tenant_missing", {}, b"", {})

    assert missing.status_code == 404


def test_step6_compliance_frameworks_and_single_evaluate_endpoint():
    """Step 6 compliance framework list and single evaluation endpoint should work."""
    from civ_arcos import api

    frameworks = api.app.handle("GET", "/api/compliance/frameworks", {}, b"", {})
    assert frameworks.status_code == 200
    frameworks_data = json.loads(frameworks.body)
    assert len(frameworks_data["frameworks"]) == 5

    payload = {
        "framework": "ISO 27001",
        "evidence": {
            "vulnerability_management": True,
            "secure_development": True,
            "change_management": True,
            "event_logging": True,
            "secure_principles": True,
        },
    }
    body = json.dumps(payload).encode()
    evaluated = api.app.handle(
        "POST",
        "/api/compliance/evaluate",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert evaluated.status_code == 200
    evaluated_data = json.loads(evaluated.body)
    assert evaluated_data["result"]["framework"] == "ISO 27001"
    assert evaluated_data["result"]["status"] == "compliant"


def test_step6_compliance_evaluate_all_endpoint():
    """Step 6 evaluate-all endpoint should return aggregate compliance summary."""
    from civ_arcos import api

    payload = {
        "evidence": {
            "vulnerability_management": True,
            "secure_development": True,
            "change_management": True,
            "event_logging": True,
            "secure_principles": True,
            "access_controls": True,
            "data_integrity": True,
            "audit_trails": True,
            "audit_controls": True,
            "transmission_security": True,
            "security_testing": True,
            "vulnerability_scanning": True,
            "account_management": True,
            "change_control": True,
            "security_assessment": True,
            "flaw_remediation": True,
            "input_validation": True,
        }
    }
    body = json.dumps(payload).encode()
    evaluated = api.app.handle(
        "POST",
        "/api/compliance/evaluate-all",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    assert evaluated.status_code == 200
    data = json.loads(evaluated.body)
    assert data["framework_count"] == 5
    assert data["compliant_count"] == 5


def test_step6_compliance_evaluate_rejects_missing_framework():
    """Compliance single-evaluate should require framework identifier."""
    from civ_arcos import api

    body = json.dumps({"evidence": {"event_logging": True}}).encode()
    resp = api.app.handle(
        "POST",
        "/api/compliance/evaluate",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )

    assert resp.status_code == 400


def test_step6_compliance_evaluate_rejects_unknown_framework():
    """Compliance single-evaluate should reject unsupported frameworks."""
    from civ_arcos import api

    body = json.dumps(
        {
            "framework": "UNKNOWN",
            "evidence": {"event_logging": True},
        }
    ).encode()
    resp = api.app.handle(
        "POST",
        "/api/compliance/evaluate",
        {},
        body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
    )

    assert resp.status_code == 400


def test_step6_compliance_endpoints_reject_non_object_evidence():
    """Compliance evaluate endpoints should reject non-object evidence values."""
    from civ_arcos import api

    evaluate_body = json.dumps(
        {
            "framework": "ISO 27001",
            "evidence": ["invalid"],
        }
    ).encode()
    evaluate = api.app.handle(
        "POST",
        "/api/compliance/evaluate",
        {},
        evaluate_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(evaluate_body)),
        },
    )
    assert evaluate.status_code == 400

    evaluate_all_body = json.dumps({"evidence": ["invalid"]}).encode()
    evaluate_all = api.app.handle(
        "POST",
        "/api/compliance/evaluate-all",
        {},
        evaluate_all_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(evaluate_all_body)),
        },
    )
    assert evaluate_all.status_code == 400


def test_step6_analytics_post_trends_benchmark_and_risks_endpoints():
    """Step 6 analytics POST endpoints should return deterministic structures."""
    from civ_arcos import api

    trends_body = json.dumps(
        {
            "snapshots": [
                {
                    "quality_score": 70,
                    "coverage": 68,
                    "vulnerability_count": 12,
                    "technical_debt": 45,
                    "team_productivity": 72,
                },
                {
                    "quality_score": 78,
                    "coverage": 74,
                    "vulnerability_count": 8,
                    "technical_debt": 38,
                    "team_productivity": 76,
                },
            ]
        }
    ).encode()
    trends = api.app.handle(
        "POST",
        "/api/analytics/trends",
        {},
        trends_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(trends_body)),
        },
    )
    assert trends.status_code == 200
    trends_data = json.loads(trends.body)
    assert trends_data["trends"]["quality_score"]["direction"] == "improving"

    benchmark_body = json.dumps(
        {
            "industry": "finance",
            "metrics": {
                "quality_score": 80,
                "coverage": 78,
                "vulnerability_count": 6,
                "technical_debt": 30,
                "team_productivity": 72,
            },
        }
    ).encode()
    benchmark = api.app.handle(
        "POST",
        "/api/analytics/benchmark",
        {},
        benchmark_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(benchmark_body)),
        },
    )
    assert benchmark.status_code == 200
    benchmark_data = json.loads(benchmark.body)
    assert benchmark_data["industry"] == "finance"
    assert "average_percentile" in benchmark_data

    risks_body = json.dumps(
        {
            "metrics": {
                "quality_score": 60,
                "coverage": 55,
                "vulnerability_count": 16,
                "technical_debt": 65,
                "team_productivity": 58,
            }
        }
    ).encode()
    risks = api.app.handle(
        "POST",
        "/api/analytics/risks",
        {},
        risks_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(risks_body)),
        },
    )
    assert risks.status_code == 200
    risks_data = json.loads(risks.body)
    assert "highest_risk" in risks_data
    assert "risks" in risks_data


def test_step6_analytics_endpoints_reject_invalid_payload_shapes():
    """Analytics POST endpoints should reject non-object/list payload inputs."""
    from civ_arcos import api

    trends_body = json.dumps({"snapshots": {"invalid": True}}).encode()
    trends = api.app.handle(
        "POST",
        "/api/analytics/trends",
        {},
        trends_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(trends_body)),
        },
    )
    assert trends.status_code == 400

    benchmark_body = json.dumps({"metrics": ["invalid"]}).encode()
    benchmark = api.app.handle(
        "POST",
        "/api/analytics/benchmark",
        {},
        benchmark_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(benchmark_body)),
        },
    )
    assert benchmark.status_code == 400

    risks_body = json.dumps({"metrics": ["invalid"]}).encode()
    risks = api.app.handle(
        "POST",
        "/api/analytics/risks",
        {},
        risks_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(risks_body)),
        },
    )
    assert risks.status_code == 400


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


def test_step6_tenant_create_rejects_invalid_name_type():
    """Tenant creation endpoints should reject non-string name values."""
    from civ_arcos import api

    bad_payload = json.dumps({"name": 123, "plan": "pro"}).encode()

    legacy = api.app.handle(
        "POST",
        "/api/tenants/create",
        {},
        bad_payload,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(bad_payload)),
        },
    )
    assert legacy.status_code == 400

    v1 = api.app.handle(
        "POST",
        "/api/v1/tenants",
        {},
        bad_payload,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(bad_payload)),
        },
    )
    assert v1.status_code == 400


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


def test_step6_settings_update_rejects_invalid_port_values():
    """Settings update endpoints should reject non-integer/out-of-range ports."""
    from civ_arcos import api

    invalid_type_body = json.dumps({"port": "not-a-number"}).encode()
    legacy_type = api.app.handle(
        "POST",
        "/api/settings",
        {},
        invalid_type_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(invalid_type_body)),
        },
    )
    assert legacy_type.status_code == 400

    invalid_range_body = json.dumps({"port": 70000}).encode()
    v1_range = api.app.handle(
        "POST",
        "/api/v1/settings",
        {},
        invalid_range_body,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(invalid_range_body)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert v1_range.status_code == 400


def test_step6_v1_settings_rejects_invalid_tenant_id_type():
    """V1 settings updates should reject non-string tenant_id values."""
    from civ_arcos import api

    bad_payload = json.dumps({"tenant_id": 123, "log_level": "INFO"}).encode()
    resp = api.app.handle(
        "POST",
        "/api/v1/settings",
        {},
        bad_payload,
        {
            "Content-Type": "application/json",
            "Content-Length": str(len(bad_payload)),
            "X-Tenant-ID": "org_alpha",
        },
    )
    assert resp.status_code == 400


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


def test_step6_v1_tenant_detail_contract_shape():
    """V1 tenant detail endpoint should return tenant detail contract envelope."""
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/v1/tenants/org_alpha", {}, b"", {})
    assert resp.status_code == 200

    data = json.loads(resp.body)
    assert data["contract"]["name"] == "TenantDetail"
    assert data["data"]["tenant"]["id"] == "org_alpha"


def test_step6_v1_tenant_detail_unknown_tenant_returns_404():
    """Unknown tenant detail lookup should return 404 on v1 route."""
    from civ_arcos import api

    resp = api.app.handle("GET", "/api/v1/tenants/tenant_missing", {}, b"", {})
    assert resp.status_code == 404


def test_step6_v1_tenant_detail_cross_tenant_denied():
    """Tenant identity header should block cross-tenant detail reads on v1 route."""
    from civ_arcos import api

    denied = api.app.handle(
        "GET",
        "/api/v1/tenants/org_beta",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert denied.status_code == 403

    allowed = api.app.handle(
        "GET",
        "/api/v1/tenants/org_alpha",
        {},
        b"",
        {"X-Tenant-ID": "org_alpha"},
    )
    assert allowed.status_code == 200


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
