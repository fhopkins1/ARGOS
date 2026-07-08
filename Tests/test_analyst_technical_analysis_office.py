from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    AnalystTechnicalAnalysisOffice,
    PatternReliabilityAnalyst,
    TechnicalAnalysisOfficeChief,
    TechnicalReasoningObservation,
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
            prompt_id="PROMPT-031",
            title="Technical Analyst AAR Prompt",
            owner_group_id="DEP-004",
            author_staff_id="STF-032",
            purpose="Generate deterministic Technical Analytical Assessment Reports.",
            allowed_environments=("development",),
            input_contract_types=("SEEKER_TECHNICAL_REPORT",),
            output_contract_types=("AAR",),
            dependencies=("EO-031",),
            safety_notes="No discovery, trade recommendation, execution, command decisions, source modification, or Risk Office override.",
        ),
        "1.0.0",
        "Create deterministic technical assessment only.",
    )
    return repository


def observation() -> TechnicalReasoningObservation:
    return TechnicalReasoningObservation(
        closes=(100, 102, 105, 107),
        highs=(101, 103, 106, 108),
        lows=(99, 100, 103, 104),
        volumes=(1000, 1200, 1300, 1800),
        benchmark_closes=(100, 101, 102, 103),
        historical_pattern_successes=7,
        historical_pattern_trials=10,
        timeframe_alignment_score=0.72,
    )


def contradictory_observation() -> TechnicalReasoningObservation:
    return TechnicalReasoningObservation(
        closes=(100, 102, 105, 107),
        highs=(101, 103, 106, 108),
        lows=(99, 100, 103, 104),
        volumes=(1000, 1200, 1300, 900),
        benchmark_closes=(100, 101, 102, 103),
        historical_pattern_successes=4,
        historical_pattern_trials=10,
        timeframe_alignment_score=0.72,
    )


def source_report() -> OperationalContract:
    created = utc_timestamp()
    payload = {"office_id": "SEEKER-OFFICE-001", "report_status": "technical_candidate_unanalysed"}
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id="DOC-301",
        contract_type="COR",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id="STF-021",
        produced_by_group_id="DEP-003",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic technical Seeker source.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def office() -> AnalystTechnicalAnalysisOffice:
    return AnalystTechnicalAnalysisOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class AnalystTechnicalAnalysisOfficeTests(unittest.TestCase):
    def test_technical_reasoning_is_deterministic(self) -> None:
        reasoning = TechnicalAnalysisOfficeChief().reason(observation())

        self.assertEqual(reasoning["trend"]["trend"], "rising")
        self.assertEqual(reasoning["momentum"]["momentum"], "positive")
        self.assertEqual(reasoning["market_structure"]["structure"], "higher_high_higher_low")
        self.assertEqual(reasoning["volume"]["volume_state"], "expanding")
        self.assertEqual(reasoning["technical_fusion"]["technical_conclusion"], "technically_confirmed")

    def test_pattern_reliability_and_historical_validation(self) -> None:
        reliability = PatternReliabilityAnalyst().evaluate(7, 10)

        self.assertEqual(reliability, {"reliability": 0.7, "grade": "high"})

    def test_argument_graph_generation_preserves_contradictory_evidence(self) -> None:
        chief = TechnicalAnalysisOfficeChief()
        reasoning = chief.reason(contradictory_observation())

        graphs = chief.argument_graphs(reasoning, ("DOC-301",))
        alternatives = chief.alternative_explanations(reasoning)

        self.assertEqual(len(graphs), 1)
        self.assertEqual(graphs[0].conclusion_id, "TECH-CONCLUSION-001")
        self.assertIn("pattern_reliability", graphs[0].contradictory_evidence)
        self.assertIn("failed breakout", alternatives[0])

    def test_technical_aar_generation_persists_reasoning_payload(self) -> None:
        technical = office()

        aar = technical.generate_technical_aar(observation(), (source_report(),), "CF-001", "TC-001", 1901, "PROMPT-031")

        self.assertEqual(aar.contract_type, "AAR")
        self.assertEqual(aar.machine_payload["assessment_status"], "technical_analytical_assessment")
        self.assertIn("technical_reasoning", aar.machine_payload)
        self.assertIn("technical_argument_graphs", aar.machine_payload)
        self.assertEqual(aar.machine_payload["historical_pattern_reliability"]["grade"], "high")
        self.assertIsNotNone(technical.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-1901"))

    def test_technical_aar_preserves_boundaries_and_source_intelligence(self) -> None:
        technical = office()
        source = source_report()
        before = source.to_json()

        aar = technical.generate_technical_aar(observation(), (source,), "CF-001", "TC-001", 1902, "PROMPT-031")

        self.assertEqual(source.to_json(), before)
        self.assertFalse(aar.machine_payload["seeker_intelligence_modified"])
        self.assertFalse(aar.machine_payload["risk_office_override"])
        self.assertNotIn("trade_recommendation", aar.machine_payload)
        self.assertNotIn("execution_instruction", aar.machine_payload)
        self.assertNotIn("command_decision", aar.machine_payload)

    def test_courier_routing_generates_audit_events(self) -> None:
        technical = office()
        aar = technical.generate_technical_aar(observation(), (source_report(),), "CF-001", "TC-001", 1903, "PROMPT-031")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = technical.route_aar(aar, executive_inbox)
        event_types = [event.event_type for event in technical.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-1903"), aar)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        technical = office()
        aar = technical.generate_technical_aar(observation(), (source_report(),), "CF-001", "TC-001", 1904, "PROMPT-031")
        technical.route_aar(aar, IncomingMailbox("STF-002", "DEP-002"))

        panel = technical.instrument_panel()

        self.assertEqual(panel.office_id, "ANALYST-OFFICE-002")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")


if __name__ == "__main__":
    unittest.main()
