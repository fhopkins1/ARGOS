from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import (  # noqa: E402
    EnterpriseCommunicationsBus,
    EnterprisePositionLifecycleManager,
    MarketDataProviderAbstractionLayer,
    PerformanceTruthEngine,
    WorkflowExecutionToken,
)
from argos.foundation.audit import AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.contracts import utc_timestamp  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.trader import DeterministicPaperBrokerage, OrderManagementOffice, PaperBrokerAccount, PaperBrokerMarketDataAdapter, PaperBrokerOrderTicket  # noqa: E402


def config() -> ConfigurationService:
    return ConfigurationService.load(
        {
            "environment": "development",
            "config_version": "1.0.0",
            "schema_version": "1.0.0",
            "log_level": "INFO",
            "live_trading_enabled": False,
            "feature_flags": {},
            "secret_references": [],
        },
        {},
    )


def token(owner: str = "Trader") -> WorkflowExecutionToken:
    return WorkflowExecutionToken("WF-004", owner, "Executive", "Performance Truth", "Trader", 3600, 10.0, ("position_lifecycle",), "TOK-004", utc_timestamp(), 4, "Executing")


def decision() -> dict[str, object]:
    provenance = {
        "asset_identifier": "AAPL",
        "asset_class": "equity",
        "direction": "buy",
        "thesis": "OR-004 supervised paper position",
        "evidence": "Authorized office judgment",
        "market_context": "controlled authoritative quote",
        "entry_conditions": "broker executable",
        "price_source": "controlled-authoritative",
        "quantity": "2",
        "position_sizing_basis": "cash",
        "confidence": "0.7",
        "time_horizon": "day",
        "risk_factors": "documented",
        "stop_conditions": "documented",
        "exit_conditions": "profit target",
        "expected_return": "0.01",
        "risk_approval": "Authorized office judgment",
        "trader_authorization": "Authorized office judgment",
    }
    return {
        "decisionObjectId": "DO-OR004",
        "office": "Trader",
        "sourceSystem": "Trader",
        "executionMode": "PAPER",
        "truthClassification": "PAPER_OPERATIONAL",
        "certificationStatus": "PAPER_OPERATIONAL_CERTIFIED",
        "materialFieldProvenance": provenance,
        "recommendation": "BUY",
        "targetPrice": 501.0,
        "stopLoss": 480.0,
        "riskScore": 0.2,
        "confidence": 0.72,
        "currentStrategy": "STRAT-004",
    }


class AAPLMarketDataProvider(MarketDataProviderAbstractionLayer):
    def __init__(self) -> None:
        timestamp = utc_timestamp()
        configured = MarketDataProviderAbstractionLayer.with_controlled_authoritative_provider(
            observations={
                "AAPL": {"symbol": "AAPL", "bid": "502.24", "ask": "502.26", "last": "502.25", "volume": "1000000", "venue": "NASDAQ", "source_timestamp_utc": timestamp},
                "MARKET": {"symbol": "MARKET", "status": "PAPER_OPEN", "venue": "US", "source_timestamp_utc": timestamp},
            }
        )
        super().__init__(gateway=configured.gateway, provider_id="controlled-authoritative")

    def snapshot(self, *, timestamp_utc: str, workflow_id: str = "", decision_object_id: str = "") -> dict[str, object]:
        quote = self.get_quote("AAPL", timestamp_utc, workflow_id=workflow_id, decision_object_id=decision_object_id)["normalizedObject"]
        return {"normalizedObjects": {"quotes": (quote,), "marketStatus": ({"status": "PAPER_OPEN", "timestamp": timestamp_utc},)}}


def open_ticket(quantity: float = 2.0) -> PaperBrokerOrderTicket:
    return PaperBrokerOrderTicket(
        order_id="ORD-OR004-OPEN",
        workflow_id="WF-004",
        mission_id="MISSION-004",
        decision_object_id="DO-OR004",
        workflow_token="TOK-004",
        trader_identity="Trader",
        account_id="ACCT-PAPER-001",
        symbol="AAPL",
        asset_type="equity",
        side="buy",
        quantity=quantity,
        order_type="market",
        time_in_force="day",
        risk_approval_id="DOC-3702",
        policy_approval_id="POLICY-004",
        strategy_id="STRAT-004",
        execution_plan_id="EXP-004",
        decision_object=decision(),
    )


