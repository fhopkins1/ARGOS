from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.trader import BrokerOrderMessage, ExecutionOrderRequest, OrderFillRecord, OrderLifecycleState, OrderManagementOffice  # noqa: E402


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


def request(**overrides) -> ExecutionOrderRequest:
    values = {
        "execution_plan_id": "EXP-054A",
        "instrument_id": "AAPL",
        "quantity": 100.0,
        "direction": "buy",
        "execution_method": "limit",
        "venue": "NASDAQ",
        "account_id": "ACCT-PAPER-001",
        "strategy_id": "STRAT-054A",
        "executive_authorization_id": "DOC-5201",
        "risk_reference_id": "DOC-3702",
        "position_id": "POS-054A",
        "order_priority": 1,
        "broker_destination": "BROKER-PAPER",
        "exchange_destination": "NASDAQ",
        "execution_constraints": ("do_not_modify_strategy",),
    }
    values.update(overrides)
    return ExecutionOrderRequest(**values)


class OrderManagementOfficeTests(unittest.TestCase):
    def test_order_creation_assigns_identifiers_and_authoritative_state(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = OrderManagementOffice(config(), persistence, audit, PromptRepository())

        report = office.create_order(request(), "CF-001", "TC-001", 1, 5401)
        managed = office.managed_order("ORD-000001")

        self.assertEqual(report.contract_type, "ORDER_RECORD")
        self.assertIsNotNone(managed)
        self.assertEqual(managed.current_state, OrderLifecycleState.QUEUED)
        self.assertEqual(managed.identifiers.order_id, "ORD-000001")
        self.assertEqual(managed.identifiers.executive_decision_id, "DOC-5201")
        self.assertEqual(len(managed.state_history), 2)
        self.assertEqual(managed.state_history[-1].audit_record_id, "AUD-ORD-000001")
        self.assertEqual(managed.state_history[-1].position_id, "POS-054A")
        self.assertIn("Order Management Office", report.machine_payload["order_management_system_prompt"]["prompt_text"])
        self.assertFalse(report.machine_payload["executive_intent_modified"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-000001"))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))
        self.assertIn(AuditEventType.STAFF_DECISION, tuple(event.event_type for event in audit.audit_log.events))

    def test_incomplete_or_invalid_order_is_rejected(self) -> None:
        office = OrderManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        report = office.create_order(request(quantity=0, direction="hold"), "CF-001", "TC-001", 2, 5402)

        self.assertEqual(report.contract_type, "ORDER_EXCEPTION")
        self.assertIn("order quantity must be positive", report.machine_payload["validation_errors"])
        self.assertIn("order direction is unsupported", report.machine_payload["validation_errors"])

    def test_duplicate_order_is_prevented(self) -> None:
        office = OrderManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        office.create_order(request(), "CF-001", "TC-001", 3, 5403)
        duplicate = office.create_order(request(), "CF-001", "TC-001", 3, 5404)

        self.assertEqual(duplicate.contract_type, "ORDER_EXCEPTION")
        self.assertIn("duplicate order: ORD-000003", duplicate.machine_payload["validation_errors"])

    def test_approved_transitions_are_recorded_and_unapproved_transitions_raise(self) -> None:
        office = OrderManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.create_order(request(), "CF-001", "TC-001", 4, 5405)

        submitted = office.transition_order("ORD-000004", OrderLifecycleState.SUBMITTED, "broker_submission", "Order transmitted to broker adapter.", "CF-001", "TC-001", 5406)
        acknowledged = office.transition_order("ORD-000004", OrderLifecycleState.ACKNOWLEDGED, "broker_ack", "Broker acknowledged order receipt.", "CF-001", "TC-001", 5407)

        self.assertEqual(submitted.machine_payload["managed_order"]["current_state"], "submitted")
        self.assertEqual(acknowledged.machine_payload["managed_order"]["current_state"], "acknowledged")
        self.assertEqual(len(office.order_history("ORD-000004")), 4)
        with self.assertRaises(ValueError):
            office.transition_order("ORD-000004", OrderLifecycleState.FILLED, "bad_jump", "Unauthorized jump.", "CF-001", "TC-001", 5408)

    def test_parent_child_routing_and_synchronization_are_deterministic(self) -> None:
        office = OrderManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        report = office.create_order(
            request(parent_order_id="ORD-000010", child_order_index=1, broker_destination="BROKER-B", order_priority=2),
            "CF-001",
            "TC-001",
            11,
            5409,
        )
        managed = office.managed_order("ORD-000011")

        self.assertEqual(managed.identifiers.child_order_id, "ORD-000010-CHILD-001")
        self.assertEqual(managed.routing["broker_destination"], "BROKER-B")
        self.assertEqual(managed.routing["routing_priority"], 2)
        self.assertIn("Broker Integration Office", managed.synchronization_targets)
        self.assertEqual(report.machine_payload["parent_child_linkage"]["position_id"], "POS-054A")

    def test_order_records_route_through_courier(self) -> None:
        office = OrderManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        report = office.create_order(request(), "CF-001", "TC-001", 12, 5410)
        inbox = IncomingMailbox("STF-065", "DEP-006")

        result = office.route_order_record(report, inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(inbox.get(report.contract_id), report)

    def test_synchronization_failure_generates_exception(self) -> None:
        office = OrderManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        report = office.create_order(request(), "CF-001", "TC-001", 13, 5411)
        managed = office.managed_order("ORD-000013")
        broken = type(managed)(managed.identifiers, managed.request, managed.current_state, managed.state_history, managed.routing, ("Audit Repository",))

        with self.assertRaises(ValueError):
            office.synchronization.verify(broken)
        self.assertEqual(report.machine_payload["managed_order"]["current_state"], "queued")

    def test_broker_message_and_fill_inconsistencies_generate_case_files(self) -> None:
        office = OrderManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.create_order(request(), "CF-001", "TC-001", 14, 5412)
        office.transition_order("ORD-000014", OrderLifecycleState.SUBMITTED, "broker_submission", "Order submitted.", "CF-001", "TC-001", 5413)
        office.record_broker_message(
            "ORD-000014",
            BrokerOrderMessage("BRK-MSG-001", "ORD-000014", "acknowledgement", 100.0, 0.0, 100.0, 100.0, "acknowledged", "2026-07-04T00:00:00Z"),
            "CF-001",
            "TC-001",
            54135,
        )
        first = office.record_fill(
            "ORD-000014",
            OrderFillRecord("FILL-001", "ORD-000014", 60.0, 101.0, "2026-07-04T00:00:01Z", "BRK-MSG-001"),
            "CF-001",
            "TC-001",
            5414,
        )
        duplicate = office.record_fill(
            "ORD-000014",
            OrderFillRecord("FILL-001", "ORD-000014", 50.0, 101.0, "2026-07-04T00:00:02Z", "BRK-MSG-002"),
            "CF-001",
            "TC-001",
            5415,
        )

        self.assertEqual(first.contract_type, "ORDER_RECORD")
        self.assertEqual(duplicate.contract_type, "ORDER_CASE_FILE")
        classifications = tuple(item["classification"] for item in duplicate.machine_payload["case_file"]["inconsistencies"])
        self.assertIn("duplicate_fill", classifications)
        self.assertIn("quantity_mismatch", classifications)
        self.assertTrue(duplicate.machine_payload["case_file"]["reconstructable"])

    def test_unexpected_broker_response_generates_case_file(self) -> None:
        office = OrderManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        office.create_order(request(), "CF-001", "TC-001", 15, 5416)

        case_file = office.record_broker_message(
            "ORD-000015",
            BrokerOrderMessage("BRK-MSG-003", "ORD-999999", "acknowledgement", 100.0, 0.0, 100.0, 100.0, "acknowledged", "2026-07-04T00:00:03Z"),
            "CF-001",
            "TC-001",
            5417,
        )

        self.assertEqual(case_file.contract_type, "ORDER_CASE_FILE")
        classifications = tuple(item["classification"] for item in case_file.machine_payload["case_file"]["inconsistencies"])
        self.assertIn("unexpected_broker_response", classifications)


if __name__ == "__main__":
    unittest.main()
