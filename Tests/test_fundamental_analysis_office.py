from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    FundamentalAnalysisOffice,
    FundamentalAnalysisOfficeChief,
    FundamentalBusinessObservation,
    ValuationAnalyst,
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
            prompt_id="PROMPT-032",
            title="Fundamental Analyst AAR Prompt",
            owner_group_id="DEP-004",
            author_staff_id="STF-033",
            purpose="Generate deterministic Fundamental Analytical Assessment Reports.",
            allowed_environments=("development",),
            input_contract_types=("SEEKER_FUNDAMENTAL_REPORT",),
            output_contract_types=("AAR",),
            dependencies=("EO-032",),
            safety_notes="No trade recommendation, execution, command decision, source modification, or contradiction suppression.",
        ),
        "1.0.0",
        "Create deterministic fundamental assessment only.",
    )
    return repository


def quality_observation() -> FundamentalBusinessObservation:
    return FundamentalBusinessObservation(
        revenue_growth=0.18,
        gross_margin=0.55,
        operating_margin=0.22,
        return_on_invested_capital=0.24,
        valuation_multiple=18,
        industry_average_multiple=24,
        reinvestment_rate=0.35,
        management_quality_score=0.82,
        accrual_ratio=0.04,
        debt_to_equity=0.4,
        interest_coverage=9,
        free_cash_flow_margin=0.18,
        industry_concentration_score=0.7,
        moat_durability_score=0.75,
    )


def contradictory_observation() -> FundamentalBusinessObservation:
    return FundamentalBusinessObservation(
        revenue_growth=0.05,
        gross_margin=0.28,
        operating_margin=0.04,
        return_on_invested_capital=0.08,
        valuation_multiple=35,
        industry_average_multiple=20,
        reinvestment_rate=0.2,
        management_quality_score=0.5,
        accrual_ratio=0.22,
        debt_to_equity=1.8,
        interest_coverage=2,
        free_cash_flow_margin=0.03,
        industry_concentration_score=0.25,
        moat_durability_score=0.2,
    )


def source_report() -> OperationalContract:
    created = utc_timestamp()
    payload = {"office_id": "SEEKER-OFFICE-002", "report_status": "fundamental_candidate_unanalysed"}
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id="DOC-401",
        contract_type="COR",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id="STF-022",
        produced_by_group_id="DEP-003",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic fundamental Seeker source.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def office() -> FundamentalAnalysisOffice:
    return FundamentalAnalysisOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class FundamentalAnalysisOfficeTests(unittest.TestCase):
    def test_business_analysis_and_quality_scoring_are_deterministic(self) -> None:
        reasoning = FundamentalAnalysisOfficeChief().analyze(quality_observation())

        self.assertEqual(reasoning["financial_statement"]["statement_quality"], "strong")
        self.assertEqual(reasoning["business_quality_score"], {"score": 1.0, "grade": "high"})
        self.assertEqual(reasoning["fundamental_conclusion"]["business_conclusion"], "business_quality_confirmed")

    def test_valuation_and_economic_moat_evaluation(self) -> None:
        valuation = ValuationAnalyst().analyze(quality_observation())
        reasoning = FundamentalAnalysisOfficeChief().analyze(quality_observation())

        self.assertEqual(valuation, {"valuation_state": "discount", "relative_multiple": 0.75})
        self.assertEqual(reasoning["economic_moat"], {"moat_state": "durable_moat"})

    def test_reasoning_graph_generation_preserves_contradictory_evidence(self) -> None:
        chief = FundamentalAnalysisOfficeChief()
        reasoning = chief.analyze(contradictory_observation())

        graphs = chief.reasoning_graphs(reasoning, ("DOC-401",))
        alternatives = chief.alternative_explanations(reasoning)

        self.assertEqual(len(graphs), 1)
        self.assertEqual(graphs[0].conclusion_id, "FUND-CONCLUSION-001")
        self.assertIn("valuation", graphs[0].contradictory_evidence)
        self.assertIn("offset", alternatives[0])

    def test_fundamental_aar_generation_persists_reasoning_payload(self) -> None:
        fundamental = office()

        aar = fundamental.generate_fundamental_aar(quality_observation(), (source_report(),), "CF-001", "TC-001", 2001, "PROMPT-032")

        self.assertEqual(aar.contract_type, "AAR")
        self.assertEqual(aar.machine_payload["assessment_status"], "fundamental_analytical_assessment")
        self.assertIn("fundamental_reasoning", aar.machine_payload)
        self.assertIn("fundamental_reasoning_graphs", aar.machine_payload)
        self.assertEqual(aar.machine_payload["business_quality_score"]["grade"], "high")
        self.assertIsNotNone(fundamental.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-2001"))

    def test_fundamental_aar_preserves_boundaries_and_source_intelligence(self) -> None:
        fundamental = office()
        source = source_report()
        before = source.to_json()

        aar = fundamental.generate_fundamental_aar(quality_observation(), (source,), "CF-001", "TC-001", 2002, "PROMPT-032")

        self.assertEqual(source.to_json(), before)
        self.assertFalse(aar.machine_payload["seeker_intelligence_modified"])
        self.assertFalse(aar.machine_payload["risk_office_override"])
        self.assertNotIn("trade_recommendation", aar.machine_payload)
        self.assertNotIn("execution_instruction", aar.machine_payload)
        self.assertNotIn("command_decision", aar.machine_payload)

    def test_courier_routing_generates_audit_events(self) -> None:
        fundamental = office()
        aar = fundamental.generate_fundamental_aar(quality_observation(), (source_report(),), "CF-001", "TC-001", 2003, "PROMPT-032")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = fundamental.route_aar(aar, executive_inbox)
        event_types = [event.event_type for event in fundamental.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-2003"), aar)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        fundamental = office()
        aar = fundamental.generate_fundamental_aar(quality_observation(), (source_report(),), "CF-001", "TC-001", 2004, "PROMPT-032")
        fundamental.route_aar(aar, IncomingMailbox("STF-002", "DEP-002"))

        panel = fundamental.instrument_panel()

        self.assertEqual(panel.office_id, "ANALYST-OFFICE-003")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")


if __name__ == "__main__":
    unittest.main()
