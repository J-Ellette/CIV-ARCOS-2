"""Assurance case fragments and reusable fragment library."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from civ_arcos.assurance.case import AssuranceCase, AssuranceCaseBuilder


@dataclass
class AssuranceCaseFragment:
    """Self-contained assurance fragment with optional dependencies."""

    fragment_id: str
    title: str
    description: str
    case: AssuranceCase
    dependencies: List[str] = field(default_factory=list)

    def add_dependency(self, dependency_id: str) -> None:
        """Register another fragment as a dependency."""
        if dependency_id and dependency_id not in self.dependencies:
            self.dependencies.append(dependency_id)

    def strength(self) -> float:
        """Estimate fragment strength from validation and evidence links."""
        total_nodes = len(self.case.nodes)
        if total_nodes == 0:
            return 0.0

        linked_nodes = 0
        for node in self.case.nodes.values():
            if node.evidence_ids:
                linked_nodes += 1

        validation = self.case.validate()
        base = linked_nodes / total_nodes
        if validation["valid"]:
            return round(min(1.0, base + 0.2), 3)
        return round(max(0.0, base - 0.2), 3)


class FragmentLibrary:
    """Factory and registry for common assurance case fragments."""

    def __init__(self) -> None:
        self._fragment_builders = {
            "component_quality": self._build_component_quality,
            "component_security": self._build_component_security,
            "integration": self._build_integration,
        }
        self._fragments: Dict[str, AssuranceCaseFragment] = {}

    def register_pattern(self, name: str, pattern_builder) -> None:
        """Register a custom fragment builder callable."""
        self._fragment_builders[name] = pattern_builder

    def create_fragment(
        self,
        pattern: str,
        fragment_id: str,
        title: str,
        description: str,
        component_name: str = "component",
    ) -> AssuranceCaseFragment:
        """Create, register, and return a fragment from a pattern."""
        builder = self._fragment_builders.get(pattern)
        if builder is None:
            raise ValueError(f"Unknown fragment pattern: {pattern}")
        fragment = builder(fragment_id, title, description, component_name)
        self._fragments[fragment.fragment_id] = fragment
        return fragment

    def get_fragment(self, fragment_id: str) -> Optional[AssuranceCaseFragment]:
        """Fetch a previously created fragment by ID."""
        return self._fragments.get(fragment_id)

    def list_fragments(self) -> List[AssuranceCaseFragment]:
        """Return all registered fragments in deterministic order."""
        return [self._fragments[k] for k in sorted(self._fragments.keys())]

    def _build_component_quality(
        self,
        fragment_id: str,
        title: str,
        description: str,
        component_name: str,
    ) -> AssuranceCaseFragment:
        case_builder = AssuranceCaseBuilder(
            title=title,
            description=description,
            project_type="fragment",
        )
        case_builder.add_goal(
            f"{component_name} quality is acceptable",
            node_id=f"{fragment_id}_goal_quality",
        ).set_as_root()
        case_builder.add_strategy(
            "Argument by static analysis and test evidence",
            node_id=f"{fragment_id}_strategy_quality",
        ).link_to_parent(f"{fragment_id}_goal_quality")
        case_builder.add_solution(
            "Coverage and complexity evidence supports quality",
            evidence_ids=[f"ev_{fragment_id}_quality"],
            node_id=f"{fragment_id}_solution_quality",
        ).link_to_parent(f"{fragment_id}_strategy_quality")

        return AssuranceCaseFragment(
            fragment_id=fragment_id,
            title=title,
            description=description,
            case=case_builder.build(),
        )

    def _build_component_security(
        self,
        fragment_id: str,
        title: str,
        description: str,
        component_name: str,
    ) -> AssuranceCaseFragment:
        case_builder = AssuranceCaseBuilder(
            title=title,
            description=description,
            project_type="fragment",
        )
        case_builder.add_goal(
            f"{component_name} has acceptable security posture",
            node_id=f"{fragment_id}_goal_security",
        ).set_as_root()
        case_builder.add_solution(
            "Security scan indicates no critical vulnerabilities",
            evidence_ids=[f"ev_{fragment_id}_security"],
            node_id=f"{fragment_id}_solution_security",
        ).link_to_parent(f"{fragment_id}_goal_security")

        return AssuranceCaseFragment(
            fragment_id=fragment_id,
            title=title,
            description=description,
            case=case_builder.build(),
        )

    def _build_integration(
        self,
        fragment_id: str,
        title: str,
        description: str,
        component_name: str,
    ) -> AssuranceCaseFragment:
        case_builder = AssuranceCaseBuilder(
            title=title,
            description=description,
            project_type="fragment",
        )
        case_builder.add_goal(
            f"{component_name} integrations preserve system integrity",
            node_id=f"{fragment_id}_goal_integration",
        ).set_as_root()
        case_builder.add_strategy(
            "Argument by interface tests and dependency validation",
            node_id=f"{fragment_id}_strategy_integration",
        ).link_to_parent(f"{fragment_id}_goal_integration")
        case_builder.add_solution(
            "Integration tests validate expected cross-component behavior",
            evidence_ids=[f"ev_{fragment_id}_integration"],
            node_id=f"{fragment_id}_solution_integration",
        ).link_to_parent(f"{fragment_id}_strategy_integration")

        return AssuranceCaseFragment(
            fragment_id=fragment_id,
            title=title,
            description=description,
            case=case_builder.build(),
        )
