from __future__ import annotations

import json
import unittest

from Scripts import historian_ecs003_audit_002 as audit


class HistorianECS003Audit002Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        audit.generate()

    def _load(self, name: str):
        return json.loads((audit.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_final_decision_is_fail_not_conditional(self) -> None:
        decision = self._load("final_ecs003_certification_decision.json")
        self.assertEqual("FAIL", decision["decision"])
        self.assertFalse(decision["previous_certification_assumed_valid"])
        self.assertFalse(decision["constitutional_architecture_modified"])
        self.assertFalse(decision["implementation_modified"])
        self.assertTrue(decision["blocking_findings"])

    def test_all_named_audit_reports_are_generated(self) -> None:
        manifest = self._load("audit_manifest.json")
        required = {
            "independent_repository_discovery_report.json",
            "independent_implementation_inventory.json",
            "enterprise_information_journey_verification_report.json",
            "historical_custody_verification_report.json",
            "provenance_graph_verification_report.json",
            "historical_reconstruction_report.json",
            "language_preservation_verification_report.json",
            "missing_information_verification_report.json",
            "enterprise_learning_readiness_report.json",
            "counterfactual_readiness_report.json",
            "mutation_validation_report.json",
            "fail_closed_validation_report.json",
            "deterministic_replay_report.json",
            "cross_office_verification_report.json",
            "evidence_regeneration_report.json",
            "certification_findings_register.json",
            "final_ecs003_certification_decision.json",
        }
        self.assertTrue(required.issubset(set(manifest["deliverables"])))

    def test_findings_are_evidence_backed(self) -> None:
        findings = self._load("certification_findings_register.json")
        self.assertGreaterEqual(len(findings), 6)
        for finding in findings:
            self.assertEqual("BLOCKING", finding["severity"])
            self.assertTrue(finding["objective_evidence"])
            self.assertTrue(finding["required_remediation"])


if __name__ == "__main__":
    unittest.main()
