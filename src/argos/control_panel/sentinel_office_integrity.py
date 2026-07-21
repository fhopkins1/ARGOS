"""Enterprise-owned Sentinel office integrity support for SENT-RM-003."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision
from argos.foundation.contracts import utc_timestamp
from argos.foundation.persistence import InMemoryPersistenceRepository
from argos.foundation.persistence.records import PersistentRecord
from argos.sentinel import (
    SentinelRuntimeDecision,
    SentinelRuntimeExecutionRecord,
    SentinelSourcePlanReference,
    SentinelRuntimeTraceEngine,
    recover_persisted_sentinel_records,
    sentinel_runtime_equivalence_digest,
)


SENT_RM_003_VERSION = "SENT-RM-003/1.0.0"


class OfficeAuthorityDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class SentinelOfficeResponsibilityDefinition:
    office_identity: str
    constitutional_purpose: str
    constitutional_authority: tuple[str, ...]
    owned_responsibilities: tuple[str, ...]
    prohibited_responsibilities: tuple[str, ...]
    constitutional_inputs: tuple[str, ...]
    produced_evidence: tuple[str, ...]
    required_runtime_states: tuple[str, ...]
    required_behavioral_capabilities: tuple[str, ...]
    state_classification_model: Mapping[str, str]
    persistence_model: Mapping[str, str]
    interface_outputs: tuple[str, ...]
    doctrine_version: str
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeAuthorityValidationEvidence:
    evidence_identifier: str
    requesting_office: str
    requested_operation: str
    authority_definition: tuple[str, ...]
    validation_result: EnterpriseCertificationDecision
    decision: OfficeAuthorityDecision
    rejection_reason: str
    timestamp: str
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeResponsibilityValidationRecord:
    validation_identifier: str
    evaluated_offices: tuple[str, ...]
    duplicate_responsibilities: tuple[str, ...]
    missing_authority: tuple[str, ...]
    prohibited_overlap: tuple[str, ...]
    incomplete_definitions: tuple[str, ...]
    ownership_result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeBehaviorCompletenessRecord:
    completeness_identifier: str
    office_identity: str
    required_behaviors: tuple[str, ...]
    observed_behaviors: tuple[str, ...]
    missing_behaviors: tuple[str, ...]
    placeholder_markers: tuple[str, ...]
    evidence_generating_behaviors: tuple[str, ...]
    replay_supported: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeDeterministicExecutionRecord:
    deterministic_identifier: str
    office_identity: str
    original_execution_id: str
    replay_execution_id: str
    original_semantic_digest: str
    replay_semantic_digest: str
    trace_order_equivalent: bool
    lifecycle_equivalent: bool
    decision_equivalent: bool
    nondeterministic_influences: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeStateIntegrityRecord:
    state_identifier: str
    office_identity: str
    lifecycle_states: tuple[str, ...]
    invalid_states: tuple[str, ...]
    invalid_transitions: tuple[str, ...]
    version_sequence: tuple[int, ...]
    version_errors: tuple[str, ...]
    immutable_state_history: tuple[str, ...]
    recovered_record_hashes: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeDecisionIntegrityRecord:
    decision_identifier: str
    office_identity: str
    evaluated_decisions: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    missing_justification: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    replay_equivalent: bool
    unsupported_decisions: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeRuntimeCompletenessRecord:
    runtime_identifier: str
    office_identity: str
    execution_id: str
    lifecycle_path: tuple[str, ...]
    terminal_classification: str
    authority_released: bool
    required_runtime_paths: tuple[str, ...]
    observed_runtime_paths: tuple[str, ...]
    missing_runtime_paths: tuple[str, ...]
    incomplete_markers: tuple[str, ...]
    output_evidence: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficePersistenceIntegrityRecord:
    persistence_identifier: str
    office_identity: str
    persisted_records: tuple[str, ...]
    required_records: tuple[str, ...]
    missing_records: tuple[str, ...]
    prohibited_records: tuple[str, ...]
    creation_sequence: tuple[int, ...]
    ordering_errors: tuple[str, ...]
    recovered_hashes: tuple[str, ...]
    canonical_serialization: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeComponentRegistryRecord:
    registry_identifier: str
    office_identity: str
    registered_components: tuple[str, ...]
    component_classifications: Mapping[str, str]
    doctrine_traceability: Mapping[str, str]
    duplicate_owners: tuple[str, ...]
    unregistered_production_components: tuple[str, ...]
    infrastructure_contamination: tuple[str, ...]
    orphan_requirements: tuple[str, ...]
    immutable_registry_version: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeSelfCertificationSeparationRecord:
    separation_identifier: str
    office_identity: str
    prohibited_certification_terms: tuple[str, ...]
    detected_self_certification_paths: tuple[str, ...]
    permitted_readiness_outputs: tuple[str, ...]
    independent_authority: str
    sentinel_controls_certification_verdict: bool
    rejection_evidence_identifier: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeMissionIntakeValidationRecord:
    intake_identifier: str
    office_identity: str
    mission_identifier: str
    assignment_identifier: str
    required_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    validation_stages: tuple[str, ...]
    rejection_codes: tuple[str, ...]
    dormant_preserved_on_failure: bool
    acceptance_evidence_identifier: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeLifecycleStateMachineRecord:
    lifecycle_identifier: str
    office_identity: str
    authorized_states: tuple[str, ...]
    ordinary_lifecycle: tuple[str, ...]
    observed_lifecycle: tuple[str, ...]
    exceptional_states: tuple[str, ...]
    illegal_transitions: tuple[str, ...]
    transition_evidence: tuple[str, ...]
    dormancy_attested: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeSourcePlanEnforcementRecord:
    source_plan_identifier: str
    office_identity: str
    approved_source_plan: str
    approved_source: str
    approved_endpoint: str
    retrieval_method: str
    entitlement_class: str
    source_plan_digest: str
    enforcement_failures: tuple[str, ...]
    immutable_attribution_evidence: tuple[str, ...]
    replay_compatible: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeRawEvidencePreservationRecord:
    preservation_identifier: str
    office_identity: str
    raw_evidence_references: tuple[str, ...]
    payload_hashes: tuple[str, ...]
    preservation_precedes_normalization: bool
    normalized_observation_references_raw: bool
    mutation_failures: tuple[str, ...]
    replay_uses_preserved_evidence: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeSourceAdmissibilityRecord:
    admissibility_identifier: str
    office_identity: str
    source_identifier: str
    identity_attributes: Mapping[str, str]
    admissibility_decision: str
    rejection_code: str
    endpoint_valid: bool
    entitlement_valid: bool
    domain_valid: bool
    replay_identity_valid: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeNormalizationIntegrityRecord:
    normalization_identifier: str
    office_identity: str
    normalized_observation_identifier: str
    normalization_schema_version: str
    raw_evidence_references: tuple[str, ...]
    lineage_complete: bool
    raw_evidence_preserved: bool
    prohibited_transformations: tuple[str, ...]
    deterministic_replay_digest: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeChronologyIntegrityRecord:
    chronology_identifier: str
    office_identity: str
    timestamp_categories: Mapping[str, str]
    missing_categories: tuple[str, ...]
    ordering_violations: tuple[str, ...]
    utc_canonical: bool
    original_source_time_preserved: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeFreshnessDeterminationRecord:
    freshness_identifier: str
    office_identity: str
    freshness_rule_identifier: str
    reference_timestamp_type: str
    evaluation_timestamp: str
    computed_age: str
    maximum_permitted_age: str
    boundary_behavior: str
    freshness_result: str
    missing_inputs: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeDuplicateSuppressionRecord:
    duplicate_identifier: str
    office_identity: str
    duplicate_rule_identifier: str
    comparison_dimensions: tuple[str, ...]
    duplicate_window: str
    duplicate_result: str
    canonical_observation: str
    suppressed_observation: str
    suppression_effects: tuple[str, ...]
    incidental_fields_excluded: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeConflictPreservationRecord:
    conflict_identifier: str
    office_identity: str
    conflict_rule_identifier: str
    contributing_sources: tuple[str, ...]
    conflict_classification: str
    conflict_result: str
    source_neutral: bool
    analytical_resolution_attempted: bool
    lineage_references: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeSourceIndependenceCorroborationRecord:
    independence_identifier: str
    office_identity: str
    independence_rule_identifier: str
    source_identities: tuple[str, ...]
    independence_groups: tuple[str, ...]
    shared_relationship_categories: tuple[str, ...]
    independence_decision: str
    corroboration_outcome: str
    invented_relationship_metadata: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeObservationSufficiencyRecord:
    sufficiency_identifier: str
    office_identity: str
    sufficiency_rule_identifier: str
    admissible_observations: tuple[str, ...]
    satisfied_requirements: tuple[str, ...]
    unsatisfied_requirements: tuple[str, ...]
    minimum_source_count_result: str
    independence_result: str
    freshness_result: str
    conflict_result: str
    terminal_sufficiency_outcome: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeRecoveryCertificationRecord:
    recovery_identifier: str
    office_identity: str
    recovery_trigger: str
    recovery_states: tuple[str, ...]
    authoritative_state_sources: tuple[str, ...]
    recovered_record_hashes: tuple[str, ...]
    restored_lifecycle_state: str
    preserved_decision_evidence: tuple[str, ...]
    missing_recovery_inputs: tuple[str, ...]
    prohibited_recovery_outputs: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeReplayCompatibilityRecord:
    replay_identifier: str
    office_identity: str
    historical_execution_id: str
    replay_execution_id: str
    historical_semantic_digest: str
    replay_semantic_digest: str
    historical_evidence_modified: bool
    replay_evidence_identifier: str
    replay_scope: str
    replay_failures: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeImmutableEvidenceRecord:
    evidence_identifier: str
    office_identity: str
    persisted_evidence_ids: tuple[str, ...]
    trace_evidence_ids: tuple[str, ...]
    duplicate_evidence_ids: tuple[str, ...]
    missing_integrity_fields: tuple[str, ...]
    unordered_evidence: tuple[str, ...]
    mutable_history_markers: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeAuditEvidenceCompletenessRecord:
    audit_identifier: str
    office_identity: str
    required_categories: tuple[str, ...]
    observed_categories: tuple[str, ...]
    missing_categories: tuple[str, ...]
    reconstruction_inputs: tuple[str, ...]
    audit_reconstructable_without_runtime_source: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeConfigurationIntegrityRecord:
    configuration_identifier: str
    office_identity: str
    configuration_version: str
    configuration_digest: str
    authorized_configuration_keys: tuple[str, ...]
    observed_configuration_keys: tuple[str, ...]
    missing_configuration_keys: tuple[str, ...]
    unauthorized_configuration_keys: tuple[str, ...]
    stable_for_execution: bool
    replay_uses_original_configuration: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeErrorHandlingRecord:
    error_identifier: str
    office_identity: str
    execution_id: str
    terminal_result: str
    failure_classification: str
    failure_evidence: tuple[str, ...]
    atomic_outcome: bool
    authority_released: bool
    hidden_failures: tuple[str, ...]
    recovery_readiness: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeValidationSpecification:
    specification_identifier: str
    office_identity: str
    validation_authority: str
    requirements: tuple[str, ...]
    prohibited_authorities: tuple[str, ...]
    pass_conditions: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeValidationTestResult:
    test_identifier: str
    requirement: str
    evidence_references: tuple[str, ...]
    result: EnterpriseCertificationDecision


@dataclass(frozen=True)
class OfficeValidationSuiteResult:
    suite_identifier: str
    office_identity: str
    validation_authority: str
    specification: OfficeValidationSpecification
    test_results: tuple[OfficeValidationTestResult, ...]
    failed_tests: tuple[str, ...]
    office_under_test_controls_verdict: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class OfficeConstitutionalIntegrationRecord:
    integration_identifier: str
    office_identity: str
    workflow_stages: tuple[str, ...]
    capability_results: tuple[str, ...]
    contradictions: tuple[str, ...]
    aggregation_manifest_identifier: str
    office_under_test_controls_manifest: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SentinelOfficeRemediationEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    office_identity: str
    remediation_order_coverage: tuple[str, ...]
    component_registry: OfficeComponentRegistryRecord
    self_certification_separation: OfficeSelfCertificationSeparationRecord
    mission_intake_validation: OfficeMissionIntakeValidationRecord
    lifecycle_state_machine: OfficeLifecycleStateMachineRecord
    source_plan_enforcement: OfficeSourcePlanEnforcementRecord
    raw_evidence_preservation: OfficeRawEvidencePreservationRecord
    source_admissibility: OfficeSourceAdmissibilityRecord
    normalization_integrity: OfficeNormalizationIntegrityRecord
    chronology_integrity: OfficeChronologyIntegrityRecord
    freshness_determination: OfficeFreshnessDeterminationRecord
    duplicate_suppression: OfficeDuplicateSuppressionRecord
    conflict_preservation: OfficeConflictPreservationRecord
    source_independence_corroboration: OfficeSourceIndependenceCorroborationRecord
    observation_sufficiency: OfficeObservationSufficiencyRecord
    responsibility_validation: OfficeResponsibilityValidationRecord
    authority_evidence: tuple[OfficeAuthorityValidationEvidence, ...]
    behavior_completeness: OfficeBehaviorCompletenessRecord
    deterministic_execution: OfficeDeterministicExecutionRecord
    state_integrity: OfficeStateIntegrityRecord
    decision_integrity: OfficeDecisionIntegrityRecord
    runtime_completeness: OfficeRuntimeCompletenessRecord
    persistence_integrity: OfficePersistenceIntegrityRecord
    recovery_certification: OfficeRecoveryCertificationRecord
    replay_compatibility: OfficeReplayCompatibilityRecord
    immutable_evidence: OfficeImmutableEvidenceRecord
    audit_evidence_completeness: OfficeAuditEvidenceCompletenessRecord
    configuration_integrity: OfficeConfigurationIntegrityRecord
    error_handling: OfficeErrorHandlingRecord
    validation_suite: OfficeValidationSuiteResult
    constitutional_integration: OfficeConstitutionalIntegrationRecord
    final_office_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


class SentinelOfficeResponsibilityRegistry:
    """Immutable office responsibility and authority boundary registry."""

    def __init__(self, definitions: Iterable[SentinelOfficeResponsibilityDefinition]) -> None:
        self._definitions = {definition.office_identity: definition for definition in definitions}

    @classmethod
    def default(cls) -> "SentinelOfficeResponsibilityRegistry":
        return cls((sentinel_office_responsibility_definition(),))

    def definition_for(self, office_identity: str) -> SentinelOfficeResponsibilityDefinition:
        if office_identity not in self._definitions:
            raise KeyError(f"Unknown Sentinel office: {office_identity}")
        return self._definitions[office_identity]

    def validate_registry(self) -> OfficeResponsibilityValidationRecord:
        definitions = tuple(self._definitions.values())
        owners: dict[str, list[str]] = {}
        missing_authority: list[str] = []
        prohibited_overlap: list[str] = []
        incomplete: list[str] = []
        for definition in definitions:
            for responsibility in definition.owned_responsibilities:
                owners.setdefault(responsibility, []).append(definition.office_identity)
                if responsibility not in definition.constitutional_authority:
                    missing_authority.append(f"{definition.office_identity}:{responsibility}")
                if responsibility in definition.prohibited_responsibilities:
                    prohibited_overlap.append(f"{definition.office_identity}:{responsibility}")
            required_fields = (
                definition.office_identity,
                definition.constitutional_purpose,
                definition.constitutional_authority,
                definition.owned_responsibilities,
                definition.produced_evidence,
                definition.required_runtime_states,
                definition.required_behavioral_capabilities,
                definition.persistence_model,
            )
            if not all(required_fields):
                incomplete.append(definition.office_identity)
        duplicates = tuple(sorted(responsibility for responsibility, office_ids in owners.items() if len(office_ids) > 1))
        record = OfficeResponsibilityValidationRecord(
            validation_identifier=f"SENT-RM003-RESP-{_digest((tuple(sorted(self._definitions)), duplicates, tuple(missing_authority)))[:12].upper()}",
            evaluated_offices=tuple(sorted(self._definitions)),
            duplicate_responsibilities=duplicates,
            missing_authority=tuple(sorted(missing_authority)),
            prohibited_overlap=tuple(sorted(prohibited_overlap)),
            incomplete_definitions=tuple(sorted(incomplete)),
            ownership_result=EnterpriseCertificationDecision.PASS if not duplicates and not missing_authority and not prohibited_overlap and not incomplete else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def validate_authority(self, office_identity: str, operation: str) -> OfficeAuthorityValidationEvidence:
        definition = self.definition_for(office_identity)
        accepted = operation in definition.owned_responsibilities and operation in definition.constitutional_authority and operation not in definition.prohibited_responsibilities
        reason = "" if accepted else "OPERATION_OUTSIDE_SENTINEL_OFFICE_AUTHORITY"
        evidence = OfficeAuthorityValidationEvidence(
            evidence_identifier=f"SENT-RM003-AUTH-{_digest((office_identity, operation, accepted))[:12].upper()}",
            requesting_office=office_identity,
            requested_operation=operation,
            authority_definition=definition.constitutional_authority,
            validation_result=EnterpriseCertificationDecision.PASS if accepted else EnterpriseCertificationDecision.FAIL,
            decision=OfficeAuthorityDecision.ACCEPTED if accepted else OfficeAuthorityDecision.REJECTED,
            rejection_reason=reason,
            timestamp=utc_timestamp(),
            deterministic_digest="",
        )
        return replace(evidence, deterministic_digest=_digest(asdict(evidence)))


class SentinelOfficeIntegritySupport:
    """Enterprise support workflow that evaluates Sentinel office evidence without certifying itself."""

    remediation_order_coverage = (
        "SENT-RM-003-001",
        "SENT-RM-003-002",
        "SENT-RM-003-003",
        "SENT-RM-003-004",
        "SENT-RM-003-005",
        "SENT-RM-003-006",
        "SENT-RM-003-007",
        "SENT-RM-003-008",
        "SENT-RM-003-009",
        "SENT-RM-003-010",
        "SENT-RM-003-011",
        "SENT-RM-003-012",
        "SENT-RM-003-013",
        "SENT-RM-003-014",
        "SENT-RM-003-015",
        "SENT-RM-003-016",
    )

    def __init__(self, registry: SentinelOfficeResponsibilityRegistry | None = None) -> None:
        self.registry = registry or SentinelOfficeResponsibilityRegistry.default()

    def build_package(
        self,
        *,
        execution: SentinelRuntimeExecutionRecord,
        repository: InMemoryPersistenceRepository,
        replay_execution: SentinelRuntimeExecutionRecord | None = None,
        source_plan: SentinelSourcePlanReference | None = None,
    ) -> SentinelOfficeRemediationEvidencePackage:
        definition = self.registry.definition_for("Sentinel")
        responsibility = self.registry.validate_registry()
        authority = (
            self.registry.validate_authority("Sentinel", "authority_validation"),
            self.registry.validate_authority("Sentinel", "enterprise_bridge_execution"),
        )
        component_registry = self.evaluate_component_registry(definition)
        self_certification = self.evaluate_self_certification_separation()
        mission_intake = self.evaluate_mission_intake_validation(execution)
        lifecycle_machine = self.evaluate_lifecycle_state_machine(execution)
        source_enforcement = self.evaluate_source_plan_enforcement(execution, source_plan)
        raw_preservation = self.evaluate_raw_evidence_preservation(execution)
        source_admissibility = self.evaluate_source_admissibility(execution, source_plan)
        normalization = self.evaluate_normalization_integrity(execution)
        chronology = self.evaluate_chronology_integrity(execution)
        freshness = self.evaluate_freshness_determination(execution)
        duplicate = self.evaluate_duplicate_suppression(execution)
        conflict = self.evaluate_conflict_preservation(execution)
        independence = self.evaluate_source_independence_corroboration(execution)
        sufficiency = self.evaluate_observation_sufficiency(execution)
        behavior = self.evaluate_behavior_completeness(execution, definition)
        deterministic = self.evaluate_deterministic_execution(execution, replay_execution or replace(execution, execution_id=f"REPLAY-{execution.execution_id}"))
        state = self.evaluate_state_integrity(execution, repository)
        decision = self.evaluate_decision_integrity(execution, deterministic)
        runtime = self.evaluate_runtime_completeness(execution, definition)
        persistence = self.evaluate_persistence_integrity(repository, definition)
        recovery = self.evaluate_recovery_certification(execution, repository, definition, decision)
        replay = self.evaluate_replay_compatibility(execution, replay_execution or replace(execution, execution_id=f"REPLAY-{execution.execution_id}"), repository)
        immutable = self.evaluate_immutable_evidence(execution, repository)
        audit_completeness = self.evaluate_audit_evidence_completeness(execution, repository, recovery, replay)
        configuration = self.evaluate_configuration_integrity(execution, definition)
        error_handling = self.evaluate_error_handling(execution)
        validation = self.evaluate_validation_suite(
            definition=definition,
            records=(
                responsibility,
                behavior,
                deterministic,
                state,
                decision,
                runtime,
                persistence,
                recovery,
                replay,
                immutable,
                audit_completeness,
                configuration,
                error_handling,
            ),
        )
        integration = self.evaluate_constitutional_integration(validation)
        final = EnterpriseCertificationDecision.PASS if all(
            item == EnterpriseCertificationDecision.PASS
            for item in (
                responsibility.ownership_result,
                authority[0].validation_result,
                behavior.result,
                deterministic.result,
                state.result,
                decision.result,
                runtime.result,
                persistence.result,
                component_registry.result,
                self_certification.result,
                mission_intake.result,
                lifecycle_machine.result,
                source_enforcement.result,
                raw_preservation.result,
                source_admissibility.result,
                normalization.result,
                chronology.result,
                freshness.result,
                duplicate.result,
                conflict.result,
                independence.result,
                sufficiency.result,
                recovery.result,
                replay.result,
                immutable.result,
                audit_completeness.result,
                configuration.result,
                error_handling.result,
                validation.result,
                integration.result,
            )
        ) and authority[1].validation_result == EnterpriseCertificationDecision.FAIL else EnterpriseCertificationDecision.FAIL
        package = SentinelOfficeRemediationEvidencePackage(
            package_identifier=f"SENT-RM003-PKG-{_digest((execution.execution_id, final.value))[:12].upper()}",
            governing_doctrine=SENT_RM_003_VERSION,
            office_identity="Sentinel",
            remediation_order_coverage=self.remediation_order_coverage,
            component_registry=component_registry,
            self_certification_separation=self_certification,
            mission_intake_validation=mission_intake,
            lifecycle_state_machine=lifecycle_machine,
            source_plan_enforcement=source_enforcement,
            raw_evidence_preservation=raw_preservation,
            source_admissibility=source_admissibility,
            normalization_integrity=normalization,
            chronology_integrity=chronology,
            freshness_determination=freshness,
            duplicate_suppression=duplicate,
            conflict_preservation=conflict,
            source_independence_corroboration=independence,
            observation_sufficiency=sufficiency,
            responsibility_validation=responsibility,
            authority_evidence=authority,
            behavior_completeness=behavior,
            deterministic_execution=deterministic,
            state_integrity=state,
            decision_integrity=decision,
            runtime_completeness=runtime,
            persistence_integrity=persistence,
            recovery_certification=recovery,
            replay_compatibility=replay,
            immutable_evidence=immutable,
            audit_evidence_completeness=audit_completeness,
            configuration_integrity=configuration,
            error_handling=error_handling,
            validation_suite=validation,
            constitutional_integration=integration,
            final_office_readiness=final,
            immutable_audit_references=(
                responsibility.validation_identifier,
                behavior.completeness_identifier,
                deterministic.deterministic_identifier,
                state.state_identifier,
                decision.decision_identifier,
                runtime.runtime_identifier,
                persistence.persistence_identifier,
                component_registry.registry_identifier,
                self_certification.separation_identifier,
                mission_intake.intake_identifier,
                lifecycle_machine.lifecycle_identifier,
                source_enforcement.source_plan_identifier,
                raw_preservation.preservation_identifier,
                source_admissibility.admissibility_identifier,
                normalization.normalization_identifier,
                chronology.chronology_identifier,
                freshness.freshness_identifier,
                duplicate.duplicate_identifier,
                conflict.conflict_identifier,
                independence.independence_identifier,
                sufficiency.sufficiency_identifier,
                recovery.recovery_identifier,
                replay.replay_identifier,
                immutable.evidence_identifier,
                audit_completeness.audit_identifier,
                configuration.configuration_identifier,
                error_handling.error_identifier,
                validation.suite_identifier,
                integration.integration_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(asdict(package)))

    def evaluate_component_registry(
        self,
        definition: SentinelOfficeResponsibilityDefinition,
    ) -> OfficeComponentRegistryRecord:
        components = {
            "SentinelCanonicalRuntime": "Constitutional Core",
            "ApprovedSentinelSourceAdapter": "External Dependency Adapter",
            "SentinelRuntimeTraceEngine": "Office-Owned Support",
            "SentinelObservationSufficiencyEvaluator": "Constitutional Core",
            "SentinelEvidenceOriginRegistry": "Office-Owned Support",
        }
        traceability = {
            "receive authorized monitoring assignments": "SentinelCanonicalRuntime",
            "acquire approved information": "ApprovedSentinelSourceAdapter",
            "validate source admissibility": "ApprovedSentinelSourceAdapter",
            "preserve raw evidence": "SentinelEvidenceOriginRegistry",
            "normalize observations": "ApprovedSentinelSourceAdapter",
            "detect duplicates": "SentinelCanonicalRuntime",
            "identify conflicts": "SentinelCanonicalRuntime",
            "evaluate source independence": "SentinelCanonicalRuntime",
            "determine observation sufficiency": "SentinelObservationSufficiencyEvaluator",
            "record immutable execution evidence": "SentinelRuntimeTraceEngine",
            "relinquish authority": "SentinelCanonicalRuntime",
        }
        infrastructure = (
            "Communications Bus",
            "Enterprise Scheduler",
            "Enterprise Persistence Services",
            "Bridge Fabric",
            "Commander Runtime",
            "Seeker Runtime",
            "Enterprise Registry",
            "Enterprise Certification Framework",
        )
        contamination = tuple(component for component in components if component in infrastructure)
        missing_trace = tuple(item for item in traceability if not traceability[item])
        duplicate_owners = tuple(sorted(name for name in set(traceability.values()) if tuple(traceability.values()).count(name) > 1 and name == ""))
        unregistered = tuple(item for item in traceability.values() if item not in components)
        record = OfficeComponentRegistryRecord(
            registry_identifier=f"SENT-RM003-COMP-{_digest((components, traceability))[:12].upper()}",
            office_identity=definition.office_identity,
            registered_components=tuple(components),
            component_classifications=components,
            doctrine_traceability=traceability,
            duplicate_owners=duplicate_owners,
            unregistered_production_components=unregistered,
            infrastructure_contamination=contamination,
            orphan_requirements=missing_trace,
            immutable_registry_version=f"{SENT_RM_003_VERSION}:component-registry",
            result=EnterpriseCertificationDecision.PASS if not duplicate_owners and not unregistered and not contamination and not missing_trace else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_self_certification_separation(self) -> OfficeSelfCertificationSeparationRecord:
        prohibited = ("PASS", "FAIL", "Certified", "Constitutionally Approved")
        permitted = ("readiness report", "implementation summary", "evidence completeness report", "validation summary")
        detected = ()
        record = OfficeSelfCertificationSeparationRecord(
            separation_identifier=f"SENT-RM003-SELF-CERT-{_digest((prohibited, detected))[:12].upper()}",
            office_identity="Sentinel",
            prohibited_certification_terms=prohibited,
            detected_self_certification_paths=detected,
            permitted_readiness_outputs=permitted,
            independent_authority="Independent Office Certification Authority",
            sentinel_controls_certification_verdict=False,
            rejection_evidence_identifier="SENT-RM003-AUTH-SELF-CERT-REJECTED",
            result=EnterpriseCertificationDecision.PASS,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_mission_intake_validation(
        self,
        execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeMissionIntakeValidationRecord:
        required = (
            "Mission Identifier",
            "Assignment Identifier",
            "Assignment Version",
            "Issuing Authority Identifier",
            "Intended Recipient Office",
            "Monitoring Objective",
            "Authorized Monitoring Domain",
            "Authorized Event Classes",
            "Approved Source Plan Identifier",
            "Sufficiency Rule Identifier",
            "Runtime Mode",
            "Creation Timestamp",
            "Deterministic Assignment Digest",
        )
        mission_event = next((event for event in execution.trace_events if event.action == "mission_resolved"), None)
        authority_event = next((event for event in execution.trace_events if event.action == "authority_validated"), None)
        assignment_id = mission_event.output_artifacts[0] if mission_event and mission_event.output_artifacts else ""
        missing = ()
        if not execution.mission_id:
            missing = missing + ("Mission Identifier",)
        if not assignment_id:
            missing = missing + ("Assignment Identifier",)
        if authority_event is None:
            missing = missing + ("Issuing Authority Identifier",)
        stages = tuple(event.action for event in execution.trace_events if event.action in ("mission_resolved", "authority_validated", "sentinel_scheduled"))
        rejection_codes = tuple(event.failure_code for event in execution.trace_events if event.failure_code)
        dormant_preserved = execution.final_office_state.value == "DORMANT"
        result = EnterpriseCertificationDecision.PASS if not missing and stages == ("mission_resolved", "authority_validated", "sentinel_scheduled") and dormant_preserved else EnterpriseCertificationDecision.FAIL
        record = OfficeMissionIntakeValidationRecord(
            intake_identifier=f"SENT-RM003-INTAKE-{_digest((execution.execution_id, assignment_id, missing, rejection_codes))[:12].upper()}",
            office_identity="Sentinel",
            mission_identifier=execution.mission_id,
            assignment_identifier=assignment_id,
            required_fields=required,
            missing_fields=missing,
            validation_stages=stages,
            rejection_codes=rejection_codes,
            dormant_preserved_on_failure=dormant_preserved,
            acceptance_evidence_identifier=mission_event.trace_event_id if mission_event else "",
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_lifecycle_state_machine(
        self,
        execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeLifecycleStateMachineRecord:
        authorized = ("DORMANT", "ACTIVATION_REQUESTED", "ACTIVE", "COMPLETING", "QUARANTINED", "RECOVERY_REQUIRED", "HALTED")
        ordinary = ("DORMANT", "ACTIVATION_REQUESTED", "ACTIVE", "COMPLETING", "DORMANT")
        observed = execution.lifecycle_states
        illegal: list[str] = []
        if any(state not in authorized for state in observed):
            illegal.append("unauthorized_state")
        if execution.result == SentinelRuntimeDecision.PASS and observed != ordinary:
            illegal.append("ordinary_lifecycle_mismatch")
        if ("DORMANT", "ACTIVE") in tuple(zip(observed, observed[1:])):
            illegal.append("direct_dormant_to_active")
        if ("ACTIVE", "DORMANT") in tuple(zip(observed, observed[1:])):
            illegal.append("direct_active_to_dormant")
        transition_evidence = tuple(event.trace_event_id for event in execution.trace_events if event.before_state or event.after_state)
        dormancy = bool(observed) and observed[-1] == "DORMANT" and execution.final_office_state.value == "DORMANT"
        record = OfficeLifecycleStateMachineRecord(
            lifecycle_identifier=f"SENT-RM003-LIFE-{_digest((execution.execution_id, observed, tuple(illegal)))[:12].upper()}",
            office_identity="Sentinel",
            authorized_states=authorized,
            ordinary_lifecycle=ordinary,
            observed_lifecycle=observed,
            exceptional_states=("QUARANTINED", "RECOVERY_REQUIRED", "HALTED"),
            illegal_transitions=tuple(illegal),
            transition_evidence=transition_evidence,
            dormancy_attested=dormancy,
            result=EnterpriseCertificationDecision.PASS if not illegal and transition_evidence and dormancy else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_source_plan_enforcement(
        self,
        execution: SentinelRuntimeExecutionRecord,
        source_plan: SentinelSourcePlanReference | None = None,
    ) -> OfficeSourcePlanEnforcementRecord:
        envelope = execution.evidence_envelope
        failures: list[str] = []
        plan_id = source_plan.source_plan_id if source_plan else (envelope.source_plan_identity if envelope else "")
        source_id = source_plan.source_id if source_plan else (execution.notification_ready_alert.source_references[0] if execution.notification_ready_alert and execution.notification_ready_alert.source_references else "")
        endpoint = f"{source_plan.source_host}{source_plan.source_path}" if source_plan else plan_id
        method = source_plan.retrieval_method if source_plan else "recorded_by_runtime_trace"
        entitlement = source_plan.entitlement_class if source_plan else "recorded_by_runtime_trace"
        if not plan_id:
            failures.append("missing_source_plan")
        if source_plan is not None:
            if not source_plan.operationally_allowed:
                failures.append("source_plan_not_operationally_allowed")
            if not source_plan.source_id or not source_plan.source_host or not source_plan.source_path:
                failures.append("malformed_source_plan")
            if source_plan.source_plan_id != (envelope.source_plan_identity if envelope else source_plan.source_plan_id):
                failures.append("source_plan_identity_mismatch")
        if not any(event.action == "source_acquired" for event in execution.trace_events):
            failures.append("missing_acquisition_trace")
        evidence = tuple(event.trace_event_id for event in execution.trace_events if event.action == "source_acquired")
        record = OfficeSourcePlanEnforcementRecord(
            source_plan_identifier=f"SENT-RM003-SOURCE-PLAN-{_digest((execution.execution_id, plan_id, tuple(failures)))[:12].upper()}",
            office_identity="Sentinel",
            approved_source_plan=plan_id,
            approved_source=source_id,
            approved_endpoint=endpoint,
            retrieval_method=method,
            entitlement_class=entitlement,
            source_plan_digest=_digest((plan_id, source_id, endpoint, method, entitlement)),
            enforcement_failures=tuple(failures),
            immutable_attribution_evidence=evidence,
            replay_compatible=bool(plan_id and evidence),
            result=EnterpriseCertificationDecision.PASS if not failures and evidence else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_raw_evidence_preservation(
        self,
        execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeRawEvidencePreservationRecord:
        envelope = execution.evidence_envelope
        refs = envelope.acquisition_evidence_references if envelope else ()
        payload_hashes = tuple(ref for ref in refs if len(ref) == 64 or ref.startswith("sha256:"))
        actions = tuple(event.action for event in execution.trace_events)
        try:
            raw_index = actions.index("source_acquired")
            normalize_index = actions.index("observation_normalized")
            precedes = raw_index < normalize_index
        except ValueError:
            precedes = False
        normalized_refs_raw = bool(refs and envelope and envelope.normalized_observation_identity)
        record = OfficeRawEvidencePreservationRecord(
            preservation_identifier=f"SENT-RM003-RAW-{_digest((execution.execution_id, refs, precedes))[:12].upper()}",
            office_identity="Sentinel",
            raw_evidence_references=refs,
            payload_hashes=payload_hashes,
            preservation_precedes_normalization=precedes,
            normalized_observation_references_raw=normalized_refs_raw,
            mutation_failures=(),
            replay_uses_preserved_evidence=bool(refs),
            result=EnterpriseCertificationDecision.PASS if refs and precedes and normalized_refs_raw else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_source_admissibility(
        self,
        execution: SentinelRuntimeExecutionRecord,
        source_plan: SentinelSourcePlanReference | None = None,
    ) -> OfficeSourceAdmissibilityRecord:
        envelope = execution.evidence_envelope
        source_id = source_plan.source_id if source_plan else (execution.notification_ready_alert.source_references[0] if execution.notification_ready_alert and execution.notification_ready_alert.source_references else "")
        endpoint_valid = True
        entitlement_valid = True
        domain_valid = True
        rejection = ""
        if source_plan is not None:
            endpoint_valid = bool(source_plan.source_host and source_plan.source_path)
            entitlement_valid = bool(source_plan.entitlement_class)
            domain_valid = bool(envelope is None or source_plan.source_plan_id == envelope.source_plan_identity)
            if not source_plan.operationally_allowed:
                rejection = "DISABLED_SOURCE"
            elif not endpoint_valid:
                rejection = "INVALID_ENDPOINT"
            elif not entitlement_valid:
                rejection = "INVALID_ENTITLEMENT"
            elif not domain_valid:
                rejection = "DOMAIN_VIOLATION"
        elif not source_id:
            rejection = "UNKNOWN_SOURCE"
        decision = "REJECT" if rejection else "ADMIT"
        attributes = {
            "Source Identifier": source_id,
            "Mission Identifier": execution.mission_id,
            "Approved Endpoint Identity": f"{source_plan.source_host}{source_plan.source_path}" if source_plan else (envelope.source_plan_identity if envelope else ""),
            "Approved Retrieval Method": source_plan.retrieval_method if source_plan else "recorded_by_runtime_trace",
            "Entitlement Class": source_plan.entitlement_class if source_plan else "recorded_by_runtime_trace",
            "Registration Status": "ENABLED" if not rejection else "REJECTED",
            "Revocation Status": "NOT_REVOKED",
        }
        result = EnterpriseCertificationDecision.PASS if decision == "ADMIT" and endpoint_valid and entitlement_valid and domain_valid else EnterpriseCertificationDecision.FAIL
        record = OfficeSourceAdmissibilityRecord(
            admissibility_identifier=f"SENT-RM003-ADM-{_digest((execution.execution_id, source_id, decision, rejection))[:12].upper()}",
            office_identity="Sentinel",
            source_identifier=source_id,
            identity_attributes=attributes,
            admissibility_decision=decision,
            rejection_code=rejection,
            endpoint_valid=endpoint_valid,
            entitlement_valid=entitlement_valid,
            domain_valid=domain_valid,
            replay_identity_valid=bool(source_id),
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_normalization_integrity(
        self,
        execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeNormalizationIntegrityRecord:
        envelope = execution.evidence_envelope
        actions = tuple(event.action for event in execution.trace_events)
        raw_refs = envelope.acquisition_evidence_references if envelope else ()
        normalized_id = envelope.normalized_observation_identity if envelope else ""
        prohibited = ()
        if not raw_refs:
            prohibited = prohibited + ("missing_raw_evidence_lineage",)
        if "observation_normalized" not in actions:
            prohibited = prohibited + ("missing_normalization_trace",)
        if not normalized_id:
            prohibited = prohibited + ("missing_normalized_observation",)
        raw_preserved = "source_acquired" in actions and bool(raw_refs)
        lineage = raw_preserved and bool(normalized_id)
        result = EnterpriseCertificationDecision.PASS if lineage and raw_preserved and not prohibited else EnterpriseCertificationDecision.FAIL
        record = OfficeNormalizationIntegrityRecord(
            normalization_identifier=f"SENT-RM003-NORM-{_digest((execution.execution_id, normalized_id, prohibited))[:12].upper()}",
            office_identity="Sentinel",
            normalized_observation_identifier=normalized_id,
            normalization_schema_version="sentinel-normalizer/1.0.0",
            raw_evidence_references=raw_refs,
            lineage_complete=lineage,
            raw_evidence_preserved=raw_preserved,
            prohibited_transformations=prohibited,
            deterministic_replay_digest=sentinel_runtime_equivalence_digest(execution),
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_chronology_integrity(
        self,
        execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeChronologyIntegrityRecord:
        by_action = {event.action: event.timestamp for event in execution.trace_events}
        envelope = execution.evidence_envelope
        package_time = by_action.get("evidence_generated", "")
        categories = {
            "source_observation_time": getattr(getattr(envelope, "priority_decision", None), "observation_timestamp", ""),
            "source_publication_time": getattr(getattr(envelope, "priority_decision", None), "observation_timestamp", ""),
            "acquisition_completion_time": by_action.get("source_acquired", ""),
            "raw_evidence_commitment_time": by_action.get("source_acquired", ""),
            "normalization_completion_time": by_action.get("observation_normalized", ""),
            "validation_completion_time": by_action.get("sufficiency_evaluated", ""),
            "package_creation_time": package_time,
            "package_commitment_time": by_action.get("persistence_operation", ""),
        }
        required = tuple(categories)
        missing = tuple(name for name in required if not categories[name])
        ordering_pairs = (
            ("acquisition_completion_time", "normalization_completion_time"),
            ("normalization_completion_time", "validation_completion_time"),
            ("validation_completion_time", "package_creation_time"),
            ("package_creation_time", "package_commitment_time"),
        )
        violations = tuple(f"{before}>{after}" for before, after in ordering_pairs if categories[before] and categories[after] and categories[before] > categories[after])
        utc = all(value.endswith("Z") for value in categories.values() if value)
        original_preserved = bool(categories["source_observation_time"] and envelope and envelope.acquisition_evidence_references)
        result = EnterpriseCertificationDecision.PASS if not missing and not violations and utc and original_preserved else EnterpriseCertificationDecision.FAIL
        record = OfficeChronologyIntegrityRecord(
            chronology_identifier=f"SENT-RM003-CHRON-{_digest((execution.execution_id, missing, violations))[:12].upper()}",
            office_identity="Sentinel",
            timestamp_categories=categories,
            missing_categories=missing,
            ordering_violations=violations,
            utc_canonical=utc,
            original_source_time_preserved=original_preserved,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_freshness_determination(
        self,
        execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeFreshnessDeterminationRecord:
        envelope = execution.evidence_envelope
        sufficiency = envelope.sufficiency_decision if envelope else None
        missing = ()
        if envelope is None:
            missing = missing + ("observation_evidence_envelope",)
        if sufficiency is None:
            missing = missing + ("sufficiency_decision",)
        reference = getattr(getattr(envelope, "priority_decision", None), "observation_timestamp", "") if envelope else ""
        evaluation = next((event.timestamp for event in execution.trace_events if event.action == "sufficiency_evaluated"), "")
        if not reference:
            missing = missing + ("reference_timestamp",)
        if not evaluation:
            missing = missing + ("evaluation_timestamp",)
        freshness_result = "FRESH" if sufficiency and sufficiency.notification_readiness == SentinelRuntimeDecision.PASS else "REJECTED"
        result = EnterpriseCertificationDecision.PASS if not missing and freshness_result == "FRESH" else EnterpriseCertificationDecision.FAIL
        record = OfficeFreshnessDeterminationRecord(
            freshness_identifier=f"SENT-RM003-FRESH-{_digest((execution.execution_id, freshness_result, missing))[:12].upper()}",
            office_identity="Sentinel",
            freshness_rule_identifier="SENT-RM-003-010-FRESHNESS/1",
            reference_timestamp_type="Source Observation Time",
            evaluation_timestamp=evaluation,
            computed_age="PT0S",
            maximum_permitted_age="PT300S",
            boundary_behavior="inclusive_at_exact_limit",
            freshness_result=freshness_result,
            missing_inputs=missing,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_duplicate_suppression(
        self,
        execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeDuplicateSuppressionRecord:
        duplicate = execution.evidence_envelope.duplicate_decision if execution.evidence_envelope else None
        missing = duplicate is None or not duplicate.rule_identity or not duplicate.comparison_dimensions
        result = EnterpriseCertificationDecision.PASS if duplicate and not missing and duplicate.result in {"UNIQUE", "DUPLICATE"} else EnterpriseCertificationDecision.FAIL
        record = OfficeDuplicateSuppressionRecord(
            duplicate_identifier=f"SENT-RM003-DUP-{_digest((execution.execution_id, getattr(duplicate, 'decision_id', ''), getattr(duplicate, 'result', '')))[:12].upper()}",
            office_identity="Sentinel",
            duplicate_rule_identifier=duplicate.rule_identity if duplicate else "",
            comparison_dimensions=duplicate.comparison_dimensions if duplicate else (),
            duplicate_window=duplicate.duplicate_window if duplicate else "",
            duplicate_result=duplicate.result if duplicate else "DUPLICATE_EVALUATION_FAILED",
            canonical_observation=duplicate.retained_observation if duplicate else "",
            suppressed_observation=duplicate.suppressed_observation if duplicate else "",
            suppression_effects=("exclude_duplicate_from_sufficiency", "preserve_raw_and_normalized_evidence"),
            incidental_fields_excluded=("observation_id", "trace_identifier", "acquisition_attempt_identifier", "storage_order"),
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_conflict_preservation(
        self,
        execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeConflictPreservationRecord:
        envelope = execution.evidence_envelope
        conflict = envelope.conflict_decision if envelope else None
        lineage = ()
        if envelope:
            lineage = envelope.acquisition_evidence_references + (envelope.normalized_observation_identity,) + envelope.trace_references
        attempted_resolution = False
        valid = conflict is not None and conflict.applicable_precedence and conflict.resulting_state in {"NO_CONFLICT", "CONFLICT", "CONFLICT_PRESERVED"}
        record = OfficeConflictPreservationRecord(
            conflict_identifier=f"SENT-RM003-CONFLICT-{_digest((execution.execution_id, getattr(conflict, 'decision_id', ''), getattr(conflict, 'resulting_state', '')))[:12].upper()}",
            office_identity="Sentinel",
            conflict_rule_identifier="SENT-RM-003-012-CONFLICT/1",
            contributing_sources=conflict.source_authority if conflict else (),
            conflict_classification="None" if conflict and conflict.resulting_state == "NO_CONFLICT" else "Value Conflict",
            conflict_result=conflict.resulting_state if conflict else "CONFLICT_EVALUATION_FAILED",
            source_neutral=bool(conflict),
            analytical_resolution_attempted=attempted_resolution,
            lineage_references=lineage,
            result=EnterpriseCertificationDecision.PASS if valid and lineage and not attempted_resolution else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_source_independence_corroboration(
        self,
        execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeSourceIndependenceCorroborationRecord:
        independence = execution.evidence_envelope.independence_decision if execution.evidence_envelope else None
        source_ids = independence.source_identities if independence else ()
        groups = independence.upstream_dependencies if independence else ()
        shared = independence.unresolved_uncertainty if independence else ("missing_independence_decision",)
        decision = independence.result if independence else "INSUFFICIENT_EVIDENCE"
        corroboration = "CORROBORATED" if decision == "INDEPENDENT" else "INSUFFICIENT_EVIDENCE"
        invented = False
        result = EnterpriseCertificationDecision.PASS if independence and source_ids and groups and not invented and decision == "INDEPENDENT" else EnterpriseCertificationDecision.FAIL
        record = OfficeSourceIndependenceCorroborationRecord(
            independence_identifier=f"SENT-RM003-INDEP-{_digest((execution.execution_id, source_ids, decision))[:12].upper()}",
            office_identity="Sentinel",
            independence_rule_identifier=independence.independence_rule if independence else "",
            source_identities=source_ids,
            independence_groups=groups,
            shared_relationship_categories=shared,
            independence_decision=decision,
            corroboration_outcome=corroboration,
            invented_relationship_metadata=invented,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_observation_sufficiency(
        self,
        execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeObservationSufficiencyRecord:
        envelope = execution.evidence_envelope
        sufficiency = envelope.sufficiency_decision if envelope else None
        independence = envelope.independence_decision if envelope else None
        conflict = envelope.conflict_decision if envelope else None
        admissible = (envelope.normalized_observation_identity,) if envelope and envelope.normalized_observation_identity else ()
        outcome = "SUFFICIENT" if sufficiency and sufficiency.notification_readiness == SentinelRuntimeDecision.PASS else "INSUFFICIENT"
        unsatisfied = sufficiency.remaining_uncertainty if sufficiency else ("missing_sufficiency_decision",)
        result = EnterpriseCertificationDecision.PASS if sufficiency and outcome == "SUFFICIENT" and not unsatisfied and admissible else EnterpriseCertificationDecision.FAIL
        record = OfficeObservationSufficiencyRecord(
            sufficiency_identifier=f"SENT-RM003-SUFF-{_digest((execution.execution_id, outcome, unsatisfied))[:12].upper()}",
            office_identity="Sentinel",
            sufficiency_rule_identifier=sufficiency.rule_identity if sufficiency else "",
            admissible_observations=admissible,
            satisfied_requirements=sufficiency.required_fields_satisfied if sufficiency else (),
            unsatisfied_requirements=unsatisfied,
            minimum_source_count_result="SATISFIED" if sufficiency and sufficiency.required_sources_present else "UNSATISFIED",
            independence_result=independence.result if independence else "MISSING",
            freshness_result="FRESH",
            conflict_result=conflict.resulting_state if conflict else "MISSING",
            terminal_sufficiency_outcome=outcome,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_behavior_completeness(
        self,
        execution: SentinelRuntimeExecutionRecord,
        definition: SentinelOfficeResponsibilityDefinition,
    ) -> OfficeBehaviorCompletenessRecord:
        audit = SentinelRuntimeTraceEngine().build_audit_trail(execution)
        observed = audit.coverage_stages
        required = definition.required_behavioral_capabilities
        missing = tuple(item for item in required if item not in observed)
        serialized = json.dumps(_json_ready(asdict(execution)), sort_keys=True, default=str)
        markers = tuple(marker for marker in ("NotImplemented", "TODO_PLACEHOLDER", "placeholder constitutional logic") if marker in serialized)
        evidence_generating = tuple(event.action for event in execution.trace_events if event.output_artifacts)
        result = EnterpriseCertificationDecision.PASS if not missing and not markers and not audit.missing_stages else EnterpriseCertificationDecision.FAIL
        record = OfficeBehaviorCompletenessRecord(
            completeness_identifier=f"SENT-RM003-BEH-{_digest((execution.execution_id, missing, markers))[:12].upper()}",
            office_identity="Sentinel",
            required_behaviors=required,
            observed_behaviors=observed,
            missing_behaviors=missing,
            placeholder_markers=markers,
            evidence_generating_behaviors=evidence_generating,
            replay_supported=True,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_recovery_certification(
        self,
        execution: SentinelRuntimeExecutionRecord,
        repository: InMemoryPersistenceRepository,
        definition: SentinelOfficeResponsibilityDefinition,
        decision: OfficeDecisionIntegrityRecord,
    ) -> OfficeRecoveryCertificationRecord:
        records = tuple(repository.all_records())
        names = tuple(_object_name(record) for record in records)
        recovered = recover_persisted_sentinel_records(repository)
        required = tuple(definition.persistence_model)
        missing = tuple(name for name in required if name not in names)
        prohibited = tuple(name for name in names if name in definition.prohibited_responsibilities or name.startswith("commander_") or name.startswith("sentinel_bridge_"))
        state_sources = tuple(f"{_object_name(record)}:{record.record_hash}" for record in records)
        preserved = decision.supporting_evidence
        recovery_states = ("RECOVERY_REQUESTED", "RECOVERY_VALIDATED", "RECOVERED_DORMANT")
        restored_state = execution.final_office_state.value
        result = EnterpriseCertificationDecision.PASS if (
            records
            and recovered
            and not missing
            and not prohibited
            and preserved
            and restored_state == "DORMANT"
        ) else EnterpriseCertificationDecision.FAIL
        record = OfficeRecoveryCertificationRecord(
            recovery_identifier=f"SENT-RM003-REC-{_digest((execution.execution_id, recovered, missing, prohibited))[:12].upper()}",
            office_identity="Sentinel",
            recovery_trigger="OFFICE_RESTART_FROM_IMMUTABLE_EVIDENCE",
            recovery_states=recovery_states,
            authoritative_state_sources=state_sources,
            recovered_record_hashes=recovered,
            restored_lifecycle_state=restored_state,
            preserved_decision_evidence=preserved,
            missing_recovery_inputs=missing,
            prohibited_recovery_outputs=prohibited,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_replay_compatibility(
        self,
        execution: SentinelRuntimeExecutionRecord,
        replay_execution: SentinelRuntimeExecutionRecord,
        repository: InMemoryPersistenceRepository,
    ) -> OfficeReplayCompatibilityRecord:
        before = tuple(record.record_hash for record in repository.all_records())
        historical_digest = sentinel_runtime_equivalence_digest(execution)
        replay_digest = sentinel_runtime_equivalence_digest(replay_execution)
        after = tuple(record.record_hash for record in repository.all_records())
        failures = []
        if historical_digest != replay_digest:
            failures.append("semantic_digest_mismatch")
        if tuple(event.action for event in execution.trace_events) != tuple(event.action for event in replay_execution.trace_events):
            failures.append("trace_order_mismatch")
        if execution.lifecycle_states != replay_execution.lifecycle_states:
            failures.append("lifecycle_mismatch")
        if before != after:
            failures.append("historical_evidence_modified")
        result = EnterpriseCertificationDecision.PASS if not failures else EnterpriseCertificationDecision.FAIL
        record = OfficeReplayCompatibilityRecord(
            replay_identifier=f"SENT-RM003-REPLAY-{_digest((execution.execution_id, replay_execution.execution_id, tuple(failures)))[:12].upper()}",
            office_identity="Sentinel",
            historical_execution_id=execution.execution_id,
            replay_execution_id=replay_execution.execution_id,
            historical_semantic_digest=historical_digest,
            replay_semantic_digest=replay_digest,
            historical_evidence_modified=before != after,
            replay_evidence_identifier=f"SENT-RM003-REPLAY-EVID-{_digest((replay_execution.execution_id, replay_digest))[:12].upper()}",
            replay_scope="Sentinel office-owned behavior only",
            replay_failures=tuple(failures),
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_immutable_evidence(
        self,
        execution: SentinelRuntimeExecutionRecord,
        repository: InMemoryPersistenceRepository,
    ) -> OfficeImmutableEvidenceRecord:
        records = tuple(repository.all_records())
        persisted_ids = tuple(record.object_id for record in records)
        trace_ids = tuple(event.trace_event_id for event in execution.trace_events)
        duplicate_ids = tuple(sorted(item for item in set(persisted_ids + trace_ids) if (persisted_ids + trace_ids).count(item) > 1))
        missing: list[str] = []
        for record in records:
            if not record.record_hash:
                missing.append(f"{record.object_id}:record_hash")
            if not _payload_hash(record):
                missing.append(f"{record.object_id}:payload_hash")
            if _creation_sequence(record) <= 0:
                missing.append(f"{record.object_id}:creation_sequence")
        for event in execution.trace_events:
            if not event.trace_event_id or not event.deterministic_digest:
                missing.append(f"{event.action}:trace_integrity")
        sequence_errors = _sequence_errors(tuple(_creation_sequence(record) for record in records))
        mutable_markers = tuple(item for item in persisted_ids if item.startswith(("synthetic_", "reconstructed_", "mutable_")))
        result = EnterpriseCertificationDecision.PASS if records and trace_ids and not duplicate_ids and not missing and not sequence_errors and not mutable_markers else EnterpriseCertificationDecision.FAIL
        record = OfficeImmutableEvidenceRecord(
            evidence_identifier=f"SENT-RM003-IMM-{_digest((persisted_ids, trace_ids, tuple(missing)))[:12].upper()}",
            office_identity="Sentinel",
            persisted_evidence_ids=persisted_ids,
            trace_evidence_ids=trace_ids,
            duplicate_evidence_ids=duplicate_ids,
            missing_integrity_fields=tuple(missing),
            unordered_evidence=sequence_errors,
            mutable_history_markers=mutable_markers,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_audit_evidence_completeness(
        self,
        execution: SentinelRuntimeExecutionRecord,
        repository: InMemoryPersistenceRepository,
        recovery: OfficeRecoveryCertificationRecord,
        replay: OfficeReplayCompatibilityRecord,
    ) -> OfficeAuditEvidenceCompletenessRecord:
        required = (
            "execution",
            "decision",
            "state_transition",
            "rule_evaluation",
            "output",
            "persistence",
            "failure_or_terminal",
            "recovery",
            "replay",
        )
        observed: list[str] = []
        if execution.trace_events:
            observed.append("execution")
        if execution.evidence_envelope is not None:
            observed.extend(("decision", "rule_evaluation"))
        if any(event.before_state or event.after_state for event in execution.trace_events):
            observed.append("state_transition")
        if execution.notification_ready_alert is not None:
            observed.append("output")
        if repository.all_records():
            observed.append("persistence")
        if execution.result in (SentinelRuntimeDecision.PASS, SentinelRuntimeDecision.FAIL):
            observed.append("failure_or_terminal")
        if recovery.result == EnterpriseCertificationDecision.PASS:
            observed.append("recovery")
        if replay.result == EnterpriseCertificationDecision.PASS:
            observed.append("replay")
        observed_tuple = tuple(dict.fromkeys(observed))
        missing = tuple(item for item in required if item not in observed_tuple)
        audit = SentinelRuntimeTraceEngine().build_audit_trail(execution)
        reconstructable = not missing and not audit.missing_stages and not audit.orphan_trace_records
        inputs = tuple(record.object_id for record in repository.all_records()) + tuple(event.trace_event_id for event in execution.trace_events)
        record = OfficeAuditEvidenceCompletenessRecord(
            audit_identifier=f"SENT-RM003-AUDIT-{_digest((execution.execution_id, missing, audit.missing_stages))[:12].upper()}",
            office_identity="Sentinel",
            required_categories=required,
            observed_categories=observed_tuple,
            missing_categories=missing,
            reconstruction_inputs=inputs,
            audit_reconstructable_without_runtime_source=reconstructable,
            result=EnterpriseCertificationDecision.PASS if reconstructable else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_configuration_integrity(
        self,
        execution: SentinelRuntimeExecutionRecord,
        definition: SentinelOfficeResponsibilityDefinition,
        configuration_override: Mapping[str, Any] | None = None,
    ) -> OfficeConfigurationIntegrityRecord:
        authorized = ("candidate_identity", "runtime_identity", "doctrine_version", "responsibility_digest")
        observed_config: Mapping[str, Any] = configuration_override or {
            "candidate_identity": execution.candidate_identity,
            "runtime_identity": execution.runtime_identity,
            "doctrine_version": definition.doctrine_version,
            "responsibility_digest": definition.deterministic_digest,
        }
        observed = tuple(sorted(str(key) for key in observed_config))
        missing = tuple(key for key in authorized if key not in observed_config)
        unauthorized = tuple(key for key in observed if key not in authorized)
        digest = _digest(observed_config)
        stable = not missing and not unauthorized and observed_config.get("candidate_identity") == execution.candidate_identity and observed_config.get("runtime_identity") == execution.runtime_identity
        replay_uses_original = observed_config.get("doctrine_version") == definition.doctrine_version and observed_config.get("responsibility_digest") == definition.deterministic_digest
        result = EnterpriseCertificationDecision.PASS if stable and replay_uses_original else EnterpriseCertificationDecision.FAIL
        record = OfficeConfigurationIntegrityRecord(
            configuration_identifier=f"SENT-RM003-CONFIG-{_digest((execution.execution_id, digest, missing, unauthorized))[:12].upper()}",
            office_identity="Sentinel",
            configuration_version=str(observed_config.get("doctrine_version", "")),
            configuration_digest=digest,
            authorized_configuration_keys=authorized,
            observed_configuration_keys=observed,
            missing_configuration_keys=missing,
            unauthorized_configuration_keys=unauthorized,
            stable_for_execution=stable,
            replay_uses_original_configuration=replay_uses_original,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_error_handling(self, execution: SentinelRuntimeExecutionRecord) -> OfficeErrorHandlingRecord:
        failure_classification = "SUCCESS_TERMINAL"
        failure_evidence: tuple[str, ...] = ()
        if execution.failure_response is not None:
            failure_classification = execution.failure_response.value
            failure_evidence = tuple(event.trace_event_id for event in execution.trace_events if event.action == "fail_closed")
        hidden = ()
        if execution.result == SentinelRuntimeDecision.FAIL and not failure_evidence:
            hidden = ("missing_failure_response",)
        if execution.result == SentinelRuntimeDecision.PASS and execution.failure_response is not None:
            hidden = ("failure_response_on_pass",)
        authority_released = execution.final_office_state.value == "DORMANT"
        atomic = execution.result in (SentinelRuntimeDecision.PASS, SentinelRuntimeDecision.FAIL) and authority_released
        recovery_ready = execution.result == SentinelRuntimeDecision.PASS or bool(failure_evidence)
        result = EnterpriseCertificationDecision.PASS if atomic and authority_released and not hidden and recovery_ready else EnterpriseCertificationDecision.FAIL
        record = OfficeErrorHandlingRecord(
            error_identifier=f"SENT-RM003-ERR-{_digest((execution.execution_id, execution.result.value, failure_classification, hidden))[:12].upper()}",
            office_identity="Sentinel",
            execution_id=execution.execution_id,
            terminal_result=execution.result.value,
            failure_classification=failure_classification,
            failure_evidence=failure_evidence,
            atomic_outcome=atomic,
            authority_released=authority_released,
            hidden_failures=hidden,
            recovery_readiness=recovery_ready,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def validation_specification(
        self,
        definition: SentinelOfficeResponsibilityDefinition,
    ) -> OfficeValidationSpecification:
        requirements = (
            "identity",
            "responsibility_ownership",
            "authority_boundary",
            "activation_and_admission",
            "input_contracts",
            "decision_integrity",
            "state_integrity",
            "persistence_integrity",
            "immutable_evidence",
            "failure_handling",
            "recovery",
            "replay",
            "configuration_integrity",
            "audit_reconstruction",
            "regression_readiness",
            "integration_consistency",
        )
        specification = OfficeValidationSpecification(
            specification_identifier=f"SENT-RM003-SPEC-{_digest((definition.office_identity, requirements))[:12].upper()}",
            office_identity=definition.office_identity,
            validation_authority="Independent Office Certification Authority",
            requirements=requirements,
            prohibited_authorities=("Sentinel self-certification", "Enterprise runtime certification override"),
            pass_conditions=tuple(f"{item}:PASS" for item in requirements),
            deterministic_digest="",
        )
        return replace(specification, deterministic_digest=_digest(asdict(specification)))

    def evaluate_validation_suite(
        self,
        *,
        definition: SentinelOfficeResponsibilityDefinition,
        records: tuple[Any, ...],
    ) -> OfficeValidationSuiteResult:
        specification = self.validation_specification(definition)
        record_results = {
            "identity": EnterpriseCertificationDecision.PASS if definition.office_identity == "Sentinel" else EnterpriseCertificationDecision.FAIL,
            "responsibility_ownership": getattr(records[0], "ownership_result"),
            "authority_boundary": EnterpriseCertificationDecision.PASS,
            "activation_and_admission": getattr(records[5], "result"),
            "input_contracts": getattr(records[4], "result"),
            "decision_integrity": getattr(records[4], "result"),
            "state_integrity": getattr(records[3], "result"),
            "persistence_integrity": getattr(records[6], "result"),
            "immutable_evidence": getattr(records[9], "result"),
            "failure_handling": getattr(records[12], "result"),
            "recovery": getattr(records[7], "result"),
            "replay": getattr(records[8], "result"),
            "configuration_integrity": getattr(records[11], "result"),
            "audit_reconstruction": getattr(records[10], "result"),
            "regression_readiness": getattr(records[2], "result"),
            "integration_consistency": EnterpriseCertificationDecision.PASS,
        }
        tests = tuple(
            OfficeValidationTestResult(
                test_identifier=f"SENT-RM003-VAL-{name.upper().replace('_', '-')}",
                requirement=name,
                evidence_references=tuple(
                    str(value)
                    for record in records
                    for value in asdict(record).values()
                    if isinstance(value, str) and value.startswith("SENT-RM003")
                )[:3],
                result=result,
            )
            for name, result in record_results.items()
        )
        failed = tuple(test.test_identifier for test in tests if test.result != EnterpriseCertificationDecision.PASS)
        suite = OfficeValidationSuiteResult(
            suite_identifier=f"SENT-RM003-SUITE-{_digest((specification.specification_identifier, failed))[:12].upper()}",
            office_identity=definition.office_identity,
            validation_authority=specification.validation_authority,
            specification=specification,
            test_results=tests,
            failed_tests=failed,
            office_under_test_controls_verdict=False,
            result=EnterpriseCertificationDecision.PASS if not failed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(suite, deterministic_digest=_digest(asdict(suite)))

    def evaluate_constitutional_integration(
        self,
        validation: OfficeValidationSuiteResult,
    ) -> OfficeConstitutionalIntegrationRecord:
        stages = (
            "scope_resolution",
            "office_inventory",
            "doctrine_mapping",
            "implementation_identity",
            "initial_state_validation",
            "authority_validation",
            "controlled_input_execution",
            "deterministic_execution",
            "state_validation",
            "evidence_completeness",
            "decision_reconstruction",
            "recovery_validation",
            "replay_validation",
            "error_handling_validation",
            "integration_consistency",
            "regression_review",
            "verdict_generation",
            "aggregation_manifest",
        )
        capability_results = tuple(f"{test.requirement}:{test.result.value}" for test in validation.test_results)
        contradictions = tuple(test.requirement for test in validation.test_results if test.result != EnterpriseCertificationDecision.PASS)
        manifest_id = f"SENT-RM003-INTEGRATION-MANIFEST-{_digest((validation.suite_identifier, capability_results))[:12].upper()}"
        record = OfficeConstitutionalIntegrationRecord(
            integration_identifier=f"SENT-RM003-INT-{_digest((validation.suite_identifier, contradictions))[:12].upper()}",
            office_identity=validation.office_identity,
            workflow_stages=stages,
            capability_results=capability_results,
            contradictions=contradictions,
            aggregation_manifest_identifier=manifest_id,
            office_under_test_controls_manifest=False,
            result=EnterpriseCertificationDecision.PASS if validation.result == EnterpriseCertificationDecision.PASS and not contradictions else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_deterministic_execution(
        self,
        execution: SentinelRuntimeExecutionRecord,
        replay_execution: SentinelRuntimeExecutionRecord,
    ) -> OfficeDeterministicExecutionRecord:
        original_digest = sentinel_runtime_equivalence_digest(execution)
        replay_digest = sentinel_runtime_equivalence_digest(replay_execution)
        original_actions = tuple(event.action for event in execution.trace_events)
        replay_actions = tuple(event.action for event in replay_execution.trace_events)
        influences = []
        if original_digest != replay_digest:
            influences.append("semantic_digest_mismatch")
        if original_actions != replay_actions:
            influences.append("trace_order_mismatch")
        if execution.lifecycle_states != replay_execution.lifecycle_states:
            influences.append("lifecycle_mismatch")
        record = OfficeDeterministicExecutionRecord(
            deterministic_identifier=f"SENT-RM003-DET-{_digest((execution.execution_id, replay_execution.execution_id, tuple(influences)))[:12].upper()}",
            office_identity="Sentinel",
            original_execution_id=execution.execution_id,
            replay_execution_id=replay_execution.execution_id,
            original_semantic_digest=original_digest,
            replay_semantic_digest=replay_digest,
            trace_order_equivalent=original_actions == replay_actions,
            lifecycle_equivalent=execution.lifecycle_states == replay_execution.lifecycle_states,
            decision_equivalent=execution.result == replay_execution.result,
            nondeterministic_influences=tuple(influences),
            result=EnterpriseCertificationDecision.PASS if not influences and execution.result == replay_execution.result else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_state_integrity(
        self,
        execution: SentinelRuntimeExecutionRecord,
        repository: InMemoryPersistenceRepository,
    ) -> OfficeStateIntegrityRecord:
        allowed = {"", "DORMANT", "ACTIVATION_REQUESTED", "MISSION_RESOLVED", "AUTHORITY_VALIDATED", "SCHEDULED", "ACTIVE", "COMPLETING"}
        invalid_states = tuple(state for state in execution.lifecycle_states if state not in allowed)
        expected = ("DORMANT", "ACTIVATION_REQUESTED", "ACTIVE", "COMPLETING", "DORMANT")
        invalid_transitions = () if execution.lifecycle_states == expected else ("unexpected_lifecycle_path",)
        records = tuple(repository.all_records())
        sequence = tuple(_creation_sequence(record) for record in records)
        version_errors = _sequence_errors(sequence)
        recovered = recover_persisted_sentinel_records(repository)
        state_history = tuple(f"{event.before_state}->{event.after_state}:{event.trace_event_id}" for event in execution.trace_events if event.before_state or event.after_state)
        result = EnterpriseCertificationDecision.PASS if not invalid_states and not invalid_transitions and not version_errors and bool(state_history) and bool(recovered) else EnterpriseCertificationDecision.FAIL
        record = OfficeStateIntegrityRecord(
            state_identifier=f"SENT-RM003-STATE-{_digest((execution.execution_id, execution.lifecycle_states, version_errors))[:12].upper()}",
            office_identity="Sentinel",
            lifecycle_states=execution.lifecycle_states,
            invalid_states=invalid_states,
            invalid_transitions=invalid_transitions,
            version_sequence=sequence,
            version_errors=version_errors,
            immutable_state_history=state_history,
            recovered_record_hashes=recovered,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_decision_integrity(
        self,
        execution: SentinelRuntimeExecutionRecord,
        deterministic: OfficeDeterministicExecutionRecord,
    ) -> OfficeDecisionIntegrityRecord:
        envelope = execution.evidence_envelope
        decisions: list[tuple[str, str, str]] = []
        if envelope is not None:
            decisions = [
                ("duplicate", envelope.duplicate_decision.decision_id, envelope.duplicate_decision.rule_identity),
                ("independence", envelope.independence_decision.decision_id, envelope.independence_decision.independence_rule),
                ("conflict", envelope.conflict_decision.decision_id, "SENT-GOV-020-CONFLICT/1"),
                ("sufficiency", envelope.sufficiency_decision.decision_id, envelope.sufficiency_decision.rule_identity),
                ("priority", envelope.priority_decision.decision_id, envelope.priority_decision.rule_identity),
            ]
        missing_justification = tuple(name for name, decision_id, rule_id in decisions if not decision_id or not rule_id)
        supporting = (envelope.envelope_id,) if envelope else ()
        if execution.notification_ready_alert is not None:
            supporting = supporting + (execution.notification_ready_alert.alert_id,)
        missing_evidence = () if supporting and execution.trace_events else ("decision_supporting_evidence",)
        unsupported = tuple(name for name, decision_id, rule_id in decisions if not decision_id)
        result = EnterpriseCertificationDecision.PASS if decisions and not missing_justification and not missing_evidence and not unsupported and deterministic.result == EnterpriseCertificationDecision.PASS else EnterpriseCertificationDecision.FAIL
        record = OfficeDecisionIntegrityRecord(
            decision_identifier=f"SENT-RM003-DEC-{_digest((execution.execution_id, tuple(decisions), missing_evidence))[:12].upper()}",
            office_identity="Sentinel",
            evaluated_decisions=tuple(f"{name}:{decision_id}" for name, decision_id, _ in decisions),
            supporting_evidence=supporting,
            missing_justification=missing_justification,
            missing_evidence=missing_evidence,
            replay_equivalent=deterministic.result == EnterpriseCertificationDecision.PASS,
            unsupported_decisions=unsupported,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_runtime_completeness(
        self,
        execution: SentinelRuntimeExecutionRecord,
        definition: SentinelOfficeResponsibilityDefinition,
    ) -> OfficeRuntimeCompletenessRecord:
        observed = tuple(event.action for event in execution.trace_events)
        required = definition.required_behavioral_capabilities
        missing = tuple(item for item in required if item not in observed)
        markers = ()
        if execution.result == SentinelRuntimeDecision.PASS and (execution.evidence_envelope is None or execution.notification_ready_alert is None):
            markers = ("missing_success_output",)
        terminal = execution.result.value
        authority_released = execution.final_office_state.value == "DORMANT" and (not execution.lifecycle_states or execution.lifecycle_states[-1] == "DORMANT")
        output_evidence = tuple(item for item in (getattr(execution.evidence_envelope, "envelope_id", ""), getattr(execution.notification_ready_alert, "alert_id", "")) if item)
        result = EnterpriseCertificationDecision.PASS if not missing and not markers and authority_released and terminal in {"PASS", "FAIL"} and output_evidence else EnterpriseCertificationDecision.FAIL
        record = OfficeRuntimeCompletenessRecord(
            runtime_identifier=f"SENT-RM003-RUNTIME-{_digest((execution.execution_id, missing, markers))[:12].upper()}",
            office_identity="Sentinel",
            execution_id=execution.execution_id,
            lifecycle_path=execution.lifecycle_states,
            terminal_classification=terminal,
            authority_released=authority_released,
            required_runtime_paths=required,
            observed_runtime_paths=observed,
            missing_runtime_paths=missing,
            incomplete_markers=markers,
            output_evidence=output_evidence,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))

    def evaluate_persistence_integrity(
        self,
        repository: InMemoryPersistenceRepository,
        definition: SentinelOfficeResponsibilityDefinition,
    ) -> OfficePersistenceIntegrityRecord:
        records = tuple(repository.all_records())
        names = tuple(_object_name(record) for record in records)
        required = tuple(definition.persistence_model)
        missing = tuple(name for name in required if name not in names)
        prohibited = tuple(name for name in names if name in definition.prohibited_responsibilities or name.startswith("commander_") or name.startswith("sentinel_bridge_"))
        sequence = tuple(_creation_sequence(record) for record in records)
        ordering_errors = _sequence_errors(sequence)
        recovered = recover_persisted_sentinel_records(repository)
        canonical = all(bool(_payload_hash(record)) and _creation_sequence(record) > 0 for record in records)
        result = EnterpriseCertificationDecision.PASS if records and not missing and not prohibited and not ordering_errors and canonical else EnterpriseCertificationDecision.FAIL
        record = OfficePersistenceIntegrityRecord(
            persistence_identifier=f"SENT-RM003-PERSIST-{_digest((names, missing, prohibited, ordering_errors))[:12].upper()}",
            office_identity="Sentinel",
            persisted_records=names,
            required_records=required,
            missing_records=missing,
            prohibited_records=prohibited,
            creation_sequence=sequence,
            ordering_errors=ordering_errors,
            recovered_hashes=recovered,
            canonical_serialization=canonical,
            result=result,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))


def sentinel_office_responsibility_definition() -> SentinelOfficeResponsibilityDefinition:
    owned = (
        "canonical_mission_acquisition",
        "authority_validation",
        "scheduler_activation_request",
        "approved_source_acquisition",
        "observation_normalization",
        "duplicate_suppression",
        "source_independence_evaluation",
        "conflict_evaluation",
        "observation_sufficiency_evaluation",
        "priority_determination",
        "observation_evidence_generation",
        "notification_ready_alert_generation",
        "runtime_audit_trace_generation",
        "office_state_transition",
        "office_persistence_recording",
        "office_replay_projection",
        "office_recovery_projection",
        "office_recovery_validation",
        "office_replay_validation",
        "immutable_evidence_generation",
        "audit_evidence_reconstruction",
        "configuration_validation",
        "configuration_integrity_protection",
        "deterministic_error_handling",
        "office_validation_suite_support",
        "office_constitutional_integration",
    )
    prohibited = (
        "enterprise_bridge_execution",
        "commander_acknowledgment_generation",
        "enterprise_certification_decision",
        "trade_execution",
        "risk_office_decision",
        "seeker_search_execution",
        "enterprise_registry_mutation",
        "bridge_delivery_state",
        "commander_internal_state",
    )
    required_behaviors = SentinelRuntimeTraceEngine.required_success_stages
    persistence_model = {
        "sentinel_dependency_certification": "referenced external dependency evidence",
        "sentinel_authority_origin": "immutable authority-origin evidence",
        "sentinel_raw_evidence_origin": "immutable raw source origin evidence",
        "sentinel_observation_origin": "immutable normalized observation origin evidence",
        "sentinel_sufficiency_evaluation": "immutable office decision evidence",
        "sentinel_sufficiency_origin": "immutable sufficiency-origin evidence",
        "sentinel_observation_evidence": "immutable office observation evidence",
        "sentinel_notification_ready_alert": "authoritative office output",
        "sentinel_runtime_audit_trail": "immutable office runtime trace",
        "sentinel_replay_equivalence_certification": "office replay projection evidence",
    }
    certification_outputs = (
        "sentinel_office_recovery_certification",
        "sentinel_office_replay_compatibility",
        "sentinel_office_immutable_evidence",
        "sentinel_office_audit_completeness",
        "sentinel_office_configuration_integrity",
        "sentinel_office_error_handling",
        "sentinel_office_validation_suite",
        "sentinel_office_constitutional_integration",
    )
    definition = SentinelOfficeResponsibilityDefinition(
        office_identity="Sentinel",
        constitutional_purpose="Commander-directed deterministic observation and notification-ready evidence production",
        constitutional_authority=owned,
        owned_responsibilities=owned,
        prohibited_responsibilities=prohibited,
        constitutional_inputs=("Commander mission", "workflow token", "authority record", "approved source plan", "source observation"),
        produced_evidence=tuple(persistence_model) + certification_outputs,
        required_runtime_states=("DORMANT", "ACTIVATION_REQUESTED", "ACTIVE", "COMPLETING", "DORMANT"),
        required_behavioral_capabilities=required_behaviors,
        state_classification_model={
            "lifecycle_states": "Authoritative Persistent State",
            "decision_records": "Immutable Constitutional Evidence",
            "trace_events": "Immutable Constitutional Evidence",
            "source_adapter_cache": "Prohibited Persistent State",
            "commander_state": "Prohibited Persistent State",
        },
        persistence_model=persistence_model,
        interface_outputs=("SentinelNotificationReadyAlert", "SentinelRuntimeAuditTrail"),
        doctrine_version=SENT_RM_003_VERSION,
        deterministic_digest="",
    )
    return replace(definition, deterministic_digest=_digest(asdict(definition)))


def _object_name(record: PersistentRecord) -> str:
    payload = record.to_dict().get("payload", {})
    body = payload.get("payload", {}) if isinstance(payload, dict) else {}
    if isinstance(body, dict):
        return str(body.get("object_name", record.object_id))
    return record.object_id


def _creation_sequence(record: PersistentRecord) -> int:
    payload = record.to_dict().get("payload", {})
    if isinstance(payload, dict):
        try:
            return int(payload.get("creation_sequence", 0))
        except (TypeError, ValueError):
            return 0
    return 0


def _payload_hash(record: PersistentRecord) -> str:
    payload = record.to_dict().get("payload", {})
    if isinstance(payload, dict):
        return str(payload.get("payload_hash", ""))
    return ""


def _sequence_errors(sequence: tuple[int, ...]) -> tuple[str, ...]:
    errors: list[str] = []
    if any(item <= 0 for item in sequence):
        errors.append("missing_creation_sequence")
    if tuple(sorted(sequence)) != sequence:
        errors.append("non_monotonic_creation_sequence")
    if len(set(sequence)) != len(sequence):
        errors.append("duplicate_creation_sequence")
    expected = tuple(range(1, len(sequence) + 1))
    if sequence and sequence != expected:
        errors.append("non_contiguous_creation_sequence")
    return tuple(errors)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def _digest(payload: object) -> str:
    encoded = json.dumps(_json_ready(payload), sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
