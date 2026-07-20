from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.sentinel import (  # noqa: E402
    CommanderNotificationRequest,
    CommanderNotificationRuntime,
    DeterministicObservationScheduler,
    MonitoringObjective,
    ObservationIntegrityValidator,
    ObservationRecord,
    SentinelCertificationFramework,
    SentinelCertificationInput,
    SentinelDecision,
    SentinelFailure,
    SentinelTraceabilityRecord,
    SourceRecord,
    SyntheticObservationEliminationEngine,
    observation_fingerprint,
)


def objective(**overrides) -> MonitoringObjective:
    data = {
        "objective_id": "OBJ-1",
        "commander_authorization_id": "CMD-AUTH-1",
        "monitoring_domain": "source_health",
        "interval_seconds": 60,
        "polling_cadence_seconds": 15,
        "priority": 10,
        "retry_policy": (5, 15, 45),
        "timeout_seconds": 30,
    }
    data.update(overrides)
    return MonitoringObjective(**data)


def source(**overrides) -> SourceRecord:
    data = {
        "source_id": "SRC-1",
        "enabled": True,
        "authorized": True,
        "health_state": "HEALTHY",
        "independence_group": "primary",
        "availability_score": 1.0,
        "response_success_rate": 1.0,
    }
    data.update(overrides)
    return SourceRecord(**data)


def observation(**overrides) -> ObservationRecord:
    data = {
        "observation_id": "OBS-1",
        "objective_id": "OBJ-1",
        "source_id": "SRC-1",
        "collection_mechanism": "approved_poll",
        "acquisition_timestamp": "2026-07-20T12:00:01Z",
        "observation_timestamp": "2026-07-20T12:00:00Z",
        "evidence_creation_timestamp": "2026-07-20T12:00:02Z",
        "value_hash": "sha256:value",
        "evidence_references": ("sha256:raw",),
        "mission_assignment_id": "CMD-AUTH-1",
        "freshness_limit_seconds": 60,
        "observed_age_seconds": 5,
    }
    data.update(overrides)
    return ObservationRecord(**data)


def notification(**overrides) -> CommanderNotificationRequest:
    data = {
        "notification_id": "NOTIFY-1",
        "observation_id": "OBS-1",
        "event_id": "EVENT-1",
        "commander_recipient": "Commander",
        "runtime_bridge_id": "BRIDGE-SENT-CMD",
        "workflow_token_id": "TOKEN-1",
        "authority_verified": True,
        "bridge_verified": True,
        "token_continuous": True,
        "downstream_recipients": ("Commander",),
    }
    data.update(overrides)
    return CommanderNotificationRequest(**data)


def certification_input(**overrides) -> SentinelCertificationInput:
    results = {category: True for category in SentinelCertificationFramework.required_categories}
    data = {
        "verification_results": results,
        "traceability": (
            SentinelTraceabilityRecord(
                requirement_id="SENT-MO-001",
                governing_doctrine="SENT Doctrine",
                implementation_component="argos.sentinel",
                verification_procedure="unit",
                evidence_artifact="sha256:evidence",
                certification_result=SentinelDecision.PASS,
            ),
        ),
        "immutable_package_hash": "sha256:package",
        "independent_audit_result": SentinelDecision.PASS,
    }
    data.update(overrides)
    return SentinelCertificationInput(**data)


