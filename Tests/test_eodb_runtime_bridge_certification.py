from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import (
    BridgeCertificationState,
    BridgeFindingClass,
    CanonicalEnterpriseRuntime,
    RuntimeBridgeCertificationHarness,
    RuntimeBridgeRegistry,
    RuntimeProviderError,
    create_runtime_provider_for_tests,
    office_inventory,
    required_runtime_bridge_matrix,
    static_call_graph,
)


class RuntimeBridgeCertificationTests(unittest.TestCase):
    def test_required_bridge_matrix_registers_all_constitutional_bridges(self) -> None:
        registry = RuntimeBridgeRegistry()
        ids = {bridge.bridge_id for bridge in registry.all()}

        self.assertGreaterEqual(len(ids), 30)
        self.assertIn("BRIDGE-SCHED-MISSION-001", ids)
        self.assertIn("BRIDGE-TRADER-BROKER-001", ids)
        self.assertIn("BRIDGE-FILL-POSITION-001", ids)
        self.assertIn("BRIDGE-CLOSE-CPT-001", ids)
        self.assertIn("BRIDGE-PT-HISTORIAN-001", ids)
        self.assertIn("BRIDGE-ASSURANCE-COMMANDER-001", ids)
        self.assertTrue(all(bridge.payload_schema for bridge in registry.all()))
        self.assertFalse(any("LIVE" in bridge.truth_domains for bridge in registry.all()))

    def test_registry_rejects_duplicate_ids_missing_schema_and_live_modes(self) -> None:
        bridge = required_runtime_bridge_matrix()[0]
        registry = RuntimeBridgeRegistry((bridge,))

        with self.assertRaisesRegex(ValueError, "duplicate bridge id"):
            registry.register(bridge)
        with self.assertRaisesRegex(ValueError, "payload schema required"):
            RuntimeBridgeRegistry((replace(bridge, bridge_id="BRIDGE-BAD-SCHEMA", payload_schema=""),))
        with self.assertRaisesRegex(ValueError, "live bridge registration is disabled"):
            RuntimeBridgeRegistry((replace(bridge, bridge_id="BRIDGE-BAD-LIVE", runtime_modes=("live",)),))

    def test_duplicate_production_source_target_pairs_are_detected(self) -> None:
        bridge = required_runtime_bridge_matrix()[0]
        duplicate = replace(bridge, bridge_id="BRIDGE-SCHED-MISSION-DUPLICATE")
        registry = RuntimeBridgeRegistry((bridge, duplicate))

        pairs = registry.duplicate_production_pairs()

        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], "Scheduler")
        self.assertEqual(pairs[0][1], "Mission Planner")

    def test_office_inventory_covers_required_authorities_and_exposes_partial_coverage(self) -> None:
        offices = {office.office_name: office for office in office_inventory()}

        for name in ("Scheduler", "Mission Planner", "Workflow Orchestrator", "Trader", "Paper Broker", "Position Registry", "Performance Truth", "Historian", "Commander"):
            self.assertIn(name, offices)
        self.assertTrue(offices["Trader"].inbound_bridges)
        self.assertTrue(offices["Trader"].outbound_bridges)
        self.assertEqual(offices["Historian"].current_status, BridgeCertificationState.PARTIAL)

    def test_static_call_graph_finds_imports_and_calls_without_certifying_them(self) -> None:
        edges = static_call_graph(REPOSITORY_ROOT / "src" / "argos" / "control_panel")
        targets = {edge.target_symbol for edge in edges}

        self.assertTrue(edges)
        self.assertIn("get_server_runtime_provider", targets)
        self.assertIn("create_runtime", targets)
        self.assertTrue(any(edge.edge_type == "call" and "snapshot" in edge.target_symbol for edge in edges))

    def test_canonical_runtime_and_provider_are_one_bridge_authority_and_live_disabled(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        provider = create_runtime_provider_for_tests(runtime)

        self.assertIs(provider.runtime, runtime)
        self.assertFalse(provider.status().live_trading_enabled)
        with self.assertRaises(RuntimeProviderError):
            create_runtime_provider_for_tests(object())  # type: ignore[arg-type]

    def test_certification_report_is_honest_about_current_partial_bridge_state(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        provider = create_runtime_provider_for_tests(runtime)
        harness = RuntimeBridgeCertificationHarness()

        report = harness.certify(runtime=runtime, provider=provider, repo_root=REPOSITORY_ROOT, branch="main", commit_sha="test")

        self.assertEqual(report.verdict, "FAIL")
        self.assertGreaterEqual(report.required_bridge_count, 30)
        self.assertGreater(report.certified_production_count, 0)
        self.assertGreater(report.conditionally_production_count, 0)
        self.assertGreater(report.partial_count, 0)
        self.assertGreaterEqual(report.dynamic_trace_count, 3)
        self.assertFalse(report.live_trading_enabled)
        self.assertFalse(report.financial_mutation_authority)
        self.assertFalse(report.certifies_argos)
        self.assertFalse(report.certifies_continuous_paper_trading)
        self.assertTrue(any(finding.finding_class == BridgeFindingClass.PARTIAL_BRIDGE for finding in report.findings))

    def test_dynamic_reachability_uses_canonical_runtime_without_financial_mutation(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        before = runtime.read_only_snapshot()
        harness = RuntimeBridgeCertificationHarness()

        report = harness.certify(runtime=runtime, provider=create_runtime_provider_for_tests(runtime), repo_root=REPOSITORY_ROOT)
        after = runtime.read_only_snapshot()
        traced_ids = {trace.bridge_id for trace in harness.traces}

        self.assertIn("BRIDGE-SCHED-MISSION-001", traced_ids)
        self.assertIn("BRIDGE-MISSION-WORKFLOW-001", traced_ids)
        self.assertIn("BRIDGE-SI-SEEKER-001", traced_ids)
        self.assertEqual(after["paperBrokerOrderCount"], before["paperBrokerOrderCount"])
        self.assertEqual(after["positionCount"], before["positionCount"])
        self.assertGreaterEqual(report.dynamic_trace_count, 3)

    def test_commander_read_model_observes_but_cannot_certify_or_enable_live(self) -> None:
        harness = RuntimeBridgeCertificationHarness()
        report = harness.certify(repo_root=REPOSITORY_ROOT)
        model = harness.commander_read_model(report)

        self.assertEqual(model["engineeringOrder"], "EO-DB")
        self.assertEqual(model["verdict"], report.verdict)
        self.assertTrue(model["commanderControls"]["mayViewBridgeMatrix"])
        self.assertTrue(model["commanderControls"]["mayRequestRetest"])
        self.assertFalse(model["commanderControls"]["mayManuallyMarkBridgeCertified"])
        self.assertFalse(model["commanderControls"]["mayOverrideEODC"])
        self.assertFalse(model["commanderControls"]["mayOverrideEODD"])
        self.assertFalse(model["commanderControls"]["mayFabricateReachability"])
        self.assertFalse(model["commanderControls"]["mayEnableLiveTrading"])
        self.assertFalse(model["financialMutationAuthority"])

    def test_eodg_read_boundary_findings_are_integrated(self) -> None:
        harness = RuntimeBridgeCertificationHarness()
        report = harness.certify(repo_root=REPOSITORY_ROOT)

        self.assertTrue(any(finding.finding_class == BridgeFindingClass.READ_ONLY for finding in report.findings))
        self.assertFalse(any(finding.finding_class == BridgeFindingClass.LIVE_BOUNDARY for finding in report.findings))

    def test_evidence_bundle_writes_machine_readable_artifacts(self) -> None:
        harness = RuntimeBridgeCertificationHarness()
        report = harness.certify(repo_root=REPOSITORY_ROOT)

        with tempfile.TemporaryDirectory() as directory:
            paths = harness.write_evidence_bundle(directory, report)

            self.assertEqual(set(paths), {"bridgeGraph", "officeGraph", "bypassFindings", "callEdges", "certificationReport"})
            self.assertTrue(Path(paths["bridgeGraph"]).read_text(encoding="utf-8").startswith("["))
            self.assertIn("source_file", Path(paths["callEdges"]).read_text(encoding="utf-8"))
            self.assertIn("bridge_matrix_hash", Path(paths["certificationReport"]).read_text(encoding="utf-8"))

    def test_bridge_matrix_blocks_proof_simulation_test_replay_as_production(self) -> None:
        registry = RuntimeBridgeRegistry()
        replay_only = registry.get("BRIDGE-REPLAY-LAB-001")

        self.assertEqual(replay_only.certification_state, BridgeCertificationState.REPLAY_ONLY)
        self.assertFalse(any(bridge.certification_state == BridgeCertificationState.PROOF_ONLY for bridge in registry.all()))
        self.assertFalse(any(bridge.certification_state == BridgeCertificationState.SIMULATION_ONLY for bridge in registry.all()))
        self.assertFalse(any(bridge.certification_state == BridgeCertificationState.TEST_ONLY for bridge in registry.all()))


if __name__ == "__main__":
    unittest.main()
