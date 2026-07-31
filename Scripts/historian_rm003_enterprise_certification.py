from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ORDER_ID = "HISTORIAN-RM-003"
OUTPUT_DIR = Path("Documentation") / "HISTORIAN_RM003_ENTERPRISE_CERTIFICATION"
ATTACHMENT_PATH = Path(
    r"C:\Users\Fletc\.codex\attachments\433535f7-9dc8-4225-a131-ba2c01dde6f1\pasted-text.txt"
)
RM002_REPORT = Path("Documentation") / "HISTORIAN_RM002_IMPLEMENTATION_CERTIFICATION" / "implementation_completeness_report.json"
RM002_BLOCKERS = Path("Documentation") / "HISTORIAN_RM002_IMPLEMENTATION_CERTIFICATION" / "certification_blocker_registry.json"
MO001_BASELINE = Path("Documentation") / "HISTORIAN_MO001_INFORMATION_JOURNEY_HARDENING" / "enterprise_information_journey_baseline.json"
EXECUTION_UTC = "2026-07-31T23:05:00+00:00"


ORDERS = (
    ("HISTORIAN-RM-003-B01", "Constitutional Compliance Verification"),
    ("HISTORIAN-RM-003-B02", "Enterprise Integration Certification"),
    ("HISTORIAN-RM-003-B03", "Enterprise Information Journey Continuity Certification"),
    ("HISTORIAN-RM-003-B04", "Enterprise Historical Custody Certification"),
    ("HISTORIAN-RM-003-B05", "Provenance and Historical Graph Certification"),
    ("HISTORIAN-RM-003-B06", "Deterministic Replay Certification"),
    ("HISTORIAN-RM-003-B07", "Enterprise Learning Readiness Certification"),
    ("HISTORIAN-RM-003-B08", "Counterfactual Readiness Certification"),
    ("HISTORIAN-RM-003-B09", "Enterprise Regression Certification"),
    ("HISTORIAN-RM-003-B10", "Historical Integrity Certification"),
    ("HISTORIAN-RM-003-B11", "Certification Evidence Finalization"),
    ("HISTORIAN-RM-003-B12", "Constitutional Freeze and Operational Transition"),
)


@dataclass(frozen=True)
class EnterpriseCertificationOrder:
    order_id: str
    title: str
    disposition: str
    precondition_status: str
    objective_evidence: tuple[dict[str, Any], ...]
    certification_impact: str
    required_corrective_action: str


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_digest() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _source_evidence(evidence_id: str, path: Path, summary: str) -> dict[str, Any]:
    exists = path.exists()
    payload: dict[str, Any] = {
        "evidence_id": evidence_id,
        "path": str(path),
        "exists": exists,
        "summary": summary,
    }
    if exists:
        payload["sha256"] = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    return payload


def _orders(rm002: dict[str, Any], blockers: list[dict[str, Any]], baseline: dict[str, Any]) -> tuple[EnterpriseCertificationOrder, ...]:
    blocker_ids = tuple(rm002.get("blocking_findings", ()))
    evidence = (
        {
            "evidence_id": "HIST-RM003-EVID-RM002-GATE",
            "source": str(RM002_REPORT),
            "rm002_final_disposition": rm002.get("final_disposition"),
            "rm003_authorized": rm002.get("rm003_authorized"),
            "blocking_findings": blocker_ids,
        },
        {
            "evidence_id": "HIST-RM003-EVID-MO001-BASELINE",
            "source": str(MO001_BASELINE),
            "baseline_id": baseline.get("baseline_id"),
            "historian_prohibitions": baseline.get("historian_prohibitions", ()),
            "closure_gates": baseline.get("closure_gates", ()),
        },
        {
            "evidence_id": "HIST-RM003-EVID-BLOCKER-COUNT",
            "source": str(RM002_BLOCKERS),
            "blocker_count": len(blockers),
            "blocker_categories": sorted({item.get("category", "UNKNOWN") for item in blockers}),
        },
    )
    result: list[EnterpriseCertificationOrder] = []
    for order_id, title in ORDERS:
        if rm002.get("rm003_authorized") is True and rm002.get("final_disposition") == "PASS":
            disposition = "READY_FOR_EXECUTION"
            precondition = "SATISFIED"
            impact = "RM-003 may execute this enterprise certification order."
            action = "Execute the bounded enterprise certification order."
        else:
            disposition = "BLOCKED_PRECONDITION"
            precondition = "FAILED_RM002_IMPLEMENTATION_CERTIFICATION"
            impact = (
                "Enterprise certification cannot proceed without weakening ECS-003 because implementation "
                "certification remains fail-closed."
            )
            action = (
                "Complete Historian implementation remediation for all RM-002 blocking findings, regenerate "
                "RM-002 evidence, and re-evaluate RM-003 authorization."
            )
        result.append(
            EnterpriseCertificationOrder(
                order_id=order_id,
                title=title,
                disposition=disposition,
                precondition_status=precondition,
                objective_evidence=evidence,
                certification_impact=impact,
                required_corrective_action=action,
            )
        )
    return tuple(result)


