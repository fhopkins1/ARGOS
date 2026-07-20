from decimal import Decimal
from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.intelligence import (  # noqa: E402
    BrokerOrderRecord,
    BrokerReconciliationDisposition,
    BrokerReconciliationEngine,
    EvidencePackageService,
    EvidenceRole,
    EvidenceSufficiencyState,
    ExecutionRecord,
    ExecutionState,
    MissingEvidenceRecord,
    NewsClaim,
    NewsClaimReconciliationEngine,
    NewsClaimState,
    NewsEventClass,
    NewsReport,
    NewsSourceClass,
    NewsSourceRecord,
    OfficialConfirmationStatus,
    OrderIntentRecord,
    OrderLifecycleState,
    PositionSnapshot,
    SeekerConflictClass,
    SeekerEvidenceRecord,
    SentinelAlertState,
    SentinelConflictEngine,
    SentinelSignal,
    SentinelSignalType,
    SnapshotSourceType,
    TradeRestrictionState,
)


def news_source(source_class=NewsSourceClass.RECOGNIZED_NEWSWIRE, source_id="SRC-NEWS-1") -> NewsSourceRecord:
    return NewsSourceRecord(source_id, "ORG-1", "Wire", "api", source_class, "GROUP-1", "PARENT-1", (), (), "US", "api-key", "NOT_OFFICIAL", "VERIFIED", "published-corrections", "published-retractions", ("raw", "timestamp"), ("discovery",), ("provisional",), ("independent_if_origin_unique",), ("truth_without_origin",))


def news_claim(**overrides) -> NewsClaim:
    data = {
        "claim_id": "CLAIM-1",
        "subject_entity": "ISSUER-1",
        "affected_instrument": "AAPL",
        "event_class": NewsEventClass.MERGER_OR_ACQUISITION,
        "asserted_action": "is discussing acquisition",
        "asserted_actor": "ISSUER-1",
        "asserted_target": "TARGET-1",
        "asserted_status": "UNCONFIRMED",
        "asserted_jurisdiction": "US",
        "asserted_event_time": "2026-07-20T12:00:00Z",
        "asserted_effective_time": "",
        "asserted_publication_time": "2026-07-20T12:01:00Z",
        "claim_scope": "deal_rumor",
        "source_language": "en",
        "normalized_claim": "ISSUER-1 discussing acquisition TARGET-1",
        "qualifying_language": "people familiar",
        "uncertainty_language": "may",
        "denial_language": "",
        "conditional_language": "",
        "future_tense_language": "",
        "evidence_references": ("sha256:claim",),
    }
    data.update(overrides)
    return NewsClaim(**data)


def news_report(**overrides) -> NewsReport:
    data = {
        "report_id": "REPORT-1",
        "workflow_id": "WF-TR",
        "claim": news_claim(),
        "source": news_source(),
        "origin_evidence_id": "ORIGIN-1",
        "cited_report_ids": (),
        "cited_evidence_retrievable": True,
        "publication_time": "2026-07-20T12:01:00Z",
        "retrieval_time": "2026-07-20T12:02:00Z",
        "correction_time": "",
        "retraction_time": "",
        "expiration_time": "2099-01-01T00:00:00Z",
        "named_source_present": False,
        "anonymous_source_present": True,
        "official_confirmation_status": OfficialConfirmationStatus.NO_OFFICIAL_AUTHORITY_PRESENT,
    }
    data.update(overrides)
    return NewsReport(**data)


def order_intent(**overrides) -> OrderIntentRecord:
    data = {
        "order_intent_id": "INTENT-1",
        "workflow_id": "WF-TR",
        "decision_object_id": "DO-1",
        "risk_authorization_id": "RISK-1",
        "account_id": "ACCT-1",
        "strategy_id": "STRAT-1",
        "instrument_id": "AAPL",
        "side": "BUY",
        "position_effect": "OPEN",
        "order_type": "LIMIT",
        "time_in_force": "DAY",
        "requested_quantity": Decimal("10"),
        "limit_price": Decimal("200"),
        "currency": "USD",
        "client_order_id": "CLIENT-1",
        "idempotency_key": "IDEMP-1",
        "authorized_at": "2026-07-20T12:00:00Z",
        "workflow_execution_token_id": "TOKEN-1",
        "intent_status": OrderLifecycleState.TRANSMITTED,
        "created_at": "2026-07-20T12:00:00Z",
        "evidence_references": ("sha256:intent",),
    }
    data.update(overrides)
    return OrderIntentRecord(**data)


