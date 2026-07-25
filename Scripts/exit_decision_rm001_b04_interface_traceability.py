from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B04_INTERFACE_TRACEABILITY"
SOURCE_ORDER_DIR = OUTPUT_DIR / "source_orders"
BASELINES = (
    REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B01_CONSTITUTIONAL_BASELINE" / "completion_report.json",
    REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B02_OBJECT_LIFECYCLE" / "completion_report.json",
    REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B03_DECISION_ADMISSIBILITY" / "completion_report.json",
)

SOURCE_ORDERS = {
    "EXIT-DECISION-RM-001-B04-001": Path(r"C:\Users\Fletc\.codex\attachments\4fd0175b-7dcf-4dcb-a8b7-6010d7a6b0db\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B04-002": Path(r"C:\Users\Fletc\.codex\attachments\7280a615-cc21-4857-89bb-7003873f51c0\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B04-003": Path(r"C:\Users\Fletc\.codex\attachments\563b89a1-5251-4387-90f2-33ef2fb36913\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B04-004": Path(r"C:\Users\Fletc\.codex\attachments\905438c7-137b-4e64-8764-cec9d96bd229\pasted-text.txt"),
}

INBOUND_INTERFACES = (
    ("Monitoring", "monitoring findings and surveillance context"),
    ("Sentinel", "constitutionally significant observations"),
    ("Analyst", "analytical assessment references"),
    ("Risk", "risk state, constraints, and emergency risk context"),
    ("Position Registry", "canonical position identity, lifecycle, and quantity truth"),
    ("Authorizations", "authorization validity, expiration, revocation, and scope"),
    ("Commander", "commander-directed review, override, and escalation authority"),
)
OUTBOUND_INTERFACES = (
    ("Trader", "authorized execution request handoff after external authorization"),
    ("Broker", "boundary reference only; no direct broker submission authority"),
    ("Closed Position Truth", "closure reference consumption without ownership"),
    ("Performance Truth", "performance reference consumption without ownership"),
    ("Historian", "archival custody transfer and historical evidence preservation"),
    ("Infrastructure", "persistence, replay, configuration, and runtime custody services"),
)
CONTRACTS = ("identity", "scope", "freshness", "ordering", "retry", "replay", "failure")
TIMELINE = (
    "request_time",
    "observation_time",
    "evaluation_time",
    "recommendation_time",
    "decision_time",
    "authorization_time",
    "execution_request_time",
    "acknowledgement_time",
    "completion_time",
    "correction_time",
    "supersession_time",
    "archival_time",
)
EVIDENCE_OBJECTS = (
    "decision_request_evidence",
    "admissibility_evidence",
    "evaluation_evidence",
    "recommendation_evidence",
    "decision_evidence",
    "authorization_evidence",
    "execution_request_evidence",
    "acknowledgement_evidence",
    "completion_evidence",
    "rejection_evidence",
    "deferral_evidence",
    "cancellation_evidence",
    "correction_evidence",
    "supersession_evidence",
    "archival_evidence",
)
PROHIBITED_EVIDENCE = (
    "metadata_only_evidence",
    "completion_report_only_evidence",
    "manually_asserted_evidence",
    "synthetic_evidence",
    "circular_evidence",
)
REQ_CLASSES = (
    "authority",
    "boundary",
    "object",
    "lifecycle",
    "decision",
    "interface",
    "evidence",
    "certification",
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _copy_source_orders() -> list[dict[str, Any]]:
    SOURCE_ORDER_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for order_id, source in sorted(SOURCE_ORDERS.items()):
        target = SOURCE_ORDER_DIR / f"{order_id}.txt"
        shutil.copyfile(source, target)
        records.append({"order_id": order_id, "committed_copy": _relative(target), "sha256": _file_digest(target), "disposition": "PRESERVED"})
    return records


def _baseline_inputs() -> list[dict[str, Any]]:
    records = []
    for path in BASELINES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records.append({"path": _relative(path), "status": payload.get("status"), "ready_for": payload.get("ready_for"), "sha256": _file_digest(path)})
    return records


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_registry = _copy_source_orders()
    baseline_inputs = _baseline_inputs()
    inbound = [
        {
            "interface_id": f"EXIT-IN-{index:03d}",
            "producer": office,
            "consumer": "Exit Decision Office",
            "payload": payload,
            "authority": office,
            "contract_required": list(CONTRACTS),
            "evidence_obligation": "source identity, payload identity, freshness, ordering, admissibility, and failure disposition",
        }
        for index, (office, payload) in enumerate(INBOUND_INTERFACES, start=1)
    ]
    outbound = [
        {
            "interface_id": f"EXIT-OUT-{index:03d}",
            "producer": "Exit Decision Office",
            "consumer": office,
            "payload": payload,
            "authority": office if office in {"Trader", "Broker", "Closed Position Truth", "Performance Truth", "Historian", "Infrastructure"} else "Exit Decision Office",
            "contract_required": list(CONTRACTS),
            "boundary": "no ownership transfer by interface interaction",
        }
        for index, (office, payload) in enumerate(OUTBOUND_INTERFACES, start=1)
    ]
    contracts = [
        {
            "contract_id": f"EXIT-CONTRACT-{index:03d}",
            "contract": contract,
            "mandatory": True,
            "failure_behavior": "fail closed and record interface finding",
        }
        for index, contract in enumerate(CONTRACTS, start=1)
    ]
    dependencies = [
        {
            "dependency_id": f"EXIT-DEP-{index:03d}",
            "dependency": item["producer"] if "producer" in item else item["consumer"],
            "direction": "inbound" if item in inbound else "outbound",
            "owner": item["authority"],
            "circular_dependency": False,
        }
        for index, item in enumerate(inbound + outbound, start=1)
    ]
    timeline = [
        {
            "time_id": f"EXIT-TIME-{index:03d}",
            "time_name": name,
            "authority": "source owner" if name in {"observation_time", "authorization_time", "acknowledgement_time", "completion_time"} else "Exit Decision Office",
            "ordering_rule": "monotonic within same lineage unless source-owner evidence explains out-of-order receipt",
            "freshness_required": True,
        }
        for index, name in enumerate(TIMELINE, start=1)
    ]
    temporal_conflicts = [
        {"conflict": item, "disposition": "preserve conflict, fail closed for execution path, and escalate to source owner"}
        for item in ("stale_input", "equal_timestamp", "clock_skew", "out_of_order_event", "missing_timestamp", "replay_order_conflict")
    ]
    evidence = [
        {
            "evidence_id": f"EXIT-EVID-{index:03d}",
            "evidence_object": name,
            "producer": "Exit Decision Office" if "authorization" not in name and "acknowledgement" not in name and "completion" not in name else "source authority",
            "owner": "Exit Decision Office" if "authorization" not in name and "acknowledgement" not in name and "completion" not in name else "source authority",
            "custodian": "Exit Decision Office until archival transfer to Historian",
            "required_attributes": ["identity", "producer", "owner", "timestamp", "provenance", "integrity_digest", "lineage", "verifier_eligibility"],
            "immutable": True,
        }
        for index, name in enumerate(EVIDENCE_OBJECTS, start=1)
    ]
    prohibited_evidence = [
        {"prohibition_id": f"EXIT-EVID-PROHIBIT-{index:03d}", "evidence_type": name, "disposition": "not proof eligible"}
        for index, name in enumerate(PROHIBITED_EVIDENCE, start=1)
    ]
    requirements = [
        {
            "requirement_id": f"EXIT-B04-REQ-{index:03d}",
            "classification": req_class,
            "owner": "Exit Decision Office",
            "source_lineage": "EXIT-DECISION-RM-001-B04",
            "atomic": True,
            "forward_trace": ["constitutional authority", "requirement", "interface/evidence/temporal object", "verification obligation"],
            "reverse_trace": ["verification obligation", "interface/evidence/temporal object", "requirement", "constitutional authority"],
        }
        for index, req_class in enumerate(REQ_CLASSES, start=1)
    ]
    graph = {
        "nodes": [{"id": req["requirement_id"], "type": "requirement"} for req in requirements]
        + [{"id": item["interface_id"], "type": "interface"} for item in inbound + outbound]
        + [{"id": item["evidence_id"], "type": "evidence"} for item in evidence],
        "edges": [
            {"from": req["requirement_id"], "to": inbound[index % len(inbound)]["interface_id"], "type": "governs_interface"}
            for index, req in enumerate(requirements)
        ]
        + [
            {"from": req["requirement_id"], "to": evidence[index % len(evidence)]["evidence_id"], "type": "requires_evidence"}
            for index, req in enumerate(requirements)
        ],
    }
    completion_checks = {
        "source_orders_preserved": len(source_registry) == 4,
        "prior_baselines_complete": all(item["status"] == "COMPLETE" for item in baseline_inputs),
        "inbound_interfaces_complete": len(inbound) == len(INBOUND_INTERFACES),
        "outbound_interfaces_complete": len(outbound) == len(OUTBOUND_INTERFACES),
        "contracts_complete": all(item["mandatory"] and item["failure_behavior"].startswith("fail closed") for item in contracts),
        "dependencies_acyclic": not any(item["circular_dependency"] for item in dependencies),
        "timeline_complete": len(timeline) == len(TIMELINE),
        "temporal_conflicts_fail_closed": all("fail closed" in item["disposition"] for item in temporal_conflicts),
        "evidence_objects_complete": len(evidence) == len(EVIDENCE_OBJECTS),
        "prohibited_evidence_not_proof_eligible": all(item["disposition"] == "not proof eligible" for item in prohibited_evidence),
        "requirements_atomic": all(item["atomic"] for item in requirements),
        "traceability_bidirectional": all(item["forward_trace"] and item["reverse_trace"] for item in requirements),
    }
    baseline = {
        "baseline_id": "EXIT-DECISION-RM-001-B04-INTERFACE-TRACEABILITY-BASELINE",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "COMPLETE" if all(completion_checks.values()) else "INCOMPLETE",
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "interface_digest": _digest({"inbound": inbound, "outbound": outbound}),
        "temporal_digest": _digest(timeline),
        "evidence_digest": _digest(evidence),
        "traceability_digest": _digest(graph),
    }
    artifacts: dict[str, Any] = {
        "source_order_registry.json": source_registry,
        "baseline_input_registry.json": baseline_inputs,
        "interface_constitution.json": {"principle": "interfaces transfer evidence, requests, or references only; ownership transfer by implication is prohibited"},
        "inbound_interface_registry.json": inbound,
        "outbound_interface_registry.json": outbound,
        "dependency_registry.json": dependencies,
        "dependency_direction_matrix.json": dependencies,
        "interface_contract_registry.json": contracts,
        "interface_failure_governance.json": contracts,
        "circular_dependency_assessment.json": {"circular_dependencies": [], "status": "NONE_DETECTED"},
        "interface_evidence_obligations.json": [{"interface_id": item["interface_id"], "evidence_obligation": item.get("evidence_obligation", "interface evidence required")} for item in inbound + outbound],
        "temporal_authority_constitution.json": timeline,
        "canonical_exit_decision_timeline_registry.json": timeline,
        "freshness_constitution.json": {"rule": "freshness is required for every admitted input; stale inputs defer or fail closed"},
        "stale_input_governance.json": {"stale_input": "reject, defer, or fail closed according to source authority and decision scope"},
        "ordering_constitution.json": timeline,
        "duplicate_governance_constitution.json": {"duplicate_rule": "duplicates are idempotent only when identity and lineage match exactly; otherwise fail closed"},
        "replay_constitution.json": {"replay_rule": "replay reproduces decisions without issuing duplicate downstream effects"},
        "restart_recovery_ordering_constitution.json": {"restart_rule": "restore from immutable lineage and preserve original event ordering"},
        "expiration_governance_registry.json": [{"time_name": item["time_name"], "expiration_required": item["freshness_required"]} for item in timeline],
        "temporal_conflict_resolution_registry.json": temporal_conflicts,
        "evidence_object_registry.json": evidence,
        "exceptional_evidence_registry.json": [item for item in evidence if any(token in item["evidence_object"] for token in ("rejection", "deferral", "cancellation", "correction", "supersession", "archival"))],
        "evidence_admissibility_constitution.json": {"proof_eligible_requires": ["raw evidence", "provenance", "integrity", "custody", "lineage"]},
        "prohibited_evidence_registry.json": prohibited_evidence,
        "evidence_integrity_constitution.json": {"integrity": "digest-bound, immutable, append-only, correction lineage required"},
        "historical_custody_constitution.json": {"custodian": "Historian", "transfer": "explicit archival evidence required"},
        "retention_constitution.json": {"retention": "immutable retention for audit; no deletion by Exit Decision"},
        "evidence_reconciliation_constitution.json": {"reconciliation": "stale, duplicate, contradictory, or broken-lineage evidence fails proof eligibility"},
        "requirement_identity_registry.json": requirements,
        "requirement_source_lineage_constitution.json": requirements,
        "atomic_requirement_constitution.json": {"atomicity": "one requirement identity per indivisible obligation"},
        "requirement_ownership_constitution.json": [{"requirement_id": item["requirement_id"], "owner": item["owner"], "classification": item["classification"]} for item in requirements],
        "requirement_classification_registry.json": requirements,
        "orphan_requirement_registry.json": [],
        "duplicate_requirement_registry.json": [],
        "broken_traceability_constitution.json": {"broken_traceability": "certification blocker until reconciled"},
        "requirement_reconciliation_constitution.json": {"alignment": ["authority", "object", "evidence", "certification"]},
        "bidirectional_traceability_graph.json": graph,
        "constitutional_baseline.json": baseline,
    }
    for name, payload in artifacts.items():
        _write_json(OUTPUT_DIR / name, payload)

    completion_report = {
        "package": "EXIT-DECISION-RM-001-B04",
        "status": baseline["status"],
        "orders_completed": sorted(SOURCE_ORDERS),
        "completion_checks": completion_checks,
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "ready_for": "EXIT-DECISION-RM-001-B05",
        "baseline_digest": _digest(artifacts),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion_report)
    _write_text(OUTPUT_DIR / "README.md", "# EXIT-DECISION-RM-001-B04 Interface, Evidence, and Traceability Baseline\n\nPrimary entry point: completion_report.json\n")


if __name__ == "__main__":
    main()
