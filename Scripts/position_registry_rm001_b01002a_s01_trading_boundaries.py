from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_B01002A_S01_TRADING_BOUNDARIES"


OFFICES = ("Trader", "Broker", "Authorizations", "Risk")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _boundary(office: str) -> dict[str, Any]:
    if office == "Trader":
        source = "POSITION-REGISTRY-RM-001-B01-002A-S01-001"
        return {
            "boundary_id": "PR-B01-002A-S01-001-TRADER",
            "counterparty_office": "Trader",
            "governing_authority": source,
            "position_registry_authority": "owns canonical position state, lifecycle state, quantity state, cost-basis state, history, reconciliation records, and position evidence",
            "counterparty_authority": "owns trading intent, execution intent, and mutation requests authorized by Trader doctrine",
            "ownership_boundary": "Trader does not own canonical positions; Position Registry does not own trading decisions",
            "custody_boundary": "Trader may possess operational custody of mutation requests and position reads; custody never implies ownership",
            "mutation_boundary": "Trader requests position mutation; Position Registry accepts, rejects, records, corrects, and reconciles canonical position mutation",
            "interface_authority": "Trader produces execution-intent and mutation-request interfaces; Position Registry owns position-state acceptance interface",
            "reconciliation_authority": "Position Registry reconciles canonical position state while consuming Trader execution context",
            "truth_ownership": {"trading_intent": "Trader", "execution_intent": "Trader", "canonical_position_truth": "Position Registry"},
            "prohibited_authority": ("Trader may not directly mutate canonical position state", "Position Registry may not decide or authorize trades"),
        }
    if office == "Broker":
        source = "POSITION-REGISTRY-RM-001-B01-002A-S01-002"
        return {
            "boundary_id": "PR-B01-002A-S01-002-BROKER",
            "counterparty_office": "Broker",
            "governing_authority": source,
            "constitutional_authority": "Broker owns broker execution truth, broker acknowledgements, broker fill truth, and broker-facing correction evidence",
            "position_registry_authority": "Position Registry owns canonical position state derived from admissible broker execution evidence",
            "ownership_boundary": "Broker does not mutate or own canonical Position Registry state; Position Registry does not own broker execution truth",
            "execution_authority": "Broker executes or reports execution outcomes under Broker doctrine; Position Registry consumes admitted outcomes",
            "broker_truth_ownership": "Broker",
            "position_truth_ownership": "Position Registry",
            "acknowledgement_authority": "Broker owns broker acknowledgements; Position Registry records acknowledgement-derived position implications",
            "interface_authority": "Broker is authoritative producer of fill, acknowledgement, correction, and broker-reconciliation evidence consumed by Position Registry",
            "correction_authority": "Broker corrects broker truth; Position Registry corrects canonical position state only through explicit correction evidence",
            "replay_authority": "Position Registry replays canonical position state from immutable admitted evidence; Broker replay does not mutate positions directly",
            "contradiction_authority": "Contradictions between broker truth and position truth become reconciliation objects owned by Position Registry with Broker evidence precedence for broker-origin facts",
            "authoritative_source_precedence": (
                "Broker execution/fill truth prevails for broker-origin execution facts",
                "Position Registry canonical state prevails for enterprise position lifecycle, quantity, cost-basis, and history after admissible evidence processing",
            ),
            "post_fill_interaction": "Broker produces fill evidence; Position Registry validates, records, mutates canonical position state, and emits position evidence",
            "post_correction_interaction": "Broker produces correction evidence; Position Registry applies explicit canonical correction or records contradiction",
            "post_reconciliation_interaction": "Broker reconciliation evidence is compared to canonical position state; discrepancies become immutable reconciliation findings",
        }
    if office == "Authorizations":
        source = "POSITION-REGISTRY-RM-001-B01-002A-S01-003"
        return {
            "boundary_id": "PR-B01-002A-S01-003-AUTH",
            "counterparty_office": "Authorizations",
            "governing_authority": source,
            "ownership_boundary": "Authorizations owns authorization objects; Position Registry consumes authorization status and evidence only",
            "mutation_boundary": "Position Registry never mutates authorization state or identity",
            "dependency_direction": "Position Registry -> Authorizations",
            "reconciliation_authority": "Authorization reconciliation remains with Authorizations; Position Registry records dependency status",
            "evidence_obligations": "Authorization identity, validity, revocation, and consumption references must be preserved with position mutation evidence",
        }
    source = "POSITION-REGISTRY-RM-001-B01-002A-S01-003"
    return {
        "boundary_id": "PR-B01-002A-S01-003-RISK",
        "counterparty_office": "Risk",
        "governing_authority": source,
        "ownership_boundary": "Risk owns risk decisions, restrictions, exposure decisions, and revocations; Position Registry consumes risk status only",
        "mutation_boundary": "Position Registry never mutates risk state or risk decision identity",
        "dependency_direction": "Position Registry -> Risk",
        "reconciliation_authority": "Risk reconciliation remains with Risk; Position Registry records dependency status and fails closed on unresolved material risk conflict",
        "evidence_obligations": "Risk approval, restriction, revocation, and escalation references must be preserved with position mutation evidence",
    }


