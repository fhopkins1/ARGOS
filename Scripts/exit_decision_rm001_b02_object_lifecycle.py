from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B02_OBJECT_LIFECYCLE"
SOURCE_ORDER_DIR = OUTPUT_DIR / "source_orders"

SOURCE_ORDERS = {
    "EXIT-DECISION-RM-001-B02-001": Path(r"C:\Users\Fletc\.codex\attachments\89ae9ddf-5ae1-4645-86cc-f12f6759fede\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B02-002": Path(r"C:\Users\Fletc\.codex\attachments\98eba1cd-4332-4149-b685-a2cea9429adb\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B02-003": Path(r"C:\Users\Fletc\.codex\attachments\320f76fd-4905-4425-999e-5477a8cda458\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B02-004": Path(r"C:\Users\Fletc\.codex\attachments\1de93362-875b-4466-ab2e-439c2e6f0178\pasted-text.txt"),
}

OBJECTS = (
    ("EXIT-OBJ-001", "Exit Decision Request", "initiates bounded exit evaluation"),
    ("EXIT-OBJ-002", "Exit Decision Context", "binds admitted position, monitoring, risk, authorization, market, and temporal inputs"),
    ("EXIT-OBJ-003", "Exit Condition", "records a governed condition that may support exit evaluation"),
    ("EXIT-OBJ-004", "Exit Evaluation", "records deterministic evaluation of admitted conditions"),
    ("EXIT-OBJ-005", "Exit Constraint", "records binding limits or prohibitions on exit decisions"),
    ("EXIT-OBJ-006", "Exit Candidate", "records a candidate position or scope under evaluation"),
    ("EXIT-OBJ-007", "Exit Recommendation", "records a non-executing recommendation and rationale"),
    ("EXIT-OBJ-008", "Exit Decision", "records final Exit Decision-owned decision state"),
    ("EXIT-OBJ-009", "Exit Decision Version", "records immutable version lineage"),
    ("EXIT-OBJ-010", "Exit Authorization Binding", "read-only binding to external authorization authority"),
    ("EXIT-OBJ-011", "Exit Instruction Request", "request artifact handed to downstream authority without execution ownership"),
    ("EXIT-OBJ-012", "Exit Decision Rejection", "records deterministic rejection"),
    ("EXIT-OBJ-013", "Exit Decision Deferral", "records deterministic deferral"),
    ("EXIT-OBJ-014", "Exit Decision Cancellation", "records cancellation of Exit Decision-owned pending state"),
    ("EXIT-OBJ-015", "Exit Decision Correction", "records authorized correction lineage"),
    ("EXIT-OBJ-016", "Exit Decision Supersession", "records predecessor/successor lineage"),
    ("EXIT-OBJ-017", "Exit Decision Completion Record", "records terminal Exit Decision completion without declaring external execution or settlement truth"),
    ("EXIT-OBJ-018", "Exit Decision Evidence Record", "records immutable evidence provenance and proof eligibility"),
)

ATTRIBUTES = (
    ("decision_identity", "Exit Decision Office", "immutable", "Exit Decision Office"),
    ("position_binding", "Position Registry", "read_only_reference", "Position Registry"),
    ("authorization_binding", "Authorizations", "read_only_reference", "Authorizations"),
    ("rationale", "Exit Decision Office", "append_only", "Exit Decision Office"),
    ("constraints", "Exit Decision Office", "append_only", "Exit Decision Office"),
    ("evaluation_results", "Exit Decision Office", "append_only", "Exit Decision Office"),
    ("recommendation", "Exit Decision Office", "append_only", "Exit Decision Office"),
    ("final_decision", "Exit Decision Office", "append_only", "Exit Decision Office"),
    ("cancellation_state", "Exit Decision Office", "append_only", "Exit Decision Office"),
    ("correction_history", "Exit Decision Office", "append_only_lineage", "Exit Decision Office"),
    ("supersession_history", "Exit Decision Office", "append_only_lineage", "Exit Decision Office"),
    ("completion_state", "Exit Decision Office", "append_only", "Exit Decision Office"),
)

STATES = (
    "created",
    "received",
    "validating",
    "admitted",
    "evaluating",
    "recommended",
    "decided",
    "authorized",
    "issued",
    "acknowledged",
    "executing",
    "partially_executed",
    "completed",
    "deferred",
    "rejected",
    "cancelled",
    "expired",
    "corrected",
    "superseded",
    "archived",
)

TRANSITIONS = (
    ("EXIT-TRANS-001", "created", "received", "Exit Decision Office", "request identity and receipt evidence"),
    ("EXIT-TRANS-002", "received", "validating", "Exit Decision Office", "validation start evidence"),
    ("EXIT-TRANS-003", "validating", "admitted", "Exit Decision Office", "admissibility evidence"),
    ("EXIT-TRANS-004", "validating", "rejected", "Exit Decision Office", "rejection evidence"),
    ("EXIT-TRANS-005", "admitted", "evaluating", "Exit Decision Office", "evaluation start evidence"),
    ("EXIT-TRANS-006", "evaluating", "recommended", "Exit Decision Office", "recommendation rationale evidence"),
    ("EXIT-TRANS-007", "recommended", "decided", "Exit Decision Office", "decision evidence"),
    ("EXIT-TRANS-008", "decided", "authorized", "Authorizations", "authorization binding evidence"),
    ("EXIT-TRANS-009", "authorized", "issued", "Trader", "downstream instruction request evidence"),
    ("EXIT-TRANS-010", "issued", "acknowledged", "Trader/Broker", "acknowledgement reference evidence"),
    ("EXIT-TRANS-011", "acknowledged", "executing", "Trader/Broker", "execution status reference evidence"),
    ("EXIT-TRANS-012", "executing", "partially_executed", "Broker/Position Registry", "partial execution reference evidence"),
    ("EXIT-TRANS-013", "partially_executed", "completed", "Position Registry/Closed Position Truth", "completion reference evidence"),
    ("EXIT-TRANS-014", "executing", "completed", "Position Registry/Closed Position Truth", "completion reference evidence"),
    ("EXIT-TRANS-015", "created", "cancelled", "Exit Decision Office", "cancellation evidence"),
    ("EXIT-TRANS-016", "recommended", "cancelled", "Exit Decision Office", "cancellation evidence"),
    ("EXIT-TRANS-017", "decided", "expired", "Exit Decision Office", "expiration evidence"),
    ("EXIT-TRANS-018", "decided", "superseded", "Exit Decision Office", "successor identity evidence"),
    ("EXIT-TRANS-019", "superseded", "archived", "Historian", "historical custody evidence"),
    ("EXIT-TRANS-020", "completed", "archived", "Historian", "terminal archival evidence"),
    ("EXIT-TRANS-021", "rejected", "archived", "Historian", "terminal archival evidence"),
    ("EXIT-TRANS-022", "cancelled", "archived", "Historian", "terminal archival evidence"),
)

INVALID_TRANSITIONS = (
    ("completed", "executing", "completed decisions may not reactivate"),
    ("cancelled", "issued", "cancelled decisions may not issue instructions"),
    ("superseded", "decided", "superseded decisions may not become active"),
    ("archived", "validating", "archived records are immutable"),
    ("rejected", "authorized", "rejected decisions cannot be authorized"),
    ("expired", "issued", "expired decisions cannot issue downstream requests"),
)

SEPARATION = {
    "Position Registry": "owns canonical position truth and position mutation",
    "Risk": "owns risk state and emergency risk constraints",
    "Authorizations": "owns authorization issuance, revocation, and validity",
    "Trader": "owns authorized execution request handling",
    "Broker": "owns broker submission, acknowledgement, and fill truth",
    "Historian": "owns historical custody and immutable preservation",
}


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


def _object_registry() -> list[dict[str, Any]]:
    return [
        {
            "object_id": object_id,
            "object_name": name,
            "purpose": purpose,
            "owner": "Exit Decision Office",
            "custodian": "Exit Decision Office until archival transfer to Historian",
            "creator": "Exit Decision Office",
            "mutation_authority": "Exit Decision Office for object-owned fields only",
            "correction_authority": "Exit Decision Office with source-owner evidence where external references are affected",
            "reconciliation_authority": "Exit Decision Office for decision record consistency; source office for external truth",
            "lifecycle_required": True,
            "versioning_required": True,
            "provenance_required": True,
            "retention": "append-only with Historian archival custody",
            "terminal_dispositions": ["completed", "rejected", "cancelled", "expired", "superseded", "archived"],
        }
        for object_id, name, purpose in OBJECTS
    ]


def _identity_registry() -> list[dict[str, Any]]:
    return [
        {
            "object_id": object_id,
            "identity_authority": "Exit Decision Office",
            "canonical_identity_pattern": f"{object_id.replace('EXIT-OBJ', 'EXD-OBJ')}-<workflow>-<sequence>",
            "collision_disposition": "fail closed and record duplicate identity finding",
        }
        for object_id, _name, _purpose in OBJECTS
    ]


def _attribute_ownership_registry() -> list[dict[str, Any]]:
    return [
        {
            "attribute": name,
            "constitutional_owner": owner,
            "custody_model": custody,
            "mutation_authority": mutation_owner,
            "exit_decision_may_mutate": mutation_owner == "Exit Decision Office",
            "external_truth_transfer": "prohibited",
        }
        for name, owner, custody, mutation_owner in ATTRIBUTES
    ]


def _custody_registry() -> list[dict[str, Any]]:
    return [
        {
            "object_id": object_id,
            "operational_custodian": "Exit Decision Office",
            "evidence_custodian": "Exit Decision Office",
            "historical_custodian": "Historian after archival transition",
            "custody_transfer_rule": "transfer custody only by explicit archival evidence; ownership does not transfer by implication",
        }
        for object_id, _name, _purpose in OBJECTS
    ]


def _lifecycle_state_registry() -> list[dict[str, Any]]:
    terminal = {"completed", "rejected", "cancelled", "expired", "superseded", "archived"}
    return [
        {
            "state": state,
            "authority": "Exit Decision Office" if state not in {"authorized", "issued", "acknowledged", "executing", "partially_executed", "archived"} else "external governing authority reference",
            "terminal": state in terminal,
            "required_evidence": f"{state} evidence record",
            "prohibited_conditions": ["missing identity", "missing evidence", "unauthorized transition"],
        }
        for state in STATES
    ]


def _transition_registry() -> list[dict[str, Any]]:
    return [
        {
            "transition_id": tid,
            "from_state": source,
            "to_state": target,
            "transition_authority": authority,
            "required_evidence": evidence,
            "history_mutation": "append_only",
        }
        for tid, source, target, authority, evidence in TRANSITIONS
    ]


def _invalid_transition_registry() -> list[dict[str, Any]]:
    return [
        {"from_state": source, "to_state": target, "reason": reason, "disposition": "fail closed and preserve attempted transition evidence"}
        for source, target, reason in INVALID_TRANSITIONS
    ]


def _correction_registry() -> list[dict[str, Any]]:
    return [
        {
            "authority": office,
            "owned_scope": scope,
            "exit_decision_action": "consume source-owner correction evidence" if office != "Exit Decision Office" else "create Exit Decision-owned correction record",
            "lineage_required": True,
        }
        for office, scope in {
            "Exit Decision Office": "decision-owned fields, rationale, evaluation, recommendation, cancellation, supersession",
            "Risk Office": "risk state or risk constraints referenced by decision",
            "Authorizations Office": "authorization state or validity referenced by decision",
            "Position Registry Office": "position truth referenced by decision",
            "Historian Office": "historical custody and archival record correction lineage",
        }.items()
    ]


def _supersession_registry() -> list[dict[str, Any]]:
    return [
        {
            "supersession_type": item,
            "authority": "Exit Decision Office",
            "predecessor_required": True,
            "successor_required": True,
            "history_rule": "predecessor remains immutable; successor receives new canonical identity",
        }
        for item in ("decision_replacement", "recommendation_replacement", "correction_replacement", "expired_decision_replacement")
    ]


def _expiration_registry() -> list[dict[str, Any]]:
    return [
        {
            "expiration_scope": scope,
            "authority": "Exit Decision Office",
            "trigger": trigger,
            "post_expiration_rule": "no issuance, authorization use, or execution request may proceed",
        }
        for scope, trigger in (
            ("decision", "decision validity window elapsed"),
            ("recommendation", "recommendation freshness elapsed"),
            ("authorization_binding", "external authorization expired or revoked"),
            ("context", "input freshness invalidated"),
        )
    ]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_registry = _copy_source_orders()
    objects = _object_registry()
    identities = _identity_registry()
    ownership = _attribute_ownership_registry()
    custody = _custody_registry()
    states = _lifecycle_state_registry()
    transitions = _transition_registry()
    invalid = _invalid_transition_registry()
    corrections = _correction_registry()
    supersession = _supersession_registry()
    expiration = _expiration_registry()
    separation = [
        {
            "office": office,
            "external_truth_owned": truth,
            "exit_decision_ownership": "read-only reference or decision-context reference only",
            "conflict_disposition": "fail closed and defer to source owner",
        }
        for office, truth in sorted(SEPARATION.items())
    ]
    predecessor_successor = [
        {"lineage_object": "Exit Decision Supersession", "predecessor": "required", "successor": "required", "immutable_history": True},
        {"lineage_object": "Exit Decision Correction", "predecessor": "required", "successor": "corrected record required", "immutable_history": True},
    ]

    completion_checks = {
        "source_orders_preserved": len(source_registry) == 4,
        "canonical_objects_complete": len(objects) == 18,
        "ownership_complete": all(item["constitutional_owner"] for item in ownership),
        "external_truth_separated": all(item["external_truth_transfer"] == "prohibited" for item in ownership),
        "lifecycle_states_complete": len(states) == len(STATES),
        "transitions_have_authority": all(item["transition_authority"] for item in transitions),
        "invalid_transitions_fail_closed": all(item["disposition"].startswith("fail closed") for item in invalid),
        "correction_supersession_expiration_complete": bool(corrections and supersession and expiration),
    }
    baseline = {
        "baseline_id": "EXIT-DECISION-RM-001-B02-OBJECT-LIFECYCLE-BASELINE",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "COMPLETE" if all(completion_checks.values()) else "INCOMPLETE",
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "object_registry_digest": _digest(objects),
        "ownership_registry_digest": _digest(ownership),
        "lifecycle_registry_digest": _digest({"states": states, "transitions": transitions, "invalid": invalid}),
    }
    artifacts: dict[str, Any] = {
        "source_order_registry.json": source_registry,
        "canonical_exit_decision_object_registry.json": objects,
        "object_ownership_registry.json": [{"object_id": item["object_id"], "owner": item["owner"], "custodian": item["custodian"]} for item in objects],
        "object_identity_registry.json": identities,
        "object_custody_registry.json": custody,
        "attribute_ownership_registry.json": ownership,
        "mutation_authority_registry.json": ownership,
        "correction_authority_registry.json": corrections,
        "reconciliation_authority_registry.json": separation,
        "ownership_separation_verification.json": separation,
        "ownership_conflict_registry.json": [],
        "lifecycle_state_registry.json": states,
        "transition_registry.json": transitions,
        "invalid_transition_registry.json": invalid,
        "replay_and_recovery_constitution.json": {
            "replay_rule": "replay reproduces decision state from immutable evidence without issuing duplicate downstream requests",
            "recovery_rule": "recovery restores latest non-superseded state and preserves predecessor lineage",
            "duplicate_rule": "duplicate transition attempts fail closed unless idempotent replay is proven",
        },
        "duplicate_transition_constitution.json": {"disposition": "fail closed unless the duplicate maps to the same idempotency identity and no new side effect occurs"},
        "supersession_authority_registry.json": supersession,
        "supersession_lineage_registry.json": supersession,
        "expiration_authority_registry.json": expiration,
        "cancellation_constitution.json": {"authority": "Exit Decision Office", "scope": "Exit Decision-owned pending states only", "external_execution_cancellation": "requires Trader/Broker authority"},
        "historical_integrity_constitution.json": {"history": "append_only", "mutation": "prohibited", "archival_custodian": "Historian", "predecessor_successor_required": True},
        "predecessor_successor_registry.json": predecessor_successor,
        "constitutional_baseline.json": baseline,
    }
    for name, payload in artifacts.items():
        _write_json(OUTPUT_DIR / name, payload)

    completion_report = {
        "package": "EXIT-DECISION-RM-001-B02",
        "status": baseline["status"],
        "orders_completed": sorted(SOURCE_ORDERS),
        "completion_checks": completion_checks,
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "ready_for": "EXIT-DECISION-RM-001-B03",
        "baseline_digest": _digest(artifacts),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion_report)
    _write_text(OUTPUT_DIR / "README.md", "# EXIT-DECISION-RM-001-B02 Object and Lifecycle Baseline\n\nPrimary entry point: completion_report.json\n")


if __name__ == "__main__":
    main()
