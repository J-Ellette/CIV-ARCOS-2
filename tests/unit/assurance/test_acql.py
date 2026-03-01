"""Unit tests for ACQL query evaluation."""

import pytest

from civ_arcos.assurance.case import AssuranceCaseBuilder
from civ_arcos.assurance.acql import ACQLEngine
from civ_arcos.assurance.fragments import FragmentLibrary
from civ_arcos.assurance.gsn import GSNAssumption


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


def test_acql_invalid_syntax_returns_error_result() -> None:
    """Malformed ACQL syntax should return a failed parse result."""
    engine = _seed_acql()

    result = engine.execute_line("consistency frag_case")

    assert result.passed is False
    assert result.query_type == "unknown"
    assert "Invalid ACQL syntax" in result.summary


def test_acql_unknown_target_returns_failed_result() -> None:
    """Querying an unregistered target should fail cleanly."""
    engine = _seed_acql()

    result = engine.execute_line("consistency on missing_case")

    assert result.passed is False
    assert "Unknown target" in result.summary


def test_acql_defeaters_query_finds_unsupported_assumption() -> None:
    """Defeaters query should identify uncovered assumption nodes."""
    builder = AssuranceCaseBuilder(title="Defeater Case")
    builder.add_goal("System remains safe", node_id="g1").set_as_root()
    case = builder.build()
    case.add_node(GSNAssumption("Assume trusted runtime", node_id="a1"))

    engine = ACQLEngine()
    engine.register_case(case)

    result = engine.execute_line(f"defeaters on {case.case_id}")

    assert result.query_type == "defeaters"
    assert result.passed is False
    assert "a1" in str(result.details)


def test_acql_invalid_query_type_raises_value_error() -> None:
    """Unsupported ACQL query keywords should raise ValueError."""
    engine = _seed_acql()

    with pytest.raises(ValueError):
        engine.execute_line("nonsense on frag_case")


def test_acql_dependencies_on_case_target_fails_cleanly() -> None:
    """Dependencies query should fail when target is a case, not a fragment."""
    builder = AssuranceCaseBuilder(title="Case Target")
    builder.add_goal("Goal", node_id="g1").set_as_root()
    case = builder.build()

    engine = ACQLEngine()
    engine.register_case(case)

    result = engine.execute_line(f"dependencies on {case.case_id}")

    assert result.query_type == "dependencies"
    assert result.passed is False
    assert "requires a fragment target" in result.summary


def test_acql_execute_script_ignores_blank_lines() -> None:
    """Script execution should skip empty lines and keep query ordering."""
    engine = _seed_acql()

    results = engine.execute_script("""

consistency on frag_case

coverage on frag_case
""".strip())

    assert len(results) == 2
    assert results[0].query_type == "consistency"
    assert results[1].query_type == "coverage"


def test_acql_coverage_query_passes_after_full_evidence_linking() -> None:
    """Coverage query should pass when evidence ratio meets threshold."""
    library = FragmentLibrary()
    fragment = library.create_fragment(
        pattern="component_quality",
        fragment_id="frag_cov",
        title="Coverage Case",
        description="Coverage",
        component_name="engine",
    )

    for node in fragment.case.nodes.values():
        if not node.evidence_ids:
            node.evidence_ids.append(f"ev_{node.id}")

    engine = ACQLEngine()
    engine.register_fragment(fragment)

    result = engine.execute_line("coverage on frag_cov")

    assert result.query_type == "coverage"
    assert result.passed is True


def test_acql_completeness_fails_when_warnings_present() -> None:
    """Completeness should fail when nodes are missing evidence links."""
    engine = _seed_acql()

    result = engine.execute_line("completeness on frag_case")

    assert result.query_type == "completeness"
    assert result.passed is False
    assert "warnings" in result.details


def test_acql_completeness_passes_after_full_evidence_linking() -> None:
    """Completeness should pass once all nodes have evidence and no errors."""
    library = FragmentLibrary()
    fragment = library.create_fragment(
        pattern="component_quality",
        fragment_id="frag_complete",
        title="Complete Case",
        description="Complete",
        component_name="component",
    )
    for node in fragment.case.nodes.values():
        if not node.evidence_ids:
            node.evidence_ids.append(f"ev_{node.id}")

    engine = ACQLEngine()
    engine.register_fragment(fragment)

    result = engine.execute_line("completeness on frag_complete")

    assert result.query_type == "completeness"
    assert result.passed is True


