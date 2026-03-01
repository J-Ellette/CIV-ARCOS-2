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


def test_reasoning_recommends_evidence_when_case_has_no_links() -> None:
    """Recommendations should include evidence coverage guidance when needed."""
    builder = AssuranceCaseBuilder(title="Sparse Case")
    builder.add_goal("Service quality is acceptable", node_id="g1").set_as_root()
    sparse_case = builder.build()

    engine = ReasoningEngine()
    result = engine.reason_about_case(sparse_case, context={})

    joined = " ".join(result["recommendations"]).lower()
    assert "evidence" in joined


def test_estimate_risk_reaches_high_or_critical_for_invalid_case() -> None:
    """Invalid cases with critical vulnerabilities should elevate risk level."""
    invalid_case = AssuranceCaseBuilder(title="Invalid").build()

    engine = ReasoningEngine()
    result = engine.estimate_risk(
        invalid_case,
        context={"critical_vulnerabilities": 2},
    )

    assert result["risk_level"] in {"high", "critical"}
    assert result["risk_score"] >= 0.50


def test_reasoning_can_become_indefeasible_for_fully_evidenced_case() -> None:
    """A fully evidenced valid case should reach indefeasible true."""
    case = _quality_case()
    for node in case.nodes.values():
        if not node.evidence_ids:
            node.evidence_ids.append(f"ev_{node.id}")

    engine = ReasoningEngine()
    result = engine.reason_about_case(case, context={})

    assert result["indefeasible"] is True
    assert result["confidence_score"] >= 0.70


def test_estimate_risk_reports_low_for_high_confidence_case() -> None:
    """Risk should fall to low when confidence is high enough."""
    case = _quality_case()
    for node in case.nodes.values():
        if not node.evidence_ids:
            node.evidence_ids.append(f"ev_{node.id}")

    engine = ReasoningEngine()
    risk = engine.estimate_risk(case, context={})

    assert risk["risk_level"] == "low"
    assert risk["risk_score"] < 0.25


def test_reasoning_adds_theory_activation_recommendation_when_none_apply() -> None:
    """No applicable theories should trigger a theory-activation recommendation."""
    invalid_case = AssuranceCaseBuilder(title="No Theory Case").build()

    engine = ReasoningEngine()
    result = engine.reason_about_case(invalid_case, context={})

    joined = " ".join(result["recommendations"])
    assert "Collect additional evidence to activate theories" in joined


def test_reasoning_reports_multiple_active_defeaters_when_applicable() -> None:
    """Multiple simultaneous defeaters should all be surfaced."""
    builder = AssuranceCaseBuilder(title="Multi Defeater")
    builder.add_goal("Top goal", node_id="g1").set_as_root()
    case = builder.build()
    case.add_node(GSNAssumption("Assume secure runtime", node_id="a1"))

    engine = ReasoningEngine()
    result = engine.reason_about_case(
        case,
        context={"critical_vulnerabilities": 1},
    )

    defeaters = {item["defeater_id"] for item in result["active_defeaters"]}
    assert "uncovered_assumptions" in defeaters
    assert "critical_vulnerabilities" in defeaters


def test_reasoning_recommendations_include_all_active_defeater_guidance() -> None:
    """Recommendations should include guidance for each active defeater."""
    builder = AssuranceCaseBuilder(title="Recommendation Case")
    builder.add_goal("Top goal", node_id="g1").set_as_root()
    case = builder.build()
    case.add_node(GSNAssumption("Assume trusted supplier", node_id="a1"))

    engine = ReasoningEngine()
    result = engine.reason_about_case(
        case,
        context={"critical_vulnerabilities": 2},
    )

    recommendations = " ".join(result["recommendations"])
    assert "Resolve assurance-case structural errors" in recommendations
    assert "Justify or evidence all assumption nodes" in recommendations
    assert "Mitigate critical vulnerabilities before release" in recommendations


def test_reasoning_confidence_is_capped_at_one_with_high_weight_theory() -> None:
    """Confidence score should cap at 1.0 even with excessive positive weight."""
    case = _quality_case()
    engine = ReasoningEngine()
    engine.register_theory(
        ArgumentTheory(
            theory_id="high_weight",
            premise="Always true",
            conclusion="Strong confidence",
            weight=5.0,
            evaluator=lambda _case, _ctx: True,
        )
    )

    result = engine.reason_about_case(case, context={})

    assert result["confidence_score"] == 1.0


def test_reasoning_recommendations_fallback_for_strong_case() -> None:
    """No-remediation fallback recommendation should appear for strong cases."""
    case = _quality_case()
    for node in case.nodes.values():
        if not node.evidence_ids:
            node.evidence_ids.append(f"ev_{node.id}")

    engine = ReasoningEngine()
    result = engine.reason_about_case(case, context={})

    assert (
        "Maintain current evidence quality and monitor drift."
        in result["recommendations"]
    )


def test_estimate_risk_defeater_count_matches_reasoning_output() -> None:
    """Risk output defeater count should align with direct reasoning output."""
    builder = AssuranceCaseBuilder(title="Count Case")
    builder.add_goal("Goal", node_id="g1").set_as_root()
    case = builder.build()
    case.add_node(GSNAssumption("Assume trusted third-party", node_id="a1"))

    engine = ReasoningEngine()
    reasoning = engine.reason_about_case(
        case,
        context={"critical_vulnerabilities": 1},
    )
    risk = engine.estimate_risk(
        case,
        context={"critical_vulnerabilities": 1},
    )

    assert risk["defeater_count"] == len(reasoning["active_defeaters"])
