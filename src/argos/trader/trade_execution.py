"""Trade Execution Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .offices import TRADER_GROUP_ID
from .order_management import ExecutionOrderRequest, OrderManagementOffice


TRADE_EXECUTION_OFFICE_ID = "TRADER-OFFICE-001"
TRADE_EXECUTION_STAFF_ID = "STF-061"


class ExecutionExceptionSeverity(str, Enum):
    """Execution exception severity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ExecutionAuthorization:
    """Approved execution authorization input."""

    cdr_id: str
    risk_certification_id: str
    approved_quantity: float
    instrument_id: str
    direction: str
    expected_price: float
    max_slippage_percent: float
    execution_window_seconds: int
    strategy_id: str
    position_id: str
    account_id: str
    venue: str


@dataclass(frozen=True)
class MarketConditionSnapshot:
    """Recorded market conditions for deterministic execution."""

    bid: float
    ask: float
    last_price: float
    available_liquidity: float
    volatility_score: float
    spread: float
    market_open: bool


@dataclass(frozen=True)
class ExecutionPlan:
    """Deterministic execution plan."""

    plan_id: str
    approved_strategy: str
    selected_methodology: str
    selected_venue: str
    constraints: tuple[str, ...]
    order_slices: tuple[dict[str, object], ...]
    timeline: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class ExecutionFill:
    """Single execution fill."""

    fill_id: str
    order_id: str
    fill_price: float
    fill_quantity: float
    fill_timestamp_utc: str
    execution_venue: str
    execution_latency_ms: int
    bid_ask_spread: float
    midpoint_deviation: float
    execution_sequence: int


@dataclass(frozen=True)
class ExecutionProgress:
    """Execution monitoring state."""

    submitted_quantity: float
    acknowledged_quantity: float
    working_quantity: float
    filled_quantity: float
    remaining_quantity: float
    cancelled_quantity: float
    rejected_quantity: float
    elapsed_execution_time_ms: int
    execution_latency_ms: int


@dataclass(frozen=True)
class FillQualityProfile:
    """Complete fill quality profile."""

    average_fill_price: float
    total_fill_quantity: float
    venue_count: int
    max_latency_ms: int
    fills: tuple[ExecutionFill, ...]


@dataclass(frozen=True)
class SlippageAnalysis:
    """Deterministic slippage analysis."""

    expected_execution_price: float
    actual_execution_price: float
    absolute_slippage: float
    percentage_slippage: float
    slippage_attribution: str
    cumulative_slippage: float


@dataclass(frozen=True)
class TransactionCostAnalysis:
    """Deterministic transaction cost analysis."""

    commissions: float
    regulatory_fees: float
    exchange_fees: float
    clearing_fees: float
    spread_costs: float
    implicit_market_impact: float
    total_transaction_cost: float


@dataclass(frozen=True)
class ImplementationShortfallAnalysis:
    """Implementation shortfall analysis."""

    decision_price: float
    arrival_price: float
    average_execution_price: float
    opportunity_cost: float
    delay_cost: float
    execution_cost: float
    realized_implementation_shortfall: float


@dataclass(frozen=True)
class MarketImpactEvaluation:
    """Market impact evaluation."""

    price_displacement: float
    order_book_movement: float
    liquidity_depletion: float
    execution_footprint: float
    participation_rate: float
    recovery_behavior: str


@dataclass(frozen=True)
class ExecutionException:
    """Execution anomaly classification."""

    exception_id: str
    classification: str
    severity: ExecutionExceptionSeverity
    probable_cause: str
    recommended_response: str


@dataclass(frozen=True)
class ExecutionRecoveryAction:
    """Deterministic recovery action."""

    action_id: str
    action: str
    preserves_executive_intent: bool
    requires_approval: bool


@dataclass(frozen=True)
class TradeAuthorizationVerificationRecord:
    """Trade authorization verification record."""

    record_id: str
    cdr_id: str
    risk_certification_id: str
    authorization_valid: bool
    risk_certification_verified: bool


@dataclass(frozen=True)
class ExecutionStrategyRecord:
    """Execution strategy selection record."""

    record_id: str
    strategy_id: str
    selected_strategy: str
    policy_basis: str


