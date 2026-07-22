"""ANALYST-RM-002 office completion certification support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


@dataclass(frozen=True)
class AnalystCanonicalObjectCompletionRecord:
    completion_identifier: str
    canonical_objects: Mapping[str, str]
    required_attributes: tuple[str, ...]
    immutable_relationship_chain: tuple[str, ...]
    object_invariants: tuple[str, ...]
    undefined_objects: tuple[str, ...]
    missing_attributes: tuple[str, ...]
    ambiguous_ownership: tuple[str, ...]
    relationship_violations: tuple[str, ...]
    invariant_violations: tuple[str, ...]
    replay_supported: bool
    recovery_supported: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystInputCompletionRecord:
    completion_identifier: str
    input_classes: tuple[str, ...]
    contract_fields: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    freshness_fields: tuple[str, ...]
    dependency_requirements: tuple[str, ...]
    unauthorized_inputs: tuple[str, ...]
    missing_contract_fields: tuple[str, ...]
    ownership_transfer_violations: tuple[str, ...]
    normalization_failures: tuple[str, ...]
    validation_failures: tuple[str, ...]
    circular_dependencies: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystOutputCompletionRecord:
    completion_identifier: str
    output_classes: tuple[str, ...]
    identity_fields: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    publication_requirements: tuple[str, ...]
    unauthorized_outputs: tuple[str, ...]
    missing_identity_fields: tuple[str, ...]
    unmet_completion_requirements: tuple[str, ...]
    validation_failures: tuple[str, ...]
    duplicate_publication_findings: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_integrity_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystLifecycleCompletionRecord:
    completion_identifier: str
    lifecycle_states: tuple[str, ...]
    legal_transition_sequence: tuple[str, ...]
    restoration_transition_sequence: tuple[str, ...]
    prohibited_transitions: tuple[str, ...]
    observed_transition_sequence: tuple[str, ...]
    illegal_transitions: tuple[str, ...]
    missing_states: tuple[str, ...]
    revision_violations: tuple[str, ...]
    archival_violations: tuple[str, ...]
    replay_lifecycle_violations: tuple[str, ...]
    recovery_lifecycle_violations: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystReasoningArchitectureCompletionRecord:
    completion_identifier: str
    reasoning_stages: tuple[str, ...]
    inference_fields: tuple[str, ...]
    dependency_fields: tuple[str, ...]
    persistent_reasoning_state: tuple[str, ...]
    missing_stages: tuple[str, ...]
    undocumented_assumptions: tuple[str, ...]
    hidden_inferences: tuple[str, ...]
    circular_dependencies: tuple[str, ...]
    contradiction_suppression_findings: tuple[str, ...]
    replay_reasoning_violations: tuple[str, ...]
    recovery_reasoning_violations: tuple[str, ...]
    fail_closed_on_incomplete_reasoning: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm002CompletionEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    canonical_objects: AnalystCanonicalObjectCompletionRecord
    analytical_inputs: AnalystInputCompletionRecord
    analytical_outputs: AnalystOutputCompletionRecord
    analytical_lifecycle: AnalystLifecycleCompletionRecord
    reasoning_architecture: AnalystReasoningArchitectureCompletionRecord
    final_completion_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystConfidenceProbabilityCompletionRecord:
    completion_identifier: str
    confidence_object_fields: tuple[str, ...]
    admissible_confidence_inputs: tuple[str, ...]
    lifecycle_states: tuple[str, ...]
    required_registries: tuple[str, ...]
    missing_object_fields: tuple[str, ...]
    inadmissible_inputs: tuple[str, ...]
    uncertainty_gaps: tuple[str, ...]
    implicit_inheritance_findings: tuple[str, ...]
    contradiction_suppression_findings: tuple[str, ...]
    replay_drift_findings: tuple[str, ...]
    recovery_recompute_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystCompetingHypothesisCompletionRecord:
    completion_identifier: str
    hypothesis_identity_fields: tuple[str, ...]
    relationship_types: tuple[str, ...]
    lifecycle_states: tuple[str, ...]
    evaluation_criteria: tuple[str, ...]
    unsupported_hypotheses: tuple[str, ...]
    duplicate_hypotheses: tuple[str, ...]
    missing_contradiction_records: tuple[str, ...]
    nondeterministic_order_findings: tuple[str, ...]
    suppressed_non_selected_hypotheses: tuple[str, ...]
    lifecycle_violations: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystDeterministicDecisionCompletionRecord:
    completion_identifier: str
    decision_classes: tuple[str, ...]
    required_outputs: tuple[str, ...]
    dependency_rules: tuple[str, ...]
    missing_decision_classes: tuple[str, ...]
    shared_authority_findings: tuple[str, ...]
    undefined_inputs: tuple[str, ...]
    circular_dependencies: tuple[str, ...]
    default_approval_findings: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_history_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystValidationCompletionRecord:
    completion_identifier: str
    validation_lifecycle: tuple[str, ...]
    validation_classes: tuple[str, ...]
    validation_sequence: tuple[str, ...]
    validation_outcomes: tuple[str, ...]
    missing_stages: tuple[str, ...]
    ordering_violations: tuple[str, ...]
    bypass_findings: tuple[str, ...]
    invalid_outcomes: tuple[str, ...]
    evidence_gaps: tuple[str, ...]
    replay_validation_gaps: tuple[str, ...]
    recovery_validation_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystPersistenceCompletionRecord:
    completion_identifier: str
    persistent_state_classes: tuple[str, ...]
    transient_state_classes: tuple[str, ...]
    persistence_lifecycle: tuple[str, ...]
    commit_fields: tuple[str, ...]
    missing_persistent_state: tuple[str, ...]
    transient_state_violations: tuple[str, ...]
    lifecycle_bypass_findings: tuple[str, ...]
    partial_commit_findings: tuple[str, ...]
    durability_failures: tuple[str, ...]
    integrity_failures: tuple[str, ...]
    replay_regeneration_findings: tuple[str, ...]
    recovery_mutation_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm002AdvancedCompletionEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    confidence_probability: AnalystConfidenceProbabilityCompletionRecord
    competing_hypotheses: AnalystCompetingHypothesisCompletionRecord
    deterministic_decisions: AnalystDeterministicDecisionCompletionRecord
    validation_completion: AnalystValidationCompletionRecord
    persistence_completion: AnalystPersistenceCompletionRecord
    final_advanced_completion_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystReplayCompletionRecord:
    completion_identifier: str
    replay_scope: tuple[str, ...]
    historical_inputs: tuple[str, ...]
    semantic_comparison_fields: tuple[str, ...]
    admissible_runtime_differences: tuple[str, ...]
    prohibited_differences: tuple[str, ...]
    failure_classes: tuple[str, ...]
    missing_scope: tuple[str, ...]
    current_state_substitutions: tuple[str, ...]
    prohibited_difference_findings: tuple[str, ...]
    validation_gaps: tuple[str, ...]
    history_mutation_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRecoveryCompletionRecord:
    completion_identifier: str
    recovery_scope: tuple[str, ...]
    recovery_checkpoints: tuple[str, ...]
    checkpoint_fields: tuple[str, ...]
    recovery_sequence: tuple[str, ...]
    missing_recovery_state: tuple[str, ...]
    arbitrary_checkpoint_findings: tuple[str, ...]
    partial_restore_findings: tuple[str, ...]
    idempotency_violations: tuple[str, ...]
    invariant_violations: tuple[str, ...]
    fail_closed: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystConfigurationCompletionRecord:
    completion_identifier: str
    configuration_classes: tuple[str, ...]
    identity_fields: tuple[str, ...]
    compatibility_targets: tuple[str, ...]
    missing_configuration_classes: tuple[str, ...]
    ownership_violations: tuple[str, ...]
    hidden_configuration_findings: tuple[str, ...]
    implicit_default_findings: tuple[str, ...]
    compatibility_gaps: tuple[str, ...]
    integrity_failures: tuple[str, ...]
    replay_substitution_findings: tuple[str, ...]
    recovery_drift_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystTraceabilityCompletionRecord:
    completion_identifier: str
    artifact_scope: tuple[str, ...]
    canonical_chain: tuple[str, ...]
    relationship_types: tuple[str, ...]
    trace_identity_fields: tuple[str, ...]
    orphaned_artifacts: tuple[str, ...]
    implicit_lineage_findings: tuple[str, ...]
    undefined_relationships: tuple[str, ...]
    broken_lineage_findings: tuple[str, ...]
    replay_trace_gaps: tuple[str, ...]
    recovery_trace_gaps: tuple[str, ...]
    certification_trace_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystIndependentCompletionReviewRecord:
    completion_identifier: str
    required_work_orders: tuple[str, ...]
    completed_work_orders: tuple[str, ...]
    review_domains: tuple[str, ...]
    missing_work_orders: tuple[str, ...]
    constitutional_inconsistencies: tuple[str, ...]
    implementation_discretion_findings: tuple[str, ...]
    missing_certification_evidence: tuple[str, ...]
    missing_audit_evidence: tuple[str, ...]
    progression_authorized: bool
    completion_outcome: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm002FinalCompletionEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    remediation_order_coverage: tuple[str, ...]
    replay_completion: AnalystReplayCompletionRecord
    recovery_completion: AnalystRecoveryCompletionRecord
    configuration_completion: AnalystConfigurationCompletionRecord
    traceability_completion: AnalystTraceabilityCompletionRecord
    independent_completion_review: AnalystIndependentCompletionReviewRecord
    final_rm002_completion_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


class AnalystOfficeCompletionSupport:
    """Build deterministic certification-support records for ANALYST-RM-002."""

    remediation_order_coverage = (
        "ANALYST-RM-002-001",
        "ANALYST-RM-002-002",
        "ANALYST-RM-002-003",
        "ANALYST-RM-002-004",
        "ANALYST-RM-002-005",
    )

    advanced_order_coverage = (
        "ANALYST-RM-002-006",
        "ANALYST-RM-002-007",
        "ANALYST-RM-002-008",
        "ANALYST-RM-002-009",
        "ANALYST-RM-002-010",
    )

    final_order_coverage = (
        "ANALYST-RM-002-011",
        "ANALYST-RM-002-012",
        "ANALYST-RM-002-013",
        "ANALYST-RM-002-014",
        "ANALYST-RM-002-015",
    )

    def build_package(
        self,
        *,
        observed_lifecycle: tuple[str, ...] | None = None,
    ) -> AnalystRm002CompletionEvidencePackage:
        objects = self.evaluate_canonical_object_completion()
        inputs = self.evaluate_input_completion()
        outputs = self.evaluate_output_completion()
        lifecycle = self.evaluate_lifecycle_completion(
            observed_transition_sequence=observed_lifecycle
            or (
                "Created",
                "Initialized",
                "Under Validation",
                "Validated",
                "Active",
                "Revised",
                "Superseded",
                "Archived",
                "Terminal",
            )
        )
        reasoning = self.evaluate_reasoning_architecture_completion()
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (objects, inputs, outputs, lifecycle, reasoning)
        ) else EnterpriseCertificationDecision.FAIL
        package = AnalystRm002CompletionEvidencePackage(
            package_identifier=f"ANALYST-RM-002-PACKAGE-{_digest((objects, inputs, outputs, lifecycle, reasoning))[:12].upper()}",
            governing_doctrine="ANALYST-RM-002-001-TO-005/1.0.0",
            remediation_order_coverage=self.remediation_order_coverage,
            canonical_objects=objects,
            analytical_inputs=inputs,
            analytical_outputs=outputs,
            analytical_lifecycle=lifecycle,
            reasoning_architecture=reasoning,
            final_completion_readiness=final,
            immutable_audit_references=(
                objects.completion_identifier,
                inputs.completion_identifier,
                outputs.completion_identifier,
                lifecycle.completion_identifier,
                reasoning.completion_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_canonical_object_completion(
        self,
        *,
        undefined_objects: tuple[str, ...] = (),
        missing_attributes: tuple[str, ...] = (),
        ambiguous_ownership: tuple[str, ...] = (),
        relationship_violations: tuple[str, ...] = (),
        invariant_violations: tuple[str, ...] = (),
        replay_supported: bool = True,
        recovery_supported: bool = True,
    ) -> AnalystCanonicalObjectCompletionRecord:
        objects = MappingProxyType(
            {
                "AO-001 Analytical Mission": "complete constitutional analytical assignment",
                "AO-002 Analytical Plan": "deterministic execution strategy",
                "AO-003 Analytical Evidence Package": "immutable admissible evidence collection",
                "AO-004 Analytical Reasoning Graph": "evidence-to-conclusion reasoning structure",
                "AO-005 Analytical Hypothesis": "one admissible explanation of evidence",
                "AO-006 Competing Hypothesis Set": "complete competing explanation set",
                "AO-007 Confidence Assessment": "deterministic constitutional confidence",
                "AO-008 Analytical Conclusion": "final analytical determination",
                "AO-009 Validation Record": "immutable validation evidence",
                "AO-010 Analytical Trace Record": "complete constitutional traceability",
                "AO-011 Analytical Metrics Record": "deterministic analytical measurements",
                "AO-012 Analytical Configuration Snapshot": "exact execution configuration",
            }
        )
        attributes = (
            "Constitutional Identifier",
            "Object Type",
            "Canonical Name",
            "Constitutional Owner",
            "Schema Version",
            "Object Version",
            "Lifecycle State",
            "Creation Authority",
            "Creation Timestamp",
            "Validation Status",
            "Integrity Status",
            "Provenance References",
            "Relationship References",
            "Certification Metadata",
        )
        chain = tuple(objects)
        invariants = ("Identity", "Ownership", "Integrity", "Provenance", "Validation", "Traceability", "Determinism", "Replay", "Recovery", "Auditability")
        missing = tuple(attribute for attribute in attributes if attribute in missing_attributes)
        passed = (
            not undefined_objects
            and not missing
            and not ambiguous_ownership
            and not relationship_violations
            and not invariant_violations
            and replay_supported
            and recovery_supported
        )
        record = AnalystCanonicalObjectCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-001-OBJ-{_digest(objects)[:12].upper()}",
            canonical_objects=objects,
            required_attributes=attributes,
            immutable_relationship_chain=chain,
            object_invariants=invariants,
            undefined_objects=undefined_objects,
            missing_attributes=missing,
            ambiguous_ownership=ambiguous_ownership,
            relationship_violations=relationship_violations,
            invariant_violations=invariant_violations,
            replay_supported=replay_supported,
            recovery_supported=recovery_supported,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_input_completion(
        self,
        *,
        unauthorized_inputs: tuple[str, ...] = (),
        missing_contract_fields: tuple[str, ...] = (),
        ownership_transfer_violations: tuple[str, ...] = (),
        normalization_failures: tuple[str, ...] = (),
        validation_failures: tuple[str, ...] = (),
        circular_dependencies: tuple[str, ...] = (),
    ) -> AnalystInputCompletionRecord:
        input_classes = (
            "Analysis Mission",
            "Candidate Package",
            "Enterprise Context",
            "Supporting Evidence",
            "Configuration Snapshot",
            "Constitutional Rules",
            "Replay Inputs",
            "Recovery Inputs",
        )
        contract = (
            "input identifier",
            "object type",
            "originating office",
            "originating authority",
            "ownership status",
            "schema version",
            "admissibility status",
            "normalization status",
            "validation status",
            "freshness status",
            "constitutional lifecycle state",
        )
        validation = ("schema compliance", "ownership legitimacy", "identifier integrity", "provenance completeness", "constitutional admissibility", "version compatibility", "integrity verification", "normalization completion")
        freshness = ("creation timestamp", "effective timestamp", "expiration criteria", "staleness evaluation", "supersession behavior", "replay freshness", "recovery freshness")
        dependencies = ("mandatory prerequisites", "optional supporting inputs", "mutually exclusive inputs", "dependency ordering", "dependency validation")
        missing = tuple(field for field in contract if field in missing_contract_fields)
        passed = (
            not unauthorized_inputs
            and not missing
            and not ownership_transfer_violations
            and not normalization_failures
            and not validation_failures
            and not circular_dependencies
        )
        record = AnalystInputCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-002-IN-{_digest((input_classes, contract))[:12].upper()}",
            input_classes=input_classes,
            contract_fields=contract,
            validation_requirements=validation,
            freshness_fields=freshness,
            dependency_requirements=dependencies,
            unauthorized_inputs=unauthorized_inputs,
            missing_contract_fields=missing,
            ownership_transfer_violations=ownership_transfer_violations,
            normalization_failures=normalization_failures,
            validation_failures=validation_failures,
            circular_dependencies=circular_dependencies,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_output_completion(
        self,
        *,
        unauthorized_outputs: tuple[str, ...] = (),
        missing_identity_fields: tuple[str, ...] = (),
        unmet_completion_requirements: tuple[str, ...] = (),
        validation_failures: tuple[str, ...] = (),
        duplicate_publication_findings: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_integrity_findings: tuple[str, ...] = (),
    ) -> AnalystOutputCompletionRecord:
        outputs = (
            "Analysis Package",
            "Analytical Conclusion",
            "Decision Recommendation",
            "Confidence Assessment",
            "Hypothesis Evaluation",
            "Competing Hypothesis Report",
            "Evidence Assessment Package",
            "Reasoning Trace Package",
            "Validation Report",
            "Analytical Metrics",
            "Constitutional Audit Evidence",
            "Certification Evidence",
            "Replay Artifact",
            "Recovery Artifact",
        )
        identity = ("canonical identifier", "output class", "constitutional owner", "version identifier", "schema version", "creation timestamp", "integrity metadata")
        completion = ("evidence validation", "reasoning completion", "contradiction resolution", "confidence determination", "schema validation", "integrity verification", "persistence", "audit recording")
        publication = ("exactly-once constitutional publication", "deterministic recipient identification", "immutable payload", "delivery audit evidence", "replay compatibility")
        missing = tuple(field for field in identity if field in missing_identity_fields)
        unmet = tuple(requirement for requirement in completion if requirement in unmet_completion_requirements)
        passed = (
            not unauthorized_outputs
            and not missing
            and not unmet
            and not validation_failures
            and not duplicate_publication_findings
            and not replay_divergence_findings
            and not recovery_integrity_findings
        )
        record = AnalystOutputCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-003-OUT-{_digest(outputs)[:12].upper()}",
            output_classes=outputs,
            identity_fields=identity,
            completion_requirements=completion,
            publication_requirements=publication,
            unauthorized_outputs=unauthorized_outputs,
            missing_identity_fields=missing,
            unmet_completion_requirements=unmet,
            validation_failures=validation_failures,
            duplicate_publication_findings=duplicate_publication_findings,
            replay_divergence_findings=replay_divergence_findings,
            recovery_integrity_findings=recovery_integrity_findings,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_lifecycle_completion(
        self,
        *,
        observed_transition_sequence: tuple[str, ...],
        revision_violations: tuple[str, ...] = (),
        archival_violations: tuple[str, ...] = (),
        replay_lifecycle_violations: tuple[str, ...] = (),
        recovery_lifecycle_violations: tuple[str, ...] = (),
    ) -> AnalystLifecycleCompletionRecord:
        states = ("Created", "Initialized", "Under Validation", "Validated", "Active", "Revised", "Superseded", "Archived", "Restored", "Terminal")
        legal = ("Created", "Initialized", "Under Validation", "Validated", "Active", "Revised", "Superseded", "Archived", "Terminal")
        restoration = ("Archived", "Restored", "Archived")
        legal_edges = set(zip(legal, legal[1:])) | set(zip(restoration, restoration[1:]))
        prohibited = ("Created->Active", "Initialized->Active", "Under Validation->Active", "Active->Created", "Archived->Revised", "Terminal->Active", "Superseded->Active", "Terminal->Restored")
        illegal = tuple(f"{left}->{right}" for left, right in zip(observed_transition_sequence, observed_transition_sequence[1:]) if (left, right) not in legal_edges)
        required_for_terminal = tuple(state for state in legal if state not in observed_transition_sequence and observed_transition_sequence[-1:] == ("Terminal",))
        passed = (
            bool(observed_transition_sequence)
            and not illegal
            and not required_for_terminal
            and not revision_violations
            and not archival_violations
            and not replay_lifecycle_violations
            and not recovery_lifecycle_violations
            and observed_transition_sequence[-1] in {"Archived", "Terminal"}
        )
        record = AnalystLifecycleCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-004-LIFE-{_digest(observed_transition_sequence)[:12].upper()}",
            lifecycle_states=states,
            legal_transition_sequence=legal,
            restoration_transition_sequence=restoration,
            prohibited_transitions=prohibited,
            observed_transition_sequence=observed_transition_sequence,
            illegal_transitions=illegal,
            missing_states=required_for_terminal,
            revision_violations=revision_violations,
            archival_violations=archival_violations,
            replay_lifecycle_violations=replay_lifecycle_violations,
            recovery_lifecycle_violations=recovery_lifecycle_violations,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_reasoning_architecture_completion(
        self,
        *,
        observed_stages: tuple[str, ...] | None = None,
        undocumented_assumptions: tuple[str, ...] = (),
        hidden_inferences: tuple[str, ...] = (),
        circular_dependencies: tuple[str, ...] = (),
        contradiction_suppression_findings: tuple[str, ...] = (),
        replay_reasoning_violations: tuple[str, ...] = (),
        recovery_reasoning_violations: tuple[str, ...] = (),
        fail_closed_on_incomplete_reasoning: bool = True,
    ) -> AnalystReasoningArchitectureCompletionRecord:
        stages = (
            "Evidence Acquisition",
            "Evidence Classification",
            "Evidence Evaluation",
            "Inference Construction",
            "Dependency Resolution",
            "Contradiction Evaluation",
            "Alternative Reasoning",
            "Analytical Synthesis",
            "Recommendation Derivation",
            "Reasoning Validation",
        )
        observed = observed_stages or stages
        missing = tuple(stage for stage in stages if stage not in observed)
        inference_fields = ("inference identifier", "inference type", "parent evidence identifiers", "supporting assumptions", "dependency references", "analytical rationale", "confidence inputs", "contradiction references", "generated findings", "validation status", "provenance references")
        dependency_fields = ("source object", "dependent object", "dependency type", "dependency strength", "ordering requirements", "completion requirements")
        persistent_state = ("inference graph", "dependency graph", "assumption registry", "contradiction registry", "reasoning history", "validation status", "analytical findings", "recommendation lineage")
        passed = (
            not missing
            and not undocumented_assumptions
            and not hidden_inferences
            and not circular_dependencies
            and not contradiction_suppression_findings
            and not replay_reasoning_violations
            and not recovery_reasoning_violations
            and fail_closed_on_incomplete_reasoning
        )
        record = AnalystReasoningArchitectureCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-005-REASON-{_digest(stages)[:12].upper()}",
            reasoning_stages=stages,
            inference_fields=inference_fields,
            dependency_fields=dependency_fields,
            persistent_reasoning_state=persistent_state,
            missing_stages=missing,
            undocumented_assumptions=undocumented_assumptions,
            hidden_inferences=hidden_inferences,
            circular_dependencies=circular_dependencies,
            contradiction_suppression_findings=contradiction_suppression_findings,
            replay_reasoning_violations=replay_reasoning_violations,
            recovery_reasoning_violations=recovery_reasoning_violations,
            fail_closed_on_incomplete_reasoning=fail_closed_on_incomplete_reasoning,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_advanced_completion_package(self) -> AnalystRm002AdvancedCompletionEvidencePackage:
        confidence = self.evaluate_confidence_probability_completion()
        hypotheses = self.evaluate_competing_hypothesis_completion()
        decisions = self.evaluate_deterministic_decision_completion()
        validation = self.evaluate_validation_completion()
        persistence = self.evaluate_persistence_completion()
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (confidence, hypotheses, decisions, validation, persistence)
        ) else EnterpriseCertificationDecision.FAIL
        package = AnalystRm002AdvancedCompletionEvidencePackage(
            package_identifier=f"ANALYST-RM-002-ADV-{_digest((confidence, hypotheses, decisions, validation, persistence))[:12].upper()}",
            governing_doctrine="ANALYST-RM-002-006-TO-010/1.0.0",
            remediation_order_coverage=self.advanced_order_coverage,
            confidence_probability=confidence,
            competing_hypotheses=hypotheses,
            deterministic_decisions=decisions,
            validation_completion=validation,
            persistence_completion=persistence,
            final_advanced_completion_readiness=final,
            immutable_audit_references=(
                confidence.completion_identifier,
                hypotheses.completion_identifier,
                decisions.completion_identifier,
                validation.completion_identifier,
                persistence.completion_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_confidence_probability_completion(
        self,
        *,
        missing_object_fields: tuple[str, ...] = (),
        inadmissible_inputs: tuple[str, ...] = (),
        uncertainty_gaps: tuple[str, ...] = (),
        implicit_inheritance_findings: tuple[str, ...] = (),
        contradiction_suppression_findings: tuple[str, ...] = (),
        replay_drift_findings: tuple[str, ...] = (),
        recovery_recompute_findings: tuple[str, ...] = (),
    ) -> AnalystConfidenceProbabilityCompletionRecord:
        fields_required = (
            "Confidence Identifier",
            "Associated Conclusion",
            "Supported Hypothesis",
            "Evidence References",
            "Reasoning References",
            "Confidence Representation",
            "Uncertainty Representation",
            "Confidence Contributors",
            "Confidence Inheritance",
            "Validation Status",
            "Version",
            "Provenance",
            "Certification Metadata",
        )
        inputs = ("validated evidence", "validated reasoning", "competing hypotheses", "contradiction analysis", "analytical completeness", "validation outcomes", "provenance integrity")
        lifecycle = ("Proposed", "Draft", "Under Evaluation", "Validated", "Approved", "Published", "Superseded", "Archived")
        registries = ("Confidence Registry", "Probability Representation Registry", "Uncertainty Registry", "Confidence Version Registry", "Confidence Validation Registry", "Confidence Traceability Registry")
        missing = tuple(field for field in fields_required if field in missing_object_fields)
        passed = (
            not missing
            and not inadmissible_inputs
            and not uncertainty_gaps
            and not implicit_inheritance_findings
            and not contradiction_suppression_findings
            and not replay_drift_findings
            and not recovery_recompute_findings
        )
        record = AnalystConfidenceProbabilityCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-006-CONF-{_digest((fields_required, inputs))[:12].upper()}",
            confidence_object_fields=fields_required,
            admissible_confidence_inputs=inputs,
            lifecycle_states=lifecycle,
            required_registries=registries,
            missing_object_fields=missing,
            inadmissible_inputs=inadmissible_inputs,
            uncertainty_gaps=uncertainty_gaps,
            implicit_inheritance_findings=implicit_inheritance_findings,
            contradiction_suppression_findings=contradiction_suppression_findings,
            replay_drift_findings=replay_drift_findings,
            recovery_recompute_findings=recovery_recompute_findings,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_competing_hypothesis_completion(
        self,
        *,
        unsupported_hypotheses: tuple[str, ...] = (),
        duplicate_hypotheses: tuple[str, ...] = (),
        missing_contradiction_records: tuple[str, ...] = (),
        nondeterministic_order_findings: tuple[str, ...] = (),
        suppressed_non_selected_hypotheses: tuple[str, ...] = (),
        lifecycle_violations: tuple[str, ...] = (),
    ) -> AnalystCompetingHypothesisCompletionRecord:
        identity = (
            "Hypothesis Identifier",
            "Analysis Mission Identifier",
            "Parent Analytical Context",
            "Supporting Evidence References",
            "Contradicting Evidence References",
            "Assumptions",
            "Confidence Assessment",
            "Evaluation Status",
            "Lifecycle State",
            "Version Identifier",
        )
        relationships = ("Independent Hypothesis", "Competing Hypothesis", "Complementary Hypothesis", "Derived Hypothesis", "Refined Hypothesis", "Superseding Hypothesis", "Mutually Exclusive Hypothesis")
        lifecycle = ("Proposed", "Accepted for Evaluation", "Evidence Collection", "Evaluation", "Confidence Assignment", "Comparison", "Selected", "Rejected", "Superseded", "Archived")
        criteria = ("evidence completeness", "evidence quality", "contradiction severity", "logical consistency", "constitutional admissibility", "dependency satisfaction", "validation status", "confidence determination")
        passed = (
            not unsupported_hypotheses
            and not duplicate_hypotheses
            and not missing_contradiction_records
            and not nondeterministic_order_findings
            and not suppressed_non_selected_hypotheses
            and not lifecycle_violations
        )
        record = AnalystCompetingHypothesisCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-007-HYP-{_digest((identity, relationships))[:12].upper()}",
            hypothesis_identity_fields=identity,
            relationship_types=relationships,
            lifecycle_states=lifecycle,
            evaluation_criteria=criteria,
            unsupported_hypotheses=unsupported_hypotheses,
            duplicate_hypotheses=duplicate_hypotheses,
            missing_contradiction_records=missing_contradiction_records,
            nondeterministic_order_findings=nondeterministic_order_findings,
            suppressed_non_selected_hypotheses=suppressed_non_selected_hypotheses,
            lifecycle_violations=lifecycle_violations,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_deterministic_decision_completion(
        self,
        *,
        missing_decision_classes: tuple[str, ...] = (),
        shared_authority_findings: tuple[str, ...] = (),
        undefined_inputs: tuple[str, ...] = (),
        circular_dependencies: tuple[str, ...] = (),
        default_approval_findings: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_history_findings: tuple[str, ...] = (),
    ) -> AnalystDeterministicDecisionCompletionRecord:
        decisions = (
            "Evidence Admissibility Decision",
            "Evidence Sufficiency Decision",
            "Analytical Completeness Decision",
            "Confidence Classification Decision",
            "Hypothesis Acceptance Decision",
            "Hypothesis Rejection Decision",
            "Contradiction Resolution Decision",
            "Competing Hypothesis Ranking",
            "Consensus Decision",
            "Conclusion Approval Decision",
            "Recommendation Authorization",
            "Validation Decision",
            "Publication Authorization",
            "Revision Authorization",
            "Certification Evidence Acceptance",
        )
        outputs = ("decision identifier", "decision class", "outcome", "reasoning references", "confidence", "supporting evidence", "audit metadata")
        dependencies = ("deterministic dependency order", "incomplete dependencies prohibit execution", "dependency cycles prohibited", "conflicts preserve contradictory evidence")
        missing = tuple(decision for decision in decisions if decision in missing_decision_classes)
        passed = (
            not missing
            and not shared_authority_findings
            and not undefined_inputs
            and not circular_dependencies
            and not default_approval_findings
            and not replay_divergence_findings
            and not recovery_history_findings
        )
        record = AnalystDeterministicDecisionCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-008-DEC-{_digest(decisions)[:12].upper()}",
            decision_classes=decisions,
            required_outputs=outputs,
            dependency_rules=dependencies,
            missing_decision_classes=missing,
            shared_authority_findings=shared_authority_findings,
            undefined_inputs=undefined_inputs,
            circular_dependencies=circular_dependencies,
            default_approval_findings=default_approval_findings,
            replay_divergence_findings=replay_divergence_findings,
            recovery_history_findings=recovery_history_findings,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_validation_completion(
        self,
        *,
        observed_sequence: tuple[str, ...] | None = None,
        bypass_findings: tuple[str, ...] = (),
        invalid_outcomes: tuple[str, ...] = (),
        evidence_gaps: tuple[str, ...] = (),
        replay_validation_gaps: tuple[str, ...] = (),
        recovery_validation_gaps: tuple[str, ...] = (),
    ) -> AnalystValidationCompletionRecord:
        lifecycle = ("Validation Request", "Input Verification", "Schema Validation", "Identity Validation", "Ownership Validation", "Integrity Validation", "Semantic Validation", "Dependency Validation", "Invariant Validation", "Certification Validation", "Validation Decision", "Validation Audit Recording")
        classes = ("Structural Validation", "Identity Validation", "Ownership Validation", "Evidence Validation", "Reasoning Validation", "Confidence Validation", "Hypothesis Validation", "Configuration Validation", "Lifecycle Validation", "Output Validation")
        sequence = ("Structure", "Identity", "Ownership", "Evidence", "Reasoning", "Confidence", "Hypotheses", "Configuration", "Lifecycle", "Output", "Certification")
        observed = observed_sequence or sequence
        outcomes = ("Pass", "Conditional Pass", "Reject", "Deferred", "Invalid")
        missing = tuple(stage for stage in sequence if stage not in observed)
        index = {stage: position for position, stage in enumerate(sequence)}
        ordering = tuple(f"{left}->{right}" for left, right in zip(observed, observed[1:]) if left in index and right in index and index[left] > index[right])
        invalid = tuple(outcome for outcome in invalid_outcomes if outcome not in outcomes)
        passed = (
            not missing
            and not ordering
            and not bypass_findings
            and not invalid
            and not evidence_gaps
            and not replay_validation_gaps
            and not recovery_validation_gaps
        )
        record = AnalystValidationCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-009-VAL-{_digest((lifecycle, sequence))[:12].upper()}",
            validation_lifecycle=lifecycle,
            validation_classes=classes,
            validation_sequence=sequence,
            validation_outcomes=outcomes,
            missing_stages=missing,
            ordering_violations=ordering,
            bypass_findings=bypass_findings,
            invalid_outcomes=invalid,
            evidence_gaps=evidence_gaps,
            replay_validation_gaps=replay_validation_gaps,
            recovery_validation_gaps=recovery_validation_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_persistence_completion(
        self,
        *,
        missing_persistent_state: tuple[str, ...] = (),
        transient_state_violations: tuple[str, ...] = (),
        lifecycle_bypass_findings: tuple[str, ...] = (),
        partial_commit_findings: tuple[str, ...] = (),
        durability_failures: tuple[str, ...] = (),
        integrity_failures: tuple[str, ...] = (),
        replay_regeneration_findings: tuple[str, ...] = (),
        recovery_mutation_findings: tuple[str, ...] = (),
    ) -> AnalystPersistenceCompletionRecord:
        persistent = ("Mission State", "Evidence State", "Reasoning State", "Confidence State", "Recommendation State", "Validation State", "Lifecycle State", "Audit State", "Configuration State")
        transient = ("runtime caches", "temporary indexes", "scheduling queues", "execution buffers", "memory optimizations", "thread-local execution state", "implementation-specific optimization structures")
        lifecycle = ("Created", "Validated", "Prepared", "Committed", "Verified", "Immutable", "Archived", "Certified")
        commit_fields = ("object identity", "object revision", "lifecycle state", "dependency references", "validation results", "configuration version", "constitutional version", "timestamp", "integrity verification")
        missing = tuple(state for state in persistent if state in missing_persistent_state)
        passed = (
            not missing
            and not transient_state_violations
            and not lifecycle_bypass_findings
            and not partial_commit_findings
            and not durability_failures
            and not integrity_failures
            and not replay_regeneration_findings
            and not recovery_mutation_findings
        )
        record = AnalystPersistenceCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-010-PERSIST-{_digest((persistent, lifecycle))[:12].upper()}",
            persistent_state_classes=persistent,
            transient_state_classes=transient,
            persistence_lifecycle=lifecycle,
            commit_fields=commit_fields,
            missing_persistent_state=missing,
            transient_state_violations=transient_state_violations,
            lifecycle_bypass_findings=lifecycle_bypass_findings,
            partial_commit_findings=partial_commit_findings,
            durability_failures=durability_failures,
            integrity_failures=integrity_failures,
            replay_regeneration_findings=replay_regeneration_findings,
            recovery_mutation_findings=recovery_mutation_findings,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def build_final_completion_package(self) -> AnalystRm002FinalCompletionEvidencePackage:
        replay = self.evaluate_replay_completion()
        recovery = self.evaluate_recovery_completion()
        configuration = self.evaluate_configuration_completion()
        traceability = self.evaluate_traceability_completion()
        review = self.evaluate_independent_completion_review(
            completed_work_orders=self.remediation_order_coverage
            + self.advanced_order_coverage
            + self.final_order_coverage
        )
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (replay, recovery, configuration, traceability, review)
        ) else EnterpriseCertificationDecision.FAIL
        package = AnalystRm002FinalCompletionEvidencePackage(
            package_identifier=f"ANALYST-RM-002-FINAL-{_digest((replay, recovery, configuration, traceability, review))[:12].upper()}",
            governing_doctrine="ANALYST-RM-002-011-TO-015/1.0.0",
            remediation_order_coverage=self.final_order_coverage,
            replay_completion=replay,
            recovery_completion=recovery,
            configuration_completion=configuration,
            traceability_completion=traceability,
            independent_completion_review=review,
            final_rm002_completion_readiness=final,
            immutable_audit_references=(
                replay.completion_identifier,
                recovery.completion_identifier,
                configuration.completion_identifier,
                traceability.completion_identifier,
                review.completion_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_replay_completion(
        self,
        *,
        missing_scope: tuple[str, ...] = (),
        current_state_substitutions: tuple[str, ...] = (),
        prohibited_difference_findings: tuple[str, ...] = (),
        validation_gaps: tuple[str, ...] = (),
        history_mutation_findings: tuple[str, ...] = (),
    ) -> AnalystReplayCompletionRecord:
        scope = ("Analytical Mission", "Analytical Plan", "Evidence Package", "Reasoning Graph", "Hypotheses", "Confidence Assessment", "Analytical Conclusion", "Validation Records", "Configuration Snapshot", "Provenance", "Metrics")
        inputs = ("evidence", "configuration", "constitutional rules", "schemas", "registries", "object versions", "analytical parameters")
        comparison = ("analytical conclusions", "confidence assessments", "evidence utilization", "reasoning structure", "competing hypotheses", "validation outcomes", "provenance", "object relationships")
        admissible = ("execution duration", "processor allocation", "memory layout", "storage location", "internal optimization", "scheduling", "thread execution", "resource utilization")
        prohibited = ("analytical conclusions", "evidence admissibility", "confidence values", "hypothesis ranking", "validation outcomes", "ownership", "provenance", "object identity", "lifecycle transitions", "constitutional decisions")
        failures = ("Input inconsistency", "Configuration inconsistency", "Reasoning inconsistency", "Validation inconsistency", "Conclusion inconsistency", "Provenance inconsistency", "Lifecycle inconsistency", "Constitutional invariant violation")
        missing = tuple(item for item in scope if item in missing_scope)
        passed = not missing and not current_state_substitutions and not prohibited_difference_findings and not validation_gaps and not history_mutation_findings
        record = AnalystReplayCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-011-REPLAY-{_digest(scope)[:12].upper()}",
            replay_scope=scope,
            historical_inputs=inputs,
            semantic_comparison_fields=comparison,
            admissible_runtime_differences=admissible,
            prohibited_differences=prohibited,
            failure_classes=failures,
            missing_scope=missing,
            current_state_substitutions=current_state_substitutions,
            prohibited_difference_findings=prohibited_difference_findings,
            validation_gaps=validation_gaps,
            history_mutation_findings=history_mutation_findings,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_recovery_completion(
        self,
        *,
        missing_recovery_state: tuple[str, ...] = (),
        arbitrary_checkpoint_findings: tuple[str, ...] = (),
        partial_restore_findings: tuple[str, ...] = (),
        idempotency_violations: tuple[str, ...] = (),
        invariant_violations: tuple[str, ...] = (),
        fail_closed: bool = True,
    ) -> AnalystRecoveryCompletionRecord:
        scope = ("Analysis Missions", "Analytical Packages", "Analytical Context", "Evidence Sets", "Reasoning Models", "Hypothesis Sets", "Validation Results", "Confidence Determinations", "Decision Records", "Configuration Snapshots", "Trace Records", "Persistent State", "Execution State")
        checkpoints = ("Mission Acceptance Checkpoint", "Input Validation Checkpoint", "Evidence Completion Checkpoint", "Reasoning Completion Checkpoint", "Hypothesis Evaluation Checkpoint", "Confidence Assignment Checkpoint", "Decision Completion Checkpoint", "Output Preparation Checkpoint", "Output Publication Checkpoint")
        fields_required = ("execution identifier", "checkpoint identifier", "lifecycle state", "mission identity", "configuration version", "reasoning state", "validation state", "hypothesis state", "decision state", "traceability references", "persistent object references")
        sequence = ("Detect interruption", "Verify checkpoint integrity", "Restore checkpoint state", "Validate restored state", "Verify constitutional invariants", "Resume execution", "Record immutable recovery evidence")
        missing = tuple(item for item in scope if item in missing_recovery_state)
        passed = not missing and not arbitrary_checkpoint_findings and not partial_restore_findings and not idempotency_violations and not invariant_violations and fail_closed
        record = AnalystRecoveryCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-012-RECOVERY-{_digest((scope, checkpoints))[:12].upper()}",
            recovery_scope=scope,
            recovery_checkpoints=checkpoints,
            checkpoint_fields=fields_required,
            recovery_sequence=sequence,
            missing_recovery_state=missing,
            arbitrary_checkpoint_findings=arbitrary_checkpoint_findings,
            partial_restore_findings=partial_restore_findings,
            idempotency_violations=idempotency_violations,
            invariant_violations=invariant_violations,
            fail_closed=fail_closed,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_configuration_completion(
        self,
        *,
        missing_configuration_classes: tuple[str, ...] = (),
        ownership_violations: tuple[str, ...] = (),
        hidden_configuration_findings: tuple[str, ...] = (),
        implicit_default_findings: tuple[str, ...] = (),
        compatibility_gaps: tuple[str, ...] = (),
        integrity_failures: tuple[str, ...] = (),
        replay_substitution_findings: tuple[str, ...] = (),
        recovery_drift_findings: tuple[str, ...] = (),
    ) -> AnalystConfigurationCompletionRecord:
        classes = ("Analytical Model Configuration", "Evidence Evaluation Configuration", "Confidence Configuration", "Hypothesis Evaluation Configuration", "Decision Threshold Configuration", "Validation Configuration", "Normalization Configuration", "Replay Configuration", "Recovery Configuration", "Persistence Configuration", "Audit Configuration", "Metrics Configuration", "Registry Configuration", "Version Compatibility Configuration", "Certification Configuration")
        identity = ("configuration identifier", "configuration class", "constitutional owner", "schema version", "configuration version", "integrity metadata", "effective version metadata")
        compatibility = ("schema versions", "analytical models", "replay environments", "recovery checkpoints", "certification environments")
        missing = tuple(item for item in classes if item in missing_configuration_classes)
        passed = not missing and not ownership_violations and not hidden_configuration_findings and not implicit_default_findings and not compatibility_gaps and not integrity_failures and not replay_substitution_findings and not recovery_drift_findings
        record = AnalystConfigurationCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-013-CONFIG-{_digest(classes)[:12].upper()}",
            configuration_classes=classes,
            identity_fields=identity,
            compatibility_targets=compatibility,
            missing_configuration_classes=missing,
            ownership_violations=ownership_violations,
            hidden_configuration_findings=hidden_configuration_findings,
            implicit_default_findings=implicit_default_findings,
            compatibility_gaps=compatibility_gaps,
            integrity_failures=integrity_failures,
            replay_substitution_findings=replay_substitution_findings,
            recovery_drift_findings=recovery_drift_findings,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_traceability_completion(
        self,
        *,
        orphaned_artifacts: tuple[str, ...] = (),
        implicit_lineage_findings: tuple[str, ...] = (),
        undefined_relationships: tuple[str, ...] = (),
        broken_lineage_findings: tuple[str, ...] = (),
        replay_trace_gaps: tuple[str, ...] = (),
        recovery_trace_gaps: tuple[str, ...] = (),
        certification_trace_gaps: tuple[str, ...] = (),
    ) -> AnalystTraceabilityCompletionRecord:
        artifacts = ("Analytical Missions", "Analytical Plans", "Analytical Packages", "Evidence Packages", "Evidence Items", "Reasoning Graphs", "Confidence Assessments", "Competing Hypotheses", "Contradiction Records", "Consensus Records", "Decision Objects", "Analytical Outputs", "Validation Records", "Lifecycle Records", "Replay Records", "Recovery Records", "Audit Records", "Certification Evidence")
        chain = ("Mission Authorization", "Analytical Mission", "Analytical Plan", "Input Acquisition", "Evidence Normalization", "Evidence Validation", "Reasoning Construction", "Hypothesis Evaluation", "Confidence Determination", "Contradiction Resolution", "Consensus Formation", "Decision Generation", "Output Construction", "Output Validation", "Delivery Eligibility", "Audit Record", "Certification Evidence")
        relationships = ("Created From", "Derived From", "Validated By", "Supported By", "Contradicted By", "Supersedes", "Superseded By", "Depends Upon", "Produced By", "Delivered By", "Certified By", "Audited By", "Replayed From", "Recovered From")
        identity = ("Trace Identifier", "Parent Identifier", "Child Identifier", "Relationship Type", "Relationship Authority", "Creation Timestamp", "Schema Version", "Validation State")
        undefined = tuple(item for item in undefined_relationships if item not in relationships)
        passed = not orphaned_artifacts and not implicit_lineage_findings and not undefined and not broken_lineage_findings and not replay_trace_gaps and not recovery_trace_gaps and not certification_trace_gaps
        record = AnalystTraceabilityCompletionRecord(
            completion_identifier=f"ANALYST-RM-002-014-TRACE-{_digest((artifacts, chain))[:12].upper()}",
            artifact_scope=artifacts,
            canonical_chain=chain,
            relationship_types=relationships,
            trace_identity_fields=identity,
            orphaned_artifacts=orphaned_artifacts,
            implicit_lineage_findings=implicit_lineage_findings,
            undefined_relationships=undefined,
            broken_lineage_findings=broken_lineage_findings,
            replay_trace_gaps=replay_trace_gaps,
            recovery_trace_gaps=recovery_trace_gaps,
            certification_trace_gaps=certification_trace_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_independent_completion_review(
        self,
        *,
        completed_work_orders: tuple[str, ...],
        constitutional_inconsistencies: tuple[str, ...] = (),
        implementation_discretion_findings: tuple[str, ...] = (),
        missing_certification_evidence: tuple[str, ...] = (),
        missing_audit_evidence: tuple[str, ...] = (),
    ) -> AnalystIndependentCompletionReviewRecord:
        required = self.remediation_order_coverage + self.advanced_order_coverage + self.final_order_coverage
        domains = ("analytical objects", "analytical inputs", "analytical outputs", "lifecycle behavior", "reasoning architecture", "confidence architecture", "competing hypotheses", "deterministic decisions", "validation", "persistence", "replay", "recovery", "configuration governance", "traceability", "constitutional invariants")
        missing = tuple(order for order in required if order not in completed_work_orders)
        passed = not missing and not constitutional_inconsistencies and not implementation_discretion_findings and not missing_certification_evidence and not missing_audit_evidence
        record = AnalystIndependentCompletionReviewRecord(
            completion_identifier=f"ANALYST-RM-002-015-REVIEW-{_digest((required, completed_work_orders))[:12].upper()}",
            required_work_orders=required,
            completed_work_orders=completed_work_orders,
            review_domains=domains,
            missing_work_orders=missing,
            constitutional_inconsistencies=constitutional_inconsistencies,
            implementation_discretion_findings=implementation_discretion_findings,
            missing_certification_evidence=missing_certification_evidence,
            missing_audit_evidence=missing_audit_evidence,
            progression_authorized=passed,
            completion_outcome="COMPLETE" if passed else "INCOMPLETE",
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
