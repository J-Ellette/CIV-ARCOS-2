"""Test template generation and untested function detection."""
import ast
import os
from typing import Any, Dict, List, Optional


def _parse_functions_and_classes(path: str):
    """Return (functions, classes) lists from a Python source file."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            source = fh.read()
        tree = ast.parse(source, filename=path)
    except (OSError, SyntaxError):
        return [], []

    functions: List[Dict[str, Any]] = []
    classes: List[Dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # skip private/dunder at module level unless inside class
            params = [a.arg for a in node.args.args]
            functions.append({"name": node.name, "params": params, "lineno": node.lineno})
        elif isinstance(node, ast.ClassDef):
            methods = [
                {"name": n.name, "params": [a.arg for a in n.args.args]}
                for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n is not node
            ]
            classes.append({"name": node.name, "methods": methods, "lineno": node.lineno})

    return functions, classes


def _gather_tested_names(source_path: str) -> set:
    """Find test function names in the tests/ directory or sibling test files."""
    tested: set = set()
    base_dir = os.path.dirname(os.path.abspath(source_path))
    root = base_dir
    # Walk up to find a tests/ directory
    for _ in range(5):
        candidate = os.path.join(root, "tests")
        if os.path.isdir(candidate):
            for dirpath, _dirs, files in os.walk(candidate):
                for fname in files:
                    if fname.endswith(".py"):
                        _collect_test_names(os.path.join(dirpath, fname), tested)
            break
        root = os.path.dirname(root)

    # Also check sibling test files
    module_stem = os.path.splitext(os.path.basename(source_path))[0]
    for name in (f"test_{module_stem}.py", f"{module_stem}_test.py"):
        candidate = os.path.join(base_dir, name)
        if os.path.isfile(candidate):
            _collect_test_names(candidate, tested)

    return tested


def _collect_test_names(path: str, tested: set) -> None:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            source = fh.read()
        tree = ast.parse(source, filename=path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                tested.add(node.name)
                # strip 'test_' prefix to infer target name
                if node.name.startswith("test_"):
                    tested.add(node.name[5:])
    except (OSError, SyntaxError):
        pass


class TestGenerator:
    """Generate pytest test templates for Python source files."""

    def analyze_source(self, path: str) -> Dict[str, Any]:
        functions, classes = _parse_functions_and_classes(path)
        tested = _gather_tested_names(path)

        untested_functions = [f for f in functions if f["name"] not in tested
                              and not f["name"].startswith("_")]
        untested_classes = [c for c in classes if c["name"] not in tested]

        return {
            "functions": functions,
            "classes": classes,
            "untested_functions": untested_functions,
            "untested_classes": untested_classes,
        }

    def generate_test_template(self, func_name: str, params: List[str],
                               class_name: Optional[str] = None) -> str:
        indentation = "    "
        if class_name:
            args = ", ".join("None" for p in params if p != "self")
            lines = [
                f"def test_{func_name}():",
                f"{indentation}instance = {class_name}()",
                f"{indentation}result = instance.{func_name}({args})",
                f"{indentation}assert result is not None  # TODO: add assertions",
            ]
        else:
            args = ", ".join("None" for _ in params)
            lines = [
                f"def test_{func_name}():",
                f"{indentation}result = {func_name}({args})",
                f"{indentation}assert result is not None  # TODO: add assertions",
            ]
        return "\n".join(lines)

    def generate_test_file(self, source_path: str) -> str:
        functions, classes = _parse_functions_and_classes(source_path)
        module_name = os.path.splitext(os.path.basename(source_path))[0]

        header_lines = [
            f'"""Auto-generated tests for {module_name}."""',
            "import pytest",
            f"from {module_name} import *  # noqa: F401,F403",
            "",
            "",
        ]

        templates: List[str] = []
        for func in functions:
            if not func["name"].startswith("_"):
                templates.append(self.generate_test_template(func["name"], func["params"]))
                templates.append("")

        for cls in classes:
            for method in cls.get("methods", []):
                if not method["name"].startswith("_"):
                    templates.append(
                        self.generate_test_template(method["name"], method["params"], cls["name"])
                    )
                    templates.append("")

        return "\n".join(header_lines + templates)

    def get_suggestions(self, path: str) -> Dict[str, Any]:
        analysis = self.analyze_source(path)
        suggestions: List[Dict[str, Any]] = []

        for func in analysis["untested_functions"]:
            suggestions.append({
                "name": func["name"],
                "type": "function",
                "template": self.generate_test_template(func["name"], func["params"]),
            })

        for cls in analysis["untested_classes"]:
            for method in cls.get("methods", []):
                if not method["name"].startswith("_"):
                    suggestions.append({
                        "name": f"{cls['name']}.{method['name']}",
                        "type": "method",
                        "template": self.generate_test_template(
                            method["name"], method["params"], cls["name"]
                        ),
                    })

        return {
            "functions_found": len(analysis["functions"]),
            "classes_found": len(analysis["classes"]),
            "total_test_suggestions": len(suggestions),
            "suggestions": suggestions,
        }
