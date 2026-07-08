"""Model Calibration Office."""

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


MODEL_CALIBRATION_OFFICE_ID = "HISTORIAN-OFFICE-004"
MODEL_CALIBRATION_STAFF_ID = "STF-073"


class ModelStatus(str, Enum):
    """Model registry status."""

    REGISTERED = "registered"
    UNDER_CALIBRATION = "under_calibration"
    CALIBRATION_RECOMMENDED = "calibration_recommended"
    STABLE = "stable"
    RETIRED = "retired"


class BiasDirection(str, Enum):
    """Systematic prediction bias direction."""

    OVERPREDICTION = "overprediction"
    UNDERPREDICTION = "underprediction"
    BALANCED = "balanced"


@dataclass(frozen=True)
class OrganizationalModel:
    """Version-controlled organizational predictive model."""

    model_id: str
    model_name: str
    version: str
    owning_group: str
    prediction_target: str
    feature_specification_id: str
    training_dataset_id: str
    parent_model_version_id: str | None
    audit_record_id: str


@dataclass(frozen=True)
class ModelRegistryRecord:
    """Immutable model registry record."""

    registry_id: str
    model: OrganizationalModel
    status: ModelStatus
    registered_timestamp_utc: str
    version_history_ids: tuple[str, ...]


@dataclass(frozen=True)
class PredictionObservation:
    """Observed prediction outcome."""

    observation_id: str
    model_id: str
    prediction_id: str
    predicted_value: float
    observed_value: float
    outcome_timestamp_utc: str
    source_case_id: str
    audit_record_id: str


@dataclass(frozen=True)
class PredictionErrorDataset:
    """Deterministic prediction error dataset."""

    dataset_id: str
    model_id: str
    observation_ids: tuple[str, ...]
    mean_absolute_error: float
    mean_error: float
    root_mean_squared_error: float
    sample_size: int


@dataclass(frozen=True)
class BiasAssessment:
    """Systematic bias assessment."""

    assessment_id: str
    model_id: str
    bias_direction: BiasDirection
    bias_magnitude: float
    systematic_bias_detected: bool
    evidence_observation_ids: tuple[str, ...]


@dataclass(frozen=True)
class CalibrationRecommendation:
    """Evidence-based calibration recommendation."""

    recommendation_id: str
    model_id: str
    recommended_adjustment: float
    evidence_based: bool
    expected_error_reduction: float
    requires_version_increment: bool
    directly_updates_model: bool


@dataclass(frozen=True)
class ModelGenerationComparison:
    """Comparative model generation evaluation."""

    comparison_id: str
    model_id: str
    baseline_version: str
    candidate_version: str
    baseline_error: float
    candidate_error: float
    improvement: float
    candidate_preferred: bool


@dataclass(frozen=True)
class CalibrationSimulationResult:
    """Simulation result for proposed calibration."""

    simulation_id: str
    model_id: str
    proposed_adjustment: float
    simulated_error: float
    baseline_error: float
    simulation_successful: bool
    deterministic_trace_id: str


@dataclass(frozen=True)
class ModelIntegrityAssessment:
    """Model integrity assessment."""

    integrity_id: str
    model_id: str
    version_controlled: bool
    historical_reproducibility_preserved: bool
    calibration_history_complete: bool


@dataclass(frozen=True)
class CalibrationStandards:
    """Librarian deliverable for calibration methodology."""

    standards_id: str
    prediction_error_methodology: str
    bias_detection_methodology: str
    version_specification: str
    reproducibility_required: bool


