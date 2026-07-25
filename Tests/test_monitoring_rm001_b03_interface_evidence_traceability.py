import json
import unittest
from pathlib import Path

from Scripts import monitoring_rm001_b03_interface_evidence_traceability as b03


class MonitoringRM001B03InterfaceEvidenceTraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completion = b03.generate()
        cls.output_dir = b03.OUTPUT_DIR

    def _load(self, name):
        return json.loads((self.output_dir / name).read_text(encoding="utf-8"))

    def test_interface_and_dependency_registries_are_complete(self):
        interfaces = self._load("B03-001_constitutional_interface_registry.json")
        dependency_matrix = self._load("B03-001_dependency_direction_matrix.json")
        validation = self._load("B03-001_constitutional_validation_report.json")

        self.assertEqual(len(interfaces), len(b03.INTERFACE_PARTNERS))
        self.assertEqual(len(dependency_matrix), len(b03.INTERFACE_PARTNERS))
        self.assertTrue(all(item["constitutional_producer"] for item in interfaces))
        self.assertTrue(all(item["constitutional_consumer"] for item in interfaces))
        self.assertTrue(all(item["deterministic"] for item in dependency_matrix))
        self.assertTrue(all("Monitoring" in item["direction"] for item in dependency_matrix))
        self.assertEqual(validation["ambiguities"], [])
        self.assertEqual(validation["undocumented_interfaces"], [])
        self.assertEqual(validation["unauthorized_interfaces"], [])
        self.assertTrue(validation["producer_consumer_complete"])

    def test_temporal_freshness_and_duplicate_governance_are_deterministic(self):
        temporal = self._load("B03-002_canonical_temporal_event_registry.json")
        freshness = self._load("B03-002_freshness_evaluation_registry.json")
        duplicates = self._load("B03-002_duplicate_governance_registry.json")
        integrity = self._load("B03-002_temporal_integrity_verification_report.json")

        self.assertEqual(len(temporal), len(b03.TEMPORAL_EVENTS))
        self.assertEqual(len(freshness), len(b03.FRESHNESS_CLASSES))
        self.assertTrue(all(item["stale_determination"] == "deterministic comparison against threshold" for item in freshness))
        self.assertTrue(all(item["historical_preservation"] == "all duplicates remain traceable" for item in duplicates))
        self.assertTrue(integrity["freshness_deterministic"])
        self.assertEqual(integrity["ambiguities"], [])

    def test_evidence_doctrine_rejects_non_event_evidence(self):
        evidence = self._load("B03-003_canonical_evidence_registry.json")
        rejected = self._load("B03-003_constitutionally_rejected_evidence_registry.json")
        ambiguity = self._load("B03-003_evidence_ambiguity_resolution_report.json")

        rejected_classes = {item["rejected_class"] for item in rejected}
        self.assertEqual(len(evidence), len(b03.EVIDENCE_EVENTS))
        self.assertIn("metadata-only evidence", rejected_classes)
        self.assertIn("completion-report-only evidence", rejected_classes)
        self.assertTrue(all("immutability" in item["integrity_requirements"] for item in evidence))
        self.assertEqual(ambiguity["ambiguities"], [])

    def test_requirement_identity_and_traceability_have_no_orphans(self):
        requirements = self._load("B03-004_canonical_requirement_registry.json")
        traceability = self._load("B03-004_bidirectional_constitutional_traceability_registry.json")
        orphan_requirements = self._load("B03-004_orphan_requirement_registry.json")
        orphan_artifacts = self._load("B03-004_orphan_constitutional_artifact_registry.json")
        completeness = self._load("B03-004_constitutional_completeness_verification_report.json")

        requirement_ids = [item["canonical_requirement_identity"] for item in requirements]
        self.assertEqual(len(requirement_ids), len(set(requirement_ids)))
        self.assertEqual(len(traceability), len(requirements))
        self.assertEqual(orphan_requirements, [])
        self.assertEqual(orphan_artifacts, [])
        self.assertTrue(completeness["traceability_graph_complete"])
        self.assertEqual(completeness["omitted_requirements"], [])

    def test_series_completion_preserves_execution_boundaries(self):
        completion = self._load("completion_report.json")
        series = self._load("series_completion_report.json")
        baseline = self._load("monitoring_rm001_b03_authoritative_baseline.json")

        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(series["status"], "COMPLETE")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["certification_activity_executed"])
        self.assertEqual(completion["baseline_digest"], baseline["digest"])


if __name__ == "__main__":
    unittest.main()
