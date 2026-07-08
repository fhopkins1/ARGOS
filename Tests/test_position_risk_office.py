from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import OrganizationalBeliefState  # noqa: E402
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402
from argos.risk import PositionRiskOffice, PositionRiskOfficeChief, ProposedPosition  # noqa: E402


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
            prompt_id="PROMPT-041",
            title="Position Risk Report Prompt",
            owner_group_id="DEP-005",
            author_staff_id="STF-041",
            purpose="Generate deterministic single-position risk reports.",
            allowed_environments=("development",),
            input_contract_types=("OBS",),
            output_contract_types=("RAR",),
            dependencies=("EO-041",),
            safety_notes="No investment recommendation, portfolio interaction, execution, Command Decision, or Executive override.",
        ),
        "1.0.0",
        "Create deterministic Position Risk Report only.",
    )
    return repository


def belief_state() -> OrganizationalBeliefState:
    return OrganizationalBeliefState(
        "OBS-001",
        "risk_elevated",
        0.56,
        0.75,
        0.75,
        ("DOC-2601", "DOC-2602", "DOC-2603"),
    )


def proposed_position() -> ProposedPosition:
    return ProposedPosition(
        asset="ARGOS_TEST",
        position_size=100,
        entry_price=50,
        stop_loss_price=45,
        expected_success_gain_pct=0.2,
        liquidity_score=0.45,
        volatility_score=0.7,
        sensitivity_score=0.65,
        gap_down_loss_pct=0.28,
        gap_up_loss_pct=0.12,
        interest_rate_shock_loss_pct=0.08,
        regulatory_event_loss_pct=0.35,
        unexpected_earnings_loss_pct=0.22,
        geopolitical_event_loss_pct=0.18,
        execution_failure_loss_pct=0.11,
        historical_adversary_loss_pct=0.3,
        recovery_score=0.5,
        thesis_invalidation_evidence=("revenue_miss", "regulatory_action"),
    )


def office() -> PositionRiskOffice:
    return PositionRiskOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class PositionRiskOfficeTests(unittest.TestCase):
    def test_position_risk_model_is_deterministic(self) -> None:
        review = PositionRiskOfficeChief().evaluate(belief_state(), proposed_position())
        model = review["position_risk_model"]

        self.assertEqual(model["maximum_expected_loss"], 1750.0)
        self.assertEqual(model["expected_drawdown"], 1268.75)
        self.assertEqual(model["probability_of_failure"], 0.5895)
        self.assertEqual(model["probability_of_success"], 0.4105)
        self.assertEqual(model["recommended_position_limit"], 1932.5)
        self.assertEqual(model["confidence"], 0.5615)
        self.assertEqual(model["organizational_confidence_surface_contribution"], 0.3144)

    def test_stress_tests_cover_required_scenarios(self) -> None:
        review = PositionRiskOfficeChief().evaluate(belief_state(), proposed_position())
        stress_tests = review["stress_test_results"]

        self.assertEqual(len(stress_tests), 11)
        self.assertEqual(stress_tests[0]["scenario"], "Market Crash")
        self.assertEqual(stress_tests[4], {"scenario": "Liquidity Collapse", "loss_pct": 0.275, "loss_amount": 1375.0, "severity": "severe"})
        self.assertEqual(stress_tests[6], {"scenario": "Regulatory Event", "loss_pct": 0.35, "loss_amount": 1750.0, "severity": "catastrophic"})

    def test_readiness_score_and_failure_modes_are_documented(self) -> None:
        review = PositionRiskOfficeChief().evaluate(belief_state(), proposed_position())

        self.assertEqual(review["position_readiness_score"], {"score": 52.72, "category": "Needs Additional Analysis"})
        self.assertIn("catastrophic_stress_loss", review["failure_modes"])
        self.assertIn("liquidity_disappears", review["failure_modes"])
        self.assertIn("thesis_invalidation", review["failure_modes"])
        self.assertIn("What prevents the catastrophic stress path from becoming the base case?", review["recommended_commander_questions"])

    def test_position_risk_report_contains_required_fields_and_boundaries(self) -> None:
        position_risk = office()

        report = position_risk.generate_position_risk_report(belief_state(), proposed_position(), "CF-001", "TC-001", 2901, "PROMPT-041")

        self.assertEqual(report.contract_type, "RAR")
        self.assertEqual(report.machine_payload["risk_id"], "PR-002901")
        self.assertEqual(report.machine_payload["asset"], "ARGOS_TEST")
        self.assertEqual(report.machine_payload["position_size"], 100)
        self.assertEqual(report.machine_payload["maximum_loss"], 1750.0)
        self.assertEqual(report.machine_payload["expected_loss"], 1268.75)
        self.assertEqual(len(report.machine_payload["stress_test_results"]), 11)
        self.assertEqual(report.machine_payload["position_readiness_score"]["category"], "Needs Additional Analysis")
        self.assertFalse(report.machine_payload["organizational_belief_state_modified"])
        self.assertFalse(report.machine_payload["portfolio_interactions_evaluated"])
        self.assertIsNone(report.machine_payload["investment_recommendation"])
        self.assertIsNone(report.machine_payload["execution_instruction"])
        self.assertIsNone(report.machine_payload["command_decision"])
        self.assertIsNotNone(position_risk.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-2901"))

    def test_position_risk_requires_organizational_belief_state(self) -> None:
        with self.assertRaises(TypeError):
            PositionRiskOfficeChief().evaluate({"state_id": "OBS-001"}, proposed_position())

    def test_courier_routing_generates_audit_events(self) -> None:
        position_risk = office()
        report = position_risk.generate_position_risk_report(belief_state(), proposed_position(), "CF-001", "TC-001", 2902, "PROMPT-041")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = position_risk.route_report(report, executive_inbox)
        event_types = [event.event_type for event in position_risk.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-2902"), report)
        self.assertIn(AuditEventType.DOCUMENT_CREATED, event_types)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_displays_position_review_values(self) -> None:
        position_risk = office()
        report = position_risk.generate_position_risk_report(belief_state(), proposed_position(), "CF-001", "TC-001", 2903, "PROMPT-041")
        position_risk.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        panel = position_risk.instrument_panel()

        self.assertEqual(panel.base_panel.office_id, "RISK-OFFICE-001")
        self.assertEqual(panel.base_panel.metrics.reports_generated, 1)
        self.assertEqual(panel.base_panel.metrics.routed_reports, 1)
        self.assertEqual(panel.maximum_exposure, 5000.0)
        self.assertEqual(panel.expected_drawdown, 1268.75)
        self.assertEqual(panel.stress_tests, 11)
        self.assertEqual(panel.failure_modes, 4)


if __name__ == "__main__":
    unittest.main()
