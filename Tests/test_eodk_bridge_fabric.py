from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import (  # noqa: E402
    BridgeRejectionCode,
    BridgeResultStatus,
    BridgeTransferClass,
    CanonicalBridgeDefinition,
    CanonicalBridgeExecutor,
    CanonicalBridgeRegistry,
    CanonicalEnterpriseRuntime,
    default_bridge_definitions,
    make_bridge_request,
)


def payload() -> dict[str, str]:
    return {"artifact": "decision", "id": "A-1"}


class EODKBridgeFabricTests(unittest.TestCase):
    def test_registry_rejects_duplicate_bridge_ids(self) -> None:
        definition = default_bridge_definitions()[0]
        with self.assertRaises(ValueError):
            CanonicalBridgeRegistry((definition, definition))

    def test_ownership_transfer_requires_current_owner_and_token(self) -> None:
        executor = CanonicalBridgeExecutor(runtime_instance_id="R1")
        executor.ownership.establish("WF-1", "Seeker", "TOK-1")
        request = make_bridge_request(bridge_id="BRIDGE-SEEKER-ANALYST-001", runtime_instance_id="R1", workflow_id="WF-1", source="Seeker", destination="Analyst", artifact_id="A-1", payload=payload(), current_owner="Seeker", next_owner="Analyst", token_id="TOK-1")
        result = executor.execute(request)
        self.assertEqual(result.status, BridgeResultStatus.ACCEPTED)
        self.assertEqual(result.resulting_owner, "Analyst")
        self.assertIn("Seeker", executor.ownership.released("WF-1"))
        bad = make_bridge_request(bridge_id="BRIDGE-ANALYST-RISK-001", runtime_instance_id="R1", workflow_id="WF-1", source="Analyst", destination="Risk", artifact_id="A-2", payload=payload(), current_owner="Seeker", next_owner="Risk", token_id="TOK-1")
        rejected = executor.execute(bad)
        self.assertEqual(rejected.rejection_code, BridgeRejectionCode.BRIDGE_INVALID_OWNER)

    def test_information_delivery_does_not_transfer_owner(self) -> None:
        executor = CanonicalBridgeExecutor(runtime_instance_id="R1")
        executor.ownership.establish("WF-2", "Trader", "TOK-2")
        request = make_bridge_request(bridge_id="BRIDGE-BROKER-FILL-001", runtime_instance_id="R1", workflow_id="WF-2", source="Paper Broker", destination="Fill Ledger", artifact_id="FILL-1", payload=payload(), current_owner="Trader", token_id="TOK-2")
        result = executor.execute(request)
        self.assertEqual(result.status, BridgeResultStatus.ACCEPTED)
        self.assertEqual(executor.ownership.owner("WF-2"), "Trader")

    def test_artifact_hash_mismatch_rejects_execution(self) -> None:
        executor = CanonicalBridgeExecutor(runtime_instance_id="R1")
        request = make_bridge_request(bridge_id="BRIDGE-BROKER-FILL-001", runtime_instance_id="R1", workflow_id="WF-3", source="Paper Broker", destination="Fill Ledger", artifact_id="FILL-1", payload=payload(), current_owner="Trader")
        tampered = request.__class__(**{**request.__dict__, "artifact_hash": "bad"})
        result = executor.execute(tampered)
        self.assertEqual(result.rejection_code, BridgeRejectionCode.BRIDGE_ARTIFACT_HASH_MISMATCH)

    def test_replay_only_bridge_rejects_paper_domain(self) -> None:
        executor = CanonicalBridgeExecutor(runtime_instance_id="R1")
        request = make_bridge_request(bridge_id="BRIDGE-REPLAY-LAB-001", runtime_instance_id="R1", workflow_id="WF-4", source="Replay", destination="Decision Laboratory", artifact_id="R-1", payload=payload(), current_owner="Replay", proof_domain="PAPER")
        result = executor.execute(request)
        self.assertEqual(result.rejection_code, BridgeRejectionCode.BRIDGE_PROOF_DOMAIN_REJECTED)

    def test_idempotent_replay_returns_duplicate_success(self) -> None:
        executor = CanonicalBridgeExecutor(runtime_instance_id="R1")
        request = make_bridge_request(bridge_id="BRIDGE-BROKER-FILL-001", runtime_instance_id="R1", workflow_id="WF-5", source="Paper Broker", destination="Fill Ledger", artifact_id="FILL-1", payload=payload(), current_owner="Trader")
        self.assertEqual(executor.execute(request).status, BridgeResultStatus.ACCEPTED)
        self.assertEqual(executor.execute(request).status, BridgeResultStatus.DUPLICATE_IDEMPOTENT_SUCCESS)

    def test_disabled_bridge_rejects_execution(self) -> None:
        definition = default_bridge_definitions()[0]
        disabled = CanonicalBridgeDefinition(**{**definition.__dict__, "enabled": False})
        executor = CanonicalBridgeExecutor(runtime_instance_id="R1", registry=CanonicalBridgeRegistry((disabled,)))
        request = make_bridge_request(bridge_id=definition.bridge_id, runtime_instance_id="R1", workflow_id="WF-6", source=definition.source_component, destination=definition.destination_component, artifact_id="A-1", payload=payload(), current_owner=definition.source_component)
        self.assertEqual(executor.execute(request).rejection_code, BridgeRejectionCode.BRIDGE_DISABLED)

    def test_canonical_runtime_emits_bridge_fabric_trace(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        runtime.start()
        runtime.admit_scheduled_obligation("post_open_discovery")
        snapshot = runtime.read_only_snapshot()
        self.assertGreaterEqual(snapshot["bridgeFabric"]["dynamicTraceCount"], 1)


if __name__ == "__main__":
    unittest.main()
