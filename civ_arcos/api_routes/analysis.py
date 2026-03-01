"""Analysis domain routes for legacy and v1 APIs."""

from __future__ import annotations

from civ_arcos.analysis.collectors import ComprehensiveAnalysisCollector
from civ_arcos.analysis.security_scanner import SecurityScanner
from civ_arcos.analysis.static_analyzer import StaticAnalyzer
from civ_arcos.analysis.test_generator import TestGenerator
from civ_arcos.contracts.v1 import (
    analysis_comprehensive_contract,
    analysis_security_contract,
    analysis_static_contract,
    analysis_tests_contract,
)
from civ_arcos.storage.graph import EvidenceGraph
from civ_arcos.utils import iter_python_files
from civ_arcos.web.framework import Application, Request, Response


def register_analysis_legacy_routes(app: Application, graph: EvidenceGraph) -> None:
    """Register legacy analysis routes under ``/api/analysis``."""

    @app.route("/api/analysis/static", methods=["POST"])
    def analysis_static(req: Request) -> Response:
        body = req.json() or {}
        source_path = body.get("source_path", ".")
        analyzer = StaticAnalyzer()
        results = analyzer.analyze_directory(source_path)
        return Response({"results": results, "file_count": len(results)})

    @app.route("/api/analysis/security", methods=["POST"])
    def analysis_security(req: Request) -> Response:
        body = req.json() or {}
        source_path = body.get("source_path", ".")
        scanner = SecurityScanner()
        results = scanner.scan_directory(source_path)
        score = scanner.calculate_security_score(results)
        return Response(
            {"results": results, "score": score, "file_count": len(results)}
        )

    @app.route("/api/analysis/tests", methods=["POST"])
    def analysis_tests(req: Request) -> Response:
        body = req.json() or {}
        source_path = body.get("source_path", ".")
        use_ai = bool(body.get("use_ai", False))
        llm_backend = str(body.get("llm_backend", "mock"))
        generator = TestGenerator(use_ai=use_ai, llm_backend=llm_backend)
        suggestions_list = [
            generator.get_suggestions(fpath) for fpath in iter_python_files(source_path)
        ]
        return Response(
            {"results": suggestions_list, "file_count": len(suggestions_list)}
        )

    @app.route("/api/analysis/comprehensive", methods=["POST"])
    def analysis_comprehensive(req: Request) -> Response:
        body = req.json() or {}
        source_path = body.get("source_path", ".")
        collector = ComprehensiveAnalysisCollector(source_path, graph)
        evidence_list = collector.collect()
        return Response(
            {
                "evidence_collected": len(evidence_list),
                "evidence_ids": [evidence.id for evidence in evidence_list],
            }
        )


def register_analysis_v1_routes(app: Application, graph: EvidenceGraph) -> None:
    """Register versioned analysis routes under ``/api/v1/analysis``."""

    @app.route("/api/v1/analysis/static", methods=["POST"])
    def analysis_static_v1(req: Request) -> Response:
        body = req.json() or {}
        source_path = body.get("source_path", ".")
        analyzer = StaticAnalyzer()
        results = analyzer.analyze_directory(source_path)
        return Response(
            analysis_static_contract({"results": results, "file_count": len(results)})
        )

    @app.route("/api/v1/analysis/security", methods=["POST"])
    def analysis_security_v1(req: Request) -> Response:
        body = req.json() or {}
        source_path = body.get("source_path", ".")
        scanner = SecurityScanner()
        results = scanner.scan_directory(source_path)
        score = scanner.calculate_security_score(results)
        return Response(
            analysis_security_contract(
                {"results": results, "score": score, "file_count": len(results)}
            )
        )

    @app.route("/api/v1/analysis/tests", methods=["POST"])
    def analysis_tests_v1(req: Request) -> Response:
        body = req.json() or {}
        source_path = body.get("source_path", ".")
        use_ai = bool(body.get("use_ai", False))
        llm_backend = str(body.get("llm_backend", "mock"))
        generator = TestGenerator(use_ai=use_ai, llm_backend=llm_backend)
        suggestions_list = [
            generator.get_suggestions(fpath) for fpath in iter_python_files(source_path)
        ]
        return Response(
            analysis_tests_contract(
                {"results": suggestions_list, "file_count": len(suggestions_list)}
            )
        )

    @app.route("/api/v1/analysis/comprehensive", methods=["POST"])
    def analysis_comprehensive_v1(req: Request) -> Response:
        body = req.json() or {}
        source_path = body.get("source_path", ".")
        collector = ComprehensiveAnalysisCollector(source_path, graph)
        evidence_list = collector.collect()
        return Response(
            analysis_comprehensive_contract(
                {
                    "evidence_collected": len(evidence_list),
                    "evidence_ids": [evidence.id for evidence in evidence_list],
                }
            )
        )
