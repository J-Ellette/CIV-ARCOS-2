# CIV-ARCOS Status

Last updated: 2026-02-28
Owner: Project maintainers
Source of truth scope: project status, verification posture, known gaps

## Overall Status

- Program state: Documentation indicates implementation through Step 10 plus I18N/Digital Twin additions.
- Verification state: Mixed; many docs report passing tests, but consolidated re-verification is not yet tracked in one place.
- Confidence level: Medium (high narrative completeness, moderate centralized verification maturity).

## Phase Status (Canonical)

| Phase | Legacy Mapping | Status | Verification | Notes |
|---|---|---|---|---|
| Phase 1: Foundation | Step 1 | Reported Complete | Needs Central Re-Check | Evidence graph, collector, base API, badges introduced |
| Phase 2: Analysis | Step 2 | Reported Complete | Needs Central Re-Check | Static/security/testing analyzers |
| Phase 3: Assurance | Step 3 + 4.2 portions | Reported Complete | Needs Central Re-Check | GSN, templates, pattern instantiation, reasoning tooling |
| Phase 4: Dashboard/UX | Step 4 + Step 8 portions | Reported Complete | Needs Central Re-Check | Dashboard pages, interactive visualization |
| Phase 5: Platform Services | Step 5 / 5.5 / 5_6 | Reported Complete | Needs Central Re-Check | Cache/tasks/websocket/reporting/plugin SDK overlap |
| Phase 6: AI Optionality | Step 6 | Reported Complete | Needs Central Re-Check | AI + rule-based fallback design |
| Phase 7: Distributed/Federated | Step 7 | Reported Complete | Needs Central Re-Check | Federated network, ledger, sync engine |
| Phase 8: Visualization Ecosystem | Step 8 | Reported Complete | Needs Central Re-Check | Advanced widgets and executive/developer dashboards |
| Phase 9: Marketplace/API Ecosystem | Step 9 | Reported Complete | Needs Central Re-Check | Plugin marketplace, API ecosystem, community platform |
| Phase 10: Innovation Extensions | Step 10 | Reported Complete | Needs Central Re-Check | Quantum, edge, autonomous quality |
| Add-on: I18N + Digital Twin | I18N_DIGITALTWIN | Reported Complete | Needs Central Re-Check | Localization + simulation/predictive maintenance |

## Current Priorities (from unified improvements)

1. Plugin sandbox hardening
2. API modularization + contract versioning
3. Webhook/idempotency security controls
4. Health model + observability baseline
5. Persistence and isolation testing expansion
6. Quality engineering upgrades
7. Docs normalization + rebuild runbook + verification matrix hardening

## Known Documentation Gaps

- Step naming/ordering drift across legacy step files.
- Status drift between summary docs and later completion docs.
- Verification proof is distributed rather than centralized.

## Verification Policy (starting now)

A phase can move from **Reported Complete** to **Verified Complete** only when:

- Required command set is run and recorded in `VERIFICATION_MATRIX.md`.
- Expected outputs are attached or summarized with timestamp.
- Any failed checks are linked to remediation tasks.

## Change Log

- 2026-02-28: Initial canonical status file created.
- 2026-02-28: Q-002 remediation completed (formatting baseline):
  - Applied code formatting: `python -m black civ_arcos tests` (47 files reformatted).
  - Verification: `python -m black --check civ_arcos tests` (pass; 64 files unchanged).
  - Regression: `python -m pytest tests/integration/test_api.py tests/integration/test_health_webhook.py tests/integration/test_dashboard.py -q` (45 passed).
- 2026-02-28: V-007 remediation completed (dashboard dedicated verification):
  - Added dedicated integration tests in `tests/integration/test_dashboard.py` for `GET /dashboard` status/content-type and HTML marker assertions.
  - Verification: `python -m pytest tests/integration/test_dashboard.py -q` (2 passed).
  - Updated `build_docs/VERIFICATION_MATRIX.md` V-007 from `PARTIAL` to `PASS`.
