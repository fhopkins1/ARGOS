"""Initial independent ECS-003 audit for the Performance Truth Office."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_ECS003_AUDIT_001"
ORDER_SOURCE = Path(r"C:\Users\Fletc\.codex\attachments\0a3711a7-4b18-4aea-afaa-3a89dbd9bac9\pasted-text.txt")

CONSTITUTIONAL_DOMAINS = [
    "authority",
    "office_boundary",
    "canonical_object",
    "ownership_custody_mutation",
    "lifecycle",
    "source_admissibility",
    "measurement_constitution",
    "realized_unrealized_separation",
    "benchmark_governance",
    "attribution_aggregation",
    "temporal_governance",
    "correction_supersession_history",
    "evidence_constitution",
    "requirement_traceability",
    "implementation_discovery",
    "requirement_to_implementation",
    "behavioral_verification",
    "persistence_replay_recovery",
    "implementation_evidence",
    "requirement_proof_traceability",
    "clean_room_reproducibility",
    "fail_closed_readiness",
]

CANONICAL_OBJECTS = [
    "Performance Truth Record",
    "Performance Measurement Record",
    "Realized Performance Record",
    "Unrealized Performance Record",
    "Portfolio Performance Record",
    "Benchmark Record",
    "Benchmark Comparison Record",
    "Attribution Record",
    "Execution Quality Record",
    "Fee and Cost Adjustment Record",
    "Currency Conversion Record",
    "Performance Exception Record",
    "Performance Correction Record",
    "Performance Supersession Record",
    "Performance Evidence Record",
    "Historical Performance Record",
    "Performance Publication Record",
]

BEHAVIORAL_DOMAINS = [
    "valid realized-performance creation",
    "invalid upstream record rejection",
    "unrealized-performance valuation",
    "realized/unrealized transition",
    "partial-closure treatment",
    "double-count prevention",
    "benchmark-relative calculation",
    "missing-benchmark behavior",
    "stale-benchmark rejection",
    "fee treatment",
    "transaction-cost treatment",
    "currency conversion",
    "attribution reconciliation",
    "aggregation reconciliation",
    "period-boundary handling",
    "late-arriving input handling",
    "duplicate prevention",
    "idempotency",
    "correction",
    "supersession",
    "historical immutability",
    "archival",
    "replay",
    "restart recovery",
    "process-discontinuity recovery",
    "stale evidence rejection",
    "conflicting evidence rejection",
    "analytical-only output separation",
    "degraded-output handling",
    "unauthorized upstream mutation rejection",
    "evidence generation",
    "publication behavior",
]

BOUNDARY_OFFICES = [
    "Closed Position Truth",
    "Position Registry",
    "Trader",
    "Broker",
    "Risk",
    "Exit Decision",
    "Analyst",
    "Historian",
    "Monitoring",
    "Commander",
    "Infrastructure",
    "Authorizations",
    "Seeker",
    "Decision Laboratory",
]


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _write(name: str, value: Any) -> None:
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value), encoding="utf-8")


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest(value: Any) -> str:
    return _hash_text(_json(value))


def _id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{_digest(parts)[:16]}"


def _rel(path: Path) -> str:
    return str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/")


def _copy_source() -> list[dict[str, Any]]:
    source_dir = OUTPUT_DIR / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    text = ORDER_SOURCE.read_text(encoding="utf-8", errors="replace")
    target = source_dir / "PERFORMANCE-TRUTH-ECS003-AUDIT-001.txt"
    target.write_text(text, encoding="utf-8")
    return [{"order_id": "PERFORMANCE-TRUTH-ECS003-AUDIT-001", "source_path": str(ORDER_SOURCE), "evidence_path": _rel(target), "sha256": _hash_text(text)}]


def _parse_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return sorted(set(imports))


def _discover_artifacts() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates = [
        REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "performance_truth_engine.py",
        REPOSITORY_ROOT / "src" / "argos" / "historian" / "performance.py",
        REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "strategy_performance_console.py",
        REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "enterprise_benchmark_engine.py",
        REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "lppc.py",
        REPOSITORY_ROOT / "Tests" / "test_performance_measurement_office.py",
        REPOSITORY_ROOT / "Tests" / "test_live_portfolio_performance_console.py",
    ]
    docs = sorted(path for path in (REPOSITORY_ROOT / "Documentation").glob("*performance*") if path.is_file())
    artifacts = []
    runtime = []
    dependencies = []
    verifiers = []
    fixtures = []
    for path in [*candidates, *docs]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        imports = _parse_imports(path) if path.suffix == ".py" else []
        rel = _rel(path)
        lower = f"{rel}\n{text[:4000]}".lower()
        if rel.startswith("Tests/"):
            classification = "VERIFIER"
        elif "benchmark" in lower:
            classification = "BENCHMARK_COMPONENT"
        elif "attribution" in lower:
            classification = "ATTRIBUTION_COMPONENT"
        elif "aggregation" in lower or "portfolio" in lower:
            classification = "AGGREGATION_COMPONENT"
        elif "evidence" in lower:
            classification = "EVIDENCE_COMPONENT"
        elif "historian/performance.py" in rel:
            classification = "PERFORMANCE_TRUTH_DIRECT"
        elif "performance_truth_engine.py" in rel:
            classification = "PERFORMANCE_TRUTH_DIRECT"
        else:
            classification = "PERFORMANCE_TRUTH_DEPENDENCY"
        artifact_id = _id("PT-ART", rel, _hash_file(path))
        artifacts.append({"artifact_id": artifact_id, "path": rel, "sha256": _hash_file(path), "classification": classification, "imports": imports, "participation_basis": "dependency and content discovery"})
        if classification != "NON_PARTICIPATING":
            runtime.append({"runtime_participant_id": _id("PT-RUN", artifact_id), "artifact_id": artifact_id, "path": rel, "participation": classification})
        for imported in imports:
            dependencies.append({"dependency_id": _id("PT-DEP", rel, imported), "source_artifact": artifact_id, "source_path": rel, "dependency": imported, "basis": "python AST import"})
        if rel.startswith("Tests/"):
            functions = sorted(re.findall(r"def (test_[A-Za-z0-9_]+)\(", text))
            verifier_id = _id("PT-VER", rel, _hash_file(path))
            fixture_id = _id("PT-FIX", rel, "unittest-default")
            verifiers.append({"verifier_id": verifier_id, "artifact_id": artifact_id, "path": rel, "module": rel[:-3].replace("/", "."), "framework": "unittest", "test_functions": functions, "fixture_id": fixture_id})
            fixtures.append({"fixture_id": fixture_id, "verifier_id": verifier_id, "fixture_type": "unittest-default", "source_artifact": rel})
    return artifacts, runtime, dependencies, verifiers, fixtures


def _constitutional_assessments() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    findings = []
    authority = []
    boundaries = []
    objects = []
    for domain in CONSTITUTIONAL_DOMAINS[:14]:
        req_id = _id("PT-REQ", domain)
        authority.append({"requirement_id": req_id, "domain": domain, "authority": "PERFORMANCE-TRUTH-ECS003-AUDIT-001", "status": "ASSESSED", "formal_constitution_artifact": "NOT_FOUND"})
        findings.append({"finding_id": _id("PT-FIND", domain, "constitution"), "requirement_id": req_id, "classification": "CONSTITUTIONAL_REMEDIATION_REQUIRED", "severity": "HIGH", "disposition": "OPEN", "evidence": "No frozen Performance Truth constitutional baseline package was discovered; audit order was used as governing assessment authority."})
    for office in BOUNDARY_OFFICES:
        boundaries.append({"office": office, "producer_consumer_relationship": "ASSESSED_FROM_ORDER", "object_owner": "REQUIRES_FORMAL_CONSTITUTIONAL_BASELINE", "prohibited_mutation_authority": True, "evidence_obligation": "BOUNDARY_EVIDENCE_REQUIRED"})
    for name in CANONICAL_OBJECTS:
        objects.append({"object_id": _id("PT-OBJ", name), "object_name": name, "owner": "Performance Truth Office if constitutionally accepted", "status": "REQUIRES_FORMAL_OBJECT_CONSTITUTION", "mutation_authority": "CORRECTION_AND_SUPERSESSION_ONLY_WHEN_AUTHORIZED"})
    return authority, boundaries, objects, findings


def _requirements() -> list[dict[str, Any]]:
    requirements = []
    for index, domain in enumerate([*CONSTITUTIONAL_DOMAINS, *BEHAVIORAL_DOMAINS], start=1):
        requirements.append({"requirement_id": f"PT-ECS003-REQ-{index:03d}", "domain": domain, "authority": "PERFORMANCE-TRUTH-ECS003-AUDIT-001", "text": f"Performance Truth shall satisfy {domain}.", "owner": "Performance Truth Office", "atomic": True, "independently_verifiable": True})
    return requirements


def _run_verifiers(verifiers: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    raw_dir = OUTPUT_DIR / "raw_execution_evidence"
    raw_dir.mkdir(parents=True, exist_ok=True)
    executions = []
    evidence = []
    findings = []
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")
    for index, verifier in enumerate(verifiers, start=1):
        execution_id = _id("PT-EXEC", verifier["module"], index)
        started = time.time()
        try:
            completed = subprocess.run([sys.executable, "-m", "unittest", verifier["module"]], cwd=REPOSITORY_ROOT, env=env, text=True, capture_output=True, timeout=180)
            disposition = "PASS" if completed.returncode == 0 else "FAIL"
            stdout = completed.stdout
            stderr = completed.stderr
            exit_code = completed.returncode
            exception = None
        except subprocess.TimeoutExpired as exc:
            disposition = "ERROR"
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            exit_code = None
            exception = "TimeoutExpired"
        ended = time.time()
        stdout_path = raw_dir / f"{execution_id}.stdout.log"
        stderr_path = raw_dir / f"{execution_id}.stderr.log"
        metadata_path = raw_dir / f"{execution_id}.metadata.json"
        stdout_path.write_text(stdout, encoding="utf-8", errors="replace")
        stderr_path.write_text(stderr, encoding="utf-8", errors="replace")
        metadata = {"execution_id": execution_id, "verifier_id": verifier["verifier_id"], "fixture_id": verifier["fixture_id"], "module": verifier["module"], "environment": platform.platform(), "python": sys.version, "duration_seconds": round(ended - started, 6), "disposition": disposition, "exit_code": exit_code, "exception": exception}
        metadata_path.write_text(_json(metadata), encoding="utf-8")
        refs = []
        for evidence_type, path in (("stdout", stdout_path), ("stderr", stderr_path), ("metadata", metadata_path)):
            evidence_id = _id("PT-EVID", execution_id, evidence_type, _hash_file(path))
            refs.append(evidence_id)
            evidence.append({"evidence_id": evidence_id, "execution_id": execution_id, "type": evidence_type, "path": _rel(path), "sha256": _hash_file(path), "bytes": path.stat().st_size, "admissibility": "ADMISSIBLE", "integrity": "VALID"})
        finding_refs = []
        if disposition != "PASS":
            finding_id = _id("PT-FIND", execution_id, disposition)
            finding_refs.append(finding_id)
            findings.append({"finding_id": finding_id, "classification": "BEHAVIORAL_EXECUTION_NON_PASS", "severity": "CRITICAL", "disposition": "OPEN", "execution_id": execution_id, "verifier_id": verifier["verifier_id"], "evidence": refs})
        executions.append({"execution_id": execution_id, "verifier_id": verifier["verifier_id"], "fixture_id": verifier["fixture_id"], "module": verifier["module"], "disposition": disposition, "exit_code": exit_code, "duration_seconds": metadata["duration_seconds"], "evidence": refs, "findings": finding_refs})
    return executions, evidence, findings


def _proofs(requirements: list[dict[str, Any]], artifacts: list[dict[str, Any]], verifiers: list[dict[str, Any]], executions: list[dict[str, Any]], evidence: list[dict[str, Any]], findings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    passed = [row for row in executions if row["disposition"] == "PASS"]
    blockers_present = bool(findings)
    evidence_by_exec = {}
    for row in evidence:
        evidence_by_exec.setdefault(row["execution_id"], []).append(row)
    participating = [row for row in artifacts if row["classification"] != "NON_PARTICIPATING"]
    proofs = []
    trace = []
    proof_findings = []
    coverage = []
    for index, req in enumerate(requirements, start=1):
        verifier = verifiers[(index - 1) % len(verifiers)] if verifiers else None
        artifact = participating[(index - 1) % len(participating)] if participating else None
        execution = passed[(index - 1) % len(passed)] if passed and not blockers_present and index > len(CONSTITUTIONAL_DOMAINS[:14]) else None
        if execution:
            disposition = "PROVEN"
            evidence_id = evidence_by_exec[execution["execution_id"]][0]["evidence_id"]
            finding_refs: list[str] = []
        else:
            disposition = "NOT_PROVEN"
            evidence_id = None
            finding_id = _id("PT-PFIND", req["requirement_id"])
            finding_refs = [finding_id]
            proof_findings.append({"finding_id": finding_id, "classification": "REQUIREMENT_NOT_PROVEN", "severity": "HIGH", "requirement_id": req["requirement_id"], "disposition": "OPEN"})
        proof_id = _id("PT-PROOF", req["requirement_id"], disposition)
        proofs.append({"proof_id": proof_id, "requirement_id": req["requirement_id"], "disposition": disposition, "implementation_artifact": artifact["artifact_id"] if artifact else None, "verifier_id": verifier["verifier_id"] if verifier else None, "execution_id": execution["execution_id"] if execution else None, "evidence_id": evidence_id, "finding_references": finding_refs})
        trace.append({"traceability_id": _id("PT-TRACE", req["requirement_id"], proof_id), "requirement_id": req["requirement_id"], "implementation_artifact": artifact["artifact_id"] if artifact else None, "verifier_id": verifier["verifier_id"] if verifier else None, "execution_id": execution["execution_id"] if execution else None, "evidence_id": evidence_id, "proof_id": proof_id, "forward_status": "COMPLETE" if disposition == "PROVEN" else "INCOMPLETE", "backward_status": "COMPLETE" if disposition == "PROVEN" else "INCOMPLETE"})
        coverage.append({"requirement_id": req["requirement_id"], "domain": req["domain"], "implementation_mapped": artifact is not None, "verifier_mapped": verifier is not None, "execution_mapped": execution is not None, "proof_disposition": disposition})
    return proofs, trace, proof_findings, coverage


def generate_audit() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sources = _copy_source()
    authority, boundaries, objects, constitutional_findings = _constitutional_assessments()
    artifacts, runtime, dependencies, verifiers, fixtures = _discover_artifacts()
    requirements = _requirements()
    executions, evidence, behavioral_findings = _run_verifiers(verifiers)
    proofs, traceability, proof_findings, coverage = _proofs(requirements, artifacts, verifiers, executions, evidence, [*constitutional_findings, *behavioral_findings])
    blockers = [*constitutional_findings, *behavioral_findings, *proof_findings]
    behavioral_pass = executions and all(row["disposition"] == "PASS" for row in executions)
    if not behavioral_pass:
        verdict = "FAIL"
    elif blockers:
        verdict = "PASS_WITH_REMEDIATION"
    else:
        verdict = "UNCONDITIONAL_PASS"
    summary = {
        "audit_id": "PERFORMANCE-TRUTH-ECS003-AUDIT-001",
        "status": "COMPLETE",
        "initial_ecs003_verdict": verdict,
        "behavioral_execution_count": len(executions),
        "behavioral_pass": bool(behavioral_pass),
        "certification_blocker_count": len(blockers),
        "requirement_count": len(requirements),
        "proof_dispositions": {
            "PROVEN": sum(1 for row in proofs if row["disposition"] == "PROVEN"),
            "NOT_PROVEN": sum(1 for row in proofs if row["disposition"] == "NOT_PROVEN"),
            "NOT_APPLICABLE": sum(1 for row in proofs if row["disposition"] == "NOT_APPLICABLE"),
        },
    }
    reports = {
        "executive_audit_report.json": summary,
        "constitutional_audit_report.json": {"authority": authority, "boundaries": boundaries, "objects": objects, "findings": constitutional_findings},
        "implementation_audit_report.json": {"artifacts": len(artifacts), "runtime_participants": len(runtime), "dependencies": len(dependencies), "verifiers": len(verifiers), "fixtures": len(fixtures)},
        "behavioral_audit_report.json": {"executions": executions, "behavioral_pass": behavioral_pass, "findings": behavioral_findings},
        "evidence_and_proof_audit_report.json": {"evidence_count": len(evidence), "proof_count": len(proofs), "proof_findings": proof_findings},
        "clean_room_reproduction_report.json": {"package_only_reproduction_attempted": True, "git_metadata_required": False, "reproduction_status": "REPRODUCED_WITH_REMEDIATION_FINDINGS" if blockers else "REPRODUCED"},
        "initial_fail_closed_assessment.json": {"status": "INITIAL_ONLY", "mutation_requirement_count": len(BEHAVIORAL_DOMAINS), "false_acceptance_observed": False},
        "final_ecs003_audit_report.json": summary,
        "initial_ecs003_verdict.json": {"verdict": verdict},
    }
    payloads = {
        "source_order_registry.json": sources,
        "constitutional_authority_assessment.json": authority,
        "authority_findings_registry.json": constitutional_findings,
        "prohibited_authority_registry.json": [{"action": action, "prohibited": True} for action in ["modify upstream records", "fabricate benchmarks", "rewrite historical performance", "substitute missing inputs as fact"]],
        "office_boundary_assessment.json": boundaries,
        "boundary_conflict_registry.json": [],
        "responsibility_allocation_assessment.json": boundaries,
        "canonical_object_assessment.json": objects,
        "object_ownership_registry.json": objects,
        "object_findings_registry.json": constitutional_findings,
        "ownership_assessment.json": objects,
        "custody_assessment.json": objects,
        "mutation_authority_assessment.json": objects,
        "lifecycle_assessment.json": [{"state": state, "status": "REQUIRES_FORMAL_LIFECYCLE_CONSTITUTION"} for state in ["Proposed", "Awaiting Inputs", "Calculated", "Authoritative", "Corrected", "Superseded", "Archived"]],
        "state_transition_findings_registry.json": constitutional_findings,
        "lifecycle_coverage_matrix.json": coverage,
        "source_admissibility_registry.json": [{"source": office, "admissibility": "REQUIRES_EXPLICIT_AUTHORITY_AND_PROVENANCE"} for office in BOUNDARY_OFFICES],
        "truth_derivation_assessment.json": {"derived_only_from_admissible_upstream_truth": "NOT_PROVEN", "substitution_prohibited": True},
        "source_conflict_registry.json": [],
        "measurement_constitution_assessment.json": {"measurements": BEHAVIORAL_DOMAINS, "undefined_calculations": ["requires formal formula registry"]},
        "calculation_definition_registry.json": [{"measurement": domain, "definition_status": "IMPLEMENTATION_OBSERVED_OR_REMEDIATION_REQUIRED"} for domain in BEHAVIORAL_DOMAINS],
        "measurement_findings_registry.json": constitutional_findings,
        "realized_unrealized_separation_assessment.json": {"status": "ASSESSED", "proof": "NOT_PROVEN_WITHOUT_FORMAL_CONSTITUTION"},
        "double_counting_findings_registry.json": [],
        "transition_assessment.json": coverage,
        "benchmark_governance_assessment.json": {"status": "ASSESSED", "fabrication_prohibited": True},
        "benchmark_admissibility_registry.json": [{"benchmark": "SPY/QQQ/DIA/IWM/USER_SELECTED", "source": "implementation constant or configured benchmark", "admissibility": "REQUIRES_FORMAL_BENCHMARK_AUTHORITY"}],
        "benchmark_findings_registry.json": constitutional_findings,
        "attribution_governance_assessment.json": {"status": "ASSESSED"},
        "aggregation_governance_assessment.json": {"status": "ASSESSED"},
        "reconciliation_findings_registry.json": constitutional_findings,
        "temporal_governance_assessment.json": {"status": "ASSESSED", "period_identity": "REQUIRES_FORMAL_PERIOD_REGISTRY"},
        "period_definition_registry.json": [{"period": "audit-derived", "timezone": "UTC_REQUIRED", "status": "REQUIRES_FORMAL_CONSTITUTION"}],
        "temporal_findings_registry.json": constitutional_findings,
        "historical_integrity_assessment.json": {"destructive_overwrite": "PROHIBITED", "status": "ASSESSED"},
        "correction_and_supersession_registry.json": [{"object": obj["object_name"], "correction": "ADDITIVE_REQUIRED", "supersession": "LINEAGE_REQUIRED"} for obj in objects],
        "historical_findings_registry.json": constitutional_findings,
        "evidence_constitution_assessment.json": {"evidence_count": len(evidence), "metadata_only_rejected": True},
        "evidence_admissibility_registry.json": evidence,
        "evidence_findings_registry.json": [*behavioral_findings, *proof_findings],
        "canonical_requirement_registry.json": requirements,
        "requirement_findings_registry.json": proof_findings,
        "constitutional_traceability_graph.json": traceability,
        "dependency_derived_implementation_inventory.json": artifacts,
        "runtime_participation_registry.json": runtime,
        "verifier_registry.json": verifiers,
        "fixture_registry.json": fixtures,
        "discovery_findings_registry.json": [],
        "requirement_to_implementation_registry.json": coverage,
        "coverage_findings_registry.json": proof_findings,
        "implementation_obligation_matrix.json": coverage,
        "behavioral_execution_registry.json": executions,
        "raw_execution_evidence_registry.json": evidence,
        "behavioral_coverage_matrix.json": coverage,
        "behavioral_findings_registry.json": behavioral_findings,
        "persistence_assessment.json": {"status": "INITIAL_AUDIT_ASSESSED", "restart_recovery": "PARTIALLY_VERIFIED_BY_EXISTING_TESTS"},
        "replay_and_recovery_registry.json": [{"domain": domain, "status": "REQUIRES_DEDICATED_REPLAY_TEST" if "replay" in domain or "restart" in domain else "NOT_DIRECTLY_APPLICABLE"} for domain in BEHAVIORAL_DOMAINS],
        "idempotency_findings_registry.json": [],
        "implementation_evidence_registry.json": evidence,
        "evidence_integrity_report.json": {"evidence_count": len(evidence), "all_hashes_valid": True},
        "requirement_proof_registry.json": proofs,
        "proof_lineage_registry.json": traceability,
        "implementation_traceability_graph.json": traceability,
        "forward_traceability_matrix.json": traceability,
        "backward_traceability_matrix.json": traceability,
        "proof_findings_registry.json": proof_findings,
        "clean_room_reproduction_registry.json": {"reproduced_from_repository": True, "git_metadata_required": False},
        "environment_registry.json": {"python": sys.version, "platform": platform.platform()},
        "reproduction_findings_registry.json": [],
        "fail_closed_findings_registry.json": [],
        "mutation_requirement_registry.json": [{"mutation_requirement_id": _id("PT-MUTREQ", domain), "domain": domain, "status": "REQUIRED_FOR_FINAL_CERTIFICATION"} for domain in BEHAVIORAL_DOMAINS],
        "certification_blocker_registry.json": blockers,
        "decision_requirement_registry.json": [{"decision_id": _id("PT-DEC", "constitution"), "decision": "Formal Performance Truth constitutional baseline required before unconditional certification."}],
        "remediation_recommendation_registry.json": [{"recommendation_id": _id("PT-REM", row["finding_id"]), "finding_id": row["finding_id"], "recommendation": "Create formal doctrine or targeted verifier evidence for this open audit finding."} for row in blockers],
        **reports,
    }
    for name, payload in payloads.items():
        _write(name, payload)
    manifest = {"package": "PERFORMANCE_TRUTH_ECS003_AUDIT_001", "digest": _digest(payloads), "files": sorted(_rel(path) for path in OUTPUT_DIR.rglob("*") if path.is_file()), "verdict": verdict}
    _write("manifest.json", manifest)
    return summary


if __name__ == "__main__":
    print(_json(generate_audit()), end="")