class PositionLifecycleTests(unittest.TestCase):
    def make_manager(self) -> tuple[EnterprisePositionLifecycleManager, DeterministicPaperBrokerage, EnterpriseCommunicationsBus, PerformanceTruthEngine]:
        bus = EnterpriseCommunicationsBus()
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        omo = OrderManagementOffice(config(), persistence, audit, PromptRepository())
        truth = PerformanceTruthEngine(paper_starting_cash=100000.0)
        broker = DeterministicPaperBrokerage(
            order_management=omo,
            performance_truth=truth,
            communications_bus=bus,
            market_data=PaperBrokerMarketDataAdapter(AAPLMarketDataProvider()),
            account=PaperBrokerAccount("ACCT-PAPER-001", 100000.0),
        )
        manager = EnterprisePositionLifecycleManager(
            performance_truth=truth,
            paper_broker=broker,
            market_data_provider=AAPLMarketDataProvider(),
            communications_bus=bus,
        )
        return manager, broker, bus, truth

    def test_broker_fill_creates_supervised_position_with_lineage(self) -> None:
        manager, broker, _bus, _truth = self.make_manager()

        broker.submit_order(open_ticket(), workflow_token=token())
        position = manager.registry.position("POS-AAPL-DO-OR004")

        self.assertEqual(position.owner, "Enterprise")
        self.assertEqual(position.quantity, 2.0)
        self.assertEqual(position.lifecycle_status, "open")
        self.assertEqual(position.mission_id, "MISSION-004")
        self.assertEqual(position.workflow_token_lineage, ("TOK-004",))
        self.assertTrue(position.broker_order_ids)
        self.assertTrue(position.fill_ids)

    def test_exit_recommendation_and_authorization_do_not_close_position(self) -> None:
        manager, broker, _bus, _truth = self.make_manager()
        broker.submit_order(open_ticket(), workflow_token=token())

        monitoring = manager.monitor_positions(timestamp_utc="2026-07-09T15:00:00Z")
        exits = manager.evaluate_exits(surveillance=monitoring["surveillance"], timestamp_utc="2026-07-09T15:00:00Z")
        exit_decision = exits["latestDecisions"][0]
        authorization = manager.authorize_exit(
            exit_decision=exit_decision,
            decision_object=decision(),
            authorized_by="Executive",
            risk_approval_id="DOC-3702",
            policy_approval_id="POLICY-004",
            mission_id="MISSION-004",
        )
        position = manager.registry.position("POS-AAPL-DO-OR004")

        self.assertEqual(authorization.authorization_state, "authorized")
        self.assertEqual(position.lifecycle_status, "exit_pending")
        self.assertEqual(position.quantity, 2.0)
        self.assertEqual(position.pending_close_quantity, 2.0)

    def test_partial_and_full_closure_require_broker_confirmed_fills(self) -> None:
        manager, broker, _bus, truth = self.make_manager()
        broker.submit_order(open_ticket(), workflow_token=token())
        position_id = "POS-AAPL-DO-OR004"

        partial_exit = {
            "exit_decision_id": "EXD-PARTIAL",
            "position_id": position_id,
            "workflow_id": "WF-004",
            "decision_object_id": "DO-OR004",
            "recommended_quantity": 1.0,
        }
        partial_auth = manager.authorize_exit(exit_decision=partial_exit, decision_object=decision(), authorized_by="Executive", risk_approval_id="DOC-3702", policy_approval_id="POLICY-004", mission_id="MISSION-004")
        partial_result = manager.submit_authorized_exit(partial_auth, workflow_token=token(), decision_object=decision())
        partial_position = manager.registry.position(position_id)

        self.assertTrue(partial_result["accepted"])
        self.assertEqual(partial_position.quantity, 1.0)
        self.assertNotEqual(partial_position.lifecycle_status, "closed")
        self.assertEqual(truth.snapshot(execution_environment="paper")["closedPositionTruth"], ())

        full_exit = {
            "exit_decision_id": "EXD-FULL",
            "position_id": position_id,
            "workflow_id": "WF-004",
            "decision_object_id": "DO-OR004",
            "recommended_quantity": 1.0,
        }
        full_auth = manager.authorize_exit(exit_decision=full_exit, decision_object=decision(), authorized_by="Executive", risk_approval_id="DOC-3702", policy_approval_id="POLICY-004", mission_id="MISSION-004")
        manager.submit_authorized_exit(full_auth, workflow_token=token(), decision_object=decision())
        closed = manager.registry.position(position_id)
        reconciliation = manager.reconcile_position(position_id, exit_decision_state={"latestDecisions": (full_exit,)}, surveillance_state={})
        closed_truth = truth.snapshot(execution_environment="paper")["closedPositionTruth"]

        self.assertEqual(closed.quantity, 0.0)
        self.assertEqual(closed.lifecycle_status, "closed")
        self.assertEqual(reconciliation.status, "reconciled")
        self.assertEqual(len(closed_truth), 1)
        self.assertEqual(closed_truth[0]["position_id"], position_id)


if __name__ == "__main__":
    unittest.main()
