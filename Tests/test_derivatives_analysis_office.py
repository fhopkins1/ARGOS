from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    DerivativesAnalysisOffice,
    DerivativesAnalysisOfficeChief,
    DerivativesReasoningObservation,
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
            prompt_id="PROMPT-034",
            title="Derivatives Analyst AAR Prompt",
            owner_group_id="DEP-004",
            author_staff_id="STF-035",
            purpose="Generate deterministic Derivatives Analytical Assessment Reports.",
            allowed_environments=("development",),
            input_contract_types=("IAR", "OTR"),
            output_contract_types=("AAR",),
            dependencies=("EO-034",),
            safety_notes="No trade recommendation, execution, command decision, source modification, or thesis suppression.",
        ),
        "1.0.0",
        "Create deterministic derivatives assessment only.",
    )
    return repository


def observation() -> DerivativesReasoningObservation:
    return DerivativesReasoningObservation(
        implied_volatility=0.62,
        historical_volatility=0.38,
        options_volume_ratio=3.0,
        dealer_gamma_position=-1200000,
        gamma_exposure=-800000,
        delta_exposure=900000,
        skew=0.31,
        open_interest_change=50000,
        days_to_expiration=3,
        institutional_notional=2500000,
    )


def source_report() -> OperationalContract:
    created = utc_timestamp()
    payload = {"office_id": "SEEKER-OFFICE-005", "report_status": "institutional_activity_identified"}
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id="DOC-601",
        contract_type="IAR",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id="STF-025",
        produced_by_group_id="DEP-003",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic options-flow Seeker source.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def office() -> DerivativesAnalysisOffice:
    return DerivativesAnalysisOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class DerivativesAnalysisOfficeTests(unittest.TestCase):
    def test_derivative_reasoning_is_deterministic(self) -> None:
        reasoning = DerivativesAnalysisOfficeChief().analyze(observation())

        self.assertEqual(reasoning["volatility"]["volatility_state"], "elevated_iv_premium")
        self.assertEqual(reasoning["options_flow"]["options_flow"], "unusual_options_activity")
        self.assertEqual(reasoning["dealer_positioning"]["dealer_positioning"], "dealer_short_gamma")
        self.assertEqual(reasoning["gamma"]["gamma_risk"], "elevated_gamma_risk")
        self.assertEqual(reasoning["derivatives_conclusion"], {"primary_scenario": "volatility_expansion", "probability": 0.4932})

    def test_probability_landscape_is_reproducible(self) -> None:
        reasoning = DerivativesAnalysisOfficeChief().analyze(observation())
        landscape = reasoning["probability_landscape"]

        self.assertEqual(landscape["landscape_id"], "DPL-001")
        self.assertEqual(len(landscape["scenarios"]), 3)
        self.assertEqual(landscape["scenarios"][0], {"scenario": "volatility_expansion", "probability": 0.4932})
        self.assertEqual(landscape["scenarios"][1], {"scenario": "institutional_positioning", "probability": 0.3378})
        self.assertEqual(landscape["scenarios"][2], {"scenario": "volatility_normalization", "probability": 0.1689})

    def test_competing_thesis_analysis_preserves_multiple_explanations(self) -> None:
        reasoning = DerivativesAnalysisOfficeChief().analyze(observation())
        theses = reasoning["competing_theses"]

        self.assertEqual(len(theses), 3)
        self.assertEqual(tuple(thesis["thesis_id"] for thesis in theses), ("DTA-001", "DTA-002", "DTA-003"))
        self.assertEqual(theses[2]["name"], "volatility_normalization")

    def test_reasoning_graph_generation_references_competing_theses(self) -> None:
        chief = DerivativesAnalysisOfficeChief()
        reasoning = chief.analyze(observation())

        graphs = chief.reasoning_graphs(reasoning, ("DOC-601",))

        self.assertEqual(len(graphs), 1)
        self.assertEqual(graphs[0].conclusion_id, "DERIVATIVES-CONCLUSION-001")
        self.assertEqual(graphs[0].competing_hypotheses, ("DTA-001", "DTA-002", "DTA-003"))

    def test_derivatives_aar_generation_persists_reasoning_payload(self) -> None:
        derivatives = office()

        aar = derivatives.generate_derivatives_aar(observation(), (source_report(),), "CF-001", "TC-001", 2201, "PROMPT-034")

        self.assertEqual(aar.contract_type, "AAR")
        self.assertEqual(aar.machine_payload["assessment_status"], "derivatives_analytical_assessment")
        self.assertEqual(aar.machine_payload["probability_landscape"]["landscape_id"], "DPL-001")
        self.assertEqual(len(aar.machine_payload["competing_thesis_analysis"]), 3)
        self.assertIsNotNone(derivatives.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-2201"))

    def test_derivatives_aar_preserves_boundaries_and_source_intelligence(self) -> None:
        derivatives = office()
        source = source_report()
        before = source.to_json()

        aar = derivatives.generate_derivatives_aar(observation(), (source,), "CF-001", "TC-001", 2202, "PROMPT-034")

        self.assertEqual(source.to_json(), before)
        self.assertFalse(aar.machine_payload["seeker_intelligence_modified"])
        self.assertFalse(aar.machine_payload["risk_office_override"])
        self.assertNotIn("trade_recommendation", aar.machine_payload)
        self.assertNotIn("execution_instruction", aar.machine_payload)
        self.assertNotIn("command_decision", aar.machine_payload)

    def test_courier_routing_generates_audit_events(self) -> None:
        derivatives = office()
        aar = derivatives.generate_derivatives_aar(observation(), (source_report(),), "CF-001", "TC-001", 2203, "PROMPT-034")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = derivatives.route_aar(aar, executive_inbox)
        event_types = [event.event_type for event in derivatives.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-2203"), aar)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        derivatives = office()
        aar = derivatives.generate_derivatives_aar(observation(), (source_report(),), "CF-001", "TC-001", 2204, "PROMPT-034")
        derivatives.route_aar(aar, IncomingMailbox("STF-002", "DEP-002"))

        panel = derivatives.instrument_panel()

        self.assertEqual(panel.office_id, "ANALYST-OFFICE-005")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")


if __name__ == "__main__":
    unittest.main()
