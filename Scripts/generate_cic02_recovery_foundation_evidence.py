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

from argos.control_panel.certification_recovery_foundation import execute_cic02_recovery_foundation  # noqa: E402


DEFAULT_OUTPUT = REPOSITORY_ROOT / "outputs" / "cic02_recovery_foundation"


def main() -> None:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    payload = execute_cic02_recovery_foundation(REPOSITORY_ROOT, commit=commit)
    write(output / "cic02_result.json", payload)
    write(output / "canonical_test_manifest.json", payload["canonicalTestManifest"])
    write(output / "denominator_ledger.json", payload["denominatorLedger"])
    write(output / "cr7_evidence_envelope.json", payload["cr7Evidence"])
    write(output / "cr10_qualification.json", payload["cr10Qualification"])
    write(output / "css_prerequisite_publication.json", payload["cssPrerequisitePublication"])
    write(output / "runtime_interface.json", payload["runtimeInterface"])
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
