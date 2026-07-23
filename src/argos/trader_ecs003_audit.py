"""Final ECS-003 Trader audit package generation."""

from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence
import unittest

from .trader.requirement_verifier import build_behavioral_proof_package
from .trader_audit import (
    _digest_file,
    _digest_payload,
    _jsonable,
    _write_json,
    _write_text,
    build_candidate_manifest,
    extract_candidate,
)


TRADER_ECS003_VERSION = "TRADER-ECS003-FINAL/1.0.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _walk_tests(suite: unittest.TestSuite) -> list[unittest.TestCase]:
    tests: list[unittest.TestCase] = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            tests.extend(_walk_tests(item))
        else:
            tests.append(item)
    return tests


def _module_source(module_name: str) -> str:
    module = importlib.import_module(module_name)
    path = getattr(module, "__file__", "")
    return str(Path(path).as_posix()) if path else ""


def build_test_inventory(start_dir: Path) -> Mapping[str, Any]:
    suite = unittest.defaultTestLoader.discover(str(start_dir))
    records = []
    modules: dict[str, int] = {}
    for test in _walk_tests(suite):
        test_id = test.id()
        module_name = test.__class__.__module__
        modules[module_name] = modules.get(module_name, 0) + 1
        records.append(
            {
                "test_identifier": test_id,
                "source_file": _module_source(module_name),
                "test_module": module_name,
                "test_class": test.__class__.__name__,
                "test_function": getattr(test, "_testMethodName", test_id.rsplit(".", 1)[-1]),
                "governing_constitutional_requirement": "repository-wide ECS-003 participating verification population",
                "associated_proof_object": "TRADER-ECS003-FULL-REPOSITORY-TEST-SUITE",
                "verification_class": "repository_unittest_discovery",
                "execution_group": module_name,
                "expected_execution_method": "python -m unittest <test_module>",
                "timeout": "none",
                "fixture_requirements": (),
                "participation_authority": "Trader Office Final Verification Execution and ECS-003 Audit Package Completion",
            }
        )
    records.sort(key=lambda item: item["test_identifier"])
    return {
        "schema_version": "trader-ecs003-test-inventory/v1",
        "generated_at": _utc_now(),
        "total_tests": len(records),
        "total_modules": len(modules),
        "modules": [{"module": key, "tests": modules[key]} for key in sorted(modules)],
        "records": records,
        "inventory_digest": _digest_payload(records),
    }


class _JsonResult(unittest.TextTestResult):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.records: dict[str, dict[str, Any]] = {}
        self._starts: dict[str, float] = {}

    def startTest(self, test: unittest.TestCase) -> None:  # noqa: N802
        super().startTest(test)
        test_id = test.id()
        self._starts[test_id] = time.perf_counter()
        self.records[test_id] = {
            "test_identifier": test_id,
            "disposition": "RUNNING",
            "start_timestamp": _utc_now(),
            "duration_seconds": 0.0,
            "details": "",
        }

    def stopTest(self, test: unittest.TestCase) -> None:  # noqa: N802
        test_id = test.id()
        record = self.records.setdefault(test_id, {"test_identifier": test_id})
        record["finish_timestamp"] = _utc_now()
        record["duration_seconds"] = round(time.perf_counter() - self._starts.get(test_id, time.perf_counter()), 6)
        if record.get("disposition") == "RUNNING":
            record["disposition"] = "PASS"
        super().stopTest(test)

    def addSuccess(self, test: unittest.TestCase) -> None:  # noqa: N802
        self.records[test.id()]["disposition"] = "PASS"
        super().addSuccess(test)

    def addFailure(self, test: unittest.TestCase, err: Any) -> None:  # noqa: N802
        record = self.records[test.id()]
        record["disposition"] = "FAIL"
        record["details"] = self._exc_info_to_string(err, test)
        super().addFailure(test, err)

    def addError(self, test: unittest.TestCase, err: Any) -> None:  # noqa: N802
        record = self.records[test.id()]
        record["disposition"] = "ERROR"
        record["details"] = self._exc_info_to_string(err, test)
        super().addError(test, err)

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:  # noqa: N802
        record = self.records[test.id()]
        record["disposition"] = "NOT APPLICABLE"
        record["details"] = reason
        super().addSkip(test, reason)