- 2026-02-28: Q-003 remediation completed (type-safety baseline):
  - Fixed mypy-reported typing errors in `civ_arcos/adapters/github_adapter.py` and `civ_arcos/api.py`.
  - Verification: `python -m mypy civ_arcos` (clean, 0 issues).
  - Regression: `python -m pytest tests/integration/test_api.py tests/integration/test_health_webhook.py -q` (43 passed).
- 2026-02-28: Verification backlog closure pass completed:
  - Executed all previously `NOT_RUN` rows in `build_docs/VERIFICATION_MATRIX.md` (V-001..V-012 and Q-001..Q-005).
  - Updated statuses to concrete outcomes (`PASS`/`FAIL`/`PARTIAL`) with verified commands, dates, and notes.
  - Identified stale matrix command references for removed test files and captured adjusted verification commands where applicable.
- 2026-02-28: Isolation sub-slice implemented (tenant-bound evidence collection and reads in v1):
  - Added `POST /api/v1/evidence/collect` in `civ_arcos/api_routes/evidence_v1.py` with required `X-Tenant-ID`, tenant validation, idempotency replay support, and `EvidenceCollection` contract envelope.
  - Added tenant-scoped behavior for `GET /api/v1/evidence` and cross-tenant deny behavior for `GET /api/v1/evidence/{evidence_id}` under tenant context.
  - Added tenant metadata in evidence summary contract items and expanded registry with `EvidenceCollection`.
  - Verification: `python -m pytest tests/integration/test_api.py tests/integration/test_plugin_api.py tests/integration/test_health_webhook.py tests/unit/test_graph.py tests/unit/test_evidence.py -q` (67 passed).
- 2026-02-28: Isolation sub-slice implemented (tenant-bound authorization + cross-tenant tests):
  - Updated `civ_arcos/api_routes/admin.py` v1 tenant/settings routes to enforce tenant identity from `X-Tenant-ID` and deny cross-tenant target access.
  - Added per-tenant settings override storage for v1 settings flows.
  - Added integration coverage in `tests/integration/test_api.py` for missing-tenant rejection, cross-tenant deny behavior, and per-tenant settings isolation.
  - Verification: `python -m pytest tests/integration/test_api.py tests/integration/test_plugin_api.py tests/integration/test_health_webhook.py tests/unit/test_graph.py tests/unit/test_evidence.py -q` (64 passed).
- 2026-02-28: Persistence/isolation testing expansion (storage baseline):
  - Hardened `civ_arcos/storage/graph.py` with lock-guarded graph operations and atomic persistence writes.
  - Added cold-start, crash-recovery, and concurrent-write tests in `tests/unit/test_graph.py` and `tests/unit/test_evidence.py`.
  - Verification: `python -m pytest tests/unit/test_graph.py tests/unit/test_evidence.py -q` (17 passed).
  - Regression verification: `python -m pytest tests/integration/test_api.py tests/integration/test_plugin_api.py tests/integration/test_health_webhook.py -q` (43 passed).
- 2026-02-28: API modularization phase 2 slice implemented (Analysis/Assurance expansion):
  - Added `civ_arcos/api_routes/analysis.py` and `civ_arcos/api_routes/assurance.py` to extract legacy analysis/assurance route registration from `civ_arcos/api.py`.
  - Expanded `civ_arcos/api_routes/assurance_v1.py` with `GET /api/v1/assurance/templates` and `POST /api/v1/assurance/auto-generate`.
  - Added v1 contracts in `civ_arcos/contracts/v1.py`: `AssuranceTemplates`, `AssuranceAutoGenerate`, `AnalysisStatic`, `AnalysisSecurity`, `AnalysisTests`, `AnalysisComprehensive`.
  - Verification: `python -m pytest tests/integration/test_api.py tests/integration/test_plugin_api.py tests/integration/test_health_webhook.py -q` (43 passed).
