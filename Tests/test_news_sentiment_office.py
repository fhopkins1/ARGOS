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
from argos.seeker import NewsItem, NewsSentimentObservation, NewsSentimentOffice, NewsSentimentScreener  # noqa: E402


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
            prompt_id="PROMPT-022",
            title="News Sentiment Report Prompt",
            owner_group_id="DEP-003",
            author_staff_id="STF-024",
            purpose="Generate deterministic news and sentiment reports.",
            allowed_environments=("development",),
            input_contract_types=("NEWS_SENTIMENT_OBSERVATION",),
            output_contract_types=("COR", "STR", "IGR"),
            dependencies=("EO-022",),
            safety_notes="No trade recommendations, sizing, execution, or source modification.",
        ),
        "1.0.0",
        "Create descriptive news and sentiment reports only.",
    )
    return repository


def mixed_observation() -> NewsSentimentObservation:
    return NewsSentimentObservation(
        items=(
            NewsItem("SRC-001", "financial_news", "Revenue outlook improves", 0.45, 0.4, "earnings", 0.9, True),
            NewsItem("SRC-002", "social", "Retail crowd enthusiasm increases", 0.35, 0.3, "sentiment", 0.8, True),
            NewsItem("SRC-003", "institutional", "Institutional desk upgrades sector", 0.25, 0.2, "commentary", 0.7, True),
            NewsItem("SRC-007", "financial_news", "Margin guidance exceeds expectations", 0.3, 0.4, "earnings", 0.8, True),
            NewsItem("SRC-004", "financial_news", "Regulator opens inquiry", -0.55, 0.6, "regulatory", 0.9, True),
            NewsItem("SRC-005", "financial_news", "Border conflict disrupts supply route", -0.35, 0.7, "geopolitical", 0.95, True),
            NewsItem("SRC-006", "financial_news", "Unexpected CEO resignation", -0.4, 0.9, "breaking", 0.8, True),
        )
    )


def unknown_observation() -> NewsSentimentObservation:
    return NewsSentimentObservation(
        items=(
            NewsItem(None, "financial_news", "Unverified market note", None, None, "earnings", 0.4, False),
        )
    )


def office() -> NewsSentimentOffice:
    return NewsSentimentOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class NewsSentimentOfficeTests(unittest.TestCase):
    def test_news_ingestion_generates_nine_sentiment_signals(self) -> None:
        signals = NewsSentimentScreener().monitor(mixed_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(len(signals), 9)
        self.assertEqual(by_name["financial_news"].signal, "financial_news_relevant")
        self.assertEqual(by_name["social_sentiment"].signal, "social_sentiment_positive")
        self.assertEqual(by_name["regulatory_news"].signal, "regulatory_pressure")
        self.assertEqual(by_name["geopolitical_news"].signal, "geopolitical_stress")
        self.assertEqual(by_name["breaking_news"].signal, "breaking_news_threat")

    def test_sentiment_aggregation_and_narrative_detection_are_deterministic(self) -> None:
        signals = NewsSentimentScreener().monitor(mixed_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(by_name["sentiment_aggregator"].signal, "aggregate_sentiment_neutral")
        self.assertEqual(by_name["narrative_tracker"].signal, "dominant_narrative:earnings")
        self.assertEqual(by_name["narrative_tracker"].value, "earnings")

    def test_candidate_opportunity_report_generation_persists_sentiment_cor(self) -> None:
        sentiment = office()

        cor = sentiment.generate_cor(mixed_observation(), "CF-001", "TC-001", 601, "PROMPT-022")

        self.assertEqual(cor.contract_id, "DOC-601")
        self.assertEqual(cor.contract_type, "COR")
        self.assertEqual(cor.machine_payload["report_status"], "sentiment_candidate_unanalysed")
        self.assertGreater(len(cor.machine_payload["news_sentiment_signals"]), 0)
        self.assertIsNotNone(sentiment.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-601"))

    def test_threat_generation_persists_sentiment_threat_report(self) -> None:
        sentiment = office()

        report = sentiment.generate_threat_report(mixed_observation(), "CF-001", "TC-001", 602, "PROMPT-022")
        signals = {signal["signal"] for signal in report.machine_payload["news_sentiment_signals"]}

        self.assertEqual(report.contract_type, "STR")
        self.assertEqual(report.machine_payload["report_status"], "sentiment_threat_identified")
        self.assertIn("regulatory_pressure", signals)
        self.assertIn("breaking_news_threat", signals)

    def test_unknown_detection_generates_information_gap_report(self) -> None:
        sentiment = office()

        report = sentiment.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 603, "PROMPT-022")
        signals = {signal["signal"] for signal in report.machine_payload["news_sentiment_signals"]}

        self.assertEqual(report.contract_type, "IGR")
        self.assertEqual(report.machine_payload["report_status"], "sentiment_information_gap")
        self.assertIn("social_sentiment_unknown", signals)
        self.assertIn("institutional_commentary_unknown", signals)
        self.assertIn("aggregate_sentiment_unknown", signals)

    def test_courier_routing_uses_deterministic_interfaces(self) -> None:
        sentiment = office()
        report = sentiment.generate_threat_report(mixed_observation(), "CF-001", "TC-001", 604, "PROMPT-022")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = sentiment.route_report(report, executive_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-604"), report)
        self.assertEqual(sentiment.office.routed_reports, 1)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        sentiment = office()
        cor = sentiment.generate_cor(mixed_observation(), "CF-001", "TC-001", 605, "PROMPT-022")
        threat = sentiment.generate_threat_report(mixed_observation(), "CF-001", "TC-001", 606, "PROMPT-022")
        gap = sentiment.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 607, "PROMPT-022")
        sentiment.route_report(cor, IncomingMailbox("STF-002", "DEP-002"))
        sentiment.route_report(threat, IncomingMailbox("STF-002", "DEP-002"))
        sentiment.route_report(gap, IncomingMailbox("STF-002", "DEP-002"))

        panel = sentiment.instrument_panel()

        self.assertEqual(panel.office_id, "SEEKER-OFFICE-004")
        self.assertEqual(panel.metrics.reports_generated, 3)
        self.assertEqual(panel.metrics.routed_reports, 3)
        self.assertEqual(panel.health.status, "healthy")

    def test_routing_generates_audit_events_and_payload_avoids_forbidden_fields(self) -> None:
        sentiment = office()
        source = mixed_observation()
        original_items = source.items
        report = sentiment.generate_cor(source, "CF-001", "TC-001", 608, "PROMPT-022")
        sentiment.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        event_types = [event.event_type for event in sentiment.department.audit_service.audit_log.events]

        self.assertEqual(source.items, original_items)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)
        self.assertNotIn("trade_recommendation", report.machine_payload)
        self.assertNotIn("position_size", report.machine_payload)
        self.assertNotIn("execution_instruction", report.machine_payload)
        self.assertNotIn("source_modification", report.machine_payload)


if __name__ == "__main__":
    unittest.main()
