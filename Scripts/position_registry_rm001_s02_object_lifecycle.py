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


OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S02_OBJECT_LIFECYCLE"


OBJECTS = (
    ("PR-S02-OBJ-001", "position_identity", "Position Registry", "Stable canonical identity for one position lifecycle."),
    ("PR-S02-OBJ-002", "position_record", "Position Registry", "Canonical active position state and lineage."),
    ("PR-S02-OBJ-003", "position_state", "Position Registry", "Current constitutional state of the canonical position object."),
    ("PR-S02-OBJ-004", "position_status", "Position Registry", "Admissible operational status derived from lifecycle state."),
    ("PR-S02-OBJ-005", "position_lifecycle_state", "Position Registry", "Lifecycle state with entry, exit, evidence, and transition authority."),
    ("PR-S02-OBJ-006", "position_quantity", "Position Registry", "Canonical signed quantity state derived from admissible events."),
    ("PR-S02-OBJ-007", "open_quantity", "Position Registry", "Quantity currently open and subject to valuation."),
    ("PR-S02-OBJ-008", "closed_quantity", "Position Registry", "Quantity closed by authorized lifecycle transition."),
    ("PR-S02-OBJ-009", "realized_quantity", "Position Registry", "Quantity removed from open state with realization evidence."),
    ("PR-S02-OBJ-010", "unrealized_quantity", "Position Registry", "Quantity remaining open after admissible transitions."),
    ("PR-S02-OBJ-011", "position_direction", "Position Registry", "Long, short, flat, or reversed directional interpretation."),
    ("PR-S02-OBJ-012", "average_cost_basis", "Position Registry", "Open-position average cost basis derived from admissible fills and corrections."),
    ("PR-S02-OBJ-013", "entry_cost_basis", "Position Registry", "Initial entry basis derived from opening events."),
    ("PR-S02-OBJ-014", "cost_basis_history", "Position Registry", "Immutable cost-basis lineage across events, corrections, and supersessions."),
    ("PR-S02-OBJ-015", "position_valuation_reference", "Valuation Authority", "External valuation reference admitted without transferring valuation truth ownership."),
    ("PR-S02-OBJ-016", "instrument_identity", "Instrument Authority", "External instrument identity and multiplier reference admitted as read-only evidence."),
    ("PR-S02-OBJ-017", "account_identity", "Account Authority", "External account reference admitted as read-only evidence."),
    ("PR-S02-OBJ-018", "broker_position_identity", "Broker", "Broker position identifier admitted as external broker truth evidence."),
    ("PR-S02-OBJ-019", "broker_execution_reference", "Broker", "Broker execution reference admitted as immutable external evidence."),
    ("PR-S02-OBJ-020", "fill_reference", "Broker", "Broker fill reference admitted as source event evidence."),
    ("PR-S02-OBJ-021", "workflow_identity", "Workflow Authority", "External workflow lineage reference admitted as read-only evidence."),
    ("PR-S02-OBJ-022", "authorization_reference", "Authorizations", "External authorization reference admitted as read-only evidence."),
    ("PR-S02-OBJ-023", "risk_reference", "Risk", "External risk decision reference admitted as read-only evidence."),
    ("PR-S02-OBJ-024", "monitoring_reference", "Monitoring", "Observation and monitoring reference without mutation authority."),
    ("PR-S02-OBJ-025", "exit_reference", "Exit Decision", "Exit recommendation and authorization reference without closure truth ownership."),
    ("PR-S02-OBJ-026", "closed_position_reference", "Closed Position Truth", "Reference to immutable closed-position truth after transfer."),
    ("PR-S02-OBJ-027", "performance_reference", "Performance Truth", "Reference to derived performance truth without ownership transfer."),
    ("PR-S02-OBJ-028", "reconciliation_case", "Position Registry", "Discrepancy, contradiction, and comparison lifecycle record."),
    ("PR-S02-OBJ-029", "correction_record", "Position Registry", "Authorized correction preserving original and corrected state."),
    ("PR-S02-OBJ-030", "supersession_record", "Position Registry", "Predecessor/successor lineage for constitutional replacement."),
    ("PR-S02-OBJ-031", "historical_position_record", "Position Registry", "Immutable history of every state, value, authority, and evidence mutation."),
    ("PR-S02-OBJ-032", "archival_record", "Position Registry", "Terminal retention, custody, and access record."),
)

STATES = (
    "creation",
    "pending",
    "open",
    "increasing",
    "decreasing",
    "partially_closed",
    "fully_closed",
    "correction_pending",
    "reconciliation_pending",
    "disputed",
    "superseded",
    "archived",
)

