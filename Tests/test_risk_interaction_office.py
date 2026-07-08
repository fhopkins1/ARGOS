from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    RiskInteractionObservation,
    RiskInteractionOffice,
    RiskInteractionOfficeChief,
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
            prompt_id="PROMPT-036",
            title="Risk Interaction Analyst AAR Prompt",
            owner_group_id="DEP-004",
            author_staff_id="STF-037",
            purpose="Generate deterministic Risk Interaction pressure-test reports.",
            allowed_environments=("development",),
            input_contract_types=("AAR", "BDM"),
            output_contract_types=("AAR",),
            dependencies=("EO-036",),
            safety_notes="No trade recommendation, execution, Risk Office override, Decision Model modification, or Command Decision.",
        ),
        "1.0.0",
        "Create deterministic Risk Interaction assessment only.",
    )
    return repository


def observation() -> RiskInteractionObservation:
    return RiskInteractionObservation(
        decision_model_id="BDM-001",
        decision_state="behavioral_risk_elevated",
        assumption_count=6,
        weak_assumption_count=2,
        scenario_count=3,
        stress_severity=0.65,
        contradiction_count=1,
        uncertainty_score=0.52,
        missing_evidence_count=1,
        failure_mode_count=2,
        devil_advocate_strength=0.7,
    )


def decision_model() -> dict[str, object]:
    return {
        "model_id": "BDM-001",
        "decision_state": "behavioral_risk_elevated",
        "drivers": ["crowd_euphoric", "positive_feedback_loop"],
        "inhibitors": ["normalization_thesis_preserved_for_competing_explanation"],
    }


def source_report() -> OperationalContract:
    created = utc_timestamp()
    payload = {"office_id": "ANALYST-OFFICE-006", "decision_model": decision_model()}
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id="DOC-801",
        contract_type="AAR",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id="STF-036",
        produced_by_group_id="DEP-004",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic Behavioral Analyst source.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def office() -> RiskInteractionOffice:
    return RiskInteractionOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class RiskInteractionOfficeTests(unittest.TestCase):
    def test_stress_testing_and_scenario_generation_are_deterministic(self) -> None:
        reasoning = RiskInteractionOfficeChief().analyze(observation())
        stress_test = reasoning["analytical_stress_test"]

        self.assertEqual(stress_test["test_id"], "AST-001")
        self.assertEqual(stress_test["stress_state"], "stress_elevated")
        self.assertEqual(stress_test["scenarios"][0], {"scenario": "base_case", "stress_impact": 0.325})
        self.assertEqual(stress_test["scenarios"][2], {"scenario": "extreme_case", "stress_impact": 0.8125})

    def test_risk_readiness_scoring_and_confidence_adjustment(self) -> None:
        reasoning = RiskInteractionOfficeChief().analyze(observation())
        readiness = reasoning["risk_readiness_report"]

        self.assertEqual(readiness["report_id"], "RRR-001")
        self.assertEqual(readiness["readiness_score"], 28)
        self.assertEqual(readiness["readiness_state"], "not_risk_ready")
        self.assertEqual(reasoning["confidence_adjustment_recommendation"], {"method": "risk_readiness_penalty", "adjustment": -0.36})

    def test_challenge_report_identifies_weak_assumptions(self) -> None:
        reasoning = RiskInteractionOfficeChief().analyze(observation())
        challenge = reasoning["decision_model_challenge_report"]

        self.assertEqual(challenge["challenge_id"], "DMCR-001")
        self.assertEqual(challenge["challenged_model_id"], "BDM-001")
        self.assertEqual(challenge["challenge_state"], "material_challenge")
        self.assertIn("weak_assumptions_identified", challenge["findings"])
        self.assertIn("contradictions_present", challenge["findings"])

    def test_reasoning_graph_generation_references_risk_readiness(self) -> None:
        chief = RiskInteractionOfficeChief()
        reasoning = chief.analyze(observation())

        graphs = chief.reasoning_graphs(reasoning, ("DOC-801",))

        self.assertEqual(len(graphs), 1)
        self.assertEqual(graphs[0].conclusion_id, "RISK-INTERACTION-CONCLUSION-001")
        self.assertIn("claim:risk_readiness", graphs[0].nodes)

    def test_risk_interaction_aar_generation_persists_pressure_test_payload(self) -> None:
        risk_interaction = office()

        aar = risk_interaction.generate_risk_interaction_aar(observation(), decision_model(), (source_report(),), "CF-001", "TC-001", 2401, "PROMPT-036")

        self.assertEqual(aar.contract_type, "AAR")
        self.assertEqual(aar.machine_payload["assessment_status"], "risk_interaction_analytical_assessment")
        self.assertEqual(aar.machine_payload["risk_readiness_report"]["report_id"], "RRR-001")
        self.assertEqual(aar.machine_payload["decision_model_challenge_report"]["challenge_id"], "DMCR-001")
        self.assertIsNotNone(risk_interaction.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-2401"))

    def test_risk_interaction_aar_preserves_boundaries_and_decision_model(self) -> None:
        risk_interaction = office()
        model = decision_model()
        model_before = json.dumps(model, sort_keys=True, separators=(",", ":"))
        source = source_report()
        source_before = source.to_json()

        aar = risk_interaction.generate_risk_interaction_aar(observation(), model, (source,), "CF-001", "TC-001", 2402, "PROMPT-036")

        self.assertEqual(json.dumps(model, sort_keys=True, separators=(",", ":")), model_before)
        self.assertEqual(source.to_json(), source_before)
        self.assertFalse(aar.machine_payload["decision_model_modified"])
        self.assertFalse(aar.machine_payload["risk_office_override"])
        self.assertFalse(aar.machine_payload["seeker_intelligence_modified"])
        self.assertNotIn("trade_recommendation", aar.machine_payload)
        self.assertNotIn("execution_instruction", aar.machine_payload)
        self.assertNotIn("command_decision", aar.machine_payload)

    def test_courier_routing_generates_audit_events(self) -> None:
        risk_interaction = office()
        aar = risk_interaction.generate_risk_interaction_aar(observation(), decision_model(), (source_report(),), "CF-001", "TC-001", 2403, "PROMPT-036")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = risk_interaction.route_aar(aar, executive_inbox)
        event_types = [event.event_type for event in risk_interaction.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-2403"), aar)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        risk_interaction = office()
        aar = risk_interaction.generate_risk_interaction_aar(observation(), decision_model(), (source_report(),), "CF-001", "TC-001", 2404, "PROMPT-036")
        risk_interaction.route_aar(aar, IncomingMailbox("STF-002", "DEP-002"))

        panel = risk_interaction.instrument_panel()

        self.assertEqual(panel.office_id, "ANALYST-OFFICE-007")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")


if __name__ == "__main__":
    unittest.main()
