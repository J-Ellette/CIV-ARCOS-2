"""Unit tests for tenant-scoped compliance report persistence."""

import json

from civ_arcos.core.compliance_reports import ComplianceReportStore


def _framework(status: str, name: str = "ISO 27001") -> dict:
    """Build a minimal framework status payload for report artifacts."""
    return {
        "framework": name,
        "status": status,
        "percentage": 88.0 if status == "compliant" else 72.0,
    }


def test_create_report_summary_counts_are_deterministic(tmp_path):
    """Creating a report should compute framework summary counters correctly."""
    storage_path = tmp_path / "compliance_reports.json"
    store = ComplianceReportStore(storage_path=storage_path)

    report = store.create_report(
        tenant_id="org_alpha",
        frameworks=[
            _framework("compliant", "ISO 27001"),
            _framework("partial", "NIST 800-53"),
            _framework("compliant", "FedRAMP"),
        ],
    )

    assert report["tenant_id"] == "org_alpha"
    assert report["summary"]["framework_count"] == 3
    assert report["summary"]["compliant_count"] == 2
    assert report["summary"]["partial_count"] == 1


def test_list_reports_is_tenant_scoped(tmp_path):
    """Listing artifacts should only return reports for the requested tenant."""
    storage_path = tmp_path / "compliance_reports.json"
    store = ComplianceReportStore(storage_path=storage_path)

    alpha = store.create_report(
        tenant_id="org_alpha",
        frameworks=[_framework("compliant")],
    )
    beta = store.create_report(
        tenant_id="org_beta",
        frameworks=[_framework("partial")],
    )

    alpha_reports = store.list_reports("org_alpha")
    assert len(alpha_reports) == 1
    assert alpha_reports[0]["report_id"] == alpha["report_id"]

    beta_reports = store.list_reports("org_beta")
    assert len(beta_reports) == 1
    assert beta_reports[0]["report_id"] == beta["report_id"]


def test_load_skips_invalid_rows_and_keeps_valid_artifacts(tmp_path):
    """Loader should ignore malformed rows while preserving valid artifacts."""
    storage_path = tmp_path / "compliance_reports.json"
    storage_path.write_text(
        json.dumps(
            [
                {
                    "report_id": "cmp_valid001",
                    "tenant_id": "org_alpha",
                    "generated_at": "2026-03-01T00:00:00+00:00",
                    "frameworks": [
                        {
                            "framework": "ISO 27001",
                            "status": "compliant",
                            "percentage": 90.0,
                        }
                    ],
                    "summary": {
                        "framework_count": 1,
                        "compliant_count": 1,
                        "partial_count": 0,
                    },
                },
                {
                    "report_id": "cmp_invalid001",
                    "tenant_id": "org_beta",
                    "generated_at": "2026-03-01T00:00:00+00:00",
                    "frameworks": "not-a-list",
                    "summary": {},
                },
            ]
        ),
        encoding="utf-8",
    )

    store = ComplianceReportStore(storage_path=storage_path)
    loaded = store.get_report("cmp_valid001")

    assert loaded is not None
    assert loaded["tenant_id"] == "org_alpha"
    assert store.get_report("cmp_invalid001") is None


def test_load_tolerates_corrupted_json(tmp_path):
    """Corrupted persisted JSON should not crash report store initialization."""
    storage_path = tmp_path / "compliance_reports.json"
    storage_path.write_text("{not-valid-json", encoding="utf-8")

    store = ComplianceReportStore(storage_path=storage_path)

    assert store.list_reports("org_alpha") == []
