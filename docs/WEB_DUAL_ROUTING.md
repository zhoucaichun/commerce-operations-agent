# ShopPilot Web dual-routing plan

`src/web` is a source-only copy of the existing ShopPilot 3C Next.js frontend. The original AIPM frontend is not edited by this repository.

## Route ownership

| User intent | Web route | Backend owner |
|---|---|---|
| Product discovery and open-ended recommendation | `/api/dify/chat` | Existing Dify workflow |
| Order, shipment, policy evidence, compatibility decision, or human handoff | `/api/agent/chat` | Commerce Agent FastAPI API |

The new `/api/agent/chat` Next.js route is a server-side proxy. It reads `COMMERCE_AGENT_API_BASE_URL` and optional synthetic-only `COMMERCE_AGENT_DEMO_TOKEN` from deployment environment variables; browser code never sees a token or calls the agent directly.

## Integration sequence

1. Keep the existing home page, start form, recommendation cards, and Dify route unchanged.
2. Add intent routing in the copied chat page: recommendation questions remain on Dify; operations questions use `/api/agent/chat`.
3. Render Agent results as order, policy, handoff, and simulated-ticket cards within the existing chat visual system.
4. Deploy the copied frontend only after an approved HTTPS endpoint is configured for the synthetic Commerce Agent.

No route is allowed to invoke a real merchant production system or perform inventory, refund, cancellation, or address mutations.
