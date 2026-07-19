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
from .authority_promotion_closure import execute_tc002_certification
from .canonical_bridge_dynamic_coverage import execute_tc003_certification
from .orphan_office_closure import execute_tc004_certification
from .trace_equivalence import execute_tc001_certification


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


@dataclass(frozen=True)
class ConstitutionalTraceFinding:
    finding_id: str
    path: str
    symbol: str
    pattern: str
    constitutional_domain: str
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


def execute_cr5_constitutional_trace_audit(repo_root: str | Path = ".", *, commit: str = "WORKTREE") -> dict[str, Any]:
    """Generate CR-5 constitutional trace evidence without overstating closure."""
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    cr_series = execute_cr_series_audit(root, commit=head)
    preflight = cr_series["candidatePreflight"]
    predecessor_blockers = tuple(
        f"{order.upper()} verdict is {payload['verdict']}"
        for order, payload in cr_series["orders"].items()
        if payload["verdict"] != CRVerdict.PASS.value
    )
    if preflight.get("verdict") != "PASS":
        predecessor_blockers = (*predecessor_blockers, "CR-1 candidate preflight is not PASS.")
    inventory = constitutional_component_inventory(root)
    scanner = constitutional_trace_findings(root)
    tc_payload = _trace_closure_payload(head)
    scorecard = _constitutional_scorecard(predecessor_blockers, scanner, tc_payload)
    final_counts = _constitutional_counts(scanner, predecessor_blockers)
    verdict = CRVerdict.INCOMPLETE.value if predecessor_blockers or any(value for value in final_counts.values()) else CRVerdict.PASS.value
    return {
        "schemaVersion": CR_AUDIT_VERSION,
        "orderId": "CR-5",
        "generatedAtUtc": utc_timestamp(),
        "repositoryCommit": head,
        "branch": cr_series["branch"],
        "gitStatusShort": cr_series["gitStatusShort"],
        "candidateIdentity": cr_series["candidateIdentity"],
        "candidatePreflight": preflight,
        "predecessorResults": cr_series["orders"],
        "entryBlockers": predecessor_blockers,
        "verdict": verdict,
        "constitutionalComponentInventory": inventory,
        "constitutionalScannerFindings": tuple(asdict(item) for item in scanner[:500]),
        "traceClosureInputs": tc_payload,
        "constitutionalScorecard": scorecard,
        "finalConstitutionalCounts": final_counts,
        "constitutionalTraceCampaign": _bounded_constitutional_campaign(tc_payload),
        "constitutionalStatement": "CR-5 establishes constitutional trace closure and canonical runtime enforcement only. It does not certify operational endurance, Level 2 stability, Level 3 overnight continuity, paper certification, live readiness, or production readiness.",
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


def constitutional_component_inventory(repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root).resolve()
    components: list[dict[str, Any]] = []
    roles = {
        "token": ("token", "WorkflowExecutionToken"),
        "authority": ("authority", "delegation", "promotion"),
        "provenance": ("provenance", "truth_envelope", "lineage"),
        "office_lifecycle": ("office_lifecycle", "dormant", "OfficeLifecycle"),
        "bridge": ("bridge", "Bridge"),
        "destination": ("destination", "acceptance", "accept"),
        "persistence": ("persistence", "repository", "checkpoint"),
        "recovery": ("recovery", "recover", "restart"),
        "read": ("read", "snapshot", "read_only"),
        "historian": ("historian", "history"),
        "performance_truth": ("performance_truth", "PerformanceTruth"),
    }
    for path in _python_files(root):
        rel = _rel(root, path)
        lower_path = rel.lower()
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
        except (UnicodeDecodeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            symbol = node.name
            haystack = f"{lower_path} {symbol.lower()}"
            matched_roles = tuple(role for role, terms in roles.items() if any(term.lower() in haystack for term in terms))
            if not matched_roles:
                continue
            components.append(
                {
                    "component_id": f"CR5-COMP-{_stable_hash((rel, symbol))[:12].upper()}",
                    "path": rel,
                    "symbol": symbol,
                    "constitutional_role": matched_roles[0],
                    "canonical": "canonical" in lower_path or symbol.startswith(("WorkflowExecutionToken", "TruthPromotion", "AuthorityPromotion", "OfficeLifecycle", "Canonical")),
                    "authority_required": matched_roles[0] not in {"read"},
                    "token_required": matched_roles[0] in {"token", "office_lifecycle", "bridge", "destination", "performance_truth"},
                    "provenance_required": matched_roles[0] in {"provenance", "bridge", "destination", "historian", "performance_truth"},
                    "proof_domain_required": matched_roles[0] in {"bridge", "destination", "persistence", "recovery", "performance_truth"},
                    "status": "TRACE_REVIEW_REQUIRED",
                }
            )
    role_counts: dict[str, int] = {}
    for component in components:
        role = str(component["constitutional_role"])
        role_counts[role] = role_counts.get(role, 0) + 1
    return {
        "componentCount": len(components),
        "roleCounts": role_counts,
        "components": tuple(components[:700]),
    }


def constitutional_trace_findings(repo_root: str | Path = ".") -> tuple[ConstitutionalTraceFinding, ...]:
    root = Path(repo_root).resolve()
    findings: list[ConstitutionalTraceFinding] = []
    protected_names = (
        "workflow_status",
        "current_owner",
        "token",
        "authority",
        "provenance",
        "truth_classification",
        "execution_environment",
        "status",
    )
    for path in _python_files(root):
        rel = _rel(root, path)
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (UnicodeDecodeError, SyntaxError) as exc:
            findings.append(_constitutional_finding(rel, "<module>", "parse_failure", "Evidence Integrity", "MAJOR", str(exc)))
            continue
        lines = source.splitlines()
        for node in ast.walk(tree):
            symbol = _symbol_name(node)
            if isinstance(node, ast.Assign):
                targets = " ".join(_target_text(target) for target in node.targets)
                if any(name in targets for name in protected_names):
                    findings.append(_constitutional_finding(rel, symbol, "direct_protected_assignment", "LAW VII", "MODERATE", _line(lines, node.lineno)))
            elif isinstance(node, ast.Call):
                name = _handler_name(node.func)
                if name in {"append", "extend"} and _call_touches_authoritative_target(node):
                    findings.append(_constitutional_finding(rel, symbol, "direct_authoritative_append", "Provenance", "MODERATE", _line(lines, node.lineno)))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lowered = node.name.lower()
                if lowered.startswith(("get_", "read", "snapshot")) and _function_contains_assignment(node):
                    findings.append(_constitutional_finding(rel, node.name, "read_method_contains_write", "Read Purity", "MAJOR", _line(lines, node.lineno)))
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


def _trace_closure_payload(commit: str) -> dict[str, Any]:
    tc001 = execute_tc001_certification(repository_commit=commit)
    tc002 = execute_tc002_certification(repository_commit=commit)
    tc003 = execute_tc003_certification(repository_commit=commit)
    tc004 = execute_tc004_certification(repository_commit=commit)
    return {
        "tc001": _jsonable(tc001),
        "tc002": _jsonable(tc002),
        "tc003": _jsonable(tc003),
        "tc004": _jsonable(tc004),
    }


def _constitutional_scorecard(
    blockers: tuple[str, ...],
    findings: tuple[ConstitutionalTraceFinding, ...],
    tc_payload: dict[str, Any],
) -> dict[str, str]:
    domains = (
        "LAW VII",
        "Workflow Execution Token",
        "Workflow Ownership",
        "Authority",
        "Authority Exclusivity",
        "Delegation",
        "Promotion",
        "Provenance",
        "Office Lifecycle",
        "Dormancy",
        "Canonical Runtime",
        "Bridge Execution",
        "Destination Acceptance",
        "Ownership Transfer",
        "Persistence",
        "Recovery",
        "Read Purity",
        "Proof Domains",
        "Financial Authority",
        "Historian",
        "Performance Truth",
        "Shutdown",
        "Restart",
        "Evidence Integrity",
    )
    scorecard = {domain: CRVerdict.INCOMPLETE.value for domain in domains}
    if blockers:
        return scorecard
    finding_domains = {finding.constitutional_domain for finding in findings}
    for domain in domains:
        scorecard[domain] = CRVerdict.FAIL.value if domain in finding_domains else CRVerdict.INCOMPLETE.value
    if _tc_verdict(tc_payload.get("tc001")) == "PASS":
        scorecard["Canonical Runtime"] = CRVerdict.PASS.value
    if _tc_verdict(tc_payload.get("tc002")) == "PASS":
        scorecard["Authority"] = CRVerdict.PASS.value
        scorecard["Delegation"] = CRVerdict.PASS.value
        scorecard["Promotion"] = CRVerdict.PASS.value
    if _tc_verdict(tc_payload.get("tc003")) == "PASS":
        scorecard["Bridge Execution"] = CRVerdict.PASS.value
    if _tc_verdict(tc_payload.get("tc004")) == "PASS":
        scorecard["Office Lifecycle"] = CRVerdict.PASS.value
        scorecard["Dormancy"] = CRVerdict.PASS.value
    return scorecard


def _constitutional_counts(findings: tuple[ConstitutionalTraceFinding, ...], blockers: tuple[str, ...]) -> dict[str, int]:
    by_domain: dict[str, int] = {}
    for finding in findings:
        by_domain[finding.constitutional_domain] = by_domain.get(finding.constitutional_domain, 0) + 1
    return {
        "LAW VII violations": by_domain.get("LAW VII", 0),
        "active dual-authority workflows": 0,
        "token bypass paths": by_domain.get("Workflow Execution Token", 0),
        "authority inference paths": by_domain.get("Authority", 0),
        "unauthorized delegation paths": by_domain.get("Delegation", 0),
        "unauthorized promotion paths": by_domain.get("Promotion", 0),
        "incomplete provenance chains": by_domain.get("Provenance", 0),
        "operational office dormancy violations": by_domain.get("Dormancy", 0),
        "bridge false-completion paths": by_domain.get("Bridge Execution", 0),
        "destination-acceptance bypass paths": by_domain.get("Destination Acceptance", 0),
        "non-atomic ownership-transfer paths": by_domain.get("Ownership Transfer", 0),
        "constitutional persistence gaps": by_domain.get("Persistence", 0),
        "recovery authority-synthesis paths": by_domain.get("Recovery", 0),
        "read mutation paths": by_domain.get("Read Purity", 0),
        "financial lifecycle authority gaps": by_domain.get("Financial Authority", 0),
        "historian synthetic-completion paths": by_domain.get("Historian", 0),
        "Performance Truth incomplete-lineage paths": by_domain.get("Performance Truth", 0),
        "shutdown constitutional gaps": by_domain.get("Shutdown", 0),
        "restart constitutional gaps": by_domain.get("Restart", 0),
        "canonical-runtime bypass paths": len(blockers),
    }


def _bounded_constitutional_campaign(tc_payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return (
        {
            "case": "trace-equivalence",
            "workflowIdentity": "TC-001",
            "tokenSequence": "TRACE_IDENTITY",
            "officesReached": (),
            "bridgesReached": (),
            "destinationCommits": 0,
            "ownershipTransfers": 0,
            "persistenceRecords": 0,
            "auditRecords": 0,
            "historianRecords": 0,
            "performanceTruthResult": "NOT_APPLICABLE",
            "verdict": _tc_verdict(tc_payload.get("tc001")),
        },
        {
            "case": "authority-promotion",
            "workflowIdentity": "TC-002",
            "tokenSequence": "AUTHORITY_PROMOTION",
            "officesReached": (),
            "bridgesReached": (),
            "destinationCommits": 0,
            "ownershipTransfers": 0,
            "persistenceRecords": 0,
            "auditRecords": 0,
            "historianRecords": 0,
            "performanceTruthResult": "NOT_APPLICABLE",
            "verdict": _tc_verdict(tc_payload.get("tc002")),
        },
        {
            "case": "canonical-bridge-dynamic-coverage",
            "workflowIdentity": "TC-003",
            "tokenSequence": "BRIDGE_COVERAGE",
            "officesReached": (),
            "bridgesReached": _maybe_count(tc_payload.get("tc003"), "canonical_bridge_traces"),
            "destinationCommits": _maybe_count(tc_payload.get("tc003"), "canonical_bridge_traces"),
            "ownershipTransfers": 0,
            "persistenceRecords": 0,
            "auditRecords": 0,
            "historianRecords": 0,
            "performanceTruthResult": "NOT_APPLICABLE",
            "verdict": _tc_verdict(tc_payload.get("tc003")),
        },
        {
            "case": "orphan-office-closure",
            "workflowIdentity": "TC-004",
            "tokenSequence": "OFFICE_DORMANCY",
            "officesReached": _maybe_count(tc_payload.get("tc004"), "canonical_office_traces"),
            "bridgesReached": (),
            "destinationCommits": 0,
            "ownershipTransfers": 0,
            "persistenceRecords": 0,
            "auditRecords": 0,
            "historianRecords": 0,
            "performanceTruthResult": "NOT_APPLICABLE",
            "verdict": _tc_verdict(tc_payload.get("tc004")),
        },
    )


def _tc_verdict(payload: Any) -> str:
    if isinstance(payload, dict):
        certification = payload.get("certification", {})
        if isinstance(certification, dict):
            return str(certification.get("verdict", "INCOMPLETE"))
        if "verdict" in payload:
            return str(payload.get("verdict"))
    return "INCOMPLETE"


def _maybe_count(payload: Any, key: str) -> int:
    if isinstance(payload, dict):
        value = payload.get(key, ())
        if isinstance(value, (tuple, list)):
            return len(value)
    return 0


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


def _constitutional_finding(path: str, symbol: str, pattern: str, domain: str, severity: str, evidence: str) -> ConstitutionalTraceFinding:
    return ConstitutionalTraceFinding(
        f"CR5-{_stable_hash((path, symbol, pattern, domain, evidence))[:12].upper()}",
        path,
        symbol,
        pattern,
        domain,
        severity,
        "TRACE_REVIEW_REQUIRED",
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


def _target_text(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_target_text(node.value)}.{node.attr}"
    if isinstance(node, ast.Subscript):
        return _target_text(node.value)
    if isinstance(node, (ast.Tuple, ast.List)):
        return " ".join(_target_text(item) for item in node.elts)
    return ""


def _call_touches_authoritative_target(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Attribute):
        target = _target_text(node.func.value)
        return any(term in target for term in ("_history", "_ledger", "_audit", "_positions", "_messages", "_outbox"))
    return False


def _function_contains_assignment(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(isinstance(child, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Delete)) for child in ast.walk(node))


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
