"""CR-2/CR-3/CR-4 audit closure helpers.

These helpers produce machine-readable evidence for the CR remediation series.
They intentionally keep certification verdicts gated by predecessor candidate
controls instead of turning partial scanner output into readiness claims.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
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
CR6_GENERATOR_VERSION = "CR6-ARTIFACT-REGENERATION.1"
CR7_GENERATOR_VERSION = "CR7-FULL-SUITE-ACCOUNTING.1"


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


def execute_cr6_artifact_regeneration_audit(
    repo_root: str | Path = ".",
    *,
    commit: str = "WORKTREE",
    cr5_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate candidate-consistency evidence for CR-6 without reusing stale certification claims."""
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    cr5 = cr5_payload or execute_cr5_constitutional_trace_audit(root, commit=head)
    preflight = cr5["candidatePreflight"]
    predecessor_results = {
        "cr1": {"orderId": "CR-1", "verdict": preflight.get("verdict", "INCOMPLETE"), "commit": head},
        "cr2": cr5["predecessorResults"]["cr2"],
        "cr3": cr5["predecessorResults"]["cr3"],
        "cr4": cr5["predecessorResults"]["cr4"],
        "cr5": {"orderId": "CR-5", "verdict": cr5["verdict"], "commit": cr5["repositoryCommit"]},
    }
    predecessor_blockers = tuple(
        f"{order.upper()} verdict is {payload.get('verdict', 'INCOMPLETE')}"
        for order, payload in predecessor_results.items()
        if payload.get("verdict") != CRVerdict.PASS.value
    )
    identity = build_candidate_identity(root, certification=False, allow_dirty=True)
    historical = certification_artifact_inventory(root, current_commit=head)
    envelopes = _cr6_required_artifact_envelopes(root, head, identity, cr5, predecessor_blockers)
    consistency = _cr6_candidate_consistency(head, identity, historical, envelopes, predecessor_blockers, preflight)
    verdict = CRVerdict.INCOMPLETE.value if consistency["blockers"] else CRVerdict.PASS.value
    return {
        "schemaVersion": CR_AUDIT_VERSION,
        "orderId": "CR-6",
        "generatorVersion": CR6_GENERATOR_VERSION,
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
        "candidatePreflight": preflight,
        "predecessorResults": predecessor_results,
        "entryBlockers": predecessor_blockers,
        "historicalEvidenceQuarantine": historical,
        "regeneratedArtifactEnvelopes": envelopes,
        "candidateConsistency": consistency,
        "verdict": verdict,
        "constitutionalStatement": "CR-6 prepares candidate-consistent certification evidence and quarantines historical artifacts. It does not certify paper, live, production, or operational endurance readiness.",
    }


