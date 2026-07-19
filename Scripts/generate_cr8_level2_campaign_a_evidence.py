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

from argos.control_panel.cr_audit_closure import execute_cr8_level2_campaign_a_audit  # noqa: E402


DEFAULT_OUTPUT = REPOSITORY_ROOT / "outputs" / "cr8_level2_campaign_a"


def main() -> None:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    payload = execute_cr8_level2_campaign_a_audit(REPOSITORY_ROOT, commit=commit)
    write(output / "cr8_result.json", payload)
    write(output / "campaign_configuration.json", payload["campaignConfiguration"])
    write(output / "campaign_attempts.json", payload["campaignAttempts"])
    write(output / "monitoring_plan.json", payload["monitoringPlan"])
    write(output / "activity_floor.json", payload["activityFloor"])
    write(output / "reconciliation_plan.json", payload["reconciliationPlan"])
    write(output / "shutdown_plan.json", payload["shutdownPlan"])
    write(output / "certification.json", payload["certification"])
    write(
        output / "manifest.json",
        {
            "schemaVersion": payload["schemaVersion"],
            "orderId": payload["orderId"],
            "repositoryCommit": commit,
            "verdict": payload["verdict"],
            "gitStatus": git("status", "--short"),
            "generatedArtifacts": tuple(file_record(path, output) for path in sorted(output.glob("*.json")) if path.name != "manifest.json"),
        },
    )


def write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def file_record(path: Path, output: Path) -> dict[str, str]:
    return {"path": path.relative_to(output).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def git(*args: str) -> str:
    result = subprocess.run(("git", *args), cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: jsonable(item) for key, item in value.__dict__.items()}
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    main()
