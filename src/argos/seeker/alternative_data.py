"""Alternative Data Office scaffolding and deterministic real-world monitoring."""

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


ALTERNATIVE_DATA_OFFICE_ID = "SEEKER-OFFICE-008"


@dataclass(frozen=True)
class AlternativeDataObservation:
    """Input observation for deterministic alternative-data monitoring."""

    satellite_activity_change: float | None
    shipping_delay_index: float | None
    web_traffic_change: float | None
    consumer_activity_change: float | None
    energy_consumption_change: float | None
    weather_disruption_score: float | None
    supply_chain_stress_score: float | None
    patent_activity_change: float | None
    employment_posting_change: float | None


@dataclass(frozen=True)
class AlternativeDataSignal:
    """Deterministic alternative-data signal."""

    seeker: str
    signal: str
    value: float | str | None
    report_hint: str


class SatelliteImagerySeeker:
    def generate(self, observation: AlternativeDataObservation) -> AlternativeDataSignal:
        if observation.satellite_activity_change is None:
            return AlternativeDataSignal("satellite_imagery", "satellite_activity_unknown", None, "information_gap")
        signal = "satellite_activity_expanding" if observation.satellite_activity_change > 0 else "satellite_activity_contracting"
        return AlternativeDataSignal("satellite_imagery", signal, observation.satellite_activity_change, "alternative_intelligence" if observation.satellite_activity_change > 0 else "threat")


class ShippingLogisticsSeeker:
    def generate(self, observation: AlternativeDataObservation) -> AlternativeDataSignal:
        if observation.shipping_delay_index is None:
            return AlternativeDataSignal("shipping_logistics", "shipping_logistics_unknown", None, "information_gap")
        signal = "shipping_delay_threat" if observation.shipping_delay_index >= 0.6 else "shipping_flow_orderly"
        return AlternativeDataSignal("shipping_logistics", signal, observation.shipping_delay_index, "threat" if signal.endswith("threat") else "opportunity")


class WebTrafficSeeker:
    def generate(self, observation: AlternativeDataObservation) -> AlternativeDataSignal:
        if observation.web_traffic_change is None:
            return AlternativeDataSignal("web_traffic", "web_traffic_unknown", None, "information_gap")
        signal = "web_traffic_expanding" if observation.web_traffic_change > 0 else "web_traffic_contracting"
        return AlternativeDataSignal("web_traffic", signal, observation.web_traffic_change, "alternative_intelligence" if observation.web_traffic_change > 0 else "threat")


class ConsumerActivitySeeker:
    def generate(self, observation: AlternativeDataObservation) -> AlternativeDataSignal:
        if observation.consumer_activity_change is None:
            return AlternativeDataSignal("consumer_activity", "consumer_activity_unknown", None, "information_gap")
        signal = "consumer_activity_expanding" if observation.consumer_activity_change > 0 else "consumer_activity_contracting"
        return AlternativeDataSignal("consumer_activity", signal, observation.consumer_activity_change, "opportunity" if observation.consumer_activity_change > 0 else "threat")


class EnergyConsumptionSeeker:
    def generate(self, observation: AlternativeDataObservation) -> AlternativeDataSignal:
        if observation.energy_consumption_change is None:
            return AlternativeDataSignal("energy_consumption", "energy_consumption_unknown", None, "information_gap")
        signal = "energy_consumption_expanding" if observation.energy_consumption_change > 0 else "energy_consumption_contracting"
        return AlternativeDataSignal("energy_consumption", signal, observation.energy_consumption_change, "alternative_intelligence" if observation.energy_consumption_change > 0 else "threat")


class WeatherIntelligenceSeeker:
    def generate(self, observation: AlternativeDataObservation) -> AlternativeDataSignal:
        if observation.weather_disruption_score is None:
            return AlternativeDataSignal("weather_intelligence", "weather_intelligence_unknown", None, "information_gap")
        signal = "weather_disruption_threat" if observation.weather_disruption_score >= 0.5 else "weather_conditions_orderly"
        return AlternativeDataSignal("weather_intelligence", signal, observation.weather_disruption_score, "threat" if signal.endswith("threat") else "opportunity")


