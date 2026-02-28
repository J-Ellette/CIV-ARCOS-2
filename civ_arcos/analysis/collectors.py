"""Evidence collectors integrating analysis tools with the evidence system."""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from civ_arcos.evidence.collector import Evidence, EvidenceCollector, EvidenceStore
from civ_arcos.storage.graph import EvidenceGraph
from civ_arcos.analysis.static_analyzer import StaticAnalyzer
from civ_arcos.analysis.security_scanner import SecurityScanner
from civ_arcos.analysis.test_generator import TestGenerator
from civ_arcos.analysis.coverage_analyzer import CoverageAnalyzer


def _make_evidence(ev_type: str, source: str, data: Dict[str, Any]) -> Evidence:
    return Evidence(
        id=str(uuid.uuid4()),
        type=ev_type,
        source=source,
        timestamp=datetime.now(timezone.utc).isoformat(),
        data=data,
        provenance={"collector": ev_type, "source_path": source},
    )


class StaticAnalysisCollector(EvidenceCollector):
    def __init__(self, source_path: str, graph: Optional[EvidenceGraph] = None) -> None:
        self._source_path = source_path
        self._store = EvidenceStore(graph) if graph else None

    def collect(self, *args: Any, **kwargs: Any) -> List[Evidence]:
        analyzer = StaticAnalyzer()
        results = analyzer.analyze_directory(self._source_path)
        ev = _make_evidence("static_analysis", self._source_path, {"results": results})
        if self._store:
            self._store.store_evidence(ev)
        return [ev]

    def collect_from_github(self, repo_url: str, commit_hash: str) -> List[Evidence]:
        return []

    def collect_from_ci(self, build_id: str) -> List[Evidence]:
        return []

    def collect_from_security_tools(self, scan_results: Dict[str, Any]) -> List[Evidence]:
        return []


class SecurityScanCollector(EvidenceCollector):
    def __init__(self, source_path: str, graph: Optional[EvidenceGraph] = None) -> None:
        self._source_path = source_path
        self._store = EvidenceStore(graph) if graph else None

    def collect(self, *args: Any, **kwargs: Any) -> List[Evidence]:
        scanner = SecurityScanner()
        results = scanner.scan_directory(self._source_path)
        score_data = scanner.calculate_security_score(results)
        ev = _make_evidence(
            "security_scan",
            self._source_path,
            {"results": results, "score": score_data},
        )
        if self._store:
            self._store.store_evidence(ev)
        return [ev]

    def collect_from_github(self, repo_url: str, commit_hash: str) -> List[Evidence]:
        return []

    def collect_from_ci(self, build_id: str) -> List[Evidence]:
        return []

    def collect_from_security_tools(self, scan_results: Dict[str, Any]) -> List[Evidence]:
        ev = _make_evidence("security_scan", self._source_path, scan_results)
        if self._store:
            self._store.store_evidence(ev)
        return [ev]


class TestGenerationCollector(EvidenceCollector):
    def __init__(self, source_path: str, graph: Optional[EvidenceGraph] = None) -> None:
        self._source_path = source_path
        self._store = EvidenceStore(graph) if graph else None

    def collect(self, *args: Any, **kwargs: Any) -> List[Evidence]:
        import os
        gen = TestGenerator()
        suggestions_list = []
        for root, _dirs, files in os.walk(self._source_path):
            for fname in files:
                if fname.endswith(".py"):
                    suggestions_list.append(
                        gen.get_suggestions(os.path.join(root, fname))
                    )
        ev = _make_evidence(
            "test_generation",
            self._source_path,
            {"suggestions": suggestions_list},
        )
        if self._store:
            self._store.store_evidence(ev)
        return [ev]

    def collect_from_github(self, repo_url: str, commit_hash: str) -> List[Evidence]:
        return []

    def collect_from_ci(self, build_id: str) -> List[Evidence]:
        return []

    def collect_from_security_tools(self, scan_results: Dict[str, Any]) -> List[Evidence]:
        return []


class CoverageCollector(EvidenceCollector):
    def __init__(self, source_path: str, graph: Optional[EvidenceGraph] = None,
                 test_path: Optional[str] = None) -> None:
        self._source_path = source_path
        self._test_path = test_path or source_path
        self._store = EvidenceStore(graph) if graph else None

    def collect(self, *args: Any, **kwargs: Any) -> List[Evidence]:
        analyzer = CoverageAnalyzer()
        raw = analyzer.run_coverage(self._test_path, self._source_path)
        if raw:
            analysis = analyzer.analyze_coverage_data(raw)
        else:
            analysis = {"line_coverage_pct": 0.0, "branch_coverage_pct": 0.0,
                        "tier": "none", "summary": "Coverage data unavailable"}
        ev = _make_evidence("coverage", self._source_path, analysis)
        if self._store:
            self._store.store_evidence(ev)
        return [ev]

    def collect_from_github(self, repo_url: str, commit_hash: str) -> List[Evidence]:
        return []

    def collect_from_ci(self, build_id: str) -> List[Evidence]:
        return []

    def collect_from_security_tools(self, scan_results: Dict[str, Any]) -> List[Evidence]:
        return []


class ComprehensiveAnalysisCollector:
    """Run all analysis collectors and return aggregated evidence."""

    def __init__(self, source_path: str, graph: Optional[EvidenceGraph] = None) -> None:
        self._source_path = source_path
        self._graph = graph

    def collect(self) -> List[Evidence]:
        all_evidence: List[Evidence] = []
        for cls in (StaticAnalysisCollector, SecurityScanCollector, TestGenerationCollector):
            collector = cls(self._source_path, self._graph)
            all_evidence.extend(collector.collect())
        # CoverageCollector takes an optional test_path; use source_path as fallback
        cov_collector = CoverageCollector(self._source_path, self._graph)
        all_evidence.extend(cov_collector.collect())
        return all_evidence