class SENTMO001To005SentinelObservationTests(unittest.TestCase):
    def test_sent_mo001_schedule_is_deterministic_and_commander_directed(self) -> None:
        scheduler = DeterministicObservationScheduler()
        plan = scheduler.build_schedule(
            (objective(objective_id="B", priority=1), objective(objective_id="A", priority=10)),
            "2026-07-20T12:00:00Z",
        )
        replay = scheduler.build_schedule(
            (objective(objective_id="B", priority=1), objective(objective_id="A", priority=10)),
            "2026-07-20T12:00:00Z",
        )
        failed = scheduler.build_schedule((objective(commander_authorization_id=""),), "2026-07-20T12:00:00Z")

        self.assertEqual(plan.decision, SentinelDecision.PASS)
        self.assertEqual(tuple(entry.objective_id for entry in plan.entries), ("A", "B"))
        self.assertEqual(plan.schedule_digest, replay.schedule_digest)
        self.assertIn(SentinelFailure.UNAUTHORIZED_OBJECTIVE, failed.failures)

    def test_sent_mo002_validates_source_freshness_duplicates_conflicts_and_provenance(self) -> None:
        validator = ObservationIntegrityValidator()
        admitted = validator.validate(observation(), source())
        duplicate = validator.validate(observation(observation_id="OBS-2"), source(), (observation(),))
        conflict = validator.validate(observation(observation_id="OBS-3", value_hash="sha256:other"), source(), (observation(),))
        stale = validator.validate(observation(observed_age_seconds=99), source())

        self.assertEqual(admitted.decision, SentinelDecision.ADMITTED)
        self.assertTrue(admitted.admissible)
        self.assertEqual(admitted.fingerprint, observation_fingerprint(observation()))
        self.assertEqual(duplicate.decision, SentinelDecision.DUPLICATE)
        self.assertEqual(conflict.decision, SentinelDecision.CONFLICT)
        self.assertIn(SentinelFailure.STALE_OBSERVATION, stale.failures)

    def test_sent_mo002_requires_independent_corroboration_when_mission_demands_it(self) -> None:
        decision = ObservationIntegrityValidator().validate(
            observation(),
            source(independence_group="shared"),
            corroborating_sources=(source(source_id="SRC-2", independence_group="shared"),),
            require_independent_corroboration=True,
        )

        self.assertEqual(decision.decision, SentinelDecision.REJECTED)
        self.assertIn(SentinelFailure.SOURCE_NOT_INDEPENDENT, decision.failures)

    def test_sent_mo003_notifies_commander_first_and_never_creates_workflows(self) -> None:
        runtime = CommanderNotificationRuntime()
        delivered = runtime.notify(notification())
        duplicate = runtime.notify(notification())
        invalid = runtime.notify(
            notification(
                notification_id="NOTIFY-2",
                downstream_recipients=("Risk", "Commander"),
                workflow_creation_attempted=True,
                authority_verified=False,
            )
        )

        self.assertEqual(delivered.decision, SentinelDecision.NOTIFIED_COMMANDER)
        self.assertIn(SentinelFailure.DUPLICATE_NOTIFICATION, duplicate.failures)
        self.assertIn(SentinelFailure.COMMANDER_NOT_FIRST, invalid.failures)
        self.assertIn(SentinelFailure.WORKFLOW_CREATION_ATTEMPT, invalid.failures)
        self.assertIn(SentinelFailure.AUTHORITY_UNVERIFIED, invalid.failures)

    def test_sent_mo004_rejects_synthetic_placeholder_unsupported_and_incomplete_observations(self) -> None:
        engine = SyntheticObservationEliminationEngine()
        decision = engine.evaluate(
            observation(placeholder=True, synthetic_indicator=True, evidence_references=()),
            source(enabled=False, authorized=False),
        )

        self.assertEqual(decision.decision, SentinelDecision.REJECTED)
        self.assertIn(SentinelFailure.PLACEHOLDER_OBSERVATION, decision.failures)
        self.assertIn(SentinelFailure.SYNTHETIC_OBSERVATION, decision.failures)
        self.assertIn(SentinelFailure.SOURCE_UNAUTHORIZED, decision.failures)
        self.assertIn(SentinelFailure.INCOMPLETE_EVIDENCE, decision.failures)

    def test_sent_mo005_certifies_only_complete_evidence_and_traceability(self) -> None:
        framework = SentinelCertificationFramework()
        passed = framework.certify(certification_input())
        failed_results = {category: True for category in SentinelCertificationFramework.required_categories}
        failed_results["runtime"] = False
        failed = framework.certify(
            certification_input(
                verification_results=failed_results,
                traceability=(),
                immutable_package_hash="",
                independent_audit_result=SentinelDecision.FAIL_CLOSED,
            )
        )

        self.assertEqual(passed.decision, SentinelDecision.PASS)
        self.assertTrue(passed.certified)
        self.assertEqual(failed.decision, SentinelDecision.FAIL_CLOSED)
        self.assertIn(SentinelFailure.MISSING_CERTIFICATION_EVIDENCE, failed.failures)
        self.assertIn(SentinelFailure.TRACEABILITY_GAP, failed.failures)


if __name__ == "__main__":
    unittest.main()
