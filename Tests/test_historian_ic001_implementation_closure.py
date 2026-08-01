from __future__ import annotations

import json
import unittest

from Scripts import historian_ic001_implementation_closure as closure


class HistorianIC001ImplementationClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        closure.generate()

    def _load(self, name: str):
        return json.loads((closure.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_closure_freezes_operational_baseline(self) -> None:
        report = self._load("completion_report.json")
        self.assertEqual("IMPLEMENTATION CLOSED AND BASELINE FROZEN", report["closure_decision"])
        self.assertEqual("AUTHORIZED", report["operational_status"])
        self.assertTrue(report["implementation_development_closed"])
        self.assertTrue(all(item["disposition"] == "PASS" for item in report["completion_criteria"]))

    def test_certifications_are_preserved(self) -> None:
        registry = self._load("certification_preservation_registry.json")
        decisions = {item["certification_id"]: item["decision"] for item in registry["preserved_certifications"]}
        self.assertEqual("ECS-003 CERTIFIED", decisions["HISTORIAN-ECS003-AUDIT-003"])
        self.assertEqual("ECS-004 CERTIFIED", decisions["HISTORIAN-ECS004-AUDIT-001"])
        self.assertEqual("READY", decisions["HISTORIAN-RM-004"])

    def test_future_modification_governance_requires_recertification(self) -> None:
        governance = self._load("future_modification_governance_registry.json")
        self.assertTrue(all(item["recertification_required"] for item in governance["recertification_triggers"]))
        control = self._load("configuration_control_registry.json")
        self.assertTrue(control["undocumented_changes_prohibited"])

    def test_enterprise_integration_is_authorized(self) -> None:
        integration = self._load("enterprise_integration_authorization.json")
        self.assertGreaterEqual(len(integration["authorized_offices"]), 12)
        self.assertTrue(all(item["integration_authorized"] for item in integration["authorized_offices"]))


if __name__ == "__main__":
    unittest.main()
