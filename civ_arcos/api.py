"""CIV-ARCOS REST API server."""
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict

from civ_arcos.adapters.github_adapter import GitHubCollector
from civ_arcos.core.config import get_config
from civ_arcos.distributed.blockchain_ledger import BlockchainLedger
from civ_arcos.evidence.collector import EvidenceStore
from civ_arcos.storage.graph import EvidenceGraph
from civ_arcos.web.badges import BadgeGenerator
from civ_arcos.web.framework import Application, Request, Response, create_app
from civ_arcos.analysis.static_analyzer import StaticAnalyzer
from civ_arcos.analysis.security_scanner import SecurityScanner
from civ_arcos.analysis.test_generator import TestGenerator
from civ_arcos.analysis.collectors import ComprehensiveAnalysisCollector
from civ_arcos.assurance.case import AssuranceCaseBuilder
from civ_arcos.assurance.patterns import PatternInstantiator, ProjectType
from civ_arcos.assurance.templates import TemplateLibrary
from civ_arcos.assurance.visualizer import GSNVisualizer

_start_time = time.time()
app: Application = create_app()
_graph = EvidenceGraph()
_store = EvidenceStore(_graph)
_ledger = BlockchainLedger()
_badges = BadgeGenerator()
_template_library = TemplateLibrary()
_visualizer = GSNVisualizer()
_assurance_cases: Dict[str, Any] = {}


@app.route("/", methods=["GET"])
def index(req: Request) -> Response:
    return Response({
        "name": "CIV-ARCOS API",
        "version": "0.1.0",
        "description": "Civilian Assurance-based Risk Computation and Orchestration System",
    })


