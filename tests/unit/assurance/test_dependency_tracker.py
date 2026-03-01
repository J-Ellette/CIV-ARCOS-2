"""Unit tests for CAID-tools-style dependency tracker behavior."""

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
