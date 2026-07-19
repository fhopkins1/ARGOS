from __future__ import annotations

import unittest

from argos.control_panel.canonical_bridge_denominator_execution import (
    BridgeExecutionEvidenceClass,
    execute_eoea_certification,
)
from argos.control_panel.canonical_bridge_fabric import BridgeResultStatus
from argos.control_panel.canonical_enterprise_runtime import CanonicalEnterpriseRuntime


class EOEACanonicalBridgeDenominatorExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_eoea_certification("TEST-COMMIT")

    def test_denominator_reconciles_prior_audit_without_hiding_replay_bridge(self) -> None:
        denominator = self.payload["bridge_denominator"]

        self.assertEqual(denominator["priorRequiredCount"], 30)
        self.assertEqual(denominator["currentRequiredCount"], 29)
        self.assertEqual(denominator["removedBridges"], ())
        self.assertIn("BRIDGE-REPLAY-LAB-001", denominator["reconciliation"])
        self.assertEqual(len(denominator["reclassifiedBridges"]), 1)

    def test_every_required_bridge_has_truth_model_and_coverage_row(self) -> None:
        truth_models = self.payload["bridge_truth_models"]
        matrix = self.payload["bridge_coverage_matrix"]

        required_ids = {row["bridge_id"] for row in matrix}
        truth_ids = {row["bridge_id"] for row in truth_models}
        self.assertTrue(required_ids.issubset(truth_ids))
        self.assertEqual(len(matrix), self.payload["bridge_classification"]["required_bridge_count"])
        self.assertEqual(len(required_ids), len(matrix))

    def test_runtime_campaign_generates_canonical_origin_and_acceptance(self) -> None:
        campaign = self.payload["canonical_runtime_campaigns"]
        executed = [row for row in campaign["bridgeResults"] if row.get("executed")]

        self.assertGreater(len(executed), 0)
        self.assertTrue(all(row["executionOrigin"] == "CANONICAL_RUNTIME" for row in executed))
        self.assertTrue(all(row["destinationAcceptanceReference"] for row in executed if row["status"] == BridgeResultStatus.ACCEPTED.value))
        self.assertFalse(campaign["directHarnessExecution"])

    def test_coverage_matrix_counts_runtime_execution_not_declarations(self) -> None:
        coverage = self.payload["bridge_classification"]
        matrix = self.payload["bridge_coverage_matrix"]

        self.assertEqual(coverage["canonical_runtime_executed"], sum(1 for row in matrix if row["final_status"] == BridgeExecutionEvidenceClass.CANONICAL_RUNTIME_EXECUTED.value))
        self.assertEqual(coverage["contract_only"], 0)
        self.assertEqual(coverage["integration_only"], 0)

    def test_partial_metadata_no_longer_blocks_accepted_canonical_runtime_traces(self) -> None:
        matrix = self.payload["bridge_coverage_matrix"]
        blocked = [row for row in matrix if row["final_status"] == BridgeExecutionEvidenceClass.BLOCKED.value]

        self.assertEqual(len(blocked), 0)
        self.assertEqual(self.payload["certification"]["canonicalRuntimeExecuted"], 29)
        self.assertEqual(self.payload["certification"]["verdict"], "PASS")

    def test_static_assurance_rejects_harness_counting(self) -> None:
        static = self.payload["static_assurance"]

        self.assertFalse(static["directCertificationBridgeExecutionCounted"])
        self.assertTrue(static["destinationAcceptanceRequired"])
        self.assertFalse(static["denominatorDerivedFromSuccessfulTraces"])

    def test_runtime_campaign_is_available_from_canonical_runtime(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        runtime.start()
        try:
            campaign = runtime.run_canonical_bridge_denominator_campaign(campaign_id="EOEA-TEST")
        finally:
            runtime.halt(reason="EO-EA test complete")

        self.assertGreater(campaign["acceptedBridgeCount"], 0)
        self.assertEqual(campaign["stimulusBoundary"], "operator-level canonical runtime campaign request")

    def test_trace_index_contains_audit_correlators(self) -> None:
        trace_index = self.payload["bridge_trace_index"]

        self.assertTrue(all("bridgeId" in row for row in trace_index))
        self.assertTrue(any(row["destinationAcceptanceReference"] for row in trace_index))
        self.assertTrue(any(row["deterministicHash"] for row in trace_index))


if __name__ == "__main__":
    unittest.main()
