"""Unit tests for ArgTL script execution."""

from civ_arcos.assurance.argtl import ArgTLEngine
from civ_arcos.assurance.fragments import FragmentLibrary


def _seed_engine() -> ArgTLEngine:
    """Create an engine preloaded with two baseline fragments."""
    library = FragmentLibrary()
    frag_a = library.create_fragment(
        pattern="component_quality",
        fragment_id="frag_a",
        title="A",
        description="A",
        component_name="collector",
    )
    frag_b = library.create_fragment(
        pattern="component_security",
        fragment_id="frag_b",
        title="B",
        description="B",
        component_name="collector",
    )

    engine = ArgTLEngine()
    engine.register_fragment(frag_a)
    engine.register_fragment(frag_b)
    return engine


def test_argtl_compose_creates_target_fragment() -> None:
    """Compose operation should create a new fragment from source fragments."""
    engine = _seed_engine()

    result = engine.execute_line("compose frag_a frag_b -> system")

    assert result.success is True
    assert engine.get_fragment("system") is not None
    assert result.detail["node_count"] >= 2


def test_argtl_link_adds_dependency() -> None:
    """Link operation should append source as target dependency."""
    engine = _seed_engine()

    result = engine.execute_line("link frag_a to frag_b")

    assert result.success is True
    target = engine.get_fragment("frag_b")
    assert target is not None
    assert "frag_a" in target.dependencies


def test_argtl_validate_reports_fragment_state() -> None:
    """Validate operation should return case validation metadata."""
    engine = _seed_engine()

    result = engine.execute_line("validate frag_a")

    assert result.operation == "validate"
    assert "warnings" in result.detail
