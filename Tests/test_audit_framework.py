from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import (  # noqa: E402
    AppendOnlyAuditLog,
    AuditEventType,
    AuditIntegrityError,
    AuditService,
    TraceEngine,
)
from argos.foundation.communication import CourierService, IncomingMailbox, OutgoingMailbox  # noqa: E402
from argos.foundation.contracts import BaseContract  # noqa: E402


def valid_contract_data(contract_id: str = "DOC-101") -> dict[str, object]:
    return {
        "contract_id": contract_id,
        "contract_type": "AUDIT_TEST_CONTRACT",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "case_file_id": "CF-001",
        "trade_cycle_id": "TC-001",
        "parent_contract_ids": [],
        "produced_by_staff_id": "STF-001",
        "produced_by_group_id": "DEP-003",
        "intended_consumer_group_id": "DEP-004",
        "created_timestamp_utc": "2026-07-03T14:00:00Z",
        "updated_timestamp_utc": "2026-07-03T14:00:00Z",
        "validation_status": "valid",
        "validation_errors": [],
        "human_summary": "Audit framework test contract.",
        "machine_payload": {"audit": "fixture"},
        "signature_hash": "c" * 64,
        "source_reference_ids": [],
    }


class AuditFrameworkTests(unittest.TestCase):
    def test_courier_generates_required_audit_events_for_successful_delivery(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        audit_service = AuditService()
        courier = CourierService(audit_service=audit_service)

        result = courier.deliver(
            OutgoingMailbox("STF-001", "DEP-003"),
            IncomingMailbox("STF-002", "DEP-004"),
            contract,
        )

        self.assertTrue(result.delivered)
        self.assertEqual(
            [event.event_type for event in audit_service.audit_log.events],
            [
                AuditEventType.DOCUMENT_CREATED,
                AuditEventType.VALIDATION_RESULT,
                AuditEventType.MAILBOX_DEPOSITED,
                AuditEventType.COURIER_TRANSFER,
                AuditEventType.DOCUMENT_RECEIVED,
            ],
        )
        self.assertTrue(audit_service.audit_log.verify_integrity())

    def test_search_functions_return_matching_events(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        audit_service = AuditService()
        audit_service.record_document_creation(contract)
        audit_service.record_staff_decision(
            contract,
            staff_id="STF-001",
            group_id="DEP-003",
            decision="approve_handoff",
            rationale="Fixture decision.",
        )

        self.assertEqual(len(audit_service.search_by_case_file_id("CF-001")), 2)
        self.assertEqual(len(audit_service.search_by_trade_cycle_id("TC-001")), 2)
        self.assertEqual(len(audit_service.search_by_staff_id("STF-001")), 2)
        self.assertEqual(len(audit_service.search_by_document_id("DOC-101")), 2)

    def test_trace_engine_replays_case_file_in_order(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        audit_service = AuditService()
        courier = CourierService(audit_service=audit_service)
        courier.deliver(
            OutgoingMailbox("STF-001", "DEP-003"),
            IncomingMailbox("STF-002", "DEP-004"),
            contract,
        )
        audit_service.record_staff_decision(
            contract,
            staff_id="STF-002",
            group_id="DEP-004",
            decision="received",
            rationale="Receipt acknowledged.",
        )

        replay = TraceEngine(audit_service.audit_log).replay_case_file("CF-001")

        self.assertEqual(replay.case_file_id, "CF-001")
        self.assertEqual([event.sequence for event in replay.events], [1, 2, 3, 4, 5, 6])
        self.assertEqual(replay.document_ids, ("DOC-101",))
        self.assertEqual(replay.staff_ids, ("STF-001", "STF-002"))
        self.assertEqual(replay.trade_cycle_ids, ("TC-001",))

    def test_append_only_log_rejects_out_of_order_event(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        audit_service = AuditService()
        audit_service.record_document_creation(contract)
        second_event = audit_service.record_staff_decision(
            contract,
            staff_id="STF-001",
            group_id="DEP-003",
            decision="continue",
            rationale="Create second sequence event.",
        )
        bad_log = AppendOnlyAuditLog()

        with self.assertRaises(AuditIntegrityError):
            bad_log.append(second_event)

    def test_audit_event_payload_is_immutable(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        audit_service = AuditService()
        event = audit_service.record_document_creation(contract)

        with self.assertRaises(TypeError):
            event.payload["new_value"] = "blocked"  # type: ignore[index]

    def test_failed_validation_is_audited_before_rejected_transfer(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data("DOC-102"))
        audit_service = AuditService()
        courier = CourierService(audit_service=audit_service)

        result = courier.deliver(
            OutgoingMailbox("STF-001", "DEP-003"),
            IncomingMailbox("STF-002", "DEP-005"),
            contract,
        )

        self.assertFalse(result.delivered)
        validation_events = [
            event
            for event in audit_service.audit_log.events
            if event.event_type == AuditEventType.VALIDATION_RESULT
        ]
        self.assertEqual(len(validation_events), 1)
        self.assertFalse(validation_events[0].payload["passed"])
        self.assertIn("incoming mailbox group", validation_events[0].payload["errors"][0])
        self.assertEqual(audit_service.audit_log.events[-1].event_type, AuditEventType.COURIER_TRANSFER)
        self.assertEqual(audit_service.audit_log.events[-1].payload["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
