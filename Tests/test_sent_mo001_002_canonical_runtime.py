from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.scheduler import EnterpriseOperatingMode, EnterpriseOperationsScheduler  # noqa: E402
from argos.sentinel import (  # noqa: E402
    CommanderAcknowledgmentResult,
    DeterministicSentinelSourceAdapter,
    FailureResponse,
    SENTINEL_COMMANDER_BRIDGE_ID,
    SentinelAuthorityRegistry,
    SentinelCanonicalRuntime,
    SentinelCommanderBridgeRuntime,
    SentinelDependencyCertifier,
    SentinelEnterpriseCompositionRoot,
    SentinelEnterpriseServiceRegistry,
    SentinelEnterpriseServices,
    SentinelEventSufficiencyRule,
    SentinelSufficiencyPolicyRegistry,
    SentinelNotificationStatus,
    SentinelRuntimeTraceEngine,
    SentinelRuntimeDecision,
    SentinelSourcePlanReference,
    recover_persisted_sentinel_records,
    sentinel_commander_bridge_definition,
    sentinel_delivery_equivalence_digest,
    sentinel_runtime_equivalence_digest,
)


def scheduler_with_mission() -> tuple[EnterpriseOperationsScheduler, object]:
    scheduler = EnterpriseOperationsScheduler()
    scheduler.enabled = True
    scheduler.operating_mode = EnterpriseOperatingMode.OBSERVATION_ONLY
    mission = scheduler.create_commander_directed_mission(
        mission_name="Sentinel exposure monitoring",
        required_offices=("Sentinel",),
        directive_id="CMD-DIR-SENTINEL-001",
        priority="Commander-Directed",
        maximum_api_calls=1,
        workflow_type="commander_directed_mission",
    )
    return scheduler, mission


def source_plan(**overrides) -> SentinelSourcePlanReference:
    data = {
        "source_plan_id": "SRCPLAN-SENT-001",
        "objective_id": "OBJ-SENT-EXPOSURE",
        "source_id": "APPROVED-SOURCE-001",
        "adapter_id": "SENTINEL-DETERMINISTIC-SOURCE-ADAPTER/1.0.0",
        "source_host": "approved.example",
        "source_path": "/events",
        "retrieval_method": "approved_poll",
        "entitlement_class": "paper-authoritative",
        "operationally_allowed": True,
    }
    data.update(overrides)
    return SentinelSourcePlanReference(**data)


def authority_for(mission, candidate: str = "commit:sentinel-candidate", runtime: str = "ARGOS-CANONICAL-RUNTIME") -> SentinelAuthorityRegistry:
    return SentinelAuthorityRegistry.for_mission(mission, candidate, runtime)


