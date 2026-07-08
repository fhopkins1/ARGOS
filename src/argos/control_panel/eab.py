"""Enterprise Activity Bus for deterministic control-panel events."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.contracts import OperationalContract, ValidationStatus, utc_timestamp
from argos.foundation.identity import generate_case_file_id, generate_document_id, generate_trade_cycle_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType


ORGANIZATIONS = {
    "Executive",
    "Seeker",
    "Analyst",
    "Risk",
    "Trader",
    "Historian",
    "Librarian",
    "Academy",
    "Infrastructure",
    "Commander Interface",
}

SEVERITIES = {"INFO", "NOTICE", "WARNING", "CRITICAL", "EMERGENCY"}

SUBSCRIPTIONS: dict[str, dict[str, tuple[str, ...]]] = {
    "Commander": {"organizations": ("*",), "severities": ("*",), "categories": ("*",)},
    "Historian": {"organizations": ("*",), "severities": ("*",), "categories": ("*",)},
    "Executive": {"organizations": ("*",), "severities": ("CRITICAL", "EMERGENCY"), "categories": ("*",)},
    "Trader": {"organizations": ("Trader", "Executive", "Risk"), "severities": ("*",), "categories": ("EXECUTION", "COMMAND", "TRADING")},
    "Academy": {"organizations": ("Academy", "Historian", "Librarian"), "severities": ("*",), "categories": ("KNOWLEDGE", "EDUCATION")},
    "Alert Center": {"organizations": ("*",), "severities": ("WARNING", "CRITICAL", "EMERGENCY"), "categories": ("*",)},
}


@dataclass(frozen=True)
class EnterpriseEvent:
    """Canonical normalized enterprise event."""

    event_id: str
    sequence: int
    timestamp_utc: str
    organization: str
    office: str
    workflow: str
    task_identifier: str
    event_category: str
    severity: str
    summary: str
    detailed_description: str
    supporting_evidence: tuple[str, ...]
    correlation_identifier: str
    audit_identifier: str
    asset: str
    portfolio: str
    case_file_id: str
    status: str


@dataclass(frozen=True)
class EventDelivery:
    """Deterministic subscription delivery record."""

    delivery_id: str
    event_id: str
    subscriber: str
    status: str
    timestamp_utc: str


class EnterpriseActivityBus:
    """Append-only event bus for local ARGOS operational activity."""

    def __init__(self, audit_service: AuditService, persistence_repository: InMemoryPersistenceRepository) -> None:
        self.audit_service = audit_service
        self.persistence_repository = persistence_repository
        self._events: list[EnterpriseEvent] = []
        self._deliveries: list[EventDelivery] = []
        self._event_signatures: set[str] = set()
        self._duplicate_events = 0
        self._unauthorized_events = 0
        self._broken_correlations = 0

    def publish(
        self,
        *,
        organization: str,
        office: str,
        workflow: str,
        task_identifier: str,
        event_category: str,
        severity: str,
        summary: str,
        detailed_description: str,
        supporting_evidence: tuple[str, ...] = (),
        correlation_identifier: str = "",
        audit_identifier: str = "",
        asset: str = "",
        portfolio: str = "",
        case_file_id: str = "",
        status: str = "RECORDED",
    ) -> EnterpriseEvent:
        """Normalize, archive, audit, and distribute one enterprise event."""
        normalized_severity = severity.upper()
        if organization not in ORGANIZATIONS:
            self._unauthorized_events += 1
            raise ValueError(f"unauthorized event organization: {organization}")
        if normalized_severity not in SEVERITIES:
            raise ValueError(f"unsupported event severity: {severity}")
        if not correlation_identifier:
            self._broken_correlations += 1
            correlation_identifier = f"CORR-{len(self._events) + 1:06d}"
        if not case_file_id:
            case_file_id = generate_case_file_id(9900 + len(self._events) + 1)

        sequence = len(self._events) + 1
        event = EnterpriseEvent(
            event_id=f"EAB-{sequence:06d}",
            sequence=sequence,
            timestamp_utc=utc_timestamp(),
            organization=organization,
            office=office,
            workflow=workflow,
            task_identifier=task_identifier,
            event_category=event_category.upper(),
            severity=normalized_severity,
            summary=summary,
            detailed_description=detailed_description,
            supporting_evidence=tuple(supporting_evidence),
            correlation_identifier=correlation_identifier,
            audit_identifier=audit_identifier,
            asset=asset,
            portfolio=portfolio,
            case_file_id=case_file_id,
            status=status.upper(),
        )
        signature = _event_signature(event)
        if signature in self._event_signatures:
            self._duplicate_events += 1
        self._event_signatures.add(signature)

        contract = _event_contract(sequence, event)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        audit = self.audit_service.record_document_creation(contract)
        event = EnterpriseEvent(**{**asdict(event), "audit_identifier": audit.event_id})
        self._events.append(event)
        self._deliver(event)
        return event

    def snapshot(self, filters: dict[str, str] | None = None) -> dict[str, Any]:
        """Return EAB state, optionally filtered for Commander display."""
        events = self.search(filters or {})
        return {
            "events": tuple(asdict(event) for event in reversed(events[-50:])),
            "feed": tuple(_feed_item(event) for event in reversed(events[-12:])),
            "subscriptions": SUBSCRIPTIONS,
            "deliveries": tuple(asdict(delivery) for delivery in reversed(self._deliveries[-30:])),
            "health": self._health(),
            "detections": {
                "lostEvents": 0,
                "duplicateEvents": self._duplicate_events,
                "delayedEvents": 0,
                "brokenCorrelations": self._broken_correlations,
                "communicationFailures": 0,
                "unauthorizedEvents": self._unauthorized_events,
            },
        }

    def search(self, filters: dict[str, str]) -> tuple[EnterpriseEvent, ...]:
        """Search events by Commander-supported fields."""
        normalized = {key: str(value).strip() for key, value in filters.items() if str(value).strip()}
        return tuple(event for event in self._events if _matches(event, normalized))

    def _deliver(self, event: EnterpriseEvent) -> None:
        for subscriber, rules in SUBSCRIPTIONS.items():
            if _subscribed(event, rules):
                self._deliveries.append(
                    EventDelivery(
                        delivery_id=f"DEL-{len(self._deliveries) + 1:06d}",
                        event_id=event.event_id,
                        subscriber=subscriber,
                        status="DELIVERED",
                        timestamp_utc=utc_timestamp(),
                    )
                )

    def _health(self) -> dict[str, Any]:
        delivered_events = {delivery.event_id for delivery in self._deliveries if delivery.status == "DELIVERED"}
        delivery_success = 100 if not self._events else round((len(delivered_events) / len(self._events)) * 100, 1)
        return {
            "eventThroughput": len(self._events),
            "eventLatencyMs": 0,
            "eventOrdering": "CHRONOLOGICAL",
            "communicationHealth": "NOMINAL",
            "subscriptionHealth": "NOMINAL" if self._deliveries or not self._events else "NO_DELIVERIES",
            "correlationIntegrity": "NOMINAL" if self._broken_correlations == 0 else "ATTENTION",
            "eventDeliverySuccess": f"{delivery_success}%",
            "archiveDepth": len(self._events),
        }


def _event_contract(sequence: int, event: EnterpriseEvent) -> OperationalContract:
    payload = asdict(event)
    timestamp = event.timestamp_utc
    return OperationalContract(
        contract_id=generate_document_id(9900 + sequence),
        contract_type="ENTERPRISE_ACTIVITY_EVENT",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=event.case_file_id,
        trade_cycle_id=generate_trade_cycle_id(9900 + sequence),
        parent_contract_ids=(),
        produced_by_staff_id="STF-001",
        produced_by_group_id="DEP-001",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=timestamp,
        updated_timestamp_utc=timestamp,
        validation_status=ValidationStatus.VALID,
        validation_errors=(),
        human_summary=f"EAB event {event.event_id}: {event.summary}",
        machine_payload=payload,
        signature_hash=sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest(),
        source_reference_ids=(),
    )


def _event_signature(event: EnterpriseEvent) -> str:
    return sha256(
        json.dumps(
            {
                "organization": event.organization,
                "office": event.office,
                "workflow": event.workflow,
                "task_identifier": event.task_identifier,
                "event_category": event.event_category,
                "summary": event.summary,
                "correlation_identifier": event.correlation_identifier,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _subscribed(event: EnterpriseEvent, rules: dict[str, tuple[str, ...]]) -> bool:
    return (
        _contains(rules["organizations"], event.organization)
        and _contains(rules["severities"], event.severity)
        and _contains(rules["categories"], event.event_category)
    )


def _contains(values: tuple[str, ...], candidate: str) -> bool:
    return "*" in values or candidate in values


def _matches(event: EnterpriseEvent, filters: dict[str, str]) -> bool:
    fields = {
        "organization": event.organization,
        "office": event.office,
        "severity": event.severity,
        "workflow": event.workflow,
        "asset": event.asset,
        "portfolio": event.portfolio,
        "caseFile": event.case_file_id,
        "case_file": event.case_file_id,
        "case_file_id": event.case_file_id,
        "status": event.status,
        "time": event.timestamp_utc,
    }
    for key, value in filters.items():
        if key == "time":
            if value not in event.timestamp_utc:
                return False
            continue
        if fields.get(key, "").lower() != value.lower():
            return False
    return True


def _feed_item(event: EnterpriseEvent) -> dict[str, str]:
    return {
        "time": event.timestamp_utc[11:19],
        "group": event.organization.upper(),
        "message": event.summary,
        "reference": event.event_id,
        "status": event.status,
    }
