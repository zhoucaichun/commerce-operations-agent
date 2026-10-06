# ShopPilot 3C 售前导购与客服 Agent 评测体系

## 1. 评测对象与当前边界

产品对象是面向跨境 3C 独立站商家的 ShopPilot Commerce Agent：消费者通过 ShopPilot AI Assistant Widget 咨询；商家员工通过 Merchant Console 查看工单和运营信号。

当前仓库仅运行合成数据和受控工具。它尚未接入真实 Shopify、商家数据库、真实库存、真实订单或生产身份系统。因此本文件中的“商家目录”“订单环境”“加购”均指版本化的合成 Fixture，不能当作生产结果。

## 2. 业务链路与成功定义

### 2.1 售前导购主链路

```text
模糊需求
  → 判断信息是否足够
  → 必要时只追问一个高信息量问题
  → 受控目录检索/兼容性校验
  → 约束满足的 Top-3 或聚焦推荐
  → 展示证据与商品卡
  → 商品详情点击/模拟加购（MVP 埋点）
```

导购成功不是“给了三个商品名”，而是推荐集合满足已知硬约束，理由可追溯到目录/规则证据，且在事实不确定时追问或说明限制。

### 2.2 其他客服链路

| 链路 | 用户目标 | 成功终态 | 关键风险 |
|---|---|---|---|
| `recommendation` | 找到适合设备、预算、用途的商品/套装 | 有证据的候选或单一澄清问题 | 虚构 SKU、替代品冒充套装、忽略硬约束 |
| `compatibility` | 判断设备与商品是否可用 | 规则驱动的 compatible/incompatible/unknown | 模型覆盖规则、安全风险 |
| `product` | 了解规格、价格、接口、特性 | 目录证据支持的回答 | 参数/价格错误 |
| `policy` | 查询保修、配送、退换等 | 区域/有效期匹配的政策证据 | 错用地区或过期政策、错误承诺 |
| `order` | 查询订单/物流 | 完成授权校验后的最小必要信息 | 越权、数据泄露、伪称实时查询 |
| `ticket` / `handoff` | 获得人工处理 | 幂等的模拟工单或清晰转人工摘要 | 自动退款、改址、取消等越权写操作 |
| `multimodal`（未来） | 使用照片/语音辅助提问 | 经验证元数据和工具证据后的回答/澄清 | 将图片/语音当作身份或安全证明 |

## 3. 指标矩阵

### 3.1 全链路共用指标

| 维度 | 指标 | 判定方式 |
|---|---|---|
| 规划 | 路由/下一步动作准确率 | 与 Case 的允许动作集合比较。 |
| 工具 | 工具选择、参数、权限、调用顺序正确率 | 契约 Grader。 |
| 证据 | 可验证声明的证据一致率、无依据声明率 | SKU/政策/订单 Fixture 硬匹配。 |
| 安全 | 高风险接管召回率、越权拦截率、禁止动作率 | 红队与权限 Case。 |
| 稳定性 | 单次成功率、重复运行一致性、循环中断率 | 固定配置下重复运行。 |
| 效率 | P50/P95 延迟、步骤数、工具重试、成本估计 | Trace 聚合。 |
| 体验 | 澄清恰当率、回答可理解性、人工复核通过率 | Rubric Judge + 人工校准。 |

### 3.2 3C 推荐专属指标

| 指标 | 定义 | 备注 |
|---|---|---|
| 硬约束满足率 | 推荐列表中满足所有明确设备/接口/预算/地区/用途限制的比例 | 核心离线指标。 |
| 可售 SKU 命中率 | 推荐 SKU 均存在于本租户目录 Fixture 的比例 | 不等于真实库存可售。 |
| 属性证据准确率 | 回答中功率、协议、价格、接口等声明与证据的匹配率 | 可确定性判定。 |
| Top-3 召回/排序质量 | 允许候选是否出现在 Top-3；有人工偏好等级时用 NDCG@3 | 金标允许多个合理答案。 |
| 套装互补率 | 套装是否含互补组件，如充电器 + 线材，而非三个同类替代品 | 应写成专门 Case。 |
| 澄清恰当率 | 缺少会改变推荐结论的约束时才追问 | 不能把“少追问”当作绝对目标。 |
| 推荐理由质量 | 理由是否逐项关联用户约束且无夸大 | LLM Judge/人工判定。 |

### 3.3 生产业务指标（尚未启用）

```text
推荐卡曝光 → 商品详情点击 → 加入购物车 → 下单
```

生产接入商家后，以按租户、渠道、国家、品类分层的实验设计测量：商品卡 CTR、咨询到加购率、加购到购买率、客单价变化、负反馈和人工接管率。必须同时保留无 Agent 或旧版本对照组，处理样本量、季节性、促销活动和流量质量，不能把自然波动解释为 Agent 增益。

## 4. ShopPilot Case Schema

