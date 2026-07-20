"""INF-005 Infrastructure certification doctrine controls."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


INF_005_VERSION = "INF-005/1.0.0"


class InfrastructureCertificationLifecycleState(str, Enum):
    NOT_CERTIFIED = "Not Certified"
    PROVISIONALLY_CERTIFIED = "Provisionally Certified"
    CONSTITUTIONALLY_CERTIFIED = "Constitutionally Certified"
    CERTIFICATION_REVOKED = "Certification Revoked"


class InfrastructureCertificationPhase(str, Enum):
    CONSTRUCTION_VERIFICATION = "Infrastructure Construction Verification"
    IDENTITY_VERIFICATION = "Identity Verification"
    AUTHORITY_VERIFICATION = "Authority Verification"
    BRIDGE_CERTIFICATION = "Bridge Certification"
    RUNTIME_CERTIFICATION = "Runtime Certification"
    PERSISTENCE_CERTIFICATION = "Persistence Certification"
    RECOVERY_CERTIFICATION = "Recovery Certification"
    REPLAY_CERTIFICATION = "Replay Certification"
    EVIDENCE_CERTIFICATION = "Evidence Certification"
    PROOF_CERTIFICATION = "Proof Certification"
    SYNTHETIC_TRUTH_CERTIFICATION = "Synthetic Truth Certification"
    CONSTITUTIONAL_ACCEPTANCE = "Constitutional Acceptance"


class InfrastructureTestCategory(str, Enum):
    IDENTITY = "Identity Testing"
    AUTHORITY = "Authority Testing"
    REPOSITORY = "Repository Testing"
    CANDIDATE = "Candidate Testing"
    BRIDGE = "Bridge Testing"
    DEPENDENCY = "Dependency Testing"
    RUNTIME = "Runtime Testing"
    PERSISTENCE = "Persistence Testing"
    REPLAY = "Replay Testing"
    RECOVERY = "Recovery Testing"
    WORKFLOW = "Workflow Testing"
    TOKEN = "Token Testing"
    SCHEDULER = "Scheduler Testing"
    AUDIT = "Audit Testing"
    EVIDENCE = "Evidence Testing"
    HEALTH = "Health Testing"
    SYNTHETIC_TRUTH_PREVENTION = "Synthetic Truth Prevention Testing"
    FAILURE_INJECTION = "Failure Injection Testing"
    REGRESSION = "Regression Testing"
    CERTIFICATION = "Certification Testing"
    CROSS_OFFICE_DEPENDENCY = "Cross-Office Dependency Testing"


class InfrastructureCertificationFailure(str, Enum):
    MISSING_PHASE = "missing_phase"
    MISSING_TEST_CATEGORY = "missing_test_category"
    MISSING_EVIDENCE = "missing_evidence"
    MISSING_PROOF = "missing_proof"
    NON_REPRODUCIBLE_PROOF = "non_reproducible_proof"
    FAIL_CLOSED_NOT_EXERCISED = "fail_closed_not_exercised"
    REVOCATION_TRIGGER = "revocation_trigger"
    PARTIAL_CERTIFICATION_ATTEMPT = "partial_certification_attempt"


@dataclass(frozen=True)
class InfrastructureCertificationEvidence:
    evidence_id: str
    phase: InfrastructureCertificationPhase
    test_category: InfrastructureTestCategory
    immutable: bool
    proof_id: str
    proof_reproducible: bool
    fail_closed_exercised: bool
    passed: bool


@dataclass(frozen=True)
class InfrastructureCertificationDecision:
    state: InfrastructureCertificationLifecycleState
    failures: tuple[InfrastructureCertificationFailure, ...]
    operational_certification_allowed: bool
    dependent_operational_certifications_suspended: bool


class InfrastructureCertificationDoctrineEngine:
    """Executes the INF-005 certification gate across all phases and categories."""

    revocation_triggers = {
        "authority_violation",
        "uncertified_bridge",
        "failed_replay",
        "failed_recovery",
        "failed_persistence",
        "synthetic_truth",
        "candidate_identity_inconsistency",
        "repository_identity_inconsistency",
        "constitutional_invariant_violation",
        "missing_evidence",
        "missing_proof",
        "audit_corruption",
        "runtime_nondeterminism",
    }

    def certify(
        self,
        evidence: Iterable[InfrastructureCertificationEvidence],
        discovered_violations: Iterable[str] = (),
        provisional_requested: bool = False,
    ) -> InfrastructureCertificationDecision:
        evidence_items = tuple(evidence)
        failures: list[InfrastructureCertificationFailure] = []
        phase_set = {item.phase for item in evidence_items if item.passed}
        category_set = {item.test_category for item in evidence_items if item.passed}

        if set(phase_set) != set(InfrastructureCertificationPhase):
            failures.append(InfrastructureCertificationFailure.MISSING_PHASE)
        if set(category_set) != set(InfrastructureTestCategory):
            failures.append(InfrastructureCertificationFailure.MISSING_TEST_CATEGORY)
        if any(not item.immutable or not item.evidence_id for item in evidence_items):
            failures.append(InfrastructureCertificationFailure.MISSING_EVIDENCE)
        if any(not item.proof_id for item in evidence_items):
            failures.append(InfrastructureCertificationFailure.MISSING_PROOF)
        if any(not item.proof_reproducible for item in evidence_items):
            failures.append(InfrastructureCertificationFailure.NON_REPRODUCIBLE_PROOF)
        if any(not item.fail_closed_exercised for item in evidence_items):
            failures.append(InfrastructureCertificationFailure.FAIL_CLOSED_NOT_EXERCISED)
        if provisional_requested:
            failures.append(InfrastructureCertificationFailure.PARTIAL_CERTIFICATION_ATTEMPT)
        if set(discovered_violations) & self.revocation_triggers:
            failures.append(InfrastructureCertificationFailure.REVOCATION_TRIGGER)

        unique_failures = tuple(dict.fromkeys(failures))
        if InfrastructureCertificationFailure.REVOCATION_TRIGGER in unique_failures:
            state = InfrastructureCertificationLifecycleState.CERTIFICATION_REVOKED
        elif unique_failures:
            state = InfrastructureCertificationLifecycleState.NOT_CERTIFIED
        else:
            state = InfrastructureCertificationLifecycleState.CONSTITUTIONALLY_CERTIFIED
        return InfrastructureCertificationDecision(
            state=state,
            failures=unique_failures,
            operational_certification_allowed=state == InfrastructureCertificationLifecycleState.CONSTITUTIONALLY_CERTIFIED,
            dependent_operational_certifications_suspended=state != InfrastructureCertificationLifecycleState.CONSTITUTIONALLY_CERTIFIED,
        )
