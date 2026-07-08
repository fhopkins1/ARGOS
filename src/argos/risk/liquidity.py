"""Liquidity Risk Office."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from argos.analyst import OrganizationalBeliefState
from argos.foundation.audit import AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService

from .department import RiskDepartment
from .offices import RISK_GROUP_ID, RiskOfficeInstrumentPanel


LIQUIDITY_RISK_OFFICE_ID = "RISK-OFFICE-003"


@dataclass(frozen=True)
class LiquidityObservation:
    """Liquidity data for execution feasibility review."""

    asset: str
    order_size: float
    average_daily_volume: float
    bid_ask_spread_bps: float
    top_of_book_depth: float
    order_book_depth: float
    execution_window_minutes: int
    volatility_score: float
    market_participation_limit: float
    historical_liquidity_events: tuple[str, ...]


@dataclass(frozen=True)
class LiquidityRiskModel:
    """Liquidity Risk Model."""

    asset: str
    participation_rate: float
    depth_coverage: float
    estimated_slippage_bps: float
    spread_cost_bps: float
    market_impact_bps: float
    exit_feasibility: str
    liquidity_risk_score: float


@dataclass(frozen=True)
class ExecutionFeasibilityReport:
    """Execution feasibility report."""

    report_id: str
    feasible: bool
    feasibility_state: str
    required_execution_slices: int
    estimated_minutes_required: int


@dataclass(frozen=True)
class LiquidityStressReport:
    """Liquidity stress report."""

    report_id: str
    stress_tests: tuple[dict[str, float | str], ...]
    historical_replay_events: tuple[str, ...]


@dataclass(frozen=True)
class LiquidityReadinessScore:
    """Liquidity Readiness Score."""

    score: float
    category: str


@dataclass(frozen=True)
class LiquidityRiskInstrumentPanel:
    """Liquidity Risk Office instrument panel display."""

    base_panel: RiskOfficeInstrumentPanel
    open_liquidity_reviews: int
    estimated_slippage_bps: float
    market_impact_bps: float
    stress_tests: int
    historical_events: int


class MarketDepthAnalyst:
    def analyze(self, observation: LiquidityObservation) -> dict[str, float | str]:
        coverage = observation.top_of_book_depth / observation.order_size if observation.order_size else 0
        state = "depth_sufficient" if coverage >= 1 else "depth_insufficient"
        return {"depth_coverage": round(coverage, 4), "depth_state": state}


class SlippageAnalyst:
    def estimate(self, observation: LiquidityObservation, depth_coverage: float) -> dict[str, float]:
        depth_penalty = max(0.0, 1 - depth_coverage) * 35
        participation = observation.order_size / observation.average_daily_volume if observation.average_daily_volume else 1
        slippage = observation.bid_ask_spread_bps * 0.5 + depth_penalty + participation * 120 + observation.volatility_score * 20
        return {"estimated_slippage_bps": round(slippage, 4)}


class ExecutionAnalyst:
    def analyze(self, observation: LiquidityObservation) -> dict[str, int | float | str]:
        max_slice = observation.average_daily_volume * observation.market_participation_limit * max(1, observation.execution_window_minutes / 390)
        slices = max(1, int((observation.order_size + max_slice - 1) // max_slice)) if max_slice else 999
        minutes_required = slices * max(1, observation.execution_window_minutes)
        state = "execution_feasible" if slices <= 3 else "execution_constrained"
        return {"max_slice": round(max_slice, 4), "required_execution_slices": slices, "estimated_minutes_required": minutes_required, "execution_state": state}


class SpreadAnalyst:
    def analyze(self, observation: LiquidityObservation) -> dict[str, float | str]:
        state = "spread_wide" if observation.bid_ask_spread_bps >= 25 else "spread_normal"
        return {"spread_cost_bps": round(observation.bid_ask_spread_bps, 4), "spread_state": state}


class OrderBookAnalyst:
    def analyze(self, observation: LiquidityObservation) -> dict[str, float | str]:
        coverage = observation.order_book_depth / observation.order_size if observation.order_size else 0
        return {"order_book_coverage": round(coverage, 4), "order_book_state": "order_book_thin" if coverage < 2 else "order_book_resilient"}


class ExitStrategyAnalyst:
    def analyze(self, execution_state: str, order_book_state: str) -> dict[str, str]:
        if execution_state == "execution_feasible" and order_book_state == "order_book_resilient":
            state = "exit_feasible"
        elif execution_state == "execution_constrained":
            state = "exit_constrained"
        else:
            state = "exit_requires_staging"
        return {"exit_feasibility": state}


class LiquidityStressAnalyst:
    def stress(self, observation: LiquidityObservation, slippage_bps: float) -> LiquidityStressReport:
        scenarios = (
            {"scenario": "Market Depth Halves", "stressed_slippage_bps": round(slippage_bps * 1.35, 4)},
            {"scenario": "Spread Triples", "stressed_slippage_bps": round(slippage_bps + observation.bid_ask_spread_bps * 2, 4)},
            {"scenario": "ADV Contracts", "stressed_slippage_bps": round(slippage_bps + (observation.order_size / max(1, observation.average_daily_volume * 0.5)) * 80, 4)},
            {"scenario": "Historical Liquidity Replay", "stressed_slippage_bps": round(slippage_bps + len(observation.historical_liquidity_events) * 12, 4)},
        )
        return LiquidityStressReport("LSR-001", scenarios, observation.historical_liquidity_events)


class MarketImpactAnalyst:
    def estimate(self, observation: LiquidityObservation) -> dict[str, float]:
        participation = observation.order_size / observation.average_daily_volume if observation.average_daily_volume else 1
        impact = participation * 160 + observation.volatility_score * 25 + max(0, observation.bid_ask_spread_bps - 10) * 0.4
        return {"market_impact_bps": round(impact, 4)}


class LiquidityRiskOfficeChief:
    """Office Chief for liquidity risk review."""

    def __init__(self) -> None:
        self.market_depth = MarketDepthAnalyst()
        self.slippage = SlippageAnalyst()
        self.execution = ExecutionAnalyst()
        self.spread = SpreadAnalyst()
        self.order_book = OrderBookAnalyst()
        self.exit_strategy = ExitStrategyAnalyst()
        self.liquidity_stress = LiquidityStressAnalyst()
        self.market_impact = MarketImpactAnalyst()

    def evaluate(self, belief_state: OrganizationalBeliefState, observation: LiquidityObservation) -> dict[str, object]:
        if not isinstance(belief_state, OrganizationalBeliefState):
            raise TypeError("Liquidity Risk Office requires an OrganizationalBeliefState")
        depth = self.market_depth.analyze(observation)
        slippage = self.slippage.estimate(observation, float(depth["depth_coverage"]))
        execution = self.execution.analyze(observation)
        spread = self.spread.analyze(observation)
        order_book = self.order_book.analyze(observation)
        exit_strategy = self.exit_strategy.analyze(str(execution["execution_state"]), str(order_book["order_book_state"]))
        impact = self.market_impact.estimate(observation)
        stress = self.liquidity_stress.stress(observation, float(slippage["estimated_slippage_bps"]))
        participation = observation.order_size / observation.average_daily_volume if observation.average_daily_volume else 1
        risk_score = self.risk_score(belief_state, slippage["estimated_slippage_bps"], impact["market_impact_bps"], execution["required_execution_slices"], len(observation.historical_liquidity_events))
        model = LiquidityRiskModel(
            observation.asset,
            round(participation, 4),
            float(depth["depth_coverage"]),
            float(slippage["estimated_slippage_bps"]),
            float(spread["spread_cost_bps"]),
            float(impact["market_impact_bps"]),
            str(exit_strategy["exit_feasibility"]),
            risk_score,
        )
        feasibility = ExecutionFeasibilityReport(
            "EFR-001",
            execution["execution_state"] == "execution_feasible" and risk_score < 0.65,
            str(execution["execution_state"]),
            int(execution["required_execution_slices"]),
            int(execution["estimated_minutes_required"]),
        )
        readiness = self.readiness_score(risk_score, model.exit_feasibility)
        return {
            "market_depth": depth,
            "slippage": slippage,
            "execution": execution,
            "spread": spread,
            "order_book": order_book,
            "exit_strategy": exit_strategy,
            "market_impact": impact,
            "liquidity_risk_model": model.__dict__,
            "execution_feasibility_report": feasibility.__dict__,
            "liquidity_stress_report": stress.__dict__,
            "liquidity_readiness_score": readiness.__dict__,
        }

    def risk_score(self, belief_state: OrganizationalBeliefState, slippage_bps: float, impact_bps: float, slices: int, historical_event_count: int) -> float:
        raw = (slippage_bps / 200) * 0.25 + (impact_bps / 200) * 0.25 + min(1.0, slices / 6) * 0.2 + historical_event_count * 0.06 + (1 - belief_state.organizational_confidence) * 0.18
        return round(max(0.0, min(1.0, raw)), 4)

    def readiness_score(self, risk_score: float, exit_feasibility: str) -> LiquidityReadinessScore:
        score = 100 - risk_score * 70
        if exit_feasibility == "exit_constrained":
            score -= 12
        elif exit_feasibility == "exit_requires_staging":
            score -= 6
        score = round(max(0.0, min(100.0, score)), 2)
        if score >= 80:
            category = "Approved"
        elif score >= 65:
            category = "Conditionally Approved"
        elif score >= 50:
            category = "Needs Additional Analysis"
        elif score >= 35:
            category = "Needs Additional Evidence"
        else:
            category = "Reject"
        return LiquidityReadinessScore(score, category)


class LiquidityRiskOffice:
    """Liquidity Risk Office integrated with the Risk Department framework."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = RiskDepartment(configuration_service, persistence_repository, audit_service, prompt_repository)
        self.office = self.department.offices[LIQUIDITY_RISK_OFFICE_ID]
        self.chief = LiquidityRiskOfficeChief()
        self._latest_review: dict[str, object] | None = None

    def generate_liquidity_risk_report(
        self,
        belief_state: OrganizationalBeliefState,
        observation: LiquidityObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        """Generate a Liquidity Risk Report as a RAR."""
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        review = self.chief.evaluate(belief_state, observation)
        created = utc_timestamp()
        payload = {
            "risk_id": f"LIQ-{document_sequence:06d}",
            "office_id": LIQUIDITY_RISK_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "liquidity_risk_assessment",
            "case_file_id": case_file_id,
            "trade_cycle_id": trade_cycle_id,
            "asset": observation.asset,
            "liquidity_risk_model": review["liquidity_risk_model"],
            "execution_feasibility_report": review["execution_feasibility_report"],
            "liquidity_stress_report": review["liquidity_stress_report"],
            "liquidity_readiness_score": review["liquidity_readiness_score"],
            "organizational_belief_state_id": belief_state.state_id,
            "organizational_belief_state_modified": False,
            "historical_liquidity_events_ignored": False,
            "investment_recommendation": None,
            "execution_instruction": None,
            "command_decision": None,
            "timestamp": created,
        }
        signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        report = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type="RAR",
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            parent_contract_ids=belief_state.source_report_ids,
            produced_by_staff_id=self.office.record.configuration.staff_id,
            produced_by_group_id=RISK_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary="Liquidity Risk Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=belief_state.source_report_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.department.audit_service.record_document_creation(report)
        self.office.reports_generated += 1
        self._latest_review = review
        return report

    def route_report(self, report: OperationalContract, target_inbox: IncomingMailbox):
        """Route a Liquidity Risk Report through Courier Framework."""
        return self.department.route_rar(LIQUIDITY_RISK_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> LiquidityRiskInstrumentPanel:
        """Return the Liquidity Risk Office instrument panel."""
        base = self.office.instrument_panel()
        if not self._latest_review:
            return LiquidityRiskInstrumentPanel(base, len(self.office.queue), 0.0, 0.0, 0, 0)
        model = self._latest_review["liquidity_risk_model"]
        stress = self._latest_review["liquidity_stress_report"]
        return LiquidityRiskInstrumentPanel(
            base,
            len(self.office.queue),
            float(model["estimated_slippage_bps"]),
            float(model["market_impact_bps"]),
            len(stress["stress_tests"]),
            len(stress["historical_replay_events"]),
        )