class SentinelCanonicalRuntimeIntegrationTests(unittest.TestCase):
    def test_sent_mo001_executes_from_commander_mission_to_notification_ready_alert(self) -> None:
        scheduler, mission = scheduler_with_mission()
        runtime = SentinelCanonicalRuntime(
            scheduler=scheduler,
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )

        record = runtime.execute_observation(
            mission=mission,
            source_plan=source_plan(),
            event_class="EXPOSURE_SOURCE_ALERT",
        )

        self.assertEqual(record.result, SentinelRuntimeDecision.PASS)
        self.assertEqual(record.final_office_state.name, "DORMANT")
        self.assertEqual(record.lifecycle_states, ("DORMANT", "ACTIVATION_REQUESTED", "ACTIVE", "COMPLETING", "DORMANT"))
        self.assertIsNotNone(record.evidence_envelope)
        self.assertIsNotNone(record.notification_ready_alert)
        assert record.notification_ready_alert is not None
        assert record.evidence_envelope is not None
        self.assertEqual(record.notification_ready_alert.notification_status, SentinelNotificationStatus.NOT_YET_DELIVERED)
        self.assertEqual(record.notification_ready_alert.required_destination, "Commander")
        self.assertEqual(record.evidence_envelope.final_notification_readiness_state, SentinelRuntimeDecision.PASS)
        self.assertTrue(any(event.action == "source_acquired" for event in record.trace_events))
        self.assertTrue(any(event.action == "sentinel_dormant" for event in record.trace_events))
        self.assertFalse(any("Seeker" in event.output_artifacts for event in record.trace_events))
        self.assertTrue(recover_persisted_sentinel_records(runtime.persistence))
        self.assertEqual(record.deterministic_digest, record.deterministic_digest)
        self.assertTrue(sentinel_runtime_equivalence_digest(record).startswith("sha256:"))

    def test_sent_mo001_rejects_non_commander_mission_without_activation(self) -> None:
        scheduler, mission = scheduler_with_mission()
        bad_mission = mission.__class__(**{**mission.__dict__, "trigger_type": "Scheduled", "commander_directive_id": ""})
        runtime = SentinelCanonicalRuntime(scheduler=scheduler, candidate_identity="commit:sentinel-candidate")

        record = runtime.execute_observation(
            mission=bad_mission,
            source_plan=source_plan(),
            event_class="EXPOSURE_SOURCE_ALERT",
        )

        self.assertEqual(record.result, SentinelRuntimeDecision.FAIL)
        self.assertEqual(record.failure_response, FailureResponse.QUARANTINE)
        self.assertIsNone(record.notification_ready_alert)
        self.assertEqual(record.final_office_state.name, "DORMANT")

    def test_sent_mo001_blocks_deterministic_adapter_in_operational_execution(self) -> None:
        scheduler, mission = scheduler_with_mission()
        runtime = SentinelCanonicalRuntime(
            scheduler=scheduler,
            source_adapter=DeterministicSentinelSourceAdapter(),
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )

        record = runtime.execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")

        self.assertEqual(record.result, SentinelRuntimeDecision.FAIL)
        self.assertEqual(record.failure_response, FailureResponse.HALT)
        self.assertIsNone(record.notification_ready_alert)

    def test_sent_mo001_repeated_runs_are_semantically_equivalent(self) -> None:
        scheduler_a, mission_a = scheduler_with_mission()
        scheduler_b, mission_b = scheduler_with_mission()
        first = SentinelCanonicalRuntime(
            scheduler=scheduler_a,
            authority_registry=authority_for(mission_a),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        ).execute_observation(mission=mission_a, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")
        second = SentinelCanonicalRuntime(
            scheduler=scheduler_b,
            authority_registry=authority_for(mission_b),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        ).execute_observation(mission=mission_b, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")

        self.assertEqual(sentinel_runtime_equivalence_digest(first), sentinel_runtime_equivalence_digest(second))

    def test_sent_mo002_delivers_alert_through_canonical_bridge_to_commander_ack(self) -> None:
        scheduler, mission = scheduler_with_mission()
        sentinel_runtime = SentinelCanonicalRuntime(
            scheduler=scheduler,
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )
        execution = sentinel_runtime.execute_observation(
            mission=mission,
            source_plan=source_plan(),
            event_class="EXPOSURE_SOURCE_ALERT",
        )
        assert execution.notification_ready_alert is not None
        bridge_runtime = SentinelCommanderBridgeRuntime(
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )

        delivery = bridge_runtime.deliver(execution.notification_ready_alert)

        self.assertEqual(sentinel_commander_bridge_definition().bridge_id, SENTINEL_COMMANDER_BRIDGE_ID)
        self.assertEqual(delivery.bridge_result_status, "ACCEPTED")
        self.assertEqual(delivery.sentinel_delivery_state, SentinelNotificationStatus.ACKNOWLEDGED)
        self.assertIsNotNone(delivery.commander_receipt)
        self.assertIsNotNone(delivery.commander_acknowledgment)
        assert delivery.commander_receipt is not None
        assert delivery.commander_acknowledgment is not None
        self.assertEqual(delivery.commander_receipt.destination_office, "Commander")
        self.assertEqual(delivery.commander_acknowledgment.acknowledgment_result, CommanderAcknowledgmentResult.ACCEPTED)
        self.assertEqual(delivery.downstream_activation_attempts, ())
        self.assertEqual(1, len(bridge_runtime.bridge_executor.traces()))
        self.assertEqual(sentinel_commander_bridge_definition().certification_status.value, "CERTIFIED_PRODUCTION")
        self.assertTrue(recover_persisted_sentinel_records(bridge_runtime.persistence))
        self.assertTrue(sentinel_delivery_equivalence_digest(delivery).startswith("sha256:"))

    def test_sent_mo002_duplicate_delivery_is_idempotent_without_second_commander_record(self) -> None:
        scheduler, mission = scheduler_with_mission()
        execution = SentinelCanonicalRuntime(
            scheduler=scheduler,
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        ).execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")
        assert execution.notification_ready_alert is not None
        bridge_runtime = SentinelCommanderBridgeRuntime(
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )

        first = bridge_runtime.deliver(execution.notification_ready_alert)
        second = bridge_runtime.deliver(execution.notification_ready_alert)

        self.assertEqual(first.sentinel_delivery_state, SentinelNotificationStatus.ACKNOWLEDGED)
        self.assertEqual(second.sentinel_delivery_state, SentinelNotificationStatus.ACKNOWLEDGED)
        self.assertEqual(1, len(bridge_runtime.commander.receipts))
        self.assertEqual(1, len(bridge_runtime.commander.acknowledgments))
        self.assertEqual(bridge_runtime.commander.acknowledgments[-1].acknowledgment_result, CommanderAcknowledgmentResult.ACCEPTED)

    def test_sent_mo002_rejects_forged_commander_destination_and_preserves_pending_alert(self) -> None:
        scheduler, mission = scheduler_with_mission()
        execution = SentinelCanonicalRuntime(
            scheduler=scheduler,
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        ).execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")
        assert execution.notification_ready_alert is not None
        forged = execution.notification_ready_alert.__class__(**{**execution.notification_ready_alert.__dict__, "required_destination": "Risk"})
        bridge_runtime = SentinelCommanderBridgeRuntime(
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )

        delivery = bridge_runtime.deliver(forged)

        self.assertEqual(delivery.sentinel_delivery_state, SentinelNotificationStatus.REJECTED)
        self.assertIsNone(delivery.commander_receipt)
        self.assertEqual((), bridge_runtime.static_bypass_analysis()["unresolved_findings"])

    def test_sent_mo1001_certified_composition_root_supplies_runtime_dependencies(self) -> None:
        root = SentinelEnterpriseCompositionRoot.paper()
        root.scheduler.enabled = True
        root.scheduler.operating_mode = EnterpriseOperatingMode.OBSERVATION_ONLY
        mission = root.scheduler.create_commander_directed_mission(
            mission_name="Certified Sentinel monitoring",
            required_offices=("Sentinel",),
            directive_id="CMD-DIR-SENTINEL-CERT",
            priority="Commander-Directed",
            maximum_api_calls=1,
            workflow_type="commander_directed_mission",
        )
        services = root.services_for_mission(
            mission,
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
            event_classes=("EXPOSURE_SOURCE_ALERT",),
        )
        certification = SentinelDependencyCertifier().certify(services)
        runtime = SentinelCanonicalRuntime.from_enterprise_services(
            services,
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )

        record = runtime.execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")

        self.assertEqual(certification.result, SentinelRuntimeDecision.PASS)
        self.assertEqual(record.result, SentinelRuntimeDecision.PASS)
        self.assertIs(runtime.scheduler, services.scheduler)
        self.assertIs(runtime.persistence, services.persistence)
        persisted_names = tuple(item.payload["payload"]["object_name"] for item in runtime.persistence.all_records())
        self.assertIn("sentinel_dependency_certification", persisted_names)
        self.assertIn("sentinel_authority_origin", persisted_names)
        self.assertIn("sentinel_sufficiency_evaluation", persisted_names)
        self.assertIn("sentinel_sufficiency_origin", persisted_names)

    def test_sent_mo1004_certification_mode_fails_closed_without_composition_root(self) -> None:
        scheduler, mission = scheduler_with_mission()
        runtime = SentinelCanonicalRuntime(
            scheduler=scheduler,
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
            require_certified_dependencies=True,
        )

        record = runtime.execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")

        self.assertEqual(record.result, SentinelRuntimeDecision.FAIL)
        self.assertEqual(record.failure_response, FailureResponse.HALT)
        self.assertTrue(any("DEPENDENCY_CERTIFICATION_FAILED" in event.failure_code for event in record.trace_events))

    def test_sent_mo1002_rejects_missing_authoritative_authority_in_certified_runtime(self) -> None:
        root = SentinelEnterpriseCompositionRoot.paper()
        root.scheduler.enabled = True
        root.scheduler.operating_mode = EnterpriseOperatingMode.OBSERVATION_ONLY
        mission = root.scheduler.create_commander_directed_mission(
            mission_name="Authority negative Sentinel monitoring",
            required_offices=("Sentinel",),
            directive_id="CMD-DIR-SENTINEL-AUTH-NEG",
            priority="Commander-Directed",
            maximum_api_calls=1,
            workflow_type="commander_directed_mission",
        )
        services = root.services_for_mission(
            mission,
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
            event_classes=("EXPOSURE_SOURCE_ALERT",),
        )
        bad_services = SentinelEnterpriseServices(
            scheduler=services.scheduler,
            lifecycle=services.lifecycle,
            source_adapter=services.source_adapter,
            mission_registry=services.mission_registry,
            authority_registry=SentinelAuthorityRegistry(()),
            persistence=services.persistence,
            evidence_origin_registry=services.evidence_origin_registry,
            sufficiency_policy_registry=services.sufficiency_policy_registry,
            service_registry=services.service_registry,
        )
        runtime = SentinelCanonicalRuntime.from_enterprise_services(
            bad_services,
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )

        record = runtime.execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")

        self.assertEqual(record.result, SentinelRuntimeDecision.FAIL)
        self.assertTrue(any("DEPENDENCY_CERTIFICATION_FAILED" in event.failure_code for event in record.trace_events))

    def test_sent_mo1005_sufficiency_uses_authoritative_event_class_policy(self) -> None:
        root = SentinelEnterpriseCompositionRoot.paper()
        root.scheduler.enabled = True
        root.scheduler.operating_mode = EnterpriseOperatingMode.OBSERVATION_ONLY
        mission = root.scheduler.create_commander_directed_mission(
            mission_name="Sufficiency negative Sentinel monitoring",
            required_offices=("Sentinel",),
            directive_id="CMD-DIR-SENTINEL-SUFF-NEG",
            priority="Commander-Directed",
            maximum_api_calls=1,
            workflow_type="commander_directed_mission",
        )
        services = root.services_for_mission(
            mission,
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
            event_classes=("EXPOSURE_SOURCE_ALERT",),
        )
        strict_policy = SentinelSufficiencyPolicyRegistry(
            (
                SentinelEventSufficiencyRule(
                    rule_id="SENT-TEST-STRICT-TWO-INDEPENDENT-SOURCES/1",
                    event_class="EXPOSURE_SOURCE_ALERT",
                    required_evidence_fields=("event_class", "value_hash", "source_timestamp", "raw_evidence"),
                    required_source_count=2,
                    required_independent_source_count=2,
                    required_dependencies=("Enterprise Authority Registry", "Enterprise Persistence", "Runtime Audit Infrastructure"),
                ),
            )
        )
        strict_registry = SentinelEnterpriseServiceRegistry(
            {
                "Enterprise Scheduler": services.scheduler,
                "Enterprise Mission Registry": services.mission_registry,
                "Enterprise Authority Registry": services.authority_registry,
                "Enterprise Persistence": services.persistence,
                "Runtime Audit Infrastructure": services.evidence_origin_registry,
                "Approved Operational Source Adapters": services.source_adapter,
                "Constitutional Sufficiency Policy": strict_policy,
            },
            acquisition_source="test strict constitutional policy registry",
        )
        strict_services = SentinelEnterpriseServices(
            scheduler=services.scheduler,
            lifecycle=services.lifecycle,
            source_adapter=services.source_adapter,
            mission_registry=services.mission_registry,
            authority_registry=services.authority_registry,
            persistence=services.persistence,
            evidence_origin_registry=services.evidence_origin_registry,
            sufficiency_policy_registry=strict_policy,
            service_registry=strict_registry,
        )
        runtime = SentinelCanonicalRuntime.from_enterprise_services(
            strict_services,
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )

        record = runtime.execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")

        self.assertEqual(record.result, SentinelRuntimeDecision.FAIL)
        self.assertTrue(any("OBSERVATION_SUFFICIENCY_NOT_SATISFIED" in event.failure_code for event in record.trace_events))

    def test_sent_mo1007_runtime_audit_trail_reconstructs_complete_trace(self) -> None:
        scheduler, mission = scheduler_with_mission()
        runtime = SentinelCanonicalRuntime(
            scheduler=scheduler,
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )

        record = runtime.execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")
        audit = runtime.audit_trail_for(record)

        self.assertEqual(audit.audit_reconstruction_result, SentinelRuntimeDecision.PASS)
        self.assertEqual(audit.missing_stages, ())
        self.assertEqual(audit.orphan_trace_records, ())
        self.assertEqual(tuple(item.execution_order for item in audit.trace_records), tuple(range(1, len(audit.trace_records) + 1)))
        self.assertIn("duplicate_suppression_evaluated", audit.coverage_stages)
        self.assertIn("source_independence_evaluated", audit.coverage_stages)
        self.assertIn("conflict_evaluated", audit.coverage_stages)
        self.assertIn("sufficiency_evaluated", audit.coverage_stages)
        self.assertIn("priority_determined", audit.coverage_stages)
        self.assertIn("persistence_operation", audit.coverage_stages)
        persisted_names = tuple(item.payload["payload"]["object_name"] for item in runtime.persistence.all_records())
        self.assertIn("sentinel_runtime_audit_trail", persisted_names)
        self.assertIn("sentinel_replay_equivalence_certification", persisted_names)

    def test_sent_mo1009_replay_semantic_equivalence_passes_and_detects_divergence(self) -> None:
        scheduler, mission = scheduler_with_mission()
        runtime = SentinelCanonicalRuntime(
            scheduler=scheduler,
            authority_registry=authority_for(mission),
            candidate_identity="commit:sentinel-candidate",
            runtime_identity="ARGOS-CANONICAL-RUNTIME",
        )
        record = runtime.execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")

        equivalent = runtime.certify_replay_equivalence(record)
        divergent = SentinelRuntimeTraceEngine().certify_replay_equivalence(
            record,
            record.__class__(**{**record.__dict__, "result": SentinelRuntimeDecision.FAIL}),
        )

        self.assertEqual(equivalent.result, SentinelRuntimeDecision.PASS)
        self.assertEqual(equivalent.semantic_differences, ())
        self.assertEqual(divergent.result, SentinelRuntimeDecision.FAIL)
        self.assertIn("semantic_digest", divergent.semantic_differences)
        self.assertIn("completion_status", divergent.semantic_differences)


if __name__ == "__main__":
    unittest.main()
