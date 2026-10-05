# Agent 运行时契约

## 状态与用途

这是 ShopPilot Commerce Agent 的运行时契约。它区分当前 MVP 与生产目标，并补充 [PRD](../PRD.md) 的用户结果、[技术架构](../技术架构.md) 的实现视图、[Dify 工作流说明](DIFY_WORKFLOW_SPEC.md) 的历史迁移关系，以及 [评测规范](../agent评测/评测规范.md) 的发布门槛。

**当前 MVP：**FastAPI 在确定性的目录、兼容性、政策、订单和模拟工单工具外运行 LangGraph 状态机。模型适配器默认未配置；在显式环境变量配置后，可仅对合成数据进行受控的 OpenAI 兼容模型试验，失败始终回退为规则路径。当前 Planner 默认是关键词/规则路由，而非生产级 LLM Planner；全部数据均为合成或标记为公开参考的演示数据。

**生产目标：**模型辅助的 Planner 和回答编排器可改善语言理解与解释，但所有运营事实和决策仍受下述工具、Schema、政策、授权和安全 Harness 约束。

## 运行时职责

| Component | Production responsibility | MVP status |
|---|---|---|
| Model | Extract intent/slots, propose a typed next action, summarize tool evidence, and produce user-facing language | 默认禁用；获批环境变量配置后仅可做合成数据试验，失败回退确定性路径 |
| Planner | Select `ask_user`, `call_tool`, `respond`, or `handoff` within a typed action schema | Rule-based routing only |
| Tool use | Query approved merchant-scoped read models and create only approved, idempotent support requests | Controlled synthetic tools; simulated tickets only |
| Memory | Keep thread state, verified slots, tool summaries, and approved preferences in tenant scope | Synthetic sessions/checkpoints; no long-term customer profile |
| Harness | Enforce identity, tenant scope, schemas, allow-lists, risk routing, limits, auditability, and safe fallback | Core input/risk/step checks exist; production controls remain pending |

## 模型契约

The model may classify, extract slots, ask one necessary question, choose among registered actions, re-rank tool candidates using declared attributes, and compose an evidence-grounded answer. It must not:

- invent SKU, price, stock, shipment, policy, compatibility, order, or merchant facts;
- make refund, cancellation, inventory, address, payout, or permission decisions;
- issue raw SQL, HTTP requests, shell commands, or unvalidated tool arguments;
- expose hidden reasoning, secrets, full personal data, or another tenant's records.

The model receives minimized, role-scoped context and summarized prior tool results. It returns a schema-validated action; internal reasoning is neither requested nor persisted as customer-visible trace data.

## Planner 与循环

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

每轮只接受一个动作。`tool_name` 必须在注册白名单中，API 入参和模型动作均须经过本地校验。生产目标中的循环是：

```text
guard -> load scoped memory -> plan -> tool/ask/handoff -> validate -> plan or compose -> persist trace
```

当前 Graph 每次请求只运行一次工具处理链，跨轮通过会话状态延续；同请求的反复 replan 是生产目标。Harness 已对高风险、越权和无法校验请求安全降级；完整的超时、重复失败与最大步数编排须在后续实现并评测。

## 受控工具

| Tool family | Required proof before response | Authority |
|---|---|---|
| Product search and recommendation | Tenant catalogue records, source label, effective price/availability timestamp | Read-only |
| Compatibility | Registered compatibility rule/version plus product/device fields | Read-only decision support |
| Policy | Effective policy version, region and applicability | Read-only |
| Order and shipment | Tenant scope, order identifier, required ownership check | Read-only, minimized output |
| Support ticket | Valid idempotency key and approved handoff reason | Controlled write; no commerce mutation |

Future Shopify/ERP/OMS adapters query a tenant-local, read-only projection, never arbitrary merchant database credentials. See [PRODUCTION_MERCHANT_DATA.md](../integration/PRODUCTION_MERCHANT_DATA.md).

## 记忆与 Trace 契约

Short-term memory may contain a `thread_id`, verified slots, concise message summaries, tool references, risk state, and retry/step counters. Long-term preferences require explicit user confirmation. Attachments, raw secrets, full identity data, and hidden model reasoning are not placed in prompts, checkpoints, or logs.

Every operation records request/thread/tenant identifiers, action and tool names, schema-safe parameters, evidence references, policy/prompt/model versions where applicable, timing, status, and reason codes. Audit records are tenant-scoped and retention-controlled.

## 生产激活前的 Harness 要求

1. OIDC authentication with organization, membership, and role mapping; a Widget visitor never receives staff permissions.
2. PostgreSQL row-level tenant isolation, encrypted secrets, rate limits, idempotency locks, tool timeouts, retries, circuit breakers, and alerting.
3. Prompt-injection defenses for text/OCR, attachment scanning and consent controls, and no unrestricted browser/model tool access.
4. Approval gates for any new write capability; refunds, cancellations, inventory changes, and address changes remain disabled unless separately designed and approved.
5. Evaluation gates defined in [评测规范.md](../agent评测/评测规范.md), red-team tests, security review, sandbox connector verification, and rollback drills.
