"""Assurance Case Query Language (ACQL) baseline evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from civ_arcos.assurance.case import AssuranceCase
from civ_arcos.assurance.fragments import AssuranceCaseFragment


class ACQLQueryType(str, Enum):
    """Supported ACQL query categories."""

    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    SOUNDNESS = "soundness"
    COVERAGE = "coverage"
    TRACEABILITY = "traceability"
    WEAKNESSES = "weaknesses"
    DEPENDENCIES = "dependencies"
    DEFEATERS = "defeaters"


@dataclass
class ACQLResult:
    """Structured ACQL query result payload."""

    query_type: str
    target: str
    passed: bool
    summary: str
    details: Dict[str, object]


class ACQLEngine:
    """Evaluate ACQL queries over assurance cases and fragments."""

    def __init__(self) -> None:
        self._cases: Dict[str, AssuranceCase] = {}
        self._fragments: Dict[str, AssuranceCaseFragment] = {}

    def register_case(self, case: AssuranceCase) -> None:
        """Register an assurance case for ACQL querying."""
        self._cases[case.case_id] = case

    def register_fragment(self, fragment: AssuranceCaseFragment) -> None:
        """Register an assurance fragment for ACQL querying."""
        self._fragments[fragment.fragment_id] = fragment

    def execute_script(self, script: str) -> List[ACQLResult]:
        """Execute newline-delimited ACQL query script lines."""
        results: List[ACQLResult] = []
        for line in script.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            results.append(self.execute_line(stripped))
        return results

    def execute_line(self, line: str) -> ACQLResult:
        """Execute one ACQL line in form '<query> on <target>'."""
        tokens = line.split()
        if len(tokens) != 3 or tokens[1].lower() != "on":
            return ACQLResult(
                query_type="unknown",
                target="unknown",
                passed=False,
                summary="Invalid ACQL syntax",
                details={"error": "Use format: <query> on <target>"},
            )

        query_type = tokens[0].lower()
        target = tokens[2]
        qtype = ACQLQueryType(query_type)
        return self.run_query(qtype, target)

    def run_query(self, query_type: ACQLQueryType, target: str) -> ACQLResult:
        """Run one ACQL query for a target case/fragment."""
        fragment = self._fragments.get(target)
        case = self._cases.get(target)
        target_case: Optional[AssuranceCase] = None

        if fragment is not None:
            target_case = fragment.case
        elif case is not None:
            target_case = case

        if target_case is None:
            return ACQLResult(
                query_type=query_type.value,
                target=target,
                passed=False,
                summary="Unknown target",
                details={"error": f"No case or fragment named '{target}'"},
            )

        if query_type == ACQLQueryType.CONSISTENCY:
            return self._query_consistency(target, target_case)
        if query_type == ACQLQueryType.COMPLETENESS:
            return self._query_completeness(target, target_case)
        if query_type == ACQLQueryType.SOUNDNESS:
            return self._query_soundness(target, target_case)
        if query_type == ACQLQueryType.COVERAGE:
            return self._query_coverage(target, target_case)
        if query_type == ACQLQueryType.TRACEABILITY:
            return self._query_traceability(target, target_case)
        if query_type == ACQLQueryType.WEAKNESSES:
            return self._query_weaknesses(target, target_case)
        if query_type == ACQLQueryType.DEPENDENCIES:
            return self._query_dependencies(target)
        return self._query_defeaters(target, target_case)

    def _query_consistency(
        self,
        target: str,
        case: AssuranceCase,
    ) -> ACQLResult:
        validation = case.validate()
        passed = bool(validation["valid"])
        return ACQLResult(
            query_type=ACQLQueryType.CONSISTENCY.value,
            target=target,
            passed=passed,
            summary="Case is consistent" if passed else "Case has inconsistencies",
            details=validation,
        )

    def _query_completeness(
        self,
        target: str,
        case: AssuranceCase,
    ) -> ACQLResult:
        validation = case.validate()
        warnings = validation["warnings"]
        passed = len(warnings) == 0 and bool(validation["valid"])
        return ACQLResult(
            query_type=ACQLQueryType.COMPLETENESS.value,
            target=target,
            passed=passed,
            summary=(
                "Case is complete" if passed
                else "Case has missing coverage/evidence elements"
            ),
            details={"warnings": warnings, "errors": validation["errors"]},
        )

    def _query_soundness(
        self,
        target: str,
        case: AssuranceCase,
    ) -> ACQLResult:
        validation = case.validate()
        passed = bool(validation["valid"]) and case.root_goal_id is not None
        return ACQLResult(
            query_type=ACQLQueryType.SOUNDNESS.value,
            target=target,
            passed=passed,
            summary="Case is sound" if passed else "Case is unsound",
            details={
                "root_goal_id": case.root_goal_id,
                "errors": validation["errors"],
            },
        )

    def _query_coverage(
        self,
        target: str,
        case: AssuranceCase,
    ) -> ACQLResult:
        total = len(case.nodes)
        covered = 0
        for node in case.nodes.values():
            if node.evidence_ids:
                covered += 1

        ratio = 0.0 if total == 0 else round(covered / total, 3)
        passed = ratio >= 0.7
        return ACQLResult(
            query_type=ACQLQueryType.COVERAGE.value,
            target=target,
            passed=passed,
            summary=f"Evidence coverage ratio: {ratio}",
            details={"covered_nodes": covered, "total_nodes": total, "ratio": ratio},
        )

    def _query_traceability(
        self,
        target: str,
        case: AssuranceCase,
    ) -> ACQLResult:
        links = 0
        for node in case.nodes.values():
            links += len(node.evidence_ids)

        passed = links > 0
        return ACQLResult(
            query_type=ACQLQueryType.TRACEABILITY.value,
            target=target,
            passed=passed,
            summary="Traceability links found" if passed else "No traceability links",
            details={"evidence_links": links},
        )

    def _query_weaknesses(
        self,
        target: str,
        case: AssuranceCase,
    ) -> ACQLResult:
        validation = case.validate()
        weaknesses = list(validation["errors"]) + list(validation["warnings"])
        passed = len(weaknesses) == 0
        return ACQLResult(
            query_type=ACQLQueryType.WEAKNESSES.value,
            target=target,
            passed=passed,
            summary="No weaknesses found" if passed else "Weaknesses identified",
            details={"weaknesses": weaknesses},
        )

    def _query_dependencies(self, target: str) -> ACQLResult:
        fragment = self._fragments.get(target)
        if fragment is None:
            return ACQLResult(
                query_type=ACQLQueryType.DEPENDENCIES.value,
                target=target,
                passed=False,
                summary="Dependencies query requires a fragment target",
                details={"dependencies": []},
            )

        return ACQLResult(
            query_type=ACQLQueryType.DEPENDENCIES.value,
            target=target,
            passed=True,
            summary="Dependencies enumerated",
            details={"dependencies": list(fragment.dependencies)},
        )

    def _query_defeaters(
        self,
        target: str,
        case: AssuranceCase,
    ) -> ACQLResult:
        defeaters = []
        for node in case.nodes.values():
            if node.node_type.value == "assumption" and not node.evidence_ids:
                defeaters.append(node.id)

        passed = len(defeaters) == 0
        return ACQLResult(
            query_type=ACQLQueryType.DEFEATERS.value,
            target=target,
            passed=passed,
            summary=(
                "No active defeaters" if passed else
                "Potential defeaters identified"
            ),
            details={"defeaters": defeaters},
        )
