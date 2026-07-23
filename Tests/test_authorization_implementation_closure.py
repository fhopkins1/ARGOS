from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.authorization_implementation_closure import (  # noqa: E402
    AuthorizationImplementationClosureStatus,
    AuthorizationImplementationSubmissionVerdict,
    AuthorizationsOfficeImplementationClosureSupport,
    AuthorizationZipManifestEntry,
    _digest,
    verify_zip_archive,
    write_canonical_zip,
)


class AuthorizationsOfficeImplementationClosureTests(unittest.TestCase):
    def test_auth_ic001_submission_covers_all_implementation_closure_orders(self) -> None:
        submission = AuthorizationsOfficeImplementationClosureSupport().build_implementation_closure_submission(REPOSITORY_ROOT)

        self.assertEqual(submission.order_coverage, tuple(f"AUTH-IC-001-{index:03d}" for index in range(1, 11)))
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

    def test_auth_ic001010_reproduction_closure_is_package_bound_and_identical(self) -> None:
        submission = AuthorizationsOfficeImplementationClosureSupport().build_implementation_closure_submission(REPOSITORY_ROOT)
        closure = submission.reproduction_closure

        self.assertEqual(closure.status, AuthorizationImplementationClosureStatus.PASSING)
        self.assertEqual(closure.candidate_archive.status, AuthorizationImplementationClosureStatus.PASSING)
        self.assertEqual(closure.evidence_archive.status, AuthorizationImplementationClosureStatus.PASSING)
        self.assertEqual(closure.normalized_comparison, "IDENTICAL")
        self.assertTrue(closure.claimed_result_matches_reproduced_result)
        self.assertEqual(closure.unresolved_findings, 0)
        self.assertEqual(closure.unknown_results, 0)
        self.assertEqual(closure.not_executed_results, 0)
        self.assertEqual(len(closure.reproduction_runs), 2)
        self.assertTrue(all(not run.repository_access_detected for run in closure.reproduction_runs))
        self.assertTrue(all(not run.reused_state_detected for run in closure.reproduction_runs))

    def test_archive_verifier_accepts_canonical_zip_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "canonical.zip"
            files = {
                "00_identity/candidate_identity.json": b"{}",
                "01_execution/execution_summary.json": b"{\"status\":\"PASS\"}",
            }
            manifest = write_canonical_zip(zip_path, files)
            result = verify_zip_archive(
                zip_path,
                manifest,
                required_paths=tuple(files),
                declared_package_identifier=_digest(manifest),
            )

        self.assertEqual(result.status, AuthorizationImplementationClosureStatus.PASSING)
        self.assertTrue(result.canonical_paths_verified)
        self.assertTrue(result.hashes_verified)

    def test_archive_verifier_rejects_backslash_absolute_traversal_and_case_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "bad_paths.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("00_identity\\bad.json", b"bad")
                archive.writestr("/absolute.json", b"bad")
                archive.writestr("../traversal.json", b"bad")
                archive.writestr("Case/File.json", b"one")
                archive.writestr("case/file.json", b"two")
            manifest = (
                _manifest_entry("00_identity/bad.json", b"bad"),
                _manifest_entry("absolute.json", b"bad"),
                _manifest_entry("traversal.json", b"bad"),
                _manifest_entry("Case/File.json", b"one"),
                _manifest_entry("case/file.json", b"two"),
            )
            result = verify_zip_archive(
                zip_path,
                manifest,
                required_paths=("00_identity/bad.json",),
                declared_package_identifier=_digest(manifest),
            )

        self.assertEqual(result.status, AuthorizationImplementationClosureStatus.FAILING)
        self.assertFalse(result.canonical_paths_verified)
        self.assertFalse(result.normalized_collisions_absent)
        self.assertTrue(any("nonportable archive path" in finding for finding in result.findings))

    def test_archive_verifier_rejects_missing_undeclared_and_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "bad_manifest.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("declared.json", b"modified")
                archive.writestr("undeclared.json", b"extra")
            manifest = (
                _manifest_entry("declared.json", b"expected"),
                _manifest_entry("missing.json", b"missing"),
            )
            result = verify_zip_archive(
                zip_path,
                manifest,
                required_paths=("declared.json", "missing.json"),
                declared_package_identifier=_digest(manifest),
            )

        self.assertEqual(result.status, AuthorizationImplementationClosureStatus.FAILING)
        self.assertFalse(result.manifest_reconciled)
        self.assertFalse(result.hashes_verified)
        self.assertFalse(result.required_artifacts_present)
        self.assertTrue(any("undeclared archive file" in finding for finding in result.findings))
        self.assertTrue(any("declared archive file missing" in finding for finding in result.findings))
        self.assertTrue(any("archive hash mismatch" in finding for finding in result.findings))


def _manifest_entry(path: str, payload: bytes) -> AuthorizationZipManifestEntry:
    record = AuthorizationZipManifestEntry(
        path=path,
        sha256=__import__("hashlib").sha256(payload).hexdigest(),
        size_bytes=len(payload),
        deterministic_digest="",
    )
    return __import__("dataclasses").replace(record, deterministic_digest=_digest(record))


if __name__ == "__main__":
    unittest.main()
