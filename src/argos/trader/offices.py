"""Trader Group office framework."""

from __future__ import annotations

from dataclasses import dataclass, field

from argos.foundation.communication import IncomingMailbox, OutgoingMailbox


TRADER_GROUP_ID = "DEP-006"


@dataclass(frozen=True)
class TraderOfficeConfiguration:
    """Trader office configuration."""

    office_id: str
    name: str
    staff_id: str
    enabled: bool = True


@dataclass(frozen=True)
class TraderOfficeRecord:
    """Registered Trader office record."""

    configuration: TraderOfficeConfiguration
    inbox: IncomingMailbox
    outbox: OutgoingMailbox


class TraderOfficeRegistry:
    """Deterministic Trader office registry."""

    def __init__(self) -> None:
        self._offices: dict[str, TraderOfficeRecord] = {}

    def register(self, configuration: TraderOfficeConfiguration) -> TraderOfficeRecord:
        """Register a Trader office once."""
        if configuration.office_id in self._offices:
            raise ValueError(f"trader office already registered: {configuration.office_id}")
        record = TraderOfficeRecord(
            configuration,
            IncomingMailbox(configuration.staff_id, TRADER_GROUP_ID),
            OutgoingMailbox(configuration.staff_id, TRADER_GROUP_ID),
        )
        self._offices[configuration.office_id] = record
        return record

    def get(self, office_id: str) -> TraderOfficeRecord | None:
        """Return a Trader office record."""
        return self._offices.get(office_id)

    def all(self) -> tuple[TraderOfficeRecord, ...]:
        """Return all offices in deterministic order."""
        return tuple(self._offices[key] for key in sorted(self._offices))


class TraderOfficeQueue:
    """FIFO queue for deterministic Trader work."""

    def __init__(self) -> None:
        self._items: list[str] = []

    def enqueue(self, item_id: str) -> None:
        self._items.append(item_id)

    def dequeue(self) -> str:
        if not self._items:
            raise IndexError("trader office queue is empty")
        return self._items.pop(0)

    def __len__(self) -> int:
        return len(self._items)


@dataclass(frozen=True)
class TraderOfficeMetrics:
    """Trader office metrics."""

    queue_depth: int
    generated_records: int
    routed_records: int


@dataclass(frozen=True)
class TraderOfficeHealth:
    """Trader office health."""

    status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class TraderOfficeInstrumentPanel:
    """Traceable Trader office instrument panel."""

    office_id: str
    metrics: TraderOfficeMetrics
    health: TraderOfficeHealth
    source: str


@dataclass
class TraderOffice:
    """Trader execution office scaffold."""

    record: TraderOfficeRecord
    queue: TraderOfficeQueue = field(default_factory=TraderOfficeQueue)
    generated_records: int = 0
    routed_records: int = 0

    def metrics(self) -> TraderOfficeMetrics:
        return TraderOfficeMetrics(len(self.queue), self.generated_records, self.routed_records)

    def health(self) -> TraderOfficeHealth:
        reasons = []
        if not self.record.configuration.enabled:
            reasons.append("office_disabled")
        if len(self.queue) > 10:
            reasons.append("queue_depth_high")
        return TraderOfficeHealth("healthy" if not reasons else "attention", tuple(reasons))

    def instrument_panel(self) -> TraderOfficeInstrumentPanel:
        return TraderOfficeInstrumentPanel(
            self.record.configuration.office_id,
            self.metrics(),
            self.health(),
            f"office:{self.record.configuration.office_id}",
        )


def trader_office_templates() -> tuple[TraderOfficeConfiguration, ...]:
    """Return EO-052 Trader office templates."""
    names = (
        "Trade Execution Office",
        "Order Management Office",
        "Broker Integration Office",
        "Execution Quality Office",
        "Position Management Office",
        "Trade Monitoring Office",
        "Trader Fusion Office",
    )
    return tuple(
        TraderOfficeConfiguration(f"TRADER-OFFICE-{index:03d}", name, f"STF-{60 + index:03d}")
        for index, name in enumerate(names, start=1)
    )
