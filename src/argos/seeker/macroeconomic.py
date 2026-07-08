"""Macroeconomic Office scaffolding and deterministic monitoring."""

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


MACROECONOMIC_OFFICE_ID = "SEEKER-OFFICE-003"


@dataclass(frozen=True)
class MacroeconomicObservation:
    """Input observation for deterministic macroeconomic monitoring."""

    inflation_rate: float | None
    policy_rate: float | None
    unemployment_rate: float | None
    gdp_growth: float | None
    monetary_policy_bias: str | None
    fiscal_policy_bias: str | None
    currency_change: float | None
    yield_curve_spread: float | None
    commodity_index_change: float | None
    global_growth: float | None


@dataclass(frozen=True)
class MacroeconomicSignal:
    """Deterministic macroeconomic signal."""

    seeker: str
    signal: str
    value: float | str | None
    report_hint: str


class InflationSeeker:
    def generate(self, observation: MacroeconomicObservation) -> MacroeconomicSignal:
        if observation.inflation_rate is None:
            return MacroeconomicSignal("inflation", "inflation_unknown", None, "information_gap")
        signal = "inflation_threat" if observation.inflation_rate > 4 else "inflation_contained"
        return MacroeconomicSignal("inflation", signal, observation.inflation_rate, "threat" if signal.endswith("threat") else "opportunity")


class InterestRateSeeker:
    def generate(self, observation: MacroeconomicObservation) -> MacroeconomicSignal:
        if observation.policy_rate is None:
            return MacroeconomicSignal("interest_rate", "policy_rate_unknown", None, "information_gap")
        signal = "restrictive_rates" if observation.policy_rate >= 5 else "accommodative_rates"
        return MacroeconomicSignal("interest_rate", signal, observation.policy_rate, "threat" if signal == "restrictive_rates" else "opportunity")


class LaborMarketSeeker:
    def generate(self, observation: MacroeconomicObservation) -> MacroeconomicSignal:
        if observation.unemployment_rate is None:
            return MacroeconomicSignal("labor_market", "labor_data_unknown", None, "information_gap")
        signal = "labor_market_stress" if observation.unemployment_rate > 6 else "labor_market_resilient"
        return MacroeconomicSignal("labor_market", signal, observation.unemployment_rate, "threat" if signal.endswith("stress") else "opportunity")


class GDPSeeker:
    def generate(self, observation: MacroeconomicObservation) -> MacroeconomicSignal:
        if observation.gdp_growth is None:
            return MacroeconomicSignal("gdp", "gdp_growth_unknown", None, "information_gap")
        signal = "growth_contraction" if observation.gdp_growth < 0 else "growth_expansion"
        return MacroeconomicSignal("gdp", signal, observation.gdp_growth, "threat" if signal.endswith("contraction") else "opportunity")


class MonetaryPolicySeeker:
    def generate(self, observation: MacroeconomicObservation) -> MacroeconomicSignal:
        if observation.monetary_policy_bias is None:
            return MacroeconomicSignal("monetary_policy", "monetary_policy_unknown", None, "information_gap")
        normalized = observation.monetary_policy_bias.lower()
        signal = "monetary_tightening" if normalized == "tightening" else "monetary_neutral_or_easing"
        return MacroeconomicSignal("monetary_policy", signal, normalized, "threat" if signal == "monetary_tightening" else "opportunity")


class FiscalPolicySeeker:
    def generate(self, observation: MacroeconomicObservation) -> MacroeconomicSignal:
        if observation.fiscal_policy_bias is None:
            return MacroeconomicSignal("fiscal_policy", "fiscal_policy_unknown", None, "information_gap")
        normalized = observation.fiscal_policy_bias.lower()
        signal = "fiscal_supportive" if normalized == "supportive" else "fiscal_restrictive_or_neutral"
        return MacroeconomicSignal("fiscal_policy", signal, normalized, "opportunity" if signal == "fiscal_supportive" else "threat")


class CurrencySeeker:
    def generate(self, observation: MacroeconomicObservation) -> MacroeconomicSignal:
        if observation.currency_change is None:
            return MacroeconomicSignal("currency", "currency_data_unknown", None, "information_gap")
        signal = "currency_volatility" if abs(observation.currency_change) > 3 else "currency_stable"
        return MacroeconomicSignal("currency", signal, observation.currency_change, "threat" if signal.endswith("volatility") else "opportunity")


