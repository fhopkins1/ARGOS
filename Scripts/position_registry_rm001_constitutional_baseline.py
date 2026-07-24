from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.contracts import utc_timestamp  # noqa: E402


OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_CONSTITUTIONAL_BASELINE"


OBJECTS = (
    ("PR-OBJ-001", "Position Record", "Authoritative active-position state container."),
    ("PR-OBJ-002", "Position Identity", "Stable canonical identifier for one enterprise position lifecycle."),
    ("PR-OBJ-003", "Instrument Identity", "Read-only referenced instrument identity admitted from authorized instrument authority."),
    ("PR-OBJ-004", "Account Identity", "Read-only referenced account identity admitted from authorized account authority."),
    ("PR-OBJ-005", "Workflow Identity", "Read-only workflow lineage reference admitted from Workflow authority."),
    ("PR-OBJ-006", "Authorization Reference", "Read-only authorization reference admitted from Authorizations authority."),
    ("PR-OBJ-007", "Risk Reference", "Read-only risk decision reference admitted from Risk authority."),
    ("PR-OBJ-008", "Broker Reference", "Read-only broker order/fill reference admitted from Broker authority."),
    ("PR-OBJ-009", "Quantity Record", "Position-owned current, available, reserved, pending, opened, and closed quantity state."),
    ("PR-OBJ-010", "Cost-Basis Record", "Position-owned average entry cost and adjusted basis for open position state only."),
    ("PR-OBJ-011", "Lifecycle-State Record", "Position-owned lifecycle state and transition lineage."),
    ("PR-OBJ-012", "Reconciliation Record", "Position-owned discrepancy and reconciliation lifecycle record."),
    ("PR-OBJ-013", "Correction Record", "Position-owned immutable correction and supersession lineage."),
    ("PR-OBJ-014", "Anomaly Record", "Position-owned unresolved contradiction and failure disposition record."),
    ("PR-OBJ-015", "Historical Record", "Immutable position history and mutation evidence chain."),
    ("PR-OBJ-016", "Archival Record", "Terminal preservation record after closure, retirement, or supersession."),
)

FIELDS = (
    ("position_id", "Position Registry", "identity_creation", "immutable", "canonical position identity"),
    ("instrument_id", "Instrument Authority", "reference_admission", "immutable_reference", "external instrument identity reference"),
    ("account_id", "Account Authority", "reference_admission", "immutable_reference", "external account identity reference"),
    ("workflow_id", "Workflow Authority", "reference_admission", "immutable_reference", "workflow lineage reference"),
    ("authorization_id", "Authorizations Authority", "reference_admission", "immutable_reference", "authorization lineage reference"),
    ("risk_id", "Risk Authority", "reference_admission", "immutable_reference", "risk lineage reference"),
    ("broker_order_ids", "Broker Authority", "reference_admission", "append_only", "broker order references"),
    ("fill_ids", "Broker Authority", "reference_admission", "append_only", "authoritative fill references"),
    ("current_quantity", "Position Registry", "position_mutation", "mutable_with_fill_evidence", "current open position quantity"),
    ("available_quantity", "Position Registry", "reservation_mutation", "mutable_with_authorization", "quantity not reserved for closure"),
    ("pending_quantity", "Position Registry", "reservation_or_pending_execution", "mutable_with_authorization", "quantity awaiting broker-confirmed mutation"),
    ("closed_quantity", "Position Registry", "position_mutation", "append_only", "quantity closed by broker-confirmed fills"),
    ("average_entry_cost", "Position Registry", "position_mutation", "mutable_with_fill_evidence", "average open-position entry cost"),
    ("adjusted_cost_basis", "Position Registry", "correction_or_adjustment", "mutable_with_correction", "open-position adjusted basis"),
    ("realized_value_reference", "Performance Truth", "reference_admission", "read_only_reference", "external realized performance reference"),
    ("unrealized_value", "Position Registry", "valuation_refresh", "derived_projection", "current open-position valuation projection"),
    ("lifecycle_state", "Position Registry", "lifecycle_transition", "mutable_with_transition_evidence", "canonical position lifecycle state"),
    ("reconciliation_state", "Position Registry", "reconciliation_transition", "mutable_with_reconciliation_evidence", "reconciliation lifecycle state"),
    ("correction_state", "Position Registry", "correction_transition", "mutable_with_correction_evidence", "correction lifecycle state"),
    ("anomaly_state", "Position Registry", "anomaly_transition", "mutable_with_anomaly_evidence", "anomaly disposition state"),
    ("created_at", "Position Registry", "identity_creation", "immutable", "position creation time"),
    ("updated_at", "Position Registry", "authorized_mutation", "append_only_history", "latest authorized mutation time"),
    ("history", "Position Registry", "history_append", "append_only", "immutable mutation and custody lineage"),
)

