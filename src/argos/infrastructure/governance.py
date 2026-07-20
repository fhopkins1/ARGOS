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
    MULTIPLE_ACTIVE_VERSIONS = "multiple_active_versions"
    SUPERSEDED_VERSION_MISSING = "superseded_version_missing"
    UNRESOLVED_CONFLICT = "unresolved_conflict"
    MISSING_DEPENDENCY_GRAPH = "missing_dependency_graph"
    CERTIFICATION_DEPENDENCY_CHANGED = "certification_dependency_changed"
    MISSING_FAILURE_CLASSIFICATION_METADATA = "missing_failure_classification_metadata"
    ORPHANED_REQUIREMENT = "orphaned_requirement"
    ILLEGAL_AMENDMENT_TRANSITION = "illegal_amendment_transition"
    UNAUTHORIZED_AMENDMENT = "unauthorized_amendment"
    UNCERTIFIED_DOCTRINE_RUNTIME_USE = "uncertified_doctrine_runtime_use"


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


class DoctrineStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


class ConflictResolutionStep(str, Enum):
    INVARIANT_PRECEDENCE = "invariant_precedence"
    AUTHORITY_HIERARCHY = "authority_hierarchy"
    MORE_RESTRICTIVE_BEHAVIOR = "more_restrictive_behavior"
    FORMAL_AMENDMENT_REQUIRED = "formal_amendment_required"


class AmendmentLifecycleState(str, Enum):
    DRAFT = "draft"
    COMMITTEE_REVIEW = "committee_review"
    APPROVED = "approved"
    EFFECTIVE = "effective"
    SUPERSEDED = "superseded"


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


class FreezeStatus(str, Enum):
    FROZEN = "frozen"
    NOT_FROZEN = "not_frozen"


class CertificationValidity(str, Enum):
    VALID = "valid"
    INVALID = "invalid"


class ChangeClassification(str, Enum):
    DOCUMENTATION = "documentation"
    REFACTOR = "refactor"
    BEHAVIOR = "behavior"
    CONSTITUTION = "constitution"
    UNKNOWN = "unknown"


class EquivalenceResult(str, Enum):
    EQUIVALENT = "equivalent"
    NOT_EQUIVALENT = "not_equivalent"
    UNABLE_TO_DETERMINE = "unable_to_determine"


@dataclass(frozen=True)
class CertificationFreezeState:
    certification_id: str
    certification_timestamp: str
    certified_doctrine_version: str
    certified_repository_hash: str
    certified_bridge_registry_version: str
    certified_authority_model_version: str
    certified_runtime_version: str
    freeze_status: FreezeStatus
    certification_status: CertificationValidity
    invalidation_reason: str


@dataclass(frozen=True)
class ChangeRequest:
    change_id: str
    changed_paths: tuple[str, ...]
    affected_guarantees: tuple[str, ...]
    constitutional_amendment: bool = False
    explicit_behavioral_change: bool = False


@dataclass(frozen=True)
class BehavioralEquivalenceEvidence:
    certified_behavior_hash: str
    runtime_behavior_hash: str
    authority_transition_hash: str
    audit_record_hash: str
    persistence_hash: str
    replay_hash: str
    constitutional_output_hash: str


@dataclass(frozen=True)
class FreezeAuditEntry:
    change_id: str
    classification: ChangeClassification
    equivalence: EquivalenceResult
    certification_decision: CertificationValidity
    freeze_state: CertificationFreezeState
    evidence_reference: str


@dataclass(frozen=True)
class FreezeDecision:
    classification: ChangeClassification
    equivalence: EquivalenceResult
    certification_status: CertificationValidity
    failures: tuple[GovernanceFailure, ...]
    audit_entry: FreezeAuditEntry


@dataclass(frozen=True)
class RegressionAssessment:
    changed_inputs: tuple[ConstitutionalInput, ...]
    requested_scope: RegressionScope
    uncertainty: bool


