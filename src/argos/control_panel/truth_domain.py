"""Truth-domain and provenance guards for ARGOS operational records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any


class RuntimeMode(str, Enum):
    """Supported ARGOS runtime truth domains."""

    TEST = "TEST"
    PROOF = "PROOF"
    SIMULATION = "SIMULATION"
    PAPER = "PAPER"
    LIVE = "LIVE"


class TruthClassification(str, Enum):
    """Certification class for an enterprise record."""

    TEST_FIXTURE = "TEST_FIXTURE"
    PROOF_ONLY = "PROOF_ONLY"
    SIMULATION_ONLY = "SIMULATION_ONLY"
    PAPER_OPERATIONAL = "PAPER_OPERATIONAL"
    PAPER_PROVISIONAL_BROKER_MODEL = "PAPER_PROVISIONAL_BROKER_MODEL"
    LIVE_DISABLED = "LIVE_DISABLED"
    INCOMPLETE = "INCOMPLETE"


class ProvenanceStatus(str, Enum):
    """Whether material record fields have sufficient provenance."""

    VALIDATED = "VALIDATED"
    MISSING = "MISSING"
    UNVERIFIED = "UNVERIFIED"
    REJECTED = "REJECTED"


class CertificationStatus(str, Enum):
    """Canonical certification states used by operational truth envelopes."""

    PAPER_OPERATIONAL_CERTIFIED = "PAPER_OPERATIONAL_CERTIFIED"
    PROOF_MODE_NOT_ACTIONABLE = "PROOF_MODE_NOT_ACTIONABLE"
    SIMULATION_ONLY_NOT_OPERATIONAL_TRUTH = "SIMULATION_ONLY_NOT_OPERATIONAL_TRUTH"
    DEGRADED_ANALYTICAL_ONLY = "DEGRADED_ANALYTICAL_ONLY"
    UNCERTIFIED = "UNCERTIFIED"
    REJECTED_NOT_OPERATIONAL_TRUTH = "REJECTED_NOT_OPERATIONAL_TRUTH"


class TruthEnvelopeError(ValueError):
    """Raised when an authoritative write lacks validated operational truth."""

    def __init__(self, codes: tuple[str, ...]) -> None:
        self.codes = codes
        super().__init__(",".join(codes))


@dataclass(frozen=True)
class OperationalTruthEnvelope:
    """Validated provenance contract for authoritative PAPER writes."""

    truth_domain: str
    provenance_status: str
    truth_classification: str
    certification_status: str
    originating_authority: str
    originating_workflow_id: str
    workflow_token_id: str
    mission_id: str
    source_event_id: str
    schema_version: str
    validation_result: str
    idempotency_key: str
    timestamp_utc: str
    caller: str
    source_system: str = ""
    degraded: bool = False


@dataclass(frozen=True)
class TruthEnvelopeValidation:
    """Deterministic envelope validation result."""

    valid: bool
    codes: tuple[str, ...]
    envelope: dict[str, Any]


PLACEHOLDER_SOURCES = {
    "deterministic_placeholder",
    "runtime_placeholder",
    "workflow_proof",
    "paper_trading_proof",
    "dry_run_fallback",
}

AUTHORIZED_OFFICE_PRODUCERS = {
    "Seeker",
    "Analyst",
    "Risk",
    "Trader",
    "Historian",
}

AUTHORIZED_OPERATIONAL_AUTHORITIES = {
    "EnterpriseWorkflowOrchestrator",
    "EnterpriseOperationsScheduler",
    "EnterpriseMissionPlanner",
    "DeterministicPaperBrokerage",
    "PositionRegistry",
    "PerformanceTruthEngine",
    "EnterpriseDoctrinePolicyManager",
    "Risk",
    "Trader",
    "Seeker",
    "Analyst",
    "Historian",
}

OPERATIONAL_FIELD_PROVENANCE = (
    "asset_identifier",
    "asset_class",
    "direction",
    "thesis",
    "evidence",
    "market_context",
    "entry_conditions",
    "price_source",
    "quantity",
    "position_sizing_basis",
    "confidence",
    "time_horizon",
    "risk_factors",
    "stop_conditions",
    "exit_conditions",
    "expected_return",
    "risk_approval",
    "trader_authorization",
)


@dataclass(frozen=True)
class ProvenanceValidation:
    """Deterministic provenance validation result."""

    valid: bool
    codes: tuple[str, ...]
    truth_domain: str
    truth_classification: str
    certification_status: str


def proof_metadata(*, source_system: str, source_record_ids: tuple[str, ...], workflow_id: str = "", decision_object_id: str = "", created_at: str = "") -> dict[str, Any]:
    """Return common metadata for proof-only records."""
    return {
        "environment": "proof",
        "executionMode": RuntimeMode.PROOF.value,
        "truthClassification": TruthClassification.PROOF_ONLY.value,
        "sourceSystem": source_system,
        "sourceRecordIds": tuple(source_record_ids),
        "workflowId": workflow_id,
        "decisionObjectId": decision_object_id,
        "officeAuthority": "NONE_PROOF_ONLY",
        "createdAt": created_at,
        "deterministicId": deterministic_id(source_system, workflow_id, decision_object_id, source_record_ids),
        "provenanceStatus": ProvenanceStatus.REJECTED.value,
        "certificationStatus": "PROOF_MODE_NOT_ACTIONABLE",
        "commanderTruthLabel": "PROOF MODE - NOT OPERATIONAL TRUTH",
    }


def paper_broker_metadata(*, source_system: str, source_record_ids: tuple[str, ...], workflow_id: str = "", decision_object_id: str = "", created_at: str = "") -> dict[str, Any]:
    """Return common metadata for provisional paper-broker records."""
    return {
        "environment": "paper",
        "executionMode": RuntimeMode.PAPER.value,
        "truthClassification": TruthClassification.PAPER_PROVISIONAL_BROKER_MODEL.value,
        "sourceSystem": source_system,
        "sourceRecordIds": tuple(source_record_ids),
        "workflowId": workflow_id,
        "decisionObjectId": decision_object_id,
        "officeAuthority": "TRADER_REQUIRED",
        "createdAt": created_at,
        "deterministicId": deterministic_id(source_system, workflow_id, decision_object_id, source_record_ids),
        "provenanceStatus": ProvenanceStatus.UNVERIFIED.value,
        "certificationStatus": "PAPER_BROKER_PROVISIONAL_OR003",
        "commanderTruthLabel": "PAPER - PROVISIONAL BROKER MODEL",
    }


def simulation_metadata(*, source_system: str, source_record_ids: tuple[str, ...], created_at: str = "") -> dict[str, Any]:
    """Return common metadata for simulation-only analytical records."""
    return {
        "environment": "simulation",
        "executionMode": RuntimeMode.SIMULATION.value,
        "truthClassification": TruthClassification.SIMULATION_ONLY.value,
        "sourceSystem": source_system,
        "sourceRecordIds": tuple(source_record_ids),
        "createdAt": created_at,
        "deterministicId": deterministic_id(source_system, "", "", source_record_ids),
        "provenanceStatus": ProvenanceStatus.VALIDATED.value,
        "certificationStatus": "SIMULATION_ONLY_NOT_OPERATIONAL_TRUTH",
        "commanderTruthLabel": "SIMULATION - NO BROKER ORDER",
    }


def validate_decision_object_for_operational_truth(decision_object: dict[str, Any], *, execution_environment: str) -> ProvenanceValidation:
    """Validate that a Decision Object may affect PAPER/LIVE operational truth."""
    domain = str(decision_object.get("executionMode") or decision_object.get("environment") or execution_environment or "").upper()
    classification = str(decision_object.get("truthClassification") or "")
    certification = str(decision_object.get("certificationStatus") or "")
    provenance = decision_object.get("materialFieldProvenance")
    office = str(decision_object.get("office", ""))
    revision_source = str(decision_object.get("revisionSource", ""))
    source_system = str(decision_object.get("sourceSystem", ""))
    codes: list[str] = []

    if execution_environment == "live":
        codes.append("LIVE_DISABLED")
    if domain in {RuntimeMode.PROOF.value, "PROOF"} or classification == TruthClassification.PROOF_ONLY.value:
        codes.append("PROOF_MODE_NOT_ACTIONABLE")
    if domain in {RuntimeMode.SIMULATION.value, "SIMULATION"} or classification == TruthClassification.SIMULATION_ONLY.value:
        codes.append("SIMULATION_VALUE_IN_OPERATIONAL_PATH")
    if revision_source in PLACEHOLDER_SOURCES or "placeholder" in revision_source.lower():
        codes.append("PLACEHOLDER_VALUE")
    if source_system.lower() in {"runtime", "controlpanelruntime", "control_panel_runtime"}:
        codes.append("UNAUTHORIZED_PRODUCER")
    if office not in AUTHORIZED_OFFICE_PRODUCERS:
        codes.append("UNAUTHORIZED_PRODUCER")
    if not isinstance(provenance, dict):
        codes.append("MISSING_PROVENANCE")
    else:
        missing = [field for field in OPERATIONAL_FIELD_PROVENANCE if provenance.get(field) in {None, "", "Missing", "MISSING"}]
        if missing:
            codes.append("MISSING_PROVENANCE")
        if provenance.get("price_source") in {"Simulation-only value", "SIMULATION_ONLY"}:
            codes.append("SIMULATION_VALUE_IN_OPERATIONAL_PATH")
        if provenance.get("risk_approval") != "Authorized office judgment":
            codes.append("MISSING_RISK_AUTHORITY")
        if provenance.get("trader_authorization") != "Authorized office judgment":
            codes.append("MISSING_TRADER_AUTHORITY")
    if certification not in {"PAPER_OPERATIONAL_CERTIFIED"}:
        codes.append("UNCERTIFIED_DECISION_OBJECT")

    unique = tuple(dict.fromkeys(codes))
    return ProvenanceValidation(
        valid=not unique,
        codes=unique,
        truth_domain=domain or execution_environment.upper(),
        truth_classification=classification or TruthClassification.INCOMPLETE.value,
        certification_status=certification or "UNCERTIFIED_DECISION_OBJECT",
    )


def make_paper_operational_truth_envelope(
    *,
    originating_authority: str,
    originating_workflow_id: str,
    workflow_token_id: str,
    mission_id: str,
    source_event_id: str,
    idempotency_key: str,
    timestamp_utc: str,
    caller: str,
    source_system: str = "",
    schema_version: str = "IFVR-001.3.5",
) -> OperationalTruthEnvelope:
    """Create the canonical validated envelope for PAPER operational truth."""
    return OperationalTruthEnvelope(
        truth_domain=RuntimeMode.PAPER.value,
        provenance_status=ProvenanceStatus.VALIDATED.value,
        truth_classification=TruthClassification.PAPER_OPERATIONAL.value,
        certification_status=CertificationStatus.PAPER_OPERATIONAL_CERTIFIED.value,
        originating_authority=originating_authority,
        originating_workflow_id=originating_workflow_id,
        workflow_token_id=workflow_token_id,
        mission_id=mission_id,
        source_event_id=source_event_id,
        schema_version=schema_version,
        validation_result="VALIDATED",
        idempotency_key=idempotency_key,
        timestamp_utc=timestamp_utc,
        caller=caller,
        source_system=source_system or originating_authority,
        degraded=False,
    )


def validate_operational_truth_envelope(
    envelope: OperationalTruthEnvelope | dict[str, Any] | None,
    *,
    target_authority: str,
    allowed_authorities: set[str] | None = None,
) -> TruthEnvelopeValidation:
    """Validate the canonical envelope required at authoritative write boundaries."""
    payload = _envelope_payload(envelope)
    authorities = allowed_authorities or AUTHORIZED_OPERATIONAL_AUTHORITIES
    codes: list[str] = []
    if not payload:
        codes.append("MISSING_TRUTH_ENVELOPE")
    truth_domain = str(payload.get("truth_domain") or payload.get("truthDomain") or "").upper()
    classification = str(payload.get("truth_classification") or payload.get("truthClassification") or "")
    provenance = str(payload.get("provenance_status") or payload.get("provenanceStatus") or "")
    certification = str(payload.get("certification_status") or payload.get("certificationStatus") or "")
    validation = str(payload.get("validation_result") or payload.get("validationResult") or "")
    authority = str(payload.get("originating_authority") or payload.get("originatingAuthority") or "")
    degraded = bool(payload.get("degraded", False))

    if truth_domain != RuntimeMode.PAPER.value:
        if truth_domain in {RuntimeMode.PROOF.value, "PROOF"}:
            codes.append("PROOF_MODE_NOT_ACTIONABLE")
        elif truth_domain in {RuntimeMode.SIMULATION.value, "SIMULATION"}:
            codes.append("SIMULATION_VALUE_IN_OPERATIONAL_PATH")
        elif truth_domain == RuntimeMode.LIVE.value:
            codes.append("LIVE_DISABLED")
        else:
            codes.append("INVALID_TRUTH_DOMAIN")
    if classification != TruthClassification.PAPER_OPERATIONAL.value:
        if classification == TruthClassification.PROOF_ONLY.value:
            codes.append("PROOF_MODE_NOT_ACTIONABLE")
        elif classification == TruthClassification.SIMULATION_ONLY.value:
            codes.append("SIMULATION_VALUE_IN_OPERATIONAL_PATH")
        elif classification == TruthClassification.LIVE_DISABLED.value:
            codes.append("LIVE_DISABLED")
        else:
            codes.append("INVALID_TRUTH_CLASSIFICATION")
    if provenance != ProvenanceStatus.VALIDATED.value:
        codes.append("PROVENANCE_NOT_VALIDATED")
    if certification != CertificationStatus.PAPER_OPERATIONAL_CERTIFIED.value:
        codes.append("UNCERTIFIED_OPERATIONAL_TRUTH")
    if validation != "VALIDATED":
        codes.append("VALIDATION_RESULT_NOT_VALIDATED")
    if degraded:
        codes.append("DEGRADED_TRUTH_NOT_AUTHORITATIVE")
    if authority not in authorities:
        codes.append("UNAUTHORIZED_AUTHORITY")
    for field in (
        "originating_workflow_id",
        "workflow_token_id",
        "mission_id",
        "source_event_id",
        "schema_version",
        "idempotency_key",
        "timestamp_utc",
        "caller",
    ):
        if not str(payload.get(field) or payload.get(_camel(field)) or ""):
            codes.append(f"MISSING_{field.upper()}")
    if target_authority and str(payload.get("caller") or "") != target_authority:
        codes.append("CALLER_TARGET_AUTHORITY_MISMATCH")

    unique = tuple(dict.fromkeys(codes))
    return TruthEnvelopeValidation(valid=not unique, codes=unique, envelope=payload)


def require_operational_truth_envelope(
    envelope: OperationalTruthEnvelope | dict[str, Any] | None,
    *,
    target_authority: str,
    allowed_authorities: set[str] | None = None,
) -> dict[str, Any]:
    """Return a validated envelope payload or raise deterministic rejection codes."""
    validation = validate_operational_truth_envelope(envelope, target_authority=target_authority, allowed_authorities=allowed_authorities)
    if not validation.valid:
        raise TruthEnvelopeError(validation.codes)
    return validation.envelope


def deterministic_id(source_system: str, workflow_id: str, decision_object_id: str, source_record_ids: tuple[str, ...]) -> str:
    payload = {
        "decision_object_id": decision_object_id,
        "source_record_ids": tuple(source_record_ids),
        "source_system": source_system,
        "workflow_id": workflow_id,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()[:16]
    return f"TRUTH-{digest.upper()}"


def _envelope_payload(envelope: OperationalTruthEnvelope | dict[str, Any] | None) -> dict[str, Any]:
    if envelope is None:
        return {}
    if isinstance(envelope, OperationalTruthEnvelope):
        return dict(envelope.__dict__)
    return dict(envelope)


def _camel(field: str) -> str:
    parts = field.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])