class BondMarketSeeker:
    def generate(self, observation: MacroeconomicObservation) -> MacroeconomicSignal:
        if observation.yield_curve_spread is None:
            return MacroeconomicSignal("bond_market", "yield_curve_unknown", None, "information_gap")
        signal = "yield_curve_inversion" if observation.yield_curve_spread < 0 else "yield_curve_normal"
        return MacroeconomicSignal("bond_market", signal, observation.yield_curve_spread, "threat" if signal.endswith("inversion") else "opportunity")


class CommoditySeeker:
    def generate(self, observation: MacroeconomicObservation) -> MacroeconomicSignal:
        if observation.commodity_index_change is None:
            return MacroeconomicSignal("commodity", "commodity_data_unknown", None, "information_gap")
        signal = "commodity_shock" if abs(observation.commodity_index_change) > 10 else "commodity_stable"
        return MacroeconomicSignal("commodity", signal, observation.commodity_index_change, "threat" if signal.endswith("shock") else "opportunity")


class GlobalEconomySeeker:
    def generate(self, observation: MacroeconomicObservation) -> MacroeconomicSignal:
        if observation.global_growth is None:
            return MacroeconomicSignal("global_economy", "global_growth_unknown", None, "information_gap")
        signal = "global_slowdown" if observation.global_growth < 1 else "global_growth_supportive"
        return MacroeconomicSignal("global_economy", signal, observation.global_growth, "threat" if signal.endswith("slowdown") else "opportunity")


class MacroeconomicScreener:
    """Combines macroeconomic seekers without trade recommendation."""

    def __init__(self) -> None:
        self.seekers = (
            InflationSeeker(),
            InterestRateSeeker(),
            LaborMarketSeeker(),
            GDPSeeker(),
            MonetaryPolicySeeker(),
            FiscalPolicySeeker(),
            CurrencySeeker(),
            BondMarketSeeker(),
            CommoditySeeker(),
            GlobalEconomySeeker(),
        )

    def monitor(self, observation: MacroeconomicObservation) -> tuple[MacroeconomicSignal, ...]:
        return tuple(seeker.generate(observation) for seeker in self.seekers)


class MacroeconomicOfficeChief:
    """Office Chief for deterministic Macroeconomic Office."""

    def __init__(self, screener: MacroeconomicScreener | None = None) -> None:
        self.screener = screener or MacroeconomicScreener()

    def review(self, observation: MacroeconomicObservation) -> tuple[MacroeconomicSignal, ...]:
        return self.screener.monitor(observation)


class MacroeconomicOffice:
    """Macroeconomic Office integrated with Seeker Department."""

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
        self.office = self.department.offices[MACROECONOMIC_OFFICE_ID]
        self.chief = MacroeconomicOfficeChief()
        self.last_signals: tuple[MacroeconomicSignal, ...] = ()

    def ingest(self, observation: MacroeconomicObservation) -> tuple[MacroeconomicSignal, ...]:
        self.last_signals = self.chief.review(observation)
        return self.last_signals

    def generate_cor(
        self,
        observation: MacroeconomicObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "opportunity")
        return self._generate_report(
            "COR",
            "macro_candidate_unanalysed",
            "Macroeconomic Candidate Opportunity Report.",
            signals,
            case_file_id,
            trade_cycle_id,
            document_sequence,
            prompt_id,
        )

    def generate_threat_report(
        self,
        observation: MacroeconomicObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "threat")
        return self._generate_report(
            "MTR",
            "macro_threat_identified",
            "Macroeconomic Threat Report.",
            signals,
            case_file_id,
            trade_cycle_id,
            document_sequence,
            prompt_id,
        )

    def generate_information_gap_report(
        self,
        observation: MacroeconomicObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "information_gap")
        return self._generate_report(
            "IGR",
            "macro_information_gap",
            "Macroeconomic Information Gap Report.",
            signals,
            case_file_id,
            trade_cycle_id,
            document_sequence,
            prompt_id,
        )

    def route_report(self, report: OperationalContract, target_inbox: IncomingMailbox):
        result = self.department.route_cor(MACROECONOMIC_OFFICE_ID, report, target_inbox)
        return result

    def instrument_panel(self) -> OfficeInstrumentPanel:
        return self.office.instrument_panel()

    def _generate_report(
        self,
        contract_type: str,
        report_status: str,
        human_summary: str,
        signals: tuple[MacroeconomicSignal, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(
            prompt_id,
            case_file_id,
            trade_cycle_id,
        )
        created = utc_timestamp()
        payload = {
            "office_id": MACROECONOMIC_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "report_status": report_status,
            "macroeconomic_signals": [signal.__dict__ for signal in signals],
        }
        signature_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
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
