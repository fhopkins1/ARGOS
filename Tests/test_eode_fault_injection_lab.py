import unittest

from argos.control_panel.fault_injection_lab import (
    CampaignOutcome,
    FaultCategory,
    FaultInjectionRecoveryLaboratory,
    canonical_fault_catalog,
)
from argos.control_panel.transaction_reconciliation import TransactionState
from argos.control_panel.truth_promotion import PromotionDecisionStatus


class FaultInjectionRecoveryLaboratoryTests(unittest.TestCase):
    def test_fault_catalog_covers_required_categories_and_campaign_families(self):
        catalog = canonical_fault_catalog()
        categories = {fault.category for fault in catalog}
        names = {fault.name for fault in catalog}

        self.assertGreaterEqual(len(catalog), 35)
        self.assertIn(FaultCategory.STARTUP, categories)
        self.assertIn(FaultCategory.BROKER, categories)
        self.assertIn(FaultCategory.POSITION, categories)
        self.assertIn(FaultCategory.PERSISTENCE, categories)
        self.assertIn(FaultCategory.REPLAY, categories)
        self.assertIn(FaultCategory.RECOVERY, categories)
        self.assertIn(FaultCategory.TRUTH_DOMAIN_CONTAMINATION, categories)
        self.assertIn("duplicate startup", names)
        self.assertIn("duplicate fill", names)
        self.assertIn("replay contamination attempt", names)

    def test_every_fault_executes_and_preserves_evidence_without_mutation(self):
        lab = FaultInjectionRecoveryLaboratory()
        report = lab.launch_campaign(repetitions=1)

        self.assertEqual(len(report.records), len(lab.catalog))
        self.assertEqual(report.verdict, CampaignOutcome.PASS)
        self.assertTrue(all(record.pass_criteria_met for record in report.records))
        self.assertTrue(all(record.injected_evidence["productionTruthWriteAttempted"] is False for record in report.records))
        self.assertTrue(all(record.synthetic_truth_introduced is False for record in report.records))
        self.assertTrue(all(record.financial_mutation_authority is False for record in report.records))
        self.assertTrue(all(record.live_trading_enabled is False for record in report.records))

    def test_identical_campaigns_produce_deterministic_signatures(self):
        lab = FaultInjectionRecoveryLaboratory()
        report = lab.launch_campaign(
            fault_ids=("EO-DE-BROKER-002", "EO-DE-PERSIST-004", "EO-DE-READONLY-001"),
            repetitions=3,
        )

        self.assertTrue(report.deterministic)
        self.assertEqual(report.nondeterministic_faults, ())
        by_fault = {}
        for record in report.records:
            by_fault.setdefault(record.fault_id, set()).add(record.determinism_signature)
        self.assertTrue(all(len(signatures) == 1 for signatures in by_fault.values()))

    def test_truth_domain_contamination_is_rejected_by_eodc_without_synthetic_truth(self):
        lab = FaultInjectionRecoveryLaboratory()
        report = lab.launch_campaign(fault_ids=("EO-DE-REPLAY-003",), repetitions=2)

        for record in report.records:
            self.assertEqual(record.eodc_decision["decision"], PromotionDecisionStatus.REJECTED.value)
            self.assertIn("DOMAIN_CONTAMINATION_BLOCKED", record.eodc_decision["reason_codes"])
            self.assertFalse(record.eodc_decision["syntheticTruthPromoted"])
            self.assertFalse(record.synthetic_truth_introduced)

    def test_broker_position_faults_block_eodd_commit_through_reconciliation(self):
        lab = FaultInjectionRecoveryLaboratory()
        report = lab.launch_campaign(fault_ids=("EO-DE-BROKER-002", "EO-DE-POSITION-005"), repetitions=1)

        for record in report.records:
            self.assertEqual(record.eodd_evidence["engine"], "EO-DD")
            self.assertEqual(record.eodd_evidence["state"], TransactionState.BLOCKED.value)
            self.assertTrue(record.eodd_evidence["blocksCommit"])
            self.assertGreater(record.eodd_evidence["discrepancyCount"], 0)

    def test_recovery_faults_mark_transaction_recovery_required_without_duplicates(self):
        lab = FaultInjectionRecoveryLaboratory()
        report = lab.launch_campaign(fault_ids=("EO-DE-RECOVERY-001", "EO-DE-PERSIST-004"), repetitions=1)

        for record in report.records:
            self.assertEqual(record.eodd_evidence["state"], TransactionState.RECOVERY_REQUIRED.value)
            self.assertEqual(record.recovery_evidence["duplicateWorkflows"], 0)
            self.assertEqual(record.recovery_evidence["duplicateTokens"], 0)
            self.assertEqual(record.recovery_evidence["duplicateFills"], 0)
            self.assertTrue(record.recovery_evidence["evidencePreserved"])

    def test_read_only_faults_do_not_mutate_and_commit_cleanly(self):
        lab = FaultInjectionRecoveryLaboratory()
        report = lab.launch_campaign(
            fault_ids=("EO-DE-READONLY-001", "EO-DE-READONLY-002", "EO-DE-READONLY-003"),
            repetitions=1,
        )

        for record in report.records:
            self.assertEqual(record.eodd_evidence["state"], TransactionState.COMMITTED.value)
            self.assertEqual(record.eoda_evidence["verdict"], "PASS")
            self.assertFalse(record.financial_mutation_authority)
            self.assertFalse(record.synthetic_truth_introduced)

    def test_resource_exhaustion_fault_remains_bounded(self):
        lab = FaultInjectionRecoveryLaboratory()
        report = lab.launch_campaign(fault_ids=("EO-DE-RESOURCE-001",), repetitions=2)

        self.assertTrue(report.deterministic)
        self.assertTrue(all(record.resource_snapshot.bounded for record in report.records))
        self.assertTrue(all(record.resource_snapshot.queue_depth <= 10 for record in report.records))
        self.assertTrue(all(record.resource_snapshot.thread_count == 1 for record in report.records))

    def test_commander_can_acknowledge_and_halt_without_altering_results(self):
        lab = FaultInjectionRecoveryLaboratory()
        report = lab.launch_campaign(fault_ids=("EO-DE-BROKER-002",), repetitions=1)
        ack = lab.acknowledge_failure(report.campaign_id, "EO-DE-BROKER-002")
        halt = lab.halt_campaign(report.campaign_id)
        read_model = lab.commander_read_model()

        self.assertFalse(ack["resultsAltered"])
        self.assertFalse(halt["resultsAltered"])
        self.assertFalse(read_model["commanderControls"]["mayAlterResults"])
        self.assertFalse(read_model["commanderControls"]["mayCreateFill"])
        self.assertFalse(read_model["financialMutationAuthority"])
        self.assertFalse(read_model["liveTradingEnabled"])

    def test_package_exports_lab(self):
        from argos.control_panel import FaultInjectionRecoveryLaboratory as ExportedLaboratory

        self.assertIs(ExportedLaboratory, FaultInjectionRecoveryLaboratory)


if __name__ == "__main__":
    unittest.main()
