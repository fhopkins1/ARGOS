from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.communication import (  # noqa: E402
    CourierService,
    DeliveryStatus,
    DirectCommunicationRejected,
    IncomingMailbox,
    MailboxDeliveryError,
    OutgoingMailbox,
)
from argos.foundation.contracts import BaseContract  # noqa: E402


def valid_contract_data(contract_id: str = "DOC-011") -> dict[str, object]:
    return {
        "contract_id": contract_id,
        "contract_type": "HANDOFF_CONTRACT",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "case_file_id": "CF-001",
        "trade_cycle_id": "TC-001",
        "parent_contract_ids": [],
        "produced_by_staff_id": "STF-001",
        "produced_by_group_id": "DEP-003",
        "intended_consumer_group_id": "DEP-004",
        "created_timestamp_utc": "2026-07-03T13:00:00Z",
        "updated_timestamp_utc": "2026-07-03T13:00:00Z",
        "validation_status": "valid",
        "validation_errors": [],
        "human_summary": "Courier test handoff.",
        "machine_payload": {"handoff": "ready"},
        "signature_hash": "b" * 64,
        "source_reference_ids": [],
    }


class CommunicationFrameworkTests(unittest.TestCase):
    def test_successful_delivery_moves_contract_through_courier(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        outgoing = OutgoingMailbox("STF-001", "DEP-003")
        incoming = IncomingMailbox("STF-002", "DEP-004")
        courier = CourierService()

        result = courier.deliver(outgoing, incoming, contract)

        self.assertTrue(result.delivered)
        self.assertEqual(result.log_entry.status, DeliveryStatus.DELIVERED)
        self.assertIsNone(outgoing.get("DOC-011"))
        self.assertEqual(incoming.get("DOC-011"), contract)
        self.assertEqual(len(courier.transfer_log), 1)

    def test_direct_incoming_mailbox_delivery_is_rejected(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        incoming = IncomingMailbox("STF-002", "DEP-004")

        with self.assertRaises(DirectCommunicationRejected):
            incoming.receive_direct(contract)

        self.assertIsNone(incoming.get("DOC-011"))

    def test_courier_rejects_direct_staff_to_staff_communication(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        courier = CourierService()

        with self.assertRaises(MailboxDeliveryError):
            courier.reject_direct_communication("STF-001", "STF-002", contract)

    def test_validation_failure_is_logged_and_not_delivered(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        outgoing = OutgoingMailbox("STF-001", "DEP-003")
        wrong_incoming_group = IncomingMailbox("STF-002", "DEP-005")
        courier = CourierService()

        result = courier.deliver(outgoing, wrong_incoming_group, contract)

        self.assertFalse(result.delivered)
        self.assertEqual(result.log_entry.status, DeliveryStatus.REJECTED)
        self.assertIn("incoming mailbox group", result.log_entry.reason)
        self.assertIsNone(wrong_incoming_group.get("DOC-011"))
        self.assertEqual(outgoing.get("DOC-011"), None)

    def test_retry_increments_attempt_and_can_succeed_after_rejection(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data("DOC-012"))
        outgoing = OutgoingMailbox("STF-001", "DEP-003")
        wrong_incoming_group = IncomingMailbox("STF-002", "DEP-005")
        correct_incoming_group = IncomingMailbox("STF-003", "DEP-004")
        courier = CourierService()

        failed = courier.deliver(outgoing, wrong_incoming_group, contract)
        retried = courier.retry(outgoing, correct_incoming_group, contract)

        self.assertFalse(failed.delivered)
        self.assertEqual(failed.attempt, 1)
        self.assertTrue(retried.delivered)
        self.assertEqual(retried.attempt, 2)
        self.assertEqual(correct_incoming_group.get("DOC-012"), contract)
        self.assertEqual([entry.status for entry in courier.transfer_log], [
            DeliveryStatus.REJECTED,
            DeliveryStatus.DELIVERED,
        ])

    def test_mailbox_owner_identifiers_are_validated(self) -> None:
        with self.assertRaises(MailboxDeliveryError):
            OutgoingMailbox("DEP-001", "DEP-003")
        with self.assertRaises(MailboxDeliveryError):
            IncomingMailbox("STF-001", "STF-003")


if __name__ == "__main__":
    unittest.main()

