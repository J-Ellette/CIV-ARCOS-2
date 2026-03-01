"""Unit tests for enterprise compliance framework evaluation."""

import pytest

from civ_arcos.core.compliance import ComplianceEngine


def _strong_evidence() -> dict:
    """Return evidence set that satisfies all mapped controls."""
    return {
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


def test_list_frameworks_includes_all_five_frameworks() -> None:
    """Framework listing should include all Step 6 compliance frameworks."""
    engine = ComplianceEngine()

    listed = engine.list_frameworks()

    names = [item["framework"] for item in listed]
    assert names == ["HIPAA", "ISO 27001", "NIST 800-53", "PCI-DSS", "SOX"]
    assert len(listed) == 5


def test_evaluate_framework_returns_compliant_for_full_evidence() -> None:
    """A fully evidenced framework should evaluate as compliant."""
    engine = ComplianceEngine()

    result = engine.evaluate_framework("ISO 27001", _strong_evidence())

    assert result["framework"] == "ISO 27001"
    assert result["status"] == "compliant"
    assert result["score"] == 1.0


def test_evaluate_framework_returns_partial_for_mixed_evidence() -> None:
    """A mixed evidence set should produce a partial framework status."""
    engine = ComplianceEngine()

    result = engine.evaluate_framework(
        "SOX",
        {
            "access_controls": True,
            "change_management": True,
            "data_integrity": False,
            "audit_trails": False,
        },
    )

    assert result["status"] == "partial"
    assert result["score"] == 0.5
    assert result["passed_controls"] == 2


def test_evaluate_framework_returns_non_compliant_for_empty_evidence() -> None:
    """An empty evidence set should fail framework controls."""
    engine = ComplianceEngine()

    result = engine.evaluate_framework("HIPAA", {})

    assert result["status"] == "non_compliant"
    assert result["score"] == 0.0


def test_evaluate_framework_raises_for_unknown_framework() -> None:
    """Unsupported framework names should fail fast."""
    engine = ComplianceEngine()

    with pytest.raises(ValueError):
        engine.evaluate_framework("UNKNOWN", {})


def test_evaluate_all_returns_summary_counts() -> None:
    """Aggregate evaluation should include summary counts and average score."""
    engine = ComplianceEngine()

    summary = engine.evaluate_all(_strong_evidence())

    assert summary["framework_count"] == 5
    assert summary["compliant_count"] == 5
    assert summary["partial_count"] == 0
    assert summary["non_compliant_count"] == 0
    assert summary["average_score"] == 1.0


def test_evaluate_all_with_sparse_evidence_has_non_compliant_frameworks() -> None:
    """Sparse evidence should produce at least one non-compliant framework."""
    engine = ComplianceEngine()

    summary = engine.evaluate_all({"event_logging": True})

    assert summary["non_compliant_count"] >= 1
    assert summary["average_score"] < 0.5


def test_framework_recommendations_include_failed_controls() -> None:
    """Failed controls should produce actionable recommendation lines."""
    engine = ComplianceEngine()

    result = engine.evaluate_framework(
        "PCI-DSS",
        {
            "secure_development": True,
            "security_testing": False,
            "access_controls": False,
            "vulnerability_scanning": True,
        },
    )

    recommendations = " ".join(result["recommendations"])
    assert "Req-6.3 security testing" in recommendations
    assert "Req-7.1 access control" in recommendations


def test_framework_recommendations_fallback_for_compliant_case() -> None:
    """Compliant frameworks should return a maintenance recommendation."""
    engine = ComplianceEngine()

    result = engine.evaluate_framework("NIST 800-53", _strong_evidence())

    assert result["recommendations"] == ["Maintain current control evidence quality."]


def test_control_level_result_shape_contains_expected_keys() -> None:
    """Control-level output should include control metadata and pass state."""
    engine = ComplianceEngine()

    result = engine.evaluate_framework("SOX", _strong_evidence())

    first = result["controls"][0]
    assert set(first.keys()) == {"control", "evidence_key", "passed"}


def test_framework_scores_truthy_non_boolean_evidence_values() -> None:
    """Truthy non-boolean evidence values should count as passed controls."""
    engine = ComplianceEngine()

    result = engine.evaluate_framework(
        "SOX",
        {
            "access_controls": 1,
            "change_management": "yes",
            "data_integrity": ["present"],
            "audit_trails": {"enabled": True},
        },
    )

    assert result["status"] == "compliant"
    assert result["score"] == 1.0
    assert result["passed_controls"] == 4


def test_framework_status_thresholds_map_to_expected_categories() -> None:
    """Boundary scores should map to compliant, partial, and non-compliant."""
    engine = ComplianceEngine()

    compliant = engine.evaluate_framework(
        "ISO 27001",
        {
            "vulnerability_management": True,
            "secure_development": True,
            "change_management": True,
            "event_logging": True,
            "secure_principles": False,
        },
    )
    partial = engine.evaluate_framework(
        "ISO 27001",
        {
            "vulnerability_management": True,
            "secure_development": True,
            "change_management": False,
            "event_logging": False,
            "secure_principles": False,
        },
    )
    non_compliant = engine.evaluate_framework(
        "ISO 27001",
        {
            "vulnerability_management": True,
            "secure_development": False,
            "change_management": False,
            "event_logging": False,
            "secure_principles": False,
        },
    )

    assert compliant["score"] == 0.8
    assert compliant["status"] == "compliant"
    assert partial["score"] == 0.4
    assert partial["status"] == "non_compliant"
    assert non_compliant["score"] == 0.2
    assert non_compliant["status"] == "non_compliant"


def test_evaluate_all_returns_partial_count_for_mid_score_frameworks() -> None:
    """Aggregate summary should count partial frameworks when score is mid-band."""
    engine = ComplianceEngine()

    summary = engine.evaluate_all(
        {
            "change_management": True,
            "access_controls": True,
            "data_integrity": True,
            "audit_trails": False,
            "audit_controls": False,
            "transmission_security": False,
            "secure_development": False,
            "security_testing": False,
            "vulnerability_scanning": False,
            "account_management": False,
            "change_control": False,
            "security_assessment": False,
            "flaw_remediation": False,
            "input_validation": False,
        }
    )

    assert summary["framework_count"] == 5
    assert summary["partial_count"] >= 1


def test_framework_recommendations_count_matches_failed_controls() -> None:
    """Recommendation count should match number of failed controls."""
    engine = ComplianceEngine()

    result = engine.evaluate_framework(
        "HIPAA",
        {
            "access_controls": True,
            "audit_controls": False,
            "data_integrity": False,
            "transmission_security": True,
        },
    )

    assert len(result["recommendations"]) == 2
