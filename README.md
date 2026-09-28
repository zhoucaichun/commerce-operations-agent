# Commerce Operations Agent

## Current delivery status

The runnable MVP uses FastAPI, PostgreSQL-backed synthetic state in Compose, Redis rate limiting/checkpoints/retry counters, and an explicit LangGraph `guard -> planner -> controlled tool -> validate -> handoff` orchestration. All product, policy, order and ticket data remain synthetic. No merchant production system, inventory mutation, refund, cancellation, or address change is connected or permitted.

Run local regression with `python -m unittest discover -s tests -p "test_*.py" -v` and `python src/eval/run_smoke.py`. For the isolated Compose integration check, start Compose and run `python src/eval/run_compose_smoke.py --restart-api`.

## Web interface

Open `http://127.0.0.1:8000/` after starting the API or Compose stack. The bundled frontend provides safe chat, optional order ID/suffix fields, simulated-ticket idempotency input, synthetic-token input, tool summaries, and explicit handoff results. It only calls the same-origin `/api/v1/chat` API and has no direct merchant-system integration.

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

- 尚未接入 FastAPI/Pydantic、PostgreSQL/pgvector、Redis、LangGraph、LLM、Next.js、SSE、Docker Compose、迁移、CI 和完整评测集。
- 会话、工单和指标仅存于进程内，重启后丢失；尚无生产级鉴权、限流或多实例一致性。

## 安全边界

首版不连接真实商家系统，不扣库存、不退款、不取消真实订单、不修改真实地址。调用方不能绕过工具白名单、订单身份校验、幂等键或人工接管规则。

GitLab：`https://gitlab.com/zhoucaichun/commerce-operations-agent.git`

## FastAPI 与本地数据

当前 API 已升级为 FastAPI/Pydantic。启动：`python src/backend/main.py`；OpenAPI 文档：`/docs`。默认使用内存 SQLite；要保留会话、幂等工单和指标，请设置 `COMMERCE_DB_PATH` 到本机未提交的文件路径，或执行 `python src/backend/seed.py --database <路径>` 初始化本地库。

评测冒烟：`python src/eval/run_smoke.py`。该评测只覆盖模拟兼容性、模拟订单和高风险接管，不调用模型或真实商家系统。

## Compose 基础设施

已提供独立的 API、PostgreSQL 与 Redis Compose，见 `src/infra/docker-compose.yml`。启动、检查和回滚命令见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。当前 PostgreSQL/Redis 是部署基础设施，业务读写尚未迁移，运行时仍使用 SQLite；此边界已在部署文档中明确。

PostgreSQL/Redis 适配器现已可由 `COMMERCE_POSTGRES_DSN` 与 `COMMERCE_REDIS_URL` 启用；缺少驱动或依赖不可用时 `/ready` 会安全失败。当前工作环境未能完成驱动安装且 Docker 权限受限，因此尚未宣称 PostgreSQL/Redis 集成测试完成。
