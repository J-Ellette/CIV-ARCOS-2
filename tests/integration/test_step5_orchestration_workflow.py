"""Integration test for the Step 5 six-step orchestration workflow."""

import tempfile
from pathlib import Path

from civ_arcos.assurance.acql import ACQLEngine
from civ_arcos.assurance.architecture import ArchitectureMapper
from civ_arcos.assurance.argtl import ArgTLEngine
from civ_arcos.assurance.dependency_tracker import (
    DependencyTracker,
    DependencyType,
    ResourceType,
)
from civ_arcos.assurance.fragments import FragmentLibrary
from civ_arcos.assurance.reasoning import ReasoningEngine


def _create_sample_source_tree(tmp_path: Path) -> str:
    """Create a minimal source tree for architecture inference."""
    sample_module = tmp_path / "payments.py"
    sample_module.write_text(
        """
class PaymentService:
    pass

def process_payment():
    return True

def _internal_helper():
    return False
""".strip(),
        encoding="utf-8",
    )
    return str(tmp_path)


def test_step5_six_step_orchestration_workflow() -> None:
    """Run architecture→fragments→ArgTL→ACQL→reasoning→dependency flow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = _create_sample_source_tree(Path(tmpdir))

        mapper = ArchitectureMapper()
        inferred = mapper.infer_architecture(source_path)

    components = inferred["components"]
    assert inferred["component_count"] >= 2

    library = FragmentLibrary()
    fragments = []
    for index, component in enumerate(components):
        pattern = (
            "component_quality"
            if component["type"] == "class"
            else "component_security"
        )
        fragment = library.create_fragment(
            pattern=pattern,
            fragment_id=f"frag_{index}",
            title=f"{component['name']} Fragment",
            description="Auto-generated from architecture inference",
            component_name=component["name"],
        )
        fragments.append(fragment)

    assert len(fragments) >= 2

    argtl = ArgTLEngine()
    for fragment in fragments:
        argtl.register_fragment(fragment)

    source_fragment_ids = " ".join(fragment.fragment_id for fragment in fragments)
    compose_result = argtl.execute_line(
        f"compose {source_fragment_ids} -> system_orchestration_case"
    )
    assert compose_result.success is True

    assembled_fragment = argtl.get_fragment("system_orchestration_case")
    assert assembled_fragment is not None

    for node in assembled_fragment.case.nodes.values():
        if not node.evidence_ids:
            node.evidence_ids.append(f"ev_{node.id}")

    acql = ACQLEngine()
    acql.register_fragment(assembled_fragment)
    completeness = acql.execute_line("completeness on system_orchestration_case")
    assert completeness.query_type == "completeness"
    assert completeness.passed is True

    reasoning = ReasoningEngine()
    reasoning_result = reasoning.reason_about_case(
        assembled_fragment.case,
        context={"critical_vulnerabilities": 0},
    )
    assert 0.0 <= reasoning_result["confidence_score"] <= 1.0
    assert "recommendations" in reasoning_result

    tracker = DependencyTracker()
    tracker.register_resource(
        "res_case",
        ResourceType.MODEL,
        "system_orchestration_case",
    )
    tracker.register_resource(
        "res_test",
        ResourceType.TEST,
        "test_step5_orchestration_workflow",
    )
    tracker.register_resource(
        "res_evidence",
        ResourceType.EVIDENCE,
        "step5_workflow_evidence",
    )

    for index, component in enumerate(components):
        resource_id = f"res_component_{index}"
        resource_type = (
            ResourceType.FILE
            if component["type"] == "class"
            else ResourceType.DIRECTORY
        )
        tracker.register_resource(resource_id, resource_type, component["name"])
        tracker.link_dependency(resource_id, "res_case", DependencyType.IMPLEMENTS)

    tracker.link_dependency("res_case", "res_test", DependencyType.TESTS)
    tracker.link_dependency("res_test", "res_evidence", DependencyType.VALIDATES)

    impact = tracker.impact_analysis("res_component_0")
    impacted_ids = {item["resource_id"] for item in impact["impacted_resources"]}

    assert impact["impacted_count"] >= 3
    assert "res_case" in impacted_ids
    assert "res_test" in impacted_ids
    assert "res_evidence" in impacted_ids
