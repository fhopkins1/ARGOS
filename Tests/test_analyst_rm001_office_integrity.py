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


if __name__ == "__main__":
    unittest.main()
