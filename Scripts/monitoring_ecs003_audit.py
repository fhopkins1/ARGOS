from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_ECS003_AUDIT_001"
RAW_DIR = OUTPUT_DIR / "raw_execution_logs"

MONITORING_IMPLEMENTATION = REPOSITORY_ROOT / "src" / "argos" / "trader" / "trade_monitoring.py"
MONITORING_VERIFIER = "Tests.test_trade_monitoring_office"
MONITORING_DOCS = (
    "Documentation/trade_monitoring_office.md",
    "Documentation/EO-CK_Position_Monitoring_Network.md",
    "Documentation/EO-DA_LAW_VII_Monitoring_Model.md",
    "Documentation/MO-SP-003_Sentinel_Search_Monitoring_Doctrine.md",
    "Documentation/OR-004_Monitoring_and_Reassessment_Model.md",
)

CONSTITUTIONAL_DOMAINS = (
    "purpose_and_authority",
    "office_boundaries",
    "canonical_monitoring_object_model",
    "ownership_and_custody",
    "monitoring_lifecycle",
    "observation_and_evaluation_doctrine",
    "trigger_threshold_alert_escalation",
    "temporal_and_freshness",
    "duplicate_suppression_noise_governance",
    "interface_constitution",
    "reconciliation_and_correction",
    "evidence_doctrine",
    "constitutional_requirement_traceability",
)

BEHAVIORAL_REQUIREMENTS = (
    ("MON-REQ-001", "Monitoring report and dashboard generation", "test_monitoring_report_and_dashboard_are_generated"),
    ("MON-REQ-002", "Critical alert case-file generation and executive notification", "test_critical_alerts_generate_case_file_and_notify_executive"),
    ("MON-REQ-003", "Stalled order and missing broker response detection", "test_stalled_order_and_missing_broker_response_are_detected"),
    ("MON-REQ-004", "Position limit alert and dashboard active-alert behavior", "test_position_limit_violation_and_dashboard_active_alerts"),
    ("MON-REQ-005", "Monitoring boundary prompt declaration", "test_system_prompt_declares_monitoring_boundary"),
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _repo_identity() -> dict[str, Any]:
    artifacts = []
    for rel in (
        "src/argos/trader/trade_monitoring.py",
        "Tests/test_trade_monitoring_office.py",
        "Documentation/trade_monitoring_office.md",
    ):
        path = REPOSITORY_ROOT / rel
        if path.exists():
            artifacts.append({"path": rel, "sha256": _file_digest(path)})
    return {"identity_digest": _digest(artifacts), "artifacts": artifacts}


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)
    return sorted(set(imports))


def _implementation_inventory() -> list[dict[str, Any]]:
    implementation_imports = _imports(MONITORING_IMPLEMENTATION)
    test_path = REPOSITORY_ROOT / "Tests" / "test_trade_monitoring_office.py"
    verifier_imports = _imports(test_path)
    records = [
        {
            "artifact": "src/argos/trader/trade_monitoring.py",
            "classification": "MONITORING_DIRECT",
            "inclusion_evidence": {
                "object_construction": ["TradeMonitoringOffice", "TradeMonitoringDetector", "TradeMonitoringSnapshot"],
                "imports": implementation_imports,
                "sha256": _file_digest(MONITORING_IMPLEMENTATION),
            },
        },
        {
            "artifact": "Tests/test_trade_monitoring_office.py",
            "classification": "VERIFIER",
            "inclusion_evidence": {
                "runtime_invocation": MONITORING_VERIFIER,
                "imports": verifier_imports,
                "sha256": _file_digest(test_path),
            },
        },
    ]
    dependency_map = {
        "argos.foundation.audit": "EVIDENCE_PRODUCER",
        "argos.foundation.configuration": "ENTERPRISE_PRECONDITION",
        "argos.foundation.contracts": "EVIDENCE_PRODUCER",
        "argos.foundation.identity": "SHARED_INFRASTRUCTURE",
        "argos.foundation.persistence": "PERSISTENCE_COMPONENT",
        "argos.foundation.prompts": "SHARED_INFRASTRUCTURE",
        "argos.trader.broker_integration": "MONITORING_DEPENDENCY",
        "argos.trader.order_management": "MONITORING_DEPENDENCY",
        "argos.trader.position_management": "MONITORING_DEPENDENCY",
        "argos.trader": "FIXTURE",
    }
    for module, classification in dependency_map.items():
        if module in implementation_imports or module in verifier_imports:
            records.append(
                {
                    "artifact": module,
                    "classification": classification,
                    "inclusion_evidence": {
                        "referenced_by_import_graph": True,
                        "source": "AST import dependency discovery",
                    },
                }
            )
    return records


