from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.sentinel import (  # noqa: E402
    CommanderBridgeCertification,
    CommanderBridgeDiagnostic,
    DeterministicObservationScheduler,
    MonitoringObjective,
    ObservationRecord,
    ObservationReplayEngine,
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
