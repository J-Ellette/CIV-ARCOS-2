"""Contract version 1 serializers for API payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from civ_arcos.assurance.case import AssuranceCase
from civ_arcos.evidence.collector import Evidence

CONTRACT_VERSION = "1.0"


def _envelope(name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap contract payload data in a common envelope."""
    return {
        "contract": {
            "name": name,
            "version": CONTRACT_VERSION,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


def evidence_summary_item(evidence: Evidence) -> Dict[str, Any]:
    """Serialize an evidence record as summary metadata."""
    return {
        "id": evidence.id,
        "type": evidence.type,
        "source": evidence.source,
        "timestamp": evidence.timestamp,
        "checksum": evidence.checksum,
        "tenant_id": evidence.provenance.get("tenant_id"),
    }


def evidence_detail_item(evidence: Evidence) -> Dict[str, Any]:
    """Serialize a full evidence record."""
    return {
        "id": evidence.id,
        "type": evidence.type,
        "source": evidence.source,
        "timestamp": evidence.timestamp,
        "checksum": evidence.checksum,
        "data": evidence.data,
        "provenance": evidence.provenance,
    }


def evidence_list_contract(items: List[Evidence]) -> Dict[str, Any]:
    """Build a versioned contract for evidence summary list responses."""
    return _envelope(
        "EvidenceList",
        {
            "count": len(items),
            "items": [evidence_summary_item(item) for item in items],
        },
    )


def evidence_detail_contract(item: Evidence) -> Dict[str, Any]:
    """Build a versioned contract for evidence detail responses."""
    return _envelope("EvidenceDetail", {"item": evidence_detail_item(item)})


def evidence_collection_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for evidence collection responses."""
    return _envelope("EvidenceCollection", payload)


def assurance_summary_item(case: AssuranceCase) -> Dict[str, Any]:
    """Serialize assurance case summary metadata."""
    return {
        "case_id": case.case_id,
        "title": case.title,
        "description": case.description,
        "project_type": case.project_type,
        "root_goal_id": case.root_goal_id,
        "node_count": len(case.nodes),
        "created_at": case.created_at,
    }


def assurance_list_contract(cases: List[AssuranceCase]) -> Dict[str, Any]:
    """Build a versioned contract for assurance case list responses."""
    return _envelope(
        "AssuranceCaseList",
        {
            "count": len(cases),
            "cases": [assurance_summary_item(case) for case in cases],
        },
    )


def assurance_detail_contract(case: AssuranceCase) -> Dict[str, Any]:
    """Build a versioned contract for assurance case detail responses."""
    return _envelope("AssuranceCaseDetail", {"case": case.to_dict()})


def assurance_templates_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for assurance template list responses."""
    return _envelope("AssuranceTemplates", payload)


def assurance_auto_generate_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for assurance auto-generated case responses."""
    return _envelope("AssuranceAutoGenerate", payload)


def analysis_static_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for static analysis responses."""
    return _envelope("AnalysisStatic", payload)


def analysis_security_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for security analysis responses."""
    return _envelope("AnalysisSecurity", payload)


def analysis_tests_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for test generation analysis responses."""
    return _envelope("AnalysisTests", payload)


def analysis_comprehensive_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for comprehensive analysis responses."""
    return _envelope("AnalysisComprehensive", payload)


def risk_map_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for risk map responses."""
    return _envelope("RiskMap", payload)


def compliance_status_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for compliance status responses."""
    return _envelope("ComplianceStatus", payload)


def analytics_trends_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for analytics trends responses."""
    return _envelope("AnalyticsTrends", payload)


def tenants_list_contract(tenants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a versioned contract for tenant list responses."""
    return _envelope(
        "TenantsList",
        {
            "count": len(tenants),
            "tenants": tenants,
        },
    )


def tenant_detail_contract(tenant: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for tenant detail responses."""
    return _envelope("TenantDetail", {"tenant": tenant})


def settings_state_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for current settings state."""
    return _envelope("SettingsState", payload)


def settings_update_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for settings update responses."""
    return _envelope("SettingsUpdate", payload)


def plugin_validation_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for plugin validation responses."""
    return _envelope("PluginValidation", payload)


def plugin_execution_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a versioned contract for plugin execution responses."""
    return _envelope("PluginExecution", payload)


def contracts_registry() -> Dict[str, Any]:
    """Return discoverable contract metadata for v1 endpoints."""
    return _envelope(
        "ContractRegistry",
        {
            "api_version": "v1",
            "contracts": [
                {"name": "EvidenceList", "version": CONTRACT_VERSION},
                {"name": "EvidenceDetail", "version": CONTRACT_VERSION},
                {"name": "EvidenceCollection", "version": CONTRACT_VERSION},
                {"name": "AssuranceCaseList", "version": CONTRACT_VERSION},
                {"name": "AssuranceCaseDetail", "version": CONTRACT_VERSION},
                {"name": "AssuranceTemplates", "version": CONTRACT_VERSION},
                {"name": "AssuranceAutoGenerate", "version": CONTRACT_VERSION},
                {"name": "AnalysisStatic", "version": CONTRACT_VERSION},
                {"name": "AnalysisSecurity", "version": CONTRACT_VERSION},
                {"name": "AnalysisTests", "version": CONTRACT_VERSION},
                {"name": "AnalysisComprehensive", "version": CONTRACT_VERSION},
                {"name": "RiskMap", "version": CONTRACT_VERSION},
                {"name": "ComplianceStatus", "version": CONTRACT_VERSION},
                {"name": "AnalyticsTrends", "version": CONTRACT_VERSION},
                {"name": "TenantsList", "version": CONTRACT_VERSION},
                {"name": "TenantDetail", "version": CONTRACT_VERSION},
                {"name": "SettingsState", "version": CONTRACT_VERSION},
                {"name": "SettingsUpdate", "version": CONTRACT_VERSION},
                {"name": "PluginValidation", "version": CONTRACT_VERSION},
                {"name": "PluginExecution", "version": CONTRACT_VERSION},
            ],
        },
    )
