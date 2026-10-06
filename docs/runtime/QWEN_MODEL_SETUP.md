# Qwen 配置兼容入口

更新：2026-10-06。历史 PowerShell 临时变量只影响那个窗口的子进程，不是永久配置。现在聊天与向量模型全部维护在后端未跟踪的 `src/backend/.env`，不要再分别维护多份密钥。

完整字段、模型候选、启动入口和 Compose 读取方式见 [模型选型与统一配置](模型选型与统一配置.md)。

默认离线验收：`python src/eval/run_project_checks.py`。
显式联网小批检查：`python src/eval/run_project_checks.py --live --limit 3`。
完整 Agent 联网开发集：`python src/eval/run_agent_eval.py --live --report reports/model/agent-live.json`。

用户本机聊天探测已返回成功；这不等于本助手执行环境可访问同一网关，更不等于全部 Agent 任务已通过模型质量验收。密钥不得发聊天、写截图或提交仓库。
