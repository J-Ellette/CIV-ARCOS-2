"""Unit tests for CAID-tools-style dependency tracker behavior."""

import pytest

from civ_arcos.assurance.dependency_tracker import (
    DependencyTracker,
    DependencyType,
    ResourceType,
)


def _seed_tracker() -> DependencyTracker:
    """Create baseline tracker with representative resource graph."""
    tracker = DependencyTracker()
    tracker.register_resource("f1", ResourceType.FILE, "collector.py")
    tracker.register_resource("m1", ResourceType.MODEL, "collector_model")
    tracker.register_resource("t1", ResourceType.TEST, "test_collector")
    tracker.register_resource("e1", ResourceType.EVIDENCE, "coverage_evidence")
    return tracker


def test_register_and_list_resources() -> None:
    """Resource registration should persist and list deterministically."""
    tracker = _seed_tracker()
    resources = tracker.list_resources()

    assert len(resources) == 4
    assert resources[0].resource_id == "e1"
    assert tracker.get_resource("f1") is not None


def test_link_dependency_deduplicates_same_edge() -> None:
    """Linking the same dependency twice should not duplicate edges."""
    tracker = _seed_tracker()
    tracker.link_dependency("f1", "m1", DependencyType.IMPLEMENTS)
    tracker.link_dependency("f1", "m1", DependencyType.IMPLEMENTS)

    dependencies = tracker.list_dependencies()
    assert len(dependencies) == 1
    assert dependencies[0].dependency_type == DependencyType.IMPLEMENTS


def test_update_listener_notified_on_resource_change() -> None:
    """Registered listeners should be called on update notifications."""
    tracker = _seed_tracker()
    seen = []

    def listener(resource):
        seen.append(resource.resource_id)

    tracker.add_update_listener(listener)
    tracker.notify_resource_update("m1")

    assert seen == ["m1"]


def test_impact_analysis_returns_transitive_dependents() -> None:
    """Impact analysis should include transitive downstream resources."""
    tracker = _seed_tracker()
    tracker.link_dependency("f1", "m1", DependencyType.IMPLEMENTS)
    tracker.link_dependency("m1", "t1", DependencyType.TESTS)
    tracker.link_dependency("t1", "e1", DependencyType.VALIDATES)

    result = tracker.impact_analysis("f1")

    impacted_ids = [item["resource_id"] for item in result["impacted_resources"]]
    assert result["impacted_count"] == 3
    assert impacted_ids == ["e1", "m1", "t1"]


def test_link_dependency_rejects_unknown_resources() -> None:
    """Linking should fail when source or target resources are unknown."""
    tracker = _seed_tracker()

    with pytest.raises(ValueError):
        tracker.link_dependency("unknown", "m1", DependencyType.IMPLEMENTS)

    with pytest.raises(ValueError):
        tracker.link_dependency("f1", "unknown", DependencyType.IMPLEMENTS)


def test_notify_resource_update_rejects_unknown_resource() -> None:
    """Update notification should fail for unregistered resources."""
    tracker = _seed_tracker()

    with pytest.raises(ValueError):
        tracker.notify_resource_update("missing")


def test_register_resource_updates_existing_entry() -> None:
    """Re-registering the same id should update stored resource fields."""
    tracker = _seed_tracker()

    tracker.register_resource(
        "f1",
        ResourceType.FILE,
        "collector_v2.py",
        metadata={"version": 2},
    )

    resource = tracker.get_resource("f1")
    assert resource is not None
    assert resource.name == "collector_v2.py"
    assert resource.metadata["version"] == 2


def test_list_dependencies_preserves_insertion_order() -> None:
    """Dependency listing should keep insertion order for traceability."""
    tracker = _seed_tracker()
    tracker.link_dependency("f1", "m1", DependencyType.IMPLEMENTS)
    tracker.link_dependency("m1", "t1", DependencyType.TESTS)

    deps = tracker.list_dependencies()

    assert len(deps) == 2
    assert deps[0].source_id == "f1"
    assert deps[1].source_id == "m1"


def test_link_dependency_allows_same_nodes_with_different_edge_types() -> None:
    """Deduplication should be edge-type aware for same node pair."""
    tracker = _seed_tracker()
    tracker.link_dependency("f1", "m1", DependencyType.IMPLEMENTS)
    tracker.link_dependency("f1", "m1", DependencyType.REQUIRES)

    deps = tracker.list_dependencies()

    assert len(deps) == 2
    assert {dep.dependency_type for dep in deps} == {
        DependencyType.IMPLEMENTS,
        DependencyType.REQUIRES,
    }


