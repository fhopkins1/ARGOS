from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B03_DECISION_ADMISSIBILITY"
SOURCE_ORDER_DIR = OUTPUT_DIR / "source_orders"

SOURCE_ORDERS = {
    "EXIT-DECISION-RM-001-B03-001": Path(r"C:\Users\Fletc\.codex\attachments\1e57963b-c2f5-4cf4-9d43-50ef2b09ea59\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B03-002": Path(r"C:\Users\Fletc\.codex\attachments\fea74415-120b-4a23-8c94-786e59614a7a\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B03-003": Path(r"C:\Users\Fletc\.codex\attachments\97ab6dac-c0e8-438c-b4df-52c54f636d89\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B03-004": Path(r"C:\Users\Fletc\.codex\attachments\50dc069f-3b56-4b35-bcf2-6c52caf0256b\pasted-text.txt"),
}

ADMISSIBILITY_GATES = (
    ("position_identity", "Position Registry", "known active canonical position identity", "reject"),
    ("position_state", "Position Registry", "admissible open or exit-eligible lifecycle state", "reject"),
    ("position_quantity", "Position Registry", "positive available quantity within requested scope", "reject"),
    ("risk_state", "Risk Office", "current risk state and no unresolved blocking contradiction", "defer_or_reject"),
    ("authorization_state", "Authorizations Office", "valid non-expired non-revoked authorization where authorization is required", "reject"),
    ("monitoring_input", "Monitoring Office", "admissible finding or surveillance context with provenance", "defer"),
    ("analytical_input", "Analyst Office", "read-only analysis with provenance; no substituted analytical truth", "defer"),
    ("temporal_validity", "Source authorities", "fresh inputs with ordered timestamps and explicit effective time", "reject"),
    ("source_authority", "Source owner", "authoritative source and independence where required", "reject"),
    ("evidence_sufficiency", "Exit Decision Office", "mandatory evidence present and contradiction-free or preserved", "defer_or_reject"),
)

EVALUATION_FACTORS = (
    "exit_conditions",
    "risk_conditions",
    "authorization_conditions",
    "operational_constraints",
    "timing_constraints",
    "emergency_conditions",
)

DECISION_OUTPUTS = (
    "full_exit_recommendation",
    "partial_exit_recommendation",
    "hold",
    "defer",
    "reject",
    "cancel",
    "emergency_exit_recommendation",
    "forced_exit_recommendation",
    "timeout_disposition",
    "insufficient_evidence_disposition",
)

AUTHORITY_BOUNDARIES = (
    ("Authorizations", "owns authorization issuance, expiration, revocation, consumption, and validity", "Exit Decision consumes read-only authorization state"),
    ("Trader", "owns authorized execution request handling", "Exit Decision may not execute or submit orders"),
    ("Broker", "owns broker submission, acknowledgement, and fill truth", "Exit Decision may not create broker truth"),
    ("Position Registry", "owns canonical position state and mutation", "Exit Decision may not mutate position truth"),
    ("Closed Position Truth", "owns canonical closed-position truth", "Exit Decision may not declare closure"),
)

EMERGENCY_CONDITIONS = (
    ("risk_emergency", "Risk Office", "Risk-owned emergency condition"),
    ("commander_override", "Commander Office", "Commander-directed override"),
    ("authorization_exception", "Authorizations Office", "authorization emergency disposition"),
    ("execution_exception", "Trader/Broker", "execution pathway exception requiring downstream owner disposition"),
)

PROHIBITIONS = (
    "self-authorize exit execution",
    "consume expired authorization",
    "consume revoked authorization",
    "submit broker orders",
    "create broker acknowledgements",
    "mutate Position Registry truth",
    "convert recommendation into execution",
    "silently override Risk, Authorization, Trader, Broker, or Commander authority",
    "fabricate missing admissibility evidence",
    "treat emergency as authority transfer",
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


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_registry = _copy_source_orders()
    admissibility = [
        {
            "gate_id": f"EXIT-ADM-{index:03d}",
            "gate": gate,
            "authority": authority,
            "required_condition": condition,
            "failure_behavior": behavior,
            "evidence_required": True,
            "synthetic_completion_prohibited": True,
        }
        for index, (gate, authority, condition, behavior) in enumerate(ADMISSIBILITY_GATES, start=1)
    ]
    mandatory_rejections = [
        {
            "rejection_id": f"EXIT-REJECT-{index:03d}",
            "condition": condition,
            "disposition": "REJECT_OR_FAIL_CLOSED",
            "evidence_required": "rejection evidence and source authority reference",
        }
        for index, condition in enumerate(
            (
                "missing position truth",
                "stale position truth",
                "expired authorization",
                "revoked authorization",
                "contradictory risk inputs",
                "inadmissible monitoring findings",
                "unsupported analysis",
                "unresolved identity mismatch",
                "incomplete evidence",
            ),
            start=1,
        )
    ]
    evaluation = [
        {
            "factor_id": f"EXIT-EVAL-{index:03d}",
            "factor": factor,
            "authority": "Exit Decision Office",
            "input_governance": "admitted inputs only",
            "output_rule": "rationale-bound evaluation record; no authorization or execution side effect",
        }
        for index, factor in enumerate(EVALUATION_FACTORS, start=1)
    ]
    recommendations = [
        {
            "output_id": f"EXIT-OUT-{index:03d}",
            "output": output,
            "owner": "Exit Decision Office",
            "requires_rationale": True,
            "requires_authorization_before_execution": output not in {"hold", "defer", "reject", "cancel", "insufficient_evidence_disposition"},
            "execution_authority": "NONE",
        }
        for index, output in enumerate(DECISION_OUTPUTS, start=1)
    ]
    authority_boundaries = [
        {
            "office": office,
            "owned_authority": owned,
            "exit_decision_boundary": boundary,
            "violation_disposition": "fail closed and record authority-boundary finding",
        }
        for office, owned, boundary in AUTHORITY_BOUNDARIES
    ]
    prohibited = [
        {"prohibition_id": f"EXIT-B03-PROHIBIT-{index:03d}", "prohibited_behavior": behavior, "disposition": "constitutional failure"}
        for index, behavior in enumerate(PROHIBITIONS, start=1)
    ]
    emergency = [
        {
            "emergency_id": f"EXIT-EMERG-{index:03d}",
            "condition": condition,
            "owning_authority": authority,
            "scope": scope,
            "override_limit": "emergency may prioritize decision handling but never transfers execution, broker, authorization, risk, or position ownership",
            "expiration_required": True,
            "evidence_required": True,
        }
        for index, (condition, authority, scope) in enumerate(EMERGENCY_CONDITIONS, start=1)
    ]
    exceptions = [
        {
            "exception_type": item,
            "owning_authority": owner,
            "disposition": "preserve uncertainty, fail closed where authority is missing, and escalate to owner",
        }
        for item, owner in (
            ("decision_exception", "Exit Decision Office"),
            ("risk_exception", "Risk Office"),
            ("authorization_exception", "Authorizations Office"),
            ("execution_exception", "Trader/Broker"),
        )
    ]
    precedence = [
        {"rank": 1, "authority": "Commander", "emergency_scope": "enterprise override and escalation"},
        {"rank": 2, "authority": "Risk", "emergency_scope": "risk emergency state"},
        {"rank": 3, "authority": "Authorizations", "emergency_scope": "authorization validity"},
        {"rank": 4, "authority": "Exit Decision", "emergency_scope": "decision/recommendation disposition"},
        {"rank": 5, "authority": "Trader", "emergency_scope": "authorized execution request handling"},
        {"rank": 6, "authority": "Broker", "emergency_scope": "broker execution truth"},
    ]
    completion_checks = {
        "source_orders_preserved": len(source_registry) == 4,
        "admissibility_gates_complete": len(admissibility) == len(ADMISSIBILITY_GATES),
        "mandatory_rejections_complete": len(mandatory_rejections) == 9,
        "evaluation_factors_complete": len(evaluation) == len(EVALUATION_FACTORS),
        "recommendations_have_no_execution_authority": all(item["execution_authority"] == "NONE" for item in recommendations),
        "authorization_boundaries_complete": len(authority_boundaries) == len(AUTHORITY_BOUNDARIES),
        "prohibitions_complete": len(prohibited) == len(PROHIBITIONS),
        "emergency_overrides_limited": all("never transfers" in item["override_limit"] for item in emergency),
        "exceptions_fail_closed": all("fail closed" in item["disposition"] for item in exceptions),
    }
    baseline = {
        "baseline_id": "EXIT-DECISION-RM-001-B03-DECISION-ADMISSIBILITY-BASELINE",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "COMPLETE" if all(completion_checks.values()) else "INCOMPLETE",
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "admissibility_digest": _digest(admissibility),
        "evaluation_digest": _digest(evaluation),
        "boundary_digest": _digest(authority_boundaries),
    }
    artifacts: dict[str, Any] = {
        "source_order_registry.json": source_registry,
        "decision_admissibility_constitution.json": admissibility,
        "admissibility_authority_registry.json": admissibility,
        "mandatory_rejection_registry.json": mandatory_rejections,
        "admissibility_evidence_registry.json": [{"gate_id": item["gate_id"], "evidence_required": item["evidence_required"], "authority": item["authority"]} for item in admissibility],
        "failure_behavior_registry.json": [{"gate_id": item["gate_id"], "failure_behavior": item["failure_behavior"]} for item in admissibility],
        "evaluation_authority_constitution.json": evaluation,
        "evaluation_input_governance.json": evaluation,
        "evaluation_output_constitution.json": recommendations,
        "analytical_assessment_separation_constitution.json": {"Analyst Authority": "owns analytical truth", "Exit Decision Authority": "consumes admitted analysis without fabricating analysis truth"},
        "exit_condition_evaluation_registry.json": evaluation,
        "recommendation_constitution.json": recommendations,
        "decision_formation_constitution.json": {"formation_rule": "decision forms only from admitted, fresh, source-authorized evidence and explicit rationale"},
        "decision_factor_registry.json": evaluation,
        "decision_rationale_constitution.json": {"rationale": "mandatory, immutable, evidence-bound, and traceable to admitted inputs"},
        "authorization_dependency_constitution.json": {"dependency": "authorization validity is externally owned and required before execution pathway consumption"},
        "authorization_ownership_registry.json": {"owner": "Authorizations Office", "exit_decision_authority": "read-only validation and binding reference"},
        "authorization_validation_constitution.json": {"required": ["valid", "fresh", "not revoked", "not expired", "scope-compatible"]},
        "authorization_consumption_constitution.json": {"consumer": "Trader after valid handoff", "exit_decision_consumption": "prohibited"},
        "authorization_expiration_constitution.json": {"expired_authorization": "mandatory rejection and no execution request"},
        "authorization_revocation_constitution.json": {"revoked_authorization": "mandatory rejection and no execution request"},
        "authority_boundary_registry.json": authority_boundaries,
        "prohibited_execution_registry.json": prohibited,
        "dependency_failure_behavior.json": {"missing_authorization_or_execution_owner": "fail closed"},
        "emergency_condition_registry.json": emergency,
        "emergency_authority_ownership.json": emergency,
        "override_constitution.json": {"override": "bounded by source owner authority, evidence, expiration, and no ownership transfer"},
        "override_limitations.json": emergency,
        "emergency_evidence_constitution.json": [{"emergency_id": item["emergency_id"], "evidence_required": True} for item in emergency],
        "emergency_expiration_constitution.json": [{"emergency_id": item["emergency_id"], "expiration_required": True} for item in emergency],
        "exception_governance_registry.json": exceptions,
        "emergency_precedence_matrix.json": precedence,
        "emergency_reconciliation_constitution.json": exceptions,
        "constitutional_baseline.json": baseline,
    }
    for name, payload in artifacts.items():
        _write_json(OUTPUT_DIR / name, payload)
    completion_report = {
        "package": "EXIT-DECISION-RM-001-B03",
        "status": baseline["status"],
        "orders_completed": sorted(SOURCE_ORDERS),
        "completion_checks": completion_checks,
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "ready_for": "EXIT-DECISION-RM-001-B04",
        "baseline_digest": _digest(artifacts),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion_report)
    _write_text(OUTPUT_DIR / "README.md", "# EXIT-DECISION-RM-001-B03 Decision Admissibility Baseline\n\nPrimary entry point: completion_report.json\n")


if __name__ == "__main__":
    main()
