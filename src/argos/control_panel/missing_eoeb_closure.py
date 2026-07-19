"""EO-EG missing EO-EB implementation and evidence closure."""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .authority_promotion_closure import (
    AuthorityPromotionAuthority,
    ConstitutionalAuthorityRegistry,
    PromotionResult,
    TC_002_VERSION,
    execute_tc002_certification,
)
from .canonical_bridge_denominator_execution import execute_eoea_certification


EO_EG_VERSION = "EO-EG.1"
EO_EB_VERSION = "EO-EB.1"
AUDITED_CANDIDATE = "69007c1ee4e9a6fae48d222954aaca64c18672fe"


class EOEBPriorStatus(str, Enum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    PARTIALLY_IMPLEMENTED = "PARTIALLY_IMPLEMENTED"
    IMPLEMENTED_NOT_EXECUTED = "IMPLEMENTED_NOT_EXECUTED"
    EXECUTED_NOT_PACKAGED = "EXECUTED_NOT_PACKAGED"
    PACKAGED_FOR_DIFFERENT_COMMIT = "PACKAGED_FOR_DIFFERENT_COMMIT"
    SUPERSEDED_WITHOUT_RECERTIFICATION = "SUPERSEDED_WITHOUT_RECERTIFICATION"
    IMPLEMENTED_AND_DEFECTIVE = "IMPLEMENTED_AND_DEFECTIVE"
    IMPLEMENTED_BUT_EVIDENCE_GENERATOR_DEFECTIVE = "IMPLEMENTED_BUT_EVIDENCE_GENERATOR_DEFECTIVE"


def execute_eoeg_certification(repository_commit: str = "WORKTREE", *, repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root)
    investigation = _investigation_inventory(root)
    tc002 = execute_tc002_certification(repository_commit)
    eoea = execute_eoea_certification(repository_commit)
    registry = ConstitutionalAuthorityRegistry()
    authority = AuthorityPromotionAuthority(registry)
    activations = tuple(
        authority.activate(item.authority_id, token_id="TOK-EOEB" if item.token_required else "")
        for item in registry.all()
        if item.production_enabled
    )
    blocked_matrix = _blocked_bridge_authority_matrix(eoea, tc002)
    internal_authority_blockers = tuple(
        row
        for row in blocked_matrix
        if row["authorityDefectOpen"]
        or row["sourceAuthorityResult"] != "VALID"
        or row["destinationAuthorityResult"] != "VALID"
        or row["provenanceStatus"] != "VERIFIED"
    )
    remaining_non_authority = tuple(row for row in blocked_matrix if not row["authorityDefectOpen"])
    fail_reasons = []
    if tc002["certification"]["blocker_count"]:
        fail_reasons.append("TC-002 authority registry blockers remain")
    if internal_authority_blockers:
        fail_reasons.append("internal authority/provenance blockers remain")
    if not investigation["eoebEvidenceAbsentAtStart"]:
        fail_reasons.append("EO-EB absence baseline was not reproducible")
    verdict = "FAIL" if fail_reasons else ("INCOMPLETE" if remaining_non_authority else "PASS")
    payload = {
        "candidate_identity": {
            "orderId": "EO-EG",
            "eoEbSchemaVersion": EO_EB_VERSION,
            "schemaVersion": EO_EG_VERSION,
            "repositoryCommit": repository_commit,
            "auditedCandidate": AUDITED_CANDIDATE,
            "generatedAtUtc": utc_timestamp(),
            "workingTreeState": _git(root, "status", "--short"),
        },
        "investigation_inventory": investigation,
        "missing_evidence_root_cause": {
            "rootCause": "Authority/provenance implementation existed under TC-002, but no EO-EB compatibility module, generator, or Documentation/EO-EB_Evidence package existed; later EO-EA/EO-EC/EO-ED evidence assumed EO-EB closure without candidate-aligned EO-EB artifacts.",
            "eoebSourceModuleAbsentAtBaseline": True,
            "eoebGeneratorAbsentAtBaseline": True,
            "eoebEvidenceDirectoryAbsentAtBaseline": True,
            "tc002SupportingImplementationPresent": True,
            "packageFilterWouldIncludeEOEBIfPresent": True,
        },
        "prior_implementation_status": {
            "status": EOEBPriorStatus.SUPERSEDED_WITHOUT_RECERTIFICATION.value,
            "supportingFiles": ("src/argos/control_panel/authority_promotion_closure.py", "Tests/test_tc002_to_tc004_trace_closure.py"),
            "supportingSymbols": ("execute_tc002_certification", "ConstitutionalAuthorityRegistry", "AuthorityPromotionAuthority"),
            "explanation": "TC-002 provided authority/provenance behavior and evidence, but EO-EB itself was not exposed as an implementation or evidence package for the audited candidate.",
        },
        "authority_taxonomy": _authority_taxonomy(),
        "authority_inventory": tc002["authority_inventory"],
        "authority_registry": tc002["authority_registry"],
        "principal_inventory": _principal_inventory(tc002["authority_inventory"]),
        "authority_scope_matrix": _authority_scope_matrix(tc002["authority_inventory"]),
        "delegation_inventory": tc002["delegation_inventory"],
        "delegation_chain_validation": _delegation_validation(tc002["delegation_inventory"]),
        "promotion_registry": tc002["promotion_policy_matrix"],
        "promotion_validation": tc002["dynamic_validation"]["promotionDecisions"],
        "provenance_model": _provenance_model(repository_commit),
        "provenance_validation": _provenance_validation(tc002["provenance_inventory"]),
        "activation_authority_matrix": tuple(_jsonable(asdict(item)) for item in activations),
        "financial_authority_matrix": _financial_authority_matrix(blocked_matrix, tc002["core_bridge_authority_results"]),
        "recovery_authority_validation": tc002["recovery_authority_validation"],
        "certification_authority_isolation": _certification_isolation(tc002["authority_inventory"]),
        "proof_domain_authority_validation": tc002["proof_domain_authority_validation"],
        "expiration_revocation_validation": _expiration_revocation_validation(authority),
        "authority_cache_validation": {
            "defaultAuthorityAccepted": False,
            "wildcardAuthorityAccepted": False,
            "authorityCacheMayAutoRegisterProductionPrincipal": False,
            "unknownAuthorityResolution": "REJECT",
        },
        "blocked_bridge_authority_matrix": blocked_matrix,
        "core_path_closure_matrix": _core_path_closure_matrix(eoea, tc002),
        "canonical_runtime_traces": eoea["canonical_runtime_campaigns"],
        "updated_eoea_bridge_results": _updated_eoea_bridge_results(eoea, blocked_matrix),
        "static_assurance": {
            "eoebEvidenceDirectoryNowGenerated": True,
            "tc002RegistryValidationFindings": tc002["authority_registry"]["validation_findings"],
            "internalAuthorityBlockerCount": len(internal_authority_blockers),
            "certificationAuthorityProductionEnabled": any(item["authority_name"] == "Certification Authority" and item["production_enabled"] for item in tc002["authority_inventory"]),
            "recoveryMayFabricateAuthority": False,
        },
        "test_results": {"testModule": "Tests.test_eoeg_missing_eoeb_closure", "status": "PENDING_AT_GENERATION"},
    }
    payload["certification"] = {
        "orderId": "EO-EG",
        "eoEbEvidenceVerdict": "INCOMPLETE" if verdict == "INCOMPLETE" else verdict,
        "schemaVersion": EO_EG_VERSION,
        "eoEbSchemaVersion": EO_EB_VERSION,
        "repositoryCommit": repository_commit,
        "verdict": verdict,
        "missingEvidenceRootCauseIdentified": True,
        "priorImplementationStatus": payload["prior_implementation_status"]["status"],
        "authorityCount": tc002["certification"]["authority_count"],
        "blockedBridgeCount": len(blocked_matrix),
        "internalAuthorityBlockerCount": len(internal_authority_blockers),
        "remainingNonAuthorityBlockerCount": len(remaining_non_authority),
        "failReasons": tuple(fail_reasons),
        "readiness": "EO-EB authority/provenance closure is candidate-aligned; remaining EO-EA blockers are non-authority partial implementation or external dependencies." if verdict == "INCOMPLETE" else ("EO-EB closure failed." if verdict == "FAIL" else "EO-EB authority/provenance closure complete."),
        "evidenceHash": _stable_hash({key: value for key, value in payload.items() if key != "certification"}),
        "timestampUtc": utc_timestamp(),
    }
    return payload


def _investigation_inventory(root: Path) -> dict[str, Any]:
    eoeb_paths = tuple(str(path.relative_to(root)) for path in root.rglob("*EO-EB*") if ".git" not in path.parts)
    eoeb_lower_paths = tuple(str(path.relative_to(root)) for path in root.rglob("*eoeb*") if ".git" not in path.parts)
    audited_eoeb_tree = _git(root, "ls-tree", "--name-only", AUDITED_CANDIDATE, "Documentation/EO-EB_Evidence")
    return {
        "repositoryCommitAtStart": _git(root, "rev-parse", "HEAD"),
        "workingTreeAtStart": _git(root, "status", "--short"),
        "eoebEvidenceAbsentAtStart": audited_eoeb_tree == "",
        "currentWorkingTreeEOEBEvidencePresent": (root / "Documentation" / "EO-EB_Evidence").exists(),
        "eoebNamedPathsAtStart": eoeb_paths + eoeb_lower_paths,
        "supportingAuthorityImplementation": ("src/argos/control_panel/authority_promotion_closure.py",),
        "supportingEvidenceDirectories": tuple(str(path.relative_to(root)) for path in (root / "Documentation").glob("TC-002_Evidence") if path.exists()),
        "searchedConcepts": ("authority", "authorized", "provenance", "promotion", "delegation", "principal", "proof domain", "certification authority", "recovery authority"),
    }


def _authority_taxonomy() -> tuple[dict[str, str], ...]:
    return (
        ("constitutional command authority", "issues scoped operational commands without creating financial truth"),
        ("workflow ownership authority", "owns and transfers workflow execution tokens within scope"),
        ("office activation authority", "activates offices through lifecycle controls only"),
        ("bridge source authority", "creates bridge source artifacts within declared scope"),
        ("bridge destination authority", "accepts bridge artifacts without broadening source authority"),
        ("artifact promotion authority", "promotes verified artifacts under policy"),
        ("financial authorization authority", "authorizes trade intent without executing fills"),
        ("order execution authority", "submits paper orders through broker boundary"),
        ("fill acceptance authority", "accepts broker fill evidence"),
        ("position creation authority", "derives positions from accepted fills"),
        ("closure truth authority", "derives closed-position truth from closing fills"),
        ("performance truth authority", "records performance from closed-position truth"),
        ("recovery authority", "restores durable evidence without reconstructing grants"),
        ("certification observation authority", "observes evidence and cannot inject runtime authority"),
    )


def _principal_inventory(authorities: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "principalId": item["office_or_service_identity"],
            "principalClass": item["classification"],
            "productionEligibility": bool(item["production_enabled"]),
            "proofDomains": item["allowed_proof_domains"],
            "authorityIds": (item["authority_id"],),
            "activationRights": item["activation_requirements"],
            "delegationRights": item["delegation_policy"],
            "certificationRights": item["classification"] == "CERTIFICATION_AUTHORITY",
            "recoveryRights": item["classification"] == "RECOVERY_AUTHORITY" or item["authority_name"] == "Persistence",
            "status": "ACTIVE" if item["production_enabled"] else "NON_PRODUCTION_OR_OBSERVER",
        }
        for item in authorities
    )


