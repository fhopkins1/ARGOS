from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.authorization_implementation_closure import (  # noqa: E402
    AuthorizationImplementationClosureStatus,
    AuthorizationImplementationSubmissionVerdict,
    AuthorizationsOfficeImplementationClosureSupport,
)


class AuthorizationsOfficeImplementationClosureTests(unittest.TestCase):
    def test_auth_ic001_submission_covers_all_implementation_closure_orders(self) -> None:
        submission = AuthorizationsOfficeImplementationClosureSupport().build_implementation_closure_submission(REPOSITORY_ROOT)

        self.assertEqual(submission.order_coverage, tuple(f"AUTH-IC-001-{index:03d}" for index in range(1, 10)))
        self.assertEqual(submission.final_verdict, AuthorizationImplementationSubmissionVerdict.READY_FOR_INDEPENDENT_OFFICE_CERTIFICATION)
        self.assertFalse(submission.findings)
        self.assertNotEqual(submission.deterministic_digest, "")

    def test_candidate_package_integrity_is_complete_and_immutable(self) -> None:
        submission = AuthorizationsOfficeImplementationClosureSupport().build_implementation_closure_submission(REPOSITORY_ROOT)
        integrity = submission.candidate_integrity

        self.assertEqual(integrity.status, AuthorizationImplementationClosureStatus.PASSING)
        self.assertGreater(integrity.archive_artifacts_enumerated, 0)
        self.assertGreater(integrity.manifest_entries_reconciled, integrity.archive_artifacts_enumerated)
        self.assertTrue(integrity.cryptographic_hash_verified)
        self.assertTrue(integrity.canonical_paths_verified)

    def test_dependency_closure_and_traceability_are_explicit(self) -> None:
        submission = AuthorizationsOfficeImplementationClosureSupport().build_implementation_closure_submission(REPOSITORY_ROOT)

        self.assertTrue(submission.closure_graph.complete)
        self.assertTrue(submission.closure_graph.dependency_derived)
        self.assertTrue(submission.closure_graph.constitutional_edges)
        self.assertTrue(submission.explicit_traceability)
        self.assertTrue(all(record.evidence_hash for record in submission.explicit_traceability))
        self.assertTrue(all(record.forward_trace_digest and record.reverse_trace_digest for record in submission.explicit_traceability))

    def test_independent_rule_execution_is_evidence_derived(self) -> None:
        submission = AuthorizationsOfficeImplementationClosureSupport().build_implementation_closure_submission(REPOSITORY_ROOT)

        self.assertEqual(len(submission.rule_executions), len(submission.explicit_traceability))
        self.assertTrue(all(record.actual_result == AuthorizationImplementationClosureStatus.PASSING for record in submission.rule_executions))
        self.assertTrue(all(record.evidence_digest for record in submission.rule_executions))

    def test_persistence_and_recovery_harnesses_use_fresh_process_state(self) -> None:
        submission = AuthorizationsOfficeImplementationClosureSupport().build_implementation_closure_submission(REPOSITORY_ROOT)

        self.assertTrue(submission.persistence_harness.process_boundary_verified)
        self.assertTrue(submission.persistence_harness.deterministic_recovery_verified)
        self.assertTrue(submission.replay_recovery_harness.process_boundary_verified)
        self.assertTrue(submission.replay_recovery_harness.deterministic_recovery_verified)

    def test_dual_clean_room_and_portable_evidence_are_ready(self) -> None:
        submission = AuthorizationsOfficeImplementationClosureSupport().build_implementation_closure_submission(REPOSITORY_ROOT)

        self.assertTrue(submission.dual_clean_room.isolated)
        self.assertTrue(submission.dual_clean_room.constitutionally_equivalent)
        self.assertNotEqual(submission.dual_clean_room.run_a_digest, submission.dual_clean_room.run_b_digest)
        self.assertEqual(submission.dual_clean_room.normalized_a_digest, submission.dual_clean_room.normalized_b_digest)
        self.assertEqual(submission.portable_evidence_package.verification_status, AuthorizationImplementationClosureStatus.PASSING)
        self.assertTrue(submission.portable_evidence_package.platform_independent)
        self.assertTrue(submission.portable_evidence_package.self_contained)

    def test_implementation_closure_is_reproducible(self) -> None:
        support = AuthorizationsOfficeImplementationClosureSupport()
        first = support.build_implementation_closure_submission(REPOSITORY_ROOT)
        second = support.build_implementation_closure_submission(REPOSITORY_ROOT)

        self.assertEqual(first.deterministic_digest, second.deterministic_digest)
        self.assertEqual(first.final_verdict, second.final_verdict)


if __name__ == "__main__":
    unittest.main()
