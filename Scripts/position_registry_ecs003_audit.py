from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import unittest
import zipfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.contracts import utc_timestamp  # noqa: E402


OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_ECS003_AUDIT_001"
FOCUSED_TEST_MODULES = (
    "Tests.test_or004_position_lifecycle",
    "Tests.test_position_management_office",
)
CONSTITUTIONAL_DOCS = (
    "Documentation/OR-004_Position_Lifecycle_Architecture.md",
    "Documentation/OR-004_Position_and_Trade_Identity_Model.md",
    "Documentation/OR-004_Position_Reconciliation_Specification.md",
    "Documentation/EO-DD_Broker_to_Position_Transaction.md",
    "Documentation/EO-DD_Position_Exit_and_Closure_Transaction.md",
    "Documentation/EO-DA_Authority_Registry.md",
    "Documentation/EO-DA_Write_Site_Registry.md",
    "Documentation/EO-DB_Runtime_Bridge_Registry.md",
    "Documentation/EO-DH_Position_and_EOCK_Audit.md",
)
CANONICAL_REQUIREMENTS = (
    ("POS-REQ-001", "Position Registry authority, ownership, prohibited responsibilities, amendment, freeze, and certification authority are explicit.", "constitutional_authority"),
    ("POS-REQ-002", "Position object and field ownership, custody, mutation authority, correction authority, and read-only consumption are complete.", "ownership_custody"),
    ("POS-REQ-003", "Position lifecycle transitions, terminal states, late events, duplicate events, replay, restart, recovery, correction, and contradiction handling are deterministic.", "lifecycle"),
    ("POS-REQ-004", "Quantity, average cost, long/short behavior, reductions, reversals, precision, fees, settlement, currency, and corporate action treatment are constitutionally governed.", "quantity_cost_basis"),
    ("POS-REQ-005", "Inbound and outbound Position Registry interfaces have authority contracts, schemas, ordering, retry, replay, acknowledgement, and evidence obligations.", "interfaces"),
    ("POS-REQ-006", "Reconciliation and correction preserve source precedence, contradiction lineage, supersession, historical truth, and unresolved discrepancy escalation.", "reconciliation"),
    ("POS-REQ-007", "Temporal doctrine covers event, broker, effective, receipt, processing, persistence, reconciliation, correction, terminal, stale, late, and equal-time semantics.", "temporal"),
    ("POS-REQ-008", "Every position mutation and certification proof is backed by raw execution evidence, immutable provenance, verifier identity, and reproducible proof.", "evidence_proof"),
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_files(root: Path = REPOSITORY_ROOT) -> tuple[str, ...]:
    try:
        output = subprocess.check_output(["git", "ls-files"], cwd=root, text=True, stderr=subprocess.DEVNULL)
        return tuple(line.strip() for line in output.splitlines() if line.strip())
    except Exception:
        return tuple(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and ".git" not in path.parts)


def _candidate_digest(root: Path = REPOSITORY_ROOT) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        files = []
        for rel in _git_files(root):
            path = root / rel
            if path.exists() and path.is_file():
                files.append({"path": rel, "sha256": _file_digest(path), "bytes": path.stat().st_size})
        return "portable:" + hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _constitutional_sources() -> list[dict[str, Any]]:
    sources = []
    for rel in CONSTITUTIONAL_DOCS:
        path = REPOSITORY_ROOT / rel
        sources.append(
            {
                "path": rel,
                "present": path.exists(),
                "sha256": _file_digest(path) if path.exists() else "",
                "contains_position_registry": "Position Registry" in path.read_text(encoding="utf-8", errors="ignore") if path.exists() else False,
            }
        )
    return sources


def _implementation_inventory() -> list[dict[str, Any]]:
    inventory = []
    for rel in _git_files():
        path = REPOSITORY_ROOT / rel
        if not path.exists() or not path.is_file():
            continue
        if not rel.endswith((".py", ".md", ".json")):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "PositionRegistry" not in text and "Position Registry" not in text and "PositionManagementOffice" not in text and "position_management" not in text:
            continue
        if rel == "src/argos/control_panel/position_registry.py":
            classification = "POSITION_REGISTRY_DIRECT"
        elif rel == "src/argos/trader/position_management.py":
            classification = "POSITION_REGISTRY_DEPENDENCY"
        elif rel.startswith("Tests/"):
            classification = "VERIFIER"
        elif rel.startswith("Documentation/"):
            classification = "EVIDENCE_CONSUMER"
        else:
            classification = "POSITION_REGISTRY_DEPENDENCY"
        inventory.append({"path": rel, "classification": classification, "sha256": _file_digest(path), "participation_evidence": "content dependency reference"})
    return sorted(inventory, key=lambda item: (item["classification"], item["path"]))


def _run_tests() -> dict[str, Any]:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module in FOCUSED_TEST_MODULES:
        suite.addTests(loader.loadTestsFromName(module))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    records = []
    for test, traceback in result.failures:
        records.append({"test_identifier": str(test), "disposition": "FAIL", "details": traceback[-2000:]})
    for test, traceback in result.errors:
        records.append({"test_identifier": str(test), "disposition": "ERROR", "details": traceback[-2000:]})
    executed = suite.countTestCases()
    failed_ids = {item["test_identifier"] for item in records}
    for test in _iter_tests(suite):
        test_id = str(test)
        if test_id not in failed_ids:
            records.append({"test_identifier": test_id, "disposition": "PASS", "details": ""})
    return {
        "schema_version": "position-registry-ecs003-focused-tests/v1",
        "modules": FOCUSED_TEST_MODULES,
        "tests_run": executed,
        "successful": result.wasSuccessful(),
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "records": sorted(records, key=lambda item: item["test_identifier"]),
        "runner_output": stream.getvalue(),
    }


def _iter_tests(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_tests(item)
        else:
            yield item


def _findings(constitutional_sources: list[dict[str, Any]], tests: dict[str, Any]) -> list[dict[str, Any]]:
    findings = [
        _finding("POS-ECS003-FINDING-001", "POS-REQ-001", "Position Registry constitutional corpus", "CRITICAL", "No standalone Position Registry constitution establishes complete authority, freeze, amendment, and certification authority.", "CONSTITUTIONAL_BLOCKER", "OPEN", "Create bounded constitutional authority series before freeze."),
        _finding("POS-ECS003-FINDING-002", "POS-REQ-002", "src/argos/control_panel/position_registry.py", "CRITICAL", "Snapshot declares Trader owns Position Objects while audit order requires Position Registry ownership and custody resolution.", "OWNERSHIP_AMBIGUITY", "OPEN", "Reconcile field-level ownership and custody in doctrine."),
        _finding("POS-ECS003-FINDING-003", "POS-REQ-003", "Position Registry lifecycle evidence", "HIGH", "Focused tests cover creation, exit authorization, partial/full closure, and invalid transition rejection, but no complete late, out-of-order, contradiction, restart, or partial-write recovery verification exists.", "IMPLEMENTATION_UNVERIFIED", "OPEN", "Add bounded lifecycle/recovery verification after doctrine closure."),
        _finding("POS-ECS003-FINDING-004", "POS-REQ-004", "Position Registry quantity and cost basis doctrine", "HIGH", "Repository evidence does not fully govern short positions, reversals, fees, settlement, currency, multipliers, corporate actions, or lot-based treatment.", "CONSTITUTIONAL_BLOCKER", "OPEN", "Create quantity and cost-basis doctrine series."),
        _finding("POS-ECS003-FINDING-005", "POS-REQ-007", "Position Registry temporal doctrine", "HIGH", "No complete temporal doctrine covers broker time, effective time, persistence time, equal timestamps, clock skew, and replay ordering semantics.", "CONSTITUTIONAL_BLOCKER", "OPEN", "Create temporal doctrine before certification."),
        _finding("POS-ECS003-FINDING-006", "POS-REQ-008", "Position Registry proof baseline", "CRITICAL", "No one-proof-per-canonical-requirement Position Registry proof baseline exists; existing evidence is test and bridge support, not independently reproducible requirement proof.", "PROOF_INSUFFICIENT", "OPEN", "Create proof construction and clean reproduction series after implementation verification."),
    ]
    if not tests["successful"]:
        findings.append(_finding("POS-ECS003-FINDING-007", "POS-REQ-008", "focused Position Registry verifier population", "CRITICAL", "Focused behavioral verifier failed.", "VERIFIER_FAILED", "OPEN", "Repair verifier or implementation under remediation order."))
    missing_docs = [item["path"] for item in constitutional_sources if not item["present"]]
    if missing_docs:
        findings.append(_finding("POS-ECS003-FINDING-008", "POS-REQ-001", "constitutional source inventory", "MEDIUM", "Expected constitutional references are missing: " + ", ".join(missing_docs), "EVIDENCE_MISSING", "OPEN", "Materialize authoritative source inventory."))
    return findings


def _finding(identifier: str, requirement: str, artifact: str, severity: str, evidence: str, classification: str, disposition: str, recommendation: str) -> dict[str, Any]:
    return {
        "finding_id": identifier,
        "governing_requirement": requirement,
        "affected_artifact": artifact,
        "severity": severity,
        "evidence": evidence,
        "classification": classification,
        "disposition": disposition,
        "remediation_recommendation": recommendation,
    }


def _proofs(requirements: list[dict[str, Any]], findings: list[dict[str, Any]], tests: dict[str, Any]) -> list[dict[str, Any]]:
    findings_by_req: dict[str, list[dict[str, Any]]] = {}
    for finding in findings:
        findings_by_req.setdefault(finding["governing_requirement"], []).append(finding)
    proofs = []
    for req in requirements:
        blockers = findings_by_req.get(req["requirement_id"], [])
        behavior_supported = tests["successful"] and req["requirement_id"] in {"POS-REQ-003", "POS-REQ-006"}
        if blockers:
            disposition = "TRACEABILITY_INCOMPLETE" if req["requirement_id"] in {"POS-REQ-001", "POS-REQ-002", "POS-REQ-008"} else "NOT_PROVEN"
        elif behavior_supported:
            disposition = "PROVEN"
        else:
            disposition = "IMPLEMENTATION_UNVERIFIED"
        proofs.append(
            {
                "proof_id": f"PROOF-{req['requirement_id']}",
                "requirement_id": req["requirement_id"],
                "implementation_obligation": req["requirement_text"],
                "implementation_artifacts": ["src/argos/control_panel/position_registry.py", "src/argos/trader/position_management.py"],
                "verifiers": list(FOCUSED_TEST_MODULES),
                "execution_records": [item["test_identifier"] for item in tests["records"] if item["disposition"] == "PASS"],
                "findings": [item["finding_id"] for item in blockers],
                "disposition": disposition,
                "proof_sufficiency": "SUFFICIENT" if disposition == "PROVEN" else "INSUFFICIENT",
            }
        )
    return proofs


def _run_clean_environment() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="position_registry_ecs003_clean_") as tmp:
        clean_root = Path(tmp) / "repo"
        clean_root.mkdir()
        archive = subprocess.check_output(["git", "archive", "--format=zip", "HEAD"], cwd=REPOSITORY_ROOT)
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            package.extractall(clean_root)
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{clean_root}{os.pathsep}{clean_root / 'src'}{os.pathsep}{clean_root / 'Scripts'}"
        command = [sys.executable, "Scripts/position_registry_ecs003_audit.py", "--no-clean"]
        result = subprocess.run(command, cwd=clean_root, env=env, capture_output=True, text=True, timeout=180)
        return {
            "clean_root_git_metadata_present": (clean_root / ".git").exists(),
            "command": " ".join(command),
            "returncode": result.returncode,
            "succeeded": result.returncode == 0,
            "stdout_tail": result.stdout[-4000:],
            "stderr_tail": result.stderr[-4000:],
            "portable_candidate_digest": _candidate_digest(clean_root),
        }


def run_audit(include_clean: bool = True) -> dict[str, Any]:
    generated_at = utc_timestamp()
    candidate = _candidate_digest()
    constitutional_sources = _constitutional_sources()
    implementation = _implementation_inventory()
    tests = _run_tests()
    requirements = [
        {"requirement_id": req_id, "requirement_text": text, "domain": domain, "canonical_identity": req_id}
        for req_id, text, domain in CANONICAL_REQUIREMENTS
    ]
    findings = _findings(constitutional_sources, tests)
    proofs = _proofs(requirements, findings, tests)
    blocker_ids = [item["finding_id"] for item in findings if item["severity"] in {"CRITICAL", "HIGH"}]
    phase_i = "FAIL" if any(item["classification"] == "CONSTITUTIONAL_BLOCKER" for item in findings) else "UNCONDITIONAL_PASS"
    phase_ii = "FAIL" if any(proof["disposition"] != "PROVEN" for proof in proofs) else "UNCONDITIONAL_PASS"
    clean = _run_clean_environment() if include_clean else {"succeeded": True, "skipped_for_nested_clean_run": True}
    final_verdict = "UNCONDITIONAL_PASS" if phase_i == "UNCONDITIONAL_PASS" and phase_ii == "UNCONDITIONAL_PASS" and clean["succeeded"] and not blocker_ids else "FAIL"
    final_report = {
        "candidate": "POSITION-REGISTRY-ECS003-AUDIT-001",
        "candidate_digest": candidate,
        "generated_at": generated_at,
        "phase_i_verdict": phase_i,
        "phase_ii_verdict": phase_ii,
        "final_ecs003_verdict": final_verdict,
        "certification_blockers": blocker_ids,
        "remediation_recommendation": "multiple bounded work-order series",
        "remediation_basis": "Findings span constitutional authority, ownership, lifecycle/recovery verification, quantity/cost doctrine, temporal doctrine, and proof reproducibility.",
    }
    traceability = {
        "edges": [
            {
                "requirement": proof["requirement_id"],
                "implementation": proof["implementation_artifacts"],
                "verifier": proof["verifiers"],
                "execution": proof["execution_records"],
                "finding": proof["findings"],
                "proof": proof["proof_id"],
                "disposition": proof["disposition"],
            }
            for proof in proofs
        ]
    }
    coverage = {
        "requirements_total": len(requirements),
        "requirements_proven": sum(1 for item in proofs if item["disposition"] == "PROVEN"),
        "requirements_not_proven": sum(1 for item in proofs if item["disposition"] != "PROVEN"),
        "focused_tests_run": tests["tests_run"],
        "focused_tests_passed": tests["status"] == "PASS",
    }
    _write_json(OUTPUT_DIR / "executive_audit_report.json", final_report)
    _write_json(OUTPUT_DIR / "constitutional_audit_report.json", {"phase_i_verdict": phase_i, "sources": constitutional_sources, "findings": findings})
    _write_json(OUTPUT_DIR / "constitutional_finding_registry.json", [item for item in findings if item["classification"].startswith("CONSTITUTIONAL") or item["classification"] in {"OWNERSHIP_AMBIGUITY"}])
    _write_json(OUTPUT_DIR / "canonical_constitutional_requirement_registry.json", requirements)
    _write_json(OUTPUT_DIR / "ownership_and_custody_assessment.json", {"verdict": "FAIL", "finding_ids": ["POS-ECS003-FINDING-002"]})
    _write_json(OUTPUT_DIR / "lifecycle_assessment.json", {"verdict": "PASS_WITH_GAPS", "finding_ids": ["POS-ECS003-FINDING-003"]})
    _write_json(OUTPUT_DIR / "interface_assessment.json", {"verdict": "PARTIAL", "supporting_sources": [item for item in constitutional_sources if item["present"]]})
    _write_json(OUTPUT_DIR / "temporal_assessment.json", {"verdict": "FAIL", "finding_ids": ["POS-ECS003-FINDING-005"]})
    _write_json(OUTPUT_DIR / "reconciliation_assessment.json", {"verdict": "PARTIAL", "finding_ids": []})
    _write_json(OUTPUT_DIR / "evidence_assessment.json", {"verdict": "INSUFFICIENT_FOR_CERTIFICATION", "finding_ids": ["POS-ECS003-FINDING-006"]})
    _write_json(OUTPUT_DIR / "dependency_derived_implementation_inventory.json", implementation)
    _write_json(OUTPUT_DIR / "participation_registry.json", [item for item in implementation if item["classification"] != "NONPARTICIPATING"])
    _write_json(OUTPUT_DIR / "exclusion_registry.json", [])
    _write_json(OUTPUT_DIR / "requirement_to_implementation_matrix.json", proofs)
    _write_json(OUTPUT_DIR / "verifier_inventory.json", {"modules": FOCUSED_TEST_MODULES, "selection": "dependency-derived focused Position Registry behavioral tests"})
    _write_json(OUTPUT_DIR / "behavioral_execution_registry.json", tests)
    _write_json(OUTPUT_DIR / "persistence_and_recovery_report.json", {"verdict": "IMPLEMENTATION_UNVERIFIED", "reason": "No complete actual restart, partial-write, corrupted-state, and recovery verifier population exists."})
    _write_json(OUTPUT_DIR / "execution_evidence_registry.json", tests["records"])
    _write_json(OUTPUT_DIR / "evidence_sufficiency_report.json", {"sufficient": False, "coverage": coverage})
    _write_json(OUTPUT_DIR / "requirement_proof_registry.json", proofs)
    _write_json(OUTPUT_DIR / "proof_coverage_matrix.json", coverage)
    _write_json(OUTPUT_DIR / "proof_reproducibility_report.json", {"reproducible": False, "clean_environment": clean, "reason": "Clean runner executes, but proof population remains certification-blocked."})
    _write_json(OUTPUT_DIR / "execution_derived_traceability_graph.json", traceability)
    _write_json(OUTPUT_DIR / "finding_reconciliation_registry.json", findings)
    _write_json(OUTPUT_DIR / "certification_blocker_registry.json", [item for item in findings if item["finding_id"] in blocker_ids])
    _write_json(OUTPUT_DIR / "clean_environment_reproduction_report.json", clean)
    _write_json(OUTPUT_DIR / "final_ecs003_certification_report.json", final_report)
    _write_json(OUTPUT_DIR / "final_ecs003_verdict.json", {"verdict": final_verdict})
    _write_json(OUTPUT_DIR / "recommended_remediation_structure.json", {"recommendation": "multiple bounded work-order series", "basis": final_report["remediation_basis"]})
    _write_json(OUTPUT_DIR / "completion_report.json", final_report)
    _write_text(OUTPUT_DIR / "README.md", "# Position Registry ECS-003 Audit 001\n\nFinal verdict: " + final_verdict + "\n")
    _write_text(OUTPUT_DIR / "REPRODUCE.md", "Run `python Scripts/position_registry_ecs003_audit.py` from the repository root with `PYTHONPATH=.;src;Scripts`.\n")
    return final_report


def main() -> int:
    include_clean = "--no-clean" not in sys.argv
    report = run_audit(include_clean=include_clean)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
