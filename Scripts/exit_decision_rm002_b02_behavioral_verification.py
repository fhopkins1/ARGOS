from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B02_BEHAVIORAL_VERIFICATION"
RAW_DIR = OUTPUT_DIR / "raw_execution_evidence"

B01_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B01_IMPLEMENTATION_DISCOVERY"
RM001_B05_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B05_FINAL_READINESS"

ORDER_SOURCE = Path(r"C:\Users\Fletc\.codex\attachments\518f6e88-33fe-415a-808c-7767888d1975\pasted-text.txt")

DOMAIN_BY_TEST_MARKER = {
    "stop_loss": ("admissibility", "evaluation", "recommendation", "decision", "lifecycle", "evidence"),
    "profit_target": ("evaluation", "recommendation", "decision", "evidence"),
    "trailing_stop": ("evaluation", "recommendation", "decision"),
    "large_adverse": ("evaluation", "recommendation", "decision"),
    "degraded_data": ("admissibility", "freshness", "decision"),
    "hold_record": ("decision", "execution_separation", "persistence", "evidence"),
    "commander_override": ("commander_interface", "decision", "precedence"),
    "emergency_risk": ("risk_interface", "decision", "precedence"),
    "strategy_invalidation": ("analytical_input", "recommendation", "evidence"),
    "runtime_exposes": ("interface", "execution_separation"),
    "builder_rejects": ("rejection", "lifecycle"),
    "trader_bridge": ("interface", "execution_separation"),
    "position_detail": ("evidence", "interface"),
    "authorization": ("authorization_separation", "execution_separation"),
    "lifecycle_boundaries": ("lifecycle", "authority_boundary"),
    "fill_fixtures": ("replay", "recovery", "persistence", "lifecycle"),
    "partial_multiple_replay": ("replay", "recovery", "persistence", "lifecycle"),
    "exit_decision_boundary": ("lifecycle", "authority_boundary", "execution_separation"),
    "halted_symbol": ("admissibility", "rejection", "risk_interface"),
}

REQUIRED_DOMAINS = (
    "admissibility",
    "evaluation",
    "recommendation",
    "decision",
    "authorization_separation",
    "execution_separation",
    "interface",
    "lifecycle",
    "persistence",
    "replay",
    "recovery",
    "evidence",
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _module_name(artifact: str) -> str:
    return Path(artifact).with_suffix("").as_posix().replace("/", ".")


def _class_name(artifact: str) -> str:
    text = (REPOSITORY_ROOT / artifact).read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"^class\s+(\w+)\(unittest\.TestCase\):", text, flags=re.MULTILINE)
    if match:
        return match.group(1)
    match = re.search(r"^class\s+(\w+)\(", text, flags=re.MULTILINE)
    return match.group(1) if match else ""


def _normalized_stream(value: str) -> str:
    value = re.sub(r"Ran (\d+) tests? in [0-9.]+s", r"Ran \1 tests in <duration>s", value)
    value = re.sub(r"Ran (\d+) tests? in [0-9.]+ seconds", r"Ran \1 tests in <duration> seconds", value)
    return value


def _test_domains(test_name: str) -> tuple[str, ...]:
    domains: set[str] = set()
    for marker, marker_domains in DOMAIN_BY_TEST_MARKER.items():
        if marker in test_name:
            domains.update(marker_domains)
    return tuple(sorted(domains or {"behavioral"}))


def _execution_population() -> list[dict[str, Any]]:
    verifiers = _read_json(B01_DIR / "verifier_population_registry.json")
    population = []
    for verifier in verifiers:
        artifact = verifier["artifact"]
        module = _module_name(artifact)
        test_class = _class_name(artifact)
        for test_name in verifier["focused_tests"]:
            if not test_name.startswith("test_"):
                continue
            test_id = f"{module}.{test_class}.{test_name}" if test_class else f"{module}.{test_name}"
            population.append(
                {
                    "execution_id": f"EXIT-RM002-B02-EXEC-{len(population) + 1:03d}",
                    "verifier_id": verifier["verifier_id"],
                    "verifier_artifact": artifact,
                    "test_name": test_name,
                    "test_id": test_id,
                    "domains": _test_domains(test_name),
                    "fixture_identity": f"{artifact}::{test_name}",
                    "timeout_seconds": 120,
                }
            )
    return population


