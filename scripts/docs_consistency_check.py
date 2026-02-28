"""Automated documentation consistency gate for CIV-ARCOS build docs."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "build_docs" / "VERIFICATION_MATRIX.md"
GUIDE_PATH = ROOT / "build_docs" / "build-guide-updated.md"
STATUS_PATH = ROOT / "build_docs" / "STATUS.md"
Q_IDS = ["Q-001", "Q-002", "Q-003", "Q-004", "Q-005"]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _read_text(path: Path) -> str:
    """Read UTF-8 text from a required file path."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def _parse_q_rows(matrix_text: str) -> Dict[str, Dict[str, str]]:
    """Parse Q-row entries from the non-functional verification markdown table."""
    rows: Dict[str, Dict[str, str]] = {}
    for line in matrix_text.splitlines():
        if not line.startswith("| Q-"):
            continue
        parts = [part.strip() for part in line.split("|")[1:-1]]
        if len(parts) < 8:
            continue
        row_id = parts[0]
        rows[row_id] = {
            "method": parts[2],
            "command": parts[3],
            "expected": parts[4],
            "last_verified": parts[5],
            "status": parts[6],
            "notes": parts[7],
        }
    return rows


def _parse_q_checkboxes(guide_text: str) -> Dict[str, bool]:
    """Parse Q-row checklist completion state from the updated build guide."""
    checks: Dict[str, bool] = {}
    for line in guide_text.splitlines():
        match = re.match(r"^- \[(?P<state>[ xX])\] \*\*(?P<qid>Q-\d{3})", line.strip())
        if not match:
            continue
        checks[match.group("qid")] = match.group("state").lower() == "x"
    return checks


def _validate(matrix_rows: Dict[str, Dict[str, str]], checks: Dict[str, bool], status_text: str) -> Tuple[bool, list[str]]:
    """Validate docs consistency constraints for Q rows."""
    errors: list[str] = []

    for qid in Q_IDS:
        if qid not in matrix_rows:
            errors.append(f"Missing matrix row for {qid}.")
            continue

        row = matrix_rows[qid]

        if row["command"] in {"(to be defined)", "", "`(to be defined)`"}:
            errors.append(f"{qid} command is undefined.")

        if not DATE_PATTERN.match(row["last_verified"]):
            errors.append(
                f"{qid} has invalid last-verified date: {row['last_verified']}."
            )

        if qid not in checks:
            if row["status"] in {"FAIL", "PARTIAL"}:
                errors.append(
                    f"Missing checklist line for open item {qid} in build guide."
                )
        else:
            if row["status"] == "PASS" and not checks[qid]:
                errors.append(f"{qid} is PASS in matrix but unchecked in build guide.")
            if row["status"] in {"FAIL", "PARTIAL"} and checks[qid]:
                errors.append(
                    f"{qid} is open in matrix ({row['status']}) but checked in build guide."
                )

    if "Q-005 remediation completed" not in status_text:
        errors.append("STATUS changelog does not include Q-005 remediation entry.")

    return (len(errors) == 0, errors)


def main() -> int:
    """Run docs consistency gate and return process exit code."""
    try:
        matrix_text = _read_text(MATRIX_PATH)
        guide_text = _read_text(GUIDE_PATH)
        status_text = _read_text(STATUS_PATH)
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}")
        return 1

    matrix_rows = _parse_q_rows(matrix_text)
    checks = _parse_q_checkboxes(guide_text)
    ok, errors = _validate(matrix_rows, checks, status_text)

    if not ok:
        print("FAIL: docs consistency gate failed")
        for err in errors:
            print(f"- {err}")
        return 1

    print("PASS: docs consistency gate passed")
    print("- Verified Q-001..Q-005 matrix rows, checklist parity, and status changelog link")
    return 0


if __name__ == "__main__":
    sys.exit(main())