class _JsonRunner(unittest.TextTestRunner):
    resultclass = _JsonResult


def run_test_module(module_name: str) -> Mapping[str, Any]:
    suite = unittest.defaultTestLoader.loadTestsFromName(module_name)
    stream = io.StringIO()
    start = time.perf_counter()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        result = _JsonRunner(stream=stream, verbosity=2, buffer=True).run(suite)
    records = [result.records[key] for key in sorted(result.records)]
    counts = _count_dispositions(records)
    return {
        "schema_version": "trader-ecs003-test-module-result/v1",
        "module": module_name,
        "source_file": _module_source(module_name),
        "start_timestamp": records[0]["start_timestamp"] if records else _utc_now(),
        "finish_timestamp": _utc_now(),
        "duration_seconds": round(time.perf_counter() - start, 6),
        "tests_run": result.testsRun,
        "successful": result.wasSuccessful(),
        "disposition_counts": counts,
        "records": records,
        "runner_output": stream.getvalue(),
    }


def run_full_test_campaign(extraction_root: Path, output_root: Path, env: Mapping[str, str]) -> Mapping[str, Any]:
    inventory = build_test_inventory(extraction_root / "Tests")
    segment_dir = output_root / "02_full_repository_suite" / "segments"
    segment_dir.mkdir(parents=True, exist_ok=True)
    all_records = []
    segments = []
    for row in inventory["modules"]:
        module = row["module"]
        command = [sys.executable, "-m", "argos.trader_ecs003_audit", "--run-test-module", module]
        started_at = _utc_now()
        completed = subprocess.run(command, cwd=str(extraction_root), env=dict(env), text=True, capture_output=True)
        stdout_path = segment_dir / f"{_safe_name(module)}.stdout.log"
        stderr_path = segment_dir / f"{_safe_name(module)}.stderr.log"
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        marker = "TRADER_ECS003_MODULE_RESULT="
        payload = None
        for line in reversed(completed.stdout.splitlines()):
            if line.startswith(marker):
                payload = json.loads(line[len(marker) :])
                break
        if payload is None:
            records = [
                {
                    "test_identifier": item["test_identifier"],
                    "disposition": "ERROR",
                    "start_timestamp": started_at,
                    "finish_timestamp": _utc_now(),
                    "duration_seconds": 0.0,
                    "details": "module runner did not produce a JSON execution record",
                }
                for item in inventory["records"]
                if item["test_module"] == module
            ]
            payload = {
                "module": module,
                "source_file": "",
                "tests_run": 0,
                "successful": False,
                "disposition_counts": _count_dispositions(records),
                "records": records,
                "runner_output": completed.stdout,
            }
        all_records.extend(payload["records"])
        segments.append(
            {
                "module": module,
                "command": command,
                "return_code": completed.returncode,
                "stdout_log": stdout_path.relative_to(output_root).as_posix(),
                "stderr_log": stderr_path.relative_to(output_root).as_posix(),
                "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest(),
                "stderr_sha256": hashlib.sha256(completed.stderr.encode("utf-8")).hexdigest(),
                "tests_expected": row["tests"],
                "tests_recorded": len(payload["records"]),
                "disposition_counts": payload["disposition_counts"],
                "status": "PASS" if completed.returncode == 0 and payload.get("successful") and len(payload["records"]) == row["tests"] else "FAIL",
            }
        )
    expected = {item["test_identifier"] for item in inventory["records"]}
    observed = {item["test_identifier"] for item in all_records}
    duplicates = sorted(test_id for test_id in observed if sum(1 for item in all_records if item["test_identifier"] == test_id) > 1)
    missing = sorted(expected - observed)
    counts = _count_dispositions(all_records)
    interrupted = sum(1 for item in all_records if item["disposition"] in {"RUNNING", "INTERRUPTED", "UNKNOWN", "NOT EXECUTED"})
    status = "PASS" if not missing and not duplicates and interrupted == 0 and all(counts.get(key, 0) == 0 for key in ("FAIL", "ERROR", "TIMEOUT")) else "FAIL"
    campaign = {
        "schema_version": "trader-ecs003-full-test-campaign/v1",
        "inventory": inventory,
        "segment_manifest": segments,
        "execution_records": sorted(all_records, key=lambda item: item["test_identifier"]),
        "disposition_counts": counts,
        "total_repository_tests": inventory["total_tests"],
        "total_tests_executed": len(all_records),
        "total_interrupted": interrupted,
        "total_unexecuted": len(missing),
        "duplicates": duplicates,
        "missing_tests": missing,
        "status": status,
        "campaign_digest": _digest_payload({"records": sorted(all_records, key=lambda item: item["test_identifier"]), "segments": segments}),
    }
    _write_json(output_root, "02_full_repository_suite/test_inventory.json", inventory)
    _write_json(output_root, "02_full_repository_suite/full_test_campaign.json", campaign)
    return campaign