class SupplyChainIntelligenceSeeker:
    def generate(self, observation: AlternativeDataObservation) -> AlternativeDataSignal:
        if observation.supply_chain_stress_score is None:
            return AlternativeDataSignal("supply_chain_intelligence", "supply_chain_intelligence_unknown", None, "information_gap")
        signal = "supply_chain_stress" if observation.supply_chain_stress_score >= 0.5 else "supply_chain_stable"
        return AlternativeDataSignal("supply_chain_intelligence", signal, observation.supply_chain_stress_score, "threat" if signal.endswith("stress") else "alternative_intelligence")


class PatentActivitySeeker:
    def generate(self, observation: AlternativeDataObservation) -> AlternativeDataSignal:
        if observation.patent_activity_change is None:
            return AlternativeDataSignal("patent_activity", "patent_activity_unknown", None, "information_gap")
        signal = "patent_activity_expanding" if observation.patent_activity_change > 0 else "patent_activity_contracting"
        return AlternativeDataSignal("patent_activity", signal, observation.patent_activity_change, "alternative_intelligence" if observation.patent_activity_change > 0 else "threat")


class EmploymentIntelligenceSeeker:
    def generate(self, observation: AlternativeDataObservation) -> AlternativeDataSignal:
        if observation.employment_posting_change is None:
            return AlternativeDataSignal("employment_intelligence", "employment_intelligence_unknown", None, "information_gap")
        signal = "employment_postings_expanding" if observation.employment_posting_change > 0 else "employment_postings_contracting"
        return AlternativeDataSignal("employment_intelligence", signal, observation.employment_posting_change, "opportunity" if observation.employment_posting_change > 0 else "threat")


class AlternativeDataScreener:
    """Combines alternative-data seekers without trade recommendation."""

    def __init__(self) -> None:
        self.seekers = (
            SatelliteImagerySeeker(),
            ShippingLogisticsSeeker(),
            WebTrafficSeeker(),
            ConsumerActivitySeeker(),
            EnergyConsumptionSeeker(),
            WeatherIntelligenceSeeker(),
            SupplyChainIntelligenceSeeker(),
            PatentActivitySeeker(),
            EmploymentIntelligenceSeeker(),
        )

    def monitor(self, observation: AlternativeDataObservation) -> tuple[AlternativeDataSignal, ...]:
        return tuple(seeker.generate(observation) for seeker in self.seekers)


class AlternativeDataOfficeChief:
    """Office Chief for deterministic Alternative Data Office."""

    def __init__(self, screener: AlternativeDataScreener | None = None) -> None:
        self.screener = screener or AlternativeDataScreener()

    def review(self, observation: AlternativeDataObservation) -> tuple[AlternativeDataSignal, ...]:
        return self.screener.monitor(observation)


class AlternativeDataOffice:
    """Alternative Data Office integrated with Seeker Department."""

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
        self.office = self.department.offices[ALTERNATIVE_DATA_OFFICE_ID]
        self.chief = AlternativeDataOfficeChief()
        self.last_signals: tuple[AlternativeDataSignal, ...] = ()

    def ingest(self, observation: AlternativeDataObservation) -> tuple[AlternativeDataSignal, ...]:
        self.last_signals = self.chief.review(observation)
        return self.last_signals

    def generate_cor(self, observation: AlternativeDataObservation, case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "opportunity")
        return self._generate_report("COR", "alternative_candidate_unanalysed", "Alternative Data Candidate Opportunity Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_threat_report(self, observation: AlternativeDataObservation, case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "threat")
        return self._generate_report("ATR", "alternative_threat_identified", "Alternative Data Threat Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_information_gap_report(self, observation: AlternativeDataObservation, case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "information_gap")
        return self._generate_report("IGR", "alternative_information_gap", "Alternative Data Information Gap Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_alternative_intelligence_report(self, observation: AlternativeDataObservation, case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "alternative_intelligence")
        return self._generate_report("AIR", "alternative_intelligence_available", "Alternative Intelligence Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def route_report(self, report: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_cor(ALTERNATIVE_DATA_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> OfficeInstrumentPanel:
        return self.office.instrument_panel()

    def _generate_report(
        self,
        contract_type: str,
        report_status: str,
        human_summary: str,
        signals: tuple[AlternativeDataSignal, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        created = utc_timestamp()
        payload = {
            "office_id": ALTERNATIVE_DATA_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "report_status": report_status,
            "alternative_data_signals": [signal.__dict__ for signal in signals],
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
