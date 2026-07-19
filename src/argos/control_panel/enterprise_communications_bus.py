"""Enterprise Communications Bus for ARGOS EO-CL."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
from typing import Any
from uuid import uuid4

from argos.foundation.contracts import utc_timestamp


class EnterpriseMessageKind(str, Enum):
    COMMAND = "COMMAND"
    EVENT = "EVENT"
    OBSERVATION = "OBSERVATION"
    QUERY = "QUERY"
    QUERY_RESPONSE = "QUERY_RESPONSE"
    WORKFLOW_HANDOFF = "WORKFLOW_HANDOFF"
    MISSION_MESSAGE = "MISSION_MESSAGE"
    HEALTH_SIGNAL = "HEALTH_SIGNAL"
    POLICY_PUBLICATION = "POLICY_PUBLICATION"
    AUDIT_NOTIFICATION = "AUDIT_NOTIFICATION"
    RECOVERY_MESSAGE = "RECOVERY_MESSAGE"
    SYSTEM_NOTIFICATION = "SYSTEM_NOTIFICATION"


class MessageMode(str, Enum):
    PAPER = "PAPER"
    LIVE = "LIVE"
    SHARED = "SHARED"


class DeliveryState(str, Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    FAILED = "FAILED"
    DEAD_LETTERED = "DEAD_LETTERED"
    QUARANTINED = "QUARANTINED"
    EXPIRED = "EXPIRED"
    DUPLICATE_SUPPRESSED = "DUPLICATE_SUPPRESSED"


class BusHealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    BACKLOGGED = "BACKLOGGED"
    PARTITIONED = "PARTITIONED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    SECURITY_HOLD = "SECURITY_HOLD"


class CompatibilityMode(str, Enum):
    BACKWARD_COMPATIBLE = "backward_compatible"
    FORWARD_COMPATIBLE = "forward_compatible"
    FULLY_COMPATIBLE = "fully_compatible"
    EXACT_VERSION_ONLY = "exact_version_only"


class ReplayStatus(str, Enum):
    ORIGINAL = "ORIGINAL"
    ANALYTICAL_REPLAY = "ANALYTICAL_REPLAY"
    PRODUCTION_REDELIVERY = "PRODUCTION_REDELIVERY"


AUTHORITY_SENSITIVE_KINDS = {
    EnterpriseMessageKind.COMMAND,
    EnterpriseMessageKind.WORKFLOW_HANDOFF,
    EnterpriseMessageKind.MISSION_MESSAGE,
    EnterpriseMessageKind.POLICY_PUBLICATION,
    EnterpriseMessageKind.RECOVERY_MESSAGE,
}

AUTHORITY_SENSITIVE_TYPES = {
    "MISSION_AUTHORIZED",
    "MISSION_AUTHORIZATION_COMMAND",
    "OFFICE_ACTIVATION_COMMAND",
    "WORKFLOW_TOKEN_HANDOFF",
    "COST_APPROVAL",
    "BROKER_ORDER_COMMAND",
    "LEDGER_MUTATION_COMMAND",
    "POLICY_ACTIVATION",
    "LIVE_RECOVERY_COMMAND",
}


@dataclass(frozen=True)
class MessageSchemaRegistration:
    message_type: str
    schema_name: str
    current_version: str
    supported_prior_versions: tuple[str, ...]
    owning_authority: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()
    compatibility_mode: CompatibilityMode = CompatibilityMode.FULLY_COMPATIBLE
    deprecated: bool = False
    activation_date: str = "2026-07-10"
    retirement_date: str = ""


@dataclass(frozen=True)
class MessageSubscription:
    subscription_id: str
    subscriber_service_id: str
    subscriber_office_id: str
    supported_message_types: tuple[str, ...]
    supported_schema_versions: tuple[str, ...]
    routing_filters: dict[str, Any]
    paper_live_modes: tuple[MessageMode, ...]
    delivery_mode: str = "local_in_process"
    maximum_concurrency: int = 1
    ordering_required: bool = False
    acknowledgement_timeout_seconds: int = 30
    max_retries: int = 3
    dead_letter_after_attempts: int = 3
    replay_capability: str = "analytical_only"
    side_effect_classification: str = "read_only"
    idempotent: bool = True
    replay_safe: bool = True
    authority_sensitive: bool = False
    read_only: bool = True
    active: bool = True
    health_state: str = "HEALTHY"
    created_at: str = ""
    policy_version: str = "EO-CL-1.0"


@dataclass(frozen=True)
class EnterpriseMessageEnvelope:
    message_id: str
    message_kind: EnterpriseMessageKind
    message_type: str
    schema_name: str
    schema_version: str
    payload_version: str
    source_service_id: str
    source_office_id: str
    source_authority_type: str
    target_service_id: str
    target_office_id: str
    target_topic: str
    routing_key: str
    created_at: str
    published_at: str
    available_after: str
    expires_at: str
    correlation_id: str
    causation_id: str
    parent_message_id: str
    root_message_id: str
    workflow_id: str
    mission_id: str
    decision_object_id: str
    position_id: str
    order_id: str
    policy_version: str
    paper_live_mode: MessageMode
    priority_class: str
    idempotency_key: str
    partition_key: str
    ordering_key: str
    sequence_number: int
    retry_count: int
    replay_status: ReplayStatus
    replay_source_message_id: str
    security_classification: str
    authorization_context_reference: str
    payload_hash: str
    envelope_hash: str
    trace_metadata: dict[str, Any]
    payload: dict[str, Any]


@dataclass(frozen=True)
class PublishResult:
    accepted: bool
    message_id: str
    status: str
    reason_code: str
    delivery_count: int
    correlation_id: str
    rejection_id: str = ""


@dataclass(frozen=True)
class DeliveryRecord:
    delivery_id: str
    message_id: str
    subscription_id: str
    subscriber_service_id: str
    delivery_state: DeliveryState
    attempt_count: int
    first_attempt_at: str
    last_attempt_at: str
    acknowledged_at: str
    next_retry_at: str
    failure_reason: str
    idempotency_key: str
    replay_mode: bool = False


@dataclass(frozen=True)
class DeadLetterRecord:
    dead_letter_id: str
    message_id: str
    subscription_id: str
    reason_code: str
    failure_reason: str
    attempts: int
    created_at: str
    replay_eligible: bool
    review_status: str = "PENDING_REVIEW"


@dataclass(frozen=True)
class QuarantineRecord:
    quarantine_id: str
    message_id: str
    reason_code: str
    reason: str
    source_service_id: str
    schema_name: str
    paper_live_mode: MessageMode
    created_at: str
    commander_review_state: str = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class MessageAuditRecord:
    audit_id: str
    timestamp: str
    action: str
    message_id: str
    message_type: str
    subscription_id: str
    publisher_id: str
    subscriber_id: str
    correlation_id: str
    causation_id: str
    mission_id: str
    workflow_id: str
    paper_live_mode: str
    attempt_count: int
    prior_state: str
    new_state: str
    reason_code: str
    policy_version: str
    payload_hash: str
    envelope_hash: str


class MessageSchemaRegistry:
    def __init__(self) -> None:
        self._schemas: dict[str, MessageSchemaRegistration] = {}
        self._register_defaults()

    def register(self, registration: MessageSchemaRegistration) -> None:
        self._schemas[registration.message_type] = registration

    def get(self, message_type: str) -> MessageSchemaRegistration | None:
        return self._schemas.get(message_type)

    def validate(self, envelope: EnterpriseMessageEnvelope) -> tuple[bool, str]:
        schema = self.get(envelope.message_type)
        if not schema:
            if envelope.message_kind in AUTHORITY_SENSITIVE_KINDS or envelope.message_type in AUTHORITY_SENSITIVE_TYPES:
                return False, "unknown_schema"
            return True, "dynamic_non_authority_schema"
        if envelope.schema_name != schema.schema_name:
            return False, "schema_name_mismatch"
        if envelope.schema_version != schema.current_version and envelope.schema_version not in schema.supported_prior_versions:
            return False, "unsupported_schema_version"
        missing = tuple(field for field in schema.required_fields if field not in envelope.payload)
        if missing:
            return False, f"payload_missing_required_fields:{','.join(missing)}"
        if schema.deprecated:
            return True, "deprecated_schema_warning"
        return True, "schema_valid"

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in sorted(self._schemas.values(), key=lambda item: item.message_type))

    def _register_defaults(self) -> None:
        defaults = (
            MessageSchemaRegistration("ENTERPRISE_ACTIVITY_EVENT", "EnterpriseActivityEvent", "1.0", (), "Enterprise Activity Bus", ("summary", "severity")),
            MessageSchemaRegistration("POSITION_MONITORING_OBSERVATION", "PositionMonitoringObservation", "1.0", (), "Position Monitoring Network", ("event_type", "position_id")),
            MessageSchemaRegistration("EVENT_DETECTION_VALIDATED", "EventDetectionValidatedEvent", "1.0", (), "Event Detection Engine", ("event_type", "severity")),
            MessageSchemaRegistration("MISSION_AUTHORIZED", "MissionAuthorizedEvent", "1.0", (), "Enterprise Operations Scheduler", ("mission_id", "status")),
            MessageSchemaRegistration("MISSION_MESSAGE", "MissionMessage", "1.0", (), "Enterprise Mission Planner", ("mission_id", "message")),
            MessageSchemaRegistration("WORKFLOW_TOKEN_HANDOFF", "WorkflowHandoff", "1.0", (), "Workflow Runtime Monitor", ("workflow_id", "target_office_id", "token_reference")),
            MessageSchemaRegistration("COST_APPROVAL", "CostApproval", "1.0", (), "Enterprise Cost Governor", ("authorization_id", "amount_usd")),
            MessageSchemaRegistration("BROKER_ORDER_COMMAND", "BrokerOrderCommand", "1.0", (), "Unified Order Execution Engine", ("order_id", "side", "symbol")),
            MessageSchemaRegistration("HEALTH_SIGNAL", "HealthSignal", "1.0", (), "Enterprise Health Monitor", ("component", "state")),
            MessageSchemaRegistration("AUDIT_NOTIFICATION", "AuditNotification", "1.0", (), "Audit Service", ("audit_id", "action")),
            MessageSchemaRegistration("SYSTEM_NOTIFICATION", "SystemNotification", "1.0", (), "Commander Interface", ("summary",)),
        )
        for item in defaults:
            self.register(item)


class EnterpriseCommunicationsBus:
    """Reliable typed local communications fabric; transport only, never authority."""

    def __init__(self) -> None:
        self.schema_registry = MessageSchemaRegistry()
        self._subscriptions: dict[str, MessageSubscription] = {}
        self._messages: dict[str, EnterpriseMessageEnvelope] = {}
        self._outbox: list[DeliveryRecord] = []
        self._inbox_keys: set[tuple[str, str]] = set()
        self._dead_letters: list[DeadLetterRecord] = []
        self._quarantine: list[QuarantineRecord] = []
        self._audit: list[MessageAuditRecord] = []
        self._rejections: list[dict[str, Any]] = []
        self._idempotency_index: dict[str, str] = {}
        self._sequence_state: dict[str, int] = {}
        self._sequence_gaps: list[dict[str, Any]] = []
        self._replay_records: list[dict[str, Any]] = []
        self._metrics = {
            "messagesPublished": 0,
            "messagesDelivered": 0,
            "messagesAcknowledged": 0,
            "messagesRejected": 0,
            "messagesExpired": 0,
            "messagesRetried": 0,
            "messagesDeadLettered": 0,
            "messagesQuarantined": 0,
            "duplicateMessagesSuppressed": 0,
            "schemaValidationFailures": 0,
            "authorizationFailures": 0,
            "paperLiveConflictAttempts": 0,
            "replayRequests": 0,
            "replayFailures": 0,
            "sequenceGaps": 0,
        }
        self._register_default_subscribers()

    def publish(self, envelope: EnterpriseMessageEnvelope) -> PublishResult:
        envelope = self._finalize_envelope(envelope)
        validation = self._validate_envelope(envelope)
        if validation:
            return self._reject(envelope, validation)
        duplicate = self._idempotency_index.get(envelope.idempotency_key)
        if duplicate:
            self._metrics["duplicateMessagesSuppressed"] += 1
            self._audit_event("duplicate_suppressed", envelope, prior_state="NEW", new_state=DeliveryState.DUPLICATE_SUPPRESSED.value, reason_code="duplicate_idempotency_key")
            return PublishResult(True, duplicate, DeliveryState.DUPLICATE_SUPPRESSED.value, "duplicate_idempotency_key", 0, envelope.correlation_id)
        self._messages[envelope.message_id] = envelope
        self._idempotency_index[envelope.idempotency_key] = envelope.message_id
        self._metrics["messagesPublished"] += 1
        self._audit_event("message_published", envelope, new_state="PUBLISHED", reason_code="accepted")
        self._check_sequence(envelope)
        deliveries = self._route(envelope)
        return PublishResult(True, envelope.message_id, "PUBLISHED", "accepted", len(deliveries), envelope.correlation_id)

    def publish_event(self, *, message_type: str, source_service_id: str, payload: dict[str, Any], **kwargs: Any) -> PublishResult:
        return self.publish(self.create_envelope(EnterpriseMessageKind.EVENT, message_type, source_service_id, payload, **kwargs))

    def publish_observation(self, *, message_type: str, source_service_id: str, payload: dict[str, Any], **kwargs: Any) -> PublishResult:
        return self.publish(self.create_envelope(EnterpriseMessageKind.OBSERVATION, message_type, source_service_id, payload, **kwargs))

    def publish_command(self, *, message_type: str, source_service_id: str, target_service_id: str, payload: dict[str, Any], **kwargs: Any) -> PublishResult:
        return self.publish(self.create_envelope(EnterpriseMessageKind.COMMAND, message_type, source_service_id, payload, target_service_id=target_service_id, **kwargs))

    def publish_batch(self, envelopes: tuple[EnterpriseMessageEnvelope, ...]) -> dict[str, Any]:
        results = tuple(self.publish(envelope) for envelope in envelopes)
        return {"accepted": sum(1 for item in results if item.accepted), "rejected": sum(1 for item in results if not item.accepted), "results": tuple(_public(item) for item in results)}

    def create_envelope(
        self,
        message_kind: EnterpriseMessageKind,
        message_type: str,
        source_service_id: str,
        payload: dict[str, Any],
        *,
        schema_name: str = "",
        schema_version: str = "1.0",
        target_service_id: str = "",
        target_office_id: str = "",
        target_topic: str = "",
        routing_key: str = "",
        source_office_id: str = "",
        source_authority_type: str = "enterprise_service",
        correlation_id: str = "",
        causation_id: str = "",
        parent_message_id: str = "",
        root_message_id: str = "",
        workflow_id: str = "",
        mission_id: str = "",
        decision_object_id: str = "",
        position_id: str = "",
        order_id: str = "",
        paper_live_mode: MessageMode | str = MessageMode.PAPER,
        priority_class: str = "normal",
        idempotency_key: str = "",
        partition_key: str = "",
        ordering_key: str = "",
        sequence_number: int = 0,
        security_classification: str = "internal",
        authorization_context_reference: str = "",
        trace_metadata: dict[str, Any] | None = None,
        replay_status: ReplayStatus = ReplayStatus.ORIGINAL,
        replay_source_message_id: str = "",
        expires_at: str = "",
    ) -> EnterpriseMessageEnvelope:
        now = utc_timestamp()
        schema = self.schema_registry.get(message_type)
        message_id = f"ECL-MSG-{uuid4().hex.upper()}"
        correlation = correlation_id or root_message_id or parent_message_id or message_id
        root = root_message_id or parent_message_id or correlation
        mode = paper_live_mode if isinstance(paper_live_mode, MessageMode) else MessageMode(str(paper_live_mode).upper())
        payload_hash = _hash(payload)
        return EnterpriseMessageEnvelope(
            message_id=message_id,
            message_kind=message_kind,
            message_type=message_type,
            schema_name=schema_name or (schema.schema_name if schema else message_type.title().replace("_", "")),
            schema_version=schema_version,
            payload_version=schema_version,
            source_service_id=source_service_id,
            source_office_id=source_office_id,
            source_authority_type=source_authority_type,
            target_service_id=target_service_id,
            target_office_id=target_office_id,
            target_topic=target_topic,
            routing_key=routing_key or target_topic or target_service_id or message_type,
            created_at=now,
            published_at="",
            available_after=now,
            expires_at=expires_at,
            correlation_id=correlation,
            causation_id=causation_id,
            parent_message_id=parent_message_id,
            root_message_id=root,
            workflow_id=workflow_id,
            mission_id=mission_id,
            decision_object_id=decision_object_id,
            position_id=position_id or str(payload.get("position_id", payload.get("positionId", ""))),
            order_id=order_id or str(payload.get("order_id", payload.get("orderId", ""))),
            policy_version="EO-CL-1.0",
            paper_live_mode=mode,
            priority_class=priority_class,
            idempotency_key=idempotency_key or _hash({"source": source_service_id, "type": message_type, "payload": payload, "correlation": correlation}),
            partition_key=partition_key or mode.value,
            ordering_key=ordering_key,
            sequence_number=sequence_number,
            retry_count=0,
            replay_status=replay_status,
            replay_source_message_id=replay_source_message_id,
            security_classification=security_classification,
            authorization_context_reference=authorization_context_reference,
            payload_hash=payload_hash,
            envelope_hash="",
            trace_metadata=dict(trace_metadata or {}),
            payload=dict(payload),
        )

    def register_subscriber(self, subscription: MessageSubscription) -> dict[str, Any]:
        if not subscription.subscriber_service_id:
            raise ValueError("subscriber_service_id is required")
        if not subscription.supported_message_types:
            raise ValueError("supported_message_types is required")
        created = subscription.created_at or utc_timestamp()
        subscription = replace(subscription, created_at=created)
        self._subscriptions[subscription.subscription_id] = subscription
        self._audit.append(
            MessageAuditRecord(
                f"ECL-AUD-{len(self._audit) + 1:06d}",
                utc_timestamp(),
                "subscriber_registered",
                "",
                "",
                subscription.subscription_id,
                "",
                subscription.subscriber_service_id,
                "",
                "",
                "",
                "",
                "",
                0,
                "",
                "REGISTERED",
                "subscriber_registered",
                subscription.policy_version,
                "",
                "",
            )
        )
        return {"accepted": True, "subscriptionId": subscription.subscription_id, "subscriber": subscription.subscriber_service_id}

    def unregister_subscriber(self, subscription_id: str) -> None:
        if subscription_id in self._subscriptions:
            self._subscriptions[subscription_id] = replace(self._subscriptions[subscription_id], active=False, health_state="UNAVAILABLE")

    def acknowledge(self, message_id: str, subscription_id: str, acknowledgement: dict[str, Any] | None = None) -> dict[str, Any]:
        for index, delivery in enumerate(self._outbox):
            if delivery.message_id == message_id and delivery.subscription_id == subscription_id:
                updated = replace(delivery, delivery_state=DeliveryState.ACKNOWLEDGED, acknowledged_at=utc_timestamp(), failure_reason="")
                self._outbox[index] = updated
                self._metrics["messagesAcknowledged"] += 1
                self._audit_event("delivery_acknowledged", self._messages[message_id], subscription_id=subscription_id, subscriber_id=delivery.subscriber_service_id, prior_state=delivery.delivery_state.value, new_state=DeliveryState.ACKNOWLEDGED.value, reason_code=str((acknowledgement or {}).get("reason", "acknowledged")), attempt_count=updated.attempt_count)
                return {"acknowledged": True, "delivery": _public(updated)}
        return {"acknowledged": False, "reasonCode": "delivery_not_found"}

    def reject(self, message_id: str, subscription_id: str, reason: str) -> dict[str, Any]:
        for index, delivery in enumerate(self._outbox):
            if delivery.message_id == message_id and delivery.subscription_id == subscription_id:
                updated = replace(delivery, delivery_state=DeliveryState.FAILED, failure_reason=reason, last_attempt_at=utc_timestamp())
                self._outbox[index] = updated
                self._dead_letter(updated, reason, replay_eligible=self._subscriptions.get(subscription_id, MessageSubscription("", "", "", (), (), {}, ())).replay_safe)
                return {"rejected": True, "delivery": _public(updated)}
        return {"rejected": False, "reasonCode": "delivery_not_found"}

    def retry_dead_letter(self, dead_letter_id: str, authorization: dict[str, Any] | None = None) -> dict[str, Any]:
        record = next((item for item in self._dead_letters if item.dead_letter_id == dead_letter_id), None)
        if not record:
            return {"retried": False, "reasonCode": "dead_letter_not_found"}
        envelope = self._messages.get(record.message_id)
        if not envelope:
            return {"retried": False, "reasonCode": "message_not_found"}
        if envelope.message_type in AUTHORITY_SENSITIVE_TYPES and not (authorization or {}).get("commanderAuthorized"):
            self._metrics["replayFailures"] += 1
            self._audit_event("replay_rejected", envelope, subscription_id=record.subscription_id, new_state="REJECTED", reason_code="replay_authorization_missing")
            return {"retried": False, "reasonCode": "replay_authorization_missing"}
        delivery = DeliveryRecord(
            f"ECL-DEL-{len(self._outbox) + 1:06d}",
            envelope.message_id,
            record.subscription_id,
            self._subscriptions.get(record.subscription_id, MessageSubscription("", "", "", (), (), {}, ())).subscriber_service_id,
            DeliveryState.RETRY_SCHEDULED,
            record.attempts + 1,
            utc_timestamp(),
            utc_timestamp(),
            "",
            utc_timestamp(),
            "",
            envelope.idempotency_key,
        )
        self._outbox.append(delivery)
        self._metrics["messagesRetried"] += 1
        self._audit_event("retry_scheduled", envelope, subscription_id=record.subscription_id, subscriber_id=delivery.subscriber_service_id, new_state=DeliveryState.RETRY_SCHEDULED.value, reason_code="commander_retry", attempt_count=delivery.attempt_count)
        return {"retried": True, "delivery": _public(delivery)}

    def request_replay(self, message_id: str, *, analytical: bool = True, authorization: dict[str, Any] | None = None) -> dict[str, Any]:
        self._metrics["replayRequests"] += 1
        source = self._messages.get(message_id)
        if not source:
            self._metrics["replayFailures"] += 1
            return {"accepted": False, "reasonCode": "message_not_found"}
        if not analytical and source.message_type in AUTHORITY_SENSITIVE_TYPES and not (authorization or {}).get("commanderAuthorized"):
            self._metrics["replayFailures"] += 1
            self._audit_event("replay_rejected", source, new_state="REJECTED", reason_code="replay_authorization_missing")
            return {"accepted": False, "reasonCode": "replay_authorization_missing"}
        replay = self.create_envelope(
            source.message_kind,
            source.message_type,
            source.source_service_id,
            source.payload,
            schema_name=source.schema_name,
            schema_version=source.schema_version,
            target_service_id=source.target_service_id,
            target_office_id=source.target_office_id,
            target_topic=source.target_topic,
            routing_key=source.routing_key,
            source_office_id=source.source_office_id,
            source_authority_type=source.source_authority_type,
            correlation_id=source.correlation_id,
            causation_id=source.message_id,
            parent_message_id=source.message_id,
            root_message_id=source.root_message_id,
            workflow_id=source.workflow_id,
            mission_id=source.mission_id,
            decision_object_id=source.decision_object_id,
            position_id=source.position_id,
            order_id=source.order_id,
            paper_live_mode=source.paper_live_mode,
            priority_class=source.priority_class,
            idempotency_key=f"REPLAY-{source.message_id}-{len(self._replay_records) + 1}",
            partition_key=source.partition_key,
            ordering_key=source.ordering_key,
            sequence_number=0,
            security_classification=source.security_classification,
            authorization_context_reference=source.authorization_context_reference,
            trace_metadata={**source.trace_metadata, "analyticalReplay": analytical},
            replay_status=ReplayStatus.ANALYTICAL_REPLAY if analytical else ReplayStatus.PRODUCTION_REDELIVERY,
            replay_source_message_id=source.message_id,
        )
        result = self.publish(replay)
        self._replay_records.append({"replayId": f"ECL-REPLAY-{len(self._replay_records) + 1:06d}", "sourceMessageId": source.message_id, "replayMessageId": replay.message_id, "analytical": analytical, "accepted": result.accepted})
        return {"accepted": result.accepted, "replayMessageId": replay.message_id, "productionMutation": False if analytical else "authorized_path_required"}

    def get_message(self, message_id: str) -> dict[str, Any]:
        return _public(self._messages[message_id]) if message_id in self._messages else {}

    def get_delivery_state(self, message_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._outbox if item.message_id == message_id)

    def get_correlation_trace(self, correlation_id: str) -> dict[str, Any]:
        message_snapshot = tuple(self._messages.values())
        messages = tuple(item for item in message_snapshot if item.correlation_id == correlation_id or item.root_message_id == correlation_id)
        nodes = tuple(_trace_node(item, self.get_delivery_state(item.message_id)) for item in sorted(messages, key=lambda item: item.published_at or item.created_at))
        return {"correlationId": correlation_id, "messageCount": len(nodes), "nodes": nodes}

    def get_dead_letters(self, filters: dict[str, Any] | None = None) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._dead_letters if _record_matches(_public(item), filters or {}))

    def get_quarantine(self, filters: dict[str, Any] | None = None) -> tuple[dict[str, Any], ...]:
        return tuple(_public(item) for item in self._quarantine if _record_matches(_public(item), filters or {}))

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._messages = {item["message_id"]: _envelope_from_public(item) for item in snapshot.get("messageStream", ())}
        self._outbox = [_delivery_from_public(item) for item in snapshot.get("outbox", ())]
        self._dead_letters = [_dead_letter_from_public(item) for item in snapshot.get("deadLetters", ())]
        self._quarantine = [_quarantine_from_public(item) for item in snapshot.get("quarantine", ())]
        self._audit = [_audit_from_public(item) for item in snapshot.get("auditTrail", ())]
        self._idempotency_index = {item.idempotency_key: item.message_id for item in self._messages.values()}
        self._inbox_keys = {(item.subscription_id, item.idempotency_key) for item in self._outbox}
        self._audit.append(MessageAuditRecord(f"ECL-AUD-{len(self._audit) + 1:06d}", utc_timestamp(), "startup_recovery", "", "", "", "", "", "", "", "", "", "", 0, "", "RECOVERED", "snapshot_recovered", "EO-CL-1.0", "", ""))

    def snapshot(self) -> dict[str, Any]:
        metrics = dict(self._metrics)
        message_snapshot = tuple(self._messages.values())
        outbox_snapshot = tuple(self._outbox)
        dead_letter_snapshot = tuple(self._dead_letters)
        quarantine_snapshot = tuple(self._quarantine)
        audit_snapshot = tuple(self._audit)
        pending = [item for item in outbox_snapshot if item.delivery_state in {DeliveryState.PENDING, DeliveryState.RETRY_SCHEDULED, DeliveryState.DELIVERED}]
        acknowledged = [item for item in outbox_snapshot if item.delivery_state == DeliveryState.ACKNOWLEDGED]
        delivered_total = len(outbox_snapshot)
        health_state = self._health_state(pending)
        success = 100.0 if delivered_total == 0 else round((len(acknowledged) / delivered_total) * 100, 2)
        return {
            "busName": "Enterprise Communications Bus",
            "engineeringOrder": "EO-CL",
            "health": health_state.value,
            "summary": {
                "messagesPublished": len(message_snapshot),
                "messagesPublishedPerMinute": len(message_snapshot),
                "deliverySuccessRate": success,
                "currentOutboxDepth": len(pending),
                "retryBacklog": sum(1 for item in outbox_snapshot if item.delivery_state == DeliveryState.RETRY_SCHEDULED),
                "deadLetterCount": len(dead_letter_snapshot),
                "quarantineCount": len(quarantine_snapshot),
                "oldestUndeliveredMessage": min((item.first_attempt_at for item in pending), default=""),
                "liveLaneLatencyMs": 0,
                "paperLaneLatencyMs": 0,
                "activeSubscribers": sum(1 for item in self._subscriptions.values() if item.active),
                "unavailableSubscribers": sum(1 for item in self._subscriptions.values() if not item.active or item.health_state != "HEALTHY"),
                "schemaCompatibilityWarnings": sum(1 for item in self.schema_registry.snapshot() if item.get("deprecated")),
                "sequenceGapWarnings": len(self._sequence_gaps),
            },
            "messageStream": tuple(_public(item) for item in sorted(message_snapshot, key=lambda item: item.published_at or item.created_at, reverse=True)[:80]),
            "outbox": tuple(_public(item) for item in reversed(outbox_snapshot[-80:])),
            "deadLetters": tuple(_public(item) for item in reversed(dead_letter_snapshot[-40:])),
            "quarantine": tuple(_public(item) for item in reversed(quarantine_snapshot[-40:])),
            "subscriberHealth": tuple(self._subscriber_health(item) for item in sorted(self._subscriptions.values(), key=lambda item: item.subscription_id)),
            "schemaRegistry": self.schema_registry.snapshot(),
            "correlationIndex": tuple({"correlationId": key, "messageCount": len([item for item in message_snapshot if item.correlation_id == key or item.root_message_id == key])} for key in sorted({item.correlation_id for item in message_snapshot})[:20]),
            "sequenceGaps": tuple(self._sequence_gaps[-20:]),
            "replayRecords": tuple(self._replay_records[-20:]),
            "rejections": tuple(self._rejections[-30:]),
            "auditTrail": tuple(_public(item) for item in reversed(self._audit[-80:])),
            "metrics": {
                **metrics,
                "outboxDepth": len(pending),
                "inboxProcessingDepth": len(self._inbox_keys),
                "retryBacklog": sum(1 for item in outbox_snapshot if item.delivery_state == DeliveryState.RETRY_SCHEDULED),
                "oldestPendingMessage": min((item.first_attempt_at for item in pending), default=""),
                "subscriberAvailability": self._subscriber_availability(),
                "liveLaneServiceLevel": "PROTECTED",
                "paperLaneServiceLevel": "THROTTLED_WHEN_NEEDED",
                "transportStorageGrowth": len(message_snapshot) + len(outbox_snapshot) + len(audit_snapshot),
            },
            "healthDimensions": {
                "publishAvailability": "AVAILABLE",
                "persistenceHealth": "IN_MEMORY_DURABLE_WITH_RUNTIME_SNAPSHOT",
                "deliveryHealth": health_state.value,
                "subscriberHealth": "NOMINAL" if not any(item.health_state != "HEALTHY" for item in self._subscriptions.values()) else "DEGRADED",
                "schemaCompatibility": "NOMINAL" if not self._metrics["schemaValidationFailures"] else "ATTENTION",
                "replayHealth": "NOMINAL" if not self._metrics["replayFailures"] else "ATTENTION",
            },
            "lawCL": {
                "authorizesMissions": False,
                "wakesOffices": False,
                "transfersWorkflowExecutionToken": False,
                "executesBusinessLogic": False,
                "placesTrades": False,
                "mutatesLedgers": False,
                "assignsEnterprisePriority": False,
                "spendsBudget": False,
                "routineAiInvocations": 0,
                "deterministicRouting": True,
                "paperLiveIsolation": True,
            },
        }

    def _route(self, envelope: EnterpriseMessageEnvelope) -> tuple[DeliveryRecord, ...]:
        matched = [item for item in self._subscriptions.values() if _subscription_matches(envelope, item)]
        if not matched:
            self._audit_event("message_routed_no_subscriber", envelope, new_state="PERSISTED", reason_code="no_matching_subscriber")
            return ()
        deliveries = []
        for subscription in matched:
            key = (subscription.subscription_id, envelope.idempotency_key)
            if key in self._inbox_keys:
                self._metrics["duplicateMessagesSuppressed"] += 1
                continue
            self._inbox_keys.add(key)
            delivery = DeliveryRecord(
                f"ECL-DEL-{len(self._outbox) + 1:06d}",
                envelope.message_id,
                subscription.subscription_id,
                subscription.subscriber_service_id,
                DeliveryState.PENDING,
                0,
                utc_timestamp(),
                "",
                "",
                "",
                "",
                envelope.idempotency_key,
            )
            self._outbox.append(delivery)
            self._audit_event("message_routed", envelope, subscription_id=subscription.subscription_id, subscriber_id=subscription.subscriber_service_id, new_state=DeliveryState.PENDING.value, reason_code="matched_subscription")
            deliveries.append(self._attempt_delivery(delivery, subscription, envelope))
        return tuple(deliveries)

    def _attempt_delivery(self, delivery: DeliveryRecord, subscription: MessageSubscription, envelope: EnterpriseMessageEnvelope) -> DeliveryRecord:
        index = self._outbox.index(delivery)
        if not subscription.active or subscription.health_state == "UNAVAILABLE":
            updated = replace(delivery, delivery_state=DeliveryState.RETRY_SCHEDULED, attempt_count=delivery.attempt_count + 1, last_attempt_at=utc_timestamp(), next_retry_at=utc_timestamp(), failure_reason="subscriber_unavailable")
            self._outbox[index] = updated
            self._audit_event("retry_scheduled", envelope, subscription_id=subscription.subscription_id, subscriber_id=subscription.subscriber_service_id, new_state=DeliveryState.RETRY_SCHEDULED.value, reason_code="subscriber_unavailable", attempt_count=updated.attempt_count)
            return updated
        behavior = str(subscription.routing_filters.get("testBehavior", "ack"))
        if behavior == "terminal_fail":
            updated = replace(delivery, delivery_state=DeliveryState.FAILED, attempt_count=subscription.dead_letter_after_attempts, last_attempt_at=utc_timestamp(), failure_reason="terminal_test_failure")
            self._outbox[index] = updated
            self._dead_letter(updated, "terminal_test_failure", replay_eligible=subscription.replay_safe)
            return updated
        if behavior == "transient_fail":
            attempts = delivery.attempt_count + 1
            state = DeliveryState.DEAD_LETTERED if attempts >= subscription.dead_letter_after_attempts else DeliveryState.RETRY_SCHEDULED
            updated = replace(delivery, delivery_state=state, attempt_count=attempts, last_attempt_at=utc_timestamp(), next_retry_at=utc_timestamp(), failure_reason="transient_test_failure")
            self._outbox[index] = updated
            if state == DeliveryState.DEAD_LETTERED:
                self._dead_letter(updated, "retry_exhausted", replay_eligible=subscription.replay_safe)
            else:
                self._metrics["messagesRetried"] += 1
                self._audit_event("retry_scheduled", envelope, subscription_id=subscription.subscription_id, subscriber_id=subscription.subscriber_service_id, new_state=state.value, reason_code="transient_failure", attempt_count=attempts)
            return updated
        delivered = replace(delivery, delivery_state=DeliveryState.DELIVERED, attempt_count=delivery.attempt_count + 1, last_attempt_at=utc_timestamp())
        self._outbox[index] = delivered
        self._metrics["messagesDelivered"] += 1
        self._audit_event("delivery_attempted", envelope, subscription_id=subscription.subscription_id, subscriber_id=subscription.subscriber_service_id, new_state=DeliveryState.DELIVERED.value, reason_code="delivered", attempt_count=delivered.attempt_count)
        if str(subscription.routing_filters.get("autoAck", True)).lower() != "false":
            self.acknowledge(envelope.message_id, subscription.subscription_id, {"reason": "auto_acknowledged"})
            return self._outbox[index]
        return delivered

    def _dead_letter(self, delivery: DeliveryRecord, reason: str, *, replay_eligible: bool) -> None:
        record = DeadLetterRecord(f"ECL-DLQ-{len(self._dead_letters) + 1:06d}", delivery.message_id, delivery.subscription_id, "retry_exhausted", reason, delivery.attempt_count, utc_timestamp(), replay_eligible)
        self._dead_letters.append(record)
        self._metrics["messagesDeadLettered"] += 1
        envelope = self._messages.get(delivery.message_id)
        if envelope:
            self._audit_event("message_dead_lettered", envelope, subscription_id=delivery.subscription_id, subscriber_id=delivery.subscriber_service_id, new_state=DeliveryState.DEAD_LETTERED.value, reason_code=reason, attempt_count=delivery.attempt_count)

    def _reject(self, envelope: EnterpriseMessageEnvelope, reason_code: str) -> PublishResult:
        sensitive = envelope.message_kind in AUTHORITY_SENSITIVE_KINDS or envelope.message_type in AUTHORITY_SENSITIVE_TYPES
        self._metrics["messagesRejected"] += 1
        if reason_code in {"unauthorized_publisher", "source_spoofing_rejected", "authorization_metadata_required"}:
            self._metrics["authorizationFailures"] += 1
        if reason_code == "paper_live_mode_conflict":
            self._metrics["paperLiveConflictAttempts"] += 1
        if "schema" in reason_code or "payload" in reason_code:
            self._metrics["schemaValidationFailures"] += 1
        rejection = {"rejectionId": f"ECL-REJ-{len(self._rejections) + 1:06d}", "messageId": envelope.message_id, "reasonCode": reason_code, "authoritySensitive": sensitive, "timestamp": utc_timestamp()}
        self._rejections.append(rejection)
        if sensitive or reason_code in {"paper_live_mode_conflict", "payload_hash_mismatch", "envelope_hash_mismatch", "security_classification_conflict"}:
            quarantine = QuarantineRecord(f"ECL-QUAR-{len(self._quarantine) + 1:06d}", envelope.message_id, reason_code, reason_code, envelope.source_service_id, envelope.schema_name, envelope.paper_live_mode, utc_timestamp())
            self._quarantine.append(quarantine)
            self._metrics["messagesQuarantined"] += 1
        self._audit_event("message_rejected", envelope, new_state="REJECTED", reason_code=reason_code)
        return PublishResult(False, envelope.message_id, "REJECTED", reason_code, 0, envelope.correlation_id, rejection["rejectionId"])

    def _validate_envelope(self, envelope: EnterpriseMessageEnvelope) -> str:
        required = ("message_id", "message_type", "source_service_id", "correlation_id", "idempotency_key", "payload_hash")
        for field in required:
            if not getattr(envelope, field):
                return f"missing_{field}"
        if envelope.message_kind == EnterpriseMessageKind.COMMAND and not envelope.target_service_id:
            return "target_required_for_command"
        if envelope.message_kind == EnterpriseMessageKind.QUERY_RESPONSE and not envelope.parent_message_id:
            return "query_response_missing_parent"
        if envelope.message_kind == EnterpriseMessageKind.WORKFLOW_HANDOFF:
            if not envelope.target_office_id or not envelope.workflow_id:
                return "workflow_execution_token_metadata_invalid"
            if not envelope.authorization_context_reference:
                return "authorization_metadata_required"
        if envelope.message_type == "COST_APPROVAL" and envelope.source_service_id != "Enterprise Cost Governor":
            return "unauthorized_publisher"
        if envelope.message_type == "MISSION_AUTHORIZED" and envelope.source_service_id != "Enterprise Operations Scheduler":
            return "unauthorized_publisher"
        if envelope.message_type == "BROKER_ORDER_COMMAND" and envelope.paper_live_mode == MessageMode.PAPER and "LIVE" in envelope.target_service_id.upper():
            return "paper_live_mode_conflict"
        if envelope.payload_hash != _hash(envelope.payload):
            return "payload_hash_mismatch"
        schema_ok, schema_reason = self.schema_registry.validate(envelope)
        if not schema_ok:
            return schema_reason
        if envelope.expires_at and envelope.expires_at < utc_timestamp():
            self._metrics["messagesExpired"] += 1
            return "message_expired"
        if len(json.dumps(envelope.payload, default=str)) > 20000:
            return "payload_too_large"
        return ""

    def _finalize_envelope(self, envelope: EnterpriseMessageEnvelope) -> EnterpriseMessageEnvelope:
        published = envelope.published_at or utc_timestamp()
        no_hash = replace(envelope, published_at=published, envelope_hash="")
        return replace(no_hash, envelope_hash=_hash(_public(no_hash)))

    def _check_sequence(self, envelope: EnterpriseMessageEnvelope) -> None:
        if not envelope.ordering_key or envelope.sequence_number <= 0:
            return
        expected = self._sequence_state.get(envelope.ordering_key, 0) + 1
        if envelope.sequence_number != expected:
            gap = {"orderingKey": envelope.ordering_key, "expected": expected, "observed": envelope.sequence_number, "messageId": envelope.message_id, "timestamp": utc_timestamp()}
            self._sequence_gaps.append(gap)
            self._metrics["sequenceGaps"] += 1
            self._audit_event("sequence_gap_detected", envelope, new_state="DEGRADED", reason_code="sequence_gap_detected")
        self._sequence_state[envelope.ordering_key] = max(self._sequence_state.get(envelope.ordering_key, 0), envelope.sequence_number)

    def _subscriber_health(self, subscription: MessageSubscription) -> dict[str, Any]:
        deliveries = [item for item in self._outbox if item.subscription_id == subscription.subscription_id]
        failures = [item for item in deliveries if item.delivery_state in {DeliveryState.FAILED, DeliveryState.DEAD_LETTERED, DeliveryState.RETRY_SCHEDULED}]
        return {
            "subscriptionId": subscription.subscription_id,
            "subscriber": subscription.subscriber_service_id,
            "supportedMessageTypes": subscription.supported_message_types,
            "availability": "AVAILABLE" if subscription.active and subscription.health_state == "HEALTHY" else "UNAVAILABLE",
            "latencyMs": 0,
            "errorRate": 0 if not deliveries else round((len(failures) / len(deliveries)) * 100, 2),
            "queueDepth": sum(1 for item in deliveries if item.delivery_state in {DeliveryState.PENDING, DeliveryState.RETRY_SCHEDULED}),
            "lastAcknowledgement": max((item.acknowledged_at for item in deliveries if item.acknowledged_at), default=""),
            "schemaCompatibility": "COMPATIBLE",
            "sideEffectClassification": subscription.side_effect_classification,
            "replayCapability": subscription.replay_capability,
        }

    def _subscriber_availability(self) -> str:
        if not self._subscriptions:
            return "NO_SUBSCRIBERS"
        unavailable = sum(1 for item in self._subscriptions.values() if not item.active or item.health_state != "HEALTHY")
        return f"{len(self._subscriptions) - unavailable}/{len(self._subscriptions)}"

    def _health_state(self, pending: list[DeliveryRecord]) -> BusHealthState:
        if self._quarantine:
            return BusHealthState.SECURITY_HOLD
        if self._dead_letters:
            return BusHealthState.DEGRADED
        if len(pending) > 25:
            return BusHealthState.BACKLOGGED
        if self._sequence_gaps:
            return BusHealthState.DEGRADED
        return BusHealthState.HEALTHY

    def _audit_event(
        self,
        action: str,
        envelope: EnterpriseMessageEnvelope,
        *,
        subscription_id: str = "",
        subscriber_id: str = "",
        prior_state: str = "",
        new_state: str = "",
        reason_code: str = "",
        attempt_count: int = 0,
    ) -> None:
        self._audit.append(
            MessageAuditRecord(
                f"ECL-AUD-{len(self._audit) + 1:06d}",
                utc_timestamp(),
                action,
                envelope.message_id,
                envelope.message_type,
                subscription_id,
                envelope.source_service_id,
                subscriber_id,
                envelope.correlation_id,
                envelope.causation_id,
                envelope.mission_id,
                envelope.workflow_id,
                envelope.paper_live_mode.value,
                attempt_count,
                prior_state,
                new_state,
                reason_code,
                envelope.policy_version,
                envelope.payload_hash,
                envelope.envelope_hash,
            )
        )

    def _register_default_subscribers(self) -> None:
        defaults = (
            MessageSubscription("ECL-SUB-COMMANDER", "Commander Interface", "Commander", ("*",), ("1.0",), {"autoAck": True}, (MessageMode.PAPER, MessageMode.LIVE, MessageMode.SHARED), side_effect_classification="read_only"),
            MessageSubscription("ECL-SUB-HISTORIAN", "Historian", "Historian", ("ENTERPRISE_ACTIVITY_EVENT", "MISSION_AUTHORIZED", "EVENT_DETECTION_VALIDATED"), ("1.0",), {"autoAck": True}, (MessageMode.PAPER, MessageMode.LIVE, MessageMode.SHARED), side_effect_classification="read_only"),
            MessageSubscription("ECL-SUB-EO-CC", "Event Detection Engine", "Infrastructure", ("POSITION_MONITORING_OBSERVATION",), ("1.0",), {"autoAck": True}, (MessageMode.PAPER, MessageMode.LIVE), side_effect_classification="read_only"),
            MessageSubscription("ECL-SUB-EO-CA", "Enterprise Operations Scheduler", "Executive", ("MISSION_MESSAGE", "MISSION_AUTHORIZED"), ("1.0",), {"autoAck": True}, (MessageMode.PAPER, MessageMode.LIVE, MessageMode.SHARED), authority_sensitive=True, side_effect_classification="authority_validates"),
            MessageSubscription("ECL-SUB-WORKFLOW", "Workflow Runtime Monitor", "Infrastructure", ("WORKFLOW_TOKEN_HANDOFF",), ("1.0",), {"autoAck": True}, (MessageMode.PAPER, MessageMode.LIVE, MessageMode.SHARED), authority_sensitive=True, side_effect_classification="validates_law_vii"),
        )
        for item in defaults:
            self.register_subscriber(item)


def _subscription_matches(envelope: EnterpriseMessageEnvelope, subscription: MessageSubscription) -> bool:
    if not subscription.active and subscription.health_state != "UNAVAILABLE":
        return False
    if envelope.paper_live_mode not in subscription.paper_live_modes and MessageMode.SHARED not in subscription.paper_live_modes:
        return False
    types = subscription.supported_message_types
    if "*" not in types and envelope.message_type not in types:
        return False
    versions = subscription.supported_schema_versions
    if "*" not in versions and envelope.schema_version not in versions:
        return False
    filters = subscription.routing_filters
    if filters.get("targetServiceId") and filters["targetServiceId"] != envelope.target_service_id:
        return False
    if filters.get("topic") and filters["topic"] != envelope.target_topic:
        return False
    return True


def _trace_node(envelope: EnterpriseMessageEnvelope, deliveries: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return {
        "messageId": envelope.message_id,
        "messageType": envelope.message_type,
        "kind": envelope.message_kind.value,
        "source": envelope.source_service_id,
        "target": envelope.target_service_id or envelope.target_topic,
        "causationId": envelope.causation_id,
        "parentMessageId": envelope.parent_message_id,
        "rootMessageId": envelope.root_message_id,
        "workflowId": envelope.workflow_id,
        "missionId": envelope.mission_id,
        "deliveryStates": tuple(item.get("delivery_state", "") for item in deliveries),
    }


def _record_matches(record: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key, value in filters.items():
        if str(record.get(key, "")).lower() != str(value).lower():
            return False
    return True


def _hash(value: Any) -> str:
    return sha256(json.dumps(_json_value(value), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _public(item: Any) -> dict[str, Any]:
    raw = asdict(item) if hasattr(item, "__dataclass_fields__") else item
    return _json_value(raw)


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return tuple(_json_value(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_value(item) for item in value)
    if isinstance(value, dict):
        return {str(_json_value(key)): _json_value(item) for key, item in value.items()}
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _envelope_from_public(item: dict[str, Any]) -> EnterpriseMessageEnvelope:
    data = dict(item)
    data["message_kind"] = EnterpriseMessageKind(data["message_kind"])
    data["paper_live_mode"] = MessageMode(data["paper_live_mode"])
    data["replay_status"] = ReplayStatus(data["replay_status"])
    return EnterpriseMessageEnvelope(**{key: data.get(key) for key in EnterpriseMessageEnvelope.__dataclass_fields__})


def _delivery_from_public(item: dict[str, Any]) -> DeliveryRecord:
    data = dict(item)
    data["delivery_state"] = DeliveryState(data["delivery_state"])
    return DeliveryRecord(**{key: data.get(key) for key in DeliveryRecord.__dataclass_fields__})


def _dead_letter_from_public(item: dict[str, Any]) -> DeadLetterRecord:
    return DeadLetterRecord(**{key: item.get(key) for key in DeadLetterRecord.__dataclass_fields__})


def _quarantine_from_public(item: dict[str, Any]) -> QuarantineRecord:
    data = dict(item)
    data["paper_live_mode"] = MessageMode(data["paper_live_mode"])
    return QuarantineRecord(**{key: data.get(key) for key in QuarantineRecord.__dataclass_fields__})


def _audit_from_public(item: dict[str, Any]) -> MessageAuditRecord:
    return MessageAuditRecord(**{key: item.get(key) for key in MessageAuditRecord.__dataclass_fields__})
