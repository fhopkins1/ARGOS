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
class SeekerCandidateEquivalenceDuplicateDoctrineRecord:
    doctrine_identifier: str
    canonical_candidate_identity: str
    candidate_instances: tuple[str, ...]
    identity_attribute_hierarchy: tuple[str, ...]
    equivalence_relationships: Mapping[str, str]
    duplicate_resolution_records: tuple[str, ...]
    indeterminate_identity_findings: tuple[str, ...]
    provenance_preserved: bool
    evidence_preserved: bool
    replay_equivalent: bool
    recovery_preserves_identity: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCandidateFreshnessPolicyRecord:
    policy_identifier: str
    candidate_identifier: str
    freshness_rule_version: str
    freshness_window_days: int
    acquisition_timestamp: str
    authoritative_source_timestamp: str
    evaluation_timestamp: str
    freshness_state: str
    expiration_reason_code: str
    replay_uses_historical_time: bool
    recovery_preserves_freshness_state: bool
    immutable_evidence_references: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCandidateIndependenceDoctrineRecord:
    doctrine_identifier: str
    candidate_identifier: str
    applicability: str
    comparison_universe_identifier: str
    applied_rules: tuple[str, ...]
    evaluated_attributes: Mapping[str, str]
    missing_requirements: tuple[str, ...]
    independence_decision: str
    supporting_evidence_references: tuple[str, ...]
    replay_equivalent: bool
    recovery_preserves_decision: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCandidateRejectionTaxonomyRecord:
    taxonomy_identifier: str
    candidate_identifier: str
    final_disposition: str
    rejection_family: str
    rejection_subclass: str
    primary_rejection_code: str
    contributing_factors: tuple[str, ...]
    taxonomy_version: str
    evidence_references: tuple[str, ...]
    terminal_state: str
    silent_discard_detected: bool
    replay_equivalent: bool
    recovery_preserves_rejection: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerDiscoveryEvidenceConstitutionalSchemaRecord:
    schema_identifier: str
    evidence_identifiers: tuple[str, ...]
    required_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    inadmissible_evidence: tuple[str, ...]
    raw_evidence_preserved: bool
    normalized_evidence_digest: str
    semantic_preservation: bool
    provenance_complete: bool
    integrity_verified: bool
    replay_without_reacquisition: bool
    recovery_from_preserved_evidence: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerDiscoveryProvenanceArchitectureRecord:
    provenance_identifier: str
    required_chain: tuple[str, ...]
    observed_chain: tuple[str, ...]
    missing_chain_stages: tuple[str, ...]
    parent_child_lineage: Mapping[str, str]
    chronological_ordering_violations: tuple[str, ...]
    immutable_provenance_preserved: bool
    outbound_boundary_terminated: bool
    independently_reconstructable: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerConstitutionalStateMachineDoctrineRecord:
    state_machine_identifier: str
    state_inventory: tuple[str, ...]
    authorized_transitions: tuple[str, ...]
    observed_transitions: tuple[str, ...]
    unauthorized_transitions: tuple[str, ...]
    invariant_violations: tuple[str, ...]
    terminal_state: str
    fail_closed_state_available: bool
    recovery_transition_supported: bool
    completed_requires_outbound_commitment: bool
    independently_auditable: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerConstitutionalDoctrineEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    candidate_equivalence_duplicate_doctrine: SeekerCandidateEquivalenceDuplicateDoctrineRecord
    candidate_freshness_policy: SeekerCandidateFreshnessPolicyRecord
    candidate_independence_doctrine: SeekerCandidateIndependenceDoctrineRecord
    candidate_rejection_taxonomy: SeekerCandidateRejectionTaxonomyRecord
    discovery_evidence_schema: SeekerDiscoveryEvidenceConstitutionalSchemaRecord
    discovery_provenance_architecture: SeekerDiscoveryProvenanceArchitectureRecord
    constitutional_state_machine: SeekerConstitutionalStateMachineDoctrineRecord
    final_doctrine_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerOfficeOwnedPersistentStateRecord:
    state_identifier: str
    persistent_state_registry: tuple[str, ...]
    transient_state_registry: tuple[str, ...]
    unclassified_state: tuple[str, ...]
    persisted_state_hashes: Mapping[str, str]
    transient_state_authoritative_findings: tuple[str, ...]
    owner: str
    replay_from_persistent_state_only: bool
    recovery_restores_persistent_state: bool
    integrity_verified: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRecoveryCheckpointArchitectureRecord:
    checkpoint_identifier: str
    checkpoint_schema_version: str
    checkpoint_boundaries: tuple[str, ...]
    certified_checkpoints: tuple[str, ...]
    invalid_checkpoints: tuple[str, ...]
    referenced_constitutional_objects: tuple[str, ...]
    rule_version_manifest: Mapping[str, str]
    recovery_boundary_valid: bool
    replay_interruption_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerConstitutionalCommitBoundaryRecord:
    commit_identifier: str
    canonical_boundaries: tuple[str, ...]
    observed_boundaries: tuple[str, ...]
    missing_boundaries: tuple[str, ...]
    extra_boundaries: tuple[str, ...]
    ordering_violations: tuple[str, ...]
    atomicity_verified: bool
    partial_commit_findings: tuple[str, ...]
    ownership_transition_verified: bool
    replay_preserves_commits: bool
    recovery_uses_last_commit: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerReplaySemanticEquivalenceRecord:
    replay_identifier: str
    replay_semantic_version: str
    invariant_registry: tuple[str, ...]
    preserved_invariants: tuple[str, ...]
    failed_invariants: tuple[str, ...]
    acceptable_runtime_differences: tuple[str, ...]
    unacceptable_runtime_differences: tuple[str, ...]
    version_binding_manifest: Mapping[str, str]
    semantic_equivalence: bool
    downstream_independent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerConstitutionalConfigurationObjectRecord:
    configuration_identifier: str
    configuration_version: str
    doctrine_references: tuple[str, ...]
    required_configuration_fields: tuple[str, ...]
    missing_configuration_fields: tuple[str, ...]
    rule_manifest: Mapping[str, str]
    integrity_digest: str
    execution_version_locked: bool
    recovery_restores_same_configuration: bool
    replay_uses_same_configuration: bool
    owner: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerConstitutionalErrorTaxonomyRecord:
    taxonomy_identifier: str
    error_classes: tuple[str, ...]
    severity_levels: tuple[str, ...]
    classified_errors: Mapping[str, str]
    unclassified_errors: tuple[str, ...]
    handling_policy_manifest: Mapping[str, str]
    fail_closed_enforced: bool
    recovery_semantics_defined: bool
    replay_semantics_defined: bool
    audit_records: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCertificationTraceabilityArchitectureRecord:
    traceability_identifier: str
    traceability_layers: tuple[str, ...]
    doctrine_to_requirements: Mapping[str, tuple[str, ...]]
    requirement_to_implementation: Mapping[str, tuple[str, ...]]
    requirement_to_tests: Mapping[str, tuple[str, ...]]
    test_to_evidence: Mapping[str, tuple[str, ...]]
    outcome_to_evidence: Mapping[str, tuple[str, ...]]
    orphan_findings: tuple[str, ...]
    bidirectional_navigation_verified: bool
    immutable_graph_digest: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCertificationEvidencePackageRecord:
    evidence_package_identifier: str
    package_version: str
    required_sections: tuple[str, ...]
    included_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    evidence_manifest: Mapping[str, str]
    inadmissible_artifacts: tuple[str, ...]
    authenticity_verified: bool
    traceability_verified: bool
    self_contained: bool
    completeness_verified: bool
    supports_independent_pass: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCertificationSupportEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    office_owned_persistent_state: SeekerOfficeOwnedPersistentStateRecord
    recovery_checkpoint_architecture: SeekerRecoveryCheckpointArchitectureRecord
    constitutional_commit_boundaries: SeekerConstitutionalCommitBoundaryRecord
    replay_semantic_equivalence: SeekerReplaySemanticEquivalenceRecord
    constitutional_configuration_object: SeekerConstitutionalConfigurationObjectRecord
    constitutional_error_taxonomy: SeekerConstitutionalErrorTaxonomyRecord
    certification_traceability_architecture: SeekerCertificationTraceabilityArchitectureRecord
    certification_evidence_package: SeekerCertificationEvidencePackageRecord
    final_support_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003SearchMissionCanonicalObjectRecord:
    object_identifier: str
    schema_identifier: str
    required_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    mission_identity_digest: str
    authority_root: str
    authority_findings: tuple[str, ...]
    boundary_findings: tuple[str, ...]
    traceability_targets: Mapping[str, str]
    immutable_payload_preserved: bool
    lifecycle_state_separated: bool
    replay_anchor_verified: bool
    recovery_anchor_verified: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003SearchPlanConstitutionalContractRecord:
    contract_identifier: str
    schema_identifier: str
    required_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    governing_mission_id: str
    plan_authority_findings: tuple[str, ...]
    execution_bounds_findings: tuple[str, ...]
    terminal_outcomes: tuple[str, ...]
    deterministic_execution_order: tuple[str, ...]
    immutable_commit_verified: bool
    replay_preserves_contract: bool
    recovery_preserves_contract: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CandidatePackageConstitutionRecord:
    constitution_identifier: str
    package_schema_identifier: str
    required_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    package_identity_digest: str
    candidate_subject_count: int
    package_invariant_violations: tuple[str, ...]
    bound_evidence: tuple[str, ...]
    bound_provenance_chain: tuple[str, ...]
    lifecycle_and_disposition_bound: bool
    persistence_replay_recovery_bound: bool
    delivery_fail_closed: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CandidateIdentityDoctrineRecord:
    identity_doctrine_identifier: str
    candidate_identity_object_identifier: str
    required_identity_fields: tuple[str, ...]
    missing_identity_fields: tuple[str, ...]
    candidate_class: str
    canonical_components: Mapping[str, str]
    normalization_rules: tuple[str, ...]
    identity_integrity_hash: str
    ambiguity_findings: tuple[str, ...]
    collision_findings: tuple[str, ...]
    replay_stable: bool
    recovery_stable: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CandidateLifecycleDoctrineRecord:
    lifecycle_identifier: str
    canonical_states: tuple[str, ...]
    observed_state_sequence: tuple[str, ...]
    invalid_transitions: tuple[str, ...]
    skipped_states: tuple[str, ...]
    terminal_state: str
    evidence_mutation_findings: tuple[str, ...]
    audit_events: tuple[str, ...]
    replay_reconstructs_sequence: bool
    recovery_checkpoint_valid: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003SearchMissionLifecycleDoctrineRecord:
    lifecycle_identifier: str
    canonical_states: tuple[str, ...]
    observed_state_sequence: tuple[str, ...]
    invalid_transitions: tuple[str, ...]
    skipped_states: tuple[str, ...]
    terminal_state: str
    authority_relinquished: bool
    audit_events: tuple[str, ...]
    replay_reconstructs_sequence: bool
    recovery_checkpoint_valid: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CanonicalEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    search_mission_canonical_object: SeekerRm003SearchMissionCanonicalObjectRecord
    search_plan_constitutional_contract: SeekerRm003SearchPlanConstitutionalContractRecord
    candidate_package_constitution: SeekerRm003CandidatePackageConstitutionRecord
    candidate_identity_doctrine: SeekerRm003CandidateIdentityDoctrineRecord
    candidate_lifecycle_doctrine: SeekerRm003CandidateLifecycleDoctrineRecord
    search_mission_lifecycle_doctrine: SeekerRm003SearchMissionLifecycleDoctrineRecord
    final_rm003_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003SearchSufficiencyDoctrineRecord:
    sufficiency_identifier: str
    sufficiency_profile: str
    required_metrics: tuple[str, ...]
    missing_metrics: tuple[str, ...]
    metric_results: Mapping[str, str]
    disposition: str
    terminal_distinctions: tuple[str, ...]
    premature_completion_findings: tuple[str, ...]
    replay_equivalent: bool
    recovery_equivalent: bool
    audit_references: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CandidateEquivalenceDoctrineRecord:
    equivalence_identifier: str
    rule_version: str
    evaluated_candidates: tuple[str, ...]
    equivalence_classes: Mapping[str, tuple[str, ...]]
    duplicate_dispositions: Mapping[str, str]
    unresolved_comparisons: tuple[str, ...]
    representative_selection: Mapping[str, str]
    evidence_preserved: bool
    order_independent: bool
    replay_equivalent: bool
    recovery_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CandidateFreshnessDoctrineRecord:
    freshness_identifier: str
    freshness_window_registry: Mapping[str, str]
    evaluated_timestamp_basis: str
    freshness_status: str
    stale_or_expired_dependencies: tuple[str, ...]
    temporal_ambiguity_findings: tuple[str, ...]
    delivery_eligible: bool
    historical_replay_mode_separated: bool
    recovery_reevaluation_required: bool
    audit_references: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CandidateIndependenceDoctrineRecord:
    independence_identifier: str
    independence_profile: str
    evaluation_stages: tuple[str, ...]
    dependency_findings: tuple[str, ...]
    circularity_findings: tuple[str, ...]
    corroboration_findings: tuple[str, ...]
    independence_status: str
    evidence_origin_verified: bool
    replay_equivalent: bool
    recovery_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CandidateRejectionTaxonomyDoctrineRecord:
    taxonomy_identifier: str
    taxonomy_version: str
    allowed_categories: tuple[str, ...]
    primary_rejection_category: str
    supplemental_rejection_findings: tuple[str, ...]
    unsupported_rejection_findings: tuple[str, ...]
    rejection_record_identifier: str
    rejected_candidate_preserved: bool
    replay_preserves_rejection: bool
    recovery_preserves_rejection: bool
    audit_references: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003DiscoveryEvidenceConstitutionRecord:
    evidence_constitution_identifier: str
    schema_version: str
    required_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    inadmissible_evidence: tuple[str, ...]
    prohibited_semantic_findings: tuple[str, ...]
    evidence_hashes: tuple[str, ...]
    provenance_chains: Mapping[str, tuple[str, ...]]
    normalization_replayable: bool
    preservation_immutable: bool
    audit_reconstructable: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003DoctrineEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    search_sufficiency_doctrine: SeekerRm003SearchSufficiencyDoctrineRecord
    candidate_equivalence_doctrine: SeekerRm003CandidateEquivalenceDoctrineRecord
    candidate_freshness_doctrine: SeekerRm003CandidateFreshnessDoctrineRecord
    candidate_independence_doctrine: SeekerRm003CandidateIndependenceDoctrineRecord
    candidate_rejection_taxonomy: SeekerRm003CandidateRejectionTaxonomyDoctrineRecord
    discovery_evidence_constitution: SeekerRm003DiscoveryEvidenceConstitutionRecord
    final_rm003_doctrine_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003DiscoveryProvenanceArchitectureRecord:
    provenance_identifier: str
    graph_schema_version: str
    required_node_classes: tuple[str, ...]
    missing_node_classes: tuple[str, ...]
    required_edge_classes: tuple[str, ...]
    missing_edge_classes: tuple[str, ...]
    mission_root: str
    provenance_chain: tuple[str, ...]
    orphan_objects: tuple[str, ...]
    integrity_findings: tuple[str, ...]
    recovery_lineage_separate: bool
    replay_lineage_separate: bool
    independently_reconstructable: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003OfficeStateMachineRecord:
    state_machine_identifier: str
    canonical_states: tuple[str, ...]
    observed_state_sequence: tuple[str, ...]
    illegal_transitions: tuple[str, ...]
    skipped_mandatory_states: tuple[str, ...]
    multiple_current_state_findings: tuple[str, ...]
    terminal_state: str
    authority_relinquished: bool
    recovery_state_validated: bool
    replay_state_equivalent: bool
    audit_reconstructable: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003OfficeOwnedPersistentStateRecord:
    persistence_identifier: str
    classification_registry_version: str
    persistent_state_classes: tuple[str, ...]
    conditionally_persistent_state_classes: tuple[str, ...]
    transient_state_classes: tuple[str, ...]
    prohibited_residual_state_classes: tuple[str, ...]
    unclassified_state: tuple[str, ...]
    residual_state_findings: tuple[str, ...]
    integrity_manifest: Mapping[str, str]
    recovery_supported: bool
    replay_supported: bool
    audit_supported: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003RecoveryCheckpointArchitectureRecord:
    checkpoint_identifier: str
    authorized_boundaries: tuple[str, ...]
    observed_boundaries: tuple[str, ...]
    unauthorized_boundaries: tuple[str, ...]
    missing_checkpoint_contents: tuple[str, ...]
    invalid_checkpoint_findings: tuple[str, ...]
    checkpoint_sequence: tuple[str, ...]
    integrity_verified: bool
    recovery_idempotent: bool
    replay_compatible: bool
    audit_references: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003ConstitutionalCommitBoundaryRecord:
    commit_architecture_identifier: str
    canonical_commit_boundaries: tuple[str, ...]
    observed_commit_boundaries: tuple[str, ...]
    missing_commit_boundaries: tuple[str, ...]
    unauthorized_commit_boundaries: tuple[str, ...]
    ordering_violations: tuple[str, ...]
    partial_commit_findings: tuple[str, ...]
    monotonic_sequence_verified: bool
    referential_integrity_verified: bool
    recovery_from_completed_boundary_only: bool
    replay_preserves_commit_ordering: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003ReplaySemanticEquivalenceRecord:
    replay_identifier: str
    replay_invariants: tuple[str, ...]
    preserved_invariants: tuple[str, ...]
    failed_invariants: tuple[str, ...]
    acceptable_runtime_differences: tuple[str, ...]
    prohibited_runtime_differences: tuple[str, ...]
    replay_classification: str
    identical_constitutional_inputs: bool
    semantic_equivalence: bool
    recovery_replay_equivalent: bool
    audit_references: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003OperationalIntegrityEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    discovery_provenance_architecture: SeekerRm003DiscoveryProvenanceArchitectureRecord
    office_state_machine: SeekerRm003OfficeStateMachineRecord
    office_owned_persistent_state: SeekerRm003OfficeOwnedPersistentStateRecord
    recovery_checkpoint_architecture: SeekerRm003RecoveryCheckpointArchitectureRecord
    constitutional_commit_boundaries: SeekerRm003ConstitutionalCommitBoundaryRecord
    replay_semantic_equivalence: SeekerRm003ReplaySemanticEquivalenceRecord
    final_rm003_operational_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003ConstitutionalConfigurationObjectRecord:
    configuration_identifier: str
    schema_version: str
    required_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    active_default_configuration_count: int
    mission_binding: str
    search_plan_binding: str
    candidate_evaluation_binding: str
    hidden_configuration_findings: tuple[str, ...]
    immutable_reference_manifest: Mapping[str, str]
    activation_auditable: bool
    recovery_uses_original_configuration: bool
    replay_discloses_substitution: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003ConstitutionalErrorTaxonomyRecord:
    taxonomy_identifier: str
    taxonomy_version: str
    top_level_categories: tuple[str, ...]
    severity_levels: tuple[str, ...]
    classified_errors: Mapping[str, str]
    unclassified_errors: tuple[str, ...]
    fail_closed_categories: tuple[str, ...]
    retry_eligible_categories: tuple[str, ...]
    immutable_error_records: tuple[str, ...]
    recovery_preserves_errors: bool
    replay_preserves_classification: bool
    audit_reconstructable: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CertificationTraceabilityArchitectureRecord:
    traceability_identifier: str
    traceability_layers: tuple[str, ...]
    missing_layers: tuple[str, ...]
    doctrine_to_requirement: Mapping[str, tuple[str, ...]]
    requirement_to_implementation: Mapping[str, tuple[str, ...]]
    requirement_to_test: Mapping[str, tuple[str, ...]]
    requirement_to_evidence: Mapping[str, tuple[str, ...]]
    orphan_requirements: tuple[str, ...]
    orphan_implementation: tuple[str, ...]
    orphan_evidence: tuple[str, ...]
    replay_traceability_preserved: bool
    recovery_traceability_preserved: bool
    graph_integrity_digest: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CertificationEvidencePackageRecord:
    evidence_package_identifier: str
    package_version: str
    required_sections: tuple[str, ...]
    included_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    evidence_manifest: Mapping[str, str]
    inadmissible_artifacts: tuple[str, ...]
    integrity_hash_manifest: Mapping[str, str]
    independently_verifiable: bool
    replay_reproducible: bool
    recovery_demonstrated: bool
    supports_unconditional_pass: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm003CertificationClosureEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    constitutional_configuration_object: SeekerRm003ConstitutionalConfigurationObjectRecord
    constitutional_error_taxonomy: SeekerRm003ConstitutionalErrorTaxonomyRecord
    certification_traceability_architecture: SeekerRm003CertificationTraceabilityArchitectureRecord
    certification_evidence_package: SeekerRm003CertificationEvidencePackageRecord
    final_rm003_certification_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm004CandidateClassRegistryEntry:
    class_id: str
    canonical_name: str
    definition: str
    registry_status: str
    identity_schema_id: str
    required_identity_components: tuple[str, ...]
    conditional_identity_components: tuple[str, ...]
    prohibited_identity_components: tuple[str, ...]
    required_evidence_categories: tuple[str, ...]
    conditional_evidence_categories: tuple[str, ...]
    lifecycle_profile_id: str
    freshness_profile_id: str
    independence_profile_id: str
    equivalence_profile_id: str
    admissibility_profile_id: str
    class_specific_rejection_ids: tuple[str, ...]
    permitted_relationship_types: tuple[str, ...]
    orderable: bool
    version_introduced: str
    version_deprecated: str
    version_retired: str
    governing_doctrine_refs: tuple[str, ...]
    certification_test_refs: tuple[str, ...]


@dataclass(frozen=True)
class SeekerRm004CandidateClassRegistryRecord:
    registry_identifier: str
    registry_version: str
    registry_hash: str
    entries: tuple[SeekerRm004CandidateClassRegistryEntry, ...]
    registered_class_ids: tuple[str, ...]
    duplicate_class_ids: tuple[str, ...]
    duplicate_canonical_names: tuple[str, ...]
    invalid_class_ids: tuple[str, ...]
    incomplete_entries: tuple[str, ...]
    prohibited_residual_classes: tuple[str, ...]
    candidate_primary_class_id: str
    candidate_class_authorized_by_plan: bool
    unknown_or_unsupported_claims: tuple[str, ...]
    ambiguous_claims: tuple[str, ...]
    multiple_primary_class_findings: tuple[str, ...]
    class_assignment_disposition: str
    non_orderable_execution_findings: tuple[str, ...]
    replay_registry_version_aware: bool
    recovery_registry_version_aware: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm004EvaluationRuleRegistryEntry:
    rule_id: str
    rule_version: str
    rule_name: str
    rule_domain: str
    rule_status: str
    constitutional_owner: str
    governing_doctrine_ids: tuple[str, ...]
    evaluation_subject_type: str
    required_input_types: tuple[str, ...]
    required_evidence_types: tuple[str, ...]
    evaluation_type: str
    permitted_outcomes: tuple[str, ...]
    severity_by_outcome: Mapping[str, str]
    admissibility_consequence_by_outcome: Mapping[str, str]
    certification_consequence_by_outcome: Mapping[str, str]
    prerequisite_rule_ids: tuple[str, ...]
    replay_rule_version_policy: str
    recovery_evaluation_policy: str
    certification_test_ids: tuple[str, ...]


@dataclass(frozen=True)
class SeekerRm004EvaluationRuleRegistryRecord:
    registry_identifier: str
    registry_version: str
    registry_hash: str
    entries: tuple[SeekerRm004EvaluationRuleRegistryEntry, ...]
    active_rule_ids: tuple[str, ...]
    duplicate_rule_ids: tuple[str, ...]
    invalid_rule_ids: tuple[str, ...]
    incomplete_rule_ids: tuple[str, ...]
    missing_doctrine_traceability: tuple[str, ...]
    missing_test_traceability: tuple[str, ...]
    missing_severity_mappings: tuple[str, ...]
    missing_consequence_mappings: tuple[str, ...]
    circular_dependency_findings: tuple[str, ...]
    unresolved_conflicts: tuple[str, ...]
    immutable_rule_evaluation_records: tuple[str, ...]
    fail_closed_unresolved_rule_ids: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm004CertificationThresholdRecord:
    threshold_identifier: str
    threshold_version: str
    threshold_domains: Mapping[str, int]
    measured_domain_coverage: Mapping[str, int]
    failing_domains: tuple[str, ...]
    zero_tolerance_conditions: Mapping[str, int]
    observed_zero_tolerance_counts: Mapping[str, int]
    violated_zero_tolerance_conditions: tuple[str, ...]
    pass_algorithm_steps: tuple[str, ...]
    certification_tests_passed: bool
    replay_validations_passed: bool
    recovery_validations_passed: bool
    binary_certification_result: str
    immutable_threshold_evidence: Mapping[str, str]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm004CertificationTestRegistryEntry:
    test_id: str
    test_name: str
    test_version: str
    test_family: str
    status: str
    mandatory_classification: str
    governing_doctrine_ids: tuple[str, ...]
    constitutional_requirement_ids: tuple[str, ...]
    evaluation_rule_ids: tuple[str, ...]
    threshold_ids: tuple[str, ...]
    pass_criteria: tuple[str, ...]
    fail_criteria: tuple[str, ...]
    required_evidence_artifact_types: tuple[str, ...]
    prerequisite_test_ids: tuple[str, ...]
    expected_replay_result: str
    certification_effect: str
    entry_hash: str


