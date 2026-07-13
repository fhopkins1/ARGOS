import inspect
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import server  # noqa: E402
from argos.control_panel.canonical_enterprise_runtime import CanonicalEnterpriseRuntime  # noqa: E402
from argos.control_panel.closed_position_truth import ClosedPositionTruthBuilder  # noqa: E402
from argos.control_panel.enterprise_persistence import DurableEnterprisePersistenceStore, EnterprisePersistenceError  # noqa: E402
from argos.control_panel.performance_truth_engine import PerformanceTruthEngine  # noqa: E402
from argos.control_panel.truth_domain import (  # noqa: E402
    ProvenanceStatus,
    RuntimeMode,
    TruthClassification,
    make_paper_operational_truth_envelope,
    validate_decision_object_for_operational_truth,
    validate_operational_truth_envelope,
)
from argos.foundation.persistence.records import ObjectType  # noqa: E402


TIMESTAMP = "2026-07-13T15:00:00Z"


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


def _decision_object(**overrides: str) -> dict[str, object]:
    decision = {
        "executionMode": RuntimeMode.PAPER.value,
        "truthClassification": TruthClassification.PAPER_OPERATIONAL.value,
        "certificationStatus": "PAPER_OPERATIONAL_CERTIFIED",
        "office": "Trader",
        "sourceSystem": "Trader",
        "revisionSource": "authorized_office_judgment",
        "materialFieldProvenance": _material_provenance(),
        "recommendation": "BUY",
        "currentStrategy": "IFVR Phase III.5",
        "expectedReturn": 0.02,
        "confidence": 0.9,
        "riskScore": 0.2,
    }
    decision.update(overrides)
    return decision


def _truth_envelope(*, caller: str = "PerformanceTruthEngine", authority: str = "DeterministicPaperBrokerage", source_event_id: str = "PBE-IFVR-001") -> object:
    return make_paper_operational_truth_envelope(
        originating_authority=authority,
        originating_workflow_id="WF-IFVR-001",
        workflow_token_id="TOKEN-IFVR-001",
        mission_id="MISSION-IFVR-001",
        source_event_id=source_event_id,
        idempotency_key=source_event_id,
        timestamp_utc=TIMESTAMP,
        caller=caller,
    )


def _broker_order() -> dict[str, object]:
    return {
        "order_id": "ORDER-IFVR-001",
        "status": "settled",
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
        "requested_quantity": 10,
        "filled_quantity": 10,
        "remaining_quantity": 0,
        "average_fill_price": 100.02,
        "ticket": {
            "workflow_id": "WF-IFVR-001",
            "mission_id": "MISSION-IFVR-001",
            "workflow_token": "TOKEN-IFVR-001",
            "decision_object_id": "DO-IFVR-001",
            "strategy_id": "IFVR Phase III.5",
            "symbol": "AAPL",
            "asset_type": "stock",
            "side": "buy",
            "order_type": "market",
            "time_in_force": "day",
            "quantity": 10,
            "risk_approval_id": "RISK-IFVR-001",
            "policy_approval_id": "POLICY-IFVR-001",
            "trader_identity": "Trader",
            "account_id": "ACCT-PAPER-001",
            "decision_object": _decision_object(),
        },
        "market_state": {"bid": 100.0, "ask": 100.02, "last": 100.01, "volume": 100000, "session": "REGULAR"},
        "fills": ({"fill_id": "FILL-IFVR-001", "quantity": 10, "price": 100.02, "commission": 0, "slippage": 0.01},),
    }


def _closed_position_payloads() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    position_registry = {
        "allPositions": (
            {
                "position_id": "POS-IFVR-001",
                "workflow_id": "WF-IFVR-001",
                "decision_object_id": "DO-IFVR-001",
                "symbol": "AAPL",
                "asset_type": "STOCK",
                "side": "LONG",
                "quantity": 0.0,
                "lifecycle_status": "closed",
                "entry_time": "2026-07-13T14:30:00Z",
                "updated_at": "2026-07-13T14:45:00Z",
                "entry_thesis": "IFVR lifecycle fixture",
                "current_risk": 10.0,
            },
        )
    }
    performance_truth = {
        "orderLedger": (
            {"order_id": "BUY-IFVR-001", "symbol": "AAPL", "decision_object_id": "DO-IFVR-001", "status": "FILLED", "side": "BUY", "filled_quantity": 10.0, "average_fill_price": 100.0, "timestamp": "2026-07-13T14:30:00Z", "slippage": 0.0, "spread_cost": 0.0, "realized_profit_loss": 0.0},
            {"order_id": "SELL-IFVR-001", "symbol": "AAPL", "decision_object_id": "DO-IFVR-001", "status": "SETTLED", "side": "SELL", "filled_quantity": 10.0, "average_fill_price": 110.0, "timestamp": "2026-07-13T14:45:00Z", "slippage": 0.0, "spread_cost": 0.0, "realized_profit_loss": 100.0},
        )
    }
    surveillance = {"surveillanceSnapshots": ({"snapshot_id": "SURV-IFVR-001", "position_id": "POS-IFVR-001", "unrealized_pnl": 5.0, "detected_events": ()},)}
    exit_decision = {"exitDecisionRecords": ({"exit_decision_id": "EXIT-IFVR-001", "position_id": "POS-IFVR-001", "trigger_type": "target_reached"},)}
    return position_registry, performance_truth, surveillance, exit_decision


