"""Canonical repository candidate identity and freeze controls for CR-1."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from typing import Any, Iterable

from argos.foundation.contracts import utc_timestamp


CANDIDATE_FORMAT_VERSION = "1"
GENERATOR_VERSION = "CR-1.1"

DEFAULT_EXCLUSIONS = (
    ".git/**",
    "__pycache__/**",
    "*.pyc",
    ".pytest_cache/**",
    ".mypy_cache/**",
    ".ruff_cache/**",
    ".coverage",
    "htmlcov/**",
    ".venv/**",
    "venv/**",
    "env/**",
    "build/**",
    "dist/**",
    "*.egg-info/**",
    "audit_exports/**",
    "audit_work/**",
    "outputs/**",
    "*.zip",
    "*.sha256",
    "Documentation/*_Evidence/**",
    "Documentation/*_Evidence",
    "Documentation/IFVA-001_Evidence/**",
    "Documentation/IFVA-001_Evidence",
)

DEPENDENCY_PATTERNS = (
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Dockerfile",
    "docker-compose*.yml",
    "docker-compose*.yaml",
)

CONFIGURATION_PATTERNS = (
    ".env.example",
    "*.toml",
    "*.ini",
    "*.cfg",
    "*.yaml",
    "*.yml",
    "*.json",
    "Scripts/*.ps1",
    "Scripts/*.cmd",
)

POLICY_KEYWORDS = (
    "policy",
    "authority",
    "constitutional",
    "truth",
    "governance",
    "risk",
    "broker",
    "promotion",
    "recovery",
    "persistence",
)

SCHEMA_KEYWORDS = (
    "schema",
    "migration",
    "event",
    "message",
    "record",
    "decision_object",
    "position",
    "order",
    "checkpoint",
)


@dataclass(frozen=True)
class CandidateRejection(Exception):
    code: str
    reason: str
    offending_paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "reason": self.reason, "offending_paths": self.offending_paths}


def build_candidate_identity(
    repo_root: str | Path,
    *,
    certification: bool = True,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    commit = resolve_commit(root)
    status = working_tree_status(root)
    if certification or not allow_dirty:
        reject_dirty_status(status)
    tracked_files = tuple(sorted(_tracked_files(root)))
    manifest_entries = tuple(_manifest_entry(root, path) for path in tracked_files if _is_candidate_file(path))
    manifest_hash = _hash_json(manifest_entries)
    source_identity = _domain_identity(root, manifest_entries, "source_tree", lambda entry: True)
    dependency_identity = _domain_identity(
        root,
        manifest_entries,
        "dependency",
        lambda entry: _matches_any(entry["path"], DEPENDENCY_PATTERNS),
    )
    configuration_identity = _domain_identity(
        root,
        manifest_entries,
        "configuration",
        lambda entry: _classify_path(entry["path"]) == "configuration",
    )
    policy_identity = _domain_identity(
        root,
        manifest_entries,
        "policy",
        lambda entry: _classify_path(entry["path"]) == "policy",
    )
    schema_identity = _domain_identity(
        root,
        manifest_entries,
        "schema",
        lambda entry: _classify_path(entry["path"]) == "schema",
    )
    historical = historical_evidence_inventory(root)
    mixed = mixed_candidate_scan(root, commit)
    identity = {
        "candidate_format_version": CANDIDATE_FORMAT_VERSION,
        "repository_commit": commit,
        "repository_branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "working_tree_clean": status["clean"],
        "working_tree_status": status,
        "source_tree_hash": source_identity["combined_hash"],
        "dependency_hash": dependency_identity["combined_hash"],
        "configuration_hash": configuration_identity["combined_hash"],
        "policy_hash": policy_identity["combined_hash"],
        "schema_hash": schema_identity["combined_hash"],
        "manifest_hash": manifest_hash,
        "generator_version": GENERATOR_VERSION,
        "runtime_version": _runtime_version(root),
        "python_version": sys.version,
        "platform_identity": platform.platform(),
        "generated_at_utc": utc_timestamp(),
        "stable_identity_hash": _hash_json(
            {
                "candidate_format_version": CANDIDATE_FORMAT_VERSION,
                "repository_commit": commit,
                "source_tree_hash": source_identity["combined_hash"],
                "dependency_hash": dependency_identity["combined_hash"],
                "configuration_hash": configuration_identity["combined_hash"],
                "policy_hash": policy_identity["combined_hash"],
                "schema_hash": schema_identity["combined_hash"],
                "manifest_hash": manifest_hash,
                "generator_version": GENERATOR_VERSION,
                "runtime_version": _runtime_version(root),
                "python_version": sys.version,
                "platform_identity": platform.platform(),
            }
        ),
    }
    return {
        "candidate_identity": identity,
        "candidate_manifest": {
            "candidate_identity_hash": identity["stable_identity_hash"],
            "manifest_hash": manifest_hash,
            "included_paths": tuple(entry["path"] for entry in manifest_entries),
            "entries": manifest_entries,
            "exclusions": exclusions(),
        },
        "source_tree_identity": source_identity,
        "dependency_identity": dependency_identity,
        "configuration_identity": configuration_identity,
        "policy_identity": policy_identity,
        "schema_identity": schema_identity,
        "historical_evidence_inventory": historical,
        "mixed_candidate_scan": mixed,
    }


def run_preflight(
    repo_root: str | Path,
    *,
    certification: bool = False,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    try:
        payload = build_candidate_identity(repo_root, certification=certification, allow_dirty=allow_dirty)
        mixed = payload["mixed_candidate_scan"]
        if certification and mixed["active_mixed_candidate_rejected"]:
            raise CandidateRejection(
                "CANDIDATE_MIXED_IDENTITY",
                "Active identity-bearing evidence contains commits that differ from HEAD.",
                tuple(mixed["active_mismatched_paths"]),
            )
        payload["preflight_result"] = {
            "verdict": "PASS",
            "certification_mode": certification,
            "generated_at_utc": utc_timestamp(),
            "rejections": (),
            "constitutional_statement": _constitutional_statement(),
        }
        return payload
    except CandidateRejection as exc:
        commit = _maybe_commit(repo_root)
        return {
            "candidate_identity": {
                "candidate_format_version": CANDIDATE_FORMAT_VERSION,
                "repository_commit": commit,
                "repository_branch": _git(Path(repo_root).resolve(), "rev-parse", "--abbrev-ref", "HEAD"),
                "working_tree_clean": False,
                "generator_version": GENERATOR_VERSION,
                "generated_at_utc": utc_timestamp(),
            },
            "preflight_result": {
                "verdict": "FAIL",
                "certification_mode": certification,
                "generated_at_utc": utc_timestamp(),
                "rejections": (exc.to_dict(),),
                "constitutional_statement": _constitutional_statement(),
            },
        }


def freeze_candidate(repo_root: str | Path, output_dir: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir).resolve()
    payload = run_preflight(root, certification=True)
    if payload["preflight_result"]["verdict"] != "PASS":
        raise CandidateRejection(
            "FREEZE_PREFLIGHT_FAILED",
            "Candidate freeze requires a passing certification preflight.",
            tuple(path for rejection in payload["preflight_result"]["rejections"] for path in rejection["offending_paths"]),
        )
    identity = payload["candidate_identity"]
    commit = identity["repository_commit"]
    out.mkdir(parents=True, exist_ok=True)
    archive_path = out / f"ARGOS_CANDIDATE_{commit}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for entry in payload["candidate_manifest"]["entries"]:
            path = root / entry["path"]
            archive.write(path, f"ARGOS-{commit}/{entry['path']}")
    archive_hash = _file_hash(archive_path)
    verification = verify_archive(archive_path, payload["candidate_manifest"]["entries"], commit)
    result = {
        **payload,
        "freeze_result": {
            "verdict": "PASS",
            "archive": str(archive_path),
            "archive_sha256": archive_hash,
            "verification": verification,
            "generated_at_utc": utc_timestamp(),
        },
    }
    _write_external_evidence(out / "cr-1", result)
    return result


def verify_archive(archive_path: str | Path, manifest_entries: Iterable[dict[str, Any]], commit: str) -> dict[str, Any]:
    expected = {f"ARGOS-{commit}/{entry['path']}": entry for entry in manifest_entries}
    with zipfile.ZipFile(archive_path, "r") as archive:
        names = tuple(sorted(name for name in archive.namelist() if not name.endswith("/")))
        missing = tuple(sorted(set(expected) - set(names)))
        extra = tuple(sorted(set(names) - set(expected)))
        mismatched = []
        for name, entry in expected.items():
            if name in names:
                if hashlib.sha256(archive.read(name)).hexdigest() != entry["sha256"]:
                    mismatched.append(name)
    return {
        "archive": str(archive_path),
        "verified": not missing and not extra and not mismatched,
        "missing": missing,
        "extra": extra,
        "mismatched": tuple(mismatched),
    }


def resolve_commit(repo_root: Path) -> str:
    commit = _git(repo_root, "rev-parse", "HEAD")
    if len(commit) != 40:
        raise CandidateRejection("CANDIDATE_INVALID_COMMIT", "Git did not return a full 40-character commit.", (commit,))
    if _git(repo_root, "cat-file", "-t", commit) != "commit":
        raise CandidateRejection("CANDIDATE_INVALID_COMMIT", "Resolved commit is not a valid commit.", (commit,))
    return commit


def working_tree_status(repo_root: Path) -> dict[str, Any]:
    result = subprocess.run(("git", "status", "--porcelain=v1"), cwd=repo_root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise CandidateRejection("GIT_COMMAND_FAILED", f"git status --porcelain=v1 failed: {result.stderr.strip()}")
    lines = tuple(line for line in result.stdout.splitlines() if line)
    staged = tuple(line[3:] for line in lines if line[:1] not in (" ", "?") and line[:2] != "??")
    unstaged = tuple(line[3:] for line in lines if len(line) > 1 and line[1] not in (" ", "?"))
    untracked = tuple(line[3:] for line in lines if line[:2] == "??")
    conflicts = tuple(line[3:] for line in lines if line[:2] in {"DD", "AU", "UD", "UA", "DU", "AA", "UU"})
    return {
        "clean": not lines,
        "porcelain": lines,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "conflicts": conflicts,
    }


def reject_dirty_status(status: dict[str, Any]) -> None:
    if status["conflicts"]:
        raise CandidateRejection("CANDIDATE_MERGE_CONFLICT", "Unresolved merge conflicts are present.", tuple(status["conflicts"]))
    if status["staged"]:
        raise CandidateRejection("CANDIDATE_DIRTY_STAGED", "Staged changes are present.", tuple(status["staged"]))
    if status["unstaged"]:
        raise CandidateRejection("CANDIDATE_DIRTY_TRACKED", "Unstaged tracked changes are present.", tuple(status["unstaged"]))
    if status["untracked"]:
        raise CandidateRejection("CANDIDATE_DIRTY_UNTRACKED", "Untracked files are present.", tuple(status["untracked"]))


def historical_evidence_inventory(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    paths = []
    for pattern in ("Documentation/*_Evidence*", "Documentation/IFVA-001_Evidence*", "*.zip", "*.sha256"):
        for path in root.glob(pattern):
            paths.append(path)
    records = tuple(
        {
            "path": _rel(path, root),
            "kind": "directory" if path.is_dir() else "file",
            "tracked": _is_tracked(root, path),
            "authoritative_for_current_candidate": False,
        }
        for path in sorted(set(paths))
    )
    return {
        "historical_evidence_policy": "Historical evidence is non-authoritative and excluded from CR-1 candidate packaging.",
        "records": records,
        "count": len(records),
    }


def mixed_candidate_scan(repo_root: str | Path, candidate_commit: str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    active_paths = tuple(path for path in root.glob("Documentation/**/*") if path.is_file() and _is_candidate_file(_rel(path, root)))
    commits_by_path: dict[str, tuple[str, ...]] = {}
    for path in active_paths:
        if path.suffix.lower() not in {".json", ".md", ".txt", ".csv", ".sha256"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        commits = tuple(sorted(set(_extract_commits(text))))
        if commits:
            commits_by_path[_rel(path, root)] = commits
    mismatched = tuple(
        path for path, commits in commits_by_path.items() if any(commit != candidate_commit for commit in commits)
    )
    return {
        "candidate_commit": candidate_commit,
        "active_identity_paths_scanned": len(active_paths),
        "commit_bearing_paths": commits_by_path,
        "active_mismatched_paths": mismatched,
        "active_mixed_candidate_rejected": bool(mismatched),
    }


def exclusions() -> dict[str, Any]:
    return {
        "patterns": DEFAULT_EXCLUSIONS,
        "policy": "Exclude local caches, generated audit evidence, historical archives, and prior ZIP/hash packages from source candidate archives.",
    }


def _write_external_evidence(output_dir: Path, payload: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    unavailable = {"status": "UNAVAILABLE", "reason": "Preflight failed before this artifact could be generated."}
    files = {
        "candidate_identity.json": payload["candidate_identity"],
        "candidate_manifest.json": payload.get("candidate_manifest", unavailable),
        "dependency_identity.json": payload.get("dependency_identity", unavailable),
        "configuration_identity.json": payload.get("configuration_identity", unavailable),
        "policy_identity.json": payload.get("policy_identity", unavailable),
        "schema_identity.json": payload.get("schema_identity", unavailable),
        "source_tree_identity.json": payload.get("source_tree_identity", unavailable),
        "preflight_result.json": payload["preflight_result"],
        "historical_evidence_inventory.json": payload.get("historical_evidence_inventory", unavailable),
        "exclusions.json": exclusions(),
        "test_results.json": {"status": "external_freeze_does_not_run_tests"},
    }
    for name, content in files.items():
        (output_dir / name).write_text(json.dumps(content, indent=2, sort_keys=True, default=str), encoding="utf-8")
    manifest_path = output_dir / "candidate_manifest.json"
    (output_dir / "candidate_manifest.sha256").write_text(_file_hash(manifest_path), encoding="utf-8")
    report = _preflight_report(payload)
    (output_dir / "preflight_report.md").write_text(report, encoding="utf-8")
    (output_dir / "traceability.md").write_text(_traceability_report(), encoding="utf-8")
    (output_dir / "implementation_summary.md").write_text(_implementation_summary(), encoding="utf-8")
    (output_dir / "operator_instructions.md").write_text(_operator_instructions(), encoding="utf-8")


def _preflight_report(payload: dict[str, Any]) -> str:
    identity = payload["candidate_identity"]
    result = payload["preflight_result"]
    return (
        "# CR-1 Candidate Preflight Report\n\n"
        f"Verdict: {result['verdict']}\n\n"
        f"Commit: {identity.get('repository_commit', '')}\n\n"
        f"Branch: {identity.get('repository_branch', '')}\n\n"
        f"Working tree clean: {identity.get('working_tree_clean', False)}\n\n"
        f"Source tree hash: {identity.get('source_tree_hash', '')}\n\n"
        f"Dependency hash: {identity.get('dependency_hash', '')}\n\n"
        f"Configuration hash: {identity.get('configuration_hash', '')}\n\n"
        f"Policy hash: {identity.get('policy_hash', '')}\n\n"
        f"Schema hash: {identity.get('schema_hash', '')}\n\n"
        f"Manifest hash: {identity.get('manifest_hash', '')}\n\n"
        f"{_constitutional_statement()}\n"
    )


def _traceability_report() -> str:
    return "# CR-1 Traceability\n\nCandidate identity, preflight, dirty-tree rejection, mixed-candidate scanning, and archive verification are implemented in `src/argos/candidate_identity.py`.\n"


def _implementation_summary() -> str:
    return "# CR-1 Implementation Summary\n\nImplemented candidate identity generation, deterministic domain hashes, dirty-tree enforcement, mixed-candidate scanning, historical evidence inventory, preflight, freeze, and archive verification controls.\n"


def _operator_instructions() -> str:
    return "# CR-1 Operator Instructions\n\nRun `py -3 Scripts/candidate_preflight.py --certification --output <external-dir>` from a clean repository. Run `py -3 Scripts/freeze_candidate.py --output <external-dir>` only after preflight passes.\n"


def _constitutional_statement() -> str:
    return "CR-1 establishes candidate identity and repository integrity only. It does not certify ARGOS functional correctness, constitutional runtime compliance, synthetic-truth elimination, paper readiness, live readiness, or operational readiness."


def _domain_identity(
    repo_root: Path,
    entries: tuple[dict[str, Any], ...],
    domain: str,
    predicate: Any,
) -> dict[str, Any]:
    selected = tuple(entry for entry in entries if predicate(entry))
    return {
        "domain": domain,
        "combined_hash": _hash_json(tuple((entry["path"], entry["sha256"]) for entry in selected)),
        "files": selected,
        "file_count": len(selected),
    }


def _manifest_entry(repo_root: Path, rel_path: str) -> dict[str, Any]:
    path = repo_root / rel_path
    return {
        "path": rel_path,
        "size": path.stat().st_size,
        "sha256": _file_hash(path),
        "classification": _classify_path(rel_path),
        "executable": os.access(path, os.X_OK),
        "generated": _looks_generated(rel_path),
        "identity_domains": _identity_domains(rel_path),
    }


def _classify_path(path: str) -> str:
    lower = path.lower()
    if path.startswith("src/"):
        if any(keyword in lower for keyword in POLICY_KEYWORDS):
            return "policy"
        if any(keyword in lower for keyword in SCHEMA_KEYWORDS):
            return "schema"
        return "source"
    if path.startswith("Tests/"):
        return "test"
    if path.startswith("Scripts/"):
        return "script"
    if _matches_any(path, DEPENDENCY_PATTERNS):
        return "dependency"
    if _matches_any(path, CONFIGURATION_PATTERNS):
        return "configuration"
    if path.startswith("Documentation/"):
        return "documentation"
    if path.endswith((".md", ".txt")):
        return "documentation"
    return "metadata"


def _identity_domains(path: str) -> tuple[str, ...]:
    classification = _classify_path(path)
    domains = ["source_tree"]
    if classification in {"dependency", "configuration", "policy", "schema"}:
        domains.append(classification)
    return tuple(domains)


def _looks_generated(path: str) -> bool:
    lower = path.lower()
    return "/_evidence/" in lower or lower.endswith((".zip", ".sha256", ".log", "coverage.xml"))


def _is_candidate_file(path: str) -> bool:
    normalized = _normalize_path(path)
    return not _matches_any(normalized, DEFAULT_EXCLUSIONS)


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    normalized = _normalize_path(path)
    return any(fnmatch.fnmatchcase(normalized, pattern) for pattern in patterns)


def _tracked_files(repo_root: Path) -> tuple[str, ...]:
    output = _git(repo_root, "ls-files")
    return tuple(_normalize_path(line) for line in output.splitlines() if line)


def _is_tracked(repo_root: Path, path: Path) -> bool:
    result = subprocess.run(("git", "ls-files", "--error-unmatch", str(path.relative_to(repo_root))), cwd=repo_root, text=True, capture_output=True, check=False)
    return result.returncode == 0


def _extract_commits(text: str) -> tuple[str, ...]:
    import re

    return tuple(re.findall(r"\b[0-9a-f]{40}\b", text))


def _runtime_version(repo_root: Path) -> str:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return "UNKNOWN"
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version"):
            return line.split("=", 1)[1].strip().strip('"')
    return "UNKNOWN"


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _hash_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _normalize_path(path: str) -> str:
    return str(PurePosixPath(path.replace("\\", "/")))


def _rel(path: Path, root: Path) -> str:
    return _normalize_path(str(path.relative_to(root)))


def _maybe_commit(repo_root: str | Path) -> str:
    try:
        return resolve_commit(Path(repo_root).resolve())
    except CandidateRejection:
        return "UNKNOWN"


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise CandidateRejection("GIT_COMMAND_FAILED", f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def write_preflight_outputs(payload: dict[str, Any], output_dir: str | Path) -> None:
    out = Path(output_dir).resolve() / "cr-1"
    out.mkdir(parents=True, exist_ok=True)
    _write_external_evidence(out, payload)


def candidate_preflight_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CR-1 candidate preflight")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--certification", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    payload = run_preflight(args.repo_root, certification=args.certification, allow_dirty=args.allow_dirty)
    if args.output:
        write_preflight_outputs(payload, args.output)
    print(json.dumps(payload["preflight_result"], indent=2, sort_keys=True))
    return 0 if payload["preflight_result"]["verdict"] == "PASS" else 1


def freeze_candidate_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CR-1 candidate freeze")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        result = freeze_candidate(args.repo_root, args.output)
    except CandidateRejection as exc:
        print(json.dumps({"verdict": "FAIL", "rejection": exc.to_dict()}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result["freeze_result"], indent=2, sort_keys=True))
    return 0 if result["freeze_result"]["verdict"] == "PASS" else 1
