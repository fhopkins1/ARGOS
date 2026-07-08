from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.executive import (  # noqa: E402
    CHIEF_OF_STAFF_ID,
    CommanderDecision,
    CommanderDecisionEngine,
    CommanderOffice,
    ExecutiveBriefingPacket,
    ExecutiveReportReference,
    ExecutiveWorkflowService,
    PacketStatus,
)
from argos.foundation.audit import AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import (  # noqa: E402
    InMemoryPersistenceRepository,
    ObjectType,
    canonical_schemas,
)
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402


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
            prompt_id="PROMPT-013",
            title="Executive Workflow Commander Prompt",
            owner_group_id="DEP-002",
            author_staff_id="STF-002",
            purpose="Route validated EBPs to Commander.",
            allowed_environments=("development",),
            input_contract_types=("EBP",),
            output_contract_types=("CDR",),
            dependencies=("EO-013",),
            safety_notes="No trading authority.",
        ),
        "1.0.0",
        "Use only validated Executive Workflow inputs.",
    )
    return repository


def workflow_service() -> ExecutiveWorkflowService:
    config = configuration_service()
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    office = CommanderOffice(config, persistence, audit_service=audit)
    engine = CommanderDecisionEngine(office, prompt_repository(), "PROMPT-013")
    return ExecutiveWorkflowService(engine, config, persistence, audit)


def valid_ebp(staff_id: str = CHIEF_OF_STAFF_ID) -> ExecutiveBriefingPacket:
    return ExecutiveBriefingPacket(
        ebp_id="EBP-101",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        produced_by_staff_id=staff_id,
        produced_by_group_id="DEP-002",
        risk_recommendation_document_id="DOC-010",
        evidence_reference_ids=("DOC-011", "DOC-012"),
        summary="Chief of Staff packet with risk and evidence reports.",
        recommended_action="approve",
    )


def valid_reports() -> dict[str, ExecutiveReportReference]:
    return {
        "DOC-010": ExecutiveReportReference("DOC-010", "risk", 1),
        "DOC-011": ExecutiveReportReference("DOC-011", "evidence", 1, "trend", "positive"),
        "DOC-012": ExecutiveReportReference("DOC-012", "evidence", 1, "liquidity", "adequate"),
    }


class ExecutiveWorkflowTests(unittest.TestCase):
    def test_successful_routing_sends_validated_packet_to_commander(self) -> None:
        workflow = workflow_service()

        outcome = workflow.route_packet_to_commander(
            valid_ebp(),
            valid_reports(),
            CommanderDecision.APPROVE,
            "Validated packet supports approval.",
            61,
            "DEP-005",
        )

        self.assertEqual(outcome.cdr_contract_id, "DOC-061")
        self.assertEqual(workflow.routing_log[0].action, "route_to_commander")
        self.assertEqual(workflow.routing_log[0].status, PacketStatus.VALIDATED.value)
        latest = workflow.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-061")
        self.assertEqual(latest.payload["machine_payload"]["decision_type"], "approve")

    def test_missing_reports_reject_packet(self) -> None:
        workflow = workflow_service()
        reports = valid_reports()
        reports.pop("DOC-011")

        with self.assertRaises(ValueError) as context:
            workflow.route_packet_to_commander(
                valid_ebp(),
                reports,
                CommanderDecision.APPROVE,
                "Should reject missing evidence.",
                62,
                "DEP-005",
            )

        self.assertIn("missing evidence report: DOC-011", str(context.exception))
        self.assertEqual(workflow.routing_log[-1].action, "reject_packet")

    def test_contradictory_reports_reject_packet(self) -> None:
        workflow = workflow_service()
        reports = valid_reports()
        reports["DOC-012"] = ExecutiveReportReference("DOC-012", "evidence", 1, "trend", "negative")

        with self.assertRaises(ValueError) as context:
            workflow.route_packet_to_commander(
                valid_ebp(),
                reports,
                CommanderDecision.DEFER,
                "Should reject contradiction.",
                63,
                "DEP-005",
            )

        self.assertIn("contradictory reports for claim: trend", str(context.exception))

    def test_stale_reports_reject_packet(self) -> None:
        workflow = workflow_service()
        reports = valid_reports()
        reports["DOC-010"] = ExecutiveReportReference("DOC-010", "risk", -10)

        with self.assertRaises(ValueError) as context:
            workflow.route_packet_to_commander(
                valid_ebp(),
                reports,
                CommanderDecision.REQUEST_MORE_ANALYSIS,
                "Should reject stale risk.",
                64,
                "DEP-005",
            )

        self.assertIn("risk recommendation report is stale", str(context.exception))

    def test_packet_rejection_for_chief_of_staff_bypass(self) -> None:
        workflow = workflow_service()

        with self.assertRaises(ValueError) as context:
            workflow.route_packet_to_commander(
                valid_ebp(staff_id="STF-004"),
                valid_reports(),
                CommanderDecision.APPROVE,
                "Should reject bypass.",
                65,
                "DEP-005",
            )

        self.assertIn("Chief of Staff", str(context.exception))

    def test_executive_clock_orders_routing_logs(self) -> None:
        workflow = workflow_service()
        for index in range(2):
            packet = ExecutiveBriefingPacket(
                ebp_id=f"EBP-10{index + 2}",
                case_file_id="CF-001",
                trade_cycle_id="TC-001",
                produced_by_staff_id=CHIEF_OF_STAFF_ID,
                produced_by_group_id="DEP-002",
                risk_recommendation_document_id="DOC-010",
                evidence_reference_ids=("DOC-011", "DOC-012"),
                summary="Ordered packet.",
                recommended_action="approve",
            )
            workflow.route_packet_to_commander(
                packet,
                valid_reports(),
                CommanderDecision.APPROVE,
                "Ordering check.",
                66 + index,
                "DEP-005",
            )

        self.assertEqual([entry.sequence for entry in workflow.routing_log], [1, 2, 3, 4])
        self.assertEqual([entry.clock_tick for entry in workflow.routing_log], [1, 1, 2, 2])

    def test_successful_commander_routing_sends_cdr_to_outbox_via_courier(self) -> None:
        workflow = workflow_service()
        outcome = workflow.route_packet_to_commander(
            valid_ebp(),
            valid_reports(),
            CommanderDecision.APPROVE,
            "Validated packet supports approval.",
            70,
            "DEP-005",
        )
        risk_inbox = IncomingMailbox("STF-006", "DEP-005")

        result = workflow.route_cdr_to_outbox(outcome.cdr_contract_id, risk_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(risk_inbox.get("DOC-070").contract_id, "DOC-070")

    def test_packet_rejected_when_not_received_via_courier(self) -> None:
        workflow = workflow_service()

        with self.assertRaises(ValueError) as context:
            workflow.route_packet_to_commander(
                valid_ebp(),
                valid_reports(),
                CommanderDecision.APPROVE,
                "Courier bypass.",
                71,
                "DEP-005",
                received_via_courier=False,
            )

        self.assertIn("Courier Framework", str(context.exception))


if __name__ == "__main__":
    unittest.main()

