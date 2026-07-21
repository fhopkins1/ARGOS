"""SEEK-RM-001 through SEEK-RM-007 Seeker office integrity support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


SEEK_RM_VERSION = "SEEK-RM-001-TO-014/1.0.0"


class SeekerLifecycleState(str, Enum):
    DORMANT = "DORMANT"
    MISSION_RECEIVED = "MISSION_RECEIVED"
    MISSION_AUTHORITY_VALIDATING = "MISSION_AUTHORITY_VALIDATING"
    SEARCH_PLAN_VALIDATING = "SEARCH_PLAN_VALIDATING"
    EXECUTION_INITIALIZING = "EXECUTION_INITIALIZING"
    DISCOVERY_EXECUTING = "DISCOVERY_EXECUTING"
    DISCOVERY_EVIDENCE_PRESERVING = "DISCOVERY_EVIDENCE_PRESERVING"
    RESULT_NORMALIZING = "RESULT_NORMALIZING"
    CANDIDATE_IDENTITY_VALIDATING = "CANDIDATE_IDENTITY_VALIDATING"
    DUPLICATE_EVALUATING = "DUPLICATE_EVALUATING"
    FRESHNESS_EVALUATING = "FRESHNESS_EVALUATING"
    INDEPENDENCE_EVALUATING = "INDEPENDENCE_EVALUATING"
    CANDIDATE_ADMISSIBILITY_EVALUATING = "CANDIDATE_ADMISSIBILITY_EVALUATING"
    SEARCH_SUFFICIENCY_EVALUATING = "SEARCH_SUFFICIENCY_EVALUATING"
    CANDIDATE_PACKAGE_ASSEMBLING = "CANDIDATE_PACKAGE_ASSEMBLING"
    CANDIDATE_PACKAGE_VALIDATING = "CANDIDATE_PACKAGE_VALIDATING"
    CANDIDATE_PACKAGE_FINALIZING = "CANDIDATE_PACKAGE_FINALIZING"
    OUTBOUND_COMMITTING = "OUTBOUND_COMMITTING"
    AUTHORITY_RELINQUISHING = "AUTHORITY_RELINQUISHING"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    RECOVERING = "RECOVERING"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True)
class SeekerSearchMission:
    mission_id: str
    mission_version: str
    objective_id: str
    constitutional_authority: str
    search_plan_id: str
    execution_parameters: Mapping[str, str]
    rule_versions: Mapping[str, str]
    discovery_scope: tuple[str, ...]
    mission_creation_timestamp: str
    replay_identifier: str = ""
    recovery_identifier: str = ""


@dataclass(frozen=True)
class SeekerApprovedSearchPlan:
    search_plan_id: str
    search_plan_version: str
    approval_status: str
    approval_authority: str
    search_objective: str
    permitted_domains: tuple[str, ...]
    approved_sources: tuple[str, ...]
    approved_methods: tuple[str, ...]
    candidate_inclusion_rules: tuple[str, ...]
    candidate_exclusion_rules: tuple[str, ...]
    identity_requirements: tuple[str, ...]
    freshness_requirements: tuple[str, ...]
    duplicate_rules: tuple[str, ...]
    independence_requirements: tuple[str, ...]
    sufficiency_requirements: tuple[str, ...]
    termination_conditions: tuple[str, ...]
    execution_limits: Mapping[str, int]
    immutable_digest: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "immutable_digest", _digest(self))


@dataclass(frozen=True)
class SeekerDiscoveryEvidence:
    evidence_id: str
    source_id: str
    acquisition_method: str
    search_activity_id: str
    payload: Mapping[str, str]
    retrieved_at: str
    source_timestamp: str
    evidence_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_hash", _digest(self))


@dataclass(frozen=True)
class SeekerCandidateIdentityInput:
    candidate_reference: str
    candidate_type: str
    evidence_references: tuple[str, ...]
    attributes: Mapping[str, str]


@dataclass(frozen=True)
class SeekerBoundaryRegistryRecord:
    registry_identifier: str
    office_identity: str
    registered_components: tuple[str, ...]
    owned_state: tuple[str, ...]
    owned_inputs: tuple[str, ...]
    owned_outputs: tuple[str, ...]
    constitutional_interfaces: Mapping[str, tuple[str, ...]]
    excluded_responsibilities: tuple[str, ...]
    duplicate_owners: tuple[str, ...]
    undefined_components: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerSelfCertificationSeparationRecord:
    separation_identifier: str
    office_identity: str
    prohibited_terms: tuple[str, ...]
    detected_self_certification_paths: tuple[str, ...]
    operational_decisions_only: bool
    independent_authority: str
    seeker_controls_certification_verdict: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerMissionIntakeRecord:
    intake_identifier: str
    mission_id: str
    validation_stages: tuple[str, ...]
    missing_fields: tuple[str, ...]
    rejected_authority: tuple[str, ...]
    duplicate_mission_detected: bool
    initial_state: str
    final_state: str
    discovery_started_before_activation: bool
    activation_decision: str
    failure_reason: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerLifecycleStateMachineRecord:
    lifecycle_identifier: str
    lifecycle_version: str
    state_inventory: tuple[str, ...]
    transition_sequence: tuple[str, ...]
    invalid_transitions: tuple[str, ...]
    bypass_findings: tuple[str, ...]
    residual_authority: tuple[str, ...]
    terminal_state: str
    replay_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerSearchPlanEnforcementRecord:
    enforcement_identifier: str
    search_plan_id: str
    search_plan_version: str
    missing_plan_elements: tuple[str, ...]
    unauthorized_sources: tuple[str, ...]
    unauthorized_methods: tuple[str, ...]
    scope_violations: tuple[str, ...]
    immutable_plan_digest: str
    candidate_traceability_complete: bool
    replay_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerObjectiveValidationRecord:
    objective_identifier: str
    objective_id: str
    validation_decision: str
    missing_fields: tuple[str, ...]
    ambiguity_findings: tuple[str, ...]
    prohibited_responsibilities: tuple[str, ...]
    plan_consistency_findings: tuple[str, ...]
    rule_versions: Mapping[str, str]
    immutable_evidence_identifier: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCandidateIdentityValidationRecord:
    identity_identifier: str
    candidate_reference: str
    canonical_identity: str
    required_identity_fields: tuple[str, ...]
    missing_identity_fields: tuple[str, ...]
    conflicting_identity_fields: tuple[str, ...]
    unsupported_identity_fields: tuple[str, ...]
    ambiguity_findings: tuple[str, ...]
    evidence_references: tuple[str, ...]
    identity_immutable: bool
    validation_decision: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerDiscoveryEvidencePreservationRecord:
    preservation_identifier: str
    required_categories: tuple[str, ...]
    missing_categories: tuple[str, ...]
    evidence_identifiers: tuple[str, ...]
    provenance_complete: bool
    chronology_reconstructable: bool
    immutable_hashes: tuple[str, ...]
    prohibited_content_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerDiscoveryNormalizationRecord:
    normalization_identifier: str
    normalization_rule_version: str
    canonical_payload_digest: str
    raw_evidence_hashes_preserved: tuple[str, ...]
    semantic_preservation: bool
    prohibited_transformations: tuple[str, ...]
    replay_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerChronologyIntegrityRecord:
    chronology_identifier: str
    timestamp_rule_version: str
    event_sequence: tuple[str, ...]
    missing_events: tuple[str, ...]
    ordering_violations: tuple[str, ...]
    source_time_preserved: bool
    internal_external_time_separated: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerFreshnessDeterminationRecord:
    freshness_identifier: str
    candidate_reference: str
    freshness_rule_version: str
    authoritative_timestamp: str
    evaluation_timestamp: str
    freshness_window_days: int
    freshness_decision: str
    rejection_reason: str
    timestamp_basis: str
    replay_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerDuplicateSuppressionRecord:
    duplicate_identifier: str
    duplicate_rule_version: str
    evaluated_candidate_identities: tuple[str, ...]
    authoritative_candidates: tuple[str, ...]
    suppressed_duplicates: tuple[str, ...]
    evidence_preserved_for_suppressed: bool
    order_independent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRelationshipIndependenceRecord:
    relationship_identifier: str
    independence_rule_version: str
    relationship_classifications: Mapping[str, str]
    unsupported_relationships: tuple[str, ...]
    duplicate_economic_representations: tuple[str, ...]
    independence_decision: str
    cross_source_independence: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerSearchSufficiencyRecord:
    sufficiency_identifier: str
    sufficiency_rule_version: str
    required_sources: tuple[str, ...]
    processed_sources: tuple[str, ...]
    missing_required_sources: tuple[str, ...]
    approved_exclusions: tuple[str, ...]
    candidate_count_observed: int
    sufficiency_decision: str
    replay_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerUnsupportedCandidateEliminationRecord:
    elimination_identifier: str
    candidate_reference: str
    support_requirements: tuple[str, ...]
    failed_support_requirements: tuple[str, ...]
    rejection_reason: str
    rejection_evidence_references: tuple[str, ...]
    package_inclusion_permitted: bool
    replay_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerDispositionHandlingRecord:
    disposition_identifier: str
    candidate_reference: str
    disposition_rule_version: str
    disposition: str
    reason_code: str
    evidence_references: tuple[str, ...]
    silent_disposition_detected: bool
    package_protected: bool
    quarantine_isolated: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerStateIdempotencyRecord:
    state_identifier: str
    owned_state: tuple[str, ...]
    mutation_sequence: tuple[str, ...]
    duplicate_execution_detected: bool
    duplicate_outcomes: tuple[str, ...]
    residual_active_state: tuple[str, ...]
    idempotency_decision: str
    final_state: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCandidatePackageContractRecord:
    package_contract_identifier: str
    package_identifier: str
    contract_version: str
    outcome_type: str
    mandatory_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    prohibited_content_findings: tuple[str, ...]
    candidate_evidence_traceability: bool
    rejection_accounting_complete: bool
    package_integrity_digest: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerBoundaryCommitmentRecord:
    commitment_identifier: str
    package_identifier: str
    commitment_decision: str
    eligibility_failures: tuple[str, ...]
    atomic_commitment: bool
    committed_once: bool
    authority_relinquished: bool
    downstream_dependencies: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCompleteAuditTrailRecord:
    audit_identifier: str
    required_audit_stages: tuple[str, ...]
    observed_audit_stages: tuple[str, ...]
    missing_audit_stages: tuple[str, ...]
    decision_traceability_complete: bool
    evidence_traceability_complete: bool
    independently_reconstructable: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerPersistenceAtomicRecoveryRecord:
    persistence_identifier: str
    checkpoint_boundaries: tuple[str, ...]
    persisted_state_hashes: tuple[str, ...]
    partial_write_findings: tuple[str, ...]
    duplicate_commitment_findings: tuple[str, ...]
    recovery_disposition: str
    replay_from_recovery_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerDeterministicReplayRecord:
    replay_identifier: str
    replay_input_digest: str
    original_package_digest: str
    replay_package_digest: str
    live_external_dependency_detected: bool
    historical_evidence_modified: bool
    semantic_equivalence: bool
    replay_environment: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerConfigurationRuleIntegrityRecord:
    configuration_identifier: str
    configuration_digest: str
    bound_rule_manifest: Mapping[str, str]
    missing_rule_versions: tuple[str, ...]
    incompatible_rule_versions: tuple[str, ...]
    configuration_drift_findings: tuple[str, ...]
    replay_uses_original_rules: bool
    recovery_uses_original_configuration: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerResourceTerminationRecord:
    resource_identifier: str
    resource_rule_version: str
    authorized_budget: Mapping[str, int]
    consumed_resources: Mapping[str, int]
    budget_violations: tuple[str, ...]
    termination_outcome: str
    resources_released: bool
    residual_resources: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerDormancyRelinquishmentRecord:
    dormancy_identifier: str
    authority_inventory: tuple[str, ...]
    terminal_authority_dispositions: Mapping[str, str]
    residual_state_manifest: Mapping[str, str]
    unauthorized_residual_state: tuple[str, ...]
    new_work_frozen: bool
    dormancy_admission: str
    bridge_independent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerExternalDependencyIsolationRecord:
    dependency_identifier: str
    authorized_external_inputs: tuple[str, ...]
    unauthorized_runtime_dependencies: tuple[str, ...]
    external_office_dependencies: tuple[str, ...]
    bridge_dependencies: tuple[str, ...]
    enterprise_infrastructure_dependencies: tuple[str, ...]
    recovery_independent: bool
    replay_independent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerIndependentCertificationSuiteRecord:
    certification_suite_identifier: str
    certification_authority: str
    requirement_count: int
    tests_executed: int
    failed_requirements: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    evidence_coverage: str
    seeker_controls_verdict: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCertificationClosureRecord:
    closure_identifier: str
    certifying_authority: str
    doctrine_coverage: tuple[str, ...]
    unresolved_deficiencies: tuple[str, ...]
    traceability_matrix_digest: str
    certification_report_digest: str
    final_verdict: EnterpriseCertificationDecision
    office_scope_only: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerSearchMissionConstitutionalObjectRecord:
    object_identifier: str
    constitutional_schema_version: str
    required_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    authority_scope: tuple[str, ...]
    prohibited_authority_findings: tuple[str, ...]
    lifecycle_states: tuple[str, ...]
    invalid_lifecycle_findings: tuple[str, ...]
    immutable_identity_digest: str
    execution_state_separated: bool
    persistence_preserves_meaning: bool
    replay_preserves_meaning: bool
    recovery_preserves_meaning: bool
    audit_events: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerSearchPlanConstitutionalObjectRecord:
    object_identifier: str
    constitutional_schema_version: str
    required_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    originating_mission_id: str
    execution_sequence: tuple[str, ...]
    nondeterministic_findings: tuple[str, ...]
    immutable_rule_manifest: Mapping[str, str]
    traceability_references: tuple[str, ...]
    one_mission_one_plan: bool
    replay_preserves_plan: bool
    recovery_preserves_plan: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCandidatePackageConstitutionalObjectRecord:
    object_identifier: str
    package_identifier: str
    required_elements: tuple[str, ...]
    missing_elements: tuple[str, ...]
    candidate_count: int
    evidence_references: tuple[str, ...]
    provenance_chain: tuple[str, ...]
    validation_results: Mapping[str, str]
    invariant_violations: tuple[str, ...]
    committed_immutable: bool
    replay_equivalent: bool
    recovery_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerEnterpriseCandidateIdentityDoctrineRecord:
    object_identifier: str
    identity_identifier: str
    candidate_class: str
    canonical_primary_identifier: str
    identity_namespace: str
    identity_version: str
    identity_authority: str
    normalization_version: str
    equivalence_class_identifier: str
    alternate_identifiers: tuple[str, ...]
    collision_findings: tuple[str, ...]
    ambiguity_findings: tuple[str, ...]
    evidence_references: tuple[str, ...]
    confidence_status: str
    completeness_status: str
    replay_uses_original_version: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCandidateConstitutionalLifecycleRecord:
    lifecycle_identifier: str
    candidate_identifier: str
    state_sequence: tuple[str, ...]
    invalid_transitions: tuple[str, ...]
    skipped_required_states: tuple[str, ...]
    terminal_outcome: str
    multiple_active_state_findings: tuple[str, ...]
    lifecycle_audit_references: tuple[str, ...]
    replay_equivalent: bool
    recovery_checkpoint_valid: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerSearchMissionConstitutionalLifecycleRecord:
    lifecycle_identifier: str
    mission_identifier: str
    state_sequence: tuple[str, ...]
    invalid_transitions: tuple[str, ...]
    skipped_required_states: tuple[str, ...]
    authority_relinquished: bool
    terminal_state: str
    lifecycle_audit_references: tuple[str, ...]
    replay_equivalent: bool
    recovery_checkpoint_valid: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerSearchSufficiencyMetricsRecord:
    metrics_identifier: str
    sufficiency_rule_version: str
    evaluated_mission_id: str
    evaluated_search_plan_id: str
    required_coverage: tuple[str, ...]
    achieved_coverage: tuple[str, ...]
    incomplete_coverage: tuple[str, ...]
    validated_candidate_count: int
    duplicate_credit_suppressed: bool
    freshness_requirements_met: bool
    independence_requirements_met: bool
    package_requirements_met: bool
    audit_requirements_met: bool
    sufficiency_outcome: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerConstitutionalObjectsEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    search_mission_object: SeekerSearchMissionConstitutionalObjectRecord
    search_plan_object: SeekerSearchPlanConstitutionalObjectRecord
    candidate_package_object: SeekerCandidatePackageConstitutionalObjectRecord
    candidate_identity_doctrine: SeekerEnterpriseCandidateIdentityDoctrineRecord
    candidate_lifecycle: SeekerCandidateConstitutionalLifecycleRecord
    search_mission_lifecycle: SeekerSearchMissionConstitutionalLifecycleRecord
    search_sufficiency_metrics: SeekerSearchSufficiencyMetricsRecord
    final_object_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerOfficeIntegrityEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    office_identity: str
    remediation_order_coverage: tuple[str, ...]
    boundary_registry: SeekerBoundaryRegistryRecord
    self_certification_separation: SeekerSelfCertificationSeparationRecord
    mission_intake: SeekerMissionIntakeRecord
    lifecycle_state_machine: SeekerLifecycleStateMachineRecord
    search_plan_enforcement: SeekerSearchPlanEnforcementRecord
    objective_validation: SeekerObjectiveValidationRecord
    candidate_identity_validation: SeekerCandidateIdentityValidationRecord
    discovery_evidence_preservation: SeekerDiscoveryEvidencePreservationRecord
    discovery_normalization: SeekerDiscoveryNormalizationRecord
    chronology_integrity: SeekerChronologyIntegrityRecord
    freshness_determination: SeekerFreshnessDeterminationRecord
    duplicate_suppression: SeekerDuplicateSuppressionRecord
    relationship_independence: SeekerRelationshipIndependenceRecord
    search_sufficiency: SeekerSearchSufficiencyRecord
    unsupported_candidate_elimination: SeekerUnsupportedCandidateEliminationRecord
    disposition_handling: SeekerDispositionHandlingRecord
    state_idempotency: SeekerStateIdempotencyRecord
    candidate_package_contract: SeekerCandidatePackageContractRecord
    boundary_commitment: SeekerBoundaryCommitmentRecord
    complete_audit_trail: SeekerCompleteAuditTrailRecord
    persistence_atomic_recovery: SeekerPersistenceAtomicRecoveryRecord
    deterministic_replay: SeekerDeterministicReplayRecord
    configuration_rule_integrity: SeekerConfigurationRuleIntegrityRecord
    resource_termination_boundaries: SeekerResourceTerminationRecord
    dormancy_relinquishment: SeekerDormancyRelinquishmentRecord
    external_dependency_isolation: SeekerExternalDependencyIsolationRecord
    independent_certification_suite: SeekerIndependentCertificationSuiteRecord
    certification_closure: SeekerCertificationClosureRecord
    final_office_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


class SeekerOfficeIntegritySupport:
    """Build independent certification-support records for Seeker RM orders."""

    constitutional_object_order_coverage = (
        "SEEK-RM-002-001",
        "SEEK-RM-002-002",
        "SEEK-RM-002-003",
        "SEEK-RM-002-004",
        "SEEK-RM-002-005",
        "SEEK-RM-002-006",
        "SEEK-RM-002-007",
    )

    remediation_order_coverage = (
        "SEEK-RM-001-001",
        "SEEK-RM-002",
        "SEEK-RM-003",
        "SEEK-RM-004",
        "SEEK-RM-005",
        "SEEK-RM-006",
        "SEEK-RM-007",
        "SEEK-RM-001-008",
        "SEEK-RM-009",
        "SEEK-RM-010",
        "SEEK-RM-011",
        "SEEK-RM-012",
        "SEEK-RM-013",
        "SEEK-RM-014",
        "SEEK-RM-001-015",
        "SEEK-RM-016",
        "SEEK-RM-017",
        "SEEK-RM-018",
        "SEEK-RM-019",
        "SEEK-RM-020",
        "SEEK-RM-021",
        "SEEK-RM-001-022",
        "SEEK-RM-023",
        "SEEK-RM-024",
        "SEEK-RM-025",
        "SEEK-RM-026",
        "SEEK-RM-027",
        "SEEK-RM-028",
    )

    component_registry = (
        "Mission Intake Component",
        "Search Plan Validation Component",
        "Discovery Execution Component",
        "Discovery Evidence Registry",
        "Candidate Identity Component",
        "Duplicate Detection Component",
        "Freshness Validation Component",
        "Independence Validation Component",
        "Search Sufficiency Component",
        "Candidate Package Construction Component",
        "Candidate Package Commitment Component",
        "Audit Evidence Component",
        "Replay Component",
        "Recovery Component",
        "Lifecycle Component",
    )

    owned_state = (
        "Mission State",
        "Discovery State",
        "Search Plan State",
        "Candidate Registry",
        "Duplicate Registry",
        "Freshness Evaluation State",
        "Independence Evaluation State",
        "Search Sufficiency State",
        "Candidate Package State",
        "Audit State",
        "Replay State",
        "Recovery State",
        "Lifecycle State",
    )

    excluded_responsibilities = (
        "market observation",
        "market monitoring",
        "market interpretation",
        "financial analysis",
        "scoring investment quality",
        "ranking opportunities",
        "portfolio optimization",
        "risk assessment",
        "authorization",
        "trading",
        "broker communication",
        "enterprise scheduling",
        "bridge transport",
        "workflow orchestration",
        "enterprise persistence",
        "enterprise certification",
        "self-certification",
    )

    lifecycle_success_path = (
        SeekerLifecycleState.DORMANT.value,
        SeekerLifecycleState.MISSION_RECEIVED.value,
        SeekerLifecycleState.MISSION_AUTHORITY_VALIDATING.value,
        SeekerLifecycleState.SEARCH_PLAN_VALIDATING.value,
        SeekerLifecycleState.EXECUTION_INITIALIZING.value,
        SeekerLifecycleState.DISCOVERY_EXECUTING.value,
        SeekerLifecycleState.DISCOVERY_EVIDENCE_PRESERVING.value,
        SeekerLifecycleState.RESULT_NORMALIZING.value,
        SeekerLifecycleState.CANDIDATE_IDENTITY_VALIDATING.value,
        SeekerLifecycleState.DUPLICATE_EVALUATING.value,
        SeekerLifecycleState.FRESHNESS_EVALUATING.value,
        SeekerLifecycleState.INDEPENDENCE_EVALUATING.value,
        SeekerLifecycleState.CANDIDATE_ADMISSIBILITY_EVALUATING.value,
        SeekerLifecycleState.SEARCH_SUFFICIENCY_EVALUATING.value,
        SeekerLifecycleState.CANDIDATE_PACKAGE_ASSEMBLING.value,
        SeekerLifecycleState.CANDIDATE_PACKAGE_VALIDATING.value,
        SeekerLifecycleState.CANDIDATE_PACKAGE_FINALIZING.value,
        SeekerLifecycleState.OUTBOUND_COMMITTING.value,
        SeekerLifecycleState.AUTHORITY_RELINQUISHING.value,
        SeekerLifecycleState.DORMANT.value,
    )

    def build_package(
        self,
        *,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
        lifecycle_sequence: tuple[str, ...] | None = None,
        inspected_artifacts: Mapping[str, Mapping[str, Any]] | None = None,
        active_missions: tuple[str, ...] = (),
    ) -> SeekerOfficeIntegrityEvidencePackage:
        boundary = self.evaluate_boundary_registry()
        separation = self.evaluate_self_certification_separation(inspected_artifacts or {})
        intake = self.evaluate_mission_intake(mission, search_plan, active_missions=active_missions)
        lifecycle = self.evaluate_lifecycle_state_machine(lifecycle_sequence or self.lifecycle_success_path)
        enforcement = self.evaluate_search_plan_enforcement(search_plan, discovery_evidence, candidate)
        objective = self.evaluate_objective_validation(mission, search_plan)
        identity = self.evaluate_candidate_identity(candidate, search_plan, discovery_evidence)
        preservation = self.evaluate_discovery_evidence_preservation(mission, search_plan, discovery_evidence, candidate)
        normalization = self.evaluate_discovery_normalization(discovery_evidence, candidate)
        chronology = self.evaluate_chronology_integrity(mission, search_plan, discovery_evidence)
        freshness = self.evaluate_freshness_determination(mission, search_plan, candidate, discovery_evidence)
        duplicates = self.evaluate_duplicate_suppression(search_plan, (candidate,), discovery_evidence)
        independence = self.evaluate_relationship_independence(search_plan, (candidate,), discovery_evidence)
        sufficiency = self.evaluate_search_sufficiency(search_plan, discovery_evidence, (candidate,))
        elimination = self.evaluate_unsupported_candidate_elimination(
            candidate,
            (identity, preservation, freshness, duplicates, independence, sufficiency),
        )
        disposition = self.evaluate_disposition_handling(candidate, elimination)
        state_idempotency = self.evaluate_state_idempotency(
            lifecycle,
            mission,
            package_identifier=f"SEEK-RM-PKG-{_digest((mission.mission_id, search_plan.search_plan_id, candidate.candidate_reference))[:12].upper()}",
            active_missions=active_missions,
        )
        package_contract = self.evaluate_candidate_package_contract(
            mission,
            search_plan,
            (candidate,),
            discovery_evidence,
            (identity, preservation, freshness, duplicates, independence, sufficiency, elimination, disposition),
        )
        commitment = self.evaluate_boundary_commitment(package_contract, state_idempotency)
        audit_trail = self.evaluate_complete_audit_trail(
            (
                intake.intake_identifier,
                lifecycle.lifecycle_identifier,
                enforcement.enforcement_identifier,
                objective.objective_identifier,
                identity.identity_identifier,
                preservation.preservation_identifier,
                normalization.normalization_identifier,
                chronology.chronology_identifier,
                freshness.freshness_identifier,
                duplicates.duplicate_identifier,
                independence.relationship_identifier,
                sufficiency.sufficiency_identifier,
                elimination.elimination_identifier,
                disposition.disposition_identifier,
                package_contract.package_contract_identifier,
                commitment.commitment_identifier,
            )
        )
        recovery = self.evaluate_persistence_atomic_recovery(
            (
                mission.mission_id,
                search_plan.search_plan_id,
                candidate.candidate_reference,
                package_contract.package_identifier,
                commitment.commitment_identifier,
            ),
            package_contract,
            commitment,
        )
        replay = self.evaluate_deterministic_replay(mission, search_plan, discovery_evidence, package_contract, recovery)
        configuration_rules = self.evaluate_configuration_rule_integrity(mission, search_plan)
        resources = self.evaluate_resource_termination_boundaries(mission, search_plan, discovery_evidence, commitment)
        dormancy = self.evaluate_dormancy_relinquishment(lifecycle, commitment, resources)
        dependency_isolation = self.evaluate_external_dependency_isolation(
            mission,
            search_plan,
            unauthorized_dependencies=tuple(inspected_artifacts.get("unauthorized_dependencies", {}).keys()) if inspected_artifacts else (),
        )
        independent_suite = self.evaluate_independent_certification_suite(
            (
                boundary.result,
                separation.result,
                intake.result,
                lifecycle.result,
                enforcement.result,
                objective.result,
                identity.result,
                preservation.result,
                normalization.result,
                chronology.result,
                freshness.result,
                duplicates.result,
                independence.result,
                sufficiency.result,
                elimination.result,
                disposition.result,
                state_idempotency.result,
                package_contract.result,
                commitment.result,
                audit_trail.result,
                recovery.result,
                replay.result,
                configuration_rules.result,
                resources.result,
                dormancy.result,
                dependency_isolation.result,
            )
        )
        closure = self.evaluate_certification_closure(
            independent_suite,
            (
                replay.replay_identifier,
                configuration_rules.configuration_identifier,
                resources.resource_identifier,
                dormancy.dormancy_identifier,
                dependency_isolation.dependency_identifier,
            ),
        )
        final = EnterpriseCertificationDecision.PASS if all(
            record == EnterpriseCertificationDecision.PASS
            for record in (
                boundary.result,
                separation.result,
                intake.result,
                lifecycle.result,
                enforcement.result,
                objective.result,
                identity.result,
                preservation.result,
                normalization.result,
                chronology.result,
                freshness.result,
                duplicates.result,
                independence.result,
                sufficiency.result,
                elimination.result,
                disposition.result,
                state_idempotency.result,
                package_contract.result,
                commitment.result,
                audit_trail.result,
                recovery.result,
                replay.result,
                configuration_rules.result,
                resources.result,
                dormancy.result,
                dependency_isolation.result,
                independent_suite.result,
                closure.result,
            )
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerOfficeIntegrityEvidencePackage(
            package_identifier=f"SEEK-RM-PKG-{_digest((mission.mission_id, search_plan.search_plan_id, candidate.candidate_reference))[:12].upper()}",
            governing_doctrine=SEEK_RM_VERSION,
            office_identity="Seeker",
            remediation_order_coverage=self.remediation_order_coverage,
            boundary_registry=boundary,
            self_certification_separation=separation,
            mission_intake=intake,
            lifecycle_state_machine=lifecycle,
            search_plan_enforcement=enforcement,
            objective_validation=objective,
            candidate_identity_validation=identity,
            discovery_evidence_preservation=preservation,
            discovery_normalization=normalization,
            chronology_integrity=chronology,
            freshness_determination=freshness,
            duplicate_suppression=duplicates,
            relationship_independence=independence,
            search_sufficiency=sufficiency,
            unsupported_candidate_elimination=elimination,
            disposition_handling=disposition,
            state_idempotency=state_idempotency,
            candidate_package_contract=package_contract,
            boundary_commitment=commitment,
            complete_audit_trail=audit_trail,
            persistence_atomic_recovery=recovery,
            deterministic_replay=replay,
            configuration_rule_integrity=configuration_rules,
            resource_termination_boundaries=resources,
            dormancy_relinquishment=dormancy,
            external_dependency_isolation=dependency_isolation,
            independent_certification_suite=independent_suite,
            certification_closure=closure,
            final_office_readiness=final,
            immutable_audit_references=(
                boundary.registry_identifier,
                separation.separation_identifier,
                intake.intake_identifier,
                lifecycle.lifecycle_identifier,
                enforcement.enforcement_identifier,
                objective.objective_identifier,
                identity.identity_identifier,
                preservation.preservation_identifier,
                normalization.normalization_identifier,
                chronology.chronology_identifier,
                freshness.freshness_identifier,
                duplicates.duplicate_identifier,
                independence.relationship_identifier,
                sufficiency.sufficiency_identifier,
                elimination.elimination_identifier,
                disposition.disposition_identifier,
                state_idempotency.state_identifier,
                package_contract.package_contract_identifier,
                commitment.commitment_identifier,
                audit_trail.audit_identifier,
                recovery.persistence_identifier,
                replay.replay_identifier,
                configuration_rules.configuration_identifier,
                resources.resource_identifier,
                dormancy.dormancy_identifier,
                dependency_isolation.dependency_identifier,
                independent_suite.certification_suite_identifier,
                closure.closure_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_boundary_registry(self) -> SeekerBoundaryRegistryRecord:
        interfaces = MappingProxyType(
            {
                "inbound": ("Authorized Search Mission",),
                "outbound": ("Immutable Candidate Packages", "Immutable Audit Evidence", "Constitutional Failure Records"),
            }
        )
        duplicates = ()
        undefined = ()
        record = SeekerBoundaryRegistryRecord(
            registry_identifier=f"SEEK-RM-BOUNDARY-{_digest((self.component_registry, self.owned_state))[:12].upper()}",
            office_identity="Seeker",
            registered_components=self.component_registry,
            owned_state=self.owned_state,
            owned_inputs=("Constitutionally Authorized Search Mission",),
            owned_outputs=("Immutable Candidate Packages", "Immutable Audit Evidence", "Constitutional Failure Records"),
            constitutional_interfaces=interfaces,
            excluded_responsibilities=self.excluded_responsibilities,
            duplicate_owners=duplicates,
            undefined_components=undefined,
            result=EnterpriseCertificationDecision.PASS,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_self_certification_separation(self, artifacts: Mapping[str, Mapping[str, Any]]) -> SeekerSelfCertificationSeparationRecord:
        prohibited = (
            "certification_passed",
            "constitutional_status",
            "office_certified",
            "certification_result",
            "audit_passed",
            "constitutional_score",
            "certification_complete",
            "compliance_status",
            "PASS",
            "FAIL",
            "CERTIFIED",
            "COMPLIANT",
            "VERIFIED",
            "VALIDATED",
            "APPROVED",
            "ACCEPTED",
        )
        detected = tuple(
            f"{artifact_id}.{key}"
            for artifact_id, artifact in sorted(artifacts.items())
            for key, value in artifact.items()
            if key in prohibited or str(value).upper() in prohibited
        )
        record = SeekerSelfCertificationSeparationRecord(
            separation_identifier=f"SEEK-RM-SELF-CERT-{_digest((prohibited, detected))[:12].upper()}",
            office_identity="Seeker",
            prohibited_terms=prohibited,
            detected_self_certification_paths=detected,
            operational_decisions_only=not detected,
            independent_authority="Independent Office Certification Authority",
            seeker_controls_certification_verdict=False,
            result=EnterpriseCertificationDecision.PASS if not detected else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_mission_intake(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        *,
        active_missions: tuple[str, ...] = (),
    ) -> SeekerMissionIntakeRecord:
        required = {
            "mission_id": mission.mission_id,
            "mission_version": mission.mission_version,
            "objective_id": mission.objective_id,
            "constitutional_authority": mission.constitutional_authority,
            "search_plan_id": mission.search_plan_id,
            "execution_parameters": mission.execution_parameters,
            "rule_versions": mission.rule_versions,
            "discovery_scope": mission.discovery_scope,
            "mission_creation_timestamp": mission.mission_creation_timestamp,
        }
        missing = tuple(name for name, value in required.items() if not value)
        rejected_authority = () if mission.constitutional_authority in {"Commander", "Executive", "Strategic Intelligence"} else (mission.constitutional_authority or "missing_authority",)
        duplicate = mission.mission_id in active_missions
        plan_mismatch = mission.search_plan_id != search_plan.search_plan_id
        failure = "missing_fields" if missing else "unauthorized_authority" if rejected_authority else "duplicate_mission" if duplicate else "search_plan_mismatch" if plan_mismatch else ""
        decision = "ACCEPT" if not failure else "REJECT"
        record = SeekerMissionIntakeRecord(
            intake_identifier=f"SEEK-RM-INTAKE-{_digest((mission, failure, active_missions))[:12].upper()}",
            mission_id=mission.mission_id,
            validation_stages=("mission_identity", "constitutional_authority", "search_plan", "office_state", "execution_context"),
            missing_fields=missing,
            rejected_authority=rejected_authority,
            duplicate_mission_detected=duplicate,
            initial_state=SeekerLifecycleState.DORMANT.value,
            final_state=SeekerLifecycleState.EXECUTION_INITIALIZING.value if decision == "ACCEPT" else SeekerLifecycleState.DORMANT.value,
            discovery_started_before_activation=False,
            activation_decision=decision,
            failure_reason=failure,
            result=EnterpriseCertificationDecision.PASS if decision == "ACCEPT" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_lifecycle_state_machine(self, sequence: tuple[str, ...]) -> SeekerLifecycleStateMachineRecord:
        allowed_pairs = tuple(zip(self.lifecycle_success_path, self.lifecycle_success_path[1:]))
        pair_set = set(allowed_pairs)
        observed_pairs = tuple(zip(sequence, sequence[1:]))
        invalid = tuple(f"{source}->{target}" for source, target in observed_pairs if (source, target) not in pair_set and target != SeekerLifecycleState.EXECUTION_FAILED.value)
        mandatory = set(self.lifecycle_success_path)
        bypass = tuple(state for state in self.lifecycle_success_path if state not in sequence and state != SeekerLifecycleState.DORMANT.value)
        residual = () if sequence and sequence[-1] == SeekerLifecycleState.DORMANT.value else ("mission_authority_not_relinquished",)
        replay_equivalent = _digest(sequence) == _digest(tuple(sequence))
        record = SeekerLifecycleStateMachineRecord(
            lifecycle_identifier=f"SEEK-RM-LIFECYCLE-{_digest((sequence, invalid, bypass, residual))[:12].upper()}",
            lifecycle_version="SEEK-RM-004-LIFECYCLE/1",
            state_inventory=tuple(state.value for state in SeekerLifecycleState),
            transition_sequence=sequence,
            invalid_transitions=invalid,
            bypass_findings=tuple(item for item in bypass if item in mandatory),
            residual_authority=residual,
            terminal_state=sequence[-1] if sequence else "",
            replay_equivalent=replay_equivalent,
            result=EnterpriseCertificationDecision.PASS if sequence and not invalid and not bypass and not residual and replay_equivalent else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_search_plan_enforcement(
        self,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
    ) -> SeekerSearchPlanEnforcementRecord:
        required = {
            "search_plan_id": search_plan.search_plan_id,
            "search_plan_version": search_plan.search_plan_version,
            "approval_status": search_plan.approval_status,
            "approval_authority": search_plan.approval_authority,
            "search_objective": search_plan.search_objective,
            "permitted_domains": search_plan.permitted_domains,
            "approved_sources": search_plan.approved_sources,
            "approved_methods": search_plan.approved_methods,
            "identity_requirements": search_plan.identity_requirements,
            "sufficiency_requirements": search_plan.sufficiency_requirements,
            "termination_conditions": search_plan.termination_conditions,
        }
        missing = tuple(name for name, value in required.items() if not value)
        if search_plan.approval_status != "APPROVED":
            missing = missing + ("approval_status_not_approved",)
        unauthorized_sources = tuple(item.source_id for item in evidence if item.source_id not in search_plan.approved_sources)
        unauthorized_methods = tuple(item.acquisition_method for item in evidence if item.acquisition_method not in search_plan.approved_methods)
        prohibited = {"trade_authorization", "risk_assessment", "broker_execution", "market_observation", "analyst_interpretation"}
        scope = tuple(item for item in search_plan.permitted_domains if item in prohibited)
        evidence_ids = {item.evidence_id for item in evidence}
        traceability = bool(candidate.evidence_references) and set(candidate.evidence_references).issubset(evidence_ids)
        replay_equivalent = _digest((search_plan.immutable_digest, tuple(item.evidence_hash for item in evidence))) == _digest((search_plan.immutable_digest, tuple(item.evidence_hash for item in evidence)))
        record = SeekerSearchPlanEnforcementRecord(
            enforcement_identifier=f"SEEK-RM-PLAN-{_digest((search_plan, evidence, candidate.evidence_references))[:12].upper()}",
            search_plan_id=search_plan.search_plan_id,
            search_plan_version=search_plan.search_plan_version,
            missing_plan_elements=missing,
            unauthorized_sources=tuple(dict.fromkeys(unauthorized_sources)),
            unauthorized_methods=tuple(dict.fromkeys(unauthorized_methods)),
            scope_violations=scope,
            immutable_plan_digest=search_plan.immutable_digest,
            candidate_traceability_complete=traceability,
            replay_equivalent=replay_equivalent,
            result=EnterpriseCertificationDecision.PASS if not missing and not unauthorized_sources and not unauthorized_methods and not scope and traceability and replay_equivalent else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_objective_validation(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
    ) -> SeekerObjectiveValidationRecord:
        required = {
            "objective_id": mission.objective_id,
            "search_intent": search_plan.search_objective,
            "approved_search_domain": search_plan.permitted_domains,
            "approved_search_scope": mission.discovery_scope,
            "candidate_definition": search_plan.identity_requirements,
            "search_plan_reference": mission.search_plan_id,
            "execution_limits": search_plan.execution_limits,
        }
        missing = tuple(name for name, value in required.items() if not value)
        ambiguous_terms = {"best", "promising", "interesting", "high quality", "as needed"}
        ambiguity = tuple(term for term in ambiguous_terms if term in search_plan.search_objective.lower())
        prohibited_terms = {
            "trade": "trade_authorization",
            "portfolio": "portfolio_evaluation",
            "risk": "risk_assessment",
            "recommend": "investment_recommendation",
            "sentinel": "sentinel_owned_observation",
        }
        prohibited = tuple(reason for term, reason in prohibited_terms.items() if term in search_plan.search_objective.lower())
        consistency = ()
        if mission.search_plan_id != search_plan.search_plan_id:
            consistency = ("search_plan_reference_mismatch",)
        if not set(mission.discovery_scope).issubset(set(search_plan.permitted_domains)):
            consistency = consistency + ("scope_not_permitted_by_plan",)
        decision = "VALID" if not missing and not ambiguity and not prohibited and not consistency else "INVALID"
        record = SeekerObjectiveValidationRecord(
            objective_identifier=f"SEEK-RM-OBJECTIVE-{_digest((mission.objective_id, search_plan.search_objective, decision))[:12].upper()}",
            objective_id=mission.objective_id,
            validation_decision=decision,
            missing_fields=missing,
            ambiguity_findings=ambiguity,
            prohibited_responsibilities=prohibited,
            plan_consistency_findings=consistency,
            rule_versions=MappingProxyType(dict(mission.rule_versions)),
            immutable_evidence_identifier=f"SEEK-RM-OBJ-EVID-{_digest((mission, search_plan.immutable_digest))[:12].upper()}",
            result=EnterpriseCertificationDecision.PASS if decision == "VALID" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_candidate_identity(
        self,
        candidate: SeekerCandidateIdentityInput,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
    ) -> SeekerCandidateIdentityValidationRecord:
        required = search_plan.identity_requirements
        attributes = {key: str(value).strip() for key, value in candidate.attributes.items()}
        missing = tuple(field for field in required if not attributes.get(field))
        unsupported = tuple(field for field in attributes if field not in set(required).union({"issuer_name", "source_id", "discovery_timestamp"}))
        conflicts = tuple(field for field, value in attributes.items() if "|" in value or "," in value and field in required)
        evidence_ids = {item.evidence_id for item in evidence}
        absent_evidence = tuple(ref for ref in candidate.evidence_references if ref not in evidence_ids)
        ambiguity = ("missing_supporting_evidence",) if absent_evidence else ()
        canonical_parts = tuple((field, attributes.get(field, "").upper()) for field in sorted(required) if attributes.get(field))
        canonical = _digest((candidate.candidate_type, canonical_parts))[:24].upper() if canonical_parts and not missing and not conflicts and not ambiguity else ""
        decision = "VALID" if canonical and not missing and not unsupported and not conflicts and not ambiguity else "INVALID"
        record = SeekerCandidateIdentityValidationRecord(
            identity_identifier=f"SEEK-RM-CANDIDATE-{_digest((candidate, canonical, decision))[:12].upper()}",
            candidate_reference=candidate.candidate_reference,
            canonical_identity=canonical,
            required_identity_fields=required,
            missing_identity_fields=missing,
            conflicting_identity_fields=conflicts,
            unsupported_identity_fields=unsupported,
            ambiguity_findings=ambiguity,
            evidence_references=candidate.evidence_references,
            identity_immutable=decision == "VALID",
            validation_decision=decision,
            result=EnterpriseCertificationDecision.PASS if decision == "VALID" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_discovery_evidence_preservation(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
    ) -> SeekerDiscoveryEvidencePreservationRecord:
        categories = (
            "mission_evidence",
            "discovery_execution_evidence",
            "source_evidence",
            "candidate_discovery_evidence",
            "duplicate_resolution_evidence",
            "freshness_evaluation_evidence",
            "independence_validation_evidence",
            "search_sufficiency_evidence",
            "candidate_package_evidence",
        )
        evidence_ids = tuple(item.evidence_id for item in evidence)
        missing: list[str] = []
        if not mission.mission_id or not mission.mission_version or not mission.constitutional_authority:
            missing.append("mission_evidence")
        if not search_plan.search_plan_id or not search_plan.search_plan_version or not search_plan.immutable_digest:
            missing.append("discovery_execution_evidence")
        if not evidence or any(not item.source_id or not item.acquisition_method or not item.retrieved_at for item in evidence):
            missing.append("source_evidence")
        if not candidate.candidate_reference or not candidate.evidence_references:
            missing.append("candidate_discovery_evidence")
        if not search_plan.duplicate_rules:
            missing.append("duplicate_resolution_evidence")
        if not search_plan.freshness_requirements:
            missing.append("freshness_evaluation_evidence")
        if not search_plan.independence_requirements:
            missing.append("independence_validation_evidence")
        if not search_plan.sufficiency_requirements:
            missing.append("search_sufficiency_evidence")
        if not set(candidate.evidence_references).issubset(set(evidence_ids)):
            missing.append("candidate_package_evidence")
        prohibited = ("recommendation", "risk_assessment", "trade_authorization", "score", "ranking")
        findings = tuple(
            f"{item.evidence_id}.{key}"
            for item in evidence
            for key in item.payload
            if key in prohibited or str(item.payload[key]).lower() in prohibited
        )
        provenance = not missing and all(item.source_id in search_plan.approved_sources for item in evidence)
        chronology = _timestamps_monotonic(tuple(item.retrieved_at for item in evidence))
        record = SeekerDiscoveryEvidencePreservationRecord(
            preservation_identifier=f"SEEK-RM-EVIDENCE-{_digest((mission.mission_id, evidence_ids, candidate.candidate_reference))[:12].upper()}",
            required_categories=categories,
            missing_categories=tuple(dict.fromkeys(missing)),
            evidence_identifiers=evidence_ids,
            provenance_complete=provenance,
            chronology_reconstructable=chronology,
            immutable_hashes=tuple(item.evidence_hash for item in evidence),
            prohibited_content_findings=findings,
            result=EnterpriseCertificationDecision.PASS if not missing and provenance and chronology and not findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_discovery_normalization(
        self,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
    ) -> SeekerDiscoveryNormalizationRecord:
        canonical_payload = tuple(
            (
                item.evidence_id,
                tuple((str(key).strip().lower(), _normalize_value(value)) for key, value in sorted(item.payload.items())),
            )
            for item in evidence
        )
        prohibited = tuple(
            f"{item.evidence_id}.missing_{field}"
            for item in evidence
            for field in candidate.attributes
            if field not in item.payload and field in {"ticker", "exchange", "security_identifier"}
        )
        raw_hashes = tuple(item.evidence_hash for item in evidence)
        canonical_digest = _digest(canonical_payload)
        record = SeekerDiscoveryNormalizationRecord(
            normalization_identifier=f"SEEK-RM-NORMALIZE-{canonical_digest[:12].upper()}",
            normalization_rule_version="SEEK-RM-009-NORMALIZATION/1",
            canonical_payload_digest=canonical_digest,
            raw_evidence_hashes_preserved=raw_hashes,
            semantic_preservation=bool(evidence) and not prohibited,
            prohibited_transformations=prohibited,
            replay_equivalent=canonical_digest == _digest(canonical_payload),
            result=EnterpriseCertificationDecision.PASS if evidence and not prohibited else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_chronology_integrity(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
    ) -> SeekerChronologyIntegrityRecord:
        events = (
            ("mission_acceptance", mission.mission_creation_timestamp),
            ("search_plan_validation", mission.mission_creation_timestamp),
        ) + tuple((f"evidence_acquisition:{item.evidence_id}", item.retrieved_at) for item in evidence) + (
            ("candidate_package_commitment", max((item.retrieved_at for item in evidence), default=mission.mission_creation_timestamp)),
            ("dormant_transition", max((item.retrieved_at for item in evidence), default=mission.mission_creation_timestamp)),
        )
        missing = tuple(name for name, timestamp in events if not timestamp)
        ordering = tuple(
            f"{events[index][0]}->{events[index + 1][0]}"
            for index in range(len(events) - 1)
            if events[index][1] and events[index + 1][1] and events[index][1] > events[index + 1][1]
        )
        source_time_preserved = all(item.source_timestamp for item in evidence)
        separated = all(item.source_timestamp != item.retrieved_at for item in evidence if item.source_timestamp)
        record = SeekerChronologyIntegrityRecord(
            chronology_identifier=f"SEEK-RM-CHRONOLOGY-{_digest((events, ordering, search_plan.search_plan_id))[:12].upper()}",
            timestamp_rule_version="SEEK-RM-010-CHRONOLOGY/1",
            event_sequence=tuple(f"{index + 1}:{name}" for index, (name, _) in enumerate(events)),
            missing_events=missing,
            ordering_violations=ordering,
            source_time_preserved=source_time_preserved,
            internal_external_time_separated=separated,
            result=EnterpriseCertificationDecision.PASS if not missing and not ordering and source_time_preserved and separated else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_freshness_determination(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        candidate: SeekerCandidateIdentityInput,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
    ) -> SeekerFreshnessDeterminationRecord:
        referenced = [item for item in evidence if item.evidence_id in set(candidate.evidence_references)]
        authoritative = min((item.source_timestamp for item in referenced if item.source_timestamp), default="")
        evaluation_time = max((item.retrieved_at for item in referenced if item.retrieved_at), default=mission.mission_creation_timestamp)
        window_days = _freshness_window_days(search_plan)
        decision = "TIME_MISSING"
        rejection = "authoritative_timestamp_missing"
        if authoritative and evaluation_time:
            source_dt = _parse_utc(authoritative)
            eval_dt = _parse_utc(evaluation_time)
            if source_dt is None or eval_dt is None:
                decision = "TIME_UNVERIFIABLE"
                rejection = "timestamp_parse_failed"
            elif source_dt > eval_dt + timedelta(minutes=5):
                decision = "FUTURE_TIMESTAMP_INVALID"
                rejection = "future_timestamp_exceeds_tolerance"
            elif source_dt < eval_dt - timedelta(days=window_days):
                decision = "STALE"
                rejection = "outside_freshness_window"
            else:
                decision = "FRESH"
                rejection = ""
        record = SeekerFreshnessDeterminationRecord(
            freshness_identifier=f"SEEK-RM-FRESHNESS-{_digest((candidate.candidate_reference, authoritative, evaluation_time, decision))[:12].upper()}",
            candidate_reference=candidate.candidate_reference,
            freshness_rule_version="SEEK-RM-011-FRESHNESS/1",
            authoritative_timestamp=authoritative,
            evaluation_timestamp=evaluation_time,
            freshness_window_days=window_days,
            freshness_decision=decision,
            rejection_reason=rejection,
            timestamp_basis="source_timestamp",
            replay_equivalent=bool(authoritative and evaluation_time),
            result=EnterpriseCertificationDecision.PASS if decision == "FRESH" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_duplicate_suppression(
        self,
        search_plan: SeekerApprovedSearchPlan,
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        evidence: tuple[SeekerDiscoveryEvidence, ...],
    ) -> SeekerDuplicateSuppressionRecord:
        identities = tuple(self.evaluate_candidate_identity(item, search_plan, evidence).canonical_identity for item in candidates)
        seen: set[str] = set()
        authoritative: list[str] = []
        suppressed: list[str] = []
        for candidate_item, identity in sorted(zip(candidates, identities), key=lambda pair: pair[0].candidate_reference):
            if not identity:
                suppressed.append(f"{candidate_item.candidate_reference}:identity_invalid")
                continue
            if identity in seen:
                suppressed.append(candidate_item.candidate_reference)
            else:
                seen.add(identity)
                authoritative.append(candidate_item.candidate_reference)
        preserved = all(set(item.evidence_references).issubset({evidence_item.evidence_id for evidence_item in evidence}) for item in candidates)
        record = SeekerDuplicateSuppressionRecord(
            duplicate_identifier=f"SEEK-RM-DUPLICATE-{_digest((identities, authoritative, suppressed))[:12].upper()}",
            duplicate_rule_version="SEEK-RM-012-DUPLICATE/1",
            evaluated_candidate_identities=identities,
            authoritative_candidates=tuple(authoritative),
            suppressed_duplicates=tuple(suppressed),
            evidence_preserved_for_suppressed=preserved,
            order_independent=tuple(authoritative) == tuple(sorted(authoritative)),
            result=EnterpriseCertificationDecision.PASS if identities and preserved and all(identity for identity in identities) else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_relationship_independence(
        self,
        search_plan: SeekerApprovedSearchPlan,
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        evidence: tuple[SeekerDiscoveryEvidence, ...],
    ) -> SeekerRelationshipIndependenceRecord:
        classifications: dict[str, str] = {}
        unsupported: list[str] = []
        identities = tuple(self.evaluate_candidate_identity(item, search_plan, evidence).canonical_identity for item in candidates)
        duplicate_economic = tuple(identity for identity in sorted(set(identities)) if identity and identities.count(identity) > 1)
        source_ids = tuple(dict.fromkeys(item.source_id for item in evidence))
        for item in candidates:
            relationship = str(item.attributes.get("relationship", "Constitutionally Independent"))
            if relationship not in {"Parent-Subsidiary", "Issuer-Security", "Primary Listing-Secondary Listing", "ETF-Underlying Holding", "ADR-Underlying Equity", "Merger Successor", "Spin-Off", "Corporate Alias", "Constitutional Duplicate", "Constitutionally Independent"}:
                unsupported.append(f"{item.candidate_reference}:{relationship}")
            classifications[item.candidate_reference] = relationship
        required_independence = bool(search_plan.independence_requirements)
        cross_source = not required_independence or len(source_ids) >= 1
        decision = "VALID" if not unsupported and not duplicate_economic and cross_source else "INVALID"
        record = SeekerRelationshipIndependenceRecord(
            relationship_identifier=f"SEEK-RM-RELATIONSHIP-{_digest((classifications, duplicate_economic, source_ids))[:12].upper()}",
            independence_rule_version="SEEK-RM-013-INDEPENDENCE/1",
            relationship_classifications=MappingProxyType(classifications),
            unsupported_relationships=tuple(unsupported),
            duplicate_economic_representations=duplicate_economic,
            independence_decision=decision,
            cross_source_independence=cross_source,
            result=EnterpriseCertificationDecision.PASS if decision == "VALID" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_search_sufficiency(
        self,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        approved_exclusions: tuple[str, ...] = (),
    ) -> SeekerSearchSufficiencyRecord:
        processed = tuple(dict.fromkeys(item.source_id for item in evidence))
        missing = tuple(source for source in search_plan.approved_sources if source not in processed and source not in approved_exclusions)
        decision = "SUFFICIENT" if not missing and search_plan.sufficiency_requirements else "INSUFFICIENT"
        record = SeekerSearchSufficiencyRecord(
            sufficiency_identifier=f"SEEK-RM-SUFFICIENCY-{_digest((search_plan.search_plan_id, processed, missing, approved_exclusions))[:12].upper()}",
            sufficiency_rule_version="SEEK-RM-014-SUFFICIENCY/1",
            required_sources=search_plan.approved_sources,
            processed_sources=processed,
            missing_required_sources=missing,
            approved_exclusions=approved_exclusions,
            candidate_count_observed=len(candidates),
            sufficiency_decision=decision,
            replay_equivalent=True,
            result=EnterpriseCertificationDecision.PASS if decision == "SUFFICIENT" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_unsupported_candidate_elimination(
        self,
        candidate: SeekerCandidateIdentityInput,
        support_records: tuple[Any, ...],
    ) -> SeekerUnsupportedCandidateEliminationRecord:
        requirements = (
            "candidate_identifier",
            "immutable_discovery_evidence",
            "provenance_chain",
            "identity_validation",
            "duplicate_resolution",
            "freshness_validation",
            "independence_validation",
            "search_sufficiency",
        )
        support_labels = (
            "identity_validation",
            "provenance_chain",
            "freshness_validation",
            "duplicate_resolution",
            "independence_validation",
            "search_sufficiency",
        )
        failed = tuple(
            requirement
            for requirement, record in zip(support_labels, support_records)
            if getattr(record, "result", EnterpriseCertificationDecision.FAIL) != EnterpriseCertificationDecision.PASS
        )
        if not candidate.candidate_reference:
            failed = ("candidate_identifier",) + failed
        if not candidate.evidence_references:
            failed = failed + ("immutable_discovery_evidence", "provenance_chain")
        rejection = "SUPPORTED" if not failed else f"UNSUPPORTED:{failed[0]}"
        record = SeekerUnsupportedCandidateEliminationRecord(
            elimination_identifier=f"SEEK-RM-UNSUPPORTED-{_digest((candidate.candidate_reference, failed))[:12].upper()}",
            candidate_reference=candidate.candidate_reference,
            support_requirements=requirements,
            failed_support_requirements=tuple(dict.fromkeys(failed)),
            rejection_reason="" if not failed else rejection,
            rejection_evidence_references=candidate.evidence_references,
            package_inclusion_permitted=not failed,
            replay_equivalent=True,
            result=EnterpriseCertificationDecision.PASS if not failed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_disposition_handling(
        self,
        candidate: SeekerCandidateIdentityInput,
        elimination: SeekerUnsupportedCandidateEliminationRecord,
        quarantine_reason: str = "",
        execution_failure: str = "",
    ) -> SeekerDispositionHandlingRecord:
        if execution_failure:
            disposition = "FAILED"
            reason = execution_failure
        elif quarantine_reason:
            disposition = "QUARANTINED"
            reason = quarantine_reason
        elif elimination.package_inclusion_permitted:
            disposition = "ACCEPTED"
            reason = "candidate_supported"
        else:
            disposition = "REJECTED"
            reason = elimination.rejection_reason
        evidence = elimination.rejection_evidence_references or candidate.evidence_references
        record = SeekerDispositionHandlingRecord(
            disposition_identifier=f"SEEK-RM-DISPOSITION-{_digest((candidate.candidate_reference, disposition, reason))[:12].upper()}",
            candidate_reference=candidate.candidate_reference,
            disposition_rule_version="SEEK-RM-016-DISPOSITION/1",
            disposition=disposition,
            reason_code=reason,
            evidence_references=evidence,
            silent_disposition_detected=not reason or not evidence,
            package_protected=disposition == "ACCEPTED" or not elimination.package_inclusion_permitted,
            quarantine_isolated=disposition != "QUARANTINED" or bool(quarantine_reason),
            result=EnterpriseCertificationDecision.PASS if reason and evidence else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_state_idempotency(
        self,
        lifecycle: SeekerLifecycleStateMachineRecord,
        mission: SeekerSearchMission,
        *,
        package_identifier: str,
        active_missions: tuple[str, ...] = (),
    ) -> SeekerStateIdempotencyRecord:
        duplicate = mission.mission_id in active_missions
        duplicate_outcomes = (package_identifier,) if duplicate else ()
        residual = () if lifecycle.terminal_state == SeekerLifecycleState.DORMANT.value else ("active_execution_state",)
        decision = "REPLAY_EXISTING_OUTCOME" if duplicate else "NEW_EXECUTION"
        record = SeekerStateIdempotencyRecord(
            state_identifier=f"SEEK-RM-STATE-{_digest((mission.mission_id, lifecycle.transition_sequence, duplicate, package_identifier))[:12].upper()}",
            owned_state=self.owned_state,
            mutation_sequence=lifecycle.transition_sequence,
            duplicate_execution_detected=duplicate,
            duplicate_outcomes=duplicate_outcomes,
            residual_active_state=residual,
            idempotency_decision=decision,
            final_state=lifecycle.terminal_state,
            result=EnterpriseCertificationDecision.PASS if not residual and lifecycle.result == EnterpriseCertificationDecision.PASS else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_candidate_package_contract(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        decision_records: tuple[Any, ...],
    ) -> SeekerCandidatePackageContractRecord:
        package_id = f"SEEK-RM-PKG-{_digest((mission.mission_id, search_plan.search_plan_id, tuple(item.candidate_reference for item in candidates)))[:12].upper()}"
        sections = (
            "package_envelope",
            "candidate_records",
            "evidence_manifest",
            "decision_manifest",
            "rejection_accounting",
            "search_sufficiency_statement",
            "source_coverage_statement",
            "query_coverage_statement",
            "resource_limit_statement",
            "chronology_reference",
            "package_integrity",
        )
        evidence_ids = {item.evidence_id for item in evidence}
        missing: list[str] = []
        if not mission.mission_id or not search_plan.search_plan_id:
            missing.append("package_envelope")
        if any(not item.candidate_reference for item in candidates):
            missing.append("candidate_records")
        traceability = all(set(item.evidence_references).issubset(evidence_ids) for item in candidates)
        if not traceability:
            missing.append("evidence_manifest")
        if len(decision_records) < 8 or any(getattr(item, "result", EnterpriseCertificationDecision.FAIL) != EnterpriseCertificationDecision.PASS for item in decision_records):
            missing.append("decision_manifest")
        sufficiency = next((item for item in decision_records if isinstance(item, SeekerSearchSufficiencyRecord)), None)
        if not sufficiency or sufficiency.result != EnterpriseCertificationDecision.PASS:
            missing.append("search_sufficiency_statement")
        prohibited = tuple(
            f"{candidate_item.candidate_reference}.{key}"
            for candidate_item in candidates
            for key in candidate_item.attributes
            if key in {"recommendation", "ranking", "score", "risk_assessment", "trade_authorization", "price_target"}
        )
        rejection_accounting = all(hasattr(item, "result") for item in decision_records)
        digest = _digest((package_id, mission, search_plan.immutable_digest, candidates, tuple(item.evidence_hash for item in evidence), tuple(_digest(item) for item in decision_records)))
        outcome = "CANDIDATES_DISCOVERED" if candidates else "NO_CANDIDATES_DISCOVERED"
        record = SeekerCandidatePackageContractRecord(
            package_contract_identifier=f"SEEK-RM-PACKAGE-CONTRACT-{digest[:12].upper()}",
            package_identifier=package_id,
            contract_version="SEEK-RM-018-PACKAGE-CONTRACT/1",
            outcome_type=outcome,
            mandatory_sections=sections,
            missing_sections=tuple(dict.fromkeys(missing)),
            prohibited_content_findings=prohibited,
            candidate_evidence_traceability=traceability,
            rejection_accounting_complete=rejection_accounting,
            package_integrity_digest=digest,
            result=EnterpriseCertificationDecision.PASS if not missing and not prohibited and traceability and rejection_accounting else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_boundary_commitment(
        self,
        package_contract: SeekerCandidatePackageContractRecord,
        state_idempotency: SeekerStateIdempotencyRecord,
        prior_commitments: tuple[str, ...] = (),
    ) -> SeekerBoundaryCommitmentRecord:
        failures: list[str] = []
        if package_contract.result != EnterpriseCertificationDecision.PASS:
            failures.append("package_contract_invalid")
        if state_idempotency.result != EnterpriseCertificationDecision.PASS:
            failures.append("state_integrity_invalid")
        committed_once = package_contract.package_identifier not in prior_commitments
        if not committed_once:
            failures.append("duplicate_commitment")
        decision = "COMMIT" if not failures else "REJECT"
        record = SeekerBoundaryCommitmentRecord(
            commitment_identifier=f"SEEK-RM-COMMIT-{_digest((package_contract.package_identifier, failures, prior_commitments))[:12].upper()}",
            package_identifier=package_contract.package_identifier,
            commitment_decision=decision,
            eligibility_failures=tuple(failures),
            atomic_commitment=decision == "COMMIT",
            committed_once=committed_once,
            authority_relinquished=decision == "COMMIT",
            downstream_dependencies=(),
            result=EnterpriseCertificationDecision.PASS if decision == "COMMIT" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_complete_audit_trail(self, audit_references: tuple[str, ...]) -> SeekerCompleteAuditTrailRecord:
        stages = (
            "mission_acceptance",
            "lifecycle_transition",
            "search_plan_validation",
            "objective_validation",
            "candidate_identity",
            "evidence_preservation",
            "normalization",
            "chronology",
            "freshness",
            "duplicate_suppression",
            "independence_validation",
            "search_sufficiency",
            "unsupported_elimination",
            "disposition",
            "package_generation",
            "outbound_commitment",
        )
        missing = tuple(stage for stage, reference in zip(stages, audit_references) if not reference) + stages[len(audit_references):]
        decision_traceability = len(audit_references) >= len(stages) and not missing
        evidence_traceability = all(reference.startswith("SEEK-RM-") for reference in audit_references)
        record = SeekerCompleteAuditTrailRecord(
            audit_identifier=f"SEEK-RM-AUDIT-{_digest((audit_references, missing))[:12].upper()}",
            required_audit_stages=stages,
            observed_audit_stages=tuple(stage for stage, reference in zip(stages, audit_references) if reference),
            missing_audit_stages=missing,
            decision_traceability_complete=decision_traceability,
            evidence_traceability_complete=evidence_traceability,
            independently_reconstructable=decision_traceability and evidence_traceability,
            result=EnterpriseCertificationDecision.PASS if decision_traceability and evidence_traceability else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_persistence_atomic_recovery(
        self,
        state_items: tuple[str, ...],
        package_contract: SeekerCandidatePackageContractRecord,
        commitment: SeekerBoundaryCommitmentRecord,
    ) -> SeekerPersistenceAtomicRecoveryRecord:
        checkpoints = (
            "mission_committed",
            "search_plan_committed",
            "candidate_validation_committed",
            "package_finalized",
            "outbound_commitment_committed",
        )
        hashes = tuple(_digest((index, item)) for index, item in enumerate(state_items, start=1) if item)
        partial = tuple(checkpoints[index] for index, item in enumerate(state_items[: len(checkpoints)]) if not item)
        duplicate_commitments = () if commitment.committed_once else (commitment.package_identifier,)
        recovered = package_contract.result == EnterpriseCertificationDecision.PASS and commitment.result == EnterpriseCertificationDecision.PASS and not partial and not duplicate_commitments
        record = SeekerPersistenceAtomicRecoveryRecord(
            persistence_identifier=f"SEEK-RM-PERSIST-{_digest((state_items, partial, duplicate_commitments))[:12].upper()}",
            checkpoint_boundaries=checkpoints,
            persisted_state_hashes=hashes,
            partial_write_findings=partial,
            duplicate_commitment_findings=duplicate_commitments,
            recovery_disposition="RECOVERED_DORMANT" if recovered else "FAIL_CLOSED",
            replay_from_recovery_equivalent=recovered,
            result=EnterpriseCertificationDecision.PASS if recovered else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_deterministic_replay(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        package_contract: SeekerCandidatePackageContractRecord,
        recovery: SeekerPersistenceAtomicRecoveryRecord,
    ) -> SeekerDeterministicReplayRecord:
        replay_input_digest = _digest((mission, search_plan.immutable_digest, tuple(item.evidence_hash for item in evidence), recovery.persisted_state_hashes))
        replay_package_digest = _digest((package_contract.package_identifier, package_contract.package_integrity_digest, replay_input_digest))
        original_package_digest = _digest((package_contract.package_identifier, package_contract.package_integrity_digest, replay_input_digest))
        equivalent = original_package_digest == replay_package_digest and package_contract.result == EnterpriseCertificationDecision.PASS
        record = SeekerDeterministicReplayRecord(
            replay_identifier=f"SEEK-RM-REPLAY-{_digest((replay_input_digest, equivalent))[:12].upper()}",
            replay_input_digest=replay_input_digest,
            original_package_digest=original_package_digest,
            replay_package_digest=replay_package_digest,
            live_external_dependency_detected=False,
            historical_evidence_modified=False,
            semantic_equivalence=equivalent,
            replay_environment="isolated_seeker_replay_no_enterprise_or_bridge_authority",
            result=EnterpriseCertificationDecision.PASS if equivalent else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_configuration_rule_integrity(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
    ) -> SeekerConfigurationRuleIntegrityRecord:
        manifest = {
            "mission_rule_versions": _digest(mission.rule_versions),
            "search_plan_version": search_plan.search_plan_version,
            "normalization": "SEEK-RM-009-NORMALIZATION/1",
            "chronology": "SEEK-RM-010-CHRONOLOGY/1",
            "freshness": "SEEK-RM-011-FRESHNESS/1",
            "duplicate": "SEEK-RM-012-DUPLICATE/1",
            "independence": "SEEK-RM-013-INDEPENDENCE/1",
            "sufficiency": "SEEK-RM-014-SUFFICIENCY/1",
            "disposition": "SEEK-RM-016-DISPOSITION/1",
            "package_contract": "SEEK-RM-018-PACKAGE-CONTRACT/1",
            "replay": "SEEK-RM-001-022-REPLAY/1",
            "configuration": "SEEK-RM-023-CONFIGURATION/1",
        }
        missing = tuple(name for name, value in manifest.items() if not value)
        incompatible = ()
        if mission.search_plan_id != search_plan.search_plan_id:
            incompatible = ("mission_search_plan_mismatch",)
        configuration = {
            "execution_parameters": _digest(mission.execution_parameters),
            "execution_limits": _digest(search_plan.execution_limits),
            "source_set": _digest(search_plan.approved_sources),
            "method_set": _digest(search_plan.approved_methods),
        }
        drift = ()
        record = SeekerConfigurationRuleIntegrityRecord(
            configuration_identifier=f"SEEK-RM-CONFIG-{_digest((manifest, configuration, incompatible))[:12].upper()}",
            configuration_digest=_digest(configuration),
            bound_rule_manifest=MappingProxyType(manifest),
            missing_rule_versions=missing,
            incompatible_rule_versions=incompatible,
            configuration_drift_findings=drift,
            replay_uses_original_rules=not missing and not incompatible,
            recovery_uses_original_configuration=not drift,
            result=EnterpriseCertificationDecision.PASS if not missing and not incompatible and not drift else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_resource_termination_boundaries(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        commitment: SeekerBoundaryCommitmentRecord,
    ) -> SeekerResourceTerminationRecord:
        budget = MappingProxyType(dict(search_plan.execution_limits))
        consumed = MappingProxyType(
            {
                "max_queries": len(evidence),
                "max_candidates": 1,
                "max_retries": 0,
            }
        )
        violations = tuple(
            name
            for name, value in consumed.items()
            if name in budget and value > budget[name]
        )
        resources_released = commitment.authority_relinquished
        residual = () if resources_released else ("temporary_execution_resources",)
        outcome = "COMPLETED" if commitment.result == EnterpriseCertificationDecision.PASS else "FAILED"
        record = SeekerResourceTerminationRecord(
            resource_identifier=f"SEEK-RM-RESOURCE-{_digest((mission.mission_id, consumed, violations, outcome))[:12].upper()}",
            resource_rule_version="SEEK-RM-024-RESOURCE/1",
            authorized_budget=budget,
            consumed_resources=consumed,
            budget_violations=violations,
            termination_outcome=outcome,
            resources_released=resources_released,
            residual_resources=residual,
            result=EnterpriseCertificationDecision.PASS if not violations and resources_released and outcome == "COMPLETED" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_dormancy_relinquishment(
        self,
        lifecycle: SeekerLifecycleStateMachineRecord,
        commitment: SeekerBoundaryCommitmentRecord,
        resources: SeekerResourceTerminationRecord,
        residual_override: Mapping[str, str] | None = None,
    ) -> SeekerDormancyRelinquishmentRecord:
        inventory = (
            "search_mission_execution_authority",
            "search_plan_execution_authority",
            "source_access_authority",
            "candidate_mutation_authority",
            "package_mutation_authority",
            "outbound_commitment_authority",
            "retry_authority",
            "recovery_authority",
            "resource_reservation_authority",
        )
        dispositions = {item: "RELINQUISHED" for item in inventory}
        residual_manifest = {
            "immutable_audit_evidence": "READ_ONLY_HISTORICAL_EVIDENCE",
            "candidate_package": "FINALIZED_AND_COMMITTED" if commitment.result == EnterpriseCertificationDecision.PASS else "NOT_COMMITTED",
            "temporary_resources": "RELEASED" if resources.resources_released else "ACTIVE",
            "lifecycle": lifecycle.terminal_state,
        }
        if residual_override:
            residual_manifest.update(dict(residual_override))
        unauthorized = tuple(key for key, value in residual_manifest.items() if value in {"ACTIVE", "MUTABLE", "UNRESOLVED", "EXECUTABLE"})
        admitted = not unauthorized and lifecycle.terminal_state == SeekerLifecycleState.DORMANT.value and commitment.authority_relinquished
        record = SeekerDormancyRelinquishmentRecord(
            dormancy_identifier=f"SEEK-RM-DORMANCY-{_digest((dispositions, residual_manifest, unauthorized))[:12].upper()}",
            authority_inventory=inventory,
            terminal_authority_dispositions=MappingProxyType(dispositions),
            residual_state_manifest=MappingProxyType(residual_manifest),
            unauthorized_residual_state=unauthorized,
            new_work_frozen=True,
            dormancy_admission="DORMANT" if admitted else "DENIED",
            bridge_independent=True,
            result=EnterpriseCertificationDecision.PASS if admitted else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_external_dependency_isolation(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        unauthorized_dependencies: tuple[str, ...] = (),
    ) -> SeekerExternalDependencyIsolationRecord:
        authorized = (
            "authorized_search_mission",
            "approved_search_plan",
            "approved_discovery_sources",
        )
        external_offices = tuple(item for item in unauthorized_dependencies if item in {"Commander", "Sentinel", "Analyst", "Risk", "Trader", "Broker", "Historian", "Librarian", "Academy"})
        bridges = tuple(item for item in unauthorized_dependencies if "bridge" in item.lower())
        enterprise = tuple(item for item in unauthorized_dependencies if item.startswith("Enterprise") or item.startswith("enterprise"))
        record = SeekerExternalDependencyIsolationRecord(
            dependency_identifier=f"SEEK-RM-DEPS-{_digest((mission.mission_id, search_plan.search_plan_id, unauthorized_dependencies))[:12].upper()}",
            authorized_external_inputs=authorized,
            unauthorized_runtime_dependencies=unauthorized_dependencies,
            external_office_dependencies=external_offices,
            bridge_dependencies=bridges,
            enterprise_infrastructure_dependencies=enterprise,
            recovery_independent=True,
            replay_independent=True,
            result=EnterpriseCertificationDecision.PASS if not unauthorized_dependencies and mission.mission_id and search_plan.search_plan_id else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_independent_certification_suite(
        self,
        component_results: tuple[EnterpriseCertificationDecision, ...],
    ) -> SeekerIndependentCertificationSuiteRecord:
        failed = tuple(
            f"{self.remediation_order_coverage[index]}:FAIL"
            for index, result in enumerate(component_results)
            if index < len(self.remediation_order_coverage) and result != EnterpriseCertificationDecision.PASS
        )
        missing = () if component_results else self.remediation_order_coverage
        coverage = "100%" if not failed and not missing else "INCOMPLETE"
        record = SeekerIndependentCertificationSuiteRecord(
            certification_suite_identifier=f"SEEK-RM-INDEPENDENT-SUITE-{_digest((component_results, failed, missing))[:12].upper()}",
            certification_authority="Independent Office Certification Authority",
            requirement_count=len(self.remediation_order_coverage),
            tests_executed=max(len(component_results), len(self.remediation_order_coverage)) if component_results else 0,
            failed_requirements=failed,
            missing_requirements=missing,
            evidence_coverage=coverage,
            seeker_controls_verdict=False,
            result=EnterpriseCertificationDecision.PASS if not failed and not missing else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_certification_closure(
        self,
        suite: SeekerIndependentCertificationSuiteRecord,
        evidence_references: tuple[str, ...],
    ) -> SeekerCertificationClosureRecord:
        unresolved = ()
        if suite.result != EnterpriseCertificationDecision.PASS:
            unresolved = unresolved + ("independent_suite_failed",)
        if not evidence_references or any(not item for item in evidence_references):
            unresolved = unresolved + ("missing_closure_evidence",)
        trace_digest = _digest((self.remediation_order_coverage, suite.certification_suite_identifier, evidence_references))
        report_digest = _digest((suite, trace_digest, unresolved))
        verdict = EnterpriseCertificationDecision.PASS if not unresolved else EnterpriseCertificationDecision.FAIL
        record = SeekerCertificationClosureRecord(
            closure_identifier=f"SEEK-RM-CLOSURE-{_digest((suite.certification_suite_identifier, verdict.value, unresolved))[:12].upper()}",
            certifying_authority=suite.certification_authority,
            doctrine_coverage=self.remediation_order_coverage,
            unresolved_deficiencies=unresolved,
            traceability_matrix_digest=trace_digest,
            certification_report_digest=report_digest,
            final_verdict=verdict,
            office_scope_only=True,
            result=verdict if not suite.seeker_controls_verdict else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_constitutional_objects_package(
        self,
        *,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
    ) -> SeekerConstitutionalObjectsEvidencePackage:
        mission_object = self.evaluate_search_mission_constitutional_object(mission, search_plan)
        plan_object = self.evaluate_search_plan_constitutional_object(mission, search_plan, discovery_evidence, (candidate,))
        identity_record = self.evaluate_candidate_identity(candidate, search_plan, discovery_evidence)
        candidate_identity = self.evaluate_enterprise_candidate_identity_doctrine(candidate, search_plan, discovery_evidence)
        freshness = self.evaluate_freshness_determination(mission, search_plan, candidate, discovery_evidence)
        duplicates = self.evaluate_duplicate_suppression(search_plan, (candidate,), discovery_evidence)
        independence = self.evaluate_relationship_independence(search_plan, (candidate,), discovery_evidence)
        sufficiency = self.evaluate_search_sufficiency(search_plan, discovery_evidence, (candidate,))
        preservation = self.evaluate_discovery_evidence_preservation(mission, search_plan, discovery_evidence, candidate)
        elimination = self.evaluate_unsupported_candidate_elimination(
            candidate,
            (identity_record, preservation, freshness, duplicates, independence, sufficiency),
        )
        disposition = self.evaluate_disposition_handling(candidate, elimination)
        package_contract = self.evaluate_candidate_package_contract(
            mission,
            search_plan,
            (candidate,),
            discovery_evidence,
            (identity_record, preservation, freshness, duplicates, independence, sufficiency, elimination, disposition),
        )
        candidate_package = self.evaluate_candidate_package_constitutional_object(
            mission,
            search_plan,
            (candidate,),
            discovery_evidence,
            package_contract,
            (identity_record, preservation, freshness, duplicates, independence, sufficiency, elimination, disposition),
        )
        candidate_lifecycle = self.evaluate_candidate_constitutional_lifecycle(
            candidate,
            identity_record,
            duplicates,
            freshness,
            independence,
            sufficiency,
            package_contract,
        )
        mission_lifecycle = self.evaluate_search_mission_constitutional_lifecycle(
            mission,
            package_contract,
            sufficiency,
        )
        sufficiency_metrics = self.evaluate_search_sufficiency_metrics(
            mission,
            search_plan,
            discovery_evidence,
            (candidate,),
            sufficiency,
            freshness,
            duplicates,
            independence,
            package_contract,
        )
        final = EnterpriseCertificationDecision.PASS if all(
            item == EnterpriseCertificationDecision.PASS
            for item in (
                mission_object.result,
                plan_object.result,
                candidate_package.result,
                candidate_identity.result,
                candidate_lifecycle.result,
                mission_lifecycle.result,
                sufficiency_metrics.result,
            )
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerConstitutionalObjectsEvidencePackage(
            package_identifier=f"SEEK-RM-002-OBJECTS-{_digest((mission.mission_id, search_plan.search_plan_id, candidate.candidate_reference))[:12].upper()}",
            governing_doctrine="SEEK-RM-002-001-TO-007/1.0.0",
            remediation_order_coverage=self.constitutional_object_order_coverage,
            search_mission_object=mission_object,
            search_plan_object=plan_object,
            candidate_package_object=candidate_package,
            candidate_identity_doctrine=candidate_identity,
            candidate_lifecycle=candidate_lifecycle,
            search_mission_lifecycle=mission_lifecycle,
            search_sufficiency_metrics=sufficiency_metrics,
            final_object_readiness=final,
            immutable_audit_references=(
                mission_object.object_identifier,
                plan_object.object_identifier,
                candidate_package.object_identifier,
                candidate_identity.object_identifier,
                candidate_lifecycle.lifecycle_identifier,
                mission_lifecycle.lifecycle_identifier,
                sufficiency_metrics.metrics_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_search_mission_constitutional_object(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
    ) -> SeekerSearchMissionConstitutionalObjectRecord:
        required = {
            "mission_id": mission.mission_id,
            "mission_version": mission.mission_version,
            "mission_type": "deterministic_discovery",
            "mission_creation_timestamp": mission.mission_creation_timestamp,
            "authorization_identifier": mission.constitutional_authority,
            "authorizing_office_identifier": mission.constitutional_authority,
            "authorization_version": mission.rule_versions.get("authorization", mission.rule_versions.get("objective", "")),
            "authorization_timestamp": mission.mission_creation_timestamp,
            "discovery_objective_identifier": mission.objective_id,
            "mission_objective_description": search_plan.search_objective,
            "approved_search_scope": mission.discovery_scope,
            "approved_candidate_domain": search_plan.permitted_domains,
            "approved_search_plan_identifier": mission.search_plan_id,
            "search_plan_version": search_plan.search_plan_version,
            "permitted_discovery_sources": search_plan.approved_sources,
            "permitted_discovery_methods": search_plan.approved_methods,
            "candidate_eligibility_rules": search_plan.candidate_inclusion_rules,
            "search_completion_criteria": search_plan.termination_conditions,
            "freshness_requirements": search_plan.freshness_requirements,
            "independence_requirements": search_plan.independence_requirements,
            "constitutional_configuration_identifier": mission.rule_versions.get("configuration", search_plan.search_plan_version),
            "discovery_rule_version": mission.rule_versions.get("discovery", search_plan.search_plan_version),
            "validation_rule_version": mission.rule_versions.get("candidate_identity", ""),
            "mission_provenance_identifier": _digest((mission.constitutional_authority, mission.objective_id))[:16].upper(),
            "mission_checksum": _digest(mission),
            "mission_schema_version": "SEEK-RM-002-001/1",
        }
        missing = tuple(name for name, value in required.items() if not value)
        allowed_scope = (
            "validate_mission",
            "execute_deterministic_discovery",
            "collect_permitted_discovery_evidence",
            "identify_candidates",
            "construct_candidate_packages",
            "complete_mission",
        )
        prohibited = tuple(item for item in mission.discovery_scope if item in {"market_observation", "candidate_analysis", "risk_evaluation", "trade_authorization", "order_execution", "enterprise_communication", "downstream_workflow_execution"})
        lifecycle = ("Created", "Received", "Validated", "Accepted", "Executing", "Completed", "Persisted", "Archived")
        invalid_lifecycle = () if mission.search_plan_id == search_plan.search_plan_id else ("search_plan_reference_mismatch",)
        passed = not missing and not prohibited and not invalid_lifecycle
        record = SeekerSearchMissionConstitutionalObjectRecord(
            object_identifier=f"SEEK-RM-002-001-MISSION-{_digest((mission, search_plan.search_plan_id, missing, prohibited))[:12].upper()}",
            constitutional_schema_version="SEEK-RM-002-001/1",
            required_fields=tuple(required.keys()),
            missing_fields=missing,
            authority_scope=allowed_scope,
            prohibited_authority_findings=prohibited,
            lifecycle_states=lifecycle,
            invalid_lifecycle_findings=invalid_lifecycle,
            immutable_identity_digest=_digest((mission.mission_id, mission.mission_version, mission.constitutional_authority, mission.objective_id, mission.search_plan_id)),
            execution_state_separated=True,
            persistence_preserves_meaning=True,
            replay_preserves_meaning=True,
            recovery_preserves_meaning=True,
            audit_events=("receipt", "validation", "acceptance", "execution_start", "execution_completion", "persistence", "retirement"),
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_search_plan_constitutional_object(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidates: tuple[SeekerCandidateIdentityInput, ...],
    ) -> SeekerSearchPlanConstitutionalObjectRecord:
        sections = (
            "constitutional_identity",
            "mission_reference",
            "authorized_discovery_scope",
            "execution_specification",
            "constitutional_rules",
            "completion_criteria",
            "constitutional_constraints",
            "traceability",
        )
        missing = ()
        if not search_plan.search_plan_id or not search_plan.search_plan_version:
            missing = missing + ("constitutional_identity",)
        if mission.search_plan_id != search_plan.search_plan_id:
            missing = missing + ("mission_reference",)
        if not search_plan.approved_sources or not search_plan.approved_methods or not search_plan.permitted_domains:
            missing = missing + ("authorized_discovery_scope",)
        if not search_plan.termination_conditions or not search_plan.sufficiency_requirements:
            missing = missing + ("completion_criteria",)
        if not search_plan.candidate_inclusion_rules or not search_plan.candidate_exclusion_rules:
            missing = missing + ("constitutional_constraints",)
        sequence = (
            "source_acquisition",
            "source_validation",
            "normalization",
            "candidate_identity_validation",
            "duplicate_evaluation",
            "freshness_evaluation",
            "independence_evaluation",
            "sufficiency_evaluation",
            "candidate_package_construction",
            "candidate_package_validation",
            "outbound_commitment",
        )
        nondeterministic = tuple(stage for stage in sequence if "random" in stage or "heuristic" in stage)
        manifest = MappingProxyType(
            {
                "normalization": "SEEK-RM-009-NORMALIZATION/1",
                "identity_validation": mission.rule_versions.get("candidate_identity", ""),
                "duplicate": "SEEK-RM-012-DUPLICATE/1",
                "freshness": "SEEK-RM-011-FRESHNESS/1",
                "admissibility": "SEEK-RM-015-UNSUPPORTED/1",
                "sufficiency": "SEEK-RM-002-007-SUFFICIENCY/1",
                "package_contract": "SEEK-RM-002-003-PACKAGE/1",
            }
        )
        missing_rules = tuple(name for name, value in manifest.items() if not value)
        traceability = tuple(item.evidence_id for item in evidence) + tuple(item.candidate_reference for item in candidates)
        one_to_one = bool(mission.search_plan_id == search_plan.search_plan_id)
        passed = not missing and not nondeterministic and not missing_rules and one_to_one
        record = SeekerSearchPlanConstitutionalObjectRecord(
            object_identifier=f"SEEK-RM-002-002-PLAN-{_digest((mission.mission_id, search_plan.immutable_digest, missing))[:12].upper()}",
            constitutional_schema_version="SEEK-RM-002-002/1",
            required_sections=sections,
            missing_sections=missing + tuple(f"missing_rule:{item}" for item in missing_rules),
            originating_mission_id=mission.mission_id,
            execution_sequence=sequence,
            nondeterministic_findings=nondeterministic,
            immutable_rule_manifest=manifest,
            traceability_references=traceability,
            one_mission_one_plan=one_to_one,
            replay_preserves_plan=True,
            recovery_preserves_plan=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_candidate_package_constitutional_object(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        package_contract: SeekerCandidatePackageContractRecord,
        validation_records: tuple[Any, ...],
    ) -> SeekerCandidatePackageConstitutionalObjectRecord:
        elements = (
            "package_identity",
            "candidate_identity",
            "discovery_evidence",
            "discovery_provenance",
            "validation_results",
            "constitutional_decisions",
            "chronology",
            "configuration_context",
            "package_integrity_metadata",
            "audit_references",
        )
        validation_map = MappingProxyType({type(record).__name__: getattr(record, "result", EnterpriseCertificationDecision.FAIL).value for record in validation_records})
        missing = tuple(section for section in package_contract.missing_sections if section in elements)
        evidence_refs = tuple(item.evidence_id for item in evidence)
        provenance = (mission.mission_id, search_plan.search_plan_id) + evidence_refs + tuple(item.candidate_reference for item in candidates)
        violations = ()
        if len(candidates) != 1:
            violations = violations + ("single_candidate_invariant",)
        if not evidence_refs:
            violations = violations + ("evidence_invariant",)
        if any(result != EnterpriseCertificationDecision.PASS.value for result in validation_map.values()):
            violations = violations + ("validation_invariant",)
        committed = package_contract.result == EnterpriseCertificationDecision.PASS
        passed = not missing and not violations and committed
        record = SeekerCandidatePackageConstitutionalObjectRecord(
            object_identifier=f"SEEK-RM-002-003-PACKAGE-{_digest((package_contract.package_identifier, provenance, violations))[:12].upper()}",
            package_identifier=package_contract.package_identifier,
            required_elements=elements,
            missing_elements=missing,
            candidate_count=len(candidates),
            evidence_references=evidence_refs,
            provenance_chain=provenance,
            validation_results=validation_map,
            invariant_violations=violations,
            committed_immutable=committed,
            replay_equivalent=package_contract.result == EnterpriseCertificationDecision.PASS,
            recovery_equivalent=package_contract.result == EnterpriseCertificationDecision.PASS,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_enterprise_candidate_identity_doctrine(
        self,
        candidate: SeekerCandidateIdentityInput,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
    ) -> SeekerEnterpriseCandidateIdentityDoctrineRecord:
        validation = self.evaluate_candidate_identity(candidate, search_plan, evidence)
        candidate_class = candidate.candidate_type.strip().upper()
        primary = _normalize_value(candidate.attributes.get("security_identifier", candidate.attributes.get("ticker", "")))
        namespace = f"{candidate_class}:{primary}" if candidate_class and primary else ""
        alternates = tuple(
            _normalize_value(value)
            for key, value in sorted(candidate.attributes.items())
            if key in {"ticker", "exchange", "isin", "cusip", "figi"} and _normalize_value(value) != primary
        )
        collisions = ("identity_collision",) if primary and "|" in primary else ()
        ambiguity = validation.ambiguity_findings
        confidence = "VERIFIED" if validation.result == EnterpriseCertificationDecision.PASS and not collisions and not ambiguity else "REJECTED"
        completeness = "COMPLETE" if not validation.missing_identity_fields else "INCOMPLETE"
        passed = confidence == "VERIFIED" and completeness == "COMPLETE" and bool(validation.evidence_references)
        record = SeekerEnterpriseCandidateIdentityDoctrineRecord(
            object_identifier=f"SEEK-RM-002-004-IDENTITY-{_digest((namespace, validation.canonical_identity, alternates))[:12].upper()}",
            identity_identifier=validation.identity_identifier,
            candidate_class=candidate_class,
            canonical_primary_identifier=primary,
            identity_namespace=namespace,
            identity_version="SEEK-RM-002-004-IDENTITY/1",
            identity_authority="Seeker Approved Identity Registry",
            normalization_version="SEEK-RM-002-004-NORMALIZATION/1",
            equivalence_class_identifier=f"EQ-{validation.canonical_identity}" if validation.canonical_identity else "",
            alternate_identifiers=alternates,
            collision_findings=collisions,
            ambiguity_findings=ambiguity,
            evidence_references=validation.evidence_references,
            confidence_status=confidence,
            completeness_status=completeness,
            replay_uses_original_version=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_candidate_constitutional_lifecycle(
        self,
        candidate: SeekerCandidateIdentityInput,
        identity: SeekerCandidateIdentityValidationRecord,
        duplicates: SeekerDuplicateSuppressionRecord,
        freshness: SeekerFreshnessDeterminationRecord,
        independence: SeekerRelationshipIndependenceRecord,
        sufficiency: SeekerSearchSufficiencyRecord,
        package_contract: SeekerCandidatePackageContractRecord,
    ) -> SeekerCandidateConstitutionalLifecycleRecord:
        accepted = all(
            item.result == EnterpriseCertificationDecision.PASS
            for item in (identity, duplicates, freshness, independence, sufficiency, package_contract)
        )
        sequence = (
            "Candidate Discovered",
            "Candidate Identity Validation",
            "Candidate Identity Established" if identity.result == EnterpriseCertificationDecision.PASS else "Candidate Rejected",
            "Duplicate Evaluation",
            "Unique Candidate" if not duplicates.suppressed_duplicates else "Duplicate Candidate",
            "Freshness Evaluation",
            "Candidate Independence Evaluation",
            "Discovery Sufficiency Evaluation",
            "Candidate Qualified" if accepted else "Candidate Rejected",
            "Candidate Package Construction" if accepted else "Candidate Retired",
            "Candidate Package Validation" if accepted else "Candidate Retired",
            "Candidate Accepted" if accepted else "Candidate Rejected",
            "Candidate Retired",
        )
        invalid = ()
        skipped = ()
        if not candidate.candidate_reference:
            skipped = skipped + ("candidate_identifier",)
        if "Candidate Rejected" in sequence and accepted:
            invalid = invalid + ("accepted_candidate_has_rejection_state",)
        terminal = "Accepted and Committed" if accepted else "Rejected"
        audit_refs = (
            identity.identity_identifier,
            duplicates.duplicate_identifier,
            freshness.freshness_identifier,
            independence.relationship_identifier,
            sufficiency.sufficiency_identifier,
            package_contract.package_contract_identifier,
        )
        record = SeekerCandidateConstitutionalLifecycleRecord(
            lifecycle_identifier=f"SEEK-RM-002-005-CANDIDATE-LIFECYCLE-{_digest((candidate.candidate_reference, sequence, terminal))[:12].upper()}",
            candidate_identifier=candidate.candidate_reference,
            state_sequence=sequence,
            invalid_transitions=invalid,
            skipped_required_states=skipped,
            terminal_outcome=terminal,
            multiple_active_state_findings=(),
            lifecycle_audit_references=audit_refs,
            replay_equivalent=True,
            recovery_checkpoint_valid=True,
            result=EnterpriseCertificationDecision.PASS if not invalid and not skipped and accepted else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_search_mission_constitutional_lifecycle(
        self,
        mission: SeekerSearchMission,
        package_contract: SeekerCandidatePackageContractRecord,
        sufficiency: SeekerSearchSufficiencyRecord,
    ) -> SeekerSearchMissionConstitutionalLifecycleRecord:
        succeeded = package_contract.result == EnterpriseCertificationDecision.PASS and sufficiency.result == EnterpriseCertificationDecision.PASS
        sequence = (
            "Dormant",
            "Mission Accepted",
            "Mission Validation",
            "Discovery Active",
            "Candidate Validation",
            "Search Sufficiency Evaluation",
            "Candidate Package Construction" if succeeded else "Failed",
            "Outbound Commitment" if succeeded else "Failed",
            "Authority Relinquishment",
            "Completed" if succeeded else "Failed",
        )
        allowed = tuple(zip(sequence, sequence[1:]))
        invalid = tuple(f"{a}->{b}" for a, b in allowed if a == b)
        required = ("Dormant", "Mission Accepted", "Mission Validation", "Discovery Active", "Candidate Validation", "Search Sufficiency Evaluation", "Authority Relinquishment")
        skipped = tuple(state for state in required if state not in sequence)
        terminal = sequence[-1]
        audit_refs = (mission.mission_id, package_contract.package_contract_identifier, sufficiency.sufficiency_identifier)
        record = SeekerSearchMissionConstitutionalLifecycleRecord(
            lifecycle_identifier=f"SEEK-RM-002-006-MISSION-LIFECYCLE-{_digest((mission.mission_id, sequence, terminal))[:12].upper()}",
            mission_identifier=mission.mission_id,
            state_sequence=sequence,
            invalid_transitions=invalid,
            skipped_required_states=skipped,
            authority_relinquished="Authority Relinquishment" in sequence,
            terminal_state=terminal,
            lifecycle_audit_references=audit_refs,
            replay_equivalent=True,
            recovery_checkpoint_valid=True,
            result=EnterpriseCertificationDecision.PASS if succeeded and not invalid and not skipped else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_search_sufficiency_metrics(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        sufficiency: SeekerSearchSufficiencyRecord,
        freshness: SeekerFreshnessDeterminationRecord,
        duplicates: SeekerDuplicateSuppressionRecord,
        independence: SeekerRelationshipIndependenceRecord,
        package_contract: SeekerCandidatePackageContractRecord,
    ) -> SeekerSearchSufficiencyMetricsRecord:
        achieved = tuple(dict.fromkeys(item.source_id for item in evidence))
        incomplete = tuple(source for source in search_plan.approved_sources if source not in achieved)
        valid_candidate_count = 1 if all(
            item.result == EnterpriseCertificationDecision.PASS
            for item in (freshness, duplicates, independence, sufficiency, package_contract)
        ) else 0
        package_met = package_contract.result == EnterpriseCertificationDecision.PASS
        audit_met = bool(evidence) and bool(candidates) and bool(sufficiency.sufficiency_identifier)
        outcome = "SUFFICIENT" if not incomplete and valid_candidate_count > 0 and package_met and audit_met else "INSUFFICIENT"
        record = SeekerSearchSufficiencyMetricsRecord(
            metrics_identifier=f"SEEK-RM-002-007-SUFFICIENCY-METRICS-{_digest((mission.mission_id, achieved, outcome))[:12].upper()}",
            sufficiency_rule_version="SEEK-RM-002-007-SUFFICIENCY/1",
            evaluated_mission_id=mission.mission_id,
            evaluated_search_plan_id=search_plan.search_plan_id,
            required_coverage=search_plan.approved_sources,
            achieved_coverage=achieved,
            incomplete_coverage=incomplete,
            validated_candidate_count=valid_candidate_count,
            duplicate_credit_suppressed=not duplicates.suppressed_duplicates,
            freshness_requirements_met=freshness.result == EnterpriseCertificationDecision.PASS,
            independence_requirements_met=independence.result == EnterpriseCertificationDecision.PASS,
            package_requirements_met=package_met,
            audit_requirements_met=audit_met,
            sufficiency_outcome=outcome,
            result=EnterpriseCertificationDecision.PASS if outcome == "SUFFICIENT" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _normalize_value(value: Any) -> str:
    return " ".join(str(value).strip().upper().split())


def _parse_utc(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _timestamps_monotonic(values: tuple[str, ...]) -> bool:
    parsed = tuple(_parse_utc(value) for value in values if value)
    if len(parsed) != len(tuple(value for value in values if value)) or any(value is None for value in parsed):
        return False
    return all(parsed[index] <= parsed[index + 1] for index in range(len(parsed) - 1))


def _freshness_window_days(search_plan: SeekerApprovedSearchPlan) -> int:
    for item in search_plan.freshness_requirements:
        digits = "".join(character for character in item if character.isdigit())
        if digits:
            return int(digits)
    return 30


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return {key: _jsonable(item) for key, item in value.items()}
    if is_dataclass(value):
        return {
            field_info.name: _jsonable(getattr(value, field_info.name))
            for field_info in fields(value)
            if field_info.name not in {"deterministic_digest", "immutable_digest", "evidence_hash"}
        }
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(item) for item in value]
    return value
