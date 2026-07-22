from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import AnalystOfficeSpecificationSupport  # noqa: E402
from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402


class AnalystRm003OfficeSpecificationTests(unittest.TestCase):
    def test_rm003_analytical_mission_specification_covers_root_authority_object(self) -> None:
        package = AnalystOfficeSpecificationSupport().build_package()

        mission = package.analytical_mission
        self.assertEqual(package.final_specification_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(package.specification_order_coverage, ("ANALYST-RM-003-001",))
        self.assertIn("Identity", mission.schema_sections)
        self.assertIn("Mission Identifier", mission.schema_sections["Identity"])
        self.assertIn("Mission Authority Token", mission.schema_sections["Authority"])
        self.assertIn("Completion Contract", mission.schema_sections["Mission Definition"])
        self.assertIn("Workflow Execution Token Identifier", mission.identity_fields)
        self.assertIn("perform deterministic reasoning", mission.permitted_authorities)
        self.assertIn("trade execution", mission.prohibited_authorities)
        self.assertIn("Analysis Plan", mission.subordinate_relationships)
        self.assertIn("Recovering", mission.lifecycle_states)
        self.assertIn("identifier uniqueness", mission.validation_requirements)
        self.assertIn("mission identity", mission.persistent_elements)
        self.assertIn("Mission Identifier", mission.replay_restoration_fields)
        self.assertIn("mission version", mission.recovery_restoration_fields)
        self.assertIn("authorization", mission.audit_events)
        self.assertIn("mission identity is immutable", mission.invariant_registry)
        self.assertTrue(mission.fail_closed)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_rm003_analytical_mission_specification_fails_closed_on_defects(self) -> None:
        mission = AnalystOfficeSpecificationSupport().evaluate_analytical_mission_specification(
            missing_schema_fields=("Mission Authority Token", "Completion Contract"),
            duplicate_identity_findings=("AN-MISSION-1 reused",),
            authority_violations=("trade execution granted",),
            lifecycle_violations=("Created->Active",),
            validation_failures=("configuration compatibility failed",),
            persistence_gaps=("audit metadata",),
            replay_divergence_findings=("mission identity regenerated",),
            recovery_inference_findings=("scope inferred from output",),
            traceability_gaps=("reasoning graph missing parent mission",),
            fail_closed=False,
        )

        self.assertEqual(mission.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Mission Authority Token", mission.missing_schema_fields)
        self.assertIn("Completion Contract", mission.missing_schema_fields)
        self.assertIn("AN-MISSION-1 reused", mission.duplicate_identity_findings)
        self.assertIn("trade execution granted", mission.authority_violations)
        self.assertIn("Created->Active", mission.lifecycle_violations)
        self.assertIn("configuration compatibility failed", mission.validation_failures)
        self.assertIn("mission identity regenerated", mission.replay_divergence_findings)
        self.assertIn("scope inferred from output", mission.recovery_inference_findings)
        self.assertFalse(mission.fail_closed)


if __name__ == "__main__":
    unittest.main()
