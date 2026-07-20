"""MO-INF-003 Infrastructure authority and bridge doctrine controls."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


INF_003_VERSION = "MO-INF-003/1.0.0"


class BridgeDirection(str, Enum):
    UNIDIRECTIONAL = "UNIDIRECTIONAL"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class InfrastructureGraphStatus(str, Enum):
    CERTIFIED = "CERTIFIED"
    FAIL_CLOSED = "FAIL_CLOSED"


class InfrastructureGraphFailure(str, Enum):
    UNCERTIFIED_BRIDGE = "uncertified_bridge"
    UNCERTIFIED_AUTHORITY = "uncertified_authority"
    UNCERTIFIED_DEPENDENCY = "uncertified_dependency"
    DUPLICATE_BRIDGE = "duplicate_bridge"
    DUPLICATE_AUTHORITY = "duplicate_authority"
    SHARED_BRIDGE_OWNER = "shared_bridge_owner"
    SHARED_AUTHORITY_OWNER = "shared_authority_owner"
    UNDECLARED_COMPONENT = "undeclared_component"
    UNDECLARED_OBJECT = "undeclared_object"
    AUTHORITY_INCOMPATIBLE = "authority_incompatible"
    DIRECT_COMMUNICATION = "direct_communication"
    DYNAMIC_DEPENDENCY = "dynamic_dependency"
    DEPENDENCY_CYCLE = "dependency_cycle"


@dataclass(frozen=True)
class BridgeDefinition:
    bridge_id: str
    source_component: str
    destination_component: str
    bridge_type: str
    constitutional_objects: tuple[str, ...]
    authority_requirements: tuple[str, ...]
    certification_status: str
    version: str
    evidence_package: str
    approval_history: tuple[str, ...]
    certification_timestamp: str
    owner: str
    direction: BridgeDirection


@dataclass(frozen=True)
class AuthorityDefinition:
    authority_id: str
    authority_name: str
    owner: str
    authorized_operations: tuple[str, ...]
    required_preconditions: tuple[str, ...]
    revocation_conditions: tuple[str, ...]
    certification_status: str
    evidence: str
    version: str


@dataclass(frozen=True)
class RuntimeDependency:
    producer: str
    consumer: str
    bridge_id: str
    required_authority: str
    required_objects: tuple[str, ...]
    certification_status: str
    version: str
    evidence: str
    dynamic: bool = False
    direct_communication: bool = False


@dataclass(frozen=True)
class RuntimeInfrastructureGraph:
    services: tuple[str, ...]
    workers: tuple[str, ...]
    queues: tuple[str, ...]
    state_managers: tuple[str, ...]
    repositories: tuple[str, ...]
    event_infrastructure: tuple[str, ...]
    audit_infrastructure: tuple[str, ...]
    storage_infrastructure: tuple[str, ...]
    proof_infrastructure: tuple[str, ...]
    recovery_infrastructure: tuple[str, ...]

    def components(self) -> set[str]:
        return set().union(
            self.services,
            self.workers,
            self.queues,
            self.state_managers,
            self.repositories,
            self.event_infrastructure,
            self.audit_infrastructure,
            self.storage_infrastructure,
            self.proof_infrastructure,
            self.recovery_infrastructure,
        )


@dataclass(frozen=True)
class InfrastructureGraphCertification:
    status: InfrastructureGraphStatus
    failures: tuple[InfrastructureGraphFailure, ...]


class InfrastructureAuthorityBridgeCertifier:
    """Certifies bridge registry, authority registry, dependency graph, and runtime topology."""

    def certify(
        self,
        bridges: Iterable[BridgeDefinition],
        authorities: Iterable[AuthorityDefinition],
        dependencies: Iterable[RuntimeDependency],
        runtime_graph: RuntimeInfrastructureGraph,
    ) -> InfrastructureGraphCertification:
        bridge_items = tuple(bridges)
        authority_items = tuple(authorities)
        dependency_items = tuple(dependencies)
        bridge_by_id = {bridge.bridge_id: bridge for bridge in bridge_items}
        authority_by_id = {authority.authority_id: authority for authority in authority_items}
        components = runtime_graph.components()
        failures: list[InfrastructureGraphFailure] = []

        if len(bridge_by_id) != len(bridge_items):
            failures.append(InfrastructureGraphFailure.DUPLICATE_BRIDGE)
        if len(authority_by_id) != len(authority_items):
            failures.append(InfrastructureGraphFailure.DUPLICATE_AUTHORITY)
        if any(not bridge.owner or "," in bridge.owner for bridge in bridge_items):
            failures.append(InfrastructureGraphFailure.SHARED_BRIDGE_OWNER)
        if any(not authority.owner or "," in authority.owner for authority in authority_items):
            failures.append(InfrastructureGraphFailure.SHARED_AUTHORITY_OWNER)
        if any(bridge.certification_status != "CERTIFIED" for bridge in bridge_items):
            failures.append(InfrastructureGraphFailure.UNCERTIFIED_BRIDGE)
        if any(authority.certification_status != "CERTIFIED" for authority in authority_items):
            failures.append(InfrastructureGraphFailure.UNCERTIFIED_AUTHORITY)

        adjacency: dict[str, set[str]] = {component: set() for component in components}
        for dependency in dependency_items:
            bridge = bridge_by_id.get(dependency.bridge_id)
            authority = authority_by_id.get(dependency.required_authority)
            if dependency.certification_status != "CERTIFIED":
                failures.append(InfrastructureGraphFailure.UNCERTIFIED_DEPENDENCY)
            if dependency.dynamic:
                failures.append(InfrastructureGraphFailure.DYNAMIC_DEPENDENCY)
            if dependency.direct_communication:
                failures.append(InfrastructureGraphFailure.DIRECT_COMMUNICATION)
            if not bridge or not authority:
                failures.append(InfrastructureGraphFailure.AUTHORITY_INCOMPATIBLE)
                continue
            if dependency.producer not in components or dependency.consumer not in components:
                failures.append(InfrastructureGraphFailure.UNDECLARED_COMPONENT)
            if not set(dependency.required_objects).issubset(set(bridge.constitutional_objects)):
                failures.append(InfrastructureGraphFailure.UNDECLARED_OBJECT)
            if dependency.required_authority not in bridge.authority_requirements:
                failures.append(InfrastructureGraphFailure.AUTHORITY_INCOMPATIBLE)
            adjacency.setdefault(dependency.producer, set()).add(dependency.consumer)

        if _has_cycle(adjacency):
            failures.append(InfrastructureGraphFailure.DEPENDENCY_CYCLE)

        unique_failures = tuple(dict.fromkeys(failures))
        return InfrastructureGraphCertification(
            status=InfrastructureGraphStatus.CERTIFIED if not unique_failures else InfrastructureGraphStatus.FAIL_CLOSED,
            failures=unique_failures,
        )


def _has_cycle(adjacency: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for neighbor in adjacency.get(node, set()):
            if visit(neighbor):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in adjacency)
