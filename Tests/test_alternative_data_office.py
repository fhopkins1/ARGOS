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
from argos.seeker import AlternativeDataObservation, AlternativeDataOffice, AlternativeDataScreener  # noqa: E402


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
            prompt_id="PROMPT-026",
            title="Alternative Data Report Prompt",
            owner_group_id="DEP-003",
            author_staff_id="STF-028",
            purpose="Generate deterministic alternative data reports.",
            allowed_environments=("development",),
            input_contract_types=("ALTERNATIVE_DATA_OBSERVATION",),
            output_contract_types=("COR", "ATR", "IGR", "AIR"),
            dependencies=("EO-026",),
            safety_notes="No trade recommendations, sizing, execution, or Risk Office bypass.",
        ),
        "1.0.0",
        "Create descriptive alternative data reports only.",
    )
    return repository


def active_observation() -> AlternativeDataObservation:
    return AlternativeDataObservation(
        satellite_activity_change=0.16,
        shipping_delay_index=0.72,
        web_traffic_change=0.24,
        consumer_activity_change=0.11,
        energy_consumption_change=0.08,
        weather_disruption_score=0.65,
        supply_chain_stress_score=0.2,
        patent_activity_change=0.18,
        employment_posting_change=-0.07,
    )


def unknown_observation() -> AlternativeDataObservation:
    return AlternativeDataObservation(
        satellite_activity_change=None,
        shipping_delay_index=None,
        web_traffic_change=None,
        consumer_activity_change=None,
        energy_consumption_change=None,
        weather_disruption_score=None,
        supply_chain_stress_score=None,
        patent_activity_change=None,
        employment_posting_change=None,
    )


def office() -> AlternativeDataOffice:
    return AlternativeDataOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class AlternativeDataOfficeTests(unittest.TestCase):
    def test_alternative_data_ingestion_generates_nine_signals(self) -> None:
        signals = AlternativeDataScreener().monitor(active_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(len(signals), 9)
        self.assertEqual(by_name["satellite_imagery"].signal, "satellite_activity_expanding")
        self.assertEqual(by_name["shipping_logistics"].signal, "shipping_delay_threat")
        self.assertEqual(by_name["web_traffic"].signal, "web_traffic_expanding")
        self.assertEqual(by_name["consumer_activity"].signal, "consumer_activity_expanding")
        self.assertEqual(by_name["employment_intelligence"].signal, "employment_postings_contracting")

    def test_signal_detection_classifies_real_world_indicators(self) -> None:
        signals = AlternativeDataScreener().monitor(active_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(by_name["satellite_imagery"].report_hint, "alternative_intelligence")
        self.assertEqual(by_name["web_traffic"].report_hint, "alternative_intelligence")
        self.assertEqual(by_name["energy_consumption"].report_hint, "alternative_intelligence")
        self.assertEqual(by_name["consumer_activity"].report_hint, "opportunity")

    def test_threat_generation_documents_real_world_stress(self) -> None:
        alternative = office()

        threat = alternative.generate_threat_report(active_observation(), "CF-001", "TC-001", 1001, "PROMPT-026")
        signals = {signal["signal"] for signal in threat.machine_payload["alternative_data_signals"]}

        self.assertEqual(threat.contract_type, "ATR")
        self.assertIn("shipping_delay_threat", signals)
        self.assertIn("weather_disruption_threat", signals)
        self.assertIn("employment_postings_contracting", signals)

    def test_report_generation_persists_all_alternative_report_types(self) -> None:
        alternative = office()

        cor = alternative.generate_cor(active_observation(), "CF-001", "TC-001", 1002, "PROMPT-026")
        threat = alternative.generate_threat_report(active_observation(), "CF-001", "TC-001", 1003, "PROMPT-026")
        gap = alternative.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 1004, "PROMPT-026")
        intelligence = alternative.generate_alternative_intelligence_report(active_observation(), "CF-001", "TC-001", 1005, "PROMPT-026")

        self.assertEqual(cor.contract_type, "COR")
        self.assertEqual(threat.contract_type, "ATR")
        self.assertEqual(gap.contract_type, "IGR")
        self.assertEqual(intelligence.contract_type, "AIR")
        self.assertEqual(intelligence.machine_payload["report_status"], "alternative_intelligence_available")
        self.assertIsNotNone(alternative.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-1005"))

    def test_unknown_detection_documents_missing_alternative_data(self) -> None:
        alternative = office()

        gap = alternative.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 1006, "PROMPT-026")
        signals = {signal["signal"] for signal in gap.machine_payload["alternative_data_signals"]}

        self.assertIn("satellite_activity_unknown", signals)
        self.assertIn("shipping_logistics_unknown", signals)
        self.assertIn("employment_intelligence_unknown", signals)

    def test_courier_routing_uses_deterministic_interfaces(self) -> None:
        alternative = office()
        report = alternative.generate_alternative_intelligence_report(active_observation(), "CF-001", "TC-001", 1007, "PROMPT-026")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = alternative.route_report(report, executive_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-1007"), report)
        self.assertEqual(alternative.office.routed_reports, 1)

    def test_instrument_panel_updates_and_reports_healthy_office(self) -> None:
        alternative = office()
        cor = alternative.generate_cor(active_observation(), "CF-001", "TC-001", 1008, "PROMPT-026")
        threat = alternative.generate_threat_report(active_observation(), "CF-001", "TC-001", 1009, "PROMPT-026")
        gap = alternative.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 1010, "PROMPT-026")
        intelligence = alternative.generate_alternative_intelligence_report(active_observation(), "CF-001", "TC-001", 1011, "PROMPT-026")
        alternative.route_report(cor, IncomingMailbox("STF-002", "DEP-002"))
        alternative.route_report(threat, IncomingMailbox("STF-002", "DEP-002"))
        alternative.route_report(gap, IncomingMailbox("STF-002", "DEP-002"))
        alternative.route_report(intelligence, IncomingMailbox("STF-002", "DEP-002"))

        panel = alternative.instrument_panel()

        self.assertEqual(panel.office_id, "SEEKER-OFFICE-008")
        self.assertEqual(panel.metrics.reports_generated, 4)
        self.assertEqual(panel.metrics.routed_reports, 4)
        self.assertEqual(panel.health.status, "healthy")

    def test_routing_generates_audit_events_and_payload_preserves_boundaries(self) -> None:
        alternative = office()
        report = alternative.generate_cor(active_observation(), "CF-001", "TC-001", 1012, "PROMPT-026")
        alternative.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        event_types = [event.event_type for event in alternative.department.audit_service.audit_log.events]

        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)
        self.assertTrue(report.machine_payload["risk_doctrine_required"])
        self.assertNotIn("trade_recommendation", report.machine_payload)
        self.assertNotIn("position_size", report.machine_payload)
        self.assertNotIn("execution_instruction", report.machine_payload)


if __name__ == "__main__":
    unittest.main()
