"""Cryptocurrency Office scaffolding and deterministic blockchain monitoring."""

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


CRYPTOCURRENCY_OFFICE_ID = "SEEKER-OFFICE-006"


@dataclass(frozen=True)
class CryptocurrencyObservation:
    """Input observation for deterministic cryptocurrency monitoring."""

    price_change: float | None
    trend_strength: float | None
    transaction_count_change: float | None
    active_address_change: float | None
    stablecoin_net_flow: float | None
    exchange_net_flow: float | None
    whale_transaction_count: int | None
    institutional_flow: float | None
    defi_total_value_locked_change: float | None
    nft_volume_change: float | None
    on_chain_risk_score: float | None


@dataclass(frozen=True)
class CryptocurrencySignal:
    """Deterministic cryptocurrency signal."""

    seeker: str
    signal: str
    value: float | int | str | None
    report_hint: str


class PriceStructureSeeker:
    def generate(self, observation: CryptocurrencyObservation) -> CryptocurrencySignal:
        if observation.price_change is None or observation.trend_strength is None:
            return CryptocurrencySignal("price_structure", "price_structure_unknown", None, "information_gap")
        signal = "price_structure_positive" if observation.price_change > 0 and observation.trend_strength >= 0.5 else "price_structure_weak"
        return CryptocurrencySignal("price_structure", signal, observation.price_change, "opportunity" if signal.endswith("positive") else "threat")


class BlockchainActivitySeeker:
    def generate(self, observation: CryptocurrencyObservation) -> CryptocurrencySignal:
        if observation.transaction_count_change is None or observation.active_address_change is None:
            return CryptocurrencySignal("blockchain_activity", "blockchain_activity_unknown", None, "information_gap")
        composite = (observation.transaction_count_change + observation.active_address_change) / 2
        signal = "blockchain_activity_expanding" if composite > 0 else "blockchain_activity_contracting"
        return CryptocurrencySignal("blockchain_activity", signal, composite, "blockchain_activity" if composite > 0 else "threat")


class StablecoinFlowSeeker:
    def generate(self, observation: CryptocurrencyObservation) -> CryptocurrencySignal:
        if observation.stablecoin_net_flow is None:
            return CryptocurrencySignal("stablecoin_flow", "stablecoin_flow_unknown", None, "information_gap")
        signal = "stablecoin_inflow" if observation.stablecoin_net_flow > 0 else "stablecoin_outflow"
        return CryptocurrencySignal("stablecoin_flow", signal, observation.stablecoin_net_flow, "blockchain_activity" if observation.stablecoin_net_flow > 0 else "threat")


class ExchangeFlowSeeker:
    def generate(self, observation: CryptocurrencyObservation) -> CryptocurrencySignal:
        if observation.exchange_net_flow is None:
            return CryptocurrencySignal("exchange_flow", "exchange_flow_unknown", None, "information_gap")
        signal = "exchange_outflow_accumulation" if observation.exchange_net_flow < 0 else "exchange_inflow_distribution"
        return CryptocurrencySignal("exchange_flow", signal, observation.exchange_net_flow, "blockchain_activity" if observation.exchange_net_flow < 0 else "threat")


class WalletActivitySeeker:
    def generate(self, observation: CryptocurrencyObservation) -> CryptocurrencySignal:
        if observation.whale_transaction_count is None:
            return CryptocurrencySignal("wallet_activity", "wallet_activity_unknown", None, "information_gap")
        signal = "whale_activity_detected" if observation.whale_transaction_count >= 10 else "wallet_activity_normal"
        return CryptocurrencySignal("wallet_activity", signal, observation.whale_transaction_count, "blockchain_activity" if signal.startswith("whale") else "opportunity")


class InstitutionalCryptoSeeker:
    def generate(self, observation: CryptocurrencyObservation) -> CryptocurrencySignal:
        if observation.institutional_flow is None:
            return CryptocurrencySignal("institutional_crypto", "institutional_crypto_unknown", None, "information_gap")
        signal = "institutional_crypto_inflow" if observation.institutional_flow > 0 else "institutional_crypto_outflow"
        return CryptocurrencySignal("institutional_crypto", signal, observation.institutional_flow, "blockchain_activity" if observation.institutional_flow > 0 else "threat")


