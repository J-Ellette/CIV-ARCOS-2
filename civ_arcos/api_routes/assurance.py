"""Legacy assurance domain routes."""

from __future__ import annotations

from typing import Any, Callable, Dict

from civ_arcos.assurance.case import AssuranceCaseBuilder
from civ_arcos.assurance.patterns import PatternInstantiator, ProjectType
from civ_arcos.assurance.templates import TemplateLibrary
from civ_arcos.assurance.visualizer import GSNVisualizer
from civ_arcos.evidence.collector import EvidenceStore
from civ_arcos.storage.graph import EvidenceGraph
from civ_arcos.web.framework import Application, Request, Response


def register_assurance_legacy_routes(
    app: Application,
    assurance_cases: Dict[str, Any],
    template_library: TemplateLibrary,
    visualizer: GSNVisualizer,
    graph: EvidenceGraph,
    store: EvidenceStore,
    idempotency_precheck: Callable[[Request], Response | None],
    idempotency_store: Callable[[Request, Response], None],
) -> None:
    """Register legacy assurance routes under ``/api/assurance``."""

    @app.route("/api/assurance", methods=["GET"])
    def assurance_list(req: Request) -> Response:
        cases = [
            {
                "case_id": case.case_id,
                "title": case.title,
                "description": case.description,
                "project_type": case.project_type,
                "node_count": len(case.nodes),
                "root_goal_id": case.root_goal_id,
            }
            for case in assurance_cases.values()
        ]
        return Response({"cases": cases, "count": len(cases)})

    @app.route("/api/assurance/templates", methods=["GET"])
    def assurance_templates(req: Request) -> Response:
        return Response({"templates": template_library.list_templates()})

    @app.route("/api/assurance/create", methods=["POST"])
    def assurance_create(req: Request) -> Response:
        replay_resp = idempotency_precheck(req)
        if replay_resp is not None:
            return replay_resp

        body = req.json() or {}
        project_name = body.get("project_name", "Unnamed Project")
        project_type = body.get("project_type", "general")
        template_name = body.get("template", "comprehensive_quality")
        description = body.get("description", "")

        template = template_library.get_template(template_name)
        if template is None:
            return Response(
                {"error": f"Template '{template_name}' not found"},
                status_code=400,
            )

        builder = AssuranceCaseBuilder(
            title=f"{project_name} Assurance Case",
            description=description or f"Quality assurance for {project_name}",
            project_type=project_type,
        )
        template.instantiate(builder, {"project_name": project_name})
        case = builder.build()
        assurance_cases[case.case_id] = case

        response = Response(
            {
                "case_id": case.case_id,
                "title": case.title,
                "node_count": len(case.nodes),
            },
            status_code=201,
        )
        idempotency_store(req, response)
        return response

    @app.route("/api/assurance/{case_id}", methods=["GET"])
    def assurance_get(req: Request, case_id: str = "") -> Response:
        case = assurance_cases.get(case_id)
        if case is None:
            return Response({"error": "Assurance case not found"}, status_code=404)
        include_nodes = req.query("include_nodes", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        data = (
            case.to_dict()
            if include_nodes
            else {
                "case_id": case.case_id,
                "title": case.title,
                "description": case.description,
                "project_type": case.project_type,
                "node_count": len(case.nodes),
                "root_goal_id": case.root_goal_id,
            }
        )
        return Response(data)

    @app.route("/api/assurance/{case_id}/visualize", methods=["GET"])
    def assurance_visualize(req: Request, case_id: str = "") -> Response:
        case = assurance_cases.get(case_id)
        if case is None:
            return Response({"error": "Assurance case not found"}, status_code=404)
        fmt = req.query("format", "summary")
        if fmt == "svg":
            svg = visualizer.to_svg(case)
            return Response(svg, content_type="image/svg+xml")
        if fmt == "dot":
            dot = visualizer.to_dot(case)
            return Response(dot, content_type="text/plain")
        return Response(visualizer.generate_summary(case))

    @app.route("/api/assurance/auto-generate", methods=["POST"])
    def assurance_auto_generate(req: Request) -> Response:
        body = req.json() or {}
        project_name = body.get("project_name", "Auto Project")
        project_type_str = body.get("project_type", "general")
        evidence_ids = body.get("evidence_ids", [])

        try:
            _ = ProjectType(project_type_str)
        except ValueError:
            project_type_str = ProjectType.GENERAL.value

        instantiator = PatternInstantiator(template_library, graph, store)
        case = instantiator.generate_from_evidence(project_name, evidence_ids)
        assurance_cases[case.case_id] = case
        return Response(
            {
                "case_id": case.case_id,
                "title": case.title,
                "node_count": len(case.nodes),
            },
            status_code=201,
        )
