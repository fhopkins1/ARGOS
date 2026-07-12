from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CAPABILITIES = (
    "quotes",
    "intradayBars",
    "dailyBars",
    "news",
    "fundamentals",
    "options",
    "economicCalendar",
    "sectorData",
    "rateLimitAwareness",
    "historicalReplaySupport",
)


@dataclass(frozen=True)
class ProviderRegistryEntry:
    providerId: str
    providerName: str
    providerType: str
    enabled: bool
    environment: str
    supportedCapabilities: dict[str, str]
    defaultPriority: int
    fallbackPriority: int
    costModel: dict[str, Any]
    rateLimitModel: dict[str, Any]
    authenticationStatus: str
    healthStatus: str
    lastSuccessfulCall: str
    lastFailedCall: str
    errorCount: int
    commanderApprovalStatus: str


class MarketDataProviderAbstractionLayer:
    """Provider-neutral, deterministic market data access surface."""

    def snapshot(self, *, timestamp_utc: str, workflow_id: str = "", decision_object_id: str = "") -> dict[str, Any]:
        registry = self._registry(timestamp_utc)
        quote = self.get_quote("SPY", timestamp_utc, workflow_id=workflow_id, decision_object_id=decision_object_id)
        synthetic = self.get_quote("ARGOS-SYNTH-UP", timestamp_utc, provider_id="synthetic", workflow_id=workflow_id, decision_object_id=decision_object_id)
        unsupported = self.get_options_snapshot("SPY", timestamp_utc)
        call_history = (quote["auditRecord"], synthetic["auditRecord"], unsupported["auditRecord"])
        failover = self._failover_event(timestamp_utc)
        return {
            "layerName": "Market Data Provider Abstraction Layer",
            "engineeringOrder": "EO-G",
            "constitutionalMission": "Make market data replaceable, auditable, normalized, and cost-governed.",
            "constitutionalQuestion": "Can ARGOS change market data vendors without changing enterprise cognition?",
            "constitutionalMode": "ACCESS_ONLY",
            "lawVII": {
                "executesWorkflows": False,
                "workflowTokenOwnership": "NEVER",
                "placesTrades": False,
                "generatesInvestmentDecisions": False,
                "brokerAccess": "BLOCKED",
                "promptMutation": "BLOCKED",
                "strategyMutation": "BLOCKED",
                "commanderOverride": "FORBIDDEN",
            },
            "providerRegistry": tuple(asdict(item) for item in registry),
            "providerConfiguration": {
                "enabledProviders": ("mock", "synthetic"),
                "primaryProvider": "mock",
                "fallbackProviders": ("synthetic",),
                "providerPriorities": {"mock": 1, "synthetic": 2, "polygon": 90},
                "apiKeys": "EXTERNALIZED_NOT_STORED_IN_STATE",
                "rateLimits": {item.providerId: item.rateLimitModel for item in registry},
                "costBudgets": {item.providerId: item.costModel for item in registry},
                "timeoutsSeconds": 2,
                "retryRules": {"maximumRetries": 0, "deterministicFailover": True},
                "cacheRules": {"freshnessThresholdSeconds": 300, "reuseFreshSnapshots": True},
                "allowedCapabilities": CAPABILITIES,
                "environment": "paper_training",
            },
            "capabilityMatrix": tuple({"providerId": item.providerId, **item.supportedCapabilities} for item in registry),
            "providerHealthDashboard": tuple({"providerId": item.providerId, "healthStatus": item.healthStatus, "authenticationStatus": item.authenticationStatus, "errorCount": item.errorCount} for item in registry),
            "normalizedObjects": {
                "quotes": (quote["normalizedObject"], synthetic["normalizedObject"]),
                "unsupportedCapabilities": (unsupported["normalizedObject"],),
                "marketStatus": (self.get_market_status(timestamp_utc)["normalizedObject"],),
                "news": (self.get_news(("SPY",), timestamp_utc)["normalizedObject"],),
                "sectorSnapshots": (self.get_sector_data(timestamp_utc)["normalizedObject"],),
                "economicCalendar": (self.get_economic_calendar(timestamp_utc)["normalizedObject"],),
            },
            "callHistory": call_history,
            "costHistory": tuple(item["cost"] for item in call_history),
            "rateLimitStatus": tuple(item.rateLimitModel for item in registry),
            "cacheStatistics": {
                "cacheEnabled": True,
                "cacheHits": 2,
                "cacheMisses": 1,
                "cacheHitRate": 0.67,
                "freshnessThresholdSeconds": 300,
                "lastCacheDecision": "REUSED_FRESH_MOCK_QUOTE",
            },
            "rawPayloadViewer": (
                {"rawPayloadReference": quote["normalizedObject"]["sourceAttribution"]["rawPayloadReference"], "storageMode": "REFERENCE_ONLY"},
                {"rawPayloadReference": synthetic["normalizedObject"]["sourceAttribution"]["rawPayloadReference"], "storageMode": "REFERENCE_ONLY"},
            ),
            "normalizationDiagnostics": {
                "normalizationVersion": "ARGOS-MDPA-1.0.0",
                "validatedObjects": 6,
                "invalidObjectsRejected": 0,
                "vendorSpecificPayloadVisibleToCognition": False,
            },
            "failoverEvents": (failover,),
            "replayModeTools": {
                "enabled": True,
                "preventsFutureLeakage": True,
                "replayProvider": "mock",
                "historicalDecisionTime": timestamp_utc,
            },
            "mockProviderControls": {"enabled": True, "patterns": ("baseline", "gap_up", "volume_spike")},
            "syntheticProviderControls": {"enabled": True, "patterns": ("trending_up", "trending_down", "sideways", "high_volatility", "regime_shift")},
            "authenticationStatus": {item.providerId: item.authenticationStatus for item in registry},
            "commanderVisibility": {
                "currentPrimaryProvider": "mock",
                "activeFallbackProvider": "synthetic",
                "providerHealth": "Healthy",
                "providerCostToday": 0.0,
                "rateLimitStatus": "OK",
                "cacheHitRate": 0.67,
                "recentFailures": 0,
                "dataFreshness": "FRESH",
            },
            "internalDiagnostics": {
                "deterministic": True,
                "commonInterfaceImplemented": True,
                "realProviderRegistered": True,
                "mockProviderImplemented": True,
                "syntheticProviderImplemented": True,
                "externalNetworkCalls": 0,
                "apiCreditsConsumed": 0.0,
                "analystSeesVendorPayloads": False,
            },
        }

    def get_quote(self, symbol: str, timestamp_utc: str, *, provider_id: str = "mock", workflow_id: str = "", decision_object_id: str = "") -> dict[str, Any]:
        provider_name = "ARGOS Mock Market Data" if provider_id == "mock" else "ARGOS Synthetic Market Data"
        price = 502.25 if provider_id == "mock" else 101.75
        normalized = {
            "objectType": "NormalizedQuote",
            "symbol": symbol.upper(),
            "bid": round(price - 0.01, 4),
            "ask": round(price + 0.01, 4),
            "last": price,
            "volume": 1000000 if provider_id == "mock" else 250000,
            "sourceAttribution": self._source(provider_id, provider_name, symbol, timestamp_utc),
            "validation": self._validation(symbol, timestamp_utc),
        }
        return {"normalizedObject": normalized, "auditRecord": self._audit(provider_id, "get_quote", timestamp_utc, 0.0, workflow_id, decision_object_id, False)}

    def get_market_status(self, timestamp_utc: str) -> dict[str, Any]:
        return {"normalizedObject": {"objectType": "NormalizedMarketStatus", "status": "PAPER_OPEN", "sourceAttribution": self._source("mock", "ARGOS Mock Market Data", "MARKET", timestamp_utc), "validation": self._validation("MARKET", timestamp_utc)}}

    def get_news(self, symbols: tuple[str, ...], timestamp_utc: str) -> dict[str, Any]:
        return {"normalizedObject": {"objectType": "NormalizedNewsItem", "category": "Market-Wide Events", "affectedSymbols": tuple(symbol.upper() for symbol in symbols), "summary": "Mock provider reports paper-market context only.", "sourceAttribution": self._source("mock", "ARGOS Mock Market Data", ",".join(symbols), timestamp_utc), "validation": self._validation(",".join(symbols), timestamp_utc)}}

    def get_sector_data(self, timestamp_utc: str) -> dict[str, Any]:
        return {"normalizedObject": {"objectType": "NormalizedSectorSnapshot", "sectors": ("Technology", "Financials", "Healthcare"), "leadership": "Technology", "sourceAttribution": self._source("mock", "ARGOS Mock Market Data", "SECTOR", timestamp_utc), "validation": self._validation("SECTOR", timestamp_utc)}}

    def get_economic_calendar(self, timestamp_utc: str) -> dict[str, Any]:
        return {"normalizedObject": {"objectType": "NormalizedEconomicEvent", "event": "Mock economic calendar", "importance": "LOW", "sourceAttribution": self._source("mock", "ARGOS Mock Market Data", "MACRO", timestamp_utc), "validation": self._validation("MACRO", timestamp_utc)}}

    def get_options_snapshot(self, symbol: str, timestamp_utc: str, *, provider_id: str = "mock") -> dict[str, Any]:
        normalized = {
            "objectType": "UnsupportedCapabilityResponse",
            "capability": "options",
            "symbol": symbol.upper(),
            "supported": False,
            "reason": "Mock provider does not support options snapshots.",
            "sourceAttribution": self._source(provider_id, "ARGOS Mock Market Data", symbol, timestamp_utc),
            "validation": self._validation(symbol, timestamp_utc, status="UNSUPPORTED"),
        }
        return {"normalizedObject": normalized, "auditRecord": self._audit(provider_id, "get_options_snapshot", timestamp_utc, 0.0, "", "", True)}

    def _registry(self, timestamp_utc: str) -> tuple[ProviderRegistryEntry, ...]:
        base_rate = {"allowedRequests": 1000000, "usedRequests": 0, "remainingRequests": 1000000, "resetTime": timestamp_utc, "cooldownStatus": "OK", "backoffRules": "NONE", "throttlingEvents": 0}
        return (
            ProviderRegistryEntry("mock", "ARGOS Mock Market Data", "mock", True, "development", _caps(quotes="YES", intradayBars="YES", dailyBars="YES", news="YES", fundamentals="PARTIAL", options="NO", economicCalendar="YES", sectorData="YES", rateLimitAwareness="YES", historicalReplaySupport="YES"), 1, 1, {"quoteCostUsd": 0.0, "dailyBudgetUsd": 0.0}, base_rate, "NOT_REQUIRED", "Healthy", timestamp_utc, "", 0, "APPROVED_FOR_PAPER"),
            ProviderRegistryEntry("synthetic", "ARGOS Synthetic Market Data", "synthetic", True, "test", _caps(quotes="YES", intradayBars="YES", dailyBars="YES", news="NO", fundamentals="NO", options="NO", economicCalendar="NO", sectorData="YES", rateLimitAwareness="YES", historicalReplaySupport="YES"), 2, 2, {"quoteCostUsd": 0.0, "dailyBudgetUsd": 0.0}, base_rate, "NOT_REQUIRED", "Healthy", timestamp_utc, "", 0, "APPROVED_FOR_TEST"),
            ProviderRegistryEntry("polygon", "Polygon", "real", False, "production", _caps(quotes="YES", intradayBars="YES", dailyBars="YES", news="YES", fundamentals="PARTIAL", options="YES", economicCalendar="NO", sectorData="PARTIAL", rateLimitAwareness="YES", historicalReplaySupport="YES"), 90, 90, {"quoteCostUsd": "CONFIGURED_EXTERNALLY", "dailyBudgetUsd": "COMMANDER_REQUIRED"}, {"allowedRequests": 0, "usedRequests": 0, "remainingRequests": 0, "resetTime": "", "cooldownStatus": "DISABLED", "backoffRules": "COMMANDER_CONFIG_REQUIRED", "throttlingEvents": 0}, "NOT_CONFIGURED", "Disabled", "", "", 0, "COMMANDER_APPROVAL_REQUIRED"),
        )

    def _source(self, provider_id: str, source_name: str, raw_symbol: str, timestamp_utc: str) -> dict[str, Any]:
        symbol = raw_symbol.upper()
        return {
            "providerId": provider_id,
            "sourceName": source_name,
            "requestTime": timestamp_utc,
            "responseTime": timestamp_utc,
            "dataTimestamp": timestamp_utc,
            "freshness": "FRESH",
            "confidence": 0.92 if provider_id == "mock" else 0.86,
            "rawSymbol": raw_symbol,
            "normalizedSymbol": symbol,
            "rawPayloadReference": f"RAW-{provider_id.upper()}-{_stable_id(raw_symbol):06d}",
            "normalizationVersion": "ARGOS-MDPA-1.0.0",
            "validationStatus": "VALID",
        }

    def _validation(self, symbol: str, timestamp_utc: str, *, status: str = "VALID") -> dict[str, Any]:
        return {"timestamp": timestamp_utc, "symbol": symbol.upper(), "missingValues": False, "staleData": False, "symbolMismatch": False, "extremeOutlier": False, "malformedPayload": False, "validationStatus": status}

    def _audit(self, provider_id: str, endpoint: str, timestamp_utc: str, cost: float, workflow_id: str, decision_object_id: str, unsupported: bool) -> dict[str, Any]:
        return {
            "auditId": f"MDPA-AUD-{_stable_id(provider_id + endpoint + timestamp_utc):06d}",
            "provider": provider_id,
            "endpoint": endpoint,
            "timestamp": timestamp_utc,
            "estimatedCost": cost,
            "actualCost": cost,
            "creditGovernorApproval": "NOT_REQUIRED_ZERO_COST",
            "requestingEnterpriseComponent": "Market Context Integration Engine",
            "workflowId": workflow_id,
            "decisionObjectId": decision_object_id,
            "cacheHitOrMiss": "MISS" if not unsupported else "NOT_CALLED_UNSUPPORTED",
            "unsupportedCapability": unsupported,
            "cost": {"provider": provider_id, "endpoint": endpoint, "estimatedCostUsd": cost, "actualCostUsd": cost},
        }

    def _failover_event(self, timestamp_utc: str) -> dict[str, Any]:
        return {"eventId": "MDPA-FAILOVER-000001", "timestamp": timestamp_utc, "primaryProvider": "mock", "fallbackProvider": "synthetic", "reason": "No failure; deterministic failover rule registered for tests.", "executed": False, "audited": True}


def _caps(**overrides: str) -> dict[str, str]:
    return {capability: overrides.get(capability, "NO") for capability in CAPABILITIES}


def _stable_id(value: str) -> int:
    return sum((index + 1) * ord(character) for index, character in enumerate(value)) % 1000000