@dataclass(frozen=True)
class ExecutionMethodSelectionRecord:
    """Execution method selection record."""

    record_id: str
    selected_method: str
    market_condition_basis: str


@dataclass(frozen=True)
class VenueSelectionRecord:
    """Deterministic venue selection record."""

    record_id: str
    selected_venue: str
    venue_basis: str


@dataclass(frozen=True)
class OrderSlicingRecord:
    """Order slicing record preserving Executive traceability."""

    record_id: str
    source_cdr_id: str
    total_quantity: float
    slices: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class ExecutionTimelineRecord:
    """Execution timeline record."""

    record_id: str
    timeline: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionConstraintValidationRecord:
    """Execution constraint validation record."""

    record_id: str
    constraints_checked: tuple[str, ...]
    valid: bool
    violations: tuple[str, ...]


@dataclass(frozen=True)
class DeterministicDecisionTrace:
    """Deterministic decision trace."""

    trace_id: str
    inputs: tuple[str, ...]
    decisions: tuple[str, ...]


@dataclass(frozen=True)
class OrganizationalPolicyComplianceRecord:
    """Organizational policy compliance record."""

    record_id: str
    compliant: bool
    policies: tuple[str, ...]


@dataclass(frozen=True)
class ExecutiveNotificationRecord:
    """Executive notification record."""

    notification_id: str
    required: bool
    reason: str
    commander_notified: bool


@dataclass(frozen=True)
class ExecutionPerformanceDataset:
    """Historian execution performance dataset."""

    dataset_id: str
    metrics: dict[str, object]


@dataclass(frozen=True)
class ExecutionEventArchive:
    """Historian execution event archive."""

    archive_id: str
    event_ids: tuple[str, ...]


class ExecutionAuthorizationVerifier:
    """Verify execution authorization and Risk certification references."""

    def verify(self, authorization: ExecutionAuthorization) -> None:
        if not authorization.cdr_id.startswith("DOC-"):
            raise ValueError("execution requires a CDR document reference")
        if not authorization.risk_certification_id.startswith("DOC-"):
            raise ValueError("execution requires a Risk certification document reference")
        if authorization.approved_quantity <= 0:
            raise ValueError("approved quantity must be positive")
        if authorization.max_slippage_percent < 0:
            raise ValueError("maximum slippage percent must be non-negative")

    def record(self, authorization: ExecutionAuthorization) -> TradeAuthorizationVerificationRecord:
        self.verify(authorization)
        return TradeAuthorizationVerificationRecord("TAVR-053", authorization.cdr_id, authorization.risk_certification_id, True, True)


class ExecutionStrategySelector:
    """Select deterministic execution methodology."""

    def select(self, authorization: ExecutionAuthorization, market: MarketConditionSnapshot) -> str:
        if not market.market_open:
            return "pause_until_market_open"
        liquidity_ratio = market.available_liquidity / authorization.approved_quantity
        if market.volatility_score >= 0.7:
            return "volatility_sensitive_sliced_limit"
        if liquidity_ratio < 2:
            return "liquidity_constrained_sliced_limit"
        return "standard_limit_execution"


class ExecutionTimingEngine:
    """Determine deterministic execution timeline."""

    def timeline(self, authorization: ExecutionAuthorization, methodology: str) -> tuple[str, ...]:
        if methodology == "pause_until_market_open":
            return ("await_market_open", "revalidate_constraints", "submit_to_order_management")
        if authorization.execution_window_seconds <= 300:
            return ("immediate_order_package", "submit_to_order_management")
        return ("stage_parent_order", "submit_child_orders", "monitor_progress")


class VenueSelectionEngine:
    """Select execution venue deterministically."""

    def select(self, authorization: ExecutionAuthorization, market: MarketConditionSnapshot) -> VenueSelectionRecord:
        venue = authorization.venue if market.market_open else "NO_OPEN_VENUE"
        basis = "executive_venue_constraint_and_market_open_state" if market.market_open else "market_closed"
        return VenueSelectionRecord("VSR-053", venue, basis)


