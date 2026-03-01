"""Unit tests for TestGenerator."""

import os
import tempfile
import pytest

from civ_arcos.analysis.test_generator import TestGenerator


def _write_tmp(content: str, suffix: str = ".py") -> str:
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w")
    f.write(content)
    f.close()
    return f.name


def test_analyze_source_finds_functions():
    src = "def foo(x):\n    return x\n\ndef bar():\n    pass\n"
    path = _write_tmp(src)
    try:
        result = TestGenerator().analyze_source(path)
        names = [f["name"] for f in result["functions"]]
        assert "foo" in names
        assert "bar" in names
    finally:
        os.unlink(path)


def test_generate_test_template_function():
    tpl = TestGenerator().generate_test_template("my_func", ["a", "b"])
    assert "def test_my_func" in tpl
    assert "my_func" in tpl


def test_generate_test_template_method():
    tpl = TestGenerator().generate_test_template(
        "my_method", ["self", "x"], class_name="MyClass"
    )
    assert "def test_my_method" in tpl
    assert "MyClass()" in tpl
    assert "instance.my_method" in tpl


def test_get_suggestions_returns_dict():
    src = "def uncovered_func(a, b):\n    return a + b\n"
    path = _write_tmp(src)
    try:
        suggestions = TestGenerator().get_suggestions(path)
        assert "functions_found" in suggestions
        assert "total_test_suggestions" in suggestions
        assert isinstance(suggestions["suggestions"], list)
    finally:
        os.unlink(path)


def test_generate_test_file_contains_import():
    src = "def hello():\n    return 'world'\n"
    path = _write_tmp(src)
    try:
        content = TestGenerator().generate_test_file(path)
        assert "import pytest" in content
        assert "def test_hello" in content
    finally:
        os.unlink(path)


def test_get_suggestions_ai_opt_in_without_env_uses_fallback_backend(monkeypatch):
    monkeypatch.delenv("CIV_AI_ENABLE", raising=False)
    src = "def uncovered_func(a, b):\n    return a + b\n"
    path = _write_tmp(src)
    try:
        suggestions = TestGenerator(use_ai=True, llm_backend="azure_openai").get_suggestions(path)
        assert suggestions["ai_enabled"] is False
        assert suggestions["ai_backend"] == "mock"
    finally:
        os.unlink(path)
