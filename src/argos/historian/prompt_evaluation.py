"""Prompt Evaluation Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from statistics import mean
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .group import HISTORIAN_GROUP_ID


PROMPT_EVALUATION_OFFICE_ID = "HISTORIAN-OFFICE-005"
PROMPT_EVALUATION_STAFF_ID = "STF-074"


class PromptLifecycleState(str, Enum):
    """Prompt lifecycle state."""

    PROPOSAL = "proposal"
    CONTROLLED_TESTING = "controlled_testing"
    PERFORMANCE_MEASUREMENT = "performance_measurement"
    HISTORICAL_COMPARISON = "historical_comparison"
    STATISTICAL_EVALUATION = "statistical_evaluation"
    RECOMMENDATION = "recommendation"
    INSTITUTIONAL_VALIDATION = "institutional_validation"
    DOCTRINE_ADOPTION = "doctrine_adoption"
    RETIRED = "retired"


class PromptSourceType(str, Enum):
    """Prompt source type."""

    ENGINEERING_ORDER = "engineering_order"
    EXECUTIVE_DIRECTIVE = "executive_directive"
    HISTORIAN_RECOMMENDATION = "historian_recommendation"
    LIBRARIAN_DOCTRINE = "librarian_doctrine"
    HUMAN_OPERATOR = "human_operator"
    EXPERIMENTAL_RESEARCH = "experimental_research"
    PERFORMANCE_REVIEW = "performance_review"
    LEARNING_INTEGRATION = "learning_integration"


class PromptRecommendationType(str, Enum):
    """Prompt optimization recommendation."""

    PROMOTE = "promote"
    RETAIN = "retain"
    REVISE = "revise"
    RETIRE = "retire"


@dataclass(frozen=True)
class OrganizationalPrompt:
    """Prompt as an organizational asset and operational hypothesis."""

    prompt_id: str
    prompt_name: str
    version: str
    author_id: str
    source_type: PromptSourceType
    supporting_doctrine_ids: tuple[str, ...]
    supporting_specification_ids: tuple[str, ...]
    approval_history_ids: tuple[str, ...]
    retirement_history_ids: tuple[str, ...]
    created_date: str


@dataclass(frozen=True)
class PromptPerformanceObservation:
    """Empirical prompt performance observation."""

    observation_id: str
    prompt_id: str
    scenario_id: str
    accuracy: float
    consistency: float
    completeness: float
    reasoning_quality: float
    evidence_usage: float
    decision_quality: float
    latency_score: float
    determinism: float
    reproducibility: float
    human_evaluation: float
    organizational_impact: float
    audit_record_id: str


@dataclass(frozen=True)
class PromptVersionRecord:
    """Prompt version history record."""

    version_record_id: str
    prompt: OrganizationalPrompt
    lifecycle_state: PromptLifecycleState
    parent_version_id: str | None
    immutable: bool


@dataclass(frozen=True)
class PromptQualityMetrics:
    """Deterministic prompt quality metrics."""

    metrics_id: str
    prompt_id: str
    accuracy: float
    consistency: float
    completeness: float
    reasoning_quality: float
    evidence_usage: float
    decision_quality: float
    latency_score: float
    determinism: float
    reproducibility: float
    human_evaluation: float
    organizational_impact: float
    prompt_effectiveness_index: float
    sample_size: int


@dataclass(frozen=True)
class PromptExperimentResult:
    """Prompt experimentation result."""

    experiment_id: str
    prompt_id: str
    experiment_types: tuple[str, ...]
    scenario_ids: tuple[str, ...]
    deterministic: bool
    anecdotal_observations_used: bool


@dataclass(frozen=True)
class PromptBenchmarkRecord:
    """Prompt benchmark and historical comparison."""

    benchmark_id: str
    prompt_id: str
    current_effectiveness_index: float
    historical_baseline_index: float
    production_baseline_index: float
    human_baseline_index: float
    historical_improvement: float
    production_improvement: float
    human_improvement: float


@dataclass(frozen=True)
class PromptValidationRecord:
    """Production prompt validation."""

    validation_id: str
    prompt_id: str
    determinism_verified: bool
    historical_improvement_verified: bool
    evidence_usage_verified: bool
    organizational_alignment_verified: bool
    safety_verified: bool
    reproducibility_verified: bool
    statistical_significance_verified: bool
    executive_approval_verified: bool
    production_validated: bool


@dataclass(frozen=True)
class PromptOptimizationRecommendation:
    """Evidence-driven prompt optimization recommendation."""

    recommendation_id: str
    prompt_id: str
    recommendation_type: PromptRecommendationType
    evidence_based: bool
    recommended_action: str
    directly_modifies_prompt: bool


@dataclass(frozen=True)
class PromptPerformanceReport:
    """Prompt performance report."""

    report_id: str
    prompt_id: str
    metrics: PromptQualityMetrics
    benchmark: PromptBenchmarkRecord
    validation: PromptValidationRecord
    recommendation: PromptOptimizationRecommendation


@dataclass(frozen=True)
class EnterprisePromptAnalytics:
    """Enterprise prompt analytics dashboard metrics."""

    analytics_id: str
    production_prompts: int
    experimental_prompts: int
    prompt_success_rate: float
    average_prompt_quality: float
    historical_improvement: float
    prompt_stability: float
    regression_rate: float
    evidence_coverage: float
    prompt_effectiveness_index: float


@dataclass(frozen=True)
class PromptEvaluationStandards:
    """Librarian deliverable for prompt evaluation methodology."""

    standards_id: str
    performance_methodology: str
    experimentation_methodology: str
    validation_methodology: str
    doctrine_rule: str


class PromptEvaluationOffice:
    """Scientific prompt effectiveness evaluation authority."""

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
        self._versions: dict[str, PromptVersionRecord] = {}
        self._evidence_repository: list[dict[str, object]] = []

    @property
    def prompt_version_history(self) -> tuple[PromptVersionRecord, ...]:
        """Return immutable prompt version history."""
        return tuple(self._versions[key] for key in sorted(self._versions))

    @property
    def prompt_evidence_repository(self) -> tuple[dict[str, object], ...]:
        """Return preserved prompt evidence repository."""
        return tuple(self._evidence_repository)

    def standards(self) -> PromptEvaluationStandards:
        """Return Prompt Evaluation standards for Librarian consumption."""
        return PromptEvaluationStandards(
            "PES-065",
            "Prompt quality is the deterministic mean of accuracy, consistency, completeness, reasoning, evidence, decision quality, latency, determinism, reproducibility, human evaluation, and organizational impact.",
            "A/B testing, historical replay, cross-model comparison, scenario testing, regression testing, longitudinal evaluation, and stress testing are preserved as experiment types.",
            "Production validation requires determinism, historical improvement, evidence usage, organizational alignment, safety, reproducibility, statistical significance, and Executive approval.",
            "No prompt shall become organizational doctrine without empirical validation.",
        )

    def register_prompt(
        self,
        prompt: OrganizationalPrompt,
        parent_version_id: str | None,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Register a prompt version for scientific evaluation."""
        self.configuration_service.validate_startup()
        version_key = f"{prompt.prompt_id}:{prompt.version}"
        if version_key in self._versions:
            raise ValueError(f"prompt version already registered: {version_key}")
        record = PromptVersionRecord(
            f"PVR-{hashlib.sha256(version_key.encode('utf-8')).hexdigest()[:8].upper()}",
            prompt,
            PromptLifecycleState.PROPOSAL,
            parent_version_id,
            True,
        )
        self._versions[version_key] = record
        return self._persist_contract(
            "PROMPT_VERSION_HISTORY",
            case_file_id,
            trade_cycle_id,
            document_sequence,
            "Prompt Version History.",
            {
                "prompt_version_record": record,
                "prompt_traceability": _traceability(prompt),
                "prompt_versions_overwritten": False,
            },
        )

    def evaluate_prompt(
        self,
        prompt_id: str,
        version: str,
        observations: tuple[PromptPerformanceObservation, ...],
        historical_baseline_index: float,
        production_baseline_index: float,
        human_baseline_index: float,
        executive_approval_id: str | None,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Evaluate prompt performance from empirical observations."""
        self.configuration_service.validate_startup()
        version_key = f"{prompt_id}:{version}"
        if version_key not in self._versions:
            raise ValueError(f"unknown prompt version: {version_key}")
        if not observations:
            raise ValueError("prompt evaluation requires observations")
        if any(item.prompt_id != prompt_id for item in observations):
            raise ValueError("all observations must match evaluated prompt")
        prompt_version = self._versions[version_key]
        metrics = _metrics(prompt_id, observations)
        experiment = _experiment(prompt_id, observations)
        benchmark = _benchmark(prompt_id, metrics, historical_baseline_index, production_baseline_index, human_baseline_index)
        validation = _validation(prompt_version.prompt, metrics, benchmark, executive_approval_id)
        recommendation = _recommendation(prompt_id, metrics, benchmark, validation)
        performance_report = PromptPerformanceReport(
            f"PPR-{hashlib.sha256(f'{prompt_id}:{version}:{metrics.metrics_id}'.encode('utf-8')).hexdigest()[:8].upper()}",
            prompt_id,
            metrics,
            benchmark,
            validation,
            recommendation,
        )
        lifecycle_state = PromptLifecycleState.INSTITUTIONAL_VALIDATION if validation.production_validated else PromptLifecycleState.RECOMMENDATION
        updated_version = PromptVersionRecord(
            prompt_version.version_record_id,
            prompt_version.prompt,
            lifecycle_state,
            prompt_version.parent_version_id,
            True,
        )
        self._versions[version_key] = updated_version
        self._evidence_repository.append(
            _json_ready(
                {
                    "prompt_id": prompt_id,
                    "version": version,
                    "observation_ids": tuple(item.observation_id for item in observations),
                    "metrics_id": metrics.metrics_id,
                    "validation_id": validation.validation_id,
                    "recommendation_id": recommendation.recommendation_id,
                }
            )
        )
        analytics = EnterprisePromptAnalytics(
            f"EPA-{document_sequence:06d}",
            1 if validation.production_validated else 0,
            0 if validation.production_validated else 1,
            1.0 if validation.production_validated else 0.0,
            metrics.prompt_effectiveness_index,
            benchmark.historical_improvement,
            metrics.determinism,
            1.0 if benchmark.historical_improvement < 0 else 0.0,
            metrics.evidence_usage,
            metrics.prompt_effectiveness_index,
        )
        return {
            "prompt_evaluation_report": self._persist_contract(
                "PROMPT_EVALUATION_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Prompt Evaluation Report.",
                {
                    "office_id": PROMPT_EVALUATION_OFFICE_ID,
                    "office_name": "Prompt Evaluation Office",
                    "prompt_performance_report": performance_report,
                    "prompt_version_record": updated_version,
                    "prompt_evaluation_standards": self.standards(),
                },
            ),
            "prompt_experiment_report": self._persist_contract(
                "PROMPT_EXPERIMENT_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Prompt Experiment Report.",
                {"prompt_experiment_result": experiment, "anecdotal_observations_used": False},
            ),
            "prompt_benchmark_report": self._persist_contract(
                "PROMPT_BENCHMARK_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Prompt Benchmark Report.",
                {"prompt_benchmark_record": benchmark, "historical_comparison_complete": True},
            ),
            "prompt_optimization_recommendation": self._persist_contract(
                "PROMPT_OPTIMIZATION_RECOMMENDATION",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Prompt Optimization Recommendation.",
                {"prompt_optimization_recommendation": recommendation, "directly_modifies_prompt": False},
            ),
            "enterprise_prompt_analytics": self._persist_contract(
                "ENTERPRISE_PROMPT_ANALYTICS",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Enterprise Prompt Analytics.",
                {"enterprise_prompt_analytics": analytics, "prompt_evidence_repository": self.prompt_evidence_repository},
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


def _traceability(prompt: OrganizationalPrompt) -> dict[str, object]:
    return {
        "prompt_identifier": prompt.prompt_id,
        "version": prompt.version,
        "author": prompt.author_id,
        "date": prompt.created_date,
        "supporting_doctrine": prompt.supporting_doctrine_ids,
        "supporting_specifications": prompt.supporting_specification_ids,
        "approval_history": prompt.approval_history_ids,
        "retirement_history": prompt.retirement_history_ids,
    }


def _metrics(prompt_id: str, observations: tuple[PromptPerformanceObservation, ...]) -> PromptQualityMetrics:
    values = {
        "accuracy": _avg(tuple(item.accuracy for item in observations)),
        "consistency": _avg(tuple(item.consistency for item in observations)),
        "completeness": _avg(tuple(item.completeness for item in observations)),
        "reasoning_quality": _avg(tuple(item.reasoning_quality for item in observations)),
        "evidence_usage": _avg(tuple(item.evidence_usage for item in observations)),
        "decision_quality": _avg(tuple(item.decision_quality for item in observations)),
        "latency_score": _avg(tuple(item.latency_score for item in observations)),
        "determinism": _avg(tuple(item.determinism for item in observations)),
        "reproducibility": _avg(tuple(item.reproducibility for item in observations)),
        "human_evaluation": _avg(tuple(item.human_evaluation for item in observations)),
        "organizational_impact": _avg(tuple(item.organizational_impact for item in observations)),
    }
    index = _avg(tuple(values.values()))
    return PromptQualityMetrics(
        f"PQM-{hashlib.sha256(f'{prompt_id}:{tuple(item.observation_id for item in observations)}'.encode('utf-8')).hexdigest()[:8].upper()}",
        prompt_id,
        values["accuracy"],
        values["consistency"],
        values["completeness"],
        values["reasoning_quality"],
        values["evidence_usage"],
        values["decision_quality"],
        values["latency_score"],
        values["determinism"],
        values["reproducibility"],
        values["human_evaluation"],
        values["organizational_impact"],
        index,
        len(observations),
    )


def _experiment(prompt_id: str, observations: tuple[PromptPerformanceObservation, ...]) -> PromptExperimentResult:
    return PromptExperimentResult(
        f"PER-{hashlib.sha256(f'{prompt_id}:experiment'.encode('utf-8')).hexdigest()[:8].upper()}",
        prompt_id,
        (
            "A/B Prompt Testing",
            "Historical Replay",
            "Cross-Model Comparison",
            "Scenario Testing",
            "Regression Testing",
            "Longitudinal Evaluation",
            "Prompt Stress Testing",
        ),
        tuple(sorted(item.scenario_id for item in observations)),
        True,
        False,
    )


def _benchmark(
    prompt_id: str,
    metrics: PromptQualityMetrics,
    historical_baseline_index: float,
    production_baseline_index: float,
    human_baseline_index: float,
) -> PromptBenchmarkRecord:
    return PromptBenchmarkRecord(
        f"PBR-{hashlib.sha256(f'{prompt_id}:benchmark'.encode('utf-8')).hexdigest()[:8].upper()}",
        prompt_id,
        metrics.prompt_effectiveness_index,
        historical_baseline_index,
        production_baseline_index,
        human_baseline_index,
        round(metrics.prompt_effectiveness_index - historical_baseline_index, 6),
        round(metrics.prompt_effectiveness_index - production_baseline_index, 6),
        round(metrics.prompt_effectiveness_index - human_baseline_index, 6),
    )


def _validation(
    prompt: OrganizationalPrompt,
    metrics: PromptQualityMetrics,
    benchmark: PromptBenchmarkRecord,
    executive_approval_id: str | None,
) -> PromptValidationRecord:
    determinism = metrics.determinism >= 0.95
    improvement = benchmark.historical_improvement > 0
    evidence = metrics.evidence_usage >= 0.85
    alignment = bool(prompt.supporting_doctrine_ids and prompt.supporting_specification_ids)
    safety = metrics.reasoning_quality >= 0.80 and metrics.completeness >= 0.80
    reproducibility = metrics.reproducibility >= 0.95
    significance = metrics.sample_size >= 2 and metrics.prompt_effectiveness_index >= 0.80
    approval = executive_approval_id is not None or bool(prompt.approval_history_ids)
    return PromptValidationRecord(
        f"PVL-{hashlib.sha256(f'{prompt.prompt_id}:{prompt.version}'.encode('utf-8')).hexdigest()[:8].upper()}",
        prompt.prompt_id,
        determinism,
        improvement,
        evidence,
        alignment,
        safety,
        reproducibility,
        significance,
        approval,
        determinism and improvement and evidence and alignment and safety and reproducibility and significance and approval,
    )


def _recommendation(
    prompt_id: str,
    metrics: PromptQualityMetrics,
    benchmark: PromptBenchmarkRecord,
    validation: PromptValidationRecord,
) -> PromptOptimizationRecommendation:
    if validation.production_validated:
        recommendation_type = PromptRecommendationType.PROMOTE
        action = "Promote prompt for institutional validation; preserve empirical evidence package."
    elif benchmark.historical_improvement < 0:
        recommendation_type = PromptRecommendationType.RETIRE
        action = "Retire or roll back prompt candidate due to historical regression."
    elif metrics.evidence_usage < 0.85 or metrics.reasoning_quality < 0.80:
        recommendation_type = PromptRecommendationType.REVISE
        action = "Revise prompt to strengthen evidence usage and reasoning quality."
    else:
        recommendation_type = PromptRecommendationType.RETAIN
        action = "Retain prompt in controlled testing until validation gates are complete."
    return PromptOptimizationRecommendation(
        f"POR-{hashlib.sha256(f'{prompt_id}:{recommendation_type.value}'.encode('utf-8')).hexdigest()[:8].upper()}",
        prompt_id,
        recommendation_type,
        True,
        action,
        False,
    )


def _avg(values: tuple[float, ...]) -> float:
    return round(mean(values), 6) if values else 0.0


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
        produced_by_staff_id=PROMPT_EVALUATION_STAFF_ID,
        produced_by_group_id=HISTORIAN_GROUP_ID,
        intended_consumer_group_id=HISTORIAN_GROUP_ID,
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
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
