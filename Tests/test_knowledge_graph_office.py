from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.librarian import (  # noqa: E402
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphOffice,
    KnowledgeNodeType,
    KnowledgeRelationshipType,
)


def config() -> ConfigurationService:
    return ConfigurationService.load(
        {
            "environment": "development",
            "config_version": "1.0.0",
            "schema_version": "1.0.0",
            "log_level": "INFO",
            "live_trading_enabled": False,
            "feature_flags": {},
            "secret_references": [],
        },
        {},
    )


def nodes() -> tuple[KnowledgeGraphNode, ...]:
    return (
        KnowledgeGraphNode("EO-074", KnowledgeNodeType.ENGINEERING_ORDER, "Knowledge Graph Office", "1.0.0", ("SPEC-EO-074",), ("EV-074",), "LIBRARIAN-GROUP", "HASH-EO-074"),
        KnowledgeGraphNode("DOC-072", KnowledgeNodeType.DOCTRINE, "Doctrine Management Office", "1.0.0", ("DOC-072",), ("EV-072",), "LIBRARIAN-GROUP", "HASH-DOC-072"),
        KnowledgeGraphNode("SPEC-073", KnowledgeNodeType.SPECIFICATION, "Specification Repository Office", "1.0.0", ("SPEC-073",), ("EV-073",), "LIBRARIAN-GROUP", "HASH-SPEC-073"),
        KnowledgeGraphNode("PROMPT-KGO-074", KnowledgeNodeType.PROMPT, "Knowledge Graph Office Prompt", "1.0.0", ("PROMPT-074",), ("EV-PROMPT-074",), "LIBRARIAN-GROUP", "HASH-PROMPT-074"),
    )


def edges() -> tuple[KnowledgeGraphEdge, ...]:
    return (
        KnowledgeGraphEdge("EDGE-074-073", "EO-074", "SPEC-073", KnowledgeRelationshipType.DEPENDS_ON, ("EV-EDGE-1",), "1.0.0", 1.0),
        KnowledgeGraphEdge("EDGE-074-072", "EO-074", "DOC-072", KnowledgeRelationshipType.REFERENCES, ("EV-EDGE-2",), "1.0.0", 0.8),
        KnowledgeGraphEdge("EDGE-074-PROMPT", "PROMPT-KGO-074", "EO-074", KnowledgeRelationshipType.IMPLEMENTS, ("EV-EDGE-3",), "1.0.0", 1.0),
    )


def integrate(
    office: KnowledgeGraphOffice,
    *,
    graph_nodes: tuple[KnowledgeGraphNode, ...] = nodes(),
    graph_edges: tuple[KnowledgeGraphEdge, ...] = edges(),
    conflicts: tuple[str, ...] = (),
    sequence: int = 7401,
):
    return office.integrate_graph_objects(
        graph_nodes,
        graph_edges,
        "EO-074",
        "SPEC-073",
        conflicts,
        "CF-001",
        "TC-001",
        sequence,
    )


class KnowledgeGraphOfficeTests(unittest.TestCase):
    def test_graph_architecture_taxonomies_traceability_and_audit_are_generated(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        office = KnowledgeGraphOffice(config(), persistence, audit, PromptRepository())

        artifacts = integrate(office)

        architecture = artifacts["enterprise_knowledge_graph_architecture"].machine_payload["architecture"]
        node_taxonomy = artifacts["node_taxonomy_standard"].machine_payload["node_taxonomy"]
        relationship_taxonomy = artifacts["relationship_taxonomy_standard"].machine_payload["relationship_taxonomy"]
        traceability = artifacts["semantic_traceability_framework"].machine_payload["semantic_traceability"]
        self.assertEqual(architecture["node_count"], 4)
        self.assertEqual(node_taxonomy["node_count_by_type"]["engineering_order"], 1)
        self.assertEqual(relationship_taxonomy["relationship_count_by_type"]["depends_on"], 1)
        self.assertTrue(traceability["complete"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["enterprise_knowledge_graph_architecture"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_dependency_discovery_and_impact_analysis_are_deterministic(self) -> None:
        office = KnowledgeGraphOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = integrate(office)

        dependency = artifacts["semantic_traceability_framework"].machine_payload["dependency_discovery"]
        impact = artifacts["organizational_impact_analysis_framework"].machine_payload["impact_analysis"]
        self.assertEqual(dependency["direct_dependency_ids"], ["SPEC-073"])
        self.assertEqual(dependency["missing_dependency_ids"], [])
        self.assertEqual(impact["changed_node_id"], "SPEC-073")
        self.assertEqual(impact["impacted_node_ids"], ["EO-074", "PROMPT-KGO-074"])
        self.assertEqual(impact["deterministic_severity"], "medium")

    def test_graph_validation_detects_missing_conflicting_and_orphan_relationships(self) -> None:
        office = KnowledgeGraphOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        graph_nodes = (*nodes(), KnowledgeGraphNode("CASE-001", KnowledgeNodeType.CASE_FILE, "Isolated Case File", "1.0.0", ("CASE-001",), ("EV-CASE",), "EXECUTIVE-GROUP", "HASH-CASE"))
        graph_edges = (*edges(), KnowledgeGraphEdge("EDGE-MISSING", "EO-074", "MISSING-NODE", KnowledgeRelationshipType.DEPENDS_ON, ("EV-MISSING",), "1.0.0", 1.0))

        artifacts = integrate(office, graph_nodes=graph_nodes, graph_edges=graph_edges, conflicts=("EDGE-074-072",))

        validation = artifacts["organizational_impact_analysis_framework"].machine_payload["graph_validation"]
        dashboard = artifacts["knowledge_query_architecture"].machine_payload["enterprise_intelligence_dashboard"]
        self.assertEqual(validation["missing_node_references"], ["MISSING-NODE"])
        self.assertEqual(validation["conflicting_relationship_ids"], ["EDGE-074-072"])
        self.assertEqual(validation["orphan_node_ids"], ["CASE-001"])
        self.assertFalse(validation["graph_valid"])
        self.assertEqual(dashboard["graph_health"], "attention")

    def test_query_architecture_returns_nodes_and_edges(self) -> None:
        office = KnowledgeGraphOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        integrate(office)

        node_query = office.query("knowledge graph")
        edge_query = office.query("depends on")

        self.assertEqual(node_query.matched_node_ids, ("EO-074", "PROMPT-KGO-074"))
        self.assertEqual(edge_query.matched_edge_ids, ("EDGE-074-073",))

    def test_lineage_and_prompt_are_preserved(self) -> None:
        office = KnowledgeGraphOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        integrate(office)
        revised = (
            KnowledgeGraphNode("EO-074", KnowledgeNodeType.ENGINEERING_ORDER, "Knowledge Graph Office", "1.0.1", ("SPEC-EO-074",), ("EV-074",), "LIBRARIAN-GROUP", "HASH-EO-074-REV2"),
        )

        artifacts = integrate(office, graph_nodes=revised, graph_edges=(), sequence=7410)

        prompt = office.system_prompt()
        lineage = artifacts["enterprise_knowledge_graph_architecture"].machine_payload["historical_lineage"]
        eo_lineage = next(item for item in lineage if item["node_id"] == "EO-074")
        self.assertIn("Knowledge Graph Office", prompt.prompt_text)
        self.assertIn("enterprise knowledge graph", prompt.prompt_text)
        self.assertEqual(eo_lineage["prior_version_hashes"], ["HASH-EO-074"])
        self.assertTrue(eo_lineage["lineage_preserved"])


if __name__ == "__main__":
    unittest.main()
