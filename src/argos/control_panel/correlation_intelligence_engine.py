"""Correlation Intelligence Engine for ARGOS EO-AH."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any


@dataclass(frozen=True)
class CorrelationIntelligenceConfig:
    correlation_intelligence_enabled: bool = True
    return_history_window: int = 20
    minimum_return_observations: int = 4
    high_correlation_threshold: float = 0.75
    inverse_correlation_threshold: float = -0.50
    low_correlation_threshold: float = 0.25
    hidden_concentration_high_threshold: float = 65.0
    diversification_quality_low_threshold: float = 45.0
    correlation_risk_high_threshold: float = 65.0
    etf_overlap_enabled: bool = True
    metadata_proxy_enabled: bool = True
    degraded_input_penalty: float = 12.0
    conservative_scoring_mode: bool = True


@dataclass(frozen=True)
class CorrelationIntelligenceRecord:
    correlation_intelligence_id: str
    timestamp: str
    portfolio_equity: float
    total_positions_analyzed: int
    total_pairs_analyzed: int
    return_history_window: int
    correlation_method: str
    correlation_matrix: dict[str, dict[str, float]]
    correlation_confidence: float
    high_correlation_pairs: tuple[dict[str, Any], ...]
    inverse_correlation_pairs: tuple[dict[str, Any], ...]
    uncorrelated_pairs: tuple[dict[str, Any], ...]
    sector_overlap_groups: tuple[dict[str, Any], ...]
    strategy_overlap_groups: tuple[dict[str, Any], ...]
    thesis_overlap_groups: tuple[dict[str, Any], ...]
    asset_type_overlap_groups: tuple[dict[str, Any], ...]
    etf_overlap_groups: tuple[dict[str, Any], ...]
    hidden_concentration_score: float
    diversification_quality_score: float
    correlation_risk_score: float
    degraded_inputs: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    audit_reference: str


class CorrelationIntelligenceEngine:
    """Deterministic portfolio overlap and correlation evaluator."""

    def __init__(self, config: CorrelationIntelligenceConfig | None = None) -> None:
        self._config = config or CorrelationIntelligenceConfig()
        self._records: list[CorrelationIntelligenceRecord] = []
        self._last_fingerprint = ""

    def evaluate(
        self,
        *,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any],
        market_context_engine: dict[str, Any] | None = None,
        enterprise_benchmark_engine: dict[str, Any] | None = None,
        enterprise_configuration_registry: dict[str, Any] | None = None,
        audit_event_count: int = 0,
    ) -> dict[str, Any]:
        config = self._resolved_config(enterprise_configuration_registry)
        if not config.correlation_intelligence_enabled:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=None, config=config)
        fingerprint = _fingerprint(performance_truth, market_data_provider, market_context_engine or {}, enterprise_benchmark_engine or {})
        if fingerprint == self._last_fingerprint and self._records:
            return self.snapshot(timestamp_utc=timestamp_utc, latest_record=self._records[-1], config=config)
        record = self._build_record(
            timestamp_utc=timestamp_utc,
            performance_truth=performance_truth,
            market_data_provider=market_data_provider,
            enterprise_benchmark_engine=enterprise_benchmark_engine or {},
            audit_event_count=audit_event_count,
            config=config,
        )
        self._records.append(record)
        self._last_fingerprint = fingerprint
        return self.snapshot(timestamp_utc=timestamp_utc, latest_record=record, config=config)

    def snapshot(self, *, timestamp_utc: str, latest_record: CorrelationIntelligenceRecord | None = None, config: CorrelationIntelligenceConfig | None = None) -> dict[str, Any]:
        config = config or self._config
        latest = latest_record or (self._records[-1] if self._records else None)
        latest_payload = asdict(latest) if latest else {}
        review = bool(latest and (latest.correlation_risk_score >= config.correlation_risk_high_threshold or latest.diversification_quality_score <= config.diversification_quality_low_threshold))
        feed = {
            "correlationRiskScore": latest.correlation_risk_score if latest else 0.0,
            "hiddenConcentrationScore": latest.hidden_concentration_score if latest else 0.0,
            "diversificationQualityScore": latest.diversification_quality_score if latest else 0.0,
            "highCorrelationPairs": latest.high_correlation_pairs if latest else (),
            "overlapGroups": (latest.sector_overlap_groups + latest.strategy_overlap_groups + latest.thesis_overlap_groups + latest.asset_type_overlap_groups + latest.etf_overlap_groups) if latest else (),
            "degradedInputs": latest.degraded_inputs if latest else ("No correlation intelligence record available.",),
            "recommendedActions": latest.recommended_actions if latest else (),
            "correlationAdjustedCapitalMultiplier": _capital_multiplier(latest.correlation_risk_score if latest else 100.0),
            "correlationAdjustedSizeMultiplier": _size_multiplier(latest.correlation_risk_score if latest else 100.0),
            "reviewRecommended": review,
        }
        return {
            "engineName": "Correlation Intelligence Engine",
            "engineeringOrder": "EO-AH",
            "constitutionalMode": "CORRELATION_MEASUREMENT_ONLY",
            "correlationIntelligenceRecords": tuple(asdict(item) for item in self._records),
            "latestCorrelationIntelligenceRecord": latest_payload,
            "riskFactorFeed": feed,
            "portfolioConstructionFeed": feed,
            "capitalAllocationFeed": feed,
            "positionSizingFeed": feed,
            "enterpriseHealthMetrics": {
                "latestCorrelationRiskScore": latest.correlation_risk_score if latest else 0.0,
                "latestHiddenConcentrationScore": latest.hidden_concentration_score if latest else 0.0,
                "diversificationQualityScore": latest.diversification_quality_score if latest else 0.0,
                "highCorrelationPairCount": len(latest.high_correlation_pairs) if latest else 0,
                "overlapGroupCount": len(feed["overlapGroups"]),
                "degradedCorrelationInputs": len(latest.degraded_inputs) if latest else 1,
                "recordAge": "CURRENT" if latest and latest.timestamp == timestamp_utc else "RECENT" if latest else "NO_RECORD",
                "recommendedReviewFlag": review,
            },
            "commanderSummary": {
                "correlationRiskScore": latest.correlation_risk_score if latest else 0.0,
                "hiddenConcentrationScore": latest.hidden_concentration_score if latest else 0.0,
                "diversificationQualityScore": latest.diversification_quality_score if latest else 0.0,
                "recommendedActions": latest.recommended_actions if latest else ("Generate first correlation intelligence record.",),
            },
            "configuration": asdict(config),
            "lawVII": {"uncontrolledLoops": False, "persistentActiveOffice": False, "terminatesImmediately": True},
            "lawVIII": {"routineAiInvocations": 0, "deterministicScoring": True},
            "internalDiagnostics": {
                "mutatesPositions": False,
                "mutatesLedgers": False,
                "placesTrades": False,
                "enforcesPolicyDirectly": False,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "recordCount": len(self._records),
                "timestamp": timestamp_utc,
            },
        }

    def _build_record(
        self,
        *,
        timestamp_utc: str,
        performance_truth: dict[str, Any],
        market_data_provider: dict[str, Any],
        enterprise_benchmark_engine: dict[str, Any],
        audit_event_count: int,
        config: CorrelationIntelligenceConfig,
    ) -> CorrelationIntelligenceRecord:
        positions = _positions(performance_truth)
        equity = _portfolio_equity(performance_truth, positions)
        histories = _return_histories(market_data_provider, config.return_history_window)
        degraded: list[str] = []
        symbols = tuple(str(position.get("symbol", "")).upper() for position in positions)
        matrix, confidence, method, history_degraded = _correlation_matrix(symbols, histories, config)
        if history_degraded:
            degraded.append("return_history_insufficient")
        if method == "metadata_proxy" and not config.metadata_proxy_enabled:
            degraded.append("metadata_proxy_disabled")
        pairs = _classify_pairs(matrix, config)
        sector_groups = _metadata_groups(positions, equity, "sector", "same_sector", "reduce_sector_overlap")
        strategy_groups = _metadata_groups(positions, equity, "currentStrategy", "same_strategy", "reduce_strategy_overlap", fallback_key="strategy_id")
        thesis_groups = _thesis_groups(positions, equity)
        asset_groups = _metadata_groups(positions, equity, "asset_type", "same_asset_type", "prefer_uncorrelated_opportunities")
        etf_groups, etf_degraded = _etf_overlap_groups(positions, market_data_provider, equity, config)
        if etf_degraded:
            degraded.append(etf_degraded)
        if not enterprise_benchmark_engine.get("tradeLevelComparisons") and not enterprise_benchmark_engine.get("benchmarkComparisons"):
            degraded.append("benchmark_relationships_limited")
        all_groups = sector_groups + strategy_groups + thesis_groups + asset_groups + etf_groups
        hidden = _hidden_concentration_score(positions, equity, pairs["high"], all_groups, degraded, config)
        diversification = _diversification_quality_score(positions, equity, pairs["high"], all_groups, degraded)
        risk = _correlation_risk_score(hidden, diversification, pairs["high"], all_groups, degraded)
        actions = _recommended_actions(hidden, diversification, risk, degraded, config)
        return CorrelationIntelligenceRecord(
            correlation_intelligence_id=f"CORR-{len(self._records) + 1:06d}",
            timestamp=timestamp_utc,
            portfolio_equity=round(equity, 4),
            total_positions_analyzed=len(positions),
            total_pairs_analyzed=len(pairs["all"]),
            return_history_window=config.return_history_window,
            correlation_method=method,
            correlation_matrix=matrix,
            correlation_confidence=confidence,
            high_correlation_pairs=tuple(pairs["high"]),
            inverse_correlation_pairs=tuple(pairs["inverse"]),
            uncorrelated_pairs=tuple(pairs["uncorrelated"]),
            sector_overlap_groups=tuple(sector_groups),
            strategy_overlap_groups=tuple(strategy_groups),
            thesis_overlap_groups=tuple(thesis_groups),
            asset_type_overlap_groups=tuple(asset_groups),
            etf_overlap_groups=tuple(etf_groups),
            hidden_concentration_score=hidden,
            diversification_quality_score=diversification,
            correlation_risk_score=risk,
            degraded_inputs=tuple(dict.fromkeys(degraded)),
            recommended_actions=actions,
            audit_reference=f"AE-CORRELATION-{audit_event_count + len(self._records) + 1:06d}",
        )

    def _resolved_config(self, enterprise_configuration_registry: dict[str, Any] | None) -> CorrelationIntelligenceConfig:
        values = asdict(self._config)
        for item in (enterprise_configuration_registry or {}).get("configurationRegistry", ()):
            key = _config_key(str(item.get("name", "")))
            if key in values:
                values[key] = _coerce_config_value(item.get("currentValue", values[key]), values[key])
        return CorrelationIntelligenceConfig(**values)


def _positions(truth: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(truth.get("positionRegistry", {}).get("activePositions", ())) or tuple(truth.get("positionLedger", ()))


def _portfolio_equity(truth: dict[str, Any], positions: tuple[dict[str, Any], ...]) -> float:
    latest = (truth.get("portfolioLedger") or ({},))[-1]
    market = sum(_value(position) for position in positions)
    cash = _number(latest.get("cash", truth.get("paperAccount", {}).get("cash", 0.0)))
    return max(1.0, _number(latest.get("total_equity", cash + market)) or cash + market)


def _return_histories(provider: dict[str, Any], window: int) -> dict[str, list[float]]:
    histories: dict[str, list[float]] = {}
    normalized = provider.get("normalizedObjects", {})
    for row in normalized.get("returnHistory", ()) + normalized.get("returns", ()):
        symbol = str(row.get("symbol", "")).upper()
        values = row.get("returns", row.get("values", ()))
        histories[symbol] = [_number(value) for value in values][-window:]
    for row in normalized.get("priceHistory", ()) + normalized.get("prices", ()):
        symbol = str(row.get("symbol", "")).upper()
        prices = [_number(value) for value in row.get("prices", row.get("values", ())) if _number(value)]
        histories[symbol] = _returns(prices[-(window + 1):])
    return histories


def _correlation_matrix(symbols: tuple[str, ...], histories: dict[str, list[float]], config: CorrelationIntelligenceConfig) -> tuple[dict[str, dict[str, float]], float, str, bool]:
    matrix: dict[str, dict[str, float]] = {symbol: {symbol: 1.0} for symbol in symbols}
    sufficient = all(len(histories.get(symbol, ())) >= config.minimum_return_observations for symbol in symbols) and len(symbols) >= 2
    if not sufficient:
        return matrix, 0.35 if symbols else 0.0, "metadata_proxy", bool(symbols)
    for left_index, left in enumerate(symbols):
        for right in symbols[left_index + 1:]:
            corr = _pearson(histories[left], histories[right])
            matrix.setdefault(left, {})[right] = corr
            matrix.setdefault(right, {})[left] = corr
    return matrix, 0.9, "pearson_return_correlation", False


def _classify_pairs(matrix: dict[str, dict[str, float]], config: CorrelationIntelligenceConfig) -> dict[str, list[dict[str, Any]]]:
    pairs: list[dict[str, Any]] = []
    symbols = tuple(matrix.keys())
    for index, left in enumerate(symbols):
        for right in symbols[index + 1:]:
            if right in matrix.get(left, {}):
                pairs.append({"left": left, "right": right, "correlation": matrix[left][right]})
    return {
        "all": pairs,
        "high": [item for item in pairs if item["correlation"] >= config.high_correlation_threshold],
        "inverse": [item for item in pairs if item["correlation"] <= config.inverse_correlation_threshold],
        "uncorrelated": [item for item in pairs if abs(item["correlation"]) <= config.low_correlation_threshold],
    }


def _metadata_groups(positions: tuple[dict[str, Any], ...], equity: float, key: str, group_type: str, action: str, fallback_key: str = "") -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for position in positions:
        value = str(position.get(key) or (position.get(fallback_key) if fallback_key else "") or ("UNKNOWN" if key == "sector" else ""))
        if key == "sector" and value == "UNKNOWN":
            value = _sector_for(str(position.get("symbol", "")))
        if value:
            buckets.setdefault(value, []).append(position)
    return [_group(f"{group_type.upper()}-{name}", group_type, members, equity, (f"{key}={name}",), 0.72, action) for name, members in buckets.items() if len(members) >= 2]


def _thesis_groups(positions: tuple[dict[str, Any], ...], equity: float) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for position in positions:
        tags = position.get("thesis_tags") or position.get("thesisTags") or position.get("thesisTag") or position.get("entry_thesis", "")
        if isinstance(tags, str):
            tags = (tags,) if tags else ()
        for tag in tags:
            buckets.setdefault(str(tag), []).append(position)
    return [_group(f"THESIS-{name}", "same_thesis", members, equity, (f"thesis={name}",), 0.76, "reduce_thesis_overlap") for name, members in buckets.items() if len(members) >= 2]


def _etf_overlap_groups(positions: tuple[dict[str, Any], ...], provider: dict[str, Any], equity: float, config: CorrelationIntelligenceConfig) -> tuple[list[dict[str, Any]], str]:
    if not config.etf_overlap_enabled:
        return [], ""
    holdings_rows = provider.get("normalizedObjects", {}).get("fundHoldings", ()) + provider.get("normalizedObjects", {}).get("etfHoldings", ())
    holdings = {str(row.get("symbol", "")).upper(): {str(item).upper() for item in row.get("holdings", ())} for row in holdings_rows}
    etfs = [position for position in positions if str(position.get("asset_type", "")).upper() in {"ETF", "FUND"}]
    if etfs and not holdings:
        return [], "etf_holdings_unavailable"
    symbols = {str(position.get("symbol", "")).upper(): position for position in positions}
    groups = []
    for etf in etfs:
        etf_symbol = str(etf.get("symbol", "")).upper()
        overlap = [symbols[symbol] for symbol in holdings.get(etf_symbol, set()) if symbol in symbols]
        if overlap:
            groups.append(_group(f"ETF-OVERLAP-{etf_symbol}", "etf_holdings_overlap", (etf, *overlap), equity, (f"{etf_symbol} holdings overlap with {tuple(position.get('symbol') for position in overlap)}",), 0.84, "reduce_correlated_exposure"))
    return groups, ""


def _group(group_id: str, group_type: str, members: tuple[dict[str, Any], ...] | list[dict[str, Any]], equity: float, evidence: tuple[str, ...], confidence: float, action: str) -> dict[str, Any]:
    member_tuple = tuple(members)
    total = sum(_value(member) for member in member_tuple)
    return {"group_id": group_id, "group_type": group_type, "members": tuple(str(member.get("symbol", "")).upper() for member in member_tuple), "total_market_value": round(total, 4), "portfolio_weight": round(total / max(1.0, equity), 6), "evidence": evidence, "confidence": confidence, "recommended_action": action}


def _hidden_concentration_score(positions: tuple[dict[str, Any], ...], equity: float, high_pairs: list[dict[str, Any]], groups: list[dict[str, Any]], degraded: list[str], config: CorrelationIntelligenceConfig) -> float:
    high_symbols = {item["left"] for item in high_pairs} | {item["right"] for item in high_pairs}
    high_weight = sum(_value(position) for position in positions if str(position.get("symbol", "")).upper() in high_symbols) / max(1.0, equity)
    group_weight = max((group["portfolio_weight"] for group in groups), default=0.0)
    independent_groups = max(1, len({tuple(group["members"]) for group in groups}) or len(positions))
    scarcity = 1 / independent_groups
    return _clamp(high_weight * 45 + group_weight * 40 + scarcity * 20 + len(degraded) * config.degraded_input_penalty)


def _diversification_quality_score(positions: tuple[dict[str, Any], ...], equity: float, high_pairs: list[dict[str, Any]], groups: list[dict[str, Any]], degraded: list[str]) -> float:
    if not positions:
        return 100.0
    weights = [_value(position) / max(1.0, equity) for position in positions]
    balance = max(0.0, 1.0 - (max(weights) - min(weights or [0.0])))
    group_penalty = min(45.0, len(groups) * 7.5)
    pair_penalty = min(30.0, len(high_pairs) * 10.0)
    data_penalty = min(30.0, len(degraded) * 6.0)
    return _clamp(balance * 85 + min(15, len(positions) * 3) - group_penalty - pair_penalty - data_penalty)


def _correlation_risk_score(hidden: float, diversification: float, high_pairs: list[dict[str, Any]], groups: list[dict[str, Any]], degraded: list[str]) -> float:
    return _clamp(hidden * 0.55 + (100 - diversification) * 0.3 + min(20.0, len(high_pairs) * 5 + len(groups) * 2) + len(degraded) * 3)


def _recommended_actions(hidden: float, diversification: float, risk: float, degraded: list[str], config: CorrelationIntelligenceConfig) -> tuple[str, ...]:
    actions = []
    if risk >= config.correlation_risk_high_threshold:
        actions.extend(("reduce_correlated_exposure", "request_risk_review", "prefer_uncorrelated_opportunities"))
    if hidden >= config.hidden_concentration_high_threshold:
        actions.append("block_new_similar_positions")
    if diversification <= config.diversification_quality_low_threshold:
        actions.append("increase_cash_buffer")
    if degraded:
        actions.append("require_more_data")
    if not actions:
        actions.append("no_action")
    return tuple(dict.fromkeys(actions))


def _returns(prices: list[float]) -> list[float]:
    return [round((right - left) / left, 8) for left, right in zip(prices, prices[1:]) if left]


def _pearson(left: list[float], right: list[float]) -> float:
    count = min(len(left), len(right))
    if count < 2:
        return 0.0
    x = left[-count:]
    y = right[-count:]
    mean_x = sum(x) / count
    mean_y = sum(y) / count
    numerator = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    denom_x = math.sqrt(sum((a - mean_x) ** 2 for a in x))
    denom_y = math.sqrt(sum((b - mean_y) ** 2 for b in y))
    if denom_x == 0 or denom_y == 0:
        return 0.0
    return round(numerator / (denom_x * denom_y), 6)


def _capital_multiplier(risk: float) -> float:
    if risk >= 80:
        return 0.35
    if risk >= 65:
        return 0.65
    return 1.0


def _size_multiplier(risk: float) -> float:
    if risk >= 80:
        return 0.5
    if risk >= 65:
        return 0.75
    return 1.0


def _value(position: dict[str, Any]) -> float:
    return _number(position.get("current_value", position.get("market_value", _number(position.get("quantity")) * _number(position.get("current_price", position.get("average_cost"))))))


def _sector_for(symbol: str) -> str:
    return {"AAPL": "Technology", "MSFT": "Technology", "SPY": "Broad Market", "QQQ": "Technology", "TLT": "Rates", "GLD": "Commodities"}.get(symbol.upper(), "UNKNOWN")


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)


def _fingerprint(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _config_key(name: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in name.strip().lower())


def _coerce_config_value(value: Any, default: Any) -> Any:
    if isinstance(default, bool):
        return str(value).lower() in {"1", "true", "yes", "enabled"}
    if isinstance(default, int):
        return int(_number(value))
    if isinstance(default, float):
        raw = _number(value)
        return raw / 100 if raw > 1.0 else raw
    return value