class IFVR001Phase35TruthEnvelopeTests(unittest.TestCase):
    def test_operational_truth_envelope_rejects_missing_proof_simulation_and_degraded_inputs(self) -> None:
        missing = validate_operational_truth_envelope(None, target_authority="PerformanceTruthEngine")
        self.assertFalse(missing.valid)
        self.assertIn("MISSING_TRUTH_ENVELOPE", missing.codes)

        proof = dict(_truth_envelope().__dict__, truth_domain="PROOF", truth_classification=TruthClassification.PROOF_ONLY.value)
        self.assertIn("PROOF_MODE_NOT_ACTIONABLE", validate_operational_truth_envelope(proof, target_authority="PerformanceTruthEngine").codes)

        simulation = dict(_truth_envelope().__dict__, truth_domain="SIMULATION", truth_classification=TruthClassification.SIMULATION_ONLY.value)
        self.assertIn("SIMULATION_VALUE_IN_OPERATIONAL_PATH", validate_operational_truth_envelope(simulation, target_authority="PerformanceTruthEngine").codes)

        degraded = dict(_truth_envelope().__dict__, degraded=True)
        self.assertIn("DEGRADED_TRUTH_NOT_AUTHORITATIVE", validate_operational_truth_envelope(degraded, target_authority="PerformanceTruthEngine").codes)

    def test_decision_object_operational_path_rejects_non_operational_truth(self) -> None:
        self.assertTrue(validate_decision_object_for_operational_truth(_decision_object(), execution_environment="paper").valid)

        proof = validate_decision_object_for_operational_truth(_decision_object(executionMode="PROOF", truthClassification=TruthClassification.PROOF_ONLY.value), execution_environment="paper")
        self.assertIn("PROOF_MODE_NOT_ACTIONABLE", proof.codes)

        simulation = validate_decision_object_for_operational_truth(_decision_object(executionMode="SIMULATION", truthClassification=TruthClassification.SIMULATION_ONLY.value), execution_environment="paper")
        self.assertIn("SIMULATION_VALUE_IN_OPERATIONAL_PATH", simulation.codes)

        uncertified = validate_decision_object_for_operational_truth(_decision_object(certificationStatus="UNCERTIFIED"), execution_environment="paper")
        self.assertIn("UNCERTIFIED_DECISION_OBJECT", uncertified.codes)

    def test_performance_truth_requires_valid_broker_envelope_before_ledger_mutation(self) -> None:
        engine = PerformanceTruthEngine()
        rejected = engine.record_broker_authoritative_order(_broker_order())

        self.assertFalse(rejected["accepted"])
        self.assertEqual("TRUTH_ENVELOPE_REJECTED", rejected["reason"])
        self.assertEqual(0, len(engine.snapshot(execution_environment="paper")["orderLedger"]))

        accepted = engine.record_broker_authoritative_order(_broker_order(), truth_envelope=_truth_envelope())
        duplicate = engine.record_broker_authoritative_order(_broker_order(), truth_envelope=_truth_envelope())
        truth = engine.snapshot(execution_environment="paper")

        self.assertTrue(accepted["accepted"])
        self.assertTrue(duplicate["idempotent"])
        self.assertEqual(1, len(truth["orderLedger"]))
        self.assertEqual(1, truth["integrity"]["syntheticTruthRejected"])

    def test_persistence_rejects_operational_snapshots_without_valid_envelope(self) -> None:
        store = DurableEnterprisePersistenceStore()
        with self.assertRaises(EnterprisePersistenceError):
            store.persist_authoritative(ObjectType.ENTERPRISE_BROKER_STATE, "paper-broker", {"orders": ()})

        record = store.persist_authoritative(
            ObjectType.ENTERPRISE_BROKER_STATE,
            "paper-broker",
            {"orders": ()},
            truth_envelope=_truth_envelope(caller="DurableEnterprisePersistenceStore"),
        )

        self.assertEqual("paper-broker", record.object_id)
        self.assertEqual(ProvenanceStatus.VALIDATED.value, record.payload["operational_truth_envelope"]["provenance_status"])

    def test_degraded_closed_position_output_is_analytical_only_and_not_learning_promoted(self) -> None:
        position_registry, performance_truth, surveillance, exit_decision = _closed_position_payloads()
        state = ClosedPositionTruthBuilder().build(
            position_registry=position_registry,
            performance_truth=performance_truth,
            position_surveillance=surveillance,
            exit_decision_engine=exit_decision,
            enterprise_benchmark_engine={},
            timestamp_utc=TIMESTAMP,
        )

        self.assertEqual(0, state["metrics"]["truthRecordCount"])
        self.assertEqual(1, state["metrics"]["degradedAnalyticalRecordCount"])
        self.assertEqual(0, state["metrics"]["learningEventCount"])
        self.assertFalse(state["degradedAnalyticalRecords"][0]["learning_promotion_allowed"])

    def test_read_only_runtime_and_compatibility_routes_do_not_create_authoritative_state(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        before = runtime.read_only_digest()
        for _ in range(3):
            runtime.read_only_snapshot()
        self.assertEqual(before, runtime.read_only_digest())

        source = inspect.getsource(server.run)
        self.assertIn("get_server_runtime_provider()", source)
        self.assertIn("/api/proof/paper/start", source)
        self.assertIn("/api/paper/start", source)


if __name__ == "__main__":
    unittest.main()
