import dataclasses
import sys
import unittest
from dataclasses import replace
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.canonical_enterprise_runtime import CanonicalEnterpriseRuntime, CanonicalRuntimeError  # noqa: E402
from argos.control_panel.constitutional_invariants import (  # noqa: E402
    BlockingLevel,
    ConstitutionalInvariantEngine,
    InvariantResultState,
    InvariantSeverity,
    LawVIIMonitor,
    ReadOnlyIntegrityGuard,
    TruthDomainInvariantGate,
    authoritative_write_site_registry,
    constitutional_authority_registry,
    constitutional_invariant_catalog,
)
from argos.control_panel.truth_domain import RuntimeMode, TruthClassification, make_paper_operational_truth_envelope  # noqa: E402


class EODAConstitutionalInvariantTests(unittest.TestCase):
    def test_catalog_authority_and_write_site_registries_are_inspectable(self) -> None:
        catalog = constitutional_invariant_catalog()
        authorities = constitutional_authority_registry()
        write_sites = authoritative_write_site_registry()

        self.assertGreaterEqual(len(catalog), 10)
        self.assertGreaterEqual(len(authorities), 25)
        self.assertGreaterEqual(len(write_sites), 10)
        self.assertTrue(all(item.schema_version == "EO-DA.1" for item in catalog))
        self.assertEqual(len({item.invariant_id for item in catalog}), len(catalog))
        self.assertIn("Paper Broker", {item.authority_name for item in authorities})
        self.assertIn("Performance Truth", {item.authority for item in write_sites})

    def test_startup_evaluator_passes_canonical_runtime_and_fails_duplicate_authority(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        engine = ConstitutionalInvariantEngine(REPOSITORY_ROOT)

        passed = engine.evaluate_startup(runtime)
        self.assertEqual("PASS", passed.verdict)
        self.assertEqual(0, passed.fail_count)
        self.assertFalse(passed.financial_mutation_authority)

        runtime.components.paper_broker = runtime.components.performance_truth  # type: ignore[assignment]
        failed = engine.evaluate_startup(runtime)
        self.assertEqual("FAIL", failed.verdict)
        self.assertTrue(any(result.invariant_id == "INV-AUTHORITY-001" and result.result == InvariantResultState.FAIL for result in failed.results))

    def test_canonical_runtime_startup_fails_closed_when_live_requested(self) -> None:
        runtime = CanonicalEnterpriseRuntime(live_trading_enabled=True)

        with self.assertRaises(CanonicalRuntimeError):
            runtime.start()

    def test_law_vii_monitor_detects_illegal_token_ownership(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        workflow = runtime.components.workflow_orchestrator.create_validate_queue_assign(
            name="EO-DA LAW VII fixture",
            stages=("Seeker",),
            runtime_budget=60,
            credit_budget=1.0,
            expected_output_schema=("mission_result",),
        )
        snapshot = runtime.components.workflow_orchestrator.snapshot()
        rows = [dict(item) for item in snapshot["workflows"]]
        rows[0]["token"] = dict(rows[0]["token"], current_owner="Runtime")
        bad_snapshot = dict(snapshot, workflows=tuple(rows), activeWorkflows=tuple(rows))

        result = LawVIIMonitor().evaluate(bad_snapshot)

        self.assertEqual(workflow.workflow_id, rows[0]["workflow_id"])
        self.assertEqual(InvariantResultState.FAIL, result.result)
        self.assertIn("OWNER_NOT_IN_WORKFLOW_STAGES", {item["code"] for item in result.observed_values["violations"]})

    def test_truth_domain_gate_accepts_valid_envelope_and_rejects_proof(self) -> None:
        gate = TruthDomainInvariantGate()
        valid = make_paper_operational_truth_envelope(
            originating_authority="DeterministicPaperBrokerage",
            originating_workflow_id="WF-EO-DA",
            workflow_token_id="TOKEN-EO-DA",
            mission_id="MISSION-EO-DA",
            source_event_id="PBE-EO-DA",
            idempotency_key="ORDER-EO-DA",
            timestamp_utc="2026-07-13T16:00:00Z",
            caller="PerformanceTruthEngine",
        )

        accepted = gate.validate(valid, target_authority="PerformanceTruthEngine", allowed_authorities={"DeterministicPaperBrokerage"})
        rejected = gate.validate(dict(valid.__dict__, truth_domain=RuntimeMode.PROOF.value, truth_classification=TruthClassification.PROOF_ONLY.value), target_authority="PerformanceTruthEngine", allowed_authorities={"DeterministicPaperBrokerage"})

        self.assertEqual(InvariantResultState.PASS, accepted.result)
        self.assertEqual(InvariantResultState.FAIL, rejected.result)
        self.assertIn("PROOF_MODE_NOT_ACTIONABLE", rejected.observed_values["codes"])

    def test_broker_position_monitor_detects_unfilled_position_lineage_and_duplicate_closed_truth(self) -> None:
        engine = ConstitutionalInvariantEngine(REPOSITORY_ROOT)
        performance_truth = {
            "orderLedger": (
                {"order_id": "ORD-REJECT", "status": "REJECTED", "filled_quantity": 1},
            ),
            "positionRegistry": {
                "allPositions": (
                    {"position_id": "POS-BAD", "quantity": 5, "fill_ids": (), "broker_order_ids": ("ORD-MISSING",)},
                )
            },
            "closedPositionTruth": (
                {"position_id": "POS-BAD", "closed_position_truth_id": "CPT-1"},
                {"position_id": "POS-BAD", "closed_position_truth_id": "CPT-2"},
            ),
        }

        broker_result, position_result = engine.broker_position_monitor.evaluate(performance_truth)

        self.assertEqual(InvariantResultState.FAIL, broker_result.result)
        self.assertEqual(InvariantResultState.FAIL, position_result.result)
        self.assertEqual(BlockingLevel.OPERATION, broker_result.blocking_status)
        self.assertIn("DUPLICATE_CLOSED_POSITION_TRUTH", {item["code"] for item in position_result.observed_values["violations"]})

    def test_read_only_guard_detects_digest_mutation_without_creating_truth(self) -> None:
        guard = ReadOnlyIntegrityGuard()
        state = {"digest": "A"}

        def digest() -> str:
            return state["digest"]

        def mutating_read() -> dict[str, str]:
            state["digest"] = "B"
            return {"ok": "no"}

        value, result = guard.evaluate(digest, mutating_read, entity="bad dashboard read")

        self.assertEqual({"ok": "no"}, value)
        self.assertEqual(InvariantResultState.FAIL, result.result)
        self.assertEqual("READ_ONLY_MUTATION_DETECTED", result.violation_code)

    def test_static_architecture_and_commander_health_model_are_read_only(self) -> None:
        engine = ConstitutionalInvariantEngine(REPOSITORY_ROOT)
        static = engine.evaluate_static_architecture()
        health = engine.commander_health_read_model(static)

        self.assertEqual("PASS", static.verdict)
        self.assertFalse(static.live_trading_enabled)
        self.assertFalse(static.financial_mutation_authority)
        self.assertEqual("Constitutional Invariant Engine", health["engineName"])
        self.assertFalse(health["commanderLimitations"]["mayCreateFill"])
        self.assertFalse(health["financialMutationAuthority"])

    def test_invariant_results_are_serializable_assurance_evidence(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        sweep = ConstitutionalInvariantEngine(REPOSITORY_ROOT).evaluate_startup(runtime)
        payload = dataclasses.asdict(sweep)

        self.assertEqual("EO-DA.1", payload["engine_version"])
        self.assertIn("results", payload)
        self.assertFalse(payload["financial_mutation_authority"])


if __name__ == "__main__":
    unittest.main()
