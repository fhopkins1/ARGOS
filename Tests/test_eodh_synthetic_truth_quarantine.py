from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import (  # noqa: E402
    FallbackPolicy,
    PerformanceTruthEngine,
    PositionRegistry,
    QuarantineController,
    SyntheticFindingStatus,
    SyntheticReachability,
    SyntheticSeverity,
    SyntheticTruthEradicationEngine,
    SyntheticTruthRegistry,
    UnknownState,
    baseline_synthetic_truth_findings,
    degraded_record,
    load_eodb_reachability,
    quarantine_namespaces,
    scan_synthetic_candidates,
    source_to_sink_analysis,
    unavailable_state,
)
from argos.control_panel.truth_domain import make_paper_operational_truth_envelope  # noqa: E402


def decision() -> dict[str, object]:
    provenance = {
        "asset_identifier": "AAPL",
        "asset_class": "equity",
        "direction": "buy",
        "thesis": "Authorized paper test",
        "evidence": "Authorized office judgment",
        "market_context": "paper quote",
        "entry_conditions": "broker executable",
        "price_source": "broker quote",
        "quantity": "1",
        "position_sizing_basis": "cash",
        "confidence": "0.7",
        "time_horizon": "day",
        "risk_factors": "documented",
        "stop_conditions": "documented",
        "exit_conditions": "documented",
        "expected_return": "0.01",
        "risk_approval": "Authorized office judgment",
        "trader_authorization": "Authorized office judgment",
    }
    return {
        "decisionObjectId": "DO-EO-DH",
        "office": "Trader",
        "sourceSystem": "Trader",
        "executionMode": "PAPER",
        "truthClassification": "PAPER_OPERATIONAL",
        "certificationStatus": "PAPER_OPERATIONAL_CERTIFIED",
        "materialFieldProvenance": provenance,
    }


def broker_order_without_fills() -> dict[str, object]:
    return {
        "order_id": "ORD-EO-DH",
        "ticket": {
            "workflow_id": "WF-EO-DH",
            "mission_id": "MIS-EO-DH",
            "decision_object_id": "DO-EO-DH",
            "workflow_token": "TOK-EO-DH",
            "trader_identity": "Trader",
            "account_id": "ACCT-PAPER-001",
            "symbol": "AAPL",
            "asset_type": "equity",
            "side": "buy",
            "quantity": 1.0,
            "order_type": "market",
            "time_in_force": "day",
            "strategy_id": "STRAT-EO-DH",
            "decision_object": decision(),
        },
        "market_state": {"bid": 100.0, "ask": 100.1, "last": 100.05, "volume": 10000.0, "session": "OPEN"},
        "status": "FILLED",
        "filled_quantity": 1.0,
        "average_fill_price": 100.1,
        "remaining_quantity": 0.0,
        "fills": (),
    }


def envelope() -> dict[str, object]:
    return make_paper_operational_truth_envelope(
        originating_authority="DeterministicPaperBrokerage",
        originating_workflow_id="WF-EO-DH",
        workflow_token_id="TOK-EO-DH",
        mission_id="MIS-EO-DH",
        source_event_id="EVT-EO-DH",
        idempotency_key="ORD-EO-DH",
        timestamp_utc="2026-07-18T00:00:00Z",
        caller="PerformanceTruthEngine",
    ).__dict__