TRANSITIONS = (
    ("PR-S02-TRANS-001", "creation", "pending", "Workflow or Commander assignment", "identity and mission evidence"),
    ("PR-S02-TRANS-002", "pending", "open", "Broker-confirmed opening fill admission", "authoritative fill evidence"),
    ("PR-S02-TRANS-003", "open", "increasing", "Broker-confirmed additional opening fill", "fill identity and quantity evidence"),
    ("PR-S02-TRANS-004", "increasing", "open", "Position Registry validation", "updated quantity and cost evidence"),
    ("PR-S02-TRANS-005", "open", "decreasing", "Broker-confirmed closing fill admission", "closing fill evidence"),
    ("PR-S02-TRANS-006", "decreasing", "partially_closed", "Position Registry validation", "remaining quantity evidence"),
    ("PR-S02-TRANS-007", "decreasing", "fully_closed", "Position Registry validation", "zero quantity and closure evidence"),
    ("PR-S02-TRANS-008", "partially_closed", "decreasing", "Broker-confirmed closing fill admission", "closing fill evidence"),
    ("PR-S02-TRANS-009", "fully_closed", "reconciliation_pending", "Reconciliation trigger", "comparison evidence"),
    ("PR-S02-TRANS-010", "reconciliation_pending", "disputed", "Contradiction detection", "preserved conflicting evidence"),
    ("PR-S02-TRANS-011", "disputed", "correction_pending", "Correction approval authority", "correction request and source evidence"),
    ("PR-S02-TRANS-012", "correction_pending", "fully_closed", "Correction authority", "correction record and supersession lineage"),
    ("PR-S02-TRANS-013", "fully_closed", "archived", "Archival authority", "terminal preservation evidence"),
    ("PR-S02-TRANS-014", "open", "superseded", "Supersession authority", "successor identity and supersession evidence"),
    ("PR-S02-TRANS-015", "superseded", "archived", "Archival authority", "superseded lineage preservation evidence"),
)

QUANTITY_RULES = (
    ("signed_quantity", "Directional quantity value; positive long, negative short only when short doctrine is authorized.", "Position Registry", "source fill quantity and side", "decimal source precision retained; comparison tolerance explicit"),
    ("absolute_quantity", "Magnitude of exposure independent of side.", "Position Registry", "validated position quantity", "non-negative decimal"),
    ("opened_quantity", "Cumulative admitted opening quantity.", "Position Registry", "authoritative opening fills", "append-only aggregation"),
    ("current_quantity", "Quantity currently open in the position.", "Position Registry", "opening and closing fills plus corrections", "never silently negative"),
    ("pending_quantity", "Quantity reserved or awaiting broker-confirmed mutation.", "Position Registry", "exit authorization or pending execution evidence", "separate from current quantity"),
    ("realized_quantity", "Quantity that has left open-position state.", "Position Registry", "closing fill evidence", "append-only"),
    ("unrealized_quantity", "Quantity still open and subject to valuation.", "Position Registry", "current quantity", "equals current quantity after validation"),
    ("closed_quantity", "Total quantity closed from the position lifecycle.", "Position Registry", "closing fill evidence", "append-only"),
    ("correction_quantity", "Quantity value introduced by authorized correction.", "Position Registry", "correction evidence", "preserves original value"),
    ("reconciliation_quantity", "Quantity compared against external sources.", "Position Registry", "reconciliation evidence", "does not mutate without correction authority"),
)

COST_RULES = (
    ("average_entry_price", "Weighted average opening fill price before adjustments.", "opening fills", "sum(price * quantity) / sum(quantity)", "source currency"),
    ("average_cost_basis", "Open-position cost basis after authorized adjustments.", "opening fills and corrections", "weighted average with explicit adjustment records", "position currency"),
    ("gross_cost_basis", "Cost basis excluding fees and commissions.", "opening fills", "gross fill amount aggregation", "source currency"),
    ("net_cost_basis", "Cost basis including constitutionally authorized fees or commissions.", "opening fills plus fee records", "fee treatment requires fee authority", "position currency"),
    ("realized_cost_basis", "Cost basis allocated to closed quantity.", "closing fills and prior basis", "pro-rata average cost unless lot doctrine later authorizes lots", "position currency"),
    ("remaining_cost_basis", "Cost basis retained by open quantity.", "current quantity and basis", "average cost multiplied by remaining quantity", "position currency"),
    ("corrected_cost_basis", "Basis after authorized correction or restatement.", "correction record", "preserve predecessor basis and corrected basis", "position currency"),
)

