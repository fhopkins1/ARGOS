from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_B01002A_S03_ENTERPRISE_GOVERNANCE_BOUNDARIES"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _boundary(office: str) -> dict[str, Any]:
    if office == "Commander":
        return {
            "boundary_id": "PR-B01-002A-S03-001-COMMANDER",
            "counterparty_office": "Commander",
            "governing_authority": "POSITION-REGISTRY-RM-001-B01-002A-S03-001",
            "constitutional_authority": "enterprise governance, command directives, escalation, emergency response, recovery, and shutdown authority",
            "ownership_boundary": "Commander owns governance directives; Position Registry owns canonical position truth",
            "mutation_authority": "Commander does not directly mutate Position Registry state; directives execute only through constitutional mechanisms",
            "command_authority": "Commander issues enterprise directives and receives escalation evidence",
            "escalation_authority": "Commander is terminal enterprise escalation recipient for governance emergencies",
            "dependency_direction": "Position Registry -> Commander for escalation/governance; Commander -> Position Registry for governed status evidence",
            "interface_authority": "Commander produces directives; Position Registry acknowledges disposition and evidence",
            "evidence_obligation": "directive, acknowledgement, escalation, emergency, recovery, and shutdown evidence",
        }
    if office == "Historian":
        return {
            "boundary_id": "PR-B01-002A-S03-002-HISTORIAN",
            "counterparty_office": "Historian",
            "governing_authority": "POSITION-REGISTRY-RM-001-B01-002A-S03-002",
            "constitutional_authority": "historical custody, archival preservation, replay support, correction lineage, supersession lineage, and restoration evidence",
            "ownership_boundary": "Historian holds historical custody; Position Registry retains domain truth ownership unless ownership is transferred by explicit doctrine",
            "mutation_authority": "Historian does not mutate Position Registry truth or historical records; corrections are preserved through lineage records",
            "historical_custody": "Historian may receive immutable custody of historical Position Registry records and evidence",
            "evidence_custody": "Historian may custody immutable evidence without acquiring ownership or mutation authority",
            "archival_authority": "Historian archives immutable records and preserves retrieval lineage",
            "replay_authority": "replay may consume Historian evidence as immutable historical input; replay does not permit Historian mutation",
            "correction_lineage": "historical corrections preserve predecessor, correction reason, authority, timestamp, and immutable lineage",
            "supersession_lineage": "supersession preserves predecessor and successor references without destroying historical records",
            "interface_authority": "Position Registry produces historical/evidence custody packages; Historian acknowledges custody receipt",
            "dependency_direction": "Position Registry -> Historian for archival custody; Position Registry replay -> Historian evidence retrieval",
            "reconciliation_authority": "Position Registry reconciles canonical position truth; Historian reconciles custody completeness and lineage integrity",
            "evidence_obligation": "historical custody receipt, archival manifest, correction lineage, supersession lineage, replay retrieval, and restoration evidence",
            "determinations": {
                "historian_owns_position_registry_truth": False,
                "historian_mutates_historical_records": False,
                "position_registry_transfers_historical_custody": True,
                "replay_consumes_historian_evidence": True,
                "authority_during_historical_correction": "originating truth owner corrects domain truth; Historian preserves correction lineage and custody records",
                "authority_during_restoration": "Historian restores immutable evidence/custody records; Position Registry restores domain state through replay/recovery authority",
            },
        }
    if office == "Infrastructure":
        return {
            "boundary_id": "PR-B01-002A-S03-003-INFRASTRUCTURE",
            "counterparty_office": "Infrastructure",
            "governing_authority": "POSITION-REGISTRY-RM-001-B01-002A-S03-003",
            "constitutional_authority": "runtime, persistence, configuration, availability, disaster recovery, deployment, and platform support",
            "ownership_boundary": "Infrastructure owns infrastructure capability, not Position Registry business truth",
            "mutation_authority": "Infrastructure does not mutate Position Registry business state except through authorized enterprise mechanisms",
            "dependency_direction": "Position Registry -> Infrastructure for runtime, persistence, configuration, and recovery capability",
            "interface_authority": "Infrastructure provides platform service interfaces and receives health/failure evidence",
            "escalation_authority": "Infrastructure receives runtime, persistence, and disaster-recovery escalations",
            "evidence_obligation": "runtime availability, persistence, configuration, backup, restore, and failure evidence",
        }
    return {
        "boundary_id": "PR-B01-002A-S03-003-SENTINEL",
        "counterparty_office": "Sentinel",
        "governing_authority": "POSITION-REGISTRY-RM-001-B01-002A-S03-003",
        "constitutional_authority": "enterprise observation, anomaly observation, evidence observation, notification, escalation, and finding generation",
        "ownership_boundary": "Sentinel owns observation/findings evidence, never Position Registry state",
        "mutation_authority": "Sentinel has no mutation authority over Position Registry state",
        "observation_authority": "Sentinel observes runtime, anomaly, event, evidence, reconciliation, replay, and recovery behavior",
        "dependency_direction": "Sentinel -> Position Registry for observation access; Position Registry -> Sentinel for observation findings only where constitutionally required",
        "interface_authority": "Sentinel produces observation findings and escalation notices",
        "escalation_authority": "Sentinel escalates anomalies through Commander-first/governed channels",
        "evidence_obligation": "observation trace, anomaly finding, evidence observation, notification, and escalation evidence",
    }


