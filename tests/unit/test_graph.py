"""Tests for graph database."""
import pytest
from civ_arcos.storage.graph import EvidenceGraph, GraphNode, GraphRelationship


def test_add_and_get_node():
    g = EvidenceGraph()
    nid = g.add_node(["Person"], {"name": "Alice"})
    node = g.get_node(nid)
    assert node is not None
    assert node.id == nid
    assert "Person" in node.labels
    assert node.properties["name"] == "Alice"


def test_add_relationship():
    g = EvidenceGraph()
    a = g.add_node(["A"], {"x": 1})
    b = g.add_node(["B"], {"y": 2})
    rid = g.add_relationship("KNOWS", a, b, {"since": 2020})
    rels = g.get_relationships(a)
    assert len(rels) == 1
    assert rels[0].type == "KNOWS"
    assert rels[0].id == rid


def test_find_nodes_by_label():
    g = EvidenceGraph()
    g.add_node(["Evidence"], {"v": 1})
    g.add_node(["Evidence"], {"v": 2})
    g.add_node(["Other"], {"v": 3})
    nodes = g.find_nodes_by_label("Evidence")
    assert len(nodes) == 2


def test_find_nodes_by_property():
    g = EvidenceGraph()
    g.add_node(["X"], {"color": "red"})
    g.add_node(["X"], {"color": "blue"})
    found = g.find_nodes_by_property("color", "red")
    assert len(found) == 1
    assert found[0].properties["color"] == "red"


def test_get_neighbors():
    g = EvidenceGraph()
    a = g.add_node(["A"], {})
    b = g.add_node(["B"], {})
    c = g.add_node(["C"], {})
    g.add_relationship("EDGE", a, b, {})
    g.add_relationship("EDGE", a, c, {})
    neighbors = g.get_neighbors(a)
    ids = {n.id for n in neighbors}
    assert b in ids
    assert c in ids


def test_save_and_load(tmp_path):
    g = EvidenceGraph()
    nid = g.add_node(["Test"], {"key": "value"})
    path = str(tmp_path / "graph.json")
    g.save(path)
    g2 = EvidenceGraph()
    g2.load(path)
    node = g2.get_node(nid)
    assert node is not None
    assert node.properties["key"] == "value"
