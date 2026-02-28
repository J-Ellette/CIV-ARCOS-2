"""Pattern instantiator: create AssuranceCases from project types."""

from enum import Enum
from typing import Any, Dict, List, Optional

from civ_arcos.assurance.case import AssuranceCase, AssuranceCaseBuilder
from civ_arcos.assurance.templates import TemplateLibrary
from civ_arcos.storage.graph import EvidenceGraph
from civ_arcos.evidence.collector import EvidenceStore


class ProjectType(Enum):
    WEB_APP = "web_app"
    API = "api"
    LIBRARY = "library"
    MOBILE_APP = "mobile_app"
    CLI_TOOL = "cli_tool"
    MICROSERVICE = "microservice"
    DESKTOP_APP = "desktop_app"
    GENERAL = "general"


# Which templates to apply per project type
_PROJECT_TEMPLATES: Dict[str, List[str]] = {
    ProjectType.WEB_APP.value: ["code_quality", "security_assurance", "test_coverage"],
    ProjectType.API.value: [
        "code_quality",
        "security_assurance",
        "test_coverage",
        "maintainability",
    ],
    ProjectType.LIBRARY.value: ["code_quality", "test_coverage", "maintainability"],
    ProjectType.MOBILE_APP.value: [
        "code_quality",
        "security_assurance",
        "test_coverage",
    ],
    ProjectType.CLI_TOOL.value: ["code_quality", "test_coverage"],
    ProjectType.MICROSERVICE.value: [
        "code_quality",
        "security_assurance",
        "test_coverage",
    ],
    ProjectType.DESKTOP_APP.value: ["code_quality", "test_coverage", "maintainability"],
    ProjectType.GENERAL.value: ["comprehensive_quality"],
}


class PatternInstantiator:
    def __init__(
        self,
        template_library: Optional[TemplateLibrary] = None,
        graph: Optional[EvidenceGraph] = None,
        evidence_store: Optional[EvidenceStore] = None,
    ) -> None:
        self._library = template_library or TemplateLibrary()
        self._graph = graph
        self._store = evidence_store

    def instantiate_for_project(
        self, project_name: str, project_type: "ProjectType | str"
    ) -> AssuranceCase:
        if isinstance(project_type, ProjectType):
            pt_value = project_type.value
        else:
            pt_value = str(project_type)

        template_names = _PROJECT_TEMPLATES.get(pt_value, ["comprehensive_quality"])
        ctx = {"project_name": project_name}

        builder = AssuranceCaseBuilder(
            title=f"{project_name} Assurance Case",
            description=f"Quality assurance for {project_name}",
            project_type=pt_value,
        )
        # Use first template as primary (sets root), rest add supplementary nodes
        for i, tname in enumerate(template_names):
            tpl = self._library.get_template(tname)
            if tpl:
                if i == 0:
                    tpl.instantiate(builder, ctx)
                else:
                    # Add supplementary goals linked to root
                    sub_builder = AssuranceCaseBuilder()
                    tpl.instantiate(sub_builder, ctx)
                    sub_case = sub_builder.build()
                    for node in sub_case.nodes.values():
                        builder._case.add_node(node)
                    # Link to existing root
                    root_id = builder._case.root_goal_id
                    if root_id and sub_case.root_goal_id:
                        builder._case.link_nodes(root_id, sub_case.root_goal_id)

        return builder.build()

    def instantiate_and_link_evidence(
        self,
        project_name: str,
        project_type: "ProjectType | str",
        evidence_filters: Optional[Dict[str, Any]] = None,
    ) -> AssuranceCase:
        case = self.instantiate_for_project(project_name, project_type)
        if self._store:
            evidence_list = self._store.list_evidence()
            filters = evidence_filters or {}
            ev_type_filter = filters.get("type")
            for ev in evidence_list:
                if ev_type_filter and ev.type != ev_type_filter:
                    continue
                root = case.get_root_goal()
                if root:
                    case.link_evidence(root.id, ev.id)
        return case

    def generate_from_evidence(
        self, project_name: str, evidence_ids: Optional[List[str]] = None
    ) -> AssuranceCase:
        evidence_ids = evidence_ids or []
        # Infer project type from evidence
        project_type = ProjectType.GENERAL
        if self._store:
            types_seen = set()
            for eid in evidence_ids:
                ev = self._store.get_evidence(eid)
                if ev:
                    types_seen.add(ev.type)
            if "security_scan" in types_seen:
                project_type = ProjectType.API
            elif "coverage" in types_seen:
                project_type = ProjectType.LIBRARY

        case = self.instantiate_for_project(project_name, project_type)
        root = case.get_root_goal()
        if root:
            for eid in evidence_ids:
                case.link_evidence(root.id, eid)
        return case
