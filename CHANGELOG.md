# Changelog

## Unreleased

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
