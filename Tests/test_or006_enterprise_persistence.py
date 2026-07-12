from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import (  # noqa: E402
    CanonicalEnterpriseRuntime,
    DurableEnterprisePersistenceStore,
    EnterprisePersistenceError,
    RecoveryMode,
    TransactionWrite,
    enterprise_persistence_inventory,
)
from argos.foundation.persistence.records import ObjectType  # noqa: E402


class OR006EnterprisePersistenceTests(unittest.TestCase):
    def test_runtime_truth_survives_planned_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "enterprise-persistence.json"
            runtime = CanonicalEnterpriseRuntime()
            runtime.start()
            admission = runtime.admit_scheduled_obligation("pre_market_readiness", now="2026-07-13T08:15:00Z")
            store = DurableEnterprisePersistenceStore(path)

            store.persist_runtime(runtime)
            recovered_store = DurableEnterprisePersistenceStore(path)
            recovered, audit = recovered_store.recover_runtime(mode=RecoveryMode.PLANNED_RESTART)

            self.assertTrue(audit.paper_operation_allowed)
            self.assertIn("missions", audit.restored_entities)
            self.assertIn("workflows", audit.restored_entities)
            self.assertEqual(recovered.components.workflow_orchestrator.workflow(admission.workflow_id).workflow_id, admission.workflow_id)
            self.assertEqual(recovered.components.scheduler.snapshot()["missionRecords"][0]["mission_id"], admission.scheduler_mission_id)

    def test_duplicate_identity_is_rejected_for_new_authoritative_record(self) -> None:
        store = DurableEnterprisePersistenceStore()
        store.persist_authoritative(ObjectType.ENTERPRISE_WORKFLOW_STATE, "WF-1", {"workflow_id": "WF-1"}, require_new_identity=True)

        with self.assertRaises(EnterprisePersistenceError):
            store.persist_authoritative(ObjectType.ENTERPRISE_WORKFLOW_STATE, "WF-1", {"workflow_id": "WF-1"}, require_new_identity=True)

    def test_transaction_boundary_records_all_writes(self) -> None:
        store = DurableEnterprisePersistenceStore()
        store.commit_transaction(
            "TX-1",
            (
                # Minimal payloads are wrapped by the OR-006 envelope.
                TransactionWrite(ObjectType.ENTERPRISE_MISSION_STATE, "M-1", {"mission_id": "M-1"}),
                TransactionWrite(ObjectType.ENTERPRISE_WORKFLOW_STATE, "W-1", {"workflow_id": "W-1"}),
            ),
        )

        transaction = store.latest_payload(ObjectType.ENTERPRISE_TRANSACTION, "TX-1")
        self.assertEqual(transaction["boundary_id"], "TX-1")
        self.assertEqual(len(transaction["writes"]), 2)

    def test_checkpoint_does_not_replace_authoritative_truth(self) -> None:
        store = DurableEnterprisePersistenceStore()
        store.checkpoint("CHK-1", {"runtime_mode": "paper_active", "positionCount": 99})

        self.assertEqual(store.latest_payload(ObjectType.ENTERPRISE_POSITION_STATE, "position-registry"), {})
        checkpoint = store.latest_payload(ObjectType.ENTERPRISE_RUNTIME_CHECKPOINT, "CHK-1")
        self.assertEqual(checkpoint["checkpoint_authority"], "continuity_only_not_financial_truth")

    def test_persistence_failure_fails_closed(self) -> None:
        store = DurableEnterprisePersistenceStore(fail_writes=True)

        with self.assertRaises(EnterprisePersistenceError):
            store.persist_authoritative(ObjectType.ENTERPRISE_MISSION_STATE, "M-FAIL", {"mission_id": "M-FAIL"})

        self.assertEqual(store.diagnostics()[0].code, "PERSISTENCE_BACKEND_UNAVAILABLE")

    def test_corrupted_backup_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "enterprise-persistence.json"
            runtime = CanonicalEnterpriseRuntime()
            runtime.start()
            store = DurableEnterprisePersistenceStore(path)
            store.persist_runtime(runtime)
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("canonical-runtime", "canonical-runtime-corrupt", 1), encoding="utf-8")

            with self.assertRaises(ValueError):
                DurableEnterprisePersistenceStore(path)

    def test_recovery_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "enterprise-persistence.json"
            runtime = CanonicalEnterpriseRuntime()
            runtime.start()
            runtime.admit_scheduled_obligation("pre_market_readiness", now="2026-07-13T08:15:00Z")
            DurableEnterprisePersistenceStore(path).persist_runtime(runtime)

            recovered_one, _ = DurableEnterprisePersistenceStore(path).recover_runtime(mode=RecoveryMode.CRASH_RECOVERY)
            recovered_two, _ = DurableEnterprisePersistenceStore(path).recover_runtime(mode=RecoveryMode.CRASH_RECOVERY)

            self.assertEqual(recovered_one.read_only_snapshot()["workflowCounts"]["workflowCount"], recovered_two.read_only_snapshot()["workflowCounts"]["workflowCount"])
            self.assertEqual(recovered_one.read_only_snapshot()["missionAdmissionCount"], recovered_two.read_only_snapshot()["missionAdmissionCount"])

    def test_inventory_classifies_authoritative_components(self) -> None:
        inventory = enterprise_persistence_inventory()
        owners = {item.authoritative_owner for item in inventory}

        self.assertIn("EnterpriseWorkflowOrchestrator", owners)
        self.assertIn("DeterministicPaperBrokerage", owners)
        self.assertIn("PositionRegistry", owners)


if __name__ == "__main__":
    unittest.main()
