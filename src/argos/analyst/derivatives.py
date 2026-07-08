"""Analyst-side Derivatives Analysis Office."""

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

from .department import AnalystDepartment
from .offices import ANALYST_GROUP_ID, AnalystOfficeInstrumentPanel


DERIVATIVES_ANALYSIS_OFFICE_ID = "ANALYST-OFFICE-005"


@dataclass(frozen=True)
class DerivativesReasoningObservation:
    """Input observation for deterministic derivatives reasoning."""

    implied_volatility: float
    historical_volatility: float
    options_volume_ratio: float
    dealer_gamma_position: float
    gamma_exposure: float
    delta_exposure: float
    skew: float
    open_interest_change: float
    days_to_expiration: int
    institutional_notional: float


@dataclass(frozen=True)
class DerivativesReasoningGraph:
    """Mandatory reasoning graph for each derivatives conclusion."""

    conclusion_id: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str, str], ...]
    competing_hypotheses: tuple[str, ...]


@dataclass(frozen=True)
class ProbabilityLandscape:
    """Deterministic scenario landscape for derivatives outcomes."""

    landscape_id: str
    scenarios: tuple[dict[str, float | str], ...]


class DerivativesVolatilityAnalyst:
    def analyze(self, observation: DerivativesReasoningObservation) -> dict[str, float | str]:
        premium = observation.implied_volatility - observation.historical_volatility
        return {"volatility_state": "elevated_iv_premium" if premium >= 0.15 else "normal_iv_premium", "iv_premium": round(premium, 4)}


class DerivativesOptionsFlowAnalyst:
    def analyze(self, observation: DerivativesReasoningObservation) -> dict[str, float | str]:
        return {
            "options_flow": "unusual_options_activity" if observation.options_volume_ratio >= 2 else "normal_options_activity",
            "volume_ratio": round(observation.options_volume_ratio, 4),
        }


class DealerPositioningAnalyst:
    def analyze(self, observation: DerivativesReasoningObservation) -> dict[str, float | str]:
        return {
            "dealer_positioning": "dealer_short_gamma" if observation.dealer_gamma_position < 0 else "dealer_long_gamma",
            "dealer_gamma_position": round(observation.dealer_gamma_position, 4),
        }


class GammaAnalyst:
    def analyze(self, observation: DerivativesReasoningObservation) -> dict[str, float | str]:
        return {"gamma_risk": "elevated_gamma_risk" if observation.gamma_exposure < -500000 else "contained_gamma_risk", "gamma_exposure": round(observation.gamma_exposure, 4)}


class DeltaAnalyst:
    def analyze(self, observation: DerivativesReasoningObservation) -> dict[str, float | str]:
        return {"delta_state": "delta_imbalance" if abs(observation.delta_exposure) >= 750000 else "delta_balanced", "delta_exposure": round(observation.delta_exposure, 4)}


class SkewAnalyst:
    def analyze(self, observation: DerivativesReasoningObservation) -> dict[str, float | str]:
        return {"skew_state": "skew_extreme" if abs(observation.skew) >= 0.25 else "skew_orderly", "skew": round(observation.skew, 4)}


class OpenInterestAnalyst:
    def analyze(self, observation: DerivativesReasoningObservation) -> dict[str, float | str]:
        return {"open_interest": "open_interest_build" if observation.open_interest_change > 0 else "open_interest_decline", "change": round(observation.open_interest_change, 4)}


class ExpirationAnalyst:
    def analyze(self, observation: DerivativesReasoningObservation) -> dict[str, int | str]:
        return {"expiration_state": "near_expiration" if observation.days_to_expiration <= 5 else "distant_expiration", "days_to_expiration": observation.days_to_expiration}


class InstitutionalPositioningAnalyst:
    def analyze(self, observation: DerivativesReasoningObservation) -> dict[str, float | str]:
        return {
            "institutional_positioning": "institutional_flow_material" if observation.institutional_notional >= 1000000 else "institutional_flow_normal",
            "institutional_notional": round(observation.institutional_notional, 4),
        }


