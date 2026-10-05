# 技术决策记录

## 2026-09-28：先交付零依赖后端纵向切片

- 背景：仓库此前只有文档和目录占位；当前环境没有 FastAPI、Pydantic 或 pytest。
- 决定：先用 Python 标准库实现可运行的 HTTP 适配器、受控工具层、内存会话和测试。后续可替换为 FastAPI/Pydantic、PostgreSQL、Redis 和 LangGraph。
- 影响：本轮可验证健康检查、订单身份校验、模拟工单幂等和人工接管；状态不持久化，不能代表生产部署完成。
- 安全约束：所有数据都是 synthetic seed；不连接真实商家系统，不扣库存、不退款、不取消真实订单、不修改真实地址。
- 验证：`python -m unittest discover -s tests -p "test_*.py" -v` 与本地 HTTP 冒烟。

## 2026-09-28：以 FastAPI/Pydantic 和 SQLite 推进可验证后端

- 决定：采用已安装的 FastAPI/Pydantic 作为 API 边界；以 SQLite 持久化会话、模拟工单和指标，并通过迁移文件初始化。
- 影响：本地可获得 OpenAPI、结构化请求校验、`request_id` 响应头和可选持久化；SQLite 不是 PostgreSQL/Redis 的等价替代，生产替换仍未完成。
- 验证：FastAPI API 测试覆盖健康、就绪、未知字段拒绝、风险接管和跨重启幂等。

## 2026-10：将合成 MVP 扩展为可复现运行时与本地 RAG

- 背景：前两条记录描述的是早期纵向切片，不能继续被误读为当前实现状态。
- 决定：保留本地直跑的内存/SQLite 模式，同时在 Compose 中启用 PostgreSQL 与 Redis；采用 LangGraph 单轮状态机、可选 OpenAI 兼容模型适配器，以及 Hashing Embedding + BM25 的本地混合 RAG。
- 影响：Compose 可持久化合成会话、工单、指标、目录、政策和订单；RAG 可执行检索、元数据过滤、重排、引用与离线专项评测。完整同请求多步 replan、生产 Embedding/pgvector、真实租户 RLS、真实连接器和 OIDC 仍未实现。
- 验证：`python -m unittest discover -s tests -p "test_*.py" -v`、`python src/eval/run_smoke.py`、`python src/eval/run_rag_eval.py` 与 Compose 冒烟脚本。