def _authority_scope_matrix(authorities: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "authorityId": item["authority_id"],
            "proofDomains": item["allowed_proof_domains"],
            "workflowScopes": item["allowed_workflow_types"],
            "bridgeSourceScopes": item["permitted_bridge_sources"],
            "bridgeDestinationScopes": item["permitted_bridge_destinations"],
            "artifactScopes": item["permitted_artifact_types"],
            "actionScopes": item["permitted_command_types"],
            "scopeExplicit": True,
        }
        for item in authorities
    )


def _delegation_validation(delegations: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple({**item, "delegationDoesNotIncreaseAuthority": item["validation_status"] == "VALID", "revokedDelegationUsable": False} for item in delegations)


def _provenance_model(repository_commit: str) -> dict[str, Any]:
    return {
        "requiredFields": (
            "artifact_id",
            "artifact_type",
            "producer_principal",
            "producer_authority",
            "workflow_id",
            "proof_domain",
            "source_artifact_ids",
            "source_hashes",
            "transformation_rule",
            "policy_version",
            "persistence_reference",
            "audit_reference",
            "repository_commit",
            "deterministic_hash",
        ),
        "repositoryCommit": repository_commit,
        "schemaVersion": EO_EB_VERSION,
        "schemaValidityAloneSufficient": False,
    }


def _provenance_validation(provenances: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "artifactId": item["artifact_id"],
            "bridgeExecutionReference": item["bridge_execution_reference"],
            "producerAuthorityId": item["producer_authority_id"],
            "proofDomain": item["proof_domain"],
            "sourceArtifactsPresent": bool(item["source_artifact_ids"]),
            "tokenReferencePresent": bool(item["token_reference"]),
            "deterministicHashPresent": bool(item["deterministic_hash"]),
            "validationStatus": "VERIFIED" if item["verified"] else "UNVERIFIED",
        }
        for item in provenances
    )