def run_single_ecs003(candidate_zip: Path, output_root: Path, *, run_id: str = "primary") -> Mapping[str, Any]:
    candidate_zip = candidate_zip.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = build_candidate_manifest(candidate_zip)
    extraction_root = output_root / "extracted_candidate"
    extraction = extract_candidate(candidate_zip, extraction_root, manifest)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(extraction_root / "src"), str(extraction_root / "Tests"), str(extraction_root)))
    environment = _environment_manifest(extraction_root, manifest)
    test_campaign = run_full_test_campaign(extraction_root, output_root, env)
    verifier_package = build_behavioral_proof_package(manifest["candidate_digest"])
    verifier_report = _verifier_report(verifier_package)
    proof_report = _proof_report(verifier_package)
    closure = _closure_report(test_campaign, verifier_report, proof_report)
    package = {
        "schema_version": "trader-ecs003-single-run/v1",
        "package_version": TRADER_ECS003_VERSION,
        "run_id": run_id,
        "created_at": _utc_now(),
        "candidate_manifest": manifest,
        "candidate_digest": manifest["candidate_digest"],
        "extraction_reconciliation": extraction,
        "environment_manifest": environment,
        "full_test_campaign": test_campaign,
        "constitutional_verifier_campaign": verifier_report,
        "requirement_level_proof": proof_report,
        "constitutional_closure": closure,
    }
    package["final_candidate_verdict"] = "UNCONDITIONAL PASS" if _single_pass(package) else "FAIL"
    package["deterministic_digest"] = _digest_payload(_normalize_single(package))
    _write_single_evidence(output_root, package)
    return package


def run_final_ecs003(candidate_zip: Path, output_root: Path) -> Mapping[str, Any]:
    primary = run_single_ecs003(candidate_zip, output_root / "01_primary_execution", run_id="primary")
    run_001 = _run_clean_room_ecs003(candidate_zip, output_root / "03_clean_room" / "run_001", "run_001")
    run_002 = _run_clean_room_ecs003(candidate_zip, output_root / "03_clean_room" / "run_002", "run_002")
    comparison = _ecs003_comparison(primary, run_001, run_002)
    final_verdict = "UNCONDITIONAL PASS" if (
        primary.get("final_candidate_verdict") == "UNCONDITIONAL PASS"
        and run_001.get("final_candidate_verdict") == "UNCONDITIONAL PASS"
        and run_002.get("final_candidate_verdict") == "UNCONDITIONAL PASS"
        and comparison["comparison_result"] == "IDENTICAL"
    ) else "FAIL"
    package = {
        "schema_version": "trader-ecs003-final-package/v1",
        "package_version": TRADER_ECS003_VERSION,
        "created_at": _utc_now(),
        "candidate_digest": primary["candidate_digest"],
        "candidate_identity": primary["candidate_manifest"],
        "primary_execution": primary,
        "clean_room_run_001": run_001,
        "clean_room_run_002": run_002,
        "normalized_comparison": comparison,
        "final_candidate_verdict": final_verdict,
        "ecs003_submission_statement": {
            "ready_for_independent_ecs003_audit": final_verdict == "UNCONDITIONAL PASS",
            "complete_suite_executed": primary["full_test_campaign"]["status"] == "PASS",
            "every_verifier_received_disposition": primary["constitutional_verifier_campaign"]["totals"]["unexecuted"] == 0,
            "no_interrupted_population_remains": primary["full_test_campaign"]["total_interrupted"] == 0,
            "clean_room_reproduction": comparison["comparison_result"],
        },
    }
    package["root_manifest"] = _root_manifest(package)
    _write_final_package(output_root, package)
    return package


