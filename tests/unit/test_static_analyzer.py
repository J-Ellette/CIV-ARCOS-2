"""Unit tests for StaticAnalyzer."""

import ast
import os
import tempfile
import pytest

from civ_arcos.analysis.static_analyzer import StaticAnalyzer


def _write_tmp(content: str) -> str:
    f = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    f.write(content)
    f.close()
    return f.name


def test_analyze_simple_function():
    src = "def foo(a, b):\n    return a + b\n"
    path = _write_tmp(src)
    try:
        result = StaticAnalyzer().analyze_file(path)
        assert result["file"] == path
        assert len(result["functions"]) == 1
        assert result["functions"][0]["name"] == "foo"
        assert result["complexity"] >= 1
    finally:
        os.unlink(path)


def test_analyze_maintainability_index_range():
    src = "x = 1\ny = 2\n"
    path = _write_tmp(src)
    try:
        result = StaticAnalyzer().analyze_file(path)
        mi = result["maintainability_index"]
        assert 0 <= mi <= 100
    finally:
        os.unlink(path)


def test_analyze_code_smell_long_function():
    body = "    pass\n" * 55
    src = f"def big_func():\n{body}"
    path = _write_tmp(src)
    try:
        result = StaticAnalyzer().analyze_file(path)
        smell_types = [s["type"] for s in result["code_smells"]]
        assert "long_function" in smell_types
    finally:
        os.unlink(path)


def test_analyze_code_smell_too_many_params():
    src = "def f(a, b, c, d, e, f, g):\n    pass\n"
    path = _write_tmp(src)
    try:
        result = StaticAnalyzer().analyze_file(path)
        smell_types = [s["type"] for s in result["code_smells"]]
        assert "too_many_params" in smell_types
    finally:
        os.unlink(path)


def test_analyze_syntax_error_handled():
    src = "def broken(:\n    pass\n"
    path = _write_tmp(src)
    try:
        result = StaticAnalyzer().analyze_file(path)
        assert "error" in result
    finally:
        os.unlink(path)


def test_analyze_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(3):
            with open(os.path.join(tmpdir, f"mod{i}.py"), "w") as fh:
                fh.write(f"x = {i}\n")
        results = StaticAnalyzer().analyze_directory(tmpdir)
        assert len(results) == 3


def test_analyze_class_detected():
    src = "class MyClass:\n    def method(self):\n        pass\n"
    path = _write_tmp(src)
    try:
        result = StaticAnalyzer().analyze_file(path)
        assert any(c["name"] == "MyClass" for c in result["classes"])
    finally:
        os.unlink(path)


def test_cyclomatic_complexity_increases_with_branches():
    src_simple = "def f():\n    return 1\n"
    src_complex = "def f(x):\n    if x > 0:\n        for i in range(x):\n            pass\n    return x\n"
    p1, p2 = _write_tmp(src_simple), _write_tmp(src_complex)
    try:
        r1 = StaticAnalyzer().analyze_file(p1)
        r2 = StaticAnalyzer().analyze_file(p2)
        assert r2["complexity"] > r1["complexity"]
    finally:
        os.unlink(p1)
        os.unlink(p2)
