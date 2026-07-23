from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.authorization_independent_certification import (  # noqa: E402
    AuthorizationCertificationDecision,
    AuthorizationVerificationResult,
    AuthorizationsOfficeIndependentCertificationSupport,
)


class AuthorizationsOfficeIndependentCertificationTests(unittest.TestCase):
    def test_auth_rm003_package_covers_all_independent_certification_orders(self) -> None:
        package = AuthorizationsOfficeIndependentCertificationSupport().build_independent_certification_package(REPOSITORY_ROOT)

        self.assertEqual(package.order_coverage, tuple(f"AUTH-RM-003-{index:03d}" for index in range(1, 6)))
        self.assertTrue(package.immutable_candidate.admissible)
        self.assertEqual(package.certification_decision, AuthorizationCertificationDecision.REPRODUCIBLE_FOR_INDEPENDENT_CERTIFICATION)
        self.assertEqual(len(package.verification_rules), 8)
        self.assertEqual(len(package.verification_verdicts), len(package.verification_rules))
        self.assertFalse(package.findings)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_verification_engine_produces_independent_rule_verdicts(self) -> None:
        package = AuthorizationsOfficeIndependentCertificationSupport().build_independent_certification_package(REPOSITORY_ROOT)

        self.assertTrue(all(record.result == AuthorizationVerificationResult.PASS for record in package.verification_verdicts))
        self.assertTrue(all(record.evaluation_hash for record in package.verification_verdicts))
        self.assertTrue(all(record.repository_fingerprint == package.immutable_candidate.repository_fingerprint for record in package.verification_verdicts))
        self.assertTrue(all(record.failure_explanation == "" for record in package.verification_verdicts))

    def test_authentic_operational_state_uses_durable_file_round_trip(self) -> None:
        package = AuthorizationsOfficeIndependentCertificationSupport().build_independent_certification_package(REPOSITORY_ROOT)
        state = package.authentic_state

        self.assertTrue(state.authentic_persistence_verified)
        self.assertTrue(state.recovery_verified)
        self.assertTrue(state.replay_verified)
        self.assertTrue(state.durability_verified)
        self.assertEqual(len(set((state.persisted_object_digest, state.post_termination_digest, state.recovery_digest, state.replay_digest) + state.restart_cycle_digests)), 1)

    def test_repository_traceability_has_zero_orphans(self) -> None:
        package = AuthorizationsOfficeIndependentCertificationSupport().build_independent_certification_package(REPOSITORY_ROOT)

        self.assertGreaterEqual(len(package.repository_traceability), 5)
        self.assertTrue(all(record.orphan_status == "closed" for record in package.repository_traceability))
        self.assertTrue(all(record.downstream_requirements for record in package.repository_traceability))

    def test_reproducibility_repeats_identical_digest(self) -> None:
        support = AuthorizationsOfficeIndependentCertificationSupport()
        first = support.build_independent_certification_package(REPOSITORY_ROOT)
        second = support.build_independent_certification_package(REPOSITORY_ROOT)

        self.assertTrue(first.reproducibility.reproducible)
        self.assertEqual(first.reproducibility.first_execution_digest, first.reproducibility.second_execution_digest)
        self.assertEqual(first.deterministic_digest, second.deterministic_digest)

    def test_missing_candidate_artifacts_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Documentation").mkdir()
            (root / "Documentation" / "AUTH-RM-001-001_TO_013_REMEDIATION_EVIDENCE.md").write_text("evidence\n", encoding="utf-8")
            package = AuthorizationsOfficeIndependentCertificationSupport().build_independent_certification_package(root)

        self.assertFalse(package.immutable_candidate.admissible)
        self.assertEqual(package.certification_decision, AuthorizationCertificationDecision.NOT_REPRODUCIBLE)
        self.assertTrue(package.findings)


if __name__ == "__main__":
    unittest.main()
