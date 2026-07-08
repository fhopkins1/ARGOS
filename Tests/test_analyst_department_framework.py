from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    AnalystDepartment,
    EvidenceEvaluationFramework,
    HypothesisFramework,
    analyst_office_templates,
)
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.contracts import OperationalContract, utc_timestamp  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
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
            prompt_id="PROMPT-029",
            title="Analyst AAR Prompt",
            owner_group_id="DEP-004",
            author_staff_id="STF-031",
            purpose="Generate deterministic Analytical Assessment Reports.",
            allowed_environments=("development",),
            input_contract_types=("SEEKER_REPORT",),
            output_contract_types=("AAR",),
            dependencies=("EO-029",),
            safety_notes="No discovery, trade recommendation, execution, Risk Office override, or Seeker report modification.",
        ),
        "1.0.0",
        "Create deterministic analytical assessment only.",
    )
    return repository


def source_report(contract_id: str, contract_type: str, staff_id: str, office_id: str) -> OperationalContract:
    created = utc_timestamp()
    payload = {
        "office_id": office_id,
        "office_name": f"Source {office_id}",
        "report_status": "source_report",
        "source_reports_modified": False,
    }
    signature_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return OperationalContract(
        contract_id=contract_id,
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id=staff_id,
        produced_by_group_id="DEP-003",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic Seeker source report.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def source_reports() -> tuple[OperationalContract, ...]:
    return (
        source_report("DOC-201", "COR", "STF-021", "SEEKER-OFFICE-001"),
        source_report("DOC-301", "ATR", "STF-028", "SEEKER-OFFICE-008"),
        source_report("DOC-401", "MIR", "STF-029", "SEEKER-OFFICE-009"),
    )


def department() -> AnalystDepartment:
    return AnalystDepartment(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class AnalystDepartmentFrameworkTests(unittest.TestCase):
    def test_office_creation_from_templates(self) -> None:
        analyst = department()

        self.assertEqual(len(analyst.registry.all()), 9)
        self.assertEqual(len(analyst_office_templates()), 9)
        self.assertEqual(analyst.registry.get("ANALYST-OFFICE-001").configuration.name, "Statistical Analysis Office")
        self.assertEqual(analyst.registry.get("ANALYST-OFFICE-009").configuration.name, "Analytical Fusion Office")

    def test_hypothesis_generation_is_deterministic(self) -> None:
        analyst = department()
        office = analyst.offices["ANALYST-OFFICE-001"]

        hypotheses = HypothesisFramework().generate(office, source_reports())

        self.assertEqual(len(hypotheses), 1)
        self.assertEqual(hypotheses[0].hypothesis_id, "HYP-ANALYST-OFFICE-001-001")
        self.assertEqual(hypotheses[0].source_report_ids, ("DOC-201", "DOC-301", "DOC-401"))

    def test_evidence_evaluation_classifies_source_reports(self) -> None:
        evaluations = EvidenceEvaluationFramework().evaluate(source_reports())
        by_report = {evaluation.source_report_id: evaluation for evaluation in evaluations}

        self.assertEqual(by_report["DOC-201"].evidence_class, "opportunity_evidence")
        self.assertEqual(by_report["DOC-301"].evidence_class, "threat_evidence")
        self.assertEqual(by_report["DOC-401"].evidence_class, "fusion_evidence")
        self.assertEqual(by_report["DOC-401"].weight, 0.9)

    def test_aar_generation_persists_assessment_without_modifying_seeker_reports(self) -> None:
        analyst = department()
        reports = source_reports()
        before = tuple(report.to_json() for report in reports)

        aar = analyst.generate_aar("ANALYST-OFFICE-001", reports, "CF-001", "TC-001", 1301, "PROMPT-029")
        after = tuple(report.to_json() for report in reports)

        self.assertEqual(before, after)
        self.assertEqual(aar.contract_id, "DOC-1301")
        self.assertEqual(aar.contract_type, "AAR")
        self.assertEqual(aar.produced_by_group_id, "DEP-004")
        self.assertFalse(aar.machine_payload["seeker_reports_modified"])
        self.assertFalse(aar.machine_payload["risk_office_override"])
        self.assertIsNotNone(analyst.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-1301"))

    def test_every_office_produces_analytical_assessment_report(self) -> None:
        analyst = department()

        for index, office_id in enumerate(sorted(analyst.offices), start=1):
            aar = analyst.generate_aar(office_id, source_reports(), "CF-001", "TC-001", 1400 + index, "PROMPT-029")
            self.assertEqual(aar.contract_type, "AAR")
            self.assertEqual(aar.machine_payload["office_id"], office_id)

    def test_office_routing_uses_courier_and_generates_audit(self) -> None:
        analyst = department()
        aar = analyst.generate_aar("ANALYST-OFFICE-001", source_reports(), "CF-001", "TC-001", 1501, "PROMPT-029")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = analyst.route_aar("ANALYST-OFFICE-001", aar, executive_inbox)
        event_types = [event.event_type for event in analyst.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-1501"), aar)
        self.assertEqual(analyst.offices["ANALYST-OFFICE-001"].routed_reports, 1)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panels_are_complete(self) -> None:
        analyst = department()
        aar = analyst.generate_aar("ANALYST-OFFICE-001", source_reports(), "CF-001", "TC-001", 1601, "PROMPT-029")
        analyst.route_aar("ANALYST-OFFICE-001", aar, IncomingMailbox("STF-002", "DEP-002"))

        panels = analyst.instrument_panels()

        self.assertEqual(len(panels), 9)
        self.assertEqual(panels[0].office_id, "ANALYST-OFFICE-001")
        self.assertEqual(panels[0].metrics.reports_generated, 1)
        self.assertEqual(panels[0].metrics.routed_reports, 1)
        self.assertEqual(panels[0].health.status, "healthy")

    def test_aar_payload_preserves_boundaries(self) -> None:
        analyst = department()

        aar = analyst.generate_aar("ANALYST-OFFICE-002", source_reports(), "CF-001", "TC-001", 1701, "PROMPT-029")

        self.assertNotIn("discovered_opportunity", aar.machine_payload)
        self.assertNotIn("trade_recommendation", aar.machine_payload)
        self.assertNotIn("execution_instruction", aar.machine_payload)
        self.assertNotIn("position_size", aar.machine_payload)


if __name__ == "__main__":
    unittest.main()
