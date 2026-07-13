import unittest

from argos.control_panel.transaction_reconciliation import (
    TRANSACTION_TYPE_REGISTRY,
    ParticipantState,
    TransactionCoordinatorError,
    TransactionReconciliationCoordinator,
    TransactionState,
    TransactionType,
)
from argos.control_panel.truth_promotion import PromotionDecisionStatus


def approved_decision(**overrides):
    base = {
        "decision_id": "EO-DC-DECISION-001",
        "envelope_id": "ENV-001",
        "requested_promotion": "PERFORMANCE_TRUTH_INGESTION",
        "requested_consumer": "TransactionCoordinator",
        "decision": PromotionDecisionStatus.APPROVED.value,
        "reason_codes": (),
        "authority_checks": ("authority accepted",),
        "provenance_checks": ("verified",),
        "lineage_checks": ("workflow lineage present",),
        "evidence_checks": ("source reference present",),
        "policy_checks": (),
        "doctrine_checks": (),
        "eoda_invariant_status": "PASS",
        "timestamp_utc": "2026-07-13T00:00:00Z",
        "deterministic_sequence": 1,
        "evaluator_version": "EO-DC.1",
        "idempotency_key": "eodc-key-001",
    }
    base.update(overrides)
    return base


def create_intent(coordinator=None, **overrides):
    coordinator = coordinator or TransactionReconciliationCoordinator()
    base = {
        "eodc_decision": approved_decision(),
        "source_authority": "DeterministicPaperBrokerage",
        "source_event_id": "fill-event-001",
        "mission_id": "mission-001",
        "workflow_id": "workflow-001",
        "workflow_execution_token_id": "token-001",
        "asset_id": "AAPL",
        "account_id": "paper-account",
        "order_id": "order-001",
        "fill_id": "fill-001",
        "position_id": "position-001",
        "idempotency_key": "tx-key-001",
    }
    base.update(overrides)
    return coordinator.coordinate_broker_fill(**base)


