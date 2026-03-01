# CIV-ARCOS Verification Matrix

Last updated: 2026-02-28
Purpose: Map each major claim to executable verification evidence.

## Status Legend

- `NOT_RUN` — not executed yet in centralized verification flow
- `PASS` — executed and matched expected outcome
- `FAIL` — executed and did not match expected outcome
- `PARTIAL` — partially verified; follow-up needed
- `DEFERRED` — intentionally postponed with owner and target milestone

## Core Claims Verification

| ID | Feature/Claim | Source Module(s) | Test / Check | Command(s) | Expected Outcome | Last Verified | Status | Notes / Follow-up |
|---|---|---|---|---|---|---|---|---|
| V-001 | Base API health endpoint works | `civ_arcos/api.py` | Integration smoke | `python -m pytest tests/integration/test_api.py -k status_route -q` | Status endpoint returns 200 with version/uptime | 2026-03-01 | PASS | Covered by integration test |
| V-002 | Evidence graph persistence/load works | `civ_arcos/storage/graph.py` | Unit tests | `python -m pytest tests/unit/test_graph.py -q` | Persistence and graph operations pass | 2026-03-01 | PASS | Graph unit tests present |
| V-003 | Evidence checksum/provenance integrity | `civ_arcos/evidence/collector.py` | Unit tests | `python -m pytest tests/unit/test_evidence.py -q` | Checksum/provenance behavior validated | 2026-03-01 | PASS | Evidence unit tests present |
| V-004 | Badge generation produces valid SVG | `civ_arcos/web/badges.py` | Unit tests | `python -m pytest tests/unit/test_badges.py -q` | Badge generation tests pass | 2026-03-01 | PASS | Badge suite present |
| V-005 | Analysis pipeline routes operational | `civ_arcos/analysis/*`, `civ_arcos/api_routes/analysis.py` | Integration tests | `python -m pytest tests/integration/test_analysis_api.py -q` | Static/security/tests/comprehensive routes pass | 2026-03-01 | PASS | Includes AI fallback test |
| V-006 | Assurance case generation/visualization | `civ_arcos/assurance/*` | Unit + integration | `python -m pytest tests/unit/test_case.py tests/unit/test_gsn.py tests/unit/test_templates.py tests/integration/test_assurance_api.py -q` | Assurance suites pass | 2026-03-01 | PASS | Core assurance capability validated |
| V-007 | Dashboard route renders Carbon HTML | `civ-arcos-carbon.html`, `civ_arcos/api.py` | Integration tests | `python -m pytest tests/integration/test_dashboard.py -q` | `/dashboard` returns expected HTML markers | 2026-03-01 | PASS | Live-update hooks asserted |
| V-008 | Webhook signature and replay protection | `civ_arcos/web/webhook.py` | Unit + integration | `python -m pytest tests/unit/test_webhook.py tests/integration/test_health_webhook.py -q` | Signature/replay protections behave correctly | 2026-03-01 | PASS | Existing coverage in place |
| V-009 | Idempotency behavior on write endpoints | `civ_arcos/web/idempotency.py` | Unit + integration | `python -m pytest tests/unit/test_idempotency.py tests/integration/test_api.py -k idempotency -q` | Replay and conflict semantics hold | 2026-03-01 | PASS | Key write paths covered |
| V-010 | Versioned API contract envelope (`/api/v1/*`) | `civ_arcos/contracts/v1.py`, `civ_arcos/api_routes/*` | Integration tests | `python -m pytest tests/integration/test_api.py tests/integration/test_plugin_api.py -q` | Contract envelope shape stable | 2026-03-01 | PASS | v1 coverage across domains |
| V-011 | Plugin sandbox + compatibility registry | `civ_arcos/core/plugin_marketplace.py` | Unit + integration | `python -m pytest tests/unit/test_plugin_marketplace.py tests/integration/test_plugin_api.py -q` | Validation, sandbox, compatibility checks pass | 2026-03-01 | PASS | Includes timeout and registry scenarios |
| V-012 | Sync event stream polling | `civ_arcos/distributed/sync_events.py`, `civ_arcos/api.py` | Integration tests | `python -m pytest tests/integration/test_api.py -k "sync_events or blockchain" -q` | Event polling and replay behavior pass | 2026-03-01 | PASS | No duplicate event replay |
| V-013 | Quality metrics trend/forecast baseline | `civ_arcos/core/quality_metrics_history.py` | Integration tests | `python -m pytest tests/integration/test_api.py -k "quality_metrics_trends or quality_metrics_forecast" -q` | Deterministic trends/forecast contract pass | 2026-03-01 | PASS | Slope-based deterministic forecast |
| V-014 | Step 5 bounded methodologies core | `civ_arcos/assurance/fragments.py`, `civ_arcos/assurance/argtl.py`, `civ_arcos/assurance/acql.py` | Unit tests | `python -m pytest tests/unit/assurance -q` | Fragment library, ArgTL operations, and ACQL queries pass focused suite | 2026-03-01 | PASS | 21 focused tests passing after reasoning + architecture + dependency tracker slices |
| V-015 | Step 5 reasoning engine baseline | `civ_arcos/assurance/reasoning.py` | Unit tests | `python -m pytest tests/unit/assurance/test_reasoning.py -q` | Theory/defeater reasoning, custom theory registration, and risk estimation behavior pass | 2026-02-28 | PASS | 4 focused tests passing |
| V-016 | Step 5 architecture mapper baseline | `civ_arcos/assurance/architecture.py` | Unit tests | `python -m pytest tests/unit/assurance/test_architecture.py -q` | Architecture inference, discrepancy detection, coverage mapping, and traceability matrix generation pass | 2026-03-01 | PASS | 4 focused tests passing |
| V-017 | Step 5 dependency tracker baseline | `civ_arcos/assurance/dependency_tracker.py` | Unit tests | `python -m pytest tests/unit/assurance/test_dependency_tracker.py -q` | Resource registration, dependency linking, update listeners, and impact analysis pass | 2026-03-01 | PASS | 4 focused tests passing |
| V-018 | Build-guide Step 12 (I18N + digital twin) | N/A | Scope reconciliation | `N/A` | Deferred with owner + milestone | 2026-03-01 | DEFERRED | Owner: Project maintainers; milestone: 2026-Q2 |

