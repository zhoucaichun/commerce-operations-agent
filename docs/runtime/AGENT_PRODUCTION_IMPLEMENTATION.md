# Agent Completion and Production Activation Plan

This document is the implementation record for the ten Agent capabilities. It distinguishes code available in this repository from activation that requires an external merchant, model provider, or identity-provider authorization.

| Capability | Delivered in repository | Activation boundary |
|---|---|---|
| 1. Model adapter | OpenAI-compatible `ModelAdapter`, Qwen-compatible provider label, optional JSON Schema request, local typed validation, timeout, environment-only configuration, deterministic fallback | Provide an approved provider endpoint/key/model outside Git; run the synthetic Dify model evaluation before enabling |
| 2. Agent loop | LangGraph `guard -> load_memory -> planner -> tool -> validate -> compose/handoff -> persist`; six-step inner tool boundary | Model planner/composer only after evaluation gate passes |
| 3. Dify migration | Four Dify branch families mapped to typed intents, slots, controlled tools, and regression records | Review/port any later Dify prompt change through versioned tests |
| 4. Tool harness | Allow-list, typed plan validation, tool-result validation, read-only retry, idempotent simulated ticket, risk handoff | No commerce write is enabled; any new write requires security/product approval |
| 5. Memory | Thread-scoped summaries/slots, bounded compaction, explicit preference writing, user memory-delete command | Tenant-scoped durable memory, retention/deletion jobs, and consent review for production |
| 6. Retrieval/recommendation | Catalogue/policy lexical retrieval, metadata filters, source labels, compatibility rules, bundle selection of complementary charger+cable components | pgvector/hybrid retrieval and merchant catalogue projection after approved data connection |
| 7. Multimodal | Bounded metadata adapter, safety/confidence gate, battery-risk handoff, no byte retention | Approved STT/vision provider, encrypted object store, scanning, EXIF stripping, consent/retention controls |
| 8. Human handoff | Reason code, structured summary, priority, SLA target, simulated lifecycle and idempotent ticket creation | Approved helpdesk integration and staff workflow/SLA ownership |
| 9. Evaluation | Unit/API/graph/model-safety tests, deterministic smoke/eval, Dify source datasets, regression contract | Human labels, held-out model suite, red-team results, score thresholds and release sign-off |
| 10. Merchant/OIDC | Read-only connector protocol, disabled-by-default Shopify boundary, readiness endpoint, synthetic roles | Shopify OAuth/sandbox/test merchant, encrypted secret manager, PostgreSQL RLS, OIDC issuer and security approval |

## Model configuration

Set these only in a local untracked environment file or deployment secret manager:

```text
COMMERCE_LLM_BASE_URL=https://approved-provider.example/v1
COMMERCE_LLM_API_KEY=provider-secret
COMMERCE_LLM_MODEL=approved-model-name
COMMERCE_LLM_PROVIDER=qwen_openai_compatible
COMMERCE_LLM_RESPONSE_MODE=json_schema
COMMERCE_LLM_TIMEOUT_SECONDS=8
```

The adapter calls the OpenAI-compatible `/chat/completions` endpoint with `temperature: 0` and JSON-object output by default. When an approved endpoint supports it, `COMMERCE_LLM_RESPONSE_MODE=json_schema` requests a strict action-plan/answer schema; local allow-list validation remains authoritative. It sends only a bounded customer message, verified slots, response draft, and evidence summary. It never sends secrets, raw attachment bytes, full order identity information, or another tenant's data. If configuration is incomplete, network access fails, the selected endpoint does not support the schema mode, or model JSON is invalid, the deterministic route and templated answer are used instead. See [QWEN_MODEL_SETUP.md](QWEN_MODEL_SETUP.md) for the explicit synthetic-only evaluation sequence.

## Dify-to-runtime prompt contract

The imported workflow informs intent names and slot fields: `device_model`, `country`, `budget_text`, `usage_scenario`, `category_preference`, `target_product`, `connector_type`, `power_requirement`, `risk_reason`, and `handoff_needed`. The runtime planner may only return `call_tool`, `ask_user`, or `handoff`, and only these intents: product, recommendation, compatibility, policy, order, ticket, handoff.

Business facts are never prompt-only: compatibility is resolved by the compatibility tool; policy uses scoped policy records; order access needs the suffix check; a support write requires idempotency; protected commerce operations always hand off. See [DIFY_WORKFLOW_SPEC.md](DIFY_WORKFLOW_SPEC.md) and [AGENT_RUNTIME_SPEC.md](AGENT_RUNTIME_SPEC.md).

## Retrieval and recommendation contract

1. Filter candidate products by tenant/catalogue scope, region, declared device compatibility, category, and budget before re-ranking.
2. Attach SKU, source, price timestamp/value, compatibility declaration, and limitations to output evidence.
3. A `bundle`/`套餐`/`套装` request selects complementary components before filling remaining recommendation positions; it must not return only three interchangeable chargers.
4. Vehicle products are penalized unless vehicle context is explicit. Public-reference records remain labelled non-live and are never claimed as merchant stock.
5. Missing high-value constraints cause one focused clarification rather than a confident recommendation.

## Multimodal and handoff contract

The MVP accepts metadata only. Production upload flow is `consent -> signed upload -> MIME signature/size/duration check -> malware scan -> EXIF strip -> provider adapter -> confidence/safety gate -> controlled tools`; raw media never enters traces/checkpoints. A possible swollen/damaged battery, uncertainty about electrical safety, or low-confidence ownership extraction must hand off.

Handoffs are structured as `reason`, `summary`, `priority`, `sla_hours`, and `lifecycle`. The simulated lifecycle is `simulated_open -> simulated_in_progress -> simulated_resolved`; it does not contact a real helpdesk. A future staff resolution may add an approved, evidence-linked summary to a conversation, but never changes the original tool evidence.

## Production release gate

`GET /api/v1/production-readiness` intentionally reports configuration booleans only and always reports `live_operations_enabled: false`. Production activation requires all of the following outside this repository: model evaluation threshold/sign-off, Shopify sandbox OAuth installation, encrypted secrets, PostgreSQL tenant RLS, OIDC organization/role mapping, DPA/security approval, monitoring, backup/restore drill, connector rollback, and an explicit decision for each requested write operation.
