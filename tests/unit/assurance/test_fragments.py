"""Unit tests for assurance case fragments."""

from civ_arcos.assurance.fragments import FragmentLibrary


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
