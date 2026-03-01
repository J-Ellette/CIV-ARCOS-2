"""Integration tests for Step 5 orchestration failure/edge paths."""

import tempfile
from pathlib import Path

import pytest

from civ_arcos.assurance.acql import ACQLEngine
from civ_arcos.assurance.architecture import ArchitectureMapper
from civ_arcos.assurance.argtl import ArgTLEngine
from civ_arcos.assurance.dependency_tracker import (
    DependencyTracker,
    DependencyType,
    ResourceType,
)
from civ_arcos.assurance.fragments import FragmentLibrary


def _create_source_tree(tmp_path: Path) -> str:
    """Create minimal source tree used by orchestration negative tests."""
    module = tmp_path / "module.py"
    module.write_text(
        """
class Service:
    pass

def run_service():
    return True
""".strip(),
        encoding="utf-8",
    )
    return str(tmp_path)


def _build_fragments_from_architecture() -> list:
    """Infer architecture and create baseline fragments for each component."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = _create_source_tree(Path(tmpdir))
        inferred = ArchitectureMapper().infer_architecture(source_path)

    library = FragmentLibrary()
    fragments = []
    for index, component in enumerate(inferred["components"]):
        pattern = (
            "component_quality"
            if component["type"] == "class"
            else "component_security"
        )
        fragments.append(
            library.create_fragment(
                pattern=pattern,
                fragment_id=f"frag_fail_{index}",
                title=f"{component['name']} fragment",
                description="failure path",
                component_name=component["name"],
            )
        )
    return fragments


def test_orchestration_acql_completeness_fails_without_added_evidence() -> None:
    """Completeness should fail when composed case retains warning-level gaps."""
    fragments = _build_fragments_from_architecture()
    engine = ArgTLEngine()
    for fragment in fragments:
        engine.register_fragment(fragment)

    compose = engine.execute_line(
        "compose "
        + " ".join(fragment.fragment_id for fragment in fragments)
        + " -> system_fail_case"
    )
    assert compose.success is True

    assembled = engine.get_fragment("system_fail_case")
    assert assembled is not None

    acql = ACQLEngine()
    acql.register_fragment(assembled)
    completeness = acql.execute_line("completeness on system_fail_case")

    assert completeness.query_type == "completeness"
    assert completeness.passed is False


def test_orchestration_argtl_compose_fails_with_unknown_fragment() -> None:
    """Compose should fail when orchestration references missing fragments."""
    fragments = _build_fragments_from_architecture()
    engine = ArgTLEngine()
    engine.register_fragment(fragments[0])

    compose = engine.execute_line(
        "compose frag_fail_0 frag_missing -> system_fail_case"
    )

    assert compose.operation == "compose"
    assert compose.success is False


def test_orchestration_argtl_link_fails_for_missing_target() -> None:
    """Link operation should fail for unregistered target fragment."""
    fragments = _build_fragments_from_architecture()
    engine = ArgTLEngine()
    engine.register_fragment(fragments[0])

    link = engine.execute_line("link frag_fail_0 to missing_target")

    assert link.operation == "link"
    assert link.success is False


def test_orchestration_dependency_link_fails_for_missing_resource() -> None:
    """Dependency linkage should fail when required resources are absent."""
    tracker = DependencyTracker()
    tracker.register_resource("res_case", ResourceType.MODEL, "assembled_case")

    with pytest.raises(ValueError):
        tracker.link_dependency(
            "res_component_0",
            "res_case",
            DependencyType.IMPLEMENTS,
        )


def test_orchestration_dependency_impact_fails_for_unknown_start_node() -> None:
    """Impact analysis should reject unknown root resources."""
    tracker = DependencyTracker()
    tracker.register_resource("res_case", ResourceType.MODEL, "assembled_case")

    with pytest.raises(ValueError):
        tracker.impact_analysis("missing_resource")
