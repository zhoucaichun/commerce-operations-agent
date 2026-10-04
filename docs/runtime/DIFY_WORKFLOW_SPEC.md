# Dify Workflow Migration Specification

## Role of the exported workflow

The exported Dify workflow is a reviewed historical asset, not the ShopPilot Commerce Agent runtime, database, authorization layer, or merchant connector. Its value is the product work already invested in prompts, intent splits, slot design, and badcase iteration.

Source assets remain traceable in:

- `docs/dify/跨境 3C Copilot（接前端）.yml` — DSL export;
- `src/backend/commerce_agent/data/dify_product_catalog.csv` and `dify_policy_catalog.csv` — reviewed synthetic seed data;
- `src/eval/data/dify_eval_*.csv` — historical prompt/evaluation inputs.

Keys, user conversations, and real merchant data must never be copied from Dify into this repository.

## Branch inventory and migration target

| Dify branch/node family | Business outcome | Runtime target |
|---|---|---|
| State reset and exception classifier | Clear stale context and detect unsafe/ambiguous input | Guard + scoped memory normalization |
| Intent router | Classify recommendation, compatibility, policy, order/logistics, handoff, or clarification | Typed planner action |
| `LLM_RECO_SLOT_UPDATE` | Capture device, budget, country, scenario and recommendation constraints | Slot extraction followed by `recommend_products` |
| `LLM_COMPAT_SLOT_UPDATE` | Capture device/product/SKU details for compatibility | Slot extraction followed by compatibility rule tool |
| `LLM_POLICY_QUERY_BUILD` | Build policy topic/region query | Schema-checked `policy_search` |
| `LLM_HANDOFF_DIRECT` | Explain a risk or exception and route to support | Handoff reason + controlled ticket request |
| `LLM_CLARIFY` | Ask the smallest necessary missing question | `ask_user` planner action |

## Per-chain implementation record

For every migrated branch, maintain the following fields in a versioned implementation record or evaluation case:

1. User goal and supported channel (Widget, full consumer chat, or merchant staff console).
2. Required and optional slots, normalizers, and acceptable confidence thresholds.
3. Typed action/output schema and the only permitted tools.
4. Evidence required before making a factual claim.
5. Safety constraints, forbidden claims/actions, and handoff conditions.
6. Representative historical badcases, expected result, and a regression identifier.

This keeps PRD requirements stable while allowing prompts, few-shot examples, and model/provider choices to evolve safely.

## Migration method

1. Extract the branch intent, slots, prompt constraints, and JSON/output contract from the DSL.
2. Translate it into the typed planner/tool contract in [AGENT_RUNTIME_SPEC.md](AGENT_RUNTIME_SPEC.md); do not paste unreviewed prompt text directly into production.
3. Preserve business-critical instructions as executable rules, schemas, evidence requirements, or handoff gates whenever possible.
4. Convert each evaluated Dify badcase into a case in [EVALUATION_SPEC.md](../agent评测/EVALUATION_SPEC.md), including a golden action/evidence expectation and forbidden outcomes.
5. Run deterministic tools first; only then introduce a replaceable model adapter behind structured output validation and release gates.

## Explicit non-goals

- Dify does not own tenant data, session persistence, RBAC, audit logs, Shopify OAuth, or production operations.
- A model response never substitutes for compatibility rules, policy effective dates, ownership verification, or merchant-scoped data.
- The current MVP must not present Dify-derived synthetic records as live Shopify product, inventory, or order information.
