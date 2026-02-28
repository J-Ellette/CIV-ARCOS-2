# CIV-ARCOS

Civilian Assurance-based Risk Computation and Orchestration System.

CIV-ARCOS adapts assurance-driven engineering patterns into a practical platform for software quality evidence collection, risk analysis, assurance case generation, and operational visibility.

## What this project provides

- Evidence graph ingestion and provenance tracking
- Blockchain-style tamper-evident evidence ledger
- Static analysis, security scanning, and test suggestion workflows
- Digital assurance case generation (GSN-oriented)
- Badge generation APIs for quality/coverage/security reporting
- Operational API with health probes, structured logs, correlation IDs, and webhook security
- Idempotency controls on write endpoints
- Versioned API contract surface (`/api/v1/*`)
- IBM Carbon-based operational console UI (`civ-arcos-carbon.html`)

## Design system decisions

- Operational console surfaces use IBM Carbon Design System (G100 dark theme).
- Exported report and public-facing surfaces should use USWDS patterns.
- USWDS output must not include the "An official website of the United States government" top banner (this is not government software).

## Current status

- Core backend platform: implemented and tested
- Operational console (Carbon): implemented across all planned pages
- API modularization + contract versioning: phase 2 baseline implemented (Evidence, Assurance, Analysis, Risk, Compliance, Analytics, Tenants, Settings, and Plugins modularized with `/api/v1` contract coverage)
- Central verification tracking: maintained in `build_docs/VERIFICATION_MATRIX.md`

## Roadmap next up

This section mirrors `build_docs/improvements.md` (Copilot-priority implementation order) and should be updated as items move.

- **1) Plugin sandbox hardening**
  - Status: implemented (baseline)
  - Done: AST-based plugin validation, isolated subprocess execution (`-I`), timeout controls, and bounded output capture.
  - Next: add permission profiles and stricter host capability controls per plugin type.

- **2) API modularization + contract versioning (phase 2)**
  - Status: implemented (baseline)
  - Done: modular route registration for legacy and `/api/v1` surfaces across Evidence, Assurance, Analysis, Risk, Compliance, Analytics, Tenants, Settings, and Plugins; contract tests cover all current high-traffic endpoints.
  - Next: expand schema-level contract assertions and add compatibility regression gates in CI.

- **3) Webhook/idempotency security controls**
  - Status: implemented (baseline)
  - Done: HMAC validation, replay checks, idempotency key controls for key write endpoints.

- **4) Health model + observability baseline**
  - Status: implemented (baseline)
  - Done: liveness/readiness/dependencies endpoints plus correlation IDs and structured request logging.

- **5) Persistence and isolation testing expansion**
  - Status: in progress
  - Done: explicit cold-start, atomic-save recovery, and concurrent-write verification for `EvidenceGraph` and `EvidenceStore`; tenant-bound authorization checks and cross-tenant isolation tests for v1 admin routes; tenant-bound v1 evidence collection and scoped/cross-tenant read checks.
  - Next: carry tenant-bound authorization into additional write-heavy domains (assurance/plugin operations) as tenancy model matures.

- **6) Quality engineering upgrades**
  - Status: partially in progress
  - Done: focused endpoint integration tests and idempotency/contract tests.
  - Next: contract coverage expansion, mutation/property testing, critical-module coverage gates.

- **7) Documentation normalization + rebuild runbook + verification matrix hardening**
  - Status: in progress
  - Done: canonical status + verification matrix + expanded README.
  - Next: deterministic rebuild runbook and doc CI checks.

- **8) Build/packaging modernization**
  - Status: not started
  - Goal: `pyproject.toml`, CI gates, packaging cleanup, and environment-config hardening.

- **9) Strategic enhancements**
  - Status: not started
  - Scope: OpenAPI generation, TLS support, advanced test methods, and later-stage platform maturity work.

See also:

- `copilot.md` (implementation tracker)
- `build_docs/STATUS.md` (canonical status)
- `build_docs/improvements.md` (priority roadmap)

## Repository layout

