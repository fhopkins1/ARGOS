"""Options Flow Office scaffolding and deterministic derivative monitoring."""

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


OPTIONS_FLOW_OFFICE_ID = "SEEKER-OFFICE-005"


@dataclass(frozen=True)
class OptionsFlowObservation:
    """Input observation for deterministic options-flow monitoring."""

    option_volume: int | None
    average_option_volume: int | None
    largest_order_notional: float | None
    gamma_exposure: float | None
    delta_exposure: float | None
    open_interest: int | None
    open_interest_change: int | None
    implied_volatility: float | None
    historical_volatility: float | None
    surface_skew: float | None
    dealer_gamma_position: float | None
    days_to_expiration: int | None


@dataclass(frozen=True)
class OptionsFlowSignal:
    """Deterministic options-flow signal."""

    seeker: str
    signal: str
    value: float | int | str | None
    report_hint: str


class UnusualOptionsActivitySeeker:
    def generate(self, observation: OptionsFlowObservation) -> OptionsFlowSignal:
        if observation.option_volume is None or observation.average_option_volume in (None, 0):
            return OptionsFlowSignal("unusual_options_activity", "options_activity_unknown", None, "information_gap")
        ratio = observation.option_volume / observation.average_option_volume
        signal = "unusual_options_activity" if ratio >= 2 else "normal_options_activity"
        return OptionsFlowSignal("unusual_options_activity", signal, ratio, "institutional_activity" if ratio >= 2 else "opportunity")


class LargeOrderSeeker:
    def generate(self, observation: OptionsFlowObservation) -> OptionsFlowSignal:
        if observation.largest_order_notional is None:
            return OptionsFlowSignal("large_order", "large_order_unknown", None, "information_gap")
        signal = "large_order_detected" if observation.largest_order_notional >= 1_000_000 else "no_large_order"
        return OptionsFlowSignal("large_order", signal, observation.largest_order_notional, "institutional_activity" if signal == "large_order_detected" else "opportunity")


class GammaExposureSeeker:
    def generate(self, observation: OptionsFlowObservation) -> OptionsFlowSignal:
        if observation.gamma_exposure is None:
            return OptionsFlowSignal("gamma_exposure", "gamma_exposure_unknown", None, "information_gap")
        signal = "negative_gamma_threat" if observation.gamma_exposure < -500_000 else "gamma_exposure_contained"
        return OptionsFlowSignal("gamma_exposure", signal, observation.gamma_exposure, "threat" if signal.startswith("negative") else "opportunity")


class DeltaExposureSeeker:
    def generate(self, observation: OptionsFlowObservation) -> OptionsFlowSignal:
        if observation.delta_exposure is None:
            return OptionsFlowSignal("delta_exposure", "delta_exposure_unknown", None, "information_gap")
        signal = "large_delta_imbalance" if abs(observation.delta_exposure) >= 750_000 else "delta_exposure_balanced"
        return OptionsFlowSignal("delta_exposure", signal, observation.delta_exposure, "institutional_activity" if signal.startswith("large") else "opportunity")


class OpenInterestSeeker:
    def generate(self, observation: OptionsFlowObservation) -> OptionsFlowSignal:
        if observation.open_interest is None or observation.open_interest_change is None:
            return OptionsFlowSignal("open_interest", "open_interest_unknown", None, "information_gap")
        signal = "open_interest_build" if observation.open_interest_change > 0 else "open_interest_decline"
        return OptionsFlowSignal("open_interest", signal, observation.open_interest_change, "institutional_activity" if signal.endswith("build") else "threat")


class ImpliedVolatilitySeeker:
    def generate(self, observation: OptionsFlowObservation) -> OptionsFlowSignal:
        if observation.implied_volatility is None or observation.historical_volatility is None:
            return OptionsFlowSignal("implied_volatility", "volatility_unknown", None, "information_gap")
        premium = observation.implied_volatility - observation.historical_volatility
        signal = "iv_premium_elevated" if premium >= 0.15 else "iv_premium_normal"
        return OptionsFlowSignal("implied_volatility", signal, premium, "threat" if signal.endswith("elevated") else "opportunity")


