from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import OrganizationalBeliefState  # noqa: E402
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402
from argos.risk import RecoveryEvent, RecoveryPlanningOffice, RecoveryPlanningOfficeChief  # noqa: E402


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
            prompt_id="PROMPT-049",
            title="Recovery Planning Report Prompt",
            owner_group_id="DEP-005",
            author_staff_id="STF-049",
            purpose="Generate deterministic recovery planning reports.",
            allowed_environments=("development",),
            input_contract_types=("OBS", "RECOVERY_EVENT"),
            output_contract_types=("RAR",),
            dependencies=("EO-049",),
            safety_notes="Objective engineering recovery only; no investment recommendation, execution, Organizational Belief State modification, or Command Decision.",
        ),
        "1.0.0",
        "Create deterministic Recovery Planning Report only.",
    )
    return repository


def belief_state() -> OrganizationalBeliefState:
    return OrganizationalBeliefState(
        "OBS-001",
        "risk_elevated",
        0.56,
        0.75,
        0.75,
        ("DOC-2601", "DOC-2602"),
    )


def recovery_event() -> RecoveryEvent:
    return RecoveryEvent("REV-001", "market_operational_stress", 0.24, 0.68, 0.72, 2, 0.08, 3, 0.82)


def office() -> RecoveryPlanningOffice:
    return RecoveryPlanningOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class RecoveryPlanningOfficeTests(unittest.TestCase):
    def test_recovery_scenarios_and_classification_are_deterministic(self) -> None:
        review = RecoveryPlanningOfficeChief().evaluate(belief_state(), recovery_event())

        self.assertEqual(review["recovery_plan"]["classification"], "operational_failure")
        self.assertEqual(len(review["recovery_plan"]["scenarios"]), 3)
        self.assertEqual(review["recovery_plan"]["scenarios"][1]["scenario_id"], "RS-002")

    def test_stabilization_and_workflow_generation_are_operational(self) -> None:
        review = RecoveryPlanningOfficeChief().evaluate(belief_state(), recovery_event())

        self.assertEqual(review["recovery_workflow"]["workflow_id"], "RW-001")
        self.assertEqual(len(review["recovery_workflow"]["steps"]), 3)
        self.assertEqual(review["recovery_workflow"]["steps"][0], {"sequence": 1, "scenario_id": "RS-002", "action": "isolate_disruption"})
        self.assertIn("raise_liquidity_reserve", review["recovery_progress_report"]["stabilization"]["activities"])
        self.assertIn("restore_operational_services", review["recovery_progress_report"]["stabilization"]["activities"])

    def test_capital_readiness_validation_and_improvements_are_reproducible(self) -> None:
        review = RecoveryPlanningOfficeChief().evaluate(belief_state(), recovery_event())

        self.assertEqual(review["capital_restoration_plan"], {"plan_id": "CRP-001", "restoration_required_pct": 0.16, "restoration_state": "capital_restoration_required"})
        self.assertEqual(review["recovery_readiness_assessment"], {"assessment_id": "RRA-001", "readiness_score": 43.8, "readiness_state": "recovery_not_ready"})
        self.assertEqual(review["recovery_validation_report"], {"report_id": "RVR-001", "validated": False, "validation_score": 61.54, "incomplete_actions": 3})
        self.assertEqual(review["executive_recovery_status_report"]["procedural_improvements"], ("tighten_control_breach_escalation", "reduce_recovery_action_backlog", "increase_recovery_validation_threshold"))

    def test_recovery_archive_and_confidence_restoration_are_generated(self) -> None:
        review = RecoveryPlanningOfficeChief().evaluate(belief_state(), recovery_event())

        self.assertEqual(review["recovery_event_archive"], {"archive_id": "REA-001", "event_id": "REV-001", "event_type": "market_operational_stress", "scenario_ids": ("RS-001", "RS-002", "RS-003")})
        self.assertEqual(review["confidence_restoration_record"], {"record_id": "CRR-001", "prior_confidence": 0.56, "restored_confidence": 0.5643, "restoration_delta": 0.0043})
        self.assertEqual(review["organizational_recovery_summary"], {"summary_id": "ORS-001", "readiness_state": "recovery_not_ready", "validated": False})

    def test_recovery_planning_report_contains_required_artifacts_and_boundaries(self) -> None:
        recovery = office()

        report = recovery.generate_recovery_plan_report(belief_state(), recovery_event(), "CF-001", "TC-001", 3501, "PROMPT-049")

        self.assertEqual(report.contract_type, "RAR")
        self.assertEqual(report.machine_payload["risk_id"], "REC-003501")
        self.assertEqual(report.machine_payload["recovery_plan"]["plan_id"], "RP-001")
        self.assertEqual(report.machine_payload["recovery_workflow"]["workflow_id"], "RW-001")
        self.assertEqual(report.machine_payload["recovery_readiness_assessment"]["assessment_id"], "RRA-001")
        self.assertEqual(report.machine_payload["capital_restoration_plan"]["plan_id"], "CRP-001")
        self.assertEqual(report.machine_payload["recovery_validation_report"]["report_id"], "RVR-001")
        self.assertEqual(report.machine_payload["executive_recovery_status_report"]["report_id"], "ERSR-001")
        self.assertEqual(report.machine_payload["recovery_event_archive"]["archive_id"], "REA-001")
        self.assertEqual(report.machine_payload["confidence_restoration_record"]["record_id"], "CRR-001")
        self.assertFalse(report.machine_payload["organizational_belief_state_modified"])
        self.assertFalse(report.machine_payload["subjective_judgment_used"])
        self.assertIsNone(report.machine_payload["investment_recommendation"])
        self.assertIsNone(report.machine_payload["execution_instruction"])
        self.assertIsNone(report.machine_payload["command_decision"])
        self.assertIsNotNone(recovery.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-3501"))

    def test_recovery_planning_requires_organizational_belief_state(self) -> None:
        with self.assertRaises(TypeError):
            RecoveryPlanningOfficeChief().evaluate({"state_id": "OBS-001"}, recovery_event())

    def test_courier_routing_generates_audit_events(self) -> None:
        recovery = office()
        report = recovery.generate_recovery_plan_report(belief_state(), recovery_event(), "CF-001", "TC-001", 3502, "PROMPT-049")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = recovery.route_report(report, executive_inbox)
        event_types = [event.event_type for event in recovery.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-3502"), report)
        self.assertIn(AuditEventType.DOCUMENT_CREATED, event_types)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_displays_recovery_values(self) -> None:
        recovery = office()
        report = recovery.generate_recovery_plan_report(belief_state(), recovery_event(), "CF-001", "TC-001", 3503, "PROMPT-049")
        recovery.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        panel = recovery.instrument_panel()

        self.assertEqual(panel.base_panel.office_id, "RISK-OFFICE-009")
        self.assertEqual(panel.base_panel.metrics.reports_generated, 1)
        self.assertEqual(panel.base_panel.metrics.routed_reports, 1)
        self.assertEqual(panel.active_recovery_events, 1)
        self.assertEqual(panel.readiness_score, 43.8)
        self.assertEqual(panel.capital_restoration_required_pct, 0.16)
        self.assertEqual(panel.workflow_steps, 3)
        self.assertEqual(panel.archived_events, 1)


if __name__ == "__main__":
    unittest.main()
