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
            (
                "SEEK-RM-001-001",
                "SEEK-RM-002",
                "SEEK-RM-003",
                "SEEK-RM-004",
                "SEEK-RM-005",
                "SEEK-RM-006",
                "SEEK-RM-007",
                "SEEK-RM-001-008",
                "SEEK-RM-009",
                "SEEK-RM-010",
                "SEEK-RM-011",
                "SEEK-RM-012",
                "SEEK-RM-013",
                "SEEK-RM-014",
            ),
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
        self.assertEqual(package.discovery_evidence_preservation.missing_categories, ())
        self.assertTrue(package.discovery_evidence_preservation.provenance_complete)
        self.assertEqual(package.discovery_normalization.prohibited_transformations, ())
        self.assertTrue(package.discovery_normalization.semantic_preservation)
        self.assertEqual(package.chronology_integrity.ordering_violations, ())
        self.assertTrue(package.chronology_integrity.internal_external_time_separated)
        self.assertEqual(package.freshness_determination.freshness_decision, "FRESH")
        self.assertEqual(package.duplicate_suppression.suppressed_duplicates, ())
        self.assertEqual(package.relationship_independence.independence_decision, "VALID")
        self.assertEqual(package.search_sufficiency.sufficiency_decision, "SUFFICIENT")
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

    def test_discovery_evidence_preservation_rejects_missing_provenance_or_prohibited_content(self) -> None:
        bad_evidence = discovery_evidence(evidence_id="DISC-EVID-UNLINKED", payload={"ticker": "ARG", "recommendation": "buy"})
        record = SeekerOfficeIntegritySupport().evaluate_discovery_evidence_preservation(
            mission(),
            search_plan(),
            (bad_evidence,),
            candidate(),
        )

        self.assertEqual(record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("candidate_package_evidence", record.missing_categories)
        self.assertEqual(record.prohibited_content_findings, ("DISC-EVID-UNLINKED.recommendation",))

    def test_normalization_and_chronology_fail_closed_on_missing_fields_or_reversed_time(self) -> None:
        support = SeekerOfficeIntegritySupport()
        sparse = discovery_evidence(payload={"ticker": " arg "})
        reversed_time = discovery_evidence(retrieved_at="2026-07-20T10:01:00Z")

        normalization = support.evaluate_discovery_normalization((sparse,), candidate())
        chronology = support.evaluate_chronology_integrity(mission(), search_plan(), (reversed_time,))

        self.assertEqual(normalization.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("DISC-EVID-001.missing_exchange", normalization.prohibited_transformations)
        self.assertEqual(chronology.result, EnterpriseCertificationDecision.FAIL)
        self.assertNotEqual(chronology.ordering_violations, ())

    def test_freshness_rejects_stale_missing_or_future_timestamps(self) -> None:
        support = SeekerOfficeIntegritySupport()
        stale = support.evaluate_freshness_determination(
            mission(),
            search_plan(),
            candidate(),
            (discovery_evidence(source_timestamp="2026-05-01T09:55:00Z"),),
        )
        missing = support.evaluate_freshness_determination(
            mission(),
            search_plan(),
            candidate(),
            (discovery_evidence(source_timestamp=""),),
        )
        future = support.evaluate_freshness_determination(
            mission(),
            search_plan(),
            candidate(),
            (discovery_evidence(source_timestamp="2026-07-22T09:55:00Z"),),
        )

        self.assertEqual(stale.freshness_decision, "STALE")
        self.assertEqual(stale.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(missing.freshness_decision, "TIME_MISSING")
        self.assertEqual(future.freshness_decision, "FUTURE_TIMESTAMP_INVALID")

    def test_duplicate_relationship_and_sufficiency_records_fail_closed_on_invalid_inputs(self) -> None:
        support = SeekerOfficeIntegritySupport()
        duplicate = candidate(candidate_reference="CAND-002")
        duplicates = support.evaluate_duplicate_suppression(search_plan(), (candidate(), duplicate), (discovery_evidence(),))
        relationship = support.evaluate_relationship_independence(
            search_plan(),
            (candidate(attributes={**candidate().attributes, "relationship": "Speculative Link"}),),
            (discovery_evidence(),),
        )
        insufficient = support.evaluate_search_sufficiency(
            search_plan(approved_sources=("SEC-EDGAR", "ISSUER-IR")),
            (discovery_evidence(),),
            (candidate(),),
        )

        self.assertEqual(duplicates.result, EnterpriseCertificationDecision.PASS)
        self.assertEqual(duplicates.suppressed_duplicates, ("CAND-002",))
        self.assertEqual(relationship.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(relationship.unsupported_relationships, ("CAND-001:Speculative Link",))
        self.assertEqual(insufficient.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(insufficient.missing_required_sources, ("ISSUER-IR",))


if __name__ == "__main__":
    unittest.main()
