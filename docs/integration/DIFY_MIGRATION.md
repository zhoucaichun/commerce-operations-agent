# Dify migration boundary

## Decision

`ShopPilot Commerce Agent` is the runtime owner for the ShopPilot 3C Store. Dify is retained as a reviewed historical workflow, migration source, and future regression reference; it is not required for the Store Widget or Store-originated full chat page.

## Migrated assets

| Source | Packaged destination | Runtime use |
|---|---|---|
| Dify DSL export | `docs/dify/` | Traceability only; no key or API invocation |
| 55 synthetic products | `src/backend/commerce_agent/data/dify_product_catalog.csv` | Deterministic search, recommendation, compatibility evidence |
| 35 synthetic policies | `src/backend/commerce_agent/data/dify_policy_catalog.csv` | Region/topic policy evidence |
| 100 full + 30 + 15 regression prompts | `src/eval/data/dify_eval_*.csv` | Evaluation source for the next evaluation expansion |

`catalog_loader.py` normalizes source headers into the controlled tool schema. The in-memory MVP also retains three legacy safety-test products and two legacy policies, so the runtime count is 58 products and 37 policies.

## Intent and slot correspondence

| Historical Dify branch | Commerce Agent path |
|---|---|
| Recommendation / budget / candidate sort | `recommend_products` with device, country, budget, category and usage constraints |
| Compatibility | `compatibility_check` with catalogue declaration and power/port fallback rule |
| Policy / product availability | `policy_search` filtered by topic and region |
| Direct high-risk handoff | guard and simulated-ticket/handoff path |
| Clarification | `needs_input` response when verified information is absent |

The current MVP uses deterministic rules, not a model call, so answers stay grounded in the packaged synthetic records. It must not claim real price, stock, Shopify availability, delivery data, or execute a merchant operation.
