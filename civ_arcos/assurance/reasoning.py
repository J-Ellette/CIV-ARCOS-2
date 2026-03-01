"""Reasoning engine for assurance cases (CLARISSA-style baseline)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List

from civ_arcos.assurance.case import AssuranceCase
from civ_arcos.assurance.gsn import GSNNodeType


class DefeaterType(str, Enum):
    """Kinds of defeaters that can reduce argument confidence."""

    REBUTTAL = "rebuttal"
    UNDERCUT = "undercut"
    COUNTEREXAMPLE = "counterexample"


@dataclass
class ArgumentTheory:
    """Reusable reasoning theory with a premise evaluator."""

    theory_id: str
    premise: str
    conclusion: str
    weight: float
    evaluator: Callable[[AssuranceCase, Dict[str, Any]], bool]


@dataclass
class Defeater:
    """A defeater rule that can challenge assurance conclusions."""

    defeater_id: str
    defeater_type: DefeaterType
    description: str
    severity: float
    evaluator: Callable[[AssuranceCase, Dict[str, Any]], bool]


class ReasoningEngine:
    """Reason about assurance cases using theories and defeaters."""

    def __init__(self) -> None:
        """Initialize built-in theories and defeaters."""
        self._theories: Dict[str, ArgumentTheory] = {}
        self._defeaters: Dict[str, Defeater] = {}
        self._register_defaults()

    def register_theory(self, theory: ArgumentTheory) -> None:
        """Register or replace a custom theory."""
        self._theories[theory.theory_id] = theory

    def reason_about_case(
        self,
        case: AssuranceCase,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Evaluate case confidence, defeasibility, and recommendations."""
        ctx = context or {}

        applicable_theories: List[Dict[str, Any]] = []
        for theory in self._theories.values():
            if theory.evaluator(case, ctx):
                applicable_theories.append(
                    {
                        "theory_id": theory.theory_id,
                        "premise": theory.premise,
                        "conclusion": theory.conclusion,
                        "weight": theory.weight,
                    }
                )

        active_defeaters: List[Dict[str, Any]] = []
        for defeater in self._defeaters.values():
            if defeater.evaluator(case, ctx):
                active_defeaters.append(
                    {
                        "defeater_id": defeater.defeater_id,
                        "type": defeater.defeater_type.value,
                        "description": defeater.description,
                        "severity": defeater.severity,
                    }
                )

        theory_weight = sum(item["weight"] for item in applicable_theories)
        defeater_weight = sum(item["severity"] for item in active_defeaters)
        confidence = max(0.0, min(1.0, 0.40 + theory_weight - defeater_weight))

        recommendations = self._build_recommendations(
            case,
            applicable_theories,
            active_defeaters,
        )

        return {
            "applicable_theories": applicable_theories,
            "active_defeaters": active_defeaters,
            "confidence_score": round(confidence, 3),
            "indefeasible": len(active_defeaters) == 0 and confidence >= 0.70,
            "recommendations": recommendations,
        }

    def estimate_risk(
        self,
        case: AssuranceCase,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Estimate risk score/level from reasoning output."""
        reasoning = self.reason_about_case(case, context=context)
        confidence = float(reasoning["confidence_score"])
        risk_score = round(max(0.0, min(1.0, 1.0 - confidence)), 3)

        if risk_score >= 0.75:
            risk_level = "critical"
        elif risk_score >= 0.50:
            risk_level = "high"
        elif risk_score >= 0.25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence_score": confidence,
            "defeater_count": len(reasoning["active_defeaters"]),
        }

    def _register_defaults(self) -> None:
        """Register baseline theories and defeater rules."""
        self.register_theory(
            ArgumentTheory(
                theory_id="structural_validity",
                premise="Assurance case has no structural validation errors",
                conclusion="Case structure supports argument soundness",
                weight=0.25,
                evaluator=lambda case, _ctx: bool(case.validate()["valid"]),
            )
        )
        self.register_theory(
            ArgumentTheory(
                theory_id="evidence_coverage",
                premise="Most nodes have linked evidence",
                conclusion="Evidence base is sufficiently comprehensive",
                weight=0.25,
                evaluator=lambda case, _ctx: self._coverage_ratio(case) >= 0.70,
            )
        )
        self.register_theory(
            ArgumentTheory(
                theory_id="goal_support",
                premise="Goals are decomposed into child strategies/solutions",
                conclusion="Top-level claims have supporting structure",
                weight=0.20,
                evaluator=lambda case, _ctx: self._goal_support_ratio(case) >= 0.70,
            )
        )

        self._defeaters["validation_errors"] = Defeater(
            defeater_id="validation_errors",
            defeater_type=DefeaterType.REBUTTAL,
            description="Case validation errors undermine the argument",
            severity=0.35,
            evaluator=lambda case, _ctx: not bool(case.validate()["valid"]),
        )
        self._defeaters["uncovered_assumptions"] = Defeater(
            defeater_id="uncovered_assumptions",
            defeater_type=DefeaterType.UNDERCUT,
            description="Unjustified assumptions are present",
            severity=0.20,
            evaluator=lambda case, _ctx: self._assumption_without_evidence(case) > 0,
        )
        self._defeaters["critical_vulnerabilities"] = Defeater(
            defeater_id="critical_vulnerabilities",
            defeater_type=DefeaterType.COUNTEREXAMPLE,
            description="Critical vulnerabilities are reported in context",
            severity=0.30,
            evaluator=lambda _case, ctx: int(ctx.get("critical_vulnerabilities", 0)) > 0,
        )

    def _coverage_ratio(self, case: AssuranceCase) -> float:
        """Return ratio of nodes that have any linked evidence."""
        total = len(case.nodes)
        if total == 0:
            return 0.0
        covered = sum(1 for node in case.nodes.values() if node.evidence_ids)
        return covered / total

    def _goal_support_ratio(self, case: AssuranceCase) -> float:
        """Return ratio of goal nodes that have at least one child."""
        goals = [
            node
            for node in case.nodes.values()
            if node.node_type == GSNNodeType.GOAL
        ]
        if not goals:
            return 0.0
        supported = sum(1 for goal in goals if goal.children)
        return supported / len(goals)

    def _assumption_without_evidence(self, case: AssuranceCase) -> int:
        """Count assumption nodes with no evidence attachments."""
        return sum(
            1
            for node in case.nodes.values()
            if node.node_type == GSNNodeType.ASSUMPTION and not node.evidence_ids
        )

    def _build_recommendations(
        self,
        case: AssuranceCase,
        applicable_theories: List[Dict[str, Any]],
        active_defeaters: List[Dict[str, Any]],
    ) -> List[str]:
        """Produce concise remediation recommendations for reasoning output."""
        recommendations: List[str] = []

        if not applicable_theories:
            recommendations.append("Collect additional evidence to activate theories.")

        if self._coverage_ratio(case) < 0.70:
            recommendations.append("Increase evidence coverage across case nodes.")

        for defeater in active_defeaters:
            if defeater["defeater_id"] == "validation_errors":
                recommendations.append("Resolve assurance-case structural errors.")
            elif defeater["defeater_id"] == "uncovered_assumptions":
                recommendations.append("Justify or evidence all assumption nodes.")
            elif defeater["defeater_id"] == "critical_vulnerabilities":
                recommendations.append("Mitigate critical vulnerabilities before release.")

        if not recommendations:
            recommendations.append("Maintain current evidence quality and monitor drift.")

        return recommendations