def test_acql_soundness_passes_for_valid_case_with_root() -> None:
    """Soundness should pass for a valid case with an explicit root goal."""
    engine = _seed_acql()

    result = engine.execute_line("soundness on frag_case")

    assert result.query_type == "soundness"
    assert result.passed is True


def test_acql_soundness_fails_for_case_without_root() -> None:
    """Soundness should fail when the case has no root goal set."""
    builder = AssuranceCaseBuilder(title="No Root")
    builder.add_goal("Top claim", node_id="g1")
    case = builder.build()

    engine = ACQLEngine()
    engine.register_case(case)

    result = engine.execute_line(f"soundness on {case.case_id}")

    assert result.query_type == "soundness"
    assert result.passed is False


def test_acql_traceability_fails_when_no_evidence_links_exist() -> None:
    """Traceability should fail when there are zero evidence links."""
    builder = AssuranceCaseBuilder(title="No Traceability")
    builder.add_goal("Goal", node_id="g1").set_as_root()
    builder.add_strategy("Strategy", node_id="s1").link_to_parent("g1")
    case = builder.build()

    engine = ACQLEngine()
    engine.register_case(case)

    result = engine.execute_line(f"traceability on {case.case_id}")

    assert result.query_type == "traceability"
    assert result.passed is False


def test_acql_traceability_passes_when_evidence_links_exist() -> None:
    """Traceability should pass when at least one evidence link is present."""
    library = FragmentLibrary()
    fragment = library.create_fragment(
        pattern="component_quality",
        fragment_id="frag_trace",
        title="Trace Case",
        description="Trace",
        component_name="component",
    )
    for node in fragment.case.nodes.values():
        node.evidence_ids.append(f"ev_{node.id}")

    engine = ACQLEngine()
    engine.register_fragment(fragment)

    result = engine.execute_line("traceability on frag_trace")

    assert result.query_type == "traceability"
    assert result.passed is True


def test_acql_coverage_fails_below_threshold() -> None:
    """Coverage should fail when evidence ratio is under the acceptance threshold."""
    builder = AssuranceCaseBuilder(title="Coverage Low")
    builder.add_goal("Goal", node_id="g1").set_as_root()
    builder.add_strategy("Strategy", node_id="s1").link_to_parent("g1")
    builder.add_solution(
        "Solution",
        evidence_ids=["ev_sln"],
        node_id="sol1",
    ).link_to_parent("s1")
    case = builder.build()

    engine = ACQLEngine()
    engine.register_case(case)

    result = engine.execute_line(f"coverage on {case.case_id}")

    assert result.query_type == "coverage"
    assert result.passed is False


def test_acql_execute_line_is_case_insensitive_for_query_and_keyword() -> None:
    """Line execution should parse query and 'on' keyword case-insensitively."""
    engine = _seed_acql()

    result = engine.execute_line("CONSISTENCY ON frag_case")

    assert result.query_type == "consistency"
    assert result.passed is True


def test_acql_execute_line_with_extra_tokens_returns_invalid_syntax() -> None:
    """Four-token ACQL lines should be rejected as invalid syntax."""
    engine = _seed_acql()

    result = engine.execute_line("consistency on frag_case now")

    assert result.query_type == "unknown"
    assert result.passed is False
    assert "Invalid ACQL syntax" in result.summary


def test_acql_execute_script_mixed_queries_preserves_result_order() -> None:
    """Script mode should preserve mixed valid/invalid/unknown-target ordering."""
    engine = _seed_acql()

    results = engine.execute_script("""
consistency on frag_case
consistency frag_case
coverage on missing_case
""".strip())

    assert len(results) == 3
    assert [result.query_type for result in results] == [
        "consistency",
        "unknown",
        "coverage",
    ]
    assert [result.passed for result in results] == [True, False, False]


def test_acql_execute_script_raises_for_unsupported_query_type() -> None:
    """Script mode should raise ValueError when a query keyword is unsupported."""
    engine = _seed_acql()

    with pytest.raises(ValueError):
        engine.execute_script("""
consistency on frag_case
nonsense on frag_case
""".strip())


def test_acql_defeaters_passes_when_assumption_has_supporting_evidence() -> None:
    """Defeaters query should pass when assumptions have evidence links."""
    builder = AssuranceCaseBuilder(title="Assumption Supported")
    builder.add_goal("Safety claim", node_id="g1").set_as_root()
    case = builder.build()
    assumption = GSNAssumption("Assume trusted runtime", node_id="a1")
    assumption.evidence_ids.append("ev_assumption")
    case.add_node(assumption)

    engine = ACQLEngine()
    engine.register_case(case)

    result = engine.execute_line(f"defeaters on {case.case_id}")

    assert result.query_type == "defeaters"
    assert result.passed is True
    assert result.details["defeaters"] == []


