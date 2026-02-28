"""Assurance case templates for common quality scenarios."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from civ_arcos.assurance.case import AssuranceCaseBuilder, AssuranceCase


class AssuranceTemplate(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    def display_name(self) -> str:
        return self.name.replace("_", " ").title()

    @property
    def description(self) -> str:
        return ""

    @property
    def category(self) -> str:
        return "general"

    @abstractmethod
    def instantiate(self, builder: AssuranceCaseBuilder,
                    context: Optional[Dict[str, Any]] = None) -> AssuranceCaseBuilder:
        ...


class CodeQualityTemplate(AssuranceTemplate):
    @property
    def name(self) -> str:
        return "code_quality"

    @property
    def display_name(self) -> str:
        return "Code Quality"

    @property
    def description(self) -> str:
        return "Argues that code meets quality standards (complexity, maintainability, no smells)"

    @property
    def category(self) -> str:
        return "quality"

    def instantiate(self, builder: AssuranceCaseBuilder,
                    context: Optional[Dict[str, Any]] = None) -> AssuranceCaseBuilder:
        ctx = context or {}
        project = ctx.get("project_name", "the system")

        goal_id = "cq_root"
        strat_id = "cq_strat"
        (
            builder
            .add_goal(f"The code of {project} meets quality standards", node_id=goal_id)
            .set_as_root()
            .add_strategy(
                "Argue by demonstrating low complexity, high maintainability, and absence of code smells",
                node_id=strat_id,
            )
            .link_to_parent(goal_id)
            .add_solution("Cyclomatic complexity is within acceptable limits")
            .link_to_parent(strat_id)
            .add_solution("Maintainability index is above threshold")
            .link_to_parent(strat_id)
            .add_solution("No significant code smells detected")
            .link_to_parent(strat_id)
        )
        return builder


class TestCoverageTemplate(AssuranceTemplate):
    @property
    def name(self) -> str:
        return "test_coverage"

    @property
    def display_name(self) -> str:
        return "Test Coverage"

    @property
    def description(self) -> str:
        return "Argues that the system is adequately tested (line/branch coverage, critical functions)"

    @property
    def category(self) -> str:
        return "testing"

    def instantiate(self, builder: AssuranceCaseBuilder,
                    context: Optional[Dict[str, Any]] = None) -> AssuranceCaseBuilder:
        ctx = context or {}
        project = ctx.get("project_name", "the system")

        goal_id = "tc_root"
        strat_id = "tc_strat"
        (
            builder
            .add_goal(f"{project} is adequately tested", node_id=goal_id)
            .set_as_root()
            .add_strategy(
                "Argue by demonstrating sufficient line/branch coverage and critical function tests",
                node_id=strat_id,
            )
            .link_to_parent(goal_id)
            .add_solution("Line coverage meets minimum threshold (≥80%)")
            .link_to_parent(strat_id)
            .add_solution("Branch coverage meets minimum threshold (≥70%)")
            .link_to_parent(strat_id)
            .add_solution("All critical functions have corresponding tests")
            .link_to_parent(strat_id)
        )
        return builder


class SecurityAssuranceTemplate(AssuranceTemplate):
    @property
    def name(self) -> str:
        return "security_assurance"

    @property
    def display_name(self) -> str:
        return "Security Assurance"

    @property
    def description(self) -> str:
        return "Argues that the system is secure (no critical vulns, no secrets, no SQL injection)"

    @property
    def category(self) -> str:
        return "security"

    def instantiate(self, builder: AssuranceCaseBuilder,
                    context: Optional[Dict[str, Any]] = None) -> AssuranceCaseBuilder:
        ctx = context or {}
        project = ctx.get("project_name", "the system")

        goal_id = "sec_root"
        strat_id = "sec_strat"
        (
            builder
            .add_goal(f"{project} is free from known security vulnerabilities", node_id=goal_id)
            .set_as_root()
            .add_strategy(
                "Argue by demonstrating absence of OWASP Top-10 vulnerabilities via automated scanning",
                node_id=strat_id,
            )
            .link_to_parent(goal_id)
            .add_solution("No critical vulnerabilities (SQL injection, command injection)")
            .link_to_parent(strat_id)
            .add_solution("No hardcoded secrets or credentials")
            .link_to_parent(strat_id)
            .add_solution("No use of insecure deserialization functions")
            .link_to_parent(strat_id)
        )
        return builder


class MaintainabilityTemplate(AssuranceTemplate):
    @property
    def name(self) -> str:
        return "maintainability"

    @property
    def display_name(self) -> str:
        return "Maintainability"

    @property
    def description(self) -> str:
        return "Argues that the system is maintainable (complexity, style, docs)"

    @property
    def category(self) -> str:
        return "quality"

    def instantiate(self, builder: AssuranceCaseBuilder,
                    context: Optional[Dict[str, Any]] = None) -> AssuranceCaseBuilder:
        ctx = context or {}
        project = ctx.get("project_name", "the system")

        goal_id = "maint_root"
        strat_id = "maint_strat"
        (
            builder
            .add_goal(f"{project} is maintainable and understandable", node_id=goal_id)
            .set_as_root()
            .add_strategy(
                "Argue by demonstrating low complexity, consistent style, and documentation",
                node_id=strat_id,
            )
            .link_to_parent(goal_id)
            .add_solution("Functions have low cyclomatic complexity")
            .link_to_parent(strat_id)
            .add_solution("Code follows consistent style guidelines")
            .link_to_parent(strat_id)
            .add_solution("Public API is documented with docstrings")
            .link_to_parent(strat_id)
        )
        return builder


class ComprehensiveQualityTemplate(AssuranceTemplate):
    @property
    def name(self) -> str:
        return "comprehensive_quality"

    @property
    def display_name(self) -> str:
        return "Comprehensive Quality"

    @property
    def description(self) -> str:
        return "Combines code quality, test coverage, security, and maintainability"

    @property
    def category(self) -> str:
        return "comprehensive"

    def instantiate(self, builder: AssuranceCaseBuilder,
                    context: Optional[Dict[str, Any]] = None) -> AssuranceCaseBuilder:
        ctx = context or {}
        project = ctx.get("project_name", "the system")

        root_id = "comp_root"
        builder.add_goal(f"{project} meets comprehensive software quality standards",
                         node_id=root_id).set_as_root()

        for sub_tpl in (CodeQualityTemplate(), TestCoverageTemplate(),
                        SecurityAssuranceTemplate(), MaintainabilityTemplate()):
            sub_ctx = dict(ctx)
            sub_builder = AssuranceCaseBuilder()
            sub_builder = sub_tpl.instantiate(sub_builder, sub_ctx)
            sub_case = sub_builder.build()
            # Merge sub-case nodes into main builder via the public API
            builder.merge_nodes_from(sub_case, link_root_to=root_id)

        return builder


class TemplateLibrary:
    def __init__(self) -> None:
        self._templates: Dict[str, AssuranceTemplate] = {}
        for tpl in (
            CodeQualityTemplate(),
            TestCoverageTemplate(),
            SecurityAssuranceTemplate(),
            MaintainabilityTemplate(),
            ComprehensiveQualityTemplate(),
        ):
            self._templates[tpl.name] = tpl

    def get_template(self, name: str) -> Optional[AssuranceTemplate]:
        return self._templates.get(name)

    def list_templates(self) -> List[Dict[str, str]]:
        return [
            {
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "category": t.category,
            }
            for t in self._templates.values()
        ]

    def add_template(self, name: str, template: AssuranceTemplate) -> None:
        self._templates[name] = template
