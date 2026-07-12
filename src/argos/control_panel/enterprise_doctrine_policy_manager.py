"""Enterprise Doctrine & Policy Manager for ARGOS EO-CO."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any
from uuid import uuid4

from argos.foundation.contracts import utc_timestamp


class DoctrineType(str, Enum):
    CONSTITUTIONAL = "CONSTITUTIONAL"
    ENTERPRISE = "ENTERPRISE"
    OPERATIONAL_PRINCIPLE = "OPERATIONAL_PRINCIPLE"
    SECURITY = "SECURITY"
    SAFETY = "SAFETY"
    TRADING = "TRADING"
    RECOVERY = "RECOVERY"
    DATA_GOVERNANCE = "DATA_GOVERNANCE"
    AUDIT = "AUDIT"
    COST = "COST"
    OFFICE_LIFECYCLE = "OFFICE_LIFECYCLE"
    WORKFLOW = "WORKFLOW"
    PAPER_LIVE_ISOLATION = "PAPER_LIVE_ISOLATION"


class PolicyDomain(str, Enum):
    SCHEDULING = "SCHEDULING"
    DUTY_OFFICER = "DUTY_OFFICER"
    EVENT_DETECTION = "EVENT_DETECTION"
    MISSION_PLANNING = "MISSION_PLANNING"
    COST_GOVERNANCE = "COST_GOVERNANCE"
    FRESHNESS = "FRESHNESS"
    MEMORY = "MEMORY"
    WORKFLOW_DELTA = "WORKFLOW_DELTA"
    OFFICE_WAKEFULNESS = "OFFICE_WAKEFULNESS"
    PRIORITY = "PRIORITY"
    POSITION_MONITORING = "POSITION_MONITORING"
    COMMUNICATIONS = "COMMUNICATIONS"
    HEALTH_RECOVERY = "HEALTH_RECOVERY"
    EFFICIENCY_ANALYTICS = "EFFICIENCY_ANALYTICS"
    WORKFLOW_EXECUTION = "WORKFLOW_EXECUTION"
    BROKER_EXECUTION = "BROKER_EXECUTION"
    LEDGER = "LEDGER"
    SECURITY = "SECURITY"
    AUDIT = "AUDIT"
    ENTERPRISE_MODE = "ENTERPRISE_MODE"


class PolicyStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    INVALID = "INVALID"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    STAGING = "STAGING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    SUSPENDED = "SUSPENDED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"
    REJECTED = "REJECTED"
    EMERGENCY_ONLY = "EMERGENCY_ONLY"


class PolicyLevel(str, Enum):
    CONSTITUTIONAL_DOCTRINE = "CONSTITUTIONAL_DOCTRINE"
    ENTERPRISE_DOCTRINE = "ENTERPRISE_DOCTRINE"
    ENTERPRISE_OPERATIONAL_POLICY = "ENTERPRISE_OPERATIONAL_POLICY"
    SUBSYSTEM_POLICY = "SUBSYSTEM_POLICY"
    OFFICE_POLICY = "OFFICE_POLICY"
    MISSION_CLASS_POLICY = "MISSION_CLASS_POLICY"
    MODE_SPECIFIC_POLICY = "MODE_SPECIFIC_POLICY"
    TEMPORARY_DIRECTIVE = "TEMPORARY_DIRECTIVE"
    EMERGENCY_RESTRICTION = "EMERGENCY_RESTRICTION"


class PolicyScopeType(str, Enum):
    ENTERPRISE_WIDE = "enterprise_wide"
    SUBSYSTEM = "subsystem"
    OFFICE = "office"
    MISSION_TYPE = "mission_type"
    STRATEGY = "strategy"
    INSTRUMENT_CLASS = "instrument_class"
    ACCOUNT = "account"
    WORKFLOW_TYPE = "workflow_type"
    PAPER_MODE = "paper_mode"
    LIVE_MODE = "live_mode"
    SHARED_INFRASTRUCTURE = "shared_infrastructure"
    TIME_WINDOW = "time_window"
    ENVIRONMENT = "environment"


class ActivationStrategy(str, Enum):
    IMMEDIATE = "IMMEDIATE"
    SCHEDULED = "SCHEDULED"
    STAGED = "STAGED"
    PAPER_FIRST = "PAPER_FIRST"
    CANARY = "CANARY"
    SUBSYSTEM_SEQUENCE = "SUBSYSTEM_SEQUENCE"
    MAINTENANCE_WINDOW = "MAINTENANCE_WINDOW"
    EMERGENCY_RESTRICTION = "EMERGENCY_RESTRICTION"
    MANUAL_CONFIRMATION = "MANUAL_CONFIRMATION"


class CompatibilityDecision(str, Enum):
    COMPATIBLE = "compatible"
    COMPATIBLE_WITH_WARNINGS = "compatible_with_warnings"
    MIGRATION_REQUIRED = "migration_required"
    STAGING_REQUIRED = "staging_required"
    INCOMPATIBLE = "incompatible"
    PROHIBITED_BY_DOCTRINE = "prohibited_by_doctrine"


class AcknowledgementState(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    STAGED = "STAGED"
    APPLIED = "APPLIED"
    ACTIVE = "ACTIVE"
    ROLLBACK_READY = "ROLLBACK_READY"
    ROLLED_BACK = "ROLLED_BACK"
    DRIFTED = "DRIFTED"
    UNAVAILABLE = "UNAVAILABLE"


class DriftClassification(str, Enum):
    BENIGN_LOCAL = "BENIGN_LOCAL"
    STALE = "STALE"
    PARTIAL_APPLICATION = "PARTIAL_APPLICATION"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNAUTHORIZED_OVERRIDE = "UNAUTHORIZED_OVERRIDE"
    SECURITY_CONCERN = "SECURITY_CONCERN"
    UNKNOWN = "UNKNOWN"


class PolicyManagementHealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    INCONSISTENT = "INCONSISTENT"
    PARTIALLY_DISTRIBUTED = "PARTIALLY_DISTRIBUTED"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    SECURITY_HOLD = "SECURITY_HOLD"
    UNAVAILABLE = "UNAVAILABLE"


class PolicyErrorCode(str, Enum):
    DOCTRINE_VIOLATION = "doctrine_violation"
    LAW_VII_CONFLICT = "law_vii_conflict"
    AUTHORITY_BOUNDARY_CONFLICT = "authority_boundary_conflict"
    INVALID_POLICY_SCHEMA = "invalid_policy_schema"
    UNKNOWN_POLICY_DOMAIN = "unknown_policy_domain"
    INVALID_POLICY_VERSION = "invalid_policy_version"
    DUPLICATE_ACTIVE_VERSION = "duplicate_active_version"
    MISSING_APPROVAL = "missing_approval"
    EXPIRED_APPROVAL = "expired_approval"
    INCOMPATIBLE_SUBSYSTEM_VERSION = "incompatible_subsystem_version"
    INCOMPATIBLE_SCHEMA_VERSION = "incompatible_schema_version"
    MISSING_DEPENDENCY = "missing_dependency"
    DEPENDENCY_CYCLE = "dependency_cycle"
    INVALID_SCOPE = "invalid_scope"
    PAPER_LIVE_MODE_CONFLICT = "paper_live_mode_conflict"
    ACTIVATION_PRECONDITION_FAILED = "activation_precondition_failed"
    SUBSCRIBER_REJECTED = "subscriber_rejected"
    ACKNOWLEDGEMENT_TIMEOUT = "acknowledgement_timeout"
    POLICY_HASH_MISMATCH = "policy_hash_mismatch"
    LOCAL_DRIFT_DETECTED = "local_drift_detected"
    UNAUTHORIZED_OVERRIDE = "unauthorized_override"
    ROLLBACK_UNSAFE = "rollback_unsafe"
    CONSTITUTIONAL_AMENDMENT_REQUIRED = "constitutional_amendment_required"
    COMMANDER_AUTHORITY_INSUFFICIENT = "commander_authority_insufficient"
    EO_CL_UNAVAILABLE = "eo_cl_unavailable"
    EO_CM_READINESS_FAILURE = "eo_cm_readiness_failure"
    POLICY_REPOSITORY_UNAVAILABLE = "policy_repository_unavailable"
    ACTIVATION_ALREADY_IN_PROGRESS = "activation_already_in_progress"
    POLICY_ALREADY_RETIRED = "policy_already_retired"
    DIRECTIVE_EXPIRED = "directive_expired"
    IMPORT_SOURCE_UNTRUSTED = "import_source_untrusted"


@dataclass(frozen=True)
class EnterpriseDoctrineRecord:
    doctrine_id: str
    title: str
    doctrine_type: DoctrineType
    version: str
    status: str
    authority_level: str
    statement: str
    machine_constraints: dict[str, Any]
    rationale: str
    owner: str
    approved_by: str
    approved_at: str
    effective_at: str
    supersedes_doctrine_id: str
    related_doctrine_ids: tuple[str, ...]
    amendment_requirements: str
    policy_implications: tuple[str, ...]
    audit_requirements: tuple[str, ...]
    doctrine_hash: str = ""


@dataclass(frozen=True)
class PolicyScope:
    scope_type: PolicyScopeType
    scope_id: str
    mode: str
    environment: str = "development"


@dataclass(frozen=True)
class EnterprisePolicyDefinition:
    policy_id: str
    policy_name: str
    policy_domain: PolicyDomain
    scope: PolicyScope
    owner_authority: str
    description: str
    rationale: str
    schema_id: str
    compatibility_class: str
    required_approvals: tuple[str, ...]
    required_subscribers: tuple[str, ...]
    activation_strategy: ActivationStrategy
    rollback_strategy: str
    paper_live_applicability: tuple[str, ...]
    emergency_applicability: bool
    retention_requirements: str
    audit_classification: str
    created_at: str
    created_by: str


@dataclass(frozen=True)
class EnterprisePolicyVersion:
    policy_version_id: str
    policy_id: str
    semantic_version: str
    status: PolicyStatus
    effective_scope: PolicyScope
    configuration_payload: dict[str, Any]
    human_readable_summary: str
    change_summary: str
    rationale: str
    source_request: str
    parent_version: str
    superseded_version: str
    schema_version: str
    doctrine_dependencies: tuple[str, ...]
    policy_dependencies: tuple[str, ...]
    minimum_compatible_subsystem_versions: dict[str, str]
    maximum_compatible_subsystem_versions: dict[str, str]
    migration_requirements: tuple[str, ...]
    rollback_target: str
    activation_criteria: tuple[str, ...]
    success_criteria: tuple[str, ...]
    rollback_criteria: tuple[str, ...]
    observation_period: str
    expected_effects: tuple[str, ...]
    known_risks: tuple[str, ...]
    policy_hash: str
    created_at: str
    submitted_at: str
    approved_at: str
    activated_at: str
    retired_at: str


@dataclass(frozen=True)
class PolicySchemaDefinition:
    schema_id: str
    policy_domain: PolicyDomain
    schema_version: str
    field_definitions: dict[str, str]
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    units: dict[str, str]
    allowed_ranges: dict[str, tuple[float, float]]
    enums: dict[str, tuple[str, ...]]
    cross_field_constraints: tuple[str, ...]
    default_handling: str
    security_classification: str
    compatibility_rules: tuple[str, ...]
    migration_adapters: tuple[str, ...]
    owning_subsystem: str
    validation_tests: tuple[str, ...]
    deprecation_state: str = "ACTIVE"


@dataclass(frozen=True)
class PolicyApprovalRecord:
    approval_id: str
    policy_version_id: str
    approval_type: str
    approver_identity: str
    approver_authority: str
    decision: str
    reason: str
    conditions: tuple[str, ...]
    timestamp: str
    expiration: str
    signature_or_integrity_reference: str
    audit_hash: str


@dataclass(frozen=True)
class PolicyCompatibilityResult:
    compatibility_id: str
    policy_version_id: str
    decision: CompatibilityDecision
    compatible: bool
    warnings: tuple[str, ...]
    failures: tuple[str, ...]
    migration_required: bool
    staging_required: bool
    subscriber_results: tuple[dict[str, Any], ...]
    checked_at: str
    result_hash: str


@dataclass(frozen=True)
class PolicyActivationPlan:
    activation_plan_id: str
    policy_version_id: str
    activation_strategy: ActivationStrategy
    target_subscribers: tuple[str, ...]
    activation_sequence: tuple[str, ...]
    scheduled_time: str
    preconditions: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    acknowledgement_requirements: tuple[AcknowledgementState, ...]
    observation_window: str
    success_criteria: tuple[str, ...]
    rollback_criteria: tuple[str, ...]
    rollback_target: str
    paper_live_stages: tuple[str, ...]
    commander_approval_requirement: str
    eo_cm_health_requirement: str
    eo_cl_availability_requirement: str
    plan_hash: str


@dataclass(frozen=True)
class PolicyDistributionRecord:
    distribution_id: str
    policy_version_id: str
    subscriber_id: str
    sent_at: str
    received_at: str
    validated_at: str
    acknowledged_at: str
    acknowledgement_status: AcknowledgementState
    applied_at: str
    local_hash: str
    compatibility_result: str
    failure_reason: str
    retry_count: int
    correlation_id: str


@dataclass(frozen=True)
class PolicyDriftRecord:
    drift_id: str
    policy_version_id: str
    subscriber_id: str
    detected_at: str
    expected_hash: str
    actual_hash: str
    expected_values: dict[str, Any]
    actual_values: dict[str, Any]
    drift_classification: DriftClassification
    severity: str
    likely_cause: str
    reconciliation_status: str
    incident_id: str


@dataclass(frozen=True)
class CommanderPolicyDirective:
    directive_id: str
    directive_type: str
    issuer: str
    authority: str
    issued_at: str
    effective_at: str
    expires_at: str
    scope: PolicyScope
    requested_change: dict[str, Any]
    rationale: str
    urgency: str
    affected_policies: tuple[str, ...]
    compatibility_result: str
    approval_requirements: tuple[str, ...]
    status: str
    correlation_id: str
    directive_hash: str


@dataclass(frozen=True)
class ResolvedPolicyConfiguration:
    requesting_subsystem: str
    scope: PolicyScope
    mode: str
    applicable_doctrine: tuple[str, ...]
    applicable_policy_versions: tuple[str, ...]
    applicable_directives: tuple[str, ...]
    final_resolved_values: dict[str, Any]
    source_for_each_value: dict[str, str]
    conflict_resolution: str
    resolution_time: str
    resolution_hash: str


class PolicySchemaRegistry:
    def __init__(self) -> None:
        self._schemas: dict[str, PolicySchemaDefinition] = {}

    def register(self, schema: PolicySchemaDefinition) -> None:
        self._schemas[schema.schema_id] = schema

    def get(self, schema_id: str) -> PolicySchemaDefinition | None:
        return self._schemas.get(schema_id)

    def validate(self, version: EnterprisePolicyVersion) -> tuple[bool, tuple[str, ...]]:
        schema = self.get(version.schema_version)
        if not schema:
            return False, (PolicyErrorCode.INVALID_POLICY_SCHEMA.value,)
        errors: list[str] = []
        payload = version.configuration_payload
        unknown = set(payload) - set(schema.required_fields) - set(schema.optional_fields)
        if unknown and schema.security_classification in {"authority_sensitive", "constitutional"}:
            errors.append(f"unknown_fields:{','.join(sorted(unknown))}")
        for field in schema.required_fields:
            if field not in payload:
                errors.append(f"missing_required_field:{field}")
        for field, allowed in schema.enums.items():
            if field in payload and str(payload[field]) not in allowed:
                errors.append(f"invalid_enum:{field}")
        for field, (minimum, maximum) in schema.allowed_ranges.items():
            if field in payload:
                try:
                    value = float(payload[field])
                except (TypeError, ValueError):
                    errors.append(f"invalid_number:{field}")
                    continue
                if value < minimum or value > maximum:
                    errors.append(f"range_violation:{field}")
        return not errors, tuple(errors)

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in sorted(self._schemas.values(), key=lambda item: item.schema_id))


class PolicyDependencyResolver:
    def __init__(self, versions: dict[str, EnterprisePolicyVersion]) -> None:
        self._versions = versions

    def resolve(self, version: EnterprisePolicyVersion) -> dict[str, Any]:
        missing = tuple(item for item in version.policy_dependencies if item and item not in self._versions)
        cycle = self._detect_cycle(version.policy_version_id, set(), set())
        order = self._activation_order(version.policy_version_id, set())
        return {"missingDependencies": missing, "cycleDetected": cycle, "activationOrder": order, "valid": not missing and not cycle}

    def _detect_cycle(self, version_id: str, visiting: set[str], visited: set[str]) -> bool:
        if version_id in visiting:
            return True
        if version_id in visited:
            return False
        version = self._versions.get(version_id)
        if not version:
            return False
        visiting.add(version_id)
        for dep in version.policy_dependencies:
            if self._detect_cycle(dep, visiting, visited):
                return True
        visiting.remove(version_id)
        visited.add(version_id)
        return False

    def _activation_order(self, version_id: str, visited: set[str]) -> tuple[str, ...]:
        if version_id in visited:
            return ()
        visited.add(version_id)
        version = self._versions.get(version_id)
        if not version:
            return ()
        order: list[str] = []
        for dep in version.policy_dependencies:
            order.extend(self._activation_order(dep, visited))
        order.append(version_id)
        return tuple(dict.fromkeys(order))


class EnterpriseDoctrinePolicyManager:
    """Central deterministic policy authority; never operational executor."""

    def __init__(self) -> None:
        self.schema_registry = PolicySchemaRegistry()
        self._doctrine: dict[str, EnterpriseDoctrineRecord] = {}
        self._definitions: dict[str, EnterprisePolicyDefinition] = {}
        self._versions: dict[str, EnterprisePolicyVersion] = {}
        self._active_by_domain: dict[PolicyDomain, str] = {}
        self._approvals: list[PolicyApprovalRecord] = []
        self._compatibility_results: list[PolicyCompatibilityResult] = []
        self._activation_plans: list[PolicyActivationPlan] = []
        self._distribution: list[PolicyDistributionRecord] = []
        self._drift: list[PolicyDriftRecord] = []
        self._directives: list[CommanderPolicyDirective] = []
        self._emergency_restrictions: list[CommanderPolicyDirective] = []
        self._audit: list[dict[str, Any]] = []
        self._subscribers = _default_subscribers()
        self._idempotency: dict[str, str] = {}
        self._bootstrap()

    def snapshot(self, sources: dict[str, Any] | None = None) -> dict[str, Any]:
        sources = dict(sources or {})
        health = self.get_health()
        active_versions = tuple(self._versions[vid] for vid in self._active_by_domain.values() if vid in self._versions)
        return {
            "managerName": "Enterprise Doctrine & Policy Manager",
            "engineeringOrder": "EO-CO",
            "status": health["overallState"],
            "health": health,
            "activeDoctrineVersion": "ARGOS-CONSTITUTION-1.0",
            "doctrineLibrary": tuple(_public(item) for item in sorted(self._doctrine.values(), key=lambda item: item.doctrine_id)),
            "policySchemaRegistry": self.schema_registry.snapshot(),
            "policyDefinitions": tuple(_public(item) for item in sorted(self._definitions.values(), key=lambda item: item.policy_id)),
            "policyVersions": tuple(_public(item) for item in sorted(self._versions.values(), key=lambda item: item.policy_version_id)),
            "activePolicyMatrix": tuple(_active_policy_row(self._definitions[item.policy_id], item, self._distribution, self._drift) for item in active_versions),
            "pendingApprovals": tuple(_approval_queue_row(self._definitions[item.policy_id], item) for item in self._versions.values() if item.status == PolicyStatus.AWAITING_APPROVAL),
            "scheduledActivations": tuple(_public(item) for item in self._activation_plans if item.scheduled_time),
            "stagingPolicies": tuple(_public(item) for item in self._versions.values() if item.status == PolicyStatus.STAGING),
            "degradedPolicies": tuple(_public(item) for item in self._versions.values() if item.status == PolicyStatus.DEGRADED),
            "rollbackRequiredPolicies": tuple(_public(item) for item in self._versions.values() if item.status == PolicyStatus.ROLLING_BACK),
            "subscriberRegistry": tuple(dict(item) for item in self._subscribers),
            "subscriberIncompatibilities": tuple(item for result in self._compatibility_results for item in result.subscriber_results if item.get("decision") not in {"compatible", "compatible_with_warnings"}),
            "distributionRecords": tuple(_public(item) for item in self._distribution[-40:]),
            "driftDetections": tuple(_public(item) for item in self._drift[-40:]),
            "temporaryDirectives": tuple(_public(item) for item in self._directives[-20:]),
            "emergencyRestrictions": tuple(_public(item) for item in self._emergency_restrictions[-20:]),
            "activationPlans": tuple(_public(item) for item in self._activation_plans[-20:]),
            "approvalRecords": tuple(_public(item) for item in self._approvals[-40:]),
            "compatibilityResults": tuple(_public(item) for item in self._compatibility_results[-30:]),
            "dependencyGraph": self.dependency_graph(),
            "seriesCIntegrationMatrix": self.series_c_policy_integration_matrix(sources),
            "configurationPrecedence": tuple(level.value for level in PolicyLevel),
            "configurationGovernance": self.configuration_governance(),
            "policyMetrics": self.get_metrics(),
            "policyReports": self.reports(),
            "commanderControls": {
                "createPolicyDraft": True,
                "submitPolicyForValidation": True,
                "requestImpactAnalysis": True,
                "approvePolicy": True,
                "scheduleActivation": True,
                "beginStaging": True,
                "suspendPolicy": True,
                "requestRollback": True,
                "issueTemporaryRestrictiveDirective": True,
                "activateEmergencyRestriction": True,
                "acknowledgeDrift": True,
                "exportPolicyReport": True,
                "startsMissions": False,
                "wakesOffices": False,
                "transfersWorkflowExecutionToken": False,
                "approvesIndividualExpenditure": False,
                "executesTrades": False,
                "rewritesLedgers": False,
            },
            "lawCO": self.law_boundaries(),
            "auditTrail": tuple(self._audit[-80:]),
            "dashboardFeed": {
                "overallState": health["overallState"],
                "activePolicies": len(active_versions),
                "pendingApprovals": sum(1 for item in self._versions.values() if item.status == PolicyStatus.AWAITING_APPROVAL),
                "driftCount": len(self._drift),
                "emergencyRestrictions": len(self._emergency_restrictions),
                "policyAuthority": "EO-CO",
                "lawVIIIntact": True,
            },
            "healthSignalsForEOCM": self.health_signals(),
            "efficiencyMetricsForEOCN": self.efficiency_feed(),
        }

    def submit_policy(self, draft: dict[str, Any], *, idempotency_key: str = "", actor: str = "Commander") -> dict[str, Any]:
        if idempotency_key and idempotency_key in self._idempotency:
            return {"accepted": True, "idempotentReplay": True, "policyVersionId": self._idempotency[idempotency_key], "state": self.snapshot()}
        domain = _domain(draft.get("policyDomain", draft.get("policy_domain", PolicyDomain.PRIORITY.value)))
        schema_id = str(draft.get("schemaId", draft.get("schema_id", f"CO-SCHEMA-{domain.value}")))
        definition = self._definitions.get(str(draft.get("policyId", draft.get("policy_id", f"CO-POL-{domain.value}"))))
        if not definition:
            definition = self._definition_for(domain, schema_id)
            self._definitions[definition.policy_id] = definition
        now = utc_timestamp()
        version_id = str(draft.get("policyVersionId", draft.get("policy_version_id", f"{definition.policy_id}-DRAFT-{uuid4().hex[:8].upper()}")))
        version = EnterprisePolicyVersion(
            policy_version_id=version_id,
            policy_id=definition.policy_id,
            semantic_version=str(draft.get("semanticVersion", draft.get("semantic_version", "1.0.1"))),
            status=PolicyStatus.DRAFT,
            effective_scope=definition.scope,
            configuration_payload=dict(draft.get("configuration", draft.get("configuration_payload", {})) or {}),
            human_readable_summary=str(draft.get("summary", "Commander-submitted operational policy draft.")),
            change_summary=str(draft.get("changeSummary", draft.get("change_summary", "Policy draft submitted."))),
            rationale=str(draft.get("rationale", "Commander requested policy review.")),
            source_request=str(draft.get("sourceRequest", draft.get("source_request", actor))),
            parent_version=str(draft.get("parentVersion", draft.get("parent_version", self._active_by_domain.get(domain, "")))),
            superseded_version=str(draft.get("supersededVersion", "")),
            schema_version=schema_id,
            doctrine_dependencies=tuple(draft.get("doctrineDependencies", ("LAW-VII", "DOCTRINE-DETERMINISTIC-FIRST")) or ()),
            policy_dependencies=tuple(draft.get("policyDependencies", ()) or ()),
            minimum_compatible_subsystem_versions=dict(draft.get("minimumCompatibleSubsystemVersions", {}) or {}),
            maximum_compatible_subsystem_versions=dict(draft.get("maximumCompatibleSubsystemVersions", {}) or {}),
            migration_requirements=tuple(draft.get("migrationRequirements", ()) or ()),
            rollback_target=str(draft.get("rollbackTarget", self._active_by_domain.get(domain, ""))),
            activation_criteria=tuple(draft.get("activationCriteria", ("validation_passed", "required_approvals_present")) or ()),
            success_criteria=tuple(draft.get("successCriteria", ("subscriber_acknowledgement_complete",)) or ()),
            rollback_criteria=tuple(draft.get("rollbackCriteria", ("subscriber_rejection", "law_vii_violation", "drift_detected")) or ()),
            observation_period=str(draft.get("observationPeriod", "current_session")),
            expected_effects=tuple(draft.get("expectedEffects", ()) or ()),
            known_risks=tuple(draft.get("knownRisks", ()) or ()),
            policy_hash="",
            created_at=now,
            submitted_at=now,
            approved_at="",
            activated_at="",
            retired_at="",
        )
        version = _hash_policy_version(version)
        validation = self.validate_policy(version)
        status = PolicyStatus.AWAITING_APPROVAL if validation["valid"] else PolicyStatus.INVALID
        version = replace(version, status=status)
        self._versions[version.policy_version_id] = version
        if idempotency_key:
            self._idempotency[idempotency_key] = version.policy_version_id
        self._audit_event("policy_submitted", version.policy_id, version.policy_version_id, actor, status.value, validation)
        return {"accepted": validation["valid"], "policyVersion": _public(version), "validation": validation, "state": self.snapshot()}

    def validate_policy(self, policy_version: EnterprisePolicyVersion | dict[str, Any]) -> dict[str, Any]:
        version = policy_version if isinstance(policy_version, EnterprisePolicyVersion) else _version_from_dict(policy_version)
        structural_ok, structural_errors = self.schema_registry.validate(version)
        doctrine_errors = self._doctrine_errors(version)
        operational_errors = self._operational_errors(version)
        dependency = PolicyDependencyResolver(self._versions | {version.policy_version_id: version}).resolve(version)
        errors = tuple(structural_errors) + doctrine_errors + operational_errors + tuple(dependency["missingDependencies"])
        if dependency["cycleDetected"]:
            errors += (PolicyErrorCode.DEPENDENCY_CYCLE.value,)
        valid = structural_ok and not doctrine_errors and not operational_errors and dependency["valid"]
        return {
            "valid": valid,
            "structuralValid": structural_ok,
            "doctrineValid": not doctrine_errors,
            "dependencyValid": dependency["valid"],
            "operationalValid": not operational_errors,
            "errors": errors,
            "warnings": tuple(),
            "lawVIIIntact": PolicyErrorCode.LAW_VII_CONFLICT.value not in errors,
            "activationBlocked": not valid,
        }

    def check_compatibility(self, policy_version_id: str, subscriber_versions: dict[str, str] | None = None) -> PolicyCompatibilityResult:
        version = self._versions[policy_version_id]
        definition = self._definitions[version.policy_id]
        subscriber_versions = dict(subscriber_versions or {})
        rows: list[dict[str, Any]] = []
        failures: list[str] = []
        for subscriber in self._subscribers:
            sid = subscriber["subscriberId"]
            if sid not in definition.required_subscribers:
                continue
            supports_domain = definition.policy_domain.value in subscriber["supportedPolicyDomains"]
            supports_schema = version.schema_version in subscriber["supportedPolicySchemaVersions"]
            min_version = version.minimum_compatible_subsystem_versions.get(sid)
            reported_version = subscriber_versions.get(sid, subscriber["currentSubsystemVersion"])
            version_ok = not min_version or reported_version >= min_version
            decision = CompatibilityDecision.COMPATIBLE if supports_domain and supports_schema and version_ok else CompatibilityDecision.INCOMPATIBLE
            if decision == CompatibilityDecision.INCOMPATIBLE:
                failures.append(f"{sid}:incompatible")
            rows.append({"subscriberId": sid, "domainSupported": supports_domain, "schemaSupported": supports_schema, "reportedVersion": reported_version, "decision": decision.value})
        decision = CompatibilityDecision.COMPATIBLE if not failures else CompatibilityDecision.INCOMPATIBLE
        result = PolicyCompatibilityResult(
            f"CO-COMP-{len(self._compatibility_results) + 1:06d}",
            policy_version_id,
            decision,
            decision == CompatibilityDecision.COMPATIBLE,
            tuple(),
            tuple(failures),
            False,
            definition.activation_strategy in {ActivationStrategy.PAPER_FIRST, ActivationStrategy.STAGED, ActivationStrategy.CANARY},
            tuple(rows),
            utc_timestamp(),
            "",
        )
        result = replace(result, result_hash=_hash(_public(result)))
        self._compatibility_results.append(result)
        self._audit_event("compatibility_checked", version.policy_id, policy_version_id, "EO-CO", decision.value, {"failures": failures})
        return result

    def approve_policy(self, policy_version_id: str, approval: dict[str, Any], *, idempotency_key: str = "") -> dict[str, Any]:
        if idempotency_key and idempotency_key in self._idempotency:
            return {"approved": True, "idempotentReplay": True, "approvalId": self._idempotency[idempotency_key], "state": self.snapshot()}
        version = self._versions[policy_version_id]
        validation = self.validate_policy(version)
        if not validation["valid"]:
            self._audit_event("approval_rejected", version.policy_id, policy_version_id, str(approval.get("approver", "Commander")), "validation_failed", validation)
            return {"approved": False, "reasonCode": PolicyErrorCode.DOCTRINE_VIOLATION.value, "validation": validation, "state": self.snapshot()}
        if any(dep == "LAW-VII" for dep in version.doctrine_dependencies) and approval.get("directiveType") == "constitutional_amendment":
            return {"approved": False, "reasonCode": PolicyErrorCode.CONSTITUTIONAL_AMENDMENT_REQUIRED.value, "state": self.snapshot()}
        record = PolicyApprovalRecord(
            f"CO-APP-{len(self._approvals) + 1:06d}",
            policy_version_id,
            str(approval.get("approvalType", "commander_policy_approval")),
            str(approval.get("approver", "Commander")),
            str(approval.get("authority", "Commander")),
            str(approval.get("decision", "APPROVED")),
            str(approval.get("reason", "Policy approved after deterministic validation.")),
            tuple(approval.get("conditions", ()) or ()),
            utc_timestamp(),
            str(approval.get("expiration", "")),
            str(approval.get("signature", "")),
            "",
        )
        record = replace(record, audit_hash=_hash(_public(record)))
        self._approvals.append(record)
        self._versions[policy_version_id] = replace(version, status=PolicyStatus.APPROVED, approved_at=record.timestamp)
        if idempotency_key:
            self._idempotency[idempotency_key] = record.approval_id
        self._audit_event("approval_granted", version.policy_id, policy_version_id, record.approver_identity, "APPROVED", _public(record))
        return {"approved": True, "approvalRecord": _public(record), "state": self.snapshot()}

    def schedule_activation(self, policy_version_id: str, plan: dict[str, Any] | None = None, *, idempotency_key: str = "") -> dict[str, Any]:
        if idempotency_key and idempotency_key in self._idempotency:
            return {"scheduled": True, "idempotentReplay": True, "activationPlanId": self._idempotency[idempotency_key], "state": self.snapshot()}
        plan = dict(plan or {})
        version = self._versions[policy_version_id]
        definition = self._definitions[version.policy_id]
        compatibility = self.check_compatibility(policy_version_id)
        if not compatibility.compatible:
            return {"scheduled": False, "reasonCode": PolicyErrorCode.INCOMPATIBLE_SUBSYSTEM_VERSION.value, "compatibility": _public(compatibility), "state": self.snapshot()}
        approval_refs = [item.approval_id for item in self._approvals if item.policy_version_id == policy_version_id and item.decision == "APPROVED"]
        if definition.required_approvals and not approval_refs:
            return {"scheduled": False, "reasonCode": PolicyErrorCode.MISSING_APPROVAL.value, "state": self.snapshot()}
        target_subscribers = tuple(plan.get("targetSubscribers", definition.required_subscribers) or ())
        strategy = _activation_strategy(plan.get("activationStrategy", definition.activation_strategy.value))
        activation_plan = PolicyActivationPlan(
            f"CO-ACT-{len(self._activation_plans) + 1:06d}",
            policy_version_id,
            strategy,
            target_subscribers,
            tuple(plan.get("activationSequence", target_subscribers) or ()),
            str(plan.get("scheduledTime", "")),
            tuple(plan.get("preconditions", ("policy_valid", "approvals_current", "eo_cl_available", "eo_cm_ready")) or ()),
            tuple(plan.get("validationRequirements", ("schema", "doctrine", "compatibility", "dependencies")) or ()),
            tuple(AcknowledgementState(item) if isinstance(item, str) else item for item in plan.get("acknowledgementRequirements", (AcknowledgementState.ACTIVE.value,)) or ()),
            str(plan.get("observationWindow", version.observation_period)),
            tuple(plan.get("successCriteria", version.success_criteria) or ()),
            tuple(plan.get("rollbackCriteria", version.rollback_criteria) or ()),
            str(plan.get("rollbackTarget", version.rollback_target)),
            tuple(plan.get("paperLiveStages", _paper_live_stages(strategy, definition.paper_live_applicability)) or ()),
            str(plan.get("commanderApprovalRequirement", "required_for_material_or_live_policy")),
            str(plan.get("eoCmHealthRequirement", "healthy_or_degraded_allowed_for_restrictive_changes_only")),
            str(plan.get("eoClAvailabilityRequirement", "required_for_authoritative_distribution")),
            "",
        )
        activation_plan = replace(activation_plan, plan_hash=_hash(_public(activation_plan)))
        self._activation_plans.append(activation_plan)
        self._versions[policy_version_id] = replace(version, status=PolicyStatus.SCHEDULED if activation_plan.scheduled_time else PolicyStatus.STAGING)
        if idempotency_key:
            self._idempotency[idempotency_key] = activation_plan.activation_plan_id
        self._audit_event("activation_scheduled", version.policy_id, policy_version_id, "EO-CO", activation_plan.activation_strategy.value, _public(activation_plan))
        return {"scheduled": True, "activationPlan": _public(activation_plan), "state": self.snapshot()}

    def activate_policy(self, activation_plan_id: str, *, communications_bus: Any | None = None, idempotency_key: str = "") -> dict[str, Any]:
        if idempotency_key and idempotency_key in self._idempotency:
            return {"activated": True, "idempotentReplay": True, "policyVersionId": self._idempotency[idempotency_key], "state": self.snapshot()}
        plan = next((item for item in self._activation_plans if item.activation_plan_id == activation_plan_id), None)
        if not plan:
            return {"activated": False, "reasonCode": PolicyErrorCode.INVALID_POLICY_VERSION.value, "state": self.snapshot()}
        version = self._versions[plan.policy_version_id]
        definition = self._definitions[version.policy_id]
        validation = self.validate_policy(version)
        if not validation["valid"]:
            self._versions[version.policy_version_id] = replace(version, status=PolicyStatus.INVALID)
            return {"activated": False, "reasonCode": PolicyErrorCode.DOCTRINE_VIOLATION.value, "validation": validation, "state": self.snapshot()}
        now = utc_timestamp()
        correlation_id = f"CO-DIST-{uuid4().hex[:8].upper()}"
        publication_result: dict[str, Any] = {"accepted": False, "reasonCode": "no_bus_supplied"}
        if communications_bus is not None:
            publication_result = self._publish_policy(communications_bus, version, plan, correlation_id)
        for subscriber_id in plan.target_subscribers:
            self._distribution.append(
                PolicyDistributionRecord(
                    f"CO-DIST-{len(self._distribution) + 1:06d}",
                    version.policy_version_id,
                    subscriber_id,
                    now,
                    now,
                    now,
                    now,
                    AcknowledgementState.ACTIVE,
                    now,
                    version.policy_hash,
                    "compatible",
                    "",
                    0,
                    correlation_id,
                )
            )
        prior = self._active_by_domain.get(definition.policy_domain)
        if prior and prior in self._versions:
            self._versions[prior] = replace(self._versions[prior], status=PolicyStatus.SUPERSEDED, superseded_version=version.policy_version_id)
        self._versions[version.policy_version_id] = replace(version, status=PolicyStatus.ACTIVE, activated_at=now)
        self._active_by_domain[definition.policy_domain] = version.policy_version_id
        if idempotency_key:
            self._idempotency[idempotency_key] = version.policy_version_id
        self._audit_event("policy_activated", version.policy_id, version.policy_version_id, "EO-CO", "ACTIVE", {"activationPlanId": activation_plan_id, "publicationResult": publication_result})
        return {"activated": True, "policyVersionId": version.policy_version_id, "publicationResult": publication_result, "state": self.snapshot()}

    def suspend_policy(self, policy_version_id: str, reason: str, *, actor: str = "Commander") -> dict[str, Any]:
        version = self._versions[policy_version_id]
        self._versions[policy_version_id] = replace(version, status=PolicyStatus.SUSPENDED)
        self._audit_event("policy_suspended", version.policy_id, policy_version_id, actor, "SUSPENDED", {"reason": reason, "fallbackPolicy": version.rollback_target})
        return {"suspended": True, "fallbackPolicy": version.rollback_target, "state": self.snapshot()}

    def rollback_policy(self, policy_version_id: str, authorization: dict[str, Any] | None = None) -> dict[str, Any]:
        version = self._versions[policy_version_id]
        if not version.rollback_target or version.rollback_target not in self._versions:
            return {"rolledBack": False, "reasonCode": PolicyErrorCode.ROLLBACK_UNSAFE.value, "state": self.snapshot()}
        target = self._versions[version.rollback_target]
        if any(req == "manual_migration_required" for req in version.migration_requirements):
            return {"rolledBack": False, "reasonCode": PolicyErrorCode.ROLLBACK_UNSAFE.value, "requiresCommanderReview": True, "state": self.snapshot()}
        definition = self._definitions[version.policy_id]
        now = utc_timestamp()
        self._versions[policy_version_id] = replace(version, status=PolicyStatus.ROLLED_BACK, retired_at=now)
        self._versions[target.policy_version_id] = replace(target, status=PolicyStatus.ACTIVE, activated_at=target.activated_at or now)
        self._active_by_domain[definition.policy_domain] = target.policy_version_id
        self._audit_event("rollback_completed", version.policy_id, policy_version_id, str((authorization or {}).get("actor", "Commander")), "ROLLED_BACK", {"rollbackTarget": target.policy_version_id})
        return {"rolledBack": True, "rollbackTarget": target.policy_version_id, "state": self.snapshot()}

    def retire_policy(self, policy_version_id: str) -> dict[str, Any]:
        dependents = tuple(item.policy_version_id for item in self._versions.values() if policy_version_id in item.policy_dependencies and item.status == PolicyStatus.ACTIVE)
        if dependents:
            return {"retired": False, "reasonCode": PolicyErrorCode.MISSING_DEPENDENCY.value, "activeDependents": dependents, "state": self.snapshot()}
        version = self._versions[policy_version_id]
        self._versions[policy_version_id] = replace(version, status=PolicyStatus.RETIRED, retired_at=utc_timestamp())
        self._audit_event("policy_retired", version.policy_id, policy_version_id, "EO-CO", "RETIRED", {})
        return {"retired": True, "state": self.snapshot()}

    def issue_temporary_directive(self, payload: dict[str, Any], *, emergency: bool = False) -> dict[str, Any]:
        domain = _domain(payload.get("policyDomain", PolicyDomain.ENTERPRISE_MODE.value))
        scope = PolicyScope(_scope_type(payload.get("scopeType", PolicyScopeType.ENTERPRISE_WIDE.value)), str(payload.get("scopeId", "enterprise")), str(payload.get("mode", "PAPER")))
        directive = CommanderPolicyDirective(
            f"CO-DIR-{len(self._directives) + len(self._emergency_restrictions) + 1:06d}",
            "emergency_restriction" if emergency else "temporary_restrictive_directive",
            str(payload.get("issuer", "Commander")),
            str(payload.get("authority", "Commander")),
            utc_timestamp(),
            str(payload.get("effectiveAt", utc_timestamp())),
            str(payload.get("expiresAt", payload.get("expires_at", ""))),
            scope,
            dict(payload.get("requestedChange", payload.get("requested_change", {})) or {}),
            str(payload.get("rationale", "Commander directive.")),
            str(payload.get("urgency", "normal")),
            tuple(payload.get("affectedPolicies", tuple(self._active_by_domain.get(domain, ""))) or ()),
            "compatible_restrictive_directive",
            ("Commander",),
            "ACTIVE",
            str(payload.get("correlationId", f"CO-DIR-CORR-{uuid4().hex[:8].upper()}")),
            "",
        )
        directive = replace(directive, directive_hash=_hash(_public(directive)))
        if emergency:
            self._emergency_restrictions.append(directive)
            action = "emergency_restriction_activated"
        else:
            self._directives.append(directive)
            action = "temporary_directive_issued"
        self._audit_event(action, "", "", directive.issuer, directive.status, _public(directive))
        return {"accepted": True, "directive": _public(directive), "state": self.snapshot()}

    def detect_drift(self, subscriber_id: str, policy_version_id: str, actual_values: dict[str, Any], actual_hash: str = "") -> dict[str, Any]:
        version = self._versions[policy_version_id]
        actual_hash = actual_hash or _hash(actual_values)
        classification = DriftClassification.BENIGN_LOCAL if actual_hash == version.policy_hash else DriftClassification.UNAUTHORIZED_OVERRIDE
        record = PolicyDriftRecord(
            f"CO-DRIFT-{len(self._drift) + 1:06d}",
            policy_version_id,
            subscriber_id,
            utc_timestamp(),
            version.policy_hash,
            actual_hash,
            version.configuration_payload,
            dict(actual_values),
            classification,
            "INFO" if classification == DriftClassification.BENIGN_LOCAL else "CRITICAL",
            "hash_match" if classification == DriftClassification.BENIGN_LOCAL else "manual_local_override_or_stale_process",
            "none_required" if classification == DriftClassification.BENIGN_LOCAL else "commander_review_required",
            "" if classification == DriftClassification.BENIGN_LOCAL else f"CO-INC-{len(self._drift) + 1:06d}",
        )
        self._drift.append(record)
        self._audit_event("policy_drift_detected", version.policy_id, policy_version_id, "EO-CO", record.drift_classification.value, _public(record))
        return {"driftDetected": classification != DriftClassification.BENIGN_LOCAL, "driftRecord": _public(record), "state": self.snapshot()}

    def get_active_policy(self, domain: PolicyDomain | str, scope: dict[str, Any] | None = None, mode: str = "PAPER") -> ResolvedPolicyConfiguration:
        domain_value = _domain(domain)
        version_id = self._active_by_domain.get(domain_value)
        version = self._versions[version_id] if version_id else None
        scope_obj = PolicyScope(_scope_type((scope or {}).get("scopeType", PolicyScopeType.ENTERPRISE_WIDE.value)), str((scope or {}).get("scopeId", "enterprise")), mode)
        values = dict(version.configuration_payload if version else {})
        sources = {key: version.policy_version_id for key in values} if version else {}
        active_directives = tuple(item for item in self._directives + self._emergency_restrictions if _not_expired(item))
        for directive in active_directives:
            for key, value in directive.requested_change.items():
                prior = values.get(key)
                if prior is None or _more_restrictive(prior, value):
                    values[key] = value
                    sources[key] = directive.directive_id
        resolved = ResolvedPolicyConfiguration(
            requesting_subsystem=_domain_to_subsystem(domain_value),
            scope=scope_obj,
            mode=mode,
            applicable_doctrine=tuple(self._doctrine),
            applicable_policy_versions=(version.policy_version_id,) if version else (),
            applicable_directives=tuple(item.directive_id for item in active_directives),
            final_resolved_values=values,
            source_for_each_value=sources,
            conflict_resolution="deterministic_precedence_fail_closed",
            resolution_time=utc_timestamp(),
            resolution_hash="",
        )
        return replace(resolved, resolution_hash=_hash(_public(resolved)))

    def get_policy_version(self, policy_version_id: str) -> dict[str, Any]:
        return _public(self._versions[policy_version_id])

    def get_active_doctrine(self) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._doctrine.values())

    def get_policy_history(self, policy_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._versions.values() if item.policy_id == policy_id)

    def get_drift_records(self, filters: dict[str, Any] | None = None) -> tuple[dict[str, Any], ...]:
        filters = dict(filters or {})
        records = self._drift
        if filters.get("subscriberId"):
            records = [item for item in records if item.subscriber_id == filters["subscriberId"]]
        return tuple(_public(item) for item in records)

    def get_health(self) -> dict[str, Any]:
        critical_drift = sum(1 for item in self._drift if item.severity == "CRITICAL")
        incomplete = sum(1 for item in self._distribution if item.acknowledgement_status not in {AcknowledgementState.ACTIVE, AcknowledgementState.APPLIED})
        state = PolicyManagementHealthState.HEALTHY
        if critical_drift:
            state = PolicyManagementHealthState.SECURITY_HOLD
        elif incomplete:
            state = PolicyManagementHealthState.PARTIALLY_DISTRIBUTED
        return {
            "overallState": state.value,
            "repositoryHealth": "HEALTHY",
            "doctrineIntegrity": "VALID",
            "activePolicyConsistency": "CONSISTENT" if not self._duplicate_active_domains() else "INCONSISTENT",
            "subscriberAcknowledgement": "COMPLETE" if not incomplete else "INCOMPLETE",
            "drift": "NONE" if not critical_drift else "CRITICAL",
            "compatibility": "VALID" if not any(not item.compatible for item in self._compatibility_results[-10:]) else "BLOCKED",
            "distributionBacklog": incomplete,
            "rollbackReadiness": "READY",
            "auditHealth": "COMPLETE" if self._audit else "AWAITING_ACTIVITY",
        }

    def get_metrics(self) -> dict[str, Any]:
        active = sum(1 for item in self._versions.values() if item.status == PolicyStatus.ACTIVE)
        drafts = sum(1 for item in self._versions.values() if item.status == PolicyStatus.DRAFT)
        approvals = sum(1 for item in self._versions.values() if item.status == PolicyStatus.AWAITING_APPROVAL)
        activations = [item for item in self._audit if item["action"] == "policy_activated"]
        failures = [item for item in self._audit if item["action"] == "activation_failed"]
        total_activation = len(activations) + len(failures)
        return {
            "totalPolicyDefinitions": len(self._definitions),
            "activePolicies": active,
            "draftPolicies": drafts,
            "pendingApprovals": approvals,
            "scheduledActivations": sum(1 for item in self._versions.values() if item.status == PolicyStatus.SCHEDULED),
            "activationSuccessRate": round((len(activations) / total_activation) * 100, 4) if total_activation else 100.0,
            "activationFailureRate": round((len(failures) / total_activation) * 100, 4) if total_activation else 0.0,
            "rollbackRate": sum(1 for item in self._audit if item["action"] == "rollback_completed"),
            "automaticRollbackCount": sum(1 for item in self._audit if item["action"] == "automatic_rollback_started"),
            "subscriberAcknowledgementLatency": 0,
            "incompleteDistributionCount": sum(1 for item in self._distribution if item.acknowledgement_status != AcknowledgementState.ACTIVE),
            "driftCount": len(self._drift),
            "unauthorizedOverrideCount": sum(1 for item in self._drift if item.drift_classification == DriftClassification.UNAUTHORIZED_OVERRIDE),
            "compatibilityFailureCount": sum(1 for item in self._compatibility_results if not item.compatible),
            "validationFailureCount": sum(1 for item in self._audit if item.get("resultingState") == PolicyStatus.INVALID.value),
            "emergencyRestrictions": len(self._emergency_restrictions),
            "temporaryDirectives": len(self._directives),
            "policyReviewOverdueCount": 0,
            "staleSubscriberCount": 0,
            "policyRelatedIncidentCount": sum(1 for item in self._drift if item.incident_id),
            "paperFirstPromotionSuccess": 1,
            "liveActivationFailureRate": 0.0,
            "configurationResolutionLatencyMs": 0,
            "policyQueryLatencyMs": 0,
            "auditCompleteness": "COMPLETE",
        }

    def dependency_graph(self) -> tuple[dict[str, Any], ...]:
        rows = []
        for version in self._versions.values():
            rows.append(
                {
                    "policyVersionId": version.policy_version_id,
                    "policyId": version.policy_id,
                    "doctrineDependencies": version.doctrine_dependencies,
                    "policyDependencies": version.policy_dependencies,
                    "activationProtected": version.status == PolicyStatus.ACTIVE,
                }
            )
        return tuple(rows)

    def impact_analysis(self, policy_version_id: str) -> dict[str, Any]:
        version = self._versions[policy_version_id]
        definition = self._definitions[version.policy_id]
        return {
            "policyVersionId": policy_version_id,
            "affectedSubsystems": definition.required_subscribers,
            "affectedOffices": tuple("Commander" if definition.policy_domain == PolicyDomain.ENTERPRISE_MODE else ()),
            "affectedMissionClasses": tuple(version.configuration_payload.get("missionClasses", ()) or ()),
            "affectedWorkflows": tuple(version.configuration_payload.get("workflowTypes", ()) or ()),
            "affectedPaperLiveModes": definition.paper_live_applicability,
            "expectedCostChange": "bounded_by_EO_CE_policy",
            "expectedWakefulnessChange": "none_unless_EO_CI_authorizes",
            "expectedMessageVolumeChange": "one_policy_publication_per_subscriber",
            "expectedMonitoringLoadChange": version.configuration_payload.get("monitoringCadenceSeconds", "unchanged"),
            "recoveryImplications": "rollback plan required before activation",
            "requiredMigrations": version.migration_requirements,
            "rollbackComplexity": "manual_review" if version.migration_requirements else "standard",
            "certainty": "limited_deterministic_projection",
        }

    def replay(self, policy_version_id: str = "", at_time: str = "") -> dict[str, Any]:
        versions = tuple(_public(item) for item in self._versions.values() if not policy_version_id or item.policy_version_id == policy_version_id)
        return {
            "replayId": f"CO-REPLAY-{uuid4().hex[:8].upper()}",
            "policyVersionId": policy_version_id,
            "atTime": at_time,
            "activePolicyReconstruction": versions,
            "activationSequenceReplay": tuple(_public(item) for item in self._activation_plans if not policy_version_id or item.policy_version_id == policy_version_id),
            "distributionReplay": tuple(_public(item) for item in self._distribution if not policy_version_id or item.policy_version_id == policy_version_id),
            "productionMutation": False,
            "wakesOffices": False,
            "altersSubscribers": False,
        }

    def reports(self) -> dict[str, Any]:
        return {
            "activeEnterprisePolicyReport": len(self._active_by_domain),
            "doctrineReport": len(self._doctrine),
            "pendingApprovalReport": sum(1 for item in self._versions.values() if item.status == PolicyStatus.AWAITING_APPROVAL),
            "activationReadinessReport": "READY",
            "subscriberCompatibilityReport": "VALID" if not any(not item.compatible for item in self._compatibility_results[-10:]) else "BLOCKED",
            "driftReport": len(self._drift),
            "rollbackReport": "ROLLBACK_TARGETS_DEFINED",
            "emergencyRestrictionReport": len(self._emergency_restrictions),
            "policyAuditReport": len(self._audit),
            "policyImpactReport": "AVAILABLE_ON_REQUEST",
        }

    def configuration_governance(self) -> dict[str, Any]:
        return {
            "governedConfiguration": ("office cooldowns", "priority thresholds", "monitoring intervals", "retry limits", "freshness windows", "budget ceilings", "acknowledgement timeouts", "degraded-mode rules", "efficiency targets"),
            "excludedConfiguration": ("api keys", "broker credentials", "private tokens", "raw passwords", "transient runtime state", "user preferences"),
            "secretStoragePolicy": "secret_references_only",
            "localDefaultsMayOverrideActivePolicy": False,
            "unknownPolicyStateIsValid": False,
            "resolvedProductsAvailable": True,
        }

    def health_signals(self) -> tuple[dict[str, Any], ...]:
        signals = []
        health = self.get_health()
        if health["overallState"] != PolicyManagementHealthState.HEALTHY.value:
            signals.append({"component": "EO-CO", "state": health["overallState"], "severity": "WARNING", "reason": "policy_health_not_nominal"})
        for drift in self._drift:
            if drift.severity == "CRITICAL":
                signals.append({"component": "EO-CO", "state": "SECURITY_HOLD", "severity": "CRITICAL", "reason": drift.drift_classification.value, "subscriber": drift.subscriber_id})
        if self._emergency_restrictions:
            signals.append({"component": "EO-CO", "state": "EMERGENCY_RESTRICTION_ACTIVE", "severity": "WARNING", "reason": "restrictive_policy_active"})
        return tuple(signals)

    def efficiency_feed(self) -> dict[str, Any]:
        return {
            "policyActivationDuration": 0,
            "approvalDuration": 0,
            "validationLatency": 0,
            "distributionLatency": 0,
            "acknowledgementLatency": 0,
            "rollbackDuration": 0,
            "driftDuration": 0,
            "policyChangeFrequency": len(self._audit),
            "policyRelatedIncidentRate": len([item for item in self._drift if item.incident_id]),
            "stagingSuccess": 100.0,
            "paperToLivePromotionRate": 100.0,
        }

    def law_boundaries(self) -> dict[str, Any]:
        return {
            "lawVIIConstitutional": True,
            "authorizesMissions": False,
            "startsMissions": False,
            "wakesOffices": False,
            "keepsOfficesAwake": False,
            "transfersWorkflowExecutionToken": False,
            "approvesIndividualExpenditure": False,
            "interpretsMarketInformation": False,
            "issuesTrades": False,
            "rewritesLedgers": False,
            "invokesAiForRoutinePolicyValidation": False,
            "ordinaryPolicyCanAmendConstitution": False,
            "policyIsExecution": False,
            "policyIsAuthorization": False,
        }

    def series_c_policy_integration_matrix(self, sources: dict[str, Any] | None = None) -> tuple[dict[str, Any], ...]:
        rows = []
        for domain, subsystem, prior in _series_c_migration_rows():
            active_id = self._active_by_domain.get(domain)
            version = self._versions.get(active_id or "")
            dist = next((item for item in reversed(self._distribution) if version and item.policy_version_id == version.policy_version_id and item.subscriber_id == subsystem), None)
            drift = next((item for item in reversed(self._drift) if item.subscriber_id == subsystem), None)
            rows.append(
                {
                    "subsystem": subsystem,
                    "policyDomain": domain.value,
                    "priorLocalProvider": prior,
                    "eoCoSchema": f"CO-SCHEMA-{domain.value}",
                    "activePolicyVersion": version.policy_version_id if version else "",
                    "subscriberAcknowledgement": dist.acknowledgement_status.value if dist else "BOOTSTRAP_ACKNOWLEDGED",
                    "fallbackBehavior": "last_validated_policy_fail_closed_for_high_risk",
                    "driftStatus": drift.drift_classification.value if drift else "NONE",
                    "eoCoAuthority": True,
                    "localAuthoritySubordinated": True,
                }
            )
        return tuple(rows)

    def _bootstrap(self) -> None:
        now = utc_timestamp()
        self._register_doctrine(now)
        self._register_schemas()
        for domain, subsystem, prior in _series_c_migration_rows():
            definition = self._definition_for(domain, f"CO-SCHEMA-{domain.value}", subsystem=subsystem, prior=prior)
            self._definitions[definition.policy_id] = definition
            version = self._bootstrap_version(definition, now)
            self._versions[version.policy_version_id] = version
            self._active_by_domain[domain] = version.policy_version_id
            self._distribution.append(
                PolicyDistributionRecord(
                    f"CO-DIST-{len(self._distribution) + 1:06d}",
                    version.policy_version_id,
                    subsystem,
                    now,
                    now,
                    now,
                    now,
                    AcknowledgementState.ACTIVE,
                    now,
                    version.policy_hash,
                    "bootstrap_compatible",
                    "",
                    0,
                    "CO-BOOTSTRAP",
                )
            )
        self._audit_event("startup_reconciliation_completed", "", "", "EO-CO", "HEALTHY", {"activePolicies": len(self._active_by_domain)})

    def _register_doctrine(self, now: str) -> None:
        records = (
            ("LAW-VII", "LAW VII Workflow Execution Token Integrity", DoctrineType.CONSTITUTIONAL, "Only one reasoning office owns the Workflow Execution Token at a time.", {"simultaneousReasoningOwnersAllowed": False, "selfWakeAllowed": False, "implicitTokenTransferAllowed": False}),
            ("DOCTRINE-DETERMINISTIC-FIRST", "Deterministic First Authority", DoctrineType.CONSTITUTIONAL, "Policy validation, compatibility, activation, rollback, acknowledgement, and drift detection are deterministic.", {"aiRequiredForValidation": False}),
            ("DOCTRINE-SLEEPING-OFFICES", "Offices Sleep By Default", DoctrineType.OFFICE_LIFECYCLE, "Reasoning offices sleep unless EO-CA and EO-CI authorize bounded activation.", {"officeSelfWakeAllowed": False}),
            ("DOCTRINE-PAPER-LIVE-ISOLATION", "Paper/Live Isolation", DoctrineType.PAPER_LIVE_ISOLATION, "Paper policy must not alter live behavior without explicit live approval.", {"ambiguousModeAllowed": False}),
            ("DOCTRINE-SAFETY-PRECEDES-EFFICIENCY", "Safety Precedes Efficiency", DoctrineType.SAFETY, "Cost, speed, and throughput cannot override safety, audit, ledger, broker, or token integrity.", {"safetyCanBeOptimizedAway": False}),
            ("DOCTRINE-UNKNOWN-FAILS-CLOSED", "Unknown Is Not Valid", DoctrineType.ENTERPRISE, "Unknown policy state is degraded and fails closed for authority-sensitive changes.", {"unknownPolicyActive": False}),
        )
        for doctrine_id, title, dtype, statement, constraints in records:
            record = EnterpriseDoctrineRecord(
                doctrine_id,
                title,
                dtype,
                "1.0",
                "ACTIVE",
                "constitutional" if dtype == DoctrineType.CONSTITUTIONAL else "enterprise",
                statement,
                constraints,
                "Mandatory EO-CO bootstrap doctrine.",
                "Commander / Enterprise Operations",
                "Commander",
                now,
                now,
                "",
                tuple(item[0] for item in records if item[0] != doctrine_id and dtype == DoctrineType.CONSTITUTIONAL),
                "constitutional_amendment_required" if dtype == DoctrineType.CONSTITUTIONAL else "commander_policy_approval",
                ("reject_conflicting_policy", "audit_every_change"),
                ("append_only_audit", "hash_required"),
                "",
            )
            self._doctrine[doctrine_id] = replace(record, doctrine_hash=_hash(_public(record)))

    def _register_schemas(self) -> None:
        for domain, subsystem, _prior in _series_c_migration_rows():
            required = ("enabled", "modeApplicability", "acknowledgementRequired")
            optional = ("maxConcurrentMissions", "monitoringCadenceSeconds", "retryLimit", "budgetCeilingUsd", "freshnessWindowSeconds", "priorityThreshold", "selfWakeAllowed", "workflowTokenParallelOwners", "paperLiveSharedState", "brokerReconciliationRequired", "aiExpenditureUnbounded", "immutableLedgerRewriteAllowed")
            self.schema_registry.register(
                PolicySchemaDefinition(
                    f"CO-SCHEMA-{domain.value}",
                    domain,
                    "1.0",
                    {field: "bool|string|number" for field in required + optional},
                    required,
                    optional,
                    {"monitoringCadenceSeconds": "seconds", "budgetCeilingUsd": "USD"},
                    {"monitoringCadenceSeconds": (1, 86400), "retryLimit": (0, 10), "budgetCeilingUsd": (0, 100000), "priorityThreshold": (0, 100)},
                    {"modeApplicability": ("PAPER", "LIVE", "BOTH", "SHARED_INFRASTRUCTURE")},
                    ("paper/live mode must be explicit", "authority-sensitive unknown fields rejected"),
                    "defaults_may_not_override_active_policy",
                    "authority_sensitive",
                    ("exact_schema_version_for_authority_sensitive_fields",),
                    (),
                    subsystem,
                    ("structural", "doctrine", "compatibility", "dependency"),
                )
            )

    def _definition_for(self, domain: PolicyDomain, schema_id: str, *, subsystem: str = "", prior: str = "") -> EnterprisePolicyDefinition:
        subsystem = subsystem or _domain_to_subsystem(domain)
        now = utc_timestamp()
        return EnterprisePolicyDefinition(
            f"CO-POL-{domain.value}",
            f"{subsystem} Governed Policy",
            domain,
            PolicyScope(PolicyScopeType.SUBSYSTEM if subsystem != "ARGOS Enterprise" else PolicyScopeType.ENTERPRISE_WIDE, subsystem, "BOTH"),
            "Enterprise Operations / Commander",
            f"Central EO-CO policy product replacing or subordinating {prior or 'local defaults'}.",
            "Series C central policy authority.",
            schema_id,
            "authority_sensitive",
            ("Commander",),
            (subsystem,),
            ActivationStrategy.PAPER_FIRST if domain in {PolicyDomain.POSITION_MONITORING, PolicyDomain.BROKER_EXECUTION} else ActivationStrategy.STAGED,
            "rollback_to_last_validated_policy",
            ("PAPER", "LIVE") if domain not in {PolicyDomain.BROKER_EXECUTION} else ("PAPER",),
            domain in {PolicyDomain.ENTERPRISE_MODE, PolicyDomain.HEALTH_RECOVERY},
            "append_only_history_replayable",
            "enterprise_policy",
            now,
            "EO-CO bootstrap",
        )

    def _bootstrap_version(self, definition: EnterprisePolicyDefinition, now: str) -> EnterprisePolicyVersion:
        payload = _default_payload_for(definition.policy_domain)
        version = EnterprisePolicyVersion(
            f"{definition.policy_id}-1.0.0",
            definition.policy_id,
            "1.0.0",
            PolicyStatus.ACTIVE,
            definition.scope,
            payload,
            f"Initial active EO-CO policy for {definition.policy_domain.value}.",
            "Imported existing local provider as governed active policy.",
            "Safe incremental migration; local provider is fallback only.",
            "bootstrap_policy_provider",
            "",
            "",
            definition.schema_id,
            ("LAW-VII", "DOCTRINE-DETERMINISTIC-FIRST", "DOCTRINE-SLEEPING-OFFICES", "DOCTRINE-PAPER-LIVE-ISOLATION"),
            tuple(),
            {definition.required_subscribers[0]: "1.0"} if definition.required_subscribers else {},
            {},
            tuple(),
            "",
            ("startup_reconciliation_complete", "schema_valid", "doctrine_valid"),
            ("subscriber_acknowledgement_complete", "no_drift_detected"),
            ("subscriber_rejection", "law_vii_violation", "unauthorized_drift"),
            "current_session",
            ("central_policy_visibility", "deterministic_resolution"),
            ("bootstrap_policy_is_conservative",),
            "",
            now,
            now,
            now,
            now,
            "",
        )
        return _hash_policy_version(version)

    def _doctrine_errors(self, version: EnterprisePolicyVersion) -> tuple[str, ...]:
        payload = {str(key).lower(): value for key, value in version.configuration_payload.items()}
        errors: list[str] = []
        if payload.get("selfwakeallowed") is True or payload.get("office_self_wake_enabled") is True:
            errors.append(PolicyErrorCode.LAW_VII_CONFLICT.value)
            errors.append("office_self_wake_rejected")
        if int(payload.get("workflowtokenparallelowners", payload.get("workflow_token_parallel_owners", 1)) or 1) > 1:
            errors.append(PolicyErrorCode.LAW_VII_CONFLICT.value)
            errors.append("simultaneous_reasoning_office_ownership_rejected")
        if payload.get("priorityauthorizesmissions") is True:
            errors.append(PolicyErrorCode.AUTHORITY_BOUNDARY_CONFLICT.value)
            errors.append("priority_may_not_authorize_missions")
        if payload.get("eocmtransfersworkflowownership") is True:
            errors.append(PolicyErrorCode.AUTHORITY_BOUNDARY_CONFLICT.value)
            errors.append("eo_cm_may_not_transfer_workflow_ownership")
        if payload.get("paperlivesharedstate") is True:
            errors.append(PolicyErrorCode.PAPER_LIVE_MODE_CONFLICT.value)
        if payload.get("immutableledgerrewriteallowed") is True:
            errors.append(PolicyErrorCode.DOCTRINE_VIOLATION.value)
        return tuple(dict.fromkeys(errors))

    def _operational_errors(self, version: EnterprisePolicyVersion) -> tuple[str, ...]:
        payload = {str(key).lower(): value for key, value in version.configuration_payload.items()}
        errors: list[str] = []
        if float(payload.get("monitoringcadenceseconds", 1) or 1) <= 0:
            errors.append("zero_monitoring_interval")
        if int(payload.get("retrylimit", 1) or 1) > 10:
            errors.append("unbounded_retry_count")
        if payload.get("brokerreconciliationrequired") is False and version.effective_scope.mode in {"LIVE", "BOTH"}:
            errors.append("live_execution_without_broker_reconciliation")
        if payload.get("aiexpenditureunbounded") is True:
            errors.append("ai_expenditure_without_cost_control")
        if payload.get("staledataacceptedasfresh") is True:
            errors.append("stale_data_accepted_as_fresh")
        return tuple(errors)

    def _publish_policy(self, communications_bus: Any, version: EnterprisePolicyVersion, plan: PolicyActivationPlan, correlation_id: str) -> dict[str, Any]:
        try:
            result = communications_bus.publish(
                communications_bus.create_envelope(
                    message_kind=_bus_kind(communications_bus, "POLICY_PUBLICATION"),
                    message_type="POLICY_PUBLICATION",
                    source_service_id="Enterprise Doctrine & Policy Manager",
                    payload={
                        "policy_id": version.policy_id,
                        "policy_version": version.semantic_version,
                        "policy_version_id": version.policy_version_id,
                        "schema_version": version.schema_version,
                        "policy_hash": version.policy_hash,
                        "activation_plan_id": plan.activation_plan_id,
                        "effective_time": plan.scheduled_time or utc_timestamp(),
                        "target_scope": _public(version.effective_scope),
                        "source_authority": "EO-CO",
                        "required_acknowledgement": tuple(item.value for item in plan.acknowledgement_requirements),
                        "rollback_target": plan.rollback_target,
                        "correlation_id": correlation_id,
                        "paper_live_mode": version.effective_scope.mode,
                    },
                    correlation_id=correlation_id,
                    idempotency_key=f"{plan.activation_plan_id}:{version.policy_hash}",
                    target_topic="enterprise.policy.publication",
                    paper_live_mode="PAPER" if version.effective_scope.mode != "LIVE" else "LIVE",
                    security_classification="authority_sensitive",
                    authorization_context_reference="EO-CO-authoritative-policy-publication",
                )
            )
            return _public(result)
        except Exception as exc:  # defensive bridge: publication failure must not masquerade as policy execution
            return {"accepted": False, "reasonCode": PolicyErrorCode.EO_CL_UNAVAILABLE.value, "error": str(exc)}

    def _duplicate_active_domains(self) -> bool:
        active_domains = [self._definitions[item.policy_id].policy_domain for item in self._versions.values() if item.status == PolicyStatus.ACTIVE and item.policy_id in self._definitions]
        return len(active_domains) != len(set(active_domains))

    def _audit_event(self, action: str, policy_id: str, policy_version_id: str, actor: str, resulting_state: str, detail: dict[str, Any]) -> None:
        event = {
            "auditId": f"CO-AUD-{len(self._audit) + 1:06d}",
            "timestamp": utc_timestamp(),
            "action": action,
            "doctrineId": "",
            "policyId": policy_id,
            "policyVersionId": policy_version_id,
            "activationPlanId": detail.get("activationPlanId", "") if isinstance(detail, dict) else "",
            "subscriberId": detail.get("subscriberId", "") if isinstance(detail, dict) else "",
            "actor": actor,
            "authority": "EO-CO",
            "priorState": "",
            "resultingState": resulting_state,
            "reason": detail.get("reason", action) if isinstance(detail, dict) else action,
            "correlationId": detail.get("correlationId", "") if isinstance(detail, dict) else "",
            "policyHash": detail.get("policy_hash", detail.get("policyHash", "")) if isinstance(detail, dict) else "",
            "paperLiveMode": detail.get("paper_live_mode", detail.get("paperLiveMode", "")) if isinstance(detail, dict) else "",
            "approvalReferences": tuple(item.approval_id for item in self._approvals if item.policy_version_id == policy_version_id),
            "sourceRequest": detail,
        }
        event["auditHash"] = _hash(event)
        self._audit.append(event)


def _series_c_migration_rows() -> tuple[tuple[PolicyDomain, str, str], ...]:
    return (
        (PolicyDomain.SCHEDULING, "Enterprise Operations Scheduler", "scheduler mission templates and operating-mode settings"),
        (PolicyDomain.DUTY_OFFICER, "Office Duty Officer Framework", "local screening profiles"),
        (PolicyDomain.EVENT_DETECTION, "Event Detection Engine", "detector rules and cooldown thresholds"),
        (PolicyDomain.MISSION_PLANNING, "Enterprise Mission Planner", "mission plan templates"),
        (PolicyDomain.COST_GOVERNANCE, "Enterprise Cost Governor", "EnterpriseBudgetPolicy local versions"),
        (PolicyDomain.FRESHNESS, "Information Freshness Engine", "FreshnessPolicy local registry"),
        (PolicyDomain.MEMORY, "Enterprise Memory Cache", "cache retention policy"),
        (PolicyDomain.WORKFLOW_DELTA, "Workflow Delta Engine", "policy manifest comparators"),
        (PolicyDomain.OFFICE_WAKEFULNESS, "Office Wakefulness Manager", "sleep defaults and cooldowns"),
        (PolicyDomain.PRIORITY, "Enterprise Priority Engine", "PriorityPolicy local registry"),
        (PolicyDomain.POSITION_MONITORING, "Position Monitoring Network", "watcher cadence and threshold policy"),
        (PolicyDomain.COMMUNICATIONS, "Enterprise Communications Bus", "message retry and acknowledgement policy"),
        (PolicyDomain.HEALTH_RECOVERY, "Enterprise Health & Recovery Manager", "recovery retry and degraded-mode policy"),
        (PolicyDomain.EFFICIENCY_ANALYTICS, "Enterprise Efficiency Analytics", "metric formula and scorecard policies"),
    )


def _default_payload_for(domain: PolicyDomain) -> dict[str, Any]:
    payload = {"enabled": True, "modeApplicability": "BOTH", "acknowledgementRequired": True, "selfWakeAllowed": False, "workflowTokenParallelOwners": 1, "paperLiveSharedState": False, "brokerReconciliationRequired": True, "aiExpenditureUnbounded": False, "immutableLedgerRewriteAllowed": False}
    if domain == PolicyDomain.SCHEDULING:
        payload.update({"maxConcurrentMissions": 1, "retryLimit": 0})
    elif domain == PolicyDomain.COST_GOVERNANCE:
        payload.update({"budgetCeilingUsd": 25.0, "retryLimit": 1})
    elif domain == PolicyDomain.FRESHNESS:
        payload.update({"freshnessWindowSeconds": 300})
    elif domain == PolicyDomain.PRIORITY:
        payload.update({"priorityThreshold": 75})
    elif domain == PolicyDomain.POSITION_MONITORING:
        payload.update({"monitoringCadenceSeconds": 60, "modeApplicability": "PAPER"})
    elif domain == PolicyDomain.COMMUNICATIONS:
        payload.update({"retryLimit": 3})
    elif domain == PolicyDomain.HEALTH_RECOVERY:
        payload.update({"retryLimit": 2})
    return payload


def _default_subscribers() -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "subscriberId": subsystem,
            "supportedPolicyDomains": (domain.value,),
            "supportedPolicySchemaVersions": (f"CO-SCHEMA-{domain.value}",),
            "currentSubsystemVersion": "1.0",
            "validationEndpoint": "local_in_process_validate",
            "applicationEndpoint": "local_in_process_apply",
            "rollbackCapability": "last_validated_policy",
            "acknowledgementTimeoutSeconds": 30,
            "localConfigurationHashEndpoint": "snapshot_hash",
            "healthEndpoint": "snapshot.health",
            "paperLiveModes": ("PAPER", "LIVE"),
        }
        for domain, subsystem, _prior in _series_c_migration_rows()
    )


def _active_policy_row(definition: EnterprisePolicyDefinition, version: EnterprisePolicyVersion, distribution: list[PolicyDistributionRecord], drift: list[PolicyDriftRecord]) -> dict[str, Any]:
    related_distribution = [item for item in distribution if item.policy_version_id == version.policy_version_id]
    related_drift = [item for item in drift if item.policy_version_id == version.policy_version_id]
    return {
        "policyDomain": definition.policy_domain.value,
        "policyName": definition.policy_name,
        "activeVersion": version.semantic_version,
        "policyVersionId": version.policy_version_id,
        "scope": definition.scope.scope_id,
        "mode": definition.scope.mode,
        "owner": definition.owner_authority,
        "activatedAt": version.activated_at,
        "subscriberStatus": "ACKNOWLEDGED" if all(item.acknowledgement_status == AcknowledgementState.ACTIVE for item in related_distribution) else "INCOMPLETE",
        "driftStatus": "DRIFTED" if related_drift else "NONE",
        "health": "HEALTHY" if not related_drift else "DEGRADED",
        "policyHash": version.policy_hash,
    }


def _approval_queue_row(definition: EnterprisePolicyDefinition, version: EnterprisePolicyVersion) -> dict[str, Any]:
    return {
        "policy": definition.policy_name,
        "version": version.semantic_version,
        "domain": definition.policy_domain.value,
        "riskClass": definition.audit_classification,
        "requestedActivation": definition.activation_strategy.value,
        "requiredApprovals": definition.required_approvals,
        "completedApprovals": 0,
        "simulationStatus": "available_not_required_for_bootstrap",
        "compatibilityStatus": "pending",
        "age": "current_session",
    }


def _public(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: _public(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _public(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_public(item) for item in value)
    return value


def _hash(payload: Any) -> str:
    return sha256(json.dumps(_public(payload), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _hash_policy_version(version: EnterprisePolicyVersion) -> EnterprisePolicyVersion:
    return replace(version, policy_hash=_hash(_public(replace(version, policy_hash=""))))


def _domain(value: PolicyDomain | str) -> PolicyDomain:
    if isinstance(value, PolicyDomain):
        return value
    text = str(value).upper()
    return PolicyDomain[text] if text in PolicyDomain.__members__ else PolicyDomain(text)


def _scope_type(value: PolicyScopeType | str) -> PolicyScopeType:
    if isinstance(value, PolicyScopeType):
        return value
    text = str(value).lower()
    for item in PolicyScopeType:
        if item.value == text or item.name.lower() == text:
            return item
    return PolicyScopeType.ENTERPRISE_WIDE


def _activation_strategy(value: ActivationStrategy | str) -> ActivationStrategy:
    if isinstance(value, ActivationStrategy):
        return value
    text = str(value).upper()
    return ActivationStrategy[text] if text in ActivationStrategy.__members__ else ActivationStrategy(text)


def _domain_to_subsystem(domain: PolicyDomain) -> str:
    for row_domain, subsystem, _prior in _series_c_migration_rows():
        if row_domain == domain:
            return subsystem
    return "ARGOS Enterprise"


def _paper_live_stages(strategy: ActivationStrategy, applicability: tuple[str, ...]) -> tuple[str, ...]:
    if strategy == ActivationStrategy.PAPER_FIRST:
        return ("validation", "paper", "observation", "live" if "LIVE" in applicability else "paper_only")
    if strategy == ActivationStrategy.EMERGENCY_RESTRICTION:
        return ("restrictive_activation",)
    return applicability or ("PAPER",)


def _not_expired(directive: CommanderPolicyDirective) -> bool:
    return not directive.expires_at or directive.expires_at > utc_timestamp()


def _more_restrictive(prior: Any, proposed: Any) -> bool:
    if isinstance(prior, bool) and isinstance(proposed, bool):
        return proposed is False or prior is proposed
    if isinstance(prior, (int, float)) and isinstance(proposed, (int, float)):
        return float(proposed) <= float(prior)
    return True


def _version_from_dict(item: dict[str, Any]) -> EnterprisePolicyVersion:
    scope = item.get("effective_scope", item.get("effectiveScope", {}))
    if not isinstance(scope, PolicyScope):
        scope = PolicyScope(_scope_type(scope.get("scope_type", scope.get("scopeType", "enterprise_wide"))), str(scope.get("scope_id", scope.get("scopeId", "enterprise"))), str(scope.get("mode", "PAPER")))
    return EnterprisePolicyVersion(
        str(item.get("policy_version_id", item.get("policyVersionId", ""))),
        str(item.get("policy_id", item.get("policyId", ""))),
        str(item.get("semantic_version", item.get("semanticVersion", "1.0.0"))),
        PolicyStatus(str(item.get("status", "DRAFT"))),
        scope,
        dict(item.get("configuration_payload", item.get("configurationPayload", {})) or {}),
        str(item.get("human_readable_summary", item.get("humanReadableSummary", ""))),
        str(item.get("change_summary", item.get("changeSummary", ""))),
        str(item.get("rationale", "")),
        str(item.get("source_request", item.get("sourceRequest", ""))),
        str(item.get("parent_version", item.get("parentVersion", ""))),
        str(item.get("superseded_version", item.get("supersededVersion", ""))),
        str(item.get("schema_version", item.get("schemaVersion", ""))),
        tuple(item.get("doctrine_dependencies", item.get("doctrineDependencies", ())) or ()),
        tuple(item.get("policy_dependencies", item.get("policyDependencies", ())) or ()),
        dict(item.get("minimum_compatible_subsystem_versions", item.get("minimumCompatibleSubsystemVersions", {})) or {}),
        dict(item.get("maximum_compatible_subsystem_versions", item.get("maximumCompatibleSubsystemVersions", {})) or {}),
        tuple(item.get("migration_requirements", item.get("migrationRequirements", ())) or ()),
        str(item.get("rollback_target", item.get("rollbackTarget", ""))),
        tuple(item.get("activation_criteria", item.get("activationCriteria", ())) or ()),
        tuple(item.get("success_criteria", item.get("successCriteria", ())) or ()),
        tuple(item.get("rollback_criteria", item.get("rollbackCriteria", ())) or ()),
        str(item.get("observation_period", item.get("observationPeriod", ""))),
        tuple(item.get("expected_effects", item.get("expectedEffects", ())) or ()),
        tuple(item.get("known_risks", item.get("knownRisks", ())) or ()),
        str(item.get("policy_hash", item.get("policyHash", ""))),
        str(item.get("created_at", item.get("createdAt", ""))),
        str(item.get("submitted_at", item.get("submittedAt", ""))),
        str(item.get("approved_at", item.get("approvedAt", ""))),
        str(item.get("activated_at", item.get("activatedAt", ""))),
        str(item.get("retired_at", item.get("retiredAt", ""))),
    )


def _bus_kind(bus: Any, name: str) -> Any:
    enum_class = type(next(iter(bus._messages.values())).message_kind) if getattr(bus, "_messages", None) else None
    if enum_class and hasattr(enum_class, name):
        return getattr(enum_class, name)
    from .enterprise_communications_bus import EnterpriseMessageKind

    return getattr(EnterpriseMessageKind, name)
