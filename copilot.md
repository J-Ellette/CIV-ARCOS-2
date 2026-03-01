# Copilot Progress Tracker

## Current Status
UI operational console (Carbon) fully implemented — all pages complete, plus interactive enhancements (SVG charts, command palette, settings persistence, notification panel, help modal, sidebar toggle, user menu, interactive risk matrix).
Backend observability + security hardening: structured logging with correlation IDs, health probes, webhook HMAC-SHA256 signature + replay protection, write-endpoint idempotency key controls, and modularized versioned API contracts (`/api/v1`).

## Design System Decisions
| Surface | Design System | Notes |
|---------|--------------|-------|
| Operational console (`civ-arcos-carbon.html`) | IBM Carbon Design System v11 · G100 dark theme | All UI chrome, pages, components |
| Exported reports / public-facing surfaces | USWDS (U.S. Web Design System) | No "An official website" banner — not a government site |

## Completed
- [x] Created `build_docs/` folder
- [x] Moved all build-related `.md` files into `build_docs/`
- [x] Created this `copilot.md` progress tracker
- [x] Created comprehensive root `README.md` — project overview, architecture, feature inventory, setup/run/test instructions, endpoint catalog, `/api/v1` contract model, security/idempotency behavior, UI design-system policy, and documentation update workflow
- [x] Expanded root `README.md` with release management sections — added **Release checklist** (verification/API/security/docs gates) and **Known limitations** (current architectural and operational constraints) to support repeatable handoffs
- [x] Added **Roadmap next up** section to root `README.md` — compact, ordered mapping to `build_docs/build-guide.md` Section 18 with per-item status (`not started` / `in progress` / `implemented`) and immediate next actions
- [x] Implemented `civ-arcos-carbon.html` — full IBM Carbon G100 shell (header, side nav, footer)
- [x] **Dashboard page** — stat tiles, evidence feed, GSN assurance case, compliance status, risk map, blockchain ledger, platform sync, federated network, active alerts, live ticker, clock
- [x] **Evidence Store page** — searchable/filterable Carbon data table, stat row, tabs (All/Tests/Scans/Commits/Compliance/Analysis), pagination
- [x] **Assurance Cases page** — GSN hierarchy viewer (CASE-001 security+quality, CASE-002 federated trust)
- [x] **Code Analysis page** — findings table with severity/CWE, complexity hotspots, coverage breakdown
- [x] **Quality Badges page** — badge gallery (coverage/quality/security/compliance/ledger/monitored), tier thresholds table, copy-to-clipboard embed codes
- [x] **Compliance Frameworks page** — accordion per framework (ISO 27001, FedRAMP, SOX ITGC, NIST 800-53, PCI-DSS) with control tables, stat row
- [x] **Analytics / Trends page** — 30-day quality metrics, compliance trends per framework, security history table, evidence velocity table
- [x] **Settings page** — general config, notifications, platform integrations (GitHub/GitLab/Azure/CircleCI toggles), scan configuration
- [x] **Risk Map page** — risk register table, probability×impact matrix, risk trend bars, stat tiles (critical/high/medium/mitigated/score)
- [x] **CIV-SCAP page** — benchmark results (NIST/CIS/STIG/OVAL), scan history table, failed rules table, stat tiles
- [x] **Federated Network page** — node topology table (7 nodes/4 orgs), network health trend bars, recent activity feed, stat tiles
- [x] **Blockchain Ledger page** — block explorer table (recent 6 blocks), chain health/evidence-type trend bars, stat tiles (height/txns/integrity/nodes/block-time)
- [x] **Platform Sync page** — integration status table (GitHub/GitLab/Azure/Jenkins/CircleCI), sync events table, ingestion trend bars, stat tiles
- [x] **Digital Twin page** — what-if scenario table (5 scenarios), model health trend bars, drift alerts feed, stat tiles (models/simulations/coverage/drift)
- [x] **Multi-Tenant page** — tenant registry table (6 tenants), per-tenant compliance trend bars, resource usage table, stat tiles
- [x] **SVG Sparkline charts** — inline SVG area/line charts on Dashboard (quality trend, evidence velocity), Analytics (quality, compliance, security findings trends), Blockchain (chain height); `renderSparkline()` utility with configurable color, min/max, labels, dots
- [x] **Global Command Palette (Ctrl+K / ⌘K)** — full-keyboard page navigation, action shortcuts (Run Scan, Export Report), fuzzy label+section filtering, arrow-key + Enter navigation, Escape/overlay-click to dismiss; trigger button in header
- [x] **Settings persistence (localStorage)** — `saveSettings()` / `loadSettings()` / `discardSettings()` with `localStorage` backend; all 12 settings inputs/toggles wired with `id` attributes; Discard button reverts to last saved state
- [x] **Notification Panel** — slide-out right panel (340px) with grouped notifications (Security/Risk, Compliance, Blockchain, Platform Events); unread badge count on header bell button; Mark All Read action; auto-increment on live events; close on outside click
- [x] **Help modal (keyboard shortcuts)** — Carbon modal listing all keyboard shortcuts: Ctrl+K (command palette), Alt+N (notifications), Alt+B (sidebar toggle), Alt+S (scan), Alt+E (export), G+letter page-jump shortcuts; feature overview and API endpoint display
- [x] **Sidebar toggle** — hamburger button collapses/expands side nav with CSS transition; `Alt+B` keyboard shortcut; content margin adjusts automatically
- [x] **User profile dropdown menu** — click JE avatar to open Carbon-styled dropdown with nav shortcuts (Settings, Export Report, Run Scan, Help, Sign Out); closes on outside click
- [x] **Interactive Risk Matrix** — probability×impact grid cells now have `risk-cell` class with hover tooltip listing specific RISK-IDs in each bucket; keyboard-accessible focus ring
- [x] **Improved `setPage()` navigation** — when called programmatically (e.g., from notifications panel, user menu, keyboard shortcuts), auto-highlights the matching sidebar nav item
- [x] **Additional keyboard shortcuts** — G+D/E/A/C/R/B/T/S/N page-jump hotkeys; Alt+N/B/S/E action shortcuts; all documented in help modal
- [x] **Structured logging + correlation IDs** (`civ_arcos/web/framework.py`) — every HTTP request logs a JSON line (`ts`, `correlation_id`, `method`, `path`, `status`, `duration_ms`) via `civ_arcos.web` logger; `X-Correlation-ID` header echoed on every response; incoming `X-Correlation-ID` from callers is honoured and propagated
- [x] **Health endpoints** — `GET /api/health/live` (liveness probe, always 200), `GET /api/health/ready` (readiness: checks blockchain integrity + evidence store, 200/503), `GET /api/health/dependencies` (full health with uptime/version/assurance-case count)
- [x] **Webhook security module** (`civ_arcos/web/webhook.py`) — `validate_github_signature()` (HMAC-SHA256, constant-time compare), `validate_timestamp()` (ISO-8601 + configurable tolerance), `_NonceCache` (thread-safe in-memory replay cache with TTL eviction), module-level `nonce_cache` singleton
- [x] **`POST /api/webhooks/github`** — accepts GitHub webhook deliveries; validates `X-Hub-Signature-256` when `CIV_WEBHOOK_SECRET` env var is set; rejects duplicate `X-GitHub-Delivery` IDs (409 Conflict); 202 Accepted on success
- [x] **Idempotency key controls for write endpoints** — added `civ_arcos/web/idempotency.py` (`IdempotencyCache`, payload fingerprinting), integrated precheck/store logic in `POST /api/evidence/collect`, `POST /api/blockchain/add`, `POST /api/assurance/create`, and `POST /api/webhooks/github`; supports replayed response (`X-Idempotency-Replayed: true`) and key-payload conflict rejection (`409`)
- [x] **API modularization + versioned contracts (phase 1)**
	- Added contract serializers in `civ_arcos/contracts/v1.py` with common envelope (`contract`, `generated_at`, `data`) for Evidence and Assurance payloads.
	- Added modular v1 route packages: `civ_arcos/api_routes/evidence_v1.py` and `civ_arcos/api_routes/assurance_v1.py`.
	- Registered new endpoints in `civ_arcos/api.py`: `GET /api/v1/contracts`, `GET /api/v1/evidence`, `GET /api/v1/evidence/{evidence_id}`, `GET /api/v1/assurance`, `GET /api/v1/assurance/{case_id}`, `POST /api/v1/assurance/create`.
	- Preserved existing `/api/*` responses for backward compatibility while introducing explicit versioned contracts.
