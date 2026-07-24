from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.trader_rm002a016_b02_runner import (  # noqa: E402
    B02_CONTROLLED_TESTS,
    DEFAULT_PRIOR_CAMPAIGN_ROOT,
    THIRTEEN_DASHBOARD_FIXTURE_TESTS,
    affected_inventory,
    candidate_manifest,
)


class TraderRM002A016B02RunnerTests(unittest.TestCase):
    def test_inventory_is_limited_to_authoritative_fill_fixture_population(self) -> None:
        inventory = affected_inventory(DEFAULT_PRIOR_CAMPAIGN_ROOT)
        identifiers = {record["immutable_test_identifier"] for record in inventory["records"]}

        self.assertEqual(13, inventory["prior_authoritative_fill_errors"])
        self.assertTrue(set(THIRTEEN_DASHBOARD_FIXTURE_TESTS).issubset(identifiers))
        self.assertTrue(set(B02_CONTROLLED_TESTS).issubset(identifiers))
        self.assertFalse(any("test_cic" in item or "test_css" in item or "test_authorization" in item or "test_risk" in item for item in identifiers))
        self.assertTrue(inventory["freeze_digest"])

    def test_candidate_manifest_records_fill_fixture_identity(self) -> None:
        manifest = candidate_manifest()

        self.assertTrue(manifest["candidate_digest"])
        self.assertTrue(manifest["authoritative_fill_implementation_digest"])
        self.assertTrue(manifest["position_implementation_digest"])
        self.assertTrue(manifest["fixture_source_digest"])
        self.assertTrue(manifest["test_population_digest"])


if __name__ == "__main__":
    unittest.main()
