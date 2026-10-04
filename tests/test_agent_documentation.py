from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class AgentDocumentationTests(unittest.TestCase):
    def test_docs_index_describes_the_grouped_documentation(self):
        index = (DOCS / "INDEX.md").read_text(encoding="utf-8")
        for section in ("product/", "runtime/", "integration/", "agent评测/", "operations/"):
            self.assertIn(section, index)

    def test_runtime_contract_covers_five_agent_components(self):
        text = (DOCS / "runtime" / "AGENT_RUNTIME_SPEC.md").read_text(encoding="utf-8")
        for component in ("Model", "Planner", "Tool use", "Memory", "Harness"):
            self.assertIn(component, text)
        self.assertIn("No LLM provider is connected", text)

    def test_dify_and_evaluation_specs_are_linked_from_prd(self):
        prd = (DOCS / "PRD.md").read_text(encoding="utf-8")
        for document in (
            "AGENT_RUNTIME_SPEC.md",
            "DIFY_WORKFLOW_SPEC.md",
            "EVALUATION_SPEC.md",
        ):
            self.assertIn(document, prd)

    def test_evaluation_spec_blocks_unsupported_facts(self):
        text = (DOCS / "agent评测" / "EVALUATION_SPEC.md").read_text(encoding="utf-8")
        self.assertIn("forbidden-claim rate", text)
        self.assertIn("release blocker", text)
