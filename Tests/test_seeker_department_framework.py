from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402
from argos.seeker import SeekerDepartment, seeker_office_templates  # noqa: E402


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
            prompt_id="PROMPT-018",
            title="Seeker COR Prompt",
            owner_group_id="DEP-003",
            author_staff_id="STF-021",
            purpose="Generate deterministic COR scaffold.",
            allowed_environments=("development",),
            input_contract_types=("SEEKER_OFFICE_INPUT",),
            output_contract_types=("COR",),
            dependencies=("EO-018",),
            safety_notes="No market analysis or trade authority.",
        ),
        "1.0.0",
        "Generate only a deterministic COR scaffold.",
    )
    return repository


def department() -> SeekerDepartment:
    return SeekerDepartment(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class SeekerDepartmentFrameworkTests(unittest.TestCase):
    def test_office_creation_from_templates(self) -> None:
        seeker = department()

        self.assertEqual(len(seeker.registry.all()), 8)
        self.assertEqual(len(seeker_office_templates()), 8)
        self.assertEqual(seeker.registry.get("SEEKER-OFFICE-001").configuration.name, "Technical Analysis Office")

    def test_cor_generation_persists_operational_document(self) -> None:
        seeker = department()

        cor = seeker.generate_cor("SEEKER-OFFICE-001", "CF-001", "TC-001", 201, "PROMPT-018")

        self.assertEqual(cor.contract_id, "DOC-201")
        self.assertEqual(cor.contract_type, "COR")
        self.assertEqual(cor.produced_by_group_id, "DEP-003")
        self.assertEqual(cor.machine_payload["candidate_status"], "unanalysed_candidate")
        self.assertIsNotNone(seeker.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-201"))

    def test_cor_routes_through_courier(self) -> None:
        seeker = department()
        cor = seeker.generate_cor("SEEKER-OFFICE-001", "CF-001", "TC-001", 202, "PROMPT-018")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = seeker.route_cor("SEEKER-OFFICE-001", cor, executive_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-202"), cor)
        self.assertEqual(seeker.offices["SEEKER-OFFICE-001"].routed_reports, 1)

    def test_office_metrics_and_health(self) -> None:
        seeker = department()
        office = seeker.offices["SEEKER-OFFICE-001"]
        office.queue.enqueue("TASK-001")

        metrics = office.metrics()
        health = office.health()

        self.assertEqual(metrics.queue_depth, 1)
        self.assertEqual(metrics.reports_generated, 0)
        self.assertEqual(health.status, "healthy")

    def test_instrument_panels_are_complete(self) -> None:
        seeker = department()
        panels = seeker.instrument_panels()

        self.assertEqual(len(panels), 8)
        self.assertEqual(panels[0].office_id, "SEEKER-OFFICE-001")
        self.assertTrue(panels[0].source.startswith("office:"))

    def test_disabled_office_health_reports_attention(self) -> None:
        templates = list(seeker_office_templates())
        disabled = type(templates[0])(
            office_id="SEEKER-OFFICE-999",
            name="Disabled Office",
            staff_id="STF-099",
            enabled=False,
        )
        seeker = department()
        record = seeker.registry.register(disabled)
        from argos.seeker import SeekerOffice

        office = SeekerOffice(record)
        self.assertEqual(office.health().status, "attention")
        self.assertIn("office_disabled", office.health().reasons)


if __name__ == "__main__":
    unittest.main()

