from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.sentinel import (  # noqa: E402
    CommanderBridgeCertification,
    CommanderBridgeDiagnostic,
    CommanderNotificationRequest,
    CommanderNotificationRuntime,
    DeterministicObservationScheduler,
    MonitoringObjective,
    ObservationRecord,
    ObservationReplayEngine,
    ObservationScheduleEntry,
    RuntimeObservationPipeline,
    SentinelCertificationFramework,
    SentinelCertificationInput,
    SentinelConstitutionalAuditPackageGenerator,
    SentinelDecision,
    SentinelFailure,
    SentinelTraceabilityRecord,
    SourceRecord,
)


def objective() -> MonitoringObjective:
    return MonitoringObjective(
        objective_id="OBJ-RUNTIME",
        commander_authorization_id="CMD-AUTH-RUNTIME",
        monitoring_domain="source_health",
        interval_seconds=60,
        polling_cadence_seconds=15,
        priority=1,
        retry_policy=(5, 15, 45),
        timeout_seconds=30,
    )


def source(**overrides) -> SourceRecord:
    data = {
        "source_id": "SRC-RUNTIME",
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
        "observation_id": "OBS-RUNTIME",
        "objective_id": "OBJ-RUNTIME",
        "source_id": "SRC-RUNTIME",
        "collection_mechanism": "approved_poll",
        "acquisition_timestamp": "2026-07-20T12:00:01Z",
        "observation_timestamp": "2026-07-20T12:00:00Z",
        "evidence_creation_timestamp": "2026-07-20T12:00:02Z",
        "value_hash": "sha256:value",
        "evidence_references": ("sha256:raw",),
        "mission_assignment_id": "CMD-AUTH-RUNTIME",
        "freshness_limit_seconds": 60,
        "observed_age_seconds": 1,
    }
    data.update(overrides)
    return ObservationRecord(**data)


def notification(**overrides) -> CommanderNotificationRequest:
    data = {
        "notification_id": "NOTIFY-RUNTIME",
        "observation_id": "OBS-RUNTIME",
        "event_id": "EVENT-RUNTIME",
        "commander_recipient": "Commander",
        "runtime_bridge_id": "SENTINEL-COMMANDER-BRIDGE",
        "workflow_token_id": "CMD-AUTH-RUNTIME",
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
                requirement_id="SENT-MO-003-AUTHORITY",
                governing_doctrine="SENT-MO-003",
                implementation_component="argos.sentinel",
                verification_procedure="runtime-certification",
                evidence_artifact="sha256:authority-evidence",
                certification_result=SentinelDecision.PASS,
            ),
        ),
        "immutable_package_hash": "sha256:sentinel-package",
        "independent_audit_result": SentinelDecision.PASS,
    }
    data.update(overrides)
    return SentinelCertificationInput(**data)


