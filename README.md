# Commerce Operations Agent

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
