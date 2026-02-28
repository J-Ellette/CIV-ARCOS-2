"""Legacy assurance domain routes."""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from civ_arcos.assurance.case import AssuranceCaseBuilder
from civ_arcos.assurance.patterns import PatternInstantiator, ProjectType
from civ_arcos.assurance.templates import TemplateLibrary
from civ_arcos.assurance.visualizer import GSNVisualizer
from civ_arcos.evidence.collector import EvidenceStore
from civ_arcos.storage.graph import EvidenceGraph
from civ_arcos.web.framework import Application, Request, Response


def _pdf_escape(text: str) -> str:
    """Escape text for use in a PDF literal string."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _render_simple_pdf(lines: List[str]) -> bytes:
    """Render a compact single-page PDF with plain text lines."""
    text_lines = [f"({_pdf_escape(line)}) Tj" for line in lines]
    stream = "BT\n/F1 12 Tf\n50 780 Td\n" + "\nT*\n".join(text_lines) + "\nET"
    stream_bytes = stream.encode("utf-8")

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        ),
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        (
            b"5 0 obj\n<< /Length "
            + str(len(stream_bytes)).encode("ascii")
            + b" >>\nstream\n"
            + stream_bytes
            + b"\nendstream\nendobj\n"
        ),
    ]

    out = bytearray()
    out.extend(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    out.extend(
        (
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(out)


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

    @app.route("/api/assurance/{case_id}/export", methods=["GET"])
    def assurance_export(req: Request, case_id: str = "") -> Response:
        case = assurance_cases.get(case_id)
        if case is None:
            return Response({"error": "Assurance case not found"}, status_code=404)

        export_format = req.query("format", "pdf").lower()
        if export_format != "pdf":
            return Response(
                {"error": "Unsupported export format. Use format=pdf"},
                status_code=400,
            )

        summary = visualizer.generate_summary(case)
        pdf_bytes = _render_simple_pdf(
            [
                "CIV-ARCOS Assurance Summary",
                f"Case ID: {case.case_id}",
                f"Title: {case.title}",
                f"Project Type: {case.project_type}",
                f"Node Count: {summary['node_count']}",
                f"Evidence Count: {summary['evidence_count']}",
                f"Max Depth: {summary['max_depth']}",
            ]
        )
        return Response(
            pdf_bytes,
            content_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="assurance-{case.case_id}.pdf"'
            },
        )

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
