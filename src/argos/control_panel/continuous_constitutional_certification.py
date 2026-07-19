"""Continuous Constitutional Certification sustainment framework.

The CSS framework is observational. It indexes repository truth, evaluates
certification sustainment gates, and fails closed when CR prerequisites or
evidence are missing. It never repairs runtime behavior or fabricates PASS.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from argos.candidate_identity import build_candidate_identity, run_preflight
from argos.foundation.contracts import utc_timestamp

from .canonical_bridge_fabric import default_bridge_definitions
from .cr_audit_closure import (
    CRVerdict,
    certification_artifact_inventory,
    constitutional_trace_findings,
    execute_cr10_level3_paper_candidate_audit,
    execute_cr7_full_suite_accounting_audit,
    synthetic_truth_inventory,
)


CSS_VERSION = "CSS-SUSTAINMENT.1"


class CSSVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CSSStageResult:
    stage_id: str
    name: str
    verdict: CSSVerdict
    evidence_refs: tuple[str, ...]
    findings: tuple[str, ...]
    evidence_hash: str


def execute_css_sustainment_pipeline(
    repo_root: str | Path = ".",
    *,
    commit: str = "WORKTREE",
    cr7_payload: dict[str, Any] | None = None,
    cr10_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the CSS-001 through CSS-006 continuous certification checks."""
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    identity = build_candidate_identity(root, certification=False, allow_dirty=True)
    preflight = run_preflight(root, certification=True).get("preflight_result", {})
    cr7 = cr7_payload or execute_cr7_full_suite_accounting_audit(root, commit=head)
    cr10 = cr10_payload or execute_cr10_level3_paper_candidate_audit(root, commit=head)
    repository_index = build_repository_truth_index(root, commit=head)
    claim_registry = build_certification_claim_registry(root, commit=head, repository_index=repository_index)
    evidence_manifest = build_css_evidence_manifest(root, commit=head)
    drift = detect_certification_drift(root, commit=head, repository_index=repository_index, evidence_manifest=evidence_manifest)
    prerequisite_blockers = _css_prerequisite_blockers(preflight, cr7, cr10)
    stage_payloads = (
        _pipeline_stage("CSS-001", "Continuous Constitutional Certification Pipeline", prerequisite_blockers, ("candidate_preflight", "cr10_result", "repository_truth_index")),
        _pipeline_stage("CSS-002", "Lifecycle Continuous Certification Pipeline", prerequisite_blockers, ("pipeline_stage_matrix", "evidence_manifest")),
        _pipeline_stage("CSS-003", "Continuous Constitutional Verification Framework", prerequisite_blockers + tuple(drift["blockingFindings"]), ("verification_task_catalog", "drift_report")),
        _pipeline_stage("CSS-004", "Repository Truth and Evidence Integrity Sustainment", prerequisite_blockers + tuple(claim_registry["blockingFindings"]), ("repository_truth_index", "claim_registry", "evidence_manifest")),
        _pipeline_stage("CSS-005", "Continuous Constitutional Certification Framework", prerequisite_blockers + tuple(drift["regressions"]), ("readiness_report", "evidence_ledger", "baseline_comparison")),
        _pipeline_stage("CSS-006", "Certification Drift Detection and Regression Guard", prerequisite_blockers + tuple(drift["blockingFindings"]), ("drift_report", "regression_guard")),
    )
    verdict = CSSVerdict.PASS.value if all(stage.verdict == CSSVerdict.PASS for stage in stage_payloads) else CSSVerdict.FAIL.value
    return {
        "schemaVersion": CSS_VERSION,
        "generatedAtUtc": utc_timestamp(),
        "repositoryCommit": head,
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "gitStatusShort": _git(root, "status", "--short"),
        "candidateIdentity": identity["candidate_identity"],
        "candidatePreflight": preflight,
        "cr7Certification": {"verdict": cr7["verdict"], "repositoryCommit": cr7["repositoryCommit"], "denominatorHash": cr7["canonicalTestDenominator"]["denominatorHash"]},
        "cr10Certification": {"verdict": cr10["verdict"], "repositoryCommit": cr10["repositoryCommit"], "paperCandidateQualified": cr10["paperCandidateQualification"]["qualified"]},
        "prerequisiteBlockers": prerequisite_blockers,
        "pipelineStages": tuple(_jsonable(asdict(stage)) for stage in stage_payloads),
        "repositoryTruthIndex": repository_index,
        "certificationClaimRegistry": claim_registry,
        "evidenceManifest": evidence_manifest,
        "verificationTaskCatalog": _verification_task_catalog(),
        "driftReport": drift,
        "readiness": {
            "state": "CERTIFIABLE" if verdict == CSSVerdict.PASS.value else "NOT CERTIFIABLE",
            "reason": "CSS fail-closed checks require CR-10 PASS, clean candidate preflight, supported claims, fresh evidence, and no regression drift.",
        },
        "verdict": verdict,
        "constitutionalStatement": "CSS continuously measures certification readiness and drift. It does not replace CR certification, repair implementation, or certify paper/live/production readiness.",
    }


