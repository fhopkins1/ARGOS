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
from argos.seeker import EventIntelligenceObservation, EventIntelligenceOffice, EventIntelligenceScreener  # noqa: E402


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
            prompt_id="PROMPT-025",
            title="Event Intelligence Report Prompt",
            owner_group_id="DEP-003",
            author_staff_id="STF-027",
            purpose="Generate deterministic event intelligence reports.",
            allowed_environments=("development",),
            input_contract_types=("EVENT_INTELLIGENCE_OBSERVATION",),
            output_contract_types=("COR", "ETR", "IGR", "EAR"),
            dependencies=("EO-025",),
            safety_notes="No trade recommendations, sizing, execution, or Risk Office bypass.",
        ),
        "1.0.0",
        "Create descriptive event intelligence reports only.",
    )
    return repository


def active_observation() -> EventIntelligenceObservation:
    return EventIntelligenceObservation(
        earnings_surprise=0.14,
        merger_announced=True,
        bankruptcy_risk_score=0.82,
        regulatory_severity=0.7,
        fda_decision_score=-0.6,
        litigation_severity=0.65,
        product_launch_score=0.55,
        geopolitical_severity=0.3,
        supply_chain_disruption_score=0.2,
    )


def unknown_observation() -> EventIntelligenceObservation:
    return EventIntelligenceObservation(
        earnings_surprise=None,
        merger_announced=None,
        bankruptcy_risk_score=None,
        regulatory_severity=None,
        fda_decision_score=None,
        litigation_severity=None,
        product_launch_score=None,
        geopolitical_severity=None,
        supply_chain_disruption_score=None,
    )


def office() -> EventIntelligenceOffice:
    return EventIntelligenceOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class EventIntelligenceOfficeTests(unittest.TestCase):
    def test_event_ingestion_generates_nine_event_signals(self) -> None:
        signals = EventIntelligenceScreener().monitor(active_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(len(signals), 9)
        self.assertEqual(by_name["earnings_event"].signal, "positive_earnings_event")
        self.assertEqual(by_name["merger_acquisition"].signal, "ma_event_announced")
        self.assertEqual(by_name["bankruptcy"].signal, "bankruptcy_risk_elevated")
        self.assertEqual(by_name["regulatory_event"].signal, "regulatory_event_material")
        self.assertEqual(by_name["product_launch"].signal, "product_launch_constructive")

    def test_event_classification_and_threat_detection_are_deterministic(self) -> None:
        signals = EventIntelligenceScreener().monitor(active_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(by_name["bankruptcy"].report_hint, "threat")
        self.assertEqual(by_name["fda_event"].signal, "fda_event_negative")
        self.assertEqual(by_name["litigation"].report_hint, "threat")
        self.assertEqual(by_name["merger_acquisition"].report_hint, "event_assessment")
        self.assertEqual(by_name["supply_chain_event"].report_hint, "event_assessment")

    def test_report_generation_persists_all_event_report_types(self) -> None:
        event_office = office()

        cor = event_office.generate_cor(active_observation(), "CF-001", "TC-001", 901, "PROMPT-025")
        threat = event_office.generate_threat_report(active_observation(), "CF-001", "TC-001", 902, "PROMPT-025")
        gap = event_office.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 903, "PROMPT-025")
        assessment = event_office.generate_event_assessment_report(active_observation(), "CF-001", "TC-001", 904, "PROMPT-025")

        self.assertEqual(cor.contract_type, "COR")
        self.assertEqual(threat.contract_type, "ETR")
        self.assertEqual(gap.contract_type, "IGR")
        self.assertEqual(assessment.contract_type, "EAR")
        self.assertEqual(assessment.machine_payload["report_status"], "event_assessment_available")
        self.assertIsNotNone(event_office.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-904"))

    def test_threat_report_documents_objective_event_threats(self) -> None:
        event_office = office()

        threat = event_office.generate_threat_report(active_observation(), "CF-001", "TC-001", 905, "PROMPT-025")
        signals = {signal["signal"] for signal in threat.machine_payload["event_intelligence_signals"]}

        self.assertIn("bankruptcy_risk_elevated", signals)
        self.assertIn("regulatory_event_material", signals)
        self.assertIn("fda_event_negative", signals)
        self.assertIn("litigation_threat", signals)

    def test_unknown_detection_documents_missing_event_data(self) -> None:
        event_office = office()

        gap = event_office.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 906, "PROMPT-025")
        signals = {signal["signal"] for signal in gap.machine_payload["event_intelligence_signals"]}

        self.assertIn("earnings_event_unknown", signals)
        self.assertIn("ma_event_unknown", signals)
        self.assertIn("supply_chain_event_unknown", signals)

    def test_courier_routing_uses_deterministic_interfaces(self) -> None:
        event_office = office()
        report = event_office.generate_event_assessment_report(active_observation(), "CF-001", "TC-001", 907, "PROMPT-025")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = event_office.route_report(report, executive_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-907"), report)
        self.assertEqual(event_office.office.routed_reports, 1)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        event_office = office()
        cor = event_office.generate_cor(active_observation(), "CF-001", "TC-001", 908, "PROMPT-025")
        threat = event_office.generate_threat_report(active_observation(), "CF-001", "TC-001", 909, "PROMPT-025")
        gap = event_office.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 910, "PROMPT-025")
        assessment = event_office.generate_event_assessment_report(active_observation(), "CF-001", "TC-001", 911, "PROMPT-025")
        event_office.route_report(cor, IncomingMailbox("STF-002", "DEP-002"))
        event_office.route_report(threat, IncomingMailbox("STF-002", "DEP-002"))
        event_office.route_report(gap, IncomingMailbox("STF-002", "DEP-002"))
        event_office.route_report(assessment, IncomingMailbox("STF-002", "DEP-002"))

        panel = event_office.instrument_panel()

        self.assertEqual(panel.office_id, "SEEKER-OFFICE-007")
        self.assertEqual(panel.metrics.reports_generated, 4)
        self.assertEqual(panel.metrics.routed_reports, 4)
        self.assertEqual(panel.health.status, "healthy")

    def test_routing_generates_audit_events_and_payload_preserves_boundaries(self) -> None:
        event_office = office()
        report = event_office.generate_cor(active_observation(), "CF-001", "TC-001", 912, "PROMPT-025")
        event_office.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        event_types = [event.event_type for event in event_office.department.audit_service.audit_log.events]

        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)
        self.assertTrue(report.machine_payload["risk_doctrine_required"])
        self.assertNotIn("trade_recommendation", report.machine_payload)
        self.assertNotIn("position_size", report.machine_payload)
        self.assertNotIn("execution_instruction", report.machine_payload)


if __name__ == "__main__":
    unittest.main()
