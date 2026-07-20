from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.infrastructure import (  # noqa: E402
    AmendmentLifecycleState,
    AmendmentRegistryRecord,
    AuthorityTier,
    BehavioralEquivalenceEvidence,
    CertificationDependency,
    CertificationDependencyGraph,
    CertificationFreezeState,
    CertificationValidity,
    ChangeRequest,
    ConflictCase,
    ConflictResolutionStep,
    ConstitutionalAmendmentRegistry,
    ConstitutionalInput,
    DoctrineStatus,
    DoctrineVersionRecord,
    EquivalenceResult,
    FailureClassificationPolicy,
    FailureResponseClass,
    FreezeManager,
    FreezeStatus,
    GovernanceDecision,
    GovernanceFailure,
    InfrastructureGovernanceDoctrine,
    ModificationImpact,
    RegressionClassificationEngine,
    RegressionScope,
    RequirementTraceRecord,
)


def freeze_state() -> CertificationFreezeState:
    return CertificationFreezeState(
        certification_id="CERT-INF",
        certification_timestamp="2026-07-20T12:00:00Z",
        certified_doctrine_version="INF-006/1.0.0",
        certified_repository_hash="sha256:repo",
        certified_bridge_registry_version="bridge-v1",
        certified_authority_model_version="authority-v1",
        certified_runtime_version="runtime-v1",
        freeze_status=FreezeStatus.FROZEN,
        certification_status=CertificationValidity.VALID,
        invalidation_reason="",
    )


def equivalence(hash_value: str = "sha256:same") -> BehavioralEquivalenceEvidence:
    return BehavioralEquivalenceEvidence(
        certified_behavior_hash=hash_value,
        runtime_behavior_hash=hash_value,
        authority_transition_hash=hash_value,
        audit_record_hash=hash_value,
        persistence_hash=hash_value,
        replay_hash=hash_value,
        constitutional_output_hash=hash_value,
    )


def amendment_record(**overrides) -> AmendmentRegistryRecord:
    data = {
        "amendment_id": "AMD-INF-007",
        "amendment_title": "Governance additions",
        "amendment_type": "constitutional_governance",
        "amendment_status": AmendmentLifecycleState.EFFECTIVE,
        "authorizing_committee": "Infrastructure Constitutional Committee",
        "amendment_timestamp": "2026-07-20T12:01:00Z",
        "effective_date": "2026-07-20T12:02:00Z",
        "constitutional_version_before": "INF-006/1.0.0",
        "constitutional_version_after": "INF-007/1.0.0",
        "rationale": "Adopt constitutional version, conflict, and traceability doctrine.",
        "affected_doctrine": ("INF-GOV-017", "INF-GOV-018", "INF-GOV-019"),
        "affected_guarantees": ("constitutional_version_integrity", "constitutional_traceability"),
        "required_certification_scope": RegressionScope.INFRASTRUCTURE,
        "certification_status": "RECERTIFICATION_REQUIRED",
        "approval_evidence": "sha256:approval",
        "audit_references": ("sha256:audit",),
        "consistency_validated": True,
    }
    data.update(overrides)
    return AmendmentRegistryRecord(**data)


