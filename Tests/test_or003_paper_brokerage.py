from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import EnterpriseCommunicationsBus, MarketDataProviderAbstractionLayer, PerformanceTruthEngine, PositionMonitoringNetwork, WorkflowExecutionToken  # noqa: E402
from argos.foundation.audit import AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.contracts import utc_timestamp  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.trader import (  # noqa: E402
    DeterministicPaperBrokerage,
    ExecutionOrderRequest,
    ExecutionQualityOffice,
    MarketState,
    OrderManagementOffice,
    PaperBrokerAccount,
    PaperBrokerMarketDataAdapter,
    PaperBrokerOrderTicket,
    PaperBrokerRejectionCode,
)


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


def token(owner: str = "Trader", status: str = "Executing") -> WorkflowExecutionToken:
    return WorkflowExecutionToken("WF-OR003", owner, "Executive", "Performance Truth", "Trader", 3600, 10.0, ("broker_order",), "TOK-OR003", utc_timestamp(), 4, status)


def decision() -> dict[str, object]:
    provenance = {
        "asset_identifier": "AAPL",
        "asset_class": "equity",
        "direction": "buy",
        "thesis": "Authorized paper test",
        "evidence": "Authorized office judgment",
        "market_context": "controlled authoritative quote",
        "entry_conditions": "broker executable",
        "price_source": "controlled-authoritative",
        "quantity": "1",
        "position_sizing_basis": "cash",
        "confidence": "0.7",
        "time_horizon": "day",
        "risk_factors": "documented",
        "stop_conditions": "documented",
        "exit_conditions": "documented",
        "expected_return": "0.01",
        "risk_approval": "Authorized office judgment",
        "trader_authorization": "Authorized office judgment",
    }
    return {
        "decisionObjectId": "DO-OR003",
        "office": "Trader",
        "sourceSystem": "Trader",
        "executionMode": "PAPER",
        "truthClassification": "PAPER_OPERATIONAL",
        "certificationStatus": "PAPER_OPERATIONAL_CERTIFIED",
        "materialFieldProvenance": provenance,
    }


def execution_request() -> ExecutionOrderRequest:
    return ExecutionOrderRequest(
        "EXP-003",
        "AAPL",
        1.0,
        "buy",
        "market",
        "PAPER",
        "ACCT-PAPER-001",
        "STRAT-OR003",
        "DOC-5201",
        "DOC-3702",
        "POS-OR003",
        1,
        "BROKER-PAPER-OR003",
        "PAPER",
    )


def ticket(**overrides) -> PaperBrokerOrderTicket:
    values = {
        "order_id": "ORD-000001",
        "workflow_id": "WF-OR003",
        "mission_id": "MISSION-OR003",
        "decision_object_id": "DO-OR003",
        "workflow_token": "TOK-OR003",
        "trader_identity": "Trader",
        "account_id": "ACCT-PAPER-001",
        "symbol": "AAPL",
        "asset_type": "equity",
        "side": "buy",
        "quantity": 1.0,
        "order_type": "market",
        "time_in_force": "day",
        "risk_approval_id": "DOC-3702",
        "policy_approval_id": "POLICY-OR003",
        "strategy_id": "STRAT-OR003",
        "execution_plan_id": "EXP-003",
        "decision_object": decision(),
    }
    values.update(overrides)
    return PaperBrokerOrderTicket(**values)


class ClosedMarketData(PaperBrokerMarketDataAdapter):
    def market_state(self, symbol: str, timestamp_utc: str, workflow_id: str, decision_object_id: str) -> MarketState:
        return MarketState(symbol, 100.0, 100.1, 100.05, 100000.0, "CLOSED", "test", timestamp_utc)


class PaperBrokerageTests(unittest.TestCase):
    def make_broker(self, market_data: PaperBrokerMarketDataAdapter | None = None) -> tuple[DeterministicPaperBrokerage, EnterpriseCommunicationsBus, PerformanceTruthEngine]:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        omo = OrderManagementOffice(config(), persistence, audit, PromptRepository())
        omo.create_order(execution_request(), "CF-001", "TC-001", 1, 3001)
        truth = PerformanceTruthEngine(paper_starting_cash=100000.0)
        broker = DeterministicPaperBrokerage(
            order_management=omo,
            execution_quality=ExecutionQualityOffice(config(), persistence, audit, PromptRepository()),
            performance_truth=truth,
            communications_bus=EnterpriseCommunicationsBus(),
            position_monitoring=PositionMonitoringNetwork(),
            market_data=market_data or PaperBrokerMarketDataAdapter(MarketDataProviderAbstractionLayer.with_controlled_authoritative_provider(observations={"AAPL": {"symbol": "AAPL", "bid": "502.24", "ask": "502.26", "last": "502.25", "volume": "1000000", "venue": "NASDAQ", "source_timestamp_utc": utc_timestamp()}, "MARKET": {"symbol": "MARKET", "status": "PAPER_OPEN", "venue": "US", "source_timestamp_utc": utc_timestamp()}})),
            account=PaperBrokerAccount("ACCT-PAPER-001", 100000.0),
        )
        return broker, broker.communications_bus, truth

    def test_market_order_fills_and_performance_truth_records_broker_event(self) -> None:
        broker, bus, truth = self.make_broker()

        result = broker.submit_order(ticket(), workflow_token=token())

        self.assertTrue(result.accepted)
        self.assertEqual(result.order.status, "settled")
        self.assertEqual(result.order.filled_quantity, 1.0)
        self.assertTrue(any(event.event_type == "Fill" for event in result.events))
        snapshot = truth.snapshot(execution_environment="paper")
        self.assertEqual(len(snapshot["orderLedger"]), 1)
        self.assertEqual(snapshot["orderLedger"][0]["order_id"], "ORD-000001")
        self.assertTrue(snapshot["integrity"]["paperLiveIsolated"])
        self.assertGreaterEqual(bus.snapshot()["metrics"]["messagesPublished"], 1)

    def test_invalid_workflow_owner_rejects_without_fill(self) -> None:
        broker, _bus, truth = self.make_broker()

        result = broker.submit_order(ticket(), workflow_token=token(owner="Risk"))

        self.assertFalse(result.accepted)
        self.assertEqual(result.rejection_code, PaperBrokerRejectionCode.INVALID_WORKFLOW_OWNER.value)
        self.assertEqual(result.order.fills, ())
        self.assertEqual(len(truth.snapshot(execution_environment="paper")["orderLedger"]), 0)

    def test_non_executable_limit_order_does_not_fabricate_fill(self) -> None:
        broker, _bus, truth = self.make_broker(ClosedMarketData())

        result = broker.submit_order(ticket(order_type="limit", limit_price=90.0), workflow_token=token())

        self.assertTrue(result.accepted)
        self.assertEqual(result.order.status, "queued")
        self.assertEqual(result.order.filled_quantity, 0.0)
        self.assertEqual(result.order.fills, ())
        self.assertEqual(len(truth.snapshot(execution_environment="paper")["orderLedger"]), 0)


if __name__ == "__main__":
    unittest.main()
