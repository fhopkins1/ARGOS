"""INF-MO-001 through INF-MO-006 infrastructure remediation controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Iterable, Mapping


INF_MO_VERSION = "INF-MO-001-006/1.0.0"


class INFMOStatus(str, Enum):
    PASS = "PASS"
    FAIL_CLOSED = "FAIL_CLOSED"
    CONSTITUTIONAL_FREEZE = "CONSTITUTIONAL_FREEZE"


class INFMOFailure(str, Enum):
    MUTABLE_REPOSITORY = "mutable_repository"
    STAGED_OR_UNSTAGED_CHANGES = "staged_or_unstaged_changes"
    UNTRACKED_CONSTITUTIONAL_FILES = "untracked_constitutional_files"
    MISSING_SNAPSHOT = "missing_snapshot"
    MISSING_MANIFEST = "missing_manifest"
    MISSING_PROVENANCE = "missing_provenance"
    WORKSPACE_CONTAMINATION = "workspace_contamination"
    MIXED_CANDIDATE = "mixed_candidate"
    NON_REPRODUCIBLE_INPUTS = "non_reproducible_inputs"
    CANDIDATE_IDENTITY_AMBIGUITY = "candidate_identity_ambiguity"
    UNCERTIFIED_BRIDGE_ASSET = "uncertified_bridge_asset"
    UNAUTHORIZED_BRIDGE_PATH = "unauthorized_bridge_path"
    ORPHAN_INFRASTRUCTURE_COMPONENT = "orphan_infrastructure_component"
    SYNTHETIC_TRUTH_FINDING = "synthetic_truth_finding"
    FALLBACK_VALUE = "fallback_value"
    CACHE_AUTHORITY = "cache_authority"
    RECOVERY_RECONSTRUCTION = "recovery_reconstruction"
    MUTABLE_CHECKPOINT = "mutable_checkpoint"
    UNCERTIFIED_CHECKPOINT = "uncertified_checkpoint"
    REPLAY_CONTAMINATION = "replay_contamination"
    REPLAY_NONDETERMINISM = "replay_nondeterminism"
    AUTHORITY_MUTATION_DURING_RECOVERY = "authority_mutation_during_recovery"
    LEDGER_DISCONTINUITY = "ledger_discontinuity"
    SKIPPED_VERIFICATION = "skipped_verification"
    UNKNOWN_VERIFICATION = "unknown_verification"
    INCOMPLETE_COVERAGE = "incomplete_coverage"
    TIMEOUT_AMBIGUITY = "timeout_ambiguity"
    MISSING_TRACEABILITY = "missing_traceability"
    UNRESOLVED_CERTIFICATION_FINDING = "unresolved_certification_finding"
    MISSING_FREEZE_DECLARATION = "missing_freeze_declaration"
    MISSING_SENTINEL_AUTHORIZATION = "missing_sentinel_authorization"
    DENOMINATOR_MUTATION = "denominator_mutation"
    DUPLICATE_TEST = "duplicate_test"
    ORPHAN_TEST = "orphan_test"
    DISABLED_TEST = "disabled_test"
    NON_DETERMINISTIC_SCHEDULING = "non_deterministic_scheduling"
    ENDURANCE_FAILURE = "endurance_failure"
    REPEATABILITY_DIVERGENCE = "repeatability_divergence"
    MUTABLE_CERTIFICATION_RESULT = "mutable_certification_result"


@dataclass(frozen=True)
class ImmutableCandidateRecord:
    candidate_id: str
    repository_commit: str
    repository_tree: str
    dependency_fingerprint: str
    doctrine_fingerprint: str
    schema_fingerprint: str
    bridge_fingerprint: str
    runtime_fingerprint: str
    certification_timestamp: str
    candidate_sequence_id: str
    snapshot_fingerprint: str
    workspace_fingerprint: str
    manifest_fingerprint: str
    provenance_fingerprint: str
    repository_clean: bool
    staged_changes: bool
    unstaged_changes: bool
    untracked_constitutional_files: bool
    hermetic_workspace: bool
    evidence_candidate_ids: tuple[str, ...]
    reproducible_inputs: bool
    immutable: bool


@dataclass(frozen=True)
class CandidateCertificationDecision:
    status: INFMOStatus
    failures: tuple[INFMOFailure, ...]
    candidate_digest: str


class ImmutableCandidateInfrastructure:
    """INF-MO-001 candidate identity, locking, and evidence binding."""

    def certify(self, candidate: ImmutableCandidateRecord) -> CandidateCertificationDecision:
        failures: list[INFMOFailure] = []
        required = (
            candidate.candidate_id,
            candidate.repository_commit,
            candidate.repository_tree,
            candidate.snapshot_fingerprint,
            candidate.workspace_fingerprint,
            candidate.manifest_fingerprint,
            candidate.provenance_fingerprint,
        )
        if any(_blank(value) for value in required):
            failures.append(INFMOFailure.CANDIDATE_IDENTITY_AMBIGUITY)
        if not candidate.repository_clean or candidate.staged_changes or candidate.unstaged_changes:
            failures.append(INFMOFailure.STAGED_OR_UNSTAGED_CHANGES)
        if candidate.untracked_constitutional_files:
            failures.append(INFMOFailure.UNTRACKED_CONSTITUTIONAL_FILES)
        if _blank(candidate.snapshot_fingerprint):
            failures.append(INFMOFailure.MISSING_SNAPSHOT)
        if _blank(candidate.manifest_fingerprint):
            failures.append(INFMOFailure.MISSING_MANIFEST)
        if _blank(candidate.provenance_fingerprint):
            failures.append(INFMOFailure.MISSING_PROVENANCE)
        if not candidate.hermetic_workspace:
            failures.append(INFMOFailure.WORKSPACE_CONTAMINATION)
        if not candidate.evidence_candidate_ids or any(item != candidate.candidate_id for item in candidate.evidence_candidate_ids):
            failures.append(INFMOFailure.MIXED_CANDIDATE)
        if not candidate.reproducible_inputs:
            failures.append(INFMOFailure.NON_REPRODUCIBLE_INPUTS)
        if not candidate.immutable:
            failures.append(INFMOFailure.MUTABLE_REPOSITORY)
        unique = tuple(dict.fromkeys(failures))
        return CandidateCertificationDecision(
            status=INFMOStatus.PASS if not unique else INFMOStatus.FAIL_CLOSED,
            failures=unique,
            candidate_digest=_digest(asdict(candidate)),
        )


@dataclass(frozen=True)
class CanonicalBridgeAsset:
    bridge_id: str
    source_component: str
    destination_component: str
    bridge_owner: str
    authority_owner: str
    schema_version: str
    dependency_classification: str
    runtime_direction: str
    certification_state: str
    schema_certified: bool
    dependencies_certified: bool
    traversal_evidence: str
    unauthorized_path: bool = False
    orphan_component: bool = False
    shared_owner: bool = False


@dataclass(frozen=True)
class BridgeInfrastructureCertification:
    status: INFMOStatus
    failures: tuple[INFMOFailure, ...]
    certified_bridge_count: int


class CanonicalBridgeInfrastructureCertification:
    """INF-MO-002 complete bridge inventory, ownership, schema, and traversal certification."""

    def certify(self, bridge_assets: Iterable[CanonicalBridgeAsset], runtime_components: Iterable[str]) -> BridgeInfrastructureCertification:
        bridges = tuple(bridge_assets)
        components = set(runtime_components)
        failures: list[INFMOFailure] = []
        bridge_ids = [bridge.bridge_id for bridge in bridges]
        if len(set(bridge_ids)) != len(bridge_ids):
            failures.append(INFMOFailure.UNCERTIFIED_BRIDGE_ASSET)
        for bridge in bridges:
            if (
                _blank(bridge.bridge_id)
                or _blank(bridge.bridge_owner)
                or bridge.shared_owner
                or bridge.certification_state != "CERTIFIED"
                or not bridge.schema_certified
                or not bridge.dependencies_certified
                or _blank(bridge.traversal_evidence)
            ):
                failures.append(INFMOFailure.UNCERTIFIED_BRIDGE_ASSET)
            if bridge.unauthorized_path:
                failures.append(INFMOFailure.UNAUTHORIZED_BRIDGE_PATH)
            if bridge.orphan_component or bridge.source_component not in components or bridge.destination_component not in components:
                failures.append(INFMOFailure.ORPHAN_INFRASTRUCTURE_COMPONENT)
        connected = {item for bridge in bridges for item in (bridge.source_component, bridge.destination_component)}
        if components - connected:
            failures.append(INFMOFailure.ORPHAN_INFRASTRUCTURE_COMPONENT)
        unique = tuple(dict.fromkeys(failures))
        return BridgeInfrastructureCertification(INFMOStatus.PASS if not unique else INFMOStatus.FAIL_CLOSED, unique, len(bridges))


@dataclass(frozen=True)
class TruthFlowRecord:
    datum_id: str
    candidate_id: str
    source_id: str
    destination_id: str
    bridge_id: str
    authority_id: str
    source_hash: str
    transport_hash: str
    persistence_hash: str
    delivery_hash: str
    cache_fresh: bool
    cache_authoritative: bool
    fallback_used: bool
    synthetic_indicator: bool
    transformation_authorized: bool
    recovery_reconstructed: bool
    evidence_hash: str


@dataclass(frozen=True)
class SyntheticTruthCertification:
    status: INFMOStatus
    failures: tuple[INFMOFailure, ...]
    flow_count: int


class InfrastructureSyntheticTruthEliminator:
    """INF-MO-003 source-to-sink truth neutrality and fallback elimination."""

    def certify(self, flows: Iterable[TruthFlowRecord]) -> SyntheticTruthCertification:
        failures: list[INFMOFailure] = []
        flow_items = tuple(flows)
        for flow in flow_items:
            if any(_blank(value) for value in (flow.source_id, flow.destination_id, flow.bridge_id, flow.authority_id, flow.evidence_hash)):
                failures.append(INFMOFailure.SYNTHETIC_TRUTH_FINDING)
            if flow.source_hash != flow.transport_hash or flow.transport_hash != flow.persistence_hash or flow.persistence_hash != flow.delivery_hash:
                failures.append(INFMOFailure.SYNTHETIC_TRUTH_FINDING)
            if flow.fallback_used:
                failures.append(INFMOFailure.FALLBACK_VALUE)
            if flow.cache_authoritative or not flow.cache_fresh:
                failures.append(INFMOFailure.CACHE_AUTHORITY)
            if flow.synthetic_indicator or not flow.transformation_authorized:
                failures.append(INFMOFailure.SYNTHETIC_TRUTH_FINDING)
            if flow.recovery_reconstructed:
                failures.append(INFMOFailure.RECOVERY_RECONSTRUCTION)
        unique = tuple(dict.fromkeys(failures))
        return SyntheticTruthCertification(INFMOStatus.PASS if not unique else INFMOStatus.FAIL_CLOSED, unique, len(flow_items))


@dataclass(frozen=True)
class CheckpointCertificationRecord:
    checkpoint_id: str
    immutable: bool
    certified: bool
    integrity_verified: bool
    completeness_verified: bool
    schema_compatible: bool
    bridge_compatible: bool
    workflow_consistent: bool
    authority_consistent: bool
    candidate_id: str
    evidence_complete: bool


@dataclass(frozen=True)
class RecoveryReplayRecord:
    checkpoint: CheckpointCertificationRecord
    restored_objects: tuple[str, ...]
    required_objects: tuple[str, ...]
    authority_unchanged: bool
    ledger_continuous: bool
    replay_isolated: bool
    replay_hashes: tuple[str, ...]
    production_mutation_attempted: bool
    recovery_evidence: str
    replay_evidence: str


@dataclass(frozen=True)
class PersistenceReplayCertification:
    status: INFMOStatus
    failures: tuple[INFMOFailure, ...]


class InfrastructurePersistenceReplayCertifier:
    """INF-MO-004 checkpoint, restart, recovery, replay, authority, and ledger certification."""

    def certify(self, record: RecoveryReplayRecord) -> PersistenceReplayCertification:
        failures: list[INFMOFailure] = []
        checkpoint = record.checkpoint
        if not checkpoint.immutable:
            failures.append(INFMOFailure.MUTABLE_CHECKPOINT)
        if not all(
            (
                checkpoint.certified,
                checkpoint.integrity_verified,
                checkpoint.completeness_verified,
                checkpoint.schema_compatible,
                checkpoint.bridge_compatible,
                checkpoint.workflow_consistent,
                checkpoint.authority_consistent,
                checkpoint.evidence_complete,
            )
        ):
            failures.append(INFMOFailure.UNCERTIFIED_CHECKPOINT)
        if set(record.required_objects) - set(record.restored_objects):
            failures.append(INFMOFailure.RECOVERY_RECONSTRUCTION)
        if not record.authority_unchanged:
            failures.append(INFMOFailure.AUTHORITY_MUTATION_DURING_RECOVERY)
        if not record.ledger_continuous:
            failures.append(INFMOFailure.LEDGER_DISCONTINUITY)
        if not record.replay_isolated or record.production_mutation_attempted:
            failures.append(INFMOFailure.REPLAY_CONTAMINATION)
        if len(set(record.replay_hashes)) > 1 or not record.replay_hashes:
            failures.append(INFMOFailure.REPLAY_NONDETERMINISM)
        if _blank(record.recovery_evidence) or _blank(record.replay_evidence):
            failures.append(INFMOFailure.UNCERTIFIED_CHECKPOINT)
        unique = tuple(dict.fromkeys(failures))
        return PersistenceReplayCertification(INFMOStatus.PASS if not unique else INFMOStatus.FAIL_CLOSED, unique)


class VerificationOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class VerificationActivity:
    activity_id: str
    category: str
    outcome: VerificationOutcome
    deterministic: bool
    timeout_defined: bool
    evidence_hash: str
    traceability_refs: tuple[str, ...]


@dataclass(frozen=True)
class VerificationCompletionReport:
    status: INFMOStatus
    failures: tuple[INFMOFailure, ...]
    coverage: Mapping[str, int]
    operational_readiness: bool


class InfrastructureVerificationCompletionEngine:
    """INF-MO-005 complete denominator, execution, coverage, and readiness verification."""

    required_categories = (
        "unit",
        "integration",
        "bridge",
        "persistence",
        "replay",
        "startup",
        "shutdown",
        "recovery",
        "constitutional",
        "evidence",
        "workflow",
        "law_vii",
        "authority",
        "synthetic_truth",
        "health",
        "endurance",
        "restart",
        "stress",
        "failure",
    )

    def certify(self, activities: Iterable[VerificationActivity]) -> VerificationCompletionReport:
        items = tuple(activities)
        failures: list[INFMOFailure] = []
        categories = {item.category for item in items}
        if set(self.required_categories) - categories:
            failures.append(INFMOFailure.INCOMPLETE_COVERAGE)
        if any(item.outcome == VerificationOutcome.SKIPPED for item in items):
            failures.append(INFMOFailure.SKIPPED_VERIFICATION)
        if any(item.outcome in {VerificationOutcome.UNKNOWN, VerificationOutcome.BLOCKED} for item in items):
            failures.append(INFMOFailure.UNKNOWN_VERIFICATION)
        if any(item.outcome == VerificationOutcome.FAIL for item in items):
            failures.append(INFMOFailure.UNRESOLVED_CERTIFICATION_FINDING)
        if any(not item.deterministic for item in items):
            failures.append(INFMOFailure.UNKNOWN_VERIFICATION)
        if any(not item.timeout_defined for item in items):
            failures.append(INFMOFailure.TIMEOUT_AMBIGUITY)
        if any(_blank(item.evidence_hash) for item in items):
            failures.append(INFMOFailure.SYNTHETIC_TRUTH_FINDING)
        if any(not item.traceability_refs for item in items):
            failures.append(INFMOFailure.MISSING_TRACEABILITY)
        coverage = {
            "executed": sum(item.outcome in {VerificationOutcome.PASS, VerificationOutcome.FAIL} for item in items),
            "passed": sum(item.outcome == VerificationOutcome.PASS for item in items),
            "failed": sum(item.outcome == VerificationOutcome.FAIL for item in items),
            "skipped": sum(item.outcome == VerificationOutcome.SKIPPED for item in items),
            "blocked": sum(item.outcome == VerificationOutcome.BLOCKED for item in items),
            "unknown": sum(item.outcome == VerificationOutcome.UNKNOWN for item in items),
            "required_categories": len(self.required_categories),
            "covered_categories": len(categories),
        }
        unique = tuple(dict.fromkeys(failures))
        return VerificationCompletionReport(INFMOStatus.PASS if not unique else INFMOStatus.FAIL_CLOSED, unique, coverage, not unique)


@dataclass(frozen=True)
class InfrastructureConstitutionalCertificationPackage:
    candidate: CandidateCertificationDecision
    bridges: BridgeInfrastructureCertification
    synthetic_truth: SyntheticTruthCertification
    persistence_replay: PersistenceReplayCertification
    verification: VerificationCompletionReport
    category_reports: Mapping[str, str]
    unresolved_findings: tuple[str, ...]
    freeze_declaration: str
    sentinel_authorization: str


@dataclass(frozen=True)
class FinalInfrastructureCertification:
    status: INFMOStatus
    failures: tuple[INFMOFailure, ...]
    package_digest: str
    sentinel_certification_authorized: bool


class InfrastructureConstitutionalCertificationEngine:
    """INF-MO-006 final constitutional PASS, freeze, and Sentinel authorization gate."""

    required_reports = {
        "authority",
        "runtime",
        "canonical_bridge",
        "persistence",
        "replay",
        "synthetic_truth",
        "certification_integrity",
        "pass_checklist",
    }

    def certify(self, package: InfrastructureConstitutionalCertificationPackage) -> FinalInfrastructureCertification:
        failures: list[INFMOFailure] = []
        for decision in (package.candidate, package.bridges, package.synthetic_truth, package.persistence_replay, package.verification):
            if decision.status != INFMOStatus.PASS:
                failures.extend(decision.failures)
        if self.required_reports - set(package.category_reports) or any(_blank(value) for value in package.category_reports.values()):
            failures.append(INFMOFailure.UNRESOLVED_CERTIFICATION_FINDING)
        if package.unresolved_findings:
            failures.append(INFMOFailure.UNRESOLVED_CERTIFICATION_FINDING)
        if _blank(package.freeze_declaration):
            failures.append(INFMOFailure.MISSING_FREEZE_DECLARATION)
        if _blank(package.sentinel_authorization):
            failures.append(INFMOFailure.MISSING_SENTINEL_AUTHORIZATION)
        unique = tuple(dict.fromkeys(failures))
        status = INFMOStatus.CONSTITUTIONAL_FREEZE if not unique else INFMOStatus.FAIL_CLOSED
        return FinalInfrastructureCertification(status, unique, _digest(asdict(package)), status == INFMOStatus.CONSTITUTIONAL_FREEZE)


@dataclass(frozen=True)
class InfrastructureTestRegistration:
    test_id: str
    category: str
    executable: bool
    disabled: bool
    orphaned: bool


@dataclass(frozen=True)
class CertificationTimeoutRecord:
    test_id: str
    elapsed_seconds: float
    configured_timeout_seconds: float
    system_state: str
    candidate_id: str
    workflow_id: str
    stack_reference: str
    failure_classification: str


@dataclass(frozen=True)
class EnduranceCycleRecord:
    cycle_id: str
    runtime_validated: bool
    startup_validated: bool
    shutdown_validated: bool
    persistence_validated: bool
    replay_validated: bool
    workflow_validated: bool
    authority_validated: bool
    repository_validated: bool
    evidence_hash: str


@dataclass(frozen=True)
class RepeatabilityRunRecord:
    run_id: str
    execution_order_hash: str
    evidence_hash: str
    candidate_hash: str
    repository_hash: str
    persistence_hash: str
    replay_hash: str
    authority_hash: str


@dataclass(frozen=True)
class CertificationSessionInput:
    session_id: str
    candidate_id: str
    repository_id: str
    certification_id: str
    expected_tests: tuple[str, ...]
    registered_tests: tuple[InfrastructureTestRegistration, ...]
    denominator_hash_before: str
    denominator_hash_after: str
    approved_concurrency: bool
    execution_order: tuple[str, ...]
    timeout_records: tuple[CertificationTimeoutRecord, ...]
    endurance_cycles: tuple[EnduranceCycleRecord, ...]
    repeatability_runs: tuple[RepeatabilityRunRecord, ...]
    immutable_evidence_hash: str
    audit_package_hash: str
    pass_inputs: Mapping[str, bool]


@dataclass(frozen=True)
class InfrastructureCertificationExecutionRecord:
    status: INFMOStatus
    failures: tuple[INFMOFailure, ...]
    deterministic_order: tuple[str, ...]
    audit_package_hash: str
    result_digest: str


class InfrastructureCertificationExecutionEngine:
    """INF-MO-004 deterministic certification execution and audit-package engine."""

    required_pass_inputs = (
        "candidate_identity",
        "repository_identity",
        "replay",
        "persistence",
        "law_vii",
        "authority",
        "bridge",
        "synthetic_truth_zero",
        "repeatability",
        "endurance",
        "immutable_evidence",
    )

    def execute(self, session: CertificationSessionInput) -> InfrastructureCertificationExecutionRecord:
        failures: list[INFMOFailure] = []
        expected = tuple(session.expected_tests)
        registered_ids = tuple(item.test_id for item in session.registered_tests)
        if set(expected) != set(registered_ids):
            failures.append(INFMOFailure.INCOMPLETE_COVERAGE)
        if len(set(registered_ids)) != len(registered_ids):
            failures.append(INFMOFailure.DUPLICATE_TEST)
        if any(item.disabled for item in session.registered_tests):
            failures.append(INFMOFailure.DISABLED_TEST)
        if any(item.orphaned for item in session.registered_tests):
            failures.append(INFMOFailure.ORPHAN_TEST)
        if any(not item.executable for item in session.registered_tests):
            failures.append(INFMOFailure.UNKNOWN_VERIFICATION)
        if session.denominator_hash_before != session.denominator_hash_after:
            failures.append(INFMOFailure.DENOMINATOR_MUTATION)
        if tuple(sorted(expected)) != session.execution_order:
            failures.append(INFMOFailure.NON_DETERMINISTIC_SCHEDULING)
        if session.approved_concurrency:
            failures.append(INFMOFailure.NON_DETERMINISTIC_SCHEDULING)
        if session.timeout_records:
            failures.append(INFMOFailure.TIMEOUT_AMBIGUITY)
        if not session.endurance_cycles or any(not _endurance_cycle_passed(cycle) for cycle in session.endurance_cycles):
            failures.append(INFMOFailure.ENDURANCE_FAILURE)
        if not _repeatability_passed(session.repeatability_runs):
            failures.append(INFMOFailure.REPEATABILITY_DIVERGENCE)
        if _blank(session.immutable_evidence_hash) or _blank(session.audit_package_hash):
            failures.append(INFMOFailure.MUTABLE_CERTIFICATION_RESULT)
        if any(not session.pass_inputs.get(name, False) for name in self.required_pass_inputs):
            failures.append(INFMOFailure.UNRESOLVED_CERTIFICATION_FINDING)
        unique = tuple(dict.fromkeys(failures))
        return InfrastructureCertificationExecutionRecord(
            status=INFMOStatus.PASS if not unique else INFMOStatus.FAIL_CLOSED,
            failures=unique,
            deterministic_order=session.execution_order,
            audit_package_hash=session.audit_package_hash,
            result_digest=_digest(asdict(session)),
        )


def _blank(value: str) -> bool:
    return str(value).strip().lower() in {"", "unknown", "placeholder", "synthetic", "none", "null"}


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _endurance_cycle_passed(cycle: EnduranceCycleRecord) -> bool:
    return all(
        (
            cycle.runtime_validated,
            cycle.startup_validated,
            cycle.shutdown_validated,
            cycle.persistence_validated,
            cycle.replay_validated,
            cycle.workflow_validated,
            cycle.authority_validated,
            cycle.repository_validated,
            not _blank(cycle.evidence_hash),
        )
    )


def _repeatability_passed(runs: tuple[RepeatabilityRunRecord, ...]) -> bool:
    if len(runs) < 2:
        return False
    fields = (
        "execution_order_hash",
        "evidence_hash",
        "candidate_hash",
        "repository_hash",
        "persistence_hash",
        "replay_hash",
        "authority_hash",
    )
    return all(len({getattr(run, field) for run in runs}) == 1 for field in fields)
