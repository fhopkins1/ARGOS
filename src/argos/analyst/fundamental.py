"""Analyst-side Fundamental Analysis Office."""

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


FUNDAMENTAL_ANALYSIS_OFFICE_ID = "ANALYST-OFFICE-003"


@dataclass(frozen=True)
class FundamentalBusinessObservation:
    """Input observation for deterministic business analysis."""

    revenue_growth: float
    gross_margin: float
    operating_margin: float
    return_on_invested_capital: float
    valuation_multiple: float
    industry_average_multiple: float
    reinvestment_rate: float
    management_quality_score: float
    accrual_ratio: float
    debt_to_equity: float
    interest_coverage: float
    free_cash_flow_margin: float
    industry_concentration_score: float
    moat_durability_score: float


@dataclass(frozen=True)
class FundamentalReasoningGraph:
    """Mandatory reasoning graph for each fundamental conclusion."""

    conclusion_id: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str, str], ...]
    contradictory_evidence: tuple[str, ...]


class FinancialStatementAnalyst:
    def analyze(self, observation: FundamentalBusinessObservation) -> dict[str, float | str]:
        score = (observation.revenue_growth + observation.gross_margin + observation.operating_margin) / 3
        return {"statement_quality": "strong" if score >= 0.15 else "weak", "score": round(score, 4)}


class ValuationAnalyst:
    def analyze(self, observation: FundamentalBusinessObservation) -> dict[str, float | str]:
        relative = observation.valuation_multiple / observation.industry_average_multiple if observation.industry_average_multiple else 0
        return {"valuation_state": "discount" if relative <= 0.9 else "premium" if relative >= 1.1 else "fair", "relative_multiple": round(relative, 4)}


class CompetitiveAdvantageAnalyst:
    def analyze(self, observation: FundamentalBusinessObservation) -> dict[str, float | str]:
        score = (observation.moat_durability_score + observation.return_on_invested_capital) / 2
        return {"moat": "durable" if score >= 0.45 else "limited", "score": round(score, 4)}


class CapitalAllocationAnalyst:
    def analyze(self, observation: FundamentalBusinessObservation) -> dict[str, float | str]:
        score = observation.reinvestment_rate * observation.return_on_invested_capital
        return {"capital_allocation": "productive" if score >= 0.05 else "unproven", "score": round(score, 4)}


class ManagementQualityAnalyst:
    def analyze(self, observation: FundamentalBusinessObservation) -> dict[str, float | str]:
        return {"management_quality": "high" if observation.management_quality_score >= 0.7 else "watch", "score": round(observation.management_quality_score, 4)}


class EarningsQualityAnalyst:
    def analyze(self, observation: FundamentalBusinessObservation) -> dict[str, float | str]:
        quality = "clean" if observation.accrual_ratio <= 0.1 else "accrual_risk"
        return {"earnings_quality": quality, "accrual_ratio": round(observation.accrual_ratio, 4)}


class BalanceSheetAnalyst:
    def analyze(self, observation: FundamentalBusinessObservation) -> dict[str, float | str]:
        resilient = observation.debt_to_equity <= 1 and observation.interest_coverage >= 4
        return {"balance_sheet": "resilient" if resilient else "leveraged", "debt_to_equity": round(observation.debt_to_equity, 4)}


class CashFlowAnalyst:
    def analyze(self, observation: FundamentalBusinessObservation) -> dict[str, float | str]:
        return {"cash_flow": "strong" if observation.free_cash_flow_margin >= 0.1 else "weak", "free_cash_flow_margin": round(observation.free_cash_flow_margin, 4)}


class IndustryStructureAnalyst:
    def analyze(self, observation: FundamentalBusinessObservation) -> dict[str, float | str]:
        return {"industry_structure": "favorable" if observation.industry_concentration_score >= 0.5 else "fragmented", "score": round(observation.industry_concentration_score, 4)}


