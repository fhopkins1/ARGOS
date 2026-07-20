"""Sentinel constitutional governance controls for SENT-GOV-019 through SENT-GOV-021."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Iterable, Mapping


SENT_GOV_VERSION = "SENT-GOV-019-021/1.0.0"


class GovernanceDecision(str, Enum):
    PASS = "PASS"
    FAIL_CLOSED = "FAIL_CLOSED"


class BridgeClass(str, Enum):
    PRODUCTION = "production"
    CONDITIONAL = "conditional"
    TEST_ONLY = "test_only"
    REPLAY_ONLY = "replay_only"
    SIMULATION_ONLY = "simulation_only"
    RECOVERY = "recovery"
    NOTIFICATION = "notification"
    WORKFLOW_AUTHORITY = "workflow_authority"
    EVIDENCE_TRANSFER = "evidence_transfer"


class OperatingMode(str, Enum):
    PAPER_OBSERVED = "PAPER_OBSERVED"
    SIMULATION_SYNTHETIC = "SIMULATION_SYNTHETIC"
    REPLAY_HISTORICAL = "REPLAY_HISTORICAL"
    DEGRADED_NO_MARKET_TRUTH = "DEGRADED_NO_MARKET_TRUTH"
    TEST = "TEST"


class BridgeCertificationState(str, Enum):
    UNCERTIFIED = "UNCERTIFIED"
    CANDIDATE = "CANDIDATE"
    EVIDENCE_READY = "EVIDENCE_READY"
    AUDITOR_REVIEW = "AUDITOR_REVIEW"
    CERTIFIED = "CERTIFIED"
    REVOKED = "REVOKED"


class BridgeRejectionCode(str, Enum):
    BRIDGE_NOT_REGISTERED = "bridge_not_registered"
    BRIDGE_CLASS_NOT_PERMITTED = "bridge_class_not_permitted"
    SOURCE_UNAUTHORIZED = "source_unauthorized"
    DESTINATION_UNAUTHORIZED = "destination_unauthorized"
    OPERATING_MODE_PROHIBITED = "operating_mode_prohibited"
    BRIDGE_UNCERTIFIED = "bridge_uncertified"
    PRODUCTION_ELIGIBILITY_ABSENT = "production_eligibility_absent"
    WORKFLOW_TOKEN_MISSING = "workflow_token_missing"
    WORKFLOW_TOKEN_INVALID = "workflow_token_invalid"
    WORKFLOW_TOKEN_STALE = "workflow_token_stale"
    WORKFLOW_TOKEN_DUPLICATED = "workflow_token_duplicated"
    WORKFLOW_MISMATCH = "workflow_mismatch"
    CONTRACT_VIOLATION = "contract_violation"
    DUPLICATE_MUTATION_PREVENTED = "duplicate_mutation_prevented"
    REGISTRY_VERSION_MISMATCH = "registry_version_mismatch"
    CANDIDATE_IDENTITY_MISMATCH = "candidate_identity_mismatch"
    EVIDENCE_PERSISTENCE_FAILURE = "evidence_persistence_failure"
    RECOVERY_EVIDENCE_INSUFFICIENT = "recovery_evidence_insufficient"
    CONSTITUTIONAL_BYPASS_DETECTED = "constitutional_bypass_detected"
    ORPHAN_OFFICE_CONDITION = "orphan_office_condition"
    UNDECLARED_CALL_PATH_DETECTED = "undeclared_call_path_detected"


class TruthClassification(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    ESTIMATED = "ESTIMATED"
    SYNTHETIC = "SYNTHETIC"
    UNKNOWN = "UNKNOWN"


class TruthDomain(str, Enum):
    CURRENT_OBSERVED_PAPER = "CURRENT_OBSERVED_PAPER"
    SYNTHETIC_SIMULATION = "SYNTHETIC_SIMULATION"
    HISTORICAL_REPLAY = "HISTORICAL_REPLAY"
    DEGRADED_OPERATION = "DEGRADED_OPERATION"
    CERTIFICATION_EVIDENCE = "CERTIFICATION_EVIDENCE"
    TEST_FIXTURE = "TEST_FIXTURE"
    RECOVERY_QUARANTINE = "RECOVERY_QUARANTINE"


class TruthFailure(str, Enum):
    SOURCE_AUTHORITY_MISSING = "source_authority_missing"
    PROVENANCE_MISSING = "provenance_missing"
    TRUTH_CLASSIFICATION_ABSENT = "truth_classification_absent"
    OPERATING_MODE_AMBIGUOUS = "operating_mode_ambiguous"
    TRUTH_DOMAIN_AMBIGUOUS = "truth_domain_ambiguous"
    SYNTHETIC_PROMOTION_ATTEMPT = "synthetic_promotion_attempt"
    UNKNOWN_PROMOTION_ATTEMPT = "unknown_promotion_attempt"
    STALE_INFORMATION = "stale_information"
    CONFLICT_UNRESOLVED = "conflict_unresolved"
    LINEAGE_MISSING = "lineage_missing"
    DOMAIN_CONTAMINATION = "domain_contamination"
    CORRUPTED_EVIDENCE = "corrupted_evidence"
    RECOVERY_FABRICATION_REQUIRED = "recovery_fabrication_required"
    QUARANTINED_RECORD_USED = "quarantined_record_used"


class CertificationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INDETERMINATE = "INDETERMINATE"
    INVALID_AUDIT = "INVALID_AUDIT"


@dataclass(frozen=True)
class RegistryVersion:
    registry_id: str
    version_id: str
    governing_doctrine: str
    creation_timestamp: str
    schema_version: str
    supersedes: str | None
    content_hash: str


@dataclass(frozen=True)
class CanonicalBridgeRecord:
    bridge_id: str
    bridge_name: str
    bridge_class: BridgeClass
    source: str
    destination: str
    governing_doctrine: str
    governing_modification_order: str
    transferred_object_types: tuple[str, ...]
    transferred_authority: str
    permitted_workflow_states: tuple[str, ...]
    permitted_operating_modes: tuple[OperatingMode, ...]
    workflow_token_required: bool
    rejection_conditions: tuple[BridgeRejectionCode, ...]
    evidence_requirements: tuple[str, ...]
    certification_requirements: tuple[str, ...]
    certification_state: BridgeCertificationState
    production_eligible: bool
    version_id: str
    immutable_content_hash: str


@dataclass(frozen=True)
class WorkflowTokenEvidence:
    token_id: str
    workflow_id: str
    current_owner: str
    next_owner: str
    authentic: bool
    stale: bool = False
    duplicated: bool = False


@dataclass(frozen=True)
class BridgeInvocationRequest:
    bridge_id: str
    workflow_id: str
    source: str
    destination: str
    operating_mode: OperatingMode
    transferred_object_type: str
    transferred_object_id: str
    input_hash: str
    output_hash: str
    invocation_timestamp: str
    completion_timestamp: str
    sequence_number: int
    candidate_identity: str
    workflow_token: WorkflowTokenEvidence | None


@dataclass(frozen=True)
class BridgeInvocationEvidence:
    decision: GovernanceDecision
    bridge_id: str
    registry_version: str
    workflow_id: str
    workflow_token_id: str
    source: str
    destination: str
    operating_mode: OperatingMode
    transferred_object_type: str
    transferred_object_id: str
    invocation_timestamp: str
    completion_timestamp: str
    deterministic_sequence_number: int
    rejection_codes: tuple[BridgeRejectionCode, ...]
    duplicate_status: GovernanceDecision
    idempotency_result: str
    recovery_status: str
    implementation_candidate_identity: str
    evidence_chain_reference: str
    evidence_hash: str


@dataclass(frozen=True)
class BridgeCertificationResult:
    bridge_id: str
    decision: GovernanceDecision
    state: BridgeCertificationState
    failed_dimensions: tuple[str, ...]
    evidence_hash: str


class CanonicalBridgeRegistry:
    """Immutable SENT-GOV-019 bridge registry with deterministic lookup and hashing."""

    def __init__(self, registry: RegistryVersion, bridges: Iterable[CanonicalBridgeRecord]) -> None:
        self.registry = registry
        self._bridges = tuple(sorted(bridges, key=lambda item: item.bridge_id))
        self._by_id = {bridge.bridge_id: bridge for bridge in self._bridges}

    @property
    def bridges(self) -> tuple[CanonicalBridgeRecord, ...]:
        return self._bridges

    @property
    def registry_hash(self) -> str:
        return _digest({"registry": asdict(self.registry), "bridges": tuple(asdict(item) for item in self._bridges)})

    def get(self, bridge_id: str) -> CanonicalBridgeRecord | None:
        return self._by_id.get(bridge_id)

    def discovered_call_path_report(self, discovered_bridge_ids: Iterable[str]) -> Mapping[str, tuple[str, ...]]:
        discovered = tuple(sorted(discovered_bridge_ids))
        declared = tuple(bridge.bridge_id for bridge in self._bridges)
        return {
            "matched_declared_bridge": tuple(item for item in discovered if item in declared),
            "declared_bridge_not_observed": tuple(item for item in declared if item not in discovered),
            "undeclared_call_path": tuple(item for item in discovered if item not in declared),
        }


class BridgeGovernanceEngine:
    """Constitutional bridge evaluator that fails closed and records immutable evidence."""

    def __init__(self, registry: CanonicalBridgeRegistry, candidate_identity: str) -> None:
        self.registry = registry
        self.candidate_identity = candidate_identity
        self._evidence: tuple[BridgeInvocationEvidence, ...] = ()
        self._seen_objects: set[tuple[str, str, str]] = set()

    @property
    def evidence(self) -> tuple[BridgeInvocationEvidence, ...]:
        return self._evidence

    def invoke(self, request: BridgeInvocationRequest) -> BridgeInvocationEvidence:
        bridge = self.registry.get(request.bridge_id)
        rejection_codes: list[BridgeRejectionCode] = []
        duplicate_key = (request.bridge_id, request.workflow_id, request.transferred_object_id)
        if bridge is None:
            rejection_codes.append(BridgeRejectionCode.BRIDGE_NOT_REGISTERED)
        else:
            rejection_codes.extend(self._validate_registered_bridge(bridge, request))
        if duplicate_key in self._seen_objects:
            rejection_codes.append(BridgeRejectionCode.DUPLICATE_MUTATION_PREVENTED)
        if request.candidate_identity != self.candidate_identity:
            rejection_codes.append(BridgeRejectionCode.CANDIDATE_IDENTITY_MISMATCH)

        unique = tuple(dict.fromkeys(rejection_codes))
        decision = GovernanceDecision.PASS if not unique else GovernanceDecision.FAIL_CLOSED
        if decision == GovernanceDecision.PASS:
            self._seen_objects.add(duplicate_key)
        evidence = self._evidence_record(request, decision, unique)
        self._evidence = self._evidence + (evidence,)
        return evidence

    def certify_bridge(
        self,
        bridge_id: str,
        dimension_results: Mapping[str, bool],
        mandatory_dimensions: Iterable[str],
        negative_tests_complete: bool,
        restart_tests_complete: bool,
        recovery_tests_complete: bool,
        self_attested: bool = False,
    ) -> BridgeCertificationResult:
        bridge = self.registry.get(bridge_id)
        failed = []
        if bridge is None:
            failed.append(BridgeRejectionCode.BRIDGE_NOT_REGISTERED.value)
        for dimension in mandatory_dimensions:
            if not dimension_results.get(dimension, False):
                failed.append(dimension)
        if not negative_tests_complete:
            failed.append("negative_tests_incomplete")
        if not restart_tests_complete:
            failed.append("restart_tests_incomplete")
        if not recovery_tests_complete:
            failed.append("recovery_tests_incomplete")
        if self_attested:
            failed.append("self_attestation_prohibited")
        unique = tuple(dict.fromkeys(failed))
        return BridgeCertificationResult(
            bridge_id=bridge_id,
            decision=GovernanceDecision.PASS if not unique else GovernanceDecision.FAIL_CLOSED,
            state=BridgeCertificationState.CERTIFIED if not unique else BridgeCertificationState.UNCERTIFIED,
            failed_dimensions=unique,
            evidence_hash=_digest({"bridge_id": bridge_id, "failed": unique, "dimensions": dict(dimension_results)}),
        )

    def orphan_offices(self, active_offices: Iterable[str]) -> tuple[str, ...]:
        offices = tuple(sorted(active_offices))
        connected = {bridge.source for bridge in self.registry.bridges} | {bridge.destination for bridge in self.registry.bridges}
        return tuple(office for office in offices if office not in connected)

    def _validate_registered_bridge(
        self,
        bridge: CanonicalBridgeRecord,
        request: BridgeInvocationRequest,
    ) -> tuple[BridgeRejectionCode, ...]:
        failures: list[BridgeRejectionCode] = []
        if request.source != bridge.source:
            failures.append(BridgeRejectionCode.SOURCE_UNAUTHORIZED)
        if request.destination != bridge.destination:
            failures.append(BridgeRejectionCode.DESTINATION_UNAUTHORIZED)
        if request.operating_mode not in bridge.permitted_operating_modes:
            failures.append(BridgeRejectionCode.OPERATING_MODE_PROHIBITED)
        if request.transferred_object_type not in bridge.transferred_object_types:
            failures.append(BridgeRejectionCode.CONTRACT_VIOLATION)
        if bridge.certification_state != BridgeCertificationState.CERTIFIED:
            failures.append(BridgeRejectionCode.BRIDGE_UNCERTIFIED)
        if request.operating_mode == OperatingMode.PAPER_OBSERVED and not bridge.production_eligible:
            failures.append(BridgeRejectionCode.PRODUCTION_ELIGIBILITY_ABSENT)
        if bridge.bridge_class == BridgeClass.TEST_ONLY and request.operating_mode != OperatingMode.TEST:
            failures.append(BridgeRejectionCode.BRIDGE_CLASS_NOT_PERMITTED)
        if bridge.bridge_class == BridgeClass.REPLAY_ONLY and request.operating_mode != OperatingMode.REPLAY_HISTORICAL:
            failures.append(BridgeRejectionCode.BRIDGE_CLASS_NOT_PERMITTED)
        if bridge.bridge_class == BridgeClass.SIMULATION_ONLY and request.operating_mode != OperatingMode.SIMULATION_SYNTHETIC:
            failures.append(BridgeRejectionCode.BRIDGE_CLASS_NOT_PERMITTED)
        failures.extend(self._token_failures(bridge, request))
        return tuple(failures)

    @staticmethod
    def _token_failures(
        bridge: CanonicalBridgeRecord,
        request: BridgeInvocationRequest,
    ) -> tuple[BridgeRejectionCode, ...]:
        if not bridge.workflow_token_required:
            return ()
        token = request.workflow_token
        if token is None or not token.token_id:
            return (BridgeRejectionCode.WORKFLOW_TOKEN_MISSING,)
        failures: list[BridgeRejectionCode] = []
        if not token.authentic:
            failures.append(BridgeRejectionCode.WORKFLOW_TOKEN_INVALID)
        if token.stale:
            failures.append(BridgeRejectionCode.WORKFLOW_TOKEN_STALE)
        if token.duplicated:
            failures.append(BridgeRejectionCode.WORKFLOW_TOKEN_DUPLICATED)
        if token.workflow_id != request.workflow_id:
            failures.append(BridgeRejectionCode.WORKFLOW_MISMATCH)
        if token.current_owner != request.source or token.next_owner != request.destination:
            failures.append(BridgeRejectionCode.WORKFLOW_TOKEN_INVALID)
        return tuple(failures)

    def _evidence_record(
        self,
        request: BridgeInvocationRequest,
        decision: GovernanceDecision,
        rejection_codes: tuple[BridgeRejectionCode, ...],
    ) -> BridgeInvocationEvidence:
        token_id = request.workflow_token.token_id if request.workflow_token else ""
        payload = {"request": asdict(request), "decision": decision.value, "rejections": tuple(item.value for item in rejection_codes)}
        return BridgeInvocationEvidence(
            decision=decision,
            bridge_id=request.bridge_id,
            registry_version=self.registry.registry.version_id,
            workflow_id=request.workflow_id,
            workflow_token_id=token_id,
            source=request.source,
            destination=request.destination,
            operating_mode=request.operating_mode,
            transferred_object_type=request.transferred_object_type,
            transferred_object_id=request.transferred_object_id,
            invocation_timestamp=request.invocation_timestamp,
            completion_timestamp=request.completion_timestamp,
            deterministic_sequence_number=request.sequence_number,
            rejection_codes=rejection_codes,
            duplicate_status=GovernanceDecision.FAIL_CLOSED if BridgeRejectionCode.DUPLICATE_MUTATION_PREVENTED in rejection_codes else GovernanceDecision.PASS,
            idempotency_result="prior_result_preserved" if BridgeRejectionCode.DUPLICATE_MUTATION_PREVENTED in rejection_codes else "new_event_recorded",
            recovery_status="authoritative_evidence_required",
            implementation_candidate_identity=request.candidate_identity,
            evidence_chain_reference=_digest(payload),
            evidence_hash=_digest(payload),
        )


@dataclass(frozen=True)
class SourceProvenance:
    source_id: str
    provider_id: str
    source_authority: bool
    acquisition_method: str
    request_id: str
    response_id: str
    source_timestamp: str
    receipt_timestamp: str
    effective_timestamp: str
    raw_payload_hash: str
    chain_of_custody: tuple[str, ...]


@dataclass(frozen=True)
class TransformationLineage:
    transformation_id: str
    transformation_version: str
    input_record_ids: tuple[str, ...]
    input_truth_classes: tuple[TruthClassification, ...]
    parameters_hash: str
    output_hash: str
    reproducible: bool


@dataclass(frozen=True)
class TruthRecord:
    record_id: str
    record_version: str
    subject_identity: str
    value_hash: str
    primary_classification: TruthClassification
    operating_mode: OperatingMode
    truth_domain: TruthDomain
    source_id: str
    freshness_status: str
    provenance: SourceProvenance | None
    transformation_lineage: TransformationLineage | None
    parent_record_ids: tuple[str, ...]
    workflow_id: str
    office_id: str
    bridge_id: str
    conflict_status: str
    independence_status: str
    recovery_status: str
    reconstruction_status: str
    quarantine_status: str
    integrity_evidence: str
    persistence_evidence: str
    certification_eligible: bool
    learning_eligible: bool
    performance_eligible: bool


@dataclass(frozen=True)
class TruthValidationResult:
    decision: GovernanceDecision
    failures: tuple[TruthFailure, ...]
    quarantine_required: bool
    evidence_hash: str


class TruthGovernanceEngine:
    """SENT-GOV-020 truth provenance, simulation isolation, and recovery controls."""

    def __init__(self, approved_sources: Mapping[TruthDomain, tuple[str, ...]]) -> None:
        self.approved_sources = approved_sources

    def validate(self, record: TruthRecord) -> TruthValidationResult:
        failures: list[TruthFailure] = []
        if record.provenance is None:
            failures.append(TruthFailure.PROVENANCE_MISSING)
        elif not record.provenance.source_authority or record.source_id not in self.approved_sources.get(record.truth_domain, ()):
            failures.append(TruthFailure.SOURCE_AUTHORITY_MISSING)
        if record.primary_classification == TruthClassification.OBSERVED:
            if record.truth_domain in {TruthDomain.SYNTHETIC_SIMULATION, TruthDomain.HISTORICAL_REPLAY, TruthDomain.TEST_FIXTURE}:
                failures.append(TruthFailure.DOMAIN_CONTAMINATION)
            if record.provenance is None or record.provenance.raw_payload_hash == "":
                failures.append(TruthFailure.PROVENANCE_MISSING)
        if record.primary_classification == TruthClassification.DERIVED:
            if record.transformation_lineage is None or not record.transformation_lineage.reproducible:
                failures.append(TruthFailure.LINEAGE_MISSING)
        if record.primary_classification == TruthClassification.SYNTHETIC and record.truth_domain == TruthDomain.CURRENT_OBSERVED_PAPER:
            failures.append(TruthFailure.SYNTHETIC_PROMOTION_ATTEMPT)
        if record.primary_classification == TruthClassification.UNKNOWN and record.certification_eligible:
            failures.append(TruthFailure.UNKNOWN_PROMOTION_ATTEMPT)
        if record.freshness_status == "STALE":
            failures.append(TruthFailure.STALE_INFORMATION)
        if record.conflict_status == "UNRESOLVED":
            failures.append(TruthFailure.CONFLICT_UNRESOLVED)
        if record.recovery_status == "FABRICATED":
            failures.append(TruthFailure.RECOVERY_FABRICATION_REQUIRED)
        if record.quarantine_status == "QUARANTINED" and (record.performance_eligible or record.certification_eligible):
            failures.append(TruthFailure.QUARANTINED_RECORD_USED)
        if record.integrity_evidence == "":
            failures.append(TruthFailure.CORRUPTED_EVIDENCE)
        unique = tuple(dict.fromkeys(failures))
        return TruthValidationResult(
            decision=GovernanceDecision.PASS if not unique else GovernanceDecision.FAIL_CLOSED,
            failures=unique,
            quarantine_required=bool(unique),
            evidence_hash=_digest({"record": asdict(record), "failures": tuple(item.value for item in unique)}),
        )

    def classify_transition(
        self,
        prior: TruthClassification,
        proposed: TruthClassification,
        qualifying_authoritative_evidence: bool,
    ) -> TruthValidationResult:
        failures: list[TruthFailure] = []
        if prior == TruthClassification.SYNTHETIC and proposed == TruthClassification.OBSERVED:
            failures.append(TruthFailure.SYNTHETIC_PROMOTION_ATTEMPT)
        if prior == TruthClassification.UNKNOWN and proposed == TruthClassification.OBSERVED and not qualifying_authoritative_evidence:
            failures.append(TruthFailure.UNKNOWN_PROMOTION_ATTEMPT)
        unique = tuple(dict.fromkeys(failures))
        return TruthValidationResult(
            decision=GovernanceDecision.PASS if not unique else GovernanceDecision.FAIL_CLOSED,
            failures=unique,
            quarantine_required=bool(unique),
            evidence_hash=_digest({"prior": prior.value, "proposed": proposed.value, "failures": tuple(item.value for item in unique)}),
        )


@dataclass(frozen=True)
class CertificationCandidate:
    repository_revision: str
    doctrine_revision: str
    configuration_hash: str
    dependency_hash: str
    requirement_registry_hash: str
    evidence_registry_hash: str
    evidence_package_hash: str
    execution_environment_hash: str
    certification_scope: tuple[str, ...]
    excluded_scope: tuple[str, ...]
    requirement_results: Mapping[str, bool]
    evidence_results: Mapping[str, bool]
    deterministic_rerun: bool
    repository_integrity_verified: bool
    audit_independent: bool
    implementation_self_certified: bool
    skipped_mandatory_tests: tuple[str, ...] = ()
    corrupted_evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class CertificationAssessment:
    verdict: CertificationVerdict
    failures: tuple[str, ...]
    certification_record_hash: str


class IndependentCertificationAuthority:
    """SENT-GOV-021 mechanical verdict evaluator; it never grants final auditor authority."""

    def assess(self, candidate: CertificationCandidate) -> CertificationAssessment:
        invalid: list[str] = []
        fail: list[str] = []
        indeterminate: list[str] = []
        identity_fields = (
            candidate.repository_revision,
            candidate.doctrine_revision,
            candidate.configuration_hash,
            candidate.dependency_hash,
            candidate.requirement_registry_hash,
            candidate.evidence_registry_hash,
            candidate.evidence_package_hash,
            candidate.execution_environment_hash,
        )
        if any(_blank(item) for item in identity_fields):
            invalid.append("candidate_identity_incomplete")
        if not candidate.certification_scope:
            invalid.append("certification_scope_ambiguous")
        if candidate.skipped_mandatory_tests:
            invalid.append("mandatory_tests_skipped")
        if candidate.corrupted_evidence:
            invalid.append("corrupted_evidence")
        if candidate.implementation_self_certified:
            invalid.append("implementation_self_certified")
        if not candidate.repository_integrity_verified:
            invalid.append("repository_integrity_unverified")
        if not candidate.audit_independent:
            invalid.append("audit_independence_absent")
        if not candidate.deterministic_rerun:
            invalid.append("deterministic_rerun_failed")
        for requirement, passed in sorted(candidate.requirement_results.items()):
            if not passed:
                fail.append(f"requirement_failed:{requirement}")
        for evidence, present in sorted(candidate.evidence_results.items()):
            if not present:
                indeterminate.append(f"evidence_missing:{evidence}")
        if invalid:
            verdict = CertificationVerdict.INVALID_AUDIT
            failures = tuple(dict.fromkeys(invalid + fail + indeterminate))
        elif fail:
            verdict = CertificationVerdict.FAIL
            failures = tuple(dict.fromkeys(fail))
        elif indeterminate:
            verdict = CertificationVerdict.INDETERMINATE
            failures = tuple(dict.fromkeys(indeterminate))
        else:
            verdict = CertificationVerdict.PASS
            failures = ()
        return CertificationAssessment(
            verdict=verdict,
            failures=failures,
            certification_record_hash=_digest({"candidate": asdict(candidate), "verdict": verdict.value, "failures": failures}),
        )


def _blank(value: str) -> bool:
    return str(value).strip().lower() in {"", "unknown", "placeholder", "synthetic", "none", "null"}


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