- [x] **API modularization + versioned contracts (phase 2 slice: Risk/Compliance/Analytics)**
	- Added modular route package `civ_arcos/api_routes/platform.py` for legacy and v1 route registration.
	- Extracted legacy route logic from `civ_arcos/api.py` for: `/api/risk/map`, `/api/compliance/status`, `/api/analytics/trends`.
	- Added v1 contract serializers in `civ_arcos/contracts/v1.py`: `RiskMap`, `ComplianceStatus`, `AnalyticsTrends`.
	- Added v1 endpoints: `GET /api/v1/risk/map`, `GET /api/v1/compliance/status`, `GET /api/v1/analytics/trends`.
	- Added integration coverage in `tests/integration/test_api.py` for new v1 contracts and legacy compatibility.
- [x] **API modularization + versioned contracts (phase 2 slice: Tenants/Settings)**
	- Added modular route package `civ_arcos/api_routes/admin.py`.
	- Extracted legacy route logic from `civ_arcos/api.py` for: `/api/tenants`, `/api/settings`.
	- Added v1 contract serializers in `civ_arcos/contracts/v1.py`: `TenantsList`, `TenantDetail`, `SettingsState`, `SettingsUpdate`.
	- Added v1 endpoints: `GET /api/v1/tenants`, `POST /api/v1/tenants`, `GET /api/v1/settings`, `POST /api/v1/settings`.
	- Added integration coverage in `tests/integration/test_api.py` for new v1 contracts and legacy compatibility.