def _json_ready(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return _json_ready(asdict(value))
    return value


def _write_json(name: str, data: Any) -> None:
    (OUTPUT_DIR / name).write_text(json.dumps(_json_ready(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rm002 = _load_json(RM002_REPORT)
    blockers = _load_json(RM002_BLOCKERS)
    baseline = _load_json(MO001_BASELINE)
    orders = _orders(rm002, blockers, baseline)
    blocked = tuple(order.order_id for order in orders if order.disposition == "BLOCKED_PRECONDITION")

    if ATTACHMENT_PATH.exists():
        (OUTPUT_DIR / "source_order.txt").write_text(ATTACHMENT_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    _write_json("enterprise_certification_order_registry.json", orders)
    for order in orders:
        _write_json(f"{order.order_id.lower().replace('-', '_')}.json", order)
    _write_json(
        "rm003_precondition_gate_report.json",
        {
            "order_id": ORDER_ID,
            "generated_at_utc": EXECUTION_UTC,
            "candidate_digest": _candidate_digest(),
            "required_precondition": "HISTORIAN-RM-002 implementation certification PASS and rm003_authorized true",
            "observed_rm002_final_disposition": rm002.get("final_disposition"),
            "observed_rm003_authorized": rm002.get("rm003_authorized"),
            "rm002_blocking_findings": rm002.get("blocking_findings", ()),
            "precondition_gate": "FAILED",
            "enterprise_certification_execution_authorized": False,
            "constitutional_freeze_authorized": False,
            "operational_transition_authorized": False,
            "hist_ecs003_audit_002_authorized": False,
            "decision": "HISTORIAN-RM-003 is blocked by failed RM-002 implementation certification.",
        },
    )
    _write_json(
        "enterprise_certification_blocker_registry.json",
        [
            {
                "blocker_id": "HIST-RM003-BLOCKER-RM002-GATE",
                "severity": "BLOCKING",
                "source_order": "HISTORIAN-RM-002",
                "source_disposition": rm002.get("final_disposition"),
                "source_findings": rm002.get("blocking_findings", ()),
                "affected_rm003_orders": blocked,
                "certification_impact": "Blocks final constitutional certification, freeze, operational transition, and HISTORIAN-ECS003-AUDIT-002 initiation.",
                "required_corrective_action": "Remediate and recertify RM-002 before RM-003 enterprise certification execution.",
            }
        ],
    )
    _write_json(
        "permanent_certification_package_index.json",
        {
            "order_id": ORDER_ID,
            "candidate_digest": _candidate_digest(),
            "included_evidence": (
                _source_evidence("HIST-RM003-EVID-SOURCE-ORDER", ATTACHMENT_PATH, "User-provided RM-003 execution order."),
                _source_evidence("HIST-RM003-EVID-RM002-REPORT", RM002_REPORT, "RM-002 implementation certification report."),
                _source_evidence("HIST-RM003-EVID-RM002-BLOCKERS", RM002_BLOCKERS, "RM-002 blocker registry."),
                _source_evidence("HIST-RM003-EVID-MO001-BASELINE", MO001_BASELINE, "MO-001 hardened Enterprise Information Journey baseline."),
            ),
            "package_disposition": "PRECONDITION_BLOCKED_CERTIFICATION_RECORD",
        },
    )
    _write_json(
        "constitutional_freeze_decision.json",
        {
            "order_id": "HISTORIAN-RM-003-B12",
            "constitutional_freeze_declared": False,
            "operational_transition_authorized": False,
            "future_modifications_restricted_to_mo_campaigns": "NOT_ACTIVATED_BY_RM003",
            "reason": "RM-003 predecessor orders are blocked because RM-002 implementation certification failed closed.",
        },
    )
    _write_json(
        "completion_report.json",
        {
            "order_id": ORDER_ID,
            "generated_at_utc": EXECUTION_UTC,
            "candidate_digest": _candidate_digest(),
            "program_scope": "enterprise_integration_certification",
            "constitutional_architecture_modified": False,
            "implementation_modified": False,
            "new_behavior_introduced": False,
            "orders_total": len(orders),
            "orders_blocked": len(blocked),
            "orders_passed": len([order for order in orders if order.disposition == "PASS"]),
            "final_certification": "NOT_CERTIFIED_PRECONDITION_FAILED",
            "constitutional_freeze_authorized": False,
            "operational_authorization": False,
            "hist_ecs003_audit_002_authorized": False,
            "required_next_step": "Historian implementation remediation for RM-002 blockers.",
        },
    )
    manifest = {
        "order_id": ORDER_ID,
        "generated_at_utc": EXECUTION_UTC,
        "candidate_digest": _candidate_digest(),
        "deliverables": sorted(path.name for path in OUTPUT_DIR.iterdir() if path.is_file()),
        "orders_total": len(orders),
        "orders_blocked": len(blocked),
        "final_certification": "NOT_CERTIFIED_PRECONDITION_FAILED",
    }
    _write_json("campaign_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