class OrderSlicingEngine:
    """Slice orders deterministically while preserving CDR traceability."""

    def slice(self, authorization: ExecutionAuthorization, market: MarketConditionSnapshot) -> OrderSlicingRecord:
        if authorization.approved_quantity <= 100 or market.available_liquidity >= authorization.approved_quantity * 5:
            quantities = (authorization.approved_quantity,)
        else:
            slice_count = 4 if market.volatility_score >= 0.7 else 2
            base = round(authorization.approved_quantity / slice_count, 4)
            quantities = tuple(base for _ in range(slice_count - 1)) + (round(authorization.approved_quantity - base * (slice_count - 1), 4),)
        slices = tuple(
            {
                "slice_id": f"SLICE-{index:03d}",
                "source_cdr_id": authorization.cdr_id,
                "quantity": quantity,
                "sequence": index,
            }
            for index, quantity in enumerate(quantities, start=1)
        )
        return OrderSlicingRecord("OSR-053", authorization.cdr_id, authorization.approved_quantity, slices)


class ExecutionConstraintValidationEngine:
    """Validate execution constraints continuously."""

    def validate(self, authorization: ExecutionAuthorization, market: MarketConditionSnapshot) -> ExecutionConstraintValidationRecord:
        violations = []
        if not market.market_open:
            violations.append("market_closed")
        if market.spread > authorization.expected_price * 0.01:
            violations.append("spread_constraint_violation")
        return ExecutionConstraintValidationRecord(
            "ECVR-053",
            (
                "market_open",
                "spread_within_threshold",
                "risk_certification_present",
                "executive_authorization_present",
            ),
            not violations,
            tuple(violations),
        )


class ExecutionPlanEngine:
    """Create execution plans."""

    def __init__(self) -> None:
        self.authorization = ExecutionAuthorizationVerifier()
        self.strategy = ExecutionStrategySelector()
        self.timing = ExecutionTimingEngine()
        self.venue = VenueSelectionEngine()
        self.slicing = OrderSlicingEngine()
        self.constraints = ExecutionConstraintValidationEngine()

    def plan(self, authorization: ExecutionAuthorization, market: MarketConditionSnapshot) -> ExecutionPlan:
        self.authorization.verify(authorization)
        methodology = self.strategy.select(authorization, market)
        venue = self.venue.select(authorization, market)
        slices = self.slicing.slice(authorization, market)
        constraints = (
            f"max_slippage_percent:{authorization.max_slippage_percent}",
            f"execution_window_seconds:{authorization.execution_window_seconds}",
            f"risk_certification:{authorization.risk_certification_id}",
            "preserve_executive_intent",
        )
        return ExecutionPlan(
            "TEP-053B",
            authorization.strategy_id,
            methodology,
            venue.selected_venue,
            constraints,
            slices.slices,
            self.timing.timeline(authorization, methodology),
            "Methodology selected deterministically from recorded liquidity, volatility, and market-open state.",
        )

    def records(self, authorization: ExecutionAuthorization, market: MarketConditionSnapshot, plan: ExecutionPlan) -> dict[str, object]:
        authorization_record = self.authorization.record(authorization)
        strategy_record = ExecutionStrategyRecord("ESR-053", authorization.strategy_id, plan.selected_methodology, "documented_liquidity_volatility_market_open_policy")
        method_record = ExecutionMethodSelectionRecord("EMSR-053", plan.selected_methodology, "market_conditions_and_executive_constraints")
        venue_record = self.venue.select(authorization, market)
        slicing_record = self.slicing.slice(authorization, market)
        timeline_record = ExecutionTimelineRecord("ETR-053", plan.timeline)
        constraint_record = self.constraints.validate(authorization, market)
        decision_trace = DeterministicDecisionTrace(
            "DDT-053",
            (authorization.cdr_id, authorization.risk_certification_id, "market_condition_snapshot", "organizational_execution_policy"),
            (plan.selected_methodology, plan.selected_venue, tuple(item["slice_id"] for item in slicing_record.slices)),
        )
        policy = OrganizationalPolicyComplianceRecord(
            "OPCR-053",
            constraint_record.valid,
            ("separation_of_duties", "no_direct_broker_communication", "preserve_executive_intent", "risk_certification_required"),
        )
        return {
            "trade_authorization_verification_record": authorization_record,
            "execution_strategy_record": strategy_record,
            "execution_method_selection_record": method_record,
            "venue_selection_record": venue_record,
            "order_slicing_record": slicing_record,
            "execution_timeline_record": timeline_record,
            "execution_constraint_validation_record": constraint_record,
            "deterministic_decision_trace": decision_trace,
            "organizational_policy_compliance_record": policy,
        }