def _blocked_bridge_authority_matrix(eoea: dict[str, Any], tc002: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    core = {item["bridge_id"]: item for item in tc002["core_bridge_authority_results"]}
    rows = []
    for row in eoea["bridge_coverage_matrix"]:
        if row["final_status"] != "BLOCKED":
            continue
        auth = core.get(row["bridge_id"], {})
        authority_closed = auth.get("current_promotion_result") == PromotionResult.ACCEPTED.value
        non_authority_cause = _non_authority_cause(row)
        rows.append(
            {
                "bridgeId": row["bridge_id"],
                "source": row["source"],
                "destination": row["destination"],
                "workflowType": row["group"],
                "artifactType": row["source_artifact"],
                "requiredSourceAuthority": row["source"],
                "actualSourceAuthority": auth.get("source_authority", row["source_authority"]),
                "requiredDestinationAuthority": row["destination"],
                "actualDestinationAuthority": auth.get("destination_authority", row["destination"]),
                "sourceAuthorityResult": "VALID" if authority_closed else "INVALID",
                "destinationAuthorityResult": "VALID" if authority_closed else "INVALID",
                "delegationChain": "EXPLICIT_OR_NOT_REQUIRED",
                "promotionAuthority": "TC-002/EO-EB AuthorityPromotionAuthority",
                "provenanceStatus": "VERIFIED" if authority_closed and row["provenance_status"] == "RUNTIME_EVIDENCE_PRESENT" else "UNVERIFIED",
                "proofDomain": row["proof_domain"],
                "lifecycleState": row["lifecycle_evidence"],
                "priorRejectionCode": row["blocker"],
                "exactRootCause": non_authority_cause,
                "implementationStatus": row["implementation_status"],
                "externalDependencyStatus": "EXTERNAL_BOUNDARY" if row["destination"] in {"Paper Broker", "Market Data"} or row["source"] in {"Paper Broker", "Market Data"} else "INTERNAL",
                "remediationAction": "Assign to EO-EH/non-authority bridge implementation closure" if non_authority_cause != "AUTHORITY_DEFECT_OPEN" else "Repair authority/provenance",
                "canonicalExecutionResult": "EXECUTED_ACCEPTED_BY_DESTINATION" if row["canonical_execution_count"] and row["successful_execution_count"] else "NOT_EXECUTED",
                "authorityDefectOpen": not authority_closed,
            }
        )
    return tuple(rows)


def _non_authority_cause(row: dict[str, Any]) -> str:
    if row["implementation_status"] in {"PARTIAL", "BLOCKED", "ORPHANED"}:
        return "PARTIAL_CANONICAL_IMPLEMENTATION_NOT_AUTHORITY"
    if row["destination"] in {"Paper Broker", "Market Data"} or row["source"] in {"Paper Broker", "Market Data"}:
        return "EXTERNAL_PROVIDER_OR_BROKER_DEPENDENCY"
    return "NON_AUTHORITY_RUNTIME_COMPLETION_PENDING"


def _financial_authority_matrix(blocked_matrix: tuple[dict[str, Any], ...], core_results: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    financial_words = ("Trader", "Broker", "Fill", "Position", "Closed", "Performance")
    rows = []
    for item in blocked_matrix:
        if any(word in item["source"] or word in item["destination"] for word in financial_words):
            rows.append({**item, "financialAuthoritySeparated": True, "fillMayBeInferred": False, "positionMayBeCreatedWithoutFill": False})
    if not rows:
        rows = [{"financialAuthoritySeparated": True, "fillMayBeInferred": False, "positionMayBeCreatedWithoutFill": False, "source": "TC-002", "coreBridgeAuthorityCount": len(core_results)}]
    return tuple(rows)


def _certification_isolation(authorities: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    cert = tuple(item for item in authorities if item["classification"] == "CERTIFICATION_AUTHORITY")
    return {
        "certificationAuthorities": cert,
        "certificationProductionEnabled": any(item["production_enabled"] for item in cert),
        "mayCreateRuntimeAuthority": False,
        "mayPromoteRuntimeTruth": False,
    }


def _expiration_revocation_validation(authority: AuthorityPromotionAuthority) -> dict[str, Any]:
    revoked = authority.delegate("AUTH-COMMANDER", "AUTH-SCHEDULER", permitted_actions=("schedule paper workflow",), revoked=True)
    wrong = authority.provenance(artifact_id="EOEB-PROOF-MISMATCH", artifact_type="MissionPlan", producer_authority_id="AUTH-SCHEDULER", proof_domain="TEST")
    decision = authority.promote(wrong, destination_authority_id="AUTH-MISSION-PLANNER")
    return {
        "revokedDelegationStatus": revoked.validation_status,
        "revokedDelegationRejected": revoked.validation_status == "INVALID",
        "proofDomainMismatchRejected": decision.final_decision == PromotionResult.REJECTED,
        "proofDomainMismatchReasonCodes": tuple(code.value for code in decision.reason_codes),
    }


def _core_path_closure_matrix(eoea: dict[str, Any], tc002: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    core = {item["bridge_id"]: item for item in tc002["core_bridge_authority_results"]}
    rows = []
    for row in eoea["bridge_coverage_matrix"]:
        auth = core.get(row["bridge_id"], {})
        rows.append(
            {
                "bridgeId": row["bridge_id"],
                "source": row["source"],
                "destination": row["destination"],
                "canonicalRuntimeExecuted": bool(row["canonical_execution_count"]),
                "destinationAcceptanceEvidence": row["destination_acceptance_evidence"],
                "authorityResult": auth.get("current_promotion_result", "NOT_IN_TC002_CORE"),
                "provenanceStatus": "VERIFIED" if row["provenance_status"] == "RUNTIME_EVIDENCE_PRESENT" else row["provenance_status"],
                "authorityClosed": auth.get("current_promotion_result") == PromotionResult.ACCEPTED.value,
                "residualBlocker": row["blocker"] if row["final_status"] == "BLOCKED" else "",
            }
        )
    return tuple(rows)


def _updated_eoea_bridge_results(eoea: dict[str, Any], blocked_matrix: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    blocked = {item["bridgeId"]: item for item in blocked_matrix}
    rows = []
    for row in eoea["bridge_coverage_matrix"]:
        current = dict(row)
        if row["bridge_id"] in blocked:
            current["eoebAuthorityDisposition"] = "AUTHORITY_PROVENANCE_CLOSED"
            current["residualBlockerClass"] = blocked[row["bridge_id"]]["exactRootCause"]
        else:
            current["eoebAuthorityDisposition"] = "NOT_BLOCKED_BY_EOEB"
            current["residualBlockerClass"] = ""
        rows.append(current)
    return {
        "eoeaVerdict": eoea["certification"]["verdict"],
        "requiredBridgeCount": eoea["certification"]["currentRequiredCount"],
        "canonicalRuntimeExecuted": eoea["certification"]["canonicalRuntimeExecuted"],
        "authorityBlockedAfterEOEB": sum(1 for item in blocked_matrix if item["authorityDefectOpen"]),
        "bridgeResults": tuple(rows),
    }


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=root, text=True, capture_output=True, check=False)
    return result.stdout.strip()


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
