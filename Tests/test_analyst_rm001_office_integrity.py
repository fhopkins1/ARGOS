from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import AnalystLifecycleState, AnalystOfficeIntegritySupport  # noqa: E402
from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402


def admissible_input(**overrides):
    data = {
        "canonical_identifier": "AN-IN-000001",
        "object_class": "Candidate Package",
        "object_version": "1.0.0",
        "owner": "Seeker Office",
        "producer_office": "Seeker Office",
        "production_timestamp": "2026-07-22T09:00:00Z",
        "constitutional_schema_version": "1.0.0",
        "provenance_metadata": {"workflow": "WF-AN-001", "authority": "Commander"},
        "integrity_verification_metadata": {"sha256": "abc123"},
        "admissibility_metadata": {"validated": True},
    }
    data.update(overrides)
    return data


def complete_output(**overrides):
    data = {
        "output_identifier": "AN-OUT-000001",
        "output_type": "Analytical Assessment",
        "source_analysis_identifier": "AN-MISSION-000001",
        "analyst_office_identifier": "Analyst Office",
        "version": "1.0.0",
        "creation_timestamp": "2026-07-22T09:05:00Z",
        "constitutional_owner": "Analyst Office",
        "schema_version": "1.0.0",
        "provenance_identifier": "AN-PROV-000001",
        "certification_state": "Validated",
        "mandatory_fields_populated": True,
        "reasoning_complete": True,
        "evidence_attached": True,
        "validation_complete": True,
        "invariants_satisfied": True,
        "confidence_established": True,
        "contradictions_resolved": True,
        "provenance_finalized": True,
        "schema_validated": True,
        "certification_state_assigned": True,
    }
    data.update(overrides)
    return data


