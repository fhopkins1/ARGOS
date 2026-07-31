from __future__ import annotations

import json
import unittest
from pathlib import Path

from Scripts import historian_ecs003_audit_001 as audit


class HistorianECS003Audit001Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        audit.generate()

    def _load(self, name: str):
        return json.loads((audit.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_deliverables_are_generated(self) -> None:
        manifest = self._load("audit_manifest.json")
        required = {
            "constitutional_findings_register.json",
            "missing_responsibility_register.json",
            "ownership_findings_register.json",
            "historical_completeness_assessment.json",
            "provenance_assessment.json",
            "enterprise_journey_assessment.json",
            "interface_assessment.json",
            "enterprise_learning_readiness_assessment.json",
            "counterfactual_readiness_assessment.json",
            "constitutional_risk_assessment.json",
            "ecs003_certification_recommendation.json",
            "completion_report.json",
        }
        self.assertTrue(required.issubset(set(manifest["deliverables"])))

    def test_every_finding_has_order_required_fields_and_evidence(self) -> None:
        findings = self._load("constitutional_findings_register.json")
        self.assertGreaterEqual(len(findings), 8)
        for finding in findings:
            for field in audit.REQUIRED_FIELDS:
                self.assertTrue(finding[field], f"{finding['finding_id']} missing {field}")
            self.assertTrue(finding["objective_evidence"])
            self.assertIn(finding["severity"], {"BLOCKING", "MAJOR"})

    def test_recommendation_requires_constitutional_remediation_only(self) -> None:
        report = self._load("completion_report.json")
        self.assertEqual(report["ecs003_certification_recommendation"], "REQUIRES_CONSTITUTIONAL_REMEDIATION")
        self.assertFalse(report["implementation_quality_evaluated"])
        self.assertFalse(report["runtime_behavior_modified"])
        self.assertFalse(report["constitutional_authority_modified"])
        self.assertFalse(report["implementation_verification_authorized"])
        self.assertTrue(report["blocking_findings"])


if __name__ == "__main__":
    unittest.main()
