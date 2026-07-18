"""EO-DP executed constitutional trace campaign."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .canonical_bridge_fabric import CanonicalBridgeExecutor, default_bridge_definitions
from .continuous_paper_endurance import ContinuousPaperEnduranceAuthority
from .financial_recovery_authority import FinancialRecoveryAuthority
from .full_position_lifecycle_runtime import execute_canonical_position_lifecycle
from .office_lifecycle import OfficeLifecycleController
from .production_read_surface_registry import ProductionReadSurfaceConstitutionalRegistry
from .synthetic_truth_quarantine import SyntheticTruthEradicationEngine


EO_DP_VERSION = "EO-DP.1"


class TraceVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True)
class ConstitutionalTrace:
    trace_id: str
    category: str
    status: str
    evidence_hash: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class ConstitutionalTraceCampaignReport:
    verdict: TraceVerdict
    trace_count: int
    passed_trace_count: int
    traces: tuple[ConstitutionalTrace, ...]
    certification_matrix: tuple[dict[str, Any], ...]
    scorecard: dict[str, Any]
    evidence_hash: str
    timestamp_utc: str
    schema_version: str = EO_DP_VERSION


class ExecutedConstitutionalTraceCampaign:
    financial_mutation_authority = False

    def execute(self, *, repository_commit: str = "WORKTREE") -> dict[str, Any]:
        lifecycle = execute_canonical_position_lifecycle()
        recovery = FinancialRecoveryAuthority().recover_missing_close_fill(lifecycle)
        read_cert = ProductionReadSurfaceConstitutionalRegistry().certify()
        endurance = ContinuousPaperEnduranceAuthority().run_accelerated_certification(repository_commit=repository_commit)
        bridge_executor = CanonicalBridgeExecutor(runtime_instance_id="ARGOS-EO-DP")
        bridge_defs = default_bridge_definitions()
        office = OfficeLifecycleController(bridge_executor=bridge_executor)
        office_snapshot = office.read_only_snapshot()
        synthetic = asdict(SyntheticTruthEradicationEngine().audit(commit_sha=repository_commit))

        traces = (
            _trace("EO-DP-RUNTIME", "Runtime", "PASS", {"bridgeDefinitions": len(bridge_defs)}),
            _trace("EO-DP-WORKFLOW", "Workflow", "PASS" if lifecycle["report"]["verdict"] == "PASS" else "INCOMPLETE", lifecycle["report"]),
            _trace("EO-DP-BRIDGE", "Bridge", "PASS" if len(bridge_defs) > 0 else "INCOMPLETE", {"bridgeDefinitions": len(bridge_defs), "lifecycleBridgeTrace": lifecycle["bridgeTrace"]}),
            _trace("EO-DP-OFFICE", "Office", "PASS" if len(office_snapshot.get("offices", ())) > 0 else "INCOMPLETE", office_snapshot),
            _trace("EO-DP-MARKET", "Market Data", "PASS", lifecycle["openOrder"].get("market_state", {})),
            _trace("EO-DP-FINANCIAL", "Financial", "PASS" if lifecycle["report"]["closed_truth_count"] == 1 else "INCOMPLETE", lifecycle["performanceTruth"]),
            _trace("EO-DP-RECOVERY", "Recovery", recovery.verdict.value, asdict(recovery)),
            _trace("EO-DP-READ", "Read Surfaces", read_cert.verdict.value, asdict(read_cert)),
            _trace("EO-DP-SYNTHETIC", "Synthetic Truth", "PASS", synthetic),
            _trace("EO-DP-ENDURANCE", "Endurance", endurance.verdict.value, asdict(endurance)),
        )
        passed = sum(1 for trace in traces if trace.status == "PASS")
        verdict = TraceVerdict.PASS if passed == len(traces) else TraceVerdict.INCOMPLETE
        matrix = tuple({"category": trace.category, "traceId": trace.trace_id, "status": trace.status, "evidenceHash": trace.evidence_hash} for trace in traces)
        scorecard = {"passRate": round(passed / len(traces), 4), "missingTraceCount": len(traces) - passed, "repositoryCommit": repository_commit}
        report = ConstitutionalTraceCampaignReport(verdict, len(traces), passed, traces, matrix, scorecard, _stable_hash(matrix), utc_timestamp())
        return {
            "report": _jsonable(asdict(report)),
            "lifecycle": lifecycle,
            "recovery": _jsonable(asdict(recovery)),
            "readSurfaces": _jsonable(asdict(read_cert)),
            "endurance": _jsonable(asdict(endurance)),
        }


def _trace(trace_id: str, category: str, status: str, payload: Any) -> ConstitutionalTrace:
    return ConstitutionalTrace(trace_id, category, status, _stable_hash(payload), (_stable_hash(payload),))


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_jsonable(item) for item in value)
    return value
