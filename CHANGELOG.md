# Changelog

## Unreleased

- Translated and renamed the Agent evaluation runtime contract to `docs/agent评测/评测规范.md`; assessment fields remain stable English identifiers while requirements and release gates are Chinese.
- Reorganized project documentation by product, runtime, integration/data, Agent evaluation, and operations; added `docs/INDEX.md` with a status-aware reading path and updated repository links, documentation tests, and production-document validation paths.

- Added `docs/agent评测/`: a versioned enterprise Agent-evaluation playbook, ShopPilot 3C customer-service/recommendation metric system, and a critical review of recent benchmark research and evaluation frameworks. The documentation explicitly separates deterministic evidence, LLM judging, human calibration, synthetic MVP results, and future real-merchant production metrics.

- Corrected the OpenAI-compatible endpoint builder: service-root URLs now use `/v1/chat/completions`, while URLs already ending in `/v1` remain supported. Added a documented custom-path override and regression tests.

- Added secret-free aggregate LLM adapter diagnostics to live model evaluation reports, distinguishing provider HTTP/network/JSON/response-shape failures from local schema rejection without retaining keys, URLs, prompts, or responses.

- Added a Qwen-labelled OpenAI-compatible model configuration path, optional JSON Schema request mode, and local schema/authority validation fallback.
- Added an explicit `--live` Dify model-evaluation runner for all 145 migrated synthetic cases; its default dry run makes no provider call and reports only dataset/model scope.
- Added Qwen model-selection, secret-handling, and staged synthetic-evaluation guidance; no real merchant, order, media, or Shopify data is sent to a model.

- Added an optional, bounded OpenAI-compatible model adapter for JSON-validated Agent plans and evidence-grounded answer composition; it defaults to deterministic fallback and never enables commerce operations.
- Expanded the LangGraph execution path to guard, memory load, typed plan, controlled tool, validation, compose/handoff, and persistence nodes.
- Added explicit memory deletion/compaction and user-confirmed preference rules, structured simulated handoff priority/SLA fields, complementary bundle selection, a disabled read-only Shopify connector boundary, and a secret-safe production-readiness endpoint.
- Added the Agent completion/production-activation document and model-runtime regression tests.

- Defined the canonical Agent runtime contract (Model, Planner, Tool use, Memory, Harness), including the distinction between the current deterministic LangGraph MVP and a future model-assisted runtime.
- Added a Dify workflow migration specification and an Agent evaluation specification, so reviewed Dify prompts/nodes/badcases are source material rather than an unbounded runtime dependency.
- Corrected README status language: FastAPI, Next.js, Compose, Redis, LangGraph state-machine, CI, and deterministic checks exist; LLM quality, real merchant connectors, production RLS/OIDC, and full release evaluation remain incomplete.

- Prevent the legacy static recommendation preview from appearing in Store-origin Commerce Agent conversations.
- Hide Store Widget starter prompts immediately after the first customer action, preserving room for the ongoing conversation.
- Restyled the Store-origin full-chat composer as a privacy-labelled pill with voice, attachment, camera and send controls; actions remain synthetic-only demonstrations.
- Added direct text chat and synthetic voice/photo actions to the ShopPilot Store Widget, with a shared Agent `thread_id` when opening the full conversation page.
- Added a dated, source-labelled public product-reference catalogue for realistic demonstration facts. It is not a live merchant connection, inventory feed, or price promise.
- Improved non-vehicle iPhone charging-bundle ranking to avoid car chargers and added regression coverage.

## Unreleased

- Added structured recommendation evidence to Agent responses so the web can show SKU, category, price, and migrated synthetic-catalogue provenance.
- Documented the non-implemented production merchant-data path: tenant-scoped PostgreSQL, Shopify OAuth/read-only projection, and approval gates.

- Added a synthetic multimodal MVP: bounded image/audio metadata, synthetic recognition summaries, compatibility slot enrichment, and a battery-safety handoff gate; no media bytes or model provider are used.

- Migrated the reviewed Dify synthetic catalogue (55 products), policy set (35 records), and 145 evaluation prompts into this repository; no Dify API key or real merchant data was copied.
- Added deterministic `recommend_products` ranking and expanded compatibility/policy lookup to use the migrated synthetic records.
- Routed all ShopPilot Store-originated full-chat questions to the Commerce Agent; the old Dify route is now a historical standalone comparison path only.
- Added Dify migration traceability and a runnable ShopPilot functional MVP demo guide.

- Added the original ShopPilot 3C Store storefront mock with a floating AI Assistant preview and support entry points.
- Styled store-originated full conversations in the matching storefront theme and corrected their return path to the simulated store.
- Added a synthetic two-merchant B2B demonstration: consumer Widget, Merchant Console, merchant-scoped Agent state and simulated ticket handling.
- Added B2B product, architecture and delivery-plan documentation, including explicit production boundaries.

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
- Copied the existing ShopPilot Next.js source into `src/web` without modifying the AIPM project, retaining Dify recommendation routing and adding a server-side Commerce Agent proxy plus dual-routing plan.
- Routed operations intents within the copied chat page to the Commerce Agent and rendered structured synthetic operation result cards in the existing chat stream.
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
