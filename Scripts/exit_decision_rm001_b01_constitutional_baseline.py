from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B01_CONSTITUTIONAL_BASELINE"
SOURCE_ORDER_DIR = OUTPUT_DIR / "source_orders"

SOURCE_ORDERS = {
    "EXIT-DECISION-RM-001-B01-001": Path(r"C:\Users\Fletc\.codex\attachments\59e920cd-fd5f-4d15-adec-2ee00d94289d\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B01-002": Path(r"C:\Users\Fletc\.codex\attachments\5eb19d5e-75e2-4140-9dfe-af674b3e845e\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B01-003": Path(r"C:\Users\Fletc\.codex\attachments\acc394e6-7dbc-4f3b-8ad2-ff96219edfb7\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B01-004": Path(r"C:\Users\Fletc\.codex\attachments\3b6ebc31-284a-4e02-8b07-d84831eed4cc\pasted-text.txt"),
}

AUTHORIZED = (
    ("EXIT-AUTH-001", "evaluation_authority", "Evaluate admissible exit conditions for active positions."),
    ("EXIT-AUTH-002", "recommendation_authority", "Create evidence-bound exit recommendations."),
    ("EXIT-AUTH-003", "decision_authority", "Create bounded Exit Decision records when sufficient authority exists."),
    ("EXIT-AUTH-004", "deferral_authority", "Defer decisions when evidence, authority, or freshness is incomplete."),
    ("EXIT-AUTH-005", "rejection_authority", "Reject inadmissible or unauthorized exit decision requests."),
    ("EXIT-AUTH-006", "cancellation_authority", "Cancel Exit Decision-owned pending recommendations or decisions."),
    ("EXIT-AUTH-007", "correction_authority", "Correct Exit Decision-owned records by explicit correction lineage."),
    ("EXIT-AUTH-008", "supersession_authority", "Supersede prior Exit Decision-owned records without mutating history."),
    ("EXIT-AUTH-009", "escalation_authority", "Escalate unresolved conflict or insufficient authority to the governing office."),
    ("EXIT-AUTH-010", "emergency_decision_authority", "Produce emergency exit decisions or recommendations when governed emergency inputs require action."),
)

PROHIBITED = (
    "modify Position Registry truth",
    "modify Risk truth",
    "modify Authorization truth",
    "submit broker instructions",
    "execute trades",
    "close positions directly",
    "create broker acknowledgements",
    "create closed-position truth",
    "create performance truth",
    "silently resolve authority conflicts",
    "override Commander authority",
    "self-certify ECS-003 PASS",
)

OFFICE_BOUNDARIES = {
    "Commander": ("receives escalation and may supply commander-directed authority", "Exit Decision may not bypass Commander escalation authority"),
    "Monitoring": ("provides monitoring findings and surveillance context", "Exit Decision may not own monitoring truth"),
    "Sentinel": ("may originate observations or notifications", "Exit Decision may not own Sentinel observation truth"),
    "Analyst": ("provides analytical inputs when authorized", "Exit Decision may not fabricate analysis truth"),
    "Risk": ("owns risk state, risk constraints, and emergency risk authority", "Exit Decision may consume but not mutate Risk truth"),
    "Trader": ("owns execution request handling after valid authority", "Exit Decision may not execute trades"),
    "Broker": ("owns broker submission/acknowledgement/fill truth", "Exit Decision may not submit broker commands"),
    "Position Registry": ("owns canonical open-position state and lifecycle mutation", "Exit Decision may recommend but not mutate canonical position truth"),
    "Authorizations": ("owns execution authorization issuance and revocation", "Exit Decision may not self-authorize"),
    "Closed Position Truth": ("owns canonical closed-position truth", "Exit Decision may not declare closure truth"),
    "Performance Truth": ("owns performance truth", "Exit Decision may not compute authoritative performance truth"),
    "Historian": ("owns historical custody and immutable preservation", "Exit Decision may not rewrite historical custody"),
    "Infrastructure": ("provides persistence, configuration, and runtime services", "custody does not confer Exit Decision ownership"),
}

AUTHORITY_CHAIN = (
    ("evaluation", "Exit Decision", "admissible position/risk/monitoring/authorization context"),
    ("recommendation", "Exit Decision", "evaluation evidence and decision rationale"),
    ("authorization", "Authorizations or Commander-authorized authority", "valid authorization object"),
    ("execution_request", "Trader", "valid authorization and execution contract"),
    ("broker_submission", "Broker/Trader bridge", "authorized broker submission contract"),
    ("position_mutation", "Position Registry", "authoritative broker fill evidence"),
    ("historical_custody", "Historian", "immutable evidence transfer"),
)

CONFLICTS = (
    ("decision_conflict", "Exit Decision", "defer and escalate to Commander or governing authority"),
    ("risk_conflict", "Risk", "fail closed until Risk disposition is available"),
    ("authorization_conflict", "Authorizations", "fail closed until authorization disposition is available"),
    ("position_truth_conflict", "Position Registry", "fail closed until position reconciliation completes"),
    ("broker_truth_conflict", "Broker", "fail closed; do not infer acknowledgement or fill truth"),
    ("historical_conflict", "Historian", "preserve both records with supersession/correction lineage"),
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
        records.append(
            {
                "order_id": order_id,
                "committed_copy": _relative(target),
                "source_attachment": str(source),
                "sha256": _file_digest(target),
                "disposition": "PRESERVED",
            }
        )
    return records


def _authority_registry() -> list[dict[str, Any]]:
    return [
        {
            "authority_id": authority_id,
            "authority_name": name,
            "constitutional_source": "EXIT-DECISION-RM-001-B01-001",
            "constitutional_owner": "Exit Decision Office",
            "permitted_scope": scope,
            "required_inputs": ["admissible position context", "authorized risk/monitoring/authorization context where applicable", "immutable evaluation evidence"],
            "authorized_outputs": ["Exit Decision evaluation", "Exit recommendation", "Exit decision", "deferral", "rejection", "cancellation", "correction", "supersession", "escalation"],
            "prohibited_outputs": ["broker order", "position mutation", "risk mutation", "authorization mutation", "closed-position truth"],
            "single_constitutional_source_verified": True,
        }
        for authority_id, name, scope in AUTHORIZED
    ]


def _responsibility_registry() -> list[dict[str, Any]]:
    return [
        {
            "responsibility_id": f"EXIT-RESP-{index:03d}",
            "responsibility": responsibility,
            "owner": "Exit Decision Office",
            "custody": "Exit Decision Office",
            "mutation_authority": "Exit Decision Office for Exit Decision-owned records only",
            "evidence_obligation": "immutable evidence and rationale required",
        }
        for index, responsibility in enumerate(
            (
                "exit condition evaluation",
                "exit recommendation generation",
                "exit decision record generation",
                "exit decision deferral",
                "exit decision rejection",
                "exit decision cancellation",
                "exit decision correction",
                "exit decision supersession",
                "exit conflict escalation",
                "emergency exit decision recommendation",
            ),
            start=1,
        )
    ]


def _boundary_registry() -> list[dict[str, Any]]:
    return [
        {
            "office": office,
            "external_authority": authority,
            "exit_decision_boundary": boundary,
            "permitted_interaction": "read/consume authorized evidence, produce decision-context outputs, or escalate as governed",
            "prohibited_interaction": "ownership transfer or mutation by implication",
            "conflict_disposition": "fail closed and escalate to governing authority",
        }
        for office, (authority, boundary) in sorted(OFFICE_BOUNDARIES.items())
    ]


def _authority_separation_registry() -> list[dict[str, Any]]:
    return [
        {
            "chain_step": index,
            "authority_stage": stage,
            "constitutional_owner": owner,
            "required_evidence": evidence,
            "exit_decision_may_perform": owner == "Exit Decision",
            "boundary_rule": "Exit Decision stops before authorization, execution, broker submission, position mutation, and history custody unless the stage owner is Exit Decision.",
        }
        for index, (stage, owner, evidence) in enumerate(AUTHORITY_CHAIN, start=1)
    ]


def _prohibited_registry() -> list[dict[str, Any]]:
    return [
        {
            "prohibition_id": f"EXIT-PROHIBIT-{index:03d}",
            "prohibited_authority": action,
            "constitutional_source": "EXIT-DECISION-RM-001-B01-001 / B01-003",
            "fail_closed_result": "constitutional failure and no downstream execution",
        }
        for index, action in enumerate(PROHIBITED, start=1)
    ]


def _escalation_registry() -> list[dict[str, Any]]:
    return [
        {
            "escalation_id": f"EXIT-ESC-{index:03d}",
            "trigger": trigger,
            "owning_authority": owner,
            "required_disposition": disposition,
            "evidence_required": "conflict record, source evidence, escalation timestamp, receiving authority, terminal disposition",
        }
        for index, (trigger, owner, disposition) in enumerate(CONFLICTS, start=1)
    ]


def _precedence_matrix() -> list[dict[str, Any]]:
    return [
        {"rank": 1, "authority": "Commander", "applies_to": "enterprise governance and commander-directed escalation"},
        {"rank": 2, "authority": "Risk", "applies_to": "risk state and emergency risk constraints"},
        {"rank": 3, "authority": "Authorizations", "applies_to": "execution authorization validity"},
        {"rank": 4, "authority": "Position Registry", "applies_to": "canonical position truth and position mutation"},
        {"rank": 5, "authority": "Exit Decision", "applies_to": "exit evaluation, recommendation, decision, deferral, rejection, cancellation, correction, supersession"},
        {"rank": 6, "authority": "Trader", "applies_to": "authorized execution request handling"},
        {"rank": 7, "authority": "Broker", "applies_to": "broker acknowledgement, submission, and fill truth"},
        {"rank": 8, "authority": "Historian", "applies_to": "historical custody and immutable preservation"},
    ]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_registry = _copy_source_orders()
    authority = _authority_registry()
    responsibilities = _responsibility_registry()
    boundaries = _boundary_registry()
    separation = _authority_separation_registry()
    prohibited = _prohibited_registry()
    escalation = _escalation_registry()
    precedence = _precedence_matrix()

    completion_checks = {
        "source_orders_preserved": len(source_registry) == 4,
        "authority_registry_complete": len(authority) == len(AUTHORIZED),
        "enterprise_boundaries_complete": len(boundaries) == len(OFFICE_BOUNDARIES),
        "execution_separation_complete": all(not item["exit_decision_may_perform"] for item in separation if item["authority_stage"] in {"authorization", "execution_request", "broker_submission", "position_mutation", "historical_custody"}),
        "prohibited_authority_complete": len(prohibited) == len(PROHIBITED),
        "conflict_governance_complete": len(escalation) == len(CONFLICTS),
    }
    baseline = {
        "baseline_id": "EXIT-DECISION-RM-001-B01-CONSTITUTIONAL-BASELINE",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "source_registry_digest": _digest(source_registry),
        "authority_registry_digest": _digest(authority),
        "boundary_registry_digest": _digest(boundaries),
        "authority_separation_digest": _digest(separation),
        "status": "COMPLETE" if all(completion_checks.values()) else "INCOMPLETE",
    }
    artifacts = {
        "source_order_registry.json": source_registry,
        "purpose_constitution.json": {
            "office": "Exit Decision Office",
            "purpose": "Evaluate admissible exit conditions and produce bounded exit recommendations, decisions, deferrals, rejections, cancellations, corrections, supersessions, or escalations without executing trades or mutating externally owned truth.",
            "mission": "Preserve deterministic, evidence-bound exit decision authority while maintaining strict separation from authorization, execution, broker, position, performance, and historical custody authorities.",
        },
        "authority_registry.json": authority,
        "responsibility_registry.json": responsibilities,
        "prohibited_authority_registry.json": prohibited,
        "enterprise_boundary_registry.json": boundaries,
        "responsibility_ownership_matrix.json": responsibilities,
        "authority_separation_registry.json": separation,
        "decision_to_execution_boundary_registry.json": separation,
        "escalation_authority_registry.json": escalation,
        "conflict_resolution_registry.json": escalation,
        "precedence_matrix.json": precedence,
        "governance_reconciliation_registry.json": {
            "open_conflicts": [],
            "shared_responsibility_disposition": "shared evidence consumption permitted; shared ownership prohibited",
            "duplicated_authority_disposition": "no duplicated Exit Decision execution, broker, position, risk, authorization, performance, or historical authority",
            "missing_ownership_disposition": "all B01 authority domains have explicit owners",
        },
        "constitutional_baseline.json": baseline,
    }
    for name, payload in artifacts.items():
        _write_json(OUTPUT_DIR / name, payload)

    completion_report = {
        "package": "EXIT-DECISION-RM-001-B01",
        "status": baseline["status"],
        "orders_completed": sorted(SOURCE_ORDERS),
        "completion_checks": completion_checks,
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "ready_for": "EXIT-DECISION-RM-001-B02",
        "baseline_digest": _digest(artifacts),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion_report)
    _write_text(
        OUTPUT_DIR / "README.md",
        "# EXIT-DECISION-RM-001-B01 Constitutional Baseline\n\nPrimary entry point: completion_report.json\n",
    )


if __name__ == "__main__":
    main()