class VolatilitySurfaceSeeker:
    def generate(self, observation: OptionsFlowObservation) -> OptionsFlowSignal:
        if observation.surface_skew is None:
            return OptionsFlowSignal("volatility_surface", "volatility_surface_unknown", None, "information_gap")
        signal = "surface_skew_extreme" if abs(observation.surface_skew) >= 0.25 else "surface_skew_orderly"
        return OptionsFlowSignal("volatility_surface", signal, observation.surface_skew, "threat" if signal.endswith("extreme") else "opportunity")


class DealerPositioningSeeker:
    def generate(self, observation: OptionsFlowObservation) -> OptionsFlowSignal:
        if observation.dealer_gamma_position is None:
            return OptionsFlowSignal("dealer_positioning", "dealer_positioning_unknown", None, "information_gap")
        signal = "dealer_short_gamma" if observation.dealer_gamma_position < 0 else "dealer_long_gamma"
        return OptionsFlowSignal("dealer_positioning", signal, observation.dealer_gamma_position, "threat" if signal.endswith("short_gamma") else "opportunity")


class ExpirationSeeker:
    def generate(self, observation: OptionsFlowObservation) -> OptionsFlowSignal:
        if observation.days_to_expiration is None:
            return OptionsFlowSignal("expiration", "expiration_unknown", None, "information_gap")
        signal = "near_expiration_pressure" if observation.days_to_expiration <= 5 else "expiration_distant"
        return OptionsFlowSignal("expiration", signal, observation.days_to_expiration, "threat" if signal.startswith("near") else "opportunity")


class OptionsFlowScreener:
    """Combines options-flow seekers without trade recommendation."""

    def __init__(self) -> None:
        self.seekers = (
            UnusualOptionsActivitySeeker(),
            LargeOrderSeeker(),
            GammaExposureSeeker(),
            DeltaExposureSeeker(),
            OpenInterestSeeker(),
            ImpliedVolatilitySeeker(),
            VolatilitySurfaceSeeker(),
            DealerPositioningSeeker(),
            ExpirationSeeker(),
        )

    def monitor(self, observation: OptionsFlowObservation) -> tuple[OptionsFlowSignal, ...]:
        return tuple(seeker.generate(observation) for seeker in self.seekers)


class OptionsFlowOfficeChief:
    """Office Chief for deterministic Options Flow Office."""

    def __init__(self, screener: OptionsFlowScreener | None = None) -> None:
        self.screener = screener or OptionsFlowScreener()

    def review(self, observation: OptionsFlowObservation) -> tuple[OptionsFlowSignal, ...]:
        return self.screener.monitor(observation)


class OptionsFlowOffice:
    """Options Flow Office integrated with Seeker Department."""

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
        self.office = self.department.offices[OPTIONS_FLOW_OFFICE_ID]
        self.chief = OptionsFlowOfficeChief()
        self.last_signals: tuple[OptionsFlowSignal, ...] = ()

    def ingest(self, observation: OptionsFlowObservation) -> tuple[OptionsFlowSignal, ...]:
        self.last_signals = self.chief.review(observation)
        return self.last_signals

    def generate_cor(
        self,
        observation: OptionsFlowObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "opportunity")
        return self._generate_report("COR", "options_candidate_unanalysed", "Options Flow Candidate Opportunity Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_institutional_activity_report(
        self,
        observation: OptionsFlowObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "institutional_activity")
        return self._generate_report("IAR", "institutional_activity_identified", "Institutional Activity Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_threat_report(
        self,
        observation: OptionsFlowObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "threat")
        return self._generate_report("OTR", "options_threat_identified", "Options Flow Threat Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_information_gap_report(
        self,
        observation: OptionsFlowObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "information_gap")
        return self._generate_report("IGR", "options_information_gap", "Options Flow Information Gap Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def route_report(self, report: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_cor(OPTIONS_FLOW_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> OfficeInstrumentPanel:
        return self.office.instrument_panel()

    def _generate_report(
        self,
        contract_type: str,
        report_status: str,
        human_summary: str,
        signals: tuple[OptionsFlowSignal, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        created = utc_timestamp()
        payload = {
            "office_id": OPTIONS_FLOW_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "report_status": report_status,
            "options_flow_signals": [signal.__dict__ for signal in signals],
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
