"""EO-DL office lifecycle and orphan-closure model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .canonical_bridge_fabric import BridgeTransferClass, CanonicalBridgeExecutor, make_bridge_request
EO_DL_VERSION = "EO-DL.1"


class OfficeClassification(str, Enum):
    CORE_PRODUCTION = "CORE_PRODUCTION"
    OPTIONAL_PRODUCTION = "OPTIONAL_PRODUCTION"
    INFORMATION_ONLY = "INFORMATION_ONLY"
    EXTERNAL_AUTHORITY_ADAPTER = "EXTERNAL_AUTHORITY_ADAPTER"
    REPLAY_ONLY = "REPLAY_ONLY"
    TEST_ONLY = "TEST_ONLY"
    DEVELOPMENT_ONLY = "DEVELOPMENT_ONLY"
    FUTURE_RESERVED = "FUTURE_RESERVED"
    RETIRED = "RETIRED"
    PROHIBITED = "PROHIBITED"
    UNRESOLVED = "UNRESOLVED"


class OfficeLifecycleState(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    DORMANT = "DORMANT"
    ACTIVATION_PENDING = "ACTIVATION_PENDING"
    ACTIVE = "ACTIVE"
    HANDOFF_PENDING = "HANDOFF_PENDING"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    SUSPENDED = "SUSPENDED"
    RECOVERY_PENDING = "RECOVERY_PENDING"
    QUARANTINED = "QUARANTINED"
    RETIRING = "RETIRING"
    RETIRED = "RETIRED"
    FAILED = "FAILED"


class OfficeActivationAuthority(str, Enum):
    CANONICAL_BRIDGE = "CANONICAL_BRIDGE"
    SCHEDULER = "SCHEDULER"
    DUTY_OFFICER = "DUTY_OFFICER"
    COMMANDER = "COMMANDER"
    RECOVERY = "RECOVERY"
    REPLAY_HARNESS = "REPLAY_HARNESS"
    TEST_HARNESS = "TEST_HARNESS"


class OfficeCertificationStatus(str, Enum):
    UNCERTIFIED = "UNCERTIFIED"
    STATICALLY_VALIDATED = "STATICALLY_VALIDATED"
    DYNAMICALLY_TRACED = "DYNAMICALLY_TRACED"
    CONDITIONALLY_PRODUCTION = "CONDITIONALLY_PRODUCTION"
    CERTIFIED_PRODUCTION = "CERTIFIED_PRODUCTION"
    REPLAY_CERTIFIED = "REPLAY_CERTIFIED"
    TEST_ONLY_VALIDATED = "TEST_ONLY_VALIDATED"
    RETIRED_CONFIRMED = "RETIRED_CONFIRMED"
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"


class OfficeRejectionCode(str, Enum):
    OFFICE_NOT_REGISTERED = "OFFICE_NOT_REGISTERED"
    OFFICE_RETIRED = "OFFICE_RETIRED"
    OFFICE_PROHIBITED = "OFFICE_PROHIBITED"
    OFFICE_FUTURE_RESERVED = "OFFICE_FUTURE_RESERVED"
    OFFICE_INVALID_ACTIVATION_AUTHORITY = "OFFICE_INVALID_ACTIVATION_AUTHORITY"
    OFFICE_TOKEN_REQUIRED = "OFFICE_TOKEN_REQUIRED"
    OFFICE_WRONG_OWNER = "OFFICE_WRONG_OWNER"
    OFFICE_DORMANT_MUTATION_REJECTED = "OFFICE_DORMANT_MUTATION_REJECTED"
    OFFICE_INVALID_TRANSITION = "OFFICE_INVALID_TRANSITION"


@dataclass(frozen=True)
class OfficeDefinition:
    office_id: str
    office_name: str
    office_version: str
    implementation_path: str
    classification: OfficeClassification
    constitutional_role: str
    allowed_workflow_types: tuple[str, ...]
    allowed_proof_domains: tuple[str, ...]
    ownership_bearing: bool
    allowed_activation_authorities: tuple[OfficeActivationAuthority, ...]
    ingress_bridges: tuple[str, ...]
    egress_bridges: tuple[str, ...]
    information_subscriptions: tuple[str, ...]
    required_dependencies: tuple[str, ...]
    persistence_required: bool
    recovery_required: bool
    default_state: OfficeLifecycleState
    background_activity_policy: str
    multiplicity_policy: str
    enabled: bool
    production_required: bool
    retirement_status: str = ""
    schema_version: str = EO_DL_VERSION


@dataclass(frozen=True)
class OfficeStateRecord:
    office_id: str
    state: OfficeLifecycleState
    workflow_id: str
    token_id: str
    owner: str
    proof_domain: str
    last_transition_at_utc: str
    activation_authority: str = ""
    rejection_code: OfficeRejectionCode | None = None


@dataclass(frozen=True)
class OfficeActivationResult:
    accepted: bool
    office_id: str
    state: OfficeLifecycleState
    workflow_id: str
    rejection_code: OfficeRejectionCode | None
    message: str


class OfficeRegistry:
    def __init__(self, definitions: tuple[OfficeDefinition, ...] | None = None) -> None:
        self._definitions: dict[str, OfficeDefinition] = {}
        for definition in definitions or default_office_definitions():
            self.register(definition)

    def register(self, definition: OfficeDefinition) -> None:
        if definition.office_id in self._definitions:
            raise ValueError(f"duplicate office id: {definition.office_id}")
        if definition.classification == OfficeClassification.PROHIBITED and definition.enabled:
            raise ValueError(f"prohibited office cannot be enabled: {definition.office_id}")
        self._definitions[definition.office_id] = definition

    def get(self, office_id: str) -> OfficeDefinition | None:
        return self._definitions.get(office_id)

    def all(self) -> tuple[OfficeDefinition, ...]:
        return tuple(self._definitions.values())


class OfficeLifecycleController:
    """Validate activation, handoff, Dormancy, retirement, and read safety."""

    def __init__(self, *, registry: OfficeRegistry | None = None, bridge_executor: CanonicalBridgeExecutor | None = None) -> None:
        self.registry = registry or OfficeRegistry()
        self.bridge_executor = bridge_executor or CanonicalBridgeExecutor()
        self._states: dict[str, OfficeStateRecord] = {
            definition.office_id: OfficeStateRecord(definition.office_id, definition.default_state, "", "", "", "", utc_timestamp())
            for definition in self.registry.all()
        }
        self._history: list[dict[str, Any]] = []

    def activate(
        self,
        office_id: str,
        *,
        authority: OfficeActivationAuthority,
        workflow_id: str = "",
        token_id: str = "",
        current_owner: str = "",
        proof_domain: str = "PAPER",
    ) -> OfficeActivationResult:
        definition = self.registry.get(office_id)
        if definition is None:
            return self._activation(False, office_id, OfficeLifecycleState.FAILED, workflow_id, OfficeRejectionCode.OFFICE_NOT_REGISTERED, "office is not registered")
        rejection = self._activation_rejection(definition, authority, workflow_id, token_id, current_owner)
        if rejection:
            state = OfficeLifecycleState.RETIRED if rejection == OfficeRejectionCode.OFFICE_RETIRED else OfficeLifecycleState.QUARANTINED
            self._set_state(office_id, state, workflow_id, token_id, current_owner, proof_domain, authority, rejection)
            return self._activation(False, office_id, state, workflow_id, rejection, rejection.value)
        self._set_state(office_id, OfficeLifecycleState.ACTIVATION_PENDING, workflow_id, token_id, current_owner, proof_domain, authority, None)
        self._set_state(office_id, OfficeLifecycleState.ACTIVE, workflow_id, token_id, current_owner, proof_domain, authority, None)
        return self._activation(True, office_id, OfficeLifecycleState.ACTIVE, workflow_id, None, "office activated")

    def deliver_information(self, office_id: str, *, workflow_id: str, artifact_id: str, payload: dict[str, Any]) -> OfficeActivationResult:
        definition = self.registry.get(office_id)
        if definition is None:
            return self._activation(False, office_id, OfficeLifecycleState.FAILED, workflow_id, OfficeRejectionCode.OFFICE_NOT_REGISTERED, "office is not registered")
        if definition.ownership_bearing:
            return self._activation(False, office_id, self.state(office_id).state, workflow_id, OfficeRejectionCode.OFFICE_INVALID_ACTIVATION_AUTHORITY, "information delivery cannot activate ownership")
        self._history.append({"event": "InformationDelivered", "officeId": office_id, "workflowId": workflow_id, "artifactId": artifact_id, "payloadHash": _hash(payload), "timestampUtc": utc_timestamp()})
        return self._activation(True, office_id, self.state(office_id).state, workflow_id, None, "information delivered without ownership transfer")

    def handoff_to_dormant(self, office_id: str, *, bridge_id: str, workflow_id: str, token_id: str, next_owner: str, artifact_id: str, payload: dict[str, Any]) -> OfficeActivationResult:
        current = self.state(office_id)
        definition = self.registry.get(office_id)
        if definition is None:
            return self._activation(False, office_id, OfficeLifecycleState.FAILED, workflow_id, OfficeRejectionCode.OFFICE_NOT_REGISTERED, "office is not registered")
        if current.state != OfficeLifecycleState.ACTIVE:
            return self._activation(False, office_id, current.state, workflow_id, OfficeRejectionCode.OFFICE_INVALID_TRANSITION, "handoff requires active source")
        self._set_state(office_id, OfficeLifecycleState.HANDOFF_PENDING, workflow_id, token_id, current.owner, current.proof_domain, OfficeActivationAuthority.CANONICAL_BRIDGE, None)
        request = make_bridge_request(bridge_id=bridge_id, runtime_instance_id=self.bridge_executor.runtime_instance_id, workflow_id=workflow_id, source=office_id, destination=next_owner, artifact_id=artifact_id, payload=payload, current_owner=current.owner or office_id, next_owner=next_owner, token_id=token_id, proof_domain=current.proof_domain or "PAPER")
        result = self.bridge_executor.execute(request)
        if result.status.value != "ACCEPTED":
            self._set_state(office_id, OfficeLifecycleState.QUARANTINED, workflow_id, token_id, current.owner, current.proof_domain, OfficeActivationAuthority.CANONICAL_BRIDGE, OfficeRejectionCode.OFFICE_INVALID_TRANSITION)
            return self._activation(False, office_id, OfficeLifecycleState.QUARANTINED, workflow_id, OfficeRejectionCode.OFFICE_INVALID_TRANSITION, "bridge handoff failed")
        self._set_state(office_id, OfficeLifecycleState.DORMANT, workflow_id, "", "", current.proof_domain, OfficeActivationAuthority.CANONICAL_BRIDGE, None)
        return self._activation(True, office_id, OfficeLifecycleState.DORMANT, workflow_id, None, "source returned to Dormant")

    def reject_dormant_mutation(self, office_id: str, action: str) -> OfficeActivationResult:
        current = self.state(office_id)
        if current.state == OfficeLifecycleState.DORMANT:
            return self._activation(False, office_id, current.state, current.workflow_id, OfficeRejectionCode.OFFICE_DORMANT_MUTATION_REJECTED, f"Dormant office cannot {action}")
        return self._activation(True, office_id, current.state, current.workflow_id, None, "action permitted by active state")

    def transition(self, office_id: str, state: OfficeLifecycleState) -> OfficeActivationResult:
        current = self.state(office_id)
        if state not in permitted_transitions(current.state):
            return self._activation(False, office_id, current.state, current.workflow_id, OfficeRejectionCode.OFFICE_INVALID_TRANSITION, "invalid lifecycle transition")
        self._set_state(office_id, state, current.workflow_id, current.token_id, current.owner, current.proof_domain, OfficeActivationAuthority.COMMANDER, None)
        return self._activation(True, office_id, state, current.workflow_id, None, "transition accepted")

    def state(self, office_id: str) -> OfficeStateRecord:
        return self._states.get(office_id, OfficeStateRecord(office_id, OfficeLifecycleState.UNINITIALIZED, "", "", "", "", utc_timestamp()))

    def read_only_snapshot(self) -> dict[str, Any]:
        return {"offices": tuple(asdict(item) for item in self._states.values()), "historyDepth": len(self._history)}

    def orphan_analysis(self) -> tuple[dict[str, Any], ...]:
        rows = []
        for definition in self.registry.all():
            reasons = []
            if definition.production_required and not definition.ingress_bridges and OfficeActivationAuthority.SCHEDULER not in definition.allowed_activation_authorities and OfficeActivationAuthority.COMMANDER not in definition.allowed_activation_authorities:
                reasons.append("missing legitimate production ingress")
            if definition.production_required and not definition.egress_bridges and definition.classification not in {OfficeClassification.INFORMATION_ONLY, OfficeClassification.EXTERNAL_AUTHORITY_ADAPTER}:
                reasons.append("missing egress or terminal classification")
            if definition.classification in {OfficeClassification.FUTURE_RESERVED, OfficeClassification.UNRESOLVED}:
                reasons.append(f"{definition.classification.value.lower()} readiness blocker")
            rows.append({"office_id": definition.office_id, "orphan": bool(reasons), "reasons": tuple(reasons), "classification": definition.classification.value})
        return tuple(rows)

    def certification_matrix(self) -> tuple[dict[str, Any], ...]:
        traced = {item.get("officeId") for item in self._history}
        rows = []
        for definition in self.registry.all():
            orphan = next(item for item in self.orphan_analysis() if item["office_id"] == definition.office_id)
            if definition.classification == OfficeClassification.RETIRED:
                status = OfficeCertificationStatus.RETIRED_CONFIRMED
            elif orphan["orphan"]:
                status = OfficeCertificationStatus.UNCERTIFIED
            elif definition.office_id in traced:
                status = OfficeCertificationStatus.DYNAMICALLY_TRACED
            else:
                status = OfficeCertificationStatus.STATICALLY_VALIDATED
            rows.append({"office_id": definition.office_id, "classification": definition.classification.value, "certification_status": status.value, "orphan": orphan["orphan"]})
        return tuple(rows)

    def _activation_rejection(self, definition: OfficeDefinition, authority: OfficeActivationAuthority, workflow_id: str, token_id: str, current_owner: str) -> OfficeRejectionCode | None:
        if definition.classification == OfficeClassification.RETIRED:
            return OfficeRejectionCode.OFFICE_RETIRED
        if definition.classification == OfficeClassification.PROHIBITED:
            return OfficeRejectionCode.OFFICE_PROHIBITED
        if definition.classification == OfficeClassification.FUTURE_RESERVED:
            return OfficeRejectionCode.OFFICE_FUTURE_RESERVED
        if authority not in definition.allowed_activation_authorities:
            return OfficeRejectionCode.OFFICE_INVALID_ACTIVATION_AUTHORITY
        if definition.ownership_bearing and not token_id:
            return OfficeRejectionCode.OFFICE_TOKEN_REQUIRED
        if definition.ownership_bearing and current_owner and current_owner != definition.office_id:
            return OfficeRejectionCode.OFFICE_WRONG_OWNER
        return None

    def _set_state(self, office_id: str, state: OfficeLifecycleState, workflow_id: str, token_id: str, owner: str, proof_domain: str, authority: OfficeActivationAuthority, rejection: OfficeRejectionCode | None) -> None:
        self._states[office_id] = OfficeStateRecord(office_id, state, workflow_id, token_id, owner, proof_domain, utc_timestamp(), authority.value, rejection)
        self._history.append({"event": "OfficeStateTransition", "officeId": office_id, "state": state.value, "workflowId": workflow_id, "authority": authority.value, "rejectionCode": rejection.value if rejection else "", "timestampUtc": utc_timestamp()})

    def _activation(self, accepted: bool, office_id: str, state: OfficeLifecycleState, workflow_id: str, code: OfficeRejectionCode | None, message: str) -> OfficeActivationResult:
        return OfficeActivationResult(accepted, office_id, state, workflow_id, code, message)


def permitted_transitions(state: OfficeLifecycleState) -> tuple[OfficeLifecycleState, ...]:
    return {
        OfficeLifecycleState.UNINITIALIZED: (OfficeLifecycleState.DORMANT, OfficeLifecycleState.FAILED),
        OfficeLifecycleState.DORMANT: (OfficeLifecycleState.ACTIVATION_PENDING, OfficeLifecycleState.RETIRING, OfficeLifecycleState.SUSPENDED),
        OfficeLifecycleState.ACTIVATION_PENDING: (OfficeLifecycleState.ACTIVE, OfficeLifecycleState.QUARANTINED, OfficeLifecycleState.FAILED),
        OfficeLifecycleState.ACTIVE: (OfficeLifecycleState.HANDOFF_PENDING, OfficeLifecycleState.WAITING_EXTERNAL, OfficeLifecycleState.SUSPENDED, OfficeLifecycleState.QUARANTINED, OfficeLifecycleState.DORMANT),
        OfficeLifecycleState.HANDOFF_PENDING: (OfficeLifecycleState.DORMANT, OfficeLifecycleState.QUARANTINED, OfficeLifecycleState.RECOVERY_PENDING),
        OfficeLifecycleState.WAITING_EXTERNAL: (OfficeLifecycleState.ACTIVE, OfficeLifecycleState.RECOVERY_PENDING, OfficeLifecycleState.QUARANTINED),
        OfficeLifecycleState.SUSPENDED: (OfficeLifecycleState.ACTIVATION_PENDING, OfficeLifecycleState.RETIRED),
        OfficeLifecycleState.RECOVERY_PENDING: (OfficeLifecycleState.DORMANT, OfficeLifecycleState.QUARANTINED, OfficeLifecycleState.FAILED),
        OfficeLifecycleState.QUARANTINED: (OfficeLifecycleState.RECOVERY_PENDING, OfficeLifecycleState.RETIRED),
        OfficeLifecycleState.RETIRING: (OfficeLifecycleState.RETIRED,),
        OfficeLifecycleState.RETIRED: (),
        OfficeLifecycleState.FAILED: (OfficeLifecycleState.RECOVERY_PENDING, OfficeLifecycleState.RETIRED),
    }[state]


def default_office_definitions() -> tuple[OfficeDefinition, ...]:
    from .runtime_bridge_certification import office_inventory

    rows = []
    core = {"scheduler", "mission_planner", "workflow_orchestrator", "Strategic Intelligence", "Seeker", "Analyst", "Risk", "Trader", "Paper Broker", "Position Registry", "Performance Truth", "Historian"}
    adapters = {"Paper Broker", "API Execution Gateway", "Market Data"}
    for item in office_inventory():
        office_id = item.office_id
        name = item.office_name
        classification = OfficeClassification.CORE_PRODUCTION if name in core or office_id in core else OfficeClassification.INFORMATION_ONLY
        if name in adapters:
            classification = OfficeClassification.EXTERNAL_AUTHORITY_ADAPTER
        if item.current_status.value == "MISSING":
            classification = OfficeClassification.UNRESOLVED
        ownership = classification == OfficeClassification.CORE_PRODUCTION and name not in {"Performance Truth", "Historian"}
        rows.append(
            OfficeDefinition(
                office_id,
                name,
                EO_DL_VERSION,
                _implementation_path(name),
                classification,
                item.constitutional_purpose,
                ("paper", "proof", "replay"),
                ("PAPER", "PROOF", "REPLAY"),
                ownership,
                (OfficeActivationAuthority.CANONICAL_BRIDGE, OfficeActivationAuthority.SCHEDULER, OfficeActivationAuthority.COMMANDER),
                item.inbound_bridges,
                item.outbound_bridges,
                (),
                (),
                False,
                True,
                OfficeLifecycleState.DORMANT,
                "no autonomous work while Dormant",
                "singleton",
                classification not in {OfficeClassification.RETIRED, OfficeClassification.PROHIBITED, OfficeClassification.FUTURE_RESERVED},
                classification == OfficeClassification.CORE_PRODUCTION,
            )
        )
    rows.append(
        OfficeDefinition(
            "OFFICE-FUTURE-EO-DM",
            "EO-DM Position Lifecycle Completion",
            EO_DL_VERSION,
            "future",
            OfficeClassification.FUTURE_RESERVED,
            "Reserved endpoint for later full position lifecycle closure.",
            ("paper",),
            ("PAPER",),
            True,
            (),
            (),
            (),
            (),
            (),
            True,
            True,
            OfficeLifecycleState.DORMANT,
            "no production activation",
            "singleton",
            False,
            False,
        )
    )
    return tuple(rows)


def office_component_inventory(repo_root: str | Path = ".") -> tuple[dict[str, Any], ...]:
    root = Path(repo_root)
    rows = []
    for path in sorted((root / "src" / "argos").rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(term in text for term in ("Office", "Engine", "Authority", "Gateway", "Registry", "Manager", "Coordinator", "Broker", "Historian", "Academy", "Commander")):
            rows.append({"path": str(path.relative_to(root)).replace("\\", "/"), "component_marker": True, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})
    return tuple(rows)


def duplicate_role_analysis(definitions: tuple[OfficeDefinition, ...] | None = None) -> tuple[dict[str, Any], ...]:
    definitions = definitions or default_office_definitions()
    by_role: dict[str, list[str]] = {}
    for definition in definitions:
        key = definition.constitutional_role.lower().split(".")[0][:80]
        by_role.setdefault(key, []).append(definition.office_id)
    return tuple({"role": role, "office_ids": tuple(ids), "duplicate": len(ids) > 1} for role, ids in by_role.items() if len(ids) > 1)


def _implementation_path(name: str) -> str:
    slug = name.lower().replace(" ", "_").replace("-", "_")
    return f"src/argos/control_panel/{slug}.py"


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
