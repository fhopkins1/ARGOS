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

from argos.control_panel.final_remediation_preflight import (  # noqa: E402
    FINAL_REMEDIATION_ORDERS,
    execute_final_remediation_preflight,
)


def main() -> None:
    commit = git("rev-parse", "HEAD")
    for order_id, order in FINAL_REMEDIATION_ORDERS.items():
        evidence_root = REPOSITORY_ROOT / "Documentation" / order.evidence_dir
        evidence_root.mkdir(parents=True, exist_ok=True)
        payload = execute_final_remediation_preflight(order_id, commit, repo_root=REPOSITORY_ROOT)
        for artifact_name in order.artifact_names:
            key = artifact_name.rsplit(".", 1)[0]
            content = payload[key]
            path = evidence_root / artifact_name
            if artifact_name.endswith(".md"):
                path.write_text(str(content), encoding="utf-8")
            else:
                write(path, content)
        write(
            evidence_root / f"{order_id.lower().replace('-', '')}_manifest.json",
            {
                "repositoryCommitAtGeneration": commit,
                "gitStatusAtGeneration": git("status", "--short"),
                "orderId": order_id,
                "verdict": payload["certification"]["verdict"],
                "entryGatePassed": payload["certification"]["entryGatePassed"],
                "artifacts": tuple(file_record(path) for path in sorted(evidence_root.iterdir()) if path.is_file()),
            },
        )


def write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def file_record(path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(REPOSITORY_ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def git(*args: str) -> str:
    result = subprocess.run(("git", *args), cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip()


if __name__ == "__main__":
    main()