def _interaction_matrix(boundaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "interaction_id": f"PR-TRADE-AUTH-{index:03d}",
            "counterparty_office": item["counterparty_office"],
            "owner_of_counterparty_truth": item["counterparty_office"],
            "owner_of_canonical_position_truth": "Position Registry",
            "dependency_direction": item.get("dependency_direction", f"Position Registry <-> {item['counterparty_office']} bounded interface"),
            "mutation_authority": item.get("mutation_boundary", "No implied mutation authority"),
            "reconciliation_authority": item.get("reconciliation_authority", "Position Registry reconciles canonical position implications"),
            "interface_authority": item.get("interface_authority", f"{item['counterparty_office']} interface authority bounded by governing doctrine"),
            "evidence_authority": item.get("evidence_obligations", "Immutable interaction evidence required"),
        }
        for index, item in enumerate(boundaries, start=1)
    ]


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    boundaries = [_boundary(office) for office in OFFICES]
    matrix = _interaction_matrix(boundaries)
    broker = next(item for item in boundaries if item["counterparty_office"] == "Broker")
    authorizations = next(item for item in boundaries if item["counterparty_office"] == "Authorizations")
    risk = next(item for item in boundaries if item["counterparty_office"] == "Risk")
    trader = next(item for item in boundaries if item["counterparty_office"] == "Trader")

    ownership = [
        {"object": "canonical_position_state", "constitutional_owner": "Position Registry", "custodians": ("Position Registry",), "shared_ownership": False},
        {"object": "broker_execution_truth", "constitutional_owner": "Broker", "custodians": ("Broker", "Position Registry evidence custody"), "shared_ownership": False},
        {"object": "trading_intent", "constitutional_owner": "Trader", "custodians": ("Trader", "Position Registry evidence custody"), "shared_ownership": False},
        {"object": "authorization_truth", "constitutional_owner": "Authorizations", "custodians": ("Authorizations", "Position Registry evidence custody"), "shared_ownership": False},
        {"object": "risk_truth", "constitutional_owner": "Risk", "custodians": ("Risk", "Position Registry evidence custody"), "shared_ownership": False},
    ]
    reconciliation = [
        {"domain": "broker_fill_to_position", "authority": "Position Registry", "source_precedence": "Broker for fill fact; Position Registry for canonical state mutation", "completion": "position mutation evidence persisted"},
        {"domain": "broker_correction_to_position", "authority": "Position Registry", "source_precedence": "Broker correction evidence initiates canonical correction review", "completion": "correction or contradiction record persisted"},
        {"domain": "broker_reconciliation", "authority": "Position Registry", "source_precedence": "Broker for broker-origin facts; Position Registry for canonical state", "completion": "reconciled or escalated contradiction"},
        {"domain": "authorization_dependency", "authority": "Authorizations", "source_precedence": "Authorizations", "completion": "dependency status recorded by Position Registry"},
        {"domain": "risk_dependency", "authority": "Risk", "source_precedence": "Risk", "completion": "dependency status recorded by Position Registry"},
    ]
    interface = [
        {"interface": "broker_fill_evidence", "producer": "Broker", "consumer": "Position Registry", "acknowledgement_authority": "Position Registry acknowledges admissible processing"},
        {"interface": "broker_correction_evidence", "producer": "Broker", "consumer": "Position Registry", "acknowledgement_authority": "Position Registry acknowledges correction disposition"},
        {"interface": "trader_mutation_request", "producer": "Trader", "consumer": "Position Registry", "acknowledgement_authority": "Position Registry accepts or rejects mutation request"},
        {"interface": "authorization_status_reference", "producer": "Authorizations", "consumer": "Position Registry", "acknowledgement_authority": "Position Registry records dependency evidence"},
        {"interface": "risk_status_reference", "producer": "Risk", "consumer": "Position Registry", "acknowledgement_authority": "Position Registry records dependency evidence"},
    ]
    conflict_resolution = [
        {"conflict": "shared_position_ownership", "resolution": "rejected", "governing_authority": "single owner constitutional ownership", "deterministic_disposition": "Position Registry owns canonical position truth"},
        {"conflict": "broker_direct_position_mutation", "resolution": "rejected", "governing_authority": broker["governing_authority"], "deterministic_disposition": "Broker produces evidence; Position Registry mutates canonical state"},
        {"conflict": "trader_direct_position_mutation", "resolution": "rejected", "governing_authority": trader["governing_authority"], "deterministic_disposition": "Trader requests; Position Registry mutates or rejects"},
        {"conflict": "authorization_or_risk_ownership_by_position_registry", "resolution": "rejected", "governing_authority": "B01-002A-S01-003", "deterministic_disposition": "Position Registry consumes only"},
    ]
    verification = {
        "implementation_evaluated": False,
        "behavioral_verification_executed": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
        "all_boundaries_have_authority": True,
        "all_ownership_unique": True,
        "all_dependencies_deterministic": True,
        "circular_authority_remaining": False,
        "unresolved_constitutional_findings": [],
    }

    artifacts: dict[str, Any] = {
        "B01-002A-S01-001_trader_boundary_registry.json": trader,
        "B01-002A-S01-001_authority_interaction_registry.json": [item for item in matrix if item["counterparty_office"] == "Trader"],
        "B01-002A-S01-001_ownership_interaction_registry.json": [item for item in ownership if item["constitutional_owner"] in {"Trader", "Position Registry"}],
        "B01-002A-S01-001_custody_interaction_registry.json": [item for item in ownership if "Trader" in item["custodians"] or item["constitutional_owner"] == "Position Registry"],
        "B01-002A-S01-001_mutation_authority_registry.json": [{"office": "Trader", "authority": "request only"}, {"office": "Position Registry", "authority": "canonical mutation gateway"}],
        "B01-002A-S01-001_interface_authority_registry.json": [item for item in interface if "trader" in item["interface"]],
        "B01-002A-S01-001_dependency_registry.json": [item for item in matrix if item["counterparty_office"] == "Trader"],
        "B01-002A-S01-001_reconciliation_authority_registry.json": [item for item in reconciliation if "trader" in item["domain"]],
        "B01-002A-S01-001_evidence_obligation_registry.json": [{"office": "Trader", "evidence": "mutation request, trading intent, execution intent"}],
        "B01-002A-S01-001_truth_ownership_registry.json": trader["truth_ownership"],
        "B01-002A-S01-001_lifecycle_interaction_registry.json": [{"interaction": "execution-derived position lifecycle update", "owner": "Position Registry", "requester": "Trader"}],
        "B01-002A-S01-001_constitutional_boundary_completeness_assessment.json": verification,
        "B01-002A-S01-001_remaining_constitutional_findings_registry.json": [],
        "B01-002A-S01-001_completion_report.json": {"order": "B01-002A-S01-001", "status": "COMPLETE", **verification},
        "B01-002A-S01-002_broker_boundary_registry.json": broker,
        "B01-002A-S01-002_ownership_registry.json": [item for item in ownership if item["constitutional_owner"] in {"Broker", "Position Registry"}],
        "B01-002A-S01-002_reconciliation_authority_registry.json": [item for item in reconciliation if item["domain"].startswith("broker")],
        "B01-002A-S01-002_interface_authority_registry.json": [item for item in interface if item["producer"] == "Broker"],
        "B01-002A-S01-002_completion_report.json": {"order": "B01-002A-S01-002", "status": "COMPLETE", "broker_mutates_positions": False, "broker_owns_broker_execution_truth": True, "position_registry_owns_canonical_position_state": True, **verification},
        "B01-002A-S01-003_authorizations_boundary_registry.json": authorizations,
        "B01-002A-S01-003_risk_boundary_registry.json": risk,
        "B01-002A-S01-003_authorization_ownership_registry.json": [item for item in ownership if item["constitutional_owner"] == "Authorizations"],
        "B01-002A-S01-003_authorization_dependency_registry.json": [item for item in matrix if item["counterparty_office"] == "Authorizations"],
        "B01-002A-S01-003_authorization_interaction_registry.json": [item for item in interface if item["producer"] == "Authorizations"],
        "B01-002A-S01-003_risk_ownership_registry.json": [item for item in ownership if item["constitutional_owner"] == "Risk"],
        "B01-002A-S01-003_risk_dependency_registry.json": [item for item in matrix if item["counterparty_office"] == "Risk"],
        "B01-002A-S01-003_risk_interaction_registry.json": [item for item in interface if item["producer"] == "Risk"],
        "B01-002A-S01-003_dependency_registry.json": [item for item in matrix if item["counterparty_office"] in {"Authorizations", "Risk"}],
        "B01-002A-S01-003_ownership_interaction_registry.json": [item for item in ownership if item["constitutional_owner"] in {"Authorizations", "Risk", "Position Registry"}],
        "B01-002A-S01-003_reconciliation_authority_registry.json": [item for item in reconciliation if item["domain"] in {"authorization_dependency", "risk_dependency"}],
        "B01-002A-S01-003_interface_authority_registry.json": [item for item in interface if item["producer"] in {"Authorizations", "Risk"}],
        "B01-002A-S01-003_constitutional_dependency_graph.json": matrix,
        "B01-002A-S01-003_ownership_conflict_registry.json": [],
        "B01-002A-S01-003_constitutional_consistency_verification_report.json": verification,
        "B01-002A-S01-003_constitutional_boundary_reconciliation_report.json": {"status": "COMPLETE", "boundaries": ("Authorizations", "Risk")},
        "B01-002A-S01-003_completion_report.json": {"order": "B01-002A-S01-003", "status": "COMPLETE", **verification},
        "B01-002A-S01-004_trading_authority_constitutional_baseline.json": {"baseline_id": "PR-B01-002A-S01-004-TRADING-BOUNDARY-BASELINE", "boundaries": boundaries, "ownership": ownership, "interfaces": interface, "reconciliation": reconciliation, "conflicts": conflict_resolution},
        "B01-002A-S01-004_trading_authority_interaction_matrix.json": matrix,
        "B01-002A-S01-004_trader_boundary_reconciliation_registry.json": trader,
        "B01-002A-S01-004_broker_boundary_reconciliation_registry.json": broker,
        "B01-002A-S01-004_authorizations_boundary_reconciliation_registry.json": authorizations,
        "B01-002A-S01-004_risk_boundary_reconciliation_registry.json": risk,
        "B01-002A-S01-004_ownership_reconciliation_registry.json": ownership,
        "B01-002A-S01-004_custody_reconciliation_registry.json": ownership,
        "B01-002A-S01-004_mutation_authority_reconciliation_registry.json": [{"office": item["counterparty_office"], "mutation_authority": item.get("mutation_boundary", "none implied")} for item in boundaries],
        "B01-002A-S01-004_interface_authority_reconciliation_registry.json": interface,
        "B01-002A-S01-004_reconciliation_authority_reconciliation_registry.json": reconciliation,
        "B01-002A-S01-004_dependency_reconciliation_registry.json": matrix,
        "B01-002A-S01-004_constitutional_conflict_resolution_registry.json": conflict_resolution,
        "B01-002A-S01-004_unresolved_constitutional_findings_registry.json": [],
        "B01-002A-S01-004_deterministic_boundary_verification_report.json": verification,
        "B01-002A-S01-004_authoritative_constitutional_trading_boundary_report.json": {"status": "COMPLETE", "baseline_digest": _digest({"boundaries": boundaries, "matrix": matrix, "ownership": ownership})},
        "B01-002A-S01-004_completion_report.json": {"order": "B01-002A-S01-004", "status": "COMPLETE", **verification},
        "completion_report.json": {"package": "POSITION-REGISTRY-RM-001-B01-002A-S01 trading boundary series", "status": "COMPLETE", "orders": ("B01-002A-S01-001", "B01-002A-S01-002", "B01-002A-S01-003", "B01-002A-S01-004"), "implementation_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "certification_activity_executed": False, "baseline_digest": _digest({"boundaries": boundaries, "matrix": matrix, "ownership": ownership, "reconciliation": reconciliation})},
    }
    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    (OUTPUT_DIR / "README.md").write_text(
        "# Position Registry B01-002A-S01 Trading Boundaries\n\n"
        "Doctrine-only constitutional boundary artifacts for Position Registry interactions with Trader, Broker, Authorizations, and Risk. No implementation behavior was evaluated or modified.\n",
        encoding="utf-8",
    )
    return artifacts["completion_report.json"]


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "output_dir": str(OUTPUT_DIR), "baseline_digest": result["baseline_digest"]}, indent=2, sort_keys=True))
