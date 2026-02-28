# CIV-ARCOS Verification Matrix

Last updated: 2026-02-28
Purpose: Map each major claim to concrete verification evidence.

## Status Legend

- `NOT_RUN` — not executed yet in centralized verification flow
- `PASS` — executed and matched expected outcome
- `FAIL` — executed and did not match expected outcome
- `PARTIAL` — partially verified; follow-up needed

## How to Use

For each row:
1. Run the command(s) in the current workspace.
2. Capture output summary and timestamp.
3. Set status.
4. Link follow-up issue if failing or partial.

---

## Core Claims Verification

| ID | Feature/Claim | Source Module(s) | Test / Check | Command(s) | Expected Outcome | Last Verified | Status | Notes / Follow-up |
|---|---|---|---|---|---|---|---|---|
| V-001 | Base API health endpoint works | `civ_arcos/api.py` | Integration smoke | `python -m civ_arcos.api` then `GET /api/status` | 200 + valid JSON health payload | 2026-02-28 | PASS | Verified with live HTTP call: `/api/status` returned 200 and version payload |
| V-002 | Evidence graph persistence/load works | `civ_arcos/storage/graph.py` | Unit tests + manual reload | `pytest tests/unit/test_graph.py -q` | Tests pass; persisted data reloads correctly | 2026-02-28 | PASS | 9 tests passing |
| V-003 | Evidence checksum/provenance integrity | `civ_arcos/evidence/collector.py` | Unit tests | `pytest tests/unit/test_evidence.py -q` | Checksums stable; provenance fields present | 2026-02-28 | PASS | 8 tests passing |
| V-004 | Badge generation endpoints produce valid SVG | `civ_arcos/web/badges.py`, `civ_arcos/api.py` | Unit + endpoint check | `pytest tests/unit/test_badges.py -q` | All tests pass; SVG responses valid | 2026-02-28 | PASS | 8 tests passing |
| V-005 | Static/security/test analysis pipeline runs | `civ_arcos/analysis/*` | Unit + integration subset | `pytest tests/unit/test_static_analyzer.py tests/unit/test_security_scanner.py tests/unit/test_test_generator.py -q` | Tests pass for all analyzers | 2026-02-28 | PASS | 21 tests passing |
| V-006 | Assurance case generation/validation | `civ_arcos/assurance/*` | Unit tests | `pytest tests/unit/test_case.py tests/unit/test_gsn.py tests/unit/test_templates.py -q` | GSN/case/template tests pass | 2026-02-28 | PASS | Original glob command stale in PowerShell; adjusted assurance suite passed (21 tests) |
| V-007 | Dashboard routes render HTML | `civ_arcos/api.py`, `civ-arcos-carbon.html` | Integration route/render check | `python -m pytest tests/integration/test_dashboard.py -q` | Dashboard tests pass and HTML includes expected Carbon markers | 2026-02-28 | PASS | Dedicated dashboard test added; command passes (2 tests) |
| V-008 | Cache/task emulation stable under load | `civ_arcos/core/cache.py`, `civ_arcos/core/tasks.py` | Unit + concurrency tests | `pytest tests/unit/test_*cache* tests/unit/test_*task* -q` | No race-condition failures; deterministic behavior | 2026-02-28 | FAIL | Referenced cache/task test files and core modules are absent in current workspace; add/update scope before re-run |
| V-009 | Webhook auth hardening (signature/replay) | `civ_arcos/web/webhook.py`, `civ_arcos/api.py` | Unit + integration tests | `pytest tests/unit/test_webhook.py tests/integration/test_health_webhook.py -q` | Signature validation, replay cache, and endpoint tests pass | 2026-02-28 | PASS | 22 tests passing |
| V-010 | Multi-tenant isolation enforced | `civ_arcos/core/tenants.py`, API layer | Unit + integration | `pytest tests/integration/test_api.py -k "tenant or settings or evidence" -q` | Tenant cross-read/write blocked | 2026-02-28 | PASS | Legacy command referenced missing files; adjusted integration selection passed (12 tests) including cross-tenant deny paths |
| V-011 | Distributed ledger/network/sync features | `civ_arcos/distributed/*` | Unit + integration | `pytest tests/integration/test_api.py -k blockchain -q` | Core distributed tests pass | 2026-02-28 | PARTIAL | Blockchain integration checks pass (3 tests), but federated/sync test files referenced in matrix are absent |
| V-012 | I18N + digital twin endpoints | `civ_arcos/core/i18n.py`, `civ_arcos/core/digital_twin.py` | Unit + integration | `pytest tests/unit/test_i18n.py tests/unit/test_digital_twin.py tests/integration/test_i18n_digitaltwin_api.py -q` | All endpoint behaviors validated | 2026-02-28 | FAIL | Referenced modules/tests are not present in current workspace; verification cannot be executed without restored implementation |
| V-013 | Structured logging + correlation IDs | `civ_arcos/web/framework.py` | Unit tests | `pytest tests/unit/test_framework_logging.py -q` | JSON log lines emitted; X-Correlation-ID header on every response | 2026-02-28 | PASS | 10 tests passing |
| V-014 | Health endpoints (live/ready/dependencies) | `civ_arcos/api.py` | Integration tests | `pytest tests/integration/test_health_webhook.py -k health -q` | All health probes return correct status codes and bodies | 2026-02-28 | PASS | 9 tests passing |
| V-015 | Write-endpoint idempotency controls | `civ_arcos/web/idempotency.py`, `civ_arcos/api.py` | Unit + integration tests | `pytest tests/unit/test_idempotency.py tests/integration/test_api.py -q` | Same key+payload replays first response; same key+different payload returns 409 conflict | 2026-02-28 | PASS | 14 tests passing (5 unit, 9 integration) |
| V-016 | Versioned contracts and modular v1 routes | `civ_arcos/contracts/v1.py`, `civ_arcos/api_routes/*`, `civ_arcos/api.py` | Integration tests | `pytest tests/integration/test_api.py -q` | `/api/v1/*` endpoints return contract envelope (`contract`, `generated_at`, `data`) with expected domain payloads | 2026-02-28 | PASS | Includes contract registry + evidence + assurance v1 endpoint coverage |
| V-017 | Plugin sandbox boundary controls | `civ_arcos/core/plugin_marketplace.py`, `civ_arcos/api.py` | Unit + integration tests | `pytest tests/unit/test_plugin_marketplace.py tests/integration/test_plugin_api.py -q` | AST validation blocks forbidden imports; isolated execution returns result, timeout path returns 408, idempotent replay supported | 2026-02-28 | PASS | 10 tests passing (5 unit, 5 integration) |
| V-018 | Platform domain modularization + v1 contracts | `civ_arcos/api_routes/platform.py`, `civ_arcos/contracts/v1.py`, `civ_arcos/api.py` | Integration tests | `pytest tests/integration/test_api.py -q` | Legacy `/api/risk|compliance|analytics` routes remain functional and `/api/v1/risk|compliance|analytics` return correct contract envelopes | 2026-02-28 | PASS | 4 dedicated integration assertions added for risk/compliance/analytics v1 + legacy compatibility |
| V-019 | Admin domain modularization + v1 contracts | `civ_arcos/api_routes/admin.py`, `civ_arcos/contracts/v1.py`, `civ_arcos/api.py` | Integration tests | `pytest tests/integration/test_api.py -q` | Legacy `/api/tenants|settings` routes remain functional and `/api/v1/tenants|settings` return correct contract envelopes | 2026-02-28 | PASS | 3 dedicated integration assertions added for tenants/settings v1 + legacy compatibility |
| V-020 | Plugin domain modularization + v1 contracts | `civ_arcos/api_routes/plugins.py`, `civ_arcos/contracts/v1.py`, `civ_arcos/api.py` | Integration tests | `pytest tests/integration/test_plugin_api.py tests/integration/test_api.py -q` | Legacy `/api/plugins/*` routes remain functional and `/api/v1/plugins/*` return correct contract envelopes and idempotent replay behavior | 2026-02-28 | PASS | 2 dedicated v1 plugin contract assertions + contract registry validation |
| V-021 | Analysis + assurance domain extraction and v1 expansion | `civ_arcos/api_routes/analysis.py`, `civ_arcos/api_routes/assurance.py`, `civ_arcos/api_routes/assurance_v1.py`, `civ_arcos/contracts/v1.py`, `civ_arcos/api.py` | Integration tests | `pytest tests/integration/test_api.py tests/integration/test_plugin_api.py tests/integration/test_health_webhook.py -q` | Legacy `/api/analysis/*` and `/api/assurance*` remain available while new `/api/v1/analysis/*` plus `/api/v1/assurance/templates` and `/api/v1/assurance/auto-generate` return contract envelopes | 2026-02-28 | PASS | Combined integration run: 43 passing |
| V-022 | Persistence/isolation testing expansion (storage baseline) | `civ_arcos/storage/graph.py`, `civ_arcos/evidence/collector.py`, `tests/unit/test_graph.py`, `tests/unit/test_evidence.py` | Unit + integration regression | `pytest tests/unit/test_graph.py tests/unit/test_evidence.py tests/integration/test_api.py tests/integration/test_plugin_api.py tests/integration/test_health_webhook.py -q` | Cold-start recovery, atomic-save failure safety, and concurrent-write persistence pass in unit tests with no API regressions | 2026-02-28 | PASS | 60 passing total (17 unit + 43 integration) |
| V-023 | Tenant-bound authorization + cross-tenant isolation (admin v1) | `civ_arcos/api_routes/admin.py`, `tests/integration/test_api.py` | Integration + regression | `pytest tests/integration/test_api.py tests/integration/test_plugin_api.py tests/integration/test_health_webhook.py tests/unit/test_graph.py tests/unit/test_evidence.py -q` | `/api/v1/settings` requires tenant identity, cross-tenant read/write attempts are denied, and per-tenant settings updates do not leak across tenants | 2026-02-28 | PASS | 64 passing total (25 api integration + 39 adjacent regression tests) |
| V-024 | Tenant-bound evidence collection + cross-tenant evidence read isolation (v1) | `civ_arcos/api_routes/evidence_v1.py`, `civ_arcos/contracts/v1.py`, `civ_arcos/evidence/collector.py`, `tests/integration/test_api.py` | Integration + regression | `pytest tests/integration/test_api.py tests/integration/test_plugin_api.py tests/integration/test_health_webhook.py tests/unit/test_graph.py tests/unit/test_evidence.py -q` | `/api/v1/evidence/collect` requires tenant identity, v1 evidence list is tenant-scoped under tenant context, and cross-tenant evidence detail reads are denied | 2026-02-28 | PASS | 67 passing total (28 api integration + 39 adjacent regression tests) |