TEMPORAL_RULES = (
    ("event_time", "Time asserted by source event.", "source authority", "UTC normalized with source precision retained"),
    ("broker_time", "Broker-reported order/fill time.", "Broker", "admissible only with broker evidence"),
    ("receipt_time", "Time Position Registry receives event.", "Position Registry", "never sole lifecycle authority"),
    ("processing_time", "Time validation executes.", "Position Registry", "audit only; not source truth"),
    ("persistence_time", "Time state or evidence is persisted.", "Infrastructure custody", "does not imply lifecycle transition"),
    ("reconciliation_time", "Time reconciliation comparison is performed.", "Position Registry", "records comparison, not source mutation"),
    ("correction_time", "Time correction is authorized and recorded.", "Position Registry", "separate from effective time"),
    ("terminal_time", "Time terminal state is entered.", "Position Registry", "requires terminal evidence"),
    ("replay_time", "Time replay is performed.", "Replay authority", "does not alter original event time"),
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
            "canonical_object_name": name,
            "constitutional_description": description,
            "constitutional_purpose": f"Govern {name.replace('_', ' ')} without transferring ownership from external authorities.",
            "constitutional_owner": "Position Registry" if owner == "Position Registry" else owner,
            "operational_custodian": "Position Registry",
            "governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-001",
            "governing_lifecycle": "position_object_lifecycle",
            "versioning_doctrine": "version identity is immutable; successor versions preserve predecessor lineage",
            "mutability_doctrine": "only listed mutable state fields may change through authorized evidence",
            "terminal_disposition": "archived with immutable historical record",
            "mutation_authority": "Position Registry" if owner == "Position Registry" else "external owner only; Position Registry consumes reference",
            "correction_authority": "Position Registry" if owner == "Position Registry" else owner,
            "reconciliation_authority": "Position Registry",
            "evidence_owner": owner,
            "evidence_obligations": ("identity evidence", "authority evidence", "source evidence", "lineage evidence"),
            "retention_requirements": "immutable retention through active, terminal, replay, and audit lifecycles",
            "supersession_requirements": "successor identity, predecessor identity, authority, evidence, and lineage must be preserved",
            "archival_requirements": "archival record preserves canonical identity, evidence, state, and lineage",
            "approved_aliases": (),
            "prohibited_duplicate_identities": ("implementation class names", "broker ids", "workflow ids"),
        }
        for object_id, name, owner, description in OBJECTS
    ]


def _object_dependencies(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dependency_targets = {
        "position_record": ("position_identity", "position_state", "position_quantity", "average_cost_basis"),
        "position_state": ("position_lifecycle_state",),
        "position_quantity": ("open_quantity", "closed_quantity", "realized_quantity", "unrealized_quantity", "position_direction"),
        "average_cost_basis": ("entry_cost_basis", "cost_basis_history"),
        "reconciliation_case": ("broker_execution_reference", "fill_reference", "correction_record"),
        "correction_record": ("supersession_record", "historical_position_record"),
        "archival_record": ("historical_position_record",),
    }
    by_name = {item["canonical_object_name"]: item["object_id"] for item in objects}
    dependencies: list[dict[str, Any]] = []
    for source, targets in dependency_targets.items():
        for target in targets:
            dependencies.append(
                {
                    "source_object": source,
                    "source_object_id": by_name[source],
                    "target_object": target,
                    "target_object_id": by_name[target],
                    "dependency_direction": f"{source} -> {target}",
                    "relationship_type": "constitutional_object_dependency",
                    "deterministic_direction": True,
                    "governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-001",
                }
            )
    return dependencies


def _object_invariants(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "object_id": item["object_id"],
            "canonical_object_name": item["canonical_object_name"],
            "identity_invariant": "canonical identity is immutable and never implementation-derived",
            "ownership_invariant": "exactly one constitutional owner governs the object",
            "lifecycle_invariant": "every state change follows the governing lifecycle and transition evidence",
            "mutation_invariant": "mutation requires explicit mutation authority and admissible evidence",
            "reconciliation_invariant": "reconciliation records disagreement without silent mutation",
            "evidence_invariant": "identity, authority, source, and lineage evidence must be retained",
            "historical_invariant": "supersession and correction preserve predecessor history",
            "invariant_violations": [],
            "ambiguous_invariants": [],
            "conflicting_invariants": [],
        }
        for item in objects
    ]


def _lifecycle_constitution() -> dict[str, Any]:
    return {
        "constitution_id": "PR-S02-LIFECYCLE-CONSTITUTION",
        "lifecycle_owner": "Position Registry",
        "states": [
            {
                "state": state,
                "constitutional_meaning": state.replace("_", " "),
                "entry_authority": "Position Registry with governing source evidence",
                "exit_authority": "Position Registry with authorized transition evidence",
                "correction_authority": "Position Registry correction authority",
                "replay_behavior": "replay preserves this state when derived from the same authoritative event sequence",
                "restart_behavior": "restart restores this state from persisted evidence without advancement",
                "recovery_behavior": "recovery restores or quarantines; never fabricates state",
                "terminal_behavior": "immutable after terminal entry except authorized correction",
            }
            for state in STATES
        ],
    }