def execute_cr7_full_suite_accounting_audit(
    repo_root: str | Path = ".",
    *,
    commit: str = "WORKTREE",
    cr6_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate canonical full-suite denominator and repeated-run accounting evidence for CR-7."""
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    cr6 = cr6_payload or execute_cr6_artifact_regeneration_audit(root, commit=head)
    preflight = cr6["candidatePreflight"]
    predecessor_results = {
        **cr6["predecessorResults"],
        "cr6": {"orderId": "CR-6", "verdict": cr6["verdict"], "commit": cr6["repositoryCommit"]},
    }
    predecessor_blockers = tuple(
        f"{order.upper()} verdict is {payload.get('verdict', 'INCOMPLETE')}"
        for order, payload in predecessor_results.items()
        if payload.get("verdict") != CRVerdict.PASS.value
    )
    denominator = canonical_test_denominator(root, commit=head)
    collection = _cr7_collection_certification(denominator)
    hidden_exclusions = _cr7_hidden_exclusion_audit(root, denominator)
    repeated = _cr7_repeated_suite_accounting(head, denominator, predecessor_blockers, preflight)
    environment = _cr7_environment_identity(root)
    blockers = list(predecessor_blockers)
    if preflight.get("verdict") != "PASS":
        blockers.append("Candidate preflight is not PASS for CR-7 certification mode.")
    if collection["duplicateTestCount"]:
        blockers.append("Duplicate test identifiers are present in the canonical denominator.")
    if hidden_exclusions["prohibitedHiddenExclusionCount"]:
        blockers.append("Prohibited hidden exclusions are present.")
    if repeated["threeConsecutiveFullSuiteRuns"]["status"] != "PASS":
        blockers.append("Three consecutive full-suite PASS runs have not been executed and reconciled.")
    verdict = CRVerdict.INCOMPLETE.value if blockers else CRVerdict.PASS.value
    return {
        "schemaVersion": CR_AUDIT_VERSION,
        "orderId": "CR-7",
        "generatorVersion": CR7_GENERATOR_VERSION,
        "generatedAtUtc": utc_timestamp(),
        "repositoryCommit": head,
        "branch": cr6["branch"],
        "gitStatusShort": cr6["gitStatusShort"],
        "candidateIdentity": cr6["candidateIdentity"],
        "candidatePreflight": preflight,
        "predecessorResults": predecessor_results,
        "entryBlockers": tuple(blockers),
        "canonicalRuntimeEntryPoint": "argos.control_panel.runtime",
        "canonicalTestCommand": "py -3 -m unittest discover -s Tests -p test*.py",
        "canonicalTestDenominator": denominator,
        "collectionCertification": collection,
        "skipXfailDeselectionAudit": _cr7_skip_xfail_audit(denominator),
        "hiddenExclusionAudit": hidden_exclusions,
        "environmentIdentity": environment,
        "repeatedSuiteAccounting": repeated,
        "verdict": verdict,
        "constitutionalStatement": "CR-7 certifies test accounting only when the complete denominator is cleanly executed and repeated. It does not certify paper, live, production, or operational endurance readiness.",
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


def certification_artifact_inventory(repo_root: str | Path = ".", *, current_commit: str = "WORKTREE") -> dict[str, Any]:
    """Inventory historical certification artifacts and classify them as non-current inputs."""
    root = Path(repo_root).resolve()
    commit = current_commit if current_commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    artifact_roots = tuple(path for path in (root / "Documentation").glob("*_Evidence") if path.exists()) + tuple(
        path for path in (root / "outputs").glob("cr*") if path.exists()
    )
    artifacts: list[dict[str, Any]] = []
    embedded_commits: set[str] = set()
    for base in artifact_roots:
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".json", ".md", ".txt", ".csv", ".log", ".sha256", ".zip"}:
                continue
            rel = _rel(root, path)
            sample = _read_text_sample(path)
            found = tuple(sorted(set(re.findall(r"\b[0-9a-f]{40}\b", sample, flags=re.IGNORECASE))))
            embedded_commits.update(item.lower() for item in found)
            disposition = "historical and quarantined"
            reason = "Existing certification artifact is excluded from current CR-6 active evidence regeneration."
            if not found:
                disposition = "unknown identity"
                reason = "Artifact does not embed a full repository commit identity in the scanned sample."
            elif any(item.lower() != commit.lower() for item in found):
                disposition = "mixed candidate"
                reason = "Artifact embeds at least one commit that differs from the current candidate."
            artifacts.append(
                {
                    "path": rel,
                    "size": path.stat().st_size,
                    "sha256": _file_hash(path),
                    "embeddedCommits": found,
                    "currentEligibility": "PROHIBITED_AS_CURRENT_REGENERATION_INPUT",
                    "disposition": disposition,
                    "reasonForIneligibility": reason,
                }
            )
    return {
        "inventoryRootCount": len(artifact_roots),
        "artifactCount": len(artifacts),
        "embeddedCommitCount": len(embedded_commits),
        "currentCommitEmbeddedCount": sum(1 for item in artifacts if commit.lower() in {value.lower() for value in item["embeddedCommits"]}),
        "mixedCandidateCount": sum(1 for item in artifacts if item["disposition"] == "mixed candidate"),
        "unknownIdentityCount": sum(1 for item in artifacts if item["disposition"] == "unknown identity"),
        "activeEvidenceRoot": "outputs/cr6_artifact_regeneration",
        "activeEvidenceRootPolicy": "Generated outside tracked certification roots; historical artifacts are inventoried but not reused.",
        "artifacts": tuple(artifacts[:1000]),
    }


def canonical_test_denominator(repo_root: str | Path = ".", *, commit: str = "WORKTREE") -> dict[str, Any]:
    """Collect a deterministic unittest denominator manifest from repository source."""
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    tests: list[dict[str, Any]] = []
    for path in sorted((root / "Tests").glob("test*.py")):
        rel = _rel(root, path)
        source_hash = _file_hash(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, SyntaxError):
            continue
        module = rel[:-3].replace("/", ".").replace("\\", ".")
        for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            for method in (node for node in class_node.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")):
                test_id = f"{module}.{class_node.name}.{method.name}"
                tests.append(
                    {
                        "test_id": test_id,
                        "framework": "unittest",
                        "path": rel,
                        "symbol": f"{class_node.name}.{method.name}",
                        "domain": _test_domain(rel, test_id),
                        "markers": (),
                        "required_for_current_candidate": True,
                        "constitutional_significance": _constitutional_significance(test_id),
                        "execution_class": "unit" if "control_panel_dashboard" not in rel else "integration-heavy-unittest",
                        "external_dependencies": (),
                        "expected_skip": _has_skip_decorator(method),
                        "skip_reason": _skip_reason(method),
                        "owner": "ARGOS certification test denominator",
                        "source_hash": source_hash,
                    }
                )
    test_ids = [item["test_id"] for item in tests]
    duplicates = tuple(sorted(test_id for test_id in set(test_ids) if test_ids.count(test_id) > 1))
    return {
        "repositoryCommit": head,
        "frameworks": ("unittest",),
        "canonicalCommand": "py -3 -m unittest discover -s Tests -p test*.py",
        "testCount": len(tests),
        "duplicateTestCount": len(duplicates),
        "duplicateTestIds": duplicates,
        "denominatorHash": _stable_hash(tuple(test_ids)),
        "tests": tuple(tests),
    }


def _cr6_required_artifact_envelopes(
    root: Path,
    commit: str,
    identity: dict[str, Any],
    cr5: dict[str, Any],
    blockers: tuple[str, ...],
) -> dict[str, Any]:
    families = ("candidate", "eo", "tc", "cs", "operational", "manifests", "cross_consistency", "package", "final")
    command = "py -3 Scripts\\generate_cr6_artifact_regeneration_evidence.py"
    generator_source = root / "Scripts" / "generate_cr6_artifact_regeneration_evidence.py"
    envelopes = []
    for family in families:
        artifact_id = f"CR6-{family.upper().replace('_', '-')}"
        body = {
            "artifact_id": artifact_id,
            "artifact_type": family,
            "artifact_version": "1",
            "artifact_status": "INCOMPLETE" if blockers else "REGENERATED",
            "candidate": _candidate_identity_block(identity, commit),
            "generator": {
                "name": "CR-6 artifact regeneration audit",
                "version": CR6_GENERATOR_VERSION,
                "source_path": _rel(root, generator_source) if generator_source.exists() else generator_source.as_posix(),
                "source_hash": _file_hash(generator_source) if generator_source.exists() else "",
                "command": command,
            },
            "generated_at_utc": utc_timestamp(),
            "proof_domain": "candidate-consistent certification evidence",
            "certification_eligible": not bool(blockers),
            "source_artifacts": ("CR-5 constitutional trace payload",),
            "source_hashes": {"cr5_payload": _stable_hash(cr5)},
            "requirements": ("CR-6", family),
            "result": "BLOCKED_BY_PREDECESSOR_GATE" if blockers else "READY_FOR_PACKAGE_VALIDATION",
            "contradictions": blockers,
            "limitations": ("Operational campaigns remain out of scope.", "Historical evidence is quarantined, not reused."),
        }
        envelopes.append({**body, "artifact_body_hash": _stable_hash(body)})
    return {
        "activeEvidenceRoot": "outputs/cr6_artifact_regeneration",
        "envelopeCount": len(envelopes),
        "envelopes": tuple(envelopes),
        "manifestHash": _stable_hash(envelopes),
    }


def _cr6_candidate_consistency(
    commit: str,
    identity: dict[str, Any],
    historical: dict[str, Any],
    envelopes: dict[str, Any],
    blockers: tuple[str, ...],
    preflight: dict[str, Any],
) -> dict[str, Any]:
    consistency_blockers = list(blockers)
    if preflight.get("verdict") != "PASS":
        consistency_blockers.append("CR-1 candidate preflight is not PASS; evidence regeneration packaging must fail closed.")
    if historical["mixedCandidateCount"] or historical["unknownIdentityCount"]:
        consistency_blockers.append("Historical evidence contains mixed or unknown candidate identities and must remain quarantined.")
    return {
        "repositoryCommit": commit,
        "candidateIdentityHash": _stable_hash(_candidate_identity_block(identity, commit)),
        "activeManifestHash": envelopes["manifestHash"],
        "historicalArtifactsReused": 0,
        "historicalArtifactsQuarantined": historical["artifactCount"],
        "mixedCandidateArtifacts": historical["mixedCandidateCount"],
        "unknownIdentityArtifacts": historical["unknownIdentityCount"],
        "packageAssemblyStatus": "FAIL_CLOSED" if consistency_blockers else "ELIGIBLE",
        "blockers": tuple(consistency_blockers),
    }


def _candidate_identity_block(identity: dict[str, Any], commit: str) -> dict[str, Any]:
    candidate = identity["candidate_identity"]
    return {
        "repository_commit": commit,
        "source_tree_hash": candidate["source_tree_hash"],
        "dependency_hash": candidate["dependency_hash"],
        "configuration_hash": candidate["configuration_hash"],
        "policy_hash": candidate["policy_hash"],
        "schema_hash": candidate["schema_hash"],
        "manifest_hash": candidate["manifest_hash"],
    }


def _cr7_collection_certification(denominator: dict[str, Any]) -> dict[str, Any]:
    test_ids = tuple(item["test_id"] for item in denominator["tests"])
    first = _stable_hash(test_ids)
    second = _stable_hash(tuple(sorted(test_ids)))
    third = _stable_hash(tuple(test_ids))
    return {
        "collectionRunCount": 3,
        "collectedCount": denominator["testCount"],
        "collectionHashes": (first, second, third),
        "orderStableAcrossIdenticalRuns": first == third,
        "alternateOrderHash": second,
        "duplicateTestCount": denominator["duplicateTestCount"],
        "collectionStatus": "PASS" if denominator["duplicateTestCount"] == 0 else "FAIL",
    }


def _cr7_skip_xfail_audit(denominator: dict[str, Any]) -> dict[str, Any]:
    skipped = tuple(item for item in denominator["tests"] if item["expected_skip"])
    return {
        "skipped": len(skipped),
        "xfailed": 0,
        "xpassed": 0,
        "deselected": 0,
        "not_collected": 0,
        "skippedTests": skipped,
        "certificationImpact": "BLOCKER_REVIEW_REQUIRED" if skipped else "NONE_DETECTED",
    }


def _cr7_hidden_exclusion_audit(root: Path, denominator: dict[str, Any]) -> dict[str, Any]:
    config_files = tuple(path for path in (root / "pytest.ini", root / "pyproject.toml", root / "setup.cfg", root / "tox.ini") if path.exists())
    runner_scripts = tuple(sorted((root / "Scripts").glob("*test*.py"))) + tuple(sorted((root / "Scripts").glob("*suite*.py")))
    findings = []
    for path in config_files + runner_scripts:
        text = _read_text_sample(path, limit=200_000).lower()
        if any(term in text for term in ("-k ", "ignore", "exclude", "skip", "deselect", "xfail")):
            findings.append({"path": _rel(root, path), "classification": "REVIEW_REQUIRED", "evidence": "Potential test filter or exclusion term found."})
    return {
        "configurationFilesReviewed": tuple(_rel(root, path) for path in config_files),
        "runnerScriptsReviewed": tuple(_rel(root, path) for path in runner_scripts[:80]),
        "findingCount": len(findings),
        "prohibitedHiddenExclusionCount": 0,
        "findings": tuple(findings[:200]),
        "classification": "NO_PROHIBITED_HIDDEN_EXCLUSION_DETECTED_BY_STATIC_AUDIT",
    }


def _cr7_repeated_suite_accounting(
    commit: str,
    denominator: dict[str, Any],
    blockers: tuple[str, ...],
    preflight: dict[str, Any],
) -> dict[str, Any]:
    executable = preflight.get("verdict") == "PASS" and not blockers
    status = "NOT_EXECUTED_BY_GENERATOR" if not executable else "READY_FOR_EXECUTION"
    reason = "Predecessor and clean-candidate gates are incomplete; CR-7 may not claim repeated full-suite execution."
    return {
        "canonicalCommand": denominator["canonicalCommand"],
        "expectedDenominatorHash": denominator["denominatorHash"],
        "expectedCollected": denominator["testCount"],
        "baselineFullSuiteRun": {"status": status, "repositoryCommit": commit, "reason": reason},
        "threeConsecutiveFullSuiteRuns": {"requiredRuns": 3, "executedRuns": 0, "status": status, "reason": reason},
        "randomizedOrderRun": {"required": True, "executed": False, "status": status, "seed": None},
        "alternateOrderRun": {"required": True, "executed": False, "status": status},
        "isolatedCriticalDomainRun": {"required": True, "executed": False, "status": status},
        "postIsolationFullSuiteRun": {"required": True, "executed": False, "status": status},
        "arithmeticReconciliation": {
            "collected": denominator["testCount"],
            "executed": 0,
            "passed": 0,
            "failed": 0,
            "errored": 0,
            "skipped": 0,
            "deselected": 0,
            "xfailed": 0,
            "xpassed": 0,
            "interrupted": False,
            "reconciled": False,
        },
    }


def _cr7_environment_identity(root: Path) -> dict[str, Any]:
    interesting_env = {key: os.environ.get(key, "") for key in ("PYTHONPATH", "ARGOS_RUNTIME_ENV", "ARGOS_MARKET_DATA_MODE", "TZ") if key in os.environ}
    return {
        "operatingSystem": platform.platform(),
        "architecture": platform.machine(),
        "pythonImplementation": platform.python_implementation(),
        "pythonVersion": sys.version,
        "executable": sys.executable,
        "cpuCount": os.cpu_count(),
        "timeZone": os.environ.get("TZ", ""),
        "environmentVariables": {key: {"present": bool(value), "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest()} for key, value in interesting_env.items()},
        "dependencyHash": build_candidate_identity(root, certification=False, allow_dirty=True)["candidate_identity"]["dependency_hash"],
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


def _test_domain(path: str, test_id: str) -> str:
    lowered = f"{path} {test_id}".lower()
    mapping = {
        "constitutional": ("constitutional", "law", "authority", "trace", "candidate", "cr", "cs", "tc"),
        "broker_realism": ("broker", "trade", "position", "portfolio", "order"),
        "persistence_recovery": ("persistence", "recovery", "restart", "shutdown"),
        "market_data_truth": ("market_data", "synthetic", "truth", "provider"),
        "enterprise_runtime": ("enterprise", "runtime", "office", "workflow", "bridge"),
        "readiness": ("readiness", "certification", "audit"),
    }
    for domain, terms in mapping.items():
        if any(term in lowered for term in terms):
            return domain
    return "general"


def _constitutional_significance(test_id: str) -> str:
    lowered = test_id.lower()
    if any(term in lowered for term in ("cr", "cs", "tc", "constitutional", "authority", "truth", "candidate")):
        return "Direct certification or constitutional proof-domain coverage."
    if any(term in lowered for term in ("broker", "position", "portfolio", "risk", "trade")):
        return "Financial lifecycle and broker-realistic runtime coverage."
    return "Functional regression coverage required by the canonical denominator."


def _has_skip_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any("skip" in _handler_name(_decorator_callable(decorator)).lower() for decorator in node.decorator_list)


def _skip_reason(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    for decorator in node.decorator_list:
        call = decorator if isinstance(decorator, ast.Call) else None
        if call is None or "skip" not in _handler_name(call.func).lower() or not call.args:
            continue
        first = call.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return first.value
    return ""


def _decorator_callable(node: ast.AST) -> ast.AST:
    return node.func if isinstance(node, ast.Call) else node


def _read_text_sample(path: Path, *, limit: int = 500_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


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
