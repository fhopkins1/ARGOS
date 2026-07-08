from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.academy import (  # noqa: E402
    CompetencyDomain,
    CompetencyProfile,
    CurriculumAdaptationTrigger,
    CurriculumEffectivenessMetrics,
    CurriculumModule,
    CurriculumOffice,
    LearnerLevel,
    PrerequisiteRelationship,
)
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402


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


def profile(demonstrated: tuple[CompetencyDomain, ...] = (CompetencyDomain.EVIDENCE_REASONING,)) -> CompetencyProfile:
    return CompetencyProfile(
        "USER-001",
        LearnerLevel.DEVELOPING,
        demonstrated,
        (CompetencyDomain.RISK_DISCIPLINE, CompetencyDomain.PORTFOLIO_JUDGMENT),
        0.72,
        ("understand risk", "build portfolio judgment"),
        ("equities", "risk management"),
        "case-first",
    )


def module(module_id: str, domain: CompetencyDomain) -> CurriculumModule:
    suffix = domain.value.upper()
    return CurriculumModule(
        module_id,
        f"{domain.value.replace('_', ' ').title()} Module",
        domain,
        (f"LESSON-{suffix}",),
        (f"CF-{suffix}",),
        (f"PRACTICE-{suffix}",),
        (f"ASSESS-{suffix}",),
        (f"ADV-{suffix}",),
        (f"REINF-{suffix}",),
        (f"KNOW-{suffix}",),
        (f"DOC-{suffix}",),
        (f"SPEC-{suffix}",),
        (f"EV-{suffix}",),
    )


def modules() -> tuple[CurriculumModule, ...]:
    return (
        module("MOD-PROB", CompetencyDomain.EVIDENCE_REASONING),
        module("MOD-RISK", CompetencyDomain.RISK_DISCIPLINE),
        module("MOD-PORT", CompetencyDomain.PORTFOLIO_JUDGMENT),
        module("MOD-BEHAV", CompetencyDomain.BEHAVIORAL_AWARENESS),
    )


def prerequisites() -> tuple[PrerequisiteRelationship, ...]:
    return (
        PrerequisiteRelationship("PRE-001", CompetencyDomain.EVIDENCE_REASONING, CompetencyDomain.RISK_DISCIPLINE, "Evidence reasoning precedes risk analysis.", ("EV-PRE-001",)),
        PrerequisiteRelationship("PRE-002", CompetencyDomain.RISK_DISCIPLINE, CompetencyDomain.PORTFOLIO_JUDGMENT, "Risk analysis precedes portfolio construction.", ("EV-PRE-002",)),
        PrerequisiteRelationship("PRE-003", CompetencyDomain.PORTFOLIO_JUDGMENT, CompetencyDomain.BEHAVIORAL_AWARENESS, "Portfolio judgment precedes behavioral stress review.", ("EV-PRE-003",)),
    )


def metrics(score: float = 0.82) -> CurriculumEffectivenessMetrics:
    return CurriculumEffectivenessMetrics("CEM-080", score, 0.80, 0.83, 0.72, 0.78, 0.76, 0.81, 0.84)


def design(
    office: CurriculumOffice,
    *,
    curriculum_modules: tuple[CurriculumModule, ...] = modules(),
    prerequisite_relationships: tuple[PrerequisiteRelationship, ...] = prerequisites(),
    learner_profile: CompetencyProfile = profile(),
    effectiveness: CurriculumEffectivenessMetrics = metrics(),
    version: str = "1.0.0",
):
    return office.design_curriculum(
        "CURR-080",
        version,
        learner_profile,
        curriculum_modules,
        prerequisite_relationships,
        ("ASSESS-080-A",),
        effectiveness,
        CurriculumAdaptationTrigger.EDUCATIONAL_ANALYTICS,
        "CF-001",
        "TC-001",
        8001,
    )


