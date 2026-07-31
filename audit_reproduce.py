"""Performance Truth independent runtime reproduction entrypoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import locale
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import zipfile
from typing import Any


EXIT_INPUT = 2
EXIT_DISCOVERY = 3
EXIT_VALIDATION = 4

PERFORMANCE_TRUTH_TESTS = (
    "Tests.test_performance_truth_ecs003_audit_003",
)

PERFORMANCE_TRUTH_MODULES = (
    "src/argos/control_panel/performance_truth_engine.py",
    "src/argos/control_panel/strategy_performance_console.py",
    "src/argos/control_panel/trade_attribution_engine.py",
)


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


def _hash_value(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


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
        raise SystemExit(f"Output directory must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)


def _extract_candidate(candidate: Path, workspace: Path) -> Path:
    extract_root = workspace / "candidate"
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(candidate) as archive:
        archive.extractall(extract_root)
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
    candidate_hash_path = output / "candidate_hash.json"
    if candidate_hash_path.exists():
        candidate_hash = json.loads(candidate_hash_path.read_text(encoding="utf-8")).get("sha256", "")
        if candidate_hash:
            env["PERFORMANCE_TRUTH_CANDIDATE_HASH"] = candidate_hash
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    duration = round(time.perf_counter() - started, 4)

    stdout_path = stdout_dir / f"{command_id}.stdout.log"
    stderr_path = stderr_dir / f"{command_id}.stderr.log"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    record = {
        "command_id": command_id,
        "args": args,
        "cwd": str(cwd),
        "returncode": result.returncode,
        "duration_seconds": duration,
        "stdout": str(stdout_path.relative_to(output)).replace("\\", "/"),
        "stderr": str(stderr_path.relative_to(output)).replace("\\", "/"),
    }
    _write(transcript_dir / f"{command_id}.json", record)
    return record


def _discover_performance_truth(root: Path) -> dict[str, Any]:
    source_modules = sorted(path for path in root.rglob("*performance_truth*.py") if path.is_file())
    tests = sorted(path for path in (root / "Tests").glob("test_performance_truth*.py")) if (root / "Tests").exists() else []
    return {
        "source_modules": [_safe_rel(root, path) for path in source_modules],
        "runtime_entrypoints": ["audit_reproduce.py", "Scripts/performance_truth_ecs003_audit_003.py"],
        "test_modules": [_safe_rel(root, path) for path in tests],
        "fixtures": [],
        "configuration": [],
        "certification_utilities": [_safe_rel(root, path) for path in sorted((root / "Scripts").glob("performance_truth*.py"))] if (root / "Scripts").exists() else [],
        "replay_utilities": ["Scripts/performance_truth_ecs003_audit_003.py"],
        "mutation_utilities": ["Scripts/performance_truth_ecs003_audit_003.py"],
        "stress_utilities": ["Scripts/performance_truth_ecs003_audit_003.py"],
    }


def _output_hash_manifest(output: Path) -> list[dict[str, str]]:
    rows = []
    for path in sorted(p for p in output.rglob("*") if p.is_file() and p.name != "output_hash_manifest.json"):
        rows.append({"path": str(path.relative_to(output)).replace("\\", "/"), "sha256": _hash_file(path)})
    return rows


def reproduce(candidate: Path, output: Path) -> int:
    candidate = candidate.resolve()
    output = output.resolve()
    if not candidate.is_file():
        print(f"Candidate ZIP not found: {candidate}", file=sys.stderr)
        return EXIT_INPUT
    try:
        _validate_output(output)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return EXIT_INPUT

    run_id = f"PT-REPRO-{int(time.time())}"
    workspace = output / "_workspace"
    candidate_hash = _hash_file(candidate)
    _write(output / "candidate_hash.json", {"run_id": run_id, "candidate": str(candidate), "sha256": candidate_hash, "bytes": candidate.stat().st_size})

    started = time.perf_counter()
    try:
        root = _extract_candidate(candidate, workspace)
    except (OSError, zipfile.BadZipFile) as exc:
        _write(output / "findings.json", [{"finding_id": "PT-REPRO-FIND-EXTRACT-001", "blocking": True, "error": str(exc)}])
        return EXIT_DISCOVERY

    before_inventory = _inventory(root)
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
        },
    )

    discovery = _discover_performance_truth(root)
    _write(output / "performance_truth_discovery.json", discovery)
    if not discovery["source_modules"]:
        _write(output / "findings.json", [{"finding_id": "PT-REPRO-FIND-DISCOVERY-001", "blocking": True, "error": "No Performance Truth modules discovered."}])
        return EXIT_DISCOVERY

    commands: list[dict[str, Any]] = []
    compile_targets = [str(root / item) for item in PERFORMANCE_TRUTH_MODULES if (root / item).exists()]
    commands.append(_run_command(command_id="compile-performance-truth", args=[sys.executable, "-m", "py_compile", *compile_targets], cwd=root, output=output))

    test_inventory = [
        {"test_identifier": module, "classification": "PERFORMANCE_TRUTH_RUNTIME_REPRODUCTION", "excluded": False}
        for module in PERFORMANCE_TRUTH_TESTS
    ]
    _write(output / "test_inventory.json", test_inventory)
    for index, module in enumerate(PERFORMANCE_TRUTH_TESTS, start=1):
        commands.append(_run_command(command_id=f"runtime-test-{index:03d}", args=[sys.executable, "-m", "unittest", module], cwd=root, output=output, timeout=900))

    commands.append(_run_command(command_id="runtime-audit-003", args=[sys.executable, "Scripts/performance_truth_ecs003_audit_003.py"], cwd=root, output=output, timeout=900))
    _write(output / "command_manifest.json", commands)

    test_results = {
        "total_discovered": len(test_inventory),
        "total_executed": len(test_inventory),
        "passed": sum(1 for command in commands if command["command_id"].startswith("runtime-test") and command["returncode"] == 0),
        "failed": sum(1 for command in commands if command["command_id"].startswith("runtime-test") and command["returncode"] != 0),
        "errored": 0,
        "skipped": 0,
        "deselected": 0,
        "interrupted": 0,
        "timed_out": 0,
        "unavailable": 0,
    }
    _write(output / "test_results.json", test_results)

    generated_audit = root / "Documentation" / "PERFORMANCE_TRUTH_ECS003_AUDIT_003"
    report_map = {
        "behavioral_results.json": "behavioral_validation_report.json",
        "replay_results.json": "deterministic_replay_report.json",
        "fail_closed_results.json": "runtime_mutation_validation_report.json",
        "mutation_results.json": "runtime_mutation_validation_report.json",
        "stress_results.json": "stress_validation_report.json",
    }
    for output_name, source_name in report_map.items():
        source = generated_audit / source_name
        _write(output / output_name, json.loads(source.read_text(encoding="utf-8")) if source.exists() else {"disposition": "UNAVAILABLE"})

    findings = []
    for command in commands:
        if command["returncode"] != 0:
            findings.append({"finding_id": f"PT-REPRO-FIND-{command['command_id'].upper()}", "blocking": True, "command": command})
    after_inventory = _inventory(root)
    before_map = {row["path"]: row["sha256"] for row in before_inventory}
    modified_candidate_paths = [
        row["path"] for row in after_inventory
        if before_map.get(row["path"]) not in {None, row["sha256"]} and not row["path"].startswith("Documentation/PERFORMANCE_TRUTH_ECS003_AUDIT_003/")
    ]
    if modified_candidate_paths:
        findings.append({"finding_id": "PT-REPRO-FIND-CANDIDATE-MODIFICATION", "blocking": True, "modified_paths": modified_candidate_paths})

    _write(output / "findings.json", findings)
    _write(output / "generated_artifact_inventory.json", _inventory(output))
    summary = {
        "run_id": run_id,
        "candidate_hash": candidate_hash,
        "duration_seconds": round(time.perf_counter() - started, 4),
        "blocking_findings": len([row for row in findings if row.get("blocking")]),
        "test_counts": test_results,
        "entrypoint_issues_certification_decision": False,
        "status": "PASS" if not findings else "FAIL",
    }
    _write(output / "execution_summary.json", summary)
    _write(output / "output_hash_manifest.json", _output_hash_manifest(output))
    return 0 if not findings else EXIT_VALIDATION


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce Performance Truth AUDIT-003 runtime validation from a repository package ZIP.")
    parser.add_argument("--candidate", required=True, help="Untouched repository package ZIP.")
    parser.add_argument("--output", required=True, help="New or empty output directory.")
    args = parser.parse_args()
    return reproduce(Path(args.candidate), Path(args.output))


if __name__ == "__main__":
    raise SystemExit(main())