class SyntheticTruthQuarantineTests(unittest.TestCase):
    def test_registry_loads_preserves_remediation_and_rejects_duplicates(self) -> None:
        findings = baseline_synthetic_truth_findings()
        registry = SyntheticTruthRegistry(findings)

        self.assertGreaterEqual(len(registry.all()), 10)
        self.assertEqual(registry.get("SYN-POSITION-001").status, SyntheticFindingStatus.REMEDIATED)
        with self.assertRaisesRegex(ValueError, "duplicate synthetic finding id"):
            registry.register(registry.get("SYN-POSITION-001"))

    def test_unknown_major_production_reachability_must_fail_closed_before_registration(self) -> None:
        finding = registry_finding = baseline_synthetic_truth_findings()[0]
        unknown = replace(
            registry_finding,
            finding_id="SYN-UNKNOWN-BLOCK",
            production_paper_reachability=SyntheticReachability.UNKNOWN_REACHABILITY,
            severity=SyntheticSeverity.MAJOR,
        )

        with self.assertRaisesRegex(ValueError, "unknown production reachability"):
            SyntheticTruthRegistry((finding, unknown))

    def test_quarantine_rejects_test_proof_simulation_replay_and_display_artifacts(self) -> None:
        controller = QuarantineController()

        for domain in ("TEST", "PROOF", "SIMULATION", "REPLAY", "DISPLAY"):
            with self.assertRaisesRegex(ValueError, "QUARANTINED"):
                controller.assert_not_paper_authoritative({"executionMode": domain, "sourceSystem": f"{domain.lower()}_fixture"}, target_sink="PerformanceTruthEngine")

    def test_fallback_policy_blocks_authoritative_zero_and_allows_display_label(self) -> None:
        policy = FallbackPolicy()
        blocked = policy.evaluate("price", 0.0, consumer="Trader", truth_domain="PAPER")
        display = policy.evaluate("label", "N/A", consumer="Dashboard", truth_domain="PAPER")

        self.assertEqual(blocked.state, UnknownState.BLOCKED)
        self.assertFalse(blocked.may_default_to_zero)
        self.assertFalse(blocked.may_satisfy_authoritative_requirement)
        self.assertEqual(display.state, UnknownState.NOT_APPLICABLE)
        self.assertTrue(display.may_default_to_empty)

    def test_degraded_and_unavailable_models_do_not_satisfy_authoritative_requirements(self) -> None:
        degraded = degraded_record("Analyst", missing_evidence=("valuation",), available_evidence=("source-id",))
        unavailable = unavailable_state("market quote", "provider unavailable")

        self.assertFalse(degraded.authoritative)
        self.assertIn("Trader", degraded.prohibited_consumers)
        self.assertEqual(unavailable.state, UnknownState.UNAVAILABLE)
        self.assertFalse(unavailable.may_default_to_zero)
        self.assertFalse(unavailable.may_satisfy_authoritative_requirement)

    def test_position_registry_rejects_positive_fill_quantity_without_fill_id(self) -> None:
        registry = PositionRegistry()

        with self.assertRaisesRegex(ValueError, "authoritative fill id required"):
            registry.create_from_execution(
                {
                    "side": "BUY",
                    "symbol": "AAPL",
                    "asset_type": "equity",
                    "filled_quantity": 1.0,
                    "average_fill_price": 100.0,
                    "order_id": "ORD-MISSING-FILL",
                    "workflow_id": "WF",
                    "token_id": "TOK",
                },
                decision={"riskScore": 0.2, "confidence": 0.7},
            )

    def test_performance_truth_rejects_filled_broker_order_without_fill_evidence(self) -> None:
        engine = PerformanceTruthEngine()

        result = engine.record_broker_authoritative_order(broker_order_without_fills(), truth_envelope=envelope())

        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "AUTHORITATIVE_FILL_EVIDENCE_REQUIRED")

    def test_static_scanner_and_source_to_sink_analysis_discover_candidates(self) -> None:
        candidates = scan_synthetic_candidates(REPOSITORY_ROOT / "src" / "argos" / "control_panel")
        paths = source_to_sink_analysis(REPOSITORY_ROOT, baseline_synthetic_truth_findings())

        self.assertTrue(candidates)
        self.assertTrue(any(candidate.term in {"fallback", "synthetic", "proof"} for candidate in candidates))
        self.assertTrue(paths)
        self.assertTrue(any(path.path_id == "PATH-SYN-MARKET-002" for path in paths))

    def test_eodb_reachability_artifact_is_consumed(self) -> None:
        eodb = load_eodb_reachability(REPOSITORY_ROOT)

        self.assertEqual(eodb["engine_version"], "EO-DB.1")
        self.assertGreaterEqual(eodb["required_bridge_count"], 30)

    def test_dynamic_attacks_are_rejected_without_authoritative_mutation(self) -> None:
        engine = SyntheticTruthEradicationEngine()

        attacks = engine.run_dynamic_attacks()

        self.assertGreaterEqual(len(attacks), 8)
        self.assertTrue(all(attack.rejected for attack in attacks))
        self.assertFalse(any(attack.authoritative_mutation for attack in attacks))

    def test_audit_report_is_honest_about_remaining_synthetic_truth_blockers(self) -> None:
        engine = SyntheticTruthEradicationEngine()

        report = engine.audit(repo_root=REPOSITORY_ROOT, branch="main", commit_sha="test")

        self.assertEqual(report.verdict, "FAIL")
        self.assertGreater(report.synthetic_candidates_discovered, 0)
        self.assertGreater(report.findings_remediated, 0)
        self.assertGreater(report.findings_quarantined, 0)
        self.assertGreater(report.major_findings_remaining, 0)
        self.assertEqual(report.dynamic_attack_total, report.dynamic_attack_rejected)
        self.assertFalse(report.live_trading_enabled)
        self.assertFalse(report.financial_or_analytical_decision_authority)
        self.assertFalse(report.certifies_argos)

    def test_commander_read_model_cannot_override_quarantine_or_enable_live(self) -> None:
        engine = SyntheticTruthEradicationEngine()
        report = engine.audit(repo_root=REPOSITORY_ROOT)
        model = engine.commander_read_model(report)

        self.assertEqual(model["engineeringOrder"], "EO-DH")
        self.assertFalse(model["commanderControls"]["mayReclassifyProhibitedTruthAsLegitimate"])
        self.assertFalse(model["commanderControls"]["mayApproveUnsupportedFallback"])
        self.assertFalse(model["commanderControls"]["mayEraseFindings"])
        self.assertFalse(model["commanderControls"]["mayPromoteDegradedRecords"])
        self.assertFalse(model["commanderControls"]["mayFabricateMissingEvidence"])
        self.assertFalse(model["commanderControls"]["mayEnableLiveTrading"])

    def test_evidence_bundle_writes_machine_readable_outputs(self) -> None:
        engine = SyntheticTruthEradicationEngine()
        report = engine.audit(repo_root=REPOSITORY_ROOT)

        with tempfile.TemporaryDirectory() as directory:
            paths = engine.write_evidence_bundle(directory, report)

            self.assertEqual(set(paths), {"registry", "sourceToSink", "unresolvedFindings", "dynamicAttacks", "auditReport", "staticCandidates"})
            self.assertIn("SYN-MARKET-002", Path(paths["registry"]).read_text(encoding="utf-8"))
            self.assertIn("PATH-SYN-MARKET-002", Path(paths["sourceToSink"]).read_text(encoding="utf-8"))
            self.assertIn("verdict", Path(paths["auditReport"]).read_text(encoding="utf-8"))

    def test_quarantine_namespaces_prohibit_promotion(self) -> None:
        namespaces = quarantine_namespaces()

        self.assertGreaterEqual(len(namespaces), 5)
        self.assertTrue(all(not namespace.promotion_allowed for namespace in namespaces))
        self.assertTrue(any(namespace.domain == "REPLAY" for namespace in namespaces))


if __name__ == "__main__":
    unittest.main()
