from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "web"


class NextWebBridgeTests(unittest.TestCase):
    def test_source_copy_keeps_dify_and_adds_server_side_agent_proxy(self):
        self.assertTrue((WEB / "app" / "page.tsx").exists())
        self.assertTrue((WEB / "app" / "api" / "dify" / "chat" / "route.ts").exists())
        route = (WEB / "app" / "api" / "agent" / "chat" / "route.ts").read_text(encoding="utf-8")
        client = (WEB / "lib" / "commerce-agent.ts").read_text(encoding="utf-8")
        self.assertIn("postToCommerceAgent", route)
        self.assertIn("COMMERCE_AGENT_API_BASE_URL", client)
        self.assertNotIn("NEXT_PUBLIC_COMMERCE_AGENT_DEMO_TOKEN", client)

    def test_chat_page_routes_store_context_to_agent_without_removing_legacy_dify(self):
        page = (WEB / "app" / "chat-demo" / "page.tsx").read_text(encoding="utf-8")
        self.assertIn('fetch("/api/dify/chat"', page)
        self.assertIn('fetch("/api/agent/chat"', page)
        self.assertIn("isAgentIntent", page)
        self.assertIn("shouldUseCommerceAgent", page)
        self.assertIn("fromStore || isAgentIntent(query)", page)
        self.assertIn("AgentResultCard", page)

    def test_storefront_chat_uses_store_context_and_return_path(self):
        page = (WEB / "app" / "chat-demo" / "page.tsx").read_text(encoding="utf-8")
        store = (WEB / "app" / "store" / "page.tsx").read_text(encoding="utf-8")
        self.assertIn('searchParams.get("from") === "store"', page)
        self.assertIn('backHref={fromStore ? "/store" : "/start"}', page)
        self.assertIn('homeHref={fromStore ? "/store" : "/"}', page)
        self.assertIn("/chat-demo?from=store", store)


if __name__ == "__main__":
    unittest.main()
