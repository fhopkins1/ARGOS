from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.scheduler import EnterpriseOperatingMode, EnterpriseOperationsScheduler  # noqa: E402
from argos.control_panel.sentinel_bridge_certification_support import (  # noqa: E402
    CertificationCompletenessValidator,
    ChronologicalEvidenceVerifier,
    EnterpriseCertificationDecision,
    EnterpriseSentinelBridgeCertificationWorkflow,
    IndependentSentinelBridgeCertificationTestSuite,
    ReadOnlyCertificationEvidenceService,
)
from argos.sentinel import (  # noqa: E402
    SentinelAuthorityRegistry,
    SentinelBridgeDeliveryCompositionRoot,
    SentinelCanonicalRuntime,
    SentinelCommanderBridgeRuntime,
    SentinelSourcePlanReference,
)


def scheduler_with_mission() -> tuple[EnterpriseOperationsScheduler, object]:
    scheduler = EnterpriseOperationsScheduler()
    scheduler.enabled = True
    scheduler.operating_mode = EnterpriseOperatingMode.OBSERVATION_ONLY
    mission = scheduler.create_commander_directed_mission(
        mission_name="Sentinel bridge certification support",
        required_offices=("Sentinel",),
        directive_id="CMD-DIR-SENTINEL-RM-002",
        priority="Commander-Directed",
        maximum_api_calls=1,
        workflow_type="commander_directed_mission",
    )
    return scheduler, mission


def source_plan() -> SentinelSourcePlanReference:
    return SentinelSourcePlanReference(
        source_plan_id="SRCPLAN-SENT-RM-002",
        objective_id="OBJ-SENT-RM-002",
        source_id="APPROVED-SOURCE-RM-002",
        adapter_id="SENTINEL-APPROVED-SOURCE-ADAPTER/1.0.0",
        source_host="approved.example",
        source_path="/events",
        retrieval_method="approved_poll",
        entitlement_class="paper-authoritative",
        operationally_allowed=True,
    )


def authority_for(mission, candidate: str = "commit:sentinel-rm-candidate", runtime: str = "ARGOS-CANONICAL-RUNTIME") -> SentinelAuthorityRegistry:
    return SentinelAuthorityRegistry.for_mission(mission, candidate, runtime)


def evidence_service() -> ReadOnlyCertificationEvidenceService:
    scheduler, mission = scheduler_with_mission()
    execution = SentinelCanonicalRuntime(
        scheduler=scheduler,
        authority_registry=authority_for(mission),
        candidate_identity="commit:sentinel-rm-candidate",
        runtime_identity="ARGOS-CANONICAL-RUNTIME",
    ).execute_observation(mission=mission, source_plan=source_plan(), event_class="EXPOSURE_SOURCE_ALERT")
    assert execution.notification_ready_alert is not None
    root = SentinelBridgeDeliveryCompositionRoot.for_mission(
        mission,
        candidate_identity="commit:sentinel-rm-candidate",
        runtime_identity="ARGOS-CANONICAL-RUNTIME",
    )
    bridge_runtime = SentinelCommanderBridgeRuntime.from_enterprise_services(
        root.services(),
        candidate_identity="commit:sentinel-rm-candidate",
        runtime_identity="ARGOS-CANONICAL-RUNTIME",
    )
    bridge_runtime.deliver(execution.notification_ready_alert)
    return ReadOnlyCertificationEvidenceService(bridge_runtime.persistence)


class SentinelRm002CertificationSupportTests(unittest.TestCase):
    def test_read_only_service_retrieves_immutable_evidence_without_sentinel_runtime(self) -> None:
        service = evidence_service()

        result = service.retrieve({"object_name": "sentinel_immutable_bridge_evidence"})

        self.assertTrue(result.read_only)
        self.assertEqual(result.service_identity, "EnterpriseReadOnlyCertificationEvidenceService/SENT-RM-002")
        self.assertEqual(len(result.evidence_items), 1)
        self.assertTrue(result.evidence_items[0].immutable)
        self.assertEqual(result.evidence_items[0].object_name, "sentinel_immutable_bridge_evidence")

    def test_completeness_and_chronology_validate_required_evidence(self) -> None:
        retrieval = evidence_service().retrieve_all()

        completeness = CertificationCompletenessValidator().validate(retrieval.evidence_items)
        chronology = ChronologicalEvidenceVerifier().verify(retrieval.evidence_items)

        self.assertEqual(completeness.validation_outcome, EnterpriseCertificationDecision.PASS)
        self.assertEqual(completeness.missing_artifacts, ())
        self.assertEqual(completeness.incomplete_dependency_chains, ())
        self.assertEqual(chronology.verification_outcome, EnterpriseCertificationDecision.PASS)
        self.assertEqual(chronology.invalid_ordering, ())

    def test_independent_test_suite_and_enterprise_workflow_are_not_sentinel_owned(self) -> None:
        service = evidence_service()
        retrieval = service.retrieve_all()

        tests = IndependentSentinelBridgeCertificationTestSuite().execute(retrieval.evidence_items)
        integration = EnterpriseSentinelBridgeCertificationWorkflow().execute(service)

        self.assertTrue(all(test.result == EnterpriseCertificationDecision.PASS for test in tests))
        self.assertEqual(integration.final_certification_decision, EnterpriseCertificationDecision.PASS)
        self.assertEqual(integration.bridge_identifier, "BRIDGE-SENTINEL-COMMANDER-ALERT-001")
        self.assertIn("SENT-RM-002-001", integration.remediation_order_coverage)
        self.assertIn("SENT-RM-002-007", integration.remediation_order_coverage)

    def test_missing_evidence_is_reported_without_fabrication(self) -> None:
        service = evidence_service()

        result = service.retrieve({"required_object_names": "sentinel_immutable_bridge_evidence,missing_required_artifact"})

        self.assertIn("missing_required_artifact", result.missing_evidence)


if __name__ == "__main__":
    unittest.main()
