"""Cross-tool dependency tracking utilities (CAID-tools style baseline)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Set, Tuple


class ResourceType(str, Enum):
    """Supported resource categories for dependency tracking."""

    FILE = "file"
    DIRECTORY = "directory"
    MODEL = "model"
    TEST = "test"
    EVIDENCE = "evidence"


class DependencyType(str, Enum):
    """Supported edge types between resources."""

    REQUIRES = "requires"
    IMPLEMENTS = "implements"
    TESTS = "tests"
    VALIDATES = "validates"


@dataclass
class Resource:
    """A tracked resource node in the dependency graph."""

    resource_id: str
    resource_type: ResourceType
    name: str
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class Dependency:
    """A directed dependency edge between two resources."""

    source_id: str
    target_id: str
    dependency_type: DependencyType


class DependencyTracker:
    """Register resources, link dependencies, and analyze impact."""

    def __init__(self) -> None:
        """Initialize in-memory registries for resources and dependencies."""
        self._resources: Dict[str, Resource] = {}
        self._dependencies: List[Dependency] = []
        self._listeners: List[Callable[[Resource], None]] = []

    def register_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        name: str,
        metadata: Dict[str, object] | None = None,
    ) -> Resource:
        """Create or update a tracked resource."""
        resource = Resource(
            resource_id=resource_id,
            resource_type=resource_type,
            name=name,
            metadata=metadata or {},
        )
        self._resources[resource_id] = resource
        return resource

    def get_resource(self, resource_id: str) -> Resource | None:
        """Fetch a tracked resource by id when present."""
        return self._resources.get(resource_id)

    def list_resources(self) -> List[Resource]:
        """List all resources in deterministic id order."""
        return [self._resources[key] for key in sorted(self._resources.keys())]

    def link_dependency(
        self,
        source_id: str,
        target_id: str,
        dependency_type: DependencyType,
    ) -> Dependency:
        """Create a dependency edge between registered resources."""
        if source_id not in self._resources:
            raise ValueError(f"Unknown source resource: {source_id}")
        if target_id not in self._resources:
            raise ValueError(f"Unknown target resource: {target_id}")

        edge = Dependency(
            source_id=source_id,
            target_id=target_id,
            dependency_type=dependency_type,
        )

        exists = any(
            dependency.source_id == edge.source_id
            and dependency.target_id == edge.target_id
            and dependency.dependency_type == edge.dependency_type
            for dependency in self._dependencies
        )
        if not exists:
            self._dependencies.append(edge)
        return edge

    def list_dependencies(self) -> List[Dependency]:
        """Return all dependency edges in insertion order."""
        return list(self._dependencies)

    def add_update_listener(self, callback: Callable[[Resource], None]) -> None:
        """Register a callback triggered on resource update notifications."""
        self._listeners.append(callback)

    def notify_resource_update(self, resource_id: str) -> None:
        """Notify listeners that a specific resource has changed."""
        resource = self._resources.get(resource_id)
        if resource is None:
            raise ValueError(f"Unknown resource for update: {resource_id}")

        for callback in self._listeners:
            callback(resource)

    def impact_analysis(self, resource_id: str) -> Dict[str, object]:
        """Compute transitive downstream impact for a changed resource."""
        if resource_id not in self._resources:
            raise ValueError(f"Unknown resource for impact analysis: {resource_id}")

        adjacency: Dict[str, List[Tuple[str, DependencyType]]] = {}
        for dependency in self._dependencies:
            adjacency.setdefault(dependency.source_id, []).append(
                (dependency.target_id, dependency.dependency_type)
            )

        impacted: Set[str] = set()
        traversed_edges: List[Dict[str, str]] = []
        queue: List[str] = [resource_id]

        while queue:
            current = queue.pop(0)
            for target_id, edge_type in adjacency.get(current, []):
                traversed_edges.append(
                    {
                        "source_id": current,
                        "target_id": target_id,
                        "dependency_type": edge_type.value,
                    }
                )
                if target_id not in impacted:
                    impacted.add(target_id)
                    queue.append(target_id)

        impacted_resources = [
            {
                "resource_id": rid,
                "name": self._resources[rid].name,
                "resource_type": self._resources[rid].resource_type.value,
            }
            for rid in sorted(impacted)
        ]

        return {
            "resource_id": resource_id,
            "impacted_count": len(impacted_resources),
            "impacted_resources": impacted_resources,
            "dependency_path": traversed_edges,
        }