## Non-Functional Verification

| ID | Quality Goal | Method | Command(s) | Expected Outcome | Last Verified | Status | Notes |
|---|---|---|---|---|---|---|---|
| Q-001 | Linting baseline | Flake8 | `python -m flake8 civ_arcos tests` | No blocking lint errors | 2026-03-01 | NOT_RUN | Run in final verification pass |
| Q-002 | Formatting baseline | Black check | `python -m black --check civ_arcos tests` | No formatting drift | 2026-03-01 | NOT_RUN | Run in final verification pass |
| Q-003 | Type safety baseline | MyPy | `mypy civ_arcos` | No critical type errors | 2026-03-01 | NOT_RUN | Run in final verification pass |
| Q-004 | Coverage baseline | coverage.py | `coverage run -m pytest -q && coverage report -m` | Coverage recorded and >=91% target | 2026-03-01 | NOT_RUN | Run in final verification pass |
| Q-005 | Docs consistency gate | Scripted check | `python scripts/docs_consistency_check.py` | Build guide/matrix/status consistency passes | 2026-03-01 | NOT_RUN | Script now reads `build_docs/build-guide.md` |

## Release Readiness Checklist

- [ ] All in-scope `V-*` rows are `PASS` or explicitly `DEFERRED`.
- [ ] All `Q-*` rows are `PASS`.
- [ ] `build_docs/STATUS.md` updated with latest confidence and date.
- [ ] Deferred items include owner + target milestone.
