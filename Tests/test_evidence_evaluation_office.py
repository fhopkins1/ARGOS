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
from argos.historian import EvidenceConflictSeverity, EvidenceEvaluationOffice, EvidenceStatus, OrganizationalEvidence  # noqa: E402


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


def evidence_items() -> tuple[OrganizationalEvidence, ...]:
    return (
        OrganizationalEvidence("EVID-1", "analyst_report", "AAR-1", "CLAIM-067", "PROV-1", "2026-06-30T00:00:00Z", 0.9, 0.8, 0.85, "analyst", True, "AUD-E1"),
        OrganizationalEvidence("EVID-2", "risk_report", "RAR-1", "CLAIM-067", "PROV-2", "2026-06-29T00:00:00Z", 0.85, 0.82, 0.8, "risk", True, "AUD-E2"),
        OrganizationalEvidence("EVID-3", "market_record", "MKT-1", "CLAIM-067", "PROV-3", "2026-05-01T00:00:00Z", 0.7, 0.75, 0.65, "market", False, "AUD-E3"),
    )


class EvidenceEvaluationOfficeTests(unittest.TestCase):
    def test_evidence_registration_is_persisted_and_audited(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = EvidenceEvaluationOffice(config(), persistence, audit, PromptRepository())

        contract = office.register_evidence(evidence_items()[0], "CF-001", "TC-001", 6701)

        self.assertEqual(contract.contract_type, "EVIDENCE_REGISTRY")
        self.assertEqual(contract.machine_payload["evidence_registry_record"]["status"], EvidenceStatus.REGISTERED.value)
        self.assertTrue(contract.machine_payload["provenance_registry_updated"])
        self.assertTrue(contract.machine_payload["historical_evidence_archive_immutable"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_evidence_quality_independence_freshness_and_weights_are_calculated(self) -> None:
        office = EvidenceEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        for index, item in enumerate(evidence_items(), start=6710):
            office.register_evidence(item, "CF-001", "TC-001", index)

        artifacts = office.evaluate_evidence(("EVID-1", "EVID-2", "EVID-3"), 3, 2026 * 365 + 7 * 30 + 4, "CF-001", "TC-001", 6720)

        report = artifacts["evidence_evaluation_report"].machine_payload
        self.assertEqual(len(report["evidence_quality_dataset"]), 3)
        self.assertEqual(report["evidence_independence_assessment"]["independent_source_count"], 3)
        self.assertEqual(report["evidence_independence_assessment"]["independence_score"], 1.0)
        self.assertTrue(report["evidence_freshness_archive"][0]["freshness_score"] > report["evidence_freshness_archive"][2]["freshness_score"])
        self.assertTrue(all(item["deterministic_weight"] >= 0 for item in report["evidence_weight_database"]))
        self.assertFalse(report["conclusions_evaluated"])

    def test_conflicts_and_sufficiency_reports_are_generated(self) -> None:
        office = EvidenceEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        for index, item in enumerate(evidence_items(), start=6730):
            office.register_evidence(item, "CF-001", "TC-001", index)

        artifacts = office.evaluate_evidence(("EVID-1", "EVID-2", "EVID-3"), 3, 2026 * 365 + 7 * 30 + 4, "CF-001", "TC-001", 6740)

        conflict = artifacts["evidence_conflict_report"].machine_payload["evidence_conflict_register"][0]
        sufficiency = artifacts["evidence_sufficiency_report"].machine_payload["evidence_sufficiency_report"]
        self.assertEqual(conflict["severity"], EvidenceConflictSeverity.MODERATE.value)
        self.assertEqual(conflict["conflicting_evidence_ids"], ["EVID-3"])
        self.assertTrue(sufficiency["sufficient"])

    def test_organizational_summary_preserves_archive_and_recommendations(self) -> None:
        office = EvidenceEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        for index, item in enumerate(evidence_items(), start=6750):
            office.register_evidence(item, "CF-001", "TC-001", index)

        summary = office.evaluate_evidence(("EVID-1", "EVID-2", "EVID-3"), 3, 2026 * 365 + 7 * 30 + 4, "CF-001", "TC-001", 6760)["organizational_evidence_summary"].machine_payload

        self.assertTrue(summary["historical_evidence_archive_complete"])
        self.assertTrue(summary["confidence_proportional_to_evidence_quality"])
        recommendation = summary["organizational_recommendation_register"][0]
        self.assertTrue(recommendation["evidence_based"])
        self.assertFalse(recommendation["directly_modifies_behavior"])
        self.assertTrue(office.historical_evidence_archive)
        self.assertEqual(summary["evidence_registry"][0]["status"], EvidenceStatus.EVALUATED.value)

    def test_invalid_inputs_are_rejected(self) -> None:
        office = EvidenceEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        first, second, *_ = evidence_items()
        office.register_evidence(first, "CF-001", "TC-001", 6770)

        with self.assertRaises(ValueError):
            office.register_evidence(first, "CF-001", "TC-001", 6771)
        with self.assertRaises(ValueError):
            office.evaluate_evidence((), 1, 2026 * 365, "CF-001", "TC-001", 6772)
        with self.assertRaises(ValueError):
            office.evaluate_evidence(("UNKNOWN",), 1, 2026 * 365, "CF-001", "TC-001", 6773)
        different_claim = OrganizationalEvidence("EVID-X", "analyst_report", "AAR-X", "CLAIM-X", "PROV-X", "2026-06-30T00:00:00Z", 0.9, 0.8, 0.85, "analyst", True, "AUD-X")
        office.register_evidence(different_claim, "CF-001", "TC-001", 6774)
        with self.assertRaises(ValueError):
            office.evaluate_evidence(("EVID-1", "EVID-X"), 2, 2026 * 365, "CF-001", "TC-001", 6775)

    def test_standards_define_librarian_deliverables(self) -> None:
        standards = EvidenceEvaluationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository()).standards()

        self.assertEqual(standards.standards_id, "EES-067")
        self.assertIn("reliability", standards.quality_methodology)
        self.assertIn("weight", standards.weighting_methodology)
        self.assertIn("provenance", standards.provenance_specification)
        self.assertIn("evidence quality", standards.confidence_rule)


if __name__ == "__main__":
    unittest.main()
