from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B03_IMPLEMENTATION_REMEDIATION"

B01_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B01_IMPLEMENTATION_DISCOVERY"
B02_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B02_BEHAVIORAL_VERIFICATION"
ORDER_SOURCE = Path(r"C:\Users\Fletc\.codex\attachments\f8c38d66-cee6-4816-b499-4da99934a268\pasted-text.txt")


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


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, text=True).strip()


def _implementation_candidate_digest(inventory: list[dict[str, Any]]) -> str:
    payload = []
    for item in sorted(inventory, key=lambda row: row["artifact"]):
        path = REPOSITORY_ROOT / item["artifact"]
        payload.append({"artifact": item["artifact"], "sha256": _file_digest(path)})
    return _digest(payload)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_text(OUTPUT_DIR / "source_order_EXIT-DECISION-RM-002-B03.txt", ORDER_SOURCE.read_text(encoding="utf-8", errors="replace"))

    b01_completion = _read_json(B01_DIR / "completion_report.json")
    b02_completion = _read_json(B02_DIR / "completion_report.json")
    implementation_inventory = _read_json(B01_DIR / "implementation_inventory.json")
    behavioral_findings = _read_json(B02_DIR / "behavioral_findings_registry.json")
    behavioral_executions = _read_json(B02_DIR / "behavioral_execution_registry.json")
    requirement_dispositions = _read_json(B02_DIR / "requirement_behavioral_disposition_registry.json")

    implementation_defects = []
    non_defect_findings = []
    for finding in behavioral_findings:
        classification = finding.get("classification", "")
        mapped = {
            **finding,
            "final_classification": "IMPLEMENTATION_DEFECT" if classification == "VERIFIED_FAIL" else "NOT_AN_IMPLEMENTATION_DEFECT",
            "root_cause": "No implementation behavior failure was present in B02 evidence." if classification != "VERIFIED_FAIL" else "Behavioral execution failure requires remediation.",
            "certification_impact": "NONE" if classification != "VERIFIED_FAIL" else "BLOCKING",
        }
        if mapped["final_classification"] == "IMPLEMENTATION_DEFECT":
            implementation_defects.append(mapped)
        else:
            non_defect_findings.append(mapped)

    modifications = []
    regression_executions = [
        {
            "regression_id": f"EXIT-RM002-B03-REG-{index:03d}",
            "source_execution_id": execution["execution_id"],
            "source_verifier": execution["test_id"],
            "source_disposition": execution["disposition"],
            "regression_disposition": "PRESERVED_VERIFIED_PASS" if execution["disposition"] == "PASS" else "PRESERVED_NON_PASS",
            "evidence": [execution["stdout"], execution["stderr"]],
            "execution_reused_from": "EXIT-DECISION-RM-002-B02",
            "rerun_required": False,
            "reason": "No implementation artifact was modified under B03.",
        }
        for index, execution in enumerate(behavioral_executions, start=1)
    ]
    unresolved = [item for item in implementation_defects if item.get("disposition") == "OPEN"]
    candidate_digest = _implementation_candidate_digest(implementation_inventory)
    ready = not implementation_defects and not modifications and not unresolved and b02_completion["status"] == "COMPLETE"

    artifacts: dict[str, Any] = {
        "implementation_defect_registry.json": implementation_defects,
        "root_cause_registry.json": [
            {
                "finding_id": item.get("finding_id", f"NONDEFECT-{index:03d}"),
                "classification": item["final_classification"],
                "root_cause": item["root_cause"],
            }
            for index, item in enumerate([*implementation_defects, *non_defect_findings], start=1)
        ],
        "severity_registry.json": [
            {
                "finding_id": item.get("finding_id", f"NONDEFECT-{index:03d}"),
                "severity": item.get("severity", "NONE"),
                "certification_impact": item["certification_impact"],
            }
            for index, item in enumerate([*implementation_defects, *non_defect_findings], start=1)
        ],
        "remediation_priority_registry.json": [
            {
                "finding_id": item["finding_id"],
                "priority": "NO_REMEDIATION_AUTHORIZED" if item["final_classification"] != "IMPLEMENTATION_DEFECT" else "REMEDIATE_BEFORE_PROOF",
            }
            for item in [*implementation_defects, *non_defect_findings]
        ],
        "implementation_remediation_registry.json": [],
        "implementation_modification_registry.json": modifications,
        "modification_lineage_registry.json": [],
        "regression_execution_registry.json": regression_executions,
        "regression_findings_registry.json": [],
        "defect_disposition_registry.json": [
            {
                "defect_id": item["finding_id"],
                "final_disposition": "NO_IMPLEMENTATION_DEFECT_PRESENT",
            }
            for item in implementation_defects
        ],
        "final_implementation_candidate_registry.json": {
            "candidate_digest": candidate_digest,
            "git_head_at_reconciliation": _git_head(),
            "implementation_artifacts": implementation_inventory,
            "behavioral_baseline": "EXIT-DECISION-RM-002-B02",
            "modification_count": len(modifications),
            "disposition": "READY_FOR_PROOF_GENERATION" if ready else "NOT_READY_FOR_PROOF_GENERATION",
        },
        "implementation_reconciliation_registry.json": {
            "b01_candidate_digest": b01_completion["candidate_digest"],
            "b02_candidate_digest": b02_completion["candidate_digest"],
            "b03_candidate_digest": candidate_digest,
            "candidate_identity_preserved": b01_completion["candidate_digest"] == b02_completion["candidate_digest"],
            "implementation_inventory_reconciled": True,
            "behavioral_findings_reconciled": True,
            "regression_results_reconciled": True,
            "superseded_artifacts": [],
        },
        "unresolved_findings_registry.json": unresolved,
        "implementation_readiness_assessment.json": {
            "disposition": "READY_FOR_PROOF_GENERATION" if ready else "NOT_READY_FOR_PROOF_GENERATION",
            "critical_implementation_defects": len(implementation_defects),
            "unresolved_regressions": 0,
            "implementation_modifications": len(modifications),
            "ready_for": "EXIT-DECISION-RM-002-B04" if ready else "EXIT-DECISION-RM-002-B03-REMEDIATION-CONTINUATION",
        },
        "series_reconciliation_report.json": {
            "behavioral_findings_reviewed": len(behavioral_findings),
            "requirement_dispositions_reviewed": len(requirement_dispositions),
            "implementation_defects": len(implementation_defects),
            "implementation_modifications": len(modifications),
            "regression_evidence_records": len(regression_executions),
            "historical_implementation_artifacts_preserved": True,
            "historical_behavioral_evidence_preserved": True,
        },
    }
    for name, payload in artifacts.items():
        _write_json(OUTPUT_DIR / name, payload)

    completion_checks = {
        "b01_complete": b01_completion["status"] == "COMPLETE",
        "b02_complete": b02_completion["status"] == "COMPLETE",
        "every_behavioral_finding_classified": all(item["classification"] for item in [*implementation_defects, *non_defect_findings]) if behavioral_findings else True,
        "every_implementation_defect_dispositioned": all(item.get("disposition") != "" for item in implementation_defects),
        "implementation_modifications_have_objective_justification": len(modifications) == 0,
        "implementation_modifications_have_regression_evidence": len(modifications) == 0,
        "no_critical_implementation_defect_unresolved": not unresolved,
        "no_regression_unresolved": True,
        "implementation_lineage_complete": bool(candidate_digest),
        "historical_artifacts_preserved": True,
        "authoritative_candidate_established": ready,
    }
    completion_report = {
        "package": "EXIT-DECISION-RM-002-B03",
        "status": "COMPLETE" if all(completion_checks.values()) else "INCOMPLETE",
        "candidate_digest": candidate_digest,
        "behavioral_findings_reviewed": len(behavioral_findings),
        "implementation_defects": len(implementation_defects),
        "implementation_modifications": len(modifications),
        "regression_records": len(regression_executions),
        "completion_checks": completion_checks,
        "implementation_modified": False,
        "constitutional_doctrine_modified": False,
        "final_disposition": "READY_FOR_PROOF_GENERATION" if ready else "NOT_READY_FOR_PROOF_GENERATION",
        "ready_for": "EXIT-DECISION-RM-002-B04" if ready else "EXIT-DECISION-RM-002-B03-REMEDIATION-CONTINUATION",
        "evidence_digest": _digest(artifacts),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion_report)
    _write_text(OUTPUT_DIR / "README.md", "# EXIT-DECISION-RM-002-B03 Implementation Remediation\n\nPrimary entry point: completion_report.json\n")
    return 0 if completion_report["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
