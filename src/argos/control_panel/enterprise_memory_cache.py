"""Enterprise Memory Cache for ARGOS EO-CG."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .information_freshness_engine import FreshnessAction, FreshnessStatus, InformationDomain, InformationFreshnessEngine, SourceAuthorityClass


class CacheProductType(str, Enum):
    OFFICE_REPORT = "office_report"
    DECISION_PRODUCT = "decision_product"
    EVIDENCE_PACKAGE = "evidence_package"
    STRUCTURED_CALCULATION = "structured_calculation"
    MISSION_PRODUCT = "mission_product"
    WORKFLOW_PRODUCT = "workflow_product"
    POSITION_PRODUCT = "position_product"
    PORTFOLIO_PRODUCT = "portfolio_product"
    ENTERPRISE_PRODUCT = "enterprise_product"
    POLICY_PRODUCT = "policy_product"
    HISTORICAL_PRODUCT = "historical_product"
    REPLAY_PRODUCT = "replay_product"
    TRAINING_PRODUCT = "training_product"


class CacheTier(str, Enum):
    TRANSIENT = "transient"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    AUTHORITATIVE_REFERENCE = "authoritative_reference"
    HISTORICAL = "historical"
    ARCHIVED = "archived"
    QUARANTINED = "quarantined"


class CacheRecordStatus(str, Enum):
    PENDING_ADMISSION = "pending_admission"
    ACTIVE = "active"
    LIMITED_USE = "limited_use"
    VALIDATION_REQUIRED = "validation_required"
    PARTIALLY_INVALIDATED = "partially_invalidated"
    INVALIDATED = "invalidated"
    SUPERSEDED = "superseded"
    CONTRADICTED = "contradicted"
    QUARANTINED = "quarantined"
    ARCHIVED = "archived"
    DELETED_TOMBSTONE = "deleted_tombstone"


class CacheReuseDecision(str, Enum):
    REUSE_EXACT = "reuse_exact"
    REUSE_WITH_VALIDATION = "reuse_with_validation"
    REUSE_PARTIAL_SCOPE = "reuse_partial_scope"
    USE_AS_SUPPORTING_INPUT = "use_as_supporting_input"
    USE_HISTORICAL_ONLY = "use_historical_only"
    DELTA_REFRESH_REQUIRED = "delta_refresh_required"
    FULL_REFRESH_REQUIRED = "full_refresh_required"
    REJECT_REUSE = "reject_reuse"
    NO_MATCH = "no_match"


class CacheMatchType(str, Enum):
    RECORD_ID = "record_id"
    PRODUCT_KEY = "product_key"
    EXACT_METADATA = "exact_metadata"
    SUBJECT_PRODUCT_TYPE = "subject_product_type"
    MISSION_LINEAGE = "mission_lineage"
    WORKFLOW_LINEAGE = "workflow_lineage"
    FIELD_SCOPE = "field_scope"
    SECTION_SCOPE = "section_scope"
    STRUCTURED_SIMILARITY = "structured_similarity"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    RELATED_EVIDENCE = "related_evidence"


class CacheEnvironment(str, Enum):
    LIVE = "live"
    PAPER = "paper"
    SIMULATION = "simulation"
    REPLAY = "replay"
    TEST = "test"
    DEVELOPMENT = "development"


@dataclass(frozen=True)
class CacheProductRecord:
    cache_record_id: str
    product_type: CacheProductType
    product_subtype: str
    cache_tier: CacheTier
    status: CacheRecordStatus
    environment: CacheEnvironment
    product_key: str
    product_version: int
    title: str
    summary: str
    subject_type: str
    subject_id: str
    ticker: str
    position_id: str
    order_id: str
    portfolio_id: str
    strategy_id: str
    producing_office_id: str
    producing_service_id: str
    mission_id: str
    mission_plan_id: str
    workflow_id: str
    decision_object_id: str
    source_event_ids: tuple[str, ...]
    source_information_record_ids: tuple[str, ...]
    evidence_record_ids: tuple[str, ...]
    schema_name: str
    schema_version: str
    payload_reference: str
    payload_format: str
    payload_size_bytes: int
    field_manifest: tuple[str, ...]
    section_manifest: tuple[str, ...]
    confidence: float
    validation_state: str
    information_record_id: str
    freshness_policy_id: str
    freshness_policy_version: int
    decision_use_classes: tuple[str, ...]
    prohibited_use_classes: tuple[str, ...]
    dependency_record_ids: tuple[str, ...]
    supersedes_cache_record_id: str
    superseded_by_cache_record_id: str
    created_at: str
    admitted_at: str
    last_accessed_at: str
    content_hash: str
    metadata_hash: str


@dataclass(frozen=True)
class CacheAdmissionRequest:
    admission_request_id: str
    product_reference: str
    product_type: CacheProductType
    product_subtype: str
    proposed_tier: CacheTier
    environment: CacheEnvironment
    producing_office_id: str
    producing_service_id: str
    mission_id: str
    workflow_id: str
    subject_type: str
    subject_id: str
    schema_name: str
    schema_version: str
    provenance: dict[str, Any]
    validation_evidence: dict[str, Any]
    expected_reuse_value: str
    retention_class: str
    submitted_at: str


@dataclass(frozen=True)
class CacheAdmissionDecision:
    admission_decision_id: str
    admission_request_id: str
    admitted: bool
    assigned_tier: CacheTier | None
    assigned_status: CacheRecordStatus | None
    duplicate_record_id: str
    superseded_record_id: str
    reason_codes: tuple[str, ...]
    explanation: str
    required_corrections: tuple[str, ...]
    quarantine_required: bool
    decided_at: str
    content_hash: str


@dataclass(frozen=True)
class CacheQuery:
    cache_query_id: str
    requester_type: str
    requester_id: str
    mission_id: str
    mission_type: str
    workflow_id: str
    office_id: str
    decision_use_class: str
    environment: CacheEnvironment
    subject_type: str
    subject_id: str
    ticker: str
    position_id: str
    order_id: str
    strategy_id: str
    requested_product_types: tuple[CacheProductType, ...]
    requested_product_subtypes: tuple[str, ...]
    requested_fields: tuple[str, ...]
    requested_sections: tuple[str, ...]
    required_schema_name: str
    required_schema_version: str
    minimum_confidence: float | None
    maximum_results: int
    exact_match_only: bool
    allow_similarity: bool
    allow_historical: bool
    allow_limited_use: bool
    query_terms: tuple[str, ...]
    metadata_filters: dict[str, Any]
    requested_at: str


@dataclass(frozen=True)
class CacheMatch:
    cache_match_id: str
    cache_query_id: str
    cache_record_id: str
    match_type: CacheMatchType
    match_score: float
    exact_subject_match: bool
    exact_product_type_match: bool
    exact_scope_match: bool
    exact_environment_match: bool
    schema_compatible: bool
    matched_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    matched_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    match_reason: str
    created_at: str


@dataclass(frozen=True)
class CacheReuseEvaluation:
    cache_reuse_evaluation_id: str
    cache_query_id: str
    cache_record_id: str
    freshness_decision_id: str
    decision: CacheReuseDecision
    reusable_fields: tuple[str, ...]
    non_reusable_fields: tuple[str, ...]
    reusable_sections: tuple[str, ...]
    non_reusable_sections: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    refresh_requirements: tuple[str, ...]
    scope_coverage_percent: float
    confidence_satisfied: bool
    environment_satisfied: bool
    schema_satisfied: bool
    authority_satisfied: bool
    access_satisfied: bool
    decision_use_limitations: tuple[str, ...]
    explanation: str
    evaluated_at: str
    content_hash: str


@dataclass(frozen=True)
class CacheRetrievalResult:
    retrieval_result_id: str
    cache_query_id: str
    matches: tuple[CacheMatch, ...]
    reuse_evaluations: tuple[CacheReuseEvaluation, ...]
    selected_cache_record_ids: tuple[str, ...]
    exact_reuse_record_ids: tuple[str, ...]
    validation_required_record_ids: tuple[str, ...]
    partial_reuse_record_ids: tuple[str, ...]
    supporting_input_record_ids: tuple[str, ...]
    historical_only_record_ids: tuple[str, ...]
    rejected_record_ids: tuple[str, ...]
    overall_coverage_percent: float
    estimated_work_avoided: dict[str, Any]
    retrieved_at: str


@dataclass(frozen=True)
class CacheInvalidationRecord:
    cache_invalidation_id: str
    cache_record_id: str
    invalidation_type: str
    source_event_id: str
    source_information_record_id: str
    affected_fields: tuple[str, ...]
    affected_sections: tuple[str, ...]
    full_invalidation: bool
    prior_status: CacheRecordStatus
    new_status: CacheRecordStatus
    reason: str
    invalidated_at: str
    invalidated_by_type: str
    invalidated_by_id: str
    content_hash: str


@dataclass(frozen=True)
class CacheContradictionRecord:
    cache_contradiction_id: str
    cache_record_id: str
    contradicting_record_id: str
    contradiction_scope: str
    affected_fields: tuple[str, ...]
    affected_sections: tuple[str, ...]
    evidence_record_ids: tuple[str, ...]
    prior_status: CacheRecordStatus
    new_status: CacheRecordStatus
    reason: str
    detected_at: str
    resolved_at: str
    content_hash: str


@dataclass(frozen=True)
class CacheRetentionPolicy:
    retention_policy_id: str
    name: str
    hot_days: int
    warm_days: int
    archive_days: int
    quarantine_review_days: int
    deterministic_eviction_enabled: bool
    automatic_delete_enabled: bool
    created_at: str


@dataclass(frozen=True)
class CacheAccessRecord:
    cache_access_record_id: str
    cache_record_id: str
    cache_query_id: str
    requester_type: str
    requester_id: str
    mission_id: str
    workflow_id: str
    office_id: str
    access_type: str
    permitted: bool
    reuse_decision: CacheReuseDecision | None
    accessed_fields: tuple[str, ...]
    accessed_sections: tuple[str, ...]
    denial_reason: str
    accessed_at: str


class EnterpriseMemoryCache:
    """Governed reusable-memory layer; EO-CF remains freshness authority."""

    def __init__(self, freshness_engine: InformationFreshnessEngine) -> None:
        self._freshness = freshness_engine
        self._records: dict[str, CacheProductRecord] = {}
        self._product_key_index: dict[str, list[str]] = {}
        self._admission_requests: dict[str, CacheAdmissionRequest] = {}
        self._admission_decisions: list[CacheAdmissionDecision] = []
        self._retrieval_results: list[CacheRetrievalResult] = []
        self._invalidations: list[CacheInvalidationRecord] = []
        self._contradictions: list[CacheContradictionRecord] = []
        self._access: list[CacheAccessRecord] = []
        self._retention_policy = CacheRetentionPolicy("EMC-RET-DEFAULT", "Enterprise Memory Retention", 30, 180, 3650, 7, True, False, utc_timestamp())
        self._archival_records: list[dict[str, Any]] = []
        self._audit: list[dict[str, Any]] = []
        self._work_avoided = Decimal("0")
        self._cost_avoided = Decimal("0")

    def snapshot(self) -> dict[str, Any]:
        counts = {status.value: 0 for status in CacheRecordStatus}
        for record in self._records.values():
            counts[record.status.value] += 1
        latest = self._retrieval_results[-1] if self._retrieval_results else None
        return {
            "cacheName": "Enterprise Memory Cache",
            "engineeringOrder": "EO-CG",
            "status": "HEALTHY",
            "headerIndicators": {
                "cacheRecords": len(self._records),
                "validatedRecords": sum(1 for item in self._records.values() if item.cache_tier == CacheTier.VALIDATED),
                "candidateRecords": sum(1 for item in self._records.values() if item.cache_tier == CacheTier.CANDIDATE),
                "historicalRecords": sum(1 for item in self._records.values() if item.cache_tier == CacheTier.HISTORICAL),
                "archivedRecords": sum(1 for item in self._records.values() if item.cache_tier == CacheTier.ARCHIVED or item.status == CacheRecordStatus.ARCHIVED),
                "quarantinedRecords": sum(1 for item in self._records.values() if item.cache_tier == CacheTier.QUARANTINED or item.status == CacheRecordStatus.QUARANTINED),
                "invalidatedRecords": counts[CacheRecordStatus.INVALIDATED.value],
                "supersededRecords": counts[CacheRecordStatus.SUPERSEDED.value],
                "contradictedRecords": counts[CacheRecordStatus.CONTRADICTED.value],
                "cacheHits": sum(1 for item in self._access if item.permitted),
                "cacheMisses": sum(1 for item in self._retrieval_results if not item.selected_cache_record_ids),
                "workAvoided": float(self._work_avoided),
                "costAvoided": float(self._cost_avoided),
            },
            "memoryInventory": tuple(self._inventory_row(record) for record in self._records.values()),
            "admissionQueue": tuple(_public(item) for item in self._admission_decisions[-20:]),
            "retrievalResults": tuple(_public(item) for item in self._retrieval_results[-20:]),
            "reuseEvaluations": tuple(_public(eval_item) for result in self._retrieval_results[-10:] for eval_item in result.reuse_evaluations),
            "invalidationRecords": tuple(_public(item) for item in self._invalidations[-20:]),
            "contradictionRecords": tuple(_public(item) for item in self._contradictions[-20:]),
            "quarantineRecords": tuple(self._quarantine_row(record) for record in self._records.values() if record.status == CacheRecordStatus.QUARANTINED or record.cache_tier == CacheTier.QUARANTINED),
            "archivalRecords": tuple(self._archival_records[-20:]),
            "accessAudit": tuple(_public(item) for item in self._access[-25:]),
            "indexes": self._index_snapshot(),
            "repositoryMethods": self.repository_method_manifest(),
            "latestRetrieval": _public(latest) if latest else {},
            "metrics": {
                "recordsByStatus": counts,
                "admissions": len(self._admission_decisions),
                "retrievals": len(self._retrieval_results),
                "exactReuse": sum(1 for item in self._access if item.reuse_decision == CacheReuseDecision.REUSE_EXACT),
                "partialReuse": sum(1 for item in self._access if item.reuse_decision == CacheReuseDecision.REUSE_PARTIAL_SCOPE),
                "rejectedReuse": sum(1 for item in self._access if item.reuse_decision == CacheReuseDecision.REJECT_REUSE),
                "averageCoverage": round(sum(item.overall_coverage_percent for item in self._retrieval_results) / max(1, len(self._retrieval_results)), 4),
            },
            "retentionPolicy": _public(self._retention_policy),
            "securityAndIntegrity": {
                "contentHashRequiredForValidatedTier": True,
                "schemaRequiredForValidatedTier": True,
                "provenanceRequiredForValidatedTier": True,
                "unauthorizedAuthorityClaimsQuarantined": True,
                "automaticDeletesEnabled": self._retention_policy.automatic_delete_enabled,
            },
            "persistence": {
                "mode": "runtime_snapshot",
                "durableRepository": False,
                "restartRecovery": True,
                "indexRebuild": True,
                "duplicateSafeRecovery": True,
            },
            "lawCG": {
                "existenceEqualsReusability": False,
                "freshnessAuthority": "EO-CF",
                "validatedMemoryImmutable": True,
                "deterministicFirstRetrieval": True,
                "createsTruth": False,
                "environmentIsolation": True,
                "routineAiInvocations": 0,
                "officeWakeAuthority": False,
                "missionCreationAuthority": False,
                "expenditureAuthorizationAuthority": False,
            },
            "eoCHFeed": {
                "changedDependencies": tuple(item.source_information_record_id for item in self._invalidations[-20:] if item.source_information_record_id),
                "reusableScopes": tuple(eval_item.cache_record_id for result in self._retrieval_results[-10:] for eval_item in result.reuse_evaluations if eval_item.decision in {CacheReuseDecision.REUSE_EXACT, CacheReuseDecision.REUSE_PARTIAL_SCOPE}),
                "deltaRefreshCandidates": tuple(eval_item.cache_record_id for result in self._retrieval_results[-10:] for eval_item in result.reuse_evaluations if eval_item.decision == CacheReuseDecision.DELTA_REFRESH_REQUIRED),
            },
            "audit": tuple(self._audit[-50:]),
        }

    def admit_product(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = self._admission_request(payload)
        self._admission_requests[request.admission_request_id] = request
        corrections = self._admission_corrections(payload, request)
        duplicate = self._duplicate_for(payload, request)
        if duplicate:
            decision = self._admission_decision(request, False, None, None, ("duplicate_product",), "Exact duplicate already exists.", duplicate_record_id=duplicate)
            self._admission_decisions.append(decision)
            return {"decision": _public(decision), "record": {}}
        if corrections:
            hard_blocks = {"content_hash_missing", "provenance_missing", "authority_claim_unverified", "payload_missing"}
            tier = CacheTier.QUARANTINED if set(corrections) & hard_blocks else CacheTier.CANDIDATE
            status = CacheRecordStatus.QUARANTINED if tier == CacheTier.QUARANTINED else CacheRecordStatus.PENDING_ADMISSION
            decision = self._admission_decision(request, tier == CacheTier.CANDIDATE, tier, status, tuple(corrections), "Product requires correction before validated reuse.", corrections=tuple(corrections), quarantine=tier == CacheTier.QUARANTINED)
            self._admission_decisions.append(decision)
            if tier == CacheTier.CANDIDATE:
                record = self._record_from_payload(payload, request, tier, status)
                self._store_record(record)
                self._audit_event("candidate_admission", record.cache_record_id, ",".join(corrections))
                return {"decision": _public(decision), "record": _public(record)}
            if "content_hash_missing" not in corrections and "payload_missing" not in corrections and "provenance_missing" not in corrections:
                record = self._record_from_payload(payload, request, tier, status)
                self._store_record(record)
                self._audit_event("admission_quarantined", record.cache_record_id, ",".join(corrections))
                return {"decision": _public(decision), "record": _public(record)}
            self._audit_event("admission_quarantined", request.admission_request_id, ",".join(corrections))
            return {"decision": _public(decision), "record": {}}
        tier = request.proposed_tier if request.proposed_tier in {CacheTier.VALIDATED, CacheTier.AUTHORITATIVE_REFERENCE, CacheTier.HISTORICAL} else CacheTier.VALIDATED
        status = CacheRecordStatus.ACTIVE if tier in {CacheTier.VALIDATED, CacheTier.AUTHORITATIVE_REFERENCE} else CacheRecordStatus.ARCHIVED
        record = self._record_from_payload(payload, request, tier, status)
        self._store_record(record)
        self._register_freshness(record, payload)
        decision = self._admission_decision(request, True, tier, status, ("admitted",), "Product admitted to governed enterprise memory.", superseded_record_id=record.supersedes_cache_record_id)
        self._admission_decisions.append(decision)
        self._audit_event("product_admitted", record.cache_record_id, record.product_key)
        return {"decision": _public(decision), "record": _public(record)}

    def get_cache_record(self, record_id: str) -> dict[str, Any]:
        return _public(self._records[record_id])

    def get_product_by_key(self, product_key: str, version: int | None = None) -> dict[str, Any]:
        records = [self._records[item] for item in self._product_key_index.get(product_key, ()) if item in self._records]
        if version is not None:
            records = [item for item in records if item.product_version == version]
        if not records:
            return {}
        return _public(sorted(records, key=lambda item: item.product_version)[-1])

    def list_product_versions(self, product_key: str) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in sorted((self._records[record_id] for record_id in self._product_key_index.get(product_key, ()) if record_id in self._records), key=lambda item: item.product_version))

    def list_records_by_subject(self, subject_type: str = "", subject_id: str = "") -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._records.values() if (not subject_type or item.subject_type == subject_type) and (not subject_id or item.subject_id == subject_id))

    def list_records_by_product_type(self, product_type: CacheProductType | str) -> tuple[dict[str, Any], ...]:
        target = _product_type(product_type)
        return tuple(_public(item) for item in self._records.values() if item.product_type == target)

    def list_records_by_office(self, office_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._records.values() if item.producing_office_id == office_id)

    def list_records_by_mission(self, mission_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._records.values() if item.mission_id == mission_id)

    def list_records_by_workflow(self, workflow_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._records.values() if item.workflow_id == workflow_id)

    def list_records_by_environment(self, environment: CacheEnvironment | str) -> tuple[dict[str, Any], ...]:
        target = _environment(environment)
        return tuple(_public(item) for item in self._records.values() if item.environment == target)

    def list_records_by_status(self, status: CacheRecordStatus | str) -> tuple[dict[str, Any], ...]:
        target = _status(status)
        return tuple(_public(item) for item in self._records.values() if item.status == target)

    def list_records_by_tier(self, tier: CacheTier | str) -> tuple[dict[str, Any], ...]:
        target = _tier(tier)
        return tuple(_public(item) for item in self._records.values() if item.cache_tier == target)

    def list_invalidated_records(self) -> tuple[dict[str, Any], ...]:
        return self.list_records_by_status(CacheRecordStatus.INVALIDATED)

    def list_superseded_records(self) -> tuple[dict[str, Any], ...]:
        return self.list_records_by_status(CacheRecordStatus.SUPERSEDED)

    def list_contradicted_records(self) -> tuple[dict[str, Any], ...]:
        return self.list_records_by_status(CacheRecordStatus.CONTRADICTED)

    def list_quarantined_records(self) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._records.values() if item.status == CacheRecordStatus.QUARANTINED or item.cache_tier == CacheTier.QUARANTINED)

    def list_cache_queries(self) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._retrieval_results)

    def list_cache_hits(self) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._access if item.permitted)

    def list_cache_misses(self) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._retrieval_results if not item.selected_cache_record_ids)

    def get_product_lineage(self, record_id: str) -> dict[str, Any]:
        record = self._records[record_id]
        return {
            "cacheRecordId": record.cache_record_id,
            "productKey": record.product_key,
            "productVersion": record.product_version,
            "supersedes": record.supersedes_cache_record_id,
            "supersededBy": record.superseded_by_cache_record_id,
            "versions": self.list_product_versions(record.product_key),
        }

    def get_access_history(self, record_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._access if item.cache_record_id == record_id)

    def repository_method_manifest(self) -> tuple[str, ...]:
        return (
            "get_cache_record",
            "get_product_by_key",
            "list_product_versions",
            "list_records_by_subject",
            "list_records_by_product_type",
            "list_records_by_office",
            "list_records_by_mission",
            "list_records_by_workflow",
            "list_records_by_environment",
            "list_records_by_status",
            "list_records_by_tier",
            "list_invalidated_records",
            "list_superseded_records",
            "list_contradicted_records",
            "list_quarantined_records",
            "list_cache_queries",
            "list_cache_hits",
            "list_cache_misses",
            "get_product_lineage",
            "get_access_history",
        )

    def query(self, query_payload: dict[str, Any]) -> CacheRetrievalResult:
        query = self._query_from_dict(query_payload)
        candidates = self._candidate_matches(query)
        evaluations = tuple(self._reuse_evaluation(query, match) for match in candidates)
        selected = tuple(eval_item.cache_record_id for eval_item in evaluations if eval_item.decision in {CacheReuseDecision.REUSE_EXACT, CacheReuseDecision.REUSE_WITH_VALIDATION, CacheReuseDecision.REUSE_PARTIAL_SCOPE, CacheReuseDecision.USE_AS_SUPPORTING_INPUT})
        exact = tuple(item.cache_record_id for item in evaluations if item.decision == CacheReuseDecision.REUSE_EXACT)
        validation = tuple(item.cache_record_id for item in evaluations if item.decision == CacheReuseDecision.REUSE_WITH_VALIDATION)
        partial = tuple(item.cache_record_id for item in evaluations if item.decision == CacheReuseDecision.REUSE_PARTIAL_SCOPE)
        supporting = tuple(item.cache_record_id for item in evaluations if item.decision == CacheReuseDecision.USE_AS_SUPPORTING_INPUT)
        historical = tuple(item.cache_record_id for item in evaluations if item.decision == CacheReuseDecision.USE_HISTORICAL_ONLY)
        rejected = tuple(item.cache_record_id for item in evaluations if item.decision in {CacheReuseDecision.REJECT_REUSE, CacheReuseDecision.FULL_REFRESH_REQUIRED, CacheReuseDecision.DELTA_REFRESH_REQUIRED})
        coverage = round(sum(item.scope_coverage_percent for item in evaluations if item.cache_record_id in selected) / max(1, len(selected)), 4)
        result = CacheRetrievalResult(
            retrieval_result_id=f"EMC-RET-{len(self._retrieval_results) + 1:06d}",
            cache_query_id=query.cache_query_id,
            matches=candidates,
            reuse_evaluations=evaluations,
            selected_cache_record_ids=selected,
            exact_reuse_record_ids=exact,
            validation_required_record_ids=validation,
            partial_reuse_record_ids=partial,
            supporting_input_record_ids=supporting,
            historical_only_record_ids=historical,
            rejected_record_ids=rejected,
            overall_coverage_percent=coverage,
            estimated_work_avoided={"basis": "selected reusable cache records", "records": len(selected), "estimatedCostAvoided": round(len(selected) * 0.01, 4)},
            retrieved_at=utc_timestamp(),
        )
        self._retrieval_results.append(result)
        if selected:
            self._work_avoided += Decimal(len(selected))
            self._cost_avoided += Decimal(str(result.estimated_work_avoided["estimatedCostAvoided"]))
        for eval_item in evaluations:
            self._access_record(query, eval_item, eval_item.cache_record_id in selected)
        return result

    def invalidate(self, record_id: str, *, reason: str = "Commander invalidated cache record.", affected_fields: tuple[str, ...] = (), affected_sections: tuple[str, ...] = (), full: bool = False, source_information_record_id: str = "", actor: str = "Commander") -> CacheInvalidationRecord:
        record = self._records[record_id]
        new_status = CacheRecordStatus.INVALIDATED if full else CacheRecordStatus.PARTIALLY_INVALIDATED
        updated = replace(record, status=new_status)
        self._records[record_id] = updated
        invalidation = CacheInvalidationRecord(
            cache_invalidation_id=f"EMC-INV-{len(self._invalidations) + 1:06d}",
            cache_record_id=record_id,
            invalidation_type="full" if full else "partial",
            source_event_id="",
            source_information_record_id=source_information_record_id,
            affected_fields=affected_fields,
            affected_sections=affected_sections,
            full_invalidation=full,
            prior_status=record.status,
            new_status=new_status,
            reason=reason,
            invalidated_at=utc_timestamp(),
            invalidated_by_type="commander",
            invalidated_by_id=actor,
            content_hash="",
        )
        invalidation = _hash_invalidation(invalidation)
        self._invalidations.append(invalidation)
        if record.information_record_id:
            self._freshness.invalidate_record(record.information_record_id, "manual_invalidation", affected_fields=affected_fields, affected_sections=affected_sections, explanation=reason, full=full, actor_type="EnterpriseMemoryCache", actor_id=actor)
        self._audit_event("product_invalidated", record_id, reason)
        return invalidation

    def supersede(self, prior_record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        prior = self._records[prior_record_id]
        payload = dict(payload)
        payload["supersedesCacheRecordId"] = prior_record_id
        payload.setdefault("productKey", prior.product_key)
        admitted = self.admit_product(payload)
        new_record = admitted.get("record", {})
        if new_record:
            self._records[prior_record_id] = replace(prior, status=CacheRecordStatus.SUPERSEDED, superseded_by_cache_record_id=str(new_record["cache_record_id"]))
            self._audit_event("product_superseded", prior_record_id, str(new_record["cache_record_id"]))
        return admitted

    def register_contradiction(self, record_id: str, payload: dict[str, Any]) -> CacheContradictionRecord:
        record = self._records[record_id]
        new_status = CacheRecordStatus.CONTRADICTED
        self._records[record_id] = replace(record, status=new_status)
        contradiction = CacheContradictionRecord(
            cache_contradiction_id=f"EMC-CON-{len(self._contradictions) + 1:06d}",
            cache_record_id=record_id,
            contradicting_record_id=str(payload.get("contradictingRecordId", payload.get("contradicting_record_id", ""))),
            contradiction_scope=str(payload.get("contradictionScope", payload.get("contradiction_scope", "record"))),
            affected_fields=tuple(payload.get("affectedFields", payload.get("affected_fields", ())) or ()),
            affected_sections=tuple(payload.get("affectedSections", payload.get("affected_sections", ())) or ()),
            evidence_record_ids=tuple(payload.get("evidenceRecordIds", payload.get("evidence_record_ids", ())) or ()),
            prior_status=record.status,
            new_status=new_status,
            reason=str(payload.get("reason", "Contradicting cache evidence registered.")),
            detected_at=utc_timestamp(),
            resolved_at="",
            content_hash="",
        )
        contradiction = _hash_contradiction(contradiction)
        self._contradictions.append(contradiction)
        self._audit_event("contradiction_registered", record_id, contradiction.reason)
        return contradiction

    def quarantine_record(self, record_id: str, reason: str = "Commander quarantined cache record.") -> dict[str, Any]:
        record = self._records[record_id]
        self._records[record_id] = replace(record, cache_tier=CacheTier.QUARANTINED, status=CacheRecordStatus.QUARANTINED)
        self._audit_event("product_quarantined", record_id, reason)
        return _public(self._records[record_id])

    def archive_record(self, record_id: str, reason: str = "Retention policy archive.") -> dict[str, Any]:
        record = self._records[record_id]
        self._records[record_id] = replace(record, cache_tier=CacheTier.ARCHIVED, status=CacheRecordStatus.ARCHIVED)
        archival = {"archiveId": f"EMC-ARC-{len(self._archival_records) + 1:06d}", "cacheRecordId": record_id, "reason": reason, "archivedAt": utc_timestamp(), "priorStatus": record.status.value}
        self._archival_records.append(archival)
        self._audit_event("product_archived", record_id, reason)
        return archival

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._records = {}
        self._product_key_index = {}
        for item in snapshot.get("memoryInventory", ()):
            record = self._record_from_public(item)
            self._store_record(record)
        for item in snapshot.get("admissionQueue", ()):
            self._admission_decisions.append(self._admission_decision_from_dict(item))
        for item in snapshot.get("invalidationRecords", ()):
            self._invalidations.append(self._invalidation_from_dict(item))
        for item in snapshot.get("contradictionRecords", ()):
            self._contradictions.append(self._contradiction_from_dict(item))
        self._archival_records = list(snapshot.get("archivalRecords", ()))
        self._audit_event("restart_recovery", "EO-CG", "Enterprise Memory Cache restored from snapshot.")

    def seed_runtime_products(self, *, commander_briefing: dict[str, Any], performance_truth: dict[str, Any], timestamp_utc: str, environment: str) -> None:
        if commander_briefing.get("latestBriefingRecord") and "EMC-COMMANDER-BRIEFING" not in self._records:
            latest = commander_briefing["latestBriefingRecord"]
            self.admit_product(
                {
                    "cacheRecordId": "EMC-COMMANDER-BRIEFING",
                    "productReference": "commanderBriefingGenerator.latestBriefingRecord",
                    "productType": "mission_product",
                    "productSubtype": "commander_briefing",
                    "environment": environment,
                    "producingOfficeId": "Commander",
                    "producingServiceId": "CommanderBriefingGenerator",
                    "subjectType": "enterprise",
                    "subjectId": "ARGOS",
                    "title": "Latest Commander Briefing",
                    "summary": str(latest.get("executive_summary", "")),
                    "payloadReference": "commanderBriefingGenerator.latestBriefingRecord",
                    "payloadFormat": "json_reference",
                    "payloadSizeBytes": len(json.dumps(latest, default=str)),
                    "fieldManifest": ("overall_status", "executive_summary", "decisions_required"),
                    "sectionManifest": ("executive_summary", "risk_summary", "decisions_required"),
                    "schemaName": "CommanderBriefingRecord",
                    "schemaVersion": "EO-BN",
                    "confidence": 0.96,
                    "validationState": "VALID",
                    "sourceInformationRecordIds": ("IFR-COMMANDER-BRIEFING",),
                    "decisionUseClasses": ("commander_briefing", "historical_review"),
                    "contentHash": _content_hash(latest),
                    "createdAt": timestamp_utc,
                }
            )
        if "EMC-PORTFOLIO-TRUTH" not in self._records:
            self.admit_product(
                {
                    "cacheRecordId": "EMC-PORTFOLIO-TRUTH",
                    "productReference": "performanceTruthEngine.snapshot",
                    "productType": "portfolio_product",
                    "productSubtype": "portfolio_truth",
                    "environment": environment,
                    "producingOfficeId": "Trader",
                    "producingServiceId": "PerformanceTruthEngine",
                    "subjectType": "portfolio",
                    "subjectId": "PAPER-PORTFOLIO",
                    "title": "Portfolio Truth Snapshot",
                    "summary": "Authoritative local paper portfolio truth snapshot reference.",
                    "payloadReference": "performanceTruthEngine",
                    "payloadFormat": "json_reference",
                    "payloadSizeBytes": len(json.dumps(performance_truth, default=str)),
                    "fieldManifest": ("cash", "market_value", "positions"),
                    "sectionManifest": ("portfolioLedger", "positionRegistry"),
                    "schemaName": "PerformanceTruthSnapshot",
                    "schemaVersion": "paper",
                    "confidence": 0.98,
                    "validationState": "VALID",
                    "sourceInformationRecordIds": ("IFR-PORTFOLIO-TRUTH",),
                    "decisionUseClasses": ("commander_briefing", "historical_review"),
                    "contentHash": _content_hash(performance_truth),
                    "createdAt": timestamp_utc,
                }
            )

    def _admission_request(self, payload: dict[str, Any]) -> CacheAdmissionRequest:
        return CacheAdmissionRequest(
            admission_request_id=str(payload.get("admissionRequestId", payload.get("admission_request_id", f"EMC-ADM-REQ-{len(self._admission_requests) + 1:06d}"))),
            product_reference=str(payload.get("productReference", payload.get("product_reference", payload.get("payloadReference", "")))),
            product_type=_product_type(payload.get("productType", payload.get("product_type", CacheProductType.ENTERPRISE_PRODUCT.value))),
            product_subtype=str(payload.get("productSubtype", payload.get("product_subtype", "general"))),
            proposed_tier=_tier(payload.get("proposedTier", payload.get("proposed_tier", CacheTier.VALIDATED.value))),
            environment=_environment(payload.get("environment", CacheEnvironment.PAPER.value)),
            producing_office_id=str(payload.get("producingOfficeId", payload.get("producing_office_id", ""))),
            producing_service_id=str(payload.get("producingServiceId", payload.get("producing_service_id", ""))),
            mission_id=str(payload.get("missionId", payload.get("mission_id", ""))),
            workflow_id=str(payload.get("workflowId", payload.get("workflow_id", ""))),
            subject_type=str(payload.get("subjectType", payload.get("subject_type", ""))),
            subject_id=str(payload.get("subjectId", payload.get("subject_id", ""))),
            schema_name=str(payload.get("schemaName", payload.get("schema_name", ""))),
            schema_version=str(payload.get("schemaVersion", payload.get("schema_version", ""))),
            provenance=dict(payload.get("provenance", {}) or {}),
            validation_evidence=dict(payload.get("validationEvidence", payload.get("validation_evidence", {})) or {}),
            expected_reuse_value=str(payload.get("expectedReuseValue", payload.get("expected_reuse_value", "medium"))),
            retention_class=str(payload.get("retentionClass", payload.get("retention_class", "standard"))),
            submitted_at=str(payload.get("submittedAt", payload.get("submitted_at", utc_timestamp()))),
        )

    def _record_from_payload(self, payload: dict[str, Any], request: CacheAdmissionRequest, tier: CacheTier, status: CacheRecordStatus) -> CacheProductRecord:
        key = str(payload.get("productKey", payload.get("product_key", ""))) or _product_key(request, payload)
        version = len(self._product_key_index.get(key, ())) + 1
        record_id = str(payload.get("cacheRecordId", payload.get("cache_record_id", f"EMC-REC-{len(self._records) + 1:06d}")))
        content_hash = str(payload.get("contentHash", payload.get("content_hash", ""))) or _content_hash({"reference": request.product_reference, "summary": payload.get("summary", "")})
        info_id = str(payload.get("informationRecordId", payload.get("information_record_id", f"IFR-CACHE-{record_id}")))
        return CacheProductRecord(
            cache_record_id=record_id,
            product_type=request.product_type,
            product_subtype=request.product_subtype,
            cache_tier=tier,
            status=status,
            environment=request.environment,
            product_key=key,
            product_version=version,
            title=str(payload.get("title", request.product_subtype)),
            summary=str(payload.get("summary", "")),
            subject_type=request.subject_type,
            subject_id=request.subject_id,
            ticker=str(payload.get("ticker", "")),
            position_id=str(payload.get("positionId", payload.get("position_id", ""))),
            order_id=str(payload.get("orderId", payload.get("order_id", ""))),
            portfolio_id=str(payload.get("portfolioId", payload.get("portfolio_id", ""))),
            strategy_id=str(payload.get("strategyId", payload.get("strategy_id", ""))),
            producing_office_id=request.producing_office_id,
            producing_service_id=request.producing_service_id,
            mission_id=request.mission_id,
            mission_plan_id=str(payload.get("missionPlanId", payload.get("mission_plan_id", ""))),
            workflow_id=request.workflow_id,
            decision_object_id=str(payload.get("decisionObjectId", payload.get("decision_object_id", ""))),
            source_event_ids=tuple(payload.get("sourceEventIds", payload.get("source_event_ids", ())) or ()),
            source_information_record_ids=tuple(payload.get("sourceInformationRecordIds", payload.get("source_information_record_ids", ())) or ()),
            evidence_record_ids=tuple(payload.get("evidenceRecordIds", payload.get("evidence_record_ids", ())) or ()),
            schema_name=request.schema_name,
            schema_version=request.schema_version,
            payload_reference=str(payload.get("payloadReference", payload.get("payload_reference", request.product_reference))),
            payload_format=str(payload.get("payloadFormat", payload.get("payload_format", "json_reference"))),
            payload_size_bytes=int(payload.get("payloadSizeBytes", payload.get("payload_size_bytes", 0)) or 0),
            field_manifest=tuple(payload.get("fieldManifest", payload.get("field_manifest", ())) or ()),
            section_manifest=tuple(payload.get("sectionManifest", payload.get("section_manifest", ())) or ()),
            confidence=float(payload.get("confidence", 0.0)),
            validation_state=str(payload.get("validationState", payload.get("validation_state", "UNVERIFIED"))),
            information_record_id=info_id,
            freshness_policy_id="",
            freshness_policy_version=1,
            decision_use_classes=tuple(payload.get("decisionUseClasses", payload.get("decision_use_classes", ())) or ("tactical_analysis",)),
            prohibited_use_classes=tuple(payload.get("prohibitedUseClasses", payload.get("prohibited_use_classes", ())) or ()),
            dependency_record_ids=tuple(payload.get("dependencyRecordIds", payload.get("dependency_record_ids", ())) or ()),
            supersedes_cache_record_id=str(payload.get("supersedesCacheRecordId", payload.get("supersedes_cache_record_id", ""))),
            superseded_by_cache_record_id="",
            created_at=str(payload.get("createdAt", payload.get("created_at", utc_timestamp()))),
            admitted_at=utc_timestamp() if tier != CacheTier.CANDIDATE else "",
            last_accessed_at="",
            content_hash=content_hash,
            metadata_hash=_content_hash({"key": key, "subject": request.subject_id, "schema": request.schema_name, "version": version}),
        )

    def _store_record(self, record: CacheProductRecord) -> None:
        self._records[record.cache_record_id] = record
        self._product_key_index.setdefault(record.product_key, [])
        if record.cache_record_id not in self._product_key_index[record.product_key]:
            self._product_key_index[record.product_key].append(record.cache_record_id)
        if record.supersedes_cache_record_id and record.supersedes_cache_record_id in self._records:
            prior = self._records[record.supersedes_cache_record_id]
            self._records[prior.cache_record_id] = replace(prior, status=CacheRecordStatus.SUPERSEDED, superseded_by_cache_record_id=record.cache_record_id)

    def _register_freshness(self, record: CacheProductRecord, payload: dict[str, Any]) -> None:
        domain = _domain_for_product(record.product_type)
        authority = str(payload.get("sourceAuthorityClass", "validated_internal"))
        self._freshness.register_record(
            {
                "information_record_id": record.information_record_id,
                "domain": domain.value,
                "information_type": record.product_subtype,
                "subject_type": record.subject_type,
                "subject_id": record.subject_id,
                "ticker": record.ticker,
                "position_id": record.position_id,
                "order_id": record.order_id,
                "mission_id": record.mission_id,
                "workflow_id": record.workflow_id,
                "office_id": record.producing_office_id,
                "environment": record.environment.value,
                "source_system": record.producing_service_id or record.producing_office_id or "EnterpriseMemoryCache",
                "source_record_id": record.cache_record_id,
                "source_authority_class": authority,
                "observed_at": record.created_at,
                "validated_at": record.admitted_at or record.created_at,
                "source_version": str(record.product_version),
                "content_hash": record.content_hash,
                "confidence": record.confidence,
                "validation_state": record.validation_state,
                "payload_reference": record.payload_reference,
                "field_manifest": record.field_manifest,
                "section_manifest": record.section_manifest,
            }
        )

    def _admission_corrections(self, payload: dict[str, Any], request: CacheAdmissionRequest) -> list[str]:
        corrections = []
        if not request.product_reference and not payload.get("payloadReference"):
            corrections.append("payload_missing")
        if not request.producing_office_id and not request.producing_service_id:
            corrections.append("provenance_missing")
        if not request.subject_id or not request.subject_type:
            corrections.append("subject_missing")
        if not request.schema_name or not request.schema_version:
            corrections.append("schema_missing")
        if not payload.get("contentHash") and not payload.get("content_hash"):
            corrections.append("content_hash_missing")
        if float(payload.get("confidence", 0.0) or 0.0) < 0.5:
            corrections.append("confidence_low")
        authority = str(payload.get("sourceAuthorityClass", payload.get("source_authority_class", ""))).lower()
        service = f"{request.producing_service_id} {request.producing_office_id}".lower()
        if authority == "broker_confirmed" and "broker" not in service and "performance" not in service:
            corrections.append("authority_claim_unverified")
        return corrections

    def _duplicate_for(self, payload: dict[str, Any], request: CacheAdmissionRequest) -> str:
        content_hash = str(payload.get("contentHash", payload.get("content_hash", "")))
        for record in self._records.values():
            if content_hash and record.content_hash == content_hash:
                return record.cache_record_id
            if record.product_key == str(payload.get("productKey", "")) and record.payload_reference == request.product_reference:
                return record.cache_record_id
        return ""

    def _candidate_matches(self, query: CacheQuery) -> tuple[CacheMatch, ...]:
        matches: list[CacheMatch] = []
        for record in self._records.values():
            score = 0.0
            match_type = CacheMatchType.STRUCTURED_SIMILARITY
            if query.metadata_filters.get("cacheRecordId") == record.cache_record_id:
                score, match_type = 1.0, CacheMatchType.RECORD_ID
            elif query.metadata_filters.get("productKey") == record.product_key:
                score, match_type = 0.98, CacheMatchType.PRODUCT_KEY
            else:
                if query.subject_id and query.subject_id == record.subject_id:
                    score += 0.35
                    match_type = CacheMatchType.SUBJECT_PRODUCT_TYPE
                if query.requested_product_types and record.product_type in query.requested_product_types:
                    score += 0.25
                if query.requested_product_subtypes and record.product_subtype in query.requested_product_subtypes:
                    score += 0.15
                if query.mission_id and query.mission_id == record.mission_id:
                    score += 0.15
                    match_type = CacheMatchType.MISSION_LINEAGE
                if query.workflow_id and query.workflow_id == record.workflow_id:
                    score += 0.15
                    match_type = CacheMatchType.WORKFLOW_LINEAGE
                if set(query.requested_fields) & set(record.field_manifest):
                    score += 0.05
                    match_type = CacheMatchType.FIELD_SCOPE
                if set(query.requested_sections) & set(record.section_manifest):
                    score += 0.05
                    match_type = CacheMatchType.SECTION_SCOPE
            if query.exact_match_only and score < 0.98:
                continue
            if score <= 0:
                continue
            matched_fields = tuple(field for field in query.requested_fields if field in record.field_manifest) or (record.field_manifest if not query.requested_fields else ())
            missing_fields = tuple(field for field in query.requested_fields if field not in record.field_manifest)
            matched_sections = tuple(section for section in query.requested_sections if section in record.section_manifest) or (record.section_manifest if not query.requested_sections else ())
            missing_sections = tuple(section for section in query.requested_sections if section not in record.section_manifest)
            compatible_schema = not query.required_schema_name or (record.schema_name == query.required_schema_name and (not query.required_schema_version or record.schema_version == query.required_schema_version))
            matches.append(
                CacheMatch(
                    cache_match_id=f"EMC-MAT-{len(self._retrieval_results) + 1:06d}-{len(matches) + 1:03d}",
                    cache_query_id=query.cache_query_id,
                    cache_record_id=record.cache_record_id,
                    match_type=match_type,
                    match_score=round(min(1.0, score), 4),
                    exact_subject_match=bool(query.subject_id and query.subject_id == record.subject_id),
                    exact_product_type_match=bool(query.requested_product_types and record.product_type in query.requested_product_types),
                    exact_scope_match=not missing_fields and not missing_sections,
                    exact_environment_match=query.environment == record.environment,
                    schema_compatible=compatible_schema,
                    matched_fields=matched_fields,
                    missing_fields=missing_fields,
                    matched_sections=matched_sections,
                    missing_sections=missing_sections,
                    match_reason=f"{match_type.value} score {round(min(1.0, score), 4)}",
                    created_at=utc_timestamp(),
                )
            )
        return tuple(sorted(matches, key=lambda item: item.match_score, reverse=True)[: query.maximum_results])

    def _reuse_evaluation(self, query: CacheQuery, match: CacheMatch) -> CacheReuseEvaluation:
        record = self._records[match.cache_record_id]
        freshness = self._freshness.evaluate_record(
            record.information_record_id,
            {
                "decisionUseClass": query.decision_use_class,
                "missionType": query.mission_type,
                "subjectType": query.subject_type or record.subject_type,
                "subjectId": query.subject_id or record.subject_id,
                "ticker": query.ticker or record.ticker,
                "positionId": query.position_id or record.position_id,
                "orderId": query.order_id or record.order_id,
                "requestedFields": query.requested_fields,
                "requestedSections": query.requested_sections,
                "environment": query.environment.value,
                "requiredConfidence": query.minimum_confidence if query.minimum_confidence is not None else record.confidence,
            },
        )
        environment_ok = query.environment == record.environment or (query.allow_historical and record.environment in {CacheEnvironment.REPLAY, CacheEnvironment.SIMULATION, CacheEnvironment.TEST})
        schema_ok = match.schema_compatible
        confidence_ok = query.minimum_confidence is None or record.confidence >= query.minimum_confidence
        access_ok = query.decision_use_class not in record.prohibited_use_classes and record.status not in {CacheRecordStatus.INVALIDATED, CacheRecordStatus.QUARANTINED, CacheRecordStatus.DELETED_TOMBSTONE, CacheRecordStatus.CONTRADICTED} and record.cache_tier != CacheTier.QUARANTINED
        decision = CacheReuseDecision.REJECT_REUSE
        limitations: list[str] = []
        if not environment_ok:
            limitations.append("environment_mismatch")
        if not schema_ok:
            limitations.append("schema_incompatible")
        if not confidence_ok:
            limitations.append("confidence_below_query")
        if not access_ok:
            limitations.append("access_or_status_blocked")
        if freshness.status == FreshnessStatus.SUPERSEDED:
            decision = CacheReuseDecision.USE_HISTORICAL_ONLY if query.allow_historical else CacheReuseDecision.REJECT_REUSE
        elif freshness.status in {FreshnessStatus.CONTRADICTED, FreshnessStatus.UNUSABLE, FreshnessStatus.UNVERIFIED}:
            decision = CacheReuseDecision.REJECT_REUSE
        elif environment_ok and schema_ok and confidence_ok and access_ok and freshness.status == FreshnessStatus.FRESH and match.exact_scope_match:
            decision = CacheReuseDecision.REUSE_EXACT
        elif environment_ok and schema_ok and confidence_ok and access_ok and freshness.status == FreshnessStatus.VALIDATION_REQUIRED and query.allow_limited_use:
            decision = CacheReuseDecision.REUSE_WITH_VALIDATION
        elif environment_ok and schema_ok and confidence_ok and access_ok and freshness.status in {FreshnessStatus.FRESH_LIMITED_USE, FreshnessStatus.PARTIALLY_STALE} and query.allow_limited_use:
            decision = CacheReuseDecision.REUSE_PARTIAL_SCOPE if match.matched_fields or match.matched_sections else CacheReuseDecision.USE_AS_SUPPORTING_INPUT
        elif freshness.recommended_action in {FreshnessAction.PARTIAL_REFRESH, FreshnessAction.REFRESH_DEPENDENCIES}:
            decision = CacheReuseDecision.DELTA_REFRESH_REQUIRED
        elif freshness.recommended_action in {FreshnessAction.FULL_REFRESH, FreshnessAction.ACQUIRE_NEW_SOURCE, FreshnessAction.BLOCK_USE}:
            decision = CacheReuseDecision.FULL_REFRESH_REQUIRED
        scope_total = max(1, len(query.requested_fields) + len(query.requested_sections))
        scope_hit = len(match.matched_fields) + len(match.matched_sections)
        coverage = 1.0 if not query.requested_fields and not query.requested_sections else round(scope_hit / scope_total, 4)
        evaluation = CacheReuseEvaluation(
            cache_reuse_evaluation_id=f"EMC-REU-{len(self._retrieval_results) + 1:06d}-{match.cache_record_id}",
            cache_query_id=query.cache_query_id,
            cache_record_id=record.cache_record_id,
            freshness_decision_id=freshness.freshness_decision_id,
            decision=decision,
            reusable_fields=match.matched_fields if decision != CacheReuseDecision.REJECT_REUSE else (),
            non_reusable_fields=match.missing_fields,
            reusable_sections=match.matched_sections if decision != CacheReuseDecision.REJECT_REUSE else (),
            non_reusable_sections=match.missing_sections,
            validation_requirements=("freshness_validation",) if decision == CacheReuseDecision.REUSE_WITH_VALIDATION else (),
            refresh_requirements=tuple(freshness.refresh_scope.get("sections", ())) + tuple(freshness.refresh_scope.get("fields", ())) if isinstance(freshness.refresh_scope, dict) else (),
            scope_coverage_percent=coverage,
            confidence_satisfied=confidence_ok,
            environment_satisfied=environment_ok,
            schema_satisfied=schema_ok,
            authority_satisfied=freshness.source_authority_satisfied,
            access_satisfied=access_ok,
            decision_use_limitations=tuple(limitations),
            explanation=f"Cache reuse decision {decision.value}; freshness {freshness.status.value}.",
            evaluated_at=utc_timestamp(),
            content_hash="",
        )
        return _hash_reuse(evaluation)

    def _access_record(self, query: CacheQuery, evaluation: CacheReuseEvaluation, permitted: bool) -> None:
        record = self._records[evaluation.cache_record_id]
        self._records[record.cache_record_id] = replace(record, last_accessed_at=utc_timestamp())
        self._access.append(
            CacheAccessRecord(
                cache_access_record_id=f"EMC-ACC-{len(self._access) + 1:06d}",
                cache_record_id=record.cache_record_id,
                cache_query_id=query.cache_query_id,
                requester_type=query.requester_type,
                requester_id=query.requester_id,
                mission_id=query.mission_id,
                workflow_id=query.workflow_id,
                office_id=query.office_id,
                access_type="retrieval",
                permitted=permitted,
                reuse_decision=evaluation.decision,
                accessed_fields=evaluation.reusable_fields,
                accessed_sections=evaluation.reusable_sections,
                denial_reason="" if permitted else evaluation.explanation,
                accessed_at=utc_timestamp(),
            )
        )

    def _query_from_dict(self, item: dict[str, Any]) -> CacheQuery:
        return CacheQuery(
            cache_query_id=str(item.get("cacheQueryId", item.get("cache_query_id", f"EMC-QRY-{len(self._retrieval_results) + 1:06d}"))),
            requester_type=str(item.get("requesterType", item.get("requester_type", "system"))),
            requester_id=str(item.get("requesterId", item.get("requester_id", "Commander"))),
            mission_id=str(item.get("missionId", item.get("mission_id", ""))),
            mission_type=str(item.get("missionType", item.get("mission_type", ""))),
            workflow_id=str(item.get("workflowId", item.get("workflow_id", ""))),
            office_id=str(item.get("officeId", item.get("office_id", ""))),
            decision_use_class=str(item.get("decisionUseClass", item.get("decision_use_class", "tactical_analysis"))),
            environment=_environment(item.get("environment", CacheEnvironment.PAPER.value)),
            subject_type=str(item.get("subjectType", item.get("subject_type", ""))),
            subject_id=str(item.get("subjectId", item.get("subject_id", ""))),
            ticker=str(item.get("ticker", "")),
            position_id=str(item.get("positionId", item.get("position_id", ""))),
            order_id=str(item.get("orderId", item.get("order_id", ""))),
            strategy_id=str(item.get("strategyId", item.get("strategy_id", ""))),
            requested_product_types=tuple(_product_type(value) for value in item.get("requestedProductTypes", item.get("requested_product_types", ())) or ()),
            requested_product_subtypes=tuple(item.get("requestedProductSubtypes", item.get("requested_product_subtypes", ())) or ()),
            requested_fields=tuple(item.get("requestedFields", item.get("requested_fields", ())) or ()),
            requested_sections=tuple(item.get("requestedSections", item.get("requested_sections", ())) or ()),
            required_schema_name=str(item.get("requiredSchemaName", item.get("required_schema_name", ""))),
            required_schema_version=str(item.get("requiredSchemaVersion", item.get("required_schema_version", ""))),
            minimum_confidence=float(item["minimumConfidence"]) if "minimumConfidence" in item else (float(item["minimum_confidence"]) if "minimum_confidence" in item else None),
            maximum_results=max(1, int(item.get("maximumResults", item.get("maximum_results", 10)) or 10)),
            exact_match_only=bool(item.get("exactMatchOnly", item.get("exact_match_only", False))),
            allow_similarity=bool(item.get("allowSimilarity", item.get("allow_similarity", True))),
            allow_historical=bool(item.get("allowHistorical", item.get("allow_historical", False))),
            allow_limited_use=bool(item.get("allowLimitedUse", item.get("allow_limited_use", True))),
            query_terms=tuple(item.get("queryTerms", item.get("query_terms", ())) or ()),
            metadata_filters=dict(item.get("metadataFilters", item.get("metadata_filters", {})) or {}),
            requested_at=str(item.get("requestedAt", item.get("requested_at", utc_timestamp()))),
        )

    def _admission_decision(self, request: CacheAdmissionRequest, admitted: bool, tier: CacheTier | None, status: CacheRecordStatus | None, reasons: tuple[str, ...], explanation: str, *, corrections: tuple[str, ...] = (), quarantine: bool = False, duplicate_record_id: str = "", superseded_record_id: str = "") -> CacheAdmissionDecision:
        decision = CacheAdmissionDecision(f"EMC-ADM-{len(self._admission_decisions) + 1:06d}", request.admission_request_id, admitted, tier, status, duplicate_record_id, superseded_record_id, reasons, explanation, corrections, quarantine, utc_timestamp(), "")
        return _hash_admission(decision)

    def _admission_decision_from_dict(self, item: dict[str, Any]) -> CacheAdmissionDecision:
        return CacheAdmissionDecision(str(item.get("admission_decision_id", "")), str(item.get("admission_request_id", "")), bool(item.get("admitted", False)), _tier(item["assigned_tier"]) if item.get("assigned_tier") else None, _status(item["assigned_status"]) if item.get("assigned_status") else None, str(item.get("duplicate_record_id", "")), str(item.get("superseded_record_id", "")), tuple(item.get("reason_codes", ())), str(item.get("explanation", "")), tuple(item.get("required_corrections", ())), bool(item.get("quarantine_required", False)), str(item.get("decided_at", "")), str(item.get("content_hash", "")))

    def _record_from_public(self, item: dict[str, Any]) -> CacheProductRecord:
        return CacheProductRecord(
            cache_record_id=str(item["cache_record_id"]),
            product_type=_product_type(item["product_type"]),
            product_subtype=str(item["product_subtype"]),
            cache_tier=_tier(item["cache_tier"]),
            status=_status(item["status"]),
            environment=_environment(item["environment"]),
            product_key=str(item["product_key"]),
            product_version=int(item["product_version"]),
            title=str(item.get("title", "")),
            summary=str(item.get("summary", "")),
            subject_type=str(item.get("subject_type", "")),
            subject_id=str(item.get("subject_id", "")),
            ticker=str(item.get("ticker", "")),
            position_id=str(item.get("position_id", "")),
            order_id=str(item.get("order_id", "")),
            portfolio_id=str(item.get("portfolio_id", "")),
            strategy_id=str(item.get("strategy_id", "")),
            producing_office_id=str(item.get("producing_office_id", "")),
            producing_service_id=str(item.get("producing_service_id", "")),
            mission_id=str(item.get("mission_id", "")),
            mission_plan_id=str(item.get("mission_plan_id", "")),
            workflow_id=str(item.get("workflow_id", "")),
            decision_object_id=str(item.get("decision_object_id", "")),
            source_event_ids=tuple(item.get("source_event_ids", ())),
            source_information_record_ids=tuple(item.get("source_information_record_ids", ())),
            evidence_record_ids=tuple(item.get("evidence_record_ids", ())),
            schema_name=str(item.get("schema_name", "")),
            schema_version=str(item.get("schema_version", "")),
            payload_reference=str(item.get("payload_reference", "")),
            payload_format=str(item.get("payload_format", "")),
            payload_size_bytes=int(item.get("payload_size_bytes", 0)),
            field_manifest=tuple(item.get("field_manifest", ())),
            section_manifest=tuple(item.get("section_manifest", ())),
            confidence=float(item.get("confidence", 0.0)),
            validation_state=str(item.get("validation_state", "")),
            information_record_id=str(item.get("information_record_id", "")),
            freshness_policy_id=str(item.get("freshness_policy_id", "")),
            freshness_policy_version=int(item.get("freshness_policy_version", 1)),
            decision_use_classes=tuple(item.get("decision_use_classes", ())),
            prohibited_use_classes=tuple(item.get("prohibited_use_classes", ())),
            dependency_record_ids=tuple(item.get("dependency_record_ids", ())),
            supersedes_cache_record_id=str(item.get("supersedes_cache_record_id", "")),
            superseded_by_cache_record_id=str(item.get("superseded_by_cache_record_id", "")),
            created_at=str(item.get("created_at", "")),
            admitted_at=str(item.get("admitted_at", "")),
            last_accessed_at=str(item.get("last_accessed_at", "")),
            content_hash=str(item.get("content_hash", "")),
            metadata_hash=str(item.get("metadata_hash", "")),
        )

    def _invalidation_from_dict(self, item: dict[str, Any]) -> CacheInvalidationRecord:
        return CacheInvalidationRecord(str(item["cache_invalidation_id"]), str(item["cache_record_id"]), str(item["invalidation_type"]), str(item.get("source_event_id", "")), str(item.get("source_information_record_id", "")), tuple(item.get("affected_fields", ())), tuple(item.get("affected_sections", ())), bool(item.get("full_invalidation", False)), _status(item["prior_status"]), _status(item["new_status"]), str(item.get("reason", "")), str(item.get("invalidated_at", "")), str(item.get("invalidated_by_type", "")), str(item.get("invalidated_by_id", "")), str(item.get("content_hash", "")))

    def _contradiction_from_dict(self, item: dict[str, Any]) -> CacheContradictionRecord:
        return CacheContradictionRecord(str(item["cache_contradiction_id"]), str(item["cache_record_id"]), str(item.get("contradicting_record_id", "")), str(item.get("contradiction_scope", "")), tuple(item.get("affected_fields", ())), tuple(item.get("affected_sections", ())), tuple(item.get("evidence_record_ids", ())), _status(item["prior_status"]), _status(item["new_status"]), str(item.get("reason", "")), str(item.get("detected_at", "")), str(item.get("resolved_at", "")), str(item.get("content_hash", "")))

    def _inventory_row(self, record: CacheProductRecord) -> dict[str, Any]:
        return _public(record) | {"matchCount": sum(1 for access in self._access if access.cache_record_id == record.cache_record_id), "currentFreshnessStatus": self._freshness.get_current_status(record.information_record_id)}

    def _quarantine_row(self, record: CacheProductRecord) -> dict[str, Any]:
        latest_admission = next((item for item in reversed(self._admission_decisions) if item.admission_request_id in self._admission_requests and self._admission_requests[item.admission_request_id].product_reference == record.product_reference), None)
        return {"cacheRecordId": record.cache_record_id, "productKey": record.product_key, "status": record.status.value, "tier": record.cache_tier.value, "reasonCodes": latest_admission.reason_codes if latest_admission else (), "reviewRequired": True}

    def _index_snapshot(self) -> dict[str, Any]:
        return {
            "productKeys": len(self._product_key_index),
            "subjects": sorted({record.subject_id for record in self._records.values() if record.subject_id}),
            "productTypes": sorted({record.product_type.value for record in self._records.values()}),
            "environments": sorted({record.environment.value for record in self._records.values()}),
        }

    def _audit_event(self, action: str, record_id: str, reason: str) -> None:
        self._audit.append({"auditId": f"EMC-AUD-{len(self._audit) + 1:06d}", "timestamp": utc_timestamp(), "action": action, "recordId": record_id, "reason": reason})


def _product_key(request: CacheAdmissionRequest, payload: dict[str, Any]) -> str:
    scope = str(payload.get("scopeKey", payload.get("scope_key", "full_product")))
    strategy = str(payload.get("strategyId", payload.get("strategy_id", "")))
    return ":".join((request.environment.value, request.subject_type or "subject", request.subject_id or "unknown", request.product_type.value, request.product_subtype, scope, strategy))


def _domain_for_product(product_type: CacheProductType) -> InformationDomain:
    if product_type in {CacheProductType.PORTFOLIO_PRODUCT, CacheProductType.POSITION_PRODUCT}:
        return InformationDomain.PORTFOLIO if product_type == CacheProductType.PORTFOLIO_PRODUCT else InformationDomain.POSITION
    if product_type in {CacheProductType.OFFICE_REPORT, CacheProductType.DECISION_PRODUCT, CacheProductType.STRUCTURED_CALCULATION}:
        return InformationDomain.ANALYTICAL_PRODUCT
    if product_type in {CacheProductType.MISSION_PRODUCT, CacheProductType.WORKFLOW_PRODUCT}:
        return InformationDomain.MISSION_PRODUCT
    if product_type == CacheProductType.POLICY_PRODUCT:
        return InformationDomain.POLICY
    if product_type in {CacheProductType.HISTORICAL_PRODUCT, CacheProductType.REPLAY_PRODUCT, CacheProductType.TRAINING_PRODUCT}:
        return InformationDomain.HISTORICAL
    return InformationDomain.INTELLIGENCE


def _public(item: Any) -> dict[str, Any]:
    raw = asdict(item)
    return {key: _json_value(value) for key, value in raw.items()}


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return tuple(_json_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _content_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _hash_admission(item: CacheAdmissionDecision) -> CacheAdmissionDecision:
    return replace(item, content_hash=_content_hash(_public(replace(item, content_hash=""))))


def _hash_reuse(item: CacheReuseEvaluation) -> CacheReuseEvaluation:
    return replace(item, content_hash=_content_hash(_public(replace(item, content_hash=""))))


def _hash_invalidation(item: CacheInvalidationRecord) -> CacheInvalidationRecord:
    return replace(item, content_hash=_content_hash(_public(replace(item, content_hash=""))))


def _hash_contradiction(item: CacheContradictionRecord) -> CacheContradictionRecord:
    return replace(item, content_hash=_content_hash(_public(replace(item, content_hash=""))))


def _product_type(value: Any) -> CacheProductType:
    try:
        return value if isinstance(value, CacheProductType) else CacheProductType(str(value))
    except ValueError:
        return CacheProductType.ENTERPRISE_PRODUCT


def _tier(value: Any) -> CacheTier:
    try:
        return value if isinstance(value, CacheTier) else CacheTier(str(value))
    except ValueError:
        return CacheTier.CANDIDATE


def _status(value: Any) -> CacheRecordStatus:
    try:
        return value if isinstance(value, CacheRecordStatus) else CacheRecordStatus(str(value))
    except ValueError:
        return CacheRecordStatus.PENDING_ADMISSION


def _environment(value: Any) -> CacheEnvironment:
    try:
        return value if isinstance(value, CacheEnvironment) else CacheEnvironment(str(value))
    except ValueError:
        return CacheEnvironment.DEVELOPMENT
