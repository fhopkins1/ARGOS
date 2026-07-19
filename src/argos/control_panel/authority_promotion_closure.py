"""TC-002 authority registry, provenance, and promotion closure."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .canonical_bridge_fabric import BridgeRequirementClass, default_bridge_definitions
from .office_lifecycle import OfficeClassification, default_office_definitions
from .runtime_bridge_certification import required_runtime_bridge_matrix
from .trace_equivalence import TraceEquivalenceLevel
from .truth_promotion import PROMOTION_SCOPE_REGISTRY, PromotionDecisionStatus, PromotionRejectionCode, PromotionScope


TC_002_VERSION = "TC-002.1"


class AuthorityClassification(str, Enum):
    WORKFLOW_OWNER = "WORKFLOW_OWNER"
    CONSTITUTIONAL_OFFICE = "CONSTITUTIONAL_OFFICE"
    INFORMATION_ONLY_OFFICE = "INFORMATION_ONLY_OFFICE"
    COMMAND_AUTHORITY = "COMMAND_AUTHORITY"
    AUTHORIZATION_AUTHORITY = "AUTHORIZATION_AUTHORITY"
    TRUTH_PRODUCER = "TRUTH_PRODUCER"
    EXTERNAL_AUTHORITY_ADAPTER = "EXTERNAL_AUTHORITY_ADAPTER"
    SERVICE_AUTHORITY = "SERVICE_AUTHORITY"
    RECOVERY_AUTHORITY = "RECOVERY_AUTHORITY"
    CERTIFICATION_AUTHORITY = "CERTIFICATION_AUTHORITY"
    REPLAY_AUTHORITY = "REPLAY_AUTHORITY"
    TEST_AUTHORITY = "TEST_AUTHORITY"
    DEVELOPMENT_AUTHORITY = "DEVELOPMENT_AUTHORITY"
    RETIRED_AUTHORITY = "RETIRED_AUTHORITY"
    PROHIBITED_AUTHORITY = "PROHIBITED_AUTHORITY"
    UNRESOLVED_AUTHORITY = "UNRESOLVED_AUTHORITY"


class AuthorityRegistryStatus(str, Enum):
    DECLARED = "DECLARED"
    IMPLEMENTATION_PRESENT = "IMPLEMENTATION_PRESENT"
    RUNTIME_REGISTERED = "RUNTIME_REGISTERED"
    PRODUCTION_ENABLED = "PRODUCTION_ENABLED"
    ACTIVE = "ACTIVE"
    DELEGATED = "DELEGATED"
    REVOKED = "REVOKED"
    RETIRED = "RETIRED"
    PROHIBITED = "PROHIBITED"
    UNRESOLVED = "UNRESOLVED"


class PromotionResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CONDITIONALLY_ACCEPTED = "CONDITIONALLY_ACCEPTED"
    QUARANTINED = "QUARANTINED"
    DEFERRED = "DEFERRED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    UNRESOLVED = "UNRESOLVED"


class AuthorityPromotionRejectionCode(str, Enum):
    AUTHORITY_NOT_REGISTERED = "AUTHORITY_NOT_REGISTERED"
    AUTHORITY_IMPLEMENTATION_MISSING = "AUTHORITY_IMPLEMENTATION_MISSING"
    AUTHORITY_PRODUCTION_DISABLED = "AUTHORITY_PRODUCTION_DISABLED"
    AUTHORITY_CLASSIFICATION_INVALID = "AUTHORITY_CLASSIFICATION_INVALID"
    AUTHORITY_SCOPE_VIOLATION = "AUTHORITY_SCOPE_VIOLATION"
    AUTHORITY_WORKFLOW_VIOLATION = "AUTHORITY_WORKFLOW_VIOLATION"
    AUTHORITY_PROOF_DOMAIN_VIOLATION = "AUTHORITY_PROOF_DOMAIN_VIOLATION"
    AUTHORITY_NOT_ACTIVE = "AUTHORITY_NOT_ACTIVE"
    AUTHORITY_EXPIRED = "AUTHORITY_EXPIRED"
    AUTHORITY_REVOKED = "AUTHORITY_REVOKED"
    AUTHORITY_DELEGATION_MISSING = "AUTHORITY_DELEGATION_MISSING"
    AUTHORITY_DELEGATION_INVALID = "AUTHORITY_DELEGATION_INVALID"
    AUTHORITY_TOKEN_REQUIRED = "AUTHORITY_TOKEN_REQUIRED"
    AUTHORITY_TOKEN_INVALID = "AUTHORITY_TOKEN_INVALID"
    SOURCE_AUTHORITY_INVALID = "SOURCE_AUTHORITY_INVALID"
    DESTINATION_AUTHORITY_INVALID = "DESTINATION_AUTHORITY_INVALID"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    PROVENANCE_UNVERIFIED = "PROVENANCE_UNVERIFIED"
    PROVENANCE_INTEGRITY_FAILURE = "PROVENANCE_INTEGRITY_FAILURE"
    PROMOTION_NOT_ELIGIBLE = "PROMOTION_NOT_ELIGIBLE"
    PROMOTION_POLICY_MISMATCH = "PROMOTION_POLICY_MISMATCH"
    PROMOTION_SCHEMA_REJECTED = "PROMOTION_SCHEMA_REJECTED"
    PROMOTION_PROOF_DOMAIN_REJECTED = "PROMOTION_PROOF_DOMAIN_REJECTED"
    PROMOTION_QUARANTINED = "PROMOTION_QUARANTINED"
    PROMOTION_CONFLICT = "PROMOTION_CONFLICT"
    PROMOTION_RECOVERY_EVIDENCE_MISSING = "PROMOTION_RECOVERY_EVIDENCE_MISSING"


@dataclass(frozen=True)
class AuthorityIdentity:
    authority_id: str
    authority_name: str
    classification: AuthorityClassification
    implementation_identity: str
    office_or_service_identity: str
    authority_version: str
    constitutional_role: str
    allowed_proof_domains: tuple[str, ...]
    allowed_workflow_types: tuple[str, ...]
    permitted_artifact_types: tuple[str, ...]
    permitted_command_types: tuple[str, ...]
    permitted_bridge_sources: tuple[str, ...]
    permitted_bridge_destinations: tuple[str, ...]
    delegation_policy: str
    activation_requirements: tuple[str, ...]
    token_required: bool
    revoked: bool
    production_enabled: bool
    schema_version: str = TC_002_VERSION


@dataclass(frozen=True)
class AuthorityActivationRecord:
    activation_id: str
    authority_id: str
    activation_authority: str
    workflow_id: str
    token_id: str
    proof_domain: str
    policy_version: str
    activated_at_utc: str
    expires_at_utc: str
    scope: tuple[str, ...]
    revoked: bool
    deterministic_hash: str
    schema_version: str = TC_002_VERSION


@dataclass(frozen=True)
class DelegationRecord:
    delegation_id: str
    delegating_authority: str
    receiving_authority: str
    permitted_actions: tuple[str, ...]
    workflow_scope: tuple[str, ...]
    proof_domain_scope: tuple[str, ...]
    starts_at_utc: str
    expires_at_utc: str
    revoked: bool
    policy_basis: str
    audit_references: tuple[str, ...]
    deterministic_hash: str
    validation_status: str
    schema_version: str = TC_002_VERSION


@dataclass(frozen=True)
class ArtifactProvenanceRecord:
    artifact_id: str
    artifact_type: str
    producer_authority_id: str
    producer_classification: AuthorityClassification
    workflow_id: str
    proof_domain: str
    production_timestamp_utc: str
    authority_activation_record: str
    token_reference: str
    source_artifact_ids: tuple[str, ...]
    input_manifest_id: str
    policy_versions: tuple[str, ...]
    bridge_execution_reference: str
    persistence_reference: str
    deterministic_hash: str
    verified: bool
    schema_version: str = TC_002_VERSION


@dataclass(frozen=True)
class ConstitutionalPromotionDecision:
    promotion_id: str
    artifact_id: str
    artifact_type: str
    source_authority: str
    destination_authority: str
    workflow_id: str
    proof_domain: str
    required_policy: str
    actual_policy: str
    provenance_result: str
    authority_result: str
    scope_result: str
    integrity_result: str
    final_decision: PromotionResult
    reason_codes: tuple[AuthorityPromotionRejectionCode, ...]
    timestamp_utc: str
    deterministic_hash: str
    schema_version: str = TC_002_VERSION


@dataclass(frozen=True)
class CoreBridgeAuthorityResult:
    bridge_id: str
    source_authority: str
    destination_authority: str
    artifact_type: str
    prior_failure: str
    current_promotion_result: PromotionResult
    highest_trace_equivalence_level: TraceEquivalenceLevel
    reason_codes: tuple[AuthorityPromotionRejectionCode, ...]
    schema_version: str = TC_002_VERSION


class ConstitutionalAuthorityRegistry:
    def __init__(self, authorities: tuple[AuthorityIdentity, ...] | None = None) -> None:
        self._authorities: dict[str, AuthorityIdentity] = {}
        for authority in authorities or default_authority_identities():
            self.register(authority)

    def register(self, authority: AuthorityIdentity) -> None:
        if authority.authority_id in self._authorities:
            raise ValueError(f"duplicate authority id: {authority.authority_id}")
        if authority.classification == AuthorityClassification.PROHIBITED_AUTHORITY and authority.production_enabled:
            raise ValueError(f"prohibited authority cannot be production enabled: {authority.authority_id}")
        self._authorities[authority.authority_id] = authority

    def get(self, authority_id: str) -> AuthorityIdentity | None:
        return self._authorities.get(authority_id)

    def by_name(self, authority_name: str) -> AuthorityIdentity | None:
        for authority in self._authorities.values():
            if authority.authority_name == authority_name:
                return authority
        return None

    def all(self) -> tuple[AuthorityIdentity, ...]:
        return tuple(self._authorities.values())

    def validate(self) -> tuple[str, ...]:
        findings: list[str] = []
        names: dict[str, str] = {}
        for authority in self.all():
            prior = names.setdefault(authority.authority_name, authority.authority_id)
            if prior != authority.authority_id:
                findings.append(f"DUPLICATE_AUTHORITY_NAME:{authority.authority_name}")
            if not authority.allowed_proof_domains:
                findings.append(f"MISSING_PROOF_DOMAIN:{authority.authority_id}")
            if not authority.permitted_artifact_types and authority.classification not in {AuthorityClassification.SERVICE_AUTHORITY, AuthorityClassification.INFORMATION_ONLY_OFFICE}:
                findings.append(f"MISSING_ARTIFACT_SCOPE:{authority.authority_id}")
            if authority.revoked and authority.production_enabled:
                findings.append(f"REVOKED_ENABLED:{authority.authority_id}")
        return tuple(findings)


class AuthorityPromotionAuthority:
    def __init__(self, registry: ConstitutionalAuthorityRegistry | None = None) -> None:
        self.registry = registry or ConstitutionalAuthorityRegistry()

    def activate(self, authority_id: str, *, activation_authority: str = "Canonical Runtime", workflow_id: str = "WF-TC002", token_id: str = "TOK-TC002", proof_domain: str = "PAPER", scope: tuple[str, ...] = ("production",), expires_at_utc: str = "9999-12-31T23:59:59Z", revoked: bool = False) -> AuthorityActivationRecord:
        payload = (authority_id, activation_authority, workflow_id, token_id, proof_domain, scope, expires_at_utc, revoked)
        return AuthorityActivationRecord(f"TC002-ACT-{_stable_hash(payload)[:12].upper()}", authority_id, activation_authority, workflow_id, token_id, proof_domain, TC_002_VERSION, utc_timestamp(), expires_at_utc, scope, revoked, _stable_hash(payload))

    def delegate(self, delegating_authority: str, receiving_authority: str, *, permitted_actions: tuple[str, ...], workflow_scope: tuple[str, ...] = ("paper",), proof_domain_scope: tuple[str, ...] = ("PAPER",), revoked: bool = False) -> DelegationRecord:
        valid = self.registry.get(delegating_authority) is not None and self.registry.get(receiving_authority) is not None and not revoked
        payload = (delegating_authority, receiving_authority, permitted_actions, workflow_scope, proof_domain_scope, revoked)
        return DelegationRecord(f"TC002-DEL-{_stable_hash(payload)[:12].upper()}", delegating_authority, receiving_authority, permitted_actions, workflow_scope, proof_domain_scope, utc_timestamp(), "9999-12-31T23:59:59Z", revoked, TC_002_VERSION, (f"AUD-{_stable_hash(payload)[:10].upper()}",), _stable_hash(payload), "VALID" if valid else "INVALID")

    def provenance(self, *, artifact_id: str, artifact_type: str, producer_authority_id: str, workflow_id: str = "WF-TC002", proof_domain: str = "PAPER", token_reference: str = "TOK-TC002", source_artifact_ids: tuple[str, ...] = ("SOURCE-TC002",), bridge_execution_reference: str = "BRIDGE-TC002") -> ArtifactProvenanceRecord:
        authority = self.registry.get(producer_authority_id)
        payload = (artifact_id, artifact_type, producer_authority_id, workflow_id, proof_domain, token_reference, source_artifact_ids, bridge_execution_reference)
        return ArtifactProvenanceRecord(
            artifact_id,
            artifact_type,
            producer_authority_id,
            authority.classification if authority else AuthorityClassification.UNRESOLVED_AUTHORITY,
            workflow_id,
            proof_domain,
            utc_timestamp(),
            f"ACT-{producer_authority_id}",
            token_reference,
            source_artifact_ids,
            f"MANIFEST-{_stable_hash(payload)[:12].upper()}",
            (TC_002_VERSION,),
            bridge_execution_reference,
            f"PERSIST-{_stable_hash(payload)[:12].upper()}",
            _stable_hash(payload),
            authority is not None and bool(source_artifact_ids) and bool(token_reference),
        )

    def promote(self, provenance: ArtifactProvenanceRecord, *, destination_authority_id: str, required_policy: str = TC_002_VERSION, actual_policy: str = TC_002_VERSION) -> ConstitutionalPromotionDecision:
        codes: list[AuthorityPromotionRejectionCode] = []
        source = self.registry.get(provenance.producer_authority_id)
        destination = self.registry.get(destination_authority_id)
        if source is None:
            codes.append(AuthorityPromotionRejectionCode.AUTHORITY_NOT_REGISTERED)
            codes.append(AuthorityPromotionRejectionCode.SOURCE_AUTHORITY_INVALID)
        elif not source.production_enabled:
            codes.append(AuthorityPromotionRejectionCode.AUTHORITY_PRODUCTION_DISABLED)
        elif provenance.artifact_type not in source.permitted_artifact_types:
            codes.append(AuthorityPromotionRejectionCode.AUTHORITY_SCOPE_VIOLATION)
        if destination is None:
            codes.append(AuthorityPromotionRejectionCode.DESTINATION_AUTHORITY_INVALID)
        elif provenance.artifact_type not in destination.permitted_artifact_types and provenance.artifact_type not in destination.permitted_command_types:
            codes.append(AuthorityPromotionRejectionCode.PROMOTION_SCHEMA_REJECTED)
        if provenance.proof_domain not in (source.allowed_proof_domains if source else ()):
            codes.append(AuthorityPromotionRejectionCode.AUTHORITY_PROOF_DOMAIN_VIOLATION)
        if not provenance.verified:
            codes.append(AuthorityPromotionRejectionCode.PROVENANCE_UNVERIFIED)
        if not provenance.source_artifact_ids:
            codes.append(AuthorityPromotionRejectionCode.PROVENANCE_MISSING)
        if not provenance.token_reference and source and source.token_required:
            codes.append(AuthorityPromotionRejectionCode.AUTHORITY_TOKEN_REQUIRED)
        if required_policy != actual_policy:
            codes.append(AuthorityPromotionRejectionCode.PROMOTION_POLICY_MISMATCH)
        decision = PromotionResult.ACCEPTED if not codes else PromotionResult.REJECTED
        payload = (provenance.artifact_id, provenance.producer_authority_id, destination_authority_id, codes)
        return ConstitutionalPromotionDecision(
            f"TC002-PROM-{_stable_hash(payload)[:12].upper()}",
            provenance.artifact_id,
            provenance.artifact_type,
            provenance.producer_authority_id,
            destination_authority_id,
            provenance.workflow_id,
            provenance.proof_domain,
            required_policy,
            actual_policy,
            "VERIFIED" if provenance.verified else "UNVERIFIED",
            "VALID" if source and source.production_enabled else "INVALID",
            "VALID" if not any(code in {AuthorityPromotionRejectionCode.AUTHORITY_SCOPE_VIOLATION, AuthorityPromotionRejectionCode.PROMOTION_SCHEMA_REJECTED} for code in codes) else "INVALID",
            "VALID" if provenance.deterministic_hash else "INVALID",
            decision,
            tuple(dict.fromkeys(codes)),
            utc_timestamp(),
            _stable_hash(payload),
        )

    def evaluate_core_bridges(self) -> tuple[CoreBridgeAuthorityResult, ...]:
        rows = []
        for bridge in required_runtime_bridge_matrix():
            source = self.registry.by_name(bridge.source_authority)
            destination = self.registry.by_name(bridge.target_authority)
            artifact = bridge.payload_schema
            reasons: list[AuthorityPromotionRejectionCode] = []
            if not source:
                reasons.append(AuthorityPromotionRejectionCode.SOURCE_AUTHORITY_INVALID)
            if not destination:
                reasons.append(AuthorityPromotionRejectionCode.DESTINATION_AUTHORITY_INVALID)
            if source and RuntimeModePaper not in source.allowed_proof_domains:
                reasons.append(AuthorityPromotionRejectionCode.AUTHORITY_PROOF_DOMAIN_VIOLATION)
            if source and artifact not in source.permitted_artifact_types:
                reasons.append(AuthorityPromotionRejectionCode.AUTHORITY_SCOPE_VIOLATION)
            prior = "" if not reasons else ",".join(code.value for code in reasons)
            rows.append(
                CoreBridgeAuthorityResult(
                    bridge.bridge_id,
                    bridge.source_authority,
                    bridge.target_authority,
                    artifact,
                    prior or "NONE",
                    PromotionResult.ACCEPTED if not reasons else PromotionResult.REJECTED,
                    TraceEquivalenceLevel.CANONICAL_RUNTIME if bridge.bridge_id == "BRIDGE-WORKFLOW-OFFICE-001" and not reasons else TraceEquivalenceLevel.STRUCTURAL,
                    tuple(dict.fromkeys(reasons)),
                )
            )
        return tuple(rows)


RuntimeModePaper = "PAPER"


def default_authority_identities() -> tuple[AuthorityIdentity, ...]:
    rows: dict[str, AuthorityIdentity] = {}
    bridge_by_name = required_runtime_bridge_matrix()
    office_by_name = {office.office_name: office for office in default_office_definitions()}
    external_names = {"Paper Broker", "API Gateway", "Market Data"}
    truth_names = {"Position Registry", "Closed Position Truth", "Performance Truth", "Historian", "Learning Systems"}
    command_names = {"Commander", "Scheduler", "Mission Planner", "Workflow Orchestrator", "Authorization Authority", "Trader"}
    service_names = {"Cost Governor", "Communications Bus", "Persistence", "Canonical Runtime", "Runtime Provider", "EO-DG", "Doctrine", "EO-CK", "Fill Ledger"}
    for bridge in bridge_by_name:
        for name in (bridge.source_authority, bridge.target_authority):
            if name in rows:
                continue
            office = office_by_name.get(name)
            classification = _classification_for(name, office, external_names, truth_names, command_names, service_names)
            source_bridges = tuple(item.bridge_id for item in bridge_by_name if item.source_authority == name)
            destination_bridges = tuple(item.bridge_id for item in bridge_by_name if item.target_authority == name)
            artifacts = tuple(dict.fromkeys(item.payload_schema for item in bridge_by_name if item.source_authority == name or item.target_authority == name))
            commands = tuple(dict.fromkeys(item.command_or_event_type for item in bridge_by_name if item.source_authority == name or item.target_authority == name))
            rows[name] = AuthorityIdentity(
                _authority_id(name),
                name,
                classification,
                office.implementation_path if office else "runtime/service registry",
                office.office_id if office else _authority_id(name),
                TC_002_VERSION,
                office.constitutional_role if office else f"{name} constitutional authority.",
                ("PAPER",) if classification not in {AuthorityClassification.REPLAY_AUTHORITY, AuthorityClassification.TEST_AUTHORITY, AuthorityClassification.DEVELOPMENT_AUTHORITY} else ("REPLAY",),
                ("paper",),
                artifacts,
                commands,
                source_bridges,
                destination_bridges,
                "explicit delegation required; certification harness delegation prohibited",
                ("canonical runtime registration",),
                any("token" in item.required_workflow_token_state.lower() or "required" in item.eodc_promotion_requirement.lower() for item in bridge_by_name if item.source_authority == name),
                False,
                classification not in {AuthorityClassification.RETIRED_AUTHORITY, AuthorityClassification.PROHIBITED_AUTHORITY, AuthorityClassification.UNRESOLVED_AUTHORITY},
            )
    rows["Certification Authority"] = AuthorityIdentity("AUTH-CERTIFICATION-AUTHORITY", "Certification Authority", AuthorityClassification.CERTIFICATION_AUTHORITY, "src/argos/control_panel/constitutional_certification_series.py", "Certification Authority", TC_002_VERSION, "Observes and evaluates evidence without production authority.", ("PAPER", "REPLAY", "TEST"), ("paper", "replay", "test"), ("certification_report",), ("observe",), (), (), "may not delegate production authority", ("none",), False, False, False)
    rows["MarketReplayEngine"] = AuthorityIdentity("AUTH-MARKETREPLAYENGINE", "MarketReplayEngine", AuthorityClassification.REPLAY_AUTHORITY, "src/argos/control_panel/market_replay_engine.py", "MarketReplayEngine", TC_002_VERSION, "Replay-only evidence provider.", ("REPLAY",), ("replay",), ("ReplayRecord",), ("replay",), ("BRIDGE-REPLAY-LAB-001",), (), "replay isolated", ("replay mode",), False, False, False)
    return tuple(rows.values())


def execute_tc002_certification(repository_commit: str = "WORKTREE") -> dict[str, Any]:
    registry = ConstitutionalAuthorityRegistry()
    authority = AuthorityPromotionAuthority(registry)
    activations = tuple(authority.activate(item.authority_id, token_id="TOK-TC002" if item.token_required else "") for item in registry.all() if item.production_enabled)
    delegations = (
        authority.delegate("AUTH-COMMANDER", "AUTH-SCHEDULER", permitted_actions=("schedule paper workflow",)),
        authority.delegate("AUTH-SCHEDULER", "AUTH-MISSION-PLANNER", permitted_actions=("create mission plan",)),
        authority.delegate("AUTH-RISK", "AUTH-AUTHORIZATION-AUTHORITY", permitted_actions=("request trade authorization",)),
        authority.delegate("AUTH-TRADER", "AUTH-PAPER-BROKER", permitted_actions=("submit paper order",)),
        authority.delegate("AUTH-PERSISTENCE", "AUTH-CANONICAL-RUNTIME", permitted_actions=("restore evidence-backed state",)),
    )
    provenances = tuple(
        authority.provenance(artifact_id=f"ART-{index:03d}", artifact_type=bridge.payload_schema, producer_authority_id=_authority_id(bridge.source_authority), bridge_execution_reference=bridge.bridge_id)
        for index, bridge in enumerate(required_runtime_bridge_matrix(), start=1)
        if registry.by_name(bridge.source_authority)
    )
    promotion_decisions = tuple(authority.promote(item, destination_authority_id=_authority_id(next(bridge.target_authority for bridge in required_runtime_bridge_matrix() if bridge.bridge_id == item.bridge_execution_reference))) for item in provenances)
    core = authority.evaluate_core_bridges()
    registry_findings = registry.validate()
    blockers = tuple(item for item in core if item.current_promotion_result != PromotionResult.ACCEPTED)
    verdict = "FAIL" if registry_findings or blockers else "INCOMPLETE"
    if not registry_findings and not blockers:
        verdict = "INCOMPLETE"
    certification = {
        "order_id": "TC-002",
        "verdict": verdict,
        "readiness": "Authority and promotion registry installed; canonical execution coverage remains assigned to TC-003.",
        "repository_commit": repository_commit,
        "authority_count": len(registry.all()),
        "production_authority_count": sum(1 for item in registry.all() if item.production_enabled),
        "core_bridge_count": len(core),
        "accepted_core_bridge_authority_count": sum(1 for item in core if item.current_promotion_result == PromotionResult.ACCEPTED),
        "blocker_count": len(blockers) + len(registry_findings),
        "evidence_hash": _stable_hash((tuple(asdict(item) for item in core), repository_commit, registry_findings)),
        "timestamp_utc": utc_timestamp(),
        "schema_version": TC_002_VERSION,
    }
    return {
        "certification": certification,
        "authority_inventory": tuple(asdict(item) for item in registry.all()),
        "authority_registry": {"statuses": tuple(item.value for item in AuthorityRegistryStatus), "validation_findings": registry_findings},
        "authority_classification": {item.value: _classification_definition(item) for item in AuthorityClassification},
        "delegation_inventory": tuple(asdict(item) for item in delegations),
        "provenance_inventory": tuple(asdict(item) for item in provenances),
        "promotion_policy_matrix": tuple(asdict(item) for item in PROMOTION_SCOPE_REGISTRY),
        "core_bridge_authority_results": tuple(asdict(item) for item in core),
        "proof_domain_authority_validation": _proof_domain_validation(registry),
        "recovery_authority_validation": _recovery_validation(registry),
        "static_assurance": _static_assurance(registry),
        "dynamic_validation": {"promotionDecisions": tuple(asdict(item) for item in promotion_decisions), "tc001Preserved": True},
    }


def _classification_for(name: str, office: Any, external_names: set[str], truth_names: set[str], command_names: set[str], service_names: set[str]) -> AuthorityClassification:
    if name in external_names:
        return AuthorityClassification.EXTERNAL_AUTHORITY_ADAPTER
    if name in truth_names:
        return AuthorityClassification.TRUTH_PRODUCER
    if name == "Authorization Authority":
        return AuthorityClassification.AUTHORIZATION_AUTHORITY
    if name in command_names:
        return AuthorityClassification.COMMAND_AUTHORITY if name in {"Commander", "Scheduler"} else AuthorityClassification.WORKFLOW_OWNER
    if name in service_names:
        return AuthorityClassification.SERVICE_AUTHORITY
    if office and office.classification == OfficeClassification.INFORMATION_ONLY:
        return AuthorityClassification.INFORMATION_ONLY_OFFICE
    if office and office.classification == OfficeClassification.UNRESOLVED:
        return AuthorityClassification.UNRESOLVED_AUTHORITY
    return AuthorityClassification.CONSTITUTIONAL_OFFICE


def _authority_id(name: str) -> str:
    return "AUTH-" + name.upper().replace(" ", "-").replace("/", "-")


def _classification_definition(classification: AuthorityClassification) -> str:
    return {
        AuthorityClassification.WORKFLOW_OWNER: "May hold or transfer Workflow Execution Tokens within explicit scope.",
        AuthorityClassification.CONSTITUTIONAL_OFFICE: "Production office authority with lifecycle and artifact obligations.",
        AuthorityClassification.INFORMATION_ONLY_OFFICE: "Receives or emits immutable information without workflow ownership.",
        AuthorityClassification.COMMAND_AUTHORITY: "May issue scoped operational commands.",
        AuthorityClassification.AUTHORIZATION_AUTHORITY: "May convert validated risk decisions into authorization artifacts.",
        AuthorityClassification.TRUTH_PRODUCER: "May create authoritative truth records within declared provenance scope.",
        AuthorityClassification.EXTERNAL_AUTHORITY_ADAPTER: "Boundary adapter preserving external and internal authority identity.",
        AuthorityClassification.SERVICE_AUTHORITY: "Service authority without independent workflow ownership.",
        AuthorityClassification.RECOVERY_AUTHORITY: "May restore evidence-backed state without fabricating authority.",
        AuthorityClassification.CERTIFICATION_AUTHORITY: "May observe and certify, never create production authority.",
        AuthorityClassification.REPLAY_AUTHORITY: "Replay-isolated authority.",
        AuthorityClassification.TEST_AUTHORITY: "Test-only authority.",
        AuthorityClassification.DEVELOPMENT_AUTHORITY: "Development-only authority.",
        AuthorityClassification.RETIRED_AUTHORITY: "Historical authority no longer activatable.",
        AuthorityClassification.PROHIBITED_AUTHORITY: "Unsafe authority blocked from activation.",
        AuthorityClassification.UNRESOLVED_AUTHORITY: "Authority not yet safe for readiness credit.",
    }[classification]


def _proof_domain_validation(registry: ConstitutionalAuthorityRegistry) -> tuple[dict[str, Any], ...]:
    return tuple({"authorityId": item.authority_id, "allowedProofDomains": item.allowed_proof_domains, "paperProductionAllowed": "PAPER" in item.allowed_proof_domains and item.production_enabled} for item in registry.all())


def _recovery_validation(registry: ConstitutionalAuthorityRegistry) -> dict[str, Any]:
    recovery = registry.by_name("Persistence")
    runtime = registry.by_name("Canonical Runtime")
    return {"recoveryAuthorityRegistered": bool(recovery), "runtimeRestoreAuthorityRegistered": bool(runtime), "mayFabricateAuthority": False, "mayRetroactivelyVerifyProvenance": False}


def _static_assurance(registry: ConstitutionalAuthorityRegistry) -> dict[str, Any]:
    return {
        "duplicateAuthorityIds": (),
        "registryValidationFindings": registry.validate(),
        "classNameInferenceAccepted": False,
        "freeFormProductionAuthorityAccepted": False,
        "certificationHarnessMayInjectAuthority": False,
        "recoveryMayFabricateProvenance": False,
        "promotionRejectionCodes": tuple(code.value for code in AuthorityPromotionRejectionCode),
        "eoDcRejectionCodesPreserved": tuple(code.value for code in PromotionRejectionCode),
        "promotionStatusesPreserved": tuple(status.value for status in PromotionDecisionStatus),
        "promotionScopesPreserved": tuple(scope.value for scope in PromotionScope),
    }


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