```text
civ_arcos/
  api.py                    # API entrypoint and route registration
  analysis/                 # static/security/test analysis modules
  assurance/                # assurance case and GSN tooling
  contracts/                # versioned API contract serializers (v1)
  api_routes/               # modular route registration (v1 domains)
  distributed/              # blockchain ledger and distributed primitives
  evidence/                 # evidence model and storage interactions
  storage/                  # graph storage engine
  web/                      # lightweight web framework, badges, webhook/idempotency

tests/
  unit/                     # unit tests
  integration/              # integration tests

build_docs/                 # build and implementation documentation
civ-arcos-carbon.html       # operational console UI
copilot.md                  # implementation progress log
```

## Requirements

- Python 3.9+
- No runtime third-party dependencies are required (stdlib-first runtime)
- Dev tools: `pytest`, `coverage`, `black`, `mypy`, `flake8`

## Quick start

### 1) Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install development dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

### 3) Run the API

```powershell
python -m civ_arcos.api
```

API base URL: `http://localhost:8080`

### 4) Open the operational console

- Browser open: `civ-arcos-carbon.html`
- Or via API route: `http://localhost:8080/dashboard`

## Testing and quality checks

### Run full tests

```powershell
python -m pytest tests/ -q
```

### Targeted test examples

```powershell
python -m pytest tests/integration/test_api.py -q
python -m pytest tests/integration/test_health_webhook.py -q
python -m pytest tests/unit/test_idempotency.py -q
```

### Optional developer checks

```powershell
black --check civ_arcos tests
flake8 civ_arcos tests
mypy civ_arcos
```

## API overview

### Core status and health

- `GET /` — API metadata
- `GET /api/status` — runtime status summary
- `GET /api/health/live` — liveness probe
- `GET /api/health/ready` — readiness probe
- `GET /api/health/dependencies` — dependency health details

### Evidence and analysis

- `POST /api/evidence/collect`
- `GET /api/evidence`
- `GET /api/evidence/{evidence_id}`
- `POST /api/analysis/static`
- `POST /api/analysis/security`
- `POST /api/analysis/tests`
- `POST /api/analysis/comprehensive`

### Assurance and quality

- `GET /api/assurance`
- `GET /api/assurance/templates`
- `POST /api/assurance/create`
- `GET /api/assurance/{case_id}`
- `GET /api/assurance/{case_id}/visualize`
- `POST /api/assurance/auto-generate`
- `GET /api/badge/coverage/{owner}/{repo}`
- `GET /api/badge/quality/{owner}/{repo}`
- `GET /api/badge/security/{owner}/{repo}`

### Risk/compliance/platform

- `GET /api/risk/map`
- `GET /api/compliance/status`
- `GET /api/analytics/trends`
- `GET /api/tenants`
- `POST /api/tenants`
- `GET /api/settings`
- `POST /api/settings`

### Ledger and webhook

- `POST /api/blockchain/add`
- `GET /api/blockchain/status`
- `GET /api/blockchain/chain`
- `POST /api/webhooks/github`

### Plugin sandbox

- `POST /api/plugins/validate`
- `POST /api/plugins/execute`

## Versioned API contracts (`/api/v1`)

Contract endpoints currently cover Evidence and Assurance domains.

- `GET /api/v1/contracts`
- `GET /api/v1/evidence`
- `GET /api/v1/evidence/{evidence_id}`
- `GET /api/v1/assurance`
- `GET /api/v1/assurance/{case_id}`
- `POST /api/v1/assurance/create`
- `GET /api/v1/risk/map`
- `GET /api/v1/compliance/status`
- `GET /api/v1/analytics/trends`
- `GET /api/v1/tenants`
- `POST /api/v1/tenants`
- `GET /api/v1/settings`
- `POST /api/v1/settings`
- `POST /api/v1/plugins/validate`
- `POST /api/v1/plugins/execute`

Contract payload envelope shape:

```json
{
  "contract": {
    "name": "AssuranceCaseDetail",
    "version": "1.0"
  },
  "generated_at": "2026-02-28T00:00:00+00:00",
  "data": {}
}
```

## Security and reliability controls

### Correlation IDs and structured logs

- Every response includes `X-Correlation-ID`
- Request flow emits structured JSON log records with timing and status

### Webhook signature validation

- Endpoint: `POST /api/webhooks/github`
- Signature header: `X-Hub-Signature-256` (`sha256=<digest>`)
- Delivery replay protection via `X-GitHub-Delivery`
- Configure secret via `CIV_WEBHOOK_SECRET`

