from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.persistence import (  # noqa: E402
    InMemoryPersistenceRepository,
    ObjectType,
    canonical_schemas,
)
from argos.foundation.prompts import (  # noqa: E402
    DependencyGraph,
    DependencyNode,
    DependencyNodeType,
    PromptPassport,
    PromptRepository,
    PromptRepositoryError,
    PromptSnapshotService,
    SpecificationRecord,
    SpecificationRepository,
    SpecificationType,
)


def passport(prompt_id: str = "PROMPT-001") -> PromptPassport:
    return PromptPassport(
        prompt_id=prompt_id,
        title="Analyst Review Prompt",
        owner_group_id="DEP-004",
        author_staff_id="STF-001",
        purpose="Support deterministic analysis review.",
        allowed_environments=("development", "paper_trading"),
        input_contract_types=("BASE_CONTRACT",),
        output_contract_types=("ANALYSIS_NOTE",),
        dependencies=("PB-006", "EO-008"),
        safety_notes="No trading authority.",
    )


class PromptSpecificationRepositoryTests(unittest.TestCase):
    def test_prompt_repository_versions_and_history_are_append_only(self) -> None:
        repository = PromptRepository()
        prompt_passport = passport()

        first = repository.register(prompt_passport, "1.0.0", "Review evidence.")
        second = repository.register(prompt_passport, "1.1.0", "Review evidence with citations.")

        history = repository.history("PROMPT-001")
        self.assertEqual([record.version for record in history], ["1.0.0", "1.1.0"])
        self.assertEqual(repository.latest("PROMPT-001"), second)
        self.assertNotEqual(first.revision_hash, second.revision_hash)

    def test_prompt_repository_rejects_duplicate_revision(self) -> None:
        repository = PromptRepository()
        repository.register(passport(), "1.0.0", "Review evidence.")

        with self.assertRaises(PromptRepositoryError):
            repository.register(passport(), "1.0.0", "Overwrite attempt.")

    def test_prompt_passport_validation_rejects_bad_metadata(self) -> None:
        with self.assertRaises(PromptRepositoryError):
            PromptPassport(
                prompt_id="DOC-001",
                title="Bad prompt",
                owner_group_id="DEP-004",
                author_staff_id="STF-001",
                purpose="Invalid prompt ID.",
                allowed_environments=("development",),
                input_contract_types=(),
                output_contract_types=(),
                dependencies=(),
                safety_notes="",
            )

    def test_prompt_search_finds_body_and_passport_text(self) -> None:
        repository = PromptRepository()
        repository.register(passport(), "1.0.0", "Review evidence.")

        self.assertEqual(len(repository.search("evidence")), 1)
        self.assertEqual(len(repository.search("Analyst")), 1)

    def test_prompt_snapshot_is_linked_to_case_file(self) -> None:
        repository = PromptRepository()
        record = repository.register(passport(), "1.0.0", "Review evidence.")
        snapshot = PromptSnapshotService(repository).snapshot("PROMPT-001", "CF-001", "TC-001")

        self.assertEqual(snapshot.case_file_id, "CF-001")
        self.assertEqual(snapshot.trade_cycle_id, "TC-001")
        self.assertEqual(snapshot.prompt_id, "PROMPT-001")
        self.assertEqual(snapshot.prompt_version, "1.0.0")
        self.assertEqual(snapshot.revision_hash, record.revision_hash)
        self.assertEqual(len(snapshot.snapshot_hash), 64)

    def test_prompt_snapshot_service_rejects_unregistered_prompt(self) -> None:
        with self.assertRaises(PromptRepositoryError):
            PromptSnapshotService(PromptRepository()).snapshot("PROMPT-999", "CF-001", "TC-001")

    def test_specification_repositories_store_supported_spec_types(self) -> None:
        repository = SpecificationRepository(SpecificationType.INTERFACE)
        record = SpecificationRecord(
            specification_id="IF-001",
            specification_type=SpecificationType.INTERFACE,
            title="Courier Interface",
            version="1.0.0",
            body="Defines courier handoff.",
            dependencies=("EO-004",),
        )

        repository.register(record)

        self.assertEqual(repository.latest("IF-001"), record)
        self.assertEqual(repository.search("courier"), (record,))

    def test_specification_repository_rejects_wrong_type(self) -> None:
        repository = SpecificationRepository(SpecificationType.TEST)
        record = SpecificationRecord(
            specification_id="IF-001",
            specification_type=SpecificationType.INTERFACE,
            title="Wrong repository",
            version="1.0.0",
            body="Should not register.",
        )

        with self.assertRaises(ValueError):
            repository.register(record)

    def test_dependency_graph_links_and_searches_artifacts(self) -> None:
        graph = DependencyGraph()
        graph.add_node(DependencyNode("PB-006", DependencyNodeType.PROJECT_BIBLE, "Identifier Doctrine"))
        graph.add_node(DependencyNode("EO-008", DependencyNodeType.ENGINEERING_ORDER, "Prompt Repository"))
        graph.add_node(DependencyNode("PROMPT-001", DependencyNodeType.PROMPT, "Analyst Review Prompt"))
        graph.add_node(DependencyNode("CF-001", DependencyNodeType.CASE_FILE, "Case File"))

        graph.add_dependency("EO-008", "PB-006")
        graph.add_dependency("PROMPT-001", "EO-008")
        graph.add_dependency("CF-001", "PROMPT-001")

        self.assertEqual(graph.dependencies_for("PROMPT-001"), ("EO-008",))
        self.assertEqual(graph.dependents_of("PROMPT-001"), ("CF-001",))
        self.assertEqual(graph.transitive_dependencies_for("CF-001"), ("EO-008", "PB-006", "PROMPT-001"))
        self.assertEqual([node.node_id for node in graph.search("prompt")], ["EO-008", "PROMPT-001"])

    def test_prompt_snapshot_can_be_persisted_as_canonical_object(self) -> None:
        prompt_repository = PromptRepository()
        prompt_repository.register(passport(), "1.0.0", "Review evidence.")
        snapshot = PromptSnapshotService(prompt_repository).snapshot("PROMPT-001", "CF-001", "TC-001")
        persistence = InMemoryPersistenceRepository(canonical_schemas())

        record = persistence.persist(
            ObjectType.PROMPT_SNAPSHOT,
            snapshot.prompt_snapshot_id,
            {
                "prompt_snapshot_id": snapshot.prompt_snapshot_id,
                "case_file_id": snapshot.case_file_id,
                "prompt_id": snapshot.prompt_id,
                "prompt_version": snapshot.prompt_version,
                "snapshot_hash": snapshot.snapshot_hash,
            },
        )

        self.assertEqual(record.version, 1)
        self.assertEqual(record.object_id, "PS-000001")


if __name__ == "__main__":
    unittest.main()

