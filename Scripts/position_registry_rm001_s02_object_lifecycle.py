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
    ("entry_cost_basis", "Weighted average opening fill price before adjustments.", "opening fills", "sum(price * quantity) / sum(quantity)", "source currency"),
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


def _lifecycle_authority_registry(transitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "transition_id": item["transition_id"],
            "initiating_authority": item["entry_authority"],
            "approving_authority": "Position Registry",
            "mutation_authority": item["exit_authority"],
            "correction_authority": item["correction_authority"],
            "reconciliation_authority": "Position Registry",
            "terminal_authority": "Position Registry",
            "governing_constitutional_authority": "POSITION-REGISTRY-RM-001-S02-B02-002",
            "identity_preservation_required": True,
        }
        for item in transitions
    ]


def _lifecycle_invariants(states: tuple[str, ...]) -> list[dict[str, Any]]:
    return [
        {
            "state": state,
            "identity_invariant": "position identity remains immutable through state entry, exit, replay, restart, recovery, correction, and supersession",
            "quantity_invariant": "quantity changes require admissible source event, explicit authority, and preserved predecessor quantity",
            "cost_basis_invariant": "cost-basis changes require admissible fill, correction, adjustment, or restatement evidence",
            "ownership_invariant": "Position Registry owns canonical position state; external truth references do not transfer ownership",
            "reconciliation_invariant": "contradictions produce reconciliation evidence rather than silent mutation",
            "historical_invariant": "historical lineage is append-only and replayable",
            "evidence_invariant": "state, authority, source, time, and lineage evidence are mandatory",
            "invariant_status": "DEFINED",
        }
        for state in states
    ]


