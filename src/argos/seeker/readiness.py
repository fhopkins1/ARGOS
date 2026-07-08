"""Seeker Operational Readiness Review."""

from __future__ import annotations

from dataclasses import dataclass

from argos.foundation.audit import AuditEventType, AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas
from argos.foundation.prompts import PromptPassport, PromptRepository
from argos.foundation.testing import TestExecutionResult, TestRunner, foundation_test_registry

from .alternative_data import AlternativeDataObservation, AlternativeDataOffice
from .cryptocurrency import CryptocurrencyObservation, CryptocurrencyOffice
from .event_intelligence import EventIntelligenceObservation, EventIntelligenceOffice
from .fundamental import FundamentalObservation, FundamentalResearchOffice
from .fusion import FusionOffice
from .macroeconomic import MacroeconomicObservation, MacroeconomicOffice
from .news_sentiment import NewsItem, NewsSentimentObservation, NewsSentimentOffice
from .options_flow import OptionsFlowObservation, OptionsFlowOffice
from .technical import MarketObservation, TechnicalAnalysisOffice


@dataclass(frozen=True)
class SeekerReadinessCheck:
    """Single Seeker readiness check."""

    check_id: str
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class SeekerReadinessResult:
    """Seeker readiness result."""

    checks: tuple[SeekerReadinessCheck, ...]
    test_results: tuple[TestExecutionResult, ...]

    @property
    def certified(self) -> bool:
        """Return whether Seeker Group is certified."""
        return all(check.passed for check in self.checks) and all(result.successful for result in self.test_results)


class SeekerReadinessVerifier:
    """Verify the Seeker Group as a deterministic intelligence organization."""

    def verify(self, test_results: tuple[TestExecutionResult, ...] | None = None) -> SeekerReadinessResult:
        """Run Seeker readiness checks."""
        if test_results is None:
            test_results = TestRunner().run_all(foundation_test_registry())
        fixture = _seeker_fixture()
        checks = (
            self._check_tests(test_results),
            self._check_office_integration(fixture),
            self._check_reports(fixture),
            self._check_fusion_and_independent_scores(fixture),
            self._check_replay_and_audit(fixture),
            self._check_foundation_integration(fixture),
        )
        return SeekerReadinessResult(checks, test_results)

    def _check_tests(self, test_results: tuple[TestExecutionResult, ...]) -> SeekerReadinessCheck:
        failures = [result.suite_id for result in test_results if not result.successful]
        return SeekerReadinessCheck(
            "SORR-CHECK-001",
            "Seeker deterministic test suites",
            not failures,
            "All registered suites passed." if not failures else f"Failed suites: {', '.join(failures)}",
        )

    def _check_office_integration(self, fixture: "_SeekerFixture") -> SeekerReadinessCheck:
        required = {
            "SEEKER-OFFICE-001",
            "SEEKER-OFFICE-002",
            "SEEKER-OFFICE-003",
            "SEEKER-OFFICE-004",
            "SEEKER-OFFICE-005",
            "SEEKER-OFFICE-006",
            "SEEKER-OFFICE-007",
            "SEEKER-OFFICE-008",
            "SEEKER-OFFICE-009",
        }
        present = {report.machine_payload["office_id"] for report in fixture.generated_reports}
        present.add(fixture.fusion_mir.machine_payload["office_id"])
        return SeekerReadinessCheck(
            "SORR-CHECK-002",
            "Every Seeker office interoperates",
            required.issubset(present),
            f"Verified offices: {', '.join(sorted(present))}.",
        )

    def _check_reports(self, fixture: "_SeekerFixture") -> SeekerReadinessCheck:
        contract_types = {report.contract_type for report in fixture.generated_reports + (fixture.fusion_mir,)}
        required = {"COR", "MTR", "STR", "OTR", "CTR", "ETR", "ATR", "IGR", "MIR"}
        persisted = all(
            fixture.persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id) is not None
            for report in fixture.generated_reports + (fixture.fusion_mir,)
        )
        return SeekerReadinessCheck(
            "SORR-CHECK-003",
            "Canonical Seeker reports",
            required.issubset(contract_types) and persisted,
            f"Report types verified: {', '.join(sorted(contract_types))}.",
        )

    def _check_fusion_and_independent_scores(self, fixture: "_SeekerFixture") -> SeekerReadinessCheck:
        payload = fixture.fusion_mir.machine_payload
        passed = (
            payload["confidence"] > 0
            and payload["agreement_score"] >= 0
            and payload["evidence_diversity"] >= 2
            and payload["source_reports_modified"] is False
        )
        return SeekerReadinessCheck(
            "SORR-CHECK-004",
            "Fusion and Independent Evidence Scores",
            passed,
            f"Confidence {payload['confidence']} with evidence diversity {payload['evidence_diversity']}.",
        )

    def _check_replay_and_audit(self, fixture: "_SeekerFixture") -> SeekerReadinessCheck:
        case_events = fixture.audit.search_by_case_file_id("CF-001")
        event_types = [event.event_type for event in case_events]
        passed = (
            AuditEventType.COURIER_TRANSFER in event_types
            and AuditEventType.DOCUMENT_CREATED in event_types
            and fixture.audit.audit_log.verify_integrity()
        )
        return SeekerReadinessCheck(
            "SORR-CHECK-005",
            "Seeker replay and audit reconstruction",
            passed,
            f"Reconstructed {len(case_events)} audit events for CF-001.",
        )

    def _check_foundation_integration(self, fixture: "_SeekerFixture") -> SeekerReadinessCheck:
        prompt_snapshot_seen = any("prompt_snapshot_id" in report.machine_payload for report in fixture.generated_reports)
        configuration_valid = fixture.config.validate_startup() is None
        delivered = all(result.delivered for result in fixture.delivery_results)
        return SeekerReadinessCheck(
            "SORR-CHECK-006",
            "Courier, Persistence, Configuration, and Prompt Repository integration",
            prompt_snapshot_seen and configuration_valid and delivered,
            f"Delivered {len(fixture.delivery_results)} reports through Courier.",
        )


