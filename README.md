# Commerce Operations Agent

## Current delivery status

The runnable MVP uses FastAPI, PostgreSQL-backed synthetic state in Compose, Redis rate limiting/checkpoints/retry counters, and an explicit LangGraph `guard -> planner -> controlled tool -> validate -> handoff` orchestration. All product, policy, order and ticket data remain synthetic. No merchant production system, inventory mutation, refund, cancellation, or address change is connected or permitted.

Run local regression with `python -m unittest discover -s tests -p "test_*.py" -v` and `python src/eval/run_smoke.py`. For the isolated Compose integration check, start Compose and run `python src/eval/run_compose_smoke.py --restart-api`.

The Agent runtime now includes an optional OpenAI-compatible LLM Adapter for typed planning and evidence-grounded composition. It is disabled unless all `COMMERCE_LLM_BASE_URL`, `COMMERCE_LLM_API_KEY`, and `COMMERCE_LLM_MODEL` environment variables are configured; failures safely fall back to deterministic routing. The complete implementation/activation boundary is in `docs/AGENT_PRODUCTION_IMPLEMENTATION.md`.

Qwen is the recommended first text-model baseline for this MVP: it can use the existing OpenAI-compatible transport with an optional JSON Schema request while local validation remains authoritative. The migrated 145-case Dify dataset now has an opt-in model evaluation command: `python src/eval/run_dify_model_eval.py --report reports/dify-model-eval-dry-run.json` performs no network call; add `--live --limit 30` only after configuring an approved provider in the launching PowerShell session. See `docs/QWEN_MODEL_SETUP.md`; it also explains why product/order/policy tools remain deterministic and why voice/image need separate future adapters.

Copy `src/backend/.env.example` to an untracked local environment file and supply only an approved provider configuration when you are ready to evaluate a real model. Do not put a key in Git, the browser, Dify export, or frontend environment variables.

The synthetic evaluation now runs 30 deterministic cases. The web UI includes a read-only synthetic operations summary from `/metrics`, UTC hourly cumulative snapshots, synthetic order/ticket detail cards, and same-request retry for recoverable failures.

## Web interface

Preview the original Shopify-style ShopPilot 3C storefront mock at `/store`. Its floating assistant and Support entry open `/chat-demo?from=store`, which uses the same store theme and always returns to `/store`. Product art and catalog labels are synthetic; it does not connect to Shopify or change any real order.

The B2B product demonstration now exposes two deliberately different entries: `/widget?merchant=demo-3c-store` is a consumer-facing, embeddable Widget simulation, while `/console` is the merchant staff Console. Switch between the two synthetic merchants and roles to verify that orders, tickets, metrics and Widget configuration remain scoped to the selected merchant. The role selector is a demonstration aid, not OIDC or production authentication; see `docs/B2B_DEMO_IMPLEMENTATION_PLAN.md`.

The production-facing Next.js source baseline is in `src/web`. It is copied from the existing ShopPilot 3C frontend without modifying the AIPM source project. Store-originated conversations (`/chat-demo?from=store`) route every question, including recommendations, to the server-side `/api/agent/chat` proxy. The legacy Dify proxy remains only for comparison with the historical standalone page and is not in the ShopPilot Store customer flow; see `docs/DIFY_MIGRATION.md`.

## ShopPilot functional MVP route

The product names are fixed for the demo: `ShopPilot 3C Store` is the simulated merchant storefront, `ShopPilot AI Assistant` is its consumer-facing assistant, and `ShopPilot Commerce Agent Console` is the merchant employee interface. Start the FastAPI API, then start `src/web` on port 3000 and open `/store`. The assistant links to `/chat-demo?from=store`, which now uses the Agent for catalogue recommendation, compatibility, policy, verified synthetic order lookup, and safe handoff.

The Agent packages 55 reviewed synthetic products, 35 reviewed synthetic policies, 145 historical Dify evaluation prompts, three legacy safety-test products, and four dated public-reference demonstration records. It therefore has 62 product entries and 37 policy entries at runtime. These assets are not real Shopify, merchant, customer, order, or inventory data. Exact migration scope and the test script are in `docs/DIFY_MIGRATION.md` and `docs/DEMO_GUIDE.md`.

Store chat includes a synthetic multimodal MVP: demo photo and voice metadata are validated and normalized before the ordinary safety/tool chain. It does not upload media bytes or call a model provider; see `docs/MULTIMODAL_MVP.md`.

The floating Store Widget now supports direct text chat plus synthetic voice/photo demo actions. Its three starter prompts are shown only before the first message, then disappear to preserve space for the conversation. Its `thread_id` is passed into “Open full conversation”, so the full page continues the same server-side Agent state (not a private transcript export). Store-origin full chat disables the legacy static “Top 3 Recommendations” preview and displays only the matching structured recommendations returned by the Commerce Agent. The Store-origin full-chat composer uses a privacy-labelled pill with voice, attachment and camera actions; these still submit only synthetic demo metadata. `docs/PUBLIC_REFERENCE_CATALOG.md` documents a small dated public-reference catalogue; it is visibly non-live, never treated as merchant inventory, and does not replace the migrated synthetic ShopPilot catalogue.

Real merchant data integration is not implemented. The production Shopify/tenant database design and activation prerequisites are explicit in `docs/PRODUCTION_MERCHANT_DATA.md`; Dify is a workflow/evaluation reference, never the merchant data layer.

Open `http://127.0.0.1:8000/` after starting the API or Compose stack. The bundled frontend provides safe chat, optional order ID/suffix fields, simulated-ticket idempotency input, synthetic-token input, tool summaries, and explicit handoff results. It only calls the same-origin `/api/v1/chat` API and has no direct merchant-system integration.

