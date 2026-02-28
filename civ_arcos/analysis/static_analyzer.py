"""Static code analysis using Python's AST module."""

import ast
import math
from typing import Any, Dict, List

from civ_arcos.utils import iter_python_files


def _cyclomatic_complexity(tree: ast.AST) -> int:
    """Count cyclomatic complexity: 1 + decision points."""
    complexity_count = 1
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.Assert)
        ):
            complexity_count += 1
        elif isinstance(node, ast.BoolOp):
            # each 'and'/'or' adds (len(values)-1) branches
            complexity_count += len(node.values) - 1
        elif isinstance(node, (ast.comprehension,)):
            complexity_count += 1
    return complexity_count


def _function_complexity(func_node: ast.AST) -> int:
    complexity_count = 1
    for node in ast.walk(func_node):
        if node is func_node:
            continue
        if isinstance(
            node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.Assert)
        ):
            complexity_count += 1
        elif isinstance(node, ast.BoolOp):
            complexity_count += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            complexity_count += 1
    return complexity_count


def _nesting_depth(node: ast.AST) -> int:
    """Compute maximum nesting depth within a node."""
    nesting_types = (
        ast.If,
        ast.For,
        ast.While,
        ast.With,
        ast.Try,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
    )

    def _depth(ast_node: ast.AST, current_depth: int) -> int:
        max_depth = current_depth
        for child in ast.iter_child_nodes(ast_node):
            if isinstance(child, nesting_types):
                max_depth = max(max_depth, _depth(child, current_depth + 1))
            else:
                max_depth = max(max_depth, _depth(child, current_depth))
        return max_depth

    return _depth(node, 0)


def _collect_names(tree: ast.AST) -> List[str]:
    names: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
    return names


class StaticAnalyzer:
    """Analyze Python source files using the AST module."""

    def analyze_file(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read()
        except OSError as exc:
            return {"file": path, "error": str(exc)}

        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as exc:
            return {"file": path, "error": f"SyntaxError: {exc}"}

        lines = source.splitlines()
        lines_of_code = len(lines)

        # --- per-function and per-class info (single AST walk) ---------------
        functions: List[Dict[str, Any]] = []
        classes: List[Dict[str, Any]] = []
        code_smells: List[Dict[str, Any]] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = getattr(node, "end_lineno", start)
                func_lines = end - start + 1
                params = [a.arg for a in node.args.args]
                complexity = _function_complexity(node)
                functions.append(
                    {
                        "name": node.name,
                        "complexity": complexity,
                        "lines": func_lines,
                        "params": params,
                        "lineno": start,
                    }
                )
                if func_lines > 50:
                    code_smells.append(
                        {
                            "type": "long_function",
                            "description": f"Function '{node.name}' is {func_lines} lines (>50)",
                            "line": start,
                        }
                    )
                if len(params) > 5:
                    code_smells.append(
                        {
                            "type": "too_many_params",
                            "description": f"Function '{node.name}' has {len(params)} parameters (>5)",
                            "line": start,
                        }
                    )
                depth = _nesting_depth(node)
                if depth > 4:
                    code_smells.append(
                        {
                            "type": "deep_nesting",
                            "description": f"Function '{node.name}' has nesting depth {depth} (>4)",
                            "line": start,
                        }
                    )
            elif isinstance(node, ast.ClassDef):
                start = node.lineno
                end = getattr(node, "end_lineno", start)
                class_lines = end - start + 1
                classes.append(
                    {"name": node.name, "lines": class_lines, "lineno": start}
                )
                if class_lines > 500:
                    code_smells.append(
                        {
                            "type": "large_class",
                            "description": f"Class '{node.name}' is {class_lines} lines (>500)",
                            "line": start,
                        }
                    )

        # --- file-level complexity -------------------------------------------
        complexity = _cyclomatic_complexity(tree)

        # --- maintainability index -------------------------------------------
        operands = _collect_names(tree)
        unique_count = len(set(operands)) if operands else 1
        halstead_volume = (
            unique_count * math.log2(unique_count + 1) if unique_count > 0 else 1
        )
        safe_lines_of_code = max(1, lines_of_code)
        # Maintainability Index based on the SEI (Software Engineering Institute) formula:
        # MI = max(0, (171 - 5.2*ln(HV) - 0.23*CC - 16.2*ln(LOC)) * 100/171)
        # where HV = Halstead Volume (approximated), CC = cyclomatic complexity, LOC = lines of code
        raw_maintainability_index = (
            171
            - 5.2 * math.log(halstead_volume)
            - 0.23 * complexity
            - 16.2 * math.log(safe_lines_of_code)
        )
        maintainability_index = max(0.0, raw_maintainability_index * 100 / 171)

        return {
            "file": path,
            "complexity": complexity,
            "maintainability_index": round(maintainability_index, 2),
            "loc": lines_of_code,
            "functions": functions,
            "classes": classes,
            "code_smells": code_smells,
        }

    def analyze_directory(self, path: str) -> List[Dict[str, Any]]:
        return [self.analyze_file(fpath) for fpath in iter_python_files(path)]
