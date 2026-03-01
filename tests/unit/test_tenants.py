"""Unit tests for multi-tenant management and resolution behavior."""

from pathlib import Path

import pytest

from civ_arcos.core.tenants import TenantManager


def _manager(tmp_path: Path) -> TenantManager:
    """Create a tenant manager rooted at a temporary isolation path."""
    return TenantManager(storage_root=tmp_path / "tenants")


def test_create_tenant_creates_isolated_storage_path(tmp_path: Path) -> None:
    """Creating a tenant should materialize a tenant-specific storage folder."""
    manager = _manager(tmp_path)

    tenant = manager.create_tenant("org_alpha", {"name": "Org Alpha", "plan": "pro"})

    assert tenant["tenant_id"] == "org_alpha"
    assert (tmp_path / "tenants" / "tenant_org_alpha").exists()


def test_create_tenant_rejects_duplicate_identifier(tmp_path: Path) -> None:
    """Tenant creation should reject duplicate tenant identifiers."""
    manager = _manager(tmp_path)
    manager.create_tenant("org_alpha", {"name": "Org Alpha"})

    with pytest.raises(ValueError):
        manager.create_tenant("org_alpha", {"name": "Org Alpha 2"})


def test_list_tenants_returns_sorted_by_identifier(tmp_path: Path) -> None:
    """Tenant listing should be deterministic by identifier ordering."""
    manager = _manager(tmp_path)
    manager.create_tenant("org_beta", {"name": "Beta"})
    manager.create_tenant("org_alpha", {"name": "Alpha"})

    tenant_ids = [item["tenant_id"] for item in manager.list_tenants()]

    assert tenant_ids == ["org_alpha", "org_beta"]


def test_update_tenant_changes_settings_and_resolution_fields(tmp_path: Path) -> None:
    """Tenant update should mutate settings and resolver indexes."""
    manager = _manager(tmp_path)
    manager.create_tenant(
        "org_alpha",
        {
            "name": "Org Alpha",
            "subdomain": "alpha",
            "api_key": "key-alpha",
        },
    )

    updated = manager.update_tenant(
        "org_alpha",
        {
            "plan": "enterprise",
            "subdomain": "alpha2",
            "api_key": "key-alpha-2",
            "compliance_standards": ["ISO 27001"],
        },
    )

    assert updated["plan"] == "enterprise"
    assert updated["subdomain"] == "alpha2"
    assert updated["api_key"] == "key-alpha-2"
    assert updated["compliance_standards"] == ["ISO 27001"]


def test_delete_tenant_removes_registry_entry(tmp_path: Path) -> None:
    """Deleting an existing tenant should remove retrievable context."""
    manager = _manager(tmp_path)
    manager.create_tenant("org_alpha", {"name": "Org Alpha"})

    deleted = manager.delete_tenant("org_alpha")

    assert deleted is True
    assert manager.get_tenant("org_alpha") is None


def test_get_tenant_context_prefers_header_over_other_strategies(
    tmp_path: Path,
) -> None:
    """Header tenant identity should take precedence over query/subdomain/API key."""
    manager = _manager(tmp_path)
    manager.create_tenant(
        "org_alpha",
        {"name": "Org Alpha", "subdomain": "alpha", "api_key": "k-alpha"},
    )
    manager.create_tenant(
        "org_beta",
        {"name": "Org Beta", "subdomain": "beta", "api_key": "k-beta"},
    )

    context = manager.get_tenant_context(
        {
            "headers": {"X-Tenant-ID": "org_beta"},
            "query": {"tenant_id": "org_alpha"},
            "host": "alpha.example.com",
            "api_key": "k-alpha",
        }
    )

    assert context is not None
    assert context["tenant_id"] == "org_beta"


def test_get_tenant_context_resolves_subdomain_when_header_missing(
    tmp_path: Path,
) -> None:
    """Subdomain strategy should resolve tenant when header is absent."""
    manager = _manager(tmp_path)
    manager.create_tenant("org_alpha", {"name": "Org Alpha", "subdomain": "alpha"})

    context = manager.get_tenant_context({"host": "alpha.example.com"})

    assert context is not None
    assert context["tenant_id"] == "org_alpha"


def test_get_tenant_context_resolves_query_when_header_subdomain_missing(
    tmp_path: Path,
) -> None:
    """Query strategy should resolve tenant after header/subdomain miss."""
    manager = _manager(tmp_path)
    manager.create_tenant("org_alpha", {"name": "Org Alpha"})

    context = manager.get_tenant_context({"query": {"tenant_id": "org_alpha"}})

    assert context is not None
    assert context["tenant_id"] == "org_alpha"


def test_get_tenant_context_resolves_api_key_last(tmp_path: Path) -> None:
    """API-key strategy should resolve tenant as final fallback."""
    manager = _manager(tmp_path)
    manager.create_tenant("org_alpha", {"name": "Org Alpha", "api_key": "k-alpha"})

    context = manager.get_tenant_context({"api_key": "k-alpha"})

    assert context is not None
    assert context["tenant_id"] == "org_alpha"


def test_get_tenant_context_returns_none_when_no_strategy_matches(
    tmp_path: Path,
) -> None:
    """Unknown context should produce no tenant resolution result."""
    manager = _manager(tmp_path)
    manager.create_tenant("org_alpha", {"name": "Org Alpha", "api_key": "k-alpha"})

    context = manager.get_tenant_context(
        {"host": "unknown.example.com", "api_key": "missing"}
    )

    assert context is None
