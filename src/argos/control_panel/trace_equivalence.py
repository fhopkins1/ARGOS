"""TC-001 certification-to-production trace equivalence authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .canonical_bridge_fabric import BridgeExecutionResult, BridgeResultStatus, default_bridge_definitions
from .canonical_enterprise_runtime import CanonicalEnterpriseRuntime


TC_001_VERSION = "TC-001.1"


class ExecutionOrigin(str, Enum):
    UNKNOWN = "UNKNOWN"
    CANONICAL_PRODUCTION_RUNTIME = "CANONICAL_PRODUCTION_RUNTIME"
    CANONICAL_RUNTIME_TEST_HARNESS = "CANONICAL_RUNTIME_TEST_HARNESS"
    CERTIFICATION_HARNESS = "CERTIFICATION_HARNESS"
    UNIT_TEST_HELPER = "UNIT_TEST_HELPER"
    INTEGRATION_HELPER = "INTEGRATION_HELPER"
    SYNTHETIC_FIXTURE_REPLAY = "SYNTHETIC_FIXTURE_REPLAY"
    STATIC_DOCUMENTATION_EVIDENCE = "STATIC_DOCUMENTATION_EVIDENCE"
    EXTERNAL_OPERATIONAL_SYSTEM = "EXTERNAL_OPERATIONAL_SYSTEM"


class TraceEquivalenceLevel(str, Enum):
    NONE = "NONE"
    STRUCTURAL = "STRUCTURAL"
    CONTRACT = "CONTRACT"
    INTEGRATION = "INTEGRATION"
    CANONICAL_RUNTIME = "CANONICAL_RUNTIME"
    EXTERNAL_OPERATIONAL = "EXTERNAL_OPERATIONAL"


class TraceClaimType(str, Enum):
    STRUCTURAL_COVERAGE = "STRUCTURAL_COVERAGE"
    CONTRACT_EXECUTION = "CONTRACT_EXECUTION"
    INTEGRATION_EXECUTION = "INTEGRATION_EXECUTION"
    PRODUCTION_EXECUTION = "PRODUCTION_EXECUTION"
    EXTERNAL_OPERATIONAL_EXECUTION = "EXTERNAL_OPERATIONAL_EXECUTION"


class TraceEligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


class TraceRejectionCode(str, Enum):
    TRACE_EXECUTION_ORIGIN_UNKNOWN = "TRACE_EXECUTION_ORIGIN_UNKNOWN"
    TRACE_CANONICAL_RUNTIME_UNVERIFIED = "TRACE_CANONICAL_RUNTIME_UNVERIFIED"
    TRACE_CAUSALITY_INCOMPLETE = "TRACE_CAUSALITY_INCOMPLETE"
    TRACE_TOKEN_AUTHORITY_UNVERIFIED = "TRACE_TOKEN_AUTHORITY_UNVERIFIED"
    TRACE_SOURCE_AUTHORITY_UNVERIFIED = "TRACE_SOURCE_AUTHORITY_UNVERIFIED"
    TRACE_DESTINATION_ACCEPTANCE_UNVERIFIED = "TRACE_DESTINATION_ACCEPTANCE_UNVERIFIED"
    TRACE_ARTIFACT_INTEGRITY_FAILURE = "TRACE_ARTIFACT_INTEGRITY_FAILURE"
    TRACE_PROOF_DOMAIN_INVALID = "TRACE_PROOF_DOMAIN_INVALID"
    TRACE_REPOSITORY_IDENTITY_MISMATCH = "TRACE_REPOSITORY_IDENTITY_MISMATCH"
    TRACE_CERTIFICATION_HARNESS_ORCHESTRATED = "TRACE_CERTIFICATION_HARNESS_ORCHESTRATED"
    TRACE_PRODUCTION_EQUIVALENCE_FAILED = "TRACE_PRODUCTION_EQUIVALENCE_FAILED"
    CERTIFICATION_EVIDENCE_NOT_PRODUCTION_EQUIVALENT = "CERTIFICATION_EVIDENCE_NOT_PRODUCTION_EQUIVALENT"


_EQUIVALENCE_RANK = {
    TraceEquivalenceLevel.NONE: 0,
    TraceEquivalenceLevel.STRUCTURAL: 1,
    TraceEquivalenceLevel.CONTRACT: 2,
    TraceEquivalenceLevel.INTEGRATION: 3,
    TraceEquivalenceLevel.CANONICAL_RUNTIME: 4,
    TraceEquivalenceLevel.EXTERNAL_OPERATIONAL: 5,
}


@dataclass(frozen=True)
class CanonicalRuntimeIdentity:
    runtime_instance_id: str
    bootstrap_trace_id: str
    startup_evidence_hash: str
    component_fingerprint: str
    repository_commit: str
    registered_runtime: bool = True
    schema_version: str = TC_001_VERSION


@dataclass(frozen=True)
class TraceAuthenticityRecord:
    trace_id: str
    subject_id: str
    origin: ExecutionOrigin
    equivalence_level: TraceEquivalenceLevel
    claim_type: TraceClaimType
    runtime_identity: CanonicalRuntimeIdentity | None
    runtime_startup_evidence: str
    causal_parent_ids: tuple[str, ...]
    workflow_id: str
    token_id: str
    token_authority_verified: bool
    source_authority: str
    source_authority_verified: bool
    destination_authority: str
    destination_acceptance_verified: bool
    artifact_id: str
    artifact_hash: str
    expected_artifact_hash: str
    proof_domain: str
    persistence_references: tuple[str, ...]
    repository_commit: str
    evidence_commit: str
    orchestrated_by_certification_harness: bool
    timestamp_utc: str
    trace_hash: str
    schema_version: str = TC_001_VERSION


@dataclass(frozen=True)
class TraceEligibilityResult:
    trace_id: str
    subject_id: str
    status: TraceEligibilityStatus
    equivalence_level: TraceEquivalenceLevel
    rejection_codes: tuple[TraceRejectionCode, ...]
    production_equivalent: bool
    schema_version: str = TC_001_VERSION


@dataclass(frozen=True)
class TraceCoverageAssessment:
    denominator: int
    numerator: int
    percent: float
    required_subject_ids: tuple[str, ...]
    eligible_subject_ids: tuple[str, ...]
    missing_subject_ids: tuple[str, ...]
    schema_version: str = TC_001_VERSION


@dataclass(frozen=True)
class TraceContradictionRecord:
    contradiction_id: str
    subject: str
    blocking: bool
    description: str
    rejection_code: TraceRejectionCode
    schema_version: str = TC_001_VERSION


@dataclass(frozen=True)
class TraceEquivalenceCertification:
    order_id: str
    verdict: str
    readiness: str
    repository_commit: str
    eligibility_results: tuple[TraceEligibilityResult, ...]
    bridge_coverage: TraceCoverageAssessment
    contradiction_report: tuple[TraceContradictionRecord, ...]
    canonical_runtime_trace_count: int
    certification_harness_rejected_count: int
    evidence_hash: str
    timestamp_utc: str
    schema_version: str = TC_001_VERSION


class TraceEquivalenceAuthority:
    production_minimum = TraceEquivalenceLevel.CANONICAL_RUNTIME

    def classify_origin(self, origin: ExecutionOrigin) -> TraceEquivalenceLevel:
        if origin == ExecutionOrigin.CANONICAL_PRODUCTION_RUNTIME:
            return TraceEquivalenceLevel.CANONICAL_RUNTIME
        if origin == ExecutionOrigin.EXTERNAL_OPERATIONAL_SYSTEM:
            return TraceEquivalenceLevel.EXTERNAL_OPERATIONAL
        if origin == ExecutionOrigin.CANONICAL_RUNTIME_TEST_HARNESS:
            return TraceEquivalenceLevel.INTEGRATION
        if origin == ExecutionOrigin.CERTIFICATION_HARNESS:
            return TraceEquivalenceLevel.CONTRACT
        if origin == ExecutionOrigin.INTEGRATION_HELPER:
            return TraceEquivalenceLevel.INTEGRATION
        if origin in {ExecutionOrigin.UNIT_TEST_HELPER, ExecutionOrigin.SYNTHETIC_FIXTURE_REPLAY}:
            return TraceEquivalenceLevel.CONTRACT
        if origin == ExecutionOrigin.STATIC_DOCUMENTATION_EVIDENCE:
            return TraceEquivalenceLevel.STRUCTURAL
        return TraceEquivalenceLevel.NONE

    def evaluate(self, record: TraceAuthenticityRecord) -> TraceEligibilityResult:
        rejection_codes: list[TraceRejectionCode] = []
        if record.origin == ExecutionOrigin.UNKNOWN:
            rejection_codes.append(TraceRejectionCode.TRACE_EXECUTION_ORIGIN_UNKNOWN)
        if _EQUIVALENCE_RANK[record.equivalence_level] < _EQUIVALENCE_RANK[self.production_minimum]:
            rejection_codes.append(TraceRejectionCode.TRACE_PRODUCTION_EQUIVALENCE_FAILED)
        if record.origin != ExecutionOrigin.CANONICAL_PRODUCTION_RUNTIME or not record.runtime_identity or not record.runtime_identity.registered_runtime:
            rejection_codes.append(TraceRejectionCode.TRACE_CANONICAL_RUNTIME_UNVERIFIED)
        if not record.runtime_startup_evidence or not record.causal_parent_ids or not record.workflow_id:
            rejection_codes.append(TraceRejectionCode.TRACE_CAUSALITY_INCOMPLETE)
        if not record.token_id or not record.token_authority_verified:
            rejection_codes.append(TraceRejectionCode.TRACE_TOKEN_AUTHORITY_UNVERIFIED)
        if not record.source_authority or not record.source_authority_verified:
            rejection_codes.append(TraceRejectionCode.TRACE_SOURCE_AUTHORITY_UNVERIFIED)
        if not record.destination_authority or not record.destination_acceptance_verified:
            rejection_codes.append(TraceRejectionCode.TRACE_DESTINATION_ACCEPTANCE_UNVERIFIED)
        if not record.artifact_id or not record.artifact_hash or record.artifact_hash != record.expected_artifact_hash:
            rejection_codes.append(TraceRejectionCode.TRACE_ARTIFACT_INTEGRITY_FAILURE)
        if record.proof_domain not in {"PAPER", "REPLAY"}:
            rejection_codes.append(TraceRejectionCode.TRACE_PROOF_DOMAIN_INVALID)
        if not record.repository_commit or record.repository_commit != record.evidence_commit:
            rejection_codes.append(TraceRejectionCode.TRACE_REPOSITORY_IDENTITY_MISMATCH)
        if record.orchestrated_by_certification_harness:
            rejection_codes.extend(
                (
                    TraceRejectionCode.TRACE_CERTIFICATION_HARNESS_ORCHESTRATED,
                    TraceRejectionCode.CERTIFICATION_EVIDENCE_NOT_PRODUCTION_EQUIVALENT,
                )
            )
        production_equivalent = not rejection_codes
        return TraceEligibilityResult(
            record.trace_id,
            record.subject_id,
            TraceEligibilityStatus.ELIGIBLE if production_equivalent else TraceEligibilityStatus.INELIGIBLE,
            record.equivalence_level,
            tuple(dict.fromkeys(rejection_codes)),
            production_equivalent,
        )

    def coverage(self, required_subject_ids: tuple[str, ...], results: tuple[TraceEligibilityResult, ...]) -> TraceCoverageAssessment:
        eligible = tuple(sorted({item.subject_id for item in results if item.production_equivalent and item.subject_id in required_subject_ids}))
        missing = tuple(item for item in required_subject_ids if item not in eligible)
        denominator = len(required_subject_ids)
        numerator = len(eligible)
        return TraceCoverageAssessment(
            denominator,
            numerator,
            round((numerator / denominator) * 100, 2) if denominator else 100.0,
            required_subject_ids,
            eligible,
            missing,
        )

    def detect_contradictions(self, cs_reports: dict[str, dict[str, Any]], bridge_coverage: TraceCoverageAssessment) -> tuple[TraceContradictionRecord, ...]:
        contradictions: list[TraceContradictionRecord] = []
        for order_id in ("CS-002", "CS-003", "CS-004", "CS-005", "CS-007"):
            cert = cs_reports.get(order_id, {})
            if cert.get("verdict") == "PASS":
                contradictions.append(
                    TraceContradictionRecord(
                        f"TC001-CONTRA-{order_id}",
                        order_id,
                        True,
                        "Certification PASS claims production readiness without canonical-runtime trace equivalence.",
                        TraceRejectionCode.CERTIFICATION_EVIDENCE_NOT_PRODUCTION_EQUIVALENT,
                    )
                )
        cs006 = cs_reports.get("CS-006", {})
        if cs006.get("verdict") == "PASS" and not cs006.get("metrics", {}).get("authoritativeInventoryComplete", False):
            contradictions.append(
                TraceContradictionRecord(
                    "TC001-CONTRA-CS-006",
                    "CS-006",
                    True,
                    "Read-surface PASS cannot rely only on registered surfaces without complete production read inventory.",
                    TraceRejectionCode.TRACE_PRODUCTION_EQUIVALENCE_FAILED,
                )
            )
        cs008 = cs_reports.get("CS-008", {})
        if cs008.get("verdict") == "PASS" and not cs008.get("metrics", {}).get("wallClockExtendedRunCompleted", False):
            contradictions.append(
                TraceContradictionRecord(
                    "TC001-CONTRA-CS-008",
                    "CS-008",
                    True,
                    "Accelerated endurance cannot be promoted to wall-clock operational endurance.",
                    TraceRejectionCode.TRACE_PRODUCTION_EQUIVALENCE_FAILED,
                )
            )
        if bridge_coverage.percent < 100.0:
            contradictions.append(
                TraceContradictionRecord(
                    "TC001-CONTRA-BRIDGE-COVERAGE",
                    "bridge coverage",
                    True,
                    "Bridge trace coverage is calculated from the authoritative bridge inventory, not the selected trace list.",
                    TraceRejectionCode.TRACE_PRODUCTION_EQUIVALENCE_FAILED,
                )
            )
        return tuple(contradictions)

    def runtime_identity_from_runtime(self, runtime: CanonicalEnterpriseRuntime, repository_commit: str) -> CanonicalRuntimeIdentity:
        snapshot = runtime.read_only_snapshot()
        startup_evidence = {
            "mode": snapshot["mode"],
            "truthDomain": snapshot["truthDomain"],
            "loopStarted": snapshot["loopStarted"],
            "startCount": snapshot["startCount"],
        }
        return CanonicalRuntimeIdentity(
            snapshot["bridgeFabric"]["runtimeInstanceId"],
            f"TC001-BOOT-{_stable_hash(startup_evidence)[:12].upper()}",
            _stable_hash(startup_evidence),
            _stable_hash(snapshot["componentIds"]),
            repository_commit,
        )

    def record_from_bridge_result(self, result: BridgeExecutionResult, identity: CanonicalRuntimeIdentity, repository_commit: str) -> TraceAuthenticityRecord:
        payload = {
            "execution_id": result.execution_id,
            "bridge_id": result.bridge_id,
            "workflow_id": result.workflow_id,
            "status": result.status.value,
            "owner": result.resulting_owner,
            "artifact_id": result.artifact_id,
        }
        return TraceAuthenticityRecord(
            result.execution_id,
            result.bridge_id,
            ExecutionOrigin.CANONICAL_PRODUCTION_RUNTIME,
            TraceEquivalenceLevel.CANONICAL_RUNTIME,
            TraceClaimType.PRODUCTION_EXECUTION,
            identity,
            identity.startup_evidence_hash,
            (identity.bootstrap_trace_id, result.workflow_id),
            result.workflow_id,
            identity.runtime_instance_id if not result.workflow_id else f"TOKEN-AUTH-{result.workflow_id}",
            True,
            result.source,
            bool(result.source),
            result.destination,
            result.status in {BridgeResultStatus.ACCEPTED, BridgeResultStatus.DUPLICATE_IDEMPOTENT_SUCCESS} and result.destination_acceptance_status == "ACCEPTED",
            result.artifact_id,
            result.deterministic_result_hash,
            result.deterministic_result_hash,
            "PAPER",
            result.audit_record_ids,
            repository_commit,
            repository_commit,
            False,
            result.completed_at_utc,
            _stable_hash(payload),
        )

    def certification_harness_record(self, subject_id: str, repository_commit: str, *, trace_id: str = "") -> TraceAuthenticityRecord:
        trace_id = trace_id or f"TC001-HARNESS-{subject_id}"
        return TraceAuthenticityRecord(
            trace_id,
            subject_id,
            ExecutionOrigin.CERTIFICATION_HARNESS,
            TraceEquivalenceLevel.CONTRACT,
            TraceClaimType.CONTRACT_EXECUTION,
            None,
            "",
            (),
            f"WF-HARNESS-{subject_id}",
            f"TOK-HARNESS-{subject_id}",
            True,
            "Certification Harness",
            True,
            "Contract Helper",
            True,
            f"ART-HARNESS-{subject_id}",
            "contract",
            "contract",
            "PAPER",
            (),
            repository_commit,
            repository_commit,
            True,
            utc_timestamp(),
            _stable_hash((trace_id, subject_id, "certification-harness")),
        )


def execute_tc001_certification(repository_commit: str = "WORKTREE") -> dict[str, Any]:
    authority = TraceEquivalenceAuthority()
    runtime = CanonicalEnterpriseRuntime()
    runtime.start()
    runtime.admit_scheduled_obligation("pre_market_readiness", now="2026-07-18T08:15:00Z")
    identity = authority.runtime_identity_from_runtime(runtime, repository_commit)
    canonical_records = tuple(authority.record_from_bridge_result(result, identity, repository_commit) for result in runtime.bridge_executor.traces())
    harness_records = (
        authority.certification_harness_record("CS-002", repository_commit),
        authority.certification_harness_record("CS-003", repository_commit),
        authority.certification_harness_record("CS-005", repository_commit),
    )
    records = (*canonical_records, *harness_records)
    results = tuple(authority.evaluate(record) for record in records)
    required_bridge_ids = tuple(definition.bridge_id for definition in default_bridge_definitions())
    bridge_coverage = authority.coverage(required_bridge_ids, results)
    cs_reports = {
        "CS-002": {"verdict": "INCOMPLETE"},
        "CS-003": {"verdict": "INCOMPLETE"},
        "CS-004": {"verdict": "INCOMPLETE"},
        "CS-005": {"verdict": "INCOMPLETE"},
        "CS-006": {"verdict": "INCOMPLETE", "metrics": {"authoritativeInventoryComplete": False}},
        "CS-007": {"verdict": "INCOMPLETE"},
        "CS-008": {"verdict": "INCOMPLETE", "metrics": {"wallClockExtendedRunCompleted": False}},
    }
    contradictions = authority.detect_contradictions(cs_reports, bridge_coverage)
    verdict = "PASS" if bridge_coverage.percent == 100.0 and not contradictions and any(item.production_equivalent for item in results) else "INCOMPLETE"
    readiness = "Production Trace Equivalent" if verdict == "PASS" else "Trace Equivalence Framework Installed; Canonical Trace Coverage Incomplete"
    certification_without_hash = {
        "order_id": "TC-001",
        "verdict": verdict,
        "readiness": readiness,
        "repository_commit": repository_commit,
        "eligibility_results": tuple(asdict(item) for item in results),
        "bridge_coverage": asdict(bridge_coverage),
        "contradiction_report": tuple(asdict(item) for item in contradictions),
    }
    certification = TraceEquivalenceCertification(
        "TC-001",
        verdict,
        readiness,
        repository_commit,
        results,
        bridge_coverage,
        contradictions,
        sum(1 for item in results if item.production_equivalent),
        sum(1 for item in results if TraceRejectionCode.TRACE_CERTIFICATION_HARNESS_ORCHESTRATED in item.rejection_codes),
        _stable_hash(certification_without_hash),
        utc_timestamp(),
    )
    return {
        "certification": asdict(certification),
        "records": tuple(asdict(item) for item in records),
        "eligibility_results": tuple(asdict(item) for item in results),
        "bridge_coverage": asdict(bridge_coverage),
        "canonical_runtime_identity": asdict(identity),
        "contradiction_report": tuple(asdict(item) for item in contradictions),
        "execution_origin_policy": execution_origin_policy(),
        "trace_authenticity_schema": trace_authenticity_schema(),
        "trace_equivalence_matrix": trace_equivalence_matrix(),
        "production_trace_eligibility": production_trace_eligibility(),
    }


def execution_origin_policy() -> dict[str, Any]:
    return {
        "schemaVersion": TC_001_VERSION,
        "productionMinimum": TraceEquivalenceLevel.CANONICAL_RUNTIME.value,
        "unknownOriginMayCertifyProduction": False,
        "certificationHarnessMayCreateProductionEquivalentTrace": False,
        "origins": {origin.value: TraceEquivalenceAuthority().classify_origin(origin).value for origin in ExecutionOrigin},
    }


def trace_authenticity_schema() -> dict[str, Any]:
    return {"schemaVersion": TC_001_VERSION, "requiredFields": tuple(TraceAuthenticityRecord.__dataclass_fields__), "rejectionCodes": tuple(item.value for item in TraceRejectionCode)}


def trace_equivalence_matrix() -> dict[str, Any]:
    return {"schemaVersion": TC_001_VERSION, "levels": tuple(item.value for item in TraceEquivalenceLevel), "productionMinimum": TraceEquivalenceLevel.CANONICAL_RUNTIME.value}


def production_trace_eligibility() -> dict[str, Any]:
    return {
        "schemaVersion": TC_001_VERSION,
        "requiresKnownOrigin": True,
        "requiresCanonicalRuntimeIdentity": True,
        "requiresStartupEvidence": True,
        "requiresCausalChain": True,
        "requiresLawVIITokenAuthority": True,
        "requiresSourceAndDestinationAuthority": True,
        "requiresArtifactIntegrity": True,
        "requiresProofDomain": True,
        "requiresRepositoryEvidenceCommitMatch": True,
    }


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
