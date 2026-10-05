# Agent Runtime Contract

## Status and purpose

This is the canonical contract for the ShopPilot Commerce Agent runtime. It defines the production target and makes the current MVP boundary explicit. It complements the outcome requirements in [PRD.md](../PRD.md), the implementation view in [技术架构.md](../技术架构.md), the reviewed Dify reference in [DIFY_WORKFLOW_SPEC.md](DIFY_WORKFLOW_SPEC.md), and measurable release gates in [评测规范.md](../agent评测/评测规范.md).

**Current MVP:** FastAPI invokes a LangGraph state-machine shell around deterministic, controlled catalogue, compatibility, policy, order, and simulated-ticket tools. No LLM provider is connected. The graph's current `planner` is keyword/rule based, not an LLM planner. All data is synthetic or labelled public-reference demonstration data.

**Production target:** a model-assisted planner and answer composer may improve language understanding and explanation, but every operational fact and decision remains constrained by the tools, schemas, policy, authorization, and safety harness below.

## Runtime responsibilities

| Component | Production responsibility | MVP status |
|---|---|---|
| Model | Extract intent/slots, propose a typed next action, summarize tool evidence, and produce user-facing language | Not connected; deterministic routing/templates only |
| Planner | Select `ask_user`, `call_tool`, `respond`, or `handoff` within a typed action schema | Rule-based routing only |
| Tool use | Query approved merchant-scoped read models and create only approved, idempotent support requests | Controlled synthetic tools; simulated tickets only |
| Memory | Keep thread state, verified slots, tool summaries, and approved preferences in tenant scope | Synthetic sessions/checkpoints; no long-term customer profile |
| Harness | Enforce identity, tenant scope, schemas, allow-lists, risk routing, limits, auditability, and safe fallback | Core input/risk/step checks exist; production controls remain pending |

## Model contract

The model may classify, extract slots, ask one necessary question, choose among registered actions, re-rank tool candidates using declared attributes, and compose an evidence-grounded answer. It must not:

- invent SKU, price, stock, shipment, policy, compatibility, order, or merchant facts;
- make refund, cancellation, inventory, address, payout, or permission decisions;
- issue raw SQL, HTTP requests, shell commands, or unvalidated tool arguments;
- expose hidden reasoning, secrets, full personal data, or another tenant's records.

The model receives minimized, role-scoped context and summarized prior tool results. It returns a schema-validated action; internal reasoning is neither requested nor persisted as customer-visible trace data.

## Planner and loop

The planner output is a typed record conceptually shaped as:

```json
{
  "action": "ask_user | call_tool | respond | handoff",
  "required_slots": ["device_model"],
  "tool_name": "recommend_products",
  "arguments": {"device_model": "iPhone 15"},
  "user_question": null,
  "reason_code": "recommendation_ready"
}
```

Only one action is accepted per turn. `tool_name` must be in the registered allow-list, and `arguments` must pass that tool's Pydantic schema. The loop is:

```text
guard -> load scoped memory -> plan -> tool/ask/handoff -> validate -> plan or compose -> persist trace
```

The harness stops after the configured step limit, on timeout, invalid output, cross-tenant access, repeated failure, or a high-risk request. It then asks for a minimal clarification, returns a safe degraded response, or creates a simulated/approved human handoff.

## Controlled tools

| Tool family | Required proof before response | Authority |
|---|---|---|
| Product search and recommendation | Tenant catalogue records, source label, effective price/availability timestamp | Read-only |
| Compatibility | Registered compatibility rule/version plus product/device fields | Read-only decision support |
| Policy | Effective policy version, region and applicability | Read-only |
| Order and shipment | Tenant scope, order identifier, required ownership check | Read-only, minimized output |
| Support ticket | Valid idempotency key and approved handoff reason | Controlled write; no commerce mutation |

Future Shopify/ERP/OMS adapters query a tenant-local, read-only projection, never arbitrary merchant database credentials. See [PRODUCTION_MERCHANT_DATA.md](../integration/PRODUCTION_MERCHANT_DATA.md).

## Memory and trace contract

Short-term memory may contain a `thread_id`, verified slots, concise message summaries, tool references, risk state, and retry/step counters. Long-term preferences require explicit user confirmation. Attachments, raw secrets, full identity data, and hidden model reasoning are not placed in prompts, checkpoints, or logs.

Every operation records request/thread/tenant identifiers, action and tool names, schema-safe parameters, evidence references, policy/prompt/model versions where applicable, timing, status, and reason codes. Audit records are tenant-scoped and retention-controlled.

## Harness requirements before production activation

1. OIDC authentication with organization, membership, and role mapping; a Widget visitor never receives staff permissions.
2. PostgreSQL row-level tenant isolation, encrypted secrets, rate limits, idempotency locks, tool timeouts, retries, circuit breakers, and alerting.
3. Prompt-injection defenses for text/OCR, attachment scanning and consent controls, and no unrestricted browser/model tool access.
4. Approval gates for any new write capability; refunds, cancellations, inventory changes, and address changes remain disabled unless separately designed and approved.
5. Evaluation gates defined in [评测规范.md](../agent评测/评测规范.md), red-team tests, security review, sandbox connector verification, and rollback drills.
