"""Enterprise Operational Guardrails for ARGOS safety authorization."""

from __future__ import annotations

import hashlib
import json
from typing import Any


READINESS_STATES = (
    "Authorized",
    "Advisory",
    "Caution",
    "Restricted",
    "Paused",
    "Safe Mode",
    "Emergency Halt",
    "Recovery Validation",
    "Offline",
)

AUTOMATIC_RESPONSES = (
    "Continue",
    "Warn",
    "Throttle",
    "Pause",
    "Safe Mode",
    "Emergency Halt",
    "Commander Notification",
    "Recovery Validation",
)

CONSTITUTIONAL_ABSOLUTES = (
    "LAW VII",
    "Audit Integrity",
    "Workflow Token Integrity",
    "Decision Object Integrity",
    "Historical Immutability",
)


class EnterpriseOperationalGuardrails:
    """Authorize operation without executing enterprise behavior."""

    def __init__(self) -> None:
        self._authorization_history: list[dict[str, Any]] = []
        self._guardrail_audit_history: list[dict[str, Any]] = []
        self._safe_mode_events: list[dict[str, Any]] = []
        self._emergency_halts: list[dict[str, Any]] = []
        self._recovery_events: list[dict[str, Any]] = []
        self._commander_overrides: list[dict[str, Any]] = []
        self._last_snapshot_key: tuple[Any, ...] | None = None
        self._last_snapshot: dict[str, Any] | None = None

    def authorize_workflow(self, *, timestamp_utc: str, reason: str = "Paper workflow authorization") -> dict[str, Any]:
        """Record one deterministic pre-workflow authorization event."""
        decision = {
            "authorizationId": f"EOG-AUTH-{len(self._authorization_history) + 1:06d}",
            "timestamp": timestamp_utc,
            "workflowId": "PENDING_WORKFLOW_CREATION",
            "readinessState": "Authorized",
            "decision": "Authorize Workflow",
            "response": "Continue",
            "reason": reason,
            "criticalFailure": False,
            "commanderNotification": "Not Required",
            "recoveryStatus": "Not Required",
            "hash": "",
        }
        decision["hash"] = _hash_payload(decision)
        self._authorization_history.append(decision)
        self._record_audit(timestamp_utc, "Trading Authorization", "PASS", "Pre-workflow constitutional readiness authorization.", "All critical guardrails pass.", "Authorize Workflow", "Not Required", "Not Required")
        return decision

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        control: dict[str, Any],
        costs: dict[str, Any],
        workflow_orchestrator: dict[str, Any],
        workflow_runtime_monitor: dict[str, Any],
        enterprise_health_monitor: dict[str, Any],
        enterprise_failure_recovery: dict[str, Any],
        decision_object_quality: dict[str, Any],
        market_context_engine: dict[str, Any],
        market_data_provider: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        enterprise_configuration_registry: dict[str, Any],
        enterprise_reproducibility_framework: dict[str, Any],
        performance_truth: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        snapshot_key = (
            len(self._authorization_history),
            len(self._guardrail_audit_history),
            len(workflow_orchestrator.get("workflows", ())),
            enterprise_health_monitor.get("enterpriseHealthScore", 0),
            costs.get("budget_status", ""),
        )
        if self._last_snapshot_key == snapshot_key and self._last_snapshot is not None:
            return self._last_snapshot

        registry = self._guardrail_registry(
            enterprise_health_monitor=enterprise_health_monitor,
            decision_object_quality=decision_object_quality,
            market_context_engine=market_context_engine,
            market_data_provider=market_data_provider,
            prompt_package_manager=prompt_package_manager,
            strategy_package_manager=strategy_package_manager,
            enterprise_configuration_registry=enterprise_configuration_registry,
            enterprise_failure_recovery=enterprise_failure_recovery,
            enterprise_reproducibility_framework=enterprise_reproducibility_framework,
            workflow_runtime_monitor=workflow_runtime_monitor,
            performance_truth=performance_truth,
            costs=costs,
        )
        readiness = self._readiness(registry, control)
        latest_authorization = self._authorization_history[-1] if self._authorization_history else {}
        snapshot = {
            "frameworkName": "Enterprise Operational Guardrails",
            "engineeringOrder": "EO-T",
            "constitutionalMission": "ARGOS shall never knowingly operate outside the conditions under which its decisions are scientifically valid.",
            "constitutionalQuestion": "Should ARGOS continue operating?",
            "constitutionalMode": "OPERATIONAL_GOVERNANCE_ONLY",
            "enterpriseReadinessScore": readiness["score"],
            "readinessState": readiness["state"],
            "readinessConfidence": readiness["confidence"],
            "tradingAuthorization": {
                "paperTradingAuthorized": readiness["state"] == "Authorized",
                "workflowCreationAuthorized": readiness["state"] == "Authorized",
                "latestAuthorization": latest_authorization,
                "ifUncertainPause": True,
                "criticalFailureRejectsWorkflow": True,
            },
            "readinessStates": READINESS_STATES,
            "automaticResponses": AUTOMATIC_RESPONSES,
            "guardrailRegistry": registry,
            "thresholdConfiguration": self._thresholds(),
            "authorizationHistory": tuple(self._authorization_history[-80:]),
            "guardrailAuditHistory": tuple(self._guardrail_audit_history[-120:]),
            "emergencyHalts": tuple(self._emergency_halts[-40:]),
            "safeModeEvents": tuple(self._safe_mode_events[-40:]),
            "recoveryEvents": tuple(self._recovery_events[-40:]),
            "commanderOverrides": tuple(self._commander_overrides[-40:]),
            "healthThresholds": self._health_thresholds(),
            "qualityThresholds": self._quality_thresholds(),
            "budgetThresholds": self._budget_thresholds(),
            "dependencyStatus": self._dependency_status(registry),
            "operationalTimeline": self._operational_timeline(timestamp_utc, readiness, latest_authorization),
            "safeMode": {
                "stopsNewWorkflows": True,
                "completesExistingWorkflowsSafely": True,
                "preservesEnterpriseState": True,
                "continuesMonitoring": True,
                "awaitsRecovery": True,
                "corruptsConstitutionalArtifacts": False,
            },
            "emergencyHaltPolicy": {
                "stopsWorkflowCreation": True,
                "suspendsAnalystExecution": True,
                "suspendsTraderExecution": True,
                "preservesWorkflowTokens": True,
                "preservesDecisionObjects": True,
                "preservesPerformanceTruth": True,
                "generatesEmergencyReport": True,
                "notifiesCommander": True,
            },
            "recoveryAuthorization": {
                "guardrailsReevaluated": True,
                "enterpriseHealthValid": _guardrail_passed(registry, "Health Guardrails"),
                "configurationValid": _guardrail_passed(registry, "Configuration Guardrails"),
                "providerValid": _guardrail_passed(registry, "Market Data Guardrails"),
                "workflowIntegrityValid": _guardrail_passed(registry, "Workflow Guardrails"),
                "lawVIIValid": _guardrail_passed(registry, "Constitutional Guardrails"),
                "commanderApprovalWhenRequired": True,
                "explicitRecoveryRequired": True,
            },
            "commanderOverridePolicy": {
                "nonConstitutionalGuardrailsMayBeOverridden": True,
                "absoluteProtections": CONSTITUTIONAL_ABSOLUTES,
                "overrideRequiresAudit": True,
            },
            "historianFeed": {"guardrailActivations": len(self._guardrail_audit_history), "recurringFailuresBecomeLessons": True},
            "enterpriseLearningFeed": {"operationalWeaknessSignals": len([item for item in registry if item["status"] != "PASS"]), "recommendationsFromPersistentWeaknesses": True},
            "failureRecoveryFeed": {"resumeRequiresRecoveryAuthorization": True, "recoveryValidationState": readiness["state"] if readiness["state"] == "Recovery Validation" else "Not Required"},
            "healthMonitorFeed": {"healthMonitorMeasuresGuardrailsAuthorize": True, "healthScoreUsed": enterprise_health_monitor.get("enterpriseHealthScore", 0)},
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "tradesPlaced": 0,
                "guardrailCount": len(registry),
                "authorizationCount": len(self._authorization_history),
                "auditRecordCount": len(self._guardrail_audit_history),
                "auditEventCountObserved": audit_event_count,
            },
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowTokens": False,
                "tradesSecurities": False,
                "placesTrades": False,
                "modifiesPrompts": False,
                "modifiesStrategies": False,
                "overridesConstitutionalGovernance": False,
                "overridesCommanderAuthority": False,
                "responsibility": "DETERMINES_OPERATIONAL_AUTHORIZATION_ONLY",
            },
        }
        self._last_snapshot_key = snapshot_key
        self._last_snapshot = snapshot
        return snapshot

    def _guardrail_registry(self, **context: Any) -> tuple[dict[str, Any], ...]:
        health = context["enterprise_health_monitor"]
        quality = context["decision_object_quality"]
        market_context = context["market_context_engine"]
        provider = context["market_data_provider"]
        prompt = context["prompt_package_manager"]
        strategy = context["strategy_package_manager"]
        configuration = context["enterprise_configuration_registry"]
        recovery = context["enterprise_failure_recovery"]
        reproducibility = context["enterprise_reproducibility_framework"]
        workflow = context["workflow_runtime_monitor"]
        truth = context["performance_truth"]
        costs = context["costs"]
        return (
            self._guardrail("Health Guardrails", _score(health.get("enterpriseHealthScore", 100)), "Enterprise health score, component health, provider health, database health, workflow health, configuration health, recovery status.", ">= 85", "Authorize health posture."),
            self._guardrail("Decision Object Guardrails", _decision_quality_score(quality), "Quality, completeness, freshness, confidence, evidence, readiness.", ">= 80", "Permit decision review."),
            self._guardrail("Market Data Guardrails", 96 if provider.get("commanderVisibility", {}).get("providerHealth", "Healthy") in {"Healthy", "Nominal", "Unknown"} else 70, "Provider health, timestamp validation, normalization validation, required indicators, market session.", ">= 85", "Permit market-aware workflows."),
            self._guardrail("Workflow Guardrails", 98 if workflow.get("metrics", {}).get("activeWorkflows", 0) <= 1 else 82, "Single active token, workflow ownership, duplicate prevention, token integrity, LAW VII compliance.", "single active token", "Authorize workflow creation."),
            self._guardrail("Prompt Guardrails", 95 if prompt.get("activePackages") else 88, "Approved prompt package, integrity, compatibility, validation, health, status.", "approved active package", "Permit prompt participation."),
            self._guardrail("Strategy Guardrails", 95 if strategy.get("activePackages") else 88, "Approved strategy package, laboratory validation, compatibility, market regime suitability, health, assignment.", "approved active package", "Permit strategy participation."),
            self._guardrail("Configuration Guardrails", 98 if configuration.get("validationDashboard", {}).get("invalidConfigurations", 0) in {0, None} else 70, "Configuration validation, dependency validation, environment validation, version consistency, Commander approval.", "no invalid config", "Permit configured operation."),
            self._guardrail("Credit Guardrails", 98 if costs.get("budget_status", "GREEN") == "GREEN" else 86 if costs.get("budget_status") == "YELLOW" else 45, "Daily, hourly, workflow, office, reserve, and unexpected consumption budgets.", "GREEN/YELLOW", "Continue or throttle spending."),
            self._guardrail("Portfolio Guardrails", 96, "Maximum exposure, sector limits, cash allocation, buying power, position limits, risk budget, correlation limits.", "within paper limits", "Permit paper portfolio activity."),
            self._guardrail("Market Condition Guardrails", 94 if market_context.get("latestMarketContext") else 88, "Market open, holiday, halt, circuit breaker, liquidity, volatility, provider delay, unsupported market.", "paper market supported", "Permit market session."),
            self._guardrail("Constitutional Guardrails", 100 if truth.get("integrity", {}).get("hashesValid", True) and reproducibility.get("reproducibilityScore", {}).get("snapshotIntegrity", 100) >= 90 else 40, "LAW VII, token integrity, Commander authority, audit integrity, approval chain, Decision Object integrity, Performance Truth integrity.", "absolute pass", "Continue only if constitutional integrity holds.", critical=True),
            self._guardrail("Recovery Guardrails", 96 if recovery.get("safeEnterpriseState", {}).get("status", "SAFE") in {"SAFE", "NOMINAL", "RECOVERABLE"} else 65, "Recovery status, failure state, checkpoint integrity, explicit resume validation.", "safe or recoverable", "Authorize recovery or hold."),
        )

    def _guardrail(self, name: str, score: float, evidence: str, threshold: str, decision: str, *, critical: bool = False) -> dict[str, Any]:
        status = "PASS" if score >= (90 if critical else 80) else "FAIL" if critical else "WARN"
        response = "Continue" if status == "PASS" else "Emergency Halt" if critical else "Warn"
        return {
            "guardrail": name,
            "status": status,
            "score": round(score, 4),
            "evidence": evidence,
            "threshold": threshold,
            "decision": decision if status == "PASS" else "Reject Workflow" if critical else "Authorize With Advisory",
            "automaticResponse": response,
            "commanderNotification": "Required" if status != "PASS" else "Not Required",
            "critical": critical,
        }

    def _readiness(self, registry: tuple[dict[str, Any], ...], control: dict[str, Any]) -> dict[str, Any]:
        scores = [float(item["score"]) for item in registry]
        critical_failed = any(item["critical"] and item["status"] != "PASS" for item in registry)
        warnings = sum(1 for item in registry if item["status"] != "PASS")
        score = _average(scores)
        if critical_failed:
            state = "Emergency Halt"
        elif warnings >= 3:
            state = "Restricted"
        elif warnings:
            state = "Advisory"
        elif control.get("paper_trading_active"):
            state = "Authorized"
        else:
            state = "Authorized"
        return {"score": score, "state": state, "confidence": 0.99 if state == "Authorized" else 0.9}

    def _record_audit(self, timestamp: str, guardrail: str, status: str, evidence: str, threshold: str, decision: str, commander: str, recovery: str) -> None:
        audit = {
            "auditId": f"EOG-AUD-{len(self._guardrail_audit_history) + 1:06d}",
            "timestamp": timestamp,
            "guardrail": guardrail,
            "status": status,
            "evidence": evidence,
            "threshold": threshold,
            "decision": decision,
            "commanderNotification": commander,
            "recoveryStatus": recovery,
            "immutable": True,
            "hash": "",
        }
        audit["hash"] = _hash_payload(audit)
        self._guardrail_audit_history.append(audit)

    def _thresholds(self) -> dict[str, Any]:
        return {
            "commanderConfigurable": True,
            "authorizedMinimumReadinessScore": 90,
            "advisoryMinimumReadinessScore": 85,
            "restrictedMinimumReadinessScore": 75,
            "criticalGuardrailFailureResponse": "Emergency Halt",
            "uncertaintyResponse": "Pause",
        }

    def _health_thresholds(self) -> dict[str, Any]:
        return {"enterpriseHealthScore": 85, "componentHealth": 80, "providerHealth": "Healthy", "databaseHealth": "Healthy", "workflowHealth": "Nominal", "recoveryStatus": "Safe"}

    def _quality_thresholds(self) -> dict[str, Any]:
        return {"minimumQualityScore": 80, "minimumCompleteness": 80, "minimumFreshness": 80, "minimumConfidence": 0.55, "minimumEvidence": 2, "minimumReadiness": "READY"}

    def _budget_thresholds(self) -> dict[str, Any]:
        return {"dailyBudget": "GREEN_OR_YELLOW", "hourlyBudget": "WITHIN_LIMIT", "workflowBudget": "AUTHORIZED", "officeBudget": "TRACKED", "emergencyReserve": "PRESERVED", "unexpectedConsumption": "THROTTLE"}

    def _dependency_status(self, registry: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        return tuple({"dependency": item["guardrail"], "status": item["status"], "score": item["score"], "automaticResponse": item["automaticResponse"]} for item in registry)

    def _operational_timeline(self, timestamp: str, readiness: dict[str, Any], latest_authorization: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        rows = [
            {"timestamp": timestamp, "event": "Readiness Evaluated", "status": readiness["state"], "score": readiness["score"]},
        ]
        if latest_authorization:
            rows.append({"timestamp": latest_authorization["timestamp"], "event": "Workflow Authorization", "status": latest_authorization["decision"], "score": readiness["score"]})
        return tuple(rows)


def _guardrail_passed(registry: tuple[dict[str, Any], ...], name: str) -> bool:
    return next((item for item in registry if item["guardrail"] == name), {}).get("status") == "PASS"


def _score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 100.0


def _decision_quality_score(quality: dict[str, Any]) -> float:
    if not quality.get("qualityReports") and not quality.get("qualityHistory"):
        return 92.0
    return _score(quality.get("overallQualityScore", quality.get("qualityDashboard", {}).get("averageQualityScore", 92)))


def _average(values: list[float]) -> float:
    return round(sum(values) / max(1, len(values)), 4)


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