def broker_order(**overrides) -> BrokerOrderRecord:
    data = {
        "broker_order_record_id": "BORDER-1",
        "broker_id": "BROKER-1",
        "broker_account_id": "ACCT-1",
        "broker_order_id": "BROKER-ORDER-1",
        "client_order_id": "CLIENT-1",
        "order_intent_id": "INTENT-1",
        "instrument_id": "AAPL",
        "side": "BUY",
        "original_quantity": Decimal("10"),
        "remaining_quantity": Decimal("5"),
        "filled_quantity": Decimal("5"),
        "average_fill_price": Decimal("199.50"),
        "broker_status": OrderLifecycleState.PARTIALLY_FILLED,
        "broker_status_reason": "partial",
        "broker_received_at": "2026-07-20T12:00:02Z",
        "last_updated_at": "2026-07-20T12:01:00Z",
        "raw_broker_evidence": "sha256:broker",
        "broker_event_sequence": 1,
        "recorded_at": "2026-07-20T12:01:01Z",
    }
    data.update(overrides)
    return BrokerOrderRecord(**data)


def execution(**overrides) -> ExecutionRecord:
    data = {
        "execution_record_id": "EXEC-1",
        "broker_execution_id": "BEXEC-1",
        "broker_order_id": "BROKER-ORDER-1",
        "order_intent_id": "INTENT-1",
        "account_id": "ACCT-1",
        "instrument_id": "AAPL",
        "execution_quantity": Decimal("5"),
        "execution_price": Decimal("199.50"),
        "currency": "USD",
        "execution_timestamp": "2026-07-20T12:01:00Z",
        "commission": Decimal("0"),
        "regulatory_fees": Decimal("0"),
        "exchange_fees": Decimal("0"),
        "other_fees": Decimal("0"),
        "execution_status": ExecutionState.PARTIAL_EXECUTION,
        "raw_evidence_reference": "sha256:exec",
        "created_at": "2026-07-20T12:01:01Z",
    }
    data.update(overrides)
    return ExecutionRecord(**data)


def signal(**overrides) -> SentinelSignal:
    data = {
        "signal_id": "SIG-1",
        "workflow_id": "WF-TR",
        "decision_object_id": "DO-1",
        "observation_id": "OBS-1",
        "instrument_id": "AAPL",
        "issuer_id": "ISSUER-1",
        "event_type": "halt",
        "authority_domain": "exchange",
        "source_id": "SRC-EXCHANGE",
        "source_origin_id": "ORIGIN-EXCHANGE",
        "content_hash": "hash-1",
        "semantic_identity_id": "SEM-1",
        "signal_type": SentinelSignalType.TRADING_HALT,
        "materiality": "HIGH",
        "source_available": True,
        "source_schema_valid": True,
        "source_authenticated": True,
        "conflicting_observation_ids": (),
        "observation_time": "2026-07-20T12:00:00Z",
        "publication_time": "2026-07-20T12:00:00Z",
        "effective_time": "2026-07-20T12:00:00Z",
        "expiration_time": "2099-01-01T00:00:00Z",
        "evidence_references": ("sha256:sig",),
    }
    data.update(overrides)
    return SentinelSignal(**data)


def evidence(**overrides) -> SeekerEvidenceRecord:
    data = {
        "evidence_id": "EV-1",
        "observation_id": "OBS-1",
        "source_id": "SRC-1",
        "authority_class": "PRIMARY_AUTHORITY",
        "evidence_role": EvidenceRole.MANDATORY,
        "claim_identity": "CLAIM-1",
        "entity_id": "ISSUER-1",
        "instrument_id": "AAPL",
        "publication_time": "2026-07-20T12:00:00Z",
        "observation_time": "2026-07-20T12:00:00Z",
        "effective_time": "2026-07-20T12:00:00Z",
        "retrieval_time": "2026-07-20T12:01:00Z",
        "source_available": True,
        "provenance_complete": True,
        "normalization_complete": True,
        "identity_verified": True,
        "version_verified": True,
        "fresh": True,
        "independent_origin_id": "ORIGIN-1",
        "raw_evidence_reference": "sha256:ev1",
    }
    data.update(overrides)
    return SeekerEvidenceRecord(**data)


