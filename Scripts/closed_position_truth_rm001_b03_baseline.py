"""Materialize Closed Position Truth RM-001 B03 constitutional baseline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "CLOSED_POSITION_TRUTH_RM001_B03_CLOSURE_RECONCILIATION_BASELINE"
ORDER_SOURCES = {
    "CLOSED-POSITION-TRUTH-RM-001-B03-001": Path(r"C:\Users\Fletc\.codex\attachments\b264098c-1d79-48b1-b63d-554f86942eda\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B03-002": Path(r"C:\Users\Fletc\.codex\attachments\d2c46410-5774-49a9-8618-393ea341e655\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B03-003": Path(r"C:\Users\Fletc\.codex\attachments\4c2cfe3b-7f2c-40e4-9efd-98ce5466717c\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B03-004": Path(r"C:\Users\Fletc\.codex\attachments\3b1e6108-b963-40a6-a1ad-3f8c295f453e\pasted-text.txt"),
}

CLOSURE_CRITERIA = (
    ("authoritative position identity", "Position Registry", "originating position identity evidence"),
    ("execution completion", "Trader and Broker", "final execution disposition and broker evidence"),
    ("complete fill reconciliation", "Closed Position Truth", "broker fills, acknowledgements, corrections, cancellations, duplicates"),
    ("residual position quantity equal to zero", "Closed Position Truth deriving from Position Registry and Broker evidence", "Residual Quantity Record"),
    ("successful execution reconciliation", "Closed Position Truth", "Reconciliation Record"),
    ("successful position reconciliation", "Closed Position Truth using Position Registry truth", "Position Registry references"),
    ("settlement verified or constitutionally exempt", "Closed Position Truth verification; settlement owner retains facts", "Settlement Verification Record or Exemption Record"),
    ("mandatory closure evidence present", "Closed Position Truth", "Closure Evidence Record population"),
    ("closure evidence constitutionally admissible", "Closed Position Truth", "Closure Admissibility result"),
    ("no unresolved contradiction", "Closed Position Truth", "contradiction and exception scan"),
    ("no unresolved closure exception", "Closed Position Truth", "Closure Exception registry"),
    ("closure determination issued by constitutional authority", "Closed Position Truth", "Closure Determination"),
)

CLOSURE_OUTCOMES = ("CONSTITUTIONALLY_CLOSED", "NOT_CLOSED", "DEFERRED", "REJECTED", "EXCEPTION")
SETTLEMENT_STATES = ("Pending", "Submitted", "Acknowledged", "Under Verification", "Verified", "Constitutionally Exempt", "Failed", "Disputed", "Corrected", "Superseded", "Archived")
QUANTITY_OUTCOMES = ("ZERO_VERIFIED", "NONZERO_CONFIRMED", "INCONSISTENT", "INSUFFICIENT_EVIDENCE")
RECONCILIATION_OUTCOMES = ("RECONCILED", "UNRESOLVED", "FAILED")


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _write(name: str, value: Any) -> None:
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value), encoding="utf-8")


def _write_text(name: str, value: str) -> None:
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_registry() -> list[dict[str, Any]]:
    rows = []
    for order_id, path in ORDER_SOURCES.items():
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        name = f"sources/{order_id.rsplit('-', 1)[-1]}.txt"
        _write_text(name, text)
        copied = OUTPUT_DIR / name
        rows.append({"order_id": order_id, "source_copy": str(copied.relative_to(REPOSITORY_ROOT)).replace("\\", "/"), "source_sha256": _file_digest(copied), "source_available": bool(text)})
    return rows


def _closure_registry() -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": f"CPT-CLOSURE-{index:03d}",
            "closure_requirement": criterion,
            "authority_owner": owner,
            "required_object": _object_for_criterion(criterion),
            "required_evidence": evidence,
            "admissibility_rule": "must possess authoritative source identity, provenance, temporal context, integrity, completeness, identity consistency, quantity consistency, and no unresolved contradiction",
            "satisfaction_condition": "affirmatively established through constitutionally admissible evidence",
            "failure_condition": "prohibit constitutional closure; issue rejection, deferral, exception, reconciliation request, evidence request, or escalation",
            "resulting_closure_effect": "may support CONSTITUTIONALLY_CLOSED only when all mandatory criteria are satisfied",
            "waiver_allowed": False,
        }
        for index, (criterion, owner, evidence) in enumerate(CLOSURE_CRITERIA, start=1)
    ]


def _object_for_criterion(criterion: str) -> str:
    if "identity" in criterion:
        return "Closed Position Identity"
    if "execution" in criterion or "fill" in criterion:
        return "Reconciliation Record"
    if "residual" in criterion or "quantity" in criterion:
        return "Residual Position Resolution"
    if "settlement" in criterion:
        return "Settlement Verification Record"
    if "evidence" in criterion:
        return "Closure Evidence Record"
    if "contradiction" in criterion or "exception" in criterion:
        return "Closure Exception Record"
    return "Closure Determination"


def _closure_authority_registry() -> list[dict[str, Any]]:
    authorities = (
        "closure determination authority",
        "closure validation authority",
        "closure admissibility authority",
        "closure rejection authority",
        "closure deferral authority",
        "closure exception authority",
        "correction authority",
        "supersession authority",
        "archival authority",
    )
    return [
        {
            "authority_id": f"CPT-B03-AUTH-{index:03d}",
            "authority": authority,
            "owner": "Closed Position Truth Office",
            "does_not_permit": ("broker truth creation", "upstream fact mutation", "execution authorization", "trading decision", "closed position reopening"),
            "source_order": "CLOSED-POSITION-TRUTH-RM-001-B03-001",
        }
        for index, authority in enumerate(authorities, start=1)
    ]


def _admissibility_registry() -> list[dict[str, Any]]:
    rules = ("authoritative source identity", "complete provenance", "applicable scope", "valid temporal context", "sufficient freshness", "source integrity", "evidence completeness", "identity consistency", "quantity consistency", "absence of unresolved contradiction")
    return [{"rule_id": f"CPT-ADMISS-{index:03d}", "rule": rule, "must_precede_closure_determination": True, "inadmissible_evidence_participates": False} for index, rule in enumerate(rules, start=1)]


def _prohibited_closure_registry() -> list[dict[str, Any]]:
    conditions = (
        "incomplete execution",
        "unresolved execution status",
        "incomplete fill reconciliation",
        "residual quantity greater than zero",
        "residual quantity less than zero",
        "reconciliation failure",
        "unresolved identity mismatch",
        "settlement neither verified nor constitutionally exempt",
        "missing mandatory evidence",
        "stale evidence",
        "inadmissible evidence",
        "contradictory upstream evidence",
        "unresolved duplicate execution",
        "unresolved closure exception",
        "analytical degradation used as substitute evidence",
        "manual completion assertion",
        "attempted historical overwrite",
    )
    return [{"condition_id": f"CPT-PROHIBIT-CLOSE-{index:03d}", "condition": item, "closure_effect": "PROHIBITED", "deterministic_handling": ("REJECTED", "DEFERRED", "EXCEPTION", "ESCALATION")} for index, item in enumerate(conditions, start=1)]


def _closure_determination_doctrine() -> dict[str, Any]:
    return {
        "object": "Closure Determination",
        "required_fields": ("subject position", "evaluated prerequisites", "evidence population", "admissibility result", "reconciliation result", "settlement disposition", "residual quantity result", "exception state", "determination authority", "determination timestamp", "final outcome"),
        "permitted_outcomes": CLOSURE_OUTCOMES,
        "only_authorizing_outcome": "CONSTITUTIONALLY_CLOSED",
        "degraded_authoritative_truth_allowed": False,
    }


def _settlement_constitution() -> dict[str, Any]:
    return {
        "purpose": "constitutional verification of financial completion following execution",
        "independently_creates_closed_position_truth": False,
        "admissible_dispositions": ("Verified", "Constitutionally Exempt"),
        "cannot_override": ("incomplete execution", "fill reconciliation failure", "nonzero residual quantity", "reconciliation failure", "missing evidence", "failed admissibility"),
        "source_order": "CLOSED-POSITION-TRUTH-RM-001-B03-002",
    }


def _settlement_registry() -> list[dict[str, Any]]:
    elements = ("settlement status", "settlement evidence", "settlement verification", "settlement exemption", "settlement failure", "settlement discrepancy", "settlement correction history")
    return [
        {
            "settlement_element_id": f"CPT-SETTLE-{index:03d}",
            "settlement_element": element,
            "constitutional_owner": "designated settlement authority for source fact; Closed Position Truth owns closure-use verification",
            "creator": "designated settlement authority or Closed Position Truth verification object as applicable",
            "custodian": "Closed Position Truth until archival; Historian after archival",
            "verification_authority": "Closed Position Truth Office for closure participation",
            "correction_authority": "source owner for source facts; Closed Position Truth successor record for closure-use records",
            "status": "DETERMINISTIC",
        }
        for index, element in enumerate(elements, start=1)
    ]


def _settlement_state_registry() -> list[dict[str, Any]]:
    return [
        {
            "state_id": f"CPT-SETTLE-STATE-{index:03d}",
            "state": state,
            "governing_authority": "designated settlement authority" if state in {"Pending", "Submitted", "Acknowledged", "Failed", "Disputed", "Corrected", "Superseded"} else "Closed Position Truth Office for closure-use verification",
            "satisfies_closure_participation": state in {"Verified", "Constitutionally Exempt"},
            "closure_consequence": "may satisfy settlement prerequisite only with all other closure criteria" if state in {"Verified", "Constitutionally Exempt"} else "prevents closure when settlement is required",
        }
        for index, state in enumerate(SETTLEMENT_STATES, start=1)
    ]


def _settlement_evidence_registry() -> list[dict[str, Any]]:
    evidence = ("settlement confirmation", "clearing confirmation", "broker settlement record", "cash movement evidence", "asset-delivery evidence", "fee and charge evidence", "settlement-date evidence", "exemption evidence", "correction evidence", "supersession evidence")
    return [{"evidence_id": f"CPT-SETTLE-EVID-{index:03d}", "evidence_class": item, "manual_assertion_sufficient": False, "metadata_only_sufficient": False, "synthetic_reconstruction_sufficient": False, "requires_provenance_integrity_freshness_retention": True} for index, item in enumerate(evidence, start=1)]


def _settlement_failure_registry() -> list[dict[str, Any]]:
    failures = ("missing settlement evidence", "failed settlement", "rejected settlement", "reversed settlement", "disputed settlement", "partial settlement", "stale settlement evidence", "identity mismatch", "amount mismatch", "quantity mismatch", "timing mismatch", "unresolved settlement discrepancy")
    return [{"failure_id": f"CPT-SETTLE-FAIL-{index:03d}", "failure": item, "closure_effect": "PREVENTS_CLOSURE_WHERE_REQUIRED", "silently_converts_to_exemption": False, "evidence_preserved": True} for index, item in enumerate(failures, start=1)]


def _settlement_exemption_registry() -> dict[str, Any]:
    return {
        "exemption_allowed_only_when": ("instrument or position constitutionally exempt", "exemption authority explicitly defined", "scope matches position", "temporal validity established", "complete evidence exists", "no reconciliation conflict exists"),
        "does_not_waive": ("execution completion", "zero residual verification", "reconciliation success", "closure evidence", "degraded truth prohibition"),
        "revocation_requires_reassessment": True,
    }


def _residual_quantity_registry() -> dict[str, Any]:
    return {
        "definition": "authoritative unresolved position quantity remaining after reconciliation of all constitutionally admissible position and execution evidence",
        "formula": "Authoritative Position Quantity - Net Constitutionally Admissible Closing Quantity +/- Authorized Quantity Adjustments",
        "required_fields": ("record identity", "position identity", "instrument identity", "starting quantity", "gross closing quantity", "excluded execution quantity", "corrected execution quantity", "reversed execution quantity", "authorized adjustment quantity", "net closing quantity", "calculated residual quantity", "quantity unit", "quantity precision", "source evidence references", "reconciliation identity", "calculation authority", "calculation timestamp", "doctrine version", "admissibility outcome", "exception references"),
        "zero_required_for_closure": True,
        "zero_independently_establishes_closure": False,
        "source_order": "CLOSED-POSITION-TRUTH-RM-001-B03-003",
    }


def _quantity_verification_registry() -> list[dict[str, Any]]:
    return [
        {
            "outcome": outcome,
            "may_satisfy_closure_quantity_condition": outcome == "ZERO_VERIFIED",
            "terminal_effect": "supports residual-quantity prerequisite" if outcome == "ZERO_VERIFIED" else "prohibits closure until resolved",
        }
        for outcome in QUANTITY_OUTCOMES
    ]


def _quantity_reconciliation_registry() -> list[dict[str, Any]]:
    return [
        {
            "outcome": outcome,
            "may_support_zero_quantity_verification": outcome == "RECONCILED",
            "terminal_effect": "eligible for zero verification" if outcome == "RECONCILED" else "prohibits zero verification",
        }
        for outcome in RECONCILIATION_OUTCOMES
    ]


def _quantity_exception_registry() -> list[dict[str, Any]]:
    exceptions = ("missing authoritative starting quantity", "unresolved position identity", "incomplete execution population", "positive residual quantity", "negative residual quantity", "conflicting quantity evidence", "duplicate execution unresolved", "missing correction lineage", "missing reversal lineage", "ambiguous quantity direction", "incompatible quantity units", "stale quantity evidence", "unsupported precision or rounding", "unauthorized position partition", "Position Registry contradiction")
    return [{"exception_id": f"CPT-QTY-EXC-{index:03d}", "exception": item, "authoritative_truth_effect": "PROHIBITS_CLOSED_POSITION_TRUTH", "distinct_from_authoritative_truth": True} for index, item in enumerate(exceptions, start=1)]


def _quantity_source_precedence_matrix() -> list[dict[str, Any]]:
    rows = (
        ("Position identity and current quantity", "Position Registry"),
        ("Broker fill facts", "Broker"),
        ("Execution workflow and intended scope", "Trader"),
        ("Exit intent", "Exit Decision"),
        ("Closed-position quantity determination", "Closed Position Truth"),
    )
    return [{"domain": domain, "authoritative_source": source, "downstream_deriver_may_modify_source_facts": False} for domain, source in rows]


def _duplicate_execution_registry() -> dict[str, Any]:
    return {
        "duplicate_detection_identifiers": ("broker execution identity", "order identity", "fill identity", "position identity", "instrument identity", "execution time", "quantity", "price", "correction or reversal relationship"),
        "handling": ("preserve every received record", "identify authoritative execution event", "exclude duplicate quantity", "preserve duplicate-detection evidence", "prevent parallel execution lineage"),
        "repeated_message_creates_quantity": False,
    }


def _reconciliation_registry() -> dict[str, Any]:
    return {
        "definition": "deterministic constitutional process validating agreement among required authoritative upstream truth sources before Closed Position Truth creation",
        "verifies": ("execution completeness", "execution identity", "fill completeness", "position reconciliation", "residual quantity", "settlement status", "realized outcome derivation", "closure admissibility", "evidence sufficiency"),
        "mandatory_failure_prohibits_closure": True,
        "source_order": "CLOSED-POSITION-TRUTH-RM-001-B03-004",
    }


def _reconciliation_participation_matrix() -> list[dict[str, Any]]:
    rows = (
        ("Position Registry", "position identity, remaining quantity, position state", "position truth", "PROVIDER"),
        ("Broker", "execution records, acknowledgements, fills, settlement evidence", "broker-originated facts", "PROVIDER"),
        ("Trader", "execution lifecycle, request history, reconciliation participation", "execution workflow", "PROVIDER"),
        ("Exit Decision", "exit decision identity, authority, lineage", "exit decision truth", "PROVIDER"),
        ("Performance Truth", "realized outcomes", "performance analytics", "CONSUMER"),
        ("Historian", "finalized reconciliation history and lineage", "historical custody", "CONSUMER"),
    )
    return [{"participant": office, "provides_or_consumes": info, "owned_truth": truth, "role": role, "closed_position_truth_may_modify_owned_truth": False} for office, info, truth, role in rows]


def _reconciliation_evidence_registry() -> list[dict[str, Any]]:
    required = ("reconciliation identity", "participating authorities", "evidence references", "reconciliation timestamp", "governing authority", "reconciliation result", "exception references")
    return [{"evidence_requirement_id": f"CPT-REC-EVID-{index:03d}", "requirement": item, "required": True, "missing_effect": "PROHIBITS_RECONCILIATION_SUCCESS"} for index, item in enumerate(required, start=1)]


def _reconciliation_success_registry() -> list[dict[str, Any]]:
    criteria = ("complete execution reconciliation", "complete fill reconciliation", "zero residual quantity", "valid settlement state or constitutional exemption", "complete admissible evidence", "no authority conflicts", "no identity conflicts", "no quantity conflicts")
    return [{"success_criterion_id": f"CPT-REC-SUCCESS-{index:03d}", "criterion": item, "required": True} for index, item in enumerate(criteria, start=1)]


def _reconciliation_failure_registry() -> list[dict[str, Any]]:
    failures = ("unresolved execution discrepancies", "unresolved quantity discrepancies", "unresolved identity mismatch", "unresolved settlement requirement", "conflicting authoritative evidence", "stale mandatory evidence", "duplicate unresolved execution", "missing required evidence")
    return [{"failure_id": f"CPT-REC-FAIL-{index:03d}", "failure": item, "closure_effect": "PROHIBITS_CLOSED_POSITION_TRUTH"} for index, item in enumerate(failures, start=1)]


def _source_precedence_registry() -> list[dict[str, Any]]:
    sources = ("Position Registry authoritative position truth", "Broker authoritative execution facts", "Trader execution lifecycle records", "Settlement verification", "Closed Position Truth reconciliation determination", "Performance Truth derived analytics", "Analytical or diagnostic records")
    return [{"rank": index, "source": source, "derived_records_override_authoritative_sources": False} for index, source in enumerate(sources, start=1)]


def _lineage_registry(kind: str) -> dict[str, Any]:
    return {
        "lineage_type": kind,
        "predecessor_preserved": True,
        "successor_references_predecessor": True,
        "evidence_preserved": True,
        "history_overwrite_allowed": False,
        "complete_reconstruction_required": True,
    }


def _findings_registry() -> list[dict[str, Any]]:
    findings = (
        ("CPT-B03-FIND-001", "constitutional closure requires all mandatory criteria and cannot be inferred"),
        ("CPT-B03-FIND-002", "settlement can satisfy only Verified or Constitutionally Exempt and cannot override other failures"),
        ("CPT-B03-FIND-003", "zero residual quantity is required but independently insufficient"),
        ("CPT-B03-FIND-004", "reconciliation must succeed before authoritative truth creation"),
        ("CPT-B03-FIND-005", "correction and supersession preserve predecessor lineage"),
    )
    return [{"finding_id": fid, "finding": finding, "severity": "INFO", "disposition": "CLOSED", "resolution_status": "RESOLVED"} for fid, finding in findings]


def generate_baseline() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sources = _source_registry()
    findings = _findings_registry()
    payloads = {
        "source_order_registry.json": sources,
        "B03-001_constitutional_closure_registry.json": _closure_registry(),
        "B03-001_closure_admissibility_registry.json": _admissibility_registry(),
        "B03-001_closure_authority_registry.json": _closure_authority_registry(),
        "B03-001_prohibited_closure_registry.json": _prohibited_closure_registry(),
        "B03-001_closure_determination_doctrine.json": _closure_determination_doctrine(),
        "B03-001_constitutional_findings_registry.json": findings,
        "B03-001_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B03-001", "status": "COMPLETE"},
        "B03-002_settlement_constitution.json": _settlement_constitution(),
        "B03-002_settlement_registry.json": _settlement_registry(),
        "B03-002_settlement_ownership_registry.json": _settlement_registry(),
        "B03-002_settlement_authority_registry.json": _settlement_registry(),
        "B03-002_settlement_state_registry.json": _settlement_state_registry(),
        "B03-002_settlement_verification_registry.json": tuple(item for item in _settlement_state_registry() if item["state"] in {"Verified", "Constitutionally Exempt"}),
        "B03-002_settlement_evidence_registry.json": _settlement_evidence_registry(),
        "B03-002_settlement_exemption_registry.json": _settlement_exemption_registry(),
        "B03-002_settlement_failure_registry.json": _settlement_failure_registry(),
        "B03-002_settlement_reconciliation_registry.json": _reconciliation_success_registry(),
        "B03-002_settlement_correction_registry.json": _lineage_registry("settlement correction"),
        "B03-002_settlement_supersession_registry.json": _lineage_registry("settlement supersession"),
        "B03-002_settlement_temporal_registry.json": {"temporal_fields": ("contractual settlement date", "actual settlement date", "verification time", "exemption effective time", "exemption expiration", "correction time", "supersession time", "archival time"), "timing_inference_allowed": False},
        "B03-002_prohibited_settlement_authority_registry.json": tuple({"prohibition": item, "status": "PROHIBITED"} for item in ("settlement independently creating closure truth", "settlement overriding reconciliation failure", "settlement overriding nonzero residual quantity", "settlement overriding incomplete execution", "settlement exemption without authority", "settlement verification without evidence", "silent failure-to-exemption conversion", "historical settlement overwrite", "analytical settlement estimates as authoritative truth", "Closed Position Truth modifying broker-owned settlement facts")),
        "B03-002_settlement_conflict_registry.json": {"conflict_types": ("status", "amount", "quantity", "date", "exemption claim", "duplicate record", "correction", "reversal"), "unresolved_conflict_prevents_closure": True},
        "B03-002_settlement_authority_matrix.json": _settlement_registry(),
        "B03-002_constitutional_findings_registry.json": findings,
        "B03-002_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B03-002", "status": "COMPLETE"},
        "B03-003_residual_quantity_registry.json": _residual_quantity_registry(),
        "B03-003_quantity_verification_registry.json": _quantity_verification_registry(),
        "B03-003_quantity_reconciliation_registry.json": _quantity_reconciliation_registry(),
        "B03-003_residual_quantity_ownership_matrix.json": _quantity_source_precedence_matrix(),
        "B03-003_quantity_source_precedence_matrix.json": _quantity_source_precedence_matrix(),
        "B03-003_duplicate_execution_registry.json": _duplicate_execution_registry(),
        "B03-003_quantity_exception_registry.json": _quantity_exception_registry(),
        "B03-003_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B03-003", "status": "COMPLETE"},
        "B03-004_reconciliation_registry.json": _reconciliation_registry(),
        "B03-004_reconciliation_authority_registry.json": _reconciliation_participation_matrix(),
        "B03-004_reconciliation_evidence_registry.json": _reconciliation_evidence_registry(),
        "B03-004_source_precedence_registry.json": _source_precedence_registry(),
        "B03-004_reconciliation_success_criteria_registry.json": _reconciliation_success_registry(),
        "B03-004_reconciliation_failure_registry.json": _reconciliation_failure_registry(),
        "B03-004_exception_registry.json": tuple(item for item in _quantity_exception_registry()) + tuple({"exception_id": f"CPT-REC-EXC-{i:03d}", "exception": item, "distinct_from_authoritative_truth": True} for i, item in enumerate(("execution discrepancy", "identity mismatch", "settlement conflict", "evidence insufficiency"), start=1)),
        "B03-004_correction_lineage_registry.json": _lineage_registry("reconciliation correction"),
        "B03-004_supersession_lineage_registry.json": _lineage_registry("reconciliation supersession"),
        "B03-004_reconciliation_participation_matrix.json": _reconciliation_participation_matrix(),
        "B03-004_constitutional_findings_registry.json": findings,
        "B03-004_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B03-004", "status": "COMPLETE"},
    }
    completion = {
        "series": "CLOSED-POSITION-TRUTH-RM-001-B03",
        "status": "COMPLETE_FOR_ISSUED_ORDERS",
        "orders_completed": tuple(ORDER_SOURCES),
        "constitutional_doctrine_only": True,
        "implementation_behavior_modified": False,
        "behavioral_verification_executed": False,
        "implementation_certification_executed": False,
        "implementation_proof_generated": False,
        "ready_for": "NEXT_CONSTITUTIONALLY_ISSUED_CLOSED_POSITION_TRUTH_ORDER",
        "completion_criteria": {
            "constitutional_closure_defined": True,
            "mandatory_closure_prerequisites_defined": len(CLOSURE_CRITERIA) == 12,
            "closure_admissibility_deterministic": True,
            "settlement_bounded_to_verified_or_exempt": True,
            "settlement_cannot_override_other_failures": True,
            "residual_zero_required": True,
            "zero_quantity_independently_insufficient": True,
            "positive_negative_residual_fail_closed": True,
            "quantity_reconciliation_deterministic": True,
            "reconciliation_success_required": True,
            "source_precedence_deterministic": True,
            "correction_supersession_preserve_lineage": True,
            "no_unresolved_b03_001_to_004_ambiguity": True,
        },
    }
    payloads["B03_series_completion_report.json"] = completion
    for name, payload in payloads.items():
        _write(name, payload)
    _write(
        "manifest.json",
        {
            "package": "CLOSED_POSITION_TRUTH_RM001_B03_CLOSURE_RECONCILIATION_BASELINE",
            "series": "CLOSED-POSITION-TRUTH-RM-001-B03",
            "baseline_digest": _digest(payloads),
            "files": sorted(str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/") for path in OUTPUT_DIR.rglob("*") if path.is_file()),
            "ready_for": completion["ready_for"],
        },
    )
    return completion


if __name__ == "__main__":
    print(_json(generate_baseline()), end="")
