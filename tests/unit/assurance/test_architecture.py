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


def test_detect_discrepancies_reports_mismatch_with_medium_severity() -> None:
    """Type mismatch should be reported with medium discrepancy severity."""
    mapper = ArchitectureMapper()
    inferred = {
        "components": [
            {"name": "PaymentService", "type": "class", "file_path": "x.py"},
            {"name": "PaymentService", "type": "function", "file_path": "x.py"},
        ]
    }
    design = [{"id": "R-1", "name": "PaymentService", "type": "function"}]

    discrepancies = mapper.detect_discrepancies(design, inferred)

    assert len(discrepancies["mismatches"]) == 1
    assert discrepancies["severity"] == "medium"


def test_map_coverage_to_components_defaults_to_zero_when_empty() -> None:
    """Coverage mapping should default to zero averages for empty sets."""
    mapper = ArchitectureMapper()

    result = mapper.map_coverage_to_components([], {"components": []})

    assert result["components"] == []
    assert result["average_coverage"] == 0.0


def test_infer_architecture_skips_syntax_error_files() -> None:
    """Inference should continue when one source file contains syntax errors."""
    mapper = ArchitectureMapper()
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "good.py").write_text(
            """
class GoodClass:
    pass
""".strip(),
            encoding="utf-8",
        )
        (root / "bad.py").write_text(
            "def broken(:\n    pass\n",
            encoding="utf-8",
        )

        result = mapper.infer_architecture(str(root))

    names = [item["name"] for item in result["components"]]
    assert "GoodClass" in names


def test_detect_discrepancies_with_only_extra_components_is_low_severity() -> None:
    """Extra implementation components without missing items should be low."""
    mapper = ArchitectureMapper()
    inferred = {
        "components": [
            {"name": "ExtraComponent", "type": "class", "file_path": "x.py"},
        ]
    }

    discrepancies = mapper.detect_discrepancies([], inferred)

    assert discrepancies["missing"] == []
    assert len(discrepancies["extra"]) == 1
    assert discrepancies["severity"] == "low"


def test_map_design_to_implementation_handles_empty_design() -> None:
    """Empty design requirements should yield zero totals and zero coverage."""
    mapper = ArchitectureMapper()
    inferred = {
        "components": [
            {"name": "PaymentService", "type": "class", "file_path": "x.py"},
        ]
    }

    result = mapper.map_design_to_implementation([], inferred)

    assert result["total"] == 0
    assert result["implemented"] == 0
    assert result["coverage"] == 0.0


def test_infer_architecture_discovers_public_async_functions() -> None:
    """Inference should include public async functions as components."""
    mapper = ArchitectureMapper()
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "async_mod.py").write_text(
            """
async def process_events():
    return 1

async def _private_task():
    return 0
""".strip(),
            encoding="utf-8",
        )

        result = mapper.infer_architecture(str(root))

    names = [item["name"] for item in result["components"]]
    assert "process_events" in names
    assert "_private_task" not in names


def test_map_design_to_implementation_ignores_non_dict_inferred_items() -> None:
    """Mapping should skip malformed inferred component entries."""
    mapper = ArchitectureMapper()
    design = [{"id": "R-1", "name": "PaymentService", "type": "class"}]
    inferred = {
        "components": [
            "not-a-dict",
            {"name": "PaymentService", "type": "class", "file_path": "x.py"},
        ]
    }

    result = mapper.map_design_to_implementation(design, inferred)

    assert result["total"] == 1
    assert result["implemented"] == 1
    assert result["coverage"] == 1.0


def test_detect_discrepancies_type_mismatch_with_missing_is_high() -> None:
    """Missing requirements should keep discrepancy severity at high."""
    mapper = ArchitectureMapper()
    design = [{"id": "R-1", "name": "Gateway", "type": "function"}]
    inferred = {
        "components": [
            {"name": "Gateway", "type": "class", "file_path": "x.py"},
        ]
    }

    discrepancies = mapper.detect_discrepancies(design, inferred)

    assert len(discrepancies["missing"]) == 1
    assert len(discrepancies["mismatches"]) == 1
    assert discrepancies["severity"] == "high"


def test_map_coverage_to_components_rounds_string_scores() -> None:
    """Coverage mapping should coerce numeric strings and round scores."""
    mapper = ArchitectureMapper()
    inferred = {
        "components": [
            {"name": "collector", "type": "function", "file_path": "x.py"},
        ]
    }
    coverage = [{"name": "collector", "coverage": "88.888"}]

    result = mapper.map_coverage_to_components(coverage, inferred)

    assert result["components"][0]["coverage"] == 88.89
    assert result["average_coverage"] == 88.89


def test_generate_traceability_matrix_handles_missing_requirement_id() -> None:
    """Traceability should preserve rows when requirement ID is absent."""
    mapper = ArchitectureMapper()
    inferred = {
        "components": [
            {"name": "Gateway", "type": "function", "file_path": "x.py"},
        ]
    }
    design = [{"name": "Gateway", "type": "function"}]

    rows = mapper.generate_traceability_matrix(design, inferred)

    assert len(rows) == 1
    assert rows[0]["requirement_id"] is None
    assert rows[0]["implemented"] is True
