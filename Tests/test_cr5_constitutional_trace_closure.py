from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.cr_audit_closure import (  # noqa: E402
    constitutional_component_inventory,
    constitutional_trace_findings,
    execute_cr5_constitutional_trace_audit,
)


class CR5ConstitutionalTraceClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_cr5_constitutional_trace_audit(REPOSITORY_ROOT, commit="TEST-COMMIT")

    def test_cr5_is_incomplete_when_predecessor_gates_are_unproven(self) -> None:
        self.assertEqual("CR-5", self.payload["orderId"])
        self.assertEqual("TEST-COMMIT", self.payload["repositoryCommit"])
        self.assertEqual("INCOMPLETE", self.payload["verdict"])
        self.assertTrue(self.payload["entryBlockers"])
        self.assertIn("CR-5 establishes constitutional trace closure", self.payload["constitutionalStatement"])

    def test_scorecard_contains_required_constitutional_domains(self) -> None:
        scorecard = self.payload["constitutionalScorecard"]

        for domain in (
            "LAW VII",
            "Workflow Execution Token",
            "Authority",
            "Delegation",
            "Promotion",
            "Provenance",
            "Office Lifecycle",
            "Bridge Execution",
            "Destination Acceptance",
            "Read Purity",
            "Performance Truth",
            "Evidence Integrity",
        ):
            self.assertIn(domain, scorecard)
            self.assertIn(scorecard[domain], {"PASS", "FAIL", "INCOMPLETE"})

    def test_constitutional_inventory_discovers_runtime_components(self) -> None:
        inventory = constitutional_component_inventory(REPOSITORY_ROOT)

        self.assertGreater(inventory["componentCount"], 0)
        self.assertIn("token", inventory["roleCounts"])
        self.assertIn("authority", inventory["roleCounts"])
        self.assertIn("bridge", inventory["roleCounts"])

    def test_constitutional_scanner_returns_trace_review_leads(self) -> None:
        findings = constitutional_trace_findings(REPOSITORY_ROOT)

        self.assertTrue(findings)
        self.assertTrue(all(item.disposition == "TRACE_REVIEW_REQUIRED" for item in findings))
        self.assertTrue(any(item.constitutional_domain in {"LAW VII", "Read Purity", "Provenance"} for item in findings))

    def test_final_counts_keep_canonical_runtime_bypass_nonzero_under_entry_blockers(self) -> None:
        counts = self.payload["finalConstitutionalCounts"]

        self.assertGreater(counts["canonical-runtime bypass paths"], 0)
        self.assertIn("read mutation paths", counts)
        self.assertIn("Performance Truth incomplete-lineage paths", counts)

    def test_trace_campaign_records_tc_inputs_without_readiness_claim(self) -> None:
        campaign = self.payload["constitutionalTraceCampaign"]

        self.assertEqual(4, len(campaign))
        self.assertEqual({item["case"] for item in campaign}, {"trace-equivalence", "authority-promotion", "canonical-bridge-dynamic-coverage", "orphan-office-closure"})
        self.assertTrue(all(item["verdict"] in {"PASS", "FAIL", "INCOMPLETE"} for item in campaign))


if __name__ == "__main__":
    unittest.main()