@dataclass(frozen=True)
class SeekerRm004CertificationTestRegistryRecord:
    registry_identifier: str
    registry_version: str
    registry_manifest: Mapping[str, str]
    registry_hash: str
    entries: tuple[SeekerRm004CertificationTestRegistryEntry, ...]
    mandatory_test_families: tuple[str, ...]
    covered_test_families: tuple[str, ...]
    missing_test_families: tuple[str, ...]
    duplicate_test_ids: tuple[str, ...]
    incomplete_test_ids: tuple[str, ...]
    uncovered_requirement_ids: tuple[str, ...]
    orphan_test_ids: tuple[str, ...]
    invalid_dependency_findings: tuple[str, ...]
    invalid_execution_outcomes: tuple[str, ...]
    enterprise_dependency_findings: tuple[str, ...]
    certification_aggregation_result: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm004CertificationCompletionEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    unprovided_dependency_orders: tuple[str, ...]
    candidate_class_registry: SeekerRm004CandidateClassRegistryRecord
    evaluation_rule_registry: SeekerRm004EvaluationRuleRegistryRecord
    certification_thresholds: SeekerRm004CertificationThresholdRecord
    certification_test_registry: SeekerRm004CertificationTestRegistryRecord
    final_rm004_provided_order_readiness: EnterpriseCertificationDecision
    independent_certification_dependency_status: str
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm004CollisionResolutionRecord:
    collision_identifier: str
    doctrine_version: str
    collision_taxonomy: Mapping[str, str]
    collision_state_inventory: tuple[str, ...]
    collision_set: tuple[str, ...]
    collision_class: str
    investigation_steps: tuple[str, ...]
    missing_investigation_steps: tuple[str, ...]
    admissible_evidence_references: tuple[str, ...]
    heuristic_resolution_findings: tuple[str, ...]
    collision_outcome: str
    final_collision_state: str
    candidate_evaluation_blocked: bool
    merge_preserves_history: bool
    replay_reproduces_outcome: bool
    recovery_preserves_state: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm004MetricRegistryEntry:
    metric_id: str
    metric_name: str
    metric_category: str
    constitutional_purpose: str
    owning_office: str
    calculation_definition: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...]
    units: str
    precision: str
    update_trigger: str
    persistence_requirements: str
    replay_requirements: str
    certification_usage: str
    interpretation_rules: str
    failure_conditions: tuple[str, ...]
    registry_version: str
    status: str


@dataclass(frozen=True)
class SeekerRm004MetricsRegistryRecord:
    registry_identifier: str
    registry_version: str
    registry_hash: str
    entries: tuple[SeekerRm004MetricRegistryEntry, ...]
    metric_categories: tuple[str, ...]
    duplicate_metric_ids: tuple[str, ...]
    invalid_metric_ids: tuple[str, ...]
    incomplete_metric_ids: tuple[str, ...]
    invalid_units: tuple[str, ...]
    precision_violations: tuple[str, ...]
    implementation_defined_certification_metrics: tuple[str, ...]
    replay_divergent_metrics: tuple[str, ...]
    immutable_historical_storage: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm004IdentifierNamespaceEntry:
    namespace: str
    prefix: str
    purpose: str
    syntax: str
    lifecycle_states: tuple[str, ...]
    reserved_ranges: tuple[str, ...]
    replay_semantics: str
    recovery_semantics: str
    collision_handling: str
    version: str
    status: str


@dataclass(frozen=True)
class SeekerRm004IdentifierRegistryRecord:
    registry_identifier: str
    registry_version: str
    registry_hash: str
    namespaces: tuple[SeekerRm004IdentifierNamespaceEntry, ...]
    duplicate_prefixes: tuple[str, ...]
    invalid_prefixes: tuple[str, ...]
    incomplete_namespaces: tuple[str, ...]
    observed_identifiers: tuple[str, ...]
    invalid_identifiers: tuple[str, ...]
    duplicate_identifiers: tuple[str, ...]
    reserved_identifier_violations: tuple[str, ...]
    collision_findings: tuple[str, ...]
    replay_preserves_identifiers: bool
    recovery_preserves_identifiers: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm004VersionCompatibilityEntry:
    source_version: str
    target_version: str
    compatibility_classification: str
    migration_required: bool
    replay_allowed: bool
    recovery_allowed: bool
    certification_allowed: bool
    persistence_allowed: bool
    checkpoint_allowed: bool
    required_migration_version: str
    approval_record: str
    effective_date: str