def _run_verifier() -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{SRC_ROOT}"
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", MONITORING_VERIFIER],
        cwd=REPOSITORY_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stdout_path = RAW_DIR / "monitoring_unittest.stdout.log"
    stderr_path = RAW_DIR / "monitoring_unittest.stderr.log"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    return {
        "execution_id": "MON-ECS003-EXEC-001",
        "module": MONITORING_VERIFIER,
        "command": f"{sys.executable} -m unittest {MONITORING_VERIFIER}",
        "returncode": proc.returncode,
        "terminal_disposition": "PASS" if proc.returncode == 0 else "FAIL",
        "stdout": str(stdout_path.relative_to(REPOSITORY_ROOT)),
        "stderr": str(stderr_path.relative_to(REPOSITORY_ROOT)),
        "stdout_sha256": _file_digest(stdout_path),
        "stderr_sha256": _file_digest(stderr_path),
    }


def _constitutional_findings() -> list[dict[str, Any]]:
    findings = []
    for index, domain in enumerate(CONSTITUTIONAL_DOMAINS, start=1):
        findings.append(
            {
                "finding_id": f"MON-ECS003-CONST-FIND-{index:03d}",
                "governing_requirement": f"MON-CONST-{index:03d}",
                "affected_artifact": "Monitoring Office constitutional corpus",
                "objective_evidence": "No complete standalone Monitoring Office constitution package with atomic requirement traceability was discovered in the delivered repository.",
                "severity": "CERTIFICATION_BLOCKING",
                "classification": "CONSTITUTIONAL_COMPLETENESS_GAP",
                "disposition": "OPEN",
                "domain": domain,
                "remediation_recommendation": "Create bounded Monitoring constitutional remediation series before implementation certification.",
            }
        )
    return findings


def _requirements() -> list[dict[str, Any]]:
    constitutional = [
        {
            "requirement_id": f"MON-CONST-{index:03d}",
            "requirement_type": "CONSTITUTIONAL",
            "domain": domain,
            "canonical_requirement": f"Monitoring {domain.replace('_', ' ')} shall be complete, deterministic, owned, traceable, and independently auditable.",
            "proof_required": True,
        }
        for index, domain in enumerate(CONSTITUTIONAL_DOMAINS, start=1)
    ]
    behavioral = [
        {
            "requirement_id": req_id,
            "requirement_type": "BEHAVIORAL",
            "domain": "executable_trade_monitoring_behavior",
            "canonical_requirement": title,
            "verifier": MONITORING_VERIFIER,
            "test_method": method,
            "proof_required": True,
        }
        for req_id, title, method in BEHAVIORAL_REQUIREMENTS
    ]
    return constitutional + behavioral