@dataclass(frozen=True)
class ModificationImpact:
    modification_id: str
    changed_files: tuple[str, ...]
    affected_guarantees: tuple[ConstitutionalInput, ...]
    direct_dependencies: tuple[str, ...]
    indirect_dependencies: tuple[str, ...]
    evidence_reference: str
    behavioral_change: bool = False
    dependency_analysis_complete: bool = True
    deterministic_confidence: bool = True


@dataclass(frozen=True)
class RegressionRecord:
    regression_id: str
    modification_id: str
    repository_revision: str
    affected_doctrine: tuple[str, ...]
    affected_guarantees: tuple[ConstitutionalInput, ...]
    dependency_expansion_results: tuple[str, ...]
    selected_recertification_scope: RegressionScope
    escalation_history: tuple[RegressionScope, ...]
    deterministic_evidence: str
    certifying_authority: str
    failures: tuple[GovernanceFailure, ...]


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
class DoctrineVersionRecord:
    doctrine_id: str
    semantic_version: str
    adoption_timestamp: str
    status: DoctrineStatus
    supersedes: tuple[str, ...]
    historical_reference: str


@dataclass(frozen=True)
class CertificationDependency:
    dependency_id: str
    dependency_type: ConstitutionalInput
    certified_hash: str
    current_hash: str


@dataclass(frozen=True)
class CertificationDependencyGraph:
    certification_id: str
    immutable_graph_hash: str
    dependencies: tuple[CertificationDependency, ...]


@dataclass(frozen=True)
class FailureClassificationPolicy:
    classification: FailureResponseClass
    recovery_eligible: bool
    retry_eligible: bool
    quarantine_eligible: bool
    certification_impact: RegressionScope
    audit_severity: str
    operator_notification_required: bool


@dataclass(frozen=True)
class ConflictCase:
    conflict_id: str
    left_authority: AuthorityTier
    right_authority: AuthorityTier
    invariant_implicated: bool
    left_restriction_rank: int
    right_restriction_rank: int
    deterministic_evidence: str


@dataclass(frozen=True)
class ConflictResolution:
    decision: GovernanceDecision
    failures: tuple[GovernanceFailure, ...]
    winning_authority: AuthorityTier | None
    selected_step: ConflictResolutionStep


@dataclass(frozen=True)
class RequirementTraceRecord:
    requirement_id: str
    originating_doctrine: str
    implementing_modification_orders: tuple[str, ...]
    implementation_evidence: tuple[str, ...]
    certification_evidence: tuple[str, ...]
    audit_findings: tuple[str, ...]


@dataclass(frozen=True)
class GovernanceInvariantSet:
    invariants: tuple[str, ...]


@dataclass(frozen=True)
class AmendmentRegistryRecord:
    amendment_id: str
    amendment_title: str
    amendment_type: str
    amendment_status: AmendmentLifecycleState
    authorizing_committee: str
    amendment_timestamp: str
    effective_date: str
    constitutional_version_before: str
    constitutional_version_after: str
    rationale: str
    affected_doctrine: tuple[str, ...]
    affected_guarantees: tuple[str, ...]
    required_certification_scope: RegressionScope
    certification_status: str
    approval_evidence: str
    audit_references: tuple[str, ...]
    consistency_validated: bool