- 2026-02-28: API modularization phase 2 slice implemented (Plugins):
  - Added `civ_arcos/api_routes/plugins.py` with legacy and v1 route registration for plugin validation/execution.
  - Added v1 contracts in `civ_arcos/contracts/v1.py`: `PluginValidation`, `PluginExecution`.
  - Added endpoints: `POST /api/v1/plugins/validate`, `POST /api/v1/plugins/execute`.
  - Verification: `pytest tests/integration/test_plugin_api.py tests/integration/test_api.py tests/integration/test_health_webhook.py -q` (41 passed).
- 2026-02-28: API modularization phase 2 slice implemented (Tenants/Settings):
  - Added `civ_arcos/api_routes/admin.py` with legacy and v1 route registration for tenants/settings domains.
  - Added v1 contracts in `civ_arcos/contracts/v1.py`: `TenantsList`, `TenantDetail`, `SettingsState`, `SettingsUpdate`.
  - Added endpoints: `GET /api/v1/tenants`, `POST /api/v1/tenants`, `GET /api/v1/settings`, `POST /api/v1/settings`.
  - Verification: `pytest tests/integration/test_api.py tests/integration/test_health_webhook.py tests/integration/test_plugin_api.py -q` (39 passed).
- 2026-02-28: Operational console seeded-data cleanup completed (`civ-arcos-carbon.html`):
  - Cleared pre-filled settings/integration values and scan target defaults.
  - Reset notification panel to empty-state by default.
  - Replaced seeded analysis findings with empty-state messaging.
  - Replaced seeded USWDS report preview metrics/tables with no-data defaults.
- 2026-02-28: API modularization phase 2 slice implemented (Risk/Compliance/Analytics):
  - Added `civ_arcos/api_routes/platform.py` with shared computation helpers and route registration for legacy `/api/*` and versioned `/api/v1/*` platform endpoints.
  - Added v1 contracts in `civ_arcos/contracts/v1.py`: `RiskMap`, `ComplianceStatus`, `AnalyticsTrends`.
  - Added endpoints: `GET /api/v1/risk/map`, `GET /api/v1/compliance/status`, `GET /api/v1/analytics/trends`.
  - Verification: `pytest tests/integration/test_api.py tests/integration/test_health_webhook.py tests/integration/test_plugin_api.py -q` (36 passed).
- 2026-02-28: Implemented plugin sandbox hardening baseline:
  - Added `civ_arcos/core/plugin_marketplace.py` with AST validation (`PluginValidator`) and isolated subprocess execution (`PluginSandbox`) including timeout and output bounds.
  - Added API endpoints `POST /api/plugins/validate` and `POST /api/plugins/execute`.
  - Added tests: `tests/unit/test_plugin_marketplace.py` and `tests/integration/test_plugin_api.py`.
  - Verification: `pytest tests/unit/test_plugin_marketplace.py tests/integration/test_plugin_api.py tests/integration/test_api.py -q` (22 passed).
- 2026-02-28: Added `README.md` roadmap section (`Roadmap next up`) aligned to `build_docs/improvements.md` unified implementation order.
  - Includes current state labels and next-action notes for each priority item.
- 2026-02-28: Expanded root `README.md` with operational handoff sections:
  - Added Release checklist covering verification, API compatibility, security checks, and documentation gates.
  - Added Known limitations section documenting current scope boundaries and roadmap constraints.
- 2026-02-28: Added root `README.md` as onboarding and usage source of truth:
  - Captures architecture, implemented feature set, API catalog, `/api/v1` contract usage, security controls, and contributor workflow.
  - Includes setup/run/test commands and PowerShell API examples.
  - Defines documentation maintenance policy tying updates to `README.md`, `copilot.md`, `STATUS.md`, and `VERIFICATION_MATRIX.md`.
