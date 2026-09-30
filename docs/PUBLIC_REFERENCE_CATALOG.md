# 公开参考商品目录

演示租户同时包含两种完全不同的数据：原 3C 项目迁入的合成 ShopPilot 商品目录，以及 `src/backend/commerce_agent/data/public_reference_catalog.csv` 中的公开参考条目。

公开条目只用于让演示数据的型号、功率与价格形态更贴近真实市场；每一条都保留厂家公开集合页 URL 和 `source_checked_at` 日期。它们不是抓取任务、没有实时同步、没有库存含义，也不代表 Anker 或 Belkin 已授权成为 ShopPilot 商家。

运行时约束：

- `source=public_reference_catalog`；`stock=not_connected`。
- 推荐排序默认降低公开参考条目的权重；ShopPilot 合成商品仍是默认演示商家目录。
- 前端结果会提示公开参考数据不是商家实时价格或库存。
- 任何实际商家接入必须走 `docs/PRODUCTION_MERCHANT_DATA.md` 的审批、OAuth/只读同步、租户隔离和审计流程，不能用网页抓取替代。

截至 2026-09-30，参考来源为 [Anker 20W chargers](https://www.anker.com/collections/20w-charger)、[Anker USB-C cables](https://www.anker.com/collections/usb-c-to-usb-c-cable) 和 [Belkin MagSafe chargers](https://www.belkin.com/products/wireless-chargers/magsafe-chargers-accessories/)。价格可能已变化，不能作为报价依据。