@dataclass(frozen=True)
class AmendmentRegistryDecision:
    decision: GovernanceDecision
    failures: tuple[GovernanceFailure, ...]
    new_version: str | None
    recertification_required: bool


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

    def certification_dependency_graph(self, graph: CertificationDependencyGraph) -> GovernanceReview:
        failures = []
        if not graph.immutable_graph_hash or not graph.dependencies:
            failures.append(GovernanceFailure.MISSING_DEPENDENCY_GRAPH)
        if any(item.certified_hash != item.current_hash for item in graph.dependencies):
            failures.append(GovernanceFailure.CERTIFICATION_DEPENDENCY_CHANGED)
        return _review(failures)

    def doctrine_versions(self, versions: Iterable[DoctrineVersionRecord]) -> GovernanceReview:
        records = tuple(versions)
        active = [item for item in records if item.status == DoctrineStatus.ACTIVE]
        failures = []
        if len(active) != 1:
            failures.append(GovernanceFailure.MULTIPLE_ACTIVE_VERSIONS)
        for item in records:
            if item.status == DoctrineStatus.SUPERSEDED and not item.historical_reference:
                failures.append(GovernanceFailure.SUPERSEDED_VERSION_MISSING)
        return _review(failures)

    def failure_response(self, event: FailureEvent) -> tuple[FailureResponseClass, GovernanceReview]:
        if event.classification is None:
            return FailureResponseClass.HALT, _review((GovernanceFailure.UNKNOWN_FAILURE_CLASSIFICATION,))
        return event.classification, _review(())

    def failure_classification_policy(self, policy: FailureClassificationPolicy) -> GovernanceReview:
        failures = []
        if policy.certification_impact is None or not policy.audit_severity or policy.operator_notification_required is None:
            failures.append(GovernanceFailure.MISSING_FAILURE_CLASSIFICATION_METADATA)
        return _review(failures)

    def authority_action(self, action: AuthorityAction) -> GovernanceReview:
        ranks = {tier: index for index, tier in enumerate(self.authority_order)}
        failures = []
        if ranks[action.acting_tier] > ranks[action.affected_tier]:
            failures.append(GovernanceFailure.INVALID_AUTHORITY_OVERRIDE)
        return _review(failures)

    def resolve_conflict(self, case: ConflictCase) -> ConflictResolution:
        ranks = {tier: index for index, tier in enumerate(self.authority_order)}
        if not case.deterministic_evidence:
            return ConflictResolution(
                GovernanceDecision.REJECTED_FAIL_CLOSED,
                (GovernanceFailure.UNRESOLVED_CONFLICT,),
                None,
                ConflictResolutionStep.FORMAL_AMENDMENT_REQUIRED,
            )
        if case.invariant_implicated:
            winner = case.left_authority if ranks[case.left_authority] <= ranks[case.right_authority] else case.right_authority
            return ConflictResolution(GovernanceDecision.APPROVED, (), winner, ConflictResolutionStep.INVARIANT_PRECEDENCE)
        if ranks[case.left_authority] != ranks[case.right_authority]:
            winner = case.left_authority if ranks[case.left_authority] < ranks[case.right_authority] else case.right_authority
            return ConflictResolution(GovernanceDecision.APPROVED, (), winner, ConflictResolutionStep.AUTHORITY_HIERARCHY)
        if case.left_restriction_rank != case.right_restriction_rank:
            winner = case.left_authority if case.left_restriction_rank > case.right_restriction_rank else case.right_authority
            return ConflictResolution(GovernanceDecision.APPROVED, (), winner, ConflictResolutionStep.MORE_RESTRICTIVE_BEHAVIOR)
        return ConflictResolution(
            GovernanceDecision.REJECTED_FAIL_CLOSED,
            (GovernanceFailure.UNRESOLVED_CONFLICT,),
            None,
            ConflictResolutionStep.FORMAL_AMENDMENT_REQUIRED,
        )

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

    def traceability(self, records: Iterable[RequirementTraceRecord]) -> GovernanceReview:
        failures = []
        for item in records:
            if not item.originating_doctrine or not item.implementing_modification_orders or not item.implementation_evidence or not item.certification_evidence:
                failures.append(GovernanceFailure.ORPHANED_REQUIREMENT)
        return _review(failures)

    def invariant_set(self) -> GovernanceInvariantSet:
        return GovernanceInvariantSet(
            (
                "immutable_constitutional_history",
                "deterministic_governance",
                "deterministic_authority_delegation",
                "certification_reproducibility",
                "constitutional_traceability",
                "constitutional_dependency_determinism",
                "constitutional_version_integrity",
            )
        )

    def amendment(self, record: AmendmentRecord) -> GovernanceReview:
        failures = []
        if not record.governance_authority or not record.rationale or not record.history_reference:
            failures.append(GovernanceFailure.AMENDMENT_WITHOUT_AUTHORITY)
        if record.implementation_changes_governance:
            failures.append(GovernanceFailure.IMPLEMENTATION_REDEFINED_GOVERNANCE)
        if record.mandatory_recertification_scope is None:
            failures.append(GovernanceFailure.MISSING_RECERTIFICATION_REQUIREMENT)
        return _review(failures)


