"""Run unittest discovery and emit a minimal JUnit report without extra tooling."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest
from xml.etree.ElementTree import Element, ElementTree, SubElement


class ReportResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
    def addSuccess(self, test): self.records.append((test.id(), "success", "")); super().addSuccess(test)
    def addFailure(self, test, err): self.records.append((test.id(), "failure", self._exc_info_to_string(err, test))); super().addFailure(test, err)
    def addError(self, test, err): self.records.append((test.id(), "error", self._exc_info_to_string(err, test))); super().addError(test, err)
    def addSkip(self, test, reason): self.records.append((test.id(), "skipped", reason)); super().addSkip(test, reason)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2, resultclass=ReportResult).run(suite)
    xml = Element("testsuite", name="commerce-agent", tests=str(result.testsRun), failures=str(len(result.failures)), errors=str(len(result.errors)), skipped=str(len(result.skipped)))
    for test_id, outcome, detail in result.records:
        case = SubElement(xml, "testcase", classname=test_id.rpartition(".")[0], name=test_id.rpartition(".")[2])
        if outcome != "success":
            SubElement(case, outcome).text = detail
    args.report.parent.mkdir(parents=True, exist_ok=True)
    ElementTree(xml).write(args.report, encoding="utf-8", xml_declaration=True)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
