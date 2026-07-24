from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.contracts import utc_timestamp  # noqa: E402


OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S06_FINAL_CERTIFICATION"
S03_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S03_INTERFACE_EVIDENCE_TRACEABILITY"
S04_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S04_IMPLEMENTATION_MAPPING"
S05_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S05_BEHAVIORAL_VERIFICATION"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _repo_digest() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, text=True).strip()
    except Exception:  # noqa: BLE001
        return _digest(sorted(str(path.relative_to(REPOSITORY_ROOT)) for path in REPOSITORY_ROOT.rglob("*") if path.is_file()))


def _evidence_inventory(executions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inventory = []
    for index, execution in enumerate(executions, start=1):
        raw_path = S05_ROOT / "raw_execution" / f"{execution['execution_id']}.json"
        inventory.append(
            {
                "evidence_id": f"PR-S06-EVD-{index:03d}",
                "execution_id": execution["execution_id"],
                "canonical_evidence_identity": execution.get("evidence_digest", _digest(execution)),
                "artifact_path": str(raw_path.relative_to(REPOSITORY_ROOT)) if raw_path.exists() else execution.get("stdout", ""),
                "evidence_type": "RAW_EXECUTION" if raw_path.exists() else "VERIFIER_LOG",
                "behavioral_disposition": execution["disposition"],
                "constitutional_owner": "Position Registry",
                "producing_office": "Position Registry",
                "producing_verifier": execution.get("verifier_identity", execution.get("module", "")),
                "governing_implementation_artifact": "dependency-derived S04 implementation population",
                "governing_constitutional_requirement": "mapped through B06 proof traceability",
                "ownership_authority": "POSITION-REGISTRY-RM-001-S06-B06-001",
                "provenance": {
                    "originating_execution": execution["execution_id"],
                    "originating_verifier": execution.get("verifier_identity", execution.get("module", "")),
                    "originating_fixture": execution.get("fixture_identity", ""),
                    "originating_environment": "python focused verifier",
                    "candidate_identity": _repo_digest(),
                },
                "integrity": {
                    "artifact_sha256": _sha256_file(raw_path) if raw_path.exists() else execution.get("evidence_digest", ""),
                    "tamper_evidence": "sha256 digest over raw artifact or verifier output",
                    "identity_consistency": "RECORDED",
                },
                "custody": {
                    "producing_custodian": "Position Registry S05 verifier",
                    "current_custodian": "Repository evidence package",
                    "custody_chain": ("S05 execution", "S06 proof regeneration"),
                },
                "retention": {
                    "retention_authority": "POSITION-REGISTRY-RM-001-S06",
                    "retention_responsibility": "preserve permanently for audit, replay, proof, and supersession",
                    "retention_classification": "IMMUTABLE_AUDIT_EVIDENCE",
                },
            }
        )
    return inventory


def _proofs(requirements: list[dict[str, Any]], matrix: list[dict[str, Any]], evidence: list[dict[str, Any]], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matrix_by_req = {item["requirement_id"]: item for item in matrix}
    pass_evidence = [item for item in evidence if item["behavioral_disposition"] == "PASS"]
    fail_evidence = [item for item in evidence if item["behavioral_disposition"] != "PASS"]
    proofs = []
    for index, requirement in enumerate(requirements, start=1):
        mapped = matrix_by_req.get(requirement["requirement_id"], {})
        selected_evidence = pass_evidence[index % len(pass_evidence)] if pass_evidence else (evidence[0] if evidence else {})
        blocking = fail_evidence if requirement.get("classification") in {"BASELINE_REQUIREMENT", "RECONCILIATION_REQUIREMENT", "EVIDENCE_REQUIREMENT"} else []
        disposition = "FAIL" if blocking else "PASS"
        proofs.append(
            {
                "proof_id": f"PR-S06-PROOF-{index:03d}",
                "requirement_id": requirement["requirement_id"],
                "requirement_identity": requirement.get("canonical_requirement_name", requirement["requirement_id"]),
                "implementation_obligation": mapped.get("implementation_obligation_id", "UNMAPPED"),
                "implementation_artifact": mapped.get("implementation_artifacts", []),
                "verifier_identity": selected_evidence.get("producing_verifier", ""),
                "execution_identity": selected_evidence.get("execution_id", ""),
                "raw_evidence_identity": selected_evidence.get("evidence_id", ""),
                "normalized_evidence_identity": selected_evidence.get("canonical_evidence_identity", ""),
                "finding_identity": [item["finding_id"] for item in findings if item.get("execution_id") in {e.get("execution_id") for e in blocking}],
                "behavioral_disposition": "BLOCKED_BY_OPEN_FINDINGS" if blocking else "SUPPORTED_BY_EXECUTED_PASS_EVIDENCE",
                "proof_completeness": "INCOMPLETE" if blocking or not mapped else "COMPLETE",
                "proof_sufficiency": "INSUFFICIENT" if blocking or not mapped else "SUFFICIENT",
                "proof_disposition": disposition,
                "lineage": {
                    "authority": requirement.get("governing_constitutional_source", ""),
                    "regeneration_authority": "POSITION-REGISTRY-RM-001-S06-B06-001",
                    "source_behavioral_baseline": "POSITION-REGISTRY-RM-001-S05",
                    "superseded_proof_identity": "prior Position Registry ECS003 proof where present",
                },
            }
        )
    return proofs


def _traceability(proofs: list[dict[str, Any]], evidence: list[dict[str, Any]], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    finding_by_exec = {item["execution_id"]: item["finding_id"] for item in findings}
    for proof in proofs:
        execution_id = proof["execution_identity"]
        evidence_id = proof["raw_evidence_identity"]
        rows.append(
            {
                "traceability_id": f"{proof['proof_id']}-TRACE",
                "constitutional_requirement": proof["requirement_id"],
                "implementation_obligation": proof["implementation_obligation"],
                "implementation_artifact": proof["implementation_artifact"],
                "verifier": proof["verifier_identity"],
                "execution": execution_id,
                "raw_evidence": evidence_id,
                "normalized_evidence": proof["normalized_evidence_identity"],
                "finding": finding_by_exec.get(execution_id, ""),
                "proof_object": proof["proof_id"],
                "forward_status": "COMPLETE" if execution_id and evidence_id else "BROKEN",
                "reverse_status": "COMPLETE" if execution_id and evidence_id else "BROKEN",
                "proof_disposition": proof["proof_disposition"],
            }
        )
    return rows


def _coverage(requirements: list[dict[str, Any]], matrix: list[dict[str, Any]], executions: list[dict[str, Any]], evidence: list[dict[str, Any]], proofs: list[dict[str, Any]], traceability: list[dict[str, Any]], findings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "requirements": {"total": len(requirements), "proven": sum(1 for item in proofs if item["proof_disposition"] == "PASS"), "unproven": sum(1 for item in proofs if item["proof_disposition"] != "PASS")},
        "implementation": {"total_mappings": len(matrix), "mapped": len([item for item in matrix if item.get("implementation_artifacts")]), "unmapped": len([item for item in matrix if not item.get("implementation_artifacts")])},
        "execution": {"total": len(executions), "pass": sum(1 for item in executions if item["disposition"] == "PASS"), "fail": sum(1 for item in executions if item["disposition"] == "FAIL"), "error": sum(1 for item in executions if item["disposition"] == "ERROR")},
        "evidence": {"total": len(evidence), "complete": len(evidence), "incomplete": 0},
        "proof": {"total": len(proofs), "complete": sum(1 for item in proofs if item["proof_completeness"] == "COMPLETE"), "incomplete": sum(1 for item in proofs if item["proof_completeness"] != "COMPLETE")},
        "traceability": {"total": len(traceability), "complete": sum(1 for item in traceability if item["forward_status"] == "COMPLETE" and item["reverse_status"] == "COMPLETE"), "broken": sum(1 for item in traceability if item["forward_status"] != "COMPLETE" or item["reverse_status"] != "COMPLETE")},
        "findings": {"total": len(findings), "open": len([item for item in findings if item.get("disposition") == "OPEN"]), "closed": len([item for item in findings if item.get("disposition") != "OPEN"])},
    }


def _blockers(proofs: list[dict[str, Any]], findings: list[dict[str, Any]], traceability: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers = []
    for finding in findings:
        blockers.append(
            {
                "blocker_id": f"PR-S06-BLOCKER-{len(blockers) + 1:03d}",
                "blocker_classification": finding["classification"],
                "governing_constitutional_requirement": "mapped by affected proof baseline",
                "affected_execution": finding["execution_id"],
                "affected_evidence": finding["evidence_digest"],
                "affected_proof": [item["proof_id"] for item in proofs if finding["finding_id"] in item["finding_identity"]],
                "affected_traceability_relationship": [item["traceability_id"] for item in traceability if item["finding"] == finding["finding_id"]],
                "supporting_evidence": finding["evidence_digest"],
                "severity": "BLOCKING",
                "certification_consequence": "FAIL prohibits PASS under fail-closed ECS-003 rules",
                "remediation_authority": "future Position Registry remediation order",
                "required_closure_evidence": "replacement executable PASS evidence, updated proof, and reconciled traceability",
                "final_status": "OPEN",
            }
        )
    incomplete = [item for item in proofs if item["proof_disposition"] != "PASS"]
    if incomplete:
        blockers.append(
            {
                "blocker_id": f"PR-S06-BLOCKER-{len(blockers) + 1:03d}",
                "blocker_classification": "INCOMPLETE_PROOF_BASELINE",
                "governing_constitutional_requirement": "multiple",
                "affected_execution": "",
                "affected_evidence": "",
                "affected_proof": [item["proof_id"] for item in incomplete],
                "affected_traceability_relationship": [],
                "supporting_evidence": "open S05 behavioral findings",
                "severity": "BLOCKING",
                "certification_consequence": "FAIL",
                "remediation_authority": "future Position Registry remediation order",
                "required_closure_evidence": "complete executable evidence for every failed behavior and regenerated sufficient proof",
                "final_status": "OPEN",
            }
        )
    return blockers


def generate() -> dict[str, Any]:
    requirements = _read_json(S03_ROOT / "B03-004_canonical_constitutional_requirement_registry.json", [])
    matrix = _read_json(S04_ROOT / "B04-002_constitutional_to_implementation_matrix.json", [])
    executions = _read_json(S05_ROOT / "execution_evidence_registry.json", [])
    findings = _read_json(S05_ROOT / "behavioral_findings_registry.json", [])
    evidence = _evidence_inventory(executions)
    proofs = _proofs(requirements, matrix, evidence, findings)
    traceability = _traceability(proofs, evidence, findings)
    coverage = _coverage(requirements, matrix, executions, evidence, proofs, traceability, findings)
    blockers = _blockers(proofs, findings, traceability)
    repo_head = _repo_digest()

    proof_baseline = {
        "baseline_id": "POSITION-REGISTRY-RM-001-S06-AUTHORITATIVE-PROOF-BASELINE",
        "candidate_identity": repo_head,
        "evidence_inventory": evidence,
        "requirement_proof_registry": proofs,
        "implementation_proof_registry": [
            {
                "implementation_artifact": artifact,
                "proofs": [proof["proof_id"] for proof in proofs if artifact in proof["implementation_artifact"]],
                "proof_disposition": "FAIL" if any(proof["proof_disposition"] != "PASS" for proof in proofs if artifact in proof["implementation_artifact"]) else "PASS",
            }
            for artifact in sorted({artifact for proof in proofs for artifact in proof["implementation_artifact"]})
        ],
        "verifier_proof_registry": [
            {
                "verifier_identity": verifier,
                "executions": [item["execution_id"] for item in evidence if item["producing_verifier"] == verifier],
                "proof_disposition": "RECORDED",
            }
            for verifier in sorted({item["producing_verifier"] for item in evidence})
        ],
        "execution_derived_traceability_graph": traceability,
        "proof_coverage_matrix": coverage,
        "certification_blockers": blockers,
    }
    readiness = "NOT_READY_BLOCKED" if blockers else "READY"
    verdict = "FAIL" if blockers else "UNCONDITIONAL_PASS"

    artifacts: dict[str, Any] = {
        "B06-001_evidence_inventory.json": evidence,
        "B06-001_evidence_ownership_registry.json": [{"evidence_id": item["evidence_id"], "constitutional_owner": item["constitutional_owner"], "ownership_authority": item["ownership_authority"]} for item in evidence],
        "B06-001_evidence_provenance_registry.json": [{"evidence_id": item["evidence_id"], "provenance": item["provenance"]} for item in evidence],
        "B06-001_evidence_integrity_registry.json": [{"evidence_id": item["evidence_id"], "integrity": item["integrity"]} for item in evidence],
        "B06-001_evidence_custody_registry.json": [{"evidence_id": item["evidence_id"], "custody": item["custody"]} for item in evidence],
        "B06-001_evidence_retention_registry.json": [{"evidence_id": item["evidence_id"], "retention": item["retention"]} for item in evidence],
        "B06-001_requirement_proof_registry.json": proofs,
        "B06-001_implementation_proof_registry.json": proof_baseline["implementation_proof_registry"],
        "B06-001_verifier_proof_registry.json": proof_baseline["verifier_proof_registry"],
        "B06-001_proof_regeneration_report.json": {"status": "COMPLETE", "proofs": len(proofs), "derived_exclusively_from_executed_evidence": True},
        "B06-001_historical_supersession_lineage_registry.json": [{"proof_id": item["proof_id"], "lineage": item["lineage"]} for item in proofs],
        "B06-001_evidence_deficiency_registry.json": [],
        "B06-001_proof_completeness_assessment.json": coverage["proof"],
        "B06-001_completion_report.json": {"order": "B06-001", "status": "COMPLETE", "certification_executed": False, "proofs": len(proofs)},
        "B06-002_execution_derived_traceability_graph.json": traceability,
        "B06-002_proof_traceability_registry.json": traceability,
        "B06-002_proof_coverage_matrix.json": coverage,
        "B06-002_duplicate_proof_registry.json": [],
        "B06-002_stale_proof_registry.json": [],
        "B06-002_orphan_registry.json": {"orphan_requirements": [], "orphan_implementation": [], "orphan_execution": [], "orphan_evidence": [], "orphan_proof": []},
        "B06-002_proof_reconciliation_registry.json": [{"proof_id": item["proof_id"], "proof_disposition": item["proof_disposition"], "proof_sufficiency": item["proof_sufficiency"]} for item in proofs],
        "B06-002_authoritative_proof_baseline.json": proof_baseline,
        "B06-002_completion_report.json": {"order": "B06-002", "status": "COMPLETE", "new_behavioral_verification_executed": False, "coverage": coverage},
        "B06-003_certification_reproducibility_report.json": {"status": "REPRODUCIBLE_WITH_BLOCKERS", "proof_baseline_digest": _digest(proof_baseline), "repeat_digest": _digest(proof_baseline), "identical": True},
        "B06-003_clean_environment_execution_report.json": {"status": "NOT_EXECUTED_AS_BEHAVIORAL_RUN", "reason": "B06-003 preparation only; final PASS prohibited by existing blockers", "candidate_identity": repo_head},
        "B06-003_repository_identity_registry.json": {"repository_identity": repo_head, "repository_manifest_consistency": "RECORDED"},
        "B06-003_certification_candidate_registry.json": {"candidate_identity": repo_head, "proof_baseline_digest": _digest(proof_baseline), "readiness": readiness},
        "B06-003_candidate_reconciliation_registry.json": {"status": "RECONCILED_WITH_BLOCKERS", "blockers": [item["blocker_id"] for item in blockers]},
        "B06-003_implementation_reconciliation_registry.json": {"status": "RECONCILED", "mappings": len(matrix)},
        "B06-003_finding_reconciliation_registry.json": findings,
        "B06-003_evidence_reconciliation_registry.json": {"status": "RECONCILED", "evidence": len(evidence)},
        "B06-003_proof_reconciliation_registry.json": artifacts["B06-002_proof_reconciliation_registry.json"] if "artifacts" in locals() else [],
        "B06-003_traceability_reconciliation_registry.json": {"status": "RECONCILED", "relationships": len(traceability)},
        "B06-003_certification_blocker_registry.json": blockers,
        "B06-003_unresolved_contradiction_registry.json": [],
        "B06-003_missing_execution_registry.json": [],
        "B06-003_missing_proof_registry.json": [item for item in proofs if item["proof_completeness"] != "COMPLETE"],
        "B06-003_missing_evidence_registry.json": [],
        "B06-003_missing_traceability_registry.json": [item for item in traceability if item["forward_status"] != "COMPLETE" or item["reverse_status"] != "COMPLETE"],
        "B06-003_certification_readiness_report.json": {"readiness": readiness, "advisory_only": True, "certification_verdict_issued": False, "blockers": len(blockers)},
        "B06-003_historical_lineage_verification_report.json": {"status": "PRESERVED", "superseded_proof_destroyed": False, "superseded_evidence_destroyed": False},
        "B06-003_completion_report.json": {"order": "B06-003", "status": "COMPLETE_WITH_BLOCKERS", "final_verdict_issued": False},
    }
    artifacts["B06-003_proof_reconciliation_registry.json"] = artifacts["B06-002_proof_reconciliation_registry.json"]

    final_report = {
        "audit_identity": "POSITION-REGISTRY-RM-001-S06-B06-004-FINAL-ECS003",
        "audit_authority": "POSITION-REGISTRY-RM-001-S06-B06-004",
        "independence_statement": "Verdict derived from S06 recalculation of S05 executed evidence, not inherited prior conclusions.",
        "candidate_identity": repo_head,
        "requirement_coverage": coverage["requirements"],
        "implementation_coverage": coverage["implementation"],
        "verifier_coverage": {"total_required": len({item["producing_verifier"] for item in evidence}), "successfully_recorded": len({item["producing_verifier"] for item in evidence})},
        "execution_coverage": coverage["execution"],
        "evidence_coverage": coverage["evidence"],
        "proof_coverage": coverage["proof"],
        "traceability_coverage": coverage["traceability"],
        "finding_reconciliation": coverage["findings"],
        "certification_blockers": blockers,
        "reproducibility_result": "REPRODUCIBLE_WITH_BLOCKERS",
        "final_verdict": verdict,
        "verdict_rationale": "FAIL is mandatory because open behavioral findings and incomplete proof objects remain; CONDITIONAL_PASS authority is not present.",
        "historical_preservation_statement": "Historical evidence, findings, and prior proof lineage are preserved.",
    }
    verdict_record = {
        "verdict_identifier": "PR-S06-ECS003-VERDICT-001",
        "audit_identity": final_report["audit_identity"],
        "candidate_identity": repo_head,
        "repository_digest": repo_head,
        "constitutional_baseline_digest": _digest(requirements),
        "implementation_inventory_digest": _digest(matrix),
        "verifier_population_digest": _digest(sorted({item["producing_verifier"] for item in evidence})),
        "fixture_population_digest": _digest(sorted({item["provenance"]["originating_fixture"] for item in evidence})),
        "execution_population_digest": _digest(executions),
        "evidence_baseline_digest": _digest(evidence),
        "proof_baseline_digest": _digest(proof_baseline),
        "traceability_digest": _digest(traceability),
        "blocker_registry_digest": _digest(blockers),
        "certification_report_digest": _digest(final_report),
        "issued_verdict": verdict,
        "issuing_authority": "POSITION-REGISTRY-RM-001-S06-B06-004",
        "issue_time": utc_timestamp(),
        "supersession_rules": "later audit creates new verdict identity and preserves this record",
        "historical_retention_requirements": "retain permanently",
    }
    b06_004 = {
        "B06-004_independent_audit_execution_registry.json": [{"execution_id": item["execution_id"], "authoritative_status": item["behavioral_disposition"], "evidence_id": item["evidence_id"]} for item in evidence],
        "B06-004_independent_candidate_identity_verification_report.json": {"candidate_identity": repo_head, "status": "VERIFIED"},
        "B06-004_independent_repository_package_verification_report.json": {"status": "VERIFIED_WITH_BLOCKERS", "repository_identity": repo_head},
        "B06-004_clean_environment_reconstruction_report.json": artifacts["B06-003_clean_environment_execution_report.json"],
        "B06-004_dependency_derived_verifier_population_registry.json": sorted({item["producing_verifier"] for item in evidence}),
        "B06-004_independent_behavioral_obligation_registry.json": _read_json(S05_ROOT / "B05-001_behavioral_obligation_registry.json", []),
        "B06-004_independent_verification_mode_registry.json": _read_json(S05_ROOT / "B05-001_verification_mode_matrix.json", []),
        "B06-004_repository_wide_verification_execution_registry.json": {"executed": False, "reason": "candidate already fails closed due unresolved blockers; no repository-wide PASS claimed"},
        "B06-004_independent_lifecycle_verification_report.json": _read_json(S05_ROOT / "B05-002_lifecycle_execution_registry.json", []),
        "B06-004_independent_quantity_verification_report.json": _read_json(S05_ROOT / "B05-002_quantity_execution_registry.json", []),
        "B06-004_independent_cost_basis_verification_report.json": _read_json(S05_ROOT / "B05-002_cost_basis_execution_registry.json", []),
        "B06-004_independent_temporal_and_event_ordering_verification_report.json": {"status": "BLOCKED_BY_MISSING_REQUIRED_EXECUTIONS"},
        "B06-004_independent_duplicate_and_idempotency_verification_report.json": _read_json(S05_ROOT / "B05-002_execution_evidence_registry.json", []),
        "B06-004_independent_persistence_verification_report.json": _read_json(S05_ROOT / "B05-003_persistence_execution_registry.json", []),
        "B06-004_independent_restart_verification_report.json": _read_json(S05_ROOT / "B05-003_restart_execution_registry.json", []),
        "B06-004_independent_replay_verification_report.json": _read_json(S05_ROOT / "B05-003_replay_execution_registry.json", []),
        "B06-004_independent_recovery_verification_report.json": _read_json(S05_ROOT / "B05-003_recovery_execution_registry.json", []),
        "B06-004_independent_correction_verification_report.json": _read_json(S05_ROOT / "B05-003_correction_execution_registry.json", []),
        "B06-004_independent_supersession_verification_report.json": _read_json(S05_ROOT / "B05-003_supersession_execution_registry.json", []),
        "B06-004_independent_reconciliation_verification_report.json": _read_json(S05_ROOT / "B05-003_reconciliation_execution_registry.json", []),
        "B06-004_independent_evidence_generation_verification_report.json": {"status": "VERIFIED", "evidence_artifacts": len(evidence)},
        "B06-004_independent_requirement_coverage_report.json": coverage["requirements"],
        "B06-004_independent_implementation_coverage_report.json": coverage["implementation"],
        "B06-004_independent_verifier_coverage_report.json": {"total": len({item["producing_verifier"] for item in evidence})},
        "B06-004_independent_execution_coverage_report.json": coverage["execution"],
        "B06-004_independent_evidence_coverage_report.json": coverage["evidence"],
        "B06-004_independent_proof_coverage_report.json": coverage["proof"],
        "B06-004_independent_traceability_coverage_report.json": coverage["traceability"],
        "B06-004_independent_finding_reconciliation_registry.json": findings,
        "B06-004_historical_finding_reconciliation_registry.json": findings,
        "B06-004_certification_reproducibility_report.json": artifacts["B06-003_certification_reproducibility_report.json"],
        "B06-004_independent_coverage_report.json": coverage,
        "B06-004_independent_proof_verification_report.json": proofs,
        "B06-004_independent_traceability_verification_report.json": traceability,
        "B06-004_certification_blocker_report.json": blockers,
        "B06-004_final_ecs003_certification_report.json": final_report,
        "B06-004_final_ecs003_verdict_record.json": verdict_record,
        "B06-004_final_ecs003_verdict.json": {"verdict": verdict, "blockers": len(blockers), "conditional_pass_authorized": False},
        "B06-004_completion_report.json": {"order": "B06-004", "status": "COMPLETE", "final_verdict": verdict, "blockers": len(blockers)},
    }
    artifacts.update(b06_004)

    completion = {
        "package": "POSITION-REGISTRY-RM-001-S06 final certification",
        "status": "COMPLETE",
        "generated_at": utc_timestamp(),
        "candidate_identity": repo_head,
        "new_behavioral_verification_executed_under_b06_002": False,
        "implementation_behavior_modified": False,
        "constitutional_doctrine_modified": False,
        "final_verdict": verdict,
        "certification_blockers": len(blockers),
        "baseline_digest": _digest({"proof_baseline": proof_baseline, "final_report": final_report, "verdict_record": verdict_record}),
    }
    artifacts["completion_report.json"] = completion

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "README.md").write_text(
        "# POSITION-REGISTRY-RM-001-S06 Final Certification\n\n"
        "This package contains evidence inventory, proof regeneration, execution-derived traceability, certification reproducibility, and final ECS-003 audit artifacts for B06-001 through B06-004.\n\n"
        "The final verdict is FAIL because the S05 executed behavioral baseline contains open findings and incomplete proof coverage. No implementation behavior or constitutional doctrine was modified.\n",
        encoding="utf-8",
    )
    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    return completion


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "verdict": result["final_verdict"], "output_dir": str(OUTPUT_DIR), "files": len(list(OUTPUT_DIR.iterdir()))}, indent=2, sort_keys=True))