class ChangeClassifier:
    """Classifies frozen infrastructure changes without human interpretation."""

    documentation_suffixes = (".md", ".rst", ".txt", ".png", ".svg")

    def classify(self, request: ChangeRequest) -> ChangeClassification:
        if request.constitutional_amendment:
            return ChangeClassification.CONSTITUTION
        if request.explicit_behavioral_change:
            return ChangeClassification.BEHAVIOR
        if not request.changed_paths:
            return ChangeClassification.UNKNOWN
        if all(path.lower().endswith(self.documentation_suffixes) for path in request.changed_paths):
            return ChangeClassification.DOCUMENTATION
        if request.affected_guarantees:
            return ChangeClassification.BEHAVIOR
        return ChangeClassification.REFACTOR


class BehavioralEquivalenceVerifier:
    """Proves behavioral equivalence through deterministic evidence hashes."""

    def verify(self, evidence: BehavioralEquivalenceEvidence | None) -> EquivalenceResult:
        if evidence is None:
            return EquivalenceResult.UNABLE_TO_DETERMINE
        pairs = (
            (evidence.certified_behavior_hash, evidence.runtime_behavior_hash),
            (evidence.certified_behavior_hash, evidence.constitutional_output_hash),
            (evidence.authority_transition_hash, evidence.audit_record_hash),
            (evidence.persistence_hash, evidence.replay_hash),
        )
        if any(not left or not right for left, right in pairs):
            return EquivalenceResult.UNABLE_TO_DETERMINE
        return EquivalenceResult.EQUIVALENT if all(left == right for left, right in pairs) else EquivalenceResult.NOT_EQUIVALENT


class FreezeManager:
    """INF-MO-011 constitutional freeze enforcement system."""

    def __init__(self, classifier: ChangeClassifier | None = None, verifier: BehavioralEquivalenceVerifier | None = None) -> None:
        self.classifier = classifier or ChangeClassifier()
        self.verifier = verifier or BehavioralEquivalenceVerifier()
        self._audit: tuple[FreezeAuditEntry, ...] = ()

    @property
    def audit_history(self) -> tuple[FreezeAuditEntry, ...]:
        return self._audit

    def evaluate(
        self,
        state: CertificationFreezeState,
        request: ChangeRequest,
        equivalence_evidence: BehavioralEquivalenceEvidence | None = None,
    ) -> tuple[CertificationFreezeState, FreezeDecision]:
        classification = self.classifier.classify(request)
        equivalence = self.verifier.verify(equivalence_evidence)
        failures: list[GovernanceFailure] = []
        next_status = state.certification_status
        reason = state.invalidation_reason
        if classification == ChangeClassification.DOCUMENTATION:
            next_status = CertificationValidity.VALID
            reason = ""
        elif classification == ChangeClassification.REFACTOR and equivalence == EquivalenceResult.EQUIVALENT:
            next_status = CertificationValidity.VALID
            reason = ""
        elif classification in {ChangeClassification.BEHAVIOR, ChangeClassification.CONSTITUTION, ChangeClassification.UNKNOWN}:
            next_status = CertificationValidity.INVALID
            reason = classification.value
            failures.append(GovernanceFailure.BEHAVIOR_CHANGE_DURING_FREEZE)
        else:
            next_status = CertificationValidity.INVALID
            reason = equivalence.value
            failures.append(GovernanceFailure.MISSING_EQUIVALENCE_EVIDENCE)
        next_state = CertificationFreezeState(
            certification_id=state.certification_id,
            certification_timestamp=state.certification_timestamp,
            certified_doctrine_version=state.certified_doctrine_version,
            certified_repository_hash=state.certified_repository_hash,
            certified_bridge_registry_version=state.certified_bridge_registry_version,
            certified_authority_model_version=state.certified_authority_model_version,
            certified_runtime_version=state.certified_runtime_version,
            freeze_status=FreezeStatus.FROZEN,
            certification_status=next_status,
            invalidation_reason=reason,
        )
        entry = FreezeAuditEntry(
            change_id=request.change_id,
            classification=classification,
            equivalence=equivalence,
            certification_decision=next_status,
            freeze_state=next_state,
            evidence_reference=equivalence_evidence.certified_behavior_hash if equivalence_evidence else "",
        )
        self._audit = self._audit + (entry,)
        return next_state, FreezeDecision(classification, equivalence, next_status, tuple(dict.fromkeys(failures)), entry)

    def restore_after_recertification(self, state: CertificationFreezeState, certification_timestamp: str) -> CertificationFreezeState:
        return CertificationFreezeState(
            certification_id=state.certification_id,
            certification_timestamp=certification_timestamp,
            certified_doctrine_version=state.certified_doctrine_version,
            certified_repository_hash=state.certified_repository_hash,
            certified_bridge_registry_version=state.certified_bridge_registry_version,
            certified_authority_model_version=state.certified_authority_model_version,
            certified_runtime_version=state.certified_runtime_version,
            freeze_status=FreezeStatus.FROZEN,
            certification_status=CertificationValidity.VALID,
            invalidation_reason="",
        )


