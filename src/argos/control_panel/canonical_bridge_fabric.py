"""EO-DK canonical bridge execution fabric.

The fabric governs constitutionally significant handoffs. It is deliberately
small and synchronous for the current ARGOS runtime, but it enforces bridge
identity, proof domain, artifact integrity, idempotency, destination
acceptance, and LAW VII ownership rules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any, Callable

from argos.foundation.contracts import utc_timestamp

EO_DK_VERSION = "EO-DK.1"


class BridgeRequirementClass(str, Enum):
    REQUIRED_PRODUCTION = "REQUIRED_PRODUCTION"
    OPTIONAL_PRODUCTION = "OPTIONAL_PRODUCTION"
    REPLAY_ONLY = "REPLAY_ONLY"
    TEST_ONLY = "TEST_ONLY"
    DEVELOPMENT_ONLY = "DEVELOPMENT_ONLY"
    RETIRED = "RETIRED"
    PROHIBITED = "PROHIBITED"


class BridgeImplementationStatus(str, Enum):
    DECLARED = "DECLARED"
    IMPLEMENTED = "IMPLEMENTED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    ORPHANED = "ORPHANED"
    RETIRED = "RETIRED"


class BridgeCertificationStatus(str, Enum):
    UNCERTIFIED = "UNCERTIFIED"
    STATICALLY_VALIDATED = "STATICALLY_VALIDATED"
    DYNAMICALLY_TRACED = "DYNAMICALLY_TRACED"
    CONDITIONALLY_PRODUCTION = "CONDITIONALLY_PRODUCTION"
    CERTIFIED_PRODUCTION = "CERTIFIED_PRODUCTION"
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"


class BridgeTransferClass(str, Enum):
    OWNERSHIP_TRANSFER = "OWNERSHIP_TRANSFER"
    INFORMATION_DELIVERY = "INFORMATION_DELIVERY"
    AUTHORITY_REQUEST = "AUTHORITY_REQUEST"
    EXTERNAL_EXECUTION = "EXTERNAL_EXECUTION"


class BridgeResultStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DUPLICATE_IDEMPOTENT_SUCCESS = "DUPLICATE_IDEMPOTENT_SUCCESS"
    DEFERRED = "DEFERRED"
    TIMED_OUT = "TIMED_OUT"
    RECOVERY_PENDING = "RECOVERY_PENDING"
    QUARANTINED = "QUARANTINED"
    FAILED_BEFORE_TRANSFER = "FAILED_BEFORE_TRANSFER"
    FAILED_AFTER_INTENT = "FAILED_AFTER_INTENT"
    FAILED_AFTER_ACCEPTANCE = "FAILED_AFTER_ACCEPTANCE"
    COMPENSATION_REQUIRED = "COMPENSATION_REQUIRED"
    UNRESOLVED = "UNRESOLVED"


class BridgeIdempotencyPolicy(str, Enum):
    STRICT_ONCE = "STRICT_ONCE"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    AT_LEAST_ONCE_WITH_RECONCILIATION = "AT_LEAST_ONCE_WITH_RECONCILIATION"
    NON_RETRYABLE_FINANCIAL = "NON_RETRYABLE_FINANCIAL"


class BridgeRejectionCode(str, Enum):
    BRIDGE_NOT_REGISTERED = "BRIDGE_NOT_REGISTERED"
    BRIDGE_NOT_REQUIRED = "BRIDGE_NOT_REQUIRED"
    BRIDGE_IMPLEMENTATION_MISSING = "BRIDGE_IMPLEMENTATION_MISSING"
    BRIDGE_CANONICAL_TRIGGER_MISSING = "BRIDGE_CANONICAL_TRIGGER_MISSING"
    BRIDGE_SOURCE_ARTIFACT_INVALID = "BRIDGE_SOURCE_ARTIFACT_INVALID"
    BRIDGE_SOURCE_AUTHORITY_INVALID = "BRIDGE_SOURCE_AUTHORITY_INVALID"
    BRIDGE_PROVENANCE_INVALID = "BRIDGE_PROVENANCE_INVALID"
    BRIDGE_PROOF_DOMAIN_INVALID = "BRIDGE_PROOF_DOMAIN_INVALID"
    BRIDGE_DISABLED = "BRIDGE_DISABLED"
    BRIDGE_RETIRED = "BRIDGE_RETIRED"
    BRIDGE_PROHIBITED = "BRIDGE_PROHIBITED"
    BRIDGE_PROOF_DOMAIN_REJECTED = "BRIDGE_PROOF_DOMAIN_REJECTED"
    BRIDGE_TOKEN_REQUIRED = "BRIDGE_TOKEN_REQUIRED"
    BRIDGE_TOKEN_INVALID = "BRIDGE_TOKEN_INVALID"
    BRIDGE_SOURCE_NOT_OWNER = "BRIDGE_SOURCE_NOT_OWNER"
    BRIDGE_INVALID_OWNER = "BRIDGE_INVALID_OWNER"
    BRIDGE_ARTIFACT_MISSING = "BRIDGE_ARTIFACT_MISSING"
    BRIDGE_ARTIFACT_HASH_MISMATCH = "BRIDGE_ARTIFACT_HASH_MISMATCH"
    BRIDGE_DESTINATION_INELIGIBLE = "BRIDGE_DESTINATION_INELIGIBLE"
    BRIDGE_DESTINATION_REJECTED = "BRIDGE_DESTINATION_REJECTED"
    BRIDGE_ACCEPTANCE_EVIDENCE_MISSING = "BRIDGE_ACCEPTANCE_EVIDENCE_MISSING"
    BRIDGE_OWNERSHIP_TRANSFER_INCOMPLETE = "BRIDGE_OWNERSHIP_TRANSFER_INCOMPLETE"
    BRIDGE_PERSISTENCE_FAILED = "BRIDGE_PERSISTENCE_FAILED"
    BRIDGE_TIMEOUT = "BRIDGE_TIMEOUT"
    BRIDGE_RECOVERY_UNRESOLVED = "BRIDGE_RECOVERY_UNRESOLVED"
    BRIDGE_DUPLICATE_REJECTED = "BRIDGE_DUPLICATE_REJECTED"
    BRIDGE_IDEMPOTENCY_VIOLATION = "BRIDGE_IDEMPOTENCY_VIOLATION"
    BRIDGE_CERTIFICATION_HARNESS_ORIGIN_REJECTED = "BRIDGE_CERTIFICATION_HARNESS_ORIGIN_REJECTED"
    BRIDGE_CANONICAL_TRACE_REQUIRED = "BRIDGE_CANONICAL_TRACE_REQUIRED"
    BRIDGE_DUPLICATE_STRICT_ONCE = "BRIDGE_DUPLICATE_STRICT_ONCE"
    BRIDGE_PERSISTENCE_REQUIRED = "BRIDGE_PERSISTENCE_REQUIRED"
    BRIDGE_RUNTIME_MISMATCH = "BRIDGE_RUNTIME_MISMATCH"


@dataclass(frozen=True)
class CanonicalBridgeDefinition:
    bridge_id: str
    bridge_name: str
    bridge_version: str
    source_component: str
    destination_component: str
    allowed_workflow_types: tuple[str, ...]
    allowed_proof_domains: tuple[str, ...]
    input_artifact_type: str
    accepted_artifact_type: str
    payload_schema_version: str
    transfer_class: BridgeTransferClass
    token_required: bool
    source_preconditions: tuple[str, ...]
    destination_preconditions: tuple[str, ...]
    persistence_required: bool
    transaction_required: bool
    idempotency_policy: BridgeIdempotencyPolicy
    timeout_seconds: int
    retry_policy: str
    failure_policy: str
    recovery_policy: str
    audit_policy: str
    enabled: bool
    requirement_class: BridgeRequirementClass
    implementation_status: BridgeImplementationStatus
    certification_status: BridgeCertificationStatus
    deprecated: bool = False
    schema_version: str = EO_DK_VERSION


@dataclass(frozen=True)
class BridgeExecutionRequest:
    execution_id: str
    bridge_id: str
    bridge_version: str
    runtime_instance_id: str
    workflow_id: str
    workflow_type: str
    proof_domain: str
    correlation_id: str
    causation_id: str
    source_office: str
    destination_office: str
    current_token_id: str
    current_owner: str
    proposed_next_owner: str
    artifact_type: str
    artifact_id: str
    artifact_hash: str
    input_manifest_id: str
    requested_at_utc: str
    source_state: str
    required_destination_state: str
    idempotency_key: str
    policy_versions: tuple[str, ...]
    persistence_references: tuple[str, ...]
    payload: dict[str, Any]
    schema_version: str = EO_DK_VERSION


@dataclass(frozen=True)
class BridgeExecutionResult:
    execution_id: str
    bridge_id: str
    workflow_id: str
    source: str
    destination: str
    prior_owner: str
    resulting_owner: str
    source_release_status: str
    destination_acceptance_status: str
    artifact_id: str
    durable_intent_id: str
    audit_record_ids: tuple[str, ...]
    destination_acceptance_reference: str
    persistence_reference: str
    execution_origin: str
    requested_at_utc: str
    completed_at_utc: str
    status: BridgeResultStatus
    rejection_code: BridgeRejectionCode | None
    recovery_status: str
    resulting_workflow_state: str
    deterministic_result_hash: str
    schema_version: str = EO_DK_VERSION


class CanonicalBridgeRegistry:
    def __init__(self, definitions: tuple[CanonicalBridgeDefinition, ...] | None = None) -> None:
        self._definitions: dict[str, CanonicalBridgeDefinition] = {}
        for definition in definitions or default_bridge_definitions():
            self.register(definition)

    def register(self, definition: CanonicalBridgeDefinition) -> None:
        if definition.bridge_id in self._definitions:
            raise ValueError(f"duplicate bridge id: {definition.bridge_id}")
        self._definitions[definition.bridge_id] = definition

    def get(self, bridge_id: str) -> CanonicalBridgeDefinition | None:
        return self._definitions.get(bridge_id)

    def all(self) -> tuple[CanonicalBridgeDefinition, ...]:
        return tuple(self._definitions.values())


class WorkflowOwnershipLedger:
    def __init__(self) -> None:
        self._owners: dict[str, str] = {}
        self._tokens: dict[str, str] = {}
        self._released: dict[str, tuple[str, ...]] = {}

    def establish(self, workflow_id: str, owner: str, token_id: str) -> None:
        self._owners[workflow_id] = owner
        self._tokens[workflow_id] = token_id

    def owner(self, workflow_id: str) -> str:
        return self._owners.get(workflow_id, "")

    def token(self, workflow_id: str) -> str:
        return self._tokens.get(workflow_id, "")

    def transfer(self, workflow_id: str, prior_owner: str, next_owner: str, token_id: str) -> None:
        if self.owner(workflow_id) != prior_owner or self.token(workflow_id) != token_id:
            raise ValueError("invalid workflow ownership transfer")
        self._released[workflow_id] = (*self._released.get(workflow_id, ()), prior_owner)
        self._owners[workflow_id] = next_owner

    def released(self, workflow_id: str) -> tuple[str, ...]:
        return self._released.get(workflow_id, ())

    def snapshot(self) -> dict[str, Any]:
        return {"owners": dict(self._owners), "tokens": dict(self._tokens), "releasedOwners": dict(self._released)}


DestinationAcceptor = Callable[[BridgeExecutionRequest], dict[str, Any]]


class CanonicalBridgeExecutor:
    """Execute registered bridge contracts and preserve dynamic traces."""

    def __init__(self, *, runtime_instance_id: str = "canonical-runtime", registry: CanonicalBridgeRegistry | None = None, ownership: WorkflowOwnershipLedger | None = None) -> None:
        self.runtime_instance_id = runtime_instance_id
        self.registry = registry or CanonicalBridgeRegistry()
        self.ownership = ownership or WorkflowOwnershipLedger()
        self._acceptors: dict[str, DestinationAcceptor] = {}
        self._intents: dict[str, BridgeExecutionRequest] = {}
        self._results_by_idempotency: dict[str, BridgeExecutionResult] = {}
        self._audit_events: list[dict[str, Any]] = []
        self._traces: list[BridgeExecutionResult] = []

    def register_acceptor(self, bridge_id: str, acceptor: DestinationAcceptor) -> None:
        self._acceptors[bridge_id] = acceptor

    def execute(self, request: BridgeExecutionRequest) -> BridgeExecutionResult:
        definition = self.registry.get(request.bridge_id)
        if definition is None:
            return self._rejected(request, BridgeRejectionCode.BRIDGE_NOT_REGISTERED)
        if request.idempotency_key in self._results_by_idempotency:
            prior = self._results_by_idempotency[request.idempotency_key]
            if definition.idempotency_policy == BridgeIdempotencyPolicy.STRICT_ONCE:
                return self._rejected(request, BridgeRejectionCode.BRIDGE_DUPLICATE_STRICT_ONCE)
            duplicate = replace(prior, status=BridgeResultStatus.DUPLICATE_IDEMPOTENT_SUCCESS, completed_at_utc=utc_timestamp())
            self._traces.append(duplicate)
            return duplicate
        rejection = self._validate(definition, request)
        if rejection:
            return self._rejected(request, rejection)
        intent_id = f"BRIDGE-INTENT-{_hash((request.execution_id, request.idempotency_key))[:16].upper()}"
        if definition.persistence_required:
            self._intents[intent_id] = request
        self._audit("BridgeRequested", request, definition, intent_id)
        acceptor = self._acceptors.get(request.bridge_id, _default_acceptor)
        acceptance = acceptor(request)
        if not acceptance.get("accepted"):
            return self._rejected(request, BridgeRejectionCode.BRIDGE_DESTINATION_REJECTED, intent_id=intent_id)
        if not acceptance.get("acceptance_reference"):
            return self._rejected(request, BridgeRejectionCode.BRIDGE_ACCEPTANCE_EVIDENCE_MISSING, intent_id=intent_id)
        resulting_owner = request.current_owner
        source_release = "NOT_APPLICABLE"
        if definition.transfer_class == BridgeTransferClass.OWNERSHIP_TRANSFER:
            self.ownership.transfer(request.workflow_id, request.current_owner, request.proposed_next_owner, request.current_token_id)
            resulting_owner = request.proposed_next_owner
            source_release = "RELEASED_TO_DORMANT"
        elif request.workflow_id and not self.ownership.owner(request.workflow_id):
            self.ownership.establish(request.workflow_id, request.current_owner, request.current_token_id)
        result = self._result(request, definition, BridgeResultStatus.ACCEPTED, None, resulting_owner, source_release, "ACCEPTED", intent_id, "COMPLETE", acceptance_reference=str(acceptance["acceptance_reference"]))
        self._results_by_idempotency[request.idempotency_key] = result
        self._traces.append(result)
        self._audit("BridgeAccepted", request, definition, intent_id, result=result)
        return result

    def traces(self) -> tuple[BridgeExecutionResult, ...]:
        return tuple(self._traces)

    def audit_events(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._audit_events)

    def snapshot(self) -> dict[str, Any]:
        return {
            "runtimeInstanceId": self.runtime_instance_id,
            "registeredBridgeCount": len(self.registry.all()),
            "dynamicTraceCount": len(self._traces),
            "ownership": self.ownership.snapshot(),
            "traces": tuple(asdict(item) for item in self._traces),
            "auditEvents": tuple(self._audit_events),
        }

    def _validate(self, definition: CanonicalBridgeDefinition, request: BridgeExecutionRequest) -> BridgeRejectionCode | None:
        if request.runtime_instance_id != self.runtime_instance_id:
            return BridgeRejectionCode.BRIDGE_RUNTIME_MISMATCH
        if definition.deprecated or definition.requirement_class == BridgeRequirementClass.RETIRED:
            return BridgeRejectionCode.BRIDGE_RETIRED
        if definition.requirement_class == BridgeRequirementClass.PROHIBITED:
            return BridgeRejectionCode.BRIDGE_PROHIBITED
        if not definition.enabled:
            return BridgeRejectionCode.BRIDGE_DISABLED
        if request.proof_domain not in definition.allowed_proof_domains:
            return BridgeRejectionCode.BRIDGE_PROOF_DOMAIN_REJECTED
        if definition.token_required and not request.current_token_id:
            return BridgeRejectionCode.BRIDGE_TOKEN_REQUIRED
        if definition.transfer_class == BridgeTransferClass.OWNERSHIP_TRANSFER:
            if self.ownership.owner(request.workflow_id) and self.ownership.owner(request.workflow_id) != request.current_owner:
                return BridgeRejectionCode.BRIDGE_INVALID_OWNER
            if self.ownership.token(request.workflow_id) and self.ownership.token(request.workflow_id) != request.current_token_id:
                return BridgeRejectionCode.BRIDGE_TOKEN_REQUIRED
        if not request.artifact_id or not request.artifact_hash:
            return BridgeRejectionCode.BRIDGE_ARTIFACT_MISSING
        if request.artifact_hash != _hash(request.payload):
            return BridgeRejectionCode.BRIDGE_ARTIFACT_HASH_MISMATCH
        if definition.persistence_required and definition.transfer_class in {BridgeTransferClass.EXTERNAL_EXECUTION, BridgeTransferClass.OWNERSHIP_TRANSFER} and request.idempotency_key == "":
            return BridgeRejectionCode.BRIDGE_PERSISTENCE_REQUIRED
        return None

    def _rejected(self, request: BridgeExecutionRequest, code: BridgeRejectionCode, *, intent_id: str = "") -> BridgeExecutionResult:
        result = self._result(request, None, BridgeResultStatus.REJECTED, code, request.current_owner, "NOT_RELEASED", "REJECTED", intent_id, "UNCHANGED")
        self._traces.append(result)
        self._audit("BridgeRejected", request, None, intent_id, result=result)
        return result

    def _result(
        self,
        request: BridgeExecutionRequest,
        definition: CanonicalBridgeDefinition | None,
        status: BridgeResultStatus,
        code: BridgeRejectionCode | None,
        resulting_owner: str,
        source_release: str,
        destination_acceptance: str,
        intent_id: str,
        workflow_state: str,
        acceptance_reference: str = "",
    ) -> BridgeExecutionResult:
        payload = {
            "execution_id": request.execution_id,
            "bridge_id": request.bridge_id,
            "workflow_id": request.workflow_id,
            "status": status.value,
            "code": code.value if code else "",
            "owner": resulting_owner,
            "artifact_id": request.artifact_id,
        }
        return BridgeExecutionResult(
            request.execution_id,
            request.bridge_id,
            request.workflow_id,
            request.source_office,
            request.destination_office,
            request.current_owner,
            resulting_owner,
            source_release,
            destination_acceptance,
            request.artifact_id,
            intent_id,
            (f"AUD-{_hash(payload)[:12].upper()}",),
            acceptance_reference,
            intent_id,
            "CANONICAL_RUNTIME",
            request.requested_at_utc,
            utc_timestamp(),
            status,
            code,
            definition.recovery_policy if definition else "REVIEW_REQUIRED",
            workflow_state,
            _hash(payload),
        )

    def _audit(self, event_type: str, request: BridgeExecutionRequest, definition: CanonicalBridgeDefinition | None, intent_id: str, *, result: BridgeExecutionResult | None = None) -> None:
        self._audit_events.append(
            {
                "eventType": event_type,
                "eventId": f"EO-DK-AUD-{len(self._audit_events) + 1:06d}",
                "timestampUtc": utc_timestamp(),
                "bridgeId": request.bridge_id,
                "executionId": request.execution_id,
                "workflowId": request.workflow_id,
                "source": request.source_office,
                "destination": request.destination_office,
                "transferClass": definition.transfer_class.value if definition else "",
                "artifactId": request.artifact_id,
                "durableIntentId": intent_id,
                "resultStatus": result.status.value if result else "",
                "rejectionCode": result.rejection_code.value if result and result.rejection_code else "",
            }
        )


def default_bridge_definitions() -> tuple[CanonicalBridgeDefinition, ...]:
    from .runtime_bridge_certification import BridgeCertificationState, required_runtime_bridge_matrix

    definitions = []
    ownership_ids = {"BRIDGE-MISSION-WORKFLOW-001", "BRIDGE-WORKFLOW-OFFICE-001", "BRIDGE-SEEKER-ANALYST-001", "BRIDGE-ANALYST-RISK-001", "BRIDGE-AUTH-TRADER-001", "BRIDGE-EXIT-TRADER-001"}
    external_ids = {"BRIDGE-TRADER-BROKER-001", "BRIDGE-COST-API-001"}
    replay_ids = {"BRIDGE-REPLAY-LAB-001"}
    certified_states = {BridgeCertificationState.CERTIFIED_PRODUCTION, BridgeCertificationState.CONDITIONALLY_PRODUCTION}
    for bridge in required_runtime_bridge_matrix():
        requirement = BridgeRequirementClass.REPLAY_ONLY if bridge.bridge_id in replay_ids else BridgeRequirementClass.REQUIRED_PRODUCTION
        transfer = BridgeTransferClass.OWNERSHIP_TRANSFER if bridge.bridge_id in ownership_ids else BridgeTransferClass.EXTERNAL_EXECUTION if bridge.bridge_id in external_ids else BridgeTransferClass.INFORMATION_DELIVERY
        certification = BridgeCertificationStatus.CONDITIONALLY_PRODUCTION if bridge.certification_state in certified_states else BridgeCertificationStatus.STATICALLY_VALIDATED if bridge.certification_state != BridgeCertificationState.MISSING else BridgeCertificationStatus.UNCERTIFIED
        implementation = BridgeImplementationStatus.IMPLEMENTED if bridge.certification_state in certified_states else BridgeImplementationStatus.PARTIAL
        definitions.append(
            CanonicalBridgeDefinition(
                bridge.bridge_id,
                bridge.name,
                EO_DK_VERSION,
                bridge.source_authority,
                bridge.target_authority,
                ("paper", "proof", "replay"),
                ("REPLAY",) if bridge.bridge_id in replay_ids else bridge.truth_domains or ("PAPER",),
                bridge.payload_schema,
                bridge.payload_schema,
                bridge.schema_version,
                transfer,
                transfer == BridgeTransferClass.OWNERSHIP_TRANSFER,
                bridge.source_preconditions,
                bridge.target_preconditions,
                bridge.persistence_behavior != "none",
                bool(bridge.eodd_transaction_requirement),
                BridgeIdempotencyPolicy.NON_RETRYABLE_FINANCIAL if bridge.eodd_transaction_requirement else BridgeIdempotencyPolicy.IDEMPOTENT_REPLAY,
                30,
                bridge.retry_behavior,
                bridge.timeout_behavior,
                bridge.recovery_behavior,
                "emit request and result audit records",
                True,
                requirement,
                implementation,
                certification,
            )
        )
    return tuple(definitions)


def make_bridge_request(
    *,
    bridge_id: str,
    runtime_instance_id: str,
    workflow_id: str,
    source: str,
    destination: str,
    artifact_id: str,
    payload: dict[str, Any],
    current_owner: str,
    next_owner: str = "",
    token_id: str = "",
    proof_domain: str = "PAPER",
    workflow_type: str = "paper",
    transfer_version: str = EO_DK_VERSION,
) -> BridgeExecutionRequest:
    return BridgeExecutionRequest(
        f"EO-DK-EXEC-{_hash((bridge_id, workflow_id, artifact_id, token_id))[:12].upper()}",
        bridge_id,
        transfer_version,
        runtime_instance_id,
        workflow_id,
        workflow_type,
        proof_domain,
        f"CORR-{_hash((workflow_id, bridge_id))[:10].upper()}",
        "",
        source,
        destination,
        token_id,
        current_owner,
        next_owner or current_owner,
        "artifact_reference",
        artifact_id,
        _hash(payload),
        f"MANIFEST-{_hash(payload)[:12].upper()}",
        utc_timestamp(),
        "ACTIVE",
        "DORMANT",
        _hash((bridge_id, workflow_id, artifact_id, token_id)),
        (EO_DK_VERSION,),
        (),
        payload,
    )


def bridge_inventory() -> tuple[dict[str, Any], ...]:
    return tuple(asdict(item) for item in default_bridge_definitions())


def _default_acceptor(request: BridgeExecutionRequest) -> dict[str, Any]:
    return {
        "accepted": True,
        "destination": request.destination_office,
        "artifact_id": request.artifact_id,
        "acceptance_reference": f"ACCEPT-{_hash((request.bridge_id, request.workflow_id, request.artifact_id))[:12].upper()}",
    }


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
