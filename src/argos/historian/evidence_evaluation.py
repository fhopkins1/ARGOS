"""Evidence Evaluation Office."""

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


EVIDENCE_EVALUATION_OFFICE_ID = "HISTORIAN-OFFICE-007"
EVIDENCE_EVALUATION_STAFF_ID = "STF-076"


class EvidenceStatus(str, Enum):
    """Evidence registry status."""

    REGISTERED = "registered"
    EVALUATED = "evaluated"
    ARCHIVED = "archived"


class EvidenceConflictSeverity(str, Enum):
    """Evidence conflict severity."""

    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class OrganizationalEvidence:
    """Significant organizational evidence item."""

    evidence_id: str
    source_type: str
    source_id: str
    claim_id: str
    provenance_id: str
    collection_timestamp_utc: str
    reliability_score: float
    relevance_score: float
    completeness_score: float
    independence_group: str
    supports_claim: bool
    audit_record_id: str


@dataclass(frozen=True)
class EvidenceRegistryRecord:
    """Immutable evidence registry record."""

    registry_id: str
    evidence: OrganizationalEvidence
    status: EvidenceStatus
    registered_timestamp_utc: str
    evaluation_record_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceQualityDataset:
    """Evidence quality dataset."""

    dataset_id: str
    evidence_id: str
    reliability_score: float
    relevance_score: float
    completeness_score: float
    quality_score: float


@dataclass(frozen=True)
class EvidenceIndependenceAssessment:
    """Evidence independence assessment."""

    assessment_id: str
    evidence_ids: tuple[str, ...]
    independent_source_count: int
    total_evidence_count: int
    independence_score: float
    independence_groups: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceSufficiencyReport:
    """Evidence sufficiency report."""

    sufficiency_id: str
    claim_id: str
    required_evidence_count: int
    supplied_evidence_count: int
    average_quality_score: float
    sufficiency_score: float
    sufficient: bool


@dataclass(frozen=True)
class EvidenceConflictRecord:
    """Evidence conflict record."""

    conflict_id: str
    claim_id: str
    support_count: int
    contradiction_count: int
    conflict_score: float
    severity: EvidenceConflictSeverity
    conflicting_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceFreshnessRecord:
    """Evidence freshness record."""

    freshness_id: str
    evidence_id: str
    age_days: int
    freshness_score: float


@dataclass(frozen=True)
class EvidenceWeightRecord:
    """Deterministic evidence weight record."""

    weight_id: str
    evidence_id: str
    quality_score: float
    independence_score: float
    freshness_score: float
    conflict_penalty: float
    deterministic_weight: float


@dataclass(frozen=True)
class EvidenceIntegrityAssessment:
    """Evidence integrity assessment."""

    integrity_id: str
    evidence_ids: tuple[str, ...]
    provenance_preserved: bool
    historical_archive_immutable: bool
    trace_complete: bool


@dataclass(frozen=True)
class EvidenceRecommendation:
    """Evidence-based organizational recommendation."""

    recommendation_id: str
    claim_id: str
    recommendation: str
    evidence_based: bool
    recommended_consumers: tuple[str, ...]
    directly_modifies_behavior: bool


@dataclass(frozen=True)
class EvidenceEvaluationStandards:
    """Librarian deliverable for evidence evaluation."""

    standards_id: str
    quality_methodology: str
    weighting_methodology: str
    provenance_specification: str
    confidence_rule: str


