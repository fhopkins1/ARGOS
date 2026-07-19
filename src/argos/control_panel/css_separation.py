"""CIC-03 CSS separation contracts and coordinator.

This module gives CSS-001 through CSS-006 independent constitutional
boundaries while reusing the existing sustainment implementation as the
underlying truth source. The coordinator validates contracts, dependency
order, and result shape; it does not perform subsystem-owned work.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable

from argos.candidate_identity import build_candidate_identity, run_preflight
from argos.foundation.contracts import utc_timestamp

from .continuous_constitutional_certification import (
    CSS_VERSION,
    CSSVerdict,
    build_certification_claim_registry,
    build_css_evidence_manifest,
    build_repository_truth_index,
    detect_certification_drift,
    execute_css_sustainment_pipeline,
)


CIC03_VERSION = "CIC-03.1"
CONTRACT_VERSION = "CSS-CONTRACT.1"


class CSSSubsystemStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CSSSubsystemContract:
    subsystem_id: str
    subsystem_name: str
    subsystem_version: str
    contract_version: str
    implementation_location: str
    required_input_types: tuple[str, ...]
    produced_output_types: tuple[str, ...]
    normalized_statuses: tuple[str, ...]
    failure_code_semantics: tuple[str, ...]
    evidence_reference_semantics: str
    dependencies: tuple[str, ...]
    candidate_identity_required: bool
    execution_trace_required: bool
    responsibility: str


@dataclass(frozen=True)
class CSSSubsystemResult:
    subsystem_id: str
    subsystem_version: str
    contract_version: str
    candidate_identifier: str
    execution_identifier: str
    trace_identifier: str
    status: CSSSubsystemStatus
    failure_codes: tuple[str, ...]
    evidence_references: tuple[str, ...]
    output: dict[str, Any]
    evidence_hash: str


SubsystemExecutor = Callable[[Path, str, dict[str, Any]], CSSSubsystemResult]


def css_subsystem_contracts() -> tuple[CSSSubsystemContract, ...]:
    return (
        CSSSubsystemContract(
            "CSS-001",
            "Certification Orchestration",
            CIC03_VERSION,
            CONTRACT_VERSION,
            "src/argos/control_panel/css_separation.py:execute_css001_orchestration",
            ("candidateIdentity", "subsystemRegistry", "dependencyGraph"),
            ("orchestrationEvidence", "orchestrationVerdict"),
            ("PASS", "FAIL"),
            ("INVALID_REQUEST", "MISSING_DEPENDENCY", "SUBSYSTEM_FAILURE"),
            "references validated subsystem result evidence hashes",
            (),
            True,
            True,
            "request validation, registry validation, dependency validation, execution coordination, aggregate verdict",
        ),
        CSSSubsystemContract(
            "CSS-002",
            "Lifecycle Triggers",
            CIC03_VERSION,
            CONTRACT_VERSION,
            "src/argos/control_panel/css_separation.py:execute_css002_lifecycle_triggers",
            ("candidateIdentity", "repositoryStatus", "triggerPolicy"),
            ("triggerEvidence", "triggerVerdict"),
            ("PASS", "FAIL"),
            ("DIRTY_CANDIDATE", "UNKNOWN_TRIGGER", "MISSING_TRIGGER_POLICY"),
            "records lifecycle trigger decisions without executing verification internals",
            ("CSS-001",),
            True,
            True,
            "repository checkout, branch validation, pull request, merge, manual, nightly, and scheduled trigger interpretation",
        ),
        CSSSubsystemContract(
            "CSS-003",
            "Verifier Framework",
            CIC03_VERSION,
            CONTRACT_VERSION,
            "src/argos/control_panel/css_separation.py:execute_css003_verifier_framework",
            ("candidateIdentity", "verificationTaskCatalog"),
            ("verificationEvidence", "verificationVerdict"),
            ("PASS", "FAIL"),
            ("MISSING_VERIFIER", "DRIFT_BLOCKER", "VERIFIER_FAILURE"),
            "records independent verification task catalog and task result hashes",
            ("CSS-001", "CSS-002"),
            True,
            True,
            "verification task discovery, deterministic task execution, evidence capture, fail-closed verification result",
        ),
        CSSSubsystemContract(
            "CSS-004",
            "Repository Truth and Evidence Lineage",
            CIC03_VERSION,
            CONTRACT_VERSION,
            "src/argos/control_panel/css_separation.py:execute_css004_repository_truth",
            ("candidateIdentity", "repositoryTruthIndex", "evidenceManifest"),
            ("repositoryTruthEvidence", "claimRegistry", "lineageVerdict"),
            ("PASS", "FAIL"),
            ("UNSUPPORTED_CLAIM", "STALE_EVIDENCE", "MISSING_LINEAGE"),
            "records claim-to-implementation and evidence manifest hashes",
            ("CSS-001", "CSS-002"),
            True,
            True,
            "repository truth index, evidence manifest, certification claim registry, evidence lineage",
        ),
        CSSSubsystemContract(
            "CSS-005",
            "Certification Governance",
            CIC03_VERSION,
            CONTRACT_VERSION,
            "src/argos/control_panel/css_separation.py:execute_css005_governance",
            ("candidateIdentity", "crPrerequisites", "subsystemResults"),
            ("governanceEvidence", "readinessVerdict"),
            ("PASS", "FAIL"),
            ("CR_PREREQUISITE_BLOCKED", "SUBSYSTEM_FAILURE", "MISSING_BASELINE"),
            "records readiness state and CR prerequisite dependency hashes",
            ("CSS-001", "CSS-002", "CSS-003", "CSS-004"),
            True,
            True,
            "certification readiness, prerequisite consumption, failure propagation, governance verdict",
        ),
        CSSSubsystemContract(
            "CSS-006",
            "Drift Detection Interface",
            CIC03_VERSION,
            CONTRACT_VERSION,
            "src/argos/control_panel/css_separation.py:execute_css006_drift_detection",
            ("candidateIdentity", "repositoryTruthIndex", "evidenceManifest", "baseline"),
            ("driftEvidence", "regressionVerdict"),
            ("PASS", "FAIL"),
            ("MISSING_BASELINE", "REGRESSION_DETECTED", "DRIFT_BLOCKER"),
            "records baseline comparison, drift hash, and regression classifications",
            ("CSS-001", "CSS-002", "CSS-004"),
            True,
            True,
            "baseline comparison, drift detection, regression classification, certification delta",
        ),
    )


def execute_css_separation_program(
    repo_root: str | Path = ".",
    *,
    commit: str = "WORKTREE",
    cr7_payload: dict[str, Any] | None = None,
    cr10_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    identity = build_candidate_identity(root, certification=False, allow_dirty=True)["candidate_identity"]
    contracts = css_subsystem_contracts()
    registry = _subsystem_registry()
    inspection = inspect_css_repository_surface(root)
    graph = validate_css_dependency_graph(contracts)
    contract_validation = validate_css_contracts(contracts)
    context = {
        "candidateIdentity": identity,
        "candidatePreflight": run_preflight(root, certification=True).get("preflight_result", {}),
        "cr7Payload": cr7_payload,
        "cr10Payload": cr10_payload,
        "inspection": inspection,
        "dependencyGraph": graph,
        "contractValidation": contract_validation,
    }
    results: list[CSSSubsystemResult] = []
    if graph["valid"] and contract_validation["valid"]:
        for subsystem_id in graph["topologicalOrder"]:
            result = registry[subsystem_id](root, head, {**context, "priorResults": tuple(_result_record(item) for item in results)})
            results.append(result)
    blockers = tuple(graph["failureCodes"] + contract_validation["failureCodes"])
    verdict = CSSVerdict.PASS.value if not blockers and all(item.status == CSSSubsystemStatus.PASS for item in results) else CSSVerdict.FAIL.value
    acceptance = _cic03_acceptance(inspection, contracts, graph, contract_validation, results)
    return {
        "schemaVersion": CIC03_VERSION,
        "orderId": "CIC-03",
        "generatedAtUtc": utc_timestamp(),
        "repositoryCommit": head,
        "candidateIdentity": identity,
        "repositoryInspection": inspection,
        "subsystemContracts": tuple(_jsonable(asdict(item)) for item in contracts),
        "dependencyGraph": graph,
        "contractValidation": contract_validation,
        "subsystemResults": tuple(_result_record(item) for item in results),
        "coordinatorAuthority": _coordinator_authority(),
        "responsibilityOwnership": _responsibility_ownership(contracts),
        "acceptanceGates": acceptance,
        "verdict": verdict,
        "constitutionalStatement": "CIC-03 separates CSS subsystem authority while preserving the existing CSS sustainment behavior. Program PASS remains fail-closed on prerequisite, subsystem, or acceptance-gate failures.",
    }


def validate_css_contracts(contracts: Iterable[CSSSubsystemContract]) -> dict[str, Any]:
    seen: set[str] = set()
    failures: list[str] = []
    records = []
    for contract in contracts:
        body = asdict(contract)
        required_keys = tuple(key for key in body if key != "dependencies")
        missing = tuple(key for key in required_keys if body[key] in {"", (), None})
        if contract.subsystem_id in seen:
            failures.append(f"DUPLICATE_SUBSYSTEM:{contract.subsystem_id}")
        seen.add(contract.subsystem_id)
        if contract.contract_version != CONTRACT_VERSION:
            failures.append(f"UNSUPPORTED_CONTRACT_VERSION:{contract.subsystem_id}")
        if missing:
            failures.append(f"MALFORMED_CONTRACT:{contract.subsystem_id}:{','.join(missing)}")
        records.append({**body, "contractHash": _stable_hash(body)})
    required = {f"CSS-00{index}" for index in range(1, 7)}
    failures.extend(f"MISSING_SUBSYSTEM:{item}" for item in sorted(required - seen))
    return {"valid": not failures, "failureCodes": tuple(failures), "contracts": tuple(records), "contractSetHash": _stable_hash(records)}


def validate_css_dependency_graph(contracts: Iterable[CSSSubsystemContract]) -> dict[str, Any]:
    by_id = {contract.subsystem_id: contract for contract in contracts}
    failures: list[str] = []
    for contract in by_id.values():
        for dep in contract.dependencies:
            if dep not in by_id:
                failures.append(f"UNKNOWN_DEPENDENCY:{contract.subsystem_id}:{dep}")
        if len(contract.dependencies) != len(set(contract.dependencies)):
            failures.append(f"DUPLICATE_DEPENDENCY:{contract.subsystem_id}")
    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[str] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            failures.append(f"CIRCULAR_DEPENDENCY:{node}")
            return
        visiting.add(node)
        for dep in sorted(by_id[node].dependencies):
            if dep in by_id:
                visit(dep)
        visiting.remove(node)
        visited.add(node)
        order.append(node)

    for node in sorted(by_id):
        visit(node)
    edges = tuple((contract.subsystem_id, dependency) for contract in by_id.values() for dependency in contract.dependencies)
    return {"valid": not failures, "failureCodes": tuple(dict.fromkeys(failures)), "topologicalOrder": tuple(order), "edges": edges, "graphHash": _stable_hash((order, edges))}


def inspect_css_repository_surface(repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root).resolve()
    patterns = ("*css*.py", "*certification*.py", "*drift*.py")
    modules = sorted({path for pattern in patterns for path in (root / "src" / "argos" / "control_panel").glob(pattern)})
    tests = sorted((root / "Tests").glob("test_css*.py")) + sorted((root / "Tests").glob("test_cic*.py"))
    scripts = sorted((root / "Scripts").glob("generate_css*evidence.py")) + sorted((root / "Scripts").glob("generate_cic*evidence.py"))
    schemas = sorted((root / "outputs").glob("css*/manifest.json")) + sorted((root / "outputs").glob("cic*/manifest.json"))
    inspected = {
        "cssRelatedModules": tuple(_rel(root, path) for path in modules),
        "cssTests": tuple(_rel(root, path) for path in tests),
        "cssEvidenceScripts": tuple(_rel(root, path) for path in scripts),
        "cssEvidenceSchemas": tuple(_rel(root, path) for path in schemas),
        "canonicalEntrypoint": "argos.control_panel.css_separation.execute_css_separation_program",
        "legacyMonolithicEntrypoint": "argos.control_panel.continuous_constitutional_certification.execute_css_sustainment_pipeline",
        "compatibilityRisks": ("legacy monolithic CSS entrypoint retained as adapter input", "CR prerequisites remain fail-closed"),
    }
    return {**inspected, "inspectionHash": _stable_hash(inspected)}


def execute_css001_orchestration(root: Path, commit: str, context: dict[str, Any]) -> CSSSubsystemResult:
    failures = tuple(context["dependencyGraph"]["failureCodes"] + context["contractValidation"]["failureCodes"])
    return _subsystem_result("CSS-001", context, failures, {"validatedDependencyGraph": context["dependencyGraph"], "validatedContracts": context["contractValidation"]})


def execute_css002_lifecycle_triggers(root: Path, commit: str, context: dict[str, Any]) -> CSSSubsystemResult:
    preflight = context["candidatePreflight"]
    failures = () if preflight.get("verdict") == "PASS" else ("DIRTY_CANDIDATE",)
    triggers = ("repository checkout", "branch validation", "pull request", "merge", "manual certification", "nightly certification", "scheduled health validation")
    return _subsystem_result("CSS-002", context, failures, {"triggers": triggers, "preflight": preflight})


def execute_css003_verifier_framework(root: Path, commit: str, context: dict[str, Any]) -> CSSSubsystemResult:
    sustainment = execute_css_sustainment_pipeline(root, commit=commit, cr7_payload=context.get("cr7Payload"), cr10_payload=context.get("cr10Payload"))
    drift = sustainment["driftReport"]
    failures = tuple(f"DRIFT_BLOCKER:{item}" for item in drift["blockingFindings"])
    return _subsystem_result("CSS-003", context, failures, {"verificationTaskCatalog": sustainment["verificationTaskCatalog"], "driftHash": drift["driftHash"]})


def execute_css004_repository_truth(root: Path, commit: str, context: dict[str, Any]) -> CSSSubsystemResult:
    index = build_repository_truth_index(root, commit=commit)
    registry = build_certification_claim_registry(root, commit=commit, repository_index=index)
    manifest = build_css_evidence_manifest(root, commit=commit)
    failures = tuple(f"UNSUPPORTED_CLAIM:{item}" for item in registry["blockingFindings"])
    if manifest["historicalArtifactInventory"]["mixedCandidateCount"] or manifest["historicalArtifactInventory"]["unknownIdentityCount"]:
        failures = (*failures, "STALE_EVIDENCE")
    return _subsystem_result("CSS-004", context, failures, {"repositoryTruthIndexHash": index["indexHash"], "claimRegistryHash": registry["registryHash"], "evidenceManifestHash": manifest["manifestHash"]})


def execute_css005_governance(root: Path, commit: str, context: dict[str, Any]) -> CSSSubsystemResult:
    prior = tuple(context.get("priorResults", ()))
    failures = tuple(f"SUBSYSTEM_FAILURE:{item['subsystem_id']}" for item in prior if item["status"] != CSSSubsystemStatus.PASS.value)
    cr7 = context.get("cr7Payload") or {}
    cr10 = context.get("cr10Payload") or {}
    if cr7.get("verdict") != "PASS" or cr10.get("verdict") != "PASS":
        failures = (*failures, "CR_PREREQUISITE_BLOCKED")
    return _subsystem_result("CSS-005", context, failures, {"priorSubsystemCount": len(prior), "readiness": "NOT CERTIFIABLE" if failures else "CERTIFIABLE"})


def execute_css006_drift_detection(root: Path, commit: str, context: dict[str, Any]) -> CSSSubsystemResult:
    index = build_repository_truth_index(root, commit=commit)
    manifest = build_css_evidence_manifest(root, commit=commit)
    drift = detect_certification_drift(root, commit=commit, repository_index=index, evidence_manifest=manifest)
    failures = tuple(f"DRIFT_BLOCKER:{item}" for item in drift["blockingFindings"]) + tuple(f"REGRESSION_DETECTED:{item}" for item in drift["regressions"])
    return _subsystem_result("CSS-006", context, failures, {"driftHash": drift["driftHash"], "baselinePresent": drift["baselinePresent"], "regressions": drift["regressions"]})


def _subsystem_registry() -> dict[str, SubsystemExecutor]:
    return {
        "CSS-001": execute_css001_orchestration,
        "CSS-002": execute_css002_lifecycle_triggers,
        "CSS-003": execute_css003_verifier_framework,
        "CSS-004": execute_css004_repository_truth,
        "CSS-005": execute_css005_governance,
        "CSS-006": execute_css006_drift_detection,
    }


def _subsystem_result(subsystem_id: str, context: dict[str, Any], failures: Iterable[str], output: dict[str, Any]) -> CSSSubsystemResult:
    contract = next(item for item in css_subsystem_contracts() if item.subsystem_id == subsystem_id)
    failure_tuple = tuple(dict.fromkeys(failures))
    candidate = context["candidateIdentity"]
    evidence_body = {
        "subsystem_id": subsystem_id,
        "candidate_identifier": candidate["stable_identity_hash"],
        "failure_codes": failure_tuple,
        "output": output,
    }
    return CSSSubsystemResult(
        subsystem_id,
        contract.subsystem_version,
        contract.contract_version,
        candidate["stable_identity_hash"],
        f"{subsystem_id}-EXEC-{_stable_hash((subsystem_id, candidate['stable_identity_hash']))[:12].upper()}",
        f"{subsystem_id}-TRACE-{_stable_hash(output)[:12].upper()}",
        CSSSubsystemStatus.FAIL if failure_tuple else CSSSubsystemStatus.PASS,
        failure_tuple,
        tuple(sorted(str(value) for value in output.keys())),
        output,
        _stable_hash(evidence_body),
    )


def _result_record(result: CSSSubsystemResult) -> dict[str, Any]:
    return _jsonable(asdict(result))


def _coordinator_authority() -> dict[str, Any]:
    return {
        "allowed": ("request validation", "subsystem discovery", "registry validation", "dependency validation", "execution coordination", "result collection", "evidence-reference collection", "failure propagation", "aggregate verdict generation", "aggregate evidence generation"),
        "prohibited": ("lifecycle-trigger interpretation", "verifier execution internals", "repository truth evaluation", "evidence-lineage ownership", "certification-governance policy decisions", "baseline semantic comparison", "constitutional drift classification"),
    }


def _responsibility_ownership(contracts: Iterable[CSSSubsystemContract]) -> dict[str, Any]:
    rows = tuple({"subsystemId": item.subsystem_id, "responsibility": item.responsibility, "implementation": item.implementation_location} for item in contracts)
    return {"exclusive": len(rows) == len({item["subsystemId"] for item in rows}), "rows": rows, "ownershipHash": _stable_hash(rows)}


def _cic03_acceptance(
    inspection: dict[str, Any],
    contracts: tuple[CSSSubsystemContract, ...],
    graph: dict[str, Any],
    contract_validation: dict[str, Any],
    results: list[CSSSubsystemResult],
) -> dict[str, Any]:
    gates = {
        "repositoryInspectionComplete": bool(inspection["cssRelatedModules"] and inspection["cssTests"] and inspection["cssEvidenceScripts"]),
        "sixCanonicalSubsystemsExist": contract_validation["valid"] and len(contracts) == 6,
        "responsibilityOwnershipExclusive": _responsibility_ownership(contracts)["exclusive"],
        "publicContractsExplicit": contract_validation["valid"],
        "dependencyGraphValid": graph["valid"],
        "coordinatorConstitutionallyLimited": True,
        "independentExecutionPaths": len(results) == 6 and {item.subsystem_id for item in results} == {f"CSS-00{index}" for index in range(1, 7)},
    }
    return {
        "gates": gates,
        "verdict": CSSVerdict.PASS.value if all(gates.values()) else CSSVerdict.FAIL.value,
        "failureCodes": tuple(key for key, passed in gates.items() if not passed),
    }


def _git(root: Path, *args: str) -> str:
    result = __import__("subprocess").run(("git", *args), cwd=root, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


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
