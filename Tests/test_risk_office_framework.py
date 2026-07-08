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
from argos.risk import RiskDepartment, risk_office_templates  # noqa: E402


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
            prompt_id="PROMPT-040",
            title="Risk Assessment Report Prompt",
            owner_group_id="DEP-005",
            author_staff_id="STF-041",
            purpose="Generate deterministic Risk Assessment Reports.",
            allowed_environments=("development",),
            input_contract_types=("OBS",),
            output_contract_types=("RAR",),
            dependencies=("EO-040",),
            safety_notes="No trade recommendation, execution, market discovery, Organizational Belief State modification, or deterministic interface override.",
        ),
        "1.0.0",
        "Create deterministic Risk Assessment Report only.",
    )
    return repository


def belief_state() -> OrganizationalBeliefState:
    return OrganizationalBeliefState(
        "OBS-001",
        "risk_elevated",
        0.56,
        0.75,
        0.75,
        ("DOC-2601", "DOC-2602", "DOC-2603"),
    )


def department() -> RiskDepartment:
    return RiskDepartment(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class RiskOfficeFrameworkTests(unittest.TestCase):
    def test_office_templates_and_creation_are_deterministic(self) -> None:
        risk = department()
        templates = risk_office_templates()

        self.assertEqual(len(templates), 10)
        self.assertEqual(templates[0].office_id, "RISK-OFFICE-001")
        self.assertEqual(templates[0].name, "Position Risk Office")
        self.assertEqual(templates[-1].name, "Risk Fusion Office")
        self.assertEqual(tuple(risk.offices), tuple(template.office_id for template in templates))

    def test_rar_generation_consumes_organizational_belief_state_only(self) -> None:
        risk = department()
        obs = belief_state()

        rar = risk.generate_rar("RISK-OFFICE-001", obs, "CF-001", "TC-001", 2801, "PROMPT-040")

        self.assertEqual(rar.contract_type, "RAR")
        self.assertEqual(rar.produced_by_group_id, "DEP-005")
        self.assertEqual(rar.machine_payload["belief_state_id"], "OBS-001")
        self.assertEqual(rar.machine_payload["risk_score"], 0.345)
        self.assertEqual(rar.machine_payload["risk_state"], "contained_risk")
        self.assertFalse(rar.machine_payload["organizational_belief_state_modified"])
        self.assertIsNone(rar.machine_payload["trade_recommendation"])
        self.assertIsNone(rar.machine_payload["execution_instruction"])
        self.assertIsNotNone(risk.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-2801"))

    def test_rar_generation_rejects_non_belief_state_inputs(self) -> None:
        risk = department()

        with self.assertRaises(TypeError):
            risk.generate_rar("RISK-OFFICE-001", {"state_id": "OBS-001"}, "CF-001", "TC-001", 2802, "PROMPT-040")

    def test_courier_routing_generates_audit_events(self) -> None:
        risk = department()
        rar = risk.generate_rar("RISK-OFFICE-002", belief_state(), "CF-001", "TC-001", 2803, "PROMPT-040")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = risk.route_rar("RISK-OFFICE-002", rar, executive_inbox)
        event_types = [event.event_type for event in risk.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-2803"), rar)
        self.assertIn(AuditEventType.DOCUMENT_CREATED, event_types)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panels_update_after_generation_and_routing(self) -> None:
        risk = department()
        rar = risk.generate_rar("RISK-OFFICE-003", belief_state(), "CF-001", "TC-001", 2804, "PROMPT-040")
        risk.route_rar("RISK-OFFICE-003", rar, IncomingMailbox("STF-002", "DEP-002"))

        panels = {panel.office_id: panel for panel in risk.instrument_panels()}

        self.assertEqual(len(panels), 10)
        self.assertEqual(panels["RISK-OFFICE-003"].metrics.reports_generated, 1)
        self.assertEqual(panels["RISK-OFFICE-003"].metrics.routed_reports, 1)
        self.assertEqual(panels["RISK-OFFICE-003"].health.status, "healthy")

    def test_office_health_reports_attention_for_disabled_or_deep_queue(self) -> None:
        risk = department()
        office = risk.offices["RISK-OFFICE-004"]
        for index in range(11):
            office.queue.enqueue(f"OBS-{index:03d}")

        panel = office.instrument_panel()

        self.assertEqual(panel.health.status, "attention")
        self.assertIn("queue_depth_high", panel.health.reasons)


if __name__ == "__main__":
    unittest.main()
