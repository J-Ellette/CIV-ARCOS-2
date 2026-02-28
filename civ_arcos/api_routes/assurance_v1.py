"""Versioned assurance API routes and contract registry endpoint."""

from __future__ import annotations

from typing import Any, Callable, Dict

from civ_arcos.assurance.case import AssuranceCaseBuilder
from civ_arcos.assurance.patterns import PatternInstantiator, ProjectType
from civ_arcos.assurance.templates import TemplateLibrary
from civ_arcos.contracts.v1 import (
    assurance_auto_generate_contract,
    assurance_detail_contract,
    assurance_list_contract,
    assurance_templates_contract,
    contracts_registry,
)
from civ_arcos.evidence.collector import EvidenceStore
from civ_arcos.storage.graph import EvidenceGraph
from civ_arcos.web.framework import Application, Request, Response


def register_assurance_v1_routes(
    app: Application,
    assurance_cases: Dict[str, Any],
    template_library: TemplateLibrary,
    graph: EvidenceGraph,
    store: EvidenceStore,
    idempotency_precheck: Callable[[Request], Response | None],
    idempotency_store: Callable[[Request, Response], None],
) -> None:
    """Register ``/api/v1/assurance`` and contract discovery endpoints."""

    @app.route("/api/v1/contracts", methods=["GET"])
    def contracts_v1(req: Request) -> Response:
        return Response(contracts_registry())

    @app.route("/api/v1/assurance", methods=["GET"])
    def assurance_list_v1(req: Request) -> Response:
        cases = list(assurance_cases.values())
        return Response(assurance_list_contract(cases))

    @app.route("/api/v1/assurance/templates", methods=["GET"])
    def assurance_templates_v1(req: Request) -> Response:
        templates = template_library.list_templates()
        return Response(
            assurance_templates_contract(
                {
                    "count": len(templates),
                    "templates": templates,
                }
            )
        )

    @app.route("/api/v1/assurance/create", methods=["POST"])
    def assurance_create_v1(req: Request) -> Response:
        replay_resp = idempotency_precheck(req)
        if replay_resp is not None:
            return replay_resp

        body = req.json() or {}
        project_name = body.get("project_name", "Unnamed Project")
        project_type = body.get("project_type", "general")
        template_name = body.get("template", "comprehensive_quality")
        description = body.get("description", "")

        tpl = template_library.get_template(template_name)
        if tpl is None:
            return Response(
                {"error": f"Template '{template_name}' not found"},
                status_code=400,
            )

        builder = AssuranceCaseBuilder(
            title=f"{project_name} Assurance Case",
            description=description or f"Quality assurance for {project_name}",
            project_type=project_type,
        )
        tpl.instantiate(builder, {"project_name": project_name})
        case = builder.build()
        assurance_cases[case.case_id] = case

        response = Response(assurance_detail_contract(case), status_code=201)
        idempotency_store(req, response)
        return response

    @app.route("/api/v1/assurance/auto-generate", methods=["POST"])
    def assurance_auto_generate_v1(req: Request) -> Response:
        replay_resp = idempotency_precheck(req)
        if replay_resp is not None:
            return replay_resp

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

        response = Response(
            assurance_auto_generate_contract(
                {
                    "case": {
                        "case_id": case.case_id,
                        "title": case.title,
                        "node_count": len(case.nodes),
                    }
                }
            ),
            status_code=201,
        )
        idempotency_store(req, response)
        return response

    @app.route("/api/v1/assurance/{case_id}", methods=["GET"])
    def assurance_get_v1(req: Request, case_id: str = "") -> Response:
        case = assurance_cases.get(case_id)
        if case is None:
            return Response({"error": "Assurance case not found"}, status_code=404)
        return Response(assurance_detail_contract(case))
