# Copilot Progress Tracker

## Current Status
UI operational console (Carbon) fully implemented — all pages complete, plus interactive enhancements (SVG charts, command palette, settings persistence, notification panel, help modal, sidebar toggle, user menu, interactive risk matrix).
Backend observability + security hardening: structured logging with correlation IDs, health probes, and webhook HMAC-SHA256 signature + replay protection.

## Design System Decisions
| Surface | Design System | Notes |
|---------|--------------|-------|
| Operational console (`civ-arcos-carbon.html`) | IBM Carbon Design System v11 · G100 dark theme | All UI chrome, pages, components |
| Exported reports / public-facing surfaces | USWDS (U.S. Web Design System) | No "An official website" banner — not a government site |

## Completed
- [x] Created `build_docs/` folder
- [x] Moved all build-related `.md` files into `build_docs/`
- [x] Created this `copilot.md` progress tracker
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
- [x] **42 new tests** — `tests/unit/test_framework_logging.py` (10), `tests/unit/test_webhook.py` (17), `tests/integration/test_health_webhook.py` (15); total test count 125, all passing

## Build-Related Docs (in `build_docs/`)
| File | Description |
|------|-------------|
| `build-guide.md` | Main build guide |
| `STEP_01.md` – `STEP_10.md` | Step-by-step build steps |
| `STEP_04.2.md`, `STEP_05-06.md`, `STEP_05.0.md`, `STEP_05.5.md`, `STEP_05_ENTERPRISE.md` | Extended build step variants |
| `IMPLEMENTATION.md` | Implementation notes |
| `VERIFICATION_MATRIX.md` | Verification checklist/matrix |
| `STATUS.md` | Build/project status |
| `compliance-module-guide.md` | Compliance module guide |
| `improvements.md` | Planned improvements |
| `I18N_DIGITALTWIN.md` | Internationalisation / digital twin notes |

## Remaining Stubs
None — all pages fully implemented.

## Notes
- Run tests: `python -m pytest tests/ -q`
- Start API: `python -m civ_arcos.api` (serves on port 8080)
- Dashboard: http://localhost:8080/dashboard
- UI console: open `civ-arcos-carbon.html` directly in browser (no server required)
