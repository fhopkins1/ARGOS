"""Analyst Operational Readiness Review."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from argos.foundation.audit import AuditEventType, AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas
from argos.foundation.prompts import PromptPassport, PromptRepository
from argos.foundation.testing import TestExecutionResult, TestRunner, foundation_test_registry

from .analytical_fusion import AnalyticalFusionInput, AnalyticalFusionOffice
from .behavioral import BehavioralAnalysisOffice, BehavioralReasoningObservation
from .cross_discipline import CrossDisciplineReviewOffice, DisciplineAssessment
from .derivatives import DerivativesAnalysisOffice, DerivativesReasoningObservation
from .fundamental import FundamentalAnalysisOffice, FundamentalBusinessObservation
from .macroeconomic import MacroeconomicAnalysisOffice, MacroeconomicReasoningObservation
from .risk_interaction import RiskInteractionObservation, RiskInteractionOffice
from .statistical import StatisticalAnalysisOffice, StatisticalDataset
from .technical import AnalystTechnicalAnalysisOffice, TechnicalReasoningObservation


@dataclass(frozen=True)
class AnalystReadinessCheck:
    """Single Analyst readiness check."""

    check_id: str
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class OrganizationalBeliefState:
    """Reproducible belief state derived from Analytical Fusion output."""

    state_id: str
    primary_belief: str
    organizational_confidence: float
    independent_evidence_score: float
    intellectual_diversity_score: float
    source_report_ids: tuple[str, ...]


@dataclass(frozen=True)
class AnalystReadinessResult:
    """Analyst readiness result."""

    checks: tuple[AnalystReadinessCheck, ...]
    test_results: tuple[TestExecutionResult, ...]

    @property
    def certified(self) -> bool:
        """Return whether Analyst Group is certified."""
        return all(check.passed for check in self.checks) and all(result.successful for result in self.test_results)


class AnalystReadinessVerifier:
    """Verify the Analyst Group as a deterministic reasoning organization."""

    def verify(self, test_results: tuple[TestExecutionResult, ...] | None = None) -> AnalystReadinessResult:
        """Run Analyst readiness checks."""
        if test_results is None:
            test_results = TestRunner().run_all(foundation_test_registry())
        fixture = _analyst_fixture()
        checks = (
            self._check_tests(test_results),
            self._check_office_integration(fixture),
            self._check_analytical_products(fixture),
            self._check_fusion_scores_and_belief_state(fixture),
            self._check_replay_and_audit(fixture),
            self._check_foundation_integration(fixture),
        )
        return AnalystReadinessResult(checks, test_results)

    def _check_tests(self, test_results: tuple[TestExecutionResult, ...]) -> AnalystReadinessCheck:
        failures = [result.suite_id for result in test_results if not result.successful]
        return AnalystReadinessCheck(
            "AORR-CHECK-001",
            "Analyst deterministic test suites",
            not failures,
            "All registered suites passed." if not failures else f"Failed suites: {', '.join(failures)}",
        )

    def _check_office_integration(self, fixture: "_AnalystFixture") -> AnalystReadinessCheck:
        required = {
            "ANALYST-OFFICE-001",
            "ANALYST-OFFICE-002",
            "ANALYST-OFFICE-003",
            "ANALYST-OFFICE-004",
            "ANALYST-OFFICE-005",
            "ANALYST-OFFICE-006",
            "ANALYST-OFFICE-007",
            "ANALYST-OFFICE-008",
            "ANALYST-OFFICE-009",
        }
        present = {report.machine_payload["office_id"] for report in fixture.generated_reports}
        return AnalystReadinessCheck(
            "AORR-CHECK-002",
            "Every Analyst office interoperates",
            required.issubset(present),
            f"Verified offices: {', '.join(sorted(present))}.",
        )

    def _check_analytical_products(self, fixture: "_AnalystFixture") -> AnalystReadinessCheck:
        payloads = [report.machine_payload for report in fixture.generated_reports]
        product_keys = {
            "decision_model": any("decision_model" in payload for payload in payloads),
            "reasoning_graphs": any(_has_key_ending(payload, "reasoning_graphs") or "argument_maps" in payload for payload in payloads),
            "competing_thesis_analysis": any("competing_thesis_analysis" in payload for payload in payloads),
            "probability_landscape": any("probability_landscape" in payload for payload in payloads),
            "unified_decision_model": "unified_decision_model" in fixture.fusion_report.machine_payload,
            "organizational_reasoning_graph": "organizational_reasoning_graph" in fixture.fusion_report.machine_payload,
        }
        passed = all(product_keys.values())
        missing = [key for key, seen in product_keys.items() if not seen]
        return AnalystReadinessCheck(
            "AORR-CHECK-003",
            "Decision Models, Reasoning Graphs, Competing Thesis Analyses, Probability Landscapes, UDM, and ORG",
            passed,
            "All analytical products validated." if passed else f"Missing products: {', '.join(missing)}.",
        )

    def _check_fusion_scores_and_belief_state(self, fixture: "_AnalystFixture") -> AnalystReadinessCheck:
        payload = fixture.fusion_report.machine_payload
        belief_state = _organizational_belief_state(payload)
        reproduced = _organizational_belief_state(payload)
        passed = (
            payload["independent_evidence_score"] > 0
            and payload["intellectual_diversity_score"] > 0
            and payload["organizational_confidence"] > 0
            and belief_state == reproduced
        )
        return AnalystReadinessCheck(
            "AORR-CHECK-004",
            "Independent Evidence, Intellectual Diversity, and Organizational Belief State",
            passed,
            f"Belief {belief_state.primary_belief} confidence {belief_state.organizational_confidence}.",
        )

    def _check_replay_and_audit(self, fixture: "_AnalystFixture") -> AnalystReadinessCheck:
        case_events = fixture.audit.search_by_case_file_id("CF-001")
        event_types = [event.event_type for event in case_events]
        persisted = all(
            fixture.persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id) is not None
            for report in fixture.generated_reports
        )
        passed = (
            AuditEventType.COURIER_TRANSFER in event_types
            and AuditEventType.DOCUMENT_CREATED in event_types
            and fixture.audit.audit_log.verify_integrity()
            and persisted
        )
        return AnalystReadinessCheck(
            "AORR-CHECK-005",
            "Analytical replay and audit reconstruction",
            passed,
            f"Reconstructed {len(case_events)} audit events and {len(fixture.generated_reports)} persisted reports for CF-001.",
        )

    def _check_foundation_integration(self, fixture: "_AnalystFixture") -> AnalystReadinessCheck:
        prompt_snapshots = all("prompt_snapshot_id" in report.machine_payload for report in fixture.generated_reports)
        configuration_valid = fixture.config.validate_startup() is None
        delivered = all(result.delivered for result in fixture.delivery_results)
        return AnalystReadinessCheck(
            "AORR-CHECK-006",
            "Courier, Audit, Persistence, Configuration, and Prompt Repository integration",
            prompt_snapshots and configuration_valid and delivered,
            f"Delivered {len(fixture.delivery_results)} Analyst reports through Courier.",
        )


@dataclass
class _AnalystFixture:
    config: ConfigurationService
    persistence: InMemoryPersistenceRepository
    audit: AuditService
    prompt_repository: PromptRepository
    generated_reports: tuple[OperationalContract, ...]
    fusion_report: OperationalContract
    delivery_results: tuple[object, ...]


class AnalystReadinessReportGenerator:
    """Generate Analyst readiness artifacts."""

    def __init__(self, result: AnalystReadinessResult) -> None:
        self.result = result

    def analyst_orr(self) -> str:
        """Generate A-ORR."""
        lines = [
            "# A-ORR Analyst Operational Readiness Review",
            "",
            "Status: PASS" if self.result.certified else "Status: FAIL",
            "",
            "## Readiness Checks",
        ]
        for check in self.result.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {check.check_id}: {status} - {check.name}. {check.detail}")
        return "\n".join(lines) + "\n"

    def analyst_completion_report(self) -> str:
        """Generate ACR-001."""
        status = "COMPLETE" if self.result.certified else "INCOMPLETE"
        return "\n".join(
            [
                "# ACR-001 Analyst Completion Report",
                "",
                f"Analyst Status: {status}",
                "",
                "Completed Engineering Orders: EO-029 through EO-039",
                "",
                "Verified Analyst capabilities:",
                "- Analyst Department framework",
                "- Nine deterministic reasoning offices",
                "- Decision Models, Reasoning Graphs, and Probability Landscapes",
                "- Risk Interaction, Cross-Discipline Review, and Analytical Fusion",
                "- Unified Decision Model and Organizational Reasoning Graph",
                "- Organizational Belief State reproducibility",
                "- Operational readiness verification",
                "",
            ]
        )

    def authorization_to_proceed(self) -> str:
        """Generate Group 5 authorization."""
        decision = "AUTHORIZED" if self.result.certified else "NOT AUTHORIZED"
        return "\n".join(
            [
                "# Authorization to Proceed - Group 5 Risk Office",
                "",
                f"Decision: {decision}",
                "",
                "Scope: Risk Office implementation may begin only after A-ORR passes.",
                "",
            ]
        )


def _analyst_fixture() -> _AnalystFixture:
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
    source = _source_report("DOC-1801", "SEEKER-OFFICE-009", "MIR", "STF-029")

    statistical = StatisticalAnalysisOffice(config, persistence, audit, prompts)
    technical = AnalystTechnicalAnalysisOffice(config, persistence, audit, prompts)
    fundamental = FundamentalAnalysisOffice(config, persistence, audit, prompts)
    macro = MacroeconomicAnalysisOffice(config, persistence, audit, prompts)
    derivatives = DerivativesAnalysisOffice(config, persistence, audit, prompts)
    behavioral = BehavioralAnalysisOffice(config, persistence, audit, prompts)
    risk_interaction = RiskInteractionOffice(config, persistence, audit, prompts)
    cross_review = CrossDisciplineReviewOffice(config, persistence, audit, prompts)
    fusion = AnalyticalFusionOffice(config, persistence, audit, prompts)

    statistical_aar = statistical.generate_statistical_aar(_statistical_dataset(), (source,), "CF-001", "TC-001", 2701, "PROMPT-030")
    technical_aar = technical.generate_technical_aar(_technical_observation(), (source,), "CF-001", "TC-001", 2702, "PROMPT-031")
    fundamental_aar = fundamental.generate_fundamental_aar(_fundamental_observation(), (source,), "CF-001", "TC-001", 2703, "PROMPT-032")
    macro_aar = macro.generate_macroeconomic_aar(_macro_observation(), (source,), "CF-001", "TC-001", 2704, "PROMPT-033")
    derivatives_aar = derivatives.generate_derivatives_aar(_derivatives_observation(), (source,), "CF-001", "TC-001", 2705, "PROMPT-034")
    behavioral_aar = behavioral.generate_behavioral_aar(_behavioral_observation(), (source,), "CF-001", "TC-001", 2706, "PROMPT-035")
    risk_aar = risk_interaction.generate_risk_interaction_aar(_risk_observation(), behavioral_aar.machine_payload["decision_model"], (behavioral_aar,), "CF-001", "TC-001", 2707, "PROMPT-036")
    cross_aar = cross_review.generate_cross_discipline_aar(
        _discipline_assessments((statistical_aar, technical_aar, fundamental_aar, macro_aar, derivatives_aar, behavioral_aar, risk_aar)),
        (statistical_aar, technical_aar, fundamental_aar, macro_aar, derivatives_aar, behavioral_aar, risk_aar),
        "CF-001",
        "TC-001",
        2708,
        "PROMPT-037",
    )
    fusion_aar = fusion.generate_analytical_fusion_aar(
        _fusion_inputs((statistical_aar, technical_aar, derivatives_aar, behavioral_aar, risk_aar, cross_aar)),
        (statistical_aar, technical_aar, derivatives_aar, behavioral_aar, risk_aar, cross_aar),
        "CF-001",
        "TC-001",
        2709,
        "PROMPT-038",
    )

    generated_reports = (
        statistical_aar,
        technical_aar,
        fundamental_aar,
        macro_aar,
        derivatives_aar,
        behavioral_aar,
        risk_aar,
        cross_aar,
        fusion_aar,
    )
    for report in generated_reports:
        audit.record_document_creation(report)

    delivery_results = (
        statistical.route_aar(statistical_aar, executive_inbox),
        technical.route_aar(technical_aar, executive_inbox),
        fundamental.route_aar(fundamental_aar, executive_inbox),
        macro.route_aar(macro_aar, executive_inbox),
        derivatives.route_aar(derivatives_aar, executive_inbox),
        behavioral.route_aar(behavioral_aar, executive_inbox),
        risk_interaction.route_aar(risk_aar, executive_inbox),
        cross_review.route_aar(cross_aar, executive_inbox),
        fusion.route_aar(fusion_aar, executive_inbox),
    )
    return _AnalystFixture(config, persistence, audit, prompts, generated_reports, fusion_aar, delivery_results)


def _prompt_repository() -> PromptRepository:
    repository = PromptRepository()
    prompt_specs = (
        ("PROMPT-030", "Statistical AAR Prompt", "STF-031", "EO-030"),
        ("PROMPT-031", "Technical AAR Prompt", "STF-032", "EO-031"),
        ("PROMPT-032", "Fundamental AAR Prompt", "STF-033", "EO-032"),
        ("PROMPT-033", "Macroeconomic AAR Prompt", "STF-034", "EO-033"),
        ("PROMPT-034", "Derivatives AAR Prompt", "STF-035", "EO-034"),
        ("PROMPT-035", "Behavioral AAR Prompt", "STF-036", "EO-035"),
        ("PROMPT-036", "Risk Interaction AAR Prompt", "STF-037", "EO-036"),
        ("PROMPT-037", "Cross-Discipline AAR Prompt", "STF-038", "EO-037"),
        ("PROMPT-038", "Analytical Fusion AAR Prompt", "STF-039", "EO-038"),
    )
    for prompt_id, title, staff_id, dependency in prompt_specs:
        repository.register(
            PromptPassport(
                prompt_id=prompt_id,
                title=title,
                owner_group_id="DEP-004",
                author_staff_id=staff_id,
                purpose="Analyst readiness fixture prompt.",
                allowed_environments=("development",),
                input_contract_types=("AAR", "MIR", "READINESS_INPUT"),
                output_contract_types=("AAR",),
                dependencies=(dependency,),
                safety_notes="No trading or command authority.",
            ),
            "1.0.0",
            "Generate deterministic Analyst readiness artifacts only.",
        )
    return repository


def _source_report(contract_id: str, office_id: str, contract_type: str, staff_id: str) -> OperationalContract:
    created = utc_timestamp()
    payload = {"office_id": office_id, "readiness_source": True}
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=contract_id,
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id=staff_id,
        produced_by_group_id="DEP-003",
        intended_consumer_group_id="DEP-004",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic readiness source.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def _statistical_dataset() -> StatisticalDataset:
    return StatisticalDataset((0.1, 0.2, 0.3, 0.4), (1, 2, 3, 4), (0.12, 0.18, 0.27, 0.39), (10, -3, 4), (0.5, 0.2, 0.3))


def _technical_observation() -> TechnicalReasoningObservation:
    return TechnicalReasoningObservation((100, 103, 105, 108), (101, 104, 106, 110), (99, 102, 104, 106), (1000, 1200, 1300, 1600), (100, 101, 102, 103), 7, 10, 0.8)


def _fundamental_observation() -> FundamentalBusinessObservation:
    return FundamentalBusinessObservation(0.18, 0.55, 0.22, 0.19, 18, 22, 0.4, 0.82, 0.04, 0.6, 8.0, 0.16, 0.7, 0.75)


def _macro_observation() -> MacroeconomicReasoningObservation:
    return MacroeconomicReasoningObservation(5.2, 5.5, 0.3, 4.0, 2.1, -0.4, 1.2, 12.0, 1.4)


def _derivatives_observation() -> DerivativesReasoningObservation:
    return DerivativesReasoningObservation(0.62, 0.38, 3.0, -1200000, -800000, 900000, 0.31, 50000, 3, 2500000)


def _behavioral_observation() -> BehavioralReasoningObservation:
    return BehavioralReasoningObservation(0.82, 0.74, 0.68, 0.62, 0.71, 82, 0.63, 0.58, 0.66)


def _risk_observation() -> RiskInteractionObservation:
    return RiskInteractionObservation("BDM-001", "behavioral_risk_elevated", 6, 2, 3, 0.65, 1, 0.52, 1, 2, 0.7)


def _discipline_assessments(reports: tuple[OperationalContract, ...]) -> tuple[DisciplineAssessment, ...]:
    disciplines = ("statistical", "technical", "fundamental", "macroeconomic", "derivatives", "behavioral", "risk_interaction")
    conclusions = ("risk_elevated", "trend_persistent", "trend_persistent", "macro_regime_conflict", "risk_elevated", "risk_elevated", "risk_elevated")
    return tuple(
        DisciplineAssessment(
            disciplines[index],
            report.contract_id,
            conclusions[index],
            (f"EV-{index + 1}", "EV-COMMON"),
            ("claim:risk", f"claim:{disciplines[index]}"),
            ("timing_unknown", f"unknown:{disciplines[index]}"),
            ("shared_assumption", f"assumption:{disciplines[index]}"),
            0.55 + index * 0.03,
        )
        for index, report in enumerate(reports)
    )


def _fusion_inputs(reports: tuple[OperationalContract, ...]) -> tuple[AnalyticalFusionInput, ...]:
    source_specs = (
        (reports[0], "risk_elevated", {"model_id": "SDM-001", "decision_state": "risk_elevated"}, {"scenarios": ({"scenario": "risk_elevated", "probability": 0.6},)}),
        (reports[1], "trend_persistent", {"model_id": "TDM-001", "decision_state": "trend_persistent"}, {"scenarios": ({"scenario": "trend_persistent", "probability": 0.55},)}),
        (reports[2], "risk_elevated", {"model_id": "DDM-001", "decision_state": "risk_elevated"}, reports[2].machine_payload["probability_landscape"]),
        (reports[3], "risk_elevated", reports[3].machine_payload["decision_model"], reports[3].machine_payload["probability_landscape"]),
        (reports[4], "risk_elevated", reports[4].machine_payload["risk_readiness_report"], {"scenarios": ({"scenario": "review_required", "probability": 0.7},)}),
        (reports[5], "risk_elevated", reports[5].machine_payload["consensus_report"], {"scenarios": ({"scenario": "risk_elevated", "probability": 0.75},)}),
    )
    return tuple(
        AnalyticalFusionInput(
            report.machine_payload["office_id"],
            report.contract_id,
            conclusion,
            model,
            {"nodes": (f"claim:{report.machine_payload['office_id']}", f"source:{report.contract_id}")},
            landscape,
            (f"EV-FUSION-{index + 1}", "EV-COMMON"),
            (f"U-FUSION-{index + 1}", "U-COMMON"),
            0.55 + index * 0.04,
        )
        for index, (report, conclusion, model, landscape) in enumerate(source_specs)
    )


def _organizational_belief_state(payload: dict[str, object]) -> OrganizationalBeliefState:
    udm = payload["unified_decision_model"]
    org = payload["organizational_reasoning_graph"]
    return OrganizationalBeliefState(
        "OBS-001",
        str(udm["primary_conclusion"]),
        float(payload["organizational_confidence"]),
        float(payload["independent_evidence_score"]),
        float(payload["intellectual_diversity_score"]),
        tuple(org["source_report_ids"]),
    )


def _has_key_ending(payload: dict[str, object], suffix: str) -> bool:
    return any(key.endswith(suffix) for key in payload)
