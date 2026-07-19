from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.cr_audit_closure import (  # noqa: E402
    CR_AUDIT_VERSION,
    execute_cr_series_audit,
    repository_truth_findings,
    synthetic_truth_inventory,
)


class CRSeriesAuditClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_cr_series_audit(REPOSITORY_ROOT, commit="TEST-COMMIT")

    def test_cr_series_payload_is_identity_bound_and_non_readiness_certifying(self) -> None:
        self.assertEqual(CR_AUDIT_VERSION, self.payload["schemaVersion"])
        self.assertEqual("TEST-COMMIT", self.payload["repositoryCommit"])
        self.assertIn("candidateIdentity", self.payload)
        self.assertEqual({"cr2", "cr3", "cr4"}, set(self.payload["orders"]))
        self.assertIn("does not certify", self.payload["constitutionalStatements"]["cr3"])

    def test_dirty_or_unproven_predecessors_gate_cr3_and_cr4_to_incomplete(self) -> None:
        orders = self.payload["orders"]

        self.assertIn(orders["cr2"]["verdict"], {"INCOMPLETE", "FAIL"})
        self.assertEqual("INCOMPLETE", orders["cr3"]["verdict"])
        self.assertEqual("INCOMPLETE", orders["cr4"]["verdict"])
        self.assertTrue(orders["cr3"]["entryBlockers"])
        self.assertTrue(orders["cr4"]["entryBlockers"])

    def test_synthetic_truth_inventory_preserves_reachability_counts(self) -> None:
        inventory = synthetic_truth_inventory(REPOSITORY_ROOT)

        self.assertGreater(inventory["candidateCount"], 0)
        self.assertGreater(inventory["baselineFindingCount"], 0)
        self.assertIn("productionReachableSyntheticSources", inventory)
        self.assertIn("sampleCandidates", inventory)

    def test_repository_truth_scanner_returns_trace_review_leads(self) -> None:
        findings = repository_truth_findings(REPOSITORY_ROOT)

        self.assertTrue(findings)
        self.assertTrue(all(item.disposition == "UNRESOLVED_STATIC_LEAD" for item in findings))
        self.assertTrue(any(item.pattern in {"unfinished_marker", "broad_exception", "constant_success_return", "pass"} for item in findings))

    def test_cr4_final_counts_are_not_zeroed_when_static_leads_remain(self) -> None:
        cr4 = self.payload["orders"]["cr4"]
        counts = cr4["finalRepositoryTruthCounts"]

        self.assertGreater(cr4["repositoryInventory"]["scannerFindings"], 0)
        self.assertGreater(
            counts["false completion paths"] + counts["supported incomplete runtime paths"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
