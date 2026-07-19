from __future__ import annotations

from pathlib import Path
import unittest

from argos.control_panel.canonical_bridge_denominator_execution import execute_eoea_certification
from argos.control_panel.remaining_bridge_blocker_elimination import execute_eoeh_certification


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class EOEHRemainingBridgeBlockerEliminationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_eoeh_certification("TEST-COMMIT", repo_root=REPOSITORY_ROOT)

    def test_denominator_is_not_reduced(self) -> None:
        denominator = self.payload["denominator_reconciliation"]

        self.assertEqual(denominator["priorRequiredCount"], 29)
        self.assertEqual(denominator["currentRequiredCount"], 29)
        self.assertEqual(denominator["removals"], ())
        self.assertEqual(denominator["reclassifications"], ())

    def test_all_required_bridges_execute_canonically(self) -> None:
        cert = self.payload["certification"]

        self.assertEqual(cert["verdict"], "PASS")
        self.assertEqual(cert["requiredInternalBridges"], 29)
        self.assertEqual(cert["canonicalRuntimeExecuted"], 29)
        self.assertEqual(cert["blocked"], 0)
        self.assertEqual(cert["failed"], 0)
        self.assertEqual(cert["unexecuted"], 0)
        self.assertEqual(cert["coveragePercent"], 100.0)

    def test_root_cause_matrix_has_no_unknown_or_open_blockers(self) -> None:
        matrix = self.payload["blocker_root_cause_matrix"]

        self.assertEqual(len(matrix), 29)
        self.assertTrue(all(row["finalStatus"] == "CANONICAL_RUNTIME_EXECUTED" for row in matrix))
        self.assertFalse(any(row["primaryBlocker"] == "UNKNOWN_BLOCKER" for row in matrix))

    def test_source_destination_persistence_and_trace_evidence_are_present(self) -> None:
        matrix = self.payload["blocker_root_cause_matrix"]

        self.assertTrue(all(row["sourceArtifactAvailability"] == "AVAILABLE" for row in matrix))
        self.assertTrue(all(row["destinationAcceptanceAvailability"] == "AVAILABLE" for row in matrix))
        self.assertTrue(all(row["persistenceState"] == "PERSISTED" for row in matrix))
        self.assertTrue(all(row["canonicalTrace"] == "CANONICAL_RUNTIME" for row in matrix))

    def test_static_assurance_rejects_direct_execution_and_denominator_manipulation(self) -> None:
        static = self.payload["static_assurance"]

        self.assertFalse(static["directExecutorCallsCounted"])
        self.assertFalse(static["certificationCreatedSourceArtifacts"])
        self.assertFalse(static["denominatorNarrowed"])

    def test_eoea_and_eoeh_coverage_agree(self) -> None:
        eoea = execute_eoea_certification("TEST-COMMIT")

        self.assertEqual(eoea["certification"]["currentRequiredCount"], 29)
        self.assertEqual(eoea["certification"]["canonicalRuntimeExecuted"], 29)
        self.assertEqual(eoea["certification"]["blockedCount"], 0)
        self.assertEqual(eoea["certification"]["verdict"], "PASS")

    def test_campaign_was_not_direct_harness_execution(self) -> None:
        campaign = self.payload["canonical_campaign_inventory"]

        self.assertFalse(campaign["directHarnessExecution"])
        self.assertEqual(campaign["acceptedBridgeCount"], 29)


if __name__ == "__main__":
    unittest.main()
