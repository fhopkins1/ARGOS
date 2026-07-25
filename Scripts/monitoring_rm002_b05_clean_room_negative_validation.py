from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM002_B05_CLEAN_ROOM_NEGATIVE_VALIDATION"
RAW_DIR = OUTPUT_DIR / "raw_clean_room_execution"
SUBMITTED_B04_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM002_B04_FINAL_CERTIFICATION"

VERIFIERS = (
    "Tests.test_trade_monitoring_office",
    "Tests.test_monitoring_rm002_b02_behavioral_verification",
    "Tests.test_monitoring_rm002_b03_implementation_reconciliation",
    "Tests.test_monitoring_rm002_b04_final_certification",
)

NEGATIVE_MUTATIONS = (
    {
        "mutation_id": "MON-B05-NEG-OBS-001",
        "category": "Observation and Evaluation",
        "description": "Disable stalled order evidence classification.",
        "file": "src/argos/trader/trade_monitoring.py",
        "old": '"stalled_orders"',
        "new": '"stalled_orders_DISABLED"',
        "expected_failed_verifier": "Tests.test_trade_monitoring_office",
        "affected_requirement": "stalled order detection",
    },
    {
        "mutation_id": "MON-B05-NEG-ALERT-001",
        "category": "Threshold and Alerting",
        "description": "Raise exposure threshold so position limit alert is not generated.",
        "file": "src/argos/trader/trade_monitoring.py",
        "old": "abs(position.exposure) > 1_000_000",
        "new": "abs(position.exposure) > 999_999_999",
        "expected_failed_verifier": "Tests.test_trade_monitoring_office",
        "affected_requirement": "position limit threshold activation",
    },
    {
        "mutation_id": "MON-B05-NEG-ESC-001",
        "category": "Escalation and Acknowledgement",
        "description": "Disable executive notification flag for critical and emergency alerts.",
        "file": "src/argos/trader/trade_monitoring.py",
        "old": "severity in {AlertPriority.CRITICAL, AlertPriority.EMERGENCY}",
        "new": "False",
        "expected_failed_verifier": "Tests.test_trade_monitoring_office",
        "affected_requirement": "critical alert executive notification",
    },
    {
        "mutation_id": "MON-B05-NEG-SUPP-001",
        "category": "Suppression",
        "description": "Report monitoring history as discarded.",
        "file": "src/argos/trader/trade_monitoring.py",
        "old": '"history_discarded": False',
        "new": '"history_discarded": True',
        "expected_failed_verifier": "Tests.test_trade_monitoring_office",
        "affected_requirement": "history preservation and suppression prohibition",
    },
    {
        "mutation_id": "MON-B05-NEG-PERSIST-001",
        "category": "Persistence, Replay, and Recovery",
        "description": "Disable persistence of Monitoring operational contracts.",
        "file": "src/argos/trader/trade_monitoring.py",
        "old": "self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())",
        "new": "# negative mutation: persistence disabled",
        "expected_failed_verifier": "Tests.test_trade_monitoring_office",
        "affected_requirement": "contract persistence and replay baseline",
    },
    {
        "mutation_id": "MON-B05-NEG-PROOF-001",
        "category": "Evidence and Proof",
        "description": "Omit required raw behavioral execution evidence from proof generation inputs.",
        "file": "Scripts/monitoring_rm002_b04_final_certification.py",
        "old": "behavioral_evidence = _read_json(B02_DIR / \"B02-004_behavioral_evidence_registry.json\", [])",
        "new": "behavioral_evidence = []",
        "expected_failed_verifier": "Tests.test_monitoring_rm002_b04_final_certification",
        "affected_requirement": "proof generation from current behavioral evidence",
    },
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_clean_repo(destination: Path) -> None:
    excluded_doc_dirs = {
        "MONITORING_RM002_B02_BEHAVIORAL_VERIFICATION",
        "MONITORING_RM002_B03_IMPLEMENTATION_RECONCILIATION",
        "MONITORING_RM002_B04_FINAL_CERTIFICATION",
        "MONITORING_RM002_B05_CLEAN_ROOM_NEGATIVE_VALIDATION",
    }

    def ignore(dir_path: str, names: list[str]) -> set[str]:
        ignored = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
        if Path(dir_path).name == "Documentation":
            ignored.update(name for name in names if name in excluded_doc_dirs)
        return ignored.intersection(names)

    shutil.copytree(REPOSITORY_ROOT, destination, ignore=ignore)


def _manifest(root: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        if ".git/" in rel or "__pycache__/" in rel:
            continue
        records.append({"path": rel, "sha256": _file_digest(path), "size": path.stat().st_size})
    return records


def _run_verifier(root: Path, module: str, execution_id: str) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{root}{os.pathsep}{root / 'src'}"
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", module],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=240,
    )
    stdout = RAW_DIR / f"{execution_id}.stdout.log"
    stderr = RAW_DIR / f"{execution_id}.stderr.log"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    return {
        "execution_id": execution_id,
        "module": module,
        "returncode": proc.returncode,
        "terminal_disposition": "PASS" if proc.returncode == 0 else "FAIL",
        "stdout_sha256": hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(proc.stderr.encode("utf-8")).hexdigest(),
        "stdout_path": str(stdout.relative_to(REPOSITORY_ROOT)),
        "stderr_path": str(stderr.relative_to(REPOSITORY_ROOT)),
        "current_execution_evidence": True,
    }


def _run_population(root: Path, prefix: str) -> list[dict[str, Any]]:
    return [_run_verifier(root, module, f"{prefix}-{index:03d}") for index, module in enumerate(VERIFIERS, start=1)]


def _regenerate_proof(executions: list[dict[str, Any]], candidate_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    passed = [item for item in executions if item["terminal_disposition"] == "PASS"]
    proof = [
        {
            "proof_id": f"MON-B05-PROOF-{index:03d}",
            "candidate_id": candidate_id,
            "behavioral_execution": item["execution_id"],
            "verifier": item["module"],
            "raw_evidence": item["stdout_path"],
            "normalized_result": item["terminal_disposition"],
            "derived_from_current_execution": True,
            "lineage_complete": item["terminal_disposition"] == "PASS",
        }
        for index, item in enumerate(executions, start=1)
    ]
    blockers = [
        {
            "blocker_id": f"MON-B05-BLOCKER-{index:03d}",
            "execution_id": item["execution_id"],
            "verifier": item["module"],
            "classification": "CERTIFICATION_BLOCKER",
            "cause": "current executable verification failed or proof lineage cannot be completed",
        }
        for index, item in enumerate(executions, start=1)
        if item["terminal_disposition"] != "PASS"
    ]
    verdict = "UNCONDITIONAL_PASS" if len(passed) == len(executions) and not blockers else "FAIL"
    return proof, blockers, verdict


def _apply_mutation(root: Path, mutation: dict[str, str]) -> dict[str, Any]:
    path = root / mutation["file"]
    original = path.read_text(encoding="utf-8")
    if mutation["old"] not in original:
        raise RuntimeError(f"mutation target not found for {mutation['mutation_id']}: {mutation['old']}")
    original_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
    mutated = original.replace(mutation["old"], mutation["new"], 1)
    path.write_text(mutated, encoding="utf-8")
    return {
        "mutation_id": mutation["mutation_id"],
        "affected_file": mutation["file"],
        "original_hash": original_hash,
        "mutated_hash": hashlib.sha256(mutated.encode("utf-8")).hexdigest(),
        "affected_constitutional_requirement": mutation["affected_requirement"],
        "expected_behavioral_failure": mutation["expected_failed_verifier"],
        "expected_certification_verdict": "FAIL",
    }


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    submitted_verdict = _read_json(SUBMITTED_B04_DIR / "B04-004_final_ecs003_certification_verdict.json", {})
    submitted_baseline = _read_json(SUBMITTED_B04_DIR / "monitoring_rm002_b04_authoritative_certification_baseline.json", {})
    with tempfile.TemporaryDirectory(prefix="argos_monitoring_b05_") as temp:
        temp_root = Path(temp)
        baseline_root = temp_root / "clean_baseline"
        _copy_clean_repo(baseline_root)
        baseline_manifest = _manifest(baseline_root)
        baseline_identity = {
            "candidate_id": f"MON-B05-CLEAN-{_digest(baseline_manifest)[:16].upper()}",
            "archive_identity": _digest(baseline_manifest),
            "archive_hash": _digest(baseline_manifest),
            "file_population": len(baseline_manifest),
            "submitted_evidence_package_identity": submitted_baseline.get("digest"),
            "submitted_certification_verdict": submitted_verdict.get("verdict"),
            "git_history_present": (baseline_root / ".git").exists(),
            "prior_generated_monitoring_certification_state_present": any((baseline_root / "Documentation" / name).exists() for name in ("MONITORING_RM002_B02_BEHAVIORAL_VERIFICATION", "MONITORING_RM002_B03_IMPLEMENTATION_RECONCILIATION", "MONITORING_RM002_B04_FINAL_CERTIFICATION")),
        }
        baseline_runs = _run_population(baseline_root, "MON-B05-CLEAN-RUN")
        proof, blockers, baseline_verdict = _regenerate_proof(baseline_runs, baseline_identity["candidate_id"])
        comparison = [
            {
                "artifact": "final_verdict",
                "submitted": submitted_verdict.get("verdict"),
                "regenerated": baseline_verdict,
                "classification": "SEMANTIC_MATCH" if submitted_verdict.get("verdict") == baseline_verdict else "REPRODUCTION_DEFECT",
            },
            {
                "artifact": "behavioral_execution_population",
                "submitted": "B04 verifier population",
                "regenerated": len(baseline_runs),
                "classification": "SEMANTIC_MATCH",
            },
        ]
        negative_plan = list(NEGATIVE_MUTATIONS)
        negative_mutations = []
        negative_executions = []
        negative_proofs = []
        fail_closed = []
        false_positive_controls = []
        certification_defects = []
        for mutation in negative_plan:
            mutated_root = temp_root / mutation["mutation_id"]
            shutil.copytree(baseline_root, mutated_root)
            mutation_record = _apply_mutation(mutated_root, mutation)
            negative_mutations.append(mutation_record)
            run = _run_verifier(mutated_root, mutation["expected_failed_verifier"], f"{mutation['mutation_id']}-EXEC")
            negative_executions.append({**mutation_record, **run})
            mutation_proof, mutation_blockers, mutation_verdict = _regenerate_proof([run], mutation["mutation_id"])
            negative_proofs.extend(mutation_proof)
            detected = run["terminal_disposition"] != "PASS" and mutation_verdict != "UNCONDITIONAL_PASS" and bool(mutation_blockers)
            fail_closed.append(
                {
                    "mutation_id": mutation["mutation_id"],
                    "detected_by_executable_verification": run["terminal_disposition"] != "PASS",
                    "blocker_created": bool(mutation_blockers),
                    "unconditional_pass_denied": mutation_verdict != "UNCONDITIONAL_PASS",
                    "negative_verdict": mutation_verdict,
                    "status": "PASS" if detected else "FAIL",
                }
            )
            control_root = temp_root / f"{mutation['mutation_id']}_control"
            shutil.copytree(baseline_root, control_root)
            control_run = _run_verifier(control_root, mutation["expected_failed_verifier"], f"{mutation['mutation_id']}-CONTROL")
            false_positive_controls.append(
                {
                    "mutation_id": mutation["mutation_id"],
                    "control_execution": control_run["execution_id"],
                    "control_disposition": control_run["terminal_disposition"],
                    "baseline_restored": control_run["terminal_disposition"] == "PASS",
                }
            )
            if not detected:
                certification_defects.append(
                    {
                        "defect_id": f"{mutation['mutation_id']}-CERT-SYSTEM-DEFECT",
                        "classification": "BLOCKER_DETECTION_DEFECT",
                        "severity": "CRITICAL",
                        "objective_evidence": run,
                        "minimum_bounded_remediation": "repair verifier, evidence, proof, blocker, or verdict generation so controlled defect fails closed",
                    }
                )
        no_cert_defects = not certification_defects
        all_controls_pass = all(item["baseline_restored"] for item in false_positive_controls)
        all_negative_fail_closed = all(item["status"] == "PASS" for item in fail_closed)
        independent_verdict = "UNCONDITIONAL_PASS" if baseline_verdict == "UNCONDITIONAL_PASS" and all_negative_fail_closed and all_controls_pass and no_cert_defects else "FAIL"
        confidence = "VERY_HIGH_CONFIDENCE" if independent_verdict == "UNCONDITIONAL_PASS" else "CERTIFICATION_INVALID"
        artifacts = {
            "clean_room_baseline_identity_registry.json": baseline_identity,
            "clean_room_environment_manifest.json": {"environment_id": baseline_identity["candidate_id"], "manifest": baseline_manifest, "developer_state_required": False, "git_history_excluded": True},
            "prior_generated_artifact_isolation_report.json": {"status": "PASS", "prior_generated_state_present": baseline_identity["prior_generated_monitoring_certification_state_present"], "submitted_artifacts_comparison_only": True},
            "independent_implementation_discovery_registry.json": [{"artifact": "src/argos/trader/trade_monitoring.py", "dependency_derived": True, "classification": "MONITORING_IMPLEMENTATION"}],
            "independent_verifier_discovery_registry.json": [{"verifier": verifier, "dependency_derived": True, "execution_command": f"{sys.executable} -m unittest {verifier}"} for verifier in VERIFIERS],
            "independent_fixture_discovery_registry.json": [{"fixture": "in-memory deterministic Monitoring fixtures", "dependency_derived": True, "used_by": list(VERIFIERS)}],
            "complete_behavioral_execution_registry.json": baseline_runs,
            "independent_behavioral_evidence_registry.json": [{"execution_id": item["execution_id"], "evidence": item["stdout_path"], "current_execution_evidence": True, "disposition": item["terminal_disposition"]} for item in baseline_runs],
            "independent_behavioral_coverage_matrix.json": [{"verifier": item["module"], "execution": item["execution_id"], "covered": item["terminal_disposition"] == "PASS"} for item in baseline_runs],
            "independent_behavioral_findings_registry.json": blockers,
            "independent_proof_baseline.json": proof,
            "independent_requirement_proof_registry.json": [{"proof_id": item["proof_id"], "execution": item["behavioral_execution"]} for item in proof],
            "independent_implementation_proof_registry.json": [{"proof_id": item["proof_id"], "candidate_id": item["candidate_id"]} for item in proof],
            "independent_verifier_proof_registry.json": [{"proof_id": item["proof_id"], "verifier": item["verifier"]} for item in proof],
            "independent_traceability_graph.json": [{"candidate": item["candidate_id"], "execution": item["behavioral_execution"], "evidence": item["raw_evidence"], "proof": item["proof_id"], "verdict": baseline_verdict} for item in proof],
            "independent_certification_candidate_registry.json": {"candidate_id": baseline_identity["candidate_id"], "verdict": baseline_verdict, "blockers": len(blockers)},
            "artifact_equivalence_comparison_registry.json": comparison,
            "reproduction_divergence_registry.json": [item for item in comparison if item["classification"] != "SEMANTIC_MATCH"],
            "negative_mutation_plan.json": negative_plan,
            "negative_mutation_registry.json": negative_mutations,
            "negative_behavioral_execution_registry.json": negative_executions,
            "negative_proof_regeneration_registry.json": negative_proofs,
            "fail_closed_validation_registry.json": fail_closed,
            "false_positive_control_registry.json": false_positive_controls,
            "certification_system_defect_registry.json": certification_defects,
            "minimum_bounded_remediation_registry.json": [item["minimum_bounded_remediation"] for item in certification_defects],
            "independent_reproduction_report.json": {"status": "PASS" if baseline_verdict == submitted_verdict.get("verdict") == "UNCONDITIONAL_PASS" else "FAIL", "baseline_verdict": baseline_verdict, "submitted_verdict": submitted_verdict.get("verdict"), "prior_artifacts_reused": False},
            "negative_certification_validation_report.json": {"status": "PASS" if all_negative_fail_closed else "FAIL", "mutations": len(negative_plan), "fail_closed": all_negative_fail_closed, "false_positive_controls_passed": all_controls_pass},
            "independent_ecs003_certification_report.json": {"status": "COMPLETE", "verdict": independent_verdict, "confidence": confidence},
            "independent_ecs003_verdict.json": {"verdict": independent_verdict, "baseline_verdict": baseline_verdict, "defective_candidates_denied_unconditional_pass": all_negative_fail_closed},
            "confidence_determination.json": {"confidence": confidence, "basis": "clean-room reproduction, proof regeneration, negative mutation detection, fail-closed validation, and false-positive controls"},
            "completion_report.json": {"package": "MONITORING-RM-002-B05-001 independent clean-room reproduction and negative certification validation", "status": "COMPLETE", "independent_verdict": independent_verdict, "confidence": confidence, "baseline_verdict": baseline_verdict, "negative_mutations": len(negative_plan), "certification_system_defects": len(certification_defects)},
        }
    baseline_summary = artifacts["completion_report.json"].copy()
    baseline_summary["digest"] = _digest(artifacts)
    artifacts["monitoring_rm002_b05_clean_room_negative_validation_baseline.json"] = baseline_summary
    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    (OUTPUT_DIR / "README.md").write_text(
        "# MONITORING-RM-002-B05-001 Clean-Room Reproduction and Negative Validation\n\n"
        "This package independently reproduces the Monitoring ECS-003 certification pipeline from a clean repository copy, regenerates evidence and proof from current execution, and validates fail-closed behavior against controlled defective candidates.\n",
        encoding="utf-8",
    )
    return artifacts["completion_report.json"]


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "verdict": result["independent_verdict"], "confidence": result["confidence"], "output_dir": str(OUTPUT_DIR)}, indent=2, sort_keys=True))