- [x] **API modularization + versioned contracts (phase 2 slice: Plugins)**
	- Added modular route package `civ_arcos/api_routes/plugins.py`.
	- Extracted legacy route logic from `civ_arcos/api.py` for: `/api/plugins/validate`, `/api/plugins/execute`.
	- Added v1 contract serializers in `civ_arcos/contracts/v1.py`: `PluginValidation`, `PluginExecution`.
	- Added v1 endpoints: `POST /api/v1/plugins/validate`, `POST /api/v1/plugins/execute`.
	- Extended integration coverage in `tests/integration/test_plugin_api.py` and `tests/integration/test_api.py` for plugin v1 contracts and registry listing.
- [x] **API modularization + versioned contracts (phase 2 slice: Analysis/Assurance expansion)**
	- Added modular route packages `civ_arcos/api_routes/analysis.py` and `civ_arcos/api_routes/assurance.py`.
	- Extracted legacy route logic from `civ_arcos/api.py` for: `/api/analysis/*`, `/api/assurance*` endpoints.
	- Expanded v1 contracts in `civ_arcos/contracts/v1.py`: `AssuranceTemplates`, `AssuranceAutoGenerate`, `AnalysisStatic`, `AnalysisSecurity`, `AnalysisTests`, `AnalysisComprehensive`.
	- Expanded v1 endpoints: `GET /api/v1/assurance/templates`, `POST /api/v1/assurance/auto-generate`, `POST /api/v1/analysis/static`, `POST /api/v1/analysis/security`, `POST /api/v1/analysis/tests`, `POST /api/v1/analysis/comprehensive`.
	- Extended integration coverage in `tests/integration/test_api.py` for analysis and assurance v1 contract envelopes.
- [x] **Operational console freshness pass** (`civ-arcos-carbon.html`)
	- Removed seeded/personalized values from Settings and Scan modal defaults.
	- Cleared pre-populated Notification panel entries; default state now starts empty.
	- Replaced seeded Code Analysis findings with empty-state messaging.
	- Replaced seeded USWDS report preview values/tables with no-data defaults.
- [x] **Plugin sandbox hardening (baseline)**
	- Added `civ_arcos/core/plugin_marketplace.py` with `PluginValidator` (AST-based forbidden import checks + checksum) and `PluginSandbox` (isolated subprocess execution in Python `-I` mode, timeout limits, bounded output capture).
	- Added REST endpoints in `civ_arcos/api.py`: `POST /api/plugins/validate` and `POST /api/plugins/execute`.
	- Added idempotency support to plugin execution endpoint via existing `Idempotency-Key` controls.
- [x] **Persistence/isolation testing expansion (storage baseline)**
	- Hardened `civ_arcos/storage/graph.py` with re-entrant locking around graph mutations/reads and atomic file writes (`.tmp` + replace) for safer persistence.
	- Expanded `tests/unit/test_graph.py` with cold-start empty-load verification, atomic-save failure recovery check, and concurrent-write persistence round-trip tests.
	- Expanded `tests/unit/test_evidence.py` with `EvidenceStore` cold-start recovery and concurrent-write reload integrity tests.
	- Verified with `pytest tests/unit/test_graph.py tests/unit/test_evidence.py -q` (17 passing) and regression integration suite (43 passing).
