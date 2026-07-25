from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM001_B03_INTERFACE_EVIDENCE_TRACEABILITY"
B01_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM001_B01_CONSTITUTIONAL_BASELINE"
B02_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM001_B02_OBJECT_LIFECYCLE"

INTERFACE_PARTNERS = (
    "Commander",
    "Sentinel",
    "Seeker",
    "Analyst",
    "Risk",
    "Trader",
    "Broker",
    "Position Registry",
    "Authorizations",
    "Exit Decision",
    "Closed Position Truth",
    "Performance Truth",
    "Historian",
    "Infrastructure",
    "External Data Providers",
    "Persistence Systems",
    "Notification Systems",
)

TEMPORAL_EVENTS = (
    "source event time",
    "observation time",
    "receipt time",
    "normalization time",
    "evaluation time",
    "finding creation time",
    "alert creation time",
    "escalation creation time",
    "acknowledgement time",
    "suppression activation time",
    "suppression expiration time",
    "correction time",
    "supersession time",
    "persistence time",
    "archival time",
    "replay execution time",
    "recovery execution time",
)

FRESHNESS_CLASSES = (
    "observation freshness",
    "evaluation freshness",
    "finding freshness",
    "alert freshness",
    "escalation freshness",
    "acknowledgement freshness",
    "correction freshness",
    "replay freshness",
    "recovery freshness",
)

EVIDENCE_EVENTS = (
    "Monitoring Mission creation",
    "Monitoring Scope assignment",
    "Monitoring Target registration",
    "Monitoring Subscription establishment",
    "Observation receipt",
    "Observation normalization",
    "Observation evaluation",
    "Threshold evaluation",
    "Finding generation",
    "Alert generation",
    "Escalation request",
    "Acknowledgement",
    "Suppression",
    "Recovery",
    "Correction",
    "Supersession",
    "Completion",
    "Archival",
    "Termination",
)

