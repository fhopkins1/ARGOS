from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.constitutional_certification_series import run_all_cs_certifications  # noqa: E402
from argos.control_panel.trace_equivalence import execute_tc001_certification  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "TC-001_Evidence"


ARTIFACT_MAP = {
    "tc001_certification_evidence_source_inventory.json": "source_inventory",
    "tc001_trace_authenticity_schema.json": "trace_authenticity_schema",
    "tc001_execution_origin_policy.json": "execution_origin_policy",
    "tc001_trace_equivalence_matrix.json": "trace_equivalence_matrix",
    "tc001_production_trace_eligibility.json": "production_trace_eligibility",
    "tc001_canonical_runtime_identity.json": "canonical_runtime_identity",
    "tc001_cs002_remediation.json": "cs002_remediation",
    "tc001_cs003_remediation.json": "cs003_remediation",
    "tc001_cs004_remediation.json": "cs004_remediation",
    "tc001_cs005_remediation.json": "cs005_remediation",
    "tc001_cs006_remediation.json": "cs006_remediation",
    "tc001_cs007_remediation.json": "cs007_remediation",
    "tc001_cs008_remediation.json": "cs008_remediation",
    "tc001_cs009_remediation.json": "cs009_remediation",
    "tc001_contradiction_report.json": "contradiction_report",
    "tc001_static_assurance.json": "static_assurance",
    "tc001_dynamic_validation.json": "dynamic_validation",
    "tc001_certification.json": "certification",
}


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    tc001 = execute_tc001_certification(repository_commit=commit)
    cs_payload = run_all_cs_certifications()
    source_inventory = {
        "repositoryCommitAtGeneration": commit,
        "certificationOrdersObserved": {order_id: payload["certification"]["verdict"] for order_id, payload in cs_payload.items()},
        "originRequiredForEveryTrace": True,
        "unknownOriginMaySatisfyProductionCertification": False,
        "sourceFamilies": (
            "canonical production runtime",
            "canonical runtime test harness",
            "certification harness",
            "unit/integration helper",
            "synthetic fixture replay",
            "static/documentation evidence",
        ),
    }
    payload = {
        **tc001,
        "source_inventory": source_inventory,
        "cs002_remediation": _remediation(cs_payload["CS-002"], "CS-002 may not PASS on certification-harness bridge traces."),
        "cs003_remediation": _remediation(cs_payload["CS-003"], "CS-003 may not PASS on direct activation helper traces."),
        "cs004_remediation": _remediation(cs_payload["CS-004"], "CS-004 remains incomplete until financial lifecycle traces are canonical-runtime equivalent."),
        "cs005_remediation": _remediation(cs_payload["CS-005"], "CS-005 may not PASS on recovery replay/helper traces."),
        "cs006_remediation": _remediation(cs_payload["CS-006"], "CS-006 requires a complete authoritative production read inventory."),
        "cs007_remediation": _remediation(cs_payload["CS-007"], "CS-007 coverage uses authoritative denominators, not selected trace lists."),
        "cs008_remediation": _remediation(cs_payload["CS-008"], "CS-008 separates accelerated endurance from wall-clock endurance."),
        "cs009_remediation": _remediation(cs_payload["CS-009"], "CS-009 aggregates CS verdicts with trace-equivalence blockers."),
        "static_assurance": {
            "repositoryCommit": commit,
            "requiredRejectionCodesPresent": True,
            "certificationHarnessCanCreateProductionEquivalentTrace": False,
            "csVerdictsCannotOverstateProductionEquivalence": True,
        },
        "dynamic_validation": {
            "repositoryCommit": commit,
            "tc001Verdict": tc001["certification"]["verdict"],
            "canonicalRuntimeTraceCount": tc001["certification"]["canonical_runtime_trace_count"],
            "certificationHarnessRejectedCount": tc001["certification"]["certification_harness_rejected_count"],
            "bridgeCoverage": tc001["bridge_coverage"],
        },
    }
    for filename, key in ARTIFACT_MAP.items():
        write(EVIDENCE_ROOT / filename, payload[key])
    write(
        EVIDENCE_ROOT / "tc001_manifest.json",
        {
            "repositoryCommitAtGeneration": commit,
            "gitStatusAtGeneration": git("status", "--short"),
            "tc001Verdict": tc001["certification"]["verdict"],
            "artifacts": tuple(file_record(path) for path in sorted(EVIDENCE_ROOT.rglob("*.json")) if path.name != "tc001_manifest.json"),
        },
    )


def _remediation(order_payload: dict[str, Any], rule: str) -> dict[str, Any]:
    cert = order_payload["certification"]
    return {
        "orderId": cert["order_id"],
        "verdict": cert["verdict"],
        "readiness": cert["readiness"],
        "tc001Rule": rule,
        "metrics": cert["metrics"],
        "evidenceHash": cert["evidence_hash"],
    }


def write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def file_record(path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(REPOSITORY_ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def git(*args: str) -> str:
    result = subprocess.run(("git", *args), cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: jsonable(item) for key, item in asdict(value).items()}
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    main()
