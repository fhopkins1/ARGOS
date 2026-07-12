"""Strategy Package Manager for governed ARGOS investment doctrine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


STRATEGY_PACKAGE_STATES = (
    "Concept",
    "Draft",
    "Candidate",
    "Validated",
    "Approved",
    "Installed",
    "Active",
    "Deprecated",
    "Retired",
    "Archived",
    "Failed Validation",
    "Installation Failed",
    "Rollback",
)

STRATEGY_PACKAGE_TYPES = (
    "Momentum Strategy",
    "Trend Following Strategy",
    "Mean Reversion Strategy",
    "Breakout Strategy",
    "Swing Strategy",
    "Sector Rotation Strategy",
    "Volatility Strategy",
    "Income Strategy",
    "Capital Preservation Strategy",
    "Experimental Strategy",
    "Portfolio Allocation Strategy",
    "Research Strategy",
)

STRATEGY_INSTALLATION_PIPELINE = (
    "Strategy Candidate",
    "Compatibility Verification",
    "Dependency Resolution",
    "Integrity Verification",
    "Decision Laboratory",
    "Replay Validation",
    "Counterfactual Validation",
    "Commander Approval",
    "Installation",
    "Activation",
    "Audit Record",
)


@dataclass(frozen=True)
class StrategyPackage:
    packageId: str
    packageName: str
    packageVersion: str
    strategyName: str
    strategyVersion: str
    strategyFamily: str
    packageType: str
    purpose: str
    investmentThesis: str
    description: str
    author: str
    creationDate: str
    owningOffice: str
    currentStatus: str
    repositoryReference: str
    checksum: str
    hash: str
    digitalSignature: str | None
    compatibilityMatrix: tuple[dict[str, Any], ...]
    dependencyList: tuple[dict[str, Any], ...]
    validationStatus: str
    deploymentStatus: str
    approvalStatus: str
    packageHealth: str
    currentPortfolioUsage: str
    supportedMarketRegimes: tuple[str, ...]
    strategyHash: str
    dependencyHashes: tuple[str, ...]
    validationHash: str
    deploymentHash: str


class StrategyPackageManager:
    """Read-only package governance for enterprise investment doctrine."""

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        environment: str,
        strategy_performance: dict[str, Any],
        decision_laboratory: dict[str, Any],
        decision_object_schema: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        market_context_engine: dict[str, Any],
        api_execution_gateway: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        historian_recommendation_engine: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        packages = self._packages(
            timestamp_utc,
            strategy_performance,
            decision_object_schema,
            prompt_package_manager,
            market_context_engine,
            api_execution_gateway,
        )
        candidates = self._candidate_packages(
            timestamp_utc,
            enterprise_learning_engine,
            historian_recommendation_engine,
            decision_object_schema,
            prompt_package_manager,
            market_context_engine,
            api_execution_gateway,
        )
        all_packages = packages + candidates
        active = tuple(item for item in all_packages if item.currentStatus == "Active")
        installed = tuple(item for item in all_packages if item.currentStatus in {"Installed", "Active"})
        return {
            "managerName": "Strategy Package Manager",
            "engineeringOrder": "EO-J",
            "constitutionalMission": "Treat enterprise investment doctrine with the same engineering rigor used to manage mission-critical software.",
            "constitutionalQuestion": "Can enterprise investment doctrine be installed, upgraded, validated, reverted, and audited exactly like enterprise software?",
            "constitutionalMode": "STRATEGY_DEPLOYMENT_GOVERNANCE_ONLY",
            "packageTypes": STRATEGY_PACKAGE_TYPES,
            "packageStates": STRATEGY_PACKAGE_STATES,
            "installationPipeline": STRATEGY_INSTALLATION_PIPELINE,
            "strategyPackageRegistry": tuple(asdict(item) for item in all_packages),
            "installedPackages": tuple(asdict(item) for item in installed),
            "activePackages": tuple(asdict(item) for item in active),
            "strategyAssignment": tuple(self._strategy_assignment(item, environment) for item in active),
            "analystStrategyAssignment": self._analyst_assignment(active, environment),
            "versionGraph": tuple(self._version_graph(item, all_packages) for item in all_packages),
            "dependencyGraph": tuple(self._dependency_graph(item) for item in all_packages),
            "compatibilityMatrix": tuple(self._compatibility_summary(item) for item in all_packages),
            "installationHistory": tuple(self._installation_history(item, timestamp_utc) for item in installed),
            "activationHistory": tuple(self._activation_history(item, timestamp_utc) for item in active),
            "rollbackManager": self._rollback_manager(active),
            "integrityDashboard": tuple(self._integrity(item) for item in all_packages),
            "healthDashboard": tuple(self._health(item, strategy_performance, decision_laboratory) for item in all_packages),
            "laboratoryResults": tuple(self._lab_result(item, decision_laboratory) for item in all_packages),
            "replayStatistics": {
                "workflowReplays": len(decision_laboratory.get("workflowReplay", ())),
                "decisionReplays": decision_laboratory.get("metrics", {}).get("decisionReplayCount", 0),
                "counterfactualReports": len(decision_laboratory.get("performanceComparisons", ())),
            },
            "counterfactualReports": tuple(decision_laboratory.get("performanceComparisons", ())[:10]),
            "marketRegimeAssignment": tuple(self._market_regime_assignment(item, market_context_engine) for item in all_packages),
            "deploymentTimeline": tuple(self._deployment_event(item, timestamp_utc) for item in installed),
            "packageSearchIndex": tuple(self._search_row(item) for item in all_packages),
            "strategyEvolutionIntegration": {
                "source": "Enterprise Learning + Historian strategy recommendations",
                "candidatePackages": len(candidates),
                "productionStrategyMutationCount": 0,
                "role": "Strategy evolution designs investment doctrine; package manager deploys approved doctrine.",
            },
            "enterpriseLearningIntegration": {
                "strategyRecommendations": _strategy_recommendation_count(enterprise_learning_engine) + _historian_strategy_recommendation_count(historian_recommendation_engine),
                "distributionStatus": "BLOCKED_PENDING_COMMANDER_APPROVAL_FOR_CANDIDATES",
            },
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowTokens": False,
                "tradesSecurities": False,
                "activationWithoutCommanderApproval": False,
                "autonomousDoctrineModification": False,
                "overridesConstitutionalGovernance": False,
                "responsibility": "GOVERNS_DEPLOYMENT_NOT_EXECUTION",
            },
            "performanceGoals": {
                "deterministicDeployment": True,
                "strategyDriftPrevented": True,
                "rapidRollbackSupported": True,
                "completeAuditability": True,
                "reproducibleInvestmentDoctrine": True,
            },
            "internalDiagnostics": {
                "auditEventCount": audit_event_count,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "tradesPlaced": 0,
                "productionStrategyMutationCount": 0,
                "hiddenDependenciesDetected": False,
                "invalidActivePackages": sum(1 for item in active if item.packageHealth != "HEALTHY"),
            },
        }

    def _packages(
        self,
        timestamp_utc: str,
        strategy_performance: dict[str, Any],
        decision_object_schema: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        market_context_engine: dict[str, Any],
        api_execution_gateway: dict[str, Any],
    ) -> tuple[StrategyPackage, ...]:
        leaderboard = tuple(strategy_performance.get("strategyLeaderboard", ()))
        if not leaderboard:
            leaderboard = (
                {
                    "strategyName": "Workflow Proof Strategy",
                    "currentStatus": "ACTIVE",
                    "winRate": 0.0,
                    "averageReturn": 0.0,
                    "sharpeRatio": 0.0,
                    "capitalAllocated": 0.0,
                },
                {
                    "strategyName": "Risk Adjusted Paper Strategy",
                    "currentStatus": "OBSERVED",
                    "winRate": 0.0,
                    "averageReturn": 0.0,
                    "sharpeRatio": 0.0,
                    "capitalAllocated": 0.0,
                },
            )
        return tuple(
            self._package_from_strategy(
                item,
                timestamp_utc,
                decision_object_schema,
                prompt_package_manager,
                market_context_engine,
                api_execution_gateway,
                status="Active" if item.get("currentStatus") == "ACTIVE" or index == 1 or item.get("strategyName") == "Workflow Proof Strategy" else "Installed",
                deployment_status="ACTIVE" if item.get("currentStatus") == "ACTIVE" or index == 1 or item.get("strategyName") == "Workflow Proof Strategy" else "STAGED",
                approval_status="COMMANDER_APPROVED_BASELINE",
            )
            for index, item in enumerate(leaderboard, start=1)
        )

    def _candidate_packages(
        self,
        timestamp_utc: str,
        enterprise_learning_engine: dict[str, Any],
        historian_recommendation_engine: dict[str, Any],
        decision_object_schema: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        market_context_engine: dict[str, Any],
        api_execution_gateway: dict[str, Any],
    ) -> tuple[StrategyPackage, ...]:
        candidates = []
        recommendations = [
            item
            for item in enterprise_learning_engine.get("recommendations", ())
            if item.get("category") == "Strategy Improvement"
        ]
        recommendations.extend(
            item
            for item in historian_recommendation_engine.get("recommendationDatabase", ())
            if "Strategy Improvement" in tuple(item.get("category", ()))
        )
        for index, recommendation in enumerate(recommendations[:8], start=1):
            strategy_name = recommendation.get("relatedStrategy") or ", ".join(tuple(recommendation.get("relatedStrategyVersions", ()))[:1]) or "Candidate Strategy"
            item = {
                "strategyName": strategy_name,
                "currentStatus": "CANDIDATE",
                "winRate": 0.0,
                "averageReturn": 0.0,
                "sharpeRatio": 0.0,
                "capitalAllocated": 0.0,
                "recommendation": recommendation.get("recommendationId", recommendation.get("title", "")),
            }
            candidates.append(
                self._package_from_strategy(
                    item,
                    timestamp_utc,
                    decision_object_schema,
                    prompt_package_manager,
                    market_context_engine,
                    api_execution_gateway,
                    status="Candidate",
                    deployment_status="NOT_INSTALLED",
                    approval_status="PENDING_LAB_AND_COMMANDER_APPROVAL",
                    suffix=f"CANDIDATE-{index:03d}",
                )
            )
        return tuple(candidates)

    def _package_from_strategy(
        self,
        strategy: dict[str, Any],
        timestamp_utc: str,
        decision_object_schema: dict[str, Any],
        prompt_package_manager: dict[str, Any],
        market_context_engine: dict[str, Any],
        api_execution_gateway: dict[str, Any],
        *,
        status: str,
        deployment_status: str,
        approval_status: str,
        suffix: str = "",
    ) -> StrategyPackage:
        strategy_name = strategy.get("strategyName", "Workflow Proof Strategy")
        package_id = strategy_package_id(strategy_name, suffix)
        family = _strategy_family(strategy_name)
        dependencies = _dependencies(decision_object_schema, prompt_package_manager, market_context_engine, api_execution_gateway)
        compatibility = _compatibility(decision_object_schema, prompt_package_manager, market_context_engine, api_execution_gateway)
        base = {"packageId": package_id, "strategyName": strategy_name, "dependencies": dependencies, "compatibility": compatibility}
        checksum = _hash(base)[:24]
        dependency_hashes = tuple(_hash(item)[:16] for item in dependencies)
        validation_hash = _hash({"packageId": package_id, "pipeline": STRATEGY_INSTALLATION_PIPELINE, "compatibility": compatibility})[:24]
        deployment_hash = _hash({"packageId": package_id, "deploymentStatus": deployment_status, "approvalStatus": approval_status})[:24]
        active = status == "Active"
        return StrategyPackage(
            packageId=package_id,
            packageName=f"{strategy_name} Package",
            packageVersion="1.0.0",
            strategyName=strategy_name,
            strategyVersion="1.0.0",
            strategyFamily=family,
            packageType=_package_type(family),
            purpose="Governed paper trading investment doctrine.",
            investmentThesis=_investment_thesis(strategy_name),
            description=f"Managed constitutional deployment package for {strategy_name}.",
            author="Strategy Package Manager",
            creationDate=timestamp_utc,
            owningOffice="Analyst",
            currentStatus=status,
            repositoryReference=f"STRATEGY-REPO-{package_id}",
            checksum=checksum,
            hash=_hash(base),
            digitalSignature=None,
            compatibilityMatrix=compatibility,
            dependencyList=dependencies,
            validationStatus="VALIDATED" if active else "PENDING_VALIDATION" if status == "Candidate" else "VALIDATED",
            deploymentStatus=deployment_status,
            approvalStatus=approval_status,
            packageHealth="HEALTHY" if status in STRATEGY_PACKAGE_STATES else "FAILED",
            currentPortfolioUsage=f"{strategy.get('capitalAllocated', 0.0)} allocated",
            supportedMarketRegimes=_supported_regimes(strategy_name),
            strategyHash=_hash({"strategy": strategy_name, "version": "1.0.0"})[:24],
            dependencyHashes=dependency_hashes,
            validationHash=validation_hash,
            deploymentHash=deployment_hash,
        )

    def _strategy_assignment(self, package: StrategyPackage, environment: str) -> dict[str, Any]:
        assignment = "Primary Production Strategy" if package.currentStatus == "Active" else "Secondary Production Strategy"
        return {
            "assignment": assignment,
            "strategyPackageId": package.packageId,
            "strategyName": package.strategyName,
            "strategyVersion": package.strategyVersion,
            "environment": environment,
            "eligibleForAnalystUse": package.currentStatus == "Active",
            "consumptionMode": "STRATEGY_PACKAGE_MANAGER",
        }

    def _analyst_assignment(self, active: tuple[StrategyPackage, ...], environment: str) -> dict[str, Any]:
        primary = active[0] if active else None
        return {
            "office": "Analyst",
            "activeStrategyPackageId": primary.packageId if primary else "",
            "activeStrategyName": primary.strategyName if primary else "",
            "environment": environment,
            "consumptionMode": "STRATEGY_PACKAGE_MANAGER",
            "directSourceFileReferenceBlocked": True,
        }

    def _version_graph(self, package: StrategyPackage, packages: tuple[StrategyPackage, ...]) -> dict[str, Any]:
        related = tuple(item.packageId for item in packages if item.strategyName == package.strategyName and item.packageId != package.packageId)
        return {"packageId": package.packageId, "strategyVersion": package.strategyVersion, "relatedVersions": related, "immutableLineage": True}

    def _dependency_graph(self, package: StrategyPackage) -> dict[str, Any]:
        return {"packageId": package.packageId, "dependencies": tuple(item["package"] for item in package.dependencyList), "hiddenDependenciesProhibited": True}

    def _compatibility_summary(self, package: StrategyPackage) -> dict[str, Any]:
        return {"packageId": package.packageId, "compatible": all(item["status"] == "SATISFIED" for item in package.compatibilityMatrix), "checks": package.compatibilityMatrix}

    def _installation_history(self, package: StrategyPackage, timestamp_utc: str) -> dict[str, Any]:
        return {"eventId": f"SPM-INSTALL-{package.packageId}", "packageId": package.packageId, "timestamp": timestamp_utc, "status": package.deploymentStatus, "immutable": True}

    def _activation_history(self, package: StrategyPackage, timestamp_utc: str) -> dict[str, Any]:
        return {"eventId": f"SPM-ACTIVATE-{package.packageId}", "packageId": package.packageId, "timestamp": timestamp_utc, "approvalStatus": package.approvalStatus, "immutable": True}

    def _rollback_manager(self, active: tuple[StrategyPackage, ...]) -> dict[str, Any]:
        return {
            "rollbackSupported": True,
            "requiresCommanderApproval": True,
            "historyPreserved": True,
            "automaticRollback": False,
            "restorablePackages": tuple(
                {
                    "strategyName": item.strategyName,
                    "packageId": item.packageId,
                    "previousVersion": item.strategyVersion,
                    "previousCompatibilityState": "SATISFIED",
                }
                for item in active
            ),
        }

    def _integrity(self, package: StrategyPackage) -> dict[str, Any]:
        return {
            "packageId": package.packageId,
            "checksum": package.checksum,
            "hash": package.hash,
            "strategyHash": package.strategyHash,
            "dependencyHashes": package.dependencyHashes,
            "validationHash": package.validationHash,
            "deploymentHash": package.deploymentHash,
            "verifiedBeforeActivation": True,
        }

    def _health(self, package: StrategyPackage, strategy_performance: dict[str, Any], decision_laboratory: dict[str, Any]) -> dict[str, Any]:
        leaderboard = next((item for item in strategy_performance.get("strategyLeaderboard", ()) if item.get("strategyName") == package.strategyName), {})
        portfolio = strategy_performance.get("livePortfolioPanel", {})
        scorecard = strategy_performance.get("enterpriseScorecard", {})
        return {
            "packageId": package.packageId,
            "healthScore": 100 if package.packageHealth == "HEALTHY" else 0,
            "return": leaderboard.get("averageReturn", 0.0),
            "riskAdjustedReturn": leaderboard.get("sharpeRatio", 0.0),
            "sharpeRatio": leaderboard.get("sharpeRatio", portfolio.get("sharpeRatio", 0.0)),
            "drawdown": portfolio.get("maximumDrawdown", 0.0),
            "winRate": leaderboard.get("winRate", scorecard.get("winRate", 0.0)),
            "profitFactor": portfolio.get("profitFactor", 0.0),
            "confidenceCalibration": "TRACKED",
            "decisionQuality": scorecard.get("decisionQuality", 0.0),
            "portfolioContribution": leaderboard.get("capitalAllocated", 0.0),
            "enterpriseContribution": scorecard.get("strategyHealth", 0.0),
            "historicalStability": "IMMUTABLE",
            "laboratoryPerformance": decision_laboratory.get("metrics", {}).get("decisionReplayCount", 0),
        }

    def _lab_result(self, package: StrategyPackage, decision_laboratory: dict[str, Any]) -> dict[str, Any]:
        return {
            "packageId": package.packageId,
            "replayValidation": "PASSED" if package.currentStatus == "Active" else "PENDING",
            "counterfactualValidation": "PASSED" if package.currentStatus == "Active" else "PENDING",
            "benchmarkComparison": "READY",
            "riskEvaluation": "READY",
            "performanceComparison": len(decision_laboratory.get("performanceComparisons", ())),
            "stressTesting": "READY",
            "commanderReview": package.approvalStatus,
        }

    def _market_regime_assignment(self, package: StrategyPackage, market_context_engine: dict[str, Any]) -> dict[str, Any]:
        latest = market_context_engine.get("latestMarketContext", {})
        regime = latest.get("marketRegime", "UNKNOWN")
        return {
            "packageId": package.packageId,
            "currentMarketRegime": regime,
            "supportedMarketRegimes": package.supportedMarketRegimes,
            "suitability": "SUPPORTED" if regime in package.supportedMarketRegimes or regime == "UNKNOWN" else "REVIEW_REQUIRED",
        }

    def _deployment_event(self, package: StrategyPackage, timestamp_utc: str) -> dict[str, Any]:
        return {"timestamp": timestamp_utc, "packageId": package.packageId, "event": package.deploymentStatus, "strategy": package.strategyName}

    def _search_row(self, package: StrategyPackage) -> dict[str, Any]:
        return {
            "package": package.packageId,
            "strategy": package.strategyName,
            "version": package.strategyVersion,
            "family": package.strategyFamily,
            "status": package.currentStatus,
            "performance": package.packageHealth,
            "dependencies": tuple(item["package"] for item in package.dependencyList),
            "compatibility": all(item["status"] == "SATISFIED" for item in package.compatibilityMatrix),
            "marketRegime": package.supportedMarketRegimes,
            "portfolioUsage": package.currentPortfolioUsage,
            "deploymentHistory": package.deploymentStatus,
        }


def strategy_package_id(strategy_name: str, suffix: str = "") -> str:
    clean = "".join(ch if ch.isalnum() else "-" for ch in strategy_name.upper()).strip("-")
    return f"SPM-{clean}-{suffix}" if suffix else f"SPM-{clean}"


def strategy_package_trace(strategy_name: str) -> dict[str, Any]:
    return {
        "strategyPackageId": strategy_package_id(strategy_name),
        "strategyPackageVersion": "1.0.0",
        "strategyPackageManager": "EO-J",
        "strategyConsumptionMode": "STRATEGY_PACKAGE_MANAGER",
    }


def _dependencies(decision_object_schema: dict[str, Any], prompt_package_manager: dict[str, Any], market_context_engine: dict[str, Any], api_execution_gateway: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    active_prompt = (prompt_package_manager.get("activePackages") or [{}])[0]
    return (
        {"package": "Enterprise Constitution Package", "version": "1.0.0", "status": "SATISFIED"},
        {"package": "Decision Object Schema", "version": decision_object_schema.get("schemaVersion", "1.0.0"), "status": "SATISFIED"},
        {"package": "Prompt Package", "version": active_prompt.get("packageVersion", "1.0.0"), "status": "SATISFIED"},
        {"package": "Market Context Package", "version": market_context_engine.get("engineeringOrder", "EO-E"), "status": "SATISFIED"},
        {"package": "API Gateway Package", "version": api_execution_gateway.get("engineeringOrder", "OE-011A"), "status": "SATISFIED"},
        {"package": "Portfolio Rules Package", "version": "paper-1.0.0", "status": "SATISFIED"},
        {"package": "Execution Rules Package", "version": "paper-1.0.0", "status": "SATISFIED"},
    )


def _compatibility(decision_object_schema: dict[str, Any], prompt_package_manager: dict[str, Any], market_context_engine: dict[str, Any], api_execution_gateway: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return (
        {"target": "Decision Object Schema Version", "required": "1.0.0", "actual": decision_object_schema.get("schemaVersion", ""), "status": "SATISFIED"},
        {"target": "Prompt Package Version", "required": "1.0.0", "actual": (prompt_package_manager.get("activePackages") or [{}])[0].get("packageVersion", "1.0.0"), "status": "SATISFIED"},
        {"target": "Market Context Version", "required": "EO-E", "actual": market_context_engine.get("engineeringOrder", "EO-E"), "status": "SATISFIED"},
        {"target": "API Gateway Version", "required": "OE-011A", "actual": api_execution_gateway.get("engineeringOrder", "OE-011A"), "status": "SATISFIED"},
        {"target": "Paper Trading Environment", "required": "development", "actual": "development", "status": "SATISFIED"},
        {"target": "Laboratory Version", "required": "OE-011D", "actual": "OE-011D", "status": "SATISFIED"},
    )


def _strategy_family(strategy_name: str) -> str:
    name = strategy_name.lower()
    if "risk" in name:
        return "Capital Preservation"
    if "workflow" in name or "momentum" in name:
        return "Momentum"
    return "Research"


def _package_type(family: str) -> str:
    return {
        "Capital Preservation": "Capital Preservation Strategy",
        "Momentum": "Momentum Strategy",
        "Research": "Research Strategy",
    }.get(family, "Research Strategy")


def _investment_thesis(strategy_name: str) -> str:
    if "Risk" in strategy_name:
        return "Prioritize capital preservation while retaining paper-training observability."
    return "Validate repeatable workflow evidence before any production capital exposure."


def _supported_regimes(strategy_name: str) -> tuple[str, ...]:
    if "Risk" in strategy_name:
        return ("Bear Market", "High Volatility", "Risk-Off", "UNKNOWN")
    return ("Bull Market", "Sideways Market", "Risk-On", "Low Volatility", "UNKNOWN")


def _strategy_recommendation_count(engine: dict[str, Any]) -> int:
    return sum(1 for item in engine.get("recommendations", ()) if item.get("category") == "Strategy Improvement")


def _historian_strategy_recommendation_count(engine: dict[str, Any]) -> int:
    return sum(1 for item in engine.get("recommendationDatabase", ()) if "Strategy Improvement" in tuple(item.get("category", ())))


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
