# Commerce Operations Agent

3C Commerce Operations Agent 的独立项目仓库。该仓库是 3C 项目的代码、测试、部署配置和项目文档唯一工作区；总协调信息仍保留在 GitHub 的 AIPM 仓库。

## AI 开发入口

每次开始 Codex 会话时，按以下顺序读取：

1. `AGENTS.md`
2. `skills/commerce-agent-session/SKILL.md`
3. `docs/PRD.md`
4. `docs/技术架构.md`
5. 当前 Git 状态、分支和远程仓库

先报告当前已有内容、缺口、风险和本次任务，再修改代码。只在本仓库内实现 3C 业务，不要把代码写回 AIPM 或其他项目仓库。

## 目录约定

```text
.
├── docs/                 # PRD、架构、决策和验收记录
├── skills/               # 本项目 Codex 会话 Skill
├── src/                  # 应用实现；按 frontend/backend/eval/infra 分层
├── tests/                # 单元、集成、契约、冒烟和 badcase 测试
├── AGENTS.md             # AI 开发边界与交付规则
├── CHANGELOG.md          # 可验证的变更记录
└── README.md             # 启动、测试、评估、部署和回滚说明
```

实现需要遵循 `docs/技术架构.md` 中的 frontend、backend、eval、infra 分层；如果实际采用独立顶层目录，应在本次提交的 README 中说明映射关系。

## 当前状态

当前仓库以产品文档和工程骨架为主，尚未声称 MVP 已实现。每次完成任务后更新 README 的“当前状态”、测试命令和已知边界，并在 `CHANGELOG.md` 记录真实结果。

## Git 归属

远程仓库：`https://gitlab.com/zhoucaichun/commerce-operations-agent.git`

本仓库的提交只推送到上述 GitLab 项目。AIPM GitHub 仓库只负责三项目排期、共用基础设施和协作规则。