class RegressionClassificationEngine:
    """INF-MO-014 deterministic regression classification engine."""

    guarantee_scope = InfrastructureGovernanceDoctrine.input_scope

    def classify(self, impact: ModificationImpact, requested_scope: RegressionScope | None = None) -> RegressionRecord:
        failures: list[GovernanceFailure] = []
        selected = RegressionScope.NONE
        escalation: list[RegressionScope] = []
        for guarantee in impact.affected_guarantees:
            selected = _max_scope(selected, self.guarantee_scope[guarantee])
        if impact.behavioral_change and selected == RegressionScope.NONE:
            selected = RegressionScope.LOCAL
        if any(item.startswith("enterprise:") for item in impact.direct_dependencies + impact.indirect_dependencies):
            selected = _max_scope(selected, RegressionScope.ENTERPRISE)
        elif impact.direct_dependencies or impact.indirect_dependencies:
            selected = _max_scope(selected, RegressionScope.OFFICE)
        if not impact.dependency_analysis_complete:
            failures.append(GovernanceFailure.MISSING_DEPENDENCY_GRAPH)
            selected = _escalate(selected, escalation)
        if not impact.deterministic_confidence or not impact.evidence_reference:
            failures.append(GovernanceFailure.UNDER_SCOPED_REGRESSION)
            selected = RegressionScope.ENTERPRISE
            escalation.append(RegressionScope.ENTERPRISE)
        if requested_scope is not None and _scope_rank(requested_scope) < _scope_rank(selected):
            failures.append(GovernanceFailure.UNDER_SCOPED_REGRESSION)
        return RegressionRecord(
            regression_id=f"REG-{impact.modification_id}",
            modification_id=impact.modification_id,
            repository_revision="HEAD",
            affected_doctrine=("INF-GOV-014",),
            affected_guarantees=impact.affected_guarantees,
            dependency_expansion_results=impact.direct_dependencies + impact.indirect_dependencies,
            selected_recertification_scope=selected,
            escalation_history=tuple(escalation),
            deterministic_evidence=impact.evidence_reference,
            certifying_authority="Infrastructure Certification Authority",
            failures=tuple(dict.fromkeys(failures)),
        )

    def certification_dependency_graph(self, graph: CertificationDependencyGraph) -> GovernanceReview:
        failures = []
        if not graph.immutable_graph_hash or not graph.dependencies:
            failures.append(GovernanceFailure.MISSING_DEPENDENCY_GRAPH)
        if any(item.certified_hash != item.current_hash for item in graph.dependencies):
            failures.append(GovernanceFailure.CERTIFICATION_DEPENDENCY_CHANGED)
        return _review(failures)

    def doctrine_versions(self, versions: Iterable[DoctrineVersionRecord]) -> GovernanceReview:
        records = tuple(versions)
        active = [item for item in records if item.status == DoctrineStatus.ACTIVE]
        failures = []
        if len(active) != 1:
            failures.append(GovernanceFailure.MULTIPLE_ACTIVE_VERSIONS)
        for item in records:
            if item.status == DoctrineStatus.SUPERSEDED and not item.historical_reference:
                failures.append(GovernanceFailure.SUPERSEDED_VERSION_MISSING)
        return _review(failures)

    def failure_response(self, event: FailureEvent) -> tuple[FailureResponseClass, GovernanceReview]:
        if event.classification is None:
            return FailureResponseClass.HALT, _review((GovernanceFailure.UNKNOWN_FAILURE_CLASSIFICATION,))
        return event.classification, _review(())

    def failure_classification_policy(self, policy: FailureClassificationPolicy) -> GovernanceReview:
        failures = []
        if (
            policy.certification_impact is None
            or not policy.audit_severity
            or policy.operator_notification_required is None
        ):
            failures.append(GovernanceFailure.MISSING_FAILURE_CLASSIFICATION_METADATA)
        return _review(failures)

    def authority_action(self, action: AuthorityAction) -> GovernanceReview:
        ranks = {tier: index for index, tier in enumerate(self.authority_order)}
        failures = []
        if ranks[action.acting_tier] > ranks[action.affected_tier]:
            failures.append(GovernanceFailure.INVALID_AUTHORITY_OVERRIDE)
        return _review(failures)

    def resolve_conflict(self, case: ConflictCase) -> ConflictResolution:
        ranks = {tier: index for index, tier in enumerate(self.authority_order)}
        failures: list[GovernanceFailure] = []
        if not case.deterministic_evidence:
            failures.append(GovernanceFailure.UNRESOLVED_CONFLICT)
            return ConflictResolution(
                GovernanceDecision.REJECTED_FAIL_CLOSED,
                tuple(failures),
                None,
                ConflictResolutionStep.FORMAL_AMENDMENT_REQUIRED,
            )
        if case.invariant_implicated:
            winner = case.left_authority if ranks[case.left_authority] <= ranks[case.right_authority] else case.right_authority
            return ConflictResolution(GovernanceDecision.APPROVED, (), winner, ConflictResolutionStep.INVARIANT_PRECEDENCE)
        if ranks[case.left_authority] != ranks[case.right_authority]:
            winner = case.left_authority if ranks[case.left_authority] < ranks[case.right_authority] else case.right_authority
            return ConflictResolution(GovernanceDecision.APPROVED, (), winner, ConflictResolutionStep.AUTHORITY_HIERARCHY)
        if case.left_restriction_rank != case.right_restriction_rank:
            winner = case.left_authority if case.left_restriction_rank > case.right_restriction_rank else case.right_authority
            return ConflictResolution(GovernanceDecision.APPROVED, (), winner, ConflictResolutionStep.MORE_RESTRICTIVE_BEHAVIOR)
        return ConflictResolution(
            GovernanceDecision.REJECTED_FAIL_CLOSED,
            (GovernanceFailure.UNRESOLVED_CONFLICT,),
            None,
            ConflictResolutionStep.FORMAL_AMENDMENT_REQUIRED,
        )

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

    def traceability(self, records: Iterable[RequirementTraceRecord]) -> GovernanceReview:
        failures = []
        for item in records:
            if (
                not item.originating_doctrine
                or not item.implementing_modification_orders
                or not item.implementation_evidence
                or not item.certification_evidence
            ):
                failures.append(GovernanceFailure.ORPHANED_REQUIREMENT)
        return _review(failures)

    def invariant_set(self) -> GovernanceInvariantSet:
        return GovernanceInvariantSet(
            (
                "immutable_constitutional_history",
                "deterministic_governance",
                "deterministic_authority_delegation",
                "certification_reproducibility",
                "constitutional_traceability",
                "constitutional_dependency_determinism",
                "constitutional_version_integrity",
            )
        )

    def amendment(self, record: AmendmentRecord) -> GovernanceReview:
        failures = []
        if not record.governance_authority or not record.rationale or not record.history_reference:
            failures.append(GovernanceFailure.AMENDMENT_WITHOUT_AUTHORITY)
        if record.implementation_changes_governance:
            failures.append(GovernanceFailure.IMPLEMENTATION_REDEFINED_GOVERNANCE)
        if record.mandatory_recertification_scope is None:
            failures.append(GovernanceFailure.MISSING_RECERTIFICATION_REQUIREMENT)
        return _review(failures)


