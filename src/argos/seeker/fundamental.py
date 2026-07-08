"""Fundamental Research Office scaffolding and deterministic screening."""

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


FUNDAMENTAL_RESEARCH_OFFICE_ID = "SEEKER-OFFICE-002"


@dataclass(frozen=True)
class FundamentalObservation:
    """Input observation for deterministic fundamental screening."""

    revenue_growth: float
    earnings_growth: float
    pe_ratio: float
    debt_to_equity: float
    current_ratio: float
    free_cash_flow_positive: bool
    insider_activity_score: float
    institutional_ownership_change: float
    analyst_revision_score: float


@dataclass(frozen=True)
class FundamentalSignal:
    """Deterministic fundamental signal."""

    seeker: str
    signal: str
    value: float | bool | str


class FinancialStatementSeeker:
    def generate(self, observation: FundamentalObservation) -> FundamentalSignal:
        quality = "expanding_revenue" if observation.revenue_growth > 0 else "contracting_revenue"
        return FundamentalSignal("financial_statement", quality, observation.revenue_growth)


class EarningsSeeker:
    def generate(self, observation: FundamentalObservation) -> FundamentalSignal:
        signal = "earnings_growth" if observation.earnings_growth > 0 else "earnings_decline"
        return FundamentalSignal("earnings", signal, observation.earnings_growth)


class ValuationSeeker:
    def generate(self, observation: FundamentalObservation) -> FundamentalSignal:
        signal = "reasonable_valuation" if observation.pe_ratio <= 25 else "extended_valuation"
        return FundamentalSignal("valuation", signal, observation.pe_ratio)


class GrowthSeeker:
    def generate(self, observation: FundamentalObservation) -> FundamentalSignal:
        blended = (observation.revenue_growth + observation.earnings_growth) / 2
        signal = "growth_profile_positive" if blended > 0 else "growth_profile_weak"
        return FundamentalSignal("growth", signal, blended)


class BalanceSheetSeeker:
    def generate(self, observation: FundamentalObservation) -> FundamentalSignal:
        signal = "balance_sheet_resilient" if observation.debt_to_equity <= 1 and observation.current_ratio >= 1 else "balance_sheet_watch"
        return FundamentalSignal("balance_sheet", signal, observation.debt_to_equity)


class CashFlowSeeker:
    def generate(self, observation: FundamentalObservation) -> FundamentalSignal:
        signal = "positive_free_cash_flow" if observation.free_cash_flow_positive else "negative_free_cash_flow"
        return FundamentalSignal("cash_flow", signal, observation.free_cash_flow_positive)


class InsiderActivitySeeker:
    def generate(self, observation: FundamentalObservation) -> FundamentalSignal:
        signal = "insider_supportive" if observation.insider_activity_score > 0 else "insider_neutral_or_negative"
        return FundamentalSignal("insider_activity", signal, observation.insider_activity_score)


class InstitutionalOwnershipSeeker:
    def generate(self, observation: FundamentalObservation) -> FundamentalSignal:
        signal = "institutional_accumulation" if observation.institutional_ownership_change > 0 else "institutional_distribution"
        return FundamentalSignal("institutional_ownership", signal, observation.institutional_ownership_change)


class AnalystRevisionSeeker:
    def generate(self, observation: FundamentalObservation) -> FundamentalSignal:
        signal = "positive_revisions" if observation.analyst_revision_score > 0 else "negative_or_neutral_revisions"
        return FundamentalSignal("analyst_revision", signal, observation.analyst_revision_score)


class FundamentalScreener:
    """Combines fundamental seekers without trade recommendation."""

    def __init__(self) -> None:
        self.seekers = (
            FinancialStatementSeeker(),
            EarningsSeeker(),
            ValuationSeeker(),
            GrowthSeeker(),
            BalanceSheetSeeker(),
            CashFlowSeeker(),
            InsiderActivitySeeker(),
            InstitutionalOwnershipSeeker(),
            AnalystRevisionSeeker(),
        )

    def screen(self, observation: FundamentalObservation) -> tuple[FundamentalSignal, ...]:
        return tuple(seeker.generate(observation) for seeker in self.seekers)


class FundamentalOfficeChief:
    """Office Chief for deterministic Fundamental Research Office."""

    def __init__(self, screener: FundamentalScreener | None = None) -> None:
        self.screener = screener or FundamentalScreener()

    def review(self, observation: FundamentalObservation) -> tuple[FundamentalSignal, ...]:
        return self.screener.screen(observation)


class FundamentalResearchOffice:
    """Fundamental Research Office integrated with Seeker Department."""

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
        self.office = self.department.offices[FUNDAMENTAL_RESEARCH_OFFICE_ID]
        self.chief = FundamentalOfficeChief()
        self.last_signals: tuple[FundamentalSignal, ...] = ()

    def generate_signals(self, observation: FundamentalObservation) -> tuple[FundamentalSignal, ...]:
        self.last_signals = self.chief.review(observation)
        return self.last_signals

    def generate_cor(
        self,
        observation: FundamentalObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ):
        signals = self.generate_signals(observation)
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(
            prompt_id,
            case_file_id,
            trade_cycle_id,
        )
        created = utc_timestamp()
        payload = {
            "office_id": FUNDAMENTAL_RESEARCH_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "candidate_status": "fundamental_candidate_unanalysed",
            "fundamental_signals": [signal.__dict__ for signal in signals],
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
            human_summary="Fundamental Candidate Opportunity Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=(),
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, cor.contract_id, cor.to_dict())
        self.office.reports_generated += 1
        return cor

    def route_cor(self, cor, target_inbox: IncomingMailbox):
        return self.department.route_cor(FUNDAMENTAL_RESEARCH_OFFICE_ID, cor, target_inbox)

    def instrument_panel(self) -> OfficeInstrumentPanel:
        return self.office.instrument_panel()

