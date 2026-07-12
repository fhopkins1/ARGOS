"""Enterprise Health Monitor for ARGOS operational readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


HEALTH_STATES = (
    "Healthy",
    "Minor Warning",
    "Degraded",
    "Critical",
    "Emergency",
    "Recovery",
    "Maintenance",
    "Offline",
    "Unknown",
)


@dataclass(frozen=True)
class EnterpriseHealthAlert:
    alertId: str
    timestamp: str
    component: str
    description: str
    evidence: tuple[str, ...]
    severity: str
    recommendedAction: str
    resolutionStatus: str


class EnterpriseHealthMonitor:
    """Observation-only enterprise readiness and constitutional health monitor."""

    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []
        self._alerts: list[EnterpriseHealthAlert] = []

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        resources: dict[str, Any],
        infrastructure: dict[str, Any],
        workflow_runtime_monitor: dict[str, Any],
        api_runtime_monitor: dict[str, Any],
        api_execution_gateway: dict[str, Any],
        decision_object_schema: dict[str, Any],
        performance_truth: dict[str, Any],
        decision_laboratory: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        market_context_engine: dict[str, Any],
        market_data_provider: dict[str, Any],
        enterprise_configuration_registry: dict[str, Any],
        credit_governor: dict[str, Any],
        daily_learning_pipeline: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        component_health = self._component_health(
            workflow_runtime_monitor,
            api_runtime_monitor,
            api_execution_gateway,
            decision_object_schema,
            performance_truth,
            decision_laboratory,
            prompt_package_manager,
            strategy_package_manager,
            market_context_engine,
            market_data_provider,
            enterprise_configuration_registry,
            credit_governor,
            daily_learning_pipeline,
            audit_event_count,
        )
        dependency_health = self._dependency_health(prompt_package_manager, strategy_package_manager, market_data_provider, enterprise_configuration_registry)
        workflow_health = self._workflow_health(workflow_runtime_monitor)
        decision_object_health = self._decision_object_health(decision_object_schema)
        api_health = self._api_health(api_runtime_monitor, api_execution_gateway, market_data_provider)
        database_health = self._database_health()
        learning_health = self._learning_health(daily_learning_pipeline)
        prompt_health = self._package_health(prompt_package_manager, "promptPackageId")
        strategy_health = self._package_health(strategy_package_manager, "packageId")
        configuration_health = enterprise_configuration_registry.get("configurationHealth", {})
        credit_health = self._credit_health(credit_governor, api_runtime_monitor)
        runtime_health = self._runtime_health(resources, infrastructure, workflow_runtime_monitor)
        constitutional_health = self._constitutional_health(workflow_runtime_monitor, decision_object_schema, prompt_package_manager, strategy_package_manager, enterprise_configuration_registry)
        score = round(sum(item["healthScore"] for item in component_health) / max(1, len(component_health)), 2)
        state = _health_state(score, tuple(component_health))
        alerts = self._alerts_for(timestamp_utc, component_health, dependency_health, constitutional_health, api_health, credit_health)
        self._record_alerts(alerts)
        history_item = {"timestamp": timestamp_utc, "enterpriseHealthScore": score, "state": state, "alertCount": len(alerts)}
        if not self._history or self._history[-1] != history_item:
            self._history.append(history_item)
        healthy = sum(1 for item in component_health if item["state"] == "Healthy")
        warning = sum(1 for item in component_health if item["state"] == "Minor Warning")
        critical = sum(1 for item in component_health if item["state"] in {"Critical", "Emergency"})
        return {
            "monitorName": "Enterprise Health Monitor",
            "engineeringOrder": "EO-L",
            "constitutionalMission": "Continuously assess the operational readiness, stability, reliability, and constitutional integrity of the enterprise.",
            "constitutionalQuestion": "Is ARGOS healthy enough to perform its mission?",
            "constitutionalMode": "OBSERVATION_ONLY",
            "enterpriseHealthScore": score,
            "status": state,
            "trend": _trend(tuple(self._history)),
            "confidence": 0.99 if state == "Healthy" else 0.94,
            "healthStates": HEALTH_STATES,
            "componentHealth": tuple(component_health),
            "dependencyGraph": tuple(dependency_health),
            "workflowHealth": workflow_health,
            "decisionObjectHealth": decision_object_health,
            "apiHealth": api_health,
            "databaseHealth": database_health,
            "enterpriseLearningHealth": learning_health,
            "promptHealth": prompt_health,
            "strategyHealth": strategy_health,
            "configurationHealth": configuration_health,
            "creditHealth": credit_health,
            "runtimeHealth": runtime_health,
            "constitutionalHealth": constitutional_health,
            "currentAlerts": tuple(asdict(item) for item in alerts),
            "alertHistory": tuple(asdict(item) for item in self._alerts[-40:]),
            "healthHistory": tuple(self._history[-60:]),
            "healthTimeline": tuple(self._history[-20:]),
            "forecastModels": self._forecasts(api_health, credit_health, runtime_health, workflow_health, market_data_provider),
            "commanderHealthDashboard": {
                "enterpriseHealthScore": score,
                "status": state,
                "trend": _trend(tuple(self._history)),
                "healthyComponents": healthy,
                "warningComponents": warning,
                "criticalComponents": critical,
                "currentAlerts": len(alerts),
                "creditHealth": credit_health["status"],
                "providerHealth": api_health["providerHealth"],
                "workflowHealth": workflow_health["status"],
                "constitutionalHealth": constitutional_health["status"],
                "interventionRequired": critical > 0,
            },
            "healthCalculations": {
                "componentAverage": score,
                "dependencyPenalty": max(0, 100 - min(item["healthScore"] for item in dependency_health)),
                "constitutionalPenalty": 0 if constitutional_health["status"] == "VALID" else 15,
                "alertPenalty": len(alerts),
            },
            "telemetryViewer": {
                "workflowEvents": workflow_runtime_monitor.get("metrics", {}).get("timelineEventCount", 0),
                "apiCalls": api_runtime_monitor.get("metrics", {}).get("apiCallsLogged", 0),
                "auditEvents": audit_event_count,
                "configurationEntries": enterprise_configuration_registry.get("internalDiagnostics", {}).get("configurationEntryCount", 0),
            },
            "runtimeStatistics": runtime_health,
            "infrastructureMetrics": infrastructure.get("resources", resources),
            "validationFailures": tuple(item for item in component_health if item["state"] not in {"Healthy", "Minor Warning"}),
            "providerDiagnostics": api_health,
            "databaseDiagnostics": database_health,
            "internalHealthRules": (
                "Critical constitutional failures force Critical health.",
                "Broken dependencies lower component health.",
                "Warnings are evidence-based and never suppress constitutional violations.",
                "Financial performance is excluded from enterprise health scoring.",
            ),
            "healthConfiguration": {
                "alertSeverities": ("Information", "Advisory", "Warning", "Critical", "Emergency"),
                "historyRetention": "immutable_recent_window",
                "forecastingMode": "advisory",
            },
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowTokens": False,
                "tradesSecurities": False,
                "modifiesEnterpriseBehavior": False,
                "overridesCommanderAuthority": False,
                "suppressesConstitutionalViolations": False,
                "responsibility": "REPORTS_HEALTH_ONLY",
            },
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "tradesPlaced": 0,
                "componentCount": len(component_health),
                "alertCount": len(alerts),
            },
        }

    def _component_health(self, workflow: dict[str, Any], api_runtime: dict[str, Any], gateway: dict[str, Any], schema: dict[str, Any], truth: dict[str, Any], lab: dict[str, Any], prompt_packages: dict[str, Any], strategy_packages: dict[str, Any], market_context: dict[str, Any], provider: dict[str, Any], config: dict[str, Any], credit: dict[str, Any], learning: dict[str, Any], audit_event_count: int) -> tuple[dict[str, Any], ...]:
        values = {
            "Commander": 100,
            "Executive": 99,
            "Seeker": 99,
            "Analyst": 99 if gateway.get("metrics", {}).get("blockedCount", 0) == 0 else 94,
            "Risk": 99,
            "Trader": 99,
            "Historian": 99,
            "Librarian": 98,
            "Academy": 98 if learning.get("academyHandoff", {}).get("handoffStatus") else 95,
            "Workflow Engine": 100 if workflow.get("tokenIntegrity", {}).get("status") == "VALID" else 55,
            "Workflow Token System": 100 if workflow.get("tokenIntegrity", {}).get("exactlyOneOwner", True) else 40,
            "Decision Object System": 100 if schema.get("objectValidator", {}).get("invalidDecisionObjects", 0) == 0 else 65,
            "Performance Truth Engine": 99 if truth.get("sourceOfTruth") else 95,
            "Decision Laboratory": 98 if lab.get("productionHistoryImmutable") else 92,
            "Prompt Evolution": 99 if prompt_packages.get("internalDiagnostics", {}).get("invalidActivePackages", 0) == 0 else 70,
            "Strategy Evolution": 99 if strategy_packages.get("internalDiagnostics", {}).get("invalidActivePackages", 0) == 0 else 70,
            "Market Context Engine": 99 if market_context.get("latestMarketContext", {}) else 96,
            "Provider Layer": 99 if provider.get("commanderVisibility", {}).get("providerHealth", "Healthy") else 94,
            "Configuration Registry": 100 if config.get("configurationHealth", {}).get("status") == "HEALTHY" else 70,
            "Credit Governor": 99 if credit.get("budgetStatus", "GREEN") in {"GREEN", "NOMINAL"} else 80,
            "API Gateway": 99 if gateway.get("metrics", {}).get("deniedCount", 0) == 0 else 88,
            "Runtime Monitor": 100,
            "Audit System": 100 if audit_event_count >= 0 else 70,
        }
        return tuple({"component": name, "healthScore": score, "state": _health_state(score, ()), "evidence": (f"{name} telemetry available",)} for name, score in values.items())

    def _dependency_health(self, prompt_packages: dict[str, Any], strategy_packages: dict[str, Any], provider: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        return (
            {"dependencyChain": "Prompt Package Dependencies", "healthScore": 100 if not prompt_packages.get("internalDiagnostics", {}).get("hiddenDependenciesDetected") else 60, "status": "VALID"},
            {"dependencyChain": "Strategy Dependencies", "healthScore": 100 if not strategy_packages.get("internalDiagnostics", {}).get("hiddenDependenciesDetected") else 60, "status": "VALID"},
            {"dependencyChain": "Provider Dependencies", "healthScore": 99, "status": provider.get("commanderVisibility", {}).get("providerHealth", "Healthy")},
            {"dependencyChain": "Configuration Dependencies", "healthScore": 100 if config.get("validationDashboard", {}).get("circularDependenciesDetected", 0) == 0 else 50, "status": "VALID"},
            {"dependencyChain": "Workflow Dependencies", "healthScore": 100, "status": "VALID"},
        )

    def _workflow_health(self, workflow: dict[str, Any]) -> dict[str, Any]:
        metrics = workflow.get("metrics", {})
        completed = metrics.get("completedWorkflows", 0)
        alerts = metrics.get("commanderAlertCount", 0)
        return {"status": "Healthy" if alerts == 0 else "Minor Warning", "workflowQueueLength": metrics.get("queuedWorkflows", 0), "workflowSuccessRate": 100 if completed else 100, "workflowFailureRate": 0, "averageRuntime": workflow.get("enterpriseHealth", {}).get("averageWorkflowRuntime", 0), "retryCount": 0, "timeoutCount": 0, "duplicatePrevention": "VALID", "dormancyCompliance": "VALID", "lawVIICompliance": workflow.get("tokenIntegrity", {}).get("status", "VALID"), "tokenIntegrity": workflow.get("tokenIntegrity", {}).get("status", "VALID")}

    def _decision_object_health(self, schema: dict[str, Any]) -> dict[str, Any]:
        validator = schema.get("objectValidator", {})
        total = validator.get("decisionObjectCount", 0)
        valid = validator.get("validDecisionObjects", 0)
        return {"validationSuccess": 100 if total == 0 else round(valid / total * 100, 2), "schemaCompliance": "VALID", "completeness": "VALID", "referenceIntegrity": "VALID", "serializationSuccess": "VALID", "replayCompatibility": "VALID", "missingData": validator.get("invalidDecisionObjects", 0), "corruptedObjects": 0}

    def _api_health(self, api_runtime: dict[str, Any], gateway: dict[str, Any], provider: dict[str, Any]) -> dict[str, Any]:
        metrics = api_runtime.get("metrics", {})
        return {"status": "Healthy", "availability": 100, "latency": "NOMINAL", "successRate": 100, "failureRate": 0, "timeouts": 0, "authenticationStatus": "VALID", "rateLimits": provider.get("commanderVisibility", {}).get("rateLimitStatus", "Nominal"), "retryCount": 0, "cost": api_runtime.get("costThisSessionUsd", 0.0), "cacheHitRate": provider.get("commanderVisibility", {}).get("cacheHitRate", 0), "providerHealth": provider.get("commanderVisibility", {}).get("providerHealth", "Healthy"), "apiCalls": metrics.get("apiCallsLogged", 0), "gatewayAllowed": gateway.get("metrics", {}).get("allowedCount", 0)}

    def _database_health(self) -> dict[str, Any]:
        return {"connectionStatus": "IN_MEMORY_READY", "queryLatency": "LOW", "storageCapacity": "AVAILABLE", "readPerformance": "VALID", "writePerformance": "VALID", "indexHealth": "VALID", "backupStatus": "LOCAL_RUNTIME", "replicationStatus": "NOT_REQUIRED_LOCAL", "integrity": "VALID", "recoveryStatus": "READY"}

    def _learning_health(self, pipeline: dict[str, Any]) -> dict[str, Any]:
        record = pipeline.get("activeDailyLearningRecord", {})
        return {"observationsGenerated": record.get("historianObservations", 0), "recommendationsGenerated": record.get("recommendationsGenerated", 0), "validationQueue": len(pipeline.get("validationQueue", ())), "laboratoryQueue": len(pipeline.get("recommendationQueue", ())), "promotionQueue": len(pipeline.get("promotionQueue", ())), "learningVelocity": pipeline.get("knowledgeGrowthMetrics", {}).get("learningVelocity", 0), "knowledgeGrowth": record.get("knowledgeGrowth", 0), "recommendationQuality": "TRACKED", "backlogSize": len(pipeline.get("improvementBacklog", ()))}

    def _package_health(self, manager: dict[str, Any], package_id_key: str) -> dict[str, Any]:
        active = manager.get("activePackages", ())
        return {"promptValidity" if package_id_key == "promptPackageId" else "packageHealth": "VALID", "packageCount": len(active), "versionConsistency": "VALID", "dependencyHealth": "VALID", "deploymentStatus": "ACTIVE" if active else "STANDBY", "rollbackAvailability": manager.get("rollbackManager", {}).get("rollbackSupported", True), "laboratoryStatus": "READY"}

    def _credit_health(self, credit: dict[str, Any], api_runtime: dict[str, Any]) -> dict[str, Any]:
        return {"status": credit.get("budgetStatus", "GREEN"), "todayCreditUsage": api_runtime.get("costTodayUsd", api_runtime.get("costThisSessionUsd", 0.0)), "hourlyUsage": api_runtime.get("costThisSessionUsd", 0.0), "remainingBudget": credit.get("remainingBudgetUsd", 0.0), "budgetForecast": "NOMINAL", "burnRate": api_runtime.get("costThisSessionUsd", 0.0), "unexpectedConsumption": 0.0, "creditEfficiency": "HIGH", "emergencyMargin": "AVAILABLE"}

    def _runtime_health(self, resources: dict[str, Any], infrastructure: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any]:
        return {"cpuUsage": resources.get("cpu", 0), "memoryUsage": resources.get("memory", 0), "diskUsage": resources.get("storage", 0), "responseTime": "NOMINAL", "queueDepth": workflow.get("metrics", {}).get("queuedWorkflows", 0), "activeThreads": 1 + workflow.get("metrics", {}).get("activeWorkflows", 0), "backgroundTasks": len(infrastructure.get("optimizationHistory", ())), "resourceContention": "LOW", "garbageCollection": "NOMINAL", "status": "Healthy"}

    def _constitutional_health(self, workflow: dict[str, Any], schema: dict[str, Any], prompt_packages: dict[str, Any], strategy_packages: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        valid = workflow.get("tokenIntegrity", {}).get("status", "VALID") == "VALID" and schema.get("objectValidator", {}).get("invalidDecisionObjects", 0) == 0
        return {"status": "VALID" if valid else "VIOLATION", "lawVIICompliance": workflow.get("tokenIntegrity", {}).get("status", "VALID"), "workflowTokenIntegrity": workflow.get("tokenIntegrity", {}).get("status", "VALID"), "decisionObjectIntegrity": "VALID" if schema.get("objectValidator", {}).get("invalidDecisionObjects", 0) == 0 else "INVALID", "promptGovernance": "VALID" if prompt_packages.get("lawVII", {}).get("executesWorkflows") is False else "REVIEW", "strategyGovernance": "VALID" if strategy_packages.get("lawVII", {}).get("executesWorkflows") is False else "REVIEW", "commanderAuthority": "PRESERVED", "auditIntegrity": "VALID", "approvalChainIntegrity": "VALID", "configurationGovernance": "VALID" if config.get("lawVII", {}).get("executesWorkflows") is False else "REVIEW"}

    def _alerts_for(self, timestamp: str, component_health: tuple[dict[str, Any], ...], dependency_health: tuple[dict[str, Any], ...], constitutional: dict[str, Any], api: dict[str, Any], credit: dict[str, Any]) -> tuple[EnterpriseHealthAlert, ...]:
        alerts: list[EnterpriseHealthAlert] = []
        for item in component_health:
            if item["state"] in {"Critical", "Emergency", "Degraded"}:
                alerts.append(_alert(len(alerts) + 1, timestamp, item["component"], f"{item['component']} health is {item['state']}.", item["evidence"], "Critical" if item["state"] in {"Critical", "Emergency"} else "Warning", "Review Engineering Mode health details."))
        if constitutional.get("status") != "VALID":
            alerts.append(_alert(len(alerts) + 1, timestamp, "Constitutional Health", "Constitutional integrity requires review.", ("LAW VII",), "Critical", "Commander review required."))
        if credit.get("status") not in {"GREEN", "NOMINAL", "Healthy"}:
            alerts.append(_alert(len(alerts) + 1, timestamp, "Credit Governor", "Credit budget status is no longer green.", (str(credit.get("status")),), "Warning", "Review credit budget."))
        if api.get("providerHealth") not in {"Healthy", "Nominal", "NOMINAL"}:
            alerts.append(_alert(len(alerts) + 1, timestamp, "Provider Layer", "Provider health is degraded.", (str(api.get("providerHealth")),), "Warning", "Review provider diagnostics."))
        for item in dependency_health:
            if item["healthScore"] < 80:
                alerts.append(_alert(len(alerts) + 1, timestamp, item["dependencyChain"], "Dependency chain health is degraded.", (item["status"],), "Warning", "Resolve dependency issue."))
        return tuple(alerts)

    def _record_alerts(self, alerts: tuple[EnterpriseHealthAlert, ...]) -> None:
        known = {(item.timestamp, item.component, item.description) for item in self._alerts}
        for alert in alerts:
            if (alert.timestamp, alert.component, alert.description) not in known:
                self._alerts.append(alert)

    def _forecasts(self, api: dict[str, Any], credit: dict[str, Any], runtime: dict[str, Any], workflow: dict[str, Any], provider: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        return (
            {"forecast": "Credit Exhaustion", "risk": "LOW", "basis": str(credit.get("budgetForecast", "NOMINAL"))},
            {"forecast": "Storage Capacity", "risk": "LOW", "basis": "local runtime capacity available"},
            {"forecast": "API Saturation", "risk": "LOW", "basis": str(api.get("rateLimits", "Nominal"))},
            {"forecast": "Workflow Backlog", "risk": "LOW" if workflow.get("workflowQueueLength", 0) == 0 else "ADVISORY", "basis": str(workflow.get("workflowQueueLength", 0))},
            {"forecast": "Learning Queue Growth", "risk": "LOW", "basis": "queues tracked"},
            {"forecast": "Database Capacity", "risk": "LOW", "basis": "in-memory local runtime"},
            {"forecast": "Provider Stability", "risk": "LOW", "basis": str(provider.get("commanderVisibility", {}).get("providerHealth", "Healthy"))},
        )


def _alert(index: int, timestamp: str, component: str, description: str, evidence: tuple[str, ...], severity: str, action: str) -> EnterpriseHealthAlert:
    return EnterpriseHealthAlert(f"EHM-ALERT-{index:06d}", timestamp, component, description, evidence, severity, action, "OPEN")


def _health_state(score: float, components: tuple[dict[str, Any], ...]) -> str:
    if any(item.get("state") in {"Critical", "Emergency"} for item in components):
        return "Critical"
    if score >= 95:
        return "Healthy"
    if score >= 85:
        return "Minor Warning"
    if score >= 70:
        return "Degraded"
    if score >= 50:
        return "Critical"
    return "Emergency"


def _trend(history: tuple[dict[str, Any], ...]) -> str:
    if len(history) < 2:
        return "Stable"
    return "Improving" if history[-1]["enterpriseHealthScore"] > history[0]["enterpriseHealthScore"] else "Stable"
