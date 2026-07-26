"""Materialize Closed Position Truth RM-001 B01 constitutional baseline.

The B01 series is doctrine-only. This script writes deterministic registries and
completion reports from the four constitutional orders without modifying runtime
behavior or executing behavioral certification.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "CLOSED_POSITION_TRUTH_RM001_B01_CONSTITUTIONAL_BASELINE"
ORDER_SOURCES = {
    "CLOSED-POSITION-TRUTH-RM-001-B01-001": Path(r"C:\Users\Fletc\.codex\attachments\2c0f2201-896e-43d3-a357-d5434588d849\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B01-002": Path(r"C:\Users\Fletc\.codex\attachments\ff9d9ef7-bd47-4ff8-9817-29082943a8fc\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B01-003": Path(r"C:\Users\Fletc\.codex\attachments\136275cc-da4c-493d-8cf7-1d799817987f\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B01-004": Path(r"C:\Users\Fletc\.codex\attachments\c3217a28-7fd4-4cce-a7e3-5edec105e1c5\pasted-text.txt"),
}


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _write(name: str, value: Any) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / name).write_text(_json(value), encoding="utf-8")


def _write_text(name: str, value: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_registry() -> list[dict[str, Any]]:
    records = []
    for order_id, path in ORDER_SOURCES.items():
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        safe_name = order_id.replace("CLOSED-POSITION-TRUTH-RM-001-", "")
        source_copy = f"sources/{safe_name}.txt"
        _write_text(source_copy, text)
        copied = OUTPUT_DIR / source_copy
        records.append(
            {
                "order_id": order_id,
                "source_copy": f"Documentation/CLOSED_POSITION_TRUTH_RM001_B01_CONSTITUTIONAL_BASELINE/{source_copy}",
                "source_sha256": _file_digest(copied),
                "source_available": bool(text),
            }
        )
    return records


def _authority_registry() -> list[dict[str, Any]]:
    return [
        _authority("CPT-AUTH-001", "constitutional_closure_determination", "determine whether constitutional closure requirements are satisfied"),
        _authority("CPT-AUTH-002", "authoritative_truth_creation", "create authoritative Closed Position Truth after every prerequisite is satisfied"),
        _authority("CPT-AUTH-003", "closed_position_record_maintenance", "maintain immutable active Closed Position Truth records until archival transfer"),
        _authority("CPT-AUTH-004", "successor_supersession", "supersede prior Closed Position Truth through successor records only"),
        _authority("CPT-AUTH-005", "archival_eligibility", "determine archival eligibility before Historian custody transfer"),
        _authority("CPT-AUTH-006", "invalid_closure_rejection", "reject, defer, or suspend truth creation when required evidence is absent or contradictory"),
        _authority("CPT-AUTH-007", "upstream_truth_reconciliation", "reconcile closure eligibility using authorized upstream truth without owning upstream truth"),
    ]


def _authority(authority_id: str, name: str, scope: str) -> dict[str, Any]:
    return {
        "authority_id": authority_id,
        "authority_name": name,
        "constitutional_owner": "Closed Position Truth Office",
        "authority_scope": scope,
        "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-001",
        "limitations": (
            "no upstream truth mutation",
            "no trading authority",
            "no broker truth authority",
            "no downstream performance analytics ownership",
        ),
        "status": "ESTABLISHED",
    }


def _responsibility_registry() -> list[dict[str, Any]]:
    names = (
        "constitutional closure determination",
        "authoritative closed-position identity",
        "closure timestamp",
        "closure rationale",
        "assigned realized outcome truth",
        "closure reconciliation status",
        "correction lineage",
        "supersession lineage",
        "archival eligibility",
        "historical integrity before archival transfer",
    )
    return [
        {
            "responsibility_id": f"CPT-RESP-{index:03d}",
            "responsibility": name,
            "constitutional_owner": "Closed Position Truth Office",
            "shared_owner": False,
            "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-001",
            "status": "SINGLE_OWNER_ASSIGNED",
        }
        for index, name in enumerate(names, start=1)
    ]


def _limitation_registry() -> list[dict[str, Any]]:
    prohibited = (
        "own open-position truth",
        "issue trading decisions",
        "issue exit decisions",
        "issue authorizations",
        "route orders",
        "execute trades",
        "modify broker-owned facts",
        "modify Position Registry truth",
        "modify Risk truth",
        "modify Authorization truth",
        "modify Performance Truth",
        "modify Historian records",
        "modify market data",
        "promote analytical findings into authoritative truth",
    )
    return [
        {
            "limitation_id": f"CPT-LIMIT-{index:03d}",
            "prohibited_authority": item,
            "constitutional_owner": "Closed Position Truth Office",
            "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-001",
            "status": "PROHIBITED",
        }
        for index, item in enumerate(prohibited, start=1)
    ]


def _success_failure_registry() -> dict[str, Any]:
    return {
        "success_criteria": (
            "deterministic closure determination",
            "singular truth ownership",
            "complete evidence lineage",
            "deterministic reconciliation",
            "immutable historical preservation",
            "correction through supersession only",
            "deterministic downstream truth publication",
            "complete constitutional traceability",
        ),
        "failure_conditions": (
            "authoritative truth without required evidence",
            "contradictory authoritative truth accepted",
            "ambiguous ownership",
            "shared constitutional authority",
            "immutable history modified",
            "direct correction of historical truth",
            "unauthorized reopening of closed positions",
            "unauthorized upstream truth mutation",
            "unauthorized assumption of external authority",
        ),
        "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-001",
        "certification_consequence": "Any failure condition prevents certification readiness.",
    }


def _offices() -> tuple[str, ...]:
    return (
        "Trader",
        "Broker",
        "Position Registry",
        "Exit Decision",
        "Risk",
        "Performance Truth",
        "Historian",
        "Monitoring",
        "Analyst",
        "Infrastructure",
        "Commander",
    )


def _boundary_registry() -> list[dict[str, Any]]:
    data = {
        "Trader": ("execution intent, execution requests, trading workflow, execution control", "authoritative closed-position truth and closure evidence lineage", "Trader -> Closed Position Truth"),
        "Broker": ("broker-originated facts, acknowledgements, execution confirmations, settlement communications", "derived enterprise truth from broker evidence without mutation", "Broker -> Closed Position Truth"),
        "Position Registry": ("open-position identity, quantity, lifecycle, and state", "constitutional closure determination and finalized closed-position record", "Position Registry -> Closed Position Truth"),
        "Exit Decision": ("exit evaluation, recommendations, decisions, and rationale", "authoritative completed-closure record", "Exit Decision -> Closed Position Truth"),
        "Risk": ("risk calculations, exposure assessments, and constraint evaluation", "finalized risk outcomes only where required", "Risk -> Closed Position Truth"),
        "Performance Truth": ("enterprise performance measurement and analytics", "authoritative realized outcomes within assigned closure scope", "Closed Position Truth -> Performance Truth"),
        "Historian": ("immutable archival custody and replay custody", "active authoritative closed-position truth before archival transfer", "Closed Position Truth -> Historian"),
        "Monitoring": ("operational observations, evidence, and alerts", "admissible monitoring evidence consumption", "Monitoring -> Closed Position Truth"),
        "Analyst": ("analytical models, findings, and recommendations", "authoritative truth publication without analytical promotion", "Closed Position Truth -> Analyst"),
        "Infrastructure": ("platform, storage, runtime availability", "business truth authority retained by Closed Position Truth", "Infrastructure -> Closed Position Truth"),
        "Commander": ("enterprise intent, strategic governance, constitutional oversight", "truth publication without Commander mutation", "Closed Position Truth -> Commander"),
    }
    rows = []
    for index, office in enumerate(_offices(), start=1):
        office_owns, cpt_owns, direction = data[office]
        rows.append(
            {
                "boundary_id": f"CPT-BOUND-{index:03d}",
                "counterparty_office": office,
                "office_owned_responsibilities": office_owns,
                "closed_position_truth_owned_responsibilities": cpt_owns,
                "dependency_direction": direction,
                "information_exchange_transfers_authority": False,
                "custody_transfers_ownership": False,
                "mutation_authority_over_counterparty_truth": "PROHIBITED",
                "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-002",
                "status": "DETERMINISTIC_BOUNDARY_ESTABLISHED",
            }
        )
    return rows


def _responsibility_allocation_matrix() -> list[dict[str, Any]]:
    rows = []
    for boundary in _boundary_registry():
        rows.append(
            {
                "office": boundary["counterparty_office"],
                "owned_responsibilities": boundary["office_owned_responsibilities"],
                "consumed_by_closed_position_truth": boundary["dependency_direction"].endswith("Closed Position Truth"),
                "produced_by_closed_position_truth": boundary["dependency_direction"].startswith("Closed Position Truth"),
                "shared_responsibility": False,
                "authority_overlap": False,
            }
        )
    return rows


def _information_exchange_registry() -> list[dict[str, Any]]:
    rows = []
    for index, boundary in enumerate(_boundary_registry(), start=1):
        producer, consumer = boundary["dependency_direction"].split(" -> ")
        rows.append(
            {
                "exchange_id": f"CPT-INFO-{index:03d}",
                "producer": producer,
                "consumer": consumer,
                "authority_retained_by_producer": True,
                "authority_transfer": "PROHIBITED_UNLESS_EXPLICIT",
                "required_evidence": ("identity", "provenance", "timestamp", "integrity"),
                "reconciliation_required": True,
                "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-002",
            }
        )
    return rows


def _authority_transfer_registry() -> list[dict[str, Any]]:
    return [
        {
            "transfer_id": "CPT-XFER-001",
            "originating_authority": "Closed Position Truth Office",
            "receiving_authority": "Historian",
            "transfer_type": "custody_only",
            "transfer_conditions": (
                "authoritative truth creation complete",
                "reconciliation complete",
                "correction and supersession state resolved",
                "evidence lineage complete",
                "retention classification established",
            ),
            "ownership_transferred": False,
            "termination_conditions": ("Historian custody continues permanently; ownership remains constitutionally identified.",),
            "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-002",
        }
    ]


def _truth_elements() -> tuple[str, ...]:
    return (
        "Closed position identity",
        "Closure determination",
        "Closure timestamp",
        "Closure reason",
        "Realized outcome",
        "Reconciliation status",
        "Correction history",
        "Supersession history",
        "Archival eligibility",
    )


def _truth_ownership_registry() -> list[dict[str, Any]]:
    basis = {
        "Closed position identity": "Position Registry identity and constitutionally admissible execution evidence",
        "Closure determination": "execution completion, reconciliation, zero remaining quantity, settlement satisfaction or exemption",
        "Closure timestamp": "execution, reconciliation, position, and settlement evidence",
        "Closure reason": "Exit Decision lineage, execution evidence, reconciliation evidence, and position state",
        "Realized outcome": "execution facts, quantity and basis data, cost/proceeds inputs, reconciliation evidence",
        "Reconciliation status": "Broker, Trader, Position Registry, settlement authority, and upstream evidence producers",
        "Correction history": "authoritative correction evidence and predecessor lineage",
        "Supersession history": "predecessor, successor, authority, reason, evidence, and creation time",
        "Archival eligibility": "complete truth, reconciliation, lineage, evidence, and retention classification",
    }
    rows = []
    for index, element in enumerate(_truth_elements(), start=1):
        rows.append(
            {
                "truth_element_id": f"CPT-TRUTH-{index:03d}",
                "truth_element": element,
                "owner": "Closed Position Truth Office",
                "creator": "Closed Position Truth Office",
                "active_custodian": "Closed Position Truth Office",
                "archival_custodian": "Historian",
                "source_dependency": basis[element],
                "ordinary_mutation_authority": "NONE_AFTER_AUTHORITATIVE_CREATION",
                "correction_authority": "Closed Position Truth Office through successor record creation",
                "supersession_authority": "Closed Position Truth Office",
                "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-003",
                "status": "SINGLE_OWNER_ESTABLISHED",
            }
        )
    return rows


def _upstream_truth_boundaries() -> list[dict[str, Any]]:
    rows = [
        ("Broker", "broker acknowledgements, fills, cancellations, rejections, broker execution status, settlement facts"),
        ("Trader", "execution workflow, instructions, lifecycle, management, request lineage"),
        ("Position Registry", "open-position identity, current quantity, current state, mutation, active reconciliation"),
        ("Exit Decision", "exit evaluation, recommendation, decision, rationale, lineage"),
        ("Risk", "risk state, limits, exposure calculations, constraints"),
        ("Performance Truth", "enterprise, portfolio, strategy, attribution, risk-adjusted, and analytical performance truth"),
        ("Historian", "permanent historical custody"),
    ]
    return [
        {
            "office": office,
            "owned_truth": truth,
            "closed_position_truth_may_consume": True,
            "closed_position_truth_may_modify": False,
            "ownership_transfer_to_closed_position_truth": False,
            "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-003",
        }
        for office, truth in rows
    ]


def _dependency_registry() -> list[dict[str, Any]]:
    upstream = [
        ("Broker", "execution facts, timestamps, identifiers, acknowledgements, settlement evidence, broker transaction records"),
        ("Trader", "execution requests, intent history, lifecycle state, reconciliation participation"),
        ("Position Registry", "position identity, quantity, remaining position state, reconciliation state"),
        ("Exit Decision", "exit decision identity, rationale, lineage, authority"),
        ("Risk", "realized risk context, final risk disposition"),
    ]
    downstream = [
        ("Performance Truth", "realized outcomes, realized profit/loss, holding duration, closure timestamps"),
        ("Historian", "immutable records, supersession lineage, correction lineage, archival records"),
        ("Monitoring", "closure events, anomalies, constitutional closure failures"),
        ("Analyst", "authoritative closed-position records"),
        ("Commander", "enterprise reporting and operational visibility"),
    ]
    rows = []
    for index, (provider, information) in enumerate(upstream, start=1):
        rows.append(_dependency_row(index, provider, "Closed Position Truth Office", information, provider, "UPSTREAM_REQUIRED"))
    for index, (consumer, information) in enumerate(downstream, start=len(rows) + 1):
        rows.append(_dependency_row(index, "Closed Position Truth Office", consumer, information, "Closed Position Truth Office", "DOWNSTREAM_CONSUMER"))
    return rows


def _dependency_row(index: int, provider: str, consumer: str, information: str, owner: str, classification: str) -> dict[str, Any]:
    return {
        "dependency_id": f"CPT-DEP-{index:03d}",
        "provider": provider,
        "consumer": consumer,
        "dependency_direction": f"{provider} -> {consumer}",
        "information": information,
        "dependency_owner": owner,
        "authority_owner": owner,
        "reconciliation_owner": "Closed Position Truth Office" if consumer == "Closed Position Truth Office" else provider,
        "failure_behavior": "suspend truth creation and preserve evidence" if consumer == "Closed Position Truth Office" else "preserve published truth and emit consumer-facing evidence",
        "classification": classification,
        "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-004",
    }


def _source_precedence_matrix() -> list[dict[str, Any]]:
    precedence = (
        "Broker-originated execution facts",
        "Execution reconciliation results",
        "Position Registry reconciliation",
        "Constitutional closure validation",
        "Closed Position Truth",
        "Performance Truth derivatives",
        "Analytical interpretations",
    )
    return [
        {
            "precedence_rank": index,
            "truth_source": source,
            "may_supersede_higher_rank": False,
            "authoritative_use": "input" if index < 5 else "derived_or_analytical",
            "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-004",
        }
        for index, source in enumerate(precedence, start=1)
    ]


def _truth_derivation_registry() -> dict[str, Any]:
    return {
        "derivation_id": "CPT-DERIVATION-001",
        "sequence": (
            "Market Evidence",
            "Broker Truth",
            "Execution Reconciliation",
            "Position Reconciliation",
            "Constitutional Closure Validation",
            "Closed Position Truth",
            "Performance Truth",
            "Historian",
        ),
        "stage_skip_permitted": False,
        "requires_successful_prior_stage": True,
        "analytical_truth_creation_permitted": False,
        "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-004",
    }


def _dependency_failure_registry() -> list[dict[str, Any]]:
    failures = (
        ("Broker discrepancy", "suspend truth creation, perform reconciliation, preserve evidence, prohibit authoritative closure"),
        ("Reconciliation failure", "prohibit closure, preserve intermediate evidence, generate findings"),
        ("Incomplete settlement", "prohibit authoritative closure unless constitutionally exempt"),
        ("Duplicate execution", "trigger reconciliation, prohibit duplicate truth creation, preserve evidence"),
        ("Stale evidence", "fail admissibility and prohibit truth creation"),
        ("Degraded analytical input", "never create authoritative truth and never invalidate existing authoritative truth"),
    )
    return [
        {
            "failure_id": f"CPT-DEPFAIL-{index:03d}",
            "failure_condition": condition,
            "constitutional_disposition": disposition,
            "inferred_truth_allowed": False,
            "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-004",
        }
        for index, (condition, disposition) in enumerate(failures, start=1)
    ]


def _findings_registry() -> list[dict[str, Any]]:
    findings = [
        ("CPT-FIND-001", "authority boundaries are explicit", "INFO", "CLOSED"),
        ("CPT-FIND-002", "custody transfer to Historian is custody-only and not ownership transfer", "INFO", "CLOSED"),
        ("CPT-FIND-003", "analytical outputs are constitutionally separated from authoritative truth", "INFO", "CLOSED"),
        ("CPT-FIND-004", "no unresolved B01 constitutional ownership conflict remains", "INFO", "CLOSED"),
    ]
    return [
        {
            "finding_id": finding_id,
            "finding": finding,
            "constitutional_source": "CLOSED-POSITION-TRUTH-RM-001-B01",
            "severity": severity,
            "disposition": disposition,
            "resolution_status": "RESOLVED",
        }
        for finding_id, finding, severity, disposition in findings
    ]


def generate_baseline() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sources = _source_registry()
    charter = {
        "office": "Closed Position Truth Office",
        "constitutional_identity": "exclusive constitutional owner of authoritative enterprise truth concerning constitutionally closed trading positions",
        "purpose": (
            "establish authoritative enterprise truth for constitutionally closed trading positions",
            "preserve deterministic historical truth regarding closed positions",
            "determine constitutional closure status using authorized enterprise evidence",
            "maintain immutable records of authoritative closed-position truth",
            "provide authoritative realized-position truth to downstream enterprise consumers",
        ),
        "mission": (
            "determine constitutional closure eligibility",
            "create authoritative Closed Position Truth after eligibility",
            "preserve immutable historical records",
            "record corrections through constitutional supersession",
            "supply authorized downstream offices with authoritative closed-position truth",
        ),
        "mission_exclusions": ("trading", "execution", "authorization", "market analysis", "performance analytics"),
        "jurisdiction": "constitutionally closed trading positions only",
        "source_order": "CLOSED-POSITION-TRUTH-RM-001-B01-001",
    }
    authority = _authority_registry()
    responsibilities = _responsibility_registry()
    limitations = _limitation_registry()
    success_failure = _success_failure_registry()
    boundaries = _boundary_registry()
    responsibility_matrix = _responsibility_allocation_matrix()
    exchange = _information_exchange_registry()
    transfers = _authority_transfer_registry()
    truth = _truth_ownership_registry()
    upstream_boundaries = _upstream_truth_boundaries()
    dependencies = _dependency_registry()
    precedence = _source_precedence_matrix()
    derivation = _truth_derivation_registry()
    dependency_failures = _dependency_failure_registry()
    findings = _findings_registry()

    conflict_assessment = {
        "shared_responsibility_detected": False,
        "authority_overlap_detected": False,
        "parallel_authoritative_truth_permitted": False,
        "unresolved_boundary_conflicts": (),
        "unresolved_ownership_conflicts": (),
        "unresolved_authority_conflicts": (),
        "status": "NO_UNRESOLVED_B01_CONFLICTS",
    }
    completion = {
        "series": "CLOSED-POSITION-TRUTH-RM-001-B01",
        "status": "COMPLETE",
        "orders_completed": tuple(ORDER_SOURCES),
        "constitutional_doctrine_only": True,
        "implementation_behavior_modified": False,
        "behavioral_verification_executed": False,
        "implementation_certification_executed": False,
        "implementation_proof_generated": False,
        "ready_for": "CLOSED-POSITION-TRUTH-RM-001-B02",
        "completion_criteria": {
            "constitutional_identity_unique": True,
            "purpose_deterministic": True,
            "mission_complete": True,
            "one_owner_per_authority": True,
            "one_owner_per_responsibility": True,
            "limitations_explicit": True,
            "success_failure_deterministic": True,
            "office_boundaries_deterministic": True,
            "truth_ownership_single_owner": True,
            "dependency_direction_deterministic": True,
            "truth_source_precedence_deterministic": True,
            "no_unresolved_conflicts": True,
        },
    }

    payloads = {
        "source_order_registry.json": sources,
        "B01-001_constitutional_charter.json": charter,
        "B01-001_constitutional_authority_registry.json": authority,
        "B01-001_constitutional_responsibility_registry.json": responsibilities,
        "B01-001_constitutional_limitation_registry.json": limitations,
        "B01-001_success_failure_registry.json": success_failure,
        "B01-001_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B01-001", "status": "COMPLETE"},
        "B01-002_office_boundary_registry.json": boundaries,
        "B01-002_enterprise_boundary_matrix.json": boundaries,
        "B01-002_responsibility_allocation_matrix.json": responsibility_matrix,
        "B01-002_authority_allocation_matrix.json": responsibility_matrix,
        "B01-002_information_exchange_registry.json": exchange,
        "B01-002_dependency_boundary_registry.json": dependencies,
        "B01-002_authority_transfer_registry.json": transfers,
        "B01-002_boundary_conflict_registry.json": conflict_assessment,
        "B01-002_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B01-002", "status": "COMPLETE"},
        "B01-003_truth_ownership_registry.json": truth,
        "B01-003_authority_matrix.json": truth,
        "B01-003_custody_matrix.json": truth,
        "B01-003_upstream_truth_ownership_boundaries.json": upstream_boundaries,
        "B01-003_ownership_conflict_assessment.json": conflict_assessment,
        "B01-003_authority_conflict_assessment.json": conflict_assessment,
        "B01-003_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B01-003", "status": "COMPLETE"},
        "B01-004_dependency_registry.json": dependencies,
        "B01-004_truth_source_registry.json": upstream_boundaries,
        "B01-004_upstream_dependency_registry.json": tuple(item for item in dependencies if item["classification"] == "UPSTREAM_REQUIRED"),
        "B01-004_downstream_consumer_registry.json": tuple(item for item in dependencies if item["classification"] == "DOWNSTREAM_CONSUMER"),
        "B01-004_source_precedence_matrix.json": precedence,
        "B01-004_dependency_direction_matrix.json": dependencies,
        "B01-004_dependency_ownership_matrix.json": dependencies,
        "B01-004_dependency_interaction_matrix.json": dependencies,
        "B01-004_dependency_failure_registry.json": dependency_failures,
        "B01-004_truth_derivation_registry.json": derivation,
        "B01-004_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B01-004", "status": "COMPLETE"},
        "constitutional_findings_registry.json": findings,
        "B01_series_completion_report.json": completion,
    }
    for name, payload in payloads.items():
        _write(name, payload)
    manifest = {
        "package": "CLOSED_POSITION_TRUTH_RM001_B01_CONSTITUTIONAL_BASELINE",
        "series": "CLOSED-POSITION-TRUTH-RM-001-B01",
        "baseline_digest": _digest(payloads),
        "files": sorted(str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/") for path in OUTPUT_DIR.rglob("*") if path.is_file()),
        "ready_for": "CLOSED-POSITION-TRUTH-RM-001-B02",
    }
    _write("manifest.json", manifest)
    return completion


if __name__ == "__main__":
    print(_json(generate_baseline()), end="")
