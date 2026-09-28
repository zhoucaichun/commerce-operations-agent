---
name: commerce-agent-session
description: 在独立 Codex 会话中实现和交付 3C Commerce Operations Agent。适用于 3C 项目的代码、API、Agent、评测、部署和文档工作。
---

# 3C Agent 会话 Skill

> 独立仓库说明：本 Skill 在 `agent-repos/commerce-operations-agent` 中执行。跨项目约定需要回看 AIPM，但项目代码、测试和项目文档只写入本仓库。

## 目标

将独立 GitLab 仓库 `commerce-operations-agent` 交付为可运行、可测试、可部署、可回滚的 Commerce Operations Agent MVP。只处理 3C 项目，不修改 Enterprise Agent 或 NutriChat 的业务代码、数据和环境变量。

## 开始工作前的读取顺序

必须按以下顺序读取，不能跳过：

1. 当前仓库根目录 `AGENTS.md`
2. 当前仓库根目录 `README.md`
3. `docs/PRD.md`
4. `docs/技术架构.md`
5. 读取当前仓库 `src/`、`tests/`、Git 状态、远程仓库和分支状态；需要跨项目约定时，再回看 AIPM 的排期和部署手册

读取后先用简短文字确认：当前已有内容、缺少的工程目录、与 PRD/技术架构的差距、当前分支和是否存在未提交改动。不要因为发现旧代码或删除状态就擅自恢复、重置或删除文件。

## 实施顺序

1. 在当前仓库 `src/` 下建立或修正 `frontend/`、`backend/`、`eval/`、`infra/`，并更新根目录 `README.md`；缺少目录时可以创建。
2. 先完成 FastAPI、Pydantic Schema、Request ID、健康检查、日志脱敏、数据库迁移和 Redis 接入。
3. 导入脱敏模拟的 `products`、`policies`、`orders`、`shipments` 种子数据。
4. 实现 Commerce Graph：输入校验 → 读取会话状态 → Planner → 受控工具 → 工具结果校验 → 答复或人工接管 → Checkpoint/Trace。
5. 实现五类受控工具：商品查询、兼容性校验、政策检索、订单/物流查询、模拟工单创建。
6. 跑通两条主链路：售前兼容性判断；订单异常查询并转人工。
7. 补齐权限、订单号与身份后缀校验、工具超时、有限重试、最大 6 步、错误降级和工单幂等写入。
8. 建立核心/泛化/badcase/订单/物流/售后评测，记录真实运行结果，不预填指标。
9. 建立独立 Compose、网关配置、迁移/种子命令、健康检查、冒烟测试和回滚说明。

## 不可违反的边界

- 首版不接入真实商家生产系统，不扣库存、不退款、不取消订单、不改地址。
- 模型不能覆盖兼容性规则、订单权限或政策工具结果。
- 首版唯一写操作是带 `idempotency_key` 的模拟工单创建。
- 模型 Key、数据库密码、JWT Secret、真实用户数据和生产日志不得写入仓库。
- 只能修改 3C 项目目录；公共契约确需变化时，先说明影响，再修改排期或部署文档，不改其他项目业务代码。

## 完成前检查

- `frontend` 能访问并调用 FastAPI，而不是客户端直连 Dify。
- `/health` 和 `/ready` 可用，数据库迁移和种子命令可重复执行。
- 6 步限制、工具失败降级、人工接管和工单幂等测试通过。
- Trace 至少关联 `request_id`、`thread_id`、模型/Prompt 版本、工具耗时和错误码，并完成脱敏。
- README 写明启动、测试、评测、部署、回滚、模拟范围和已知边界。

## 交付汇报格式

结束时汇报：已完成、验证命令及结果、未完成、阻塞项、对其他项目的影响、下一会话可直接继续的入口。不要把“文档写了”当作“功能已实现”。
