# CIV-ARCOS Unified Improvements

Reviewed sources:
- `copilot-software-improvements.md` (**primary / tie-break winner**)
- `claude-improvements.md`
- `chatgpt-improvements.md`

## Merge Policy

When recommendations overlap or conflict, `copilot-software-improvements.md` is authoritative.
- Priority and implementation order follow Copilot.
- Additional items from Claude/ChatGPT are included when they do not contradict Copilot.

---

## Priority 1 — Core Software Improvements (Copilot baseline)

### Highest ROI
1. Add a formal plugin sandbox boundary (process isolation + resource/time limits), not just code validation.
2. Split the large API surface into domain modules with a registry to reduce coupling and regression risk.
3. Introduce versioned contracts for key payloads (evidence, assurance case, risk report) to avoid schema drift.
4. Add idempotency keys and replay protection to write endpoints/webhooks.
5. Add persistence abstraction tests (cold start, crash recovery, concurrent writes) for graph/cache/task layers.

### Reliability & Operability
1. Add a unified health model: liveness, readiness, and dependency health (cache/tasks/sync connectors).
2. Add structured logging + correlation IDs across request → evidence collection → assurance generation.
3. Add backpressure/queue limits for async tasks and WebSocket broadcasts to prevent memory spikes.
4. Define SLOs for critical flows (analysis latency, badge generation, webhook processing) and alert thresholds.
5. Add deterministic safe-mode startup that disables optional systems (AI, federation, marketplace) cleanly.

### Security & Trust
1. Harden webhook auth (signature validation, timestamp tolerance, nonce cache).
2. Add tenant-bound authorization checks at every read/write path, with explicit isolation tests.
3. Add secret-scanning and forbidden-config checks in CI for examples/tests/docs too.
4. Add cryptographic key rotation and audit-log immutability verification jobs.

### Quality Engineering
1. Add contract tests for every public API endpoint and plugin interface.
2. Add mutation/property tests for risk scoring and assurance template logic.
3. Track coverage by critical module (not just global percentage), with a no-drop policy on core paths.
4. Add reproducible fixture datasets for benchmark/risk/compliance tests to prevent flaky outcomes.

---

## Priority 2 — Documentation & Build-System Corrections (from ChatGPT + Claude)

These are complementary and non-conflicting; they improve rebuild reliability and contributor onboarding.

1. Fix cross-document step mapping inconsistencies (`README` vs step files) and include Step 1 explicitly.
2. Reconcile status drift (`IMPLEMENTATION`/summary says Step 1 while later steps are complete in other docs).
3. Normalize step taxonomy (`Step 5`, `5.5`, `5_6`, `5 Enterprise`) into a canonical sequence.
4. Add a single clean rebuild runbook with deterministic commands and expected outputs.
5. Add per-step verification gates (commands, expected outputs, artifacts).
6. Repair Markdown defects/typos in long guide files to restore trust and searchability.
7. Add doc CI checks (lint, spellcheck, links, heading format checks).

---

## Priority 3 — Platform Foundations to Adopt Early (from Claude, aligned)

1. Move packaging to `pyproject.toml` (PEP 517/518); keep dependency policy minimal/homegrown where required.
2. Add CI from Day 1 (format, lint, type-check, tests, security scan).
3. Enforce coverage floor in CI (start lower, raise over phases).
4. Add environment-variable-first configuration for deployability.
5. Add a developer task runner (`Makefile` or equivalent) for repeatable local workflows.
6. Add graph schema versioning + migration strategy for persistence compatibility.
7. Add relationship indexing early to avoid graph performance regressions.
8. Add Docker health checks for runtime resilience.
9. Introduce API versioning prefix early (`/api/v1/...`) to reduce refactor risk later.

---

## Priority 4 — Strategic Enhancements (later-phase)

1. OpenAPI schema generation in the custom framework for large endpoint surface management.
2. TLS support in the custom web framework/deployment path.
3. Property-based testing expansion (`hypothesis`) for integrity-critical logic.
4. Long-range roadmap extension beyond Step 10 (compliance module completion and platform maturity).
5. Clarify emulation philosophy boundaries where security-sensitive subsystems are concerned.

---

## Unified Implementation Order (Copilot-wins)

1. Plugin sandbox hardening
2. API modularization + contract versioning
3. Webhook/idempotency security controls
4. Health model + observability baseline
5. Persistence and isolation testing expansion
6. Quality engineering upgrades (contract/mutation/module-critical coverage)
7. Documentation normalization + rebuild runbook + verification matrix
8. Build/packaging modernization (`pyproject.toml`, CI gates, env-config hardening)
9. Later strategic enhancements (OpenAPI, TLS, advanced test methods)

---

## Quick Wins (1–2 days)

1. Create canonical docs truth files: `STATUS.md` and `VERIFICATION_MATRIX.md`.
2. Fix README step mapping and status wording drift.
3. Add baseline CI job with lint/type/test/security checks.
4. Add structured logging + correlation ID middleware.
5. Add webhook signature + replay protection.

---

## Notes

- This unified plan intentionally preserves Copilot recommendations as the default decision path.
- ChatGPT/Claude recommendations are merged where they strengthen execution quality without changing Copilot’s priority model.