class DerivativesAnalysisOfficeChief:
    """Office Chief for deterministic derivatives reasoning."""

    def __init__(self) -> None:
        self.volatility = DerivativesVolatilityAnalyst()
        self.options_flow = DerivativesOptionsFlowAnalyst()
        self.dealer_positioning = DealerPositioningAnalyst()
        self.gamma = GammaAnalyst()
        self.delta = DeltaAnalyst()
        self.skew = SkewAnalyst()
        self.open_interest = OpenInterestAnalyst()
        self.expiration = ExpirationAnalyst()
        self.institutional_positioning = InstitutionalPositioningAnalyst()

    def analyze(self, observation: DerivativesReasoningObservation) -> dict[str, object]:
        components = {
            "volatility": self.volatility.analyze(observation),
            "options_flow": self.options_flow.analyze(observation),
            "dealer_positioning": self.dealer_positioning.analyze(observation),
            "gamma": self.gamma.analyze(observation),
            "delta": self.delta.analyze(observation),
            "skew": self.skew.analyze(observation),
            "open_interest": self.open_interest.analyze(observation),
            "expiration": self.expiration.analyze(observation),
            "institutional_positioning": self.institutional_positioning.analyze(observation),
        }
        landscape = self.probability_landscape(components)
        components["competing_theses"] = self.competing_theses(components)
        components["probability_landscape"] = landscape.__dict__
        components["derivatives_conclusion"] = self.conclusion(landscape)
        return components

    def competing_theses(self, components: dict[str, object]) -> tuple[dict[str, object], ...]:
        return (
            {
                "thesis_id": "DTA-001",
                "name": "volatility_expansion",
                "supporting_factors": self._volatility_expansion_factors(components),
            },
            {
                "thesis_id": "DTA-002",
                "name": "institutional_positioning",
                "supporting_factors": self._institutional_positioning_factors(components),
            },
            {
                "thesis_id": "DTA-003",
                "name": "volatility_normalization",
                "supporting_factors": self._normalization_factors(components),
            },
        )

    def probability_landscape(self, components: dict[str, object]) -> ProbabilityLandscape:
        risk_flags = sum(
            (
                components["volatility"]["volatility_state"] == "elevated_iv_premium",
                components["dealer_positioning"]["dealer_positioning"] == "dealer_short_gamma",
                components["gamma"]["gamma_risk"] == "elevated_gamma_risk",
                components["delta"]["delta_state"] == "delta_imbalance",
                components["skew"]["skew_state"] == "skew_extreme",
                components["expiration"]["expiration_state"] == "near_expiration",
            )
        )
        institutional_flags = sum(
            (
                components["options_flow"]["options_flow"] == "unusual_options_activity",
                components["open_interest"]["open_interest"] == "open_interest_build",
                components["institutional_positioning"]["institutional_positioning"] == "institutional_flow_material",
            )
        )
        raw = {
            "volatility_expansion": 0.25 + risk_flags * 0.08,
            "institutional_positioning": 0.2 + institutional_flags * 0.1,
            "volatility_normalization": max(0.1, 0.55 - risk_flags * 0.05),
        }
        total = sum(raw.values())
        scenarios = tuple({"scenario": name, "probability": round(score / total, 4)} for name, score in raw.items())
        return ProbabilityLandscape("DPL-001", scenarios)

    def reasoning_graphs(self, reasoning: dict[str, object], source_report_ids: tuple[str, ...]) -> tuple[DerivativesReasoningGraph, ...]:
        thesis_ids = tuple(thesis["thesis_id"] for thesis in reasoning["competing_theses"])
        return (
            DerivativesReasoningGraph(
                "DERIVATIVES-CONCLUSION-001",
                (
                    "claim:derivatives_probability_landscape",
                    "evidence:volatility",
                    "evidence:options_flow",
                    "evidence:dealer_positioning",
                    "evidence:gamma",
                    "evidence:delta",
                    "evidence:skew",
                    "source:" + ",".join(source_report_ids),
                ),
                (
                    ("evidence:volatility", "claim:derivatives_probability_landscape", "supports"),
                    ("evidence:options_flow", "claim:derivatives_probability_landscape", "qualifies"),
                    ("evidence:dealer_positioning", "claim:derivatives_probability_landscape", "supports"),
                    ("evidence:skew", "claim:derivatives_probability_landscape", "challenges"),
                ),
                thesis_ids,
            ),
        )

    def alternative_explanations(self, reasoning: dict[str, object]) -> tuple[str, ...]:
        return (
            "Options activity may reflect hedging rather than directional conviction.",
            "Dealer positioning may change before expiration and alter the probability landscape.",
            "Volatility premium may normalize without confirming institutional accumulation.",
        )

    def conclusion(self, landscape: ProbabilityLandscape) -> dict[str, float | str]:
        top = max(landscape.scenarios, key=lambda scenario: scenario["probability"])
        return {"primary_scenario": str(top["scenario"]), "probability": float(top["probability"])}

    def _volatility_expansion_factors(self, components: dict[str, object]) -> tuple[str, ...]:
        factors: list[str] = []
        if components["volatility"]["volatility_state"] == "elevated_iv_premium":
            factors.append("elevated_iv_premium")
        if components["dealer_positioning"]["dealer_positioning"] == "dealer_short_gamma":
            factors.append("dealer_short_gamma")
        if components["gamma"]["gamma_risk"] == "elevated_gamma_risk":
            factors.append("elevated_gamma_risk")
        if components["expiration"]["expiration_state"] == "near_expiration":
            factors.append("near_expiration")
        return tuple(factors)

    def _institutional_positioning_factors(self, components: dict[str, object]) -> tuple[str, ...]:
        factors: list[str] = []
        if components["options_flow"]["options_flow"] == "unusual_options_activity":
            factors.append("unusual_options_activity")
        if components["open_interest"]["open_interest"] == "open_interest_build":
            factors.append("open_interest_build")
        if components["institutional_positioning"]["institutional_positioning"] == "institutional_flow_material":
            factors.append("institutional_flow_material")
        return tuple(factors)

    def _normalization_factors(self, components: dict[str, object]) -> tuple[str, ...]:
        factors: list[str] = []
        if components["dealer_positioning"]["dealer_positioning"] == "dealer_long_gamma":
            factors.append("dealer_long_gamma")
        if components["skew"]["skew_state"] == "skew_orderly":
            factors.append("orderly_skew")
        if components["expiration"]["expiration_state"] == "distant_expiration":
            factors.append("distant_expiration")
        return tuple(factors or ("normalization_thesis_preserved_for_competing_explanation",))


