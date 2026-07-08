"""News & Sentiment Office scaffolding and deterministic monitoring."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from argos.foundation.audit import AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService

from .department import SeekerDepartment
from .offices import OfficeInstrumentPanel, SEEKER_GROUP_ID


NEWS_SENTIMENT_OFFICE_ID = "SEEKER-OFFICE-004"


@dataclass(frozen=True)
class NewsItem:
    """Immutable public information input for deterministic sentiment monitoring."""

    source_id: str | None
    source_type: str
    headline: str
    sentiment_score: float | None
    novelty_score: float | None
    topic: str
    market_relevance: float
    verified: bool


@dataclass(frozen=True)
class NewsSentimentObservation:
    """Input observation for the News & Sentiment Office."""

    items: tuple[NewsItem, ...]


@dataclass(frozen=True)
class NewsSentimentSignal:
    """Deterministic news and sentiment signal."""

    seeker: str
    signal: str
    value: float | str | None
    report_hint: str


def _items_by_source(observation: NewsSentimentObservation, source_type: str) -> tuple[NewsItem, ...]:
    return tuple(item for item in observation.items if item.source_type == source_type)


def _average_sentiment(items: tuple[NewsItem, ...]) -> float | None:
    scores = [item.sentiment_score for item in items if item.sentiment_score is not None]
    if not scores:
        return None
    return sum(scores) / len(scores)


def _high_relevance(items: tuple[NewsItem, ...]) -> tuple[NewsItem, ...]:
    return tuple(item for item in items if item.market_relevance >= 0.7)


class FinancialNewsSeeker:
    def generate(self, observation: NewsSentimentObservation) -> NewsSentimentSignal:
        items = _items_by_source(observation, "financial_news")
        if not items:
            return NewsSentimentSignal("financial_news", "financial_news_unknown", None, "information_gap")
        relevant = len(_high_relevance(items))
        signal = "financial_news_relevant" if relevant else "financial_news_low_relevance"
        return NewsSentimentSignal("financial_news", signal, relevant, "opportunity" if relevant else "information_gap")


class SocialSentimentSeeker:
    def generate(self, observation: NewsSentimentObservation) -> NewsSentimentSignal:
        items = _items_by_source(observation, "social")
        average = _average_sentiment(items)
        if average is None:
            return NewsSentimentSignal("social_sentiment", "social_sentiment_unknown", None, "information_gap")
        signal = "social_sentiment_positive" if average >= 0.25 else "social_sentiment_negative" if average <= -0.25 else "social_sentiment_neutral"
        hint = "opportunity" if signal.endswith("positive") else "threat" if signal.endswith("negative") else "information_gap"
        return NewsSentimentSignal("social_sentiment", signal, average, hint)


class InstitutionalCommentarySeeker:
    def generate(self, observation: NewsSentimentObservation) -> NewsSentimentSignal:
        items = _items_by_source(observation, "institutional")
        average = _average_sentiment(items)
        if average is None:
            return NewsSentimentSignal("institutional_commentary", "institutional_commentary_unknown", None, "information_gap")
        signal = "institutional_constructive" if average > 0 else "institutional_cautious"
        return NewsSentimentSignal("institutional_commentary", signal, average, "opportunity" if average > 0 else "threat")


class EarningsNewsSeeker:
    def generate(self, observation: NewsSentimentObservation) -> NewsSentimentSignal:
        items = tuple(item for item in observation.items if item.topic == "earnings")
        average = _average_sentiment(items)
        if average is None:
            return NewsSentimentSignal("earnings_news", "earnings_news_unknown", None, "information_gap")
        signal = "earnings_news_positive" if average > 0 else "earnings_news_negative"
        return NewsSentimentSignal("earnings_news", signal, average, "opportunity" if average > 0 else "threat")


class RegulatoryNewsSeeker:
    def generate(self, observation: NewsSentimentObservation) -> NewsSentimentSignal:
        items = tuple(item for item in observation.items if item.topic == "regulatory")
        if not items:
            return NewsSentimentSignal("regulatory_news", "regulatory_news_unknown", None, "information_gap")
        negative = any((item.sentiment_score or 0) < -0.2 for item in items)
        signal = "regulatory_pressure" if negative else "regulatory_clear"
        return NewsSentimentSignal("regulatory_news", signal, len(items), "threat" if negative else "opportunity")


class GeopoliticalNewsSeeker:
    def generate(self, observation: NewsSentimentObservation) -> NewsSentimentSignal:
        items = tuple(item for item in observation.items if item.topic == "geopolitical")
        if not items:
            return NewsSentimentSignal("geopolitical_news", "geopolitical_news_unknown", None, "information_gap")
        severe = any(item.market_relevance >= 0.8 and (item.sentiment_score or 0) < 0 for item in items)
        signal = "geopolitical_stress" if severe else "geopolitical_stable"
        return NewsSentimentSignal("geopolitical_news", signal, len(items), "threat" if severe else "opportunity")


class BreakingNewsSeeker:
    def generate(self, observation: NewsSentimentObservation) -> NewsSentimentSignal:
        novel_items = tuple(item for item in observation.items if item.novelty_score is not None and item.novelty_score >= 0.8)
        if not novel_items:
            return NewsSentimentSignal("breaking_news", "breaking_news_absent", 0, "information_gap")
        negative = any((item.sentiment_score or 0) < 0 for item in novel_items)
        signal = "breaking_news_threat" if negative else "breaking_news_opportunity"
        return NewsSentimentSignal("breaking_news", signal, len(novel_items), "threat" if negative else "opportunity")


class NarrativeTracker:
    def generate(self, observation: NewsSentimentObservation) -> NewsSentimentSignal:
        topic_counts: dict[str, int] = {}
        for item in observation.items:
            topic_counts[item.topic] = topic_counts.get(item.topic, 0) + 1
        if not topic_counts:
            return NewsSentimentSignal("narrative_tracker", "narrative_unknown", None, "information_gap")
        topic = sorted(topic_counts.items(), key=lambda entry: (-entry[1], entry[0]))[0][0]
        signal = f"dominant_narrative:{topic}"
        return NewsSentimentSignal("narrative_tracker", signal, topic, "opportunity")


class SentimentAggregator:
    def generate(self, observation: NewsSentimentObservation) -> NewsSentimentSignal:
        average = _average_sentiment(observation.items)
        if average is None:
            return NewsSentimentSignal("sentiment_aggregator", "aggregate_sentiment_unknown", None, "information_gap")
        signal = "aggregate_sentiment_positive" if average >= 0.15 else "aggregate_sentiment_negative" if average <= -0.15 else "aggregate_sentiment_neutral"
        hint = "opportunity" if signal.endswith("positive") else "threat" if signal.endswith("negative") else "information_gap"
        return NewsSentimentSignal("sentiment_aggregator", signal, average, hint)


class NewsSentimentScreener:
    """Combines news and sentiment seekers without trade recommendation."""

    def __init__(self) -> None:
        self.seekers = (
            FinancialNewsSeeker(),
            SocialSentimentSeeker(),
            InstitutionalCommentarySeeker(),
            EarningsNewsSeeker(),
            RegulatoryNewsSeeker(),
            GeopoliticalNewsSeeker(),
            BreakingNewsSeeker(),
            NarrativeTracker(),
            SentimentAggregator(),
        )

    def monitor(self, observation: NewsSentimentObservation) -> tuple[NewsSentimentSignal, ...]:
        return tuple(seeker.generate(observation) for seeker in self.seekers)


class NewsSentimentOfficeChief:
    """Office Chief for deterministic News & Sentiment Office."""

    def __init__(self, screener: NewsSentimentScreener | None = None) -> None:
        self.screener = screener or NewsSentimentScreener()

    def review(self, observation: NewsSentimentObservation) -> tuple[NewsSentimentSignal, ...]:
        return self.screener.monitor(observation)


class NewsSentimentOffice:
    """News & Sentiment Office integrated with Seeker Department."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = SeekerDepartment(
            configuration_service,
            persistence_repository,
            audit_service,
            prompt_repository,
        )
        self.office = self.department.offices[NEWS_SENTIMENT_OFFICE_ID]
        self.chief = NewsSentimentOfficeChief()
        self.last_signals: tuple[NewsSentimentSignal, ...] = ()

    def ingest(self, observation: NewsSentimentObservation) -> tuple[NewsSentimentSignal, ...]:
        self.last_signals = self.chief.review(observation)
        return self.last_signals

    def generate_cor(
        self,
        observation: NewsSentimentObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "opportunity")
        return self._generate_report(
            "COR",
            "sentiment_candidate_unanalysed",
            "News & Sentiment Candidate Opportunity Report.",
            signals,
            case_file_id,
            trade_cycle_id,
            document_sequence,
            prompt_id,
        )

    def generate_threat_report(
        self,
        observation: NewsSentimentObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "threat")
        return self._generate_report(
            "STR",
            "sentiment_threat_identified",
            "Sentiment Threat Report.",
            signals,
            case_file_id,
            trade_cycle_id,
            document_sequence,
            prompt_id,
        )

    def generate_information_gap_report(
        self,
        observation: NewsSentimentObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "information_gap")
        return self._generate_report(
            "IGR",
            "sentiment_information_gap",
            "News & Sentiment Information Gap Report.",
            signals,
            case_file_id,
            trade_cycle_id,
            document_sequence,
            prompt_id,
        )

    def route_report(self, report: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_cor(NEWS_SENTIMENT_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> OfficeInstrumentPanel:
        return self.office.instrument_panel()

    def _generate_report(
        self,
        contract_type: str,
        report_status: str,
        human_summary: str,
        signals: tuple[NewsSentimentSignal, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(
            prompt_id,
            case_file_id,
            trade_cycle_id,
        )
        created = utc_timestamp()
        payload = {
            "office_id": NEWS_SENTIMENT_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "report_status": report_status,
            "news_sentiment_signals": [signal.__dict__ for signal in signals],
        }
        signature_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        report = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type=contract_type,
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            parent_contract_ids=(),
            produced_by_staff_id=self.office.record.configuration.staff_id,
            produced_by_group_id=SEEKER_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary=human_summary,
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=(),
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report
