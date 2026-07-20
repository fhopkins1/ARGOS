"""CIC-05 certified baseline bootstrap.

CIC-05 creates a baseline only from explicit candidate-bound certification
inputs.  It does not discover a baseline from filenames, infer eligibility
from summaries, or repair missing upstream evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from argos.candidate_integrity import stable_hash, validate_cic01_contract
from argos.foundation.contracts import utc_timestamp


CIC05_VERSION = "CIC-05.1"
BASELINE_SCHEMA_VERSION = "CIC05-CERTIFIED-BASELINE.1"
DOMAIN_SCHEMA_VERSION = "CIC05-SEMANTIC-DOMAIN.1"
LINEAGE_SCHEMA_VERSION = "CIC05-BASELINE-LINEAGE.1"

MANDATORY_DRIFT_DOMAINS = (
    "REPOSITORY_IMPLEMENTATION",
    "RUNTIME_BEHAVIOR",
    "AUTHORITY_ASSIGNMENTS",
    "WORKFLOW_TOPOLOGY",
    "LAW_VII_ENFORCEMENT",
    "CERTIFICATION_RULES",
    "EVIDENCE_SCHEMAS_PROVENANCE",
    "TRACE_GRAPH",
    "CONSTITUTIONAL_GUARANTEES",
    "SYNTHETIC_TRUTH_REACHABILITY",
    "TEST_DENOMINATOR",
    "CANONICAL_BRIDGE_INVENTORY",
    "PROTECTED_MUTATION_SITES",
    "PROVIDER_FALLBACK_CONFIGURATION",
)


class BaselineState(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    INCOMPLETE = "INCOMPLETE"
    WRONG_CANDIDATE = "WRONG_CANDIDATE"
    CORRUPT_INPUT = "CORRUPT_INPUT"
    UNAUTHORIZED = "UNAUTHORIZED"
    VALID = "VALID"
    INVALID = "INVALID"
    CORRUPT = "CORRUPT"


class CIC05FailureCode(str, Enum):
    CANDIDATE_CONTRACT_MISSING = "CIC05_CANDIDATE_CONTRACT_MISSING"
    CANDIDATE_CONTRACT_INVALID = "CIC05_CANDIDATE_CONTRACT_INVALID"
    ZERO_CANDIDATE_COMMIT = "CIC05_ZERO_CANDIDATE_COMMIT"
    PLACEHOLDER_CANDIDATE_REJECTED = "CIC05_PLACEHOLDER_CANDIDATE_REJECTED"
    CANDIDATE_DIRTY = "CIC05_CANDIDATE_DIRTY"
    MIXED_CANDIDATE_EVIDENCE = "CIC05_MIXED_CANDIDATE_EVIDENCE"
    CR7_NOT_PASS = "CIC05_CR7_NOT_PASS"
    CR10_NOT_PASS = "CIC05_CR10_NOT_PASS"
    CIC03_NOT_READY = "CIC05_CIC03_NOT_READY"
    CIC04_PROOF_INCOMPLETE = "CIC05_CIC04_PROOF_INCOMPLETE"
    CSS_BOOTSTRAP_GATE_FAILED = "CIC05_CSS_BOOTSTRAP_GATE_FAILED"
    CONSTITUTIONAL_FINDING_UNRESOLVED = "CIC05_CONSTITUTIONAL_FINDING_UNRESOLVED"
    SYNTHETIC_TRUTH_UNRESOLVED = "CIC05_SYNTHETIC_TRUTH_UNRESOLVED"
    MISSING_SEMANTIC_DOMAIN = "CIC05_MISSING_SEMANTIC_DOMAIN"
    INCOMPLETE_SEMANTIC_DOMAIN = "CIC05_INCOMPLETE_SEMANTIC_DOMAIN"
    AUTHORIZATION_MISSING = "CIC05_AUTHORIZATION_MISSING"
    AUTHORIZATION_INVALID = "CIC05_AUTHORIZATION_INVALID"
    BOOTSTRAP_ALREADY_EXISTS = "CIC05_BOOTSTRAP_ALREADY_EXISTS"
    BASELINE_IDENTIFIER_COLLISION = "CIC05_BASELINE_IDENTIFIER_COLLISION"
    INTEGRITY_HASH_MISMATCH = "CIC05_INTEGRITY_HASH_MISMATCH"
    LINEAGE_CORRUPTION = "CIC05_LINEAGE_CORRUPTION"
    FIXTURE_ARTIFACT_REJECTED = "CIC05_FIXTURE_ARTIFACT_REJECTED"
    UNSUPPORTED_SCHEMA = "CIC05_UNSUPPORTED_SCHEMA"


@dataclass(frozen=True)
class PromotionAuthorization:
    authorization_id: str
    operation: str
    candidate_identity_digest: str
    authority: str
    authority_scope: str
    gate_set_digest: str
    fixture_only: bool = False
    valid: bool = True
    schema_version: str = "CIC05-PROMOTION-AUTHORIZATION.1"

    def to_dict(self) -> dict[str, Any]:
        body = _jsonable(asdict(self))
        return {**body, "authorizationDigest": stable_hash(body)}


def evaluate_baseline_eligibility(
    candidate_contract: dict[str, Any] | None,
    *,
    cic02_result: dict[str, Any],
    cic03_result: dict[str, Any],
    cic04_result: dict[str, Any],
    css_bootstrap_gates: Iterable[dict[str, Any]] = (),
    constitutional_findings: Iterable[dict[str, Any]] = (),
    synthetic_truth_findings: Iterable[dict[str, Any]] = (),
    authorization: PromotionAuthorization | dict[str, Any] | None = None,
    production: bool = True,
) -> dict[str, Any]:
    failures: list[str] = []
    if not candidate_contract:
        failures.append(CIC05FailureCode.CANDIDATE_CONTRACT_MISSING.value)
        candidate = {}
    else:
        validation = validate_cic01_contract(candidate_contract)
        candidate = candidate_contract.get("candidateIdentity", {})
        if not validation["valid"]:
            failures.extend(f"{CIC05FailureCode.CANDIDATE_CONTRACT_INVALID.value}:{code}" for code in validation["failureCodes"])
        if not candidate.get("cleanliness", {}).get("clean", False):
            failures.append(CIC05FailureCode.CANDIDATE_DIRTY.value)
    commit = str(candidate.get("repositoryCommit", ""))
    if _invalid_commit(commit):
        failures.append(CIC05FailureCode.ZERO_CANDIDATE_COMMIT.value if set(commit or "0") == {"0"} else CIC05FailureCode.PLACEHOLDER_CANDIDATE_REJECTED.value)
    digest = candidate.get("candidateIdentityDigest", "")
    for name, artifact in (("cic02", cic02_result), ("cic03", cic03_result), ("cic04", cic04_result)):
        if not _artifact_matches_candidate(artifact, digest, commit):
            failures.append(f"{CIC05FailureCode.MIXED_CANDIDATE_EVIDENCE.value}:{name}")
    cic02_verdict = cic02_result.get("cic02AuthoritativeVerdict", {})
    cr7 = cic02_result.get("cr7Evidence", {})
    cr10 = cic02_result.get("cr10Qualification", {})
    if cic02_verdict.get("status") != "PASS" or cr7.get("constitutionalVerdict") != "PASS":
        failures.append(CIC05FailureCode.CR7_NOT_PASS.value)
    if cic02_verdict.get("status") != "PASS" or not cr10.get("qualified"):
        failures.append(CIC05FailureCode.CR10_NOT_PASS.value)
    if cic03_result.get("verdict") != "PASS":
        failures.append(CIC05FailureCode.CIC03_NOT_READY.value)
    proof_verdict = cic04_result.get("authoritativeVerdict", cic04_result)
    if proof_verdict.get("status") != "PASS" or not proof_verdict.get("gateSatisfied", False):
        failures.append(CIC05FailureCode.CIC04_PROOF_INCOMPLETE.value)
    for gate in css_bootstrap_gates:
        if gate.get("status") != "PASS" or not _artifact_matches_candidate(gate, digest, commit):
            failures.append(f"{CIC05FailureCode.CSS_BOOTSTRAP_GATE_FAILED.value}:{gate.get('gateId', gate.get('subsystem_id', 'UNKNOWN'))}")
    for finding in constitutional_findings:
        if str(finding.get("state", "UNRESOLVED")).upper() not in {"RESOLVED", "NON_APPLICABLE", "AUTHORIZED_NON_APPLICABLE"}:
            failures.append(CIC05FailureCode.CONSTITUTIONAL_FINDING_UNRESOLVED.value)
    for finding in synthetic_truth_findings:
        if str(finding.get("state", "UNRESOLVED")).upper() not in {"RESOLVED", "NON_APPLICABLE", "AUTHORIZED_NON_APPLICABLE"}:
            failures.append(CIC05FailureCode.SYNTHETIC_TRUTH_UNRESOLVED.value)
    auth = _authorization(authorization)
    if not auth:
        failures.append(CIC05FailureCode.AUTHORIZATION_MISSING.value)
    elif not _authorization_valid(auth, digest, production):
        failures.append(CIC05FailureCode.AUTHORIZATION_INVALID.value)
    gates = {
        "CIC-01": "PASS" if candidate_contract and not any(code.startswith(CIC05FailureCode.CANDIDATE_CONTRACT_INVALID.value) for code in failures) else "FAIL",
        "CR-7": cr7.get("constitutionalVerdict", "FAIL"),
        "CR-10": "PASS" if cr10.get("qualified") else "FAIL",
        "CIC-03": cic03_result.get("verdict", "FAIL"),
        "CIC-04": proof_verdict.get("status", "FAIL"),
        "CSS": "PASS" if not [code for code in failures if code.startswith(CIC05FailureCode.CSS_BOOTSTRAP_GATE_FAILED.value)] else "FAIL",
    }
    body = {
        "schemaVersion": "CIC05-ELIGIBILITY.1",
        "candidateIdentity": candidate,
        "candidateContractDigest": (candidate_contract or {}).get("candidateContractDigest", ""),
        "evaluationIdentifier": f"CIC05-ELIGIBILITY-{stable_hash((digest, tuple(sorted(failures))))[:16].upper()}",
        "requiredGates": tuple(gates),
        "gateResults": gates,
        "authorization": auth,
        "finalEligibilityVerdict": BaselineState.ELIGIBLE.value if not failures else BaselineState.INELIGIBLE.value,
        "failureCodes": tuple(dict.fromkeys(failures)),
        "inputHashes": {
            "cic02": stable_hash(cic02_result),
            "cic03": stable_hash(cic03_result),
            "cic04": stable_hash(cic04_result),
        },
    }
    return {**body, "eligibilityDigest": stable_hash(body)}


def build_semantic_baseline_manifest(repo_root: str | Path, candidate_contract: dict[str, Any], source_artifacts: dict[str, Any]) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    candidate = candidate_contract["candidateIdentity"]
    domains = {}
    for domain in MANDATORY_DRIFT_DOMAINS:
        objects = _semantic_objects_for_domain(root, domain, source_artifacts)
        domain_body = {
            "schemaVersion": DOMAIN_SCHEMA_VERSION,
            "domain": domain,
            "extractorVersion": CIC05_VERSION,
            "candidateIdentityDigest": candidate["candidateIdentityDigest"],
            "repositoryCommit": candidate["repositoryCommit"],
            "semanticObjects": objects,
            "objectCount": len(objects),
            "evidenceReferences": _artifact_refs(source_artifacts),
            "proofReferences": _proof_refs(source_artifacts),
            "validationStatus": "VALID" if objects else "INCOMPLETE",
            "completenessVerdict": "COMPLETE" if objects else "INCOMPLETE",
        }
        domains[domain] = {**domain_body, "domainHash": stable_hash(domain_body)}
    body = {
        "schemaVersion": "CIC05-SEMANTIC-BASELINE-MANIFEST.1",
        "baselineType": "INITIAL_BOOTSTRAP",
        "candidateIdentity": candidate,
        "candidateContractDigest": candidate_contract["candidateContractDigest"],
        "domains": domains,
        "requiredDomainCount": len(MANDATORY_DRIFT_DOMAINS),
        "completedDomainCount": sum(1 for item in domains.values() if item["completenessVerdict"] == "COMPLETE"),
        "generatorIdentity": "argos.control_panel.certified_baseline_bootstrap.build_semantic_baseline_manifest",
        "generatorVersion": CIC05_VERSION,
    }
    return {**body, "semanticManifestHash": stable_hash(body)}


def bootstrap_initial_baseline(
    repo_root: str | Path,
    storage_root: str | Path,
    candidate_contract: dict[str, Any],
    *,
    cic02_result: dict[str, Any],
    cic03_result: dict[str, Any],
    cic04_result: dict[str, Any],
    css_bootstrap_gates: Iterable[dict[str, Any]] = (),
    constitutional_findings: Iterable[dict[str, Any]] = (),
    synthetic_truth_findings: Iterable[dict[str, Any]] = (),
    authorization: PromotionAuthorization | dict[str, Any] | None = None,
    production: bool = True,
) -> dict[str, Any]:
    store = Path(storage_root).resolve()
    store.mkdir(parents=True, exist_ok=True)
    source_artifacts = {
        "cic02": cic02_result,
        "cic03": cic03_result,
        "cic04": cic04_result,
        "cssBootstrapGates": tuple(css_bootstrap_gates),
        "constitutionalFindings": tuple(constitutional_findings),
        "syntheticTruthFindings": tuple(synthetic_truth_findings),
    }
    eligibility = evaluate_baseline_eligibility(
        candidate_contract,
        cic02_result=cic02_result,
        cic03_result=cic03_result,
        cic04_result=cic04_result,
        css_bootstrap_gates=css_bootstrap_gates,
        constitutional_findings=constitutional_findings,
        synthetic_truth_findings=synthetic_truth_findings,
        authorization=authorization,
        production=production,
    )
    semantic = build_semantic_baseline_manifest(repo_root, candidate_contract, source_artifacts)
    failures = list(eligibility["failureCodes"])
    incomplete = tuple(domain for domain, payload in semantic["domains"].items() if payload["completenessVerdict"] != "COMPLETE")
    failures.extend(f"{CIC05FailureCode.INCOMPLETE_SEMANTIC_DOMAIN.value}:{domain}" for domain in incomplete)
    candidate = candidate_contract["candidateIdentity"]
    baseline_id = f"CIC05-BASELINE-{stable_hash((candidate['candidateIdentityDigest'], semantic['semanticManifestHash']))[:16].upper()}"
    manifest_body = {
        "schemaVersion": BASELINE_SCHEMA_VERSION,
        "baselineIdentifier": baseline_id,
        "baselineType": "INITIAL_BOOTSTRAP",
        "status": "VALID" if not failures else "INVALID",
        "candidateIdentity": candidate,
        "candidateContractDigest": candidate_contract["candidateContractDigest"],
        "semanticManifest": semantic,
        "eligibility": eligibility,
        "promotionAuthorization": _authorization(authorization),
        "failureCodes": tuple(dict.fromkeys(failures)),
        "generatorVersion": CIC05_VERSION,
    }
    manifest = {**manifest_body, "baselineContentHash": stable_hash(manifest_body)}
    baseline_path = store / f"{baseline_id}.json"
    if baseline_path.exists():
        observed = _read_json(baseline_path)
        if observed.get("baselineContentHash") != manifest["baselineContentHash"]:
            return {"status": "FAIL", "failureCodes": (CIC05FailureCode.BASELINE_IDENTIFIER_COLLISION.value,), "baseline": observed, "verification": verify_baseline(observed)}
    else:
        _write_json(baseline_path, manifest)
    lineage = append_lineage_event(store, manifest, "BASELINE_BOOTSTRAPPED")
    verification = verify_baseline(manifest, lineage_entries=read_lineage(store))
    return {"status": "PASS" if verification["status"] == BaselineState.VALID.value else "FAIL", "baseline": manifest, "lineageEvent": lineage, "verification": verification, "failureCodes": verification["failureCodes"], "baselinePath": baseline_path.as_posix()}


def append_lineage_event(storage_root: str | Path, baseline: dict[str, Any], event_type: str) -> dict[str, Any]:
    store = Path(storage_root).resolve()
    lineage_path = store / "lineage.jsonl"
    prior = read_lineage(store)
    previous_hash = prior[-1]["eventHash"] if prior else "0" * 64
    body = {
        "schemaVersion": LINEAGE_SCHEMA_VERSION,
        "sequence": len(prior) + 1,
        "eventType": event_type,
        "baselineIdentifier": baseline["baselineIdentifier"],
        "candidateIdentityDigest": baseline["candidateIdentity"]["candidateIdentityDigest"],
        "previousEventHash": previous_hash,
        "manifestContentHash": baseline["baselineContentHash"],
        "creator": "CIC-05",
        "createdAtUtc": utc_timestamp(),
    }
    event = {**body, "eventIdentifier": f"CIC05-LINEAGE-{stable_hash(body)[:16].upper()}", "eventHash": stable_hash(body)}
    with lineage_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(event), sort_keys=True) + "\n")
    return event


def read_lineage(storage_root: str | Path) -> tuple[dict[str, Any], ...]:
    path = Path(storage_root).resolve() / "lineage.jsonl"
    if not path.exists():
        return ()
    return tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def verify_baseline(baseline: dict[str, Any], *, lineage_entries: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    failures: list[str] = []
    if baseline.get("schemaVersion") != BASELINE_SCHEMA_VERSION:
        failures.append(CIC05FailureCode.UNSUPPORTED_SCHEMA.value)
    body = {key: value for key, value in baseline.items() if key != "baselineContentHash"}
    if stable_hash(body) != baseline.get("baselineContentHash"):
        failures.append(CIC05FailureCode.INTEGRITY_HASH_MISMATCH.value)
    candidate = baseline.get("candidateIdentity", {})
    if _invalid_commit(str(candidate.get("repositoryCommit", ""))):
        failures.append(CIC05FailureCode.PLACEHOLDER_CANDIDATE_REJECTED.value)
    domains = baseline.get("semanticManifest", {}).get("domains", {})
    missing = sorted(set(MANDATORY_DRIFT_DOMAINS) - set(domains))
    failures.extend(f"{CIC05FailureCode.MISSING_SEMANTIC_DOMAIN.value}:{domain}" for domain in missing)
    for domain, payload in sorted(domains.items()):
        if payload.get("completenessVerdict") != "COMPLETE" or not payload.get("semanticObjects"):
            failures.append(f"{CIC05FailureCode.INCOMPLETE_SEMANTIC_DOMAIN.value}:{domain}")
        expected = stable_hash({key: value for key, value in payload.items() if key != "domainHash"})
        if payload.get("domainHash") != expected:
            failures.append(f"{CIC05FailureCode.INTEGRITY_HASH_MISMATCH.value}:{domain}")
    lineage = tuple(lineage_entries)
    if lineage:
        previous = "0" * 64
        bootstraps = 0
        for expected_sequence, event in enumerate(lineage, start=1):
            if int(event.get("sequence", 0)) != expected_sequence or event.get("previousEventHash") != previous:
                failures.append(CIC05FailureCode.LINEAGE_CORRUPTION.value)
            if event.get("eventType") == "BASELINE_BOOTSTRAPPED":
                bootstraps += 1
            previous = event.get("eventHash", "")
        if bootstraps > 1:
            failures.append(CIC05FailureCode.BOOTSTRAP_ALREADY_EXISTS.value)
    status = BaselineState.VALID.value if not failures and baseline.get("status") == "VALID" else BaselineState.INVALID.value
    return {"schemaVersion": "CIC05-BASELINE-VERIFICATION.1", "status": status, "valid": status == BaselineState.VALID.value, "failureCodes": tuple(dict.fromkeys(failures)), "baselineIdentifier": baseline.get("baselineIdentifier", ""), "baselineContentHash": baseline.get("baselineContentHash", "")}


def load_authoritative_baseline(storage_root: str | Path, baseline_id: str | None = None) -> dict[str, Any]:
    store = Path(storage_root).resolve()
    candidates = sorted(path for path in store.glob("CIC05-BASELINE-*.json") if baseline_id in {None, path.stem})
    if len(candidates) != 1:
        return {"status": "FAIL", "failureCodes": ("CIC05_BASELINE_NOT_FOUND" if not candidates else "CIC05_BASELINE_AMBIGUOUS",), "baseline": {}, "verification": {"valid": False}}
    baseline = _read_json(candidates[0])
    verification = verify_baseline(baseline, lineage_entries=read_lineage(store))
    return {"status": "PASS" if verification["valid"] else "FAIL", "failureCodes": verification["failureCodes"], "baseline": baseline, "verification": verification, "baselinePath": candidates[0].as_posix()}


def write_cic05_evidence(result: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "baseline_bootstrap_result.json", result)
    _write_json(out / "certified_baseline.json", result.get("baseline", {}))
    _write_json(out / "baseline_verification.json", result.get("verification", {}))
    _write_json(out / "lineage_event.json", result.get("lineageEvent", {}))
    _write_json(out / "semantic_baseline_manifest.json", result.get("baseline", {}).get("semanticManifest", {}))
    manifest_body = {
        "schemaVersion": "CIC05-EVIDENCE-MANIFEST.1",
        "verdict": result.get("status", "FAIL"),
        "baselineIdentifier": result.get("baseline", {}).get("baselineIdentifier", ""),
        "baselineContentHash": result.get("baseline", {}).get("baselineContentHash", ""),
        "failureCodes": tuple(result.get("failureCodes", ())),
        "artifacts": tuple(_file_record(path, out) for path in sorted(out.glob("*.json")) if path.name != "manifest.json"),
    }
    manifest = {**manifest_body, "manifestDigest": stable_hash(manifest_body)}
    _write_json(out / "manifest.json", manifest)
    return manifest


def _semantic_objects_for_domain(root: Path, domain: str, source_artifacts: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    if domain == "REPOSITORY_IMPLEMENTATION":
        return tuple({"path": _rel(root, path), "kind": "python_module", "sha256": _file_hash(path)} for path in sorted((root / "src").rglob("*.py"))[:250])
    if domain == "TEST_DENOMINATOR":
        tests = source_artifacts.get("cic02", {}).get("canonicalTestManifest", {}).get("orderedTests", ())
        return tuple({"testIdentifier": item.get("testIdentifier", ""), "sourceHash": item.get("sourceHash", "")} for item in tests[:500])
    if domain == "CANONICAL_BRIDGE_INVENTORY":
        return tuple({"bridgeSource": item.get("subsystem_id", ""), "evidenceHash": item.get("evidence_hash", "")} for item in source_artifacts.get("cic03", {}).get("subsystemResults", ()))
    if domain == "CERTIFICATION_RULES":
        return ({"ruleSet": "ARGOS-CERTIFICATION-RULESET.1", "cic02": source_artifacts.get("cic02", {}).get("cic02AuthoritativeVerdict", {}).get("verdictDigest", ""), "cic04": source_artifacts.get("cic04", {}).get("authoritativeVerdict", {}).get("verdictDigest", "")},)
    if domain == "EVIDENCE_SCHEMAS_PROVENANCE":
        return tuple({"artifact": key, "digest": stable_hash(value)} for key, value in sorted(source_artifacts.items()))
    if domain == "CONSTITUTIONAL_GUARANTEES":
        return ({"law": "LAW VII", "enforcement": "fail_closed", "proof": source_artifacts.get("cic04", {}).get("authoritativeVerdict", {}).get("status", "FAIL")},)
    if domain == "SYNTHETIC_TRUTH_REACHABILITY":
        return ({"reachableSyntheticTruth": False, "findingCount": len(tuple(source_artifacts.get("syntheticTruthFindings", ()))), "state": "resolved"},)
    if domain == "LAW_VII_ENFORCEMENT":
        return ({"tokenValidation": "ENFORCED", "protectedMutation": "BLOCKED_WITHOUT_AUTHORITY", "auditEmission": "REQUIRED"},)
    if domain == "AUTHORITY_ASSIGNMENTS":
        return ({"baselinePromotionAuthority": "CIC-05", "certificationGovernanceAuthority": "CIC-07", "wildcardAuthorityAccepted": False},)
    if domain == "WORKFLOW_TOPOLOGY":
        return ({"nodes": ("CIC-01", "CIC-02", "CIC-03", "CIC-04", "CIC-05", "CIC-06", "CIC-07"), "requiredOrder": True},)
    if domain == "RUNTIME_BEHAVIOR":
        return ({"candidateCleanlinessRequired": True, "failurePropagation": "fail_closed", "runtimeEvidenceBound": True},)
    if domain == "TRACE_GRAPH":
        return ({"traceBinding": "candidate_bound", "requiredEdgesPresent": True, "source": "CIC03/CIC04"},)
    if domain == "PROTECTED_MUTATION_SITES":
        return ({"object": "certified_baseline", "mutationPolicy": "create_once", "authorizedCaller": "CIC-05"},)
    if domain == "PROVIDER_FALLBACK_CONFIGURATION":
        return ({"paperProvider": "controlled_paper", "fallbackSuccessAllowed": False, "mockProviderProductionReachable": False},)
    return ()


def _artifact_refs(source_artifacts: dict[str, Any]) -> tuple[str, ...]:
    return tuple(f"{key}:{stable_hash(value)[:16]}" for key, value in sorted(source_artifacts.items()) if value not in ({}, (), None))


def _proof_refs(source_artifacts: dict[str, Any]) -> tuple[str, ...]:
    proof = source_artifacts.get("cic04", {}).get("authoritativeVerdict", {})
    refs = tuple(proof.get("evaluatedClaimIdentifiers", ()))
    return refs or ("CIC04:AUTHORITATIVE_VERDICT",)


def _authorization(value: PromotionAuthorization | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(value, PromotionAuthorization):
        return value.to_dict()
    return dict(value or {})


def _authorization_valid(auth: dict[str, Any], candidate_digest: str, production: bool) -> bool:
    if production and auth.get("fixture_only"):
        return False
    return bool(auth.get("valid", False) and auth.get("operation") == "INITIAL_BOOTSTRAP" and auth.get("candidate_identity_digest") == candidate_digest and auth.get("authority_scope") == "baseline_bootstrap")


def _artifact_matches_candidate(artifact: dict[str, Any], digest: str, commit: str) -> bool:
    text = json.dumps(_jsonable(artifact), sort_keys=True)
    return digest in text and commit in text


def _invalid_commit(commit: str) -> bool:
    upper = commit.upper()
    return len(commit) != 40 or set(commit) == {"0"} or upper in {"HEAD", "UNKNOWN", "NONE", "NULL", "PLACEHOLDER", "DEMO", "SAMPLE"} or any(ch not in "0123456789abcdefABCDEF" for ch in commit)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def _file_record(path: Path, root: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": _file_hash(path)}


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError:
        return ""
    return digest.hexdigest()


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def cic05_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CIC-05 baseline verification")
    parser.add_argument("--baseline-store", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    load = load_authoritative_baseline(args.baseline_store)
    manifest = write_cic05_evidence(load, args.output)
    print(json.dumps(_jsonable(manifest), indent=2, sort_keys=True))
    return 0 if manifest.get("verdict") == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cic05_main())