---

## Non-Functional Verification

| ID | Quality Goal | Method | Command(s) | Expected Outcome | Last Verified | Status | Notes |
|---|---|---|---|---|---|---|---|
| Q-001 | Linting baseline | Flake8 | `flake8 civ_arcos tests` | No blocking lint errors | 2026-02-28 | FAIL | Flake8 exits non-zero with many existing style violations (line length/unused imports/indent) |
| Q-002 | Formatting baseline | Black check | `python -m black --check civ_arcos tests` | No formatting drift | 2026-02-28 | PASS | Applied `python -m black civ_arcos tests`; re-check passes (64 files unchanged) |
| Q-003 | Type safety baseline | MyPy | `mypy civ_arcos` | No critical type errors | 2026-02-28 | PASS | Fixed typing issues in `civ_arcos/adapters/github_adapter.py` and `civ_arcos/api.py`; `mypy civ_arcos` now exits clean |
| Q-004 | Coverage baseline | Pytest + coverage | `coverage run -m pytest -q && coverage report -m` | Coverage recorded and tracked | 2026-02-28 | PASS | `pytest --cov` unavailable (plugin missing); coverage.py fallback succeeded with 169 passing tests and 91% total coverage |
| Q-005 | Docs consistency | Manual + doc lint | (to be defined) | Step/status/docs aligned | 2026-02-28 | PARTIAL | Manual review + diagnostics indicate drift and markdown lint issues; formal command/gate still needs definition |