class ConstitutionalAmendmentRegistry:
    """Append-only INF-GOV-016 amendment and version registry."""

    allowed_transitions = {
        AmendmentLifecycleState.DRAFT: (AmendmentLifecycleState.COMMITTEE_REVIEW,),
        AmendmentLifecycleState.COMMITTEE_REVIEW: (AmendmentLifecycleState.APPROVED,),
        AmendmentLifecycleState.APPROVED: (AmendmentLifecycleState.EFFECTIVE,),
        AmendmentLifecycleState.EFFECTIVE: (AmendmentLifecycleState.SUPERSEDED,),
        AmendmentLifecycleState.SUPERSEDED: (),
    }

    def __init__(self, records: Iterable[AmendmentRegistryRecord] = ()) -> None:
        self._records = tuple(records)

    @property
    def records(self) -> tuple[AmendmentRegistryRecord, ...]:
        return self._records

    def append(self, record: AmendmentRegistryRecord, previous_state: AmendmentLifecycleState | None = None) -> tuple["ConstitutionalAmendmentRegistry", AmendmentRegistryDecision]:
        failures: list[GovernanceFailure] = []
        required = (
            record.amendment_id,
            record.amendment_title,
            record.amendment_type,
            record.authorizing_committee,
            record.amendment_timestamp,
            record.effective_date,
            record.constitutional_version_before,
            record.constitutional_version_after,
            record.rationale,
            record.certification_status,
            record.approval_evidence,
        )
        if any(not value for value in required) or record.authorizing_committee != "Infrastructure Constitutional Committee":
            failures.append(GovernanceFailure.UNAUTHORIZED_AMENDMENT)
        if previous_state is not None and record.amendment_status not in self.allowed_transitions[previous_state]:
            failures.append(GovernanceFailure.ILLEGAL_AMENDMENT_TRANSITION)
        if not record.affected_doctrine or not record.affected_guarantees or not record.audit_references:
            failures.append(GovernanceFailure.AMENDMENT_WITHOUT_AUTHORITY)
        if not record.consistency_validated:
            failures.append(GovernanceFailure.UNRESOLVED_CONFLICT)
        unique = tuple(dict.fromkeys(failures))
        if unique:
            return self, AmendmentRegistryDecision(GovernanceDecision.REJECTED_FAIL_CLOSED, unique, None, False)
        return (
            ConstitutionalAmendmentRegistry(self._records + (record,)),
            AmendmentRegistryDecision(
                GovernanceDecision.APPROVED,
                (),
                record.constitutional_version_after,
                record.required_certification_scope != RegressionScope.NONE,
            ),
        )


def _review(failures: Iterable[GovernanceFailure]) -> GovernanceReview:
    unique = tuple(dict.fromkeys(failures))
    return GovernanceReview(GovernanceDecision.APPROVED if not unique else GovernanceDecision.REJECTED_FAIL_CLOSED, unique)


def _scope_rank(scope: RegressionScope) -> int:
    return list(RegressionScope).index(scope)


def _max_scope(left: RegressionScope, right: RegressionScope) -> RegressionScope:
    return left if _scope_rank(left) >= _scope_rank(right) else right


def _escalate(scope: RegressionScope, history: list[RegressionScope]) -> RegressionScope:
    scopes = list(RegressionScope)
    next_scope = scopes[min(_scope_rank(scope) + 1, len(scopes) - 1)]
    history.append(next_scope)
    return next_scope