- [x] **Isolation sub-slice: tenant-bound authorization checks + cross-tenant tests**
	- Updated `civ_arcos/api_routes/admin.py` v1 routes to enforce tenant identity via `X-Tenant-ID` for settings access and deny cross-tenant target selection.
	- Added per-tenant settings storage isolation for v1 settings reads/writes while preserving legacy `/api/settings` behavior.
	- Added scoped tenant listing behavior for `GET /api/v1/tenants` with explicit cross-tenant filter denial.
	- Added integration tests in `tests/integration/test_api.py` for required tenant header behavior, cross-tenant read/write denial, and per-tenant settings non-leakage.
	- Verified with `pytest tests/integration/test_api.py tests/integration/test_plugin_api.py tests/integration/test_health_webhook.py tests/unit/test_graph.py tests/unit/test_evidence.py -q` (64 passing).
- [x] **Isolation sub-slice: tenant-bound checks for v1 evidence collection**
	- Expanded `civ_arcos/api_routes/evidence_v1.py` with `POST /api/v1/evidence/collect` requiring `X-Tenant-ID`, tenant validation, and idempotent contract responses.
	- Added tenant-scoped read behavior for `GET /api/v1/evidence` and cross-tenant denial on `GET /api/v1/evidence/{evidence_id}` when tenant context mismatches.
	- Extended evidence serialization/contracts in `civ_arcos/contracts/v1.py` with `EvidenceCollection` and tenant metadata in `EvidenceList` summary items.
	- Added optional tenant filtering hooks in `civ_arcos/evidence/collector.py` (`list_evidence(tenant_id=...)`, `get_evidence(..., tenant_id=...)`) to support isolation logic.
	- Added integration coverage in `tests/integration/test_api.py` for tenant-header-required collection, cross-tenant read denial, and tenant-scoped listing behavior.
	- Verified with `pytest tests/integration/test_api.py tests/integration/test_plugin_api.py tests/integration/test_health_webhook.py tests/unit/test_graph.py tests/unit/test_evidence.py -q` (67 passing).
- [x] **Plugin sandbox test coverage**
	- Added `tests/unit/test_plugin_marketplace.py` (5 tests) and `tests/integration/test_plugin_api.py` (5 tests).
	- Verified with `pytest tests/unit/test_plugin_marketplace.py tests/integration/test_plugin_api.py tests/integration/test_api.py -q` (22 passing).
- [x] **50 new tests (cumulative recent additions)** — `tests/unit/test_framework_logging.py` (10), `tests/unit/test_webhook.py` (17), `tests/integration/test_health_webhook.py` (15), `tests/unit/test_idempotency.py` (5), `tests/integration/test_api.py` idempotency scenarios (3); total test count 133, targeted suite passing
- [x] **54 new tests (cumulative recent additions)** — previous 50 plus versioned contract API tests in `tests/integration/test_api.py` (4); total test count 137, targeted suite passing
- [x] **STEP_06 slice: AI optional backend adapter (Azure OpenAI explicit opt-in)**
	- Added `civ_arcos/analysis/llm_integration.py` with `MockBackend` default behavior and `AzureOpenAIBackend` selection path.
	- Updated analysis test generation wiring (`civ_arcos/analysis/test_generator.py`, `civ_arcos/api_routes/analysis.py`) to accept `use_ai` and `llm_backend` while preserving deterministic fallback by default.
	- Added/extended coverage in `tests/unit/test_llm_integration.py`, `tests/unit/test_test_generator.py`, and `tests/integration/test_analysis_api.py`.
	- Verified with `python -m pytest tests/unit/test_llm_integration.py tests/unit/test_test_generator.py tests/integration/test_analysis_api.py -q` (14 passed).
- [x] **STEP_07 slice: blockchain sync event stream**
	- Added `civ_arcos/distributed/sync_events.py` with thread-safe in-memory event storage and cursor-based reads.
	- Updated `civ_arcos/api.py` to emit `blockchain.block_added` events on `POST /api/blockchain/add` and expose `GET /api/sync/events` polling endpoint.
	- Added integration coverage in `tests/integration/test_api.py` for publish/receive behavior and idempotent replay non-duplication.
	- Verified with `python -m pytest tests/integration/test_api.py -k "sync_events or blockchain" -q` (5 passed).
