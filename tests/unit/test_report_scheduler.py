"""Unit tests for tenant-aware report scheduler behavior."""

import json

from civ_arcos.core.report_scheduler import ReportScheduler


def test_list_jobs_can_be_tenant_scoped(tmp_path):
    """Listing jobs with tenant filter should only return matching jobs."""
    storage_path = tmp_path / "jobs.json"
    scheduler = ReportScheduler(storage_path=storage_path)

    alpha = scheduler.schedule_report(
        report_type="compliance",
        frequency="daily",
        target="console",
        tenant_id="org_alpha",
    )
    beta = scheduler.schedule_report(
        report_type="risk",
        frequency="weekly",
        target="console",
        tenant_id="org_beta",
    )

    all_jobs = scheduler.list_jobs()
    assert any(job["job_id"] == alpha.job_id for job in all_jobs)
    assert any(job["job_id"] == beta.job_id for job in all_jobs)

    alpha_jobs = scheduler.list_jobs(tenant_id="org_alpha")
    assert len(alpha_jobs) == 1
    assert alpha_jobs[0]["job_id"] == alpha.job_id
    assert alpha_jobs[0]["tenant_id"] == "org_alpha"

    beta_jobs = scheduler.list_jobs(tenant_id="org_beta")
    assert len(beta_jobs) == 1
    assert beta_jobs[0]["job_id"] == beta.job_id
    assert beta_jobs[0]["tenant_id"] == "org_beta"


def test_get_job_can_be_tenant_scoped(tmp_path):
    """Detail lookup with tenant filter should reject cross-tenant access."""
    storage_path = tmp_path / "jobs.json"
    scheduler = ReportScheduler(storage_path=storage_path)

    created = scheduler.schedule_report(
        report_type="executive_summary",
        frequency="daily",
        target="console",
        tenant_id="org_alpha",
    )

    unscoped = scheduler.get_job(created.job_id)
    assert unscoped is not None
    assert unscoped["tenant_id"] == "org_alpha"

    scoped = scheduler.get_job(created.job_id, tenant_id="org_alpha")
    assert scoped is not None
    assert scoped["job_id"] == created.job_id

    denied = scheduler.get_job(created.job_id, tenant_id="org_beta")
    assert denied is None


def test_load_supports_legacy_rows_without_tenant_id(tmp_path):
    """Legacy persisted rows without tenant_id should still load correctly."""
    storage_path = tmp_path / "jobs.json"
    storage_path.write_text(
        json.dumps(
            [
                {
                    "job_id": "rpt_legacy123",
                    "report_type": "compliance_snapshot",
                    "frequency": "daily",
                    "target": "console",
                    "created_at": "2026-03-01T00:00:00+00:00",
                    "next_run_at": "2026-03-02T00:00:00+00:00",
                    "status": "scheduled",
                }
            ]
        ),
        encoding="utf-8",
    )

    scheduler = ReportScheduler(storage_path=storage_path)
    loaded = scheduler.get_job("rpt_legacy123")

    assert loaded is not None
    assert loaded["tenant_id"] == ""
    assert scheduler.list_jobs(tenant_id="org_alpha") == []


def test_load_tolerates_corrupted_json(tmp_path):
    """Corrupted persisted JSON should not crash scheduler initialization."""
    storage_path = tmp_path / "jobs.json"
    storage_path.write_text("{not-valid-json", encoding="utf-8")

    scheduler = ReportScheduler(storage_path=storage_path)

    assert scheduler.list_jobs() == []
