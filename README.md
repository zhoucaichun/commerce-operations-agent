# ShopPilot Commerce Operations Agent

面向跨境 3C 独立站的可运行 Agent MVP。它覆盖商品推荐、兼容性判断、政策检索、经校验的合成订单/物流查询，以及模拟人工工单；所有数据、商家、订单和指标均为仓库内合成数据。

## 当前实现（2026-10）

- **运行时**：FastAPI + LangGraph 状态机；当前 Graph 执行 `guard -> load_memory -> planner -> tool -> validate -> compose/handoff -> persist`。规划动作会控制接管分支，历史槽位会合并到当前请求；商品查询内部可追加一次知识检索，但任意工具链的同请求反复 replan 仍是生产强化项。
- **受控工具**：商品搜索与推荐、兼容性规则、政策检索、知识检索、订单/物流查询、带幂等键的模拟工单。退款、取消订单、地址修改、库存修改和任何真实商家写操作均未启用。
- **数据与 RAG**：运行时含 **278 条合成商品**、**37 条合成政策**和合成订单/工单 Fixture。本地 RAG 使用 Hashing Embedding + BM25、元数据过滤、融合重排及引用 Trace；它可复现，但不是生产级语义 Embedding 或 pgvector 部署。
- **存储与部署**：本地直接运行默认使用内存/SQLite；Compose 运行时使用 PostgreSQL 保存合成会话、工单、指标、商品、政策和订单，并使用 Redis 提供就绪检查、限流、幂等锁和检查点辅助。两种模式都不连接真实商家系统。
- **体验入口**：`/store` 为合成店铺演示，`/widget` 为嵌入式 Widget 演示，`/console` 为商家 Console 演示。Dify 仅保留为历史工作流、迁移来源和评测参考，不在店铺运行时链路中。

## 快速开始

在仓库根目录执行：

```powershell
python src/backend/main.py
python -m unittest discover -s tests -p "test_*.py" -v
python src/eval/run_smoke.py
python src/eval/run_rag_eval.py
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

只有在本机 PowerShell 显式配置获批的 `COMMERCE_LLM_BASE_URL`、`COMMERCE_LLM_API_KEY` 和 `COMMERCE_LLM_MODEL` 后，才可加 `--live` 对合成 Dify 题集做受控试验。详情见 [Qwen 模型配置与评测](docs/runtime/QWEN_MODEL_SETUP.md)。密钥不得提交、写入截图或暴露给浏览器。

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

当前评测必须区分“已实现回归”和“生产目标”：`python src/eval/run_evaluation.py` 是确定性合成场景检查，`python src/eval/run_rag_eval.py` 是 RAG 检索专项检查；二者都不能替代真实商家线上指标。

部署到任何非合成环境前，必须运行 `python src/infra/validate_proxy_config.py --host <已批准域名>`，并遵循 [身份提供方设计](docs/operations/IDENTITY_PROVIDER_DESIGN.md) 与安全审批清单；本仓库不授予 OIDC 或真实商家系统接入权限。
