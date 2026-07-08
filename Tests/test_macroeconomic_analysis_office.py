from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    MacroeconomicAnalysisOffice,
    MacroeconomicAnalysisOfficeChief,
    MacroeconomicReasoningObservation,
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
            prompt_id="PROMPT-033",
            title="Macroeconomic Analyst AAR Prompt",
            owner_group_id="DEP-004",
            author_staff_id="STF-034",
            purpose="Generate deterministic Macroeconomic Analytical Assessment Reports.",
            allowed_environments=("development",),
            input_contract_types=("SEEKER_MACRO_REPORT",),
            output_contract_types=("AAR",),
            dependencies=("EO-033",),
            safety_notes="No trade recommendation, execution, command decision, source modification, or hypothesis suppression.",
        ),
        "1.0.0",
        "Create deterministic macroeconomic assessment only.",
    )
    return repository


def observation() -> MacroeconomicReasoningObservation:
    return MacroeconomicReasoningObservation(
        inflation_rate=5.2,
        policy_rate=5.5,
        fiscal_impulse=0.3,
        unemployment_rate=4.0,
        gdp_growth=2.1,
        yield_curve_spread=-0.4,
        currency_change=1.2,
        commodity_change=12.0,
        global_growth=1.4,
    )


def source_report() -> OperationalContract:
    created = utc_timestamp()
    payload = {"office_id": "SEEKER-OFFICE-003", "report_status": "macro_threat_identified"}
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id="DOC-501",
        contract_type="MTR",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id="STF-023",
        produced_by_group_id="DEP-003",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic macro Seeker source.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def office() -> MacroeconomicAnalysisOffice:
    return MacroeconomicAnalysisOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class MacroeconomicAnalysisOfficeTests(unittest.TestCase):
    def test_economic_regime_analysis_is_reproducible(self) -> None:
        reasoning = MacroeconomicAnalysisOfficeChief().analyze(observation())

        self.assertEqual(reasoning["inflation"]["inflation_state"], "elevated")
        self.assertEqual(reasoning["monetary_policy"]["monetary_policy"], "restrictive")
        self.assertEqual(reasoning["economic_regime"], {"regime": "inflationary_tightening"})

    def test_competing_thesis_generation_preserves_multiple_hypotheses(self) -> None:
        reasoning = MacroeconomicAnalysisOfficeChief().analyze(observation())
        theses = reasoning["competing_theses"]

        self.assertEqual(len(theses), 3)
        self.assertEqual(theses[0]["thesis_id"], "CTA-001")
        self.assertEqual(theses[1]["name"], "soft_landing")
        self.assertEqual(theses[2]["name"], "policy_error")

    def test_reasoning_graph_generation_references_competing_theses(self) -> None:
        chief = MacroeconomicAnalysisOfficeChief()
        reasoning = chief.analyze(observation())

        graphs = chief.reasoning_graphs(reasoning, ("DOC-501",))

        self.assertEqual(len(graphs), 1)
        self.assertEqual(graphs[0].conclusion_id, "MACRO-CONCLUSION-001")
        self.assertEqual(graphs[0].competing_hypotheses, ("CTA-001", "CTA-002", "CTA-003"))

    def test_confidence_calibration_is_deterministic(self) -> None:
        reasoning = MacroeconomicAnalysisOfficeChief().analyze(observation())

        self.assertEqual(reasoning["confidence_calibration"], {"confidence": 0.45, "method": "risk_flag_penalty"})

    def test_macroeconomic_aar_generation_persists_reasoning_payload(self) -> None:
        macro = office()

        aar = macro.generate_macroeconomic_aar(observation(), (source_report(),), "CF-001", "TC-001", 2101, "PROMPT-033")

        self.assertEqual(aar.contract_type, "AAR")
        self.assertEqual(aar.machine_payload["assessment_status"], "macroeconomic_analytical_assessment")
        self.assertEqual(aar.machine_payload["economic_regime"], {"regime": "inflationary_tightening"})
        self.assertEqual(len(aar.machine_payload["competing_thesis_analysis"]), 3)
        self.assertIsNotNone(macro.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-2101"))

    def test_macroeconomic_aar_preserves_boundaries_and_source_intelligence(self) -> None:
        macro = office()
        source = source_report()
        before = source.to_json()

        aar = macro.generate_macroeconomic_aar(observation(), (source,), "CF-001", "TC-001", 2102, "PROMPT-033")

        self.assertEqual(source.to_json(), before)
        self.assertFalse(aar.machine_payload["seeker_intelligence_modified"])
        self.assertFalse(aar.machine_payload["risk_office_override"])
        self.assertNotIn("trade_recommendation", aar.machine_payload)
        self.assertNotIn("execution_instruction", aar.machine_payload)
        self.assertNotIn("command_decision", aar.machine_payload)

    def test_courier_routing_generates_audit_events(self) -> None:
        macro = office()
        aar = macro.generate_macroeconomic_aar(observation(), (source_report(),), "CF-001", "TC-001", 2103, "PROMPT-033")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = macro.route_aar(aar, executive_inbox)
        event_types = [event.event_type for event in macro.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-2103"), aar)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        macro = office()
        aar = macro.generate_macroeconomic_aar(observation(), (source_report(),), "CF-001", "TC-001", 2104, "PROMPT-033")
        macro.route_aar(aar, IncomingMailbox("STF-002", "DEP-002"))

        panel = macro.instrument_panel()

        self.assertEqual(panel.office_id, "ANALYST-OFFICE-004")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")


if __name__ == "__main__":
    unittest.main()