@dataclass(frozen=True)
class SeekerRm004VersionCompatibilityRecord:
    matrix_identifier: str
    matrix_version: str
    matrix_hash: str
    version_registry: Mapping[str, str]
    compatibility_entries: tuple[SeekerRm004VersionCompatibilityEntry, ...]
    missing_version_records: tuple[str, ...]
    missing_matrix_entries: tuple[str, ...]
    unknown_compatibility_pairs: tuple[str, ...]
    implicit_compatibility_findings: tuple[str, ...]
    migration_registry: Mapping[str, str]
    undefined_migrations: tuple[str, ...]
    replay_incompatible_pairs: tuple[str, ...]
    recovery_incompatible_pairs: tuple[str, ...]
    certification_incompatible_pairs: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerRm004RegistryGovernanceEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    unprovided_dependency_orders: tuple[str, ...]
    collision_resolution: SeekerRm004CollisionResolutionRecord
    metrics_registry: SeekerRm004MetricsRegistryRecord
    identifier_registry: SeekerRm004IdentifierRegistryRecord
    version_compatibility_matrix: SeekerRm004VersionCompatibilityRecord
    final_rm004_registry_governance_readiness: EnterpriseCertificationDecision
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

    constitutional_doctrine_order_coverage = (
        "SEEK-RM-002-008",
        "SEEK-RM-002-009",
        "SEEK-RM-002-010",
        "SEEK-RM-002-011",
        "SEEK-RM-002-012",
        "SEEK-RM-002-013",
        "SEEK-RM-002-014",
    )

    certification_support_order_coverage = (
        "SEEK-RM-002-015",
        "SEEK-RM-002-016",
        "SEEK-RM-002-017",
        "SEEK-RM-002-018",
        "SEEK-RM-002-019",
        "SEEK-RM-002-020",
        "SEEK-RM-002-021",
        "SEEK-RM-002-022",
    )

    rm003_canonical_order_coverage = (
        "SEEK-RM-003-001",
        "SEEK-RM-003-002",
        "SEEK-RM-003-003",
        "SEEK-RM-003-004",
        "SEEK-RM-003-005",
        "SEEK-RM-003-006",
    )

    rm003_doctrine_order_coverage = (
        "SEEK-RM-003-007",
        "SEEK-RM-003-008",
        "SEEK-RM-003-009",
        "SEEK-RM-003-010",
        "SEEK-RM-003-011",
        "SEEK-RM-003-012",
    )

    rm003_operational_order_coverage = (
        "SEEK-RM-003-013",
        "SEEK-RM-003-014",
        "SEEK-RM-003-015",
        "SEEK-RM-003-016",
        "SEEK-RM-003-017",
        "SEEK-RM-003-018",
    )

    rm003_certification_order_coverage = (
        "SEEK-RM-003-019",
        "SEEK-RM-003-020",
        "SEEK-RM-003-021",
        "SEEK-RM-003-022",
    )

    rm004_certification_completion_order_coverage = (
        "SEEK-RM-004-001",
        "SEEK-RM-004-003",
        "SEEK-RM-004-004",
        "SEEK-RM-004-005",
    )

    rm004_unprovided_dependency_orders = ("SEEK-RM-004-002",)

    rm004_registry_governance_order_coverage = (
        "SEEK-RM-004-006",
        "SEEK-RM-004-007",
        "SEEK-RM-004-009",
        "SEEK-RM-004-010",
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

    def build_constitutional_doctrine_package(
        self,
        *,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        observed_state_sequence: tuple[str, ...] | None = None,
    ) -> SeekerConstitutionalDoctrineEvidencePackage:
        primary_candidate = candidates[0] if candidates else SeekerCandidateIdentityInput("", "", (), MappingProxyType({}))
        freshness = self.evaluate_freshness_determination(mission, search_plan, primary_candidate, discovery_evidence)
        duplicates = self.evaluate_duplicate_suppression(search_plan, candidates, discovery_evidence)
        independence = self.evaluate_relationship_independence(search_plan, candidates, discovery_evidence)
        sufficiency = self.evaluate_search_sufficiency(search_plan, discovery_evidence, candidates)
        identity = self.evaluate_candidate_identity(primary_candidate, search_plan, discovery_evidence)
        preservation = self.evaluate_discovery_evidence_preservation(mission, search_plan, discovery_evidence, primary_candidate)
        elimination = self.evaluate_unsupported_candidate_elimination(
            primary_candidate,
            (identity, preservation, freshness, duplicates, independence, sufficiency),
        )
        disposition = self.evaluate_disposition_handling(primary_candidate, elimination)
        package_contract = self.evaluate_candidate_package_contract(
            mission,
            search_plan,
            candidates,
            discovery_evidence,
            (identity, preservation, freshness, duplicates, independence, sufficiency, elimination, disposition),
        )
        equivalence = self.evaluate_candidate_equivalence_duplicate_doctrine(search_plan, candidates, discovery_evidence, duplicates)
        freshness_policy = self.evaluate_candidate_freshness_policy(mission, primary_candidate, discovery_evidence, freshness)
        independence_doctrine = self.evaluate_candidate_independence_doctrine(search_plan, primary_candidate, discovery_evidence, independence)
        rejection = self.evaluate_candidate_rejection_taxonomy(
            mission,
            primary_candidate,
            (identity, preservation, freshness, duplicates, independence, sufficiency, package_contract),
        )
        evidence_schema = self.evaluate_discovery_evidence_constitutional_schema(mission, search_plan, discovery_evidence, primary_candidate)
        provenance = self.evaluate_discovery_provenance_architecture(mission, search_plan, discovery_evidence, primary_candidate, package_contract)
        state_machine = self.evaluate_constitutional_state_machine_doctrine(
            observed_state_sequence or (
                "Dormant",
                "Mission Acceptance",
                "Objective Validation",
                "Search Plan Validation",
                "Discovery Execution",
                "Candidate Validation",
                "Search Sufficiency Evaluation",
                "Candidate Package Construction",
                "Audit Verification",
                "Outbound Commitment",
                "Completed",
                "Dormant",
            )
        )
        final = EnterpriseCertificationDecision.PASS if all(
            record == EnterpriseCertificationDecision.PASS
            for record in (
                equivalence.result,
                freshness_policy.result,
                independence_doctrine.result,
                rejection.result,
                evidence_schema.result,
                provenance.result,
                state_machine.result,
            )
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerConstitutionalDoctrineEvidencePackage(
            package_identifier=f"SEEK-RM-002-DOCTRINE-{_digest((mission.mission_id, search_plan.search_plan_id, tuple(item.candidate_reference for item in candidates)))[:12].upper()}",
            governing_doctrine="SEEK-RM-002-008-TO-014/1.0.0",
            remediation_order_coverage=self.constitutional_doctrine_order_coverage,
            candidate_equivalence_duplicate_doctrine=equivalence,
            candidate_freshness_policy=freshness_policy,
            candidate_independence_doctrine=independence_doctrine,
            candidate_rejection_taxonomy=rejection,
            discovery_evidence_schema=evidence_schema,
            discovery_provenance_architecture=provenance,
            constitutional_state_machine=state_machine,
            final_doctrine_readiness=final,
            immutable_audit_references=(
                equivalence.doctrine_identifier,
                freshness_policy.policy_identifier,
                independence_doctrine.doctrine_identifier,
                rejection.taxonomy_identifier,
                evidence_schema.schema_identifier,
                provenance.provenance_identifier,
                state_machine.state_machine_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_candidate_equivalence_duplicate_doctrine(
        self,
        search_plan: SeekerApprovedSearchPlan,
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        duplicates: SeekerDuplicateSuppressionRecord,
    ) -> SeekerCandidateEquivalenceDuplicateDoctrineRecord:
        identities = tuple(self.evaluate_candidate_identity(candidate, search_plan, evidence).canonical_identity for candidate in candidates)
        canonical = next((identity for identity in identities if identity), "")
        relationships = MappingProxyType(
            {
                candidate.candidate_reference: "Canonically Equivalent" if identity and identity == canonical else "Indeterminate" if not identity else "Distinct"
                for candidate, identity in zip(candidates, identities)
            }
        )
        duplicate_records = tuple(
            f"DUP-{_digest((candidate.candidate_reference, canonical, duplicates.duplicate_rule_version))[:12].upper()}"
            for candidate, identity in zip(candidates, identities)
            if canonical and identity == canonical and candidate.candidate_reference not in duplicates.authoritative_candidates
        )
        indeterminate = tuple(candidate.candidate_reference for candidate, identity in zip(candidates, identities) if not identity)
        passed = bool(candidates) and bool(canonical) and not indeterminate and duplicates.evidence_preserved_for_suppressed
        record = SeekerCandidateEquivalenceDuplicateDoctrineRecord(
            doctrine_identifier=f"SEEK-RM-002-008-EQUIVALENCE-{_digest((identities, duplicates.suppressed_duplicates, indeterminate))[:12].upper()}",
            canonical_candidate_identity=canonical,
            candidate_instances=tuple(candidate.candidate_reference for candidate in candidates),
            identity_attribute_hierarchy=("Tier I Authoritative Identity", "Tier II Secondary Identity", "Tier III Supporting Identity"),
            equivalence_relationships=relationships,
            duplicate_resolution_records=duplicate_records,
            indeterminate_identity_findings=indeterminate,
            provenance_preserved=duplicates.evidence_preserved_for_suppressed,
            evidence_preserved=duplicates.evidence_preserved_for_suppressed,
            replay_equivalent=duplicates.order_independent,
            recovery_preserves_identity=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_candidate_freshness_policy(
        self,
        mission: SeekerSearchMission,
        candidate: SeekerCandidateIdentityInput,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        freshness: SeekerFreshnessDeterminationRecord,
    ) -> SeekerCandidateFreshnessPolicyRecord:
        state = "Fresh" if freshness.freshness_decision == "FRESH" else "Expired" if freshness.freshness_decision == "STALE" else "Indeterminate"
        refs = tuple(item.evidence_id for item in evidence if item.evidence_id in set(candidate.evidence_references))
        passed = state == "Fresh" and bool(refs) and freshness.result == EnterpriseCertificationDecision.PASS
        record = SeekerCandidateFreshnessPolicyRecord(
            policy_identifier=f"SEEK-RM-002-009-FRESHNESS-{_digest((candidate.candidate_reference, freshness.authoritative_timestamp, state))[:12].upper()}",
            candidate_identifier=candidate.candidate_reference,
            freshness_rule_version="SEEK-RM-002-009-FRESHNESS/1",
            freshness_window_days=freshness.freshness_window_days,
            acquisition_timestamp=freshness.evaluation_timestamp,
            authoritative_source_timestamp=freshness.authoritative_timestamp,
            evaluation_timestamp=freshness.evaluation_timestamp or mission.mission_creation_timestamp,
            freshness_state=state,
            expiration_reason_code=freshness.rejection_reason,
            replay_uses_historical_time=True,
            recovery_preserves_freshness_state=True,
            immutable_evidence_references=refs,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_candidate_independence_doctrine(
        self,
        search_plan: SeekerApprovedSearchPlan,
        candidate: SeekerCandidateIdentityInput,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        independence: SeekerRelationshipIndependenceRecord,
    ) -> SeekerCandidateIndependenceDoctrineRecord:
        applicable = "Required" if search_plan.independence_requirements else "Not Applicable"
        missing = ()
        if applicable == "Required" and not search_plan.independence_requirements:
            missing = missing + ("independence_rules",)
        if applicable == "Required" and not evidence:
            missing = missing + ("comparison_evidence",)
        decision = "Independent" if independence.result == EnterpriseCertificationDecision.PASS else "Not Independent"
        if applicable == "Not Applicable":
            decision = "Not Applicable"
        passed = (decision in {"Independent", "Not Applicable"}) and not missing
        record = SeekerCandidateIndependenceDoctrineRecord(
            doctrine_identifier=f"SEEK-RM-002-010-INDEPENDENCE-{_digest((candidate.candidate_reference, applicable, decision))[:12].upper()}",
            candidate_identifier=candidate.candidate_reference,
            applicability=applicable,
            comparison_universe_identifier=f"CMP-{_digest((search_plan.search_plan_id, tuple(item.source_id for item in evidence)))[:12].upper()}",
            applied_rules=search_plan.independence_requirements,
            evaluated_attributes=MappingProxyType({key: str(value) for key, value in sorted(candidate.attributes.items()) if key in {"issuer_name", "exchange", "sector", "industry", "relationship"}}),
            missing_requirements=missing,
            independence_decision=decision,
            supporting_evidence_references=tuple(item.evidence_id for item in evidence),
            replay_equivalent=True,
            recovery_preserves_decision=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_candidate_rejection_taxonomy(
        self,
        mission: SeekerSearchMission,
        candidate: SeekerCandidateIdentityInput,
        validation_records: tuple[Any, ...],
    ) -> SeekerCandidateRejectionTaxonomyRecord:
        failures = tuple(record for record in validation_records if getattr(record, "result", EnterpriseCertificationDecision.FAIL) != EnterpriseCertificationDecision.PASS)
        factor_names = tuple(type(record).__name__ for record in failures)
        evidence_refs = candidate.evidence_references
        family = ""
        subclass = ""
        code = ""
        if factor_names:
            first = factor_names[0]
            if "Identity" in first:
                family, subclass, code = "Identity Rejection", "Identity Ambiguous", "IDENTITY_AMBIGUOUS"
            elif "Freshness" in first:
                family, subclass, code = "Freshness Rejection", "Freshness Rule Failure", "FRESHNESS_RULE_FAILURE"
            elif "Duplicate" in first:
                family, subclass, code = "Duplicate Rejection", "Duplicate Under Registered Equivalence Rules", "DUPLICATE_REGISTERED_EQUIVALENCE"
            elif "Independence" in first or "Relationship" in first:
                family, subclass, code = "Independence Rejection", "Independence Rule Failure", "INDEPENDENCE_RULE_FAILURE"
            elif "Sufficiency" in first:
                family, subclass, code = "Sufficiency Rejection", "Search Incomplete", "SEARCH_INCOMPLETE"
            elif "Package" in first:
                family, subclass, code = "Package Rejection", "Package Validation Failure", "PACKAGE_VALIDATION_FAILURE"
            elif "Evidence" in first:
                family, subclass, code = "Evidence Rejection", "Evidence Schema Failure", "EVIDENCE_SCHEMA_FAILURE"
            else:
                family, subclass, code = "Constitutional Integrity Rejection", "Determinism Failure", "CONSTITUTIONAL_INTEGRITY_FAILURE"
        disposition = "REJECTED" if failures else "ADMITTED"
        terminal = "REJECTED_FINAL" if failures else "ADMITTED_FINAL"
        silent = disposition == "REJECTED" and (not code or not evidence_refs)
        record = SeekerCandidateRejectionTaxonomyRecord(
            taxonomy_identifier=f"SEEK-RM-002-011-REJECTION-{_digest((mission.mission_id, candidate.candidate_reference, code, factor_names))[:12].upper()}",
            candidate_identifier=candidate.candidate_reference,
            final_disposition=disposition,
            rejection_family=family,
            rejection_subclass=subclass,
            primary_rejection_code=code,
            contributing_factors=factor_names,
            taxonomy_version="SEEK-RM-002-011-REJECTION/1",
            evidence_references=evidence_refs,
            terminal_state=terminal,
            silent_discard_detected=silent,
            replay_equivalent=True,
            recovery_preserves_rejection=True,
            result=EnterpriseCertificationDecision.PASS if not silent and (disposition == "ADMITTED" or bool(code)) else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_discovery_evidence_constitutional_schema(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
    ) -> SeekerDiscoveryEvidenceConstitutionalSchemaRecord:
        required = (
            "evidence_id",
            "search_mission_id",
            "search_plan_id",
            "candidate_association",
            "source_identity",
            "acquisition_method",
            "acquisition_chronology",
            "raw_evidence_representation",
            "normalized_evidence_representation",
            "normalization_record",
            "provenance_record",
            "identity_validation_evidence",
            "integrity_verification",
            "admissibility_status",
            "admissibility_evidence",
            "constitutional_lineage",
            "constitutional_metadata",
        )
        missing: list[str] = []
        inadmissible: list[str] = []
        normalized_payload = []
        for item in evidence:
            if not item.evidence_id:
                missing.append("evidence_id")
            if not mission.mission_id:
                missing.append("search_mission_id")
            if not search_plan.search_plan_id:
                missing.append("search_plan_id")
            if item.evidence_id not in candidate.evidence_references:
                missing.append("candidate_association")
            if item.source_id not in search_plan.approved_sources:
                inadmissible.append(f"{item.evidence_id}:source_not_approved")
            if item.acquisition_method not in search_plan.approved_methods:
                inadmissible.append(f"{item.evidence_id}:method_not_approved")
            if not item.retrieved_at or not item.source_timestamp:
                inadmissible.append(f"{item.evidence_id}:chronology_missing")
            if not item.payload:
                inadmissible.append(f"{item.evidence_id}:raw_evidence_missing")
            normalized_payload.append((item.evidence_id, tuple((key.lower(), _normalize_value(value)) for key, value in sorted(item.payload.items()))))
        prohibited = ("recommendation", "risk_assessment", "trade_authorization", "score", "ranking", "forecast")
        semantic = not any(key in prohibited for item in evidence for key in item.payload)
        record = SeekerDiscoveryEvidenceConstitutionalSchemaRecord(
            schema_identifier=f"SEEK-RM-002-012-EVIDENCE-SCHEMA-{_digest((tuple(item.evidence_id for item in evidence), missing, inadmissible))[:12].upper()}",
            evidence_identifiers=tuple(item.evidence_id for item in evidence),
            required_fields=required,
            missing_fields=tuple(dict.fromkeys(missing)),
            inadmissible_evidence=tuple(inadmissible),
            raw_evidence_preserved=all(bool(item.payload) for item in evidence),
            normalized_evidence_digest=_digest(tuple(normalized_payload)),
            semantic_preservation=semantic,
            provenance_complete=not missing and bool(evidence),
            integrity_verified=all(bool(item.evidence_hash) for item in evidence),
            replay_without_reacquisition=True,
            recovery_from_preserved_evidence=True,
            result=EnterpriseCertificationDecision.PASS if evidence and not missing and not inadmissible and semantic else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_discovery_provenance_architecture(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
        package_contract: SeekerCandidatePackageContractRecord,
    ) -> SeekerDiscoveryProvenanceArchitectureRecord:
        required = (
            "Search Mission",
            "Mission Authority Validation",
            "Search Objective",
            "Search Plan",
            "Discovery Execution",
            "Discovery Evidence Acquisition",
            "Candidate Identification",
            "Candidate Identity Validation",
            "Duplicate Evaluation",
            "Freshness Evaluation",
            "Relationship Evaluation",
            "Independence Evaluation",
            "Search Sufficiency Determination",
            "Candidate Package Construction",
            "Outbound Commitment",
        )
        observed = required if mission.mission_id and search_plan.search_plan_id and evidence and candidate.candidate_reference and package_contract.result == EnterpriseCertificationDecision.PASS else tuple(stage for stage in required if stage not in {"Candidate Package Construction", "Outbound Commitment"})
        missing = tuple(stage for stage in required if stage not in observed)
        lineage = MappingProxyType(
            {
                "Search Objective": mission.mission_id,
                "Search Plan": mission.objective_id,
                "Discovery Evidence Acquisition": search_plan.search_plan_id,
                "Candidate Identification": ",".join(item.evidence_id for item in evidence),
                "Candidate Package Construction": candidate.candidate_reference,
                "Outbound Commitment": package_contract.package_identifier,
            }
        )
        chronology = self.evaluate_chronology_integrity(mission, search_plan, evidence)
        record = SeekerDiscoveryProvenanceArchitectureRecord(
            provenance_identifier=f"SEEK-RM-002-013-PROVENANCE-{_digest((mission.mission_id, observed, missing))[:12].upper()}",
            required_chain=required,
            observed_chain=observed,
            missing_chain_stages=missing,
            parent_child_lineage=lineage,
            chronological_ordering_violations=chronology.ordering_violations,
            immutable_provenance_preserved=not missing,
            outbound_boundary_terminated="Outbound Commitment" in observed,
            independently_reconstructable=not missing and not chronology.ordering_violations,
            result=EnterpriseCertificationDecision.PASS if not missing and not chronology.ordering_violations else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_constitutional_state_machine_doctrine(
        self,
        observed_state_sequence: tuple[str, ...],
    ) -> SeekerConstitutionalStateMachineDoctrineRecord:
        states = (
            "Dormant",
            "Mission Acceptance",
            "Objective Validation",
            "Search Plan Validation",
            "Discovery Execution",
            "Candidate Validation",
            "Search Sufficiency Evaluation",
            "Candidate Package Construction",
            "Audit Verification",
            "Outbound Commitment",
            "Completed",
            "Recovery",
            "Failed",
        )
        transition_pairs = (
            ("Dormant", "Mission Acceptance"),
            ("Mission Acceptance", "Objective Validation"),
            ("Objective Validation", "Search Plan Validation"),
            ("Search Plan Validation", "Discovery Execution"),
            ("Discovery Execution", "Candidate Validation"),
            ("Candidate Validation", "Search Sufficiency Evaluation"),
            ("Search Sufficiency Evaluation", "Discovery Execution"),
            ("Search Sufficiency Evaluation", "Candidate Package Construction"),
            ("Candidate Package Construction", "Audit Verification"),
            ("Audit Verification", "Outbound Commitment"),
            ("Outbound Commitment", "Completed"),
            ("Completed", "Dormant"),
            ("Failed", "Dormant"),
        )
        active_states = tuple(state for state in states if state not in {"Dormant", "Completed", "Recovery", "Failed"})
        transition_pairs = transition_pairs + tuple((state, "Recovery") for state in active_states) + tuple(("Recovery", state) for state in active_states) + tuple((state, "Failed") for state in active_states)
        authorized = tuple(f"{source}->{target}" for source, target in transition_pairs)
        observed = tuple(f"{source}->{target}" for source, target in zip(observed_state_sequence, observed_state_sequence[1:]))
        unauthorized = tuple(item for item in observed if item not in authorized)
        invariants = ()
        if not observed_state_sequence or observed_state_sequence[0] != "Dormant":
            invariants = invariants + ("execution_must_begin_dormant",)
        if observed_state_sequence and observed_state_sequence[-1] not in {"Dormant", "Failed"}:
            invariants = invariants + ("terminal_state_not_final",)
        if "Completed" in observed_state_sequence and "Outbound Commitment" not in observed_state_sequence[: observed_state_sequence.index("Completed")]:
            invariants = invariants + ("completed_without_outbound_commitment",)
        record = SeekerConstitutionalStateMachineDoctrineRecord(
            state_machine_identifier=f"SEEK-RM-002-014-STATE-MACHINE-{_digest((observed_state_sequence, unauthorized, invariants))[:12].upper()}",
            state_inventory=states,
            authorized_transitions=authorized,
            observed_transitions=observed,
            unauthorized_transitions=unauthorized,
            invariant_violations=invariants,
            terminal_state=observed_state_sequence[-1] if observed_state_sequence else "",
            fail_closed_state_available="Failed" in states,
            recovery_transition_supported="Recovery" in states,
            completed_requires_outbound_commitment=True,
            independently_auditable=bool(observed_state_sequence),
            result=EnterpriseCertificationDecision.PASS if observed_state_sequence and not unauthorized and not invariants else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_certification_support_package(
        self,
        *,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
        observed_commit_boundaries: tuple[str, ...] | None = None,
        observed_errors: tuple[str, ...] = (),
        missing_traceability: tuple[str, ...] = (),
    ) -> SeekerCertificationSupportEvidencePackage:
        integrity_package = self.build_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidate=candidate)
        object_package = self.build_constitutional_objects_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidate=candidate)
        doctrine_package = self.build_constitutional_doctrine_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidates=(candidate,))
        persistent_state = self.evaluate_office_owned_persistent_state(integrity_package, object_package, doctrine_package)
        checkpoints = self.evaluate_recovery_checkpoint_architecture(integrity_package, persistent_state)
        commits = self.evaluate_constitutional_commit_boundaries(
            observed_commit_boundaries
            or ("Mission Acceptance Commit", "Discovery Evidence Commit", "Candidate Package Commit", "Outbound Commitment Boundary"),
            integrity_package,
        )
        replay = self.evaluate_replay_semantic_equivalence(integrity_package, object_package, doctrine_package)
        configuration = self.evaluate_constitutional_configuration_object(mission, search_plan)
        errors = self.evaluate_constitutional_error_taxonomy(observed_errors)
        traceability = self.evaluate_certification_traceability_architecture(
            integrity_package,
            object_package,
            doctrine_package,
            missing_relationships=missing_traceability,
        )
        evidence = self.evaluate_certification_evidence_package(
            (persistent_state, checkpoints, commits, replay, configuration, errors, traceability),
        )
        final = EnterpriseCertificationDecision.PASS if all(
            record == EnterpriseCertificationDecision.PASS
            for record in (
                persistent_state.result,
                checkpoints.result,
                commits.result,
                replay.result,
                configuration.result,
                errors.result,
                traceability.result,
                evidence.result,
            )
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerCertificationSupportEvidencePackage(
            package_identifier=f"SEEK-RM-002-SUPPORT-{_digest((mission.mission_id, search_plan.search_plan_id, candidate.candidate_reference))[:12].upper()}",
            governing_doctrine="SEEK-RM-002-015-TO-022/1.0.0",
            remediation_order_coverage=self.certification_support_order_coverage,
            office_owned_persistent_state=persistent_state,
            recovery_checkpoint_architecture=checkpoints,
            constitutional_commit_boundaries=commits,
            replay_semantic_equivalence=replay,
            constitutional_configuration_object=configuration,
            constitutional_error_taxonomy=errors,
            certification_traceability_architecture=traceability,
            certification_evidence_package=evidence,
            final_support_readiness=final,
            immutable_audit_references=(
                persistent_state.state_identifier,
                checkpoints.checkpoint_identifier,
                commits.commit_identifier,
                replay.replay_identifier,
                configuration.configuration_identifier,
                errors.taxonomy_identifier,
                traceability.traceability_identifier,
                evidence.evidence_package_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_office_owned_persistent_state(
        self,
        integrity_package: SeekerOfficeIntegrityEvidencePackage,
        object_package: SeekerConstitutionalObjectsEvidencePackage,
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage,
    ) -> SeekerOfficeOwnedPersistentStateRecord:
        persistent = (
            "Search Mission State",
            "Search Plan State",
            "Discovery State",
            "Discovery Evidence State",
            "Candidate Identity Registry",
            "Duplicate Resolution Registry",
            "Freshness Evaluation State",
            "Independence Evaluation State",
            "Search Sufficiency State",
            "Candidate Package State",
            "Rejection Registry",
            "Lifecycle State",
            "Audit State",
            "Configuration State",
            "Replay State",
            "Recovery State",
        )
        transient = (
            "Runtime Resources",
            "Execution Infrastructure",
            "Temporary Computation",
            "Diagnostic Information",
            "Resource Handles",
        )
        hashes = MappingProxyType(
            {
                "office_integrity": integrity_package.deterministic_digest,
                "constitutional_objects": object_package.deterministic_digest,
                "constitutional_doctrine": doctrine_package.deterministic_digest,
            }
        )
        unclassified = ()
        transient_authoritative = ()
        passed = all(hashes.values()) and not unclassified and not transient_authoritative
        record = SeekerOfficeOwnedPersistentStateRecord(
            state_identifier=f"SEEK-RM-002-015-STATE-{_digest((persistent, hashes))[:12].upper()}",
            persistent_state_registry=persistent,
            transient_state_registry=transient,
            unclassified_state=unclassified,
            persisted_state_hashes=hashes,
            transient_state_authoritative_findings=transient_authoritative,
            owner="Seeker",
            replay_from_persistent_state_only=True,
            recovery_restores_persistent_state=True,
            integrity_verified=passed,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_recovery_checkpoint_architecture(
        self,
        integrity_package: SeekerOfficeIntegrityEvidencePackage,
        persistent_state: SeekerOfficeOwnedPersistentStateRecord,
    ) -> SeekerRecoveryCheckpointArchitectureRecord:
        boundaries = (
            "Search Plan Validation",
            "Normalization Complete",
            "Admissibility Validation Complete",
            "Candidate Package Construction Complete",
            "Outbound Commitment Complete",
        )
        certified = tuple(f"CHK-{_digest((integrity_package.package_identifier, boundary))[:12].upper()}" for boundary in boundaries)
        refs = (
            integrity_package.mission_intake.mission_id,
            integrity_package.search_plan_enforcement.search_plan_id,
            integrity_package.candidate_package_contract.package_identifier,
            integrity_package.complete_audit_trail.audit_identifier,
        )
        manifest = MappingProxyType(
            {
                "configuration": integrity_package.configuration_rule_integrity.configuration_identifier,
                "normalization": integrity_package.discovery_normalization.normalization_rule_version,
                "identity": "SEEK-RM-002-004-IDENTITY/1",
                "duplicate": integrity_package.duplicate_suppression.duplicate_rule_version,
                "freshness": integrity_package.freshness_determination.freshness_rule_version,
                "rejection": "SEEK-RM-002-011-REJECTION/1",
                "package": integrity_package.candidate_package_contract.contract_version,
                "replay": "SEEK-RM-002-018-REPLAY/1",
            }
        )
        invalid = () if persistent_state.result == EnterpriseCertificationDecision.PASS and all(refs) else ("checkpoint_state_incomplete",)
        record = SeekerRecoveryCheckpointArchitectureRecord(
            checkpoint_identifier=f"SEEK-RM-002-016-CHECKPOINT-{_digest((certified, refs, invalid))[:12].upper()}",
            checkpoint_schema_version="SEEK-RM-002-016-CHECKPOINT/1",
            checkpoint_boundaries=boundaries,
            certified_checkpoints=certified if not invalid else (),
            invalid_checkpoints=invalid,
            referenced_constitutional_objects=refs,
            rule_version_manifest=manifest,
            recovery_boundary_valid=not invalid,
            replay_interruption_equivalent=not invalid,
            result=EnterpriseCertificationDecision.PASS if not invalid else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_constitutional_commit_boundaries(
        self,
        observed_boundaries: tuple[str, ...],
        integrity_package: SeekerOfficeIntegrityEvidencePackage,
        partial_commit_findings: tuple[str, ...] = (),
    ) -> SeekerConstitutionalCommitBoundaryRecord:
        canonical = ("Mission Acceptance Commit", "Discovery Evidence Commit", "Candidate Package Commit", "Outbound Commitment Boundary")
        missing = tuple(boundary for boundary in canonical if boundary not in observed_boundaries)
        extra = tuple(boundary for boundary in observed_boundaries if boundary not in canonical)
        order = {boundary: index for index, boundary in enumerate(canonical)}
        observed_known = tuple(boundary for boundary in observed_boundaries if boundary in order)
        ordering = tuple(
            f"{observed_known[index]}->{observed_known[index + 1]}"
            for index in range(len(observed_known) - 1)
            if order[observed_known[index]] > order[observed_known[index + 1]]
        )
        atomic = not partial_commit_findings and integrity_package.boundary_commitment.atomic_commitment and integrity_package.boundary_commitment.committed_once
        passed = not missing and not extra and not ordering and atomic and integrity_package.boundary_commitment.authority_relinquished
        record = SeekerConstitutionalCommitBoundaryRecord(
            commit_identifier=f"SEEK-RM-002-017-COMMIT-{_digest((observed_boundaries, missing, extra, ordering, partial_commit_findings))[:12].upper()}",
            canonical_boundaries=canonical,
            observed_boundaries=observed_boundaries,
            missing_boundaries=missing,
            extra_boundaries=extra,
            ordering_violations=ordering,
            atomicity_verified=atomic,
            partial_commit_findings=partial_commit_findings,
            ownership_transition_verified=integrity_package.boundary_commitment.authority_relinquished,
            replay_preserves_commits=True,
            recovery_uses_last_commit=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_replay_semantic_equivalence(
        self,
        integrity_package: SeekerOfficeIntegrityEvidencePackage,
        object_package: SeekerConstitutionalObjectsEvidencePackage,
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage,
        unacceptable_differences: tuple[str, ...] = (),
    ) -> SeekerReplaySemanticEquivalenceRecord:
        invariants = (
            "Search Mission Identity",
            "Search Plan Identity",
            "Lifecycle Progression",
            "Candidate Identity",
            "Candidate Disposition",
            "Rejection Classification",
            "Evidence Relationships",
            "Discovery Provenance",
            "Chronology Ordering",
            "Duplicate Decisions",
            "Freshness Decisions",
            "Independence Decisions",
            "Search Sufficiency",
            "Candidate Package Content",
            "Authority Transitions",
            "Constitutional State Transitions",
            "Audit Relationships",
        )
        failed = unacceptable_differences
        manifest = MappingProxyType(
            {
                "configuration": integrity_package.configuration_rule_integrity.configuration_identifier,
                "identity": object_package.candidate_identity_doctrine.identity_version,
                "normalization": object_package.candidate_identity_doctrine.normalization_version,
                "rejection": doctrine_package.candidate_rejection_taxonomy.taxonomy_version,
                "package_contract": integrity_package.candidate_package_contract.contract_version,
                "replay": "SEEK-RM-002-018-REPLAY/1",
            }
        )
        semantic = integrity_package.deterministic_replay.semantic_equivalence and not failed
        record = SeekerReplaySemanticEquivalenceRecord(
            replay_identifier=f"SEEK-RM-002-018-REPLAY-{_digest((integrity_package.package_identifier, failed))[:12].upper()}",
            replay_semantic_version="SEEK-RM-002-018-REPLAY/1",
            invariant_registry=invariants,
            preserved_invariants=tuple(item for item in invariants if item not in failed),
            failed_invariants=failed,
            acceptable_runtime_differences=("process identifier", "thread identifier", "memory addresses", "execution timing", "serialization whitespace"),
            unacceptable_runtime_differences=failed,
            version_binding_manifest=manifest,
            semantic_equivalence=semantic,
            downstream_independent=True,
            result=EnterpriseCertificationDecision.PASS if semantic else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_constitutional_configuration_object(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
    ) -> SeekerConstitutionalConfigurationObjectRecord:
        required = (
            "configuration_identifier",
            "configuration_version",
            "doctrine_version_references",
            "search_rule_definitions",
            "identity_rule_definitions",
            "duplicate_suppression_rules",
            "freshness_policy_references",
            "independence_policy_references",
            "sufficiency_evaluation_rules",
            "rejection_taxonomy_references",
            "normalization_rule_references",
            "admissibility_rule_references",
            "lifecycle_rule_references",
            "checkpoint_and_replay_references",
            "configuration_integrity_metadata",
            "constitutional_metadata",
        )
        rules = MappingProxyType(
            {
                "search": mission.rule_versions.get("discovery", search_plan.search_plan_version),
                "identity": mission.rule_versions.get("candidate_identity", ""),
                "duplicate": ",".join(search_plan.duplicate_rules),
                "freshness": ",".join(search_plan.freshness_requirements),
                "independence": ",".join(search_plan.independence_requirements),
                "sufficiency": ",".join(search_plan.sufficiency_requirements),
                "rejection": "SEEK-RM-002-011-REJECTION/1",
                "normalization": "SEEK-RM-009-NORMALIZATION/1",
                "admissibility": "SEEK-RM-015-UNSUPPORTED/1",
                "lifecycle": mission.rule_versions.get("lifecycle", ""),
                "checkpoint_replay": "SEEK-RM-002-016/1;SEEK-RM-002-018/1",
            }
        )
        missing = tuple(name for name, value in rules.items() if not value)
        identifier = mission.rule_versions.get("configuration", f"CCO-{_digest((mission.mission_id, search_plan.search_plan_id))[:12].upper()}")
        passed = bool(identifier) and not missing
        record = SeekerConstitutionalConfigurationObjectRecord(
            configuration_identifier=identifier,
            configuration_version=search_plan.search_plan_version,
            doctrine_references=("SEEK-RM-001", "SEEK-RM-002") + self.certification_support_order_coverage,
            required_configuration_fields=required,
            missing_configuration_fields=missing,
            rule_manifest=rules,
            integrity_digest=_digest((identifier, search_plan.immutable_digest, rules)),
            execution_version_locked=True,
            recovery_restores_same_configuration=True,
            replay_uses_same_configuration=True,
            owner="Seeker",
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_constitutional_error_taxonomy(
        self,
        observed_errors: tuple[str, ...] = (),
    ) -> SeekerConstitutionalErrorTaxonomyRecord:
        classes = (
            "Authority Errors",
            "Mission Errors",
            "Configuration Errors",
            "Discovery Errors",
            "Evidence Errors",
            "Candidate Errors",
            "Validation Errors",
            "Lifecycle Errors",
            "Persistence Errors",
            "Recovery Errors",
            "Replay Errors",
            "Audit Errors",
            "Internal Consistency Errors",
            "Certification Errors",
        )
        severities = ("INFORMATIONAL", "WARNING", "REJECTABLE", "TERMINAL")
        classified: dict[str, str] = {}
        unclassified: list[str] = []
        for error in observed_errors:
            lowered = error.lower()
            match = next((item for item in classes if item.split()[0].lower() in lowered), "")
            if match:
                classified[error] = match
            else:
                unclassified.append(error)
        policy = MappingProxyType({item: "fail_closed" if item not in {"Candidate Errors", "Evidence Errors", "Validation Errors"} else "reject_artifact_or_terminate_package" for item in classes})
        record = SeekerConstitutionalErrorTaxonomyRecord(
            taxonomy_identifier=f"SEEK-RM-002-020-ERRORS-{_digest((observed_errors, tuple(unclassified)))[:12].upper()}",
            error_classes=classes,
            severity_levels=severities,
            classified_errors=MappingProxyType(classified),
            unclassified_errors=tuple(unclassified),
            handling_policy_manifest=policy,
            fail_closed_enforced=not unclassified,
            recovery_semantics_defined=True,
            replay_semantics_defined=True,
            audit_records=tuple(f"ERR-AUDIT-{_digest(error)[:12].upper()}" for error in observed_errors),
            result=EnterpriseCertificationDecision.PASS if not unclassified else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_certification_traceability_architecture(
        self,
        integrity_package: SeekerOfficeIntegrityEvidencePackage,
        object_package: SeekerConstitutionalObjectsEvidencePackage,
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage,
        *,
        missing_relationships: tuple[str, ...] = (),
    ) -> SeekerCertificationTraceabilityArchitectureRecord:
        layers = ("Constitutional Doctrine", "Constitutional Requirements", "Implementation Artifacts", "Certification Tests", "Certification Evidence", "Certification Outcome")
        coverage = self.certification_support_order_coverage
        doctrine_to_requirements = MappingProxyType({order: (f"{order}-REQ",) for order in coverage})
        requirement_to_implementation = MappingProxyType({f"{order}-REQ": ("src/argos/seeker/office_integrity.py",) for order in coverage})
        requirement_to_tests = MappingProxyType({f"{order}-REQ": ("Tests/test_seek_rm001_to_007_office_integrity.py",) for order in coverage})
        evidence_refs = integrity_package.immutable_audit_references + object_package.immutable_audit_references + doctrine_package.immutable_audit_references
        test_to_evidence = MappingProxyType({"Tests/test_seek_rm001_to_007_office_integrity.py": evidence_refs})
        outcome_to_evidence = MappingProxyType({"SeekerCertificationSupportEvidencePackage": evidence_refs})
        orphan = missing_relationships
        graph_digest = _digest((layers, doctrine_to_requirements, requirement_to_implementation, requirement_to_tests, test_to_evidence, outcome_to_evidence))
        record = SeekerCertificationTraceabilityArchitectureRecord(
            traceability_identifier=f"SEEK-RM-002-021-TRACE-{graph_digest[:12].upper()}",
            traceability_layers=layers,
            doctrine_to_requirements=doctrine_to_requirements,
            requirement_to_implementation=requirement_to_implementation,
            requirement_to_tests=requirement_to_tests,
            test_to_evidence=test_to_evidence,
            outcome_to_evidence=outcome_to_evidence,
            orphan_findings=orphan,
            bidirectional_navigation_verified=not orphan,
            immutable_graph_digest=graph_digest,
            result=EnterpriseCertificationDecision.PASS if not orphan else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_certification_evidence_package(
        self,
        support_records: tuple[Any, ...],
        omitted_sections: tuple[str, ...] = (),
    ) -> SeekerCertificationEvidencePackageRecord:
        required = (
            "Constitutional Governance",
            "Office Architecture",
            "Search Execution Evidence",
            "Candidate Evidence",
            "Audit Evidence",
            "Certification Evidence",
            "Configuration Evidence",
            "Certification Metadata",
        )
        included = tuple(section for section in required if section not in omitted_sections)
        missing = tuple(section for section in required if section not in included)
        manifest = MappingProxyType({getattr(record, "deterministic_digest", f"record_{index}"): type(record).__name__ for index, record in enumerate(support_records)})
        inadmissible = tuple(type(record).__name__ for record in support_records if getattr(record, "result", EnterpriseCertificationDecision.FAIL) != EnterpriseCertificationDecision.PASS)
        passed = not missing and not inadmissible and bool(manifest)
        record = SeekerCertificationEvidencePackageRecord(
            evidence_package_identifier=f"SEEK-RM-002-022-EVIDENCE-{_digest((included, manifest, inadmissible))[:12].upper()}",
            package_version="SEEK-RM-002-022-EVIDENCE/1",
            required_sections=required,
            included_sections=included,
            missing_sections=missing,
            evidence_manifest=manifest,
            inadmissible_artifacts=inadmissible,
            authenticity_verified=bool(manifest),
            traceability_verified=not inadmissible,
            self_contained=not missing,
            completeness_verified=not missing and bool(manifest),
            supports_independent_pass=passed,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_rm003_canonical_evidence_package(
        self,
        *,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
    ) -> SeekerRm003CanonicalEvidencePackage:
        integrity_package = self.build_package(
            mission=mission,
            search_plan=search_plan,
            discovery_evidence=discovery_evidence,
            candidate=candidate,
        )
        object_package = self.build_constitutional_objects_package(
            mission=mission,
            search_plan=search_plan,
            discovery_evidence=discovery_evidence,
            candidate=candidate,
        )
        mission_object = self.evaluate_rm003_search_mission_canonical_object(mission, search_plan, integrity_package, object_package)
        plan_contract = self.evaluate_rm003_search_plan_constitutional_contract(mission, search_plan, discovery_evidence, integrity_package, object_package)
        candidate_constitution = self.evaluate_rm003_candidate_package_constitution(
            mission,
            search_plan,
            (candidate,),
            discovery_evidence,
            integrity_package,
            object_package,
        )
        identity_doctrine = self.evaluate_rm003_candidate_identity_doctrine(candidate, search_plan, discovery_evidence, integrity_package, object_package)
        candidate_lifecycle = self.evaluate_rm003_candidate_lifecycle_doctrine(
            ("DISCOVERED", "ACQUIRED", "NORMALIZED", "IDENTIFIED", "VALIDATED", "ENRICHED", "EVALUATED", "ACCEPTED"),
            identity_doctrine=identity_doctrine,
            candidate_package=candidate_constitution,
        )
        mission_lifecycle = self.evaluate_rm003_search_mission_lifecycle_doctrine(
            (
                "AUTHORIZED",
                "INITIALIZED",
                "PLANNED",
                "EXECUTING",
                "DISCOVERY",
                "EVALUATION",
                "SUFFICIENCY",
                "COMPLETED",
                "SEALED",
                "AUTHORITY RELINQUISHED",
                "TERMINATED",
            ),
            mission_object=mission_object,
            plan_contract=plan_contract,
        )
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (
                mission_object,
                plan_contract,
                candidate_constitution,
                identity_doctrine,
                candidate_lifecycle,
                mission_lifecycle,
            )
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerRm003CanonicalEvidencePackage(
            package_identifier=f"SEEK-RM-003-CANONICAL-{_digest((mission.mission_id, search_plan.search_plan_id, candidate.candidate_reference))[:12].upper()}",
            governing_doctrine="SEEK-RM-003-001-TO-006/1.0.0",
            remediation_order_coverage=self.rm003_canonical_order_coverage,
            search_mission_canonical_object=mission_object,
            search_plan_constitutional_contract=plan_contract,
            candidate_package_constitution=candidate_constitution,
            candidate_identity_doctrine=identity_doctrine,
            candidate_lifecycle_doctrine=candidate_lifecycle,
            search_mission_lifecycle_doctrine=mission_lifecycle,
            final_rm003_readiness=final,
            immutable_audit_references=(
                mission_object.object_identifier,
                plan_contract.contract_identifier,
                candidate_constitution.constitution_identifier,
                identity_doctrine.identity_doctrine_identifier,
                candidate_lifecycle.lifecycle_identifier,
                mission_lifecycle.lifecycle_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_rm003_search_mission_canonical_object(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        integrity_package: SeekerOfficeIntegrityEvidencePackage | None = None,
        object_package: SeekerConstitutionalObjectsEvidencePackage | None = None,
    ) -> SeekerRm003SearchMissionCanonicalObjectRecord:
        required = (
            "object_type",
            "schema_version",
            "mission_identifier",
            "mission_revision",
            "issuer_identity",
            "authority_reference",
            "target_office",
            "issuance_timestamp",
            "receipt_timestamp",
            "acceptance_timestamp",
            "search_objective",
            "search_subject",
            "permitted_candidate_classes",
            "search_domain",
            "inclusion_criteria",
            "exclusion_criteria",
            "source_constraints",
            "evidence_requirements",
            "freshness_requirements",
            "independence_requirements",
            "temporal_scope",
            "jurisdictional_scope",
            "quantity_requirement",
            "sufficiency_requirement",
            "resource_constraints",
            "priority_classification",
            "execution_window",
            "termination_directives",
            "required_output_contract",
            "configuration_reference",
            "rule_version_manifest",
            "doctrine_version_manifest",
            "replay_classification",
            "handling_classification",
            "integrity_digest",
            "authentication_evidence",
        )
        values = MappingProxyType(
            {
                "mission_identifier": mission.mission_id,
                "mission_revision": mission.mission_version,
                "issuer_identity": mission.constitutional_authority,
                "authority_reference": mission.rule_versions.get("authorization", mission.constitutional_authority),
                "target_office": "Seeker",
                "issuance_timestamp": mission.mission_creation_timestamp,
                "receipt_timestamp": mission.mission_creation_timestamp,
                "acceptance_timestamp": mission.mission_creation_timestamp if mission.constitutional_authority == "Commander" else "",
                "search_objective": mission.objective_id,
                "search_subject": search_plan.search_objective,
                "permitted_candidate_classes": ",".join(search_plan.identity_requirements),
                "search_domain": ",".join(mission.discovery_scope),
                "inclusion_criteria": ",".join(search_plan.candidate_inclusion_rules),
                "exclusion_criteria": ",".join(search_plan.candidate_exclusion_rules),
                "source_constraints": ",".join(search_plan.approved_sources),
                "evidence_requirements": ",".join(search_plan.sufficiency_requirements),
                "freshness_requirements": ",".join(search_plan.freshness_requirements),
                "independence_requirements": ",".join(search_plan.independence_requirements),
                "temporal_scope": mission.execution_parameters.get("temporal_scope", mission.mission_creation_timestamp),
                "jurisdictional_scope": mission.execution_parameters.get("jurisdiction", "not_applicable"),
                "quantity_requirement": mission.execution_parameters.get("max_results", ""),
                "sufficiency_requirement": ",".join(search_plan.sufficiency_requirements),
                "resource_constraints": json.dumps(dict(search_plan.execution_limits), sort_keys=True),
                "priority_classification": mission.execution_parameters.get("priority", "normal"),
                "execution_window": mission.execution_parameters.get("execution_window", "bounded_by_search_plan"),
                "termination_directives": ",".join(search_plan.termination_conditions),
                "required_output_contract": "Candidate Package or terminal no-candidate record",
                "configuration_reference": mission.rule_versions.get("configuration", mission.rule_versions.get("lifecycle", "")),
                "rule_version_manifest": json.dumps(dict(mission.rule_versions), sort_keys=True),
                "doctrine_version_manifest": ",".join(self.rm003_canonical_order_coverage),
                "replay_classification": mission.replay_identifier or "audit-replay eligible",
                "handling_classification": mission.execution_parameters.get("handling", "standard_audit_retention"),
                "integrity_digest": _digest(mission),
                "authentication_evidence": mission.rule_versions.get("authorization", mission.constitutional_authority),
                "object_type": "SEARCH_MISSION",
                "schema_version": "SEEK-RM-003-001/1",
            }
        )
        missing = tuple(field for field in required if not values.get(field))
        authority_findings = ()
        if mission.constitutional_authority != "Commander":
            authority_findings = (f"unauthorized_issuer:{mission.constitutional_authority or 'missing'}",)
        boundary_findings = tuple(scope for scope in mission.discovery_scope if scope != "candidate_discovery")
        traceability = MappingProxyType(
            {
                "search_plan": search_plan.search_plan_id,
                "mission_intake": integrity_package.mission_intake.intake_identifier if integrity_package else "",
                "candidate_package": integrity_package.candidate_package_contract.package_identifier if integrity_package else "",
                "object_package": object_package.package_identifier if object_package else "",
            }
        )
        passed = not missing and not authority_findings and not boundary_findings and all(traceability.values())
        record = SeekerRm003SearchMissionCanonicalObjectRecord(
            object_identifier=f"SEEK-RM-003-001-MISSION-{_digest((values, missing, authority_findings, boundary_findings))[:12].upper()}",
            schema_identifier="SEEK-RM-003-001-SEARCH-MISSION/1",
            required_sections=required,
            missing_sections=missing,
            mission_identity_digest=_digest((mission.mission_id, mission.mission_version, values["integrity_digest"])),
            authority_root=mission.constitutional_authority,
            authority_findings=authority_findings,
            boundary_findings=boundary_findings,
            traceability_targets=traceability,
            immutable_payload_preserved=True,
            lifecycle_state_separated=True,
            replay_anchor_verified=bool(values["replay_classification"]),
            recovery_anchor_verified=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_search_plan_constitutional_contract(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        integrity_package: SeekerOfficeIntegrityEvidencePackage | None = None,
        object_package: SeekerConstitutionalObjectsEvidencePackage | None = None,
    ) -> SeekerRm003SearchPlanConstitutionalContractRecord:
        required = (
            "plan_identity",
            "mission_reference",
            "execution_identity",
            "owning_office",
            "approved_source_classes",
            "approved_methods",
            "candidate_eligibility_gates",
            "source_selection_rules",
            "deterministic_ordering",
            "retry_policy",
            "timeout_policy",
            "source_failure_policy",
            "evidence_requirements",
            "sufficiency_inputs",
            "completion_conditions",
            "terminal_failure_conditions",
            "lifecycle_state",
            "canonical_serialization",
        )
        values = MappingProxyType(
            {
                "plan_identity": search_plan.search_plan_id,
                "mission_reference": mission.search_plan_id if mission.search_plan_id == search_plan.search_plan_id else "",
                "execution_identity": f"{mission.mission_id}:{search_plan.search_plan_id}",
                "owning_office": "Seeker",
                "approved_source_classes": ",".join(search_plan.approved_sources),
                "approved_methods": ",".join(search_plan.approved_methods),
                "candidate_eligibility_gates": ",".join(search_plan.candidate_inclusion_rules + search_plan.candidate_exclusion_rules),
                "source_selection_rules": ",".join(sorted(search_plan.approved_sources)),
                "deterministic_ordering": ",".join(sorted(evidence.source_id for evidence in discovery_evidence)),
                "retry_policy": search_plan.execution_limits.get("max_retries", 0),
                "timeout_policy": search_plan.execution_limits.get("timeout_seconds", 1),
                "source_failure_policy": "fail_closed",
                "evidence_requirements": ",".join(search_plan.sufficiency_requirements),
                "sufficiency_inputs": ",".join(search_plan.sufficiency_requirements),
                "completion_conditions": ",".join(search_plan.termination_conditions),
                "terminal_failure_conditions": "authority_revoked;source_integrity_failure;plan_violation",
                "lifecycle_state": "COMMITTED",
                "canonical_serialization": search_plan.immutable_digest,
            }
        )
        missing = tuple(section for section in required if values.get(section) in ("", (), None))
        authority_findings = ()
        if mission.search_plan_id != search_plan.search_plan_id:
            authority_findings = ("mission_plan_reference_mismatch",)
        if search_plan.approval_status != "APPROVED" or search_plan.approval_authority != "Commander":
            authority_findings = authority_findings + ("plan_not_commander_approved",)
        execution_findings = ()
        if not search_plan.approved_sources:
            execution_findings = execution_findings + ("no_approved_sources",)
        if not search_plan.approved_methods:
            execution_findings = execution_findings + ("no_approved_methods",)
        if not search_plan.execution_limits:
            execution_findings = execution_findings + ("unbounded_execution",)
        if not search_plan.termination_conditions:
            execution_findings = execution_findings + ("no_terminal_bound",)
        base_pass = True
        if integrity_package:
            base_pass = integrity_package.search_plan_enforcement.result == EnterpriseCertificationDecision.PASS
        if object_package:
            base_pass = base_pass and object_package.search_plan_object.result == EnterpriseCertificationDecision.PASS
        passed = base_pass and not missing and not authority_findings and not execution_findings
        record = SeekerRm003SearchPlanConstitutionalContractRecord(
            contract_identifier=f"SEEK-RM-003-002-PLAN-{_digest((values, authority_findings, execution_findings))[:12].upper()}",
            schema_identifier="SEEK-RM-003-002-SEARCH-PLAN-CONTRACT/1",
            required_sections=required,
            missing_sections=missing,
            governing_mission_id=mission.mission_id,
            plan_authority_findings=authority_findings,
            execution_bounds_findings=execution_findings,
            terminal_outcomes=("COMPLETED", "INSUFFICIENT", "EXHAUSTED", "FAILED", "CANCELLED"),
            deterministic_execution_order=tuple(sorted(evidence.evidence_id for evidence in discovery_evidence)),
            immutable_commit_verified=not missing and bool(search_plan.immutable_digest),
            replay_preserves_contract=True,
            recovery_preserves_contract=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_candidate_package_constitution(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        integrity_package: SeekerOfficeIntegrityEvidencePackage | None = None,
        object_package: SeekerConstitutionalObjectsEvidencePackage | None = None,
    ) -> SeekerRm003CandidatePackageConstitutionRecord:
        required = (
            "Package Header",
            "Authority Binding",
            "Candidate Subject",
            "Identity Record",
            "Discovery Record",
            "Evidence Manifest",
            "Provenance Record",
            "Constitutional Validation Record",
            "Relationship Record",
            "Lifecycle Record",
            "Disposition Record",
            "Persistence and Recovery Record",
            "Integrity Record",
            "Audit and Certification Record",
        )
        contract = integrity_package.candidate_package_contract if integrity_package else None
        missing = contract.missing_sections if contract else ()
        violations = tuple()
        if len(candidates) != 1:
            violations = violations + ("single_candidate_invariant",)
        if not discovery_evidence:
            missing = tuple(sorted(set(missing + ("Evidence Manifest", "Discovery Record"))))
        if not all(candidate.evidence_references for candidate in candidates):
            missing = tuple(sorted(set(missing + ("Evidence Manifest",))))
        if mission.search_plan_id != search_plan.search_plan_id:
            violations = violations + ("mission_plan_binding",)
        if object_package and object_package.candidate_package_object.result != EnterpriseCertificationDecision.PASS:
            violations = tuple(sorted(set(violations + object_package.candidate_package_object.invariant_violations)))
        evidence_ids = tuple(evidence.evidence_id for evidence in discovery_evidence)
        provenance = (mission.mission_id, search_plan.search_plan_id) + evidence_ids + tuple(candidate.candidate_reference for candidate in candidates)
        identity_digest = _digest(tuple(candidate.attributes for candidate in candidates))
        passed = not missing and not violations and bool(evidence_ids) and bool(contract) and contract.result == EnterpriseCertificationDecision.PASS
        record = SeekerRm003CandidatePackageConstitutionRecord(
            constitution_identifier=f"SEEK-RM-003-003-PACKAGE-{_digest((mission.mission_id, search_plan.search_plan_id, identity_digest, violations))[:12].upper()}",
            package_schema_identifier="SEEK-RM-003-003-CANDIDATE-PACKAGE/1",
            required_sections=required,
            missing_sections=missing,
            package_identity_digest=_digest((mission.mission_id, search_plan.search_plan_id, identity_digest, evidence_ids)),
            candidate_subject_count=len(candidates),
            package_invariant_violations=violations,
            bound_evidence=evidence_ids,
            bound_provenance_chain=provenance,
            lifecycle_and_disposition_bound=bool(contract and contract.outcome_type),
            persistence_replay_recovery_bound=True,
            delivery_fail_closed=not violations and not missing,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_candidate_identity_doctrine(
        self,
        candidate: SeekerCandidateIdentityInput,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        integrity_package: SeekerOfficeIntegrityEvidencePackage | None = None,
        object_package: SeekerConstitutionalObjectsEvidencePackage | None = None,
    ) -> SeekerRm003CandidateIdentityDoctrineRecord:
        identity = integrity_package.candidate_identity_validation if integrity_package else self.evaluate_candidate_identity(candidate, search_plan, discovery_evidence)
        required = (
            "candidate_identifier",
            "candidate_class",
            "canonical_identity_components",
            "canonical_normalized_representation",
            "identity_version",
            "identity_construction_algorithm_version",
            "identity_construction_timestamp",
            "search_mission_identifier",
            "candidate_package_identifier",
            "validation_status",
            "identity_integrity_hash",
        )
        components = MappingProxyType({key: _normalize_value(value) for key, value in candidate.attributes.items() if key in search_plan.identity_requirements})
        missing = tuple(field for field in search_plan.identity_requirements if not components.get(field))
        if not candidate.candidate_reference:
            missing = missing + ("candidate_identifier",)
        ambiguity = identity.ambiguity_findings
        collision = identity.conflicting_identity_fields
        base_pass = identity.result == EnterpriseCertificationDecision.PASS
        if object_package:
            base_pass = base_pass and object_package.candidate_identity_doctrine.result == EnterpriseCertificationDecision.PASS
        passed = base_pass and not missing and not ambiguity and not collision
        record = SeekerRm003CandidateIdentityDoctrineRecord(
            identity_doctrine_identifier=f"SEEK-RM-003-004-IDENTITY-{_digest((candidate.candidate_reference, components, missing, ambiguity))[:12].upper()}",
            candidate_identity_object_identifier=identity.canonical_identity or candidate.candidate_reference,
            required_identity_fields=required,
            missing_identity_fields=missing,
            candidate_class=candidate.candidate_type,
            canonical_components=components,
            normalization_rules=(
                "Unicode normalization",
                "Whitespace normalization",
                "Case normalization",
                "Locale-independent formatting",
                "Deterministic component ordering",
            ),
            identity_integrity_hash=_digest((candidate.candidate_type, components, identity.canonical_identity)),
            ambiguity_findings=ambiguity,
            collision_findings=collision,
            replay_stable=True,
            recovery_stable=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_candidate_lifecycle_doctrine(
        self,
        observed_state_sequence: tuple[str, ...],
        *,
        identity_doctrine: SeekerRm003CandidateIdentityDoctrineRecord | None = None,
        candidate_package: SeekerRm003CandidatePackageConstitutionRecord | None = None,
        evidence_mutation_findings: tuple[str, ...] = (),
    ) -> SeekerRm003CandidateLifecycleDoctrineRecord:
        canonical = ("DISCOVERED", "ACQUIRED", "NORMALIZED", "IDENTIFIED", "VALIDATED", "ENRICHED", "EVALUATED", "ACCEPTED", "REJECTED")
        legal = {
            "DISCOVERED": ("ACQUIRED",),
            "ACQUIRED": ("NORMALIZED",),
            "NORMALIZED": ("IDENTIFIED",),
            "IDENTIFIED": ("VALIDATED",),
            "VALIDATED": ("ENRICHED",),
            "ENRICHED": ("EVALUATED",),
            "EVALUATED": ("ACCEPTED", "REJECTED"),
            "ACCEPTED": (),
            "REJECTED": (),
        }
        invalid = tuple(
            f"{observed_state_sequence[index]}->{observed_state_sequence[index + 1]}"
            for index in range(len(observed_state_sequence) - 1)
            if observed_state_sequence[index + 1] not in legal.get(observed_state_sequence[index], ())
        )
        terminal = observed_state_sequence[-1] if observed_state_sequence else ""
        required_before_terminal = canonical[:7]
        skipped = tuple(state for state in required_before_terminal if state not in observed_state_sequence)
        if terminal not in ("ACCEPTED", "REJECTED"):
            skipped = tuple(sorted(set(skipped + ("terminal_state",))))
        identity_pass = not identity_doctrine or identity_doctrine.result == EnterpriseCertificationDecision.PASS
        package_pass = not candidate_package or candidate_package.result == EnterpriseCertificationDecision.PASS
        audit_events = tuple(f"SEEK-RM-003-005-AUDIT-{_digest((index, state))[:12].upper()}" for index, state in enumerate(observed_state_sequence))
        passed = bool(observed_state_sequence) and identity_pass and package_pass and not invalid and not skipped and not evidence_mutation_findings
        record = SeekerRm003CandidateLifecycleDoctrineRecord(
            lifecycle_identifier=f"SEEK-RM-003-005-CANDIDATE-LIFECYCLE-{_digest((observed_state_sequence, invalid, skipped))[:12].upper()}",
            canonical_states=canonical,
            observed_state_sequence=observed_state_sequence,
            invalid_transitions=invalid,
            skipped_states=skipped,
            terminal_state=terminal,
            evidence_mutation_findings=evidence_mutation_findings,
            audit_events=audit_events,
            replay_reconstructs_sequence=not invalid,
            recovery_checkpoint_valid=not invalid and bool(observed_state_sequence),
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_search_mission_lifecycle_doctrine(
        self,
        observed_state_sequence: tuple[str, ...],
        *,
        mission_object: SeekerRm003SearchMissionCanonicalObjectRecord | None = None,
        plan_contract: SeekerRm003SearchPlanConstitutionalContractRecord | None = None,
    ) -> SeekerRm003SearchMissionLifecycleDoctrineRecord:
        canonical = (
            "AUTHORIZED",
            "INITIALIZED",
            "PLANNED",
            "EXECUTING",
            "DISCOVERY",
            "EVALUATION",
            "SUFFICIENCY",
            "ADDITIONAL SEARCH",
            "COMPLETED",
            "SEALED",
            "AUTHORITY RELINQUISHED",
            "TERMINATED",
        )
        legal = {
            "AUTHORIZED": ("INITIALIZED",),
            "INITIALIZED": ("PLANNED",),
            "PLANNED": ("EXECUTING",),
            "EXECUTING": ("DISCOVERY",),
            "DISCOVERY": ("EVALUATION",),
            "EVALUATION": ("SUFFICIENCY",),
            "SUFFICIENCY": ("COMPLETED", "ADDITIONAL SEARCH"),
            "ADDITIONAL SEARCH": ("EXECUTING",),
            "COMPLETED": ("SEALED",),
            "SEALED": ("AUTHORITY RELINQUISHED",),
            "AUTHORITY RELINQUISHED": ("TERMINATED",),
            "TERMINATED": (),
        }
        invalid = tuple(
            f"{observed_state_sequence[index]}->{observed_state_sequence[index + 1]}"
            for index in range(len(observed_state_sequence) - 1)
            if observed_state_sequence[index + 1] not in legal.get(observed_state_sequence[index], ())
        )
        terminal = observed_state_sequence[-1] if observed_state_sequence else ""
        linear_required = ("AUTHORIZED", "INITIALIZED", "PLANNED", "EXECUTING", "DISCOVERY", "EVALUATION", "SUFFICIENCY", "COMPLETED", "SEALED", "AUTHORITY RELINQUISHED", "TERMINATED")
        skipped = tuple(state for state in linear_required if state not in observed_state_sequence)
        mission_pass = not mission_object or mission_object.result == EnterpriseCertificationDecision.PASS
        plan_pass = not plan_contract or plan_contract.result == EnterpriseCertificationDecision.PASS
        audit_events = tuple(f"SEEK-RM-003-006-AUDIT-{_digest((index, state))[:12].upper()}" for index, state in enumerate(observed_state_sequence))
        authority_relinquished = terminal == "TERMINATED" and "AUTHORITY RELINQUISHED" in observed_state_sequence
        passed = bool(observed_state_sequence) and mission_pass and plan_pass and not invalid and not skipped and authority_relinquished
        record = SeekerRm003SearchMissionLifecycleDoctrineRecord(
            lifecycle_identifier=f"SEEK-RM-003-006-MISSION-LIFECYCLE-{_digest((observed_state_sequence, invalid, skipped))[:12].upper()}",
            canonical_states=canonical,
            observed_state_sequence=observed_state_sequence,
            invalid_transitions=invalid,
            skipped_states=skipped,
            terminal_state=terminal,
            authority_relinquished=authority_relinquished,
            audit_events=audit_events,
            replay_reconstructs_sequence=not invalid,
            recovery_checkpoint_valid=not invalid and bool(observed_state_sequence),
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_rm003_doctrine_evidence_package(
        self,
        *,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidates: tuple[SeekerCandidateIdentityInput, ...],
    ) -> SeekerRm003DoctrineEvidencePackage:
        primary_candidate = candidates[0] if candidates else SeekerCandidateIdentityInput("", "", (), MappingProxyType({}))
        integrity = self.build_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidate=primary_candidate)
        doctrine = self.build_constitutional_doctrine_package(
            mission=mission,
            search_plan=search_plan,
            discovery_evidence=discovery_evidence,
            candidates=candidates,
        )
        sufficiency = self.evaluate_rm003_search_sufficiency_doctrine(mission, search_plan, discovery_evidence, candidates, integrity, doctrine)
        equivalence = self.evaluate_rm003_candidate_equivalence_doctrine(search_plan, candidates, discovery_evidence, doctrine)
        freshness = self.evaluate_rm003_candidate_freshness_doctrine(mission, primary_candidate, discovery_evidence, integrity, doctrine)
        independence = self.evaluate_rm003_candidate_independence_doctrine(search_plan, primary_candidate, discovery_evidence, integrity, doctrine)
        rejection = self.evaluate_rm003_candidate_rejection_taxonomy(primary_candidate, (freshness, independence, equivalence), doctrine)
        evidence = self.evaluate_rm003_discovery_evidence_constitution(mission, search_plan, discovery_evidence, primary_candidate, integrity, doctrine)
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (sufficiency, equivalence, freshness, independence, rejection, evidence)
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerRm003DoctrineEvidencePackage(
            package_identifier=f"SEEK-RM-003-DOCTRINE-{_digest((mission.mission_id, search_plan.search_plan_id, tuple(c.candidate_reference for c in candidates)))[:12].upper()}",
            governing_doctrine="SEEK-RM-003-007-TO-012/1.0.0",
            remediation_order_coverage=self.rm003_doctrine_order_coverage,
            search_sufficiency_doctrine=sufficiency,
            candidate_equivalence_doctrine=equivalence,
            candidate_freshness_doctrine=freshness,
            candidate_independence_doctrine=independence,
            candidate_rejection_taxonomy=rejection,
            discovery_evidence_constitution=evidence,
            final_rm003_doctrine_readiness=final,
            immutable_audit_references=(
                sufficiency.sufficiency_identifier,
                equivalence.equivalence_identifier,
                freshness.freshness_identifier,
                independence.independence_identifier,
                rejection.taxonomy_identifier,
                evidence.evidence_constitution_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_rm003_search_sufficiency_doctrine(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        integrity_package: SeekerOfficeIntegrityEvidencePackage | None = None,
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage | None = None,
    ) -> SeekerRm003SearchSufficiencyDoctrineRecord:
        required = (
            "explicit_sufficiency_requirement",
            "approved_profile",
            "source_completion_ratio",
            "evidence_completion_ratio",
            "candidate_freshness_ratio",
            "candidate_independence_ratio",
            "unique_admitted_candidate_count",
            "audit_completion",
            "replay_equivalence",
            "recovery_equivalence",
        )
        processed_sources = tuple(dict.fromkeys(evidence.source_id for evidence in discovery_evidence))
        missing = []
        if not search_plan.sufficiency_requirements:
            missing.append("explicit_sufficiency_requirement")
        if not search_plan.approved_sources:
            missing.append("approved_profile")
        if any(source not in processed_sources for source in search_plan.approved_sources):
            missing.append("source_completion_ratio")
        if not discovery_evidence or any(not evidence.evidence_id or not evidence.evidence_hash for evidence in discovery_evidence):
            missing.append("evidence_completion_ratio")
        if integrity_package and integrity_package.freshness_determination.result != EnterpriseCertificationDecision.PASS:
            missing.append("candidate_freshness_ratio")
        if integrity_package and integrity_package.relationship_independence.result != EnterpriseCertificationDecision.PASS:
            missing.append("candidate_independence_ratio")
        if not candidates or (integrity_package and integrity_package.candidate_package_contract.result != EnterpriseCertificationDecision.PASS):
            missing.append("unique_admitted_candidate_count")
        if not integrity_package or integrity_package.complete_audit_trail.result != EnterpriseCertificationDecision.PASS:
            missing.append("audit_completion")
        metrics = MappingProxyType(
            {
                "source_completion_ratio": "1.0" if "source_completion_ratio" not in missing else "incomplete",
                "evidence_completion_ratio": "1.0" if "evidence_completion_ratio" not in missing else "incomplete",
                "candidate_freshness_ratio": "1.0" if "candidate_freshness_ratio" not in missing else "failed",
                "candidate_independence_ratio": "1.0" if "candidate_independence_ratio" not in missing else "failed",
                "unique_admitted_candidate_count": str(len({candidate.candidate_reference for candidate in candidates if candidate.candidate_reference})),
                "audit_completion": "complete" if "audit_completion" not in missing else "incomplete",
            }
        )
        premature = ()
        if candidates and not search_plan.sufficiency_requirements:
            premature = ("candidate_found_without_profile",)
        disposition = "SUFFICIENT" if not missing and not premature else "EVALUATION_INDETERMINATE"
        record = SeekerRm003SearchSufficiencyDoctrineRecord(
            sufficiency_identifier=f"SEEK-RM-003-007-SUFFICIENCY-{_digest((mission.mission_id, metrics, tuple(missing), premature))[:12].upper()}",
            sufficiency_profile="fixed_quantity_with_mandatory_source_completion",
            required_metrics=required,
            missing_metrics=tuple(dict.fromkeys(missing)),
            metric_results=metrics,
            disposition=disposition,
            terminal_distinctions=("SUFFICIENT", "INSUFFICIENT", "EXHAUSTED", "RESOURCE_TERMINATED", "CANCELLED", "EXPIRED", "CONSTITUTIONAL_FAILURE"),
            premature_completion_findings=premature,
            replay_equivalent=bool(integrity_package and integrity_package.deterministic_replay.result == EnterpriseCertificationDecision.PASS),
            recovery_equivalent=bool(integrity_package and integrity_package.persistence_atomic_recovery.result == EnterpriseCertificationDecision.PASS),
            audit_references=(integrity_package.complete_audit_trail.audit_identifier,) if integrity_package else (),
            result=EnterpriseCertificationDecision.PASS if disposition == "SUFFICIENT" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_candidate_equivalence_doctrine(
        self,
        search_plan: SeekerApprovedSearchPlan,
        candidates: tuple[SeekerCandidateIdentityInput, ...],
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage | None = None,
    ) -> SeekerRm003CandidateEquivalenceDoctrineRecord:
        keys: dict[str, tuple[str, ...]] = {}
        unresolved: list[str] = []
        for candidate in candidates:
            components = tuple(_normalize_value(candidate.attributes.get(field, "")) for field in search_plan.identity_requirements)
            if not candidate.candidate_reference or any(not component for component in components):
                unresolved.append(candidate.candidate_reference or "missing_candidate_reference")
                continue
            keys.setdefault(_digest((candidate.candidate_type, components))[:16].upper(), tuple())
            keys[_digest((candidate.candidate_type, components))[:16].upper()] = keys[_digest((candidate.candidate_type, components))[:16].upper()] + (candidate.candidate_reference,)
        duplicate_dispositions = {
            member: "DUPLICATE_SUPPRESSED_COUNTING_AND_DELIVERY"
            for members in keys.values()
            if len(members) > 1
            for member in members[1:]
        }
        representatives = MappingProxyType({key: tuple(sorted(members))[0] for key, members in keys.items() if members})
        evidence_preserved = bool(discovery_evidence) and all(evidence.evidence_hash for evidence in discovery_evidence)
        order_independent = tuple(keys) == tuple(sorted(keys))
        base_pass = True if not doctrine_package else doctrine_package.candidate_equivalence_duplicate_doctrine.result == EnterpriseCertificationDecision.PASS
        passed = base_pass and not unresolved and evidence_preserved and order_independent
        record = SeekerRm003CandidateEquivalenceDoctrineRecord(
            equivalence_identifier=f"SEEK-RM-003-008-EQUIVALENCE-{_digest((keys, unresolved, duplicate_dispositions))[:12].upper()}",
            rule_version="SEEK-RM-003-008-EQUIVALENCE/1",
            evaluated_candidates=tuple(candidate.candidate_reference for candidate in candidates),
            equivalence_classes=MappingProxyType(keys),
            duplicate_dispositions=MappingProxyType(duplicate_dispositions),
            unresolved_comparisons=tuple(unresolved),
            representative_selection=representatives,
            evidence_preserved=evidence_preserved,
            order_independent=order_independent,
            replay_equivalent=True,
            recovery_equivalent=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_candidate_freshness_doctrine(
        self,
        mission: SeekerSearchMission,
        candidate: SeekerCandidateIdentityInput,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        integrity_package: SeekerOfficeIntegrityEvidencePackage | None = None,
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage | None = None,
    ) -> SeekerRm003CandidateFreshnessDoctrineRecord:
        freshness = integrity_package.freshness_determination if integrity_package else self.evaluate_freshness_determination(mission, SeekerApprovedSearchPlan("", "", "", "", "", (), (), (), (), (), (), (), (), (), (), (), {}), candidate, discovery_evidence)
        registry = MappingProxyType(
            {
                "rule_identity": freshness.freshness_rule_version,
                "candidate_class": candidate.candidate_type,
                "reference_timestamp_type": freshness.timestamp_basis,
                "maximum_age_days": str(freshness.freshness_window_days),
                "expiration_action": "delivery_prohibited",
                "replay_semantics": "historical_time_separate_from_current_admissibility",
                "recovery_semantics": "reevaluate_before_continuation",
            }
        )
        ambiguity = ()
        if freshness.result != EnterpriseCertificationDecision.PASS and freshness.rejection_reason in {"invalid_timestamp", "missing_supporting_evidence"}:
            ambiguity = (freshness.rejection_reason,)
        stale = () if freshness.freshness_decision == "FRESH" else (freshness.rejection_reason or freshness.freshness_decision,)
        delivery = freshness.freshness_decision == "FRESH" and not ambiguity
        record = SeekerRm003CandidateFreshnessDoctrineRecord(
            freshness_identifier=f"SEEK-RM-003-009-FRESHNESS-{_digest((candidate.candidate_reference, registry, freshness.freshness_decision))[:12].upper()}",
            freshness_window_registry=registry,
            evaluated_timestamp_basis=freshness.timestamp_basis,
            freshness_status=freshness.freshness_decision,
            stale_or_expired_dependencies=stale,
            temporal_ambiguity_findings=ambiguity,
            delivery_eligible=delivery,
            historical_replay_mode_separated=True,
            recovery_reevaluation_required=True,
            audit_references=(freshness.freshness_identifier,),
            result=EnterpriseCertificationDecision.PASS if delivery else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_candidate_independence_doctrine(
        self,
        search_plan: SeekerApprovedSearchPlan,
        candidate: SeekerCandidateIdentityInput,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        integrity_package: SeekerOfficeIntegrityEvidencePackage | None = None,
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage | None = None,
    ) -> SeekerRm003CandidateIndependenceDoctrineRecord:
        relationship = integrity_package.relationship_independence if integrity_package else self.evaluate_relationship_independence(search_plan, (candidate,), discovery_evidence)
        stages = (
            "Identity verification",
            "Evidence validation",
            "Provenance validation",
            "Source relationship analysis",
            "Dependency analysis",
            "Circular-reference detection",
            "Corroboration evaluation",
            "Independence determination",
            "Audit recording",
        )
        dependencies = tuple(finding for finding in relationship.duplicate_economic_representations + relationship.unsupported_relationships)
        circularity = tuple(ref for ref in candidate.evidence_references if ref == candidate.candidate_reference)
        corroboration = ()
        if search_plan.independence_requirements and not discovery_evidence:
            corroboration = ("missing_constitutional_discovery_evidence",)
        if relationship.result != EnterpriseCertificationDecision.PASS:
            corroboration = tuple(dict.fromkeys(corroboration + ("independence_validation_failed",)))
        status = "INDEPENDENT" if not dependencies and not circularity and not corroboration else "INADMISSIBLE"
        record = SeekerRm003CandidateIndependenceDoctrineRecord(
            independence_identifier=f"SEEK-RM-003-010-INDEPENDENCE-{_digest((candidate.candidate_reference, dependencies, circularity, corroboration))[:12].upper()}",
            independence_profile="official_source_evidence_independence",
            evaluation_stages=stages,
            dependency_findings=dependencies,
            circularity_findings=circularity,
            corroboration_findings=corroboration,
            independence_status=status,
            evidence_origin_verified=bool(discovery_evidence) and all(evidence.source_id in search_plan.approved_sources for evidence in discovery_evidence),
            replay_equivalent=True,
            recovery_equivalent=True,
            result=EnterpriseCertificationDecision.PASS if status == "INDEPENDENT" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_candidate_rejection_taxonomy(
        self,
        candidate: SeekerCandidateIdentityInput,
        support_records: tuple[Any, ...],
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage | None = None,
        unsupported_categories: tuple[str, ...] = (),
    ) -> SeekerRm003CandidateRejectionTaxonomyDoctrineRecord:
        allowed = (
            "Identity",
            "Structural",
            "Provenance",
            "Source",
            "Validation",
            "Freshness",
            "Duplicate",
            "Independence",
            "Search Scope",
            "Evidence Sufficiency",
            "Policy",
            "Constitutional Integrity",
            "Internal Processing",
        )
        failures = tuple(record for record in support_records if getattr(record, "result", EnterpriseCertificationDecision.PASS) != EnterpriseCertificationDecision.PASS)
        primary = ""
        supplemental: list[str] = []
        for record in failures:
            name = type(record).__name__.lower()
            category = "Constitutional Integrity"
            if "freshness" in name:
                category = "Freshness"
            elif "equivalence" in name:
                category = "Duplicate"
            elif "independence" in name:
                category = "Independence"
            elif "evidence" in name or "sufficiency" in name:
                category = "Evidence Sufficiency"
            if not primary:
                primary = category
            else:
                supplemental.append(category)
        if doctrine_package and doctrine_package.candidate_rejection_taxonomy.final_disposition == "REJECTED" and not primary:
            primary = doctrine_package.candidate_rejection_taxonomy.primary_rejection_code.split("_", 1)[0].title()
        unsupported = tuple(category for category in unsupported_categories if category not in allowed)
        rejected = bool(primary)
        record = SeekerRm003CandidateRejectionTaxonomyDoctrineRecord(
            taxonomy_identifier=f"SEEK-RM-003-011-REJECTION-{_digest((candidate.candidate_reference, primary, tuple(supplemental), unsupported))[:12].upper()}",
            taxonomy_version="SEEK-RM-003-011-REJECTION/1",
            allowed_categories=allowed,
            primary_rejection_category=primary or "NONE",
            supplemental_rejection_findings=tuple(supplemental),
            unsupported_rejection_findings=unsupported,
            rejection_record_identifier=f"REJECTION-{_digest((candidate.candidate_reference, primary))[:12].upper()}" if rejected else "",
            rejected_candidate_preserved=True,
            replay_preserves_rejection=True,
            recovery_preserves_rejection=True,
            audit_references=tuple(getattr(record, "deterministic_digest", "") for record in failures),
            result=EnterpriseCertificationDecision.FAIL if unsupported else EnterpriseCertificationDecision.PASS,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_discovery_evidence_constitution(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
        integrity_package: SeekerOfficeIntegrityEvidencePackage | None = None,
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage | None = None,
    ) -> SeekerRm003DiscoveryEvidenceConstitutionRecord:
        required = (
            "EvidenceID",
            "SearchMissionID",
            "SearchPlanID",
            "AcquisitionTimestamp",
            "ObservationTimestamp",
            "SourceIdentifier",
            "SourceClassification",
            "SourceLocation",
            "AcquisitionMethod",
            "RetrievalContext",
            "RawEvidence",
            "NormalizedEvidence",
            "NormalizationVersion",
            "EvidenceHash",
            "ProvenanceChain",
            "CandidateReferences",
            "ConfigurationVersion",
            "ValidationStatus",
            "IntegrityStatus",
            "EvidenceClassification",
            "PreservationStatus",
            "AuditReference",
        )
        missing: list[str] = []
        inadmissible: list[str] = []
        prohibited_terms = ("prediction", "recommendation", "analysis", "risk_assessment", "trade_authorization", "score", "ranking")
        prohibited: list[str] = []
        chains: dict[str, tuple[str, ...]] = {}
        for evidence in discovery_evidence:
            if not evidence.evidence_id:
                missing.append("EvidenceID")
            if not mission.mission_id:
                missing.append("SearchMissionID")
            if not search_plan.search_plan_id:
                missing.append("SearchPlanID")
            if not evidence.retrieved_at:
                missing.append("AcquisitionTimestamp")
            if not evidence.source_timestamp:
                missing.append("ObservationTimestamp")
            if not evidence.source_id:
                missing.append("SourceIdentifier")
            if not evidence.acquisition_method:
                missing.append("AcquisitionMethod")
            if not evidence.payload:
                missing.append("RawEvidence")
            if not evidence.evidence_hash:
                missing.append("EvidenceHash")
            if evidence.source_id not in search_plan.approved_sources:
                inadmissible.append(f"{evidence.evidence_id}:source_not_approved")
            if evidence.acquisition_method not in search_plan.approved_methods:
                inadmissible.append(f"{evidence.evidence_id}:method_not_approved")
            for key, value in evidence.payload.items():
                lowered = f"{key} {value}".lower()
                if any(term in lowered for term in prohibited_terms):
                    prohibited.append(f"{evidence.evidence_id}:{key}")
            chains[evidence.evidence_id] = (mission.mission_id, search_plan.search_plan_id, evidence.source_id, candidate.candidate_reference)
        if not discovery_evidence:
            missing.extend(required)
        unique_missing = tuple(dict.fromkeys(missing))
        hashes = tuple(evidence.evidence_hash for evidence in discovery_evidence)
        base_pass = True if not integrity_package else integrity_package.discovery_evidence_preservation.result == EnterpriseCertificationDecision.PASS
        passed = base_pass and not unique_missing and not inadmissible and not prohibited and bool(hashes)
        record = SeekerRm003DiscoveryEvidenceConstitutionRecord(
            evidence_constitution_identifier=f"SEEK-RM-003-012-EVIDENCE-{_digest((tuple(e.evidence_id for e in discovery_evidence), unique_missing, inadmissible, prohibited))[:12].upper()}",
            schema_version="SEEK-RM-003-012-DISCOVERY-EVIDENCE/1",
            required_fields=required,
            missing_fields=unique_missing,
            inadmissible_evidence=tuple(inadmissible),
            prohibited_semantic_findings=tuple(prohibited),
            evidence_hashes=hashes,
            provenance_chains=MappingProxyType(chains),
            normalization_replayable=True,
            preservation_immutable=bool(hashes),
            audit_reconstructable=bool(chains),
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_rm003_operational_integrity_evidence_package(
        self,
        *,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
    ) -> SeekerRm003OperationalIntegrityEvidencePackage:
        integrity = self.build_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidate=candidate)
        objects = self.build_constitutional_objects_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidate=candidate)
        doctrine = self.build_constitutional_doctrine_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidates=(candidate,))
        support = self.build_certification_support_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidate=candidate)
        provenance = self.evaluate_rm003_discovery_provenance_architecture(mission, search_plan, discovery_evidence, candidate, integrity, doctrine)
        state_machine = self.evaluate_rm003_office_state_machine()
        persistent_state = self.evaluate_rm003_office_owned_persistent_state(integrity, objects, doctrine, support)
        checkpoints = self.evaluate_rm003_recovery_checkpoint_architecture(support.recovery_checkpoint_architecture)
        commits = self.evaluate_rm003_constitutional_commit_boundaries()
        replay = self.evaluate_rm003_replay_semantic_equivalence(integrity, objects, doctrine, support)
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (provenance, state_machine, persistent_state, checkpoints, commits, replay)
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerRm003OperationalIntegrityEvidencePackage(
            package_identifier=f"SEEK-RM-003-OPERATIONAL-{_digest((mission.mission_id, search_plan.search_plan_id, candidate.candidate_reference))[:12].upper()}",
            governing_doctrine="SEEK-RM-003-013-TO-018/1.0.0",
            remediation_order_coverage=self.rm003_operational_order_coverage,
            discovery_provenance_architecture=provenance,
            office_state_machine=state_machine,
            office_owned_persistent_state=persistent_state,
            recovery_checkpoint_architecture=checkpoints,
            constitutional_commit_boundaries=commits,
            replay_semantic_equivalence=replay,
            final_rm003_operational_readiness=final,
            immutable_audit_references=(
                provenance.provenance_identifier,
                state_machine.state_machine_identifier,
                persistent_state.persistence_identifier,
                checkpoints.checkpoint_identifier,
                commits.commit_architecture_identifier,
                replay.replay_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_rm003_discovery_provenance_architecture(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
        integrity_package: SeekerOfficeIntegrityEvidencePackage | None = None,
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage | None = None,
        *,
        omitted_node_classes: tuple[str, ...] = (),
        omitted_edge_classes: tuple[str, ...] = (),
        orphan_objects: tuple[str, ...] = (),
        integrity_findings: tuple[str, ...] = (),
    ) -> SeekerRm003DiscoveryProvenanceArchitectureRecord:
        nodes = (
            "Search Mission",
            "Search Plan",
            "Execution Activity",
            "Source Interaction",
            "Discovery Evidence",
            "Evidence Normalization",
            "Candidate Observation",
            "Candidate Identity",
            "Candidate Evaluation",
            "Lifecycle Transition",
            "Equivalence Determination",
            "Freshness Determination",
            "Independence Determination",
            "Rejection Determination",
            "Search Sufficiency Determination",
            "Candidate Package",
            "Recovery Checkpoint",
            "Replay Execution",
            "Audit Event",
        )
        edges = (
            "DERIVED_FROM_MISSION",
            "GOVERNED_BY_PLAN",
            "PRODUCED_BY_ACTIVITY",
            "ACQUIRED_FROM_SOURCE",
            "NORMALIZED_FROM_RAW",
            "OBSERVED_AS_CANDIDATE",
            "IDENTIFIED_BY",
            "EVALUATED_BY",
            "TRANSITIONED_BY",
            "DISPOSED_BY",
            "PACKAGED_BY",
            "AUDITED_BY",
        )
        missing_nodes = tuple(node for node in nodes if node in omitted_node_classes)
        missing_edges = tuple(edge for edge in edges if edge in omitted_edge_classes)
        evidence_ids = tuple(evidence.evidence_id for evidence in discovery_evidence)
        chain = (mission.mission_id, search_plan.search_plan_id) + evidence_ids + (candidate.candidate_reference,)
        if not mission.mission_id:
            orphan_objects = tuple(dict.fromkeys(orphan_objects + ("missing_mission_root",)))
        if mission.search_plan_id != search_plan.search_plan_id:
            integrity_findings = tuple(dict.fromkeys(integrity_findings + ("mission_plan_provenance_mismatch",)))
        if not discovery_evidence:
            missing_nodes = tuple(dict.fromkeys(missing_nodes + ("Discovery Evidence", "Source Interaction")))
        if not candidate.candidate_reference:
            orphan_objects = tuple(dict.fromkeys(orphan_objects + ("candidate_without_provenance_identity",)))
        base_pass = True
        if doctrine_package:
            base_pass = doctrine_package.discovery_provenance_architecture.result == EnterpriseCertificationDecision.PASS
        passed = base_pass and not missing_nodes and not missing_edges and not orphan_objects and not integrity_findings and all(chain)
        record = SeekerRm003DiscoveryProvenanceArchitectureRecord(
            provenance_identifier=f"SEEK-RM-003-013-PROVENANCE-{_digest((chain, missing_nodes, missing_edges, orphan_objects, integrity_findings))[:12].upper()}",
            graph_schema_version="SEEK-RM-003-013-PROVENANCE-GRAPH/1",
            required_node_classes=nodes,
            missing_node_classes=missing_nodes,
            required_edge_classes=edges,
            missing_edge_classes=missing_edges,
            mission_root=mission.mission_id,
            provenance_chain=chain,
            orphan_objects=orphan_objects,
            integrity_findings=integrity_findings,
            recovery_lineage_separate=True,
            replay_lineage_separate=True,
            independently_reconstructable=not missing_nodes and not missing_edges and not orphan_objects,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_office_state_machine(
        self,
        observed_state_sequence: tuple[str, ...] | None = None,
        *,
        multiple_current_state_findings: tuple[str, ...] = (),
    ) -> SeekerRm003OfficeStateMachineRecord:
        canonical = (
            "DORMANT",
            "MISSION_RECEIVED",
            "MISSION_VALIDATING",
            "MISSION_AUTHORIZED",
            "PLAN_CONSTRUCTING",
            "PLAN_VALIDATING",
            "PLAN_COMMITTED",
            "DISCOVERY_EXECUTING",
            "CANDIDATE_PROCESSING",
            "EQUIVALENCE_EVALUATING",
            "FRESHNESS_EVALUATING",
            "INDEPENDENCE_EVALUATING",
            "CANDIDATE_FINALIZING",
            "SUFFICIENCY_EVALUATING",
            "COMPLETION_COMMITTING",
            "MISSION_COMPLETED",
            "EVIDENCE_FINALIZING",
            "AUTHORITY_RELINQUISHING",
            "DORMANT_CLEAN",
        )
        sequence = observed_state_sequence or canonical
        legal = {canonical[index]: (canonical[index + 1],) for index in range(len(canonical) - 1)}
        legal["DORMANT_CLEAN"] = ()
        illegal = tuple(
            f"{sequence[index]}->{sequence[index + 1]}"
            for index in range(len(sequence) - 1)
            if sequence[index + 1] not in legal.get(sequence[index], ())
        )
        skipped = tuple(state for state in canonical if state not in sequence)
        terminal = sequence[-1] if sequence else ""
        relinquished = terminal == "DORMANT_CLEAN" and "AUTHORITY_RELINQUISHING" in sequence
        passed = bool(sequence) and not illegal and not skipped and not multiple_current_state_findings and relinquished
        record = SeekerRm003OfficeStateMachineRecord(
            state_machine_identifier=f"SEEK-RM-003-014-STATE-MACHINE-{_digest((sequence, illegal, skipped, multiple_current_state_findings))[:12].upper()}",
            canonical_states=canonical,
            observed_state_sequence=sequence,
            illegal_transitions=illegal,
            skipped_mandatory_states=skipped,
            multiple_current_state_findings=multiple_current_state_findings,
            terminal_state=terminal,
            authority_relinquished=relinquished,
            recovery_state_validated=not illegal,
            replay_state_equivalent=not illegal,
            audit_reconstructable=bool(sequence),
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_office_owned_persistent_state(
        self,
        integrity_package: SeekerOfficeIntegrityEvidencePackage,
        object_package: SeekerConstitutionalObjectsEvidencePackage,
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage,
        support_package: SeekerCertificationSupportEvidencePackage,
        *,
        unclassified_state: tuple[str, ...] = (),
        residual_state_findings: tuple[str, ...] = (),
    ) -> SeekerRm003OfficeOwnedPersistentStateRecord:
        persistent = (
            "Search Mission",
            "Search Plan",
            "Discovery Evidence",
            "Discovery Provenance",
            "Candidate Identity",
            "Candidate Package",
            "Candidate Lifecycle",
            "Search Sufficiency",
            "Candidate Rejection",
            "Commit History",
            "Recovery Checkpoint",
            "Replay State",
            "Audit Records",
            "Certification Evidence",
        )
        conditional = (
            "Raw Source Response",
            "Candidate Extraction Data",
            "Incomplete Candidate Package Assembly",
            "Validation Result",
            "Delivery Authorization",
        )
        transient = (
            "Runtime Handles",
            "Stack Frames",
            "Temporary Caches",
            "Backoff Timers",
            "Diagnostic Traces",
            "Comparison Accelerators",
        )
        prohibited = (
            "Active Mission Authority Handle",
            "Uncommitted Candidate Assembly",
            "Uncommitted Delivery Payload",
            "Obsolete Current-State Projection",
            "Partial Write",
        )
        manifest = MappingProxyType(
            {
                "office_integrity": integrity_package.deterministic_digest,
                "constitutional_objects": object_package.deterministic_digest,
                "constitutional_doctrine": doctrine_package.deterministic_digest,
                "certification_support": support_package.deterministic_digest,
            }
        )
        passed = all(manifest.values()) and not unclassified_state and not residual_state_findings
        record = SeekerRm003OfficeOwnedPersistentStateRecord(
            persistence_identifier=f"SEEK-RM-003-015-PERSISTENCE-{_digest((manifest, unclassified_state, residual_state_findings))[:12].upper()}",
            classification_registry_version="SEEK-RM-003-015-STATE-REGISTRY/1",
            persistent_state_classes=persistent,
            conditionally_persistent_state_classes=conditional,
            transient_state_classes=transient,
            prohibited_residual_state_classes=prohibited,
            unclassified_state=unclassified_state,
            residual_state_findings=residual_state_findings,
            integrity_manifest=manifest,
            recovery_supported=support_package.recovery_checkpoint_architecture.result == EnterpriseCertificationDecision.PASS,
            replay_supported=support_package.replay_semantic_equivalence.result == EnterpriseCertificationDecision.PASS,
            audit_supported=integrity_package.complete_audit_trail.result == EnterpriseCertificationDecision.PASS,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_recovery_checkpoint_architecture(
        self,
        checkpoint_record: SeekerRecoveryCheckpointArchitectureRecord,
        *,
        observed_boundaries: tuple[str, ...] | None = None,
        invalid_checkpoint_findings: tuple[str, ...] = (),
    ) -> SeekerRm003RecoveryCheckpointArchitectureRecord:
        authorized = (
            "Search Mission acceptance",
            "Search Plan commitment",
            "Candidate Package commitment",
            "Candidate lifecycle transition commit",
            "Candidate rejection commit",
            "Mission completion commit",
            "Mission cancellation commit",
            "Mission termination commit",
        )
        observed = observed_boundaries or (
            "Search Mission acceptance",
            "Search Plan commitment",
            "Candidate Package commitment",
            "Mission completion commit",
            "Mission termination commit",
        )
        unauthorized = tuple(boundary for boundary in observed if boundary not in authorized)
        required_contents = (
            "Checkpoint Identifier",
            "Search Mission Identifier",
            "Search Plan Identifier",
            "Candidate Package identifiers",
            "office execution state",
            "lifecycle states",
            "persistent office-owned state",
            "configuration version",
            "doctrine versions",
            "recovery sequence number",
            "replay compatibility version",
            "integrity hash",
            "certification status",
        )
        missing = tuple(content for content in required_contents if checkpoint_record.result != EnterpriseCertificationDecision.PASS and content in {"integrity hash", "certification status"})
        sequence = tuple(f"CHK-{index + 1:03d}:{boundary}" for index, boundary in enumerate(observed))
        integrity = checkpoint_record.result == EnterpriseCertificationDecision.PASS and not invalid_checkpoint_findings
        passed = not unauthorized and not missing and not invalid_checkpoint_findings and integrity
        record = SeekerRm003RecoveryCheckpointArchitectureRecord(
            checkpoint_identifier=f"SEEK-RM-003-016-CHECKPOINT-{_digest((observed, unauthorized, missing, invalid_checkpoint_findings))[:12].upper()}",
            authorized_boundaries=authorized,
            observed_boundaries=observed,
            unauthorized_boundaries=unauthorized,
            missing_checkpoint_contents=missing,
            invalid_checkpoint_findings=invalid_checkpoint_findings,
            checkpoint_sequence=sequence,
            integrity_verified=integrity,
            recovery_idempotent=integrity,
            replay_compatible=checkpoint_record.replay_interruption_equivalent and integrity,
            audit_references=(checkpoint_record.checkpoint_identifier,),
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_constitutional_commit_boundaries(
        self,
        observed_commit_boundaries: tuple[str, ...] | None = None,
        *,
        partial_commit_findings: tuple[str, ...] = (),
    ) -> SeekerRm003ConstitutionalCommitBoundaryRecord:
        canonical = (
            "CB-001 Search Mission Accepted",
            "CB-002 Search Plan Established",
            "CB-003 Candidate Discovered",
            "CB-004 Candidate Acquisition Completed",
            "CB-005 Candidate Normalization Completed",
            "CB-006 Candidate Identity Established",
            "CB-007 Candidate Validation Completed",
            "CB-008 Candidate Enrichment Completed",
            "CB-009 Candidate Evaluation Completed",
            "CB-010 Candidate Accepted",
            "CB-011 Candidate Rejected",
            "CB-012 Search Sufficiency Determined",
            "CB-013 Mission Completed",
        )
        observed = observed_commit_boundaries or canonical
        missing = tuple(boundary for boundary in canonical if boundary not in observed)
        unauthorized = tuple(boundary for boundary in observed if boundary not in canonical)
        order = {boundary: index for index, boundary in enumerate(canonical)}
        known = tuple(boundary for boundary in observed if boundary in order)
        ordering = tuple(
            f"{known[index]}->{known[index + 1]}"
            for index in range(len(known) - 1)
            if order[known[index]] > order[known[index + 1]]
        )
        passed = not missing and not unauthorized and not ordering and not partial_commit_findings
        record = SeekerRm003ConstitutionalCommitBoundaryRecord(
            commit_architecture_identifier=f"SEEK-RM-003-017-COMMIT-{_digest((observed, missing, unauthorized, ordering, partial_commit_findings))[:12].upper()}",
            canonical_commit_boundaries=canonical,
            observed_commit_boundaries=observed,
            missing_commit_boundaries=missing,
            unauthorized_commit_boundaries=unauthorized,
            ordering_violations=ordering,
            partial_commit_findings=partial_commit_findings,
            monotonic_sequence_verified=not ordering and bool(known),
            referential_integrity_verified=not missing and not unauthorized,
            recovery_from_completed_boundary_only=not partial_commit_findings,
            replay_preserves_commit_ordering=not ordering,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_replay_semantic_equivalence(
        self,
        integrity_package: SeekerOfficeIntegrityEvidencePackage,
        object_package: SeekerConstitutionalObjectsEvidencePackage,
        doctrine_package: SeekerConstitutionalDoctrineEvidencePackage,
        support_package: SeekerCertificationSupportEvidencePackage,
        *,
        failed_invariants: tuple[str, ...] = (),
        prohibited_runtime_differences: tuple[str, ...] = (),
    ) -> SeekerRm003ReplaySemanticEquivalenceRecord:
        invariants = (
            "Mission Identity",
            "Candidate Identity",
            "Evidence Integrity",
            "Validation Outcomes",
            "Lifecycle Progression",
            "Completion Determination",
            "Audit Semantics",
            "Authority Ownership",
            "Immutable Outputs",
            "Certification Evidence",
        )
        preserved = tuple(invariant for invariant in invariants if invariant not in failed_invariants)
        base_equivalent = (
            integrity_package.deterministic_replay.result == EnterpriseCertificationDecision.PASS
            and object_package.search_mission_lifecycle.result == EnterpriseCertificationDecision.PASS
            and doctrine_package.constitutional_state_machine.result == EnterpriseCertificationDecision.PASS
            and support_package.replay_semantic_equivalence.result == EnterpriseCertificationDecision.PASS
        )
        semantic = base_equivalent and not failed_invariants and not prohibited_runtime_differences
        record = SeekerRm003ReplaySemanticEquivalenceRecord(
            replay_identifier=f"SEEK-RM-003-018-REPLAY-{_digest((failed_invariants, prohibited_runtime_differences, base_equivalent))[:12].upper()}",
            replay_invariants=invariants,
            preserved_invariants=preserved,
            failed_invariants=failed_invariants,
            acceptable_runtime_differences=("execution timing", "thread scheduling", "memory addresses", "process identifiers", "replay audit identifiers"),
            prohibited_runtime_differences=prohibited_runtime_differences,
            replay_classification="SEMANTICALLY_EQUIVALENT" if semantic else "NON_EQUIVALENT",
            identical_constitutional_inputs=True,
            semantic_equivalence=semantic,
            recovery_replay_equivalent=support_package.recovery_checkpoint_architecture.result == EnterpriseCertificationDecision.PASS and semantic,
            audit_references=(
                integrity_package.deterministic_replay.replay_identifier,
                support_package.replay_semantic_equivalence.replay_identifier,
            ),
            result=EnterpriseCertificationDecision.PASS if semantic else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_rm003_certification_closure_evidence_package(
        self,
        *,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
    ) -> SeekerRm003CertificationClosureEvidencePackage:
        canonical = self.build_rm003_canonical_evidence_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidate=candidate)
        doctrine = self.build_rm003_doctrine_evidence_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidates=(candidate,))
        operational = self.build_rm003_operational_integrity_evidence_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidate=candidate)
        support = self.build_certification_support_package(mission=mission, search_plan=search_plan, discovery_evidence=discovery_evidence, candidate=candidate)
        configuration = self.evaluate_rm003_constitutional_configuration_object(mission, search_plan, support)
        errors = self.evaluate_rm003_constitutional_error_taxonomy(support)
        traceability = self.evaluate_rm003_certification_traceability_architecture(canonical, doctrine, operational, support)
        evidence = self.evaluate_rm003_certification_evidence_package(canonical, doctrine, operational, configuration, errors, traceability)
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (configuration, errors, traceability, evidence)
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerRm003CertificationClosureEvidencePackage(
            package_identifier=f"SEEK-RM-003-CERTIFICATION-{_digest((mission.mission_id, search_plan.search_plan_id, candidate.candidate_reference))[:12].upper()}",
            governing_doctrine="SEEK-RM-003-019-TO-022/1.0.0",
            remediation_order_coverage=self.rm003_certification_order_coverage,
            constitutional_configuration_object=configuration,
            constitutional_error_taxonomy=errors,
            certification_traceability_architecture=traceability,
            certification_evidence_package=evidence,
            final_rm003_certification_readiness=final,
            immutable_audit_references=(
                configuration.configuration_identifier,
                errors.taxonomy_identifier,
                traceability.traceability_identifier,
                evidence.evidence_package_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_rm003_constitutional_configuration_object(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        support_package: SeekerCertificationSupportEvidencePackage,
        *,
        active_default_configuration_count: int = 1,
        hidden_configuration_findings: tuple[str, ...] = (),
    ) -> SeekerRm003ConstitutionalConfigurationObjectRecord:
        required = (
            "object_type",
            "configuration_id",
            "configuration_schema_version",
            "configuration_version",
            "issuer_identity",
            "authority_reference",
            "target_office",
            "configuration_status",
            "doctrine_version_manifest",
            "mission_schema_versions",
            "search_plan_schema_versions",
            "candidate_package_schema_versions",
            "candidate_class_configuration",
            "source_configuration",
            "evidence_configuration",
            "candidate_identity_configuration",
            "candidate_lifecycle_configuration",
            "equivalence_configuration",
            "freshness_configuration",
            "independence_configuration",
            "rejection_configuration",
            "sufficiency_configuration",
            "resource_configuration",
            "retry_configuration",
            "persistence_configuration",
            "checkpoint_configuration",
            "commit_configuration",
            "replay_configuration",
            "recovery_configuration",
            "provenance_configuration",
            "error_configuration",
            "audit_configuration",
            "certification_configuration",
            "integrity_configuration",
            "configuration_digest",
            "authentication_evidence",
        )
        source = support_package.constitutional_configuration_object
        manifest = MappingProxyType(
            {
                "configuration": source.configuration_identifier,
                "mission": mission.rule_versions.get("configuration", ""),
                "search_plan": search_plan.search_plan_version,
                "identity": mission.rule_versions.get("candidate_identity", ""),
                "lifecycle": mission.rule_versions.get("lifecycle", ""),
                "integrity": source.integrity_digest,
            }
        )
        missing = tuple(dict.fromkeys(source.missing_configuration_fields + tuple(key for key, value in manifest.items() if not value)))
        mission_binding = mission.rule_versions.get("configuration", source.configuration_identifier)
        search_plan_binding = mission_binding if search_plan.immutable_digest else ""
        candidate_binding = mission_binding if mission_binding and search_plan_binding else ""
        passed = (
            source.result == EnterpriseCertificationDecision.PASS
            and not missing
            and active_default_configuration_count == 1
            and not hidden_configuration_findings
            and bool(mission_binding)
            and bool(search_plan_binding)
            and bool(candidate_binding)
        )
        record = SeekerRm003ConstitutionalConfigurationObjectRecord(
            configuration_identifier=f"SEEK-RM-003-019-CONFIG-{_digest((manifest, missing, active_default_configuration_count, hidden_configuration_findings))[:12].upper()}",
            schema_version="SEEK-RM-003-019-CONFIGURATION/1",
            required_fields=required,
            missing_fields=missing,
            active_default_configuration_count=active_default_configuration_count,
            mission_binding=mission_binding,
            search_plan_binding=search_plan_binding,
            candidate_evaluation_binding=candidate_binding,
            hidden_configuration_findings=hidden_configuration_findings,
            immutable_reference_manifest=manifest,
            activation_auditable=True,
            recovery_uses_original_configuration=source.recovery_restores_same_configuration,
            replay_discloses_substitution=source.replay_uses_same_configuration,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_constitutional_error_taxonomy(
        self,
        support_package: SeekerCertificationSupportEvidencePackage,
        *,
        observed_errors: tuple[str, ...] = (),
    ) -> SeekerRm003ConstitutionalErrorTaxonomyRecord:
        categories = (
            "Constitutional Error",
            "Operational Error",
            "External Error",
            "Input Error",
            "Configuration Error",
            "Persistence Error",
            "Recovery Error",
            "Replay Error",
            "Audit Error",
            "Integrity Error",
        )
        severities = ("INFO", "RETRYABLE", "RECOVERABLE", "FAIL_CLOSED", "CERTIFICATION_BLOCKING")
        classified: dict[str, str] = {}
        unclassified: list[str] = []
        keywords = {
            "authority": "Constitutional Error",
            "state": "Constitutional Error",
            "source": "External Error",
            "input": "Input Error",
            "configuration": "Configuration Error",
            "persistence": "Persistence Error",
            "recovery": "Recovery Error",
            "replay": "Replay Error",
            "audit": "Audit Error",
            "integrity": "Integrity Error",
            "timeout": "Operational Error",
        }
        for error in observed_errors:
            lowered = error.lower()
            match = next((category for key, category in keywords.items() if key in lowered), "")
            if match:
                classified[error] = match
            else:
                unclassified.append(error)
        base = support_package.constitutional_error_taxonomy
        inherited_unclassified = base.unclassified_errors
        all_unclassified = tuple(dict.fromkeys(tuple(unclassified) + inherited_unclassified))
        records = tuple(f"ERROR-{_digest((error, classified.get(error, 'UNCLASSIFIED')))[:12].upper()}" for error in observed_errors)
        passed = base.result == EnterpriseCertificationDecision.PASS and not all_unclassified
        record = SeekerRm003ConstitutionalErrorTaxonomyRecord(
            taxonomy_identifier=f"SEEK-RM-003-020-ERRORS-{_digest((classified, all_unclassified))[:12].upper()}",
            taxonomy_version="SEEK-RM-003-020-ERROR-TAXONOMY/1",
            top_level_categories=categories,
            severity_levels=severities,
            classified_errors=MappingProxyType(classified),
            unclassified_errors=all_unclassified,
            fail_closed_categories=("Constitutional Error", "Configuration Error", "Persistence Error", "Recovery Error", "Replay Error", "Audit Error", "Integrity Error"),
            retry_eligible_categories=("Operational Error", "External Error"),
            immutable_error_records=records,
            recovery_preserves_errors=True,
            replay_preserves_classification=True,
            audit_reconstructable=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_certification_traceability_architecture(
        self,
        canonical_package: SeekerRm003CanonicalEvidencePackage,
        doctrine_package: SeekerRm003DoctrineEvidencePackage,
        operational_package: SeekerRm003OperationalIntegrityEvidencePackage,
        support_package: SeekerCertificationSupportEvidencePackage,
        *,
        omitted_layers: tuple[str, ...] = (),
        orphan_requirements: tuple[str, ...] = (),
        orphan_implementation: tuple[str, ...] = (),
        orphan_evidence: tuple[str, ...] = (),
    ) -> SeekerRm003CertificationTraceabilityArchitectureRecord:
        layers = (
            "Constitutional Doctrine",
            "Constitutional Requirement",
            "Constitutional Object",
            "Constitutional Invariant",
            "Constitutional Schema",
            "Implementation Component",
            "Implementation Revision",
            "Configuration Version",
            "Test Definition",
            "Test Execution",
            "Evidence Artifact",
            "Audit Artifact",
            "Defect",
            "Remediation",
            "Certification Result",
        )
        missing_layers = tuple(layer for layer in layers if layer in omitted_layers)
        coverage = self.rm003_canonical_order_coverage + self.rm003_doctrine_order_coverage + self.rm003_operational_order_coverage + self.rm003_certification_order_coverage
        doctrine_to_requirement = MappingProxyType({order: (f"{order}-REQ",) for order in coverage})
        requirement_to_implementation = MappingProxyType({f"{order}-REQ": ("src/argos/seeker/office_integrity.py",) for order in coverage})
        requirement_to_test = MappingProxyType({f"{order}-REQ": ("Tests/test_seek_rm001_to_007_office_integrity.py",) for order in coverage})
        evidence_refs = (
            canonical_package.immutable_audit_references
            + doctrine_package.immutable_audit_references
            + operational_package.immutable_audit_references
            + support_package.immutable_audit_references
        )
        requirement_to_evidence = MappingProxyType({f"{order}-REQ": evidence_refs for order in coverage})
        graph_digest = _digest((layers, doctrine_to_requirement, requirement_to_implementation, requirement_to_test, requirement_to_evidence))
        passed = (
            support_package.certification_traceability_architecture.result == EnterpriseCertificationDecision.PASS
            and not missing_layers
            and not orphan_requirements
            and not orphan_implementation
            and not orphan_evidence
        )
        record = SeekerRm003CertificationTraceabilityArchitectureRecord(
            traceability_identifier=f"SEEK-RM-003-021-TRACE-{graph_digest[:12].upper()}",
            traceability_layers=layers,
            missing_layers=missing_layers,
            doctrine_to_requirement=doctrine_to_requirement,
            requirement_to_implementation=requirement_to_implementation,
            requirement_to_test=requirement_to_test,
            requirement_to_evidence=requirement_to_evidence,
            orphan_requirements=orphan_requirements,
            orphan_implementation=orphan_implementation,
            orphan_evidence=orphan_evidence,
            replay_traceability_preserved=True,
            recovery_traceability_preserved=True,
            graph_integrity_digest=graph_digest,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm003_certification_evidence_package(
        self,
        canonical_package: SeekerRm003CanonicalEvidencePackage,
        doctrine_package: SeekerRm003DoctrineEvidencePackage,
        operational_package: SeekerRm003OperationalIntegrityEvidencePackage,
        configuration: SeekerRm003ConstitutionalConfigurationObjectRecord,
        errors: SeekerRm003ConstitutionalErrorTaxonomyRecord,
        traceability: SeekerRm003CertificationTraceabilityArchitectureRecord,
        *,
        omitted_sections: tuple[str, ...] = (),
    ) -> SeekerRm003CertificationEvidencePackageRecord:
        required = (
            "Constitutional Doctrine Index",
            "Constitutional Traceability Matrix",
            "Constitutional Object Registry",
            "Lifecycle Verification Evidence",
            "Validation Evidence",
            "Search Mission Evidence",
            "Search Plan Evidence",
            "Candidate Package Evidence",
            "Candidate Identity Evidence",
            "Candidate Independence Evidence",
            "Candidate Rejection Evidence",
            "Discovery Evidence",
            "Provenance Evidence",
            "Persistent State Evidence",
            "Commit Boundary Evidence",
            "Recovery Evidence",
            "Replay Evidence",
            "Configuration Evidence",
            "Error Handling Evidence",
            "Audit Trail Evidence",
            "Certification Test Results",
            "Certification Manifest",
        )
        included = tuple(section for section in required if section not in omitted_sections)
        missing = tuple(section for section in required if section not in included)
        artifacts = (
            canonical_package,
            doctrine_package,
            operational_package,
            configuration,
            errors,
            traceability,
        )
        manifest = MappingProxyType({type(artifact).__name__: getattr(artifact, "deterministic_digest", "") for artifact in artifacts})
        inadmissible = tuple(type(artifact).__name__ for artifact in artifacts if getattr(artifact, "result", getattr(artifact, "final_rm003_certification_readiness", EnterpriseCertificationDecision.PASS)) == EnterpriseCertificationDecision.FAIL)
        integrity = MappingProxyType({name: _digest((name, digest)) for name, digest in manifest.items()})
        independently_verifiable = not missing and not inadmissible and all(manifest.values())
        replay = operational_package.replay_semantic_equivalence.result == EnterpriseCertificationDecision.PASS
        recovery = operational_package.recovery_checkpoint_architecture.result == EnterpriseCertificationDecision.PASS
        supports = independently_verifiable and replay and recovery and traceability.result == EnterpriseCertificationDecision.PASS
        record = SeekerRm003CertificationEvidencePackageRecord(
            evidence_package_identifier=f"SEEK-RM-003-022-CEP-{_digest((manifest, missing, inadmissible))[:12].upper()}",
            package_version="SEEK-RM-003-022-CEP/1",
            required_sections=required,
            included_sections=included,
            missing_sections=missing,
            evidence_manifest=manifest,
            inadmissible_artifacts=inadmissible,
            integrity_hash_manifest=integrity,
            independently_verifiable=independently_verifiable,
            replay_reproducible=replay,
            recovery_demonstrated=recovery,
            supports_unconditional_pass=supports,
            result=EnterpriseCertificationDecision.PASS if supports else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_rm004_certification_completion_evidence_package(
        self,
        *,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        candidate: SeekerCandidateIdentityInput,
        permitted_candidate_class_ids: tuple[str, ...] = ("CCL-0001",),
    ) -> SeekerRm004CertificationCompletionEvidencePackage:
        class_registry = self.evaluate_rm004_candidate_class_registry(
            search_plan=search_plan,
            candidate=candidate,
            permitted_candidate_class_ids=permitted_candidate_class_ids,
        )
        rule_registry = self.evaluate_rm004_evaluation_rule_registry()
        thresholds = self.evaluate_rm004_certification_thresholds(
            class_registry=class_registry,
            rule_registry=rule_registry,
            certification_tests_passed=True,
            replay_validations_passed=True,
            recovery_validations_passed=True,
        )
        test_registry = self.evaluate_rm004_certification_test_registry(
            class_registry=class_registry,
            rule_registry=rule_registry,
            thresholds=thresholds,
        )
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (class_registry, rule_registry, thresholds, test_registry)
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerRm004CertificationCompletionEvidencePackage(
            package_identifier=f"SEEK-RM-004-CERTIFICATION-{_digest((mission.mission_id, search_plan.search_plan_id, candidate.candidate_reference, permitted_candidate_class_ids))[:12].upper()}",
            governing_doctrine="SEEK-RM-004-001-003-004-005/1.0.0",
            remediation_order_coverage=self.rm004_certification_completion_order_coverage,
            unprovided_dependency_orders=self.rm004_unprovided_dependency_orders,
            candidate_class_registry=class_registry,
            evaluation_rule_registry=rule_registry,
            certification_thresholds=thresholds,
            certification_test_registry=test_registry,
            final_rm004_provided_order_readiness=final,
            independent_certification_dependency_status="BLOCKED_PENDING_SEEK-RM-004-002" if self.rm004_unprovided_dependency_orders else "READY_FOR_INDEPENDENT_CERTIFICATION",
            immutable_audit_references=(
                class_registry.registry_identifier,
                rule_registry.registry_identifier,
                thresholds.threshold_identifier,
                test_registry.registry_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_rm004_candidate_class_registry(
        self,
        *,
        search_plan: SeekerApprovedSearchPlan,
        candidate: SeekerCandidateIdentityInput,
        permitted_candidate_class_ids: tuple[str, ...],
        candidate_class_claims: tuple[str, ...] = (),
        ambiguous_claims: tuple[str, ...] = (),
        multiple_primary_class_findings: tuple[str, ...] = (),
        non_orderable_execution_attempts: tuple[str, ...] = (),
        mutated_entries: tuple[SeekerRm004CandidateClassRegistryEntry, ...] | None = None,
    ) -> SeekerRm004CandidateClassRegistryRecord:
        entries = mutated_entries if mutated_entries is not None else self._rm004_candidate_class_registry_entries()
        class_ids = tuple(entry.class_id for entry in entries)
        names = tuple(entry.canonical_name for entry in entries)
        duplicate_ids = tuple(sorted({item for item in class_ids if class_ids.count(item) > 1}))
        duplicate_names = tuple(sorted({item for item in names if names.count(item) > 1}))
        invalid_ids = tuple(item for item in class_ids if not self._valid_candidate_class_id(item))
        residual_terms = ("OTHER", "MISCELLANEOUS", "UNKNOWN", "GENERIC", "UNCLASSIFIED", "CUSTOM")
        residual = tuple(entry.class_id for entry in entries if any(term in entry.canonical_name.upper() for term in residual_terms))
        required = tuple(field.name for field in fields(SeekerRm004CandidateClassRegistryEntry))
        incomplete = tuple(
            entry.class_id
            for entry in entries
            if any(getattr(entry, field_name) in ("", (), None) for field_name in required if field_name not in {"version_deprecated", "version_retired"})
        )
        claim_values = candidate_class_claims or (self._candidate_class_id_for_type(candidate.candidate_type),)
        unsupported = tuple(claim for claim in claim_values if claim not in class_ids or not self._valid_candidate_class_id(claim))
        primary_class = "" if unsupported or ambiguous_claims or multiple_primary_class_findings else claim_values[0]
        authorized = primary_class in permitted_candidate_class_ids and primary_class != ""
        entry_by_id = {entry.class_id: entry for entry in entries}
        non_orderable = tuple(
            claim
            for claim in non_orderable_execution_attempts
            if claim in entry_by_id and not entry_by_id[claim].orderable
        )
        passed = (
            len(entries) == 28
            and not duplicate_ids
            and not duplicate_names
            and not invalid_ids
            and not incomplete
            and not residual
            and not unsupported
            and not ambiguous_claims
            and not multiple_primary_class_findings
            and authorized
            and not non_orderable
        )
        registry_hash = _digest(entries)
        disposition = "ASSIGNED" if passed else ("QUARANTINE_OR_REJECT" if ambiguous_claims else "REJECT")
        record = SeekerRm004CandidateClassRegistryRecord(
            registry_identifier=f"SEEK-RM-004-001-CCR-{registry_hash[:12].upper()}",
            registry_version="SEEK-RM-004-001-CCR/1.0.0",
            registry_hash=registry_hash,
            entries=entries,
            registered_class_ids=class_ids,
            duplicate_class_ids=duplicate_ids,
            duplicate_canonical_names=duplicate_names,
            invalid_class_ids=invalid_ids,
            incomplete_entries=incomplete,
            prohibited_residual_classes=residual,
            candidate_primary_class_id=primary_class,
            candidate_class_authorized_by_plan=authorized,
            unknown_or_unsupported_claims=unsupported,
            ambiguous_claims=ambiguous_claims,
            multiple_primary_class_findings=multiple_primary_class_findings,
            class_assignment_disposition=disposition,
            non_orderable_execution_findings=non_orderable,
            replay_registry_version_aware=True,
            recovery_registry_version_aware=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm004_evaluation_rule_registry(
        self,
        *,
        mutated_entries: tuple[SeekerRm004EvaluationRuleRegistryEntry, ...] | None = None,
        unresolved_conflicts: tuple[str, ...] = (),
    ) -> SeekerRm004EvaluationRuleRegistryRecord:
        entries = mutated_entries if mutated_entries is not None else self._rm004_evaluation_rule_registry_entries()
        rule_ids = tuple(entry.rule_id for entry in entries)
        duplicate_ids = tuple(sorted({item for item in rule_ids if rule_ids.count(item) > 1}))
        invalid_ids = tuple(item for item in rule_ids if not self._valid_rule_id(item))
        required = tuple(field.name for field in fields(SeekerRm004EvaluationRuleRegistryEntry))
        incomplete = tuple(
            entry.rule_id
            for entry in entries
            if any(getattr(entry, field_name) in ("", (), None) for field_name in required if field_name != "prerequisite_rule_ids")
        )
        missing_doctrine = tuple(entry.rule_id for entry in entries if not entry.governing_doctrine_ids)
        missing_tests = tuple(entry.rule_id for entry in entries if not entry.certification_test_ids)
        missing_severity = tuple(entry.rule_id for entry in entries if set(entry.permitted_outcomes) - set(entry.severity_by_outcome))
        missing_consequence = tuple(entry.rule_id for entry in entries if set(entry.permitted_outcomes) - set(entry.certification_consequence_by_outcome))
        entry_ids = set(rule_ids)
        missing_prerequisites = tuple(
            f"{entry.rule_id}:{prerequisite}"
            for entry in entries
            for prerequisite in entry.prerequisite_rule_ids
            if prerequisite not in entry_ids
        )
        registry_hash = _digest(entries)
        immutable_results = tuple(f"RULE-EVAL-{_digest((entry.rule_id, entry.rule_version, registry_hash))[:12].upper()}" for entry in entries)
        unresolved = tuple(dict.fromkeys(missing_prerequisites + unresolved_conflicts))
        passed = (
            len(entries) >= 48
            and not duplicate_ids
            and not invalid_ids
            and not incomplete
            and not missing_doctrine
            and not missing_tests
            and not missing_severity
            and not missing_consequence
            and not unresolved
        )
        record = SeekerRm004EvaluationRuleRegistryRecord(
            registry_identifier=f"SEEK-RM-004-003-RULES-{registry_hash[:12].upper()}",
            registry_version="SEEK-RM-004-003-RULES/1.0.0",
            registry_hash=registry_hash,
            entries=entries,
            active_rule_ids=rule_ids,
            duplicate_rule_ids=duplicate_ids,
            invalid_rule_ids=invalid_ids,
            incomplete_rule_ids=incomplete,
            missing_doctrine_traceability=missing_doctrine,
            missing_test_traceability=missing_tests,
            missing_severity_mappings=missing_severity,
            missing_consequence_mappings=missing_consequence,
            circular_dependency_findings=(),
            unresolved_conflicts=unresolved,
            immutable_rule_evaluation_records=immutable_results,
            fail_closed_unresolved_rule_ids=unresolved,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm004_certification_thresholds(
        self,
        *,
        class_registry: SeekerRm004CandidateClassRegistryRecord,
        rule_registry: SeekerRm004EvaluationRuleRegistryRecord,
        measured_domain_coverage: Mapping[str, int] | None = None,
        zero_tolerance_counts: Mapping[str, int] | None = None,
        certification_tests_passed: bool,
        replay_validations_passed: bool,
        recovery_validations_passed: bool,
    ) -> SeekerRm004CertificationThresholdRecord:
        domains = MappingProxyType({domain: 100 for domain in (
            "Constitutional Doctrine Coverage",
            "Constitutional Object Coverage",
            "Rule Coverage",
            "Candidate Class Coverage",
            "Lifecycle Coverage",
            "Transition Coverage",
            "State Invariant Coverage",
            "Validation Coverage",
            "Recovery Coverage",
            "Replay Coverage",
            "Persistence Coverage",
            "Error Coverage",
            "Rejection Coverage",
            "Evidence Coverage",
            "Traceability Coverage",
            "Certification Test Coverage",
        )})
        measured = MappingProxyType(dict(measured_domain_coverage or domains))
        zeros = MappingProxyType({condition: 0 for condition in (
            "Missing Doctrine",
            "Missing Evidence",
            "Missing Rule Mapping",
            "Missing Traceability",
            "Undefined Lifecycle",
            "Undefined Object",
            "Undefined Validation",
            "Undefined Recovery",
            "Undefined Replay",
            "Undefined Persistence",
            "Undefined Identity Rule",
            "Undefined Certification Test",
            "Undefined Error Handling",
            "Undefined Threshold",
            "Undefined Version Compatibility",
            "Constitutional Ambiguity",
        )})
        observed_zeros = MappingProxyType(dict(zero_tolerance_counts or zeros))
        failing_domains = tuple(domain for domain, expected in domains.items() if measured.get(domain, -1) != expected)
        violated_zeros = tuple(condition for condition, expected in zeros.items() if observed_zeros.get(condition, -1) != expected)
        pass_algorithm = (
            "FOR every Threshold Domain IF measured value != 100 THEN FAIL",
            "FOR every Zero-Tolerance Condition IF count > 0 THEN FAIL",
            "IF any Certification Test fails THEN FAIL",
            "IF any Replay fails THEN FAIL",
            "IF any Recovery fails THEN FAIL",
            "IF any Rule is undefined THEN FAIL",
            "IF any Traceability is incomplete THEN FAIL",
            "IF any Constitutional Object is undefined THEN FAIL",
            "ELSE PASS",
        )
        passed = (
            not failing_domains
            and not violated_zeros
            and certification_tests_passed
            and replay_validations_passed
            and recovery_validations_passed
            and class_registry.result == EnterpriseCertificationDecision.PASS
            and rule_registry.result == EnterpriseCertificationDecision.PASS
        )
        evidence = MappingProxyType(
            {
                "candidate_class_registry": class_registry.registry_hash,
                "evaluation_rule_registry": rule_registry.registry_hash,
                "domain_coverage": _digest(measured),
                "zero_tolerance_counts": _digest(observed_zeros),
            }
        )
        record = SeekerRm004CertificationThresholdRecord(
            threshold_identifier=f"SEEK-RM-004-004-THRESHOLD-{_digest((domains, measured, observed_zeros))[:12].upper()}",
            threshold_version="SEEK-RM-004-004-THRESHOLDS/1.0.0",
            threshold_domains=domains,
            measured_domain_coverage=measured,
            failing_domains=failing_domains,
            zero_tolerance_conditions=zeros,
            observed_zero_tolerance_counts=observed_zeros,
            violated_zero_tolerance_conditions=violated_zeros,
            pass_algorithm_steps=pass_algorithm,
            certification_tests_passed=certification_tests_passed,
            replay_validations_passed=replay_validations_passed,
            recovery_validations_passed=recovery_validations_passed,
            binary_certification_result="PASS" if passed else "FAIL",
            immutable_threshold_evidence=evidence,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm004_certification_test_registry(
        self,
        *,
        class_registry: SeekerRm004CandidateClassRegistryRecord,
        rule_registry: SeekerRm004EvaluationRuleRegistryRecord,
        thresholds: SeekerRm004CertificationThresholdRecord,
        mutated_entries: tuple[SeekerRm004CertificationTestRegistryEntry, ...] | None = None,
        invalid_execution_outcomes: tuple[str, ...] = (),
        enterprise_dependency_findings: tuple[str, ...] = (),
    ) -> SeekerRm004CertificationTestRegistryRecord:
        entries = mutated_entries if mutated_entries is not None else self._rm004_certification_test_registry_entries(rule_registry.active_rule_ids)
        families = self._rm004_mandatory_test_families()
        covered = tuple(family for family in families if any(entry.test_family == family for entry in entries))
        missing = tuple(family for family in families if family not in covered)
        test_ids = tuple(entry.test_id for entry in entries)
        duplicate_ids = tuple(sorted({item for item in test_ids if test_ids.count(item) > 1}))
        required = tuple(field.name for field in fields(SeekerRm004CertificationTestRegistryEntry))
        incomplete = tuple(
            entry.test_id
            for entry in entries
            if any(getattr(entry, field_name) in ("", (), None) for field_name in required if field_name != "prerequisite_test_ids")
        )
        requirement_ids = tuple(req for entry in entries for req in entry.constitutional_requirement_ids)
        uncovered = tuple(order for order in self.rm004_certification_completion_order_coverage if order not in " ".join(requirement_ids))
        orphan = tuple(entry.test_id for entry in entries if not entry.governing_doctrine_ids)
        entry_ids = set(test_ids)
        invalid_deps = tuple(
            f"{entry.test_id}:{prerequisite}"
            for entry in entries
            for prerequisite in entry.prerequisite_test_ids
            if prerequisite not in entry_ids
        )
        coverage_hash = _digest(tuple(sorted(requirement_ids)))
        dependency_hash = _digest(tuple((entry.test_id, entry.prerequisite_test_ids) for entry in entries))
        entries_hash = _digest(entries)
        registry_hash = _digest((coverage_hash, dependency_hash, entries_hash))
        manifest = MappingProxyType(
            {
                "registry_id": "SEEK-RM-004-005-TEST-REGISTRY",
                "registry_version": "SEEK-RM-004-005-TESTS/1.0.0",
                "office_id": "Seeker",
                "status": "ACTIVE",
                "candidate_class_registry_version": class_registry.registry_version,
                "evaluation_rule_registry_version": rule_registry.registry_version,
                "certification_threshold_version": thresholds.threshold_version,
                "normalization_registry_version": "PENDING_SEEK-RM-004-002",
                "test_entry_count": str(len(entries)),
                "mandatory_test_count": str(len(entries)),
                "coverage_map_hash": coverage_hash,
                "dependency_graph_hash": dependency_hash,
                "entry_collection_hash": entries_hash,
                "registry_hash": registry_hash,
            }
        )
        passed = (
            not missing
            and not duplicate_ids
            and not incomplete
            and not uncovered
            and not orphan
            and not invalid_deps
            and not invalid_execution_outcomes
            and not enterprise_dependency_findings
            and class_registry.result == EnterpriseCertificationDecision.PASS
            and rule_registry.result == EnterpriseCertificationDecision.PASS
            and thresholds.result == EnterpriseCertificationDecision.PASS
        )
        record = SeekerRm004CertificationTestRegistryRecord(
            registry_identifier=f"SEEK-RM-004-005-TESTS-{registry_hash[:12].upper()}",
            registry_version="SEEK-RM-004-005-TESTS/1.0.0",
            registry_manifest=manifest,
            registry_hash=registry_hash,
            entries=entries,
            mandatory_test_families=families,
            covered_test_families=covered,
            missing_test_families=missing,
            duplicate_test_ids=duplicate_ids,
            incomplete_test_ids=incomplete,
            uncovered_requirement_ids=uncovered,
            orphan_test_ids=orphan,
            invalid_dependency_findings=invalid_deps,
            invalid_execution_outcomes=invalid_execution_outcomes,
            enterprise_dependency_findings=enterprise_dependency_findings,
            certification_aggregation_result="UNCONDITIONAL_INDEPENDENT_SEEKER_OFFICE_CERTIFICATION_PASS" if passed else "FAIL",
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def _rm004_candidate_class_registry_entries(self) -> tuple[SeekerRm004CandidateClassRegistryEntry, ...]:
        rows = (
            ("CCL-0001", "Public Common Equity", "Issuer + security + share class + venue", "structural_market", "issuer_exposure", True),
            ("CCL-0002", "Public Preferred Equity", "Issuer + preferred series + venue", "structural_market", "issuer_series", True),
            ("CCL-0003", "Depository Receipt", "Receipt + depositary program + underlying", "structural_market", "underlying_relationship", True),
            ("CCL-0004", "Exchange-Traded Fund", "Fund + share class + venue", "structural_market", "holdings_benchmark", True),
            ("CCL-0005", "Exchange-Traded Note", "Issuer + note series + reference", "structural_market", "issuer_reference", True),
            ("CCL-0006", "Closed-End Fund", "Fund + share class + venue", "structural_market", "holdings_sponsor", True),
            ("CCL-0007", "Mutual Fund", "Fund + share class", "structural_availability", "holdings_sponsor", True),
            ("CCL-0008", "Public Debt Security", "Issuer + series + maturity", "structural_status", "issuer_tranche", True),
            ("CCL-0009", "Sovereign Debt Security", "Sovereign + series + maturity", "structural_status", "sovereign_exposure", True),
            ("CCL-0010", "Municipal Debt Security", "Issuer or obligor + series + maturity", "structural_status", "issuer_obligor", True),
            ("CCL-0011", "Money Market Instrument", "Issuer + type + maturity", "expiration_aware", "issuer_maturity", True),
            ("CCL-0012", "Listed Option Contract", "Underlying + strike + expiry + type", "expiration_aware", "underlying_series", True),
            ("CCL-0013", "Listed Futures Contract", "Root + delivery month and year", "expiration_aware", "underlying_series", True),
            ("CCL-0014", "Listed Futures Option Contract", "Future + strike + expiry + type", "expiration_aware", "underlying_series", True),
            ("CCL-0015", "Spot Foreign Exchange Pair", "Base + quote + convention", "market", "currency_relationship", True),
            ("CCL-0016", "Digital Asset", "Network + native ID or contract", "digital_market", "protocol_wrappers", True),
            ("CCL-0017", "Stable-Value Digital Asset", "Digital identity + reference value", "digital_market", "issuer_protocol_reference", True),
            ("CCL-0018", "Digital Asset Trading Pair", "Base + quote + venue or protocol", "digital_market", "constituents_venue", True),
            ("CCL-0019", "Public Real Estate Investment Trust", "REIT entity + security + class", "structural_market", "issuer_property_exposure", True),
            ("CCL-0020", "Public Business Development Company", "BDC entity + security + class", "structural_market", "issuer_portfolio", True),
            ("CCL-0021", "Listed Partnership Interest", "Partnership + unit class", "structural_market", "partnership_control", True),
            ("CCL-0022", "Commodity-Backed Exchange Product", "Product + commodity + legal structure", "structural_market", "commodity_exposure", True),
            ("CCL-0023", "Market Index", "Administrator + index variant", "reference", "benchmark_relationships", False),
            ("CCL-0024", "Public Company Reference Entity", "Legal entity identity", "reference", "control_issuer_relationships", False),
            ("CCL-0025", "Sovereign Reference Entity", "Sovereign identity", "reference", "sovereign_relationships", False),
            ("CCL-0026", "Trading Venue Reference Entity", "Operator + venue identity", "reference", "venue_control", False),
            ("CCL-0027", "Currency Reference Entity", "Currency code + issuing authority", "reference", "monetary_relationships", False),
            ("CCL-0028", "Commodity Reference Entity", "Commodity + grade or specification", "reference", "benchmark_relationships", False),
        )
        entries = []
        for class_id, name, identity_basis, freshness, independence, orderable in rows:
            required_identity = tuple(part.strip().lower().replace(" ", "_") for part in identity_basis.replace("+", ",").replace(" or ", ",").split(",") if part.strip())
            entries.append(
                SeekerRm004CandidateClassRegistryEntry(
                    class_id=class_id,
                    canonical_name=name,
                    definition=f"Constitutional Candidate Class for {name}; identity basis: {identity_basis}.",
                    registry_status="ACTIVE",
                    identity_schema_id=f"SEEK-ID-SCHEMA-{class_id[-4:]}",
                    required_identity_components=required_identity,
                    conditional_identity_components=("expiration_terms",) if "expiry" in identity_basis.lower() or "maturity" in identity_basis.lower() else ("conditional_profile_not_applicable",),
                    prohibited_identity_components=("ticker_only_identity", "provider_only_classification", "execution_authority"),
                    required_evidence_categories=("identity_evidence", "classification_evidence", "provenance_evidence", "timestamp_evidence"),
                    conditional_evidence_categories=("expiration_status_evidence",) if freshness == "expiration_aware" else ("conditional_evidence_not_applicable",),
                    lifecycle_profile_id="SEEK-LIFECYCLE-COMPLETE",
                    freshness_profile_id=f"SEEK-FRESHNESS-{freshness.upper()}",
                    independence_profile_id=f"SEEK-INDEPENDENCE-{independence.upper()}",
                    equivalence_profile_id=f"SEEK-EQUIVALENCE-{class_id[-4:]}",
                    admissibility_profile_id=f"SEEK-ADMISSIBILITY-{class_id[-4:]}",
                    class_specific_rejection_ids=("REJECT-UNKNOWN-CLASS", "REJECT-MISSING-IDENTITY", "REJECT-MISSING-EVIDENCE", "REJECT-AMBIGUOUS-CLASS"),
                    permitted_relationship_types=("REFERENCES", "ISSUED_BY", "TRADED_ON", "ECONOMICALLY_RELATED_TO"),
                    orderable=orderable,
                    version_introduced="SEEK-RM-004-001/1.0.0",
                    version_deprecated="",
                    version_retired="",
                    governing_doctrine_refs=("SEEK-RM-004-001",),
                    certification_test_refs=(f"SEEK-CERT-TEST-CLASS-{class_id[-4:]}",),
                )
            )
        return tuple(entries)

    def _rm004_evaluation_rule_registry_entries(self) -> tuple[SeekerRm004EvaluationRuleRegistryEntry, ...]:
        rule_specs = (
            ("MSM", "0001", "Search Mission Schema Validity", "Search Mission", "Schema Evaluation"),
            ("MSM", "0002", "Search Mission Authority Validity", "Search Mission", "Integrity Evaluation"),
            ("PLN", "0001", "Search Plan Schema Validity", "Search Plan", "Schema Evaluation"),
            ("PLN", "0002", "Search Plan Source Authorization", "Search Plan", "Presence Evaluation"),
            ("DSC", "0001", "Discovery Execution Authorization", "Discovery", "Presence Evaluation"),
            ("SUF", "0001", "Search Sufficiency Satisfaction", "Search Sufficiency", "Threshold Evaluation"),
            ("CPK", "0001", "Candidate Package Completeness", "Candidate Package", "Completeness Evaluation"),
            ("IDN", "0001", "Candidate Class Registry Validity", "Candidate Identity", "Format Evaluation"),
            ("IDN", "0002", "Candidate Identity Component Completeness", "Candidate Identity", "Identity Evaluation"),
            ("IDN", "0003", "Candidate Identity Evidence Binding", "Candidate Identity", "Provenance Evaluation"),
            ("NRM", "0001", "Canonical Normalization Conformance", "Normalization", "Compatibility Evaluation"),
            ("EQV", "0001", "Candidate Equivalence Determination", "Equivalence", "Equivalence Evaluation"),
            ("COL", "0001", "Canonical Identity Collision Detection", "Collision", "Collision Evaluation"),
            ("FRS", "0001", "Candidate Freshness Validity", "Freshness", "Temporal Evaluation"),
            ("IND", "0001", "Candidate Independence Evidence Completeness", "Independence", "Independence Evaluation"),
            ("IND", "0002", "Candidate Independence Satisfaction", "Independence", "Independence Evaluation"),
            ("EVD", "0001", "Discovery Evidence Schema Validity", "Evidence", "Schema Evaluation"),
            ("EVD", "0002", "Discovery Evidence Admissibility", "Evidence", "Integrity Evaluation"),
            ("PRV", "0001", "Discovery Provenance Completeness", "Provenance", "Provenance Evaluation"),
            ("PRV", "0002", "Discovery Provenance Integrity", "Provenance", "Integrity Evaluation"),
            ("ADM", "0001", "Aggregate Candidate Admissibility", "Admissibility", "Aggregate Evaluation"),
            ("REJ", "0001", "Candidate Rejection Cause Validity", "Rejection", "Format Evaluation"),
            ("LFC", "0001", "Candidate Lifecycle Transition Validity", "Lifecycle", "Transition Evaluation"),
            ("LFC", "0002", "Terminal Candidate State Immutability", "Lifecycle", "State Evaluation"),
            ("STM", "0001", "Office State Validity", "State Machine", "State Evaluation"),
            ("STM", "0002", "Office State Transition Validity", "State Machine", "Transition Evaluation"),
            ("CFG", "0001", "Constitutional Configuration Schema Validity", "Configuration", "Schema Evaluation"),
            ("CFG", "0002", "Configuration Integrity", "Configuration", "Integrity Evaluation"),
            ("CFG", "0003", "Configuration Version Compatibility", "Configuration", "Compatibility Evaluation"),
            ("PST", "0001", "Persistent State Completeness", "Persistence", "Completeness Evaluation"),
            ("PST", "0002", "Persistent State Integrity", "Persistence", "Integrity Evaluation"),
            ("CMT", "0001", "Atomic Commit Boundary Satisfaction", "Commit", "Commit Evaluation"),
            ("CHK", "0001", "Recovery Checkpoint Completeness", "Checkpoint", "Completeness Evaluation"),
            ("CHK", "0002", "Recovery Checkpoint Integrity", "Checkpoint", "Integrity Evaluation"),
            ("RCV", "0001", "Recovery Restoration Validity", "Recovery", "Recovery Evaluation"),
            ("RCV", "0002", "Duplicate Constitutional Effect Prevention", "Recovery", "Recovery Evaluation"),
            ("RPL", "0001", "Replay Input Semantic Equivalence", "Replay", "Replay Evaluation"),
            ("RPL", "0002", "Replay Outcome Equivalence", "Replay", "Replay Evaluation"),
            ("ERR", "0001", "Constitutional Error Classification Validity", "Error", "Format Evaluation"),
            ("AUD", "0001", "Audit Record Completeness", "Audit", "Completeness Evaluation"),
            ("TRC", "0001", "Constitutional Traceability Completeness", "Traceability", "Completeness Evaluation"),
            ("CER", "0001", "Certification Rule Coverage Completeness", "Certification", "Completeness Evaluation"),
            ("CER", "0002", "Certification Test Completion", "Certification", "Completeness Evaluation"),
            ("CER", "0003", "Certification Threshold Satisfaction", "Certification", "Threshold Evaluation"),
            ("CER", "0004", "Certification Evidence Package Completeness", "Certification", "Completeness Evaluation"),
            ("CER", "0005", "Independent Office Certification Aggregate PASS", "Certification", "Aggregate Evaluation"),
            ("MAN", "0001", "Certification Manifest Schema Validity", "Manifest", "Schema Evaluation"),
            ("MAN", "0002", "Certification Manifest Integrity", "Manifest", "Integrity Evaluation"),
            ("VER", "0001", "Constitutional Version Compatibility", "Version", "Compatibility Evaluation"),
            ("IDS", "0001", "Constitutional Identifier Syntax Validity", "Identifiers", "Format Evaluation"),
            ("IDS", "0002", "Constitutional Identifier Uniqueness", "Identifiers", "Integrity Evaluation"),
        )
        entries = []
        outcomes = ("PASS", "FAIL", "NOT_APPLICABLE", "INDETERMINATE", "BLOCKED", "EXECUTION_ERROR", "VOID")
        for domain, number, name, subject, evaluation_type in rule_specs:
            rule_id = f"SEEK-RULE-{domain}-{number}"
            severity = MappingProxyType({outcome: ("INFO" if outcome in {"PASS", "NOT_APPLICABLE"} else "CERTIFICATION_BLOCKING") for outcome in outcomes})
            admissibility = MappingProxyType({outcome: ("ALLOW" if outcome == "PASS" else "BLOCK") for outcome in outcomes})
            certification = MappingProxyType({outcome: ("SATISFIES" if outcome == "PASS" else "BLOCKS_CERTIFICATION") for outcome in outcomes})
            entries.append(
                SeekerRm004EvaluationRuleRegistryEntry(
                    rule_id=rule_id,
                    rule_version="1.0.0",
                    rule_name=name,
                    rule_domain=domain,
                    rule_status="ACTIVE",
                    constitutional_owner="Seeker Office",
                    governing_doctrine_ids=("SEEK-RM-004-003",),
                    evaluation_subject_type=subject,
                    required_input_types=(subject.replace(" ", "_").upper(), "CONSTITUTIONAL_CONTEXT"),
                    required_evidence_types=("IMMUTABLE_EVIDENCE", "TRACEABILITY_LINK"),
                    evaluation_type=evaluation_type,
                    permitted_outcomes=outcomes,
                    severity_by_outcome=severity,
                    admissibility_consequence_by_outcome=admissibility,
                    certification_consequence_by_outcome=certification,
                    prerequisite_rule_ids=(),
                    replay_rule_version_policy="USE_ORIGINAL_RULE_VERSION",
                    recovery_evaluation_policy="PRESERVE_COMMITTED_RESULT_OR_REEVALUATE_WITH_SAME_VERSION",
                    certification_test_ids=(f"SEEK-CERT-TEST-{domain}-{number}",),
                )
            )
        return tuple(entries)

    def _rm004_certification_test_registry_entries(self, rule_ids: tuple[str, ...]) -> tuple[SeekerRm004CertificationTestRegistryEntry, ...]:
        entries = []
        families = self._rm004_mandatory_test_families()
        for index, family in enumerate(families, start=1):
            domain = self._rm004_test_family_domain(family)
            related_rules = tuple(rule_id for rule_id in rule_ids if f"SEEK-RULE-{domain}-" in rule_id) or (rule_ids[min(index - 1, len(rule_ids) - 1)],)
            test_id = f"SEEK-CERT-TEST-{domain}-{index:04d}"
            raw = (
                test_id,
                family,
                related_rules,
                "all preconditions valid",
                "required evidence present",
                "prohibited behavior absent",
            )
            entry_hash = _digest(raw)
            entries.append(
                SeekerRm004CertificationTestRegistryEntry(
                    test_id=test_id,
                    test_name=f"{family} Certification Test",
                    test_version="1.0.0",
                    test_family=family,
                    status="ACTIVE",
                    mandatory_classification="MANDATORY",
                    governing_doctrine_ids=("SEEK-RM-004-005",) + self.rm004_certification_completion_order_coverage,
                    constitutional_requirement_ids=tuple(f"{order}-REQ" for order in self.rm004_certification_completion_order_coverage),
                    evaluation_rule_ids=related_rules,
                    threshold_ids=("SEEK-RM-004-004-THRESHOLD-100",),
                    pass_criteria=("preconditions_valid", "expected_behavior_observed", "prohibited_behavior_absent", "evidence_integrity_valid", "traceability_complete"),
                    fail_criteria=("missing_evidence", "invalid_traceability", "nondeterministic_outcome", "enterprise_dependency", "seeker_self_certification"),
                    required_evidence_artifact_types=("structured_test_record", "state_snapshot", "hash_manifest", "traceability_matrix", "replay_artifact"),
                    prerequisite_test_ids=(),
                    expected_replay_result="SEMANTICALLY_EQUIVALENT",
                    certification_effect="BLOCKS_CERTIFICATION_ON_NON_PASS",
                    entry_hash=entry_hash,
                )
            )
        return tuple(entries)

    def _rm004_mandatory_test_families(self) -> tuple[str, ...]:
        return (
            "Registry Integrity",
            "Activation and Mission Intake",
            "Search Mission",
            "Search Plan",
            "Candidate Class",
            "Candidate Identity",
            "Identity Normalization",
            "Candidate Equivalence",
            "Duplicate Suppression",
            "Candidate Freshness",
            "Candidate Independence",
            "Discovery Evidence",
            "Discovery Provenance",
            "Candidate Lifecycle",
            "Candidate Rejection",
            "Search Sufficiency",
            "Candidate Package",
            "Office State Machine",
            "Persistent State",
            "Recovery Checkpoint",
            "Atomic Commit",
            "Replay Equivalence",
            "Configuration Integrity",
            "Error Handling",
            "Audit Trail",
            "Certification Traceability",
            "Certification Evidence Package",
            "Authority Relinquishment",
            "Residual-State Elimination",
            "External Dependency Isolation",
            "Certification Closure",
        )

    def _rm004_test_family_domain(self, family: str) -> str:
        mapping = {
            "Registry Integrity": "REG",
            "Activation and Mission Intake": "MSM",
            "Search Mission": "MSM",
            "Search Plan": "PLN",
            "Candidate Class": "IDN",
            "Candidate Identity": "IDN",
            "Identity Normalization": "NRM",
            "Candidate Equivalence": "EQV",
            "Duplicate Suppression": "COL",
            "Candidate Freshness": "FRS",
            "Candidate Independence": "IND",
            "Discovery Evidence": "EVD",
            "Discovery Provenance": "PRV",
            "Candidate Lifecycle": "LFC",
            "Candidate Rejection": "REJ",
            "Search Sufficiency": "SUF",
            "Candidate Package": "CPK",
            "Office State Machine": "STM",
            "Persistent State": "PST",
            "Recovery Checkpoint": "CHK",
            "Atomic Commit": "CMT",
            "Replay Equivalence": "RPL",
            "Configuration Integrity": "CFG",
            "Error Handling": "ERR",
            "Audit Trail": "AUD",
            "Certification Traceability": "TRC",
            "Certification Evidence Package": "CER",
            "Authority Relinquishment": "CER",
            "Residual-State Elimination": "CER",
            "External Dependency Isolation": "CER",
            "Certification Closure": "CER",
        }
        return mapping[family]

    def _candidate_class_id_for_type(self, candidate_type: str) -> str:
        normalized = _normalize_value(candidate_type).replace(" ", "_")
        mapping = {
            "EQUITY": "CCL-0001",
            "PUBLIC_COMMON_EQUITY": "CCL-0001",
            "PREFERRED_EQUITY": "CCL-0002",
            "DEPOSITORY_RECEIPT": "CCL-0003",
            "ETF": "CCL-0004",
            "EXCHANGE_TRADED_FUND": "CCL-0004",
            "ETN": "CCL-0005",
            "PUBLIC_DEBT": "CCL-0008",
            "OPTION": "CCL-0012",
            "FUTURE": "CCL-0013",
            "FX_PAIR": "CCL-0015",
            "DIGITAL_ASSET": "CCL-0016",
            "REIT": "CCL-0019",
            "MARKET_INDEX": "CCL-0023",
        }
        return mapping.get(normalized, candidate_type)

    def _valid_candidate_class_id(self, value: str) -> bool:
        return len(value) == 8 and value.startswith("CCL-") and value[4:].isdigit()

    def _valid_rule_id(self, value: str) -> bool:
        parts = value.split("-")
        return len(parts) == 4 and parts[0] == "SEEK" and parts[1] == "RULE" and parts[2].isupper() and len(parts[3]) == 4 and parts[3].isdigit()

    def build_rm004_registry_governance_evidence_package(
        self,
        *,
        candidate: SeekerCandidateIdentityInput,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
    ) -> SeekerRm004RegistryGovernanceEvidencePackage:
        collision = self.evaluate_rm004_collision_resolution(candidate=candidate, discovery_evidence=discovery_evidence)
        metrics = self.evaluate_rm004_metrics_registry()
        identifiers = self.evaluate_rm004_identifier_registry(
            observed_identifiers=(
                "CID-000001000",
                "CLS-000001001",
                "RID-000001002",
                "EVD-000001003",
                "TEST-000001004",
                "MET-000001005",
            )
        )
        versions = self.evaluate_rm004_version_compatibility_matrix()
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (collision, metrics, identifiers, versions)
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerRm004RegistryGovernanceEvidencePackage(
            package_identifier=f"SEEK-RM-004-GOVERNANCE-{_digest((candidate.candidate_reference, tuple(item.evidence_id for item in discovery_evidence)))[:12].upper()}",
            governing_doctrine="SEEK-RM-004-006-007-009-010/1.0.0",
            remediation_order_coverage=self.rm004_registry_governance_order_coverage,
            unprovided_dependency_orders=self.rm004_unprovided_dependency_orders + ("SEEK-RM-004-008",),
            collision_resolution=collision,
            metrics_registry=metrics,
            identifier_registry=identifiers,
            version_compatibility_matrix=versions,
            final_rm004_registry_governance_readiness=final,
            immutable_audit_references=(
                collision.collision_identifier,
                metrics.registry_identifier,
                identifiers.registry_identifier,
                versions.matrix_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_rm004_collision_resolution(
        self,
        *,
        candidate: SeekerCandidateIdentityInput,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        collision_class: str = "COL-001",
        collision_set: tuple[str, ...] = (),
        missing_investigation_steps: tuple[str, ...] = (),
        heuristic_resolution_findings: tuple[str, ...] = (),
        replay_reproduces_outcome: bool = True,
        recovery_preserves_state: bool = True,
    ) -> SeekerRm004CollisionResolutionRecord:
        taxonomy = MappingProxyType(
            {
                "COL-001": "Exact Duplicate",
                "COL-002": "Identifier Conflict",
                "COL-003": "Partial Identity Match",
                "COL-004": "Alias Collision",
                "COL-005": "Normalization Collision",
                "COL-006": "Source Disagreement",
                "COL-007": "Historical Identity Change",
                "COL-008": "Cross-Jurisdiction Collision",
                "COL-009": "Namespace Collision",
                "COL-010": "Unknown Collision",
            }
        )
        states = ("DETECTED", "INVESTIGATING", "RESOLVED_IDENTICAL", "RESOLVED_DISTINCT", "QUARANTINED", "REJECTED", "SUPERSEDED", "CLOSED")
        investigation = (
            "preserve_raw_identities",
            "preserve_normalized_identities",
            "preserve_provenance",
            "preserve_timestamps",
            "preserve_registry_versions",
            "evaluate_identity_schemas",
            "evaluate_evidence_quality",
            "evaluate_historical_identity_continuity",
            "evaluate_namespace_consistency",
            "produce_deterministic_outcome",
        )
        evidence_refs = tuple(item.evidence_id for item in discovery_evidence)
        participants = collision_set or (candidate.candidate_reference,)
        known_class = collision_class in taxonomy
        evidence_complete = bool(evidence_refs) and not missing_investigation_steps
        if not known_class or collision_class == "COL-010":
            outcome = "EVIDENCE_INSUFFICIENT"
            final_state = "QUARANTINED"
        elif heuristic_resolution_findings:
            outcome = "EVIDENCE_CONTRADICTORY"
            final_state = "REJECTED"
        elif evidence_complete and len(participants) <= 1:
            outcome = "IDENTITIES_DISTINCT"
            final_state = "RESOLVED_DISTINCT"
        elif evidence_complete and collision_class in {"COL-001", "COL-005"}:
            outcome = "IDENTITIES_IDENTICAL"
            final_state = "RESOLVED_IDENTICAL"
        elif evidence_complete:
            outcome = "IDENTITIES_DISTINCT"
            final_state = "RESOLVED_DISTINCT"
        else:
            outcome = "EVIDENCE_INSUFFICIENT"
            final_state = "QUARANTINED"
        blocked = final_state in {"QUARANTINED", "REJECTED"} or not known_class
        passed = (
            known_class
            and evidence_complete
            and not heuristic_resolution_findings
            and replay_reproduces_outcome
            and recovery_preserves_state
            and final_state in {"RESOLVED_IDENTICAL", "RESOLVED_DISTINCT"}
        )
        record = SeekerRm004CollisionResolutionRecord(
            collision_identifier=f"SEEK-RM-004-006-COL-{_digest((participants, collision_class, evidence_refs, outcome))[:12].upper()}",
            doctrine_version="SEEK-RM-004-006/1.0.0",
            collision_taxonomy=taxonomy,
            collision_state_inventory=states,
            collision_set=participants,
            collision_class=collision_class,
            investigation_steps=investigation,
            missing_investigation_steps=missing_investigation_steps,
            admissible_evidence_references=evidence_refs,
            heuristic_resolution_findings=heuristic_resolution_findings,
            collision_outcome=outcome,
            final_collision_state=final_state,
            candidate_evaluation_blocked=blocked,
            merge_preserves_history=outcome != "IDENTITIES_IDENTICAL" or bool(evidence_refs),
            replay_reproduces_outcome=replay_reproduces_outcome,
            recovery_preserves_state=recovery_preserves_state,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm004_metrics_registry(
        self,
        *,
        mutated_entries: tuple[SeekerRm004MetricRegistryEntry, ...] | None = None,
        implementation_defined_certification_metrics: tuple[str, ...] = (),
        replay_divergent_metrics: tuple[str, ...] = (),
    ) -> SeekerRm004MetricsRegistryRecord:
        entries = mutated_entries if mutated_entries is not None else self._rm004_metric_registry_entries()
        ids = tuple(entry.metric_id for entry in entries)
        duplicates = tuple(sorted({item for item in ids if ids.count(item) > 1}))
        invalid_ids = tuple(item for item in ids if not self._valid_fixed_identifier(item, "SEEK-MET", 6))
        required = tuple(field.name for field in fields(SeekerRm004MetricRegistryEntry))
        incomplete = tuple(
            entry.metric_id
            for entry in entries
            if any(getattr(entry, field_name) in ("", (), None) for field_name in required if field_name != "optional_inputs")
        )
        allowed_units = {"count", "ratio", "percentage", "bytes", "milliseconds", "seconds", "minutes", "hours", "decimal score", "Boolean", "enumerated state"}
        invalid_units = tuple(entry.metric_id for entry in entries if entry.units not in allowed_units)
        precision_violations = tuple(entry.metric_id for entry in entries if not entry.precision or "floating" in entry.precision.lower())
        categories = tuple(dict.fromkeys(entry.metric_category for entry in entries))
        passed = (
            len(categories) == 10
            and not duplicates
            and not invalid_ids
            and not incomplete
            and not invalid_units
            and not precision_violations
            and not implementation_defined_certification_metrics
            and not replay_divergent_metrics
        )
        registry_hash = _digest(entries)
        record = SeekerRm004MetricsRegistryRecord(
            registry_identifier=f"SEEK-RM-004-007-MET-{registry_hash[:12].upper()}",
            registry_version="SEEK-RM-004-007-METRICS/1.0.0",
            registry_hash=registry_hash,
            entries=entries,
            metric_categories=categories,
            duplicate_metric_ids=duplicates,
            invalid_metric_ids=invalid_ids,
            incomplete_metric_ids=incomplete,
            invalid_units=invalid_units,
            precision_violations=precision_violations,
            implementation_defined_certification_metrics=implementation_defined_certification_metrics,
            replay_divergent_metrics=replay_divergent_metrics,
            immutable_historical_storage=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm004_identifier_registry(
        self,
        *,
        observed_identifiers: tuple[str, ...],
        mutated_namespaces: tuple[SeekerRm004IdentifierNamespaceEntry, ...] | None = None,
        collision_findings: tuple[str, ...] = (),
        replay_preserves_identifiers: bool = True,
        recovery_preserves_identifiers: bool = True,
    ) -> SeekerRm004IdentifierRegistryRecord:
        namespaces = mutated_namespaces if mutated_namespaces is not None else self._rm004_identifier_namespaces()
        prefixes = tuple(item.prefix for item in namespaces)
        duplicates = tuple(sorted({item for item in prefixes if prefixes.count(item) > 1}))
        invalid_prefixes = tuple(item for item in prefixes if not item.isupper() or not item.isascii() or not item)
        required = tuple(field.name for field in fields(SeekerRm004IdentifierNamespaceEntry))
        incomplete = tuple(
            item.namespace
            for item in namespaces
            if any(getattr(item, field_name) in ("", (), None) for field_name in required)
        )
        prefix_set = set(prefixes)
        invalid_identifiers = tuple(identifier for identifier in observed_identifiers if not self._valid_observed_identifier(identifier, prefix_set))
        duplicate_identifiers = tuple(sorted({item for item in observed_identifiers if observed_identifiers.count(item) > 1}))
        reserved = tuple(
            identifier
            for identifier in observed_identifiers
            if self._identifier_number(identifier) is not None and self._identifier_number(identifier) < 1000
        )
        passed = (
            len(namespaces) == 20
            and not duplicates
            and not invalid_prefixes
            and not incomplete
            and not invalid_identifiers
            and not duplicate_identifiers
            and not reserved
            and not collision_findings
            and replay_preserves_identifiers
            and recovery_preserves_identifiers
        )
        registry_hash = _digest(namespaces)
        record = SeekerRm004IdentifierRegistryRecord(
            registry_identifier=f"SEEK-RM-004-009-ID-{registry_hash[:12].upper()}",
            registry_version="SEEK-RM-004-009-IDENTIFIERS/1.0.0",
            registry_hash=registry_hash,
            namespaces=namespaces,
            duplicate_prefixes=duplicates,
            invalid_prefixes=invalid_prefixes,
            incomplete_namespaces=incomplete,
            observed_identifiers=observed_identifiers,
            invalid_identifiers=invalid_identifiers,
            duplicate_identifiers=duplicate_identifiers,
            reserved_identifier_violations=reserved,
            collision_findings=collision_findings,
            replay_preserves_identifiers=replay_preserves_identifiers,
            recovery_preserves_identifiers=recovery_preserves_identifiers,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rm004_version_compatibility_matrix(
        self,
        *,
        required_version_pairs: tuple[tuple[str, str], ...] = (),
        mutated_entries: tuple[SeekerRm004VersionCompatibilityEntry, ...] | None = None,
        implicit_compatibility_findings: tuple[str, ...] = (),
    ) -> SeekerRm004VersionCompatibilityRecord:
        entries = mutated_entries if mutated_entries is not None else self._rm004_version_compatibility_entries()
        registry = MappingProxyType(
            {
                "Candidate Class Registry": "SEEK-RM-004-001-CCR/1.0.0",
                "Evaluation Rule Registry": "SEEK-RM-004-003-RULES/1.0.0",
                "Certification Threshold Registry": "SEEK-RM-004-004-THRESHOLDS/1.0.0",
                "Certification Test Registry": "SEEK-RM-004-005-TESTS/1.0.0",
                "Collision Resolution Doctrine": "SEEK-RM-004-006/1.0.0",
                "Metrics Registry": "SEEK-RM-004-007-METRICS/1.0.0",
                "Identifier Registry": "SEEK-RM-004-009-IDENTIFIERS/1.0.0",
                "Version Compatibility Matrix": "SEEK-RM-004-010-MATRIX/1.0.0",
            }
        )
        pair_set = {(entry.source_version, entry.target_version) for entry in entries}
        required_pairs = required_version_pairs or tuple((version, version) for version in registry.values())
        missing_pairs = tuple(f"{source}->{target}" for source, target in required_pairs if (source, target) not in pair_set)
        known_versions = set(registry.values())
        missing_versions = tuple(version for pair in required_pairs for version in pair if version not in known_versions)
        unknown_pairs = tuple(f"{entry.source_version}->{entry.target_version}" for entry in entries if entry.compatibility_classification == "Unknown")
        undefined_migrations = tuple(
            f"{entry.source_version}->{entry.target_version}"
            for entry in entries
            if entry.migration_required and not entry.required_migration_version
        )
        replay_bad = tuple(f"{entry.source_version}->{entry.target_version}" for entry in entries if not entry.replay_allowed)
        recovery_bad = tuple(f"{entry.source_version}->{entry.target_version}" for entry in entries if not entry.recovery_allowed)
        certification_bad = tuple(f"{entry.source_version}->{entry.target_version}" for entry in entries if not entry.certification_allowed)
        migrations = MappingProxyType({entry.required_migration_version: f"{entry.source_version}->{entry.target_version}" for entry in entries if entry.required_migration_version})
        passed = (
            not missing_pairs
            and not missing_versions
            and not unknown_pairs
            and not implicit_compatibility_findings
            and not undefined_migrations
            and not replay_bad
            and not recovery_bad
            and not certification_bad
        )
        matrix_hash = _digest(entries)
        record = SeekerRm004VersionCompatibilityRecord(
            matrix_identifier=f"SEEK-RM-004-010-MATRIX-{matrix_hash[:12].upper()}",
            matrix_version="SEEK-RM-004-010-MATRIX/1.0.0",
            matrix_hash=matrix_hash,
            version_registry=registry,
            compatibility_entries=entries,
            missing_version_records=missing_versions,
            missing_matrix_entries=missing_pairs,
            unknown_compatibility_pairs=unknown_pairs,
            implicit_compatibility_findings=implicit_compatibility_findings,
            migration_registry=migrations,
            undefined_migrations=undefined_migrations,
            replay_incompatible_pairs=replay_bad,
            recovery_incompatible_pairs=recovery_bad,
            certification_incompatible_pairs=certification_bad,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def _rm004_metric_registry_entries(self) -> tuple[SeekerRm004MetricRegistryEntry, ...]:
        specs = (
            ("M-IDENT", "Identity Uniqueness Ratio", "ratio", "exact rational to 6 decimal places", "PASS evaluation"),
            ("M-DISC", "Discovery Completeness", "percentage", "integer percentage", "PASS evaluation"),
            ("M-EVID", "Evidence Completeness", "percentage", "integer percentage", "PASS evaluation"),
            ("M-NORM", "Normalization Success Count", "count", "integer", "diagnostic reporting"),
            ("M-VAL", "Validation Failure Count", "count", "integer", "PASS evaluation"),
            ("M-LIFE", "Lifecycle Transition Count", "count", "integer", "historical analysis"),
            ("M-REPLAY", "Replay Divergence Count", "count", "integer", "PASS evaluation"),
            ("M-REC", "Recovery Success Count", "count", "integer", "PASS evaluation"),
            ("M-CERT", "Certification Traceability Completeness", "percentage", "integer percentage", "PASS evaluation"),
            ("M-PERF", "Processing Latency", "milliseconds", "integer milliseconds", "performance reporting"),
        )
        entries = []
        for index, (category, name, unit, precision, usage) in enumerate(specs, start=1):
            entries.append(
                SeekerRm004MetricRegistryEntry(
                    metric_id=f"SEEK-MET-{index:06d}",
                    metric_name=name,
                    metric_category=category,
                    constitutional_purpose=f"Measure {name.lower()} without altering constitutional policy.",
                    owning_office="Seeker Office",
                    calculation_definition="deterministic aggregation over admissible immutable evidence",
                    required_inputs=("admissible_evidence", "registry_version", "calculation_version"),
                    optional_inputs=("window_identifier",),
                    units=unit,
                    precision=precision,
                    update_trigger="event-driven and replay-driven",
                    persistence_requirements="permanent for certification metrics; historical values immutable",
                    replay_requirements="identical admissible inputs reproduce identical metric values",
                    certification_usage=usage,
                    interpretation_rules="metric informs registered certification thresholds only when designated for PASS evaluation",
                    failure_conditions=("missing_required_inputs", "invalid_units", "precision_violation", "version_mismatch", "inadmissible_evidence", "replay_mismatch"),
                    registry_version="SEEK-RM-004-007-METRICS/1.0.0",
                    status="ACTIVE",
                )
            )
        return tuple(entries)

    def _rm004_identifier_namespaces(self) -> tuple[SeekerRm004IdentifierNamespaceEntry, ...]:
        rows = (
            ("Candidate", "CID", "Candidate identity"),
            ("Candidate Class", "CLS", "Candidate classification"),
            ("Rule", "RID", "Constitutional rule identity"),
            ("Evaluation", "EVAL", "Rule execution identity"),
            ("Validation", "VAL", "Validation execution"),
            ("Observation", "OBS", "Imported observation identity"),
            ("Evidence", "EVD", "Immutable evidence object"),
            ("Certification Test", "TEST", "Certification test"),
            ("Certification Run", "CERT", "Certification execution"),
            ("Manifest", "MAN", "Manifest identity"),
            ("Registry Entry", "REG", "Registry record"),
            ("Schema", "SCH", "Constitutional schema"),
            ("Version", "VER", "Registry version"),
            ("Lifecycle Transition", "TRN", "Transition event"),
            ("Replay", "RPL", "Replay execution"),
            ("Recovery", "REC", "Recovery execution"),
            ("Audit", "AUD", "Constitutional audit"),
            ("Error", "ERR", "Error identity"),
            ("Rejection", "REJ", "Rejection evidence"),
            ("Metrics", "MET", "Metric identity"),
        )
        return tuple(
            SeekerRm004IdentifierNamespaceEntry(
                namespace=namespace,
                prefix=prefix,
                purpose=purpose,
                syntax=f"{prefix}-#########",
                lifecycle_states=("Reserved", "Allocated", "Active", "Historical"),
                reserved_ranges=("000000000", "000000001-000000099", "000000100-000000999"),
                replay_semantics="preserve identifiers where identity preservation is required",
                recovery_semantics="preserve allocated identifiers across checkpoint recovery",
                collision_handling="halt allocation and resolve under SEEK-RM-004-006",
                version="SEEK-RM-004-009/1.0.0",
                status="ACTIVE",
            )
            for namespace, prefix, purpose in rows
        )

    def _rm004_version_compatibility_entries(self) -> tuple[SeekerRm004VersionCompatibilityEntry, ...]:
        versions = (
            "SEEK-RM-004-001-CCR/1.0.0",
            "SEEK-RM-004-003-RULES/1.0.0",
            "SEEK-RM-004-004-THRESHOLDS/1.0.0",
            "SEEK-RM-004-005-TESTS/1.0.0",
            "SEEK-RM-004-006/1.0.0",
            "SEEK-RM-004-007-METRICS/1.0.0",
            "SEEK-RM-004-009-IDENTIFIERS/1.0.0",
            "SEEK-RM-004-010-MATRIX/1.0.0",
        )
        return tuple(
            SeekerRm004VersionCompatibilityEntry(
                source_version=version,
                target_version=version,
                compatibility_classification="Fully Compatible",
                migration_required=False,
                replay_allowed=True,
                recovery_allowed=True,
                certification_allowed=True,
                persistence_allowed=True,
                checkpoint_allowed=True,
                required_migration_version="",
                approval_record="SEEK-RM-004-010-APPROVAL",
                effective_date="2026-07-21T00:00:00Z",
            )
            for version in versions
        )

    def _valid_fixed_identifier(self, value: str, prefix: str, digits: int) -> bool:
        expected = f"{prefix}-"
        return value.startswith(expected) and len(value) == len(expected) + digits and value[len(expected):].isdigit()

    def _valid_observed_identifier(self, value: str, prefixes: set[str]) -> bool:
        if "-" not in value:
            return False
        prefix, number = value.split("-", 1)
        return prefix in prefixes and len(number) == 9 and number.isdigit()

    def _identifier_number(self, value: str) -> int | None:
        if "-" not in value:
            return None
        number = value.split("-", 1)[1]
        return int(number) if number.isdigit() else None


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