### Idempotency keys

Write endpoints support idempotent retry behavior using `Idempotency-Key`.

- Same key + same request payload: returns cached/replayed response
- Same key + different payload: returns `409`
- Replayed responses include `X-Idempotency-Replayed: true`

## Example usage

### Collect evidence

```powershell
$body = @{ repo_url = "https://github.com/example/repo" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8080/api/evidence/collect" -ContentType "application/json" -Body $body
```

### Create an assurance case with idempotency

```powershell
$headers = @{ "Idempotency-Key" = "assurance-create-001" }
$body = @{
  project_name = "Demo Project"
  project_type = "api"
  template = "comprehensive_quality"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8080/api/assurance/create" -Headers $headers -ContentType "application/json" -Body $body
```

### Discover v1 contracts

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8080/api/v1/contracts"
```

## Operational console (`civ-arcos-carbon.html`)

The console includes pages for:

- Dashboard, Evidence Store, Assurance Cases, Code Analysis
- Quality Badges, Compliance Frameworks, Analytics/Trends
- Risk Map, CIV-SCAP, Federated Network, Blockchain Ledger
- Platform Sync, Digital Twin, Multi-Tenant, Settings

UX capabilities include command palette, keyboard shortcuts, notifications panel, settings persistence, user menu, and interactive risk matrix.

## Documentation workflow

When implementation changes are made, update all of the following in the same work session:

- Root `README.md` (feature and usage truth)
- `copilot.md` (implementation progress)
- `build_docs/STATUS.md` (canonical status + change log)
- `build_docs/VERIFICATION_MATRIX.md` (evidence-backed verification rows)

## Release checklist

Use this checklist before tagging or publishing a release candidate.

### Verification and test gates

- [ ] Run full test suite: `python -m pytest tests/ -q`
- [ ] Run focused integration checks for API/webhook/idempotency paths
- [ ] Update `build_docs/VERIFICATION_MATRIX.md` with timestamps and outcomes
- [ ] Ensure no regressions in versioned contract endpoints (`/api/v1/*`)

### API and compatibility

- [ ] Confirm legacy `/api/*` compatibility has not regressed
- [ ] Confirm contract envelope shape remains stable (`contract`, `generated_at`, `data`)
- [ ] Document any endpoint behavior changes in this `README.md`
- [ ] Document any deferred/breaking changes in `build_docs/STATUS.md`

### Operational and security checks

- [ ] Confirm liveness/readiness/dependency probes return expected statuses
- [ ] Validate webhook signature flow with `CIV_WEBHOOK_SECRET` enabled
- [ ] Validate idempotency-key behavior on write endpoints
- [ ] Verify correlation ID propagation in responses and structured logs

### Documentation and handoff

- [ ] Update root `README.md` feature and usage sections
- [ ] Update `copilot.md` completed implementation log
- [ ] Update `build_docs/STATUS.md` change log
- [ ] Update `build_docs/VERIFICATION_MATRIX.md` evidence rows

## Known limitations

- API modularization is currently partial: significant legacy routes still live in `civ_arcos/api.py` while `/api/v1` routes are modularized.
- Versioned contract coverage currently focuses on Evidence and Assurance domains; Risk/Compliance/Analytics contracts are not yet versioned.
- Persistence remains primarily in-memory/file-emulated components; full production-grade persistence isolation and crash-recovery matrix is still expanding.
- Authentication/authorization is not yet comprehensive for all API surfaces (multi-tenant isolation hardening remains a roadmap item).
- WebSocket real-time channel infrastructure referenced in planning docs is not yet a validated, active runtime component in this repository state.
- UI console (`civ-arcos-carbon.html`) is static frontend logic and not yet backed by a fully role-aware, authenticated session model.
- CI/doc automation gates (doc linting, schema/contract enforcement, release automation) are still maturing and should be treated as in-progress.

## Contributing notes

- Keep runtime dependencies minimal and intentional.
- Prefer clear interfaces and modular route registration over monolithic endpoint files.
- Add tests for any new endpoint or contract payload behavior.
- Preserve backward compatibility for legacy `/api/*` routes when adding versioned `/api/v*` contracts.
