"""Knowledge Graph Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .group import LIBRARIAN_GROUP_ID


KNOWLEDGE_GRAPH_OFFICE_ID = "LIBRARIAN-OFFICE-004"
KNOWLEDGE_GRAPH_STAFF_ID = "STF-084"


class KnowledgeNodeType(str, Enum):
    """Enterprise organizational node taxonomy."""

    ENGINEERING_ORDER = "engineering_order"
    DOCTRINE = "doctrine"
    SPECIFICATION = "specification"
    WORKFLOW = "workflow"
    SOFTWARE_COMPONENT = "software_component"
    AI_OFFICE = "ai_office"
    DATABASE_SCHEMA = "database_schema"
    PROMPT = "prompt"
    DECISION_MODEL = "decision_model"
    CASE_FILE = "case_file"
    HISTORIAN_REPORT = "historian_report"
    OPERATIONAL_ARTIFACT = "operational_artifact"


class KnowledgeRelationshipType(str, Enum):
    """Enterprise relationship taxonomy."""

    DEPENDS_ON = "depends_on"
    IMPLEMENTS = "implements"
    PRODUCES = "produces"
    CONSUMES = "consumes"
    VALIDATES = "validates"
    SUPERSEDES = "supersedes"
    REFERENCES = "references"
    EVIDENCES = "evidences"
    DERIVES_FROM = "derives_from"
    ROUTES_TO = "routes_to"


@dataclass(frozen=True)
class KnowledgeGraphNode:
    """Enterprise knowledge graph node."""

    node_id: str
    node_type: KnowledgeNodeType
    title: str
    version: str
    source_reference_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    owner_group_id: str
    content_hash: str


@dataclass(frozen=True)
class KnowledgeGraphEdge:
    """Enterprise knowledge graph relationship edge."""

    edge_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: KnowledgeRelationshipType
    evidence_ids: tuple[str, ...]
    version: str
    deterministic_weight: float


@dataclass(frozen=True)
class EnterpriseKnowledgeGraphArchitecture:
    """Enterprise knowledge graph architecture."""

    architecture_id: str
    node_count: int
    edge_count: int
    lineage_preserved: bool
    version_controlled: bool
    auditable: bool


@dataclass(frozen=True)
class NodeTaxonomyStandard:
    """Node taxonomy standard artifact."""

    taxonomy_id: str
    supported_node_types: tuple[KnowledgeNodeType, ...]
    node_count_by_type: dict[str, int]


@dataclass(frozen=True)
class RelationshipTaxonomyStandard:
    """Relationship taxonomy standard artifact."""

    taxonomy_id: str
    supported_relationship_types: tuple[KnowledgeRelationshipType, ...]
    relationship_count_by_type: dict[str, int]


@dataclass(frozen=True)
class SemanticTraceabilityRecord:
    """Semantic traceability framework record."""

    traceability_id: str
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    source_reference_ids: tuple[str, ...]
    complete: bool


@dataclass(frozen=True)
class DependencyDiscoveryRecord:
    """Dependency discovery engine result."""

    discovery_id: str
    root_node_id: str
    direct_dependency_ids: tuple[str, ...]
    transitive_dependency_ids: tuple[str, ...]
    missing_dependency_ids: tuple[str, ...]


@dataclass(frozen=True)
class OrganizationalImpactAnalysis:
    """Organizational impact analysis framework record."""

    impact_id: str
    changed_node_id: str
    impacted_node_ids: tuple[str, ...]
    impact_count: int
    deterministic_severity: str


@dataclass(frozen=True)
class GraphValidationRecord:
    """Graph validation standard result."""

    validation_id: str
    node_count: int
    edge_count: int
    missing_node_references: tuple[str, ...]
    conflicting_relationship_ids: tuple[str, ...]
    duplicate_node_ids: tuple[str, ...]
    orphan_node_ids: tuple[str, ...]
    graph_valid: bool


@dataclass(frozen=True)
class KnowledgeQueryRecord:
    """Knowledge query architecture record."""

    query_id: str
    normalized_terms: tuple[str, ...]
    matched_node_ids: tuple[str, ...]
    matched_edge_ids: tuple[str, ...]


@dataclass(frozen=True)
class EnterpriseIntelligenceDashboard:
    """Enterprise intelligence dashboard metrics."""

    dashboard_id: str
    node_count: int
    edge_count: int
    missing_relationship_count: int
    conflict_count: int
    orphan_count: int
    dependency_impact_count: int
    graph_health: str


@dataclass(frozen=True)
class HistoricalLineageRecord:
    """Historical relationship lineage record."""

    lineage_id: str
    node_id: str
    prior_version_hashes: tuple[str, ...]
    current_content_hash: str
    lineage_preserved: bool


@dataclass(frozen=True)
class KnowledgeGraphSystemPrompt:
    """Knowledge Graph Office prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class KnowledgeGraphOffice:
    """Enterprise semantic graph for ARGOS organizational knowledge."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.prompt_repository = prompt_repository
        self._nodes: dict[str, KnowledgeGraphNode] = {}
        self._edges: dict[str, KnowledgeGraphEdge] = {}
        self._lineage: dict[str, list[str]] = {}

    @property
    def nodes(self) -> tuple[KnowledgeGraphNode, ...]:
        """Return deterministic graph nodes."""
        return tuple(self._nodes[node_id] for node_id in sorted(self._nodes))

    @property
    def edges(self) -> tuple[KnowledgeGraphEdge, ...]:
        """Return deterministic graph edges."""
        return tuple(self._edges[edge_id] for edge_id in sorted(self._edges))

    def system_prompt(self) -> KnowledgeGraphSystemPrompt:
        """Return governing Knowledge Graph prompt."""
        return KnowledgeGraphSystemPrompt(
            "PROMPT-KGO-074",
            "1.0.0",
            (
                "You are the Knowledge Graph Office of ARGOS.\n\n"
                "Maintain the enterprise knowledge graph representing every organizational object and every "
                "relationship between those objects. Continuously validate graph integrity, preserve historical "
                "lineage, detect missing or conflicting relationships, calculate dependency impacts, enrich "
                "organizational memory, and provide deterministic knowledge navigation across every Engineering "
                "Order, doctrine, specification, workflow, software component, AI office, database, prompt, "
                "decision model, case file, historian report, and operational artifact."
            ),
        )

    def integrate_graph_objects(
        self,
        nodes: tuple[KnowledgeGraphNode, ...],
        edges: tuple[KnowledgeGraphEdge, ...],
        root_node_id: str,
        changed_node_id: str,
        conflicting_relationship_ids: tuple[str, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Integrate organizational graph objects and produce deterministic graph artifacts."""
        self.configuration_service.validate_startup()
        duplicate_node_ids = _duplicates(tuple(node.node_id for node in nodes))
        for node in nodes:
            prior_hashes = tuple(self._lineage.get(node.node_id, ()))
            if node.node_id in self._nodes and self._nodes[node.node_id].content_hash != node.content_hash:
                self._lineage.setdefault(node.node_id, []).append(self._nodes[node.node_id].content_hash)
            elif node.node_id not in self._lineage:
                self._lineage[node.node_id] = list(prior_hashes)
            self._nodes[node.node_id] = node
        for edge in edges:
            self._edges[edge.edge_id] = edge

        validation = _validate_graph(tuple(self._nodes.values()), tuple(self._edges.values()), duplicate_node_ids, conflicting_relationship_ids)
        dependency = _dependency_discovery(root_node_id, tuple(self._nodes), tuple(self._edges.values()))
        impact = _impact_analysis(changed_node_id, tuple(self._edges.values()))
        traceability = _traceability(tuple(self._nodes.values()), tuple(self._edges.values()))
        architecture = EnterpriseKnowledgeGraphArchitecture(
            f"EKGA-{document_sequence:06d}",
            len(self._nodes),
            len(self._edges),
            True,
            True,
            True,
        )
        node_taxonomy = NodeTaxonomyStandard(
            f"NTS-{document_sequence:06d}",
            tuple(KnowledgeNodeType),
            _count_by_type(tuple(self._nodes.values())),
        )
        relationship_taxonomy = RelationshipTaxonomyStandard(
            f"RTS-{document_sequence:06d}",
            tuple(KnowledgeRelationshipType),
            _count_relationships(tuple(self._edges.values())),
        )
        lineage = tuple(
            HistoricalLineageRecord(
                f"HLR-{hashlib.sha256(node.node_id.encode('utf-8')).hexdigest()[:8].upper()}",
                node.node_id,
                tuple(self._lineage.get(node.node_id, ())),
                node.content_hash,
                True,
            )
            for node in self.nodes
        )
        query = _query(" ".join(node.title for node in self._nodes.values()), tuple(self._nodes.values()), tuple(self._edges.values()))
        dashboard = EnterpriseIntelligenceDashboard(
            f"EID-{document_sequence:06d}",
            len(self._nodes),
            len(self._edges),
            len(validation.missing_node_references),
            len(conflicting_relationship_ids),
            len(validation.orphan_node_ids),
            impact.impact_count,
            "healthy" if validation.graph_valid else "attention",
        )
        return {
            "enterprise_knowledge_graph_architecture": self._persist_contract(
                "ENTERPRISE_KNOWLEDGE_GRAPH_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Enterprise Knowledge Graph Architecture.",
                {"architecture": architecture, "historical_lineage": lineage, "system_prompt": self.system_prompt()},
            ),
            "node_taxonomy_standard": self._persist_contract(
                "NODE_TAXONOMY_STANDARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Node Taxonomy Standard.",
                {"node_taxonomy": node_taxonomy, "graph_nodes": self.nodes},
            ),
            "relationship_taxonomy_standard": self._persist_contract(
                "RELATIONSHIP_TAXONOMY_STANDARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Relationship Taxonomy Standard.",
                {"relationship_taxonomy": relationship_taxonomy, "graph_edges": self.edges},
            ),
            "semantic_traceability_framework": self._persist_contract(
                "SEMANTIC_TRACEABILITY_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Semantic Traceability Framework.",
                {"semantic_traceability": traceability, "dependency_discovery": dependency},
            ),
            "organizational_impact_analysis_framework": self._persist_contract(
                "ORGANIZATIONAL_IMPACT_ANALYSIS_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Organizational Impact Analysis Framework.",
                {"impact_analysis": impact, "graph_validation": validation},
            ),
            "knowledge_query_architecture": self._persist_contract(
                "KNOWLEDGE_QUERY_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Knowledge Query Architecture.",
                {"query_record": query, "enterprise_intelligence_dashboard": dashboard},
            ),
        }

    def query(self, query_text: str) -> KnowledgeQueryRecord:
        """Query graph nodes and edges deterministically."""
        return _query(query_text, tuple(self._nodes.values()), tuple(self._edges.values()))

    def _persist_contract(
        self,
        contract_type: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        human_summary: str,
        payload: dict[str, Any],
    ) -> OperationalContract:
        contract = _contract(contract_type, case_file_id, trade_cycle_id, document_sequence, human_summary, payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract


def _duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return tuple(sorted(duplicates))


def _validate_graph(
    nodes: tuple[KnowledgeGraphNode, ...],
    edges: tuple[KnowledgeGraphEdge, ...],
    duplicate_node_ids: tuple[str, ...],
    conflicting_relationship_ids: tuple[str, ...],
) -> GraphValidationRecord:
    node_ids = {node.node_id for node in nodes}
    missing = tuple(sorted({item for edge in edges for item in (edge.source_node_id, edge.target_node_id) if item not in node_ids}))
    connected = {item for edge in edges for item in (edge.source_node_id, edge.target_node_id) if item in node_ids}
    orphans = tuple(sorted(node.node_id for node in nodes if node.node_id not in connected and edges))
    return GraphValidationRecord(
        f"GVR-{hashlib.sha256(':'.join(sorted(node_ids)).encode('utf-8')).hexdigest()[:8].upper()}",
        len(nodes),
        len(edges),
        missing,
        conflicting_relationship_ids,
        duplicate_node_ids,
        orphans,
        not missing and not conflicting_relationship_ids and not duplicate_node_ids,
    )


def _dependency_discovery(root_node_id: str, known_node_ids: tuple[str, ...], edges: tuple[KnowledgeGraphEdge, ...]) -> DependencyDiscoveryRecord:
    direct = tuple(sorted(edge.target_node_id for edge in edges if edge.source_node_id == root_node_id and edge.relationship_type == KnowledgeRelationshipType.DEPENDS_ON))
    discovered: set[str] = set(direct)
    frontier = list(direct)
    while frontier:
        current = frontier.pop(0)
        for edge in edges:
            if edge.source_node_id == current and edge.relationship_type == KnowledgeRelationshipType.DEPENDS_ON and edge.target_node_id not in discovered:
                discovered.add(edge.target_node_id)
                frontier.append(edge.target_node_id)
    known = set(known_node_ids)
    missing = tuple(sorted(item for item in discovered if item not in known))
    return DependencyDiscoveryRecord(
        f"DDR-{hashlib.sha256(root_node_id.encode('utf-8')).hexdigest()[:8].upper()}",
        root_node_id,
        direct,
        tuple(sorted(discovered)),
        missing,
    )


def _impact_analysis(changed_node_id: str, edges: tuple[KnowledgeGraphEdge, ...]) -> OrganizationalImpactAnalysis:
    impacted: set[str] = set()
    frontier = [changed_node_id]
    while frontier:
        current = frontier.pop(0)
        for edge in edges:
            if edge.target_node_id == current and edge.source_node_id not in impacted:
                impacted.add(edge.source_node_id)
                frontier.append(edge.source_node_id)
    severity = "high" if len(impacted) >= 3 else "medium" if impacted else "low"
    return OrganizationalImpactAnalysis(
        f"OIA-{hashlib.sha256(changed_node_id.encode('utf-8')).hexdigest()[:8].upper()}",
        changed_node_id,
        tuple(sorted(impacted)),
        len(impacted),
        severity,
    )


def _traceability(nodes: tuple[KnowledgeGraphNode, ...], edges: tuple[KnowledgeGraphEdge, ...]) -> SemanticTraceabilityRecord:
    evidence_ids = tuple(sorted({item for node in nodes for item in node.evidence_ids} | {item for edge in edges for item in edge.evidence_ids}))
    source_reference_ids = tuple(sorted({item for node in nodes for item in node.source_reference_ids}))
    return SemanticTraceabilityRecord(
        f"STR-{hashlib.sha256(':'.join(sorted(node.node_id for node in nodes)).encode('utf-8')).hexdigest()[:8].upper()}",
        tuple(sorted(node.node_id for node in nodes)),
        tuple(sorted(edge.edge_id for edge in edges)),
        evidence_ids,
        source_reference_ids,
        bool(evidence_ids) and bool(source_reference_ids),
    )


def _count_by_type(nodes: tuple[KnowledgeGraphNode, ...]) -> dict[str, int]:
    counts = {node_type.value: 0 for node_type in KnowledgeNodeType}
    for node in nodes:
        counts[node.node_type.value] += 1
    return counts


def _count_relationships(edges: tuple[KnowledgeGraphEdge, ...]) -> dict[str, int]:
    counts = {relationship_type.value: 0 for relationship_type in KnowledgeRelationshipType}
    for edge in edges:
        counts[edge.relationship_type.value] += 1
    return counts


def _query(query_text: str, nodes: tuple[KnowledgeGraphNode, ...], edges: tuple[KnowledgeGraphEdge, ...]) -> KnowledgeQueryRecord:
    terms = tuple(_normalize_terms(query_text))
    matched_nodes = []
    for node in nodes:
        haystack = set(_normalize_terms(f"{node.node_id} {node.node_type.value} {node.title} {node.owner_group_id} {' '.join(node.evidence_ids)}"))
        if all(term in haystack for term in terms):
            matched_nodes.append(node.node_id)
    matched_edges = []
    for edge in edges:
        haystack = set(_normalize_terms(f"{edge.edge_id} {edge.source_node_id} {edge.target_node_id} {edge.relationship_type.value} {' '.join(edge.evidence_ids)}"))
        if all(term in haystack for term in terms):
            matched_edges.append(edge.edge_id)
    return KnowledgeQueryRecord(
        f"KQR-{hashlib.sha256(':'.join(terms).encode('utf-8')).hexdigest()[:8].upper()}",
        terms,
        tuple(sorted(matched_nodes)),
        tuple(sorted(matched_edges)),
    )


def _normalize_terms(value: str) -> tuple[str, ...]:
    return tuple(term for term in "".join(char.lower() if char.isalnum() else " " for char in value).split() if term)


def _contract(
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    document_sequence: int,
    human_summary: str,
    payload: dict[str, Any],
) -> OperationalContract:
    created = utc_timestamp()
    normalized_payload = _json_ready(payload)
    signature_hash = hashlib.sha256(json.dumps(normalized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        parent_contract_ids=(),
        produced_by_staff_id=KNOWLEDGE_GRAPH_STAFF_ID,
        produced_by_group_id=LIBRARIAN_GROUP_ID,
        intended_consumer_group_id=LIBRARIAN_GROUP_ID,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=human_summary,
        machine_payload=normalized_payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