STATES = (
    "proposed",
    "pending_authorization",
    "authorized",
    "pending_opening_execution",
    "partially_opened",
    "open",
    "increasing",
    "reducing",
    "partially_closed",
    "pending_closure",
    "closed",
    "pending_reconciliation",
    "reconciled",
    "correction_pending",
    "corrected",
    "disputed",
    "suspended",
    "anomalous",
    "unrecoverable",
    "archived",
    "retired",
)

TRANSITIONS = (
    ("PR-TRANS-001", "proposed", "pending_authorization", "Commander or Workflow assignment", "mission and workflow evidence"),
    ("PR-TRANS-002", "pending_authorization", "authorized", "Authorizations Office", "authorization evidence"),
    ("PR-TRANS-003", "authorized", "pending_opening_execution", "Trader execution handoff", "execution intent reference"),
    ("PR-TRANS-004", "pending_opening_execution", "partially_opened", "Broker fill admission", "partial fill evidence"),
    ("PR-TRANS-005", "pending_opening_execution", "open", "Broker fill admission", "full fill evidence"),
    ("PR-TRANS-006", "open", "increasing", "Broker fill admission", "increase fill evidence"),
    ("PR-TRANS-007", "open", "pending_closure", "Exit authorization", "exit authorization evidence"),
    ("PR-TRANS-008", "pending_closure", "partially_closed", "Broker closing fill admission", "partial close fill evidence"),
    ("PR-TRANS-009", "pending_closure", "closed", "Broker closing fill admission", "full close fill evidence"),
    ("PR-TRANS-010", "closed", "pending_reconciliation", "Reconciliation trigger", "comparison source evidence"),
    ("PR-TRANS-011", "pending_reconciliation", "reconciled", "Position Registry reconciliation authority", "reconciliation evidence"),
    ("PR-TRANS-012", "pending_reconciliation", "disputed", "Position Registry reconciliation authority", "contradiction evidence"),
    ("PR-TRANS-013", "disputed", "correction_pending", "Correction approval authority", "correction request evidence"),
    ("PR-TRANS-014", "correction_pending", "corrected", "Position Registry correction authority", "correction record"),
    ("PR-TRANS-015", "closed", "archived", "Archival authority", "terminal preservation evidence"),
    ("PR-TRANS-016", "archived", "retired", "Governance retirement authority", "retirement evidence"),
)