class DeFiSeeker:
    def generate(self, observation: CryptocurrencyObservation) -> CryptocurrencySignal:
        if observation.defi_total_value_locked_change is None:
            return CryptocurrencySignal("defi", "defi_activity_unknown", None, "information_gap")
        signal = "defi_tvl_expanding" if observation.defi_total_value_locked_change > 0 else "defi_tvl_contracting"
        return CryptocurrencySignal("defi", signal, observation.defi_total_value_locked_change, "opportunity" if signal.endswith("expanding") else "threat")


class NFTMarketSeeker:
    def generate(self, observation: CryptocurrencyObservation) -> CryptocurrencySignal:
        if observation.nft_volume_change is None:
            return CryptocurrencySignal("nft_market", "nft_market_unknown", None, "information_gap")
        signal = "nft_activity_expanding" if observation.nft_volume_change > 0 else "nft_activity_contracting"
        return CryptocurrencySignal("nft_market", signal, observation.nft_volume_change, "opportunity" if signal.endswith("expanding") else "threat")


class OnChainAnalyticsSeeker:
    def generate(self, observation: CryptocurrencyObservation) -> CryptocurrencySignal:
        if observation.on_chain_risk_score is None:
            return CryptocurrencySignal("on_chain_analytics", "on_chain_risk_unknown", None, "information_gap")
        signal = "on_chain_risk_elevated" if observation.on_chain_risk_score >= 0.7 else "on_chain_risk_contained"
        return CryptocurrencySignal("on_chain_analytics", signal, observation.on_chain_risk_score, "threat" if signal.endswith("elevated") else "opportunity")


class CryptocurrencyScreener:
    """Combines cryptocurrency seekers without trade recommendation."""

    def __init__(self) -> None:
        self.seekers = (
            PriceStructureSeeker(),
            BlockchainActivitySeeker(),
            StablecoinFlowSeeker(),
            ExchangeFlowSeeker(),
            WalletActivitySeeker(),
            InstitutionalCryptoSeeker(),
            DeFiSeeker(),
            NFTMarketSeeker(),
            OnChainAnalyticsSeeker(),
        )

    def monitor(self, observation: CryptocurrencyObservation) -> tuple[CryptocurrencySignal, ...]:
        return tuple(seeker.generate(observation) for seeker in self.seekers)


class CryptocurrencyOfficeChief:
    """Office Chief for deterministic Cryptocurrency Office."""

    def __init__(self, screener: CryptocurrencyScreener | None = None) -> None:
        self.screener = screener or CryptocurrencyScreener()

    def review(self, observation: CryptocurrencyObservation) -> tuple[CryptocurrencySignal, ...]:
        return self.screener.monitor(observation)


class CryptocurrencyOffice:
    """Cryptocurrency Office integrated with Seeker Department."""

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
        self.office = self.department.offices[CRYPTOCURRENCY_OFFICE_ID]
        self.chief = CryptocurrencyOfficeChief()
        self.last_signals: tuple[CryptocurrencySignal, ...] = ()

    def ingest(self, observation: CryptocurrencyObservation) -> tuple[CryptocurrencySignal, ...]:
        self.last_signals = self.chief.review(observation)
        return self.last_signals

    def generate_cor(
        self,
        observation: CryptocurrencyObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "opportunity")
        return self._generate_report("COR", "crypto_candidate_unanalysed", "Cryptocurrency Candidate Opportunity Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_blockchain_activity_report(
        self,
        observation: CryptocurrencyObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "blockchain_activity")
        return self._generate_report("CXR", "blockchain_activity_identified", "Blockchain Activity Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_threat_report(
        self,
        observation: CryptocurrencyObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "threat")
        return self._generate_report("CTR", "crypto_threat_identified", "Cryptocurrency Threat Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_information_gap_report(
        self,
        observation: CryptocurrencyObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        signals = tuple(signal for signal in self.ingest(observation) if signal.report_hint == "information_gap")
        return self._generate_report("IGR", "crypto_information_gap", "Cryptocurrency Information Gap Report.", signals, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def route_report(self, report: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_cor(CRYPTOCURRENCY_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> OfficeInstrumentPanel:
        return self.office.instrument_panel()

    def _generate_report(
        self,
        contract_type: str,
        report_status: str,
        human_summary: str,
        signals: tuple[CryptocurrencySignal, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        created = utc_timestamp()
        payload = {
            "office_id": CRYPTOCURRENCY_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "report_status": report_status,
            "cryptocurrency_signals": [signal.__dict__ for signal in signals],
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