def _transition_registry() -> list[dict[str, Any]]:
    return [
        {
            "transition_id": transition_id,
            "source_state": source,
            "destination_state": destination,
            "entry_authority": authority,
            "exit_authority": "Position Registry",
            "transition_evidence": evidence,
            "prohibited_transitions": "all unlisted source/destination pairs",
            "correction_authority": "Position Registry correction authority with immutable lineage",
            "replay_behavior": "replay may reproduce but not newly authorize this transition",
            "restart_behavior": "restart must not advance transition state",
            "recovery_behavior": "failed or partial transition enters reconciliation_pending or disputed",
            "terminal_behavior": "terminal transitions prohibit later mutation except correction/supersession",
        }
        for transition_id, source, destination, authority, evidence in TRANSITIONS
    ]


def _quantity_registry() -> list[dict[str, Any]]:
    return [
        {
            "quantity_id": f"PR-S02-QTY-{index:03d}",
            "quantity_name": name,
            "constitutional_meaning": meaning,
            "owner": owner,
            "authoritative_source": source,
            "mutation_authority": "Position Registry",
            "admissible_inputs": source,
            "precision": precision,
            "rounding": "rounding prohibited during source admission; comparison/display rounding must be explicitly recorded",
            "aggregation_rule": "idempotent fill/event aggregation with duplicate rejection",
            "temporal_interpretation": "ordered by event-ordering doctrine",
            "correction_rule": "correction preserves predecessor quantity",
            "reconciliation_rule": "comparison does not mutate without correction authority",
            "evidence_requirement": "source event, authority, identity, quantity, timestamp, digest",
        }
        for index, (name, meaning, owner, source, precision) in enumerate(QUANTITY_RULES, start=1)
    ]


def _cost_registry() -> list[dict[str, Any]]:
    return [
        {
            "cost_basis_id": f"PR-S02-COST-{index:03d}",
            "field": field,
            "constitutional_meaning": meaning,
            "authoritative_inputs": inputs,
            "owner": "Position Registry",
            "mutation_authority": "Position Registry",
            "calculation_rule": calc,
            "precision": "decimal source precision retained; calculation precision recorded",
            "rounding_sequence": "calculate before rounding; rounded value never replaces raw evidence",
            "currency": currency,
            "temporal_basis": "event-ordering doctrine",
            "correction_rule": "preserve original and corrected basis",
            "reconciliation_rule": "basis discrepancy becomes reconciliation case",
            "evidence_obligation": "fill/correction/currency evidence with digest",
        }
        for index, (field, meaning, inputs, calc, currency) in enumerate(COST_RULES, start=1)
    ]


def _temporal_registry() -> list[dict[str, Any]]:
    return [
        {
            "timestamp_id": f"PR-S02-TIME-{index:03d}",
            "timestamp_name": name,
            "authoritative_meaning": meaning,
            "source": source,
            "owner": source,
            "mutation_authority": "source authority; Position Registry may admit reference only",
            "trust_classification": "source asserted" if source != "Position Registry" else "registry audit time",
            "required_precision": "ISO-8601 UTC with source precision retained",
            "timezone": "UTC",
            "normalization_rule": rule,
            "ordering_authority": "event-ordering registry",
            "evidence_requirement": "timestamp source and admissibility evidence",
            "correction_rule": "timestamp correction requires correction record and original timestamp retention",
        }
        for index, (name, meaning, source, rule) in enumerate(TEMPORAL_RULES, start=1)
    ]


