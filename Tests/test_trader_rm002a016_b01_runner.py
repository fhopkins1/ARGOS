from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.trader_rm002a016_b01_runner import BATCH_ID, _scenario_specs, candidate_manifest  # noqa: E402


class TraderRM002A016B01RunnerTests(unittest.TestCase):
    def test_runner_validation_inventory_is_controlled_and_excludes_production_modules(self) -> None:
        specs = _scenario_specs()
        names = {spec["name"] for spec in specs}

        self.assertIn("pass_valid_json", names)
        self.assertIn("malformed_json", names)
        self.assertIn("timeout", names)
        self.assertIn("wrong_candidate_digest", names)
        self.assertIn("concurrency_isolation_a", names)
        self.assertFalse(any("cic" in name or "css" in name for name in names))

    def test_candidate_manifest_records_batch_and_runner_identity(self) -> None:
        manifest = candidate_manifest()

        self.assertEqual(BATCH_ID, manifest["batch_identifier"])
        self.assertTrue(manifest["commit_identifier"])
        self.assertTrue(manifest["runner_source_digest"])
        self.assertTrue(manifest["runner_test_digest"])
        self.assertTrue(manifest["candidate_digest"])


if __name__ == "__main__":
    unittest.main()
