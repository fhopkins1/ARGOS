"""MO-TR-019 reconciliation evidence, replay, and certification doctrine."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.foundation.contracts import utc_timestamp


MO_TR_019_VERSION = "MO-TR-019/1.0.0"


class EvidenceNodeType(str, Enum):
    RAW_OBSERVATION = "RAW_OBSERVATION"
    NORMALIZED_OBSERVATION = "NORMALIZED_OBSERVATION"
    IDENTITY_RECORD = "IDENTITY_RECORD"
    COMPARABILITY_RECORD = "COMPARABILITY_RECORD"
    SOURCE_RECORD = "SOURCE_RECORD"
    SOURCE_ORIGIN_RECORD = "SOURCE_ORIGIN_RECORD"
    SOURCE_INDEPENDENCE_RECORD = "SOURCE_INDEPENDENCE_RECORD"
    AUTHORITY_RECORD = "AUTHORITY_RECORD"
    TIMESTAMP_RECORD = "TIMESTAMP_RECORD"
    VERSION_RECORD = "VERSION_RECORD"
    NORMALIZATION_RECORD = "NORMALIZATION_RECORD"
    TOLERANCE_RECORD = "TOLERANCE_RECORD"
    CONFLICT_RECORD = "CONFLICT_RECORD"
    MATERIALITY_RECORD = "MATERIALITY_RECORD"
    EVIDENCE_SUFFICIENCY_RECORD = "EVIDENCE_SUFFICIENCY_RECORD"
    ANALYST_DECISION = "ANALYST_DECISION"
    RISK_DECISION = "RISK_DECISION"
    TRADER_ELIGIBILITY_DECISION = "TRADER_ELIGIBILITY_DECISION"
    BROKER_RECONCILIATION_RECORD = "BROKER_RECONCILIATION_RECORD"
    HUMAN_REVIEW_RECORD = "HUMAN_REVIEW_RECORD"
    HISTORIAN_RECORD = "HISTORIAN_RECORD"
    DOCTRINE_VERSION = "DOCTRINE_VERSION"
    RULE_VERSION = "RULE_VERSION"
    REPLAY_RECORD = "REPLAY_RECORD"
    AUDIT_RECORD = "AUDIT_RECORD"
    CERTIFICATION_RECORD = "CERTIFICATION_RECORD"


class EvidenceEdgeType(str, Enum):
    DERIVED_FROM = "DERIVED_FROM"
    NORMALIZED_FROM = "NORMALIZED_FROM"
    SAME_ORIGIN_AS = "SAME_ORIGIN_AS"
    COPIED_FROM = "COPIED_FROM"
    CORROBORATES = "CORROBORATES"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    SUPERSEDES = "SUPERSEDES"
    CORRECTS = "CORRECTS"
    REVISES = "REVISES"
    AMENDS = "AMENDS"
    COMPARES = "COMPARES"
    CLASSIFIED_BY = "CLASSIFIED_BY"
    RESOLVED_BY = "RESOLVED_BY"
    RESTRICTED_BY = "RESTRICTED_BY"
    BLOCKED_BY = "BLOCKED_BY"
    ROUTED_TO = "ROUTED_TO"
    REVIEWED_BY = "REVIEWED_BY"
    AUTHORIZED_BY = "AUTHORIZED_BY"
    GOVERNED_BY = "GOVERNED_BY"
    REPLAYED_FROM = "REPLAYED_FROM"
    CERTIFIED_BY = "CERTIFIED_BY"
    PRESERVED_BY = "PRESERVED_BY"


class ReconciliationCertificationState(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    CERTIFICATION_PENDING = "CERTIFICATION_PENDING"
    CERTIFIED = "CERTIFIED"
    CERTIFIED_WITH_LIMITATION = "CERTIFIED_WITH_LIMITATION"
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"
    CERTIFICATION_REVOKED = "CERTIFICATION_REVOKED"
    REPLAY_MISMATCH = "REPLAY_MISMATCH"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    UNAUTHORIZED_ACTION = "UNAUTHORIZED_ACTION"
    UNKNOWN_CERTIFICATION_STATE = "UNKNOWN_CERTIFICATION_STATE"


@dataclass(frozen=True)
class EvidenceGraphNode:
    node_id: str
    node_type: EvidenceNodeType
    artifact_id: str
    artifact_hash: str
    doctrine_version: str
    created_at: str


@dataclass(frozen=True)
class EvidenceGraphEdge:
    edge_id: str
    edge_type: EvidenceEdgeType
    from_node_id: str
    to_node_id: str
    rule_version: str
    created_at: str


@dataclass(frozen=True)
class ReconciliationEvidencePackage:
    reconciliation_id: str
    reconciliation_attempt_id: str
    workflow_id: str
    workflow_execution_token_id: str
    decision_object_id: str
    decision_object_version: str
    fact_domain: str
    claim_id: str
    instrument_id: str
    issuer_id: str
    account_id: str
    broker_id: str
    office_performing_reconciliation: str
    office_authority_record: str
    competing_observation_ids: tuple[str, ...]
    competing_observation_hashes: tuple[str, ...]
    raw_evidence_references: tuple[str, ...]
    normalized_observation_references: tuple[str, ...]
    observation_identity_record: str
    comparability_record: str
    source_authority_records: tuple[str, ...]
    source_precedence_rule: str
    source_independence_record: str
    timestamp_governing_rule: str
    version_comparison_record: str
    conflict_classification: str
    conflict_record_id: str
    applicable_reconciliation_rule: str
    doctrine_version: str
    rule_version: str
    intermediate_dispositions: tuple[str, ...]
    final_reconciliation_disposition: str
    risk_consequence: str
    trader_consequence: str
    resolution_state: str
    created_time: str
    finalized_time: str
    replay_id: str
    audit_id: str
    predecessor_package_id: str = ""
    package_hash: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_hash", _stable_digest(self))


@dataclass(frozen=True)
class ReconciliationCertificationRecord:
    certification_id: str
    reconciliation_id: str
    evidence_package_hash: str
    certification_state: ReconciliationCertificationState
    reason_codes: tuple[str, ...]
    replay_id: str
    audit_id: str
    doctrine_version: str
    certified_at: str
    record_digest: str = field(default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_digest", _stable_digest(self))


class EvidenceGraphRepository:
    def __init__(self) -> None:
        self._nodes: dict[str, EvidenceGraphNode] = {}
        self._edges: dict[str, EvidenceGraphEdge] = {}

    def append_node(self, node: EvidenceGraphNode) -> None:
        if node.node_id in self._nodes:
            raise ValueError("evidence graph nodes are append-only")
        self._nodes[node.node_id] = node

    def append_edge(self, edge: EvidenceGraphEdge) -> None:
        if edge.edge_id in self._edges:
            raise ValueError("evidence graph edges are append-only")
        self._edges[edge.edge_id] = edge

    def node_types(self) -> set[EvidenceNodeType]:
        return {node.node_type for node in self._nodes.values()}


class CertificationRepository:
    def __init__(self) -> None:
        self._records: dict[str, ReconciliationCertificationRecord] = {}

    def append(self, record: ReconciliationCertificationRecord) -> None:
        if record.certification_id in self._records:
            raise ValueError("certification records are append-only")
        self._records[record.certification_id] = record


class ReconciliationCertificationService:
    def __init__(self, repository: CertificationRepository | None = None) -> None:
        self.repository = repository or CertificationRepository()

    def certify(self, package: ReconciliationEvidencePackage, graph: EvidenceGraphRepository, *, replay_matches: bool = True, authorized_offices: tuple[str, ...] = ("Intelligence", "Seeker", "Analyst", "Risk", "Trader", "Historian", "SourceHealth", "HumanEscalation")) -> ReconciliationCertificationRecord:
        reasons = _certification_reasons(package, graph, replay_matches, authorized_offices)
        state = _certification_state(reasons)
        record = ReconciliationCertificationRecord(_stable_id("CERT", package.reconciliation_id, package.package_hash, state.value), package.reconciliation_id, package.package_hash, state, tuple(reasons or ("certification_complete",)), package.replay_id, package.audit_id, MO_TR_019_VERSION, utc_timestamp())
        self.repository.append(record)
        return record


def evidence_node(node_type: EvidenceNodeType, artifact_id: str, artifact: Any) -> EvidenceGraphNode:
    return EvidenceGraphNode(_stable_id("NODE", node_type.value, artifact_id), node_type, artifact_id, _stable_digest(artifact), MO_TR_019_VERSION, utc_timestamp())


def evidence_edge(edge_type: EvidenceEdgeType, from_node_id: str, to_node_id: str) -> EvidenceGraphEdge:
    return EvidenceGraphEdge(_stable_id("EDGE", edge_type.value, from_node_id, to_node_id), edge_type, from_node_id, to_node_id, MO_TR_019_VERSION, utc_timestamp())


def _certification_reasons(package: ReconciliationEvidencePackage, graph: EvidenceGraphRepository, replay_matches: bool, authorized_offices: tuple[str, ...]) -> list[str]:
    reasons: list[str] = []
    if not package.reconciliation_id or not package.workflow_id or not package.doctrine_version:
        reasons.append("UNKNOWN_CERTIFICATION_STATE:mandatory_identity_missing")
    if package.package_hash != _stable_digest(package):
        reasons.append("INTEGRITY_FAILURE:package_hash_mismatch")
    if package.office_performing_reconciliation not in authorized_offices:
        reasons.append("UNAUTHORIZED_ACTION:office_not_authorized")
    mandatory_fields = (
        package.competing_observation_ids,
        package.competing_observation_hashes,
        package.raw_evidence_references,
        package.observation_identity_record,
        package.comparability_record,
        package.source_authority_records,
        package.source_independence_record,
        package.timestamp_governing_rule,
        package.conflict_classification,
        package.applicable_reconciliation_rule,
        package.final_reconciliation_disposition,
        package.risk_consequence,
        package.trader_consequence,
    )
    if any(not item for item in mandatory_fields):
        reasons.append("EVIDENCE_INCOMPLETE:EVIDENCE_CHAIN_INCOMPLETE")
    required_nodes = {EvidenceNodeType.RAW_OBSERVATION, EvidenceNodeType.AUTHORITY_RECORD, EvidenceNodeType.SOURCE_INDEPENDENCE_RECORD, EvidenceNodeType.CONFLICT_RECORD, EvidenceNodeType.RISK_DECISION, EvidenceNodeType.TRADER_ELIGIBILITY_DECISION}
    if not required_nodes <= graph.node_types():
        reasons.append("EVIDENCE_INCOMPLETE:mandatory_graph_nodes_missing")
    if not replay_matches:
        reasons.append("REPLAY_MISMATCH:deterministic_replay_failed")
    if "LIMITATION" in package.final_reconciliation_disposition:
        reasons.append("CERTIFIED_WITH_LIMITATION:final_disposition_limited")
    return reasons


def _certification_state(reasons: list[str]) -> ReconciliationCertificationState:
    precedence = [
        ReconciliationCertificationState.UNKNOWN_CERTIFICATION_STATE,
        ReconciliationCertificationState.INTEGRITY_FAILURE,
        ReconciliationCertificationState.UNAUTHORIZED_ACTION,
        ReconciliationCertificationState.EVIDENCE_INCOMPLETE,
        ReconciliationCertificationState.REPLAY_MISMATCH,
        ReconciliationCertificationState.CERTIFICATION_REVOKED,
        ReconciliationCertificationState.CERTIFICATION_FAILED,
        ReconciliationCertificationState.CERTIFIED_WITH_LIMITATION,
    ]
    for state in precedence:
        if any(reason.startswith(state.value) for reason in reasons):
            return state
    return ReconciliationCertificationState.CERTIFIED


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{_stable_digest(parts)[:24].upper()}"


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return dict(value)
    if is_dataclass(value):
        return {field_info.name: _jsonable(getattr(value, field_info.name)) for field_info in fields(value) if field_info.name not in {"record_digest", "package_hash"}}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(item) for item in value]
    return value