@app.route("/api/status", methods=["GET"])
def status(req: Request) -> Response:
    return Response({
        "version": "0.1.0",
        "uptime_seconds": round(time.time() - _start_time, 2),
        "evidence_count": len(_store.list_evidence()),
        "blockchain_length": _ledger.get_chain_length(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/api/evidence/collect", methods=["POST"])
def collect_evidence(req: Request) -> Response:
    body = req.json() or {}
    repo_url = body.get("repo_url", "")
    token = body.get("token")
    config = get_config()
    collector = GitHubCollector(token=token or config.github_token or None)
    evidence_list = collector.collect(repo_url=repo_url)
    node_ids = []
    for ev in evidence_list:
        nid = _store.store_evidence(ev)
        _ledger.add_block({"evidence_id": ev.id, "checksum": ev.checksum})
        node_ids.append(nid)
    return Response({"collected": len(evidence_list), "node_ids": node_ids}, status_code=201)


@app.route("/api/evidence", methods=["GET"])
def list_evidence(req: Request) -> Response:
    evidence = _store.list_evidence()
    return Response([{
        "id": e.id, "type": e.type, "source": e.source,
        "timestamp": e.timestamp, "checksum": e.checksum
    } for e in evidence])


@app.route("/api/evidence/{evidence_id}", methods=["GET"])
def get_evidence(req: Request, evidence_id: str = "") -> Response:
    ev = _store.get_evidence(evidence_id)
    if ev is None:
        return Response({"error": "Evidence not found"}, status_code=404)
    return Response({
        "id": ev.id, "type": ev.type, "source": ev.source,
        "timestamp": ev.timestamp, "data": ev.data,
        "provenance": ev.provenance, "checksum": ev.checksum
    })


@app.route("/api/badge/coverage/{owner}/{repo}", methods=["GET"])
def badge_coverage(req: Request, owner: str = "", repo: str = "") -> Response:
    try:
        pct = float(req.query("coverage", "0"))
    except ValueError:
        pct = 0.0
    svg = _badges.generate_coverage_badge(pct)
    return Response(svg, content_type="image/svg+xml")


@app.route("/api/badge/quality/{owner}/{repo}", methods=["GET"])
def badge_quality(req: Request, owner: str = "", repo: str = "") -> Response:
    try:
        score = float(req.query("score", "0"))
    except ValueError:
        score = 0.0
    svg = _badges.generate_quality_badge(score)
    return Response(svg, content_type="image/svg+xml")


@app.route("/api/badge/security/{owner}/{repo}", methods=["GET"])
def badge_security(req: Request, owner: str = "", repo: str = "") -> Response:
    try:
        vulns = int(req.query("vulns", "0"))
    except ValueError:
        vulns = 0
    svg = _badges.generate_security_badge(vulns)
    return Response(svg, content_type="image/svg+xml")


@app.route("/api/blockchain/add", methods=["POST"])
def blockchain_add(req: Request) -> Response:
    data = req.json() or {}
    block = _ledger.add_block(data)
    return Response({
        "index": block.index, "hash": block.hash,
        "timestamp": block.timestamp
    }, status_code=201)


@app.route("/api/blockchain/status", methods=["GET"])
def blockchain_status(req: Request) -> Response:
    return Response({
        "length": _ledger.get_chain_length(),
        "valid": _ledger.validate_chain(),
        "genesis_hash": _ledger.get_block(0).hash if _ledger.get_chain_length() > 0 else None,
    })


def run_server() -> None:
    config = get_config()
    app.run(host=config.host, port=config.port)


# ---------------------------------------------------------------------------
# Analysis routes
# ---------------------------------------------------------------------------

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
    return Response({"results": results, "score": score, "file_count": len(results)})


@app.route("/api/analysis/tests", methods=["POST"])
def analysis_tests(req: Request) -> Response:
    body = req.json() or {}
    source_path = body.get("source_path", ".")
    import os
    gen = TestGenerator()
    suggestions_list = []
    if os.path.isfile(source_path):
        suggestions_list.append(gen.get_suggestions(source_path))
    else:
        for root, _dirs, files in os.walk(source_path):
            for fname in files:
                if fname.endswith(".py"):
                    suggestions_list.append(gen.get_suggestions(os.path.join(root, fname)))
    return Response({"results": suggestions_list, "file_count": len(suggestions_list)})


@app.route("/api/analysis/comprehensive", methods=["POST"])
def analysis_comprehensive(req: Request) -> Response:
    body = req.json() or {}
    source_path = body.get("source_path", ".")
    collector = ComprehensiveAnalysisCollector(source_path, _graph)
    evidence_list = collector.collect()
    return Response({
        "evidence_collected": len(evidence_list),
        "evidence_ids": [e.id for e in evidence_list],
    })


# ---------------------------------------------------------------------------
# Assurance routes
# ---------------------------------------------------------------------------

@app.route("/api/assurance/templates", methods=["GET"])
def assurance_templates(req: Request) -> Response:
    return Response({"templates": _template_library.list_templates()})


@app.route("/api/assurance/create", methods=["POST"])
def assurance_create(req: Request) -> Response:
    body = req.json() or {}
    project_name = body.get("project_name", "Unnamed Project")
    project_type = body.get("project_type", "general")
    template_name = body.get("template", "comprehensive_quality")
    description = body.get("description", "")

    tpl = _template_library.get_template(template_name)
    if tpl is None:
        return Response({"error": f"Template '{template_name}' not found"}, status_code=400)

    builder = AssuranceCaseBuilder(
        title=f"{project_name} Assurance Case",
        description=description or f"Quality assurance for {project_name}",
        project_type=project_type,
    )
    tpl.instantiate(builder, {"project_name": project_name})
    case = builder.build()
    _assurance_cases[case.case_id] = case
    return Response({"case_id": case.case_id, "title": case.title,
                     "node_count": len(case.nodes)}, status_code=201)


@app.route("/api/assurance/{case_id}", methods=["GET"])
def assurance_get(req: Request, case_id: str = "") -> Response:
    case = _assurance_cases.get(case_id)
    if case is None:
        return Response({"error": "Assurance case not found"}, status_code=404)
    include_nodes = req.query("include_nodes", "false").lower() in ("1", "true", "yes")
    data = case.to_dict() if include_nodes else {
        "case_id": case.case_id,
        "title": case.title,
        "description": case.description,
        "project_type": case.project_type,
        "node_count": len(case.nodes),
        "root_goal_id": case.root_goal_id,
    }
    return Response(data)


@app.route("/api/assurance/{case_id}/visualize", methods=["GET"])
def assurance_visualize(req: Request, case_id: str = "") -> Response:
    case = _assurance_cases.get(case_id)
    if case is None:
        return Response({"error": "Assurance case not found"}, status_code=404)
    fmt = req.query("format", "summary")
    if fmt == "svg":
        svg = _visualizer.to_svg(case)
        return Response(svg, content_type="image/svg+xml")
    if fmt == "dot":
        dot = _visualizer.to_dot(case)
        return Response(dot, content_type="text/plain")
    return Response(_visualizer.generate_summary(case))


@app.route("/api/assurance/auto-generate", methods=["POST"])
def assurance_auto_generate(req: Request) -> Response:
    body = req.json() or {}
    project_name = body.get("project_name", "Auto Project")
    project_type_str = body.get("project_type", "general")
    evidence_ids = body.get("evidence_ids", [])

    try:
        pt = ProjectType(project_type_str)
    except ValueError:
        pt = ProjectType.GENERAL

    instantiator = PatternInstantiator(_template_library, _graph, _store)
    case = instantiator.generate_from_evidence(project_name, evidence_ids)
    _assurance_cases[case.case_id] = case
    return Response({"case_id": case.case_id, "title": case.title,
                     "node_count": len(case.nodes)}, status_code=201)


if __name__ == "__main__":
    run_server()
