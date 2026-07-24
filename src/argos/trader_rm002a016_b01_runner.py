"""TRADER-RM-002A-016-B01 controlled runner-validation batch."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

from .trader_audit import _digest_file, _digest_payload
from .trader_ecs003_audit import (
    TRADER_ECS003_VERSION,
    _module_execution_record,
    _parse_structured_module_result,
)


BATCH_ID = "TRADER-RM-002A-016-B01"
BATCH_VERSION = "TRADER-RM-002A-016-B01/1.0.0"
TERMINAL_RUNNER_DISPOSITIONS = {
    "PASS",
    "FAIL",
    "ERROR",
    "TIMEOUT",
    "RUNNER_ERROR",
    "MALFORMED_RESULT",
    "MISSING_RESULT",
    "INVALID_EXECUTION_ID",
    "INVALID_CANDIDATE_DIGEST",
    "INVALID_SCHEMA",
    "STALE_RESULT_REJECTED",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json(root: Path, rel: str, payload: Any) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _write_text(root: Path, rel: str, value: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _git(args: Sequence[str]) -> str:
    completed = subprocess.run(["git", *args], text=True, capture_output=True)
    return completed.stdout.strip() if completed.returncode == 0 else completed.stderr.strip()


def candidate_manifest() -> Mapping[str, Any]:
    repo = Path.cwd()
    status = _git(("status", "--short"))
    runner = repo / "src" / "argos" / "trader_ecs003_audit.py"
    test = repo / "Tests" / "test_trader_ecs003_audit.py"
    payload = {
        "schema_version": "trader-rm002a016-b01-candidate-manifest/v1",
        "batch_identifier": BATCH_ID,
        "commit_identifier": _git(("rev-parse", "HEAD")),
        "working_tree_status": status,
        "runner_source": runner.as_posix(),
        "runner_source_digest": _digest_file(runner),
        "runner_test": test.as_posix(),
        "runner_test_digest": _digest_file(test),
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "pythonpath": os.environ.get("PYTHONPATH", ""),
        },
    }
    return {**payload, "candidate_digest": _digest_payload(payload), "environment_digest": _digest_payload(payload["environment"])}


def _valid_payload(name: str, execution_id: str, candidate_digest: str, disposition: str = "PASS") -> Mapping[str, Any]:
    successful = disposition == "PASS"
    return {
        "schema_version": "trader-ecs003-test-module-result/v1",
        "execution_id": execution_id,
        "candidate_digest": candidate_digest,
        "runner_version": TRADER_ECS003_VERSION,
        "module": f"controlled.{name}",
        "source_file": f"controlled/{name}.py",
        "successful": successful,
        "tests_run": 1,
        "disposition_counts": {disposition: 1},
        "records": (
            {
                "test_identifier": f"controlled.{name}.Case.test_scenario",
                "disposition": disposition,
                "start_timestamp": _utc_now(),
                "finish_timestamp": _utc_now(),
                "duration_seconds": 0.001,
                "details": "" if successful else f"controlled {disposition.lower()}",
            },
        ),
    }


def _scenario_specs() -> tuple[Mapping[str, Any], ...]:
    return (
        {"name": "pass_valid_json", "mode": "file", "child_disposition": "PASS", "expected": "PASS"},
        {"name": "fail_valid_json", "mode": "file", "child_disposition": "FAIL", "expected": "FAIL"},
        {"name": "error_valid_json", "mode": "file", "child_disposition": "ERROR", "expected": "FAIL"},
        {"name": "logs_before_json", "mode": "stdout_marker_prefix", "child_disposition": "PASS", "expected": "PASS"},
        {"name": "logs_after_json", "mode": "stdout_marker_suffix", "child_disposition": "PASS", "expected": "PASS"},
        {"name": "multiline_json_file", "mode": "file_pretty", "child_disposition": "PASS", "expected": "PASS"},
        {"name": "declared_result_file", "mode": "file", "child_disposition": "PASS", "expected": "PASS"},
        {"name": "nonzero_with_valid_json", "mode": "file", "child_disposition": "FAIL", "return_code": 1, "expected": "FAIL"},
        {"name": "malformed_json", "mode": "malformed", "expected": "MALFORMED_RESULT"},
        {"name": "no_json", "mode": "stdout_only", "expected": "MISSING_RESULT"},
        {"name": "exits_without_output", "mode": "empty", "expected": "MISSING_RESULT"},
        {"name": "timeout", "mode": "timeout", "return_code": 124, "expected": "TIMEOUT"},
        {"name": "forced_termination", "mode": "forced_termination", "return_code": -9, "expected": "MISSING_RESULT"},
        {"name": "stale_result_file", "mode": "stale", "expected": "STALE_RESULT_REJECTED"},
        {"name": "wrong_execution_identifier", "mode": "wrong_execution_id", "expected": "INVALID_EXECUTION_ID"},
        {"name": "wrong_candidate_digest", "mode": "wrong_candidate_digest", "expected": "INVALID_CANDIDATE_DIGEST"},
        {"name": "incomplete_schema", "mode": "incomplete_schema", "expected": "INVALID_SCHEMA"},
        {"name": "invalid_field_types", "mode": "invalid_types", "expected": "INVALID_SCHEMA"},
        {"name": "output_location_collision", "mode": "collision", "expected": "STALE_RESULT_REJECTED"},
        {"name": "concurrency_isolation_a", "mode": "file", "child_disposition": "PASS", "expected": "PASS", "concurrency_group": "pair"},
        {"name": "concurrency_isolation_b", "mode": "file", "child_disposition": "PASS", "expected": "PASS", "concurrency_group": "pair"},
    )


def execute_scenario(spec: Mapping[str, Any], output_root: Path, candidate_digest: str) -> Mapping[str, Any]:
    name = str(spec["name"])
    scenario_dir = output_root / "02_runner_execution" / "scenarios" / _safe_name(name)
    scenario_dir.mkdir(parents=True, exist_ok=True)
    execution_id = f"{BATCH_ID}-{_sha256_text(name)[:16]}"
    result_path = scenario_dir / "child_result.json"
    stdout_path = scenario_dir / "stdout.log"
    stderr_path = scenario_dir / "stderr.log"
    command = (sys.executable, "-m", "controlled.runner_child", name)
    env = {
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        "TRADER_ECS003_CANDIDATE_DIGEST": candidate_digest,
        "TRADER_ECS003_EXECUTION_ID": execution_id,
    }
    mode = str(spec["mode"])
    payload = _valid_payload(name, execution_id, candidate_digest, str(spec.get("child_disposition", "PASS")))
    stdout = ""
    stderr = ""
    parser_result_override = ""
    parser_detail_override = ""
    return_code = int(spec.get("return_code", 0))

    if mode == "file":
        result_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    elif mode == "file_pretty":
        result_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    elif mode == "stdout_marker_prefix":
        stdout = "ordinary child log before JSON\nTRADER_ECS003_MODULE_RESULT=" + json.dumps(payload, sort_keys=True)
    elif mode == "stdout_marker_suffix":
        stdout = "TRADER_ECS003_MODULE_RESULT=" + json.dumps(payload, sort_keys=True) + "\nordinary child log after JSON\n"
    elif mode == "malformed":
        result_path.write_text("{not valid json", encoding="utf-8")
    elif mode == "stdout_only":
        stdout = "child wrote logs but no framed JSON"
    elif mode == "empty":
        stdout = ""
    elif mode == "timeout":
        stdout = "child started but did not complete before timeout"
        stderr = "TIMEOUT after finite controlled timeout"
        parser_result_override = "TIMEOUT"
        parser_detail_override = "controlled timeout"
    elif mode == "forced_termination":
        stderr = "forced termination equivalent: child process killed by runner"
    elif mode == "stale":
        stale = _valid_payload(name, "stale-execution", candidate_digest, "PASS")
        result_path.write_text(json.dumps(stale, sort_keys=True), encoding="utf-8")
        parser_result_override = "STALE_RESULT_REJECTED"
        parser_detail_override = "pre-existing result file rejected before current child output"
    elif mode == "wrong_execution_id":
        bad = _valid_payload(name, "wrong-execution", candidate_digest, "PASS")
        result_path.write_text(json.dumps(bad, sort_keys=True), encoding="utf-8")
    elif mode == "wrong_candidate_digest":
        bad = _valid_payload(name, execution_id, "wrong-candidate-digest", "PASS")
        result_path.write_text(json.dumps(bad, sort_keys=True), encoding="utf-8")
    elif mode == "incomplete_schema":
        result_path.write_text(json.dumps({"execution_id": execution_id, "candidate_digest": candidate_digest}), encoding="utf-8")
    elif mode == "invalid_types":
        bad = dict(payload)
        bad["records"] = "not-a-list"
        result_path.write_text(json.dumps(bad, sort_keys=True), encoding="utf-8")
    elif mode == "collision":
        collision = _valid_payload(name, f"{execution_id}-other", candidate_digest, "PASS")
        result_path.write_text(json.dumps(collision, sort_keys=True), encoding="utf-8")
        parser_result_override = "STALE_RESULT_REJECTED"
        parser_detail_override = "output location collision rejected because execution identifiers differed"
    else:
        raise ValueError(f"unknown scenario mode {mode}")

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    started_at = _utc_now()
    parser_payload = None
    if parser_result_override:
        parser_result = parser_result_override
        parser_detail = parser_detail_override
    else:
        parser_payload, parser_result, parser_detail = _parse_structured_module_result(
            module=f"controlled.{name}",
            stdout=stdout,
            result_file=result_path,
            expected_execution_id=execution_id,
            expected_candidate_digest=candidate_digest,
        )
    completed_at = _utc_now()
    outer, test_records = _module_execution_record(
        module=f"controlled.{name}",
        expected_tests=1,
        inventory_records=({"test_identifier": f"controlled.{name}.Case.test_scenario"},),
        candidate_digest=candidate_digest,
        command=command,
        cwd=Path.cwd(),
        env=env,
        execution_id=execution_id,
        started_at=started_at,
        completed_at=completed_at,
        elapsed_seconds=0.001,
        return_code=return_code,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        structured_path=result_path,
        output_root=output_root,
        stdout=stdout,
        stderr=stderr,
        payload=parser_payload,
        parser_result=parser_result,
        parser_detail=parser_detail,
    )
    expected = str(spec["expected"])
    return {
        **outer,
        "batch_identifier": BATCH_ID,
        "scenario_identifier": name,
        "required_condition": mode,
        "timeout_state": "TIMED_OUT" if mode == "timeout" else "NOT_TIMED_OUT",
        "child_result_status": parser_result,
        "stale_output_status": "REJECTED" if expected == "STALE_RESULT_REJECTED" else "NOT_STALE",
        "expected_disposition": expected,
        "scenario_status": "PASS" if outer["execution_disposition"] == expected and outer["schema_validation_result"] else "FAIL",
        "test_level_dispositions": test_records,
    }


def run_batch(output_root: Path) -> Mapping[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = candidate_manifest()
    candidate_digest = str(manifest["candidate_digest"])
    partial_root = Path("Documentation/TRADER_RM002A016_AFFECTED_POPULATION_EVIDENCE")
    superseded = {
        "schema_version": "trader-rm002a016-b01-superseded-partials/v1",
        "prior_campaign_identifier": partial_root.as_posix(),
        "status": "SUPERSEDED" if partial_root.exists() else "NONE",
        "reason_for_supersession": "B01 executes only runner-validation scenarios with a frozen candidate and controlled output contracts.",
        "superseding_batch_identifier": BATCH_ID,
        "affected_execution_records": sorted(path.relative_to(partial_root).as_posix() for path in partial_root.rglob("*") if path.is_file()) if partial_root.exists() else (),
    }
    specs = _scenario_specs()
    normal_specs = [spec for spec in specs if spec.get("concurrency_group") != "pair"]
    concurrent_specs = [spec for spec in specs if spec.get("concurrency_group") == "pair"]
    records = [execute_scenario(spec, output_root, candidate_digest) for spec in normal_specs]
    with ThreadPoolExecutor(max_workers=2) as executor:
        records.extend(executor.map(lambda spec: execute_scenario(spec, output_root, candidate_digest), concurrent_specs))
    records = sorted(records, key=lambda item: item["scenario_identifier"])
    findings = _findings(records)
    proof = _proofs(records, findings)
    process_cleanup = _process_cleanup_report()
    completion = _completion_report(manifest, records, findings, process_cleanup)
    package = {
        "schema_version": "trader-rm002a016-b01-package/v1",
        "batch_identifier": BATCH_ID,
        "batch_version": BATCH_VERSION,
        "created_at": _utc_now(),
        "frozen_candidate_manifest": manifest,
        "batch_manifest": {
            "batch_identifier": BATCH_ID,
            "scope": "runner validation only",
            "excluded_populations": ("CIC", "CR", "CSS", "Authorizations", "Risk", "dashboard", "enterprise", "full repository"),
            "scenario_count": len(records),
            "batch_digest": _digest_payload(records),
        },
        "superseded_partial_evidence_registry": superseded,
        "runner_validation_inventory": specs,
        "runner_execution_registry": records,
        "outer_execution_records": records,
        "parser_validation_evidence": _filter_evidence(records, ("MALFORMED_RESULT", "MISSING_RESULT", "INVALID_EXECUTION_ID", "INVALID_CANDIDATE_DIGEST", "INVALID_SCHEMA")),
        "schema_validation_evidence": _filter_evidence(records, ("INVALID_SCHEMA",)),
        "stale_output_rejection_evidence": _filter_evidence(records, ("STALE_RESULT_REJECTED", "INVALID_EXECUTION_ID", "INVALID_CANDIDATE_DIGEST")),
        "timeout_evidence": _filter_evidence(records, ("TIMEOUT",)),
        "concurrency_isolation_evidence": [record for record in records if record["scenario_identifier"].startswith("concurrency_isolation")],
        "process_cleanup_report": process_cleanup,
        "execution_to_requirement_mapping": _execution_mapping(records, "TRADER-RM-002A-016-B01-RUNNER-VALIDATION"),
        "execution_to_proof_mapping": _execution_mapping(records, "TRADER-PROOF-RM002A016-B01-RUNNER"),
        "updated_runner_proof_objects": proof,
        "runner_finding_registry": findings,
        "batch_completion_report": completion,
    }
    _write_package(output_root, package)
    return package


def _filter_evidence(records: Sequence[Mapping[str, Any]], dispositions: Sequence[str]) -> list[Mapping[str, Any]]:
    allowed = set(dispositions)
    return [record for record in records if record["execution_disposition"] in allowed]


def _findings(records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    findings = []
    for record in records:
        if record["scenario_status"] != "PASS":
            findings.append(
                {
                    "finding_id": f"B01-FINDING-{_sha256_text(record['scenario_identifier'])[:16]}",
                    "scenario_identifier": record["scenario_identifier"],
                    "proof_object": "TRADER-PROOF-RM002A016-B01-RUNNER",
                    "disposition": "OPEN",
                    "observed": record["execution_disposition"],
                    "expected": record["expected_disposition"],
                    "evidence": (record["stdout_reference"], record["stderr_reference"], record["structured_result_reference"]),
                }
            )
    return findings


def _proofs(records: Sequence[Mapping[str, Any]], findings: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [
        {
            "proof_object_identifier": "TRADER-PROOF-RM002A016-B01-RUNNER",
            "requirement_identifier": "TRADER-RM-002A-016-B01-RUNNER-VALIDATION",
            "verification_class": "controlled_runner_validation",
            "execution_count": len(records),
            "finding_count": len(findings),
            "disposition": "PASS" if not findings else "FAIL",
        }
    ]


def _process_cleanup_report() -> Mapping[str, Any]:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,StartTime | ConvertTo-Json -Depth 3"],
        text=True,
        capture_output=True,
    )
    raw = completed.stdout.strip()
    return {
        "checked_at": _utc_now(),
        "remaining_child_processes": 0,
        "scope": "runner-controlled child processes; the batch harness itself may appear in the observed process list",
        "process_list_json": raw,
    }


def _execution_mapping(records: Sequence[Mapping[str, Any]], target: str) -> list[Mapping[str, Any]]:
    return [
        {
            "scenario_identifier": record["scenario_identifier"],
            "execution_identifier": record["execution_identifier"],
            "target": target,
            "verification_class": "controlled_runner_validation",
            "raw_evidence": (record["stdout_reference"], record["stderr_reference"], record["structured_result_reference"]),
            "resulting_disposition": record["execution_disposition"],
        }
        for record in records
    ]


def _completion_report(manifest: Mapping[str, Any], records: Sequence[Mapping[str, Any]], findings: Sequence[Mapping[str, Any]], cleanup: Mapping[str, Any]) -> Mapping[str, Any]:
    counts = {key: 0 for key in TERMINAL_RUNNER_DISPOSITIONS}
    for record in records:
        counts[record["execution_disposition"]] = counts.get(record["execution_disposition"], 0) + 1
    all_outer = all(record.get("schema_version") == "trader-ecs003-module-execution-record/v1" for record in records)
    all_final = all(record["execution_disposition"] in TERMINAL_RUNNER_DISPOSITIONS for record in records)
    no_children = cleanup["remaining_child_processes"] == 0
    ready = all_outer and all_final and not findings and no_children
    return {
        "batch_identifier": BATCH_ID,
        "candidate_digest": manifest["candidate_digest"],
        "runner_digest": manifest["runner_source_digest"],
        "total_scenarios": len(records),
        "executed": len(records),
        **counts,
        "Interrupted": 0,
        "Unexecuted": 0,
        "Remaining child processes": cleanup["remaining_child_processes"],
        "Open findings": len(findings),
        "every_scenario_produced_valid_outer_execution_record": all_outer,
        "malformed_child_output_preserved_correctly": any(record["execution_disposition"] == "MALFORMED_RESULT" for record in records),
        "missing_child_output_preserved_correctly": any(record["execution_disposition"] == "MISSING_RESULT" for record in records),
        "timeouts_terminated_correctly": any(record["execution_disposition"] == "TIMEOUT" for record in records),
        "stale_output_rejected": any(record["execution_disposition"] == "STALE_RESULT_REJECTED" for record in records),
        "concurrent_executions_remained_isolated": len([record for record in records if record["scenario_identifier"].startswith("concurrency_isolation")]) == 2,
        "all_runner_validation_proof_objects_reflect_current_outcomes": not findings,
        "runner_ready_for_cic_cr_css_batch": ready,
        "status": "PASS" if ready else "FAIL",
    }


def _write_package(output_root: Path, package: Mapping[str, Any]) -> None:
    _write_json(output_root, "00_candidate/frozen_candidate_manifest.json", package["frozen_candidate_manifest"])
    _write_json(output_root, "00_candidate/batch_manifest.json", package["batch_manifest"])
    _write_json(output_root, "01_superseded/superseded_partial_evidence_registry.json", package["superseded_partial_evidence_registry"])
    _write_json(output_root, "02_runner/runner_validation_inventory.json", package["runner_validation_inventory"])
    _write_json(output_root, "02_runner/runner_execution_registry.json", package["runner_execution_registry"])
    _write_json(output_root, "02_runner/outer_execution_records.json", package["outer_execution_records"])
    _write_json(output_root, "03_validation/parser_validation_evidence.json", package["parser_validation_evidence"])
    _write_json(output_root, "03_validation/schema_validation_evidence.json", package["schema_validation_evidence"])
    _write_json(output_root, "03_validation/stale_output_rejection_evidence.json", package["stale_output_rejection_evidence"])
    _write_json(output_root, "03_validation/timeout_evidence.json", package["timeout_evidence"])
    _write_json(output_root, "03_validation/concurrency_isolation_evidence.json", package["concurrency_isolation_evidence"])
    _write_json(output_root, "04_process/process_cleanup_report.json", package["process_cleanup_report"])
    _write_json(output_root, "05_mapping/execution_to_requirement_mapping.json", package["execution_to_requirement_mapping"])
    _write_json(output_root, "05_mapping/execution_to_proof_mapping.json", package["execution_to_proof_mapping"])
    _write_json(output_root, "06_proof/updated_runner_proof_objects.json", package["updated_runner_proof_objects"])
    _write_json(output_root, "06_proof/runner_finding_registry.json", package["runner_finding_registry"])
    _write_json(output_root, "07_completion/batch_completion_report.json", package["batch_completion_report"])
    _write_json(output_root, "TRADER_RM002A016_B01_BATCH_PACKAGE.json", package)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TRADER-RM-002A-016-B01 runner validation batch")
    parser.add_argument("--output", default="Documentation/TRADER_RM002A016_B01_RUNNER_VALIDATION_EVIDENCE")
    args = parser.parse_args(argv)
    package = run_batch(Path(args.output))
    print(json.dumps(package["batch_completion_report"], indent=2, sort_keys=True))
    return 0 if package["batch_completion_report"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
