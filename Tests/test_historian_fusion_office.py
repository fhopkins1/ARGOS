from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.historian import HistorianFusionInput, HistorianFusionOffice, HistorianOfficeFinding, LearningStatus  # noqa: E402


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


def finding(finding_id: str, office: str, report: str, confidence: float = 0.86, supports: bool = True, contradictions: tuple[str, ...] = ()) -> HistorianOfficeFinding:
    return HistorianOfficeFinding(
        finding_id,
        office,
        report,
        "validated_learning",
        "Evidence-first process improved organizational quality.",
        confidence,
        (f"EV-{finding_id}",),
        ("evidence_first", "decision_discipline"),
        supports,
        contradictions,
    )


def fusion_input() -> HistorianFusionInput:
    return HistorianFusionInput(
        "HFI-068",
        (finding("PERF-1", "HISTORIAN-OFFICE-002", "DOC-6201"),),
        (finding("HYP-1", "HISTORIAN-OFFICE-003", "DOC-6301"),),
        (finding("MODEL-1", "HISTORIAN-OFFICE-004", "DOC-6401"),),
        (finding("DEC-1", "HISTORIAN-OFFICE-006", "DOC-6601"),),
        (finding("EVID-1", "HISTORIAN-OFFICE-007", "DOC-6701"),),
    )


class HistorianFusionOfficeTests(unittest.TestCase):
    def test_historian_reports_are_integrated_and_audited(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = HistorianFusionOffice(config(), persistence, audit, PromptRepository())

        artifacts = office.fuse(fusion_input(), "CF-001", "TC-001", 6801)

        self.assertIn("organizational_learning_assessment", artifacts)
        self.assertIn("organizational_evolution_report", artifacts)
        self.assertIn("institutional_knowledge_report", artifacts)
        self.assertIn("historian_fusion_summary", artifacts)
        assessment = artifacts["organizational_learning_assessment"]
        self.assertEqual(assessment.contract_type, "ORGANIZATIONAL_LEARNING_ASSESSMENT")
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, assessment.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_validated_learning_promotes_institutional_knowledge(self) -> None:
        office = HistorianFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = office.fuse(fusion_input(), "CF-001", "TC-001", 6810)

        assessment = artifacts["organizational_learning_assessment"].machine_payload["organizational_learning_assessment"]
        knowledge = artifacts["institutional_knowledge_report"].machine_payload["institutional_knowledge_record"]
        librarian = artifacts["institutional_knowledge_report"].machine_payload["validated_institutional_knowledge_package"]
        self.assertEqual(assessment["status"], LearningStatus.VALIDATED.value)
        self.assertTrue(assessment["provenance_complete"])
        self.assertTrue(knowledge["promoted"])
        self.assertTrue(knowledge["doctrine_promotion_recommended"])
        self.assertIn(knowledge["knowledge_id"], librarian["institutional_knowledge_ids"])

    def test_conflicting_evaluations_are_preserved(self) -> None:
        conflicted = HistorianFusionInput(
            "HFI-CONFLICT",
            (finding("PERF-1", "HISTORIAN-OFFICE-002", "DOC-6201"),),
            (finding("HYP-1", "HISTORIAN-OFFICE-003", "DOC-6301", supports=False, contradictions=("EVID-1",)),),
            (finding("MODEL-1", "HISTORIAN-OFFICE-004", "DOC-6401"),),
            (finding("DEC-1", "HISTORIAN-OFFICE-006", "DOC-6601"),),
            (finding("EVID-1", "HISTORIAN-OFFICE-007", "DOC-6701"),),
        )

        artifacts = HistorianFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository()).fuse(conflicted, "CF-001", "TC-001", 6820)

        consistency = artifacts["organizational_learning_assessment"].machine_payload["cross_evaluation_consistency_record"]
        knowledge = artifacts["institutional_knowledge_report"].machine_payload["institutional_knowledge_record"]
        self.assertEqual(consistency["conflict_count"], 1)
        self.assertIn("HYP-1", consistency["conflicting_finding_ids"])
        self.assertFalse(knowledge["promoted"])

    def test_patterns_and_academy_interface_are_generated(self) -> None:
        artifacts = HistorianFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository()).fuse(fusion_input(), "CF-001", "TC-001", 6830)

        learning_payload = artifacts["organizational_learning_assessment"].machine_payload
        academy = artifacts["institutional_knowledge_report"].machine_payload["curriculum_development_package"]
        patterns = {item["pattern_tag"]: item for item in learning_payload["organizational_pattern_database"]}
        self.assertTrue(patterns["evidence_first"]["recurring"])
        self.assertIn("Evidence-based organizational learning", academy["curriculum_topics"])
        self.assertIn("evidence_first", academy["best_practice_archive"])

    def test_fusion_summary_archives_interfaces_and_traceability(self) -> None:
        office = HistorianFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        summary = office.fuse(fusion_input(), "CF-001", "TC-001", 6840)["historian_fusion_summary"].machine_payload

        self.assertTrue(summary["historian_integration_archive"])
        self.assertTrue(summary["librarian_interface_ready"])
        self.assertTrue(summary["academy_interface_ready"])
        self.assertTrue(office.historian_integration_archive)

    def test_missing_office_findings_are_rejected(self) -> None:
        office = HistorianFusionOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        with self.assertRaises(ValueError):
            office.fuse(HistorianFusionInput("EMPTY", (), (), (), (), ()), "CF-001", "TC-001", 6850)
        with self.assertRaises(ValueError):
            office.fuse(HistorianFusionInput("MISSING", (), fusion_input().hypothesis_findings, fusion_input().model_calibration_findings, fusion_input().decision_findings, fusion_input().evidence_findings), "CF-001", "TC-001", 6851)


if __name__ == "__main__":
    unittest.main()
