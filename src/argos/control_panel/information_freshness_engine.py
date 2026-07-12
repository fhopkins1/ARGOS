"""Information Freshness Engine for ARGOS EO-CF."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp


class InformationDomain(str, Enum):
    MARKET = "market"
    BROKER = "broker"
    ORDER = "order"
    POSITION = "position"
    PORTFOLIO = "portfolio"
    RISK = "risk"
    FUNDAMENTAL = "fundamental"
    CORPORATE = "corporate"
    FILING = "filing"
    INTELLIGENCE = "intelligence"
    ANALYTICAL_PRODUCT = "analytical_product"
    MISSION_PRODUCT = "mission_product"
    POLICY = "policy"
    CONFIGURATION = "configuration"
    ENTERPRISE_HEALTH = "enterprise_health"
    HISTORICAL = "historical"


class FreshnessStatus(str, Enum):
    FRESH = "fresh"
    FRESH_LIMITED_USE = "fresh_limited_use"
    VALIDATION_REQUIRED = "validation_required"
    PARTIALLY_STALE = "partially_stale"
    STALE = "stale"
    SUPERSEDED = "superseded"
    CONTRADICTED = "contradicted"
    UNVERIFIED = "unverified"
    UNUSABLE = "unusable"
    UNKNOWN = "unknown"


class FreshnessAction(str, Enum):
    REUSE_EXACT = "reuse_exact"
    REUSE_WITH_VALIDATION = "reuse_with_validation"
    REUSE_LIMITED_SCOPE = "reuse_limited_scope"
    REFRESH_DEPENDENCIES = "refresh_dependencies"
    PARTIAL_REFRESH = "partial_refresh"
    FULL_REFRESH = "full_refresh"
    ACQUIRE_NEW_SOURCE = "acquire_new_source"
    RESOLVE_CONTRADICTION = "resolve_contradiction"
    BLOCK_USE = "block_use"
    DEFER = "defer"
    NO_ACTION = "no_action"


class SourceAuthorityClass(str, Enum):
    BROKER_CONFIRMED = "broker_confirmed"
    REGULATORY_PRIMARY = "regulatory_primary"
    COMPANY_PRIMARY = "company_primary"
    MARKET_DATA_PRIMARY = "market_data_primary"
    ENTERPRISE_TRUTH = "enterprise_truth"
    VALIDATED_INTERNAL = "validated_internal"
    APPROVED_SECONDARY = "approved_secondary"
    UNVALIDATED_SECONDARY = "unvalidated_secondary"
    USER_PROVIDED = "user_provided"
    SIMULATED = "simulated"
    UNKNOWN = "unknown"


class DecisionUseClass(str, Enum):
    LIVE_ORDER_ACTION = "live_order_action"
    POSITION_SAFETY = "position_safety"
    BROKER_RECONCILIATION = "broker_reconciliation"
    RISK_ENFORCEMENT = "risk_enforcement"
    TRADE_ENTRY = "trade_entry"
    TRADE_EXIT = "trade_exit"
    PORTFOLIO_ALLOCATION = "portfolio_allocation"
    TACTICAL_ANALYSIS = "tactical_analysis"
    STRATEGIC_ANALYSIS = "strategic_analysis"
    COMMANDER_BRIEFING = "commander_briefing"
    HISTORICAL_REVIEW = "historical_review"
    TRAINING = "training"
    REPLAY = "replay"


class InvalidationReason(str, Enum):
    TIME_WINDOW_EXPIRED = "time_window_expired"
    SOURCE_SUPERSEDED = "source_superseded"
    SOURCE_CORRECTED = "source_corrected"
    CONTRADICTORY_EVIDENCE = "contradictory_evidence"
    DEPENDENCY_STALE = "dependency_stale"
    DEPENDENCY_INVALIDATED = "dependency_invalidated"
    SUBJECT_CHANGED = "subject_changed"
    POSITION_CHANGED = "position_changed"
    ORDER_CHANGED = "order_changed"
    MARKET_CHANGED = "market_changed"
    POLICY_CHANGED = "policy_changed"
    CONFIGURATION_CHANGED = "configuration_changed"
    DATA_QUALITY_FAILURE = "data_quality_failure"
    SOURCE_UNAVAILABLE = "source_unavailable"
    HASH_MISMATCH = "hash_mismatch"
    MANUAL_INVALIDATION = "manual_invalidation"
    EVENT_TRIGGERED = "event_triggered"


@dataclass(frozen=True)
class InformationRecord:
    information_record_id: str
    domain: InformationDomain
    information_type: str
    schema_name: str
    schema_version: str
    subject_type: str
    subject_id: str
    ticker: str
    position_id: str
    order_id: str
    mission_id: str
    workflow_id: str
    office_id: str
    environment: str
    source_system: str
    source_record_id: str
    source_authority_class: SourceAuthorityClass
    source_published_at: str
    source_effective_at: str
    observed_at: str
    acquired_at: str
    validated_at: str
    source_version: str
    content_hash: str
    confidence: float
    validation_state: str
    payload_reference: str
    field_manifest: tuple[str, ...]
    section_manifest: tuple[str, ...]
    policy_id: str
    policy_version: int
    supersedes_record_id: str
    superseded_by_record_id: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class FreshnessPolicy:
    policy_id: str
    version: int
    name: str
    description: str
    domain: InformationDomain
    information_type: str
    decision_use_class: DecisionUseClass | None
    mission_types: tuple[str, ...]
    subject_types: tuple[str, ...]
    maximum_age_seconds: int | None
    validation_age_seconds: int | None
    limited_use_age_seconds: int | None
    market_hours_maximum_age_seconds: int | None
    after_hours_maximum_age_seconds: int | None
    open_position_maximum_age_seconds: int | None
    active_order_maximum_age_seconds: int | None
    minimum_confidence: float
    minimum_source_authority: SourceAuthorityClass
    required_dependencies: tuple[str, ...]
    invalidating_event_types: tuple[str, ...]
    supersession_rule: str
    contradiction_policy: str
    field_overrides: dict[str, dict[str, Any]]
    section_overrides: dict[str, dict[str, Any]]
    stale_action: FreshnessAction
    partial_stale_action: FreshnessAction
    contradiction_action: FreshnessAction
    operating_mode_overrides: dict[str, dict[str, Any]]
    enabled: bool
    effective_at: str
    expires_at: str
    created_by: str
    created_at: str
    reason: str
    content_hash: str


@dataclass(frozen=True)
class FreshnessEvaluationContext:
    evaluation_context_id: str
    decision_use_class: DecisionUseClass
    mission_type: str
    subject_type: str
    subject_id: str
    ticker: str
    position_id: str
    order_id: str
    operating_mode: str
    market_state: str
    market_calendar_id: str
    open_position: bool
    active_order: bool
    safety_critical: bool
    required_confidence: float | None
    required_source_authority: SourceAuthorityClass | None
    requested_fields: tuple[str, ...]
    requested_sections: tuple[str, ...]
    environment: str
    evaluation_requested_at: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class DependencyLink:
    dependency_link_id: str
    dependent_record_id: str
    dependency_record_id: str
    dependency_type: str
    required: bool
    affected_fields: tuple[str, ...]
    affected_sections: tuple[str, ...]
    invalidation_behavior: str
    maximum_dependency_age_seconds: int | None
    created_at: str
    content_hash: str


@dataclass(frozen=True)
class FreshnessDecision:
    freshness_decision_id: str
    information_record_id: str
    evaluation_context_id: str
    policy_id: str
    policy_version: int
    status: FreshnessStatus
    recommended_action: FreshnessAction
    evaluated_at: str
    chronological_age_seconds: int | None
    effective_age_seconds: int | None
    age_limit_seconds: int | None
    validation_limit_seconds: int | None
    source_authority_satisfied: bool
    confidence_satisfied: bool
    provenance_satisfied: bool
    stale_dependency_ids: tuple[str, ...]
    invalid_dependency_ids: tuple[str, ...]
    contradictory_record_ids: tuple[str, ...]
    superseding_record_id: str
    fresh_fields: tuple[str, ...]
    stale_fields: tuple[str, ...]
    unknown_fields: tuple[str, ...]
    fresh_sections: tuple[str, ...]
    stale_sections: tuple[str, ...]
    unknown_sections: tuple[str, ...]
    usable_for_requested_scope: bool
    reusable_scope: dict[str, Any]
    refresh_scope: dict[str, Any]
    reason_codes: tuple[str, ...]
    explanation: str
    expires_at: str
    next_evaluation_at: str
    content_hash: str


@dataclass(frozen=True)
class InvalidationRecord:
    invalidation_id: str
    information_record_id: str
    reason: InvalidationReason
    source_event_id: str
    source_record_id: str
    source_policy_id: str
    affected_fields: tuple[str, ...]
    affected_sections: tuple[str, ...]
    full_invalidation: bool
    invalidated_at: str
    invalidated_by_type: str
    invalidated_by_id: str
    explanation: str
    metadata: dict[str, Any]
    content_hash: str


@dataclass(frozen=True)
class ContradictionRecord:
    contradiction_id: str
    record_a_id: str
    record_b_id: str
    contradiction_type: str
    affected_fields: tuple[str, ...]
    affected_sections: tuple[str, ...]
    materiality: str
    resolution_required: bool
    preferred_record_id: str
    preference_reason: str
    detected_at: str
    resolved_at: str
    resolution_type: str
    resolution_summary: str
    content_hash: str


class InformationFreshnessEngine:
    """Central deterministic freshness evaluator; never retrieves data or starts work."""

    def __init__(self) -> None:
        self._policies: dict[str, FreshnessPolicy] = {}
        self._policy_versions: list[FreshnessPolicy] = []
        self._records: dict[str, InformationRecord] = {}
        self._contexts: dict[str, FreshnessEvaluationContext] = {}
        self._decisions: list[FreshnessDecision] = []
        self._dependencies: dict[str, DependencyLink] = {}
        self._invalidations: list[InvalidationRecord] = []
        self._contradictions: list[ContradictionRecord] = []
        self._manual_overrides: list[dict[str, Any]] = []
        self._event_checkpoints: list[dict[str, Any]] = []
        self._audit: list[dict[str, Any]] = []
        self._refreshes_avoided = 0
        self._retrievals_avoided = Decimal("0")
        self._seed_default_policies()

    def snapshot(self) -> dict[str, Any]:
        latest = {decision.information_record_id: decision for decision in self._decisions}
        counts = {status.value: 0 for status in FreshnessStatus}
        for record_id in self._records:
            decision = latest.get(record_id)
            counts[(decision.status if decision else FreshnessStatus.UNKNOWN).value] += 1
        due = self.list_records_due_for_evaluation()
        return {
            "engineName": "Information Freshness Engine",
            "engineeringOrder": "EO-CF",
            "status": "HEALTHY",
            "registeredInformationRecords": len(self._records),
            "headerIndicators": {
                "registeredInformationRecords": len(self._records),
                "freshRecords": counts[FreshnessStatus.FRESH.value],
                "limitedUseRecords": counts[FreshnessStatus.FRESH_LIMITED_USE.value],
                "validationRequiredRecords": counts[FreshnessStatus.VALIDATION_REQUIRED.value],
                "partiallyStaleRecords": counts[FreshnessStatus.PARTIALLY_STALE.value],
                "staleRecords": counts[FreshnessStatus.STALE.value],
                "supersededRecords": counts[FreshnessStatus.SUPERSEDED.value],
                "contradictedRecords": counts[FreshnessStatus.CONTRADICTED.value],
                "recordsDueForReevaluation": len(due),
                "refreshMissionsAvoided": self._refreshes_avoided,
                "paidRetrievalsAvoided": float(self._retrievals_avoided),
            },
            "freshnessInventory": tuple(self._inventory_row(record, latest.get(record.information_record_id)) for record in self._records.values()),
            "staleAndAtRiskInformation": tuple(self._at_risk_row(decision) for decision in self._decisions if decision.status in {FreshnessStatus.STALE, FreshnessStatus.PARTIALLY_STALE, FreshnessStatus.UNVERIFIED, FreshnessStatus.UNUSABLE}),
            "dependencyMap": tuple(self._dependency_row(link, latest) for link in self._dependencies.values()),
            "supersessionAndContradictions": tuple(self._contradiction_row(item) for item in self._contradictions) + tuple(self._supersession_rows()),
            "freshnessPolicies": tuple(_public(policy) for policy in self._policy_versions),
            "reuseAndRefresh": self._reuse_panel(),
            "reevaluationQueue": tuple(self._queue_row(record_id, latest.get(record_id)) for record_id in due),
            "freshnessDecisions": tuple(_public(item) for item in self._decisions[-50:]),
            "invalidationRecords": tuple(_public(item) for item in self._invalidations[-50:]),
            "contradictionRecords": tuple(_public(item) for item in self._contradictions[-50:]),
            "metrics": self._metrics(counts, due),
            "lawCF": {
                "retrievalAuthority": False,
                "officeWakeAuthority": False,
                "missionCreationAuthority": False,
                "expenditureAuthorizationAuthority": False,
                "routineAiInvocations": 0,
                "uncontrolledLoopsCreated": False,
                "decisionsAppendOnly": True,
            },
            "integrationFeeds": {
                "eoCB": {"queryPath": "evaluate_record", "dutyOfficersMustNotGuessFreshness": True},
                "eoCD": {"reuseEvidenceAvailable": True, "partialRefreshScopeAvailable": True},
                "eoCE": {"freshnessJustificationAvailable": True, "financialDecisionAuthority": False},
                "eoCG": {"cacheFreshnessAuthority": True},
                "eoCH": {"deltaImpactFeedAvailable": True},
            },
            "manualOverrides": tuple(self._manual_overrides),
            "audit": tuple(self._audit[-50:]),
        }

    def register_record(self, record: InformationRecord | dict[str, Any]) -> InformationRecord:
        if isinstance(record, dict):
            record = self._record_from_dict(record)
        self._records[record.information_record_id] = record
        if record.supersedes_record_id and record.supersedes_record_id in self._records:
            prior = self._records[record.supersedes_record_id]
            prior = replace(prior, superseded_by_record_id=record.information_record_id, updated_at=utc_timestamp())
            self._records[prior.information_record_id] = prior
            self.invalidate_record(
                prior.information_record_id,
                InvalidationReason.SOURCE_SUPERSEDED,
                explanation=f"Record superseded by {record.information_record_id}.",
                source_record_id=record.information_record_id,
                full=True,
            )
        self._audit_event("record_registered", record.information_record_id, f"{record.domain.value}/{record.information_type}")
        return record

    def create_policy_version(self, updates: dict[str, Any], *, actor: str = "Commander", reason: str = "Policy update.") -> FreshnessPolicy:
        base = self._resolve_policy(
            _domain(updates.get("domain", InformationDomain.HISTORICAL.value)),
            str(updates.get("informationType", updates.get("information_type", "enterprise_default"))),
            _decision_use_or_none(updates.get("decisionUseClass", updates.get("decision_use_class", ""))),
        )
        policy = replace(
            base,
            policy_id=str(updates.get("policyId", updates.get("policy_id", base.policy_id))),
            version=max(policy.version for policy in self._policy_versions) + 1,
            maximum_age_seconds=_int_or_none(updates.get("maximumAgeSeconds", updates.get("maximum_age_seconds", base.maximum_age_seconds))),
            validation_age_seconds=_int_or_none(updates.get("validationAgeSeconds", updates.get("validation_age_seconds", base.validation_age_seconds))),
            limited_use_age_seconds=_int_or_none(updates.get("limitedUseAgeSeconds", updates.get("limited_use_age_seconds", base.limited_use_age_seconds))),
            minimum_confidence=float(updates.get("minimumConfidence", updates.get("minimum_confidence", base.minimum_confidence))),
            stale_action=_freshness_action(updates.get("staleAction", updates.get("stale_action", base.stale_action.value))),
            enabled=bool(updates.get("enabled", base.enabled)),
            created_by=actor,
            created_at=utc_timestamp(),
            reason=str(updates.get("reason", reason)),
            content_hash="",
        )
        policy = _hash_policy(policy)
        self._policies[_policy_key(policy.domain, policy.information_type, policy.decision_use_class)] = policy
        self._policy_versions.append(policy)
        self._audit_event("policy_version_created", policy.policy_id, policy.reason)
        return policy

    def evaluate_record(self, record_id: str, context: FreshnessEvaluationContext | dict[str, Any] | None = None) -> FreshnessDecision:
        record = self._records.get(record_id)
        if not record:
            context = self._context_from_dict(context or {"subjectId": record_id})
            return self._decision(
                record_id,
                context,
                self._fallback_policy(),
                FreshnessStatus.UNKNOWN,
                FreshnessAction.BLOCK_USE,
                ("record_missing",),
                "Information record is not registered.",
                provenance=False,
                usable=False,
            )
        context = self._context_from_dict(context or {})
        self._contexts[context.evaluation_context_id] = context
        policy = self._resolve_policy(record.domain, record.information_type, context.decision_use_class, context.mission_type, record.subject_type)
        reasons: list[str] = []
        age_limit = self._age_limit(policy, context)
        validation_limit = policy.validation_age_seconds
        age = _age_seconds(record.observed_at or record.acquired_at or record.source_published_at, context.evaluation_requested_at)
        effective_age = _age_seconds(record.source_effective_at or record.source_published_at or record.observed_at, context.evaluation_requested_at)
        provenance_ok = self._provenance_ok(record)
        authority_ok = _authority_rank(record.source_authority_class) >= _authority_rank(context.required_source_authority or policy.minimum_source_authority)
        confidence_floor = context.required_confidence if context.required_confidence is not None else policy.minimum_confidence
        confidence_ok = record.confidence >= confidence_floor
        stale_deps, invalid_deps, stale_fields, stale_sections = self._dependency_state(record, context)
        contradictions = self._unresolved_contradictions(record.information_record_id)
        full_invalidations = tuple(item for item in self._invalidations if item.information_record_id == record.information_record_id and item.full_invalidation)
        partial_invalidations = tuple(item for item in self._invalidations if item.information_record_id == record.information_record_id and not item.full_invalidation)

        status = FreshnessStatus.FRESH
        action = FreshnessAction.REUSE_EXACT
        if context.environment == "production" and record.environment in {"simulation", "replay", "test"}:
            status, action = FreshnessStatus.UNUSABLE, FreshnessAction.BLOCK_USE
            reasons.append("cross_environment_reuse_blocked")
        elif not provenance_ok:
            status, action = FreshnessStatus.UNVERIFIED, FreshnessAction.BLOCK_USE if _high_stakes(context) else FreshnessAction.REUSE_WITH_VALIDATION
            reasons.append("provenance_missing")
        elif not authority_ok:
            status, action = FreshnessStatus.UNUSABLE if _high_stakes(context) else FreshnessStatus.VALIDATION_REQUIRED, FreshnessAction.BLOCK_USE if _high_stakes(context) else FreshnessAction.REUSE_WITH_VALIDATION
            reasons.append("source_authority_insufficient")
        elif not confidence_ok:
            status, action = FreshnessStatus.UNVERIFIED, FreshnessAction.BLOCK_USE if _high_stakes(context) else FreshnessAction.REUSE_WITH_VALIDATION
            reasons.append("confidence_below_policy")
        elif record.superseded_by_record_id:
            status, action = FreshnessStatus.SUPERSEDED, FreshnessAction.BLOCK_USE if _high_stakes(context) else FreshnessAction.REUSE_LIMITED_SCOPE
            reasons.append("source_superseded")
        elif contradictions:
            status, action = FreshnessStatus.CONTRADICTED, policy.contradiction_action
            reasons.append("contradictory_evidence")
        elif full_invalidations:
            status, action = FreshnessStatus.STALE, policy.stale_action
            reasons.append(full_invalidations[-1].reason.value)
        elif stale_deps or invalid_deps:
            status, action = (FreshnessStatus.STALE, policy.stale_action) if _high_stakes(context) else (FreshnessStatus.PARTIALLY_STALE, policy.partial_stale_action)
            reasons.append("dependency_stale")
        elif partial_invalidations:
            status, action = FreshnessStatus.PARTIALLY_STALE, policy.partial_stale_action
            reasons.append(partial_invalidations[-1].reason.value)
            stale_fields += tuple(field for item in partial_invalidations for field in item.affected_fields)
            stale_sections += tuple(section for item in partial_invalidations for section in item.affected_sections)
        elif age is None:
            status, action = FreshnessStatus.UNVERIFIED, FreshnessAction.REUSE_WITH_VALIDATION if not _high_stakes(context) else FreshnessAction.BLOCK_USE
            reasons.append("timestamp_missing")
        elif age_limit is not None and age > age_limit:
            if policy.limited_use_age_seconds and age <= policy.limited_use_age_seconds and not _high_stakes(context):
                status, action = FreshnessStatus.FRESH_LIMITED_USE, FreshnessAction.REUSE_LIMITED_SCOPE
                reasons.append("limited_use_window")
            else:
                status, action = FreshnessStatus.STALE, policy.stale_action
                reasons.append("time_window_expired")
        elif validation_limit is not None and age > validation_limit:
            status, action = FreshnessStatus.VALIDATION_REQUIRED, FreshnessAction.REUSE_WITH_VALIDATION
            reasons.append("validation_window_expired")
        else:
            reasons.append("freshness_policy_satisfied")

        requested_fields = context.requested_fields or record.field_manifest
        requested_sections = context.requested_sections or record.section_manifest
        stale_fields = tuple(dict.fromkeys(stale_fields))
        stale_sections = tuple(dict.fromkeys(stale_sections))
        fresh_fields = tuple(field for field in requested_fields if field not in stale_fields)
        fresh_sections = tuple(section for section in requested_sections if section not in stale_sections)
        unknown_fields = tuple(field for field in requested_fields if field not in record.field_manifest and record.field_manifest)
        unknown_sections = tuple(section for section in requested_sections if section not in record.section_manifest and record.section_manifest)
        if (stale_fields or stale_sections) and status == FreshnessStatus.FRESH:
            status, action = FreshnessStatus.PARTIALLY_STALE, policy.partial_stale_action
            reasons.append("partial_scope_stale")
        usable = status in {FreshnessStatus.FRESH, FreshnessStatus.FRESH_LIMITED_USE, FreshnessStatus.VALIDATION_REQUIRED, FreshnessStatus.PARTIALLY_STALE} and not (_high_stakes(context) and status != FreshnessStatus.FRESH)
        decision = self._decision(
            record.information_record_id,
            context,
            policy,
            status,
            action,
            tuple(dict.fromkeys(reasons)),
            _explanation(status, action, reasons),
            chronological_age=age,
            effective_age=effective_age,
            age_limit=age_limit,
            validation_limit=validation_limit,
            authority=authority_ok,
            confidence=confidence_ok,
            provenance=provenance_ok,
            stale_deps=tuple(stale_deps),
            invalid_deps=tuple(invalid_deps),
            contradictions=tuple(item.contradiction_id for item in contradictions),
            superseding=record.superseded_by_record_id,
            fresh_fields=fresh_fields,
            stale_fields=stale_fields,
            unknown_fields=unknown_fields,
            fresh_sections=fresh_sections,
            stale_sections=stale_sections,
            unknown_sections=unknown_sections,
            reusable_scope={"fields": fresh_fields, "sections": fresh_sections, "status": status.value},
            refresh_scope={"fields": stale_fields, "sections": stale_sections, "dependencies": tuple(stale_deps), "action": action.value},
            usable=usable,
        )
        self._decisions.append(decision)
        if action in {FreshnessAction.REUSE_EXACT, FreshnessAction.REUSE_LIMITED_SCOPE, FreshnessAction.REUSE_WITH_VALIDATION}:
            self._refreshes_avoided += 1
        return decision

    def evaluate_records(self, record_ids: tuple[str, ...] | list[str], context: FreshnessEvaluationContext | dict[str, Any] | None = None) -> dict[str, Any]:
        decisions = tuple(self.evaluate_record(record_id, context) for record_id in record_ids)
        blocked = tuple(item.information_record_id for item in decisions if item.recommended_action == FreshnessAction.BLOCK_USE)
        full = tuple(item.information_record_id for item in decisions if item.recommended_action in {FreshnessAction.FULL_REFRESH, FreshnessAction.ACQUIRE_NEW_SOURCE})
        partial = tuple(item.information_record_id for item in decisions if item.recommended_action in {FreshnessAction.PARTIAL_REFRESH, FreshnessAction.REFRESH_DEPENDENCIES})
        validation = tuple(item.information_record_id for item in decisions if item.status == FreshnessStatus.VALIDATION_REQUIRED)
        reusable = tuple(item.information_record_id for item in decisions if item.usable_for_requested_scope and item.recommended_action in {FreshnessAction.REUSE_EXACT, FreshnessAction.REUSE_LIMITED_SCOPE, FreshnessAction.REUSE_WITH_VALIDATION})
        return {
            "decisions": tuple(_public(item) for item in decisions),
            "overallStatus": _worst_status(tuple(item.status for item in decisions)).value if decisions else FreshnessStatus.UNKNOWN.value,
            "reusableRecordIds": reusable,
            "validationRequiredRecordIds": validation,
            "partialRefreshRecordIds": partial,
            "fullRefreshRecordIds": full,
            "blockedRecordIds": blocked,
            "recommendedRefreshScope": {item.information_record_id: item.refresh_scope for item in decisions if item.refresh_scope.get("fields") or item.refresh_scope.get("sections") or item.refresh_scope.get("dependencies")},
            "estimatedReuseRatio": round(len(reusable) / max(1, len(decisions)), 4),
            "explanation": "Freshness evaluation completed without retrieval or mission creation.",
        }

    def get_current_status(self, record_id: str) -> str:
        decision = self.get_latest_decision(record_id)
        return decision.status.value if decision else FreshnessStatus.UNKNOWN.value

    def get_latest_decision(self, record_id: str, context: Any = None) -> FreshnessDecision | None:
        for decision in reversed(self._decisions):
            if decision.information_record_id == record_id:
                return decision
        return None

    def list_stale_records(self) -> tuple[str, ...]:
        return tuple(item.information_record_id for item in self._decisions if item.status == FreshnessStatus.STALE)

    def list_partially_stale_records(self) -> tuple[str, ...]:
        return tuple(item.information_record_id for item in self._decisions if item.status == FreshnessStatus.PARTIALLY_STALE)

    def list_superseded_records(self) -> tuple[str, ...]:
        return tuple(record.information_record_id for record in self._records.values() if record.superseded_by_record_id)

    def list_contradicted_records(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item.record_a_id for item in self._contradictions if not item.resolved_at))

    def list_records_due_for_evaluation(self) -> tuple[str, ...]:
        now = _parse_time(utc_timestamp())
        due: list[str] = []
        latest = {decision.information_record_id: decision for decision in self._decisions}
        for record_id, decision in latest.items():
            if decision.next_evaluation_at and _parse_time(decision.next_evaluation_at) <= now:
                due.append(record_id)
        return tuple(due)

    def list_records_by_subject(self, subject_id: str) -> tuple[str, ...]:
        return tuple(record.information_record_id for record in self._records.values() if record.subject_id == subject_id)

    def list_records_by_information_type(self, information_type: str) -> tuple[str, ...]:
        return tuple(record.information_record_id for record in self._records.values() if record.information_type == information_type)

    def list_dependencies(self, record_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(_public(link) for link in self._dependencies.values() if link.dependent_record_id == record_id)

    def list_dependents(self, record_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(_public(link) for link in self._dependencies.values() if link.dependency_record_id == record_id)

    def get_reusable_scope(self, record_id: str, context: Any = None) -> dict[str, Any]:
        return (self.get_latest_decision(record_id) or self.evaluate_record(record_id, context)).reusable_scope

    def get_refresh_scope(self, record_id: str, context: Any = None) -> dict[str, Any]:
        return (self.get_latest_decision(record_id) or self.evaluate_record(record_id, context)).refresh_scope

    def add_dependency(self, link: DependencyLink | dict[str, Any]) -> DependencyLink:
        if isinstance(link, dict):
            link = self._dependency_from_dict(link)
        if self._creates_cycle(link.dependent_record_id, link.dependency_record_id):
            raise ValueError("dependency cycle detected")
        self._dependencies[link.dependency_link_id] = link
        self._audit_event("dependency_registered", link.dependent_record_id, f"depends on {link.dependency_record_id}")
        return link

    def invalidate_record(
        self,
        record_id: str,
        reason: InvalidationReason | str,
        *,
        affected_fields: tuple[str, ...] = (),
        affected_sections: tuple[str, ...] = (),
        explanation: str = "",
        source_event_id: str = "",
        source_record_id: str = "",
        source_policy_id: str = "",
        full: bool = False,
        actor_type: str = "system",
        actor_id: str = "InformationFreshnessEngine",
        metadata: dict[str, Any] | None = None,
    ) -> InvalidationRecord:
        item = InvalidationRecord(
            invalidation_id=f"IFR-INV-{len(self._invalidations) + 1:06d}",
            information_record_id=record_id,
            reason=_invalidation_reason(reason),
            source_event_id=source_event_id,
            source_record_id=source_record_id,
            source_policy_id=source_policy_id,
            affected_fields=affected_fields,
            affected_sections=affected_sections,
            full_invalidation=bool(full),
            invalidated_at=utc_timestamp(),
            invalidated_by_type=actor_type,
            invalidated_by_id=actor_id,
            explanation=explanation or f"Record invalidated by {reason}.",
            metadata=metadata or {},
            content_hash="",
        )
        item = _hash_invalidation(item)
        self._invalidations.append(item)
        for link in tuple(self._dependencies.values()):
            if link.dependency_record_id == record_id:
                self.invalidate_record(
                    link.dependent_record_id,
                    InvalidationReason.DEPENDENCY_INVALIDATED,
                    affected_fields=link.affected_fields,
                    affected_sections=link.affected_sections,
                    explanation=f"Dependency {record_id} invalidated.",
                    source_record_id=record_id,
                    full=link.invalidation_behavior == "full",
                    actor_id="DependencyGraph",
                )
        return item

    def register_contradiction(self, item: ContradictionRecord | dict[str, Any]) -> ContradictionRecord:
        if isinstance(item, dict):
            item = self._contradiction_from_dict(item)
        self._contradictions.append(item)
        self.invalidate_record(item.record_a_id, InvalidationReason.CONTRADICTORY_EVIDENCE, affected_fields=item.affected_fields, affected_sections=item.affected_sections, source_record_id=item.record_b_id, explanation="Material contradictory evidence registered.")
        self.invalidate_record(item.record_b_id, InvalidationReason.CONTRADICTORY_EVIDENCE, affected_fields=item.affected_fields, affected_sections=item.affected_sections, source_record_id=item.record_a_id, explanation="Material contradictory evidence registered.")
        return item

    def resolve_contradiction(self, contradiction_id: str, *, actor: str = "Commander", reason: str = "Contradiction resolved.") -> ContradictionRecord:
        for index, item in enumerate(self._contradictions):
            if item.contradiction_id == contradiction_id:
                resolved = replace(item, resolved_at=utc_timestamp(), resolution_type="manual", resolution_summary=f"{actor}: {reason}")
                resolved = _hash_contradiction(resolved)
                self._contradictions[index] = resolved
                return resolved
        raise KeyError(contradiction_id)

    def apply_manual_override(self, record_id: str, status: str, *, actor: str = "Commander", reason: str = "Temporary freshness override.", expires_at: str = "") -> dict[str, Any]:
        override = {"overrideId": f"IFR-OVR-{len(self._manual_overrides) + 1:06d}", "recordId": record_id, "status": status, "actor": actor, "reason": reason, "expiresAt": expires_at, "createdAt": utc_timestamp()}
        self._manual_overrides.append(override)
        self._audit_event("manual_override", record_id, reason)
        return override

    def handle_event(self, event: dict[str, Any]) -> dict[str, Any]:
        event_type = str(event.get("event_type", event.get("eventType", "")))
        subject_id = str(event.get("subject_id", event.get("subjectId", event.get("ticker", ""))))
        touched: list[str] = []
        for record in self._records.values():
            policy = self._resolve_policy(record.domain, record.information_type, None)
            if event_type in policy.invalidating_event_types and (not subject_id or subject_id in {record.subject_id, record.ticker, record.position_id, record.order_id}):
                self.invalidate_record(record.information_record_id, InvalidationReason.EVENT_TRIGGERED, affected_sections=record.section_manifest, explanation=f"EO-CC event {event_type} invalidated record.", source_event_id=str(event.get("event_id", event.get("eventId", ""))), full=False)
                touched.append(record.information_record_id)
        checkpoint = {"eventId": event.get("event_id", event.get("eventId", "")), "eventType": event_type, "recordsTouched": tuple(touched), "processedAt": utc_timestamp()}
        self._event_checkpoints.append(checkpoint)
        return checkpoint

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._policies.clear()
        self._policy_versions = []
        for item in snapshot.get("freshnessPolicies", ()):
            policy = self._policy_from_dict(item)
            self._policies[_policy_key(policy.domain, policy.information_type, policy.decision_use_class)] = policy
            self._policy_versions.append(policy)
        self._records = {str(item["information_record_id"]): self._record_from_dict(item) for item in snapshot.get("freshnessInventory", ()) if item.get("information_record_id")}
        for item in snapshot.get("freshnessDecisions", ()):
            self._decisions.append(self._decision_from_dict(item))
        for item in snapshot.get("invalidationRecords", ()):
            self._invalidations.append(self._invalidation_from_dict(item))
        for item in snapshot.get("contradictionRecords", ()):
            self._contradictions.append(self._contradiction_from_dict(item))
        for item in snapshot.get("dependencyMap", ()):
            if item.get("dependency_link_id"):
                link = self._dependency_from_dict(item)
                self._dependencies[link.dependency_link_id] = link
        self._audit_event("restart_recovery", "EO-CF", "Information Freshness Engine restored from snapshot.")

    def eo_cd_reuse_query(self, record_ids: tuple[str, ...] | list[str], context: dict[str, Any]) -> dict[str, Any]:
        return self.evaluate_records(record_ids, context)

    def eo_ce_refresh_justification(self, record_id: str, context: dict[str, Any]) -> dict[str, Any]:
        decision = self.evaluate_record(record_id, context)
        unnecessary = decision.status == FreshnessStatus.FRESH and decision.recommended_action == FreshnessAction.REUSE_EXACT
        if unnecessary:
            self._retrievals_avoided += Decimal(str(context.get("estimatedCostUsd", 0.0) or 0.0))
        return {"paidRetrievalJustified": not unnecessary, "decision": _public(decision), "reason": decision.explanation}

    def seed_runtime_records(self, *, timestamp_utc: str, market_data_provider: dict[str, Any], performance_truth: dict[str, Any], commander_briefing: dict[str, Any]) -> None:
        if "IFR-MARKET-PROVIDER" not in self._records:
            self.register_record(
                {
                    "information_record_id": "IFR-MARKET-PROVIDER",
                    "domain": "market",
                    "information_type": "last_trade",
                    "subject_type": "market_feed",
                    "subject_id": "PAPER-MARKET",
                    "source_system": "MarketDataProviderAbstractionLayer",
                    "source_record_id": "MDPA-SNAPSHOT",
                    "source_authority_class": "market_data_primary",
                    "observed_at": timestamp_utc,
                    "validated_at": timestamp_utc,
                    "content_hash": _content_hash(market_data_provider),
                    "confidence": 0.99,
                    "validation_state": "VALID",
                    "field_manifest": ("last", "bid", "ask", "volume"),
                    "section_manifest": ("quotes",),
                    "payload_reference": "marketDataProviderAbstractionLayer",
                }
            )
        if "IFR-PORTFOLIO-TRUTH" not in self._records:
            self.register_record(
                {
                    "information_record_id": "IFR-PORTFOLIO-TRUTH",
                    "domain": "portfolio",
                    "information_type": "portfolio_truth",
                    "subject_type": "portfolio",
                    "subject_id": "PAPER-PORTFOLIO",
                    "source_system": "PerformanceTruthEngine",
                    "source_record_id": "PTE-SNAPSHOT",
                    "source_authority_class": "enterprise_truth",
                    "observed_at": timestamp_utc,
                    "validated_at": timestamp_utc,
                    "content_hash": _content_hash(performance_truth),
                    "confidence": 0.98,
                    "validation_state": "VALID",
                    "field_manifest": ("cash", "market_value", "positions"),
                    "section_manifest": ("portfolioLedger", "positionRegistry"),
                    "payload_reference": "performanceTruthEngine",
                }
            )
        if "IFR-COMMANDER-BRIEFING" not in self._records and commander_briefing.get("latestBriefingRecord"):
            self.register_record(
                {
                    "information_record_id": "IFR-COMMANDER-BRIEFING",
                    "domain": "mission_product",
                    "information_type": "commander_briefing",
                    "subject_type": "enterprise",
                    "subject_id": "ARGOS",
                    "source_system": "CommanderBriefingGenerator",
                    "source_record_id": str(commander_briefing.get("latestBriefingRecord", {}).get("commander_briefing_id", "CBG-LATEST")),
                    "source_authority_class": "validated_internal",
                    "observed_at": timestamp_utc,
                    "validated_at": timestamp_utc,
                    "content_hash": _content_hash(commander_briefing.get("latestBriefingRecord", {})),
                    "confidence": 0.96,
                    "validation_state": "VALID",
                    "field_manifest": ("overall_status", "executive_summary", "decisions_required"),
                    "section_manifest": ("executive_summary", "risk_summary", "decisions_required"),
                    "payload_reference": "commanderBriefingGenerator.latestBriefingRecord",
                }
            )
        for record_id, use_class in (("IFR-MARKET-PROVIDER", "tactical_analysis"), ("IFR-PORTFOLIO-TRUTH", "commander_briefing"), ("IFR-COMMANDER-BRIEFING", "commander_briefing")):
            if record_id in self._records and not self.get_latest_decision(record_id):
                self.evaluate_record(record_id, {"decisionUseClass": use_class, "subjectId": self._records[record_id].subject_id, "environment": "paper"})

    def _record_from_dict(self, item: dict[str, Any]) -> InformationRecord:
        now = item.get("created_at", item.get("createdAt", utc_timestamp()))
        domain = _domain(item.get("domain", InformationDomain.HISTORICAL.value))
        info_type = str(item.get("information_type", item.get("informationType", "unknown_information")))
        policy = self._resolve_policy(domain, info_type, _decision_use_or_none(item.get("decision_use_class", item.get("decisionUseClass", ""))))
        record_id = str(item.get("information_record_id", item.get("informationRecordId", f"IFR-REC-{len(self._records) + 1:06d}")))
        return InformationRecord(
            information_record_id=record_id,
            domain=domain,
            information_type=info_type,
            schema_name=str(item.get("schema_name", item.get("schemaName", ""))),
            schema_version=str(item.get("schema_version", item.get("schemaVersion", ""))),
            subject_type=str(item.get("subject_type", item.get("subjectType", ""))),
            subject_id=str(item.get("subject_id", item.get("subjectId", ""))),
            ticker=str(item.get("ticker", "")),
            position_id=str(item.get("position_id", item.get("positionId", ""))),
            order_id=str(item.get("order_id", item.get("orderId", ""))),
            mission_id=str(item.get("mission_id", item.get("missionId", ""))),
            workflow_id=str(item.get("workflow_id", item.get("workflowId", ""))),
            office_id=str(item.get("office_id", item.get("officeId", ""))),
            environment=str(item.get("environment", "paper")),
            source_system=str(item.get("source_system", item.get("sourceSystem", ""))),
            source_record_id=str(item.get("source_record_id", item.get("sourceRecordId", ""))),
            source_authority_class=_authority(item.get("source_authority_class", item.get("sourceAuthorityClass", SourceAuthorityClass.UNKNOWN.value))),
            source_published_at=str(item.get("source_published_at", item.get("sourcePublishedAt", ""))),
            source_effective_at=str(item.get("source_effective_at", item.get("sourceEffectiveAt", ""))),
            observed_at=str(item.get("observed_at", item.get("observedAt", utc_timestamp()))),
            acquired_at=str(item.get("acquired_at", item.get("acquiredAt", ""))),
            validated_at=str(item.get("validated_at", item.get("validatedAt", ""))),
            source_version=str(item.get("source_version", item.get("sourceVersion", ""))),
            content_hash=str(item.get("content_hash", item.get("contentHash", _content_hash(item)))),
            confidence=float(item.get("confidence", 0.0)),
            validation_state=str(item.get("validation_state", item.get("validationState", "UNVERIFIED"))),
            payload_reference=str(item.get("payload_reference", item.get("payloadReference", ""))),
            field_manifest=tuple(item.get("field_manifest", item.get("fieldManifest", ())) or ()),
            section_manifest=tuple(item.get("section_manifest", item.get("sectionManifest", ())) or ()),
            policy_id=str(item.get("policy_id", item.get("policyId", policy.policy_id))),
            policy_version=int(item.get("policy_version", item.get("policyVersion", policy.version))),
            supersedes_record_id=str(item.get("supersedes_record_id", item.get("supersedesRecordId", ""))),
            superseded_by_record_id=str(item.get("superseded_by_record_id", item.get("supersededByRecordId", ""))),
            created_at=str(now),
            updated_at=str(item.get("updated_at", item.get("updatedAt", now))),
        )

    def _context_from_dict(self, item: FreshnessEvaluationContext | dict[str, Any]) -> FreshnessEvaluationContext:
        if isinstance(item, FreshnessEvaluationContext):
            return item
        return FreshnessEvaluationContext(
            evaluation_context_id=str(item.get("evaluation_context_id", item.get("evaluationContextId", f"IFR-CTX-{len(self._contexts) + 1:06d}"))),
            decision_use_class=_decision_use(item.get("decision_use_class", item.get("decisionUseClass", DecisionUseClass.TACTICAL_ANALYSIS.value))),
            mission_type=str(item.get("mission_type", item.get("missionType", ""))),
            subject_type=str(item.get("subject_type", item.get("subjectType", ""))),
            subject_id=str(item.get("subject_id", item.get("subjectId", ""))),
            ticker=str(item.get("ticker", "")),
            position_id=str(item.get("position_id", item.get("positionId", ""))),
            order_id=str(item.get("order_id", item.get("orderId", ""))),
            operating_mode=str(item.get("operating_mode", item.get("operatingMode", "Observation Only"))),
            market_state=str(item.get("market_state", item.get("marketState", "closed"))),
            market_calendar_id=str(item.get("market_calendar_id", item.get("marketCalendarId", "XNYS"))),
            open_position=bool(item.get("open_position", item.get("openPosition", False))),
            active_order=bool(item.get("active_order", item.get("activeOrder", False))),
            safety_critical=bool(item.get("safety_critical", item.get("safetyCritical", False))),
            required_confidence=float(item["requiredConfidence"]) if "requiredConfidence" in item else (float(item["required_confidence"]) if "required_confidence" in item else None),
            required_source_authority=_authority(item["requiredSourceAuthority"]) if "requiredSourceAuthority" in item else (_authority(item["required_source_authority"]) if "required_source_authority" in item else None),
            requested_fields=tuple(item.get("requested_fields", item.get("requestedFields", ())) or ()),
            requested_sections=tuple(item.get("requested_sections", item.get("requestedSections", ())) or ()),
            environment=str(item.get("environment", "paper")),
            evaluation_requested_at=str(item.get("evaluation_requested_at", item.get("evaluationRequestedAt", utc_timestamp()))),
            metadata=dict(item.get("metadata", {}) or {}),
        )

    def _dependency_from_dict(self, item: dict[str, Any]) -> DependencyLink:
        link = DependencyLink(
            dependency_link_id=str(item.get("dependency_link_id", item.get("dependencyLinkId", f"IFR-DEP-{len(self._dependencies) + 1:06d}"))),
            dependent_record_id=str(item.get("dependent_record_id", item.get("dependentRecordId", ""))),
            dependency_record_id=str(item.get("dependency_record_id", item.get("dependencyRecordId", ""))),
            dependency_type=str(item.get("dependency_type", item.get("dependencyType", "source"))),
            required=bool(item.get("required", True)),
            affected_fields=tuple(item.get("affected_fields", item.get("affectedFields", ())) or ()),
            affected_sections=tuple(item.get("affected_sections", item.get("affectedSections", ())) or ()),
            invalidation_behavior=str(item.get("invalidation_behavior", item.get("invalidationBehavior", "partial"))),
            maximum_dependency_age_seconds=_int_or_none(item.get("maximum_dependency_age_seconds", item.get("maximumDependencyAgeSeconds", None))),
            created_at=str(item.get("created_at", item.get("createdAt", utc_timestamp()))),
            content_hash=str(item.get("content_hash", item.get("contentHash", ""))),
        )
        return _hash_dependency(link)

    def _contradiction_from_dict(self, item: dict[str, Any]) -> ContradictionRecord:
        contradiction = ContradictionRecord(
            contradiction_id=str(item.get("contradiction_id", item.get("contradictionId", f"IFR-CON-{len(self._contradictions) + 1:06d}"))),
            record_a_id=str(item.get("record_a_id", item.get("recordAId", ""))),
            record_b_id=str(item.get("record_b_id", item.get("recordBId", ""))),
            contradiction_type=str(item.get("contradiction_type", item.get("contradictionType", "structured_field_disagreement"))),
            affected_fields=tuple(item.get("affected_fields", item.get("affectedFields", ())) or ()),
            affected_sections=tuple(item.get("affected_sections", item.get("affectedSections", ())) or ()),
            materiality=str(item.get("materiality", "material")),
            resolution_required=bool(item.get("resolution_required", item.get("resolutionRequired", True))),
            preferred_record_id=str(item.get("preferred_record_id", item.get("preferredRecordId", ""))),
            preference_reason=str(item.get("preference_reason", item.get("preferenceReason", ""))),
            detected_at=str(item.get("detected_at", item.get("detectedAt", utc_timestamp()))),
            resolved_at=str(item.get("resolved_at", item.get("resolvedAt", ""))),
            resolution_type=str(item.get("resolution_type", item.get("resolutionType", ""))),
            resolution_summary=str(item.get("resolution_summary", item.get("resolutionSummary", ""))),
            content_hash=str(item.get("content_hash", item.get("contentHash", ""))),
        )
        return _hash_contradiction(contradiction)

    def _invalidation_from_dict(self, item: dict[str, Any]) -> InvalidationRecord:
        invalidation = InvalidationRecord(
            invalidation_id=str(item.get("invalidation_id", item.get("invalidationId", f"IFR-INV-{len(self._invalidations) + 1:06d}"))),
            information_record_id=str(item.get("information_record_id", item.get("informationRecordId", ""))),
            reason=_invalidation_reason(item.get("reason", InvalidationReason.MANUAL_INVALIDATION.value)),
            source_event_id=str(item.get("source_event_id", item.get("sourceEventId", ""))),
            source_record_id=str(item.get("source_record_id", item.get("sourceRecordId", ""))),
            source_policy_id=str(item.get("source_policy_id", item.get("sourcePolicyId", ""))),
            affected_fields=tuple(item.get("affected_fields", item.get("affectedFields", ())) or ()),
            affected_sections=tuple(item.get("affected_sections", item.get("affectedSections", ())) or ()),
            full_invalidation=bool(item.get("full_invalidation", item.get("fullInvalidation", False))),
            invalidated_at=str(item.get("invalidated_at", item.get("invalidatedAt", utc_timestamp()))),
            invalidated_by_type=str(item.get("invalidated_by_type", item.get("invalidatedByType", "system"))),
            invalidated_by_id=str(item.get("invalidated_by_id", item.get("invalidatedById", ""))),
            explanation=str(item.get("explanation", "")),
            metadata=dict(item.get("metadata", {}) or {}),
            content_hash=str(item.get("content_hash", item.get("contentHash", ""))),
        )
        return _hash_invalidation(invalidation)

    def _decision_from_dict(self, item: dict[str, Any]) -> FreshnessDecision:
        return FreshnessDecision(
            freshness_decision_id=str(item.get("freshness_decision_id", item.get("freshnessDecisionId", f"IFR-DEC-{len(self._decisions) + 1:06d}"))),
            information_record_id=str(item.get("information_record_id", item.get("informationRecordId", ""))),
            evaluation_context_id=str(item.get("evaluation_context_id", item.get("evaluationContextId", ""))),
            policy_id=str(item.get("policy_id", item.get("policyId", ""))),
            policy_version=int(item.get("policy_version", item.get("policyVersion", 1))),
            status=FreshnessStatus(item.get("status", FreshnessStatus.UNKNOWN.value)),
            recommended_action=FreshnessAction(item.get("recommended_action", item.get("recommendedAction", FreshnessAction.DEFER.value))),
            evaluated_at=str(item.get("evaluated_at", item.get("evaluatedAt", utc_timestamp()))),
            chronological_age_seconds=_int_or_none(item.get("chronological_age_seconds", item.get("chronologicalAgeSeconds", None))),
            effective_age_seconds=_int_or_none(item.get("effective_age_seconds", item.get("effectiveAgeSeconds", None))),
            age_limit_seconds=_int_or_none(item.get("age_limit_seconds", item.get("ageLimitSeconds", None))),
            validation_limit_seconds=_int_or_none(item.get("validation_limit_seconds", item.get("validationLimitSeconds", None))),
            source_authority_satisfied=bool(item.get("source_authority_satisfied", item.get("sourceAuthoritySatisfied", False))),
            confidence_satisfied=bool(item.get("confidence_satisfied", item.get("confidenceSatisfied", False))),
            provenance_satisfied=bool(item.get("provenance_satisfied", item.get("provenanceSatisfied", False))),
            stale_dependency_ids=tuple(item.get("stale_dependency_ids", item.get("staleDependencyIds", ())) or ()),
            invalid_dependency_ids=tuple(item.get("invalid_dependency_ids", item.get("invalidDependencyIds", ())) or ()),
            contradictory_record_ids=tuple(item.get("contradictory_record_ids", item.get("contradictoryRecordIds", ())) or ()),
            superseding_record_id=str(item.get("superseding_record_id", item.get("supersedingRecordId", ""))),
            fresh_fields=tuple(item.get("fresh_fields", item.get("freshFields", ())) or ()),
            stale_fields=tuple(item.get("stale_fields", item.get("staleFields", ())) or ()),
            unknown_fields=tuple(item.get("unknown_fields", item.get("unknownFields", ())) or ()),
            fresh_sections=tuple(item.get("fresh_sections", item.get("freshSections", ())) or ()),
            stale_sections=tuple(item.get("stale_sections", item.get("staleSections", ())) or ()),
            unknown_sections=tuple(item.get("unknown_sections", item.get("unknownSections", ())) or ()),
            usable_for_requested_scope=bool(item.get("usable_for_requested_scope", item.get("usableForRequestedScope", False))),
            reusable_scope=dict(item.get("reusable_scope", item.get("reusableScope", {})) or {}),
            refresh_scope=dict(item.get("refresh_scope", item.get("refreshScope", {})) or {}),
            reason_codes=tuple(item.get("reason_codes", item.get("reasonCodes", ())) or ()),
            explanation=str(item.get("explanation", "")),
            expires_at=str(item.get("expires_at", item.get("expiresAt", ""))),
            next_evaluation_at=str(item.get("next_evaluation_at", item.get("nextEvaluationAt", ""))),
            content_hash=str(item.get("content_hash", item.get("contentHash", ""))),
        )

    def _policy_from_dict(self, item: dict[str, Any]) -> FreshnessPolicy:
        policy = FreshnessPolicy(
            policy_id=str(item.get("policy_id", item.get("policyId", f"IFR-POL-{len(self._policy_versions) + 1:03d}"))),
            version=int(item.get("version", 1)),
            name=str(item.get("name", "Freshness Policy")),
            description=str(item.get("description", "")),
            domain=_domain(item.get("domain", InformationDomain.HISTORICAL.value)),
            information_type=str(item.get("information_type", item.get("informationType", "enterprise_default"))),
            decision_use_class=_decision_use_or_none(item.get("decision_use_class", item.get("decisionUseClass", ""))),
            mission_types=tuple(item.get("mission_types", item.get("missionTypes", ())) or ()),
            subject_types=tuple(item.get("subject_types", item.get("subjectTypes", ())) or ()),
            maximum_age_seconds=_int_or_none(item.get("maximum_age_seconds", item.get("maximumAgeSeconds", None))),
            validation_age_seconds=_int_or_none(item.get("validation_age_seconds", item.get("validationAgeSeconds", None))),
            limited_use_age_seconds=_int_or_none(item.get("limited_use_age_seconds", item.get("limitedUseAgeSeconds", None))),
            market_hours_maximum_age_seconds=_int_or_none(item.get("market_hours_maximum_age_seconds", item.get("marketHoursMaximumAgeSeconds", None))),
            after_hours_maximum_age_seconds=_int_or_none(item.get("after_hours_maximum_age_seconds", item.get("afterHoursMaximumAgeSeconds", None))),
            open_position_maximum_age_seconds=_int_or_none(item.get("open_position_maximum_age_seconds", item.get("openPositionMaximumAgeSeconds", None))),
            active_order_maximum_age_seconds=_int_or_none(item.get("active_order_maximum_age_seconds", item.get("activeOrderMaximumAgeSeconds", None))),
            minimum_confidence=float(item.get("minimum_confidence", item.get("minimumConfidence", 0.0))),
            minimum_source_authority=_authority(item.get("minimum_source_authority", item.get("minimumSourceAuthority", SourceAuthorityClass.UNKNOWN.value))),
            required_dependencies=tuple(item.get("required_dependencies", item.get("requiredDependencies", ())) or ()),
            invalidating_event_types=tuple(item.get("invalidating_event_types", item.get("invalidatingEventTypes", ())) or ()),
            supersession_rule=str(item.get("supersession_rule", item.get("supersessionRule", ""))),
            contradiction_policy=str(item.get("contradiction_policy", item.get("contradictionPolicy", "preserve_and_block"))),
            field_overrides=dict(item.get("field_overrides", item.get("fieldOverrides", {})) or {}),
            section_overrides=dict(item.get("section_overrides", item.get("sectionOverrides", {})) or {}),
            stale_action=_freshness_action(item.get("stale_action", item.get("staleAction", FreshnessAction.PARTIAL_REFRESH.value))),
            partial_stale_action=_freshness_action(item.get("partial_stale_action", item.get("partialStaleAction", FreshnessAction.PARTIAL_REFRESH.value))),
            contradiction_action=_freshness_action(item.get("contradiction_action", item.get("contradictionAction", FreshnessAction.RESOLVE_CONTRADICTION.value))),
            operating_mode_overrides=dict(item.get("operating_mode_overrides", item.get("operatingModeOverrides", {})) or {}),
            enabled=bool(item.get("enabled", True)),
            effective_at=str(item.get("effective_at", item.get("effectiveAt", utc_timestamp()))),
            expires_at=str(item.get("expires_at", item.get("expiresAt", ""))),
            created_by=str(item.get("created_by", item.get("createdBy", "system"))),
            created_at=str(item.get("created_at", item.get("createdAt", utc_timestamp()))),
            reason=str(item.get("reason", "")),
            content_hash=str(item.get("content_hash", item.get("contentHash", ""))),
        )
        return _hash_policy(policy)

    def _resolve_policy(self, domain: InformationDomain, information_type: str, decision_use: DecisionUseClass | None, mission_type: str = "", subject_type: str = "") -> FreshnessPolicy:
        for key in (
            _policy_key(domain, information_type, decision_use),
            _policy_key(domain, information_type, None),
            _policy_key(domain, "*", decision_use),
            _policy_key(domain, "*", None),
            _policy_key(InformationDomain.HISTORICAL, "enterprise_default", None),
        ):
            policy = self._policies.get(key)
            if policy and policy.enabled:
                return policy
        return self._fallback_policy()

    def _fallback_policy(self) -> FreshnessPolicy:
        return self._policies[_policy_key(InformationDomain.HISTORICAL, "enterprise_default", None)]

    def _age_limit(self, policy: FreshnessPolicy, context: FreshnessEvaluationContext) -> int | None:
        if context.active_order and policy.active_order_maximum_age_seconds is not None:
            return policy.active_order_maximum_age_seconds
        if context.open_position and policy.open_position_maximum_age_seconds is not None:
            return policy.open_position_maximum_age_seconds
        if context.market_state.lower() in {"open", "regular", "market_open"} and policy.market_hours_maximum_age_seconds is not None:
            return policy.market_hours_maximum_age_seconds
        if context.market_state.lower() in {"closed", "after_hours"} and policy.after_hours_maximum_age_seconds is not None:
            return policy.after_hours_maximum_age_seconds
        return policy.maximum_age_seconds

    def _provenance_ok(self, record: InformationRecord) -> bool:
        return bool(record.source_system and record.source_record_id and record.source_authority_class != SourceAuthorityClass.UNKNOWN and record.content_hash and (record.observed_at or record.acquired_at or record.source_published_at))

    def _dependency_state(self, record: InformationRecord, context: FreshnessEvaluationContext) -> tuple[list[str], list[str], tuple[str, ...], tuple[str, ...]]:
        stale: list[str] = []
        invalid: list[str] = []
        fields: list[str] = []
        sections: list[str] = []
        for link in self._dependencies.values():
            if link.dependent_record_id != record.information_record_id:
                continue
            latest = self.get_latest_decision(link.dependency_record_id) or self.evaluate_record(link.dependency_record_id, context)
            if latest.status in {FreshnessStatus.STALE, FreshnessStatus.PARTIALLY_STALE, FreshnessStatus.VALIDATION_REQUIRED}:
                stale.append(link.dependency_record_id)
                fields.extend(link.affected_fields)
                sections.extend(link.affected_sections)
            if latest.status in {FreshnessStatus.UNUSABLE, FreshnessStatus.UNVERIFIED, FreshnessStatus.CONTRADICTED, FreshnessStatus.SUPERSEDED}:
                invalid.append(link.dependency_record_id)
                fields.extend(link.affected_fields)
                sections.extend(link.affected_sections)
        return stale, invalid, tuple(fields), tuple(sections)

    def _unresolved_contradictions(self, record_id: str) -> tuple[ContradictionRecord, ...]:
        return tuple(item for item in self._contradictions if not item.resolved_at and record_id in {item.record_a_id, item.record_b_id})

    def _decision(self, record_id: str, context: FreshnessEvaluationContext, policy: FreshnessPolicy, status: FreshnessStatus, action: FreshnessAction, reason_codes: tuple[str, ...], explanation: str, *, chronological_age: int | None = None, effective_age: int | None = None, age_limit: int | None = None, validation_limit: int | None = None, authority: bool = False, confidence: bool = False, provenance: bool = False, stale_deps: tuple[str, ...] = (), invalid_deps: tuple[str, ...] = (), contradictions: tuple[str, ...] = (), superseding: str = "", fresh_fields: tuple[str, ...] = (), stale_fields: tuple[str, ...] = (), unknown_fields: tuple[str, ...] = (), fresh_sections: tuple[str, ...] = (), stale_sections: tuple[str, ...] = (), unknown_sections: tuple[str, ...] = (), reusable_scope: dict[str, Any] | None = None, refresh_scope: dict[str, Any] | None = None, usable: bool = False) -> FreshnessDecision:
        evaluated_at = utc_timestamp()
        next_eval = ""
        if age_limit is not None and chronological_age is not None:
            next_eval = (_parse_time(evaluated_at) + timedelta(seconds=max(1, age_limit - chronological_age))).isoformat().replace("+00:00", "Z")
        decision = FreshnessDecision(
            freshness_decision_id=f"IFR-DEC-{len(self._decisions) + 1:06d}",
            information_record_id=record_id,
            evaluation_context_id=context.evaluation_context_id,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            status=status,
            recommended_action=action,
            evaluated_at=evaluated_at,
            chronological_age_seconds=chronological_age,
            effective_age_seconds=effective_age,
            age_limit_seconds=age_limit,
            validation_limit_seconds=validation_limit,
            source_authority_satisfied=authority,
            confidence_satisfied=confidence,
            provenance_satisfied=provenance,
            stale_dependency_ids=stale_deps,
            invalid_dependency_ids=invalid_deps,
            contradictory_record_ids=contradictions,
            superseding_record_id=superseding,
            fresh_fields=fresh_fields,
            stale_fields=stale_fields,
            unknown_fields=unknown_fields,
            fresh_sections=fresh_sections,
            stale_sections=stale_sections,
            unknown_sections=unknown_sections,
            usable_for_requested_scope=usable,
            reusable_scope=reusable_scope or {},
            refresh_scope=refresh_scope or {},
            reason_codes=reason_codes,
            explanation=explanation,
            expires_at=next_eval,
            next_evaluation_at=next_eval,
            content_hash="",
        )
        return _hash_decision(decision)

    def _creates_cycle(self, dependent: str, dependency: str) -> bool:
        seen: set[str] = set()

        def walk(record_id: str) -> bool:
            if record_id == dependent:
                return True
            if record_id in seen:
                return False
            seen.add(record_id)
            return any(walk(link.dependency_record_id) for link in self._dependencies.values() if link.dependent_record_id == record_id)

        return walk(dependency)

    def _metrics(self, counts: dict[str, int], due: tuple[str, ...]) -> dict[str, Any]:
        return {
            "recordsByStatus": counts,
            "evaluationsPerformed": len(self._decisions),
            "recordsDueForReevaluation": len(due),
            "expirationDrivenEvaluations": sum(1 for item in self._decisions if "time_window_expired" in item.reason_codes),
            "eventDrivenEvaluations": len(self._event_checkpoints),
            "missionRequestDrivenEvaluations": sum(1 for item in self._contexts.values() if item.mission_type),
            "dependencyInvalidations": sum(1 for item in self._invalidations if item.reason in {InvalidationReason.DEPENDENCY_INVALIDATED, InvalidationReason.DEPENDENCY_STALE}),
            "supersessions": len(self.list_superseded_records()),
            "contradictions": len(self._contradictions),
            "manualOverrides": len(self._manual_overrides),
            "exactReuseDecisions": sum(1 for item in self._decisions if item.recommended_action == FreshnessAction.REUSE_EXACT),
            "partialRefreshDecisions": sum(1 for item in self._decisions if item.recommended_action == FreshnessAction.PARTIAL_REFRESH),
            "fullRefreshDecisions": sum(1 for item in self._decisions if item.recommended_action in {FreshnessAction.FULL_REFRESH, FreshnessAction.ACQUIRE_NEW_SOURCE}),
            "refreshesAvoided": self._refreshes_avoided,
            "estimatedCostAvoided": float(self._retrievals_avoided),
            "staleInformationBlocked": sum(1 for item in self._decisions if item.status in {FreshnessStatus.STALE, FreshnessStatus.UNUSABLE} and not item.usable_for_requested_scope),
            "policyCoverage": round(len(self._policies) / 10, 4),
        }

    def _inventory_row(self, record: InformationRecord, decision: FreshnessDecision | None) -> dict[str, Any]:
        row = _public(record)
        row.update(
            {
                "currentStatus": (decision.status.value if decision else FreshnessStatus.UNKNOWN.value),
                "permittedUse": "requested_scope" if decision and decision.usable_for_requested_scope else "limited_or_blocked",
                "nextEvaluation": decision.next_evaluation_at if decision else "",
                "recommendedAction": decision.recommended_action.value if decision else FreshnessAction.DEFER.value,
                "reason": ", ".join(decision.reason_codes) if decision else "not_evaluated",
            }
        )
        return row

    def _at_risk_row(self, decision: FreshnessDecision) -> dict[str, Any]:
        record = self._records.get(decision.information_record_id)
        return {
            "recordId": decision.information_record_id,
            "subject": record.subject_id if record else "",
            "status": decision.status.value,
            "reason": ", ".join(decision.reason_codes),
            "affectedMissionTypes": (self._contexts.get(decision.evaluation_context_id) or FreshnessEvaluationContext("", DecisionUseClass.TACTICAL_ANALYSIS, "", "", "", "", "", "", "", "", "", False, False, False, None, None, (), (), "paper", "", {})).mission_type,
            "staleDependencies": decision.stale_dependency_ids,
            "refreshScope": decision.refresh_scope,
            "urgency": "critical" if decision.recommended_action == FreshnessAction.BLOCK_USE else "prompt",
        }

    def _dependency_row(self, link: DependencyLink, latest: dict[str, FreshnessDecision]) -> dict[str, Any]:
        decision = latest.get(link.dependency_record_id)
        return _public(link) | {"dependencyStatus": decision.status.value if decision else FreshnessStatus.UNKNOWN.value, "invalidationPath": f"{link.dependency_record_id}->{link.dependent_record_id}"}

    def _contradiction_row(self, item: ContradictionRecord) -> dict[str, Any]:
        return _public(item) | {"recommendedAction": FreshnessAction.RESOLVE_CONTRADICTION.value if not item.resolved_at else FreshnessAction.NO_ACTION.value}

    def _supersession_rows(self) -> tuple[dict[str, Any], ...]:
        rows = []
        for record in self._records.values():
            if record.superseded_by_record_id:
                rows.append({"type": "supersession", "priorRecord": record.information_record_id, "newRecord": record.superseded_by_record_id, "sourceAuthority": record.source_authority_class.value, "supersessionScope": "record", "resolutionStatus": "superseded", "recommendedAction": FreshnessAction.REUSE_LIMITED_SCOPE.value})
        return tuple(rows)

    def _reuse_panel(self) -> dict[str, Any]:
        latest = tuple({decision.information_record_id: decision for decision in self._decisions}.values())
        return {
            "exactReuseCandidates": tuple(item.information_record_id for item in latest if item.recommended_action == FreshnessAction.REUSE_EXACT),
            "validationOnlyCandidates": tuple(item.information_record_id for item in latest if item.recommended_action == FreshnessAction.REUSE_WITH_VALIDATION),
            "partialRefreshCandidates": tuple(item.information_record_id for item in latest if item.recommended_action in {FreshnessAction.PARTIAL_REFRESH, FreshnessAction.REFRESH_DEPENDENCIES}),
            "fullRefreshCandidates": tuple(item.information_record_id for item in latest if item.recommended_action in {FreshnessAction.FULL_REFRESH, FreshnessAction.ACQUIRE_NEW_SOURCE}),
            "blockedRecords": tuple(item.information_record_id for item in latest if item.recommended_action == FreshnessAction.BLOCK_USE),
            "estimatedWorkAvoided": self._refreshes_avoided,
            "estimatedRetrievalAvoided": float(self._retrievals_avoided),
            "estimateBasis": "Counts reuse recommendations and caller-provided estimated retrieval costs only.",
        }

    def _queue_row(self, record_id: str, decision: FreshnessDecision | None) -> dict[str, Any]:
        return {"recordId": record_id, "dueTime": decision.next_evaluation_at if decision else "", "reason": "expiration", "evaluationTrigger": "scheduled_index", "priority": "high" if decision and decision.status != FreshnessStatus.FRESH else "normal", "currentDependencies": tuple(link.dependency_record_id for link in self._dependencies.values() if link.dependent_record_id == record_id), "status": decision.status.value if decision else FreshnessStatus.UNKNOWN.value}

    def _audit_event(self, action: str, record_id: str, reason: str) -> None:
        self._audit.append({"auditId": f"IFR-AUD-{len(self._audit) + 1:06d}", "timestamp": utc_timestamp(), "action": action, "recordId": record_id, "reason": reason})

    def _seed_default_policies(self) -> None:
        def add(policy: FreshnessPolicy) -> None:
            policy = _hash_policy(policy)
            self._policies[_policy_key(policy.domain, policy.information_type, policy.decision_use_class)] = policy
            self._policy_versions.append(policy)

        now = utc_timestamp()
        add(_policy("IFR-POL-DEFAULT", 1, "Enterprise Default", InformationDomain.HISTORICAL, "enterprise_default", None, 86400, 3600, 604800, SourceAuthorityClass.APPROVED_SECONDARY, 0.70, FreshnessAction.REUSE_WITH_VALIDATION, now))
        add(_policy("IFR-POL-MKT-LIVE", 1, "Live Quote", InformationDomain.MARKET, "last_trade", DecisionUseClass.LIVE_ORDER_ACTION, 5, 3, 30, SourceAuthorityClass.MARKET_DATA_PRIMARY, 0.99, FreshnessAction.ACQUIRE_NEW_SOURCE, now, market_hours=5, after_hours=900))
        add(_policy("IFR-POL-MKT-TACTICAL", 1, "Tactical Quote", InformationDomain.MARKET, "last_trade", DecisionUseClass.TACTICAL_ANALYSIS, 60, 45, 300, SourceAuthorityClass.MARKET_DATA_PRIMARY, 0.95, FreshnessAction.REFRESH_DEPENDENCIES, now, market_hours=60, after_hours=3600))
        add(_policy("IFR-POL-BROKER-ORDER", 1, "Broker Order State", InformationDomain.ORDER, "order_state", None, 10, 5, 30, SourceAuthorityClass.BROKER_CONFIRMED, 0.99, FreshnessAction.ACQUIRE_NEW_SOURCE, now, active_order=3))
        add(_policy("IFR-POL-PORTFOLIO", 1, "Portfolio Truth", InformationDomain.PORTFOLIO, "portfolio_truth", DecisionUseClass.COMMANDER_BRIEFING, 300, 180, 900, SourceAuthorityClass.ENTERPRISE_TRUTH, 0.95, FreshnessAction.REUSE_WITH_VALIDATION, now))
        add(_policy("IFR-POL-COMPANY-DESC", 1, "Business Description", InformationDomain.FUNDAMENTAL, "business_description", DecisionUseClass.STRATEGIC_ANALYSIS, 15552000, 7776000, 31536000, SourceAuthorityClass.COMPANY_PRIMARY, 0.85, FreshnessAction.PARTIAL_REFRESH, now))
        add(_policy("IFR-POL-GUIDANCE", 1, "Earnings Guidance", InformationDomain.FUNDAMENTAL, "earnings_guidance", None, 7776000, 604800, 7776000, SourceAuthorityClass.COMPANY_PRIMARY, 0.90, FreshnessAction.FULL_REFRESH, now, events=("new_earnings_release", "guidance_update", "guidance_withdrawal")))
        add(_policy("IFR-POL-ANALYST", 1, "Analyst Report", InformationDomain.ANALYTICAL_PRODUCT, "analyst_report", None, 86400, 14400, 604800, SourceAuthorityClass.VALIDATED_INTERNAL, 0.80, FreshnessAction.PARTIAL_REFRESH, now, open_position=14400, events=("new_earnings_release", "price_threshold_movement", "risk_policy_change")))
        add(_policy("IFR-POL-RISK", 1, "Risk Assessment", InformationDomain.RISK, "risk_assessment", None, 900, 300, 3600, SourceAuthorityClass.VALIDATED_INTERNAL, 0.90, FreshnessAction.PARTIAL_REFRESH, now, open_position=300, events=("position_quantity_changed", "risk_policy_change", "market_data_stale")))
        add(_policy("IFR-POL-BRIEFING", 1, "Commander Briefing", InformationDomain.MISSION_PRODUCT, "commander_briefing", DecisionUseClass.COMMANDER_BRIEFING, 3600, 1800, 14400, SourceAuthorityClass.VALIDATED_INTERNAL, 0.90, FreshnessAction.REUSE_WITH_VALIDATION, now))


def _policy(policy_id: str, version: int, name: str, domain: InformationDomain, information_type: str, use: DecisionUseClass | None, max_age: int | None, validation_age: int | None, limited_age: int | None, authority: SourceAuthorityClass, confidence: float, stale_action: FreshnessAction, now: str, *, market_hours: int | None = None, after_hours: int | None = None, open_position: int | None = None, active_order: int | None = None, events: tuple[str, ...] = ()) -> FreshnessPolicy:
    return FreshnessPolicy(policy_id, version, name, name, domain, information_type, use, (), (), max_age, validation_age, limited_age, market_hours, after_hours, open_position, active_order, confidence, authority, (), events, "newer_authoritative_same_scope", "preserve_and_block", {}, {}, stale_action, FreshnessAction.PARTIAL_REFRESH, FreshnessAction.RESOLVE_CONTRADICTION, {}, True, now, "", "system", now, "Default EO-CF policy.", "")


def _policy_key(domain: InformationDomain, information_type: str, use: DecisionUseClass | None) -> str:
    return f"{domain.value}:{information_type}:{use.value if use else '*'}"


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


def _hash_policy(policy: FreshnessPolicy) -> FreshnessPolicy:
    return replace(policy, content_hash=_content_hash(_public(replace(policy, content_hash=""))))


def _hash_decision(decision: FreshnessDecision) -> FreshnessDecision:
    return replace(decision, content_hash=_content_hash(_public(replace(decision, content_hash=""))))


def _hash_dependency(link: DependencyLink) -> DependencyLink:
    return replace(link, content_hash=_content_hash(_public(replace(link, content_hash=""))))


def _hash_invalidation(item: InvalidationRecord) -> InvalidationRecord:
    return replace(item, content_hash=_content_hash(_public(replace(item, content_hash=""))))


def _hash_contradiction(item: ContradictionRecord) -> ContradictionRecord:
    return replace(item, content_hash=_content_hash(_public(replace(item, content_hash=""))))


def _content_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _domain(value: Any) -> InformationDomain:
    try:
        return value if isinstance(value, InformationDomain) else InformationDomain(str(value))
    except ValueError:
        return InformationDomain.HISTORICAL


def _decision_use(value: Any) -> DecisionUseClass:
    try:
        return value if isinstance(value, DecisionUseClass) else DecisionUseClass(str(value))
    except ValueError:
        return DecisionUseClass.TACTICAL_ANALYSIS


def _decision_use_or_none(value: Any) -> DecisionUseClass | None:
    return None if not value else _decision_use(value)


def _freshness_action(value: Any) -> FreshnessAction:
    try:
        return value if isinstance(value, FreshnessAction) else FreshnessAction(str(value))
    except ValueError:
        return FreshnessAction.DEFER


def _authority(value: Any) -> SourceAuthorityClass:
    try:
        return value if isinstance(value, SourceAuthorityClass) else SourceAuthorityClass(str(value))
    except ValueError:
        return SourceAuthorityClass.UNKNOWN


def _invalidation_reason(value: Any) -> InvalidationReason:
    try:
        return value if isinstance(value, InvalidationReason) else InvalidationReason(str(value))
    except ValueError:
        return InvalidationReason.MANUAL_INVALIDATION


def _authority_rank(value: SourceAuthorityClass) -> int:
    order = (
        SourceAuthorityClass.UNKNOWN,
        SourceAuthorityClass.SIMULATED,
        SourceAuthorityClass.USER_PROVIDED,
        SourceAuthorityClass.UNVALIDATED_SECONDARY,
        SourceAuthorityClass.APPROVED_SECONDARY,
        SourceAuthorityClass.VALIDATED_INTERNAL,
        SourceAuthorityClass.ENTERPRISE_TRUTH,
        SourceAuthorityClass.MARKET_DATA_PRIMARY,
        SourceAuthorityClass.COMPANY_PRIMARY,
        SourceAuthorityClass.REGULATORY_PRIMARY,
        SourceAuthorityClass.BROKER_CONFIRMED,
    )
    return order.index(value) if value in order else 0


def _age_seconds(value: str, now: str) -> int | None:
    if not value:
        return None
    return max(0, int((_parse_time(now) - _parse_time(value)).total_seconds()))


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(UTC)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _high_stakes(context: FreshnessEvaluationContext) -> bool:
    return context.safety_critical or context.decision_use_class in {DecisionUseClass.LIVE_ORDER_ACTION, DecisionUseClass.POSITION_SAFETY, DecisionUseClass.BROKER_RECONCILIATION, DecisionUseClass.RISK_ENFORCEMENT, DecisionUseClass.TRADE_ENTRY, DecisionUseClass.TRADE_EXIT, DecisionUseClass.PORTFOLIO_ALLOCATION}


def _explanation(status: FreshnessStatus, action: FreshnessAction, reasons: list[str] | tuple[str, ...]) -> str:
    return f"{status.value} for requested context; recommended action {action.value}. Reason: {', '.join(reasons)}."


def _worst_status(statuses: tuple[FreshnessStatus, ...]) -> FreshnessStatus:
    rank = {
        FreshnessStatus.FRESH: 0,
        FreshnessStatus.FRESH_LIMITED_USE: 1,
        FreshnessStatus.VALIDATION_REQUIRED: 2,
        FreshnessStatus.PARTIALLY_STALE: 3,
        FreshnessStatus.STALE: 4,
        FreshnessStatus.SUPERSEDED: 5,
        FreshnessStatus.CONTRADICTED: 6,
        FreshnessStatus.UNVERIFIED: 7,
        FreshnessStatus.UNUSABLE: 8,
        FreshnessStatus.UNKNOWN: 9,
    }
    return max(statuses, key=lambda item: rank[item]) if statuses else FreshnessStatus.UNKNOWN
