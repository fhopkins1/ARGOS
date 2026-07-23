from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.authorization_final_certification import (  # noqa: E402
    AuthorizationFinalCertificationVerdict,
    AuthorizationRunIsolationStatus,
    AuthorizationsOfficeFinalCertificationSupport,
)
from argos.control_panel.authorization_portable_certification import AuthorizationPortableStatus  # noqa: E402


class AuthorizationsOfficeFinalCertificationTests(unittest.TestCase):
    def test_auth_rm005_submission_covers_all_final_work_orders(self) -> None:
        submission = AuthorizationsOfficeFinalCertificationSupport().build_final_certification_submission(REPOSITORY_ROOT)

        self.assertEqual(submission.order_coverage, tuple(f"AUTH-RM-005-{index:03d}" for index in range(1, 13)))
        self.assertEqual(
            submission.final_verdict,
            AuthorizationFinalCertificationVerdict.UNCONDITIONAL_INDEPENDENT_AUTHORIZATIONS_OFFICE_CERTIFICATION_PASS,
        )
        self.assertFalse(submission.findings)
        self.assertNotEqual(submission.deterministic_digest, "")

    def test_final_candidate_is_enumerated_and_reconciled_from_package(self) -> None:
        submission = AuthorizationsOfficeFinalCertificationSupport().build_final_certification_submission(REPOSITORY_ROOT)
        enumeration = submission.candidate_enumeration

        self.assertGreater(enumeration.artifact_count, 0)
        self.assertGreater(enumeration.evidence_count, 0)
        self.assertTrue(enumeration.file_to_manifest_reconciled)
        self.assertTrue(enumeration.manifest_to_file_reconciled)
        self.assertTrue(enumeration.orphan_evidence_free)

    def test_package_bound_runner_prohibits_repository_access(self) -> None:
        submission = AuthorizationsOfficeFinalCertificationSupport().build_final_certification_submission(REPOSITORY_ROOT)
        runner = submission.package_bound_runner

        self.assertTrue(runner.repository_access_prohibited)
        self.assertTrue(runner.package_sovereignty_verified)
        self.assertEqual(runner.status, AuthorizationPortableStatus.PASSING)
        self.assertIn("PACKAGE_LOCKED", runner.execution_lifecycle)

    def test_dependency_discovery_and_explicit_traceability_are_complete(self) -> None:
        submission = AuthorizationsOfficeFinalCertificationSupport().build_final_certification_submission(REPOSITORY_ROOT)

        self.assertTrue(submission.dependency_discovery)
        self.assertTrue(all(record.discovered_from_package_only for record in submission.dependency_discovery))
        self.assertTrue(all(record.dependency_targets for record in submission.dependency_discovery))
        self.assertTrue(submission.explicit_traceability_registry)
        self.assertTrue(all(record.evidence_hash for record in submission.explicit_traceability_registry))
        self.assertTrue(all(not record.findings for record in submission.explicit_traceability_registry))

    def test_persistence_and_recovery_harnesses_cross_process_boundary(self) -> None:
        submission = AuthorizationsOfficeFinalCertificationSupport().build_final_certification_submission(REPOSITORY_ROOT)

        self.assertEqual(submission.persistence_harness.status, AuthorizationPortableStatus.PASSING)
        self.assertEqual(submission.persistence_harness.committed_digest, submission.persistence_harness.fresh_process_digest)
        self.assertTrue(submission.persistence_harness.idempotency_verified)
        self.assertEqual(submission.recovery_harness.status, AuthorizationPortableStatus.PASSING)
        self.assertEqual(submission.recovery_harness.committed_digest, submission.recovery_harness.restored_digest)

    def test_dual_clean_room_execution_and_normalized_comparison_pass(self) -> None:
        submission = AuthorizationsOfficeFinalCertificationSupport().build_final_certification_submission(REPOSITORY_ROOT)

        self.assertEqual(submission.dual_clean_room_execution.isolation_status, AuthorizationRunIsolationStatus.ISOLATED)
        self.assertTrue(submission.dual_clean_room_execution.equivalent)
        self.assertNotEqual(submission.dual_clean_room_execution.run_a_digest, submission.dual_clean_room_execution.run_b_digest)
        self.assertTrue(submission.normalized_comparison.equivalent)
        self.assertFalse(submission.normalized_comparison.prohibited_differences)

    def test_evidence_export_environment_lock_and_provenance_are_complete(self) -> None:
        submission = AuthorizationsOfficeFinalCertificationSupport().build_final_certification_submission(REPOSITORY_ROOT)

        self.assertEqual(submission.portable_evidence_export.verification_status, AuthorizationPortableStatus.PASSING)
        self.assertGreaterEqual(len(submission.portable_evidence_export.exported_artifacts), 16)
        self.assertTrue(submission.portable_evidence_export.platform_independent)
        self.assertTrue(submission.portable_evidence_export.repository_independent)
        self.assertTrue(submission.locked_environment.deterministic)
        self.assertTrue(all(record.package_inclusion_verified for record in submission.evidence_provenance))
        self.assertTrue(all(record.reverse_trace_digest for record in submission.evidence_provenance))

    def test_final_submission_is_reproducible(self) -> None:
        support = AuthorizationsOfficeFinalCertificationSupport()
        first = support.build_final_certification_submission(REPOSITORY_ROOT)
        second = support.build_final_certification_submission(REPOSITORY_ROOT)

        self.assertEqual(first.deterministic_digest, second.deterministic_digest)
        self.assertEqual(first.final_verdict, second.final_verdict)


if __name__ == "__main__":
    unittest.main()
