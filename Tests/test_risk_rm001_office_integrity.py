from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskOfficeIntegritySupport  # noqa: E402


class RiskRm001OfficeIntegrityTests(unittest.TestCase):
    def test_rm001_integrity_package_covers_authority_objects_inputs_outputs_and_lifecycle(self) -> None:
        package = RiskOfficeIntegritySupport().build_integrity_package()

        self.assertEqual(package.final_integrity_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-001-001",
                "RISK-RM-001-002",
                "RISK-RM-001-003",
                "RISK-RM-001-004",
                "RISK-RM-001-005",
            ),
        )
        self.assertIn("evaluate risk", package.authority_boundaries.exclusive_authorities)
        self.assertIn("execute trades", package.authority_boundaries.prohibited_authorities)
        self.assertEqual(len(package.object_inventory.objects), 15)
        self.assertIn("RO-007", {item.object_identifier for item in package.object_inventory.objects})
        self.assertIn("Analyst Office", package.input_admissibility.authorized_sources)
        self.assertIn("Constitutional Compatibility", package.input_admissibility.validation_gates)
        self.assertIn("Risk Decision", package.output_contracts.authorized_outputs)
        self.assertIn("exactly-once constitutional delivery", package.output_contracts.delivery_semantics)
        self.assertEqual(len(package.lifecycle.universal_states), 18)
        self.assertIn("TERMINATED", package.lifecycle.exceptional_terminal_states)
        self.assertIn("Replay Tests", package.lifecycle.required_test_classes)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm001_integrity_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeIntegritySupport()

        authority = support.evaluate_authority_boundaries(
            unauthorized_authority_findings=("Risk attempted execution",),
            boundary_ambiguity_findings=("Analyst modification boundary unclear",),
            activation_findings=("unauthorized activation accepted",),
            deactivation_findings=("transient state remained active",),
            ownership_findings=("shared ownership detected",),
            interface_findings=("foreign state mutation",),
            invariant_violations=("Risk override Commander",),
        )
        inventory = support.evaluate_object_inventory(
            missing_object_findings=("RO-015 missing",),
            duplicate_identifier_findings=("RO-007 duplicated",),
            ownership_findings=("Risk Decision co-owned",),
            incomplete_definition_findings=("Risk Evidence Package lacks replay",),
            scope_findings=("Risk Rule Set owns foreign config",),
            traceability_gaps=("Risk Finding lacks lineage",),
        )
        inputs = support.evaluate_input_admissibility(
            unauthorized_source_findings=("Seeker submitted raw market opportunity",),
            missing_metadata_findings=("workflow identifier missing",),
            ownership_findings=("input has shared owner",),
            schema_findings=("invalid schema",),
            integrity_findings=("hash mismatch",),
            provenance_gaps=("origin unverifiable",),
            freshness_findings=("expired input admitted",),
            duplicate_handling_findings=("manual duplicate resolution",),
            rejection_findings=("rejected input entered evaluation",),
        )
        outputs = support.evaluate_output_contracts(
            unauthorized_output_findings=("Trade Order produced",),
            completion_findings=("partial output delivered",),
            delivery_findings=("delivery before persistence",),
            acceptance_findings=("accepted without verification",),
            immutability_findings=("completed output mutated",),
            persistence_findings=("audit record not persisted",),
            replay_recovery_findings=("replay output changed",),
            traceability_gaps=("output lacks evidence link",),
        )
        lifecycle = support.evaluate_lifecycle(
            undefined_state_findings=("implementation-defined state",),
            ownership_findings=("silent ownership transfer",),
            transition_findings=("unregistered transition",),
            validation_findings=("entered active before validation",),
            completion_findings=("completed by assumption",),
            terminal_disposition_findings=("terminal object reactivated",),
            persistence_findings=("transition record lost",),
            replay_recovery_findings=("recovery inferred state",),
            traceability_gaps=("terminal disposition unaudited",),
        )

        self.assertEqual(authority.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Risk attempted execution", authority.unauthorized_authority_findings)
        self.assertIn("shared ownership detected", authority.ownership_findings)
        self.assertEqual(inventory.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("RO-015 missing", inventory.missing_object_findings)
        self.assertIn("Risk Evidence Package lacks replay", inventory.incomplete_definition_findings)
        self.assertEqual(inputs.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("expired input admitted", inputs.freshness_findings)
        self.assertIn("rejected input entered evaluation", inputs.rejection_findings)
        self.assertEqual(outputs.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Trade Order produced", outputs.unauthorized_output_findings)
        self.assertIn("completed output mutated", outputs.immutability_findings)
        self.assertEqual(lifecycle.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("unregistered transition", lifecycle.transition_findings)
        self.assertIn("terminal object reactivated", lifecycle.terminal_disposition_findings)

    def test_rm001_architecture_package_covers_validation_decision_persistence_replay_and_recovery(self) -> None:
        package = RiskOfficeIntegritySupport().build_architecture_package()

        self.assertEqual(package.final_architecture_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-001-006",
                "RISK-RM-001-007",
                "RISK-RM-001-008",
                "RISK-RM-001-009",
                "RISK-RM-001-010",
            ),
        )
        self.assertEqual(len(package.validation_architecture.validation_categories), 10)
        self.assertEqual(package.validation_architecture.validation_outcomes, ("Valid", "Invalid", "Incomplete"))
        self.assertIn("RD-006 Risk Acceptance Decision", package.decision_architecture.canonical_decisions)
        self.assertEqual(package.decision_architecture.authority_matrix["RD-001 Input Admissibility Decision"], "Risk Office")
        self.assertIn("Risk Decision Record", package.persistence_architecture.persistent_state_inventory)
        self.assertIn("Checkpoint Persisted", package.persistence_architecture.persistence_ordering)
        self.assertIn("Independent Certification", package.replay_architecture.authorized_replay_authorities)
        self.assertIn("decision mismatch", package.replay_architecture.failure_conditions)
        self.assertIn("UNKNOWN_INTERRUPTION", package.recovery_architecture.interruption_classes)
        self.assertIn("COMMIT_STATUS_AMBIGUOUS", package.recovery_architecture.commit_ambiguity_classes)
        self.assertIn("Idempotency Tests", package.recovery_architecture.required_test_classes)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm001_architecture_records_fail_closed_on_defects(self) -> None:
        support = RiskOfficeIntegritySupport()

        validation = support.evaluate_validation_architecture(
            ownership_findings=("shared validation owner",),
            sequence_findings=("validation stage skipped",),
            precondition_findings=("configuration unverified",),
            outcome_findings=("Maybe outcome",),
            rejection_findings=("invalid artifact progressed",),
            evidence_gaps=("validation evidence missing",),
            invariant_violations=("validation modified evidence",),
        )
        decision = support.evaluate_decision_architecture(
            missing_decision_findings=("RD-006 absent",),
            ownership_findings=("delegated Risk decision",),
            hidden_input_findings=("hidden runtime heuristic",),
            precondition_findings=("decision before evidence",),
            sequence_findings=("Risk Acceptance before Rule Validation",),
            unsupported_outcome_findings=("DEFERRED",),
            evidence_gaps=("justification absent",),
            replay_recovery_gaps=("decision replay changed",),
        )
        persistence = support.evaluate_persistence_architecture(
            missing_persistent_state_findings=("Risk Decision Record missing",),
            transient_state_findings=("cache required for correctness",),
            ownership_findings=("Audit Record co-owned",),
            atomicity_findings=("partial commit survived",),
            ordering_findings=("decision persisted before evidence",),
            integrity_findings=("hash absent",),
            recovery_sufficiency_findings=("cannot restore from persisted state",),
            audit_gaps=("persistence failure unaudited",),
        )
        replay = support.evaluate_replay_architecture(
            authority_findings=("production workflow initiated replay",),
            input_findings=("inferred replay input",),
            lifecycle_findings=("backward replay transition",),
            equivalence_findings=("decision mismatch",),
            side_effect_findings=("production history mutated",),
            evidence_gaps=("replay evidence absent",),
            traceability_gaps=("replay lacks source evaluation",),
        )
        recovery = support.evaluate_recovery_architecture(
            authority_findings=("Infrastructure selected Risk truth",),
            checkpoint_findings=("corrupted checkpoint admitted",),
            commit_classification_findings=("ambiguous commit retried",),
            idempotency_findings=("duplicate Risk Decision",),
            reconciliation_findings=("output delivery ambiguous",),
            corruption_quarantine_findings=("corruption silently repaired",),
            invariant_violations=("normal processing resumed early",),
            evidence_gaps=("recovery manifest missing",),
        )

        self.assertEqual(validation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("validation stage skipped", validation.sequence_findings)
        self.assertIn("validation modified evidence", validation.invariant_violations)
        self.assertEqual(decision.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("hidden runtime heuristic", decision.hidden_input_findings)
        self.assertIn("DEFERRED", decision.unsupported_outcome_findings)
        self.assertEqual(persistence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("partial commit survived", persistence.atomicity_findings)
        self.assertIn("decision persisted before evidence", persistence.ordering_findings)
        self.assertEqual(replay.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("production history mutated", replay.side_effect_findings)
        self.assertIn("decision mismatch", replay.equivalence_findings)
        self.assertEqual(recovery.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("ambiguous commit retried", recovery.commit_classification_findings)
        self.assertIn("duplicate Risk Decision", recovery.idempotency_findings)


if __name__ == "__main__":
    unittest.main()
