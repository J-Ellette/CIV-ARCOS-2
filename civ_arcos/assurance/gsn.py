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
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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


class GSNGoal(GSNNode):
    def __init__(self, statement: str, node_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(
            id=node_id or str(uuid.uuid4()),
            node_type=GSNNodeType.GOAL,
            statement=statement,
            **kwargs,
        )


class GSNStrategy(GSNNode):
    def __init__(self, statement: str, node_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(
            id=node_id or str(uuid.uuid4()),
            node_type=GSNNodeType.STRATEGY,
            statement=statement,
            **kwargs,
        )


class GSNSolution(GSNNode):
    def __init__(self, statement: str, node_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(
            id=node_id or str(uuid.uuid4()),
            node_type=GSNNodeType.SOLUTION,
            statement=statement,
            **kwargs,
        )


class GSNContext(GSNNode):
    def __init__(self, statement: str, node_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(
            id=node_id or str(uuid.uuid4()),
            node_type=GSNNodeType.CONTEXT,
            statement=statement,
            **kwargs,
        )


class GSNAssumption(GSNNode):
    def __init__(self, statement: str, node_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(
            id=node_id or str(uuid.uuid4()),
            node_type=GSNNodeType.ASSUMPTION,
            statement=statement,
            **kwargs,
        )


class GSNJustification(GSNNode):
    def __init__(self, statement: str, node_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(
            id=node_id or str(uuid.uuid4()),
            node_type=GSNNodeType.JUSTIFICATION,
            statement=statement,
            **kwargs,
        )