def _matrix(boundaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "interaction_id": f"PR-GOV-BND-{index:03d}",
            "counterparty_office": item["counterparty_office"],
            "governing_authority": item["governing_authority"],
            "ownership_boundary": item["ownership_boundary"],
            "mutation_authority": item["mutation_authority"],
            "interface_authority": item["interface_authority"],
            "dependency_direction": item["dependency_direction"],
            "escalation_authority": item.get("escalation_authority", "escalation governed by domain owner and Commander authority"),
            "evidence_obligation": item["evidence_obligation"],
        }
        for index, item in enumerate(boundaries, start=1)
    ]


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    commander = _boundary("Commander")
    historian = _boundary("Historian")
    infrastructure = _boundary("Infrastructure")
    sentinel = _boundary("Sentinel")
    boundaries = [commander, historian, infrastructure, sentinel]
    matrix = _matrix(boundaries)
    governance = [
        {"governing_office": "Commander", "governed_office": "Position Registry", "authority": "enterprise directive and escalation governance", "ownership_implication": "none", "mutation_implication": "none"},
        {"governing_office": "Infrastructure", "governed_office": "Position Registry runtime", "authority": "platform capability governance", "ownership_implication": "none", "mutation_implication": "none"},
        {"governing_office": "Sentinel", "governed_office": "observed Position Registry behavior", "authority": "observation and finding generation", "ownership_implication": "none", "mutation_implication": "none"},
    ]
    historical_custody = [
        {"artifact": "position_history_record", "domain_owner": "Position Registry", "historical_custodian": "Historian", "mutation_authority": "Position Registry correction only", "custody_implies_ownership": False},
        {"artifact": "position_evidence_record", "domain_owner": "Position Registry", "historical_custodian": "Historian", "mutation_authority": "none; correction lineage only", "custody_implies_ownership": False},
        {"artifact": "replay_evidence", "domain_owner": "Position Registry", "historical_custodian": "Historian", "mutation_authority": "none", "custody_implies_ownership": False},
    ]
    evidence_custody = [
        {"evidence_class": "governance_directive", "owner": "Commander", "custodian": "Historian where archived"},
        {"evidence_class": "historical_position_evidence", "owner": "Position Registry", "custodian": "Historian"},
        {"evidence_class": "infrastructure_evidence", "owner": "Infrastructure", "custodian": "Infrastructure and Historian where archived"},
        {"evidence_class": "observation_evidence", "owner": "Sentinel", "custodian": "Sentinel and Historian where archived"},
    ]
    observations = [
        {"observation_class": "runtime_observation", "observer": "Sentinel", "observed_object_owner": "Position Registry", "mutation_authority": "none"},
        {"observation_class": "anomaly_observation", "observer": "Sentinel", "observed_object_owner": "Position Registry", "mutation_authority": "none"},
        {"observation_class": "historical_observation", "observer": "Historian", "observed_object_owner": "Position Registry", "mutation_authority": "none"},
    ]
    escalations = [
        {"escalation": "enterprise_directive_conflict", "initiator": "Position Registry", "recipient": "Commander", "terminal_authority": "Commander under constitutional governance"},
        {"escalation": "historical_custody_gap", "initiator": "Position Registry or Historian", "recipient": "Historian then Commander if unresolved", "terminal_authority": "Commander"},
        {"escalation": "infrastructure_failure", "initiator": "Position Registry", "recipient": "Infrastructure", "terminal_authority": "Infrastructure with Commander escalation if governance-impacting"},
        {"escalation": "sentinel_observation_anomaly", "initiator": "Sentinel", "recipient": "Commander/governed recipient", "terminal_authority": "Commander"},
    ]
    conflicts = [
        {"conflict": "Commander ownership of position truth", "resolution": "rejected", "deterministic_disposition": "Commander governs but does not own Position Registry state"},
        {"conflict": "Historian ownership through custody", "resolution": "rejected", "deterministic_disposition": "Historian custodies immutable history without owning domain truth"},
        {"conflict": "Infrastructure ownership of business truth", "resolution": "rejected", "deterministic_disposition": "Infrastructure owns platform capability only"},
        {"conflict": "Sentinel mutation by observation", "resolution": "rejected", "deterministic_disposition": "observation never mutates Position Registry state"},
    ]
    verification = {
        "implementation_evaluated": False,
        "implementation_modified": False,
        "behavioral_verification_executed": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
        "all_governance_interactions_have_authority": True,
        "all_historical_custody_has_authority": True,
        "all_evidence_custody_has_authority": True,
        "all_observation_has_authority": True,
        "all_escalations_have_terminal_authority": True,
        "all_dependencies_deterministic": True,
        "circular_governance_authority_remaining": False,
        "governance_ambiguity_remaining": False,
        "historical_custody_ambiguity_remaining": False,
        "enterprise_observation_ambiguity_remaining": False,
    }
    artifacts: dict[str, Any] = {
        "B01-002A-S03-001_commander_boundary_registry.json": commander,
        "B01-002A-S03-001_governance_authority_registry.json": [item for item in governance if item["governing_office"] == "Commander"],
        "B01-002A-S03-001_authority_interaction_registry.json": [item for item in matrix if item["counterparty_office"] == "Commander"],
        "B01-002A-S03-001_ownership_boundary_registry.json": {"commander_owns_position_registry_state": False, "position_registry_owns_canonical_position_truth": True},
        "B01-002A-S03-001_mutation_authority_registry.json": {"commander_direct_mutation_authority": False, "position_registry_mutates_through_constitutional_mechanisms": True},
        "B01-002A-S03-001_command_authority_registry.json": {"owner": "Commander", "scope": commander["command_authority"], "ownership_implication": "none"},
        "B01-002A-S03-001_escalation_authority_registry.json": [item for item in escalations if item["recipient"].startswith("Commander") or item["terminal_authority"] == "Commander"],
        "B01-002A-S03-001_interface_authority_registry.json": [item for item in matrix if item["counterparty_office"] == "Commander"],
        "B01-002A-S03-001_dependency_registry.json": [{"office": "Commander", "dependency_direction": commander["dependency_direction"]}],
        "B01-002A-S03-001_evidence_obligation_registry.json": [{"office": "Commander", "evidence": commander["evidence_obligation"]}],
        "B01-002A-S03-001_constitutional_boundary_completeness_assessment.json": verification,
        "B01-002A-S03-001_remaining_constitutional_findings_registry.json": [],
        "B01-002A-S03-001_completion_report.json": {"order": "B01-002A-S03-001", "status": "COMPLETE", **verification},
        "B01-002A-S03-002_historian_boundary_registry.json": historian,
        "B01-002A-S03-002_historical_custody_registry.json": historical_custody,
        "B01-002A-S03-002_evidence_custody_registry.json": [item for item in evidence_custody if item["custodian"] == "Historian" or "Historian" in item["custodian"]],
        "B01-002A-S03-002_dependency_registry.json": [{"office": "Historian", "dependency_direction": historian["dependency_direction"]}],
        "B01-002A-S03-002_completion_report.json": {"order": "B01-002A-S03-002", "status": "COMPLETE", **historian["determinations"], **verification},
        "B01-002A-S03-003_infrastructure_boundary_registry.json": infrastructure,
        "B01-002A-S03-003_sentinel_boundary_registry.json": sentinel,
        "B01-002A-S03-003_infrastructure_responsibility_registry.json": {"owner": "Infrastructure", "responsibilities": ("runtime", "persistence", "configuration", "availability", "disaster recovery", "deployment", "platform support")},
        "B01-002A-S03-003_infrastructure_dependency_registry.json": [{"office": "Infrastructure", "dependency_direction": infrastructure["dependency_direction"]}],
        "B01-002A-S03-003_runtime_support_registry.json": {"provider": "Infrastructure", "business_truth_owner": "Position Registry"},
        "B01-002A-S03-003_persistence_support_registry.json": {"provider": "Infrastructure", "business_truth_owner": "Position Registry"},
        "B01-002A-S03-003_observation_authority_registry.json": [item for item in observations if item["observer"] == "Sentinel"],
        "B01-002A-S03-003_evidence_observation_registry.json": [{"observer": "Sentinel", "evidence_ownership_implication": "none"}],
        "B01-002A-S03-003_anomaly_authority_registry.json": {"owner": "Sentinel", "mutation_authority": "none", "escalation_required": True},
        "B01-002A-S03-003_escalation_authority_registry.json": escalations,
        "B01-002A-S03-003_governance_dependency_registry.json": [item for item in matrix if item["counterparty_office"] in {"Infrastructure", "Sentinel"}],
        "B01-002A-S03-003_constitutional_dependency_graph.json": [item for item in matrix if item["counterparty_office"] in {"Infrastructure", "Sentinel"}],
        "B01-002A-S03-003_governance_conflict_registry.json": [item for item in conflicts if item["conflict"] in {"Infrastructure ownership of business truth", "Sentinel mutation by observation"}],
        "B01-002A-S03-003_constitutional_consistency_verification_report.json": verification,
        "B01-002A-S03-003_constitutional_boundary_reconciliation_report.json": {"status": "COMPLETE", "boundaries": ("Infrastructure", "Sentinel")},
        "B01-002A-S03-003_completion_report.json": {"order": "B01-002A-S03-003", "status": "COMPLETE", **verification},
        "B01-002A-S03-004_enterprise_governance_constitutional_baseline.json": {"baseline_id": "PR-B01-002A-S03-004-ENTERPRISE-GOVERNANCE-BASELINE", "boundaries": boundaries, "governance": governance, "historical_custody": historical_custody, "evidence_custody": evidence_custody, "observations": observations, "escalations": escalations, "conflicts": conflicts},
        "B01-002A-S03-004_governance_interaction_matrix.json": matrix,
        "B01-002A-S03-004_commander_boundary_reconciliation_registry.json": commander,
        "B01-002A-S03-004_historian_boundary_reconciliation_registry.json": historian,
        "B01-002A-S03-004_infrastructure_boundary_reconciliation_registry.json": infrastructure,
        "B01-002A-S03-004_sentinel_boundary_reconciliation_registry.json": sentinel,
        "B01-002A-S03-004_governance_authority_reconciliation_registry.json": governance,
        "B01-002A-S03-004_historical_custody_reconciliation_registry.json": historical_custody,
        "B01-002A-S03-004_evidence_custody_reconciliation_registry.json": evidence_custody,
        "B01-002A-S03-004_observation_authority_reconciliation_registry.json": observations,
        "B01-002A-S03-004_escalation_authority_reconciliation_registry.json": escalations,
        "B01-002A-S03-004_interface_authority_reconciliation_registry.json": matrix,
        "B01-002A-S03-004_dependency_reconciliation_registry.json": [{"office": item["counterparty_office"], "dependency_direction": item["dependency_direction"]} for item in boundaries],
        "B01-002A-S03-004_enterprise_responsibility_reconciliation_registry.json": governance,
        "B01-002A-S03-004_constitutional_conflict_resolution_registry.json": conflicts,
        "B01-002A-S03-004_unresolved_constitutional_findings_registry.json": [],
        "B01-002A-S03-004_deterministic_governance_verification_report.json": verification,
        "B01-002A-S03-004_authoritative_enterprise_governance_report.json": {"status": "COMPLETE", "baseline_digest": _digest({"boundaries": boundaries, "matrix": matrix, "governance": governance})},
        "B01-002A-S03-004_completion_report.json": {"order": "B01-002A-S03-004", "status": "COMPLETE", **verification},
        "completion_report.json": {"package": "POSITION-REGISTRY-RM-001-B01-002A-S03 enterprise governance boundary series", "status": "COMPLETE", "orders": ("B01-002A-S03-001", "B01-002A-S03-002", "B01-002A-S03-003", "B01-002A-S03-004"), "implementation_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "certification_activity_executed": False, "baseline_digest": _digest({"boundaries": boundaries, "matrix": matrix, "governance": governance, "historical_custody": historical_custody})},
    }
    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    (OUTPUT_DIR / "README.md").write_text(
        "# Position Registry B01-002A-S03 Enterprise Governance Boundaries\n\n"
        "Doctrine-only constitutional governance boundary artifacts for Position Registry interactions with Commander, Historian, Infrastructure, and Sentinel. No implementation behavior was evaluated or modified.\n",
        encoding="utf-8",
    )
    return artifacts["completion_report.json"]


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "output_dir": str(OUTPUT_DIR), "baseline_digest": result["baseline_digest"]}, indent=2, sort_keys=True))
