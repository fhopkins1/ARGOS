"""Hypothesis Validation Office."""

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

from .group import HISTORIAN_GROUP_ID


HYPOTHESIS_VALIDATION_OFFICE_ID = "HISTORIAN-OFFICE-003"
HYPOTHESIS_VALIDATION_STAFF_ID = "STF-072"


class HypothesisStatus(str, Enum):
    """Deterministic hypothesis lifecycle status."""

    REGISTERED = "registered"
    UNDER_REVIEW = "under_review"
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    VALIDATED = "validated"
    REJECTED = "rejected"
    DRIFTING = "drifting"
    ARCHIVED = "archived"


class EvidenceRelationship(str, Enum):
    """Evidence relationship to a hypothesis."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class OrganizationalHypothesis:
    """Significant organizational hypothesis."""

    hypothesis_id: str
    title: str
    originating_group: str
    statement: str
    confidence_prior: float
    doctrine_candidate: bool
    created_case_id: str
    audit_record_id: str


@dataclass(frozen=True)
class HypothesisRegistryRecord:
    """Immutable hypothesis registry record."""

    registry_id: str
    hypothesis: OrganizationalHypothesis
    current_status: HypothesisStatus
    registered_timestamp_utc: str
    lifecycle_record_ids: tuple[str, ...]


@dataclass(frozen=True)
class ValidationLifecycleRecord:
    """Hypothesis lifecycle transition."""

    lifecycle_id: str
    hypothesis_id: str
    previous_status: HypothesisStatus
    new_status: HypothesisStatus
    triggering_evidence_ids: tuple[str, ...]
    timestamp_utc: str
    deterministic_reason: str


@dataclass(frozen=True)
class HypothesisEvidence:
    """Evidence correlated to a hypothesis."""

    evidence_id: str
    source_case_id: str
    relationship: EvidenceRelationship
    strength: float
    observed_metric: str
    observed_value: float
    audit_record_id: str


@dataclass(frozen=True)
class EvidenceCorrelationRecord:
    """Deterministic evidence correlation record."""

    correlation_id: str
    hypothesis_id: str
    support_score: float
    contradiction_score: float
    neutral_score: float
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class FalsificationRecord:
    """Active falsification result."""

    falsification_id: str
    hypothesis_id: str
    contradicted: bool
    contradiction_evidence_ids: tuple[str, ...]
    falsification_threshold: float
    deterministic_result: str


@dataclass(frozen=True)
class ConfidenceCalibrationRecord:
    """Confidence calibration result."""

    calibration_id: str
    hypothesis_id: str
    prior_confidence: float
    calibrated_confidence: float
    calibration_error: float
    calibration_dataset_ids: tuple[str, ...]


@dataclass(frozen=True)
class HypothesisDriftRecord:
    """Hypothesis drift detection result."""

    drift_id: str
    hypothesis_id: str
    drift_detected: bool
    baseline_confidence: float
    current_confidence: float
    drift_delta: float
    evidence_window_ids: tuple[str, ...]


@dataclass(frozen=True)
class OrganizationalLearningRecommendation:
    """Evidence-based learning recommendation."""

    recommendation_id: str
    hypothesis_id: str
    recommendation: str
    evidence_based: bool
    eligible_for_doctrine: bool
    recommended_consumers: tuple[str, ...]
    directly_modifies_behavior: bool


@dataclass(frozen=True)
class HypothesisValidationStandards:
    """Librarian deliverable for validation standards."""

    standards_id: str
    validation_methodology: str
    confidence_calibration_methodology: str
    doctrine_gate: str


class HypothesisValidationOffice:
    """Deterministic scientific validation authority."""

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
        self._registry: dict[str, HypothesisRegistryRecord] = {}
        self._validation_archive: list[dict[str, object]] = []

    @property
    def hypothesis_registry(self) -> tuple[HypothesisRegistryRecord, ...]:
        """Return immutable registry records."""
        return tuple(self._registry[key] for key in sorted(self._registry))

    @property
    def validation_history_archive(self) -> tuple[dict[str, object], ...]:
        """Return preserved validation history."""
        return tuple(self._validation_archive)

    def standards(self) -> HypothesisValidationStandards:
        """Return validation standards for Librarian consumption."""
        return HypothesisValidationStandards(
            "HVS-063",
            "Correlate empirical evidence, actively falsify, calibrate confidence, and gate doctrine by validation status.",
            "calibrated_confidence = bounded(prior + support_score - contradiction_score); calibration_error = abs(prior - calibrated)",
            "Only validated hypotheses may progress toward institutional doctrine.",
        )

    def register_hypothesis(
        self,
        hypothesis: OrganizationalHypothesis,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Register a significant organizational hypothesis."""
        self.configuration_service.validate_startup()
        if hypothesis.hypothesis_id in self._registry:
            raise ValueError(f"hypothesis already registered: {hypothesis.hypothesis_id}")
        lifecycle = ValidationLifecycleRecord(
            f"HLR-{document_sequence:06d}",
            hypothesis.hypothesis_id,
            HypothesisStatus.REGISTERED,
            HypothesisStatus.REGISTERED,
            (),
            utc_timestamp(),
            "Initial deterministic hypothesis registration.",
        )
        record = HypothesisRegistryRecord(
            f"HRR-{hashlib.sha256(hypothesis.hypothesis_id.encode('utf-8')).hexdigest()[:8].upper()}",
            hypothesis,
            HypothesisStatus.REGISTERED,
            lifecycle.timestamp_utc,
            (lifecycle.lifecycle_id,),
        )
        self._registry[hypothesis.hypothesis_id] = record
        return self._persist_contract(
            "HYPOTHESIS_REGISTRY",
            case_file_id,
            trade_cycle_id,
            document_sequence,
            "Hypothesis Registry.",
            {
                "hypothesis_registry_record": record,
                "validation_lifecycle_record": lifecycle,
                "historical_validation_archive_updated": True,
            },
        )

    def validate_hypothesis(
        self,
        hypothesis_id: str,
        evidence: tuple[HypothesisEvidence, ...],
        calibration_dataset_ids: tuple[str, ...],
        baseline_confidence: float,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Validate a registered hypothesis from empirical evidence."""
        self.configuration_service.validate_startup()
        if hypothesis_id not in self._registry:
            raise ValueError(f"unknown hypothesis: {hypothesis_id}")
        if not evidence:
            raise ValueError("hypothesis validation requires empirical evidence")
        registry = self._registry[hypothesis_id]
        correlation = _correlate(hypothesis_id, evidence)
        falsification = _falsify(hypothesis_id, evidence, correlation)
        calibration = _calibrate(registry.hypothesis, correlation, calibration_dataset_ids)
        drift = _drift(hypothesis_id, baseline_confidence, calibration.calibrated_confidence, evidence)
        status = _status(correlation, falsification, drift)
        lifecycle = ValidationLifecycleRecord(
            f"HLR-{document_sequence:06d}",
            hypothesis_id,
            registry.current_status,
            status,
            tuple(item.evidence_id for item in evidence),
            utc_timestamp(),
            f"support={correlation.support_score}; contradiction={correlation.contradiction_score}; drift={drift.drift_detected}",
        )
        updated_registry = HypothesisRegistryRecord(
            registry.registry_id,
            registry.hypothesis,
            status,
            registry.registered_timestamp_utc,
            (*registry.lifecycle_record_ids, lifecycle.lifecycle_id),
        )
        self._registry[hypothesis_id] = updated_registry
        recommendation = _recommendation(hypothesis_id, status, correlation, falsification)
        archive_entry = {
            "hypothesis_id": hypothesis_id,
            "status": status.value,
            "evidence_ids": tuple(item.evidence_id for item in evidence),
            "calibrated_confidence": calibration.calibrated_confidence,
            "doctrine_eligible": recommendation.eligible_for_doctrine,
        }
        self._validation_archive.append(_json_ready(archive_entry))
        return {
            "hypothesis_validation_report": self._persist_contract(
                "HYPOTHESIS_VALIDATION_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Hypothesis Validation Report.",
                {
                    "office_id": HYPOTHESIS_VALIDATION_OFFICE_ID,
                    "office_name": "Hypothesis Validation Office",
                    "hypothesis_registry_record": updated_registry,
                    "validation_lifecycle_record": lifecycle,
                    "evidence_correlation_record": correlation,
                    "falsification_record": falsification,
                    "confidence_calibration_record": calibration,
                    "organizational_learning_recommendation": recommendation,
                    "validation_standards": self.standards(),
                    "empirical_evidence_required": True,
                },
            ),
            "hypothesis_drift_report": self._persist_contract(
                "HYPOTHESIS_DRIFT_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Hypothesis Drift Report.",
                {"hypothesis_drift_record": drift, "hypothesis_drift_archive_updated": True},
            ),
            "organizational_hypothesis_summary": self._persist_contract(
                "ORGANIZATIONAL_HYPOTHESIS_SUMMARY",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Organizational Hypothesis Summary.",
                {"hypothesis_registry": self.hypothesis_registry, "only_validated_hypotheses_progress_to_doctrine": True},
            ),
            "confidence_calibration_report": self._persist_contract(
                "CONFIDENCE_CALIBRATION_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Confidence Calibration Report.",
                {"confidence_calibration_record": calibration, "calibration_dataset": calibration_dataset_ids},
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


def _correlate(hypothesis_id: str, evidence: tuple[HypothesisEvidence, ...]) -> EvidenceCorrelationRecord:
    support = sum(item.strength for item in evidence if item.relationship == EvidenceRelationship.SUPPORTS)
    contradiction = sum(item.strength for item in evidence if item.relationship == EvidenceRelationship.CONTRADICTS)
    neutral = sum(item.strength for item in evidence if item.relationship == EvidenceRelationship.NEUTRAL)
    total = max(support + contradiction + neutral, 1.0)
    return EvidenceCorrelationRecord(
        f"ECR-{hashlib.sha256(f'{hypothesis_id}:{tuple(item.evidence_id for item in evidence)}'.encode('utf-8')).hexdigest()[:8].upper()}",
        hypothesis_id,
        round(support / total, 6),
        round(contradiction / total, 6),
        round(neutral / total, 6),
        tuple(item.evidence_id for item in evidence),
    )


def _falsify(hypothesis_id: str, evidence: tuple[HypothesisEvidence, ...], correlation: EvidenceCorrelationRecord) -> FalsificationRecord:
    threshold = 0.55
    contradiction_ids = tuple(item.evidence_id for item in evidence if item.relationship == EvidenceRelationship.CONTRADICTS)
    contradicted = correlation.contradiction_score >= threshold
    return FalsificationRecord(
        f"FR-{hashlib.sha256(f'{hypothesis_id}:{contradiction_ids}'.encode('utf-8')).hexdigest()[:8].upper()}",
        hypothesis_id,
        contradicted,
        contradiction_ids,
        threshold,
        "hypothesis_contradicted" if contradicted else "hypothesis_not_falsified",
    )


def _calibrate(hypothesis: OrganizationalHypothesis, correlation: EvidenceCorrelationRecord, dataset_ids: tuple[str, ...]) -> ConfidenceCalibrationRecord:
    calibrated = min(max(hypothesis.confidence_prior + (correlation.support_score * 0.3) - (correlation.contradiction_score * 0.5), 0.0), 1.0)
    calibrated = round(calibrated, 6)
    return ConfidenceCalibrationRecord(
        f"CCR-{hashlib.sha256(f'{hypothesis.hypothesis_id}:{dataset_ids}'.encode('utf-8')).hexdigest()[:8].upper()}",
        hypothesis.hypothesis_id,
        hypothesis.confidence_prior,
        calibrated,
        round(abs(hypothesis.confidence_prior - calibrated), 6),
        dataset_ids,
    )


def _drift(hypothesis_id: str, baseline: float, current: float, evidence: tuple[HypothesisEvidence, ...]) -> HypothesisDriftRecord:
    delta = round(current - baseline, 6)
    return HypothesisDriftRecord(
        f"HDR-{hashlib.sha256(f'{hypothesis_id}:{baseline}:{current}'.encode('utf-8')).hexdigest()[:8].upper()}",
        hypothesis_id,
        abs(delta) > 0.2,
        baseline,
        current,
        delta,
        tuple(item.evidence_id for item in evidence),
    )


def _status(correlation: EvidenceCorrelationRecord, falsification: FalsificationRecord, drift: HypothesisDriftRecord) -> HypothesisStatus:
    if falsification.contradicted:
        return HypothesisStatus.REJECTED
    if correlation.support_score >= 0.65:
        return HypothesisStatus.VALIDATED
    if drift.drift_detected:
        return HypothesisStatus.DRIFTING
    if correlation.support_score > correlation.contradiction_score:
        return HypothesisStatus.SUPPORTED
    return HypothesisStatus.CONTRADICTED


def _recommendation(
    hypothesis_id: str,
    status: HypothesisStatus,
    correlation: EvidenceCorrelationRecord,
    falsification: FalsificationRecord,
) -> OrganizationalLearningRecommendation:
    eligible = status == HypothesisStatus.VALIDATED and not falsification.contradicted
    if eligible:
        recommendation = "Promote hypothesis toward validated institutional knowledge review."
    elif status == HypothesisStatus.REJECTED:
        recommendation = "Reject hypothesis and prevent doctrine promotion."
    elif status == HypothesisStatus.DRIFTING:
        recommendation = "Continue validation and investigate hypothesis drift."
    else:
        recommendation = "Continue empirical validation before doctrine consideration."
    return OrganizationalLearningRecommendation(
        f"OLR-{hashlib.sha256(f'{hypothesis_id}:{status.value}:{correlation.support_score}'.encode('utf-8')).hexdigest()[:8].upper()}",
        hypothesis_id,
        recommendation,
        True,
        eligible,
        ("Librarian Group", "Executive Group", "Future Engineering Orders"),
        False,
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
        produced_by_staff_id=HYPOTHESIS_VALIDATION_STAFF_ID,
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