def test_impact_analysis_returns_zero_for_resource_without_edges() -> None:
    """Impact analysis should return empty impact set when no edges originate."""
    tracker = _seed_tracker()

    result = tracker.impact_analysis("e1")

    assert result["impacted_count"] == 0
    assert result["impacted_resources"] == []
    assert result["dependency_path"] == []


def test_impact_analysis_rejects_unknown_resource() -> None:
    """Impact analysis should fail for unregistered resource ids."""
    tracker = _seed_tracker()

    with pytest.raises(ValueError):
        tracker.impact_analysis("missing")


def test_notify_resource_update_invokes_listeners_in_registration_order() -> None:
    """Listeners should be called in the same order they were added."""
    tracker = _seed_tracker()
    calls = []

    def first(resource):
        calls.append(f"first:{resource.resource_id}")

    def second(resource):
        calls.append(f"second:{resource.resource_id}")

    tracker.add_update_listener(first)
    tracker.add_update_listener(second)
    tracker.notify_resource_update("m1")

    assert calls == ["first:m1", "second:m1"]


def test_impact_analysis_handles_cycle_without_infinite_loop() -> None:
    """Cycle traversal should terminate and report impacted nodes deterministically."""
    tracker = _seed_tracker()
    tracker.link_dependency("f1", "m1", DependencyType.IMPLEMENTS)
    tracker.link_dependency("m1", "f1", DependencyType.REQUIRES)

    result = tracker.impact_analysis("f1")

    impacted_ids = [item["resource_id"] for item in result["impacted_resources"]]
    assert result["impacted_count"] == 2
    assert impacted_ids == ["f1", "m1"]


def test_impact_analysis_branching_deduplicates_shared_downstream_node() -> None:
    """Shared downstream nodes should appear once in impacted resource output."""
    tracker = _seed_tracker()
    tracker.link_dependency("f1", "m1", DependencyType.IMPLEMENTS)
    tracker.link_dependency("f1", "t1", DependencyType.TESTS)
    tracker.link_dependency("m1", "e1", DependencyType.VALIDATES)
    tracker.link_dependency("t1", "e1", DependencyType.VALIDATES)

    result = tracker.impact_analysis("f1")

    impacted_ids = [item["resource_id"] for item in result["impacted_resources"]]
    assert result["impacted_count"] == 3
    assert impacted_ids == ["e1", "m1", "t1"]


def test_impact_analysis_branching_preserves_all_traversed_edges() -> None:
    """Dependency path output should retain all traversed branch edges."""
    tracker = _seed_tracker()
    tracker.link_dependency("f1", "m1", DependencyType.IMPLEMENTS)
    tracker.link_dependency("f1", "t1", DependencyType.TESTS)

    result = tracker.impact_analysis("f1")

    edges = {
        (item["source_id"], item["target_id"]) for item in result["dependency_path"]
    }
    assert edges == {("f1", "m1"), ("f1", "t1")}


def test_impact_analysis_from_middle_node_includes_only_downstream_branch() -> None:
    """Impact from an interior node should include only reachable descendants."""
    tracker = _seed_tracker()
    tracker.link_dependency("f1", "m1", DependencyType.IMPLEMENTS)
    tracker.link_dependency("m1", "t1", DependencyType.TESTS)
    tracker.link_dependency("t1", "e1", DependencyType.VALIDATES)

    result = tracker.impact_analysis("m1")

    impacted_ids = [item["resource_id"] for item in result["impacted_resources"]]
    assert result["impacted_count"] == 2
    assert impacted_ids == ["e1", "t1"]


def test_impact_analysis_self_loop_reports_single_impacted_resource() -> None:
    """Self-loop dependencies should not duplicate impacted resource entries."""
    tracker = _seed_tracker()
    tracker.link_dependency("m1", "m1", DependencyType.REQUIRES)

    result = tracker.impact_analysis("m1")

    impacted_ids = [item["resource_id"] for item in result["impacted_resources"]]
    assert result["impacted_count"] == 1
    assert impacted_ids == ["m1"]


def test_impact_analysis_three_node_cycle_includes_all_cycle_nodes() -> None:
    """Three-node cycle traversal should include each reachable node once."""
    tracker = _seed_tracker()
    tracker.link_dependency("f1", "m1", DependencyType.IMPLEMENTS)
    tracker.link_dependency("m1", "t1", DependencyType.TESTS)
    tracker.link_dependency("t1", "f1", DependencyType.REQUIRES)

    result = tracker.impact_analysis("f1")

    impacted_ids = [item["resource_id"] for item in result["impacted_resources"]]
    assert result["impacted_count"] == 3
    assert impacted_ids == ["f1", "m1", "t1"]
