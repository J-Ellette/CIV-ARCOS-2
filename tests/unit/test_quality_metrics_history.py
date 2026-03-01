"""Unit tests for tenant-aware quality metrics history behavior."""

import json

from civ_arcos.core.quality_metrics_history import QualityMetricsHistory


def test_list_snapshots_can_be_tenant_scoped(tmp_path):
    """Snapshot listing with tenant filter should only return matching rows."""
    storage_path = tmp_path / "quality_history.json"
    history = QualityMetricsHistory(storage_path=storage_path)

    history.record_snapshot(
        score=20,
        evidence_total=5,
        risk_components=7,
        source="test",
        tenant_id="org_alpha",
    )
    history.record_snapshot(
        score=90,
        evidence_total=9,
        risk_components=2,
        source="test",
        tenant_id="org_beta",
    )

    all_snapshots = history.list_snapshots(limit=10)
    assert len(all_snapshots) == 2

    alpha_snapshots = history.list_snapshots(limit=10, tenant_id="org_alpha")
    assert len(alpha_snapshots) == 1
    assert alpha_snapshots[0]["tenant_id"] == "org_alpha"

    beta_snapshots = history.list_snapshots(limit=10, tenant_id="org_beta")
    assert len(beta_snapshots) == 1
    assert beta_snapshots[0]["tenant_id"] == "org_beta"


def test_trend_and_forecast_are_tenant_scoped(tmp_path):
    """Trend and forecast summaries should use only the selected tenant scope."""
    storage_path = tmp_path / "quality_history.json"
    history = QualityMetricsHistory(storage_path=storage_path)

    history.record_snapshot(
        score=10,
        evidence_total=5,
        risk_components=8,
        source="test",
        tenant_id="org_alpha",
    )
    history.record_snapshot(
        score=12,
        evidence_total=6,
        risk_components=7,
        source="test",
        tenant_id="org_alpha",
    )
    history.record_snapshot(
        score=85,
        evidence_total=7,
        risk_components=2,
        source="test",
        tenant_id="org_beta",
    )
    history.record_snapshot(
        score=90,
        evidence_total=8,
        risk_components=2,
        source="test",
        tenant_id="org_beta",
    )

    alpha_trend = history.trend_summary(window=2, tenant_id="org_alpha")
    assert alpha_trend["count"] == 2
    assert alpha_trend["current_score"] == 12.0

    beta_forecast = history.forecast_summary(
        window=2,
        horizon=2,
        tenant_id="org_beta",
    )
    assert beta_forecast["count"] == 2
    assert beta_forecast["current_score"] == 90.0
    assert beta_forecast["forecast"][0]["projected_score"] == 95.0


def test_load_supports_legacy_rows_without_tenant_id(tmp_path):
    """Legacy persisted snapshots without tenant_id should still load."""
    storage_path = tmp_path / "quality_history.json"
    storage_path.write_text(
        json.dumps(
            [
                {
                    "snapshot_id": "qms_legacy123",
                    "timestamp": "2026-03-01T00:00:00+00:00",
                    "score": 50.0,
                    "evidence_total": 4,
                    "risk_components": 3,
                    "source": "legacy",
                }
            ]
        ),
        encoding="utf-8",
    )

    history = QualityMetricsHistory(storage_path=storage_path)
    loaded = history.list_snapshots(limit=5)

    assert len(loaded) == 1
    assert loaded[0]["snapshot_id"] == "qms_legacy123"
    assert loaded[0]["tenant_id"] == ""
    assert history.list_snapshots(limit=5, tenant_id="org_alpha") == []


def test_load_tolerates_corrupted_json(tmp_path):
    """Corrupted persisted JSON should not crash history initialization."""
    storage_path = tmp_path / "quality_history.json"
    storage_path.write_text("{not-valid-json", encoding="utf-8")

    history = QualityMetricsHistory(storage_path=storage_path)

    assert history.list_snapshots(limit=5) == []
