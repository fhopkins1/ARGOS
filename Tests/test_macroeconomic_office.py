from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402
from argos.seeker import MacroeconomicObservation, MacroeconomicOffice, MacroeconomicScreener  # noqa: E402


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
            prompt_id="PROMPT-021",
            title="Macroeconomic Report Prompt",
            owner_group_id="DEP-003",
            author_staff_id="STF-023",
            purpose="Generate deterministic macroeconomic reports.",
            allowed_environments=("development",),
            input_contract_types=("MACROECONOMIC_OBSERVATION",),
            output_contract_types=("COR", "MTR", "IGR"),
            dependencies=("EO-021",),
            safety_notes="No trade recommendations, sizing, execution, or company valuation.",
        ),
        "1.0.0",
        "Create descriptive macroeconomic reports only.",
    )
    return repository


def mixed_observation() -> MacroeconomicObservation:
    return MacroeconomicObservation(
        inflation_rate=5.2,
        policy_rate=5.5,
        unemployment_rate=4.1,
        gdp_growth=2.3,
        monetary_policy_bias="tightening",
        fiscal_policy_bias="supportive",
        currency_change=1.2,
        yield_curve_spread=-0.4,
        commodity_index_change=12.5,
        global_growth=0.8,
    )


def unknown_observation() -> MacroeconomicObservation:
    return MacroeconomicObservation(
        inflation_rate=None,
        policy_rate=4.25,
        unemployment_rate=None,
        gdp_growth=1.1,
        monetary_policy_bias=None,
        fiscal_policy_bias="neutral",
        currency_change=None,
        yield_curve_spread=0.5,
        commodity_index_change=None,
        global_growth=2.2,
    )


def office() -> MacroeconomicOffice:
    return MacroeconomicOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class MacroeconomicOfficeTests(unittest.TestCase):
    def test_economic_data_ingestion_generates_ten_macro_signals(self) -> None:
        signals = MacroeconomicScreener().monitor(mixed_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(len(signals), 10)
        self.assertEqual(by_name["inflation"].signal, "inflation_threat")
        self.assertEqual(by_name["interest_rate"].signal, "restrictive_rates")
        self.assertEqual(by_name["labor_market"].signal, "labor_market_resilient")
        self.assertEqual(by_name["gdp"].signal, "growth_expansion")
        self.assertEqual(by_name["bond_market"].signal, "yield_curve_inversion")

    def test_candidate_opportunity_report_generation_persists_macro_cor(self) -> None:
        macro = office()

        cor = macro.generate_cor(mixed_observation(), "CF-001", "TC-001", 501, "PROMPT-021")

        self.assertEqual(cor.contract_id, "DOC-501")
        self.assertEqual(cor.contract_type, "COR")
        self.assertEqual(cor.machine_payload["report_status"], "macro_candidate_unanalysed")
        self.assertGreater(len(cor.machine_payload["macroeconomic_signals"]), 0)
        self.assertIsNotNone(macro.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-501"))

    def test_threat_generation_persists_macro_threat_report(self) -> None:
        macro = office()

        report = macro.generate_threat_report(mixed_observation(), "CF-001", "TC-001", 502, "PROMPT-021")
        signals = {signal["signal"] for signal in report.machine_payload["macroeconomic_signals"]}

        self.assertEqual(report.contract_type, "MTR")
        self.assertEqual(report.machine_payload["report_status"], "macro_threat_identified")
        self.assertIn("inflation_threat", signals)
        self.assertIn("yield_curve_inversion", signals)

    def test_unknown_detection_generates_information_gap_report(self) -> None:
        macro = office()

        report = macro.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 503, "PROMPT-021")
        signals = {signal["signal"] for signal in report.machine_payload["macroeconomic_signals"]}

        self.assertEqual(report.contract_type, "IGR")
        self.assertEqual(report.machine_payload["report_status"], "macro_information_gap")
        self.assertIn("inflation_unknown", signals)
        self.assertIn("labor_data_unknown", signals)
        self.assertIn("monetary_policy_unknown", signals)

    def test_courier_routing_uses_deterministic_interfaces(self) -> None:
        macro = office()
        report = macro.generate_threat_report(mixed_observation(), "CF-001", "TC-001", 504, "PROMPT-021")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = macro.route_report(report, executive_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-504"), report)
        self.assertEqual(macro.office.routed_reports, 1)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        macro = office()
        cor = macro.generate_cor(mixed_observation(), "CF-001", "TC-001", 505, "PROMPT-021")
        threat = macro.generate_threat_report(mixed_observation(), "CF-001", "TC-001", 506, "PROMPT-021")
        gap = macro.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 507, "PROMPT-021")
        macro.route_report(cor, IncomingMailbox("STF-002", "DEP-002"))
        macro.route_report(threat, IncomingMailbox("STF-002", "DEP-002"))
        macro.route_report(gap, IncomingMailbox("STF-002", "DEP-002"))

        panel = macro.instrument_panel()

        self.assertEqual(panel.office_id, "SEEKER-OFFICE-003")
        self.assertEqual(panel.metrics.reports_generated, 3)
        self.assertEqual(panel.metrics.routed_reports, 3)
        self.assertEqual(panel.health.status, "healthy")

    def test_routing_generates_audit_events_and_payload_avoids_forbidden_fields(self) -> None:
        macro = office()
        report = macro.generate_cor(mixed_observation(), "CF-001", "TC-001", 508, "PROMPT-021")
        macro.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        event_types = [event.event_type for event in macro.department.audit_service.audit_log.events]

        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)
        self.assertNotIn("trade_recommendation", report.machine_payload)
        self.assertNotIn("position_size", report.machine_payload)
        self.assertNotIn("execution_instruction", report.machine_payload)
        self.assertNotIn("company_valuation", report.machine_payload)


if __name__ == "__main__":
    unittest.main()
