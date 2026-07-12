"""Deterministic exit decision records for active ARGOS positions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .position_registry import PositionObject, PositionRegistry


SUPPORTED_EXIT_DECISIONS = (
    "hold",
    "exit_full",
    "exit_partial",
    "tighten_stop",
    "request_ai_review",
    "request_commander_review",
    "emergency_exit",
)


@dataclass(frozen=True)
class ExitDecisionConfig:
    """Deterministic configuration for EO-XC."""

    engine_enabled: bool = True
    profit_target_behavior: str = "exit_full"
    stop_loss_behavior: str = "exit_full"
    trailing_stop_behavior: str = "exit_full"
    stale_data_policy: str = "commander_review"
    partial_exit_allowed: bool = True
    partial_exit_percent: float = 0.5
    large_adverse_move_behavior: str = "exit_full"
    strategy_invalidation_behavior: str = "request_ai_review"
    market_regime_change_behavior: str = "request_ai_review"
    minimum_confidence_for_exit: float = 0.55
    risk_threshold: float = 0.85
    max_holding_minutes: int = 390
    concentration_threshold: float = 0.2
    ai_review_allowed: bool = True
    commander_review_required_threshold: float = 0.75


@dataclass(frozen=True)
class ExitDecisionRecord:
    """Immutable decision that may later be executed by EO-XD."""

    exit_decision_id: str
    position_id: str
    workflow_id: str
    decision_object_id: str
    snapshot_id: str
    timestamp: str
    symbol: str
    asset_type: str
    current_price: float
    quantity: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    decision: str
    recommended_action: str
    recommended_quantity: float
    recommended_percent: float
    urgency: str
    trigger_type: str
    trigger_evidence: dict[str, Any]
    strategy_rule_id: str
    risk_rule_id: str
    commander_override_id: str
    deterministic_reasoning: tuple[str, ...]
    confidence: float
    ai_review_required: bool
    ai_review_reason: str
    next_engine: str
    audit_reference: str


class ExitDecisionEngine:
    """Evaluate active positions for deterministic exit decisions."""

    def __init__(self, config: ExitDecisionConfig | None = None) -> None:
        self._config = config or ExitDecisionConfig()
        self._records: list[ExitDecisionRecord] = []
        self._last_decision_by_position: dict[str, str] = {}

    def evaluate(
        self,
        *,
        position_registry: PositionRegistry,
        position_surveillance: dict[str, Any],
        timestamp_utc: str,
        strategy_package_manager: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        risk_context: dict[str, Any] | None = None,
        commander_overrides: tuple[dict[str, Any], ...] = (),
        mutate_registry: bool = True,
    ) -> dict[str, Any]:
        """Evaluate active positions once and return immediately."""
        config = self._resolved_config(enterprise_configuration_registry)
        active_positions = position_registry.active_positions()
        latest_snapshots = _latest_snapshot_by_position(position_surveillance)
        escalations = _escalations_by_position(position_surveillance)
        pass_records: list[ExitDecisionRecord] = []

        for position in active_positions:
            snapshot = latest_snapshots.get(position.position_id)
            record = self._decision_record(
                position=position,
                snapshot=snapshot,
                escalations=escalations.get(position.position_id, ()),
                config=config,
                timestamp=timestamp_utc,
                strategy_package_manager=strategy_package_manager or {},
                risk_context=risk_context or {},
                commander_overrides=commander_overrides,
            )
            if self._should_append(record):
                self._records.append(record)
                self._last_decision_by_position[position.position_id] = record.decision
                pass_records.append(record)
                current_position = position_registry.position(position.position_id)
                if (
                    mutate_registry
                    and record.decision not in {"hold", "request_ai_review", "request_commander_review"}
                    and current_position.exit_recommendation != record.decision
                ):
                    position_registry.recommend_exit(
                        position.position_id,
                        record.decision,
                        reason=f"EO-XC {record.trigger_type}",
                        source="ExitDecisionEngine",
                    )
            else:
                pass_records.append(record)

        return self.snapshot(timestamp_utc=timestamp_utc, latest_decisions=tuple(pass_records), config=config)

    def snapshot(self, *, timestamp_utc: str, latest_decisions: tuple[ExitDecisionRecord, ...] = (), config: ExitDecisionConfig | None = None) -> dict[str, Any]:
        resolved = config or self._config
        return {
            "engineName": "Exit Decision Engine",
            "engineeringOrder": "EO-XC",
            "constitutionalMission": "Decide whether active capital should remain at risk without executing orders.",
            "supportedDecisions": SUPPORTED_EXIT_DECISIONS,
            "lawVII": {
                "executesWorkflows": False,
                "workflowTokenOwnership": "NEVER",
                "placesTrades": False,
                "mutatesPortfolioLedgers": False,
                "positionLifecycleMutationGateway": "PositionRegistry",
            },
            "lawVIII": {
                "routineAiCallsUsed": 0,
                "deterministicExitEvaluation": True,
                "aiReviewMarkedOnly": True,
            },
            "configuration": asdict(resolved),
            "exitDecisionRecords": tuple(asdict(item) for item in self._records),
            "latestDecisions": tuple(asdict(item) for item in latest_decisions),
            "metrics": {
                "recordsCreated": len(self._records),
                "latestDecisionCount": len(latest_decisions),
                "latestActionableCount": sum(1 for item in latest_decisions if item.decision not in {"hold", "request_ai_review", "request_commander_review"}),
                "ordersExecuted": 0,
            },
            "diagnostics": {
                "backgroundWorkerActive": False,
                "returnsImmediately": True,
                "aiCallsUsed": 0,
                "executionDeferredTo": "EO-XD Broker-Realistic Exit Execution",
                "recordAppendOnly": True,
                "timestampUtc": timestamp_utc,
            },
        }

    def _decision_record(
        self,
        *,
        position: PositionObject,
        snapshot: dict[str, Any] | None,
        escalations: tuple[dict[str, Any], ...],
        config: ExitDecisionConfig,
        timestamp: str,
        strategy_package_manager: dict[str, Any],
        risk_context: dict[str, Any],
        commander_overrides: tuple[dict[str, Any], ...],
    ) -> ExitDecisionRecord:
        trigger = self._trigger(position, snapshot, escalations, config, strategy_package_manager, risk_context, commander_overrides)
        quantity = float(snapshot.get("quantity", position.quantity) if snapshot else position.quantity)
        decision = trigger["decision"]
        recommended_percent = _recommended_percent(decision, trigger, config)
        recommended_quantity = round(quantity * recommended_percent, 4)
        audit = f"EO-XC-AUD-{len(self._records) + 1:06d}-{position.position_id}"
        return ExitDecisionRecord(
            exit_decision_id=f"EXD-{len(self._records) + 1:06d}",
            position_id=position.position_id,
            workflow_id=position.workflow_id,
            decision_object_id=position.decision_object_id,
            snapshot_id=str(snapshot.get("snapshot_id", "")) if snapshot else "",
            timestamp=timestamp,
            symbol=position.symbol,
            asset_type=position.asset_type,
            current_price=float(snapshot.get("current_price", position.current_price) if snapshot else position.current_price),
            quantity=quantity,
            unrealized_pnl=float(snapshot.get("unrealized_pnl", position.unrealized_pnl) if snapshot else position.unrealized_pnl),
            unrealized_pnl_percent=float(snapshot.get("unrealized_pnl_percent", 0.0) if snapshot else 0.0),
            decision=decision,
            recommended_action=_recommended_action(decision),
            recommended_quantity=recommended_quantity,
            recommended_percent=recommended_percent,
            urgency=str(trigger["urgency"]),
            trigger_type=str(trigger["trigger_type"]),
            trigger_evidence=dict(trigger["evidence"]),
            strategy_rule_id=str(trigger.get("strategy_rule_id", "")),
            risk_rule_id=str(trigger.get("risk_rule_id", "")),
            commander_override_id=str(trigger.get("commander_override_id", "")),
            deterministic_reasoning=tuple(trigger["reasoning"]),
            confidence=float(trigger["confidence"]),
            ai_review_required=bool(trigger.get("ai_review_required", False)),
            ai_review_reason=str(trigger.get("ai_review_reason", "")),
            next_engine="EO-XD Broker-Realistic Exit Execution" if decision in {"exit_full", "exit_partial", "emergency_exit"} else "Trader Position Monitoring",
            audit_reference=audit,
        )

    def _trigger(
        self,
        position: PositionObject,
        snapshot: dict[str, Any] | None,
        escalations: tuple[dict[str, Any], ...],
        config: ExitDecisionConfig,
        strategy_package_manager: dict[str, Any],
        risk_context: dict[str, Any],
        commander_overrides: tuple[dict[str, Any], ...],
    ) -> dict[str, Any]:
        override = _commander_override_for_position(position.position_id, commander_overrides)
        if override:
            return _trigger(
                _override_decision(override),
                "commander_directed",
                "commander_manual_exit_request",
                {"override": override},
                ("Commander override took priority over deterministic rules.",),
                confidence=1.0,
                commander_override_id=str(override.get("overrideId", override.get("override_id", "COMMANDER-OVERRIDE"))),
            )
        if risk_context.get("emergencyRiskOverride") or risk_context.get("emergency_halt"):
            return _trigger("emergency_exit", "emergency", "emergency_risk_override", dict(risk_context), ("Risk context declared emergency override.",), confidence=1.0, risk_rule_id="RISK-EMERGENCY-OVERRIDE")
        if not snapshot:
            return _trigger("request_commander_review", "medium", "missing_surveillance_snapshot", {"positionId": position.position_id}, ("No surveillance snapshot was available; execution is not authorized.",), confidence=0.4)

        events = set(snapshot.get("detected_events", ()))
        strategy_flags = _strategy_flags(position, strategy_package_manager)
        if "strategy_invalidation" in strategy_flags:
            decision = config.strategy_invalidation_behavior
            return _ai_or_review(decision, "strategy_invalidation_flag", {"strategyFlags": strategy_flags}, "Strategy invalidation requires interpretive review.")
        if "market_regime_change" in strategy_flags:
            decision = config.market_regime_change_behavior
            return _ai_or_review(decision, "market_regime_change_flag", {"strategyFlags": strategy_flags}, "Market regime change may require interpretation.")
        if "stop_loss_reached" in events:
            return _trigger(config.stop_loss_behavior, "high", "stop_loss_reached", {"snapshot": snapshot}, ("Stop loss reached; capital preservation rule requires exit decision.",), confidence=0.96, risk_rule_id="RISK-STOP-LOSS")
        if "trailing_stop_reached" in events:
            return _trigger(config.trailing_stop_behavior, "high", "trailing_stop_reached", {"snapshot": snapshot}, ("Trailing stop reached; exit decision produced.",), confidence=0.94, strategy_rule_id="STRAT-TRAILING-STOP")
        if "profit_target_reached" in events:
            decision = "exit_partial" if config.partial_exit_allowed and config.profit_target_behavior == "exit_partial" else config.profit_target_behavior
            return _trigger(decision, "medium", "profit_target_reached", {"snapshot": snapshot}, ("Profit target reached; strategy profit-taking rule fired.",), confidence=0.9, strategy_rule_id="STRAT-PROFIT-TARGET")
        if _minutes_in_trade(str(snapshot.get("time_in_trade", ""))) >= config.max_holding_minutes:
            return _trigger("exit_full", "medium", "max_holding_period_exceeded", {"timeInTrade": snapshot.get("time_in_trade")}, ("Configured maximum holding period exceeded.",), confidence=0.86, strategy_rule_id="STRAT-TIME-STOP")
        if float(snapshot.get("risk_score", position.current_risk) or 0.0) >= config.risk_threshold:
            return _trigger("emergency_exit", "high", "risk_threshold_exceeded", {"riskScore": snapshot.get("risk_score"), "threshold": config.risk_threshold}, ("Risk threshold exceeded deterministic limit.",), confidence=0.92, risk_rule_id="RISK-THRESHOLD")
        if _position_concentration(position, risk_context) >= config.concentration_threshold:
            return _trigger("exit_partial", "medium", "position_concentration_exceeded", {"concentration": _position_concentration(position, risk_context), "threshold": config.concentration_threshold}, ("Position concentration exceeded configured limit.",), confidence=0.82, risk_rule_id="RISK-CONCENTRATION")
        if snapshot.get("surveillance_status") == "DEGRADED" or "market_data_missing" in events or any(item.get("event_type") == "market_data_missing" for item in escalations):
            decision = "request_commander_review" if config.stale_data_policy == "commander_review" else "hold"
            return _trigger(decision, "medium", "market_data_degraded", {"snapshot": snapshot}, ("Market data quality degraded; sell execution deferred pending review.",), confidence=0.48)
        if "large_adverse_move" in events or "unusual_unrealized_loss" in events:
            return _trigger(config.large_adverse_move_behavior, "high", "large_adverse_move", {"snapshot": snapshot}, ("Large adverse move crossed deterministic threshold.",), confidence=0.88, risk_rule_id="RISK-LARGE-ADVERSE-MOVE")
        return _trigger("hold", "low", "no_exit_trigger", {"snapshot": snapshot}, ("No deterministic exit trigger was present.",), confidence=0.78)

    def _should_append(self, record: ExitDecisionRecord) -> bool:
        if self._last_decision_by_position.get(record.position_id) == record.decision:
            return False
        return True

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> ExitDecisionConfig:
        if not enterprise_configuration_registry:
            return self._config
        values = asdict(self._config)
        name_map = {
            "Exit Decision Engine Enabled": "engine_enabled",
            "Exit Decision Profit Target Behavior": "profit_target_behavior",
            "Exit Decision Stop Loss Behavior": "stop_loss_behavior",
            "Exit Decision Partial Exit Allowed": "partial_exit_allowed",
            "Exit Decision Partial Exit Percent": "partial_exit_percent",
            "Exit Decision Risk Threshold": "risk_threshold",
            "Exit Decision Max Holding Minutes": "max_holding_minutes",
        }
        for entry in enterprise_configuration_registry.get("configurationRegistry", ()):
            key = name_map.get(str(entry.get("configurationName", "")))
            if key:
                try:
                    values[key] = type(values[key])(entry.get("configuredValue"))
                except (TypeError, ValueError):
                    values[key] = entry.get("configuredValue")
        return ExitDecisionConfig(**values)


def _latest_snapshot_by_position(position_surveillance: dict[str, Any]) -> dict[str, dict[str, Any]]:
    snapshots = tuple(position_surveillance.get("latestSnapshots", ())) or tuple(position_surveillance.get("surveillanceSnapshots", ()))
    latest: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        latest[str(snapshot.get("position_id", ""))] = snapshot
    return latest


def _escalations_by_position(position_surveillance: dict[str, Any]) -> dict[str, tuple[dict[str, Any], ...]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for escalation in position_surveillance.get("latestEscalations", ()) or position_surveillance.get("escalations", ()):
        grouped.setdefault(str(escalation.get("position_id", "")), []).append(escalation)
    return {key: tuple(value) for key, value in grouped.items()}


def _trigger(decision: str, urgency: str, trigger_type: str, evidence: dict[str, Any], reasoning: tuple[str, ...], *, confidence: float, strategy_rule_id: str = "", risk_rule_id: str = "", commander_override_id: str = "") -> dict[str, Any]:
    return {
        "decision": decision if decision in SUPPORTED_EXIT_DECISIONS else "request_commander_review",
        "urgency": urgency,
        "trigger_type": trigger_type,
        "evidence": evidence,
        "reasoning": reasoning,
        "confidence": confidence,
        "strategy_rule_id": strategy_rule_id,
        "risk_rule_id": risk_rule_id,
        "commander_override_id": commander_override_id,
        "ai_review_required": decision == "request_ai_review",
        "ai_review_reason": "Interpretive review marked; no AI call executed." if decision == "request_ai_review" else "",
    }


def _ai_or_review(decision: str, trigger_type: str, evidence: dict[str, Any], reason: str) -> dict[str, Any]:
    if decision == "exit_full":
        return _trigger("exit_full", "high", trigger_type, evidence, (reason, "Strategy rules demanded deterministic full exit."), confidence=0.8, strategy_rule_id="STRAT-INVALIDATION")
    return _trigger("request_ai_review", "medium", trigger_type, evidence, (reason, "AI review is marked only; no AI execution occurred."), confidence=0.62, strategy_rule_id="STRAT-REVIEW")


def _recommended_action(decision: str) -> str:
    return {
        "hold": "KEEP_POSITION_OPEN",
        "exit_full": "PREPARE_FULL_EXIT_ORDER",
        "exit_partial": "PREPARE_PARTIAL_EXIT_ORDER",
        "tighten_stop": "PREPARE_STOP_ADJUSTMENT",
        "request_ai_review": "REQUEST_INTERPRETIVE_REVIEW",
        "request_commander_review": "REQUEST_COMMANDER_REVIEW",
        "emergency_exit": "PREPARE_EMERGENCY_EXIT_ORDER",
    }.get(decision, "REQUEST_COMMANDER_REVIEW")


def _recommended_percent(decision: str, trigger: dict[str, Any], config: ExitDecisionConfig) -> float:
    if decision in {"exit_full", "emergency_exit"}:
        return 1.0
    if decision == "exit_partial":
        evidence = trigger.get("evidence", {})
        override = evidence.get("override", {}) if isinstance(evidence, dict) else {}
        return round(max(0.0, min(1.0, float(override.get("recommendedPercent", override.get("recommended_percent", config.partial_exit_percent)) or config.partial_exit_percent))), 4)
    return 0.0


def _commander_override_for_position(position_id: str, overrides: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    for override in reversed(overrides):
        if str(override.get("positionId", override.get("position_id", ""))) == position_id:
            return override
    return {}


def _override_decision(override: dict[str, Any]) -> str:
    action = str(override.get("action", override.get("decision", ""))).lower()
    return {
        "exit_full": "exit_full",
        "exit_partial": "exit_partial",
        "hold": "hold",
        "cancel_exit": "hold",
        "request_review": "request_commander_review",
        "request_commander_review": "request_commander_review",
    }.get(action, "exit_full")


def _strategy_flags(position: PositionObject, strategy_package_manager: dict[str, Any]) -> set[str]:
    flags = set()
    context = position.market_context if isinstance(position.market_context, dict) else {}
    if context.get("strategyInvalidation") or context.get("strategy_invalidation"):
        flags.add("strategy_invalidation")
    if context.get("marketRegimeChanged") or context.get("market_regime_change"):
        flags.add("market_regime_change")
    for rule in strategy_package_manager.get("exitRules", ()):
        if rule.get("positionId") == position.position_id and rule.get("flag"):
            flags.add(str(rule["flag"]))
    return flags


def _position_concentration(position: PositionObject, risk_context: dict[str, Any]) -> float:
    if "positionConcentration" in risk_context:
        return float(risk_context.get("positionConcentration") or 0.0)
    portfolio_value = float(risk_context.get("portfolioValue", 0.0) or 0.0)
    if portfolio_value <= 0:
        return 0.0
    return position.current_value / portfolio_value


def _minutes_in_trade(value: str) -> int:
    if value.endswith("m"):
        try:
            return int(value[:-1])
        except ValueError:
            return 0
    return 0
