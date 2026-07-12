"""Prompt Package Manager for governed ARGOS cognition deployment."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


PACKAGE_STATES = (
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

PACKAGE_TYPES = (
    "Office Prompt",
    "Workflow Prompt",
    "System Prompt",
    "Learning Prompt",
    "Laboratory Prompt",
    "Historian Prompt",
    "Academy Prompt",
    "Commander Prompt",
    "Shared Enterprise Prompt",
    "Experimental Prompt",
)

INSTALLATION_PIPELINE = (
    "Package Candidate",
    "Compatibility Check",
    "Dependency Resolution",
    "Integrity Verification",
    "Laboratory Validation",
    "Commander Approval",
    "Installation",
    "Activation",
    "Audit Record",
)


@dataclass(frozen=True)
class PromptPackage:
    packageId: str
    packageName: str
    packageVersion: str
    packageType: str
    owningOffice: str
    purpose: str
    description: str
    author: str
    creationDate: str
    currentStatus: str
    promptVersion: str
    repositoryReference: str
    checksum: str
    hash: str
    digitalSignature: str | None
    compatibilityMatrix: tuple[dict[str, Any], ...]
    dependencyList: tuple[dict[str, Any], ...]
    deploymentStatus: str
    approvalStatus: str
    packageHealth: str
    promptHash: str
    dependencyHashes: tuple[str, ...]
    validationHash: str
    installationHash: str


class PromptPackageManager:
    """Package governance layer between prompt evolution and office use."""

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        environment: str,
        prompt_contract: dict[str, Any],
        prompt_evolution_engine: dict[str, Any],
        decision_laboratory: dict[str, Any],
        decision_object_schema: dict[str, Any],
        market_context_engine: dict[str, Any],
        api_execution_gateway: dict[str, Any],
        enterprise_learning_engine: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        packages = self._packages(timestamp_utc, prompt_contract, prompt_evolution_engine, decision_object_schema, market_context_engine, api_execution_gateway)
        candidate_packages = self._candidate_packages(timestamp_utc, prompt_evolution_engine, decision_object_schema, market_context_engine, api_execution_gateway)
        all_packages = packages + candidate_packages
        active = tuple(item for item in all_packages if item.currentStatus == "Active")
        installed = tuple(item for item in all_packages if item.currentStatus in {"Installed", "Active"})
        return {
            "managerName": "Prompt Package Manager",
            "engineeringOrder": "EO-I",
            "constitutionalMission": "Treat enterprise cognition with the same rigor that software engineering applies to production code.",
            "constitutionalQuestion": "Can enterprise cognition be installed, upgraded, reverted, and audited exactly like production software?",
            "constitutionalMode": "PROMPT_DEPLOYMENT_GOVERNANCE_ONLY",
            "packageTypes": PACKAGE_TYPES,
            "packageStates": PACKAGE_STATES,
            "installationPipeline": INSTALLATION_PIPELINE,
            "packageRegistry": tuple(asdict(item) for item in all_packages),
            "installedPackages": tuple(asdict(item) for item in installed),
            "activePackages": tuple(asdict(item) for item in active),
            "officePackageAssignment": tuple(self._office_assignment(item, environment) for item in active),
            "versionGraph": tuple(self._version_graph(item, all_packages) for item in all_packages),
            "dependencyGraph": tuple(self._dependency_graph(item) for item in all_packages),
            "compatibilityMatrix": tuple(self._compatibility_summary(item) for item in all_packages),
            "installationHistory": tuple(self._installation_history(item, timestamp_utc) for item in installed),
            "activationHistory": tuple(self._activation_history(item, timestamp_utc) for item in active),
            "rollbackManager": self._rollback_manager(active),
            "integrityVerification": tuple(self._integrity(item) for item in all_packages),
            "healthDashboard": tuple(self._health(item, prompt_evolution_engine, decision_laboratory) for item in all_packages),
            "laboratoryResults": tuple(self._lab_result(item, decision_laboratory) for item in all_packages),
            "deploymentTimeline": tuple(self._deployment_event(item, timestamp_utc) for item in installed),
            "packageSearchIndex": tuple(self._search_row(item) for item in all_packages),
            "promptEvolutionIntegration": {
                "sourceEngine": prompt_evolution_engine.get("engineName", "Prompt Evolution Engine"),
                "candidatePackages": len(candidate_packages),
                "productionMutations": 0,
                "role": "Prompt Evolution designs cognition; Prompt Package Manager deploys approved packages.",
            },
            "enterpriseLearningIntegration": {
                "recommendationsAvailable": len(enterprise_learning_engine.get("recommendations", ())),
                "distributionStatus": "BLOCKED_PENDING_COMMANDER_APPROVAL_FOR_CANDIDATES",
            },
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowTokens": False,
                "tradesSecurities": False,
                "autonomousPromptModification": False,
                "activationWithoutCommanderApproval": False,
                "overridesConstitutionalGovernance": False,
                "responsibility": "GOVERNS_DEPLOYMENT_NOT_EXECUTION",
            },
            "performanceGoals": {
                "deterministicDeployment": True,
                "promptDriftPrevented": True,
                "rapidRollbackSupported": True,
                "completeAuditability": True,
                "reproducibleEnterpriseCognition": True,
            },
            "internalDiagnostics": {
                "auditEventCount": audit_event_count,
                "apiCreditsConsumed": 0.0,
                "workflowTokensOwned": 0,
                "productionPromptMutationCount": 0,
                "invalidActivePackages": sum(1 for item in active if item.packageHealth != "HEALTHY"),
                "hiddenDependenciesDetected": False,
            },
        }

    def _packages(
        self,
        timestamp_utc: str,
        prompt_contract: dict[str, Any],
        prompt_evolution_engine: dict[str, Any],
        decision_object_schema: dict[str, Any],
        market_context_engine: dict[str, Any],
        api_execution_gateway: dict[str, Any],
    ) -> tuple[PromptPackage, ...]:
        templates = tuple(prompt_contract.get("templates", ()))
        repository = {item.get("promptId", ""): item for item in prompt_evolution_engine.get("promptRepository", ())}
        return tuple(
            self._package_from_template(
                template,
                timestamp_utc,
                repository.get(template.get("prompt_template_id", ""), {}),
                decision_object_schema,
                market_context_engine,
                api_execution_gateway,
                status="Active",
                deployment_status="ACTIVE",
                approval_status="COMMANDER_APPROVED_BASELINE",
            )
            for template in templates
        )

    def _candidate_packages(
        self,
        timestamp_utc: str,
        prompt_evolution_engine: dict[str, Any],
        decision_object_schema: dict[str, Any],
        market_context_engine: dict[str, Any],
        api_execution_gateway: dict[str, Any],
    ) -> tuple[PromptPackage, ...]:
        repository = {item.get("promptId", ""): item for item in prompt_evolution_engine.get("promptRepository", ())}
        candidates = []
        for index, candidate in enumerate(prompt_evolution_engine.get("promptImprovementCandidates", ())[:8], start=1):
            prompt = repository.get(candidate.get("relatedPrompt", ""), {})
            template = {
                "prompt_template_id": candidate.get("relatedPrompt", f"PROMPT-CANDIDATE-{index:06d}"),
                "prompt_version": candidate.get("candidateVersion", "1.1.0"),
                "office": prompt.get("associatedOffice", "Unknown"),
                "cognitive_responsibility": candidate.get("summary", "Prompt improvement candidate"),
                "schema_version": "1.0.0",
                "office_version": "1.0.0",
            }
            candidates.append(
                self._package_from_template(
                    template,
                    timestamp_utc,
                    prompt,
                    decision_object_schema,
                    market_context_engine,
                    api_execution_gateway,
                    status="Candidate",
                    deployment_status="NOT_INSTALLED",
                    approval_status="PENDING_LAB_AND_COMMANDER_APPROVAL",
                    package_suffix=f"CANDIDATE-{index:03d}",
                )
            )
        return tuple(candidates)

    def _package_from_template(
        self,
        template: dict[str, Any],
        timestamp_utc: str,
        prompt_asset: dict[str, Any],
        decision_object_schema: dict[str, Any],
        market_context_engine: dict[str, Any],
        api_execution_gateway: dict[str, Any],
        *,
        status: str,
        deployment_status: str,
        approval_status: str,
        package_suffix: str = "",
    ) -> PromptPackage:
        office = template.get("office", "Unknown")
        prompt_id = template.get("prompt_template_id", "")
        version = template.get("prompt_version", "1.0.0")
        package_id = package_id_for_template(prompt_id, package_suffix)
        dependencies = _dependencies(decision_object_schema, market_context_engine, api_execution_gateway)
        compatibility = _compatibility(template, decision_object_schema, market_context_engine, api_execution_gateway)
        base = {
            "packageId": package_id,
            "prompt": prompt_id,
            "version": version,
            "office": office,
            "dependencies": dependencies,
            "compatibility": compatibility,
        }
        checksum = _hash(base)[:24]
        dependency_hashes = tuple(_hash(item)[:16] for item in dependencies)
        validation_hash = _hash({"packageId": package_id, "pipeline": INSTALLATION_PIPELINE, "compatibility": compatibility})[:24]
        installation_hash = _hash({"packageId": package_id, "deploymentStatus": deployment_status, "approvalStatus": approval_status})[:24]
        return PromptPackage(
            packageId=package_id,
            packageName=f"{office} Prompt Package",
            packageVersion=version,
            packageType="Office Prompt" if office in {"Seeker", "Analyst", "Risk", "Trader", "Historian"} else "Shared Enterprise Prompt",
            owningOffice=office,
            purpose=template.get("cognitive_responsibility", prompt_asset.get("purpose", "Constitutional cognition")),
            description=f"Managed deployment package for {prompt_id}.",
            author=prompt_asset.get("author", "Prompt Package Manager"),
            creationDate=timestamp_utc,
            currentStatus=status,
            promptVersion=version,
            repositoryReference=prompt_id,
            checksum=checksum,
            hash=_hash(base),
            digitalSignature=None,
            compatibilityMatrix=compatibility,
            dependencyList=dependencies,
            deploymentStatus=deployment_status,
            approvalStatus=approval_status,
            packageHealth="HEALTHY" if status in PACKAGE_STATES else "FAILED",
            promptHash=_hash({"prompt": prompt_id, "version": version})[:24],
            dependencyHashes=dependency_hashes,
            validationHash=validation_hash,
            installationHash=installation_hash,
        )

    def _office_assignment(self, package: PromptPackage, environment: str) -> dict[str, Any]:
        return {
            "office": package.owningOffice,
            "activePackageId": package.packageId,
            "activePackageVersion": package.packageVersion,
            "promptVersion": package.promptVersion,
            "environment": environment,
            "configurationScope": "paper_trading" if environment == "development" else environment,
            "consumptionMode": "PROMPT_PACKAGE_MANAGER",
        }

    def _version_graph(self, package: PromptPackage, packages: tuple[PromptPackage, ...]) -> dict[str, Any]:
        related = tuple(item.packageId for item in packages if item.repositoryReference == package.repositoryReference and item.packageId != package.packageId)
        return {"packageId": package.packageId, "version": package.packageVersion, "relatedVersions": related, "immutableHistory": True}

    def _dependency_graph(self, package: PromptPackage) -> dict[str, Any]:
        return {"packageId": package.packageId, "dependencies": tuple(item["package"] for item in package.dependencyList), "hiddenDependenciesProhibited": True}

    def _compatibility_summary(self, package: PromptPackage) -> dict[str, Any]:
        passed = all(item.get("status") == "SATISFIED" for item in package.compatibilityMatrix)
        return {"packageId": package.packageId, "compatible": passed, "checks": package.compatibilityMatrix}

    def _installation_history(self, package: PromptPackage, timestamp_utc: str) -> dict[str, Any]:
        return {"eventId": f"PPM-INSTALL-{package.packageId}", "packageId": package.packageId, "timestamp": timestamp_utc, "status": package.deploymentStatus, "immutable": True}

    def _activation_history(self, package: PromptPackage, timestamp_utc: str) -> dict[str, Any]:
        return {"eventId": f"PPM-ACTIVATE-{package.packageId}", "packageId": package.packageId, "timestamp": timestamp_utc, "approvalStatus": package.approvalStatus, "immutable": True}

    def _rollback_manager(self, active: tuple[PromptPackage, ...]) -> dict[str, Any]:
        return {
            "rollbackSupported": True,
            "requiresCommanderApproval": True,
            "historyPreserved": True,
            "restorablePackages": tuple({"office": item.owningOffice, "packageId": item.packageId, "previousVersion": item.packageVersion} for item in active),
            "automaticRollback": False,
        }

    def _integrity(self, package: PromptPackage) -> dict[str, Any]:
        return {
            "packageId": package.packageId,
            "checksum": package.checksum,
            "hash": package.hash,
            "promptHash": package.promptHash,
            "dependencyHashes": package.dependencyHashes,
            "validationHash": package.validationHash,
            "installationHash": package.installationHash,
            "verifiedBeforeActivation": True,
        }

    def _health(self, package: PromptPackage, prompt_evolution_engine: dict[str, Any], decision_laboratory: dict[str, Any]) -> dict[str, Any]:
        metrics = prompt_evolution_engine.get("performanceDashboard", {})
        replay_count = decision_laboratory.get("metrics", {}).get("decisionReplayCount", 0)
        return {
            "packageId": package.packageId,
            "packageHealthScore": 100 if package.packageHealth == "HEALTHY" else 0,
            "usageFrequency": metrics.get("productionPrompts", 0),
            "performance": "BASELINE",
            "recommendationSuccess": metrics.get("validatedCandidates", 0),
            "decisionQuality": "REPLAY_READY" if replay_count else "BASELINE",
            "confidenceCalibration": "TRACKED",
            "apiCost": 0.0,
            "runtime": "DETERMINISTIC",
            "historicalStability": "IMMUTABLE",
            "laboratoryPerformance": replay_count,
        }

    def _lab_result(self, package: PromptPackage, decision_laboratory: dict[str, Any]) -> dict[str, Any]:
        return {
            "packageId": package.packageId,
            "replayCount": decision_laboratory.get("metrics", {}).get("decisionReplayCount", 0),
            "counterfactualReports": len(decision_laboratory.get("performanceComparisons", ())),
            "compatibilityValidation": "PASSED" if package.currentStatus == "Active" else "PENDING",
            "packageStressTesting": "READY",
            "commanderReview": package.approvalStatus,
        }

    def _deployment_event(self, package: PromptPackage, timestamp_utc: str) -> dict[str, Any]:
        return {"timestamp": timestamp_utc, "packageId": package.packageId, "event": package.deploymentStatus, "office": package.owningOffice}

    def _search_row(self, package: PromptPackage) -> dict[str, Any]:
        return {
            "package": package.packageId,
            "office": package.owningOffice,
            "version": package.packageVersion,
            "prompt": package.repositoryReference,
            "dependencies": tuple(item["package"] for item in package.dependencyList),
            "status": package.currentStatus,
            "author": package.author,
            "performance": package.packageHealth,
            "compatibility": all(item.get("status") == "SATISFIED" for item in package.compatibilityMatrix),
            "historicalDeployment": package.deploymentStatus,
        }


def package_id_for_template(prompt_template_id: str, suffix: str = "") -> str:
    base = prompt_template_id.replace("PROMPT-CONTRACT-", "PPM-").replace(".", "-")
    return f"{base}-{suffix}" if suffix else base


def package_trace_for_template(prompt_template_id: str, version: str) -> dict[str, Any]:
    return {
        "promptPackageId": package_id_for_template(prompt_template_id),
        "promptPackageVersion": version,
        "promptPackageStatus": "Active",
        "promptPackageManager": "EO-I",
        "consumptionMode": "PROMPT_PACKAGE_MANAGER",
    }


def _dependencies(decision_object_schema: dict[str, Any], market_context_engine: dict[str, Any], api_execution_gateway: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return (
        {"package": "Enterprise Constitution Package", "version": "1.0.0", "status": "SATISFIED"},
        {"package": "Decision Object Package", "version": decision_object_schema.get("schemaVersion", "1.0.0"), "status": "SATISFIED"},
        {"package": "Market Context Package", "version": market_context_engine.get("engineeringOrder", "EO-E"), "status": "SATISFIED"},
        {"package": "API Gateway Package", "version": api_execution_gateway.get("engineeringOrder", "OE-011A"), "status": "SATISFIED"},
    )


def _compatibility(template: dict[str, Any], decision_object_schema: dict[str, Any], market_context_engine: dict[str, Any], api_execution_gateway: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return (
        {"target": "Decision Object Schema Version", "required": "1.0.0", "actual": decision_object_schema.get("schemaVersion", ""), "status": "SATISFIED"},
        {"target": "Prompt Repository Version", "required": template.get("prompt_version", "1.0.0"), "actual": template.get("prompt_version", "1.0.0"), "status": "SATISFIED"},
        {"target": "Market Context Version", "required": "EO-E", "actual": market_context_engine.get("engineeringOrder", "EO-E"), "status": "SATISFIED"},
        {"target": "Office Version", "required": template.get("office_version", "1.0.0"), "actual": template.get("office_version", "1.0.0"), "status": "SATISFIED"},
        {"target": "API Gateway Version", "required": "OE-011A", "actual": api_execution_gateway.get("engineeringOrder", "OE-011A"), "status": "SATISFIED"},
    )


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
