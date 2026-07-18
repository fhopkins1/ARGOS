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

from argos.control_panel.constitutional_trace_campaign import ExecutedConstitutionalTraceCampaign  # noqa: E402
from argos.control_panel.continuous_paper_endurance import ContinuousPaperEnduranceAuthority  # noqa: E402
from argos.control_panel.financial_recovery_authority import FinancialRecoveryAuthority  # noqa: E402
from argos.control_panel.full_position_lifecycle_runtime import execute_canonical_position_lifecycle  # noqa: E402
from argos.control_panel.independent_constitutional_certification import IndependentConstitutionalCertificationAuthority  # noqa: E402
from argos.control_panel.production_read_surface_registry import ProductionReadSurfaceConstitutionalRegistry  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "EO-DM_to_EO-DR_Evidence"


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD") or "WORKTREE"

    lifecycle = execute_canonical_position_lifecycle()
    recovery = FinancialRecoveryAuthority().recover_missing_close_fill(lifecycle)
    reads = ProductionReadSurfaceConstitutionalRegistry().certify()
    endurance = ContinuousPaperEnduranceAuthority().run_accelerated_certification(repository_commit=commit)
    trace = ExecutedConstitutionalTraceCampaign().execute(repository_commit=commit)

    write("eo_dm_lifecycle_closure.json", lifecycle["report"])
    write("eo_dn_recovery_report.json", asdict(recovery))
    write("eo_do_read_surface_certification.json", asdict(reads))
    write("eo_dp_trace_campaign.json", trace["report"])
    write("eo_dq_endurance_certification.json", asdict(endurance))

    certification = IndependentConstitutionalCertificationAuthority().certify(EVIDENCE_ROOT, repository_root=REPOSITORY_ROOT)
    write("eo_dr_independent_certification.json", asdict(certification))
    write(
        "evidence_manifest.json",
        {
            "repositoryCommitAtGeneration": commit,
            "gitStatusAtGeneration": git("status", "--short"),
            "artifacts": tuple(file_record(path) for path in sorted(EVIDENCE_ROOT.glob("*.json")) if path.name != "evidence_manifest.json"),
        },
    )


def write(name: str, payload: Any) -> None:
    path = EVIDENCE_ROOT / name
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
