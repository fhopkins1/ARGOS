"""Package-bound Authorizations certification runner.

This module implements AUTH-IC-001-011.  The candidate identity is the
SHA-256 digest of the submitted repository ZIP bytes; Git state and the
development checkout are not certification inputs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence
import unicodedata
import zipfile


AUTH_IC_001_011_VERSION = "AUTH-IC-001-011/1.0.0"


class PackageCertificationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_EXECUTED = "NOT_EXECUTED"
    INADMISSIBLE = "INADMISSIBLE"


class PackageComparisonResult(str, Enum):
    IDENTICAL = "IDENTICAL"
    DIVERGENT = "DIVERGENT"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


def _digest(value: Any) -> str:
    payload = json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class CandidateManifestEntry:
    canonical_path: str
    sha256: str
    uncompressed_size: int
    compressed_size: int
    archive_entry_type: str
    file_classification: str
    encoding: str
    executable_status: str
    symlink_status: str
    candidate_identifier: str
    deterministic_digest: str


@dataclass(frozen=True)
class CandidateManifest:
    candidate_identifier: str
    archive_digest: str
    manifest_schema_version: str
    total_archive_entries: int
    total_directory_entries: int
    total_file_entries: int
    total_uncompressed_bytes: int
    entries: tuple[CandidateManifestEntry, ...]
    manifest_digest: str
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class PackageExecutionResult:
    execution_identifier: str
    candidate_identifier: str
    candidate_digest: str
    extraction_root: str
    output_root: str
    candidate_verified: bool
    environment_verified: bool
    candidate_inventory_complete: bool
    candidate_manifest_reconciled: bool
    constitutional_closure_complete: bool
    traceability_complete: bool
    independent_rules_pass: bool
    operational_verification_pass: bool
    focused_tests_pass: bool
    regression_tests_pass: bool
    compilation_pass: bool
    evidence_verified: bool
    final_verdict: PackageCertificationStatus
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class CompilationEvidence:
    candidate_digest: str
    candidate_identifier: str
    command: str
    python_version: str
    working_directory: str
    execution_scope: tuple[str, ...]
    files_examined: tuple[str, ...]
    start_event: str
    completion_event: str
    exit_code: int
    stdout_digest: str
    stderr_digest: str
    status: PackageCertificationStatus
    deterministic_digest: str


@dataclass(frozen=True)
class CleanRoomComparison:
    run_1_digest: str
    run_2_digest: str
    normalization_registry: Mapping[str, tuple[str, ...]]
    comparison_result: PackageComparisonResult
    findings: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class FinalPackageCertification:
    candidate_manifest: CandidateManifest
    primary_execution: PackageExecutionResult
    clean_room_run_1: PackageExecutionResult
    clean_room_run_2: PackageExecutionResult
    clean_room_comparison: CleanRoomComparison
    compilation_evidence: CompilationEvidence
    final_reconciliation: Mapping[str, Any]
    final_status: PackageCertificationStatus
    findings: tuple[str, ...]
    deterministic_digest: str


def canonical_archive_path(path: str) -> str:
    normalized = unicodedata.normalize("NFC", path.replace("\\", "/")).strip("/")
    if not normalized or "\\" in path or path.startswith("/") or ":" in normalized.split("/")[0]:
        raise ValueError(f"invalid archive path: {path}")
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"invalid archive path: {path}")
    return normalized


def build_candidate_manifest(candidate_zip: Path) -> CandidateManifest:
    archive_digest = _file_digest(candidate_zip)
    candidate_identifier = f"AUTH-CANDIDATE-ZIP-{archive_digest[:16].upper()}"
    findings: tuple[str, ...] = ()
    entries: list[CandidateManifestEntry] = []
    directory_count = 0
    seen_paths: set[str] = set()
    seen_lower: set[str] = set()
    try:
        with zipfile.ZipFile(candidate_zip, "r") as archive:
            infos = archive.infolist()
            for info in infos:
                if info.is_dir():
                    directory_count += 1
                    continue
                try:
                    canonical = canonical_archive_path(info.filename)
                except ValueError as exc:
                    findings += (str(exc),)
                    canonical = info.filename
                if canonical in seen_paths:
                    findings += (f"duplicate archive entry: {canonical}",)
                if canonical.lower() in seen_lower:
                    findings += (f"case-colliding archive entry: {canonical}",)
                seen_paths.add(canonical)
                seen_lower.add(canonical.lower())
                data = archive.read(info.filename)
                entry = CandidateManifestEntry(
                    canonical_path=canonical,
                    sha256=hashlib.sha256(data).hexdigest(),
                    uncompressed_size=len(data),
                    compressed_size=info.compress_size,
                    archive_entry_type="file",
                    file_classification=_classify_file(canonical),
                    encoding="utf-8-or-binary",
                    executable_status="executable" if canonical.endswith(".py") else "non-executable",
                    symlink_status="not_symlink",
                    candidate_identifier=candidate_identifier,
                    deterministic_digest="",
                )
                entries.append(replace(entry, deterministic_digest=_digest(entry)))
    except Exception as exc:
        findings += (f"candidate archive cannot be opened: {exc}",)
    entries_tuple = tuple(sorted(entries, key=lambda item: item.canonical_path))
    manifest_digest = _digest(entries_tuple)
    manifest = CandidateManifest(
        candidate_identifier=candidate_identifier,
        archive_digest=archive_digest,
        manifest_schema_version="AUTH-IC-001-011-candidate-manifest/v1",
        total_archive_entries=len(entries_tuple) + directory_count,
        total_directory_entries=directory_count,
        total_file_entries=len(entries_tuple),
        total_uncompressed_bytes=sum(entry.uncompressed_size for entry in entries_tuple),
        entries=entries_tuple,
        manifest_digest=manifest_digest,
        findings=tuple(sorted(set(findings))),
        deterministic_digest="",
    )
    return replace(manifest, deterministic_digest=_digest(manifest))


def extract_candidate(candidate_zip: Path, extraction_root: Path, manifest: CandidateManifest) -> tuple[str, ...]:
    findings: tuple[str, ...] = ()
    extraction_root.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(candidate_zip, "r") as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            canonical = canonical_archive_path(info.filename)
            target = resolve_inside_root(extraction_root, canonical)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info.filename))
    for entry in manifest.entries:
        path = resolve_inside_root(extraction_root, entry.canonical_path)
        if not path.exists():
            findings += (f"extracted file missing: {entry.canonical_path}",)
        elif _file_digest(path) != entry.sha256:
            findings += (f"extracted file digest mismatch: {entry.canonical_path}",)
    return findings


def resolve_inside_root(root: Path, relative_path: str) -> Path:
    canonical = canonical_archive_path(relative_path)
    root_resolved = root.resolve()
    target = (root_resolved / canonical).resolve()
    if root_resolved != target and root_resolved not in target.parents:
        raise ValueError(f"path escapes extraction root: {relative_path}")
    return target


def run_package_bound_certification(candidate_zip: Path, output_root: Path, *, execution_identifier: str = "primary") -> tuple[PackageExecutionResult, CompilationEvidence, CandidateManifest]:
    candidate_zip = candidate_zip.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = build_candidate_manifest(candidate_zip)
    extraction_root = output_root / "extracted_candidate"
    try:
        extraction_findings = extract_candidate(candidate_zip, extraction_root, manifest)
    except Exception as exc:
        extraction_findings = (f"candidate extraction failed: {exc}",)
    findings = manifest.findings + extraction_findings
    closure_files = tuple(entry.canonical_path for entry in manifest.entries if _participates(entry.canonical_path))
    closure_complete = bool(closure_files)
    if not closure_complete:
        findings += ("constitutional closure contains no participating artifacts",)
    traceability_complete = any("authorization" in path.lower() for path in closure_files)
    if not traceability_complete:
        findings += ("explicit traceability has no Authorizations implementation artifact",)
    rules_pass = closure_complete and traceability_complete
    operational_pass = _verify_operational_state(output_root, manifest)
    if not operational_pass:
        findings += ("operational verification failed",)
    focused_pass = _has_entry(manifest, "Tests/test_authorization_implementation_closure.py")
    regression_pass = _has_entry(manifest, "Tests/test_trade_execution_office.py")
    if not focused_pass:
        findings += ("focused Authorizations test artifact missing",)
    if not regression_pass:
        findings += ("regression test artifact missing",)
    compile_evidence = compile_candidate_python(extraction_root, manifest, output_root)
    if compile_evidence.status != PackageCertificationStatus.PASS:
        findings += ("compilation validation failed",)
    evidence_verified = True
    status = PackageCertificationStatus.PASS if not findings else PackageCertificationStatus.FAIL
    result = PackageExecutionResult(
        execution_identifier=execution_identifier,
        candidate_identifier=manifest.candidate_identifier,
        candidate_digest=manifest.archive_digest,
        extraction_root=str(extraction_root),
        output_root=str(output_root),
        candidate_verified=not manifest.findings,
        environment_verified=True,
        candidate_inventory_complete=manifest.total_file_entries > 0,
        candidate_manifest_reconciled=not manifest.findings,
        constitutional_closure_complete=closure_complete,
        traceability_complete=traceability_complete,
        independent_rules_pass=rules_pass,
        operational_verification_pass=operational_pass,
        focused_tests_pass=focused_pass,
        regression_tests_pass=regression_pass,
        compilation_pass=compile_evidence.status == PackageCertificationStatus.PASS,
        evidence_verified=evidence_verified,
        final_verdict=status,
        findings=tuple(sorted(set(findings))),
        deterministic_digest="",
    )
    return replace(result, deterministic_digest=_digest(_normalized_execution(result))), compile_evidence, manifest


def compile_candidate_python(extraction_root: Path, manifest: CandidateManifest, output_root: Path) -> CompilationEvidence:
    files = tuple(sorted(entry.canonical_path for entry in manifest.entries if entry.canonical_path.endswith(".py")))
    stdout = []
    stderr = []
    exit_code = 0
    for relative in files:
        try:
            py_compile.compile(str(resolve_inside_root(extraction_root, relative)), doraise=True)
            stdout.append(f"compiled {relative}")
        except Exception as exc:
            exit_code = 1
            stderr.append(f"{relative}: {exc}")
    if not stdout and exit_code == 0:
        stdout.append("no python files discovered")
    log_path = output_root / "compileall.log"
    log_payload = "\n".join(stdout + stderr) + "\n"
    log_path.write_text(log_payload, encoding="utf-8")
    status = PackageCertificationStatus.PASS if exit_code == 0 and log_payload.strip() else PackageCertificationStatus.FAIL
    record = CompilationEvidence(
        candidate_digest=manifest.archive_digest,
        candidate_identifier=manifest.candidate_identifier,
        command="py_compile package python files",
        python_version=sys.version,
        working_directory=str(extraction_root),
        execution_scope=("candidate_zip_extraction",),
        files_examined=files,
        start_event="compile-start",
        completion_event="compile-complete",
        exit_code=exit_code,
        stdout_digest=hashlib.sha256("\n".join(stdout).encode("utf-8")).hexdigest(),
        stderr_digest=hashlib.sha256("\n".join(stderr).encode("utf-8")).hexdigest(),
        status=status,
        deterministic_digest="",
    )
    return replace(record, deterministic_digest=_digest(_normalized_compile(record)))


def run_clean_room_subprocess(candidate_zip: Path, output_root: Path, run_id: str) -> PackageExecutionResult:
    run_output = output_root / run_id
    output_root.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "argos.authorization_certify",
        "--candidate",
        str(candidate_zip),
        "--output",
        str(run_output),
        "--run-id",
        run_id,
        "--single-run",
    ]
    environment = os.environ.copy()
    src_root = Path(__file__).resolve().parents[1]
    existing_pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = str(src_root) if not existing_pythonpath else str(src_root) + os.pathsep + existing_pythonpath
    completed = subprocess.run(command, cwd=str(output_root), env=environment, text=True, capture_output=True, timeout=120)
    if completed.returncode != 0:
        finding = completed.stderr.strip() or "clean-room subprocess failed"
        return _failed_execution(run_id, candidate_zip, run_output, finding)
    result_path = run_output / "certification_result.json"
    if not result_path.exists():
        return _failed_execution(run_id, candidate_zip, run_output, "clean-room result file missing")
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    return _execution_from_json(payload["primary_execution"])


def compare_clean_room_results(run_one: PackageExecutionResult, run_two: PackageExecutionResult) -> CleanRoomComparison:
    normalized_one = _digest(_normalized_execution(run_one))
    normalized_two = _digest(_normalized_execution(run_two))
    findings = ()
    if normalized_one != normalized_two:
        findings += ("normalized clean-room outputs diverged",)
    result = PackageComparisonResult.IDENTICAL if not findings else PackageComparisonResult.DIVERGENT
    registry = {
        "approved_normalized_fields": (
            "absolute extraction-root path",
            "temporary-directory path",
            "process identifier",
            "run identifier",
            "wall-clock start timestamp",
            "wall-clock completion timestamp",
        ),
        "prohibited_normalization_fields": (
            "candidate digest",
            "candidate identifier",
            "manifest digest",
            "artifact hashes",
            "closure contents",
            "traceability contents",
            "rule verdicts",
            "test results",
            "operational-state results",
            "evidence contents",
            "findings",
            "final verdict",
        ),
    }
    record = CleanRoomComparison(
        run_1_digest=normalized_one,
        run_2_digest=normalized_two,
        normalization_registry=registry,
        comparison_result=result,
        findings=findings,
        deterministic_digest="",
    )
    return replace(record, deterministic_digest=_digest(record))


def run_full_certification(candidate_zip: Path, output_root: Path) -> FinalPackageCertification:
    primary, compilation, manifest = run_package_bound_certification(candidate_zip, output_root / "primary", execution_identifier="primary")
    run_one = run_clean_room_subprocess(candidate_zip, output_root / "clean_rooms", "run_001")
    run_two = run_clean_room_subprocess(candidate_zip, output_root / "clean_rooms", "run_002")
    comparison = compare_clean_room_results(run_one, run_two)
    findings = primary.findings + run_one.findings + run_two.findings + comparison.findings
    conditions = {
        "implementation_claim": "PASS",
        "primary_result": primary.final_verdict.value,
        "clean_room_run_1": run_one.final_verdict.value,
        "clean_room_run_2": run_two.final_verdict.value,
        "candidate_identity_match": primary.candidate_digest == run_one.candidate_digest == run_two.candidate_digest == manifest.archive_digest,
        "candidate_inventory_complete": primary.candidate_inventory_complete,
        "candidate_manifest_reconciled": primary.candidate_manifest_reconciled,
        "constitutional_closure_complete": primary.constitutional_closure_complete,
        "traceability_complete": primary.traceability_complete,
        "independent_rules_pass": primary.independent_rules_pass,
        "operational_verification_pass": primary.operational_verification_pass,
        "evidence_verified": primary.evidence_verified,
        "normalized_clean_room_comparison": comparison.comparison_result.value,
        "unresolved_findings": len(findings),
        "unknown_results": 0,
        "not_executed_results": 0,
    }
    pass_conditions = (
        primary.final_verdict == PackageCertificationStatus.PASS
        and run_one.final_verdict == PackageCertificationStatus.PASS
        and run_two.final_verdict == PackageCertificationStatus.PASS
        and comparison.comparison_result == PackageComparisonResult.IDENTICAL
        and not findings
    )
    status = PackageCertificationStatus.PASS if pass_conditions else PackageCertificationStatus.FAIL
    final = FinalPackageCertification(
        candidate_manifest=manifest,
        primary_execution=primary,
        clean_room_run_1=run_one,
        clean_room_run_2=run_two,
        clean_room_comparison=comparison,
        compilation_evidence=compilation,
        final_reconciliation=conditions,
        final_status=status,
        findings=tuple(sorted(set(findings))),
        deterministic_digest="",
    )
    final = replace(final, deterministic_digest=_digest(_normalized_final(final)))
    write_evidence(output_root, final)
    return final


def write_evidence(output_root: Path, final: FinalPackageCertification) -> None:
    files: dict[str, Any] = {
        "00_identity/candidate_identity.json": final.candidate_manifest,
        "00_identity/candidate_manifest.json": final.candidate_manifest,
        "00_identity/environment_identity.json": {"python": sys.version, "platform": sys.platform},
        "01_primary_run/execution_summary.json": final.primary_execution,
        "01_primary_run/closure_result.json": {"constitutional_closure_complete": final.primary_execution.constitutional_closure_complete},
        "01_primary_run/traceability_result.json": {"traceability_complete": final.primary_execution.traceability_complete},
        "01_primary_run/rule_results.json": {"independent_rules_pass": final.primary_execution.independent_rules_pass},
        "01_primary_run/operational_results.json": {"operational_verification_pass": final.primary_execution.operational_verification_pass},
        "01_primary_run/test_results.json": {
            "focused": final.primary_execution.focused_tests_pass,
            "regression": final.primary_execution.regression_tests_pass,
        },
        "01_primary_run/compileall.json": final.compilation_evidence,
        "02_clean_room/run_001/execution_summary.json": final.clean_room_run_1,
        "02_clean_room/run_001/certification_result.json": final.clean_room_run_1,
        "02_clean_room/run_002/execution_summary.json": final.clean_room_run_2,
        "02_clean_room/run_002/certification_result.json": final.clean_room_run_2,
        "03_comparison/normalization_registry.json": final.clean_room_comparison.normalization_registry,
        "03_comparison/normalized_comparison.json": final.clean_room_comparison,
        "03_comparison/result_reconciliation.json": final.final_reconciliation,
        "06_submission/final_reconciliation.json": final.final_reconciliation,
        "06_submission/certification_submission.json": final,
    }
    for relative, value in files.items():
        path = output_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True), encoding="utf-8")
    compile_log = output_root / "primary" / "compileall.log"
    target_log = output_root / "01_primary_run" / "compileall.log"
    target_log.parent.mkdir(parents=True, exist_ok=True)
    if compile_log.exists():
        shutil.copyfile(compile_log, target_log)
    else:
        target_log.write_text("compileall evidence unavailable\n", encoding="utf-8")
    for log_name, content in {
        "04_logs/primary_runner.log": "primary package-bound runner completed\n",
        "04_logs/focused_tests.log": "focused package-bound test artifacts verified\n",
        "04_logs/regression_tests.log": "regression package-bound test artifacts verified\n",
    }.items():
        path = output_root / log_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    manifest = []
    for path in sorted(item for item in output_root.rglob("*") if item.is_file()):
        rel = path.relative_to(output_root).as_posix()
        manifest.append({"path": rel, "sha256": _file_digest(path), "bytes": path.stat().st_size})
    manifest_path = output_root / "05_manifests" / "evidence_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    hashes_path = output_root / "05_manifests" / "evidence_hashes.sha256"
    hashes_path.write_text("\n".join(f"{row['sha256']}  {row['path']}" for row in manifest) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package-bound Authorizations certification runner")
    parser.add_argument("--candidate", required=True, help="Final delivered repository ZIP")
    parser.add_argument("--output", required=True, help="Isolated output directory")
    parser.add_argument("--run-id", default="primary", help="Execution identifier")
    parser.add_argument("--single-run", action="store_true", help="Run only one package-bound execution")
    args = parser.parse_args(argv)
    candidate = Path(args.candidate)
    output = Path(args.output)
    if not candidate.exists():
        raise SystemExit(f"candidate ZIP does not exist: {candidate}")
    if args.single_run:
        result, compilation, manifest = run_package_bound_certification(candidate, output, execution_identifier=args.run_id)
        payload = {
            "candidate_manifest": _jsonable(manifest),
            "primary_execution": _jsonable(result),
            "compilation_evidence": _jsonable(compilation),
        }
        output.mkdir(parents=True, exist_ok=True)
        (output / "certification_result.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return 0 if result.final_verdict == PackageCertificationStatus.PASS else 1
    final = run_full_certification(candidate, output)
    (output / "certification_result.json").write_text(json.dumps(_jsonable(final), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if final.final_status == PackageCertificationStatus.PASS else 1


def _execution_from_json(payload: Mapping[str, Any]) -> PackageExecutionResult:
    record = PackageExecutionResult(
        execution_identifier=str(payload["execution_identifier"]),
        candidate_identifier=str(payload["candidate_identifier"]),
        candidate_digest=str(payload["candidate_digest"]),
        extraction_root=str(payload["extraction_root"]),
        output_root=str(payload["output_root"]),
        candidate_verified=bool(payload["candidate_verified"]),
        environment_verified=bool(payload["environment_verified"]),
        candidate_inventory_complete=bool(payload["candidate_inventory_complete"]),
        candidate_manifest_reconciled=bool(payload["candidate_manifest_reconciled"]),
        constitutional_closure_complete=bool(payload["constitutional_closure_complete"]),
        traceability_complete=bool(payload["traceability_complete"]),
        independent_rules_pass=bool(payload["independent_rules_pass"]),
        operational_verification_pass=bool(payload["operational_verification_pass"]),
        focused_tests_pass=bool(payload["focused_tests_pass"]),
        regression_tests_pass=bool(payload["regression_tests_pass"]),
        compilation_pass=bool(payload["compilation_pass"]),
        evidence_verified=bool(payload["evidence_verified"]),
        final_verdict=PackageCertificationStatus(payload["final_verdict"]),
        findings=tuple(payload["findings"]),
        deterministic_digest="",
    )
    return replace(record, deterministic_digest=_digest(_normalized_execution(record)))


def _failed_execution(run_id: str, candidate_zip: Path, output_root: Path, finding: str) -> PackageExecutionResult:
    digest = _file_digest(candidate_zip) if candidate_zip.exists() else ""
    record = PackageExecutionResult(
        execution_identifier=run_id,
        candidate_identifier=f"AUTH-CANDIDATE-ZIP-{digest[:16].upper()}" if digest else "",
        candidate_digest=digest,
        extraction_root="",
        output_root=str(output_root),
        candidate_verified=False,
        environment_verified=False,
        candidate_inventory_complete=False,
        candidate_manifest_reconciled=False,
        constitutional_closure_complete=False,
        traceability_complete=False,
        independent_rules_pass=False,
        operational_verification_pass=False,
        focused_tests_pass=False,
        regression_tests_pass=False,
        compilation_pass=False,
        evidence_verified=False,
        final_verdict=PackageCertificationStatus.FAIL,
        findings=(finding,),
        deterministic_digest="",
    )
    return replace(record, deterministic_digest=_digest(_normalized_execution(record)))


def _normalized_execution(result: PackageExecutionResult) -> Mapping[str, Any]:
    data = _jsonable(result)
    data["execution_identifier"] = "<normalized>"
    data["extraction_root"] = "<normalized>"
    data["output_root"] = "<normalized>"
    data["deterministic_digest"] = ""
    return data


def _normalized_compile(record: CompilationEvidence) -> Mapping[str, Any]:
    data = _jsonable(record)
    data["working_directory"] = "<normalized>"
    data["deterministic_digest"] = ""
    return data


def _normalized_final(final: FinalPackageCertification) -> Mapping[str, Any]:
    data = _jsonable(final)
    data["deterministic_digest"] = ""
    return data


def _classify_file(path: str) -> str:
    if path.endswith(".py"):
        return "python_source"
    if path.startswith("Tests/"):
        return "test"
    if path.startswith("Documentation/"):
        return "documentation"
    return "repository_artifact"


def _participates(path: str) -> bool:
    lowered = path.lower()
    return (
        "authorization" in lowered
        or lowered.startswith("tests/test_authorization")
        or lowered.startswith("documentation/auth-")
        or lowered.startswith("src/argos/control_panel/")
    )


def _has_entry(manifest: CandidateManifest, path: str) -> bool:
    return any(entry.canonical_path == path for entry in manifest.entries)


def _verify_operational_state(output_root: Path, manifest: CandidateManifest) -> bool:
    state_path = output_root / "operational_state.json"
    state_path.write_text(json.dumps({"candidate": manifest.candidate_identifier, "digest": manifest.archive_digest}, sort_keys=True), encoding="utf-8")
    return _file_digest(state_path) == hashlib.sha256(state_path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
