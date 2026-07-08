"""Analyst-side Macroeconomic Analysis Office."""

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


MACROECONOMIC_ANALYSIS_OFFICE_ID = "ANALYST-OFFICE-004"


@dataclass(frozen=True)
class MacroeconomicReasoningObservation:
    """Input observation for deterministic macroeconomic reasoning."""

    inflation_rate: float
    policy_rate: float
    fiscal_impulse: float
    unemployment_rate: float
    gdp_growth: float
    yield_curve_spread: float
    currency_change: float
    commodity_change: float
    global_growth: float


@dataclass(frozen=True)
class MacroeconomicReasoningGraph:
    """Mandatory reasoning graph for each macro conclusion."""

    conclusion_id: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str, str], ...]
    competing_hypotheses: tuple[str, ...]


class InflationAnalyst:
    def analyze(self, observation: MacroeconomicReasoningObservation) -> dict[str, float | str]:
        return {"inflation_state": "elevated" if observation.inflation_rate >= 4 else "contained", "value": round(observation.inflation_rate, 4)}


class MonetaryPolicyAnalyst:
    def analyze(self, observation: MacroeconomicReasoningObservation) -> dict[str, float | str]:
        restrictive = observation.policy_rate >= 5
        return {"monetary_policy": "restrictive" if restrictive else "accommodative", "policy_rate": round(observation.policy_rate, 4)}


class FiscalPolicyAnalyst:
    def analyze(self, observation: MacroeconomicReasoningObservation) -> dict[str, float | str]:
        return {"fiscal_policy": "supportive" if observation.fiscal_impulse > 0 else "restrictive", "fiscal_impulse": round(observation.fiscal_impulse, 4)}


class LaborMarketAnalyst:
    def analyze(self, observation: MacroeconomicReasoningObservation) -> dict[str, float | str]:
        return {"labor_market": "tight" if observation.unemployment_rate <= 4.5 else "softening", "unemployment_rate": round(observation.unemployment_rate, 4)}


class BusinessCycleAnalyst:
    def analyze(self, observation: MacroeconomicReasoningObservation) -> dict[str, float | str]:
        return {"business_cycle": "expansion" if observation.gdp_growth > 1 else "slowdown", "gdp_growth": round(observation.gdp_growth, 4)}


class YieldCurveAnalyst:
    def analyze(self, observation: MacroeconomicReasoningObservation) -> dict[str, float | str]:
        return {"yield_curve": "inverted" if observation.yield_curve_spread < 0 else "normal", "spread": round(observation.yield_curve_spread, 4)}


class CurrencyAnalyst:
    def analyze(self, observation: MacroeconomicReasoningObservation) -> dict[str, float | str]:
        return {"currency": "volatile" if abs(observation.currency_change) >= 3 else "stable", "change": round(observation.currency_change, 4)}


class CommodityAnalyst:
    def analyze(self, observation: MacroeconomicReasoningObservation) -> dict[str, float | str]:
        return {"commodity": "shock" if abs(observation.commodity_change) >= 10 else "orderly", "change": round(observation.commodity_change, 4)}


class GlobalEconomyAnalyst:
    def analyze(self, observation: MacroeconomicReasoningObservation) -> dict[str, float | str]:
        return {"global_economy": "supportive" if observation.global_growth >= 2 else "fragile", "global_growth": round(observation.global_growth, 4)}


