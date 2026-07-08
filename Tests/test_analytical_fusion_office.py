from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    AnalyticalFusionInput,
    AnalyticalFusionOffice,
    AnalyticalFusionOfficeChief,
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
            prompt_id="PROMPT-038",
            title="Analytical Fusion AAR Prompt",
            owner_group_id="DEP-004",
            author_staff_id="STF-039",
            purpose="Generate deterministic Analytical Fusion Reports.",
            allowed_environments=("development",),
            input_contract_types=("AAR",),
            output_contract_types=("AAR",),
            dependencies=("EO-038",),
            safety_notes="No new analysis, analyst conclusion modification, disagreement suppression, uncertainty discard, or Command Decision.",
        ),
        "1.0.0",
        "Create deterministic analytical fusion assessment only.",
    )
    return repository


def fusion_inputs() -> tuple[AnalyticalFusionInput, ...]:
    return (
        AnalyticalFusionInput(
            "ANALYST-OFFICE-001",
            "DOC-1001",
            "risk_elevated",
            {"model_id": "SDM-001", "decision_state": "risk_elevated"},
            {"nodes": ("claim:statistical", "evidence:probability")},
            {"scenarios": ({"scenario": "risk_elevated", "probability": 0.6}, {"scenario": "trend_persistent", "probability": 0.4})},
            ("EV-1", "EV-2"),
            ("U-1", "U-COMMON"),
            0.7,
        ),
        AnalyticalFusionInput(
            "ANALYST-OFFICE-002",
            "DOC-1002",
            "trend_persistent",
            {"model_id": "TDM-001", "decision_state": "trend_persistent"},
            {"nodes": ("claim:technical", "evidence:trend")},
            {"scenarios": ({"scenario": "risk_elevated", "probability": 0.45}, {"scenario": "trend_persistent", "probability": 0.55})},
            ("EV-3", "EV-COMMON"),
            ("U-2", "U-COMMON"),
            0.6,
        ),
        AnalyticalFusionInput(
            "ANALYST-OFFICE-006",
            "DOC-1003",
            "risk_elevated",
            {"model_id": "BDM-001", "decision_state": "behavioral_risk_elevated"},
            {"nodes": ("claim:behavioral", "evidence:crowd")},
            {"scenarios": ({"scenario": "risk_elevated", "probability": 0.7}, {"scenario": "sentiment_normalization", "probability": 0.3})},
            ("EV-4", "EV-COMMON"),
            ("U-3", "U-COMMON"),
            0.8,
        ),
        AnalyticalFusionInput(
            "ANALYST-OFFICE-007",
            "DOC-1004",
            "risk_elevated",
            {"model_id": "RRR-001", "decision_state": "review_required"},
            {"nodes": ("claim:risk_readiness", "evidence:stress")},
            {"scenarios": ({"scenario": "risk_elevated", "probability": 0.65}, {"scenario": "review_required", "probability": 0.35})},
            ("EV-5", "EV-COMMON"),
            ("U-4", "U-COMMON"),
            0.5,
        ),
    )


def source_report(contract_id: str, staff_id: str) -> OperationalContract:
    created = utc_timestamp()
    payload = {"source": contract_id, "assessment_status": "analytical_assessment"}
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=contract_id,
        contract_type="AAR",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id=staff_id,
        produced_by_group_id="DEP-004",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic Analyst source.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def source_reports() -> tuple[OperationalContract, ...]:
    return (
        source_report("DOC-1001", "STF-031"),
        source_report("DOC-1002", "STF-032"),
        source_report("DOC-1003", "STF-036"),
        source_report("DOC-1004", "STF-037"),
    )


