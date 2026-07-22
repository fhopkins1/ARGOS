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


class AnalystOfficeCompletionSupport:
    """Build deterministic certification-support records for ANALYST-RM-002."""

    remediation_order_coverage = (
        "ANALYST-RM-002-001",
        "ANALYST-RM-002-002",
        "ANALYST-RM-002-003",
        "ANALYST-RM-002-004",
        "ANALYST-RM-002-005",
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
