# Dify 迁移边界

## 决策

`ShopPilot Commerce Agent` 是 ShopPilot 3C Store 的运行时所有者。Dify 仅保留为已审查的历史工作流、迁移来源和后续回归参考；Store Widget 与从店铺进入的完整对话页均不依赖 Dify。

## 已迁移资产

| 来源 | 仓库内目标位置 | 运行时用途 |
|---|---|---|
| Dify DSL 导出 | `docs/dify/` | 仅供追溯，不含密钥，也不会发起 API 调用 |
| 55 条合成商品 | `src/backend/commerce_agent/data/dify_product_catalog.csv` | 确定性搜索、推荐与兼容性证据 |
| 35 条合成政策 | `src/backend/commerce_agent/data/dify_policy_catalog.csv` | 地区/主题政策证据 |
| 100 条全量 + 30 条 + 15 条回归提示 | `src/eval/data/dify_eval_*.csv` | 后续评测扩展的来源 |

`catalog_loader.py` 将源表头规范化为受控工具 Schema。内存 MVP 还保留三条历史安全测试商品和两条历史政策；运行时另有扩展的合成目录，不能把早期 58 条商品、37 条政策的统计口径当作当前完整语料规模。

## 意图和槽位对应关系

| 历史 Dify 分支 | Commerce Agent 路径 |
|---|---|
| 推荐 / 预算 / 候选排序 | 以设备、国家、预算、品类和用途约束调用 `recommend_products` |
| 兼容性 | 以目录声明和功率/接口兜底规则调用 `compatibility_check` |
| 政策 / 商品可售性 | 以主题、地区、版本元数据过滤调用 `policy_search` |
| 直接高风险转人工 | 输入防护与模拟工单/人工接管路径 |
| 澄清 | 已验证信息缺失时返回 `needs_input` |

当前 MVP 使用确定性规则，因此答复受仓库内合成记录约束；不得声称真实价格、库存、Shopify 可售性、配送数据，也不得执行商家操作。