The API sets CSP, `nosniff`, no-referrer and restrictive permissions headers. The UI explains authentication (401), permission (403), duplicate (409), validation (422), and rate-limit (429) responses without claiming that a real action occurred. Run browser E2E locally with `cd tests/e2e; npm ci; npm test` (Windows uses installed Edge; CI uses Playwright Chromium).

The UI supports native keyboard navigation, a skip link, visible focus, and Alt+1/Alt+2/Alt+3 presets. Production boundary and future OIDC design are documented in `docs/PRODUCTION.md` and `docs/IDENTITY_PROVIDER_DESIGN.md`; neither connects a real provider.

Before a production deployment, run `python src/infra/validate_proxy_config.py --host <approved-dns-name>` and follow the certificate rotation runbook in `docs/PRODUCTION.md`.

OIDC sandbox activation requires an external written security approval; use `docs/SECURITY_APPROVAL_CHECKLIST.md` as the required evidence checklist. This repository cannot grant that approval.

GitLab CI automatically runs fast regression/evaluation and an isolated PostgreSQL Repository suite. An optional manual Docker Compose smoke validates API-restart persistence; it requires a GitLab Runner that permits Docker-in-Docker privileged mode.

## Synthetic authentication

Local development is open by default. Set `COMMERCE_AUTH_REQUIRED=true` to require `Authorization: Bearer <synthetic-token>`, then supply `COMMERCE_DEMO_TOKENS` only through deployment/CI environment variables as a JSON map whose records contain `subject` and one of `viewer`, `support`, or `operator`. Do not commit a token map or real identity data. Viewers can use product/policy queries; order lookup and simulated ticket creation require `support` or `operator` and still require the existing order suffix/idempotency checks.

独立的 3C Commerce Operations Agent 仓库。本轮交付一个可本地运行、仅使用脱敏模拟数据的后端纵向切片；不连接真实商家生产系统。

## 当前实现

- `src/backend/commerce_agent/`：输入校验、内存会话、受控工具、确定性 Agent Loop、Trace 和人工接管。
- `src/backend/main.py`：标准库 HTTP 适配器，提供 `GET /health`、`GET /ready`、`GET /metrics` 和 `POST /api/v1/chat`。
- 受控工具：商品查询、兼容性校验、政策查询、订单/物流查询、带 `idempotency_key` 的模拟工单创建。
- 安全保护：订单查询必须同时提供订单号与脱敏身份后四位；退款、取消订单、真实地址或库存修改均直接人工接管；消息原文不写入 Trace。

## 启动与测试

在仓库根目录执行：

```powershell
python src/backend/main.py
python -m unittest discover -s tests -p "test_*.py" -v
```

示例请求：

```powershell
$body = @{ thread_id = "demo-thread"; message = "查订单 ORD-10023 物流，后四位 4821" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/v1/chat -Method Post -ContentType "application/json" -Body $body
```

已验证：6 个单元测试通过；`/health`、`/ready`、模拟订单查询和风险接管 HTTP 冒烟通过。所有订单、商品、政策与库存均为 synthetic seed，不代表真实信息。

## 已知未完成项

- 当前未接入 LLM Provider、pgvector/RAG、真实 Shopify/ERP/OMS/WMS/CRM 数据连接器、真实 OIDC 身份提供方或生产级 PostgreSQL 行级租户隔离。
- 当前商品、政策、订单、会话、工单和指标均为演示数据或演示状态；PostgreSQL/Redis/Compose、FastAPI、Next.js、LangGraph 状态机、CI 与确定性评测已经存在，但不等于生产激活。
- 当前评测覆盖确定性工具、安全链路和冒烟场景；模型质量、完整 badcase 回归集、人工标注与正式发布阈值尚待完成。
- 当前运行时/工作流/评测文档见 `docs/AGENT_RUNTIME_SPEC.md`、`docs/DIFY_WORKFLOW_SPEC.md`、`docs/EVALUATION_SPEC.md`：它们明确区分现有 MVP 与生产目标。

## 安全边界

首版不连接真实商家系统，不扣库存、不退款、不取消真实订单、不修改真实地址。调用方不能绕过工具白名单、订单身份校验、幂等键或人工接管规则。

GitLab：`https://gitlab.com/zhoucaichun/commerce-operations-agent.git`

## FastAPI 与本地数据

当前 API 已升级为 FastAPI/Pydantic。启动：`python src/backend/main.py`；OpenAPI 文档：`/docs`。默认使用内存 SQLite；要保留会话、幂等工单和指标，请设置 `COMMERCE_DB_PATH` 到本机未提交的文件路径，或执行 `python src/backend/seed.py --database <路径>` 初始化本地库。

评测冒烟：`python src/eval/run_smoke.py`。该评测只覆盖模拟兼容性、模拟订单和高风险接管，不调用模型或真实商家系统。

## Compose 基础设施

已提供独立的 API、PostgreSQL 与 Redis Compose，见 `src/infra/docker-compose.yml`。启动、检查和回滚命令见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。当前 PostgreSQL/Redis 是部署基础设施，业务读写尚未迁移，运行时仍使用 SQLite；此边界已在部署文档中明确。

PostgreSQL/Redis 适配器现已可由 `COMMERCE_POSTGRES_DSN` 与 `COMMERCE_REDIS_URL` 启用；缺少驱动或依赖不可用时 `/ready` 会安全失败。当前工作环境未能完成驱动安装且 Docker 权限受限，因此尚未宣称 PostgreSQL/Redis 集成测试完成。
