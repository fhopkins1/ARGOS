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


def deterministic_id(source_system: str, workflow_id: str, decision_object_id: str, source_record_ids: tuple[str, ...]) -> str:
    payload = {
        "decision_object_id": decision_object_id,
        "source_record_ids": tuple(source_record_ids),
        "source_system": source_system,
        "workflow_id": workflow_id,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()[:16]
    return f"TRUTH-{digest.upper()}"

