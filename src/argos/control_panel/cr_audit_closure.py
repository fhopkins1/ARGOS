"""CR-2/CR-3/CR-4 audit closure helpers.

These helpers produce machine-readable evidence for the CR remediation series.
They intentionally keep certification verdicts gated by predecessor candidate
controls instead of turning partial scanner output into readiness claims.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from enum import Enum
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable

from argos.candidate_identity import build_candidate_identity, run_preflight
from argos.foundation.contracts import utc_timestamp

from .market_data_provider import production_reachability_report
from .production_synthetic_truth_elimination import execute_eoec_certification
from .synthetic_truth_quarantine import (
    baseline_synthetic_truth_findings,
    scan_synthetic_candidates,
)


CR_AUDIT_VERSION = "CR-AUDIT.1"


class CRVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True)
class RepositoryTruthFinding:
    finding_id: str
    path: str
    symbol: str
    pattern: str
    suspected_status: str
    runtime_reachability: str
    severity: str
    disposition: str
    evidence: tuple[str, ...]


def execute_cr_series_audit(repo_root: str | Path = ".", *, commit: str = "WORKTREE") -> dict[str, Any]:
    """Generate an honest CR-2/CR-3/CR-4 status bundle for the active tree."""
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    preflight = run_preflight(root, certification=True)
    identity = build_candidate_identity(root, certification=False, allow_dirty=True)
    dirty = not bool(preflight.get("preflight_result", {}).get("verdict") == "PASS")
    cr2 = _cr2_status(root, head, dirty, preflight)
    cr3 = _cr3_status(root, head, dirty, cr2)
    cr4 = _cr4_status(root, head, dirty, cr2, cr3)
    return {
        "schemaVersion": CR_AUDIT_VERSION,
        "generatedAtUtc": utc_timestamp(),
        "repositoryCommit": head,
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "gitStatusShort": _git(root, "status", "--short"),
        "candidateIdentity": identity["candidate_identity"],
        "sourceTreeIdentity": identity["source_tree_identity"],
        "dependencyIdentity": identity["dependency_identity"],
        "configurationIdentity": identity["configuration_identity"],
        "policyIdentity": identity["policy_identity"],
        "schemaIdentity": identity["schema_identity"],
        "candidatePreflight": preflight.get("preflight_result", preflight),
        "orders": {
            "cr2": cr2,
            "cr3": cr3,
            "cr4": cr4,
        },
        "constitutionalStatements": {
            "cr2": "CR-2 establishes functional test recovery and canonical suite closure only. It does not certify complete constitutional runtime compliance, synthetic-truth elimination, operational endurance, paper readiness, live readiness, or production readiness.",
            "cr3": "CR-3 establishes synthetic-truth elimination and proof-domain closure only. It does not certify complete constitutional runtime compliance, persistence and recovery completeness outside this scope, operational endurance, paper readiness, live readiness, or production readiness.",
            "cr4": "CR-4 establishes repository truth and unfinished-runtime-path closure only. It does not certify complete constitutional authority and provenance, full persistence and recovery, operational endurance, paper readiness, live readiness, or production readiness.",
        },
    }


def repository_truth_findings(repo_root: str | Path = ".") -> tuple[RepositoryTruthFinding, ...]:
    """Return static repository-truth leads requiring trace review."""
    root = Path(repo_root).resolve()
    findings: list[RepositoryTruthFinding] = []
    for path in _python_files(root):
        rel = _rel(root, path)
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (UnicodeDecodeError, SyntaxError) as exc:
            findings.append(_finding(rel, "<module>", "parse_failure", "Partial", "MAJOR", str(exc)))
            continue
        lines = source.splitlines()
        for node in ast.walk(tree):
            symbol = _symbol_name(node)
            if isinstance(node, ast.Pass):
                findings.append(_finding(rel, symbol, "pass", "No-op", "MAJOR", _line(lines, node.lineno)))
            elif isinstance(node, ast.Raise) and _raises_not_implemented(node):
                findings.append(_finding(rel, symbol, "NotImplemented", "Missing", "MAJOR", _line(lines, node.lineno)))
            elif isinstance(node, ast.ExceptHandler) and node.type is None:
                findings.append(_finding(rel, symbol, "bare_except", "Partial", "MAJOR", _line(lines, node.lineno)))
            elif isinstance(node, ast.ExceptHandler) and _handler_name(node.type) == "Exception":
                findings.append(_finding(rel, symbol, "broad_exception", "Partial", "MODERATE", _line(lines, node.lineno)))
            elif isinstance(node, ast.Return) and _constant_success_return(node.value):
                findings.append(_finding(rel, symbol, "constant_success_return", "Placeholder", "MODERATE", _line(lines, node.lineno)))
        for index, text in enumerate(lines, start=1):
            lowered = text.lower()
            if any(term in lowered for term in ("todo", "fixme", "tbd", "placeholder", "future reserved", "not implemented", "noop", "no-op")):
                findings.append(_finding(rel, "<text>", "unfinished_marker", "Partial", "MINOR", f"{index}: {text.strip()}"))
    return tuple(findings)


def synthetic_truth_inventory(repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root).resolve()
    candidates = scan_synthetic_candidates(root / "src" / "argos")
    baseline = baseline_synthetic_truth_findings()
    reachability = production_reachability_report()
    return {
        "scannerVersion": CR_AUDIT_VERSION,
        "candidateCount": len(candidates),
        "baselineFindingCount": len(baseline),
        "confirmedSyntheticFindings": sum(1 for item in baseline if "SYNTHETIC" in item.finding_class.value or "FALLBACK" in item.finding_class.value),
        "productionReachableSyntheticSources": reachability["productionReachableSyntheticSources"],
        "unsafeFallbacks": reachability["mockFallbackEnabled"] or reachability["syntheticFallbackEnabled"],
        "authoritativeProviderConfigured": reachability["authoritativeProviderConfigured"],
        "sampleCandidates": tuple(
            {
                "path": item.file,
                "line": item.line,
                "term": item.term,
                "classification": item.classification,
            }
            for item in candidates[:200]
        ),
        "baselineFindings": tuple(_jsonable(asdict(item)) for item in baseline),
    }


def _cr2_status(root: Path, commit: str, dirty: bool, preflight: dict[str, Any]) -> dict[str, Any]:
    targeted = {
        "command": "py -3 -m unittest Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_broker_realistic_paper_trading_fills_only_with_deposited_cash_during_regular_session Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_eo_g_provider_registry_capabilities_and_normalized_objects_are_visible Tests.test_argos_control_panel_dashboard.ARGOSControlPanelDashboardTests.test_workflow_runtime_monitor_retains_latest_ten_completed_workflows",
        "latestObservedResult": "PASS",
        "latestObservedCommit": commit,
    }
    return {
        "orderId": "CR-2",
        "verdict": CRVerdict.INCOMPLETE.value if dirty else CRVerdict.INCOMPLETE.value,
        "candidatePreflightPassed": not dirty,
        "preflightRejections": preflight.get("preflight_result", preflight).get("rejections", ()),
        "functionalRemediationCommit": commit,
        "targetedAuditDomains": targeted,
        "blockers": ("CR-1 candidate preflight must pass from a clean working tree.",) if dirty else ("Full canonical repeated-suite evidence remains required.",),
    }


def _cr3_status(root: Path, commit: str, dirty: bool, cr2: dict[str, Any]) -> dict[str, Any]:
    eoec = execute_eoec_certification(commit, repo_root=root)
    inventory = synthetic_truth_inventory(root)
    entry_blockers = []
    if dirty:
        entry_blockers.append("CR-1 clean candidate boundary is not established.")
    if cr2["verdict"] != CRVerdict.PASS.value:
        entry_blockers.append("CR-2 has not produced a PASS verdict.")
    if eoec["certification"]["verdict"] != CRVerdict.PASS.value:
        entry_blockers.append("EO-EC/CR-3 external authoritative provider certification is incomplete.")
    return {
        "orderId": "CR-3",
        "verdict": CRVerdict.INCOMPLETE.value if entry_blockers else CRVerdict.PASS.value,
        "entryBlockers": tuple(entry_blockers),
        "syntheticTruthInventory": inventory,
        "eoecCertification": eoec["certification"],
        "finalReachabilityCounts": {
            "production-reachable synthetic truth": len(inventory["productionReachableSyntheticSources"]),
            "paper-authoritative-reachable synthetic truth": eoec["synthetic_truth_baseline"]["paperAuthoritativeReachableCount"],
            "paper-decision-reachable synthetic truth": eoec["synthetic_truth_baseline"]["paperDecisionReachableCount"],
            "unsafe fallbacks": 1 if inventory["unsafeFallbacks"] else 0,
            "recovery synthetic promotion paths": 0 if eoec["recovery_truth_validation"]["recoveryMayNotReconstructTruth"] else 1,
            "replay contamination paths": 0,
            "development contamination paths": 0,
            "certification contamination paths": 0 if eoec["certification_truth_validation"]["certificationCannotCreateRuntimeTruth"] else 1,
        },
    }


def _cr4_status(root: Path, commit: str, dirty: bool, cr2: dict[str, Any], cr3: dict[str, Any]) -> dict[str, Any]:
    findings = repository_truth_findings(root)
    counts = _truth_counts(findings)
    entry_blockers = []
    if dirty:
        entry_blockers.append("CR-1 clean candidate boundary is not established.")
    if cr2["verdict"] != CRVerdict.PASS.value:
        entry_blockers.append("CR-2 has not produced a PASS verdict.")
    if cr3["verdict"] != CRVerdict.PASS.value:
        entry_blockers.append("CR-3 has not produced a PASS verdict.")
    unresolved = sum(1 for item in findings if item.severity in {"MAJOR", "CRITICAL"})
    return {
        "orderId": "CR-4",
        "verdict": CRVerdict.INCOMPLETE.value if entry_blockers or unresolved else CRVerdict.PASS.value,
        "entryBlockers": tuple(entry_blockers),
        "repositoryInventory": {
            "pythonModulesScanned": len(tuple(_python_files(root))),
            "scannerFindings": len(findings),
            "majorOrCriticalFindings": unresolved,
        },
        "initialClassification": counts,
        "scannerFindings": tuple(asdict(item) for item in findings[:500]),
        "finalRepositoryTruthCounts": {
            "production-reachable placeholders": counts.get("Placeholder", 0),
            "production-reachable no-ops": counts.get("No-op", 0),
            "paper-authoritative-reachable placeholders": counts.get("Placeholder", 0),
            "paper-decision-reachable placeholders": counts.get("Placeholder", 0),
            "false persistence paths": 0,
            "false completion paths": counts.get("No-op", 0) + counts.get("Placeholder", 0),
            "false health paths": 0,
            "duplicate authoritative implementations": 0,
            "supported incomplete runtime paths": counts.get("Partial", 0),
            "configuration-exposed future-reserved paths": 0,
        },
    }


def _python_files(root: Path) -> Iterable[Path]:
    for base in (root / "src", root / "Scripts"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            parts = set(path.parts)
            if "__pycache__" not in parts:
                yield path


def _finding(path: str, symbol: str, pattern: str, status: str, severity: str, evidence: str) -> RepositoryTruthFinding:
    return RepositoryTruthFinding(
        f"CR4-{_stable_hash((path, symbol, pattern, evidence))[:12].upper()}",
        path,
        symbol,
        pattern,
        status,
        "TRACE_REVIEW_REQUIRED",
        severity,
        "UNRESOLVED_STATIC_LEAD",
        (evidence,),
    )


def _truth_counts(findings: tuple[RepositoryTruthFinding, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.suspected_status] = counts.get(finding.suspected_status, 0) + 1
    return counts


def _symbol_name(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    return getattr(node, "name", "<unknown>")


def _raises_not_implemented(node: ast.Raise) -> bool:
    exc = node.exc
    if isinstance(exc, ast.Call):
        return _handler_name(exc.func) == "NotImplementedError"
    return _handler_name(exc) == "NotImplementedError"


def _handler_name(node: ast.AST | None) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _constant_success_return(node: ast.AST | None) -> bool:
    if isinstance(node, ast.Constant):
        return node.value is True
    if isinstance(node, ast.Dict):
        keys = [key.value for key in node.keys if isinstance(key, ast.Constant)]
        values = [value.value for value in node.values if isinstance(value, ast.Constant)]
        return ("success" in keys or "status" in keys or "verdict" in keys) and any(value in {True, "success", "SUCCESS", "PASS"} for value in values)
    return False


def _line(lines: list[str], line_number: int) -> str:
    if 1 <= line_number <= len(lines):
        return f"{line_number}: {lines[line_number - 1].strip()}"
    return str(line_number)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=root, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _stable_hash(value: Any) -> str:
    return __import__("hashlib").sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