def test_acql_execute_script_soundness_then_traceability_on_case_target() -> None:
    """Script should evaluate soundness and traceability in command order."""
    builder = AssuranceCaseBuilder(title="Case Script")
    builder.add_goal("Goal", node_id="g1").set_as_root()
    builder.add_solution(
        "Solution",
        evidence_ids=["ev_1"],
        node_id="sln1",
    ).link_to_parent("g1")
    case = builder.build()

    engine = ACQLEngine()
    engine.register_case(case)

    results = engine.execute_script(f"""
soundness on {case.case_id}
traceability on {case.case_id}
""".strip())

    assert [item.query_type for item in results] == ["soundness", "traceability"]
    assert [item.passed for item in results] == [True, True]


def test_acql_execute_script_traceability_then_soundness_both_fail() -> None:
    """Script should preserve ordering when both queries fail on sparse case."""
    builder = AssuranceCaseBuilder(title="Sparse Script")
    builder.add_goal("Goal", node_id="g1")
    case = builder.build()

    engine = ACQLEngine()
    engine.register_case(case)

    results = engine.execute_script(f"""
traceability on {case.case_id}
soundness on {case.case_id}
""".strip())

    assert [item.query_type for item in results] == ["traceability", "soundness"]
    assert [item.passed for item in results] == [False, False]


def test_acql_execute_script_mixed_case_and_fragment_targets() -> None:
    """Script should support mixed target types in one execution batch."""
    engine = _seed_acql()
    library = FragmentLibrary()
    trace_fragment = library.create_fragment(
        pattern="component_quality",
        fragment_id="frag_script_trace",
        title="Script Trace",
        description="Script Trace",
        component_name="engine",
    )
    for node in trace_fragment.case.nodes.values():
        if not node.evidence_ids:
            node.evidence_ids.append(f"ev_{node.id}")
    engine.register_fragment(trace_fragment)

    results = engine.execute_script("""
consistency on frag_case
traceability on frag_script_trace
""".strip())

    assert len(results) == 2
    assert all(item.passed for item in results)


def test_acql_execute_script_unknown_target_between_valid_queries() -> None:
    """Script should continue evaluation when one query target is unknown."""
    engine = _seed_acql()

    results = engine.execute_script("""
consistency on frag_case
soundness on missing_case
coverage on frag_case
""".strip())

    assert [item.query_type for item in results] == [
        "consistency",
        "soundness",
        "coverage",
    ]
    assert results[0].passed is True
    assert results[1].passed is False
    assert "Unknown target" in results[1].summary


def test_acql_execute_script_dependencies_mixed_fragment_and_case_targets() -> None:
    """Dependencies script should pass for fragment and fail for case target."""
    engine = _seed_acql()
    builder = AssuranceCaseBuilder(title="Dependency Case")
    builder.add_goal("Goal", node_id="g1").set_as_root()
    case = builder.build()
    engine.register_case(case)

    results = engine.execute_script(f"""
dependencies on frag_case
dependencies on {case.case_id}
""".strip())

    assert [result.query_type for result in results] == ["dependencies", "dependencies"]
    assert results[0].passed is True
    assert results[1].passed is False
    assert "requires a fragment target" in results[1].summary


def test_acql_execute_script_defeaters_then_traceability_on_supported_case() -> None:
    """Defeaters and traceability should both pass for supported assumptions."""
    builder = AssuranceCaseBuilder(title="Supported Script Case")
    builder.add_goal("Goal", node_id="g1").set_as_root()
    assumption = GSNAssumption("Assume reviewed supplier", node_id="a1")
    assumption.evidence_ids.append("ev_assumption")
    case = builder.build()
    case.add_node(assumption)

    for node in case.nodes.values():
        if not node.evidence_ids:
            node.evidence_ids.append(f"ev_{node.id}")

    engine = ACQLEngine()
    engine.register_case(case)

    results = engine.execute_script(f"""
defeaters on {case.case_id}
traceability on {case.case_id}
""".strip())

    assert [result.query_type for result in results] == ["defeaters", "traceability"]
    assert all(result.passed for result in results)
