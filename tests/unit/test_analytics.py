"""Unit tests for enterprise analytics engine behaviors."""

from civ_arcos.core.analytics import AnalyticsEngine


def test_trend_analysis_detects_improving_and_degrading_directions() -> None:
    """Trend analysis should classify metric directions deterministically."""
    engine = AnalyticsEngine()
    snapshots = [
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
            "technical_debt": 40,
            "team_productivity": 75,
        },
    ]

    result = engine.trend_analysis(snapshots)

    assert result["count"] == 2
    assert result["trends"]["quality_score"]["direction"] == "improving"
    assert result["trends"]["coverage"]["direction"] == "improving"
    assert result["trends"]["vulnerability_count"]["direction"] == "improving"


def test_trend_analysis_returns_stable_for_single_snapshot() -> None:
    """Single-point trend analysis should return stable baseline directions."""
    engine = AnalyticsEngine()

    result = engine.trend_analysis(
        [
            {
                "quality_score": 80,
                "coverage": 82,
                "vulnerability_count": 5,
                "technical_debt": 20,
                "team_productivity": 78,
            }
        ]
    )

    assert result["count"] == 1
    assert result["trends"]["quality_score"]["direction"] == "stable"
    assert result["trends"]["technical_debt"]["direction"] == "stable"


def test_benchmark_analysis_returns_general_when_industry_unknown() -> None:
    """Unknown benchmark industry should fallback to general baselines."""
    engine = AnalyticsEngine()

    result = engine.benchmark_analysis(
        {
            "quality_score": 80,
            "coverage": 76,
            "vulnerability_count": 6,
            "technical_debt": 30,
            "team_productivity": 74,
        },
        industry="unknown",
    )

    assert result["industry"] == "general"
    assert "average_percentile" in result
    assert len(result["comparisons"]) == 5


def test_benchmark_analysis_includes_recommendations_for_low_percentiles() -> None:
    """Low benchmark percentiles should produce actionable recommendations."""
    engine = AnalyticsEngine()

    result = engine.benchmark_analysis(
        {
            "quality_score": 50,
            "coverage": 45,
            "vulnerability_count": 20,
            "technical_debt": 75,
            "team_productivity": 40,
        },
        industry="finance",
    )

    joined = " ".join(result["recommendations"]).lower()
    assert "improve" in joined


def test_risk_prediction_outputs_probability_range_and_highest_risk() -> None:
    """Risk prediction should return bounded probabilities and top risk label."""
    engine = AnalyticsEngine()

    result = engine.risk_prediction(
        {
            "quality_score": 60,
            "coverage": 55,
            "vulnerability_count": 18,
            "technical_debt": 70,
            "team_productivity": 58,
        }
    )

    assert set(result["risks"].keys()) == {
        "security_incident",
        "maintenance_burden",
        "quality_degradation",
        "technical_debt",
    }
    assert all(0.0 <= value <= 1.0 for value in result["risks"].values())
    assert result["highest_risk"] in result["risks"]


def test_risk_prediction_returns_low_risk_recommendation_when_bounded() -> None:
    """Low-risk metrics should produce bounded-risk maintenance guidance."""
    engine = AnalyticsEngine()

    result = engine.risk_prediction(
        {
            "quality_score": 92,
            "coverage": 95,
            "vulnerability_count": 1,
            "technical_debt": 8,
            "team_productivity": 88,
        }
    )

    assert result["recommendations"] == [
        "Current projected risks are within acceptable bounds."
    ]


def test_listed_metric_comparisons_cover_all_tracked_metrics() -> None:
    """Benchmark comparisons should include all tracked metric categories."""
    engine = AnalyticsEngine()

    result = engine.benchmark_analysis(
        {
            "quality_score": 78,
            "coverage": 76,
            "vulnerability_count": 8,
            "technical_debt": 30,
            "team_productivity": 74,
        },
        industry="saas",
    )

    compared = {item["metric"] for item in result["comparisons"]}
    assert compared == {
        "quality_score",
        "coverage",
        "vulnerability_count",
        "technical_debt",
        "team_productivity",
    }


def test_trend_analysis_handles_missing_metric_values_with_defaults() -> None:
    """Missing metrics should be normalized to defaults without crashing."""
    engine = AnalyticsEngine()

    result = engine.trend_analysis([{}, {}])

    assert result["count"] == 2
    assert result["trends"]["quality_score"]["current"] == 0.0


def test_trend_analysis_marks_inverse_metrics_degrading_on_increase() -> None:
    """Increasing inverse-risk metrics should be labeled as degrading."""
    engine = AnalyticsEngine()

    result = engine.trend_analysis(
        [
            {
                "vulnerability_count": 5,
                "technical_debt": 15,
            },
            {
                "vulnerability_count": 9,
                "technical_debt": 21,
            },
        ]
    )

    assert result["trends"]["vulnerability_count"]["direction"] == "degrading"
    assert result["trends"]["technical_debt"]["direction"] == "degrading"


def test_trend_analysis_normalizes_non_numeric_values_to_zero() -> None:
    """Invalid metric values should normalize safely to zero."""
    engine = AnalyticsEngine()

    result = engine.trend_analysis(
        [
            {
                "quality_score": "invalid",
                "coverage": None,
                "vulnerability_count": "n/a",
                "technical_debt": object(),
                "team_productivity": "bad",
            }
        ]
    )

    for metric in (
        "quality_score",
        "coverage",
        "vulnerability_count",
        "technical_debt",
        "team_productivity",
    ):
        assert result["trends"][metric]["current"] == 0.0


def test_benchmark_analysis_uses_maintenance_guidance_when_all_percentiles_high() -> (
    None
):
    """High-percentile benchmark runs should emit maintenance guidance."""
    engine = AnalyticsEngine()

    result = engine.benchmark_analysis(
        {
            "quality_score": 99,
            "coverage": 99,
            "vulnerability_count": 1,
            "technical_debt": 5,
            "team_productivity": 95,
        },
        industry="general",
    )

    assert result["average_percentile"] >= 50.0
    assert result["recommendations"] == [
        "Maintain benchmark parity and monitor metric drift."
    ]


def test_risk_prediction_returns_targeted_recommendations_for_high_risk_categories() -> (
    None
):
    """Elevated risks should produce category-specific recommendation strings."""
    engine = AnalyticsEngine()

    result = engine.risk_prediction(
        {
            "quality_score": 40,
            "coverage": 20,
            "vulnerability_count": 30,
            "technical_debt": 100,
            "team_productivity": 45,
        }
    )

    recommendations = " ".join(result["recommendations"]).lower()
    assert "vulnerability remediation" in recommendations
    assert "maintainability" in recommendations
    assert "technical debt" in recommendations
