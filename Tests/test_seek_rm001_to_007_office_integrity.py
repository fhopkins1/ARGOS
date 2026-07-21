from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.seeker import (  # noqa: E402
    SeekerApprovedSearchPlan,
    SeekerCandidateIdentityInput,
    SeekerDiscoveryEvidence,
    SeekerLifecycleState,
    SeekerOfficeIntegritySupport,
    SeekerSearchMission,
)


def mission(**overrides) -> SeekerSearchMission:
    data = {
        "mission_id": "SEARCH-MISSION-001",
        "mission_version": "1",
        "objective_id": "SEARCH-OBJECTIVE-001",
        "constitutional_authority": "Commander",
        "search_plan_id": "SEARCH-PLAN-001",
        "execution_parameters": {"max_results": "5", "mode": "deterministic"},
        "rule_versions": {
            "objective": "SEEK-RM-006/1",
            "candidate_identity": "SEEK-RM-007/1",
            "lifecycle": "SEEK-RM-004/1",
        },
        "discovery_scope": ("candidate_discovery",),
        "mission_creation_timestamp": "2026-07-21T10:00:00Z",
    }
    data.update(overrides)
    return SeekerSearchMission(**data)


def search_plan(**overrides) -> SeekerApprovedSearchPlan:
    data = {
        "search_plan_id": "SEARCH-PLAN-001",
        "search_plan_version": "1",
        "approval_status": "APPROVED",
        "approval_authority": "Commander",
        "search_objective": "Discover equity candidate from approved filing evidence",
        "permitted_domains": ("candidate_discovery",),
        "approved_sources": ("SEC-EDGAR",),
        "approved_methods": ("official_filing_retrieval",),
        "candidate_inclusion_rules": ("issuer_has_current_filing",),
        "candidate_exclusion_rules": ("unsupported_identity",),
        "identity_requirements": ("ticker", "exchange", "security_identifier"),
        "freshness_requirements": ("source_timestamp_within_30d",),
        "duplicate_rules": ("canonical_identity_digest",),
        "independence_requirements": ("official_source_required",),
        "sufficiency_requirements": ("mandatory_source_attempted",),
        "termination_conditions": ("mandatory_sources_complete",),
        "execution_limits": {"max_queries": 1, "max_candidates": 5},
    }
    data.update(overrides)
    return SeekerApprovedSearchPlan(**data)


def discovery_evidence(**overrides) -> SeekerDiscoveryEvidence:
    data = {
        "evidence_id": "DISC-EVID-001",
        "source_id": "SEC-EDGAR",
        "acquisition_method": "official_filing_retrieval",
        "search_activity_id": "SEARCH-ACTIVITY-001",
        "payload": {
            "ticker": "ARG",
            "exchange": "NYSE",
            "security_identifier": "000000001",
            "issuer_name": "Argos Test Issuer",
        },
        "retrieved_at": "2026-07-21T10:01:00Z",
        "source_timestamp": "2026-07-21T09:55:00Z",
    }
    data.update(overrides)
    return SeekerDiscoveryEvidence(**data)


def candidate(**overrides) -> SeekerCandidateIdentityInput:
    data = {
        "candidate_reference": "CAND-001",
        "candidate_type": "equity",
        "evidence_references": ("DISC-EVID-001",),
        "attributes": {
            "ticker": "ARG",
            "exchange": "NYSE",
            "security_identifier": "000000001",
            "issuer_name": "Argos Test Issuer",
        },
    }
    data.update(overrides)
    return SeekerCandidateIdentityInput(**data)


