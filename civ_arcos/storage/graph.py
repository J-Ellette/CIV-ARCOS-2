"""Graph database emulation with Neo4j-style API."""
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


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

    def add_node(self, labels: List[str], properties: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc).isoformat()
        node_id = str(uuid.uuid4())
        self._nodes[node_id] = GraphNode(
            id=node_id, labels=labels, properties=properties,
            created_at=now, updated_at=now
        )
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
        return rel_id

    def get_relationships(self, node_id: str) -> List[GraphRelationship]:
        return [r for r in self._relationships.values()
                if r.source_id == node_id or r.target_id == node_id]

    def find_nodes_by_label(self, label: str) -> List[GraphNode]:
        return [n for n in self._nodes.values() if label in n.labels]

    def find_nodes_by_property(self, key: str, value: Any) -> List[GraphNode]:
        return [n for n in self._nodes.values() if n.properties.get(key) == value]

    def get_neighbors(self, node_id: str) -> List[GraphNode]:
        neighbors = []
        for r in self._relationships.values():
            if r.source_id == node_id and r.target_id in self._nodes:
                neighbors.append(self._nodes[r.target_id])
            elif r.target_id == node_id and r.source_id in self._nodes:
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
        self._nodes = {k: GraphNode(**v) for k, v in data.get("nodes", {}).items()}
        self._relationships = {k: GraphRelationship(**v) for k, v in data.get("relationships", {}).items()}