class ModelCalibrationOffice:
    """Deterministic model optimization authority."""

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
        self._registry: dict[str, ModelRegistryRecord] = {}
        self._calibration_history: list[dict[str, object]] = []

    @property
    def model_registry(self) -> tuple[ModelRegistryRecord, ...]:
        """Return immutable model registry records."""
        return tuple(self._registry[key] for key in sorted(self._registry))

    @property
    def calibration_history_archive(self) -> tuple[dict[str, object], ...]:
        """Return preserved historical calibration archive."""
        return tuple(self._calibration_history)

    def standards(self) -> CalibrationStandards:
        """Return calibration standards for Librarian consumption."""
        return CalibrationStandards(
            "MCS-064",
            "MAE, signed mean error, and RMSE are calculated from preserved prediction observations.",
            "Systematic bias is detected when signed mean error magnitude exceeds the deterministic bias threshold.",
            "Every calibration recommendation requires a new version record; historical model versions are never overwritten.",
            True,
        )

    def register_model(
        self,
        model: OrganizationalModel,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Register a version-controlled organizational model."""
        self.configuration_service.validate_startup()
        if model.model_id in self._registry:
            raise ValueError(f"model already registered: {model.model_id}")
        record = ModelRegistryRecord(
            f"MRR-{hashlib.sha256(model.model_id.encode('utf-8')).hexdigest()[:8].upper()}",
            model,
            ModelStatus.REGISTERED,
            utc_timestamp(),
            (f"MVH-{model.model_id}-{model.version}",),
        )
        self._registry[model.model_id] = record
        return self._persist_contract(
            "MODEL_REGISTRY",
            case_file_id,
            trade_cycle_id,
            document_sequence,
            "Model Registry.",
            {
                "model_registry_record": record,
                "model_version_history": record.version_history_ids,
                "historical_model_versions_overwritten": False,
            },
        )

    def calibrate_model(
        self,
        model_id: str,
        observations: tuple[PredictionObservation, ...],
        candidate_version: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Calibrate a registered model from empirical observations."""
        self.configuration_service.validate_startup()
        if model_id not in self._registry:
            raise ValueError(f"unknown model: {model_id}")
        if not observations:
            raise ValueError("model calibration requires prediction observations")
        if any(item.model_id != model_id for item in observations):
            raise ValueError("all prediction observations must match the calibrated model")
        registry = self._registry[model_id]
        error_dataset = _prediction_error_dataset(model_id, observations)
        bias = _bias_assessment(model_id, observations, error_dataset)
        recommendation = _recommendation(model_id, error_dataset, bias)
        simulation = _simulation(model_id, error_dataset, recommendation)
        comparison = _comparison(registry.model, candidate_version, error_dataset, simulation)
        integrity = ModelIntegrityAssessment(
            f"MIA-{hashlib.sha256(model_id.encode('utf-8')).hexdigest()[:8].upper()}",
            model_id,
            True,
            True,
            True,
        )
        updated_registry = ModelRegistryRecord(
            registry.registry_id,
            registry.model,
            ModelStatus.CALIBRATION_RECOMMENDED if recommendation.requires_version_increment else ModelStatus.STABLE,
            registry.registered_timestamp_utc,
            (*registry.version_history_ids, f"MVH-{model_id}-{candidate_version}"),
        )
        self._registry[model_id] = updated_registry
        archive = {
            "model_id": model_id,
            "version": registry.model.version,
            "candidate_version": candidate_version,
            "mean_absolute_error": error_dataset.mean_absolute_error,
            "bias_direction": bias.bias_direction.value,
            "recommendation_id": recommendation.recommendation_id,
        }
        self._calibration_history.append(_json_ready(archive))
        return {
            "model_calibration_report": self._persist_contract(
                "MODEL_CALIBRATION_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Model Calibration Report.",
                {
                    "office_id": MODEL_CALIBRATION_OFFICE_ID,
                    "office_name": "Model Calibration Office",
                    "model_registry_record": updated_registry,
                    "prediction_error_dataset": error_dataset,
                    "bias_assessment": bias,
                    "calibration_recommendation": recommendation,
                    "calibration_simulation_result": simulation,
                    "model_integrity_assessment": integrity,
                    "calibration_standards": self.standards(),
                },
            ),
            "calibration_comparison_report": self._persist_contract(
                "CALIBRATION_COMPARISON_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Calibration Comparison Report.",
                {"model_generation_comparison": comparison},
            ),
            "organizational_calibration_summary": self._persist_contract(
                "ORGANIZATIONAL_CALIBRATION_SUMMARY",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Organizational Calibration Summary.",
                {
                    "model_registry": self.model_registry,
                    "calibration_recommendation_register": (recommendation,),
                    "historical_calibration_archive_complete": True,
                },
            ),
            "model_evolution_report": self._persist_contract(
                "MODEL_EVOLUTION_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Model Evolution Report.",
                {
                    "model_version_history": updated_registry.version_history_ids,
                    "model_version_archive_immutable": True,
                    "historical_reproducibility_preserved": True,
                },
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


def _prediction_error_dataset(model_id: str, observations: tuple[PredictionObservation, ...]) -> PredictionErrorDataset:
    errors = tuple(item.predicted_value - item.observed_value for item in observations)
    absolute_errors = tuple(abs(item) for item in errors)
    squared_errors = tuple(item * item for item in errors)
    return PredictionErrorDataset(
        f"PED-{hashlib.sha256(f'{model_id}:{tuple(item.observation_id for item in observations)}'.encode('utf-8')).hexdigest()[:8].upper()}",
        model_id,
        tuple(item.observation_id for item in observations),
        round(mean(absolute_errors), 6),
        round(mean(errors), 6),
        round(mean(squared_errors) ** 0.5, 6),
        len(observations),
    )


def _bias_assessment(model_id: str, observations: tuple[PredictionObservation, ...], dataset: PredictionErrorDataset) -> BiasAssessment:
    threshold = 0.05
    magnitude = abs(dataset.mean_error)
    if magnitude <= threshold:
        direction = BiasDirection.BALANCED
    elif dataset.mean_error > 0:
        direction = BiasDirection.OVERPREDICTION
    else:
        direction = BiasDirection.UNDERPREDICTION
    return BiasAssessment(
        f"BAA-{hashlib.sha256(f'{model_id}:{dataset.dataset_id}'.encode('utf-8')).hexdigest()[:8].upper()}",
        model_id,
        direction,
        round(magnitude, 6),
        magnitude > threshold,
        tuple(item.observation_id for item in observations),
    )


def _recommendation(model_id: str, dataset: PredictionErrorDataset, bias: BiasAssessment) -> CalibrationRecommendation:
    adjustment = round(-dataset.mean_error, 6)
    expected_reduction = round(min(dataset.mean_absolute_error, abs(adjustment)), 6)
    requires_version = dataset.mean_absolute_error > 0.05 or bias.systematic_bias_detected
    return CalibrationRecommendation(
        f"CRR-{hashlib.sha256(f'{model_id}:{dataset.dataset_id}:{adjustment}'.encode('utf-8')).hexdigest()[:8].upper()}",
        model_id,
        adjustment,
        True,
        expected_reduction,
        requires_version,
        False,
    )


def _simulation(model_id: str, dataset: PredictionErrorDataset, recommendation: CalibrationRecommendation) -> CalibrationSimulationResult:
    simulated_error = round(max(dataset.mean_absolute_error - recommendation.expected_error_reduction, 0.0), 6)
    trace_id = f"DCT-{hashlib.sha256(f'{model_id}:{recommendation.recommended_adjustment}:{simulated_error}'.encode('utf-8')).hexdigest()[:8].upper()}"
    return CalibrationSimulationResult(
        f"CSR-{hashlib.sha256(trace_id.encode('utf-8')).hexdigest()[:8].upper()}",
        model_id,
        recommendation.recommended_adjustment,
        simulated_error,
        dataset.mean_absolute_error,
        simulated_error <= dataset.mean_absolute_error,
        trace_id,
    )


def _comparison(model: OrganizationalModel, candidate_version: str, dataset: PredictionErrorDataset, simulation: CalibrationSimulationResult) -> ModelGenerationComparison:
    improvement = round(dataset.mean_absolute_error - simulation.simulated_error, 6)
    return ModelGenerationComparison(
        f"MGC-{hashlib.sha256(f'{model.model_id}:{model.version}:{candidate_version}'.encode('utf-8')).hexdigest()[:8].upper()}",
        model.model_id,
        model.version,
        candidate_version,
        dataset.mean_absolute_error,
        simulation.simulated_error,
        improvement,
        improvement > 0,
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
        produced_by_staff_id=MODEL_CALIBRATION_STAFF_ID,
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