@dataclass
class _SeekerFixture:
    config: ConfigurationService
    persistence: InMemoryPersistenceRepository
    audit: AuditService
    prompt_repository: PromptRepository
    generated_reports: tuple[object, ...]
    fusion_mir: object
    delivery_results: tuple[object, ...]


class SeekerReadinessReportGenerator:
    """Generate Seeker readiness artifacts."""

    def __init__(self, result: SeekerReadinessResult) -> None:
        self.result = result

    def seeker_orr(self) -> str:
        """Generate S-ORR."""
        lines = [
            "# S-ORR Seeker Operational Readiness Review",
            "",
            "Status: PASS" if self.result.certified else "Status: FAIL",
            "",
            "## Readiness Checks",
        ]
        for check in self.result.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {check.check_id}: {status} - {check.name}. {check.detail}")
        return "\n".join(lines) + "\n"

    def seeker_completion_report(self) -> str:
        """Generate SCR-001."""
        status = "COMPLETE" if self.result.certified else "INCOMPLETE"
        return "\n".join(
            [
                "# SCR-001 Seeker Completion Report",
                "",
                f"Seeker Status: {status}",
                "",
                "Completed Engineering Orders: EO-018 through EO-028",
                "",
                "Verified Seeker capabilities:",
                "- Seeker Department framework",
                "- Eight deterministic discovery offices",
                "- Multi-Office Intelligence Fusion Office",
                "- Candidate, threat, information gap, and fusion reports",
                "- Courier, audit, persistence, configuration, and prompt repository integration",
                "- Operational readiness verification",
                "",
            ]
        )

    def authorization_to_proceed(self) -> str:
        """Generate Group 4 authorization."""
        decision = "AUTHORIZED" if self.result.certified else "NOT AUTHORIZED"
        return "\n".join(
            [
                "# Authorization to Proceed - Group 4 Analyst Group",
                "",
                f"Decision: {decision}",
                "",
                "Scope: Analyst Group implementation may begin only after S-ORR passes.",
                "",
            ]
        )


