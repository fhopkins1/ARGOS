from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.contracts import utc_timestamp  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.trader import (  # noqa: E402
    AlertPriority,
    BrokerConnectionStatus,
    BrokerHealthStatus,
    EnterpriseReadiness,
    ExecutionOrderRequest,
    ExecutionQualityMetrics,
    OrderManagementOffice,
    PositionExecutionEvent,
    PositionManagementOffice,
    SystemHealthSnapshot,
    TraderFusionOffice,
    TraderFusionSnapshot,
    TradeMonitoringAlert,
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
    return ExecutionOrderRequest("EXP-059", "AAPL", 100.0, "buy", "limit", "NASDAQ", "ACCT-1", "STRAT-059", "DOC-5201", "DOC-3702", "POS-059", 1, "BROKER-PAPER", "NASDAQ")


def execution_event() -> PositionExecutionEvent:
    return PositionExecutionEvent("EXEC-EVT-059", "ORD-000001", "POS-059", "AAPL", "PORT-059", "STRAT-059", "DOC-5201", 100.0, 100.0, "buy", "2026-07-04T00:00:00Z", "DOC-5502")


def quality_metrics() -> ExecutionQualityMetrics:
    return ExecutionQualityMetrics(100.0, 100.1, 100.0, 0.1, 0.02, 1.0, 20, 200, 1.0, 0.1, 0.01, 0.98, 0.99)


def monitoring_alert(classification: str = "broker_disconnects", severity: AlertPriority = AlertPriority.CRITICAL) -> TradeMonitoringAlert:
    return TradeMonitoringAlert("TMA-TEST", severity, utc_timestamp(), "Trade Monitoring Office", ("BROKER-PAPER",), (classification,), "notify_executive", "active", True)


def healthy_snapshot() -> TraderFusionSnapshot:
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    omo = OrderManagementOffice(config(), persistence, audit, PromptRepository())
    omo.create_order(order_request(), "CF-001", "TC-001", 1, 5901)
    pmo = PositionManagementOffice(config(), persistence, audit, PromptRepository())
    pmo.apply_execution_event(execution_event(), 100.0, "CF-001", "TC-001", 5902)
    return TraderFusionSnapshot(
        "TFS-HEALTHY",
        ("EXP-059",),
        (omo.managed_order("ORD-000001"),),
        (pmo.position("POS-059"),),
        pmo.publish_portfolio_state("PORT-059"),
        (BrokerHealthStatus("BROKER-PAPER", BrokerConnectionStatus.CONNECTED, "authenticated", True, 20, 30, True, 100, True, True),),
        ("ORD-000001",),
        (quality_metrics(),),
        (),
        SystemHealthSnapshot(100, "healthy", 10.0, 0.4, True),
        "contained",
        ("HIST-059",),
    )


class TraderFusionOfficeTests(unittest.TestCase):
    def test_fusion_assessment_and_summary_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = TraderFusionOffice(config(), persistence, audit, PromptRepository())

        artifacts = office.fuse(healthy_snapshot(), "CF-001", "TC-001", 5905)

        self.assertIn("trader_fusion_assessment", artifacts)
        self.assertIn("enterprise_execution_summary", artifacts)
        self.assertNotIn("trader_fusion_case_file", artifacts)
        assessment = artifacts["trader_fusion_assessment"]
        summary = artifacts["enterprise_execution_summary"].machine_payload["enterprise_execution_summary"]
        self.assertEqual(assessment.contract_type, "TRADER_FUSION_ASSESSMENT")
        self.assertEqual(summary["enterprise_readiness"], EnterpriseReadiness.READY.value)
        self.assertEqual(summary["trader_operational_health"], "healthy")
        self.assertTrue(assessment.machine_payload["recommendations_advisory_only"])
        self.assertFalse(assessment.machine_payload["execution_history_modified"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, assessment.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_cross_office_inconsistencies_generate_case_file(self) -> None:
        snapshot = healthy_snapshot()
        inconsistent_snapshot = TraderFusionSnapshot(
            "TFS-INCONSISTENT",
            snapshot.execution_request_ids,
            snapshot.orders,
            (),
            snapshot.portfolio_state,
            snapshot.broker_health,
            (),
            (),
            snapshot.monitoring_alerts,
            snapshot.system_health,
            snapshot.risk_status,
            snapshot.historian_record_ids,
        )
        office = TraderFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = office.fuse(inconsistent_snapshot, "CF-001", "TC-001", 5910)

        self.assertIn("trader_fusion_case_file", artifacts)
        case_file = artifacts["trader_fusion_case_file"].machine_payload["case_file"]
        classifications = tuple(item["classification"] for item in case_file["anomalies"])
        self.assertIn("position_reconciliation_failures", classifications)
        self.assertIn("portfolio_inconsistencies", classifications)
        self.assertTrue(case_file["executive_group_notified"])

    def test_monitoring_alert_and_broker_degradation_reduce_readiness(self) -> None:
        snapshot = healthy_snapshot()
        degraded_snapshot = TraderFusionSnapshot(
            "TFS-DEGRADED",
            snapshot.execution_request_ids,
            snapshot.orders,
            snapshot.positions,
            snapshot.portfolio_state,
            (BrokerHealthStatus("BROKER-PAPER", BrokerConnectionStatus.DISCONNECTED, "expired", False, 1500, 1600, False, 0, False, False),),
            snapshot.execution_quality_order_ids,
            snapshot.execution_quality_metrics,
            (monitoring_alert(),),
            SystemHealthSnapshot(1500, "degraded", 1.0, 0.92, False),
            "elevated",
            snapshot.historian_record_ids,
        )

        artifacts = TraderFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository()).fuse(degraded_snapshot, "CF-001", "TC-001", 5920)

        summary = artifacts["enterprise_execution_summary"].machine_payload["enterprise_execution_summary"]
        classifications = tuple(item["classification"] for item in artifacts["trader_fusion_case_file"].machine_payload["case_file"]["anomalies"])
        self.assertEqual(summary["enterprise_readiness"], EnterpriseReadiness.NOT_READY.value)
        self.assertIn("broker_degradation", classifications)
        self.assertIn("enterprise_execution_risk", classifications)
        self.assertIn("capacity_constraints", classifications)

    def test_system_prompt_declares_fusion_boundaries(self) -> None:
        office = TraderFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()

        self.assertIn("Trader Fusion Office", prompt.prompt_text)
        self.assertIn("You do not determine what should be traded", prompt.prompt_text)
        self.assertIn("Every anomaly shall generate a Trader Fusion Case File", prompt.prompt_text)
        self.assertIn("Recommendations shall remain advisory", prompt.prompt_text)
        self.assertEqual(prompt.version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