class CurriculumOfficeTests(unittest.TestCase):
    def test_curriculum_architecture_map_version_history_and_audit_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = CurriculumOffice(config(), persistence, audit, PromptRepository())

        artifacts = design(office)

        architecture = artifacts["curriculum_architecture"].machine_payload
        curriculum = artifacts["curriculum_map"].machine_payload["curriculum_map"]
        self.assertTrue(architecture["competency_driven"])
        self.assertFalse(architecture["creates_new_institutional_knowledge"])
        self.assertEqual(curriculum["curriculum_id"], "CURR-080")
        self.assertTrue(curriculum["version_record"]["immutable"])
        self.assertEqual(len(office.curriculum_version_history), 1)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["curriculum_architecture"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_personalized_pathway_skips_demonstrated_competencies_and_preserves_prerequisite_order(self) -> None:
        office = CurriculumOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = design(office)

        pathway = artifacts["personalized_learning_pathway"].machine_payload["learning_pathway"]
        self.assertEqual(pathway["skipped_demonstrated_competencies"], [CompetencyDomain.EVIDENCE_REASONING.value])
        self.assertEqual(pathway["ordered_module_ids"], ["MOD-RISK", "MOD-PORT", "MOD-BEHAV"])
        self.assertTrue(pathway["competency_driven"])
        self.assertIn("preferred_learning_style=case-first", pathway["personalization_factors"])

    def test_traceability_adaptation_dashboard_and_metrics_are_complete(self) -> None:
        office = CurriculumOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = design(office)

        traceability = artifacts["curriculum_traceability_record"].machine_payload["curriculum_traceability_record"]
        adaptation = artifacts["curriculum_adaptation_record"].machine_payload["curriculum_adaptation_record"]
        dashboard = artifacts["curriculum_dashboard"].machine_payload["curriculum_dashboard"]
        self.assertTrue(traceability["complete"])
        self.assertIn("LESSON-RISK_DISCIPLINE", traceability["lesson_ids"])
        self.assertEqual(adaptation["trigger"], CurriculumAdaptationTrigger.EDUCATIONAL_ANALYTICS.value)
        self.assertEqual(adaptation["assessment_result_ids"], ["ASSESS-080-A"])
        self.assertEqual(dashboard["curriculum_health"], "healthy")
        self.assertEqual(dashboard["curriculum_effectiveness"], 0.82)

    def test_version_history_preserves_previous_curriculum_versions(self) -> None:
        office = CurriculumOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        design(office)

        artifacts = design(office, version="1.1.0", effectiveness=metrics(0.86))

        version_history = artifacts["curriculum_dashboard"].machine_payload["curriculum_version_history"]
        current = artifacts["curriculum_map"].machine_payload["curriculum_map"]["version_record"]
        self.assertEqual(len(version_history), 2)
        self.assertEqual(current["parent_version_id"], "CVR-008001")
        self.assertFalse(artifacts["curriculum_traceability_record"].machine_payload["previous_curriculum_versions_discarded"])

    def test_missing_prerequisite_and_low_effectiveness_flag_attention(self) -> None:
        office = CurriculumOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        bad_prerequisites = (
            PrerequisiteRelationship("PRE-MISSING", CompetencyDomain.MARKET_STRUCTURE, CompetencyDomain.RISK_DISCIPLINE, "Missing prerequisite module.", ("EV-PRE-MISSING",)),
        )

        artifacts = design(office, prerequisite_relationships=bad_prerequisites, effectiveness=metrics(0.50))

        missing = artifacts["curriculum_map"].machine_payload["missing_prerequisite_relationships"]
        dashboard = artifacts["curriculum_dashboard"].machine_payload["curriculum_dashboard"]
        self.assertEqual(missing, ["PRE-MISSING"])
        self.assertFalse(dashboard["traceability_complete"])
        self.assertEqual(dashboard["curriculum_health"], "attention")

    def test_system_prompt_documents_boundaries(self) -> None:
        office = CurriculumOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = office.system_prompt()

        self.assertIn("Curriculum Office", prompt.prompt_text)
        self.assertIn("You do not create new institutional knowledge", prompt.prompt_text)
        self.assertIn("do not", prompt.prompt_text.lower())


if __name__ == "__main__":
    unittest.main()