class TransactionReconciliationCoordinatorTests(unittest.TestCase):
    def test_transaction_registry_covers_required_lifecycle_types_without_mutation_authority(self):
        registered = {item.transaction_type for item in TRANSACTION_TYPE_REGISTRY}

        self.assertIn(TransactionType.OPENING_FILL, registered)
        self.assertIn(TransactionType.FULL_CLOSURE, registered)
        self.assertIn(TransactionType.RECONCILIATION_CORRECTION, registered)
        self.assertFalse(any(item.coordinator_mutation_authority for item in TRANSACTION_TYPE_REGISTRY))

    def test_intent_is_persisted_before_participant_completion(self):
        coordinator = TransactionReconciliationCoordinator()
        intent = create_intent(coordinator)

        snapshot = coordinator.snapshot(intent.transaction_id)
        self.assertEqual(snapshot.state, TransactionState.PRECONDITIONS_VALIDATED.value)
        self.assertEqual(snapshot.intent["transaction_hash"], intent.transaction_hash)
        self.assertEqual(len(snapshot.participants), 4)
        self.assertEqual(coordinator.journal.records[0].event_type, "INTENT_PERSISTED")

    def test_non_paper_or_unapproved_eodc_decision_is_rejected(self):
        coordinator = TransactionReconciliationCoordinator()

        with self.assertRaisesRegex(TransactionCoordinatorError, "EO_DC_APPROVAL_REQUIRED"):
            create_intent(coordinator, eodc_decision=approved_decision(decision=PromotionDecisionStatus.REJECTED.value))

        with self.assertRaisesRegex(TransactionCoordinatorError, "EO_DD_LIVE_OR_NON_PAPER_DOMAIN_DISABLED"):
            coordinator.create_intent(
                TransactionType.OPENING_FILL,
                eodc_decision=approved_decision(),
                source_authority="LiveBroker",
                source_event_id="live-fill",
                mission_id="mission",
                workflow_id="workflow",
                workflow_execution_token_id="token",
                asset_id="AAPL",
                account_id="live-account",
                truth_domain="LIVE",
            )

    def test_idempotency_returns_existing_intent_without_duplicate_journal_intent(self):
        coordinator = TransactionReconciliationCoordinator()
        first = create_intent(coordinator)
        second = create_intent(coordinator)

        self.assertEqual(first.transaction_id, second.transaction_id)
        self.assertEqual(len(coordinator.journal.intents), 1)
        self.assertEqual(sum(1 for item in coordinator.journal.records if item.event_type == "INTENT_PERSISTED"), 1)

    def test_commit_is_blocked_until_required_participants_ack_and_reconcile(self):
        coordinator = TransactionReconciliationCoordinator()
        intent = create_intent(coordinator)

        state = coordinator.evaluate_commit(intent.transaction_id)

        self.assertEqual(state, TransactionState.PARTICIPANTS_READY)
        self.assertNotEqual(coordinator.snapshot(intent.transaction_id).state, TransactionState.COMMITTED.value)

    def test_all_acknowledgments_and_clean_reconciliation_commit_transaction(self):
        coordinator = TransactionReconciliationCoordinator()
        intent = create_intent(coordinator)
        for authority in intent.intended_participants:
            coordinator.acknowledge_participant(
                intent.transaction_id,
                authority,
                evidence_reference=f"{authority}-ledger-v1",
                output_version="v1",
            )

        reconciliation = coordinator.reconcile_transaction(intent.transaction_id, performance_truth_snapshot={"orderLedger": (), "positionRegistry": {"allPositions": ()}, "closedPositionTruth": ()})
        state = coordinator.evaluate_commit(intent.transaction_id)

        self.assertEqual(reconciliation.verdict, "RECONCILED")
        self.assertEqual(state, TransactionState.COMMITTED)

    def test_partial_acknowledgment_cannot_masquerade_as_complete(self):
        coordinator = TransactionReconciliationCoordinator()
        intent = create_intent(coordinator)
        coordinator.acknowledge_participant(
            intent.transaction_id,
            "Paper Broker",
            evidence_reference="broker-fill-ledger-v1",
            output_version="v1",
        )

        state = coordinator.evaluate_commit(intent.transaction_id)
        snapshot = coordinator.snapshot(intent.transaction_id)

        self.assertEqual(state, TransactionState.RECONCILIATION_PENDING)
        self.assertEqual(snapshot.participants[0]["state"], ParticipantState.ACKNOWLEDGED.value)
        self.assertNotEqual(snapshot.state, TransactionState.COMMITTED.value)

    def test_duplicate_acknowledgment_is_idempotent(self):
        coordinator = TransactionReconciliationCoordinator()
        intent = create_intent(coordinator)

        first = coordinator.acknowledge_participant(
            intent.transaction_id,
            "Paper Broker",
            evidence_reference="broker-fill-ledger-v1",
            output_version="v1",
            idempotency_key="ack-key-001",
        )
        second = coordinator.acknowledge_participant(
            intent.transaction_id,
            "Paper Broker",
            evidence_reference="broker-fill-ledger-v1",
            output_version="v1",
            idempotency_key="ack-key-001",
        )

        self.assertEqual(first.acknowledgment_id, second.acknowledgment_id)
        self.assertEqual(coordinator.journal.participants[intent.transaction_id]["Paper Broker"].ack_count, 1)

    def test_reconciliation_detects_cross_ledger_discrepancies_and_blocks_commit(self):
        coordinator = TransactionReconciliationCoordinator()
        intent = create_intent(coordinator)
        for authority in intent.intended_participants:
            coordinator.acknowledge_participant(
                intent.transaction_id,
                authority,
                evidence_reference=f"{authority}-ledger-v1",
                output_version="v1",
            )
        snapshot = {
            "orderLedger": ({"order_id": "order-001", "status": "FILLED", "filled_quantity": 0},),
            "positionRegistry": {"allPositions": ({"position_id": "position-001", "quantity": 10, "broker_order_ids": ("order-001",), "fill_ids": ()},)},
            "closedPositionTruth": (
                {"position_id": "position-001"},
                {"position_id": "position-001"},
            ),
        }

        reconciliation = coordinator.reconcile_transaction(intent.transaction_id, performance_truth_snapshot=snapshot)
        state = coordinator.evaluate_commit(intent.transaction_id)

        self.assertTrue(reconciliation.blocks_commit)
        self.assertGreaterEqual(len(reconciliation.discrepancies), 2)
        self.assertEqual(state, TransactionState.BLOCKED)

    def test_recovery_replay_marks_nonterminal_transactions_without_repair(self):
        coordinator = TransactionReconciliationCoordinator()
        intent = create_intent(coordinator)

        recovered = coordinator.recover_nonterminal()
        recovered_again = coordinator.recover_nonterminal()

        self.assertEqual(recovered[0]["transactionId"], intent.transaction_id)
        self.assertEqual(coordinator.snapshot(intent.transaction_id).state, TransactionState.RECOVERY_REQUIRED.value)
        self.assertEqual(recovered_again[0]["recoveryState"], TransactionState.RECOVERY_REQUIRED.value)

    def test_commander_read_model_is_read_only_and_reports_integrity(self):
        coordinator = TransactionReconciliationCoordinator()
        intent = create_intent(coordinator)
        coordinator.recover_nonterminal()

        read_model = coordinator.commander_read_model()

        self.assertEqual(read_model["engineeringOrder"], "EO-DD")
        self.assertFalse(read_model["financialMutationAuthority"])
        self.assertFalse(read_model["liveTradingEnabled"])
        self.assertFalse(read_model["commanderLimitations"]["mayCreateFill"])
        self.assertEqual(read_model["journalIntegrityFindings"], ())
        self.assertEqual(read_model["blockedOrRecoveryRequired"][0]["transaction_id"], intent.transaction_id)


if __name__ == "__main__":
    unittest.main()
