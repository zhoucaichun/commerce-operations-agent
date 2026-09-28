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
