import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "ECS003_DOCTRINE_LIBRARY_CERTIFICATION"


class ECS003DoctrineLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/ecs003_doctrine_library.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=120,
        )
        cls.returncode = completed.returncode
        cls.stderr = completed.stderr

    def _read_json(self, filename: str):
        return json.loads((OUTPUT_DIR / filename).read_text(encoding="utf-8"))

    def test_generator_executes_successfully(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_library_inventory_preserves_all_source_orders(self):
        inventory = self._read_json("library_inventory_registry.json")
        self.assertEqual(len(inventory), 10)
        self.assertTrue(all(record["structural_status"] == "VALIDATED" for record in inventory))
        self.assertEqual(len({record["sha256"] for record in inventory}), 10)

    def test_cross_references_and_terms_are_validated(self):
        cross_refs = self._read_json("cross_reference_validation_registry.json")
        terms = self._read_json("canonical_terminology_registry.json")
        self.assertTrue(cross_refs)
        self.assertTrue(all(record["resolution"] == "RESOLVED" for record in cross_refs))
        self.assertTrue(all(record["disposition"] == "CANONICAL_USAGE_PRESENT" for record in terms))

    def test_requirements_have_matching_proof_skeletons_and_traceability(self):
        requirements = self._read_json("requirement_registry.json")
        proofs = self._read_json("proof_skeleton_registry.json")
        graph = self._read_json("traceability_graph.json")
        self.assertGreater(len(requirements), 100)
        self.assertEqual(len(requirements), len(proofs))
        self.assertEqual(graph["coverage"]["requirements"], len(requirements))
        self.assertTrue(graph["coverage"]["bidirectional_links_present"])

    def test_office_instantiation_is_deterministic_and_fail_closed_governed(self):
        instantiation = self._read_json("office_instantiation_registry.json")
        self.assertEqual(instantiation["disposition"], "INSTANTIATION_READY")
        self.assertIn("UNKNOWN_VALUES_FAIL_CLOSED", instantiation["placeholder_governance"])
        self.assertEqual(len(instantiation["program_identifiers"]), 7)

    def test_mutation_library_and_self_certification_are_ready(self):
        mutations = self._read_json("mutation_library_registry.json")
        self_cert = self._read_json("self_certification_report.json")
        completion = self._read_json("completion_report.json")
        self.assertGreaterEqual(len(mutations), 6)
        self.assertTrue(all(record["restoration_required"] for record in mutations))
        self.assertEqual(self_cert["final_disposition"], "LIBRARY_READY_FOR_INDEPENDENT_AUDIT")
        self.assertEqual(completion["status"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
