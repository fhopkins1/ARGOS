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

from argos.control_panel.cr_audit_closure import execute_cr_series_audit  # noqa: E402


DEFAULT_OUTPUT = REPOSITORY_ROOT / "outputs" / "cr_series_audit"


def main() -> None:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    payload = execute_cr_series_audit(REPOSITORY_ROOT, commit=commit)
    write(output / "cr_series_audit.json", payload)
    write(output / "cr2_result.json", payload["orders"]["cr2"])
    write(output / "cr3_result.json", payload["orders"]["cr3"])
    write(output / "cr4_result.json", payload["orders"]["cr4"])
    write(
        output / "manifest.json",
        {
            "schemaVersion": payload["schemaVersion"],
            "repositoryCommit": commit,
            "gitStatus": git("status", "--short"),
            "generatedArtifacts": tuple(file_record(path, output) for path in sorted(output.glob("*.json")) if path.name != "manifest.json"),
        },
    )


def write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def file_record(path: Path, output: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(output).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


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
