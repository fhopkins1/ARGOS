import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from argos.trader.rm002a016_b07_candidate_readiness import _affected_population, _completed_batches, execute_b07


class TraderRM002A016B07CandidateReadinessTests(unittest.TestCase):
    def test_completed_batches_inventory_b04_b05_b06(self):
        batches = _completed_batches()
        self.assertEqual({batch.batch_id for batch in batches}, {"B04", "B05", "B06"})
        self.assertTrue(all(batch.terminal_status != "MISSING" for batch in batches))

    def test_affected_population_has_terminal_mappings(self):
        records = _affected_population()
        self.assertGreater(len(records), 0)
        self.assertTrue(all(record.final_disposition for record in records))
        self.assertTrue(all(record.requirement_id for record in records))
        self.assertTrue(all(record.proof_id for record in records))

    def test_b07_produces_final_readiness_evidence(self):
        with TemporaryDirectory() as temp_dir:
            result = execute_b07(Path(temp_dir))
            self.assertEqual(result["B07-001"]["completion"], "PASS")
            self.assertEqual(result["B07-002"]["completion"], "PASS")
            self.assertEqual(result["B07-003"]["completion"], "PASS")
            self.assertIn(result["B07-003"]["final_verdict"], {"READY", "NOT_READY"})


if __name__ == "__main__":
    unittest.main()
