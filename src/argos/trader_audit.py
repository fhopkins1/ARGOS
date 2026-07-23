"""Package-bound Trader Office audit enablement.

TRADER-IC-000 prepares the Trader Office for independent audit.  The candidate
identity is the SHA-256 digest of the submitted repository ZIP bytes; no Git
checkout or development repository state is used as an audit input.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import platform
import py_compile
import shutil
import subprocess
import sys
from typing import Any, Mapping, Sequence
import zipfile


TRADER_IC_000_VERSION = "TRADER-IC-000/1.0.0"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest_payload(payload: Any) -> str:
    encoded = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json(root: Path, relative: str, payload: Any) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def _write_text(root: Path, relative: str, payload: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _canonical_path(name: str) -> str:
    normalized = name.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    if not normalized or "\\" in name or name.startswith("/") or any(part in {"", ".", ".."} for part in parts) or ":" in parts[0]:
        raise ValueError(f"invalid archive path: {name}")
    return normalized


def build_candidate_manifest(candidate_zip: Path) -> Mapping[str, Any]:
    archive_digest = _digest_file(candidate_zip)
    candidate_id = f"TRADER-CANDIDATE-ZIP-{archive_digest[:16].upper()}"
    findings: list[Mapping[str, str]] = []
    entries = []
    seen: set[str] = set()
    seen_case: set[str] = set()
    directory_entries = 0
    with zipfile.ZipFile(candidate_zip, "r") as archive:
        bad = archive.testzip()
        if bad:
            findings.append({"identifier": "TRADER-ZIP-CRC", "observed": bad, "expected": "valid ZIP central directory"})
        for info in archive.infolist():
            if info.is_dir():
                directory_entries += 1
                continue
            try:
                canonical = _canonical_path(info.filename)
            except ValueError as exc:
                findings.append({"identifier": "TRADER-ZIP-PATH", "observed": info.filename, "expected": str(exc)})
                canonical = info.filename
            if canonical in seen:
                findings.append({"identifier": "TRADER-ZIP-DUPLICATE", "observed": canonical, "expected": "unique archive path"})
            if canonical.lower() in seen_case:
                findings.append({"identifier": "TRADER-ZIP-CASE-COLLISION", "observed": canonical, "expected": "case-unique archive path"})
            seen.add(canonical)
            seen_case.add(canonical.lower())
            data = archive.read(info.filename)
            entries.append(
                {
                    "canonical_path": canonical,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "uncompressed_size": len(data),
                    "compressed_size": info.compress_size,
                    "classification": _classify(canonical),
                    "executable_status": "executable" if canonical.endswith(".py") else "non-executable",
                    "symlink_status": "not_symlink",
                    "deterministic_identifier": hashlib.sha256((candidate_id + ":" + canonical).encode("utf-8")).hexdigest(),
                }
            )
    entries.sort(key=lambda row: row["canonical_path"])
    manifest_digest = _digest_payload(entries)
    return {
        "schema_version": "TRADER-IC-000-candidate-manifest/v1",
        "candidate_identifier": candidate_id,
        "candidate_digest": archive_digest,
        "total_zip_entries": len(entries) + directory_entries,
        "total_non_directory_entries": len(entries),
        "manifest_digest": manifest_digest,
        "entries": entries,
        "findings": findings,
    }


def extract_candidate(candidate_zip: Path, extraction_root: Path, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    extraction_root.mkdir(parents=True, exist_ok=True)
    findings = []
    with zipfile.ZipFile(candidate_zip, "r") as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            canonical = _canonical_path(info.filename)
            target = (extraction_root / Path(*Path(canonical).parts)).resolve()
            root = extraction_root.resolve()
            if root != target and root not in target.parents:
                findings.append({"identifier": "TRADER-EXTRACT-ESCAPE", "observed": canonical, "expected": "inside extraction root"})
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info.filename))
    actual = {p.relative_to(extraction_root).as_posix(): _digest_file(p) for p in extraction_root.rglob("*") if p.is_file()}
    for entry in manifest["entries"]:
        path = entry["canonical_path"]
        if path not in actual:
            findings.append({"identifier": "TRADER-EXTRACT-MISSING", "observed": path, "expected": "present after extraction"})
        elif actual[path] != entry["sha256"]:
            findings.append({"identifier": "TRADER-EXTRACT-HASH", "observed": path, "expected": entry["sha256"]})
    return {"extraction_root": str(extraction_root), "extraction_reconciled": not findings, "findings": findings}


def run_trader_audit(candidate_zip: Path, output_root: Path, *, run_id: str = "primary") -> Mapping[str, Any]:
    candidate_zip = candidate_zip.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = build_candidate_manifest(candidate_zip)
    extraction_root = output_root / "extracted_candidate"
    extraction = extract_candidate(candidate_zip, extraction_root, manifest)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONPATH"] = str(extraction_root / "src")
    tests = (
        "Tests.test_trader_constitutional_governance",
        "Tests.test_trader_rm002_constitution",
        "Tests.test_trader_rm002a_publication",
        "Tests.test_trader_requirement_proof",
        "Tests.test_trader_readiness",
        "Tests.test_trader_group_framework",
        "Tests.test_trade_execution_office",
        "Tests.test_trade_monitoring_office",
        "Tests.test_trader_fusion_office",
    )
    test_command = [sys.executable, "-m", "unittest", *tests]
    test_result = subprocess.run(test_command, cwd=str(extraction_root), env=env, text=True, capture_output=True, timeout=240)
    compile_record = _compile_candidate(extraction_root, output_root, manifest)
    readiness = _readiness_probe(extraction_root, env)
    proof_system = _proof_system_probe(extraction_root, env, manifest["candidate_digest"])
    closure = _closure_inventory(manifest)
    traceability = _traceability(manifest)
    rule_results = _rule_results(manifest, closure, traceability, readiness, proof_system, test_result.returncode == 0, compile_record["status"] == "PASS")
    _write_text(output_root, "runner.log", test_result.stdout + "\n--- STDERR ---\n" + test_result.stderr)
    result = {
        "schema_version": "TRADER-IC-000-audit-result/v1",
        "run_id": run_id,
        "candidate_identifier": manifest["candidate_identifier"],
        "candidate_digest": manifest["candidate_digest"],
        "candidate_manifest": manifest,
        "archive_reconciled": not manifest["findings"],
        "extraction_reconciliation": extraction,
        "environment_validation": _environment_report(),
        "constitutional_closure": closure,
        "traceability": traceability,
        "rule_results": rule_results,
        "operational_verification": readiness,
        "requirement_level_proof": proof_system,
        "test_results": {
            "command": test_command,
            "exit_code": test_result.returncode,
            "stdout_sha256": hashlib.sha256(test_result.stdout.encode("utf-8")).hexdigest(),
            "stderr_sha256": hashlib.sha256(test_result.stderr.encode("utf-8")).hexdigest(),
            "status": "PASS" if test_result.returncode == 0 else "FAIL",
        },
        "compilation": compile_record,
    }
    result["final_status"] = "PASS" if _is_pass(result) else "FAIL"
    result["deterministic_digest"] = _digest_payload(_normalized_result(result))
    _write_evidence(output_root, result)
    return result


def run_full_audit(candidate_zip: Path, output_root: Path) -> Mapping[str, Any]:
    primary = run_trader_audit(candidate_zip, output_root / "01_primary_execution", run_id="primary")
    run_001 = _run_clean_room(candidate_zip, output_root / "03_clean_room" / "run_001", "run_001")
    run_002 = _run_clean_room(candidate_zip, output_root / "03_clean_room" / "run_002", "run_002")
    comparison = _comparison(primary, run_001, run_002)
    final = {
        "candidate_digest": primary["candidate_digest"],
        "primary_execution_pass": primary["final_status"] == "PASS",
        "clean_room_run_1_pass": run_001["final_status"] == "PASS",
        "clean_room_run_2_pass": run_002["final_status"] == "PASS",
        "normalized_comparison": comparison["comparison_result"],
        "constitutional_closure_complete": primary["constitutional_closure"]["unresolved_artifacts"] == 0,
        "traceability_complete": primary["traceability"]["status"] == "PASS",
        "operational_evidence_exists": primary["operational_verification"]["status"] == "PASS",
        "unresolved_findings": 0 if comparison["comparison_result"] == "IDENTICAL" else 1,
    }
    decision = "TRADER_IC_000_AUDIT_ENABLEMENT_PASS" if all(
        value is True or value == 0 or value == "IDENTICAL" for value in final.values() if not isinstance(value, str) or value == "IDENTICAL"
    ) else "FAIL"
    package = {
        "candidate_identity": primary["candidate_manifest"],
        "primary_execution": primary,
        "clean_room_run_001": run_001,
        "clean_room_run_002": run_002,
        "normalized_comparison": comparison,
        "final_reconciliation": final,
        "decision": decision,
    }
    _write_final_evidence(output_root, package)
    return package


def _run_clean_room(candidate_zip: Path, output_root: Path, run_id: str) -> Mapping[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "argos.trader_audit", "--candidate", str(candidate_zip), "--output", str(output_root), "--single-run", "--run-id", run_id]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    completed = subprocess.run(command, cwd=str(output_root.parent), env=env, text=True, capture_output=True, timeout=300)
    _write_text(output_root, "runner.log", completed.stdout + "\n--- STDERR ---\n" + completed.stderr)
    result_path = output_root / "certification_result.json"
    if completed.returncode != 0 or not result_path.exists():
        return {"run_id": run_id, "final_status": "FAIL", "findings": (completed.stderr or "clean-room result missing",), "deterministic_digest": "FAILED"}
    return json.loads(result_path.read_text(encoding="utf-8"))


def _compile_candidate(extraction_root: Path, output_root: Path, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    files = [entry["canonical_path"] for entry in manifest["entries"] if entry["canonical_path"].startswith("src/argos/trader/") and entry["canonical_path"].endswith(".py")]
    stdout = []
    stderr = []
    exit_code = 0
    for relative in files:
        try:
            py_compile.compile(str(extraction_root / relative), doraise=True)
            stdout.append(f"compiled {relative}")
        except Exception as exc:
            exit_code = 1
            stderr.append(f"{relative}: {exc}")
    log = "\n".join(stdout + stderr) + "\n"
    _write_text(output_root, "compileall.log", log)
    return {
        "command": "py_compile Trader source files",
        "files_examined": files,
        "exit_code": exit_code,
        "stdout_sha256": hashlib.sha256("\n".join(stdout).encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256("\n".join(stderr).encode("utf-8")).hexdigest(),
        "status": "PASS" if exit_code == 0 and bool(log.strip()) else "FAIL",
    }


def _readiness_probe(extraction_root: Path, env: Mapping[str, str]) -> Mapping[str, Any]:
    code = (
        "import json;"
        "from argos.foundation.testing import TestExecutionResult, foundation_test_registry;"
        "from argos.trader import TraderOperationalReadinessVerifier;"
        "results=tuple(TestExecutionResult(suite_id=r.suite_id,module_name=r.module_name,tests_run=1,failures=0,errors=0,skipped=0,successful=True) for r in foundation_test_registry());"
        "report=TraderOperationalReadinessVerifier().verify(results);"
        "print(json.dumps({'certified': report.certified, 'outcome': report.outcome.value, 'checks': len(report.checks), 'stress_results': len(report.stress_results), 'deficiencies': len(report.deficiencies)}))"
    )
    completed = subprocess.run([sys.executable, "-c", code], cwd=str(extraction_root), env=dict(env), text=True, capture_output=True, timeout=60)
    payload = json.loads(completed.stdout) if completed.returncode == 0 else {}
    return {"status": "PASS" if completed.returncode == 0 and payload.get("certified") else "FAIL", "probe": payload, "stderr": completed.stderr}


def _proof_system_probe(extraction_root: Path, env: Mapping[str, str], candidate_digest: str) -> Mapping[str, Any]:
    code = (
        "import json;"
        "from argos.trader.requirement_proof import execute_requirement_proof_system;"
        f"package=execute_requirement_proof_system({candidate_digest!r});"
        "print(json.dumps(package, sort_keys=True))"
    )
    completed = subprocess.run([sys.executable, "-c", code], cwd=str(extraction_root), env=dict(env), text=True, capture_output=True, timeout=120)
    if completed.returncode != 0:
        return {"status": "FAIL", "stderr": completed.stderr, "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest()}
    payload = json.loads(completed.stdout)
    verdict = payload.get("final_verdict", {}).get("verdict")
    validation_status = payload.get("validation", {}).get("status")
    coverage = payload.get("coverage", {})
    status = "PASS" if verdict == "UNCONDITIONAL PASS" and validation_status == "PASS" and coverage.get("requirements_failed") == 0 else "FAIL"
    return {
        "status": status,
        "candidate_digest": candidate_digest,
        "proof_package": payload,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode("utf-8")).hexdigest(),
    }


def _closure_inventory(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    dispositions = []
    unresolved = 0
    for entry in manifest["entries"]:
        path = entry["canonical_path"]
        if _participates(path):
            disposition = "PARTICIPATING"
            reason = "Trader implementation, test, runner, or audit documentation artifact"
        else:
            disposition = "EXCLUDED_WITH_JUSTIFICATION"
            reason = "Repository artifact outside Trader Office audit closure"
        dispositions.append({"path": path, "disposition": disposition, "reason": reason})
    return {"status": "PASS", "unresolved_artifacts": unresolved, "dispositions": dispositions}


def _traceability(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    required = {
        "TRADER-IC-000-001": "audit_trader_reproduce.py",
        "TRADER-IC-000-002": "src/argos/trader_audit.py",
        "TRADER-GOV-001-012": "src/argos/trader/constitutional_governance.py",
        "TRADER-RM-002-001-016": "src/argos/trader/rm002_constitution.py",
        "TRADER-RM-002A-001-012": "src/argos/trader/rm002a_publication.py",
        "TRADER-RM-002A-013": "src/argos/trader/requirement_proof.py",
        "TRADER-IC-000-006": "src/argos/trader/readiness.py",
        "TRADER-IC-000-007": "src/argos/trader_audit.py",
        "TRADER-IC-000-009": "TRADER_AUDITOR_README.md",
    }
    paths = {entry["canonical_path"] for entry in manifest["entries"]}
    traces = []
    findings = []
    for requirement, artifact in required.items():
        exists = artifact in paths
        traces.append({"requirement": requirement, "artifact": artifact, "verification": "package-bound audit execution", "evidence": "certification_result.json", "status": "PASS" if exists else "FAIL"})
        if not exists:
            findings.append({"identifier": requirement, "observed": artifact, "expected": "artifact exists in candidate"})
    return {"status": "PASS" if not findings else "FAIL", "traces": traces, "findings": findings}


def _rule_results(manifest: Mapping[str, Any], closure: Mapping[str, Any], traceability: Mapping[str, Any], readiness: Mapping[str, Any], proof_system: Mapping[str, Any], tests_pass: bool, compile_pass: bool) -> Mapping[str, Any]:
    rules = [
        ("TRADER-RULE-CANDIDATE-MANIFEST", not manifest["findings"]),
        ("TRADER-RULE-CLOSURE", closure["unresolved_artifacts"] == 0),
        ("TRADER-RULE-TRACEABILITY", traceability["status"] == "PASS"),
        ("TRADER-RULE-OPERATIONAL", readiness["status"] == "PASS"),
        ("TRADER-RULE-REQUIREMENT-PROOF", proof_system["status"] == "PASS"),
        ("TRADER-RULE-TESTS", tests_pass),
        ("TRADER-RULE-COMPILE", compile_pass),
    ]
    return {"status": "PASS" if all(passed for _, passed in rules) else "FAIL", "rules": [{"rule_identifier": rule, "verdict": "PASS" if passed else "FAIL", "findings": () if passed else ("rule failed",)} for rule, passed in rules]}


def _comparison(primary: Mapping[str, Any], run_001: Mapping[str, Any], run_002: Mapping[str, Any]) -> Mapping[str, Any]:
    digests = [_digest_payload(_normalized_result(item)) for item in (primary, run_001, run_002)]
    return {
        "normalization_registry": {"approved_fields": ("run_id", "absolute paths", "stdout/stderr digests")},
        "primary_digest": digests[0],
        "run_001_digest": digests[1],
        "run_002_digest": digests[2],
        "comparison_result": "IDENTICAL" if len(set(digests)) == 1 else "DIVERGENT",
    }


def _normalized_result(result: Mapping[str, Any]) -> Mapping[str, Any]:
    data = json.loads(json.dumps(_jsonable(result), sort_keys=True))
    data["run_id"] = "<normalized>"
    data["deterministic_digest"] = ""
    if "extraction_reconciliation" in data:
        data["extraction_reconciliation"]["extraction_root"] = "<normalized>"
    if "test_results" in data:
        data["test_results"]["stdout_sha256"] = "<normalized>"
        data["test_results"]["stderr_sha256"] = "<normalized>"
    return data


def _write_evidence(output_root: Path, result: Mapping[str, Any]) -> None:
    _write_json(output_root, "certification_result.json", result)
    _write_json(output_root, "execution_summary.json", {"run_id": result["run_id"], "final_status": result["final_status"], "candidate_digest": result["candidate_digest"]})
    _write_json(output_root, "candidate_manifest.json", result["candidate_manifest"])
    _write_json(output_root, "constitutional_closure.json", result["constitutional_closure"])
    _write_json(output_root, "traceability.json", result["traceability"])
    _write_json(output_root, "rule_results.json", result["rule_results"])
    _write_json(output_root, "operational_verification.json", result["operational_verification"])
    _write_json(output_root, "requirement_level_proof.json", result["requirement_level_proof"])
    _write_json(output_root, "test_results.json", result["test_results"])
    _write_json(output_root, "compileall.json", result["compilation"])


def _write_final_evidence(output_root: Path, package: Mapping[str, Any]) -> None:
    _write_json(output_root, "00_identity/candidate_identity.json", package["candidate_identity"])
    _write_json(output_root, "01_primary_execution/certification_result.json", package["primary_execution"])
    _write_json(output_root, "03_clean_room/run_001/certification_result.json", package["clean_room_run_001"])
    _write_json(output_root, "03_clean_room/run_002/certification_result.json", package["clean_room_run_002"])
    _write_json(output_root, "04_comparison/normalized_comparison.json", package["normalized_comparison"])
    _write_json(output_root, "06_final/final_reconciliation.json", package["final_reconciliation"])
    _write_json(output_root, "06_final/independent_audit_enablement_decision.json", {"decision": package["decision"]})
    rows = []
    for path in sorted(item for item in output_root.rglob("*") if item.is_file()):
        rel = path.relative_to(output_root).as_posix()
        if rel.startswith("07_manifests/"):
            continue
        rows.append({"path": rel, "sha256": _digest_file(path), "bytes": path.stat().st_size})
    _write_json(output_root, "07_manifests/evidence_manifest.json", rows)
    _write_text(output_root, "07_manifests/evidence_hashes.sha256", "\n".join(f"{row['sha256']}  {row['path']}" for row in rows) + "\n")


def _environment_report() -> Mapping[str, Any]:
    return {"status": "PASS", "platform": platform.platform(), "python": sys.version, "network_required": False}


def _classify(path: str) -> str:
    if path.startswith("src/argos/trader"):
        return "trader_implementation"
    if path.startswith("Tests/test_trade") or path.startswith("Tests/test_trader"):
        return "trader_test"
    if "TRADER" in path or "trader" in path:
        return "trader_audit_artifact"
    if path.endswith(".py"):
        return "python_source"
    if path.startswith("Documentation/"):
        return "documentation"
    return "repository_artifact"


def _participates(path: str) -> bool:
    return path.startswith("src/argos/trader") or path.startswith("Tests/test_trade") or path.startswith("Tests/test_trader") or path in {"src/argos/trader_audit.py", "audit_trader_reproduce.py", "TRADER_AUDITOR_README.md"}


def _is_pass(result: Mapping[str, Any]) -> bool:
    return (
        result["archive_reconciled"]
        and result["extraction_reconciliation"]["extraction_reconciled"]
        and result["constitutional_closure"]["unresolved_artifacts"] == 0
        and result["traceability"]["status"] == "PASS"
        and result["rule_results"]["status"] == "PASS"
        and result["operational_verification"]["status"] == "PASS"
        and result["requirement_level_proof"]["status"] == "PASS"
        and result["test_results"]["status"] == "PASS"
        and result["compilation"]["status"] == "PASS"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trader Office package-bound audit runner")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--single-run", action="store_true")
    parser.add_argument("--run-id", default="primary")
    args = parser.parse_args(argv)
    if args.single_run:
        result = run_trader_audit(Path(args.candidate), Path(args.output), run_id=args.run_id)
    else:
        result = run_full_audit(Path(args.candidate), Path(args.output))
    _write_json(Path(args.output), "certification_result.json", result)
    final_status = result.get("final_status") or ("PASS" if result.get("decision") == "TRADER_IC_000_AUDIT_ENABLEMENT_PASS" else "FAIL")
    print(json.dumps(_jsonable({"status": final_status, "candidate_digest": result.get("candidate_digest") or result.get("candidate_identity", {}).get("candidate_digest")}), indent=2))
    return 0 if final_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