def _seeker_fixture() -> _SeekerFixture:
    config = ConfigurationService.load(
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
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    prompts = _prompt_repository()
    executive_inbox = IncomingMailbox("STF-002", "DEP-002")

    technical = TechnicalAnalysisOffice(config, persistence, audit, prompts)
    fundamental = FundamentalResearchOffice(config, persistence, audit, prompts)
    macro = MacroeconomicOffice(config, persistence, audit, prompts)
    sentiment = NewsSentimentOffice(config, persistence, audit, prompts)
    options = OptionsFlowOffice(config, persistence, audit, prompts)
    crypto = CryptocurrencyOffice(config, persistence, audit, prompts)
    event = EventIntelligenceOffice(config, persistence, audit, prompts)
    alternative = AlternativeDataOffice(config, persistence, audit, prompts)
    fusion = FusionOffice(config, persistence, audit, prompts)

    reports = (
        technical.generate_cor(_technical_observations(), "CF-001", "TC-001", 1201, "PROMPT-019"),
        fundamental.generate_cor(_fundamental_observation(), "CF-001", "TC-001", 1202, "PROMPT-020"),
        macro.generate_cor(_macro_observation(), "CF-001", "TC-001", 1203, "PROMPT-021"),
        macro.generate_threat_report(_macro_observation(), "CF-001", "TC-001", 1204, "PROMPT-021"),
        macro.generate_information_gap_report(_macro_unknown(), "CF-001", "TC-001", 1205, "PROMPT-021"),
        sentiment.generate_cor(_news_observation(), "CF-001", "TC-001", 1206, "PROMPT-022"),
        sentiment.generate_threat_report(_news_observation(), "CF-001", "TC-001", 1207, "PROMPT-022"),
        options.generate_threat_report(_options_observation(), "CF-001", "TC-001", 1208, "PROMPT-023"),
        crypto.generate_threat_report(_crypto_observation(), "CF-001", "TC-001", 1209, "PROMPT-024"),
        event.generate_threat_report(_event_observation(), "CF-001", "TC-001", 1210, "PROMPT-025"),
        alternative.generate_threat_report(_alternative_observation(), "CF-001", "TC-001", 1211, "PROMPT-026"),
    )
    fusion_mir = fusion.generate_mir(reports, "CF-001", "TC-001", 1212, "PROMPT-027")

    delivery_results = (
        technical.route_cor(reports[0], executive_inbox),
        macro.route_report(reports[3], executive_inbox),
        sentiment.route_report(reports[6], executive_inbox),
        options.route_report(reports[7], executive_inbox),
        crypto.route_report(reports[8], executive_inbox),
        event.route_report(reports[9], executive_inbox),
        alternative.route_report(reports[10], executive_inbox),
        fusion.route_report(fusion_mir, executive_inbox),
    )
    return _SeekerFixture(config, persistence, audit, prompts, reports, fusion_mir, delivery_results)


def _prompt_repository() -> PromptRepository:
    repository = PromptRepository()
    prompt_specs = (
        ("PROMPT-019", "Technical COR Prompt", "STF-021", ("COR",), "EO-019"),
        ("PROMPT-020", "Fundamental COR Prompt", "STF-022", ("COR",), "EO-020"),
        ("PROMPT-021", "Macroeconomic Report Prompt", "STF-023", ("COR", "MTR", "IGR"), "EO-021"),
        ("PROMPT-022", "News Sentiment Report Prompt", "STF-024", ("COR", "STR", "IGR"), "EO-022"),
        ("PROMPT-023", "Options Flow Report Prompt", "STF-025", ("COR", "IAR", "OTR", "IGR"), "EO-023"),
        ("PROMPT-024", "Cryptocurrency Report Prompt", "STF-026", ("COR", "CXR", "CTR", "IGR"), "EO-024"),
        ("PROMPT-025", "Event Intelligence Report Prompt", "STF-027", ("COR", "ETR", "IGR", "EAR"), "EO-025"),
        ("PROMPT-026", "Alternative Data Report Prompt", "STF-028", ("COR", "ATR", "IGR", "AIR"), "EO-026"),
        ("PROMPT-027", "Fusion Report Prompt", "STF-029", ("MIR", "CFR", "ICR"), "EO-027"),
    )
    for prompt_id, title, staff_id, outputs, dependency in prompt_specs:
        repository.register(
            PromptPassport(
                prompt_id=prompt_id,
                title=title,
                owner_group_id="DEP-003",
                author_staff_id=staff_id,
                purpose="Seeker readiness fixture prompt.",
                allowed_environments=("development",),
                input_contract_types=("READINESS_INPUT",),
                output_contract_types=outputs,
                dependencies=(dependency,),
                safety_notes="No trading authority.",
            ),
            "1.0.0",
            "Generate deterministic readiness reports only.",
        )
    return repository


def _technical_observations() -> tuple[MarketObservation, ...]:
    return (
        MarketObservation(100, 101, 99, 1000),
        MarketObservation(104, 105, 102, 1400),
    )


def _fundamental_observation() -> FundamentalObservation:
    return FundamentalObservation(0.12, 0.18, 22, 0.4, 1.8, True, 1.0, 0.05, 0.7)


def _macro_observation() -> MacroeconomicObservation:
    return MacroeconomicObservation(5.2, 5.5, 4.1, 2.3, "tightening", "supportive", 1.2, -0.4, 12.5, 0.8)


def _macro_unknown() -> MacroeconomicObservation:
    return MacroeconomicObservation(None, None, None, None, None, None, None, None, None, None)


def _news_observation() -> NewsSentimentObservation:
    return NewsSentimentObservation(
        (
            NewsItem("SRC-001", "financial_news", "Guidance improves", 0.45, 0.4, "earnings", 0.9, True),
            NewsItem("SRC-002", "social", "Crowd interest grows", 0.35, 0.3, "sentiment", 0.8, True),
            NewsItem("SRC-003", "financial_news", "Regulator opens inquiry", -0.55, 0.8, "regulatory", 0.9, True),
        )
    )


def _options_observation() -> OptionsFlowObservation:
    return OptionsFlowObservation(120000, 40000, 2500000, -800000, 900000, 300000, 50000, 0.62, 0.38, 0.31, -1200000, 3)


def _crypto_observation() -> CryptocurrencyObservation:
    return CryptocurrencyObservation(0.08, 0.75, 0.12, 0.18, 250000000, -120000000, 14, 80000000, 0.05, -0.2, 0.82)


def _event_observation() -> EventIntelligenceObservation:
    return EventIntelligenceObservation(0.14, True, 0.82, 0.7, -0.6, 0.65, 0.55, 0.3, 0.2)


def _alternative_observation() -> AlternativeDataObservation:
    return AlternativeDataObservation(0.16, 0.72, 0.24, 0.11, 0.08, 0.65, 0.2, 0.18, -0.07)