def office() -> AnalyticalFusionOffice:
    return AnalyticalFusionOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class AnalyticalFusionOfficeTests(unittest.TestCase):
    def test_decision_model_fusion_preserves_sources(self) -> None:
        reasoning = AnalyticalFusionOfficeChief().analyze(fusion_inputs())
        udm = reasoning["unified_decision_model"]

        self.assertEqual(udm["model_id"], "UDM-001")
        self.assertEqual(udm["primary_conclusion"], "risk_elevated")
        self.assertTrue(udm["disagreement_preserved"])
        self.assertEqual(tuple(model["source_report_id"] for model in udm["source_models"]), ("DOC-1001", "DOC-1002", "DOC-1003", "DOC-1004"))

    def test_reasoning_graph_integration_preserves_traceability(self) -> None:
        reasoning = AnalyticalFusionOfficeChief().analyze(fusion_inputs())
        org = reasoning["organizational_reasoning_graph"]

        self.assertEqual(org["graph_id"], "ORG-001")
        self.assertEqual(org["source_report_ids"], ("DOC-1001", "DOC-1002", "DOC-1003", "DOC-1004"))
        self.assertIn("source:DOC-1001", org["nodes"])
        self.assertIn(("source:DOC-1002", "claim:unified_decision_model", "contributes"), org["edges"])

    def test_probability_landscape_integration_is_deterministic(self) -> None:
        reasoning = AnalyticalFusionOfficeChief().analyze(fusion_inputs())
        landscape = reasoning["integrated_probability_landscape"]

        self.assertEqual(landscape["landscape_id"], "AFL-001")
        self.assertIn({"scenario": "risk_elevated", "mean_probability": 0.6, "source_count": 4}, landscape["scenarios"])
        self.assertIn({"scenario": "trend_persistent", "mean_probability": 0.475, "source_count": 2}, landscape["scenarios"])

    def test_consensus_and_conflict_are_documented(self) -> None:
        reasoning = AnalyticalFusionOfficeChief().analyze(fusion_inputs())

        self.assertEqual(reasoning["consensus"]["consensus_conclusion"], "risk_elevated")
        self.assertEqual(reasoning["consensus"]["agreement_score"], 0.75)
        self.assertEqual(reasoning["conflicts"]["conflict_state"], "conflict_present")
        self.assertEqual(reasoning["conflicts"]["conflicts"][0]["source_report_id"], "DOC-1002")

    def test_evidence_diversity_and_confidence_scores_are_reproducible(self) -> None:
        reasoning = AnalyticalFusionOfficeChief().analyze(fusion_inputs())

        self.assertEqual(reasoning["independent_evidence_score"], 0.75)
        self.assertEqual(reasoning["intellectual_diversity_score"], 0.75)
        self.assertEqual(reasoning["organizational_confidence"], 0.56)
        self.assertEqual(reasoning["analytical_fusion_report"]["report_id"], "AFR-001")

    def test_analytical_fusion_aar_generation_persists_payload(self) -> None:
        fusion = office()

        aar = fusion.generate_analytical_fusion_aar(fusion_inputs(), source_reports(), "CF-001", "TC-001", 2601, "PROMPT-038")

        self.assertEqual(aar.contract_type, "AAR")
        self.assertEqual(aar.machine_payload["assessment_status"], "analytical_fusion_assessment")
        self.assertEqual(aar.machine_payload["unified_decision_model"]["model_id"], "UDM-001")
        self.assertEqual(aar.machine_payload["organizational_reasoning_graph"]["graph_id"], "ORG-001")
        self.assertIsNotNone(fusion.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-2601"))

    def test_analytical_fusion_preserves_boundaries_and_uncertainty(self) -> None:
        fusion = office()
        reports = source_reports()
        before = tuple(report.to_json() for report in reports)

        aar = fusion.generate_analytical_fusion_aar(fusion_inputs(), reports, "CF-001", "TC-001", 2602, "PROMPT-038")

        self.assertEqual(tuple(report.to_json() for report in reports), before)
        self.assertFalse(aar.machine_payload["new_analysis_created"])
        self.assertFalse(aar.machine_payload["analyst_conclusions_modified"])
        self.assertFalse(aar.machine_payload["disagreement_suppressed"])
        self.assertFalse(aar.machine_payload["uncertainty_discarded"])
        self.assertNotIn("command_decision", aar.machine_payload)

    def test_courier_routing_generates_audit_events(self) -> None:
        fusion = office()
        aar = fusion.generate_analytical_fusion_aar(fusion_inputs(), source_reports(), "CF-001", "TC-001", 2603, "PROMPT-038")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = fusion.route_aar(aar, executive_inbox)
        event_types = [event.event_type for event in fusion.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-2603"), aar)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        fusion = office()
        aar = fusion.generate_analytical_fusion_aar(fusion_inputs(), source_reports(), "CF-001", "TC-001", 2604, "PROMPT-038")
        fusion.route_aar(aar, IncomingMailbox("STF-002", "DEP-002"))

        panel = fusion.instrument_panel()

        self.assertEqual(panel.office_id, "ANALYST-OFFICE-009")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")


if __name__ == "__main__":
    unittest.main()
