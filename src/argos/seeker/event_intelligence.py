"""Event Intelligence Office scaffolding and deterministic event monitoring."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from argos.foundation.audit import AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService

from .department import SeekerDepartment
from .offices import OfficeInstrumentPanel, SEEKER_GROUP_ID


EVENT_INTELLIGENCE_OFFICE_ID = "SEEKER-OFFICE-007"


@dataclass(frozen=True)
class EventIntelligenceObservation:
    """Input observation for deterministic objective event monitoring."""

    earnings_surprise: float | None
    merger_announced: bool | None
    bankruptcy_risk_score: float | None
    regulatory_severity: float | None
    fda_decision_score: float | None
    litigation_severity: float | None
    product_launch_score: float | None
    geopolitical_severity: float | None
    supply_chain_disruption_score: float | None


@dataclass(frozen=True)
class EventIntelligenceSignal:
    """Deterministic event intelligence signal."""

    seeker: str
    signal: str
    value: float | bool | str | None
    report_hint: str


class EarningsEventSeeker:
    def generate(self, observation: EventIntelligenceObservation) -> EventIntelligenceSignal:
        if observation.earnings_surprise is None:
            return EventIntelligenceSignal("earnings_event", "earnings_event_unknown", None, "information_gap")
        signal = "positive_earnings_event" if observation.earnings_surprise > 0 else "negative_earnings_event"
        return EventIntelligenceSignal("earnings_event", signal, observation.earnings_surprise, "opportunity" if observation.earnings_surprise > 0 else "threat")


class MergerAcquisitionSeeker:
    def generate(self, observation: EventIntelligenceObservation) -> EventIntelligenceSignal:
        if observation.merger_announced is None:
            return EventIntelligenceSignal("merger_acquisition", "ma_event_unknown", None, "information_gap")
        signal = "ma_event_announced" if observation.merger_announced else "ma_event_absent"
        return EventIntelligenceSignal("merger_acquisition", signal, observation.merger_announced, "event_assessment" if observation.merger_announced else "information_gap")


class BankruptcySeeker:
    def generate(self, observation: EventIntelligenceObservation) -> EventIntelligenceSignal:
        if observation.bankruptcy_risk_score is None:
            return EventIntelligenceSignal("bankruptcy", "bankruptcy_risk_unknown", None, "information_gap")
        signal = "bankruptcy_risk_elevated" if observation.bankruptcy_risk_score >= 0.7 else "bankruptcy_risk_contained"
        return EventIntelligenceSignal("bankruptcy", signal, observation.bankruptcy_risk_score, "threat" if signal.endswith("elevated") else "opportunity")


class RegulatoryEventSeeker:
    def generate(self, observation: EventIntelligenceObservation) -> EventIntelligenceSignal:
        if observation.regulatory_severity is None:
            return EventIntelligenceSignal("regulatory_event", "regulatory_event_unknown", None, "information_gap")
        signal = "regulatory_event_material" if observation.regulatory_severity >= 0.5 else "regulatory_event_minor"
        return EventIntelligenceSignal("regulatory_event", signal, observation.regulatory_severity, "threat" if signal.endswith("material") else "event_assessment")


class FDAEventSeeker:
    def generate(self, observation: EventIntelligenceObservation) -> EventIntelligenceSignal:
        if observation.fda_decision_score is None:
            return EventIntelligenceSignal("fda_event", "fda_event_unknown", None, "information_gap")
        signal = "fda_event_positive" if observation.fda_decision_score > 0 else "fda_event_negative"
        return EventIntelligenceSignal("fda_event", signal, observation.fda_decision_score, "opportunity" if observation.fda_decision_score > 0 else "threat")


class LitigationSeeker:
    def generate(self, observation: EventIntelligenceObservation) -> EventIntelligenceSignal:
        if observation.litigation_severity is None:
            return EventIntelligenceSignal("litigation", "litigation_event_unknown", None, "information_gap")
        signal = "litigation_threat" if observation.litigation_severity >= 0.5 else "litigation_minor"
        return EventIntelligenceSignal("litigation", signal, observation.litigation_severity, "threat" if signal.endswith("threat") else "event_assessment")


class ProductLaunchSeeker:
    def generate(self, observation: EventIntelligenceObservation) -> EventIntelligenceSignal:
        if observation.product_launch_score is None:
            return EventIntelligenceSignal("product_launch", "product_launch_unknown", None, "information_gap")
        signal = "product_launch_constructive" if observation.product_launch_score > 0 else "product_launch_weak"
        return EventIntelligenceSignal("product_launch", signal, observation.product_launch_score, "opportunity" if observation.product_launch_score > 0 else "threat")


class GeopoliticalEventSeeker:
    def generate(self, observation: EventIntelligenceObservation) -> EventIntelligenceSignal:
        if observation.geopolitical_severity is None:
            return EventIntelligenceSignal("geopolitical_event", "geopolitical_event_unknown", None, "information_gap")
        signal = "geopolitical_event_threat" if observation.geopolitical_severity >= 0.6 else "geopolitical_event_watch"
        return EventIntelligenceSignal("geopolitical_event", signal, observation.geopolitical_severity, "threat" if signal.endswith("threat") else "event_assessment")


class SupplyChainEventSeeker:
    def generate(self, observation: EventIntelligenceObservation) -> EventIntelligenceSignal:
        if observation.supply_chain_disruption_score is None:
            return EventIntelligenceSignal("supply_chain_event", "supply_chain_event_unknown", None, "information_gap")
        signal = "supply_chain_disruption" if observation.supply_chain_disruption_score >= 0.5 else "supply_chain_stable"
        return EventIntelligenceSignal("supply_chain_event", signal, observation.supply_chain_disruption_score, "threat" if signal.endswith("disruption") else "event_assessment")


class EventIntelligenceScreener:
    """Combines objective event seekers without trade recommendation."""

    def __init__(self) -> None:
        self.seekers = (
            EarningsEventSeeker(),
            MergerAcquisitionSeeker(),
            BankruptcySeeker(),
            RegulatoryEventSeeker(),
            FDAEventSeeker(),
            LitigationSeeker(),
            ProductLaunchSeeker(),
            GeopoliticalEventSeeker(),
            SupplyChainEventSeeker(),
        )

    def monitor(self, observation: EventIntelligenceObservation) -> tuple[EventIntelligenceSignal, ...]:
        return tuple(seeker.generate(observation) for seeker in self.seekers)


class EventIntelligenceOfficeChief:
    """Office Chief for deterministic Event Intelligence Office."""

    def __init__(self, screener: EventIntelligenceScreener | None = None) -> None:
        self.screener = screener or EventIntelligenceScreener()

    def review(self, observation: EventIntelligenceObservation) -> tuple[EventIntelligenceSignal, ...]:
        return self.screener.monitor(observation)


class EventIntelligenceOffice:
    """Event Intelligence Office integrated with Seeker Department."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = SeekerDepartment(
            configuration_service,
            persistence_repository,
            audit_service,
            prompt_repository,
        )
        self.office = self.department.offices[EVENT_INTELLIGENCE_OFFICE_ID]
        self.chief = EventIntelligenceOfficeChief()
        self.last_signals: tuple[EventIntelligenceSignal, ...] = ()

    def ingest(self, observation: EventIntelligenceObservation) -> tuple[EventIntelligenceSignal, ...]:
        self.last_signals = self.chief.review(observation)
        return self.last_signals

    def generate_cor(self, observation: EventIntelligenceObservation, case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "opportunity")
        return self._generate_report("COR", "event_candidate_unanalysed", "Event Intelligence Candidate Opportunity Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_threat_report(self, observation: EventIntelligenceObservation, case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "threat")
        return self._generate_report("ETR", "event_threat_identified", "Event Intelligence Threat Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_information_gap_report(self, observation: EventIntelligenceObservation, case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "information_gap")
        return self._generate_report("IGR", "event_information_gap", "Event Intelligence Information Gap Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_event_assessment_report(self, observation: EventIntelligenceObservation, case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "event_assessment")
        return self._generate_report("EAR", "event_assessment_available", "Event Assessment Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def route_report(self, report: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_cor(EVENT_INTELLIGENCE_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> OfficeInstrumentPanel:
        return self.office.instrument_panel()

    def _generate_report(
        self,
        contract_type: str,
        report_status: str,
        human_summary: str,
        signals: tuple[EventIntelligenceSignal, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        created = utc_timestamp()
        payload = {
            "office_id": EVENT_INTELLIGENCE_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "report_status": report_status,
            "event_intelligence_signals": [signal.__dict__ for signal in signals],
            "risk_doctrine_required": True,
        }
        signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        report = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type=contract_type,
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            parent_contract_ids=(),
            produced_by_staff_id=self.office.record.configuration.staff_id,
            produced_by_group_id=SEEKER_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary=human_summary,
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=(),
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report
