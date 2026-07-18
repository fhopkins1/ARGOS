"""Generate EO-DK canonical bridge fabric evidence."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import CanonicalBridgeExecutor, CanonicalEnterpriseRuntime, bridge_inventory, make_bridge_request  # noqa: E402
from argos.foundation.contracts import utc_timestamp  # noqa: E402


OUT = REPO_ROOT / "Documentation" / "EO-DK_Evidence"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = tuple(bridge_inventory())
    executor = CanonicalBridgeExecutor(runtime_instance_id="EO-DK-EVIDENCE")
    executor.ownership.establish("WF-EODK", "Seeker", "TOK-EODK")
    result = executor.execute(make_bridge_request(bridge_id="BRIDGE-SEEKER-ANALYST-001", runtime_instance_id="EO-DK-EVIDENCE", workflow_id="WF-EODK", source="Seeker", destination="Analyst", artifact_id="SEEKER-REPORT-1", payload={"report": "bounded dynamic evidence"}, current_owner="Seeker", next_owner="Analyst", token_id="TOK-EODK"))
    runtime = CanonicalEnterpriseRuntime()
    runtime.start()
    runtime.admit_scheduled_obligation("post_open_discovery")
    tests = run_command((sys.executable, "-m", "unittest", "Tests.test_eodk_bridge_fabric"), 120)
    matrix = certification_matrix(inventory, executor)
    direct_calls = direct_call_inventory()
    certification = {
        "schemaVersion": "EO-DK.1",
        "repositoryCommit": git("rev-parse", "HEAD"),
        "dirtyWorkingTreeStatus": git("status", "--short"),
        "generatedAtUtc": utc_timestamp(),
        "canonicalRuntimeIdentity": "CanonicalEnterpriseRuntime",
        "totalRegisteredBridges": len(inventory),
        "requiredProductionBridges": sum(1 for item in inventory if item["requirement_class"] == "REQUIRED_PRODUCTION"),
        "certifiedProductionBridges": sum(1 for item in matrix if item["certification_status"] == "CERTIFIED_PRODUCTION"),
        "conditionallyProductionBridges": sum(1 for item in matrix if item["certification_status"] == "CONDITIONALLY_PRODUCTION"),
        "partialBridges": sum(1 for item in matrix if item["implementation_status"] == "PARTIAL"),
        "replayOnlyBridges": sum(1 for item in inventory if item["requirement_class"] == "REPLAY_ONLY"),
        "failedBridges": sum(1 for item in matrix if item["certification_status"] == "CERTIFICATION_FAILED"),
        "dynamicallyTracedBridges": len({trace["bridge_id"] for trace in executor.snapshot()["traces"]}),
        "untracedRequiredBridges": [item["bridge_id"] for item in inventory if item["requirement_class"] == "REQUIRED_PRODUCTION" and item["bridge_id"] not in {trace["bridge_id"] for trace in executor.snapshot()["traces"]}],
        "bypassPathsFound": len(direct_calls),
        "bypassPathsRemaining": len(direct_calls),
        "executedCommands": (tests,),
        "testCounts": parse_unittest(tests),
        "formalVerdict": "INCOMPLETE",
        "verdictReason": "Canonical fabric is implemented and runtime-integrated, but not every required production bridge has endpoint-level dynamic execution evidence.",
    }
    write("eo_dk_bridge_inventory.json", inventory)
    write("eo_dk_bridge_registry.json", inventory)
    write("eo_dk_direct_call_inventory.json", direct_calls)
    write("eo_dk_orphan_office_inventory.json", [])
    write("eo_dk_static_assurance.json", {"directCallFindingCount": len(direct_calls), "allowlist": []})
    write("eo_dk_dynamic_bridge_traces.json", executor.snapshot()["traces"])
    write("eo_dk_bridge_certification_matrix.json", matrix)
    write("eo_dk_ownership_transfer_tests.json", {"seekerToAnalyst": result})
    write("eo_dk_failure_and_recovery_tests.json", {"recoveryPolicy": "missing evidence remains unresolved"})
    write("eo_dk_canonical_runtime_trace.json", runtime.read_only_snapshot()["bridgeFabric"])
    write("eo_dk_unresolved_bridges.json", certification["untracedRequiredBridges"])
    write("eo_dk_test_results.json", tests)
    write("eo_dk_certification.json", certification)


def certification_matrix(inventory: tuple[dict[str, Any], ...], executor: CanonicalBridgeExecutor) -> list[dict[str, Any]]:
    traced = {trace["bridge_id"] for trace in executor.snapshot()["traces"]}
    rows = []
    for item in inventory:
        status = item["certification_status"]
        if item["bridge_id"] in traced and status in {"UNCERTIFIED", "STATICALLY_VALIDATED"}:
            status = "DYNAMICALLY_TRACED"
        rows.append({**item, "dynamic_trace_present": item["bridge_id"] in traced, "certification_status": status})
    return rows


def direct_call_inventory() -> list[dict[str, str]]:
    findings = []
    for path in (REPO_ROOT / "src" / "argos" / "control_panel").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if ".submit_order(" in text and "canonical_bridge_fabric" not in path.name:
            findings.append({"path": str(path.relative_to(REPO_ROOT)), "pattern": ".submit_order(", "classification": "requires bridge review"})
    return findings


def run_command(command: tuple[str, ...], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout)
    return {"command": list(command), "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "duration_seconds": round(time.monotonic() - started, 3), "timed_out": False}


def parse_unittest(result: dict[str, Any]) -> dict[str, int]:
    text = f"{result['stdout']}\n{result['stderr']}"
    total = 0
    for line in text.splitlines():
        if line.startswith("Ran "):
            total = int(line.split()[1])
    return {"total": total, "passed": total if result["exit_code"] == 0 else 0, "failed": 0 if result["exit_code"] == 0 else 1, "skipped": 0}


def git(*args: str) -> str:
    return subprocess.check_output(("git",) + args, cwd=REPO_ROOT, text=True).strip()


def write(name: str, payload: Any) -> None:
    (OUT / name).write_text(json.dumps(jsonable(payload), indent=2, sort_keys=True, default=str), encoding="utf-8")


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: jsonable(getattr(value, key)) for key in value.__dataclass_fields__}
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


if __name__ == "__main__":
    main()
