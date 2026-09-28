# 技术决策记录

## 2026-09-28：先交付零依赖后端纵向切片

- 背景：仓库此前只有文档和目录占位；当前环境没有 FastAPI、Pydantic 或 pytest。
- 决定：先用 Python 标准库实现可运行的 HTTP 适配器、受控工具层、内存会话和测试。后续可替换为 FastAPI/Pydantic、PostgreSQL、Redis 和 LangGraph。
- 影响：本轮可验证健康检查、订单身份校验、模拟工单幂等和人工接管；状态不持久化，不能代表生产部署完成。
- 安全约束：所有数据都是 synthetic seed；不连接真实商家系统，不扣库存、不退款、不取消真实订单、不修改真实地址。
- 验证：`python -m unittest discover -s tests -p "test_*.py" -v` 与本地 HTTP 冒烟。
