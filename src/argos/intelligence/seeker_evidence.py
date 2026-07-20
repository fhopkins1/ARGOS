"""MO-TR-012 Seeker conflict-preservation and evidence-sufficiency doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_012_VERSION = "MO-TR-012/1.0.0"


class SeekerConflictClass(str, Enum):
    NO_CONFLICT = "NO_CONFLICT"
    FORMAT_DIFFERENCE = "FORMAT_DIFFERENCE"
    ROUNDING_DIFFERENCE = "ROUNDING_DIFFERENCE"
    TIMING_DIFFERENCE = "TIMING_DIFFERENCE"
    MARKET_SESSION_DIFFERENCE = "MARKET_SESSION_DIFFERENCE"
    MARKET_VENUE_DIFFERENCE = "MARKET_VENUE_DIFFERENCE"
    PRELIMINARY_VS_FINAL = "PRELIMINARY_VS_FINAL"
    REVISED_VALUE = "REVISED_VALUE"
    SOURCE_LAG = "SOURCE_LAG"
    STALE_SOURCE = "STALE_SOURCE"
    PARTIAL_DATA = "PARTIAL_DATA"
    MISSING_DATA = "MISSING_DATA"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    INSTRUMENT_CONFLICT = "INSTRUMENT_CONFLICT"
    UNIT_CONFLICT = "UNIT_CONFLICT"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    DEFINITION_CONFLICT = "DEFINITION_CONFLICT"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    NUMERICAL_CONFLICT = "NUMERICAL_CONFLICT"
    EVENT_CONFLICT = "EVENT_CONFLICT"
    CORRUPTION_SUSPECTED = "CORRUPTION_SUSPECTED"
    MANIPULATION_SUSPECTED = "MANIPULATION_SUSPECTED"
    UNRESOLVED_CONFLICT = "UNRESOLVED_CONFLICT"
    UNKNOWN = "UNKNOWN"


class EvidenceSufficiencyState(str, Enum):
    COMPLETE = "COMPLETE"
    COMPLETE_WITH_CONFLICT = "COMPLETE_WITH_CONFLICT"
    INCOMPLETE = "INCOMPLETE"
    PRIMARY_SOURCE_MISSING = "PRIMARY_SOURCE_MISSING"
    INDEPENDENCE_UNPROVEN = "INDEPENDENCE_UNPROVEN"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    WRONG_ENTITY = "WRONG_ENTITY"
    WRONG_INSTRUMENT = "WRONG_INSTRUMENT"
    WRONG_TIME_WINDOW = "WRONG_TIME_WINDOW"
    UNKNOWN = "UNKNOWN"


class EvidencePackageLifecycleState(str, Enum):
    CREATING = "CREATING"
    COLLECTING = "COLLECTING"
    AWAITING_REQUIRED_EVIDENCE = "AWAITING_REQUIRED_EVIDENCE"
    AWAITING_RETRY = "AWAITING_RETRY"
    READY_FOR_SUFFICIENCY = "READY_FOR_SUFFICIENCY"
    COMPLETE = "COMPLETE"
    COMPLETE_WITH_CONFLICT = "COMPLETE_WITH_CONFLICT"
    INCOMPLETE = "INCOMPLETE"
    ARCHIVED = "ARCHIVED"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN = "UNKNOWN"


class EvidenceRole(str, Enum):
    MANDATORY = "MANDATORY"
    OPTIONAL = "OPTIONAL"
    CORROBORATING = "CORROBORATING"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"


@dataclass(frozen=True)
class SeekerEvidenceRecord:
    evidence_id: str
    observation_id: str
    source_id: str
    authority_class: str
    evidence_role: EvidenceRole
    claim_identity: str
    entity_id: str
    instrument_id: str
    publication_time: str
    observation_time: str
    effective_time: str
    retrieval_time: str
    source_available: bool
    provenance_complete: bool
    normalization_complete: bool
    identity_verified: bool
    version_verified: bool
    fresh: bool
    independent_origin_id: str
    raw_evidence_reference: str
    evidence_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_digest", _stable_digest(self))


@dataclass(frozen=True)
class SeekerConflictRecord:
    conflict_id: str
    workflow_id: str
    claim_identity: str
    fact_domain: str
    observation_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    authority_classes: tuple[str, ...]
    independence_relationships: tuple[str, ...]
    publication_times: tuple[str, ...]
    observation_times: tuple[str, ...]
    effective_times: tuple[str, ...]
    normalization_states: tuple[str, ...]
    conflict_class: SeekerConflictClass
    materiality_status: str
    affected_office: str
    affected_strategy: str
    affected_trade: str
    required_action: str
    resolution_state: str
    rule_version: str
    audit_references: tuple[str, ...]
    system_recorded_time: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


@dataclass(frozen=True)
class MissingEvidenceRecord:
    missing_id: str
    evidence_type: str
    required_role: EvidenceRole
    reason: str
    retry_policy: str
    source_availability: str
    recorded_at: str


@dataclass(frozen=True)
class EvidencePackage:
    package_id: str
    workflow_id: str
    fact_domain: str
    claim_identity: str
    claim_scope: str
    security_identity: str
    issuer_identity: str
    instrument_identity: str
    market_identity: str
    account_identity: str
    observation_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    authority_classes: tuple[str, ...]
    independence_graph: Mapping[str, tuple[str, ...]]
    conflict_graph: Mapping[str, tuple[str, ...]]
    evidence_records: tuple[SeekerEvidenceRecord, ...]
    conflict_records: tuple[SeekerConflictRecord, ...]
    missing_evidence: tuple[MissingEvidenceRecord, ...]
    sufficiency_state: EvidenceSufficiencyState
    lifecycle_state: EvidencePackageLifecycleState
    package_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_digest", _stable_digest(self))


@dataclass(frozen=True)
class EvidencePackageRevision:
    revision_id: str
    previous_package_id: str
    new_package_id: str
    revision_timestamp: str
    revision_reason: str
    new_observations: tuple[str, ...]
    new_conflicts: tuple[str, ...]
    new_missing_items: tuple[str, ...]
    removed_items: tuple[str, ...]
    rule_version: str


class EvidencePackageRepository:
    def __init__(self) -> None:
        self._packages: dict[str, EvidencePackage] = {}
        self._revisions: dict[str, EvidencePackageRevision] = {}

    def create_evidence_package(self, package: EvidencePackage) -> None:
        if package.package_id in self._packages:
            raise ValueError("evidence packages are append-only by package id")
        self._packages[package.package_id] = package

    def get_evidence_package(self, package_id: str) -> EvidencePackage:
        return self._packages[package_id]

    def append_revision(self, revision: EvidencePackageRevision, package: EvidencePackage) -> None:
        if revision.revision_id in self._revisions:
            raise ValueError("evidence package revisions are append-only")
        self._revisions[revision.revision_id] = revision
        self.create_evidence_package(package)

    def get_package_revision(self, revision_id: str) -> EvidencePackageRevision:
        return self._revisions[revision_id]


class EvidencePackageService:
    def __init__(self, repository: EvidencePackageRepository | None = None) -> None:
        self.repository = repository or EvidencePackageRepository()

    def create_evidence_package(self, workflow_id: str, fact_domain: str, claim_identity: str, claim_scope: str = "", security_identity: str = "", issuer_identity: str = "", instrument_identity: str = "", market_identity: str = "", account_identity: str = "") -> EvidencePackage:
        package = EvidencePackage(_stable_id("EVPKG", workflow_id, fact_domain, claim_identity, utc_timestamp()), workflow_id, fact_domain, claim_identity, claim_scope, security_identity, issuer_identity, instrument_identity, market_identity, account_identity, (), (), (), MappingProxyType({}), MappingProxyType({}), (), (), (), EvidenceSufficiencyState.INCOMPLETE, EvidencePackageLifecycleState.CREATING)
        self.repository.create_evidence_package(package)
        return package

    def append_observation(self, package: EvidencePackage, evidence: SeekerEvidenceRecord) -> EvidencePackage:
        records = package.evidence_records + (evidence,)
        return self._revision(package, records, package.conflict_records, package.missing_evidence, "append_observation", (evidence.observation_id,), (), ())

    def append_conflict(self, package: EvidencePackage, conflict: SeekerConflictRecord) -> EvidencePackage:
        return self._revision(package, package.evidence_records, package.conflict_records + (conflict,), package.missing_evidence, "append_conflict", (), (conflict.conflict_id,), ())

    def append_missing_evidence(self, package: EvidencePackage, missing: MissingEvidenceRecord) -> EvidencePackage:
        return self._revision(package, package.evidence_records, package.conflict_records, package.missing_evidence + (missing,), "append_missing_evidence", (), (), (missing.missing_id,))

    def classify_conflict(self, package: EvidencePackage, left: SeekerEvidenceRecord, right: SeekerEvidenceRecord) -> SeekerConflictRecord:
        if left.entity_id != right.entity_id:
            conflict = SeekerConflictClass.IDENTITY_CONFLICT
        elif left.instrument_id != right.instrument_id:
            conflict = SeekerConflictClass.INSTRUMENT_CONFLICT
        elif left.publication_time != right.publication_time or left.effective_time != right.effective_time:
            conflict = SeekerConflictClass.TIMING_DIFFERENCE
        elif left.authority_class != right.authority_class:
            conflict = SeekerConflictClass.AUTHORITY_CONFLICT
        elif left.raw_evidence_reference == right.raw_evidence_reference:
            conflict = SeekerConflictClass.NO_CONFLICT
        else:
            conflict = SeekerConflictClass.UNRESOLVED_CONFLICT
        return SeekerConflictRecord(_stable_id("SEEKCONF", left.observation_id, right.observation_id, conflict.value), package.workflow_id, package.claim_identity, package.fact_domain, (left.observation_id, right.observation_id), (left.source_id, right.source_id), (left.authority_class, right.authority_class), (_independence(left, right),), (left.publication_time, right.publication_time), (left.observation_time, right.observation_time), (left.effective_time, right.effective_time), (str(left.normalization_complete), str(right.normalization_complete)), conflict, "NOT_ASSESSED_BY_SEEKER", "Analyst", "", "", "preserve_conflict_without_resolution", "UNRESOLVED", MO_TR_012_VERSION, (left.raw_evidence_reference, right.raw_evidence_reference), utc_timestamp())

    def evaluate_sufficiency(self, package: EvidencePackage, mandatory_roles: tuple[EvidenceRole, ...] = (EvidenceRole.MANDATORY,)) -> EvidenceSufficiencyState:
        if package.missing_evidence:
            if any(item.required_role is EvidenceRole.MANDATORY for item in package.missing_evidence):
                return EvidenceSufficiencyState.PRIMARY_SOURCE_MISSING
            return EvidenceSufficiencyState.INCOMPLETE
        if not package.evidence_records:
            return EvidenceSufficiencyState.INCOMPLETE
        if any(not record.source_available for record in package.evidence_records):
            return EvidenceSufficiencyState.SOURCE_UNAVAILABLE
        if any(not record.fresh for record in package.evidence_records):
            return EvidenceSufficiencyState.STALE_EVIDENCE
        if any(not record.identity_verified for record in package.evidence_records):
            return EvidenceSufficiencyState.WRONG_ENTITY
        if any(not record.provenance_complete or not record.normalization_complete or not record.version_verified for record in package.evidence_records):
            return EvidenceSufficiencyState.INCOMPLETE
        mandatory_present = any(record.evidence_role in mandatory_roles for record in package.evidence_records)
        if not mandatory_present:
            return EvidenceSufficiencyState.PRIMARY_SOURCE_MISSING
        origins = {record.independent_origin_id for record in package.evidence_records if record.independent_origin_id}
        if len(package.evidence_records) > 1 and len(origins) < 2:
            return EvidenceSufficiencyState.INDEPENDENCE_UNPROVEN
        return EvidenceSufficiencyState.COMPLETE_WITH_CONFLICT if package.conflict_records else EvidenceSufficiencyState.COMPLETE

    def handoff_to_analyst(self, package: EvidencePackage) -> str:
        state = self.evaluate_sufficiency(package)
        if state not in {EvidenceSufficiencyState.COMPLETE, EvidenceSufficiencyState.COMPLETE_WITH_CONFLICT}:
            raise ValueError(f"package not sufficient for Analyst review: {state.value}")
        return _stable_id("ANALYSTHANDOFF", package.package_id, state.value)

    def replay_evidence_package(self, package: EvidencePackage) -> EvidenceSufficiencyState:
        return self.evaluate_sufficiency(package)

    def _revision(self, package: EvidencePackage, records: tuple[SeekerEvidenceRecord, ...], conflicts: tuple[SeekerConflictRecord, ...], missing: tuple[MissingEvidenceRecord, ...], reason: str, new_observations: tuple[str, ...], new_conflicts: tuple[str, ...], new_missing: tuple[str, ...]) -> EvidencePackage:
        state = self.evaluate_sufficiency(replace(package, evidence_records=records, conflict_records=conflicts, missing_evidence=missing))
        lifecycle = EvidencePackageLifecycleState.COMPLETE_WITH_CONFLICT if state is EvidenceSufficiencyState.COMPLETE_WITH_CONFLICT else EvidencePackageLifecycleState.COMPLETE if state is EvidenceSufficiencyState.COMPLETE else EvidencePackageLifecycleState.AWAITING_REQUIRED_EVIDENCE
        new_package = EvidencePackage(_stable_id("EVPKG", package.package_id, reason, len(records), len(conflicts), len(missing)), package.workflow_id, package.fact_domain, package.claim_identity, package.claim_scope, package.security_identity, package.issuer_identity, package.instrument_identity, package.market_identity, package.account_identity, tuple(record.observation_id for record in records), tuple(record.source_id for record in records), tuple(record.authority_class for record in records), MappingProxyType(_independence_graph(records)), MappingProxyType(_conflict_graph(conflicts)), records, conflicts, missing, state, lifecycle)
        revision = EvidencePackageRevision(_stable_id("EVREV", package.package_id, new_package.package_id, reason), package.package_id, new_package.package_id, utc_timestamp(), reason, new_observations, new_conflicts, new_missing, (), MO_TR_012_VERSION)
        self.repository.append_revision(revision, new_package)
        return new_package


def _independence(left: SeekerEvidenceRecord, right: SeekerEvidenceRecord) -> str:
    if not left.independent_origin_id or not right.independent_origin_id:
        return "UNKNOWN"
    return "INDEPENDENT" if left.independent_origin_id != right.independent_origin_id else "SAME_ORIGIN"


def _independence_graph(records: tuple[SeekerEvidenceRecord, ...]) -> dict[str, tuple[str, ...]]:
    graph: dict[str, list[str]] = {}
    for record in records:
        graph.setdefault(record.independent_origin_id or "UNKNOWN", []).append(record.observation_id)
    return {key: tuple(value) for key, value in graph.items()}


def _conflict_graph(conflicts: tuple[SeekerConflictRecord, ...]) -> dict[str, tuple[str, ...]]:
    return {conflict.conflict_id: conflict.observation_ids for conflict in conflicts}


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{_stable_digest(parts)[:24].upper()}"


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return dict(value)
    if is_dataclass(value):
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"record_digest", "evidence_digest", "package_digest"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
