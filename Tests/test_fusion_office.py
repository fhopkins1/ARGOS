from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.contracts import OperationalContract, utc_timestamp  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402
from argos.seeker import FusionOffice  # noqa: E402


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
            prompt_id="PROMPT-027",
            title="Fusion Report Prompt",
            owner_group_id="DEP-003",
            author_staff_id="STF-029",
            purpose="Generate deterministic multi-office fusion reports.",
            allowed_environments=("development",),
            input_contract_types=("COR", "ATR", "AIR"),
            output_contract_types=("MIR", "CFR", "ICR"),
            dependencies=("EO-027",),
            safety_notes="No original intelligence, report modification, trade recommendations, or confidence averaging.",
        ),
        "1.0.0",
        "Fuse only existing Seeker reports deterministically.",
    )
    return repository


def report(
    contract_id: str,
    contract_type: str,
    staff_id: str,
    office_id: str,
    signal_key: str,
    signals: list[dict],
) -> OperationalContract:
    created = utc_timestamp()
    payload = {
        "office_id": office_id,
        "office_name": f"Office {office_id}",
        "report_status": "source_report",
        signal_key: signals,
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
        human_summary="Synthetic source report.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def source_reports() -> tuple[OperationalContract, ...]:
    return (
        report(
            "DOC-201",
            "COR",
            "STF-021",
            "SEEKER-OFFICE-001",
            "technical_signals",
            [
                {"seeker": "demand", "signal": "demand_positive", "report_hint": "opportunity"},
                {"seeker": "liquidity", "signal": "liquidity_orderly", "report_hint": "opportunity"},
            ],
        ),
        report(
            "DOC-1005",
            "AIR",
            "STF-028",
            "SEEKER-OFFICE-008",
            "alternative_data_signals",
            [{"seeker": "demand", "signal": "web_traffic_expanding", "report_hint": "opportunity"}],
        ),
        report(
            "DOC-1001",
            "ATR",
            "STF-028",
            "SEEKER-OFFICE-008",
            "alternative_data_signals",
            [{"seeker": "demand", "signal": "shipping_delay_threat", "report_hint": "threat"}],
        ),
    )


def office() -> FusionOffice:
    return FusionOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class FusionOfficeTests(unittest.TestCase):
    def test_fusion_extracts_findings_without_modifying_source_reports(self) -> None:
        fusion = office()
        reports = source_reports()
        before = tuple(report.to_json() for report in reports)

        assessment = fusion.fuse(reports)
        after = tuple(report.to_json() for report in reports)

        self.assertEqual(before, after)
        self.assertEqual(len(assessment.findings), 4)
        self.assertFalse(any("trade_recommendation" in finding.signal for finding in assessment.findings))

    def test_conflict_detection_preserves_opposing_evidence(self) -> None:
        assessment = office().fuse(source_reports())

        self.assertEqual(len(assessment.conflicts), 1)
        conflict = assessment.conflicts[0]
        self.assertEqual(conflict.seeker, "demand")
        self.assertIn("DOC-201", conflict.opportunity_report_ids)
        self.assertIn("DOC-1001", conflict.threat_report_ids)

    def test_agreement_scoring_and_corroboration_are_deterministic(self) -> None:
        assessment = office().fuse(source_reports())

        self.assertIn("demand", assessment.corroborated_seekers)
        self.assertEqual(assessment.agreement_score, 0.4)

    def test_evidence_classification_and_confidence_calculation(self) -> None:
        assessment = office().fuse(source_reports())

        self.assertEqual(
            assessment.evidence_classes,
            ("opportunity_evidence", "specialized_intelligence_evidence", "threat_evidence"),
        )
        self.assertEqual(assessment.evidence_diversity, 3)
        self.assertEqual(assessment.confidence, 0.52)

    def test_mir_cfr_and_icr_generation_persist_reports(self) -> None:
        fusion = office()
        reports = source_reports()

        mir = fusion.generate_mir(reports, "CF-001", "TC-001", 1101, "PROMPT-027")
        cfr = fusion.generate_conflict_report(reports, "CF-001", "TC-001", 1102, "PROMPT-027")
        icr = fusion.generate_corroboration_report(reports, "CF-001", "TC-001", 1103, "PROMPT-027")

        self.assertEqual(mir.contract_type, "MIR")
        self.assertEqual(cfr.contract_type, "CFR")
        self.assertEqual(icr.contract_type, "ICR")
        self.assertEqual(mir.parent_contract_ids, ("DOC-201", "DOC-1005", "DOC-1001"))
        self.assertFalse(mir.machine_payload["source_reports_modified"])
        self.assertIsNotNone(fusion.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-1103"))

    def test_courier_routing_and_audit_generation(self) -> None:
        fusion = office()
        mir = fusion.generate_mir(source_reports(), "CF-001", "TC-001", 1104, "PROMPT-027")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = fusion.route_report(mir, executive_inbox)
        event_types = [event.event_type for event in fusion.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-1104"), mir)
        self.assertEqual(fusion.routed_reports, 1)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_updates_and_reflects_conflicts(self) -> None:
        fusion = office()
        mir = fusion.generate_mir(source_reports(), "CF-001", "TC-001", 1105, "PROMPT-027")
        fusion.route_report(mir, IncomingMailbox("STF-002", "DEP-002"))

        panel = fusion.instrument_panel()

        self.assertEqual(panel.office_id, "SEEKER-OFFICE-009")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "attention")
        self.assertIn("conflicts_present", panel.health.reasons)


if __name__ == "__main__":
    unittest.main()
