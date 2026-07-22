"""ANALYST-RM-001 office integrity certification support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


class AnalystLifecycleState(str, Enum):
    CREATED = "Created"
    INITIALIZED = "Initialized"
    INPUT_VALIDATION = "Input Validation"
    NORMALIZED = "Normalized"
    ANALYTICAL_PROCESSING = "Analytical Processing"
    INTERNAL_VALIDATION = "Internal Validation"
    COMPLETED = "Completed"
    DELIVERED = "Delivered"
    ARCHIVED = "Archived"
    CERTIFIED = "Certified"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"
    SUPERSEDED = "Superseded"
    EXPIRED = "Expired"


@dataclass(frozen=True)
class AnalystAuthorityBoundaryRecord:
    authority_identifier: str
    exclusive_authorities: tuple[str, ...]
    prohibited_authorities: tuple[str, ...]
    neighboring_office_boundaries: Mapping[str, str]
    ownership_registry: Mapping[str, str]
    undefined_responsibilities: tuple[str, ...]
    overlapping_authorities: tuple[str, ...]
    prohibited_authority_findings: tuple[str, ...]
    activation_requirements: tuple[str, ...]
    relinquishment_triggers: tuple[str, ...]
    deterministic_replay_supported: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystObjectInventoryRecord:
    inventory_identifier: str
    object_registry: Mapping[str, str]
    ownership_matrix: Mapping[str, str]
    relationship_matrix: Mapping[str, tuple[str, ...]]
    authority_matrix: Mapping[str, tuple[str, ...]]
    identity_fields: tuple[str, ...]
    duplicate_objects: tuple[str, ...]
    undefined_objects: tuple[str, ...]
    ambiguous_ownership: tuple[str, ...]
    circular_relationships: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystInputAdmissibilityRecord:
    admissibility_identifier: str
    authorized_input_classes: tuple[str, ...]
    received_input_class: str
    required_components: tuple[str, ...]
    missing_components: tuple[str, ...]
    provenance_complete: bool
    ownership_valid: bool
    schema_valid: bool
    version_compatible: bool
    integrity_valid: bool
    normalization_semantic_preservation: bool
    duplicate_findings: tuple[str, ...]
    rejection_taxonomy: tuple[str, ...]
    admissibility_decision: str
    replay_reproduces_decision: bool
    recovery_preserves_audit: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystOutputContractRecord:
    contract_identifier: str
    authorized_output_classes: tuple[str, ...]
    output_type: str
    identity_fields: tuple[str, ...]
    missing_identity_fields: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    unmet_completion_requirements: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    failed_validations: tuple[str, ...]
    delivery_atomic: bool
    provenance_chain_complete: bool
    immutable_after_completion: bool
    confidence_contract_complete: bool
    contradiction_preservation_complete: bool
    replay_equivalent: bool
    recovery_preserves_ownership: bool
    delivery_decision: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystLifecycleRemediationRecord:
    lifecycle_identifier: str
    canonical_states: tuple[str, ...]
    terminal_states: tuple[str, ...]
    legal_transition_sequence: tuple[str, ...]
    observed_transition_sequence: tuple[str, ...]
    illegal_transitions: tuple[str, ...]
    skipped_required_states: tuple[str, ...]
    multiple_active_state_findings: tuple[str, ...]
    validation_failures: tuple[str, ...]
    persistence_fields: tuple[str, ...]
    replay_equivalent: bool
    recovery_preserves_lifecycle: bool
    final_state: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm001EvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    authority_boundary: AnalystAuthorityBoundaryRecord
    object_inventory: AnalystObjectInventoryRecord
    input_admissibility: AnalystInputAdmissibilityRecord
    output_contracts: AnalystOutputContractRecord
    lifecycle_remediation: AnalystLifecycleRemediationRecord
    final_rm001_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystValidationArchitectureRecord:
    validation_identifier: str
    validation_categories: tuple[str, ...]
    validation_sequence: tuple[str, ...]
    ownership_matrix: Mapping[str, str]
    missing_categories: tuple[str, ...]
    ordering_violations: tuple[str, ...]
    failed_validation_stages: tuple[str, ...]
    contradiction_reports: tuple[str, ...]
    missing_information_findings: tuple[str, ...]
    reasoning_integrity_findings: tuple[str, ...]
    downstream_reasoning_blocked: bool
    immutable_validation_evidence: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystDecisionArchitectureRecord:
    decision_identifier: str
    decision_registry: Mapping[str, tuple[str, ...]]
    authority_matrix: Mapping[str, str]
    dependency_graph: Mapping[str, tuple[str, ...]]
    missing_decisions: tuple[str, ...]
    ambiguous_authority: tuple[str, ...]
    circular_dependencies: tuple[str, ...]
    undocumented_inputs: tuple[str, ...]
    unsupported_assumptions: tuple[str, ...]
    deterministic_replay_supported: bool
    fail_closed_decisions: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystPersistenceArchitectureRecord:
    persistence_identifier: str
    persistent_state_registry: tuple[str, ...]
    transient_state_registry: tuple[str, ...]
    atomic_commit_boundaries: tuple[str, ...]
    missing_persistent_state: tuple[str, ...]
    transient_evidence_violations: tuple[str, ...]
    missing_commit_boundaries: tuple[str, ...]
    partial_commit_findings: tuple[str, ...]
    durability_failures: tuple[str, ...]
    integrity_verification_failures: tuple[str, ...]
    replay_compatible: bool
    recovery_compatible: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystReplayArchitectureRecord:
    replay_identifier: str
    replay_scope: tuple[str, ...]
    replay_prerequisites: tuple[str, ...]
    admissible_runtime_variations: tuple[str, ...]
    non_admissible_variations: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    production_mutation_findings: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    provenance_gaps: tuple[str, ...]
    validation_failures: tuple[str, ...]
    replay_outcome: str
    immutable_replay_evidence: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRecoveryArchitectureRecord:
    recovery_identifier: str
    recovery_phases: tuple[str, ...]
    checkpoint_requirements: tuple[str, ...]
    restored_state_elements: tuple[str, ...]
    missing_checkpoint_fields: tuple[str, ...]
    unauthorized_recovery_attempts: tuple[str, ...]
    invariant_violations: tuple[str, ...]
    duplicate_recovery_effects: tuple[str, ...]
    partial_recovery_findings: tuple[str, ...]
    idempotent_recovery: bool
    restart_authorized: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm001ArchitectureEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    validation_architecture: AnalystValidationArchitectureRecord
    decision_architecture: AnalystDecisionArchitectureRecord
    persistence_architecture: AnalystPersistenceArchitectureRecord
    replay_architecture: AnalystReplayArchitectureRecord
    recovery_architecture: AnalystRecoveryArchitectureRecord
    final_architecture_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


class AnalystOfficeIntegritySupport:
    """Build deterministic certification-support records for ANALYST-RM-001."""

    remediation_order_coverage = (
        "ANALYST-RM-001-001",
        "ANALYST-RM-001-002",
        "ANALYST-RM-001-003",
        "ANALYST-RM-001-004",
        "ANALYST-RM-001-005",
    )

    architecture_order_coverage = (
        "ANALYST-RM-001-006",
        "ANALYST-RM-001-007",
        "ANALYST-RM-001-008",
        "ANALYST-RM-001-009",
        "ANALYST-RM-001-010",
    )

    def build_package(
        self,
        *,
        input_object: Mapping[str, Any],
        output_object: Mapping[str, Any],
        observed_lifecycle: tuple[str, ...] | None = None,
    ) -> AnalystRm001EvidencePackage:
        authority = self.evaluate_authority_boundary()
        inventory = self.evaluate_object_inventory()
        admissibility = self.evaluate_input_admissibility(input_object)
        outputs = self.evaluate_output_contract(output_object)
        lifecycle = self.evaluate_lifecycle_remediation(
            observed_lifecycle
            or (
                AnalystLifecycleState.CREATED.value,
                AnalystLifecycleState.INITIALIZED.value,
                AnalystLifecycleState.INPUT_VALIDATION.value,
                AnalystLifecycleState.NORMALIZED.value,
                AnalystLifecycleState.ANALYTICAL_PROCESSING.value,
                AnalystLifecycleState.INTERNAL_VALIDATION.value,
                AnalystLifecycleState.COMPLETED.value,
                AnalystLifecycleState.DELIVERED.value,
                AnalystLifecycleState.ARCHIVED.value,
                AnalystLifecycleState.CERTIFIED.value,
            )
        )
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (authority, inventory, admissibility, outputs, lifecycle)
        ) else EnterpriseCertificationDecision.FAIL
        package = AnalystRm001EvidencePackage(
            package_identifier=f"ANALYST-RM-001-PACKAGE-{_digest((input_object, output_object, observed_lifecycle))[:12].upper()}",
            governing_doctrine="ANALYST-RM-001-001-TO-005/1.0.0",
            remediation_order_coverage=self.remediation_order_coverage,
            authority_boundary=authority,
            object_inventory=inventory,
            input_admissibility=admissibility,
            output_contracts=outputs,
            lifecycle_remediation=lifecycle,
            final_rm001_readiness=final,
            immutable_audit_references=(
                authority.authority_identifier,
                inventory.inventory_identifier,
                admissibility.admissibility_identifier,
                outputs.contract_identifier,
                lifecycle.lifecycle_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_authority_boundary(
        self,
        *,
        undefined_responsibilities: tuple[str, ...] = (),
        overlapping_authorities: tuple[str, ...] = (),
        prohibited_authority_findings: tuple[str, ...] = (),
    ) -> AnalystAuthorityBoundaryRecord:
        exclusive = (
            "Analytical Interpretation",
            "Evidence Integration",
            "Analytical Reasoning",
            "Analytical Object Production",
            "Analytical Validation",
            "Analytical Provenance",
            "Analytical Confidence",
            "Analytical Traceability",
        )
        prohibited = (
            "Discover Information",
            "Collect Raw Intelligence",
            "Monitor External Sources",
            "Perform Risk Evaluation",
            "Execute Trades",
            "Maintain Enterprise History",
            "Modify Enterprise Configuration",
            "Reassign Constitutional Ownership",
            "Invent Missing Evidence",
            "Override Validation",
            "Produce Non-Deterministic Conclusions",
        )
        neighbors = MappingProxyType(
            {
                "Commander": "authorizes analytical work; does not reason",
                "Sentinel": "supplies observations; does not conclude",
                "Seeker": "discovers candidate information; does not analyze",
                "Risk": "evaluates uncertainty and enterprise risk",
                "Trader": "owns execution",
                "Historian": "archives enterprise truth",
                "Librarian": "manages approved knowledge",
                "Academy": "owns learning and improvement",
            }
        )
        ownership = MappingProxyType({authority: "Analyst Office" for authority in exclusive})
        passed = not undefined_responsibilities and not overlapping_authorities and not prohibited_authority_findings
        record = AnalystAuthorityBoundaryRecord(
            authority_identifier=f"ANALYST-RM-001-001-AUTH-{_digest((exclusive, prohibited, neighbors))[:12].upper()}",
            exclusive_authorities=exclusive,
            prohibited_authorities=prohibited,
            neighboring_office_boundaries=neighbors,
            ownership_registry=ownership,
            undefined_responsibilities=undefined_responsibilities,
            overlapping_authorities=overlapping_authorities,
            prohibited_authority_findings=prohibited_authority_findings,
            activation_requirements=("valid_activation", "admissible_inputs", "successful_validation", "ownership_assignment"),
            relinquishment_triggers=("analytical_completion", "constitutional_rejection", "constitutional_failure", "office_termination"),
            deterministic_replay_supported=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_object_inventory(
        self,
        *,
        undefined_objects: tuple[str, ...] = (),
        ambiguous_ownership: tuple[str, ...] = (),
        circular_relationships: tuple[str, ...] = (),
    ) -> AnalystObjectInventoryRecord:
        registry = MappingProxyType(
            {
                "Analysis Mission": "immutable analytical assignment",
                "Analytical Context": "normalized contextual information",
                "Analytical Evidence Set": "admissible evidence accepted for analysis",
                "Analytical Model": "normalized analytical representation",
                "Analytical Findings": "immutable findings from analysis",
                "Analytical Assessment": "complete constitutional assessment",
                "Analytical Recommendation": "Analyst-owned recommendation",
                "Analytical Decision Record": "deterministic analytical decision",
                "Analytical Trace Record": "input-to-output reasoning trace",
                "Analyst Validation Record": "validation result and violations",
                "Analyst Configuration Snapshot": "immutable configuration versions",
                "Analyst Audit Record": "immutable execution evidence",
            }
        )
        ownership = MappingProxyType({name: "Analyst Office" for name in registry})
        relationships = MappingProxyType(
            {
                "Analysis Mission": ("Analytical Context", "Analytical Evidence Set"),
                "Analytical Context": ("Analytical Model",),
                "Analytical Evidence Set": ("Analytical Findings", "Analytical Trace Record"),
                "Analytical Model": ("Analytical Findings",),
                "Analytical Findings": ("Analytical Assessment", "Analytical Recommendation"),
                "Analytical Assessment": ("Analytical Decision Record", "Analytical Trace Record"),
                "Analytical Recommendation": ("Analytical Decision Record",),
                "Analytical Decision Record": ("Analyst Audit Record",),
                "Analytical Trace Record": ("Analyst Audit Record",),
                "Analyst Validation Record": ("Analytical Assessment", "Analyst Audit Record"),
                "Analyst Configuration Snapshot": ("Analysis Mission", "Analyst Validation Record"),
                "Analyst Audit Record": (),
            }
        )
        authority = MappingProxyType({name: ("create", "validate", "archive", "retire") for name in registry})
        duplicates = tuple(sorted({name for name in registry if list(registry).count(name) > 1}))
        passed = not duplicates and not undefined_objects and not ambiguous_ownership and not circular_relationships
        record = AnalystObjectInventoryRecord(
            inventory_identifier=f"ANALYST-RM-001-002-OBJ-{_digest(registry)[:12].upper()}",
            object_registry=registry,
            ownership_matrix=ownership,
            relationship_matrix=relationships,
            authority_matrix=authority,
            identity_fields=("object_identifier", "object_type", "object_version", "originating_office", "originating_authority", "creation_timestamp", "constitutional_status"),
            duplicate_objects=duplicates,
            undefined_objects=undefined_objects,
            ambiguous_ownership=ambiguous_ownership,
            circular_relationships=circular_relationships,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_input_admissibility(
        self,
        input_object: Mapping[str, Any],
        *,
        duplicate_findings: tuple[str, ...] = (),
    ) -> AnalystInputAdmissibilityRecord:
        authorized = (
            "Candidate Package",
            "Discovery Evidence",
            "Search Provenance",
            "Source Metadata",
            "Sentinel Intelligence",
            "Historical Context",
            "Configuration Object",
            "Replay Object",
            "Recovery Object",
            "Certification Object",
        )
        required = (
            "canonical_identifier",
            "object_class",
            "object_version",
            "owner",
            "producer_office",
            "production_timestamp",
            "constitutional_schema_version",
            "provenance_metadata",
            "integrity_verification_metadata",
            "admissibility_metadata",
        )
        missing = tuple(field for field in required if not input_object.get(field))
        input_class = str(input_object.get("object_class", ""))
        provenance_complete = bool(input_object.get("provenance_metadata"))
        ownership_valid = input_object.get("owner") in {"Seeker Office", "Sentinel Office", "Historian Office", "Enterprise Infrastructure", "Certification Authority", "Analyst Office"}
        schema_valid = bool(input_object.get("constitutional_schema_version")) and not input_object.get("schema_error")
        version_compatible = str(input_object.get("object_version", "")).startswith("1.")
        integrity_valid = bool(input_object.get("integrity_verification_metadata")) and not input_object.get("corrupt")
        semantic = not bool(input_object.get("semantic_mutation"))
        rejection = []
        if input_class not in authorized:
            rejection.append("unauthorized_input_class")
        if missing:
            rejection.append("incomplete_metadata")
        if not ownership_valid:
            rejection.append("invalid_owner")
        if not provenance_complete:
            rejection.append("invalid_provenance")
        if not schema_valid:
            rejection.append("invalid_schema")
        if not version_compatible:
            rejection.append("unsupported_version")
        if not integrity_valid:
            rejection.append("failed_integrity_verification")
        if duplicate_findings:
            rejection.append("duplicate_violation")
        if not semantic:
            rejection.append("normalization_semantic_mutation")
        passed = not rejection
        record = AnalystInputAdmissibilityRecord(
            admissibility_identifier=f"ANALYST-RM-001-003-IN-{_digest(input_object)[:12].upper()}",
            authorized_input_classes=authorized,
            received_input_class=input_class,
            required_components=required,
            missing_components=missing,
            provenance_complete=provenance_complete,
            ownership_valid=ownership_valid,
            schema_valid=schema_valid,
            version_compatible=version_compatible,
            integrity_valid=integrity_valid,
            normalization_semantic_preservation=semantic,
            duplicate_findings=duplicate_findings,
            rejection_taxonomy=tuple(rejection),
            admissibility_decision="Admitted" if passed else "Rejected",
            replay_reproduces_decision=True,
            recovery_preserves_audit=True,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_output_contract(
        self,
        output_object: Mapping[str, Any],
        *,
        failed_validations: tuple[str, ...] = (),
    ) -> AnalystOutputContractRecord:
        authorized = (
            "Analytical Assessment",
            "Analytical Conclusion",
            "Evidence Package",
            "Confidence Assessment",
            "Alternative Hypothesis Evaluation",
            "Contradiction Report",
            "Analytical Recommendation",
            "Risk Characterization Input",
            "Commander Decision Support Package",
            "Certification Evidence Package",
        )
        identity = ("output_identifier", "output_type", "source_analysis_identifier", "analyst_office_identifier", "version", "creation_timestamp", "constitutional_owner", "schema_version", "provenance_identifier", "certification_state")
        completion = ("mandatory_fields_populated", "reasoning_complete", "evidence_attached", "validation_complete", "invariants_satisfied", "confidence_established", "contradictions_resolved", "provenance_finalized", "schema_validated", "certification_state_assigned")
        validations = ("Schema Validation", "Identity Validation", "Ownership Validation", "Evidence Completeness", "Reasoning Integrity", "Confidence Validation", "Contradiction Resolution", "Invariant Validation", "Version Validation", "Certification Validation")
        missing_identity = tuple(field for field in identity if not output_object.get(field))
        unmet = tuple(item for item in completion if not output_object.get(item))
        output_type = str(output_object.get("output_type", ""))
        failed = tuple(dict.fromkeys(failed_validations + (() if output_type in authorized else ("unauthorized_output_type",))))
        atomic = bool(output_object.get("delivery_atomic", True))
        provenance = bool(output_object.get("provenance_chain_complete", True))
        immutable = bool(output_object.get("immutable_after_completion", True))
        confidence = bool(output_object.get("confidence_contract_complete", True))
        contradiction = bool(output_object.get("contradiction_preservation_complete", True))
        replay = bool(output_object.get("replay_equivalent", True))
        recovery = bool(output_object.get("recovery_preserves_ownership", True))
        passed = not missing_identity and not unmet and not failed and atomic and provenance and immutable and confidence and contradiction and replay and recovery
        record = AnalystOutputContractRecord(
            contract_identifier=f"ANALYST-RM-001-004-OUT-{_digest(output_object)[:12].upper()}",
            authorized_output_classes=authorized,
            output_type=output_type,
            identity_fields=identity,
            missing_identity_fields=missing_identity,
            completion_requirements=completion,
            unmet_completion_requirements=unmet,
            validation_requirements=validations,
            failed_validations=failed,
            delivery_atomic=atomic,
            provenance_chain_complete=provenance,
            immutable_after_completion=immutable,
            confidence_contract_complete=confidence,
            contradiction_preservation_complete=contradiction,
            replay_equivalent=replay,
            recovery_preserves_ownership=recovery,
            delivery_decision="Deliver" if passed else "Do Not Deliver",
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_lifecycle_remediation(
        self,
        observed_transition_sequence: tuple[str, ...],
        *,
        multiple_active_state_findings: tuple[str, ...] = (),
        validation_failures: tuple[str, ...] = (),
        replay_equivalent: bool = True,
        recovery_preserves_lifecycle: bool = True,
    ) -> AnalystLifecycleRemediationRecord:
        canonical = tuple(state.value for state in AnalystLifecycleState)
        terminal = (
            AnalystLifecycleState.REJECTED.value,
            AnalystLifecycleState.CANCELLED.value,
            AnalystLifecycleState.SUPERSEDED.value,
            AnalystLifecycleState.EXPIRED.value,
            AnalystLifecycleState.CERTIFIED.value,
        )
        legal = (
            AnalystLifecycleState.CREATED.value,
            AnalystLifecycleState.INITIALIZED.value,
            AnalystLifecycleState.INPUT_VALIDATION.value,
            AnalystLifecycleState.NORMALIZED.value,
            AnalystLifecycleState.ANALYTICAL_PROCESSING.value,
            AnalystLifecycleState.INTERNAL_VALIDATION.value,
            AnalystLifecycleState.COMPLETED.value,
            AnalystLifecycleState.DELIVERED.value,
            AnalystLifecycleState.ARCHIVED.value,
            AnalystLifecycleState.CERTIFIED.value,
        )
        legal_edges = set(zip(legal, legal[1:])) | {
            (AnalystLifecycleState.INPUT_VALIDATION.value, AnalystLifecycleState.REJECTED.value),
            (AnalystLifecycleState.INTERNAL_VALIDATION.value, AnalystLifecycleState.REJECTED.value),
            (AnalystLifecycleState.CREATED.value, AnalystLifecycleState.CANCELLED.value),
            (AnalystLifecycleState.COMPLETED.value, AnalystLifecycleState.SUPERSEDED.value),
            (AnalystLifecycleState.INITIALIZED.value, AnalystLifecycleState.EXPIRED.value),
        }
        illegal = tuple(f"{left}->{right}" for left, right in zip(observed_transition_sequence, observed_transition_sequence[1:]) if (left, right) not in legal_edges)
        skipped = tuple(state for state in legal if state not in observed_transition_sequence and observed_transition_sequence[-1:] == (AnalystLifecycleState.CERTIFIED.value,))
        final_state = observed_transition_sequence[-1] if observed_transition_sequence else ""
        passed = (
            bool(observed_transition_sequence)
            and not illegal
            and not skipped
            and not multiple_active_state_findings
            and not validation_failures
            and replay_equivalent
            and recovery_preserves_lifecycle
            and final_state in terminal
        )
        record = AnalystLifecycleRemediationRecord(
            lifecycle_identifier=f"ANALYST-RM-001-005-LIFE-{_digest(observed_transition_sequence)[:12].upper()}",
            canonical_states=canonical,
            terminal_states=terminal,
            legal_transition_sequence=legal,
            observed_transition_sequence=observed_transition_sequence,
            illegal_transitions=illegal,
            skipped_required_states=skipped,
            multiple_active_state_findings=multiple_active_state_findings,
            validation_failures=validation_failures,
            persistence_fields=("current_lifecycle_state", "transition_history", "timestamps", "owner", "validation_evidence", "transition_authority", "dependency_references"),
            replay_equivalent=replay_equivalent,
            recovery_preserves_lifecycle=recovery_preserves_lifecycle,
            final_state=final_state,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_architecture_package(self) -> AnalystRm001ArchitectureEvidencePackage:
        validation = self.evaluate_validation_architecture()
        decision = self.evaluate_decision_architecture()
        persistence = self.evaluate_persistence_architecture()
        replay = self.evaluate_replay_architecture()
        recovery = self.evaluate_recovery_architecture()
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (validation, decision, persistence, replay, recovery)
        ) else EnterpriseCertificationDecision.FAIL
        package = AnalystRm001ArchitectureEvidencePackage(
            package_identifier=f"ANALYST-RM-001-ARCH-{_digest((validation, decision, persistence, replay, recovery))[:12].upper()}",
            governing_doctrine="ANALYST-RM-001-006-TO-010/1.0.0",
            remediation_order_coverage=self.architecture_order_coverage,
            validation_architecture=validation,
            decision_architecture=decision,
            persistence_architecture=persistence,
            replay_architecture=replay,
            recovery_architecture=recovery,
            final_architecture_readiness=final,
            immutable_audit_references=(
                validation.validation_identifier,
                decision.decision_identifier,
                persistence.persistence_identifier,
                replay.replay_identifier,
                recovery.recovery_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_validation_architecture(
        self,
        *,
        observed_sequence: tuple[str, ...] | None = None,
        failed_validation_stages: tuple[str, ...] = (),
        contradiction_reports: tuple[str, ...] = (),
        missing_information_findings: tuple[str, ...] = (),
        reasoning_integrity_findings: tuple[str, ...] = (),
    ) -> AnalystValidationArchitectureRecord:
        categories = (
            "Identity Validation",
            "Schema Validation",
            "Ownership Validation",
            "Admissibility Validation",
            "Dependency Validation",
            "Evidence Integrity Validation",
            "Rule Compliance Validation",
            "Analytical Consistency Validation",
            "Provenance Validation",
            "Completion Validation",
        )
        sequence = observed_sequence or categories
        missing = tuple(category for category in categories if category not in sequence)
        expected_index = {stage: index for index, stage in enumerate(categories)}
        ordering = tuple(
            f"{left}->{right}"
            for left, right in zip(sequence, sequence[1:])
            if left in expected_index and right in expected_index and expected_index[left] > expected_index[right]
        )
        ownership = MappingProxyType({category: "Analyst Office" for category in categories})
        blocked = bool(failed_validation_stages or missing or ordering or reasoning_integrity_findings)
        passed = not missing and not ordering and not failed_validation_stages and not reasoning_integrity_findings
        evidence = tuple(f"VAL-EVID-{_digest((stage, index))[:12].upper()}" for index, stage in enumerate(sequence, start=1))
        record = AnalystValidationArchitectureRecord(
            validation_identifier=f"ANALYST-RM-001-006-VAL-{_digest((sequence, failed_validation_stages))[:12].upper()}",
            validation_categories=categories,
            validation_sequence=sequence,
            ownership_matrix=ownership,
            missing_categories=missing,
            ordering_violations=ordering,
            failed_validation_stages=failed_validation_stages,
            contradiction_reports=contradiction_reports,
            missing_information_findings=missing_information_findings,
            reasoning_integrity_findings=reasoning_integrity_findings,
            downstream_reasoning_blocked=blocked,
            immutable_validation_evidence=evidence,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_decision_architecture(
        self,
        *,
        missing_decisions: tuple[str, ...] = (),
        ambiguous_authority: tuple[str, ...] = (),
        circular_dependencies: tuple[str, ...] = (),
        undocumented_inputs: tuple[str, ...] = (),
        unsupported_assumptions: tuple[str, ...] = (),
        deterministic_replay_supported: bool = True,
    ) -> AnalystDecisionArchitectureRecord:
        decisions = MappingProxyType(
            {
                "Input Admissibility Decision": ("Accepted", "Rejected", "Deferred Pending Validation"),
                "Evidence Sufficiency Decision": ("Sufficient", "Insufficient"),
                "Evidence Consistency Decision": ("Consistent", "Inconsistent", "Requires Resolution"),
                "Analytical Completeness Decision": ("Complete", "Incomplete"),
                "Finding Acceptance Decision": ("Accepted", "Rejected"),
                "Recommendation Authorization Decision": ("Authorized", "Rejected"),
                "Output Readiness Decision": ("Ready", "Not Ready"),
                "Constitutional Validation Decision": ("Valid", "Invalid"),
                "Replay Equivalence Decision": ("Equivalent", "Divergent"),
                "Recovery Integrity Decision": ("Preserved", "Invalid"),
            }
        )
        authority = MappingProxyType({name: "Analyst Office" for name in decisions})
        dependency = MappingProxyType(
            {
                "Input Admissibility Decision": (),
                "Evidence Sufficiency Decision": ("Input Admissibility Decision",),
                "Evidence Consistency Decision": ("Evidence Sufficiency Decision",),
                "Analytical Completeness Decision": ("Evidence Consistency Decision",),
                "Finding Acceptance Decision": ("Analytical Completeness Decision",),
                "Recommendation Authorization Decision": ("Finding Acceptance Decision",),
                "Output Readiness Decision": ("Recommendation Authorization Decision",),
                "Constitutional Validation Decision": ("Output Readiness Decision",),
                "Replay Equivalence Decision": ("Constitutional Validation Decision",),
                "Recovery Integrity Decision": ("Constitutional Validation Decision",),
            }
        )
        fail_closed = missing_decisions + ambiguous_authority + circular_dependencies + undocumented_inputs + unsupported_assumptions
        passed = not fail_closed and deterministic_replay_supported
        record = AnalystDecisionArchitectureRecord(
            decision_identifier=f"ANALYST-RM-001-007-DEC-{_digest(decisions)[:12].upper()}",
            decision_registry=decisions,
            authority_matrix=authority,
            dependency_graph=dependency,
            missing_decisions=missing_decisions,
            ambiguous_authority=ambiguous_authority,
            circular_dependencies=circular_dependencies,
            undocumented_inputs=undocumented_inputs,
            unsupported_assumptions=unsupported_assumptions,
            deterministic_replay_supported=deterministic_replay_supported,
            fail_closed_decisions=fail_closed,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_persistence_architecture(
        self,
        *,
        missing_persistent_state: tuple[str, ...] = (),
        transient_evidence_violations: tuple[str, ...] = (),
        missing_commit_boundaries: tuple[str, ...] = (),
        partial_commit_findings: tuple[str, ...] = (),
        durability_failures: tuple[str, ...] = (),
        integrity_verification_failures: tuple[str, ...] = (),
        replay_compatible: bool = True,
        recovery_compatible: bool = True,
    ) -> AnalystPersistenceArchitectureRecord:
        persistent = (
            "Analysis Objects",
            "Analytical Decisions",
            "Reasoning Artifacts",
            "Decision Evidence",
            "Validation Results",
            "Candidate Evaluations",
            "Provenance Records",
            "Configuration Snapshots",
            "Audit Records",
            "Replay Metadata",
            "Recovery Metadata",
            "Certification Evidence",
        )
        transient = (
            "temporary calculations",
            "execution stacks",
            "temporary caches",
            "optimization structures",
            "runtime indexes",
            "temporary scheduling queues",
            "ephemeral execution variables",
            "temporary serialization buffers",
            "intermediate parsing structures",
            "temporary memory allocations",
        )
        commits = (
            "Analysis Object creation",
            "analysis completion",
            "decision publication",
            "evidence publication",
            "validation completion",
            "configuration commitment",
            "checkpoint creation",
            "audit commitment",
            "certification evidence creation",
        )
        missing = tuple(item for item in persistent if item in missing_persistent_state) + tuple(item for item in missing_commit_boundaries if item in commits)
        passed = (
            not missing
            and not transient_evidence_violations
            and not partial_commit_findings
            and not durability_failures
            and not integrity_verification_failures
            and replay_compatible
            and recovery_compatible
        )
        record = AnalystPersistenceArchitectureRecord(
            persistence_identifier=f"ANALYST-RM-001-008-PERSIST-{_digest((persistent, commits))[:12].upper()}",
            persistent_state_registry=persistent,
            transient_state_registry=transient,
            atomic_commit_boundaries=commits,
            missing_persistent_state=tuple(item for item in persistent if item in missing_persistent_state),
            transient_evidence_violations=transient_evidence_violations,
            missing_commit_boundaries=tuple(item for item in missing_commit_boundaries if item in commits),
            partial_commit_findings=partial_commit_findings,
            durability_failures=durability_failures,
            integrity_verification_failures=integrity_verification_failures,
            replay_compatible=replay_compatible,
            recovery_compatible=recovery_compatible,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_replay_architecture(
        self,
        *,
        missing_prerequisites: tuple[str, ...] = (),
        production_mutation_findings: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        provenance_gaps: tuple[str, ...] = (),
        validation_failures: tuple[str, ...] = (),
    ) -> AnalystReplayArchitectureRecord:
        scope = (
            "Analytical Inputs",
            "Normalized Evidence",
            "Evidence Packages",
            "Analytical Objects",
            "Analytical Reasoning",
            "Decision Objects",
            "Confidence Assessments",
            "Alternative Evaluations",
            "Contradiction Analysis",
            "Analytical Outputs",
            "Validation Results",
            "Delivery Records",
            "Audit Records",
        )
        prerequisites = ("complete constitutional inputs", "preserved immutable evidence", "required schemas", "compatible configuration", "valid ownership", "replay authorization")
        admissible = ("execution timing", "processor architecture", "operating system", "thread scheduling", "memory layout", "storage implementation", "network latency", "internal optimization")
        non_admissible = ("analytical conclusions", "ownership", "object identity", "confidence calculation", "evidence relationships", "contradiction resolution", "validation outcome", "certification state", "audit meaning", "provenance")
        passed = not missing_prerequisites and not production_mutation_findings and not replay_divergence_findings and not provenance_gaps and not validation_failures
        record = AnalystReplayArchitectureRecord(
            replay_identifier=f"ANALYST-RM-001-009-REPLAY-{_digest(scope)[:12].upper()}",
            replay_scope=scope,
            replay_prerequisites=prerequisites,
            admissible_runtime_variations=admissible,
            non_admissible_variations=non_admissible,
            missing_prerequisites=missing_prerequisites,
            production_mutation_findings=production_mutation_findings,
            replay_divergence_findings=replay_divergence_findings,
            provenance_gaps=provenance_gaps,
            validation_failures=validation_failures,
            replay_outcome="Equivalent" if passed else "Failed",
            immutable_replay_evidence=tuple(f"REPLAY-EVID-{_digest((item, index))[:12].upper()}" for index, item in enumerate(scope, start=1)),
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_recovery_architecture(
        self,
        *,
        missing_checkpoint_fields: tuple[str, ...] = (),
        unauthorized_recovery_attempts: tuple[str, ...] = (),
        invariant_violations: tuple[str, ...] = (),
        duplicate_recovery_effects: tuple[str, ...] = (),
        partial_recovery_findings: tuple[str, ...] = (),
        idempotent_recovery: bool = True,
        restart_authorized: bool = True,
    ) -> AnalystRecoveryArchitectureRecord:
        phases = ("Environment Verification", "Checkpoint Validation", "State Restoration", "Invariant Verification", "Restart Authorization")
        checkpoint = ("checkpoint identifier", "execution identifier", "object identities", "lifecycle states", "ownership information", "committed analytical outputs", "validation status", "dependency references", "configuration version", "constitutional version", "persistence metadata", "integrity verification data")
        restored = ("persistent office state", "lifecycle states", "object identities", "dependency relationships", "validation status", "execution metadata")
        passed = (
            not missing_checkpoint_fields
            and not unauthorized_recovery_attempts
            and not invariant_violations
            and not duplicate_recovery_effects
            and not partial_recovery_findings
            and idempotent_recovery
            and restart_authorized
        )
        record = AnalystRecoveryArchitectureRecord(
            recovery_identifier=f"ANALYST-RM-001-010-RECOVERY-{_digest((phases, checkpoint))[:12].upper()}",
            recovery_phases=phases,
            checkpoint_requirements=checkpoint,
            restored_state_elements=restored,
            missing_checkpoint_fields=missing_checkpoint_fields,
            unauthorized_recovery_attempts=unauthorized_recovery_attempts,
            invariant_violations=invariant_violations,
            duplicate_recovery_effects=duplicate_recovery_effects,
            partial_recovery_findings=partial_recovery_findings,
            idempotent_recovery=idempotent_recovery,
            restart_authorized=restart_authorized,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return {key: _jsonable(item) for key, item in value.items()}
    if is_dataclass(value):
        return {
            field_info.name: _jsonable(getattr(value, field_info.name))
            for field_info in fields(value)
            if field_info.name != "deterministic_digest"
        }
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(item) for item in value]
    return value