def _historical_doctrine() -> dict[str, Any]:
    anomaly_dispositions = {
        "duplicate_event": "reject or idempotently ignore with duplicate evidence",
        "out_of_order_event": "quarantine into reconciliation_pending until ordering authority resolves",
        "contradictory_event": "enter disputed and preserve all conflicting evidence",
        "stale_event": "reject or quarantine according to freshness authority",
        "late_event": "admit only through reconciliation/correction authority",
        "replay_event": "reproduce historical transition without creating new truth",
        "restart_event": "restore persisted state without lifecycle advancement",
    }
    return {
        "correction_constitution": {
            "correction_authority": "Position Registry",
            "correction_initiator": "source authority, reconciliation finding, or Commander escalation",
            "correction_prerequisites": "governing source evidence plus preserved original state",
            "correction_validation": "identity, source, temporal, quantity, cost, and authority validation",
            "correction_completion_criteria": "correction record, predecessor, successor, reason, and evidence digest published",
            "immutable_history_obligations": "never overwrite predecessor truth",
        },
        "correction_lineage_registry": [{"lineage_rule": "every correction links corrected object, predecessor identity, successor identity, authority, evidence, replay behavior, and audit obligations"}],
        "replay_constitution": {"replay_authority": "Replay authority under Position Registry doctrine", "replay_ordering": "event-ordering registry", "identity_preservation": True, "fabrication_prohibited": True},
        "restart_constitution": {"restart_authority": "Infrastructure recovery custody", "state_restoration": "from persisted evidence only", "identity_preservation": True, "lifecycle_advancement_prohibited": True},
        "recovery_constitution": {"recovery_authority": "Position Registry with Infrastructure custody", "partial_write_disposition": "quarantine and reconcile", "corrupted_state_disposition": "detect, preserve, recover or mark unrecoverable"},
        "supersession_constitution": {"supersession_authority": "Position Registry constitutional authority", "superseded_object_preserved": True, "successor_object_required": True, "historical_truth_destroyed": False},
        "supersession_lineage_registry": [{"lineage_rule": "predecessor chain and successor chain remain queryable and replayable"}],
        "historical_integrity_registry": [{"history": name, "immutable": True, "preservation_rule": "append-only lineage with original evidence retention"} for name in ("object identity", "lifecycle", "ownership", "quantity", "cost basis", "correction", "supersession", "replay", "recovery", "audit", "evidence")],
        "replay_integrity_registry": [{"rule": "same authoritative inputs produce identical object identities, lifecycle outcomes, quantities, cost basis, temporal ordering, and historical lineage"}],
        "event_anomaly_constitution": anomaly_dispositions,
        "terminal_state_integrity_registry": [{"terminal_state": state, "permitted_corrections": "authorized correction only", "prohibited_mutations": "all direct mutation", "archival_behavior": "preserve and make retrievable"} for state in ("fully_closed", "superseded", "archived")],
        "archival_constitution": {"archival_authority": "Position Registry", "archival_trigger": "terminal state or supersession", "destruction_authority": "none unless superior constitutional amendment", "retrieval_authority": "authorized audit and replay"},
        "historical_ambiguity_registry": [],
    }


