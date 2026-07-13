import dataclasses
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.enterprise_persistence import DurableEnterprisePersistenceStore, EnterprisePersistenceError  # noqa: E402
from argos.control_panel.performance_truth_engine import PerformanceTruthEngine  # noqa: E402
from argos.control_panel.truth_domain import RuntimeMode, TruthClassification, make_paper_operational_truth_envelope  # noqa: E402
from argos.control_panel.truth_promotion import (  # noqa: E402
    EvidenceQuality,
    PromotionDecisionStatus,
    PromotionRejectionCode,
    PromotionScope,
    TruthInformationClass,
    TruthPromotionAuthority,
    PROMOTION_SCOPE_REGISTRY,
)
from argos.foundation.persistence.records import ObjectType  # noqa: E402


TIMESTAMP = "2026-07-13T17:00:00Z"


def _material_provenance() -> dict[str, str]:
    return {
        "asset_identifier": "Authorized office judgment",
        "asset_class": "Authorized office judgment",
        "direction": "Authorized office judgment",
        "thesis": "Authorized office judgment",
        "evidence": "Authorized office judgment",
        "market_context": "Authorized office judgment",
        "entry_conditions": "Authorized office judgment",
        "price_source": "Authorized broker market observation",
        "quantity": "Authorized office judgment",
        "position_sizing_basis": "Authorized office judgment",
        "confidence": "Authorized office judgment",
        "time_horizon": "Authorized office judgment",
        "risk_factors": "Authorized office judgment",
        "stop_conditions": "Authorized office judgment",
        "exit_conditions": "Authorized office judgment",
        "expected_return": "Authorized office judgment",
        "risk_approval": "Authorized office judgment",
        "trader_authorization": "Authorized office judgment",
    }


def _decision_object(**overrides: object) -> dict[str, object]:
    decision = {
        "decisionObjectId": "DO-EO-DC-001",
        "workflowId": "WF-EO-DC-001",
        "missionId": "MISSION-EO-DC-001",
        "workflowTokenId": "TOKEN-EO-DC-001",
        "executionMode": RuntimeMode.PAPER.value,
        "truthClassification": TruthClassification.PAPER_OPERATIONAL.value,
        "certificationStatus": "PAPER_OPERATIONAL_CERTIFIED",
        "office": "Trader",
        "sourceSystem": "Trader",
        "revisionSource": "authorized_office_judgment",
        "materialFieldProvenance": _material_provenance(),
        "recommendation": "BUY",
        "currentStrategy": "EO-DC",
        "expectedReturn": 0.02,
        "confidence": 0.9,
        "riskScore": 0.2,
        "apiFallbackUsed": False,
    }
    decision.update(overrides)
    return decision


def _envelope(*, caller: str = "PerformanceTruthEngine", authority: str = "DeterministicPaperBrokerage"):
    return make_paper_operational_truth_envelope(
        originating_authority=authority,
        originating_workflow_id="WF-EO-DC-001",
        workflow_token_id="TOKEN-EO-DC-001",
        mission_id="MISSION-EO-DC-001",
        source_event_id="PBE-EO-DC-001",
        idempotency_key="ORDER-EO-DC-001",
        timestamp_utc=TIMESTAMP,
        caller=caller,
    )


def _broker_order() -> dict[str, object]:
    return {
        "order_id": "ORDER-EO-DC-001",
        "status": "settled",
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
        "requested_quantity": 5,
        "filled_quantity": 5,
        "remaining_quantity": 0,
        "average_fill_price": 100.02,
        "ticket": {
            "workflow_id": "WF-EO-DC-001",
            "mission_id": "MISSION-EO-DC-001",
            "workflow_token": "TOKEN-EO-DC-001",
            "decision_object_id": "DO-EO-DC-001",
            "strategy_id": "EO-DC",
            "symbol": "AAPL",
            "asset_type": "stock",
            "side": "buy",
            "order_type": "market",
            "time_in_force": "day",
            "quantity": 5,
            "risk_approval_id": "RISK-EO-DC-001",
            "policy_approval_id": "POLICY-EO-DC-001",
            "trader_identity": "Trader",
            "account_id": "ACCT-PAPER-001",
            "decision_object": _decision_object(),
        },
        "market_state": {"bid": 100.0, "ask": 100.02, "last": 100.01, "volume": 100000, "session": "REGULAR"},
        "fills": ({"fill_id": "FILL-EO-DC-001", "quantity": 5, "price": 100.02, "commission": 0, "slippage": 0.01},),
    }


