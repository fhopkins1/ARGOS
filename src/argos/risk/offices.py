"""Risk Office framework and RAR generation."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json

from argos.analyst import OrganizationalBeliefState
from argos.foundation.communication import IncomingMailbox, OutgoingMailbox
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService


RISK_GROUP_ID = "DEP-005"


@dataclass(frozen=True)
class RiskOfficeConfiguration:
    """Risk office configuration."""

    office_id: str
    name: str
    staff_id: str
    enabled: bool = True


@dataclass(frozen=True)
class RiskOfficeRecord:
    """Registered Risk office record."""

    configuration: RiskOfficeConfiguration
    inbox: IncomingMailbox
    outbox: OutgoingMailbox


class RiskOfficeRegistry:
    """Deterministic Risk office registry."""

    def __init__(self) -> None:
        self._offices: dict[str, RiskOfficeRecord] = {}

    def register(self, configuration: RiskOfficeConfiguration) -> RiskOfficeRecord:
        """Register a Risk office."""
        if configuration.office_id in self._offices:
            raise ValueError(f"risk office already registered: {configuration.office_id}")
        record = RiskOfficeRecord(
            configuration,
            IncomingMailbox(configuration.staff_id, RISK_GROUP_ID),
            OutgoingMailbox(configuration.staff_id, RISK_GROUP_ID),
        )
        self._offices[configuration.office_id] = record
        return record

    def get(self, office_id: str) -> RiskOfficeRecord | None:
        """Return a Risk office record."""
        return self._offices.get(office_id)

    def all(self) -> tuple[RiskOfficeRecord, ...]:
        """Return all Risk office records in deterministic order."""
        return tuple(self._offices[key] for key in sorted(self._offices))


class RiskOfficeQueue:
    """Risk office work queue."""

    def __init__(self) -> None:
        self._items: list[str] = []

    def enqueue(self, item_id: str) -> None:
        self._items.append(item_id)

    def dequeue(self) -> str:
        if not self._items:
            raise IndexError("risk office queue is empty")
        return self._items.pop(0)

    def __len__(self) -> int:
        return len(self._items)


@dataclass(frozen=True)
class RiskOfficeMetrics:
    """Risk office metrics."""

    queue_depth: int
    reports_generated: int
    routed_reports: int


@dataclass(frozen=True)
class RiskOfficeHealth:
    """Risk office health."""

    status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class RiskOfficeInstrumentPanel:
    """Traceable Risk office instrument panel."""

    office_id: str
    metrics: RiskOfficeMetrics
    health: RiskOfficeHealth
    source: str


@dataclass
class RiskOffice:
    """Risk safeguard office scaffold."""

    record: RiskOfficeRecord
    queue: RiskOfficeQueue = field(default_factory=RiskOfficeQueue)
    reports_generated: int = 0
    routed_reports: int = 0

    def metrics(self) -> RiskOfficeMetrics:
        return RiskOfficeMetrics(len(self.queue), self.reports_generated, self.routed_reports)

    def health(self) -> RiskOfficeHealth:
        reasons = []
        if not self.record.configuration.enabled:
            reasons.append("office_disabled")
        if len(self.queue) > 10:
            reasons.append("queue_depth_high")
        return RiskOfficeHealth("healthy" if not reasons else "attention", tuple(reasons))

    def instrument_panel(self) -> RiskOfficeInstrumentPanel:
        return RiskOfficeInstrumentPanel(
            self.record.configuration.office_id,
            self.metrics(),
            self.health(),
            f"office:{self.record.configuration.office_id}",
        )


class RiskAssessmentReportGenerator:
    """Generate Risk Assessment Reports from Organizational Belief States only."""

    def generate(
        self,
        office: RiskOffice,
        belief_state: OrganizationalBeliefState,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_repository: PromptRepository,
        prompt_id: str,
        persistence_repository: InMemoryPersistenceRepository,
    ) -> OperationalContract:
        """Generate and persist a Risk Assessment Report."""
        if not isinstance(belief_state, OrganizationalBeliefState):
            raise TypeError("Risk Assessment Reports require an OrganizationalBeliefState")
        snapshot = PromptSnapshotService(prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        risk_score = self._risk_score(belief_state)
        payload = {
            "office_id": office.record.configuration.office_id,
            "office_name": office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "risk_assessment",
            "belief_state_id": belief_state.state_id,
            "belief_state_source_report_ids": list(belief_state.source_report_ids),
            "risk_score": risk_score,
            "risk_state": self._risk_state(risk_score),
            "organizational_belief_state_modified": False,
            "trade_recommendation": None,
            "execution_instruction": None,
        }
        created = utc_timestamp()
        signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        rar = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type="RAR",
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            parent_contract_ids=belief_state.source_report_ids,
            produced_by_staff_id=office.record.configuration.staff_id,
            produced_by_group_id=RISK_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary=f"Risk Assessment Report from {office.record.configuration.name}.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=belief_state.source_report_ids,
        )
        persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, rar.contract_id, rar.to_dict())
        office.reports_generated += 1
        return rar

    def _risk_score(self, belief_state: OrganizationalBeliefState) -> float:
        confidence_risk = 1 - belief_state.organizational_confidence
        evidence_risk = 1 - belief_state.independent_evidence_score
        diversity_risk = 1 - belief_state.intellectual_diversity_score
        return round(max(0.0, min(1.0, confidence_risk * 0.5 + evidence_risk * 0.3 + diversity_risk * 0.2)), 4)

    def _risk_state(self, risk_score: float) -> str:
        if risk_score >= 0.65:
            return "high_risk"
        if risk_score >= 0.35:
            return "moderate_risk"
        return "contained_risk"


def risk_office_templates() -> tuple[RiskOfficeConfiguration, ...]:
    """Return EO-040 Risk office templates."""
    names = (
        "Position Risk Office",
        "Portfolio Risk Office",
        "Liquidity Risk Office",
        "Correlation Risk Office",
        "Volatility Risk Office",
        "Tail Risk Office",
        "Black Swan Office",
        "Bubble Detection Office",
        "Recovery Planning Office",
        "Risk Fusion Office",
    )
    return tuple(
        RiskOfficeConfiguration(f"RISK-OFFICE-{index:03d}", name, f"STF-{40 + index:03d}")
        for index, name in enumerate(names, start=1)
    )
