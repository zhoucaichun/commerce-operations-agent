# ShopPilot functional MVP demo guide

## Start

Open two PowerShell terminals from the repository root.

```powershell
python src/backend/main.py
```

```powershell
cd src/web
node node_modules/next/dist/bin/next dev --port 3000
```

Open `http://127.0.0.1:3000/store`.

## What to demonstrate

1. Present `/store` as the simulated **ShopPilot 3C Store**. Open the lower-right assistant or Support entry; it opens the themed full chat and its back controls return to `/store`.
2. Ask: `I use an iPhone 15 and want a charger under $25`. Expected: an Agent response grounded in synthetic SKUs, not a Dify response.
3. Ask: `Will SKU005 work with MacBook Air M2?`. Expected: deterministic compatibility result with a tool summary.
4. Ask: `How long is standard shipping to US?`. Expected: a synthetic policy record and its source/date.
5. Ask: `Track ORD-10023, last four digits 4821`. Expected: a verified synthetic shipment result. Omit the last four digits to see safe `needs_input`.
6. Ask to refund, cancel, alter an address, or change inventory. Expected: no action, only a safe human handoff.
7. Open `/console` to show merchant-only views, and `/widget?merchant=demo-3c-store` to show the embed simulation. These are separate interfaces, not separate production logins yet.

## Scope reminder

The MVP is complete enough to experience its core front/back Agent flow. It is not a production activation: no real authentication, Shopify connector, merchant database, payment, order write, inventory write, refund, cancellation, or address change exists.