class MOTR009To012OperationalReconciliationTests(unittest.TestCase):
    def test_motr009_repeated_rumor_does_not_become_truth(self) -> None:
        first = news_report(source=news_source(NewsSourceClass.ANONYMOUS_SOURCE_REPORT, "SRC-A"), origin_evidence_id="ANON-1")
        copy = news_report(report_id="REPORT-2", source=news_source(NewsSourceClass.SYNDICATED_COPY, "SRC-B"), origin_evidence_id="ANON-1")

        record = NewsClaimReconciliationEngine().reconcile((first, copy))

        self.assertEqual(record.current_claim_state, NewsClaimState.UNCONFIRMED)
        self.assertEqual(record.analyst_consequence, "NO_TRUTH_SELECTED_BY_NEWS_ENGINE")
        self.assertEqual(record.trader_consequence, "EXECUTION_PROHIBITED")

    def test_motr009_official_confirmation_is_distinct_from_report_count(self) -> None:
        official = news_report(source=news_source(NewsSourceClass.ORIGINATING_AUTHORITY, "SRC-ISSUER"), official_confirmation_status=OfficialConfirmationStatus.OFFICIAL_CONFIRMATION, anonymous_source_present=False, named_source_present=True)

        record = NewsClaimReconciliationEngine().reconcile((official,))

        self.assertEqual(record.current_claim_state, NewsClaimState.OFFICIALLY_CONFIRMED)
        self.assertEqual(record.official_confirmation_status, OfficialConfirmationStatus.OFFICIAL_CONFIRMATION)

    def test_motr010_broker_quantity_mismatch_blocks_new_orders_without_rewriting_intent(self) -> None:
        broker = broker_order(filled_quantity=Decimal("10"))
        partial_execution = execution(execution_quantity=Decimal("5"))

        record = BrokerReconciliationEngine().reconcile_order(order_intent(), broker, (partial_execution,))

        self.assertEqual(record.disposition, BrokerReconciliationDisposition.QUANTITY_MISMATCH)
        self.assertEqual(record.trade_restriction.scope, TradeRestrictionState.AFFECTED_INSTRUMENT_NEW_ORDERS_BLOCKED)
        self.assertEqual(record.internal_state, OrderLifecycleState.TRANSMITTED)
        self.assertEqual(record.broker_state, OrderLifecycleState.PARTIALLY_FILLED)

    def test_motr010_position_reconciliation_preserves_source_type_boundary(self) -> None:
        internal = PositionSnapshot("POS-I", SnapshotSourceType.INTERNAL_EXPECTED, "BROKER-1", "ACCT-1", "AAPL", "2026-07-20T12:00:00Z", Decimal("10"), Decimal("10"), Decimal("0"), Decimal("200"), "USD", "sha256:intpos", "2026-07-20T12:00:01Z")
        broker = PositionSnapshot("POS-B", SnapshotSourceType.BROKER_REPORTED, "BROKER-1", "ACCT-1", "AAPL", "2026-07-20T12:00:00Z", Decimal("5"), Decimal("5"), Decimal("0"), Decimal("199"), "USD", "sha256:brpos", "2026-07-20T12:00:01Z")

        self.assertEqual(BrokerReconciliationEngine().reconcile_position(internal, broker), BrokerReconciliationDisposition.POSITION_MISMATCH)

    def test_motr011_duplicate_suppression_records_no_action_without_priority_inflation(self) -> None:
        engine = SentinelConflictEngine()
        first = engine.evaluate(signal())
        duplicate = engine.evaluate(signal(signal_id="SIG-2", observation_id="OBS-2"))

        self.assertEqual(first.alert_state, SentinelAlertState.MARKET_SAFETY_ALERT)
        self.assertEqual(duplicate.alert_state, SentinelAlertState.NO_ACTION)
        self.assertEqual(duplicate.required_action, "record_duplicate_suppression")

    def test_motr011_source_health_and_replay_are_deterministic(self) -> None:
        engine = SentinelConflictEngine()
        unhealthy = signal(source_available=False, signal_type=SentinelSignalType.NEWS_ALERT)
        record = engine.evaluate(unhealthy)

        self.assertEqual(record.alert_state, SentinelAlertState.SOURCE_HEALTH_ALERT)
        self.assertEqual(engine.replay(record, unhealthy), SentinelAlertState.SOURCE_HEALTH_ALERT)

    def test_motr012_seeker_preserves_conflicts_and_marks_complete_with_conflict(self) -> None:
        service = EvidencePackageService()
        package = service.create_evidence_package("WF-TR", "news_event", "CLAIM-1")
        left = evidence()
        right = evidence(evidence_id="EV-2", observation_id="OBS-2", source_id="SRC-2", raw_evidence_reference="sha256:ev2", independent_origin_id="ORIGIN-2", authority_class="SECONDARY_AUTHORITY")
        package = service.append_observation(package, left)
        package = service.append_observation(package, right)
        conflict = service.classify_conflict(package, left, right)
        package = service.append_conflict(package, conflict)

        self.assertEqual(conflict.conflict_class, SeekerConflictClass.AUTHORITY_CONFLICT)
        self.assertEqual(service.evaluate_sufficiency(package), EvidenceSufficiencyState.COMPLETE_WITH_CONFLICT)
        self.assertTrue(service.handoff_to_analyst(package).startswith("ANALYSTHANDOFF-"))

    def test_motr012_missing_mandatory_evidence_prevents_analyst_handoff(self) -> None:
        service = EvidencePackageService()
        package = service.create_evidence_package("WF-TR", "sec_filing", "CLAIM-2")
        missing = MissingEvidenceRecord("MISS-1", "primary_filing", EvidenceRole.MANDATORY, "primary authority unavailable", "retry", "UNAVAILABLE", "2026-07-20T12:00:00Z")
        package = service.append_missing_evidence(package, missing)

        self.assertEqual(service.evaluate_sufficiency(package), EvidenceSufficiencyState.PRIMARY_SOURCE_MISSING)
        with self.assertRaises(ValueError):
            service.handoff_to_analyst(package)


if __name__ == "__main__":
    unittest.main()
