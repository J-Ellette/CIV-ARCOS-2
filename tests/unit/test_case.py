"""Unit tests for AssuranceCase and AssuranceCaseBuilder."""
import pytest
from civ_arcos.assurance.case import AssuranceCase, AssuranceCaseBuilder
from civ_arcos.assurance.gsn import GSNGoal, GSNStrategy, GSNSolution, GSNNodeType


def _build_simple_case() -> AssuranceCase:
    return (
        AssuranceCaseBuilder(title="Test Case")
        .add_goal("The system is safe", node_id="g1")
        .set_as_root()
        .add_strategy("Argue via testing", node_id="s1")
        .link_to_parent("g1")
        .add_solution("All tests pass", node_id="sn1")
        .link_to_parent("s1")
        .build()
    )


def test_case_builder_creates_case():
    case = _build_simple_case()
    assert case.title == "Test Case"
    assert len(case.nodes) == 3


def test_case_root_goal_set():
    case = _build_simple_case()
    assert case.root_goal_id == "g1"
    root = case.get_root_goal()
    assert root is not None
    assert root.statement == "The system is safe"


def test_case_link_nodes():
    case = _build_simple_case()
    g1 = case.get_node("g1")
    assert "s1" in g1.children


def test_case_traverse_dfs():
    case = _build_simple_case()
    nodes = case.traverse()
    ids = [n.id for n in nodes]
    assert "g1" in ids
    assert "s1" in ids
    assert "sn1" in ids


def test_case_validate_valid():
    case = _build_simple_case()
    result = case.validate()
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_case_validate_no_root():
    case = AssuranceCase()
    case.add_node(GSNGoal("A goal", node_id="g1"))
    result = case.validate()
    assert result["valid"] is False
    assert any("root" in e.lower() for e in result["errors"])


def test_case_to_dict_and_from_dict():
    case = _build_simple_case()
    d = case.to_dict()
    restored = AssuranceCase.from_dict(d)
    assert restored.case_id == case.case_id
    assert restored.title == "Test Case"
    assert len(restored.nodes) == 3


def test_case_link_evidence():
    case = _build_simple_case()
    case.link_evidence("g1", "ev-abc")
    g1 = case.get_node("g1")
    assert "ev-abc" in g1.evidence_ids
