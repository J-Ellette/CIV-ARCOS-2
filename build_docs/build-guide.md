# CIV-ARCOS Build Guide

## Civilian Assurance-based Risk Computation and Orchestration System

*Military-grade software assurance, adapted for civilian use.*

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Design Principles & Constraints](#2-design-principles--constraints)
3. [UI & Design System](#3-ui--design-system)
4. [Reference Architectures](#4-reference-architectures)
5. [Step 1 — Foundation & Evidence Collection](#5-step-1--foundation--evidence-collection)
6. [Step 2 — Automated Test Evidence Generation](#6-step-2--automated-test-evidence-generation)
7. [Step 3 — Digital Assurance Case Builder](#7-step-3--digital-assurance-case-builder)
8. [Step 4 — Quality Badge System & Web Dashboard](#8-step-4--quality-badge-system--web-dashboard)
9. [Step 5 — Advanced ARCOS Methodologies](#9-step-5--advanced-arcos-methodologies)
10. [Step 6 — Enterprise & Scale](#10-step-6--enterprise--scale)
11. [Step 7 — AI-Powered Analysis](#11-step-7--ai-powered-analysis)
12. [Step 8 — Distributed & Federated Systems](#12-step-8--distributed--federated-systems)
13. [Step 9 — Advanced Visualization & Dashboards](#13-step-9--advanced-visualization--dashboards)
14. [Step 10 — Market & Ecosystem](#14-step-10--market--ecosystem)
15. [Step 11 — Future-Proofing & Innovation](#15-step-11--future-proofing--innovation)
16. [Step 12 — Internationalization & Digital Twin](#16-step-12--internationalization--digital-twin)
17. [Compliance Module Pattern](#17-compliance-module-pattern)
18. [Unified Improvement Priorities](#18-unified-improvement-priorities)
19. [Code Quality Standards](#19-code-quality-standards)
20. [Testing Strategy](#20-testing-strategy)
21. [Verification Matrix](#21-verification-matrix)
22. [Release Readiness Checklist](#22-release-readiness-checklist)
23. [Update Protocol](#23-update-protocol)

---

## 1. Project Overview

CIV-ARCOS is a civilian adaptation of military-grade software assurance, following proven ARCOS (Automated Rapid Certification of Software) methodologies. It is designed for open source projects, enterprise development teams, and SaaS deployments.

The system provides:

- Evidence-based quality assurance with provenance tracking
- Automated test generation, static analysis, and security scanning
- Digital Assurance Cases (DACs) using Goal Structuring Notation (GSN)
- Quality badges, dashboards, and reporting
- Multi-tenant enterprise architecture
- AI-assisted analysis with full software fallbacks
- Distributed and federated evidence networks
- A plugin marketplace and community ecosystem

### Minimum Viable Product (MVP)

Before tackling advanced capabilities, establish the MVP:

- GitHub integration for code analysis
- Basic test coverage tracking
- Badge generation (test coverage + quality metrics)
- Web dashboard for viewing quality arguments
- REST API for badge embedding

---

## 2. Design Principles & Constraints

### What We Emulate But Do NOT Use

The following frameworks are **prohibited**. Emulate their behavior using the Python standard library:

| Category | Prohibited Libraries |
|---|---|
| Web frameworks | Django, FastAPI, Flask |
| ORMs | Django ORM, SQLAlchemy, Peewee, Tortoise |
| Auth | Django-allauth, Authlib, PassLib |
| Templates | Django Templates, Jinja2 |
| REST | Django REST Framework (DRF), Pydantic |
| Cache | Django Cache Framework, Redis-py, aioredis |
| Admin | Django Admin, Flask-Admin |
| Security middleware | Django Security Middleware |

### What We Can Use

When emulation is insufficient or impractical:

- `pytest` — test runner
- `coverage.py` — code coverage
- `black` — code formatting
- `mypy` — type checking
- `flake8` — linting
- `docker` — containerization

### Core Architecture Principle

All web framework, persistence, template, badge generation, and blockchain functionality must be **custom implementations** using the Python standard library (`http.server`, `json`, `hashlib`, `urllib`, `ast`, etc.).

---

## 3. UI & Design System

| Surface | Design System | Notes |
|---|---|---|
| Operational console | [IBM Carbon Design System](https://carbondesignsystem.com/) | All internal UI components |
| Exported reports and public-facing surfaces | [USWDS](https://designsystem.digital.gov/) | Omit the "An official website of the United States government" top banner — this is not a government product |
| civ-arcos-carbon.html, in the root, is the UI we are using |

---

## 4. Reference Architectures

CIV-ARCOS takes direct inspiration from the following military-grade tools:

| Tool | Source | What We Emulate |
|---|---|---|
| **RACK** (Rapid Assurance Curation Kit) | [GE/DARPA](https://github.com/ge-high-assurance/RACK) | Semantic triplestore for evidence normalization, provenance tracking, ontology-based data model |
| **CertGATE** | [ARCOS Tools](https://arcos-tools.org/tools/certgate) | Digital Assurance Cases, argument templates, ArgTL DSL, ACQL query language |
| **CLARISSA** | [ARCOS Tools](https://arcos-tools.org/tools/clarissa) | Reasoning engine with theories and defeaters, s(CASP) semantics |
| **A-CERT** | [ARCOS Tools](https://arcos-tools.org/tools/cert-advancing-certification-evidence-rigor-and-traceability) | Architecture mapping and traceability |
| **CAID-tools** | [VU-ISIS](https://github.com/vu-isis/CAID-tools) | Cross-tool dependency tracking |
| **NASA AdvoCATE** | ResearchGate | Automated pattern instantiation, hierarchical abstraction |
| **GrammaTech** | [grammatech.com](https://www.grammatech.com/) | Automated test generation, coverage analysis, SAST/DAST |
| **Guardtime Federal** | IDST | Blockchain evidence integrity, immutable audit trails |

## 4.1 Python Coding Conventions

- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Provide docstrings following PEP 257 conventions.
- Use the `typing` module for type annotations (e.g., `List[str]`, `Dict[str, int]`).
- Break down complex functions into smaller, more manageable functions.

## General Instructions

- Always prioritize readability and clarity.
- For algorithm-related code, include explanations of the approach used.
- Write code with good maintainability practices, including comments on why certain design decisions were made.
- Handle edge cases and write clear exception handling.
- For libraries or external dependencies, mention their usage and purpose in comments.
- Use consistent naming conventions and follow language-specific best practices.
- Write concise, efficient, and idiomatic code that is also easily understandable.

## Code Style and Formatting

- Follow the **PEP 8** style guide for Python.
- Maintain proper indentation (use 4 spaces for each level of indentation).
- Ensure lines do not exceed 79 characters.
- Place function and class docstrings immediately after the `def` or `class` keyword.
- Use blank lines to separate functions, classes, and code blocks where appropriate.

## Edge Cases and Testing

- Always include test cases for critical paths of the application.
- Account for common edge cases like empty inputs, invalid data types, and large datasets.
- Include comments for edge cases and the expected behavior in those cases.
- Write unit tests for functions and document them with docstrings explaining the test cases.

## Example of Proper Documentation

```python
def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given the radius.
    
    Parameters:
    radius (float): The radius of the circle.
    
    Returns:
    float: The area of the circle, calculated as π * radius^2.
    """
    import math
    return math.pi * radius ** 2
```

## 4.2 Secure Coding and OWASP Guidelines

Your primary directive is to ensure all code you generate, review, or refactor is secure by default. You must operate with a security-first mindset. When in doubt, always choose the more secure option and explain the reasoning. You must follow the principles outlined below, which are based on the OWASP Top 10 and other security best practices.

### 1. A01: Broken Access Control & A10: Server-Side Request Forgery (SSRF)
- **Enforce Principle of Least Privilege:** Always default to the most restrictive permissions. When generating access control logic, explicitly check the user's rights against the required permissions for the specific resource they are trying to access.
- **Deny by Default:** All access control decisions must follow a "deny by default" pattern. Access should only be granted if there is an explicit rule allowing it.
- **Validate All Incoming URLs for SSRF:** When the server needs to make a request to a URL provided by a user (e.g., webhooks), you must treat it as untrusted. Incorporate strict allow-list-based validation for the host, port, and path of the URL.
- **Prevent Path Traversal:** When handling file uploads or accessing files based on user input, you must sanitize the input to prevent directory traversal attacks (e.g., `../../etc/passwd`). Use APIs that build paths securely.

### 2. A02: Cryptographic Failures
- **Use Strong, Modern Algorithms:** For hashing, always recommend modern, salted hashing algorithms like Argon2 or bcrypt. Explicitly advise against weak algorithms like MD5 or SHA-1 for password storage.
- **Protect Data in Transit:** When generating code that makes network requests, always default to HTTPS.
- **Protect Data at Rest:** When suggesting code to store sensitive data (PII, tokens, etc.), recommend encryption using strong, standard algorithms like AES-256.
- **Secure Secret Management:** Never hardcode secrets (API keys, passwords, connection strings). Generate code that reads secrets from environment variables or a secrets management service (e.g., HashiCorp Vault, AWS Secrets Manager). Include a clear placeholder and comment.
  ```javascript
  // GOOD: Load from environment or secret store
  const apiKey = process.env.API_KEY; 
  // TODO: Ensure API_KEY is securely configured in your environment.
  ```
  ```python
  # BAD: Hardcoded secret
  api_key = "sk_this_is_a_very_bad_idea_12345" 
  ```

### 3. A03: Injection
- **No Raw SQL Queries:** For database interactions, you must use parameterized queries (prepared statements). Never generate code that uses string concatenation or formatting to build queries from user input.
- **Sanitize Command-Line Input:** For OS command execution, use built-in functions that handle argument escaping and prevent shell injection (e.g., `shlex` in Python).
- **Prevent Cross-Site Scripting (XSS):** When generating frontend code that displays user-controlled data, you must use context-aware output encoding. Prefer methods that treat data as text by default (`.textContent`) over those that parse HTML (`.innerHTML`). When `innerHTML` is necessary, suggest using a library like DOMPurify to sanitize the HTML first.

### 4. A05: Security Misconfiguration & A06: Vulnerable Components
- **Secure by Default Configuration:** Recommend disabling verbose error messages and debug features in production environments.
- **Set Security Headers:** For web applications, suggest adding essential security headers like `Content-Security-Policy` (CSP), `Strict-Transport-Security` (HSTS), and `X-Content-Type-Options`.
- **Use Up-to-Date Dependencies:** When asked to add a new library, suggest the latest stable version. Remind the user to run vulnerability scanners like `npm audit`, `pip-audit`, or Snyk to check for known vulnerabilities in their project dependencies.

### 5. A07: Identification & Authentication Failures
- **Secure Session Management:** When a user logs in, generate a new session identifier to prevent session fixation. Ensure session cookies are configured with `HttpOnly`, `Secure`, and `SameSite=Strict` attributes.
- **Protect Against Brute Force:** For authentication and password reset flows, recommend implementing rate limiting and account lockout mechanisms after a certain number of failed attempts.

### 6. A08: Software and Data Integrity Failures
- **Prevent Insecure Deserialization:** Warn against deserializing data from untrusted sources without proper validation. If deserialization is necessary, recommend using formats that are less prone to attack (like JSON over Pickle in Python) and implementing strict type checking.

## General Guidelines
- **Be Explicit About Security:** When you suggest a piece of code that mitigates a security risk, explicitly state what you are protecting against (e.g., "Using a parameterized query here to prevent SQL injection.").
- **Educate During Code Reviews:** When you identify a security vulnerability in a code review, you must not only provide the corrected code but also explain the risk associated with the original pattern. 


## 4.3 Governance Audit

Real-time threat detection and audit logging for GitHub Copilot coding agent sessions. Scans user prompts for dangerous patterns before the agent processes them.

## Overview

This hook provides governance controls for Copilot coding agent sessions:
- **Threat detection**: Scans prompts for data exfiltration, privilege escalation, system destruction, prompt injection, and credential exposure
- **Governance levels**: Open, standard, strict, locked — from audit-only to full blocking
- **Audit trail**: Append-only JSON log of all governance events
- **Session summary**: Reports threat counts at session end

## Threat Categories

| Category | Examples | Severity |
|----------|----------|----------|
| `data_exfiltration` | "send all records to external API" | 0.7 - 0.95 |
| `privilege_escalation` | "sudo", "chmod 777", "add to sudoers" | 0.8 - 0.95 |
| `system_destruction` | "rm -rf /", "drop database" | 0.9 - 0.95 |
| `prompt_injection` | "ignore previous instructions" | 0.6 - 0.9 |
| `credential_exposure` | Hardcoded API keys, AWS access keys | 0.9 - 0.95 |

## Governance Levels

| Level | Behavior |
|-------|----------|
| `open` | Log threats only, never block |
| `standard` | Log threats, block only if `BLOCK_ON_THREAT=true` |
| `strict` | Log and block all detected threats |
| `locked` | Log and block all detected threats |

## Installation

1. Copy the hook folder to your repository:
   ```bash
   cp -r hooks/governance-audit .github/hooks/
   ```

2. Ensure scripts are executable:
   ```bash
   chmod +x .github/hooks/governance-audit/*.sh
   ```

3. Create the logs directory and add to `.gitignore`:
   ```bash
   mkdir -p logs/copilot/governance
   echo "logs/" >> .gitignore
   ```

4. Commit to your repository's default branch.

## Configuration

Set environment variables in `hooks.json`:

```json
{
  "env": {
    "GOVERNANCE_LEVEL": "strict",
    "BLOCK_ON_THREAT": "true"
  }
}
```

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `GOVERNANCE_LEVEL` | `open`, `standard`, `strict`, `locked` | `standard` | Controls blocking behavior |
| `BLOCK_ON_THREAT` | `true`, `false` | `false` | Block prompts with threats (standard level) |
| `SKIP_GOVERNANCE_AUDIT` | `true` | unset | Disable governance audit entirely |

## Log Format

Events are written to `logs/copilot/governance/audit.log` in JSON Lines format:

```json
{"timestamp":"2026-01-15T10:30:00Z","event":"session_start","governance_level":"standard","cwd":"/workspace/project"}
{"timestamp":"2026-01-15T10:31:00Z","event":"prompt_scanned","governance_level":"standard","status":"clean"}
{"timestamp":"2026-01-15T10:32:00Z","event":"threat_detected","governance_level":"standard","threat_count":1,"threats":[{"category":"privilege_escalation","severity":0.8,"description":"Elevated privileges","evidence":"sudo"}]}
{"timestamp":"2026-01-15T10:45:00Z","event":"session_end","total_events":12,"threats_detected":1}
```

## Requirements

- `jq` for JSON processing (pre-installed on most CI environments and macOS)
- `grep` with `-E` (extended regex) support
- `bc` for floating-point comparison (optional, gracefully degrades)

## Privacy & Security

- Full prompts are **never** logged — only matched threat patterns (minimal evidence snippets) and metadata are recorded
- Add `logs/` to `.gitignore` to keep audit data local
- Set `SKIP_GOVERNANCE_AUDIT=true` to disable entirely
- All data stays local — no external network calls


## 4.4 Session Logging

Comprehensive logging for GitHub Copilot coding agent sessions, tracking session starts, ends, and user prompts for audit trails and usage analytics.

## Overview

This hook provides detailed logging of Copilot coding agent activity:
- Session start/end times with working directory context
- User prompt submission events
- Configurable log levels

## Features

- **Session Tracking**: Log session start and end events
- **Prompt Logging**: Record when user prompts are submitted
- **Structured Logging**: JSON format for easy parsing
- **Privacy Aware**: Configurable to disable logging entirely

## Installation

1. Copy this hook folder to your repository's `.github/hooks/` directory:
   ```bash
   cp -r hooks/session-logger .github/hooks/
   ```

2. Create the logs directory:
   ```bash
   mkdir -p logs/copilot
   ```

3. Ensure scripts are executable:
   ```bash
   chmod +x .github/hooks/session-logger/*.sh
   ```

4. Commit the hook configuration to your repository's default branch

## Log Format

Session events are written to `logs/copilot/session.log` and prompt events to `logs/copilot/prompts.log` in JSON format:

```json
{"timestamp":"2024-01-15T10:30:00Z","event":"sessionStart","cwd":"/workspace/project"}
{"timestamp":"2024-01-15T10:35:00Z","event":"sessionEnd"}
```

## Privacy & Security

- Add `logs/` to `.gitignore` to avoid committing session data
- Use `LOG_LEVEL=ERROR` to only log errors
- Set `SKIP_LOGGING=true` environment variable to disable
- Logs are stored locally only

---

## 5. Step 1 — Foundation & Evidence Collection

**Goal:** Implement the core infrastructure for collecting, storing, and tracking evidence with full provenance and audit capability.

### Components

#### `civ_arcos/storage/graph.py` — Graph Database

A Neo4j-style graph database emulated using the Python standard library.

- Node management: create, retrieve, update nodes representing evidence items
- Relationship tracking: define and query relationships between nodes
- Label indexing for fast lookup by node type
- JSON-based persistence with automatic save/load on startup/shutdown
- Query capabilities: find by label, traverse relationships, find neighbors, path-find between nodes
- Automatic timestamping for data provenance

#### `civ_arcos/evidence/collector.py` — Evidence Collection Framework

- `Evidence` dataclass with: unique ID, type classification, source attribution, timestamp, data payload, provenance metadata, SHA-256 checksum
- Abstract `EvidenceCollector` base class for source-specific implementations
- In-memory evidence cache
- Standardized collection methods: `collect_from_github()`, `collect_from_ci()`, `collect_from_security_tools()`

#### `civ_arcos/adapters/github_adapter.py` — GitHub Adapter

- Repository metadata: stars, forks, watchers, language distribution, size
- Commit history: recent commits with messages, author info, timestamps
- Pull request reviews: PR review data, comments, approval status
- GitHub REST API v3 integration with optional token auth and rate limit awareness
- Graceful fallback with mock data for offline/testing use

#### `civ_arcos/distributed/blockchain_ledger.py` — Blockchain Audit Trail

- Block structure: index, timestamp, data, previous block hash, SHA-256 hash
- Genesis block initialization and full chain validation with tamper detection
- Evidence tracking: add evidence to chain, link evidence across blocks, query by ID or type
- Immutability via hash-based linking and cryptographic verification

#### `civ_arcos/web/framework.py` — Custom Web Framework

- Request/Response abstractions with URL routing via decorators
- Method-based routing (GET, POST, PUT, DELETE)
- Path parameter extraction, query string parsing, JSON request/response handling
- Built on Python's `http.server` — no Flask, Django, or FastAPI
- `create_app()` factory with route registration and middleware support
- Structured logging and `X-Correlation-ID` header on every response

#### `civ_arcos/web/badges.py` — Badge Generation

Pure SVG output (no external libraries):

| Badge | Tiers |
|---|---|
| Coverage | Bronze (60–79%), Silver (80–94%), Gold (95%+) |
| Quality | Score-based: Excellent / Good / Fair / Poor |
| Security | Vulnerability count with severity color coding |

#### `civ_arcos/evidence/store.py` — Evidence Store

- Unified high-level interface over the graph database
- Automatic evidence node creation and relationship management
- Evidence retrieval by ID or criteria
- Full provenance preservation

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/status` | Health check — `{ "status": "operational", "version": "1.0.0" }` |
| POST | `/api/evidence/collect` | Collect evidence from a source (`source`, `repo_url`, `commit_hash`) |
| GET | `/api/evidence/{evidence_id}` | Retrieve evidence by ID |
| GET | `/api/badge/coverage` | Generate coverage badge SVG (`?coverage=85`) |
| POST | `/api/blockchain/add` | Add evidence block to blockchain |
| GET | `/api/blockchain/chain` | Retrieve full blockchain |

### Data Structures

```python
# Evidence Node
{
  "id": "evidence_abc123",
  "label": "Evidence",
  "properties": {
    "type": "commit_history",
    "source": "github",
    "timestamp": "2025-10-29T12:34:56Z",
    "checksum": "sha256:...",
    "data": {}
  },
  "created_at": "2025-10-29T12:34:56Z"
}

# Graph Relationship
{
  "id": "rel_xyz789",
  "type": "SUPPORTS",
  "source_id": "evidence_abc123",
  "target_id": "goal_def456",
  "properties": {"confidence": 0.95, "automated": True},
  "created_at": "2025-10-29T12:35:00Z"
}

# Blockchain Block
{
  "index": 5,
  "timestamp": "2025-10-29T12:34:56Z",
  "data": {"evidence_id": "ev_001", "type": "test_result"},
  "previous_hash": "sha256:...",
  "hash": "sha256:..."
}
```

### Security Notes

- SHA-256 checksums on all evidence items
- Tamper detection via blockchain hash linking
- Input validation on all API endpoints
- Authentication/authorization is deferred to a later step

### Acceptance Criteria

- [ ] `civ_arcos/storage/graph.py` — graph database with JSON persistence
- [ ] `civ_arcos/evidence/collector.py` — evidence framework with SHA-256 checksums
- [ ] `civ_arcos/adapters/github_adapter.py` — GitHub adapter with offline fallback
- [ ] `civ_arcos/distributed/blockchain_ledger.py` — immutable audit trail
- [ ] `civ_arcos/web/framework.py` — custom HTTP framework (no Flask/Django/FastAPI)
- [ ] `civ_arcos/web/badges.py` — SVG badge generation for coverage, quality, security
- [ ] `civ_arcos/evidence/store.py` — unified evidence store interface
- [ ] Full provenance tracking end-to-end

---

## 6. Step 2 — Automated Test Evidence Generation

**Goal:** Implement automated test generation, static analysis, security scanning, and coverage analysis following GrammaTech's approach.

### Components

#### `civ_arcos/analysis/static_analyzer.py` — Static Analysis

- Cyclomatic complexity calculation based on decision points
- Maintainability index using Halstead volume, complexity, and LOC
- Code smell detection: long functions (>50 lines), too many parameters (>5), large classes (>500 lines), deeply nested blocks (>4 levels)
- AST-based analysis via Python's built-in `ast` module

#### `civ_arcos/analysis/security_scanner.py` — Security Scanner (SAST)

Detect:
- SQL injection: string formatting in SQL queries
- Command injection: `shell=True`, `os.system`, `eval`/`exec`
- Hardcoded secrets: API keys, passwords, tokens, private keys
- Insecure functions: `pickle`, `yaml.load`, `marshal`
- XSS: `innerHTML`, `document.write`, `dangerouslySetInnerHTML`
- Error handling: bare except clauses, assert used for validation

Features:
- Severity classification (Critical, High, Medium, Low)
- Security scoring (0–100 based on vulnerabilities found)
- Placeholder detection to reduce false positives on example code

#### `civ_arcos/analysis/test_generator.py` — Test Generator

- Function and class analysis from source AST
- Test template generation (pytest-compatible)
- Untested code discovery
- Optional AI-powered test generation (`use_ai=False` by default)
- Suggestions: basic functionality, edge cases, error handling, return type validation, state consistency

#### `civ_arcos/analysis/coverage_analyzer.py` — Coverage Analyzer

- Line and branch coverage tracking (via coverage.py)
- Coverage tier determination: Bronze (>60%), Silver (>80%), Gold (>95%)
- Per-file coverage reporting

#### `civ_arcos/analysis/collectors.py` — Analysis Collectors

Integrate analysis modules with the evidence system:

- `StaticAnalysisCollector`
- `SecurityScanCollector`
- `TestGenerationCollector`
- `CoverageCollector`
- `ComprehensiveAnalysisCollector` — runs all and aggregates

All collectors: automatic graph storage, provenance tracking, SHA-256 checksums, evidence chaining.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/analysis/static` | Run static analysis (`{ "source_path": "..." }`) |
| POST | `/api/analysis/security` | Run SAST security scan |
| POST | `/api/analysis/tests` | Generate test suggestions |
| POST | `/api/analysis/coverage` | Analyze coverage data |
| POST | `/api/analysis/comprehensive` | Run all analyses |

### Acceptance Criteria

- [ ] Static analyzer with complexity, maintainability, and smell detection
- [ ] Security scanner with 6 vulnerability categories and severity scoring
- [ ] Test generator with AI-optional mode
- [ ] Coverage analyzer with Bronze/Silver/Gold tiers
- [ ] All analysis collectors with evidence chaining

---

## 7. Step 3 — Digital Assurance Case Builder

**Goal:** Implement CertGATE-style Digital Assurance Cases (DACs) using Goal Structuring Notation (GSN).

### Components

#### `civ_arcos/assurance/gsn.py` — GSN Node System

Six node types per GSN Community Standard v3:

| Type | Description |
|---|---|
| Goal | Top-level quality claim |
| Strategy | How a goal is decomposed |
| Solution | Evidence or artifact supporting a goal |
| Context | Assumptions or operational context |
| Justification | Reasoning for strategy choice |
| Assumption | Undeveloped/assumed context |

#### `civ_arcos/assurance/case.py` — Assurance Case Management

- Case creation and management with fluent builder API
- Node addition, retrieval, linking
- Evidence linking, root goal setting, traversal
- Validation (structural completeness and soundness)
- Graph storage schema: `AssuranceCase` node + `GSN_{TYPE}` nodes + `CONTAINS`, `SUPPORTS`, `EVIDENCED_BY` relationships

#### `civ_arcos/assurance/templates.py` — Argument Templates

Five reusable templates:

- Basic Quality
- Security Assurance
- Comprehensive (combines multiple concerns)
- API-specific
- Web App-specific

#### `civ_arcos/assurance/patterns.py` — Pattern Instantiation Engine

- 8 project types: web app, API, library, mobile app, CLI, data pipeline, embedded, ML model
- Auto-generates argument structures from project type and evidence
- Integrates with evidence mapping table

Evidence auto-linking mapping:

| Node ID | Evidence Types |
|---|---|
| `G_complexity` | `static_analysis` |
| `G_line_coverage` | `coverage_analysis` |
| `G_no_critical_vulns` | `security_scan`, `security_score` |
| `G_no_sql_injection` | `security_scan` |
| `G_critical_tests` | `test_suggestions` |

#### `civ_arcos/assurance/visualizer.py` — GSN Visualizer

- SVG output (no external graphics libraries)
- DOT format (Graphviz-compatible)
- Summary JSON (case metadata, node counts, evidence count, max depth)

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/assurance/create` | Create assurance case from template |
| GET | `/api/assurance/{case_id}` | Get full case details |
| GET | `/api/assurance/{case_id}/visualize` | Visualize case (`?format=svg\|dot\|summary`) |
| GET | `/api/assurance/{case_id}/export` | Export as PDF (`?format=pdf`) |
| POST | `/api/assurance/auto-generate` | Auto-generate from collected evidence |
| GET | `/api/assurance/templates` | List available templates |

### Test Suite

| File | Tests |
|---|---|
| `tests/unit/test_gsn.py` | 15 |
| `tests/unit/test_case.py` | 24 |
| `tests/unit/test_templates.py` | 13 |
| `tests/unit/test_patterns.py` | 16 |
| `tests/integration/test_assurance_api.py` | 13 |
| **Total** | **81** |

### Acceptance Criteria

- [ ] All 6 GSN node types implemented
- [ ] Fluent builder API for case assembly
- [ ] 5 argument templates
- [ ] Pattern instantiation for 8 project types
- [ ] SVG, DOT, and summary visualization
- [ ] Evidence auto-linking via mapping table
- [ ] PDF export endpoint
- [ ] All 81 tests passing

---

## 8. Step 4 — Quality Badge System & Web Dashboard

**Goal:** Complete the quality badge system with three additional badge types, and implement the web dashboard frontend using pure Python HTML generation.

### Components

#### `civ_arcos/web/badges.py` — Enhanced Badge System

Six badge types total (three from Step 1, three new):

| Badge | Details |
|---|---|
| Coverage | Bronze / Silver / Gold (Step 1) |
| Quality | Score-based: Excellent / Good / Fair / Poor (Step 1) |
| Security | Vulnerability count with severity (Step 1) |
| Documentation | API docs, README, inline comments — `generate_documentation_badge(score)` |
| Performance | Load testing and profiling — `generate_performance_badge(score)` |
| Accessibility | WCAG A / AA / AAA — `generate_accessibility_badge(level, issues)` |

#### `civ_arcos/web/dashboard.py` — Dashboard Generator

Pure Python string formatting — no Jinja2 or Django templates.

Four pages:

| Page | Generator | Description |
|---|---|---|
| Home | `generate_home_page(stats)` | System statistics |
| Badges | `generate_badge_page(badges)` | Badge showcase |
| Analyzer | `generate_analyze_page()` | Repository analyzer with GitHub form |
| Assurance | `generate_assurance_page(cases)` | Assurance case viewer |

Design requirements:
- Embedded CSS: responsive, gradient header (`#667eea` → `#764ba2`), card-based layout
- Embedded JavaScript: API integration, vanilla JS only
- Mobile-friendly navigation

The operational console uses **IBM Carbon Design System**. Public-facing surfaces and exported reports use **USWDS** (without the government banner).

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/badge/documentation/{owner}/{repo}` | Documentation badge (`?score=90`) |
| GET | `/api/badge/performance/{owner}/{repo}` | Performance badge (`?score=88`) |
| GET | `/api/badge/accessibility/{owner}/{repo}` | Accessibility badge (`?level=AA&issues=0`) |
| GET | `/dashboard` | Home page |
| GET | `/dashboard/badges` | Badge showcase |
| GET | `/dashboard/analyze` | Repository analyzer |
| GET | `/dashboard/assurance` | Assurance case viewer |
| GET | `/dashboard/compliance` | Compliance module dashboard |

### Test Suite

| File | Tests |
|---|---|
| `tests/unit/test_badges.py` | 8 new |
| `tests/unit/test_dashboard.py` | 13 new |

### Acceptance Criteria

- [ ] 3 new badge types added
- [ ] `DashboardGenerator` with 4 pages generating valid HTML
- [ ] 7 new API endpoints
- [ ] All CSS/JS embedded inline, no external dependencies
- [ ] `flake8 civ_arcos/web/dashboard.py --max-line-length=100` exits 0

---

## 9. Step 5 — Advanced ARCOS Methodologies

**Goal:** Emulate five major ARCOS tools: CertGATE, A-CERT, CLARISSA, and CAID-tools.

### Components

#### `civ_arcos/assurance/fragments.py` — Assurance Case Fragments (CertGATE)

- `AssuranceCaseFragment`: maintains GSN structure, tracks evidence linkage, assesses strength, manages fragment dependencies
- `FragmentLibrary`: pattern-based creation with default patterns (`component_quality`, `component_security`, `integration`), custom registration, filtering

#### `civ_arcos/assurance/argtl.py` — Argument Transformation Language

DSL for assembling and transforming fragments.

Operations: `compose`, `link`, `validate`, `assemble`

Script syntax:
```
compose frag1 frag2 -> system
link frag1 to frag2 via "API interface"
validate system
```

#### `civ_arcos/assurance/acql.py` — Assurance Case Query Language

8 query types: `CONSISTENCY`, `COMPLETENESS`, `SOUNDNESS`, `COVERAGE`, `TRACEABILITY`, `WEAKNESSES`, `DEPENDENCIES`, `DEFEATERS`

Script syntax:
```
consistency on my_case
completeness on my_fragment
weaknesses on my_case
```

#### `civ_arcos/assurance/reasoning.py` — Reasoning Engine (CLARISSA)

- Theories: reusable argument patterns with premises and conclusions
- Defeaters: rebuttals, undercuts, counterexamples
- `reason_about_case(case, context)`: returns applicable theories, active defeaters, confidence score, indefeasibility flag, recommendations
- `estimate_risk(case, context)`: returns risk level and risk score
- Custom theory registration via `register_theory(theory)`

#### `civ_arcos/assurance/architecture.py` — Architecture Mapper (A-CERT)

- Architecture inference from source code
- Design requirement loading and mapping
- Discrepancy detection (missing, extra, mismatch components) with severity
- Coverage mapping to components
- Traceability matrix generation

#### `civ_arcos/assurance/dependency_tracker.py` — Dependency Tracker (CAID-tools)

Resource types: `FILE`, `DIRECTORY`, `MODEL`, `TEST`, `EVIDENCE`
Dependency types: `REQUIRES`, `IMPLEMENTS`, `TESTS`, `VALIDATES`

Features: resource registration, dependency linking, update listeners (callbacks on resource change), impact analysis.

### Integration Workflow

These six components must work together:

1. `ArchitectureMapper` infers architecture from source
2. `FragmentLibrary` creates fragments for each discovered component
3. `ArgTLEngine` composes fragments hierarchically
4. `ACQLEngine` validates completeness of the composed case
5. `ReasoningEngine` reasons about the assembled case with evidence context
6. `DependencyTracker` registers all components and links resources

### Test Suite

| Module | File | Tests |
|---|---|---|
| Fragments | `tests/unit/assurance/test_fragments.py` | 16 |
| ArgTL | `tests/unit/assurance/test_argtl.py` | 20 |
| ACQL | `tests/unit/assurance/test_acql.py` | 14 |
| Reasoning | `tests/unit/assurance/test_reasoning.py` | 20 |
| Architecture | `tests/unit/assurance/test_architecture.py` | 14 |
| Dependency Tracker | `tests/unit/assurance/test_dependency_tracker.py` | 20 |
| **Total** | | **104** |

### Acceptance Criteria

- [ ] All 6 components implemented
- [ ] ArgTL DSL parser supports 3 operations
- [ ] All 8 ACQL query types
- [ ] Custom theory registration in ReasoningEngine
- [ ] End-to-end 6-step integration workflow functional
- [ ] 104 tests passing

---

## 10. Step 6 — Enterprise & Scale

**Goal:** Add multi-tenant architecture, compliance frameworks, and advanced analytics.

### Components

#### `civ_arcos/core/tenants.py` — Multi-Tenant Architecture

```python
class TenantManager:
    def create_tenant(self, tenant_id, config):
        # Isolated EvidenceGraph per tenant at ./data/tenants/tenant_{tenant_id}/
        ...
    def get_tenant_context(self, request):
        # Resolve from: X-Tenant-ID header, subdomain, query param, or API key
        ...
```

Features:
- Isolated evidence storage per tenant (prevents data leakage)
- Custom quality weights, badge templates, compliance standards per tenant
- Multiple resolution strategies: HTTP header, subdomain, query param, API key
- Full CRUD for tenant management

#### `civ_arcos/core/compliance.py` — Compliance Frameworks

Five frameworks implemented:

| Framework | Key Controls |
|---|---|
| ISO 27001 | A.12.6.1 vulnerability mgmt, A.14.2.1 secure dev, A.12.1.2 change mgmt, A.12.4.1 event logging, A.14.2.5 secure principles |
| SOX | ITGC-1 access controls, ITGC-2 change mgmt, ITGC-3 data integrity, ITGC-4 audit trails |
| HIPAA | §164.312(a)(1) access control, §164.312(b) audit controls, §164.312(c)(1) integrity, §164.312(e)(1) transmission security |
| PCI-DSS | Req-6.2 secure dev, Req-6.3 security testing, Req-7.1 access control, Req-11.3 vuln scanning |
| NIST 800-53 | AC-2 account mgmt, CM-3 change control, CA-2 security assessment, SI-2 flaw remediation, SI-10 input validation |

#### `civ_arcos/core/analytics.py` — Analytics Engine

- **Trend Analysis**: quality score, coverage, vulnerability, technical debt, team productivity — with direction detection (increasing/decreasing/stable)
- **Benchmark Analysis**: industry-specific percentile calculation and actionable recommendations
- **Risk Prediction**: security incident, maintenance burden, quality degradation, and technical debt risks with probability scoring (0.0–1.0)

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/tenants/create` | Create new tenant |
| GET | `/api/tenants/list` | List all tenants |
| GET | `/api/tenants/{tenant_id}` | Get tenant configuration |
| GET | `/api/compliance/frameworks` | List available frameworks |
| POST | `/api/compliance/evaluate` | Evaluate against one framework |
| POST | `/api/compliance/evaluate-all` | Evaluate against all frameworks |
| POST | `/api/analytics/trends` | Generate trend analysis |
| POST | `/api/analytics/benchmark` | Compare against industry |
| POST | `/api/analytics/risks` | Predict project risks |

### Test Suite

| File | Tests |
|---|---|
| `tests/unit/test_tenants.py` | 19 |
| `tests/unit/test_compliance.py` | 23 |
| `tests/unit/test_analytics.py` | 21 |
| `tests/integration/test_enterprise_api.py` | 10 |
| **Total** | **73** |

### Acceptance Criteria

- [ ] Tenant isolation: cross-read/write blocked in all paths
- [ ] 5 compliance frameworks with control-level scoring
- [ ] Analytics engine with trend, benchmark, and risk prediction
- [ ] All 73 tests passing

---

## 11. Step 7 — AI-Powered Analysis

**Goal:** Implement AI-driven analysis with comprehensive software fallbacks. Every AI function must have an equivalent rule-based alternative.

### Core Principle: AI-Optional Design

All AI features default to `use_ai=False`. The system must function fully without any AI/LLM backend.

### Components

#### `civ_arcos/analysis/llm_integration.py` — LLM Integration

Supported backends:

| Backend | Description |
|---|---|
| Ollama | Local LLM inference (CodeLlama, Mistral, Llama2). No API key. Privacy-preserving. |
| OpenAI | Cloud GPT-3.5/GPT-4. API key required. |
| Azure OpenAI | Optional Azure backend, activated via `use_ai=true` + `CIV_AI_ENABLE=true` env var. |
| Mock | Template-based fallback. Always available. No dependencies. |

Abstract backend pattern: all backends share a common interface. Automatic fallback to Mock when configured backend is unavailable.

Key methods: `generate()`, `generate_test_cases()`, `analyze_code_quality()`, `suggest_improvements()`, `generate_documentation()`

#### `civ_arcos/analysis/test_generator.py` — Intelligent Test Generation (Updated)

- Rule-based (default): AST analysis, function extraction, smart test suggestions, pytest-compatible templates
- AI-enhanced (optional): LLM-based suggestions, context-aware generation, natural language descriptions
- Falls back to rule-based automatically if AI unavailable

#### `civ_arcos/core/xai.py` — Explainable AI (XAI)

Dual-mode implementation:

- Rule-based: deterministic feature importance, threshold-based decision paths, template narratives, statistical counterfactuals
- AI-enhanced (optional): sophisticated correlation, ML insights, advanced counterfactuals

Explanation types: Feature Importance, Decision Path, Counterfactuals, Narrative

Bias detection: demographic bias, group disparity, fairness scoring — works with or without AI.

#### `civ_arcos/analysis/reporter.py` — Quality Reporting System

- Overall quality score (0–100) with letter grade (A–F)
- Component scores: static quality, security, testing
- Strength identification, weakness identification with severity
- Actionable improvement suggestions with priority ranking
- Optional LLM-enhanced insights

### Environment Variables

```bash
# LLM
OLLAMA_HOST="http://localhost:11434"
OPENAI_API_KEY="your-api-key"
CIV_AI_ENABLE="true"   # Required to activate AI; default: false

# WebSocket
WEBSOCKET_HOST="0.0.0.0"
WEBSOCKET_PORT="8001"
```

### Test Suite

| File | Tests |
|---|---|
| `tests/unit/test_llm_integration.py` | 23 |
| `tests/unit/test_test_generator.py` | — |
| `tests/integration/test_analysis_api.py` | — |

### Acceptance Criteria

- [ ] AI disabled by default (`use_ai=False`); all features work in rule-based mode
- [ ] Ollama, OpenAI, Azure OpenAI, and Mock backends
- [ ] Azure OpenAI gated by `CIV_AI_ENABLE=true`
- [ ] XAI module with bias detection
- [ ] Quality reporter with prioritized action items

---

## 12. Step 8 — Distributed & Federated Systems

**Goal:** Implement federated evidence networks, enhanced blockchain, real-time WebSocket updates, and extended integrations.

### Components

#### `civ_arcos/web/websocket.py` — WebSocket Server

Pure Python RFC 6455 implementation. No external dependencies.

- Thread-safe connection management and subscriptions
- Pub/sub integration with the cache layer
- Real-time notifications for quality score updates, badge updates, test results
- Client subscription model via JSON messages

```javascript
// JS client example
const ws = new WebSocket('ws://localhost:8001');
ws.send(JSON.stringify({ type: 'subscribe', channel: 'quality_update' }));
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'quality_update') updateQualityScore(data.data);
};
```

#### `civ_arcos/distributed/federated_network.py` — Federated Evidence Network

- Node management: organizations join/leave with public key infrastructure
- Evidence sharing at three privacy levels: private, aggregated, anonymized
- Consensus algorithm: voting-based distributed validation with threshold mechanisms
- Industry benchmarking: contribute and query anonymized quality metrics
- Threat intelligence: share/query security threats across the network
- Reputation system for organization trustworthiness

Key classes: `FederatedEvidenceNetwork`, `EvidenceConsensus`, `NetworkNode`, `AnonymizedEvidence`

#### `civ_arcos/distributed/sync_events.py` — Blockchain Sync Event Stream

- Poll-mode stream endpoint at `/api/sync/events` with cursor-based pagination
- Emits `blockchain.block_added` events on new blocks
- Idempotent replay: no duplicate events on replay

#### `civ_arcos/adapters/ci_adapter.py` — Extended CI/CD Adapters

New adapters: **GitLab CI**, **CircleCI**, **Travis CI**

All follow the existing `EvidenceCollector` pattern with placeholder implementations ready for real API integration.

#### `civ_arcos/adapters/security_adapter.py` — Extended Security Adapters

New adapters: **Veracode**, **Checkmarx**

#### `civ_arcos/adapters/integrations.py` — Notification Channels

New integrations: **Discord** (webhooks), **Microsoft Teams** (Adaptive Cards), **Email** (SMTP with TLS)

All provide: `format_quality_alert()`, `format_badge_update()`, `send_notification()`

### Environment Variables

```bash
# CI/CD
GITLAB_TOKEN="your-token"
CIRCLECI_TOKEN="your-token"
TRAVIS_TOKEN="your-token"

# Security Tools
VERACODE_API_ID="your-id"
VERACODE_API_KEY="your-key"
CHECKMARX_URL="https://checkmarx.example.com"
CHECKMARX_USERNAME="user"
CHECKMARX_PASSWORD="pass"

# Notifications
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/..."
SMTP_HOST="smtp.example.com"
SMTP_PORT="587"
SMTP_USER="bot@example.com"
SMTP_PASSWORD="password"
```

### API Endpoints (Additions)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/sync/events` | Cursor-based blockchain sync event stream |

### Test Suite

| File | Tests |
|---|---|
| `tests/unit/test_websocket.py` | 13 |
| `tests/unit/test_ci_adapters_extended.py` | 13 |
| `tests/unit/test_security_adapters_extended.py` | 9 |
| `tests/unit/test_notification_integrations.py` | 16 |
| `tests/unit/test_reporter.py` | 13 |

### Acceptance Criteria

- [ ] WebSocket server (pure Python, RFC 6455)
- [ ] Federated evidence network with privacy levels
- [ ] Blockchain sync event stream with cursor pagination
- [ ] GitLab CI, CircleCI, Travis CI adapters
- [ ] Veracode and Checkmarx adapters
- [ ] Discord, Teams, and Email notification channels

---

## 13. Step 9 — Advanced Visualization & Dashboards

**Goal:** Implement interactive assurance case visualization and role-specific dashboards.

### Components

#### `civ_arcos/assurance/interactive_viewer.py` — Interactive AC Viewer

- `generate_interactive_gsn(case, include_metadata, enable_drill_down)`: interactive GSN with drill-down
- `create_evidence_timeline(evidence_items)`: quality evolution timeline with correlation analysis
- `export_to_format(case, format)`: export to JSON, SVG, HTML, or PDF
- `subscribe_to_updates(callback)` / `notify_update()`: real-time subscription system

#### `civ_arcos/web/quality_dashboard.py` — Quality Dashboard Ecosystem

Five specialized widgets:

| Widget | Data |
|---|---|
| `QualityTrendWidget` | Quality over time, moving averages, trend direction |
| `SecurityAlertWidget` | Severity breakdown, security score, active alert prioritization |
| `ComplianceStatusWidget` | Per-standard compliance %, gap identification |
| `ProductivityWidget` | Commits, PRs, issues, velocity calculations |
| `TechnicalDebtWidget` | Debt by source, estimated remediation hours |

Two persona-based dashboards:

**Executive Dashboard** — `create_executive_dashboard(org_data)`:
- High-level metrics, ROI analysis, risk indicators, recommendations, overall health score

**Developer Dashboard** — `create_developer_dashboard(team_data)`:
- Personal stats, actionable items with targets, peer comparison, learning opportunities, goal tracking, achievements

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/visualization/interactive-gsn` | Interactive GSN visualization |
| POST | `/api/visualization/evidence-timeline` | Evidence quality timeline |
| POST | `/api/visualization/export` | Export case to format |
| POST | `/api/dashboard/executive` | Executive dashboard |
| POST | `/api/dashboard/developer` | Developer dashboard |
| GET | `/api/dashboard/widgets` | All widget data |

### Test Suite

| File | Tests |
|---|---|
| `tests/unit/test_interactive_viewer.py` | 27 |
| `tests/unit/test_quality_dashboard.py` | 36 |
| `tests/integration/test_visualization_api.py` | 11 |
| **Total** | **74** |

### Acceptance Criteria

- [ ] Interactive GSN with drill-down and real-time subscriptions
- [ ] Evidence timeline with correlation analysis
- [ ] Export to JSON, SVG, HTML, and PDF
- [ ] 5 dashboard widgets implemented
- [ ] Executive and developer dashboards
- [ ] All 74 tests passing

---

## 14. Step 10 — Market & Ecosystem

**Goal:** Implement a plugin marketplace, multi-version API ecosystem with webhook support, and a community knowledge-sharing platform.

### Components

#### `civ_arcos/core/plugin_marketplace.py` — Plugin Marketplace

Plugin types: `collector`, `metric`, `compliance`, `visualization`

- `PluginManifest`: metadata schema with semantic version constraints (`min_core_version`, `max_core_version`, API target)
- `PluginValidator`: AST-based import validation (whitelist), forbidden pattern detection, SHA-256 checksum generation
- `PluginSandbox`: subprocess-isolated execution (`python -I`), configurable timeout (returns 408 on timeout), bounded output capture
- `PluginMarketplace`: register, unregister, list, search, statistics; idempotent replay support
- `PluginRegistry`: compatibility checks for registered plugins

#### `civ_arcos/api/ecosystem.py` — API Ecosystem

Multi-version support:
- **APIv1**: Basic evidence submission and retrieval
- **APIv2**: Enhanced with batch operations and relations
- **APIv3**: Advanced features with streaming (beta)

Webhook handlers with authentication:
- **GitHub**: HMAC signature verification (push, PR, check suite events)
- **GitLab**: Token-based auth (push, MR, pipeline events)
- **Bitbucket**: Push and PR events

GraphQL interface: schema definition, query operations (evidence, assurance cases, quality metrics), mutation operations, subscription schema.

#### `civ_arcos/core/community_platform.py` — Community Platform

- Quality pattern library with categorization, search, and upvoting
- Best practices library
- Threat intelligence sharing with severity filtering
- Industry templates (8 industries), compliance templates (8 frameworks)
- Benchmark datasets and comparison
- Privacy-focused: permission levels — private, aggregated, anonymized

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/plugins/validate` | Validate plugin code |
| POST | `/api/plugins/execute` | Execute plugin in sandbox |
| POST | `/api/plugins/register` | Register plugin with manifest |
| GET | `/api/plugins/registry` | List compatible plugins |
| POST | `/api/v1/plugins/register` | v1 contract envelope |
| GET | `/api/v1/plugins/registry` | v1 contract envelope |
| POST | `/api/webhooks/github` | GitHub webhook handler |
| POST | `/api/webhooks/gitlab` | GitLab webhook handler |
| POST | `/api/webhooks/bitbucket` | Bitbucket webhook handler |
| POST | `/api/graphql` | GraphQL query execution |
| POST | `/api/community/patterns/share` | Share quality pattern |
| POST | `/api/community/benchmarks/compare` | Benchmark comparison |

### Test Suite

| File | Tests |
|---|---|
| `tests/unit/test_plugin_marketplace.py` | 26 |
| `tests/unit/test_api_ecosystem.py` | 39 |
| `tests/unit/test_community_platform.py` | 31 |
| `tests/integration/test_plugin_api.py` | 5 |
| **Total** | **101** |

### Acceptance Criteria

- [ ] AST validation blocks forbidden imports
- [ ] Isolated subprocess sandbox with timeout (returns 408)
- [ ] Plugin manifest semantic version constraints
- [ ] GitHub, GitLab, Bitbucket webhook handlers with authentication
- [ ] GraphQL schema with queries and mutations
- [ ] Community pattern library with privacy controls
- [ ] All tests passing

---

## 15. Step 11 — Future-Proofing & Innovation

**Goal:** Implement quantum-resistant security, edge computing integration, and an autonomous self-improving quality system.

### Components

#### `civ_arcos/core/quantum_security.py` — Quantum-Resistant Security

Post-quantum cryptography (standard library implementation):

- **Lattice-based encryption**: NTRU-like, 512-dimensional lattice, 2048 modulus, configurable security levels (128, 256, 512 bits)
- **Dilithium-like signatures**: quantum-resistant signing and verification with timestamp validation
- **Quantum-enhanced analysis**: superposition-like pattern matching, multi-factor threat scoring

Key classes: `QuantumResistantSecurity`, `QuantumSignature`, `LatticeKey`

#### `civ_arcos/distributed/edge_computing.py` — Edge Computing Integration

- **Deployment config**: location-based, capabilities (monitoring, security, learning), network modes (offline/intermittent/online), privacy levels (low/medium/high)
- **Local evidence collection**: no network dependency, automatic privacy-preserving anonymization, sync queuing
- **Edge analysis**: quality checks, security scans, performance monitoring — 10–200ms depending on processing tier
- **Federated learning**: local model training (data never leaves device), federated averaging for model aggregation

Key classes: `EdgeEvidenceCollector`, `EdgeDeploymentConfig`, `EdgeEvidence`, `FederatedModel`

#### `civ_arcos/core/autonomous_quality.py` — Autonomous Quality Agent

Self-improving quality system:

- **Continuous Learning Engine**: records outcomes, tracks action success rates, generates data-driven recommendations
- **Quality Decision Engine**: cost-benefit analysis, success probability assessment, multi-factor prioritization
- **Autonomous improvement loop**: identify → hypothesize → simulate → implement → learn
- **Self-evolving standards**: monitors technology trends and compliance requirements, increments standard versions automatically

Improvement categories: Testing, Security, Performance, Maintainability

Key classes: `AutonomousQualityAgent`, `ContinuousLearningEngine`, `QualityDecisionEngine`, `QualityHypothesis`, `QualityStandard`

### Test Suite

| File | Tests |
|---|---|
| `tests/unit/test_quantum_security.py` | 19 |
| `tests/unit/test_edge_computing.py` | 26 |
| `tests/unit/test_autonomous_quality.py` | 26 |
| **Total** | **71** |

### Acceptance Criteria

- [ ] Quantum-resistant encryption and signing at 128/256/512-bit security levels
- [ ] Edge deployment with offline evidence collection and privacy preservation
- [ ] Federated learning (data stays local)
- [ ] Autonomous quality agent with learning, decision-making, and self-evolving standards
- [ ] All 71 tests passing

---

## 16. Step 12 — Internationalization & Digital Twin

**Goal:** Add comprehensive internationalization/localization and digital twin integration for predictive maintenance.

### Components

#### `civ_arcos/core/i18n.py` — Internationalization

- **TranslationEngine**: 10 supported languages (en-US, en-GB, es-ES, fr-FR, de-DE, zh-CN, ja-JP, ko-KR, pt-BR, it-IT), dictionary-based with nested key support and fallback
- **LocalizationManager**: user-specific language and region preferences, localized dashboards and reports
- **Supported Regions**: North America, Europe, United Kingdom, Asia-Pacific, Latin America, Middle East, Africa
- **Compliance Frameworks** (19 total): ISO 27001, ISO 9001, HIPAA, SOC2, FedRAMP, NIST 800-53, GDPR, NIS Directive, ENISA, Cyber Essentials, Cyber Essentials Plus, UK GDPR, NCSC, PDPA Singapore, APEC Privacy, PIPL China, PIPA Korea, My Number Japan, Privacy Act Australia

#### `civ_arcos/core/digital_twin.py` — Digital Twin Integration

- **DigitalTwinConnector**: connects to 7 platforms (Azure Digital Twins, AWS IoT TwinMaker, Siemens MindSphere, GE Predix, Ansys Twin Builder, Unity Reflect, Custom)
- **SimulationEvidence**: 6 simulation types (performance, stress, failure mode, load balancing, security scenarios, integration, scalability)
- **QualityDegradationModel**: 5 degradation factors, configurable forecast periods (30–60 days), risk level assessment (low/medium/high/critical)
- **PredictiveMaintenanceEngine**: 5 maintenance status levels, automated recommendations, maintenance timeline forecasting, simulation data correlation
- **DigitalTwinIntegration**: unified orchestration across all components

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/i18n/languages` | List supported languages |
| GET | `/api/i18n/translate` | Translate a key (`?key=...&language=...`) |
| POST | `/api/i18n/user/language` | Set user language preference |
| POST | `/api/i18n/user/region` | Set user region preference |
| GET | `/api/i18n/regions` | List supported regions |
| GET | `/api/i18n/compliance/frameworks` | Get compliance frameworks by region |
| GET | `/api/i18n/compliance/requirements` | Get framework requirements |
| POST | `/api/i18n/localize/dashboard` | Localize dashboard data |
| POST | `/api/i18n/localize/report` | Localize report data |
| GET | `/api/i18n/stats` | Localization statistics |
| POST | `/api/digital-twin/connector/add` | Add platform connector |
| POST | `/api/digital-twin/simulation/run` | Run simulation |
| POST | `/api/digital-twin/component/register` | Register component |
| GET | `/api/digital-twin/component/analyze` | Analyze component health |
| POST | `/api/digital-twin/quality/predict-degradation` | Predict quality degradation |
| GET | `/api/digital-twin/maintenance/forecast` | Maintenance forecast |
| GET | `/api/digital-twin/stats` | Integration statistics |

### Test Suite

| File | Tests |
|---|---|
| `tests/unit/test_i18n.py` | 43 |
| `tests/unit/test_digital_twin.py` | 47 |
| `tests/integration/test_i18n_digitaltwin_api.py` | 26 |
| **Total** | **116** |

> **Note (2026-02-28):** I18N and digital twin modules are deferred in the current workspace. Owner: Project maintainers. Target milestone: 2026-Q2.

### Acceptance Criteria

- [ ] 10 languages with fallback support
- [ ] 7 regional compliance frameworks
- [ ] 7 digital twin platform connectors
- [ ] Quality degradation forecasting (30–60 days)
- [ ] Predictive maintenance scheduling with 5 status levels
- [ ] All 116 tests passing

---

## 17. Compliance Module Pattern

All compliance and security automation modules follow a consistent pattern. Reference implementation: `civ_arcos/compliance/scap.py`.

### High-Priority Compliance Modules (Planned)

| ID | Module | Emulates |
|---|---|---|
| 1 | CIV-STIG | DISA STIGs configuration compliance |
| 2 | CIV-GRUNDSCHUTZ | BSI IT-Grundschutz methodology |
| 3 | CIV-ACAS | DISA ACAS vulnerability assessment |
| 4 | CIV-NESSUS | Tenable Nessus vulnerability scanning |
| 5 | CIV-SBOM | Software Bill of Materials |
| 6 | CIV-FEDRAMP | Federal cloud authorization |
| 7 | CIV-SOC2 | SOC 2 Type II trust services |
| 8 | CIV-ISO27001 | ISO 27001 information security |
| 9 | CIV-REGSCALE | Compliance as code (RegScale) |
| 10 | CIV-DIOPTRA | AI technology characterization |

### Module File Structure

```
civ_arcos/compliance/<module_name>.py
tests/unit/test_<module>.py
emu-soft/compliance/<module_name>.py
```

### Module Implementation Pattern

```python
"""Module docstring explaining the emulated tool/standard."""

from dataclasses import dataclass
from enum import Enum

@dataclass
class ModuleDataObject:
    """Domain-specific data structure."""
    pass

class ModuleEngine:
    """Main orchestration engine for the module."""

    def __init__(self):
        """Initialize with sample/demo data."""
        pass

    def perform_scan(self, input_data):
        """Core scanning/assessment functionality."""
        pass

    def generate_report(self, results):
        """Generate standardized reports."""
        pass
```

**Required Components:**
- Enums for status/severity levels
- Dataclasses for domain objects
- Parser/processor classes for standard rules
- Reporter class supporting multiple output formats
- Main engine class orchestrating all components

### API Pattern (3 Endpoints Per Module)

```python
POST /api/compliance/<module>/scan      # Run scan
GET  /api/compliance/<module>/report/{scan_id}  # Generate report
GET  /api/compliance/<module>/docs      # API documentation
```

### Dashboard Card Pattern

Add a card to `generate_compliance_page()` in `civ_arcos/web/dashboard.py` using USWDS classes.

### Implementation Checklist (Per Module)

- [ ] `civ_arcos/compliance/<module>.py` — data classes, enums, parser, reporter, engine
- [ ] Added to `civ_arcos/compliance/__init__.py`
- [ ] 3 API endpoints in `civ_arcos/api.py`
- [ ] Dashboard card in `civ_arcos/web/dashboard.py`
- [ ] Unit tests `tests/unit/test_<module>.py` — >90% coverage, all passing
- [ ] Copy to `emu-soft/compliance/`
- [ ] Update `emu-soft/compliance/README.md`
- [ ] Marked COMPLETE in `incorporate.md`

**Time Estimates:** Simple: 4–6 hrs | Medium: 8–12 hrs | Complex: 16–24 hrs

---

## 18. Unified Improvement Priorities

The following improvement order is the canonical execution sequence, based on highest ROI.

### Priority 1 — Core Software (Highest ROI)

1. Add formal plugin sandbox boundary (process isolation, resource/time limits), not just AST validation
2. Split large API surface into domain modules with a registry (`civ_arcos/api_routes/`)
3. Introduce versioned contracts for key payloads (evidence, assurance case, risk report) under `/api/v1/`
4. Add idempotency keys and replay protection to write endpoints and webhooks
5. Add persistence abstraction tests (cold start, crash recovery, concurrent writes) for graph/cache/task layers
6. Unified health model: liveness, readiness, dependency health (`/api/health/live`, `/api/health/ready`)
7. Structured logging + correlation IDs across the full request lifecycle
8. Harden webhook auth (signature validation, timestamp tolerance, nonce/replay cache)
9. Tenant-bound authorization on every read/write path with explicit isolation tests
10. API versioning prefix `/api/v1/` from the start

### Priority 2 — Documentation & Build System

1. Fix cross-document mapping inconsistencies and status drift
2. Normalize taxonomy into a canonical sequence (this document)
3. Deterministic rebuild runbook with expected commands and outputs
4. Verification gates (commands, expected outputs, artifacts)
5. Doc CI checks (lint, spellcheck, link validation, heading format)

### Priority 3 — Platform Foundations

1. `pyproject.toml` (PEP 517/518); minimal/homegrown dependencies
2. CI from Day 1: format, lint, type-check, tests, security scan
3. Coverage floor in CI (start lower, raise over phases; currently targeting 91%+)
4. Environment-variable-first configuration
5. Developer task runner (`Makefile` or equivalent)
6. Graph schema versioning + migration strategy
7. Docker health checks for runtime resilience

### Priority 4 — Strategic (Later Phase)

1. OpenAPI schema generation for large endpoint surface
2. TLS support in the custom web framework
3. Property-based testing (`hypothesis`) for integrity-critical logic
4. Clarify emulation philosophy boundaries for security-sensitive subsystems

### Quick Wins (1–2 Days)

1. Create `STATUS.md` and `VERIFICATION_MATRIX.md` as canonical truth files
2. Add baseline CI with lint/type/test/security
3. Add structured logging + correlation ID middleware
4. Add webhook signature + replay protection

---

## 19. Code Quality Standards

All production code must meet these standards:

**Required:**
- Type hints on all functions
- Comprehensive docstrings (module, class, method levels with Args/Returns)
- `try`/`except` error handling throughout
- Input validation on all API endpoints
- Unit test coverage >90% per module
- No external dependencies beyond the permitted list (100% homegrown where mandated)

**Style:**
- Formatted with `black`
- Lint-clean: `flake8 civ_arcos tests --max-line-length=100`
- Type-safe: `mypy civ_arcos` exits clean

**Best Practices:**
- Use `@dataclass` for data structures
- Use `Enum` for status/severity classifications
- Provide sample/demo data in `__init__` for testability
- Keep functions focused and independently testable
- Follow existing naming conventions throughout

---

## 20. Testing Strategy

### Unit Tests

- Test each component independently
- Mock external dependencies (API calls, file I/O)
- Test error conditions and edge cases
- Target execution time: <1 second per test

### Integration Tests

- Test API endpoints end-to-end
- Test dashboard pages render valid HTML
- Test complete workflows
- May be slower but must be reliable and deterministic

### Manual Testing

```bash
# Start API server
python -m civ_arcos.api

# Run all tests
pytest tests/ -q

# Run with coverage
coverage run -m pytest -q && coverage report -m

# Lint and type check
python -m flake8 civ_arcos tests
python -m black --check civ_arcos tests
mypy civ_arcos

# Docs consistency gate
python scripts/docs_consistency_check.py
```

### Quality Gates for CI

| Check | Command | Target |
|---|---|---|
| Formatting | `python -m black --check civ_arcos tests` | 0 drift |
| Linting | `python -m flake8 civ_arcos tests` | 0 errors |
| Type safety | `mypy civ_arcos` | 0 critical errors |
| Coverage | `coverage run -m pytest -q && coverage report -m` | ≥91% |
| Docs consistency | `python scripts/docs_consistency_check.py` | PASS |

---

## 21. Verification Matrix

Last updated: 2026-02-28

### Status Legend

- `NOT_RUN` — not yet executed in centralized verification flow
- `PASS` — executed and matched expected outcome
- `FAIL` — executed, outcome did not match
- `PARTIAL` — partially verified; follow-up needed
- `DEFERRED` — deferred with documented owner and milestone

### Core Claims Verification

| ID | Feature | Module(s) | Command | Status | Notes |
|---|---|---|---|---|---|
| V-001 | Base API health endpoint | `civ_arcos/api.py` | `GET /api/status` | PASS | Returns 200 + version payload |
| V-002 | Evidence graph persistence | `civ_arcos/storage/graph.py` | `pytest tests/unit/test_graph.py -q` | PASS | 9 tests passing |
| V-003 | Evidence checksum/provenance | `civ_arcos/evidence/collector.py` | `pytest tests/unit/test_evidence.py -q` | PASS | 8 tests passing |
| V-004 | Badge generation SVG | `civ_arcos/web/badges.py` | `pytest tests/unit/test_badges.py -q` | PASS | 8 tests passing |
| V-005 | Analysis pipeline | `civ_arcos/analysis/*` | `pytest tests/unit/test_static_analyzer.py tests/unit/test_security_scanner.py tests/unit/test_test_generator.py -q` | PASS | 21 tests passing |
| V-006 | Assurance case generation | `civ_arcos/assurance/*` | `pytest tests/unit/test_case.py tests/unit/test_gsn.py tests/unit/test_templates.py -q` | PASS | 21 tests passing |
| V-007 | Dashboard routes render HTML | `civ_arcos/api.py`, `civ-arcos-carbon.html` | `pytest tests/integration/test_dashboard.py -q` | PASS | 2 tests passing |
| V-008 | Cache/task emulation under load | `N/A` | `N/A` | DEFERRED | Owner: Project maintainers. Milestone: 2026-Q2 |
| V-009 | Webhook auth hardening | `civ_arcos/web/webhook.py` | `pytest tests/unit/test_webhook.py tests/integration/test_health_webhook.py -q` | PASS | 22 tests passing |
| V-010 | Multi-tenant isolation | `civ_arcos/core/tenants.py` | `pytest tests/integration/test_api.py -k "tenant or settings or evidence" -q` | PASS | 12 tests including cross-tenant deny paths |
| V-011 | Blockchain ledger | `civ_arcos/distributed/blockchain_ledger.py` | `pytest tests/integration/test_api.py -k blockchain -q` | PASS | 3 tests passing |
| V-012 | I18N + digital twin | `N/A` | `N/A` | DEFERRED | Owner: Project maintainers. Milestone: 2026-Q2 |
| V-013 | Structured logging + correlation IDs | `civ_arcos/web/framework.py` | `pytest tests/unit/test_framework_logging.py -q` | PASS | 10 tests passing |
| V-014 | Health endpoints (live/ready/dependencies) | `civ_arcos/api.py` | `pytest tests/integration/test_health_webhook.py -k health -q` | PASS | 9 tests passing |
| V-015 | Write-endpoint idempotency | `civ_arcos/web/idempotency.py` | `pytest tests/unit/test_idempotency.py tests/integration/test_api.py -q` | PASS | 14 tests (5 unit, 9 integration) |
| V-016 | Versioned contracts (`/api/v1/*`) | `civ_arcos/contracts/v1.py` | `pytest tests/integration/test_api.py -q` | PASS | Contract envelope on all v1 responses |
| V-017 | Plugin sandbox boundary | `civ_arcos/core/plugin_marketplace.py` | `pytest tests/unit/test_plugin_marketplace.py tests/integration/test_plugin_api.py -q` | PASS | 10 tests (5 unit, 5 integration) |
| V-018–V-027 | Platform/admin/plugin/analysis domain modularization, compliance reports, quality metrics, report scheduling | Various `civ_arcos/api_routes/*` | `pytest tests/integration/test_api.py -q` | PASS | 35 tests passing (V-027) |
| V-028 | Tenant-scoped compliance reports | `civ_arcos/core/compliance_reports.py` | `pytest tests/integration/test_api.py -k "compliance and report" -q` | PASS | 3 tests, cross-tenant blocked |
| V-029 | Azure OpenAI adapter behind opt-in | `civ_arcos/analysis/llm_integration.py` | `pytest tests/unit/test_llm_integration.py tests/integration/test_analysis_api.py -q` | PASS | Fallback to mock when unconfigured |
| V-030 | Blockchain sync event stream | `civ_arcos/distributed/sync_events.py` | `pytest tests/integration/test_api.py -k "sync_events or blockchain" -q` | PASS | No duplicate replay events |
| V-031 | Dashboard live update hooks | `civ-arcos-carbon.html` | `pytest tests/integration/test_dashboard.py tests/integration/test_api.py -k "dashboard or sync_events or blockchain" -q` | PASS | `initDashboardLiveUpdates` polling `/api/sync/events` |
| V-032 | Plugin versioning + compatibility | `civ_arcos/core/plugin_marketplace.py` | `pytest tests/unit/test_plugin_marketplace.py tests/integration/test_plugin_api.py -q` | PASS | `PluginManifest` version constraints |
| V-033 | Predictive quality forecasting | `civ_arcos/core/quality_metrics_history.py` | `pytest tests/integration/test_api.py -k "quality_metrics_forecast or quality_metrics_trends or quality_metrics_record" -q` | PASS | Deterministic slope-based projections |

### Non-Functional Verification

| ID | Goal | Command | Status | Notes |
|---|---|---|---|---|
| Q-001 | Linting baseline | `python -m flake8 civ_arcos tests` | PASS | 0 errors |
| Q-002 | Formatting baseline | `python -m black --check civ_arcos tests` | PASS | 64 files unchanged |
| Q-003 | Type safety | `mypy civ_arcos` | PASS | 0 critical errors |
| Q-004 | Coverage baseline | `coverage run -m pytest -q && coverage report -m` | PASS | 169 tests, 91% coverage |
| Q-005 | Docs consistency | `python scripts/docs_consistency_check.py` | PASS | Cross-doc Q-row parity validated |

---

## 22. Release Readiness Checklist

Mark all as complete before a formal release candidate:

- [ ] All `V-*` rows for in-scope features are `PASS` or explicitly `DEFERRED` with owner and milestone
- [ ] All `Q-*` rows are `PASS`
- [ ] `STATUS.md` updated with current confidence level and verification date
- [ ] All deferred items documented with owner and target milestone
- [ ] `README.md` updated with all active endpoints and features
- [ ] `emu-soft/compliance/README.md` updated for all implemented modules

---

## 23. Update Protocol

When any implementation work changes scope, priority, or completion status, update **all** of the following in a single commit:

1. **This file** (`build-guide.md`) — narrative and acceptance criteria
2. **`README.md`** — endpoint references and feature status in the roadmap
3. **`copilot.md`** (or equivalent tracker) — execution log
4. **`build_docs/STATUS.md`** — changelog entry with date and confidence level
5. **`build_docs/VERIFICATION_MATRIX.md`** — passing evidence, command output, and timestamps

This keeps the roadmap, execution log, and verification evidence synchronized at all times.

---

*CIV-ARCOS — Military-grade assurance for civilian code.*