"""Multi-tenant management utilities for enterprise isolation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


@dataclass
class TenantRecord:
    """A tenant registry record with isolation and resolution metadata."""

    tenant_id: str
    name: str
    plan: str
    created_at: str
    storage_path: str
    quality_weights: Dict[str, float]
    badge_template: str
    compliance_standards: List[str]
    subdomain: str
    api_key: str


class TenantManager:
    """Manage tenant lifecycle, isolation paths, and request tenant resolution."""

    def __init__(self, storage_root: Optional[Path] = None) -> None:
        """Initialize in-memory tenant registry and storage root path."""
        self._storage_root = storage_root or Path("data") / "tenants"
        self._tenants: Dict[str, TenantRecord] = {}
        self._subdomain_index: Dict[str, str] = {}
        self._api_key_index: Dict[str, str] = {}

    def create_tenant(
        self, tenant_id: str, config: Mapping[str, Any]
    ) -> Dict[str, Any]:
        """Create a tenant and ensure isolated storage path exists on disk."""
        normalized_id = tenant_id.strip()
        if not normalized_id:
            raise ValueError("tenant_id is required")
        if normalized_id in self._tenants:
            raise ValueError("Tenant already exists")

        name = str(config.get("name") or normalized_id)
        plan = str(config.get("plan") or "free")
        subdomain = str(config.get("subdomain") or normalized_id)
        api_key = str(config.get("api_key") or "")

        storage_path = self._storage_root / f"tenant_{normalized_id}"
        storage_path.mkdir(parents=True, exist_ok=True)

        record = TenantRecord(
            tenant_id=normalized_id,
            name=name,
            plan=plan,
            created_at=datetime.now(timezone.utc).isoformat(),
            storage_path=str(storage_path),
            quality_weights=dict(config.get("quality_weights") or {}),
            badge_template=str(config.get("badge_template") or "default"),
            compliance_standards=list(config.get("compliance_standards") or []),
            subdomain=subdomain,
            api_key=api_key,
        )

        self._tenants[normalized_id] = record
        if record.subdomain:
            self._subdomain_index[record.subdomain.lower()] = normalized_id
        if record.api_key:
            self._api_key_index[record.api_key] = normalized_id
        return asdict(record)

    def list_tenants(self) -> List[Dict[str, Any]]:
        """List tenants in deterministic identifier order."""
        return [
            asdict(self._tenants[tenant_id])
            for tenant_id in sorted(self._tenants.keys())
        ]

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get one tenant by identifier when present."""
        record = self._tenants.get(tenant_id)
        return asdict(record) if record else None

    def update_tenant(
        self, tenant_id: str, updates: Mapping[str, Any]
    ) -> Dict[str, Any]:
        """Update mutable tenant fields and maintain resolver indexes."""
        record = self._tenants.get(tenant_id)
        if record is None:
            raise ValueError("Tenant not found")

        if "name" in updates:
            record.name = str(updates["name"])
        if "plan" in updates:
            record.plan = str(updates["plan"])
        if "quality_weights" in updates:
            record.quality_weights = dict(updates["quality_weights"])
        if "badge_template" in updates:
            record.badge_template = str(updates["badge_template"])
        if "compliance_standards" in updates:
            record.compliance_standards = list(updates["compliance_standards"])
        if "subdomain" in updates:
            old_subdomain = record.subdomain.lower()
            if self._subdomain_index.get(old_subdomain) == tenant_id:
                self._subdomain_index.pop(old_subdomain, None)
            record.subdomain = str(updates["subdomain"])
            if record.subdomain:
                self._subdomain_index[record.subdomain.lower()] = tenant_id
        if "api_key" in updates:
            if record.api_key and self._api_key_index.get(record.api_key) == tenant_id:
                self._api_key_index.pop(record.api_key, None)
            record.api_key = str(updates["api_key"])
            if record.api_key:
                self._api_key_index[record.api_key] = tenant_id

        return asdict(record)

    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete one tenant from in-memory registry and resolver indexes."""
        record = self._tenants.pop(tenant_id, None)
        if record is None:
            return False
        if self._subdomain_index.get(record.subdomain.lower()) == tenant_id:
            self._subdomain_index.pop(record.subdomain.lower(), None)
        if record.api_key and self._api_key_index.get(record.api_key) == tenant_id:
            self._api_key_index.pop(record.api_key, None)
        return True

    def get_tenant_context(
        self, request: Mapping[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Resolve tenant context from header, subdomain, query, then API key."""
        headers = request.get("headers") or {}
        query = request.get("query") or {}
        host = str(request.get("host") or "")
        api_key = str(request.get("api_key") or "")

        if not isinstance(headers, Mapping):
            headers = {}
        if not isinstance(query, Mapping):
            query = {}

        header_tenant = str(
            headers.get("X-Tenant-ID") or headers.get("x-tenant-id") or ""
        ).strip()
        if header_tenant:
            return self.get_tenant(header_tenant)

        subdomain_tenant = self._tenant_from_subdomain(host)
        if subdomain_tenant:
            return self.get_tenant(subdomain_tenant)

        query_tenant = str(query.get("tenant_id") or "").strip()
        if query_tenant:
            return self.get_tenant(query_tenant)

        api_key_tenant = self._api_key_index.get(api_key)
        if api_key_tenant:
            return self.get_tenant(api_key_tenant)
        return None

    def _tenant_from_subdomain(self, host: str) -> str:
        """Resolve tenant identifier from subdomain host pattern."""
        normalized = host.strip().lower()
        if not normalized:
            return ""
        subdomain = normalized.split(".")[0]
        return self._subdomain_index.get(subdomain, "")
