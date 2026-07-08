"""Case Study Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .framework import ACADEMY_GROUP_ID, CompetencyDomain, LearnerLevel


CASE_STUDY_OFFICE_ID = "ACADEMY-OFFICE-004"
CASE_STUDY_STAFF_ID = "STF-091"


class CasePerspective(str, Enum):
    """Case study perspective."""

    EXECUTIVE = "executive"
    SEEKER = "seeker"
    ANALYST = "analyst"
    RISK = "risk"
    TRADER = "trader"
    HISTORIAN = "historian"


class CaseComplexity(str, Enum):
    """Case complexity."""

    FOUNDATION = "foundation"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass(frozen=True)
class HistoricalEvidencePacket:
    """Information available at the simulated decision time."""

    evidence_id: str
    source_type: str
    available_timestamp_utc: str
    summary: str
    outcome_revealing: bool


@dataclass(frozen=True)
class CaseStudyArchitecture:
    """Case study architecture."""

    architecture_id: str
    immersive: bool
    pre_outcome_reconstruction_required: bool
    evidence_traceability_required: bool
    deterministic_principles: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalReconstructionFramework:
    """Historical reconstruction framework."""

    reconstruction_id: str
    case_study_id: str
    event_name: str
    decision_timestamp_utc: str
    available_evidence_ids: tuple[str, ...]
    excluded_outcome_evidence_ids: tuple[str, ...]
    historically_accurate: bool


@dataclass(frozen=True)
class PerspectiveAnalysis:
    """Single perspective analysis standard."""

    perspective_id: str
    perspective: CasePerspective
    evidence_ids: tuple[str, ...]
    likely_questions: tuple[str, ...]
    blind_spots: tuple[str, ...]


@dataclass(frozen=True)
class MultiPerspectiveAnalysisStandard:
    """Multi-perspective analysis framework."""

    standard_id: str
    case_study_id: str
    perspectives: tuple[PerspectiveAnalysis, ...]
    balanced: bool


@dataclass(frozen=True)
class DecisionSimulationFramework:
    """Decision simulation process."""

    simulation_id: str
    case_study_id: str
    prompt_questions: tuple[str, ...]
    required_reasoning_steps: tuple[str, ...]
    outcome_hidden_until_submission: bool
    assessed_competencies: tuple[CompetencyDomain, ...]


@dataclass(frozen=True)
class AlternativeHistoryScenario:
    """Alternative history scenario."""

    scenario_id: str
    case_study_id: str
    changed_assumption: str
    plausible_outcome: str
    supporting_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PersonalizedCaseSelection:
    """Personalized case selection engine result."""

    selection_id: str
    learner_id: str
    selected_case_study_ids: tuple[str, ...]
    selection_basis: tuple[str, ...]
    learner_level: LearnerLevel


@dataclass(frozen=True)
class CaseValidationStandard:
    """Case validation process."""

    validation_id: str
    case_study_id: str
    traceability_complete: bool
    no_outcome_leakage: bool
    multi_perspective_complete: bool
    validation_errors: tuple[str, ...]
    valid: bool


@dataclass(frozen=True)
class CaseEducationalAnalyticsFramework:
    """Educational analytics framework."""

    analytics_id: str
    case_study_id: str
    learner_id: str
    evidence_evaluation_score: float
    risk_assessment_score: float
    reasoning_quality_score: float
    decision_justification_score: float
    learning_value_score: float


@dataclass(frozen=True)
class CaseStudyDashboard:
    """Case Study Office dashboard."""

    dashboard_id: str
    case_study_count: int
    evidence_packet_count: int
    perspective_count: int
    selected_case_count: int
    validation_ready: bool
    average_learning_value: float
    case_study_health: str


@dataclass(frozen=True)
class CaseStudySystemPrompt:
    """Case Study Office prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class CaseStudyOffice:
    """Experiential learning engine for historical financial decisions."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.prompt_repository = prompt_repository

    def system_prompt(self) -> CaseStudySystemPrompt:
        """Return governing Case Study Office prompt."""
        return CaseStudySystemPrompt(
            "PROMPT-CASE-STUDY-082",
            "1.0.0",
            (
                "You are the Case Study Office of the ARGOS Academy.\n\n"
                "Create immersive educational experiences from historical financial events, investment decisions, "
                "market environments, and organizational learning. Reconstruct authentic decision environments using "
                "only the information available at the time, requiring students to evaluate evidence, assess risk, "
                "and justify their reasoning before historical outcomes are revealed."
            ),
        )

    def create_case_study(
        self,
        case_study_id: str,
        learner_id: str,
        learner_level: LearnerLevel,
        event_name: str,
        decision_timestamp_utc: str,
        evidence_packets: tuple[HistoricalEvidencePacket, ...],
        targeted_competencies: tuple[CompetencyDomain, ...],
        analytics_scores: tuple[float, float, float, float],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Create a deterministic historical case study experience."""
        self.configuration_service.validate_startup()
        ordered_evidence = tuple(sorted(evidence_packets, key=lambda item: item.evidence_id))
        included = tuple(item for item in ordered_evidence if not item.outcome_revealing and item.available_timestamp_utc <= decision_timestamp_utc)
        excluded = tuple(item for item in ordered_evidence if item.outcome_revealing or item.available_timestamp_utc > decision_timestamp_utc)
        architecture = CaseStudyArchitecture(
            f"CSA-{document_sequence:06d}",
            True,
            True,
            True,
            (
                "Use only information available at the decision timestamp.",
                "Hide outcomes until the student submits reasoning.",
                "Preserve balanced perspectives and evidence lineage.",
                "Validate every case before educational use.",
            ),
        )
        reconstruction = HistoricalReconstructionFramework(
            f"HRF-{document_sequence:06d}",
            case_study_id,
            event_name,
            decision_timestamp_utc,
            tuple(item.evidence_id for item in included),
            tuple(item.evidence_id for item in excluded),
            bool(included),
        )
        perspectives = _perspectives(case_study_id, included, targeted_competencies, document_sequence)
        simulation = DecisionSimulationFramework(
            f"DSF-{document_sequence:06d}",
            case_study_id,
            (
                "What evidence supports the decision thesis?",
                "What risks could invalidate the decision?",
                "What alternative explanation remains plausible?",
                "What action would be justified from only the available information?",
            ),
            (
                "Separate known evidence from assumptions.",
                "Assess risk before choosing an action.",
                "Document confidence and uncertainty.",
                "Justify the decision before outcome reveal.",
            ),
            True,
            tuple(sorted(targeted_competencies, key=lambda item: item.value)),
        )
        alternatives = _alternatives(case_study_id, included, document_sequence)
        selection = PersonalizedCaseSelection(
            f"PCS-{document_sequence:06d}",
            learner_id,
            (case_study_id,),
            (
                f"learner_level={learner_level.value}",
                f"targeted_competencies={','.join(domain.value for domain in sorted(targeted_competencies, key=lambda item: item.value))}",
            ),
            learner_level,
        )
        validation = _validation(case_study_id, included, excluded, perspectives, document_sequence)
        analytics = CaseEducationalAnalyticsFramework(
            f"CEAF-{document_sequence:06d}",
            case_study_id,
            learner_id,
            analytics_scores[0],
            analytics_scores[1],
            analytics_scores[2],
            analytics_scores[3],
            round(sum(analytics_scores) / len(analytics_scores), 4),
        )
        dashboard = CaseStudyDashboard(
            f"CSDASH-{document_sequence:06d}",
            1,
            len(included),
            len(perspectives.perspectives),
            len(selection.selected_case_study_ids),
            validation.valid,
            analytics.learning_value_score,
            "healthy" if validation.valid and analytics.learning_value_score >= 0.70 else "attention",
        )
        return {
            "case_study_architecture": self._persist_contract(
                "CASE_STUDY_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Case Study Architecture.",
                {"case_study_architecture": architecture, "case_study_system_prompt": self.system_prompt()},
            ),
            "historical_reconstruction_framework": self._persist_contract(
                "HISTORICAL_RECONSTRUCTION_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Historical Reconstruction Framework.",
                {"historical_reconstruction_framework": reconstruction, "available_evidence_packets": included},
            ),
            "decision_simulation_framework": self._persist_contract(
                "DECISION_SIMULATION_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Decision Simulation Framework.",
                {"decision_simulation_framework": simulation, "alternative_history_scenarios": alternatives},
            ),
            "multi_perspective_analysis_standard": self._persist_contract(
                "MULTI_PERSPECTIVE_ANALYSIS_STANDARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Multi-Perspective Analysis Standard.",
                {"multi_perspective_analysis_standard": perspectives},
            ),
            "personalized_case_selection_engine": self._persist_contract(
                "PERSONALIZED_CASE_SELECTION_ENGINE",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Personalized Case Selection Engine.",
                {"personalized_case_selection": selection},
            ),
            "case_study_dashboard": self._persist_contract(
                "CASE_STUDY_DASHBOARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Case Study Dashboard.",
                {"case_validation_standard": validation, "educational_analytics_framework": analytics, "case_study_dashboard": dashboard},
            ),
        }

    def _persist_contract(
        self,
        contract_type: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        human_summary: str,
        payload: dict[str, Any],
    ) -> OperationalContract:
        contract = _contract(contract_type, case_file_id, trade_cycle_id, document_sequence, human_summary, payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract


def _perspectives(
    case_study_id: str,
    evidence_packets: tuple[HistoricalEvidencePacket, ...],
    targeted_competencies: tuple[CompetencyDomain, ...],
    document_sequence: int,
) -> MultiPerspectiveAnalysisStandard:
    evidence_ids = tuple(item.evidence_id for item in evidence_packets)
    perspectives = tuple(
        PerspectiveAnalysis(
            f"PA-{document_sequence:06d}-{index:03d}",
            perspective,
            evidence_ids,
            (f"What would the {perspective.value} perspective emphasize?",),
            tuple(f"May underweight {domain.value.replace('_', ' ')}" for domain in targeted_competencies[:2]),
        )
        for index, perspective in enumerate((CasePerspective.EXECUTIVE, CasePerspective.ANALYST, CasePerspective.RISK, CasePerspective.HISTORIAN), start=1)
    )
    return MultiPerspectiveAnalysisStandard(
        f"MPAS-{document_sequence:06d}",
        case_study_id,
        perspectives,
        len(perspectives) >= 3 and bool(evidence_ids),
    )


def _alternatives(
    case_study_id: str,
    evidence_packets: tuple[HistoricalEvidencePacket, ...],
    document_sequence: int,
) -> tuple[AlternativeHistoryScenario, ...]:
    evidence_ids = tuple(item.evidence_id for item in evidence_packets)
    return (
        AlternativeHistoryScenario(
            f"AHS-{document_sequence:06d}-001",
            case_study_id,
            "Liquidity conditions deteriorate faster than expected.",
            "The decision fails despite apparently supportive evidence.",
            evidence_ids,
        ),
        AlternativeHistoryScenario(
            f"AHS-{document_sequence:06d}-002",
            case_study_id,
            "Risk evidence receives greater weight than momentum evidence.",
            "The organization defers action and preserves optionality.",
            evidence_ids,
        ),
    )


def _validation(
    case_study_id: str,
    included: tuple[HistoricalEvidencePacket, ...],
    excluded: tuple[HistoricalEvidencePacket, ...],
    perspectives: MultiPerspectiveAnalysisStandard,
    document_sequence: int,
) -> CaseValidationStandard:
    errors = []
    if not included:
        errors.append("missing_pre_outcome_evidence")
    if any(item.outcome_revealing for item in included):
        errors.append("outcome_leakage")
    if not perspectives.balanced:
        errors.append("insufficient_perspective_balance")
    return CaseValidationStandard(
        f"CVS-{document_sequence:06d}",
        case_study_id,
        bool(included),
        not any(item.outcome_revealing for item in included),
        perspectives.balanced,
        tuple(sorted(errors)),
        not errors,
    )


def _contract(
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    document_sequence: int,
    human_summary: str,
    payload: dict[str, Any],
) -> OperationalContract:
    created = utc_timestamp()
    normalized_payload = _json_ready(payload)
    signature_hash = hashlib.sha256(json.dumps(normalized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        parent_contract_ids=(),
        produced_by_staff_id=CASE_STUDY_STAFF_ID,
        produced_by_group_id=ACADEMY_GROUP_ID,
        intended_consumer_group_id=ACADEMY_GROUP_ID,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=human_summary,
        machine_payload=normalized_payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {_json_ready(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
