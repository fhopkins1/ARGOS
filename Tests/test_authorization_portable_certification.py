from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.authorization_independent_certification import AuthorizationVerificationResult  # noqa: E402
from argos.control_panel.authorization_portable_certification import (  # noqa: E402
    AuthorizationEvidenceLifecycleState,
    AuthorizationPortableStatus,
    AuthorizationsOfficePortableCertificationSupport,
)


class AuthorizationsOfficePortableCertificationTests(unittest.TestCase):
    def test_auth_rm004_package_covers_all_portable_certification_orders(self) -> None:
        package = AuthorizationsOfficePortableCertificationSupport().build_portable_certification_package(REPOSITORY_ROOT)

        self.assertEqual(package.order_coverage, tuple(f"AUTH-RM-004-{index:03d}" for index in range(1, 12)))
        self.assertEqual(package.final_status, AuthorizationPortableStatus.PASSING)
        self.assertTrue(package.candidate_integrity.admissible)
        self.assertFalse(package.findings)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_portable_manifests_are_canonical_and_integrity_checked(self) -> None:
        package = AuthorizationsOfficePortableCertificationSupport().build_portable_certification_package(REPOSITORY_ROOT)
        paths = [record.canonical_relative_path for record in package.candidate_manifest.entries]

        self.assertEqual(paths, sorted(paths))
        self.assertTrue(all(not path.startswith("/") and ":\\" not in path and "\\" not in path for path in paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertTrue(package.candidate_integrity.file_to_manifest_reconciled)
        self.assertTrue(package.candidate_integrity.manifest_to_file_reconciled)
        self.assertTrue(package.candidate_integrity.duplicate_free)
        self.assertTrue(package.candidate_integrity.path_integrity_verified)
        self.assertTrue(package.candidate_integrity.case_collision_free)
        self.assertEqual(package.candidate_manifest.hash_algorithm, "SHA-256")
        self.assertEqual(package.evidence_manifest.hash_algorithm, "SHA-256")

    def test_rule_engine_executes_every_rule_independently(self) -> None:
        package = AuthorizationsOfficePortableCertificationSupport().build_portable_certification_package(REPOSITORY_ROOT)

        self.assertEqual(len(package.rule_executions), len(package.traceability))
        self.assertTrue(all(record.result == AuthorizationVerificationResult.PASS for record in package.rule_executions))
        self.assertTrue(all("EXECUTED" in record.lifecycle for record in package.rule_executions))
        self.assertTrue(all(record.produced_evidence for record in package.rule_executions))

    def test_durable_persistence_and_replay_cross_fresh_process_boundary(self) -> None:
        package = AuthorizationsOfficePortableCertificationSupport().build_portable_certification_package(REPOSITORY_ROOT)

        self.assertTrue(package.durable_persistence.process_boundary_verified)
        self.assertTrue(package.durable_persistence.semantic_equivalence_verified)
        self.assertEqual(package.durable_persistence.committed_digest, package.durable_persistence.fresh_process_digest)
        self.assertTrue(package.replay_recovery.deterministic_replay_verified)
        self.assertTrue(package.replay_recovery.fail_closed_recovery_verified)

    def test_clean_room_runs_are_isolated_and_reproduce_conclusion(self) -> None:
        package = AuthorizationsOfficePortableCertificationSupport().build_portable_certification_package(REPOSITORY_ROOT)

        self.assertEqual(len(package.clean_room_runs), 2)
        self.assertTrue(all(record.status == AuthorizationPortableStatus.PASSING for record in package.clean_room_runs))
        self.assertTrue(all(not record.reused_state_detected for record in package.clean_room_runs))
        self.assertNotEqual(package.clean_room_runs[0].isolated_workspace_fingerprint, package.clean_room_runs[1].isolated_workspace_fingerprint)
        self.assertEqual(package.clean_room_runs[0].candidate_manifest_digest, package.clean_room_runs[1].candidate_manifest_digest)

    def test_evidence_provenance_is_current_execution_and_complete(self) -> None:
        package = AuthorizationsOfficePortableCertificationSupport().build_portable_certification_package(REPOSITORY_ROOT)
        lifecycle = tuple(state.value for state in AuthorizationEvidenceLifecycleState)

        self.assertEqual(len(package.evidence_provenance), len(package.rule_executions))
        self.assertTrue(all(record.lifecycle == lifecycle for record in package.evidence_provenance))
        self.assertTrue(all(record.manifest_digest == package.evidence_manifest.manifest_digest for record in package.evidence_provenance))
        self.assertTrue(all(record.certification_status == AuthorizationPortableStatus.PASSING for record in package.evidence_provenance))


if __name__ == "__main__":
    unittest.main()