- [x] **STEP_08 slice: dashboard live updates path**
	- Added live-update dashboard hooks in `civ-arcos-carbon.html` for risk + ledger widget refresh targets.
	- Added `initDashboardLiveUpdates` polling logic consuming `GET /api/sync/events` and refresh requests to `GET /api/risk/map` and `GET /api/blockchain/chain`.
	- Extended dashboard route integration checks in `tests/integration/test_dashboard.py` for live update hook/endpoint wiring.
	- Verified with `python -m pytest tests/integration/test_dashboard.py tests/integration/test_api.py -k "dashboard or sync_events or blockchain" -q` (8 passed).
- [x] **STEP_09 slice: plugin version metadata + compatibility checks**
	- Added `PluginManifest` and `PluginRegistry` in `civ_arcos/core/plugin_marketplace.py` with semantic version compatibility checks and API target validation.
	- Extended plugin endpoints in `civ_arcos/api_routes/plugins.py` with legacy/v1 registration and registry listing routes (`/api/plugins/register|registry`, `/api/v1/plugins/register|registry`).
	- Added v1 contracts in `civ_arcos/contracts/v1.py`: `PluginRegistration` and `PluginRegistry`.
	- Added compatibility matrix coverage in `tests/unit/test_plugin_marketplace.py` and integration registry checks in `tests/integration/test_plugin_api.py`.
	- Verified with `python -m pytest tests/unit/test_plugin_marketplace.py tests/integration/test_plugin_api.py -q` (18 passed).
- [x] **STEP_10 slice: predictive quality forecasting baseline**
	- Added deterministic forecast generation to `civ_arcos/core/quality_metrics_history.py` via `forecast_summary(window, horizon)` using linear slope-based projections.
	- Added legacy/v1 forecast endpoints in `civ_arcos/api_routes/platform.py`: `GET /api/quality/metrics/forecast` and `GET /api/v1/quality/metrics/forecast`.
	- Added v1 forecast contract serializer in `civ_arcos/contracts/v1.py` (`QualityMetricsForecast`).
	- Added integration regression checks in `tests/integration/test_api.py` for deterministic projections and contract envelope shape.
	- Verified with `python -m pytest tests/integration/test_api.py -k "quality_metrics_forecast or quality_metrics_trends or quality_metrics_record" -q` (4 passed).
- [x] **Governance + session hooks + docs rebuild slice**
	- Added governance audit scripts under `.github/hooks/governance-audit/` and session logging scripts under `.github/hooks/session-logger/`.
	- Added session prompt submit logger hook: `.github/hooks/session-logger/user-prompt-submit.sh`.
	- Added baseline CI quality workflow: `.github/workflows/quality-gates.yml`.
	- Recreated canonical docs: `build_docs/STATUS.md` and `build_docs/VERIFICATION_MATRIX.md`.
	- Updated `scripts/docs_consistency_check.py` to validate against `build_docs/build-guide.md`.
- [x] **STEP_05 bounded slice: fragments + ArgTL + ACQL core**
	- Added `civ_arcos/assurance/fragments.py` with `AssuranceCaseFragment` and `FragmentLibrary` default patterns (`component_quality`, `component_security`, `integration`).
	- Added `civ_arcos/assurance/argtl.py` with `compose`, `link`, `validate`, and `assemble` operation support in `ArgTLEngine`.
	- Added `civ_arcos/assurance/acql.py` with 8 ACQL query types (`CONSISTENCY`, `COMPLETENESS`, `SOUNDNESS`, `COVERAGE`, `TRACEABILITY`, `WEAKNESSES`, `DEPENDENCIES`, `DEFEATERS`).
	- Added focused Step 5 tests: `tests/unit/assurance/test_fragments.py`, `tests/unit/assurance/test_argtl.py`, `tests/unit/assurance/test_acql.py`.
	- Verified with `python -m pytest tests/unit/assurance -q` (9 passed) and assurance regression `python -m pytest tests/unit/test_case.py tests/unit/test_gsn.py tests/unit/test_templates.py tests/integration/test_assurance_api.py -q` (27 passed).

## Build-Related Docs (in `build_docs/`)
| File | Description |
|------|-------------|
| `build-guide.md` | Main build guide |
| `VERIFICATION_MATRIX.md` | Verification checklist/matrix |
| `STATUS.md` | Build/project status |

## Remaining Stubs
None — all pages fully implemented.

## Notes
- Run tests: `python -m pytest tests/ -q`
- Start API: `python -m civ_arcos.api` (serves on port 8080)
- Dashboard: http://localhost:8080/dashboard
- UI console: open `civ-arcos-carbon.html` directly in browser (no server required)
