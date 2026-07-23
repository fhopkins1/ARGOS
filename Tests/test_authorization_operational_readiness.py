from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.authorization_authority import AuthorizationComplianceStatus  # noqa: E402
from argos.control_panel.authorization_operational_readiness import (  # noqa: E402
    AuthorizationCandidateState,
    AuthorizationReadinessDecision,
    AuthorizationTestCategory,
    AuthorizationsOfficeOperationalReadinessSupport,
)


class AuthorizationsOfficeOperationalReadinessTests(unittest.TestCase):
    def test_auth_rm002_package_covers_all_operational_readiness_orders(self) -> None:
        package = AuthorizationsOfficeOperationalReadinessSupport().build_operational_readiness_package(REPOSITORY_ROOT)

        self.assertEqual(package.order_coverage, tuple(f"AUTH-RM-002-{index:03d}" for index in range(1, 7)))
        self.assertEqual(package.candidate_governance.candidate_state, AuthorizationCandidateState.ADMISSIBLE)
        self.assertEqual(package.readiness_decision, AuthorizationReadinessDecision.READY_FOR_INDEPENDENT_CERTIFICATION)
        self.assertEqual(len(package.executable_requirements), 8)
        self.assertFalse(package.findings)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_independent_certification_tests_cover_each_required_category(self) -> None:
        package = AuthorizationsOfficeOperationalReadinessSupport().build_operational_readiness_package(REPOSITORY_ROOT)
        categories = {category for category in AuthorizationTestCategory}

        by_requirement = {}
        for record in package.independent_certification_tests:
            by_requirement.setdefault(record.requirement_identifier, set()).add(record.category)

        self.assertEqual(set(by_requirement), {record.requirement_identifier for record in package.executable_requirements})
        self.assertTrue(all(seen == categories for seen in by_requirement.values()))
        self.assertTrue(all(record.status == AuthorizationComplianceStatus.PASSING for record in package.independent_certification_tests))

    def test_missing_candidate_artifacts_reject_candidate_and_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Documentation").mkdir()
            (root / "Documentation" / "AUTH-RM-001-001_TO_013_REMEDIATION_EVIDENCE.md").write_text("evidence\n", encoding="utf-8")
            package = AuthorizationsOfficeOperationalReadinessSupport().build_operational_readiness_package(root)

        self.assertEqual(package.candidate_governance.candidate_state, AuthorizationCandidateState.REJECTED)
        self.assertEqual(package.readiness_decision, AuthorizationReadinessDecision.NOT_READY)
        self.assertTrue(any(finding.startswith("required candidate artifact missing") for finding in package.findings))

    def test_operational_state_is_semantically_equivalent_after_recovery(self) -> None:
        package = AuthorizationsOfficeOperationalReadinessSupport().build_operational_readiness_package(REPOSITORY_ROOT)
        state = package.operational_state

        self.assertTrue(state.semantic_equivalence_verified)
        self.assertTrue(state.checkpoint_restoration_verified)
        self.assertTrue(state.operational_continuity_verified)
        self.assertEqual(state.uninterrupted_digest, state.interrupted_digest)
        self.assertFalse(state.findings)

    def test_evidence_traceability_has_zero_orphans(self) -> None:
        package = AuthorizationsOfficeOperationalReadinessSupport().build_operational_readiness_package(REPOSITORY_ROOT)

        self.assertEqual(len(package.evidence_traceability), len(package.executable_requirements))
        self.assertTrue(all(record.orphan_status == "closed" for record in package.evidence_traceability))
        self.assertTrue(package.readiness_evidence)


if __name__ == "__main__":
    unittest.main()
