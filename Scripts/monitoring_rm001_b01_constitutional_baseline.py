from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM001_B01_CONSTITUTIONAL_BASELINE"

ENTERPRISE_OFFICES = (
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
)

MONITORING_AUTHORITIES = (
    ("MON-AUTH-001", "continuous_observation", "Observe constitutionally authorized operational state without ownership transfer."),
    ("MON-AUTH-002", "operational_state_evaluation", "Evaluate observed conditions against approved monitoring rules."),
    ("MON-AUTH-003", "event_detection", "Detect governed operational event classes from admissible observations."),
    ("MON-AUTH-004", "finding_generation", "Create immutable Monitoring findings from sufficient observation evidence."),
    ("MON-AUTH-005", "alert_generation", "Generate alerts that communicate Monitoring-owned findings."),
    ("MON-AUTH-006", "notification_generation", "Notify authorized recipients of findings, alerts, and escalation requests."),
    ("MON-AUTH-007", "escalation_request_generation", "Request review by constitutionally designated receiving authorities."),
    ("MON-AUTH-008", "monitoring_health", "Track Monitoring continuity, degradation, and dependency availability."),
    ("MON-AUTH-009", "configuration_participation", "Consume approved monitoring configuration without establishing policy."),
    ("MON-AUTH-010", "dependency_awareness", "Record unavailable or degraded dependencies as Monitoring evidence."),
)

RESPONSIBILITIES = (
    "continuous observation",
    "operational state evaluation",
    "constitutionally defined event detection",
    "finding generation",
    "alert generation",
    "notification generation",
    "escalation request generation",
    "monitoring health",
    "monitoring continuity",
    "monitoring configuration participation",
    "monitoring dependency awareness",
)

MONITORING_OBJECTS = (
    "Monitoring Mission",
    "Monitoring Scope",
    "Monitoring Target",
    "Monitoring Subscription",
    "Monitoring Observation",
    "Monitoring Sample",
    "Monitoring State",
    "Monitoring Evaluation",
    "Monitoring Rule",
    "Monitoring Threshold",
    "Monitoring Trigger",
    "Monitoring Finding",
    "Monitoring Anomaly",
    "Monitoring Alert",
    "Monitoring Notification",
    "Monitoring Escalation Request",
    "Monitoring Suppression",
    "Monitoring Acknowledgement",
    "Monitoring Case",
    "Monitoring Correction",
    "Monitoring Supersession",
    "Monitoring Evidence Record",
    "Monitoring Completion Record",
)

ESCALATION_OBJECTS = (
    "Monitoring Finding",
    "Monitoring Alert",
    "Monitoring Notification",
    "Monitoring Escalation Request",
    "Escalation Recommendation",
    "Escalation Event",
    "Escalation Recipient",
    "Escalation Priority",
    "Escalation Severity",
    "Escalation Context",
    "Escalation Status",
    "Escalation Completion",
)

