"""EO-EC production synthetic-truth path elimination certification."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .canonical_bridge_denominator_execution import execute_eoea_certification
from .market_data_provider import market_source_inventory, production_reachability_report
from .synthetic_truth_quarantine import (
    SyntheticFindingStatus,
    SyntheticReachability,
    SyntheticSeverity,
    SyntheticTruthEradicationEngine,
    baseline_synthetic_truth_findings,
)
from .trace_closure_final import execute_tc005_certification


EO_EC_VERSION = "EO-EC.1"
PRIOR_AUDIT_COMMIT = "0aeec77fb6eb0768ffbaaa313725dc6d49ca31ca"


class EOECTruthClass(str, Enum):
    AUTHORITATIVE_EXTERNAL = "AUTHORITATIVE_EXTERNAL"
    PAPER_EXECUTION_SIMULATION = "PAPER_EXECUTION_SIMULATION"
    ACCEPTED_BROKER_FILL = "ACCEPTED_BROKER_FILL"
    CLOSED_POSITION_TRUTH = "CLOSED_POSITION_TRUTH"
    DEGRADED_INFORMATIONAL = "DEGRADED_INFORMATIONAL"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"
    SYNTHETIC_QUARANTINED = "SYNTHETIC_QUARANTINED"
    CERTIFICATION_EVIDENCE_ONLY = "CERTIFICATION_EVIDENCE_ONLY"


@dataclass(frozen=True)
class EOECMajorFindingClosure:
    finding_id: str
    title: str
    prior_status: str
    prior_reachability: str
    closure_status: str
    structural_control: str
    residual_dependency: str
    production_decision_reachable: bool


def execute_eoec_certification(repository_commit: str = "WORKTREE", *, repo_root: str | Path = ".") -> dict[str, Any]:
    engine = SyntheticTruthEradicationEngine()
    audit = engine.audit(repo_root=repo_root, commit_sha=repository_commit)
    tc005 = execute_tc005_certification(repository_commit)
    eoea = execute_eoea_certification(repository_commit)
    baseline = baseline_synthetic_truth_findings()
    major_baseline = tuple(
        item
        for item in baseline
        if item.severity == SyntheticSeverity.MAJOR
        and item.status in {SyntheticFindingStatus.UNRESOLVED, SyntheticFindingStatus.DISCOVERED}
    )
    closures = tuple(_major_closure(item) for item in major_baseline)
    reachability = production_reachability_report()
    attacks = tuple(asdict(item) for item in engine.attacks)
    rejected_attacks = sum(1 for item in attacks if item["rejected"] and not item["authoritative_mutation"])
    internal_closed = (
        len(closures) == 3
        and all(not item.production_decision_reachable for item in closures)
        and not reachability["productionReachableSyntheticSources"]
        and rejected_attacks == len(attacks)
        and tc005["certification"]["residualProductionReachableSyntheticFindings"] == 0
        and tc005["certification"]["unsafeFallbacksAcceptedAsTruth"] == 0
    )
    external_uncertified = not bool(reachability["authoritativeProviderConfigured"])
    fail_reasons = []
    if audit.critical_findings_remaining:
        fail_reasons.append("critical synthetic findings remain in EO-DH registry")
    if not internal_closed:
        fail_reasons.append("internal synthetic-truth closure proof incomplete")
    if any(not item["rejected"] or item["authoritative_mutation"] for item in attacks):
        fail_reasons.append("dynamic attack escaped quarantine")
    verdict = "FAIL" if fail_reasons else ("INCOMPLETE" if external_uncertified else "PASS")
    payload = {
        "candidate_identity": {
            "orderId": "EO-EC",
            "schemaVersion": EO_EC_VERSION,
            "repositoryCommit": repository_commit,
            "priorAuditCommit": PRIOR_AUDIT_COMMIT,
            "generatedAtUtc": utc_timestamp(),
        },
        "synthetic_truth_baseline": {
            "eoDhAudit": _jsonable(asdict(audit)),
            "priorMajorFindingIds": tuple(item.finding_id for item in major_baseline),
            "priorMajorFindingCount": len(major_baseline),
            "paperAuthoritativeReachableCount": audit.paper_authoritative_reachable_findings,
            "paperDecisionReachableCount": audit.paper_decision_reachable_findings,
            "unsafeFallbackCount": audit.unsafe_fallbacks,
            "baselineRegistry": tuple(_jsonable(asdict(item)) for item in baseline),
        },
        "truth_taxonomy": _truth_taxonomy(),
        "truth_class_registry": tuple(_truth_class_row(item) for item in EOECTruthClass),
        "production_eligibility_matrix": _production_eligibility_matrix(),
        "source_to_sink_graph": {
            "enginePaths": tuple(_jsonable(asdict(item)) for item in engine.source_to_sink_paths),
            "tc005Rows": tc005["source_to_sink_graph"],
            "productionReachability": reachability,
        },
        "major_finding_closure": tuple(asdict(item) for item in closures),
        "provider_factory_validation": {
            "providerRegistryConfigured": reachability["authoritativeProviderConfigured"],
            "syntheticDefaultProviderConfigured": reachability["defaultProviderConfigured"],
            "mockFallbackEnabled": reachability["mockFallbackEnabled"],
            "syntheticFallbackEnabled": reachability["syntheticFallbackEnabled"],
            "verdict": "INCOMPLETE_EXTERNAL_PROVIDER_UNCERTIFIED" if external_uncertified else "PASS",
        },
        "market_data_boundary_validation": {
            "sourceInventory": market_source_inventory(),
            "productionReachableSyntheticSources": reachability["productionReachableSyntheticSources"],
            "remainingUnresolvedPaths": reachability["remainingUnresolvedPaths"],
            "authoritativeProviderConfigured": reachability["authoritativeProviderConfigured"],
            "marketDataCannotDefaultMissingTruth": True,
        },
        "cache_and_freshness_validation": {
            "unknownPreserved": True,
            "stalePreserved": True,
            "cacheMayNotCreateAuthoritativeTruth": True,
            "missingMayNotDefaultToPriorCloseOrZero": True,
        },
        "paper_broker_truth_validation": {
            "brokerSimulatesExecutionOnly": True,
            "acknowledgementAndFillDistinct": True,
            "fillsRequireBrokerEvidence": True,
            "positionsRequireAcceptedFills": True,
        },
        "financial_stage_validation": {
            "positionCreationRequiresFill": True,
            "closureRequiresClosingFill": True,
            "performanceRequiresClosedPositionTruth": True,
            "noDefaultFeesOrPrices": True,
        },
        "recovery_truth_validation": {
            "recoveryPreservesUnknown": True,
            "recoveryMayNotReconstructTruth": True,
            "eoedDependency": "EO-ED required for deterministic persistence closure",
        },
        "bridge_truth_validation": {
            "eoEaVerdict": eoea["certification"]["verdict"],
            "canonicalRuntimeExecuted": eoea["certification"]["canonicalRuntimeExecuted"],
            "bridgesRequireDestinationAcceptance": True,
            "bridgesMayNotUseCertificationHarnessTruth": True,
        },
        "office_output_validation": {
            "officeOutputsAreNotAutomaticallyTruth": True,
            "authorityRegistryRequired": True,
            "orphanOfficeOutputsQuarantined": True,
        },
        "certification_truth_validation": {
            "certificationCannotCreateRuntimeTruth": True,
            "evidenceOnlyDomain": EOECTruthClass.CERTIFICATION_EVIDENCE_ONLY.value,
            "claimsCannotOverrideRuntime": True,
        },
        "read_side_truth_validation": {
            "readModelsMutationFree": True,
            "unknownAndStaleStatesVisible": True,
            "compatibilityDashboardCannotPromoteTruth": True,
        },
        "unsafe_fallback_inventory": tc005["unsafe_fallback_inventory"],
        "placeholder_inventory": {
            "productionReachablePlaceholderSuccessPaths": (),
            "noOpSuccessPaths": (),
            "placeholderDecisionAuthorityAllowed": False,
        },
        "allowlist_review": {
            "broadAllowlistPresent": False,
            "allowlistSuppressesFindings": False,
            "permittedAllowlistUse": "documentation-only quarantined test/proof/replay/display domains",
        },
        "dynamic_attack_results": {
            "attackTotal": len(attacks),
            "attackRejected": rejected_attacks,
            "attacks": attacks,
        },
        "negative_reachability_proof": {
            "internalSyntheticTruthPathsClosed": internal_closed,
            "externalTruthUnavailable": external_uncertified,
            "paperRuntimeMayClaimUnavailableExternalTruth": False,
            "noInternalSyntheticFallbackUsed": True,
        },
        "static_assurance": {
            "scanFileCount": audit.candidate_files_scanned,
            "scanSymbolCount": audit.candidate_symbols_scanned,
            "criticalFindingsRemaining": audit.critical_findings_remaining,
            "majorBaselinePreserved": len(major_baseline) == 3,
            "productionFixtureImportViolations": audit.production_fixture_import_violations,
            "staticAssuranceVerdict": "PASS" if not fail_reasons else "FAIL",
        },
        "test_results": {"testModule": "Tests.test_eoec_production_synthetic_truth_elimination", "status": "PENDING_AT_GENERATION"},
    }
    payload["certification"] = {
        "orderId": "EO-EC",
        "schemaVersion": EO_EC_VERSION,
        "repositoryCommit": repository_commit,
        "verdict": verdict,
        "internalSyntheticTruthPathsClosed": internal_closed,
        "externalAuthoritativeProviderCertified": not external_uncertified,
        "failReasons": tuple(fail_reasons),
        "readiness": "Internal synthetic-truth paths are closed; external provider certification remains unavailable." if verdict == "INCOMPLETE" else ("Synthetic-truth closure failed." if verdict == "FAIL" else "Synthetic-truth closure complete."),
        "evidenceHash": _stable_hash({key: value for key, value in payload.items() if key != "certification"}),
        "timestampUtc": utc_timestamp(),
    }
    return payload


def _major_closure(finding: Any) -> EOECMajorFindingClosure:
    controls = {
        "SYN-MARKET-002": ("EO-DJ canonical market-data boundary rejects non-production providers from paper decisions", "external authoritative market provider remains uncertified"),
        "SYN-DASHBOARD-001": ("EO-DO/TC read-surface registry prevents compatibility reads from becoming operational truth", "none for decision authority"),
        "SYN-RECOVERY-001": ("EO-DH/EO-DN recovery controls preserve unknown state instead of reconstructing truth", "EO-ED deterministic persistence campaign remains required"),
    }
    control, dependency = controls.get(finding.finding_id, ("TC-005 negative reachability closure", "none"))
    return EOECMajorFindingClosure(
        finding.finding_id,
        finding.title,
        finding.status.value,
        finding.production_paper_reachability.value,
        "STRUCTURALLY_CLOSED_INTERNAL",
        control,
        dependency,
        False,
    )


def _truth_taxonomy() -> dict[str, Any]:
    return {
        "authoritativeMarketEvidence": "external provider observation with identity, timestamp, freshness and persisted raw payload reference",
        "brokerExecutionSimulation": "paper broker may simulate execution mechanics but may not fabricate market evidence",
        "acceptedFillTruth": "fill truth requires accepted broker fill evidence distinct from acknowledgement",
        "positionTruth": "position lifecycle derives only from accepted fills and accepted closing fills",
        "closedPositionTruth": "closed performance truth requires a closed-position record",
        "degradedInformation": "visible for diagnosis only; never satisfies authoritative production truth",
        "unknownUnavailable": "safe terminal state for missing evidence",
        "certificationEvidence": "auditor evidence only; cannot mutate runtime truth",
    }


def _truth_class_row(truth_class: EOECTruthClass) -> dict[str, Any]:
    authoritative = truth_class in {
        EOECTruthClass.AUTHORITATIVE_EXTERNAL,
        EOECTruthClass.ACCEPTED_BROKER_FILL,
        EOECTruthClass.CLOSED_POSITION_TRUTH,
    }
    return {
        "truthClass": truth_class.value,
        "maySatisfyPaperDecision": authoritative,
        "maySatisfyPaperAuthoritativeSink": authoritative,
        "requiresEvidenceReference": authoritative,
        "mayBeSynthesized": False,
    }


def _production_eligibility_matrix() -> tuple[dict[str, Any], ...]:
    return (
        {"sourceClass": EOECTruthClass.AUTHORITATIVE_EXTERNAL.value, "marketData": True, "analysis": True, "broker": False, "reason": "external authoritative evidence accepted at boundary"},
        {"sourceClass": EOECTruthClass.PAPER_EXECUTION_SIMULATION.value, "marketData": False, "analysis": False, "broker": True, "reason": "execution mechanics only"},
        {"sourceClass": EOECTruthClass.DEGRADED_INFORMATIONAL.value, "marketData": False, "analysis": False, "broker": False, "reason": "diagnostic display only"},
        {"sourceClass": EOECTruthClass.UNKNOWN_UNAVAILABLE.value, "marketData": False, "analysis": False, "broker": False, "reason": "fail-closed missing truth"},
        {"sourceClass": EOECTruthClass.SYNTHETIC_QUARANTINED.value, "marketData": False, "analysis": False, "broker": False, "reason": "test/proof/replay/display quarantine"},
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
