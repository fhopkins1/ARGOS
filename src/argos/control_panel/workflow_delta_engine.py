"""Workflow Delta Engine for ARGOS EO-CH."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .enterprise_memory_cache import CacheProductType, EnterpriseMemoryCache
from .information_freshness_engine import FreshnessAction, FreshnessStatus, InformationFreshnessEngine


class DeltaRequestType(str, Enum):
    EVENT_TRIGGERED = "event_triggered"
    MISSION_PLANNING = "mission_planning"
    MANUAL_COMPARISON = "manual_comparison"
    FRESHNESS_INVALIDATION = "freshness_invalidation"
    CACHE_REUSE_REVIEW = "cache_reuse_review"
    POLICY_CHANGE = "policy_change"
    BROKER_RECONCILIATION = "broker_reconciliation"
    POSITION_REVIEW = "position_review"
    REPLAY = "replay"


class ChangeType(str, Enum):
    UNCHANGED = "unchanged"
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    CORRECTED = "corrected"
    SUPERSEDED = "superseded"
    INVALIDATED = "invalidated"
    CONTRADICTED = "contradicted"
    RESTORED = "restored"
    SCHEMA_CHANGED = "schema_changed"
    POLICY_CHANGED = "policy_changed"
    ENVIRONMENT_CHANGED = "environment_changed"
    UNKNOWN = "unknown"


class DeltaMateriality(str, Enum):
    NONE = "none"
    IMMATERIAL = "immaterial"
    MINOR = "minor"
    MATERIAL = "material"
    MAJOR = "major"
    CRITICAL = "critical"


class RevisionRequirement(str, Enum):
    REUSE_EXACT = "reuse_exact"
    REUSE_WITH_VALIDATION = "reuse_with_validation"
    RECOMPUTE_DETERMINISTIC = "recompute_deterministic"
    PARTIAL_REVISION = "partial_revision"
    FULL_REVISION = "full_revision"
    REACQUIRE_SOURCE = "reacquire_source"
    RESOLVE_CONTRADICTION = "resolve_contradiction"
    BLOCK_USE = "block_use"
    NO_ACTION = "no_action"


class OfficeImpactDecision(str, Enum):
    NOT_REQUIRED = "not_required"
    REUSE_PRIOR_OUTPUT = "reuse_prior_output"
    VALIDATION_ONLY = "validation_only"
    DETERMINISTIC_SERVICE_ONLY = "deterministic_service_only"
    PARTIAL_REACTIVATION = "partial_reactivation"
    FULL_REACTIVATION = "full_reactivation"
    CONDITIONALLY_REQUIRED = "conditionally_required"
    PROHIBITED = "prohibited"


@dataclass(frozen=True)
class DeltaBaseline:
    baseline_id: str
    mission_id: str
    mission_plan_id: str
    workflow_id: str
    decision_object_id: str
    subject_type: str
    subject_id: str
    ticker: str
    position_id: str
    order_id: str
    portfolio_id: str
    strategy_id: str
    environment: str
    cache_record_ids: tuple[str, ...]
    information_record_ids: tuple[str, ...]
    evidence_record_ids: tuple[str, ...]
    product_record_ids: tuple[str, ...]
    input_manifest: dict[str, Any]
    output_manifest: dict[str, Any]
    assumption_manifest: dict[str, Any]
    policy_manifest: dict[str, Any]
    dependency_manifest: dict[str, Any]
    workflow_manifest: dict[str, Any]
    schema_versions: dict[str, str]
    content_hashes: dict[str, str]
    validation_state: str
    validated_at: str
    created_at: str
    content_hash: str


@dataclass(frozen=True)
class DeltaAnalysisRequest:
    delta_request_id: str
    request_type: DeltaRequestType
    baseline_id: str
    current_mission_plan_id: str
    current_workflow_id: str
    source_event_ids: tuple[str, ...]
    source_event_group_ids: tuple[str, ...]
    current_information_record_ids: tuple[str, ...]
    current_cache_record_ids: tuple[str, ...]
    current_evidence_record_ids: tuple[str, ...]
    subject_type: str
    subject_id: str
    mission_type: str
    decision_use_class: str
    requested_fields: tuple[str, ...]
    requested_sections: tuple[str, ...]
    requested_products: tuple[str, ...]
    environment: str
    submitted_by_type: str
    submitted_by_id: str
    submitted_at: str


@dataclass(frozen=True)
class FieldChange:
    field_change_id: str
    field_path: str
    change_type: ChangeType
    prior_value_reference: str
    current_value_reference: str
    prior_normalized_value: Any
    current_normalized_value: Any
    absolute_delta: str
    percentage_delta: str
    units: str
    comparison_method: str
    tolerance_used: str
    materiality: DeltaMateriality
    materiality_score: float
    affected_dependency_ids: tuple[str, ...]
    affected_product_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class SectionChange:
    section_change_id: str
    section_name: str
    change_type: ChangeType
    changed_fields: tuple[str, ...]
    unchanged_fields: tuple[str, ...]
    materiality: DeltaMateriality
    revision_requirement: RevisionRequirement
    explanation: str


@dataclass(frozen=True)
class EvidenceChange:
    evidence_change_id: str
    evidence_record_id: str
    change_type: ChangeType
    materiality: DeltaMateriality
    source_authority_change: bool
    explanation: str


@dataclass(frozen=True)
class ProductImpact:
    product_impact_id: str
    product_record_id: str
    cache_record_id: str
    affected_fields: tuple[str, ...]
    affected_sections: tuple[str, ...]
    reusable_fields: tuple[str, ...]
    reusable_sections: tuple[str, ...]
    revision_requirement: RevisionRequirement
    reuse_decision_reference: str
    reason: str


@dataclass(frozen=True)
class OfficeImpact:
    office_impact_id: str
    office_id: str
    prior_role: str
    impact_decision: OfficeImpactDecision
    required_scope: tuple[str, ...]
    excluded_reason: str
    estimated_runtime_seconds: int
    estimated_api_calls: int
    reason: str


@dataclass(frozen=True)
class DependencyImpact:
    dependency_impact_id: str
    changed_input: str
    dependency_path: tuple[str, ...]
    affected_calculations: tuple[str, ...]
    affected_products: tuple[str, ...]
    affected_offices: tuple[str, ...]
    propagation_boundary: str
    materiality: DeltaMateriality


@dataclass(frozen=True)
class WorkflowNodeDelta:
    node_delta_id: str
    node_id: str
    office_id: str
    change_type: ChangeType
    prior_required: bool
    current_required: bool
    token_path_preserved: bool
    reason: str


@dataclass(frozen=True)
class DeltaPackage:
    delta_package_id: str
    package_version: int
    delta_request_id: str
    baseline_id: str
    subject_type: str
    subject_id: str
    environment: str
    highest_materiality: DeltaMateriality
    full_reassessment_required: bool
    field_changes: tuple[FieldChange, ...]
    section_changes: tuple[SectionChange, ...]
    evidence_changes: tuple[EvidenceChange, ...]
    product_impacts: tuple[ProductImpact, ...]
    office_impacts: tuple[OfficeImpact, ...]
    dependency_impacts: tuple[DependencyImpact, ...]
    workflow_node_deltas: tuple[WorkflowNodeDelta, ...]
    reusable_cache_record_ids: tuple[str, ...]
    validation_only_record_ids: tuple[str, ...]
    deterministic_recompute_scope: tuple[str, ...]
    partial_revision_scope: tuple[str, ...]
    blocked_scope: tuple[str, ...]
    minimum_revision_scope: tuple[str, ...]
    recommended_sequence: tuple[str, ...]
    mission_planner_feed: dict[str, Any]
    cost_reduction_evidence: dict[str, Any]
    freshness_decision_references: tuple[str, ...]
    memory_retrieval_references: tuple[str, ...]
    law_ch: dict[str, Any]
    created_at: str
    content_hash: str


class WorkflowDeltaEngine:
    """Deterministic delta analysis; EO-CD remains mission authority."""

    def __init__(self, freshness_engine: InformationFreshnessEngine, memory_cache: EnterpriseMemoryCache) -> None:
        self._freshness = freshness_engine
        self._memory = memory_cache
        self._baselines: dict[str, DeltaBaseline] = {}
        self._requests: dict[str, DeltaAnalysisRequest] = {}
        self._packages: dict[str, DeltaPackage] = {}
        self._request_to_package: dict[str, str] = {}
        self._audit: list[dict[str, Any]] = []
        self._dead_letters: list[dict[str, Any]] = []
        self._checkpoints: list[dict[str, Any]] = []
        self._alerts: list[dict[str, Any]] = []
        self._manual_reviews: list[dict[str, Any]] = []

    def snapshot(self) -> dict[str, Any]:
        packages = tuple(self._packages.values())
        latest = packages[-1] if packages else None
        return {
            "engineName": "Workflow Delta Engine",
            "engineeringOrder": "EO-CH",
            "status": "HEALTHY",
            "summary": {
                "baselines": len(self._baselines),
                "requests": len(self._requests),
                "packages": len(self._packages),
                "pendingRequests": max(0, len(self._requests) - len(self._packages)),
                "fullReassessments": sum(1 for item in packages if item.full_reassessment_required),
                "partialRevisions": sum(1 for item in packages if item.partial_revision_scope),
                "reusedProducts": sum(len(item.reusable_cache_record_ids) for item in packages),
                "officesAvoided": sum(int(item.cost_reduction_evidence.get("officesAvoided", 0)) for item in packages),
                "estimatedCostAvoided": round(sum(float(item.cost_reduction_evidence.get("estimatedCostAvoided", 0.0)) for item in packages), 4),
            },
            "baselineInventory": tuple(_public(item) for item in self._baselines.values()),
            "deltaRequestQueue": tuple(_public(item) for item in self._requests.values()),
            "deltaPackages": tuple(_public(item) for item in packages[-20:]),
            "changeSummary": self._change_summary(latest),
            "fieldAndSectionDelta": {
                "fields": tuple(_public(item) for item in latest.field_changes) if latest else (),
                "sections": tuple(_public(item) for item in latest.section_changes) if latest else (),
            },
            "productImpactMatrix": tuple(_public(item) for item in latest.product_impacts) if latest else (),
            "officeImpactMatrix": tuple(_public(item) for item in latest.office_impacts) if latest else (),
            "dependencyImpactMap": tuple(_public(item) for item in latest.dependency_impacts) if latest else (),
            "workflowGraphComparison": tuple(_public(item) for item in latest.workflow_node_deltas) if latest else (),
            "reuseAndWorkReduction": latest.cost_reduction_evidence if latest else {},
            "missionPlannerFeed": latest.mission_planner_feed if latest else {},
            "comparatorInventory": self.comparator_inventory(),
            "commanderControls": {
                "requestDeltaAnalysis": True,
                "selectBaseline": True,
                "compareProductVersions": True,
                "compareMissionVersions": True,
                "compareWorkflowVersions": True,
                "requestBroaderComparison": True,
                "requestNarrowerComparison": True,
                "markChangeImmaterial": True,
                "requestValidationReview": True,
                "requestFullReassessmentReview": True,
                "exportDeltaPackage": True,
                "replayDelta": True,
                "viewLineage": True,
                "directExecutionAuthority": False,
                "directOfficeWakeAuthority": False,
                "directMissionAuthorization": False,
            },
            "alerts": tuple(self._alerts[-20:]),
            "manualReviewHistory": tuple(self._manual_reviews[-20:]),
            "auditHistory": tuple(self._audit[-50:]),
            "deadLetters": tuple(self._dead_letters[-20:]),
            "recovery": {"checkpoints": tuple(self._checkpoints[-20:]), "restartRecovery": True, "duplicatePackagePrevention": True},
            "lawCH": self._law_state(),
        }

    def create_baseline(self, payload: dict[str, Any]) -> DeltaBaseline:
        baseline_id = str(payload.get("baselineId", payload.get("baseline_id", f"CH-BL-{len(self._baselines) + 1:06d}")))
        if baseline_id in self._baselines:
            return self._baselines[baseline_id]
        baseline = DeltaBaseline(
            baseline_id=baseline_id,
            mission_id=str(payload.get("missionId", payload.get("mission_id", ""))),
            mission_plan_id=str(payload.get("missionPlanId", payload.get("mission_plan_id", ""))),
            workflow_id=str(payload.get("workflowId", payload.get("workflow_id", ""))),
            decision_object_id=str(payload.get("decisionObjectId", payload.get("decision_object_id", ""))),
            subject_type=str(payload.get("subjectType", payload.get("subject_type", "enterprise"))),
            subject_id=str(payload.get("subjectId", payload.get("subject_id", "ARGOS"))),
            ticker=str(payload.get("ticker", "")),
            position_id=str(payload.get("positionId", payload.get("position_id", ""))),
            order_id=str(payload.get("orderId", payload.get("order_id", ""))),
            portfolio_id=str(payload.get("portfolioId", payload.get("portfolio_id", ""))),
            strategy_id=str(payload.get("strategyId", payload.get("strategy_id", ""))),
            environment=str(payload.get("environment", "paper")),
            cache_record_ids=tuple(payload.get("cacheRecordIds", payload.get("cache_record_ids", ())) or ()),
            information_record_ids=tuple(payload.get("informationRecordIds", payload.get("information_record_ids", ())) or ()),
            evidence_record_ids=tuple(payload.get("evidenceRecordIds", payload.get("evidence_record_ids", ())) or ()),
            product_record_ids=tuple(payload.get("productRecordIds", payload.get("product_record_ids", ())) or ()),
            input_manifest=dict(payload.get("inputManifest", payload.get("input_manifest", {})) or {}),
            output_manifest=dict(payload.get("outputManifest", payload.get("output_manifest", {})) or {}),
            assumption_manifest=dict(payload.get("assumptionManifest", payload.get("assumption_manifest", {})) or {}),
            policy_manifest=dict(payload.get("policyManifest", payload.get("policy_manifest", {})) or {}),
            dependency_manifest=dict(payload.get("dependencyManifest", payload.get("dependency_manifest", {})) or {}),
            workflow_manifest=dict(payload.get("workflowManifest", payload.get("workflow_manifest", {})) or {}),
            schema_versions={str(k): str(v) for k, v in dict(payload.get("schemaVersions", payload.get("schema_versions", {})) or {}).items()},
            content_hashes={str(k): str(v) for k, v in dict(payload.get("contentHashes", payload.get("content_hashes", {})) or {}).items()},
            validation_state=str(payload.get("validationState", payload.get("validation_state", "VALID"))),
            validated_at=str(payload.get("validatedAt", payload.get("validated_at", utc_timestamp()))),
            created_at=str(payload.get("createdAt", payload.get("created_at", utc_timestamp()))),
            content_hash="",
        )
        computed_hash = _baseline_integrity_hash(baseline)
        supplied_hash = str(payload.get("contentHash", payload.get("content_hash", "")))
        baseline = replace(baseline, content_hash=supplied_hash or computed_hash)
        self._baselines[baseline.baseline_id] = baseline
        self._audit_event("baseline_created", baseline.baseline_id, "Validated baseline registered for delta analysis.")
        return baseline

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        if "baseline" in payload and not payload.get("baselineId") and not payload.get("baseline_id"):
            baseline = self.create_baseline(dict(payload["baseline"]))
            payload = dict(payload) | {"baselineId": baseline.baseline_id}
        request = self._request_from_payload(payload)
        if request.delta_request_id in self._request_to_package:
            package = self._packages[self._request_to_package[request.delta_request_id]]
            self._audit_event("duplicate_delta_suppressed", request.delta_request_id, package.delta_package_id)
            return {"request": _public(request), "package": _public(package), "duplicate": True}
        self._requests[request.delta_request_id] = request
        if request.baseline_id not in self._baselines:
            self._dead_letter(request.delta_request_id, "baseline_unavailable", "Baseline unavailable; trusted delta cannot be produced.")
            return {"request": _public(request), "package": {}, "duplicate": False}
        baseline = self._baselines[request.baseline_id]
        if baseline.validation_state.upper() not in {"VALID", "VALIDATED"} or not baseline.content_hash:
            self._dead_letter(request.delta_request_id, "baseline_untrusted", "Baseline is not validated or lacks integrity hash.")
            return {"request": _public(request), "package": {}, "duplicate": False}
        if _baseline_integrity_hash(baseline) != baseline.content_hash:
            self._dead_letter(request.delta_request_id, "baseline_hash_failure", "Baseline content hash does not match its manifest.")
            return {"request": _public(request), "package": {}, "duplicate": False}
        if baseline.subject_id and request.subject_id and baseline.subject_id != request.subject_id:
            self._dead_letter(request.delta_request_id, "subject_mismatch", "Request subject does not match validated baseline subject.")
            return {"request": _public(request), "package": {}, "duplicate": False}
        if baseline.environment != request.environment and request.request_type != DeltaRequestType.REPLAY:
            self._dead_letter(request.delta_request_id, "environment_mismatch", "Cross-environment delta blocked outside replay context.")
            return {"request": _public(request), "package": {}, "duplicate": False}
        self._checkpoint(request, "baseline_validated")
        package = self._build_package(baseline, request, payload)
        self._packages[package.delta_package_id] = package
        self._request_to_package[request.delta_request_id] = package.delta_package_id
        self._audit_event("delta_package_created", package.delta_package_id, "Structured workflow delta package produced for EO-CD.")
        return {"request": _public(request), "package": _public(package), "duplicate": False}

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._baselines = {}
        self._requests = {}
        self._packages = {}
        self._request_to_package = {}
        for item in snapshot.get("baselineInventory", ()):
            baseline = self._baseline_from_public(item)
            self._baselines[baseline.baseline_id] = baseline
        for item in snapshot.get("deltaRequestQueue", ()):
            request = self._request_from_public(item)
            self._requests[request.delta_request_id] = request
        for item in snapshot.get("deltaPackages", ()):
            package = self._package_from_public(item)
            self._packages[package.delta_package_id] = package
            self._request_to_package[package.delta_request_id] = package.delta_package_id
        self._audit_event("restart_recovery", "EO-CH", "Workflow Delta Engine restored from snapshot.")

    def export_package(self, package_id: str, fmt: str = "json") -> str:
        if package_id not in self._packages:
            self._dead_letter(package_id or "unknown_package", "delta_package_unavailable", "Delta package unavailable for export.")
            return ""
        package = self._packages[package_id]
        data = _public(package)
        self._audit_event("delta_exported", package_id, fmt)
        if fmt.lower() == "markdown":
            return "\n".join(
                (
                    f"# Workflow Delta Package {package.delta_package_id}",
                    "",
                    f"- Baseline: {package.baseline_id}",
                    f"- Highest materiality: {package.highest_materiality.value}",
                    f"- Full reassessment required: {package.full_reassessment_required}",
                    f"- Minimum revision scope: {', '.join(package.minimum_revision_scope) or 'none'}",
                    f"- Recommended sequence: {', '.join(package.recommended_sequence) or 'none'}",
                    f"- Content hash: {package.content_hash}",
                )
            )
        return json.dumps(data, sort_keys=True, indent=2, default=str)

    def replay(self, package_id: str) -> dict[str, Any]:
        if package_id not in self._packages:
            self._dead_letter(package_id or "unknown_package", "delta_package_unavailable", "Delta package unavailable for replay.")
            return {"replayMode": True, "productionMutation": False, "packageId": package_id, "error": "delta_package_unavailable", "missionCreated": False, "officeWakeIssued": False, "brokerMutation": False}
        package = self._packages[package_id]
        self._audit_event("delta_replayed", package_id, "Replay inspected package without production mutation.")
        return {
            "replayMode": True,
            "productionMutation": False,
            "packageId": package.delta_package_id,
            "baselineId": package.baseline_id,
            "fieldChanges": len(package.field_changes),
            "officeImpacts": len(package.office_impacts),
            "missionCreated": False,
            "officeWakeIssued": False,
            "brokerMutation": False,
        }

    def request_manual_review(self, package_id: str, action: str, reason: str) -> dict[str, Any]:
        if package_id not in self._packages:
            self._dead_letter(package_id or "unknown_package", "delta_package_unavailable", "Delta package unavailable for manual review.")
            return {"reviewId": "", "packageId": package_id, "action": action, "reason": reason, "accepted": False, "blockedByFreshness": False, "createsNewPackageVersion": False, "authorizesOfficeActivation": False, "authorizesMission": False, "timestamp": utc_timestamp(), "error": "delta_package_unavailable"}
        package = self._packages[package_id]
        blocked = bool(package.blocked_scope and action == "mark_change_immaterial")
        review = {
            "reviewId": f"CH-REV-{len(self._manual_reviews) + 1:06d}",
            "packageId": package_id,
            "action": action,
            "reason": reason,
            "accepted": bool(reason) and not blocked,
            "blockedByFreshness": blocked,
            "createsNewPackageVersion": bool(reason) and not blocked,
            "authorizesOfficeActivation": False,
            "authorizesMission": False,
            "timestamp": utc_timestamp(),
        }
        self._manual_reviews.append(review)
        self._audit_event("manual_review_requested", package_id, action)
        return review

    def comparator_inventory(self) -> tuple[dict[str, Any], ...]:
        return (
            {"comparatorId": "scalar_exact", "supportedDataType": "scalar", "normalizationMethod": "string/boolean canonicalization", "tolerancePolicy": "exact", "outputType": "FieldChange"},
            {"comparatorId": "numeric_tolerance", "supportedDataType": "decimal", "normalizationMethod": "Decimal string", "tolerancePolicy": "contextual percent threshold", "outputType": "FieldChange"},
            {"comparatorId": "collection_set", "supportedDataType": "list/tuple/set", "normalizationMethod": "sorted canonical set", "tolerancePolicy": "set add/remove", "outputType": "EvidenceChange/FieldChange"},
            {"comparatorId": "structured_record", "supportedDataType": "dict", "normalizationMethod": "flattened dotted paths", "tolerancePolicy": "path-specific", "outputType": "FieldChange"},
            {"comparatorId": "market_state", "supportedDataType": "market fields", "normalizationMethod": "field map", "tolerancePolicy": "price/spread/volume thresholds", "outputType": "Materiality"},
            {"comparatorId": "broker_position", "supportedDataType": "broker/order/position", "normalizationMethod": "quantity/fill/cash fields", "tolerancePolicy": "broker truth material by default", "outputType": "OfficeImpact"},
            {"comparatorId": "portfolio_policy", "supportedDataType": "portfolio/policy", "normalizationMethod": "policy and exposure keys", "tolerancePolicy": "risk policy changes material", "outputType": "ProductImpact"},
            {"comparatorId": "workflow_graph", "supportedDataType": "workflow nodes", "normalizationMethod": "node id and office id sets", "tolerancePolicy": "token path preservation", "outputType": "WorkflowNodeDelta"},
        )

    def _build_package(self, baseline: DeltaBaseline, request: DeltaAnalysisRequest, payload: dict[str, Any]) -> DeltaPackage:
        current = dict(payload.get("currentState", payload.get("current_state", {})) or {})
        prior_state = {
            "inputs": baseline.input_manifest,
            "outputs": baseline.output_manifest,
            "assumptions": baseline.assumption_manifest,
            "policy": baseline.policy_manifest,
            "dependencies": baseline.dependency_manifest,
            "workflow": baseline.workflow_manifest,
        }
        current_state = {
            "inputs": dict(current.get("inputManifest", current.get("inputs", baseline.input_manifest)) or {}),
            "outputs": dict(current.get("outputManifest", current.get("outputs", baseline.output_manifest)) or {}),
            "assumptions": dict(current.get("assumptionManifest", current.get("assumptions", baseline.assumption_manifest)) or {}),
            "policy": dict(current.get("policyManifest", current.get("policy", baseline.policy_manifest)) or {}),
            "dependencies": dict(current.get("dependencyManifest", current.get("dependencies", baseline.dependency_manifest)) or {}),
            "workflow": dict(current.get("workflowManifest", current.get("workflow", baseline.workflow_manifest)) or {}),
        }
        fields = self._field_changes(prior_state, current_state, baseline, request)
        sections = self._section_changes(fields)
        evidence = self._evidence_changes(baseline, request)
        freshness_refs = self._freshness_references(baseline, request)
        memory_refs, reusable = self._memory_reuse_references(baseline, request)
        products = self._product_impacts(baseline, request, fields, sections, freshness_refs, reusable)
        offices = self._office_impacts(request, fields, products)
        dependencies = self._dependency_impacts(fields, baseline, products, offices)
        nodes = self._workflow_node_deltas(baseline, current_state["workflow"], offices)
        highest = _highest_materiality(tuple(item.materiality for item in fields) + tuple(item.materiality for item in evidence))
        full = highest == DeltaMateriality.CRITICAL or any(item.revision_requirement == RevisionRequirement.FULL_REVISION for item in products)
        deterministic_scope = tuple(sorted({item.field_path for item in fields if _revision_for_change(item) == RevisionRequirement.RECOMPUTE_DETERMINISTIC}))
        partial_scope = tuple(sorted({item.field_path for item in fields if _revision_for_change(item) == RevisionRequirement.PARTIAL_REVISION}))
        blocked_scope = tuple(sorted({item.field_path for item in fields if _revision_for_change(item) in {RevisionRequirement.BLOCK_USE, RevisionRequirement.RESOLVE_CONTRADICTION}}))
        minimum = tuple(sorted(set(deterministic_scope + partial_scope + blocked_scope + tuple(request.requested_fields))))
        sequence = tuple(item.office_id for item in offices if item.impact_decision in {OfficeImpactDecision.DETERMINISTIC_SERVICE_ONLY, OfficeImpactDecision.VALIDATION_ONLY, OfficeImpactDecision.PARTIAL_REACTIVATION, OfficeImpactDecision.FULL_REACTIVATION, OfficeImpactDecision.CONDITIONALLY_REQUIRED})
        cost = self._cost_reduction_evidence(products, offices, full)
        package = DeltaPackage(
            delta_package_id=f"CH-PKG-{len(self._packages) + 1:06d}",
            package_version=1,
            delta_request_id=request.delta_request_id,
            baseline_id=baseline.baseline_id,
            subject_type=request.subject_type or baseline.subject_type,
            subject_id=request.subject_id or baseline.subject_id,
            environment=request.environment,
            highest_materiality=highest,
            full_reassessment_required=full,
            field_changes=fields,
            section_changes=sections,
            evidence_changes=evidence,
            product_impacts=products,
            office_impacts=offices,
            dependency_impacts=dependencies,
            workflow_node_deltas=nodes,
            reusable_cache_record_ids=tuple(sorted(set(reusable))),
            validation_only_record_ids=tuple(item.cache_record_id for item in products if item.revision_requirement == RevisionRequirement.REUSE_WITH_VALIDATION and item.cache_record_id),
            deterministic_recompute_scope=deterministic_scope,
            partial_revision_scope=partial_scope,
            blocked_scope=blocked_scope,
            minimum_revision_scope=minimum,
            recommended_sequence=sequence,
            mission_planner_feed=self._mission_planner_feed(request, highest, full, minimum, sequence),
            cost_reduction_evidence=cost,
            freshness_decision_references=freshness_refs,
            memory_retrieval_references=memory_refs,
            law_ch=self._law_state(),
            created_at=utc_timestamp(),
            content_hash="",
        )
        return replace(package, content_hash=_hash(_public(replace(package, content_hash=""))))

    def _field_changes(self, prior: dict[str, Any], current: dict[str, Any], baseline: DeltaBaseline, request: DeltaAnalysisRequest) -> tuple[FieldChange, ...]:
        prior_flat = _flatten(prior)
        current_flat = _flatten(current)
        paths = sorted(set(prior_flat) | set(current_flat))
        changes: list[FieldChange] = []
        for index, path in enumerate(paths, start=1):
            prior_value = prior_flat.get(path)
            current_value = current_flat.get(path)
            change_type = _change_type(path, prior_value, current_value, baseline, request)
            absolute, percent = _numeric_delta(prior_value, current_value)
            materiality, score = _materiality(path, change_type, absolute, percent, request)
            dependency_ids = tuple(_dependency_ids_for(path, baseline.dependency_manifest))
            product_ids = baseline.product_record_ids or baseline.cache_record_ids
            changes.append(
                FieldChange(
                    field_change_id=f"CH-FLD-{len(self._packages) + 1:06d}-{index:03d}",
                    field_path=path,
                    change_type=change_type,
                    prior_value_reference=f"{baseline.baseline_id}:{path}" if prior_value is not None else "",
                    current_value_reference=f"{request.delta_request_id}:{path}" if current_value is not None else "",
                    prior_normalized_value=_json_value(prior_value),
                    current_normalized_value=_json_value(current_value),
                    absolute_delta=str(absolute) if absolute is not None else "",
                    percentage_delta=str(percent) if percent is not None else "",
                    units=_units_for(path),
                    comparison_method=_comparison_method(prior_value, current_value, path),
                    tolerance_used=str(_tolerance_for(path, request)),
                    materiality=materiality,
                    materiality_score=score,
                    affected_dependency_ids=dependency_ids,
                    affected_product_ids=product_ids,
                    explanation=_field_explanation(path, change_type, materiality),
                )
            )
        if not changes:
            changes.append(
                FieldChange(
                    field_change_id=f"CH-FLD-{len(self._packages) + 1:06d}-001",
                    field_path="workflow",
                    change_type=ChangeType.UNCHANGED,
                    prior_value_reference=baseline.baseline_id,
                    current_value_reference=request.delta_request_id,
                    prior_normalized_value="unchanged",
                    current_normalized_value="unchanged",
                    absolute_delta="",
                    percentage_delta="",
                    units="",
                    comparison_method="empty_manifest_guard",
                    tolerance_used="0",
                    materiality=DeltaMateriality.NONE,
                    materiality_score=0.0,
                    affected_dependency_ids=(),
                    affected_product_ids=baseline.product_record_ids or baseline.cache_record_ids,
                    explanation="No structured field differences were supplied.",
                )
            )
        return tuple(changes)

    def _section_changes(self, fields: tuple[FieldChange, ...]) -> tuple[SectionChange, ...]:
        sections: dict[str, list[FieldChange]] = {}
        for field in fields:
            sections.setdefault(field.field_path.split(".")[0], []).append(field)
        rows = []
        for index, (section, items) in enumerate(sorted(sections.items()), start=1):
            highest = _highest_materiality(tuple(item.materiality for item in items))
            changed = tuple(item.field_path for item in items if item.change_type != ChangeType.UNCHANGED)
            unchanged = tuple(item.field_path for item in items if item.change_type == ChangeType.UNCHANGED)
            rows.append(
                SectionChange(
                    section_change_id=f"CH-SEC-{len(self._packages) + 1:06d}-{index:03d}",
                    section_name=section,
                    change_type=ChangeType.UNCHANGED if not changed else ChangeType.MODIFIED,
                    changed_fields=changed,
                    unchanged_fields=unchanged,
                    materiality=highest,
                    revision_requirement=_revision_for_materiality(highest),
                    explanation=f"Section {section} has {len(changed)} changed fields and {len(unchanged)} preserved fields.",
                )
            )
        return tuple(rows)

    def _evidence_changes(self, baseline: DeltaBaseline, request: DeltaAnalysisRequest) -> tuple[EvidenceChange, ...]:
        prior = set(baseline.evidence_record_ids)
        current = set(request.current_evidence_record_ids)
        rows: list[EvidenceChange] = []
        for index, evidence_id in enumerate(sorted(prior | current), start=1):
            if evidence_id in prior and evidence_id in current:
                change, materiality = ChangeType.UNCHANGED, DeltaMateriality.NONE
            elif evidence_id in current:
                change, materiality = ChangeType.ADDED, DeltaMateriality.MATERIAL if "earn" in evidence_id.lower() or "guide" in evidence_id.lower() else DeltaMateriality.MINOR
            else:
                change, materiality = ChangeType.REMOVED, DeltaMateriality.MATERIAL
            rows.append(EvidenceChange(f"CH-EVD-{len(self._packages) + 1:06d}-{index:03d}", evidence_id, change, materiality, False, f"Evidence {evidence_id} is {change.value}."))
        return tuple(rows)

    def _freshness_references(self, baseline: DeltaBaseline, request: DeltaAnalysisRequest) -> tuple[str, ...]:
        references: list[str] = []
        for record_id in tuple(dict.fromkeys(baseline.information_record_ids + request.current_information_record_ids)):
            decision = self._freshness.evaluate_record(record_id, {"decisionUseClass": request.decision_use_class, "missionType": request.mission_type, "subjectType": request.subject_type, "subjectId": request.subject_id, "environment": request.environment})
            references.append(decision.freshness_decision_id)
        return tuple(references)

    def _memory_reuse_references(self, baseline: DeltaBaseline, request: DeltaAnalysisRequest) -> tuple[tuple[str, ...], tuple[str, ...]]:
        result = self._memory.query(
            {
                "requesterType": "engine",
                "requesterId": "WorkflowDeltaEngine",
                "missionId": request.current_mission_plan_id,
                "missionType": request.mission_type,
                "decisionUseClass": request.decision_use_class,
                "environment": request.environment,
                "subjectType": request.subject_type,
                "subjectId": request.subject_id,
                "requestedProductTypes": tuple(CacheProductType(value).value for value in _safe_product_types(request.requested_products)),
                "requestedFields": request.requested_fields,
                "requestedSections": request.requested_sections,
                "allowHistorical": request.request_type == DeltaRequestType.REPLAY,
            }
        )
        return (result.retrieval_result_id,), result.selected_cache_record_ids

    def _product_impacts(self, baseline: DeltaBaseline, request: DeltaAnalysisRequest, fields: tuple[FieldChange, ...], sections: tuple[SectionChange, ...], freshness_refs: tuple[str, ...], reusable: tuple[str, ...]) -> tuple[ProductImpact, ...]:
        records = tuple(dict.fromkeys(baseline.cache_record_ids + request.current_cache_record_ids + baseline.product_record_ids))
        if not records:
            records = ("prior_workflow_product",)
        changed_fields = tuple(item.field_path for item in fields if item.change_type != ChangeType.UNCHANGED)
        reusable_fields = tuple(item.field_path for item in fields if item.change_type == ChangeType.UNCHANGED)
        affected_sections = tuple(item.section_name for item in sections if item.change_type != ChangeType.UNCHANGED)
        reusable_sections = tuple(item.section_name for item in sections if item.change_type == ChangeType.UNCHANGED)
        highest = _highest_materiality(tuple(item.materiality for item in fields))
        revision = _revision_for_materiality(highest)
        if any(item.change_type == ChangeType.CONTRADICTED for item in fields):
            revision = RevisionRequirement.RESOLVE_CONTRADICTION
        rows = []
        for index, record_id in enumerate(records, start=1):
            item_revision = RevisionRequirement.REUSE_EXACT if record_id in reusable and not changed_fields else revision
            rows.append(
                ProductImpact(
                    product_impact_id=f"CH-PRD-{len(self._packages) + 1:06d}-{index:03d}",
                    product_record_id=record_id if record_id not in baseline.cache_record_ids else "",
                    cache_record_id=record_id if record_id in baseline.cache_record_ids or record_id in request.current_cache_record_ids else "",
                    affected_fields=changed_fields,
                    affected_sections=affected_sections,
                    reusable_fields=reusable_fields,
                    reusable_sections=reusable_sections,
                    revision_requirement=item_revision,
                    reuse_decision_reference=",".join(freshness_refs),
                    reason=f"Product impact classified as {item_revision.value}; unchanged scope is preserved.",
                )
            )
        return tuple(rows)

    def _office_impacts(self, request: DeltaAnalysisRequest, fields: tuple[FieldChange, ...], products: tuple[ProductImpact, ...]) -> tuple[OfficeImpact, ...]:
        offices: dict[str, tuple[OfficeImpactDecision, set[str], str, int, int]] = {
            "Seeker": (OfficeImpactDecision.NOT_REQUIRED, set(), "Discovery unaffected by bounded delta.", 0, 0),
            "Librarian": (OfficeImpactDecision.REUSE_PRIOR_OUTPUT, set(), "Evidence unchanged or reusable unless source facts changed.", 0, 0),
            "Analyst": (OfficeImpactDecision.REUSE_PRIOR_OUTPUT, set(), "Analytical product reusable unless thesis or valuation changed.", 0, 0),
            "Risk": (OfficeImpactDecision.REUSE_PRIOR_OUTPUT, set(), "Risk reusable unless position, exposure, policy, or contradiction changed.", 0, 0),
            "Trader": (OfficeImpactDecision.NOT_REQUIRED, set(), "Trader is not required unless broker or lifecycle state changed.", 0, 0),
            "Performance Truth": (OfficeImpactDecision.NOT_REQUIRED, set(), "Performance truth is deterministic service only when broker or portfolio state changes.", 0, 0),
        }
        for field in fields:
            path = field.field_path.lower()
            if field.change_type == ChangeType.UNCHANGED:
                continue
            if any(word in path for word in ("price", "bid", "ask", "spread", "valuation", "ratio")):
                _promote(offices, "Analyst", OfficeImpactDecision.VALIDATION_ONLY, field.field_path, "Market or valuation field changed; prior thesis can often be validated without full rewrite.", 120, 0)
                _promote(offices, "Performance Truth", OfficeImpactDecision.DETERMINISTIC_SERVICE_ONLY, field.field_path, "Price-dependent calculations can be recomputed deterministically.", 20, 0)
            if any(word in path for word in ("earnings", "guidance", "revenue", "filing", "evidence")):
                _promote(offices, "Librarian", OfficeImpactDecision.PARTIAL_REACTIVATION, field.field_path, "New source evidence requires retrieval/validation scope.", 180, 1)
                _promote(offices, "Analyst", OfficeImpactDecision.PARTIAL_REACTIVATION, field.field_path, "Fundamental change affects analytical sections.", 300, 1)
            if any(word in path for word in ("quantity", "exposure", "risk", "stop", "target", "policy", "concentration")):
                _promote(offices, "Risk", OfficeImpactDecision.PARTIAL_REACTIVATION, field.field_path, "Risk or portfolio-governed field changed.", 180, 0)
            if any(word in path for word in ("fill", "broker", "order", "cash", "buying_power")):
                _promote(offices, "Trader", OfficeImpactDecision.CONDITIONALLY_REQUIRED, field.field_path, "Broker/order state changed; Trader review may be required after EO-CD planning.", 120, 0)
                _promote(offices, "Performance Truth", OfficeImpactDecision.DETERMINISTIC_SERVICE_ONLY, field.field_path, "Broker truth reconciliation is deterministic before office work.", 60, 0)
            if field.change_type == ChangeType.CONTRADICTED:
                _promote(offices, "Analyst", OfficeImpactDecision.PARTIAL_REACTIVATION, field.field_path, "Contradictory evidence blocks exact thesis reuse.", 300, 1)
                if request.position_id:
                    _promote(offices, "Risk", OfficeImpactDecision.PARTIAL_REACTIVATION, field.field_path, "Contradiction affects an active position context.", 180, 0)
        if any(item.revision_requirement == RevisionRequirement.FULL_REVISION for item in products):
            _promote(offices, "Analyst", OfficeImpactDecision.FULL_REACTIVATION, "full_reassessment", "Full product revision is explicitly justified.", 600, 2)
        rows = []
        for index, (office, (decision, scope, reason, runtime, calls)) in enumerate(offices.items(), start=1):
            rows.append(
                OfficeImpact(
                    office_impact_id=f"CH-OFC-{len(self._packages) + 1:06d}-{index:03d}",
                    office_id=office,
                    prior_role="prior_output_owner" if office not in {"Performance Truth"} else "deterministic_service",
                    impact_decision=decision,
                    required_scope=tuple(sorted(scope)),
                    excluded_reason="" if decision not in {OfficeImpactDecision.NOT_REQUIRED, OfficeImpactDecision.REUSE_PRIOR_OUTPUT} else reason,
                    estimated_runtime_seconds=runtime,
                    estimated_api_calls=calls,
                    reason=reason,
                )
            )
        return tuple(rows)

    def _dependency_impacts(self, fields: tuple[FieldChange, ...], baseline: DeltaBaseline, products: tuple[ProductImpact, ...], offices: tuple[OfficeImpact, ...]) -> tuple[DependencyImpact, ...]:
        rows = []
        affected_products = tuple(item.cache_record_id or item.product_record_id for item in products if item.revision_requirement != RevisionRequirement.REUSE_EXACT)
        affected_offices = tuple(item.office_id for item in offices if item.impact_decision not in {OfficeImpactDecision.NOT_REQUIRED, OfficeImpactDecision.REUSE_PRIOR_OUTPUT})
        for index, field in enumerate((item for item in fields if item.change_type != ChangeType.UNCHANGED), start=1):
            rows.append(
                DependencyImpact(
                    dependency_impact_id=f"CH-DEP-{len(self._packages) + 1:06d}-{index:03d}",
                    changed_input=field.field_path,
                    dependency_path=field.affected_dependency_ids or (field.field_path,),
                    affected_calculations=tuple(_calculation_for(field.field_path)),
                    affected_products=affected_products,
                    affected_offices=affected_offices,
                    propagation_boundary="field_scope" if field.materiality in {DeltaMateriality.MINOR, DeltaMateriality.IMMATERIAL} else "section_scope",
                    materiality=field.materiality,
                )
            )
        return tuple(rows)

    def _workflow_node_deltas(self, baseline: DeltaBaseline, current_workflow: dict[str, Any], offices: tuple[OfficeImpact, ...]) -> tuple[WorkflowNodeDelta, ...]:
        prior_nodes = set(_node_ids(baseline.workflow_manifest))
        current_nodes = set(_node_ids(current_workflow)) or prior_nodes
        required = {item.office_id for item in offices if item.impact_decision not in {OfficeImpactDecision.NOT_REQUIRED, OfficeImpactDecision.REUSE_PRIOR_OUTPUT}}
        nodes = sorted(prior_nodes | current_nodes | required)
        return tuple(
            WorkflowNodeDelta(
                node_delta_id=f"CH-NOD-{len(self._packages) + 1:06d}-{index:03d}",
                node_id=node,
                office_id=node,
                change_type=ChangeType.ADDED if node in current_nodes - prior_nodes else (ChangeType.REMOVED if node in prior_nodes - current_nodes else ChangeType.UNCHANGED),
                prior_required=node in prior_nodes,
                current_required=node in current_nodes or node in required,
                token_path_preserved=True,
                reason="Workflow graph comparison preserves token path and does not mark nodes executing.",
            )
            for index, node in enumerate(nodes, start=1)
        )

    def _cost_reduction_evidence(self, products: tuple[ProductImpact, ...], offices: tuple[OfficeImpact, ...], full: bool) -> dict[str, Any]:
        offices_avoided = sum(1 for item in offices if item.impact_decision in {OfficeImpactDecision.NOT_REQUIRED, OfficeImpactDecision.REUSE_PRIOR_OUTPUT})
        api_calls_avoided = sum(max(1, item.estimated_api_calls) for item in offices if item.impact_decision in {OfficeImpactDecision.NOT_REQUIRED, OfficeImpactDecision.REUSE_PRIOR_OUTPUT})
        reused = sum(1 for item in products if item.revision_requirement in {RevisionRequirement.REUSE_EXACT, RevisionRequirement.REUSE_WITH_VALIDATION})
        partial = sum(1 for item in products if item.revision_requirement == RevisionRequirement.PARTIAL_REVISION)
        return {
            "productsReused": reused,
            "productsPartiallyRevised": partial,
            "officesAvoided": offices_avoided,
            "apiCallsAvoided": api_calls_avoided,
            "tokensAvoided": api_calls_avoided * 2500,
            "runtimeSecondsAvoided": offices_avoided * 120,
            "estimatedCostAvoided": round((api_calls_avoided * 0.01) + (reused * 0.005), 4),
            "estimateBasis": "deterministic office exclusions and reusable product impacts",
            "estimateConfidence": 0.82 if not full else 0.62,
        }

    def _mission_planner_feed(self, request: DeltaAnalysisRequest, highest: DeltaMateriality, full: bool, scope: tuple[str, ...], sequence: tuple[str, ...]) -> dict[str, Any]:
        return {
            "targetEngine": "EO-CD Enterprise Mission Planner",
            "submitted": False,
            "deltaPackageReady": True,
            "missionType": request.mission_type or "delta_review",
            "decisionUseClass": request.decision_use_class,
            "subjectType": request.subject_type,
            "subjectId": request.subject_id,
            "changedFields": scope,
            "fullReassessmentRequired": full,
            "highestMateriality": highest.value,
            "recommendedOffices": sequence,
            "reason": "EO-CH supplies smallest justified delta scope; EO-CD must decide whether to create a mission.",
        }

    def _request_from_payload(self, payload: dict[str, Any]) -> DeltaAnalysisRequest:
        return DeltaAnalysisRequest(
            delta_request_id=str(payload.get("deltaRequestId", payload.get("delta_request_id", f"CH-REQ-{len(self._requests) + 1:06d}"))),
            request_type=_request_type(payload.get("requestType", payload.get("request_type", DeltaRequestType.MANUAL_COMPARISON.value))),
            baseline_id=str(payload.get("baselineId", payload.get("baseline_id", ""))),
            current_mission_plan_id=str(payload.get("currentMissionPlanId", payload.get("current_mission_plan_id", ""))),
            current_workflow_id=str(payload.get("currentWorkflowId", payload.get("current_workflow_id", ""))),
            source_event_ids=tuple(payload.get("sourceEventIds", payload.get("source_event_ids", ())) or ()),
            source_event_group_ids=tuple(payload.get("sourceEventGroupIds", payload.get("source_event_group_ids", ())) or ()),
            current_information_record_ids=tuple(payload.get("currentInformationRecordIds", payload.get("current_information_record_ids", ())) or ()),
            current_cache_record_ids=tuple(payload.get("currentCacheRecordIds", payload.get("current_cache_record_ids", ())) or ()),
            current_evidence_record_ids=tuple(payload.get("currentEvidenceRecordIds", payload.get("current_evidence_record_ids", ())) or ()),
            subject_type=str(payload.get("subjectType", payload.get("subject_type", "enterprise"))),
            subject_id=str(payload.get("subjectId", payload.get("subject_id", "ARGOS"))),
            mission_type=str(payload.get("missionType", payload.get("mission_type", ""))),
            decision_use_class=str(payload.get("decisionUseClass", payload.get("decision_use_class", "tactical_analysis"))),
            requested_fields=tuple(payload.get("requestedFields", payload.get("requested_fields", ())) or ()),
            requested_sections=tuple(payload.get("requestedSections", payload.get("requested_sections", ())) or ()),
            requested_products=tuple(payload.get("requestedProducts", payload.get("requested_products", ())) or ()),
            environment=str(payload.get("environment", "paper")),
            submitted_by_type=str(payload.get("submittedByType", payload.get("submitted_by_type", "commander"))),
            submitted_by_id=str(payload.get("submittedById", payload.get("submitted_by_id", "Commander"))),
            submitted_at=str(payload.get("submittedAt", payload.get("submitted_at", utc_timestamp()))),
        )

    def _change_summary(self, latest: DeltaPackage | None) -> dict[str, Any]:
        if not latest:
            return {}
        counts = {item.value: 0 for item in ChangeType}
        for field in latest.field_changes:
            counts[field.change_type.value] += 1
        return {
            "packageId": latest.delta_package_id,
            "highestMateriality": latest.highest_materiality.value,
            "fullReassessmentRequired": latest.full_reassessment_required,
            "changeCounts": counts,
            "minimumRevisionScope": latest.minimum_revision_scope,
            "recommendedSequence": latest.recommended_sequence,
        }

    def _law_state(self) -> dict[str, Any]:
        return {
            "changeImpliesFullReassessment": False,
            "validatedBaselineRequired": True,
            "deterministicComparisonFirst": True,
            "executesWork": False,
            "wakesOffices": False,
            "createsMissions": False,
            "authorizesMissions": False,
            "authorizesExpenditure": False,
            "paidApiCalls": 0,
            "aiInvocations": 0,
            "brokerOrdersSubmitted": 0,
            "positionMutations": 0,
            "productOverwrite": False,
            "freshnessAuthority": "EO-CF",
            "memoryAuthority": "EO-CG",
            "missionAuthority": "EO-CD",
        }

    def _checkpoint(self, request: DeltaAnalysisRequest, stage: str) -> None:
        self._checkpoints.append({"checkpointId": f"CH-CHK-{len(self._checkpoints) + 1:06d}", "deltaRequestId": request.delta_request_id, "stage": stage, "timestamp": utc_timestamp()})

    def _dead_letter(self, request_id: str, reason_code: str, explanation: str) -> None:
        self._dead_letters.append({"deadLetterId": f"CH-DLQ-{len(self._dead_letters) + 1:06d}", "deltaRequestId": request_id, "reasonCode": reason_code, "explanation": explanation, "timestamp": utc_timestamp()})
        self._alerts.append({"alertId": f"CH-ALT-{len(self._alerts) + 1:06d}", "severity": "WARNING", "reasonCode": reason_code, "requiredAction": "manual_review", "summary": explanation, "timestamp": utc_timestamp()})
        self._audit_event("delta_denied", request_id, reason_code)

    def _audit_event(self, action: str, target: str, reason: str) -> None:
        self._audit.append({"auditId": f"CH-AUD-{len(self._audit) + 1:06d}", "timestamp": utc_timestamp(), "action": action, "target": target, "reason": reason})

    def _baseline_from_public(self, item: dict[str, Any]) -> DeltaBaseline:
        return DeltaBaseline(
            baseline_id=str(item["baseline_id"]),
            mission_id=str(item.get("mission_id", "")),
            mission_plan_id=str(item.get("mission_plan_id", "")),
            workflow_id=str(item.get("workflow_id", "")),
            decision_object_id=str(item.get("decision_object_id", "")),
            subject_type=str(item.get("subject_type", "")),
            subject_id=str(item.get("subject_id", "")),
            ticker=str(item.get("ticker", "")),
            position_id=str(item.get("position_id", "")),
            order_id=str(item.get("order_id", "")),
            portfolio_id=str(item.get("portfolio_id", "")),
            strategy_id=str(item.get("strategy_id", "")),
            environment=str(item.get("environment", "")),
            cache_record_ids=tuple(item.get("cache_record_ids", ())),
            information_record_ids=tuple(item.get("information_record_ids", ())),
            evidence_record_ids=tuple(item.get("evidence_record_ids", ())),
            product_record_ids=tuple(item.get("product_record_ids", ())),
            input_manifest=dict(item.get("input_manifest", {})),
            output_manifest=dict(item.get("output_manifest", {})),
            assumption_manifest=dict(item.get("assumption_manifest", {})),
            policy_manifest=dict(item.get("policy_manifest", {})),
            dependency_manifest=dict(item.get("dependency_manifest", {})),
            workflow_manifest=dict(item.get("workflow_manifest", {})),
            schema_versions={str(k): str(v) for k, v in dict(item.get("schema_versions", {})).items()},
            content_hashes={str(k): str(v) for k, v in dict(item.get("content_hashes", {})).items()},
            validation_state=str(item.get("validation_state", "")),
            validated_at=str(item.get("validated_at", "")),
            created_at=str(item.get("created_at", "")),
            content_hash=str(item.get("content_hash", "")),
        )

    def _request_from_public(self, item: dict[str, Any]) -> DeltaAnalysisRequest:
        payload = {key: value for key, value in item.items()}
        return DeltaAnalysisRequest(
            delta_request_id=str(payload["delta_request_id"]),
            request_type=_request_type(payload["request_type"]),
            baseline_id=str(payload["baseline_id"]),
            current_mission_plan_id=str(payload.get("current_mission_plan_id", "")),
            current_workflow_id=str(payload.get("current_workflow_id", "")),
            source_event_ids=tuple(payload.get("source_event_ids", ())),
            source_event_group_ids=tuple(payload.get("source_event_group_ids", ())),
            current_information_record_ids=tuple(payload.get("current_information_record_ids", ())),
            current_cache_record_ids=tuple(payload.get("current_cache_record_ids", ())),
            current_evidence_record_ids=tuple(payload.get("current_evidence_record_ids", ())),
            subject_type=str(payload.get("subject_type", "")),
            subject_id=str(payload.get("subject_id", "")),
            mission_type=str(payload.get("mission_type", "")),
            decision_use_class=str(payload.get("decision_use_class", "")),
            requested_fields=tuple(payload.get("requested_fields", ())),
            requested_sections=tuple(payload.get("requested_sections", ())),
            requested_products=tuple(payload.get("requested_products", ())),
            environment=str(payload.get("environment", "")),
            submitted_by_type=str(payload.get("submitted_by_type", "")),
            submitted_by_id=str(payload.get("submitted_by_id", "")),
            submitted_at=str(payload.get("submitted_at", "")),
        )

    def _package_from_public(self, item: dict[str, Any]) -> DeltaPackage:
        return DeltaPackage(
            delta_package_id=str(item["delta_package_id"]),
            package_version=int(item.get("package_version", 1)),
            delta_request_id=str(item["delta_request_id"]),
            baseline_id=str(item["baseline_id"]),
            subject_type=str(item.get("subject_type", "")),
            subject_id=str(item.get("subject_id", "")),
            environment=str(item.get("environment", "")),
            highest_materiality=_materiality_enum(item.get("highest_materiality", DeltaMateriality.NONE.value)),
            full_reassessment_required=bool(item.get("full_reassessment_required", False)),
            field_changes=tuple(_field_from_public(value) for value in item.get("field_changes", ())),
            section_changes=tuple(_section_from_public(value) for value in item.get("section_changes", ())),
            evidence_changes=tuple(_evidence_from_public(value) for value in item.get("evidence_changes", ())),
            product_impacts=tuple(_product_from_public(value) for value in item.get("product_impacts", ())),
            office_impacts=tuple(_office_from_public(value) for value in item.get("office_impacts", ())),
            dependency_impacts=tuple(_dependency_from_public(value) for value in item.get("dependency_impacts", ())),
            workflow_node_deltas=tuple(_node_from_public(value) for value in item.get("workflow_node_deltas", ())),
            reusable_cache_record_ids=tuple(item.get("reusable_cache_record_ids", ())),
            validation_only_record_ids=tuple(item.get("validation_only_record_ids", ())),
            deterministic_recompute_scope=tuple(item.get("deterministic_recompute_scope", ())),
            partial_revision_scope=tuple(item.get("partial_revision_scope", ())),
            blocked_scope=tuple(item.get("blocked_scope", ())),
            minimum_revision_scope=tuple(item.get("minimum_revision_scope", ())),
            recommended_sequence=tuple(item.get("recommended_sequence", ())),
            mission_planner_feed=dict(item.get("mission_planner_feed", {})),
            cost_reduction_evidence=dict(item.get("cost_reduction_evidence", {})),
            freshness_decision_references=tuple(item.get("freshness_decision_references", ())),
            memory_retrieval_references=tuple(item.get("memory_retrieval_references", ())),
            law_ch=dict(item.get("law_ch", {})),
            created_at=str(item.get("created_at", "")),
            content_hash=str(item.get("content_hash", "")),
        )


def _promote(offices: dict[str, tuple[OfficeImpactDecision, set[str], str, int, int]], office: str, decision: OfficeImpactDecision, scope: str, reason: str, runtime: int, calls: int) -> None:
    current = offices.get(office, (OfficeImpactDecision.NOT_REQUIRED, set(), "", 0, 0))
    rank = {
        OfficeImpactDecision.NOT_REQUIRED: 0,
        OfficeImpactDecision.REUSE_PRIOR_OUTPUT: 1,
        OfficeImpactDecision.DETERMINISTIC_SERVICE_ONLY: 2,
        OfficeImpactDecision.VALIDATION_ONLY: 3,
        OfficeImpactDecision.CONDITIONALLY_REQUIRED: 4,
        OfficeImpactDecision.PARTIAL_REACTIVATION: 5,
        OfficeImpactDecision.FULL_REACTIVATION: 6,
        OfficeImpactDecision.PROHIBITED: 7,
    }
    selected = decision if rank[decision] > rank[current[0]] else current[0]
    current[1].add(scope)
    offices[office] = (selected, current[1], reason, max(runtime, current[3]), max(calls, current[4]))


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        rows: dict[str, Any] = {}
        for key, item in value.items():
            rows.update(_flatten(item, f"{prefix}.{key}" if prefix else str(key)))
        return rows
    if isinstance(value, (list, tuple, set)):
        return {prefix: tuple(sorted(_json_value(item) for item in value))}
    return {prefix: value}


def _change_type(path: str, prior: Any, current: Any, baseline: DeltaBaseline, request: DeltaAnalysisRequest) -> ChangeType:
    if prior is None and current is not None:
        return ChangeType.ADDED
    if prior is not None and current is None:
        return ChangeType.REMOVED
    if path.startswith("policy.") and prior != current:
        return ChangeType.POLICY_CHANGED
    if path.startswith("schema_versions.") and prior != current:
        return ChangeType.SCHEMA_CHANGED
    if "contradiction" in path.lower() and prior != current:
        return ChangeType.CONTRADICTED
    if "superseded" in path.lower() and prior != current:
        return ChangeType.SUPERSEDED
    if "invalidated" in path.lower() and prior != current:
        return ChangeType.INVALIDATED
    return ChangeType.UNCHANGED if _normalize(prior) == _normalize(current) else ChangeType.MODIFIED


def _numeric_delta(prior: Any, current: Any) -> tuple[Decimal | None, Decimal | None]:
    try:
        p = Decimal(str(prior))
        c = Decimal(str(current))
    except (InvalidOperation, TypeError, ValueError):
        return None, None
    absolute = c - p
    percent = Decimal("0") if p == 0 else (absolute / abs(p)) * Decimal("100")
    return absolute, percent


def _materiality(path: str, change: ChangeType, absolute: Decimal | None, percent: Decimal | None, request: DeltaAnalysisRequest) -> tuple[DeltaMateriality, float]:
    if change == ChangeType.UNCHANGED:
        return DeltaMateriality.NONE, 0.0
    lowered = path.lower()
    if change in {ChangeType.CONTRADICTED, ChangeType.INVALIDATED, ChangeType.ENVIRONMENT_CHANGED}:
        return DeltaMateriality.CRITICAL, 1.0
    if change in {ChangeType.SUPERSEDED, ChangeType.POLICY_CHANGED, ChangeType.SCHEMA_CHANGED}:
        return DeltaMateriality.MAJOR, 0.85
    pct = abs(float(percent or Decimal("0")))
    if any(word in lowered for word in ("broker", "fill", "order", "quantity", "cash", "buying_power")):
        return (DeltaMateriality.MATERIAL, 0.7) if change != ChangeType.UNCHANGED else (DeltaMateriality.NONE, 0.0)
    if any(word in lowered for word in ("earnings", "guidance", "revenue", "risk", "stop", "target", "concentration")):
        return DeltaMateriality.MATERIAL, 0.72
    if any(word in lowered for word in ("price", "bid", "ask", "spread", "valuation")):
        if pct < 0.5:
            return DeltaMateriality.IMMATERIAL, 0.15
        if pct < 2:
            return DeltaMateriality.MINOR, 0.3
        return DeltaMateriality.MATERIAL, 0.68
    if any(word in lowered for word in ("format", "timestamp", "display")):
        return DeltaMateriality.IMMATERIAL, 0.1
    if request.mission_type in {"live_order_action", "broker_reconciliation"}:
        return DeltaMateriality.MATERIAL, 0.65
    return DeltaMateriality.MINOR, 0.35


def _revision_for_change(field: FieldChange) -> RevisionRequirement:
    if field.change_type == ChangeType.UNCHANGED:
        return RevisionRequirement.REUSE_EXACT
    if field.change_type == ChangeType.CONTRADICTED:
        return RevisionRequirement.RESOLVE_CONTRADICTION
    if field.change_type == ChangeType.INVALIDATED:
        return RevisionRequirement.BLOCK_USE
    return _revision_for_materiality(field.materiality)


def _revision_for_materiality(materiality: DeltaMateriality) -> RevisionRequirement:
    if materiality in {DeltaMateriality.NONE, DeltaMateriality.IMMATERIAL}:
        return RevisionRequirement.REUSE_EXACT
    if materiality == DeltaMateriality.MINOR:
        return RevisionRequirement.REUSE_WITH_VALIDATION
    if materiality == DeltaMateriality.MATERIAL:
        return RevisionRequirement.PARTIAL_REVISION
    if materiality == DeltaMateriality.MAJOR:
        return RevisionRequirement.FULL_REVISION
    if materiality == DeltaMateriality.CRITICAL:
        return RevisionRequirement.BLOCK_USE
    return RevisionRequirement.NO_ACTION


def _highest_materiality(values: tuple[DeltaMateriality, ...]) -> DeltaMateriality:
    rank = {DeltaMateriality.NONE: 0, DeltaMateriality.IMMATERIAL: 1, DeltaMateriality.MINOR: 2, DeltaMateriality.MATERIAL: 3, DeltaMateriality.MAJOR: 4, DeltaMateriality.CRITICAL: 5}
    return max(values, key=lambda item: rank[item]) if values else DeltaMateriality.NONE


def _dependency_ids_for(path: str, dependencies: dict[str, Any]) -> tuple[str, ...]:
    matches = []
    for key, value in dependencies.items():
        text = json.dumps(value, sort_keys=True, default=str).lower()
        if key.lower() in path.lower() or path.lower() in text:
            matches.append(str(key))
    return tuple(matches)


def _calculation_for(path: str) -> tuple[str, ...]:
    lowered = path.lower()
    if any(word in lowered for word in ("price", "valuation", "ratio")):
        return ("valuation_ratio", "entry_condition")
    if any(word in lowered for word in ("quantity", "exposure", "cash", "portfolio")):
        return ("exposure", "concentration", "portfolio_value")
    if any(word in lowered for word in ("risk", "stop", "target", "policy")):
        return ("risk_score", "position_sizing")
    return ("scope_validation",)


def _node_ids(workflow: dict[str, Any]) -> tuple[str, ...]:
    nodes = workflow.get("nodes", workflow.get("officeSequence", workflow.get("offices", ()))) if workflow else ()
    if isinstance(nodes, dict):
        return tuple(str(key) for key in nodes)
    return tuple(str(item.get("officeId", item.get("id", item))) if isinstance(item, dict) else str(item) for item in (nodes or ()))


def _safe_product_types(values: tuple[str, ...]) -> tuple[str, ...]:
    product_types = []
    for value in values or ("office_report",):
        try:
            product_types.append(CacheProductType(str(value)).value)
        except ValueError:
            product_types.append(CacheProductType.ENTERPRISE_PRODUCT.value)
    return tuple(product_types)


def _comparison_method(prior: Any, current: Any, path: str) -> str:
    if _numeric_delta(prior, current)[0] is not None:
        return "numeric_tolerance"
    if isinstance(prior, (tuple, list, set)) or isinstance(current, (tuple, list, set)):
        return "collection_set"
    if path.startswith("workflow."):
        return "workflow_graph"
    if path.startswith("policy."):
        return "policy_delta"
    return "scalar_exact"


def _tolerance_for(path: str, request: DeltaAnalysisRequest) -> Decimal:
    lowered = path.lower()
    if any(word in lowered for word in ("price", "bid", "ask")):
        return Decimal("0.50")
    if any(word in lowered for word in ("quantity", "fill", "cash", "broker")):
        return Decimal("0")
    if request.mission_type == "position_review":
        return Decimal("0.10")
    return Decimal("1.00")


def _units_for(path: str) -> str:
    lowered = path.lower()
    if any(word in lowered for word in ("price", "cash", "value", "cost")):
        return "usd"
    if any(word in lowered for word in ("percent", "return", "exposure")):
        return "percent"
    if "quantity" in lowered:
        return "shares"
    return ""


def _field_explanation(path: str, change: ChangeType, materiality: DeltaMateriality) -> str:
    if change == ChangeType.UNCHANGED:
        return f"{path} is unchanged and remains reusable."
    return f"{path} is {change.value}; classified {materiality.value} for bounded revision analysis."


def _normalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value.normalize())
    if isinstance(value, float):
        return round(value, 8)
    if isinstance(value, (list, tuple, set)):
        return tuple(sorted(_normalize(item) for item in value))
    if isinstance(value, dict):
        return {key: _normalize(value[key]) for key in sorted(value)}
    return value


def _request_type(value: Any) -> DeltaRequestType:
    try:
        return value if isinstance(value, DeltaRequestType) else DeltaRequestType(str(value))
    except ValueError:
        return DeltaRequestType.MANUAL_COMPARISON


def _materiality_enum(value: Any) -> DeltaMateriality:
    try:
        return value if isinstance(value, DeltaMateriality) else DeltaMateriality(str(value))
    except ValueError:
        return DeltaMateriality.NONE


def _change_enum(value: Any) -> ChangeType:
    try:
        return value if isinstance(value, ChangeType) else ChangeType(str(value))
    except ValueError:
        return ChangeType.UNKNOWN


def _revision_enum(value: Any) -> RevisionRequirement:
    try:
        return value if isinstance(value, RevisionRequirement) else RevisionRequirement(str(value))
    except ValueError:
        return RevisionRequirement.NO_ACTION


def _office_decision_enum(value: Any) -> OfficeImpactDecision:
    try:
        return value if isinstance(value, OfficeImpactDecision) else OfficeImpactDecision(str(value))
    except ValueError:
        return OfficeImpactDecision.NOT_REQUIRED


def _public(item: Any) -> dict[str, Any]:
    return {key: _json_value(value) for key, value in asdict(item).items()}


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return tuple(_json_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _baseline_integrity_hash(baseline: DeltaBaseline) -> str:
    return _hash(_public(replace(baseline, content_hash="")))


def _field_from_public(item: dict[str, Any]) -> FieldChange:
    return FieldChange(str(item["field_change_id"]), str(item["field_path"]), _change_enum(item["change_type"]), str(item.get("prior_value_reference", "")), str(item.get("current_value_reference", "")), item.get("prior_normalized_value"), item.get("current_normalized_value"), str(item.get("absolute_delta", "")), str(item.get("percentage_delta", "")), str(item.get("units", "")), str(item.get("comparison_method", "")), str(item.get("tolerance_used", "")), _materiality_enum(item.get("materiality", "none")), float(item.get("materiality_score", 0.0)), tuple(item.get("affected_dependency_ids", ())), tuple(item.get("affected_product_ids", ())), str(item.get("explanation", "")))


def _section_from_public(item: dict[str, Any]) -> SectionChange:
    return SectionChange(str(item["section_change_id"]), str(item["section_name"]), _change_enum(item["change_type"]), tuple(item.get("changed_fields", ())), tuple(item.get("unchanged_fields", ())), _materiality_enum(item.get("materiality", "none")), _revision_enum(item.get("revision_requirement", "no_action")), str(item.get("explanation", "")))


def _evidence_from_public(item: dict[str, Any]) -> EvidenceChange:
    return EvidenceChange(str(item["evidence_change_id"]), str(item["evidence_record_id"]), _change_enum(item["change_type"]), _materiality_enum(item.get("materiality", "none")), bool(item.get("source_authority_change", False)), str(item.get("explanation", "")))


def _product_from_public(item: dict[str, Any]) -> ProductImpact:
    return ProductImpact(str(item["product_impact_id"]), str(item.get("product_record_id", "")), str(item.get("cache_record_id", "")), tuple(item.get("affected_fields", ())), tuple(item.get("affected_sections", ())), tuple(item.get("reusable_fields", ())), tuple(item.get("reusable_sections", ())), _revision_enum(item.get("revision_requirement", "no_action")), str(item.get("reuse_decision_reference", "")), str(item.get("reason", "")))


def _office_from_public(item: dict[str, Any]) -> OfficeImpact:
    return OfficeImpact(str(item["office_impact_id"]), str(item["office_id"]), str(item.get("prior_role", "")), _office_decision_enum(item.get("impact_decision", "not_required")), tuple(item.get("required_scope", ())), str(item.get("excluded_reason", "")), int(item.get("estimated_runtime_seconds", 0)), int(item.get("estimated_api_calls", 0)), str(item.get("reason", "")))


def _dependency_from_public(item: dict[str, Any]) -> DependencyImpact:
    return DependencyImpact(str(item["dependency_impact_id"]), str(item["changed_input"]), tuple(item.get("dependency_path", ())), tuple(item.get("affected_calculations", ())), tuple(item.get("affected_products", ())), tuple(item.get("affected_offices", ())), str(item.get("propagation_boundary", "")), _materiality_enum(item.get("materiality", "none")))


def _node_from_public(item: dict[str, Any]) -> WorkflowNodeDelta:
    return WorkflowNodeDelta(str(item["node_delta_id"]), str(item["node_id"]), str(item.get("office_id", "")), _change_enum(item.get("change_type", "unknown")), bool(item.get("prior_required", False)), bool(item.get("current_required", False)), bool(item.get("token_path_preserved", True)), str(item.get("reason", "")))
