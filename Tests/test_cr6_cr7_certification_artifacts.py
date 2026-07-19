from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.cr_audit_closure import (  # noqa: E402
    canonical_test_denominator,
    certification_artifact_inventory,
    execute_cr5_constitutional_trace_audit,
    execute_cr6_artifact_regeneration_audit,
    execute_cr7_full_suite_accounting_audit,
)


class CR6CR7CertificationArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cr5 = execute_cr5_constitutional_trace_audit(REPOSITORY_ROOT, commit="TEST-COMMIT")
        cls.cr6 = execute_cr6_artifact_regeneration_audit(REPOSITORY_ROOT, commit="TEST-COMMIT", cr5_payload=cls.cr5)
        cls.cr7 = execute_cr7_full_suite_accounting_audit(REPOSITORY_ROOT, commit="TEST-COMMIT", cr6_payload=cls.cr6)

    def test_cr6_fails_closed_when_predecessor_gates_are_incomplete(self) -> None:
        payload = self.cr6

        self.assertEqual("CR-6", payload["orderId"])
        self.assertEqual("INCOMPLETE", payload["verdict"])
        self.assertTrue(payload["entryBlockers"])
        self.assertEqual("FAIL_CLOSED", payload["candidateConsistency"]["packageAssemblyStatus"])
        self.assertEqual(0, payload["candidateConsistency"]["historicalArtifactsReused"])

    def test_cr6_inventory_quarantines_existing_evidence(self) -> None:
        inventory = certification_artifact_inventory(REPOSITORY_ROOT, current_commit="TEST-COMMIT")

        self.assertGreater(inventory["artifactCount"], 0)
        self.assertGreaterEqual(inventory["unknownIdentityCount"] + inventory["mixedCandidateCount"], 1)
        self.assertTrue(all(item["currentEligibility"] == "PROHIBITED_AS_CURRENT_REGENERATION_INPUT" for item in inventory["artifacts"]))

    def test_cr6_envelopes_reference_one_candidate_identity(self) -> None:
        envelopes = self.cr6["regeneratedArtifactEnvelopes"]

        self.assertGreaterEqual(envelopes["envelopeCount"], 8)
        commits = {item["candidate"]["repository_commit"] for item in envelopes["envelopes"]}
        self.assertEqual({"TEST-COMMIT"}, commits)
        self.assertTrue(all(item["artifact_body_hash"] for item in envelopes["envelopes"]))

    def test_cr7_collects_canonical_unittest_denominator(self) -> None:
        denominator = canonical_test_denominator(REPOSITORY_ROOT, commit="TEST-COMMIT")

        self.assertEqual("py -3 -m unittest discover -s Tests -p test*.py", denominator["canonicalCommand"])
        self.assertGreater(denominator["testCount"], 1000)
        self.assertEqual(0, denominator["duplicateTestCount"])
        self.assertTrue(denominator["denominatorHash"])

    def test_cr7_records_unexecuted_repeated_suite_as_incomplete(self) -> None:
        payload = self.cr7

        self.assertEqual("CR-7", payload["orderId"])
        self.assertEqual("INCOMPLETE", payload["verdict"])
        self.assertTrue(payload["entryBlockers"])
        self.assertEqual("NOT_EXECUTED_BY_GENERATOR", payload["repeatedSuiteAccounting"]["threeConsecutiveFullSuiteRuns"]["status"])
        self.assertFalse(payload["repeatedSuiteAccounting"]["arithmeticReconciliation"]["reconciled"])

    def test_cr7_environment_and_skip_audits_are_machine_readable(self) -> None:
        payload = self.cr7

        self.assertIn("pythonVersion", payload["environmentIdentity"])
        self.assertIn("configurationFilesReviewed", payload["hiddenExclusionAudit"])
        self.assertIn("skipped", payload["skipXfailDeselectionAudit"])
        self.assertIn(payload["collectionCertification"]["collectionStatus"], {"PASS", "FAIL"})


if __name__ == "__main__":
    unittest.main()
