"""Evidence collectors integrating analysis tools with the evidence system."""

from typing import Any, Dict, List, Optional

from civ_arcos.evidence.collector import Evidence, EvidenceCollector, EvidenceStore
from civ_arcos.storage.graph import EvidenceGraph
from civ_arcos.analysis.static_analyzer import StaticAnalyzer
from civ_arcos.analysis.security_scanner import SecurityScanner
from civ_arcos.analysis.test_generator import TestGenerator
from civ_arcos.analysis.coverage_analyzer import CoverageAnalyzer
from civ_arcos.utils import iter_python_files, make_evidence


class _AnalysisCollector(EvidenceCollector):
    """Base class for analysis collectors with stub implementations.

    Subclasses *must* override :meth:`collect` to perform the actual
    analysis and return a list of :class:`~civ_arcos.evidence.collector.Evidence`
    objects.  The ``collect_from_*`` methods return empty lists by default;
    subclasses may override them as needed (e.g.
    :class:`SecurityScanCollector` overrides
    :meth:`collect_from_security_tools`).
    """

    def __init__(self, source_path: str, graph: Optional[EvidenceGraph] = None) -> None:
        self._source_path = source_path
        self._store = EvidenceStore(graph) if graph else None

    def collect_from_github(self, repo_url: str, commit_hash: str) -> List[Evidence]:
        return []

    def collect_from_ci(self, build_id: str) -> List[Evidence]:
        return []

    def collect_from_security_tools(
        self, scan_results: Dict[str, Any]
    ) -> List[Evidence]:
        return []

    def _store_and_return(self, ev: Evidence) -> List[Evidence]:
        if self._store:
            self._store.store_evidence(ev)
        return [ev]


class StaticAnalysisCollector(_AnalysisCollector):
    def collect(self, *args: Any, **kwargs: Any) -> List[Evidence]:
        analyzer = StaticAnalyzer()
        results = analyzer.analyze_directory(self._source_path)
        ev = make_evidence("static_analysis", self._source_path, {"results": results})
        return self._store_and_return(ev)


class SecurityScanCollector(_AnalysisCollector):
    def collect(self, *args: Any, **kwargs: Any) -> List[Evidence]:
        scanner = SecurityScanner()
        results = scanner.scan_directory(self._source_path)
        score_data = scanner.calculate_security_score(results)
        ev = make_evidence(
            "security_scan",
            self._source_path,
            {"results": results, "score": score_data},
        )
        return self._store_and_return(ev)

    def collect_from_security_tools(
        self, scan_results: Dict[str, Any]
    ) -> List[Evidence]:
        ev = make_evidence("security_scan", self._source_path, scan_results)
        return self._store_and_return(ev)


class TestGenerationCollector(_AnalysisCollector):
    def collect(self, *args: Any, **kwargs: Any) -> List[Evidence]:
        gen = TestGenerator()
        suggestions_list = [
            gen.get_suggestions(fpath) for fpath in iter_python_files(self._source_path)
        ]
        ev = make_evidence(
            "test_generation",
            self._source_path,
            {"suggestions": suggestions_list},
        )
        return self._store_and_return(ev)


class CoverageCollector(_AnalysisCollector):
    def __init__(
        self,
        source_path: str,
        graph: Optional[EvidenceGraph] = None,
        test_path: Optional[str] = None,
    ) -> None:
        super().__init__(source_path, graph)
        self._test_path = test_path or source_path

    def collect(self, *args: Any, **kwargs: Any) -> List[Evidence]:
        analyzer = CoverageAnalyzer()
        raw = analyzer.run_coverage(self._test_path, self._source_path)
        if raw:
            analysis = analyzer.analyze_coverage_data(raw)
        else:
            analysis = {
                "line_coverage_pct": 0.0,
                "branch_coverage_pct": 0.0,
                "tier": "none",
                "summary": "Coverage data unavailable",
            }
        ev = make_evidence("coverage", self._source_path, analysis)
        return self._store_and_return(ev)


class ComprehensiveAnalysisCollector:
    """Run all analysis collectors and return aggregated evidence."""

    def __init__(self, source_path: str, graph: Optional[EvidenceGraph] = None) -> None:
        self._source_path = source_path
        self._graph = graph

    def collect(self) -> List[Evidence]:
        all_evidence: List[Evidence] = []
        for cls in (
            StaticAnalysisCollector,
            SecurityScanCollector,
            TestGenerationCollector,
        ):
            collector = cls(self._source_path, self._graph)
            all_evidence.extend(collector.collect())
        # CoverageCollector takes an optional test_path; use source_path as fallback
        cov_collector = CoverageCollector(self._source_path, self._graph)
        all_evidence.extend(cov_collector.collect())
        return all_evidence
