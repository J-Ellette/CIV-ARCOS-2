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
    fragment = engine.get_fragment("system")
    assert fragment is not None
    assert len(fragment.case.nodes) >= 2


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


def test_argtl_assemble_alias_creates_target_fragment() -> None:
    """Assemble should behave as compose and create a target fragment."""
    engine = _seed_engine()

    result = engine.execute_line("assemble frag_a frag_b -> assembled")

    assert result.operation == "assemble"
    assert result.success is True
    assert engine.get_fragment("assembled") is not None


def test_argtl_execute_script_processes_multiple_lines() -> None:
    """Script execution should evaluate each non-empty line in order."""
    engine = _seed_engine()

    results = engine.execute_script("""
compose frag_a frag_b -> system
validate system
""".strip())

    assert len(results) == 2
    assert results[0].operation == "compose"
    assert results[1].operation == "validate"


def test_argtl_compose_requires_two_source_fragments() -> None:
    """Compose with fewer than two source fragments should fail."""
    engine = _seed_engine()

    result = engine.execute_line("compose frag_a -> single")

    assert result.operation == "compose"
    assert result.success is False
    assert "at least two source fragments" in str(result.detail.get("error", ""))


def test_argtl_unsupported_operation_returns_failed_result() -> None:
    """Unknown operations should return an explicit failure result."""
    engine = _seed_engine()

    result = engine.execute_line("transform frag_a")

    assert result.success is False
    assert result.operation == "transform"
    assert "Unsupported ArgTL operation" in str(result.detail.get("error", ""))


def test_argtl_compose_fails_for_unknown_source_fragment() -> None:
    """Compose should fail when any source fragment id is missing."""
    engine = _seed_engine()

    result = engine.execute_line("compose frag_a frag_missing -> system")

    assert result.operation == "compose"
    assert result.success is False
    assert "Unknown fragment: frag_missing" in str(result.detail.get("error", ""))


def test_argtl_link_requires_expected_to_syntax() -> None:
    """Link must include the 'to' keyword according to grammar."""
    engine = _seed_engine()

    result = engine.execute_line("link frag_a frag_b")

    assert result.operation == "link"
    assert result.success is False
    assert "Link syntax" in str(result.detail.get("error", ""))


def test_argtl_validate_fails_for_unknown_fragment() -> None:
    """Validate should fail when target fragment is not registered."""
    engine = _seed_engine()

    result = engine.execute_line("validate missing_fragment")

    assert result.operation == "validate"
    assert result.success is False
    assert "Unknown fragment" in str(result.detail.get("error", ""))


def test_argtl_compose_fails_for_missing_arrow_syntax() -> None:
    """Compose without '->' should fail with syntax guidance."""
    engine = _seed_engine()

    result = engine.execute_line("compose frag_a frag_b system")

    assert result.operation == "compose"
    assert result.success is False
    assert "Compose syntax" in str(result.detail.get("error", ""))


def test_argtl_link_fails_when_target_fragment_missing() -> None:
    """Link should fail when target fragment is not registered."""
    engine = _seed_engine()

    result = engine.execute_line("link frag_a to missing")

    assert result.operation == "link"
    assert result.success is False
    assert "must exist" in str(result.detail.get("error", ""))


def test_argtl_validate_requires_single_fragment_identifier() -> None:
    """Validate command should reject extra tokens."""
    engine = _seed_engine()

    result = engine.execute_line("validate frag_a extra")

    assert result.operation == "validate"
    assert result.success is False
    assert "Validate syntax" in str(result.detail.get("error", ""))


def test_argtl_assemble_propagates_compose_failure_for_unknown_source() -> None:
    """Assemble should report failure when compose preconditions are not met."""
    engine = _seed_engine()

    result = engine.execute_line("assemble frag_a frag_missing -> assembled")

    assert result.operation == "assemble"
    assert result.success is False
    assert "Unknown fragment" in str(result.detail.get("error", ""))


def test_argtl_operation_parsing_is_case_insensitive() -> None:
    """Uppercase operation keywords should be accepted by parser."""
    engine = _seed_engine()

    result = engine.execute_line("COMPOSE frag_a frag_b -> system_caps")

    assert result.operation == "compose"
    assert result.success is True
    assert engine.get_fragment("system_caps") is not None


def test_argtl_empty_line_returns_unknown_operation_failure() -> None:
    """Empty input line should return a structured unknown-operation error."""
    engine = _seed_engine()

    result = engine.execute_line("")

    assert result.operation == "unknown"
    assert result.success is False
    assert "Empty operation" in str(result.detail.get("error", ""))
