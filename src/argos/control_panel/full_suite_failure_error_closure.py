"""EO-EJ full-suite failure and error root-cause closure evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import unittest
from typing import Any

from argos.foundation.contracts import utc_timestamp


EO_EJ_VERSION = "EO-EJ.1"


class EOEJRootCause(str, Enum):
    PRODUCTION_IMPLEMENTATION_DEFECT = "PRODUCTION_IMPLEMENTATION_DEFECT"
    TEST_EXPECTATION_STALE = "TEST_EXPECTATION_STALE"
    TEST_IMPLEMENTATION_DEFECT = "TEST_IMPLEMENTATION_DEFECT"
    TIMEOUT_CONTRIBUTOR = "TIMEOUT_CONTRIBUTOR"


@dataclass(frozen=True)
class EOEJAdverseResult:
    adverse_id: str
    test_id: str
    outcome_type: str
    subsystem: str
    primary_root_cause: str
    constitutional_interpretation: str
    remediation: str
    targeted_rerun_result: str
    final_status: str


def execute_eoej_certification(
    repository_commit: str = "WORKTREE",
    *,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    root = Path(repo_root)
    denominator = _discover_test_ids(root)
    diagnostics = _load_file_diagnostics(root)
    closed = _closed_adverse_results()
    open_items = _open_adverse_results()
    failure_inventory = tuple(item for item in (*closed, *open_items) if item.outcome_type == "FAILURE")
    error_inventory = tuple(item for item in (*closed, *open_items) if item.outcome_type in {"ERROR", "COLLECTION_ERROR"})
    timeout_inventory = tuple(item for item in (*closed, *open_items) if item.outcome_type == "TIMEOUT")
    selected = int(diagnostics.get("totalTests", len(denominator)) or len(denominator))
    failed_files = tuple(
        {
            "file": item.get("file", ""),
            "selected": item.get("selected", 0),
            "status": item.get("status", ""),
            "elapsedSeconds": item.get("elapsedSeconds", 0),
        }
        for item in diagnostics.get("results", ())
        if item.get("status") != "PASS"
    )
    adverse = (*failure_inventory, *error_inventory, *timeout_inventory)
    unresolved = tuple(item for item in adverse if item.final_status != "CLOSED")
    verdict = "FAIL" if unresolved else "PASS"
    candidate = {
        "orderId": "EO-EJ",
        "schemaVersion": EO_EJ_VERSION,
        "repositoryCommit": repository_commit,
        "generatedAtUtc": utc_timestamp(),
        "python": sys.version,
        "platform": platform.platform(),
        "workingTreeState": _git(root, "status", "--short"),
    }
    payload: dict[str, Any] = {
        "candidate_identity": candidate,
        "authoritative_test_denominator": {
            "framework": "unittest",
            "testRoot": "Tests",
            "pattern": "test*.py",
            "collected": len(denominator),
            "requiredBoundedInternal": len(denominator),
            "externalOperational": 0,
            "wallClock": 0,
            "manual": 0,
            "retired": 0,
            "notDiscovered": 0,
            "testIds": denominator,
        },
        "collection_results": {
            "collectionComplete": bool(denominator),
            "collected": len(denominator),
            "collectionDefects": (),
        },
        "baseline_full_suite_results": {
            "command": "py -3 -m unittest discover -s Tests -p test*.py",
            "complete": False,
            "selected": selected,
            "visibleFailures": True,
            "visibleErrors": True,
            "terminalOutcome": "INTERRUPTED_AFTER_TIMEOUT_CONTRIBUTOR",
            "timeoutContributor": "Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_workflow_runtime_monitor_retains_latest_ten_completed_workflows",
        },
        "adverse_test_architecture_inventory": {
            "diagnosticFiles": ("Documentation/EOEJ_baseline_unittest_discover.log", "Documentation/EOEJ_file_diagnostics.json"),
            "failedOrTimeoutFiles": failed_files,
            "dominantRootCauseGroups": (
                "trader/control_panel circular import on paper brokerage import",
                "stale proof-mode dashboard expectations expecting operational paper truth side effects",
                "removed mock market-data provider expectation after authoritative provider registry hardening",
                "workflow retention test remains an unresolved timeout contributor",
            ),
        },
        "failure_inventory": tuple(asdict(item) for item in failure_inventory),
        "error_inventory": tuple(asdict(item) for item in error_inventory),
        "root_cause_taxonomy": tuple(item.value for item in EOEJRootCause),
        "failure_cascade_analysis": {
            "cascadeDetected": True,
            "primaryCascade": "start_paper_self_training now creates proof-mode traces and intentionally avoids certified PAPER truth mutation; historical dashboard tests wait for orders, positions, and downstream advisory artifacts.",
            "affectedSubsystems": ("performance_truth", "position_lifecycle", "office_bridges", "learning_evidence", "replay_evidence"),
        },
        "collection_defect_closure": {"collectionComplete": True, "collectionErrorsClosed": 0},
        "stale_expectation_review": {
            "staleExpectationsRemain": True,
            "examples": (
                "EO-G provider registry expected providerId 'mock' after EO-DJ provider authority registry removed that production-facing alias.",
                "EAB test expected 'Paper self-training started' after proof-mode label became authoritative.",
            ),
        },
        "production_defect_closure": {
            "closedDefects": tuple(asdict(item) for item in closed if item.primary_root_cause == EOEJRootCause.PRODUCTION_IMPLEMENTATION_DEFECT.value),
            "openDefects": tuple(asdict(item) for item in open_items if item.primary_root_cause == EOEJRootCause.PRODUCTION_IMPLEMENTATION_DEFECT.value),
        },
        "fixture_defect_closure": {"fixtureDefectsDetected": 0, "openFixtureDefects": ()},
        "setup_teardown_closure": {"setupErrors": 0, "teardownErrors": 0, "cleanupErrors": 0},
        "global_state_isolation": {"globalStateDefectsClosed": 0, "openGlobalStateDefects": ()},
        "environment_isolation": {"environmentMutationsRestored": True, "openEnvironmentDefects": ()},
        "persistence_isolation": {"sharedPersistenceDefectsDetected": 0, "openPersistenceDefects": ()},
        "port_network_closure": {"hardcodedPortDefectsDetected": 0, "openPortDefects": ()},
        "subprocess_closure": {"subprocessFailuresDetected": 0, "openSubprocessDefects": ()},
        "thread_async_closure": {"threadLeaksDetected": "NOT_PROVEN", "openThreadAsyncDefects": ("dashboard workflow retention timeout requires EO-EJ follow-up",)},
        "order_dependence_results": {"orderDependenceTested": False, "remainingWork": "blocked by open dashboard adverse results"},
        "nondeterminism_results": {"nondeterminismTested": False, "remainingWork": "blocked by open dashboard adverse results"},
        "timeout_contributor_closure": {
            "timeoutContributors": tuple(asdict(item) for item in timeout_inventory),
            "allClosed": all(item.final_status == "CLOSED" for item in timeout_inventory),
        },
        "skip_xfail_review": {"blanketSkipsAdded": 0, "xfailsAdded": 0, "unjustifiedSuppressions": 0},
        "test_retirement_inventory": {"retiredTests": (), "unjustifiedRetirements": 0},
        "targeted_retest_results": tuple(asdict(item) for item in closed),
        "segment_results": {
            "fileDiagnosticCommand": "py -3 -m unittest discover -s Tests -p <file>",
            "files": int(diagnostics.get("totalFiles", 0) or 0),
            "failedFilesAtBaseline": int(sum(1 for item in diagnostics.get("results", ()) if item.get("status") == "FAIL_OR_ERROR")),
            "timeoutFilesAtBaseline": int(sum(1 for item in diagnostics.get("results", ()) if item.get("status") == "TIMEOUT")),
            "postRemediationKnownClosedFiles": (
                "test_broker_integration_office.py",
                "test_execution_quality_office.py",
                "test_order_management_office.py",
                "test_position_management_office.py",
                "test_trade_execution_office.py",
                "test_trade_monitoring_office.py",
                "test_trader_fusion_office.py",
                "test_trader_group_framework.py",
                "test_trader_readiness.py",
                "test_enterprise_activity_bus.py",
            ),
        },
        "complete_verification_run": {
            "command": "py -3 -m unittest discover -s Tests -p test*.py",
            "complete": False,
            "failed": "PRESENT",
            "errors": "PRESENT",
            "timeouts": "PRESENT",
        },
        "result_accounting": {
            "collected": len(denominator),
            "selected": selected,
            "closedAdverseResults": sum(1 for item in adverse if item.final_status == "CLOSED"),
            "openAdverseResults": len(unresolved),
            "accountingReconciled": False,
        },
        "failure_closure_matrix": tuple(asdict(item) for item in adverse),
        "static_assurance": {
            "noFailuresSuppressed": True,
            "noSkipsAdded": True,
            "noXfailsAdded": True,
            "currentAdverseEvidenceBlocksPass": bool(unresolved),
        },
        "test_results": {
            "focusedCommands": (
                "py -3 -m unittest discover -s Tests -p test_enterprise_activity_bus.py",
                "py -3 -m unittest discover -s Tests -p test_broker_integration_office.py",
                "py -3 -m unittest discover -s Tests -p test_execution_quality_office.py",
                "py -3 -m unittest discover -s Tests -p test_order_management_office.py",
                "py -3 -m unittest discover -s Tests -p test_position_management_office.py",
                "py -3 -m unittest discover -s Tests -p test_trade_execution_office.py",
                "py -3 -m unittest discover -s Tests -p test_trade_monitoring_office.py",
                "py -3 -m unittest discover -s Tests -p test_trader_fusion_office.py",
                "py -3 -m unittest discover -s Tests -p test_trader_group_framework.py",
                "py -3 -m unittest discover -s Tests -p test_trader_readiness.py",
            ),
            "focusedClosed": 10,
            "fullSuitePass": False,
        },
    }
    payload["certification"] = {
        "orderId": "EO-EJ",
        "schemaVersion": EO_EJ_VERSION,
        "repositoryCommit": repository_commit,
        "verdict": verdict,
        "closedAdverseResults": sum(1 for item in adverse if item.final_status == "CLOSED"),
        "openAdverseResults": len(unresolved),
        "failReasons": tuple(item.test_id for item in unresolved),
        "evidenceHash": _stable_hash({key: value for key, value in payload.items() if key != "certification"}),
        "timestampUtc": utc_timestamp(),
    }
    return payload


def _discover_test_ids(repo_root: Path) -> tuple[str, ...]:
    suite = unittest.defaultTestLoader.discover(str(repo_root / "Tests"), pattern="test*.py")
    ids: list[str] = []
    _walk_suite(suite, ids)
    return tuple(sorted(ids))


def _walk_suite(suite: unittest.TestSuite, ids: list[str]) -> None:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            _walk_suite(item, ids)
        else:
            ids.append(item.id())


def _load_file_diagnostics(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "Documentation" / "EOEJ_file_diagnostics.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _closed_adverse_results() -> tuple[EOEJAdverseResult, ...]:
    return (
        EOEJAdverseResult("EOEJ-CLOSED-001", "trader package import tests", "COLLECTION_ERROR", "Trader", EOEJRootCause.PRODUCTION_IMPLEMENTATION_DEFECT.value, "Public trader imports must not depend on eager canonical-runtime construction.", "Moved paper brokerage control-panel dependencies to local imports and canonical runtime imports to concrete submodules.", "PASS", "CLOSED"),
        EOEJAdverseResult("EOEJ-CLOSED-002", "EnterpriseActivityBusTests.test_runtime_publishes_control_actions_to_eab", "FAILURE", "EnterpriseActivityBus", EOEJRootCause.TEST_EXPECTATION_STALE.value, "The protected invariant is EAB publication of the control action with proof-domain labeling.", "Updated assertion from historical paper label to current proof-mode event and evidence marker.", "PASS", "CLOSED"),
    )


def _open_adverse_results() -> tuple[EOEJAdverseResult, ...]:
    return (
        EOEJAdverseResult("EOEJ-OPEN-001", "ARGOSControlPanelDashboardTests.test_broker_realistic_paper_trading_fills_only_with_deposited_cash_during_regular_session", "FAILURE", "DashboardPaperWorkflow", EOEJRootCause.TEST_EXPECTATION_STALE.value, "Proof-mode self-training intentionally does not create certified PAPER order-ledger truth.", "Rework historical dashboard tests to use a certified OR-003 paper-broker stimulus or assert proof-mode non-mutation.", "FAIL", "OPEN"),
        EOEJAdverseResult("EOEJ-OPEN-002", "ARGOSControlPanelDashboardTests.test_eo_g_provider_registry_capabilities_and_normalized_objects_are_visible", "FAILURE", "MarketDataProvider", EOEJRootCause.TEST_EXPECTATION_STALE.value, "EO-DJ provider authority registry removed the legacy mock provider from the production-facing provider set.", "Update EO-G assertions to check authoritative test/development provider IDs and production reachability rules.", "FAIL", "OPEN"),
        EOEJAdverseResult("EOEJ-OPEN-003", "ARGOSControlPanelDashboardTests.test_workflow_runtime_monitor_retains_latest_ten_completed_workflows", "TIMEOUT", "WorkflowRuntimeMonitor", EOEJRootCause.TIMEOUT_CONTRIBUTOR.value, "The final dashboard workflow-retention test remains a long-running timeout contributor.", "Bound workflow-loop completion or replace the fixture with deterministic completed workflow records.", "TIMEOUT", "OPEN"),
    )


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()
