# Changelog

## Unreleased

### Evaluation and observability

- Expanded deterministic synthetic evaluation to 30 cases and added completed/needs-input metrics plus derived handoff and tool-call rates.
- Added a read-only frontend operations summary; it contains only synthetic runtime counters.
- Added UTC hourly cumulative metric snapshots persisted by SQLite and opt-in PostgreSQL stores, with recent snapshot buckets in the dashboard.

### LangGraph and state resilience

- Added explicit LangGraph guard, planner, controlled-tool, validation and handoff nodes around the synthetic agent.
- Added Redis-backed synthetic session checkpoints and bounded retry counters for read-only tools; Redis absence remains a safe no-retry fallback.
- Added PostgreSQL seed parity for cable and warranty data, opt-in repository tests, and a Compose smoke that checks API-restart ticket persistence.

### CI

- Added GitLab CI jobs for unit/API/graph regression, deterministic evaluation, isolated PostgreSQL repository tests, and Docker Compose restart-persistence smoke checks.
- Added JUnit and JSON evaluation report artifacts for GitLab pipeline review.

### Synthetic identity and authorization

- Added environment-only synthetic Bearer token authentication with viewer, support, and operator roles; no real identity provider or user data is connected.

### Web MVP

- Added a dependency-free, API-hosted frontend for safe chat, order lookup inputs, simulated ticket creation, trace summaries, and human-handoff presentation.
- Added synthetic order/ticket detail cards and same-request retry for recoverable errors; neither path can trigger a real merchant mutation.
- Added frontend endpoint and Compose smoke coverage; the web client only calls this repository's FastAPI endpoint.
- Added browser E2E coverage, CSP and defensive browser response headers, plus explicit UI messaging for authentication, permission, idempotency, validation and rate-limit failures.
- Added keyboard navigation, skip link and focus styles, plus a TLS reverse-proxy template, secret-handling template, and non-implemented OIDC design documentation.
- Added automated Nginx template validation, a certificate rotation/rollback runbook, and an approval-gated OIDC rollout decision record.
- Added CI checks for Nginx template validation and production-document safety guidance.
- Added an explicit external security-approval checklist that blocks OIDC sandbox activation until signed outside the repository.

### Added

- Added a dependency-free local backend slice under `src/backend/commerce_agent/`.
- Added input validation, synthetic catalog/policy/order data, session state, traces, metrics, and a controlled tool registry.
- Added product search, compatibility checks, policy search, order/shipment lookup, and idempotent simulated ticket creation.
- Added a six-step guard and explicit handoff for prohibited real-world mutations.
- Added HTTP endpoints for health, readiness, metrics, and chat.
- Added six standard-library unit tests for core and safety paths.

### Verification

- `python -m unittest discover -s tests -p "test_*.py" -v`: 6 tests passed.
- HTTP smoke for `/health`, `/ready`, a synthetic order lookup, and a refund handoff passed.

### Not included

- No FastAPI/Pydantic, PostgreSQL, Redis, LangGraph, LLM, frontend, Docker, migration, CI, or full evaluation dataset is included yet.
- No real merchant system, inventory mutation, refund, cancellation, or address mutation was used.

### FastAPI upgrade

- Replaced the standard-library HTTP adapter with FastAPI/Pydantic and OpenAPI support.
- Added local SQLite migrations for sessions, simulated tickets, and metrics; persistence is opt-in through `COMMERCE_DB_PATH`.
- Added API contract tests and a deterministic evaluation smoke entry.

### Deployment foundation

- Added isolated Docker Compose services for API, PostgreSQL, and Redis, with health checks and separate volumes.
- Added synthetic-only PostgreSQL initialization metadata and deployment/rollback documentation.
- PostgreSQL/Redis are not yet wired into business storage; no production or merchant system connection was added.

### External storage adapters

- Added opt-in PostgreSQL storage for sessions, simulated tickets, and metrics.
- Added opt-in Redis readiness guard and Compose connection configuration.
- External-service runtime verification remains pending because the local Docker configuration is inaccessible.

### Redis guards

- Added Redis-backed fixed-window chat rate limiting and short-lived idempotency locks for simulated ticket requests.