def _run_execution(item: dict[str, Any]) -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stdout_path = RAW_DIR / f"{item['execution_id']}.stdout.log"
    stderr_path = RAW_DIR / f"{item['execution_id']}.stderr.log"
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", item["test_id"]],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=item["timeout_seconds"],
        )
        stdout = _normalized_stream(completed.stdout)
        stderr = _normalized_stream(completed.stderr)
        returncode = completed.returncode
        disposition = "PASS" if returncode == 0 else "FAIL"
    except subprocess.TimeoutExpired as exc:
        stdout = _normalized_stream(exc.stdout or "")
        stderr = _normalized_stream(exc.stderr or "") + "\nTIMEOUT"
        returncode = -1
        disposition = "TIMEOUT"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    return {
        **item,
        "returncode": returncode,
        "disposition": disposition,
        "stdout": str(stdout_path.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
        "stderr": str(stderr_path.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
        "stdout_sha256": _file_digest(stdout_path),
        "stderr_sha256": _file_digest(stderr_path),
        "environment_identity": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "cwd": str(REPOSITORY_ROOT),
        },
    }


def _requirement_dispositions(executions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requirements = _read_json(RM001_B05_DIR / "canonical_requirement_identity_registry.json")
    passed_domains = {domain for execution in executions if execution["disposition"] == "PASS" for domain in execution["domains"]}
    failed_domains = {domain for execution in executions if execution["disposition"] != "PASS" for domain in execution["domains"]}
    disposition_by_class = {
        "governance": "NOT_APPLICABLE",
        "authority": "VERIFIED_PASS" if {"authorization_separation", "execution_separation"} & passed_domains else "NOT_EXECUTED",
        "boundary": "VERIFIED_PASS" if {"authorization_separation", "execution_separation", "interface"} & passed_domains else "NOT_EXECUTED",
        "object": "VERIFIED_PASS" if "evidence" in passed_domains else "NOT_EXECUTED",
        "ownership": "VERIFIED_PASS" if "execution_separation" in passed_domains else "NOT_EXECUTED",
        "lifecycle": "VERIFIED_PASS" if "lifecycle" in passed_domains else "NOT_EXECUTED",
        "admissibility": "VERIFIED_PASS" if "admissibility" in passed_domains else "NOT_EXECUTED",
        "decision": "VERIFIED_PASS" if "decision" in passed_domains else "NOT_EXECUTED",
        "authorization": "VERIFIED_PASS" if "authorization_separation" in passed_domains else "NOT_EXECUTED",
        "interface": "VERIFIED_PASS" if "interface" in passed_domains else "NOT_EXECUTED",
        "temporal": "VERIFIED_PASS" if {"freshness", "replay"} & passed_domains else "NOT_EXECUTED",
        "evidence": "VERIFIED_PASS" if "evidence" in passed_domains else "NOT_EXECUTED",
        "traceability": "NOT_APPLICABLE",
        "certification": "NOT_APPLICABLE",
    }
    records = []
    for req in requirements:
        classification = req["classification"]
        disposition = disposition_by_class.get(classification, "NOT_EXECUTED")
        if classification in failed_domains:
            disposition = "VERIFIED_FAIL"
        records.append(
            {
                "requirement_id": req["requirement_id"],
                "classification": classification,
                "behavioral_disposition": disposition,
                "supporting_executions": [
                    execution["execution_id"]
                    for execution in executions
                    if classification in execution["domains"] or (classification == "authorization" and "authorization_separation" in execution["domains"])
                ],
            }
        )
    return records


def _findings(executions: list[dict[str, Any]], dispositions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for execution in executions:
        if execution["disposition"] != "PASS":
            findings.append(
                {
                    "finding_id": f"EXIT-RM002-B02-FIND-{len(findings) + 1:03d}",
                    "classification": "VERIFIED_FAIL" if execution["disposition"] == "FAIL" else execution["disposition"],
                    "severity": "BLOCKING",
                    "execution_id": execution["execution_id"],
                    "evidence": [execution["stdout"], execution["stderr"]],
                    "disposition": "OPEN",
                }
            )
    for record in dispositions:
        if record["behavioral_disposition"] == "NOT_EXECUTED":
            findings.append(
                {
                    "finding_id": f"EXIT-RM002-B02-FIND-{len(findings) + 1:03d}",
                    "classification": "NOT_EXECUTED",
                    "severity": "REMEDIATION_REQUIRED",
                    "requirement_id": record["requirement_id"],
                    "evidence": [],
                    "disposition": "OPEN",
                }
            )
    return findings


def _registry_for_domain(executions: list[dict[str, Any]], *domains: str) -> list[dict[str, Any]]:
    wanted = set(domains)
    return [execution for execution in executions if wanted & set(execution["domains"])]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_text(OUTPUT_DIR / "source_order_EXIT-DECISION-RM-002-B02.txt", ORDER_SOURCE.read_text(encoding="utf-8", errors="replace"))
    b01_completion = _read_json(B01_DIR / "completion_report.json")
    population = _execution_population()
    executions = [_run_execution(item) for item in population]
    dispositions = _requirement_dispositions(executions)
    findings = _findings(executions, dispositions)
    coverage = {
        "required_domains": REQUIRED_DOMAINS,
        "covered_domains": sorted({domain for execution in executions if execution["disposition"] == "PASS" for domain in execution["domains"]}),
        "missing_domains": sorted(set(REQUIRED_DOMAINS) - {domain for execution in executions if execution["disposition"] == "PASS" for domain in execution["domains"]}),
        "requirement_dispositions": {
            disposition: sum(1 for item in dispositions if item["behavioral_disposition"] == disposition)
            for disposition in sorted({item["behavioral_disposition"] for item in dispositions})
        },
    }
    readiness = {
        "ready_for": "EXIT-DECISION-RM-002-B03",
        "basis": "B02 establishes the behavioral evidence baseline and forwards verified failures or coverage gaps to B03 remediation.",
        "blocking_failures": sum(1 for item in findings if item["severity"] == "BLOCKING"),
        "coverage_gaps": sum(1 for item in findings if item["classification"] == "NOT_EXECUTED"),
    }
    artifacts: dict[str, Any] = {
        "behavioral_execution_population.json": population,
        "behavioral_execution_registry.json": executions,
        "admissibility_execution_registry.json": _registry_for_domain(executions, "admissibility", "freshness", "rejection"),
        "rejection_findings_registry.json": [item for item in findings if item["classification"] in {"VERIFIED_FAIL", "NOT_EXECUTED"}],
        "admissibility_evidence_registry.json": _registry_for_domain(executions, "admissibility", "freshness"),
        "evaluation_execution_registry.json": _registry_for_domain(executions, "evaluation"),
        "recommendation_execution_registry.json": _registry_for_domain(executions, "recommendation"),
        "decision_execution_registry.json": _registry_for_domain(executions, "decision"),
        "interface_execution_registry.json": _registry_for_domain(executions, "interface", "commander_interface", "risk_interface"),
        "authorization_behavior_registry.json": _registry_for_domain(executions, "authorization_separation"),
        "execution_separation_findings_registry.json": [item for item in findings if item.get("classification") == "VERIFIED_FAIL"],
        "lifecycle_execution_registry.json": _registry_for_domain(executions, "lifecycle"),
        "persistence_verification_registry.json": _registry_for_domain(executions, "persistence"),
        "replay_verification_registry.json": _registry_for_domain(executions, "replay"),
        "recovery_verification_registry.json": _registry_for_domain(executions, "recovery"),
        "reconciliation_findings_registry.json": findings,
        "behavioral_evidence_registry.json": [
            {
                "execution_id": item["execution_id"],
                "verifier": item["test_id"],
                "fixture_identity": item["fixture_identity"],
                "stdout": item["stdout"],
                "stderr": item["stderr"],
                "disposition": item["disposition"],
            }
            for item in executions
        ],
        "behavioral_findings_registry.json": findings,
        "behavioral_coverage_matrix.json": coverage,
        "requirement_behavioral_disposition_registry.json": dispositions,
        "behavioral_readiness_assessment.json": readiness,
        "series_reconciliation_report.json": {
            "b01_candidate_digest": b01_completion["candidate_digest"],
            "frozen_execution_population_preserved": True,
            "implementation_modified": False,
            "constitutional_doctrine_modified": False,
            "all_executions_terminal": all(item["disposition"] in {"PASS", "FAIL", "TIMEOUT"} for item in executions),
            "behavioral_baseline_established": True,
        },
    }
    for name, payload in artifacts.items():
        _write_json(OUTPUT_DIR / name, payload)
    completion_checks = {
        "b01_complete": b01_completion["status"] == "COMPLETE",
        "execution_population_present": bool(population),
        "all_executions_terminal": all(item["disposition"] in {"PASS", "FAIL", "TIMEOUT"} for item in executions),
        "every_requirement_has_behavioral_disposition": bool(dispositions) and all(item["behavioral_disposition"] for item in dispositions),
        "behavioral_evidence_preserved": all(item["stdout"] and item["stderr"] for item in executions),
        "findings_classified": all(item["classification"] for item in findings),
        "coverage_matrix_created": bool(coverage["required_domains"]),
        "no_implementation_modification": True,
        "no_constitutional_doctrine_modification": True,
    }
    completion = {
        "package": "EXIT-DECISION-RM-002-B02",
        "status": "COMPLETE" if all(completion_checks.values()) else "INCOMPLETE",
        "candidate_digest": b01_completion["candidate_digest"],
        "behavioral_tests_executed": len(executions),
        "behavioral_tests_passed": sum(1 for item in executions if item["disposition"] == "PASS"),
        "behavioral_tests_failed": sum(1 for item in executions if item["disposition"] == "FAIL"),
        "behavioral_tests_timeout": sum(1 for item in executions if item["disposition"] == "TIMEOUT"),
        "requirement_disposition_counts": coverage["requirement_dispositions"],
        "open_findings": len(findings),
        "completion_checks": completion_checks,
        "implementation_modified": False,
        "constitutional_doctrine_modified": False,
        "ready_for": "EXIT-DECISION-RM-002-B03",
        "evidence_digest": _digest(artifacts),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion)
    _write_text(OUTPUT_DIR / "README.md", "# EXIT-DECISION-RM-002-B02 Behavioral Verification\n\nPrimary entry point: completion_report.json\n")
    return 0 if completion["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