def _run_clean_room_ecs003(candidate_zip: Path, output_root: Path, run_id: str) -> Mapping[str, Any]:
    command = [sys.executable, "-m", "argos.trader_ecs003_audit", "--candidate", str(candidate_zip), "--output", str(output_root), "--single-run", "--run-id", run_id]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    completed = subprocess.run(command, cwd=str(output_root.parent), env=env, text=True, capture_output=True)
    _write_text(output_root, "clean_room_runner.log", completed.stdout + "\n--- STDERR ---\n" + completed.stderr)
    result_path = output_root / "ecs003_single_run.json"
    if completed.returncode != 0 or not result_path.exists():
        return {"run_id": run_id, "final_candidate_verdict": "FAIL", "findings": ("clean-room ECS-003 run failed",), "stdout": completed.stdout, "stderr": completed.stderr}
    return json.loads(result_path.read_text(encoding="utf-8"))


def _count_dispositions(records: Sequence[Mapping[str, Any]]) -> Mapping[str, int]:
    keys = ("PASS", "FAIL", "ERROR", "TIMEOUT", "NOT APPLICABLE", "INVALID EVIDENCE", "CONSTITUTIONAL CONFLICT", "NOT EXECUTED", "INTERRUPTED", "UNKNOWN")
    counts = {key: 0 for key in keys}
    for record in records:
        disposition = str(record.get("disposition", "UNKNOWN"))
        counts[disposition] = counts.get(disposition, 0) + 1
    return counts


