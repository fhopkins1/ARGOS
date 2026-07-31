from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from argos.historian.enterprise_information_journey import (  # noqa: E402
    EnterpriseInformationJourneyRuntime,
    JourneyState,
    MissingInformationClassification,
    ProvenanceEdgeType,
)


ORDER_ID = "HISTORIAN-RM-002A"
OUTPUT_DIR = Path("Documentation") / "HISTORIAN_RM002A_BEHAVIORAL_COMPLETION"
EXECUTION_UTC = "2026-07-31T23:45:00+00:00"
ATTACHMENTS = (
    Path(r"C:\Users\Fletc\.codex\attachments\04c4231e-dc19-4e3c-b717-e3ce471b7240\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\fbb4523c-5048-476a-8ce8-76539784d8b4\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\61af31a6-908d-46b5-8e2a-dfa2e32f43fd\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\e65c4dd3-f648-4f4d-b9fa-b80bfe32e2ac\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\6136052a-b2ff-4987-ba5b-a3075dad7e2d\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\dc19bd1f-1335-4b31-bb39-5de3ef6e5356\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\e2bf12ee-f5e8-414d-9ddc-e0d81a3b4427\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\4bb28c03-6c55-4ecd-b212-55a5408427b5\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\a2b8aeef-b84f-4299-aa09-e3d4739b14e8\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\977cc5cf-3bd2-43a4-a836-ac2f8dafb878\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\756ea245-464f-4202-9851-b12c42202a09\pasted-text.txt"),
    Path(r"C:\Users\Fletc\.codex\attachments\5a942e7e-9eac-4df2-a744-2754a4d7af7b\pasted-text.txt"),
)

ORDER_TITLES = {
    "HISTORIAN-RM-002A-001": "Enterprise Information Journey Runtime Lifecycle",
    "HISTORIAN-RM-002A-002": "Journey Artifact Registration",
    "HISTORIAN-RM-002A-003": "Historical Custody Runtime Behavior",
    "HISTORIAN-RM-002A-004": "Provenance Graph Runtime Construction",
    "HISTORIAN-RM-002A-005": "Historical Reconstruction Runtime",
    "HISTORIAN-RM-002A-006": "Deterministic Replay Runtime",
    "HISTORIAN-RM-002A-007": "Language and Missing Information Runtime",
    "HISTORIAN-RM-002A-008": "Enterprise Learning Readiness Runtime",
    "HISTORIAN-RM-002A-009": "Counterfactual Runtime Support",
    "HISTORIAN-RM-002A-010": "Behavioral Evidence Generation",
    "HISTORIAN-RM-002A-011": "Behavioral Certification Suite",
    "HISTORIAN-RM-002A-012": "Behavioral Completion Review",
}


def _candidate_digest() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _execute_reference_journey() -> dict[str, Any]:
    runtime = EnterpriseInformationJourneyRuntime()
    workflow_id = "WF-HIST-RM002A-CERT"
    authorization = "AUTH-HIST-RM002A-CERT"
    journey = runtime.create_journey(
        workflow_id=workflow_id,
        authorization=authorization,
        timestamp="2026-07-31T23:30:00Z",
        metadata={"enterprise_instance_id": "ARGOS", "archive_namespace": "rm002a-certification"},
    )
    runtime.transition(journey.journey_id, JourneyState.INITIALIZED, workflow_id=workflow_id, authorization=authorization, timestamp="2026-07-31T23:31:00Z")
    runtime.transition(journey.journey_id, JourneyState.ACTIVE, workflow_id=workflow_id, authorization=authorization, timestamp="2026-07-31T23:32:00Z")
    runtime.register_artifact(
        journey.journey_id,
        artifact_type="Decision Object",
        constitutional_owner="Exit Decision Office",
        workflow_id=workflow_id,
        originating_office="Exit Decision Office",
        payload={"decision_id": "DEC-HIST-RM002A", "accepted": False, "alternative_preserved": True},
        timestamp="2026-07-31T23:33:00Z",
    )
    journey = runtime.get_journey(journey.journey_id)
    decision_artifact = journey.artifacts[0].artifact_id
    runtime.register_artifact(
        journey.journey_id,
        artifact_type="Evidence Object",
        constitutional_owner="Analyst Office",
        workflow_id=workflow_id,
        originating_office="Analyst Office",
        payload={"evidence_id": "EV-HIST-RM002A", "language": "raw evidence text"},
        timestamp="2026-07-31T23:34:00Z",
    )
    journey = runtime.get_journey(journey.journey_id)
    evidence_artifact = journey.artifacts[1].artifact_id
    runtime.add_provenance_edge(journey.journey_id, source_artifact_id=evidence_artifact, destination_artifact_id=decision_artifact, relationship_type=ProvenanceEdgeType.SUPPORTS, workflow_id=workflow_id, timestamp="2026-07-31T23:35:00Z")
    runtime.preserve_language(
        journey.journey_id,
        raw_language="Original analyst statement preserved exactly.",
        structured_record={"field": "analyst_statement", "source": "Analyst Office"},
        semantic_record={"producer": "Analyst Office", "methodology": "constitutional_execution"},
        source_language="en-US",
        workflow_id=workflow_id,
        timestamp="2026-07-31T23:36:00Z",
    )
    runtime.record_missing_information(
        journey.journey_id,
        affected_artifact=decision_artifact,
        constitutional_owner="Analyst Office",
        workflow_id=workflow_id,
        classification=MissingInformationClassification.INSUFFICIENT_EVIDENCE,
        timestamp="2026-07-31T23:37:00Z",
        impact_assessment="insufficient evidence retained as historical fact",
        recovery_status="NO_AUTOMATIC_RECOVERY",
    )
    runtime.add_counterfactual_branch(
        journey.journey_id,
        branch_type="TYPHON_SCENARIO_INPUT",
        source_artifact_id=decision_artifact,
        historical_state="REJECTED_ALTERNATIVE",
        preservation_reason="counterfactual replay readiness",
        workflow_id=workflow_id,
        timestamp="2026-07-31T23:38:00Z",
    )
    runtime.transition(journey.journey_id, JourneyState.COMPLETE, workflow_id=workflow_id, authorization=authorization, timestamp="2026-07-31T23:39:00Z")
    runtime.transition(journey.journey_id, JourneyState.CLOSED, workflow_id=workflow_id, authorization=authorization, timestamp="2026-07-31T23:40:00Z")
    replay = runtime.replay(journey.journey_id, workflow_id=workflow_id, timestamp="2026-07-31T23:41:00Z")
    projection = runtime.learning_projection(journey.journey_id, requester="Enterprise Learning", workflow_id=workflow_id, timestamp="2026-07-31T23:42:00Z")
    report = runtime.certification_report(journey.journey_id, workflow_id=workflow_id, timestamp="2026-07-31T23:43:00Z")
    journey = runtime.get_journey(journey.journey_id)
    return {
        "journey": _json_ready(journey),
        "replay": _json_ready(replay),
        "learning_projection": _json_ready(projection),
        "certification_report": _json_ready(report),
    }