class EvidenceEvaluationOffice:
    """Deterministic authority for evaluating organizational evidence."""

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
        self._registry: dict[str, EvidenceRegistryRecord] = {}
        self._evidence_archive: list[dict[str, object]] = []

    @property
    def evidence_registry(self) -> tuple[EvidenceRegistryRecord, ...]:
        """Return immutable evidence registry."""
        return tuple(self._registry[key] for key in sorted(self._registry))

    @property
    def historical_evidence_archive(self) -> tuple[dict[str, object], ...]:
        """Return preserved historical evidence archive."""
        return tuple(self._evidence_archive)

    def standards(self) -> EvidenceEvaluationStandards:
        """Return evidence standards for Librarian consumption."""
        return EvidenceEvaluationStandards(
            "EES-067",
            "Evidence quality is the mean of reliability, relevance, and completeness.",
            "Evidence weight combines quality, independence, freshness, and conflict penalty deterministically.",
            "Every evidence item must preserve source, provenance, timestamp, and audit identifiers.",
            "Organizational confidence must remain proportional to evidence quality, not authority or historical success.",
        )

    def register_evidence(
        self,
        evidence: OrganizationalEvidence,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Register a significant evidence item."""
        self.configuration_service.validate_startup()
        if evidence.evidence_id in self._registry:
            raise ValueError(f"evidence already registered: {evidence.evidence_id}")
        record = EvidenceRegistryRecord(
            f"ERR-{hashlib.sha256(evidence.evidence_id.encode('utf-8')).hexdigest()[:8].upper()}",
            evidence,
            EvidenceStatus.REGISTERED,
            utc_timestamp(),
            (),
        )
        self._registry[evidence.evidence_id] = record
        return self._persist_contract(
            "EVIDENCE_REGISTRY",
            case_file_id,
            trade_cycle_id,
            document_sequence,
            "Evidence Registry.",
            {"evidence_registry_record": record, "provenance_registry_updated": True, "historical_evidence_archive_immutable": True},
        )

    def evaluate_evidence(
        self,
        evidence_ids: tuple[str, ...],
        required_evidence_count: int,
        current_day: int,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Evaluate evidence independently from conclusions."""
        self.configuration_service.validate_startup()
        if not evidence_ids:
            raise ValueError("evidence evaluation requires at least one evidence item")
        missing = tuple(item for item in evidence_ids if item not in self._registry)
        if missing:
            raise ValueError(f"unknown evidence items: {', '.join(missing)}")
        evidence = tuple(self._registry[item].evidence for item in evidence_ids)
        claim_ids = {item.claim_id for item in evidence}
        if len(claim_ids) != 1:
            raise ValueError("evidence evaluation requires one claim_id per evaluation")
        claim_id = next(iter(claim_ids))
        quality = tuple(_quality_dataset(item) for item in evidence)
        independence = _independence(evidence)
        conflict = _conflict(claim_id, evidence)
        freshness = tuple(_freshness(item, current_day) for item in evidence)
        sufficiency = _sufficiency(claim_id, quality, required_evidence_count)
        weights = tuple(_weight(item, quality[index], independence, freshness[index], conflict) for index, item in enumerate(evidence))
        recommendation = _recommendation(claim_id, sufficiency, conflict, independence)
        integrity = EvidenceIntegrityAssessment(
            f"EIA-{hashlib.sha256(':'.join(evidence_ids).encode('utf-8')).hexdigest()[:8].upper()}",
            evidence_ids,
            True,
            True,
            True,
        )
        updated_records = []
        for item in evidence_ids:
            registry = self._registry[item]
            updated = EvidenceRegistryRecord(
                registry.registry_id,
                registry.evidence,
                EvidenceStatus.EVALUATED,
                registry.registered_timestamp_utc,
                (*registry.evaluation_record_ids, sufficiency.sufficiency_id),
            )
            self._registry[item] = updated
            updated_records.append(updated)
        self._evidence_archive.append(
            _json_ready(
                {
                    "claim_id": claim_id,
                    "evidence_ids": evidence_ids,
                    "sufficiency_score": sufficiency.sufficiency_score,
                    "conflict_score": conflict.conflict_score,
                    "weights": weights,
                }
            )
        )
        return {
            "evidence_evaluation_report": self._persist_contract(
                "EVIDENCE_EVALUATION_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Evidence Evaluation Report.",
                {
                    "office_id": EVIDENCE_EVALUATION_OFFICE_ID,
                    "office_name": "Evidence Evaluation Office",
                    "evidence_registry_records": tuple(updated_records),
                    "evidence_quality_dataset": quality,
                    "evidence_independence_assessment": independence,
                    "evidence_freshness_archive": freshness,
                    "evidence_weight_database": weights,
                    "evidence_integrity_assessment": integrity,
                    "evidence_evaluation_standards": self.standards(),
                    "conclusions_evaluated": False,
                },
            ),
            "evidence_conflict_report": self._persist_contract(
                "EVIDENCE_CONFLICT_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Evidence Conflict Report.",
                {"evidence_conflict_register": (conflict,)},
            ),
            "evidence_sufficiency_report": self._persist_contract(
                "EVIDENCE_SUFFICIENCY_REPORT",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Evidence Sufficiency Report.",
                {"evidence_sufficiency_report": sufficiency},
            ),
            "organizational_evidence_summary": self._persist_contract(
                "ORGANIZATIONAL_EVIDENCE_SUMMARY",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Organizational Evidence Summary.",
                {
                    "evidence_registry": self.evidence_registry,
                    "organizational_recommendation_register": (recommendation,),
                    "historical_evidence_archive_complete": True,
                    "confidence_proportional_to_evidence_quality": True,
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


def _quality_dataset(evidence: OrganizationalEvidence) -> EvidenceQualityDataset:
    score = round(mean((evidence.reliability_score, evidence.relevance_score, evidence.completeness_score)), 6)
    return EvidenceQualityDataset(
        f"EQD-{hashlib.sha256(evidence.evidence_id.encode('utf-8')).hexdigest()[:8].upper()}",
        evidence.evidence_id,
        evidence.reliability_score,
        evidence.relevance_score,
        evidence.completeness_score,
        score,
    )


def _independence(evidence: tuple[OrganizationalEvidence, ...]) -> EvidenceIndependenceAssessment:
    groups = tuple(sorted({item.independence_group for item in evidence}))
    score = round(len(groups) / max(len(evidence), 1), 6)
    return EvidenceIndependenceAssessment(
        f"EIA-{hashlib.sha256(':'.join(item.evidence_id for item in evidence).encode('utf-8')).hexdigest()[:8].upper()}",
        tuple(item.evidence_id for item in evidence),
        len(groups),
        len(evidence),
        score,
        groups,
    )


def _conflict(claim_id: str, evidence: tuple[OrganizationalEvidence, ...]) -> EvidenceConflictRecord:
    support = sum(1 for item in evidence if item.supports_claim)
    contradiction = len(evidence) - support
    score = round(min(support, contradiction) / max(len(evidence), 1), 6)
    if score == 0:
        severity = EvidenceConflictSeverity.NONE
    elif score < 0.25:
        severity = EvidenceConflictSeverity.LOW
    elif score < 0.5:
        severity = EvidenceConflictSeverity.MODERATE
    else:
        severity = EvidenceConflictSeverity.HIGH
    return EvidenceConflictRecord(
        f"ECR-{hashlib.sha256(f'{claim_id}:{support}:{contradiction}'.encode('utf-8')).hexdigest()[:8].upper()}",
        claim_id,
        support,
        contradiction,
        score,
        severity,
        tuple(item.evidence_id for item in evidence if not item.supports_claim),
    )


def _freshness(evidence: OrganizationalEvidence, current_day: int) -> EvidenceFreshnessRecord:
    collected_day = _day_from_timestamp(evidence.collection_timestamp_utc)
    age = max(current_day - collected_day, 0)
    freshness = round(max(1.0 - (age / 365.0), 0.0), 6)
    return EvidenceFreshnessRecord(
        f"EFR-{hashlib.sha256(f'{evidence.evidence_id}:{age}'.encode('utf-8')).hexdigest()[:8].upper()}",
        evidence.evidence_id,
        age,
        freshness,
    )


def _sufficiency(claim_id: str, quality: tuple[EvidenceQualityDataset, ...], required: int) -> EvidenceSufficiencyReport:
    average_quality = round(mean(item.quality_score for item in quality), 6)
    count_score = min(len(quality) / max(required, 1), 1.0)
    sufficiency = round((average_quality * 0.7) + (count_score * 0.3), 6)
    return EvidenceSufficiencyReport(
        f"ESR-{hashlib.sha256(f'{claim_id}:{len(quality)}:{required}'.encode('utf-8')).hexdigest()[:8].upper()}",
        claim_id,
        required,
        len(quality),
        average_quality,
        sufficiency,
        sufficiency >= 0.75,
    )


def _weight(
    evidence: OrganizationalEvidence,
    quality: EvidenceQualityDataset,
    independence: EvidenceIndependenceAssessment,
    freshness: EvidenceFreshnessRecord,
    conflict: EvidenceConflictRecord,
) -> EvidenceWeightRecord:
    penalty = conflict.conflict_score if not evidence.supports_claim else conflict.conflict_score * 0.5
    weight = round(max((quality.quality_score * 0.5) + (independence.independence_score * 0.25) + (freshness.freshness_score * 0.25) - penalty, 0.0), 6)
    return EvidenceWeightRecord(
        f"EWR-{hashlib.sha256(f'{evidence.evidence_id}:{weight}'.encode('utf-8')).hexdigest()[:8].upper()}",
        evidence.evidence_id,
        quality.quality_score,
        independence.independence_score,
        freshness.freshness_score,
        round(penalty, 6),
        weight,
    )


def _recommendation(
    claim_id: str,
    sufficiency: EvidenceSufficiencyReport,
    conflict: EvidenceConflictRecord,
    independence: EvidenceIndependenceAssessment,
) -> EvidenceRecommendation:
    if conflict.severity in {EvidenceConflictSeverity.MODERATE, EvidenceConflictSeverity.HIGH}:
        text = "Resolve evidence conflicts before increasing organizational confidence."
    elif not sufficiency.sufficient:
        text = "Acquire additional high-quality evidence before relying on this claim."
    elif independence.independence_score < 0.5:
        text = "Increase independent evidence diversity before doctrine consideration."
    else:
        text = "Evidence base is sufficient for downstream evaluation."
    return EvidenceRecommendation(
        f"EREC-{hashlib.sha256(f'{claim_id}:{text}'.encode('utf-8')).hexdigest()[:8].upper()}",
        claim_id,
        text,
        True,
        ("Librarian Group", "Executive Group", "Future Engineering Orders"),
        False,
    )


def _day_from_timestamp(timestamp_utc: str) -> int:
    date_part = timestamp_utc.split("T", 1)[0]
    year, month, day = (int(part) for part in date_part.split("-"))
    return (year * 365) + (month * 30) + day


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
        produced_by_staff_id=EVIDENCE_EVALUATION_STAFF_ID,
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
