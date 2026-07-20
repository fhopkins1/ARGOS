"""INF-006 Infrastructure governance and constitutional decision controls."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


INF_006_VERSION = "INF-006/1.0.0"


class GovernanceDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED_FAIL_CLOSED = "REJECTED_FAIL_CLOSED"


class GovernanceFailure(str, Enum):
    STALE_CERTIFICATION = "stale_certification"
    UNKNOWN_FAILURE_CLASSIFICATION = "unknown_failure_classification"
    INVALID_AUTHORITY_OVERRIDE = "invalid_authority_override"
    BEHAVIOR_CHANGE_DURING_FREEZE = "behavior_change_during_freeze"
    MISSING_EQUIVALENCE_EVIDENCE = "missing_equivalence_evidence"
    UNDER_SCOPED_REGRESSION = "under_scoped_regression"
    AMENDMENT_WITHOUT_AUTHORITY = "amendment_without_authority"
    IMPLEMENTATION_REDEFINED_GOVERNANCE = "implementation_redefined_governance"
    MISSING_RECERTIFICATION_REQUIREMENT = "missing_recertification_requirement"


class ConstitutionalInput(str, Enum):
    DOCTRINE = "doctrine"
    CODE = "code"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    BRIDGE = "bridge"
    AUTHORITY = "authority"
    PERSISTENCE = "persistence"
    REPLAY = "replay"
    TEST_DENOMINATOR = "test_denominator"
    EVIDENCE_SCHEMA = "evidence_schema"


class FailureResponseClass(str, Enum):
    AUTOMATIC_RECOVERY = "automatic_recovery"
    AUTOMATIC_RETRY = "automatic_retry"
    QUARANTINE = "quarantine"
    DEGRADED_READ_ONLY_OPERATION = "degraded_read_only_operation"
    HALT = "halt"


class AuthorityTier(str, Enum):
    CONSTITUTION = "constitution"
    CERTIFIED_INFRASTRUCTURE = "certified_infrastructure"
    CERTIFICATION_AUTHORITY = "certification_authority"
    WORKFLOW_TOKEN = "workflow_token"
    OFFICE = "office"
    RUNTIME = "runtime"
    MONITORING = "monitoring"
    REPORTING = "reporting"


class FreezeChangeClass(str, Enum):
    DOCUMENTATION = "documentation"
    IMPLEMENTATION = "implementation"
    BEHAVIOR = "behavior"
    CONSTITUTIONAL_LAW = "constitutional_law"


class RegressionScope(str, Enum):
    NONE = "none"
    LOCAL = "local"
    OFFICE = "office"
    INFRASTRUCTURE = "infrastructure"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class CertificationFreshnessRecord:
    certification_id: str
    certified_state_hash: str
    current_state_hash: str
    changed_inputs: tuple[ConstitutionalInput, ...]


@dataclass(frozen=True)
class FailureEvent:
    failure_id: str
    classification: FailureResponseClass | None
    evidence_reference: str


@dataclass(frozen=True)
class AuthorityAction:
    acting_tier: AuthorityTier
    affected_tier: AuthorityTier
    action: str


@dataclass(frozen=True)
class FreezeChangeRequest:
    change_id: str
    change_class: FreezeChangeClass
    behavioral_equivalence_evidence: str
    constitutional_amendment_authorized: bool = False


@dataclass(frozen=True)
class RegressionAssessment:
    changed_inputs: tuple[ConstitutionalInput, ...]
    requested_scope: RegressionScope
    uncertainty: bool


@dataclass(frozen=True)
class AmendmentRecord:
    amendment_id: str
    governance_authority: str
    rationale: str
    history_reference: str
    affected_doctrine: tuple[str, ...]
    affected_guarantees: tuple[str, ...]
    mandatory_recertification_scope: RegressionScope | None
    implementation_changes_governance: bool = False


@dataclass(frozen=True)
class GovernanceReview:
    decision: GovernanceDecision
    failures: tuple[GovernanceFailure, ...]


class InfrastructureGovernanceDoctrine:
    """Deterministic INF governance validator."""

    authority_order = (
        AuthorityTier.CONSTITUTION,
        AuthorityTier.CERTIFIED_INFRASTRUCTURE,
        AuthorityTier.CERTIFICATION_AUTHORITY,
        AuthorityTier.WORKFLOW_TOKEN,
        AuthorityTier.OFFICE,
        AuthorityTier.RUNTIME,
        AuthorityTier.MONITORING,
        AuthorityTier.REPORTING,
    )
    input_scope = {
        ConstitutionalInput.DOCTRINE: RegressionScope.ENTERPRISE,
        ConstitutionalInput.CODE: RegressionScope.INFRASTRUCTURE,
        ConstitutionalInput.CONFIGURATION: RegressionScope.INFRASTRUCTURE,
        ConstitutionalInput.DEPENDENCY: RegressionScope.INFRASTRUCTURE,
        ConstitutionalInput.BRIDGE: RegressionScope.INFRASTRUCTURE,
        ConstitutionalInput.AUTHORITY: RegressionScope.INFRASTRUCTURE,
        ConstitutionalInput.PERSISTENCE: RegressionScope.INFRASTRUCTURE,
        ConstitutionalInput.REPLAY: RegressionScope.INFRASTRUCTURE,
        ConstitutionalInput.TEST_DENOMINATOR: RegressionScope.INFRASTRUCTURE,
        ConstitutionalInput.EVIDENCE_SCHEMA: RegressionScope.INFRASTRUCTURE,
    }

    def certification_freshness(self, record: CertificationFreshnessRecord) -> GovernanceReview:
        failures = []
        if record.certified_state_hash != record.current_state_hash or record.changed_inputs:
            failures.append(GovernanceFailure.STALE_CERTIFICATION)
        return _review(failures)

    def failure_response(self, event: FailureEvent) -> tuple[FailureResponseClass, GovernanceReview]:
        if event.classification is None:
            return FailureResponseClass.HALT, _review((GovernanceFailure.UNKNOWN_FAILURE_CLASSIFICATION,))
        return event.classification, _review(())

    def authority_action(self, action: AuthorityAction) -> GovernanceReview:
        ranks = {tier: index for index, tier in enumerate(self.authority_order)}
        failures = []
        if ranks[action.acting_tier] > ranks[action.affected_tier]:
            failures.append(GovernanceFailure.INVALID_AUTHORITY_OVERRIDE)
        return _review(failures)

    def freeze_change(self, request: FreezeChangeRequest) -> GovernanceReview:
        failures = []
        if request.change_class in {FreezeChangeClass.IMPLEMENTATION, FreezeChangeClass.BEHAVIOR} and not request.behavioral_equivalence_evidence:
            failures.append(GovernanceFailure.MISSING_EQUIVALENCE_EVIDENCE)
        if request.change_class == FreezeChangeClass.BEHAVIOR and not request.constitutional_amendment_authorized:
            failures.append(GovernanceFailure.BEHAVIOR_CHANGE_DURING_FREEZE)
        if request.change_class == FreezeChangeClass.CONSTITUTIONAL_LAW and not request.constitutional_amendment_authorized:
            failures.append(GovernanceFailure.AMENDMENT_WITHOUT_AUTHORITY)
        return _review(failures)

    def regression_scope(self, assessment: RegressionAssessment) -> tuple[RegressionScope, GovernanceReview]:
        required = RegressionScope.NONE
        for changed_input in assessment.changed_inputs:
            required = _max_scope(required, self.input_scope[changed_input])
        if assessment.uncertainty:
            required = _max_scope(required, RegressionScope.ENTERPRISE)
        failures = []
        if _scope_rank(assessment.requested_scope) < _scope_rank(required):
            failures.append(GovernanceFailure.UNDER_SCOPED_REGRESSION)
        return required, _review(failures)

    def amendment(self, record: AmendmentRecord) -> GovernanceReview:
        failures = []
        if not record.governance_authority or not record.rationale or not record.history_reference:
            failures.append(GovernanceFailure.AMENDMENT_WITHOUT_AUTHORITY)
        if record.implementation_changes_governance:
            failures.append(GovernanceFailure.IMPLEMENTATION_REDEFINED_GOVERNANCE)
        if record.mandatory_recertification_scope is None:
            failures.append(GovernanceFailure.MISSING_RECERTIFICATION_REQUIREMENT)
        return _review(failures)


def _review(failures: Iterable[GovernanceFailure]) -> GovernanceReview:
    unique = tuple(dict.fromkeys(failures))
    return GovernanceReview(GovernanceDecision.APPROVED if not unique else GovernanceDecision.REJECTED_FAIL_CLOSED, unique)


def _scope_rank(scope: RegressionScope) -> int:
    return list(RegressionScope).index(scope)


def _max_scope(left: RegressionScope, right: RegressionScope) -> RegressionScope:
    return left if _scope_rank(left) >= _scope_rank(right) else right