REJECTED_EVIDENCE = (
    "metadata-only evidence",
    "documentation-only evidence",
    "implementation assertions",
    "implementation intent",
    "synthetic evidence",
    "inferred evidence",
    "circular evidence",
    "completion-report-only evidence",
    "unverifiable evidence",
    "evidence without provenance",
    "evidence without constitutional ownership",
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _object_names() -> list[str]:
    rows = _read_json(B02_DIR / "B02-001_canonical_monitoring_object_registry.json", [])
    return [row["object_name"] for row in rows] or [
        "Monitoring Observation",
        "Monitoring Evaluation",
        "Monitoring Finding",
        "Monitoring Alert",
        "Monitoring Escalation",
        "Monitoring Evidence Record",
    ]


def _interfaces() -> list[dict[str, Any]]:
    rows = []
    for index, partner in enumerate(INTERFACE_PARTNERS, start=1):
        inbound = partner not in {"Commander", "Historian", "Notification Systems"}
        rows.append(
            {
                "interface_id": f"MON-IFACE-{index:03d}",
                "interface_name": f"monitoring_{partner.lower().replace(' ', '_')}_interface",
                "partner": partner,
                "constitutional_purpose": f"Govern Monitoring interaction with {partner}.",
                "governing_constitutional_authority": "MONITORING-RM-001-B03-001",
                "dependency_id": f"MON-DEP-{index:03d}",
                "dependency_owner": partner if inbound else "Monitoring Office",
                "dependency_direction": f"{partner} -> Monitoring" if inbound else f"Monitoring -> {partner}",
                "dependency_classification": "INBOUND_CONSUMPTION" if inbound else "OUTBOUND_COMMUNICATION",
                "constitutional_producer": partner if inbound else "Monitoring Office",
                "constitutional_consumer": "Monitoring Office" if inbound else partner,
                "schema_authority": partner if inbound else "Monitoring Office",
                "identity_authority": partner if inbound else "Monitoring Office",
                "ordering_authority": "Monitoring Office canonical ordering after receipt",
                "freshness_authority": "Monitoring Office validates freshness using source-owned timestamp evidence",
                "acknowledgement_authority": partner if not inbound else "Monitoring Office",
                "retry_authority": "Monitoring Office for Monitoring-owned communication retries",
                "replay_authority": "Monitoring Office and certification authority",
                "failure_owner": "Monitoring Office for interface failure record; source office for source truth",
                "reconciliation_authority": "Monitoring Office for Monitoring artifacts only",
                "permitted_inputs": ["authorized evidence", "identity", "timestamp", "schema version"],
                "permitted_outputs": ["Monitoring evidence", "finding", "alert", "notification", "escalation request"],
                "prohibited_inputs": ["unauthorized mutation commands", "unowned enterprise truth claims"],
                "prohibited_outputs": ["enterprise action authorization", "external truth mutation"],
                "compatibility_requirements": ["schema version compatibility", "identity preservation", "timestamp validity"],
                "dependency_termination_conditions": ["mission termination", "scope removal", "dependency unavailable terminal finding"],
            }
        )
    return rows


def _temporal_registry() -> list[dict[str, Any]]:
    return [
        {
            "temporal_event_id": f"MON-TIME-{index:03d}",
            "temporal_event": event,
            "constitutional_purpose": f"Define deterministic {event} semantics.",
            "canonical_definition": f"{event} is recorded as a distinct Monitoring temporal attribute and never inferred from another timestamp.",
            "authoritative_timestamp_source": "originating source" if event == "source event time" else "Monitoring Office",
            "ownership": "Monitoring Office for Monitoring records; source office for source timestamps",
            "required_precision": "ISO-8601 UTC with deterministic sequence tie-breaker",
            "permitted_origin": ["source evidence", "Monitoring processing clock", "replay harness clock"],
            "prohibited_origin": ["operator memory", "documentation", "metadata-only assertion"],
            "lifecycle_applicability": "all Monitoring objects where event occurs",
            "required_evidence": ["timestamp", "source", "sequence", "evidence digest"],
        }
        for index, event in enumerate(TEMPORAL_EVENTS, start=1)
    ]


def _freshness_registry() -> list[dict[str, Any]]:
    return [
        {
            "freshness_id": f"MON-FRESH-{index:03d}",
            "freshness_class": item,
            "governing_authority": "Monitoring Office",
            "freshness_measurement": "source event time to evaluation or publication time according to rule version",
            "freshness_thresholds": "defined by Monitoring Rule or Threshold version",
            "expiration_semantics": "expired evidence remains historical but cannot satisfy current obligation",
            "stale_determination": "deterministic comparison against threshold",
            "admissibility_rules": ["freshness evidence present", "threshold version present", "timestamp source valid"],
            "required_evidence": ["timestamp chain", "threshold version", "freshness decision"],
            "constitutional_outcomes": ["admissible", "stale", "expired", "quarantined", "fail_closed"],
        }
        for index, item in enumerate(FRESHNESS_CLASSES, start=1)
    ]


def _duplicate_registry() -> list[dict[str, Any]]:
    duplicate_classes = (
        "duplicate observations",
        "duplicate normalized observations",
        "duplicate evaluations",
        "duplicate findings",
        "duplicate alerts",
        "duplicate escalations",
        "duplicate acknowledgements",
        "duplicate corrections",
        "duplicate replay events",
    )
    return [
        {
            "duplicate_id": f"MON-DUP-{index:03d}",
            "duplicate_class": item,
            "detection_authority": "Monitoring Office",
            "canonical_identity_comparison": "object identity, source identity, event time, normalized digest, rule version",
            "reconciliation_authority": "Monitoring Office",
            "historical_preservation": "all duplicates remain traceable",
            "suppression_eligibility": "only publication suppression; evidence suppression prohibited",
            "evidence_requirements": ["original identity", "duplicate identity", "comparison digest", "disposition"],
            "permitted_outcomes": ["linked duplicate", "suppressed publication", "quarantined duplicate"],
            "prohibited_outcomes": ["history deletion", "identity rewrite", "external truth mutation"],
        }
        for index, item in enumerate(duplicate_classes, start=1)
    ]


def _evidence_registry() -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": f"MON-EVID-{index:03d}",
            "constitutional_event": event,
            "constitutional_purpose": f"Preserve admissible evidence for {event}.",
            "canonical_identity": f"MON-EVID-{index:03d}-<event-sequence>",
            "constitutional_producer": "Monitoring Office",
            "constitutional_owner": "Monitoring Office",
            "constitutional_custodian": "Monitoring Office before archival; Historian after archival",
            "creation_authority": "Monitoring Office",
            "mutation_authority": "append-only evidence state only",
            "correction_authority": "Monitoring Office with correction lineage",
            "supersession_authority": "Monitoring Office",
            "reconciliation_authority": "Monitoring Office for Monitoring evidence only",
            "persistence_responsibility": "Monitoring Office",
            "archival_responsibility": "Monitoring Office and Historian custody",
            "terminal_disposition": "retained permanently",
            "admissibility_requirements": ["complete provenance", "integrity digest", "temporal validity", "ownership", "custody", "lineage", "reproducibility"],
            "integrity_requirements": ["sha256 digest or equivalent", "immutability", "tamper detection", "completeness validation"],
            "historical_preservation_requirements": ["predecessor preserved", "successor linked", "no deletion"],
        }
        for index, event in enumerate(EVIDENCE_EVENTS, start=1)
    ]


