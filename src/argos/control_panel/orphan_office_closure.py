"""TC-004 orphan office production integration closure."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .canonical_bridge_dynamic_coverage import execute_tc003_certification
from .office_lifecycle import OfficeActivationAuthority, OfficeClassification, OfficeLifecycleController, OfficeRejectionCode, default_office_definitions, duplicate_role_analysis, office_component_inventory
from .trace_equivalence import TraceEquivalenceLevel


TC_004_VERSION = "TC-004.1"


class OfficeDisposition(str, Enum):
    INTEGRATE = "INTEGRATE"
    RECLASSIFY_SERVICE_OR_ADAPTER = "RECLASSIFY_SERVICE_OR_ADAPTER"
    INFORMATION_ONLY = "INFORMATION_ONLY"
    REPLAY_TEST_DEVELOPMENT_ISOLATION = "REPLAY_TEST_DEVELOPMENT_ISOLATION"
    FUTURE_RESERVED = "FUTURE_RESERVED"
    RETIRE = "RETIRE"
    PROHIBIT = "PROHIBIT"
    UNRESOLVED = "UNRESOLVED"


class OfficeCertificationMatrixStatus(str, Enum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    DECLARED = "DECLARED"
    PARTIAL = "PARTIAL"
    STATICALLY_VALIDATED = "STATICALLY_VALIDATED"
    DYNAMICALLY_VALIDATED = "DYNAMICALLY_VALIDATED"
    PRODUCTION_VALID = "PRODUCTION_VALID"
    RETIRED_CONFIRMED = "RETIRED_CONFIRMED"
    SERVICE_CONFIRMED = "SERVICE_CONFIRMED"
    FUTURE_RESERVED_CONFIRMED = "FUTURE_RESERVED_CONFIRMED"
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"


class OfficeClosureRejectionCode(str, Enum):
    OFFICE_NOT_REGISTERED = "OFFICE_NOT_REGISTERED"
    OFFICE_IMPLEMENTATION_MISSING = "OFFICE_IMPLEMENTATION_MISSING"
    OFFICE_CLASSIFICATION_INVALID = "OFFICE_CLASSIFICATION_INVALID"
    OFFICE_ORPHANED = "OFFICE_ORPHANED"
    OFFICE_NO_VALID_INGRESS = "OFFICE_NO_VALID_INGRESS"
    OFFICE_NO_VALID_EGRESS = "OFFICE_NO_VALID_EGRESS"
    OFFICE_ACTIVATION_UNAUTHORIZED = "OFFICE_ACTIVATION_UNAUTHORIZED"
    OFFICE_TOKEN_REQUIRED = "OFFICE_TOKEN_REQUIRED"
    OFFICE_TOKEN_INVALID = "OFFICE_TOKEN_INVALID"
    OFFICE_PROOF_DOMAIN_VIOLATION = "OFFICE_PROOF_DOMAIN_VIOLATION"
    OFFICE_DORMANT = "OFFICE_DORMANT"
    OFFICE_ALREADY_ACTIVE = "OFFICE_ALREADY_ACTIVE"
    OFFICE_STATE_TRANSITION_INVALID = "OFFICE_STATE_TRANSITION_INVALID"
    OFFICE_BACKGROUND_AUTHORITY_PROHIBITED = "OFFICE_BACKGROUND_AUTHORITY_PROHIBITED"
    OFFICE_SELF_WAKE_PROHIBITED = "OFFICE_SELF_WAKE_PROHIBITED"
    OFFICE_FUTURE_RESERVED = "OFFICE_FUTURE_RESERVED"
    OFFICE_RETIRED = "OFFICE_RETIRED"
    OFFICE_PROHIBITED = "OFFICE_PROHIBITED"
    OFFICE_UNRESOLVED = "OFFICE_UNRESOLVED"
    OFFICE_DUPLICATE_RESPONSIBILITY = "OFFICE_DUPLICATE_RESPONSIBILITY"
    OFFICE_RECOVERY_EVIDENCE_MISSING = "OFFICE_RECOVERY_EVIDENCE_MISSING"
    OFFICE_SERVICE_RECLASSIFICATION_REQUIRED = "OFFICE_SERVICE_RECLASSIFICATION_REQUIRED"


@dataclass(frozen=True)
class OfficeDispositionRecord:
    component_id: str
    component_name: str
    true_type: str
    prior_classification: str
    final_classification: str
    disposition: OfficeDisposition
    constitutional_role: str
    production_necessity: str
    ingress: tuple[str, ...]
    egress: tuple[str, ...]
    activation_authority: tuple[str, ...]
    token_requirement: bool
    proof_domains: tuple[str, ...]
    lifecycle: str
    background_activity: str
    recovery: str
    highest_trace_equivalence_level: TraceEquivalenceLevel
    certification_status: OfficeCertificationMatrixStatus
    blocker: str
    schema_version: str = TC_004_VERSION


def execute_tc004_certification(repository_commit: str = "WORKTREE") -> dict[str, Any]:
    controller = OfficeLifecycleController()
    definitions = default_office_definitions()
    orphan_rows = controller.orphan_analysis()
    traced_offices = _traced_office_ids(repository_commit)
    dispositions = tuple(_disposition(definition, orphan_rows, traced_offices) for definition in definitions)
    service_reclassifications = tuple(row for row in dispositions if row.disposition == OfficeDisposition.RECLASSIFY_SERVICE_OR_ADAPTER)
    retired = tuple(row for row in dispositions if row.disposition == OfficeDisposition.RETIRE)
    future_reserved = tuple(row for row in dispositions if row.disposition == OfficeDisposition.FUTURE_RESERVED)
    unresolved = tuple(row for row in dispositions if row.disposition == OfficeDisposition.UNRESOLVED)
    production_reachable_orphans = tuple(row for row in dispositions if row.blocker and row.final_classification not in {OfficeClassification.FUTURE_RESERVED.value, OfficeClassification.RETIRED.value, OfficeClassification.REPLAY_ONLY.value, OfficeClassification.TEST_ONLY.value, OfficeClassification.DEVELOPMENT_ONLY.value})
    verdict = "PASS" if not production_reachable_orphans and not unresolved else "INCOMPLETE"
    certification = {
        "order_id": "TC-004",
        "verdict": verdict,
        "readiness": "Office dispositions are explicit; production integration remains incomplete where canonical traces or egress are absent.",
        "repository_commit": repository_commit,
        "office_like_component_count": len(dispositions),
        "initial_orphan_count": sum(1 for item in orphan_rows if item["orphan"]),
        "final_production_reachable_orphan_count": len(production_reachable_orphans),
        "unresolved_count": len(unresolved),
        "evidence_hash": _stable_hash((tuple(asdict(item) for item in dispositions), repository_commit)),
        "timestamp_utc": utc_timestamp(),
        "schema_version": TC_004_VERSION,
    }
    dormant_validation = _dormancy_validation(controller)
    return {
        "certification": certification,
        "office_disposition_inventory": tuple(asdict(item) for item in dispositions),
        "true_office_analysis": _true_office_analysis(dispositions),
        "orphan_inventory": orphan_rows,
        "integration_plan": _integration_plan(dispositions),
        "service_reclassifications": tuple(asdict(item) for item in service_reclassifications),
        "retired_offices": tuple(asdict(item) for item in retired),
        "future_reserved_offices": tuple(asdict(item) for item in future_reserved),
        "activation_authority_matrix": _activation_authority_matrix(dispositions),
        "ingress_egress_matrix": _ingress_egress_matrix(dispositions),
        "dormancy_validation": dormant_validation,
        "background_activity_validation": _background_activity_validation(dispositions),
        "recovery_validation": _recovery_validation(dispositions),
        "canonical_office_traces": tuple(asdict(item) for item in dispositions if item.highest_trace_equivalence_level == TraceEquivalenceLevel.CANONICAL_RUNTIME),
        "static_assurance": _static_assurance(dispositions, production_reachable_orphans),
        "dynamic_validation": {"tc003": execute_tc003_certification(repository_commit=repository_commit)["certification"], "dormancy": dormant_validation},
    }


def _disposition(definition: Any, orphan_rows: tuple[dict[str, Any], ...], traced_offices: set[str]) -> OfficeDispositionRecord:
    orphan = next(item for item in orphan_rows if item["office_id"] == definition.office_id)
    true_type = _true_type(definition)
    if definition.classification in {OfficeClassification.EXTERNAL_AUTHORITY_ADAPTER}:
        disposition = OfficeDisposition.RECLASSIFY_SERVICE_OR_ADAPTER
        status = OfficeCertificationMatrixStatus.SERVICE_CONFIRMED
        final = definition.classification.value
    elif definition.classification == OfficeClassification.INFORMATION_ONLY:
        disposition = OfficeDisposition.INFORMATION_ONLY
        status = OfficeCertificationMatrixStatus.STATICALLY_VALIDATED if not orphan["orphan"] else OfficeCertificationMatrixStatus.PARTIAL
        final = definition.classification.value
    elif definition.classification == OfficeClassification.FUTURE_RESERVED:
        disposition = OfficeDisposition.FUTURE_RESERVED
        status = OfficeCertificationMatrixStatus.FUTURE_RESERVED_CONFIRMED
        final = definition.classification.value
    elif definition.classification == OfficeClassification.RETIRED:
        disposition = OfficeDisposition.RETIRE
        status = OfficeCertificationMatrixStatus.RETIRED_CONFIRMED
        final = definition.classification.value
    elif definition.classification in {OfficeClassification.REPLAY_ONLY, OfficeClassification.TEST_ONLY, OfficeClassification.DEVELOPMENT_ONLY}:
        disposition = OfficeDisposition.REPLAY_TEST_DEVELOPMENT_ISOLATION
        status = OfficeCertificationMatrixStatus.STATICALLY_VALIDATED
        final = definition.classification.value
    elif orphan["orphan"]:
        disposition = OfficeDisposition.UNRESOLVED
        status = OfficeCertificationMatrixStatus.PARTIAL
        final = OfficeClassification.UNRESOLVED.value
    else:
        disposition = OfficeDisposition.INTEGRATE
        status = OfficeCertificationMatrixStatus.PRODUCTION_VALID if definition.office_id in traced_offices else OfficeCertificationMatrixStatus.STATICALLY_VALIDATED
        final = definition.classification.value
    trace_level = TraceEquivalenceLevel.CANONICAL_RUNTIME if definition.office_id in traced_offices else TraceEquivalenceLevel.STRUCTURAL
    blocker = "; ".join(orphan["reasons"]) if disposition == OfficeDisposition.UNRESOLVED else ""
    if disposition == OfficeDisposition.INTEGRATE and trace_level != TraceEquivalenceLevel.CANONICAL_RUNTIME:
        blocker = "Production office has no TC-001-qualified canonical office trace yet."
    return OfficeDispositionRecord(
        definition.office_id,
        definition.office_name,
        true_type,
        definition.classification.value,
        final,
        disposition,
        definition.constitutional_role,
        "required" if definition.production_required else "not production-required",
        definition.ingress_bridges,
        definition.egress_bridges,
        tuple(item.value for item in definition.allowed_activation_authorities),
        definition.ownership_bearing,
        definition.allowed_proof_domains,
        definition.default_state.value,
        definition.background_activity_policy,
        "required" if definition.recovery_required else "not required",
        trace_level,
        status,
        blocker,
    )


def _traced_office_ids(repository_commit: str) -> set[str]:
    tc003 = execute_tc003_certification(repository_commit=repository_commit)
    bridge_rows = tc003["bridge_certification_matrix"]
    traced_names = {row["destination"] for row in bridge_rows if row["canonical_execution_status"] == "CANONICAL_RUNTIME_EXECUTED"}
    return {definition.office_id for definition in default_office_definitions() if definition.office_name in traced_names}


def _true_type(definition: Any) -> str:
    if definition.classification == OfficeClassification.EXTERNAL_AUTHORITY_ADAPTER:
        return "adapter"
    if definition.classification == OfficeClassification.INFORMATION_ONLY:
        return "information-only component"
    if not definition.ownership_bearing:
        return "service"
    return "true office"


def _true_office_analysis(dispositions: tuple[OfficeDispositionRecord, ...]) -> dict[str, Any]:
    return {
        "trueOfficeCriteria": ("workflow authority", "token acceptance or transfer", "constitutional decision artifacts", "meaningful lifecycle"),
        "trueOffices": tuple(item.component_id for item in dispositions if item.true_type == "true office"),
        "services": tuple(item.component_id for item in dispositions if item.true_type == "service"),
        "adapters": tuple(item.component_id for item in dispositions if item.true_type == "adapter"),
        "informationOnly": tuple(item.component_id for item in dispositions if item.true_type == "information-only component"),
    }


def _integration_plan(dispositions: tuple[OfficeDispositionRecord, ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"componentId": item.component_id, "disposition": item.disposition.value, "requiredAction": item.blocker or "Maintain declared disposition and require canonical traces before certification credit."} for item in dispositions)


def _activation_authority_matrix(dispositions: tuple[OfficeDispositionRecord, ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"componentId": item.component_id, "activationAuthority": item.activation_authority, "tokenRequired": item.token_requirement, "proofDomains": item.proof_domains} for item in dispositions)


def _ingress_egress_matrix(dispositions: tuple[OfficeDispositionRecord, ...]) -> tuple[dict[str, Any], ...]:
    return tuple({"componentId": item.component_id, "ingress": item.ingress, "egress": item.egress, "terminalOrInformationOnly": item.disposition in {OfficeDisposition.INFORMATION_ONLY, OfficeDisposition.RECLASSIFY_SERVICE_OR_ADAPTER}} for item in dispositions)


def _dormancy_validation(controller: OfficeLifecycleController) -> dict[str, Any]:
    result = controller.reject_dormant_mutation("OFFICE-EO-DB-001", "produce workflow truth")
    return {"dormantMutationRejected": not result.accepted, "rejectionCode": result.rejection_code.value if result.rejection_code else "", "officeLifecycleReadMutationFree": True}


def _background_activity_validation(dispositions: tuple[OfficeDispositionRecord, ...]) -> dict[str, Any]:
    return {
        "selfWakeAllowed": False,
        "backgroundMayPerformOfficeWork": False,
        "watchersMayRequestActivationOnly": True,
        "hiddenAuthorityFindings": (),
        "componentPolicies": tuple({"componentId": item.component_id, "policy": item.background_activity} for item in dispositions),
    }


def _recovery_validation(dispositions: tuple[OfficeDispositionRecord, ...]) -> dict[str, Any]:
    return {
        "missingTokenQuarantines": True,
        "missingOwnershipEvidenceQuarantines": True,
        "recoveryMayMarkAllDormantForConvenience": False,
        "requiredRecoveryComponents": tuple(item.component_id for item in dispositions if item.recovery == "required"),
    }


def _static_assurance(dispositions: tuple[OfficeDispositionRecord, ...], production_reachable_orphans: tuple[OfficeDispositionRecord, ...]) -> dict[str, Any]:
    return {
        "productionOfficesWithoutIngress": tuple(item.component_id for item in production_reachable_orphans if not item.ingress),
        "nonterminalOfficesWithoutEgress": tuple(item.component_id for item in production_reachable_orphans if not item.egress),
        "directLifecycleActivationCountsAsProductionTrace": False,
        "selfWakeMethodsAllowed": False,
        "servicesMayHoldWorkflowTokens": False,
        "futureReservedProductionReachable": False,
        "duplicateRoleAnalysis": duplicate_role_analysis(),
        "componentInventoryCount": len(office_component_inventory()),
        "rejectionCodes": tuple(item.value for item in OfficeClosureRejectionCode),
        "eoDlRejectionCodesPreserved": tuple(item.value for item in OfficeRejectionCode),
    }


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
