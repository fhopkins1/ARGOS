from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.persistence import (  # noqa: E402
    BackupService,
    InMemoryPersistenceRepository,
    Migration,
    MigrationManager,
    ObjectType,
    PersistenceError,
    PersistenceReplayService,
    PersistenceSearchService,
    canonical_schemas,
)


def repository() -> InMemoryPersistenceRepository:
    return InMemoryPersistenceRepository(canonical_schemas())


class PersistenceFrameworkTests(unittest.TestCase):
    def test_all_required_canonical_schemas_exist(self) -> None:
        object_types = {schema.object_type for schema in canonical_schemas()}

        self.assertEqual(
            object_types,
            {
                ObjectType.CASE_FILE,
                ObjectType.OPERATIONAL_DOCUMENT,
                ObjectType.AUDIT_EVENT,
                ObjectType.CONFIGURATION_SNAPSHOT,
                ObjectType.PROMPT_SNAPSHOT,
                ObjectType.MODEL_SNAPSHOT,
                ObjectType.STAFF_REGISTRY,
                ObjectType.DEPARTMENT_REGISTRY,
            },
        )

    def test_persistence_appends_versions_without_overwrite(self) -> None:
        repo = repository()

        first = repo.persist(
            ObjectType.CASE_FILE,
            "CF-001",
            {"case_file_id": "CF-001", "trade_cycle_id": "TC-001", "status": "opened"},
        )
        second = repo.persist(
            ObjectType.CASE_FILE,
            "CF-001",
            {"case_file_id": "CF-001", "trade_cycle_id": "TC-001", "status": "reviewed"},
        )

        history = repo.history(ObjectType.CASE_FILE, "CF-001")
        self.assertEqual([record.version for record in history], [1, 2])
        self.assertEqual(first.payload["status"], "opened")
        self.assertEqual(second.payload["status"], "reviewed")
        self.assertEqual(second.previous_record_hash, first.record_hash)

    def test_missing_required_schema_fields_are_rejected(self) -> None:
        repo = repository()

        with self.assertRaises(PersistenceError):
            repo.persist(ObjectType.CASE_FILE, "CF-001", {"case_file_id": "CF-001"})

    def test_migration_manager_applies_registered_migration(self) -> None:
        manager = MigrationManager()
        manager.register(
            Migration(
                migration_id="MIG-001",
                object_type=ObjectType.CASE_FILE,
                from_version="1.0.0",
                to_version="1.1.0",
                transform=lambda payload: {**payload, "migrated": True},
            )
        )

        migrated = manager.migrate(
            ObjectType.CASE_FILE,
            {"case_file_id": "CF-001", "trade_cycle_id": "TC-001"},
            "1.0.0",
            "1.1.0",
        )

        self.assertTrue(migrated["migrated"])

    def test_search_services_find_records_by_identifiers(self) -> None:
        repo = repository()
        repo.persist(
            ObjectType.OPERATIONAL_DOCUMENT,
            "DOC-001",
            {
                "contract_id": "DOC-001",
                "case_file_id": "CF-001",
                "trade_cycle_id": "TC-001",
                "produced_by_staff_id": "STF-001",
            },
        )
        search = PersistenceSearchService(repo)

        self.assertEqual(len(search.search_by_case_file_id("CF-001")), 1)
        self.assertEqual(len(search.search_by_trade_cycle_id("TC-001")), 1)
        self.assertEqual(len(search.search_by_staff_id("STF-001")), 1)
        self.assertEqual(len(search.search_by_document_id("DOC-001")), 1)

    def test_replay_reconstructs_case_file_from_persisted_records(self) -> None:
        repo = repository()
        repo.persist(
            ObjectType.CASE_FILE,
            "CF-001",
            {"case_file_id": "CF-001", "trade_cycle_id": "TC-001"},
        )
        repo.persist(
            ObjectType.OPERATIONAL_DOCUMENT,
            "DOC-001",
            {"contract_id": "DOC-001", "case_file_id": "CF-001", "trade_cycle_id": "TC-001"},
        )
        repo.persist(
            ObjectType.AUDIT_EVENT,
            "AE-000001",
            {"event_id": "AE-000001", "case_file_id": "CF-001", "document_id": "DOC-001"},
        )

        replay = PersistenceReplayService(repo).replay_case_file("CF-001")

        self.assertEqual(replay.case_file_id, "CF-001")
        self.assertEqual(len(replay.records), 3)
        self.assertEqual(replay.document_ids, ("DOC-001",))
        self.assertEqual(replay.audit_event_ids, ("AE-000001",))

    def test_backup_and_restore_preserve_history_and_integrity(self) -> None:
        source = repository()
        source.persist(
            ObjectType.CASE_FILE,
            "CF-001",
            {"case_file_id": "CF-001", "trade_cycle_id": "TC-001", "status": "opened"},
        )
        source.persist(
            ObjectType.CASE_FILE,
            "CF-001",
            {"case_file_id": "CF-001", "trade_cycle_id": "TC-001", "status": "closed"},
        )
        backup = BackupService(source).create_backup()

        target = repository()
        BackupService(target).restore(backup)

        self.assertTrue(target.validate_integrity())
        self.assertEqual(len(target.history(ObjectType.CASE_FILE, "CF-001")), 2)
        self.assertEqual(
            target.latest(ObjectType.CASE_FILE, "CF-001").payload["status"],
            "closed",
        )

    def test_backup_restore_rejects_tampered_backup(self) -> None:
        source = repository()
        source.persist(
            ObjectType.CASE_FILE,
            "CF-001",
            {"case_file_id": "CF-001", "trade_cycle_id": "TC-001"},
        )
        backup = BackupService(source).create_backup()
        tampered = type(backup)(records=backup.records, backup_hash="0" * 64)

        with self.assertRaises(ValueError):
            BackupService(repository()).restore(tampered)

    def test_integrity_validation_detects_broken_version_history(self) -> None:
        repo = repository()
        record = repo.persist(
            ObjectType.CASE_FILE,
            "CF-001",
            {"case_file_id": "CF-001", "trade_cycle_id": "TC-001"},
        )
        broken = type(record)(
            object_type=record.object_type,
            object_id=record.object_id,
            version=3,
            schema_version=record.schema_version,
            payload=dict(record.payload),
            created_timestamp_utc=record.created_timestamp_utc,
            previous_record_hash=record.previous_record_hash,
        )

        with self.assertRaises(PersistenceError):
            repo.replace_records((broken,))


if __name__ == "__main__":
    unittest.main()