class OrderSubmissionEngine:
    """Submit executable order packages to Order Management Office only."""

    def submit(
        self,
        plan: ExecutionPlan,
        authorization: ExecutionAuthorization,
        order_management_office: OrderManagementOffice,
        case_file_id: str,
        trade_cycle_id: str,
        order_sequence: int,
        document_sequence: int,
    ) -> OperationalContract:
        if plan.selected_methodology == "pause_until_market_open":
            raise ValueError("order cannot be submitted while market is closed")
        request = ExecutionOrderRequest(
            execution_plan_id=plan.plan_id,
            instrument_id=authorization.instrument_id,
            quantity=authorization.approved_quantity,
            direction=authorization.direction,
            execution_method="limit",
            venue=authorization.venue,
            account_id=authorization.account_id,
            strategy_id=authorization.strategy_id,
            executive_authorization_id=authorization.cdr_id,
            risk_reference_id=authorization.risk_certification_id,
            position_id=authorization.position_id,
            order_priority=1,
            broker_destination="ORDER_MANAGEMENT_SELECTED_BROKER",
            exchange_destination=authorization.venue,
            execution_constraints=plan.constraints,
        )
        return order_management_office.create_order(request, case_file_id, trade_cycle_id, order_sequence, document_sequence)


class ExecutionMonitoringEngine:
    """Monitor deterministic execution progress."""

    def progress(self, submitted_quantity: float, fills: tuple[ExecutionFill, ...], cancelled_quantity: float = 0.0, rejected_quantity: float = 0.0) -> ExecutionProgress:
        filled = round(sum(fill.fill_quantity for fill in fills), 4)
        remaining = round(max(0.0, submitted_quantity - filled - cancelled_quantity - rejected_quantity), 4)
        max_latency = max((fill.execution_latency_ms for fill in fills), default=0)
        return ExecutionProgress(submitted_quantity, submitted_quantity, remaining, filled, remaining, cancelled_quantity, rejected_quantity, max_latency, max_latency)


class FillAnalysisEngine:
    """Evaluate fills independently and as a profile."""

    def profile(self, fills: tuple[ExecutionFill, ...]) -> FillQualityProfile:
        total_quantity = round(sum(fill.fill_quantity for fill in fills), 4)
        average_price = round(sum(fill.fill_price * fill.fill_quantity for fill in fills) / total_quantity, 4) if total_quantity else 0.0
        venues = {fill.execution_venue for fill in fills}
        max_latency = max((fill.execution_latency_ms for fill in fills), default=0)
        return FillQualityProfile(average_price, total_quantity, len(venues), max_latency, fills)


class SlippageAnalysisEngine:
    """Calculate deterministic execution slippage."""

    def analyze(self, expected_price: float, actual_price: float, quantity: float, market: MarketConditionSnapshot, latency_ms: int) -> SlippageAnalysis:
        absolute = round(actual_price - expected_price, 4)
        percentage = round((absolute / expected_price) * 100, 4) if expected_price else 0.0
        attribution = "spread_expansion" if market.spread > expected_price * 0.002 else "execution_delay" if latency_ms > 1000 else "market_movement"
        return SlippageAnalysis(expected_price, actual_price, absolute, percentage, attribution, round(absolute * quantity, 4))


