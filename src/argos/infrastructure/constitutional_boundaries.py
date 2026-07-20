"""INF-001 Infrastructure Office constitutional boundary registry.

Infrastructure provides deterministic enterprise mechanisms only.  This module
defines the exhaustive authority, non-authority, service, interface,
dependency, prerequisite, and invariant rules required before downstream
operational certification can proceed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Iterable, Mapping


INF_001_VERSION = "INF-001/1.0.0"


class InfrastructureAuthorityDomain(str, Enum):
    REPOSITORY_IDENTITY = "repository_identity"
    REPOSITORY_CERTIFICATION = "repository_certification"
    CANDIDATE_IDENTITY = "candidate_identity"
    CANDIDATE_CERTIFICATION = "candidate_certification"
    RUNTIME_CONSTRUCTION = "runtime_construction"
    RUNTIME_INITIALIZATION = "runtime_initialization"
    RUNTIME_DEPENDENCY_REGISTRATION = "runtime_dependency_registration"
    WORKFLOW_EXECUTION_INFRASTRUCTURE = "workflow_execution_infrastructure"
    WORKFLOW_EXECUTION_TOKEN_INFRASTRUCTURE = "workflow_execution_token_infrastructure"
    AUTHORITY_INFRASTRUCTURE = "authority_infrastructure"
    LAW_VII_ENFORCEMENT_INFRASTRUCTURE = "law_vii_enforcement_infrastructure"
    BRIDGE_REGISTRY = "bridge_registry"
    BRIDGE_CERTIFICATION = "bridge_certification"
    INFRASTRUCTURE_PERSISTENCE = "infrastructure_persistence"
    RECOVERY_INFRASTRUCTURE = "recovery_infrastructure"
    REPLAY_INFRASTRUCTURE = "replay_infrastructure"
    INFRASTRUCTURE_AUDIT_SYSTEMS = "infrastructure_audit_systems"
    INFRASTRUCTURE_EVIDENCE_SYSTEMS = "infrastructure_evidence_systems"
    INFRASTRUCTURE_PROOF_SYSTEMS = "infrastructure_proof_systems"
    INFRASTRUCTURE_HEALTH_MONITORING = "infrastructure_health_monitoring"
    INFRASTRUCTURE_TESTING_INFRASTRUCTURE = "infrastructure_testing_infrastructure"
    INFRASTRUCTURE_CERTIFICATION_INFRASTRUCTURE = "infrastructure_certification_infrastructure"
    DETERMINISTIC_EXECUTION_INFRASTRUCTURE = "deterministic_execution_infrastructure"


class InfrastructureNonAuthority(str, Enum):
    MARKET_RESEARCH = "market_research"
    FINANCIAL_INFORMATION_COLLECTION = "financial_information_collection"
    SECURITY_EVALUATION = "security_evaluation"
    INTELLIGENCE_INTERPRETATION = "intelligence_interpretation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    PORTFOLIO_CONSTRUCTION = "portfolio_construction"
    SIGNAL_GENERATION = "signal_generation"
    TRADE_APPROVAL = "trade_approval"
    TRADE_DENIAL = "trade_denial"
    RISK_CALCULATION = "risk_calculation"
    POSITION_MANAGEMENT = "position_management"
    EXIT_EVALUATION = "exit_evaluation"
    STRATEGY_LEARNING = "strategy_learning"
    HISTORICAL_TRUTH_MODIFICATION = "historical_truth_modification"
    OPERATIONAL_COMMAND_ISSUANCE = "operational_command_issuance"
    OPERATIONAL_JUDGMENT_SUBSTITUTION = "operational_judgment_substitution"


class InfrastructureServiceType(str, Enum):
    IDENTITY_SERVICES = "identity_services"
    RUNTIME_SERVICES = "runtime_services"
    PERSISTENCE_SERVICES = "persistence_services"
    REPLAY_SERVICES = "replay_services"
    CERTIFICATION_SERVICES = "certification_services"
    AUDIT_SERVICES = "audit_services"
    PROOF_SERVICES = "proof_services"
    WORKFLOW_INFRASTRUCTURE = "workflow_infrastructure"
    BRIDGE_INFRASTRUCTURE = "bridge_infrastructure"
    HEALTH_MONITORING = "health_monitoring"
    DETERMINISTIC_EXECUTION_SUPPORT = "deterministic_execution_support"


class ConstitutionalLayer(str, Enum):
    CONSTITUTIONAL_DOCTRINE = "constitutional_doctrine"
    INFRASTRUCTURE_OFFICE = "infrastructure_office"
    SHARED_CONSTITUTIONAL_SERVICES = "shared_constitutional_services"
    OPERATIONAL_OFFICES = "operational_offices"
    ENTERPRISE_WORKFLOWS = "enterprise_workflows"


class InterfaceTarget(str, Enum):
    RUNTIME_INTERNALS = "runtime_internals"
    BRIDGE_REGISTRY = "bridge_registry"
    AUTHORITY_REGISTRY = "authority_registry"
    WORKFLOW_EXECUTION_ENGINE = "workflow_execution_engine"
    CANDIDATE_REGISTRY = "candidate_registry"
    REPOSITORY_REGISTRY = "repository_registry"
    PROOF_REGISTRY = "proof_registry"
    AUDIT_REGISTRY = "audit_registry"
    PERSISTENCE_SUBSTRATE = "persistence_substrate"
    REPLAY_ENGINE = "replay_engine"


class InfrastructureCertificationPrerequisite(str, Enum):
    REPOSITORY_IDENTITY_CERTIFIED = "repository_identity_certified"
    CANDIDATE_IDENTITY_CERTIFIED = "candidate_identity_certified"
    RUNTIME_CONSTRUCTION_DETERMINISTIC = "runtime_construction_deterministic"
    WORKFLOW_INFRASTRUCTURE_CERTIFIED = "workflow_infrastructure_certified"
    AUTHORITY_INFRASTRUCTURE_CERTIFIED = "authority_infrastructure_certified"
    LAW_VII_INFRASTRUCTURE_CERTIFIED = "law_vii_infrastructure_certified"
    BRIDGE_REGISTRY_CERTIFIED = "bridge_registry_certified"
    BRIDGE_CERTIFICATION_COMPLETE = "bridge_certification_complete"
    PERSISTENCE_SUBSTRATE_CERTIFIED = "persistence_substrate_certified"
    REPLAY_INFRASTRUCTURE_CERTIFIED = "replay_infrastructure_certified"
    AUDIT_INFRASTRUCTURE_CERTIFIED = "audit_infrastructure_certified"
    PROOF_INFRASTRUCTURE_CERTIFIED = "proof_infrastructure_certified"
    DETERMINISTIC_EXECUTION_DEMONSTRATED = "deterministic_execution_demonstrated"


class InfrastructureInvariant(str, Enum):
    NEVER_OWN_OPERATIONAL_DECISIONS = "never_own_operational_decisions"
    NEVER_MODIFY_TRUTH = "never_modify_truth"
    NEVER_SYNTHESIZE_EVIDENCE = "never_synthesize_evidence"
    NEVER_INFER_AUTHORITY = "never_infer_authority"
    NEVER_BYPASS_CERTIFICATION = "never_bypass_certification"
    NEVER_EXECUTE_UNCERTIFIED_INFRASTRUCTURE = "never_execute_uncertified_infrastructure"
    NEVER_EXPOSE_UNDOCUMENTED_INTERFACES = "never_expose_undocumented_interfaces"
    NEVER_PERMIT_UNDEFINED_OR_SHARED_AUTHORITY = "never_permit_undefined_or_shared_authority"
    ALWAYS_FAIL_CLOSED = "always_fail_closed"
    ALWAYS_TRACEABLE = "always_traceable"
    ALWAYS_NEUTRAL = "always_neutral"
    ALWAYS_AUDITABLE = "always_auditable"


class InfrastructureFailureReason(str, Enum):
    AUTHORITY_UNVERIFIED = "authority_unverified"
    IDENTITY_UNPROVEN = "identity_unproven"
    BRIDGES_UNCERTIFIED = "bridges_uncertified"
    RUNTIME_UNVERIFIABLE = "runtime_unverifiable"
    DETERMINISM_NOT_DEMONSTRATED = "determinism_not_demonstrated"
    EVIDENCE_INCOMPLETE = "evidence_incomplete"
    PROOF_GENERATION_FAILED = "proof_generation_failed"
    INFRASTRUCTURE_INTEGRITY_UNESTABLISHED = "infrastructure_integrity_unestablished"
    OPERATIONAL_LOGIC_PRESENT = "operational_logic_present"
    OPERATIONAL_DECISION_PRESENT = "operational_decision_present"
    DIRECT_INTERFACE_ACCESS = "direct_interface_access"
    DEPENDENCY_CYCLE = "dependency_cycle"
    REVERSE_DEPENDENCY = "reverse_dependency"
    SHARED_OWNERSHIP = "shared_ownership"
    UNDOCUMENTED_INTERFACE = "undocumented_interface"
    UNDEFINED_OWNERSHIP = "undefined_ownership"
    NON_AUTHORITY_DECLARED = "non_authority_declared"


class InfrastructureCertificationState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SUSPENDED_DOWNSTREAM_CERTIFICATION = "SUSPENDED_DOWNSTREAM_CERTIFICATION"


@dataclass(frozen=True)
class InfrastructureDependencyEdge:
    edge_id: str
    upstream: ConstitutionalLayer
    downstream: ConstitutionalLayer
    evidence_reference: str


@dataclass(frozen=True)
class InfrastructureServiceDeclaration:
    service_id: str
    service_type: InfrastructureServiceType
    authority_domain: InfrastructureAuthorityDomain
    exposed_interface: str
    owner: ConstitutionalLayer = ConstitutionalLayer.INFRASTRUCTURE_OFFICE
    contains_operational_logic: bool = False
    performs_operational_decision: bool = False
    asserted_non_authorities: tuple[InfrastructureNonAuthority, ...] = ()
    evidence_references: tuple[str, ...] = ()


@dataclass(frozen=True)
class InfrastructurePrerequisiteEvidence:
    prerequisite: InfrastructureCertificationPrerequisite
    satisfied: bool
    evidence_reference: str
    certified_by: str
    checked_at: str


@dataclass(frozen=True)
class InterfaceAccessRequest:
    requesting_layer: ConstitutionalLayer
    target: InterfaceTarget
    interface_id: str
    direct_internal_access: bool


@dataclass(frozen=True)
class InfrastructureAuthorityBoundary:
    version: str
    authority_domains: tuple[InfrastructureAuthorityDomain, ...]
    non_authorities: tuple[InfrastructureNonAuthority, ...]
    service_types: tuple[InfrastructureServiceType, ...]
    certified_interfaces: Mapping[str, InterfaceTarget]
    dependency_order: tuple[ConstitutionalLayer, ...]
    prerequisites: tuple[InfrastructureCertificationPrerequisite, ...]
    invariants: tuple[InfrastructureInvariant, ...]


@dataclass(frozen=True)
class InfrastructureCertificationRecord:
    record_id: str
    version: str
    state: InfrastructureCertificationState
    prerequisite_statuses: Mapping[InfrastructureCertificationPrerequisite, bool]
    service_violations: Mapping[str, tuple[InfrastructureFailureReason, ...]]
    dependency_violations: tuple[InfrastructureFailureReason, ...]
    interface_violations: tuple[InfrastructureFailureReason, ...]
    failure_reasons: tuple[InfrastructureFailureReason, ...]
    downstream_certification_allowed: bool
    invariant_statuses: Mapping[InfrastructureInvariant, bool]
    evidence_references: tuple[str, ...]
    record_digest: str = field(default="")

    def with_digest(self) -> "InfrastructureCertificationRecord":
        payload = asdict(self)
        payload["record_digest"] = ""
        digest = _stable_digest(payload)
        return InfrastructureCertificationRecord(
            record_id=self.record_id,
            version=self.version,
            state=self.state,
            prerequisite_statuses=self.prerequisite_statuses,
            service_violations=self.service_violations,
            dependency_violations=self.dependency_violations,
            interface_violations=self.interface_violations,
            failure_reasons=self.failure_reasons,
            downstream_certification_allowed=self.downstream_certification_allowed,
            invariant_statuses=self.invariant_statuses,
            evidence_references=self.evidence_references,
            record_digest=digest,
        )


class InfrastructureBoundaryRegistry:
    """Immutable INF-001 constitutional boundary definition."""

    def __init__(self) -> None:
        self._certified_interfaces = MappingProxyType(
            {
                "INF-CERT-RUNTIME-INTERNALS": InterfaceTarget.RUNTIME_INTERNALS,
                "INF-CERT-BRIDGE-REGISTRY": InterfaceTarget.BRIDGE_REGISTRY,
                "INF-CERT-AUTHORITY-REGISTRY": InterfaceTarget.AUTHORITY_REGISTRY,
                "INF-CERT-WORKFLOW-ENGINE": InterfaceTarget.WORKFLOW_EXECUTION_ENGINE,
                "INF-CERT-CANDIDATE-REGISTRY": InterfaceTarget.CANDIDATE_REGISTRY,
                "INF-CERT-REPOSITORY-REGISTRY": InterfaceTarget.REPOSITORY_REGISTRY,
                "INF-CERT-PROOF-REGISTRY": InterfaceTarget.PROOF_REGISTRY,
                "INF-CERT-AUDIT-REGISTRY": InterfaceTarget.AUDIT_REGISTRY,
                "INF-CERT-PERSISTENCE-SUBSTRATE": InterfaceTarget.PERSISTENCE_SUBSTRATE,
                "INF-CERT-REPLAY-ENGINE": InterfaceTarget.REPLAY_ENGINE,
            }
        )
        self._dependency_order = (
            ConstitutionalLayer.CONSTITUTIONAL_DOCTRINE,
            ConstitutionalLayer.INFRASTRUCTURE_OFFICE,
            ConstitutionalLayer.SHARED_CONSTITUTIONAL_SERVICES,
            ConstitutionalLayer.OPERATIONAL_OFFICES,
            ConstitutionalLayer.ENTERPRISE_WORKFLOWS,
        )

    @property
    def certified_interfaces(self) -> Mapping[str, InterfaceTarget]:
        return self._certified_interfaces

    @property
    def dependency_rank(self) -> Mapping[ConstitutionalLayer, int]:
        return MappingProxyType({layer: index for index, layer in enumerate(self._dependency_order)})

    def boundary(self) -> InfrastructureAuthorityBoundary:
        return InfrastructureAuthorityBoundary(
            version=INF_001_VERSION,
            authority_domains=tuple(InfrastructureAuthorityDomain),
            non_authorities=tuple(InfrastructureNonAuthority),
            service_types=tuple(InfrastructureServiceType),
            certified_interfaces=self._certified_interfaces,
            dependency_order=self._dependency_order,
            prerequisites=tuple(InfrastructureCertificationPrerequisite),
            invariants=tuple(InfrastructureInvariant),
        )


class InfrastructureBoundaryValidator:
    """Fail-closed validator for Infrastructure Office certification."""

    def __init__(self, registry: InfrastructureBoundaryRegistry | None = None) -> None:
        self.registry = registry or InfrastructureBoundaryRegistry()

    def validate_service(self, service: InfrastructureServiceDeclaration) -> tuple[InfrastructureFailureReason, ...]:
        failures: list[InfrastructureFailureReason] = []
        if service.owner != ConstitutionalLayer.INFRASTRUCTURE_OFFICE:
            failures.append(InfrastructureFailureReason.UNDEFINED_OWNERSHIP)
        if service.exposed_interface not in self.registry.certified_interfaces:
            failures.append(InfrastructureFailureReason.UNDOCUMENTED_INTERFACE)
        if service.contains_operational_logic:
            failures.append(InfrastructureFailureReason.OPERATIONAL_LOGIC_PRESENT)
        if service.performs_operational_decision:
            failures.append(InfrastructureFailureReason.OPERATIONAL_DECISION_PRESENT)
        if service.asserted_non_authorities:
            failures.append(InfrastructureFailureReason.NON_AUTHORITY_DECLARED)
        return tuple(dict.fromkeys(failures))

    def validate_interface_access(self, request: InterfaceAccessRequest) -> tuple[InfrastructureFailureReason, ...]:
        failures: list[InfrastructureFailureReason] = []
        if request.direct_internal_access:
            failures.append(InfrastructureFailureReason.DIRECT_INTERFACE_ACCESS)
        certified_target = self.registry.certified_interfaces.get(request.interface_id)
        if certified_target is None or certified_target != request.target:
            failures.append(InfrastructureFailureReason.UNDOCUMENTED_INTERFACE)
        return tuple(dict.fromkeys(failures))

    def validate_dependency_graph(
        self, dependencies: Iterable[InfrastructureDependencyEdge]
    ) -> tuple[InfrastructureFailureReason, ...]:
        edges = tuple(dependencies)
        failures: list[InfrastructureFailureReason] = []
        rank = self.registry.dependency_rank
        adjacency: dict[ConstitutionalLayer, set[ConstitutionalLayer]] = {layer: set() for layer in ConstitutionalLayer}

        for edge in edges:
            if rank[edge.upstream] >= rank[edge.downstream]:
                failures.append(InfrastructureFailureReason.REVERSE_DEPENDENCY)
            adjacency[edge.upstream].add(edge.downstream)

        if _has_cycle(adjacency):
            failures.append(InfrastructureFailureReason.DEPENDENCY_CYCLE)
        return tuple(dict.fromkeys(failures))

    def certify(
        self,
        prerequisites: Iterable[InfrastructurePrerequisiteEvidence],
        services: Iterable[InfrastructureServiceDeclaration],
        dependencies: Iterable[InfrastructureDependencyEdge],
        interface_requests: Iterable[InterfaceAccessRequest] = (),
    ) -> InfrastructureCertificationRecord:
        evidence_by_prerequisite = {item.prerequisite: item for item in prerequisites}
        prerequisite_statuses = {
            prerequisite: bool(evidence_by_prerequisite.get(prerequisite) and evidence_by_prerequisite[prerequisite].satisfied)
            for prerequisite in InfrastructureCertificationPrerequisite
        }

        service_violations = {
            service.service_id: failures
            for service in services
            if (failures := self.validate_service(service))
        }
        dependency_violations = self.validate_dependency_graph(dependencies)
        interface_violations = tuple(
            dict.fromkeys(
                failure
                for request in interface_requests
                for failure in self.validate_interface_access(request)
            )
        )

        failure_reasons: list[InfrastructureFailureReason] = []
        if not all(prerequisite_statuses.values()):
            failure_reasons.append(InfrastructureFailureReason.EVIDENCE_INCOMPLETE)
        for prerequisite, passed in prerequisite_statuses.items():
            if passed:
                continue
            failure_reasons.append(_failure_reason_for_prerequisite(prerequisite))
        for failures in service_violations.values():
            failure_reasons.extend(failures)
        failure_reasons.extend(dependency_violations)
        failure_reasons.extend(interface_violations)
        unique_failure_reasons = tuple(dict.fromkeys(failure_reasons))

        state = (
            InfrastructureCertificationState.PASS
            if not unique_failure_reasons
            else InfrastructureCertificationState.SUSPENDED_DOWNSTREAM_CERTIFICATION
        )
        invariant_statuses = {invariant: not unique_failure_reasons for invariant in InfrastructureInvariant}
        evidence_references = tuple(
            sorted(
                {
                    item.evidence_reference
                    for item in evidence_by_prerequisite.values()
                    if item.evidence_reference
                }
                | {
                    reference
                    for service in services
                    for reference in service.evidence_references
                    if reference
                }
            )
        )
        record = InfrastructureCertificationRecord(
            record_id="INF-001-CERTIFICATION",
            version=INF_001_VERSION,
            state=state,
            prerequisite_statuses=dict(prerequisite_statuses),
            service_violations=dict(service_violations),
            dependency_violations=dependency_violations,
            interface_violations=interface_violations,
            failure_reasons=unique_failure_reasons,
            downstream_certification_allowed=state == InfrastructureCertificationState.PASS,
            invariant_statuses=dict(invariant_statuses),
            evidence_references=evidence_references,
        )
        return record.with_digest()


def default_infrastructure_boundary() -> InfrastructureAuthorityBoundary:
    return InfrastructureBoundaryRegistry().boundary()


def _failure_reason_for_prerequisite(
    prerequisite: InfrastructureCertificationPrerequisite,
) -> InfrastructureFailureReason:
    mapping = {
        InfrastructureCertificationPrerequisite.REPOSITORY_IDENTITY_CERTIFIED: InfrastructureFailureReason.IDENTITY_UNPROVEN,
        InfrastructureCertificationPrerequisite.CANDIDATE_IDENTITY_CERTIFIED: InfrastructureFailureReason.IDENTITY_UNPROVEN,
        InfrastructureCertificationPrerequisite.RUNTIME_CONSTRUCTION_DETERMINISTIC: InfrastructureFailureReason.RUNTIME_UNVERIFIABLE,
        InfrastructureCertificationPrerequisite.WORKFLOW_INFRASTRUCTURE_CERTIFIED: InfrastructureFailureReason.AUTHORITY_UNVERIFIED,
        InfrastructureCertificationPrerequisite.AUTHORITY_INFRASTRUCTURE_CERTIFIED: InfrastructureFailureReason.AUTHORITY_UNVERIFIED,
        InfrastructureCertificationPrerequisite.LAW_VII_INFRASTRUCTURE_CERTIFIED: InfrastructureFailureReason.AUTHORITY_UNVERIFIED,
        InfrastructureCertificationPrerequisite.BRIDGE_REGISTRY_CERTIFIED: InfrastructureFailureReason.BRIDGES_UNCERTIFIED,
        InfrastructureCertificationPrerequisite.BRIDGE_CERTIFICATION_COMPLETE: InfrastructureFailureReason.BRIDGES_UNCERTIFIED,
        InfrastructureCertificationPrerequisite.PERSISTENCE_SUBSTRATE_CERTIFIED: InfrastructureFailureReason.INFRASTRUCTURE_INTEGRITY_UNESTABLISHED,
        InfrastructureCertificationPrerequisite.REPLAY_INFRASTRUCTURE_CERTIFIED: InfrastructureFailureReason.INFRASTRUCTURE_INTEGRITY_UNESTABLISHED,
        InfrastructureCertificationPrerequisite.AUDIT_INFRASTRUCTURE_CERTIFIED: InfrastructureFailureReason.EVIDENCE_INCOMPLETE,
        InfrastructureCertificationPrerequisite.PROOF_INFRASTRUCTURE_CERTIFIED: InfrastructureFailureReason.PROOF_GENERATION_FAILED,
        InfrastructureCertificationPrerequisite.DETERMINISTIC_EXECUTION_DEMONSTRATED: InfrastructureFailureReason.DETERMINISM_NOT_DEMONSTRATED,
    }
    return mapping[prerequisite]


def _has_cycle(adjacency: Mapping[ConstitutionalLayer, set[ConstitutionalLayer]]) -> bool:
    visiting: set[ConstitutionalLayer] = set()
    visited: set[ConstitutionalLayer] = set()

    def visit(layer: ConstitutionalLayer) -> bool:
        if layer in visiting:
            return True
        if layer in visited:
            return False
        visiting.add(layer)
        for next_layer in adjacency.get(layer, set()):
            if visit(next_layer):
                return True
        visiting.remove(layer)
        visited.add(layer)
        return False

    return any(visit(layer) for layer in adjacency)


def _stable_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=_json_default, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _json_default(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return dict(value)
    return str(value)
