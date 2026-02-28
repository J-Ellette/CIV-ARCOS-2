"""Goal Structuring Notation (GSN) node types and classes."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class GSNNodeType(Enum):
    GOAL = "goal"
    STRATEGY = "strategy"
    SOLUTION = "solution"
    CONTEXT = "context"
    ASSUMPTION = "assumption"
    JUSTIFICATION = "justification"


@dataclass
class GSNNode:
    id: str
    node_type: GSNNodeType
    statement: str
    properties: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def add_child(self, node_id: str) -> None:
        if node_id not in self.children:
            self.children.append(node_id)
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_evidence(self, evidence_id: str) -> None:
        if evidence_id not in self.evidence_ids:
            self.evidence_ids.append(evidence_id)
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type.value,
            "statement": self.statement,
            "properties": self.properties,
            "children": self.children,
            "evidence_ids": self.evidence_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GSNNode":
        d = dict(d)
        d["node_type"] = GSNNodeType(d["node_type"])
        return cls(**d)


class _GSNTypedNode(GSNNode):
    """Private intermediate class that injects a fixed node type.

    Each concrete subclass declares a class-level ``_NODE_TYPE`` attribute;
    this single ``__init__`` uses it so the duplicated body does not need to
    be repeated in every subclass.
    """

    #: Subclasses must set this to the :class:`GSNNodeType` value that
    #: identifies the concrete node kind (e.g. ``GSNNodeType.GOAL``).
    _NODE_TYPE: GSNNodeType

    def __init__(
        self, statement: str, node_id: Optional[str] = None, **kwargs: Any
    ) -> None:
        super().__init__(
            id=node_id or str(uuid.uuid4()),
            node_type=self.__class__._NODE_TYPE,
            statement=statement,
            **kwargs,
        )


class GSNGoal(_GSNTypedNode):
    _NODE_TYPE = GSNNodeType.GOAL


class GSNStrategy(_GSNTypedNode):
    _NODE_TYPE = GSNNodeType.STRATEGY


class GSNSolution(_GSNTypedNode):
    _NODE_TYPE = GSNNodeType.SOLUTION


class GSNContext(_GSNTypedNode):
    _NODE_TYPE = GSNNodeType.CONTEXT


class GSNAssumption(_GSNTypedNode):
    _NODE_TYPE = GSNNodeType.ASSUMPTION


class GSNJustification(_GSNTypedNode):
    _NODE_TYPE = GSNNodeType.JUSTIFICATION