class SeekRm001To007OfficeIntegrityTests(unittest.TestCase):
    def test_seeker_integrity_package_covers_first_seven_remediation_orders(self) -> None:
        package = SeekerOfficeIntegritySupport().build_package(
            mission=mission(),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )

        self.assertEqual(package.final_office_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            ("SEEK-RM-001-001", "SEEK-RM-002", "SEEK-RM-003", "SEEK-RM-004", "SEEK-RM-005", "SEEK-RM-006", "SEEK-RM-007"),
        )
        self.assertIn("Mission Intake Component", package.boundary_registry.registered_components)
        self.assertIn("Lifecycle Component", package.boundary_registry.registered_components)
        self.assertEqual(package.boundary_registry.duplicate_owners, ())
        self.assertEqual(package.self_certification_separation.detected_self_certification_paths, ())
        self.assertFalse(package.self_certification_separation.seeker_controls_certification_verdict)
        self.assertEqual(package.mission_intake.activation_decision, "ACCEPT")
        self.assertEqual(package.lifecycle_state_machine.terminal_state, SeekerLifecycleState.DORMANT.value)
        self.assertEqual(package.search_plan_enforcement.unauthorized_sources, ())
        self.assertEqual(package.search_plan_enforcement.unauthorized_methods, ())
        self.assertTrue(package.search_plan_enforcement.candidate_traceability_complete)
        self.assertEqual(package.objective_validation.validation_decision, "VALID")
        self.assertEqual(package.candidate_identity_validation.validation_decision, "VALID")
        self.assertTrue(package.candidate_identity_validation.identity_immutable)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_self_certification_metadata_is_detected_and_fails_closed(self) -> None:
        record = SeekerOfficeIntegritySupport().evaluate_self_certification_separation(
            {"candidate_package": {"certification_result": "PASS", "operational_state": "completed"}}
        )

        self.assertEqual(record.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(record.detected_self_certification_paths, ("candidate_package.certification_result",))
        self.assertFalse(record.operational_decisions_only)

    def test_unauthorized_or_duplicate_mission_cannot_activate_seeker(self) -> None:
        support = SeekerOfficeIntegritySupport()
        unauthorized = support.evaluate_mission_intake(
            mission(constitutional_authority="Testing Utility"),
            search_plan(),
        )
        duplicate = support.evaluate_mission_intake(
            mission(),
            search_plan(),
            active_missions=("SEARCH-MISSION-001",),
        )

        self.assertEqual(unauthorized.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(unauthorized.activation_decision, "REJECT")
        self.assertEqual(unauthorized.rejected_authority, ("Testing Utility",))
        self.assertEqual(duplicate.result, EnterpriseCertificationDecision.FAIL)
        self.assertTrue(duplicate.duplicate_mission_detected)
        self.assertEqual(duplicate.final_state, SeekerLifecycleState.DORMANT.value)

    def test_lifecycle_rejects_bypass_and_residual_authority(self) -> None:
        bad_sequence = (
            SeekerLifecycleState.DORMANT.value,
            SeekerLifecycleState.MISSION_RECEIVED.value,
            SeekerLifecycleState.DISCOVERY_EXECUTING.value,
        )

        record = SeekerOfficeIntegritySupport().evaluate_lifecycle_state_machine(bad_sequence)

        self.assertEqual(record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("MISSION_RECEIVED->DISCOVERY_EXECUTING", record.invalid_transitions)
        self.assertIn("mission_authority_not_relinquished", record.residual_authority)
        self.assertIn(SeekerLifecycleState.SEARCH_PLAN_VALIDATING.value, record.bypass_findings)

    def test_search_plan_enforcement_rejects_unauthorized_source_method_and_scope(self) -> None:
        support = SeekerOfficeIntegritySupport()
        bad_plan = search_plan(permitted_domains=("candidate_discovery", "risk_assessment"))
        bad_evidence = discovery_evidence(source_id="UNAPPROVED-SOURCE", acquisition_method="web_scrape")

        record = support.evaluate_search_plan_enforcement(bad_plan, (bad_evidence,), candidate())

        self.assertEqual(record.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(record.unauthorized_sources, ("UNAPPROVED-SOURCE",))
        self.assertEqual(record.unauthorized_methods, ("web_scrape",))
        self.assertEqual(record.scope_violations, ("risk_assessment",))

    def test_objective_validation_rejects_ambiguous_or_downstream_objective(self) -> None:
        record = SeekerOfficeIntegritySupport().evaluate_objective_validation(
            mission(),
            search_plan(search_objective="Find the best candidate and recommend trade"),
        )

        self.assertEqual(record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("best", record.ambiguity_findings)
        self.assertIn("trade_authorization", record.prohibited_responsibilities)
        self.assertIn("investment_recommendation", record.prohibited_responsibilities)

    def test_candidate_identity_validation_rejects_missing_conflicting_or_unsupported_identity(self) -> None:
        record = SeekerOfficeIntegritySupport().evaluate_candidate_identity(
            candidate(
                attributes={
                    "ticker": "ARG|ARGX",
                    "exchange": "",
                    "security_identifier": "000000001",
                    "synthetic_identifier": "invented",
                }
            ),
            search_plan(),
            (discovery_evidence(),),
        )

        self.assertEqual(record.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(record.validation_decision, "INVALID")
        self.assertIn("exchange", record.missing_identity_fields)
        self.assertIn("ticker", record.conflicting_identity_fields)
        self.assertIn("synthetic_identifier", record.unsupported_identity_fields)
        self.assertEqual(record.canonical_identity, "")


if __name__ == "__main__":
    unittest.main()
