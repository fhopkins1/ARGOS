"""Broker Integration Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Protocol

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .offices import TRADER_GROUP_ID
from .order_management import BrokerOrderMessage, OrderManagementOffice


BROKER_INTEGRATION_OFFICE_ID = "TRADER-OFFICE-003"
BROKER_INTEGRATION_STAFF_ID = "STF-063"


class BrokerConnectionStatus(str, Enum):
    """Broker connection status."""

    CONNECTED = "connected"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"


class BrokerResponseType(str, Enum):
    """Canonical broker response event types."""

    ACKNOWLEDGEMENT = "acknowledgement"
    FILL = "fill"
    PARTIAL_FILL = "partial_fill"
    CANCELLATION = "cancellation"
    REJECTION = "rejection"
    EXECUTION_UPDATE = "execution_update"


@dataclass(frozen=True)
class BrokerAuthenticationContext:
    """Redacted broker authentication context."""

    auth_context_id: str
    credential_reference: str
    authenticated: bool


@dataclass(frozen=True)
class BrokerExecutionRequest:
    """Canonical BIO execution request."""

    execution_request_id: str
    order_id: str
    broker_id: str
    strategy_id: str
    timestamp_utc: str
    correlation_id: str
    authentication_context: BrokerAuthenticationContext
    execution_metadata: dict[str, object]


@dataclass(frozen=True)
class BrokerSpecificRequest:
    """Broker-specific request contained inside BIO only."""

    broker_id: str
    broker_payload: dict[str, object]


@dataclass(frozen=True)
class RawBrokerResponse:
    """Raw broker response retained inside BIO."""

    broker_id: str
    broker_order_id: str
    response_type: BrokerResponseType
    order_id: str
    execution_id: str
    fill_id: str | None
    position_id: str
    quantity: float
    filled_quantity: float
    remaining_quantity: float
    price: float
    status: str
    latency_ms: int
    timestamp_utc: str
    raw_payload_hash: str


@dataclass(frozen=True)
class CanonicalBrokerEvent:
    """Canonical ARGOS broker event."""

    event_id: str
    broker_id: str
    broker_order_id: str
    argos_order_id: str
    response_type: BrokerResponseType
    execution_id: str
    fill_id: str | None
    position_id: str
    quantity: float
    filled_quantity: float
    remaining_quantity: float
    price: float
    status: str
    timestamp_utc: str
    correlation_id: str


@dataclass(frozen=True)
class BrokerCapabilityProfile:
    """Broker capability profile."""

    broker_id: str
    supported_order_types: tuple[str, ...]
    supported_asset_classes: tuple[str, ...]
    supports_paper_trading: bool
    api_version: str
    max_requests_per_minute: int


@dataclass(frozen=True)
class BrokerHealthStatus:
    """Broker health status."""

    broker_id: str
    connection_status: BrokerConnectionStatus
    authentication_status: str
    api_available: bool
    broker_latency_ms: int
    execution_latency_ms: int
    message_integrity: bool
    rate_limit_remaining: int
    api_version_compatible: bool
    exchange_available: bool


@dataclass(frozen=True)
class BrokerIntegrationAnomaly:
    """BIO anomaly."""

    anomaly_id: str
    classification: str
    severity: str
    broker_id: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class BrokerIdentifierMapping:
    """Deterministic broker identifier mapping."""

    argos_order_id: str
    broker_order_id: str
    execution_id: str
    fill_id: str | None
    position_id: str
    audit_id: str


@dataclass(frozen=True)
class BrokerIntegrationCaseFile:
    """Case File generated for BIO anomalies."""

    case_file_id: str
    broker_id: str
    anomalies: tuple[BrokerIntegrationAnomaly, ...]
    reconstructable: bool


@dataclass(frozen=True)
class BrokerIntegrationSystemPrompt:
    """BIO governing prompt artifact."""

    prompt_id: str
    version: str
    prompt_text: str


class BrokerAdapter(Protocol):
    """Common execution interface implemented by broker plug-ins."""

    broker_id: str

    def capability_profile(self) -> BrokerCapabilityProfile:
        """Return broker capabilities."""

    def health_status(self) -> BrokerHealthStatus:
        """Return broker health."""

    def submit_order(self, request: BrokerSpecificRequest) -> RawBrokerResponse:
        """Submit an order through the broker adapter."""


class DeterministicPaperBrokerAdapter:
    """Deterministic paper/simulation broker adapter."""

    broker_id = "BROKER-PAPER"

    def __init__(self) -> None:
        self._submitted: set[str] = set()

    def capability_profile(self) -> BrokerCapabilityProfile:
        return BrokerCapabilityProfile(self.broker_id, ("market", "limit", "stop"), ("equity", "option", "crypto"), True, "1.0.0", 120)

    def health_status(self) -> BrokerHealthStatus:
        return BrokerHealthStatus(self.broker_id, BrokerConnectionStatus.CONNECTED, "authenticated", True, 25, 40, True, 119, True, True)

    def submit_order(self, request: BrokerSpecificRequest) -> RawBrokerResponse:
        correlation_id = str(request.broker_payload["correlation_id"])
        order_id = str(request.broker_payload["order_id"])
        quantity = float(request.broker_payload["quantity"])
        if correlation_id in self._submitted:
            status = "duplicate"
            response_type = BrokerResponseType.REJECTION
        else:
            self._submitted.add(correlation_id)
            status = "acknowledged"
            response_type = BrokerResponseType.ACKNOWLEDGEMENT
        raw_payload_hash = hashlib.sha256(json.dumps(request.broker_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return RawBrokerResponse(
            self.broker_id,
            f"BRK-{order_id}",
            response_type,
            order_id,
            f"EXEC-{order_id}",
            None,
            str(request.broker_payload["position_id"]),
            quantity,
            0.0,
            quantity,
            float(request.broker_payload.get("price", 0.0)),
            status,
            40,
            utc_timestamp(),
            raw_payload_hash,
        )


class BrokerAdapterRegistry:
    """Registry of broker adapter plug-ins."""

    def __init__(self) -> None:
        self._adapters: dict[str, BrokerAdapter] = {}

    def register(self, adapter: BrokerAdapter) -> None:
        if adapter.broker_id in self._adapters:
            raise ValueError(f"broker adapter already registered: {adapter.broker_id}")
        self._adapters[adapter.broker_id] = adapter

    def get(self, broker_id: str) -> BrokerAdapter:
        if broker_id not in self._adapters:
            raise ValueError(f"unknown broker adapter: {broker_id}")
        return self._adapters[broker_id]

    def all(self) -> tuple[BrokerAdapter, ...]:
        return tuple(self._adapters[key] for key in sorted(self._adapters))


class BrokerRequestTranslator:
    """Translate canonical ARGOS requests into broker-specific payloads inside BIO."""

    def translate(self, request: BrokerExecutionRequest) -> BrokerSpecificRequest:
        payload = {
            "execution_request_id": request.execution_request_id,
            "order_id": request.order_id,
            "strategy_id": request.strategy_id,
            "timestamp_utc": request.timestamp_utc,
            "correlation_id": request.correlation_id,
            "authentication_context_id": request.authentication_context.auth_context_id,
            **request.execution_metadata,
        }
        return BrokerSpecificRequest(request.broker_id, payload)


class BrokerResponseNormalizer:
    """Normalize broker responses into canonical ARGOS events."""

    def normalize(self, response: RawBrokerResponse, correlation_id: str) -> CanonicalBrokerEvent:
        return CanonicalBrokerEvent(
            f"BE-{hashlib.sha256(f'{response.broker_id}:{response.broker_order_id}:{response.execution_id}:{response.status}'.encode('utf-8')).hexdigest()[:10].upper()}",
            response.broker_id,
            response.broker_order_id,
            response.order_id,
            response.response_type,
            response.execution_id,
            response.fill_id,
            response.position_id,
            response.quantity,
            response.filled_quantity,
            response.remaining_quantity,
            response.price,
            response.status,
            response.timestamp_utc,
            correlation_id,
        )


class BrokerHealthMonitor:
    """Detect broker health anomalies."""

    def inspect(self, health: BrokerHealthStatus) -> tuple[BrokerIntegrationAnomaly, ...]:
        anomalies = []
        if health.connection_status != BrokerConnectionStatus.CONNECTED:
            anomalies.append(_anomaly("connection_failure", health.broker_id, health.connection_status.value))
        if health.authentication_status != "authenticated":
            anomalies.append(_anomaly("authentication_failure", health.broker_id, health.authentication_status))
        if not health.api_available:
            anomalies.append(_anomaly("broker_outage", health.broker_id, "api_unavailable"))
        if health.broker_latency_ms > 1000 or health.execution_latency_ms > 1000:
            anomalies.append(_anomaly("latency_degradation", health.broker_id, f"{health.broker_latency_ms}:{health.execution_latency_ms}"))
        if not health.message_integrity:
            anomalies.append(_anomaly("message_integrity_failure", health.broker_id, "integrity_false"))
        if health.rate_limit_remaining <= 0:
            anomalies.append(_anomaly("rate_limit_exhausted", health.broker_id, "rate_limit_zero"))
        if not health.api_version_compatible:
            anomalies.append(_anomaly("api_schema_change", health.broker_id, "version_incompatible"))
        if not health.exchange_available:
            anomalies.append(_anomaly("execution_venue_failure", health.broker_id, "exchange_unavailable"))
        return tuple(anomalies)


class BrokerInteractionMonitor:
    """Detect broker interaction anomalies."""

    def inspect(
        self,
        request: BrokerExecutionRequest,
        event: CanonicalBrokerEvent | None,
        submitted_correlations: tuple[str, ...],
    ) -> tuple[BrokerIntegrationAnomaly, ...]:
        anomalies = []
        if request.correlation_id in submitted_correlations:
            anomalies.append(_anomaly("duplicate_submission", request.broker_id, request.correlation_id))
        if event is None:
            anomalies.append(_anomaly("missing_acknowledgement", request.broker_id, request.order_id))
            return tuple(anomalies)
        if event.argos_order_id != request.order_id:
            anomalies.append(_anomaly("unexpected_broker_response", request.broker_id, event.argos_order_id))
        if event.status == "timeout":
            anomalies.append(_anomaly("communication_timeout", request.broker_id, event.event_id))
        return tuple(anomalies)


class BrokerMappingRegistry:
    """Maintain deterministic mappings between ARGOS and broker identifiers."""

    def __init__(self) -> None:
        self._mappings: dict[str, BrokerIdentifierMapping] = {}

    def record(self, event: CanonicalBrokerEvent) -> BrokerIdentifierMapping:
        mapping = BrokerIdentifierMapping(
            event.argos_order_id,
            event.broker_order_id,
            event.execution_id,
            event.fill_id,
            event.position_id,
            f"AUD-{event.event_id}",
        )
        self._mappings[event.argos_order_id] = mapping
        return mapping

    def get(self, order_id: str) -> BrokerIdentifierMapping | None:
        return self._mappings.get(order_id)


class BrokerIntegrationOffice:
    """Enterprise abstraction layer for broker integrations."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
        adapter_registry: BrokerAdapterRegistry | None = None,
    ) -> None:
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.prompt_repository = prompt_repository
        self.adapters = adapter_registry or BrokerAdapterRegistry()
        if adapter_registry is None:
            self.adapters.register(DeterministicPaperBrokerAdapter())
        self.translator = BrokerRequestTranslator()
        self.normalizer = BrokerResponseNormalizer()
        self.health_monitor = BrokerHealthMonitor()
        self.interaction_monitor = BrokerInteractionMonitor()
        self.mapping_registry = BrokerMappingRegistry()
        self._message_history: list[dict[str, object]] = []
        self._submitted_correlations: list[str] = []

    @property
    def message_history(self) -> tuple[dict[str, object], ...]:
        return tuple(self._message_history)

    def submit_execution_request(
        self,
        request: BrokerExecutionRequest,
        order_management_office: OrderManagementOffice,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Submit a canonical execution request through a broker adapter."""
        self.configuration_service.validate_startup()
        health = self.adapters.get(request.broker_id).health_status()
        health_anomalies = self.health_monitor.inspect(health)
        if health_anomalies:
            return {"broker_integration_case_file": self.generate_case_file(request.broker_id, health_anomalies, case_file_id, trade_cycle_id, document_sequence)}

        duplicate_check = self.interaction_monitor.inspect(request, None, tuple(self._submitted_correlations)) if request.correlation_id in self._submitted_correlations else ()
        if duplicate_check:
            return {"broker_integration_case_file": self.generate_case_file(request.broker_id, duplicate_check, case_file_id, trade_cycle_id, document_sequence)}

        broker_request = self.translator.translate(request)
        raw_response = self.adapters.get(request.broker_id).submit_order(broker_request)
        self._submitted_correlations.append(request.correlation_id)
        event = self.normalizer.normalize(raw_response, request.correlation_id)
        anomalies = self.interaction_monitor.inspect(request, event, ())
        self._record_history("request", request)
        self._record_history("broker_specific_request", broker_request)
        self._record_history("raw_response", raw_response)
        self._record_history("canonical_event", event)
        mapping = self.mapping_registry.record(event)
        omo_message = BrokerOrderMessage(
            event.event_id,
            event.argos_order_id,
            event.response_type.value,
            event.quantity,
            event.filled_quantity,
            event.remaining_quantity,
            event.price,
            event.status,
            event.timestamp_utc,
        )
        order_management_office.record_broker_message(event.argos_order_id, omo_message, case_file_id, trade_cycle_id, document_sequence + 1)
        if anomalies:
            return {"broker_integration_case_file": self.generate_case_file(request.broker_id, anomalies, case_file_id, trade_cycle_id, document_sequence)}
        event_contract = self._event_contract(request, event, mapping, health, case_file_id, trade_cycle_id, document_sequence)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, event_contract.contract_id, event_contract.to_dict())
        self.audit_service.record_document_creation(event_contract)
        return {"canonical_broker_event": event_contract}

    def generate_case_file(
        self,
        broker_id: str,
        anomalies: tuple[BrokerIntegrationAnomaly, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        """Generate a Broker Integration Case File."""
        case_file = BrokerIntegrationCaseFile(f"BICF-{document_sequence:06d}", broker_id, anomalies, True)
        payload = {
            "office_id": BROKER_INTEGRATION_OFFICE_ID,
            "office_name": "Broker Integration Office",
            "case_file": case_file,
            "message_history": self.message_history,
            "broker_specific_formats_exposed": False,
            "history_overwritten": False,
            "message_loss_detected": False,
        }
        contract = _contract("BROKER_CASE_FILE", case_file_id, trade_cycle_id, document_sequence, (), "Broker Integration Case File.", payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract

    def capability_profiles(self) -> tuple[BrokerCapabilityProfile, ...]:
        """Return broker capability profiles."""
        return tuple(adapter.capability_profile() for adapter in self.adapters.all())

    def health_statuses(self) -> tuple[BrokerHealthStatus, ...]:
        """Return broker health statuses."""
        return tuple(adapter.health_status() for adapter in self.adapters.all())

    def system_prompt(self) -> BrokerIntegrationSystemPrompt:
        """Return BIO governing system prompt."""
        return BrokerIntegrationSystemPrompt(
            "PROMPT-BIO-055",
            "1.0.0",
            (
                "You are the Broker Integration Office (BIO) of ARGOS. Provide deterministic, secure, and reliable "
                "communication between the Trader Group and external execution venues while isolating broker-specific "
                "behavior from the enterprise. Do not determine what should be traded, when trades should occur, or "
                "alter Executive intent. Translate deterministic execution requests into broker-specific operations, "
                "normalize every response into canonical ARGOS events, preserve complete auditability, and generate "
                "Broker Integration Case Files for every anomaly."
            ),
        )

    def _record_history(self, entry_type: str, value: object) -> None:
        self._message_history.append({"sequence": len(self._message_history) + 1, "entry_type": entry_type, "payload": _json_ready(value)})

    def _event_contract(
        self,
        request: BrokerExecutionRequest,
        event: CanonicalBrokerEvent,
        mapping: BrokerIdentifierMapping,
        health: BrokerHealthStatus,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        payload = {
            "office_id": BROKER_INTEGRATION_OFFICE_ID,
            "office_name": "Broker Integration Office",
            "broker_integration_system_prompt": self.system_prompt(),
            "canonical_broker_event": event,
            "identifier_mapping": mapping,
            "broker_health_status": health,
            "broker_capability_profile": self.adapters.get(request.broker_id).capability_profile(),
            "message_history": self.message_history,
            "broker_specific_formats_exposed": False,
            "executive_intent_modified": False,
        }
        return _contract("BROKER_EVENT", case_file_id, trade_cycle_id, document_sequence, (), "Canonical broker event.", payload)


def _anomaly(classification: str, broker_id: str, evidence: str) -> BrokerIntegrationAnomaly:
    return BrokerIntegrationAnomaly(
        f"BIA-{hashlib.sha256(f'{classification}:{broker_id}:{evidence}'.encode('utf-8')).hexdigest()[:8].upper()}",
        classification,
        "high" if classification in {"connection_failure", "authentication_failure", "broker_outage", "duplicate_submission"} else "medium",
        broker_id,
        (evidence,),
    )


def _contract(
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    document_sequence: int,
    parent_contract_ids: tuple[str, ...],
    human_summary: str,
    payload: dict[str, Any],
) -> OperationalContract:
    created = utc_timestamp()
    normalized_payload = _json_ready(payload)
    signature_hash = hashlib.sha256(json.dumps(normalized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        parent_contract_ids=parent_contract_ids,
        produced_by_staff_id=BROKER_INTEGRATION_STAFF_ID,
        produced_by_group_id=TRADER_GROUP_ID,
        intended_consumer_group_id=TRADER_GROUP_ID,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=human_summary,
        machine_payload=normalized_payload,
        signature_hash=signature_hash,
        source_reference_ids=parent_contract_ids,
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
