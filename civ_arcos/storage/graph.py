"""Graph database emulation with Neo4j-style API."""

import json
import os
import threading
import uuid
from dataclasses import dataclass
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
        self._lock = threading.RLock()
        # Indexes for O(1) lookups
        self._label_index: Dict[str, Set[str]] = {}  # label -> set of node IDs
        self._src_rel_index: Dict[str, Set[str]] = (
            {}
        )  # source node ID -> set of rel IDs
        self._tgt_rel_index: Dict[str, Set[str]] = (
            {}
        )  # target node ID -> set of rel IDs

    def add_node(self, labels: List[str], properties: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc).isoformat()
        node_id = str(uuid.uuid4())
        with self._lock:
            self._nodes[node_id] = GraphNode(
                id=node_id,
                labels=labels,
                properties=properties,
                created_at=now,
                updated_at=now,
            )
            for label in labels:
                self._label_index.setdefault(label, set()).add(node_id)
        return node_id

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        with self._lock:
            return self._nodes.get(node_id)

    def add_relationship(
        self, rel_type: str, source_id: str, target_id: str, properties: Dict[str, Any]
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        rel_id = str(uuid.uuid4())
        with self._lock:
            self._relationships[rel_id] = GraphRelationship(
                id=rel_id,
                type=rel_type,
                source_id=source_id,
                target_id=target_id,
                properties=properties,
                created_at=now,
            )
            self._src_rel_index.setdefault(source_id, set()).add(rel_id)
            self._tgt_rel_index.setdefault(target_id, set()).add(rel_id)
        return rel_id

    def get_relationships(self, node_id: str) -> List[GraphRelationship]:
        with self._lock:
            rel_ids = self._src_rel_index.get(node_id, set()) | self._tgt_rel_index.get(
                node_id, set()
            )
            return [self._relationships[rid] for rid in rel_ids]

    def find_nodes_by_label(self, label: str) -> List[GraphNode]:
        with self._lock:
            return [self._nodes[nid] for nid in self._label_index.get(label, set())]

    def find_nodes_by_property(self, key: str, value: Any) -> List[GraphNode]:
        with self._lock:
            return [n for n in self._nodes.values() if n.properties.get(key) == value]

    def get_neighbors(self, node_id: str) -> List[GraphNode]:
        with self._lock:
            neighbors = []
            for rid in self._src_rel_index.get(node_id, set()):
                rel = self._relationships[rid]
                if rel.target_id in self._nodes:
                    neighbors.append(self._nodes[rel.target_id])
            for rid in self._tgt_rel_index.get(node_id, set()):
                rel = self._relationships[rid]
                if rel.source_id in self._nodes:
                    neighbors.append(self._nodes[rel.source_id])
            return neighbors

    def save(self, path: str) -> None:
        with self._lock:
            data = {
                "nodes": {
                    key: {
                        "id": value.id,
                        "labels": value.labels,
                        "properties": value.properties,
                        "created_at": value.created_at,
                        "updated_at": value.updated_at,
                    }
                    for key, value in self._nodes.items()
                },
                "relationships": {
                    key: {
                        "id": value.id,
                        "type": value.type,
                        "source_id": value.source_id,
                        "target_id": value.target_id,
                        "properties": value.properties,
                        "created_at": value.created_at,
                    }
                    for key, value in self._relationships.items()
                },
            }

        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as file_obj:
            json.dump(data, file_obj, indent=2)
        os.replace(tmp_path, path)

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)

        with self._lock:
            self._nodes = {}
            self._relationships = {}
            self._label_index = {}
            self._src_rel_index = {}
            self._tgt_rel_index = {}
            for key, value in data.get("nodes", {}).items():
                node = GraphNode(**value)
                self._nodes[key] = node
                for label in node.labels:
                    self._label_index.setdefault(label, set()).add(key)
            for key, value in data.get("relationships", {}).items():
                relationship = GraphRelationship(**value)
                self._relationships[key] = relationship
                self._src_rel_index.setdefault(relationship.source_id, set()).add(key)
                self._tgt_rel_index.setdefault(relationship.target_id, set()).add(key)
