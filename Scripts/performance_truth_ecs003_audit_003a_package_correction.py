"""Materialize AUDIT-003A package-correction evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import zipfile
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_ECS003_AUDIT_003A"
ORDER_SOURCE = Path(r"C:\Users\Fletc\.codex\attachments\b8c6924d-3abb-45f4-936a-a2dca8fdb40a\pasted-text.txt")


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, default=str) + "\n"


def _write(name: str, value: Any) -> None:
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value), encoding="utf-8")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _candidate_digest() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=True, timeout=30)
    return result.stdout.strip()


def _copy_source() -> list[dict[str, Any]]:
    source_dir = OUTPUT_DIR / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    text = ORDER_SOURCE.read_text(encoding="utf-8", errors="replace")
    target = source_dir / "PERFORMANCE-TRUTH-ECS003-AUDIT-003A.txt"
    target.write_text(text, encoding="utf-8")
    return [{"order_id": "PERFORMANCE-TRUTH-ECS003-AUDIT-003A", "preserved_copy": str(target.relative_to(REPOSITORY_ROOT)).replace("\\", "/"), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}]


def _make_candidate_zip(path: Path) -> None:
    include = {
        "AUDITOR_README.md",
        "audit_reproduce.py",
        "Scripts/performance_truth_ecs003_audit_003.py",
        "Tests/test_performance_truth_ecs003_audit_003.py",
    }
    for source_root in (REPOSITORY_ROOT / "src").rglob("*.py"):
        include.add(str(source_root.relative_to(REPOSITORY_ROOT)).replace("\\", "/"))
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(include):
            source = REPOSITORY_ROOT / item
            if source.exists():
                archive.write(source, item)


def generate_evidence() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    digest = _candidate_digest()
    source = _copy_source()
    readme = (REPOSITORY_ROOT / "AUDITOR_README.md").read_text(encoding="utf-8")
    entrypoint = REPOSITORY_ROOT / "audit_reproduce.py"

    with tempfile.TemporaryDirectory(prefix="pt_audit003a_") as temp_dir:
        candidate_zip = Path(temp_dir) / "performance_truth_candidate.zip"
        output_dir = Path(temp_dir) / "reproduction_output"
        _make_candidate_zip(candidate_zip)
        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, str(entrypoint), "--candidate", str(candidate_zip), "--output", str(output_dir)],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            timeout=1200,
        )
        duration = round(time.perf_counter() - start, 4)
        self_validation_output = OUTPUT_DIR / "self_validation_output"
        if self_validation_output.exists():
            import shutil

            shutil.rmtree(self_validation_output)
        import shutil

        shutil.copytree(output_dir, self_validation_output)
        workspace_copy = self_validation_output / "_workspace"
        if workspace_copy.exists():
            shutil.rmtree(workspace_copy)
        output_files = sorted(str(path.relative_to(self_validation_output)).replace("\\", "/") for path in self_validation_output.rglob("*") if path.is_file())
        validation = {
            "command": [sys.executable, str(entrypoint), "--candidate", str(candidate_zip), "--output", str(output_dir)],
            "candidate_hash": _hash_file(candidate_zip),
            "exit_code": result.returncode,
            "duration_seconds": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "output_location": str(self_validation_output.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
            "generated_output_inventory": output_files,
        }

    active_path_scan = {
        "AUDITOR_README.md": {
            "contains_authorizations_office_reference": "Authorizations Office" in readme,
            "contains_auth_ioc_reference": "AUTH-IOC-001" in readme,
            "contains_authorization_certify_module": "argos.authorization_independent_certify" in readme,
        },
        "audit_reproduce.py": {
            "contains_authorizations_office_reference": "Authorizations Office" in entrypoint.read_text(encoding="utf-8"),
            "contains_auth_ioc_reference": "AUTH-IOC-001" in entrypoint.read_text(encoding="utf-8"),
            "contains_authorization_certify_module": "argos.authorization_independent_certify" in entrypoint.read_text(encoding="utf-8"),
        },
    }
    change_manifest = [
        {"path": "AUDITOR_README.md", "classification": "AUDITOR_INSTRUCTION", "business_logic_modified": False},
        {"path": "audit_reproduce.py", "classification": "REPRODUCTION_ENTRYPOINT", "business_logic_modified": False},
        {"path": "Scripts/performance_truth_ecs003_audit_003a_package_correction.py", "classification": "EVIDENCE_GENERATOR", "business_logic_modified": False},
        {"path": "Tests/test_performance_truth_ecs003_audit_003a_package_correction.py", "classification": "PACKAGE_CORRECTION_TEST", "business_logic_modified": False},
    ]

    _write("source_order_registry.json", source)
    _write("execution_command_reference.json", {"canonical_command": "python audit_reproduce.py --candidate <repository-package.zip> --output <empty-output-directory>"})
    _write("output_schema_reference.json", {"required_outputs": [
        "candidate_hash.json", "environment.json", "repository_inventory.json", "performance_truth_discovery.json",
        "command_manifest.json", "test_inventory.json", "test_results.json", "behavioral_results.json",
        "replay_results.json", "fail_closed_results.json", "mutation_results.json", "stress_results.json",
        "findings.json", "execution_summary.json", "generated_artifact_inventory.json", "output_hash_manifest.json",
    ]})
    _write("exit_code_reference.json", {"0": "all required validations passed", "2": "input failure", "3": "discovery failure", "4": "validation failure"})
    _write("historical_artifact_classification_record.json", {"historical_reports_are_non_authoritative": True, "evidence_package_used_as_proof": False})
    _write("active_auditor_path_scan.json", active_path_scan)
    _write("implementation_change_manifest.json", change_manifest)
    _write("self_validation_execution_log.json", validation)
    _write("self_validation_output_manifest.json", {"file_count": len(validation["generated_output_inventory"]), "files": validation["generated_output_inventory"]})
    complete = validation["exit_code"] == 0 and all(not any(record.values()) for record in active_path_scan.values())
    _write("completion_report.json", {
        "order": "PERFORMANCE-TRUTH-ECS003-AUDIT-003A",
        "candidate_digest": digest,
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "completion_result": "COMPLETE" if complete else "INCOMPLETE",
        "business_logic_modified": False,
        "evidence_package_used_as_proof": False,
        "entrypoint_issues_certification": False,
        "self_validation_exit_code": validation["exit_code"],
    })
    return {"status": "COMPLETE" if complete else "INCOMPLETE", "self_validation_exit_code": validation["exit_code"]}


if __name__ == "__main__":
    print(_json(generate_evidence()))