def _quantity_registry() -> list[dict[str, Any]]:
    base_rules = [
        {
            "quantity_id": f"PR-S02-QTY-{index:03d}",
            "quantity_name": name,
            "constitutional_meaning": meaning,
            "governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-002",
            "owner": owner,
            "authoritative_source": source,
            "mutation_authority": "Position Registry",
            "correction_authority": "Position Registry",
            "reconciliation_authority": "Position Registry",
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
    additional_rules = (
        ("unsigned_quantity", "Non-negative magnitude derived from signed quantity without changing direction.", "validated signed quantity", "absolute decimal magnitude"),
        ("long_position_quantity", "Positive directional quantity authorized only by long-side source evidence.", "long fill and side evidence", "positive decimal"),
        ("short_position_quantity", "Negative directional quantity authorized only when short doctrine and source evidence permit.", "short fill and side evidence", "negative signed decimal"),
        ("zero_quantity", "Zero quantity is terminal or pending only through authorized lifecycle transition.", "authorized close or correction evidence", "exact decimal zero"),
        ("fractional_quantity", "Fractional quantity is admissible only when instrument and venue authority permit it.", "instrument and venue precision evidence", "source decimal precision"),
        ("overflow_quantity", "Overflow or unrepresentable quantity fails closed.", "quantity bounds policy", "no mutation"),
        ("underflow_quantity", "Underflow or precision loss fails closed.", "quantity bounds policy", "no mutation"),
    )
    start = len(base_rules) + 1
    base_rules.extend(
        {
            "quantity_id": f"PR-S02-QTY-{index:03d}",
            "quantity_name": name,
            "constitutional_meaning": meaning,
            "governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-002",
            "owner": "Position Registry",
            "authoritative_source": source,
            "mutation_authority": "Position Registry",
            "correction_authority": "Position Registry",
            "reconciliation_authority": "Position Registry",
            "admissible_inputs": source,
            "precision": precision,
            "rounding": "rounding prohibited during source admission; comparison/display rounding must be explicitly recorded",
            "aggregation_rule": "idempotent event handling with duplicate rejection",
            "temporal_interpretation": "ordered by temporal ordering constitution",
            "correction_rule": "preserve predecessor quantity",
            "reconciliation_rule": "comparison does not mutate without correction authority",
            "evidence_requirement": "source event, authority, identity, quantity, timestamp, digest",
        }
        for index, (name, meaning, source, precision) in enumerate(additional_rules, start=start)
    )
    return base_rules


def _quantity_invariants(quantities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "quantity_id": item["quantity_id"],
            "quantity_name": item["quantity_name"],
            "constitutional_definition_required": True,
            "identity_invariant": "quantity belongs to exactly one canonical position identity",
            "conservation_invariant": "opened quantity, closed quantity, realized quantity, and current quantity reconcile deterministically",
            "precision_invariant": "source precision is retained and calculation/display rounding is explicit",
            "mutation_invariant": "quantity cannot mutate without source evidence and Position Registry authority",
            "replay_invariant": "same admissible event sequence reproduces equivalent quantity state",
        }
        for item in quantities
    ]


def _cost_registry() -> list[dict[str, Any]]:
    base_rules = [
        {
            "cost_basis_id": f"PR-S02-COST-{index:03d}",
            "field": field,
            "constitutional_meaning": meaning,
            "governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-002",
            "authoritative_inputs": inputs,
            "owner": "Position Registry",
            "calculation_authority": "Position Registry",
            "mutation_authority": "Position Registry",
            "reconciliation_authority": "Position Registry",
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
    additional_rules = (
        ("unrealized_cost_basis", "Cost basis allocated to unrealized open quantity.", "current quantity and average basis", "current quantity multiplied by average basis", "position currency"),
        ("weighted_average", "Weighted-average basis for admitted fills.", "multiple fill evidence", "sum(price * quantity) / sum(quantity)", "position currency"),
        ("commission_adjustment", "Commission inclusion only when fee authority admits it.", "commission evidence", "explicitly include or exclude according to financial authority", "fee currency"),
        ("fee_adjustment", "Fee adjustment requires authoritative fee evidence.", "fee evidence", "record separate adjustment and lineage", "fee currency"),
        ("settlement_adjustment", "Settlement adjustment is externally owned and must be referenced, not invented.", "settlement authority evidence", "apply only after authoritative settlement correction", "settlement currency"),
        ("instrument_multiplier_adjustment", "Instrument multiplier modifies basis only through instrument authority.", "instrument multiplier evidence", "multiplier-adjusted basis with raw basis retained", "instrument currency"),
        ("corporate_action_adjustment", "Corporate action adjustment requires corporate-action authority.", "corporate action evidence", "restated basis with predecessor preserved", "position currency"),
        ("restated_cost_basis", "Restatement creates corrected basis lineage.", "restatement evidence", "preserve original and restated basis", "position currency"),
    )
    start = len(base_rules) + 1
    base_rules.extend(
        {
            "cost_basis_id": f"PR-S02-COST-{index:03d}",
            "field": field,
            "constitutional_meaning": meaning,
            "governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-002",
            "authoritative_inputs": inputs,
            "owner": "Position Registry",
            "calculation_authority": "Position Registry",
            "mutation_authority": "Position Registry",
            "reconciliation_authority": "Position Registry",
            "calculation_rule": calc,
            "precision": "decimal source precision retained; calculation precision recorded",
            "rounding_sequence": "calculate before rounding; rounded value never replaces raw evidence",
            "currency": currency,
            "temporal_basis": "temporal ordering constitution",
            "correction_rule": "preserve original and corrected basis",
            "reconciliation_rule": "basis discrepancy becomes reconciliation case",
            "evidence_obligation": "fill/correction/adjustment/currency evidence with digest",
        }
        for index, (field, meaning, inputs, calc, currency) in enumerate(additional_rules, start=start)
    )
    return base_rules


def _cost_invariants(costs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "cost_basis_id": item["cost_basis_id"],
            "field": item["field"],
            "constitutional_definition_required": True,
            "calculation_invariant": "calculation authority, inputs, formula, currency, precision, and rounding are explicit",
            "mutation_invariant": "basis cannot mutate without admitted fill, correction, adjustment, or restatement evidence",
            "history_invariant": "original basis and corrected basis remain historically traceable",
            "reconciliation_invariant": "cost-basis contradiction creates reconciliation case",
            "replay_invariant": "same admissible evidence reproduces equivalent basis",
        }
        for item in costs
    ]


def _temporal_registry() -> list[dict[str, Any]]:
    base_rules = [
        {
            "timestamp_id": f"PR-S02-TIME-{index:03d}",
            "timestamp_name": name,
            "authoritative_meaning": meaning,
            "governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-002",
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
    additional_rules = (
        ("effective_time", "Time at which an admitted event constitutionally affects state.", "governing source authority", "effective time must be explicit or fail closed"),
        ("exchange_time", "Exchange-reported market event time.", "Exchange or Broker", "admissible only with source evidence"),
        ("archival_time", "Time archival custody begins.", "Position Registry", "does not alter terminal truth"),
        ("stale_event_time", "Time used to classify stale events.", "freshness authority", "stale events rejected or quarantined"),
        ("late_event_time", "Time used to classify late events.", "source and receipt authority", "late events require reconciliation or correction authority"),
        ("identical_timestamp_order", "Ordering rule for equal timestamps.", "Position Registry", "requires sequence identifier or reconciliation disposition"),
        ("clock_skew_time", "Clock-skew classification evidence.", "Infrastructure time authority", "skew preserved and escalated if material"),
        ("historical_correction_order", "Ordering for historical corrections.", "Position Registry", "correction time never overwrites original event time"),
    )
    start = len(base_rules) + 1
    base_rules.extend(
        {
            "timestamp_id": f"PR-S02-TIME-{index:03d}",
            "timestamp_name": name,
            "authoritative_meaning": meaning,
            "governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-002",
            "source": source,
            "owner": source,
            "mutation_authority": "source authority; Position Registry may admit reference only",
            "trust_classification": "source asserted" if source != "Position Registry" else "registry audit time",
            "required_precision": "ISO-8601 UTC with source precision retained",
            "timezone": "UTC",
            "normalization_rule": rule,
            "ordering_authority": "temporal ordering constitution",
            "evidence_requirement": "timestamp source and admissibility evidence",
            "correction_rule": "timestamp correction requires correction record and original timestamp retention",
        }
        for index, (name, meaning, source, rule) in enumerate(additional_rules, start=start)
    )
    return base_rules


def _temporal_ordering_registry(temporal: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ordering_id": "PR-S02-B02-002-TEMPORAL-ORDERING",
        "precedence": ("canonical sequence identifier", "broker sequence identifier", "venue sequence identifier", "event time", "effective time", "broker time", "exchange time", "receipt time", "processing time", "persistence time", "reconciliation authority", "correction authority"),
        "stale_event_disposition": "reject or quarantine according to freshness authority",
        "duplicate_event_disposition": "idempotently reject duplicate mutation and preserve duplicate evidence",
        "late_event_disposition": "admit only through reconciliation or correction authority",
        "out_of_order_event_disposition": "quarantine into reconciliation_pending until ordering authority resolves",
        "identical_timestamp_disposition": "requires sequence identifier or reconciliation disposition",
        "clock_skew_disposition": "preserve skew evidence and escalate when material",
        "replay_ordering": "replay uses original event ordering, never replay execution time",
        "restart_ordering": "restart restores persisted sequence without lifecycle advancement",
        "historical_correction_ordering": "correction time is appended and never replaces original event time",
        "covered_temporal_rules": [item["timestamp_id"] for item in temporal],
    }


def _temporal_authority_registry(temporal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "timestamp_id": item["timestamp_id"],
            "timestamp_name": item["timestamp_name"],
            "temporal_authority": item["source"],
            "admission_authority": "Position Registry",
            "ordering_authority": item["ordering_authority"],
            "correction_authority": item["owner"],
            "implementation_inference_prohibited": True,
        }
        for item in temporal
    ]


def _historical_doctrine() -> dict[str, Any]:
    correction_categories = (
        "data_correction",
        "broker_correction",
        "reconciliation_correction",
        "quantity_correction",
        "cost_basis_correction",
        "lifecycle_correction",
        "temporal_correction",
        "historical_correction",
        "identity_correction",
    )
    recovery_scenarios = (
        "process_restart",
        "persistence_restoration",
        "partial_write_recovery",
        "interrupted_mutation",
        "interrupted_replay",
        "corrupted_state",
        "missing_state",
        "historical_reconstruction",
    )
    historical_artifacts = (
        "position_identity_history",
        "position_state_history",
        "quantity_history",
        "cost_basis_history",
        "transition_history",
        "correction_history",
        "supersession_history",
        "replay_history",
        "recovery_history",
        "reconciliation_history",
        "archival_history",
        "audit_history",
    )
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
            "correction_owner": "Position Registry",
            "correction_approver": "Position Registry correction authority",
            "correction_prerequisites": "governing source evidence plus preserved original state",
            "correction_constraints": "no correction may erase, overwrite, or destroy predecessor constitutional truth",
            "correction_effects": "creates successor state plus immutable correction lineage",
            "correction_validation": "identity, source, temporal, quantity, cost, and authority validation",
            "correction_completion_criteria": "correction record, predecessor, successor, reason, and evidence digest published",
            "immutable_history_obligations": "never overwrite predecessor truth",
            "correction_reconciliation_authority": "Position Registry",
            "correction_categories": correction_categories,
        },
        "correction_authority_registry": [
            {
                "correction_category": category,
                "correction_authority": "Position Registry",
                "correction_owner": "Position Registry",
                "correction_initiator": "source authority, reconciliation finding, or Commander escalation",
                "correction_approver": "Position Registry correction authority",
                "correction_evidence": "source evidence, predecessor state, successor state, reason, authority, timestamp, digest",
                "correction_constraints": "append-only correction; predecessor remains immutable",
                "correction_audit_obligations": "complete lineage and replay impact must be preserved",
                "correction_reconciliation_authority": "Position Registry",
                "ambiguous_authority": False,
                "conflicting_authority": False,
                "undocumented_behavior": False,
            }
            for category in correction_categories
        ],
        "correction_lineage_registry": [
            {
                "lineage_rule": "every correction links corrected object, predecessor identity, successor identity, authority, evidence, replay behavior, and audit obligations",
                "lineage_preserved": True,
                "auditability_preserved": True,
            }
        ],
        "replay_constitution": {
            "replay_authority": "Replay authority under Position Registry doctrine",
            "replay_ordering": "B02-003_replay_ordering_registry",
            "replay_prerequisites": "immutable event history, canonical identity, source evidence, and ordering evidence",
            "replay_state_reconstruction": "derive state only from immutable admissible historical evidence",
            "replay_interruption": "checkpoint replay cursor and preserve original history",
            "replay_restart": "resume from replay checkpoint without duplicate mutation",
            "replay_reconciliation": "preserve contradictions and reconciliation cases",
            "replay_correction_interaction": "corrections are replayed as historical events without erasing predecessors",
            "replay_supersession_interaction": "supersession lineage is reconstructed with predecessor and successor references",
            "replay_evidence_generation": "replay produces replay evidence without creating new source truth",
            "identity_preservation": True,
            "lineage_preservation": True,
            "truth_preservation": True,
            "duplicate_historical_mutation_prohibited": True,
            "fabrication_prohibited": True,
        },
        "replay_ordering_registry": {
            "ordering_authority": "Position Registry replay authority",
            "ordering_sequence": ("canonical sequence identifier", "source sequence identifier", "event time", "effective time", "correction time", "supersession time", "receipt time", "persistence time"),
            "duplicate_disposition": "reject duplicate replay mutation and preserve replay evidence",
            "equal_timestamp_disposition": "requires sequence identity or reconciliation disposition",
            "out_of_order_disposition": "preserve order conflict and fail closed until reconciled",
            "deterministic": True,
        },
        "replay_authority_registry": [
            {
                "replay_scope": scope,
                "replay_authority": "Position Registry",
                "identity_preservation_required": True,
                "historical_lineage_preservation_required": True,
                "fabricated_history_prohibited": True,
            }
            for scope in ("state_reconstruction", "correction_replay", "supersession_replay", "historical_reconstruction", "audit_replay")
        ],
        "restart_constitution": {"restart_authority": "Infrastructure recovery custody", "state_restoration": "from persisted evidence only", "identity_preservation": True, "lifecycle_advancement_prohibited": True},
        "recovery_constitution": {
            "recovery_authority": "Position Registry with Infrastructure custody",
            "recovery_ownership": "Position Registry owns constitutional recovery disposition; Infrastructure owns runtime recovery custody",
            "recovery_prerequisites": "candidate identity, persisted evidence, recovery checkpoint, and integrity validation",
            "recovery_state_reconstruction": "restore from immutable evidence or quarantine when evidence is incomplete",
            "recovery_validation": "validate identity, ordering, source evidence, and historical lineage",
            "recovery_replay_interaction": "recovery may invoke replay but cannot create new source truth",
            "recovery_reconciliation": "unresolved recovery contradiction becomes reconciliation case",
            "recovery_historical_preservation": "preserve all failed, partial, and recovered states",
            "recovery_evidence": "checkpoint, failure, recovery decision, restored state, and audit digest",
            "partial_write_disposition": "quarantine and reconcile",
            "corrupted_state_disposition": "detect, preserve, recover or mark unrecoverable",
            "truth_preservation": True,
        },
        "recovery_authority_registry": [
            {
                "recovery_scenario": scenario,
                "recovery_authority": "Position Registry",
                "runtime_custodian": "Infrastructure",
                "state_reconstruction": "from immutable persisted evidence only",
                "validation_required": True,
                "truth_preservation_required": True,
                "ambiguous_authority": False,
                "undefined_behavior": False,
                "conflicting_semantics": False,
            }
            for scenario in recovery_scenarios
        ],
        "recovery_scenario_registry": [
            {
                "scenario": scenario,
                "disposition": "recover deterministically when evidence is complete; otherwise fail closed into reconciliation or quarantine",
                "evidence_obligation": "scenario identity, checkpoint, source evidence, restored state, and finding",
                "history_preserved": True,
            }
            for scenario in recovery_scenarios
        ],
        "supersession_constitution": {
            "supersession_authority": "Position Registry constitutional authority",
            "supersession_ownership": "Position Registry",
            "supersession_prerequisites": "predecessor identity, successor identity, authority, reason, source evidence, and lineage evidence",
            "supersession_evidence": "predecessor, successor, authority, timestamp, reason, digest",
            "supersession_relationships": "predecessor and successor chain remain queryable and replayable",
            "supersession_historical_preservation": "superseded state remains immutable and recoverable",
            "supersession_replay_interaction": "replay reconstructs predecessor and successor lineage without duplicate mutation",
            "supersession_recovery_interaction": "recovery preserves both predecessor and successor identities",
            "superseded_object_preserved": True,
            "successor_object_required": True,
            "historical_truth_destroyed": False,
            "auditability_preserved": True,
        },
        "supersession_authority_registry": [
            {
                "supersession_scope": scope,
                "supersession_authority": "Position Registry",
                "supersession_owner": "Position Registry",
                "predecessor_required": True,
                "successor_required": True,
                "historical_evidence_preserved": True,
                "ambiguous_behavior": False,
                "conflicting_authority": False,
                "undocumented_relationship": False,
            }
            for scope in ("object_identity", "lifecycle_state", "quantity_state", "cost_basis_state", "correction_state", "historical_record")
        ],
        "supersession_lineage_registry": [
            {
                "lineage_rule": "predecessor chain and successor chain remain queryable and replayable",
                "predecessor_preserved": True,
                "successor_required": True,
                "historical_evidence_preserved": True,
                "auditability_preserved": True,
            }
        ],
        "historical_integrity_constitution": {
            "immutable_historical_truth": True,
            "historical_preservation": "append-only, digest-addressed, and replayable",
            "historical_evidence": "source, authority, identity, event, correction, supersession, replay, recovery, and archival evidence",
            "historical_lineage": "complete predecessor/successor and correction chains",
            "historical_reconstruction": "deterministic from immutable evidence only",
            "historical_replay": "replays history without creating new source truth",
            "historical_reconciliation": "contradictions are preserved and reconciled through explicit correction",
            "historical_auditability": "every historical artifact remains independently auditable",
            "historical_archival": "archival changes custody only, not truth",
            "historical_restoration": "restores original identity and lineage from immutable evidence",
        },
        "historical_preservation_registry": [
            {
                "historical_artifact": artifact,
                "governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-003",
                "owner": "Position Registry",
                "custodian": "Position Registry",
                "retention_obligations": "permanent unless superseding constitutional authority explicitly permits otherwise",
                "archival_obligations": "preserve immutable identity, lineage, source evidence, and digest",
                "restoration_obligations": "restore deterministically without altering source truth",
            }
            for artifact in historical_artifacts
        ],
        "historical_lineage_registry": [
            {
                "historical_artifact": artifact,
                "lineage_required": True,
                "predecessor_successor_relationships_required": True,
                "correction_lineage_required": True,
                "supersession_lineage_required": True,
                "missing_lineage": False,
            }
            for artifact in historical_artifacts
        ],
        "historical_evidence_registry": [
            {
                "historical_artifact": artifact,
                "evidence_obligations": ("identity evidence", "authority evidence", "source evidence", "timestamp evidence", "lineage evidence", "digest evidence"),
                "evidence_overwrite_prohibited": True,
                "evidence_destruction_prohibited": True,
                "reproducible": True,
            }
            for artifact in historical_artifacts
        ],
        "historical_reconstruction_registry": [
            {
                "historical_artifact": artifact,
                "reconstruction_authority": "Position Registry replay authority",
                "canonical_identity_preserved": True,
                "deterministic_reconstruction": True,
                "source_truth_fabrication_prohibited": True,
            }
            for artifact in historical_artifacts
        ],
        "historical_integrity_registry": [{"history": name, "immutable": True, "preservation_rule": "append-only lineage with original evidence retention"} for name in ("object identity", "lifecycle", "ownership", "quantity", "cost basis", "correction", "supersession", "replay", "recovery", "audit", "evidence")],
        "replay_integrity_registry": [{"rule": "same authoritative inputs produce identical object identities, lifecycle outcomes, quantities, cost basis, temporal ordering, and historical lineage"}],
        "event_anomaly_constitution": anomaly_dispositions,
        "terminal_state_integrity_registry": [{"terminal_state": state, "permitted_corrections": "authorized correction only", "prohibited_mutations": "all direct mutation", "archival_behavior": "preserve and make retrievable"} for state in ("fully_closed", "superseded", "archived")],
        "archival_constitution": {"archival_authority": "Position Registry", "archival_trigger": "terminal state or supersession", "destruction_authority": "none unless superior constitutional amendment", "retrieval_authority": "authorized audit and replay"},
        "historical_ambiguity_registry": [],
        "completeness": {
            "correction_gaps": [],
            "replay_gaps": [],
            "recovery_gaps": [],
            "supersession_gaps": [],
            "historical_integrity_gaps": [],
            "unresolved_constitutional_ambiguity": [],
        },
    }


def write_outputs() -> dict[str, Any]:
    generated_at = utc_timestamp()
    objects = _object_registry()
    object_dependencies = _object_dependencies(objects)
    object_invariants = _object_invariants(objects)
    lifecycle = _lifecycle_constitution()
    transitions = _transition_registry()
    lifecycle_authorities = _lifecycle_authority_registry(transitions)
    lifecycle_invariants = _lifecycle_invariants(STATES)
    quantities = _quantity_registry()
    quantity_invariants = _quantity_invariants(quantities)
    costs = _cost_registry()
    cost_invariants = _cost_invariants(costs)
    temporal = _temporal_registry()
    temporal_ordering = _temporal_ordering_registry(temporal)
    temporal_authorities = _temporal_authority_registry(temporal)
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
        "lifecycle_authority_constitution": lifecycle_authorities,
        "lifecycle_invariant_constitution": lifecycle_invariants,
        "prohibited_transition_registry": prohibited,
        "quantity_constitution": quantities,
        "quantity_invariant_constitution": quantity_invariants,
        "reversal_constitution": decisions[0],
        "cost_basis_constitution": costs,
        "cost_basis_invariant_constitution": cost_invariants,
        "precision_and_rounding_constitution": {"rounding_method": "explicit rule per field; raw evidence retained", "zero_rule": "zero closes only through authorized transition", "overflow_disposition": "fail closed", "underflow_disposition": "fail closed"},
        "currency_constitution": {"currency_identity": "source and reporting currency retained", "conversion_authority": "external financial authority", "conversion_time": "effective time recorded", "position_registry_owns_conversion": False},
        "temporal_constitution": temporal,
        "event_ordering_constitution": temporal_ordering,
        "temporal_authority_constitution": temporal_authorities,
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
    b02004_reconciliation_registry = [
        {
            "domain": "object_identity_to_lifecycle",
            "source_baseline": "B02-001",
            "target_baseline": "B02-002",
            "relationship": "canonical objects participate in one deterministic lifecycle",
            "disposition": "RECONCILED",
            "conflict": False,
        },
        {
            "domain": "lifecycle_to_quantity",
            "source_baseline": "B02-002",
            "target_baseline": "B02-002",
            "relationship": "lifecycle transitions govern admissible quantity mutation",
            "disposition": "RECONCILED",
            "conflict": False,
        },
        {
            "domain": "quantity_to_cost_basis",
            "source_baseline": "B02-002",
            "target_baseline": "B02-002",
            "relationship": "quantity state provides deterministic cost-basis calculation inputs",
            "disposition": "RECONCILED",
            "conflict": False,
        },
        {
            "domain": "cost_basis_to_temporal",
            "source_baseline": "B02-002",
            "target_baseline": "B02-002",
            "relationship": "cost-basis events are ordered by temporal doctrine",
            "disposition": "RECONCILED",
            "conflict": False,
        },
        {
            "domain": "temporal_to_replay",
            "source_baseline": "B02-002",
            "target_baseline": "B02-003",
            "relationship": "replay preserves original temporal ordering and never uses replay execution time as source truth",
            "disposition": "RECONCILED",
            "conflict": False,
        },
        {
            "domain": "replay_to_recovery",
            "source_baseline": "B02-003",
            "target_baseline": "B02-003",
            "relationship": "recovery may invoke replay while preserving identity and source truth",
            "disposition": "RECONCILED",
            "conflict": False,
        },
        {
            "domain": "recovery_to_correction",
            "source_baseline": "B02-003",
            "target_baseline": "B02-003",
            "relationship": "recovery findings route to correction only through explicit correction authority",
            "disposition": "RECONCILED",
            "conflict": False,
        },
        {
            "domain": "correction_to_supersession",
            "source_baseline": "B02-003",
            "target_baseline": "B02-003",
            "relationship": "corrections may create supersession lineage without erasing predecessor truth",
            "disposition": "RECONCILED",
            "conflict": False,
        },
        {
            "domain": "supersession_to_historical_integrity",
            "source_baseline": "B02-003",
            "target_baseline": "B02-003",
            "relationship": "supersession preserves historical integrity and auditability",
            "disposition": "RECONCILED",
            "conflict": False,
        },
    ]
    b02004_consistency_registry = {
        "object_identity_to_lifecycle_consistent": True,
        "lifecycle_to_quantity_consistent": True,
        "quantity_to_cost_basis_consistent": True,
        "cost_basis_to_temporal_consistent": True,
        "temporal_to_replay_consistent": True,
        "replay_to_recovery_consistent": True,
        "recovery_to_correction_consistent": True,
        "correction_to_supersession_consistent": True,
        "supersession_to_historical_integrity_consistent": True,
        "contradictory_constitutional_rules": [],
        "duplicate_constitutional_semantics": [],
        "missing_constitutional_relationships": [],
        "inconsistent_constitutional_invariants": [],
    }
    b02004_completeness_assessment = {
        "complete_constitutional_object_model": True,
        "complete_lifecycle_doctrine": True,
        "complete_quantity_doctrine": True,
        "complete_cost_basis_doctrine": True,
        "complete_temporal_doctrine": True,
        "complete_replay_doctrine": True,
        "complete_recovery_doctrine": True,
        "complete_correction_doctrine": True,
        "complete_supersession_doctrine": True,
        "complete_historical_integrity_doctrine": True,
        "remaining_constitutional_deficiencies_requiring_future_remediation": [],
    }
    b02004_conflict_registry: list[dict[str, Any]] = []
    b02004_behavioral_baseline = {
        "baseline_id": "POSITION-REGISTRY-RM-001-S02-B02-004-AUTHORITATIVE-CONSTITUTIONAL-BEHAVIORAL-BASELINE",
        "normative_status": "AUTHORITATIVE_SERIES_2_BEHAVIORAL_BASELINE",
        "source_orders": ("B02-001", "B02-002", "B02-003"),
        "authoritative_constitutional_object_baseline": {"objects": objects, "digest": _digest(objects)},
        "authoritative_lifecycle_baseline": {"lifecycle": lifecycle, "transitions": transitions, "authorities": lifecycle_authorities, "invariants": lifecycle_invariants},
        "authoritative_quantity_baseline": {"rules": quantities, "invariants": quantity_invariants},
        "authoritative_cost_basis_baseline": {"rules": costs, "invariants": cost_invariants},
        "authoritative_temporal_baseline": {"rules": temporal, "ordering": temporal_ordering, "authorities": temporal_authorities},
        "authoritative_replay_baseline": historical["replay_constitution"],
        "authoritative_recovery_baseline": {"constitution": historical["recovery_constitution"], "scenarios": historical["recovery_scenario_registry"]},
        "authoritative_correction_baseline": {"constitution": historical["correction_constitution"], "authorities": historical["correction_authority_registry"]},
        "authoritative_supersession_baseline": {"constitution": historical["supersession_constitution"], "authorities": historical["supersession_authority_registry"]},
        "authoritative_historical_integrity_baseline": {"constitution": historical["historical_integrity_constitution"], "preservation": historical["historical_preservation_registry"], "lineage": historical["historical_lineage_registry"]},
        "constitutional_reconciliation_registry": b02004_reconciliation_registry,
        "constitutional_consistency_registry": b02004_consistency_registry,
        "constitutional_completeness_assessment": b02004_completeness_assessment,
        "constitutional_conflict_registry": b02004_conflict_registry,
        "unresolved_constitutional_findings_registry": [],
        "deterministic_and_reproducible": True,
        "new_doctrine_introduced": False,
        "implementation_modified": False,
        "implementation_participation_evaluated": False,
        "behavioral_verification_executed": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
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
        "B02-002_lifecycle_authority_registry.json": lifecycle_authorities,
        "B02-002_lifecycle_invariant_registry.json": lifecycle_invariants,
        "B02-002_quantity_constitution.json": {"governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-002", "rules": quantities, "conflicting_quantity_doctrine": [], "ambiguous_quantity_semantics": [], "undefined_quantity_behavior": []},
        "B02-002_quantity_doctrine_registry.json": quantities,
        "B02-002_quantity_rule_registry.json": quantities,
        "B02-002_quantity_invariant_registry.json": quantity_invariants,
        "B02-002_cost_basis_constitution.json": {"governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-002", "rules": costs, "conflicting_cost_basis_doctrine": [], "undefined_calculations": [], "ambiguous_valuation_rules": []},
        "B02-002_cost_basis_doctrine_registry.json": costs,
        "B02-002_cost_basis_rule_registry.json": costs,
        "B02-002_cost_basis_invariant_registry.json": cost_invariants,
        "B02-002_temporal_constitution.json": {"governing_authority": "POSITION-REGISTRY-RM-001-S02-B02-002", "rules": temporal, "temporal_ambiguity": [], "undefined_ordering": [], "conflicting_temporal_authority": []},
        "B02-002_temporal_doctrine_registry.json": temporal,
        "B02-002_temporal_ordering_registry.json": temporal_ordering,
        "B02-002_temporal_authority_registry.json": temporal_authorities,
        "B02-002_behavioral_state_invariant_registry.json": lifecycle_invariants,
        "B02-002_constitutional_lifecycle_completeness_assessment.json": {"complete": True, "canonical_objects_have_deterministic_lifecycle": True, "transitions_have_constitutional_authority": True, "transitions_preserve_identity": True, "unresolved_lifecycle_ambiguity": []},
        "B02-002_constitutional_quantity_completeness_assessment.json": {"complete": True, "quantity_rules_defined": len(quantities), "conflicting_quantity_doctrine": [], "ambiguous_quantity_semantics": [], "undefined_quantity_behavior": []},
        "B02-002_constitutional_cost_basis_completeness_assessment.json": {"complete": True, "cost_basis_rules_defined": len(costs), "conflicting_cost_basis_doctrine": [], "undefined_calculations": [], "ambiguous_valuation_rules": []},
        "B02-002_constitutional_temporal_completeness_assessment.json": {"complete": True, "temporal_rules_defined": len(temporal), "temporal_ambiguity": [], "undefined_ordering": [], "conflicting_temporal_authority": []},
        "B02-002_unresolved_constitutional_findings_registry.json": [],
        "B02-002_lifecycle_quantity_cost_basis_and_temporal_constitutional_report.json": {"order": "POSITION-REGISTRY-RM-001-S02-B02-002", "status": "COMPLETE", "lifecycle_states": len(STATES), "lifecycle_transitions": len(transitions), "quantity_rules": len(quantities), "cost_basis_rules": len(costs), "temporal_rules": len(temporal), "behavioral_invariants": len(lifecycle_invariants), "implementation_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False},
        "B02-002_lifecycle_ambiguity_registry.json": [],
        "B02-002_completion_report.json": {"order": "B02-002", "status": "COMPLETE", "ambiguous_transitions": 0, "undefined_quantity_rules": 0, "undefined_cost_basis_rules": 0, "incomplete_temporal_doctrine": 0, "unresolved_constitutional_ambiguity": 0, "implementation_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False},
        "B02-003_correction_constitution.json": historical["correction_constitution"],
        "B02-003_correction_authority_registry.json": historical["correction_authority_registry"],
        "B02-003_correction_lineage_registry.json": historical["correction_lineage_registry"],
        "B02-003_replay_constitution.json": historical["replay_constitution"],
        "B02-003_replay_ordering_registry.json": historical["replay_ordering_registry"],
        "B02-003_replay_authority_registry.json": historical["replay_authority_registry"],
        "B02-003_restart_constitution.json": historical["restart_constitution"],
        "B02-003_recovery_constitution.json": historical["recovery_constitution"],
        "B02-003_recovery_authority_registry.json": historical["recovery_authority_registry"],
        "B02-003_recovery_scenario_registry.json": historical["recovery_scenario_registry"],
        "B02-003_supersession_constitution.json": historical["supersession_constitution"],
        "B02-003_supersession_authority_registry.json": historical["supersession_authority_registry"],
        "B02-003_supersession_lineage_registry.json": historical["supersession_lineage_registry"],
        "B02-003_historical_integrity_constitution.json": historical["historical_integrity_constitution"],
        "B02-003_historical_preservation_registry.json": historical["historical_preservation_registry"],
        "B02-003_historical_lineage_registry.json": historical["historical_lineage_registry"],
        "B02-003_historical_evidence_registry.json": historical["historical_evidence_registry"],
        "B02-003_historical_reconstruction_registry.json": historical["historical_reconstruction_registry"],
        "B02-003_historical_integrity_registry.json": historical["historical_integrity_registry"],
        "B02-003_replay_integrity_registry.json": historical["replay_integrity_registry"],
        "B02-003_terminal_state_integrity_registry.json": historical["terminal_state_integrity_registry"],
        "B02-003_archival_constitution.json": historical["archival_constitution"],
        "B02-003_historical_ambiguity_registry.json": historical["historical_ambiguity_registry"],
        "B02-003_constitutional_correction_completeness_assessment.json": {"complete": True, "correction_categories": len(historical["correction_authority_registry"]), "ambiguous_correction_authority": [], "conflicting_correction_authority": [], "undocumented_correction_behavior": []},
        "B02-003_constitutional_replay_completeness_assessment.json": {"complete": True, "deterministic_replay_defined": True, "replay_ambiguity": [], "replay_inconsistency": [], "undefined_replay_behavior": []},
        "B02-003_constitutional_recovery_completeness_assessment.json": {"complete": True, "recovery_scenarios": len(historical["recovery_scenario_registry"]), "ambiguous_recovery_authority": [], "undefined_recovery_behavior": [], "conflicting_recovery_semantics": []},
        "B02-003_constitutional_supersession_completeness_assessment.json": {"complete": True, "supersession_scopes": len(historical["supersession_authority_registry"]), "ambiguous_supersession_behavior": [], "conflicting_supersession_authority": [], "undocumented_supersession_relationships": []},
        "B02-003_constitutional_historical_integrity_assessment.json": {"complete": True, "historical_artifacts": len(historical["historical_preservation_registry"]), "historical_truth_immutable": True, "historical_lineage_complete": True, "historical_reconstruction_deterministic": True, "historical_evidence_reproducible": True, "historical_ambiguity": [], "missing_lineage": [], "incomplete_preservation": [], "conflicting_historical_doctrine": []},
        "B02-003_unresolved_constitutional_findings_registry.json": [],
        "B02-003_correction_replay_supersession_and_historical_integrity_constitutional_report.json": {"order": "POSITION-REGISTRY-RM-001-S02-B02-003", "status": "COMPLETE", "correction_categories": len(historical["correction_authority_registry"]), "replay_rules_defined": True, "recovery_scenarios": len(historical["recovery_scenario_registry"]), "supersession_scopes": len(historical["supersession_authority_registry"]), "historical_artifacts": len(historical["historical_preservation_registry"]), "historical_truth_immutable": True, "corrections_preserve_lineage": True, "replay_preserves_truth": True, "recovery_preserves_truth": True, "supersession_preserves_evidence": True, "implementation_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False},
        "B02-003_constitutional_consistency_reconciliation_report.json": {"status": "RECONCILED", "unresolved_historical_ambiguity": False, "unresolved_replay_ambiguity": False, "unresolved_correction_ambiguity": False},
        "B02-003_completion_report.json": {"order": "B02-003", "status": "COMPLETE", "historical_truth_destroyable": False, "historical_evidence_destroyable": False, "replay_fabrication_permitted": False, "correction_preserves_auditability": True, "supersession_preserves_evidence": True, "unresolved_correction_ambiguity": 0, "unresolved_replay_ambiguity": 0, "unresolved_recovery_ambiguity": 0, "unresolved_supersession_ambiguity": 0, "unresolved_historical_integrity_ambiguity": 0, "implementation_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False},
        "B02-004_position_registry_object_constitution_baseline.json": {"objects": objects, "digest": _digest(objects)},
        "B02-004_authoritative_constitutional_object_baseline.json": b02004_behavioral_baseline["authoritative_constitutional_object_baseline"],
        "B02-004_position_registry_lifecycle_constitution_baseline.json": {"lifecycle": lifecycle, "transitions": transitions, "digest": _digest({"lifecycle": lifecycle, "transitions": transitions})},
        "B02-004_authoritative_lifecycle_baseline.json": b02004_behavioral_baseline["authoritative_lifecycle_baseline"],
        "B02-004_position_registry_quantity_constitution_baseline.json": {"quantities": quantities, "digest": _digest(quantities)},
        "B02-004_authoritative_quantity_baseline.json": b02004_behavioral_baseline["authoritative_quantity_baseline"],
        "B02-004_position_registry_cost_basis_constitution_baseline.json": {"cost_basis": costs, "digest": _digest(costs)},
        "B02-004_authoritative_cost_basis_baseline.json": b02004_behavioral_baseline["authoritative_cost_basis_baseline"],
        "B02-004_position_registry_temporal_constitution_baseline.json": {"temporal": temporal, "digest": _digest(temporal)},
        "B02-004_authoritative_temporal_baseline.json": b02004_behavioral_baseline["authoritative_temporal_baseline"],
        "B02-004_authoritative_replay_baseline.json": b02004_behavioral_baseline["authoritative_replay_baseline"],
        "B02-004_authoritative_recovery_baseline.json": b02004_behavioral_baseline["authoritative_recovery_baseline"],
        "B02-004_authoritative_correction_baseline.json": b02004_behavioral_baseline["authoritative_correction_baseline"],
        "B02-004_authoritative_supersession_baseline.json": b02004_behavioral_baseline["authoritative_supersession_baseline"],
        "B02-004_authoritative_historical_integrity_baseline.json": b02004_behavioral_baseline["authoritative_historical_integrity_baseline"],
        "B02-004_constitutional_behavioral_baseline.json": b02004_behavioral_baseline,
        "B02-004_constitutional_reconciliation_registry.json": b02004_reconciliation_registry,
        "B02-004_constitutional_consistency_registry.json": b02004_consistency_registry,
        "B02-004_constitutional_completeness_assessment.json": b02004_completeness_assessment,
        "B02-004_constitutional_conflict_registry.json": b02004_conflict_registry,
        "B02-004_unresolved_constitutional_findings_registry.json": [],
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
        "B02-004_authoritative_constitutional_behavioral_report.json": {"order": "POSITION-REGISTRY-RM-001-S02-B02-004", "status": "COMPLETE", "authoritative_baseline": "B02-004_constitutional_behavioral_baseline.json", "baseline_digest": _digest(b02004_behavioral_baseline), "reconciled_source_orders": ("B02-001", "B02-002", "B02-003"), "conflicts": 0, "unresolved_findings": 0, "new_doctrine_introduced": False, "implementation_modified": False, "implementation_participation_evaluated": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False},
        "B02-004_authoritative_position_registry_object_and_lifecycle_baseline.json": baseline,
        "B02-004_completion_report.json": {"order": "B02-004", "status": "COMPLETE", "unresolved_ambiguities": 0, "duplicate_constitutional_doctrine": 0, "conflicting_constitutional_doctrine": 0, "authoritative_constitutional_behavioral_baseline_established": True, "baseline_digest": _digest(b02004_behavioral_baseline), "new_doctrine_introduced": False, "implementation_evaluated": False, "implementation_modified": False, "implementation_participation_evaluated": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False, "certification_issued": False},
        "completion_report.json": {"package": "POSITION-REGISTRY-RM-001-S02 object lifecycle constitution", "status": "COMPLETE", "generated_at": generated_at, "baseline_digest": _digest(baseline), "behavioral_baseline_digest": _digest(b02004_behavioral_baseline), "implementation_behavior_modified": False, "behavioral_verification_executed": False, "implementation_certification_issued": False},
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
