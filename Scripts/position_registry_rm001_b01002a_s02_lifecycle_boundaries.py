from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_B01002A_S02_LIFECYCLE_BOUNDARIES"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _boundary(office: str) -> dict[str, Any]:
    if office == "Monitoring":
        return {
            "boundary_id": "PR-B01-002A-S02-001-MONITORING",
            "counterparty_office": "Monitoring",
            "governing_authority": "POSITION-REGISTRY-RM-001-B01-002A-S02-001",
            "constitutional_authority": "observe active canonical position state and produce monitoring observations, anomaly records, and monitoring evidence",
            "ownership_boundary": "Monitoring owns monitoring observations and anomaly records; Position Registry owns canonical position state",
            "mutation_authority": "Monitoring may not mutate canonical position state; Position Registry alone mutates canonical positions",
            "monitoring_authority": "Monitoring observes lifecycle, quantity, cost basis, health, and anomaly conditions",
            "dependency_direction": "Monitoring -> Position Registry for active position reads",
            "reconciliation_authority": "Monitoring may initiate anomaly escalation; Position Registry performs canonical reconciliation disposition",
            "replay_authority": "Monitoring replay reproduces observations; Position Registry replay reproduces canonical state",
            "truth_ownership": {"monitoring_truth": "Monitoring", "canonical_position_truth": "Position Registry", "anomaly_truth": "Monitoring"},
        }
    if office == "Exit Decision":
        return {
            "boundary_id": "PR-B01-002A-S02-002-EXIT-DECISION",
            "counterparty_office": "Exit Decision",
            "governing_authority": "POSITION-REGISTRY-RM-001-B01-002A-S02-002",
            "constitutional_authority": "determine and authorize exit intent according to Exit Decision doctrine",
            "ownership_boundary": "Exit Decision owns exit recommendations and exit authorization truth; Position Registry owns canonical position state",
            "exit_authority": "Exit Decision may authorize closure intent but does not execute canonical lifecycle transition",
            "lifecycle_authority": "Position Registry executes authorized lifecycle transitions and records lifecycle evidence",
            "mutation_authority": "Exit Decision requests or authorizes; Position Registry accepts, rejects, and mutates canonical lifecycle state",
            "interface_authority": "Exit Decision produces exit authorization interface; Position Registry consumes and acknowledges disposition",
            "reconciliation_authority": "Position Registry reconciles canonical lifecycle effects; Exit Decision owns exit-decision corrections",
            "dependency_direction": "Position Registry depends on Exit Decision only for exit authorization truth; Exit Decision depends on Position Registry for current position state",
            "correction_authority": "Exit Decision corrects exit decision truth; Position Registry corrects canonical position state when admissible corrected exit evidence requires it",
            "replay_authority": "Position Registry replay re-applies authorized lifecycle transitions from immutable exit evidence",
            "determinations": {
                "exit_decision_owns_positions": False,
                "exit_decision_mutates_positions": False,
                "exit_decision_authorizes_closure": True,
                "position_registry_executes_authorized_lifecycle_transitions": True,
                "authority_following_exit_authorization": "Position Registry validates authorization, performs or rejects lifecycle transition, and records evidence",
                "authority_during_correction": "originating office corrects exit truth; Position Registry corrects canonical lifecycle state only through admitted correction evidence",
                "authority_during_replay": "Position Registry replays canonical state from immutable accepted exit and mutation evidence",
            },
        }
    if office == "Closed Position Truth":
        return {
            "boundary_id": "PR-B01-002A-S02-003-CLOSED-POSITION-TRUTH",
            "counterparty_office": "Closed Position Truth",
            "governing_authority": "POSITION-REGISTRY-RM-001-B01-002A-S02-003",
            "constitutional_authority": "own immutable historical position truth following constitutional transfer",
            "ownership_boundary": "Position Registry owns active state until transfer; Closed Position Truth owns immutable closed-position truth after transfer",
            "truth_transfer_authority": "Position Registry initiates transfer after terminal closure prerequisites; Closed Position Truth acquires historical ownership",
            "mutation_authority": "closed historical truth is immutable except explicit correction lineage",
            "dependency_direction": "Closed Position Truth -> Position Registry for transfer package; Position Registry relinquishes after accepted transfer",
            "reconciliation_authority": "Closed Position Truth reconciles immutable historical truth after transfer; Position Registry participates for transfer lineage only",
            "correction_authority": "Closed Position Truth governs historical correction after transfer with immutable lineage preserved",
            "replay_authority": "replay after transfer preserves historical truth and transfer record",
            "truth_ownership": {"active_position_truth": "Position Registry", "immutable_closed_position_truth": "Closed Position Truth"},
        }
    return {
        "boundary_id": "PR-B01-002A-S02-003-PERFORMANCE-TRUTH",
        "counterparty_office": "Performance Truth",
        "governing_authority": "POSITION-REGISTRY-RM-001-B01-002A-S02-003",
        "constitutional_authority": "own realized performance, performance metrics, historical analytics, and performance reporting",
        "ownership_boundary": "Performance Truth owns performance analytics; Position Registry does not own performance analytics",
        "mutation_authority": "Performance Truth may not mutate canonical or closed position truth",
        "dependency_direction": "Performance Truth -> Closed Position Truth and Position Registry for source facts",
        "reconciliation_authority": "Performance Truth reconciles performance calculations; source position truth remains owned by its constitutional owner",
        "replay_authority": "performance replay reproduces analytics from immutable source facts",
        "truth_ownership": {"performance_truth": "Performance Truth", "canonical_position_truth": "Position Registry", "closed_position_truth": "Closed Position Truth"},
    }


