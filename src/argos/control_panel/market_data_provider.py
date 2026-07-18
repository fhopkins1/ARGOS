"""EO-DJ authoritative paper market-data boundary.

This module is the canonical ingress boundary for decision-reachable market
observations. It intentionally fails closed when no authorized provider is
configured and keeps test, replay, and development observations out of paper
and live decision domains.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation
from enum import Enum
import hashlib
import json
from typing import Any, Protocol

from argos.foundation.contracts import utc_timestamp


EO_DJ_VERSION = "EO-DJ.1"
CAPABILITIES = (
    "quotes",
    "intradayBars",
    "dailyBars",
    "trades",
    "orderBooks",
    "corporateActions",
    "securityIdentifiers",
    "marketStatus",
)


class MarketDataProofDomain(str, Enum):
    PAPER_AUTHORITATIVE = "PAPER_AUTHORITATIVE"
    LIVE_AUTHORITATIVE = "LIVE_AUTHORITATIVE"
    REPLAY = "REPLAY"
    TEST = "TEST"
    DEVELOPMENT_SIMULATION = "DEVELOPMENT_SIMULATION"


class ProviderAuthorityClass(str, Enum):
    AUTHORITATIVE_EXTERNAL = "AUTHORITATIVE_EXTERNAL"
    PERSISTED_AUTHORITATIVE = "PERSISTED_AUTHORITATIVE"
    REPLAY_INPUT = "REPLAY_INPUT"
    TEST_FIXTURE = "TEST_FIXTURE"
    DEVELOPMENT_SIMULATION = "DEVELOPMENT_SIMULATION"
    PROHIBITED_SYNTHETIC = "PROHIBITED_SYNTHETIC"
    UNKNOWN = "UNKNOWN"


class MarketObservationType(str, Enum):
    QUOTE = "QUOTE"
    TRADE = "TRADE"
    BAR = "BAR"
    ORDER_BOOK = "ORDER_BOOK"
    MARKET_STATUS = "MARKET_STATUS"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    SECURITY_IDENTIFIER = "SECURITY_IDENTIFIER"
    NEWS = "NEWS"


class MarketDataResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
    UNSUPPORTED = "UNSUPPORTED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    MALFORMED = "MALFORMED"
    CONFIGURATION_FAILURE = "CONFIGURATION_FAILURE"
    RATE_LIMITED = "RATE_LIMITED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"


class MarketDataFreshnessStatus(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class MarketDataEvidenceStatus(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    HISTORICAL_ONLY = "HISTORICAL_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    QUARANTINED = "QUARANTINED"


class MarketDataRejectionCode(str, Enum):
    MARKET_DATA_PROVIDER_NOT_CONFIGURED = "MARKET_DATA_PROVIDER_NOT_CONFIGURED"
    MARKET_DATA_PROVIDER_NOT_AUTHORIZED = "MARKET_DATA_PROVIDER_NOT_AUTHORIZED"
    MARKET_DATA_PROOF_DOMAIN_VIOLATION = "MARKET_DATA_PROOF_DOMAIN_VIOLATION"
    MARKET_DATA_UNAVAILABLE = "MARKET_DATA_UNAVAILABLE"
    MARKET_DATA_STALE = "MARKET_DATA_STALE"
    MARKET_DATA_EXPIRED = "MARKET_DATA_EXPIRED"
    MARKET_DATA_MALFORMED = "MARKET_DATA_MALFORMED"
    MARKET_DATA_INSTRUMENT_MISMATCH = "MARKET_DATA_INSTRUMENT_MISMATCH"
    MARKET_DATA_OBSERVATION_NOT_FOUND = "MARKET_DATA_OBSERVATION_NOT_FOUND"
    MARKET_DATA_INTEGRITY_FAILURE = "MARKET_DATA_INTEGRITY_FAILURE"
    MARKET_DATA_CONFLICT = "MARKET_DATA_CONFLICT"
    MARKET_DATA_SYNTHETIC_SOURCE_REJECTED = "MARKET_DATA_SYNTHETIC_SOURCE_REJECTED"
    MARKET_DATA_RECOVERY_EVIDENCE_MISSING = "MARKET_DATA_RECOVERY_EVIDENCE_MISSING"
    MARKET_DATA_UNSUPPORTED_OBSERVATION_TYPE = "MARKET_DATA_UNSUPPORTED_OBSERVATION_TYPE"


@dataclass(frozen=True)
class FreshnessPolicy:
    policy_id: str
    version: str
    maximum_age_seconds: int
    expire_after_seconds: int
    market_session_context: str = "regular_or_paper_session"


@dataclass(frozen=True)
class FreshnessEvaluation:
    policy_id: str
    policy_version: str
    source_timestamp_utc: str
    evaluated_at_utc: str
    age_seconds: int | None
    maximum_age_seconds: int
    expire_after_seconds: int
    market_session_context: str
    classification: MarketDataFreshnessStatus


@dataclass(frozen=True)
class ProviderAuthorityRecord:
    provider_id: str
    provider_name: str
    implementation: str
    provider_classification: ProviderAuthorityClass
    allowed_proof_domains: tuple[MarketDataProofDomain, ...]
    supported_observation_types: tuple[MarketObservationType, ...]
    supported_markets: tuple[str, ...]
    configuration_requirements: tuple[str, ...]
    enabled: bool
    policy_version: str = EO_DJ_VERSION
    schema_version: str = EO_DJ_VERSION


@dataclass(frozen=True)
class ProviderRegistryEntry:
    providerId: str
    providerName: str
    providerType: str
    enabled: bool
    environment: str
    supportedCapabilities: dict[str, str]
    defaultPriority: int
    fallbackPriority: int
    costModel: dict[str, Any]
    rateLimitModel: dict[str, Any]
    authenticationStatus: str
    healthStatus: str
    lastSuccessfulCall: str
    lastFailedCall: str
    errorCount: int
    commanderApprovalStatus: str


@dataclass(frozen=True)
class MarketDataObservation:
    observation_id: str
    proof_domain: MarketDataProofDomain
    provider_id: str
    provider_classification: ProviderAuthorityClass
    source_authority: ProviderAuthorityClass
    instrument_id: str
    symbol: str
    venue: str
    observation_type: MarketObservationType
    normalized_payload: dict[str, str]
    source_timestamp_utc: str
    ingestion_timestamp_utc: str
    freshness: FreshnessEvaluation
    evidence_status: MarketDataEvidenceStatus
    adjustment_status: str
    correlation_id: str
    request_id: str
    persistence_id: str
    schema_version: str
    deterministic_hash: str


@dataclass(frozen=True)
class MarketDataProviderRequest:
    provider_id: str
    proof_domain: MarketDataProofDomain
    instrument_id: str
    symbol: str
    observation_type: MarketObservationType
    requested_at_utc: str
    correlation_id: str
    request_id: str
    workflow_id: str = ""
    decision_object_id: str = ""


@dataclass(frozen=True)
class MarketDataProviderResult:
    status: MarketDataResultStatus
    payload: dict[str, Any]
    source_timestamp_utc: str
    provider_message: str = ""
    rejection_code: MarketDataRejectionCode | None = None


@dataclass(frozen=True)
class MarketDataGatewayResult:
    accepted: bool
    status: MarketDataResultStatus
    observation: MarketDataObservation | None = None
    rejection_code: MarketDataRejectionCode | None = None
    message: str = ""
    audit_events: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class MarketDataDecisionGuardResult:
    accepted: bool
    observation_id: str
    rejection_code: MarketDataRejectionCode | None
    message: str
    proof_domain: str = ""
    provider_id: str = ""


@dataclass(frozen=True)
class DerivedMarketFact:
    fact_id: str
    fact_type: str
    source_observation_ids: tuple[str, ...]
    input_manifest_id: str
    payload: dict[str, Any]
    schema_version: str = EO_DJ_VERSION


class MarketDataProvider(Protocol):
    provider_id: str

    def observe(self, request: MarketDataProviderRequest) -> MarketDataProviderResult:
        ...


class ProviderAuthorityRegistry:
    """Authority policy for market-data providers."""

    def __init__(self, records: tuple[ProviderAuthorityRecord, ...] | None = None) -> None:
        self._records: dict[str, ProviderAuthorityRecord] = {}
        for record in records or default_provider_authority_records():
            self.register(record)

    def register(self, record: ProviderAuthorityRecord) -> None:
        if record.provider_id in self._records:
            raise ValueError(f"duplicate market-data provider identity: {record.provider_id}")
        if record.provider_classification in {
            ProviderAuthorityClass.TEST_FIXTURE,
            ProviderAuthorityClass.DEVELOPMENT_SIMULATION,
            ProviderAuthorityClass.REPLAY_INPUT,
            ProviderAuthorityClass.PROHIBITED_SYNTHETIC,
        } and any(domain in record.allowed_proof_domains for domain in (MarketDataProofDomain.PAPER_AUTHORITATIVE, MarketDataProofDomain.LIVE_AUTHORITATIVE)):
            raise ValueError(f"non-production provider cannot be authoritative: {record.provider_id}")
        self._records[record.provider_id] = record

    def all(self) -> tuple[ProviderAuthorityRecord, ...]:
        return tuple(self._records.values())

    def get(self, provider_id: str) -> ProviderAuthorityRecord | None:
        return self._records.get(provider_id)

    def resolve(self, provider_id: str, proof_domain: MarketDataProofDomain, observation_type: MarketObservationType) -> tuple[ProviderAuthorityRecord | None, MarketDataRejectionCode | None]:
        record = self._records.get(provider_id)
        if record is None or not record.enabled:
            return None, MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_CONFIGURED
        if proof_domain not in record.allowed_proof_domains:
            if record.provider_classification in {ProviderAuthorityClass.TEST_FIXTURE, ProviderAuthorityClass.DEVELOPMENT_SIMULATION, ProviderAuthorityClass.REPLAY_INPUT, ProviderAuthorityClass.PROHIBITED_SYNTHETIC}:
                return record, MarketDataRejectionCode.MARKET_DATA_SYNTHETIC_SOURCE_REJECTED
            return record, MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_AUTHORIZED
        if observation_type not in record.supported_observation_types:
            return record, MarketDataRejectionCode.MARKET_DATA_UNSUPPORTED_OBSERVATION_TYPE
        return record, None


class MarketDataEvidenceStore:
    """Append/idempotent observation store with conflict detection."""

    def __init__(self) -> None:
        self._observations: dict[str, MarketDataObservation] = {}
        self._natural_index: dict[str, str] = {}
        self._conflicts: list[dict[str, Any]] = []

    def persist(self, observation: MarketDataObservation) -> tuple[MarketDataObservation, bool, dict[str, Any] | None]:
        natural = _natural_identity(observation)
        existing_id = self._natural_index.get(natural)
        if existing_id:
            existing = self._observations[existing_id]
            if existing.deterministic_hash == observation.deterministic_hash:
                return existing, False, None
            conflict = {
                "conflict_id": _hash({"existing": existing.observation_id, "incoming": observation.observation_id})[:16],
                "existing_observation_id": existing.observation_id,
                "incoming_observation_id": observation.observation_id,
                "provider_id": observation.provider_id,
                "instrument_id": observation.instrument_id,
                "source_timestamp_utc": observation.source_timestamp_utc,
                "detected_at_utc": utc_timestamp(),
                "rejection_code": MarketDataRejectionCode.MARKET_DATA_CONFLICT.value,
            }
            self._conflicts.append(conflict)
            return existing, False, conflict
        self._natural_index[natural] = observation.observation_id
        self._observations[observation.observation_id] = observation
        return observation, True, None

    def get(self, observation_id: str) -> MarketDataObservation | None:
        return self._observations.get(observation_id)

    def lookup(self, instrument_id: str, source_timestamp_utc: str, proof_domain: MarketDataProofDomain) -> tuple[MarketDataObservation, ...]:
        return tuple(
            item for item in self._observations.values()
            if item.instrument_id == instrument_id and item.source_timestamp_utc == source_timestamp_utc and item.proof_domain == proof_domain
        )

    def by_request(self, request_id: str = "", correlation_id: str = "") -> tuple[MarketDataObservation, ...]:
        return tuple(item for item in self._observations.values() if (request_id and item.request_id == request_id) or (correlation_id and item.correlation_id == correlation_id))

    def conflicts(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._conflicts)

    def snapshot(self) -> dict[str, Any]:
        return {
            "schemaVersion": EO_DJ_VERSION,
            "observationCount": len(self._observations),
            "conflictCount": len(self._conflicts),
            "observations": tuple(asdict(item) for item in self._observations.values()),
            "conflicts": tuple(self._conflicts),
        }


class MarketDataGateway:
    """Canonical decision-reachable market-data ingress."""

    def __init__(
        self,
        *,
        registry: ProviderAuthorityRegistry | None = None,
        evidence_store: MarketDataEvidenceStore | None = None,
        providers: dict[str, MarketDataProvider] | None = None,
        freshness_policy: FreshnessPolicy | None = None,
    ) -> None:
        self.registry = registry or ProviderAuthorityRegistry()
        self.evidence_store = evidence_store or MarketDataEvidenceStore()
        self.providers = providers or {}
        self.freshness_policy = freshness_policy or FreshnessPolicy("MD-FRESHNESS-PAPER-001", EO_DJ_VERSION, 60, 300)
        self.events: list[dict[str, Any]] = []

    def request_observation(
        self,
        *,
        provider_id: str,
        proof_domain: MarketDataProofDomain,
        symbol: str,
        observation_type: MarketObservationType,
        requested_at_utc: str,
        workflow_id: str = "",
        decision_object_id: str = "",
        correlation_id: str = "",
        request_id: str = "",
    ) -> MarketDataGatewayResult:
        correlation = correlation_id or f"MD-CORR-{_hash((provider_id, symbol, requested_at_utc))[:12]}"
        request = MarketDataProviderRequest(provider_id, proof_domain, symbol.upper(), symbol.upper(), observation_type, requested_at_utc, correlation, request_id or f"MD-REQ-{_hash((correlation, observation_type.value))[:12]}", workflow_id, decision_object_id)
        self._event("observation_requested", request=request)
        record, rejection = self.registry.resolve(provider_id, proof_domain, observation_type)
        if rejection:
            return self._reject(rejection, "provider authority policy rejected request", request=request, provider=record)
        provider = self.providers.get(provider_id)
        if provider is None:
            return self._reject(MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_CONFIGURED, "provider implementation is not configured", request=request, provider=record)
        try:
            result = provider.observe(request)
        except Exception as exc:
            return self._reject(MarketDataRejectionCode.MARKET_DATA_UNAVAILABLE, f"provider raised {type(exc).__name__}: {exc}", request=request, provider=record)
        if result.status != MarketDataResultStatus.SUCCESS:
            return self._reject(result.rejection_code or _status_rejection(result.status), result.provider_message or result.status.value, request=request, provider=record)
        assert record is not None
        observation = self._observation_from_result(record, request, result)
        if observation.symbol != request.symbol:
            return self._reject(MarketDataRejectionCode.MARKET_DATA_INSTRUMENT_MISMATCH, "provider returned mismatched instrument", request=request, provider=record)
        if observation.freshness.classification == MarketDataFreshnessStatus.UNKNOWN:
            return self._reject(MarketDataRejectionCode.MARKET_DATA_MALFORMED, "source timestamp freshness is unknown", request=request, provider=record)
        if observation.freshness.classification == MarketDataFreshnessStatus.STALE:
            return self._reject(MarketDataRejectionCode.MARKET_DATA_STALE, "observation is stale for current decision use", request=request, provider=record, observation=observation)
        if observation.freshness.classification == MarketDataFreshnessStatus.EXPIRED:
            return self._reject(MarketDataRejectionCode.MARKET_DATA_EXPIRED, "observation is expired for current decision use", request=request, provider=record, observation=observation)
        persisted, inserted, conflict = self.evidence_store.persist(observation)
        if conflict:
            self._event("observation_conflict_detected", request=request, provider=record, observation=observation, extra=conflict)
            return MarketDataGatewayResult(False, MarketDataResultStatus.CONFLICT, persisted, MarketDataRejectionCode.MARKET_DATA_CONFLICT, "conflicting observation rejected", tuple(self.events))
        self._event("observation_persisted" if inserted else "duplicate_observation_recognized", request=request, provider=record, observation=persisted)
        return MarketDataGatewayResult(True, MarketDataResultStatus.SUCCESS, persisted, None, "observation accepted", tuple(self.events))

    def _observation_from_result(self, record: ProviderAuthorityRecord, request: MarketDataProviderRequest, result: MarketDataProviderResult) -> MarketDataObservation:
        payload = _normalize_payload(result.payload)
        freshness = evaluate_freshness(result.source_timestamp_utc, request.requested_at_utc, self.freshness_policy)
        base = {
            "proof_domain": request.proof_domain.value,
            "provider_id": record.provider_id,
            "instrument_id": request.instrument_id,
            "symbol": request.symbol,
            "observation_type": request.observation_type.value,
            "source_timestamp_utc": _utc_text(result.source_timestamp_utc),
            "normalized_payload": payload,
            "schema_version": EO_DJ_VERSION,
        }
        observation_id = f"MDOBS-{_hash(base)[:24].upper()}"
        deterministic_hash = _hash({**base, "observation_id": observation_id})
        return MarketDataObservation(
            observation_id=observation_id,
            proof_domain=request.proof_domain,
            provider_id=record.provider_id,
            provider_classification=record.provider_classification,
            source_authority=record.provider_classification,
            instrument_id=request.instrument_id,
            symbol=request.symbol,
            venue=str(result.payload.get("venue", "UNKNOWN")).upper(),
            observation_type=request.observation_type,
            normalized_payload=payload,
            source_timestamp_utc=_utc_text(result.source_timestamp_utc),
            ingestion_timestamp_utc=utc_timestamp(),
            freshness=freshness,
            evidence_status=MarketDataEvidenceStatus.AUTHORITATIVE,
            adjustment_status=str(result.payload.get("adjustment_status", "UNADJUSTED")),
            correlation_id=request.correlation_id,
            request_id=request.request_id,
            persistence_id=observation_id,
            schema_version=EO_DJ_VERSION,
            deterministic_hash=deterministic_hash,
        )

    def _reject(self, code: MarketDataRejectionCode, message: str, *, request: MarketDataProviderRequest, provider: ProviderAuthorityRecord | None = None, observation: MarketDataObservation | None = None) -> MarketDataGatewayResult:
        event_name = "proof_domain_violation" if code in {MarketDataRejectionCode.MARKET_DATA_PROOF_DOMAIN_VIOLATION, MarketDataRejectionCode.MARKET_DATA_SYNTHETIC_SOURCE_REJECTED} else "observation_rejected"
        self._event(event_name, request=request, provider=provider, observation=observation, extra={"rejectionCode": code.value, "message": message})
        return MarketDataGatewayResult(False, MarketDataResultStatus.REJECTED, observation, code, message, tuple(self.events))

    def _event(self, event_type: str, *, request: MarketDataProviderRequest, provider: ProviderAuthorityRecord | None = None, observation: MarketDataObservation | None = None, extra: dict[str, Any] | None = None) -> None:
        self.events.append(
            {
                "eventType": event_type,
                "eventId": f"MD-EVT-{len(self.events) + 1:06d}",
                "timestampUtc": utc_timestamp(),
                "workflowId": request.workflow_id,
                "decisionObjectId": request.decision_object_id,
                "requestId": request.request_id,
                "correlationId": request.correlation_id,
                "providerId": request.provider_id,
                "providerAuthority": provider.provider_classification.value if provider else "UNKNOWN",
                "proofDomain": request.proof_domain.value,
                "instrumentId": request.instrument_id,
                "observationType": request.observation_type.value,
                "observationId": observation.observation_id if observation else "",
                **(extra or {}),
            }
        )


class MarketDataDecisionGuard:
    """Validate observation references before decision/authorization use."""

    def __init__(self, store: MarketDataEvidenceStore, registry: ProviderAuthorityRegistry) -> None:
        self.store = store
        self.registry = registry

    def validate(
        self,
        observation_id: str,
        *,
        accepted_proof_domains: tuple[MarketDataProofDomain, ...],
        instrument_id: str,
        observation_type: MarketObservationType,
        current_evidence_required: bool = True,
    ) -> MarketDataDecisionGuardResult:
        observation = self.store.get(observation_id)
        if observation is None:
            return self._reject(observation_id, MarketDataRejectionCode.MARKET_DATA_OBSERVATION_NOT_FOUND, "observation does not exist")
        if _hash({k: v for k, v in _observation_hash_payload(observation).items()}) != observation.deterministic_hash:
            return self._reject(observation_id, MarketDataRejectionCode.MARKET_DATA_INTEGRITY_FAILURE, "observation hash mismatch", observation)
        if observation.proof_domain not in accepted_proof_domains:
            return self._reject(observation_id, MarketDataRejectionCode.MARKET_DATA_PROOF_DOMAIN_VIOLATION, "proof domain is not accepted", observation)
        if observation.instrument_id != instrument_id.upper():
            return self._reject(observation_id, MarketDataRejectionCode.MARKET_DATA_INSTRUMENT_MISMATCH, "instrument mismatch", observation)
        if observation.observation_type != observation_type:
            return self._reject(observation_id, MarketDataRejectionCode.MARKET_DATA_UNSUPPORTED_OBSERVATION_TYPE, "observation type mismatch", observation)
        if observation.evidence_status not in {MarketDataEvidenceStatus.AUTHORITATIVE, MarketDataEvidenceStatus.HISTORICAL_ONLY}:
            return self._reject(observation_id, MarketDataRejectionCode.MARKET_DATA_UNAVAILABLE, "observation evidence is not authoritative", observation)
        if current_evidence_required and observation.freshness.classification != MarketDataFreshnessStatus.FRESH:
            code = MarketDataRejectionCode.MARKET_DATA_STALE if observation.freshness.classification == MarketDataFreshnessStatus.STALE else MarketDataRejectionCode.MARKET_DATA_EXPIRED
            return self._reject(observation_id, code, "observation is not fresh enough for current decision", observation)
        record = self.registry.get(observation.provider_id)
        if record is None or observation.proof_domain not in record.allowed_proof_domains:
            return self._reject(observation_id, MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_AUTHORIZED, "provider is not authorized for observation proof domain", observation)
        return MarketDataDecisionGuardResult(True, observation_id, None, "decision guard accepted", observation.proof_domain.value, observation.provider_id)

    def _reject(self, observation_id: str, code: MarketDataRejectionCode, message: str, observation: MarketDataObservation | None = None) -> MarketDataDecisionGuardResult:
        return MarketDataDecisionGuardResult(False, observation_id, code, message, observation.proof_domain.value if observation else "", observation.provider_id if observation else "")


class ControlledAuthoritativeMarketDataProvider:
    """Explicit test adapter for authoritative-provider boundary tests.

    The provider never generates fallback values. It returns only payloads
    supplied at construction time, so tests can prove the boundary without
    pretending an external vendor is configured.
    """

    def __init__(self, provider_id: str = "controlled-authoritative", observations: dict[str, dict[str, Any]] | None = None) -> None:
        self.provider_id = provider_id
        self._observations = {key.upper(): value for key, value in (observations or {}).items()}

    def observe(self, request: MarketDataProviderRequest) -> MarketDataProviderResult:
        payload = self._observations.get(request.symbol)
        if payload is None:
            return MarketDataProviderResult(MarketDataResultStatus.UNAVAILABLE, {}, "", "no supplied external observation", MarketDataRejectionCode.MARKET_DATA_UNAVAILABLE)
        return MarketDataProviderResult(MarketDataResultStatus.SUCCESS, payload, str(payload.get("source_timestamp_utc", request.requested_at_utc)))


class NonProductionMarketDataProvider:
    """Explicit replay/test/development provider barred from paper/live."""

    def __init__(self, provider_id: str, proof_domain: MarketDataProofDomain, payloads: dict[str, dict[str, Any]]) -> None:
        self.provider_id = provider_id
        self.proof_domain = proof_domain
        self._payloads = {key.upper(): value for key, value in payloads.items()}

    def observe(self, request: MarketDataProviderRequest) -> MarketDataProviderResult:
        if request.proof_domain != self.proof_domain:
            return MarketDataProviderResult(MarketDataResultStatus.REJECTED, {}, request.requested_at_utc, "non-production proof-domain mismatch", MarketDataRejectionCode.MARKET_DATA_SYNTHETIC_SOURCE_REJECTED)
        payload = self._payloads.get(request.symbol)
        if payload is None:
            return MarketDataProviderResult(MarketDataResultStatus.UNAVAILABLE, {}, "", "fixture observation not supplied", MarketDataRejectionCode.MARKET_DATA_UNAVAILABLE)
        return MarketDataProviderResult(MarketDataResultStatus.SUCCESS, payload, str(payload.get("source_timestamp_utc", request.requested_at_utc)))


class MarketDataProviderAbstractionLayer:
    """Compatibility facade over the EO-DJ gateway.

    Default construction has no authoritative provider implementation. Paper
    and live decisions therefore fail closed unless a caller explicitly supplies
    an authorized provider and provider id.
    """

    def __init__(
        self,
        *,
        gateway: MarketDataGateway | None = None,
        provider_id: str = "",
        proof_domain: MarketDataProofDomain = MarketDataProofDomain.PAPER_AUTHORITATIVE,
    ) -> None:
        self.gateway = gateway or MarketDataGateway()
        self.provider_id = provider_id
        self.proof_domain = proof_domain

    @classmethod
    def with_controlled_authoritative_provider(cls, *, provider_id: str = "controlled-authoritative", observations: dict[str, dict[str, Any]]) -> "MarketDataProviderAbstractionLayer":
        record = ProviderAuthorityRecord(provider_id, "Controlled External Adapter", "ControlledAuthoritativeMarketDataProvider", ProviderAuthorityClass.AUTHORITATIVE_EXTERNAL, (MarketDataProofDomain.PAPER_AUTHORITATIVE,), (MarketObservationType.QUOTE, MarketObservationType.MARKET_STATUS), ("US", "PAPER"), ("configured_observations",), True)
        registry = ProviderAuthorityRegistry((record,))
        gateway = MarketDataGateway(registry=registry, providers={provider_id: ControlledAuthoritativeMarketDataProvider(provider_id, observations)})
        return cls(gateway=gateway, provider_id=provider_id, proof_domain=MarketDataProofDomain.PAPER_AUTHORITATIVE)

    def snapshot(self, *, timestamp_utc: str, workflow_id: str = "", decision_object_id: str = "") -> dict[str, Any]:
        quote = self.get_quote("SPY", timestamp_utc, workflow_id=workflow_id, decision_object_id=decision_object_id)
        status = self.get_market_status(timestamp_utc)
        registry = self._registry(timestamp_utc)
        return {
            "layerName": "Market Data Provider Abstraction Layer",
            "engineeringOrder": "EO-DJ",
            "constitutionalMission": "Enforce authoritative market-data proof-domain boundary.",
            "constitutionalMode": "FAIL_CLOSED_INGRESS",
            "lawVII": {
                "executesWorkflows": False,
                "workflowTokenOwnership": "NEVER",
                "placesTrades": False,
                "generatesInvestmentDecisions": False,
                "brokerAccess": "OBSERVATION_REFERENCE_ONLY",
                "commanderOverride": "FORBIDDEN",
            },
            "providerRegistry": tuple(asdict(item) for item in registry),
            "providerConfiguration": {
                "enabledProviders": tuple(item.providerId for item in registry if item.enabled),
                "primaryProvider": self.provider_id,
                "fallbackProviders": (),
                "mockFallbackEnabled": False,
                "syntheticFallbackEnabled": False,
                "authoritativeProviderConfigured": bool(self.provider_id and self.provider_id in self.gateway.providers),
                "environment": self.proof_domain.value,
            },
            "normalizedObjects": {
                "quotes": tuple(item for item in (quote.get("normalizedObject"),) if item),
                "marketStatus": tuple(item for item in (status.get("normalizedObject"),) if item),
            },
            "callHistory": tuple(event for event in self.gateway.events[-20:]),
            "rejections": tuple(event for event in self.gateway.events if event.get("rejectionCode")),
            "evidenceStore": self.gateway.evidence_store.snapshot(),
            "mockProviderControls": {"enabled": False, "productionReachable": False},
            "syntheticProviderControls": {"enabled": False, "productionReachable": False},
            "commanderVisibility": {
                "currentPrimaryProvider": self.provider_id or "UNCONFIGURED",
                "activeFallbackProvider": "",
                "providerHealth": "UNCONFIGURED" if not self.provider_id else "CONFIGURED",
                "dataFreshness": (quote.get("normalizedObject") or {}).get("validation", {}).get("freshnessStatus", "UNKNOWN"),
            },
        }

    def get_quote(self, symbol: str, timestamp_utc: str, *, provider_id: str = "", workflow_id: str = "", decision_object_id: str = "") -> dict[str, Any]:
        selected = provider_id or self.provider_id
        if not selected:
            result = MarketDataGatewayResult(False, MarketDataResultStatus.REJECTED, None, MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_CONFIGURED, "no authoritative provider configured", ())
        else:
            result = self.gateway.request_observation(provider_id=selected, proof_domain=self.proof_domain, symbol=symbol, observation_type=MarketObservationType.QUOTE, requested_at_utc=timestamp_utc, workflow_id=workflow_id, decision_object_id=decision_object_id)
        return self._quote_response(symbol, timestamp_utc, selected, result)

    def get_market_status(self, timestamp_utc: str) -> dict[str, Any]:
        if not self.provider_id:
            return {"normalizedObject": None, "auditRecord": {"rejectionCode": MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_CONFIGURED.value, "timestamp": timestamp_utc}}
        result = self.gateway.request_observation(provider_id=self.provider_id, proof_domain=self.proof_domain, symbol="MARKET", observation_type=MarketObservationType.MARKET_STATUS, requested_at_utc=timestamp_utc)
        if not result.accepted or result.observation is None:
            return {"normalizedObject": None, "auditRecord": _audit_from_gateway(result, self.provider_id, "get_market_status", timestamp_utc)}
        status = result.observation.normalized_payload.get("status", "UNKNOWN")
        return {"normalizedObject": {"objectType": "NormalizedMarketStatus", "status": status, "observationId": result.observation.observation_id, "sourceAttribution": _source_from_observation(result.observation), "validation": _validation_from_observation(result.observation)}, "auditRecord": _audit_from_gateway(result, self.provider_id, "get_market_status", timestamp_utc)}

    def get_news(self, symbols: tuple[str, ...], timestamp_utc: str) -> dict[str, Any]:
        return self._unsupported("news", ",".join(symbols), timestamp_utc)

    def get_sector_data(self, timestamp_utc: str) -> dict[str, Any]:
        return self._unsupported("sectorData", "SECTOR", timestamp_utc)

    def get_economic_calendar(self, timestamp_utc: str) -> dict[str, Any]:
        return self._unsupported("economicCalendar", "MACRO", timestamp_utc)

    def get_options_snapshot(self, symbol: str, timestamp_utc: str, *, provider_id: str = "") -> dict[str, Any]:
        return self._unsupported("options", symbol, timestamp_utc)

    def _quote_response(self, symbol: str, timestamp_utc: str, provider_id: str, result: MarketDataGatewayResult) -> dict[str, Any]:
        if not result.accepted or result.observation is None:
            return {"normalizedObject": None, "auditRecord": _audit_from_gateway(result, provider_id, "get_quote", timestamp_utc)}
        observation = result.observation
        payload = observation.normalized_payload
        normalized = {
            "objectType": "NormalizedQuote",
            "symbol": observation.symbol,
            "bid": str(payload.get("bid", "")),
            "ask": str(payload.get("ask", "")),
            "last": str(payload.get("last", "")),
            "volume": str(payload.get("volume", "")),
            "observationId": observation.observation_id,
            "marketEvidenceReference": observation.observation_id,
            "sourceAttribution": _source_from_observation(observation),
            "validation": _validation_from_observation(observation),
        }
        return {"normalizedObject": normalized, "auditRecord": _audit_from_gateway(result, provider_id, "get_quote", timestamp_utc)}

    def _unsupported(self, capability: str, symbol: str, timestamp_utc: str) -> dict[str, Any]:
        return {
            "normalizedObject": {
                "objectType": "UnsupportedCapabilityResponse",
                "capability": capability,
                "symbol": symbol.upper(),
                "supported": False,
                "reason": "Capability requires an explicitly configured authoritative provider.",
                "validation": {"validationStatus": "UNSUPPORTED", "timestamp": timestamp_utc},
            },
            "auditRecord": {"rejectionCode": MarketDataRejectionCode.MARKET_DATA_UNSUPPORTED_OBSERVATION_TYPE.value, "timestamp": timestamp_utc},
        }

    def _registry(self, timestamp_utc: str) -> tuple[ProviderRegistryEntry, ...]:
        rows = []
        for record in self.gateway.registry.all():
            rows.append(
                ProviderRegistryEntry(
                    record.provider_id,
                    record.provider_name,
                    record.provider_classification.value,
                    record.enabled and record.provider_id in self.gateway.providers,
                    "production" if record.provider_classification == ProviderAuthorityClass.AUTHORITATIVE_EXTERNAL else record.provider_classification.value.lower(),
                    _caps(**{_capability_name(item): "YES" for item in record.supported_observation_types}),
                    1 if record.provider_id == self.provider_id else 99,
                    0,
                    {"quoteCostUsd": "PROVIDER_POLICY", "dailyBudgetUsd": "COMMANDER_REQUIRED"},
                    {"allowedRequests": 0, "usedRequests": 0, "remainingRequests": 0, "resetTime": timestamp_utc, "cooldownStatus": "UNKNOWN", "backoffRules": "PROVIDER_POLICY", "throttlingEvents": 0},
                    "CONFIGURED" if record.provider_id in self.gateway.providers else "NOT_CONFIGURED",
                    "Configured" if record.provider_id in self.gateway.providers else "Disabled",
                    "",
                    "",
                    0,
                    "APPROVED_BY_EO_DJ_POLICY" if MarketDataProofDomain.PAPER_AUTHORITATIVE in record.allowed_proof_domains else "NON_PRODUCTION_ONLY",
                )
            )
        return tuple(rows)


def default_provider_authority_records() -> tuple[ProviderAuthorityRecord, ...]:
    return (
        ProviderAuthorityRecord("external-paper", "External Paper Market Data", "operator_configured_adapter", ProviderAuthorityClass.AUTHORITATIVE_EXTERNAL, (MarketDataProofDomain.PAPER_AUTHORITATIVE,), (MarketObservationType.QUOTE, MarketObservationType.MARKET_STATUS), ("US",), ("provider_adapter", "credentials_reference"), False),
        ProviderAuthorityRecord("external-live", "External Live Market Data", "operator_configured_adapter", ProviderAuthorityClass.AUTHORITATIVE_EXTERNAL, (MarketDataProofDomain.LIVE_AUTHORITATIVE,), (MarketObservationType.QUOTE, MarketObservationType.MARKET_STATUS), ("US",), ("provider_adapter", "credentials_reference", "live_approval"), False),
        ProviderAuthorityRecord("replay-market-data", "Replay Market Data", "NonProductionMarketDataProvider", ProviderAuthorityClass.REPLAY_INPUT, (MarketDataProofDomain.REPLAY,), (MarketObservationType.QUOTE, MarketObservationType.MARKET_STATUS), ("REPLAY",), ("dataset_id",), True),
        ProviderAuthorityRecord("test-market-data", "Test Market Data Fixture", "NonProductionMarketDataProvider", ProviderAuthorityClass.TEST_FIXTURE, (MarketDataProofDomain.TEST,), (MarketObservationType.QUOTE, MarketObservationType.MARKET_STATUS), ("TEST",), ("fixture_id",), True),
        ProviderAuthorityRecord("development-simulation-market-data", "Development Simulation Market Data", "NonProductionMarketDataProvider", ProviderAuthorityClass.DEVELOPMENT_SIMULATION, (MarketDataProofDomain.DEVELOPMENT_SIMULATION,), (MarketObservationType.QUOTE, MarketObservationType.MARKET_STATUS), ("DEV",), ("explicit_development_mode",), True),
    )


def evaluate_freshness(source_timestamp_utc: str, evaluated_at_utc: str, policy: FreshnessPolicy) -> FreshnessEvaluation:
    source = _parse_utc(source_timestamp_utc)
    evaluated = _parse_utc(evaluated_at_utc)
    if source is None or evaluated is None:
        return FreshnessEvaluation(policy.policy_id, policy.version, source_timestamp_utc, evaluated_at_utc, None, policy.maximum_age_seconds, policy.expire_after_seconds, policy.market_session_context, MarketDataFreshnessStatus.UNKNOWN)
    age = max(0, int((evaluated - source).total_seconds()))
    if age <= policy.maximum_age_seconds:
        status = MarketDataFreshnessStatus.FRESH
    elif age <= policy.expire_after_seconds:
        status = MarketDataFreshnessStatus.STALE
    else:
        status = MarketDataFreshnessStatus.EXPIRED
    return FreshnessEvaluation(policy.policy_id, policy.version, _utc_text(source_timestamp_utc), _utc_text(evaluated_at_utc), age, policy.maximum_age_seconds, policy.expire_after_seconds, policy.market_session_context, status)


def market_source_inventory() -> tuple[dict[str, Any], ...]:
    return (
        {"source_id": "MD-SRC-001", "file": "src/argos/control_panel/market_data_provider.py", "symbol": "MarketDataGateway", "classification": "canonical ingress gateway", "production_reachable": True, "status": "authoritative boundary"},
        {"source_id": "MD-SRC-002", "file": "src/argos/control_panel/market_data_provider.py", "symbol": "ControlledAuthoritativeMarketDataProvider", "classification": "authoritative external adapter stub for tests", "production_reachable": False, "status": "explicit injection only"},
        {"source_id": "MD-SRC-003", "file": "src/argos/control_panel/market_data_provider.py", "symbol": "NonProductionMarketDataProvider", "classification": "test/replay/development simulation", "production_reachable": False, "status": "barred from paper/live by registry"},
        {"source_id": "MD-SRC-004", "file": "src/argos/trader/paper_brokerage.py", "symbol": "PaperBrokerMarketDataAdapter", "classification": "decision sink", "production_reachable": True, "status": "requires EO-DJ observation"},
        {"source_id": "MD-SRC-005", "file": "src/argos/control_panel/position_lifecycle_manager.py", "symbol": "monitor_positions", "classification": "decision sink", "production_reachable": True, "status": "uses EO-DJ snapshot facade"},
    )


def production_reachability_report() -> dict[str, Any]:
    return {
        "schemaVersion": EO_DJ_VERSION,
        "mockFallbackEnabled": False,
        "syntheticFallbackEnabled": False,
        "defaultProviderConfigured": False,
        "productionReachableSyntheticSources": (),
        "remainingUnresolvedPaths": (),
        "authoritativeProviderConfigured": False,
    }


def _normalize_payload(payload: dict[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in payload.items():
        if key in {"bid", "ask", "last", "close", "open", "high", "low", "volume"}:
            try:
                normalized[key] = str(Decimal(str(value)))
            except (InvalidOperation, ValueError):
                raise ValueError(f"malformed decimal market-data field: {key}")
        elif key not in {"source_timestamp_utc"}:
            normalized[key] = str(value)
    return normalized


def _source_from_observation(observation: MarketDataObservation) -> dict[str, Any]:
    return {
        "providerId": observation.provider_id,
        "providerType": observation.provider_classification.value,
        "sourceAuthority": observation.source_authority.value,
        "proofDomain": observation.proof_domain.value,
        "requestId": observation.request_id,
        "correlationId": observation.correlation_id,
        "dataTimestamp": observation.source_timestamp_utc,
        "ingestionTimestamp": observation.ingestion_timestamp_utc,
        "freshness": observation.freshness.classification.value,
        "rawPayloadReference": observation.persistence_id,
        "deterministicHash": observation.deterministic_hash,
        "schemaVersion": observation.schema_version,
    }


def _validation_from_observation(observation: MarketDataObservation) -> dict[str, Any]:
    return {
        "validationStatus": "VALID" if observation.evidence_status == MarketDataEvidenceStatus.AUTHORITATIVE else observation.evidence_status.value,
        "timestamp": observation.ingestion_timestamp_utc,
        "symbol": observation.symbol,
        "freshnessStatus": observation.freshness.classification.value,
        "ageSeconds": observation.freshness.age_seconds,
        "policyId": observation.freshness.policy_id,
        "policyVersion": observation.freshness.policy_version,
        "staleData": observation.freshness.classification != MarketDataFreshnessStatus.FRESH,
        "symbolMismatch": False,
        "malformedPayload": False,
    }


def _audit_from_gateway(result: MarketDataGatewayResult, provider_id: str, endpoint: str, timestamp_utc: str) -> dict[str, Any]:
    return {
        "auditId": f"MDPA-AUD-{_hash((provider_id, endpoint, timestamp_utc))[:12].upper()}",
        "provider": provider_id,
        "endpoint": endpoint,
        "timestamp": timestamp_utc,
        "rejectionCode": result.rejection_code.value if result.rejection_code else "",
        "accepted": result.accepted,
        "observationId": result.observation.observation_id if result.observation else "",
        "events": result.audit_events,
        "cost": {"estimatedCostUsd": 0.0, "actualCostUsd": 0.0},
    }


def _status_rejection(status: MarketDataResultStatus) -> MarketDataRejectionCode:
    return {
        MarketDataResultStatus.UNAVAILABLE: MarketDataRejectionCode.MARKET_DATA_UNAVAILABLE,
        MarketDataResultStatus.STALE: MarketDataRejectionCode.MARKET_DATA_STALE,
        MarketDataResultStatus.UNSUPPORTED: MarketDataRejectionCode.MARKET_DATA_UNSUPPORTED_OBSERVATION_TYPE,
        MarketDataResultStatus.MALFORMED: MarketDataRejectionCode.MARKET_DATA_MALFORMED,
        MarketDataResultStatus.CONFIGURATION_FAILURE: MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_CONFIGURED,
        MarketDataResultStatus.RATE_LIMITED: MarketDataRejectionCode.MARKET_DATA_UNAVAILABLE,
        MarketDataResultStatus.CONFLICT: MarketDataRejectionCode.MARKET_DATA_CONFLICT,
    }.get(status, MarketDataRejectionCode.MARKET_DATA_UNAVAILABLE)


def _natural_identity(observation: MarketDataObservation) -> str:
    return _hash(
        {
            "provider_id": observation.provider_id,
            "instrument_id": observation.instrument_id,
            "observation_type": observation.observation_type.value,
            "source_timestamp_utc": observation.source_timestamp_utc,
            "proof_domain": observation.proof_domain.value,
            "schema_version": observation.schema_version,
        }
    )


def _observation_hash_payload(observation: MarketDataObservation) -> dict[str, Any]:
    return {
        "proof_domain": observation.proof_domain.value,
        "provider_id": observation.provider_id,
        "instrument_id": observation.instrument_id,
        "symbol": observation.symbol,
        "observation_type": observation.observation_type.value,
        "source_timestamp_utc": observation.source_timestamp_utc,
        "normalized_payload": observation.normalized_payload,
        "schema_version": observation.schema_version,
        "observation_id": observation.observation_id,
    }


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _caps(**overrides: str) -> dict[str, str]:
    return {capability: overrides.get(capability, "NO") for capability in CAPABILITIES}


def _capability_name(observation_type: MarketObservationType) -> str:
    return {
        MarketObservationType.QUOTE: "quotes",
        MarketObservationType.TRADE: "trades",
        MarketObservationType.BAR: "intradayBars",
        MarketObservationType.ORDER_BOOK: "orderBooks",
        MarketObservationType.MARKET_STATUS: "marketStatus",
        MarketObservationType.CORPORATE_ACTION: "corporateActions",
        MarketObservationType.SECURITY_IDENTIFIER: "securityIdentifiers",
    }.get(observation_type, observation_type.value)


def _utc_text(value: str) -> str:
    return value.replace("+00:00", "Z")


def _parse_utc(value: str):
    from datetime import datetime

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
