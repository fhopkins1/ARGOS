from __future__ import annotations

import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_rm002_implementation_certification import OUTPUT_DIR, generate_certification


class ClosedPositionTruthRM002ImplementationCertificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        generate_certification()

    def _load(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_program_deliverables_exist(self) -> None:
        required = {
            "implementation_inventory.json",
            "dependency_registry.json",
            "runtime_participation_registry.json",
            "verifier_registry.json",
            "fixture_registry.json",
            "behavioral_execution_registry.json",
            "implementation_findings_registry.json",
            "remediation_registry.json",
            "regression_verification_registry.json",
            "evidence_registry.json",
            "proof_registry.json",
            "implementation_traceability_graph.json",
            "certification_candidate_registry.json",
            "independent_reproduction_report.json",
            "fail_closed_validation_report.json",
            "final_ecs003_implementation_certification_report.json",
            "final_implementation_certification_verdict.json",
            "completion_report.json",
            "manifest.json",
        }
        present = {item.name for item in Path(OUTPUT_DIR).iterdir() if item.is_file()}
        self.assertTrue(required.issubset(present))

    def test_behavioral_execution_and_mutation_evidence_pass(self) -> None:
        behavioral = self._load("behavioral_execution_registry.json")
        mutations = self._load("controlled_mutation_registry.json")

        self.assertEqual(9, len(behavioral))
        self.assertTrue(all(item["disposition"] == "PASS" for item in behavioral))
        self.assertEqual(7, len(mutations))
        self.assertTrue(all(item["disposition"] == "PASS" for item in mutations))
        self.assertTrue(all(item["deterministic_rejection"] for item in mutations))

    def test_every_canonical_requirement_has_passing_proof_and_traceability(self) -> None:
        proof = self._load("proof_registry.json")
        traceability = self._load("implementation_traceability_graph.json")
        candidate = self._load("certification_candidate_registry.json")

        self.assertEqual(34, len(proof))
        self.assertEqual(34, len(traceability))
        self.assertTrue(all(item["proof_disposition"] == "PASS" for item in proof))
        self.assertTrue(all(item["traceability_disposition"] == "PASS" for item in traceability))
        self.assertEqual(0, candidate["certification_blockers"])
        self.assertEqual("READY_FOR_CERTIFICATION", candidate["candidate_disposition"])

    def test_independent_reproduction_and_final_verdict_certify_candidate(self) -> None:
        reproduction = self._load("independent_reproduction_report.json")
        final_report = self._load("final_ecs003_implementation_certification_report.json")
        verdict = self._load("final_implementation_certification_verdict.json")
        completion = self._load("completion_report.json")

        self.assertEqual("REPRODUCIBLE", reproduction["reproduction_disposition"])
        self.assertEqual("ECS003_IMPLEMENTATION_CERTIFIED", verdict["verdict"])
        self.assertTrue(final_report["no_certification_blockers_remain"])
        self.assertTrue(final_report["fail_closed_validation_passed"])
        self.assertTrue(final_report["every_requirement_has_implementation_evidence"])
        self.assertEqual("COMPLETE", completion["status"])
        self.assertTrue(all(completion["completion_criteria"].values()))


if __name__ == "__main__":
    unittest.main()