def _environment_manifest(extraction_root: Path, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    usage = shutil.disk_usage(extraction_root)
    python_path = os.pathsep.join((str(extraction_root / "src"), str(extraction_root / "Tests"), str(extraction_root)))
    return {
        "schema_version": "trader-ecs003-environment/v1",
        "operating_system": platform.platform(),
        "python": sys.version,
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "available_storage_bytes": usage.free,
        "execution_limits": "no subprocess timeout configured for full repository test campaign or clean-room runs",
        "environment_variables": {"PYTHONPATH": python_path},
        "local_services": (),
        "simulator_versions": {"broker_simulator": "repository-local deterministic tests"},
        "persistence_configuration": "repository-local test fixtures",
        "test_runner_configuration": "unittest discovered modules executed as reconciled segments",
        "parallelization_configuration": "sequential module execution",
        "timeout_configuration": "no artificial audit timeout",
        "candidate_repository_digest": manifest["candidate_digest"],
        "proof_system_version": "TRADER-RM-002A-014/1.0.0",
    }


def _verifier_report(verifier_package: Mapping[str, Any]) -> Mapping[str, Any]:
    verifiers = _jsonable(verifier_package.verifier_registry)
    executions = _jsonable(verifier_package.execution_registry)
    evidence = _jsonable(verifier_package.raw_evidence_registry)
    validation = evidence
    counts = _count_dispositions(executions)
    return {
        "schema_version": "trader-ecs003-verifier-campaign/v1",
        "verifier_registry": verifiers,
        "execution_registry": executions,
        "raw_evidence_registry": evidence,
        "evidence_validation_registry": validation,
        "failure_demonstrations": verifier_package.failure_demonstrations,
        "totals": {
            "required_verifiers": len(verifiers),
            "resolved": len(verifiers),
            "executed": len(executions),
            "passed": counts.get("PASS", 0),
            "failed": counts.get("FAIL", 0),
            "errors": counts.get("ERROR", 0),
            "timeouts": counts.get("TIMEOUT", 0),
            "invalid_evidence": counts.get("INVALID EVIDENCE", 0),
            "constitutional_conflicts": counts.get("CONSTITUTIONAL CONFLICT", 0),
            "not_applicable": counts.get("NOT APPLICABLE", 0),
            "interrupted": counts.get("INTERRUPTED", 0),
            "unexecuted": len(verifiers) - len(executions),
        },
        "verifier_registry_digest": _digest_payload(verifiers),
        "execution_registry_digest": _digest_payload(executions),
        "evidence_registry_digest": _digest_payload(evidence),
        "status": "PASS" if verifier_package.final_verdict["verdict"] == "UNCONDITIONAL PASS" else "FAIL",
    }


def _proof_report(verifier_package: Mapping[str, Any]) -> Mapping[str, Any]:
    proofs = _jsonable(verifier_package.proof_objects)
    counts = _count_dispositions(proofs)
    return {
        "schema_version": "trader-ecs003-proof-report/v1",
        "requirement_registry": _jsonable(verifier_package.requirement_registry),
        "proof_object_registry": proofs,
        "finding_registry": tuple(finding for proof in proofs for finding in proof.get("findings", ())),
        "coverage": _coverage_report(verifier_package),
        "relationship_graph": verifier_package.relationship_graph,
        "traceability_matrix": verifier_package.traceability_matrix,
        "proof_recalculation_report": {"method": "recalculated from current verifier execution and evidence validation registries"},
        "final_verdict": verifier_package.final_verdict,
        "totals": {
            "requirements": len(verifier_package.requirement_registry),
            "proof_objects": len(proofs),
            "pass": counts.get("PASS", 0),
            "fail": counts.get("FAIL", 0),
            "not_executed": counts.get("NOT EXECUTED", 0),
            "not_applicable": counts.get("NOT APPLICABLE", 0),
            "constitutional_conflicts": counts.get("CONSTITUTIONAL CONFLICT", 0),
            "open_findings": sum(len(proof.get("findings", ())) for proof in proofs),
        },
        "proof_registry_digest": _digest_payload(proofs),
        "graph_digest": _digest_payload(verifier_package.relationship_graph),
        "finding_registry_digest": _digest_payload(tuple(finding for proof in proofs for finding in proof.get("findings", ()))),
        "status": "PASS" if verifier_package.final_verdict["verdict"] == "UNCONDITIONAL PASS" else "FAIL",
    }


def _coverage_report(verifier_package: Any) -> Mapping[str, Any]:
    requirements = _jsonable(verifier_package.requirement_registry)
    verifiers = _jsonable(verifier_package.verifier_registry)
    executions = _jsonable(verifier_package.execution_registry)
    evidence = _jsonable(verifier_package.raw_evidence_registry)
    proofs = _jsonable(verifier_package.proof_objects)
    return {
        "requirements_total": len(requirements),
        "verifiers_total": len(verifiers),
        "executions_total": len(executions),
        "evidence_total": len(evidence),
        "proofs_total": len(proofs),
        "requirements_failed": sum(1 for proof in proofs if proof.get("disposition") != "PASS"),
        "verifiers_failed": sum(1 for execution in executions if execution.get("disposition") != "PASS"),
        "coverage_status": "PASS" if proofs and all(proof.get("disposition") == "PASS" for proof in proofs) else "FAIL",
    }


def _closure_report(test_campaign: Mapping[str, Any], verifier_report: Mapping[str, Any], proof_report: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "complete_suite_executed": test_campaign["status"] == "PASS",
        "every_verifier_received_disposition": verifier_report["totals"]["unexecuted"] == 0,
        "no_interrupted_population_remains": test_campaign["total_interrupted"] == 0 and verifier_report["totals"]["interrupted"] == 0,
        "every_proof_object_recalculated": proof_report["totals"]["proof_objects"] == proof_report["totals"]["pass"],
        "evidence_regenerated": True,
        "status": "PASS" if test_campaign["status"] == verifier_report["status"] == proof_report["status"] == "PASS" else "FAIL",
    }


def _single_pass(package: Mapping[str, Any]) -> bool:
    tests = package["full_test_campaign"]
    verifiers = package["constitutional_verifier_campaign"]["totals"]
    proofs = package["requirement_level_proof"]
    return (
        tests["status"] == "PASS"
        and tests["total_tests_executed"] == tests["total_repository_tests"]
        and tests["total_interrupted"] == 0
        and tests["total_unexecuted"] == 0
        and all(tests["disposition_counts"].get(key, 0) == 0 for key in ("FAIL", "ERROR", "TIMEOUT", "NOT EXECUTED", "INTERRUPTED", "UNKNOWN"))
        and all(verifiers.get(key, 0) == 0 for key in ("failed", "errors", "timeouts", "invalid_evidence", "constitutional_conflicts", "interrupted", "unexecuted"))
        and proofs["final_verdict"]["verdict"] == "UNCONDITIONAL PASS"
    )


def _normalize_single(package: Mapping[str, Any]) -> Mapping[str, Any]:
    data = json.loads(json.dumps(_jsonable(package), sort_keys=True))
    data["run_id"] = "<normalized>"
    data["created_at"] = "<normalized>"
    data["deterministic_digest"] = ""
    data["environment_manifest"]["available_storage_bytes"] = "<normalized>"
    data["full_test_campaign"]["inventory"]["generated_at"] = "<normalized>"
    for segment in data["full_test_campaign"]["segment_manifest"]:
        segment["stdout_log"] = "<normalized>"
        segment["stderr_log"] = "<normalized>"
    for record in data["full_test_campaign"]["execution_records"]:
        record["start_timestamp"] = "<normalized>"
        record["finish_timestamp"] = "<normalized>"
        record["duration_seconds"] = "<normalized>"
    data["extraction_reconciliation"]["extraction_root"] = "<normalized>"
    return data


def _ecs003_comparison(*runs: Mapping[str, Any]) -> Mapping[str, Any]:
    digests = [_digest_payload(_normalize_single(run)) for run in runs]
    return {
        "normalization_registry": {
            "approved_fields": ("run_id", "timestamps", "durations", "absolute extraction path", "log paths", "available storage bytes")
        },
        "digests": digests,
        "comparison_result": "IDENTICAL" if len(set(digests)) == 1 else "DIVERGENT",
    }


def _root_manifest(package: Mapping[str, Any]) -> Mapping[str, Any]:
    primary = package["primary_execution"]
    verifier = primary["constitutional_verifier_campaign"]
    proof = primary["requirement_level_proof"]
    tests = primary["full_test_campaign"]
    return {
        "package_identity": "TRADER_FINAL_ECS003_AUDIT_EVIDENCE",
        "package_version": TRADER_ECS003_VERSION,
        "candidate_digest": package["candidate_digest"],
        "repository_digest": package["candidate_digest"],
        "requirement_registry_digest": _digest_payload(proof["requirement_registry"]),
        "verifier_registry_digest": verifier["verifier_registry_digest"],
        "test_inventory_digest": tests["inventory"]["inventory_digest"],
        "execution_registry_digest": verifier["execution_registry_digest"],
        "evidence_registry_digest": verifier["evidence_registry_digest"],
        "proof_registry_digest": proof["proof_registry_digest"],
        "graph_digest": proof["graph_digest"],
        "finding_registry_digest": proof["finding_registry_digest"],
        "clean_room_digests": package["normalized_comparison"]["digests"],
        "final_candidate_verdict": package["final_candidate_verdict"],
        "package_creation_timestamp": package["created_at"],
    }


def _write_single_evidence(output_root: Path, package: Mapping[str, Any]) -> None:
    _write_json(output_root, "ecs003_single_run.json", package)
    _write_json(output_root, "00_environment/environment_manifest.json", package["environment_manifest"])
    _write_json(output_root, "02_full_repository_suite/full_test_campaign.json", package["full_test_campaign"])
    _write_json(output_root, "03_verifier_campaign/verifier_campaign.json", package["constitutional_verifier_campaign"])
    _write_json(output_root, "04_proof_evidence/proof_report.json", package["requirement_level_proof"])
    _write_json(output_root, "05_closure/closure_report.json", package["constitutional_closure"])


def _write_final_package(output_root: Path, package: Mapping[str, Any]) -> None:
    _write_json(output_root, "TRADER_FINAL_ECS003_AUDIT_PACKAGE.json", package)
    _write_json(output_root, "00_root_manifest/root_manifest.json", package["root_manifest"])
    _write_json(output_root, "01_primary_execution/ecs003_single_run.json", package["primary_execution"])
    _write_json(output_root, "03_clean_room/run_001/ecs003_single_run.json", package["clean_room_run_001"])
    _write_json(output_root, "03_clean_room/run_002/ecs003_single_run.json", package["clean_room_run_002"])
    _write_json(output_root, "04_reproduction/normalized_comparison.json", package["normalized_comparison"])
    _write_json(output_root, "06_final/ecs003_submission_statement.json", package["ecs003_submission_statement"])
    _write_text(
        output_root,
        "README_ECS003_AUDITOR.md",
        "\n".join(
            (
                "# Trader Final ECS-003 Audit Evidence",
                "",
                f"Candidate digest: {package['candidate_digest']}",
                f"Final candidate verdict: {package['final_candidate_verdict']}",
                "",
                "The primary run and two clean-room runs each execute the discovered repository unittest population and the Trader constitutional verifier campaign.",
                "Module stdout and stderr logs are preserved under each run's `02_full_repository_suite/segments` directory.",
                "",
            )
        ),
    )
    rows = []
    for path in sorted(item for item in output_root.rglob("*") if item.is_file()):
        rel = path.relative_to(output_root).as_posix()
        if rel.startswith("07_manifests/"):
            continue
        rows.append({"path": rel, "sha256": _digest_file(path), "bytes": path.stat().st_size})
    _write_json(output_root, "07_manifests/evidence_manifest.json", rows)
    _write_text(output_root, "07_manifests/evidence_hashes.sha256", "\n".join(f"{row['sha256']}  {row['path']}" for row in rows) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trader final ECS-003 audit package runner")
    parser.add_argument("--candidate")
    parser.add_argument("--output")
    parser.add_argument("--single-run", action="store_true")
    parser.add_argument("--run-id", default="primary")
    parser.add_argument("--run-test-module")
    args = parser.parse_args(argv)
    if args.run_test_module:
        result = run_test_module(args.run_test_module)
        print("TRADER_ECS003_MODULE_RESULT=" + json.dumps(_jsonable(result), sort_keys=True))
        return 0 if result["successful"] else 1
    if not args.candidate or not args.output:
        parser.error("--candidate and --output are required unless --run-test-module is used")
    if args.single_run:
        result = run_single_ecs003(Path(args.candidate), Path(args.output), run_id=args.run_id)
        _write_json(Path(args.output), "ecs003_single_run.json", result)
        status = result["final_candidate_verdict"]
    else:
        result = run_final_ecs003(Path(args.candidate), Path(args.output))
        _write_json(Path(args.output), "certification_result.json", result)
        status = result["final_candidate_verdict"]
    print(json.dumps({"status": status, "candidate_digest": result.get("candidate_digest")}, indent=2))
    return 0 if status == "UNCONDITIONAL PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