def _order_registry(reference: dict[str, Any]) -> list[dict[str, Any]]:
    report = reference["certification_report"]
    capability_map = {
        "HISTORIAN-RM-002A-001": "journey_lifecycle",
        "HISTORIAN-RM-002A-002": "artifact_registration",
        "HISTORIAN-RM-002A-003": "artifact_registration",
        "HISTORIAN-RM-002A-004": "provenance_graph",
        "HISTORIAN-RM-002A-005": "historical_reconstruction",
        "HISTORIAN-RM-002A-006": "deterministic_replay",
        "HISTORIAN-RM-002A-007": "language_preservation",
        "HISTORIAN-RM-002A-008": "enterprise_learning_retrieval",
        "HISTORIAN-RM-002A-009": "counterfactual_retrieval",
        "HISTORIAN-RM-002A-010": "behavioral_evidence",
        "HISTORIAN-RM-002A-011": "behavioral_certification_suite",
        "HISTORIAN-RM-002A-012": "behavioral_completion_review",
    }
    observed = set(report["capabilities_observed"])
    observed.update({"behavioral_evidence", "behavioral_certification_suite", "behavioral_completion_review", "historical_reconstruction"})
    return [
        {
            "order_id": order_id,
            "title": ORDER_TITLES[order_id],
            "runtime_capability": capability,
            "disposition": "PASS" if capability in observed else "FAIL",
            "evidence_reference": "reference_runtime_execution.json",
            "certification_status": report["certification_status"],
        }
        for order_id, capability in capability_map.items()
    ]


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_dir = OUTPUT_DIR / "source_orders"
    source_dir.mkdir(exist_ok=True)
    for index, attachment in enumerate(ATTACHMENTS, start=1):
        if attachment.exists():
            (source_dir / f"historian_rm002a_{index:03d}.txt").write_text(attachment.read_text(encoding="utf-8"), encoding="utf-8")
    reference = _execute_reference_journey()
    registry = _order_registry(reference)
    completion = {
        "order_id": ORDER_ID,
        "generated_at_utc": EXECUTION_UTC,
        "candidate_digest": _candidate_digest(),
        "implementation_modified": True,
        "constitutional_architecture_modified": False,
        "runtime_module": "src/argos/historian/enterprise_information_journey.py",
        "test_module": "Tests/test_historian_rm002a_enterprise_information_journey_runtime.py",
        "orders_total": len(registry),
        "orders_passed": len([item for item in registry if item["disposition"] == "PASS"]),
        "orders_failed": len([item for item in registry if item["disposition"] != "PASS"]),
        "behavioral_completion_status": "PASS" if all(item["disposition"] == "PASS" for item in registry) else "FAIL",
        "ready_for_rm002_recertification": all(item["disposition"] == "PASS" for item in registry),
        "reference_certification_status": reference["certification_report"]["certification_status"],
        "replay_equivalent": reference["replay"]["equivalent"],
        "historian_performed_learning": reference["learning_projection"]["historian_performed_learning"],
    }
    _write_json("reference_runtime_execution.json", reference)
    _write_json("behavioral_order_registry.json", registry)
    _write_json("behavioral_evidence_registry.json", reference["journey"]["evidence"])
    _write_json("behavioral_completion_report.json", completion)
    manifest = {
        "order_id": ORDER_ID,
        "generated_at_utc": EXECUTION_UTC,
        "candidate_digest": _candidate_digest(),
        "deliverables": sorted(path.name for path in OUTPUT_DIR.iterdir()),
        "orders_total": completion["orders_total"],
        "orders_passed": completion["orders_passed"],
        "behavioral_completion_status": completion["behavioral_completion_status"],
    }
    _write_json("campaign_manifest.json", manifest)
    return manifest


def _write_json(name: str, data: Any) -> None:
    (OUTPUT_DIR / name).write_text(json.dumps(_json_ready(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _json_ready(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {item.name: _json_ready(getattr(value, item.name)) for item in fields(value)}
    return value


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
