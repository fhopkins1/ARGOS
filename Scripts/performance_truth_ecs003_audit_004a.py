"""Generate PERFORMANCE-TRUTH-ECS003-AUDIT-004A remediation evidence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_ECS003_AUDIT_004A"
ORDER_SOURCE = Path(r"C:\Users\Fletc\.codex\attachments\0536e004-76cf-4318-bd6a-a55b537c4ce3\pasted-text.txt")
OLD_ATTACHMENT_ID = "8b57da45-406a-4e10-a43a-fa76ff327f2d"
PACKAGE_SET_ID = "PERFORMANCE_TRUTH_ECS003_AUDIT004A"


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


def _rel(path: Path) -> str:
    return str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/")


def _copy_source() -> list[dict[str, Any]]:
    source_dir = OUTPUT_DIR / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    text = ORDER_SOURCE.read_text(encoding="utf-8", errors="replace")
    target = source_dir / "PERFORMANCE-TRUTH-ECS003-AUDIT-004A.txt"
    target.write_text(text, encoding="utf-8")
    return [{"order_id": "PERFORMANCE-TRUTH-ECS003-AUDIT-004A", "preserved_copy": _rel(target), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}]


def _candidate_digest() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        return result.stdout.strip()
    return _hash_value({"repository_root": str(REPOSITORY_ROOT), "git": "unavailable"})


def _stage_runtime_candidate(stage: Path) -> None:
    include = [
        "AUDITOR_README.md",
        "audit_reproduce.py",
        "Scripts/performance_truth_ecs003_audit_003.py",
        "Documentation/PERFORMANCE_TRUTH_ECS003_AUDIT_003/sources/PERFORMANCE-TRUTH-ECS003-AUDIT-003.txt",
        "Tests/test_performance_truth_ecs003_audit_003.py",
    ]
    for rel in include:
        source = REPOSITORY_ROOT / rel
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copytree(REPOSITORY_ROOT / "src", stage / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def _zip_dir(source: Path, target: Path) -> None:
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(source).as_posix())


def _make_runtime_package(path: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pt004a_candidate_stage_") as raw:
        stage = Path(raw) / "candidate"
        stage.mkdir(parents=True)
        _stage_runtime_candidate(stage)
        _zip_dir(stage, path)
    return {"path": _rel(path), "sha256": _hash_file(path), "bytes": path.stat().st_size}


def _copy_reproduction_output(source: Path, target: Path) -> list[str]:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("_workspace", "_pycache"))
    return sorted(_rel(path) for path in target.rglob("*") if path.is_file())


def _run_self_validation(candidate_zip: Path, run_name: str) -> dict[str, Any]:
    raw_output = OUTPUT_DIR / "self_validation_raw" / run_name
    preserved_output = OUTPUT_DIR / "self_validation" / run_name
    if raw_output.exists():
        shutil.rmtree(raw_output)
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(REPOSITORY_ROOT / "audit_reproduce.py"), "--candidate", str(candidate_zip), "--output", str(raw_output)]
    started = time.perf_counter()
    result = subprocess.run(command, cwd=REPOSITORY_ROOT, capture_output=True, text=True, timeout=1200)
    duration = round(time.perf_counter() - started, 4)
    transcript_dir = OUTPUT_DIR / "self_validation_transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    stdout = transcript_dir / f"{run_name}.stdout.log"
    stderr = transcript_dir / f"{run_name}.stderr.log"
    stdout.write_text(result.stdout, encoding="utf-8")
    stderr.write_text(result.stderr, encoding="utf-8")
    files = _copy_reproduction_output(raw_output, preserved_output) if raw_output.exists() else []
    summary_path = preserved_output / "execution_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    test_results = json.loads((preserved_output / "test_results.json").read_text(encoding="utf-8")) if (preserved_output / "test_results.json").exists() else {}
    return {
        "run_id": run_name,
        "command": command,
        "exit_code": result.returncode,
        "duration_seconds": duration,
        "stdout": _rel(stdout),
        "stderr": _rel(stderr),
        "preserved_output": _rel(preserved_output),
        "candidate_hash": summary.get("repository_package_sha256"),
        "test_discovery": summary.get("test_counts", {}).get("total_discovered"),
        "test_execution": test_results,
        "phase_results": summary.get("phase_statuses", {}),
        "final_status": summary.get("status"),
        "file_count": len(files),
        "files": files,
    }


def _canonical(value: Any) -> Any:
    volatile = {"run_id", "duration_seconds", "generation_timestamp", "candidate", "working_directory", "process_command_line", "cwd", "stdout", "stderr", "preserved_output"}
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items() if key not in volatile}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if isinstance(value, str) and ("Temp" in value or "PERFORMANCE_TRUTH_ECS003_AUDIT_004A" in value):
        return "<PATH>"
    return value


def _compare_runs(run_a: Path, run_b: Path) -> dict[str, Any]:
    artifacts = [
        "performance_truth_discovery.json",
        "test_inventory.json",
        "test_results.json",
        "behavioral_results.json",
        "replay_results.json",
        "fail_closed_results.json",
        "mutation_results.json",
        "stress_results.json",
        "findings.json",
        "execution_summary.json",
    ]
    compared = []
    for artifact in artifacts:
        a_path = run_a / artifact
        b_path = run_b / artifact
        a = _canonical(json.loads(a_path.read_text(encoding="utf-8"))) if a_path.exists() else None
        b = _canonical(json.loads(b_path.read_text(encoding="utf-8"))) if b_path.exists() else None
        compared.append({"artifact": artifact, "equivalent": a == b, "run_a_digest": _hash_value(a), "run_b_digest": _hash_value(b)})
    return {"compared_artifacts": compared, "disposition": "PASS" if all(row["equivalent"] for row in compared) else "FAIL", "unexplained_differences": [row for row in compared if not row["equivalent"]]}


def _scan_external_paths() -> dict[str, Any]:
    active_files = [
        REPOSITORY_ROOT / "AUDITOR_README.md",
        REPOSITORY_ROOT / "audit_reproduce.py",
        REPOSITORY_ROOT / "Scripts" / "performance_truth_ecs003_audit_003.py",
        REPOSITORY_ROOT / "Tests" / "test_performance_truth_ecs003_audit_003.py",
    ]
    active_hits = []
    for path in active_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if OLD_ATTACHMENT_ID in text or re.search(r"C:\\Users\\Fletc\\.codex\\attachments", text):
            active_hits.append(_rel(path))
    return {
        "old_attachment_identifier": OLD_ATTACHMENT_ID,
        "active_execution_files_scanned": [_rel(path) for path in active_files],
        "active_developer_local_path_hits": active_hits,
        "active_execution_path_clean": not active_hits,
    }


def _candidate_binding_report(candidate_zip: Path, run_reports: list[dict[str, Any]]) -> dict[str, Any]:
    package_hash = _hash_file(candidate_zip)
    mismatches = [run for run in run_reports if run.get("candidate_hash") != package_hash]
    return {
        "repository_package_sha256": package_hash,
        "run_candidate_hashes": {run["run_id"]: run.get("candidate_hash") for run in run_reports},
        "mismatches": mismatches,
        "disposition": "PASS" if not mismatches else "FAIL",
    }


def generate_evidence() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    packages_dir = OUTPUT_DIR / "runtime_input_package"
    packages_dir.mkdir(parents=True, exist_ok=True)
    candidate_zip = packages_dir / f"{PACKAGE_SET_ID}_RUNTIME_CANDIDATE.zip"
    source = _copy_source()
    runtime_package = _make_runtime_package(candidate_zip)
    run_a = _run_self_validation(candidate_zip, "run_a")
    run_b = _run_self_validation(candidate_zip, "run_b")
    comparison = _compare_runs(OUTPUT_DIR / "self_validation" / "run_a", OUTPUT_DIR / "self_validation" / "run_b")
    external_paths = _scan_external_paths()
    binding = _candidate_binding_report(candidate_zip, [run_a, run_b])
    implementation_changes = [
        {"path": "audit_reproduce.py", "classification": ["audit path resolution", "test discovery", "audit orchestration", "evidence gating", "hash binding"], "authorized": True},
        {"path": "AUDITOR_README.md", "classification": ["documentation"], "authorized": True},
        {"path": "Scripts/performance_truth_ecs003_audit_003.py", "classification": ["audit input packaging"], "authorized": True},
        {"path": "Scripts/performance_truth_ecs003_audit_003a_package_correction.py", "classification": ["audit input packaging"], "authorized": True},
        {"path": "Scripts/performance_truth_ecs003_audit_004a.py", "classification": ["packaging", "documentation"], "authorized": True},
        {"path": "Tests/test_performance_truth_ecs003_audit_004a.py", "classification": ["audit-harness testing"], "authorized": True},
    ]
    findings = []
    if run_a["exit_code"] != 0 or run_b["exit_code"] != 0:
        findings.append({"finding_id": "PT-AUDIT004A-FIND-001", "blocking": True, "title": "Self-validation reproduction failed", "run_a_exit_code": run_a["exit_code"], "run_b_exit_code": run_b["exit_code"]})
    if comparison["disposition"] != "PASS":
        findings.append({"finding_id": "PT-AUDIT004A-FIND-002", "blocking": True, "title": "Self-validation outputs are not deterministic", "differences": comparison["unexplained_differences"]})
    if not external_paths["active_execution_path_clean"]:
        findings.append({"finding_id": "PT-AUDIT004A-FIND-003", "blocking": True, "title": "Active developer-local path remains", "hits": external_paths["active_developer_local_path_hits"]})
    if binding["disposition"] != "PASS":
        findings.append({"finding_id": "PT-AUDIT004A-FIND-004", "blocking": True, "title": "Candidate hash binding mismatch", "mismatches": binding["mismatches"]})

    completion = {
        "order": "PERFORMANCE-TRUTH-ECS003-AUDIT-004A",
        "candidate_digest": _candidate_digest(),
        "completion_decision": "COMPLETE" if not findings else "INCOMPLETE",
        "ecs003_certification_issued": False,
        "business_logic_modified": False,
        "blocking_findings": len(findings),
        "ready_for_new_independent_runtime_audit": not findings,
    }
    _write(OUTPUT_DIR / "source_order_registry.json", source)
    _write(OUTPUT_DIR / "corrected_runtime_input_package.json", runtime_package)
    _write(OUTPUT_DIR / "run_a_self_validation_package.json", run_a)
    _write(OUTPUT_DIR / "run_b_self_validation_package.json", run_b)
    _write(OUTPUT_DIR / "deterministic_comparison_report.json", comparison)
    _write(OUTPUT_DIR / "external_path_removal_report.json", external_paths)
    _write(OUTPUT_DIR / "active_input_inventory.json", json.loads((OUTPUT_DIR / "self_validation" / "run_a" / "active_input_inventory.json").read_text(encoding="utf-8")))
    _write(OUTPUT_DIR / "candidate_binding_report.json", binding)
    _write(OUTPUT_DIR / "package_set_manifest.json", {"package_set_id": PACKAGE_SET_ID, "runtime_candidate_package": runtime_package, "evidence_candidate_hash": binding["repository_package_sha256"], "consistency_result": binding["disposition"]})
    _write(OUTPUT_DIR / "implementation_change_manifest.json", implementation_changes)
    _write(OUTPUT_DIR / "findings_register.json", findings)
    _write(OUTPUT_DIR / "order_completion_report.json", completion)
    return completion


if __name__ == "__main__":
    print(_json(generate_evidence()))