class DerivativesAnalysisOffice:
    """Analyst-side Derivatives Analysis Office integrated with Analyst Department."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = AnalystDepartment(
            configuration_service,
            persistence_repository,
            audit_service,
            prompt_repository,
        )
        self.office = self.department.offices[DERIVATIVES_ANALYSIS_OFFICE_ID]
        self.chief = DerivativesAnalysisOfficeChief()

    def generate_derivatives_aar(
        self,
        observation: DerivativesReasoningObservation,
        source_reports: tuple[OperationalContract, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        reasoning = self.chief.analyze(observation)
        source_ids = tuple(report.contract_id for report in source_reports)
        graphs = self.chief.reasoning_graphs(reasoning, source_ids)
        alternatives = self.chief.alternative_explanations(reasoning)
        created = utc_timestamp()
        payload = {
            "office_id": DERIVATIVES_ANALYSIS_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "derivatives_analytical_assessment",
            "source_report_ids": list(source_ids),
            "derivatives_reasoning": reasoning,
            "derivatives_reasoning_graphs": [graph.__dict__ for graph in graphs],
            "competing_thesis_analysis": list(reasoning["competing_theses"]),
            "probability_landscape": reasoning["probability_landscape"],
            "alternative_explanations": list(alternatives),
            "seeker_intelligence_modified": False,
            "risk_office_override": False,
        }
        signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        report = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type="AAR",
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            parent_contract_ids=source_ids,
            produced_by_staff_id=self.office.record.configuration.staff_id,
            produced_by_group_id=ANALYST_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary="Derivatives Analytical Assessment Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report

    def route_aar(self, aar: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_aar(DERIVATIVES_ANALYSIS_OFFICE_ID, aar, target_inbox)

    def instrument_panel(self) -> AnalystOfficeInstrumentPanel:
        return self.office.instrument_panel()
