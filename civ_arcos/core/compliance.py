"""Compliance framework evaluation engine for enterprise assurance."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Tuple


class ComplianceEngine:
    """Evaluate evidence snapshots against defined compliance frameworks."""

    def __init__(self) -> None:
        """Initialize framework definitions and control-evidence mappings."""
        self._frameworks: Dict[str, List[Tuple[str, str]]] = {
            "ISO 27001": [
                ("A.12.6.1 vulnerability management", "vulnerability_management"),
                ("A.14.2.1 secure development", "secure_development"),
                ("A.12.1.2 change management", "change_management"),
                ("A.12.4.1 event logging", "event_logging"),
                ("A.14.2.5 secure principles", "secure_principles"),
            ],
            "SOX": [
                ("ITGC-1 access controls", "access_controls"),
                ("ITGC-2 change management", "change_management"),
                ("ITGC-3 data integrity", "data_integrity"),
                ("ITGC-4 audit trails", "audit_trails"),
            ],
            "HIPAA": [
                ("§164.312(a)(1) access control", "access_controls"),
                ("§164.312(b) audit controls", "audit_controls"),
                ("§164.312(c)(1) integrity", "data_integrity"),
                ("§164.312(e)(1) transmission security", "transmission_security"),
            ],
            "PCI-DSS": [
                ("Req-6.2 secure development", "secure_development"),
                ("Req-6.3 security testing", "security_testing"),
                ("Req-7.1 access control", "access_controls"),
                ("Req-11.3 vulnerability scanning", "vulnerability_scanning"),
            ],
            "NIST 800-53": [
                ("AC-2 account management", "account_management"),
                ("CM-3 change control", "change_control"),
                ("CA-2 security assessment", "security_assessment"),
                ("SI-2 flaw remediation", "flaw_remediation"),
                ("SI-10 input validation", "input_validation"),
            ],
        }

    def list_frameworks(self) -> List[Dict[str, Any]]:
        """List supported compliance frameworks and control counts."""
        result = []
        for name in sorted(self._frameworks.keys()):
            controls = self._frameworks[name]
            result.append({"framework": name, "control_count": len(controls)})
        return result

    def evaluate_framework(
        self,
        framework: str,
        evidence: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate one framework with control-level scoring and summary."""
        controls = self._frameworks.get(framework)
        if controls is None:
            raise ValueError("Unsupported compliance framework")

        control_results = []
        passed = 0
        for control_name, evidence_key in controls:
            value = evidence.get(evidence_key, False)
            passed_control = bool(value)
            if passed_control:
                passed += 1
            control_results.append(
                {
                    "control": control_name,
                    "evidence_key": evidence_key,
                    "passed": passed_control,
                }
            )

        total = len(controls)
        score = 0.0 if total == 0 else round(passed / total, 3)
        status = self._score_status(score)

        return {
            "framework": framework,
            "score": score,
            "status": status,
            "passed_controls": passed,
            "total_controls": total,
            "controls": control_results,
            "recommendations": self._recommendations(control_results),
        }

    def evaluate_all(self, evidence: Mapping[str, Any]) -> Dict[str, Any]:
        """Evaluate all frameworks and return aggregate compliance summary."""
        framework_results = [
            self.evaluate_framework(name, evidence)
            for name in sorted(self._frameworks.keys())
        ]

        compliant = len(
            [item for item in framework_results if item["status"] == "compliant"]
        )
        partial = len(
            [item for item in framework_results if item["status"] == "partial"]
        )

        average = (
            0.0
            if not framework_results
            else round(
                sum(float(item["score"]) for item in framework_results)
                / len(framework_results),
                3,
            )
        )

        return {
            "framework_count": len(framework_results),
            "compliant_count": compliant,
            "partial_count": partial,
            "non_compliant_count": len(framework_results) - compliant - partial,
            "average_score": average,
            "frameworks": framework_results,
        }

    @staticmethod
    def _score_status(score: float) -> str:
        """Map normalized score to compliance status category."""
        if score >= 0.8:
            return "compliant"
        if score >= 0.5:
            return "partial"
        return "non_compliant"

    @staticmethod
    def _recommendations(control_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for failed controls."""
        failed = [item for item in control_results if not bool(item.get("passed"))]
        if not failed:
            return ["Maintain current control evidence quality."]

        recommendations = []
        for item in failed:
            recommendations.append(f"Add or improve evidence for {item['control']}.")
        return recommendations
