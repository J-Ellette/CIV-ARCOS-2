"""Enterprise analytics engine for trends, benchmarks, and risk prediction."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping


class AnalyticsEngine:
    """Compute deterministic analytics signals from project quality metrics."""

    _TRACKED_METRICS = [
        "quality_score",
        "coverage",
        "vulnerability_count",
        "technical_debt",
        "team_productivity",
    ]

    _INDUSTRY_BASELINES = {
        "general": {
            "quality_score": 75.0,
            "coverage": 70.0,
            "vulnerability_count": 8.0,
            "technical_debt": 35.0,
            "team_productivity": 72.0,
        },
        "finance": {
            "quality_score": 82.0,
            "coverage": 80.0,
            "vulnerability_count": 5.0,
            "technical_debt": 25.0,
            "team_productivity": 68.0,
        },
        "healthcare": {
            "quality_score": 80.0,
            "coverage": 78.0,
            "vulnerability_count": 6.0,
            "technical_debt": 28.0,
            "team_productivity": 66.0,
        },
        "saas": {
            "quality_score": 74.0,
            "coverage": 72.0,
            "vulnerability_count": 10.0,
            "technical_debt": 40.0,
            "team_productivity": 77.0,
        },
    }

    def trend_analysis(self, snapshots: List[Mapping[str, Any]]) -> Dict[str, Any]:
        """Analyze metric direction and delta trends across snapshot history."""
        normalized = self._normalize_snapshots(snapshots)
        trends: Dict[str, Dict[str, Any]] = {}

        for metric in self._TRACKED_METRICS:
            values = [snapshot[metric] for snapshot in normalized]
            if len(values) < 2:
                trends[metric] = {
                    "direction": "stable",
                    "delta": 0.0,
                    "current": values[-1] if values else 0.0,
                }
                continue

            delta = round(values[-1] - values[0], 2)
            trends[metric] = {
                "direction": self._direction(metric, delta),
                "delta": delta,
                "current": values[-1],
            }

        return {
            "count": len(normalized),
            "trends": trends,
        }

    def benchmark_analysis(
        self,
        metrics: Mapping[str, Any],
        industry: str = "general",
    ) -> Dict[str, Any]:
        """Compare project metrics with industry baseline percentiles."""
        baseline = self._INDUSTRY_BASELINES.get(
            industry, self._INDUSTRY_BASELINES["general"]
        )
        metric_values = self._normalize_metric_record(metrics)

        comparisons: List[Dict[str, Any]] = []
        for metric in self._TRACKED_METRICS:
            current = metric_values[metric]
            benchmark = baseline[metric]
            percentile = self._percentile(metric, current, benchmark)
            comparisons.append(
                {
                    "metric": metric,
                    "current": current,
                    "benchmark": benchmark,
                    "percentile": percentile,
                }
            )

        average_percentile = round(
            sum(float(item["percentile"]) for item in comparisons) / len(comparisons),
            2,
        )

        return {
            "industry": industry if industry in self._INDUSTRY_BASELINES else "general",
            "average_percentile": average_percentile,
            "comparisons": comparisons,
            "recommendations": self._benchmark_recommendations(comparisons),
        }

    def risk_prediction(self, metrics: Mapping[str, Any]) -> Dict[str, Any]:
        """Predict risk probabilities for key enterprise project outcomes."""
        values = self._normalize_metric_record(metrics)

        security_incident = self._bounded_probability(
            0.15
            + (values["vulnerability_count"] / 30.0)
            + max(0.0, (70.0 - values["coverage"]) / 200.0)
        )
        maintenance_burden = self._bounded_probability(
            0.10
            + (values["technical_debt"] / 120.0)
            + max(0.0, (75.0 - values["quality_score"]) / 180.0)
        )
        quality_degradation = self._bounded_probability(
            0.10
            + max(0.0, (75.0 - values["quality_score"]) / 160.0)
            + max(0.0, (70.0 - values["team_productivity"]) / 220.0)
        )
        technical_debt_risk = self._bounded_probability(
            0.12
            + (values["technical_debt"] / 100.0)
            + max(0.0, (65.0 - values["coverage"]) / 220.0)
        )

        risks = {
            "security_incident": security_incident,
            "maintenance_burden": maintenance_burden,
            "quality_degradation": quality_degradation,
            "technical_debt": technical_debt_risk,
        }

        return {
            "risks": risks,
            "highest_risk": max(risks, key=lambda risk_name: risks[risk_name]),
            "recommendations": self._risk_recommendations(risks),
        }

    @classmethod
    def _normalize_snapshots(
        cls,
        snapshots: List[Mapping[str, Any]],
    ) -> List[Dict[str, float]]:
        """Normalize snapshot records for tracked metric computations."""
        normalized = []
        for snapshot in snapshots:
            normalized.append(cls._normalize_metric_record(snapshot))
        return normalized

    @classmethod
    def _normalize_metric_record(cls, data: Mapping[str, Any]) -> Dict[str, float]:
        """Normalize one metric record with safe default numeric values."""
        normalized: Dict[str, float] = {}
        for metric in cls._TRACKED_METRICS:
            value = data.get(metric, 0.0)
            try:
                normalized[metric] = float(value)
            except (TypeError, ValueError):
                normalized[metric] = 0.0
        return normalized

    @staticmethod
    def _direction(metric: str, delta: float) -> str:
        """Return direction label while accounting for inverse-risk metrics."""
        if metric in {"vulnerability_count", "technical_debt"}:
            if delta > 0:
                return "degrading"
            if delta < 0:
                return "improving"
            return "stable"

        if delta > 0:
            return "improving"
        if delta < 0:
            return "degrading"
        return "stable"

    @staticmethod
    def _percentile(metric: str, current: float, benchmark: float) -> float:
        """Compute normalized percentile score for one benchmark comparison."""
        if benchmark == 0:
            return 100.0 if current > 0 else 50.0

        if metric in {"vulnerability_count", "technical_debt"}:
            ratio = (benchmark / max(current, 1.0)) * 50.0
            return round(max(0.0, min(100.0, ratio)), 2)

        ratio = (current / benchmark) * 50.0
        return round(max(0.0, min(100.0, ratio)), 2)

    @staticmethod
    def _bounded_probability(value: float) -> float:
        """Clamp and round probability values into 0.0..1.0 range."""
        return round(max(0.0, min(1.0, value)), 3)

    @staticmethod
    def _benchmark_recommendations(comparisons: List[Dict[str, Any]]) -> List[str]:
        """Build benchmark recommendations for low-percentile metrics."""
        low_items = [item for item in comparisons if float(item["percentile"]) < 50.0]
        if not low_items:
            return ["Maintain benchmark parity and monitor metric drift."]

        recommendations = []
        for item in low_items:
            recommendations.append(f"Improve {item['metric']} to close benchmark gap.")
        return recommendations

    @staticmethod
    def _risk_recommendations(risks: Mapping[str, float]) -> List[str]:
        """Build risk recommendations for elevated probability categories."""
        recommendations = []
        for risk_name, probability in risks.items():
            if probability < 0.5:
                continue
            if risk_name == "security_incident":
                recommendations.append(
                    "Prioritize vulnerability remediation and secure testing."
                )
            elif risk_name == "maintenance_burden":
                recommendations.append(
                    "Reduce complexity and improve maintainability hotspots."
                )
            elif risk_name == "quality_degradation":
                recommendations.append(
                    "Raise code quality and team throughput stability controls."
                )
            elif risk_name == "technical_debt":
                recommendations.append(
                    "Allocate sprint capacity to technical debt repayment."
                )

        if not recommendations:
            recommendations.append(
                "Current projected risks are within acceptable bounds."
            )
        return recommendations