def build_repository_truth_index(repo_root: str | Path = ".", *, commit: str = "WORKTREE") -> dict[str, Any]:
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    items: list[dict[str, Any]] = []
    for base, item_type in ((root / "src" / "argos", "runtime_module"), (root / "Tests", "test"), (root / "Scripts", "evidence_generator")):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = _rel(root, path)
            items.append(
                {
                    "itemId": f"CSS-ITEM-{_stable_hash(rel)[:12].upper()}",
                    "type": item_type,
                    "path": rel,
                    "sha256": _file_hash(path),
                    "associatedTests": _associated_tests(root, rel),
                    "associatedEvidence": _associated_evidence(root, rel),
                }
            )
    bridge_defs = tuple(asdict(item) for item in default_bridge_definitions())
    return {
        "repositoryCommit": head,
        "indexedItemCount": len(items),
        "runtimeModuleCount": sum(1 for item in items if item["type"] == "runtime_module"),
        "testCount": sum(1 for item in items if item["type"] == "test"),
        "evidenceGeneratorCount": sum(1 for item in items if item["type"] == "evidence_generator"),
        "bridgeCount": len(bridge_defs),
        "bridgeInventoryHash": _stable_hash(bridge_defs),
        "indexHash": _stable_hash(tuple((item["path"], item["sha256"]) for item in items)),
        "items": tuple(items[:1200]),
        "bridges": bridge_defs,
    }


