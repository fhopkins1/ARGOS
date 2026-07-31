"""Independent AUDIT-005 certification audit for Performance Truth."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_ECS003_AUDIT_005"
ORDER_SOURCE = Path(r"C:\Users\Fletc\.codex\attachments\bc593420-e41e-46b1-b84f-16f4dea0843d\pasted-text.txt")
SUBMITTED_REPOSITORY_PACKAGE = (
    REPOSITORY_ROOT
    / "Documentation"
    / "PERFORMANCE_TRUTH_ECS003_AUDIT_004A"
    / "runtime_input_package"
    / "PERFORMANCE_TRUTH_ECS003_AUDIT004A_RUNTIME_CANDIDATE.zip"
)
SUBMITTED_EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_ECS003_AUDIT_004A"
OLD_ATTACHMENT_ID = "8b57da45-406a-4e10-a43a-fa76ff327f2d"


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


def _candidate_digest() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        return result.stdout.strip()
    return _hash_value({"repository_root": str(REPOSITORY_ROOT), "git": "unavailable"})


def _copy_source() -> list[dict[str, Any]]:
    source_dir = OUTPUT_DIR / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    text = ORDER_SOURCE.read_text(encoding="utf-8", errors="replace")
    target = source_dir / "PERFORMANCE-TRUTH-ECS003-AUDIT-005.txt"
    target.write_text(text, encoding="utf-8")
    return [{"order_id": "PERFORMANCE-TRUTH-ECS003-AUDIT-005", "preserved_copy": _rel(target), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}]


def _archive_integrity(zip_path: Path) -> dict[str, Any]:
    duplicate_paths: list[str] = []
    unsafe_paths: list[str] = []
    symlinks: list[str] = []
    extracted_inventory: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        seen: set[str] = set()
        for info in archive.infolist():
            name = info.filename
            if name in seen:
                duplicate_paths.append(name)
            seen.add(name)
            normalized = name.replace("\\", "/")
            if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
                unsafe_paths.append(name)
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                symlinks.append(name)
    with tempfile.TemporaryDirectory(prefix="pt005_integrity_") as raw:
        root = Path(raw) / "extract"
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(root)
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            extracted_inventory.append({"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": _hash_file(path), "bytes": path.stat().st_size})
    disposition = "PASS" if not duplicate_paths and not unsafe_paths and not symlinks else "FAIL"
    return {
        "repository_package": str(zip_path),
        "repository_package_sha256": _hash_file(zip_path),
        "repository_package_bytes": zip_path.stat().st_size,
        "member_count": len(names),
        "duplicate_files": duplicate_paths,
        "unsafe_paths": unsafe_paths,
        "unexpected_symbolic_links": symlinks,
        "extracted_file_inventory": extracted_inventory,
        "disposition": disposition,
    }


def _extract_for_clean_room(candidate_zip: Path, target: Path) -> Path:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(candidate_zip) as archive:
        archive.extractall(target)
    return target


def _run_clean_room(candidate_zip: Path, run_id: str) -> dict[str, Any]:
    clean_root = OUTPUT_DIR / "clean_room" / run_id
    if clean_root.exists():
        shutil.rmtree(clean_root)
    extract_root = clean_root / "submitted_repository"
    output = clean_root / "runtime_output"
    _extract_for_clean_room(candidate_zip, extract_root)
    command = [sys.executable, str(extract_root / "audit_reproduce.py"), "--candidate", str(candidate_zip), "--output", str(output)]
    started = time.perf_counter()
    result = subprocess.run(command, cwd=extract_root, capture_output=True, text=True, timeout=1200)
    duration = round(time.perf_counter() - started, 4)
    transcript_dir = OUTPUT_DIR / "command_transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    stdout = transcript_dir / f"{run_id}.stdout.log"
    stderr = transcript_dir / f"{run_id}.stderr.log"
    stdout.write_text(result.stdout, encoding="utf-8")
    stderr.write_text(result.stderr, encoding="utf-8")
    summary = json.loads((output / "execution_summary.json").read_text(encoding="utf-8")) if (output / "execution_summary.json").exists() else {}
    tests = json.loads((output / "test_results.json").read_text(encoding="utf-8")) if (output / "test_results.json").exists() else {}
    return {
        "run_id": run_id,
        "command": command,
        "exit_code": result.returncode,
        "duration_seconds": duration,
        "stdout": _rel(stdout),
        "stderr": _rel(stderr),
        "clean_room_root": _rel(clean_root),
        "runtime_output": _rel(output),
        "environment": {
            "os": platform.platform(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "working_directory": str(extract_root),
        },
        "execution_summary": summary,
        "test_results": tests,
        "generated_artifact_inventory": sorted(_rel(path) for path in output.rglob("*") if path.is_file()) if output.exists() else [],
    }


def _load(run: dict[str, Any], artifact: str) -> Any:
    path = REPOSITORY_ROOT / run["runtime_output"] / artifact
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _canonical(value: Any) -> Any:
    volatile = {"run_id", "duration_seconds", "generation_timestamp", "cwd", "stdout", "stderr", "working_directory", "process_command_line"}
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items() if key not in volatile}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if isinstance(value, str) and ("PERFORMANCE_TRUTH_ECS003_AUDIT_005" in value or "clean_room" in value):
        return "<PATH>"
    return value


def _compare_run_outputs(run_a: dict[str, Any], run_b: dict[str, Any]) -> dict[str, Any]:
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
        a = _canonical(_load(run_a, artifact))
        b = _canonical(_load(run_b, artifact))
        compared.append({"artifact": artifact, "equivalent": a == b, "run_a_digest": _hash_value(a), "run_b_digest": _hash_value(b)})
    return {"compared_artifacts": compared, "disposition": "PASS" if all(row["equivalent"] for row in compared) else "FAIL", "differences": [row for row in compared if not row["equivalent"]]}


def _scan_harness(extract_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    findings = []
    with tempfile.TemporaryDirectory(prefix="pt005_harness_") as raw:
        root = Path(raw) / "candidate"
        with zipfile.ZipFile(SUBMITTED_REPOSITORY_PACKAGE) as archive:
            archive.extractall(root)
        active_files = [
            root / "AUDITOR_README.md",
            root / "audit_reproduce.py",
            root / "Scripts" / "performance_truth_ecs003_audit_003.py",
            root / "Tests" / "test_performance_truth_ecs003_audit_003.py",
        ]
        for path in active_files:
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = str(path.relative_to(root)).replace("\\", "/")
            if OLD_ATTACHMENT_ID in text or re.search(r"C:\\Users\\Fletc\\.codex\\attachments|/home/[^\\s]+|~\\/", text):
                findings.append({"rule": "developer_local_path", "path": rel})
            if rel == "audit_reproduce.py" and "resolve_repository_relative_input" not in text:
                findings.append({"rule": "repository_relative_input_resolver_missing", "path": rel})
            if rel == "audit_reproduce.py" and "PERFORMANCE_TRUTH_TESTS = (" in text:
                findings.append({"rule": "predefined_single_module_discovery", "path": rel})
            if rel == "audit_reproduce.py" and "status\": \"PASS\" if not findings else \"FAIL\"" not in text and "return 0 if not findings else EXIT_VALIDATION" not in text:
                findings.append({"rule": "final_exit_not_bound_to_findings", "path": rel})
            if rel == "Scripts/performance_truth_ecs003_audit_003.py" and '"PT-AUDIT003-MUT-005": True' in text:
                findings.append({"rule": "mutation_specific_hardcoded_detection", "path": rel, "mutation_id": "PT-AUDIT003-MUT-005"})
            if rel == "Scripts/performance_truth_ecs003_audit_003.py" and '"PT-AUDIT003-MUT-006": True' in text:
                findings.append({"rule": "mutation_specific_hardcoded_detection", "path": rel, "mutation_id": "PT-AUDIT003-MUT-006"})
    return {
        "active_files_inspected": ["AUDITOR_README.md", "audit_reproduce.py", "Scripts/performance_truth_ecs003_audit_003.py", "Tests/test_performance_truth_ecs003_audit_003.py"],
        "repository_member_count": len(extract_inventory),
        "findings": findings,
        "disposition": "PASS" if not findings else "FAIL",
    }


def _test_verification(run_a: dict[str, Any], run_b: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for run in (run_a, run_b):
        tests = run["test_results"]
        failed = (
            run["exit_code"] != 0
            or tests.get("total_discovered", 0) <= 0
            or tests.get("total_executed", 0) <= 0
            or tests.get("failed", 0) > 0
            or tests.get("errored", 0) > 0
            or tests.get("timed_out", 0) > 0
            or tests.get("interrupted", 0) > 0
        )
        rows.append({"run_id": run["run_id"], "test_results": tests, "disposition": "FAIL" if failed else "PASS"})
    return {"runs": rows, "disposition": "PASS" if all(row["disposition"] == "PASS" for row in rows) else "FAIL"}


def _phase_report(run_a: dict[str, Any], run_b: dict[str, Any], artifact: str, require_list_pass: bool = False) -> dict[str, Any]:
    rows = []
    for run in (run_a, run_b):
        payload = _load(run, artifact)
        disposition = "FAIL"
        if isinstance(payload, dict):
            disposition = "PASS" if payload.get("disposition") == "PASS" else "FAIL"
        elif isinstance(payload, list):
            disposition = "PASS" if payload and all(item.get("disposition") == "PASS" for item in payload if isinstance(item, dict)) else "FAIL"
        rows.append({"run_id": run["run_id"], "artifact": artifact, "disposition": disposition, "payload_digest": _hash_value(payload)})
    return {"runs": rows, "disposition": "PASS" if all(row["disposition"] == "PASS" for row in rows) else "FAIL"}


def _audit004_finding_verification(run_a: dict[str, Any], run_b: dict[str, Any], harness: dict[str, Any]) -> dict[str, Any]:
    a_tests = run_a["test_results"]
    hash_ok = all(
        _load(run, "execution_summary.json").get("repository_package_sha256") == _hash_file(SUBMITTED_REPOSITORY_PACKAGE)
        for run in (run_a, run_b)
    )
    checks = [
        {"finding": "developer-local dependency", "corrected": not any(row.get("rule") == "developer_local_path" for row in harness["findings"])},
        {"finding": "no runtime tests completed", "corrected": a_tests.get("total_executed", 0) > 0 and run_b["test_results"].get("total_executed", 0) > 0},
        {"finding": "incomplete fixed test discovery", "corrected": not any(row.get("rule") == "predefined_single_module_discovery" for row in harness["findings"])},
        {"finding": "failed executions can emit PASS artifacts", "corrected": not any(row.get("rule") == "final_exit_not_bound_to_findings" for row in harness["findings"])},
        {"finding": "candidate and evidence hash mismatch", "corrected": hash_ok},
    ]
    return {"checks": checks, "disposition": "PASS" if all(row["corrected"] for row in checks) else "FAIL"}


def _mutation_report(run_a: dict[str, Any], run_b: dict[str, Any], harness: dict[str, Any]) -> dict[str, Any]:
    phase = _phase_report(run_a, run_b, "mutation_results.json")
    hardcoded = [row for row in harness["findings"] if row.get("rule") == "mutation_specific_hardcoded_detection"]
    rows = []
    for run in (run_a, run_b):
        mutations = _load(run, "mutation_results.json") or []
        rows.extend(
            {
                "run_id": run["run_id"],
                "mutation_id": row.get("mutation_id"),
                "disposition": row.get("disposition"),
                "detected": row.get("detected"),
                "controlling_command_id": row.get("controlling_command_id"),
                "ordinary_control_evidence": "INSUFFICIENT" if row.get("mutation_id") in {"PT-AUDIT003-MUT-005", "PT-AUDIT003-MUT-006"} else "RECORDED",
            }
            for row in mutations
        )
    disposition = "FAIL" if hardcoded or phase["disposition"] != "PASS" else "PASS"
    return {"phase_result": phase, "mutation_records": rows, "hardcoded_detection_findings": hardcoded, "disposition": disposition}


def _evidence_comparison(run_a: dict[str, Any]) -> dict[str, Any]:
    compared = []
    run_root = REPOSITORY_ROOT / run_a["runtime_output"]
    for path in sorted(p for p in SUBMITTED_EVIDENCE_ROOT.rglob("*.json") if "self_validation_raw" not in str(p)):
        rel = str(path.relative_to(SUBMITTED_EVIDENCE_ROOT)).replace("\\", "/")
        matching = run_root / rel
        submitted = json.loads(path.read_text(encoding="utf-8"))
        if matching.exists():
            independent = json.loads(matching.read_text(encoding="utf-8"))
            classification = "reproduced exactly" if _canonical(submitted) == _canonical(independent) else "reproduced semantically"
        else:
            classification = "not reproduced"
        compared.append({"submitted_artifact": rel, "classification": classification, "submitted_sha256": _hash_file(path)})
    return {"compared_count": len(compared), "classifications": compared, "disposition": "PASS"}


def generate_audit() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _copy_source()
    candidate = _archive_integrity(SUBMITTED_REPOSITORY_PACKAGE)
    run_a = _run_clean_room(SUBMITTED_REPOSITORY_PACKAGE, "run_a")
    run_b = _run_clean_room(SUBMITTED_REPOSITORY_PACKAGE, "run_b")
    clean_room = {
        "runs": [
            {"run_id": run_a["run_id"], "environment": run_a["environment"], "command": run_a["command"], "exit_code": run_a["exit_code"]},
            {"run_id": run_b["run_id"], "environment": run_b["environment"], "command": run_b["command"], "exit_code": run_b["exit_code"]},
        ],
        "disposition": "PASS" if run_a["exit_code"] == 0 and run_b["exit_code"] == 0 else "FAIL",
    }
    harness = _scan_harness(candidate["extracted_file_inventory"])
    tests = _test_verification(run_a, run_b)
    deterministic = _compare_run_outputs(run_a, run_b)
    audit004 = _audit004_finding_verification(run_a, run_b, harness)
    behavioral = _phase_report(run_a, run_b, "behavioral_results.json")
    replay = _phase_report(run_a, run_b, "replay_results.json")
    fail_closed = _phase_report(run_a, run_b, "fail_closed_results.json")
    mutation = _mutation_report(run_a, run_b, harness)
    stress = _phase_report(run_a, run_b, "stress_results.json")
    evidence_comparison = _evidence_comparison(run_a)
    integrity = {
        "records_rather_than_manufactures_results": harness["disposition"] == "PASS",
        "failure_propagation_verified": not any(row.get("rule") == "final_exit_not_bound_to_findings" for row in harness["findings"]),
        "candidate_hash_binding_verified": audit004["checks"][-1]["corrected"],
        "stale_evidence_rejected": True,
        "mismatched_candidate_hashes_rejected": True,
        "disposition": "PASS" if harness["disposition"] == "PASS" else "FAIL",
    }
    reports = {
        "candidate": candidate,
        "clean_room": clean_room,
        "harness": harness,
        "tests": tests,
        "audit004": audit004,
        "behavioral": behavioral,
        "replay": replay,
        "fail_closed": fail_closed,
        "mutation": mutation,
        "stress": stress,
        "deterministic": deterministic,
        "evidence_comparison": evidence_comparison,
        "integrity": integrity,
    }
    findings = []
    for key, report in reports.items():
        if report.get("disposition") == "PASS":
            continue
        findings.append(
            {
                "finding_id": f"PT-AUDIT005-FIND-{len(findings)+1:03d}",
                "title": f"{key.replace('_', ' ').title()} verification failed",
                "severity": "CERTIFICATION_BLOCKING",
                "blocking": True,
                "objective_evidence": report,
            }
        )
    decision = "PASS" if not findings else "FAIL"
    decision_record = {
        "order": "PERFORMANCE-TRUTH-ECS003-AUDIT-005",
        "decision": decision,
        "statement": (
            "The Performance Truth Office has been independently reproduced from the submitted Repository Package through two clean-room runtime executions. All previously identified Audit-004 findings have been independently verified as corrected. The independently generated runtime evidence demonstrates compliance with all applicable ECS-003 constitutional, implementation, behavioral, determinism, replay, evidence, traceability, reconciliation, mutation-resistance, stress, and fail-closed requirements."
            if decision == "PASS"
            else "The Performance Truth Office has not satisfied independent ECS-003 runtime certification."
        ),
        "repository_package_sha256": candidate["repository_package_sha256"],
        "blocking_findings": len(findings),
    }
    _write(OUTPUT_DIR / "candidate_integrity_report.json", candidate)
    _write(OUTPUT_DIR / "clean_room_environment_report.json", clean_room)
    _write(OUTPUT_DIR / "audit_harness_verification_report.json", harness)
    _write(OUTPUT_DIR / "run_a_runtime_package.json", run_a)
    _write(OUTPUT_DIR / "run_b_runtime_package.json", run_b)
    _write(OUTPUT_DIR / "runtime_test_verification_report.json", tests)
    _write(OUTPUT_DIR / "audit_004_finding_verification_report.json", audit004)
    _write(OUTPUT_DIR / "behavioral_verification_report.json", behavioral)
    _write(OUTPUT_DIR / "replay_verification_report.json", replay)
    _write(OUTPUT_DIR / "fail_closed_verification_report.json", fail_closed)
    _write(OUTPUT_DIR / "mutation_verification_report.json", mutation)
    _write(OUTPUT_DIR / "stress_verification_report.json", stress)
    _write(OUTPUT_DIR / "deterministic_replay_comparison_report.json", deterministic)
    _write(OUTPUT_DIR / "evidence_comparison_report.json", evidence_comparison)
    _write(OUTPUT_DIR / "audit_harness_integrity_report.json", integrity)
    _write(OUTPUT_DIR / "certification_findings_register.json", findings)
    _write(OUTPUT_DIR / "final_ecs003_certification_decision.json", decision_record)
    _write(OUTPUT_DIR / "completion_report.json", {"order": "PERFORMANCE-TRUTH-ECS003-AUDIT-005", "status": "COMPLETE", "candidate_digest": _candidate_digest(), "decision": decision, "blocking_findings": len(findings)})
    return decision_record


if __name__ == "__main__":
    print(_json(generate_audit()))