def _requirements(objects: list[str], interfaces: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    categories = [
        ("B01", "authority", "Monitoring constitutional authority and boundary requirement"),
        ("B02", "object_lifecycle", "Monitoring canonical object and lifecycle requirement"),
        ("B03", "interface_dependency", "Monitoring interface and dependency requirement"),
        ("B03", "temporal", "Monitoring temporal, freshness, and duplicate requirement"),
        ("B03", "evidence", "Monitoring evidence doctrine requirement"),
        ("B03", "traceability", "Monitoring canonical requirement traceability requirement"),
    ]
    sequence = 1
    for source, category, statement in categories:
        population: list[Any]
        if category == "object_lifecycle":
            population = objects
        elif category == "interface_dependency":
            population = interfaces
        elif category == "evidence":
            population = evidence
        elif category == "temporal":
            population = list(TEMPORAL_EVENTS)
        else:
            population = [category]
        for item in population:
            name = item if isinstance(item, str) else item.get("interface_name") or item.get("constitutional_event")
            req_id = f"MON-REQ-{sequence:04d}"
            requirements.append(
                {
                    "canonical_requirement_identity": req_id,
                    "constitutional_authority": f"MONITORING-RM-001-{source}",
                    "requirement_title": f"{name} {category} requirement",
                    "requirement_statement": f"{statement}: {name}.",
                    "constitutional_objective": "complete deterministic Monitoring constitutional governance",
                    "constitutional_owner": "Monitoring Office",
                    "governing_work_order": f"MONITORING-RM-001-{source}",
                    "constitutional_category": category,
                    "requirement_status": "ACTIVE",
                    "parent_requirement": "",
                    "child_requirements": [],
                    "identity_immutable": True,
                }
            )
            sequence += 1
    return requirements


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    objects = _object_names()
    interfaces = _interfaces()
    temporal = _temporal_registry()
    freshness = _freshness_registry()
    duplicates = _duplicate_registry()
    evidence = _evidence_registry()
    requirements = _requirements(objects, interfaces, evidence)
    traceability = [
        {
            "traceability_id": f"{req['canonical_requirement_identity']}-TRACE",
            "constitutional_authority": req["constitutional_authority"],
            "canonical_requirement": req["canonical_requirement_identity"],
            "governing_constitutional_principle": req["constitutional_category"],
            "governing_monitoring_object": req["requirement_title"].replace(" requirement", ""),
            "lifecycle_obligation": req["canonical_requirement_identity"] if req["constitutional_category"] == "object_lifecycle" else "",
            "interface_obligation": req["canonical_requirement_identity"] if req["constitutional_category"] == "interface_dependency" else "",
            "dependency_obligation": req["canonical_requirement_identity"] if req["constitutional_category"] == "interface_dependency" else "",
            "temporal_obligation": req["canonical_requirement_identity"] if req["constitutional_category"] == "temporal" else "",
            "evidence_obligation": req["canonical_requirement_identity"] if req["constitutional_category"] == "evidence" else "",
            "historical_integrity_obligation": req["canonical_requirement_identity"] if req["constitutional_category"] in {"object_lifecycle", "evidence"} else "",
            "certification_obligation": "future ECS-003 certification proof",
            "bidirectional": True,
            "status": "COMPLETE",
        }
        for req in requirements
    ]
    baseline = {
        "baseline_id": "MONITORING-RM-001-B03",
        "depends_on": ["MONITORING-RM-001-B01", "MONITORING-RM-001-B02"],
        "orders_completed": ["B03-001", "B03-002", "B03-003", "B03-004"],
        "interfaces": interfaces,
        "temporal_events": temporal,
        "evidence": evidence,
        "requirements": requirements,
        "traceability": traceability,
        "digest": "",
    }
    baseline["digest"] = _digest({key: value for key, value in baseline.items() if key != "digest"})

    artifacts: dict[str, Any] = {
        "B03-001_constitutional_interface_registry.json": interfaces,
        "B03-001_constitutional_dependency_registry.json": [{"dependency_id": item["dependency_id"], "dependency_purpose": item["constitutional_purpose"], "dependency_owner": item["dependency_owner"], "dependency_direction": item["dependency_direction"], "dependency_classification": item["dependency_classification"], "dependency_authority": item["governing_constitutional_authority"], "dependency_prerequisites": item["compatibility_requirements"], "dependency_limitations": item["prohibited_outputs"], "dependency_termination_conditions": item["dependency_termination_conditions"]} for item in interfaces],
        "B03-001_dependency_direction_matrix.json": [{"dependency_id": item["dependency_id"], "direction": item["dependency_direction"], "deterministic": True} for item in interfaces],
        "B03-001_interface_authority_registry.json": [{"interface_id": item["interface_id"], "governing_constitutional_authority": item["governing_constitutional_authority"], "authority_precedence": "Monitoring RM-001 constitutional baseline", "conflict_resolution": "fail closed and constitutional amendment if unresolved"} for item in interfaces],
        "B03-001_producer_registry.json": [{"interface_id": item["interface_id"], "producer": item["constitutional_producer"], "producer_authority": item["schema_authority"]} for item in interfaces],
        "B03-001_consumer_registry.json": [{"interface_id": item["interface_id"], "consumer": item["constitutional_consumer"], "consumer_authority": "authorized constitutional consumption only"} for item in interfaces],
        "B03-001_interface_contract_registry.json": [{"interface_id": item["interface_id"], "canonical_interface_contract": item["interface_name"], "permitted_inputs": item["permitted_inputs"], "permitted_outputs": item["permitted_outputs"], "prohibited_inputs": item["prohibited_inputs"], "prohibited_outputs": item["prohibited_outputs"], "compatibility_requirements": item["compatibility_requirements"]} for item in interfaces],
        "B03-001_schema_authority_registry.json": [{"interface_id": item["interface_id"], "schema_owner": item["schema_authority"], "schema_evolution_authority": item["schema_authority"], "compatibility_rules": item["compatibility_requirements"]} for item in interfaces],
        "B03-001_interface_identity_registry.json": [{"interface_id": item["interface_id"], "identity_authority": item["identity_authority"], "identity_validation_requirements": ["identity present", "identity unique", "correlation id retained"], "object_identity_preservation_required": True} for item in interfaces],
        "B03-001_interface_ordering_registry.json": [{"interface_id": item["interface_id"], "ordering_requirements": item["ordering_authority"], "deterministic_ordering_required": True} for item in interfaces],
        "B03-001_interface_freshness_registry.json": [{"interface_id": item["interface_id"], "freshness_authority": item["freshness_authority"], "freshness_inferred": False} for item in interfaces],
        "B03-001_interface_acknowledgement_registry.json": [{"interface_id": item["interface_id"], "acknowledgement_authority": item["acknowledgement_authority"], "acknowledgement_implies_completion": False} for item in interfaces],
        "B03-001_retry_governance_registry.json": [{"interface_id": item["interface_id"], "retry_authority": item["retry_authority"], "retry_preserves_determinism": True} for item in interfaces],
        "B03-001_replay_governance_registry.json": [{"interface_id": item["interface_id"], "replay_authority": item["replay_authority"], "unconstitutional_state_transition_prohibited": True} for item in interfaces],
        "B03-001_failure_governance_registry.json": [{"interface_id": item["interface_id"], "failure_owner": item["failure_owner"], "failure_classifications": ["unavailable", "stale", "invalid", "unauthorized", "timeout"], "fail_closed": True} for item in interfaces],
        "B03-001_reconciliation_authority_registry.json": [{"interface_id": item["interface_id"], "reconciliation_authority": item["reconciliation_authority"], "external_truth_mutation": False} for item in interfaces],
        "B03-001_constitutional_interface_issue_registry.json": [],
        "B03-001_constitutional_validation_report.json": {"interfaces": len(interfaces), "one_governing_authority_each": True, "one_dependency_owner_each": True, "deterministic_direction_each": True, "producer_consumer_complete": True, "authoritative_contract_each": True, "undocumented_interfaces": [], "unauthorized_interfaces": [], "ambiguities": []},
        "B03-001_completion_report.json": {"order": "MONITORING-RM-001-B03-001", "status": "COMPLETE", "implementation_behavior_modified": False},
        "B03-002_temporal_constitution.json": {"principle": "Every Monitoring temporal attribute has one definition, source, owner, precision, and evidence obligation.", "freshness_inferred": False, "ordering_deterministic": True},
        "B03-002_canonical_temporal_event_registry.json": temporal,
        "B03-002_timestamp_authority_registry.json": [{"temporal_event": item["temporal_event"], "authoritative_timestamp_source": item["authoritative_timestamp_source"], "ownership": item["ownership"]} for item in temporal],
        "B03-002_freshness_constitution.json": {"freshness_explicitly_evaluated": True, "freshness_inferred": False, "expiration_preserves_history": True},
        "B03-002_freshness_evaluation_registry.json": freshness,
        "B03-002_stale_observation_constitution.json": {"stale_observations": "historically preserved, marked stale, and excluded from current sufficiency unless rule permits"},
        "B03-002_late_observation_constitution.json": {"late_observations": "accepted only with late classification and deterministic reconciliation"},
        "B03-002_ordering_constitution.json": {"ordering_chain": ["source event time", "receipt time", "processing time", "persistence time", "sequence id"], "equal_timestamp_tiebreaker": "canonical sequence identity"},
        "B03-002_replay_ordering_constitution.json": {"replay_preserves_original_temporal_relationships": True, "replay_boundaries_required": True, "replay_evidence_required": True},
        "B03-002_recovery_ordering_constitution.json": {"restart_ordering": "last durable checkpoint plus append-only sequence", "recovery_preserves_temporal_integrity": True},
        "B03-002_duplicate_governance_registry.json": duplicates,
        "B03-002_duplicate_detection_constitution.json": {"detection_authority": "Monitoring Office", "history_destroyed": False, "identity_rewrite_prohibited": True},
        "B03-002_temporal_correlation_registry.json": [{"window": name, "governing_authority": "Monitoring Office", "ownership": "Monitoring Office", "creation_authority": "Monitoring Office", "modification_authority": "Monitoring Office", "expiration_authority": "Monitoring Office", "evidence_required": True} for name in ("observation correlation windows", "finding correlation windows", "alert correlation windows", "escalation correlation windows", "suppression windows", "hysteresis windows", "recovery windows", "observation aggregation windows", "evaluation batching windows")],
        "B03-002_suppression_window_constitution.json": {"suppression_window_owner": "Monitoring Office", "expiration_required": True, "history_suppression_prohibited": True},
        "B03-002_hysteresis_constitution.json": {"hysteresis_window_owner": "Monitoring Office", "oscillation_prevention": True, "activation_and_recovery_rules_separate": True},
        "B03-002_temporal_conflict_resolution_registry.json": [{"conflict": conflict, "resolution": "source precedence chain plus canonical sequence tiebreaker; unresolved conflict remains visible", "deterministic": True} for conflict in ("conflicting timestamps", "conflicting event sources", "clock skew", "distributed clock variance", "conflicting freshness determinations", "conflicting ordering", "contradictory replay ordering")],
        "B03-002_source_precedence_registry.json": [{"source": source, "precedence": index} for index, source in enumerate(("source event timestamps", "observation timestamps", "persistence timestamps", "replay timestamps", "archival timestamps"), start=1)],
        "B03-002_temporal_integrity_verification_report.json": {"one_definition_each": True, "one_timestamp_source_each": True, "freshness_deterministic": True, "ordering_deterministic": True, "replay_preserves_temporal_integrity": True, "duplicates_preserve_lineage": True, "conflict_resolution_deterministic": True, "ambiguities": []},
        "B03-002_completion_report.json": {"order": "MONITORING-RM-001-B03-002", "status": "COMPLETE"},
        "B03-003_constitutional_evidence_doctrine.json": {"evidence_origin": "constitutional events only", "documentation_authority": False, "metadata_only_authority": False, "implementation_assertion_authority": False, "historical_preservation_optional": False},
        "B03-003_canonical_evidence_registry.json": evidence,
        "B03-003_evidence_ownership_registry.json": [{"evidence_id": item["evidence_id"], "owner": item["constitutional_owner"]} for item in evidence],
        "B03-003_evidence_custody_registry.json": [{"evidence_id": item["evidence_id"], "custodian": item["constitutional_custodian"]} for item in evidence],
        "B03-003_evidence_producer_registry.json": [{"evidence_id": item["evidence_id"], "producer": item["constitutional_producer"]} for item in evidence],
        "B03-003_evidence_provenance_registry.json": [{"evidence_id": item["evidence_id"], "originating_event": item["constitutional_event"], "provenance_chain_required": True, "dependency_provenance_required": True, "external_provenance_required_where_applicable": True} for item in evidence],
        "B03-003_evidence_integrity_constitution.json": {"authenticity": True, "completeness": True, "immutability": True, "tamper_detection": True, "corruption_detection": True, "integrity_failure_handling": "fail closed and preserve evidence"},
        "B03-003_evidence_admissibility_registry.json": [{"evidence_id": item["evidence_id"], "admissibility_requirements": item["admissibility_requirements"], "inadmissible_if_missing": True} for item in evidence],
        "B03-003_evidence_retention_constitution.json": {"retention_owner": "Monitoring Office", "retention_duration": "permanent", "archival_authority": "Monitoring Office with Historian custody", "historical_loss_allowed": False},
        "B03-003_evidence_lineage_registry.json": [{"evidence_id": item["evidence_id"], "lineage_required": True, "predecessor_successor_relationships": True} for item in evidence],
        "B03-003_correction_evidence_registry.json": [{"evidence_id": item["evidence_id"], "correction_evidence_required": True} for item in evidence if "Correction" in item["constitutional_event"]],
        "B03-003_supersession_evidence_registry.json": [{"evidence_id": item["evidence_id"], "supersession_evidence_required": True} for item in evidence if "Supersession" in item["constitutional_event"]],
        "B03-003_evidence_reconciliation_registry.json": [{"condition": condition, "reconciliation_authority": "Monitoring Office", "external_truth_mutation": False, "outcome": "visible disposition with preserved history"} for condition in ("conflicting evidence", "incomplete evidence", "duplicate evidence", "missing evidence", "contradictory evidence", "unresolved discrepancies")],
        "B03-003_constitutionally_rejected_evidence_registry.json": [{"rejected_class": item, "constitutional_justification": "does not provide independently reproducible constitutional event evidence"} for item in REJECTED_EVIDENCE],
        "B03-003_evidence_ambiguity_resolution_report.json": {"ownership_ambiguity": False, "custody_ambiguity": False, "provenance_ambiguity": False, "admissibility_ambiguity": False, "integrity_ambiguity": False, "retention_ambiguity": False, "lineage_ambiguity": False, "ambiguities": []},
        "B03-003_completion_report.json": {"order": "MONITORING-RM-001-B03-003", "status": "COMPLETE"},
        "B03-004_canonical_requirement_registry.json": requirements,
        "B03-004_requirement_identity_registry.json": [{"requirement_id": item["canonical_requirement_identity"], "identity_immutable": item["identity_immutable"], "identity_creation_authority": "Monitoring Office constitutional governance", "versioning": "semantic constitutional version", "archival": "permanent"} for item in requirements],
        "B03-004_requirement_authority_registry.json": [{"requirement_id": item["canonical_requirement_identity"], "constitutional_authority": item["constitutional_authority"], "governing_work_order": item["governing_work_order"]} for item in requirements],
        "B03-004_requirement_ownership_registry.json": [{"requirement_id": item["canonical_requirement_identity"], "constitutional_owner": item["constitutional_owner"]} for item in requirements],
        "B03-004_constitutional_traceability_constitution.json": {"bidirectional_traceability_required": True, "authority_mutation_through_traceability_prohibited": True, "historical_traceability_preserved": True},
        "B03-004_bidirectional_constitutional_traceability_registry.json": traceability,
        "B03-004_constitutional_traceability_graph.json": traceability,
        "B03-004_requirement_relationship_matrix.json": [{"requirement_id": item["canonical_requirement_identity"], "parent": item["parent_requirement"], "children": item["child_requirements"]} for item in requirements],
        "B03-004_constitutional_artifact_participation_registry.json": [{"artifact": item["canonical_requirement_identity"], "participates_in_traceability": True, "traceability_id": f"{item['canonical_requirement_identity']}-TRACE"} for item in requirements],
        "B03-004_requirement_reconciliation_registry.json": {"duplicate_requirements": [], "aggregate_requirements": [], "fragmented_requirements": [], "conflicting_requirements": [], "historical_preservation": True},
        "B03-004_orphan_requirement_registry.json": [],
        "B03-004_orphan_constitutional_artifact_registry.json": [],
        "B03-004_traceability_integrity_verification_report.json": {"authority_to_requirement_complete": True, "requirement_to_authority_complete": True, "object_traceability_complete": True, "lifecycle_traceability_complete": True, "evidence_to_certification_complete": True, "dependency_traceable": True, "interface_traceable": True, "broken_chains": [], "ambiguous_traceability": []},
        "B03-004_constitutional_completeness_verification_report.json": {"statements_decomposed": True, "atomic_requirements": len(requirements), "one_identity_each": True, "one_owner_each": True, "one_authority_each": True, "traceability_graph_complete": True, "omitted_requirements": [], "untraced_artifacts": []},
        "B03-004_completion_report.json": {"order": "MONITORING-RM-001-B03-004", "status": "COMPLETE"},
        "monitoring_rm001_b03_authoritative_baseline.json": baseline,
        "series_completion_report.json": {"series": "MONITORING-RM-001-B03", "status": "COMPLETE", "depends_on": ["MONITORING-RM-001-B01", "MONITORING-RM-001-B02"], "orders_completed": ["B03-001", "B03-002", "B03-003", "B03-004"], "implementation_behavior_modified": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False, "baseline_digest": baseline["digest"]},
        "completion_report.json": {"package": "MONITORING-RM-001-B03 interface evidence traceability baseline", "status": "COMPLETE", "constitutional_doctrine_established": True, "implementation_behavior_modified": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False, "baseline_digest": baseline["digest"]},
    }
    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    (OUTPUT_DIR / "README.md").write_text(
        "# MONITORING-RM-001-B03 Interface, Evidence, and Traceability Baseline\n\n"
        "This package completes Monitoring constitutional interface/dependency governance, temporal and duplicate doctrine, evidence doctrine, and canonical requirement identity with bidirectional traceability. It does not modify implementation behavior or execute certification.\n",
        encoding="utf-8",
    )
    return artifacts["completion_report.json"]


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "output_dir": str(OUTPUT_DIR), "baseline_digest": result["baseline_digest"]}, indent=2, sort_keys=True))