---

## Release Readiness Checklist

Mark all as complete before a formal release candidate:

- [ ] All `V-*` rows for in-scope features are `PASS` or explicitly deferred.
- [ ] All `Q-*` rows are `PASS`.
- [ ] `STATUS.md` updated with current confidence and verification date.
- [ ] Deferred items logged with owner + target milestone.

## Change Log

- 2026-02-28: Initial matrix created with seeded claims and commands.
- 2026-02-28: Added V-015 for idempotency key controls with passing verification command.
- 2026-02-28: Added V-016 for v1 contract endpoints and modular route registration.
- 2026-02-28: Added V-017 for plugin sandbox validation/execution controls.
- 2026-02-28: Added V-018 for platform route extraction and v1 risk/compliance/analytics contracts.
- 2026-02-28: Added V-019 for admin route extraction and v1 tenants/settings contracts.
- 2026-02-28: Added V-020 for plugin route extraction and v1 plugin contracts.
- 2026-02-28: Added V-021 for analysis/assurance route extraction and v1 endpoint expansion.
- 2026-02-28: Added V-022 for persistence/isolation testing expansion (storage baseline).
- 2026-02-28: Added V-023 for tenant-bound authorization and cross-tenant isolation checks in admin v1 routes.
- 2026-02-28: Added V-024 for tenant-bound v1 evidence collection and cross-tenant evidence read isolation checks.
- 2026-02-28: Closed all previously `NOT_RUN` rows (V-001..V-012 and Q-001..Q-005) with executed outcomes and updated commands where legacy references were stale.
- 2026-02-28: Updated Q-003 from FAIL to PASS after targeted mypy fixes (`mypy civ_arcos` clean).
