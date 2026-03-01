"""Architecture mapper for assurance-oriented implementation traceability."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from civ_arcos.utils import iter_python_files


class DiscrepancySeverity(str, Enum):
    """Severity levels for design/implementation discrepancies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ArchitectureComponent:
    """Normalized component discovered in implementation or design."""

    name: str
    component_type: str
    file_path: str


class ArchitectureMapper:
    """Infer architecture from source and map it against design intent."""

    def infer_architecture(self, source_path: str) -> Dict[str, object]:
        """Infer architecture components from Python source files."""
        components: List[ArchitectureComponent] = []

        for file_path in iter_python_files(source_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                    source = fh.read()
                tree = ast.parse(source, filename=file_path)
            except (OSError, SyntaxError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    components.append(
                        ArchitectureComponent(
                            name=node.name,
                            component_type="class",
                            file_path=file_path,
                        )
                    )
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_"):
                        continue
                    components.append(
                        ArchitectureComponent(
                            name=node.name,
                            component_type="function",
                            file_path=file_path,
                        )
                    )

        serialized = [
            {
                "name": component.name,
                "type": component.component_type,
                "file_path": component.file_path,
            }
            for component in components
        ]
        return {
            "component_count": len(serialized),
            "components": serialized,
        }

    def map_design_to_implementation(
        self,
        design_requirements: List[Dict[str, str]],
        inferred_architecture: Dict[str, object],
    ) -> Dict[str, object]:
        """Map design requirements to inferred implementation components."""
        inferred_components = inferred_architecture.get("components", [])
        index = {
            f"{item.get('type', '')}:{item.get('name', '')}": item
            for item in inferred_components
            if isinstance(item, dict)
        }

        mappings: List[Dict[str, object]] = []
        for requirement in design_requirements:
            expected_key = f"{requirement.get('type', '')}:{requirement.get('name', '')}"
            matched = index.get(expected_key)
            mappings.append(
                {
                    "requirement": requirement,
                    "implemented": matched is not None,
                    "implementation": matched,
                }
            )

        total = len(mappings)
        implemented = len([entry for entry in mappings if entry["implemented"]])
        coverage = 0.0 if total == 0 else round(implemented / total, 3)

        return {
            "mappings": mappings,
            "coverage": coverage,
            "implemented": implemented,
            "total": total,
        }

    def detect_discrepancies(
        self,
        design_requirements: List[Dict[str, str]],
        inferred_architecture: Dict[str, object],
    ) -> Dict[str, object]:
        """Detect missing/extra/mismatch components between design and code."""
        map_result = self.map_design_to_implementation(
            design_requirements,
            inferred_architecture,
        )
        missing = [
            mapping["requirement"]
            for mapping in map_result["mappings"]
            if not mapping["implemented"]
        ]

        design_keys = {
            f"{item.get('type', '')}:{item.get('name', '')}"
            for item in design_requirements
        }
        inferred_items = inferred_architecture.get("components", [])
        extra: List[Dict[str, str]] = []
        mismatches: List[Dict[str, object]] = []

        for item in inferred_items:
            if not isinstance(item, dict):
                continue
            key = f"{item.get('type', '')}:{item.get('name', '')}"
            if key not in design_keys:
                extra.append(item)

        for requirement in design_requirements:
            candidate = [
                item
                for item in inferred_items
                if isinstance(item, dict) and item.get("name") == requirement.get("name")
            ]
            for item in candidate:
                if item.get("type") != requirement.get("type"):
                    mismatches.append(
                        {
                            "requirement": requirement,
                            "implementation": item,
                            "severity": DiscrepancySeverity.MEDIUM.value,
                        }
                    )

        if missing:
            severity = DiscrepancySeverity.HIGH.value
        elif mismatches:
            severity = DiscrepancySeverity.MEDIUM.value
        elif extra:
            severity = DiscrepancySeverity.LOW.value
        else:
            severity = DiscrepancySeverity.LOW.value

        return {
            "missing": missing,
            "extra": extra,
            "mismatches": mismatches,
            "severity": severity,
        }

    def map_coverage_to_components(
        self,
        coverage_items: List[Dict[str, object]],
        inferred_architecture: Dict[str, object],
    ) -> Dict[str, object]:
        """Attach coverage scores to inferred architecture components."""
        coverage_index = {
            str(item.get("name")): float(item.get("coverage", 0.0))
            for item in coverage_items
        }
        components = inferred_architecture.get("components", [])
        mapped: List[Dict[str, object]] = []

        for item in components:
            if not isinstance(item, dict):
                continue
            score = coverage_index.get(str(item.get("name")), 0.0)
            mapped.append(
                {
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "coverage": round(score, 2),
                }
            )

        average = (
            0.0
            if not mapped
            else round(
                sum(float(entry["coverage"]) for entry in mapped) / len(mapped),
                2,
            )
        )
        return {
            "components": mapped,
            "average_coverage": average,
        }

    def generate_traceability_matrix(
        self,
        design_requirements: List[Dict[str, str]],
        inferred_architecture: Dict[str, object],
    ) -> List[Dict[str, object]]:
        """Generate requirement-to-implementation traceability rows."""
        mapping = self.map_design_to_implementation(
            design_requirements,
            inferred_architecture,
        )
        rows: List[Dict[str, object]] = []
        for item in mapping["mappings"]:
            requirement = item["requirement"]
            rows.append(
                {
                    "requirement_id": requirement.get("id"),
                    "requirement_name": requirement.get("name"),
                    "required_type": requirement.get("type"),
                    "implemented": item["implemented"],
                    "implementation": item.get("implementation"),
                }
            )
        return rows