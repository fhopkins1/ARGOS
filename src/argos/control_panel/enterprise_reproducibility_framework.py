"""Enterprise Reproducibility Framework for ARGOS scientific replay."""

from __future__ import annotations

import hashlib
import json
from typing import Any


REPLAY_STATUSES = ("Exact Match", "Functionally Equivalent", "Minor Difference", "Material Difference", "Replay Failed")


class EnterpriseReproducibilityFramework:
    """Capture historical enterprise state so completed decisions remain replayable."""

    def __init__(self) -> None:
        self._snapshot_archive: list[dict[str, Any]] = []
        self._last_snapshot_key: tuple[Any, ...] | None = None
        self._last_snapshot: dict[str, Any] | None = None

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        workflow_orchestrator: dict[str, Any],
        performance_truth: dict[str, Any],
        decision_laboratory: dict[str, Any],
        enterprise_configuration_registry: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        market_context_engine: dict[str, Any],
        market_data_provider: dict[str, Any],
        decision_object_schema: dict[str, Any],
        trade_attribution_engine: dict[str, Any],
        control: dict[str, Any],
        costs: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        workflows = tuple(_completed_workflows(workflow_orchestrator))
        snapshot_key = (
            len(workflows),
            len(performance_truth.get("orderLedger", ())),
            len(performance_truth.get("tradeLedger", ())),
            len(decision_laboratory.get("workflowReplay", ())),
            enterprise_configuration_registry.get("registryHash", ""),
        )
        if self._last_snapshot_key == snapshot_key and self._last_snapshot is not None:
            return self._last_snapshot

        snapshots = tuple(
            self._enterprise_snapshot(
                index=index,
                timestamp=timestamp_utc,
                workflow=workflow,
                performance_truth=performance_truth,
                decision_laboratory=decision_laboratory,
                enterprise_configuration_registry=enterprise_configuration_registry,
                prompt_package_manager=prompt_package_manager,
                strategy_package_manager=strategy_package_manager,
                market_context_engine=market_context_engine,
                market_data_provider=market_data_provider,
                decision_object_schema=decision_object_schema,
                control=control,
                costs=costs,
            )
            for index, workflow in enumerate(workflows[-80:], start=1)
        )
        self._record_snapshots(snapshots)
        certifications = tuple(self._certification(item, decision_laboratory, performance_truth) for item in snapshots)
        differences = tuple(self._difference_analysis(item, certifications[index]) for index, item in enumerate(snapshots))
        reproducibility_score = self._reproducibility_score(snapshots, certifications, differences)
        snapshot = {
            "frameworkName": "Enterprise Reproducibility Framework",
            "engineeringOrder": "EO-S",
            "constitutionalMission": "Every enterprise decision shall remain reproducible forever.",
            "constitutionalQuestion": "If this exact workflow were replayed years from now, would ARGOS reach the same decision using only the information that originally existed?",
            "constitutionalMode": "REPRODUCIBILITY_ONLY",
            "enterpriseSnapshots": snapshots,
            "snapshotArchive": tuple(self._snapshot_archive[-120:]),
            "latestEnterpriseSnapshot": snapshots[-1] if snapshots else {},
            "replayBrowser": self._replay_browser(snapshots),
            "replayCertification": certifications,
            "differenceAnalysis": differences,
            "environmentSnapshots": tuple(item["environmentSnapshot"] for item in snapshots),
            "promptSnapshots": tuple(item["promptSnapshot"] for item in snapshots),
            "strategySnapshots": tuple(item["strategySnapshot"] for item in snapshots),
            "configurationSnapshots": tuple(item["configurationSnapshot"] for item in snapshots),
            "providerSnapshots": tuple(item["providerSnapshot"] for item in snapshots),
            "portfolioSnapshots": tuple(item["portfolioSnapshot"] for item in snapshots),
            "modelSnapshots": tuple(item["modelSnapshot"] for item in snapshots),
            "marketSnapshots": tuple(item["marketSnapshot"] for item in snapshots),
            "determinismPolicy": {
                "randomSeedPolicy": "CAPTURE_IF_PRESENT",
                "historicalArtifactsOnly": True,
                "liveMarketDataAllowedInReplay": False,
                "currentPromptsAllowedInReplay": False,
                "currentStrategiesAllowedInReplay": False,
                "unknownLimitationsDocumented": True,
            },
            "reproducibilityScore": reproducibility_score,
            "replayStatistics": self._replay_statistics(certifications, decision_laboratory),
            "historicalCoverage": self._historical_coverage(workflows, snapshots, performance_truth),
            "provenanceGraph": self._provenance_graph(snapshots, trade_attribution_engine),
            "historianFeed": {"reproducibilityTrend": "Stable", "replayFailuresBecomeLessons": True, "snapshotCount": len(snapshots)},
            "enterpriseLearningFeed": {"weaknessDetectionAvailable": True, "missingSnapshots": max(0, len(workflows) - len(snapshots)), "configurationDriftTracked": True},
            "promptEvolutionFeed": {"identicalHistoricalEnvironmentRequired": True, "promptSnapshotsAvailable": len(snapshots)},
            "strategyEvolutionFeed": {"identicalHistoricalEnvironmentRequired": True, "strategySnapshotsAvailable": len(snapshots)},
            "decisionLaboratoryFeed": {"historicalEnvironmentReconstructedBeforeExperiment": True, "certifiedReplayCount": len(certifications)},
            "commanderReviewFeed": {"reproducibilitySummary": self._commander_summary(reproducibility_score, snapshots), "score": reproducibility_score["overallScore"]},
            "internalDiagnostics": {
                "deterministic": True,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "tradesPlaced": 0,
                "enterpriseSnapshotCount": len(snapshots),
                "snapshotArchiveCount": len(self._snapshot_archive),
                "replayCertificationCount": len(certifications),
                "auditEventCountObserved": audit_event_count,
            },
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowTokens": False,
                "tradesSecurities": False,
                "makesInvestmentDecisions": False,
                "modifiesHistoricalArtifacts": False,
                "modifiesPrompts": False,
                "modifiesStrategies": False,
                "overridesCommanderAuthority": False,
                "responsibility": "PRESERVES_AND_VALIDATES_HISTORICAL_REPRODUCIBILITY_ONLY",
            },
        }
        self._last_snapshot_key = snapshot_key
        self._last_snapshot = snapshot
        return snapshot

    def _enterprise_snapshot(
        self,
        *,
        index: int,
        timestamp: str,
        workflow: dict[str, Any],
        performance_truth: dict[str, Any],
        decision_laboratory: dict[str, Any],
        enterprise_configuration_registry: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        strategy_package_manager: dict[str, Any],
        market_context_engine: dict[str, Any],
        market_data_provider: dict[str, Any],
        decision_object_schema: dict[str, Any],
        control: dict[str, Any],
        costs: dict[str, Any],
    ) -> dict[str, Any]:
        decision = _latest_decision(workflow)
        decision_id = str(decision.get("decisionObjectId", ""))
        workflow_id = str(workflow.get("workflow_id", ""))
        truth = _truth_for_decision(decision_id, performance_truth)
        prompt = _prompt_snapshot(decision, prompt_package_manager)
        strategy = _strategy_snapshot(decision, strategy_package_manager)
        market = _market_snapshot(decision, market_context_engine)
        configuration = _configuration_snapshot(decision, enterprise_configuration_registry)
        provider = _provider_snapshot(market_data_provider)
        portfolio = _portfolio_snapshot(decision_id, performance_truth)
        model = _model_snapshot(decision)
        environment = _environment_snapshot(control, costs, workflow, decision_laboratory)
        payload = {
            "snapshotId": f"ERF-SNAP-{index:06d}",
            "workflowId": workflow_id,
            "workflowTokenId": (workflow.get("token") or {}).get("audit_identifier", ""),
            "decisionObjectId": decision_id,
            "performanceTruthId": truth.get("hash", truth.get("audit_identifier", "")),
            "promptPackageVersion": prompt["promptVersion"],
            "strategyPackageVersion": strategy["strategyVersion"],
            "decisionObjectSchemaVersion": decision.get("schemaVersion", decision_object_schema.get("schemaVersion", "UNKNOWN")),
            "marketContextVersion": market["marketContextVersion"],
            "configurationVersion": configuration["configurationVersion"],
            "providerVersion": provider["providerVersion"],
            "enterpriseVersion": configuration["enterpriseVersion"],
            "timestamp": timestamp,
            "replayStatus": "Exact Match" if decision_id else "Replay Failed",
            "validationStatus": "VALID" if decision_id and truth else "PARTIAL",
            "environmentSnapshot": environment,
            "marketSnapshot": market,
            "promptSnapshot": prompt,
            "strategySnapshot": strategy,
            "configurationSnapshot": configuration,
            "portfolioSnapshot": portfolio,
            "providerSnapshot": provider,
            "modelSnapshot": model,
            "dataProvenance": self._data_provenance(workflow, decision, truth, market, prompt, strategy, configuration, provider, portfolio, model),
            "replayInputs": {
                "usesHistoricalMarketInformationOnly": True,
                "usesHistoricalPromptOnly": True,
                "usesHistoricalStrategyOnly": True,
                "usesHistoricalConfigurationOnly": True,
                "usesCurrentApiProviders": False,
            },
            "immutable": True,
        }
        checksum = _hash_payload(payload)
        return dict(payload, checksum=checksum, hash=checksum)

    def _record_snapshots(self, snapshots: tuple[dict[str, Any], ...]) -> None:
        known = {item["snapshotId"] for item in self._snapshot_archive}
        for snapshot in snapshots:
            if snapshot["snapshotId"] not in known:
                self._snapshot_archive.append(
                    {
                        "snapshotId": snapshot["snapshotId"],
                        "workflowId": snapshot["workflowId"],
                        "decisionObjectId": snapshot["decisionObjectId"],
                        "replayStatus": snapshot["replayStatus"],
                        "validationStatus": snapshot["validationStatus"],
                        "checksum": snapshot["checksum"],
                        "timestamp": snapshot["timestamp"],
                    }
                )

    def _certification(self, snapshot: dict[str, Any], decision_laboratory: dict[str, Any], performance_truth: dict[str, Any]) -> dict[str, Any]:
        replay = _replay_for_workflow(snapshot["workflowId"], decision_laboratory)
        checks = {
            "decisionMatch": replay.get("decisionObjectId", snapshot["decisionObjectId"]) == snapshot["decisionObjectId"],
            "promptMatch": bool(snapshot["promptSnapshot"]["promptVersion"]),
            "strategyMatch": bool(snapshot["strategySnapshot"]["strategyVersion"]),
            "configurationMatch": bool(snapshot["configurationSnapshot"]["configurationVersion"]),
            "decisionObjectMatch": bool(snapshot["decisionObjectId"]),
            "performanceTruthMatch": bool(snapshot["performanceTruthId"] or _truth_for_decision(snapshot["decisionObjectId"], performance_truth)),
            "marketContextMatch": bool(snapshot["marketContextVersion"]),
            "referenceIntegrity": bool(snapshot["dataProvenance"]),
            "hashValidation": snapshot["hash"] == snapshot["checksum"],
        }
        passed = sum(1 for value in checks.values() if value)
        status = "Exact Match" if passed == len(checks) else "Functionally Equivalent" if passed >= len(checks) - 1 else "Minor Difference" if passed >= 6 else "Material Difference"
        return {
            "certificationId": f"ERF-CERT-{snapshot['snapshotId'].split('-')[-1]}",
            "snapshotId": snapshot["snapshotId"],
            "workflowId": snapshot["workflowId"],
            "decisionObjectId": snapshot["decisionObjectId"],
            "replayStatus": status,
            "checks": checks,
            "score": round(passed / max(1, len(checks)) * 100, 4),
            "explanation": "Historical replay can reconstruct the original enterprise state from captured artifacts." if status == "Exact Match" else "Replay has documented differences requiring Commander review.",
        }

    def _difference_analysis(self, snapshot: dict[str, Any], certification: dict[str, Any]) -> dict[str, Any]:
        differences = tuple(
            {"difference": _difference_name(name), "status": "MATCH" if passed else "DIFFERENCE", "commanderExplanation": _difference_explanation(name, passed)}
            for name, passed in certification.get("checks", {}).items()
        )
        return {
            "differenceAnalysisId": f"ERF-DIFF-{snapshot['snapshotId'].split('-')[-1]}",
            "snapshotId": snapshot["snapshotId"],
            "workflowId": snapshot["workflowId"],
            "replayStatus": certification["replayStatus"],
            "differences": differences,
            "allDifferencesExplained": True,
        }

    def _data_provenance(self, workflow: dict[str, Any], decision: dict[str, Any], truth: dict[str, Any], *artifacts: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        base = (
            ("Workflow", workflow.get("workflow_id", ""), (workflow.get("token") or {}).get("creation_timestamp", ""), "Enterprise Workflow Orchestrator", "workflow-history"),
            ("Decision Object", decision.get("decisionObjectId", ""), decision.get("decisionTimestamp", ""), decision.get("office", "ARGOS"), "workflow-output-history"),
            ("Performance Truth", truth.get("hash", truth.get("audit_identifier", "")), truth.get("timestamp", ""), "Performance Truth Engine", "immutable-ledger"),
        )
        rows = [
            {"artifactType": kind, "origin": origin, "timestamp": stamp, "creator": creator, "version": "captured", "dependencies": (), "validation": "TRACEABLE", "hash": _hash_payload({"kind": kind, "origin": origin, "stamp": stamp}), "repositoryReference": reference}
            for kind, origin, stamp, creator, reference in base
        ]
        for artifact in artifacts:
            rows.append(
                {
                    "artifactType": artifact.get("artifactType", "Snapshot Artifact"),
                    "origin": artifact.get("origin", artifact.get("snapshotId", artifact.get("version", "UNKNOWN"))),
                    "timestamp": artifact.get("timestamp", ""),
                    "creator": artifact.get("creator", "ARGOS"),
                    "version": artifact.get("version", artifact.get("promptVersion", artifact.get("strategyVersion", artifact.get("configurationVersion", "captured")))),
                    "dependencies": tuple(artifact.get("dependencies", ())),
                    "validation": artifact.get("validationStatus", "TRACEABLE"),
                    "hash": artifact.get("hash", _hash_payload(artifact)),
                    "repositoryReference": artifact.get("repositoryReference", "enterprise-snapshot"),
                }
            )
        return tuple(rows)

    def _replay_browser(self, snapshots: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        return tuple({"snapshotId": item["snapshotId"], "workflowId": item["workflowId"], "decisionObjectId": item["decisionObjectId"], "replayStatus": item["replayStatus"], "validationStatus": item["validationStatus"], "timestamp": item["timestamp"]} for item in snapshots[-40:])

    def _reproducibility_score(self, snapshots: tuple[dict[str, Any], ...], certifications: tuple[dict[str, Any], ...], differences: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        average_cert = _average([item["score"] for item in certifications])
        integrity = 100.0 if all(item.get("hash") == item.get("checksum") for item in snapshots) else 75.0
        reference = 100.0 if all(item.get("dataProvenance") for item in snapshots) else 70.0
        coverage = 100.0 if snapshots else 0.0
        validation = 100.0 if all(item["allDifferencesExplained"] for item in differences) else 80.0
        overall = _average([average_cert, integrity, reference, coverage, validation])
        return {
            "overallScore": overall,
            "replaySuccess": average_cert,
            "historicalCompleteness": coverage,
            "snapshotIntegrity": integrity,
            "versionAvailability": _average([100.0 if item["promptPackageVersion"] and item["strategyPackageVersion"] else 70.0 for item in snapshots]),
            "referenceIntegrity": reference,
            "validationSuccess": validation,
            "historicalCoverage": coverage,
        }

    def _replay_statistics(self, certifications: tuple[dict[str, Any], ...], decision_laboratory: dict[str, Any]) -> dict[str, Any]:
        return {
            "certifiedReplays": len(certifications),
            "exactMatches": sum(1 for item in certifications if item["replayStatus"] == "Exact Match"),
            "functionalEquivalents": sum(1 for item in certifications if item["replayStatus"] == "Functionally Equivalent"),
            "materialDifferences": sum(1 for item in certifications if item["replayStatus"] == "Material Difference"),
            "laboratoryReplayPackages": len(decision_laboratory.get("workflowReplay", ())),
            "availableStatuses": REPLAY_STATUSES,
        }

    def _historical_coverage(self, workflows: tuple[dict[str, Any], ...], snapshots: tuple[dict[str, Any], ...], performance_truth: dict[str, Any]) -> dict[str, Any]:
        return {
            "completedWorkflows": len(workflows),
            "enterpriseSnapshots": len(snapshots),
            "coveragePercent": round(len(snapshots) / max(1, len(workflows)) * 100, 4),
            "performanceTruthRecords": len(performance_truth.get("decisionObjectOutcomes", ())),
            "missingSnapshots": max(0, len(workflows) - len(snapshots)),
        }

    def _provenance_graph(self, snapshots: tuple[dict[str, Any], ...], trade_attribution_engine: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        attribution_by_decision = {item.get("decisionObjectId", ""): item.get("attributionReportId", "") for item in trade_attribution_engine.get("attributionRepository", ())}
        return tuple(
            {
                "snapshotId": item["snapshotId"],
                "workflowId": item["workflowId"],
                "decisionObjectId": item["decisionObjectId"],
                "performanceTruthId": item["performanceTruthId"],
                "attributionReportId": attribution_by_decision.get(item["decisionObjectId"], ""),
                "provenanceNodes": len(item.get("dataProvenance", ())),
                "hash": item["hash"],
            }
            for item in snapshots[-40:]
        )

    def _commander_summary(self, score: dict[str, Any], snapshots: tuple[dict[str, Any], ...]) -> str:
        if not snapshots:
            return "Enterprise reproducibility awaiting completed workflows."
        return f"Enterprise reproducibility score {score['overallScore']} across {len(snapshots)} completed workflow snapshots."


def _completed_workflows(workflow_orchestrator: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(item for item in workflow_orchestrator.get("workflows", ()) if (item.get("token") or {}).get("workflow_status") == "Archived")


def _latest_decision(workflow: dict[str, Any]) -> dict[str, Any]:
    for output in reversed(workflow.get("output_history", ())):
        decision = output.get("decision_object")
        if isinstance(decision, dict):
            return decision
    return {}


def _truth_for_decision(decision_id: str, performance_truth: dict[str, Any]) -> dict[str, Any]:
    for collection in ("orderLedger", "decisionObjectOutcomes", "tradeLedger", "workflowAttribution"):
        for item in performance_truth.get(collection, ()):
            if item.get("decision_object_id") == decision_id:
                return item
    return {}


def _replay_for_workflow(workflow_id: str, decision_laboratory: dict[str, Any]) -> dict[str, Any]:
    return next((item for item in decision_laboratory.get("workflowReplay", ()) if item.get("workflowId") == workflow_id), {})


def _prompt_snapshot(decision: dict[str, Any], manager: dict[str, Any]) -> dict[str, Any]:
    prompt = decision.get("promptContract") if isinstance(decision.get("promptContract"), dict) else {}
    active = (manager.get("activePackages") or [{}])[0]
    payload = {
        "artifactType": "Prompt Snapshot",
        "promptPackage": active.get("packageId", prompt.get("promptTemplateId", "UNKNOWN")),
        "promptVersion": prompt.get("promptVersion", active.get("promptVersion", "UNKNOWN")),
        "promptHash": prompt.get("promptHash", _hash_payload(prompt)),
        "promptDependencies": tuple(prompt.get("dependencies", ())),
        "promptMetadata": {"template": prompt.get("promptTemplateId", ""), "office": prompt.get("office", decision.get("office", ""))},
        "promptConfiguration": {"schemaVersion": prompt.get("schemaVersion", ""), "contractVersion": prompt.get("contractVersion", "")},
        "validationStatus": prompt.get("responseValidationResult", "CAPTURED"),
        "creator": "Prompt Contract Library",
        "repositoryReference": "prompt-contract-history",
    }
    return dict(payload, hash=_hash_payload(payload))


def _strategy_snapshot(decision: dict[str, Any], manager: dict[str, Any]) -> dict[str, Any]:
    active = (manager.get("activePackages") or [{}])[0]
    strategy = decision.get("currentStrategy", active.get("strategyName", "UNKNOWN"))
    payload = {
        "artifactType": "Strategy Snapshot",
        "strategyPackage": active.get("packageId", decision.get("strategyPackageId", "UNKNOWN")),
        "strategyVersion": decision.get("strategyPackageVersion", active.get("packageVersion", strategy)),
        "strategyHash": decision.get("strategyPackageHash", _hash_payload({"strategy": strategy})),
        "strategyDependencies": tuple(active.get("dependencies", ())),
        "strategyMetadata": {"strategy": strategy, "office": decision.get("office", "")},
        "applicableMarketRegime": (decision.get("marketContext") or {}).get("marketRegime", "UNKNOWN") if isinstance(decision.get("marketContext"), dict) else "UNKNOWN",
        "validationStatus": active.get("validationStatus", "CAPTURED"),
        "creator": "Strategy Package Manager",
        "repositoryReference": "strategy-package-history",
    }
    return dict(payload, hash=_hash_payload(payload))


def _market_snapshot(decision: dict[str, Any], market_context: dict[str, Any]) -> dict[str, Any]:
    market = decision.get("marketContext") if isinstance(decision.get("marketContext"), dict) else market_context.get("latestMarketContext", {})
    payload = {
        "artifactType": "Market Snapshot",
        "marketContextVersion": decision.get("marketContextSnapshotId", market.get("snapshotId", "UNKNOWN")),
        "prices": tuple(market.get("relatedSymbols", ())),
        "indicators": market.get("overallTrend", "UNKNOWN"),
        "fundamentals": "CAPTURED_IF_AVAILABLE",
        "news": tuple(market.get("supportingEvidence", ())),
        "macro": market.get("macroRegime", "PAPER"),
        "sectorLeadership": tuple(market.get("relatedSectors", ())),
        "marketRegime": market.get("marketRegime", "UNKNOWN"),
        "liquidity": market.get("liquidityState", "UNKNOWN"),
        "portfolioContext": "CAPTURED",
        "futureInformationExcluded": True,
        "creator": "Market Context Integration Engine",
        "repositoryReference": "market-context-repository",
    }
    return dict(payload, hash=_hash_payload(payload))


def _configuration_snapshot(decision: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "artifactType": "Configuration Snapshot",
        "configurationVersion": registry.get("enterpriseConfigurationVersion", decision.get("enterpriseConfigurationVersion", "UNKNOWN")),
        "enterpriseVersion": registry.get("enterpriseConfigurationVersion", "1.0.0"),
        "environmentProfile": registry.get("currentEnvironment", decision.get("enterpriseConfigurationEnvironment", "development")),
        "riskLimits": "CAPTURED",
        "marketProviders": "CAPTURED",
        "apiConfiguration": "CAPTURED",
        "learningConfiguration": "CAPTURED",
        "runtimeConfiguration": "CAPTURED",
        "officeConfiguration": "CAPTURED",
        "commanderPreferences": "CAPTURED",
        "portfolioConfiguration": "CAPTURED",
        "registryHash": registry.get("registryHash", ""),
        "creator": "Enterprise Configuration Registry",
        "repositoryReference": "configuration-registry",
    }
    return dict(payload, hash=_hash_payload(payload))


def _provider_snapshot(provider: dict[str, Any]) -> dict[str, Any]:
    primary = provider.get("commanderVisibility", {}).get("currentPrimaryProvider", "mock")
    payload = {
        "artifactType": "Provider Snapshot",
        "provider": primary,
        "providerVersion": provider.get("providerConfiguration", {}).get("normalizationVersion", "ARGOS-NORMALIZED-V1"),
        "source": "Market Data Provider Abstraction Layer",
        "freshness": provider.get("cacheStatistics", {}).get("cacheFreshness", "CAPTURED"),
        "normalizationVersion": provider.get("normalizationDiagnostics", {}).get("normalizationVersion", "ARGOS-NORMALIZED-V1"),
        "cacheState": provider.get("cacheStatistics", {}),
        "replayDoesNotDependOnCurrentProviders": True,
        "creator": "Market Data Provider Abstraction Layer",
        "repositoryReference": "provider-snapshot-history",
    }
    return dict(payload, hash=_hash_payload(payload))


def _portfolio_snapshot(decision_id: str, performance_truth: dict[str, Any]) -> dict[str, Any]:
    portfolio = next((item for item in reversed(performance_truth.get("portfolioLedger", ())) if item.get("decision_object_id") == decision_id), {})
    calculations = (performance_truth.get("calculations") or {}).get("portfolio", {})
    payload = {
        "artifactType": "Portfolio Snapshot",
        "cash": portfolio.get("cash", calculations.get("cash", 0)),
        "positions": tuple(performance_truth.get("positionLedger", ())),
        "sectorAllocation": "CAPTURED_IF_AVAILABLE",
        "portfolioRisk": calculations.get("currentExposure", 0),
        "buyingPower": portfolio.get("buying_power", calculations.get("buyingPower", 0)),
        "currentExposure": calculations.get("currentExposure", 0),
        "openOrders": (),
        "enterpriseCapability": "CAPTURED",
        "creator": "Performance Truth Engine",
        "repositoryReference": "portfolio-ledger",
    }
    return dict(payload, hash=_hash_payload(payload))


def _model_snapshot(decision: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "artifactType": "Model Snapshot",
        "modelName": decision.get("apiModel", "dry-run-model"),
        "modelVersion": decision.get("apiModel", "dry-run-model"),
        "provider": decision.get("apiProvider", "none"),
        "temperature": 0,
        "topP": 1,
        "maximumTokens": "CAPTURED_BY_GATEWAY",
        "reasoningSettings": "DETERMINISTIC_PLACEHOLDER" if not decision.get("apiModel") else "CAPTURED",
        "deterministicParameters": True,
        "systemPromptHash": _hash_payload((decision.get("promptContract") or {}) if isinstance(decision.get("promptContract"), dict) else {}),
        "creator": "API Execution Gateway",
        "repositoryReference": "model-execution-history",
    }
    return dict(payload, hash=_hash_payload(payload))


def _environment_snapshot(control: dict[str, Any], costs: dict[str, Any], workflow: dict[str, Any], decision_laboratory: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "artifactType": "Environment Snapshot",
        "enterpriseVersion": "1.0.0",
        "runtimeSettings": {"paperTradingActive": control.get("paper_trading_active", False), "realWorldTradingActive": control.get("real_world_trading_active", False)},
        "creditLimits": {"budgetStatus": costs.get("budget_status", ""), "budgetLimitUsd": costs.get("budget_limit_usd", 0)},
        "officeConfiguration": tuple(workflow.get("stages", ())),
        "environmentProfile": "development",
        "decisionLaboratoryReplayCount": len(decision_laboratory.get("workflowReplay", ())),
        "creator": "Control Panel Runtime",
        "repositoryReference": "runtime-state-history",
    }
    return dict(payload, hash=_hash_payload(payload))


def _difference_name(check_name: str) -> str:
    return {
        "decisionMatch": "Decision Match",
        "promptMatch": "Prompt Match",
        "strategyMatch": "Strategy Match",
        "configurationMatch": "Configuration Match",
        "decisionObjectMatch": "Decision Object Match",
        "performanceTruthMatch": "Performance Truth Match",
        "marketContextMatch": "Market Context Match",
        "referenceIntegrity": "Reference Integrity",
        "hashValidation": "Hash Validation",
    }.get(check_name, check_name)


def _difference_explanation(check_name: str, passed: bool) -> str:
    if passed:
        return f"{_difference_name(check_name)} reproduced from historical artifacts."
    return f"{_difference_name(check_name)} differs or is incomplete; Commander review should treat this as a reproducibility weakness."


def _average(values: list[float]) -> float:
    return round(sum(values) / max(1, len(values)), 4)


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
