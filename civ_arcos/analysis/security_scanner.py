"""Security vulnerability scanner using regex pattern matching."""

import re
from typing import Any, Dict, List

from civ_arcos.utils import iter_python_files

# Patterns and their metadata
_PATTERNS = [
    (
        "SQL_INJECTION",
        re.compile(
            r'(execute|cursor)\s*\(\s*["\'].*%' r'|(execute|cursor)\s*\(\s*f["\']',
            re.IGNORECASE,
        ),
        "CRITICAL",
        "Potential SQL injection via string formatting",
    ),
    (
        "COMMAND_INJECTION",
        re.compile(
            r"subprocess.*shell\s*=\s*True"
            r"|os\.system\s*\("
            r"|eval\s*\("
            r"|exec\s*\(",
            re.IGNORECASE,
        ),
        "CRITICAL",
        "Potential command injection",
    ),
    (
        "HARDCODED_SECRET",
        re.compile(
            r'(password|secret|api_key|token|passwd)\s*=\s*["\'][^"\']{6,}["\']',
            re.IGNORECASE,
        ),
        "HIGH",
        "Hardcoded credential or secret",
    ),
    (
        "INSECURE_FUNCTION",
        re.compile(r"\bpickle\.loads?\b|\byaml\.load\s*\("),
        "MEDIUM",
        "Use of insecure deserialization function",
    ),
    (
        "BARE_EXCEPT",
        re.compile(r"except\s*:"),
        "LOW",
        "Bare except clause hides errors",
    ),
]

_SKIP_COMMENT = re.compile(r"#\s*(example|placeholder)", re.IGNORECASE)

_SEVERITY_DEDUCTION = {
    "CRITICAL": 20,
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 2,
}


class SecurityScanner:
    """Scan Python source files for common security vulnerabilities."""

    def scan_file(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError as exc:
            return {
                "file": path,
                "vulnerabilities": [],
                "vulnerability_count": 0,
                "error": str(exc),
            }

        vulnerabilities: List[Dict[str, Any]] = []
        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()
            if _SKIP_COMMENT.search(stripped):
                continue
            for vuln_type, pattern, severity, description in _PATTERNS:
                if pattern.search(stripped):
                    vulnerabilities.append(
                        {
                            "type": vuln_type,
                            "severity": severity,
                            "description": description,
                            "line": lineno,
                            "code": stripped,
                        }
                    )

        return {
            "file": path,
            "vulnerabilities": vulnerabilities,
            "vulnerability_count": len(vulnerabilities),
        }

    def scan_directory(self, path: str) -> List[Dict[str, Any]]:
        return [self.scan_file(fpath) for fpath in iter_python_files(path)]

    def calculate_security_score(
        self, scan_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        breakdown: Dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for result in scan_results:
            for vuln in result.get("vulnerabilities", []):
                sev = vuln.get("severity", "LOW")
                breakdown[sev] = breakdown.get(sev, 0) + 1

        deduction = (
            breakdown["CRITICAL"] * 20
            + breakdown["HIGH"] * 10
            + breakdown["MEDIUM"] * 5
            + breakdown["LOW"] * 2
        )
        score = max(0, 100 - deduction)
        return {
            "score": score,
            "breakdown": breakdown,
            "total_vulnerabilities": sum(breakdown.values()),
        }
