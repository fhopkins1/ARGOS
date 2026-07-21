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
                "SEEK-RM-001-015",
                "SEEK-RM-016",
                "SEEK-RM-017",
                "SEEK-RM-018",
                "SEEK-RM-019",
                "SEEK-RM-020",
                "SEEK-RM-021",
                "SEEK-RM-001-022",
                "SEEK-RM-023",
                "SEEK-RM-024",
                "SEEK-RM-025",
                "SEEK-RM-026",
                "SEEK-RM-027",
                "SEEK-RM-028",
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
        self.assertTrue(package.unsupported_candidate_elimination.package_inclusion_permitted)
        self.assertEqual(package.disposition_handling.disposition, "ACCEPTED")
        self.assertEqual(package.state_idempotency.final_state, SeekerLifecycleState.DORMANT.value)
        self.assertEqual(package.candidate_package_contract.missing_sections, ())
        self.assertEqual(package.candidate_package_contract.outcome_type, "CANDIDATES_DISCOVERED")
        self.assertEqual(package.boundary_commitment.commitment_decision, "COMMIT")
        self.assertTrue(package.boundary_commitment.authority_relinquished)
        self.assertEqual(package.complete_audit_trail.missing_audit_stages, ())
        self.assertEqual(package.persistence_atomic_recovery.recovery_disposition, "RECOVERED_DORMANT")
        self.assertTrue(package.deterministic_replay.semantic_equivalence)
        self.assertFalse(package.deterministic_replay.live_external_dependency_detected)
        self.assertEqual(package.configuration_rule_integrity.missing_rule_versions, ())
        self.assertEqual(package.resource_termination_boundaries.budget_violations, ())
        self.assertEqual(package.dormancy_relinquishment.dormancy_admission, "DORMANT")
        self.assertEqual(package.external_dependency_isolation.unauthorized_runtime_dependencies, ())
        self.assertEqual(package.independent_certification_suite.evidence_coverage, "100%")
        self.assertEqual(package.certification_closure.final_verdict, EnterpriseCertificationDecision.PASS)
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

    def test_unsupported_candidate_elimination_and_disposition_preserve_rejection_evidence(self) -> None:
        support = SeekerOfficeIntegritySupport()
        identity = support.evaluate_candidate_identity(
            candidate(attributes={"ticker": "ARG", "exchange": "", "security_identifier": "000000001"}),
            search_plan(),
            (discovery_evidence(),),
        )
        preservation = support.evaluate_discovery_evidence_preservation(mission(), search_plan(), (discovery_evidence(),), candidate())
        freshness = support.evaluate_freshness_determination(mission(), search_plan(), candidate(), (discovery_evidence(),))
        duplicates = support.evaluate_duplicate_suppression(search_plan(), (candidate(),), (discovery_evidence(),))
        independence = support.evaluate_relationship_independence(search_plan(), (candidate(),), (discovery_evidence(),))
        sufficiency = support.evaluate_search_sufficiency(search_plan(), (discovery_evidence(),), (candidate(),))

        elimination = support.evaluate_unsupported_candidate_elimination(
            candidate(),
            (identity, preservation, freshness, duplicates, independence, sufficiency),
        )
        disposition = support.evaluate_disposition_handling(candidate(), elimination)

        self.assertEqual(elimination.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("identity_validation", elimination.failed_support_requirements)
        self.assertFalse(elimination.package_inclusion_permitted)
        self.assertEqual(disposition.disposition, "REJECTED")
        self.assertFalse(disposition.silent_disposition_detected)
        self.assertTrue(disposition.package_protected)

    def test_candidate_package_contract_blocks_analytical_content_and_missing_decisions(self) -> None:
        support = SeekerOfficeIntegritySupport()
        bad_candidate = candidate(attributes={**candidate().attributes, "recommendation": "buy"})
        identity = support.evaluate_candidate_identity(candidate(), search_plan(), (discovery_evidence(),))
        preservation = support.evaluate_discovery_evidence_preservation(mission(), search_plan(), (discovery_evidence(),), candidate())

        record = support.evaluate_candidate_package_contract(
            mission(),
            search_plan(),
            (bad_candidate,),
            (discovery_evidence(),),
            (identity, preservation),
        )

        self.assertEqual(record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("decision_manifest", record.missing_sections)
        self.assertEqual(record.prohibited_content_findings, ("CAND-001.recommendation",))

    def test_boundary_commitment_rejects_duplicate_or_invalid_package(self) -> None:
        support = SeekerOfficeIntegritySupport()
        package = support.build_package(
            mission=mission(),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )

        duplicate = support.evaluate_boundary_commitment(
            package.candidate_package_contract,
            package.state_idempotency,
            prior_commitments=(package.candidate_package_contract.package_identifier,),
        )

        self.assertEqual(duplicate.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(duplicate.commitment_decision, "REJECT")
        self.assertIn("duplicate_commitment", duplicate.eligibility_failures)
        self.assertFalse(duplicate.committed_once)

    def test_audit_trail_and_persistence_fail_closed_when_evidence_or_state_is_incomplete(self) -> None:
        support = SeekerOfficeIntegritySupport()
        package = support.build_package(
            mission=mission(),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )
        incomplete_audit = support.evaluate_complete_audit_trail(package.immutable_audit_references[:3])
        incomplete_recovery = support.evaluate_persistence_atomic_recovery(
            (mission().mission_id, "", candidate().candidate_reference),
            package.candidate_package_contract,
            package.boundary_commitment,
        )

        self.assertEqual(incomplete_audit.result, EnterpriseCertificationDecision.FAIL)
        self.assertNotEqual(incomplete_audit.missing_audit_stages, ())
        self.assertEqual(incomplete_recovery.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("search_plan_committed", incomplete_recovery.partial_write_findings)

    def test_replay_configuration_resource_dormancy_dependency_and_closure_records_fail_closed(self) -> None:
        support = SeekerOfficeIntegritySupport()
        good_package = support.build_package(
            mission=mission(),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )
        config = support.evaluate_configuration_rule_integrity(
            mission(search_plan_id="SEARCH-PLAN-OTHER"),
            search_plan(),
        )
        resources = support.evaluate_resource_termination_boundaries(
            mission(),
            search_plan(execution_limits={"max_queries": 0, "max_candidates": 1}),
            (discovery_evidence(),),
            good_package.boundary_commitment,
        )
        dormancy = support.evaluate_dormancy_relinquishment(
            good_package.lifecycle_state_machine,
            good_package.boundary_commitment,
            good_package.resource_termination_boundaries,
            residual_override={"retry_queue": "ACTIVE"},
        )
        dependencies = support.evaluate_external_dependency_isolation(
            mission(),
            search_plan(),
            unauthorized_dependencies=("Analyst", "enterprise_scheduler", "seeker_bridge"),
        )
        failed_suite = support.evaluate_independent_certification_suite((EnterpriseCertificationDecision.PASS, EnterpriseCertificationDecision.FAIL))
        closure = support.evaluate_certification_closure(failed_suite, ())

        self.assertEqual(config.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("mission_search_plan_mismatch", config.incompatible_rule_versions)
        self.assertEqual(resources.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("max_queries", resources.budget_violations)
        self.assertEqual(dormancy.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("retry_queue", dormancy.unauthorized_residual_state)
        self.assertEqual(dependencies.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Analyst", dependencies.external_office_dependencies)
        self.assertIn("enterprise_scheduler", dependencies.enterprise_infrastructure_dependencies)
        self.assertIn("seeker_bridge", dependencies.bridge_dependencies)
        self.assertEqual(failed_suite.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(closure.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("independent_suite_failed", closure.unresolved_deficiencies)
        self.assertIn("missing_closure_evidence", closure.unresolved_deficiencies)


if __name__ == "__main__":
    unittest.main()
