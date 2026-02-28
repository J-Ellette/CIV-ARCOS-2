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
| V-001 | Base API health endpoint works | `civ_arcos/api.py` | Integration smoke | `python -m civ_arcos.api` then `GET /api/status` | 200 + valid JSON health payload | — | NOT_RUN | Seeded from Step 1 docs |
| V-002 | Evidence graph persistence/load works | `civ_arcos/storage/graph.py` | Unit tests + manual reload | `pytest tests/unit/test_graph.py -q` | Tests pass; persisted data reloads correctly | — | NOT_RUN | Add crash-recovery test case |
| V-003 | Evidence checksum/provenance integrity | `civ_arcos/evidence/collector.py` | Unit tests | `pytest tests/unit/test_evidence.py -q` | Checksums stable; provenance fields present | — | NOT_RUN | |
| V-004 | Badge generation endpoints produce valid SVG | `civ_arcos/web/badges.py`, `civ_arcos/api.py` | Unit + endpoint check | `pytest tests/unit/test_badges.py -q` | All tests pass; SVG responses valid | — | NOT_RUN | |
| V-005 | Static/security/test analysis pipeline runs | `civ_arcos/analysis/*` | Unit + integration subset | `pytest tests/unit/test_static_analyzer.py tests/unit/test_security_scanner.py tests/unit/test_test_generator.py -q` | Tests pass for all analyzers | — | NOT_RUN | |
| V-006 | Assurance case generation/validation | `civ_arcos/assurance/*` | Unit tests | `pytest tests/unit/test_*assurance* -q` | GSN/case/template tests pass | — | NOT_RUN | Adjust pattern if file names differ |
| V-007 | Dashboard routes render HTML | `civ_arcos/web/dashboard.py`, `civ_arcos/api.py` | Unit + route check | `pytest tests/unit/test_dashboard.py -q` | Dashboard tests pass and pages include expected sections | — | NOT_RUN | |
| V-008 | Cache/task emulation stable under load | `civ_arcos/core/cache.py`, `civ_arcos/core/tasks.py` | Unit + concurrency tests | `pytest tests/unit/test_*cache* tests/unit/test_*task* -q` | No race-condition failures; deterministic behavior | — | NOT_RUN | Add stress benchmark |
| V-009 | Webhook auth hardening (signature/replay) | `civ_arcos/web/webhook.py`, `civ_arcos/api.py` | Unit + integration tests | `pytest tests/unit/test_webhook.py tests/integration/test_health_webhook.py -q` | Signature validation, replay cache, and endpoint tests pass | 2026-02-28 | PASS | 22 tests passing |
| V-010 | Multi-tenant isolation enforced | `civ_arcos/core/tenants.py`, API layer | Unit + integration | `pytest tests/unit/test_tenants.py tests/integration/test_enterprise_api.py -q` | Tenant cross-read/write blocked | — | NOT_RUN | Add explicit negative isolation tests |
| V-011 | Distributed ledger/network/sync features | `civ_arcos/distributed/*` | Unit + integration | `pytest tests/unit/test_federated_network.py tests/unit/test_blockchain_ledger.py tests/unit/test_sync_engine.py -q` | Core distributed tests pass | — | NOT_RUN | Some integration post endpoints historically partial |
| V-012 | I18N + digital twin endpoints | `civ_arcos/core/i18n.py`, `civ_arcos/core/digital_twin.py` | Unit + integration | `pytest tests/unit/test_i18n.py tests/unit/test_digital_twin.py tests/integration/test_i18n_digitaltwin_api.py -q` | All endpoint behaviors validated | — | NOT_RUN | |
| V-013 | Structured logging + correlation IDs | `civ_arcos/web/framework.py` | Unit tests | `pytest tests/unit/test_framework_logging.py -q` | JSON log lines emitted; X-Correlation-ID header on every response | 2026-02-28 | PASS | 10 tests passing |
| V-014 | Health endpoints (live/ready/dependencies) | `civ_arcos/api.py` | Integration tests | `pytest tests/integration/test_health_webhook.py -k health -q` | All health probes return correct status codes and bodies | 2026-02-28 | PASS | 9 tests passing |

---

## Non-Functional Verification

| ID | Quality Goal | Method | Command(s) | Expected Outcome | Last Verified | Status | Notes |
|---|---|---|---|---|---|---|---|
| Q-001 | Linting baseline | Flake8 | `flake8 civ_arcos tests` | No blocking lint errors | — | NOT_RUN | |
| Q-002 | Formatting baseline | Black check | `black --check civ_arcos tests` | No formatting drift | — | NOT_RUN | |
| Q-003 | Type safety baseline | MyPy | `mypy civ_arcos` | No critical type errors | — | NOT_RUN | |
| Q-004 | Coverage baseline | Pytest + coverage | `pytest --cov=civ_arcos --cov-report=term-missing` | Coverage recorded and tracked | — | NOT_RUN | Add phase-specific gates |
| Q-005 | Docs consistency | Manual + doc lint | (to be defined) | Step/status/docs aligned | — | NOT_RUN | Add CI doc checks |

---

## Release Readiness Checklist

Mark all as complete before a formal release candidate:

- [ ] All `V-*` rows for in-scope features are `PASS` or explicitly deferred.
- [ ] All `Q-*` rows are `PASS`.
- [ ] `STATUS.md` updated with current confidence and verification date.
- [ ] Deferred items logged with owner + target milestone.

## Change Log

- 2026-02-28: Initial matrix created with seeded claims and commands.