class SentinelRuntimeCertificationRevisionTests(unittest.TestCase):
    def test_runtime_pipeline_generates_replayable_trace_and_evidence(self) -> None:
        schedule = DeterministicObservationScheduler().build_schedule((objective(),), "2026-07-20T12:00:00Z").entries[0]
        pipeline = RuntimeObservationPipeline()

        result = pipeline.execute(schedule, observation(), source())
        replay = ObservationReplayEngine().replay(pipeline.traces, pipeline.archive)

        self.assertEqual(result.decision, SentinelDecision.PASS)
        self.assertIsNotNone(result.notification_trace)
        self.assertEqual(result.evidence.sufficiency_evaluation, SentinelDecision.PASS)
        self.assertEqual(result.evidence.priority_evaluation, SentinelDecision.PASS)
        self.assertEqual(result.evidence.ordering_sequence, 1)
        self.assertTrue(result.runtime_trace.observation_ordering_trace.startswith("sha256:"))
        self.assertTrue(result.runtime_trace.sufficiency_evaluation_trace.startswith("sha256:"))
        self.assertTrue(result.runtime_trace.priority_evaluation_trace.startswith("sha256:"))
        self.assertEqual(replay.decision, SentinelDecision.PASS)
        self.assertEqual(pipeline.archive[0].execution_trace_digest, pipeline.traces[0].trace_digest)

    def test_runtime_pipeline_preserves_duplicate_evidence_without_notification(self) -> None:
        schedule = DeterministicObservationScheduler().build_schedule((objective(),), "2026-07-20T12:00:00Z").entries[0]
        pipeline = RuntimeObservationPipeline()

        result = pipeline.execute(schedule, observation(observation_id="OBS-DUP"), source(), (observation(),))

        self.assertEqual(result.decision, SentinelDecision.FAIL_CLOSED)
        self.assertIn(SentinelFailure.DUPLICATE_OBSERVATION, result.failures)
        self.assertIsNone(result.notification_trace)
        self.assertEqual(1, len(pipeline.archive))

    def test_commander_bridge_certification_requires_immutable_bridge_evidence(self) -> None:
        schedule = DeterministicObservationScheduler().build_schedule((objective(),), "2026-07-20T12:00:00Z").entries[0]
        result = RuntimeObservationPipeline().execute(schedule, observation(), source())
        assert result.notification_trace is not None

        passed = CommanderBridgeCertification().certify(
            (result.notification_trace,),
            CommanderBridgeDiagnostic(
                bridge_id="SENTINEL-COMMANDER-BRIDGE",
                throughput_count=1,
                rejected_count=0,
                authority_failures=0,
                token_continuity_failures=0,
                replay_consistent=True,
                evidence_generated=True,
            ),
        )
        failed = CommanderBridgeCertification().certify(
            (result.notification_trace,),
            CommanderBridgeDiagnostic(
                bridge_id="SENTINEL-COMMANDER-BRIDGE",
                throughput_count=1,
                rejected_count=1,
                authority_failures=1,
                token_continuity_failures=1,
                replay_consistent=False,
                evidence_generated=False,
            ),
        )

        self.assertEqual(passed.decision, SentinelDecision.PASS)
        self.assertIn(SentinelFailure.MISSING_BRIDGE_EVIDENCE, failed.failures)
        self.assertIn(SentinelFailure.AUTHORITY_UNVERIFIED, failed.failures)
        self.assertIn(SentinelFailure.TOKEN_DISCONTINUITY, failed.failures)
        self.assertIn(SentinelFailure.REPLAY_DIVERGENCE, failed.failures)

    def test_commander_bridge_orders_simultaneous_notifications_deterministically(self) -> None:
        runtime = CommanderNotificationRuntime()
        first = notification(notification_id="NOTIFY-B", observation_id="OBS-B", event_id="EVENT-1")
        second = notification(notification_id="NOTIFY-A", observation_id="OBS-A", event_id="EVENT-1")

        batch = runtime.notify_batch((first, second))
        replay = CommanderNotificationRuntime().notify_batch((first, second))

        self.assertEqual(tuple(item.audit_identifier for item in batch), ("AUDIT-NOTIFY-A", "AUDIT-NOTIFY-B"))
        self.assertEqual(tuple(item.runtime_trace_id for item in batch), tuple(item.runtime_trace_id for item in replay))
        self.assertTrue(all(item.notification_order[0] == "Commander" for item in batch))
        self.assertTrue(all(item.bridge_evidence_digest.startswith("sha256:") for item in batch))

    def test_commander_bridge_rejection_preserves_trace_and_evidence(self) -> None:
        rejected = CommanderNotificationRuntime().notify(
            notification(
                notification_id="NOTIFY-REJECT",
                commander_recipient="Risk",
                authority_verified=False,
                bridge_verified=False,
                token_continuous=False,
                workflow_creation_attempted=True,
                downstream_recipients=("Risk", "Commander"),
            )
        )

        self.assertEqual(rejected.decision, SentinelDecision.FAIL_CLOSED)
        self.assertIn(SentinelFailure.COMMANDER_NOT_FIRST, rejected.failures)
        self.assertIn(SentinelFailure.AUTHORITY_UNVERIFIED, rejected.failures)
        self.assertIn(SentinelFailure.BRIDGE_UNVERIFIED, rejected.failures)
        self.assertIn(SentinelFailure.TOKEN_DISCONTINUITY, rejected.failures)
        self.assertIn(SentinelFailure.WORKFLOW_CREATION_ATTEMPT, rejected.failures)
        self.assertIn("authority_unverified", rejected.bridge_rejection_reason)
        self.assertTrue(rejected.runtime_trace_id.startswith("sha256:"))
        self.assertTrue(rejected.bridge_evidence_digest.startswith("sha256:"))

    def test_runtime_pipeline_fails_closed_when_sufficiency_or_priority_missing(self) -> None:
        bad_priority = ObservationScheduleEntry(
            sequence_number=0,
            objective_id="OBJ-RUNTIME",
            scheduled_execution_time="2026-07-20T12:00:00Z",
            priority=-1,
            retry_policy=(5,),
            timeout_seconds=30,
        )
        pipeline = RuntimeObservationPipeline()

        result = pipeline.execute(bad_priority, observation(evidence_references=()), source())

        self.assertEqual(result.decision, SentinelDecision.FAIL_CLOSED)
        self.assertIn(SentinelFailure.INSUFFICIENT_OBSERVATION, result.failures)
        self.assertIn(SentinelFailure.PRIORITY_UNDETERMINED, result.failures)
        self.assertIsNone(result.notification_trace)
        self.assertEqual(result.evidence.sufficiency_evaluation, SentinelDecision.FAIL_CLOSED)
        self.assertEqual(result.evidence.priority_evaluation, SentinelDecision.FAIL_CLOSED)

    def test_audit_package_generator_fails_closed_on_missing_runtime_or_bridge_evidence(self) -> None:
        package = SentinelConstitutionalAuditPackageGenerator().generate(
            repository_revision="HEAD",
            certification_input=certification_input(),
            runtime_traces=(),
            observation_evidence=(),
            bridge_traces=(),
        )

        self.assertEqual(package.pass_fail_determination, SentinelDecision.FAIL_CLOSED)
        self.assertIn(SentinelFailure.MISSING_RUNTIME_TRACE.value, package.constitutional_deficiencies)
        self.assertIn(SentinelFailure.MISSING_BRIDGE_EVIDENCE.value, package.constitutional_deficiencies)

    def test_audit_package_generator_passes_complete_certification_evidence(self) -> None:
        schedule = DeterministicObservationScheduler().build_schedule((objective(),), "2026-07-20T12:00:00Z").entries[0]
        pipeline = RuntimeObservationPipeline()
        result = pipeline.execute(schedule, observation(), source())
        assert result.notification_trace is not None

        package = SentinelConstitutionalAuditPackageGenerator().generate(
            repository_revision="HEAD",
            certification_input=certification_input(),
            runtime_traces=pipeline.traces,
            observation_evidence=pipeline.archive,
            bridge_traces=(result.notification_trace,),
        )

        self.assertEqual(package.pass_fail_determination, SentinelDecision.PASS)
        self.assertEqual((), package.constitutional_deficiencies)
        self.assertTrue(package.package_digest.startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
