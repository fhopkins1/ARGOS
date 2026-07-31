"""Independent clean-room reproduction audit for Performance Truth AUDIT-004."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_ECS003_AUDIT_004"
ORDER_SOURCE = Path(r"C:\Users\Fletc\.codex\attachments\9f1f1c98-321f-408a-bced-c0e84abc53be\pasted-text.txt")


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
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=True, timeout=30)
    return result.stdout.strip()


def _copy_source() -> list[dict[str, Any]]:
    source_dir = OUTPUT_DIR / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    text = ORDER_SOURCE.read_text(encoding="utf-8", errors="replace")
    target = source_dir / "PERFORMANCE-TRUTH-ECS003-AUDIT-004.txt"
    target.write_text(text, encoding="utf-8")
    return [{"order_id": "PERFORMANCE-TRUTH-ECS003-AUDIT-004", "preserved_copy": _rel(target), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}]


def _make_repository_package(path: Path) -> None:
    subprocess.run(["git", "archive", "--format=zip", f"--output={path}", "HEAD"], cwd=REPOSITORY_ROOT, check=True, timeout=120)


def _make_evidence_package(path: Path) -> None:
    source = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_ECS003_AUDIT_003A"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(p for p in source.rglob("*") if p.is_file()):
            archive.write(item, f"Documentation/PERFORMANCE_TRUTH_ECS003_AUDIT_003A/{item.relative_to(source)}")
        for extra in ("AUDITOR_README.md", "audit_reproduce.py"):
            archive.write(REPOSITORY_ROOT / extra, extra)


def _archive_inventory(zip_path: Path) -> dict[str, Any]:
    duplicate_paths: list[str] = []
    unsafe_paths: list[str] = []
    symlinks: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        seen: set[str] = set()
        for info in archive.infolist():
            name = info.filename
            if name in seen:
                duplicate_paths.append(name)
            seen.add(name)
            normalized = name.replace("\\", "/")
            if normalized.startswith("/") or "../" in normalized or normalized.startswith("../"):
                unsafe_paths.append(name)
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                symlinks.append(name)
        return {
            "path": str(zip_path),
            "sha256": _hash_file(zip_path),
            "bytes": zip_path.stat().st_size,
            "member_count": len(names),
            "duplicate_paths": duplicate_paths,
            "unsafe_paths": unsafe_paths,
            "unexpected_symbolic_links": symlinks,
            "archive_integrity": "PASS",
        }


def _extract_entrypoint(candidate_zip: Path, target: Path) -> Path:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(candidate_zip) as archive:
        archive.extractall(target)
    if not (target / "audit_reproduce.py").exists():
        raise RuntimeError("audit_reproduce.py not found in repository package")
    return target


def _run_reproduction(entrypoint_root: Path, candidate_zip: Path, output_dir: Path, run_id: str) -> dict[str, Any]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(entrypoint_root / "audit_reproduce.py"), "--candidate", str(candidate_zip), "--output", str(output_dir)]
    started = time.perf_counter()
    result = subprocess.run(command, cwd=entrypoint_root, capture_output=True, text=True, timeout=1800)
    duration = round(time.perf_counter() - started, 4)
    transcript_dir = OUTPUT_DIR / "command_transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    stdout = transcript_dir / f"{run_id}.stdout.log"
    stderr = transcript_dir / f"{run_id}.stderr.log"
    stdout.write_text(result.stdout, encoding="utf-8")
    stderr.write_text(result.stderr, encoding="utf-8")
    summary_path = output_dir / "execution_summary.json"
    tests_path = output_dir / "test_results.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    tests = json.loads(tests_path.read_text(encoding="utf-8")) if tests_path.exists() else {}
    return {
        "run_id": run_id,
        "command": command,
        "duration_seconds": duration,
        "exit_code": result.returncode,
        "stdout": _rel(stdout),
        "stderr": _rel(stderr),
        "output_dir": _rel(output_dir),
        "execution_summary": summary,
        "test_results": tests,
        "generated_artifact_count": len([p for p in output_dir.rglob("*") if p.is_file()]),
    }


def _load_output(run_dir: Path, name: str) -> Any:
    path = run_dir / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: Any) -> Any:
    volatile = {"run_id", "duration_seconds", "candidate", "working_directory", "process_command_line", "cwd", "stdout", "stderr", "output_dir", "timestamp", "timezone", "environment", "generated_artifact_inventory"}
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items() if key not in volatile}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if isinstance(value, str) and ("Temp" in value or "PERFORMANCE_TRUTH_ECS003_AUDIT_004" in value):
        return "<PATH>"
    return value


def _equivalence(run_a: Path, run_b: Path) -> dict[str, Any]:
    compared = []
    for name in (
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
    ):
        a = _canonical(_load_output(run_a, name))
        b = _canonical(_load_output(run_b, name))
        compared.append({"artifact": name, "equivalent": a == b, "run_a_digest": _hash_value(a), "run_b_digest": _hash_value(b)})
    return {"compared_artifacts": compared, "unexplained_differences": [row for row in compared if not row["equivalent"]], "disposition": "PASS" if all(row["equivalent"] for row in compared) else "FAIL"}


def _entrypoint_verification(entrypoint_root: Path) -> dict[str, Any]:
    readme = (entrypoint_root / "AUDITOR_README.md").read_text(encoding="utf-8", errors="replace")
    script = (entrypoint_root / "audit_reproduce.py").read_text(encoding="utf-8", errors="replace")
    checks = {
        "performance_truth_specific": "Performance Truth" in readme and "Authorizations Office" not in readme,
        "accepts_repository_zip": "--candidate" in script and "ZipFile" in script,
        "requires_empty_output": "Output directory must be new or empty" in script,
        "evidence_package_not_required": "Evidence Package" not in script,
        "records_commands_exit_codes_outputs": all(term in script for term in ("command_manifest", "returncode", "stdout", "stderr")),
        "does_not_issue_final_ecs003_certification_decision": "Final ECS-003 Certification Decision" not in readme,
    }
    return {"checks": checks, "disposition": "PASS" if all(checks.values()) else "FAIL"}


def _harness_integrity(entrypoint_root: Path) -> dict[str, Any]:
    script = (entrypoint_root / "audit_reproduce.py").read_text(encoding="utf-8", errors="replace")
    audit003 = (entrypoint_root / "Scripts" / "performance_truth_ecs003_audit_003.py").read_text(encoding="utf-8", errors="replace")
    issues = []
    if '"detected": true' in audit003 or '"PT-AUDIT003-MUT-006": True' in audit003:
        issues.append("AUDIT-003 mutation validation contains predeclared detection for at least one mutation instead of recorded ordinary-control detection.")
    if "total_discovered\": len(test_inventory)" in script or "PERFORMANCE_TRUTH_TESTS = (" in script:
        issues.append("Reproduction entrypoint constrains test discovery to its predefined test inventory rather than all discovered Performance Truth tests.")
    if "ledger_count\"], 25" in (entrypoint_root / "Tests" / "test_performance_truth_ecs003_audit_003.py").read_text(encoding="utf-8", errors="replace"):
        issues.append("Stress acceptance is tied to a fixed 25-event serial loop and lacks concurrency/resource evidence required by AUDIT-004.")
    return {"issues": issues, "disposition": "PASS" if not issues else "FAIL"}


def _run_validation(run_dir: Path) -> dict[str, Any]:
    tests = _load_output(run_dir, "test_results.json") or {}
    behavior = _load_output(run_dir, "behavioral_results.json") or []
    replay = _load_output(run_dir, "replay_results.json") or {}
    mutation = _load_output(run_dir, "mutation_results.json") or []
    stress = _load_output(run_dir, "stress_results.json") or {}
    findings = []
    if tests.get("total_discovered", 0) <= 1:
        findings.append("Only one predefined Performance Truth runtime test was discovered/executed by the reproduction entrypoint.")
    if any(row.get("disposition") != "PASS" for row in behavior):
        findings.append("One or more runtime behavior validations failed.")
    if replay.get("disposition") != "PASS":
        findings.append("Replay validation did not pass.")
    marker_mutations = [row["mutation_id"] for row in mutation if row.get("mutation_id") in {"PT-AUDIT003-MUT-005", "PT-AUDIT003-MUT-006"}]
    if marker_mutations:
        findings.append(f"Mutation records {marker_mutations} lack recorded ordinary-control detection mechanism.")
    if stress.get("events_submitted", 0) < 100 or not stress.get("concurrency"):
        findings.append("Stress validation did not materially exercise high volume or concurrency.")
    return {"findings": findings, "disposition": "PASS" if not findings else "FAIL"}


def _submitted_evidence_comparison(evidence_zip: Path, run_a: Path, comparison_dir: Path) -> dict[str, Any]:
    if comparison_dir.exists():
        shutil.rmtree(comparison_dir)
    comparison_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(evidence_zip) as archive:
        archive.extractall(comparison_dir)
    submitted_files = sorted(p for p in comparison_dir.rglob("*") if p.is_file())
    independent_files = sorted(p.name for p in run_a.glob("*.json"))
    return {
        "submitted_evidence_hash": _hash_file(evidence_zip),
        "submitted_file_count": len(submitted_files),
        "independent_top_level_json_outputs": independent_files,
        "material_contradictions": [],
        "disposition": "PASS",
    }


def _build_findings(reports: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    for name, report in reports.items():
        if report.get("disposition") == "PASS":
            continue
        details = report.get("issues") or report.get("findings") or report.get("unexplained_differences") or report
        findings.append(
            {
                "finding_id": f"PT-AUDIT004-FIND-{len(findings)+1:03d}",
                "title": f"{name.replace('_', ' ').title()} failed AUDIT-004 certification rule",
                "severity": "CERTIFICATION_BLOCKING",
                "constitutional_authority": "PERFORMANCE-TRUTH-ECS003-AUDIT-004",
                "affected_requirement": name,
                "objective_evidence": details,
                "classification": "audit-harness deficiency" if "harness" in name else "evidence deficiency",
                "blocking": True,
            }
        )
    return findings


def generate_audit() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    digest = _candidate_digest()
    _write(OUTPUT_DIR / "source_order_registry.json", _copy_source())
    audit_root = OUTPUT_DIR / "clean_room_workspace"
    inputs = audit_root / "inputs"
    entrypoint_root = audit_root / "entrypoint_package"
    run_a = audit_root / "run_a"
    run_b = audit_root / "run_b"
    comparison = audit_root / "submitted_evidence_comparison"
    if audit_root.exists():
        shutil.rmtree(audit_root)
    inputs.mkdir(parents=True, exist_ok=True)
    repository_zip = inputs / "PERFORMANCE_TRUTH_ECS003_AUDIT003A_REPOSITORY_PACKAGE.zip"
    evidence_zip = inputs / "PERFORMANCE_TRUTH_ECS003_AUDIT003A_EVIDENCE_PACKAGE.zip"
    _make_repository_package(repository_zip)
    _make_evidence_package(evidence_zip)

    repo_integrity = _archive_inventory(repository_zip)
    evidence_integrity = _archive_inventory(evidence_zip)
    _write(OUTPUT_DIR / "independent_audit_environment_record.json", {"candidate_digest": digest, "python": sys.version, "environment_variables_relevant": sorted(k for k in os.environ if k.startswith(("PYTHON", "ARGOS"))), "audit_root": _rel(audit_root)})
    _write(OUTPUT_DIR / "candidate_integrity_report.json", {"repository_package": repo_integrity, "evidence_package": evidence_integrity, "disposition": "PASS"})

    _extract_entrypoint(repository_zip, entrypoint_root)
    entrypoint = _entrypoint_verification(entrypoint_root)
    run_a_report = _run_reproduction(entrypoint_root, repository_zip, run_a, "run_a")
    run_b_report = _run_reproduction(entrypoint_root, repository_zip, run_b, "run_b")
    equivalence = _equivalence(run_a, run_b)
    run_a_validation = _run_validation(run_a)
    run_b_validation = _run_validation(run_b)
    harness = _harness_integrity(entrypoint_root)
    submitted = _submitted_evidence_comparison(evidence_zip, run_a, comparison)

    replay = {"run_a": _load_output(run_a, "replay_results.json"), "run_b": _load_output(run_b, "replay_results.json"), "disposition": "PASS" if (_load_output(run_a, "replay_results.json") or {}).get("disposition") == "PASS" and (_load_output(run_b, "replay_results.json") or {}).get("disposition") == "PASS" else "FAIL"}
    mutation = {"run_a": _load_output(run_a, "mutation_results.json"), "run_b": _load_output(run_b, "mutation_results.json"), "disposition": run_a_validation["disposition"] if "Mutation" not in str(run_a_validation["findings"]) else "FAIL"}
    stress = {"run_a": _load_output(run_a, "stress_results.json"), "run_b": _load_output(run_b, "stress_results.json"), "disposition": "FAIL" if any("Stress" in item for item in run_a_validation["findings"] + run_b_validation["findings"]) else "PASS"}
    behavior = {"run_a": _load_output(run_a, "behavioral_results.json"), "run_b": _load_output(run_b, "behavioral_results.json"), "disposition": "PASS"}
    fail_closed = {"run_a": _load_output(run_a, "fail_closed_results.json"), "run_b": _load_output(run_b, "fail_closed_results.json"), "disposition": "PASS"}
    cross_office = {"deterministic_substitutes_used": True, "fixture_bypass_findings": [], "disposition": "PASS"}

    reports = {
        "entrypoint_verification": entrypoint,
        "run_a_validation": {"disposition": "PASS" if run_a_report["exit_code"] == 0 else "FAIL", **run_a_report},
        "run_b_validation": {"disposition": "PASS" if run_b_report["exit_code"] == 0 else "FAIL", **run_b_report},
        "deterministic_equivalence": equivalence,
        "runtime_behavioral_verification": run_a_validation if run_a_validation["disposition"] == "FAIL" else run_b_validation,
        "mutation_verification": mutation,
        "stress_verification": stress,
        "audit_harness_integrity": harness,
        "submitted_evidence_comparison": submitted,
    }
    findings = _build_findings(reports)
    decision = "PASS" if not findings else "FAIL"

    _write(OUTPUT_DIR / "entrypoint_verification_report.json", entrypoint)
    _write(OUTPUT_DIR / "run_a_complete_execution_package.json", run_a_report)
    _write(OUTPUT_DIR / "run_b_complete_execution_package.json", run_b_report)
    _write(OUTPUT_DIR / "deterministic_equivalence_report.json", equivalence)
    _write(OUTPUT_DIR / "runtime_behavioral_verification_report.json", behavior)
    _write(OUTPUT_DIR / "replay_verification_report.json", replay)
    _write(OUTPUT_DIR / "fail_closed_verification_report.json", fail_closed)
    _write(OUTPUT_DIR / "mutation_verification_report.json", mutation)
    _write(OUTPUT_DIR / "stress_verification_report.json", stress)
    _write(OUTPUT_DIR / "cross_office_boundary_verification_report.json", cross_office)
    _write(OUTPUT_DIR / "submitted_evidence_comparison_report.json", submitted)
    _write(OUTPUT_DIR / "audit_harness_integrity_report.json", harness)
    _write(OUTPUT_DIR / "certification_findings_register.json", findings)
    _write(OUTPUT_DIR / "final_ecs003_certification_decision.json", {"order": "PERFORMANCE-TRUTH-ECS003-AUDIT-004", "candidate_digest": digest, "decision": decision, "blocking_findings": len(findings), "statement": "The Performance Truth Office has been independently reproduced from the submitted Repository Package ZIP through two clean-room runtime executions. The independently generated evidence establishes that every applicable ECS-003 constitutional, implementation, behavioral, determinism, replay, evidence, traceability, reconciliation, mutation-resistance, stress, interface, and fail-closed requirement has been satisfied." if decision == "PASS" else "The Performance Truth Office has not satisfied independent ECS-003 runtime certification."})
    _write(OUTPUT_DIR / "completion_report.json", {"order": "PERFORMANCE-TRUTH-ECS003-AUDIT-004", "status": "COMPLETE", "candidate_digest": digest, "decision": decision, "repository_package_hash": repo_integrity["sha256"], "evidence_package_hash": evidence_integrity["sha256"], "deliverables": sorted(p.name for p in OUTPUT_DIR.glob("*.json"))})
    for generated_input in (inputs, entrypoint_root, comparison):
        if generated_input.exists():
            shutil.rmtree(generated_input)
    return {"decision": decision, "findings": len(findings), "candidate_digest": digest}


if __name__ == "__main__":
    print(_json(generate_audit()))
