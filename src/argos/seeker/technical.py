"""Technical Analysis Office scaffolding and deterministic signals."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from argos.foundation.audit import AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository
from argos.foundation.persistence import ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService

from .department import SeekerDepartment
from .offices import OfficeInstrumentPanel, SEEKER_GROUP_ID


TECHNICAL_ANALYSIS_OFFICE_ID = "SEEKER-OFFICE-001"


@dataclass(frozen=True)
class MarketObservation:
    """Input observation for deterministic technical calculations."""

    close: float
    high: float
    low: float
    volume: float


@dataclass(frozen=True)
class TechnicalSignal:
    """Deterministic technical signal."""

    seeker: str
    signal: str
    value: float | str


class TrendSeeker:
    def generate(self, observations: tuple[MarketObservation, ...]) -> TechnicalSignal:
        start = observations[0].close
        end = observations[-1].close
        return TechnicalSignal("trend", "uptrend" if end > start else "downtrend" if end < start else "flat", end - start)


class MomentumSeeker:
    def generate(self, observations: tuple[MarketObservation, ...]) -> TechnicalSignal:
        momentum = observations[-1].close - observations[-2].close
        return TechnicalSignal("momentum", "positive" if momentum > 0 else "negative" if momentum < 0 else "neutral", momentum)


class VolatilitySeeker:
    def generate(self, observations: tuple[MarketObservation, ...]) -> TechnicalSignal:
        ranges = [item.high - item.low for item in observations]
        average_range = sum(ranges) / len(ranges)
        return TechnicalSignal("volatility", "elevated" if average_range > 2 else "normal", average_range)


class MarketStructureSeeker:
    def generate(self, observations: tuple[MarketObservation, ...]) -> TechnicalSignal:
        higher_high = observations[-1].high > observations[-2].high
        higher_low = observations[-1].low > observations[-2].low
        structure = "higher_high_higher_low" if higher_high and higher_low else "mixed_structure"
        return TechnicalSignal("market_structure", structure, structure)


class PatternRecognitionSeeker:
    def generate(self, observations: tuple[MarketObservation, ...]) -> TechnicalSignal:
        last = observations[-1]
        body = abs(last.close - ((last.high + last.low) / 2))
        pattern = "wide_range_close" if body > 1 else "no_pattern"
        return TechnicalSignal("pattern", pattern, pattern)


class VolumeSeeker:
    def generate(self, observations: tuple[MarketObservation, ...]) -> TechnicalSignal:
        average_volume = sum(item.volume for item in observations[:-1]) / max(1, len(observations) - 1)
        signal = "volume_expansion" if observations[-1].volume > average_volume else "normal_volume"
        return TechnicalSignal("volume", signal, observations[-1].volume)


class TechnicalScreener:
    """Combines technical seekers without trade recommendation."""

    def __init__(self) -> None:
        self.seekers = (
            TrendSeeker(),
            MomentumSeeker(),
            VolatilitySeeker(),
            MarketStructureSeeker(),
            PatternRecognitionSeeker(),
            VolumeSeeker(),
        )

    def screen(self, observations: tuple[MarketObservation, ...]) -> tuple[TechnicalSignal, ...]:
        if len(observations) < 2:
            raise ValueError("technical screening requires at least two observations")
        return tuple(seeker.generate(observations) for seeker in self.seekers)


class TechnicalOfficeChief:
    """Office Chief for deterministic Technical Analysis Office."""

    def __init__(self, screener: TechnicalScreener | None = None) -> None:
        self.screener = screener or TechnicalScreener()

    def review(self, observations: tuple[MarketObservation, ...]) -> tuple[TechnicalSignal, ...]:
        return self.screener.screen(observations)


class TechnicalAnalysisOffice:
    """Technical Analysis Office integrated with Seeker Department."""

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
        self.office = self.department.offices[TECHNICAL_ANALYSIS_OFFICE_ID]
        self.chief = TechnicalOfficeChief()
        self.last_signals: tuple[TechnicalSignal, ...] = ()

    def generate_signals(self, observations: tuple[MarketObservation, ...]) -> tuple[TechnicalSignal, ...]:
        self.last_signals = self.chief.review(observations)
        return self.last_signals

    def generate_cor(
        self,
        observations: tuple[MarketObservation, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ):
        signals = self.generate_signals(observations)
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(
            prompt_id,
            case_file_id,
            trade_cycle_id,
        )
        created = utc_timestamp()
        payload = {
            "office_id": TECHNICAL_ANALYSIS_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "candidate_status": "technical_candidate_unanalysed",
            "technical_signals": [signal.__dict__ for signal in signals],
        }
        signature_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        cor = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type="COR",
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
            human_summary="Technical Candidate Opportunity Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=(),
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, cor.contract_id, cor.to_dict())
        self.office.reports_generated += 1
        return cor

    def route_cor(self, cor, target_inbox: IncomingMailbox):
        return self.department.route_cor(TECHNICAL_ANALYSIS_OFFICE_ID, cor, target_inbox)

    def instrument_panel(self) -> OfficeInstrumentPanel:
        return self.office.instrument_panel()
