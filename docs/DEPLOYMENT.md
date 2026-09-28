# 本地部署与回滚

## Compose 启动

```powershell
docker compose -p commerce-agent -f src/infra/docker-compose.yml up --build -d
Invoke-WebRequest http://127.0.0.1:8000/health
Invoke-WebRequest http://127.0.0.1:8000/ready
```

该 Compose 使用独立的 `commerce-agent` 项目名、卷和网络命名空间。PostgreSQL 与 Redis 容器仅提供后续生产适配基础；当前 Agent 的运行时持久化仍使用 API 容器卷中的 SQLite，不能宣称已完成 PostgreSQL/Redis 业务读写。

容器中的默认 PostgreSQL 密码仅限本地演示，不能用于部署，也不得提交真实密钥。

## 回滚

```powershell
docker compose -p commerce-agent -f src/infra/docker-compose.yml down
docker compose -p commerce-agent -f src/infra/docker-compose.yml up -d --no-build
```

`down` 不带 `-v`，因此保留本地模拟数据卷。删除卷是破坏性操作，必须在确认不需要恢复模拟状态后单独执行。
