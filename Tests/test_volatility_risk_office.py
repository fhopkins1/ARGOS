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
from argos.risk import VolatilityMarketData, VolatilityRiskOffice, VolatilityRiskOfficeChief  # noqa: E402


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
            prompt_id="PROMPT-045",
            title="Volatility Risk Report Prompt",
            owner_group_id="DEP-005",
            author_staff_id="STF-045",
            purpose="Generate deterministic volatility risk reports.",
            allowed_environments=("development",),
            input_contract_types=("OBS", "MARKET_DATA"),
            output_contract_types=("RAR",),
            dependencies=("EO-045",),
            safety_notes="No opaque reasoning, investment recommendation, execution, Organizational Belief State modification, or Command Decision.",
        ),
        "1.0.0",
        "Create deterministic Volatility Risk Report only.",
    )
    return repository


def belief_state() -> OrganizationalBeliefState:
    return OrganizationalBeliefState(
        "OBS-001",
        "risk_elevated",
        0.56,
        0.75,
        0.75,
        ("DOC-2601", "DOC-2602"),
    )


def market_data() -> VolatilityMarketData:
    return VolatilityMarketData(
        "MKT-001",
        "ARGOS_TEST",
        (0.01, -0.012, 0.018, -0.02, 0.015, 0.06),
        0.48,
        (0.22, 0.25, 0.28, 0.31, 0.35),
        {"SPY": 0.41, "QQQ": 0.46, "TLT": 0.18},
        100000,
    )


def office() -> VolatilityRiskOffice:
    return VolatilityRiskOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class VolatilityRiskOfficeTests(unittest.TestCase):
    def test_realized_and_implied_volatility_are_deterministic(self) -> None:
        review = VolatilityRiskOfficeChief().evaluate(belief_state(), market_data(), "normal_volatility")

        self.assertEqual(review["volatility_risk_model"]["realized_volatility"], 0.4463)
        self.assertEqual(review["implied_volatility_analysis"]["implied_volatility"], 0.48)
        self.assertEqual(review["implied_volatility_analysis"]["premium"], 0.0337)
        self.assertEqual(review["implied_volatility_analysis"]["state"], "implied_volatility_elevated")

    def test_regime_transition_forecast_and_shock_detection_are_recorded(self) -> None:
        review = VolatilityRiskOfficeChief().evaluate(belief_state(), market_data(), "normal_volatility")

        self.assertEqual(review["volatility_regime_record"], {"record_id": "VRR-001", "previous_regime": "normal_volatility", "current_regime": "crisis_volatility", "transition_recorded": True})
        self.assertEqual(review["volatility_forecast"]["forecast_volatility"], 0.4988)
        self.assertFalse(review["volatility_event_report"]["shock_detected"])
        self.assertEqual(review["volatility_event_report"]["shock_magnitude"], 0.8537)

    def test_contagion_adjustment_and_archives_are_generated(self) -> None:
        review = VolatilityRiskOfficeChief().evaluate(belief_state(), market_data(), "normal_volatility")

        self.assertEqual(review["volatility_event_report"]["contagion_score"], 0.6667)
        self.assertEqual(review["volatility_event_report"]["affected_markets"], ("QQQ", "SPY"))
        self.assertEqual(review["position_adjustment_recommendation"]["action"], "reduce_risk_limit_moderately")
        self.assertEqual(review["position_adjustment_recommendation"]["adjusted_position_limit"], 56738.0)
        self.assertEqual(review["confidence_adjustment_record"], {"record_id": "CAR-001", "prior_confidence": 0.56, "adjusted_confidence": 0.4668, "adjustment": -0.0932})
        self.assertEqual(review["historical_volatility_archive"]["archive_id"], "HVA-001")
        self.assertEqual(review["implied_volatility_archive"]["archive_id"], "IVA-001")
        self.assertEqual(review["volatility_event_archive"]["archive_id"], "VEA-001")

    def test_volatility_report_contains_required_artifacts_and_boundaries(self) -> None:
        volatility = office()

        report = volatility.generate_volatility_risk_report(belief_state(), market_data(), "normal_volatility", "CF-001", "TC-001", 3201, "PROMPT-045")

        self.assertEqual(report.contract_type, "RAR")
        self.assertEqual(report.machine_payload["risk_id"], "VOL-003201")
        self.assertEqual(report.machine_payload["volatility_risk_report"]["volatility_regime"], "crisis_volatility")
        self.assertEqual(report.machine_payload["volatility_event_report"]["event_id"], "VER-001")
        self.assertEqual(report.machine_payload["organizational_volatility_summary"]["organizational_confidence_surface"], 0.4668)
        self.assertEqual(report.machine_payload["position_adjustment_recommendation"]["recommendation_id"], "PAR-001")
        self.assertFalse(report.machine_payload["organizational_belief_state_modified"])
        self.assertFalse(report.machine_payload["opaque_reasoning_used"])
        self.assertIsNone(report.machine_payload["investment_recommendation"])
        self.assertIsNone(report.machine_payload["execution_instruction"])
        self.assertIsNone(report.machine_payload["command_decision"])
        self.assertIsNotNone(volatility.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-3201"))

    def test_volatility_risk_requires_organizational_belief_state(self) -> None:
        with self.assertRaises(TypeError):
            VolatilityRiskOfficeChief().evaluate({"state_id": "OBS-001"}, market_data(), "normal_volatility")

    def test_courier_routing_generates_audit_events(self) -> None:
        volatility = office()
        report = volatility.generate_volatility_risk_report(belief_state(), market_data(), "normal_volatility", "CF-001", "TC-001", 3202, "PROMPT-045")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = volatility.route_report(report, executive_inbox)
        event_types = [event.event_type for event in volatility.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-3202"), report)
        self.assertIn(AuditEventType.DOCUMENT_CREATED, event_types)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_displays_volatility_values(self) -> None:
        volatility = office()
        report = volatility.generate_volatility_risk_report(belief_state(), market_data(), "normal_volatility", "CF-001", "TC-001", 3203, "PROMPT-045")
        volatility.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        panel = volatility.instrument_panel()

        self.assertEqual(panel.base_panel.office_id, "RISK-OFFICE-005")
        self.assertEqual(panel.base_panel.metrics.reports_generated, 1)
        self.assertEqual(panel.base_panel.metrics.routed_reports, 1)
        self.assertEqual(panel.realized_volatility, 0.4463)
        self.assertEqual(panel.implied_volatility, 0.48)
        self.assertEqual(panel.forecast_volatility, 0.4988)
        self.assertEqual(panel.regime, "crisis_volatility")
        self.assertEqual(panel.archived_events, 1)


if __name__ == "__main__":
    unittest.main()
