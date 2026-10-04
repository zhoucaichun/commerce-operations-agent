# ShopPilot Web dual-routing plan

`src/web` is a source-only copy of the existing ShopPilot 3C Next.js frontend. The original AIPM frontend is not edited by this repository.

## Route ownership

| User intent | Web route | Backend owner |
|---|---|---|
| Product discovery and open-ended recommendation from ShopPilot Store | `/api/agent/chat` | Commerce Agent deterministic catalogue tool |
| Historical standalone recommendation comparison | `/api/dify/chat` | Existing Dify workflow; not the Store runtime |
| Order, shipment, policy evidence, compatibility decision, or human handoff | `/api/agent/chat` | Commerce Agent FastAPI API |

The new `/api/agent/chat` Next.js route is a server-side proxy. It reads `COMMERCE_AGENT_API_BASE_URL` and optional synthetic-only `COMMERCE_AGENT_DEMO_TOKEN` from deployment environment variables; browser code never sees a token or calls the agent directly.

## Integration sequence

1. Keep the existing home page, start form, recommendation cards, and Dify route unchanged.
2. The copied `app/chat-demo/page.tsx` routes every Store-originated question to `/api/agent/chat`; its historical standalone entry may still use Dify for comparison.
3. Agent results render as structured operation cards within the existing chat visual system.
4. Deploy the copied frontend only after an approved HTTPS endpoint is configured for the synthetic Commerce Agent.

No route is allowed to invoke a real merchant production system or perform inventory, refund, cancellation, or address mutations.
