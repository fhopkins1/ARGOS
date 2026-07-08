from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.executive import (  # noqa: E402
    CHIEF_OF_STAFF_ID,
    ChiefOfStaffService,
    CommanderDecision,
    CommanderDecisionEngine,
    CommanderOffice,
    ExecutiveBriefingPacket,
    ExecutiveDocumentManifest,
)
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402


HASH_A = "a" * 64
HASH_B = "b" * 64


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


def prompt_repository() -> PromptRepository:
    repository = PromptRepository()
    repository.register(
        PromptPassport(
            prompt_id="PROMPT-014",
            title="Chief of Staff Commander Prompt",
            owner_group_id="DEP-002",
            author_staff_id="STF-002",
            purpose="Route validated Chief of Staff packets.",
            allowed_environments=("development",),
            input_contract_types=("EBP",),
            output_contract_types=("CDR",),
            dependencies=("EO-014",),
            safety_notes="No trading authority.",
        ),
        "1.0.0",
        "Use only Chief of Staff validated EBPs.",
    )
    return repository


def chief_service() -> ChiefOfStaffService:
    config = configuration_service()
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    office = CommanderOffice(config, persistence, audit_service=audit)
    engine = CommanderDecisionEngine(office, prompt_repository(), "PROMPT-014")
    return ChiefOfStaffService(engine, config, persistence, audit)


def ebp(evidence=("DOC-011", "DOC-012")) -> ExecutiveBriefingPacket:
    return ExecutiveBriefingPacket(
        ebp_id="EBP-201",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        produced_by_staff_id=CHIEF_OF_STAFF_ID,
        produced_by_group_id="DEP-002",
        risk_recommendation_document_id="DOC-010",
        evidence_reference_ids=evidence,
        summary="Complete Chief of Staff packet.",
        recommended_action="approve",
        document_signature_hash=HASH_A,
        configuration_snapshot_hash=HASH_B,
        prompt_snapshot_id="PS-000001",
        model_snapshot_id="MS-000001",
    )


def manifests() -> dict[str, ExecutiveDocumentManifest]:
    return {
        "DOC-010": ExecutiveDocumentManifest("DOC-010", "risk", HASH_A, HASH_B, 1),
        "DOC-011": ExecutiveDocumentManifest("DOC-011", "evidence", HASH_A, HASH_B, 1, "trend", "positive"),
        "DOC-012": ExecutiveDocumentManifest("DOC-012", "evidence", HASH_A, HASH_B, 1, "liquidity", "adequate"),
    }


class ChiefOfStaffTests(unittest.TestCase):
    def test_packet_acceptance_routes_to_commander_and_generates_cdr(self) -> None:
        service = chief_service()
        result = service.process_packet(
            ebp(),
            manifests(),
            CommanderDecision.APPROVE,
            "Chief of Staff validated packet.",
            80,
            "DEP-005",
            IncomingMailbox("STF-005", "DEP-005"),
        )

        self.assertTrue(result.accepted)
        self.assertEqual(result.commander_outcome.cdr_contract_id, "DOC-080")
        self.assertEqual(service.routing_log[0]["action"], "approved_to_commander")
        self.assertIsNotNone(service.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-080"))

    def test_packet_rejection_returns_packet_through_courier(self) -> None:
        service = chief_service()
        bad_packet = ExecutiveBriefingPacket(
            ebp_id="EBP-202",
            case_file_id="CF-001",
            trade_cycle_id="TC-001",
            produced_by_staff_id=CHIEF_OF_STAFF_ID,
            produced_by_group_id="DEP-002",
            risk_recommendation_document_id="DOC-010",
            evidence_reference_ids=("DOC-011",),
            summary="Incomplete packet.",
            recommended_action="approve",
            configuration_snapshot_hash=HASH_B,
            prompt_snapshot_id="PS-000001",
            model_snapshot_id="MS-000001",
        )
        rejection_inbox = IncomingMailbox("STF-005", "DEP-005")

        result = service.process_packet(
            bad_packet,
            manifests(),
            CommanderDecision.APPROVE,
            "Should reject missing signature.",
            81,
            "DEP-005",
            rejection_inbox,
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.rejection_contract_id, "DOC-081")
        self.assertIsNotNone(rejection_inbox.get("DOC-081"))
        self.assertIn("missing EBP signature", result.validation_errors)

    def test_contradiction_detection(self) -> None:
        service = chief_service()
        docs = manifests()
        docs["DOC-012"] = ExecutiveDocumentManifest("DOC-012", "evidence", HASH_A, HASH_B, 1, "trend", "negative")

        result = service.process_packet(
            ebp(),
            docs,
            CommanderDecision.DEFER,
            "Contradiction.",
            82,
            "DEP-005",
            IncomingMailbox("STF-005", "DEP-005"),
        )

        self.assertFalse(result.accepted)
        self.assertIn("contradictory reports for claim: trend", result.validation_errors)

    def test_missing_reports_and_duplicate_reports_are_detected(self) -> None:
        service = chief_service()
        duplicate_packet = ebp(evidence=("DOC-011", "DOC-011"))
        docs = manifests()
        docs.pop("DOC-011")

        result = service.process_packet(
            duplicate_packet,
            docs,
            CommanderDecision.REJECT,
            "Missing and duplicate.",
            83,
            "DEP-005",
            IncomingMailbox("STF-005", "DEP-005"),
        )

        self.assertFalse(result.accepted)
        self.assertIn("duplicate report references", result.validation_errors)
        self.assertIn("missing report: DOC-011", result.validation_errors)

    def test_clock_assignment_and_summary_generation(self) -> None:
        service = chief_service()
        first = service.process_packet(
            ebp(),
            manifests(),
            CommanderDecision.APPROVE,
            "First.",
            84,
            "DEP-005",
            IncomingMailbox("STF-005", "DEP-005"),
        )
        second = service.process_packet(
            ebp(),
            manifests(),
            CommanderDecision.APPROVE,
            "Second.",
            85,
            "DEP-005",
            IncomingMailbox("STF-005", "DEP-005"),
        )

        self.assertTrue(first.accepted and second.accepted)
        self.assertEqual([entry["clock_tick"] for entry in service.routing_log], [1, 2])
        self.assertIn("EBP EBP-201", first.summary)

    def test_stale_report_detection_and_audit_logging(self) -> None:
        service = chief_service()
        docs = manifests()
        docs["DOC-010"] = ExecutiveDocumentManifest("DOC-010", "risk", HASH_A, HASH_B, -10)

        result = service.process_packet(
            ebp(),
            docs,
            CommanderDecision.REQUEST_MORE_ANALYSIS,
            "Stale report.",
            86,
            "DEP-005",
            IncomingMailbox("STF-005", "DEP-005"),
        )

        self.assertFalse(result.accepted)
        self.assertIn("stale report: DOC-010", result.validation_errors)
        event_types = [event.event_type for event in service.audit_service.audit_log.events]
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)


if __name__ == "__main__":
    unittest.main()

