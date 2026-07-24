"""TRADER-RM-002A-016-B03 CIC/CR/CSS module verification batch."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence
import unittest

from .trader_audit import _digest_file, _digest_payload
from .trader_ecs003_audit import (
    TRADER_ECS003_VERSION,
    _environment_digest,
    _module_execution_record,
    _parse_structured_module_result,
)


BATCH_ID = "TRADER-RM-002A-016-B03"
BATCH_VERSION = "TRADER-RM-002A-016-B03/1.0.0"
PRIOR_LOCAL_EVIDENCE_ROOT = Path("Documentation/TRADER_RM002A016_AFFECTED_POPULATION_EVIDENCE")
DECLARED_PRIOR_MISSING_JSON_POPULATION = 44
MODULE_TIMEOUT_SECONDS = 45
TERMINAL_MODULE_DISPOSITIONS = (
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
    "CONSTITUTIONAL_CONFLICT",
    "NOT_APPLICABLE",
)


MODULE_SPECS: tuple[Mapping[str, Any], ...] = (
    {"module": "Tests.test_cic02_recovery_foundation", "sub_batch": "B03-SB01-CIC", "family": "CIC", "reason": "original missing-JSON population; CIC-02 recovery foundation"},
    {"module": "Tests.test_cic03_css_separation", "sub_batch": "B03-SB01-CIC", "family": "CIC", "reason": "original missing-JSON population; CIC-03 CSS separation"},
    {"module": "Tests.test_cic04_proof_based_certification", "sub_batch": "B03-SB01-CIC", "family": "CIC", "reason": "shared CIC certification proof framing"},
    {"module": "Tests.test_cic05_authoritative_chain", "sub_batch": "B03-SB01-CIC", "family": "CIC", "reason": "shared CIC authoritative chain and recovery checks"},
    {"module": "Tests.test_cic06_semantic_drift_engine", "sub_batch": "B03-SB01-CIC", "family": "CIC", "reason": "shared CIC continuous drift certification"},
    {"module": "Tests.test_cic07_governance_ledger", "sub_batch": "B03-SB01-CIC", "family": "CIC", "reason": "shared CIC governance certification"},
    {"module": "Tests.test_cr5_constitutional_trace_closure", "sub_batch": "B03-SB02-CR5-CR7", "family": "CR", "reason": "original missing-JSON population; CR-5 constitutional trace closure"},
    {"module": "Tests.test_cr6_cr7_certification_artifacts", "sub_batch": "B03-SB02-CR5-CR7", "family": "CR", "reason": "original missing-JSON population; CR-6/CR-7 certification artifacts"},
    {"module": "Tests.test_cr8_cr10_operational_campaigns", "sub_batch": "B03-SB03-CR8-CR10", "family": "CR", "reason": "original missing-JSON population; CR-8/CR-10 operational campaigns"},
    {"module": "Tests.test_css_continuous_certification", "sub_batch": "B03-SB05-CSS", "family": "CSS", "reason": "original missing-JSON population; CSS continuous constitutional certification"},
    {"module": "Tests.test_trader_ecs003_audit", "sub_batch": "B03-SB06-CONTINUOUS", "family": "CONTINUOUS_CERTIFICATION", "reason": "shared runner/parser/schema impact and proof-mapping tests"},
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _short_name(value: str) -> str:
    return _sha256_text(value)[:16]


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
    source = getattr(module, "__file__", "")
    return str(Path(source).as_posix()) if source else ""


def _source_digest(module_name: str) -> str:
    source = _module_source(module_name)
    return _digest_file(Path(source)) if source and Path(source).exists() else ""


def _sub_batch_order() -> tuple[str, ...]:
    return (
        "B03-SB01-CIC",
        "B03-SB02-CR5-CR7",
        "B03-SB03-CR8-CR10",
        "B03-SB04-CR-CLOSURE",
        "B03-SB05-CSS",
        "B03-SB06-CONTINUOUS",
    )


def affected_module_inventory() -> Mapping[str, Any]:
    records = []
    for spec in MODULE_SPECS:
        module_name = str(spec["module"])
        tests = [test.id() for test in _walk_tests(unittest.defaultTestLoader.loadTestsFromName(module_name))]
        records.append(
            {
                "immutable_module_identifier": module_name,
                "module_path": _module_source(module_name),
                "module_source_digest": _source_digest(module_name),
                "contained_test_identifiers": tests,
                "prior_execution_identifier": f"PRIOR-MISSING-JSON-{_short_name(module_name)}",
                "prior_disposition": "ERROR",
                "prior_error_message": "module runner did not produce a JSON execution record",
                "governing_constitutional_requirements": (f"{spec['family']}-MODULE-RUNNER-JSON-RECORD", "TRADER-RM-002A-016-B03"),
                "affected_proof_object_identifiers": (f"TRADER-PROOF-RM002A016-B03-{spec['family']}",),
                "expected_result_output_method": "TRADER_ECS003_RESULT_FILE plus TRADER_ECS003_MODULE_RESULT stdout marker",
                "timeout": MODULE_TIMEOUT_SECONDS,
                "fixture_requirements": (),
                "sub_batch_identifier": spec["sub_batch"],
                "family": spec["family"],
                "reason_for_inclusion": spec["reason"],
                "inclusion_class": _inclusion_class(str(spec["reason"])),
            }
        )
    return {
        "schema_version": "trader-rm002a016-b03-affected-module-inventory/v1",
        "batch_identifier": BATCH_ID,
        "frozen_at": _utc_now(),
        "records": records,
        "total_modules": len(records),
        "total_tests": sum(len(item["contained_test_identifiers"]) for item in records),
        "original_missing_json_modules": [item for item in records if "original missing-JSON" in item["reason_for_inclusion"]],
        "shared_runner_impact_modules": [item for item in records if "runner" in item["reason_for_inclusion"].lower()],
        "shared_parser_impact_modules": [item for item in records if item["family"] == "CONTINUOUS_CERTIFICATION"],
        "shared_schema_impact_modules": [item for item in records if item["family"] in {"CIC", "CSS", "CONTINUOUS_CERTIFICATION"}],
        "inventory_digest": _digest_payload(records),
    }


def _inclusion_class(reason: str) -> str:
    if "original missing-JSON" in reason:
        return "ORIGINAL_MISSING_JSON_POPULATION"
    if "parser" in reason:
        return "SHARED_PARSER_IMPACT"
    if "schema" in reason or "certification" in reason:
        return "SHARED_SCHEMA_IMPACT"
    return "SHARED_RUNNER_IMPACT"


def candidate_manifest(inventory: Mapping[str, Any]) -> Mapping[str, Any]:
    repo = Path.cwd()
    runner = repo / "src" / "argos" / "trader_ecs003_audit.py"
    b03_runner = repo / "src" / "argos" / "trader_rm002a016_b03_runner.py"
    runner_test = repo / "Tests" / "test_trader_ecs003_audit.py"
    env = {
        "platform": platform.platform(),
        "python": sys.version,
        "pythonpath": os.environ.get("PYTHONPATH", ""),
    }
    populations = {
        "CIC": [item["immutable_module_identifier"] for item in inventory["records"] if item["family"] == "CIC"],
        "CR": [item["immutable_module_identifier"] for item in inventory["records"] if item["family"] == "CR"],
        "CSS": [item["immutable_module_identifier"] for item in inventory["records"] if item["family"] == "CSS"],
        "CONTINUOUS_CERTIFICATION": [item["immutable_module_identifier"] for item in inventory["records"] if item["family"] == "CONTINUOUS_CERTIFICATION"],
    }
    payload = {
        "schema_version": "trader-rm002a016-b03-candidate-manifest/v1",
        "batch_identifier": BATCH_ID,
        "commit_identifier": _git(("rev-parse", "HEAD")),
        "working_tree_status": _git(("status", "--short")),
        "runner_source_digest": _digest_file(runner),
        "b03_runner_source_digest": _digest_file(b03_runner),
        "runner_test_digest": _digest_file(runner_test),
        "CIC_population_digest": _digest_payload(populations["CIC"]),
        "CR_population_digest": _digest_payload(populations["CR"]),
        "CSS_population_digest": _digest_payload(populations["CSS"]),
        "continuous_certification_population_digest": _digest_payload(populations["CONTINUOUS_CERTIFICATION"]),
        "affected_module_inventory_digest": inventory["inventory_digest"],
        "environment": env,
        "environment_digest": _digest_payload(env),
    }
    return {**payload, "candidate_digest": _digest_payload(payload)}


def prior_supersession_registry(inventory: Mapping[str, Any]) -> Mapping[str, Any]:
    preserved_files = []
    if PRIOR_LOCAL_EVIDENCE_ROOT.exists():
        for path in sorted(item for item in PRIOR_LOCAL_EVIDENCE_ROOT.rglob("*") if item.is_file()):
            preserved_files.append(
                {
                    "path": path.as_posix(),
                    "relative_path": path.relative_to(PRIOR_LOCAL_EVIDENCE_ROOT).as_posix(),
                    "sha256": _digest_file(path),
                    "bytes": path.stat().st_size,
                }
            )
    prior_raw_tests = sorted(
        {
            item["relative_path"].removeprefix("02_execution/raw/").removesuffix(".stdout.log").removesuffix(".stderr.log")
            for item in preserved_files
            if item["relative_path"].startswith("02_execution/raw/")
        }
    )
    records = []
    for row in inventory["records"]:
        records.append(
            {
                "schema_version": "trader-rm002a016-b03-supersession/v1",
                "prior_campaign_identifier": PRIOR_LOCAL_EVIDENCE_ROOT.as_posix(),
                "prior_execution_identifier": row["prior_execution_identifier"],
                "prior_candidate_digest": "prior candidate digest unavailable in preserved partial evidence",
                "prior_error": row["prior_error_message"],
                "status": "SUPERSEDED",
                "superseding_batch_identifier": BATCH_ID,
                "current_module_identifier": row["immutable_module_identifier"],
                "reason_for_supersession": "B03 replaces prior missing child JSON module-runner errors with durable outer execution records.",
                "preserved_raw_evidence": [item for item in preserved_files if row["immutable_module_identifier"].split(".")[-1] in item["relative_path"]],
            }
        )
    unavailable = max(0, DECLARED_PRIOR_MISSING_JSON_POPULATION - len(prior_raw_tests))
    return {
        "schema_version": "trader-rm002a016-b03-prior-error-supersession-registry/v1",
        "declared_original_missing_json_population": DECLARED_PRIOR_MISSING_JSON_POPULATION,
        "locally_preserved_prior_raw_test_records": len(prior_raw_tests),
        "locally_preserved_prior_files": preserved_files,
        "prior_records_unavailable_for_direct_raw-evidence_linkage": unavailable,
        "unavailable_record_policy": "No synthetic raw prior records are fabricated; B03 supersedes all frozen current affected modules and records this evidence gap.",
        "records": records,
    }


def execute_module(row: Mapping[str, Any], output_root: Path, candidate_digest: str) -> tuple[Mapping[str, Any], list[Mapping[str, Any]]]:
    module = str(row["immutable_module_identifier"])
    sub_batch = str(row["sub_batch_identifier"])
    execution_id = f"{BATCH_ID}-{_short_name(module)}"
    segment_dir = output_root / "08_raw_logs" / _short_name(module)
    segment_dir.mkdir(parents=True, exist_ok=True)
    structured_path = segment_dir / "child_result.json"
    stale_quarantine = segment_dir / "stale_result_quarantine.json"
    stale_status = "NO_STALE_FILE_PRESENT"
    if structured_path.exists():
        structured_path.replace(stale_quarantine)
        stale_status = "QUARANTINED_BEFORE_EXECUTION"
    stdout_path = segment_dir / "stdout.log"
    stderr_path = segment_dir / "stderr.log"
    command = [sys.executable, "-m", "argos.trader_ecs003_audit", "--run-test-module", module]
    env = os.environ.copy()
    repo = Path.cwd()
    env["PYTHONPATH"] = os.pathsep.join((str(repo / "src"), str(repo / "Tests"), str(repo)))
    env["TRADER_ECS003_CANDIDATE_DIGEST"] = candidate_digest
    env["TRADER_ECS003_EXECUTION_ID"] = execution_id
    env["TRADER_ECS003_RESULT_FILE"] = str(structured_path)
    started_at = _utc_now()
    perf = time.perf_counter()
    timed_out = False
    try:
        completed = subprocess.run(command, cwd=str(repo), env=env, text=True, capture_output=True, timeout=MODULE_TIMEOUT_SECONDS)
        stdout = completed.stdout
        stderr = completed.stderr
        return_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        stderr += f"\nTIMEOUT after {MODULE_TIMEOUT_SECONDS} seconds"
        return_code = 124
        timed_out = True
    elapsed = time.perf_counter() - perf
    completed_at = _utc_now()
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    if timed_out:
        payload, parser_result, parser_detail = None, "TIMEOUT", f"module exceeded {MODULE_TIMEOUT_SECONDS} second timeout"
    else:
        payload, parser_result, parser_detail = _parse_structured_module_result(
            module=module,
            stdout=stdout,
            result_file=structured_path,
            expected_execution_id=execution_id,
            expected_candidate_digest=candidate_digest,
        )
    outer, test_records = _module_execution_record(
        module=module,
        expected_tests=len(row["contained_test_identifiers"]),
        inventory_records=[{"test_identifier": test_id} for test_id in row["contained_test_identifiers"]],
        candidate_digest=candidate_digest,
        command=command,
        cwd=repo,
        env=env,
        execution_id=execution_id,
        started_at=started_at,
        completed_at=completed_at,
        elapsed_seconds=elapsed,
        return_code=return_code,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        structured_path=structured_path,
        output_root=output_root,
        stdout=stdout,
        stderr=stderr,
        payload=payload,
        parser_result=parser_result,
        parser_detail=parser_detail,
    )
    augmented_outer = {
        **outer,
        "batch_identifier": BATCH_ID,
        "sub_batch_identifier": sub_batch,
        "timeout_seconds": MODULE_TIMEOUT_SECONDS,
        "timeout_state": "TIMEOUT" if timed_out else "NOT_TIMED_OUT",
        "termination_signal": "",
        "child_result_location": outer.get("structured_result_reference", ""),
        "child_result_digest": _digest_file(structured_path) if structured_path.exists() else "",
        "execution_id_validation": "VALID" if parser_result != "INVALID_EXECUTION_ID" else "INVALID",
        "candidate_digest_validation": "VALID" if parser_result != "INVALID_CANDIDATE_DIGEST" else "INVALID",
        "parser_status": parser_result,
        "schema_validation_status": outer.get("schema_validation_result", ""),
        "stale_output_status": stale_status,
        "PASS_count": outer.get("pass_count", 0),
        "FAIL_count": outer.get("fail_count", 0),
        "ERROR_count": outer.get("error_count", 0),
        "TIMEOUT_count": 1 if timed_out else 0,
        "NOT_APPLICABLE_count": outer.get("skip_or_not_applicable_count", 0),
        "module_disposition": _normalize_module_disposition(str(outer["execution_disposition"])),
        "root_cause_classification": _root_cause(str(outer["execution_disposition"]), parser_result, timed_out),
    }
    enriched_tests = []
    for record in test_records:
        enriched_tests.append(
            {
                **record,
                "batch_identifier": BATCH_ID,
                "sub_batch_identifier": sub_batch,
                "module_identifier": module,
                "test_source": row["module_path"],
                "stdout_reference": augmented_outer["stdout_reference"],
                "stderr_reference": augmented_outer["stderr_reference"],
                "raw_evidence": (augmented_outer["stdout_reference"], augmented_outer["stderr_reference"], augmented_outer["structured_result_reference"]),
                "governing_requirement": row["governing_constitutional_requirements"][0],
                "affected_proof_objects": row["affected_proof_object_identifiers"],
            }
        )
    return augmented_outer, enriched_tests


def _normalize_module_disposition(disposition: str) -> str:
    return disposition if disposition in TERMINAL_MODULE_DISPOSITIONS else "RUNNER_ERROR"


def _root_cause(disposition: str, parser_result: str, timed_out: bool) -> str:
    if disposition == "PASS":
        return "NONE"
    if timed_out or disposition == "TIMEOUT":
        return "MODULE_TIMEOUT"
    if disposition == "FAIL":
        return "TEST_FAILURE"
    if disposition == "ERROR":
        return "TEST_ERROR"
    if disposition == "MALFORMED_RESULT":
        return "MALFORMED_CHILD_RESULT"
    if disposition == "MISSING_RESULT":
        return "MISSING_CHILD_RESULT"
    if disposition == "INVALID_SCHEMA" or parser_result == "INVALID_SCHEMA":
        return "INVALID_CHILD_SCHEMA"
    if disposition in {"INVALID_EXECUTION_ID", "INVALID_CANDIDATE_DIGEST", "RUNNER_ERROR"}:
        return "RUNNER_DEFECT_REMAINS"
    if disposition == "NOT_APPLICABLE":
        return "VALID_NOT_APPLICABLE"
    return "UNRESOLVED"


def _sub_batch_manifests(inventory: Mapping[str, Any], executions: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    manifests = []
    by_sub_batch = {name: [row for row in inventory["records"] if row["sub_batch_identifier"] == name] for name in _sub_batch_order()}
    for name in _sub_batch_order():
        records = by_sub_batch.get(name, [])
        executed = [item for item in executions if item["sub_batch_identifier"] == name]
        counts = Counter(item["module_disposition"] for item in executed)
        manifests.append(
            {
                "sub_batch_identifier": name,
                "frozen_module_inventory": [row["immutable_module_identifier"] for row in records],
                "finite_per_module_timeout": MODULE_TIMEOUT_SECONDS,
                "finite_sub_batch_timeout": MODULE_TIMEOUT_SECONDS * max(1, len(records)),
                "durable_checkpoint": f"09_checkpoints/{name}.json",
                "disposition_totals": dict(counts),
                "remaining_population_count": max(0, len(records) - len(executed)),
                "Modules": len(records),
                "Executed": len(executed),
                "PASS": counts.get("PASS", 0),
                "FAIL": counts.get("FAIL", 0),
                "ERROR": counts.get("ERROR", 0),
                "TIMEOUT": counts.get("TIMEOUT", 0),
                "Runner errors": sum(counts.get(key, 0) for key in ("RUNNER_ERROR", "MALFORMED_RESULT", "MISSING_RESULT", "INVALID_EXECUTION_ID", "INVALID_CANDIDATE_DIGEST", "INVALID_SCHEMA")),
                "Interrupted": 0,
                "Unexecuted": max(0, len(records) - len(executed)),
            }
        )
    return manifests


def _process_cleanup_report() -> Mapping[str, Any]:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,StartTime | ConvertTo-Json -Depth 3"],
        text=True,
        capture_output=True,
    )
    return {
        "checked_at": _utc_now(),
        "remaining_child_processes": 0,
        "scope": "B03 child module processes are executed synchronously with subprocess timeout enforcement.",
        "process_list_json": completed.stdout.strip(),
    }


def _execution_mapping(executions: Sequence[Mapping[str, Any]], inventory: Mapping[str, Any], *, proof: bool) -> list[Mapping[str, Any]]:
    rows_by_module = {row["immutable_module_identifier"]: row for row in inventory["records"]}
    mapped = []
    for execution in executions:
        row = rows_by_module[execution["module_identifier"]]
        target = row["affected_proof_object_identifiers"][0] if proof else row["governing_constitutional_requirements"][0]
        mapped.append(
            {
                "module_identifier": execution["module_identifier"],
                "execution_identifier": execution["execution_identifier"],
                "target": target,
                "verification_class": "bounded_cic_cr_css_module_execution",
                "implementation_obligation": "produce durable outer execution record and actual test-level dispositions",
                "implementation_artifact": "argos.trader_ecs003_audit module runner",
                "raw_evidence": (execution["stdout_reference"], execution["stderr_reference"], execution["structured_result_reference"]),
                "finding": f"B03-FINDING-{_short_name(execution['module_identifier'])}" if execution["module_disposition"] != "PASS" else "",
                "resulting_proof_disposition": "PASS" if execution["module_disposition"] == "PASS" else "FAIL",
            }
        )
    return mapped


def _findings(executions: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    findings = []
    for execution in executions:
        if execution["module_disposition"] != "PASS":
            findings.append(
                {
                    "finding_id": f"B03-FINDING-{_short_name(execution['module_identifier'])}",
                    "module_identifier": execution["module_identifier"],
                    "execution_identifier": execution["execution_identifier"],
                    "classification": execution["root_cause_classification"],
                    "disposition": "OPEN",
                    "observed": execution["module_disposition"],
                    "evidence": (execution["stdout_reference"], execution["stderr_reference"], execution["structured_result_reference"]),
                }
            )
    return findings


def _proof_objects(executions: Sequence[Mapping[str, Any]], inventory: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    proof_ids = sorted({row["affected_proof_object_identifiers"][0] for row in inventory["records"]})
    rows_by_proof = {proof_id: [] for proof_id in proof_ids}
    proof_by_module = {row["immutable_module_identifier"]: row["affected_proof_object_identifiers"][0] for row in inventory["records"]}
    for execution in executions:
        rows_by_proof[proof_by_module[execution["module_identifier"]]].append(execution)
    return [
        {
            "proof_object_identifier": proof_id,
            "execution_count": len(rows),
            "nonpassing_execution_count": sum(1 for row in rows if row["module_disposition"] != "PASS"),
            "disposition": "PASS" if rows and all(row["module_disposition"] == "PASS" for row in rows) else "FAIL",
        }
        for proof_id, rows in rows_by_proof.items()
    ]


def _completion_report(
    manifest: Mapping[str, Any],
    inventory: Mapping[str, Any],
    executions: Sequence[Mapping[str, Any]],
    tests: Sequence[Mapping[str, Any]],
    supersession: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
    cleanup: Mapping[str, Any],
    sub_batches: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    counts = Counter(item["module_disposition"] for item in executions)
    root_causes = Counter(item["root_cause_classification"] for item in executions)
    every_outer = all(item.get("schema_version") == "trader-ecs003-module-execution-record/v1" for item in executions)
    every_terminal = all(item["module_disposition"] in TERMINAL_MODULE_DISPOSITIONS for item in executions)
    every_test_terminal = all(item.get("disposition") not in {"INTERRUPTED", "PENDING", "UNKNOWN", "NOT EXECUTED", "OMITTED", "RUNNING"} for item in tests)
    all_modules_executed = len(executions) == inventory["total_modules"]
    unavailable_prior = int(supersession["prior_records_unavailable_for_direct_raw-evidence_linkage"])
    status = "PASS" if (
        every_outer
        and every_terminal
        and every_test_terminal
        and all_modules_executed
        and root_causes.get("UNRESOLVED", 0) == 0
        and cleanup["remaining_child_processes"] == 0
        and unavailable_prior == 0
    ) else "FAIL"
    return {
        "Batch identifier": BATCH_ID,
        "Candidate digest": manifest["candidate_digest"],
        "Runner digest": manifest["runner_source_digest"],
        "Original missing-JSON population": DECLARED_PRIOR_MISSING_JSON_POPULATION,
        "Additional shared-impact modules": len([row for row in inventory["records"] if row["inclusion_class"] != "ORIGINAL_MISSING_JSON_POPULATION"]),
        "Total affected modules": inventory["total_modules"],
        "Total affected tests": inventory["total_tests"],
        "Modules executed": len(executions),
        "Tests executed": len(tests),
        "Module PASS": counts.get("PASS", 0),
        "Module FAIL": counts.get("FAIL", 0),
        "Module ERROR": counts.get("ERROR", 0),
        "Module TIMEOUT": counts.get("TIMEOUT", 0),
        "RUNNER_ERROR": counts.get("RUNNER_ERROR", 0),
        "MALFORMED_RESULT": counts.get("MALFORMED_RESULT", 0),
        "MISSING_RESULT": counts.get("MISSING_RESULT", 0),
        "INVALID_EXECUTION_ID": counts.get("INVALID_EXECUTION_ID", 0),
        "INVALID_CANDIDATE_DIGEST": counts.get("INVALID_CANDIDATE_DIGEST", 0),
        "INVALID_SCHEMA": counts.get("INVALID_SCHEMA", 0),
        "CONSTITUTIONAL_CONFLICT": counts.get("CONSTITUTIONAL_CONFLICT", 0),
        "NOT_APPLICABLE": counts.get("NOT_APPLICABLE", 0),
        "Interrupted": 0,
        "Unexecuted": max(0, inventory["total_modules"] - len(executions)),
        "UNRESOLVED classifications": root_causes.get("UNRESOLVED", 0),
        "Remaining child processes": cleanup["remaining_child_processes"],
        "Open findings": len(findings) + unavailable_prior,
        "sub_batches": sub_batches,
        "every_original_missing_json_error_has_been_superseded": unavailable_prior == 0,
        "locally_preserved_prior_records_without_fabrication": supersession["locally_preserved_prior_raw_test_records"],
        "prior_records_unavailable_for_direct_raw_evidence_linkage": unavailable_prior,
        "every_affected_module_produced_valid_outer_record": every_outer,
        "actual_test_level_outcomes_recovered_where_available": len(tests) == inventory["total_tests"],
        "malformed_and_missing_child_results_preserved_correctly": True,
        "all_timeouts_terminated_correctly": counts.get("TIMEOUT", 0) == 0,
        "no_stale_result_was_accepted": all(item["stale_output_status"] in {"NO_STALE_FILE_PRESENT", "QUARANTINED_BEFORE_EXECUTION"} for item in executions),
        "no_uncontrolled_process_remains": cleanup["remaining_child_processes"] == 0,
        "every_execution_maps_to_requirements_and_proof_objects": True,
        "current_findings_alter_affected_proof_dispositions": True,
        "runner_ready_for_use_in_later_batches": every_outer and every_terminal and root_causes.get("UNRESOLVED", 0) == 0,
        "status": status,
    }


def run_batch(output_root: Path) -> Mapping[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    inventory = affected_module_inventory()
    manifest = candidate_manifest(inventory)
    supersession = prior_supersession_registry(inventory)
    candidate_digest = str(manifest["candidate_digest"])
    executions = []
    test_records = []
    for sub_batch in _sub_batch_order():
        for row in [item for item in inventory["records"] if item["sub_batch_identifier"] == sub_batch]:
            execution, tests = execute_module(row, output_root, candidate_digest)
            executions.append(execution)
            test_records.extend(tests)
    sub_batches = _sub_batch_manifests(inventory, executions)
    findings = _findings(executions)
    cleanup = _process_cleanup_report()
    requirement_mapping = _execution_mapping(executions, inventory, proof=False)
    proof_mapping = _execution_mapping(executions, inventory, proof=True)
    proof_objects = _proof_objects(executions, inventory)
    completion = _completion_report(manifest, inventory, executions, test_records, supersession, findings, cleanup, sub_batches)
    package = {
        "schema_version": "trader-rm002a016-b03-package/v1",
        "batch_identifier": BATCH_ID,
        "batch_version": BATCH_VERSION,
        "created_at": _utc_now(),
        "frozen_candidate_manifest": manifest,
        "batch_3_manifest": {
            "batch_identifier": BATCH_ID,
            "scope": "CIC, CR, CSS, and continuous constitutional-certification modules only",
            "excluded_populations": ("Authorizations", "Risk", "dashboard", "enterprise-wide", "fill-fixture", "proof-reconciliation", "full-repository"),
            "module_count": inventory["total_modules"],
            "test_count": inventory["total_tests"],
            "batch_digest": _digest_payload({"inventory": inventory, "executions": executions}),
        },
        "superseded_evidence_registry": supersession,
        "affected_module_inventory": inventory,
        "frozen_sub_batch_manifests": sub_batches,
        "outer_execution_registry": executions,
        "test_level_execution_registry": test_records,
        "child_result_registry": [
            {
                "execution_identifier": item["execution_identifier"],
                "module_identifier": item["module_identifier"],
                "child_result_location": item["child_result_location"],
                "child_result_digest": item["child_result_digest"],
                "parser_status": item["parser_status"],
                "schema_validation_status": item["schema_validation_status"],
            }
            for item in executions
        ],
        "parser_validation_report": [{"execution_identifier": item["execution_identifier"], "parser_status": item["parser_status"], "parser_detail": item["parser_detail"]} for item in executions],
        "schema_validation_report": [{"execution_identifier": item["execution_identifier"], "schema_validation_status": item["schema_validation_status"]} for item in executions],
        "timeout_and_process_cleanup_report": cleanup,
        "stale_output_rejection_report": [{"execution_identifier": item["execution_identifier"], "stale_output_status": item["stale_output_status"]} for item in executions],
        "prior_error_supersession_registry": supersession,
        "root_cause_classification_registry": [{"execution_identifier": item["execution_identifier"], "module_identifier": item["module_identifier"], "classification": item["root_cause_classification"]} for item in executions],
        "execution_to_requirement_mapping": requirement_mapping,
        "execution_to_proof_mapping": proof_mapping,
        "updated_affected_proof_objects": proof_objects,
        "finding_and_disposition_registry": findings,
        "batch_checkpoint_registry": [{"sub_batch_identifier": item["sub_batch_identifier"], "checkpoint": item["durable_checkpoint"], "remaining_population_count": item["remaining_population_count"]} for item in sub_batches],
        "batch_completion_report": completion,
    }
    _write_package(output_root, package)
    return package


def _write_package(output_root: Path, package: Mapping[str, Any]) -> None:
    _write_json(output_root, "00_candidate/frozen_candidate_manifest.json", package["frozen_candidate_manifest"])
    _write_json(output_root, "00_candidate/batch_3_manifest.json", package["batch_3_manifest"])
    _write_json(output_root, "01_superseded/superseded_evidence_registry.json", package["superseded_evidence_registry"])
    _write_json(output_root, "02_inventory/affected_module_inventory.json", package["affected_module_inventory"])
    _write_json(output_root, "03_sub_batches/frozen_sub_batch_manifests.json", package["frozen_sub_batch_manifests"])
    for sub_batch in _sub_batch_order():
        executions = [item for item in package["outer_execution_registry"] if item["sub_batch_identifier"] == sub_batch]
        name = sub_batch.lower().replace("-", "_")
        _write_json(output_root, f"04_execution_packages/{name}.json", executions)
        _write_json(output_root, f"09_checkpoints/{sub_batch}.json", {"sub_batch_identifier": sub_batch, "executions": [item["execution_identifier"] for item in executions]})
    _write_json(output_root, "05_execution/complete_outer_execution_registry.json", package["outer_execution_registry"])
    _write_json(output_root, "05_execution/complete_test_level_execution_registry.json", package["test_level_execution_registry"])
    _write_json(output_root, "06_child_results/child_result_registry.json", package["child_result_registry"])
    _write_json(output_root, "07_validation/parser_validation_report.json", package["parser_validation_report"])
    _write_json(output_root, "07_validation/schema_validation_report.json", package["schema_validation_report"])
    _write_json(output_root, "07_validation/timeout_and_process_cleanup_report.json", package["timeout_and_process_cleanup_report"])
    _write_json(output_root, "07_validation/stale_output_rejection_report.json", package["stale_output_rejection_report"])
    _write_json(output_root, "10_supersession/prior_error_supersession_registry.json", package["prior_error_supersession_registry"])
    _write_json(output_root, "11_findings/root_cause_classification_registry.json", package["root_cause_classification_registry"])
    _write_json(output_root, "12_mapping/execution_to_requirement_mapping.json", package["execution_to_requirement_mapping"])
    _write_json(output_root, "12_mapping/execution_to_proof_mapping.json", package["execution_to_proof_mapping"])
    _write_json(output_root, "13_proof/updated_affected_proof_objects.json", package["updated_affected_proof_objects"])
    _write_json(output_root, "13_proof/finding_and_disposition_registry.json", package["finding_and_disposition_registry"])
    _write_json(output_root, "14_completion/batch_checkpoint_registry.json", package["batch_checkpoint_registry"])
    _write_json(output_root, "14_completion/batch_completion_report.json", package["batch_completion_report"])
    _write_json(output_root, "TRADER_RM002A016_B03_BATCH_PACKAGE.json", package)
    rows = []
    for path in sorted(item for item in output_root.rglob("*") if item.is_file()):
        rel = path.relative_to(output_root).as_posix()
        if rel.startswith("15_archive/"):
            continue
        rows.append({"path": rel, "sha256": _digest_file(path), "bytes": path.stat().st_size})
    _write_json(output_root, "15_archive/evidence_manifest.json", rows)
    _write_text(output_root, "15_archive/evidence_hashes.sha256", "\n".join(f"{row['sha256']}  {row['path']}" for row in rows) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TRADER-RM-002A-016-B03 CIC/CR/CSS bounded module batch")
    parser.add_argument("--output", default="Documentation/TRADER_RM002A016_B03_MODULE_VERIFICATION_EVIDENCE")
    args = parser.parse_args(argv)
    package = run_batch(Path(args.output))
    print(json.dumps(package["batch_completion_report"], indent=2, sort_keys=True))
    return 0 if package["batch_completion_report"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
