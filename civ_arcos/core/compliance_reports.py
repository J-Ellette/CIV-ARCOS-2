"""Tenant-scoped compliance report artifact persistence."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, cast


@dataclass
class ComplianceReportArtifact:
    """Persisted compliance report artifact metadata and payload."""

    report_id: str
    tenant_id: str
    generated_at: str
    frameworks: List[Dict[str, Any]]
    summary: Dict[str, Any]


class ComplianceReportStore:
    """Manage tenant-scoped compliance report artifacts with file persistence."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._lock = threading.RLock()
        self._storage_path = (
            storage_path or Path(".civ_arcos") / "compliance_reports.json"
        )
        self._reports: Dict[str, ComplianceReportArtifact] = {}
        self._load()

    def create_report(
        self,
        tenant_id: str,
        frameworks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create and persist a tenant-scoped compliance report artifact."""
        report = ComplianceReportArtifact(
            report_id=f"cmp_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            frameworks=frameworks,
            summary={
                "framework_count": len(frameworks),
                "compliant_count": len(
                    [f for f in frameworks if f.get("status") == "compliant"]
                ),
                "partial_count": len(
                    [f for f in frameworks if f.get("status") == "partial"]
                ),
            },
        )
        with self._lock:
            self._reports[report.report_id] = report
            self._save()
        return asdict(report)

    def list_reports(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List report artifacts for a single tenant ordered newest first."""
        with self._lock:
            items = [
                asdict(report)
                for report in self._reports.values()
                if report.tenant_id == tenant_id
            ]
        items.sort(key=lambda item: item["generated_at"], reverse=True)
        return items

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get one persisted report artifact by ID."""
        with self._lock:
            report = self._reports.get(report_id)
            return asdict(report) if report else None

    def _load(self) -> None:
        """Load report artifacts from disk."""
        if not self._storage_path.exists():
            return

        raw = self._storage_path.read_text(encoding="utf-8")
        data_obj: Any = json.loads(raw)
        if not isinstance(data_obj, list):
            return

        data_list = cast(List[object], data_obj)
        required = {
            "report_id",
            "tenant_id",
            "generated_at",
            "frameworks",
            "summary",
        }
        for item_obj in data_list:
            if not isinstance(item_obj, dict):
                continue
            item = cast(Dict[str, object], item_obj)
            if not required.issubset(set(item.keys())):
                continue
            if not isinstance(item["report_id"], str):
                continue
            if not isinstance(item["tenant_id"], str):
                continue
            if not isinstance(item["generated_at"], str):
                continue
            if not isinstance(item["frameworks"], list):
                continue
            if not isinstance(item["summary"], dict):
                continue

            self._reports[item["report_id"]] = ComplianceReportArtifact(
                report_id=item["report_id"],
                tenant_id=item["tenant_id"],
                generated_at=item["generated_at"],
                frameworks=cast(List[Dict[str, Any]], item["frameworks"]),
                summary=cast(Dict[str, Any], item["summary"]),
            )

    def _save(self) -> None:
        """Persist report artifacts atomically."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(report) for report in self._reports.values()]
        tmp_path = self._storage_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self._storage_path)