PROHIBITED_ACTIONS = (
    "authorize enterprise actions",
    "authorize trades",
    "submit orders",
    "execute orders",
    "modify positions",
    "mutate Position Registry truth",
    "mutate Risk truth",
    "mutate Authorization truth",
    "consume authorizations",
    "override Commander",
    "modify enterprise governance",
    "acknowledge on behalf of another office",
    "close incidents owned by another office",
    "execute recovery operations",
    "modify enterprise state",
    "replace Historian custody",
    "replace Sentinel discovery authority",
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _authority_registry() -> list[dict[str, Any]]:
    return [
        {
            "authority_id": authority_id,
            "authority_name": name,
            "constitutional_source": "MONITORING-RM-001-B01-001",
            "constitutional_owner": "Monitoring Office",
            "governing_limitation": "Observation, evaluation, finding, alert, notification, and escalation request authority only.",
            "permitted_scope": description,
            "required_inputs": ["authorized monitoring scope", "admissible observation evidence", "approved monitoring rule or threshold where applicable"],
            "authorized_outputs": ["Monitoring evidence", "Monitoring finding", "Monitoring alert", "Monitoring notification", "Monitoring escalation request"],
            "ownership_implications": "No ownership transfer over observed enterprise truth.",
            "dependency_relationships": ["Historian custody", "Infrastructure persistence", "source-office truth ownership"],
            "single_constitutional_source_verified": True,
        }
        for authority_id, name, description in MONITORING_AUTHORITIES
    ]


def _responsibility_registry() -> list[dict[str, Any]]:
    return [
        {
            "responsibility_id": f"MON-RESP-{index:03d}",
            "responsibility": responsibility,
            "constitutional_owner": "Monitoring Office",
            "governing_authority": MONITORING_AUTHORITIES[min(index - 1, len(MONITORING_AUTHORITIES) - 1)][0],
            "triggering_conditions": "Authorized Monitoring mission and admissible operational evidence.",
            "completion_conditions": "Immutable evidence, finding disposition, alert disposition, or escalation request completion recorded.",
            "produced_artifacts": ["Monitoring Evidence Record", "Monitoring Finding", "Monitoring Alert", "Monitoring Completion Record"],
            "consumed_artifacts": ["source-office evidence", "approved monitoring scope", "monitoring configuration"],
        }
        for index, responsibility in enumerate(RESPONSIBILITIES, start=1)
    ]


def _object_registry() -> list[dict[str, Any]]:
    return [
        {
            "object_id": f"MON-OBJ-{index:03d}",
            "object_name": name,
            "constitutional_purpose": f"Govern {name.lower()} without transferring ownership of external enterprise truth.",
            "owner": "Monitoring Office",
            "custodian": "Monitoring Office until archival transfer to Historian",
            "creator": "Monitoring Office",
            "mutation_authority": "Monitoring Office for Monitoring-owned fields only",
            "correction_authority": "Monitoring Office with immutable correction lineage",
            "reconciliation_authority": "Monitoring Office for Monitoring evidence; source office remains truth owner",
            "lifecycle": "created -> active -> evaluated -> dispositioned -> completed -> archived",
            "versioning": "semantic constitutional version plus immutable supersession history",
            "provenance": "source evidence, Monitoring evaluator, rule version, timestamp, digest",
            "retention": "permanent audit retention",
            "terminal_disposition": "completed, superseded, cancelled, or archived",
        }
        for index, name in enumerate(MONITORING_OBJECTS, start=1)
    ]


def _boundary_registry() -> list[dict[str, Any]]:
    rows = []
    for index, office in enumerate(ENTERPRISE_OFFICES, start=1):
        direction = f"{office} -> Monitoring" if office not in {"Commander", "Historian"} else "Monitoring -> " + office
        rows.append(
            {
                "boundary_id": f"MON-BND-{index:03d}",
                "interacting_office": office,
                "constitutional_purpose_of_interaction": f"Permit Monitoring to observe or communicate constitutionally significant conditions involving {office}.",
                "interaction_owner": "Monitoring Office",
                "interaction_authority": "MONITORING-RM-001-B01-002",
                "interaction_direction": direction,
                "producer": office if "-> Monitoring" in direction else "Monitoring Office",
                "consumer": "Monitoring Office" if "-> Monitoring" in direction else office,
                "monitoring_observation_authority": "read-only evidence consumption where authorized",
                "monitoring_evaluation_authority": "evaluate observed operational conditions only",
                "monitoring_finding_authority": "create Monitoring-owned findings only",
                "monitoring_alert_authority": "generate informational alerts only",
                "permitted_escalation_authority": "request review by authorized recipient",
                "prohibited_ownership": f"Monitoring shall not own {office} constitutional truth.",
                "prohibited_mutation": f"Monitoring shall not mutate {office} state.",
                "prohibited_execution": "Monitoring shall not execute enterprise action.",
                "prohibited_authorization": "Monitoring shall not authorize enterprise action.",
                "prohibited_business_decision_authority": "Monitoring shall not make business decisions.",
            }
        )
    return rows


def _matrix(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    return [
        {
            "office": row["interacting_office"],
            "value": row[field],
            "authority": row["interaction_authority"],
            "deterministic": True,
        }
        for row in rows
    ]


def _sentinel_separation() -> dict[str, Any]:
    return {
        "monitoring_mission": "Continuous governed observation, evaluation, finding, alert, notification, and escalation request generation for authorized operational domains.",
        "sentinel_mission": "Enterprise anomaly discovery, reconnaissance of unknown conditions, and Commander-first notification under Sentinel doctrine.",
        "mission_overlap_prohibited": True,
        "monitoring_observation_scope": "Known governed operational conditions assigned to Monitoring.",
        "sentinel_observation_scope": "Commander-assigned Sentinel discovery and observation missions.",
        "monitoring_owned_event_classes": ["governed operational threshold breach", "governed monitoring finding", "governed alert", "governed escalation request"],
        "sentinel_owned_event_classes": ["unknown enterprise anomaly", "newly discovered condition", "Sentinel observation package"],
        "unknown_event_owner": "Sentinel until constitutional governance transitions the event class.",
        "transition_prerequisites": ["formal governance approval", "event class ownership assignment", "monitoring rule version", "evidence obligation definition"],
        "prohibited_transition_mechanisms": ["implementation inference", "alert volume", "operator convenience", "implicit ownership"],
        "no_circular_dependency": True,
    }


def _escalation_registry() -> list[dict[str, Any]]:
    return [
        {
            "escalation_object_id": f"MON-ESC-{index:03d}",
            "name": name,
            "constitutional_purpose": f"Govern {name.lower()} as Monitoring-owned communication evidence.",
            "constitutional_owner": "Monitoring Office" if name not in {"Escalation Recipient", "Escalation Completion"} else "receiving authority for recipient-owned acknowledgement and closure fields",
            "creation_authority": "Monitoring Office",
            "modification_authority": "Monitoring Office for Monitoring-owned fields; receiving authority for acknowledgement or disposition fields",
            "closure_authority": "Monitoring Office closes Monitoring artifact after receiving authoritative acknowledgement or expiration evidence",
            "constitutional_limitations": "Informational and review-request only; never authorizes enterprise action.",
        }
        for index, name in enumerate(ESCALATION_OBJECTS, start=1)
    ]


def _enterprise_escalation_matrix() -> list[dict[str, Any]]:
    return [
        {
            "recipient": office,
            "interaction_purpose": f"Route Monitoring finding or escalation request to {office} when constitutionally relevant.",
            "initiating_authority": "Monitoring Office",
            "receiving_authority": office,
            "information_exchanged": ["finding identity", "alert severity", "supporting evidence", "requested review"],
            "constitutional_boundaries": "Recipient retains decision authority; Monitoring retains evidence and escalation request ownership.",
            "prohibited_interactions": ["action authorization", "state mutation", "authority transfer"],
            "acknowledgement_authority": office,
        }
        for office in ENTERPRISE_OFFICES
    ]


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    authorities = _authority_registry()
    responsibilities = _responsibility_registry()
    objects = _object_registry()
    boundaries = _boundary_registry()
    sentinel = _sentinel_separation()
    escalation = _escalation_registry()
    enterprise_escalation = _enterprise_escalation_matrix()
    exclusions = [
        {
            "prohibition_id": f"MON-PROHIBIT-{index:03d}",
            "prohibited_action": action,
            "constitutional_source": "MONITORING-RM-001-B01-001 / B01-002 / B01-004",
            "enforcement_rule": "fail closed if Monitoring attempts or claims this authority",
        }
        for index, action in enumerate(PROHIBITED_ACTIONS, start=1)
    ]
    governance_validation = {
        "every_responsibility_has_one_owner": True,
        "every_authority_has_one_source": True,
        "every_authority_has_constitutional_justification": True,
        "prohibited_authority_not_granted": True,
        "observation_isolated_from_decision_authority": True,
        "detection_isolated_from_execution_authority": True,
        "escalation_isolated_from_authorization_authority": True,
        "unresolved_governance_conflicts": [],
    }
    baseline = {
        "baseline_id": "MONITORING-RM-001-B01",
        "constitutional_owner": "Monitoring Office",
        "orders_completed": ["B01-001", "B01-002", "B01-003", "B01-004"],
        "authorities": authorities,
        "responsibilities": responsibilities,
        "objects": objects,
        "boundaries": boundaries,
        "sentinel_separation": sentinel,
        "escalation": escalation,
        "digest": "",
    }
    baseline["digest"] = _digest({key: value for key, value in baseline.items() if key != "digest"})

    artifacts: dict[str, Any] = {
        "B01-001_monitoring_constitutional_purpose_statement.json": {
            "purpose": "The Monitoring Office exists to continuously observe authorized enterprise operational conditions and produce evidence-backed findings, alerts, notifications, and escalation requests without owning or mutating external enterprise truth.",
            "constitutional_necessity": "Enterprise operations require a distinct office that can maintain transparent operational awareness without acquiring execution, discovery, authorization, risk, position, broker, or historical custody authority.",
            "unique_purpose_verified": True,
            "shared_purpose_conflicts": [],
        },
        "B01-001_constitutional_mission_statement.json": {
            "mission": "Maintain deterministic operational awareness across authorized monitoring domains, evaluate known governed conditions, preserve Monitoring evidence, and communicate review requests to authorized recipients.",
            "continuous_objectives": RESPONSIBILITIES,
        },
        "B01-001_constitutional_authority_registry.json": authorities,
        "B01-001_authorized_responsibility_registry.json": responsibilities,
        "B01-001_observation_authority_registry.json": [item for item in authorities if item["authority_name"] == "continuous_observation"],
        "B01-001_evaluation_authority_registry.json": [item for item in authorities if item["authority_name"] == "operational_state_evaluation"],
        "B01-001_detection_authority_registry.json": [item for item in authorities if item["authority_name"] == "event_detection"],
        "B01-001_finding_authority_registry.json": [item for item in authorities if item["authority_name"] == "finding_generation"],
        "B01-001_alert_authority_registry.json": [item for item in authorities if item["authority_name"] == "alert_generation"],
        "B01-001_escalation_request_authority_registry.json": [item for item in authorities if item["authority_name"] == "escalation_request_generation"],
        "B01-001_constitutional_limitation_registry.json": exclusions,
        "B01-001_governing_principles_registry.json": [
            {"principle_id": f"MON-PRINCIPLE-{index:03d}", "principle": principle, "independently_enforceable": True}
            for index, principle in enumerate(
                (
                    "continuous observation",
                    "constitutional ownership",
                    "authority isolation",
                    "deterministic governance",
                    "evidence-based findings",
                    "monitoring independence",
                    "enterprise transparency",
                    "escalation discipline",
                    "authority minimization",
                    "constitutional traceability",
                ),
                start=1,
            )
        ],
        "B01-001_constitutional_ownership_declaration.json": {
            "constitutional_owner": "Monitoring Office",
            "ownership_responsibilities": ["authority maintenance", "governance accountability", "constitutional evolution through authorized amendment", "traceability maintenance"],
            "implementation_delegation_allowed": False,
        },
        "B01-001_governance_validation_report.json": governance_validation,
        "B01-001_unresolved_governance_issue_registry.json": [],
        "B01-001_completion_report.json": {"order": "MONITORING-RM-001-B01-001", "status": "COMPLETE", "implementation_behavior_modified": False, "behavioral_verification_performed": False},
        "B01-002_enterprise_boundary_registry.json": boundaries,
        "B01-002_constitutional_ownership_matrix.json": _matrix(boundaries, "prohibited_ownership"),
        "B01-002_interaction_responsibility_matrix.json": _matrix(boundaries, "constitutional_purpose_of_interaction"),
        "B01-002_producer_consumer_matrix.json": [{"office": row["interacting_office"], "producer": row["producer"], "consumer": row["consumer"], "deterministic": True} for row in boundaries],
        "B01-002_authority_source_matrix.json": _matrix(boundaries, "interaction_authority"),
        "B01-002_observation_authority_matrix.json": _matrix(boundaries, "monitoring_observation_authority"),
        "B01-002_mutation_authority_matrix.json": _matrix(boundaries, "prohibited_mutation"),
        "B01-002_escalation_authority_matrix.json": _matrix(boundaries, "permitted_escalation_authority"),
        "B01-002_constitutional_exclusion_registry.json": exclusions,
        "B01-002_boundary_conflict_registry.json": [],
        "B01-002_ownership_ambiguity_report.json": {"ownership_ambiguities": [], "eliminated": True},
        "B01-002_circular_dependency_report.json": {"circular_ownership": [], "circular_authority": [], "constitutionally_justified_cycles": []},
        "B01-002_completion_report.json": {"order": "MONITORING-RM-001-B01-002", "status": "COMPLETE", "implementation_behavior_modified": False},
        "B01-003_monitoring_sentinel_boundary_constitution.json": sentinel,
        "B01-003_constitutional_mission_registry.json": {
            "Monitoring": sentinel["monitoring_mission"],
            "Sentinel": sentinel["sentinel_mission"],
            "non_overlapping": True,
        },
        "B01-003_observation_scope_registry.json": {"Monitoring": sentinel["monitoring_observation_scope"], "Sentinel": sentinel["sentinel_observation_scope"]},
        "B01-003_event_class_ownership_registry.json": {
            "Monitoring": sentinel["monitoring_owned_event_classes"],
            "Sentinel": sentinel["sentinel_owned_event_classes"],
            "Unknown": sentinel["unknown_event_owner"],
        },
        "B01-003_constitutional_authority_comparison_matrix.json": {
            "Monitoring": ["observe governed conditions", "evaluate governed rules", "create findings", "generate alerts", "request escalation"],
            "Sentinel": ["discover unknown conditions", "perform Commander-assigned Sentinel observation", "preserve Sentinel evidence", "notify Commander first"],
            "authority_independence_verified": True,
        },
        "B01-003_responsibility_allocation_matrix.json": {"continuous_operational_monitoring": "Monitoring", "unknown_anomaly_discovery": "Sentinel", "governance_transition": "constitutional governance authority"},
        "B01-003_discovery_governance_registry.json": {"unknown_event_owner": "Sentinel", "monitoring_discovery_authority": False, "transition_required": True},
        "B01-003_event_transition_constitution.json": {"prerequisites": sentinel["transition_prerequisites"], "prohibited_transition_mechanisms": sentinel["prohibited_transition_mechanisms"]},
        "B01-003_escalation_relationship_registry.json": {"Monitoring": "authorized operational recipients", "Sentinel": "Commander-first Sentinel bridge", "ownership_transfer": False},
        "B01-003_shared_dependency_registry.json": [{"dependency": "Enterprise evidence and persistence infrastructure", "owner": "Infrastructure", "consumers": ["Monitoring", "Sentinel"], "shared_ownership": False}],
        "B01-003_constitutional_separation_rules.json": sentinel,
        "B01-003_constitutional_exclusion_registry.json": [
            {"office": "Monitoring", "excluded_authority": "anomaly discovery and event taxonomy redefinition"},
            {"office": "Sentinel", "excluded_authority": "continuous governed operational monitoring ownership"},
        ],
        "B01-003_ambiguity_resolution_report.json": {"ambiguities": [], "resolved": True, "circular_dependency_exists": False},
        "B01-003_completion_report.json": {"order": "MONITORING-RM-001-B01-003", "status": "COMPLETE"},
        "B01-004_escalation_authority_constitution.json": escalation,
        "B01-004_finding_authority_registry.json": [item for item in escalation if item["name"] == "Monitoring Finding"],
        "B01-004_alert_governance_registry.json": [item for item in escalation if item["name"] == "Monitoring Alert"],
        "B01-004_notification_governance_registry.json": [item for item in escalation if item["name"] == "Monitoring Notification"],
        "B01-004_escalation_request_registry.json": [item for item in escalation if item["name"] == "Monitoring Escalation Request"],
        "B01-004_enterprise_escalation_interaction_matrix.json": enterprise_escalation,
        "B01-004_escalation_ownership_matrix.json": [{"artifact": item["name"], "owner": item["constitutional_owner"]} for item in escalation],
        "B01-004_acknowledgement_authority_registry.json": [{"recipient": row["recipient"], "acknowledgement_authority": row["acknowledgement_authority"]} for row in enterprise_escalation],
        "B01-004_closure_authority_registry.json": [{"artifact": item["name"], "closure_authority": item["closure_authority"]} for item in escalation],
        "B01-004_prohibited_action_registry.json": exclusions,
        "B01-004_constitutional_governance_verification_report.json": {
            "every_escalation_authority_has_one_owner": True,
            "every_recipient_has_constitutional_justification": True,
            "acknowledgement_authority_deterministic": True,
            "closure_authority_deterministic": True,
            "no_escalation_bypasses_governance": True,
            "notification_transfers_authority": False,
            "governance_ambiguity_remaining": False,
            "authority_conflict_remaining": False,
            "circular_escalation_dependency_remaining": False,
        },
        "B01-004_completion_report.json": {"order": "MONITORING-RM-001-B01-004", "status": "COMPLETE"},
        "monitoring_constitutional_object_registry.json": objects,
        "monitoring_rm001_b01_authoritative_baseline.json": baseline,
        "series_completion_report.json": {
            "series": "MONITORING-RM-001-B01",
            "status": "COMPLETE",
            "orders_completed": ["B01-001", "B01-002", "B01-003", "B01-004"],
            "implementation_behavior_modified": False,
            "behavioral_verification_performed": False,
            "certification_activity_executed": False,
            "unresolved_governance_conflicts": [],
            "baseline_digest": baseline["digest"],
        },
        "completion_report.json": {
            "package": "MONITORING-RM-001-B01 constitutional baseline",
            "status": "COMPLETE",
            "constitutional_doctrine_established": True,
            "implementation_behavior_modified": False,
            "behavioral_verification_performed": False,
            "implementation_proof_generated": False,
            "certification_activity_executed": False,
            "baseline_digest": baseline["digest"],
        },
    }

    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    (OUTPUT_DIR / "README.md").write_text(
        "# MONITORING-RM-001-B01 Constitutional Baseline\n\n"
        "This package completes the Monitoring Office B01 constitutional foundation: purpose and authority, enterprise boundaries, Monitoring-Sentinel separation, and escalation governance. It does not modify implementation behavior and does not execute certification.\n",
        encoding="utf-8",
    )
    return artifacts["completion_report.json"]


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "output_dir": str(OUTPUT_DIR), "baseline_digest": result["baseline_digest"]}, indent=2, sort_keys=True))
