# 本地部署与回滚

## 当前 Compose 验证

Compose 通过 `COMMERCE_POSTGRES_DSN` 让 API 使用 PostgreSQL 保存合成会话、工单、指标、商品、政策和订单。Redis 提供就绪检查、固定窗口限流、短时幂等锁、合成会话检查点和只读工具/请求的重试计数。启动后使用 `python src/eval/run_compose_smoke.py --restart-api` 验证商品、政策、订单种子和模拟工单跨 API 重启仍可用；它不会连接真实商家系统。

## Compose 启动

```powershell
docker compose --env-file src/backend/.env -p commerce-agent -f src/infra/docker-compose.yml up --build -d
Invoke-WebRequest http://127.0.0.1:8000/health
Invoke-WebRequest http://127.0.0.1:8000/ready
```

该 Compose 使用独立的 `commerce-agent` 项目名、卷和网络命名空间。直接运行 API 时仍默认使用内存/SQLite；但 Compose 模式已使用 PostgreSQL/Redis 处理上述**合成 MVP**状态。它不等同于生产级租户 RLS、真实商家连接器或真实业务数据读写。

容器中的默认 PostgreSQL 密码仅限本地演示，不能用于部署，也不得提交真实密钥。

## 回滚

```powershell
docker compose -p commerce-agent -f src/infra/docker-compose.yml down
docker compose -p commerce-agent -f src/infra/docker-compose.yml up -d --no-build
```

`down` 不带 `-v`，因此保留本地模拟数据卷。删除卷是破坏性操作，必须在确认不需要恢复模拟状态后单独执行。