- 2026-02-28: API modularization + versioned contract layer (phase 1):
  - Added `civ_arcos/contracts/v1.py` for contract-serialized payloads with version metadata.
  - Added modular route files `civ_arcos/api_routes/evidence_v1.py` and `civ_arcos/api_routes/assurance_v1.py` and registered them from `civ_arcos/api.py`.
  - Added v1 endpoints: `GET /api/v1/contracts`, `GET /api/v1/evidence`, `GET /api/v1/evidence/{evidence_id}`, `GET /api/v1/assurance`, `GET /api/v1/assurance/{case_id}`, `POST /api/v1/assurance/create`.
  - Backward compatibility preserved: legacy `/api/*` endpoints unchanged.
  - Verification: `pytest tests/integration/test_api.py tests/integration/test_health_webhook.py tests/unit/test_idempotency.py -q` (32 passed).
- 2026-02-28: Idempotency controls implemented for write endpoints:
  - Added `civ_arcos/web/idempotency.py` with thread-safe `IdempotencyCache`, request fingerprinting (`method + path + body`), and TTL-based replay storage.
  - Wired idempotency handling into `POST /api/evidence/collect`, `POST /api/blockchain/add`, `POST /api/assurance/create`, and `POST /api/webhooks/github`.
  - Behavior: repeated requests with same `Idempotency-Key` + payload replay cached response and include `X-Idempotency-Replayed: true`; same key + different payload returns `409`.
  - Verification: `pytest tests/unit/test_idempotency.py tests/integration/test_api.py tests/integration/test_health_webhook.py -q` (29 passed).
- 2026-02-28: UI operational console (`civ-arcos-carbon.html`) significantly expanded:
  - Implemented: Evidence Store, Assurance Cases (GSN), Code Analysis, Quality Badges, Compliance Frameworks, Analytics/Trends, Settings pages
  - Added: USWDS-styled Export Report modal (no government banner)
  - Retained stubs: Risk Map, CIV-SCAP, Federated Network, Blockchain Ledger, Platform Sync, Digital Twin, Multi-Tenant
- 2026-02-28: UI interactive enhancements added to `civ-arcos-carbon.html`:
  - SVG sparkline/area charts on Dashboard, Analytics, and Blockchain pages (`renderSparkline()` + `initCharts()`)
  - Global command palette (Ctrl+K / ⌘K) with keyboard navigation and page/action shortcuts
  - Settings persistence via localStorage (save/load/discard cycle; 12 settings inputs/toggles wired)
- 2026-02-28: UI interaction enhancements (round 2):
  - Notification panel: slide-out right panel with grouped alerts (Security/Risk, Compliance, Blockchain, Platform Events); header bell badge; Mark All Read
  - Help modal: keyboard shortcuts reference, page-jump hotkeys, feature overview
  - Sidebar toggle: hamburger collapse/expand with CSS transition; Alt+B shortcut
  - User profile dropdown: avatar click opens Carbon-styled menu (Settings, Export, Scan, Help, Sign Out)
  - Interactive Risk Matrix: probability×impact cells show RISK-ID tooltips on hover
  - Improved setPage(): auto-highlights sidebar nav item when called programmatically
  - Additional keyboard shortcuts: G+letter page-jump, Alt+N/B/S/E action hotkeys
- 2026-02-28: Backend observability + security hardening:
  - Structured logging + correlation IDs in `civ_arcos/web/framework.py`: every request logs a JSON line with `ts`, `correlation_id`, `method`, `path`, `status`, `duration_ms`; `X-Correlation-ID` header echoed on every response; incoming `X-Correlation-ID` headers propagated through the request lifecycle.
  - Health endpoints added to API: `GET /api/health/live` (liveness), `GET /api/health/ready` (readiness with blockchain + evidence store checks), `GET /api/health/dependencies` (full dependency health with uptime/version).
  - Webhook security module `civ_arcos/web/webhook.py`: HMAC-SHA256 signature validation (`validate_github_signature`), timestamp tolerance checks (`validate_timestamp`), and in-memory nonce/replay cache (`_NonceCache` / `nonce_cache`).
  - `POST /api/webhooks/github` endpoint: validates `X-Hub-Signature-256`, rejects duplicate `X-GitHub-Delivery` IDs (409), dev-mode when `CIV_WEBHOOK_SECRET` unset.
  - 42 new tests (125 total, all passing).