class TransactionCostAnalysisEngine:
    """Calculate transaction costs independently from investment performance."""

    def analyze(self, quantity: float, average_price: float, market: MarketConditionSnapshot) -> TransactionCostAnalysis:
        notional = quantity * average_price
        commissions = round(quantity * 0.005, 4)
        regulatory = round(notional * 0.00001, 4)
        exchange = round(quantity * 0.001, 4)
        clearing = round(quantity * 0.0005, 4)
        spread_costs = round(market.spread * quantity / 2, 4)
        impact = round(notional * min(0.01, quantity / max(market.available_liquidity, 1) * 0.001), 4)
        total = round(commissions + regulatory + exchange + clearing + spread_costs + impact, 4)
        return TransactionCostAnalysis(commissions, regulatory, exchange, clearing, spread_costs, impact, total)


class ImplementationShortfallEngine:
    """Evaluate intended versus realized execution."""

    def analyze(self, decision_price: float, arrival_price: float, average_execution_price: float, quantity: float, costs: TransactionCostAnalysis) -> ImplementationShortfallAnalysis:
        opportunity = round((arrival_price - decision_price) * quantity, 4)
        delay = round((average_execution_price - arrival_price) * quantity, 4)
        execution_cost = costs.total_transaction_cost
        shortfall = round(opportunity + delay + execution_cost, 4)
        return ImplementationShortfallAnalysis(decision_price, arrival_price, average_execution_price, opportunity, delay, execution_cost, shortfall)


class MarketImpactEvaluationEngine:
    """Evaluate ARGOS market impact."""

    def evaluate(self, authorization: ExecutionAuthorization, market: MarketConditionSnapshot, average_execution_price: float) -> MarketImpactEvaluation:
        midpoint = (market.bid + market.ask) / 2
        displacement = round(average_execution_price - midpoint, 4)
        liquidity_depletion = round(min(1.0, authorization.approved_quantity / max(market.available_liquidity, 1)), 4)
        participation = liquidity_depletion
        return MarketImpactEvaluation(displacement, round(abs(displacement) / max(midpoint, 1), 4), liquidity_depletion, round(participation * market.volatility_score, 4), participation, "normal_recovery" if liquidity_depletion < 0.3 else "slow_recovery_expected")


class ExceptionManagementEngine:
    """Identify and classify execution anomalies."""

    def detect(
        self,
        progress: ExecutionProgress,
        slippage: SlippageAnalysis,
        impact: MarketImpactEvaluation,
        authorization: ExecutionAuthorization,
    ) -> tuple[ExecutionException, ...]:
        exceptions = []
        if progress.rejected_quantity > 0:
            exceptions.append(ExecutionException("EXEC-EXC-001", "rejected_orders", ExecutionExceptionSeverity.HIGH, "order_rejection", "request_executive_review"))
        if abs(slippage.percentage_slippage) > authorization.max_slippage_percent:
            exceptions.append(ExecutionException("EXEC-EXC-002", "excessive_slippage", ExecutionExceptionSeverity.HIGH, "market_movement_or_liquidity_limit", "pause_execution_and_request_risk_reassessment"))
        if progress.execution_latency_ms > 5000:
            exceptions.append(ExecutionException("EXEC-EXC-003", "excessive_latency", ExecutionExceptionSeverity.MEDIUM, "execution_delay", "retry_or_pause_execution"))
        if impact.liquidity_depletion > 0.5:
            exceptions.append(ExecutionException("EXEC-EXC-004", "excessive_market_impact", ExecutionExceptionSeverity.CRITICAL, "liquidity_depletion", "suspend_additional_execution"))
        return tuple(exceptions)


class ExecutionRecoveryEngine:
    """Determine deterministic recovery actions."""

    def recommend(self, exceptions: tuple[ExecutionException, ...]) -> tuple[ExecutionRecoveryAction, ...]:
        actions = []
        for exception in exceptions:
            if exception.severity == ExecutionExceptionSeverity.CRITICAL:
                actions.append(ExecutionRecoveryAction(f"REC-{len(actions) + 1:03d}", "pause_execution_and_request_executive_review", True, True))
            elif exception.classification == "excessive_slippage":
                actions.append(ExecutionRecoveryAction(f"REC-{len(actions) + 1:03d}", "request_risk_reassessment", True, True))
            else:
                actions.append(ExecutionRecoveryAction(f"REC-{len(actions) + 1:03d}", exception.recommended_response, True, False))
        return tuple(actions)


