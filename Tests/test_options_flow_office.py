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
from argos.seeker import OptionsFlowObservation, OptionsFlowOffice, OptionsFlowScreener  # noqa: E402


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
            prompt_id="PROMPT-023",
            title="Options Flow Report Prompt",
            owner_group_id="DEP-003",
            author_staff_id="STF-025",
            purpose="Generate deterministic options-flow reports.",
            allowed_environments=("development",),
            input_contract_types=("OPTIONS_FLOW_OBSERVATION",),
            output_contract_types=("COR", "IAR", "OTR", "IGR"),
            dependencies=("EO-023",),
            safety_notes="No trade recommendations, sizing, execution, or Risk Office bypass.",
        ),
        "1.0.0",
        "Create descriptive options-flow reports only.",
    )
    return repository


def active_observation() -> OptionsFlowObservation:
    return OptionsFlowObservation(
        option_volume=120_000,
        average_option_volume=40_000,
        largest_order_notional=2_500_000,
        gamma_exposure=-800_000,
        delta_exposure=900_000,
        open_interest=300_000,
        open_interest_change=50_000,
        implied_volatility=0.62,
        historical_volatility=0.38,
        surface_skew=0.31,
        dealer_gamma_position=-1_200_000,
        days_to_expiration=3,
    )


def unknown_observation() -> OptionsFlowObservation:
    return OptionsFlowObservation(
        option_volume=None,
        average_option_volume=None,
        largest_order_notional=None,
        gamma_exposure=None,
        delta_exposure=None,
        open_interest=None,
        open_interest_change=None,
        implied_volatility=None,
        historical_volatility=None,
        surface_skew=None,
        dealer_gamma_position=None,
        days_to_expiration=None,
    )


def office() -> OptionsFlowOffice:
    return OptionsFlowOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class OptionsFlowOfficeTests(unittest.TestCase):
    def test_options_data_ingestion_generates_nine_signals(self) -> None:
        signals = OptionsFlowScreener().monitor(active_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(len(signals), 9)
        self.assertEqual(by_name["unusual_options_activity"].signal, "unusual_options_activity")
        self.assertEqual(by_name["large_order"].signal, "large_order_detected")
        self.assertEqual(by_name["gamma_exposure"].signal, "negative_gamma_threat")
        self.assertEqual(by_name["open_interest"].signal, "open_interest_build")
        self.assertEqual(by_name["expiration"].signal, "near_expiration_pressure")

    def test_institutional_activity_detection_and_gamma_calculation(self) -> None:
        signals = OptionsFlowScreener().monitor(active_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(by_name["unusual_options_activity"].value, 3)
        self.assertEqual(by_name["unusual_options_activity"].report_hint, "institutional_activity")
        self.assertEqual(by_name["delta_exposure"].report_hint, "institutional_activity")
        self.assertEqual(by_name["gamma_exposure"].value, -800_000)
        self.assertEqual(by_name["gamma_exposure"].report_hint, "threat")

    def test_open_interest_analysis_flags_build(self) -> None:
        signal = {item.seeker: item for item in OptionsFlowScreener().monitor(active_observation())}["open_interest"]

        self.assertEqual(signal.signal, "open_interest_build")
        self.assertEqual(signal.value, 50_000)
        self.assertEqual(signal.report_hint, "institutional_activity")

    def test_report_generation_persists_all_options_report_types(self) -> None:
        options = office()

        cor = options.generate_cor(active_observation(), "CF-001", "TC-001", 701, "PROMPT-023")
        activity = options.generate_institutional_activity_report(active_observation(), "CF-001", "TC-001", 702, "PROMPT-023")
        threat = options.generate_threat_report(active_observation(), "CF-001", "TC-001", 703, "PROMPT-023")
        gap = options.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 704, "PROMPT-023")

        self.assertEqual(cor.contract_type, "COR")
        self.assertEqual(activity.contract_type, "IAR")
        self.assertEqual(threat.contract_type, "OTR")
        self.assertEqual(gap.contract_type, "IGR")
        self.assertEqual(activity.machine_payload["report_status"], "institutional_activity_identified")
        self.assertEqual(threat.machine_payload["report_status"], "options_threat_identified")
        self.assertEqual(gap.machine_payload["report_status"], "options_information_gap")
        self.assertIsNotNone(options.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-704"))

    def test_unknown_detection_documents_missing_options_data(self) -> None:
        options = office()

        gap = options.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 705, "PROMPT-023")
        signals = {signal["signal"] for signal in gap.machine_payload["options_flow_signals"]}

        self.assertIn("options_activity_unknown", signals)
        self.assertIn("gamma_exposure_unknown", signals)
        self.assertIn("dealer_positioning_unknown", signals)

    def test_courier_routing_uses_deterministic_interfaces(self) -> None:
        options = office()
        report = options.generate_institutional_activity_report(active_observation(), "CF-001", "TC-001", 706, "PROMPT-023")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = options.route_report(report, executive_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-706"), report)
        self.assertEqual(options.office.routed_reports, 1)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        options = office()
        cor = options.generate_cor(active_observation(), "CF-001", "TC-001", 707, "PROMPT-023")
        activity = options.generate_institutional_activity_report(active_observation(), "CF-001", "TC-001", 708, "PROMPT-023")
        threat = options.generate_threat_report(active_observation(), "CF-001", "TC-001", 709, "PROMPT-023")
        gap = options.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 710, "PROMPT-023")
        options.route_report(cor, IncomingMailbox("STF-002", "DEP-002"))
        options.route_report(activity, IncomingMailbox("STF-002", "DEP-002"))
        options.route_report(threat, IncomingMailbox("STF-002", "DEP-002"))
        options.route_report(gap, IncomingMailbox("STF-002", "DEP-002"))

        panel = options.instrument_panel()

        self.assertEqual(panel.office_id, "SEEKER-OFFICE-005")
        self.assertEqual(panel.metrics.reports_generated, 4)
        self.assertEqual(panel.metrics.routed_reports, 4)
        self.assertEqual(panel.health.status, "healthy")

    def test_routing_generates_audit_events_and_payload_preserves_boundaries(self) -> None:
        options = office()
        report = options.generate_cor(active_observation(), "CF-001", "TC-001", 711, "PROMPT-023")
        options.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        event_types = [event.event_type for event in options.department.audit_service.audit_log.events]

        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)
        self.assertTrue(report.machine_payload["risk_doctrine_required"])
        self.assertNotIn("trade_recommendation", report.machine_payload)
        self.assertNotIn("position_size", report.machine_payload)
        self.assertNotIn("execution_instruction", report.machine_payload)


if __name__ == "__main__":
    unittest.main()
