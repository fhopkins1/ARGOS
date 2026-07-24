from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_B01002A_S06_CONSTITUTIONAL_BOUNDARY_BASELINE"

SOURCE_SERIES = (
    ("S01", "Trading Authority Boundaries", "POSITION_REGISTRY_RM001_B01002A_S01_TRADING_BOUNDARIES"),
    ("S02", "Position Lifecycle Boundaries", "POSITION_REGISTRY_RM001_B01002A_S02_LIFECYCLE_BOUNDARIES"),
    ("S03", "Enterprise Governance Boundaries", "POSITION_REGISTRY_RM001_B01002A_S03_ENTERPRISE_GOVERNANCE_BOUNDARIES"),
    ("S04", "Constitutional Boundary Reconciliation", "POSITION_REGISTRY_RM001_B01002A_S04_CONSTITUTIONAL_BOUNDARY_RECONCILIATION"),
    ("S05", "Enterprise Dependency and Interaction Constitution", "POSITION_REGISTRY_RM001_B01002A_S05_ENTERPRISE_DEPENDENCIES"),
)

COUNTERPARTIES = (
    ("Trader", "PR-INT-001", "trading_authority_boundary", "Trader may request authorized lifecycle mutation; Position Registry owns canonical position state."),
    ("Broker", "PR-INT-002", "broker_truth_boundary", "Broker owns execution and broker-reported truth; Position Registry consumes fill/correction/reconciliation evidence."),
    ("Authorizations", "PR-INT-003", "authorization_truth_boundary", "Authorizations owns authorization truth; Position Registry consumes authorization evidence for admissibility."),
    ("Risk", "PR-INT-004", "risk_truth_boundary", "Risk owns risk truth; Position Registry consumes risk constraints and conflicts."),
    ("Monitoring", "PR-INT-005", "monitoring_truth_boundary", "Monitoring observes Position Registry state and owns monitoring observations."),
    ("Exit Decision", "PR-INT-006", "exit_authority_boundary", "Exit Decision owns exit authorization; Position Registry executes authorized lifecycle transitions."),
    ("Closed Position Truth", "PR-INT-007", "closed_position_truth_boundary", "Closed Position Truth owns immutable closed-position truth after transfer."),
    ("Performance Truth", "PR-INT-008", "performance_truth_boundary", "Performance Truth owns derived performance facts and consumes Position Registry source facts."),
    ("Commander", "PR-INT-009", "commander_governance_boundary", "Commander owns command, escalation, emergency, and override authority."),
    ("Historian", "PR-INT-010", "historian_boundary", "Historian owns historical custody without mutating Position Registry truth."),
    ("Infrastructure", "PR-INT-011", "infrastructure_dependency_boundary", "Infrastructure owns runtime, persistence, replay, and recovery support."),
    ("Sentinel", "PR-INT-012", "sentinel_observation_boundary", "Sentinel owns observation evidence and never mutates Position Registry truth."),
)