class ExecutionCompletionEngine:
    """Determine execution completion and immutable record readiness."""

    def complete(self, authorization: ExecutionAuthorization, progress: ExecutionProgress, exceptions: tuple[ExecutionException, ...]) -> str:
        if any(exception.severity == ExecutionExceptionSeverity.CRITICAL for exception in exceptions):
            return "execution_failure_declared"
        if progress.filled_quantity >= authorization.approved_quantity:
            return "entire_approved_quantity_executed"
        if progress.cancelled_quantity > 0:
            return "order_cancelled_by_authorization"
        return "execution_in_progress"


class TradeExecutionOffice:
    """Deterministic Trade Execution Office."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.prompt_repository = prompt_repository
        self.plan_engine = ExecutionPlanEngine()
        self.submission = OrderSubmissionEngine()
        self.monitoring = ExecutionMonitoringEngine()
        self.fill_analysis = FillAnalysisEngine()
        self.slippage = SlippageAnalysisEngine()
        self.costs = TransactionCostAnalysisEngine()
        self.shortfall = ImplementationShortfallEngine()
        self.impact = MarketImpactEvaluationEngine()
        self.exceptions = ExceptionManagementEngine()
        self.recovery = ExecutionRecoveryEngine()
        self.completion = ExecutionCompletionEngine()

    def generate_execution_plan(
        self,
        authorization: ExecutionAuthorization,
        market: MarketConditionSnapshot,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> OperationalContract:
        self.configuration_service.validate_startup()
        plan = self.plan_engine.plan(authorization, market)
        payload = {
            "office_id": TRADE_EXECUTION_OFFICE_ID,
            "execution_plan": plan.__dict__,
            "market_conditions": market.__dict__,
            **self.plan_engine.records(authorization, market, plan),
        }
        return self._persist_contract("EXECUTION_PLAN", case_file_id, trade_cycle_id, document_sequence, (authorization.cdr_id, authorization.risk_certification_id), "Trade Execution Office execution plan.", payload)

    def submit_to_order_management(
        self,
        authorization: ExecutionAuthorization,
        market: MarketConditionSnapshot,
        order_management_office: OrderManagementOffice,
        case_file_id: str,
        trade_cycle_id: str,
        order_sequence: int,
        document_sequence: int,
    ) -> OperationalContract:
        plan = self.plan_engine.plan(authorization, market)
        order_record = self.submission.submit(plan, authorization, order_management_office, case_file_id, trade_cycle_id, order_sequence, document_sequence)
        payload = {
            "office_id": TRADE_EXECUTION_OFFICE_ID,
            "submission_status": "submitted_to_order_management",
            "order_management_document_id": order_record.contract_id,
            "execution_plan": plan.__dict__,
            **self.plan_engine.records(authorization, market, plan),
            "submission_timestamp_utc": utc_timestamp(),
            "direct_broker_communication": False,
        }
        return self._persist_contract("EXECUTION_SUBMISSION", case_file_id, trade_cycle_id, document_sequence + 1, (authorization.cdr_id, authorization.risk_certification_id, order_record.contract_id), "Trade Execution Office order submission record.", payload)

    def evaluate_execution(
        self,
        authorization: ExecutionAuthorization,
        market: MarketConditionSnapshot,
        fills: tuple[ExecutionFill, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        cancelled_quantity: float = 0.0,
        rejected_quantity: float = 0.0,
    ) -> dict[str, OperationalContract]:
        progress = self.monitoring.progress(authorization.approved_quantity, fills, cancelled_quantity, rejected_quantity)
        fill_profile = self.fill_analysis.profile(fills)
        slippage = self.slippage.analyze(authorization.expected_price, fill_profile.average_fill_price, fill_profile.total_fill_quantity, market, fill_profile.max_latency_ms)
        costs = self.costs.analyze(fill_profile.total_fill_quantity, fill_profile.average_fill_price, market)
        shortfall = self.shortfall.analyze(authorization.expected_price, market.last_price, fill_profile.average_fill_price, fill_profile.total_fill_quantity, costs)
        impact = self.impact.evaluate(authorization, market, fill_profile.average_fill_price)
        exceptions = self.exceptions.detect(progress, slippage, impact, authorization)
        recovery = self.recovery.recommend(exceptions)
        completion = self.completion.complete(authorization, progress, exceptions)
        plan = self.plan_engine.plan(authorization, market)
        plan_records = self.plan_engine.records(authorization, market, plan)
        state_history = self._execution_state_history(completion, progress, exceptions)
        fill_history = tuple(fill.__dict__ for fill in fills)
        notification = self._executive_notification(exceptions)
        audit_log = self._execution_audit_log(authorization, state_history, fill_history)
        performance_dataset = ExecutionPerformanceDataset(
            "EPD-053",
            {
                "average_fill_price": fill_profile.average_fill_price,
                "total_fill_quantity": fill_profile.total_fill_quantity,
                "percentage_slippage": slippage.percentage_slippage,
                "total_transaction_cost": costs.total_transaction_cost,
                "realized_implementation_shortfall": shortfall.realized_implementation_shortfall,
                "market_impact_participation_rate": impact.participation_rate,
            },
        )
        event_archive = ExecutionEventArchive("EEA-053", tuple(event["event_id"] for event in audit_log))
        payload_base = {
            "office_id": TRADE_EXECUTION_OFFICE_ID,
            "cdr_id": authorization.cdr_id,
            "risk_certification_id": authorization.risk_certification_id,
            "investment_performance_evaluated": False,
            "execution_state_history": state_history,
            "fill_history": fill_history,
            "execution_audit_log": audit_log,
            "executive_notification_record": notification,
        }
        artifacts = {
            "execution_progress_report": {
                **payload_base,
                "execution_state": completion,
                "progress": progress.__dict__,
                "completed_fills": [fill.__dict__ for fill in fills],
                "remaining_quantity": progress.remaining_quantity,
                "active_anomalies": [exception.__dict__ for exception in exceptions],
            },
            "execution_quality_report": {
                **payload_base,
                "fill_quality": fill_profile.__dict__,
                "slippage": slippage.__dict__,
                "slippage_assessment": slippage.__dict__,
                "transaction_costs": costs.__dict__,
                "transaction_cost_assessment": costs.__dict__,
                "implementation_shortfall": shortfall.__dict__,
                "implementation_shortfall_assessment": shortfall.__dict__,
                "market_impact": impact.__dict__,
                "market_impact_assessment": impact.__dict__,
                "execution_efficiency": round(1 - min(1.0, abs(slippage.percentage_slippage) / max(authorization.max_slippage_percent, 0.0001)), 4),
            },
            "completed_execution_report": {
                **payload_base,
                "complete_execution_history": [fill.__dict__ for fill in fills],
                "final_execution_statistics": progress.__dict__,
                "execution_quality_assessment": fill_profile.__dict__,
                "transaction_cost_summary": costs.__dict__,
                "implementation_shortfall_assessment": shortfall.__dict__,
                "final_audit_references": (authorization.cdr_id, authorization.risk_certification_id),
                "completion_status": completion,
            },
            "execution_case_file": {
                **payload_base,
                "executive_decision": authorization.cdr_id,
                "organizational_risk_assessment": authorization.risk_certification_id,
                "execution_strategy": authorization.strategy_id,
                "execution_timeline": plan.timeline,
                "market_conditions": market.__dict__,
                "fills": [fill.__dict__ for fill in fills],
                "execution_anomalies": [exception.__dict__ for exception in exceptions],
                "transaction_costs": costs.__dict__,
                "implementation_shortfall_assessment": shortfall.__dict__,
                "execution_quality_metrics": fill_profile.__dict__,
                "execution_performance_dataset": performance_dataset,
                "execution_event_archive": event_archive,
                **plan_records,
            },
        }
        if exceptions:
            artifacts["execution_exception_report"] = {
                **payload_base,
                "exceptions": [exception.__dict__ for exception in exceptions],
                "organizational_impact": "execution_deviation_from_plan",
                "execution_recovery_record": [action.__dict__ for action in recovery],
                "recommended_actions": [action.__dict__ for action in recovery],
                "required_approvals": tuple(action.action for action in recovery if action.requires_approval),
            }
        contracts = {}
        for offset, (name, payload) in enumerate(artifacts.items()):
            contracts[name] = self._persist_contract(
                _contract_type_for(name),
                case_file_id,
                trade_cycle_id,
                document_sequence + offset,
                (authorization.cdr_id, authorization.risk_certification_id),
                f"Trade Execution Office {name.replace('_', ' ')}.",
                payload,
            )
        return contracts

    def _execution_state_history(
        self,
        completion: str,
        progress: ExecutionProgress,
        exceptions: tuple[ExecutionException, ...],
    ) -> tuple[dict[str, object], ...]:
        states = [
            {"sequence": 1, "state": "authorization_verified", "trigger": "authorization_validation"},
            {"sequence": 2, "state": "risk_certification_verified", "trigger": "risk_validation"},
            {"sequence": 3, "state": "execution_monitored", "trigger": "progress_update", "filled_quantity": progress.filled_quantity},
        ]
        if exceptions:
            states.append({"sequence": 4, "state": "exception_detected", "trigger": "anomaly_detection", "exception_count": len(exceptions)})
        states.append({"sequence": len(states) + 1, "state": completion, "trigger": "completion_engine"})
        return tuple(states)

    def _executive_notification(self, exceptions: tuple[ExecutionException, ...]) -> ExecutiveNotificationRecord:
        required = any(exception.severity in {ExecutionExceptionSeverity.HIGH, ExecutionExceptionSeverity.CRITICAL} for exception in exceptions)
        reason = "material_execution_exception" if required else "no_material_exception"
        return ExecutiveNotificationRecord("ENR-053", required, reason, required)

    def _execution_audit_log(
        self,
        authorization: ExecutionAuthorization,
        state_history: tuple[dict[str, object], ...],
        fill_history: tuple[dict[str, object], ...],
    ) -> tuple[dict[str, object], ...]:
        return (
            {"event_id": "EXEC-AUD-001", "event": "authorization_verified", "source": authorization.cdr_id},
            {"event_id": "EXEC-AUD-002", "event": "risk_certification_verified", "source": authorization.risk_certification_id},
            {"event_id": "EXEC-AUD-003", "event": "state_history_recorded", "state_count": len(state_history)},
            {"event_id": "EXEC-AUD-004", "event": "fill_history_recorded", "fill_count": len(fill_history)},
        )

    def _persist_contract(
        self,
        contract_type: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        parent_contract_ids: tuple[str, ...],
        human_summary: str,
        payload: dict[str, Any],
    ) -> OperationalContract:
        contract = _contract(contract_type, case_file_id, trade_cycle_id, document_sequence, parent_contract_ids, human_summary, payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract


def _contract_type_for(name: str) -> str:
    return {
        "execution_progress_report": "EXECUTION_PROGRESS",
        "execution_quality_report": "EXECUTION_QUALITY",
        "execution_exception_report": "EXECUTION_EXCEPTION",
        "completed_execution_report": "COMPLETED_EXECUTION",
        "execution_case_file": "EXECUTION_CASE_FILE",
    }[name]


def _contract(
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    document_sequence: int,
    parent_contract_ids: tuple[str, ...],
    human_summary: str,
    payload: dict[str, Any],
) -> OperationalContract:
    created = utc_timestamp()
    normalized_payload = _json_ready(payload)
    signature_hash = hashlib.sha256(
        json.dumps(normalized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        parent_contract_ids=parent_contract_ids,
        produced_by_staff_id=TRADE_EXECUTION_STAFF_ID,
        produced_by_group_id=TRADER_GROUP_ID,
        intended_consumer_group_id=TRADER_GROUP_ID,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=human_summary,
        machine_payload=normalized_payload,
        signature_hash=signature_hash,
        source_reference_ids=parent_contract_ids,
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
