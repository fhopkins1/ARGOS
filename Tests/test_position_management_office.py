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
from argos.trader import BrokerPositionRecord, PositionExecutionEvent, PositionLifecycleState, PositionManagementOffice  # noqa: E402


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


def execution_event(**overrides) -> PositionExecutionEvent:
    values = {
        "execution_event_id": "EXEC-EVT-057",
        "order_id": "ORD-000001",
        "position_id": "POS-057",
        "asset_identifier": "AAPL",
        "portfolio_id": "PORT-001",
        "strategy_id": "STRAT-057",
        "executive_decision_id": "DOC-5201",
        "quantity": 100.0,
        "price": 100.0,
        "side": "buy",
        "timestamp_utc": "2026-07-04T00:00:00Z",
        "audit_id": "DOC-5502",
        "asset_class": "equity",
    }
    values.update(overrides)
    return PositionExecutionEvent(**values)


class PositionManagementOfficeTests(unittest.TestCase):
    def test_execution_event_creates_position_and_portfolio_state(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = PositionManagementOffice(config(), persistence, audit, PromptRepository())

        artifacts = office.apply_execution_event(execution_event(), 102.0, "CF-001", "TC-001", 5701)
        position = office.position("POS-057")

        self.assertIn("position_record", artifacts)
        self.assertIn("portfolio_state", artifacts)
        self.assertEqual(position.position_status, PositionLifecycleState.CREATED)
        self.assertEqual(position.average_cost_basis, 100.0)
        self.assertEqual(position.quantity, 100.0)
        self.assertEqual(position.market_value, 10200.0)
        self.assertEqual(position.unrealized_pnl, 200.0)
        self.assertEqual(position.exposure, 10200.0)
        self.assertEqual(position.history[-1].audit_id, "DOC-5502")
        self.assertTrue(artifacts["position_record"].machine_payload["position_reconstructable"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["position_record"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(item.event_type for item in audit.audit_log.events))

    def test_existing_position_updates_cost_basis_and_realized_pnl(self) -> None:
        office = PositionManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        office.apply_execution_event(execution_event(quantity=100.0, price=100.0), 100.0, "CF-001", "TC-001", 5710)
        office.apply_execution_event(execution_event(execution_event_id="EXEC-EVT-058", quantity=100.0, price=110.0), 110.0, "CF-001", "TC-001", 5711)
        office.apply_execution_event(execution_event(execution_event_id="EXEC-EVT-059", quantity=50.0, price=120.0, side="sell"), 120.0, "CF-001", "TC-001", 5712)
        position = office.position("POS-057")

        self.assertEqual(position.quantity, 150.0)
        self.assertEqual(position.average_cost_basis, 105.0)
        self.assertEqual(position.realized_pnl, 750.0)
        self.assertEqual(position.position_status, PositionLifecycleState.REDUCING)

    def test_close_and_archive_zero_quantity_position(self) -> None:
        office = PositionManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        office.apply_execution_event(execution_event(quantity=10.0, price=50.0), 50.0, "CF-001", "TC-001", 5720)
        office.apply_execution_event(execution_event(execution_event_id="EXEC-EVT-CLOSE", quantity=10.0, price=55.0, side="sell"), 55.0, "CF-001", "TC-001", 5721)
        archived = office.close_position("POS-057", "CF-001", "TC-001", 5722)

        self.assertEqual(office.position("POS-057").position_status, PositionLifecycleState.ARCHIVED)
        self.assertEqual(archived.machine_payload["position"]["position_status"], "archived")

    def test_reconciliation_mismatch_generates_case_file(self) -> None:
        office = PositionManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.apply_execution_event(execution_event(), 102.0, "CF-001", "TC-001", 5730)

        case_file = office.reconcile_with_broker(
            "POS-057",
            BrokerPositionRecord("BROKER-PAPER", "POS-057", 90.0, 99.0, 9000.0, "2026-07-04T00:01:00Z"),
            "CF-001",
            "TC-001",
            5731,
        )

        self.assertEqual(case_file.contract_type, "POSITION_CASE_FILE")
        classifications = tuple(item["classification"] for item in case_file.machine_payload["case_file"]["anomalies"])
        self.assertIn("quantity_error", classifications)
        self.assertIn("cost_basis_error", classifications)
        self.assertIn("position_mismatch", classifications)

    def test_portfolio_exposure_and_system_prompt_are_available(self) -> None:
        office = PositionManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        office.apply_execution_event(execution_event(), 101.0, "CF-001", "TC-001", 5740)
        state = office.publish_portfolio_state("PORT-001")

        self.assertEqual(state.total_exposure, 10100.0)
        self.assertEqual(state.total_market_value, 10100.0)
        self.assertIn("Position Management Office", office.system_prompt().prompt_text)
        self.assertIn("Do not determine what should be traded", office.system_prompt().prompt_text)

    def test_unexpected_exposure_generates_case_file(self) -> None:
        office = PositionManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = office.apply_execution_event(execution_event(quantity=20000.0, price=100.0), 100.0, "CF-001", "TC-001", 5750)

        self.assertIn("position_management_case_file", artifacts)
        classifications = tuple(item["classification"] for item in artifacts["position_management_case_file"].machine_payload["case_file"]["anomalies"])
        self.assertIn("unexpected_exposure", classifications)


if __name__ == "__main__":
    unittest.main()
