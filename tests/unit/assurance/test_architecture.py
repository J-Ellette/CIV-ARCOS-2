"""Unit tests for A-CERT-style architecture mapping utilities."""

import tempfile
from pathlib import Path

from civ_arcos.assurance.architecture import ArchitectureMapper


def _create_source_tree(tmp_path: Path) -> Path:
    """Create a minimal Python source tree for architecture inference tests."""
    module = tmp_path / "sample.py"
    module.write_text(
        """
class PaymentService:
    pass

def collect_metrics():
    return 1

def _internal_helper():
    return 0
""".strip(),
        encoding="utf-8",
    )
    return tmp_path


def test_infer_architecture_discovers_classes_and_public_functions() -> None:
    """Inference should find class and non-private function components."""
    mapper = ArchitectureMapper()
    with tempfile.TemporaryDirectory() as tmpdir:
        src = _create_source_tree(Path(tmpdir))
        result = mapper.infer_architecture(str(src))

    names = [item["name"] for item in result["components"]]
    assert "PaymentService" in names
    assert "collect_metrics" in names
    assert "_internal_helper" not in names


def test_detect_discrepancies_reports_missing_and_extra_components() -> None:
    """Discrepancy detection should classify missing and extra components."""
    mapper = ArchitectureMapper()
    inferred = {
        "components": [
            {"name": "PaymentService", "type": "class", "file_path": "x.py"},
            {"name": "collect_metrics", "type": "function", "file_path": "x.py"},
        ]
    }
    design = [
        {"id": "R-1", "name": "PaymentService", "type": "class"},
        {"id": "R-2", "name": "render_report", "type": "function"},
    ]

    discrepancies = mapper.detect_discrepancies(design, inferred)

    missing_names = [item["name"] for item in discrepancies["missing"]]
    extra_names = [item["name"] for item in discrepancies["extra"]]
    assert "render_report" in missing_names
    assert "collect_metrics" in extra_names
    assert discrepancies["severity"] == "high"


def test_map_coverage_to_components_calculates_average() -> None:
    """Coverage mapping should attach component coverage and average values."""
    mapper = ArchitectureMapper()
    inferred = {
        "components": [
            {"name": "PaymentService", "type": "class", "file_path": "x.py"},
            {"name": "collect_metrics", "type": "function", "file_path": "x.py"},
        ]
    }
    coverage = [{"name": "collect_metrics", "coverage": 90.0}]

    result = mapper.map_coverage_to_components(coverage, inferred)

    assert result["average_coverage"] == 45.0
    by_name = {item["name"]: item["coverage"] for item in result["components"]}
    assert by_name["collect_metrics"] == 90.0
    assert by_name["PaymentService"] == 0.0


def test_generate_traceability_matrix_marks_implemented_rows() -> None:
    """Traceability matrix should reflect implementation status by requirement."""
    mapper = ArchitectureMapper()
    inferred = {
        "components": [
            {"name": "PaymentService", "type": "class", "file_path": "x.py"},
        ]
    }
    design = [
        {"id": "R-1", "name": "PaymentService", "type": "class"},
        {"id": "R-2", "name": "collect_metrics", "type": "function"},
    ]

    rows = mapper.generate_traceability_matrix(design, inferred)

    row_map = {row["requirement_id"]: row for row in rows}
    assert row_map["R-1"]["implemented"] is True
    assert row_map["R-2"]["implemented"] is False