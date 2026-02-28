"""Plugin validation and sandbox execution primitives.

This module introduces a formal boundary for plugin execution:

- Static validation via AST checks and forbidden import rules.
- Runtime isolation using a dedicated Python subprocess (`-I` isolated mode).
- Wall-clock timeout and bounded stdout/stderr capture.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

FORBIDDEN_IMPORT_ROOTS = {
    "subprocess",
    "socket",
    "ctypes",
    "multiprocessing",
}


@dataclass
class PluginValidationResult:
    """Outcome of static plugin source validation."""

    valid: bool
    checksum: str
    errors: List[str]


@dataclass
class PluginExecutionResult:
    """Outcome of isolated plugin function execution."""

    success: bool
    result: Any
    error: str
    timed_out: bool
    stdout: str
    stderr: str


class PluginValidator:
    """Perform AST-based static safety checks on plugin source code."""

    def __init__(
        self,
        forbidden_import_roots: Optional[Iterable[str]] = None,
    ) -> None:
        roots = forbidden_import_roots or FORBIDDEN_IMPORT_ROOTS
        self._forbidden_roots = set(roots)

    @staticmethod
    def checksum(code: str) -> str:
        """Return SHA256 digest of plugin code."""
        return hashlib.sha256(code.encode()).hexdigest()

    def validate(self, code: str) -> PluginValidationResult:
        """Validate plugin source and return structured diagnostics."""
        errors: List[str] = []

        if not code.strip():
            errors.append("Plugin code is empty")
            return PluginValidationResult(
                valid=False,
                checksum=self.checksum(code),
                errors=errors,
            )

        try:
            parsed = ast.parse(code)
        except SyntaxError as exc:
            errors.append(f"Syntax error: {exc}")
            return PluginValidationResult(
                valid=False,
                checksum=self.checksum(code),
                errors=errors,
            )

        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in self._forbidden_roots:
                        errors.append(f"Forbidden import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    if root in self._forbidden_roots:
                        errors.append(f"Forbidden import: {node.module}")

        return PluginValidationResult(
            valid=len(errors) == 0,
            checksum=self.checksum(code),
            errors=errors,
        )


class PluginSandbox:
    """Execute plugin functions in an isolated subprocess.

    Notes
    -----
    This is a practical isolation boundary using process separation and
    timeout constraints. It is intentionally conservative and designed for
    deterministic plugin utility functions that exchange JSON-compatible data.
    """

    def __init__(
        self,
        timeout_secs: float = 2.0,
        max_output_bytes: int = 8192,
    ) -> None:
        self.timeout_secs = timeout_secs
        self.max_output_bytes = max_output_bytes

    @staticmethod
    def _runner_script() -> str:
        """Generate the isolated runner source script."""
        return (
            "import importlib.util, json, sys\n"
            "plugin_path, function_name, kwargs_json = sys.argv[1], sys.argv[2], sys.argv[3]\n"
            "kwargs = json.loads(kwargs_json)\n"
            "spec = importlib.util.spec_from_file_location('plugin_module', plugin_path)\n"
            "if spec is None or spec.loader is None:\n"
            "    print(json.dumps({'ok': False, 'error': 'Could not load plugin module'}))\n"
            "    raise SystemExit(0)\n"
            "module = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(module)\n"
            "fn = getattr(module, function_name, None)\n"
            "if fn is None:\n"
            "    print(json.dumps({'ok': False, 'error': f'Missing function: {function_name}'}))\n"
            "    raise SystemExit(0)\n"
            "try:\n"
            "    result = fn(**kwargs)\n"
            "    print(json.dumps({'ok': True, 'result': result}))\n"
            "except Exception as exc:\n"
            "    print(json.dumps({'ok': False, 'error': str(exc)}))\n"
        )

    def execute(
        self,
        code: str,
        function_name: str,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> PluginExecutionResult:
        """Run a plugin function in a separate Python process."""
        payload = kwargs or {}
        with tempfile.TemporaryDirectory(prefix="civ_arcos_plugin_") as tmp_dir:
            plugin_path = Path(tmp_dir) / "plugin.py"
            plugin_path.write_text(code, encoding="utf-8")

            cmd = [
                sys.executable,
                "-I",
                "-c",
                self._runner_script(),
                str(plugin_path),
                function_name,
                json.dumps(payload),
            ]

            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_secs,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return PluginExecutionResult(
                    success=False,
                    result=None,
                    error="Plugin execution timed out",
                    timed_out=True,
                    stdout="",
                    stderr="",
                )

            stdout = (proc.stdout or "")[: self.max_output_bytes]
            stderr = (proc.stderr or "")[: self.max_output_bytes]
            line = ""
            for candidate in reversed(stdout.strip().splitlines()):
                if candidate.strip():
                    line = candidate.strip()
                    break

            if not line:
                return PluginExecutionResult(
                    success=False,
                    result=None,
                    error="Plugin returned no result payload",
                    timed_out=False,
                    stdout=stdout,
                    stderr=stderr,
                )

            try:
                decoded = json.loads(line)
            except json.JSONDecodeError:
                return PluginExecutionResult(
                    success=False,
                    result=None,
                    error="Plugin returned invalid JSON payload",
                    timed_out=False,
                    stdout=stdout,
                    stderr=stderr,
                )

            if decoded.get("ok") is True:
                return PluginExecutionResult(
                    success=True,
                    result=decoded.get("result"),
                    error="",
                    timed_out=False,
                    stdout=stdout,
                    stderr=stderr,
                )

            return PluginExecutionResult(
                success=False,
                result=None,
                error=str(decoded.get("error", "Plugin execution failed")),
                timed_out=False,
                stdout=stdout,
                stderr=stderr,
            )
