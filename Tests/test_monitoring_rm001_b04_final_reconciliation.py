import json
import unittest

from Scripts import monitoring_rm001_b04_final_reconciliation as b04


class MonitoringRM001B04FinalReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completion = b04.generate()
        cls.output_dir = b04.OUTPUT_DIR

    def _load(self, name):
        return json.loads((self.output_dir / name).read_text(encoding="utf-8"))

    def test_constitutional_consistency_has_no_open_issues(self):
        inventory = self._load("B04-001_constitutional_doctrine_inventory.json")
        consistency = self._load("B04-001_constitutional_consistency_registry.json")
        validation = self._load("B04-001_constitutional_validation_report.json")

        self.assertGreater(len(inventory), 0)
        self.assertTrue(all(item["participates_in_reconciliation"] for item in inventory))
        self.assertTrue(all(item["reconciliation_status"] == "CONSISTENT" for item in consistency))
        self.assertEqual(validation["status"], "PASS")
        self.assertEqual(validation["contradictions"], 0)
        self.assertEqual(validation["ambiguities"], 0)

    def test_requirement_population_is_canonical_and_not_orphaned(self):
        requirements = self._load("B04-002_reconciled_constitutional_requirement_registry.json")
        identities = self._load("B04-002_canonical_requirement_identity_registry.json")
        orphans = self._load("B04-002_orphan_requirement_registry.json")
        report = self._load("B04-002_requirement_reconciliation_report.json")

        requirement_ids = [item["canonical_requirement_identity"] for item in requirements]
        self.assertEqual(len(requirement_ids), len(set(requirement_ids)))
        self.assertEqual(len(identities), len(requirements))
        self.assertEqual(orphans, [])
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["identity_ambiguity"])
        self.assertFalse(report["ownership_ambiguity"])

    def test_dependency_and_traceability_are_complete(self):
        dependencies = self._load("B04-003_dependency_reconciliation_registry.json")
        direction = self._load("B04-003_dependency_direction_registry.json")
        traceability = self._load("B04-003_bidirectional_traceability_verification_matrix.json")
        broken = self._load("B04-003_broken_traceability_registry.json")
        orphans = self._load("B04-003_orphan_constitutional_artifact_registry.json")
        ambiguity = self._load("B04-003_dependency_and_traceability_ambiguity_resolution_report.json")

        self.assertGreater(len(dependencies), 0)
        self.assertTrue(all(item["constitutional_owner"] for item in dependencies))
        self.assertTrue(all(item["deterministic"] for item in direction))
        self.assertTrue(all(item["forward_traceability_complete"] and item["reverse_traceability_complete"] for item in traceability))
        self.assertEqual(broken, [])
        self.assertEqual(orphans, [])
        self.assertEqual(ambiguity["status"], "PASS")

    def test_final_audit_authorizes_freeze_and_transition(self):
        verdict = self._load("B04-004_final_constitutional_verdict.json")
        blockers = self._load("B04-004_constitutional_blocker_registry.json")
        readiness = self._load("B04-004_constitutional_readiness_assessment.json")
        freeze = self._load("B04-004_constitutional_freeze_authorization_report.json")
        transition = self._load("B04-004_monitoring_rm002_transition_authorization.json")

        self.assertEqual(verdict["verdict"], "UNCONDITIONAL_PASS")
        self.assertEqual(blockers, [])
        self.assertEqual(readiness["status"], "READY")
        self.assertTrue(freeze["authorized"])
        self.assertTrue(transition["authorized"])
        self.assertEqual(transition["target"], "MONITORING-RM-002")

    def test_completion_report_preserves_execution_boundaries(self):
        completion = self._load("completion_report.json")
        series = self._load("series_completion_report.json")
        baseline = self._load("monitoring_rm001_b04_authoritative_reconciliation_baseline.json")

        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["final_verdict"], "UNCONDITIONAL_PASS")
        self.assertEqual(series["final_verdict"], "UNCONDITIONAL_PASS")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertEqual(completion["baseline_digest"], baseline["digest"])


if __name__ == "__main__":
    unittest.main()
