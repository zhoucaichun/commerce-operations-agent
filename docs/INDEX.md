# ShopPilot Commerce Agent 文档索引

这里是本仓库的文档入口。顶层只保留产品总纲和本索引；其余文档按用途归档，避免把“已实现的 MVP”“设计中的生产能力”“历史迁移资料”混在一起。

## 先读什么

| 如果你想… | 从这里开始 |
|---|---|
| 了解产品卖给谁、解决什么问题、首版边界 | [PRD.md](PRD.md) |
| 了解前后端、Graph、数据和部署总体设计 | [技术架构.md](技术架构.md) |
| 本地体验 Store、Widget 与 Merchant Console | [产品与演示](product/DEMO_GUIDE.md) |
| 理解 Agent Runtime、Dify 迁移和模型边界 | [运行时与模型](runtime/AGENT_RUNTIME_SPEC.md) |
| 了解如何评测模型、工具、RAG 与 Agent | [Agent 评测](agent评测/README.md) |
| 部署、TLS、OIDC 或真实商家接入准备 | [运行与生产准备](operations/DEPLOYMENT.md) |

## 目录结构

```text
docs/
├─ INDEX.md                    # 本文件：总入口与阅读路线
├─ README.md                   # 兼容入口，指向 INDEX
├─ PRD.md                      # 产品需求总纲
├─ 技术架构.md                 # 技术架构总纲
├─ product/                    # 演示产品、页面路由、产品决策
├─ runtime/                    # Agent Runtime、Dify 工作流映射、模型与多模态
├─ integration/                # Dify 数据迁移、公开参考数据、商家数据接入设计
├─ agent评测/                  # 评测契约、企业评测流程、3C 指标、论文综述
├─ operations/                 # Compose、TLS、生产边界、OIDC 安全审批
└─ dify/                       # 只读 Dify DSL 导出，非运行时依赖
```

## 文件说明

### 产品与演示：`product/`

| 文件 | 说明 | 状态 |
|---|---|---|
| `B2B_DEMO_IMPLEMENTATION_PLAN.md` | Widget 与 Merchant Console 的合成多租户演示设计。 | MVP 演示已实现；不等于真实认证/RLS。 |
| `DEMO_GUIDE.md` | 启动、体验和验证 ShopPilot 演示链路。 | 当前可用。 |
| `DECISIONS.md` | 影响安全、架构与产品范围的决策记录。 | 持续维护。 |
| `WEB_DUAL_ROUTING.md` | Store Agent 与历史 Dify 对照页面的双路由边界。 | 当前可用。 |

### 运行时与模型：`runtime/`

| 文件 | 说明 | 状态 |
|---|---|---|
| `AGENT_RUNTIME_SPEC.md` | Model、Planner、Tool、Memory、Harness 的权威运行时契约。 | MVP 与生产目标均明确标注。 |
| `AGENT_PRODUCTION_IMPLEMENTATION.md` | 模型适配器、受控生成与生产激活前置条件。 | 模型连接可选；真实生产未激活。 |
| `DIFY_WORKFLOW_SPEC.md` | Dify 的提示词/节点/badcase 如何迁入 Agent。 | Dify 仅作参考和评测来源。 |
| `MULTIMODAL_MVP.md` | 图片/语音合成元数据 MVP 与安全边界。 | 不上传媒体、不调用视觉/语音模型。 |
| `QWEN_MODEL_SETUP.md` | OpenAI 兼容 Qwen 配置与合成数据评测方法。 | 仅本地环境变量启用。 |

### 集成与数据：`integration/`

| 文件 | 说明 | 状态 |
|---|---|---|
| `DIFY_MIGRATION.md` | Dify DSL、CSV 和历史评测题的审查迁移说明。 | 已迁入合成资料。 |
| `PUBLIC_REFERENCE_CATALOG.md` | 公开参考商品记录的时间、来源和非实时边界。 | 演示参考，不是商家库存。 |
| `PRODUCTION_MERCHANT_DATA.md` | Shopify/商家数据、OAuth、只读同步与租户隔离设计。 | 设计文档，未接入。 |

### Agent 评测：`agent评测/`

这是独立索引，包含当前评测契约、企业级流程、ShopPilot 3C 指标、论文和框架综述。见 [agent评测/README.md](agent评测/README.md)。

| 文件 | 说明 | 状态 |
|---|---|---|
| `评测规范.md` | 当前运行时的最小验收契约、安全门槛与回归闭环。 | 当前可用。 |

### 运行与生产准备：`operations/`

| 文件 | 说明 | 状态 |
|---|---|---|
| `DEPLOYMENT.md` | Docker Compose 启动、检查、回滚。 | 当前合成环境可用。 |
| `PRODUCTION.md` | TLS/Nginx、证书、密钥与生产运行手册。 | 生产准备设计；不是生产已上线。 |
| `IDENTITY_PROVIDER_DESIGN.md` | OIDC/RBAC 目标设计。 | 未接入真实身份提供方。 |
| `SECURITY_APPROVAL_CHECKLIST.md` | OIDC 沙箱/真实身份接入前的外部审批清单。 | 未批准前不可启动。 |

## 文档状态标记

- **当前可用**：仓库中已有对应实现和验证。
- **MVP 演示**：仅合成数据/角色/商家，用于产品体验。
- **设计文档**：描述生产目标与前置条件，不代表已实现或已获批准。
- **历史参考**：用于迁移、评测或追溯，不在当前运行时路径。

真实商家系统、真实库存、退款、取消订单、真实地址修改、真实 OIDC 与生产客户数据均不在当前启用范围内。
