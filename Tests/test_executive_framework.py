from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.executive import CommanderOffice, DecisionStatus, ExecutiveInbox  # noqa: E402
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import (  # noqa: E402
    InMemoryPersistenceRepository,
    ObjectType,
    canonical_schemas,
)


def configuration_service() -> ConfigurationService:
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


def commander() -> CommanderOffice:
    return CommanderOffice(
        configuration_service=configuration_service(),
        persistence_repository=InMemoryPersistenceRepository(canonical_schemas()),
        audit_service=AuditService(),
    )


class ExecutiveFrameworkTests(unittest.TestCase):
    def test_decision_registration_is_deterministic(self) -> None:
        office = commander()
        queued = office.submit_decision_request(
            case_file_id="CF-001",
            trade_cycle_id="TC-001",
            requested_by_staff_id="STF-005",
            decision_type="approve_analysis_handoff",
            rationale="Risk recommendation reviewed.",
            risk_recommendation_document_id="DOC-005",
            approved=True,
        )

        registered = office.register_next_decision()

        self.assertEqual(queued.decision_id, "CDR-DECISION-001")
        self.assertEqual(registered.status, DecisionStatus.REGISTERED)
        self.assertEqual(office.decision_registry.get(registered.decision_id), registered)

    def test_cdr_generation_creates_operational_contract_and_persists_it(self) -> None:
        office = commander()
        office.submit_decision_request(
            "CF-001",
            "TC-001",
            "STF-005",
            "approve_analysis_handoff",
            "Risk recommendation reviewed.",
            "DOC-005",
            True,
        )
        decision = office.register_next_decision()

        cdr = office.generate_cdr(decision.decision_id, 21, "DEP-005")

        self.assertEqual(cdr.contract_id, "DOC-021")
        self.assertEqual(cdr.contract_type, "CDR")
        self.assertEqual(cdr.produced_by_group_id, "DEP-002")
        self.assertEqual(cdr.intended_consumer_group_id, "DEP-005")
        self.assertEqual(cdr.machine_payload["risk_recommendation_document_id"], "DOC-005")
        self.assertEqual(
            office.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-021").payload[
                "contract_type"
            ],
            "CDR",
        )

    def test_cdr_generation_requires_risk_recommendation(self) -> None:
        office = commander()
        office.submit_decision_request(
            "CF-001",
            "TC-001",
            "STF-005",
            "approve_analysis_handoff",
            "Missing risk recommendation.",
            "BAD-005",
            True,
        )
        decision = office.register_next_decision()

        with self.assertRaises(ValueError):
            office.generate_cdr(decision.decision_id, 22, "DEP-005")

    def test_cdr_routes_through_courier_to_target_mailbox(self) -> None:
        office = commander()
        office.submit_decision_request(
            "CF-001",
            "TC-001",
            "STF-005",
            "approve_analysis_handoff",
            "Risk recommendation reviewed.",
            "DOC-005",
            True,
        )
        decision = office.register_next_decision()
        cdr = office.generate_cdr(decision.decision_id, 23, "DEP-005")
        risk_inbox = IncomingMailbox("STF-006", "DEP-005")

        result = office.route_cdr(cdr, risk_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(risk_inbox.get("DOC-023"), cdr)
        self.assertIn(
            AuditEventType.COURIER_TRANSFER,
            [event.event_type for event in office.audit_service.audit_log.events],
        )

    def test_executive_inbox_uses_executive_group_identity(self) -> None:
        inbox = ExecutiveInbox.create()

        self.assertEqual(inbox.mailbox.owner_group_id, "DEP-002")


if __name__ == "__main__":
    unittest.main()