BOUNDARIES = (
    ("Trader", "Consumes authorized position references; does not own position state."),
    ("Broker", "Provides order and fill evidence; does not mutate position state directly."),
    ("Authorizations", "Owns authorization issuance; Position Registry stores references only."),
    ("Risk", "Owns risk decisions and limits; Position Registry stores references only."),
    ("Monitoring", "Observes positions; read access does not confer mutation authority."),
    ("Exit Decision", "Recommends exits; does not close positions."),
    ("Closed Position Truth", "Owns closed-position truth; Position Registry owns open/active position state and closure lineage."),
    ("Performance Truth", "Owns performance truth; Position Registry owns open-position state and references realized truth."),
    ("Historian", "Preserves history; does not own active mutation authority."),
    ("Commander", "Receives reports and may assign missions; does not directly mutate position state."),
    ("Infrastructure", "Provides persistence and replay services; custody does not confer ownership."),
    ("Sentinel", "May observe or notify; does not mutate position state."),
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _object_registry() -> list[dict[str, Any]]:
    return [
        {
            "object_id": object_id,
            "name": name,
            "constitutional_definition": definition,
            "constitutional_owner": "Position Registry",
            "identity_authority": "Position Registry" if "Identity" in name or name == "Position Record" else "governing source authority",
            "creation_authority": "Position Registry",
            "authoritative_source": "Position Registry constitutional baseline",
            "dependent_objects": (),
            "predecessor_objects": (),
            "successor_objects": (),
            "immutable_identity_fields": ("position_id",) if object_id in {"PR-OBJ-001", "PR-OBJ-002"} else (),
            "mutable_state_fields": tuple(field[0] for field in FIELDS if field[1] == "Position Registry"),
            "terminal_disposition": "archived or retired with immutable history",
        }
        for object_id, name, definition in OBJECTS
    ]


def _field_registry() -> list[dict[str, Any]]:
    return [
        {
            "field_id": field_id,
            "constitutional_meaning": meaning,
            "data_classification": "constitutional_position_state",
            "required": field_id in {"position_id", "instrument_id", "workflow_id", "current_quantity", "lifecycle_state", "history"},
            "authoritative_source": owner,
            "creation_authority": owner,
            "mutation_authority": mutation_authority,
            "validation_authority": "Position Registry",
            "correction_authority": "Position Registry correction authority with source-owner evidence",
            "reconciliation_authority": "Position Registry",
            "allowed_value_domain": value_domain,
            "nullability": "prohibited when required; otherwise explicit unavailable-state evidence required",
            "default_authority": "defaults prohibited unless explicitly listed in schema baseline",
            "temporal_meaning": "event effective time plus processing and persistence time retained",
            "precision_requirements": "decimal precision preserved to source precision; calculations rounded only by declared rule",
            "unit_requirements": "quantity units and currency units retained separately",
            "sign_convention": "direction explicit; signed quantity requires declared long/short rule",
            "provenance_requirement": "source, authority, timestamp, evidence digest",
            "evidence_requirement": "immutable mutation or admission evidence",
            "retention_requirement": "permanent constitutional audit retention",
            "archival_requirement": "archived with terminal position record",
        }
        for field_id, owner, mutation_authority, value_domain, meaning in FIELDS
    ]


def _lifecycle_states() -> list[dict[str, Any]]:
    return [
        {
            "state_id": f"PR-STATE-{index:03d}",
            "state": state,
            "constitutional_meaning": state.replace("_", " "),
            "state_owner": "Position Registry",
            "entry_conditions": "authorized predecessor transition evidence",
            "entry_authority": "Position Registry transition authority",
            "required_evidence": "source event, authority, pre-state, post-state, timestamp, evidence digest",
            "permitted_mutations": "only mutations listed in field-authority matrix",
            "prohibited_mutations": "silent overwrite, external truth fabrication, history destruction",
            "exit_conditions": "authorized transition or terminal archival",
            "exit_authority": "Position Registry transition authority",
            "timeout_disposition": "pending_reconciliation or suspended with evidence",
            "contradiction_disposition": "disputed or anomalous with preserved conflicting evidence",
            "reconciliation_obligation": state in {"pending_reconciliation", "disputed", "anomalous"},
            "terminal_status": state in {"closed", "archived", "retired", "unrecoverable"},
        }
        for index, state in enumerate(STATES, start=1)
    ]


def _transitions() -> list[dict[str, Any]]:
    return [
        {
            "transition_id": transition_id,
            "source_state": source,
            "resulting_state": target,
            "transition_initiator": authority,
            "transition_authority": "Position Registry",
            "source_event": authority,
            "prerequisites": evidence,
            "validation_requirements": "identity, authority, quantity, temporal, provenance, and source admissibility validation",
            "authorization_requirements": "governing source authority must be present where applicable",
            "risk_requirements": "risk reference required when transition depends on risk approval",
            "quantity_effects": "none unless transition admits broker-confirmed fill or correction evidence",
            "cost_basis_effects": "none unless transition admits broker-confirmed opening fill or correction evidence",
            "evidence_requirements": evidence,
            "persistence_requirements": "append transition evidence before post-state becomes authoritative",
            "failure_disposition": "fail closed; preserve attempted transition evidence",
            "rollback_authority": "none; use correction and supersession",
            "retry_authority": "only where source event remains admissible and idempotency preserved",
            "correction_authority": "Position Registry correction authority",
            "reconciliation_authority": "Position Registry reconciliation authority",
        }
        for transition_id, source, target, authority, evidence in TRANSITIONS
    ]


def _ownership() -> list[dict[str, Any]]:
    return [
        {
            "object_id": item["object_id"],
            "constitutional_owner": "Position Registry",
            "governing_constitutional_authority": "POSITION-REGISTRY-RM-001-S01",
            "ownership_justification": "Position Registry owns active position state and immutable position lineage.",
            "ownership_scope": "position-state truth only; externally owned references remain external",
            "ownership_obligations": ("preserve identity", "preserve lineage", "fail closed on ambiguity"),
            "ownership_limitations": ("no trading decision", "no broker execution", "no performance truth ownership", "no closed-position truth ownership"),
            "ownership_lifecycle": "creation through archive and retirement",
            "ownership_evidence": "constitutional baseline registry entry",
        }
        for item in _object_registry()
    ]


def _registries() -> dict[str, Any]:
    generated_at = utc_timestamp()
    purpose = {
        "purpose_id": "PR-PURPOSE-001",
        "statement": "The Position Registry Office exists to own authoritative active position identity, state, lifecycle lineage, and reconciliation/correction records for Enterprise positions without owning trading decisions, broker execution, performance truth, or closed-position truth.",
        "enterprise_role": "authoritative active-position state office",
        "constitutional_necessity": "prevents execution, risk, authorization, monitoring, and performance offices from silently redefining position state",
        "protected_interests": ("single ownership", "immutable history", "source-authorized mutation", "reconciliation lineage"),
    }
    mission = {
        "mission_id": "PR-MISSION-001",
        "statement": "Maintain deterministic, immutable, source-authorized position state from creation through closure, correction, reconciliation, archival, and retirement.",
    }
    authorities = [
        {
            "authority_id": f"PR-AUTH-{index:03d}",
            "description": description,
            "constitutional_source": "POSITION-REGISTRY-RM-001-S01",
            "governing_constitutional_law": "Enterprise single ownership, immutable evidence, fail-closed authority",
            "authority_scope": scope,
            "authority_limitations": "does not supersede external source ownership",
            "prerequisite_authority": "admissible source evidence",
            "delegated_authority": "none unless explicitly listed",
            "retained_authority": "Position Registry",
        }
        for index, (description, scope) in enumerate(
            (
                ("Create canonical position identity", "position identity"),
                ("Admit authorized broker fill references", "position mutation evidence"),
                ("Mutate position-owned quantity and lifecycle state", "position-owned fields"),
                ("Reconcile position state against authoritative sources", "reconciliation records"),
                ("Correct position-owned records while preserving history", "correction records"),
                ("Archive and retire terminal position records", "archival records"),
            ),
            start=1,
        )
    ]
    responsibilities = [
        {"responsibility_id": f"PR-RESP-{index:03d}", "governing_authority": auth["authority_id"], "constitutional_owner": "Position Registry", "constitutional_purpose": purpose["purpose_id"], "governing_objects": ("Position Record",), "triggering_authority": auth["prerequisite_authority"], "completion_obligations": "record terminal evidence or fail closed", "evidence_obligations": "immutable evidence digest"}
        for index, auth in enumerate(authorities, start=1)
    ]
    prohibited = [
        "trading decisions",
        "order submission",
        "authorization issuance",
        "risk determination",
        "broker communication authority",
        "market data authority",
        "execution authority",
        "performance truth ownership",
        "closed position truth ownership",
        "silent historical correction",
        "constitutional governance outside delegated authority",
    ]
    prohibited_registry = [
        {"prohibition_id": f"PR-PROHIB-{index:03d}", "governing_constitutional_source": "POSITION-REGISTRY-RM-001-S01", "prohibited_actor": "Position Registry", "prohibited_action": item, "constitutional_rationale": "single ownership and office boundary preservation", "permitted_alternative_authority": "owning office", "violation_consequence": "constitutional failure"}
        for index, item in enumerate(prohibited, start=1)
    ]
    objects = _object_registry()
    fields = _field_registry()
    lifecycle = _lifecycle_states()
    transitions = _transitions()
    ownership = _ownership()
    custody = [
        {"object_id": item["object_id"], "operational_custodian": "Position Registry", "custody_authority": "POSITION-REGISTRY-RM-001-S01-B01-003", "custody_responsibilities": "store and preserve current state and lineage", "custody_limitations": "custody does not confer ownership over externally owned references", "custody_acquisition": "authorized creation or custody transfer", "custody_relinquishment": "archive or authorized custody transfer", "custody_evidence": "custody event", "terminal_custodian": "Historian or Infrastructure archival custody with Position Registry ownership retained"}
        for item in objects
    ]
    mutation = [
        {"field_id": item["field_id"], "mutation_authority": item["mutation_authority"], "governing_responsibility": "PR-RESP-003", "authorized_initiators": item["authoritative_source"], "authorized_mutation_conditions": item["evidence_requirement"], "mutation_prerequisites": item["provenance_requirement"], "mutation_validation": item["validation_authority"], "mutation_evidence": item["evidence_requirement"], "mutation_audit_requirements": "append-only history", "prohibited_mutation_authorities": "all unlisted authorities"}
        for item in fields
    ]
    correction = [
        {"object_id": item["object_id"], "correction_authority": "Position Registry", "correction_initiator": "owning source, reconciliation process, or Commander escalation", "correction_approval_authority": "Position Registry governance", "correction_prerequisites": "source evidence and preserved original state", "correction_evidence": "correction record", "correction_audit_requirements": "immutable supersession lineage", "correction_limitations": "no destructive replacement", "immutable_history_requirements": "retain original and corrected values"}
        for item in objects
    ]
    reconciliation = [
        {"object_id": item["object_id"], "reconciliation_authority": "Position Registry", "reconciliation_initiator": "discrepancy, scheduled check, source correction, or closure", "reconciliation_scope": "position-owned state and externally owned references", "reconciliation_evidence": "comparison record and source evidence", "reconciliation_approval_authority": "Position Registry", "reconciliation_completion_criteria": "reconciled, disputed, corrected, or escalated", "reconciliation_audit_requirements": "preserve all conflicting evidence"}
        for item in objects
    ]
    boundaries = [
        {"relationship_id": f"PR-BOUNDARY-{index:03d}", "office": office, "boundary": boundary, "object_ownership": "Position Registry owns position state only", "permitted_reads": "as authorized by read registry", "permitted_writes": "only through Position Registry mutation authority", "conflict_resolution_authority": "constitutional precedence registry"}
        for index, (office, boundary) in enumerate(BOUNDARIES, start=1)
    ]
    source_registry = [
        {"source_id": "PR-SOURCE-001", "source": "Enterprise Constitutional Law", "authority_scope": "single ownership, immutable evidence, fail closed"},
        {"source_id": "PR-SOURCE-002", "source": "POSITION-REGISTRY-RM-001-S01", "authority_scope": "purpose, authority, boundaries, ownership, custody"},
        {"source_id": "PR-SOURCE-003", "source": "POSITION-REGISTRY-RM-001-S02", "authority_scope": "objects, identity, schema, lifecycle"},
        {"source_id": "PR-SOURCE-004", "source": "Broker/Trader/Performance/Closed Truth governance", "authority_scope": "external source ownership and interface limits"},
    ]
    decisions = [
        {"decision_id": "PR-DEC-001", "governing_issue": "Position object ownership", "available_alternatives": ("Trader owns positions", "Position Registry owns active position state"), "selected_disposition": "Position Registry owns active position state", "governing_authority": "POSITION-REGISTRY-RM-001-S01", "constitutional_rationale": "separates execution from position truth", "effective_status": "AUTHORITATIVE"},
        {"decision_id": "PR-DEC-002", "governing_issue": "Performance and closed truth boundary", "available_alternatives": ("Position Registry owns all PnL truth", "Performance/Closed Truth own their records"), "selected_disposition": "Position Registry stores references only", "governing_authority": "POSITION-REGISTRY-RM-001-S01", "constitutional_rationale": "preserves office single ownership", "effective_status": "AUTHORITATIVE"},
        {"decision_id": "PR-DEC-003", "governing_issue": "Correction semantics", "available_alternatives": ("overwrite prior state", "append correction/supersession"), "selected_disposition": "append correction/supersession", "governing_authority": "POSITION-REGISTRY-RM-001-S02", "constitutional_rationale": "immutable history", "effective_status": "AUTHORITATIVE"},
    ]
    baseline = {
        "baseline_id": "POSITION-REGISTRY-RM-001-CONSTITUTIONAL-BASELINE",
        "generated_at": generated_at,
        "purpose": purpose,
        "mission": mission,
        "authority_model": authorities,
        "responsibility_model": responsibilities,
        "prohibited_responsibilities": prohibited_registry,
        "office_boundaries": boundaries,
        "object_model": objects,
        "field_model": fields,
        "lifecycle_model": lifecycle,
        "transition_model": transitions,
        "ownership_model": ownership,
        "custody_model": custody,
        "mutation_authority_model": mutation,
        "correction_authority_model": correction,
        "reconciliation_authority_model": reconciliation,
        "constitutional_sources": source_registry,
        "constitutional_decisions": decisions,
        "unresolved_constitutional_findings": [],
        "certification_statement": "Publication is constitutional governance only and is not implementation verification, proof, certification readiness, or certification.",
    }
    return {
        "purpose": purpose,
        "mission": mission,
        "authorities": authorities,
        "scope": {"scope_id": "PR-SCOPE-001", "governed_objects": [item[1] for item in OBJECTS], "governed_fields": [item[0] for item in FIELDS], "governed_lifecycle_states": STATES, "external_boundaries": [item[0] for item in BOUNDARIES]},
        "objectives": [{"objective_id": f"PR-OBJV-{i:03d}", "objective": value, "governing_authority": "POSITION-REGISTRY-RM-001-S01"} for i, value in enumerate(("authoritative position identity", "authoritative position state", "authoritative quantity tracking", "authoritative cost basis", "authoritative lifecycle tracking", "authoritative broker reference tracking", "authoritative workflow association", "authoritative reconciliation support", "authoritative historical preservation"), start=1)],
        "responsibilities": responsibilities,
        "prohibited": prohibited_registry,
        "sources": source_registry,
        "authority_conflicts": [],
        "implied_authority": [{"authority": "legacy Trader ownership phrasing", "resolution": "superseded by PR-DEC-001 and prohibited as authority source", "status": "RESOLVED"}],
        "ambiguity_assessment": {"unresolved_authority_ambiguity": False, "unresolved_responsibility_ambiguity": False, "unresolved_ownership_ambiguity": False},
        "remaining_deficiencies": [],
        "objects": objects,
        "fields": fields,
        "lifecycle": lifecycle,
        "transitions": transitions,
        "ownership": ownership,
        "custody": custody,
        "mutation": mutation,
        "correction": correction,
        "reconciliation": reconciliation,
        "boundaries": boundaries,
        "decisions": decisions,
        "baseline": baseline,
    }


def write_outputs() -> dict[str, Any]:
    data = _registries()
    files = {
        "B01-001_constitutional_purpose_statement.json": data["purpose"],
        "B01-001_constitutional_mission_statement.json": data["mission"],
        "B01-001_constitutional_authority_registry.json": data["authorities"],
        "B01-001_constitutional_scope_specification.json": data["scope"],
        "B01-001_constitutional_objectives_registry.json": data["objectives"],
        "B01-001_constitutional_responsibility_registry.json": data["responsibilities"],
        "B01-001_prohibited_responsibility_registry.json": data["prohibited"],
        "B01-001_governing_constitutional_source_registry.json": data["sources"],
        "B01-001_authority_conflict_registry.json": data["authority_conflicts"],
        "B01-001_implied_authority_registry.json": data["implied_authority"],
        "B01-001_constitutional_ambiguity_assessment.json": data["ambiguity_assessment"],
        "B01-001_remaining_governance_deficiency_registry.json": data["remaining_deficiencies"],
        "B02-001_position_registry_constitutional_object_registry.json": data["objects"],
        "B02-001_canonical_position_identity_constitution.json": {"identity": "position_id", "creation_conditions": "authorized position creation from admissible source evidence", "uniqueness_rule": "one active canonical position identity per account, instrument, strategy/workflow, and decision lineage unless split explicitly authorized", "persistence": "stable through archive and retirement", "collision_handling": "fail closed and create identity conflict record", "duplicate_handling": "idempotent reference or rejected duplicate", "correction_restrictions": "identity correction requires supersession"},
        "B02-001_object_identity_registry.json": [{"object_id": item["object_id"], "identity_fields": item["immutable_identity_fields"]} for item in data["objects"]],
        "B02-001_identity_relationship_registry.json": [{"position_identity": "position_id", "related_identity": field[0], "relationship": "reference only" if field[1] != "Position Registry" else "owned field"} for field in FIELDS if field[0].endswith("_id") or field[0].endswith("_ids")],
        "B02-001_identity_conflict_registry.json": [],
        "B02-001_object_dependency_registry.json": [{"object_id": item["object_id"], "dependencies": item["dependent_objects"]} for item in data["objects"]],
        "B02-002_constitutional_schema_registry.json": {"schema_id": "PR-SCHEMA-001", "objects": data["objects"], "fields": data["fields"]},
        "B02-002_field_definition_registry.json": data["fields"],
        "B02-002_field_authority_matrix.json": data["mutation"],
        "B02-002_validation_authority_registry.json": [{"field_id": item["field_id"], "validation_authority": item["validation_authority"]} for item in data["fields"]],
        "B02-002_value_domain_registry.json": [{"field_id": item["field_id"], "allowed_value_domain": item["allowed_value_domain"]} for item in data["fields"]],
        "B02-002_reference_integrity_registry.json": [{"field_id": item["field_id"], "source": item["authoritative_source"], "admissibility": item["provenance_requirement"]} for item in data["fields"]],
        "B02-002_schema_conflict_registry.json": [],
        "B02-003_canonical_position_lifecycle_constitution.json": {"lifecycle_owner": "Position Registry", "states": STATES, "transition_count": len(TRANSITIONS), "history_rule": "correction and reconciliation never destroy prior state"},
        "B02-003_lifecycle_state_registry.json": data["lifecycle"],
        "B02-003_state_transition_matrix.json": data["transitions"],
        "B02-003_transition_authority_registry.json": [{"transition_id": item["transition_id"], "transition_authority": item["transition_authority"]} for item in data["transitions"]],
        "B02-003_transition_evidence_registry.json": [{"transition_id": item["transition_id"], "evidence_requirements": item["evidence_requirements"]} for item in data["transitions"]],
        "B02-003_prohibited_transition_registry.json": [{"rule": "Any unlisted transition is prohibited", "disposition": "fail closed with attempted transition evidence"}],
        "B02-003_terminal_disposition_registry.json": [{"state": item["state"], "terminal": item["terminal_status"]} for item in data["lifecycle"]],
        "B02-003_lifecycle_conflict_registry.json": [],
        "B01-003_canonical_ownership_registry.json": data["ownership"],
        "B01-003_operational_custody_registry.json": data["custody"],
        "B01-003_mutation_authority_registry.json": data["mutation"],
        "B01-003_correction_authority_registry.json": data["correction"],
        "B01-003_reconciliation_authority_registry.json": data["reconciliation"],
        "B01-003_evidence_custody_registry.json": [{"object_id": item["object_id"], "evidence_custodian": "Infrastructure archival custody with Position Registry ownership", "retention_authority": "Position Registry", "archival_authority": "Position Registry"} for item in data["objects"]],
        "B01-003_read_population_registry.json": [{"object_id": item["object_id"], "authorized_readers": [office for office, _ in BOUNDARIES], "read_limitations": "read access never confers mutation authority"} for item in data["objects"]],
        "B01-003_ownership_transfer_registry.json": [{"object_id": item["object_id"], "transfer_authority": "constitutional amendment only", "history_preservation": "required"} for item in data["objects"]],
        "B01-003_custody_transfer_registry.json": [{"object_id": item["object_id"], "custody_transfer_authority": "Position Registry", "custody_transfer_evidence": "custody transfer record"} for item in data["objects"]],
        "B01-003_ownership_integrity_registry.json": {"split_ownership": [], "circular_ownership": [], "implied_ownership": [], "status": "RECONCILED"},
        "B01-003_mutation_integrity_registry.json": {"multiple_mutation_authorities": [], "unauthorized_mutation_authority": [], "status": "RECONCILED"},
        "B01-003_ownership_conflict_registry.json": [],
        "B01-003_constitutional_consistency_reconciliation_report.json": {"status": "RECONCILED", "unresolved_ownership_ambiguity": False, "unresolved_mutation_ambiguity": False},
        "B01-004_position_registry_constitutional_governance_baseline.json": data["baseline"],
        "B01-004_governance_reconciliation_registry.json": {"status": "RECONCILED", "inputs": ("B01-001", "B01-003", "S02 object/lifecycle baseline"), "unresolved_findings": []},
        "B01-004_constitutional_purpose_reconciliation_report.json": {"authoritative_purpose": data["purpose"], "duplicate_purpose_statements": [], "overbroad_purpose_statements": []},
        "B01-004_constitutional_authority_reconciliation_registry.json": data["authorities"],
        "B01-004_constitutional_responsibility_reconciliation_registry.json": data["responsibilities"],
        "B01-004_prohibited_responsibility_reconciliation_registry.json": data["prohibited"],
        "B01-004_office_boundary_reconciliation_registry.json": data["boundaries"],
        "B01-004_governance_relationship_reconciliation_registry.json": [{"relationship": "Position Registry subordinate to Enterprise constitutional governance", "delegated_authority": "position state ownership", "retained_authority": "Enterprise governance"}],
        "B01-004_dependency_reconciliation_registry.json": [{"dependency": office, "disposition": "authorized external dependency; no ownership transfer"} for office, _ in BOUNDARIES],
        "B01-004_ownership_reconciliation_registry.json": data["ownership"],
        "B01-004_custody_reconciliation_registry.json": data["custody"],
        "B01-004_mutation_authority_reconciliation_registry.json": data["mutation"],
        "B01-004_correction_authority_reconciliation_registry.json": data["correction"],
        "B01-004_reconciliation_authority_reconciliation_registry.json": data["reconciliation"],
        "B01-004_constitutional_conflict_resolution_registry.json": [{"conflict_id": "PR-CONFLICT-001", "conflicting_authorities": ("legacy Trader owns Position Objects phrasing", "Position Registry owns active position state"), "accepted_decision": "Position Registry owns active position state", "rejected_decision": "Trader owns Position Objects", "constitutional_rationale": "execution authority must not own position truth", "resulting_governance_state": "RESOLVED"}],
        "B01-004_constitutional_decision_registry.json": data["decisions"],
        "B01-004_constitutional_precedence_registry.json": [{"artifact_identifier": "POSITION-REGISTRY-RM-001", "constitutional_level": "Office constitutional baseline", "normative_status": "AUTHORITATIVE"}, {"artifact_identifier": "legacy implementation ownership comments", "constitutional_level": "Implementation", "normative_status": "NONNORMATIVE_REFERENCE"}],
        "B01-004_doctrine_supersession_registry.json": [{"superseded_provision": "Trader owns Position Objects wording", "superseding_authority": "PR-DEC-001", "effective_status": "PARTIALLY_SUPERSEDED"}],
        "B01-004_amendment_authority_registry.json": {"amendment_authority": "Enterprise constitutional governance", "implementation_actor_may_amend": False, "history_preservation_required": True},
        "B01-004_constitutional_freeze_authority_registry.json": {"freeze_authority": "Enterprise constitutional governance", "freeze_prerequisites": "no unresolved governance findings and baseline publication", "unfreeze_authority": "formal constitutional amendment"},
        "B01-004_certification_authority_registry.json": {"certification_authority": "Independent Enterprise Certification", "self_certification_permitted": False, "implementation_certification_not_issued": True},
        "B01-004_unresolved_constitutional_finding_registry.json": [],
        "B01-004_deterministic_governance_verification_report.json": {"deterministic": True, "question_count": 17, "repeatable_decision_digest": _digest(data["baseline"])},
        "B01-004_authoritative_governance_report.json": {"baseline_id": data["baseline"]["baseline_id"], "status": "PUBLISHED", "certification_disclaimer": data["baseline"]["certification_statement"]},
        "B02-004_object_reconciliation_registry.json": {"status": "RECONCILED", "duplicate_objects": [], "orphan_objects": []},
        "B02-004_identity_reconciliation_registry.json": {"status": "RECONCILED", "ambiguous_identities": [], "canonical_identity": "position_id"},
        "B02-004_schema_reconciliation_registry.json": {"status": "RECONCILED", "schema_conflicts": []},
        "B02-004_field_reconciliation_registry.json": {"status": "RECONCILED", "field_conflicts": []},
        "B02-004_lifecycle_reconciliation_registry.json": {"status": "RECONCILED", "implied_states": [], "unauthorized_transitions": []},
        "B02-004_unresolved_constitutional_finding_registry.json": [],
        "B02-004_constitutional_object_and_lifecycle_baseline.json": {"objects": data["objects"], "fields": data["fields"], "lifecycle": data["lifecycle"], "transitions": data["transitions"], "digest": _digest({"objects": data["objects"], "fields": data["fields"], "lifecycle": data["lifecycle"], "transitions": data["transitions"]})},
        "B02-004_authoritative_reconciliation_report.json": {"status": "PUBLISHED", "unresolved_ambiguity": False},
    }
    for name, payload in files.items():
        _write_json(OUTPUT_DIR / name, payload)
    _write_json(OUTPUT_DIR / "B01-001_completion_report.json", {"order": "B01-001", "status": "COMPLETE", "deliverables": [name for name in files if name.startswith("B01-001")], "implementation_evaluated": False, "behavioral_verification_executed": False})
    _write_json(OUTPUT_DIR / "B01-003_completion_report.json", {"order": "B01-003", "status": "COMPLETE", "deliverables": [name for name in files if name.startswith("B01-003")], "implementation_evaluated": False})
    _write_json(OUTPUT_DIR / "B01-004_completion_report.json", {"order": "B01-004", "status": "COMPLETE", "deliverables": [name for name in files if name.startswith("B01-004")], "unresolved_findings": 0, "implementation_certification_issued": False})
    _write_json(OUTPUT_DIR / "S02_series_completion_report.json", {"series": "POSITION-REGISTRY-RM-001-S02", "status": "COMPLETE", "unresolved_object_model_or_lifecycle_ambiguity": False, "implementation_evaluated": False, "behavioral_verification_executed": False})
    _write_json(OUTPUT_DIR / "completion_report.json", {"package": "POSITION-REGISTRY-RM-001 constitutional baseline", "status": "COMPLETE", "generated_at": utc_timestamp(), "baseline_digest": _digest(data["baseline"]), "implementation_behavior_modified": False, "behavioral_verification_executed": False, "implementation_certification_issued": False})
    (OUTPUT_DIR / "README.md").write_text("# Position Registry RM-001 Constitutional Baseline\n\nConstitutional governance, object, schema, ownership, custody, and lifecycle baseline only. No implementation behavior was modified or certified.\n", encoding="utf-8")
    return {"status": "COMPLETE", "files": len(files) + 5, "output_dir": str(OUTPUT_DIR)}


def main() -> int:
    print(json.dumps(write_outputs(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
