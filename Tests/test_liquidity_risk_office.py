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
from argos.risk import LiquidityObservation, LiquidityRiskOffice, LiquidityRiskOfficeChief  # noqa: E402


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
            prompt_id="PROMPT-043",
            title="Liquidity Risk Report Prompt",
            owner_group_id="DEP-005",
            author_staff_id="STF-043",
            purpose="Generate deterministic liquidity risk reports.",
            allowed_environments=("development",),
            input_contract_types=("OBS", "RAR"),
            output_contract_types=("RAR",),
            dependencies=("EO-043",),
            safety_notes="No investment recommendation, execution, Organizational Belief State modification, Command Decision, or ignored historical liquidity events.",
        ),
        "1.0.0",
        "Create deterministic Liquidity Risk Report only.",
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


def observation() -> LiquidityObservation:
    return LiquidityObservation(
        asset="ARGOS_TEST",
        order_size=120000,
        average_daily_volume=800000,
        bid_ask_spread_bps=18,
        top_of_book_depth=60000,
        order_book_depth=180000,
        execution_window_minutes=45,
        volatility_score=0.7,
        market_participation_limit=0.12,
        historical_liquidity_events=("flash_crash", "meme_squeeze"),
    )


def office() -> LiquidityRiskOffice:
    return LiquidityRiskOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class LiquidityRiskOfficeTests(unittest.TestCase):
    def test_liquidity_analysis_and_slippage_are_deterministic(self) -> None:
        review = LiquidityRiskOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(review["market_depth"], {"depth_coverage": 0.5, "depth_state": "depth_insufficient"})
        self.assertEqual(review["slippage"], {"estimated_slippage_bps": 58.5})
        self.assertEqual(review["market_impact"], {"market_impact_bps": 44.7})
        self.assertEqual(review["liquidity_risk_model"]["liquidity_risk_score"], 0.3949)

    def test_execution_feasibility_report_is_generated(self) -> None:
        review = LiquidityRiskOfficeChief().evaluate(belief_state(), observation())
        feasibility = review["execution_feasibility_report"]

        self.assertEqual(feasibility["report_id"], "EFR-001")
        self.assertTrue(feasibility["feasible"])
        self.assertEqual(feasibility["feasibility_state"], "execution_feasible")
        self.assertEqual(feasibility["required_execution_slices"], 2)
        self.assertEqual(feasibility["estimated_minutes_required"], 90)

    def test_liquidity_stress_and_historical_replay_are_deterministic(self) -> None:
        review = LiquidityRiskOfficeChief().evaluate(belief_state(), observation())
        stress = review["liquidity_stress_report"]

        self.assertEqual(stress["report_id"], "LSR-001")
        self.assertEqual(len(stress["stress_tests"]), 4)
        self.assertEqual(stress["stress_tests"][0], {"scenario": "Market Depth Halves", "stressed_slippage_bps": 78.975})
        self.assertEqual(stress["stress_tests"][3], {"scenario": "Historical Liquidity Replay", "stressed_slippage_bps": 82.5})
        self.assertEqual(stress["historical_replay_events"], ("flash_crash", "meme_squeeze"))

    def test_liquidity_readiness_score_is_reproducible(self) -> None:
        review = LiquidityRiskOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(review["liquidity_readiness_score"], {"score": 66.36, "category": "Conditionally Approved"})
        self.assertEqual(review["liquidity_risk_model"]["exit_feasibility"], "exit_requires_staging")

    def test_liquidity_risk_report_contains_required_fields_and_boundaries(self) -> None:
        liquidity = office()

        report = liquidity.generate_liquidity_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3101, "PROMPT-043")

        self.assertEqual(report.contract_type, "RAR")
        self.assertEqual(report.machine_payload["risk_id"], "LIQ-003101")
        self.assertEqual(report.machine_payload["asset"], "ARGOS_TEST")
        self.assertEqual(report.machine_payload["execution_feasibility_report"]["report_id"], "EFR-001")
        self.assertEqual(report.machine_payload["liquidity_stress_report"]["report_id"], "LSR-001")
        self.assertEqual(report.machine_payload["liquidity_readiness_score"]["category"], "Conditionally Approved")
        self.assertFalse(report.machine_payload["organizational_belief_state_modified"])
        self.assertFalse(report.machine_payload["historical_liquidity_events_ignored"])
        self.assertIsNone(report.machine_payload["investment_recommendation"])
        self.assertIsNone(report.machine_payload["execution_instruction"])
        self.assertIsNone(report.machine_payload["command_decision"])
        self.assertIsNotNone(liquidity.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-3101"))

    def test_liquidity_risk_requires_organizational_belief_state(self) -> None:
        with self.assertRaises(TypeError):
            LiquidityRiskOfficeChief().evaluate({"state_id": "OBS-001"}, observation())

    def test_courier_routing_generates_audit_events(self) -> None:
        liquidity = office()
        report = liquidity.generate_liquidity_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3102, "PROMPT-043")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = liquidity.route_report(report, executive_inbox)
        event_types = [event.event_type for event in liquidity.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-3102"), report)
        self.assertIn(AuditEventType.DOCUMENT_CREATED, event_types)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_displays_liquidity_review_values(self) -> None:
        liquidity = office()
        report = liquidity.generate_liquidity_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3103, "PROMPT-043")
        liquidity.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        panel = liquidity.instrument_panel()

        self.assertEqual(panel.base_panel.office_id, "RISK-OFFICE-003")
        self.assertEqual(panel.base_panel.metrics.reports_generated, 1)
        self.assertEqual(panel.base_panel.metrics.routed_reports, 1)
        self.assertEqual(panel.estimated_slippage_bps, 58.5)
        self.assertEqual(panel.market_impact_bps, 44.7)
        self.assertEqual(panel.stress_tests, 4)
        self.assertEqual(panel.historical_events, 2)


if __name__ == "__main__":
    unittest.main()
