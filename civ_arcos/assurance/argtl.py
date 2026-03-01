"""Argument Transformation Language (ArgTL) minimal execution engine."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

from civ_arcos.assurance.case import AssuranceCase
from civ_arcos.assurance.fragments import AssuranceCaseFragment


class ArgTLOperation(str, Enum):
    """Supported ArgTL operations for fragment orchestration."""

    COMPOSE = "compose"
    LINK = "link"
    VALIDATE = "validate"
    ASSEMBLE = "assemble"


@dataclass
class ArgTLResult:
    """Structured result of a parsed ArgTL operation."""

    operation: str
    success: bool
    detail: Dict[str, object]


class ArgTLEngine:
    """Parse and execute constrained ArgTL scripts over fragments."""

    def __init__(self) -> None:
        self._fragments: Dict[str, AssuranceCaseFragment] = {}

    def register_fragment(self, fragment: AssuranceCaseFragment) -> None:
        """Register a fragment into the in-memory ArgTL workspace."""
        self._fragments[fragment.fragment_id] = fragment

    def get_fragment(self, fragment_id: str) -> AssuranceCaseFragment | None:
        """Return a registered fragment by id when available."""
        return self._fragments.get(fragment_id)

    def execute_script(self, script: str) -> List[ArgTLResult]:
        """Execute newline-delimited ArgTL commands."""
        results: List[ArgTLResult] = []
        for line in script.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            results.append(self.execute_line(stripped))
        return results

    def execute_line(self, line: str) -> ArgTLResult:
        """Execute one ArgTL line and return operation result."""
        tokens = line.split()
        if not tokens:
            return ArgTLResult(
                operation="unknown",
                success=False,
                detail={"error": "Empty operation"},
            )

        op = tokens[0].lower()
        if op == ArgTLOperation.COMPOSE.value:
            return self._execute_compose(line)
        if op == ArgTLOperation.LINK.value:
            return self._execute_link(line)
        if op == ArgTLOperation.VALIDATE.value:
            return self._execute_validate(line)
        if op == ArgTLOperation.ASSEMBLE.value:
            return self._execute_assemble(line)

        return ArgTLResult(
            operation=op,
            success=False,
            detail={"error": f"Unsupported ArgTL operation: {op}"},
        )

    def _execute_compose(self, line: str) -> ArgTLResult:
        """Compose listed fragments into a new fragment id."""
        parts = line.split("->")
        if len(parts) != 2:
            return ArgTLResult(
                operation="compose",
                success=False,
                detail={"error": "Compose syntax: compose a b -> target"},
            )

        left = parts[0].strip().split()
        target = parts[1].strip()
        source_ids = left[1:]
        if len(source_ids) < 2:
            return ArgTLResult(
                operation="compose",
                success=False,
                detail={"error": "Compose requires at least two source fragments"},
            )

        source_fragments = []
        for fragment_id in source_ids:
            fragment = self._fragments.get(fragment_id)
            if fragment is None:
                return ArgTLResult(
                    operation="compose",
                    success=False,
                    detail={"error": f"Unknown fragment: {fragment_id}"},
                )
            source_fragments.append(fragment)

        first_case = copy.deepcopy(source_fragments[0].case)
        for fragment in source_fragments[1:]:
            self._merge_case(first_case, fragment.case)

        composed = AssuranceCaseFragment(
            fragment_id=target,
            title=f"Composed fragment {target}",
            description="Auto-composed via ArgTL compose",
            case=first_case,
            dependencies=source_ids,
        )
        self._fragments[target] = composed

        return ArgTLResult(
            operation="compose",
            success=True,
            detail={
                "target": target,
                "sources": source_ids,
                "node_count": len(composed.case.nodes),
            },
        )

    def _execute_link(self, line: str) -> ArgTLResult:
        """Link two fragments by dependency relation."""
        tokens = line.split()
        if len(tokens) < 4 or tokens[2].lower() != "to":
            return ArgTLResult(
                operation="link",
                success=False,
                detail={"error": "Link syntax: link source to target"},
            )

        source_id = tokens[1]
        target_id = tokens[3]
        source = self._fragments.get(source_id)
        target = self._fragments.get(target_id)
        if source is None or target is None:
            return ArgTLResult(
                operation="link",
                success=False,
                detail={"error": "Both source and target fragments must exist"},
            )

        target.add_dependency(source.fragment_id)
        return ArgTLResult(
            operation="link",
            success=True,
            detail={"source": source_id, "target": target_id},
        )

    def _execute_validate(self, line: str) -> ArgTLResult:
        """Validate a named fragment assurance case."""
        tokens = line.split()
        if len(tokens) != 2:
            return ArgTLResult(
                operation="validate",
                success=False,
                detail={"error": "Validate syntax: validate fragment_id"},
            )

        fragment = self._fragments.get(tokens[1])
        if fragment is None:
            return ArgTLResult(
                operation="validate",
                success=False,
                detail={"error": f"Unknown fragment: {tokens[1]}"},
            )

        validation = fragment.case.validate()
        return ArgTLResult(
            operation="validate",
            success=bool(validation["valid"]),
            detail=validation,
        )

    def _execute_assemble(self, line: str) -> ArgTLResult:
        """Assemble is an alias for compose with identical semantics."""
        normalized = line.replace("assemble", "compose", 1)
        result = self._execute_compose(normalized)
        return ArgTLResult(
            operation="assemble",
            success=result.success,
            detail=result.detail,
        )

    def _merge_case(self, base: AssuranceCase, incoming: AssuranceCase) -> None:
        """Merge incoming case nodes into base while preserving root links."""
        root_to_link = base.root_goal_id
        incoming_root = incoming.root_goal_id

        for node_id, node in incoming.nodes.items():
            candidate = node_id
            suffix = 1
            while candidate in base.nodes:
                suffix += 1
                candidate = f"{node_id}_{suffix}"

            if candidate != node_id:
                copied = copy.deepcopy(node)
                copied.id = candidate
                base.add_node(copied)
            else:
                base.add_node(copy.deepcopy(node))

        if root_to_link and incoming_root and incoming_root in base.nodes:
            base.link_nodes(root_to_link, incoming_root)
