from __future__ import annotations

from pathlib import Path
import unittest

from argos.control_panel.missing_eoeb_closure import EOEBPriorStatus, execute_eoeg_certification


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class EOEGMissingEOEBClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_eoeg_certification("TEST-COMMIT", repo_root=REPOSITORY_ROOT)

    def test_missing_evidence_root_cause_identifies_tc002_supersession(self) -> None:
        root = self.payload["missing_evidence_root_cause"]
        prior = self.payload["prior_implementation_status"]

        self.assertTrue(root["tc002SupportingImplementationPresent"])
        self.assertTrue(root["eoebGeneratorAbsentAtBaseline"])
        self.assertEqual(prior["status"], EOEBPriorStatus.SUPERSEDED_WITHOUT_RECERTIFICATION.value)

    def test_authority_registry_has_no_validation_findings(self) -> None:
        registry = self.payload["authority_registry"]

        self.assertEqual(registry["validation_findings"], ())
        self.assertGreater(len(self.payload["authority_inventory"]), 0)
        self.assertGreater(len(self.payload["principal_inventory"]), 0)

    def test_blocked_bridge_matrix_assigns_exact_non_authority_causes(self) -> None:
        matrix = self.payload["blocked_bridge_authority_matrix"]

        self.assertEqual(len(matrix), 14)
        self.assertTrue(all(not row["authorityDefectOpen"] for row in matrix))
        self.assertTrue(all(row["exactRootCause"] != "AUTHORITY_DEFECT_OPEN" for row in matrix))
        self.assertTrue(all(row["canonicalExecutionResult"] == "EXECUTED_ACCEPTED_BY_DESTINATION" for row in matrix))

    def test_certification_and_recovery_cannot_create_runtime_authority(self) -> None:
        certification = self.payload["certification_authority_isolation"]
        recovery = self.payload["recovery_authority_validation"]

        self.assertFalse(certification["certificationProductionEnabled"])
        self.assertFalse(certification["mayCreateRuntimeAuthority"])
        self.assertFalse(recovery["mayFabricateAuthority"])

    def test_revoked_delegation_and_proof_domain_mismatch_are_rejected(self) -> None:
        validation = self.payload["expiration_revocation_validation"]

        self.assertTrue(validation["revokedDelegationRejected"])
        self.assertTrue(validation["proofDomainMismatchRejected"])

    def test_updated_eoea_results_show_no_authority_blockers_after_eoeb(self) -> None:
        updated = self.payload["updated_eoea_bridge_results"]

        self.assertEqual(updated["authorityBlockedAfterEOEB"], 0)
        self.assertEqual(updated["requiredBridgeCount"], 29)
        self.assertEqual(updated["canonicalRuntimeExecuted"], 15)

    def test_verdict_is_incomplete_due_residual_non_authority_blockers(self) -> None:
        cert = self.payload["certification"]

        self.assertEqual(cert["verdict"], "INCOMPLETE")
        self.assertEqual(cert["internalAuthorityBlockerCount"], 0)
        self.assertEqual(cert["remainingNonAuthorityBlockerCount"], 14)
        self.assertEqual(cert["failReasons"], ())


if __name__ == "__main__":
    unittest.main()
