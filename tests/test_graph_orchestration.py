from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from commerce_agent.agent import CommerceAgent
from commerce_agent.graph import CommerceGraph
from commerce_agent.models import ChatRequest


class GraphOrchestrationTests(unittest.TestCase):
    def test_graph_records_planner_tool_and_validation_nodes(self):
        graph = CommerceGraph(CommerceAgent())
        response = graph.invoke(ChatRequest.from_dict({"thread_id": "graph", "message": "charger"}), "graph-request")
        nodes = [entry["node"] for entry in response.trace]
        self.assertEqual(response.status, "completed")
        self.assertEqual(nodes[-7:], ["graph_guard_input", "graph_load_memory", "graph_planner", "graph_tool", "graph_validate", "graph_compose", "graph_persist"])
        self.assertEqual(response.plan["intent"], "product")

    def test_handoff_uses_explicit_terminal_node(self):
        graph = CommerceGraph(CommerceAgent())
        response = graph.invoke(ChatRequest.from_dict({"thread_id": "graph-risk", "message": "refund please"}), "graph-risk-request")
        self.assertEqual(response.status, "handoff")
        self.assertEqual(response.trace[-2]["node"], "graph_handoff")
        self.assertEqual(response.trace[-1]["node"], "graph_persist")
