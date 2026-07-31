"""Performance Truth independent runtime reproduction entrypoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import locale
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import zipfile
from typing import Any


EXIT_INPUT = 2
EXIT_DISCOVERY = 3
EXIT_VALIDATION = 4

TOOL_VERSION = "performance-truth-audit-reproduce/004A"

PERFORMANCE_TRUTH_MODULES = (
    "src/argos/control_panel/performance_truth_engine.py",
    "src/argos/control_panel/strategy_performance_console.py",
    "src/argos/control_panel/trade_attribution_engine.py",
)

CERTIFICATION_PHASES = {
    "behavioral_results.json": "behavioral_validation_report.json",
    "replay_results.json": "deterministic_replay_report.json",
    "fail_closed_results.json": "runtime_mutation_validation_report.json",
    "mutation_results.json": "runtime_mutation_validation_report.json",
    "stress_results.json": "stress_validation_report.json",
}


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, default=str) + "\n"


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value), encoding="utf-8")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = str(path.relative_to(root)).replace("\\", "/")
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_hash_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _safe_rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _redacted_env() -> dict[str, str]:
    relevant_prefixes = ("PYTHON", "ARGOS", "PATH", "VIRTUAL_ENV", "TZ", "LANG")
    secret_terms = ("SECRET", "TOKEN", "KEY", "PASSWORD", "CREDENTIAL")
    result: dict[str, str] = {}
    for key, value in sorted(os.environ.items()):
        if key.upper().startswith(relevant_prefixes):
            result[key] = "<REDACTED>" if any(term in key.upper() for term in secret_terms) else value
    return result


def _validate_output(output: Path) -> None:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)


def _is_windows_user_profile(path_text: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/](Users|Documents and Settings)[\\/]", path_text))


def resolve_repository_relative_input(root: Path, input_path: str) -> Path:
    """Resolve an input path only when it is contained under the extracted candidate."""

    if not input_path or input_path.strip() != input_path:
        raise ValueError("Input path is empty or contains leading/trailing whitespace.")
    if input_path.startswith("~") or _is_windows_user_profile(input_path):
        raise ValueError(f"Developer-local or user-profile input rejected: {input_path}")
    candidate = Path(input_path)
    if candidate.is_absolute():
        raise ValueError(f"Absolute input path rejected: {input_path}")
    resolved = (root / candidate).resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Input path escapes extracted candidate root: {input_path}") from exc
    if not resolved.exists():
        raise FileNotFoundError(f"Required repository input is absent: {input_path}")
    return resolved


def _safe_extract(candidate: Path, extract_root: Path) -> None:
    with zipfile.ZipFile(candidate) as archive:
        for info in archive.infolist():
            normalized = info.filename.replace("\\", "/")
            if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
                raise ValueError(f"Unsafe archive member rejected: {info.filename}")
        archive.extractall(extract_root)


def _extract_candidate(candidate: Path, workspace: Path) -> Path:
    extract_root = workspace / "candidate"
    extract_root.mkdir(parents=True, exist_ok=True)
    _safe_extract(candidate, extract_root)
    entries = [item for item in extract_root.iterdir()]
    if len(entries) == 1 and entries[0].is_dir() and (entries[0] / "src").exists():
        return entries[0]
    return extract_root


def _inventory(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rows.append({"path": _safe_rel(root, path), "bytes": path.stat().st_size, "sha256": _hash_file(path)})
    return rows


def _run_command(
    *,
    command_id: str,
    args: list[str],
    cwd: Path,
    output: Path,
    run_id: str,
    candidate_hash: str,
    root_manifest_hash: str,
    timeout: int = 600,
) -> dict[str, Any]:
    stdout_dir = output / "stdout"
    stderr_dir = output / "stderr"
    transcript_dir = output / "transcripts"
    stdout_dir.mkdir(parents=True, exist_ok=True)
    stderr_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{cwd}{os.pathsep}{cwd / 'src'}{os.pathsep}{cwd / 'Scripts'}"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = str(output / "_pycache" / command_id)
    env["PERFORMANCE_TRUTH_CANDIDATE_HASH"] = candidate_hash
    env["PERFORMANCE_TRUTH_ROOT_MANIFEST_HASH"] = root_manifest_hash
    status = "PASS"
    returncode: int | None = None
    stdout_text = ""
    stderr_text = ""
    timed_out = False
    try:
        result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        returncode = result.returncode
        stdout_text = result.stdout
        stderr_text = result.stderr
        if result.returncode != 0:
            status = "FAIL"
    except subprocess.TimeoutExpired as exc:
        status = "TIMEOUT"
        timed_out = True
        stdout_text = exc.stdout or ""
        stderr_text = exc.stderr or ""
        if isinstance(stdout_text, bytes):
            stdout_text = stdout_text.decode("utf-8", errors="replace")
        if isinstance(stderr_text, bytes):
            stderr_text = stderr_text.decode("utf-8", errors="replace")
    duration = round(time.perf_counter() - started, 4)

    stdout_path = stdout_dir / f"{command_id}.stdout.log"
    stderr_path = stderr_dir / f"{command_id}.stderr.log"
    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")
    record = {
        "command_id": command_id,
        "args": args,
        "cwd": str(cwd),
        "returncode": returncode,
        "status": status,
        "timed_out": timed_out,
        "duration_seconds": duration,
        "stdout": str(stdout_path.relative_to(output)).replace("\\", "/"),
        "stderr": str(stderr_path.relative_to(output)).replace("\\", "/"),
        "run_id": run_id,
        "repository_package_sha256": candidate_hash,
        "candidate_root_manifest_sha256": root_manifest_hash,
        "generation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool_version": TOOL_VERSION,
    }
    _write(transcript_dir / f"{command_id}.json", record)
    return record


def _discover_performance_truth(root: Path) -> dict[str, Any]:
    source_modules = sorted(path for path in root.rglob("*performance_truth*.py") if path.is_file())
    all_tests = sorted(path for path in (root / "Tests").glob("test_performance_truth*.py")) if (root / "Tests").exists() else []
    runtime_tests: list[Path] = []
    exclusions: list[dict[str, Any]] = []
    for path in all_tests:
        rel = _safe_rel(root, path)
        text = path.read_text(encoding="utf-8", errors="replace")
        is_runtime = (
            "performance_truth_ecs003_audit_003" in rel
            and "package_correction" not in rel
            and "audit_004" not in rel
        ) or "PerformanceTruthEngine" in text
        if is_runtime:
            runtime_tests.append(path)
        else:
            exclusions.append(
                {
                    "test_module": rel,
                    "excluded": True,
                    "constitutional_justification": "Audit-harness, package-correction, documentation, or report-generation test; not a Performance Truth runtime behavioral test.",
                }
            )
    return {
        "source_modules": [_safe_rel(root, path) for path in source_modules],
        "runtime_entrypoints": ["audit_reproduce.py", "Scripts/performance_truth_ecs003_audit_003.py"],
        "test_modules": [_safe_rel(root, path) for path in runtime_tests],
        "excluded_test_modules": exclusions,
        "fixtures": [],
        "configuration": [],
        "certification_utilities": [_safe_rel(root, path) for path in sorted((root / "Scripts").glob("performance_truth*.py"))] if (root / "Scripts").exists() else [],
        "replay_utilities": ["Scripts/performance_truth_ecs003_audit_003.py"],
        "mutation_utilities": ["Scripts/performance_truth_ecs003_audit_003.py"],
        "stress_utilities": ["Scripts/performance_truth_ecs003_audit_003.py"],
    }


def _module_name(root: Path, test_path: Path) -> str:
    return _safe_rel(root, test_path).removesuffix(".py").replace("/", ".")


def _parse_unittest_counts(commands: list[dict[str, Any]], output: Path) -> dict[str, int]:
    counts = {
        "collected": len([command for command in commands if command["command_id"].startswith("runtime-test")]),
        "executed": 0,
        "passed": 0,
        "failed": 0,
        "errored": 0,
        "skipped": 0,
        "deselected": 0,
        "interrupted": 0,
        "timed_out": 0,
        "unavailable": 0,
    }
    for command in commands:
        if not command["command_id"].startswith("runtime-test"):
            continue
        stderr = (output / command["stderr"]).read_text(encoding="utf-8", errors="replace")
        stdout = (output / command["stdout"]).read_text(encoding="utf-8", errors="replace")
        combined = stdout + "\n" + stderr
        ran = re.search(r"Ran\s+(\d+)\s+tests?", combined)
        executed = int(ran.group(1)) if ran else 0
        counts["executed"] += executed
        skipped = re.search(r"skipped=(\d+)", combined)
        if skipped:
            counts["skipped"] += int(skipped.group(1))
        if command["status"] == "TIMEOUT":
            counts["timed_out"] += 1
        elif command["returncode"] != 0:
            failures = re.search(r"failures=(\d+)", combined)
            errors = re.search(r"errors=(\d+)", combined)
            if failures:
                counts["failed"] += int(failures.group(1))
            if errors:
                counts["errored"] += int(errors.group(1))
            if not failures and not errors:
                counts["failed"] += max(executed, 1)
        else:
            counts["passed"] += executed
    return counts


def _output_hash_manifest(output: Path) -> list[dict[str, str]]:
    rows = []
    for path in sorted(p for p in output.rglob("*") if p.is_file() and p.name != "output_hash_manifest.json"):
        rows.append({"path": str(path.relative_to(output)).replace("\\", "/"), "sha256": _hash_file(path)})
    return rows


def _phase_result(
    *,
    output_name: str,
    source_name: str,
    source_dir: Path,
    controlling_command: dict[str, Any] | None,
    upstream_failed: bool,
    run_id: str,
    candidate_hash: str,
    root_manifest_hash: str,
) -> Any:
    command_id = controlling_command["command_id"] if controlling_command else "UNAVAILABLE"
    base = {
        "run_id": run_id,
        "repository_package_sha256": candidate_hash,
        "candidate_root_manifest_sha256": root_manifest_hash,
        "generation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "controlling_command_id": command_id,
        "tool_version": TOOL_VERSION,
        "derivation_chain": {
            "raw_command": command_id,
            "raw_result": controlling_command,
            "phase_result_source": source_name,
        },
    }
    if upstream_failed:
        return {**base, "disposition": "NOT_EXECUTED", "status": "NOT_EXECUTED", "reason": "Upstream required execution failed; dependent PASS artifact blocked."}
    if not controlling_command or controlling_command.get("status") != "PASS" or controlling_command.get("returncode") != 0:
        return {**base, "disposition": "FAIL", "status": "FAIL", "reason": "Controlling execution failed; PASS artifact blocked."}
    source = source_dir / source_name
    if not source.exists():
        return {**base, "disposition": "FAIL", "status": "FAIL", "reason": f"Required phase source missing: {source_name}"}
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = {**payload, **base}
    elif isinstance(payload, list):
        payload = [{**item, **base} if isinstance(item, dict) else {"value": item, **base} for item in payload]
    else:
        payload = {"value": payload, **base}
    return payload


def reproduce(candidate: Path, output: Path) -> int:
    candidate = candidate.resolve()
    output = output.resolve()
    if not candidate.is_file():
        print(f"Candidate ZIP not found: {candidate}", file=sys.stderr)
        return EXIT_INPUT
    try:
        _validate_output(output)
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return EXIT_INPUT

    run_id = f"PT-REPRO-{int(time.time())}"
    workspace = output / "_workspace"
    candidate_hash = _hash_file(candidate)
    started = time.perf_counter()
    _write(
        output / "candidate_hash.json",
        {
            "run_id": run_id,
            "candidate": str(candidate),
            "sha256": candidate_hash,
            "bytes": candidate.stat().st_size,
            "generation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tool_version": TOOL_VERSION,
        },
    )

    findings: list[dict[str, Any]] = []
    try:
        root = _extract_candidate(candidate, workspace)
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        _write(output / "findings.json", [{"finding_id": "PT-REPRO-FIND-EXTRACT-001", "blocking": True, "error": str(exc)}])
        return EXIT_DISCOVERY

    def certification_inventory(candidate_root: Path) -> list[dict[str, Any]]:
        return [row for row in _inventory(candidate_root) if "__pycache__/" not in row["path"] and not row["path"].endswith(".pyc")]

    before_inventory = certification_inventory(root)
    root_manifest_hash = _hash_tree(root)
    _write(output / "repository_inventory.json", before_inventory)
    _write(
        output / "environment.json",
        {
            "run_id": run_id,
            "os": platform.platform(),
            "architecture": platform.machine(),
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "working_directory": str(root),
            "environment": _redacted_env(),
            "timezone": time.tzname,
            "locale": locale.getlocale(),
            "process_command_line": sys.argv,
            "repository_package_sha256": candidate_hash,
            "candidate_root_manifest_sha256": root_manifest_hash,
            "tool_version": TOOL_VERSION,
        },
    )

    required_inputs = [
        "AUDITOR_README.md",
        "audit_reproduce.py",
        "Scripts/performance_truth_ecs003_audit_003.py",
    ]
    active_inputs = []
    for item in required_inputs:
        try:
            resolved = resolve_repository_relative_input(root, item)
            active_inputs.append({"path": item, "resolved_path": str(resolved), "sha256": _hash_file(resolved), "status": "PRESENT"})
        except (OSError, ValueError) as exc:
            active_inputs.append({"path": item, "status": "FAIL", "error": str(exc)})
            findings.append({"finding_id": f"PT-REPRO-FIND-INPUT-{len(findings)+1:03d}", "blocking": True, "error": str(exc)})
    _write(output / "active_input_inventory.json", active_inputs)
    if findings:
        _write(output / "findings.json", findings)
        return EXIT_INPUT

    discovery = _discover_performance_truth(root)
    _write(output / "performance_truth_discovery.json", discovery)
    if not discovery["source_modules"]:
        findings.append({"finding_id": "PT-REPRO-FIND-DISCOVERY-001", "blocking": True, "error": "No Performance Truth modules discovered."})
    if not discovery["test_modules"]:
        findings.append({"finding_id": "PT-REPRO-FIND-DISCOVERY-002", "blocking": True, "error": "No Performance Truth runtime tests discovered."})
    if findings:
        _write(output / "findings.json", findings)
        return EXIT_DISCOVERY

    commands: list[dict[str, Any]] = []
    compile_targets = [str(root / item) for item in PERFORMANCE_TRUTH_MODULES if (root / item).exists()]
    commands.append(_run_command(command_id="compile-performance-truth", args=[sys.executable, "-m", "py_compile", *compile_targets], cwd=root, output=output, run_id=run_id, candidate_hash=candidate_hash, root_manifest_hash=root_manifest_hash))

    test_inventory = [
        {
            "test_identifier": _module_name(root, root / module),
            "test_path": module,
            "classification": "PERFORMANCE_TRUTH_RUNTIME_REPRODUCTION",
            "excluded": False,
            "repository_package_sha256": candidate_hash,
            "candidate_root_manifest_sha256": root_manifest_hash,
            "run_id": run_id,
        }
        for module in discovery["test_modules"]
    ]
    test_inventory.extend(discovery["excluded_test_modules"])
    _write(output / "test_inventory.json", test_inventory)
    for index, module in enumerate(discovery["test_modules"], start=1):
        commands.append(
            _run_command(
                command_id=f"runtime-test-{index:03d}",
                args=[sys.executable, "-m", "unittest", "-v", _module_name(root, root / module)],
                cwd=root,
                output=output,
                run_id=run_id,
                candidate_hash=candidate_hash,
                root_manifest_hash=root_manifest_hash,
                timeout=900,
            )
        )

    runtime_tests_failed = any(command["status"] != "PASS" or command["returncode"] != 0 for command in commands if command["command_id"].startswith("runtime-test"))
    if runtime_tests_failed:
        audit_command = {
            "command_id": "runtime-audit-003",
            "args": [sys.executable, "Scripts/performance_truth_ecs003_audit_003.py"],
            "cwd": str(root),
            "returncode": None,
            "status": "NOT_EXECUTED",
            "timed_out": False,
            "reason": "Runtime test failure blocks dependent audit artifact generation.",
            "run_id": run_id,
            "repository_package_sha256": candidate_hash,
            "candidate_root_manifest_sha256": root_manifest_hash,
            "tool_version": TOOL_VERSION,
        }
        commands.append(audit_command)
    else:
        commands.append(
            _run_command(
                command_id="runtime-audit-003",
                args=[sys.executable, "Scripts/performance_truth_ecs003_audit_003.py"],
                cwd=root,
                output=output,
                run_id=run_id,
                candidate_hash=candidate_hash,
                root_manifest_hash=root_manifest_hash,
                timeout=900,
            )
        )
    _write(output / "command_manifest.json", commands)

    test_counts = _parse_unittest_counts(commands, output)
    test_results = {
        "run_id": run_id,
        "repository_package_sha256": candidate_hash,
        "candidate_root_manifest_sha256": root_manifest_hash,
        "total_discovered": len(discovery["test_modules"]),
        "total_executed": test_counts["executed"],
        "passed": test_counts["passed"],
        "failed": test_counts["failed"],
        "errored": test_counts["errored"],
        "skipped": test_counts["skipped"],
        "deselected": test_counts["deselected"],
        "interrupted": test_counts["interrupted"],
        "timed_out": test_counts["timed_out"],
        "unavailable": test_counts["unavailable"],
        "process_exit_codes": {command["command_id"]: command.get("returncode") for command in commands},
        "tool_version": TOOL_VERSION,
    }
    _write(output / "test_results.json", test_results)
    if test_results["total_discovered"] == 0 or test_results["total_executed"] == 0:
        findings.append({"finding_id": "PT-REPRO-FIND-ZERO-TESTS", "blocking": True, "error": "Zero tests discovered or executed.", "raw_test_result": test_results})
    if test_results["failed"] or test_results["errored"] or test_results["timed_out"]:
        findings.append({"finding_id": "PT-REPRO-FIND-RUNTIME-TESTS", "blocking": True, "error": "One or more runtime tests failed, errored, or timed out.", "raw_test_result": test_results})

    generated_audit = root / "Documentation" / "PERFORMANCE_TRUTH_ECS003_AUDIT_003"
    audit_control = next((command for command in commands if command["command_id"] == "runtime-audit-003"), None)
    upstream_failed = bool(findings) or any(command["status"] in {"FAIL", "TIMEOUT", "ERROR"} for command in commands if command["command_id"] != "runtime-audit-003")
    for output_name, source_name in CERTIFICATION_PHASES.items():
        _write(
            output / output_name,
            _phase_result(
                output_name=output_name,
                source_name=source_name,
                source_dir=generated_audit,
                controlling_command=audit_control,
                upstream_failed=upstream_failed,
                run_id=run_id,
                candidate_hash=candidate_hash,
                root_manifest_hash=root_manifest_hash,
            ),
        )

    for command in commands:
        if command.get("status") in {"FAIL", "TIMEOUT", "ERROR", "NOT_EXECUTED"} or (command.get("returncode") not in {0, None}):
            findings.append({"finding_id": f"PT-REPRO-FIND-{command['command_id'].upper()}", "blocking": True, "command": command})
    after_inventory = certification_inventory(root)
    before_map = {row["path"]: row["sha256"] for row in before_inventory}
    modified_candidate_paths = [
        row["path"] for row in after_inventory
        if before_map.get(row["path"]) not in {None, row["sha256"]} and not row["path"].startswith("Documentation/PERFORMANCE_TRUTH_ECS003_AUDIT_003/")
    ]
    if modified_candidate_paths:
        findings.append({"finding_id": "PT-REPRO-FIND-CANDIDATE-MODIFICATION", "blocking": True, "modified_paths": modified_candidate_paths})

    _write(output / "findings.json", findings)
    _write(output / "generated_artifact_inventory.json", _inventory(output))
    summary_status = "PASS" if not findings else "FAIL"
    summary = {
        "run_id": run_id,
        "repository_package_sha256": candidate_hash,
        "candidate_root_manifest_sha256": root_manifest_hash,
        "duration_seconds": round(time.perf_counter() - started, 4),
        "blocking_findings": len([row for row in findings if row.get("blocking")]),
        "test_counts": test_results,
        "phase_statuses": {
            name: (json.loads((output / name).read_text(encoding="utf-8")).get("disposition") if isinstance(json.loads((output / name).read_text(encoding="utf-8")), dict) else "SEE_RECORDS")
            for name in CERTIFICATION_PHASES
        },
        "entrypoint_issues_certification_decision": False,
        "status": summary_status,
        "tool_version": TOOL_VERSION,
    }
    _write(output / "execution_summary.json", summary)
    _write(output / "output_hash_manifest.json", _output_hash_manifest(output))
    return 0 if not findings else EXIT_VALIDATION


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce Performance Truth runtime validation from a repository package ZIP.")
    parser.add_argument("--candidate", required=True, help="Untouched repository package ZIP.")
    parser.add_argument("--output", required=True, help="New or empty output directory.")
    args = parser.parse_args()
    return reproduce(Path(args.candidate), Path(args.output))


if __name__ == "__main__":
    raise SystemExit(main())
