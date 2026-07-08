from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    BehavioralAnalysisOffice,
    BehavioralAnalysisOfficeChief,
    BehavioralReasoningObservation,
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
            prompt_id="PROMPT-035",
            title="Behavioral Analyst AAR Prompt",
            owner_group_id="DEP-004",
            author_staff_id="STF-036",
            purpose="Generate deterministic Behavioral Analytical Assessment Reports.",
            allowed_environments=("development",),
            input_contract_types=("STR", "IGR", "MIR"),
            output_contract_types=("AAR",),
            dependencies=("EO-035",),
            safety_notes="No trade recommendation, execution, command decision, source modification, or competing explanation suppression.",
        ),
        "1.0.0",
        "Create deterministic behavioral assessment only.",
    )
    return repository


def observation() -> BehavioralReasoningObservation:
    return BehavioralReasoningObservation(
        crowd_participation=0.82,
        narrative_velocity=0.74,
        sentiment_score=0.68,
        institutional_accumulation=0.62,
        retail_chase_score=0.71,
        fear_greed_index=82,
        regime_stress=0.63,
        bias_intensity=0.58,
        reflexivity_feedback=0.66,
    )


def source_report() -> OperationalContract:
    created = utc_timestamp()
    payload = {"office_id": "SEEKER-OFFICE-004", "report_status": "sentiment_threat_identified"}
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id="DOC-701",
        contract_type="STR",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id="STF-024",
        produced_by_group_id="DEP-003",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic News and Sentiment Seeker source.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def office() -> BehavioralAnalysisOffice:
    return BehavioralAnalysisOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class BehavioralAnalysisOfficeTests(unittest.TestCase):
    def test_behavioral_reasoning_is_deterministic(self) -> None:
        reasoning = BehavioralAnalysisOfficeChief().analyze(observation())

        self.assertEqual(reasoning["crowd_psychology"]["crowd_psychology"], "crowd_euphoric")
        self.assertEqual(reasoning["narrative"]["narrative"], "narrative_accelerating")
        self.assertEqual(reasoning["sentiment"]["sentiment"], "sentiment_bullish")
        self.assertEqual(reasoning["reflexivity"]["reflexivity"], "positive_feedback_loop")
        self.assertEqual(reasoning["behavioral_conclusion"], {"primary_scenario": "crowding_reversal", "probability": 0.5018})

    def test_decision_model_generation_is_required_and_explainable(self) -> None:
        reasoning = BehavioralAnalysisOfficeChief().analyze(observation())
        model = reasoning["decision_model"]

        self.assertEqual(model["model_id"], "BDM-001")
        self.assertEqual(model["decision_state"], "behavioral_risk_elevated")
        self.assertIn("crowd_euphoric", model["drivers"])
        self.assertIn("normalization_thesis_preserved_for_competing_explanation", model["inhibitors"])

    def test_probability_landscape_is_reproducible(self) -> None:
        reasoning = BehavioralAnalysisOfficeChief().analyze(observation())
        landscape = reasoning["probability_landscape"]

        self.assertEqual(landscape["landscape_id"], "BPL-001")
        self.assertEqual(len(landscape["scenarios"]), 3)
        self.assertEqual(landscape["scenarios"][0], {"scenario": "crowding_reversal", "probability": 0.5018})
        self.assertEqual(landscape["scenarios"][1], {"scenario": "trend_persistence", "probability": 0.3273})
        self.assertEqual(landscape["scenarios"][2], {"scenario": "sentiment_normalization", "probability": 0.1709})

    def test_competing_thesis_analysis_preserves_multiple_explanations(self) -> None:
        reasoning = BehavioralAnalysisOfficeChief().analyze(observation())
        theses = reasoning["competing_theses"]

        self.assertEqual(len(theses), 3)
        self.assertEqual(tuple(thesis["thesis_id"] for thesis in theses), ("BTA-001", "BTA-002", "BTA-003"))
        self.assertEqual(theses[1]["name"], "trend_persistence")

    def test_reasoning_graph_generation_references_competing_theses(self) -> None:
        chief = BehavioralAnalysisOfficeChief()
        reasoning = chief.analyze(observation())

        graphs = chief.reasoning_graphs(reasoning, ("DOC-701",))

        self.assertEqual(len(graphs), 1)
        self.assertEqual(graphs[0].conclusion_id, "BEHAVIORAL-CONCLUSION-001")
        self.assertEqual(graphs[0].competing_hypotheses, ("BTA-001", "BTA-002", "BTA-003"))

    def test_behavioral_aar_generation_persists_reasoning_payload(self) -> None:
        behavioral = office()

        aar = behavioral.generate_behavioral_aar(observation(), (source_report(),), "CF-001", "TC-001", 2301, "PROMPT-035")

        self.assertEqual(aar.contract_type, "AAR")
        self.assertEqual(aar.machine_payload["assessment_status"], "behavioral_analytical_assessment")
        self.assertEqual(aar.machine_payload["decision_model"]["model_id"], "BDM-001")
        self.assertEqual(aar.machine_payload["probability_landscape"]["landscape_id"], "BPL-001")
        self.assertIsNotNone(behavioral.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-2301"))

    def test_behavioral_aar_preserves_boundaries_and_source_intelligence(self) -> None:
        behavioral = office()
        source = source_report()
        before = source.to_json()

        aar = behavioral.generate_behavioral_aar(observation(), (source,), "CF-001", "TC-001", 2302, "PROMPT-035")

        self.assertEqual(source.to_json(), before)
        self.assertFalse(aar.machine_payload["seeker_intelligence_modified"])
        self.assertFalse(aar.machine_payload["risk_office_override"])
        self.assertNotIn("trade_recommendation", aar.machine_payload)
        self.assertNotIn("execution_instruction", aar.machine_payload)
        self.assertNotIn("command_decision", aar.machine_payload)

    def test_courier_routing_generates_audit_events(self) -> None:
        behavioral = office()
        aar = behavioral.generate_behavioral_aar(observation(), (source_report(),), "CF-001", "TC-001", 2303, "PROMPT-035")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = behavioral.route_aar(aar, executive_inbox)
        event_types = [event.event_type for event in behavioral.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-2303"), aar)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        behavioral = office()
        aar = behavioral.generate_behavioral_aar(observation(), (source_report(),), "CF-001", "TC-001", 2304, "PROMPT-035")
        behavioral.route_aar(aar, IncomingMailbox("STF-002", "DEP-002"))

        panel = behavioral.instrument_panel()

        self.assertEqual(panel.office_id, "ANALYST-OFFICE-006")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")


if __name__ == "__main__":
    unittest.main()
