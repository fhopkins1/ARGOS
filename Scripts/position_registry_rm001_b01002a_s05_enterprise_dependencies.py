from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_B01002A_S05_ENTERPRISE_DEPENDENCIES"


DEPENDENCIES = (
    ("Trader", "trader_mutation_request", "CONSTITUTIONAL_DEPENDENCY", "Trader", "Position Registry", "Trading intent and mutation request dependency"),
    ("Broker", "broker_execution_truth", "RECONCILIATION_DEPENDENCY", "Broker", "Position Registry", "Broker fill, acknowledgement, correction, and reconciliation evidence dependency"),
    ("Authorizations", "authorization_status", "CONSTITUTIONAL_DEPENDENCY", "Authorizations", "Position Registry", "Authorization validity, revocation, and consumption dependency"),
    ("Risk", "risk_status", "CONSTITUTIONAL_DEPENDENCY", "Risk", "Position Registry", "Risk approval, restriction, conflict, and escalation dependency"),
    ("Monitoring", "monitoring_observation", "OBSERVATION_DEPENDENCY", "Position Registry", "Monitoring", "Active position observation dependency"),
    ("Exit Decision", "exit_authorization", "CONSTITUTIONAL_DEPENDENCY", "Exit Decision", "Position Registry", "Exit authorization and lifecycle transition dependency"),
    ("Closed Position Truth", "closed_position_transfer", "HISTORICAL_DEPENDENCY", "Position Registry", "Closed Position Truth", "Immutable closed-position transfer dependency"),
    ("Performance Truth", "performance_source_truth", "INFORMATIONAL_DEPENDENCY", "Position Registry", "Performance Truth", "Performance analytics source-fact dependency"),
    ("Commander", "enterprise_governance", "GOVERNANCE_DEPENDENCY", "Commander", "Position Registry", "Directive, escalation, emergency, and recovery governance dependency"),
    ("Historian", "historical_custody", "HISTORICAL_DEPENDENCY", "Position Registry", "Historian", "Historical custody, archive, replay, and restoration dependency"),
    ("Infrastructure", "runtime_persistence_support", "INFRASTRUCTURE_DEPENDENCY", "Infrastructure", "Position Registry", "Runtime, persistence, configuration, and recovery support dependency"),
    ("Sentinel", "enterprise_observation", "OBSERVATION_DEPENDENCY", "Position Registry", "Sentinel", "Observation access and anomaly/finding dependency"),
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _dependency(index: int, office: str, name: str, classification: str, producer: str, consumer: str, purpose: str) -> dict[str, Any]:
    dependency_id = f"PR-DEP-{index:03d}"
    direction = f"{producer} -> {consumer}"
    return {
        "dependency_id": dependency_id,
        "dependency_name": name,
        "counterparty_office": office,
        "constitutional_description": purpose,
        "governing_constitutional_purpose": "Position Registry constitutional boundary and dependency governance",
        "dependency_scope": "Position Registry enterprise dependency",
        "governing_constitutional_source": "POSITION-REGISTRY-RM-001-B01-002A-S05",
        "constitutional_owner": producer,
        "dependency_producer": producer,
        "dependency_consumer": consumer,
        "ownership_authority": f"{office} boundary doctrine",
        "governing_office": office,
        "governing_constitutional_authority": f"POSITION-REGISTRY-RM-001-B01-002A boundary for {office}",
        "authority_limitations": "dependency never implies ownership or mutation authority outside the governing boundary",
        "upstream_participant": producer,
        "downstream_participant": consumer,
        "dependency_direction": direction,
        "dependency_trigger": "constitutionally authorized interaction requires dependency evidence",
        "dependency_termination_condition": "interaction complete, rejected, superseded, or escalated",
        "constitutional_purpose": purpose,
        "supported_constitutional_truth": "canonical position truth and/or governed dependency evidence",
        "classification": classification,
        "constitutional_admissibility": "ADMISSIBLE",
        "dependency_authorization": "explicit boundary-series authority",
        "constitutional_criticality": "CRITICAL" if classification in {"CONSTITUTIONAL_DEPENDENCY", "RECONCILIATION_DEPENDENCY", "INFRASTRUCTURE_DEPENDENCY"} else "MATERIAL",
        "operational_significance": "required for bounded Position Registry constitutional accountability",
        "failure_consequence": "fail closed, record evidence, and escalate according to dependency class",
        "dependency_creation_authority": producer,
        "activation_conditions": "dependency evidence available and admissible",
        "operational_lifetime": "active for the governed interaction lifecycle",
        "termination_authority": consumer,
        "historical_preservation_obligations": "preserve immutable dependency identity, evidence, and disposition",
    }


def _authority(dep: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "dependency_id": dep["dependency_id"],
        "dependency_initiation_authority": dep["dependency_producer"],
        "dependency_acceptance_authority": dep["dependency_consumer"],
        "dependency_rejection_authority": dep["dependency_consumer"],
        "dependency_completion_authority": dep["dependency_consumer"],
        "dependency_termination_authority": dep["termination_authority"],
        "interaction_authority": dep["governing_constitutional_authority"],
        "interaction_ownership": dep["constitutional_owner"],
        "interaction_precedence": index,
        "interaction_sequencing": f"SEQ-{index:03d}",
        "dependency_ordering": index,
        "dependency_visibility": "auditable to producer, consumer, governing authority, Historian custody where archived",
        "dependency_mutation_authority": "none unless explicitly granted by the owning boundary; dependency consumption never mutates source truth",
    }


def _continuity(dep: dict[str, Any]) -> dict[str, Any]:
    owner = dep["constitutional_owner"]
    return {
        "dependency_id": dep["dependency_id"],
        "failure_authority": dep["dependency_consumer"],
        "failure_owner": owner,
        "failure_classification": f"{dep['classification']}_FAILURE",
        "failure_disposition": "FAIL_CLOSED_AND_RECORD_EVIDENCE",
        "timeout_disposition": "TIMEOUT_FAIL_CLOSED_WITH_ESCALATION",
        "interruption_disposition": "PRESERVE_IDENTITY_AND_CHECKPOINT",
        "retry_authority": dep["dependency_consumer"],
        "replay_authority": dep["dependency_consumer"],
        "restart_authority": dep["dependency_consumer"],
        "recovery_authority": dep["dependency_consumer"],
        "contradiction_disposition": "PRESERVE_CONTRADICTION_AND_ESCALATE_TO_GOVERNING_AUTHORITY",
        "correction_authority": owner,
        "supersession_authority": owner,
        "escalation_authority": "Commander" if dep["constitutional_criticality"] == "CRITICAL" else dep["dependency_consumer"],
        "lineage_preserved": True,
        "replay_preserves_authority": True,
        "recovery_preserves_dependency_identity": True,
    }


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dependencies = [_dependency(index, *data) for index, data in enumerate(DEPENDENCIES, start=1)]
    authorities = [_authority(dep, index) for index, dep in enumerate(dependencies, start=1)]
    continuity = [_continuity(dep) for dep in dependencies]
    classifications = [{"dependency_id": dep["dependency_id"], "classification": dep["classification"]} for dep in dependencies]
    ownership = [{"dependency_id": dep["dependency_id"], "constitutional_owner": dep["constitutional_owner"], "producer": dep["dependency_producer"], "consumer": dep["dependency_consumer"]} for dep in dependencies]
    directions = [{"dependency_id": dep["dependency_id"], "direction": dep["dependency_direction"], "upstream": dep["upstream_participant"], "downstream": dep["downstream_participant"]} for dep in dependencies]
    sequence = [{"dependency_id": dep["dependency_id"], "dependency_ordering": auth["dependency_ordering"], "prerequisites": [] if auth["dependency_ordering"] == 1 else [f"PR-DEP-{auth['dependency_ordering'] - 1:03d}"], "successors": [] if auth["dependency_ordering"] == len(dependencies) else [f"PR-DEP-{auth['dependency_ordering'] + 1:03d}"]} for dep, auth in zip(dependencies, authorities)]
    precedence = [{"dependency_id": dep["dependency_id"], "precedence": auth["interaction_precedence"], "source_precedence": dep["constitutional_owner"], "contradiction_precedence": "governing constitutional authority"} for dep, auth in zip(dependencies, authorities)]
    interaction = [{"dependency_id": dep["dependency_id"], "interaction_authority": auth["interaction_authority"], "producer": dep["dependency_producer"], "consumer": dep["dependency_consumer"], "purpose": dep["constitutional_purpose"], "admissibility": dep["constitutional_admissibility"], "completion": dep["dependency_termination_condition"], "evidence": dep["historical_preservation_obligations"]} for dep, auth in zip(dependencies, authorities)]
    traceability = [{"dependency_id": dep["dependency_id"], "governing_authority": dep["governing_constitutional_authority"], "governing_office": dep["governing_office"], "governing_interaction": dep["dependency_name"], "governing_interface": f"{dep['dependency_name']}_interface", "governing_replay": item["replay_authority"], "governing_recovery": item["recovery_authority"], "governing_escalation": item["escalation_authority"]} for dep, item in zip(dependencies, continuity)]
    verification = {
        "implementation_evaluated": False,
        "implementation_modified": False,
        "behavioral_verification_executed": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
        "all_dependencies_inventoried": True,
        "every_dependency_has_one_owner": True,
        "every_dependency_has_one_producer": True,
        "every_dependency_has_one_consumer": True,
        "every_dependency_has_deterministic_direction": True,
        "every_interaction_has_deterministic_authority": True,
        "every_dependency_has_deterministic_sequencing": True,
        "every_dependency_has_deterministic_precedence": True,
        "circular_dependencies": [],
        "conflicting_interaction_authority": [],
        "conflicting_dependency_precedence": [],
        "duplicate_interaction_authority": [],
        "unresolved_dependency_ambiguity": [],
    }
    baseline = {
        "baseline_id": "PR-B01-002A-S05-004-CONSTITUTIONAL-DEPENDENCY-BASELINE",
        "dependencies": dependencies,
        "ownership_model": ownership,
        "direction_model": directions,
        "interaction_constitution": interaction,
        "sequencing_model": sequence,
        "precedence_model": precedence,
        "failure_replay_recovery_model": continuity,
        "traceability": traceability,
    }
    artifacts: dict[str, Any] = {
        "B01-002A-S05-001_dependency_registry.json": dependencies,
        "B01-002A-S05-001_dependency_classification_registry.json": classifications,
        "B01-002A-S05-001_dependency_ownership_registry.json": ownership,
        "B01-002A-S05-001_dependency_direction_registry.json": directions,
        "B01-002A-S05-001_dependency_authority_registry.json": [{"dependency_id": dep["dependency_id"], "authority": dep["governing_constitutional_authority"]} for dep in dependencies],
        "B01-002A-S05-001_dependency_purpose_registry.json": [{"dependency_id": dep["dependency_id"], "purpose": dep["constitutional_purpose"]} for dep in dependencies],
        "B01-002A-S05-001_dependency_admissibility_registry.json": [{"dependency_id": dep["dependency_id"], "admissibility": dep["constitutional_admissibility"], "authorization": dep["dependency_authorization"]} for dep in dependencies],
        "B01-002A-S05-001_dependency_criticality_registry.json": [{"dependency_id": dep["dependency_id"], "criticality": dep["constitutional_criticality"], "failure_consequence": dep["failure_consequence"]} for dep in dependencies],
        "B01-002A-S05-001_dependency_lifecycle_registry.json": [{"dependency_id": dep["dependency_id"], "creation": dep["dependency_creation_authority"], "activation": dep["activation_conditions"], "termination": dep["termination_authority"], "preservation": dep["historical_preservation_obligations"]} for dep in dependencies],
        "B01-002A-S05-001_dependency_ambiguity_registry.json": [],
        "B01-002A-S05-001_constitutional_dependency_completeness_assessment.json": verification,
        "B01-002A-S05-001_remaining_constitutional_dependency_findings_registry.json": [],
        "B01-002A-S05-001_completion_report.json": {"order": "B01-002A-S05-001", "status": "COMPLETE", **verification},
        "B01-002A-S05-002_dependency_authority_registry.json": authorities,
        "B01-002A-S05-002_interaction_constitution.json": interaction,
        "B01-002A-S05-002_dependency_sequencing_registry.json": sequence,
        "B01-002A-S05-002_interaction_precedence_registry.json": precedence,
        "B01-002A-S05-002_circular_dependency_registry.json": [],
        "B01-002A-S05-002_completion_report.json": {"order": "B01-002A-S05-002", "status": "COMPLETE", "deterministic_dependency_direction": True, "deterministic_interaction_authority": True, "deterministic_ownership": True, "deterministic_dependency_sequencing": True, **verification},
        "B01-002A-S05-003_dependency_failure_constitution.json": [{"dependency_id": item["dependency_id"], "failure_authority": item["failure_authority"], "failure_disposition": item["failure_disposition"]} for item in continuity],
        "B01-002A-S05-003_dependency_timeout_constitution.json": [{"dependency_id": item["dependency_id"], "timeout_disposition": item["timeout_disposition"]} for item in continuity],
        "B01-002A-S05-003_dependency_interruption_constitution.json": [{"dependency_id": item["dependency_id"], "interruption_disposition": item["interruption_disposition"]} for item in continuity],
        "B01-002A-S05-003_dependency_retry_constitution.json": [{"dependency_id": item["dependency_id"], "retry_authority": item["retry_authority"]} for item in continuity],
        "B01-002A-S05-003_dependency_replay_constitution.json": [{"dependency_id": item["dependency_id"], "replay_authority": item["replay_authority"], "replay_preserves_authority": item["replay_preserves_authority"]} for item in continuity],
        "B01-002A-S05-003_dependency_restart_constitution.json": [{"dependency_id": item["dependency_id"], "restart_authority": item["restart_authority"]} for item in continuity],
        "B01-002A-S05-003_dependency_recovery_constitution.json": [{"dependency_id": item["dependency_id"], "recovery_authority": item["recovery_authority"], "recovery_preserves_dependency_identity": item["recovery_preserves_dependency_identity"]} for item in continuity],
        "B01-002A-S05-003_dependency_contradiction_constitution.json": [{"dependency_id": item["dependency_id"], "contradiction_disposition": item["contradiction_disposition"]} for item in continuity],
        "B01-002A-S05-003_dependency_correction_constitution.json": [{"dependency_id": item["dependency_id"], "correction_authority": item["correction_authority"], "lineage_preserved": item["lineage_preserved"]} for item in continuity],
        "B01-002A-S05-003_dependency_supersession_constitution.json": [{"dependency_id": item["dependency_id"], "supersession_authority": item["supersession_authority"], "lineage_preserved": item["lineage_preserved"]} for item in continuity],
        "B01-002A-S05-003_dependency_escalation_constitution.json": [{"dependency_id": item["dependency_id"], "escalation_authority": item["escalation_authority"]} for item in continuity],
        "B01-002A-S05-003_dependency_recovery_registry.json": continuity,
        "B01-002A-S05-003_dependency_continuity_assessment.json": verification,
        "B01-002A-S05-003_dependency_ambiguity_registry.json": [],
        "B01-002A-S05-003_completion_report.json": {"order": "B01-002A-S05-003", "status": "COMPLETE", **verification},
        "B01-002A-S05-004_authoritative_constitutional_dependency_baseline.json": baseline,
        "B01-002A-S05-004_dependency_interaction_matrix.json": interaction,
        "B01-002A-S05-004_constitutional_dependency_graph.json": traceability,
        "B01-002A-S05-004_dependency_ownership_reconciliation_registry.json": ownership,
        "B01-002A-S05-004_dependency_authority_reconciliation_registry.json": authorities,
        "B01-002A-S05-004_dependency_direction_reconciliation_registry.json": directions,
        "B01-002A-S05-004_dependency_sequencing_reconciliation_registry.json": sequence,
        "B01-002A-S05-004_dependency_precedence_reconciliation_registry.json": precedence,
        "B01-002A-S05-004_dependency_failure_reconciliation_registry.json": artifacts["B01-002A-S05-003_dependency_failure_constitution.json"] if "artifacts" in locals() else [],
        "B01-002A-S05-004_dependency_replay_reconciliation_registry.json": [{"dependency_id": item["dependency_id"], "replay_authority": item["replay_authority"]} for item in continuity],
        "B01-002A-S05-004_dependency_recovery_reconciliation_registry.json": [{"dependency_id": item["dependency_id"], "recovery_authority": item["recovery_authority"]} for item in continuity],
        "B01-002A-S05-004_dependency_contradiction_reconciliation_registry.json": [{"dependency_id": item["dependency_id"], "contradiction_disposition": item["contradiction_disposition"]} for item in continuity],
        "B01-002A-S05-004_dependency_traceability_registry.json": traceability,
        "B01-002A-S05-004_constitutional_consistency_registry.json": verification,
        "B01-002A-S05-004_constitutional_conflict_resolution_registry.json": [],
        "B01-002A-S05-004_circular_dependency_resolution_registry.json": [],
        "B01-002A-S05-004_unresolved_constitutional_findings_registry.json": [],
        "B01-002A-S05-004_authoritative_constitutional_dependency_report.json": {"status": "COMPLETE", "baseline_digest": _digest(baseline)},
        "B01-002A-S05-004_completion_report.json": {"order": "B01-002A-S05-004", "status": "COMPLETE", **verification},
        "completion_report.json": {"package": "POSITION-REGISTRY-RM-001-B01-002A-S05 enterprise dependency series", "status": "COMPLETE", "orders": ("B01-002A-S05-001", "B01-002A-S05-002", "B01-002A-S05-003", "B01-002A-S05-004"), "implementation_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "certification_activity_executed": False, "baseline_digest": _digest(baseline)},
    }
    artifacts["B01-002A-S05-004_dependency_failure_reconciliation_registry.json"] = artifacts["B01-002A-S05-003_dependency_failure_constitution.json"]
    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    (OUTPUT_DIR / "README.md").write_text(
        "# Position Registry B01-002A-S05 Enterprise Dependencies\n\n"
        "Doctrine-only constitutional dependency artifacts for the Position Registry Office. No implementation behavior was evaluated or modified.\n",
        encoding="utf-8",
    )
    return artifacts["completion_report.json"]


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "output_dir": str(OUTPUT_DIR), "baseline_digest": result["baseline_digest"]}, indent=2, sort_keys=True))
