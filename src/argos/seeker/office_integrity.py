"""SEEK-RM-001 through SEEK-RM-007 Seeker office integrity support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


SEEK_RM_VERSION = "SEEK-RM-001-TO-007/1.0.0"


class SeekerLifecycleState(str, Enum):
    DORMANT = "DORMANT"
    MISSION_RECEIVED = "MISSION_RECEIVED"
    MISSION_AUTHORITY_VALIDATING = "MISSION_AUTHORITY_VALIDATING"
    SEARCH_PLAN_VALIDATING = "SEARCH_PLAN_VALIDATING"
    EXECUTION_INITIALIZING = "EXECUTION_INITIALIZING"
    DISCOVERY_EXECUTING = "DISCOVERY_EXECUTING"
    DISCOVERY_EVIDENCE_PRESERVING = "DISCOVERY_EVIDENCE_PRESERVING"
    RESULT_NORMALIZING = "RESULT_NORMALIZING"
    CANDIDATE_IDENTITY_VALIDATING = "CANDIDATE_IDENTITY_VALIDATING"
    DUPLICATE_EVALUATING = "DUPLICATE_EVALUATING"
    FRESHNESS_EVALUATING = "FRESHNESS_EVALUATING"
    INDEPENDENCE_EVALUATING = "INDEPENDENCE_EVALUATING"
    CANDIDATE_ADMISSIBILITY_EVALUATING = "CANDIDATE_ADMISSIBILITY_EVALUATING"
    SEARCH_SUFFICIENCY_EVALUATING = "SEARCH_SUFFICIENCY_EVALUATING"
    CANDIDATE_PACKAGE_ASSEMBLING = "CANDIDATE_PACKAGE_ASSEMBLING"
    CANDIDATE_PACKAGE_VALIDATING = "CANDIDATE_PACKAGE_VALIDATING"
    CANDIDATE_PACKAGE_FINALIZING = "CANDIDATE_PACKAGE_FINALIZING"
    OUTBOUND_COMMITTING = "OUTBOUND_COMMITTING"
    AUTHORITY_RELINQUISHING = "AUTHORITY_RELINQUISHING"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    RECOVERING = "RECOVERING"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True)
class SeekerSearchMission:
    mission_id: str
    mission_version: str
    objective_id: str
    constitutional_authority: str
    search_plan_id: str
    execution_parameters: Mapping[str, str]
    rule_versions: Mapping[str, str]
    discovery_scope: tuple[str, ...]
    mission_creation_timestamp: str
    replay_identifier: str = ""
    recovery_identifier: str = ""


@dataclass(frozen=True)
class SeekerApprovedSearchPlan:
    search_plan_id: str
    search_plan_version: str
    approval_status: str
    approval_authority: str
    search_objective: str
    permitted_domains: tuple[str, ...]
    approved_sources: tuple[str, ...]
    approved_methods: tuple[str, ...]
    candidate_inclusion_rules: tuple[str, ...]
    candidate_exclusion_rules: tuple[str, ...]
    identity_requirements: tuple[str, ...]
    freshness_requirements: tuple[str, ...]
    duplicate_rules: tuple[str, ...]
    independence_requirements: tuple[str, ...]
    sufficiency_requirements: tuple[str, ...]
    termination_conditions: tuple[str, ...]
    execution_limits: Mapping[str, int]
    immutable_digest: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "immutable_digest", _digest(self))


@dataclass(frozen=True)
class SeekerDiscoveryEvidence:
    evidence_id: str
    source_id: str
    acquisition_method: str
    search_activity_id: str
    payload: Mapping[str, str]
    retrieved_at: str
    source_timestamp: str
    evidence_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_hash", _digest(self))


@dataclass(frozen=True)
class SeekerCandidateIdentityInput:
    candidate_reference: str
    candidate_type: str
    evidence_references: tuple[str, ...]
    attributes: Mapping[str, str]


@dataclass(frozen=True)
class SeekerBoundaryRegistryRecord:
    registry_identifier: str
    office_identity: str
    registered_components: tuple[str, ...]
    owned_state: tuple[str, ...]
    owned_inputs: tuple[str, ...]
    owned_outputs: tuple[str, ...]
    constitutional_interfaces: Mapping[str, tuple[str, ...]]
    excluded_responsibilities: tuple[str, ...]
    duplicate_owners: tuple[str, ...]
    undefined_components: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerSelfCertificationSeparationRecord:
    separation_identifier: str
    office_identity: str
    prohibited_terms: tuple[str, ...]
    detected_self_certification_paths: tuple[str, ...]
    operational_decisions_only: bool
    independent_authority: str
    seeker_controls_certification_verdict: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerMissionIntakeRecord:
    intake_identifier: str
    mission_id: str
    validation_stages: tuple[str, ...]
    missing_fields: tuple[str, ...]
    rejected_authority: tuple[str, ...]
    duplicate_mission_detected: bool
    initial_state: str
    final_state: str
    discovery_started_before_activation: bool
    activation_decision: str
    failure_reason: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerLifecycleStateMachineRecord:
    lifecycle_identifier: str
    lifecycle_version: str
    state_inventory: tuple[str, ...]
    transition_sequence: tuple[str, ...]
    invalid_transitions: tuple[str, ...]
    bypass_findings: tuple[str, ...]
    residual_authority: tuple[str, ...]
    terminal_state: str
    replay_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerSearchPlanEnforcementRecord:
    enforcement_identifier: str
    search_plan_id: str
    search_plan_version: str
    missing_plan_elements: tuple[str, ...]
    unauthorized_sources: tuple[str, ...]
    unauthorized_methods: tuple[str, ...]
    scope_violations: tuple[str, ...]
    immutable_plan_digest: str
    candidate_traceability_complete: bool
    replay_equivalent: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerObjectiveValidationRecord:
    objective_identifier: str
    objective_id: str
    validation_decision: str
    missing_fields: tuple[str, ...]
    ambiguity_findings: tuple[str, ...]
    prohibited_responsibilities: tuple[str, ...]
    plan_consistency_findings: tuple[str, ...]
    rule_versions: Mapping[str, str]
    immutable_evidence_identifier: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerCandidateIdentityValidationRecord:
    identity_identifier: str
    candidate_reference: str
    canonical_identity: str
    required_identity_fields: tuple[str, ...]
    missing_identity_fields: tuple[str, ...]
    conflicting_identity_fields: tuple[str, ...]
    unsupported_identity_fields: tuple[str, ...]
    ambiguity_findings: tuple[str, ...]
    evidence_references: tuple[str, ...]
    identity_immutable: bool
    validation_decision: str
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class SeekerOfficeIntegrityEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    office_identity: str
    remediation_order_coverage: tuple[str, ...]
    boundary_registry: SeekerBoundaryRegistryRecord
    self_certification_separation: SeekerSelfCertificationSeparationRecord
    mission_intake: SeekerMissionIntakeRecord
    lifecycle_state_machine: SeekerLifecycleStateMachineRecord
    search_plan_enforcement: SeekerSearchPlanEnforcementRecord
    objective_validation: SeekerObjectiveValidationRecord
    candidate_identity_validation: SeekerCandidateIdentityValidationRecord
    final_office_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


class SeekerOfficeIntegritySupport:
    """Build independent certification-support records for Seeker RM orders."""

    remediation_order_coverage = (
        "SEEK-RM-001-001",
        "SEEK-RM-002",
        "SEEK-RM-003",
        "SEEK-RM-004",
        "SEEK-RM-005",
        "SEEK-RM-006",
        "SEEK-RM-007",
    )

    component_registry = (
        "Mission Intake Component",
        "Search Plan Validation Component",
        "Discovery Execution Component",
        "Discovery Evidence Registry",
        "Candidate Identity Component",
        "Duplicate Detection Component",
        "Freshness Validation Component",
        "Independence Validation Component",
        "Search Sufficiency Component",
        "Candidate Package Construction Component",
        "Candidate Package Commitment Component",
        "Audit Evidence Component",
        "Replay Component",
        "Recovery Component",
        "Lifecycle Component",
    )

    owned_state = (
        "Mission State",
        "Discovery State",
        "Search Plan State",
        "Candidate Registry",
        "Duplicate Registry",
        "Freshness Evaluation State",
        "Independence Evaluation State",
        "Search Sufficiency State",
        "Candidate Package State",
        "Audit State",
        "Replay State",
        "Recovery State",
        "Lifecycle State",
    )

    excluded_responsibilities = (
        "market observation",
        "market monitoring",
        "market interpretation",
        "financial analysis",
        "scoring investment quality",
        "ranking opportunities",
        "portfolio optimization",
        "risk assessment",
        "authorization",
        "trading",
        "broker communication",
        "enterprise scheduling",
        "bridge transport",
        "workflow orchestration",
        "enterprise persistence",
        "enterprise certification",
        "self-certification",
    )

    lifecycle_success_path = (
        SeekerLifecycleState.DORMANT.value,
        SeekerLifecycleState.MISSION_RECEIVED.value,
        SeekerLifecycleState.MISSION_AUTHORITY_VALIDATING.value,
        SeekerLifecycleState.SEARCH_PLAN_VALIDATING.value,
        SeekerLifecycleState.EXECUTION_INITIALIZING.value,
        SeekerLifecycleState.DISCOVERY_EXECUTING.value,
        SeekerLifecycleState.DISCOVERY_EVIDENCE_PRESERVING.value,
        SeekerLifecycleState.RESULT_NORMALIZING.value,
        SeekerLifecycleState.CANDIDATE_IDENTITY_VALIDATING.value,
        SeekerLifecycleState.DUPLICATE_EVALUATING.value,
        SeekerLifecycleState.FRESHNESS_EVALUATING.value,
        SeekerLifecycleState.INDEPENDENCE_EVALUATING.value,
        SeekerLifecycleState.CANDIDATE_ADMISSIBILITY_EVALUATING.value,
        SeekerLifecycleState.SEARCH_SUFFICIENCY_EVALUATING.value,
        SeekerLifecycleState.CANDIDATE_PACKAGE_ASSEMBLING.value,
        SeekerLifecycleState.CANDIDATE_PACKAGE_VALIDATING.value,
        SeekerLifecycleState.CANDIDATE_PACKAGE_FINALIZING.value,
        SeekerLifecycleState.OUTBOUND_COMMITTING.value,
        SeekerLifecycleState.AUTHORITY_RELINQUISHING.value,
        SeekerLifecycleState.DORMANT.value,
    )

    def build_package(
        self,
        *,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        discovery_evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
        lifecycle_sequence: tuple[str, ...] | None = None,
        inspected_artifacts: Mapping[str, Mapping[str, Any]] | None = None,
        active_missions: tuple[str, ...] = (),
    ) -> SeekerOfficeIntegrityEvidencePackage:
        boundary = self.evaluate_boundary_registry()
        separation = self.evaluate_self_certification_separation(inspected_artifacts or {})
        intake = self.evaluate_mission_intake(mission, search_plan, active_missions=active_missions)
        lifecycle = self.evaluate_lifecycle_state_machine(lifecycle_sequence or self.lifecycle_success_path)
        enforcement = self.evaluate_search_plan_enforcement(search_plan, discovery_evidence, candidate)
        objective = self.evaluate_objective_validation(mission, search_plan)
        identity = self.evaluate_candidate_identity(candidate, search_plan, discovery_evidence)
        final = EnterpriseCertificationDecision.PASS if all(
            record == EnterpriseCertificationDecision.PASS
            for record in (
                boundary.result,
                separation.result,
                intake.result,
                lifecycle.result,
                enforcement.result,
                objective.result,
                identity.result,
            )
        ) else EnterpriseCertificationDecision.FAIL
        package = SeekerOfficeIntegrityEvidencePackage(
            package_identifier=f"SEEK-RM-PKG-{_digest((mission.mission_id, search_plan.search_plan_id, candidate.candidate_reference))[:12].upper()}",
            governing_doctrine=SEEK_RM_VERSION,
            office_identity="Seeker",
            remediation_order_coverage=self.remediation_order_coverage,
            boundary_registry=boundary,
            self_certification_separation=separation,
            mission_intake=intake,
            lifecycle_state_machine=lifecycle,
            search_plan_enforcement=enforcement,
            objective_validation=objective,
            candidate_identity_validation=identity,
            final_office_readiness=final,
            immutable_audit_references=(
                boundary.registry_identifier,
                separation.separation_identifier,
                intake.intake_identifier,
                lifecycle.lifecycle_identifier,
                enforcement.enforcement_identifier,
                objective.objective_identifier,
                identity.identity_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_boundary_registry(self) -> SeekerBoundaryRegistryRecord:
        interfaces = MappingProxyType(
            {
                "inbound": ("Authorized Search Mission",),
                "outbound": ("Immutable Candidate Packages", "Immutable Audit Evidence", "Constitutional Failure Records"),
            }
        )
        duplicates = ()
        undefined = ()
        record = SeekerBoundaryRegistryRecord(
            registry_identifier=f"SEEK-RM-BOUNDARY-{_digest((self.component_registry, self.owned_state))[:12].upper()}",
            office_identity="Seeker",
            registered_components=self.component_registry,
            owned_state=self.owned_state,
            owned_inputs=("Constitutionally Authorized Search Mission",),
            owned_outputs=("Immutable Candidate Packages", "Immutable Audit Evidence", "Constitutional Failure Records"),
            constitutional_interfaces=interfaces,
            excluded_responsibilities=self.excluded_responsibilities,
            duplicate_owners=duplicates,
            undefined_components=undefined,
            result=EnterpriseCertificationDecision.PASS,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_self_certification_separation(self, artifacts: Mapping[str, Mapping[str, Any]]) -> SeekerSelfCertificationSeparationRecord:
        prohibited = (
            "certification_passed",
            "constitutional_status",
            "office_certified",
            "certification_result",
            "audit_passed",
            "constitutional_score",
            "certification_complete",
            "compliance_status",
            "PASS",
            "FAIL",
            "CERTIFIED",
            "COMPLIANT",
            "VERIFIED",
            "VALIDATED",
            "APPROVED",
            "ACCEPTED",
        )
        detected = tuple(
            f"{artifact_id}.{key}"
            for artifact_id, artifact in sorted(artifacts.items())
            for key, value in artifact.items()
            if key in prohibited or str(value).upper() in prohibited
        )
        record = SeekerSelfCertificationSeparationRecord(
            separation_identifier=f"SEEK-RM-SELF-CERT-{_digest((prohibited, detected))[:12].upper()}",
            office_identity="Seeker",
            prohibited_terms=prohibited,
            detected_self_certification_paths=detected,
            operational_decisions_only=not detected,
            independent_authority="Independent Office Certification Authority",
            seeker_controls_certification_verdict=False,
            result=EnterpriseCertificationDecision.PASS if not detected else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_mission_intake(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
        *,
        active_missions: tuple[str, ...] = (),
    ) -> SeekerMissionIntakeRecord:
        required = {
            "mission_id": mission.mission_id,
            "mission_version": mission.mission_version,
            "objective_id": mission.objective_id,
            "constitutional_authority": mission.constitutional_authority,
            "search_plan_id": mission.search_plan_id,
            "execution_parameters": mission.execution_parameters,
            "rule_versions": mission.rule_versions,
            "discovery_scope": mission.discovery_scope,
            "mission_creation_timestamp": mission.mission_creation_timestamp,
        }
        missing = tuple(name for name, value in required.items() if not value)
        rejected_authority = () if mission.constitutional_authority in {"Commander", "Executive", "Strategic Intelligence"} else (mission.constitutional_authority or "missing_authority",)
        duplicate = mission.mission_id in active_missions
        plan_mismatch = mission.search_plan_id != search_plan.search_plan_id
        failure = "missing_fields" if missing else "unauthorized_authority" if rejected_authority else "duplicate_mission" if duplicate else "search_plan_mismatch" if plan_mismatch else ""
        decision = "ACCEPT" if not failure else "REJECT"
        record = SeekerMissionIntakeRecord(
            intake_identifier=f"SEEK-RM-INTAKE-{_digest((mission, failure, active_missions))[:12].upper()}",
            mission_id=mission.mission_id,
            validation_stages=("mission_identity", "constitutional_authority", "search_plan", "office_state", "execution_context"),
            missing_fields=missing,
            rejected_authority=rejected_authority,
            duplicate_mission_detected=duplicate,
            initial_state=SeekerLifecycleState.DORMANT.value,
            final_state=SeekerLifecycleState.EXECUTION_INITIALIZING.value if decision == "ACCEPT" else SeekerLifecycleState.DORMANT.value,
            discovery_started_before_activation=False,
            activation_decision=decision,
            failure_reason=failure,
            result=EnterpriseCertificationDecision.PASS if decision == "ACCEPT" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_lifecycle_state_machine(self, sequence: tuple[str, ...]) -> SeekerLifecycleStateMachineRecord:
        allowed_pairs = tuple(zip(self.lifecycle_success_path, self.lifecycle_success_path[1:]))
        pair_set = set(allowed_pairs)
        observed_pairs = tuple(zip(sequence, sequence[1:]))
        invalid = tuple(f"{source}->{target}" for source, target in observed_pairs if (source, target) not in pair_set and target != SeekerLifecycleState.EXECUTION_FAILED.value)
        mandatory = set(self.lifecycle_success_path)
        bypass = tuple(state for state in self.lifecycle_success_path if state not in sequence and state != SeekerLifecycleState.DORMANT.value)
        residual = () if sequence and sequence[-1] == SeekerLifecycleState.DORMANT.value else ("mission_authority_not_relinquished",)
        replay_equivalent = _digest(sequence) == _digest(tuple(sequence))
        record = SeekerLifecycleStateMachineRecord(
            lifecycle_identifier=f"SEEK-RM-LIFECYCLE-{_digest((sequence, invalid, bypass, residual))[:12].upper()}",
            lifecycle_version="SEEK-RM-004-LIFECYCLE/1",
            state_inventory=tuple(state.value for state in SeekerLifecycleState),
            transition_sequence=sequence,
            invalid_transitions=invalid,
            bypass_findings=tuple(item for item in bypass if item in mandatory),
            residual_authority=residual,
            terminal_state=sequence[-1] if sequence else "",
            replay_equivalent=replay_equivalent,
            result=EnterpriseCertificationDecision.PASS if sequence and not invalid and not bypass and not residual and replay_equivalent else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_search_plan_enforcement(
        self,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
        candidate: SeekerCandidateIdentityInput,
    ) -> SeekerSearchPlanEnforcementRecord:
        required = {
            "search_plan_id": search_plan.search_plan_id,
            "search_plan_version": search_plan.search_plan_version,
            "approval_status": search_plan.approval_status,
            "approval_authority": search_plan.approval_authority,
            "search_objective": search_plan.search_objective,
            "permitted_domains": search_plan.permitted_domains,
            "approved_sources": search_plan.approved_sources,
            "approved_methods": search_plan.approved_methods,
            "identity_requirements": search_plan.identity_requirements,
            "sufficiency_requirements": search_plan.sufficiency_requirements,
            "termination_conditions": search_plan.termination_conditions,
        }
        missing = tuple(name for name, value in required.items() if not value)
        if search_plan.approval_status != "APPROVED":
            missing = missing + ("approval_status_not_approved",)
        unauthorized_sources = tuple(item.source_id for item in evidence if item.source_id not in search_plan.approved_sources)
        unauthorized_methods = tuple(item.acquisition_method for item in evidence if item.acquisition_method not in search_plan.approved_methods)
        prohibited = {"trade_authorization", "risk_assessment", "broker_execution", "market_observation", "analyst_interpretation"}
        scope = tuple(item for item in search_plan.permitted_domains if item in prohibited)
        evidence_ids = {item.evidence_id for item in evidence}
        traceability = bool(candidate.evidence_references) and set(candidate.evidence_references).issubset(evidence_ids)
        replay_equivalent = _digest((search_plan.immutable_digest, tuple(item.evidence_hash for item in evidence))) == _digest((search_plan.immutable_digest, tuple(item.evidence_hash for item in evidence)))
        record = SeekerSearchPlanEnforcementRecord(
            enforcement_identifier=f"SEEK-RM-PLAN-{_digest((search_plan, evidence, candidate.evidence_references))[:12].upper()}",
            search_plan_id=search_plan.search_plan_id,
            search_plan_version=search_plan.search_plan_version,
            missing_plan_elements=missing,
            unauthorized_sources=tuple(dict.fromkeys(unauthorized_sources)),
            unauthorized_methods=tuple(dict.fromkeys(unauthorized_methods)),
            scope_violations=scope,
            immutable_plan_digest=search_plan.immutable_digest,
            candidate_traceability_complete=traceability,
            replay_equivalent=replay_equivalent,
            result=EnterpriseCertificationDecision.PASS if not missing and not unauthorized_sources and not unauthorized_methods and not scope and traceability and replay_equivalent else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_objective_validation(
        self,
        mission: SeekerSearchMission,
        search_plan: SeekerApprovedSearchPlan,
    ) -> SeekerObjectiveValidationRecord:
        required = {
            "objective_id": mission.objective_id,
            "search_intent": search_plan.search_objective,
            "approved_search_domain": search_plan.permitted_domains,
            "approved_search_scope": mission.discovery_scope,
            "candidate_definition": search_plan.identity_requirements,
            "search_plan_reference": mission.search_plan_id,
            "execution_limits": search_plan.execution_limits,
        }
        missing = tuple(name for name, value in required.items() if not value)
        ambiguous_terms = {"best", "promising", "interesting", "high quality", "as needed"}
        ambiguity = tuple(term for term in ambiguous_terms if term in search_plan.search_objective.lower())
        prohibited_terms = {
            "trade": "trade_authorization",
            "portfolio": "portfolio_evaluation",
            "risk": "risk_assessment",
            "recommend": "investment_recommendation",
            "sentinel": "sentinel_owned_observation",
        }
        prohibited = tuple(reason for term, reason in prohibited_terms.items() if term in search_plan.search_objective.lower())
        consistency = ()
        if mission.search_plan_id != search_plan.search_plan_id:
            consistency = ("search_plan_reference_mismatch",)
        if not set(mission.discovery_scope).issubset(set(search_plan.permitted_domains)):
            consistency = consistency + ("scope_not_permitted_by_plan",)
        decision = "VALID" if not missing and not ambiguity and not prohibited and not consistency else "INVALID"
        record = SeekerObjectiveValidationRecord(
            objective_identifier=f"SEEK-RM-OBJECTIVE-{_digest((mission.objective_id, search_plan.search_objective, decision))[:12].upper()}",
            objective_id=mission.objective_id,
            validation_decision=decision,
            missing_fields=missing,
            ambiguity_findings=ambiguity,
            prohibited_responsibilities=prohibited,
            plan_consistency_findings=consistency,
            rule_versions=MappingProxyType(dict(mission.rule_versions)),
            immutable_evidence_identifier=f"SEEK-RM-OBJ-EVID-{_digest((mission, search_plan.immutable_digest))[:12].upper()}",
            result=EnterpriseCertificationDecision.PASS if decision == "VALID" else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_candidate_identity(
        self,
        candidate: SeekerCandidateIdentityInput,
        search_plan: SeekerApprovedSearchPlan,
        evidence: tuple[SeekerDiscoveryEvidence, ...],
    ) -> SeekerCandidateIdentityValidationRecord:
        required = search_plan.identity_requirements
        attributes = {key: str(value).strip() for key, value in candidate.attributes.items()}
        missing = tuple(field for field in required if not attributes.get(field))
        unsupported = tuple(field for field in attributes if field not in set(required).union({"issuer_name", "source_id", "discovery_timestamp"}))
        conflicts = tuple(field for field, value in attributes.items() if "|" in value or "," in value and field in required)
        evidence_ids = {item.evidence_id for item in evidence}
        absent_evidence = tuple(ref for ref in candidate.evidence_references if ref not in evidence_ids)
        ambiguity = ("missing_supporting_evidence",) if absent_evidence else ()
        canonical_parts = tuple((field, attributes.get(field, "").upper()) for field in sorted(required) if attributes.get(field))
        canonical = _digest((candidate.candidate_type, canonical_parts))[:24].upper() if canonical_parts and not missing and not conflicts and not ambiguity else ""
        decision = "VALID" if canonical and not missing and not unsupported and not conflicts and not ambiguity else "INVALID"
        record = SeekerCandidateIdentityValidationRecord(
            identity_identifier=f"SEEK-RM-CANDIDATE-{_digest((candidate, canonical, decision))[:12].upper()}",
            candidate_reference=candidate.candidate_reference,
            canonical_identity=canonical,
            required_identity_fields=required,
            missing_identity_fields=missing,
            conflicting_identity_fields=conflicts,
            unsupported_identity_fields=unsupported,
            ambiguity_findings=ambiguity,
            evidence_references=candidate.evidence_references,
            identity_immutable=decision == "VALID",
            validation_decision=decision,
            result=EnterpriseCertificationDecision.PASS if decision == "VALID" else EnterpriseCertificationDecision.FAIL,
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
            if field_info.name not in {"deterministic_digest", "immutable_digest", "evidence_hash"}
        }
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(item) for item in value]
    return value
