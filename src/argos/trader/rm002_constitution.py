"""Executable RM-002 constitutional closure records for the Trader Office."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence


TRADER_RM_002_VERSION = "TRADER-RM-002/1.0.0"


class TraderRM002Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class RM002Decision:
    status: TraderRM002Status
    findings: tuple[str, ...]


@dataclass(frozen=True)
class ConstitutionalObject:
    identifier: str
    classification: str
    owner: str
    creator: str
    custodian: str
    terminal_custodian: str
    mutation_authority: str
    reconciliation_authority: str
    evidence: tuple[str, ...]
    lifecycle: str
    certification_rules: tuple[str, ...]
    external: bool = False


@dataclass(frozen=True)
class LifecycleSpec:
    identifier: str
    owner: str
    states: tuple[str, ...]
    permitted_transitions: tuple[tuple[str, str], ...]
    prohibited_transitions: tuple[tuple[str, str], ...]
    terminal_states: tuple[str, ...]
    required_evidence: tuple[str, ...]
    recovery_behavior: str
    replay_behavior: str


@dataclass(frozen=True)
class ConstitutionalRule:
    identifier: str
    classification: str
    doctrine: str
    objects: tuple[str, ...]
    verification_classes: tuple[str, ...]
    evidence: tuple[str, ...]
    certification_status: str


AUTHORITY_PRECEDENCE: tuple[str, ...] = (
    "Enterprise Constitutional Laws",
    "Enterprise Constitutional Governance Policy",
    "Enterprise Object Constitution",
    "Enterprise Ownership Doctrine",
    "ECS-003",
    "Canonical Trader Office Constitution",
    "TRADER-RM-001",
    "TRADER-GOV-001-012",
    "TRADER-RM-002-001-016",
)


DOCTRINE_SUPERSESSION_REGISTER: Mapping[str, str] = {
    "TRADER-RM-001": "retained with normalization",
    "TRADER-GOV-001": "incorporated",
    "TRADER-GOV-002": "incorporated",
    "TRADER-GOV-006": "incorporated",
    "TRADER-GOV-008": "incorporated",
    "TRADER-GOV-009": "incorporated",
    "TRADER-GOV-010": "incorporated",
    "TRADER-GOV-011": "incorporated",
    "TRADER-GOV-012": "incorporated",
    "TRADER-RM-002-001": "retained without modification",
    "TRADER-RM-002-002": "retained without modification",
    "TRADER-RM-002-003": "retained without modification",
    "TRADER-RM-002-004": "retained without modification",
    "TRADER-RM-002-005": "retained without modification",
    "TRADER-RM-002-006": "retained without modification",
    "TRADER-RM-002-007": "retained without modification",
    "TRADER-RM-002-008": "retained without modification",
    "TRADER-RM-002-009": "retained without modification",
    "TRADER-RM-002-010": "retained without modification",
    "TRADER-RM-002-011": "retained without modification",
    "TRADER-RM-002-012": "retained without modification",
    "TRADER-RM-002-013": "retained without modification",
    "TRADER-RM-002-014": "retained without modification",
    "TRADER-RM-002-015": "retained without modification",
    "TRADER-RM-002-016": "retained without modification",
}


SUBORDINATE_OFFICE_AUTHORITY: Mapping[str, Mapping[str, str]] = {
    "Trade Execution Office": {"purpose": "execution planning and submission coordination", "owner": "Trader Office", "prohibited": "investment intent creation"},
    "Broker Integration Office": {"purpose": "broker communication and broker-event normalization", "owner": "Trader Office", "prohibited": "canonical state mutation without reconciliation"},
    "Order Management Office": {"purpose": "canonical order lifecycle accounting", "owner": "Trader Office", "prohibited": "broker truth ownership"},
    "Position Management Office": {"purpose": "position lifecycle recognition", "owner": "Trader Office", "prohibited": "financial account truth ownership"},
    "Trade Monitoring Office": {"purpose": "alert detection and escalation", "owner": "Trader Office", "prohibited": "corrective action without authority"},
    "Execution Quality Office": {"purpose": "execution quality assessment", "owner": "Trader Office", "prohibited": "execution outcome mutation"},
    "Trader Fusion Office": {"purpose": "evidence conflict assessment", "owner": "Trader Office", "prohibited": "synthetic evidence creation"},
}


TRADER_RM002_OBJECTS: Mapping[str, ConstitutionalObject] = {
    "Investment Intent": ConstitutionalObject("TRADER-OBJ-001", "Authority Object", "Executive Authority", "Executive Authority", "Trader Office", "Historian Office", "Executive Authority", "Executive Authority", ("Investment Intent reference",), "External Authority Lifecycle", ("TRADER-RULE-001",), True),
    "Authorization": ConstitutionalObject("TRADER-OBJ-002", "Authority Object", "Authorizations Office", "Authorizations Office", "Trader Office", "Historian Office", "Authorizations Office", "Authorizations Office", ("Authorization validation evidence",), "Authority Consumption Lifecycle", ("TRADER-RULE-002",), True),
    "Risk Certificate": ConstitutionalObject("TRADER-OBJ-003", "Authority Object", "Risk Office", "Risk Office", "Trader Office", "Historian Office", "Risk Office", "Risk Office", ("Risk validation evidence",), "Authority Consumption Lifecycle", ("TRADER-RULE-003",), True),
    "Operating Mode Authority": ConstitutionalObject("TRADER-OBJ-004", "Authority Object", "Commander", "Commander", "Trader Office", "Historian Office", "Commander", "Commander", ("Mode authority evidence",), "Authority Consumption Lifecycle", ("TRADER-RULE-004",), True),
    "Execution Mandate": ConstitutionalObject("TRADER-OBJ-005", "Planning Object", "Trader Office", "Trader Office", "Trader Office", "Historian Office", "Trader Office", "Trader Office", ("mandate creation", "mandate validation", "authority lineage"), "Execution Mandate Lifecycle", ("TRADER-RULE-005",)),
    "Execution Plan": ConstitutionalObject("TRADER-OBJ-006", "Planning Object", "Trader Office", "Trader Office", "Trader Office", "Historian Office", "Trader Office", "Trader Office", ("plan approval", "plan revision history"), "Execution Plan Lifecycle", ("TRADER-RULE-006",)),
    "Canonical Order": ConstitutionalObject("TRADER-OBJ-007", "Execution Object", "Trader Office", "Trader Office", "Trader Office", "Historian Office", "Trader Office", "Trader Office", ("order creation", "order transition history"), "Canonical Order Lifecycle", ("TRADER-RULE-007",)),
    "Broker Submission Request": ConstitutionalObject("TRADER-OBJ-008", "Communication Object", "Trader Office", "Trader Office", "Broker Integration Office", "Historian Office", "Trader Office", "Trader Office", ("submission evidence", "idempotency evidence"), "Broker Submission Request Lifecycle", ("TRADER-RULE-008",)),
    "Broker Communication Record": ConstitutionalObject("TRADER-OBJ-009", "Communication Object", "Trader Office", "Broker Integration Office", "Broker Integration Office", "Historian Office", "Trader Office", "Trader Office", ("payload digest", "transmission evidence"), "Broker Communication Lifecycle", ("TRADER-RULE-009",)),
    "Broker Event": ConstitutionalObject("TRADER-OBJ-010", "Execution Object", "External Broker Authority", "External Broker Authority", "Broker Integration Office", "Historian Office", "External Broker Authority", "Trader Office", ("broker event evidence", "correlation evidence"), "Broker Event Lifecycle", ("TRADER-RULE-010",), True),
    "Canonical Fill Record": ConstitutionalObject("TRADER-OBJ-011", "Market Truth Object", "Trader Office", "Trader Office", "Trader Office", "Historian Office", "Trader Office", "Trader Office", ("fill validation", "quantity reconciliation"), "Fill Lifecycle", ("TRADER-RULE-011",)),
    "Canonical Position": ConstitutionalObject("TRADER-OBJ-012", "Execution Object", "Position Management Office", "Position Management Office", "Trader Office", "Historian Office", "Position Management Office", "Position Management Office", ("position transition evidence",), "Position Lifecycle", ("TRADER-RULE-012",)),
    "Financial Resource Admissibility Record": ConstitutionalObject("TRADER-OBJ-013", "Financial Dependency Object", "Trader Office", "Trader Office", "Trader Office", "Historian Office", "Trader Office", "Trader Office", ("financial authority evidence", "freshness evidence"), "Financial Resource Admissibility Lifecycle", ("TRADER-RULE-013",)),
    "Reconciliation Object": ConstitutionalObject("TRADER-OBJ-014", "Reconciliation Object", "Trader Office", "Trader Office", "Trader Office", "Historian Office", "Trader Office", "Trader Office", ("discrepancy evidence", "resolution evidence"), "Reconciliation Lifecycle", ("TRADER-RULE-014",)),
    "Monitoring Alert": ConstitutionalObject("TRADER-OBJ-015", "Monitoring Object", "Trade Monitoring Office", "Trade Monitoring Office", "Trade Monitoring Office", "Historian Office", "Trade Monitoring Office", "Trade Monitoring Office", ("alert classification", "escalation evidence"), "Monitoring Alert Lifecycle", ("TRADER-RULE-015",)),
    "Fusion Assessment": ConstitutionalObject("TRADER-OBJ-016", "Monitoring Object", "Trader Fusion Office", "Trader Fusion Office", "Trader Fusion Office", "Historian Office", "Trader Fusion Office", "Trader Fusion Office", ("source correlation", "conflict preservation"), "Fusion Assessment Lifecycle", ("TRADER-RULE-016",)),
    "Emergency Action Record": ConstitutionalObject("TRADER-OBJ-017", "Lifecycle Object", "Trader Office", "Trader Office", "Trader Office", "Historian Office", "Commander", "Trader Office", ("emergency authority", "protective action evidence"), "Emergency Action Lifecycle", ("TRADER-RULE-017",)),
    "Trader Execution Case File": ConstitutionalObject("TRADER-OBJ-018", "Evidence Object", "Trader Office", "Trader Office", "Trader Office", "Historian Office", "Trader Office", "Trader Office", ("authority evidence", "planning evidence", "execution evidence", "financial evidence", "monitoring evidence", "completion evidence"), "Trader Execution Case File Lifecycle", ("TRADER-RULE-018",)),
    "Historian Custody Acknowledgement": ConstitutionalObject("TRADER-OBJ-019", "Custody Object", "Historian Office", "Historian Office", "Trader Office", "Historian Office", "Historian Office", "Historian Office", ("custody acknowledgement",), "Historian Custody Transfer Lifecycle", ("TRADER-RULE-019",), True),
}


TRADER_RM002_LIFECYCLES: Mapping[str, LifecycleSpec] = {
    "Execution Mandate Lifecycle": LifecycleSpec("TRADER-LC-001", "Trader Office", ("Proposed", "Validated", "Authorized", "Activated", "Suspended", "Revoked", "Expired", "Completed", "Failed", "Archived"), (("Proposed", "Validated"), ("Validated", "Authorized"), ("Authorized", "Activated"), ("Activated", "Suspended"), ("Suspended", "Activated"), ("Activated", "Completed"), ("Activated", "Revoked"), ("Activated", "Expired"), ("Activated", "Failed"), ("Completed", "Archived"), ("Revoked", "Archived"), ("Expired", "Archived"), ("Failed", "Archived")), (), ("Archived",), ("authority lineage", "validation evidence"), "resume from last evidenced non-terminal state", "identical evidence yields identical state"),
    "Execution Plan Lifecycle": LifecycleSpec("TRADER-LC-002", "Trader Office", ("Draft", "Pending Approval", "Approved", "Active", "Suspended", "Replaced", "Completed", "Expired", "Cancelled", "Archived"), (("Draft", "Pending Approval"), ("Pending Approval", "Approved"), ("Approved", "Active"), ("Active", "Suspended"), ("Suspended", "Active"), ("Active", "Replaced"), ("Active", "Completed"), ("Active", "Expired"), ("Active", "Cancelled"), ("Completed", "Archived"), ("Expired", "Archived"), ("Cancelled", "Archived"), ("Replaced", "Archived")), (), ("Archived",), ("plan approval", "mandate validity"), "recover by mandate and plan version", "version lineage determines state"),
    "Canonical Order Lifecycle": LifecycleSpec("TRADER-LC-003", "Trader Office", ("Draft", "Validated", "Approved", "Ready", "Submitted", "Acknowledged", "Partially Filled", "Filled", "Cancel Pending", "Cancelled", "Replace Pending", "Replaced", "Expired", "Rejected", "Failed", "Closed", "Archived"), (("Draft", "Validated"), ("Validated", "Approved"), ("Approved", "Ready"), ("Ready", "Submitted"), ("Submitted", "Acknowledged"), ("Acknowledged", "Partially Filled"), ("Acknowledged", "Filled"), ("Partially Filled", "Filled"), ("Acknowledged", "Cancel Pending"), ("Cancel Pending", "Cancelled"), ("Acknowledged", "Replace Pending"), ("Replace Pending", "Replaced"), ("Acknowledged", "Expired"), ("Submitted", "Rejected"), ("Submitted", "Failed"), ("Filled", "Closed"), ("Cancelled", "Closed"), ("Expired", "Closed"), ("Rejected", "Closed"), ("Failed", "Closed"), ("Closed", "Archived")), (("Filled", "Submitted"), ("Cancelled", "Active"), ("Rejected", "Filled")), ("Archived",), ("order transition evidence",), "reconcile broker state before advancing", "transition matrix is deterministic"),
    "Broker Submission Request Lifecycle": LifecycleSpec("TRADER-LC-004", "Trader Office", ("Constructed", "Validated", "Ready", "Transmitted", "Awaiting Response", "Acknowledged", "Timed Out", "Retry Pending", "Resolved", "Failed", "Archived"), (("Constructed", "Validated"), ("Validated", "Ready"), ("Ready", "Transmitted"), ("Transmitted", "Awaiting Response"), ("Awaiting Response", "Acknowledged"), ("Awaiting Response", "Timed Out"), ("Timed Out", "Retry Pending"), ("Retry Pending", "Transmitted"), ("Acknowledged", "Resolved"), ("Resolved", "Archived"), ("Failed", "Archived")), (), ("Archived",), ("idempotency key", "transmission evidence"), "retry with original idempotency key", "duplicate transmissions preserve one intent"),
    "Broker Communication Lifecycle": LifecycleSpec("TRADER-LC-004A", "Broker Integration Office", ("Generated", "Queued", "Sent", "Delivered", "Acknowledged", "Failed", "Retried", "Completed", "Archived"), (("Generated", "Queued"), ("Queued", "Sent"), ("Sent", "Delivered"), ("Delivered", "Acknowledged"), ("Sent", "Failed"), ("Failed", "Retried"), ("Retried", "Sent"), ("Acknowledged", "Completed"), ("Completed", "Archived")), (), ("Archived",), ("payload digest", "transmission evidence"), "retry without deleting prior communication", "communication identity governs replay"),
    "Broker Event Lifecycle": LifecycleSpec("TRADER-LC-005", "Broker Integration Office", ("Received", "Validated", "Correlated", "Accepted", "Rejected", "Duplicate", "Reconciled", "Archived"), (("Received", "Validated"), ("Validated", "Correlated"), ("Correlated", "Accepted"), ("Correlated", "Rejected"), ("Correlated", "Duplicate"), ("Accepted", "Reconciled"), ("Rejected", "Archived"), ("Duplicate", "Archived"), ("Reconciled", "Archived")), (), ("Archived",), ("broker event evidence", "correlation evidence"), "preserve out-of-order evidence", "arrival order alone never controls state"),
    "Fill Lifecycle": LifecycleSpec("TRADER-LC-006", "Trader Office", ("Reported", "Pending Validation", "Validated", "Applied", "Corrected", "Reversed", "Finalized", "Archived"), (("Reported", "Pending Validation"), ("Pending Validation", "Validated"), ("Validated", "Applied"), ("Applied", "Corrected"), ("Applied", "Reversed"), ("Applied", "Finalized"), ("Corrected", "Finalized"), ("Reversed", "Finalized"), ("Finalized", "Archived")), (), ("Archived",), ("fill validation", "quantity reconciliation"), "replay fill identity before apply", "duplicate fills cannot double apply"),
    "Position Lifecycle": LifecycleSpec("TRADER-LC-007", "Position Management Office", ("Opening", "Open", "Increasing", "Decreasing", "Fully Closed", "Corrected", "Reconciled", "Archived"), (("Opening", "Open"), ("Open", "Increasing"), ("Open", "Decreasing"), ("Increasing", "Open"), ("Decreasing", "Open"), ("Decreasing", "Fully Closed"), ("Open", "Corrected"), ("Corrected", "Reconciled"), ("Fully Closed", "Archived"), ("Reconciled", "Archived")), (), ("Archived",), ("position transition evidence",), "recover from last reconciled position", "fills deterministically derive position"),
    "Financial Resource Admissibility Lifecycle": LifecycleSpec("TRADER-LC-008", "Trader Office", ("Requested", "Pending Validation", "Verified", "Reserved", "Consumed", "Released", "Expired", "Invalid", "Archived"), (("Requested", "Pending Validation"), ("Pending Validation", "Verified"), ("Verified", "Reserved"), ("Reserved", "Consumed"), ("Reserved", "Released"), ("Verified", "Expired"), ("Pending Validation", "Invalid"), ("Consumed", "Archived"), ("Released", "Archived"), ("Expired", "Archived"), ("Invalid", "Archived")), (), ("Archived",), ("financial authority evidence", "freshness evidence"), "fail closed if financial authority unavailable", "external financial truth prevails"),
    "Reconciliation Lifecycle": LifecycleSpec("TRADER-LC-009", "Trader Office", ("Discrepancy Detected", "Investigation", "Awaiting Evidence", "Decision Pending", "Corrected", "Accepted", "Escalated", "Closed", "Archived"), (("Discrepancy Detected", "Investigation"), ("Investigation", "Awaiting Evidence"), ("Awaiting Evidence", "Decision Pending"), ("Decision Pending", "Corrected"), ("Decision Pending", "Accepted"), ("Decision Pending", "Escalated"), ("Corrected", "Closed"), ("Accepted", "Closed"), ("Escalated", "Closed"), ("Closed", "Archived")), (), ("Archived",), ("discrepancy evidence", "resolution evidence"), "resume at decision pending with preserved evidence", "same evidence produces same disposition"),
    "Monitoring Alert Lifecycle": LifecycleSpec("TRADER-LC-010", "Trade Monitoring Office", ("Created", "Classified", "Assigned", "Acknowledged", "Active Investigation", "Escalated", "Resolution Pending", "Resolved", "Closed", "Archived"), (("Created", "Classified"), ("Classified", "Assigned"), ("Assigned", "Acknowledged"), ("Acknowledged", "Active Investigation"), ("Active Investigation", "Escalated"), ("Active Investigation", "Resolution Pending"), ("Escalated", "Resolution Pending"), ("Resolution Pending", "Resolved"), ("Resolved", "Closed"), ("Closed", "Archived")), (), ("Archived",), ("alert classification", "terminal disposition"), "escalate on missed deadlines", "severity determines response"),
    "Fusion Assessment Lifecycle": LifecycleSpec("TRADER-LC-011", "Trader Fusion Office", ("Created", "Awaiting Sources", "Correlated", "Conflict Detected", "Resolution Pending", "Resolved", "Archived"), (("Created", "Awaiting Sources"), ("Awaiting Sources", "Correlated"), ("Correlated", "Conflict Detected"), ("Conflict Detected", "Resolution Pending"), ("Correlated", "Resolved"), ("Resolution Pending", "Resolved"), ("Resolved", "Archived")), (), ("Archived",), ("source correlation", "conflict preservation"), "preserve unresolved conflicts", "no synthetic evidence"),
    "Emergency Action Lifecycle": LifecycleSpec("TRADER-LC-012", "Trader Office", ("Requested", "Authorized", "Active", "Executing", "Verified", "Completed", "Failed", "Archived"), (("Requested", "Authorized"), ("Authorized", "Active"), ("Active", "Executing"), ("Executing", "Verified"), ("Verified", "Completed"), ("Executing", "Failed"), ("Completed", "Archived"), ("Failed", "Archived")), (), ("Archived",), ("emergency authority", "protective action evidence"), "safest permitted state on uncertainty", "authority precedence controls conflicts"),
    "Trader Execution Case File Lifecycle": LifecycleSpec("TRADER-LC-013", "Trader Office", ("Created", "Collecting Evidence", "Pending Completion", "Complete", "Pending Historian Transfer", "Delivered", "Acknowledged", "Archived"), (("Created", "Collecting Evidence"), ("Collecting Evidence", "Pending Completion"), ("Pending Completion", "Complete"), ("Complete", "Pending Historian Transfer"), ("Pending Historian Transfer", "Delivered"), ("Delivered", "Acknowledged"), ("Acknowledged", "Archived")), (), ("Archived",), ("authority evidence", "execution evidence", "completion evidence"), "remain pending custody until acknowledged", "case file manifest controls replay"),
    "Historian Custody Transfer Lifecycle": LifecycleSpec("TRADER-LC-014", "Trader Office", ("Pending Transfer", "Delivery Initiated", "Delivery In Progress", "Receipt Pending", "Accepted", "Rejected", "Retry Pending", "Alternate Custody", "Historian Custody Complete", "Archived"), (("Pending Transfer", "Delivery Initiated"), ("Delivery Initiated", "Delivery In Progress"), ("Delivery In Progress", "Receipt Pending"), ("Receipt Pending", "Accepted"), ("Receipt Pending", "Rejected"), ("Rejected", "Retry Pending"), ("Retry Pending", "Delivery Initiated"), ("Receipt Pending", "Alternate Custody"), ("Alternate Custody", "Delivery Initiated"), ("Accepted", "Historian Custody Complete"), ("Historian Custody Complete", "Archived")), (), ("Archived",), ("delivery record", "custody acknowledgement"), "retry without overwriting delivery evidence", "acknowledgement is required for completion"),
}


VERIFICATION_CLASSES = (
    "positive",
    "negative",
    "boundary",
    "stale_input",
    "expired_authority",
    "conflicting_authority",
    "replay",
    "restart",
    "recovery",
    "missing_evidence",
)


TRADER_RM002_RULES: Mapping[str, ConstitutionalRule] = {
    "TRADER-RULE-001": ConstitutionalRule("TRADER-RULE-001", "Authority Rule", "TRADER-RM-002-001", ("Investment Intent",), VERIFICATION_CLASSES, ("Investment Intent reference",), "Verified"),
    "TRADER-RULE-002": ConstitutionalRule("TRADER-RULE-002", "Authority Rule", "TRADER-RM-002-007", ("Authorization",), VERIFICATION_CLASSES, ("Authorization validation evidence",), "Verified"),
    "TRADER-RULE-003": ConstitutionalRule("TRADER-RULE-003", "Authority Rule", "TRADER-RM-002-007", ("Risk Certificate",), VERIFICATION_CLASSES, ("Risk validation evidence",), "Verified"),
    "TRADER-RULE-004": ConstitutionalRule("TRADER-RULE-004", "Time Rule", "TRADER-GOV-012", ("Operating Mode Authority",), VERIFICATION_CLASSES, ("Mode authority evidence",), "Verified"),
    "TRADER-RULE-005": ConstitutionalRule("TRADER-RULE-005", "Lifecycle Rule", "TRADER-RM-002-003", ("Execution Mandate",), VERIFICATION_CLASSES, ("mandate validation",), "Verified"),
    "TRADER-RULE-006": ConstitutionalRule("TRADER-RULE-006", "Lifecycle Rule", "TRADER-RM-002-003", ("Execution Plan",), VERIFICATION_CLASSES, ("plan approval",), "Verified"),
    "TRADER-RULE-007": ConstitutionalRule("TRADER-RULE-007", "Object Rule", "TRADER-RM-002-004", ("Canonical Order",), VERIFICATION_CLASSES, ("order transition history",), "Verified"),
    "TRADER-RULE-008": ConstitutionalRule("TRADER-RULE-008", "Broker Rule", "TRADER-RM-002-008", ("Broker Submission Request",), VERIFICATION_CLASSES, ("idempotency evidence",), "Verified"),
    "TRADER-RULE-009": ConstitutionalRule("TRADER-RULE-009", "Broker Rule", "TRADER-RM-002-008", ("Broker Communication Record",), VERIFICATION_CLASSES, ("payload digest",), "Verified"),
    "TRADER-RULE-010": ConstitutionalRule("TRADER-RULE-010", "Broker Rule", "TRADER-RM-002-008", ("Broker Event",), VERIFICATION_CLASSES, ("broker event evidence",), "Verified"),
    "TRADER-RULE-011": ConstitutionalRule("TRADER-RULE-011", "Lifecycle Rule", "TRADER-RM-002-005", ("Canonical Fill Record",), VERIFICATION_CLASSES, ("fill validation",), "Verified"),
    "TRADER-RULE-012": ConstitutionalRule("TRADER-RULE-012", "Lifecycle Rule", "TRADER-RM-002-005", ("Canonical Position",), VERIFICATION_CLASSES, ("position transition evidence",), "Verified"),
    "TRADER-RULE-013": ConstitutionalRule("TRADER-RULE-013", "Financial Dependency Rule", "TRADER-RM-002-009", ("Financial Resource Admissibility Record",), VERIFICATION_CLASSES, ("financial authority evidence",), "Verified"),
    "TRADER-RULE-014": ConstitutionalRule("TRADER-RULE-014", "Traceability Rule", "TRADER-RM-002-006", ("Reconciliation Object",), VERIFICATION_CLASSES, ("discrepancy evidence",), "Verified"),
    "TRADER-RULE-015": ConstitutionalRule("TRADER-RULE-015", "Monitoring Rule", "TRADER-RM-002-010", ("Monitoring Alert",), VERIFICATION_CLASSES, ("alert classification",), "Verified"),
    "TRADER-RULE-016": ConstitutionalRule("TRADER-RULE-016", "Monitoring Rule", "TRADER-RM-002-010", ("Fusion Assessment",), VERIFICATION_CLASSES, ("source correlation",), "Verified"),
    "TRADER-RULE-017": ConstitutionalRule("TRADER-RULE-017", "Emergency Rule", "TRADER-RM-002-011", ("Emergency Action Record",), VERIFICATION_CLASSES, ("emergency authority",), "Verified"),
    "TRADER-RULE-018": ConstitutionalRule("TRADER-RULE-018", "Evidence Rule", "TRADER-RM-002-012", ("Trader Execution Case File",), VERIFICATION_CLASSES, ("completion evidence",), "Verified"),
    "TRADER-RULE-019": ConstitutionalRule("TRADER-RULE-019", "Certification Rule", "TRADER-RM-002-013", ("Historian Custody Acknowledgement",), VERIFICATION_CLASSES, ("custody acknowledgement",), "Verified"),
    "TRADER-RULE-020": ConstitutionalRule("TRADER-RULE-020", "Repository Closure Rule", "TRADER-RM-002-015", tuple(TRADER_RM002_OBJECTS), VERIFICATION_CLASSES, ("dependency evidence",), "Verified"),
    "TRADER-RULE-021": ConstitutionalRule("TRADER-RULE-021", "Traceability Rule", "TRADER-RM-002-016", tuple(TRADER_RM002_OBJECTS), VERIFICATION_CLASSES, ("traceability matrix",), "Verified"),
}


CASE_FILE_REQUIRED_EVIDENCE = (
    "Investment Intent reference",
    "Authorization validation evidence",
    "Risk validation evidence",
    "Mode authority evidence",
    "mandate creation",
    "plan approval",
    "order creation",
    "submission evidence",
    "broker event evidence",
    "fill validation",
    "position transition evidence",
    "financial authority evidence",
    "discrepancy evidence",
    "alert classification",
    "source correlation",
    "completion evidence",
    "custody acknowledgement",
)


DEPENDENCY_CLASSES = (
    "Authority Dependency",
    "Object Dependency",
    "Lifecycle Dependency",
    "Interface Dependency",
    "Persistence Dependency",
    "Evidence Dependency",
    "Certification Dependency",
    "Runtime Dependency",
    "Configuration Dependency",
    "Financial Dependency",
    "Historical Dependency",
)


def validate_rm002_constitution() -> RM002Decision:
    findings = []
    findings.extend(_validate_precedence())
    findings.extend(_validate_objects())
    findings.extend(_validate_lifecycles())
    findings.extend(_validate_rules())
    findings.extend(_validate_traceability())
    return _decision(findings)


def validate_lifecycle_transition(lifecycle_name: str, source: str, destination: str) -> RM002Decision:
    lifecycle = TRADER_RM002_LIFECYCLES.get(lifecycle_name)
    if lifecycle is None:
        return _decision((f"unknown lifecycle: {lifecycle_name}",))
    if (source, destination) in lifecycle.prohibited_transitions:
        return _decision((f"prohibited transition: {source}->{destination}",))
    if (source, destination) not in lifecycle.permitted_transitions:
        return _decision((f"undefined transition: {source}->{destination}",))
    return _decision(())


def validate_case_file_evidence(present_evidence: Sequence[str]) -> RM002Decision:
    present = set(present_evidence)
    missing = tuple(evidence for evidence in CASE_FILE_REQUIRED_EVIDENCE if evidence not in present)
    if missing:
        return _decision(("case file evidence incomplete: " + ", ".join(missing),))
    return _decision(())


def validate_independent_certification_authority(verdict: str, issuer: str) -> RM002Decision:
    findings = []
    if issuer != "Independent Final Reconciliation Authority":
        findings.append("certification issuer is not independent final reconciliation authority")
    if verdict not in {"UNCONDITIONAL PASS", "FAIL"}:
        findings.append(f"prohibited certification verdict: {verdict}")
    return _decision(findings)


def _validate_precedence() -> tuple[str, ...]:
    findings = []
    if len(AUTHORITY_PRECEDENCE) != len(set(AUTHORITY_PRECEDENCE)):
        findings.append("authority precedence contains duplicates")
    for doctrine in ("TRADER-RM-002-001", "TRADER-RM-002-016"):
        if doctrine not in DOCTRINE_SUPERSESSION_REGISTER:
            findings.append(f"missing supersession disposition: {doctrine}")
    return tuple(findings)


def _validate_objects() -> tuple[str, ...]:
    findings = []
    identifiers = [record.identifier for record in TRADER_RM002_OBJECTS.values()]
    if len(identifiers) != len(set(identifiers)):
        findings.append("duplicate constitutional object identifier")
    for name, record in TRADER_RM002_OBJECTS.items():
        if not record.owner:
            findings.append(f"missing owner: {name}")
        if not record.evidence:
            findings.append(f"missing evidence obligation: {name}")
        if record.lifecycle not in TRADER_RM002_LIFECYCLES and not record.external:
            findings.append(f"missing lifecycle specification: {name}")
        if record.owner == "Trader Office" and "Financial" in name and name != "Financial Resource Admissibility Record":
            findings.append(f"Trader owns financial truth by implication: {name}")
    return tuple(findings)


def _validate_lifecycles() -> tuple[str, ...]:
    findings = []
    for name, lifecycle in TRADER_RM002_LIFECYCLES.items():
        states = set(lifecycle.states)
        if not lifecycle.terminal_states:
            findings.append(f"missing terminal states: {name}")
        for source, destination in lifecycle.permitted_transitions:
            if source not in states or destination not in states:
                findings.append(f"transition references unknown state in {name}: {source}->{destination}")
        if not lifecycle.required_evidence:
            findings.append(f"missing transition evidence: {name}")
        if not lifecycle.recovery_behavior or not lifecycle.replay_behavior:
            findings.append(f"missing replay or recovery behavior: {name}")
    return tuple(findings)


def _validate_rules() -> tuple[str, ...]:
    findings = []
    valid_statuses = {"Verified", "Verification Failed", "Superseded", "Archived"}
    for rule in TRADER_RM002_RULES.values():
        if rule.certification_status not in valid_statuses:
            findings.append(f"invalid rule certification status: {rule.identifier}")
        missing_classes = tuple(item for item in VERIFICATION_CLASSES if item not in rule.verification_classes)
        if missing_classes:
            findings.append(f"missing verification classes for {rule.identifier}: {', '.join(missing_classes)}")
        for obj in rule.objects:
            if obj not in TRADER_RM002_OBJECTS:
                findings.append(f"rule references unknown object: {rule.identifier}:{obj}")
        if not rule.evidence:
            findings.append(f"rule missing evidence: {rule.identifier}")
    return tuple(findings)


def _validate_traceability() -> tuple[str, ...]:
    findings = []
    governed_objects = {obj for rule in TRADER_RM002_RULES.values() for obj in rule.objects}
    for name in TRADER_RM002_OBJECTS:
        if name not in governed_objects:
            findings.append(f"orphan constitutional object: {name}")
    object_rules = {rule for record in TRADER_RM002_OBJECTS.values() for rule in record.certification_rules}
    missing_rules = tuple(rule for rule in object_rules if rule not in TRADER_RM002_RULES)
    if missing_rules:
        findings.append("object references missing certification rules: " + ", ".join(missing_rules))
    return tuple(findings)


def _decision(findings: Sequence[str]) -> RM002Decision:
    normalized = tuple(findings)
    return RM002Decision(TraderRM002Status.FAIL if normalized else TraderRM002Status.PASS, normalized)
