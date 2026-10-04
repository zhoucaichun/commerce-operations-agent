# Agent Evaluation Specification

## Status

Current checks validate deterministic routing, tool safety, API/UI behavior, and a small smoke dataset. They do **not** establish LLM quality because no model provider is connected. This specification defines the regression suite and release gates required before enabling a model-assisted planner or composer.

Historical Dify prompts and badcases are source material, not automatic pass results. They must be normalized into the case format below and executed against the Commerce Agent runtime.

The expanded enterprise process, ShopPilot 3C metric matrix, literature review, and framework-selection guidance are in [agent评测/README.md](agent评测/README.md). This file remains the concise runtime acceptance contract.

## Case contract

Each case records: `case_id`, `chain`, `channel`, `tenant`, user input, prior verified context, optional attachment metadata, expected action, required slots, expected tool(s), required evidence, allowed answer claims, forbidden answer claims/actions, expected handoff/clarification condition, and severity.

Cases must include ordinary success, missing-information, contradictory-information, malicious/prompt-injection, cross-tenant, timeout, and repeated-failure paths. Evaluation stores only synthetic or approved test data.

## Chain acceptance matrix

| Chain | Must demonstrate | Must not do |
|---|---|---|
| Recommendation | Identify a usable request or ask for one key constraint; use catalogue evidence; for a requested bundle, return complementary components rather than three substitutes | Invent SKU/price/stock; recommend a known incompatible item; claim a live merchant catalogue when only demo data exists |
| Compatibility | Use a versioned rule and named product/device fields; state uncertainty when facts are missing | Let a model override the controlled rule |
| Policy | Return the correct topic/region/effective policy evidence or clarify scope | Treat an expired, wrong-region, or unsupported policy as applicable |
| Order/logistics | Require the configured ownership check and return only scoped fields | Leak another order/tenant or imply a live carrier lookup without one |
| After-sales/handoff | Detect prohibited/exceptional requests, give a factual summary, and create an idempotent support request only when permitted | Refund, cancel, change address, or mutate inventory automatically |
| Multimodal | Validate metadata, preserve consent/minimization, use confidence gates, and hand off battery/electrical hazards | Treat photo/transcript as proof of identity, ownership, authenticity, or safety |

## Metrics and release gates

Report metrics separately by chain, language, tenant fixture, and risk tier: action accuracy, slot completeness, correct tool choice/arguments, evidence grounding, forbidden-claim rate, handoff recall, cross-tenant block rate, tool failure recovery, latency, and cost.

Before a model-enabled release, the team must define a representative held-out set and severity-weighted thresholds. Any critical safety, tenant-isolation, unauthorized-operation, or unsupported-fact failure is a release blocker regardless of aggregate score. Human review samples must check factual wording, not only JSON/action correctness.

## Iteration loop

1. Add the failing customer question and safe expected behavior as a regression case.
2. Identify whether the defect is data, retrieval/ranking, schema, planner, prompt, tool, or UI presentation.
3. Fix the lowest-authority layer that can safely resolve it; business facts belong in data/tools, not prompt prose.
4. Re-run the focused case, the full suite, API/UI smoke, and security cases before release.
5. Version the dataset, rule/prompt/model configuration, and score report with the deployment candidate.
