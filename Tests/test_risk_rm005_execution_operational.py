from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskRm005ArtifactRecord, RiskRm005ExecutionOperationalSupport  # noqa: E402


class RiskRm005ExecutionOperationalTests(unittest.TestCase):
    def test_execution_package_covers_attached_orders_and_records_missing_seven(self) -> None:
        package = RiskRm005ExecutionOperationalSupport().build_operational_package(REPOSITORY_ROOT)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-005-006",
                "RISK-RM-005-008",
                "RISK-RM-005-009",
                "RISK-RM-005-010",
            ),
        )
        self.assertIn("RISK-RM-005-007 was not attached", package.omitted_order_notes[0])
        self.assertGreater(package.coverage_summary["schema_validated_artifacts"], 0)
        self.assertEqual(package.coverage_summary["schema_validated_artifacts"], package.coverage_summary["passing_schema_validations"])
        self.assertGreater(package.coverage_summary["registered_tests"], 0)
        self.assertEqual(package.coverage_summary["registered_tests"], package.coverage_summary["executed_tests"])
        self.assertEqual(package.coverage_summary["executed_tests"], package.coverage_summary["passing_test_executions"])
        self.assertNotEqual(package.deterministic_digest, "")

    def test_temp_candidate_materializes_schema_rules_tests_and_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "argos" / "risk").mkdir(parents=True)
            (root / "Tests").mkdir()
            (root / "src" / "argos" / "risk" / "candidate_surface.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "Tests" / "test_risk_candidate_operational.py").write_text("def test_surface():\n    assert True\n", encoding="utf-8")
            package = RiskRm005ExecutionOperationalSupport().build_operational_package(root)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(len(package.schema_validations), 2)
        self.assertEqual(len(package.rule_evaluations), 2)
        self.assertEqual(len(package.certification_tests), 1)
        self.assertEqual(len(package.test_executions), 1)
        self.assertEqual(package.test_executions[0].result, EnterpriseCertificationDecision.PASS)

    def test_schema_validation_fails_closed_on_invalid_artifact_digest_and_class(self) -> None:
        artifact = RiskRm005ArtifactRecord(
            artifact_identifier="ARTIFACT-1",
            relative_path="src/argos/risk/bad.py",
            artifact_class="unexpected-class",
            constitutional_owner="Risk Office",
            byte_size=1,
            content_digest="bad",
            candidate_digest="candidate",
        )

        validation = RiskRm005ExecutionOperationalSupport().validate_schema(artifact)

        self.assertEqual(validation.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("artifact content digest invalid", validation.findings)
        self.assertIn("artifact class not governed by executable Risk schema", validation.findings)

    def test_rule_and_test_execution_fail_closed_when_prerequisites_fail(self) -> None:
        support = RiskRm005ExecutionOperationalSupport()
        artifact = RiskRm005ArtifactRecord(
            artifact_identifier="ARTIFACT-2",
            relative_path="Tests/not_a_certification_test.py",
            artifact_class="risk-certification-test",
            constitutional_owner="Risk Office",
            byte_size=1,
            content_digest="a" * 64,
            candidate_digest="candidate",
        )
        validation = support.validate_schema(artifact, findings=("forced schema failure",))
        rule = support.evaluate_rule(artifact, validation)
        test_record = support.populate_test_record(artifact, 1)
        execution = support.execute_test_record(test_record, 1)

        self.assertEqual(rule.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("schema validation failed before rule evaluation", rule.findings)
        self.assertEqual(test_record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("test artifact is not executable Risk certification test", test_record.findings)
        self.assertEqual(execution.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("test execution blocked by non-executable registry record", execution.findings)


if __name__ == "__main__":
    unittest.main()
