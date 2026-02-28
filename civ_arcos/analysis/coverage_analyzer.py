"""Coverage analysis and tier classification."""
import subprocess
import re
from typing import Any, Dict


class CoverageAnalyzer:
    """Analyse test coverage data and assign quality tiers."""

    def get_coverage_tier(self, pct: float) -> str:
        if pct >= 95:
            return "gold"
        if pct >= 80:
            return "silver"
        if pct >= 60:
            return "bronze"
        return "none"

    def analyze_coverage_data(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        lines_covered = coverage_data.get("lines_covered", 0)
        lines_total = coverage_data.get("lines_total", 1)
        branches_covered = coverage_data.get("branches_covered", 0)
        branches_total = coverage_data.get("branches_total", 1)

        line_pct = (lines_covered / lines_total * 100) if lines_total > 0 else 0.0
        branch_pct = (branches_covered / branches_total * 100) if branches_total > 0 else 0.0

        tier = self.get_coverage_tier(line_pct)
        summary = (
            f"{line_pct:.1f}% line coverage, "
            f"{branch_pct:.1f}% branch coverage — tier: {tier}"
        )

        return {
            "line_coverage_pct": round(line_pct, 2),
            "branch_coverage_pct": round(branch_pct, 2),
            "tier": tier,
            "summary": summary,
        }

    def run_coverage(self, test_path: str, source_path: str) -> Dict[str, Any]:
        """Run pytest with coverage and parse the output."""
        try:
            result = subprocess.run(
                [
                    "python", "-m", "pytest",
                    test_path,
                    f"--cov={source_path}",
                    "--cov-report=term-missing",
                    "-q",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = result.stdout + result.stderr
            # Parse "TOTAL   N   N   N%" line
            match = re.search(r'TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%', output)
            if match:
                stmts = int(match.group(1))
                missed = int(match.group(2))
                covered = stmts - missed
                return {
                    "lines_covered": covered,
                    "lines_total": stmts,
                    "branches_covered": 0,
                    "branches_total": 0,
                    "raw_output": output,
                }
        except Exception:
            pass
        return {}
