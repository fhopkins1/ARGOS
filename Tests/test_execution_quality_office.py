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
from argos.trader import CompletedExecutionRecord, ExecutionQualityOffice  # noqa: E402


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


def execution_record(**overrides) -> CompletedExecutionRecord:
    values = {
        "execution_record_id": "EXREC-056",
        "executive_decision_id": "DOC-5201",
        "execution_strategy_id": "STRAT-056",
        "order_id": "ORD-000001",
        "broker_id": "BROKER-PAPER",
        "broker_execution_id": "EXEC-ORD-000001",
        "market_condition_id": "MKT-056",
        "position_id": "POS-056",
        "audit_id": "DOC-5502",
        "requested_price": 100.0,
        "requested_quantity": 100.0,
        "average_fill_price": 100.1,
        "filled_quantity": 100.0,
        "best_available_market_price": 100.0,
        "bid_ask_spread": 0.1,
        "fill_latency_ms": 300,
        "order_completion_time_ms": 900,
        "commission_cost": 0.5,
        "fees": 0.2,
        "realized_market_impact": 0.05,
        "asset_class": "equity",
        "exchange": "NASDAQ",
        "liquidity_regime": "normal",
        "volatility_regime": "contained",
        "time_of_day": "regular_session_open",
        "order_type": "limit",
    }
    values.update(overrides)
    return CompletedExecutionRecord(**values)


class ExecutionQualityOfficeTests(unittest.TestCase):
    def test_execution_quality_report_and_historian_dataset_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = ExecutionQualityOffice(config(), persistence, audit, PromptRepository())

        reports = office.evaluate_execution(execution_record(), "CF-001", "TC-001", 5601)

        self.assertIn("execution_quality_report", reports)
        self.assertIn("execution_quality_historian_dataset", reports)
        report = reports["execution_quality_report"]
        self.assertEqual(report.contract_type, "EXECUTION_QUALITY")
        self.assertAlmostEqual(report.machine_payload["metrics"]["slippage"], 0.1)
        self.assertEqual(report.machine_payload["comparison"]["broker_id"], "BROKER-PAPER")
        self.assertEqual(report.machine_payload["trace"]["executive_decision_id"], "DOC-5201")
        self.assertFalse(report.machine_payload["execution_behavior_modified"])
        self.assertFalse(report.machine_payload["history_overwritten"])
        self.assertFalse(report.machine_payload["statistics_discarded"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_anomalies_generate_case_file_and_nonautomatic_recommendations(self) -> None:
        office = ExecutionQualityOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        poor = execution_record(
            average_fill_price=104.0,
            filled_quantity=50.0,
            fill_latency_ms=8000,
            commission_cost=80.0,
            fees=40.0,
            realized_market_impact=3.5,
        )

        reports = office.evaluate_execution(poor, "CF-001", "TC-001", 5610)

        self.assertIn("execution_quality_case_file", reports)
        case_file = reports["execution_quality_case_file"].machine_payload["case_file"]
        classifications = tuple(item["classification"] for item in case_file["anomalies"])
        self.assertIn("excessive_slippage", classifications)
        self.assertIn("poor_fill_quality", classifications)
        self.assertIn("latency_spike", classifications)
        recommendations = reports["execution_quality_case_file"].machine_payload["recommendations"]
        self.assertTrue(all(item["historian_validation_required"] for item in recommendations))
        self.assertTrue(all(item["automatically_alters_execution"] is False for item in recommendations))
        self.assertTrue(case_file["reconstructable"])

    def test_comparison_dimensions_cover_enterprise_quality_axes(self) -> None:
        office = ExecutionQualityOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        report = office.evaluate_execution(
            execution_record(asset_class="option", exchange="CBOE", liquidity_regime="thin", volatility_regime="elevated", time_of_day="close", order_type="market"),
            "CF-001",
            "TC-001",
            5620,
        )["execution_quality_report"]

        comparison = report.machine_payload["comparison"]
        self.assertEqual(comparison["asset_class"], "option")
        self.assertEqual(comparison["exchange"], "CBOE")
        self.assertEqual(comparison["liquidity_regime"], "thin")
        self.assertEqual(comparison["volatility_regime"], "elevated")
        self.assertEqual(comparison["time_of_day"], "close")
        self.assertEqual(comparison["order_type"], "market")

    def test_system_prompt_declares_scientific_evaluation_boundary(self) -> None:
        office = ExecutionQualityOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()

        self.assertIn("Execution Quality Office", prompt.prompt_text)
        self.assertIn("Do not determine what should be traded", prompt.prompt_text)
        self.assertEqual(prompt.version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
