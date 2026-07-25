import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B04_PROOF_GENERATION"


class ExitDecisionRM002B04ProofGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_rm002_b04_proof_generation.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=120,
        )
        cls.returncode = completed.returncode
        cls.stderr = completed.stderr

    def _read_json(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_generator_completes(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_every_requirement_has_one_proof_disposition(self):
        proofs = self._read_json("requirement_proof_registry.json")
        self.assertEqual(len(proofs), 94)
        self.assertTrue(all(item["proof_id"] and item["proof_disposition"] for item in proofs))
        self.assertEqual(len({item["requirement_id"] for item in proofs}), 94)

    def test_proven_proofs_have_execution_and_evidence_lineage(self):
        proofs = self._read_json("requirement_proof_registry.json")
        proven = [item for item in proofs if item["proof_disposition"] == "PROVEN"]
        self.assertGreater(len(proven), 70)
        self.assertTrue(all(item["execution_identity"] for item in proven))
        self.assertTrue(all(item["evidence_identity"] for item in proven))

    def test_traceability_and_candidate_are_ready(self):
        graph = self._read_json("execution_derived_traceability_graph.json")
        candidate = self._read_json("certification_candidate_registry.json")
        readiness = self._read_json("certification_readiness_assessment.json")
        self.assertTrue(graph["nodes"])
        self.assertTrue(graph["edges"])
        self.assertEqual(candidate["candidate_disposition"], "READY_FOR_INDEPENDENT_REPRODUCTION")
        self.assertEqual(readiness["ready_for"], "EXIT-DECISION-RM-002-B05")

    def test_no_final_certification_is_issued(self):
        assessment = self._read_json("initial_ecs003_certification_assessment.json")
        self.assertFalse(assessment["final_ecs003_certification_issued"])
        self.assertTrue(assessment["requires_independent_reproduction"])

    def test_completion_report(self):
        completion = self._read_json("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["ready_for"], "EXIT-DECISION-RM-002-B05")
        self.assertEqual(completion["certification_blockers"], 0)
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["final_ecs003_certification_issued"])
        self.assertTrue(all(completion["completion_checks"].values()))


if __name__ == "__main__":
    unittest.main()
