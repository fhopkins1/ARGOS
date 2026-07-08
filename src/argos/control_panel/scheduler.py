"""Office operating modes and deterministic scheduling for ARGOS."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .ecc import ORGANIZATION_OFFICES


class OperatingMode(str, Enum):
    """Permitted office operating modes."""

    DORMANT = "Dormant"
    EVENT_DRIVEN = "Event Driven"
    SCHEDULED = "Scheduled"
    BUSINESS_HOURS = "Business Hours"
    CONTINUOUS_OPERATION = "Continuous Operation"


@dataclass
class OfficeSchedule:
    """Commander-configurable schedule and resource policy for one office."""

    schedule_id: str
    organization: str
    office: str
    operating_mode: OperatingMode
    status: str
    time_zone: str
    business_hours: str
    scheduled_tasks: tuple[str, ...]
    wake_triggers: tuple[str, ...]
    sleep_triggers: tuple[str, ...]
    runtime_limit_minutes: int
    resource_budget_usd: float
    runtime_minutes: int
    cpu_usage: int
    memory_usage: int
    token_consumption: int
    queue_length: int
    wake_count: int
    last_transition_utc: str


class OfficeScheduler:
    """Manage office activation, suspension, modes, budgets, and analytics."""

    def __init__(self) -> None:
        self._offices = _baseline_offices()
        self._detections = {
            "runawayProcesses": 0,
            "scheduleConflicts": 0,
            "resourceExhaustion": 0,
            "missedActivations": 0,
            "unexpectedWakeEvents": 0,
            "stalledOffices": 0,
            "runtimeViolations": 0,
        }

    def snapshot(self) -> dict[str, Any]:
        """Return deterministic scheduler state and analytics."""
        offices = tuple(asdict(office) | {"operating_mode": office.operating_mode.value} for office in self._offices.values())
        active = [office for office in self._offices.values() if office.status == "ACTIVE"]
        sleeping = [office for office in self._offices.values() if office.status == "SLEEPING"]
        return {
            "offices": offices,
            "summary": {
                "activeOffices": len(active),
                "sleepingOffices": len(sleeping),
                "totalOffices": len(self._offices),
                "estimatedComputeCostUsd": round(sum(_estimated_cost(office) for office in self._offices.values()), 4),
                "tokenConsumption": sum(office.token_consumption for office in self._offices.values()),
                "queueLength": sum(office.queue_length for office in self._offices.values()),
            },
            "analytics": {
                "officeUtilization": _percentage(len(active), len(self._offices)),
                "runtimeStatistics": {
                    "averageRuntimeMinutes": round(sum(office.runtime_minutes for office in self._offices.values()) / len(self._offices), 2),
                    "maxRuntimeMinutes": max(office.runtime_minutes for office in self._offices.values()),
                },
                "schedulingEfficiency": _scheduling_efficiency(self._offices.values()),
                "resourceAllocation": _resource_allocation(self._offices.values()),
                "wakeFrequency": sum(office.wake_count for office in self._offices.values()),
            },
            "detections": dict(self._detections),
        }

    def configure(
        self,
        *,
        organization: str,
        office: str,
        operating_mode: str,
        time_zone: str = "America/Cancun",
        business_hours: str = "09:30-16:00",
        scheduled_tasks: tuple[str, ...] = (),
        wake_triggers: tuple[str, ...] = (),
        sleep_triggers: tuple[str, ...] = (),
        runtime_limit_minutes: int = 60,
        resource_budget_usd: float = 5.0,
    ) -> OfficeSchedule:
        """Configure an office schedule and operating mode."""
        key = _key(organization, office)
        if key not in self._offices:
            raise ValueError(f"unknown office schedule target: {organization}/{office}")
        mode = _mode(operating_mode)
        office_state = self._offices[key]
        office_state.operating_mode = mode
        office_state.time_zone = time_zone
        office_state.business_hours = business_hours
        office_state.scheduled_tasks = tuple(scheduled_tasks)
        office_state.wake_triggers = tuple(wake_triggers)
        office_state.sleep_triggers = tuple(sleep_triggers)
        office_state.runtime_limit_minutes = max(1, int(runtime_limit_minutes))
        office_state.resource_budget_usd = max(0.0, round(float(resource_budget_usd), 2))
        office_state.last_transition_utc = utc_timestamp()
        _refresh_detections(office_state, self._detections)
        return office_state

    def activate(self, organization: str, office: str, trigger: str) -> OfficeSchedule:
        """Wake an office for a deterministic trigger."""
        office_state = self._office(organization, office)
        office_state.status = "ACTIVE"
        office_state.wake_count += 1
        office_state.last_transition_utc = utc_timestamp()
        if trigger and trigger not in office_state.wake_triggers and trigger not in {"Commander", "Critical Alert", "Enterprise Event", "Scheduled Event"}:
            self._detections["unexpectedWakeEvents"] += 1
        return office_state

    def suspend(self, organization: str, office: str, trigger: str) -> OfficeSchedule:
        """Suspend an office after completion or Commander request."""
        office_state = self._office(organization, office)
        office_state.status = "SLEEPING"
        office_state.last_transition_utc = utc_timestamp()
        return office_state

    def tick(self) -> None:
        """Advance deterministic runtime counters for active offices."""
        for office in self._offices.values():
            if office.status != "ACTIVE":
                continue
            office.runtime_minutes += 1
            office.token_consumption += 48
            office.cpu_usage = min(100, office.cpu_usage + 1)
            office.memory_usage = min(100, office.memory_usage + 1)
            _refresh_detections(office, self._detections)

    def _office(self, organization: str, office: str) -> OfficeSchedule:
        key = _key(organization, office)
        if key not in self._offices:
            raise ValueError(f"unknown office schedule target: {organization}/{office}")
        return self._offices[key]


def _baseline_offices() -> dict[str, OfficeSchedule]:
    offices: dict[str, OfficeSchedule] = {}
    sequence = 1
    for organization, office_names in ORGANIZATION_OFFICES.items():
        for office in office_names:
            mode = OperatingMode.CONTINUOUS_OPERATION if organization in {"Executive", "Infrastructure"} else OperatingMode.EVENT_DRIVEN
            status = "ACTIVE" if mode == OperatingMode.CONTINUOUS_OPERATION else "SLEEPING"
            offices[_key(organization, office)] = OfficeSchedule(
                schedule_id=f"SCH-{sequence:06d}",
                organization=organization,
                office=office,
                operating_mode=mode,
                status=status,
                time_zone="America/Cancun",
                business_hours="09:30-16:00",
                scheduled_tasks=("heartbeat",) if status == "ACTIVE" else (),
                wake_triggers=("Commander", "Enterprise Event", "Critical Alert"),
                sleep_triggers=("Workflow Complete", "Commander", "Runtime Limit"),
                runtime_limit_minutes=240 if status == "ACTIVE" else 60,
                resource_budget_usd=12.0 if status == "ACTIVE" else 3.0,
                runtime_minutes=15 if status == "ACTIVE" else 0,
                cpu_usage=18 if status == "ACTIVE" else 2,
                memory_usage=24 if status == "ACTIVE" else 4,
                token_consumption=720 if status == "ACTIVE" else 0,
                queue_length=1 if status == "ACTIVE" else 0,
                wake_count=1 if status == "ACTIVE" else 0,
                last_transition_utc=utc_timestamp(),
            )
            sequence += 1
    return offices


def _key(organization: str, office: str) -> str:
    return f"{organization}::{office}"


def _mode(value: str) -> OperatingMode:
    normalized = value.strip().replace("_", " ").title()
    aliases = {
        "Active": OperatingMode.CONTINUOUS_OPERATION,
        "Paper Trading": OperatingMode.EVENT_DRIVEN,
    }
    if normalized in aliases:
        return aliases[normalized]
    for mode in OperatingMode:
        if mode.value == normalized:
            return mode
    raise ValueError(f"unsupported operating mode: {value}")


def _percentage(value: int, total: int) -> str:
    return f"{round((value / total) * 100, 1) if total else 0}%"


def _estimated_cost(office: OfficeSchedule) -> float:
    return (office.runtime_minutes * 0.0025) + (office.token_consumption / 1000 * 0.0015)


def _scheduling_efficiency(offices: Any) -> str:
    office_tuple = tuple(offices)
    productive = sum(1 for office in office_tuple if office.status == "ACTIVE" and office.queue_length <= 3)
    return _percentage(productive, len(office_tuple))


def _resource_allocation(offices: Any) -> dict[str, int]:
    office_tuple = tuple(offices)
    return {
        "cpuAverage": round(sum(office.cpu_usage for office in office_tuple) / len(office_tuple)),
        "memoryAverage": round(sum(office.memory_usage for office in office_tuple) / len(office_tuple)),
        "budgetAverageUsd": round(sum(office.resource_budget_usd for office in office_tuple) / len(office_tuple)),
    }


def _refresh_detections(office: OfficeSchedule, detections: dict[str, int]) -> None:
    if office.runtime_minutes > office.runtime_limit_minutes:
        detections["runtimeViolations"] += 1
    if office.cpu_usage >= 95 or office.memory_usage >= 95:
        detections["resourceExhaustion"] += 1
    if office.status == "ACTIVE" and office.runtime_minutes > office.runtime_limit_minutes * 2:
        detections["runawayProcesses"] += 1
    if office.status == "ACTIVE" and office.queue_length > 10:
        detections["stalledOffices"] += 1
    if office.operating_mode == OperatingMode.SCHEDULED and not office.scheduled_tasks:
        detections["scheduleConflicts"] += 1
