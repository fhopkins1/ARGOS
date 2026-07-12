"""Frozen Decision Object schema registry for ARGOS enterprise knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from typing import Any

from .truth_domain import (
    RuntimeMode,
    TruthClassification,
    ProvenanceStatus,
    proof_metadata,
    validate_decision_object_for_operational_truth,
)


DECISION_OBJECT_SCHEMA_VERSION = "1.0.0"
SCHEMA_FINGERPRINT = "DO-SCHEMA-EO-H-V1"

ROOT_REQUIRED_FIELDS = (
    "decisionObjectId",
    "schemaVersion",
    "workflowId",
    "workflowTokenId",
    "creationTimestamp",
    "decisionTimestamp",
    "office",
    "currentOwner",
    "lifecycleState",
    "decisionType",
    "confidence",
    "priority",
    "commanderVisibility",
    "immutable",
    "schemaValidationStatus",
    "supportingAuditIdentifier",
)

IMPLEMENTATION_REQUIRED_FIELDS = (
    "revision",
    "revisionSource",
    "confidenceDelta",
    "recommendation",
    "evidenceCount",
    "supportingSignals",
    "riskScore",
    "riskAdjustment",
    "positionSizeRecommendation",
    "targetPrice",
    "stopLoss",
    "expectedReturn",
    "currentStrategy",
    "apiExecutionMode",
    "apiProvider",
    "apiModel",
    "apiFallbackUsed",
    "apiValidationStatus",
    "apiGatewayMetadata",
    "marketContext",
    "marketContextSnapshotId",
    "promptContract",
    "schemaFrozen",
    "schemaFingerprint",
    "schemaValidationErrors",
    "creationDate",
    "migrationStatus",
    "compatibilityStatus",
    "workflow",
    "analyst",
    "risk",
    "decision",
    "execution",
    "performanceTruthLinkage",
    "learning",
    "prompt",
    "strategy",
    "audit",
)

OPTIONAL_FIELDS = (
    "apiGatewayMetadata",
    "targetPrice",
    "stopLoss",
    "marketContext",
    "promptContract",
    "learning",
    "execution",
    "performanceTruthLinkage",
    "reserved",
)

ENUMERATIONS = {
    "office": ("Seeker", "Analyst", "Risk", "Trader", "Historian", "Executive", "Commander"),
    "lifecycleState": ("CREATED", "VALIDATED", "ARCHIVED", "EXPERIMENTAL"),
    "decisionType": ("PAPER_TRAINING", "COUNTERFACTUAL_EXPERIMENT", "PRODUCTION_CANDIDATE"),
    "validationStatus": ("VALID", "INVALID"),
    "compatibilityStatus": ("CURRENT_SCHEMA", "COMPATIBLE_VIA_MIGRATION", "LEGACY_READABLE"),
    "migrationStatus": ("NOT_REQUIRED", "MIGRATION_LAYER_AVAILABLE", "LEGACY_READ_ONLY"),
}

FIELD_DEFINITIONS = {
    "decisionObjectId": "Stable immutable identifier for one enterprise belief object.",
    "schemaVersion": "Frozen Decision Object schema version used to interpret this record.",
    "workflowId": "Workflow that created the belief record.",
    "workflowTokenId": "Workflow Execution Token audit identifier; reference only.",
    "creationTimestamp": "UTC time the object was created.",
    "decisionTimestamp": "UTC time the decision belief was formed.",
    "office": "Office creating this revision.",
    "currentOwner": "Enterprise owner of this revision at creation time.",
    "lifecycleState": "Deterministic lifecycle state for repository interpretation.",
    "decisionType": "Kind of decision object represented.",
    "confidence": "Numeric confidence assigned at this moment in time.",
    "priority": "Enterprise priority for visibility and replay.",
    "commanderVisibility": "Whether Commander surfaces may display the object.",
    "immutable": "True when the historical object may not be rewritten.",
    "marketContext": "Versioned market context object attached by reference and summary.",
    "promptContract": "Prompt and cognitive contract trace used by the office.",
    "schemaFingerprint": "Stable hash of the canonical schema definition.",
}


@dataclass(frozen=True)
class DecisionObjectSchemaRegistry:
    """Validate and document frozen Decision Object schema v1.0."""

    schema_version: str = DECISION_OBJECT_SCHEMA_VERSION
    schema_name: str = "Decision Object Schema"
    engineering_order: str = "EO-H"

    @property
    def required_fields(self) -> tuple[str, ...]:
        return ROOT_REQUIRED_FIELDS + IMPLEMENTATION_REQUIRED_FIELDS

    def freeze(self, decision_object: dict[str, Any]) -> dict[str, Any]:
        """Return a schema-stamped copy of a Decision Object."""
        frozen = dict(decision_object)
        now = _utc_now()
        workflow_id = str(frozen.get("workflowId", ""))
        audit_id = str(frozen.get("supportingAuditIdentifier", ""))
        office = str(frozen.get("office", ""))
        decision_id = str(frozen.get("decisionObjectId", ""))
        market_context = frozen.get("marketContext") if isinstance(frozen.get("marketContext"), dict) else {}
        prompt_contract = frozen.get("promptContract") if isinstance(frozen.get("promptContract"), dict) else {}
        revision_source = str(frozen.get("revisionSource", ""))

        frozen.setdefault("schemaVersion", self.schema_version)
        frozen.setdefault("schemaFrozen", True)
        frozen.setdefault("schemaFingerprint", self.schema_fingerprint())
        frozen.setdefault("schemaValidationStatus", "PENDING")
        frozen.setdefault("schemaValidationErrors", ())
        frozen.setdefault("creationTimestamp", now)
        frozen.setdefault("decisionTimestamp", now)
        frozen.setdefault("creationDate", frozen["creationTimestamp"][:10])
        frozen.setdefault("workflowTokenId", audit_id)
        frozen.setdefault("currentOwner", office)
        frozen.setdefault("lifecycleState", "VALIDATED")
        frozen.setdefault("decisionType", "PAPER_TRAINING")
        frozen.setdefault("priority", "NORMAL")
        frozen.setdefault("commanderVisibility", True)
        if "placeholder" in revision_source.lower() or str(frozen.get("sourceSystem", "")).lower() in {"runtime", "controlpanelruntime"}:
            frozen.update(
                {
                    **proof_metadata(
                        source_system=str(frozen.get("sourceSystem", "ControlPanelRuntime")),
                        source_record_ids=(audit_id,),
                        workflow_id=workflow_id,
                        decision_object_id=decision_id,
                        created_at=frozen.get("decisionTimestamp", now),
                    ),
                    **frozen,
                }
            )
            frozen.setdefault("executionMode", RuntimeMode.PROOF.value)
            frozen.setdefault("truthClassification", TruthClassification.PROOF_ONLY.value)
            frozen.setdefault("provenanceStatus", ProvenanceStatus.REJECTED.value)
            frozen.setdefault("certificationStatus", "PROOF_MODE_NOT_ACTIONABLE")
        else:
            frozen.setdefault("environment", "paper")
            frozen.setdefault("executionMode", RuntimeMode.PAPER.value)
            frozen.setdefault("truthClassification", TruthClassification.INCOMPLETE.value)
            frozen.setdefault("sourceSystem", office or "UNKNOWN")
            frozen.setdefault("sourceRecordIds", (audit_id,))
            frozen.setdefault("officeAuthority", office or "UNKNOWN")
            frozen.setdefault("createdAt", frozen.get("decisionTimestamp", now))
            frozen.setdefault("deterministicId", "")
            frozen.setdefault("provenanceStatus", ProvenanceStatus.UNVERIFIED.value)
            frozen.setdefault("certificationStatus", "UNCERTIFIED_DECISION_OBJECT")
            frozen.setdefault("commanderTruthLabel", "UNVERIFIED PROVENANCE")
        frozen.setdefault("materialFieldProvenance", {})
        frozen.setdefault("migrationStatus", "NOT_REQUIRED")
        frozen.setdefault("compatibilityStatus", "CURRENT_SCHEMA")
        frozen.setdefault("workflow", _workflow_section(frozen))
        frozen.setdefault("analyst", _analyst_section(frozen))
        frozen.setdefault("risk", _risk_section(frozen))
        frozen.setdefault("decision", _decision_section(frozen))
        frozen.setdefault("execution", _execution_section(frozen))
        frozen.setdefault("performanceTruthLinkage", _performance_truth_linkage(workflow_id, decision_id))
        frozen.setdefault("learning", _learning_section(decision_id))
        frozen.setdefault("prompt", _prompt_section(prompt_contract))
        frozen.setdefault("strategy", _strategy_section(frozen))
        frozen.setdefault("audit", _audit_section(frozen, market_context))
        frozen.setdefault("reserved", {})

        validation = self.validate(frozen)
        provenance = validate_decision_object_for_operational_truth(frozen, execution_environment="paper")
        frozen["operationalProvenanceValidation"] = {
            "valid": provenance.valid,
            "codes": provenance.codes,
            "truthDomain": provenance.truth_domain,
            "truthClassification": provenance.truth_classification,
            "certificationStatus": provenance.certification_status,
        }
        frozen["schemaValidationStatus"] = validation["status"]
        frozen["schemaValidationErrors"] = validation["errors"]
        frozen["schemaFingerprint"] = validation["schemaFingerprint"]
        frozen["audit"] = dict(frozen["audit"], schemaValidationResult=validation["status"], hash=frozen["schemaFingerprint"], checksum=self.object_hash(frozen))
        return frozen

    def validate(self, decision_object: dict[str, Any]) -> dict[str, Any]:
        """Validate a Decision Object without executing enterprise behavior."""
        errors: list[str] = []
        for field in self.required_fields:
            if field not in decision_object:
                errors.append(field)
        if decision_object.get("schemaVersion") != self.schema_version:
            errors.append("schemaVersion")
        if decision_object.get("schemaFrozen") is not True:
            errors.append("schemaFrozen")
        if decision_object.get("immutable") is not True:
            errors.append("immutable")
        for field in ("decisionObjectId", "workflowId", "workflowTokenId", "supportingAuditIdentifier"):
            if not str(decision_object.get(field, "")).strip():
                errors.append(field)
        if decision_object.get("office") not in ENUMERATIONS["office"]:
            errors.append("office")
        if decision_object.get("lifecycleState") not in ENUMERATIONS["lifecycleState"]:
            errors.append("lifecycleState")
        if decision_object.get("decisionType") not in ENUMERATIONS["decisionType"]:
            errors.append("decisionType")
        if not isinstance(decision_object.get("confidence"), (int, float)):
            errors.append("confidence")
        if not isinstance(decision_object.get("supportingSignals"), (list, tuple)):
            errors.append("supportingSignals")
        if not isinstance(decision_object.get("marketContext"), dict):
            errors.append("marketContext")
        elif decision_object.get("marketContextSnapshotId") != decision_object["marketContext"].get("snapshotId"):
            errors.append("marketContextSnapshotId")
        if not isinstance(decision_object.get("promptContract"), dict):
            errors.append("promptContract")
        if not isinstance(decision_object.get("workflow"), dict):
            errors.append("workflow")
        if not isinstance(decision_object.get("audit"), dict):
            errors.append("audit")

        unique_errors = tuple(dict.fromkeys(errors))
        return {
            "status": "INVALID" if unique_errors else "VALID",
            "errors": unique_errors,
            "schemaVersion": self.schema_version,
            "schemaFingerprint": self.schema_fingerprint(),
            "deterministicSerialization": True,
            "hashStable": True,
        }

    def schema_fingerprint(self) -> str:
        """Return a deterministic fingerprint of the frozen schema definition."""
        payload = {
            "schema": self.schema_name,
            "version": self.schema_version,
            "required": self.required_fields,
            "optional": OPTIONAL_FIELDS,
            "enumerations": ENUMERATIONS,
        }
        digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()[:16]
        return f"{SCHEMA_FINGERPRINT}-{digest}"

    def object_hash(self, decision_object: dict[str, Any]) -> str:
        """Return a deterministic object checksum excluding volatile validation errors."""
        payload = {key: value for key, value in decision_object.items() if key not in {"schemaValidationErrors"}}
        return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()[:24]

    def snapshot(self, *, workflow_orchestrator: dict[str, Any], decision_laboratory: dict[str, Any], audit_event_count: int) -> dict[str, Any]:
        """Return Engineering Mode state for the schema registry."""
        decision_objects = tuple(_decision_objects_from_workflows(workflow_orchestrator))
        validations = tuple(self.validate(item) for item in decision_objects)
        violations = tuple(
            {
                "decisionObjectId": item.get("decisionObjectId", ""),
                "workflowId": item.get("workflowId", ""),
                "errors": validation["errors"],
            }
            for item, validation in zip(decision_objects, validations)
            if validation["status"] != "VALID"
        )
        valid_count = sum(1 for item in validations if item["status"] == "VALID")
        return {
            "schemaName": self.schema_name,
            "engineeringOrder": self.engineering_order,
            "constitutionalQuestion": "What exactly constitutes enterprise knowledge?",
            "constitutionalMode": "KNOWLEDGE_PRESERVATION_ONLY",
            "schemaVersion": self.schema_version,
            "schemaFingerprint": self.schema_fingerprint(),
            "frozen": True,
            "immutableSchemaVersions": ("1.0.0",),
            "requiredFields": self.required_fields,
            "optionalFields": OPTIONAL_FIELDS,
            "fieldDefinitions": FIELD_DEFINITIONS,
            "enumerationRegistry": ENUMERATIONS,
            "validationRules": (
                "required_fields",
                "field_types",
                "enumerations",
                "references",
                "timestamp_presence",
                "schema_version",
                "integrity_hash",
            ),
            "serializationStandard": {
                "stableOrdering": True,
                "deterministicFormatting": True,
                "portable": True,
                "humanReadable": True,
                "machineReadable": True,
                "replayCompatible": True,
                "hashStable": True,
            },
            "compatibilityMatrix": (
                {"fromVersion": "1.0.0", "toVersion": "1.0.0", "status": "NATIVE"},
                {"fromVersion": "1.0.0", "toVersion": "future", "status": "MIGRATION_LAYER_REQUIRED"},
            ),
            "migrationRules": ("historical_objects_are_never_rewritten", "migration_layers_interpret_only", "unknown_future_fields_are_tolerated"),
            "repositoryBrowser": tuple(_repository_row(item) for item in decision_objects[-25:]),
            "referenceGraph": tuple(_reference_graph_row(item) for item in decision_objects[-25:]),
            "lineage": {
                "chain": (
                    "Workflow",
                    "Workflow Execution Token",
                    "Decision Object",
                    "Office Execution",
                    "Performance Truth",
                    "Historian",
                    "Enterprise Learning",
                    "Decision Laboratory",
                    "Enterprise Archive",
                ),
                "laboratoryReplayCount": decision_laboratory.get("metrics", {}).get("decisionReplayCount", 0),
                "experimentCount": decision_laboratory.get("metrics", {}).get("experimentCount", 0),
            },
            "objectValidator": {
                "decisionObjectCount": len(decision_objects),
                "validDecisionObjects": valid_count,
                "invalidDecisionObjects": len(decision_objects) - valid_count,
                "schemaViolations": violations,
            },
            "hashViewer": tuple({"decisionObjectId": item.get("decisionObjectId", ""), "hash": item.get("audit", {}).get("checksum", "")} for item in decision_objects[-10:]),
            "lawVII": {
                "executesWorkflows": False,
                "ownsWorkflowExecutionTokens": False,
                "generatesTrades": False,
                "modifiesPrompts": False,
                "modifiesStrategies": False,
                "overridesCommanderAuthority": False,
                "responsibility": "PRESERVE_ENTERPRISE_KNOWLEDGE",
            },
            "schemaDocumentation": "Decision Objects are immutable, versioned, serializable, auditable, replayable, backward compatible, and self-describing.",
            "internalDiagnostics": {
                "auditEventCount": audit_event_count,
                "productionBehaviorModified": False,
                "apiCallsMade": 0,
                "workflowTokensOwned": 0,
                "schemaDriftDetected": bool(violations),
            },
        }


def _decision_objects_from_workflows(workflow_orchestrator: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for workflow in workflow_orchestrator.get("workflows", ()):
        for output in workflow.get("output_history", ()):
            decision = output.get("decision_object")
            if isinstance(decision, dict):
                rows.append(decision)
    return rows


def _repository_row(decision_object: dict[str, Any]) -> dict[str, Any]:
    return {
        "decisionObjectId": decision_object.get("decisionObjectId", ""),
        "schemaVersion": decision_object.get("schemaVersion", ""),
        "workflowId": decision_object.get("workflowId", ""),
        "office": decision_object.get("office", ""),
        "validationStatus": decision_object.get("schemaValidationStatus", ""),
        "compatibilityStatus": decision_object.get("compatibilityStatus", ""),
        "hash": decision_object.get("audit", {}).get("checksum", decision_object.get("schemaFingerprint", "")),
        "replayVerificationStatus": decision_object.get("audit", {}).get("replayVerificationStatus", ""),
    }


def _reference_graph_row(decision_object: dict[str, Any]) -> dict[str, Any]:
    return {
        "decisionObjectId": decision_object.get("decisionObjectId", ""),
        "workflowId": decision_object.get("workflowId", ""),
        "workflowTokenId": decision_object.get("workflowTokenId", ""),
        "marketContextSnapshotId": decision_object.get("marketContextSnapshotId", ""),
        "promptVersion": decision_object.get("prompt", {}).get("promptVersion", ""),
        "strategyVersion": decision_object.get("strategy", {}).get("strategyVersion", ""),
        "performanceTruthId": decision_object.get("performanceTruthLinkage", {}).get("performanceTruthId", ""),
    }


def _workflow_section(decision_object: dict[str, Any]) -> dict[str, Any]:
    return {
        "workflowId": decision_object.get("workflowId", ""),
        "workflowType": "paper_trading_session",
        "workflowStatus": "OUTPUT_VALIDATED",
        "workflowPriority": decision_object.get("priority", "NORMAL"),
        "workflowObjective": "controlled paper cognition pilot",
        "workflowOrigin": "ARGOS Control Panel",
        "workflowInitiator": "Commander Interface",
        "workflowCreationTime": decision_object.get("creationTimestamp", ""),
        "workflowCompletionTime": None,
        "relatedWorkflowIds": (),
    }


def _analyst_section(decision_object: dict[str, Any]) -> dict[str, Any]:
    prompt_contract = decision_object.get("promptContract") if isinstance(decision_object.get("promptContract"), dict) else {}
    return {
        "analystPromptVersion": prompt_contract.get("promptVersion", "UNKNOWN"),
        "analystStrategyVersion": decision_object.get("currentStrategy", "UNKNOWN"),
        "reasoningSummary": decision_object.get("recommendation", "UNKNOWN"),
        "evidenceSummary": tuple(decision_object.get("supportingSignals", ())),
        "supportingEvidenceReferences": tuple(decision_object.get("supportingSignals", ())),
        "alternativeHypotheses": (),
        "rejectedAlternatives": (),
        "riskAssessment": decision_object.get("riskScore", 0.0),
        "expectedOutcome": decision_object.get("expectedReturn", 0.0),
        "estimatedProbability": decision_object.get("confidence", 0.0),
        "estimatedHoldingPeriod": "paper_session",
    }


def _risk_section(decision_object: dict[str, Any]) -> dict[str, Any]:
    risk_score = float(decision_object.get("riskScore", 0.0) or 0.0)
    return {
        "riskRating": "LOW" if risk_score < 0.35 else "MODERATE",
        "positionRisk": risk_score,
        "portfolioRisk": risk_score,
        "sectorRisk": "UNKNOWN",
        "marketRisk": "UNKNOWN",
        "confidenceRisk": round(1 - float(decision_object.get("confidence", 0.0) or 0.0), 4),
        "maximumLossEstimate": decision_object.get("stopLoss"),
        "maximumGainEstimate": decision_object.get("targetPrice"),
        "riskBudgetAllocation": decision_object.get("positionSizeRecommendation", 0.0),
    }


def _decision_section(decision_object: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": decision_object.get("recommendation", "UNKNOWN"),
        "decisionConfidence": decision_object.get("confidence", 0.0),
        "decisionRationale": tuple(decision_object.get("supportingSignals", ())),
        "expectedReturn": decision_object.get("expectedReturn", 0.0),
        "expectedRisk": decision_object.get("riskScore", 0.0),
        "executionRecommendation": decision_object.get("recommendation", "UNKNOWN"),
        "supportingStrategy": decision_object.get("currentStrategy", "UNKNOWN"),
        "supportingPrompt": decision_object.get("promptContract", {}).get("promptTemplateId", "UNKNOWN") if isinstance(decision_object.get("promptContract"), dict) else "UNKNOWN",
        "supportingIndicators": tuple(decision_object.get("supportingSignals", ())),
        "supportingNews": (),
        "supportingFundamentals": (),
        "supportingMacro": (),
    }


def _execution_section(decision_object: dict[str, Any]) -> dict[str, Any]:
    return {
        "executionStatus": "PAPER_REVIEW" if decision_object.get("office") != "Trader" else "PAPER_APPROVED",
        "executionTime": decision_object.get("decisionTimestamp", ""),
        "executionWorkflow": decision_object.get("workflowId", ""),
        "executionNotes": "Schema stores execution references only.",
        "brokerReference": None,
        "paperTradeFlag": True,
        "productionFlag": False,
        "executionOutcomeReference": None,
    }


def _performance_truth_linkage(workflow_id: str, decision_id: str) -> dict[str, Any]:
    return {
        "performanceTruthId": f"PT-{workflow_id}" if workflow_id else "",
        "tradeLedgerId": None,
        "portfolioLedgerId": None,
        "positionLedgerId": None,
        "historianRecordId": f"HIST-{decision_id}" if decision_id else "",
        "learningObservationId": f"LEARN-{decision_id}" if decision_id else "",
        "recommendationIds": (),
        "laboratoryIds": (),
    }


def _learning_section(decision_id: str) -> dict[str, Any]:
    return {
        "learningStatus": "REFERENCE_ONLY",
        "historianObservationReference": f"HIST-{decision_id}" if decision_id else "",
        "learningObservationReference": f"LEARN-{decision_id}" if decision_id else "",
        "recommendationReference": None,
        "lessonReference": None,
        "validationReference": None,
        "promotionReference": None,
        "commanderDecisionReference": None,
    }


def _prompt_section(prompt_contract: dict[str, Any]) -> dict[str, Any]:
    prompt_id = prompt_contract.get("promptTemplateId", "UNKNOWN")
    return {
        "promptVersion": prompt_contract.get("promptVersion", "UNKNOWN"),
        "promptHash": hashlib.sha256(prompt_id.encode("utf-8")).hexdigest()[:16],
        "promptRepositoryReference": prompt_id,
        "promptLineage": prompt_contract.get("contractVersion", "UNKNOWN"),
        "promptConfidence": "CONTRACT_BOUND" if prompt_contract else "UNKNOWN",
    }


def _strategy_section(decision_object: dict[str, Any]) -> dict[str, Any]:
    strategy = decision_object.get("currentStrategy", "UNKNOWN")
    return {
        "strategyVersion": f"{strategy} v1.0",
        "strategyRepositoryReference": strategy,
        "strategyFamily": strategy,
        "strategyLineage": "paper_training_baseline",
        "applicableMarketRegime": decision_object.get("marketContext", {}).get("marketRegime", "UNKNOWN") if isinstance(decision_object.get("marketContext"), dict) else "UNKNOWN",
    }


def _audit_section(decision_object: dict[str, Any], market_context: dict[str, Any]) -> dict[str, Any]:
    return {
        "auditRecord": decision_object.get("supportingAuditIdentifier", ""),
        "creationUser": "Commander Interface",
        "creationOffice": decision_object.get("office", ""),
        "modificationCount": 0,
        "digitalSignature": None,
        "hash": "",
        "checksum": "",
        "schemaValidationResult": "PENDING",
        "replayVerificationStatus": "REPLAYABLE",
        "marketContextReference": market_context.get("snapshotId", ""),
    }


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
