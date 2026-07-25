from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S02_OBJECT_LIFECYCLE"


class PositionRegistryRM001S02ObjectLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_s02_object_lifecycle.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_b02_001_objects_are_complete(self) -> None:
        objects = json.loads((EVIDENCE_ROOT / "B02-001_canonical_object_registry.json").read_text(encoding="utf-8"))
        conflicts = json.loads((EVIDENCE_ROOT / "B02-001_object_conflict_registry.json").read_text(encoding="utf-8"))
        expected = {
            "position_identity",
            "position_record",
            "position_state",
            "position_status",
            "position_lifecycle_state",
            "position_quantity",
            "open_quantity",
            "closed_quantity",
            "realized_quantity",
            "unrealized_quantity",
            "position_direction",
            "average_cost_basis",
            "entry_cost_basis",
            "cost_basis_history",
            "position_valuation_reference",
            "instrument_identity",
            "account_identity",
            "broker_position_identity",
            "broker_execution_reference",
            "fill_reference",
            "workflow_identity",
            "authorization_reference",
            "risk_reference",
            "monitoring_reference",
            "exit_reference",
            "closed_position_reference",
            "performance_reference",
            "reconciliation_case",
            "correction_record",
            "supersession_record",
            "historical_position_record",
            "archival_record",
        }
        self.assertEqual({item["canonical_object_name"] for item in objects}, expected)
        self.assertTrue(all(item["object_id"] for item in objects))
        self.assertTrue(all(item["constitutional_owner"] for item in objects))
        self.assertTrue(all(item["governing_authority"] == "POSITION-REGISTRY-RM-001-S02-B02-001" for item in objects))
        self.assertTrue(all(item["reconciliation_authority"] == "Position Registry" for item in objects))
        self.assertEqual(conflicts, [])

    def test_b02_001_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B02-001_canonical_object_registry.json",
            "B02-001_canonical_object_identity_registry.json",
            "B02-001_constitutional_object_authority_registry.json",
            "B02-001_constitutional_object_ownership_registry.json",
            "B02-001_constitutional_object_custody_registry.json",
            "B02-001_object_relationship_registry.json",
            "B02-001_object_dependency_registry.json",
            "B02-001_object_lifecycle_participation_registry.json",
            "B02-001_object_evidence_registry.json",
            "B02-001_object_invariant_registry.json",
            "B02-001_object_completeness_assessment.json",
            "B02-001_duplicate_object_registry.json",
            "B02-001_orphan_object_registry.json",
            "B02-001_unresolved_constitutional_object_findings_registry.json",
            "B02-001_canonical_object_constitution_report.json",
            "B02-001_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

        completeness = json.loads((EVIDENCE_ROOT / "B02-001_object_completeness_assessment.json").read_text(encoding="utf-8"))
        duplicates = json.loads((EVIDENCE_ROOT / "B02-001_duplicate_object_registry.json").read_text(encoding="utf-8"))
        orphans = json.loads((EVIDENCE_ROOT / "B02-001_orphan_object_registry.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B02-001_unresolved_constitutional_object_findings_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(completeness["complete"])
        self.assertEqual(duplicates, [])
        self.assertEqual(orphans, [])
        self.assertEqual(unresolved, [])

    def test_b02_001_invariants_and_dependencies_are_deterministic(self) -> None:
        dependencies = json.loads((EVIDENCE_ROOT / "B02-001_object_dependency_registry.json").read_text(encoding="utf-8"))
        invariants = json.loads((EVIDENCE_ROOT / "B02-001_object_invariant_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(dependencies)
        self.assertTrue(all(item["deterministic_direction"] for item in dependencies))
        self.assertTrue(all(item["invariant_violations"] == [] for item in invariants))
        self.assertTrue(all(item["ambiguous_invariants"] == [] for item in invariants))
        self.assertTrue(all(item["conflicting_invariants"] == [] for item in invariants))

    def test_b02_002_quantity_cost_and_temporal_rules_exist(self) -> None:
        quantity = json.loads((EVIDENCE_ROOT / "B02-002_quantity_doctrine_registry.json").read_text(encoding="utf-8"))
        cost = json.loads((EVIDENCE_ROOT / "B02-002_cost_basis_doctrine_registry.json").read_text(encoding="utf-8"))
        temporal = json.loads((EVIDENCE_ROOT / "B02-002_temporal_doctrine_registry.json").read_text(encoding="utf-8"))
        ambiguity = json.loads((EVIDENCE_ROOT / "B02-002_lifecycle_ambiguity_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(quantity)
        self.assertTrue(cost)
        self.assertTrue(temporal)
        self.assertEqual(ambiguity, [])

    def test_b02_002_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B02-002_lifecycle_constitution.json",
            "B02-002_lifecycle_transition_registry.json",
            "B02-002_lifecycle_authority_registry.json",
            "B02-002_lifecycle_invariant_registry.json",
            "B02-002_quantity_constitution.json",
            "B02-002_quantity_rule_registry.json",
            "B02-002_quantity_invariant_registry.json",
            "B02-002_cost_basis_constitution.json",
            "B02-002_cost_basis_rule_registry.json",
            "B02-002_cost_basis_invariant_registry.json",
            "B02-002_temporal_constitution.json",
            "B02-002_temporal_ordering_registry.json",
            "B02-002_temporal_authority_registry.json",
            "B02-002_behavioral_state_invariant_registry.json",
            "B02-002_constitutional_lifecycle_completeness_assessment.json",
            "B02-002_constitutional_quantity_completeness_assessment.json",
            "B02-002_constitutional_cost_basis_completeness_assessment.json",
            "B02-002_constitutional_temporal_completeness_assessment.json",
            "B02-002_unresolved_constitutional_findings_registry.json",
            "B02-002_lifecycle_quantity_cost_basis_and_temporal_constitutional_report.json",
            "B02-002_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

    def test_b02_002_semantic_constitutions_cover_required_behavior(self) -> None:
        lifecycle = json.loads((EVIDENCE_ROOT / "B02-002_lifecycle_constitution.json").read_text(encoding="utf-8"))
        quantity = json.loads((EVIDENCE_ROOT / "B02-002_quantity_rule_registry.json").read_text(encoding="utf-8"))
        cost = json.loads((EVIDENCE_ROOT / "B02-002_cost_basis_rule_registry.json").read_text(encoding="utf-8"))
        temporal = json.loads((EVIDENCE_ROOT / "B02-002_temporal_doctrine_registry.json").read_text(encoding="utf-8"))
        temporal_ordering = json.loads((EVIDENCE_ROOT / "B02-002_temporal_ordering_registry.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B02-002_unresolved_constitutional_findings_registry.json").read_text(encoding="utf-8"))

        states = {item["state"] for item in lifecycle["states"]}
        self.assertTrue({"pending", "open", "increasing", "decreasing", "partially_closed", "fully_closed", "correction_pending", "reconciliation_pending", "disputed", "superseded", "archived"}.issubset(states))
        self.assertTrue({"signed_quantity", "unsigned_quantity", "zero_quantity", "fractional_quantity", "overflow_quantity", "underflow_quantity"}.issubset({item["quantity_name"] for item in quantity}))
        self.assertTrue({"average_cost_basis", "entry_cost_basis", "realized_cost_basis", "unrealized_cost_basis", "weighted_average", "commission_adjustment", "fee_adjustment", "settlement_adjustment", "corporate_action_adjustment", "restated_cost_basis"}.issubset({item["field"] for item in cost}))
        self.assertTrue({"event_time", "effective_time", "broker_time", "exchange_time", "receipt_time", "processing_time", "persistence_time", "reconciliation_time", "correction_time", "archival_time", "terminal_time"}.issubset({item["timestamp_name"] for item in temporal}))
        self.assertEqual(temporal_ordering["identical_timestamp_disposition"], "requires sequence identifier or reconciliation disposition")
        self.assertEqual(unresolved, [])

    def test_b02_002_authorities_and_invariants_are_defined(self) -> None:
        lifecycle_authority = json.loads((EVIDENCE_ROOT / "B02-002_lifecycle_authority_registry.json").read_text(encoding="utf-8"))
        quantity_invariants = json.loads((EVIDENCE_ROOT / "B02-002_quantity_invariant_registry.json").read_text(encoding="utf-8"))
        cost_invariants = json.loads((EVIDENCE_ROOT / "B02-002_cost_basis_invariant_registry.json").read_text(encoding="utf-8"))
        temporal_authority = json.loads((EVIDENCE_ROOT / "B02-002_temporal_authority_registry.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "B02-002_completion_report.json").read_text(encoding="utf-8"))
        self.assertTrue(all(item["identity_preservation_required"] for item in lifecycle_authority))
        self.assertTrue(all(item["constitutional_definition_required"] for item in quantity_invariants))
        self.assertTrue(all(item["constitutional_definition_required"] for item in cost_invariants))
        self.assertTrue(all(item["implementation_inference_prohibited"] for item in temporal_authority))
        self.assertFalse(completion["implementation_evaluated"])
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["certification_activity_executed"])

    def test_b02_003_historical_integrity_prohibits_fabrication(self) -> None:
        replay = json.loads((EVIDENCE_ROOT / "B02-003_replay_constitution.json").read_text(encoding="utf-8"))
        supersession = json.loads((EVIDENCE_ROOT / "B02-003_supersession_constitution.json").read_text(encoding="utf-8"))
        self.assertTrue(replay["identity_preservation"])
        self.assertTrue(replay["fabrication_prohibited"])
        self.assertTrue(supersession["superseded_object_preserved"])

    def test_b02_003_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B02-003_correction_constitution.json",
            "B02-003_correction_authority_registry.json",
            "B02-003_correction_lineage_registry.json",
            "B02-003_replay_constitution.json",
            "B02-003_replay_ordering_registry.json",
            "B02-003_replay_authority_registry.json",
            "B02-003_recovery_constitution.json",
            "B02-003_recovery_authority_registry.json",
            "B02-003_recovery_scenario_registry.json",
            "B02-003_supersession_constitution.json",
            "B02-003_supersession_authority_registry.json",
            "B02-003_supersession_lineage_registry.json",
            "B02-003_historical_integrity_constitution.json",
            "B02-003_historical_preservation_registry.json",
            "B02-003_historical_lineage_registry.json",
            "B02-003_historical_evidence_registry.json",
            "B02-003_historical_reconstruction_registry.json",
            "B02-003_constitutional_correction_completeness_assessment.json",
            "B02-003_constitutional_replay_completeness_assessment.json",
            "B02-003_constitutional_recovery_completeness_assessment.json",
            "B02-003_constitutional_supersession_completeness_assessment.json",
            "B02-003_constitutional_historical_integrity_assessment.json",
            "B02-003_unresolved_constitutional_findings_registry.json",
            "B02-003_correction_replay_supersession_and_historical_integrity_constitutional_report.json",
            "B02-003_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

    def test_b02_003_correction_replay_recovery_supersession_are_complete(self) -> None:
        corrections = json.loads((EVIDENCE_ROOT / "B02-003_correction_authority_registry.json").read_text(encoding="utf-8"))
        replay = json.loads((EVIDENCE_ROOT / "B02-003_replay_constitution.json").read_text(encoding="utf-8"))
        recovery = json.loads((EVIDENCE_ROOT / "B02-003_recovery_scenario_registry.json").read_text(encoding="utf-8"))
        supersession = json.loads((EVIDENCE_ROOT / "B02-003_supersession_authority_registry.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B02-003_unresolved_constitutional_findings_registry.json").read_text(encoding="utf-8"))

        self.assertTrue({"data_correction", "broker_correction", "reconciliation_correction", "quantity_correction", "cost_basis_correction", "lifecycle_correction", "temporal_correction", "historical_correction", "identity_correction"}.issubset({item["correction_category"] for item in corrections}))
        self.assertTrue(all(not item["ambiguous_authority"] for item in corrections))
        self.assertTrue(replay["duplicate_historical_mutation_prohibited"])
        self.assertTrue(replay["truth_preservation"])
        self.assertTrue({"process_restart", "persistence_restoration", "partial_write_recovery", "interrupted_mutation", "interrupted_replay", "corrupted_state", "missing_state", "historical_reconstruction"}.issubset({item["scenario"] for item in recovery}))
        self.assertTrue(all(item["historical_evidence_preserved"] for item in supersession))
        self.assertEqual(unresolved, [])

    def test_b02_003_historical_artifacts_are_immutable_and_reconstructable(self) -> None:
        integrity = json.loads((EVIDENCE_ROOT / "B02-003_historical_integrity_constitution.json").read_text(encoding="utf-8"))
        preservation = json.loads((EVIDENCE_ROOT / "B02-003_historical_preservation_registry.json").read_text(encoding="utf-8"))
        lineage = json.loads((EVIDENCE_ROOT / "B02-003_historical_lineage_registry.json").read_text(encoding="utf-8"))
        evidence = json.loads((EVIDENCE_ROOT / "B02-003_historical_evidence_registry.json").read_text(encoding="utf-8"))
        reconstruction = json.loads((EVIDENCE_ROOT / "B02-003_historical_reconstruction_registry.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "B02-003_completion_report.json").read_text(encoding="utf-8"))

        self.assertTrue(integrity["immutable_historical_truth"])
        self.assertTrue(all(item["retention_obligations"].startswith("permanent") for item in preservation))
        self.assertTrue(all(item["lineage_required"] for item in lineage))
        self.assertTrue(all(item["evidence_overwrite_prohibited"] and item["evidence_destruction_prohibited"] for item in evidence))
        self.assertTrue(all(item["canonical_identity_preserved"] and item["deterministic_reconstruction"] for item in reconstruction))
        self.assertFalse(completion["implementation_evaluated"])
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["certification_activity_executed"])

    def test_b02_004_baseline_has_no_unresolved_findings_or_certification(self) -> None:
        baseline = json.loads((EVIDENCE_ROOT / "B02-004_authoritative_position_registry_object_and_lifecycle_baseline.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(baseline["unresolved_constitutional_finding_registry"], [])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_certification_issued"])

    def test_b02_004_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B02-004_authoritative_constitutional_object_baseline.json",
            "B02-004_authoritative_lifecycle_baseline.json",
            "B02-004_authoritative_quantity_baseline.json",
            "B02-004_authoritative_cost_basis_baseline.json",
            "B02-004_authoritative_temporal_baseline.json",
            "B02-004_authoritative_replay_baseline.json",
            "B02-004_authoritative_recovery_baseline.json",
            "B02-004_authoritative_correction_baseline.json",
            "B02-004_authoritative_supersession_baseline.json",
            "B02-004_authoritative_historical_integrity_baseline.json",
            "B02-004_constitutional_behavioral_baseline.json",
            "B02-004_constitutional_reconciliation_registry.json",
            "B02-004_constitutional_consistency_registry.json",
            "B02-004_constitutional_completeness_assessment.json",
            "B02-004_constitutional_conflict_registry.json",
            "B02-004_unresolved_constitutional_findings_registry.json",
            "B02-004_authoritative_constitutional_behavioral_report.json",
            "B02-004_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

    def test_b02_004_reconciles_all_series_2_domains_without_conflicts(self) -> None:
        baseline = json.loads((EVIDENCE_ROOT / "B02-004_constitutional_behavioral_baseline.json").read_text(encoding="utf-8"))
        reconciliation = json.loads((EVIDENCE_ROOT / "B02-004_constitutional_reconciliation_registry.json").read_text(encoding="utf-8"))
        consistency = json.loads((EVIDENCE_ROOT / "B02-004_constitutional_consistency_registry.json").read_text(encoding="utf-8"))
        completeness = json.loads((EVIDENCE_ROOT / "B02-004_constitutional_completeness_assessment.json").read_text(encoding="utf-8"))
        conflicts = json.loads((EVIDENCE_ROOT / "B02-004_constitutional_conflict_registry.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B02-004_unresolved_constitutional_findings_registry.json").read_text(encoding="utf-8"))

        self.assertEqual(baseline["source_orders"], ["B02-001", "B02-002", "B02-003"])
        self.assertEqual(baseline["normative_status"], "AUTHORITATIVE_SERIES_2_BEHAVIORAL_BASELINE")
        self.assertTrue(baseline["deterministic_and_reproducible"])
        self.assertTrue(all(item["disposition"] == "RECONCILED" and not item["conflict"] for item in reconciliation))
        self.assertEqual(consistency["contradictory_constitutional_rules"], [])
        self.assertEqual(consistency["duplicate_constitutional_semantics"], [])
        self.assertEqual(conflicts, [])
        self.assertEqual(unresolved, [])
        self.assertTrue(all(value is True or value == [] for value in completeness.values()))

    def test_b02_004_completion_is_doctrine_only(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "B02-004_completion_report.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B02-004_authoritative_constitutional_behavioral_report.json").read_text(encoding="utf-8"))
        self.assertTrue(completion["authoritative_constitutional_behavioral_baseline_established"])
        self.assertEqual(completion["duplicate_constitutional_doctrine"], 0)
        self.assertEqual(completion["conflicting_constitutional_doctrine"], 0)
        self.assertFalse(completion["new_doctrine_introduced"])
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["implementation_participation_evaluated"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["certification_activity_executed"])
        self.assertEqual(report["unresolved_findings"], 0)


if __name__ == "__main__":
    unittest.main()
