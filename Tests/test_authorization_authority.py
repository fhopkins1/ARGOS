from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.authorization_authority import (  # noqa: E402
    AUTHORIZATION_AUTHORITY_PATH,
    AuthorizationDecisionStatus,
    AuthorizationReadiness,
    AuthorizationsOfficeRemediationSupport,
)


class AuthorizationsOfficeRemediationTests(unittest.TestCase):
    def test_auth_rm001_package_covers_all_remediation_orders(self) -> None:
        package = AuthorizationsOfficeRemediationSupport().build_remediation_package(REPOSITORY_ROOT)

        self.assertEqual(len(package.order_coverage), 13)
        self.assertEqual(package.order_coverage[0], "AUTH-RM-001-001")
        self.assertEqual(package.order_coverage[-1], "AUTH-RM-001-013")
        self.assertTrue(package.candidate.admissible_snapshot)
        self.assertTrue(any(record.canonical_path == AUTHORIZATION_AUTHORITY_PATH for record in package.artifacts))
        self.assertEqual(len(package.requirements), 13)
        self.assertGreaterEqual(len(package.objects), 10)
        self.assertGreaterEqual(len(package.contracts), 4)
        self.assertTrue(package.persistence.replay_equivalent)
        self.assertTrue(package.persistence.recovery_equivalent)
        self.assertEqual(package.readiness_review.readiness, AuthorizationReadiness.READY_FOR_AUTH_RM_002)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_authorization_decision_is_deterministic_and_fail_closed(self) -> None:
        support = AuthorizationsOfficeRemediationSupport()
        first = support.evaluate_authorization_request(
            "REQ-1",
            evidence=("workflow_authority_token", "authorization_policy.v1", "risk_recommendation.v1"),
            authority_valid=True,
        )
        second = support.evaluate_authorization_request(
            "REQ-1",
            evidence=("risk_recommendation.v1", "authorization_policy.v1", "workflow_authority_token"),
            authority_valid=True,
        )
        denied = support.evaluate_authorization_request(
            "REQ-2",
            evidence=("risk_recommendation.v1",),
            authority_valid=False,
        )

        self.assertEqual(first.decision, AuthorizationDecisionStatus.AUTHORIZED)
        self.assertEqual(first.deterministic_digest, second.deterministic_digest)
        self.assertEqual(denied.decision, AuthorizationDecisionStatus.DENIED)
        self.assertIn("authority invalid", denied.denial_reasons)
        self.assertIn("missing evidence: workflow_authority_token", denied.denial_reasons)

    def test_traceability_has_no_orphans_for_canonical_candidate(self) -> None:
        package = AuthorizationsOfficeRemediationSupport().build_remediation_package(REPOSITORY_ROOT)

        self.assertEqual(len(package.traceability), len(package.requirements))
        self.assertTrue(all(record.zero_orphan_status == "closed" for record in package.traceability))
        self.assertTrue(all(record.positive_path_verified and record.negative_path_verified for record in package.operational_evidence))

    def test_missing_canonical_implementation_keeps_readiness_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Documentation").mkdir()
            (root / "Documentation" / "AUTH-RM-001-001_TO_013_REMEDIATION_EVIDENCE.md").write_text("evidence\n", encoding="utf-8")
            package = AuthorizationsOfficeRemediationSupport().build_remediation_package(root)

        self.assertEqual(package.readiness_review.readiness, AuthorizationReadiness.NOT_READY)
        self.assertIn("required Authorizations artifact missing", package.readiness_review.unresolved_findings)

    def test_registry_and_certification_records_are_materialized(self) -> None:
        package = AuthorizationsOfficeRemediationSupport().build_remediation_package(REPOSITORY_ROOT)

        registry_names = {record.registry_name for record in package.registries}
        self.assertIn("Constitutional Rule Registry", registry_names)
        self.assertIn("Certification Registry", registry_names)
        self.assertEqual(package.certification.rule_count, len(package.requirements))
        self.assertEqual(package.certification.test_count, len(package.requirements))
        self.assertFalse(package.certification.findings)


if __name__ == "__main__":
    unittest.main()
