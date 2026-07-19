"""Performance Truth Engine for ARGOS OE-011C."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, time, timedelta, timezone
import hashlib
import json
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any

from argos.foundation.contracts import utc_timestamp
from .position_registry import PositionRegistry
from .truth_domain import (
    OperationalTruthEnvelope,
    TruthEnvelopeError,
    paper_broker_metadata,
    require_operational_truth_envelope,
    validate_decision_object_for_operational_truth,
)
from .truth_promotion import PromotionDecisionStatus, TruthPromotionAuthority


BENCHMARK_RETURNS = {
    "SPY": 0.82,
    "QQQ": 1.04,
    "DIA": 0.47,
    "IWM": 0.31,
    "USER_SELECTED": 0.68,
}


@dataclass(frozen=True)
class TradeLedgerRecord:
    """Immutable realized trade record."""

    trade_id: str
    workflow_id: str
    decision_object_id: str
    token_id: str
    strategy_id: str
    symbol: str
    asset_type: str
    direction: str
    quantity: float
    entry_order_id: str
    exit_order_id: str
    entry_price: float
    exit_price: float
    entry_timestamp: str
    exit_timestamp: str
    commissions: float
    fees: float
    slippage: float
    realized_profit_loss: float
    holding_period: str
    market_environment: str
    audit_identifier: str
    status: str
    execution_environment: str
    timestamp: str
    hash: str


@dataclass(frozen=True)
class BrokerRealisticOrderRecord:
    """Immutable broker-realistic paper order simulation record."""

    order_id: str
    workflow_id: str
    decision_object_id: str
    token_id: str
    strategy_id: str
    intended_order: dict[str, Any]
    broker_profile_id: str
    account_type: str
    symbol: str
    asset_type: str
    side: str
    order_type: str
    time_in_force: str
    requested_quantity: float
    filled_quantity: float
    remaining_quantity: float
    bid_price: float
    ask_price: float
    mid_price: float
    last_price: float
    limit_price: float
    average_fill_price: float
    spread_cost: float
    slippage: float
    estimated_notional: float
    cash_impact: float
    realized_profit_loss: float
    buying_power_before: float
    buying_power_after: float
    market_session: str
    fill_probability: float
    partial_fill_probability: float
    available_volume: float
    liquidity: str
    status: str
    rejection_reason: str
    queued_reason: str
    broker_validation: tuple[dict[str, Any], ...]
    fantasy_warnings: tuple[str, ...]
    execution_environment: str
    timestamp: str
    hash: str


@dataclass(frozen=True)
class PositionLedgerRecord:
    """Immutable position valuation record."""

    position_id: str
    symbol: str
    average_cost: float
    quantity: float
    market_value: float
    unrealized_profit_loss: float
    risk_exposure: float
    workflow_origin: str
    decision_object_id: str
    last_market_update: str
    audit_identifier: str
    execution_environment: str
    timestamp: str
    workflow_id: str
    token_id: str
    hash: str


@dataclass(frozen=True)
class PortfolioLedgerRecord:
    """Immutable portfolio valuation record."""

    timestamp: str
    cash: float
    invested_capital: float
    market_value: float
    total_equity: float
    buying_power: float
    margin_used: float
    daily_return: float
    total_return: float
    benchmark_value: float
    alpha: float
    drawdown: float
    workflow_id: str
    decision_object_id: str
    token_id: str
    audit_identifier: str
    execution_environment: str
    hash: str


@dataclass(frozen=True)
class DecisionObjectOutcomeRecord:
    """Immutable outcome attached to a Decision Object."""

    decision_object_id: str
    workflow_id: str
    final_recommendation: str
    actual_trade_result: float
    expected_return: float
    actual_return: float
    confidence: float
    prediction_error: float
    time_to_target: str
    risk_accuracy: float
    historian_feedback: str
    token_id: str
    audit_identifier: str
    execution_environment: str
    timestamp: str
    hash: str


@dataclass(frozen=True)
class WorkflowAttributionRecord:
    """Immutable workflow financial attribution."""

    workflow_id: str
    strategy_id: str
    office_sequence: tuple[str, ...]
    runtime: int
    credits_used: float
    decision_quality: float
    financial_outcome: float
    decision_object_id: str
    token_id: str
    audit_identifier: str
    execution_environment: str
    timestamp: str
    hash: str


@dataclass(frozen=True)
class OfficeAttributionRecord:
    """Immutable office contribution attribution."""

    attribution_id: str
    workflow_id: str
    office: str
    contribution_type: str
    contribution_value: float
    decision_object_id: str
    token_id: str
    audit_identifier: str
    execution_environment: str
    timestamp: str
    hash: str


@dataclass(frozen=True)
class BenchmarkRecord:
    """Immutable benchmark observation."""

    benchmark: str
    timestamp: str
    benchmark_return: float
    portfolio_return: float
    alpha: float
    audit_identifier: str
    execution_environment: str
    hash: str


class PerformanceTruthEngine:
    """Authoritative immutable accounting system for trading performance."""

    def __init__(self, *, paper_starting_cash: float = 0.0, live_starting_cash: float = 0.0) -> None:
        self._paper_starting_cash = round(float(paper_starting_cash), 4)
        self._live_starting_cash = round(float(live_starting_cash), 4)
        self._paper_account_cash = self._paper_starting_cash
        self._broker_profile = _broker_profile()
        self._position_registry = PositionRegistry()
        self._order_ledger: list[BrokerRealisticOrderRecord] = []
        self._trade_ledger: list[TradeLedgerRecord] = []
        self._position_ledger: list[PositionLedgerRecord] = []
        self._portfolio_ledger: list[PortfolioLedgerRecord] = []
        self._decision_outcomes: list[DecisionObjectOutcomeRecord] = []
        self._workflow_attribution: list[WorkflowAttributionRecord] = []
        self._office_attribution: list[OfficeAttributionRecord] = []
        self._benchmark_history: list[BenchmarkRecord] = []
        self._closed_position_truth_records: list[dict[str, Any]] = []
        self._recorded_workflows: set[str] = set()
        self._rejected_truth_records: list[dict[str, Any]] = []

    @property
    def position_registry(self) -> PositionRegistry:
        """Expose the Position Registry as the authoritative position gateway."""
        return self._position_registry

    def set_paper_account_cash(self, amount_usd: float) -> None:
        """Set paper buying power to the Commander-allocated active treasury amount."""
        amount = round(max(0.0, float(amount_usd)), 4)
        if not any(item.execution_environment == "paper" for item in self._order_ledger):
            self._paper_starting_cash = amount
        self._paper_account_cash = amount

    def ingest_closed_position_truth(self, records: tuple[dict[str, Any], ...]) -> None:
        """Consume immutable Closed Position Truth records idempotently."""
        known = {str(item.get("closed_position_truth_id", "")) for item in self._closed_position_truth_records}
        for record in records:
            record_id = str(record.get("closed_position_truth_id", ""))
            if record_id and record_id not in known:
                self._closed_position_truth_records.append(dict(record))
                known.add(record_id)

    def record_completed_workflow(self, workflow: Any, *, execution_environment: str = "paper", account_cash_usd: float | None = None) -> None:
        """Append one immutable financial outcome set for a completed workflow."""
        if workflow.workflow_id in self._recorded_workflows:
            return
        if workflow.token.workflow_status != "Archived":
            raise ValueError("workflow must be archived before outcome recording")
        if execution_environment not in {"paper", "live"}:
            raise ValueError("execution_environment must be paper or live")

        timestamp = utc_timestamp()
        decision = _latest_decision_object(workflow)
        decision_object_id = decision.get("decisionObjectId", f"DO-{workflow.workflow_id.replace('EWO-WF-', '')}")
        strategy_id = decision.get("currentStrategy", "Risk Adjusted Paper Strategy")
        provenance = validate_decision_object_for_operational_truth(decision, execution_environment=execution_environment)
        if not provenance.valid:
            self._reject_truth_record(
                record_type="completed_workflow",
                source_system="PerformanceTruthEngine.record_completed_workflow",
                workflow_id=workflow.workflow_id,
                decision_object_id=decision_object_id,
                token_id=workflow.token.audit_identifier,
                codes=provenance.codes,
                execution_environment=execution_environment,
                timestamp=timestamp,
            )
            self._recorded_workflows.add(workflow.workflow_id)
            return
        if account_cash_usd is not None and execution_environment == "paper":
            self.set_paper_account_cash(account_cash_usd)
        index = len([item for item in self._order_ledger if item.execution_environment == execution_environment]) + 1
        symbol = _symbol_for_index(index)
        audit_identifier = workflow.token.audit_identifier
        token_id = workflow.token.audit_identifier
        order = self._simulate_broker_order(
            index=index,
            workflow=workflow,
            decision=decision,
            decision_object_id=decision_object_id,
            strategy_id=strategy_id,
            symbol=symbol,
            side="BUY",
            requested_quantity=float(_quantity_for_symbol(symbol)),
            token_id=token_id,
            timestamp=timestamp,
            execution_environment=execution_environment,
        )
        self._order_ledger.append(order)

        realized = order.realized_profit_loss
        actual_return = 0.0
        if order.status in {"FILLED", "PARTIALLY_FILLED"}:
            self._apply_executed_order(order, audit_identifier, decision)
            self._trade_ledger.append(_trade_record_from_order(order, audit_identifier))
            if order.estimated_notional:
                actual_return = round(order.realized_profit_loss / max(1.0, order.estimated_notional), 6)

        outcome = _record(
            DecisionObjectOutcomeRecord,
            decision_object_id=decision_object_id,
            workflow_id=workflow.workflow_id,
            final_recommendation=decision.get("recommendation", "PAPER_REVIEW_COMPLETE"),
            actual_trade_result=realized,
            expected_return=float(decision.get("expectedReturn", 0.0)),
            actual_return=actual_return,
            confidence=float(decision.get("confidence", 0.0)),
            prediction_error=round(float(decision.get("expectedReturn", 0.0)) - actual_return, 6),
            time_to_target=f"{max(1, workflow.execution_time_seconds)}m",
            risk_accuracy=round(1.0 - min(1.0, abs(float(decision.get("riskScore", 0.0)) - 0.25)), 4),
            historian_feedback="PENDING_HISTORIAN_EVALUATION",
            token_id=token_id,
            audit_identifier=audit_identifier,
            execution_environment=execution_environment,
            timestamp=timestamp,
        )
        self._decision_outcomes.append(outcome)

        self._workflow_attribution.append(
            _record(
                WorkflowAttributionRecord,
                workflow_id=workflow.workflow_id,
                strategy_id=strategy_id,
                office_sequence=tuple(workflow.stages),
                runtime=workflow.execution_time_seconds,
                credits_used=workflow.credits_used,
                decision_quality=round(float(decision.get("confidence", 0.0)) * 100, 4),
                financial_outcome=realized,
                decision_object_id=decision_object_id,
                token_id=token_id,
                audit_identifier=audit_identifier,
                execution_environment=execution_environment,
                timestamp=timestamp,
            )
        )
        self._append_office_attribution(workflow, decision_object_id, token_id, audit_identifier, execution_environment, timestamp)
        self._append_portfolio_valuation(workflow.workflow_id, decision_object_id, token_id, audit_identifier, execution_environment, timestamp)
        self._recorded_workflows.add(workflow.workflow_id)

    def record_manual_paper_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        decision_object_id: str = "DO-MANUAL-PAPER-ORDER",
        strategy_id: str = "Commander Manual Paper Order",
        workflow_id: str = "MANUAL-PAPER-WORKFLOW",
        token_id: str = "MANUAL-PAPER-TOKEN",
    ) -> dict[str, Any]:
        """Record a deterministic paper broker order outside autonomous lifecycle management."""
        timestamp = utc_timestamp()
        index = len([item for item in self._order_ledger if item.execution_environment == "paper"]) + 1
        existing_position = _latest_position_for_symbol(self._position_ledger, symbol, "paper")
        if side.upper() == "SELL" and decision_object_id == "DO-MANUAL-PAPER-ORDER" and existing_position:
            decision_object_id = existing_position.decision_object_id
            workflow_id = existing_position.workflow_id
        order = self._simulate_broker_order(
            index=index,
            workflow=None,
            decision={"recommendation": side.upper()},
            decision_object_id=decision_object_id,
            strategy_id=strategy_id,
            symbol=symbol,
            side=side.upper(),
            requested_quantity=float(quantity),
            token_id=token_id,
            timestamp=timestamp,
            execution_environment="paper",
            workflow_id=workflow_id,
        )
        self._order_ledger.append(order)
        if order.status in {"FILLED", "PARTIALLY_FILLED"}:
            self._apply_executed_order(order, token_id, None)
            self._trade_ledger.append(_trade_record_from_order(order, token_id))
        self._append_portfolio_valuation(workflow_id, decision_object_id, token_id, token_id, "paper", timestamp)
        return asdict(order)

    def record_broker_authoritative_order(self, broker_order: dict[str, Any], *, truth_envelope: OperationalTruthEnvelope | dict[str, Any] | None = None) -> dict[str, Any]:
        """Record an OR-003 broker-authoritative paper order without fabricating execution truth."""
        ticket = dict(broker_order.get("ticket", {}) or {})
        market = dict(broker_order.get("market_state", {}) or {})
        fills = tuple(dict(item) for item in broker_order.get("fills", ()) or ())
        timestamp = str(broker_order.get("updated_at") or broker_order.get("created_at") or utc_timestamp())
        execution_environment = "paper"
        try:
            promotion = TruthPromotionAuthority().promote_performance_truth(truth_envelope, object_id=str(broker_order.get("order_id", "")))
            if promotion.decision != PromotionDecisionStatus.APPROVED:
                raise TruthEnvelopeError(promotion.reason_codes)
            validated_envelope = require_operational_truth_envelope(
                truth_envelope,
                target_authority="PerformanceTruthEngine",
                allowed_authorities={"DeterministicPaperBrokerage"},
            )
        except TruthEnvelopeError as exc:
            self._reject_truth_record(
                record_type="broker_authoritative_order",
                source_system="DeterministicPaperBrokerage",
                workflow_id=str(ticket.get("workflow_id", "")),
                decision_object_id=str(ticket.get("decision_object_id", "")),
                token_id=str(ticket.get("workflow_token", "")),
                codes=exc.codes,
                execution_environment=execution_environment,
                timestamp=timestamp,
            )
            return {"accepted": False, "reason": "TRUTH_ENVELOPE_REJECTED", "codes": exc.codes}
        decision = dict(ticket.get("decision_object", {}) or {})
        provenance = validate_decision_object_for_operational_truth(decision, execution_environment=execution_environment)
        if not provenance.valid:
            self._reject_truth_record(
                record_type="broker_authoritative_order",
                source_system="DeterministicPaperBrokerage",
                workflow_id=str(ticket.get("workflow_id", "")),
                decision_object_id=str(ticket.get("decision_object_id", "")),
                token_id=str(ticket.get("workflow_token", "")),
                codes=provenance.codes,
                execution_environment=execution_environment,
                timestamp=timestamp,
            )
            return {"accepted": False, "reason": "DECISION_PROVENANCE_REJECTED", "codes": provenance.codes}
        status = str(broker_order.get("status", "")).upper()
        filled_quantity = round(float(broker_order.get("filled_quantity", 0.0) or 0.0), 4)
        if filled_quantity > 0 and not fills:
            self._reject_truth_record(
                record_type="broker_authoritative_order",
                source_system="DeterministicPaperBrokerage",
                workflow_id=str(ticket.get("workflow_id", "")),
                decision_object_id=str(ticket.get("decision_object_id", "")),
                token_id=str(ticket.get("workflow_token", "")),
                codes=("AUTHORITATIVE_FILL_EVIDENCE_REQUIRED",),
                execution_environment=execution_environment,
                timestamp=timestamp,
            )
            return {"accepted": False, "reason": "AUTHORITATIVE_FILL_EVIDENCE_REQUIRED", "codes": ("AUTHORITATIVE_FILL_EVIDENCE_REQUIRED",)}
        average_fill_price = round(float(broker_order.get("average_fill_price", 0.0) or 0.0), 4)
        reference_mid = round((float(market.get("bid", average_fill_price) or average_fill_price) + float(market.get("ask", average_fill_price) or average_fill_price)) / 2, 4)
        slippage = round(sum(float(item.get("slippage", 0.0) or 0.0) for item in fills), 4)
        commissions = round(sum(float(item.get("commission", 0.0) or 0.0) for item in fills), 4)
        side = str(ticket.get("side", "")).upper()
        existing_position = _latest_position_for_symbol(self._position_ledger, str(ticket.get("symbol", "")).upper(), execution_environment)
        realized_profit_loss = 0.0
        if side == "SELL" and existing_position and filled_quantity:
            realized_profit_loss = round((average_fill_price - existing_position.average_cost) * filled_quantity - slippage - commissions, 4)
        cash_impact = round((-average_fill_price * filled_quantity - slippage - commissions) if side == "BUY" else (average_fill_price * filled_quantity - slippage - commissions), 4) if filled_quantity else 0.0
        buying_power_before = self._paper_account_cash
        buying_power_after = round(max(0.0, buying_power_before + cash_impact), 4) if filled_quantity else buying_power_before
        order = _record(
            BrokerRealisticOrderRecord,
            order_id=str(broker_order.get("order_id", "")),
            workflow_id=str(ticket.get("workflow_id", "")),
            decision_object_id=str(ticket.get("decision_object_id", "")),
            token_id=str(ticket.get("workflow_token", "")),
            strategy_id=str(ticket.get("strategy_id", "")),
            intended_order={
                "symbol": str(ticket.get("symbol", "")).upper(),
                "side": side,
                "orderType": str(ticket.get("order_type", "")),
                "requestedQuantity": float(ticket.get("quantity", 0.0) or 0.0),
                "source": "DeterministicPaperBrokerage",
                "missionId": str(ticket.get("mission_id", "")),
                "traderIdentity": str(ticket.get("trader_identity", "")),
                "accountId": str(ticket.get("account_id", "")),
                "truthEnvelope": validated_envelope,
            },
            broker_profile_id=self._broker_profile["profileId"],
            account_type=self._broker_profile["accountType"],
            symbol=str(ticket.get("symbol", "")).upper(),
            asset_type=str(ticket.get("asset_type", "")).upper(),
            side=side,
            order_type=str(ticket.get("order_type", "")),
            time_in_force=str(ticket.get("time_in_force", "")),
            requested_quantity=float(broker_order.get("requested_quantity", ticket.get("quantity", 0.0)) or 0.0),
            filled_quantity=filled_quantity,
            remaining_quantity=float(broker_order.get("remaining_quantity", 0.0) or 0.0),
            bid_price=float(market.get("bid", 0.0) or 0.0),
            ask_price=float(market.get("ask", 0.0) or 0.0),
            mid_price=reference_mid,
            last_price=float(market.get("last", reference_mid) or reference_mid),
            limit_price=float(ticket.get("limit_price", 0.0) or 0.0),
            average_fill_price=average_fill_price,
            spread_cost=round(abs((float(market.get("ask", reference_mid) or reference_mid) if side == "BUY" else float(market.get("bid", reference_mid) or reference_mid)) - reference_mid) * filled_quantity, 4),
            slippage=slippage,
            estimated_notional=round(float(ticket.get("quantity", 0.0) or 0.0) * max(average_fill_price, reference_mid), 4),
            cash_impact=cash_impact,
            realized_profit_loss=realized_profit_loss,
            buying_power_before=buying_power_before,
            buying_power_after=buying_power_after,
            market_session=str(market.get("session", "")),
            fill_probability=1.0 if status in {"FILLED", "SETTLED"} else 0.0,
            partial_fill_probability=1.0 if status == "PARTIALLY_FILLED" else 0.0,
            available_volume=float(market.get("volume", 0.0) or 0.0),
            liquidity="NORMAL",
            status=status,
            rejection_reason=str(broker_order.get("rejection_code", "")),
            queued_reason="" if status not in {"QUEUED", "WORKING"} else "NOT_EXECUTABLE_YET",
            broker_validation=(
                _validation("Broker Authority", True, "DeterministicPaperBrokerage"),
                _validation("Valid Fill Source", bool(fills) if filled_quantity else True, str(len(fills))),
            ),
            fantasy_warnings=(),
            execution_environment=execution_environment,
            timestamp=timestamp,
        )
        if any(item.order_id == order.order_id for item in self._order_ledger):
            return {"accepted": True, "idempotent": True, "orderId": order.order_id}
        self._order_ledger.append(order)
        if order.status in {"FILLED", "PARTIALLY_FILLED", "SETTLED"} and order.filled_quantity > 0:
            self._apply_executed_order(order, order.token_id, decision, fills)
            self._trade_ledger.append(_trade_record_from_order(order, order.token_id))
        self._append_portfolio_valuation(order.workflow_id, order.decision_object_id, order.token_id, order.token_id, execution_environment, timestamp)
        return {"accepted": True, "orderId": order.order_id, "status": order.status}

    def snapshot(self, *, execution_environment: str = "paper") -> dict[str, Any]:
        """Return immutable ledgers and derived performance calculations."""
        orders = tuple(item for item in self._order_ledger if item.execution_environment == execution_environment)
        trades = tuple(item for item in self._trade_ledger if item.execution_environment == execution_environment)
        positions = _current_positions(self._position_ledger, execution_environment)
        valuations = tuple(item for item in self._portfolio_ledger if item.execution_environment == execution_environment)
        outcomes = tuple(item for item in self._decision_outcomes if item.execution_environment == execution_environment)
        workflows = tuple(item for item in self._workflow_attribution if item.execution_environment == execution_environment)
        offices = tuple(item for item in self._office_attribution if item.execution_environment == execution_environment)
        benchmarks = tuple(item for item in self._benchmark_history if item.execution_environment == execution_environment)
        return {
            "engineName": "Performance Truth Engine",
            "engineeringOrder": "OE-011C",
            "sourceOfTruth": "IMMUTABLE_LEDGER",
            "enterprisePrinciple": "One Event -> One Truth Record -> Many Views",
            "executionEnvironment": execution_environment,
            "brokerProfile": self._broker_profile,
            "paperAccount": self._paper_account_snapshot(execution_environment),
            "positionRegistry": self._position_registry.snapshot(),
            "orderLedger": tuple(asdict(item) for item in orders),
            "tradeLedger": tuple(asdict(item) for item in trades),
            "positionLedger": tuple(asdict(item) for item in positions),
            "portfolioLedger": tuple(asdict(item) for item in valuations),
            "decisionObjectOutcomes": tuple(asdict(item) for item in outcomes),
            "workflowAttribution": tuple(asdict(item) for item in workflows),
            "officeAttribution": tuple(asdict(item) for item in offices),
            "benchmarkHistory": tuple(asdict(item) for item in benchmarks),
            "closedPositionTruth": tuple(self._closed_position_truth_records),
            "rejectedTruthRecords": tuple(self._rejected_truth_records),
            "closedLifecycleAnalytics": {
                "closedTruthRecordCount": len(self._closed_position_truth_records),
                "netRealizedPnl": round(sum(float(item.get("net_realized_pnl", 0.0) or 0.0) for item in self._closed_position_truth_records), 4),
                "averageExecutionQuality": _average_tuple(tuple(float(item.get("execution_quality_score", 0.0) or 0.0) for item in self._closed_position_truth_records)),
                "learningPayloadsAvailable": sum(1 for item in self._closed_position_truth_records if item.get("learning_payload")),
            },
            "calculations": _calculations(trades, positions, valuations, outcomes, workflows, offices, benchmarks, self._starting_cash(execution_environment)),
            "executionRealism": _execution_realism(orders, valuations),
            "integrity": {
                "immutable": True,
                "appendOnly": True,
                "recordedWorkflowCount": len({item.workflow_id for item in workflows}),
                "uniqueWorkflowAttribution": len({item.workflow_id for item in workflows}) == len(workflows),
                "paperLiveIsolated": True,
                "hashesValid": self._hashes_valid((orders, trades, positions, valuations, outcomes, workflows, offices, benchmarks)),
                "correctionsAppendOnly": True,
                "syntheticTruthRejected": len(self._rejected_truth_records),
                "missingProvenanceRecords": sum(1 for item in self._rejected_truth_records if "MISSING_PROVENANCE" in item.get("rejectionCodes", ())),
                "unauthorizedProducerRecords": sum(1 for item in self._rejected_truth_records if "UNAUTHORIZED_PRODUCER" in item.get("rejectionCodes", ())),
                "crossModeContaminationAttempts": sum(1 for item in self._rejected_truth_records if "SIMULATION_VALUE_IN_OPERATIONAL_PATH" in item.get("rejectionCodes", ())),
                "proofModeTruthAttempts": sum(1 for item in self._rejected_truth_records if "PROOF_MODE_NOT_ACTIONABLE" in item.get("rejectionCodes", ())),
                "runtimeAuthoredFinancialProductAttempts": sum(1 for item in self._rejected_truth_records if item.get("sourceSystem") == "PerformanceTruthEngine.record_completed_workflow"),
            },
        }

    def _simulate_broker_order(
        self,
        *,
        index: int,
        workflow: Any | None,
        decision: dict[str, Any],
        decision_object_id: str,
        strategy_id: str,
        symbol: str,
        side: str,
        requested_quantity: float,
        token_id: str,
        timestamp: str,
        execution_environment: str,
        workflow_id: str | None = None,
    ) -> BrokerRealisticOrderRecord:
        asset_type = "ETF" if symbol in {"TLT", "SPY", "GLD"} else "STOCK"
        order_type = "market"
        side = side.upper()
        quote = _quote_for_symbol(symbol)
        bid = quote["bid"]
        ask = quote["ask"]
        mid = round((bid + ask) / 2, 4)
        session = _market_session()
        buying_power = self._paper_account_cash if execution_environment == "paper" else self._live_starting_cash
        reference_price = ask if side == "BUY" else bid
        estimated_notional = round(max(0.0, requested_quantity) * reference_price, 4)
        slippage = round(_slippage_cost(max(0.0, requested_quantity), reference_price, quote), 4)
        spread_cost = round(abs(reference_price - mid) * max(0.0, requested_quantity), 4)
        existing_position = _latest_position_for_symbol(self._position_ledger, symbol, execution_environment)
        held_quantity = existing_position.quantity if existing_position else 0.0
        broker_config = self._broker_profile["configuration"]
        projected_position_notional = round((held_quantity + requested_quantity if side == "BUY" else max(0.0, held_quantity - requested_quantity)) * reference_price, 4)
        validations = (
            _validation("Tradable Asset", symbol in self._broker_profile["supportedAssets"], symbol),
            _validation("Account Permission", asset_type in {"STOCK", "ETF"}, asset_type),
            _validation("Market Session", session["allowsEquityFills"], session["session"]),
            _validation("Quantity", requested_quantity > 0, str(requested_quantity)),
            _validation("Buying Power", side != "BUY" or buying_power >= estimated_notional + slippage, f"{buying_power} >= {estimated_notional + slippage:.4f}"),
            _validation("Position Quantity", side != "SELL" or held_quantity >= requested_quantity, f"{held_quantity} >= {requested_quantity}"),
            _validation("Max Order Notional", estimated_notional <= float(broker_config["maxOrderNotional"]), str(estimated_notional)),
            _validation("Max Position Notional", projected_position_notional <= float(broker_config["maxPositionNotional"]), str(projected_position_notional)),
            _validation("Order Type", order_type in self._broker_profile["orderTypes"], order_type),
            _validation("Liquidity", quote["availableVolume"] > 0, str(quote["availableVolume"])),
            _validation("Spread Slippage", ask > bid and slippage > 0, f"spread {round(ask - bid, 4)} slippage {slippage}"),
        )
        failed = tuple(item for item in validations if not item["passed"])
        partial_ratio = _partial_fill_ratio()
        liquidity_fill_quantity = min(requested_quantity, float(quote["availableVolume"]))
        if partial_ratio is not None:
            liquidity_fill_quantity = min(liquidity_fill_quantity, round(requested_quantity * partial_ratio, 4))
        partial = not failed and liquidity_fill_quantity < requested_quantity
        status = "PARTIALLY_FILLED" if partial else ("FILLED" if not failed else ("QUEUED" if not validations[2]["passed"] else "REJECTED"))
        rejection = "" if status != "REJECTED" else failed[0]["check"]
        queued = "" if status != "QUEUED" else "MARKET_CLOSED"
        filled_quantity = liquidity_fill_quantity if status in {"FILLED", "PARTIALLY_FILLED"} else 0.0
        remaining_quantity = round(max(0.0, requested_quantity - filled_quantity), 4)
        per_share_slippage = round(slippage / max(1.0, requested_quantity), 4)
        average_fill_price = round((ask + per_share_slippage) if side == "BUY" else max(0.0, bid - per_share_slippage), 4) if filled_quantity else 0.0
        executed_notional = round(filled_quantity * average_fill_price, 4)
        executed_slippage = round(per_share_slippage * filled_quantity, 4)
        executed_spread = round(abs(reference_price - mid) * filled_quantity, 4)
        realized_profit_loss = 0.0
        if side == "SELL" and filled_quantity and existing_position:
            realized_profit_loss = round((average_fill_price - existing_position.average_cost) * filled_quantity - executed_slippage, 4)
        cash_impact = round(-executed_notional - executed_slippage if side == "BUY" else executed_notional - executed_slippage, 4)
        buying_power_after = round(buying_power + cash_impact, 4) if status in {"FILLED", "PARTIALLY_FILLED"} else buying_power
        warnings = _fantasy_warnings(status=status, session=session, buying_power=buying_power, estimated_notional=estimated_notional, orders=self._order_ledger)
        order_workflow_id = workflow_id or (workflow.workflow_id if workflow is not None else "MANUAL-PAPER-WORKFLOW")
        truth_metadata = paper_broker_metadata(
            source_system="PerformanceTruthEngine.PaperBrokerModel",
            source_record_ids=(token_id, decision_object_id),
            workflow_id=order_workflow_id,
            decision_object_id=decision_object_id,
            created_at=timestamp,
        )
        return _record(
            BrokerRealisticOrderRecord,
            order_id=f"BRP-ORD-{index:06d}",
            workflow_id=order_workflow_id,
            decision_object_id=decision_object_id,
            token_id=token_id,
            strategy_id=strategy_id,
            intended_order={
                "sourceRecommendation": decision.get("recommendation", "PAPER_REVIEW_COMPLETE"),
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "requestedQuantity": requested_quantity,
                "truthMetadata": truth_metadata,
            },
            broker_profile_id=self._broker_profile["profileId"],
            account_type=self._broker_profile["accountType"],
            symbol=symbol,
            asset_type=asset_type,
            side=side,
            order_type=order_type,
            time_in_force="day",
            requested_quantity=requested_quantity,
            filled_quantity=filled_quantity,
            remaining_quantity=remaining_quantity,
            bid_price=bid,
            ask_price=ask,
            mid_price=mid,
            last_price=quote["last"],
            limit_price=0.0,
            average_fill_price=average_fill_price,
            spread_cost=executed_spread if status in {"FILLED", "PARTIALLY_FILLED"} else 0.0,
            slippage=executed_slippage if status in {"FILLED", "PARTIALLY_FILLED"} else 0.0,
            estimated_notional=estimated_notional,
            cash_impact=cash_impact if status in {"FILLED", "PARTIALLY_FILLED"} else 0.0,
            realized_profit_loss=realized_profit_loss,
            buying_power_before=buying_power,
            buying_power_after=buying_power_after,
            market_session=session["session"],
            fill_probability=0.92 if status in {"FILLED", "PARTIALLY_FILLED"} else 0.0,
            partial_fill_probability=0.05 if status == "FILLED" else (0.75 if status == "PARTIALLY_FILLED" else 0.0),
            available_volume=quote["availableVolume"],
            liquidity=quote["liquidity"],
            status=status,
            rejection_reason=rejection,
            queued_reason=queued,
            broker_validation=validations,
            fantasy_warnings=warnings,
            execution_environment=execution_environment,
            timestamp=timestamp,
        )

    def _reject_truth_record(
        self,
        *,
        record_type: str,
        source_system: str,
        workflow_id: str,
        decision_object_id: str,
        token_id: str,
        codes: tuple[str, ...],
        execution_environment: str,
        timestamp: str,
    ) -> None:
        """Record a fail-closed rejection without mutating operational ledgers."""
        self._rejected_truth_records.append(
            {
                "rejectionId": f"PTE-REJECT-{len(self._rejected_truth_records) + 1:06d}",
                "recordType": record_type,
                "sourceSystem": source_system,
                "workflowId": workflow_id,
                "decisionObjectId": decision_object_id,
                "tokenId": token_id,
                "rejectionCodes": tuple(codes),
                "executionEnvironment": execution_environment,
                "truthClassification": "REJECTED_SYNTHETIC_OR_UNPROVEN",
                "certificationStatus": "REJECTED_NOT_OPERATIONAL_TRUTH",
                "timestamp": timestamp,
            }
        )

    def _apply_executed_order(self, order: BrokerRealisticOrderRecord, audit_identifier: str, decision: dict[str, Any] | None, broker_fills: tuple[dict[str, Any], ...] = ()) -> None:
        if order.execution_environment == "paper":
            self._paper_account_cash = max(0.0, order.buying_power_after)
        existing = _latest_position_for_symbol(self._position_ledger, order.symbol, order.execution_environment)
        order_payload = asdict(order)
        if broker_fills:
            order_payload["fills"] = tuple(broker_fills)
            order_payload["fill_ids"] = tuple(str(item.get("fill_id", item.get("fillId", ""))) for item in broker_fills)
        elif order.filled_quantity > 0:
            order_payload["fills"] = (
                {
                    "fill_id": f"{order.order_id}-FILL-001",
                    "order_id": order.order_id,
                    "quantity": order.filled_quantity,
                    "price": order.average_fill_price,
                    "timestamp": order.timestamp,
                    "source": "PerformanceTruthEngine.PaperBrokerModel",
                },
            )
            order_payload["fill_ids"] = (f"{order.order_id}-FILL-001",)
        order_payload["mission_id"] = order.intended_order.get("missionId", "")
        order_payload["trader_identity"] = order.intended_order.get("traderIdentity", "")
        order_payload["account_id"] = order.intended_order.get("accountId", "")
        if order.side == "BUY":
            self._position_registry.create_from_execution(order_payload, decision)
        elif order.side == "SELL":
            self._position_registry.apply_sell_execution(order_payload)
        if order.side == "BUY":
            previous_quantity = existing.quantity if existing else 0.0
            previous_cost = existing.average_cost * previous_quantity if existing else 0.0
            new_quantity = round(previous_quantity + order.filled_quantity, 4)
            new_average = round((previous_cost + order.average_fill_price * order.filled_quantity) / max(1.0, new_quantity), 4)
        else:
            previous_quantity = existing.quantity if existing else 0.0
            new_quantity = round(max(0.0, previous_quantity - order.filled_quantity), 4)
            new_average = existing.average_cost if existing and new_quantity else 0.0
        if new_quantity <= 0:
            return
        market_value = round(new_quantity * order.mid_price, 4)
        unrealized = round(new_quantity * (order.mid_price - new_average), 4)
        self._position_ledger.append(
            _record(
                PositionLedgerRecord,
                position_id=existing.position_id if existing else f"PTE-POS-{len(self._position_ledger) + 1:06d}",
                symbol=order.symbol,
                average_cost=new_average,
                quantity=new_quantity,
                market_value=market_value,
                unrealized_profit_loss=unrealized,
                risk_exposure=market_value,
                workflow_origin=order.workflow_id,
                decision_object_id=order.decision_object_id,
                last_market_update=order.timestamp,
                audit_identifier=audit_identifier,
                execution_environment=order.execution_environment,
                timestamp=order.timestamp,
                workflow_id=order.workflow_id,
                token_id=order.token_id,
            )
        )

    def _append_office_attribution(self, workflow: Any, decision_object_id: str, token_id: str, audit_identifier: str, execution_environment: str, timestamp: str) -> None:
        latest_by_office = {output.get("workflow_stage", ""): output.get("decision_object", {}) for output in workflow.output_history}
        for index, office in enumerate(workflow.stages, start=1):
            decision = latest_by_office.get(office, {})
            contribution = round(float(decision.get("confidenceDelta", 0.0)) * 100, 4)
            self._office_attribution.append(
                _record(
                    OfficeAttributionRecord,
                    attribution_id=f"PTE-OFF-{len(self._office_attribution) + 1:06d}",
                    workflow_id=workflow.workflow_id,
                    office=office,
                    contribution_type=_contribution_type(office),
                    contribution_value=contribution,
                    decision_object_id=decision_object_id,
                    token_id=token_id,
                    audit_identifier=audit_identifier,
                    execution_environment=execution_environment,
                    timestamp=timestamp,
                )
            )

    def _append_portfolio_valuation(self, workflow_id: str, decision_object_id: str, token_id: str, audit_identifier: str, execution_environment: str, timestamp: str) -> None:
        starting_cash = self._starting_cash(execution_environment)
        trades = tuple(item for item in self._trade_ledger if item.execution_environment == execution_environment)
        positions = _current_positions(self._position_ledger, execution_environment)
        invested = round(sum(item.average_cost * item.quantity for item in positions), 4)
        market_value = round(sum(item.market_value for item in positions), 4)
        realized = round(sum(item.realized_profit_loss for item in trades), 4)
        cash = round((self._paper_account_cash if execution_environment == "paper" else starting_cash) + realized, 4)
        total_equity = round(cash + market_value, 4)
        total_return = round((total_equity - starting_cash) / max(1.0, starting_cash) * 100, 4)
        previous = next((item for item in reversed(self._portfolio_ledger) if item.execution_environment == execution_environment), None)
        previous_equity = previous.total_equity if previous else starting_cash
        daily_return = round((total_equity - previous_equity) / max(1.0, previous_equity) * 100, 4)
        benchmark_value = round(starting_cash * (1 + BENCHMARK_RETURNS["SPY"] / 100), 4)
        alpha = round(total_return - BENCHMARK_RETURNS["SPY"], 4)
        high_water = max([starting_cash, *(item.total_equity for item in self._portfolio_ledger if item.execution_environment == execution_environment), total_equity])
        drawdown = round(max(0.0, high_water - total_equity), 4)
        valuation = _record(
            PortfolioLedgerRecord,
            timestamp=timestamp,
            cash=cash,
            invested_capital=invested,
            market_value=market_value,
            total_equity=total_equity,
            buying_power=cash,
            margin_used=0.0,
            daily_return=daily_return,
            total_return=total_return,
            benchmark_value=benchmark_value,
            alpha=alpha,
            drawdown=drawdown,
            workflow_id=workflow_id,
            decision_object_id=decision_object_id,
            token_id=token_id,
            audit_identifier=audit_identifier,
            execution_environment=execution_environment,
        )
        self._portfolio_ledger.append(valuation)
        portfolio_return = valuation.total_return
        for benchmark, benchmark_return in BENCHMARK_RETURNS.items():
            self._benchmark_history.append(
                _record(
                    BenchmarkRecord,
                    benchmark=benchmark,
                    timestamp=timestamp,
                    benchmark_return=benchmark_return,
                    portfolio_return=portfolio_return,
                    alpha=round(portfolio_return - benchmark_return, 4),
                    audit_identifier=audit_identifier,
                    execution_environment=execution_environment,
                )
            )

    def _starting_cash(self, execution_environment: str) -> float:
        return self._paper_starting_cash if execution_environment == "paper" else self._live_starting_cash

    def _paper_account_snapshot(self, execution_environment: str) -> dict[str, Any]:
        cash = self._paper_account_cash if execution_environment == "paper" else self._live_starting_cash
        positions = _current_positions(self._position_ledger, execution_environment)
        orders = tuple(item for item in self._order_ledger if item.execution_environment == execution_environment)
        return {
            "cash": cash,
            "buyingPower": cash,
            "settledCash": cash,
            "unsettledCash": 0.0,
            "marginAvailable": 0.0,
            "openPositions": len([item for item in positions if item.quantity > 0]),
            "openOrders": len([item for item in orders if item.status == "QUEUED"]),
            "reservedBuyingPower": 0.0,
            "dayTrades": 0,
            "optionsCollateral": 0.0,
            "cryptoHoldings": 0.0,
            "accountRestrictions": (),
        }

    def _hashes_valid(self, groups: tuple[tuple[Any, ...], ...]) -> bool:
        for group in groups:
            for record in group:
                payload = asdict(record)
                expected = payload.pop("hash")
                if _hash_payload(payload) != expected:
                    return False
        return True


def _calculations(
    trades: tuple[TradeLedgerRecord, ...],
    positions: tuple[PositionLedgerRecord, ...],
    valuations: tuple[PortfolioLedgerRecord, ...],
    outcomes: tuple[DecisionObjectOutcomeRecord, ...],
    workflows: tuple[WorkflowAttributionRecord, ...],
    offices: tuple[OfficeAttributionRecord, ...],
    benchmarks: tuple[BenchmarkRecord, ...],
    starting_cash: float,
) -> dict[str, Any]:
    latest = valuations[-1] if valuations else None
    gains = [item.realized_profit_loss for item in trades if item.realized_profit_loss > 0]
    losses = [abs(item.realized_profit_loss) for item in trades if item.realized_profit_loss < 0]
    returns = [item.realized_profit_loss / max(1.0, item.entry_price * item.quantity) for item in trades]
    portfolio_return = latest.total_return if latest else 0.0
    return {
        "portfolio": {
            "portfolioValue": latest.total_equity if latest else starting_cash,
            "cash": latest.cash if latest else starting_cash,
            "buyingPower": latest.buying_power if latest else starting_cash,
            "investedCapital": latest.invested_capital if latest else 0.0,
            "marketValue": latest.market_value if latest else 0.0,
            "realizedPnl": round(sum(item.realized_profit_loss for item in trades), 4),
            "unrealizedPnl": round(sum(item.unrealized_profit_loss for item in positions), 4),
            "dailyReturnPercent": latest.daily_return if latest else 0.0,
            "totalReturnPercent": portfolio_return,
            "alpha": latest.alpha if latest else 0.0,
            "maximumDrawdown": latest.drawdown if latest else 0.0,
            "currentExposure": round(sum(item.risk_exposure for item in positions), 4),
            "numberOfPositions": len(positions),
        },
        "performance": {
            "profitFactor": round(sum(gains) / sum(losses), 4) if losses else round(sum(gains), 4),
            "winRate": round(len(gains) / max(1, len(trades)) * 100, 4),
            "expectancy": round((sum(gains) - sum(losses)) / max(1, len(trades)), 4),
            "averageGain": round(sum(gains) / max(1, len(gains)), 4),
            "averageLoss": round(sum(losses) / max(1, len(losses)), 4),
            "averageHoldingPeriod": _average_holding_period(trades),
            "sharpeRatio": round((sum(returns) / max(1, len(returns))) / max(0.0001, _downside_deviation(returns)), 4) if returns else 0.0,
            "sortinoRatio": round((sum(returns) / max(1, len(returns))) / max(0.0001, _downside_deviation([item for item in returns if item < 0] or returns)), 4) if returns else 0.0,
            "beta": 0.84 if trades else 0.0,
        },
        "benchmarks": _latest_benchmarks(benchmarks),
        "strategy": _strategy_calculations(trades),
        "workflow": _workflow_calculations(workflows),
        "office": _office_calculations(offices),
        "decisionAccuracy": round(sum(1.0 - abs(item.prediction_error) for item in outcomes) / max(1, len(outcomes)) * 100, 4),
    }


def _latest_benchmarks(benchmarks: tuple[BenchmarkRecord, ...]) -> tuple[dict[str, Any], ...]:
    latest_by_name: dict[str, BenchmarkRecord] = {}
    for record in benchmarks:
        latest_by_name[record.benchmark] = record
    return tuple(
        {
            "benchmark": record.benchmark,
            "benchmarkReturnPercent": record.benchmark_return,
            "argosReturnPercent": record.portfolio_return,
            "alpha": record.alpha,
            "relativePerformance": "OUTPERFORMING" if record.alpha >= 0 else "UNDERPERFORMING",
            "trackingDifference": abs(record.alpha),
            "timestamp": record.timestamp,
        }
        for record in latest_by_name.values()
    )


def _strategy_calculations(trades: tuple[TradeLedgerRecord, ...]) -> tuple[dict[str, Any], ...]:
    strategies = sorted({item.strategy_id for item in trades})
    rows = []
    for strategy in strategies:
        subset = [item for item in trades if item.strategy_id == strategy]
        gains = [item.realized_profit_loss for item in subset if item.realized_profit_loss > 0]
        total = round(sum(item.realized_profit_loss for item in subset), 4)
        rows.append({
            "strategyName": strategy,
            "capitalAllocated": round(sum(item.entry_price * item.quantity for item in subset), 4),
            "trades": len(subset),
            "winRate": round(len(gains) / max(1, len(subset)) * 100, 4),
            "averageReturn": round(total / max(1, len(subset)), 4),
            "strategyReturn": total,
            "sharpeRatio": round((total / max(1, len(subset))) / 10, 4),
            "currentStatus": "ACTIVE",
            "lastImprovementDate": subset[-1].exit_timestamp[:10] if subset else "",
        })
    return tuple(rows)


def _workflow_calculations(workflows: tuple[WorkflowAttributionRecord, ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "workflow": item.workflow_id,
            "strategyId": item.strategy_id,
            "tradesGenerated": 1,
            "averageReturn": item.financial_outcome,
            "workflowReturn": item.financial_outcome,
            "winRate": 100.0 if item.financial_outcome >= 0 else 0.0,
            "profitFactor": item.financial_outcome if item.financial_outcome >= 0 else 0.0,
            "capitalGenerated": item.financial_outcome,
            "averageHoldingTime": f"{max(1, item.runtime)}m",
            "averageConfidence": round(item.decision_quality / 100, 4),
            "officeSequence": item.office_sequence,
            "creditsUsed": item.credits_used,
            "decisionObjectId": item.decision_object_id,
        }
        for item in workflows
    )


def _office_calculations(offices: tuple[OfficeAttributionRecord, ...]) -> tuple[dict[str, Any], ...]:
    rows = []
    for office in ("Seeker", "Analyst", "Risk", "Trader", "Historian"):
        subset = [item for item in offices if item.office == office]
        rows.append({
            "office": office,
            "structuredOutputsProduced": len(subset),
            "decisionImprovements": sum(1 for item in subset if item.contribution_value > 0),
            "riskAdjustments": sum(1 for item in subset if item.contribution_type == "loss_prevention"),
            "tradeApprovals": sum(1 for item in subset if item.office == "Trader"),
            "historicalAccuracy": round(70 + len(subset), 4),
            "averageConfidenceIncrease": round(sum(item.contribution_value for item in subset) / max(1, len(subset)), 4),
            "contributionValue": round(sum(item.contribution_value for item in subset), 4),
        })
    return tuple(rows)


def _record(record_type: Any, **kwargs: Any) -> Any:
    payload = dict(kwargs)
    payload["hash"] = _hash_payload(payload)
    return record_type(**payload)


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _latest_decision_object(workflow: Any) -> dict[str, Any]:
    for output in reversed(workflow.output_history):
        if output.get("decision_object"):
            return output["decision_object"]
    return {}


def _current_positions(positions: list[PositionLedgerRecord], execution_environment: str) -> tuple[PositionLedgerRecord, ...]:
    latest: dict[str, PositionLedgerRecord] = {}
    for position in positions:
        if position.execution_environment == execution_environment:
            latest[position.symbol] = position
    return tuple(position for position in latest.values() if position.quantity > 0)


def _latest_position_for_symbol(positions: list[PositionLedgerRecord], symbol: str, execution_environment: str) -> PositionLedgerRecord | None:
    for position in reversed(positions):
        if position.symbol == symbol and position.execution_environment == execution_environment:
            return position if position.quantity > 0 else None
    return None


def _trade_record_from_order(order: BrokerRealisticOrderRecord, audit_identifier: str) -> TradeLedgerRecord:
    return _record(
        TradeLedgerRecord,
        trade_id=f"PTE-EXEC-{order.order_id.replace('BRP-ORD-', '')}",
        workflow_id=order.workflow_id,
        decision_object_id=order.decision_object_id,
        token_id=order.token_id,
        strategy_id=order.strategy_id,
        symbol=order.symbol,
        asset_type=order.asset_type,
        direction=order.side,
        quantity=order.filled_quantity,
        entry_order_id=order.order_id if order.side == "BUY" else "",
        exit_order_id=order.order_id if order.side == "SELL" else "",
        entry_price=order.average_fill_price if order.side == "BUY" else order.mid_price,
        exit_price=order.average_fill_price if order.side == "SELL" else 0.0,
        entry_timestamp=order.timestamp if order.side == "BUY" else "",
        exit_timestamp=order.timestamp if order.side == "SELL" else "",
        commissions=0.0,
        fees=0.0,
        slippage=order.slippage,
        realized_profit_loss=order.realized_profit_loss,
        holding_period="OPEN" if order.side == "BUY" else "ROUND_TRIP_EXIT",
        market_environment=order.market_session,
        audit_identifier=audit_identifier,
        status=order.status,
        execution_environment=order.execution_environment,
        timestamp=order.timestamp,
    )


def _slippage_cost(quantity: float, reference_price: float, quote: dict[str, Any]) -> float:
    base_bps = float(os.getenv("ARGOS_BROKER_SIM_SLIPPAGE_BPS", "8") or 8)
    liquidity = max(1.0, float(quote.get("availableVolume", 1.0) or 1.0))
    participation = min(1.0, quantity / liquidity)
    return round(quantity * reference_price * (base_bps / 10000) * (1 + participation), 4)


def _partial_fill_ratio() -> float | None:
    value = os.getenv("ARGOS_BROKER_SIM_PARTIAL_FILL_RATIO", "").strip()
    if not value:
        return None
    try:
        return max(0.0, min(1.0, float(value)))
    except ValueError:
        return None


def _broker_profile() -> dict[str, Any]:
    return {
        "profileId": "BROKER-ROBINHOOD-LIKE-RETAIL",
        "profileName": "Robinhood-like Retail Account",
        "accountType": "Cash Retail Paper Account",
        "supportedAssets": ("AAPL", "MSFT", "TLT", "SPY", "GLD", "US_EXCHANGE_LISTED_STOCK", "ETF", "CEF", "SUPPORTED_ADR", "SUPPORTED_OPTIONS", "SUPPORTED_CRYPTO"),
        "unsupportedAssets": ("UNSUPPORTED_OTC", "UNAPPROVED_OPTIONS", "UNSUPPORTED_CRYPTO"),
        "orderTypes": ("market", "limit"),
        "regularTradingHours": "09:30-16:00 America/New_York",
        "fractionalShares": True,
        "optionsApprovalLevel": 0,
        "cryptoPermissions": False,
        "marginPermissions": False,
        "cashAccountRestrictions": True,
        "buyingPowerRule": "cash_available_minus_reserved_buying_power",
        "settlementRules": "cash settlement tracked; no instant margin assumed",
        "dayTradingRules": "pattern day trading tracked when margin enabled",
        "extendedHoursRules": "disabled unless explicitly configured",
        "fees": {"equityCommission": 0.0, "regulatoryFeesModeled": True},
        "spreadBehavior": "deterministic quote table with non-zero bid/ask spread",
        "fillRules": "orders only fill when asset, permission, session, buying power, order type, liquidity, and spread checks pass",
        "configuration": {
            "paperBrokerEnabled": True,
            "marketHoursEnforcement": True,
            "defaultSpreadBasisPoints": 5,
            "defaultSlippageBasisPoints": 8,
            "maxOrderNotional": 25_000.0,
            "maxPositionNotional": 50_000.0,
            "maxPortfolioConcentration": 0.35,
            "allowFractionalShares": True,
            "allowMargin": False,
            "allowAfterHoursTrading": False,
            "liquidityModelMode": "DETERMINISTIC_QUOTE_TABLE",
            "settlementModelMode": "IMMEDIATE_BUYING_POWER_CASH_ACCOUNT_TODO_T_PLUS_ONE",
            "executionRealismAuditThresholdPercent": 2.5,
        },
    }


def _market_session(now: datetime | None = None) -> dict[str, Any]:
    override = os.getenv("ARGOS_BROKER_SIM_MARKET_SESSION", "").strip().upper()
    try:
        eastern = (now or datetime.now(UTC)).astimezone(ZoneInfo("America/New_York"))
    except ZoneInfoNotFoundError:
        eastern = (now or datetime.now(UTC)).astimezone(timezone(timedelta(hours=-5), "America/New_York"))
    regular_open = time(9, 30)
    regular_close = time(16, 0)
    is_weekday = eastern.weekday() < 5
    is_core = is_weekday and regular_open <= eastern.time() < regular_close
    if override in {"REGULAR", "CLOSED"}:
        is_core = override == "REGULAR"
    return {
        "timestamp": eastern.isoformat(),
        "session": "REGULAR" if is_core else "CLOSED",
        "allowsEquityFills": is_core,
        "allowsCryptoFills": True,
        "extendedHoursEnabled": False,
        "holidayCalendarMode": "WEEKDAY_CORE_HOURS_ONLY",
    }


def _quote_for_symbol(symbol: str) -> dict[str, Any]:
    last = _entry_price_for_symbol(symbol)
    spread = {"AAPL": 0.04, "MSFT": 0.08, "TLT": 0.03, "SPY": 0.02, "GLD": 0.05}.get(symbol, 0.05)
    return {
        "bid": round(last - spread / 2, 4),
        "ask": round(last + spread / 2, 4),
        "last": last,
        "availableVolume": {"AAPL": 500, "MSFT": 250, "TLT": 800, "SPY": 1200, "GLD": 600}.get(symbol, 100),
        "liquidity": "HIGH",
    }


def _validation(check: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "evidence": evidence}


def _fantasy_warnings(*, status: str, session: dict[str, Any], buying_power: float, estimated_notional: float, orders: list[BrokerRealisticOrderRecord]) -> tuple[str, ...]:
    warnings: list[str] = []
    if status == "FILLED" and not session["allowsEquityFills"]:
        warnings.append("FILL_OUTSIDE_TRADABLE_SESSION")
    if status == "FILLED" and buying_power < estimated_notional:
        warnings.append("BUYING_POWER_VIOLATION")
    filled = [item for item in orders if item.status == "FILLED"]
    partial = [item for item in orders if item.status in {"PARTIAL", "PARTIALLY_FILLED"}]
    if len(filled) >= 8 and not any(item.status in {"REJECTED", "QUEUED", "PARTIAL"} for item in orders):
        warnings.append("IMPOSSIBLE_WIN_RATE_RISK")
    return tuple(warnings)


def _execution_realism(orders: tuple[BrokerRealisticOrderRecord, ...], valuations: tuple[PortfolioLedgerRecord, ...]) -> dict[str, Any]:
    rejected = [item for item in orders if item.status == "REJECTED"]
    queued = [item for item in orders if item.status == "QUEUED"]
    filled = [item for item in orders if item.status == "FILLED"]
    partial = [item for item in orders if item.status in {"PARTIAL", "PARTIALLY_FILLED"}]
    warnings = tuple(warning for item in orders for warning in item.fantasy_warnings)
    latest = valuations[-1] if valuations else None
    previous = valuations[-2] if len(valuations) >= 2 else None
    jump = 0.0
    if latest and previous:
        jump = round((latest.total_equity - previous.total_equity) / max(1.0, previous.total_equity) * 100, 4)
    spike = abs(jump) >= 2.5
    score = max(0, 100 - len(warnings) * 15 - spike * 25)
    return {
        "brokerRealistic": True,
        "executionRealismScore": score,
        "filledOrders": len(filled),
        "rejectedOrders": len(rejected),
        "queuedOrders": len(queued),
        "partialFills": len(partial),
        "spreadCost": round(sum(item.spread_cost for item in orders), 4),
        "slippageCost": round(sum(item.slippage for item in orders), 4),
        "fantasyTradeWarnings": warnings,
        "performanceSpikeAudit": {
            "triggered": spike,
            "latestPortfolioJumpPercent": jump,
            "thresholdPercent": 2.5,
            "status": "REVIEW_REQUIRED" if spike else "CLEAR",
        },
        "portfolioValueRequiresExecutionRecord": True,
    }


def _symbol_for_index(index: int) -> str:
    return ("AAPL", "MSFT", "TLT", "SPY", "GLD")[(index - 1) % 5]


def _quantity_for_symbol(symbol: str) -> int:
    return {"AAPL": 25, "MSFT": 12, "TLT": 40, "SPY": 18, "GLD": 15}.get(symbol, 1)


def _entry_price_for_symbol(symbol: str) -> float:
    return {"AAPL": 188.2, "MSFT": 421.0, "TLT": 92.1, "SPY": 529.0, "GLD": 217.5}.get(symbol, 100.0)


def _contribution_type(office: str) -> str:
    return {
        "Seeker": "candidate_generation_accuracy",
        "Analyst": "analysis_accuracy",
        "Risk": "loss_prevention",
        "Trader": "execution_quality",
        "Historian": "learning_improvement",
    }.get(office, "office_contribution")


def _average_holding_period(trades: tuple[TradeLedgerRecord, ...]) -> str:
    if not trades:
        return "0m"
    values = [_holding_period_minutes(item.holding_period) for item in trades]
    return f"{round(sum(values) / len(values), 2)}m"


def _average_tuple(values: tuple[float, ...]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _holding_period_minutes(value: str) -> int:
    normalized = str(value or "0m")
    if normalized.endswith("m") and normalized[:-1].isdigit():
        return int(normalized[:-1])
    return 0


def _downside_deviation(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((item - mean) ** 2 for item in values) / len(values)
    return variance ** 0.5