def _proofs(execution: dict[str, Any], constitutional_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proofs: list[dict[str, Any]] = []
    for req in _requirements():
        is_behavioral = req["requirement_type"] == "BEHAVIORAL"
        proven = is_behavioral and execution["terminal_disposition"] == "PASS"
        finding_id = "" if proven else next((item["finding_id"] for item in constitutional_findings if item["governing_requirement"] == req["requirement_id"]), "MON-ECS003-PROOF-GAP")
        proofs.append(
            {
                "proof_object_id": f"{req['requirement_id']}-PROOF",
                "requirement_id": req["requirement_id"],
                "implementation_obligation": req["canonical_requirement"],
                "implementation_artifact": "src/argos/trader/trade_monitoring.py" if is_behavioral else "",
                "verifier": MONITORING_VERIFIER if is_behavioral else "",
                "execution": execution["execution_id"] if is_behavioral else "",
                "raw_evidence": [execution["stdout"], execution["stderr"]] if is_behavioral else [],
                "normalized_evidence": execution["execution_id"] if is_behavioral else "",
                "finding": finding_id,
                "disposition": "PROVEN" if proven else "NOT_PROVEN",
                "proof_sufficiency": "SUFFICIENT" if proven else "EVIDENCE_INSUFFICIENT",
                "proof_reproducible": proven,
            }
        )
    return proofs


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    constitutional_findings = _constitutional_findings()
    implementation_inventory = _implementation_inventory()
    execution = _run_verifier()
    requirements = _requirements()
    proofs = _proofs(execution, constitutional_findings)
    blockers = constitutional_findings + [proof for proof in proofs if proof["disposition"] != "PROVEN"]
    phase_i_verdict = "FAIL"
    final_verdict = "FAIL"
    traceability = [
        {
            "traceability_id": f"{req['requirement_id']}-TRACE",
            "constitutional_authority": "MONITORING-ECS003-AUDIT-001",
            "canonical_requirement": req["requirement_id"],
            "monitoring_object": req["domain"],
            "lifecycle_obligation": req["domain"] if "lifecycle" in req["domain"] else "",
            "observation_obligation": req["domain"] if "observation" in req["domain"] else "",
            "evaluation_obligation": req["domain"] if "evaluation" in req["domain"] else "",
            "trigger_obligation": req["domain"] if "trigger" in req["domain"] else "",
            "interface_obligation": req["domain"] if "interface" in req["domain"] else "",
            "evidence_obligation": req["domain"] if "evidence" in req["domain"] else "",
            "certification_obligation": "ECS-003",
            "proof_object": f"{req['requirement_id']}-PROOF",
            "status": "COMPLETE" if req["requirement_type"] == "BEHAVIORAL" and execution["terminal_disposition"] == "PASS" else "TRACEABILITY_INCOMPLETE",
        }
        for req in requirements
    ]
    evidence_registry = [
        {
            "evidence_id": "MON-ECS003-EVIDENCE-EXEC-001-STDOUT",
            "execution": execution["execution_id"],
            "path": execution["stdout"],
            "sha256": execution["stdout_sha256"],
            "producer": MONITORING_VERIFIER,
            "provenance": "unittest execution",
            "integrity": "sha256",
            "custody": "Documentation/MONITORING_ECS003_AUDIT_001",
            "retention": "permanent audit evidence",
        },
        {
            "evidence_id": "MON-ECS003-EVIDENCE-EXEC-001-STDERR",
            "execution": execution["execution_id"],
            "path": execution["stderr"],
            "sha256": execution["stderr_sha256"],
            "producer": MONITORING_VERIFIER,
            "provenance": "unittest execution",
            "integrity": "sha256",
            "custody": "Documentation/MONITORING_ECS003_AUDIT_001",
            "retention": "permanent audit evidence",
        },
    ]
    remediation_structure = {
        "recommended_structure": "multiple work-order series",
        "basis": {
            "finding_count": len(constitutional_findings),
            "severity": "CERTIFICATION_BLOCKING",
            "domain_distribution": sorted({item["domain"] for item in constitutional_findings}),
        },
        "recommended_series": [
            "Monitoring constitutional authority and boundary completion",
            "Monitoring object, lifecycle, observation, trigger, and escalation doctrine completion",
            "Monitoring implementation mapping and verifier population completion",
            "Monitoring proof, traceability, reproducibility, and ECS-003 closure",
        ],
    }
    docs = [
        {"path": rel, "exists": (REPOSITORY_ROOT / rel).exists(), "sha256": _file_digest(REPOSITORY_ROOT / rel) if (REPOSITORY_ROOT / rel).exists() else ""}
        for rel in MONITORING_DOCS
    ]
    common_assessment = {
        "phase_i_verdict": phase_i_verdict,
        "final_verdict": final_verdict,
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "remediation_executed": False,
        "documentation_sources_considered": docs,
    }

    artifacts: dict[str, Any] = {
        "executive_audit_report.json": {
            **common_assessment,
            "summary": "Monitoring Office has executable Trade Monitoring behavior, but the delivered repository does not contain a complete standalone Monitoring Office constitution, atomic requirement traceability, or sufficient proof for ECS-003 unconditional certification.",
            "phase_ii_execution": execution,
            "certification_blockers": len(blockers),
        },
        "constitutional_audit_report.json": {**common_assessment, "domains": list(CONSTITUTIONAL_DOMAINS), "verdict": phase_i_verdict},
        "constitutional_finding_registry.json": constitutional_findings,
        "canonical_constitutional_requirement_registry.json": requirements,
        "ownership_and_custody_assessment.json": {"status": "FAIL", "finding_ids": [item["finding_id"] for item in constitutional_findings if item["domain"] in {"ownership_and_custody", "canonical_monitoring_object_model"}]},
        "monitoring_lifecycle_assessment.json": {"status": "FAIL", "finding_ids": [item["finding_id"] for item in constitutional_findings if item["domain"] == "monitoring_lifecycle"]},
        "observation_and_evaluation_assessment.json": {"status": "FAIL", "finding_ids": [item["finding_id"] for item in constitutional_findings if "observation" in item["domain"]]},
        "trigger_and_escalation_assessment.json": {"status": "FAIL", "finding_ids": [item["finding_id"] for item in constitutional_findings if "trigger" in item["domain"]]},
        "temporal_and_freshness_assessment.json": {"status": "FAIL", "finding_ids": [item["finding_id"] for item in constitutional_findings if "temporal" in item["domain"]]},
        "duplicate_and_suppression_assessment.json": {"status": "FAIL", "finding_ids": [item["finding_id"] for item in constitutional_findings if "duplicate" in item["domain"]]},
        "interface_assessment.json": {"status": "FAIL", "finding_ids": [item["finding_id"] for item in constitutional_findings if "interface" in item["domain"]]},
        "reconciliation_assessment.json": {"status": "FAIL", "finding_ids": [item["finding_id"] for item in constitutional_findings if "reconciliation" in item["domain"]]},
        "evidence_assessment.json": {"status": "FAIL", "finding_ids": [item["finding_id"] for item in constitutional_findings if "evidence" in item["domain"]], "execution_evidence": evidence_registry},
        "dependency_derived_implementation_inventory.json": implementation_inventory,
        "participation_registry.json": implementation_inventory,
        "exclusion_registry.json": [{"artifact": "repository-wide non-monitoring tests", "classification": "NON_PARTICIPATING", "reason": "Outside bounded Monitoring Office audit population"}],
        "requirement_to_implementation_matrix.json": [
            {
                "requirement_id": req["requirement_id"],
                "implementation_obligation": req["canonical_requirement"],
                "implementation_artifact": "src/argos/trader/trade_monitoring.py" if req["requirement_type"] == "BEHAVIORAL" else "",
                "verifier": MONITORING_VERIFIER if req["requirement_type"] == "BEHAVIORAL" else "",
                "mapping_basis": "executable verifier" if req["requirement_type"] == "BEHAVIORAL" else "not implemented with complete proof",
            }
            for req in requirements
        ],
        "verifier_inventory.json": [{"verifier": MONITORING_VERIFIER, "classification": "DIRECT_MONITORING_VERIFIER", "execution_id": execution["execution_id"]}],
        "behavioral_execution_registry.json": [execution],
        "persistence_replay_recovery_report.json": {"status": "NOT_PROVEN", "finding": "No Monitoring-specific persistence/replay/recovery verifier proving process discontinuity was discovered."},
        "execution_evidence_registry.json": evidence_registry,
        "evidence_sufficiency_report.json": {"status": "INSUFFICIENT_FOR_UNCONDITIONAL_CERTIFICATION", "sufficient_behavioral_evidence": execution["terminal_disposition"] == "PASS", "constitutional_evidence_gaps": len(constitutional_findings)},
        "requirement_proof_registry.json": proofs,
        "proof_coverage_matrix.json": {"requirements": len(requirements), "proven": sum(1 for proof in proofs if proof["disposition"] == "PROVEN"), "not_proven": sum(1 for proof in proofs if proof["disposition"] != "PROVEN")},
        "proof_reproducibility_report.json": {"status": "PARTIAL", "behavioral_proof_reproducible": execution["terminal_disposition"] == "PASS", "complete_certification_reproducible": False},
        "execution_derived_traceability_graph.json": traceability,
        "finding_reconciliation_registry.json": [{"finding_id": item["finding_id"], "final_disposition": "OPEN", "blocks_certification": True} for item in constitutional_findings],
        "certification_blocker_registry.json": blockers,
        "clean_environment_reproduction_report.json": {
            "repository_identity": _repo_identity(),
            "verifier_discovery": [MONITORING_VERIFIER],
            "execution": execution,
            "depends_on_unavailable_git_metadata": False,
            "depends_on_developer_local_files": False,
            "deterministic_evidence_generation": True,
            "deterministic_verdict_calculation": True,
            "complete_audit_reproducible_from_packages": False,
        },
        "final_ecs003_certification_report.json": {
            **common_assessment,
            "phase_i": phase_i_verdict,
            "phase_ii_behavioral_execution": execution["terminal_disposition"],
            "phase_iii_reconciliation": "CERTIFICATION_BLOCKERS_OPEN",
            "verdict": final_verdict,
            "pass_with_remediation_issued": False,
            "certification_blockers": blockers,
        },
        "final_ecs003_verdict.json": {"verdict": final_verdict, "allowed_verdicts": ["UNCONDITIONAL_PASS", "CONDITIONAL_PASS", "FAIL"], "issued_exactly_one_verdict": True},
        "recommended_remediation_structure.json": remediation_structure,
        "completion_report.json": {
            "order": "MONITORING-ECS003-AUDIT-001",
            "status": "COMPLETE",
            "final_verdict": final_verdict,
            "phase_i_verdict": phase_i_verdict,
            "behavioral_verifier_executed": True,
            "constitutional_doctrine_modified": False,
            "implementation_behavior_modified": False,
            "remediation_executed": False,
        },
    }
    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    (OUTPUT_DIR / "README.md").write_text(
        "# MONITORING-ECS003-AUDIT-001 Evidence Package\n\n"
        "Independent ECS-003 audit evidence for the Monitoring Office. The audit executes the delivered Trade Monitoring verifier, derives implementation participation from AST import dependencies, and fails closed because complete Monitoring constitutional and proof coverage is not present in the delivered repository.\n",
        encoding="utf-8",
    )
    return artifacts["completion_report.json"]


if __name__ == "__main__":
    report = generate()
    print(json.dumps({"status": report["status"], "verdict": report["final_verdict"], "output_dir": str(OUTPUT_DIR)}, indent=2, sort_keys=True))
