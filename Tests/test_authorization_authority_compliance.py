from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.authorization_authority import (  # noqa: E402
    AuthorizationComplianceStatus,
    AuthorizationsOfficeComplianceSupport,
)


class AuthorizationsOfficeComplianceTests(unittest.TestCase):
    def test_auth_rm001_compliance_package_covers_revised_orders(self) -> None:
        package = AuthorizationsOfficeComplianceSupport().build_compliance_package(REPOSITORY_ROOT)

        self.assertEqual(package.order_coverage, tuple(f"AUTH-RM-001-{index:03d}" for index in range(1, 9)))
        self.assertEqual(package.final_status, AuthorizationComplianceStatus.PASSING)
        self.assertTrue(package.candidate_compliance.immutable_commit_bound)
        self.assertTrue(package.candidate_compliance.artifact_inventory_bound)
        self.assertTrue(package.candidate_compliance.evidence_candidate_aligned)
        self.assertEqual(len(package.requirements), 8)
        self.assertEqual(len(package.certification_tests), 8)
        self.assertEqual(len(package.certification_test_executions), 8)
        self.assertFalse(package.findings)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_certification_tests_are_executable_and_candidate_bound(self) -> None:
        package = AuthorizationsOfficeComplianceSupport().build_compliance_package(REPOSITORY_ROOT)

        self.assertTrue(
            all(record.candidate_identifier == package.candidate_compliance.candidate_identifier for record in package.certification_test_executions)
        )
        self.assertTrue(all(record.status == AuthorizationComplianceStatus.PASSING for record in package.certification_test_executions))
        self.assertTrue(all(record.required_evidence for record in package.certification_tests))
        self.assertEqual(package.certification_infrastructure.decision, AuthorizationComplianceStatus.PASSING)
        self.assertEqual(package.certification_infrastructure.test_count, len(package.certification_tests))
        self.assertGreaterEqual(package.certification_infrastructure.registry_count, 10)

    def test_missing_canonical_artifact_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Documentation").mkdir()
            (root / "Documentation" / "AUTH-RM-001-001_TO_013_REMEDIATION_EVIDENCE.md").write_text("evidence\n", encoding="utf-8")
            package = AuthorizationsOfficeComplianceSupport().build_compliance_package(root)

        self.assertEqual(package.final_status, AuthorizationComplianceStatus.FAILING)
        self.assertIn("required Authorizations artifact missing", package.findings)
        self.assertTrue(all(record.status == AuthorizationComplianceStatus.FAILING for record in package.certification_test_executions))

    def test_persistence_replay_and_recovery_are_verified(self) -> None:
        package = AuthorizationsOfficeComplianceSupport().build_compliance_package(REPOSITORY_ROOT)
        verification = package.persistence_verification

        self.assertTrue(verification.replay_semantically_equivalent)
        self.assertTrue(verification.recovery_semantically_equivalent)
        self.assertTrue(verification.interruption_boundary_verified)
        self.assertTrue(verification.idempotency_verified)
        self.assertFalse(verification.findings)


if __name__ == "__main__":
    unittest.main()
