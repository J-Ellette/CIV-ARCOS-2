# CIV-ARCOS Build Guide (Updated Worklist)

Last updated: 2026-02-28  
Source scope: all `.md` files under `build_docs/`.

## Purpose

This file consolidates items in `build_docs/` that are still not implemented, partial, pending verification, or explicitly marked as future work.

## A) Core implementation backlog

Source: `build_docs/improvements.md`.

- Reliability and operability:
  - Add backpressure/queue limits for async tasks and WebSocket broadcasts.
  - Define SLOs and alert thresholds for critical flows.
  - Add deterministic safe-mode startup for optional systems.
- Security and trust:
  - Extend tenant-bound authorization to all read/write paths (currently partial).
  - Add secret-scanning and forbidden-config checks in CI (including examples/tests/docs).
  - Add cryptographic key rotation and audit-log immutability verification jobs.
- Quality engineering:
  - Add contract tests for every public API endpoint and plugin interface.
  - Add mutation/property tests for risk scoring and assurance templates.
  - Track coverage by critical module with a no-drop policy.
  - Add reproducible fixture datasets for benchmark/risk/compliance tests.
- Documentation/build-system corrections:
  - Reconcile cross-document step mapping and status drift.
  - Normalize Step 5 taxonomy variants.
  - Add deterministic rebuild runbook with expected outputs.
  - Add per-step verification gates and artifact expectations.
  - Add doc CI checks (lint/spellcheck/links/heading format).
- Platform modernization:
  - Migrate packaging to `pyproject.toml`.
  - Add CI gates (format/lint/type/test/security).
  - Enforce coverage floors in CI.
  - Add environment-variable-first configuration hardening.
  - Add developer task runner and graph schema versioning/migrations.
- Strategic enhancements:
  - OpenAPI generation.
  - TLS support in custom framework/deployment.
  - Property-based testing expansion.

## B) Verification backlog (`NOT_RUN`)

Source: `build_docs/VERIFICATION_MATRIX.md`.

Status update (2026-02-28): `NOT_RUN` rows have now been closed in the matrix and replaced with `PASS`, `FAIL`, or `PARTIAL` outcomes.

### Remediation checklist (from current FAIL/PARTIAL outcomes)

#### FAIL rows (5)

- [ ] **V-008 (FAIL): cache/task load stability checks are stale**
  - Gap: matrix command references missing modules/tests (`civ_arcos/core/cache.py`, `civ_arcos/core/tasks.py`, related test files).
  - Action:
    - Decide whether cache/tasks are still in scope.
    - If in scope: implement/restore modules + tests and run concurrency/load checks.
    - If out of scope: mark deferred with owner/milestone and update matrix source modules/claim.
  - Exit criterion: row is `PASS` with executable command, or explicitly `DEFERRED` (tracked owner + milestone).

- [ ] **V-012 (FAIL): I18N + digital twin verification paths are stale**
  - Gap: referenced modules/tests are absent from current workspace.
  - Action:
    - Reconcile docs vs repository state for I18N/digital twin.
    - Either restore implementation/tests or update matrix + status docs to deferred/archived scope.
  - Exit criterion: row is `PASS` with runnable command, or explicitly deferred with ownership.

- [ ] **Q-001 (FAIL): flake8 baseline fails**
  - Gap: existing codebase has many lint violations.
  - Action:
    - Define lint policy (scope, ignores, max-line-length, staged adoption).
    - Triage violations into mechanical vs semantic fixes.
    - Apply fixes in targeted batches and re-run flake8.
  - Exit criterion: agreed baseline command returns exit code 0.

- [x] **Q-002 (FAIL): black --check fails**
  - Gap: formatter reports 47 files would be reformatted.
  - Action:
    - Run black formatting in a dedicated formatting PR/slice.
    - Re-run `black --check civ_arcos tests`.
  - Exit criterion: formatter check passes with no files changed.
  - Result (2026-02-28): ✅ `python -m black --check civ_arcos tests` passes (`64 files would be left unchanged`) after applying `python -m black civ_arcos tests`.

- [x] **Q-003 (FAIL): mypy baseline fails**
  - Gap: current run reports 2 mypy errors.
  - Action:
    - Fix concrete typed errors in `civ_arcos/adapters/github_adapter.py` and `civ_arcos/api.py`.
    - Re-run mypy and confirm clean exit.
  - Exit criterion: `mypy civ_arcos` exits 0.
  - Result (2026-02-28): ✅ `mypy civ_arcos` passes (`Success: no issues found in 41 source files`).