class AnalystRm001OfficeIntegrityTests(unittest.TestCase):
    def test_rm001_package_covers_authority_objects_inputs_outputs_and_lifecycle(self) -> None:
        package = AnalystOfficeIntegritySupport().build_package(
            input_object=admissible_input(),
            output_object=complete_output(),
        )

        self.assertEqual(package.final_rm001_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            (
                "ANALYST-RM-001-001",
                "ANALYST-RM-001-002",
                "ANALYST-RM-001-003",
                "ANALYST-RM-001-004",
                "ANALYST-RM-001-005",
            ),
        )
        self.assertIn("Analytical Reasoning", package.authority_boundary.exclusive_authorities)
        self.assertIn("Execute Trades", package.authority_boundary.prohibited_authorities)
        self.assertEqual(len(package.object_inventory.object_registry), 12)
        self.assertEqual(package.input_admissibility.admissibility_decision, "Admitted")
        self.assertEqual(package.input_admissibility.rejection_taxonomy, ())
        self.assertEqual(package.output_contracts.delivery_decision, "Deliver")
        self.assertTrue(package.output_contracts.delivery_atomic)
        self.assertEqual(package.lifecycle_remediation.final_state, AnalystLifecycleState.CERTIFIED.value)
        self.assertEqual(package.lifecycle_remediation.illegal_transitions, ())
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm001_records_fail_closed_on_boundary_input_output_and_lifecycle_defects(self) -> None:
        support = AnalystOfficeIntegritySupport()

        authority = support.evaluate_authority_boundary(
            undefined_responsibilities=("analytical_risk_scoring",),
            overlapping_authorities=("Risk Office: uncertainty evaluation",),
            prohibited_authority_findings=("trade_execution_attempt",),
        )
        inventory = support.evaluate_object_inventory(
            undefined_objects=("Scenario Evaluation",),
            ambiguous_ownership=("Analytical Recommendation",),
            circular_relationships=("Analytical Assessment->Analytical Trace Record->Analytical Assessment",),
        )
        input_record = support.evaluate_input_admissibility(
            admissible_input(
                object_class="Direct User Prompt",
                owner="Operator",
                provenance_metadata={},
                constitutional_schema_version="",
                corrupt=True,
            ),
            duplicate_findings=("AN-IN-000001",),
        )
        output_record = support.evaluate_output_contract(
            complete_output(
                output_type="Trade Instruction",
                confidence_established=False,
                provenance_chain_complete=False,
                recovery_preserves_ownership=False,
            ),
            failed_validations=("Reasoning Integrity",),
        )
        lifecycle = support.evaluate_lifecycle_remediation(
            (
                AnalystLifecycleState.CREATED.value,
                AnalystLifecycleState.ANALYTICAL_PROCESSING.value,
                AnalystLifecycleState.CERTIFIED.value,
            ),
            multiple_active_state_findings=("Created+Processing",),
            validation_failures=("missing_input_validation",),
            replay_equivalent=False,
            recovery_preserves_lifecycle=False,
        )

        self.assertEqual(authority.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("trade_execution_attempt", authority.prohibited_authority_findings)
        self.assertEqual(inventory.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Scenario Evaluation", inventory.undefined_objects)
        self.assertEqual(input_record.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(input_record.admissibility_decision, "Rejected")
        self.assertIn("unauthorized_input_class", input_record.rejection_taxonomy)
        self.assertIn("failed_integrity_verification", input_record.rejection_taxonomy)
        self.assertEqual(output_record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("unauthorized_output_type", output_record.failed_validations)
        self.assertIn("confidence_established", output_record.unmet_completion_requirements)
        self.assertEqual(output_record.delivery_decision, "Do Not Deliver")
        self.assertEqual(lifecycle.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Created->Analytical Processing", lifecycle.illegal_transitions)
        self.assertIn("Created+Processing", lifecycle.multiple_active_state_findings)
        self.assertFalse(lifecycle.replay_equivalent)

    def test_rm001_architecture_package_covers_validation_decision_persistence_replay_and_recovery(self) -> None:
        package = AnalystOfficeIntegritySupport().build_architecture_package()

        self.assertEqual(package.final_architecture_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            (
                "ANALYST-RM-001-006",
                "ANALYST-RM-001-007",
                "ANALYST-RM-001-008",
                "ANALYST-RM-001-009",
                "ANALYST-RM-001-010",
            ),
        )
        self.assertEqual(package.validation_architecture.validation_sequence[0], "Identity Validation")
        self.assertEqual(package.validation_architecture.ordering_violations, ())
        self.assertIn("Output Readiness Decision", package.decision_architecture.decision_registry)
        self.assertEqual(package.decision_architecture.fail_closed_decisions, ())
        self.assertIn("Analytical Decisions", package.persistence_architecture.persistent_state_registry)
        self.assertIn("temporary caches", package.persistence_architecture.transient_state_registry)
        self.assertEqual(package.persistence_architecture.partial_commit_findings, ())
        self.assertEqual(package.replay_architecture.replay_outcome, "Equivalent")
        self.assertIn("analytical conclusions", package.replay_architecture.non_admissible_variations)
        self.assertTrue(package.recovery_architecture.idempotent_recovery)
        self.assertTrue(package.recovery_architecture.restart_authorized)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm001_architecture_records_fail_closed_on_defects(self) -> None:
        support = AnalystOfficeIntegritySupport()

        validation = support.evaluate_validation_architecture(
            observed_sequence=("Schema Validation", "Identity Validation"),
            failed_validation_stages=("Ownership Validation",),
            contradiction_reports=("evidence_conflict_preserved",),
            missing_information_findings=("missing_source_lineage",),
            reasoning_integrity_findings=("unsupported_assumption",),
        )
        decision = support.evaluate_decision_architecture(
            missing_decisions=("Replay Equivalence Decision",),
            ambiguous_authority=("Risk Office overlap on uncertainty",),
            circular_dependencies=("Output Readiness Decision->Input Admissibility Decision",),
            undocumented_inputs=("runtime_cache",),
            unsupported_assumptions=("estimated_evidence",),
            deterministic_replay_supported=False,
        )
        persistence = support.evaluate_persistence_architecture(
            missing_persistent_state=("Analytical Decisions",),
            transient_evidence_violations=("temporary cache committed"),
            missing_commit_boundaries=("decision publication",),
            partial_commit_findings=("validation_result_without_audit"),
            durability_failures=("restart_lost_decision"),
            integrity_verification_failures=("checksum_missing"),
            replay_compatible=False,
            recovery_compatible=False,
        )
        replay = support.evaluate_replay_architecture(
            missing_prerequisites=("required schemas",),
            production_mutation_findings=("production_output_overwritten"),
            replay_divergence_findings=("confidence calculation changed"),
            provenance_gaps=("replay input missing source trace"),
            validation_failures=("schema compatibility failed"),
        )
        recovery = support.evaluate_recovery_architecture(
            missing_checkpoint_fields=("integrity verification data",),
            unauthorized_recovery_attempts=("Risk Office selected checkpoint"),
            invariant_violations=("ownership changed"),
            duplicate_recovery_effects=("decision replayed twice"),
            partial_recovery_findings=("uncommitted finding restored"),
            idempotent_recovery=False,
            restart_authorized=False,
        )

        self.assertEqual(validation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Schema Validation->Identity Validation", validation.ordering_violations)
        self.assertTrue(validation.downstream_reasoning_blocked)
        self.assertEqual(decision.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("runtime_cache", decision.undocumented_inputs)
        self.assertIn("Replay Equivalence Decision", decision.fail_closed_decisions)
        self.assertEqual(persistence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Analytical Decisions", persistence.missing_persistent_state)
        self.assertIn("temporary cache committed", persistence.transient_evidence_violations)
        self.assertEqual(replay.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(replay.replay_outcome, "Failed")
        self.assertIn("confidence calculation changed", replay.replay_divergence_findings)
        self.assertEqual(recovery.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Risk Office selected checkpoint", recovery.unauthorized_recovery_attempts)
        self.assertFalse(recovery.restart_authorized)


if __name__ == "__main__":
    unittest.main()
