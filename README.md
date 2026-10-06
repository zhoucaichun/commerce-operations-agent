# ShopPilot Commerce Operations Agent

面向跨境 3C 独立站的可运行 Agent MVP。它覆盖商品推荐、兼容性判断、政策检索、经校验的合成订单/物流查询，以及模拟人工工单；所有数据、商家、订单和指标均为仓库内合成数据。

## 当前实现（2026-10）

- **运行时**：真实 LangGraph 受控循环：校验→记忆→模型规划→工具→结果验证→再次规划→答复/追问/接管→持久化。最多六次工具调用，重复动作接管；已支持跨轮补充与约束覆盖。
- **受控工具**：商品搜索与推荐、兼容性规则、政策检索、知识检索、订单/物流查询、带幂等键的模拟工单。退款、取消订单、地址修改、库存修改和任何真实商家写操作均未启用。
- **数据与 RAG**：278 条合成商品、37 条合成政策与 FAQ；配置后使用语义 Embedding + BM25、元数据过滤和引用；离线评测明确使用 Hashing 基线。向量缓存可保存到 SQLite，向量索引在内存，不是 pgvector/神经 Reranker。
- **存储与部署**：本地直接运行默认使用内存/SQLite；Compose 运行时使用 PostgreSQL 保存合成会话、工单、指标、商品、政策和订单，并使用 Redis 提供就绪检查、限流、幂等锁和检查点辅助。两种模式都不连接真实商家系统。
- **体验入口**：`/store` 为合成店铺演示，`/widget` 为嵌入式 Widget 演示，`/console` 为商家 Console 演示。Dify 仅保留为历史工作流、迁移来源和评测参考，不在店铺运行时链路中。

## 快速开始

在仓库根目录执行：

```powershell
python src/backend/main.py
python src/eval/run_project_checks.py
```

API 默认地址为 `http://127.0.0.1:8000`，可查看 `/health`、`/ready`、`/metrics` 与 `/docs`。`POST /api/v1/chat` 当前返回 JSON，不是 SSE 流。

若要体验 Next.js 演示前端：

```powershell
cd src/web
npm run dev
```

打开 `http://127.0.0.1:3000/store`。Docker Compose 启动、检查与回滚见 [部署文档](docs/operations/DEPLOYMENT.md)。

## 模型评测边界

模型适配器默认禁用。以下命令仅校验本地合成数据，不产生网络调用：

```powershell
python src/eval/run_dify_model_eval.py --report reports/dify-model-eval-dry-run.json
```

聊天与向量模型统一填写 `src/backend/.env`（模板是同目录 `.env.example`）。`main:app` 启动 API 时加载；历史试验仅在 `--live` 时加载，默认不发送题目。实际聊天请求也会触发已配置模型。详情见 [模型选型与统一配置](docs/runtime/模型选型与统一配置.md)。聊天及向量接口已有单条连通记录；受控循环已实现，但全量真实模型+语义索引端到端验收尚未完成。密钥不得提交、写入截图或暴露给浏览器。

## 明确不在当前范围内

- 不接入真实 Shopify、ERP、OMS、WMS、CRM、客户、订单、库存或支付系统；
- 不启用真实 OIDC、生产 RLS、真实客服系统写入或真实库存/退款/取消/地址变更；
- 不把本地 RAG、合成评测通过或模型试验结果描述成真实商家生产质量。

## 文档入口

从 [docs/INDEX.md](docs/INDEX.md) 开始：

- [产品需求](docs/PRD.md)：用户结果、边界与产品验收目标；
- [技术架构](docs/技术架构.md)：当前实现、部署模式与生产目标；
- [RAG 实现](docs/runtime/RAG_IMPLEMENTATION.md)：本地混合 RAG 的事实源、限制与评测；
- [Agent 评测](docs/agent评测/README.md)：当前评测入口、企业方法、3C 指标与论文综述；
- [生产边界](docs/operations/PRODUCTION.md)：生产激活前不可省略的安全与运维条件。

当前首选入口是 `python src/eval/run_project_checks.py`：无网络单元/冒烟/任务/RAG 回归。新版任务集含 16 个开发任务、21 轮，不是盲测；旧 110 检查不是 110 个独立任务。联网小批用 `python src/eval/run_project_checks.py --live --limit 3`；完整任务集用 `run_agent_eval.py --live`。结果与待审批项见 [升级验收](docs/runtime/升级验收与待审批事项.md)，不使用旧简历数字。

部署到任何非合成环境前，必须运行 `python src/infra/validate_proxy_config.py --host <已批准域名>`，并遵循 [身份提供方设计](docs/operations/IDENTITY_PROVIDER_DESIGN.md) 与安全审批清单；本仓库不授予 OIDC 或真实商家系统接入权限。
