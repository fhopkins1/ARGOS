"""EO-DC truth provenance and promotion authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .constitutional_invariants import ConstitutionalInvariantEngine
from .truth_domain import (
    OperationalTruthEnvelope,
    ProvenanceStatus,
    RuntimeMode,
    TruthClassification,
    validate_decision_object_for_operational_truth,
    validate_operational_truth_envelope,
)


EO_DC_VERSION = "EO-DC.1"


class TruthInformationClass(str, Enum):
    RAW_OBSERVATION = "RAW_OBSERVATION"
    CANDIDATE_EVIDENCE = "CANDIDATE_EVIDENCE"
    VALIDATED_EVIDENCE = "VALIDATED_EVIDENCE"
    CERTIFIED_OPERATIONAL_INPUT = "CERTIFIED_OPERATIONAL_INPUT"
    AUTHORITATIVE_OPERATIONAL_FACT = "AUTHORITATIVE_OPERATIONAL_FACT"
    ANALYTICAL_ENRICHMENT = "ANALYTICAL_ENRICHMENT"
    DEGRADED_ANALYTICAL_RECORD = "DEGRADED_ANALYTICAL_RECORD"
    PROOF_RECORD = "PROOF_RECORD"
    SIMULATION_RECORD = "SIMULATION_RECORD"
    REPLAY_RECORD = "REPLAY_RECORD"
    TEST_FIXTURE = "TEST_FIXTURE"
    LIVE_RECORD = "LIVE_RECORD"


class PromotionState(str, Enum):
    CREATED = "CREATED"
    DOMAIN_IDENTIFIED = "DOMAIN_IDENTIFIED"
    PROVENANCE_VALIDATED = "PROVENANCE_VALIDATED"
    AUTHORITY_VALIDATED = "AUTHORITY_VALIDATED"
    LINEAGE_VALIDATED = "LINEAGE_VALIDATED"
    EVIDENCE_VALIDATED = "EVIDENCE_VALIDATED"
    SCOPE_CERTIFIED = "SCOPE_CERTIFIED"
    PROMOTION_APPROVED = "PROMOTION_APPROVED"
    AUTHORITATIVE_OWNER_ACCEPTED = "AUTHORITATIVE_OWNER_ACCEPTED"
    AUTHORITATIVE_FACT_CREATED = "AUTHORITATIVE_FACT_CREATED"
    REJECTED = "REJECTED"
    DEGRADED = "DEGRADED"
    QUARANTINED = "QUARANTINED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    SUPERSEDED = "SUPERSEDED"
    INCONCLUSIVE = "INCONCLUSIVE"
    PROOF_ONLY = "PROOF_ONLY"
    SIMULATION_ONLY = "SIMULATION_ONLY"
    REPLAY_ONLY = "REPLAY_ONLY"
    TEST_ONLY = "TEST_ONLY"
    LIVE_DISABLED = "LIVE_DISABLED"


class PromotionDecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEGRADED = "DEGRADED"
    QUARANTINED = "QUARANTINED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    INCONCLUSIVE = "INCONCLUSIVE"


class PromotionScope(str, Enum):
    ANALYST_CONSIDERATION = "ANALYST_CONSIDERATION"
    RISK_EVALUATION = "RISK_EVALUATION"
    TRADER_ORDER_CONSTRUCTION = "TRADER_ORDER_CONSTRUCTION"
    BROKER_SUBMISSION = "BROKER_SUBMISSION"
    POSITION_REGISTRY_MUTATION = "POSITION_REGISTRY_MUTATION"
    PERFORMANCE_TRUTH_INGESTION = "PERFORMANCE_TRUTH_INGESTION"
    HISTORIAN_PRESERVATION = "HISTORIAN_PRESERVATION"
    CERTIFIED_LEARNING = "CERTIFIED_LEARNING"
    COMMANDER_DISPLAY = "COMMANDER_DISPLAY"
    REPLAY_ONLY = "REPLAY_ONLY"
    SIMULATION_RESEARCH = "SIMULATION_RESEARCH"


class EvidenceQuality(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTORY = "CONTRADICTORY"
    MISSING = "MISSING"
    SYNTHETIC = "SYNTHETIC"
    FALLBACK = "FALLBACK"
    PROOF = "PROOF"
    SIMULATION = "SIMULATION"
    REPLAY = "REPLAY"
    TEST = "TEST"
    REVOKED = "REVOKED"


class PromotionRejectionCode(str, Enum):
    DOMAIN_MISSING = "DOMAIN_MISSING"
    DOMAIN_NOT_OPERATIONAL = "DOMAIN_NOT_OPERATIONAL"
    PROOF_NOT_PROMOTABLE = "PROOF_NOT_PROMOTABLE"
    SIMULATION_NOT_PROMOTABLE = "SIMULATION_NOT_PROMOTABLE"
    TEST_NOT_PROMOTABLE = "TEST_NOT_PROMOTABLE"
    REPLAY_CANNOT_CREATE_NEW_TRUTH = "REPLAY_CANNOT_CREATE_NEW_TRUTH"
    LIVE_DISABLED = "LIVE_DISABLED"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    PROVENANCE_UNVERIFIED = "PROVENANCE_UNVERIFIED"
    PROVENANCE_CONTRADICTORY = "PROVENANCE_CONTRADICTORY"
    SOURCE_AUTHORITY_INVALID = "SOURCE_AUTHORITY_INVALID"
    CONSUMER_SCOPE_INVALID = "CONSUMER_SCOPE_INVALID"
    WORKFLOW_MISSING = "WORKFLOW_MISSING"
    MISSION_MISSING = "MISSION_MISSING"
    TOKEN_MISSING = "TOKEN_MISSING"
    TOKEN_OWNER_INVALID = "TOKEN_OWNER_INVALID"
    LINEAGE_MISSING = "LINEAGE_MISSING"
    LINEAGE_CONFLICT = "LINEAGE_CONFLICT"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    EVIDENCE_STALE = "EVIDENCE_STALE"
    FALLBACK_NOT_AUTHORITATIVE = "FALLBACK_NOT_AUTHORITATIVE"
    SYNTHETIC_NOT_AUTHORITATIVE = "SYNTHETIC_NOT_AUTHORITATIVE"
    DEGRADED_NOT_AUTHORITATIVE = "DEGRADED_NOT_AUTHORITATIVE"
    CERTIFICATION_SCOPE_MISSING = "CERTIFICATION_SCOPE_MISSING"
    POLICY_REJECTED = "POLICY_REJECTED"
    DOCTRINE_REJECTED = "DOCTRINE_REJECTED"
    INVARIANT_BLOCKING_FAILURE = "INVARIANT_BLOCKING_FAILURE"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    ENVELOPE_EXPIRED = "ENVELOPE_EXPIRED"
    ENVELOPE_REVOKED = "ENVELOPE_REVOKED"
    PERSISTENCE_NAMESPACE_MISMATCH = "PERSISTENCE_NAMESPACE_MISMATCH"
    UNKNOWN_WRITER = "UNKNOWN_WRITER"
    UNKNOWN_CONSUMER = "UNKNOWN_CONSUMER"


@dataclass(frozen=True)
class ValidatedTruthEnvelope:
    envelope_id: str
    schema_version: str
    object_type: str
    object_id: str
    truth_domain: str
    truth_classification: str
    provenance_status: str
    certification_status: str
    evidence_quality: str
    originating_authority: str
    intended_consuming_authority: str
    originating_mission: str
    originating_workflow: str
    workflow_execution_token_id: str
    token_owner_at_production: str
    source_event_id: str
    parent_envelope_ids: tuple[str, ...]
    source_references: tuple[str, ...]
    creation_timestamp: str
    observation_timestamp: str
    effective_timestamp: str
    freshness_result: str
    integrity_hash: str
    idempotency_key: str
    doctrine_version: str
    policy_version: str
    validation_results: tuple[str, ...]
    promotion_scope: str
    permitted_consumers: tuple[str, ...]
    prohibited_consumers: tuple[str, ...]
    expiration: str
    revocation_state: str
    degraded_reasons: tuple[str, ...]
    fallback_indicators: tuple[str, ...]
    synthetic_indicators: tuple[str, ...]
    replay_indicators: tuple[str, ...]
    test_proof_simulation_indicators: tuple[str, ...]
    evaluator_version: str
    promotion_state: str = PromotionState.CREATED.value


@dataclass(frozen=True)
class PromotionDecision:
    decision_id: str
    envelope_id: str
    requested_promotion: str
    requested_consumer: str
    decision: PromotionDecisionStatus
    reason_codes: tuple[str, ...]
    authority_checks: tuple[str, ...]
    provenance_checks: tuple[str, ...]
    lineage_checks: tuple[str, ...]
    evidence_checks: tuple[str, ...]
    policy_checks: tuple[str, ...]
    doctrine_checks: tuple[str, ...]
    eoda_invariant_status: str
    timestamp_utc: str
    deterministic_sequence: int
    evaluator_version: str
    idempotency_key: str


@dataclass(frozen=True)
class PromotionRecord:
    decision: PromotionDecision
    envelope: ValidatedTruthEnvelope
    first_evaluated_utc: str
    last_evaluated_utc: str
    evaluation_count: int
    current_decision: str
    superseding_decision_id: str = ""
    revocation_status: str = "ACTIVE"


@dataclass(frozen=True)
class PromotionScopeDefinition:
    scope: PromotionScope
    permitted_consumers: tuple[str, ...]
    permitted_source_authorities: tuple[str, ...]
    requires_operational_envelope: bool
    permits_degraded: bool
    permits_replay: bool
    permits_learning: bool


PROMOTION_SCOPE_REGISTRY: tuple[PromotionScopeDefinition, ...] = (
    PromotionScopeDefinition(PromotionScope.TRADER_ORDER_CONSTRUCTION, ("Trader",), ("Seeker", "Analyst", "Risk", "Trader"), False, False, False, False),
    PromotionScopeDefinition(PromotionScope.BROKER_SUBMISSION, ("DeterministicPaperBrokerage",), ("Trader",), False, False, False, False),
    PromotionScopeDefinition(PromotionScope.POSITION_REGISTRY_MUTATION, ("PositionRegistry",), ("DeterministicPaperBrokerage",), True, False, False, False),
    PromotionScopeDefinition(PromotionScope.PERFORMANCE_TRUTH_INGESTION, ("PerformanceTruthEngine",), ("DeterministicPaperBrokerage", "PositionRegistry", "PerformanceTruthEngine"), True, False, False, False),
    PromotionScopeDefinition(PromotionScope.HISTORIAN_PRESERVATION, ("Historian",), ("PerformanceTruthEngine", "PositionRegistry", "DeterministicPaperBrokerage"), True, False, True, False),
    PromotionScopeDefinition(PromotionScope.CERTIFIED_LEARNING, ("EnterpriseLearningEngine", "LearningIntegrationOffice"), ("PerformanceTruthEngine", "ClosedPositionTruthBuilder", "Historian"), True, False, False, True),
    PromotionScopeDefinition(PromotionScope.COMMANDER_DISPLAY, ("Commander",), ("Seeker", "Analyst", "Risk", "Trader", "PerformanceTruthEngine", "Historian"), False, True, True, False),
    PromotionScopeDefinition(PromotionScope.REPLAY_ONLY, ("MarketReplayEngine",), ("Replay", "MarketReplayEngine"), False, True, True, False),
    PromotionScopeDefinition(PromotionScope.SIMULATION_RESEARCH, ("SimulationResearch",), ("Simulation", "MarketReplayEngine"), False, True, False, False),
)


class TruthPromotionAuthority:
    """Canonical EO-DC promotion authority; creates assurance decisions only."""

    def __init__(self, *, eoda_engine: ConstitutionalInvariantEngine | None = None) -> None:
        self.eoda_engine = eoda_engine or ConstitutionalInvariantEngine()
        self._records: dict[str, PromotionRecord] = {}
        self._sequence = 0

    def scope_registry(self) -> tuple[PromotionScopeDefinition, ...]:
        return PROMOTION_SCOPE_REGISTRY

    def promote_operational_envelope(
        self,
        envelope: OperationalTruthEnvelope | dict[str, Any] | ValidatedTruthEnvelope | None,
        *,
        scope: PromotionScope,
        requested_consumer: str,
        object_type: str,
        object_id: str,
    ) -> PromotionDecision:
        validated = self._normalize_envelope(envelope, scope=scope, requested_consumer=requested_consumer, object_type=object_type, object_id=object_id)
        codes = list(_domain_codes(validated))
        codes.extend(_scope_codes(validated, scope, requested_consumer))
        codes.extend(_lineage_codes(validated))
        codes.extend(_evidence_codes(validated, scope))
        if not _authority_allowed(validated.originating_authority, scope):
            codes.append(PromotionRejectionCode.SOURCE_AUTHORITY_INVALID.value)
        if validated.revocation_state != "ACTIVE":
            codes.append(PromotionRejectionCode.ENVELOPE_REVOKED.value)
        if _expired(validated.expiration):
            codes.append(PromotionRejectionCode.ENVELOPE_EXPIRED.value)
        decision = self._decision(validated, scope, requested_consumer, tuple(dict.fromkeys(codes)))
        self._record(decision, validated)
        return decision

    def promote_decision_object(self, decision_object: dict[str, Any], *, scope: PromotionScope = PromotionScope.TRADER_ORDER_CONSTRUCTION, requested_consumer: str = "Trader") -> PromotionDecision:
        object_id = str(decision_object.get("decisionObjectId") or decision_object.get("decision_object_id") or "")
        validation = validate_decision_object_for_operational_truth(decision_object, execution_environment="paper")
        codes = list(_decision_object_codes(decision_object))
        codes.extend(_map_provenance_codes(validation.codes))
        if requested_consumer not in _scope_definition(scope).permitted_consumers:
            codes.append(PromotionRejectionCode.CONSUMER_SCOPE_INVALID.value)
        if scope != PromotionScope.TRADER_ORDER_CONSTRUCTION:
            codes.append(PromotionRejectionCode.CERTIFICATION_SCOPE_MISSING.value)
        envelope = self._candidate_envelope(
            object_type="DecisionObject",
            object_id=object_id,
            scope=scope,
            requested_consumer=requested_consumer,
            source_authority=str(decision_object.get("office") or decision_object.get("sourceSystem") or ""),
            workflow_id=str(decision_object.get("workflowId") or decision_object.get("workflow_id") or ""),
            mission_id=str(decision_object.get("missionId") or decision_object.get("mission_id") or ""),
            token_id=str(decision_object.get("workflowTokenId") or decision_object.get("workflow_token") or ""),
            source_event_id=object_id,
            truth_domain=str(decision_object.get("executionMode") or decision_object.get("environment") or ""),
            truth_classification=str(decision_object.get("truthClassification") or TruthClassification.INCOMPLETE.value),
            provenance_status=ProvenanceStatus.VALIDATED.value if validation.valid else ProvenanceStatus.REJECTED.value,
            certification_status=str(decision_object.get("certificationStatus") or "UNCERTIFIED_DECISION_OBJECT"),
            evidence_quality=EvidenceQuality.VERIFIED.value if validation.valid else EvidenceQuality.UNVERIFIED.value,
            validation_results=validation.codes,
            idempotency_key=object_id or "decision-object-missing-id",
            degraded_reasons=tuple(decision_object.get("degradedReasons", ()) or ()),
            fallback_indicators=("apiFallbackUsed",) if decision_object.get("apiFallbackUsed") else (),
            synthetic_indicators=("placeholder",) if "placeholder" in str(decision_object.get("revisionSource", "")).lower() else (),
            test_proof_simulation_indicators=_domain_indicators(decision_object),
        )
        if not envelope.originating_mission:
            # Existing Decision Object fixtures do not always include mission IDs; keep this explicit.
            codes.append(PromotionRejectionCode.MISSION_MISSING.value)
        decision = self._decision(envelope, scope, requested_consumer, tuple(dict.fromkeys(codes)))
        self._record(decision, envelope)
        return decision

    def promote_broker_event(self, event_envelope: OperationalTruthEnvelope | dict[str, Any] | None, *, requested_consumer: str = "PositionRegistry", object_type: str = "BrokerEvent", object_id: str = "") -> PromotionDecision:
        return self.promote_operational_envelope(event_envelope, scope=PromotionScope.POSITION_REGISTRY_MUTATION, requested_consumer=requested_consumer, object_type=object_type, object_id=object_id)

    def promote_position_mutation(self, fill_envelope: OperationalTruthEnvelope | dict[str, Any] | None, *, requested_consumer: str = "PositionRegistry", object_id: str = "") -> PromotionDecision:
        return self.promote_operational_envelope(fill_envelope, scope=PromotionScope.POSITION_REGISTRY_MUTATION, requested_consumer=requested_consumer, object_type="BrokerFill", object_id=object_id)

    def promote_performance_truth(self, source_envelope: OperationalTruthEnvelope | dict[str, Any] | None, *, requested_consumer: str = "PerformanceTruthEngine", object_id: str = "") -> PromotionDecision:
        return self.promote_operational_envelope(source_envelope, scope=PromotionScope.PERFORMANCE_TRUTH_INGESTION, requested_consumer=requested_consumer, object_type="PerformanceTruthSource", object_id=object_id)

    def promote_learning_input(self, envelope: OperationalTruthEnvelope | dict[str, Any] | ValidatedTruthEnvelope | None, *, requested_consumer: str = "EnterpriseLearningEngine", object_type: str = "LearningInput", object_id: str = "") -> PromotionDecision:
        return self.promote_operational_envelope(envelope, scope=PromotionScope.CERTIFIED_LEARNING, requested_consumer=requested_consumer, object_type=object_type, object_id=object_id)

    def promote_replay_record(self, envelope: dict[str, Any], *, creates_new_active_truth: bool = False, object_id: str = "") -> PromotionDecision:
        candidate = self._candidate_envelope(
            object_type="ReplayRecord",
            object_id=object_id or str(envelope.get("replay_run_id") or envelope.get("id") or ""),
            scope=PromotionScope.REPLAY_ONLY,
            requested_consumer="MarketReplayEngine",
            source_authority="MarketReplayEngine",
            workflow_id=str(envelope.get("workflow_id", "")),
            mission_id=str(envelope.get("mission_id", "")),
            token_id=str(envelope.get("token_id", "")),
            source_event_id=str(envelope.get("replay_run_id") or envelope.get("id") or ""),
            truth_domain="REPLAY",
            truth_classification="REPLAY_ONLY",
            provenance_status=ProvenanceStatus.VALIDATED.value,
            certification_status="REPLAY_ONLY",
            evidence_quality=EvidenceQuality.REPLAY.value,
            validation_results=(),
            idempotency_key=str(envelope.get("replay_run_id") or envelope.get("id") or "replay"),
            replay_indicators=("replay",),
        )
        codes = () if not creates_new_active_truth else (PromotionRejectionCode.REPLAY_CANNOT_CREATE_NEW_TRUTH.value,)
        decision = self._decision(candidate, PromotionScope.REPLAY_ONLY, "MarketReplayEngine", codes)
        self._record(decision, candidate)
        return decision

    def revoke(self, envelope_id: str, *, reason: str, revocation_authority: str) -> PromotionDecision:
        record = self._records.get(envelope_id)
        if not record:
            envelope = self._candidate_envelope(
                object_type="Unknown",
                object_id=envelope_id,
                scope=PromotionScope.COMMANDER_DISPLAY,
                requested_consumer="Commander",
                source_authority=revocation_authority,
                workflow_id="",
                mission_id="",
                token_id="",
                source_event_id=envelope_id,
                truth_domain="",
                truth_classification=TruthClassification.INCOMPLETE.value,
                provenance_status=ProvenanceStatus.MISSING.value,
                certification_status="UNKNOWN",
                evidence_quality=EvidenceQuality.MISSING.value,
                validation_results=(reason,),
                idempotency_key=envelope_id,
            )
        else:
            envelope = replace(record.envelope, revocation_state="REVOKED", validation_results=(*record.envelope.validation_results, reason))
        decision = self._decision(envelope, PromotionScope.COMMANDER_DISPLAY, "Commander", (PromotionRejectionCode.ENVELOPE_REVOKED.value,), status=PromotionDecisionStatus.REVOKED)
        self._record(decision, envelope)
        return decision

    def commander_read_model(self) -> dict[str, Any]:
        records = tuple(self._records.values())
        return {
            "engineName": "Truth Provenance and Promotion Authority",
            "engineeringOrder": "EO-DC",
            "pendingPromotionRequests": (),
            "approvals": tuple(asdict(record.decision) for record in records if record.decision.decision == PromotionDecisionStatus.APPROVED),
            "rejections": tuple(asdict(record.decision) for record in records if record.decision.decision == PromotionDecisionStatus.REJECTED),
            "quarantinedRecords": tuple(asdict(record.decision) for record in records if record.decision.decision == PromotionDecisionStatus.QUARANTINED),
            "degradedRecords": tuple(asdict(record.decision) for record in records if record.decision.decision == PromotionDecisionStatus.DEGRADED),
            "revokedApprovals": tuple(asdict(record.decision) for record in records if record.decision.decision == PromotionDecisionStatus.REVOKED),
            "domainViolations": tuple(asdict(record.decision) for record in records if any("DOMAIN" in code or "PROOF" in code or "SIMULATION" in code or "LIVE" in code for code in record.decision.reason_codes)),
            "learningEligibility": tuple(asdict(record.decision) for record in records if record.decision.requested_promotion == PromotionScope.CERTIFIED_LEARNING.value),
            "commanderLimitations": {
                "mayConvertProofToPaper": False,
                "mayMarkUnverifiedEvidenceVerified": False,
                "mayOverrideCriticalPromotionBypass": False,
                "mayRewritePromotionHistory": False,
                "mayEraseRejectionEvidence": False,
                "mayEnableLivePromotion": False,
            },
            "financialMutationAuthority": False,
        }

    def _normalize_envelope(self, envelope: OperationalTruthEnvelope | dict[str, Any] | ValidatedTruthEnvelope | None, *, scope: PromotionScope, requested_consumer: str, object_type: str, object_id: str) -> ValidatedTruthEnvelope:
        if isinstance(envelope, ValidatedTruthEnvelope):
            return envelope
        payload = dict(envelope.__dict__) if isinstance(envelope, OperationalTruthEnvelope) else dict(envelope or {})
        validation = validate_operational_truth_envelope(payload, target_authority=str(payload.get("caller") or requested_consumer)) if payload else None
        codes = validation.codes if validation else (PromotionRejectionCode.PROVENANCE_MISSING.value,)
        return self._candidate_envelope(
            object_type=object_type,
            object_id=object_id or str(payload.get("source_event_id") or payload.get("sourceEventId") or payload.get("idempotency_key") or ""),
            scope=scope,
            requested_consumer=requested_consumer,
            source_authority=str(payload.get("originating_authority") or payload.get("originatingAuthority") or ""),
            workflow_id=str(payload.get("originating_workflow_id") or payload.get("originatingWorkflowId") or ""),
            mission_id=str(payload.get("mission_id") or payload.get("missionId") or ""),
            token_id=str(payload.get("workflow_token_id") or payload.get("workflowTokenId") or ""),
            source_event_id=str(payload.get("source_event_id") or payload.get("sourceEventId") or ""),
            truth_domain=str(payload.get("truth_domain") or payload.get("truthDomain") or ""),
            truth_classification=str(payload.get("truth_classification") or payload.get("truthClassification") or ""),
            provenance_status=str(payload.get("provenance_status") or payload.get("provenanceStatus") or ""),
            certification_status=str(payload.get("certification_status") or payload.get("certificationStatus") or ""),
            evidence_quality=EvidenceQuality.VERIFIED.value if validation and validation.valid else EvidenceQuality.UNVERIFIED.value,
            validation_results=codes,
            idempotency_key=str(payload.get("idempotency_key") or payload.get("idempotencyKey") or object_id),
            degraded_reasons=("degraded",) if payload.get("degraded") else (),
            fallback_indicators=tuple(payload.get("fallback_indicators", ()) or ()),
            synthetic_indicators=tuple(payload.get("synthetic_indicators", ()) or ()),
        )

    def _candidate_envelope(
        self,
        *,
        object_type: str,
        object_id: str,
        scope: PromotionScope,
        requested_consumer: str,
        source_authority: str,
        workflow_id: str,
        mission_id: str,
        token_id: str,
        source_event_id: str,
        truth_domain: str,
        truth_classification: str,
        provenance_status: str,
        certification_status: str,
        evidence_quality: str,
        validation_results: tuple[str, ...],
        idempotency_key: str,
        degraded_reasons: tuple[str, ...] = (),
        fallback_indicators: tuple[str, ...] = (),
        synthetic_indicators: tuple[str, ...] = (),
        replay_indicators: tuple[str, ...] = (),
        test_proof_simulation_indicators: tuple[str, ...] = (),
    ) -> ValidatedTruthEnvelope:
        now = utc_timestamp()
        integrity_payload = {
            "object_id": object_id,
            "object_type": object_type,
            "scope": scope.value,
            "source_authority": source_authority,
            "source_event_id": source_event_id,
            "truth_domain": truth_domain,
        }
        digest = _stable_hash(integrity_payload)
        envelope_id = f"EO-DC-ENV-{digest[:16].upper()}"
        scope_def = _scope_definition(scope)
        return ValidatedTruthEnvelope(
            envelope_id=envelope_id,
            schema_version=EO_DC_VERSION,
            object_type=object_type,
            object_id=object_id,
            truth_domain=truth_domain.upper(),
            truth_classification=truth_classification,
            provenance_status=provenance_status,
            certification_status=certification_status,
            evidence_quality=evidence_quality,
            originating_authority=source_authority,
            intended_consuming_authority=requested_consumer,
            originating_mission=mission_id,
            originating_workflow=workflow_id,
            workflow_execution_token_id=token_id,
            token_owner_at_production="",
            source_event_id=source_event_id,
            parent_envelope_ids=(),
            source_references=(source_event_id,) if source_event_id else (),
            creation_timestamp=now,
            observation_timestamp=now,
            effective_timestamp=now,
            freshness_result="CURRENT",
            integrity_hash=digest,
            idempotency_key=idempotency_key,
            doctrine_version="CURRENT",
            policy_version="CURRENT",
            validation_results=tuple(validation_results),
            promotion_scope=scope.value,
            permitted_consumers=scope_def.permitted_consumers,
            prohibited_consumers=tuple(sorted(set(_all_consumers()) - set(scope_def.permitted_consumers))),
            expiration="",
            revocation_state="ACTIVE",
            degraded_reasons=tuple(degraded_reasons),
            fallback_indicators=tuple(fallback_indicators),
            synthetic_indicators=tuple(synthetic_indicators),
            replay_indicators=tuple(replay_indicators),
            test_proof_simulation_indicators=tuple(test_proof_simulation_indicators),
            evaluator_version=EO_DC_VERSION,
        )

    def _decision(self, envelope: ValidatedTruthEnvelope, scope: PromotionScope, requested_consumer: str, codes: tuple[str, ...], *, status: PromotionDecisionStatus | None = None) -> PromotionDecision:
        self._sequence += 1
        decision_status = status or (PromotionDecisionStatus.APPROVED if not codes else PromotionDecisionStatus.REJECTED)
        payload = {"envelope_id": envelope.envelope_id, "scope": scope.value, "consumer": requested_consumer, "codes": codes, "version": EO_DC_VERSION}
        decision_id = f"EO-DC-DEC-{_stable_hash(payload)[:16].upper()}"
        return PromotionDecision(
            decision_id=decision_id,
            envelope_id=envelope.envelope_id,
            requested_promotion=scope.value,
            requested_consumer=requested_consumer,
            decision=decision_status,
            reason_codes=tuple(codes),
            authority_checks=("SOURCE_AUTHORITY_VALID" if PromotionRejectionCode.SOURCE_AUTHORITY_INVALID.value not in codes else "SOURCE_AUTHORITY_INVALID",),
            provenance_checks=("PROVENANCE_VALIDATED" if not any(code.startswith("PROVENANCE") for code in codes) else "PROVENANCE_REJECTED",),
            lineage_checks=("LINEAGE_VALIDATED" if not any(code in {PromotionRejectionCode.WORKFLOW_MISSING.value, PromotionRejectionCode.MISSION_MISSING.value, PromotionRejectionCode.TOKEN_MISSING.value, PromotionRejectionCode.LINEAGE_MISSING.value} for code in codes) else "LINEAGE_REJECTED",),
            evidence_checks=("EVIDENCE_VALIDATED" if not any("EVIDENCE" in code or "SYNTHETIC" in code or "FALLBACK" in code or "DEGRADED" in code for code in codes) else "EVIDENCE_REJECTED",),
            policy_checks=("POLICY_NOT_REJECTED",),
            doctrine_checks=("DOCTRINE_NOT_REJECTED",),
            eoda_invariant_status="NOT_EVALUATED_RUNTIME_LOCAL",
            timestamp_utc=utc_timestamp(),
            deterministic_sequence=self._sequence,
            evaluator_version=EO_DC_VERSION,
            idempotency_key=envelope.idempotency_key,
        )

    def _record(self, decision: PromotionDecision, envelope: ValidatedTruthEnvelope) -> PromotionRecord:
        existing = self._records.get(envelope.envelope_id)
        now = utc_timestamp()
        if existing and existing.decision.decision_id == decision.decision_id:
            record = PromotionRecord(decision, envelope, existing.first_evaluated_utc, now, existing.evaluation_count + 1, decision.decision.value, existing.superseding_decision_id, existing.revocation_status)
        else:
            record = PromotionRecord(decision, envelope, now, now, 1, decision.decision.value)
        self._records[envelope.envelope_id] = record
        return record


def _scope_definition(scope: PromotionScope) -> PromotionScopeDefinition:
    return next(item for item in PROMOTION_SCOPE_REGISTRY if item.scope == scope)


def _all_consumers() -> tuple[str, ...]:
    values: set[str] = set()
    for item in PROMOTION_SCOPE_REGISTRY:
        values.update(item.permitted_consumers)
    return tuple(values)


def _domain_codes(envelope: ValidatedTruthEnvelope) -> tuple[str, ...]:
    domain = envelope.truth_domain.upper()
    codes: list[str] = []
    if not domain:
        codes.append(PromotionRejectionCode.DOMAIN_MISSING.value)
    elif domain == RuntimeMode.PROOF.value:
        codes.append(PromotionRejectionCode.PROOF_NOT_PROMOTABLE.value)
    elif domain == RuntimeMode.SIMULATION.value:
        codes.append(PromotionRejectionCode.SIMULATION_NOT_PROMOTABLE.value)
    elif domain == RuntimeMode.TEST.value:
        codes.append(PromotionRejectionCode.TEST_NOT_PROMOTABLE.value)
    elif domain == "REPLAY":
        codes.append(PromotionRejectionCode.REPLAY_CANNOT_CREATE_NEW_TRUTH.value)
    elif domain == RuntimeMode.LIVE.value:
        codes.append(PromotionRejectionCode.LIVE_DISABLED.value)
    elif domain != RuntimeMode.PAPER.value:
        codes.append(PromotionRejectionCode.DOMAIN_NOT_OPERATIONAL.value)
    return tuple(codes)


def _scope_codes(envelope: ValidatedTruthEnvelope, scope: PromotionScope, requested_consumer: str) -> tuple[str, ...]:
    scope_def = _scope_definition(scope)
    codes = []
    if requested_consumer not in scope_def.permitted_consumers:
        codes.append(PromotionRejectionCode.CONSUMER_SCOPE_INVALID.value)
    if not scope_def.permits_replay and envelope.replay_indicators:
        codes.append(PromotionRejectionCode.REPLAY_CANNOT_CREATE_NEW_TRUTH.value)
    if not scope_def.permits_degraded and envelope.degraded_reasons:
        codes.append(PromotionRejectionCode.DEGRADED_NOT_AUTHORITATIVE.value)
    return tuple(codes)


def _lineage_codes(envelope: ValidatedTruthEnvelope) -> tuple[str, ...]:
    codes = []
    if not envelope.originating_workflow:
        codes.append(PromotionRejectionCode.WORKFLOW_MISSING.value)
    if not envelope.originating_mission:
        codes.append(PromotionRejectionCode.MISSION_MISSING.value)
    if not envelope.workflow_execution_token_id:
        codes.append(PromotionRejectionCode.TOKEN_MISSING.value)
    if not envelope.source_event_id:
        codes.append(PromotionRejectionCode.LINEAGE_MISSING.value)
    return tuple(codes)


def _evidence_codes(envelope: ValidatedTruthEnvelope, scope: PromotionScope) -> tuple[str, ...]:
    codes = []
    if envelope.provenance_status in {"", ProvenanceStatus.MISSING.value}:
        codes.append(PromotionRejectionCode.PROVENANCE_MISSING.value)
    if envelope.provenance_status == ProvenanceStatus.UNVERIFIED.value or envelope.evidence_quality in {EvidenceQuality.UNVERIFIED.value, EvidenceQuality.PARTIALLY_VERIFIED.value}:
        codes.append(PromotionRejectionCode.PROVENANCE_UNVERIFIED.value)
    if envelope.evidence_quality == EvidenceQuality.CONTRADICTORY.value:
        codes.append(PromotionRejectionCode.PROVENANCE_CONTRADICTORY.value)
    if envelope.evidence_quality == EvidenceQuality.SYNTHETIC.value or envelope.synthetic_indicators:
        codes.append(PromotionRejectionCode.SYNTHETIC_NOT_AUTHORITATIVE.value)
    if envelope.evidence_quality == EvidenceQuality.FALLBACK.value or envelope.fallback_indicators:
        codes.append(PromotionRejectionCode.FALLBACK_NOT_AUTHORITATIVE.value)
    if envelope.evidence_quality == EvidenceQuality.MISSING.value:
        codes.append(PromotionRejectionCode.EVIDENCE_INCOMPLETE.value)
    if scope == PromotionScope.CERTIFIED_LEARNING and envelope.degraded_reasons:
        codes.append(PromotionRejectionCode.DEGRADED_NOT_AUTHORITATIVE.value)
    return tuple(codes)


def _authority_allowed(authority: str, scope: PromotionScope) -> bool:
    return authority in _scope_definition(scope).permitted_source_authorities


def _decision_object_codes(decision_object: dict[str, Any]) -> tuple[str, ...]:
    codes = []
    if decision_object.get("apiFallbackUsed"):
        codes.append(PromotionRejectionCode.FALLBACK_NOT_AUTHORITATIVE.value)
    if decision_object.get("degradedReasons"):
        codes.append(PromotionRejectionCode.DEGRADED_NOT_AUTHORITATIVE.value)
    if not str(decision_object.get("workflowId") or decision_object.get("workflow_id") or ""):
        codes.append(PromotionRejectionCode.WORKFLOW_MISSING.value)
    if not str(decision_object.get("workflowTokenId") or decision_object.get("workflow_token") or ""):
        codes.append(PromotionRejectionCode.TOKEN_MISSING.value)
    if str(decision_object.get("sourceSystem", "")).lower() in {"runtime", "controlpanelruntime", "control_panel_runtime"}:
        codes.append(PromotionRejectionCode.SOURCE_AUTHORITY_INVALID.value)
    return tuple(codes)


def _map_provenance_codes(codes: tuple[str, ...]) -> tuple[str, ...]:
    mapped = []
    for code in codes:
        if code == "PROOF_MODE_NOT_ACTIONABLE":
            mapped.append(PromotionRejectionCode.PROOF_NOT_PROMOTABLE.value)
        elif code == "SIMULATION_VALUE_IN_OPERATIONAL_PATH":
            mapped.append(PromotionRejectionCode.SIMULATION_NOT_PROMOTABLE.value)
        elif code == "LIVE_DISABLED":
            mapped.append(PromotionRejectionCode.LIVE_DISABLED.value)
        elif code in {"MISSING_PROVENANCE", "MISSING_RISK_AUTHORITY", "MISSING_TRADER_AUTHORITY"}:
            mapped.append(PromotionRejectionCode.PROVENANCE_MISSING.value)
        elif code == "UNAUTHORIZED_PRODUCER":
            mapped.append(PromotionRejectionCode.SOURCE_AUTHORITY_INVALID.value)
        elif code == "UNCERTIFIED_DECISION_OBJECT":
            mapped.append(PromotionRejectionCode.CERTIFICATION_SCOPE_MISSING.value)
        elif code == "PLACEHOLDER_VALUE":
            mapped.append(PromotionRejectionCode.SYNTHETIC_NOT_AUTHORITATIVE.value)
    return tuple(mapped)


def _domain_indicators(payload: dict[str, Any]) -> tuple[str, ...]:
    domain = str(payload.get("executionMode") or payload.get("environment") or "").upper()
    indicators = []
    if domain in {"PROOF", "SIMULATION", "TEST", "REPLAY", "LIVE"}:
        indicators.append(domain.lower())
    classification = str(payload.get("truthClassification") or "")
    if classification in {TruthClassification.PROOF_ONLY.value, TruthClassification.SIMULATION_ONLY.value, TruthClassification.TEST_FIXTURE.value}:
        indicators.append(classification.lower())
    return tuple(indicators)


def _expired(expiration: str) -> bool:
    return bool(expiration and expiration < utc_timestamp())


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
