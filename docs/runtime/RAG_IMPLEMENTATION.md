# ShopPilot 3C RAG 实现说明

## 结论与范围

本项目现在具备可运行的、可审计的本地 RAG 链路，用于政策、FAQ 与商品说明类知识问答。它不是把结构化商品筛选改成向量搜索：SKU、价格、库存、订单和兼容性结论仍必须由受控结构化工具或规则提供事实。

数据全部是仓库内的合成数据。既不连接 Shopify、ERP、真实商家知识库，也不宣称有真实库存或时效性。

## 当前执行链路

```text
合成商品/政策数据 + 合成 FAQ
  -> KnowledgeDocument（来源、版本、地区、主题、有效期元数据）
  -> 560 字符切分，80 字符重叠
  -> 本地 Hashing Embedding 向量 + BM25 词法索引
  -> 元数据硬过滤（kind / region / effective_from）
  -> 向量、BM25、标题命中融合重排
  -> cited chunks（document_id / chunk_id / source / version）
  -> policy_search / knowledge_search 受控工具
  -> 仅基于命中证据的回答，或转人工
  -> tool summary + Agent trace
```

对应实现：

- `src/backend/commerce_agent/rag.py`：文档模型、切分、向量化、混合召回、重排和引用。
- `src/backend/commerce_agent/synthetic_catalog.py`：216 条可复现的合成 3C 商品记录；与原 Dify 迁移商品共同构成约 278 条本地商品数据。
- `src/backend/commerce_agent/tools.py`：`policy_search` 和 `knowledge_search`。
- `tests/test_rag_pipeline.py`：语料规模、地区过滤、无证据拒答、引用进入 Trace 的回归测试。

## 为什么本地向量不是生产 Embedding

`HashingEmbedder` 是无需网络、稳定可复现的特征哈希向量器。它使本地开发、单元测试和评测可以真实运行“切分 → 向量检索 → 融合排序”的完整链路，但不应被描述成生产级语义 Embedding。

生产替换必须在数据授权后完成：选定 Embedding 模型，批量建向量，保存模型与数据版本，并用 PostgreSQL + pgvector（或经审批的向量库）持久化。替换前后必须同时跑检索专项集，比较 Recall@k、MRR、nDCG、证据充分性和端到端任务完成率；不能只看最终回答是否通顺。

## 路由边界

| 问题 | 事实源 | 是否使用 RAG |
| --- | --- | --- |
| “美国标准配送多久？” | 政策文档 | 是，地区/版本过滤后检索并引用 |
| “SKU005 是否兼容 MacBook Air M2？” | 兼容规则 + SKU 结构化属性 | 否，不能由相似文本替代规则 |
| “预算 25 美元推荐充电器” | 结构化目录、地区、预算筛选 | 否；RAG 只能补充说明，不能生成价格/库存 |
| “订单 ORD-10023 在哪里？” | 经身份校验的订单工具 | 否 |

## 从原 Dify 的迁移关系

原 `跨境3c项目` 的 Dify 工作流已经有商品/政策知识库、Embedding、Knowledge Retrieval 与“仅据召回内容回答”的约束。本实现保留这四项原则，并补充了可测试的引用、版本、地区过滤及 Trace；同时不修改原项目。

## 下一步：扩展评测顺序

1. 已冻结 V1 检索金标集：11 条 query、允许地区、目标 document 与不可回答样本；运行 `python src/eval/run_rag_eval.py` 可计算 Recall@4、MRR@4、过滤正确率和空证据行为。
2. 扩展金标集的地区、主题、版本冲突、同义改写和多文档场景，并补充 nDCG 与重排消融。
3. 在 Agent 端评估证据忠实性、引用正确性、回答相关性、任务完成率和延迟/成本；语义指标须通过人工校准，而非只用模型裁判。
4. 当接入批准的真实 Embedding 与 pgvector 后，冻结相同数据集做版本对比；线上数据必须完成脱敏、授权与租户隔离后才能进入评测闭环。
