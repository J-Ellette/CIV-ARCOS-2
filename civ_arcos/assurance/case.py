"""Assurance case builder and case model."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from civ_arcos.assurance.gsn import (
    GSNNode, GSNNodeType, GSNGoal, GSNStrategy, GSNSolution, GSNContext,
    GSNAssumption, GSNJustification,
)

_TYPE_MAP = {
    GSNNodeType.GOAL: GSNGoal,
    GSNNodeType.STRATEGY: GSNStrategy,
    GSNNodeType.SOLUTION: GSNSolution,
    GSNNodeType.CONTEXT: GSNContext,
    GSNNodeType.ASSUMPTION: GSNAssumption,
    GSNNodeType.JUSTIFICATION: GSNJustification,
}


class AssuranceCase:
    """An assurance case backed by a GSN graph."""

    def __init__(self, case_id: Optional[str] = None, title: str = "",
                 description: str = "", project_type: str = "general") -> None:
        self.case_id: str = case_id or str(uuid.uuid4())
        self.title: str = title
        self.description: str = description
        self.project_type: str = project_type
        self.nodes: Dict[str, GSNNode] = {}
        self.root_goal_id: Optional[str] = None
        self.created_at: str = datetime.now(timezone.utc).isoformat()

    def add_node(self, node: GSNNode) -> None:
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[GSNNode]:
        return self.nodes.get(node_id)

    def set_root(self, node_id: str) -> None:
        self.root_goal_id = node_id

    def get_root_goal(self) -> Optional[GSNNode]:
        return self.nodes.get(self.root_goal_id) if self.root_goal_id else None

    def link_nodes(self, parent_id: str, child_id: str) -> None:
        parent = self.nodes.get(parent_id)
        if parent:
            parent.add_child(child_id)

    def link_evidence(self, node_id: str, evidence_id: str) -> None:
        node = self.nodes.get(node_id)
        if node:
            node.add_evidence(evidence_id)

    def traverse(self, node_id: Optional[str] = None) -> List[GSNNode]:
        """DFS traversal from root (or given node)."""
        start = node_id or self.root_goal_id
        if not start or start not in self.nodes:
            return list(self.nodes.values())

        visited: List[GSNNode] = []
        seen: set = set()

        def _dfs(current_node_id: str) -> None:
            if current_node_id in seen or current_node_id not in self.nodes:
                return
            seen.add(current_node_id)
            node = self.nodes[current_node_id]
            visited.append(node)
            for child_id in node.children:
                _dfs(child_id)

        _dfs(start)
        return visited

    def validate(self) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if not self.root_goal_id:
            errors.append("No root goal set")
        elif self.root_goal_id not in self.nodes:
            errors.append(f"Root goal '{self.root_goal_id}' not found in nodes")

        # Orphan nodes (not reachable from root)
        if self.root_goal_id and self.root_goal_id in self.nodes:
            reachable = {n.id for n in self.traverse()}
            for nid in self.nodes:
                if nid not in reachable:
                    errors.append(f"Orphan node: {nid}")

        # Empty statements
        for nid, node in self.nodes.items():
            if not node.statement.strip():
                errors.append(f"Node '{nid}' has an empty statement")

        # Warnings
        for nid, node in self.nodes.items():
            if not node.evidence_ids:
                warnings.append(f"Node '{nid}' has no evidence linked")
            if node.node_type == GSNNodeType.GOAL and not node.children:
                warnings.append(f"Goal '{nid}' has no supporting strategies or solutions")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "description": self.description,
            "project_type": self.project_type,
            "root_goal_id": self.root_goal_id,
            "created_at": self.created_at,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AssuranceCase":
        case = cls(
            case_id=d.get("case_id"),
            title=d.get("title", ""),
            description=d.get("description", ""),
            project_type=d.get("project_type", "general"),
        )
        case.root_goal_id = d.get("root_goal_id")
        case.created_at = d.get("created_at", case.created_at)
        for node_dict in d.get("nodes", {}).values():
            nd = dict(node_dict)
            node_type = GSNNodeType(nd["node_type"])
            node_cls = _TYPE_MAP.get(node_type, GSNNode)
            if node_cls is GSNNode:
                node = GSNNode.from_dict(nd)
            else:
                node = GSNNode.from_dict(nd)
                node.__class__ = node_cls
            case.nodes[node.id] = node
        return case


class AssuranceCaseBuilder:
    """Fluent builder API for constructing an AssuranceCase."""

    def __init__(self, title: str = "", description: str = "",
                 project_type: str = "general") -> None:
        self._case = AssuranceCase(title=title, description=description,
                                   project_type=project_type)
        self._last_node_id: Optional[str] = None

    def add_goal(self, statement: str, node_id: Optional[str] = None) -> "AssuranceCaseBuilder":
        node = GSNGoal(statement, node_id=node_id)
        self._case.add_node(node)
        self._last_node_id = node.id
        return self

    def add_strategy(self, statement: str, node_id: Optional[str] = None) -> "AssuranceCaseBuilder":
        node = GSNStrategy(statement, node_id=node_id)
        self._case.add_node(node)
        self._last_node_id = node.id
        return self

    def add_solution(self, statement: str, evidence_ids: Optional[List[str]] = None,
                     node_id: Optional[str] = None) -> "AssuranceCaseBuilder":
        node = GSNSolution(statement, node_id=node_id)
        for eid in (evidence_ids or []):
            node.add_evidence(eid)
        self._case.add_node(node)
        self._last_node_id = node.id
        return self

    def add_context(self, statement: str, node_id: Optional[str] = None) -> "AssuranceCaseBuilder":
        node = GSNContext(statement, node_id=node_id)
        self._case.add_node(node)
        self._last_node_id = node.id
        return self

    def set_as_root(self) -> "AssuranceCaseBuilder":
        if self._last_node_id:
            self._case.set_root(self._last_node_id)
        return self

    def link_to_parent(self, parent_id: str) -> "AssuranceCaseBuilder":
        if self._last_node_id:
            self._case.link_nodes(parent_id, self._last_node_id)
        return self

    def merge_nodes_from(self, other_case: AssuranceCase,
                         link_root_to: Optional[str] = None) -> "AssuranceCaseBuilder":
        """Merge all nodes from another AssuranceCase into this builder's case.

        Args:
            other_case: The source case whose nodes will be merged in.
            link_root_to: If set, link the other case's root goal as a child of this node ID.
        """
        for node in other_case.nodes.values():
            self._case.add_node(node)
        if link_root_to and other_case.root_goal_id:
            self._case.link_nodes(link_root_to, other_case.root_goal_id)
        return self

    def build(self) -> AssuranceCase:
        return self._case