class INF007GovernanceAdditionsTests(unittest.TestCase):
    def test_doctrine_versions_require_one_active_version_and_preserved_history(self) -> None:
        doctrine = InfrastructureGovernanceDoctrine()
        valid = doctrine.doctrine_versions(
            (
                DoctrineVersionRecord("INF-006", "1.0.0", "2026-07-20T12:00:00Z", DoctrineStatus.SUPERSEDED, (), "sha256:old"),
                DoctrineVersionRecord("INF-007", "1.0.0", "2026-07-20T12:01:00Z", DoctrineStatus.ACTIVE, ("INF-006",), "sha256:new"),
            )
        )
        invalid = doctrine.doctrine_versions(
            (
                DoctrineVersionRecord("INF-006", "1.0.0", "2026-07-20T12:00:00Z", DoctrineStatus.ACTIVE, (), "sha256:old"),
                DoctrineVersionRecord("INF-007", "1.0.0", "2026-07-20T12:01:00Z", DoctrineStatus.ACTIVE, ("INF-006",), "sha256:new"),
            )
        )

        self.assertEqual(valid.decision, GovernanceDecision.APPROVED)
        self.assertIn(GovernanceFailure.MULTIPLE_ACTIVE_VERSIONS, invalid.failures)

    def test_certification_dependency_graph_requires_recertification_on_any_input_change(self) -> None:
        review = InfrastructureGovernanceDoctrine().certification_dependency_graph(
            CertificationDependencyGraph(
                certification_id="CERT-INF",
                immutable_graph_hash="sha256:graph",
                dependencies=(
                    CertificationDependency("bridge", ConstitutionalInput.BRIDGE, "sha256:old", "sha256:new"),
                ),
            )
        )

        self.assertEqual(review.decision, GovernanceDecision.REJECTED_FAIL_CLOSED)
        self.assertIn(GovernanceFailure.CERTIFICATION_DEPENDENCY_CHANGED, review.failures)

    def test_conflict_resolution_uses_hierarchy_then_more_restrictive_behavior(self) -> None:
        doctrine = InfrastructureGovernanceDoctrine()
        hierarchy = doctrine.resolve_conflict(
            ConflictCase("CONFLICT-1", AuthorityTier.CONSTITUTION, AuthorityTier.RUNTIME, False, 1, 5, "sha256:evidence")
        )
        unresolved = doctrine.resolve_conflict(
            ConflictCase("CONFLICT-2", AuthorityTier.RUNTIME, AuthorityTier.RUNTIME, False, 1, 1, "")
        )

        self.assertEqual(hierarchy.selected_step, ConflictResolutionStep.AUTHORITY_HIERARCHY)
        self.assertEqual(hierarchy.winning_authority, AuthorityTier.CONSTITUTION)
        self.assertEqual(unresolved.decision, GovernanceDecision.REJECTED_FAIL_CLOSED)
        self.assertIn(GovernanceFailure.UNRESOLVED_CONFLICT, unresolved.failures)

    def test_failure_classification_policy_requires_governed_metadata(self) -> None:
        review = InfrastructureGovernanceDoctrine().failure_classification_policy(
            FailureClassificationPolicy(
                classification=FailureResponseClass.QUARANTINE,
                recovery_eligible=False,
                retry_eligible=False,
                quarantine_eligible=True,
                certification_impact=RegressionScope.INFRASTRUCTURE,
                audit_severity="critical",
                operator_notification_required=True,
            )
        )

        self.assertEqual(review.decision, GovernanceDecision.APPROVED)

    def test_freeze_manager_invalidates_behavior_and_accepts_equivalent_refactor(self) -> None:
        manager = FreezeManager()
        state, refactor = manager.evaluate(freeze_state(), ChangeRequest("CHG-1", ("src/argos/infrastructure/governance.py",), (), False, False), equivalence())
        _, behavior = manager.evaluate(state, ChangeRequest("CHG-2", ("src/argos/infrastructure/governance.py",), ("authority",), False, True))

        self.assertEqual(refactor.certification_status, CertificationValidity.VALID)
        self.assertEqual(refactor.equivalence, EquivalenceResult.EQUIVALENT)
        self.assertEqual(behavior.certification_status, CertificationValidity.INVALID)
        self.assertEqual(len(manager.audit_history), 2)

    def test_regression_classification_escalates_uncertainty_to_enterprise(self) -> None:
        record = RegressionClassificationEngine().classify(
            ModificationImpact(
                modification_id="MOD-1",
                changed_files=("src/argos/infrastructure/governance.py",),
                affected_guarantees=(ConstitutionalInput.BRIDGE,),
                direct_dependencies=("enterprise:sentinel",),
                indirect_dependencies=(),
                evidence_reference="",
                behavioral_change=True,
                dependency_analysis_complete=False,
                deterministic_confidence=False,
            ),
            requested_scope=RegressionScope.LOCAL,
        )

        self.assertEqual(record.selected_recertification_scope, RegressionScope.ENTERPRISE)
        self.assertIn(GovernanceFailure.MISSING_DEPENDENCY_GRAPH, record.failures)
        self.assertIn(GovernanceFailure.UNDER_SCOPED_REGRESSION, record.failures)

    def test_traceability_rejects_orphaned_requirements_and_invariants_include_additions(self) -> None:
        doctrine = InfrastructureGovernanceDoctrine()
        orphan = doctrine.traceability(
            (RequirementTraceRecord("REQ-1", "INF-GOV-019", (), ("sha256:impl",), ("sha256:cert",), ()),)
        )

        self.assertIn(GovernanceFailure.ORPHANED_REQUIREMENT, orphan.failures)
        self.assertIn("constitutional_version_integrity", doctrine.invariant_set().invariants)

    def test_amendment_registry_is_append_only_authorized_and_requires_recertification(self) -> None:
        registry, decision = ConstitutionalAmendmentRegistry().append(amendment_record(), previous_state=AmendmentLifecycleState.APPROVED)
        unchanged, rejected = registry.append(
            amendment_record(amendment_id="AMD-BAD", authorizing_committee="Runtime", consistency_validated=False),
            previous_state=AmendmentLifecycleState.DRAFT,
        )

        self.assertEqual(decision.decision, GovernanceDecision.APPROVED)
        self.assertTrue(decision.recertification_required)
        self.assertEqual(len(registry.records), 1)
        self.assertEqual(unchanged.records, registry.records)
        self.assertIn(GovernanceFailure.UNAUTHORIZED_AMENDMENT, rejected.failures)


if __name__ == "__main__":
    unittest.main()
