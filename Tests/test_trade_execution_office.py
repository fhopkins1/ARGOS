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
    ExecutionAuthorization,
    ExecutionFill,
    MarketConditionSnapshot,
    OrderManagementOffice,
    TradeExecutionOffice,
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


def authorization(**overrides) -> ExecutionAuthorization:
    values = {
        "cdr_id": "DOC-5201",
        "risk_certification_id": "DOC-3702",
        "approved_quantity": 100.0,
        "instrument_id": "AAPL",
        "direction": "buy",
        "expected_price": 100.0,
        "max_slippage_percent": 1.0,
        "execution_window_seconds": 600,
        "strategy_id": "STRAT-053B",
        "position_id": "POS-053B",
        "account_id": "ACCT-PAPER-001",
        "venue": "NASDAQ",
    }
    values.update(overrides)
    return ExecutionAuthorization(**values)


def market(**overrides) -> MarketConditionSnapshot:
    values = {
        "bid": 99.95,
        "ask": 100.05,
        "last_price": 100.0,
        "available_liquidity": 1000.0,
        "volatility_score": 0.25,
        "spread": 0.1,
        "market_open": True,
    }
    values.update(overrides)
    return MarketConditionSnapshot(**values)


def fills() -> tuple[ExecutionFill, ...]:
    return (
        ExecutionFill("FILL-001", "ORD-000001", 100.10, 40.0, "2026-07-04T00:00:01Z", "NASDAQ", 250, 0.1, 0.05, 1),
        ExecutionFill("FILL-002", "ORD-000001", 100.20, 60.0, "2026-07-04T00:00:02Z", "NASDAQ", 300, 0.1, 0.10, 2),
    )


class TradeExecutionOfficeTests(unittest.TestCase):
    def test_execution_plan_is_deterministic_and_traceable(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = TradeExecutionOffice(config(), persistence, audit, PromptRepository())

        report = office.generate_execution_plan(authorization(), market(), "CF-001", "TC-001", 5301)

        self.assertEqual(report.contract_type, "EXECUTION_PLAN")
        self.assertEqual(report.machine_payload["execution_plan"]["selected_methodology"], "standard_limit_execution")
        self.assertEqual(report.machine_payload["execution_plan"]["selected_venue"], "NASDAQ")
        self.assertIn("preserve_executive_intent", report.machine_payload["execution_plan"]["constraints"])
        self.assertIn("trade_authorization_verification_record", report.machine_payload)
        self.assertIn("venue_selection_record", report.machine_payload)
        self.assertIn("order_slicing_record", report.machine_payload)
        self.assertIn("deterministic_decision_trace", report.machine_payload)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_submission_goes_to_order_management_not_broker(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = TradeExecutionOffice(config(), persistence, audit, PromptRepository())
        omo = OrderManagementOffice(config(), persistence, audit, PromptRepository())

        submission = office.submit_to_order_management(authorization(), market(), omo, "CF-001", "TC-001", 1, 5302)

        self.assertEqual(submission.contract_type, "EXECUTION_SUBMISSION")
        self.assertFalse(submission.machine_payload["direct_broker_communication"])
        self.assertIn("execution_constraint_validation_record", submission.machine_payload)
        self.assertEqual(omo.managed_order("ORD-000001").request.execution_plan_id, "TEP-053B")

    def test_quality_slippage_cost_shortfall_and_case_file_are_generated(self) -> None:
        office = TradeExecutionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        reports = office.evaluate_execution(authorization(), market(), fills(), "CF-001", "TC-001", 5310)

        self.assertIn("execution_progress_report", reports)
        self.assertIn("execution_quality_report", reports)
        self.assertIn("completed_execution_report", reports)
        self.assertIn("execution_case_file", reports)
        quality = reports["execution_quality_report"].machine_payload
        self.assertAlmostEqual(quality["fill_quality"]["average_fill_price"], 100.16)
        self.assertAlmostEqual(quality["slippage"]["absolute_slippage"], 0.16)
        self.assertGreater(quality["transaction_costs"]["total_transaction_cost"], 0)
        self.assertIn("realized_implementation_shortfall", quality["implementation_shortfall"])
        self.assertIn("execution_state_history", quality)
        self.assertIn("fill_history", quality)
        self.assertIn("execution_audit_log", quality)
        self.assertFalse(quality["investment_performance_evaluated"])
        case_file = reports["execution_case_file"].machine_payload
        self.assertIn("execution_performance_dataset", case_file)
        self.assertIn("execution_event_archive", case_file)
        self.assertIn("organizational_policy_compliance_record", case_file)

    def test_execution_exception_and_recovery_are_generated_for_excessive_slippage(self) -> None:
        office = TradeExecutionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        bad_fills = (ExecutionFill("FILL-003", "ORD-000001", 103.0, 100.0, "2026-07-04T00:00:03Z", "NASDAQ", 7000, 0.5, 3.0, 1),)

        reports = office.evaluate_execution(authorization(max_slippage_percent=0.5), market(spread=0.5), bad_fills, "CF-001", "TC-001", 5320)

        self.assertIn("execution_exception_report", reports)
        exceptions = reports["execution_exception_report"].machine_payload["exceptions"]
        self.assertTrue(any(item["classification"] == "excessive_slippage" for item in exceptions))
        self.assertTrue(reports["execution_exception_report"].machine_payload["executive_notification_record"]["required"])
        self.assertIn("execution_recovery_record", reports["execution_exception_report"].machine_payload)
        self.assertTrue(reports["execution_exception_report"].machine_payload["required_approvals"])

    def test_order_slicing_preserves_traceability_for_large_low_liquidity_order(self) -> None:
        office = TradeExecutionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        report = office.generate_execution_plan(
            authorization(approved_quantity=1000.0),
            market(available_liquidity=1200.0, volatility_score=0.8),
            "CF-001",
            "TC-001",
            5325,
        )

        slices = report.machine_payload["order_slicing_record"]["slices"]
        self.assertEqual(len(slices), 4)
        self.assertTrue(all(item["source_cdr_id"] == "DOC-5201" for item in slices))
        self.assertEqual(sum(item["quantity"] for item in slices), 1000.0)

    def test_closed_market_blocks_submission(self) -> None:
        office = TradeExecutionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        omo = OrderManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        with self.assertRaises(ValueError):
            office.submit_to_order_management(authorization(), market(market_open=False), omo, "CF-001", "TC-001", 2, 5330)

    def test_invalid_authorization_is_rejected(self) -> None:
        office = TradeExecutionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        with self.assertRaises(ValueError):
            office.generate_execution_plan(authorization(cdr_id="CDR-DECISION-001"), market(), "CF-001", "TC-001", 5340)


if __name__ == "__main__":
    unittest.main()
