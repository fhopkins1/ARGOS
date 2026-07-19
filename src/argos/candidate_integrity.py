"""CIC-01 candidate integrity contracts and artifact binding.

The CIC-01 contract is the canonical certification input boundary.  It
describes one immutable Git candidate, rejects dirty or ambiguous inputs, and
binds evidence artifacts to a content-addressed snapshot instead of a branch
name or a mutable summary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Any, Iterable

from argos.foundation.contracts import utc_timestamp


CIC01_VERSION = "CIC-01.2"
CANDIDATE_IDENTITY_SCHEMA_VERSION = "CIC01-CANDIDATE-IDENTITY.1"
CANDIDATE_SNAPSHOT_SCHEMA_VERSION = "CIC01-CANDIDATE-SNAPSHOT.1"
INPUT_LOCK_SCHEMA_VERSION = "CIC01-INPUT-LOCK.1"
ARTIFACT_BINDING_SCHEMA_VERSION = "CIC01-ARTIFACT-BINDING.1"
EVIDENCE_MANIFEST_SCHEMA_VERSION = "CIC01-EVIDENCE-MANIFEST.1"

RELEVANT_UNTRACKED_PATTERNS = (
    "*.py",
    "*.pyi",
    "*.json",
    "*.toml",
    "*.yaml",
    "*.yml",
    "*.ini",
    "*.cfg",
    "*.ps1",
    "*.cmd",
    "*.bat",
    "*.sh",
    "Dockerfile",
    "docker-compose*.yml",
    "docker-compose*.yaml",
    "requirements*.txt",
    "pyproject.toml",
    "poetry.lock",
    "package*.json",
    "Scripts/**",
    "Tests/**",
    "src/**",
    "Documentation/**/*policy*",
    "Documentation/**/*schema*",
)

PERMITTED_UNTRACKED_PATTERNS = (
    "outputs/**",
    "audit_exports/**",
    "audit_work/**",
    "*.zip",
    "*.sha256",
    "*.log",
    ".pytest_cache/**",
    "__pycache__/**",
)


class CIC01FailureCode(str, Enum):
    IDENTITY_UNRESOLVED = "CIC01_CANDIDATE_IDENTITY_UNRESOLVED"
    TRACKED_STATE_DIRTY = "CIC01_TRACKED_STATE_DIRTY"
    INDEX_STATE_DIRTY = "CIC01_INDEX_STATE_DIRTY"
    RELEVANT_UNTRACKED_STATE_DIRTY = "CIC01_RELEVANT_UNTRACKED_STATE_DIRTY"
    UNTRACKED_RELEVANCE_AMBIGUOUS = "CIC01_UNTRACKED_RELEVANCE_AMBIGUOUS"
    SUBMODULE_STATE_DIRTY = "CIC01_SUBMODULE_STATE_DIRTY"
    SNAPSHOT_MISMATCH = "CIC01_SNAPSHOT_MISMATCH"
    INPUT_LOCK_MISMATCH = "CIC01_INPUT_LOCK_MISMATCH"
    CANDIDATE_MUTATED = "CIC01_CANDIDATE_MUTATED"
    ARTIFACT_IDENTITY_MISSING = "CIC01_ARTIFACT_IDENTITY_MISSING"
    ARTIFACT_IDENTITY_MISMATCH = "CIC01_ARTIFACT_IDENTITY_MISMATCH"
    MIXED_CANDIDATE_PACKAGE = "CIC01_MIXED_CANDIDATE_PACKAGE"
    EVIDENCE_OUTPUT_INSIDE_CANDIDATE = "CIC01_EVIDENCE_OUTPUT_INSIDE_CANDIDATE"
    IDENTITY_AGREEMENT_FAILED = "CIC01_IDENTITY_AGREEMENT_FAILED"
    ARTIFACT_TAMPER_DETECTED = "CIC01_ARTIFACT_TAMPER_DETECTED"


@dataclass(frozen=True)
class CIC01Rejection(Exception):
    code: CIC01FailureCode
    reason: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code.value, "reason": self.reason, "details": self.details}


def build_cic01_candidate_contract(
    repo_root: str | Path,
    *,
    baseline_identity: str = "ARGOS-CURRENT-BASELINE",
    ruleset_identity: str = "ARGOS-CERTIFICATION-RULESET.1",
    configuration_identity: str = "ARGOS-CERTIFICATION-CONFIG.1",
    evidence_schema_version: str = EVIDENCE_MANIFEST_SCHEMA_VERSION,
    require_clean: bool = True,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    identity = resolve_candidate_identity(root, require_clean=require_clean)
    snapshot = create_candidate_snapshot(root, identity)
    lock = create_certification_input_lock(
        identity,
        snapshot,
        baseline_identity=baseline_identity,
        ruleset_identity=ruleset_identity,
        configuration_identity=configuration_identity,
        evidence_schema_version=evidence_schema_version,
    )
    body = {
        "schemaVersion": "CIC01-CANDIDATE-CONTRACT.1",
        "cicImplementationVersion": CIC01_VERSION,
        "status": "PASS" if identity["cleanliness"]["clean"] else "FAIL",
        "candidateIdentity": identity,
        "candidateSnapshot": snapshot,
        "certificationInputLock": lock,
        "failureCodes": tuple(identity["cleanliness"]["failureCodes"]),
        "artifactBindingRequirements": {
            "requiredFields": (
                "candidateIdentityDigest",
                "repositoryCommit",
                "candidateSnapshotDigest",
                "certificationRunIdentifier",
                "inputLockIdentifier",
                "artifactSchemaVersion",
                "artifactType",
                "artifactDigest",
                "producer",
            )
        },
        "generatedAtUtc": utc_timestamp(),
    }
    return {**body, "candidateContractDigest": stable_hash(_contract_digest_body(body))}


def resolve_candidate_identity(repo_root: str | Path, *, require_clean: bool = True) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    try:
        commit = git(root, "rev-parse", "HEAD")
        tree = git(root, "rev-parse", f"{commit}^{{tree}}")
        parents = tuple(git(root, "show", "-s", "--format=%P", commit).split())
        object_format = git(root, "rev-parse", "--show-object-format")
    except Exception as exc:  # pragma: no cover - platform/git failure path
        raise CIC01Rejection(
            CIC01FailureCode.IDENTITY_UNRESOLVED,
            "Git candidate identity could not be resolved.",
            {"error": str(exc)},
        ) from exc
    tracked = tracked_status(root)
    untracked = relevant_untracked_status(root)
    submodules = submodule_status(root)
    lfs = lfs_pointer_status(root)
    cleanliness = cleanliness_result(tracked, untracked, submodules)
    if require_clean and not cleanliness["clean"]:
        raise CIC01Rejection(
            CIC01FailureCode.TRACKED_STATE_DIRTY
            if tracked["dirty"]
            else CIC01FailureCode.RELEVANT_UNTRACKED_STATE_DIRTY,
            "Candidate is not clean enough for certification.",
            cleanliness,
        )
    identity_defining = {
        "schemaVersion": CANDIDATE_IDENTITY_SCHEMA_VERSION,
        "repositoryIdentifier": repository_identifier(root),
        "gitObjectFormat": object_format,
        "repositoryCommit": commit,
        "commitTreeHash": tree,
        "parentCommitHashes": parents,
        "trackedStateDigest": stable_hash(tracked["identityDefining"]),
        "stagedIndexDigest": stable_hash(tracked["staged"]),
        "relevantUntrackedDigest": stable_hash(untracked["identityDefining"]),
        "submoduleDigest": stable_hash(submodules["identityDefining"]),
        "gitLfsDigest": stable_hash(lfs["identityDefining"]),
        "candidateSnapshotFormatVersion": CANDIDATE_SNAPSHOT_SCHEMA_VERSION,
        "identityGenerationToolVersion": CIC01_VERSION,
    }
    digest = stable_hash(identity_defining)
    return {
        **identity_defining,
        "candidateIdentityDigest": digest,
        "repositorySnapshotDigest": "",
        "stable_identity_hash": digest,
        "working_tree_clean": cleanliness["clean"],
        "repository_branch": git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "informational": {
            "headState": "detached" if git(root, "rev-parse", "--abbrev-ref", "HEAD") == "HEAD" else "branch",
            "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        },
        "environmentMetadata": {
            "pythonVersion": sys.version.split()[0],
            "pathDigest": stable_hash(root.as_posix().lower()),
        },
        "cleanliness": cleanliness,
        "trackedStatus": tracked,
        "relevantUntrackedStatus": untracked,
        "submoduleStatus": submodules,
        "gitLfsStatus": lfs,
        "generatedAtUtc": utc_timestamp(),
    }


def tracked_status(repo_root: Path) -> dict[str, Any]:
    raw = git(repo_root, "status", "--porcelain=v1", "-z", "--untracked-files=no")
    entries = tuple(item for item in raw.split("\0") if item)
    staged = tuple(sorted(item[3:] for item in entries if item[0] not in (" ", "?")))
    unstaged = tuple(sorted(item[3:] for item in entries if len(item) > 1 and item[1] not in (" ", "?")))
    conflicts = tuple(sorted(item[3:] for item in entries if item[:2] in {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}))
    return {
        "dirty": bool(staged or unstaged or conflicts),
        "staged": staged,
        "unstaged": unstaged,
        "conflicts": conflicts,
        "identityDefining": {"staged": staged, "unstaged": unstaged, "conflicts": conflicts},
    }


def relevant_untracked_status(repo_root: Path) -> dict[str, Any]:
    raw = git(repo_root, "ls-files", "--others", "--exclude-standard", "-z")
    paths = tuple(sorted(normalize_path(item) for item in raw.split("\0") if item))
    relevant = tuple(path for path in paths if matches_any(path, RELEVANT_UNTRACKED_PATTERNS))
    permitted = tuple(path for path in paths if path not in relevant and matches_any(path, PERMITTED_UNTRACKED_PATTERNS))
    ambiguous = tuple(path for path in paths if path not in relevant and path not in permitted)
    return {
        "clean": not relevant and not ambiguous,
        "relevant": relevant,
        "permitted": permitted,
        "ambiguous": ambiguous,
        "policy": {
            "relevantPatterns": RELEVANT_UNTRACKED_PATTERNS,
            "permittedPatterns": PERMITTED_UNTRACKED_PATTERNS,
            "unknownPolicy": "fail_closed",
        },
        "identityDefining": {"relevant": relevant, "ambiguous": ambiguous},
    }


def submodule_status(repo_root: Path) -> dict[str, Any]:
    gitmodules = repo_root / ".gitmodules"
    if not gitmodules.exists():
        return {"present": False, "dirty": False, "records": (), "identityDefining": ()}
    raw = git(repo_root, "submodule", "status", "--recursive")
    records = tuple(line.strip() for line in raw.splitlines() if line.strip())
    dirty = any(line[:1] in {"+", "-", "U"} for line in records)
    return {"present": True, "dirty": dirty, "records": records, "identityDefining": records}


def lfs_pointer_status(repo_root: Path) -> dict[str, Any]:
    attrs = tuple(sorted(path.as_posix() for path in repo_root.glob("**/.gitattributes") if ".git/" not in path.as_posix()))
    records: list[dict[str, str]] = []
    for rel in tracked_files(repo_root):
        path = repo_root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if text.startswith("version https://git-lfs.github.com/spec/"):
            records.append({"path": rel, "pointerSha256": stable_hash(text)})
    return {"attributes": attrs, "pointers": tuple(records), "identityDefining": {"attributes": attrs, "pointers": tuple(records)}}


def cleanliness_result(tracked: dict[str, Any], untracked: dict[str, Any], submodules: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if tracked["conflicts"]:
        failures.append(CIC01FailureCode.TRACKED_STATE_DIRTY.value)
    if tracked["staged"]:
        failures.append(CIC01FailureCode.INDEX_STATE_DIRTY.value)
    if tracked["unstaged"]:
        failures.append(CIC01FailureCode.TRACKED_STATE_DIRTY.value)
    if untracked["relevant"]:
        failures.append(CIC01FailureCode.RELEVANT_UNTRACKED_STATE_DIRTY.value)
    if untracked["ambiguous"]:
        failures.append(CIC01FailureCode.UNTRACKED_RELEVANCE_AMBIGUOUS.value)
    if submodules["dirty"]:
        failures.append(CIC01FailureCode.SUBMODULE_STATE_DIRTY.value)
    return {"clean": not failures, "failureCodes": tuple(dict.fromkeys(failures))}


def create_candidate_snapshot(repo_root: str | Path, candidate_identity: dict[str, Any]) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    entries = []
    for rel in tracked_files(root):
        path = root / rel
        stat = path.lstat()
        entries.append(
            {
                "path": rel,
                "mode": git(root, "ls-files", "-s", rel).split()[0],
                "size": stat.st_size,
                "sha256": file_hash(path) if path.is_file() else "",
                "symlinkTarget": os.readlink(path) if path.is_symlink() else "",
                "executable": bool(stat.st_mode & 0o111),
            }
        )
    entries = sorted(entries, key=lambda item: item["path"])
    body = {
        "schemaVersion": CANDIDATE_SNAPSHOT_SCHEMA_VERSION,
        "candidateIdentityDigest": candidate_identity["candidateIdentityDigest"],
        "repositoryCommit": candidate_identity["repositoryCommit"],
        "commitTreeHash": candidate_identity["commitTreeHash"],
        "fileCount": len(entries),
        "files": tuple(entries),
    }
    digest = stable_hash(body)
    return {**body, "candidateSnapshotDigest": digest, "repositorySnapshotDigest": digest}


def create_certification_input_lock(
    candidate_identity: dict[str, Any],
    candidate_snapshot: dict[str, Any],
    *,
    baseline_identity: str,
    ruleset_identity: str,
    configuration_identity: str,
    evidence_schema_version: str,
    invocation_parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = {
        "schemaVersion": INPUT_LOCK_SCHEMA_VERSION,
        "candidateIdentityDigest": candidate_identity["candidateIdentityDigest"],
        "repositoryCommit": candidate_identity["repositoryCommit"],
        "candidateSnapshotDigest": candidate_snapshot["candidateSnapshotDigest"],
        "baselineIdentity": baseline_identity,
        "certificationRulesetIdentity": ruleset_identity,
        "cicImplementationVersion": CIC01_VERSION,
        "crResultSetIdentity": "LOCKED_BY_CIC02",
        "cssResultSetIdentity": "LOCKED_BY_CIC03",
        "certificationConfigurationIdentity": configuration_identity,
        "evidenceSchemaVersion": evidence_schema_version,
        "dependencyLocks": (),
        "invocationParameters": invocation_parameters or {},
    }
    digest = stable_hash(body)
    return {**body, "inputLockIdentifier": f"CIC01-LOCK-{digest[:16].upper()}", "inputLockDigest": digest, "immutable": True}


def validate_cic01_contract(contract: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    required = ("schemaVersion", "status", "candidateIdentity", "candidateSnapshot", "certificationInputLock", "candidateContractDigest")
    for key in required:
        if key not in contract:
            failures.append(f"MISSING_FIELD:{key}")
    if failures:
        return {"valid": False, "failureCodes": tuple(failures)}
    if contract["schemaVersion"] != "CIC01-CANDIDATE-CONTRACT.1":
        failures.append("UNSUPPORTED_CONTRACT_VERSION")
    if contract["status"] != "PASS":
        failures.append("CIC01_CONTRACT_NOT_PASS")
    identity = contract["candidateIdentity"]
    snapshot = contract["candidateSnapshot"]
    lock = contract["certificationInputLock"]
    if len(str(identity.get("repositoryCommit", ""))) != 40:
        failures.append("COMMIT_HASH_NOT_FULL")
    if identity.get("candidateIdentityDigest") != snapshot.get("candidateIdentityDigest"):
        failures.append(CIC01FailureCode.SNAPSHOT_MISMATCH.value)
    if identity.get("candidateIdentityDigest") != lock.get("candidateIdentityDigest"):
        failures.append(CIC01FailureCode.INPUT_LOCK_MISMATCH.value)
    if snapshot.get("candidateSnapshotDigest") != lock.get("candidateSnapshotDigest"):
        failures.append(CIC01FailureCode.INPUT_LOCK_MISMATCH.value)
    expected = stable_hash(_contract_digest_body({key: contract[key] for key in contract if key != "candidateContractDigest"}))
    if expected != contract.get("candidateContractDigest"):
        failures.append(CIC01FailureCode.ARTIFACT_TAMPER_DETECTED.value)
    return {
        "valid": not failures,
        "failureCodes": tuple(dict.fromkeys(failures)),
        "candidateIdentityDigest": identity.get("candidateIdentityDigest", ""),
        "repositoryCommit": identity.get("repositoryCommit", ""),
        "candidateSnapshotDigest": snapshot.get("candidateSnapshotDigest", ""),
        "inputLockIdentifier": lock.get("inputLockIdentifier", ""),
        "candidateContractDigest": contract.get("candidateContractDigest", ""),
    }


def detect_candidate_mutation(repo_root: str | Path, locked_contract: dict[str, Any], *, stage: str) -> dict[str, Any]:
    try:
        observed = resolve_candidate_identity(repo_root, require_clean=False)
    except CIC01Rejection as exc:
        return {
            "verdict": "FAIL",
            "failureCodes": (exc.code.value,),
            "stage": stage,
            "expectedCandidateIdentity": locked_contract.get("candidateIdentity", {}),
            "observedCandidateIdentity": {},
            "changedIdentityComponents": ("identity_unresolved",),
        }
    expected = locked_contract["candidateIdentity"]
    components = tuple(
        key
        for key in ("repositoryCommit", "commitTreeHash", "trackedStateDigest", "stagedIndexDigest", "relevantUntrackedDigest")
        if expected.get(key) != observed.get(key)
    )
    return {
        "verdict": "PASS" if not components else "FAIL",
        "failureCodes": () if not components else (CIC01FailureCode.CANDIDATE_MUTATED.value,),
        "stage": stage,
        "expectedCandidateIdentity": expected,
        "observedCandidateIdentity": observed,
        "changedIdentityComponents": components,
        "inputLockIdentifier": locked_contract.get("certificationInputLock", {}).get("inputLockIdentifier", ""),
        "evidenceQuarantined": bool(components),
    }


def bind_artifact_identity(
    artifact: dict[str, Any],
    contract: dict[str, Any],
    *,
    artifact_type: str,
    producer: str,
    schema_version: str = ARTIFACT_BINDING_SCHEMA_VERSION,
) -> dict[str, Any]:
    artifact_digest = stable_hash(artifact)
    identity = contract["candidateIdentity"]
    snapshot = contract["candidateSnapshot"]
    lock = contract["certificationInputLock"]
    body = {
        "schemaVersion": schema_version,
        "artifactType": artifact_type,
        "producer": producer,
        "producerVersion": CIC01_VERSION,
        "candidateIdentityDigest": identity["candidateIdentityDigest"],
        "repositoryCommit": identity["repositoryCommit"],
        "candidateSnapshotDigest": snapshot["candidateSnapshotDigest"],
        "certificationRunIdentifier": lock["inputLockIdentifier"],
        "inputLockIdentifier": lock["inputLockIdentifier"],
        "artifactDigest": artifact_digest,
    }
    return {**body, "bindingDigest": stable_hash(body)}


def validate_artifact_binding(artifact: dict[str, Any], binding: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if not binding:
        failures.append(CIC01FailureCode.ARTIFACT_IDENTITY_MISSING.value)
    else:
        if binding.get("artifactDigest") != stable_hash(artifact):
            failures.append(CIC01FailureCode.ARTIFACT_TAMPER_DETECTED.value)
        if binding.get("repositoryCommit") != contract["candidateIdentity"].get("repositoryCommit"):
            failures.append(CIC01FailureCode.ARTIFACT_IDENTITY_MISMATCH.value)
        if binding.get("candidateIdentityDigest") != contract["candidateIdentity"].get("candidateIdentityDigest"):
            failures.append(CIC01FailureCode.ARTIFACT_IDENTITY_MISMATCH.value)
        if binding.get("candidateSnapshotDigest") != contract["candidateSnapshot"].get("candidateSnapshotDigest"):
            failures.append(CIC01FailureCode.ARTIFACT_IDENTITY_MISMATCH.value)
        if binding.get("inputLockIdentifier") != contract["certificationInputLock"].get("inputLockIdentifier"):
            failures.append(CIC01FailureCode.ARTIFACT_IDENTITY_MISMATCH.value)
    return {"valid": not failures, "failureCodes": tuple(dict.fromkeys(failures))}


def validate_mixed_candidate_package(artifacts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records = tuple(artifacts)
    commits = {item.get("repositoryCommit") for item in records if item.get("repositoryCommit")}
    identities = {item.get("candidateIdentityDigest") for item in records if item.get("candidateIdentityDigest")}
    snapshots = {item.get("candidateSnapshotDigest") for item in records if item.get("candidateSnapshotDigest")}
    locks = {item.get("inputLockIdentifier") for item in records if item.get("inputLockIdentifier")}
    failures = []
    if len(commits) != 1 or len(identities) != 1 or len(snapshots) != 1 or len(locks) != 1:
        failures.append(CIC01FailureCode.MIXED_CANDIDATE_PACKAGE.value)
    if len(records) and any(not item.get("candidateIdentityDigest") for item in records):
        failures.append(CIC01FailureCode.ARTIFACT_IDENTITY_MISSING.value)
    return {
        "valid": not failures,
        "failureCodes": tuple(dict.fromkeys(failures)),
        "artifactCount": len(records),
        "commits": tuple(sorted(str(item) for item in commits)),
        "candidateIdentityDigests": tuple(sorted(str(item) for item in identities)),
        "candidateSnapshotDigests": tuple(sorted(str(item) for item in snapshots)),
        "inputLockIdentifiers": tuple(sorted(str(item) for item in locks)),
    }


def generate_cic01_evidence(repo_root: str | Path, evidence_output: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(evidence_output).resolve()
    if is_relative_to(out, root):
        failure = {
            "schemaVersion": EVIDENCE_MANIFEST_SCHEMA_VERSION,
            "verdict": "FAIL",
            "failureCodes": (CIC01FailureCode.EVIDENCE_OUTPUT_INSIDE_CANDIDATE.value,),
            "candidateRootDigest": stable_hash(root.as_posix().lower()),
            "evidenceOutput": str(out),
        }
        return failure
    out.mkdir(parents=True, exist_ok=True)
    pre = build_cic01_candidate_contract(root, require_clean=True)
    mutation_before = detect_candidate_mutation(root, pre, stage="after_input_lock")
    artifacts = {
        "candidate_contract.json": pre,
        "candidate_identity.json": pre["candidateIdentity"],
        "candidate_snapshot.json": pre["candidateSnapshot"],
        "certification_input_lock.json": pre["certificationInputLock"],
        "mutation_after_lock.json": mutation_before,
    }
    bindings = []
    for filename, payload in artifacts.items():
        binding = bind_artifact_identity(payload, pre, artifact_type=filename.removesuffix(".json"), producer="argos.candidate_integrity")
        bindings.append(binding)
        write_json(out / filename, payload)
        write_json(out / f"{filename}.binding.json", binding)
    agreement = validate_mixed_candidate_package(bindings)
    post = detect_candidate_mutation(root, pre, stage="after_evidence_generation")
    manifest_body = {
        "schemaVersion": EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "orderId": "CIC-01",
        "candidateIdentityDigest": pre["candidateIdentity"]["candidateIdentityDigest"],
        "repositoryCommit": pre["candidateIdentity"]["repositoryCommit"],
        "candidateSnapshotDigest": pre["candidateSnapshot"]["candidateSnapshotDigest"],
        "inputLockIdentifier": pre["certificationInputLock"]["inputLockIdentifier"],
        "artifactBindings": tuple(bindings),
        "identityAgreement": agreement,
        "postGenerationMutationCheck": post,
        "verdict": "PASS" if agreement["valid"] and post["verdict"] == "PASS" else "FAIL",
    }
    manifest = {**manifest_body, "manifestDigest": stable_hash(manifest_body)}
    write_json(out / "cic01_evidence_manifest.json", manifest)
    return manifest


def tracked_files(repo_root: Path) -> tuple[str, ...]:
    return tuple(sorted(normalize_path(line) for line in git(repo_root, "ls-files").splitlines() if line))


def repository_identifier(repo_root: Path) -> str:
    try:
        top = git(repo_root, "rev-parse", "--show-toplevel")
        remote = git(repo_root, "remote", "get-url", "origin")
    except Exception:
        remote = ""
        top = repo_root.as_posix()
    return stable_hash({"gitTopLevelName": Path(top).name, "origin": remote})


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    import fnmatch

    normalized = normalize_path(path)
    return any(fnmatch.fnmatchcase(normalized, pattern) for pattern in patterns)


def normalize_path(path: str) -> str:
    return str(PurePosixPath(path.replace("\\", "/")))


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def jsonable(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _contract_digest_body(body: dict[str, Any]) -> dict[str, Any]:
    return strip_volatile(
        {
            key: value
            for key, value in body.items()
            if key not in {"generatedAtUtc", "candidateContractDigest"}
        }
    )


def strip_volatile(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): strip_volatile(item)
            for key, item in value.items()
            if key not in {"generatedAtUtc", "generated_at_utc", "timestampUtc", "executionTimestamp"}
        }
    if isinstance(value, (tuple, list)):
        return [strip_volatile(item) for item in value]
    return value


def cic01_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CIC-01 candidate integrity")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--evidence-output", required=True)
    args = parser.parse_args(argv)
    try:
        result = generate_cic01_evidence(args.repo_root, args.evidence_output)
    except CIC01Rejection as exc:
        result = {"verdict": "FAIL", "failureCodes": (exc.code.value,), "rejection": exc.to_dict()}
    print(json.dumps(jsonable(result), indent=2, sort_keys=True))
    return 0 if result.get("verdict") == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cic01_main())