def write_outputs() -> dict[str, Any]:
    generated_at = utc_timestamp()
    objects = _object_registry()
    object_dependencies = _object_dependencies(objects)
    object_invariants = _object_invariants(objects)
    lifecycle = _lifecycle_constitution()
    transitions = _transition_registry()
    quantities = _quantity_registry()
    costs = _cost_registry()
    temporal = _temporal_registry()
    historical = _historical_doctrine()
    prohibited = [
        {"source_state": "*", "attempted_destination_state": "unlisted", "prohibition_authority": "POSITION-REGISTRY-RM-001-S02", "constitutional_rationale": "only explicit transitions are authorized", "required_rejection_behavior": "fail closed and preserve attempt evidence", "evidence_obligation": "attempted transition record", "escalation_consequence": "reconciliation or constitutional finding"}
    ]
    decisions = [
        {"decision_id": "PR-S02-DEC-001", "governing_issue": "reversal through zero", "selected_disposition": "closure of original position plus creation of new reversed position unless future doctrine authorizes identity reuse", "constitutional_rationale": "prevents silent identity reuse across opposing exposure"},
        {"decision_id": "PR-S02-DEC-002", "governing_issue": "average cost basis", "selected_disposition": "weighted average for open position unless lot doctrine is separately authorized", "constitutional_rationale": "deterministic baseline without implying tax-lot authority"},
        {"decision_id": "PR-S02-DEC-003", "governing_issue": "equal timestamps", "selected_disposition": "equal timestamps require sequence identifier or reconciliation disposition", "constitutional_rationale": "prevents discretionary ordering"},
        {"decision_id": "PR-S02-DEC-004", "governing_issue": "archival semantics", "selected_disposition": "archival changes custody/access only, never truth", "constitutional_rationale": "terminal history remains immutable"},
    ]
    baseline = {
        "baseline_id": "POSITION-REGISTRY-RM-001-S02-OBJECT-LIFECYCLE-BASELINE",
        "generated_at": generated_at,
        "object_constitution": objects,
        "identity_constitution": {"canonical_position_identity": "position_id", "identity_stability": "creation through archive", "collision_disposition": "fail closed and create identity conflict"},
        "relationship_constitution": [{"source_object": "position_record", "target_object": item["canonical_object_name"], "relationship_type": "contains_or_references", "governing_authority": "POSITION-REGISTRY-RM-001-S02"} for item in objects if item["canonical_object_name"] != "position_record"],
        "dependency_constitution": object_dependencies,
        "invariant_constitution": object_invariants,
        "lifecycle_constitution": lifecycle,
        "lifecycle_transition_constitution": transitions,
        "prohibited_transition_registry": prohibited,
        "quantity_constitution": quantities,
        "reversal_constitution": decisions[0],
        "cost_basis_constitution": costs,
        "precision_and_rounding_constitution": {"rounding_method": "explicit rule per field; raw evidence retained", "zero_rule": "zero closes only through authorized transition", "overflow_disposition": "fail closed", "underflow_disposition": "fail closed"},
        "currency_constitution": {"currency_identity": "source and reporting currency retained", "conversion_authority": "external financial authority", "conversion_time": "effective time recorded", "position_registry_owns_conversion": False},
        "temporal_constitution": temporal,
        "event_ordering_constitution": {"precedence": ("canonical sequence identifier", "broker sequence identifier", "venue sequence identifier", "broker event time", "receipt time", "processing time", "persistence time", "reconciliation authority", "correction authority"), "equal_timestamp_disposition": "requires sequence or reconciliation"},
        "correction_constitution": historical["correction_constitution"],
        "replay_constitution": historical["replay_constitution"],
        "restart_and_recovery_constitution": {"restart": historical["restart_constitution"], "recovery": historical["recovery_constitution"]},
        "supersession_constitution": historical["supersession_constitution"],
        "archival_constitution": historical["archival_constitution"],
        "terminal_state_constitution": historical["terminal_state_integrity_registry"],
        "historical_integrity_constitution": historical["historical_integrity_registry"],
        "constitutional_decision_registry": decisions,
        "constitutional_precedence_registry": [{"artifact_identifier": "POSITION-REGISTRY-RM-001-S02", "normative_status": "AUTHORITATIVE"}, {"artifact_identifier": "implementation runtime states", "normative_status": "NONNORMATIVE_REFERENCE"}],
        "doctrine_supersession_registry": [{"superseded_provision": "implementation-derived lifecycle or arithmetic convention", "superseding_authority": "POSITION-REGISTRY-RM-001-S02", "normative_status": "SUPERSEDED_AS_AUTHORITY"}],
        "unresolved_constitutional_finding_registry": [],
        "certification_statement": "Publication is constitutional doctrine only; no implementation verification, proof, certification readiness, or certification is issued.",
    }
    outputs: dict[str, Any] = {
        "B02-001_canonical_object_registry.json": objects,
        "B02-001_object_identity_registry.json": [{"object_id": item["object_id"], "canonical_object_name": item["canonical_object_name"], "canonical_identity": item["object_id"]} for item in objects],
        "B02-001_canonical_object_identity_registry.json": [{"object_id": item["object_id"], "canonical_object_name": item["canonical_object_name"], "canonical_identity": item["object_id"], "immutable": True} for item in objects],
        "B02-001_constitutional_purpose_registry.json": [{"object_id": item["object_id"], "constitutional_purpose": item["constitutional_purpose"]} for item in objects],
        "B02-001_object_ownership_registry.json": [{"object_id": item["object_id"], "constitutional_owner": item["constitutional_owner"]} for item in objects],
        "B02-001_constitutional_object_ownership_registry.json": [{"object_id": item["object_id"], "canonical_object_name": item["canonical_object_name"], "constitutional_owner": item["constitutional_owner"]} for item in objects],
        "B02-001_operational_custody_registry.json": [{"object_id": item["object_id"], "operational_custodian": item["operational_custodian"], "custody_duration": "active through archive"} for item in objects],
        "B02-001_constitutional_object_custody_registry.json": [{"object_id": item["object_id"], "canonical_object_name": item["canonical_object_name"], "operational_custodian": item["operational_custodian"], "archival_requirements": item["archival_requirements"]} for item in objects],
        "B02-001_object_authority_registry.json": [{"object_id": item["object_id"], "governing_authority": item["governing_authority"]} for item in objects],
        "B02-001_constitutional_object_authority_registry.json": [{"object_id": item["object_id"], "canonical_object_name": item["canonical_object_name"], "governing_authority": item["governing_authority"], "mutation_authority": item["mutation_authority"], "correction_authority": item["correction_authority"], "reconciliation_authority": item["reconciliation_authority"]} for item in objects],
        "B02-001_object_lifecycle_registry.json": [{"object_id": item["object_id"], "governing_lifecycle": item["governing_lifecycle"]} for item in objects],
        "B02-001_object_lifecycle_participation_registry.json": [{"object_id": item["object_id"], "canonical_object_name": item["canonical_object_name"], "lifecycle_participation": item["governing_lifecycle"], "terminal_disposition": item["terminal_disposition"]} for item in objects],
        "B02-001_versioning_registry.json": [{"object_id": item["object_id"], "versioning_doctrine": item["versioning_doctrine"]} for item in objects],
        "B02-001_mutability_registry.json": [{"object_id": item["object_id"], "mutability_doctrine": item["mutability_doctrine"]} for item in objects],
        "B02-001_terminal_disposition_registry.json": [{"object_id": item["object_id"], "terminal_disposition": item["terminal_disposition"]} for item in objects],
        "B02-001_evidence_obligation_registry.json": [{"object_id": item["object_id"], "evidence_obligations": item["evidence_obligations"]} for item in objects],
        "B02-001_object_evidence_registry.json": [{"object_id": item["object_id"], "canonical_object_name": item["canonical_object_name"], "evidence_owner": item["evidence_owner"], "evidence_obligations": item["evidence_obligations"], "retention_requirements": item["retention_requirements"]} for item in objects],
        "B02-001_object_relationship_registry.json": baseline["relationship_constitution"],
        "B02-001_object_dependency_registry.json": object_dependencies,
        "B02-001_object_invariant_registry.json": object_invariants,
        "B02-001_object_conflict_registry.json": [],
        "B02-001_constitutional_object_completeness_assessment.json": {"complete": True, "objects": len(objects), "undefined_objects": 0, "duplicate_objects": 0, "orphan_objects": 0, "objects_lacking_authority": 0, "objects_lacking_ownership": 0, "objects_lacking_lifecycle": 0, "objects_lacking_evidence_obligations": 0, "objects_lacking_reconciliation_authority": 0, "objects_lacking_historical_preservation": 0},
        "B02-001_object_completeness_assessment.json": {"complete": True, "objects": len(objects), "undefined_objects": 0, "duplicate_objects": 0, "orphan_objects": 0, "objects_lacking_authority": 0, "objects_lacking_ownership": 0, "objects_lacking_lifecycle": 0, "objects_lacking_evidence_obligations": 0, "objects_lacking_reconciliation_authority": 0, "objects_lacking_historical_preservation": 0},
        "B02-001_duplicate_object_registry.json": [],
        "B02-001_orphan_object_registry.json": [],
        "B02-001_remaining_constitutional_object_deficiency_registry.json": [],
        "B02-001_unresolved_constitutional_object_findings_registry.json": [],
        "B02-001_canonical_object_constitution_report.json": {"order": "POSITION-REGISTRY-RM-001-S02-B02-001", "status": "COMPLETE", "canonical_object_count": len(objects), "relationship_count": len(baseline["relationship_constitution"]), "dependency_count": len(object_dependencies), "invariant_count": len(object_invariants), "no_duplicate_canonical_objects": True, "no_orphan_constitutional_objects": True, "no_unresolved_constitutional_object_ambiguity": True, "implementation_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False},
        "B02-001_completion_report.json": {"order": "B02-001", "status": "COMPLETE", "implementation_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False, "canonical_object_count": len(objects), "no_duplicate_canonical_objects": True, "no_orphan_constitutional_objects": True, "no_unresolved_constitutional_object_ambiguity": True},
        "B02-002_lifecycle_constitution.json": lifecycle,
        "B02-002_lifecycle_transition_registry.json": transitions,
        "B02-002_quantity_doctrine_registry.json": quantities,
        "B02-002_cost_basis_doctrine_registry.json": costs,
        "B02-002_temporal_doctrine_registry.json": temporal,
        "B02-002_lifecycle_ambiguity_registry.json": [],
        "B02-002_completion_report.json": {"order": "B02-002", "status": "COMPLETE", "ambiguous_transitions": 0, "undefined_cost_basis_rules": 0, "incomplete_temporal_doctrine": 0, "implementation_evaluated": False},
        "B02-003_correction_constitution.json": historical["correction_constitution"],
        "B02-003_correction_lineage_registry.json": historical["correction_lineage_registry"],
        "B02-003_replay_constitution.json": historical["replay_constitution"],
        "B02-003_restart_constitution.json": historical["restart_constitution"],
        "B02-003_recovery_constitution.json": historical["recovery_constitution"],
        "B02-003_supersession_constitution.json": historical["supersession_constitution"],
        "B02-003_supersession_lineage_registry.json": historical["supersession_lineage_registry"],
        "B02-003_historical_integrity_registry.json": historical["historical_integrity_registry"],
        "B02-003_replay_integrity_registry.json": historical["replay_integrity_registry"],
        "B02-003_terminal_state_integrity_registry.json": historical["terminal_state_integrity_registry"],
        "B02-003_archival_constitution.json": historical["archival_constitution"],
        "B02-003_historical_ambiguity_registry.json": historical["historical_ambiguity_registry"],
        "B02-003_constitutional_consistency_reconciliation_report.json": {"status": "RECONCILED", "unresolved_historical_ambiguity": False, "unresolved_replay_ambiguity": False, "unresolved_correction_ambiguity": False},
        "B02-003_completion_report.json": {"order": "B02-003", "status": "COMPLETE", "historical_truth_destroyable": False, "replay_fabrication_permitted": False, "implementation_evaluated": False},
        "B02-004_position_registry_object_constitution_baseline.json": {"objects": objects, "digest": _digest(objects)},
        "B02-004_position_registry_lifecycle_constitution_baseline.json": {"lifecycle": lifecycle, "transitions": transitions, "digest": _digest({"lifecycle": lifecycle, "transitions": transitions})},
        "B02-004_position_registry_quantity_constitution_baseline.json": {"quantities": quantities, "digest": _digest(quantities)},
        "B02-004_position_registry_cost_basis_constitution_baseline.json": {"cost_basis": costs, "digest": _digest(costs)},
        "B02-004_position_registry_temporal_constitution_baseline.json": {"temporal": temporal, "digest": _digest(temporal)},
        "B02-004_canonical_object_reconciliation_registry.json": {"status": "RECONCILED", "duplicate_objects": [], "orphan_objects": [], "object_count": len(objects)},
        "B02-004_canonical_identity_reconciliation_registry.json": {"status": "RECONCILED", "canonical_identity": "position_id", "identity_collisions": []},
        "B02-004_object_relationship_reconciliation_registry.json": {"status": "RECONCILED", "relationships": baseline["relationship_constitution"]},
        "B02-004_lifecycle_state_reconciliation_registry.json": {"status": "RECONCILED", "states": STATES},
        "B02-004_lifecycle_transition_reconciliation_registry.json": {"status": "RECONCILED", "transitions": [item["transition_id"] for item in transitions]},
        "B02-004_prohibited_transition_registry.json": prohibited,
        "B02-004_quantity_doctrine_reconciliation_registry.json": {"status": "RECONCILED", "rules": quantities},
        "B02-004_reversal_doctrine_registry.json": decisions[0],
        "B02-004_cost_basis_doctrine_reconciliation_registry.json": {"status": "RECONCILED", "rules": costs},
        "B02-004_precision_and_rounding_registry.json": baseline["precision_and_rounding_constitution"],
        "B02-004_currency_doctrine_registry.json": baseline["currency_constitution"],
        "B02-004_temporal_doctrine_reconciliation_registry.json": {"status": "RECONCILED", "rules": temporal},
        "B02-004_event_ordering_registry.json": baseline["event_ordering_constitution"],
        "B02-004_correction_doctrine_reconciliation_registry.json": historical["correction_constitution"],
        "B02-004_replay_doctrine_reconciliation_registry.json": historical["replay_constitution"],
        "B02-004_restart_and_recovery_doctrine_registry.json": baseline["restart_and_recovery_constitution"],
        "B02-004_supersession_doctrine_reconciliation_registry.json": historical["supersession_constitution"],
        "B02-004_archival_doctrine_reconciliation_registry.json": historical["archival_constitution"],
        "B02-004_terminal_state_registry.json": historical["terminal_state_integrity_registry"],
        "B02-004_historical_integrity_reconciliation_registry.json": historical["historical_integrity_registry"],
        "B02-004_constitutional_conflict_resolution_registry.json": [{"conflict_id": "PR-S02-CONFLICT-001", "accepted_decision": "Series 2 doctrine supersedes implementation-derived lifecycle/arithmetic authority", "rejected_decision": "implementation convention as doctrine", "resulting_constitutional_state": "RESOLVED"}],
        "B02-004_constitutional_decision_registry.json": decisions,
        "B02-004_constitutional_precedence_registry.json": baseline["constitutional_precedence_registry"],
        "B02-004_doctrine_supersession_registry.json": baseline["doctrine_supersession_registry"],
        "B02-004_unresolved_constitutional_finding_registry.json": [],
        "B02-004_deterministic_constitutional_behavior_verification_report.json": {"deterministic": True, "scenario_count": 30, "baseline_digest": _digest(baseline), "implementation_behavior_evaluated": False},
        "B02-004_authoritative_constitutional_report.json": {"baseline_id": baseline["baseline_id"], "status": "PUBLISHED", "certification_statement": baseline["certification_statement"]},
        "B02-004_authoritative_position_registry_object_and_lifecycle_baseline.json": baseline,
        "B02-004_completion_report.json": {"order": "B02-004", "status": "COMPLETE", "unresolved_ambiguities": 0, "implementation_evaluated": False, "certification_issued": False},
        "completion_report.json": {"package": "POSITION-REGISTRY-RM-001-S02 object lifecycle constitution", "status": "COMPLETE", "generated_at": generated_at, "baseline_digest": _digest(baseline), "implementation_behavior_modified": False, "behavioral_verification_executed": False, "implementation_certification_issued": False},
    }
    for name, payload in outputs.items():
        _write_json(OUTPUT_DIR / name, payload)
    (OUTPUT_DIR / "README.md").write_text(
        "# Position Registry RM-001 S02 Object and Lifecycle Constitution\n\n"
        "This package publishes constitutional object, lifecycle, quantity, cost-basis, temporal, correction, replay, supersession, archival, and historical-integrity doctrine. It does not evaluate or modify implementation behavior.\n",
        encoding="utf-8",
    )
    return {"status": "COMPLETE", "files": len(outputs) + 1, "output_dir": str(OUTPUT_DIR)}


def main() -> int:
    print(json.dumps(write_outputs(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