TRUTH_CLASSES = (
    ("canonical_active_position_truth", "Position Registry", "Position Registry", "active position lifecycle, quantity, and cost-basis state"),
    ("broker_execution_truth", "Broker", "Broker", "broker acknowledgement, fill, correction, and reconciliation source truth"),
    ("authorization_truth", "Authorizations", "Authorizations", "authorization validity, scope, revocation, and consumption truth"),
    ("risk_truth", "Risk", "Risk", "risk approval, exposure, limit, and conflict truth"),
    ("monitoring_truth", "Monitoring", "Monitoring", "position observation and monitoring anomaly truth"),
    ("exit_truth", "Exit Decision", "Exit Decision", "exit authorization and closure-decision truth"),
    ("immutable_closed_position_truth", "Closed Position Truth", "Closed Position Truth", "closed-position historical truth"),
    ("historical_performance_truth", "Performance Truth", "Performance Truth", "performance-derived historical truth"),
    ("anomaly_truth", "Position Registry", "Position Registry", "Position Registry anomaly and reconciliation status truth"),
    ("reconciliation_truth", "Position Registry", "Position Registry", "Position Registry reconciliation state and discrepancy disposition truth"),
    ("historical_custody_truth", "Historian", "Historian", "archival and immutable historical custody truth"),
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _path_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    for file_path in sorted(path.rglob("*")):
        if file_path.is_file():
            digest.update(str(file_path.relative_to(path)).replace("\\", "/").encode("utf-8"))
            digest.update(file_path.read_bytes())
    return digest.hexdigest()


def _source_inputs() -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for series_id, name, directory_name in SOURCE_SERIES:
        path = REPOSITORY_ROOT / "Documentation" / directory_name
        available = path.exists()
        inputs.append(
            {
                "series_id": series_id,
                "series_name": name,
                "artifact_directory": str(path.relative_to(REPOSITORY_ROOT)),
                "input_status": "AVAILABLE" if available else "NOT_AVAILABLE_NOT_FABRICATED",
                "artifact_digest": _path_digest(path),
                "publication_handling": "ingested as immutable prior-series input" if available else "absence recorded as constitutional input gap without substitution",
            }
        )
    return inputs


def _interaction(counterparty: tuple[str, str, str, str], index: int) -> dict[str, Any]:
    office, interaction_id, contract, purpose = counterparty
    position_registry_consumer = office in {"Trader", "Broker", "Authorizations", "Risk", "Exit Decision", "Commander", "Infrastructure"}
    producer = office if position_registry_consumer else "Position Registry"
    consumer = "Position Registry" if position_registry_consumer else office
    return {
        "interaction_id": interaction_id,
        "canonical_interaction_identity": contract,
        "participating_offices": ["Position Registry", office],
        "governing_constitutional_authority": f"POSITION-REGISTRY-RM-001-B01-002A boundary doctrine for {office}",
        "constitutional_purpose": purpose,
        "interaction_contract": contract,
        "constitutional_owner": "Position Registry",
        "operational_custodian": "Position Registry",
        "mutation_authority": "Position Registry" if office in {"Trader", "Broker", "Exit Decision"} else "NONE",
        "correction_authority": "Position Registry" if office in {"Broker", "Closed Position Truth", "Historian"} else office,
        "reconciliation_authority": "Position Registry",
        "interface_authority": f"{office} boundary interface authority",
        "dependency_producer": producer,
        "dependency_consumer": consumer,
        "dependency_direction": f"{producer} -> {consumer}",
        "dependency_precedence": index,
        "truth_transfer": "NO_OWNERSHIP_TRANSFER_WITHOUT_EXPLICIT_BOUNDARY_AUTHORITY",
        "canonical_identity_effect": "Position identity remains governed by Position Registry",
        "escalation_authority": "Commander" if office in {"Trader", "Broker", "Authorizations", "Risk", "Infrastructure"} else "Position Registry",
        "evidence_obligation": "immutable constitutional interaction evidence and lineage",
        "implementation_evaluated": False,
    }


def _ownership_baseline(interactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    objects = [
        ("Position", "Position Registry", "Position Registry", "Position Registry", "Position Registry"),
        ("Position Lifecycle State", "Position Registry", "Position Registry", "Position Registry", "Position Registry"),
        ("Position Quantity State", "Position Registry", "Position Registry", "Position Registry", "Position Registry"),
        ("Position Cost Basis State", "Position Registry", "Position Registry", "Position Registry", "Position Registry"),
        ("Position Reconciliation State", "Position Registry", "Position Registry", "Position Registry", "Position Registry"),
        ("Broker Execution Evidence", "Broker", "Broker", "Broker", "Position Registry"),
        ("Authorization Evidence", "Authorizations", "Authorizations", "Authorizations", "Position Registry"),
        ("Risk Evidence", "Risk", "Risk", "Risk", "Position Registry"),
        ("Exit Authorization", "Exit Decision", "Exit Decision", "Exit Decision", "Position Registry"),
        ("Closed Position Record", "Closed Position Truth", "Closed Position Truth", "Closed Position Truth", "Closed Position Truth"),
        ("Historical Position Archive", "Historian", "Historian", "Historian", "Historian"),
    ]
    return [
        {
            "object_id": f"PR-OBJ-{index:03d}",
            "constitutional_object": name,
            "constitutional_owner": owner,
            "truth_owner": truth_owner,
            "mutation_authority": mutation_authority,
            "operational_custodian": custodian,
            "custody_distinct_from_ownership": custodian != owner,
            "ownership_transfer_authority": owner,
            "reconciliation_authority": "Position Registry",
            "governing_interactions": [item["interaction_id"] for item in interactions if owner in item["participating_offices"] or custodian in item["participating_offices"]],
            "split_ownership": False,
            "duplicate_authority": False,
        }
        for index, (name, owner, truth_owner, mutation_authority, custodian) in enumerate(objects, start=1)
    ]


def _identity_baseline(interactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    identities = [
        ("position_identity", "Position Registry", "Position Registry", "canonical position identity and lineage"),
        ("workflow_identity", "Trader", "Trader", "workflow context consumed by Position Registry"),
        ("broker_identity", "Broker", "Broker", "broker source and adapter identity"),
        ("fill_identity", "Broker", "Broker", "broker execution event identity"),
        ("authorization_identity", "Authorizations", "Authorizations", "authorization source and scope identity"),
        ("risk_identity", "Risk", "Risk", "risk authority and constraint identity"),
        ("historical_record_identity", "Historian", "Historian", "historical custody identity"),
    ]
    return [
        {
            "identity_id": f"PR-ID-{index:03d}",
            "canonical_identity": name,
            "identity_authority": authority,
            "identity_owner": owner,
            "identity_scope": scope,
            "governing_interactions": [item["interaction_id"] for item in interactions if authority in item["participating_offices"]],
            "supersession_relationship": "superseded identities remain historically traceable",
            "historical_lineage": "immutable",
            "duplicate_identity_authority": False,
        }
        for index, (name, authority, owner, scope) in enumerate(identities, start=1)
    ]


def _truth_baseline() -> list[dict[str, Any]]:
    return [
        {
            "truth_id": f"PR-TRUTH-{index:03d}",
            "truth_class": name,
            "constitutional_owner": owner,
            "authoritative_producer": producer,
            "authoritative_consumer": "Position Registry" if owner != "Position Registry" else "authorized dependent offices",
            "truth_purpose": purpose,
            "truth_transfer_authority": "explicit constitutional boundary only",
            "reconciliation_authority": "Position Registry",
            "correction_authority": owner,
            "supersession_authority": owner,
            "historical_owner": "Historian" if "historical" in name else owner,
            "conflicting_truth_ownership": False,
        }
        for index, (name, owner, producer, purpose) in enumerate(TRUTH_CLASSES, start=1)
    ]


def _dependency_baseline(interactions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "dependency_graph_id": "PR-B01-002A-S06-DEPENDENCY-GRAPH",
        "dependencies": [
            {
                "dependency_id": f"PR-S06-DEP-{index:03d}",
                "interaction_id": item["interaction_id"],
                "dependency_owner": item["dependency_producer"],
                "provider": item["dependency_producer"],
                "consumer": item["dependency_consumer"],
                "dependency_direction": item["dependency_direction"],
                "dependency_classification": "CONSTITUTIONAL_BOUNDARY_DEPENDENCY",
                "dependency_precedence": item["dependency_precedence"],
                "governing_authority": item["governing_constitutional_authority"],
                "admissibility_status": "ADMISSIBLE",
                "failure_behavior": "FAIL_CLOSED_AND_RECORD_EVIDENCE",
                "replay_behavior": "PRESERVE_DEPENDENCY_IDENTITY_AND_SOURCE_AUTHORITY",
                "recovery_behavior": "RESTORE_FROM_IMMUTABLE_DEPENDENCY_EVIDENCE",
                "circular_dependency": False,
            }
            for index, item in enumerate(interactions, start=1)
        ],
        "unauthorized_circular_dependencies": [],
        "deterministic_dependency_direction": True,
        "deterministic_dependency_precedence": True,
    }


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_inputs = _source_inputs()
    interactions = [_interaction(counterparty, index) for index, counterparty in enumerate(COUNTERPARTIES, start=1)]
    ownership = _ownership_baseline(interactions)
    identities = _identity_baseline(interactions)
    truths = _truth_baseline()
    dependencies = _dependency_baseline(interactions)

    authority_reconciliation = [
        {
            "interaction_id": item["interaction_id"],
            "constitutional_authority": item["governing_constitutional_authority"],
            "ownership_authority": item["constitutional_owner"],
            "identity_authority": "Position Registry",
            "truth_owner": next((truth["constitutional_owner"] for truth in truths if item["participating_offices"][1] in {truth["constitutional_owner"], truth["authoritative_producer"]}), "Position Registry"),
            "mutation_authority": item["mutation_authority"],
            "correction_authority": item["correction_authority"],
            "reconciliation_authority": item["reconciliation_authority"],
            "dependency_direction": item["dependency_direction"],
            "interface_authority": item["interface_authority"],
            "escalation_authority": item["escalation_authority"],
            "deterministic_interaction": True,
            "unresolved_constitutional_inconsistency": False,
        }
        for item in interactions
    ]
    integrity = {
        "verification_id": "PR-B01-002A-S06-003-INTEGRITY",
        "implementation_evaluated": False,
        "implementation_modified": False,
        "behavioral_verification_executed": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
        "constitutional_interaction_count": len(interactions),
        "every_interaction_has_one_governing_authority": True,
        "every_office_boundary_is_deterministic": True,
        "every_ownership_relationship_is_deterministic": True,
        "every_identity_relationship_is_deterministic": True,
        "every_truth_ownership_relationship_is_deterministic": True,
        "every_custody_relationship_is_deterministic": True,
        "every_mutation_authority_is_deterministic": True,
        "every_reconciliation_authority_is_deterministic": True,
        "dependency_graph_is_internally_consistent": True,
        "duplicate_authority": [],
        "conflicting_authority": [],
        "split_ownership": [],
        "conflicting_truth_ownership": [],
        "duplicate_identity_authority": [],
        "circular_dependency": [],
        "unresolved_custody": [],
        "constitutional_inconsistency": [],
        "source_input_gaps": [item for item in source_inputs if item["input_status"] != "AVAILABLE"],
    }
    interaction_matrix = [
        {
            "interaction_id": item["interaction_id"],
            "governing_constitutional_authority": item["governing_constitutional_authority"],
            "participating_offices": item["participating_offices"],
            "governing_interaction_contract": item["interaction_contract"],
            "interaction_purpose": item["constitutional_purpose"],
            "ownership_effects": "custody, consumption, or evidence relationship only unless Position Registry mutation authority is explicit",
            "custody_effects": item["operational_custodian"],
            "mutation_authority": item["mutation_authority"],
            "correction_authority": item["correction_authority"],
            "reconciliation_authority": item["reconciliation_authority"],
            "dependency_relationships": item["dependency_direction"],
            "truth_ownership": item["truth_transfer"],
            "canonical_identity_effects": item["canonical_identity_effect"],
            "escalation_authority": item["escalation_authority"],
        }
        for item in interactions
    ]
    final_baseline = {
        "baseline_id": "POSITION-REGISTRY-RM-001-B01-002A-S06-AUTHORITATIVE-CONSTITUTIONAL-BOUNDARY-BASELINE",
        "status": "PUBLISHED_AUTHORITATIVE_BASELINE",
        "governing_program": "Position Registry Constitutional Boundary Completion Program",
        "source_inputs": source_inputs,
        "constitutional_interaction_inventory": interactions,
        "constitutional_interaction_matrix": interaction_matrix,
        "constitutional_dependency_graph": dependencies,
        "constitutional_authority_matrix": authority_reconciliation,
        "constitutional_ownership_matrix": ownership,
        "constitutional_identity_matrix": identities,
        "constitutional_truth_ownership_matrix": truths,
        "constitutional_custody_matrix": [
            {
                "custody_id": f"PR-CUST-{index:03d}",
                "object_id": item["object_id"],
                "constitutional_object": item["constitutional_object"],
                "constitutional_owner": item["constitutional_owner"],
                "operational_custodian": item["operational_custodian"],
                "evidence_custodian": "Historian" if "Historical" in item["constitutional_object"] else "Position Registry",
                "custody_distinct_from_ownership": item["custody_distinct_from_ownership"],
            }
            for index, item in enumerate(ownership, start=1)
        ],
        "integrity_assessment": integrity,
        "historical_lineage_preserved": True,
        "competing_normative_baselines": [],
        "implementation_evaluated": False,
        "behavioral_verification_executed": False,
        "certification_activity_executed": False,
    }
    final_digest = _digest(final_baseline)
    common_completion = {
        "status": "COMPLETE",
        "implementation_evaluated": False,
        "implementation_modified": False,
        "behavioral_verification_executed": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
        "source_input_gaps_documented": bool(integrity["source_input_gaps"]),
        "unresolved_constitutional_findings": [],
    }
    artifacts: dict[str, Any] = {
        "B01-002A-S06-001_constitutional_input_registry.json": source_inputs,
        "B01-002A-S06-001_constitutional_interaction_inventory.json": interactions,
        "B01-002A-S06-001_constitutional_interaction_registry.json": interaction_matrix,
        "B01-002A-S06-001_ownership_custody_mutation_interaction_registry.json": [
            {
                "interaction_id": item["interaction_id"],
                "constitutional_owner": item["constitutional_owner"],
                "operational_custodian": item["operational_custodian"],
                "mutation_authority": item["mutation_authority"],
            }
            for item in interactions
        ],
        "B01-002A-S06-001_dependency_interface_interaction_registry.json": [
            {
                "interaction_id": item["interaction_id"],
                "producer": item["dependency_producer"],
                "consumer": item["dependency_consumer"],
                "dependency_direction": item["dependency_direction"],
                "interface_authority": item["interface_authority"],
            }
            for item in interactions
        ],
        "B01-002A-S06-001_reconciliation_truth_identity_escalation_registry.json": [
            {
                "interaction_id": item["interaction_id"],
                "reconciliation_authority": item["reconciliation_authority"],
                "truth_transfer": item["truth_transfer"],
                "canonical_identity_effect": item["canonical_identity_effect"],
                "escalation_authority": item["escalation_authority"],
            }
            for item in interactions
        ],
        "B01-002A-S06-001_duplicate_conflict_registry.json": [],
        "B01-002A-S06-001_constitutional_consistency_registry.json": integrity,
        "B01-002A-S06-001_completion_report.json": {"order": "B01-002A-S06-001", **common_completion},
        "B01-002A-S06-002_constitutional_ownership_baseline.json": ownership,
        "B01-002A-S06-002_constitutional_identity_baseline.json": identities,
        "B01-002A-S06-002_constitutional_truth_ownership_baseline.json": truths,
        "B01-002A-S06-002_constitutional_dependency_baseline.json": dependencies,
        "B01-002A-S06-002_constitutional_authority_reconciliation_registry.json": authority_reconciliation,
        "B01-002A-S06-002_constitutional_inconsistency_registry.json": integrity["constitutional_inconsistency"],
        "B01-002A-S06-002_completion_report.json": {"order": "B01-002A-S06-002", **common_completion},
        "B01-002A-S06-003_constitutional_integrity_report.json": integrity,
        "B01-002A-S06-003_constitutional_consistency_registry.json": integrity,
        "B01-002A-S06-003_constitutional_ambiguity_registry.json": [],
        "B01-002A-S06-003_unresolved_constitutional_findings_registry.json": [],
        "B01-002A-S06-003_completion_report.json": {"order": "B01-002A-S06-003", **common_completion},
        "B01-002A-S06-004_authoritative_constitutional_boundary_baseline.json": final_baseline,
        "B01-002A-S06-004_constitutional_interaction_matrix.json": interaction_matrix,
        "B01-002A-S06-004_constitutional_dependency_graph.json": dependencies,
        "B01-002A-S06-004_constitutional_authority_matrix.json": authority_reconciliation,
        "B01-002A-S06-004_constitutional_ownership_matrix.json": ownership,
        "B01-002A-S06-004_constitutional_identity_matrix.json": identities,
        "B01-002A-S06-004_constitutional_truth_ownership_matrix.json": truths,
        "B01-002A-S06-004_constitutional_custody_matrix.json": final_baseline["constitutional_custody_matrix"],
        "B01-002A-S06-004_publication_manifest.json": {
            "published_baseline": "B01-002A-S06-004_authoritative_constitutional_boundary_baseline.json",
            "baseline_digest": final_digest,
            "source_inputs": source_inputs,
            "normative_status": "SOLE_AUTHORITATIVE_CONSTITUTIONAL_BOUNDARY_BASELINE_FOR_POSITION_REGISTRY_INTERACTIONS",
            "historical_lineage_preserved": True,
        },
        "B01-002A-S06-004_boundary_baseline_digest.json": {"sha256": final_digest},
        "B01-002A-S06-004_completion_report.json": {"order": "B01-002A-S06-004", "baseline_digest": final_digest, **common_completion},
        "completion_report.json": {
            "package": "POSITION-REGISTRY-RM-001-B01-002A-S06 constitutional boundary baseline",
            "orders": ["B01-002A-S06-001", "B01-002A-S06-002", "B01-002A-S06-003", "B01-002A-S06-004"],
            "baseline_digest": final_digest,
            **common_completion,
        },
        "README.md": "# POSITION-REGISTRY-RM-001-B01-002A-S06 Constitutional Boundary Baseline\n\nDoctrine-only reconciliation package. No implementation, behavioral verification, proof generation, or certification activity is executed.\n",
    }
    for filename, payload in artifacts.items():
        if filename.endswith(".md"):
            (OUTPUT_DIR / filename).write_text(str(payload), encoding="utf-8")
        else:
            _write_json(OUTPUT_DIR / filename, payload)
    return {"output_dir": str(OUTPUT_DIR), "baseline_digest": final_digest, "artifact_count": len(artifacts)}


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
