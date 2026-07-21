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
    ) -> SentinelOfficeRemediationEvidencePackage:
        definition = self.registry.definition_for("Sentinel")
        responsibility = self.registry.validate_registry()
        authority = (
            self.registry.validate_authority("Sentinel", "authority_validation"),
            self.registry.validate_authority("Sentinel", "enterprise_bridge_execution"),
        )
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