#### PARTIAL rows (3)

- [x] **V-007 (PARTIAL): dashboard route smoke exists, dedicated test missing**
  - Current evidence: `/dashboard` returns HTTP 200.
  - Action:
    - Add dedicated dashboard route/render assertions in integration/unit tests.
    - Update matrix command to point at existing test file(s).
  - Exit criterion: dedicated test command passes and row moves to `PASS`.
  - Result (2026-02-28): ✅ `python -m pytest tests/integration/test_dashboard.py -q` passes (`2 passed`) and matrix row is now `PASS`.

- [ ] **V-011 (PARTIAL): blockchain checks pass, federated/sync coverage missing**
  - Current evidence: blockchain integration checks pass.
  - Action:
    - Add or restore federated/sync tests (or update claim scope to blockchain-only if intentionally removed).
    - Align matrix source modules + command with actual codebase.
  - Exit criterion: full distributed claim covered by runnable tests and row moves to `PASS` (or scoped/deferred clearly).

- [ ] **Q-005 (PARTIAL): docs consistency gate is undefined**
  - Current evidence: manual review indicates drift + markdown lint issues.
  - Action:
    - Define explicit docs-consistency command(s) and pass criteria.
    - Add command to matrix row and run it in CI/local.
  - Exit criterion: row has defined automated check and passes.

### Release checklist items still open

- [ ] All in-scope `V-*` rows are `PASS` or explicitly deferred.
- [ ] All `Q-*` rows are `PASS`.
- [ ] Deferred items are logged with owner and target milestone.

## C) Step-level items explicitly partial/pending

- Step 1 (`build_docs/STEP_01.md`): authentication/authorization deferred.
- Step 2 (`build_docs/STEP_02.md`): mutation testing remains a placeholder.
- Step 5.0 (`build_docs/STEP_05.0.md`): threading tests skipped/pending in cache/tasks unit tests.
- Step 9 (`build_docs/STEP_09.md`): full marketplace lifecycle, community platform, GraphQL ecosystem, and additional webhooks still marked planned/partial.

## D) Compliance module backlog

Source: `build_docs/compliance-module-guide.md` ("Remaining Modules").

- CIV-STIG
- CIV-GRUNDSCHUTZ
- CIV-ACAS
- CIV-NESSUS
- Software Supply Chain Security
- SBOM
- Accelerated ATO
- DEF STAN 00-970
- MIL-STD-498
- SOC 2 Type II
- ISO 27001
- FedRAMP
- CSA STAR
- CASE/4GL Development Tools
- Verification & Validation Tools
- Configuration Management Systems
- System Design & Architecture Tools
- Mathematical & Statistical Analysis
- RegScale
- ARMATURE Fabric
- Qualtrax
- UiPath Platform
- Hyland Solutions
- Automated Cryptographic Validation (NIST ACVP)
- NIST RMM API
- Dioptra

## E) Optional future-enhancement parking lot

These are listed as optional/future in step docs and are not currently in baseline scope:

- `build_docs/STEP_04.0.md`
- `build_docs/STEP_05-06.md`
- `build_docs/STEP_05.5.md`
- `build_docs/STEP_05_ENTERPRISE.md`
- `build_docs/STEP_06.md`
- `build_docs/STEP_07.md`
- `build_docs/STEP_08.md`
- `build_docs/STEP_09.md`
- `build_docs/STEP_10.md`

## F) Status/document drift items to reconcile

- `build_docs/STATUS.md`: all phases marked "Needs Central Re-Check".
- `build_docs/IMPLEMENTATION.md`: still reports "Step 1 Complete" and older metrics; requires modernization or archival labeling.

## Suggested execution order

1. ~~Close all `NOT_RUN` verification rows in `VERIFICATION_MATRIX.md`.~~ ✅ Completed (2026-02-28).
2. Complete tenant-bound authorization expansion across remaining write-heavy domains.
3. Deliver quality-engineering upgrades (contract breadth, mutation/property tests, module coverage gates).
4. Complete docs normalization + deterministic rebuild runbook + doc CI checks.
5. Start compliance modules in prioritized slices.

## Update protocol

When an item is implemented:

1. Update this file.
2. Update `README.md` roadmap.
3. Update `copilot.md` tracker.
4. Update `build_docs/STATUS.md` changelog.
5. Update `build_docs/VERIFICATION_MATRIX.md` with passing evidence.