def build_certification_claim_registry(
    repo_root: str | Path = ".",
    *,
    commit: str = "WORKTREE",
    repository_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    index = repository_index or build_repository_truth_index(root, commit=head)
    claims = []
    claim_specs = (
        ("CSS-CLAIM-CANDIDATE-IDENTITY", "Candidate identity exists and fail-closed preflight is executable.", ("src/argos/candidate_identity.py",), ("Tests/test_cr1_candidate_identity.py",)),
        ("CSS-CLAIM-BRIDGE-FIDELITY", "Canonical bridge denominator is indexed and dynamically verifiable.", ("src/argos/control_panel/canonical_bridge_fabric.py", "src/argos/control_panel/canonical_bridge_dynamic_coverage.py"), ("Tests/test_eoea_canonical_bridge_denominator_execution.py", "Tests/test_tc002_to_tc004_trace_closure.py")),
        ("CSS-CLAIM-SYNTHETIC-TRUTH", "Synthetic truth detection remains executable and production fallback is prohibited.", ("src/argos/control_panel/production_synthetic_truth_elimination.py", "src/argos/control_panel/synthetic_truth_quarantine.py"), ("Tests/test_eoec_production_synthetic_truth_elimination.py", "Tests/test_eodh_synthetic_truth_quarantine.py")),
        ("CSS-CLAIM-EVIDENCE-INTEGRITY", "Certification evidence has current manifests and cannot satisfy certification from historical artifacts.", ("src/argos/control_panel/cr_audit_closure.py",), ("Tests/test_cr6_cr7_certification_artifacts.py",)),
        ("CSS-CLAIM-DRIFT-GUARD", "Certification drift detection compares candidate repository truth against immutable baseline evidence.", ("src/argos/control_panel/continuous_constitutional_certification.py",), ("Tests/test_css_continuous_certification.py",)),
    )
    indexed_paths = {item["path"] for item in index["items"]}
    for claim_id, description, implementations, tests in claim_specs:
        missing_impl = tuple(path for path in implementations if path not in indexed_paths)
        missing_tests = tuple(path for path in tests if path not in indexed_paths)
        status = CSSVerdict.FAIL.value if missing_impl or missing_tests else CSSVerdict.PASS.value
        claims.append(
            {
                "claimId": claim_id,
                "description": description,
                "responsibleImplementation": implementations,
                "supportingTests": tests,
                "supportingRuntimeEvidence": _claim_evidence_refs(root, claim_id),
                "evidenceFreshness": "CURRENT_CANDIDATE_REQUIRED",
                "dependencies": implementations + tests,
                "verificationStatus": status,
                "findings": tuple(f"missing implementation {path}" for path in missing_impl) + tuple(f"missing test {path}" for path in missing_tests),
            }
        )
    blockers = tuple(f"{claim['claimId']}:{finding}" for claim in claims for finding in claim["findings"])
    return {
        "repositoryCommit": head,
        "claimCount": len(claims),
        "passingClaimCount": sum(1 for claim in claims if claim["verificationStatus"] == CSSVerdict.PASS.value),
        "blockingFindingCount": len(blockers),
        "blockingFindings": blockers,
        "claims": tuple(claims),
        "registryHash": _stable_hash(claims),
    }


def build_css_evidence_manifest(repo_root: str | Path = ".", *, commit: str = "WORKTREE") -> dict[str, Any]:
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    inventory = certification_artifact_inventory(root, current_commit=head)
    generator_paths = tuple(sorted(path for path in (root / "Scripts").glob("generate_*evidence.py")))
    generators = tuple({"path": _rel(root, path), "sha256": _file_hash(path), "command": f"py -3 {path.relative_to(root)}"} for path in generator_paths)
    return {
        "repositoryCommit": head,
        "historicalArtifactInventory": inventory,
        "generatorCount": len(generators),
        "generators": generators,
        "freshnessPolicy": "Evidence must embed the current full commit and be regenerated by a tracked generator for this candidate.",
        "manifestHash": _stable_hash((inventory["artifactCount"], inventory["mixedCandidateCount"], generators)),
    }


def detect_certification_drift(
    repo_root: str | Path = ".",
    *,
    commit: str = "WORKTREE",
    repository_index: dict[str, Any] | None = None,
    evidence_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    index = repository_index or build_repository_truth_index(root, commit=head)
    manifest = evidence_manifest or build_css_evidence_manifest(root, commit=head)
    baseline = _load_css_baseline(root)
    synthetic = synthetic_truth_inventory(root)
    trace_findings = constitutional_trace_findings(root)
    regressions: list[str] = []
    blocking: list[str] = []
    if baseline is None:
        blocking.append("No immutable CSS certified baseline is present.")
    else:
        if baseline.get("repositoryTruthIndexHash") != index["indexHash"]:
            regressions.append("Repository truth index differs from certified baseline.")
        if baseline.get("evidenceManifestHash") != manifest["manifestHash"]:
            regressions.append("Evidence manifest differs from certified baseline.")
    if synthetic["unsafeFallbacks"]:
        regressions.append("Unsafe synthetic fallback remains reachable by current provider configuration.")
    if manifest["historicalArtifactInventory"]["mixedCandidateCount"] or manifest["historicalArtifactInventory"]["unknownIdentityCount"]:
        blocking.append("Historical evidence contains mixed or unknown candidate identities.")
    if trace_findings:
        blocking.append("Constitutional trace findings require review before CSS PASS.")
    return {
        "repositoryCommit": head,
        "baselinePresent": baseline is not None,
        "baseline": baseline or {},
        "candidateRepositoryTruthIndexHash": index["indexHash"],
        "candidateEvidenceManifestHash": manifest["manifestHash"],
        "syntheticTruthFindingCount": synthetic["candidateCount"],
        "constitutionalTraceFindingCount": len(trace_findings),
        "regressions": tuple(regressions),
        "blockingFindings": tuple(blocking),
        "verdict": CSSVerdict.FAIL.value if regressions or blocking else CSSVerdict.PASS.value,
        "driftHash": _stable_hash((head, index["indexHash"], manifest["manifestHash"], regressions, blocking)),
    }


def _css_prerequisite_blockers(preflight: dict[str, Any], cr7: dict[str, Any], cr10: dict[str, Any]) -> tuple[str, ...]:
    blockers = []
    if preflight.get("verdict") != "PASS":
        blockers.append("Candidate preflight is not PASS.")
    if cr7.get("verdict") != CRVerdict.PASS.value:
        blockers.append("CR-7 canonical full-suite certification is not PASS.")
    if cr10.get("verdict") != CRVerdict.PASS.value:
        blockers.append("CR-10 Controlled Paper Candidate qualification is not PASS.")
    if not cr10.get("paperCandidateQualification", {}).get("qualified"):
        blockers.append("Controlled Paper Candidate qualification is absent.")
    return tuple(blockers)


def _pipeline_stage(stage_id: str, name: str, findings: Iterable[str], evidence_refs: Iterable[str]) -> CSSStageResult:
    finding_tuple = tuple(dict.fromkeys(findings))
    evidence_tuple = tuple(evidence_refs)
    verdict = CSSVerdict.FAIL if finding_tuple else CSSVerdict.PASS
    return CSSStageResult(stage_id, name, verdict, evidence_tuple, finding_tuple, _stable_hash((stage_id, finding_tuple, evidence_tuple)))


def _verification_task_catalog() -> tuple[dict[str, Any], ...]:
    tasks = (
        ("repository-integrity", "Repository Truth", ("candidate identity", "required modules", "hash identity")),
        ("build-integrity", "Build Truth", ("compileall", "dependency identity", "immutable source")),
        ("static-constitutional-analysis", "Constitutional Boundaries", ("LAW VII", "authority", "ownership", "provenance")),
        ("synthetic-truth-analysis", "Synthetic Truth Prohibition", ("placeholders", "mock production paths", "forced PASS", "suppressed failures")),
        ("bridge-fidelity", "Canonical Bridge Fidelity", ("bridge denominator", "dynamic traces", "destination acceptance")),
        ("evidence-integrity", "Evidence Truth", ("fresh manifests", "current commit", "generator hashes")),
        ("drift-detection", "Certification Drift", ("baseline", "candidate delta", "regression classification")),
        ("final-verdict", "Fail-Closed Decision", ("all stages pass", "no missing evidence", "no unknowns")),
    )
    return tuple({"taskId": task_id, "domain": domain, "checks": checks, "mayModifyRuntime": False, "failClosed": True} for task_id, domain, checks in tasks)


def _associated_tests(root: Path, rel: str) -> tuple[str, ...]:
    stem = Path(rel).stem
    normalized = stem.replace("_", "")
    tests = []
    for path in sorted((root / "Tests").glob("test*.py")):
        if stem in path.stem or normalized in path.stem.replace("_", ""):
            tests.append(_rel(root, path))
    return tuple(tests[:20])


def _associated_evidence(root: Path, rel: str) -> tuple[str, ...]:
    stem = Path(rel).stem.lower().replace("_", "")
    evidence = []
    for base in (root / "Documentation", root / "outputs"):
        if not base.exists():
            continue
        for path in sorted(base.glob("*Evidence*/*.json")):
            haystack = f"{path.name} {path.parent.name}".lower().replace("_", "")
            if stem in haystack:
                evidence.append(_rel(root, path))
    return tuple(evidence[:20])


def _claim_evidence_refs(root: Path, claim_id: str) -> tuple[str, ...]:
    mapping = {
        "CSS-CLAIM-CANDIDATE-IDENTITY": ("outputs/cr10_preflight_after_operational_campaign_tooling/preflight.json",),
        "CSS-CLAIM-BRIDGE-FIDELITY": ("outputs/cr5_constitutional_trace/constitutional_trace_campaign.json",),
        "CSS-CLAIM-SYNTHETIC-TRUTH": ("outputs/cr_series_audit/cr3_result.json",),
        "CSS-CLAIM-EVIDENCE-INTEGRITY": ("outputs/cr6_artifact_regeneration/candidate_consistency.json",),
        "CSS-CLAIM-DRIFT-GUARD": ("outputs/css_sustainment/drift_report.json",),
    }
    return tuple(path for path in mapping.get(claim_id, ()) if (root / path).exists())


def _load_css_baseline(root: Path) -> dict[str, Any] | None:
    path = root / "outputs" / "css_sustainment" / "certified_baseline.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _git(root: Path, *args: str) -> str:
    result = __import__("subprocess").run(("git", *args), cwd=root, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


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
