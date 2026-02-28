"""Graph database emulation with Neo4j-style API."""
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


@dataclass
class GraphNode:
    id: str
    labels: List[str]
    properties: Dict[str, Any]
    created_at: str
    updated_at: str


@dataclass
class GraphRelationship:
    id: str
    type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any]
    created_at: str


class EvidenceGraph:
    """In-memory graph database with JSON persistence."""

    def __init__(self) -> None:
        self._nodes: Dict[str, GraphNode] = {}
        self._relationships: Dict[str, GraphRelationship] = {}
        # Indexes for O(1) lookups
        self._label_index: Dict[str, Set[str]] = {}          # label -> set of node IDs
        self._src_rel_index: Dict[str, Set[str]] = {}         # source node ID -> set of rel IDs
        self._tgt_rel_index: Dict[str, Set[str]] = {}         # target node ID -> set of rel IDs

    def add_node(self, labels: List[str], properties: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc).isoformat()
        node_id = str(uuid.uuid4())
        self._nodes[node_id] = GraphNode(
            id=node_id, labels=labels, properties=properties,
            created_at=now, updated_at=now
        )
        for label in labels:
            self._label_index.setdefault(label, set()).add(node_id)
        return node_id

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def add_relationship(self, rel_type: str, source_id: str, target_id: str, properties: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc).isoformat()
        rel_id = str(uuid.uuid4())
        self._relationships[rel_id] = GraphRelationship(
            id=rel_id, type=rel_type, source_id=source_id, target_id=target_id,
            properties=properties, created_at=now
        )
        self._src_rel_index.setdefault(source_id, set()).add(rel_id)
        self._tgt_rel_index.setdefault(target_id, set()).add(rel_id)
        return rel_id

    def get_relationships(self, node_id: str) -> List[GraphRelationship]:
        rel_ids = (
            self._src_rel_index.get(node_id, set())
            | self._tgt_rel_index.get(node_id, set())
        )
        return [self._relationships[rid] for rid in rel_ids]

    def find_nodes_by_label(self, label: str) -> List[GraphNode]:
        return [self._nodes[nid] for nid in self._label_index.get(label, set())]

    def find_nodes_by_property(self, key: str, value: Any) -> List[GraphNode]:
        return [n for n in self._nodes.values() if n.properties.get(key) == value]

    def get_neighbors(self, node_id: str) -> List[GraphNode]:
        neighbors = []
        for rid in self._src_rel_index.get(node_id, set()):
            r = self._relationships[rid]
            if r.target_id in self._nodes:
                neighbors.append(self._nodes[r.target_id])
        for rid in self._tgt_rel_index.get(node_id, set()):
            r = self._relationships[rid]
            if r.source_id in self._nodes:
                neighbors.append(self._nodes[r.source_id])
        return neighbors

    def save(self, path: str) -> None:
        data = {
            "nodes": {k: {"id": v.id, "labels": v.labels, "properties": v.properties,
                          "created_at": v.created_at, "updated_at": v.updated_at}
                     for k, v in self._nodes.items()},
            "relationships": {k: {"id": v.id, "type": v.type, "source_id": v.source_id,
                                  "target_id": v.target_id, "properties": v.properties,
                                  "created_at": v.created_at}
                              for k, v in self._relationships.items()}
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> None:
        with open(path, "r") as f:
            data = json.load(f)
        self._nodes = {}
        self._relationships = {}
        self._label_index = {}
        self._src_rel_index = {}
        self._tgt_rel_index = {}
        for k, v in data.get("nodes", {}).items():
            node = GraphNode(**v)
            self._nodes[k] = node
            for label in node.labels:
                self._label_index.setdefault(label, set()).add(k)
        for k, v in data.get("relationships", {}).items():
            rel = GraphRelationship(**v)
            self._relationships[k] = rel
            self._src_rel_index.setdefault(rel.source_id, set()).add(k)
            self._tgt_rel_index.setdefault(rel.target_id, set()).add(k)
