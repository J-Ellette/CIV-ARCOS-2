"""Unit tests for assurance templates and TemplateLibrary."""
import pytest
from civ_arcos.assurance.templates import (
    TemplateLibrary, CodeQualityTemplate, TestCoverageTemplate,
    SecurityAssuranceTemplate, ComprehensiveQualityTemplate,
)
from civ_arcos.assurance.case import AssuranceCaseBuilder


def test_template_library_lists_templates():
    lib = TemplateLibrary()
    templates = lib.list_templates()
    assert len(templates) >= 4
    names = [t["name"] for t in templates]
    assert "code_quality" in names
    assert "security_assurance" in names


def test_get_template_by_name():
    lib = TemplateLibrary()
    tpl = lib.get_template("code_quality")
    assert tpl is not None
    assert tpl.name == "code_quality"


def test_code_quality_template_instantiates():
    tpl = CodeQualityTemplate()
    builder = AssuranceCaseBuilder(title="CQ Test")
    tpl.instantiate(builder, {"project_name": "MyApp"})
    case = builder.build()
    assert case.root_goal_id is not None
    assert len(case.nodes) >= 4


def test_security_assurance_template_instantiates():
    tpl = SecurityAssuranceTemplate()
    builder = AssuranceCaseBuilder(title="Sec Test")
    tpl.instantiate(builder, {"project_name": "MyApp"})
    case = builder.build()
    assert any(n.node_type.value == "solution" for n in case.nodes.values())


def test_comprehensive_quality_template_combines():
    tpl = ComprehensiveQualityTemplate()
    builder = AssuranceCaseBuilder(title="Comp Test")
    tpl.instantiate(builder, {"project_name": "MyApp"})
    case = builder.build()
    # Should have nodes from multiple sub-templates
    assert len(case.nodes) > 8


def test_add_custom_template():
    lib = TemplateLibrary()
    tpl = CodeQualityTemplate()
    lib.add_template("my_custom", tpl)
    assert lib.get_template("my_custom") is not None
