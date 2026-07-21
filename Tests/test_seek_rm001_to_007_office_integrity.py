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

    def test_seek_rm002_constitutional_object_package_passes_with_complete_inputs(self) -> None:
        package = SeekerOfficeIntegritySupport().build_constitutional_objects_package(
            mission=mission(rule_versions={**mission().rule_versions, "authorization": "AUTH/1", "discovery": "DISCOVERY/1", "configuration": "CONFIG/1"}),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )

        self.assertEqual(package.final_object_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            (
                "SEEK-RM-002-001",
                "SEEK-RM-002-002",
                "SEEK-RM-002-003",
                "SEEK-RM-002-004",
                "SEEK-RM-002-005",
                "SEEK-RM-002-006",
                "SEEK-RM-002-007",
            ),
        )
        self.assertEqual(package.search_mission_object.missing_fields, ())
        self.assertEqual(package.search_plan_object.missing_sections, ())
        self.assertEqual(package.candidate_package_object.invariant_violations, ())
        self.assertEqual(package.candidate_identity_doctrine.confidence_status, "VERIFIED")
        self.assertEqual(package.candidate_lifecycle.terminal_outcome, "Accepted and Committed")
        self.assertEqual(package.search_mission_lifecycle.terminal_state, "Completed")
        self.assertEqual(package.search_sufficiency_metrics.sufficiency_outcome, "SUFFICIENT")
        self.assertNotEqual(package.deterministic_digest, "")

    def test_seek_rm002_constitutional_objects_fail_closed_on_invalid_inputs(self) -> None:
        support = SeekerOfficeIntegritySupport()
        bad_mission = mission(
            constitutional_authority="",
            search_plan_id="SEARCH-PLAN-OTHER",
            discovery_scope=("candidate_discovery", "trade_authorization"),
        )
        bad_plan = search_plan(
            approved_sources=("SEC-EDGAR", "NASDAQ"),
            sufficiency_requirements=(),
            termination_conditions=(),
        )
        bad_candidate = candidate(attributes={"ticker": "ARG|AMBIGUOUS", "exchange": "NYSE"})
        bad_evidence = (discovery_evidence(source_id="SEC-EDGAR"),)

        mission_object = support.evaluate_search_mission_constitutional_object(bad_mission, bad_plan)
        plan_object = support.evaluate_search_plan_constitutional_object(bad_mission, bad_plan, bad_evidence, (bad_candidate,))
        identity = support.evaluate_candidate_identity(bad_candidate, bad_plan, bad_evidence)
        freshness = support.evaluate_freshness_determination(mission(), bad_plan, bad_candidate, bad_evidence)
        duplicates = support.evaluate_duplicate_suppression(bad_plan, (bad_candidate,), bad_evidence)
        independence = support.evaluate_relationship_independence(bad_plan, (bad_candidate,), bad_evidence)
        sufficiency = support.evaluate_search_sufficiency(bad_plan, bad_evidence, (bad_candidate,))
        preservation = support.evaluate_discovery_evidence_preservation(mission(), bad_plan, bad_evidence, bad_candidate)
        contract = support.evaluate_candidate_package_contract(
            mission(),
            bad_plan,
            (bad_candidate, candidate(candidate_reference="CAND-002")),
            bad_evidence,
            (identity, preservation, freshness, duplicates, independence, sufficiency),
        )
        candidate_package = support.evaluate_candidate_package_constitutional_object(
            mission(),
            bad_plan,
            (bad_candidate, candidate(candidate_reference="CAND-002")),
            bad_evidence,
            contract,
            (identity, preservation, freshness, duplicates, independence, sufficiency),
        )
        identity_doctrine = support.evaluate_enterprise_candidate_identity_doctrine(bad_candidate, bad_plan, bad_evidence)
        candidate_lifecycle = support.evaluate_candidate_constitutional_lifecycle(
            bad_candidate,
            identity,
            duplicates,
            freshness,
            independence,
            sufficiency,
            contract,
        )
        mission_lifecycle = support.evaluate_search_mission_constitutional_lifecycle(mission(), contract, sufficiency)
        sufficiency_metrics = support.evaluate_search_sufficiency_metrics(
            mission(),
            bad_plan,
            bad_evidence,
            (bad_candidate,),
            sufficiency,
            freshness,
            duplicates,
            independence,
            contract,
        )

        self.assertEqual(mission_object.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("authorization_identifier", mission_object.missing_fields)
        self.assertIn("trade_authorization", mission_object.prohibited_authority_findings)
        self.assertEqual(plan_object.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("mission_reference", plan_object.missing_sections)
        self.assertIn("completion_criteria", plan_object.missing_sections)
        self.assertEqual(candidate_package.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("single_candidate_invariant", candidate_package.invariant_violations)
        self.assertEqual(identity_doctrine.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(identity_doctrine.confidence_status, "REJECTED")
        self.assertEqual(candidate_lifecycle.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(mission_lifecycle.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(sufficiency_metrics.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(sufficiency_metrics.sufficiency_outcome, "INSUFFICIENT")

    def test_seek_rm002_doctrine_package_passes_with_complete_inputs(self) -> None:
        package = SeekerOfficeIntegritySupport().build_constitutional_doctrine_package(
            mission=mission(),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidates=(candidate(),),
        )

        self.assertEqual(package.final_doctrine_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            (
                "SEEK-RM-002-008",
                "SEEK-RM-002-009",
                "SEEK-RM-002-010",
                "SEEK-RM-002-011",
                "SEEK-RM-002-012",
                "SEEK-RM-002-013",
                "SEEK-RM-002-014",
            ),
        )
        self.assertEqual(package.candidate_equivalence_duplicate_doctrine.indeterminate_identity_findings, ())
        self.assertEqual(package.candidate_freshness_policy.freshness_state, "Fresh")
        self.assertEqual(package.candidate_independence_doctrine.independence_decision, "Independent")
        self.assertEqual(package.candidate_rejection_taxonomy.final_disposition, "ADMITTED")
        self.assertEqual(package.discovery_evidence_schema.inadmissible_evidence, ())
        self.assertEqual(package.discovery_provenance_architecture.missing_chain_stages, ())
        self.assertEqual(package.constitutional_state_machine.unauthorized_transitions, ())
        self.assertNotEqual(package.deterministic_digest, "")

    def test_seek_rm002_doctrine_records_fail_closed_on_defects(self) -> None:
        support = SeekerOfficeIntegritySupport()
        duplicate_candidate = candidate(candidate_reference="CAND-002")
        candidates = (candidate(), duplicate_candidate)
        stale_evidence = discovery_evidence(
            evidence_id="DISC-EVID-STALE",
            retrieved_at="2026-07-21T10:01:00Z",
            source_timestamp="2026-01-01T09:55:00Z",
        )
        unauthorized_evidence = discovery_evidence(
            evidence_id="DISC-EVID-BAD",
            source_id="UNAPPROVED-SOURCE",
            acquisition_method="manual_guess",
        )
        plan = search_plan(approved_sources=("SEC-EDGAR", "NASDAQ"))
        duplicates = support.evaluate_duplicate_suppression(search_plan(), candidates, (discovery_evidence(),))
        equivalence = support.evaluate_candidate_equivalence_duplicate_doctrine(search_plan(), candidates, (discovery_evidence(),), duplicates)
        freshness = support.evaluate_freshness_determination(mission(), search_plan(), candidate(evidence_references=("DISC-EVID-STALE",)), (stale_evidence,))
        freshness_policy = support.evaluate_candidate_freshness_policy(mission(), candidate(evidence_references=("DISC-EVID-STALE",)), (stale_evidence,), freshness)
        independence = support.evaluate_relationship_independence(search_plan(), (candidate(),), ())
        independence_doctrine = support.evaluate_candidate_independence_doctrine(search_plan(), candidate(), (), independence)
        identity = support.evaluate_candidate_identity(candidate(attributes={"ticker": "ARG|AMBIGUOUS", "exchange": "NYSE"}), search_plan(), (discovery_evidence(),))
        rejection = support.evaluate_candidate_rejection_taxonomy(mission(), candidate(attributes={"ticker": "ARG|AMBIGUOUS", "exchange": "NYSE"}), (identity,))
        evidence_schema = support.evaluate_discovery_evidence_constitutional_schema(mission(), plan, (unauthorized_evidence,), candidate(evidence_references=("DISC-EVID-BAD",)))
        package_contract = support.evaluate_candidate_package_contract(mission(), plan, (candidate(),), (unauthorized_evidence,), (identity,))
        provenance = support.evaluate_discovery_provenance_architecture(mission(), plan, (unauthorized_evidence,), candidate(evidence_references=("DISC-EVID-BAD",)), package_contract)
        state_machine = support.evaluate_constitutional_state_machine_doctrine(("Dormant", "Discovery Execution", "Completed"))

        self.assertEqual(equivalence.result, EnterpriseCertificationDecision.PASS)
        self.assertIn("CAND-002", duplicates.suppressed_duplicates)
        self.assertEqual(freshness_policy.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(freshness_policy.freshness_state, "Expired")
        self.assertEqual(independence_doctrine.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("comparison_evidence", independence_doctrine.missing_requirements)
        self.assertEqual(rejection.result, EnterpriseCertificationDecision.PASS)
        self.assertEqual(rejection.final_disposition, "REJECTED")
        self.assertEqual(rejection.primary_rejection_code, "IDENTITY_AMBIGUOUS")
        self.assertEqual(evidence_schema.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("DISC-EVID-BAD:source_not_approved", evidence_schema.inadmissible_evidence)
        self.assertEqual(provenance.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Outbound Commitment", provenance.missing_chain_stages)
        self.assertEqual(state_machine.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Dormant->Discovery Execution", state_machine.unauthorized_transitions)

    def test_seek_rm002_certification_support_package_passes_with_complete_inputs(self) -> None:
        package = SeekerOfficeIntegritySupport().build_certification_support_package(
            mission=mission(rule_versions={**mission().rule_versions, "authorization": "AUTH/1", "discovery": "DISCOVERY/1", "configuration": "CONFIG/1"}),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )

        self.assertEqual(package.final_support_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            (
                "SEEK-RM-002-015",
                "SEEK-RM-002-016",
                "SEEK-RM-002-017",
                "SEEK-RM-002-018",
                "SEEK-RM-002-019",
                "SEEK-RM-002-020",
                "SEEK-RM-002-021",
                "SEEK-RM-002-022",
            ),
        )
        self.assertEqual(package.office_owned_persistent_state.unclassified_state, ())
        self.assertEqual(package.recovery_checkpoint_architecture.invalid_checkpoints, ())
        self.assertEqual(package.constitutional_commit_boundaries.missing_boundaries, ())
        self.assertTrue(package.replay_semantic_equivalence.semantic_equivalence)
        self.assertEqual(package.constitutional_configuration_object.missing_configuration_fields, ())
        self.assertEqual(package.constitutional_error_taxonomy.unclassified_errors, ())
        self.assertEqual(package.certification_traceability_architecture.orphan_findings, ())
        self.assertTrue(package.certification_evidence_package.supports_independent_pass)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_seek_rm002_certification_support_records_fail_closed_on_defects(self) -> None:
        support = SeekerOfficeIntegritySupport()
        integrity = support.build_package(mission=mission(), search_plan=search_plan(), discovery_evidence=(discovery_evidence(),), candidate=candidate())
        objects = support.build_constitutional_objects_package(mission=mission(), search_plan=search_plan(), discovery_evidence=(discovery_evidence(),), candidate=candidate())
        doctrine = support.build_constitutional_doctrine_package(mission=mission(), search_plan=search_plan(), discovery_evidence=(discovery_evidence(),), candidates=(candidate(),))
        bad_commits = support.evaluate_constitutional_commit_boundaries(
            ("Discovery Evidence Commit", "Mission Acceptance Commit", "Outbound Commitment Boundary"),
            integrity,
            partial_commit_findings=("candidate_package_partial",),
        )
        bad_replay = support.evaluate_replay_semantic_equivalence(integrity, objects, doctrine, unacceptable_differences=("Candidate Identity",))
        bad_config = support.evaluate_constitutional_configuration_object(mission(rule_versions={"objective": "SEEK-RM-006/1"}), search_plan(duplicate_rules=(), freshness_requirements=(), independence_requirements=(), sufficiency_requirements=()))
        bad_errors = support.evaluate_constitutional_error_taxonomy(("mystery impossible condition",))
        bad_trace = support.evaluate_certification_traceability_architecture(integrity, objects, doctrine, missing_relationships=("orphan_requirement",))
        bad_evidence = support.evaluate_certification_evidence_package((bad_commits, bad_replay, bad_errors, bad_trace), omitted_sections=("Certification Evidence",))

        self.assertEqual(bad_commits.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Candidate Package Commit", bad_commits.missing_boundaries)
        self.assertIn("Discovery Evidence Commit->Mission Acceptance Commit", bad_commits.ordering_violations)
        self.assertIn("candidate_package_partial", bad_commits.partial_commit_findings)
        self.assertEqual(bad_replay.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Candidate Identity", bad_replay.failed_invariants)
        self.assertEqual(bad_config.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("identity", bad_config.missing_configuration_fields)
        self.assertEqual(bad_errors.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("mystery impossible condition", bad_errors.unclassified_errors)
        self.assertEqual(bad_trace.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("orphan_requirement", bad_trace.orphan_findings)
        self.assertEqual(bad_evidence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Certification Evidence", bad_evidence.missing_sections)
        self.assertIn("SeekerConstitutionalCommitBoundaryRecord", bad_evidence.inadmissible_artifacts)

    def test_seek_rm003_canonical_evidence_package_passes_with_complete_inputs(self) -> None:
        package = SeekerOfficeIntegritySupport().build_rm003_canonical_evidence_package(
            mission=mission(rule_versions={**mission().rule_versions, "authorization": "AUTH/1", "configuration": "CONFIG/1"}),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )

        self.assertEqual(package.final_rm003_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            (
                "SEEK-RM-003-001",
                "SEEK-RM-003-002",
                "SEEK-RM-003-003",
                "SEEK-RM-003-004",
                "SEEK-RM-003-005",
                "SEEK-RM-003-006",
            ),
        )
        self.assertEqual(package.search_mission_canonical_object.missing_sections, ())
        self.assertEqual(package.search_mission_canonical_object.authority_findings, ())
        self.assertTrue(package.search_mission_canonical_object.lifecycle_state_separated)
        self.assertEqual(package.search_plan_constitutional_contract.missing_sections, ())
        self.assertEqual(package.search_plan_constitutional_contract.terminal_outcomes, ("COMPLETED", "INSUFFICIENT", "EXHAUSTED", "FAILED", "CANCELLED"))
        self.assertEqual(package.candidate_package_constitution.candidate_subject_count, 1)
        self.assertEqual(package.candidate_package_constitution.package_invariant_violations, ())
        self.assertEqual(package.candidate_identity_doctrine.missing_identity_fields, ())
        self.assertTrue(package.candidate_identity_doctrine.replay_stable)
        self.assertEqual(package.candidate_lifecycle_doctrine.terminal_state, "ACCEPTED")
        self.assertEqual(package.candidate_lifecycle_doctrine.invalid_transitions, ())
        self.assertEqual(package.search_mission_lifecycle_doctrine.terminal_state, "TERMINATED")
        self.assertTrue(package.search_mission_lifecycle_doctrine.authority_relinquished)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_seek_rm003_canonical_records_fail_closed_on_defects(self) -> None:
        support = SeekerOfficeIntegritySupport()
        bad_mission = mission(
            constitutional_authority="Testing Utility",
            search_plan_id="SEARCH-PLAN-OTHER",
            discovery_scope=("candidate_discovery", "portfolio_selection"),
            rule_versions={"objective": "SEEK-RM-006/1"},
        )
        bad_plan = search_plan(
            approval_status="DRAFT",
            approved_sources=(),
            approved_methods=(),
            sufficiency_requirements=(),
            termination_conditions=(),
            execution_limits={},
        )
        bad_candidate = candidate(candidate_reference="", attributes={"ticker": "ARG|AMBIGUOUS", "exchange": "NYSE"})
        integrity = support.build_package(
            mission=mission(),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )
        objects = support.build_constitutional_objects_package(
            mission=mission(),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )

        mission_record = support.evaluate_rm003_search_mission_canonical_object(bad_mission, bad_plan, integrity, objects)
        plan_record = support.evaluate_rm003_search_plan_constitutional_contract(bad_mission, bad_plan, (), integrity, objects)
        package_record = support.evaluate_rm003_candidate_package_constitution(
            bad_mission,
            bad_plan,
            (bad_candidate, candidate(candidate_reference="CAND-002")),
            (),
            integrity,
            objects,
        )
        identity_record = support.evaluate_rm003_candidate_identity_doctrine(bad_candidate, search_plan(), (discovery_evidence(),), None, objects)
        candidate_lifecycle = support.evaluate_rm003_candidate_lifecycle_doctrine(("DISCOVERED", "IDENTIFIED", "ACCEPTED"))
        mission_lifecycle = support.evaluate_rm003_search_mission_lifecycle_doctrine(("AUTHORIZED", "DISCOVERY", "TERMINATED"))

        self.assertEqual(mission_record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("unauthorized_issuer:Testing Utility", mission_record.authority_findings)
        self.assertIn("portfolio_selection", mission_record.boundary_findings)
        self.assertEqual(plan_record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("mission_plan_reference_mismatch", plan_record.plan_authority_findings)
        self.assertIn("unbounded_execution", plan_record.execution_bounds_findings)
        self.assertEqual(package_record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("single_candidate_invariant", package_record.package_invariant_violations)
        self.assertIn("Evidence Manifest", package_record.missing_sections)
        self.assertEqual(identity_record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("candidate_identifier", identity_record.missing_identity_fields)
        self.assertIn("ticker", identity_record.collision_findings)
        self.assertEqual(candidate_lifecycle.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("DISCOVERED->IDENTIFIED", candidate_lifecycle.invalid_transitions)
        self.assertIn("ACQUIRED", candidate_lifecycle.skipped_states)
        self.assertEqual(mission_lifecycle.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("AUTHORIZED->DISCOVERY", mission_lifecycle.invalid_transitions)
        self.assertIn("INITIALIZED", mission_lifecycle.skipped_states)

    def test_seek_rm003_doctrine_evidence_package_passes_with_complete_inputs(self) -> None:
        package = SeekerOfficeIntegritySupport().build_rm003_doctrine_evidence_package(
            mission=mission(rule_versions={**mission().rule_versions, "authorization": "AUTH/1", "configuration": "CONFIG/1"}),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidates=(candidate(),),
        )

        self.assertEqual(package.final_rm003_doctrine_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            (
                "SEEK-RM-003-007",
                "SEEK-RM-003-008",
                "SEEK-RM-003-009",
                "SEEK-RM-003-010",
                "SEEK-RM-003-011",
                "SEEK-RM-003-012",
            ),
        )
        self.assertEqual(package.search_sufficiency_doctrine.disposition, "SUFFICIENT")
        self.assertEqual(package.search_sufficiency_doctrine.missing_metrics, ())
        self.assertTrue(package.candidate_equivalence_doctrine.order_independent)
        self.assertEqual(package.candidate_equivalence_doctrine.unresolved_comparisons, ())
        self.assertEqual(package.candidate_freshness_doctrine.freshness_status, "FRESH")
        self.assertTrue(package.candidate_freshness_doctrine.delivery_eligible)
        self.assertEqual(package.candidate_independence_doctrine.independence_status, "INDEPENDENT")
        self.assertEqual(package.candidate_rejection_taxonomy.unsupported_rejection_findings, ())
        self.assertEqual(package.discovery_evidence_constitution.inadmissible_evidence, ())
        self.assertEqual(package.discovery_evidence_constitution.prohibited_semantic_findings, ())
        self.assertNotEqual(package.deterministic_digest, "")

    def test_seek_rm003_doctrine_records_fail_closed_on_defects(self) -> None:
        support = SeekerOfficeIntegritySupport()
        bad_plan = search_plan(
            approved_sources=("SEC-EDGAR", "NASDAQ"),
            sufficiency_requirements=(),
            termination_conditions=(),
        )
        stale_evidence = discovery_evidence(
            evidence_id="DISC-EVID-STALE",
            retrieved_at="2026-07-21T10:01:00Z",
            source_timestamp="2026-01-01T09:55:00Z",
            payload={
                "ticker": "ARG",
                "exchange": "NYSE",
                "security_identifier": "000000001",
                "analysis": "do not admit",
            },
        )
        unauthorized_evidence = discovery_evidence(
            evidence_id="DISC-EVID-BAD",
            source_id="UNAPPROVED-SOURCE",
            acquisition_method="manual_guess",
        )
        bad_candidate = candidate(candidate_reference="", evidence_references=("DISC-EVID-STALE",))
        duplicate_candidate = candidate(candidate_reference="CAND-002")
        integrity = support.build_package(
            mission=mission(),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )
        doctrine = support.build_constitutional_doctrine_package(
            mission=mission(),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidates=(candidate(),),
        )

        sufficiency = support.evaluate_rm003_search_sufficiency_doctrine(mission(), bad_plan, (stale_evidence,), (bad_candidate,), integrity, doctrine)
        equivalence = support.evaluate_rm003_candidate_equivalence_doctrine(search_plan(), (bad_candidate, duplicate_candidate), (stale_evidence,), doctrine)
        freshness = support.evaluate_rm003_candidate_freshness_doctrine(mission(), bad_candidate, (stale_evidence,), None, doctrine)
        independence = support.evaluate_rm003_candidate_independence_doctrine(search_plan(), bad_candidate, (), None, doctrine)
        rejection = support.evaluate_rm003_candidate_rejection_taxonomy(bad_candidate, (freshness, independence), doctrine, unsupported_categories=("Operator Preference",))
        evidence = support.evaluate_rm003_discovery_evidence_constitution(mission(), search_plan(), (unauthorized_evidence, stale_evidence), bad_candidate, None, doctrine)

        self.assertEqual(sufficiency.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("explicit_sufficiency_requirement", sufficiency.missing_metrics)
        self.assertEqual(sufficiency.disposition, "EVALUATION_INDETERMINATE")
        self.assertEqual(equivalence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("missing_candidate_reference", equivalence.unresolved_comparisons)
        self.assertEqual(freshness.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("outside_freshness_window", freshness.stale_or_expired_dependencies)
        self.assertFalse(freshness.delivery_eligible)
        self.assertEqual(independence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("missing_constitutional_discovery_evidence", independence.corroboration_findings)
        self.assertEqual(rejection.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Operator Preference", rejection.unsupported_rejection_findings)
        self.assertEqual(evidence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("DISC-EVID-BAD:source_not_approved", evidence.inadmissible_evidence)
        self.assertIn("DISC-EVID-STALE:analysis", evidence.prohibited_semantic_findings)

    def test_seek_rm003_operational_integrity_package_passes_with_complete_inputs(self) -> None:
        package = SeekerOfficeIntegritySupport().build_rm003_operational_integrity_evidence_package(
            mission=mission(rule_versions={**mission().rule_versions, "authorization": "AUTH/1", "configuration": "CONFIG/1", "discovery": "DISCOVERY/1"}),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )

        self.assertEqual(package.final_rm003_operational_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            (
                "SEEK-RM-003-013",
                "SEEK-RM-003-014",
                "SEEK-RM-003-015",
                "SEEK-RM-003-016",
                "SEEK-RM-003-017",
                "SEEK-RM-003-018",
            ),
        )
        self.assertEqual(package.discovery_provenance_architecture.orphan_objects, ())
        self.assertTrue(package.discovery_provenance_architecture.independently_reconstructable)
        self.assertEqual(package.office_state_machine.terminal_state, "DORMANT_CLEAN")
        self.assertTrue(package.office_state_machine.authority_relinquished)
        self.assertEqual(package.office_owned_persistent_state.unclassified_state, ())
        self.assertTrue(package.office_owned_persistent_state.recovery_supported)
        self.assertEqual(package.recovery_checkpoint_architecture.unauthorized_boundaries, ())
        self.assertTrue(package.recovery_checkpoint_architecture.replay_compatible)
        self.assertEqual(package.constitutional_commit_boundaries.missing_commit_boundaries, ())
        self.assertTrue(package.constitutional_commit_boundaries.monotonic_sequence_verified)
        self.assertTrue(package.replay_semantic_equivalence.semantic_equivalence)
        self.assertEqual(package.replay_semantic_equivalence.failed_invariants, ())
        self.assertNotEqual(package.deterministic_digest, "")

    def test_seek_rm003_operational_records_fail_closed_on_defects(self) -> None:
        support = SeekerOfficeIntegritySupport()
        integrity = support.build_package(mission=mission(), search_plan=search_plan(), discovery_evidence=(discovery_evidence(),), candidate=candidate())
        objects = support.build_constitutional_objects_package(mission=mission(), search_plan=search_plan(), discovery_evidence=(discovery_evidence(),), candidate=candidate())
        doctrine = support.build_constitutional_doctrine_package(mission=mission(), search_plan=search_plan(), discovery_evidence=(discovery_evidence(),), candidates=(candidate(),))
        cert_support = support.build_certification_support_package(
            mission=mission(rule_versions={**mission().rule_versions, "authorization": "AUTH/1", "configuration": "CONFIG/1", "discovery": "DISCOVERY/1"}),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )

        provenance = support.evaluate_rm003_discovery_provenance_architecture(
            mission(search_plan_id="OTHER-PLAN"),
            search_plan(),
            (),
            candidate(candidate_reference=""),
            integrity,
            doctrine,
            omitted_node_classes=("Discovery Evidence",),
            omitted_edge_classes=("ACQUIRED_FROM_SOURCE",),
            orphan_objects=("orphan_candidate",),
        )
        state_machine = support.evaluate_rm003_office_state_machine(("DORMANT", "DISCOVERY_EXECUTING", "DORMANT_CLEAN"), multiple_current_state_findings=("dual_current_state",))
        persistence = support.evaluate_rm003_office_owned_persistent_state(
            integrity,
            objects,
            doctrine,
            cert_support,
            unclassified_state=("operator_cache",),
            residual_state_findings=("active_authority_handle",),
        )
        checkpoints = support.evaluate_rm003_recovery_checkpoint_architecture(
            cert_support.recovery_checkpoint_architecture,
            observed_boundaries=("Search Mission acceptance", "Partial parsing buffer"),
            invalid_checkpoint_findings=("integrity_hash_mismatch",),
        )
        commits = support.evaluate_rm003_constitutional_commit_boundaries(
            ("CB-002 Search Plan Established", "CB-001 Search Mission Accepted", "CB-999 Runtime Convenience Commit"),
            partial_commit_findings=("candidate_partial_write",),
        )
        replay = support.evaluate_rm003_replay_semantic_equivalence(
            integrity,
            objects,
            doctrine,
            cert_support,
            failed_invariants=("Evidence Integrity",),
            prohibited_runtime_differences=("changed_candidate_identity",),
        )

        self.assertEqual(provenance.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Discovery Evidence", provenance.missing_node_classes)
        self.assertIn("ACQUIRED_FROM_SOURCE", provenance.missing_edge_classes)
        self.assertIn("orphan_candidate", provenance.orphan_objects)
        self.assertIn("mission_plan_provenance_mismatch", provenance.integrity_findings)
        self.assertEqual(state_machine.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("DORMANT->DISCOVERY_EXECUTING", state_machine.illegal_transitions)
        self.assertIn("MISSION_RECEIVED", state_machine.skipped_mandatory_states)
        self.assertIn("dual_current_state", state_machine.multiple_current_state_findings)
        self.assertEqual(persistence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("operator_cache", persistence.unclassified_state)
        self.assertIn("active_authority_handle", persistence.residual_state_findings)
        self.assertEqual(checkpoints.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Partial parsing buffer", checkpoints.unauthorized_boundaries)
        self.assertIn("integrity_hash_mismatch", checkpoints.invalid_checkpoint_findings)
        self.assertEqual(commits.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("CB-003 Candidate Discovered", commits.missing_commit_boundaries)
        self.assertIn("CB-999 Runtime Convenience Commit", commits.unauthorized_commit_boundaries)
        self.assertIn("CB-002 Search Plan Established->CB-001 Search Mission Accepted", commits.ordering_violations)
        self.assertIn("candidate_partial_write", commits.partial_commit_findings)
        self.assertEqual(replay.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Evidence Integrity", replay.failed_invariants)
        self.assertIn("changed_candidate_identity", replay.prohibited_runtime_differences)

    def test_seek_rm003_certification_closure_package_passes_with_complete_inputs(self) -> None:
        package = SeekerOfficeIntegritySupport().build_rm003_certification_closure_evidence_package(
            mission=mission(rule_versions={**mission().rule_versions, "authorization": "AUTH/1", "configuration": "CONFIG/1", "discovery": "DISCOVERY/1"}),
            search_plan=search_plan(),
            discovery_evidence=(discovery_evidence(),),
            candidate=candidate(),
        )

        self.assertEqual(package.final_rm003_certification_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.remediation_order_coverage,
            (
                "SEEK-RM-003-019",
                "SEEK-RM-003-020",
                "SEEK-RM-003-021",
                "SEEK-RM-003-022",
            ),
        )
        self.assertEqual(package.constitutional_configuration_object.missing_fields, ())
        self.assertEqual(package.constitutional_configuration_object.active_default_configuration_count, 1)
        self.assertEqual(package.constitutional_error_taxonomy.unclassified_errors, ())
        self.assertIn("Constitutional Error", package.constitutional_error_taxonomy.fail_closed_categories)
        self.assertEqual(package.certification_traceability_architecture.missing_layers, ())
        self.assertEqual(package.certification_traceability_architecture.orphan_requirements, ())
        self.assertEqual(package.certification_evidence_package.missing_sections, ())
        self.assertTrue(package.certification_evidence_package.supports_unconditional_pass)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_seek_rm003_certification_closure_records_fail_closed_on_defects(self) -> None:
        support = SeekerOfficeIntegritySupport()
        good_mission = mission(rule_versions={**mission().rule_versions, "authorization": "AUTH/1", "configuration": "CONFIG/1", "discovery": "DISCOVERY/1"})
        canonical = support.build_rm003_canonical_evidence_package(mission=good_mission, search_plan=search_plan(), discovery_evidence=(discovery_evidence(),), candidate=candidate())
        doctrine = support.build_rm003_doctrine_evidence_package(mission=good_mission, search_plan=search_plan(), discovery_evidence=(discovery_evidence(),), candidates=(candidate(),))
        operational = support.build_rm003_operational_integrity_evidence_package(mission=good_mission, search_plan=search_plan(), discovery_evidence=(discovery_evidence(),), candidate=candidate())
        cert_support = support.build_certification_support_package(mission=good_mission, search_plan=search_plan(), discovery_evidence=(discovery_evidence(),), candidate=candidate())

        configuration = support.evaluate_rm003_constitutional_configuration_object(
            mission(rule_versions={"objective": "SEEK-RM-006/1"}),
            search_plan(),
            cert_support,
            active_default_configuration_count=2,
            hidden_configuration_findings=("ENV_SEEKER_LIMIT",),
        )
        errors = support.evaluate_rm003_constitutional_error_taxonomy(cert_support, observed_errors=("mystery behavior", "replay mismatch"))
        traceability = support.evaluate_rm003_certification_traceability_architecture(
            canonical,
            doctrine,
            operational,
            cert_support,
            omitted_layers=("Evidence Artifact",),
            orphan_requirements=("SEEK-RM-003-021-REQ",),
            orphan_implementation=("src/argos/seeker/orphan.py",),
            orphan_evidence=("missing-evidence-record",),
        )
        evidence = support.evaluate_rm003_certification_evidence_package(
            canonical,
            doctrine,
            operational,
            configuration,
            errors,
            traceability,
            omitted_sections=("Replay Evidence",),
        )

        self.assertEqual(configuration.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("mission", configuration.missing_fields)
        self.assertEqual(configuration.active_default_configuration_count, 2)
        self.assertIn("ENV_SEEKER_LIMIT", configuration.hidden_configuration_findings)
        self.assertEqual(errors.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("mystery behavior", errors.unclassified_errors)
        self.assertIn("replay mismatch", errors.classified_errors)
        self.assertEqual(traceability.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Evidence Artifact", traceability.missing_layers)
        self.assertIn("SEEK-RM-003-021-REQ", traceability.orphan_requirements)
        self.assertEqual(evidence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("Replay Evidence", evidence.missing_sections)
        self.assertIn("SeekerRm003ConstitutionalConfigurationObjectRecord", evidence.inadmissible_artifacts)
        self.assertFalse(evidence.supports_unconditional_pass)


if __name__ == "__main__":
    unittest.main()
