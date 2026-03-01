"""Unit tests for CLARISSA-style assurance reasoning engine."""

from civ_arcos.assurance.case import AssuranceCaseBuilder
from civ_arcos.assurance.fragments import FragmentLibrary
from civ_arcos.assurance.gsn import GSNAssumption
from civ_arcos.assurance.reasoning import ArgumentTheory, ReasoningEngine


def _quality_case():
    """Create a structurally valid assurance case with baseline evidence."""
    library = FragmentLibrary()
    fragment = library.create_fragment(
        pattern="component_quality",
        fragment_id="frag_reason",
        title="Reasoning Fragment",
        description="Reasoning baseline",
        component_name="api",
    )
    return fragment.case


def test_reason_about_case_returns_expected_shape() -> None:
    """Reasoning output includes theories, defeaters, and confidence fields."""
    engine = ReasoningEngine()
    result = engine.reason_about_case(_quality_case(), context={})

    assert "applicable_theories" in result
    assert "active_defeaters" in result
    assert "confidence_score" in result
    assert 0.0 <= result["confidence_score"] <= 1.0


def test_reasoning_marks_indefeasible_false_with_assumption_defeater() -> None:
    """Uncovered assumptions should activate defeaters and reduce certainty."""
    builder = AssuranceCaseBuilder(title="Assumption Case")
    builder.add_goal("System is safe", node_id="g1").set_as_root()
    builder.add_context("Operational context", node_id="c1").link_to_parent("g1")
    # Add an unsupported assumption to trigger the defeater path.
    case = builder.build()
    case.add_node(GSNAssumption("Assume trusted environment", node_id="a1"))

    engine = ReasoningEngine()
    result = engine.reason_about_case(case, context={})

    assert result["indefeasible"] is False
    defeater_ids = [item["defeater_id"] for item in result["active_defeaters"]]
    assert "uncovered_assumptions" in defeater_ids


def test_register_theory_influences_applicable_theories() -> None:
    """Custom theory registration should affect reasoning evaluation."""
    engine = ReasoningEngine()

    custom = ArgumentTheory(
        theory_id="context_release_gate",
        premise="Release gate approved in context",
        conclusion="Release readiness argument is strengthened",
        weight=0.10,
        evaluator=lambda _case, ctx: bool(ctx.get("release_gate_approved", False)),
    )
    engine.register_theory(custom)

    result = engine.reason_about_case(
        _quality_case(),
        context={"release_gate_approved": True},
    )

    theory_ids = [item["theory_id"] for item in result["applicable_theories"]]
    assert "context_release_gate" in theory_ids


def test_estimate_risk_elevates_with_critical_vulnerabilities() -> None:
    """Risk estimate should increase when critical vulnerabilities are present."""
    engine = ReasoningEngine()
    case = _quality_case()

    baseline = engine.estimate_risk(case, context={})
    stressed = engine.estimate_risk(
        case,
        context={"critical_vulnerabilities": 2},
    )

    assert stressed["risk_score"] >= baseline["risk_score"]
    assert stressed["risk_level"] in {"low", "medium", "high", "critical"}