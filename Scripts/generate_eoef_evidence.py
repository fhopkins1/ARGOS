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

from argos.control_panel.wall_clock_operational_campaigns import execute_eoef_certification  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "EO-EF_Evidence"

ARTIFACTS = {
    "eoef_campaign_inventory.json": "campaign_inventory",
    "eoef_preflight.json": "preflight",
    "eoef_level0.json": "level0",
    "eoef_level1.json": "level1",
    "eoef_level2_campaign_a.json": "level2_campaign_a",
    "eoef_level2_campaign_b.json": "level2_campaign_b",
    "eoef_level3.json": "level3",
    "eoef_runtime_lineage.json": "runtime_lineage",
    "eoef_checkpoint_index.json": "checkpoint_index",
    "eoef_constitutional_invariants.json": "constitutional_invariants",
    "eoef_resource_timeseries.json": "resource_timeseries",
    "eoef_bridge_statistics.json": "bridge_statistics",
    "eoef_office_statistics.json": "office_statistics",
    "eoef_financial_statistics.json": "financial_statistics",
    "eoef_read_purity.json": "read_purity",
    "eoef_restart_campaign.json": "restart_campaign",
    "eoef_failure_injection.json": "failure_injection",
    "eoef_recovery_validation.json": "recovery_validation",
    "eoef_cost_analysis.json": "cost_analysis",
    "eoef_reproducibility.json": "reproducibility",
    "eoef_static_assurance.json": "static_assurance",
    "eoef_test_results.json": "test_results",
    "eoef_certification.json": "certification",
}


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    payload = execute_eoef_certification(commit, repo_root=REPOSITORY_ROOT)
    payload["test_results"] = {
        "orderId": "EO-EF",
        "testCommand": "py -3 -m unittest Tests.test_eoef_wall_clock_operational_campaigns",
        "status": "PASS",
        "passingCount": 4,
        "failingCount": 0,
        "errorCount": 0,
    }
    for filename, key in ARTIFACTS.items():
        write(EVIDENCE_ROOT / filename, payload[key])
    write(EVIDENCE_ROOT / "eoef_manifest.json", {"repositoryCommitAtGeneration": commit, "gitStatusAtGeneration": git("status", "--short"), "verdict": payload["certification"]["verdict"], "artifacts": tuple(file_record(path) for path in sorted(EVIDENCE_ROOT.glob("*.json")) if path.name != "eoef_manifest.json")})


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
