"""Unit tests for assurance case fragments."""

import pytest
from typing import Any, cast

from civ_arcos.assurance.case import AssuranceCase, AssuranceCaseBuilder
from civ_arcos.assurance.fragments import AssuranceCaseFragment, FragmentLibrary


def test_fragment_library_creates_component_quality_fragment() -> None:
    """Library should build a reusable quality fragment with a root goal."""
    library = FragmentLibrary()
    fragment = library.create_fragment(
        pattern="component_quality",
        fragment_id="frag_quality",
        title="Quality Fragment",
        description="Quality argument for module",
        component_name="storage",
    )

    assert fragment.fragment_id == "frag_quality"
    assert fragment.case.root_goal_id == "frag_quality_goal_quality"
    assert fragment.case.get_root_goal() is not None


def test_fragment_strength_increases_with_valid_evidence() -> None:
    """Fragment strength score should be positive for valid/evidenced case."""
    library = FragmentLibrary()
    fragment = library.create_fragment(
        pattern="component_security",
        fragment_id="frag_sec",
        title="Security Fragment",
        description="Security argument",
        component_name="api",
    )

    assert fragment.strength() > 0.0


def test_fragment_dependencies_are_unique() -> None:
    """Dependency ids should not be duplicated in fragment metadata."""
    library = FragmentLibrary()
    fragment = library.create_fragment(
        pattern="integration",
        fragment_id="frag_int",
        title="Integration Fragment",
        description="Integration argument",
        component_name="platform",
    )

    fragment.add_dependency("frag_a")
    fragment.add_dependency("frag_a")

    assert fragment.dependencies == ["frag_a"]


def test_fragment_library_rejects_unknown_pattern() -> None:
    """Creating a fragment with unknown pattern should fail fast."""
    library = FragmentLibrary()

    with pytest.raises(ValueError):
        library.create_fragment(
            pattern="unknown_pattern",
            fragment_id="frag_x",
            title="X",
            description="X",
        )


def test_fragment_library_lists_fragments_in_sorted_id_order() -> None:
    """Fragment listing should be deterministic and sorted by fragment id."""
    library = FragmentLibrary()
    library.create_fragment(
        pattern="component_quality",
        fragment_id="frag_b",
        title="B",
        description="B",
    )
    library.create_fragment(
        pattern="component_security",
        fragment_id="frag_a",
        title="A",
        description="A",
    )

    listed_ids = [fragment.fragment_id for fragment in library.list_fragments()]
    assert listed_ids == ["frag_a", "frag_b"]


def test_fragment_get_fragment_returns_none_for_unknown_id() -> None:
    """Unknown fragment identifiers should return None."""
    library = FragmentLibrary()

    assert library.get_fragment("missing_fragment") is None


def test_fragment_register_pattern_supports_custom_builder() -> None:
    """Custom pattern builders should be invokable through create_fragment."""
    library = FragmentLibrary()

    def custom_builder(
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

    cast(Any, library).register_pattern("custom_security", custom_builder)
    fragment = library.create_fragment(
        pattern="custom_security",
        fragment_id="frag_custom",
        title="Custom",
        description="Custom",
        component_name="service",
    )

    assert fragment.fragment_id == "frag_custom"
    assert fragment.case.root_goal_id == "frag_custom_goal_security"


def test_fragment_strength_is_capped_at_one_for_fully_linked_valid_case() -> None:
    """Strength score should never exceed 1.0 for strong cases."""
    library = FragmentLibrary()
    fragment = library.create_fragment(
        pattern="component_quality",
        fragment_id="frag_cap",
        title="Cap",
        description="Cap",
        component_name="service",
    )

    for node in fragment.case.nodes.values():
        if not node.evidence_ids:
            node.evidence_ids.append(f"ev_{node.id}")

    assert fragment.strength() == 1.0


def test_fragment_strength_is_zero_for_invalid_case_without_evidence() -> None:
    """Invalid fragment with no evidence should floor strength at zero."""
    library = FragmentLibrary()

    def empty_builder(
        fragment_id: str,
        title: str,
        description: str,
        _component_name: str,
    ) -> AssuranceCaseFragment:
        case = AssuranceCase(title=title, description=description)
        return AssuranceCaseFragment(
            fragment_id=fragment_id,
            title=title,
            description=description,
            case=case,
        )

    cast(Any, library).register_pattern("empty_case", empty_builder)
    fragment = library.create_fragment(
        pattern="empty_case",
        fragment_id="frag_empty",
        title="Empty",
        description="Empty",
    )

    assert fragment.strength() == 0.0


def test_fragment_add_dependency_ignores_empty_dependency_id() -> None:
    """Empty dependency identifiers should not be added."""
    library = FragmentLibrary()
    fragment = library.create_fragment(
        pattern="integration",
        fragment_id="frag_dep",
        title="Deps",
        description="Deps",
        component_name="platform",
    )

    fragment.add_dependency("")

    assert fragment.dependencies == []
