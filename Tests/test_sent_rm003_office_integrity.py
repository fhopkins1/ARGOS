from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.scheduler import EnterpriseOperatingMode, EnterpriseOperationsScheduler  # noqa: E402
from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.control_panel.sentinel_office_integrity import (  # noqa: E402
    OfficeAuthorityDecision,
    SentinelOfficeIntegritySupport,
    SentinelOfficeResponsibilityRegistry,
    sentinel_office_responsibility_definition,
)
from argos.sentinel import (  # noqa: E402
    SentinelAuthorityRegistry,
    SentinelCanonicalRuntime,
    SentinelRuntimeDecision,
    SentinelSourcePlanReference,
    sentinel_runtime_equivalence_digest,
)


def scheduler_with_mission() -> tuple[EnterpriseOperationsScheduler, object]:
    scheduler = EnterpriseOperationsScheduler()
    scheduler.enabled = True
    scheduler.operating_mode = EnterpriseOperatingMode.OBSERVATION_ONLY
    mission = scheduler.create_commander_directed_mission(
        mission_name="Sentinel office integrity certification support",
        required_offices=("Sentinel",),
        directive_id="CMD-DIR-SENTINEL-RM-003",
        priority="Commander-Directed",
        maximum_api_calls=1,
        workflow_type="commander_directed_mission",
    )
    return scheduler, mission


def source_plan() -> SentinelSourcePlanReference:
    return SentinelSourcePlanReference(
        source_plan_id="SRCPLAN-SENT-RM-003",
        objective_id="OBJ-SENT-RM-003",
        source_id="APPROVED-SOURCE-RM-003",
        adapter_id="SENTINEL-APPROVED-SOURCE-ADAPTER/1.0.0",
        source_host="approved.example",
        source_path="/events",
        retrieval_method="approved_poll",
        entitlement_class="paper-authoritative",
        operationally_allowed=True,
    )


def authority_for(mission, candidate: str = "commit:sentinel-rm003-candidate", runtime: str = "ARGOS-CANONICAL-RUNTIME") -> SentinelAuthorityRegistry:
    return SentinelAuthorityRegistry.for_mission(mission, candidate, runtime)


def runtime_and_execution() -> tuple[SentinelCanonicalRuntime, object]:
    scheduler, mission = scheduler_with_mission()
    runtime = SentinelCanonicalRuntime(
        scheduler=scheduler,
        authority_registry=authority_for(mission),
        candidate_identity="commit:sentinel-rm003-candidate",
        runtime_identity="ARGOS-CANONICAL-RUNTIME",
    )
    execution = runtime.execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")
    return runtime, execution


class SentinelRm003OfficeIntegrityTests(unittest.TestCase):
    def test_responsibility_registry_is_complete_and_rejects_enterprise_authority(self) -> None:
        registry = SentinelOfficeResponsibilityRegistry.default()

        validation = registry.validate_registry()
        accepted = registry.validate_authority("Sentinel", "authority_validation")
        rejected = registry.validate_authority("Sentinel", "enterprise_bridge_execution")

        self.assertEqual(validation.ownership_result, EnterpriseCertificationDecision.PASS)
        self.assertEqual(validation.duplicate_responsibilities, ())
        self.assertEqual(accepted.decision, OfficeAuthorityDecision.ACCEPTED)
        self.assertEqual(rejected.decision, OfficeAuthorityDecision.REJECTED)
        self.assertEqual(rejected.validation_result, EnterpriseCertificationDecision.FAIL)

    def test_office_integrity_package_uses_runtime_evidence_without_sentinel_self_certification(self) -> None:
        runtime, execution = runtime_and_execution()

        package = SentinelOfficeIntegritySupport().build_package(execution=execution, repository=runtime.persistence)

        self.assertEqual(execution.result, SentinelRuntimeDecision.PASS)
        self.assertEqual(package.final_office_readiness, EnterpriseCertificationDecision.PASS)
        self.assertIn("SENT-RM-003-008", package.remediation_order_coverage)
        self.assertEqual(package.responsibility_validation.ownership_result, EnterpriseCertificationDecision.PASS)
        self.assertEqual(package.behavior_completeness.missing_behaviors, ())
        self.assertEqual(package.runtime_completeness.missing_runtime_paths, ())
        self.assertTrue(package.runtime_completeness.authority_released)
        self.assertEqual(package.persistence_integrity.missing_records, ())
        self.assertEqual(package.persistence_integrity.prohibited_records, ())
        self.assertEqual(package.authority_evidence[1].decision, OfficeAuthorityDecision.REJECTED)

    def test_replay_equivalence_preserves_office_decisions_and_state(self) -> None:
        first_runtime, first = runtime_and_execution()
        second_runtime, second = runtime_and_execution()

        package = SentinelOfficeIntegritySupport().build_package(
            execution=first,
            replay_execution=second,
            repository=first_runtime.persistence,
        )

        self.assertEqual(sentinel_runtime_equivalence_digest(first), sentinel_runtime_equivalence_digest(second))
        self.assertNotEqual(first_runtime.persistence.all_records()[0].record_hash, "")
        self.assertNotEqual(second_runtime.persistence.all_records()[0].record_hash, "")
        self.assertEqual(package.deterministic_execution.result, EnterpriseCertificationDecision.PASS)
        self.assertTrue(package.decision_integrity.replay_equivalent)
        self.assertEqual(package.state_integrity.invalid_transitions, ())

    def test_missing_persistence_record_fails_closed_without_fabricating_completion(self) -> None:
        definition = sentinel_office_responsibility_definition()
        runtime, _ = runtime_and_execution()

        persistence = SentinelOfficeIntegritySupport().evaluate_persistence_integrity(runtime.persistence, definition)

        self.assertEqual(persistence.result, EnterpriseCertificationDecision.PASS)
        altered_model = dict(definition.persistence_model)
        altered_model["sentinel_missing_required_record"] = "required state intentionally absent"
        altered_definition = definition.__class__(**{**definition.__dict__, "persistence_model": altered_model})
        failed = SentinelOfficeIntegritySupport().evaluate_persistence_integrity(runtime.persistence, altered_definition)

        self.assertEqual(failed.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("sentinel_missing_required_record", failed.missing_records)


if __name__ == "__main__":
    unittest.main()