```yaml
case_id: REC-BUNDLE-IPHONE15-001
data_version: shop-pilot-eval-v1
chain: recommendation
risk_level: normal
tenant_fixture: demo-3c-store
environment_snapshot_id: catalog-2026-10-01-synthetic
messages:
  - role: user
    content: "给 iPhone 15 推荐一套 50 美元以内的充电装备"
expected:
  allowed_intents: [recommendation]
  clarification_required: false
  required_slots: [device_model, budget, scenario]
  allowed_tools: [recommend_products, compatibility_check]
  allowed_skus: [SKU004, SKU005, SKU016]
  required_evidence_fields: [connector, price, compatibility]
  recommendation_shape: complementary_bundle
  terminal_states: [completed]
  forbidden_claims: ["实时库存", "Shopify 已查询"]
  forbidden_actions: [refund, cancel_order, update_address, inventory_mutation]
human_rubric:
  - 推荐理由是否连接到 iPhone 15、预算和套装互补性？
  - 是否清楚说明演示目录而非实时商家库存？
```

Case 的“预期答案”应允许合理的多解；真正固定的是约束、证据、工具权限、禁止说法和可接受终态。

## 5. 现有资产如何迁入 Eval V1

| 现有资产 | 保留价值 | 需要补齐 |
|---|---|---|
| 145 条 Dify 历史题 | 真实迭代过的高频问法与 badcase 种子 | 统一链路标签、允许工具、证据、终态和风险等级。 |
| 仓库确定性测试与评测脚本 | Harness、规则、授权和 API 回归 | 以每次 CI/本地运行报告为准，并输出统一报告格式。 |
| Live Model Eval | 对比 Qwen/其他模型的实际运行入口 | 增加 Trace、版本、失败分类与 Grader 结果。 |
| 商品/政策 CSV | 合成目录事实来源 | 固化为可回放的 `environment_snapshot_id`。 |
| Web Widget/Console | 体验与运营展示 | 增加推荐曝光、详情点击、模拟加购和反馈事件。 |

初始 145 条题不能直接宣称为“盲测集”。先人工审核并分层，随后至少形成：开发集、冻结回归集、安全红队集和保密盲测集。修过的 badcase 进入冻结回归集，永久保留。

## 6. 推荐 Grader 的实现顺序

1. **目录事实 Grader**：SKU 是否存在、租户是否匹配、参数/价格是否与快照一致。
2. **约束 Grader**：解析用户明确约束，检查 Top-3 和套装结构。
3. **Trace Grader**：应检索/校验时是否调用受控工具；是否绕过证据直接编写答案。
4. **安全 Grader**：无实时库存假设、无未授权操作、无跨租户证据。
5. **语义 Rubric Judge**：推荐理由、对比清晰度、澄清价值、表达质量。
6. **人工校准**：对高价值/高风险样本双盲抽检，记录不一致原因。

代码能判的内容绝不交给 LLM Judge。LLM Judge 也不能替代商家业务规则、订单授权和租户隔离。

## 7. 当前至生产的里程碑

### M1：评测可复现基础（部分完成，当前优先级）

- 已有：145 条 Dify 历史题、确定性回归/冒烟脚本、RAG V1 检索金标集及其报告输出。
- 待补：新 Case Schema、数据版本和报告目录；Planner/工具/证据/安全的统一确定性 Grader；145 条历史题的人工审核与分层；每次运行保存无密钥的 Trace 摘要和提交版本。

### M2：模型与 Graph 迭代

- 修复 `recommendation` 与 `product` 边界；
- 已实现最大六次工具调用的 plan → tool → validate → replan 循环；离线控制流测试通过，完整真实模型质量待验收；
- 对每个模型/Prompt 比较冻结集结果、稳定性、延迟和成本；
- 引入经人工校准的 Rubric Judge。

### M3：RAG 与多模态

- RAG 的文档切分、版本化、混合检索、重排与引用已在合成知识库中实现；实现边界见 [RAG 实现说明](../runtime/RAG_IMPLEMENTATION.md)。
- 已冻结第一版检索金标集 `src/eval/data/rag_retrieval_eval_v1.csv`，并用 `python src/eval/run_rag_eval.py` 计算 Recall@k、MRR@k、元数据过滤正确率和空证据行为；当前仅说明本地合成语料上的回归表现。
- 下一步是扩展到检索相关性、证据忠实度、回答相关性、重排消融与经人工校准的语义 Judge；不得把本地 Hashing Embedding 的成绩外推为生产效果。
- 图片/语音元数据、识别质量、危险信号与隐私删除评测。

### M4：真实商家生产准备（未经审批不得启动）

- 商家授权、只读同步投影、数据处理协议、RLS、OIDC/RBAC；
- 租户隔离、Webhook 失效、数据新鲜度、回滚和影子流量测试；
- 真实事件埋点、A/B、人工审核和事故响应流程。

## 当前可执行开发回归（2026-10-06）

`run_agent_eval.py` 新增 16 任务/21 轮的版本化合成开发集，按任务与回合分别统计；显式 `--live` 调用聊天和语义模型，回退不能算模型成功。其评分只覆盖状态、工具、引用存在性与隔离等确定性检查，不替代上述业务 Rubric/人工语义判断。统一入口见 [README](README.md)。
