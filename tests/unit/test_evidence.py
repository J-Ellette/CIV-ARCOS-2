"""Tests for evidence collection and storage."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from civ_arcos.evidence.collector import Evidence, EvidenceStore
from civ_arcos.storage.graph import EvidenceGraph


def make_evidence(etype="test", source="test_source") -> Evidence:
    import uuid
    from datetime import datetime, timezone

    return Evidence(
        id=str(uuid.uuid4()),
        type=etype,
        source=source,
        timestamp=datetime.now(timezone.utc).isoformat(),
        data={"key": "value", "num": 42},
        provenance={"collector": "test"},
    )


def test_evidence_checksum_computed():
    ev = make_evidence()
    assert ev.checksum != ""
    assert len(ev.checksum) == 64  # sha256 hex


def test_store_and_retrieve_evidence():
    store = EvidenceStore()
    ev = make_evidence()
    nid = store.store_evidence(ev)
    assert nid != ""
    retrieved = store.get_evidence(ev.id)
    assert retrieved is not None
    assert retrieved.id == ev.id
    assert retrieved.type == ev.type


def test_list_evidence():
    store = EvidenceStore()
    e1 = make_evidence("type_a")
    e2 = make_evidence("type_b")
    store.store_evidence(e1)
    store.store_evidence(e2)
    lst = store.list_evidence()
    assert len(lst) == 2


def test_verify_chain_valid():
    store = EvidenceStore()
    for _ in range(3):
        store.store_evidence(make_evidence())
    assert store.verify_chain() is True


def test_evidence_not_found():
    store = EvidenceStore()
    result = store.get_evidence("nonexistent-id")
    assert result is None


def test_evidence_checksum_detects_tamper():
    import hashlib
    import json

    ev = make_evidence()
    assert (
        ev.checksum
        == hashlib.sha256(json.dumps(ev.data, sort_keys=True).encode()).hexdigest()
    )


def test_evidence_store_cold_start_recovery(tmp_path):
    graph = EvidenceGraph()
    store = EvidenceStore(graph)
    evidence = make_evidence("recovery")
    store.store_evidence(evidence)

    path = str(tmp_path / "evidence_graph.json")
    graph.save(path)

    loaded_graph = EvidenceGraph()
    loaded_graph.load(path)
    rehydrated_store = EvidenceStore(loaded_graph)
    restored = rehydrated_store.get_evidence(evidence.id)

    assert restored is not None
    assert restored.id == evidence.id
    assert restored.type == "recovery"


def test_evidence_store_concurrent_writes_preserved_after_reload(tmp_path):
    graph = EvidenceGraph()
    store = EvidenceStore(graph)

    def _write(_: int) -> str:
        evidence = make_evidence("parallel")
        return store.store_evidence(evidence)

    write_count = 100
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(_write, range(write_count)))

    assert len(results) == write_count

    path = str(tmp_path / "parallel_graph.json")
    graph.save(path)

    loaded_graph = EvidenceGraph()
    loaded_graph.load(path)
    loaded_store = EvidenceStore(loaded_graph)
    loaded = loaded_store.list_evidence()
    assert len(loaded) == write_count
