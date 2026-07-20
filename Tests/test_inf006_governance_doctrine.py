from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.infrastructure import (  # noqa: E402
    AmendmentRecord,
    AuthorityAction,
    AuthorityTier,
    CertificationFreshnessRecord,
    ConstitutionalInput,
    FailureEvent,
    FailureResponseClass,
    FreezeChangeClass,
    FreezeChangeRequest,
    GovernanceDecision,
    GovernanceFailure,
    InfrastructureGovernanceDoctrine,
    RegressionAssessment,
    RegressionScope,
)


class INF006GovernanceDoctrineTests(unittest.TestCase):
    def test_certification_freshness_is_state_based_not_date_based(self) -> None:
        doctrine = InfrastructureGovernanceDoctrine()

        fresh = doctrine.certification_freshness(CertificationFreshnessRecord("CERT-1", "sha256:state", "sha256:state", ()))
        stale = doctrine.certification_freshness(
            CertificationFreshnessRecord("CERT-1", "sha256:state", "sha256:changed", (ConstitutionalInput.BRIDGE,))
        )

        self.assertEqual(fresh.decision, GovernanceDecision.APPROVED)
        self.assertEqual(stale.decision, GovernanceDecision.REJECTED_FAIL_CLOSED)
        self.assertIn(GovernanceFailure.STALE_CERTIFICATION, stale.failures)

    def test_unknown_failure_classification_halts_fail_closed(self) -> None:
        response, review = InfrastructureGovernanceDoctrine().failure_response(FailureEvent("FAIL-1", None, "sha256:fail"))

        self.assertEqual(response, FailureResponseClass.HALT)
        self.assertEqual(review.decision, GovernanceDecision.REJECTED_FAIL_CLOSED)
        self.assertIn(GovernanceFailure.UNKNOWN_FAILURE_CLASSIFICATION, review.failures)

    def test_authority_hierarchy_prevents_runtime_monitoring_or_reporting_override(self) -> None:
        doctrine = InfrastructureGovernanceDoctrine()

        valid = doctrine.authority_action(AuthorityAction(AuthorityTier.CONSTITUTION, AuthorityTier.RUNTIME, "constrain runtime"))
        invalid = doctrine.authority_action(
            AuthorityAction(AuthorityTier.REPORTING, AuthorityTier.CERTIFIED_INFRASTRUCTURE, "declare infrastructure truth")
        )

        self.assertEqual(valid.decision, GovernanceDecision.APPROVED)
        self.assertEqual(invalid.decision, GovernanceDecision.REJECTED_FAIL_CLOSED)
        self.assertIn(GovernanceFailure.INVALID_AUTHORITY_OVERRIDE, invalid.failures)

    def test_freeze_requires_behavioral_equivalence_or_amendment_authority(self) -> None:
        doctrine = InfrastructureGovernanceDoctrine()

        refactor = doctrine.freeze_change(FreezeChangeRequest("CHG-1", FreezeChangeClass.IMPLEMENTATION, "sha256:equivalence"))
        behavior_change = doctrine.freeze_change(FreezeChangeRequest("CHG-2", FreezeChangeClass.BEHAVIOR, ""))

        self.assertEqual(refactor.decision, GovernanceDecision.APPROVED)
        self.assertIn(GovernanceFailure.MISSING_EQUIVALENCE_EVIDENCE, behavior_change.failures)
        self.assertIn(GovernanceFailure.BEHAVIOR_CHANGE_DURING_FREEZE, behavior_change.failures)

    def test_regression_scope_uses_smallest_safe_scope_and_expands_on_uncertainty(self) -> None:
        doctrine = InfrastructureGovernanceDoctrine()

        required, review = doctrine.regression_scope(
            RegressionAssessment((ConstitutionalInput.CONFIGURATION,), RegressionScope.INFRASTRUCTURE, False)
        )
        uncertain_required, uncertain_review = doctrine.regression_scope(
            RegressionAssessment((ConstitutionalInput.CONFIGURATION,), RegressionScope.INFRASTRUCTURE, True)
        )

        self.assertEqual(required, RegressionScope.INFRASTRUCTURE)
        self.assertEqual(review.decision, GovernanceDecision.APPROVED)
        self.assertEqual(uncertain_required, RegressionScope.ENTERPRISE)
        self.assertIn(GovernanceFailure.UNDER_SCOPED_REGRESSION, uncertain_review.failures)

    def test_amendment_separates_governance_from_implementation_and_requires_recertification(self) -> None:
        doctrine = InfrastructureGovernanceDoctrine()

        approved = doctrine.amendment(
            AmendmentRecord(
                amendment_id="AMD-1",
                governance_authority="Constitutional Committee",
                rationale="Clarify infrastructure governance",
                history_reference="sha256:history",
                affected_doctrine=("INF-006",),
                affected_guarantees=("fail_closed",),
                mandatory_recertification_scope=RegressionScope.INFRASTRUCTURE,
            )
        )
        rejected = doctrine.amendment(
            AmendmentRecord(
                amendment_id="AMD-2",
                governance_authority="",
                rationale="",
                history_reference="",
                affected_doctrine=("INF-006",),
                affected_guarantees=("fail_closed",),
                mandatory_recertification_scope=None,
                implementation_changes_governance=True,
            )
        )

        self.assertEqual(approved.decision, GovernanceDecision.APPROVED)
        self.assertIn(GovernanceFailure.AMENDMENT_WITHOUT_AUTHORITY, rejected.failures)
        self.assertIn(GovernanceFailure.IMPLEMENTATION_REDEFINED_GOVERNANCE, rejected.failures)
        self.assertIn(GovernanceFailure.MISSING_RECERTIFICATION_REQUIREMENT, rejected.failures)


if __name__ == "__main__":
    unittest.main()
