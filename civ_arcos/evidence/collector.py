"""Evidence collection with provenance tracking."""
import hashlib
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from civ_arcos.storage.graph import EvidenceGraph


@dataclass
class Evidence:
    """Immutable evidence record with cryptographic checksum."""
    id: str
    type: str
    source: str
    timestamp: str
    data: Dict[str, Any]
    provenance: Dict[str, Any]
    checksum: str = field(default="")

    def __post_init__(self) -> None:
        if not self.checksum:
            self.checksum = hashlib.sha256(
                json.dumps(self.data, sort_keys=True).encode()
            ).hexdigest()


class EvidenceCollector(ABC):
    """Abstract base class for evidence collectors."""

    @abstractmethod
    def collect(self, *args: Any, **kwargs: Any) -> List[Evidence]:
        """Collect evidence from a source."""

    @abstractmethod
    def collect_from_github(self, repo_url: str, commit_hash: str) -> List[Evidence]:
        """Collect evidence from GitHub."""

    @abstractmethod
    def collect_from_ci(self, build_id: str) -> List[Evidence]:
        """Collect evidence from CI system."""

    @abstractmethod
    def collect_from_security_tools(self, scan_results: Dict[str, Any]) -> List[Evidence]:
        """Collect evidence from security tools."""


class EvidenceStore:
    """Stores and retrieves evidence using graph database with chain linking."""

    def __init__(self, graph: Optional[EvidenceGraph] = None) -> None:
        self._graph = graph or EvidenceGraph()
        self._last_hash = "0" * 64  # genesis hash

    def store_evidence(self, evidence: Evidence) -> str:
        props = {
            "evidence_id": evidence.id,
            "type": evidence.type,
            "source": evidence.source,
            "timestamp": evidence.timestamp,
            "data": json.dumps(evidence.data),
            "provenance": json.dumps(evidence.provenance),
            "checksum": evidence.checksum,
            "previous_hash": self._last_hash,
        }
        node_id = self._graph.add_node(["Evidence", evidence.type], props)
        self._last_hash = evidence.checksum
        return node_id

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        nodes = self._graph.find_nodes_by_property("evidence_id", evidence_id)
        if not nodes:
            return None
        return self._node_to_evidence(nodes[0].properties)

    def list_evidence(self) -> List[Evidence]:
        nodes = self._graph.find_nodes_by_label("Evidence")
        return [self._node_to_evidence(n.properties) for n in nodes]

    def verify_chain(self) -> bool:
        """Verify evidence chain integrity by checking checksums."""
        nodes = sorted(
            self._graph.find_nodes_by_label("Evidence"),
            key=lambda n: n.properties.get("timestamp", "")
        )
        for node in nodes:
            props = node.properties
            data = json.loads(props.get("data", "{}"))
            expected = hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()
            if props.get("checksum") != expected:
                return False
        return True

    @staticmethod
    def _node_to_evidence(props: Dict[str, Any]) -> Evidence:
        return Evidence(
            id=props["evidence_id"],
            type=props["type"],
            source=props["source"],
            timestamp=props["timestamp"],
            data=json.loads(props.get("data", "{}")),
            provenance=json.loads(props.get("provenance", "{}")),
            checksum=props.get("checksum", ""),
        )