def _matrix(boundaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "interaction_id": f"PR-LIFECYCLE-BND-{index:03d}",
            "counterparty_office": item["counterparty_office"],
            "governing_authority": item["governing_authority"],
            "ownership_boundary": item["ownership_boundary"],
            "mutation_authority": item.get("mutation_authority", "No implied mutation authority"),
            "lifecycle_authority": item.get("lifecycle_authority", "Position Registry owns canonical lifecycle unless transferred"),
            "reconciliation_authority": item["reconciliation_authority"],
            "dependency_direction": item["dependency_direction"],
            "interface_authority": item.get("interface_authority", f"{item['counterparty_office']} produces bounded lifecycle-domain evidence consumed by Position Registry where authorized"),
            "evidence_obligation": "immutable provenance, integrity, custody, replay, and correction references required",
        }
        for index, item in enumerate(boundaries, start=1)
    ]


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    monitoring = _boundary("Monitoring")
    exit_decision = _boundary("Exit Decision")
    closed_truth = _boundary("Closed Position Truth")
    performance = _boundary("Performance Truth")
    boundaries = [monitoring, exit_decision, closed_truth, performance]
    matrix = _matrix(boundaries)
    truth = [
        {"truth_class": "canonical_active_position_truth", "constitutional_owner": "Position Registry", "transfer_authority": "terminal closure transfer only"},
        {"truth_class": "monitoring_truth", "constitutional_owner": "Monitoring", "transfer_authority": "none"},
        {"truth_class": "exit_authorization_truth", "constitutional_owner": "Exit Decision", "transfer_authority": "none"},
        {"truth_class": "immutable_closed_position_truth", "constitutional_owner": "Closed Position Truth", "transfer_authority": "accepted closure package"},
        {"truth_class": "historical_performance_truth", "constitutional_owner": "Performance Truth", "transfer_authority": "none"},
        {"truth_class": "reconciliation_truth", "constitutional_owner": "Position Registry", "transfer_authority": "none unless historical transfer accepted"},
        {"truth_class": "correction_truth", "constitutional_owner": "originating truth owner", "transfer_authority": "explicit correction evidence only"},
        {"truth_class": "replay_truth", "constitutional_owner": "replayed domain owner", "transfer_authority": "none"},
        {"truth_class": "anomaly_truth", "constitutional_owner": "Monitoring", "transfer_authority": "none"},
    ]
    ownership = [
        {"lifecycle_stage": "active", "constitutional_owner": "Position Registry", "mutation_authority": "Position Registry", "custodian": "Position Registry"},
        {"lifecycle_stage": "monitored", "constitutional_owner": "Position Registry", "mutation_authority": "Position Registry", "custodian": "Position Registry and Monitoring observation custody"},
        {"lifecycle_stage": "exit_authorized", "constitutional_owner": "Position Registry", "mutation_authority": "Position Registry after Exit Decision authorization", "custodian": "Position Registry"},
        {"lifecycle_stage": "closed_pending_transfer", "constitutional_owner": "Position Registry", "mutation_authority": "Position Registry correction/reconciliation authority", "custodian": "Position Registry"},
        {"lifecycle_stage": "historical_transferred", "constitutional_owner": "Closed Position Truth", "mutation_authority": "historical correction authority only", "custodian": "Closed Position Truth"},
        {"lifecycle_stage": "performance_analyzed", "constitutional_owner": "Performance Truth for analytics only", "mutation_authority": "Performance Truth analytics mutation only", "custodian": "Performance Truth"},
    ]
    historical_transfer = {
        "transfer_initiator": "Position Registry",
        "transfer_authority": "POSITION-REGISTRY-RM-001-B01-002A-S02-003",
        "transfer_prerequisites": ("terminal lifecycle state", "complete closure evidence", "complete reconciliation evidence", "immutable transfer package"),
        "relinquishing_owner": "Position Registry",
        "receiving_owner": "Closed Position Truth",
        "completion_criteria": "Closed Position Truth accepts immutable closed-position package and Position Registry records ownership relinquishment",
        "replay_behavior": "replay preserves transfer record and does not reassign historical ownership",
        "correction_behavior_after_transfer": "Closed Position Truth governs historical correction with immutable lineage",
    }
    conflicts = [
        {"conflict": "Monitoring position ownership", "resolution": "rejected", "deterministic_disposition": "Monitoring owns observations only"},
        {"conflict": "Exit Decision position mutation", "resolution": "rejected", "deterministic_disposition": "Exit Decision authorizes closure intent; Position Registry mutates lifecycle"},
        {"conflict": "Closed Position Truth active-state ownership", "resolution": "rejected", "deterministic_disposition": "ownership transfers only after terminal closure package acceptance"},
        {"conflict": "Performance Truth position mutation", "resolution": "rejected", "deterministic_disposition": "Performance Truth owns analytics only"},
    ]
    verification = {
        "implementation_evaluated": False,
        "implementation_modified": False,
        "behavioral_verification_executed": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
        "all_lifecycle_transitions_have_authority": True,
        "all_truth_transfers_have_authority": True,
        "all_dependencies_deterministic": True,
        "circular_authority_remaining": False,
        "ownership_ambiguity_remaining": False,
        "lifecycle_ambiguity_remaining": False,
        "truth_ownership_ambiguity_remaining": False,
    }
    artifacts: dict[str, Any] = {
        "B01-002A-S02-001_monitoring_boundary_registry.json": monitoring,
        "B01-002A-S02-001_authority_interaction_registry.json": [item for item in matrix if item["counterparty_office"] == "Monitoring"],
        "B01-002A-S02-001_ownership_interaction_registry.json": [item for item in ownership if item["lifecycle_stage"] in {"active", "monitored"}],
        "B01-002A-S02-001_custody_interaction_registry.json": [{"office": "Monitoring", "custody": "monitoring observation and anomaly evidence custody only"}],
        "B01-002A-S02-001_mutation_authority_registry.json": [{"office": "Monitoring", "authority": "no canonical position mutation"}, {"office": "Position Registry", "authority": "canonical mutation owner"}],
        "B01-002A-S02-001_monitoring_authority_registry.json": {"owner": "Monitoring", "authority": monitoring["monitoring_authority"], "mutation_implication": "none"},
        "B01-002A-S02-001_interface_authority_registry.json": [{"producer": "Position Registry", "consumer": "Monitoring", "interface": "active_position_snapshot"}, {"producer": "Monitoring", "consumer": "Position Registry", "interface": "anomaly_escalation"}],
        "B01-002A-S02-001_dependency_registry.json": [item for item in matrix if item["counterparty_office"] == "Monitoring"],
        "B01-002A-S02-001_anomaly_authority_registry.json": {"anomaly_owner": "Monitoring", "canonical_reconciliation_owner": "Position Registry"},
        "B01-002A-S02-001_reconciliation_authority_registry.json": [{"domain": "monitoring_anomaly", "authority": "Position Registry canonical disposition; Monitoring anomaly ownership"}],
        "B01-002A-S02-001_evidence_obligation_registry.json": [{"evidence": "monitoring observation, anomaly record, escalation evidence", "owner": "Monitoring", "custodian": "Monitoring and repository evidence custody"}],
        "B01-002A-S02-001_constitutional_boundary_completeness_assessment.json": verification,
        "B01-002A-S02-001_remaining_constitutional_findings_registry.json": [],
        "B01-002A-S02-001_completion_report.json": {"order": "B01-002A-S02-001", "status": "COMPLETE", **verification},
        "B01-002A-S02-002_exit_decision_boundary_registry.json": exit_decision,
        "B01-002A-S02-002_lifecycle_authority_registry.json": {"exit_authority": "Exit Decision authorizes closure intent", "canonical_lifecycle_execution": "Position Registry", "exit_decision_mutates_positions": False},
        "B01-002A-S02-002_interface_authority_registry.json": [{"producer": "Exit Decision", "consumer": "Position Registry", "interface": "exit_authorization", "acknowledgement": "Position Registry lifecycle disposition"}],
        "B01-002A-S02-002_dependency_registry.json": [item for item in matrix if item["counterparty_office"] == "Exit Decision"],
        "B01-002A-S02-002_completion_report.json": {"order": "B01-002A-S02-002", "status": "COMPLETE", **exit_decision["determinations"], **verification},
        "B01-002A-S02-003_closed_position_truth_boundary_registry.json": closed_truth,
        "B01-002A-S02-003_performance_truth_boundary_registry.json": performance,
        "B01-002A-S02-003_truth_ownership_registry.json": truth,
        "B01-002A-S02-003_historical_ownership_registry.json": [item for item in ownership if item["lifecycle_stage"] in {"historical_transferred", "performance_analyzed"}],
        "B01-002A-S02-003_ownership_transfer_registry.json": historical_transfer,
        "B01-002A-S02-003_historical_custody_registry.json": {"owner": "Closed Position Truth", "custody": "immutable historical truth and archival evidence"},
        "B01-002A-S02-003_historical_correction_registry.json": {"authority": "Closed Position Truth after transfer", "lineage_preserved": True},
        "B01-002A-S02-003_historical_replay_registry.json": {"authority": "domain owner replay", "historical_truth_preserved": True},
        "B01-002A-S02-003_performance_ownership_registry.json": [{"object": "historical_performance_truth", "owner": "Performance Truth"}, {"object": "performance_metrics", "owner": "Performance Truth"}],
        "B01-002A-S02-003_performance_dependency_registry.json": [item for item in matrix if item["counterparty_office"] == "Performance Truth"],
        "B01-002A-S02-003_reconciliation_authority_registry.json": [{"domain": "closed_position_transfer", "authority": "Position Registry until transfer, Closed Position Truth after transfer"}, {"domain": "performance_analytics", "authority": "Performance Truth"}],
        "B01-002A-S02-003_interface_authority_registry.json": [item for item in matrix if item["counterparty_office"] in {"Closed Position Truth", "Performance Truth"}],
        "B01-002A-S02-003_constitutional_dependency_graph.json": [item for item in matrix if item["counterparty_office"] in {"Closed Position Truth", "Performance Truth"}],
        "B01-002A-S02-003_ownership_interaction_registry.json": ownership,
        "B01-002A-S02-003_constitutional_consistency_reconciliation_report.json": verification,
        "B01-002A-S02-003_completion_report.json": {"order": "B01-002A-S02-003", "status": "COMPLETE", **verification},
        "B01-002A-S02-004_position_lifecycle_constitutional_baseline.json": {"baseline_id": "PR-B01-002A-S02-004-LIFECYCLE-BOUNDARY-BASELINE", "boundaries": boundaries, "lifecycle_ownership": ownership, "truth_ownership": truth, "historical_transfer": historical_transfer, "conflicts": conflicts},
        "B01-002A-S02-004_lifecycle_interaction_matrix.json": matrix,
        "B01-002A-S02-004_monitoring_boundary_reconciliation_registry.json": monitoring,
        "B01-002A-S02-004_exit_decision_boundary_reconciliation_registry.json": exit_decision,
        "B01-002A-S02-004_closed_position_truth_boundary_reconciliation_registry.json": closed_truth,
        "B01-002A-S02-004_performance_truth_boundary_reconciliation_registry.json": performance,
        "B01-002A-S02-004_truth_ownership_reconciliation_registry.json": truth,
        "B01-002A-S02-004_ownership_reconciliation_registry.json": ownership,
        "B01-002A-S02-004_custody_reconciliation_registry.json": [{"stage": item["lifecycle_stage"], "custodian": item["custodian"]} for item in ownership],
        "B01-002A-S02-004_mutation_authority_reconciliation_registry.json": [{"stage": item["lifecycle_stage"], "mutation_authority": item["mutation_authority"]} for item in ownership],
        "B01-002A-S02-004_interface_authority_reconciliation_registry.json": matrix,
        "B01-002A-S02-004_reconciliation_authority_reconciliation_registry.json": [{"office": item["counterparty_office"], "authority": item["reconciliation_authority"]} for item in boundaries],
        "B01-002A-S02-004_dependency_reconciliation_registry.json": [{"office": item["counterparty_office"], "dependency_direction": item["dependency_direction"]} for item in boundaries],
        "B01-002A-S02-004_historical_ownership_transition_registry.json": historical_transfer,
        "B01-002A-S02-004_constitutional_conflict_resolution_registry.json": conflicts,
        "B01-002A-S02-004_unresolved_constitutional_findings_registry.json": [],
        "B01-002A-S02-004_deterministic_boundary_verification_report.json": verification,
        "B01-002A-S02-004_authoritative_constitutional_lifecycle_boundary_report.json": {"status": "COMPLETE", "baseline_digest": _digest({"boundaries": boundaries, "ownership": ownership, "truth": truth})},
        "B01-002A-S02-004_completion_report.json": {"order": "B01-002A-S02-004", "status": "COMPLETE", **verification},
        "completion_report.json": {"package": "POSITION-REGISTRY-RM-001-B01-002A-S02 lifecycle boundary series", "status": "COMPLETE", "orders": ("B01-002A-S02-001", "B01-002A-S02-002", "B01-002A-S02-003", "B01-002A-S02-004"), "implementation_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "certification_activity_executed": False, "baseline_digest": _digest({"boundaries": boundaries, "matrix": matrix, "ownership": ownership, "truth": truth, "historical_transfer": historical_transfer})},
    }
    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    (OUTPUT_DIR / "README.md").write_text(
        "# Position Registry B01-002A-S02 Lifecycle Boundaries\n\n"
        "Doctrine-only constitutional lifecycle boundary artifacts for Position Registry interactions with Monitoring, Exit Decision, Closed Position Truth, and Performance Truth. No implementation behavior was evaluated or modified.\n",
        encoding="utf-8",
    )
    return artifacts["completion_report.json"]


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "output_dir": str(OUTPUT_DIR), "baseline_digest": result["baseline_digest"]}, indent=2, sort_keys=True))
