"""Unit tests for ACQL query evaluation."""

from civ_arcos.assurance.acql import ACQLEngine
from civ_arcos.assurance.fragments import FragmentLibrary


def _seed_acql() -> ACQLEngine:
    """Build ACQL engine with one fragment and one case target."""
    library = FragmentLibrary()
    fragment = library.create_fragment(
        pattern="component_quality",
        fragment_id="frag_case",
        title="Case",
        description="Case",
        component_name="graph",
    )

    engine = ACQLEngine()
    engine.register_fragment(fragment)
    engine.register_case(fragment.case)
    return engine


def test_acql_consistency_query_passes_for_valid_fragment() -> None:
    """Consistency query should pass for a structurally valid fragment."""
    engine = _seed_acql()

    result = engine.execute_line("consistency on frag_case")

    assert result.passed is True
    assert result.query_type == "consistency"


def test_acql_dependencies_returns_fragment_dependencies() -> None:
    """Dependencies query should expose tracked fragment dependencies."""
    engine = _seed_acql()
    fragment = engine._fragments["frag_case"]
    fragment.add_dependency("frag_other")

    result = engine.execute_line("dependencies on frag_case")

    assert result.passed is True
    assert result.details["dependencies"] == ["frag_other"]


def test_acql_weaknesses_lists_validation_findings() -> None:
    """Weaknesses query should return warnings/errors when present."""
    engine = _seed_acql()

    result = engine.execute_line("weaknesses on frag_case")

    assert result.query_type == "weaknesses"
    assert "weaknesses" in result.details