class EODCTruthPromotionTests(unittest.TestCase):
    def test_truth_taxonomy_and_scope_registry_are_explicit(self) -> None:
        self.assertIn(TruthInformationClass.AUTHORITATIVE_OPERATIONAL_FACT, tuple(TruthInformationClass))
        self.assertIn(TruthInformationClass.DEGRADED_ANALYTICAL_RECORD, tuple(TruthInformationClass))
        scopes = {item.scope for item in PROMOTION_SCOPE_REGISTRY}
        self.assertIn(PromotionScope.PERFORMANCE_TRUTH_INGESTION, scopes)
        self.assertIn(PromotionScope.CERTIFIED_LEARNING, scopes)

    def test_domain_rules_reject_test_proof_simulation_replay_and_live(self) -> None:
        authority = TruthPromotionAuthority()
        base = _envelope().__dict__
        cases = (
            (RuntimeMode.TEST.value, PromotionRejectionCode.TEST_NOT_PROMOTABLE.value),
            (RuntimeMode.PROOF.value, PromotionRejectionCode.PROOF_NOT_PROMOTABLE.value),
            (RuntimeMode.SIMULATION.value, PromotionRejectionCode.SIMULATION_NOT_PROMOTABLE.value),
            ("REPLAY", PromotionRejectionCode.REPLAY_CANNOT_CREATE_NEW_TRUTH.value),
            (RuntimeMode.LIVE.value, PromotionRejectionCode.LIVE_DISABLED.value),
        )
        for domain, expected in cases:
            decision = authority.promote_performance_truth(dict(base, truth_domain=domain), object_id=f"OBJ-{domain}")
            self.assertEqual(PromotionDecisionStatus.REJECTED, decision.decision)
            self.assertIn(expected, decision.reason_codes)

    def test_valid_paper_envelope_is_scope_approved_and_idempotent(self) -> None:
        authority = TruthPromotionAuthority()
        first = authority.promote_performance_truth(_envelope(), object_id="ORDER-EO-DC-001")
        second = authority.promote_performance_truth(_envelope(), object_id="ORDER-EO-DC-001")

        self.assertEqual(PromotionDecisionStatus.APPROVED, first.decision)
        self.assertEqual(first.decision_id, second.decision_id)
        self.assertFalse(first.reason_codes)

    def test_provenance_authority_lineage_and_scope_failures_are_deterministic(self) -> None:
        authority = TruthPromotionAuthority()
        bad = dict(_envelope().__dict__)
        bad["originating_authority"] = "Runtime"
        bad["workflow_token_id"] = ""
        bad["provenance_status"] = "UNVERIFIED"
        bad["fallback_indicators"] = ("fallback_quote",)

        decision = authority.promote_performance_truth(bad, object_id="BAD")

        self.assertIn(PromotionRejectionCode.SOURCE_AUTHORITY_INVALID.value, decision.reason_codes)
        self.assertIn(PromotionRejectionCode.TOKEN_MISSING.value, decision.reason_codes)
        self.assertIn(PromotionRejectionCode.PROVENANCE_UNVERIFIED.value, decision.reason_codes)
        self.assertIn(PromotionRejectionCode.FALLBACK_NOT_AUTHORITATIVE.value, decision.reason_codes)

    def test_decision_object_gate_accepts_certified_object_and_rejects_uncertified_or_runtime_authored(self) -> None:
        authority = TruthPromotionAuthority()

        accepted = authority.promote_decision_object(_decision_object())
        uncertified = authority.promote_decision_object(_decision_object(certificationStatus="UNCERTIFIED"))
        runtime = authority.promote_decision_object(_decision_object(sourceSystem="Runtime", revisionSource="runtime_placeholder"))

        self.assertEqual(PromotionDecisionStatus.APPROVED, accepted.decision)
        self.assertIn(PromotionRejectionCode.CERTIFICATION_SCOPE_MISSING.value, uncertified.reason_codes)
        self.assertIn(PromotionRejectionCode.SOURCE_AUTHORITY_INVALID.value, runtime.reason_codes)

    def test_learning_gate_rejects_degraded_proof_and_fallback_inputs(self) -> None:
        authority = TruthPromotionAuthority()
        degraded = dict(_envelope(authority="PerformanceTruthEngine").__dict__, degraded=True)
        proof = dict(_envelope(authority="PerformanceTruthEngine").__dict__, truth_domain=RuntimeMode.PROOF.value, truth_classification=TruthClassification.PROOF_ONLY.value)
        fallback = dict(_envelope(authority="PerformanceTruthEngine").__dict__, fallback_indicators=("default_benchmark",))

        self.assertIn(PromotionRejectionCode.DEGRADED_NOT_AUTHORITATIVE.value, authority.promote_learning_input(degraded, object_id="DEG").reason_codes)
        self.assertIn(PromotionRejectionCode.PROOF_NOT_PROMOTABLE.value, authority.promote_learning_input(proof, object_id="PROOF").reason_codes)
        self.assertIn(PromotionRejectionCode.FALLBACK_NOT_AUTHORITATIVE.value, authority.promote_learning_input(fallback, object_id="FALLBACK").reason_codes)

    def test_performance_truth_ingestion_requires_eodc_approved_promotion(self) -> None:
        engine = PerformanceTruthEngine()
        bad = dict(_envelope().__dict__, truth_domain=RuntimeMode.SIMULATION.value, truth_classification=TruthClassification.SIMULATION_ONLY.value)

        rejected = engine.record_broker_authoritative_order(_broker_order(), truth_envelope=bad)
        accepted = engine.record_broker_authoritative_order(_broker_order(), truth_envelope=_envelope())

        self.assertFalse(rejected["accepted"])
        self.assertIn(PromotionRejectionCode.SIMULATION_NOT_PROMOTABLE.value, rejected["codes"])
        self.assertTrue(accepted["accepted"])

    def test_persistence_requires_approved_promotion_envelope_and_records_decision(self) -> None:
        store = DurableEnterprisePersistenceStore()
        with self.assertRaises(EnterprisePersistenceError):
            store.persist_authoritative(ObjectType.ENTERPRISE_PERFORMANCE_TRUTH, "performance-truth-paper", {"records": ()}, truth_envelope=dict(_envelope(caller="DurableEnterprisePersistenceStore").__dict__, truth_domain=RuntimeMode.PROOF.value))

        record = store.persist_authoritative(
            ObjectType.ENTERPRISE_PERFORMANCE_TRUTH,
            "performance-truth-paper",
            {"records": ()},
            truth_envelope=_envelope(caller="DurableEnterprisePersistenceStore", authority="PerformanceTruthEngine"),
        )

        promotion = record.payload["operational_truth_envelope"]["eo_dc_promotion_decision"]
        self.assertEqual(PromotionDecisionStatus.APPROVED.value, promotion["decision"])

    def test_replay_cannot_create_new_active_paper_truth_and_commander_cannot_override(self) -> None:
        authority = TruthPromotionAuthority()
        replay = authority.promote_replay_record({"replay_run_id": "REPLAY-EO-DC"}, creates_new_active_truth=True)
        authority.revoke(replay.envelope_id, reason="test revocation", revocation_authority="Commander")
        model = authority.commander_read_model()

        self.assertIn(PromotionRejectionCode.REPLAY_CANNOT_CREATE_NEW_TRUTH.value, replay.reason_codes)
        self.assertFalse(model["commanderLimitations"]["mayConvertProofToPaper"])
        self.assertFalse(model["financialMutationAuthority"])
        self.assertTrue(model["revokedApprovals"])

    def test_promotion_decisions_are_serializable_assurance_evidence(self) -> None:
        decision = TruthPromotionAuthority().promote_performance_truth(_envelope(), object_id="SERIAL")
        payload = dataclasses.asdict(decision)

        self.assertEqual("EO-DC.1", payload["evaluator_version"])
        self.assertEqual(PromotionDecisionStatus.APPROVED, decision.decision)


if __name__ == "__main__":
    unittest.main()
