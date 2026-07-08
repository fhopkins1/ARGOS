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
from argos.risk import PortfolioPosition, PortfolioRiskObservation, PortfolioRiskOffice, PortfolioRiskOfficeChief  # noqa: E402


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
            prompt_id="PROMPT-042",
            title="Portfolio Risk Report Prompt",
            owner_group_id="DEP-005",
            author_staff_id="STF-042",
            purpose="Generate deterministic portfolio-level risk reports.",
            allowed_environments=("development",),
            input_contract_types=("OBS", "RAR"),
            output_contract_types=("RAR",),
            dependencies=("EO-042",),
            safety_notes="No investment recommendation, execution, Organizational Belief State modification, Command Decision, or deterministic interface override.",
        ),
        "1.0.0",
        "Create deterministic Portfolio Risk Report only.",
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


def observation() -> PortfolioRiskObservation:
    return PortfolioRiskObservation(
        "PORT-001",
        (
            PortfolioPosition("ALPHA", 5000, "technology", "US", "growth", 0.6, 0.7, 0.58, (0.01, 0.02, -0.01, 0.03)),
            PortfolioPosition("BETA", 3000, "technology", "US", "growth", 0.55, 0.65, 0.54, (0.012, 0.018, -0.008, 0.026)),
            PortfolioPosition("GAMMA", 2000, "energy", "EU", "inflation", 0.5, 0.5, 0.62, (-0.01, 0.0, 0.015, -0.005)),
        ),
    )


def office() -> PortfolioRiskOffice:
    return PortfolioRiskOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class PortfolioRiskOfficeTests(unittest.TestCase):
    def test_correlation_matrix_generation_is_deterministic(self) -> None:
        review = PortfolioRiskOfficeChief().evaluate(belief_state(), observation())
        matrix = review["correlation_matrix"]

        self.assertEqual(matrix["assets"], ("ALPHA", "BETA", "GAMMA"))
        self.assertEqual(matrix["matrix"][0][0], 1.0)
        self.assertGreater(matrix["matrix"][0][1], 0.99)
        self.assertEqual(matrix["average_correlation"], 0.8349)

    def test_stress_testing_and_historical_adversaries_execute(self) -> None:
        review = PortfolioRiskOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(len(review["historical_adversary_library"]), 3)
        self.assertEqual(review["historical_adversary_library"][0]["adversary_id"], "HAL-2008")
        self.assertEqual(len(review["portfolio_stress_tests"]), 6)
        self.assertEqual(review["portfolio_stress_tests"][0], {"scenario": "Market Crash", "loss_amount": 2200.0, "loss_pct": 0.22, "affected_assets": ("ALPHA", "BETA", "GAMMA")})
        self.assertEqual(review["portfolio_stress_tests"][3]["scenario"], "Credit Crisis")

    def test_failure_cascade_and_diversification_are_documented(self) -> None:
        review = PortfolioRiskOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(len(review["failure_cascades"]), 1)
        self.assertEqual(review["failure_cascades"][0]["trigger_asset"], "ALPHA")
        self.assertEqual(review["failure_cascades"][0]["affected_asset"], "BETA")
        self.assertEqual(review["diversification"]["sector_count"], 2)
        self.assertEqual(review["diversification"]["geography_count"], 2)
        self.assertEqual(review["diversification"]["diversification_score"], 0.5162)

    def test_portfolio_readiness_and_confidence_surface_are_deterministic(self) -> None:
        review = PortfolioRiskOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(review["portfolio_risk_model"]["total_exposure"], 10000)
        self.assertEqual(review["portfolio_risk_model"]["concentration_score"], 0.5)
        self.assertEqual(review["portfolio_risk_model"]["systemic_risk_score"], 0.6299)
        self.assertEqual(review["portfolio_readiness_score"], {"score": 64.97, "category": "Needs Additional Analysis"})
        self.assertEqual(review["organizational_confidence_surface"], 0.5396)

    def test_portfolio_risk_report_contains_required_fields_and_boundaries(self) -> None:
        portfolio = office()

        report = portfolio.generate_portfolio_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3001, "PROMPT-042")

        self.assertEqual(report.contract_type, "RAR")
        self.assertEqual(report.machine_payload["risk_id"], "POR-003001")
        self.assertEqual(report.machine_payload["portfolio_id"], "PORT-001")
        self.assertEqual(report.machine_payload["correlation_matrix"]["average_correlation"], 0.8349)
        self.assertEqual(report.machine_payload["portfolio_readiness_score"]["category"], "Needs Additional Analysis")
        self.assertFalse(report.machine_payload["organizational_belief_state_modified"])
        self.assertIsNone(report.machine_payload["investment_recommendation"])
        self.assertIsNone(report.machine_payload["execution_instruction"])
        self.assertIsNone(report.machine_payload["command_decision"])
        self.assertIsNotNone(portfolio.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-3001"))

    def test_portfolio_risk_requires_organizational_belief_state(self) -> None:
        with self.assertRaises(TypeError):
            PortfolioRiskOfficeChief().evaluate({"state_id": "OBS-001"}, observation())

    def test_courier_routing_generates_audit_events(self) -> None:
        portfolio = office()
        report = portfolio.generate_portfolio_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3002, "PROMPT-042")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = portfolio.route_report(report, executive_inbox)
        event_types = [event.event_type for event in portfolio.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-3002"), report)
        self.assertIn(AuditEventType.DOCUMENT_CREATED, event_types)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_displays_portfolio_review_values(self) -> None:
        portfolio = office()
        report = portfolio.generate_portfolio_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3003, "PROMPT-042")
        portfolio.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        panel = portfolio.instrument_panel()

        self.assertEqual(panel.base_panel.office_id, "RISK-OFFICE-002")
        self.assertEqual(panel.base_panel.metrics.reports_generated, 1)
        self.assertEqual(panel.base_panel.metrics.routed_reports, 1)
        self.assertEqual(panel.total_exposure, 10000)
        self.assertEqual(panel.maximum_position_exposure, 5000)
        self.assertEqual(panel.average_correlation, 0.8349)
        self.assertEqual(panel.stress_tests, 6)
        self.assertEqual(panel.failure_cascades, 1)


if __name__ == "__main__":
    unittest.main()
