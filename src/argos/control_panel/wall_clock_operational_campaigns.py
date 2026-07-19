"""EO-EF genuine wall-clock operational campaign gate and evidence model."""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .canonical_bridge_denominator_execution import execute_eoea_certification
from .deterministic_persistence_recovery_closure import execute_eoed_certification
from .full_suite_failure_timeout_elimination import execute_eoee_certification
from .production_synthetic_truth_elimination import execute_eoec_certification


EO_EF_VERSION = "EO-EF.1"


class EOEFCampaignStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"
    PASS = "PASS"
    FAIL = "FAIL"


def execute_eoef_certification(repository_commit: str = "WORKTREE", *, repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root)
    preflight = eoef_preflight(repository_commit, root)
    blocked = tuple(item for item in preflight["gates"] if item["status"] != "PASS")
    campaign_inventory = _campaign_inventory()
    level0 = _blocked_campaign("LEVEL0", 10 * 60, blocked)
    level1 = _blocked_campaign("LEVEL1", 30 * 60, blocked)
    level2a = _blocked_campaign("LEVEL2-A", 2 * 60 * 60, blocked)
    level2b = _blocked_campaign("LEVEL2-B", 2 * 60 * 60, blocked)
    level3 = _blocked_campaign("LEVEL3", 8 * 60 * 60, blocked)
    fail_reasons = tuple(item["gateId"] for item in blocked if item["severity"] == "FAIL")
    verdict = "FAIL" if fail_reasons else "INCOMPLETE"
    payload = {
        "campaign_inventory": campaign_inventory,
        "preflight": preflight,
        "level0": level0,
        "level1": level1,
        "level2_campaign_a": level2a,
        "level2_campaign_b": level2b,
        "level3": level3,
        "runtime_lineage": {"campaignsUseCanonicalRuntime": True, "campaignCodeMayNotCreateAuthority": True, "startedCampaignIds": ()},
        "checkpoint_index": {"checkpointCount": 0, "unexplainedGaps": (), "reason": "preflight blocked launch"},
        "constitutional_invariants": {"violations": (), "notEvaluatedReason": "no long-duration campaign launched"},
        "resource_timeseries": {"samples": (), "notEvaluatedReason": "no long-duration campaign launched"},
        "bridge_statistics": {"samples": (), "notEvaluatedReason": "no long-duration campaign launched"},
        "office_statistics": {"samples": (), "notEvaluatedReason": "no long-duration campaign launched"},
        "financial_statistics": {"samples": (), "notEvaluatedReason": "no long-duration campaign launched"},
        "read_purity": {"readMutationDetected": False, "notEvaluatedReason": "no long-duration campaign launched"},
        "restart_campaign": {"status": EOEFCampaignStatus.PREFLIGHT_BLOCKED.value, "deterministicRestartRequired": True},
        "failure_injection": {"status": EOEFCampaignStatus.PREFLIGHT_BLOCKED.value, "failuresInjected": 0},
        "recovery_validation": {"status": EOEFCampaignStatus.PREFLIGHT_BLOCKED.value, "recoveryFabricatedTruth": False},
        "cost_analysis": {"estimatedCostUsd": 0.0, "campaignsLaunched": 0},
        "reproducibility": {"level2CampaignsMateriallyIdentical": False, "reason": "two Level 2 campaigns not executed"},
        "static_assurance": {"acceleratedEvidenceLabeledAsLevel2Or3": False, "elapsedDurationMayNotBeInferred": True},
        "test_results": {"testModule": "Tests.test_eoef_wall_clock_operational_campaigns", "status": "PENDING_AT_GENERATION"},
    }
    payload["certification"] = {
        "orderId": "EO-EF",
        "schemaVersion": EO_EF_VERSION,
        "repositoryCommit": repository_commit,
        "verdict": verdict,
        "preflightPassed": not blocked,
        "level2CampaignsPassed": 0,
        "level3CampaignsPassed": 0,
        "failReasons": fail_reasons,
        "readiness": "Level 2/3 launch is preflight-blocked; no wall-clock certification is claimed.",
        "evidenceHash": _stable_hash({key: value for key, value in payload.items() if key != "certification"}),
        "timestampUtc": utc_timestamp(),
    }
    return payload


def eoef_preflight(repository_commit: str, repo_root: Path) -> dict[str, Any]:
    eoea = execute_eoea_certification(repository_commit)["certification"]
    eoec = execute_eoec_certification(repository_commit, repo_root=repo_root)["certification"]
    eoed = execute_eoed_certification(repository_commit)["certification"]
    eoee = execute_eoee_certification(repository_commit, repo_root=repo_root)["certification"]
    gates = (
        _gate("EO-EA", eoea["verdict"] != "FAIL", eoea["verdict"]),
        _gate("EO-EC", eoec["verdict"] != "FAIL", eoec["verdict"]),
        _gate("EO-ED", eoed["verdict"] != "FAIL", eoed["verdict"]),
        _gate("EO-EE", eoee["verdict"] != "FAIL", eoee["verdict"], severity="FAIL"),
        _gate("DETERMINISTIC_RESTART", eoed.get("deterministicRestartVerdict") == "PASS", eoed.get("deterministicRestartVerdict", "")),
        _gate("BOUNDED_INTERNAL_SUITE", eoee["verdict"] != "FAIL", eoee["verdict"], severity="FAIL"),
    )
    return {"repositoryCommit": repository_commit, "preflightPassed": all(item["status"] == "PASS" for item in gates), "gates": gates}


def _gate(gate_id: str, passed: bool, evidence: str, *, severity: str = "BLOCK") -> dict[str, str]:
    return {"gateId": gate_id, "status": "PASS" if passed else "BLOCKED", "evidence": evidence, "severity": severity}


def _campaign_inventory() -> tuple[dict[str, Any], ...]:
    return (
        {"level": "LEVEL0", "minimumElapsedSeconds": 600, "certifying": False},
        {"level": "LEVEL1", "minimumElapsedSeconds": 1800, "certifying": False},
        {"level": "LEVEL2-A", "minimumElapsedSeconds": 7200, "certifying": True},
        {"level": "LEVEL2-B", "minimumElapsedSeconds": 7200, "certifying": True},
        {"level": "LEVEL3", "minimumElapsedSeconds": 28800, "certifying": True},
    )


def _blocked_campaign(campaign_id: str, duration: int, blockers: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    return {
        "campaignId": campaign_id,
        "minimumElapsedSeconds": duration,
        "status": EOEFCampaignStatus.PREFLIGHT_BLOCKED.value if blockers else EOEFCampaignStatus.NOT_STARTED.value,
        "realElapsedSeconds": 0,
        "usesAcceleratedClock": False,
        "blockers": tuple(item["gateId"] for item in blockers),
    }


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