class FundamentalAnalysisOfficeChief:
    """Office Chief for analyst-side Fundamental Analysis Office."""

    def __init__(self) -> None:
        self.financial_statement = FinancialStatementAnalyst()
        self.valuation = ValuationAnalyst()
        self.competitive_advantage = CompetitiveAdvantageAnalyst()
        self.capital_allocation = CapitalAllocationAnalyst()
        self.management_quality = ManagementQualityAnalyst()
        self.earnings_quality = EarningsQualityAnalyst()
        self.balance_sheet = BalanceSheetAnalyst()
        self.cash_flow = CashFlowAnalyst()
        self.industry_structure = IndustryStructureAnalyst()

    def analyze(self, observation: FundamentalBusinessObservation) -> dict[str, object]:
        components = {
            "financial_statement": self.financial_statement.analyze(observation),
            "valuation": self.valuation.analyze(observation),
            "competitive_advantage": self.competitive_advantage.analyze(observation),
            "capital_allocation": self.capital_allocation.analyze(observation),
            "management_quality": self.management_quality.analyze(observation),
            "earnings_quality": self.earnings_quality.analyze(observation),
            "balance_sheet": self.balance_sheet.analyze(observation),
            "cash_flow": self.cash_flow.analyze(observation),
            "industry_structure": self.industry_structure.analyze(observation),
        }
        components["business_quality_score"] = self.business_quality_score(components)
        components["economic_moat"] = self.economic_moat(components)
        components["fundamental_conclusion"] = self.conclusion(components)
        return components

    def business_quality_score(self, components: dict[str, object]) -> dict[str, float | str]:
        positives = sum(
            (
                components["financial_statement"]["statement_quality"] == "strong",
                components["competitive_advantage"]["moat"] == "durable",
                components["capital_allocation"]["capital_allocation"] == "productive",
                components["management_quality"]["management_quality"] == "high",
                components["earnings_quality"]["earnings_quality"] == "clean",
                components["balance_sheet"]["balance_sheet"] == "resilient",
                components["cash_flow"]["cash_flow"] == "strong",
                components["industry_structure"]["industry_structure"] == "favorable",
            )
        )
        score = positives / 8
        return {"score": round(score, 4), "grade": "high" if score >= 0.7 else "watch"}

    def economic_moat(self, components: dict[str, object]) -> dict[str, str]:
        durable = (
            components["competitive_advantage"]["moat"] == "durable"
            and components["industry_structure"]["industry_structure"] == "favorable"
            and components["capital_allocation"]["capital_allocation"] == "productive"
        )
        return {"moat_state": "durable_moat" if durable else "moat_unproven"}

    def conclusion(self, components: dict[str, object]) -> dict[str, object]:
        contradictory = tuple(
            key
            for key, value in components.items()
            if isinstance(value, dict)
            and any(item in value.values() for item in ("premium", "accrual_risk", "leveraged", "weak", "fragmented", "watch"))
        )
        return {
            "business_conclusion": "business_quality_confirmed" if components["business_quality_score"]["grade"] == "high" else "business_quality_unconfirmed",
            "contradictory_factors": contradictory,
        }

    def reasoning_graphs(self, reasoning: dict[str, object], source_report_ids: tuple[str, ...]) -> tuple[FundamentalReasoningGraph, ...]:
        contradictory = tuple(reasoning["fundamental_conclusion"]["contradictory_factors"])
        return (
            FundamentalReasoningGraph(
                "FUND-CONCLUSION-001",
                (
                    "claim:fundamental_business_quality",
                    "evidence:financial_statement",
                    "evidence:competitive_advantage",
                    "evidence:cash_flow",
                    "evidence:balance_sheet",
                    "source:" + ",".join(source_report_ids),
                ),
                (
                    ("evidence:financial_statement", "claim:fundamental_business_quality", "supports"),
                    ("evidence:competitive_advantage", "claim:fundamental_business_quality", "supports"),
                    ("evidence:cash_flow", "claim:fundamental_business_quality", "supports"),
                    ("evidence:balance_sheet", "claim:fundamental_business_quality", "qualifies"),
                ),
                contradictory,
            ),
        )

    def alternative_explanations(self, reasoning: dict[str, object]) -> tuple[str, ...]:
        contradictory = tuple(reasoning["fundamental_conclusion"]["contradictory_factors"])
        if contradictory:
            return ("Business quality may be offset by valuation, accounting, leverage, or industry risks.",)
        return ("Observed business strength may reflect cyclical conditions rather than durable advantage.",)


class FundamentalAnalysisOffice:
    """Analyst-side Fundamental Analysis Office integrated with Analyst Department."""

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
        self.office = self.department.offices[FUNDAMENTAL_ANALYSIS_OFFICE_ID]
        self.chief = FundamentalAnalysisOfficeChief()

    def generate_fundamental_aar(
        self,
        observation: FundamentalBusinessObservation,
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
            "office_id": FUNDAMENTAL_ANALYSIS_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "fundamental_analytical_assessment",
            "source_report_ids": list(source_ids),
            "fundamental_reasoning": reasoning,
            "fundamental_reasoning_graphs": [graph.__dict__ for graph in graphs],
            "business_quality_score": reasoning["business_quality_score"],
            "economic_moat": reasoning["economic_moat"],
            "alternative_business_explanations": list(alternatives),
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
            human_summary="Fundamental Analytical Assessment Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report

    def route_aar(self, aar: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_aar(FUNDAMENTAL_ANALYSIS_OFFICE_ID, aar, target_inbox)

    def instrument_panel(self) -> AnalystOfficeInstrumentPanel:
        return self.office.instrument_panel()
