"""Custody-only Enterprise Information Journey runtime for the Historian Office."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, replace
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping


HISTORIAN_RM002A_VERSION = "HISTORIAN-RM-002A/1.0.0"
HISTORIAN_OFFICE = "Historian Office"


class HistorianRuntimeError(ValueError):
    """Raised when Historian runtime behavior must fail closed."""

    def __init__(self, code: str, message: str, evidence: "BehavioralEvidence") -> None:
        super().__init__(message)
        self.code = code
        self.evidence = evidence


class JourneyState(str, Enum):
    CREATED = "Created"
    INITIALIZED = "Initialized"
    ACTIVE = "Active"
    COMPLETE = "Complete"
    CLOSED = "Closed"
    SUPERSEDED = "Superseded"


class ArtifactLifecycleState(str, Enum):
    ACCEPTED = "accepted"
    REGISTERED = "registered"
    SUPERSEDED = "updated through supersession"
    ARCHIVED = "archived"
    RETAINED = "retained"


class CustodyState(str, Enum):
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    VERIFIED = "VERIFIED"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class ProvenanceEdgeType(str, Enum):
    OBSERVED_BY = "OBSERVED_BY"
    CREATED_BY = "CREATED_BY"
    PRODUCED_BY = "PRODUCED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    TRANSFORMED_BY = "TRANSFORMED_BY"
    CONSUMES = "CONSUMES"
    REFERENCES = "REFERENCES"
    DEPENDS_ON = "DEPENDS_ON"
    AUTHORIZED_BY = "AUTHORIZED_BY"
    VALIDATED_BY = "VALIDATED_BY"
    CERTIFIED_BY = "CERTIFIED_BY"
    CORRECTED_BY = "CORRECTED_BY"
    CORRECTS = "CORRECTS"
    SUPERSEDED_BY = "SUPERSEDED_BY"
    SUPERSEDES = "SUPERSEDES"
    ARCHIVED_BY = "ARCHIVED_BY"
    RECONSTRUCTS = "RECONSTRUCTS"
    REPLAYS = "REPLAYS"
    SUPPORTS = "SUPPORTS"
    REJECTED_BY = "REJECTED_BY"
    REJECTS = "REJECTS"


class MissingInformationClassification(str, Enum):
    UNKNOWN = "Unknown"
    NOT_COLLECTED = "Not Collected"
    NOT_YET_AVAILABLE = "Not Yet Available"
    WITHHELD_BY_AUTHORITY = "Withheld by Authority"
    OUTSIDE_CONSTITUTIONAL_SCOPE = "Outside Constitutional Scope"
    LOST_PRIOR_TO_ACQUISITION = "Lost Prior to Acquisition"
    INVALIDATED = "Invalidated"
    PENDING_VERIFICATION = "Pending Verification"
    CONFLICTING_SOURCES = "Conflicting Sources"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


ALLOWED_TRANSITIONS: Mapping[JourneyState, JourneyState] = MappingProxyType(
    {
        JourneyState.CREATED: JourneyState.INITIALIZED,
        JourneyState.INITIALIZED: JourneyState.ACTIVE,
        JourneyState.ACTIVE: JourneyState.COMPLETE,
        JourneyState.COMPLETE: JourneyState.CLOSED,
        JourneyState.CLOSED: JourneyState.SUPERSEDED,
    }
)


@dataclass(frozen=True)
class BehavioralEvidence:
    evidence_id: str
    execution_id: str
    workflow_id: str
    journey_id: str
    artifact_id: str
    capability: str
    producing_office: str
    producing_component: str
    timestamp: str
    classification: str
    outcome: str
    details: Mapping[str, Any]
    evidence_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))
        object.__setattr__(self, "evidence_digest", _stable_digest(_without_digest(self, "evidence_digest")))


@dataclass(frozen=True)
class JourneyTransition:
    transition_id: str
    previous_state: str
    new_state: str
    timestamp: str
    executing_workflow: str
    authorization: str
    evidence_id: str


@dataclass(frozen=True)
class HistoricalArtifact:
    artifact_id: str
    artifact_type: str
    journey_id: str
    constitutional_owner: str
    workflow_id: str
    originating_office: str
    payload: Mapping[str, Any]
    registered_at: str
    custody_id: str
    lifecycle_state: str
    provenance_node_id: str
    artifact_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
        object.__setattr__(self, "artifact_digest", _stable_digest(_without_digest(self, "artifact_digest")))


@dataclass(frozen=True)
class HistoricalCustodyRecord:
    custody_id: str
    artifact_id: str
    artifact_type: str
    journey_id: str
    current_custodian_office: str
    previous_custodian: str
    custody_state: str
    assignment_authority: str
    assignment_timestamp: str
    acceptance_timestamp: str
    validation_timestamp: str
    verification_status: str
    supersession_status: str
    custody_evidence_references: tuple[str, ...]
    integrity_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "integrity_digest", _stable_digest(_without_digest(self, "integrity_digest")))


@dataclass(frozen=True)
class ProvenanceNode:
    node_id: str
    object_id: str
    object_classification: str
    constitutional_owner: str
    creation_timestamp: str
    producing_workflow: str
    producing_execution: str
    historical_version: str
    certification_state: str
    node_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_digest", _stable_digest(_without_digest(self, "node_digest")))


@dataclass(frozen=True)
class ProvenanceEdge:
    edge_id: str
    source_node: str
    destination_node: str
    relationship_type: str
    creation_event: str
    workflow_owner: str
    evidence_reference: str
    edge_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "edge_digest", _stable_digest(_without_digest(self, "edge_digest")))


@dataclass(frozen=True)
class LanguageArtifact:
    language_id: str
    journey_id: str
    raw_language: str
    structured_record: Mapping[str, Any]
    semantic_record: Mapping[str, Any]
    source_language: str
    producing_workflow: str
    timestamp: str
    language_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "structured_record", MappingProxyType(dict(self.structured_record)))
        object.__setattr__(self, "semantic_record", MappingProxyType(dict(self.semantic_record)))
        object.__setattr__(self, "language_digest", _stable_digest(_without_digest(self, "language_digest")))


@dataclass(frozen=True)
class MissingInformationRecord:
    deficiency_id: str
    journey_id: str
    affected_artifact: str
    constitutional_owner: str
    detecting_workflow: str
    classification: str
    discovery_timestamp: str
    associated_evidence: tuple[str, ...]
    impact_assessment: str
    recovery_status: str
    deficiency_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "deficiency_digest", _stable_digest(_without_digest(self, "deficiency_digest")))


@dataclass(frozen=True)
class CounterfactualBranch:
    branch_id: str
    journey_id: str
    branch_type: str
    source_artifact_id: str
    historical_state: str
    preservation_reason: str
    evidence_references: tuple[str, ...]
    branch_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch_digest", _stable_digest(_without_digest(self, "branch_digest")))


@dataclass(frozen=True)
class EnterpriseInformationJourney:
    journey_id: str
    constitutional_owner: str
    workflow_id: str
    authorization: str
    created_at: str
    lifecycle_state: JourneyState
    metadata: Mapping[str, Any]
    transitions: tuple[JourneyTransition, ...] = ()
    artifacts: tuple[HistoricalArtifact, ...] = ()
    custody_records: tuple[HistoricalCustodyRecord, ...] = ()
    provenance_nodes: tuple[ProvenanceNode, ...] = ()
    provenance_edges: tuple[ProvenanceEdge, ...] = ()
    language_artifacts: tuple[LanguageArtifact, ...] = ()
    missing_information: tuple[MissingInformationRecord, ...] = ()
    counterfactual_branches: tuple[CounterfactualBranch, ...] = ()
    evidence: tuple[BehavioralEvidence, ...] = ()
    superseded_by: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class HistoricalReconstructionResult:
    reconstruction_id: str
    journey_id: str
    lifecycle_state: str
    timeline: tuple[Mapping[str, Any], ...]
    artifact_ids: tuple[str, ...]
    custody_ids: tuple[str, ...]
    provenance_node_ids: tuple[str, ...]
    provenance_edge_ids: tuple[str, ...]
    language_ids: tuple[str, ...]
    missing_information_ids: tuple[str, ...]
    counterfactual_branch_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    completeness_status: str
    reconstruction_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "timeline", tuple(MappingProxyType(dict(item)) for item in self.timeline))
        object.__setattr__(self, "reconstruction_digest", _stable_digest(_without_digest(self, "reconstruction_digest")))


@dataclass(frozen=True)
class ReplayResult:
    replay_id: str
    journey_id: str
    reconstruction_digest: str
    replay_digest: str
    equivalent: bool
    evidence_id: str


class EnterpriseInformationJourneyRuntime:
    """Deterministic, in-memory Historian runtime with fail-closed behavior."""

    def __init__(self) -> None:
        self._journeys: dict[str, EnterpriseInformationJourney] = {}

    def create_journey(self, *, workflow_id: str, authorization: str, timestamp: str, metadata: Mapping[str, Any]) -> EnterpriseInformationJourney:
        self._require(workflow_id, "workflow_id", "CREATE")
        self._require(authorization, "authorization", "CREATE")
        self._require(timestamp, "timestamp", "CREATE")
        journey_id = _stable_id("EIJ", workflow_id, authorization, timestamp)
        if journey_id in self._journeys:
            self._fail("DUPLICATE_JOURNEY", journey_id, workflow_id, "lifecycle", timestamp, {"journey_id": journey_id})
        evidence = _evidence(journey_id, workflow_id, journey_id, "journey_lifecycle", timestamp, "PASS", {"transition": "CREATE"})
        transition = JourneyTransition(_stable_id("TRANS", journey_id, "NONE", JourneyState.CREATED.value, timestamp), "NONE", JourneyState.CREATED.value, timestamp, workflow_id, authorization, evidence.evidence_id)
        journey = EnterpriseInformationJourney(journey_id, HISTORIAN_OFFICE, workflow_id, authorization, timestamp, JourneyState.CREATED, metadata, transitions=(transition,), evidence=(evidence,))
        self._journeys[journey_id] = journey
        return journey

    def transition(self, journey_id: str, new_state: JourneyState, *, workflow_id: str, authorization: str, timestamp: str) -> EnterpriseInformationJourney:
        journey = self._get(journey_id)
        expected = ALLOWED_TRANSITIONS.get(journey.lifecycle_state)
        if expected != new_state:
            self._fail("INVALID_TRANSITION", journey_id, workflow_id, "journey_lifecycle", timestamp, {"current": journey.lifecycle_state.value, "requested": new_state.value})
        if workflow_id != journey.workflow_id or authorization != journey.authorization:
            self._fail("AUTHORIZATION_MISMATCH", journey_id, workflow_id, "journey_lifecycle", timestamp, {"expected_workflow": journey.workflow_id})
        if new_state is JourneyState.COMPLETE:
            self._validate_completion(journey, timestamp)
        evidence = _evidence(journey_id, workflow_id, journey_id, "journey_lifecycle", timestamp, "PASS", {"from": journey.lifecycle_state.value, "to": new_state.value})
        transition = JourneyTransition(_stable_id("TRANS", journey_id, journey.lifecycle_state.value, new_state.value, timestamp), journey.lifecycle_state.value, new_state.value, timestamp, workflow_id, authorization, evidence.evidence_id)
        updated = replace(journey, lifecycle_state=new_state, transitions=journey.transitions + (transition,), evidence=journey.evidence + (evidence,))
        self._journeys[journey_id] = updated
        return updated

    def register_artifact(self, journey_id: str, *, artifact_type: str, constitutional_owner: str, workflow_id: str, originating_office: str, payload: Mapping[str, Any], timestamp: str) -> EnterpriseInformationJourney:
        journey = self._get(journey_id)
        if journey.lifecycle_state is not JourneyState.ACTIVE:
            self._fail("REGISTRATION_STATE_VIOLATION", journey_id, workflow_id, "artifact_registration", timestamp, {"state": journey.lifecycle_state.value})
        if workflow_id != journey.workflow_id:
            self._fail("ARTIFACT_WORKFLOW_MISMATCH", journey_id, workflow_id, "artifact_registration", timestamp, {"journey_workflow": journey.workflow_id})
        for name, value in {"artifact_type": artifact_type, "constitutional_owner": constitutional_owner, "originating_office": originating_office, "timestamp": timestamp}.items():
            self._require(value, name, "REGISTER")
        artifact_id = _stable_id("HART", journey_id, artifact_type, constitutional_owner, workflow_id, _stable_digest(payload))
        if any(item.artifact_id == artifact_id for item in journey.artifacts):
            self._fail("DUPLICATE_ARTIFACT", journey_id, workflow_id, "artifact_registration", timestamp, {"artifact_id": artifact_id})
        evidence = _evidence(journey_id, workflow_id, artifact_id, "artifact_registration", timestamp, "PASS", {"artifact_type": artifact_type, "owner": constitutional_owner})
        custody = self._custody_record(journey_id, artifact_id, artifact_type, constitutional_owner, "", CustodyState.ACCEPTED, journey.authorization, timestamp, (evidence.evidence_id,))
        node = ProvenanceNode(_stable_id("PNODE", artifact_id), artifact_id, artifact_type, constitutional_owner, timestamp, workflow_id, evidence.execution_id, "1", "UNCERTIFIED")
        edge = ProvenanceEdge(_stable_id("PEDGE", journey_id, node.node_id, ProvenanceEdgeType.PRODUCED_BY.value), _stable_id("PNODE", journey_id), node.node_id, ProvenanceEdgeType.PRODUCED_BY.value, evidence.execution_id, workflow_id, evidence.evidence_id)
        journey_node = ProvenanceNode(_stable_id("PNODE", journey_id), journey_id, "Enterprise Information Journey", HISTORIAN_OFFICE, journey.created_at, journey.workflow_id, journey.transitions[0].transition_id, "1", "UNCERTIFIED")
        nodes = journey.provenance_nodes
        if not any(item.node_id == journey_node.node_id for item in nodes):
            nodes = nodes + (journey_node,)
        artifact = HistoricalArtifact(artifact_id, artifact_type, journey_id, constitutional_owner, workflow_id, originating_office, payload, timestamp, custody.custody_id, ArtifactLifecycleState.REGISTERED.value, node.node_id)
        updated = replace(
            journey,
            artifacts=journey.artifacts + (artifact,),
            custody_records=journey.custody_records + (custody,),
            provenance_nodes=nodes + (node,),
            provenance_edges=journey.provenance_edges + (edge,),
            evidence=journey.evidence + (evidence,),
        )
        self._journeys[journey_id] = updated
        return updated

    def add_provenance_edge(self, journey_id: str, *, source_artifact_id: str, destination_artifact_id: str, relationship_type: ProvenanceEdgeType, workflow_id: str, timestamp: str) -> EnterpriseInformationJourney:
        journey = self._get(journey_id)
        source = self._node_for_artifact(journey, source_artifact_id, workflow_id, timestamp)
        destination = self._node_for_artifact(journey, destination_artifact_id, workflow_id, timestamp)
        edge_id = _stable_id("PEDGE", source.node_id, destination.node_id, relationship_type.value)
        if any(edge.edge_id == edge_id for edge in journey.provenance_edges):
            self._fail("DUPLICATE_PROVENANCE_EDGE", journey_id, workflow_id, "provenance_graph", timestamp, {"edge_id": edge_id})
        evidence = _evidence(journey_id, workflow_id, edge_id, "provenance_graph", timestamp, "PASS", {"relationship_type": relationship_type.value})
        edge = ProvenanceEdge(edge_id, source.node_id, destination.node_id, relationship_type.value, evidence.execution_id, workflow_id, evidence.evidence_id)
        updated = replace(journey, provenance_edges=journey.provenance_edges + (edge,), evidence=journey.evidence + (evidence,))
        self._journeys[journey_id] = updated
        return updated

    def preserve_language(self, journey_id: str, *, raw_language: str, structured_record: Mapping[str, Any], semantic_record: Mapping[str, Any], source_language: str, workflow_id: str, timestamp: str) -> EnterpriseInformationJourney:
        journey = self._get(journey_id)
        if not raw_language:
            self._fail("MISSING_RAW_LANGUAGE", journey_id, workflow_id, "language_preservation", timestamp, {})
        language_id = _stable_id("LANG", journey_id, raw_language, source_language, timestamp)
        if any(item.language_id == language_id for item in journey.language_artifacts):
            self._fail("DUPLICATE_LANGUAGE", journey_id, workflow_id, "language_preservation", timestamp, {"language_id": language_id})
        evidence = _evidence(journey_id, workflow_id, language_id, "language_preservation", timestamp, "PASS", {"source_language": source_language})
        language = LanguageArtifact(language_id, journey_id, raw_language, structured_record, semantic_record, source_language, workflow_id, timestamp)
        updated = replace(journey, language_artifacts=journey.language_artifacts + (language,), evidence=journey.evidence + (evidence,))
        self._journeys[journey_id] = updated
        return updated

    def record_missing_information(self, journey_id: str, *, affected_artifact: str, constitutional_owner: str, workflow_id: str, classification: MissingInformationClassification, timestamp: str, impact_assessment: str, recovery_status: str) -> EnterpriseInformationJourney:
        journey = self._get(journey_id)
        deficiency_id = _stable_id("MISS", journey_id, affected_artifact, classification.value, timestamp)
        if any(item.deficiency_id == deficiency_id for item in journey.missing_information):
            self._fail("DUPLICATE_MISSING_INFORMATION", journey_id, workflow_id, "missing_information", timestamp, {"deficiency_id": deficiency_id})
        evidence = _evidence(journey_id, workflow_id, affected_artifact, "missing_information", timestamp, "PASS", {"classification": classification.value})
        record = MissingInformationRecord(deficiency_id, journey_id, affected_artifact, constitutional_owner, workflow_id, classification.value, timestamp, (evidence.evidence_id,), impact_assessment, recovery_status)
        updated = replace(journey, missing_information=journey.missing_information + (record,), evidence=journey.evidence + (evidence,))
        self._journeys[journey_id] = updated
        return updated

    def add_counterfactual_branch(self, journey_id: str, *, branch_type: str, source_artifact_id: str, historical_state: str, preservation_reason: str, workflow_id: str, timestamp: str) -> EnterpriseInformationJourney:
        journey = self._get(journey_id)
        if not any(artifact.artifact_id == source_artifact_id for artifact in journey.artifacts):
            self._fail("COUNTERFACTUAL_SOURCE_MISSING", journey_id, workflow_id, "counterfactual_retrieval", timestamp, {"source_artifact_id": source_artifact_id})
        branch_id = _stable_id("CF", journey_id, branch_type, source_artifact_id, historical_state)
        evidence = _evidence(journey_id, workflow_id, source_artifact_id, "counterfactual_retrieval", timestamp, "PASS", {"branch_type": branch_type})
        branch = CounterfactualBranch(branch_id, journey_id, branch_type, source_artifact_id, historical_state, preservation_reason, (evidence.evidence_id,))
        updated = replace(journey, counterfactual_branches=journey.counterfactual_branches + (branch,), evidence=journey.evidence + (evidence,))
        self._journeys[journey_id] = updated
        return updated

    def reconstruct(self, journey_id: str, *, workflow_id: str, timestamp: str) -> HistoricalReconstructionResult:
        journey = self._get(journey_id)
        self._verify_journey(journey, workflow_id, "historical_reconstruction", timestamp)
        timeline = tuple(sorted((_event_projection(item) for item in journey.transitions), key=lambda item: (item["timestamp"], item["id"])))
        result = HistoricalReconstructionResult(
            _stable_id("HREC", journey_id, timestamp, _stable_digest(timeline)),
            journey_id,
            journey.lifecycle_state.value,
            timeline,
            tuple(sorted(item.artifact_id for item in journey.artifacts)),
            tuple(sorted(item.custody_id for item in journey.custody_records)),
            tuple(sorted(item.node_id for item in journey.provenance_nodes)),
            tuple(sorted(item.edge_id for item in journey.provenance_edges)),
            tuple(sorted(item.language_id for item in journey.language_artifacts)),
            tuple(sorted(item.deficiency_id for item in journey.missing_information)),
            tuple(sorted(item.branch_id for item in journey.counterfactual_branches)),
            tuple(sorted(item.evidence_id for item in journey.evidence if item.capability not in {"deterministic_replay", "enterprise_learning_retrieval"})),
            "COMPLETE" if journey.artifacts and journey.custody_records and journey.provenance_edges else "INCOMPLETE",
        )
        if result.completeness_status != "COMPLETE":
            self._fail("INCOMPLETE_RECONSTRUCTION", journey_id, workflow_id, "historical_reconstruction", timestamp, {"status": result.completeness_status})
        return result

    def replay(self, journey_id: str, *, workflow_id: str, timestamp: str) -> ReplayResult:
        first = self.reconstruct(journey_id, workflow_id=workflow_id, timestamp=timestamp)
        second = self.reconstruct(journey_id, workflow_id=workflow_id, timestamp=timestamp)
        equivalent = first.reconstruction_digest == second.reconstruction_digest
        evidence = _evidence(journey_id, workflow_id, journey_id, "deterministic_replay", timestamp, "PASS" if equivalent else "FAIL", {"reconstruction_digest": first.reconstruction_digest})
        if not equivalent:
            self._fail("NON_DETERMINISTIC_REPLAY", journey_id, workflow_id, "deterministic_replay", timestamp, {})
        journey = self._get(journey_id)
        self._journeys[journey_id] = replace(journey, evidence=journey.evidence + (evidence,))
        return ReplayResult(_stable_id("REPLAY", journey_id, timestamp, first.reconstruction_digest), journey_id, first.reconstruction_digest, _stable_digest({"first": first.reconstruction_digest, "second": second.reconstruction_digest}), equivalent, evidence.evidence_id)

    def learning_projection(self, journey_id: str, *, requester: str, workflow_id: str, timestamp: str) -> Mapping[str, Any]:
        if requester != "Enterprise Learning":
            self._fail("UNAUTHORIZED_LEARNING_RETRIEVAL", journey_id, workflow_id, "enterprise_learning_retrieval", timestamp, {"requester": requester})
        journey = self._get(journey_id)
        reconstruction = self.reconstruct(journey_id, workflow_id=workflow_id, timestamp=timestamp)
        evidence = _evidence(journey_id, workflow_id, journey_id, "enterprise_learning_retrieval", timestamp, "PASS", {"requester": requester})
        self._journeys[journey_id] = replace(journey, evidence=journey.evidence + (evidence,))
        return MappingProxyType(
            {
                "journey_id": journey_id,
                "read_only": True,
                "historian_performed_learning": False,
                "artifact_ids": reconstruction.artifact_ids,
                "missing_information_ids": reconstruction.missing_information_ids,
                "counterfactual_branch_ids": reconstruction.counterfactual_branch_ids,
                "provenance_edge_ids": reconstruction.provenance_edge_ids,
                "reconstruction_digest": reconstruction.reconstruction_digest,
            }
        )

    def certification_report(self, journey_id: str, *, workflow_id: str, timestamp: str) -> Mapping[str, Any]:
        journey = self._get(journey_id)
        reconstruction = self.reconstruct(journey_id, workflow_id=workflow_id, timestamp=timestamp)
        capabilities = {item.capability for item in journey.evidence}
        required = {
            "journey_lifecycle",
            "artifact_registration",
            "provenance_graph",
            "language_preservation",
            "missing_information",
            "counterfactual_retrieval",
            "deterministic_replay",
            "enterprise_learning_retrieval",
        }
        return MappingProxyType(
            {
                "journey_id": journey_id,
                "runtime_version": HISTORIAN_RM002A_VERSION,
                "certification_status": "PASS" if required.issubset(capabilities) and reconstruction.completeness_status == "COMPLETE" else "FAIL",
                "capabilities_observed": tuple(sorted(capabilities)),
                "missing_capabilities": tuple(sorted(required - capabilities)),
                "reconstruction_digest": reconstruction.reconstruction_digest,
                "evidence_count": len(journey.evidence),
            }
        )

    def get_journey(self, journey_id: str) -> EnterpriseInformationJourney:
        return self._get(journey_id)

    def _custody_record(self, journey_id: str, artifact_id: str, artifact_type: str, custodian: str, previous: str, state: CustodyState, authority: str, timestamp: str, evidence_ids: tuple[str, ...]) -> HistoricalCustodyRecord:
        custody_id = _stable_id("HCR", journey_id, artifact_id, custodian, state.value)
        return HistoricalCustodyRecord(custody_id, artifact_id, artifact_type, journey_id, custodian, previous, state.value, authority, timestamp, timestamp, timestamp, "VALID", "CURRENT", evidence_ids)

    def _get(self, journey_id: str) -> EnterpriseInformationJourney:
        if journey_id not in self._journeys:
            self._fail("UNKNOWN_JOURNEY", journey_id, "", "repository_access", "", {"journey_id": journey_id})
        return self._journeys[journey_id]

    def _require(self, value: str, field_name: str, operation: str) -> None:
        if not value:
            self._fail(f"MISSING_{field_name.upper()}", "", "", operation, "", {field_name: value})

    def _node_for_artifact(self, journey: EnterpriseInformationJourney, artifact_id: str, workflow_id: str, timestamp: str) -> ProvenanceNode:
        for artifact in journey.artifacts:
            if artifact.artifact_id == artifact_id:
                for node in journey.provenance_nodes:
                    if node.node_id == artifact.provenance_node_id:
                        return node
        self._fail("UNKNOWN_PROVENANCE_ARTIFACT", journey.journey_id, workflow_id, "provenance_graph", timestamp, {"artifact_id": artifact_id})

    def _verify_journey(self, journey: EnterpriseInformationJourney, workflow_id: str, capability: str, timestamp: str) -> None:
        if workflow_id != journey.workflow_id:
            self._fail("WORKFLOW_MISMATCH", journey.journey_id, workflow_id, capability, timestamp, {"expected": journey.workflow_id})
        self._validate_graph(journey, timestamp)
        for artifact in journey.artifacts:
            if not any(custody.artifact_id == artifact.artifact_id and custody.current_custodian_office for custody in journey.custody_records):
                self._fail("BROKEN_CUSTODY_CHAIN", journey.journey_id, workflow_id, capability, timestamp, {"artifact_id": artifact.artifact_id})

    def _validate_completion(self, journey: EnterpriseInformationJourney, timestamp: str) -> None:
        if not journey.artifacts:
            self._fail("COMPLETION_WITHOUT_ARTIFACTS", journey.journey_id, journey.workflow_id, "journey_lifecycle", timestamp, {})
        self._validate_graph(journey, timestamp)
        if len({record.artifact_id for record in journey.custody_records}) != len({artifact.artifact_id for artifact in journey.artifacts}):
            self._fail("COMPLETION_CUSTODY_GAP", journey.journey_id, journey.workflow_id, "journey_lifecycle", timestamp, {})

    def _validate_graph(self, journey: EnterpriseInformationJourney, timestamp: str) -> None:
        node_ids = {node.node_id for node in journey.provenance_nodes}
        for edge in journey.provenance_edges:
            if edge.source_node not in node_ids or edge.destination_node not in node_ids:
                self._fail("BROKEN_PROVENANCE_EDGE", journey.journey_id, journey.workflow_id, "provenance_graph", timestamp, {"edge_id": edge.edge_id})

    def _fail(self, code: str, journey_id: str, workflow_id: str, capability: str, timestamp: str, details: Mapping[str, Any]) -> None:
        evidence = _evidence(journey_id or "UNKNOWN", workflow_id or "UNKNOWN", journey_id or "UNKNOWN", capability, timestamp or "UNKNOWN", "FAIL_CLOSED", {"failure_code": code, **dict(details)})
        raise HistorianRuntimeError(code, code, evidence)


def _event_projection(transition: JourneyTransition) -> Mapping[str, Any]:
    return MappingProxyType({"id": transition.transition_id, "timestamp": transition.timestamp, "from": transition.previous_state, "to": transition.new_state, "evidence_id": transition.evidence_id})


def _evidence(journey_id: str, workflow_id: str, artifact_id: str, capability: str, timestamp: str, outcome: str, details: Mapping[str, Any]) -> BehavioralEvidence:
    execution_id = _stable_id("EXEC", journey_id, workflow_id, capability, timestamp, _stable_digest(details))
    evidence_id = _stable_id("EVID", execution_id, artifact_id, outcome)
    return BehavioralEvidence(evidence_id, execution_id, workflow_id, journey_id, artifact_id, capability, HISTORIAN_OFFICE, "EnterpriseInformationJourneyRuntime", timestamp, "BEHAVIORAL", outcome, details)


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{_stable_digest(parts)[:16].upper()}"


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_json_ready(value), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _without_digest(value: Any, field_name: str) -> Mapping[str, Any]:
    payload = {item.name: getattr(value, item.name) for item in fields(value)}
    payload[field_name] = ""
    return payload


def _json_ready(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return _json_ready(asdict(value))
    return value