class MacroeconomicAnalysisOfficeChief:
    """Office Chief for deterministic macroeconomic reasoning."""

    def __init__(self) -> None:
        self.inflation = InflationAnalyst()
        self.monetary_policy = MonetaryPolicyAnalyst()
        self.fiscal_policy = FiscalPolicyAnalyst()
        self.labor_market = LaborMarketAnalyst()
        self.business_cycle = BusinessCycleAnalyst()
        self.yield_curve = YieldCurveAnalyst()
        self.currency = CurrencyAnalyst()
        self.commodity = CommodityAnalyst()
        self.global_economy = GlobalEconomyAnalyst()

    def analyze(self, observation: MacroeconomicReasoningObservation) -> dict[str, object]:
        components = {
            "inflation": self.inflation.analyze(observation),
            "monetary_policy": self.monetary_policy.analyze(observation),
            "fiscal_policy": self.fiscal_policy.analyze(observation),
            "labor_market": self.labor_market.analyze(observation),
            "business_cycle": self.business_cycle.analyze(observation),
            "yield_curve": self.yield_curve.analyze(observation),
            "currency": self.currency.analyze(observation),
            "commodity": self.commodity.analyze(observation),
            "global_economy": self.global_economy.analyze(observation),
        }
        components["economic_regime"] = self.classify_regime(components)
        components["competing_theses"] = self.competing_theses(components)
        components["confidence_calibration"] = self.confidence_calibration(components)
        return components

    def classify_regime(self, components: dict[str, object]) -> dict[str, str]:
        if components["inflation"]["inflation_state"] == "elevated" and components["monetary_policy"]["monetary_policy"] == "restrictive":
            regime = "inflationary_tightening"
        elif components["business_cycle"]["business_cycle"] == "slowdown" or components["yield_curve"]["yield_curve"] == "inverted":
            regime = "late_cycle_slowdown"
        else:
            regime = "expansionary_growth"
        return {"regime": regime}

    def competing_theses(self, components: dict[str, object]) -> tuple[dict[str, object], ...]:
        primary = components["economic_regime"]["regime"]
        return (
            {"thesis_id": "CTA-001", "name": primary, "supporting_factors": self._supporting_factors(components, primary)},
            {"thesis_id": "CTA-002", "name": "soft_landing", "supporting_factors": ("supportive_fiscal_policy", "tight_labor_market")},
            {"thesis_id": "CTA-003", "name": "policy_error", "supporting_factors": ("restrictive_policy", "yield_curve_inversion")},
        )

    def confidence_calibration(self, components: dict[str, object]) -> dict[str, float | str]:
        risk_flags = sum(
            (
                components["inflation"]["inflation_state"] == "elevated",
                components["monetary_policy"]["monetary_policy"] == "restrictive",
                components["yield_curve"]["yield_curve"] == "inverted",
                components["commodity"]["commodity"] == "shock",
                components["global_economy"]["global_economy"] == "fragile",
            )
        )
        confidence = round(max(0.35, 0.85 - risk_flags * 0.08), 4)
        return {"confidence": confidence, "method": "risk_flag_penalty"}

    def reasoning_graphs(self, reasoning: dict[str, object], source_report_ids: tuple[str, ...]) -> tuple[MacroeconomicReasoningGraph, ...]:
        thesis_ids = tuple(thesis["thesis_id"] for thesis in reasoning["competing_theses"])
        return (
            MacroeconomicReasoningGraph(
                "MACRO-CONCLUSION-001",
                (
                    "claim:economic_regime",
                    "evidence:inflation",
                    "evidence:monetary_policy",
                    "evidence:business_cycle",
                    "evidence:yield_curve",
                    "source:" + ",".join(source_report_ids),
                ),
                (
                    ("evidence:inflation", "claim:economic_regime", "supports"),
                    ("evidence:monetary_policy", "claim:economic_regime", "supports"),
                    ("evidence:business_cycle", "claim:economic_regime", "qualifies"),
                    ("evidence:yield_curve", "claim:economic_regime", "challenges"),
                ),
                thesis_ids,
            ),
        )

    def alternative_explanations(self, reasoning: dict[str, object]) -> tuple[str, ...]:
        return (
            "Macro data may represent a temporary policy lag rather than a durable regime.",
            "Competing thesis may explain the same evidence under different timing assumptions.",
        )

    def _supporting_factors(self, components: dict[str, object], regime: str) -> tuple[str, ...]:
        if regime == "inflationary_tightening":
            return ("elevated_inflation", "restrictive_monetary_policy")
        if regime == "late_cycle_slowdown":
            return ("yield_curve_inversion", "business_cycle_slowdown")
        return ("contained_inflation", "global_growth_support")


class MacroeconomicAnalysisOffice:
    """Analyst-side Macroeconomic Analysis Office integrated with Analyst Department."""

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
        self.office = self.department.offices[MACROECONOMIC_ANALYSIS_OFFICE_ID]
        self.chief = MacroeconomicAnalysisOfficeChief()

    def generate_macroeconomic_aar(
        self,
        observation: MacroeconomicReasoningObservation,
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
            "office_id": MACROECONOMIC_ANALYSIS_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "macroeconomic_analytical_assessment",
            "source_report_ids": list(source_ids),
            "macroeconomic_reasoning": reasoning,
            "macroeconomic_reasoning_graphs": [graph.__dict__ for graph in graphs],
            "economic_regime": reasoning["economic_regime"],
            "competing_thesis_analysis": list(reasoning["competing_theses"]),
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
            human_summary="Macroeconomic Analytical Assessment Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report

    def route_aar(self, aar: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_aar(MACROECONOMIC_ANALYSIS_OFFICE_ID, aar, target_inbox)

    def instrument_panel(self) -> AnalystOfficeInstrumentPanel:
        return self.office.instrument_panel()
