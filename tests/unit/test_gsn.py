"""Unit tests for GSN node types and classes."""
import pytest
from civ_arcos.assurance.gsn import (
    GSNNodeType, GSNNode, GSNGoal, GSNStrategy, GSNSolution,
    GSNContext, GSNAssumption, GSNJustification,
)


def test_gsn_goal_creation():
    node = GSNGoal("The system is safe")
    assert node.node_type == GSNNodeType.GOAL
    assert node.statement == "The system is safe"
    assert node.id is not None


def test_gsn_strategy_creation():
    node = GSNStrategy("Argue by testing")
    assert node.node_type == GSNNodeType.STRATEGY


def test_gsn_solution_creation():
    node = GSNSolution("Test results evidence")
    assert node.node_type == GSNNodeType.SOLUTION


def test_add_child_and_evidence():
    node = GSNGoal("Root goal")
    node.add_child("child-001")
    node.add_evidence("ev-001")
    assert "child-001" in node.children
    assert "ev-001" in node.evidence_ids


def test_add_child_no_duplicates():
    node = GSNGoal("Root goal")
    node.add_child("child-001")
    node.add_child("child-001")
    assert node.children.count("child-001") == 1


def test_to_dict_and_from_dict():
    node = GSNGoal("Test goal", node_id="g1")
    node.add_child("g2")
    d = node.to_dict()
    restored = GSNNode.from_dict(d)
    assert restored.id == "g1"
    assert restored.node_type == GSNNodeType.GOAL
    assert "g2" in restored.children


def test_node_type_enum_values():
    assert GSNNodeType.GOAL.value == "goal"
    assert GSNNodeType.STRATEGY.value == "strategy"
    assert GSNNodeType.SOLUTION.value == "solution"
