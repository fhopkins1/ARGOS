from __future__ import annotations

import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from argos.historian.enterprise_information_journey import (
    EnterpriseInformationJourneyRuntime,
    HistorianRuntimeError,
    JourneyState,
    MissingInformationClassification,
    ProvenanceEdgeType,
)


class HistorianRM002AEnterpriseInformationJourneyRuntimeTest(unittest.TestCase):
    def _complete_runtime(self) -> tuple[EnterpriseInformationJourneyRuntime, str, str, str]:
        runtime = EnterpriseInformationJourneyRuntime()
        workflow_id = "WF-HIST-002A-001"
        authorization = "AUTH-HIST-002A-001"
        journey = runtime.create_journey(
            workflow_id=workflow_id,
            authorization=authorization,
            timestamp="2026-07-31T14:00:00Z",
            metadata={"enterprise_instance_id": "ARGOS", "archive_namespace": "historian-rm002a"},
        )
        journey = runtime.transition(journey.journey_id, JourneyState.INITIALIZED, workflow_id=workflow_id, authorization=authorization, timestamp="2026-07-31T14:01:00Z")
        journey = runtime.transition(journey.journey_id, JourneyState.ACTIVE, workflow_id=workflow_id, authorization=authorization, timestamp="2026-07-31T14:02:00Z")
        journey = runtime.register_artifact(
            journey.journey_id,
            artifact_type="Decision Object",
            constitutional_owner="Exit Decision Office",
            workflow_id=workflow_id,
            originating_office="Exit Decision Office",
            payload={"decision_id": "DEC-001", "decision": "REJECTED_ALTERNATIVE_PRESERVED"},
            timestamp="2026-07-31T14:03:00Z",
        )
        first_artifact = journey.artifacts[0].artifact_id
        journey = runtime.register_artifact(
            journey.journey_id,
            artifact_type="Evidence Object",
            constitutional_owner="Analyst Office",
            workflow_id=workflow_id,
            originating_office="Analyst Office",
            payload={"evidence_id": "EV-001", "raw": "source language preserved"},
            timestamp="2026-07-31T14:04:00Z",
        )
        second_artifact = journey.artifacts[1].artifact_id
        runtime.add_provenance_edge(
            journey.journey_id,
            source_artifact_id=second_artifact,
            destination_artifact_id=first_artifact,
            relationship_type=ProvenanceEdgeType.SUPPORTS,
            workflow_id=workflow_id,
            timestamp="2026-07-31T14:05:00Z",
        )
        runtime.preserve_language(
            journey.journey_id,
            raw_language="The original decision rationale remains unchanged.",
            structured_record={"record_type": "decision_rationale", "decision_id": "DEC-001"},
            semantic_record={"producer": "Exit Decision Office", "interpretation_version": "1"},
            source_language="en-US",
            workflow_id=workflow_id,
            timestamp="2026-07-31T14:06:00Z",
        )
        runtime.record_missing_information(
            journey.journey_id,
            affected_artifact=first_artifact,
            constitutional_owner="Analyst Office",
            workflow_id=workflow_id,
            classification=MissingInformationClassification.CONFLICTING_SOURCES,
            timestamp="2026-07-31T14:07:00Z",
            impact_assessment="conflict preserved for learning and replay",
            recovery_status="UNRESOLVED_RETAINED",
        )
        runtime.add_counterfactual_branch(
            journey.journey_id,
            branch_type="alternative_exit",
            source_artifact_id=first_artifact,
            historical_state="REJECTED",
            preservation_reason="required for deterministic counterfactual reconstruction",
            workflow_id=workflow_id,
            timestamp="2026-07-31T14:08:00Z",
        )
        runtime.transition(journey.journey_id, JourneyState.COMPLETE, workflow_id=workflow_id, authorization=authorization, timestamp="2026-07-31T14:09:00Z")
        runtime.transition(journey.journey_id, JourneyState.CLOSED, workflow_id=workflow_id, authorization=authorization, timestamp="2026-07-31T14:10:00Z")
        return runtime, journey.journey_id, workflow_id, authorization

    def test_complete_journey_lifecycle_registration_custody_graph_language_and_completion(self) -> None:
        runtime, journey_id, workflow_id, _authorization = self._complete_runtime()
        journey = runtime.get_journey(journey_id)
        self.assertEqual(JourneyState.CLOSED, journey.lifecycle_state)
        self.assertEqual(2, len(journey.artifacts))
        self.assertEqual(2, len(journey.custody_records))
        self.assertGreaterEqual(len(journey.provenance_edges), 3)
        self.assertEqual(1, len(journey.language_artifacts))
        self.assertEqual(1, len(journey.missing_information))
        self.assertEqual(1, len(journey.counterfactual_branches))
        self.assertTrue(all(record.current_custodian_office for record in journey.custody_records))
        self.assertTrue(all(evidence.evidence_digest for evidence in journey.evidence))
        reconstruction = runtime.reconstruct(journey_id, workflow_id=workflow_id, timestamp="2026-07-31T14:11:00Z")
        self.assertEqual("COMPLETE", reconstruction.completeness_status)

    def test_replay_and_learning_projection_are_deterministic_and_read_only(self) -> None:
        runtime, journey_id, workflow_id, _authorization = self._complete_runtime()
        replay_a = runtime.replay(journey_id, workflow_id=workflow_id, timestamp="2026-07-31T14:12:00Z")
        replay_b = runtime.replay(journey_id, workflow_id=workflow_id, timestamp="2026-07-31T14:12:00Z")
        self.assertTrue(replay_a.equivalent)
        self.assertEqual(replay_a.replay_digest, replay_b.replay_digest)
        projection = runtime.learning_projection(journey_id, requester="Enterprise Learning", workflow_id=workflow_id, timestamp="2026-07-31T14:13:00Z")
        self.assertTrue(projection["read_only"])
        self.assertFalse(projection["historian_performed_learning"])
        self.assertEqual(2, len(projection["artifact_ids"]))
        with self.assertRaises(TypeError):
            projection["read_only"] = False  # type: ignore[index]

    def test_fail_closed_on_invalid_transition_duplicate_registration_and_unauthorized_learning(self) -> None:
        runtime = EnterpriseInformationJourneyRuntime()
        journey = runtime.create_journey(
            workflow_id="WF-HIST-FAIL",
            authorization="AUTH-HIST-FAIL",
            timestamp="2026-07-31T15:00:00Z",
            metadata={"test": "fail_closed"},
        )
        with self.assertRaises(HistorianRuntimeError) as invalid_transition:
            runtime.transition(journey.journey_id, JourneyState.ACTIVE, workflow_id="WF-HIST-FAIL", authorization="AUTH-HIST-FAIL", timestamp="2026-07-31T15:01:00Z")
        self.assertEqual("INVALID_TRANSITION", invalid_transition.exception.code)
        self.assertEqual("FAIL_CLOSED", invalid_transition.exception.evidence.outcome)

        runtime.transition(journey.journey_id, JourneyState.INITIALIZED, workflow_id="WF-HIST-FAIL", authorization="AUTH-HIST-FAIL", timestamp="2026-07-31T15:02:00Z")
        runtime.transition(journey.journey_id, JourneyState.ACTIVE, workflow_id="WF-HIST-FAIL", authorization="AUTH-HIST-FAIL", timestamp="2026-07-31T15:03:00Z")
        runtime.register_artifact(
            journey.journey_id,
            artifact_type="Audit Record",
            constitutional_owner="Enterprise Audit",
            workflow_id="WF-HIST-FAIL",
            originating_office="Enterprise Audit",
            payload={"audit_id": "AUD-001"},
            timestamp="2026-07-31T15:04:00Z",
        )
        with self.assertRaises(HistorianRuntimeError) as duplicate:
            runtime.register_artifact(
                journey.journey_id,
                artifact_type="Audit Record",
                constitutional_owner="Enterprise Audit",
                workflow_id="WF-HIST-FAIL",
                originating_office="Enterprise Audit",
                payload={"audit_id": "AUD-001"},
                timestamp="2026-07-31T15:05:00Z",
            )
        self.assertEqual("DUPLICATE_ARTIFACT", duplicate.exception.code)
        with self.assertRaises(HistorianRuntimeError) as unauthorized:
            runtime.learning_projection(journey.journey_id, requester="Commander", workflow_id="WF-HIST-FAIL", timestamp="2026-07-31T15:06:00Z")
        self.assertEqual("UNAUTHORIZED_LEARNING_RETRIEVAL", unauthorized.exception.code)

    def test_certification_report_covers_all_rm002a_capabilities(self) -> None:
        runtime, journey_id, workflow_id, _authorization = self._complete_runtime()
        runtime.replay(journey_id, workflow_id=workflow_id, timestamp="2026-07-31T14:12:00Z")
        runtime.learning_projection(journey_id, requester="Enterprise Learning", workflow_id=workflow_id, timestamp="2026-07-31T14:13:00Z")
        report = runtime.certification_report(journey_id, workflow_id=workflow_id, timestamp="2026-07-31T14:14:00Z")
        self.assertEqual("PASS", report["certification_status"])
        self.assertEqual((), report["missing_capabilities"])
        self.assertGreaterEqual(report["evidence_count"], 10)


if __name__ == "__main__":
    unittest.main()
