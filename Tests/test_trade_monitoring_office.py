from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.trader import (  # noqa: E402
    BrokerConnectionStatus,
    BrokerHealthStatus,
    ExecutionOrderRequest,
    MarketStatusSnapshot,
    OrderLifecycleState,
    OrderManagementOffice,
    PositionExecutionEvent,
    PositionManagementOffice,
    SystemHealthSnapshot,
    TradeMonitoringOffice,
    TradeMonitoringSnapshot,
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


def order_request() -> ExecutionOrderRequest:
    return ExecutionOrderRequest("EXP-058", "AAPL", 100.0, "buy", "limit", "NASDAQ", "ACCT-1", "STRAT-058", "DOC-5201", "DOC-3702", "POS-058", 1, "BROKER-PAPER", "NASDAQ")


def execution_event(quantity: float = 100.0) -> PositionExecutionEvent:
    return PositionExecutionEvent("EXEC-EVT-058", "ORD-000001", "POS-058", "AAPL", "PORT-058", "STRAT-058", "DOC-5201", quantity, 100.0, "buy", "2026-07-04T00:00:00Z", "DOC-5502")


def healthy_snapshot() -> TradeMonitoringSnapshot:
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    omo = OrderManagementOffice(config(), persistence, audit, PromptRepository())
    omo.create_order(order_request(), "CF-001", "TC-001", 1, 5801)
    pmo = PositionManagementOffice(config(), persistence, audit, PromptRepository())
    pmo.apply_execution_event(execution_event(), 100.0, "CF-001", "TC-001", 5802)
    return TradeMonitoringSnapshot(
        "TMS-HEALTHY",
        (omo.managed_order("ORD-000001"),),
        (pmo.position("POS-058"),),
        pmo.publish_portfolio_state("PORT-058"),
        (BrokerHealthStatus("BROKER-PAPER", BrokerConnectionStatus.CONNECTED, "authenticated", True, 20, 30, True, 100, True, True),),
        MarketStatusSnapshot(True, "NASDAQ", "regular", True),
        SystemHealthSnapshot(100, "healthy", 10.0, 0.4, True),
        "contained",
        "normal",
    )


class TradeMonitoringOfficeTests(unittest.TestCase):
    def test_monitoring_report_and_dashboard_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = TradeMonitoringOffice(config(), persistence, audit, PromptRepository())

        reports = office.monitor(healthy_snapshot(), "CF-001", "TC-001", 5805)

        self.assertIn("trade_monitoring_report", reports)
        self.assertIn("trade_monitoring_dashboard", reports)
        report = reports["trade_monitoring_report"]
        dashboard = reports["trade_monitoring_dashboard"].machine_payload["dashboard"]
        self.assertEqual(report.contract_type, "TRADE_MONITORING_REPORT")
        self.assertFalse(report.machine_payload["history_discarded"])
        self.assertFalse(report.machine_payload["anomalies_suppressed"])
        self.assertEqual(dashboard["trader_group_health"], "healthy")
        self.assertEqual(dashboard["order_status"]["queued"], 1)
        self.assertEqual(len(office.monitoring_history), 5)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_critical_alerts_generate_case_file_and_notify_executive(self) -> None:
        snapshot = healthy_snapshot()
        bad_snapshot = TradeMonitoringSnapshot(
            "TMS-BAD",
            snapshot.orders,
            snapshot.positions,
            snapshot.portfolio_state,
            (BrokerHealthStatus("BROKER-PAPER", BrokerConnectionStatus.DISCONNECTED, "expired", False, 1500, 1600, False, 0, False, False),),
            MarketStatusSnapshot(True, "NASDAQ", "regular", False, market_halt=True),
            SystemHealthSnapshot(2000, "degraded", 1.0, 0.95, False),
            "elevated",
            "attention",
        )
        office = TradeMonitoringOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        reports = office.monitor(bad_snapshot, "CF-001", "TC-001", 5810)

        self.assertIn("trade_monitoring_case_file", reports)
        case_file = reports["trade_monitoring_case_file"].machine_payload
        alert_evidence = tuple(alert["supporting_evidence"][0] for alert in case_file["case_file"]["alerts"])
        self.assertIn("broker_disconnects", alert_evidence)
        self.assertIn("market_halts", alert_evidence)
        self.assertIn("infrastructure_failures", alert_evidence)
        self.assertTrue(case_file["executive_group_notified"])

    def test_stalled_order_and_missing_broker_response_are_detected(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        omo = OrderManagementOffice(config(), persistence, audit, PromptRepository())
        omo.create_order(order_request(), "CF-001", "TC-001", 2, 5820)
        omo.transition_order("ORD-000002", OrderLifecycleState.SUBMITTED, "broker_submission", "Submitted without acknowledgement.", "CF-001", "TC-001", 5821)
        pmo = PositionManagementOffice(config(), persistence, audit, PromptRepository())
        pmo.apply_execution_event(execution_event(), 100.0, "CF-001", "TC-001", 5822)
        snapshot = TradeMonitoringSnapshot(
            "TMS-STALLED",
            (omo.managed_order("ORD-000002"),),
            (pmo.position("POS-058"),),
            pmo.publish_portfolio_state("PORT-058"),
            (BrokerHealthStatus("BROKER-PAPER", BrokerConnectionStatus.CONNECTED, "authenticated", True, 20, 30, True, 100, True, True),),
            MarketStatusSnapshot(True, "NASDAQ", "regular", True),
            SystemHealthSnapshot(100, "healthy", 10.0, 0.4, True),
            "contained",
            "normal",
        )
        office = TradeMonitoringOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        reports = office.monitor(snapshot, "CF-001", "TC-001", 5823)

        alerts = reports["trade_monitoring_case_file"].machine_payload["case_file"]["alerts"]
        evidence = tuple(alert["supporting_evidence"][0] for alert in alerts)
        self.assertIn("stalled_orders", evidence)
        self.assertIn("missing_broker_responses", evidence)

    def test_position_limit_violation_and_dashboard_active_alerts(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        omo = OrderManagementOffice(config(), persistence, audit, PromptRepository())
        omo.create_order(order_request(), "CF-001", "TC-001", 3, 5830)
        pmo = PositionManagementOffice(config(), persistence, audit, PromptRepository())
        pmo.apply_execution_event(execution_event(quantity=20000.0), 100.0, "CF-001", "TC-001", 5831)
        snapshot = TradeMonitoringSnapshot(
            "TMS-LIMIT",
            (omo.managed_order("ORD-000003"),),
            (pmo.position("POS-058"),),
            pmo.publish_portfolio_state("PORT-058"),
            (BrokerHealthStatus("BROKER-PAPER", BrokerConnectionStatus.CONNECTED, "authenticated", True, 20, 30, True, 100, True, True),),
            MarketStatusSnapshot(True, "NASDAQ", "regular", True),
            SystemHealthSnapshot(100, "healthy", 10.0, 0.4, True),
            "contained",
            "normal",
        )

        reports = TradeMonitoringOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository()).monitor(snapshot, "CF-001", "TC-001", 5832)

        dashboard = reports["trade_monitoring_dashboard"].machine_payload["dashboard"]
        self.assertEqual(dashboard["trader_group_health"], "critical")
        self.assertTrue(dashboard["active_alerts"])

    def test_system_prompt_declares_monitoring_boundary(self) -> None:
        office = TradeMonitoringOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()

        self.assertIn("Trade Monitoring Office", prompt.prompt_text)
        self.assertIn("You do not determine what should be traded", prompt.prompt_text)
        self.assertIn("Every detected anomaly shall generate a Trade Monitoring Case File", prompt.prompt_text)
        self.assertIn("Critical alerts shall immediately notify the Executive Group", prompt.prompt_text)
        self.assertIn("Never discard monitoring history", prompt.prompt_text)
        self.assertEqual(prompt.version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
