# Copilot Progress Tracker

## Current Status
UI operational console (Carbon) fully implemented — all pages complete.

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
