"""Enterprise Grand Strategy Engine for ARGOS EO-BX."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any


class StrategicPosture(str, Enum):
    PRESERVATION = "preservation"
    DEFENSIVE = "defensive"
    CAUTIOUS_GROWTH = "cautious_growth"
    BALANCED_GROWTH = "balanced_growth"
    OPPORTUNISTIC = "opportunistic"
    AGGRESSIVE_RESEARCH = "aggressive_research"
    RECOVERY = "recovery"
    CALIBRATION_ONLY = "calibration_only"
    MANAGE_EXISTING_POSITIONS_ONLY = "manage_existing_positions_only"
    NO_NEW_RISK = "no_new_risk"
    HALTED = "halted"


@dataclass(frozen=True)
class GrandStrategyConfig:
    grand_strategy_engine_enabled: bool = True
    supported_planning_horizons: tuple[str, ...] = ("immediate", "daily", "weekly", "monthly", "quarterly", "annual", "multi_year")
    default_strategic_posture: str = StrategicPosture.PRESERVATION.value
    conservative_missing_intent_policy: bool = True
    required_cash_reserve_percent: float = 0.15
    maximum_drawdown_tolerance: float = 0.08
    daily_loss_limit_percent: float = 0.02
    weekly_loss_limit_percent: float = 0.04
    experimental_capital_cap: float = 0.03
    maximum_deployable_capital_percent: float = 0.35
    acceptable_composite_risk: float = 55.0
    critical_risk_threshold: float = 80.0
    minimum_reality_fidelity: float = 80.0
    unsafe_reality_fidelity: float = 60.0
    minimum_learning_reliability: float = 80.0
    minimum_closed_trade_sample: int = 30
    minimum_reproducibility_score: float = 80.0
    minimum_black_swan_survival_score: float = 65.0
    maximum_monte_carlo_ruin_probability: float = 0.05
    maximum_ai_daily_credit_policy: float = 25.0
    maximum_strategy_count: int = 4
    maximum_concurrent_experiments: int = 3
    material_revision_threshold: float = 10.0
    optional_narrative_enabled: bool = False


@dataclass(frozen=True)
class CommanderIntentRecord:
    intent_id: str
    mission: str
    capital_objective: str
    acceptable_drawdown: float
    acceptable_risk: float
    operating_mode: str
    desired_deployment_pace: str
    preferred_markets: tuple[str, ...]
    prohibited_markets: tuple[str, ...]
    liquidity_requirements: str
    time_horizon: str
    research_appetite: str
    experiment_appetite: str
    credit_budget: float
    required_cash_reserve: float
    autonomy_limits: tuple[str, ...]
    live_trading_permission_state: str
    review_cadence: str
    strategic_priorities: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class GrandStrategyRecord:
    grand_strategy_id: str
    strategy_version: str
    prior_strategy_version: str
    effective_from: str
    effective_until: str
    created_at: str
    planning_horizon: str
    commander_intent_reference: str
    constitutional_reference: str
    enterprise_mission: str
    strategic_posture: str
    primary_objectives: tuple[dict[str, Any], ...]
    secondary_objectives: tuple[dict[str, Any], ...]
    prohibited_actions: tuple[dict[str, Any], ...]
    capital_preservation_policy: dict[str, Any]
    benchmark_objective: dict[str, Any]
    return_objective: dict[str, Any]
    drawdown_tolerance: dict[str, Any]
    risk_tolerance: dict[str, Any]
    deployment_policy: dict[str, Any]
    cash_reserve_policy: dict[str, Any]
    strategy_portfolio_policy: dict[str, Any]
    research_priorities: tuple[dict[str, Any], ...]
    experiment_priorities: tuple[dict[str, Any], ...]
    capability_priorities: tuple[dict[str, Any], ...]
    operational_maturity_targets: dict[str, Any]
    AI_usage_policy: dict[str, Any]
    credit_budget_policy: dict[str, Any]
    market_participation_policy: dict[str, Any]
    data_quality_requirements: dict[str, Any]
    reality_fidelity_requirements: dict[str, Any]
    learning_reliability_requirements: dict[str, Any]
    live_readiness_policy: dict[str, Any]
    escalation_conditions: tuple[dict[str, Any], ...]
    review_triggers: tuple[dict[str, Any], ...]
    success_metrics: tuple[dict[str, Any], ...]
    failure_conditions: tuple[dict[str, Any], ...]
    confidence: float
    degraded_inputs: tuple[str, ...]
    evidence_references: tuple[dict[str, Any], ...]
    deterministic_reasoning: tuple[str, ...]
    conflicts: tuple[dict[str, Any], ...]
    revision_reason: str
    changed_policies: tuple[str, ...]
    audit_reference: str
    immutable: bool
    hash: str


class EnterpriseGrandStrategyEngine:
    """Deterministic long-horizon policy synthesis for ARGOS."""

    def __init__(self, config: GrandStrategyConfig | None = None) -> None:
        self._config = config or GrandStrategyConfig()
        self._records: list[GrandStrategyRecord] = []
        self._records_by_fingerprint: dict[str, GrandStrategyRecord] = {}

    def generate(
        self,
        *,
        timestamp_utc: str,
        planning_horizon: str = "monthly",
        commander_intent: dict[str, Any] | None = None,
        sources: dict[str, Any],
    ) -> dict[str, Any]:
        config = self._resolved_config(sources.get("enterpriseConfigurationRegistry") or sources.get("enterprise_configuration_registry") or {})
        intent = self._intent(commander_intent, sources, config)
        evidence = _evidence(sources)
        posture, reasoning = self._posture(intent, evidence, config)
        maturity = self._maturity(evidence, config)
        live = self._live_readiness(intent, evidence, maturity, config)
        confidence, degraded = self._confidence(intent, evidence, maturity, config)
        conflicts = self._conflicts(intent, evidence, posture)
        policies = self._policies(intent, evidence, posture, maturity, live, config)
        objectives = self._objectives(intent, evidence, posture, config)
        record_basis = {
            "intent": asdict(intent),
            "planning_horizon": planning_horizon,
            "posture": posture,
            "policies": policies,
            "objectives": objectives,
            "evidence": _stable_evidence(evidence),
            "conflicts": conflicts,
        }
        fingerprint = _hash(record_basis)
        existing = self._records_by_fingerprint.get(fingerprint)
        if existing:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=existing)

        prior = self._records[-1] if self._records else None
        version = f"GS-{len(self._records) + 1:04d}"
        changed = _changed_policies(prior, policies, posture)
        record_payload = {
            "grand_strategy_id": f"GSR-{len(self._records) + 1:06d}",
            "strategy_version": version,
            "prior_strategy_version": prior.strategy_version if prior else "",
            "effective_from": timestamp_utc,
            "effective_until": "",
            "created_at": timestamp_utc,
            "planning_horizon": planning_horizon if planning_horizon in config.supported_planning_horizons else "monthly",
            "commander_intent_reference": intent.intent_id,
            "constitutional_reference": "ARGOS Constitution / LAW VII / LAW VIII",
            "enterprise_mission": intent.mission,
            "strategic_posture": posture,
            "primary_objectives": objectives["primary"],
            "secondary_objectives": objectives["secondary"],
            "prohibited_actions": policies["prohibited_actions"],
            "capital_preservation_policy": policies["capital_preservation"],
            "benchmark_objective": policies["benchmark_objective"],
            "return_objective": policies["return_objective"],
            "drawdown_tolerance": policies["drawdown_tolerance"],
            "risk_tolerance": policies["risk_tolerance"],
            "deployment_policy": policies["deployment_policy"],
            "cash_reserve_policy": policies["cash_reserve_policy"],
            "strategy_portfolio_policy": policies["strategy_portfolio_policy"],
            "research_priorities": policies["research_priorities"],
            "experiment_priorities": policies["experiment_priorities"],
            "capability_priorities": policies["capability_priorities"],
            "operational_maturity_targets": maturity,
            "AI_usage_policy": policies["ai_usage_policy"],
            "credit_budget_policy": policies["credit_budget_policy"],
            "market_participation_policy": policies["market_participation_policy"],
            "data_quality_requirements": policies["data_quality_requirements"],
            "reality_fidelity_requirements": policies["reality_fidelity_requirements"],
            "learning_reliability_requirements": policies["learning_reliability_requirements"],
            "live_readiness_policy": live,
            "escalation_conditions": policies["escalation_conditions"],
            "review_triggers": policies["review_triggers"],
            "success_metrics": policies["success_metrics"],
            "failure_conditions": policies["failure_conditions"],
            "confidence": confidence,
            "degraded_inputs": degraded,
            "evidence_references": policies["evidence_references"],
            "deterministic_reasoning": reasoning,
            "conflicts": conflicts,
            "revision_reason": "initial_strategy" if not prior else "material_evidence_or_intent_change",
            "changed_policies": changed,
            "audit_reference": f"AE-GRAND-STRATEGY-{len(self._records) + 1:06d}",
            "immutable": True,
        }
        record_hash = _hash(record_payload)
        record = GrandStrategyRecord(**record_payload, hash=record_hash)
        self._records.append(record)
        self._records_by_fingerprint[fingerprint] = record
        return self.snapshot(timestamp_utc=timestamp_utc, latest_record=record)

    def snapshot(self, *, timestamp_utc: str, latest_record: GrandStrategyRecord | None = None) -> dict[str, Any]:
        latest = latest_record or (self._records[-1] if self._records else None)
        latest_payload = asdict(latest) if latest else {}
        return {
            "engineName": "Enterprise Grand Strategy Engine",
            "engineeringOrder": "EO-BX",
            "constitutionalMode": "STRATEGIC_POLICY_ONLY_NO_TRADING",
            "grandStrategyRecords": tuple(asdict(item) for item in self._records),
            "activeGrandStrategyRecord": latest_payload,
            "dashboardFeed": _dashboard_feed(latest_payload),
            "briefingFeed": _briefing_feed(latest_payload),
            "dailyReviewFeed": _daily_review_feed(latest_payload),
            "capitalAllocationFeed": _policy_feed(latest_payload, "capital"),
            "portfolioConstructionFeed": _policy_feed(latest_payload, "construction"),
            "positionSizingFeed": _policy_feed(latest_payload, "sizing"),
            "strategyEvolutionFeed": _evolution_feed(latest_payload, "strategy"),
            "promptEvolutionFeed": _evolution_feed(latest_payload, "prompt"),
            "experimentSchedulerFeed": _experiment_feed(latest_payload),
            "organizationalEvolutionFeed": _organizational_feed(latest_payload),
            "creditGovernorFeed": latest_payload.get("credit_budget_policy", {}),
            "conflictResolutionPrecedence": (
                "constitutional_law",
                "emergency_safety_and_risk_halt",
                "explicit_current_commander_directive",
                "broker_and_legal_constraints",
                "operational_guardrails",
                "grand_strategy",
                "lower_level_engine_preferences",
            ),
            "configuration": asdict(self._config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "executesTrades": False, "amendsConstitution": False, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicStrategy": True, "optionalNarrativeMayNotAlterPolicy": True},
            "internalDiagnostics": {
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "mutatesTruthRecords": False,
                "promotesStrategies": False,
                "promotesPrompts": False,
                "schedulesExperiments": False,
                "enablesLiveTrading": False,
                "apiCreditsConsumed": 0.0,
                "recordCount": len(self._records),
                "timestampUtc": timestamp_utc,
            },
        }

    def _intent(self, commander_intent: dict[str, Any] | None, sources: dict[str, Any], config: GrandStrategyConfig) -> CommanderIntentRecord:
        control = sources.get("control", {})
        intent = commander_intent or {}
        missing = not bool(intent)
        return CommanderIntentRecord(
            intent_id=str(intent.get("intent_id") or intent.get("intentId") or ("COMMANDER-INTENT-MISSING-CONSERVATIVE" if missing else "COMMANDER-INTENT-001")),
            mission=str(intent.get("mission") or "Build a broker-realistic, scientifically reproducible paper-trading institution before live autonomy."),
            capital_objective=str(intent.get("capital_objective") or "preserve_capital_then_validate_benchmark_relative_growth"),
            acceptable_drawdown=_number(intent.get("acceptable_drawdown"), config.maximum_drawdown_tolerance),
            acceptable_risk=_number(intent.get("acceptable_risk"), config.acceptable_composite_risk),
            operating_mode=str(intent.get("operating_mode") or ("paper" if control.get("paper_trading_active") else "paper_validation")),
            desired_deployment_pace=str(intent.get("desired_deployment_pace") or "measured"),
            preferred_markets=tuple(intent.get("preferred_markets") or ("equities", "etfs")),
            prohibited_markets=tuple(intent.get("prohibited_markets") or ("options", "crypto", "margin", "short_selling", "futures")),
            liquidity_requirements=str(intent.get("liquidity_requirements") or "high_liquidity_only"),
            time_horizon=str(intent.get("time_horizon") or "multi_year"),
            research_appetite=str(intent.get("research_appetite") or "moderate"),
            experiment_appetite=str(intent.get("experiment_appetite") or "bounded"),
            credit_budget=_number(intent.get("credit_budget"), config.maximum_ai_daily_credit_policy),
            required_cash_reserve=_number(intent.get("required_cash_reserve"), config.required_cash_reserve_percent),
            autonomy_limits=tuple(intent.get("autonomy_limits") or ("no_live_trading_without_commander_authorization", "no_ai_for_deterministic_tasks")),
            live_trading_permission_state=str(intent.get("live_trading_permission_state") or "prohibited"),
            review_cadence=str(intent.get("review_cadence") or "daily_and_material_event"),
            strategic_priorities=tuple(intent.get("strategic_priorities") or ("capital_preservation", "reality_fidelity", "complete_trade_truth", "benchmark_evidence")),
            source="explicit" if intent else "conservative_default",
        )

    def _posture(self, intent: CommanderIntentRecord, evidence: dict[str, Any], config: GrandStrategyConfig) -> tuple[str, tuple[str, ...]]:
        risk = evidence["risk_score"]
        fidelity = evidence["reality_fidelity"]
        drawdown = evidence["drawdown"]
        closed = evidence["closed_trade_count"]
        mc_ruin = evidence["monte_carlo_ruin_probability"]
        if evidence["trading_halted"]:
            return StrategicPosture.HALTED.value, ("Funds or operating state halted; Grand Strategy cannot authorize activity.",)
        if fidelity and fidelity < config.unsafe_reality_fidelity:
            return StrategicPosture.CALIBRATION_ONLY.value, ("Reality fidelity is unsafe; strategy shifts to calibration only.",)
        if risk >= config.critical_risk_threshold:
            return StrategicPosture.DEFENSIVE.value, ("Composite risk breached critical threshold; defensive posture required.",)
        if drawdown >= intent.acceptable_drawdown:
            return StrategicPosture.RECOVERY.value, ("Drawdown exceeds Commander tolerance; recovery posture required.",)
        if mc_ruin > config.maximum_monte_carlo_ruin_probability:
            return StrategicPosture.NO_NEW_RISK.value, ("Monte Carlo ruin probability exceeds strategic tolerance.",)
        if intent.source != "explicit":
            return StrategicPosture.PRESERVATION.value, ("Commander intent missing; conservative preservation policy applies.",)
        if closed < config.minimum_closed_trade_sample:
            return StrategicPosture.CAUTIOUS_GROWTH.value, ("Evidence sample is not statistically mature; recent gains do not justify aggression.",)
        if evidence["benchmark_alpha"] > 0 and fidelity >= config.minimum_reality_fidelity and risk < config.acceptable_composite_risk:
            return StrategicPosture.BALANCED_GROWTH.value, ("Validated benchmark-relative evidence supports balanced growth, not aggression.",)
        return StrategicPosture.PRESERVATION.value, ("Default preservation posture selected from current evidence.",)

    def _maturity(self, evidence: dict[str, Any], config: GrandStrategyConfig) -> dict[str, Any]:
        blockers = []
        stage = "architectural"
        if evidence["broker_realism_score"] >= 70:
            stage = "broker_realistic"
        if evidence["lifecycle_complete"]:
            stage = "lifecycle_complete"
        if evidence["reproducibility_score"] >= config.minimum_reproducibility_score:
            stage = "scientifically_reproducible"
        if evidence["closed_trade_count"] >= config.minimum_closed_trade_sample:
            stage = "statistically_informative"
        if evidence["reality_fidelity"] >= config.minimum_reality_fidelity and evidence["closed_trade_count"] >= config.minimum_closed_trade_sample:
            stage = "strategically_adaptive"
        for condition, blocker in (
            (evidence["broker_realism_score"] < 80, "broker_realism_not_validated"),
            (not evidence["lifecycle_complete"], "position_lifecycle_not_complete"),
            (evidence["closed_trade_count"] < config.minimum_closed_trade_sample, "closed_trade_sample_too_small"),
            (evidence["reality_fidelity"] < config.minimum_reality_fidelity, "reality_fidelity_below_live_threshold"),
            (evidence["reproducibility_score"] < config.minimum_reproducibility_score, "reproducibility_not_certified"),
        ):
            if condition:
                blockers.append(blocker)
        return {"currentStage": stage, "nextStage": _next_stage(stage), "blockers": tuple(blockers), "stageRequirementsExplicit": True}

    def _live_readiness(self, intent: CommanderIntentRecord, evidence: dict[str, Any], maturity: dict[str, Any], config: GrandStrategyConfig) -> dict[str, Any]:
        checks = {
            "commanderPolicy": intent.live_trading_permission_state,
            "brokerRealism": evidence["broker_realism_score"] >= 80,
            "lifecycleCompleteness": evidence["lifecycle_complete"],
            "realityFidelity": evidence["reality_fidelity"] >= config.minimum_reality_fidelity,
            "closedTradeSample": evidence["closed_trade_count"] >= config.minimum_closed_trade_sample,
            "riskState": evidence["risk_score"] < config.acceptable_composite_risk,
            "stressResilience": evidence["black_swan_survival_score"] >= config.minimum_black_swan_survival_score,
            "monteCarloRuin": evidence["monte_carlo_ruin_probability"] <= config.maximum_monte_carlo_ruin_probability,
            "reproducibility": evidence["reproducibility_score"] >= config.minimum_reproducibility_score,
            "architectureAlone": False,
        }
        if intent.live_trading_permission_state == "prohibited":
            state = "prohibited"
        elif all(value is True for key, value in checks.items() if key not in {"commanderPolicy", "architectureAlone"}):
            state = "candidate_pending_review"
        elif maturity["currentStage"] in {"architectural", "broker_realistic"}:
            state = "paper_validation"
        else:
            state = "not_ready"
        return {"state": state, "checks": checks, "liveTradingEnabledByThisEngine": False, "requiredCommanderAuthorization": True}

    def _confidence(self, intent: CommanderIntentRecord, evidence: dict[str, Any], maturity: dict[str, Any], config: GrandStrategyConfig) -> tuple[float, tuple[str, ...]]:
        degraded = []
        score = 100.0
        if intent.source != "explicit":
            degraded.append("commander_intent_missing")
            score -= 15
        if evidence["reality_fidelity"] < config.minimum_reality_fidelity:
            degraded.append("reality_fidelity_degraded")
            score -= 20
        if evidence["closed_trade_count"] < config.minimum_closed_trade_sample:
            degraded.append("closed_trade_sample_limited")
            score -= 15
        if evidence["reproducibility_score"] < config.minimum_reproducibility_score:
            degraded.append("reproducibility_limited")
            score -= 10
        if evidence["benchmark_alpha"] == 0:
            degraded.append("benchmark_evidence_limited")
            score -= 5
        if maturity["blockers"]:
            score -= min(20, len(maturity["blockers"]) * 4)
        return round(max(0.0, min(100.0, score)), 4), tuple(dict.fromkeys(degraded))

    def _conflicts(self, intent: CommanderIntentRecord, evidence: dict[str, Any], posture: str) -> tuple[dict[str, Any], ...]:
        conflicts = []
        if intent.live_trading_permission_state != "prohibited" and not evidence["constitution_live_allowed"]:
            conflicts.append({"conflict": "commander_live_permission_conflicts_with_configuration", "precedenceWinner": "constitutional_law", "resolution": "live_trading_remains_disabled"})
        if evidence["risk_halt_recommended"] and posture not in {StrategicPosture.HALTED.value, StrategicPosture.DEFENSIVE.value, StrategicPosture.RECOVERY.value}:
            conflicts.append({"conflict": "risk_halt_overrides_growth_posture", "precedenceWinner": "emergency_safety_and_risk_halt", "resolution": "reduce_or_halt_risk"})
        return tuple(conflicts)

    def _policies(self, intent: CommanderIntentRecord, evidence: dict[str, Any], posture: str, maturity: dict[str, Any], live: dict[str, Any], config: GrandStrategyConfig) -> dict[str, Any]:
        max_deployable = 0.0 if posture in {StrategicPosture.CALIBRATION_ONLY.value, StrategicPosture.NO_NEW_RISK.value, StrategicPosture.HALTED.value} else config.maximum_deployable_capital_percent
        prohibited = (
            _prohibition("no_live_trading", "Live trading remains disabled unless Commander and constitutional gates approve."),
            _prohibition("no_margin", "Margin is unsupported and prohibited."),
            _prohibition("no_unsupported_assets", "Options, crypto, short selling, futures, and margin remain future-only."),
            _prohibition("no_strategy_promotion_without_sample_threshold", "Strategy promotion requires closed-trade and benchmark evidence."),
            _prohibition("no_ai_for_deterministic_tasks", "LAW VIII keeps deterministic work out of AI paths."),
            _prohibition("no_learning_promotion_from_incomplete_trades", "Closed Position Truth required for learning promotion."),
        )
        research = (
            _priority("reality_fidelity", "Improve calibration and truth reliability.", "Enterprise Reality Calibration Engine", "high"),
            _priority("complete_trade_sample", "Increase closed-position truth observations.", "Trader / Historian", "high"),
            _priority("benchmark_evidence", "Improve benchmark-relative evidence quality.", "Enterprise Benchmark Engine", "medium"),
        )
        capability = (
            _capability("market_data_fidelity", "Needed for realistic valuation and live-readiness evidence.", "market-data-workstream", "high"),
            _capability("order_execution_realism", "Needed before live readiness can be considered.", "execution-realism-workstream", "high"),
            _capability("tax_lot_and_corporate_actions", "Future live brokerage readiness dependency.", "future-brokerage-workstream", "medium"),
        )
        return {
            "prohibited_actions": prohibited,
            "capital_preservation": {"requiredCashReservePercent": intent.required_cash_reserve, "maximumDrawdown": intent.acceptable_drawdown, "dailyLossLimitPercent": config.daily_loss_limit_percent, "weeklyLossLimitPercent": config.weekly_loss_limit_percent, "experimentalCapitalCap": config.experimental_capital_cap, "maximumDeployableCapitalPercent": max_deployable, "haltConditions": ("critical_risk", "unsafe_reality_fidelity", "constitutional_violation")},
            "benchmark_objective": {"primaryBenchmark": "cash_then_SPY", "objective": "risk_adjusted_outperformance_after_evidence_maturity", "minimumEvidence": config.minimum_closed_trade_sample},
            "return_objective": {"mode": "evidence_accumulation_then_benchmark_outperformance", "profitIsNotSoleObjective": True},
            "drawdown_tolerance": {"maximumDrawdown": intent.acceptable_drawdown, "recoveryModeTrigger": intent.acceptable_drawdown},
            "risk_tolerance": {"acceptableCompositeRisk": intent.acceptable_risk, "acceptableCorrelationRisk": 55, "acceptableRuinProbability": config.maximum_monte_carlo_ruin_probability, "minimumBlackSwanSurvivalScore": config.minimum_black_swan_survival_score, "response": "reduce_risk_or_pause_new_entries"},
            "deployment_policy": {"posture": posture, "pace": intent.desired_deployment_pace, "newRiskAllowed": posture not in {StrategicPosture.CALIBRATION_ONLY.value, StrategicPosture.NO_NEW_RISK.value, StrategicPosture.HALTED.value}, "maximumDeployableCapitalPercent": max_deployable},
            "cash_reserve_policy": {"requiredCashReservePercent": intent.required_cash_reserve, "increaseReserveWhen": ("drawdown", "critical_risk", "reality_degraded")},
            "strategy_portfolio_policy": {"enabledCategories": ("paper_equity", "paper_etf", "research_only"), "maximumSimultaneousStrategies": config.maximum_strategy_count, "maximumCapitalPerStrategy": 0.20, "promotionRequirements": ("closed_trade_sample_threshold", "benchmark_comparison", "reproducibility"), "retirementConditions": ("persistent_underperformance", "excess_drawdown", "low_attribution_confidence")},
            "research_priorities": research,
            "experiment_priorities": (_priority("information_gain", "Prioritize high knowledge-per-credit experiments.", "Enterprise Experiment Scheduler", "high"), _priority("reproducibility", "Require reproducible replay before promotion.", "Decision Laboratory", "high")),
            "capability_priorities": capability,
            "ai_usage_policy": {"permittedUseCases": ("authorized_narrative_explanation", "commander_requested_analysis"), "prohibitedUseCases": ("deterministic_scoring", "routine_policy_generation", "trade_authority"), "minimumJustificationThreshold": "LAW_VIII_AUTHORIZED"},
            "credit_budget_policy": {"dailyCreditCeiling": min(intent.credit_budget, config.maximum_ai_daily_credit_policy), "researchCreditBudget": round(min(intent.credit_budget, config.maximum_ai_daily_credit_policy) * 0.4, 4), "operationalCreditBudget": round(min(intent.credit_budget, config.maximum_ai_daily_credit_policy) * 0.4, 4), "emergencyAnalysisBudget": round(min(intent.credit_budget, config.maximum_ai_daily_credit_policy) * 0.2, 4), "throttleWhen": "credit_efficiency_degraded"},
            "market_participation_policy": _market_policy(intent, maturity),
            "data_quality_requirements": {"marketDataHealthRequired": "healthy", "staleDataPolicy": "reduce_confidence_and_require_review"},
            "reality_fidelity_requirements": {"minimumRealityFidelity": config.minimum_reality_fidelity, "unsafeThreshold": config.unsafe_reality_fidelity, "belowMinimumResponse": "calibration_only"},
            "learning_reliability_requirements": {"minimumLearningReliability": config.minimum_learning_reliability, "closedTruthRequired": True},
            "escalation_conditions": (_response("unsafe_reality_fidelity", "enter_calibration_mode"), _response("critical_risk", "pause_new_entries"), _response("drawdown_breach", "enter_recovery_mode")),
            "review_triggers": (_response("scheduled_horizon", "create_new_strategy_version"), _response("material_drawdown", "review_strategy"), _response("critical_risk_change", "review_strategy"), _response("commander_directive", "review_strategy"), _response("live_readiness_milestone", "require_commander_review")),
            "success_metrics": (_metric("capital_preservation", evidence["drawdown"], intent.acceptable_drawdown), _metric("reality_fidelity", evidence["reality_fidelity"], config.minimum_reality_fidelity), _metric("closed_trade_sample", evidence["closed_trade_count"], config.minimum_closed_trade_sample), _metric("credit_efficiency", evidence["credits_used_today"], intent.credit_budget)),
            "failure_conditions": (_failure("drawdown_exceeds_tolerance", "enter_recovery_mode"), _failure("unsafe_reality_fidelity", "enter_calibration_mode"), _failure("critical_risk", "halt_or_reduce_risk"), _failure("excessive_ai_cost", "suspend_nonessential_ai")),
            "evidence_references": _references(),
        }

    def _objectives(self, intent: CommanderIntentRecord, evidence: dict[str, Any], posture: str, config: GrandStrategyConfig) -> dict[str, tuple[dict[str, Any], ...]]:
        primary = (
            _objective(1, "preserve_capital", "drawdown", evidence["drawdown"], intent.acceptable_drawdown, "daily", "Performance Truth", "active", "none"),
            _objective(2, "restore_or_maintain_reality_fidelity", "overallRealityFidelityScore", evidence["reality_fidelity"], config.minimum_reality_fidelity, "daily", "Enterprise Reality Calibration", "active", "calibration_evidence"),
            _objective(3, "build_complete_trade_evidence", "closedTradeCount", evidence["closed_trade_count"], config.minimum_closed_trade_sample, "monthly", "Closed Position Truth", "active", "round_trip_sample"),
        )
        secondary = (
            _objective(4, "reduce_correlation_concentration", "correlationRisk", evidence["correlation_risk"], 55, "weekly", "Correlation Intelligence", "watch", "sector_strategy_metadata"),
            _objective(5, "improve_research_yield", "queuedExperiments", evidence["queued_experiments"], config.maximum_concurrent_experiments, "weekly", "Experiment Scheduler", "watch", "knowledge_gap_quality"),
            _objective(6, "reduce_intelligence_cost", "creditsUsedToday", evidence["credits_used_today"], intent.credit_budget, "daily", "Credit Governor", "watch", "LAW VIII justification"),
        )
        return {"primary": primary, "secondary": secondary}

    def _resolved_config(self, registry: dict[str, Any]) -> GrandStrategyConfig:
        configs = registry.get("activeConfiguration", {}) or registry.get("configurationRegistry", {})
        strategy = configs.get("enterpriseGrandStrategyEngine", {}) if isinstance(configs, dict) else {}
        if not isinstance(strategy, dict):
            return self._config
        values = asdict(self._config)
        for key, value in strategy.items():
            if key in values:
                values[key] = tuple(value) if isinstance(values[key], tuple) and isinstance(value, list) else value
        return GrandStrategyConfig(**values)


def _evidence(sources: dict[str, Any]) -> dict[str, Any]:
    truth = sources.get("performanceTruthEngine", {})
    dashboard = sources.get("commanderStrategicDashboard", {})
    risk = sources.get("enterpriseRiskFactorEngine", {})
    reality = sources.get("enterpriseRealityCalibrationEngine", {})
    correlation = sources.get("correlationIntelligenceEngine", {})
    trader = sources.get("traderCommandBridge", {})
    closed = sources.get("closedPositionTruthBuilder", {})
    reproducibility = sources.get("enterpriseReproducibilityFramework", {})
    black = sources.get("blackSwanSimulationEngine", {})
    monte = sources.get("monteCarloPortfolioEngine", {})
    learning = sources.get("enterpriseLearningEngine", {})
    experiments = sources.get("enterpriseExperimentScheduler", {})
    costs = sources.get("costs", {})
    control = sources.get("control", {})
    perf = truth.get("calculations", {}).get("portfolio", {})
    return {
        "risk_score": _number(risk.get("commanderSummary", {}).get("compositeRiskScore")),
        "risk_halt_recommended": bool(risk.get("riskOfficeFeed", {}).get("haltRecommended")),
        "reality_fidelity": _number(reality.get("commanderSummary", {}).get("overallRealityFidelityScore"), 100.0),
        "learning_reliability": _number(reality.get("latestCalibrationReport", {}).get("learning_reliability_score"), 100.0),
        "drawdown": _number(perf.get("maximumDrawdown")),
        "benchmark_alpha": _number(perf.get("alpha")),
        "closed_trade_count": int(closed.get("metrics", {}).get("truthRecordCount", 0)),
        "correlation_risk": _number(correlation.get("commanderSummary", {}).get("correlationRiskScore")),
        "queued_experiments": len(experiments.get("experimentQueue", ())),
        "credits_used_today": _number(costs.get("today_api_credits_usd")),
        "broker_realism_score": _number(truth.get("executionRealism", {}).get("executionRealismScore"), 0.0),
        "lifecycle_complete": bool(trader.get("summary", {}).get("surveillance_health") or trader.get("activePositions") is not None),
        "reproducibility_score": _number(reproducibility.get("commanderReviewFeed", {}).get("score"), 0.0),
        "black_swan_survival_score": _number(black.get("commanderSummary", {}).get("survivalScore"), 100.0),
        "monte_carlo_ruin_probability": _number(monte.get("commanderSummary", {}).get("probabilityOfRuin")),
        "trading_halted": bool(control.get("user_funds_halted")),
        "constitution_live_allowed": bool(control.get("real_world_trading_active")),
        "strategic_dashboard_posture": (dashboard.get("strategic_recommendation") or {}).get("recommendation", ""),
        "strategy_candidates": len(sources.get("strategyPackageManager", {}).get("promotionQueue", ())),
        "prompt_candidates": len(sources.get("promptEvolutionEngine", {}).get("promptImprovementCandidates", ())),
        "learning_candidates": len(learning.get("recommendations", ())),
    }


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return round(float(default), 4)
        return round(float(value), 4)
    except (TypeError, ValueError):
        return round(float(default), 4)


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _stable_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in evidence.items() if key not in {"strategic_dashboard_posture"}}


def _next_stage(stage: str) -> str:
    stages = ("architectural", "operational", "broker_realistic", "lifecycle_complete", "scientifically_reproducible", "statistically_informative", "strategically_adaptive", "live_candidate", "controlled_live", "mature_institution")
    index = stages.index(stage) if stage in stages else 0
    return stages[min(len(stages) - 1, index + 1)]


def _prohibition(identifier: str, reason: str) -> dict[str, Any]:
    return {"prohibition": identifier, "reason": reason, "precedence": "constitutional_or_grand_strategy_policy"}


def _priority(priority_id: str, rationale: str, owner: str, urgency: str) -> dict[str, Any]:
    return {"priority": priority_id, "rationale": rationale, "owner": owner, "urgency": urgency, "status": "active"}


def _capability(name: str, rationale: str, workstream: str, urgency: str) -> dict[str, Any]:
    return {"capability": name, "rationale": rationale, "strategicValue": "live_readiness_and_scientific_quality", "dependency": workstream, "urgency": urgency, "estimatedComplexity": "medium", "evidenceGap": name, "recommendedWorkstream": workstream}


def _response(condition: str, response: str) -> dict[str, Any]:
    return {"condition": condition, "strategicResponse": response}


def _metric(name: str, current: Any, target: Any) -> dict[str, Any]:
    return {"metric": name, "currentValue": current, "targetValue": target, "status": "measured"}


def _failure(condition: str, response: str) -> dict[str, Any]:
    return {"failureCondition": condition, "strategicResponse": response}


def _objective(priority: int, name: str, metric: str, current: Any, target: Any, horizon: str, owner: str, status: str, blocker: str) -> dict[str, Any]:
    return {"priority": priority, "objective": name, "targetMetric": metric, "currentValue": current, "targetValue": target, "reviewHorizon": horizon, "evidenceRequirement": owner, "owner": owner, "status": status, "blockingConditions": (blocker,) if blocker else ()}


def _market_policy(intent: CommanderIntentRecord, maturity: dict[str, Any]) -> dict[str, Any]:
    return {
        "equities": {"enabled": "equities" in intent.preferred_markets, "maturityRequirement": "broker_realistic", "commanderAuthorizationRequired": False, "riskLimit": "standard"},
        "etfs": {"enabled": "etfs" in intent.preferred_markets, "maturityRequirement": "broker_realistic", "commanderAuthorizationRequired": False, "riskLimit": "standard"},
        "options": {"enabled": False, "maturityRequirement": "future_options_mechanics", "commanderAuthorizationRequired": True, "riskLimit": "prohibited"},
        "crypto": {"enabled": False, "maturityRequirement": "future_crypto_policy", "commanderAuthorizationRequired": True, "riskLimit": "prohibited"},
        "bonds": {"enabled": False, "maturityRequirement": "future_fixed_income_support", "commanderAuthorizationRequired": True, "riskLimit": "prohibited"},
        "cash_equivalents": {"enabled": True, "maturityRequirement": "current", "commanderAuthorizationRequired": False, "riskLimit": "preservation"},
        "short_selling": {"enabled": False, "maturityRequirement": "future_margin_and_borrow_controls", "commanderAuthorizationRequired": True, "riskLimit": "prohibited"},
        "margin": {"enabled": False, "maturityRequirement": "not_supported", "commanderAuthorizationRequired": True, "riskLimit": "prohibited"},
        "institutionalMaturityStage": maturity["currentStage"],
    }


def _references() -> tuple[dict[str, Any], ...]:
    return (
        {"recordType": "Performance Truth", "recordId": "performanceTruthEngine"},
        {"recordType": "Risk Factor Record", "recordId": "enterpriseRiskFactorEngine"},
        {"recordType": "Reality Calibration Report", "recordId": "enterpriseRealityCalibrationEngine"},
        {"recordType": "Closed Position Truth", "recordId": "closedPositionTruthBuilder"},
        {"recordType": "Commander Intent", "recordId": "commanderIntent"},
    )


def _changed_policies(prior: GrandStrategyRecord | None, policies: dict[str, Any], posture: str) -> tuple[str, ...]:
    if not prior:
        return ("initial_policy_set",)
    changed = []
    if prior.strategic_posture != posture:
        changed.append("strategic_posture")
    if prior.capital_preservation_policy != policies["capital_preservation"]:
        changed.append("capital_preservation_policy")
    if prior.risk_tolerance != policies["risk_tolerance"]:
        changed.append("risk_tolerance")
    return tuple(changed)


def _dashboard_feed(record: dict[str, Any]) -> dict[str, Any]:
    return {"currentStrategicPosture": record.get("strategic_posture", ""), "primaryObjectives": tuple(record.get("primary_objectives", ())[:3]), "topPriorities": tuple(record.get("capability_priorities", ())[:3]), "prohibitedActions": tuple(record.get("prohibited_actions", ())[:5]), "successMetrics": tuple(record.get("success_metrics", ())[:5]), "currentMaturityStage": record.get("operational_maturity_targets", {}).get("currentStage", ""), "liveReadinessState": record.get("live_readiness_policy", {}).get("state", ""), "strategicConfidence": record.get("confidence", 0.0), "activeReviewTriggers": tuple(record.get("review_triggers", ())[:5]), "decisionsRequired": tuple(item for item in record.get("review_triggers", ()) if "commander" in str(item).lower())}


def _briefing_feed(record: dict[str, Any]) -> dict[str, Any]:
    return {"strategyVersion": record.get("strategy_version", ""), "posture": record.get("strategic_posture", ""), "confidence": record.get("confidence", 0.0), "maturity": record.get("operational_maturity_targets", {}).get("currentStage", ""), "liveReadiness": record.get("live_readiness_policy", {}).get("state", ""), "summary": f"Grand Strategy {record.get('strategy_version', '')}: {record.get('strategic_posture', '')} with confidence {record.get('confidence', 0.0)}."}


def _daily_review_feed(record: dict[str, Any]) -> dict[str, Any]:
    return {"currentPosture": record.get("strategic_posture", ""), "reviewCadence": tuple(record.get("review_triggers", ())[:3]), "capabilityPriorities": tuple(record.get("capability_priorities", ())[:3])}


def _policy_feed(record: dict[str, Any], consumer: str) -> dict[str, Any]:
    return {"strategyVersion": record.get("strategy_version", ""), "strategicPosture": record.get("strategic_posture", ""), "capitalPolicy": record.get("capital_preservation_policy", {}), "riskTolerance": record.get("risk_tolerance", {}), "deploymentPolicy": record.get("deployment_policy", {}), "marketParticipationPolicy": record.get("market_participation_policy", {}), "consumer": consumer}


def _evolution_feed(record: dict[str, Any], consumer: str) -> dict[str, Any]:
    return {"strategyVersion": record.get("strategy_version", ""), "promotionRequirements": record.get("strategy_portfolio_policy", {}).get("promotionRequirements", ()), "priorities": record.get("research_priorities", ()), "consumer": consumer}


def _experiment_feed(record: dict[str, Any]) -> dict[str, Any]:
    return {"strategyVersion": record.get("strategy_version", ""), "researchPriorities": record.get("research_priorities", ()), "experimentPriorities": record.get("experiment_priorities", ()), "maximumConcurrentExperiments": 3, "requiredReproducibility": True}


def _organizational_feed(record: dict[str, Any]) -> dict[str, Any]:
    return {"strategyVersion": record.get("strategy_version", ""), "capabilityGaps": record.get("capability_priorities", ()), "maturityBlockers": record.get("operational_maturity_targets", {}).get("blockers", ()), "priorityWorkstreams": tuple(item.get("recommendedWorkstream", "") for item in record.get("capability_priorities", ()))}
