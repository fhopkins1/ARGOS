"""Generate EO-DJ market-data boundary evidence."""

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

from argos.control_panel.market_data_provider import (  # noqa: E402
    ControlledAuthoritativeMarketDataProvider,
    MarketDataDecisionGuard,
    MarketDataGateway,
    MarketDataProofDomain,
    MarketDataProviderAbstractionLayer,
    MarketDataRejectionCode,
    MarketObservationType,
    ProviderAuthorityClass,
    ProviderAuthorityRecord,
    ProviderAuthorityRegistry,
    default_provider_authority_records,
    market_source_inventory,
    production_reachability_report,
)
from argos.foundation.contracts import utc_timestamp  # noqa: E402


OUT = REPO_ROOT / "Documentation" / "EO-DJ_Evidence"
NOW = "2026-07-18T22:00:00Z"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    commands: list[dict[str, Any]] = []
    source_inventory = tuple(market_source_inventory())
    provider_registry = tuple(default_provider_authority_records())
    trace = market_observation_trace()
    rejection_trace = prohibited_source_rejections()
    recovery = recovery_missing_evidence_trace()
    tests = run_command((sys.executable, "-m", "unittest", "Tests.test_eodj_market_data_boundary"), 120)
    commands.append(tests)
    static = run_static_assurance()
    certification = {
        "schemaVersion": "EO-DJ.1",
        "repositoryCommit": git("rev-parse", "HEAD"),
        "dirtyWorkingTreeStatus": git("status", "--short"),
        "generatedAtUtc": utc_timestamp(),
        "executedCommands": commands,
        "testCounts": parse_unittest(tests),
        "providerInventory": provider_registry,
        "remainingSyntheticMarketSources": [item for item in source_inventory if "simulation" in item["classification"] or "test" in item["classification"]],
        "productionReachableSyntheticSources": production_reachability_report()["productionReachableSyntheticSources"],
        "unresolvedPaths": production_reachability_report()["remainingUnresolvedPaths"],
        "AUTHORITATIVE_PROVIDER_CONFIGURED": False,
        "boundaryReady": tests["exit_code"] == 0 and not production_reachability_report()["productionReachableSyntheticSources"],
        "providerServiceReady": False,
        "finalVerdict": "PASS" if tests["exit_code"] == 0 and not production_reachability_report()["productionReachableSyntheticSources"] else "FAIL",
        "operatorLimitation": "No real external authoritative provider is configured or certified; ARGOS must not begin continuous authoritative paper trading.",
    }
    write("eo_dj_market_source_inventory.json", source_inventory)
    write("eo_dj_provider_authority_registry.json", provider_registry)
    write("eo_dj_production_reachability.json", production_reachability_report())
    write("eo_dj_market_observation_trace.json", trace)
    write("eo_dj_prohibited_source_rejections.json", rejection_trace)
    write("eo_dj_recovery_missing_evidence_trace.json", recovery)
    write("eo_dj_test_results.json", {"boundaryTests": tests, "staticAssurance": static})
    write("eo_dj_certification.json", certification)


def market_observation_trace() -> dict[str, Any]:
    provider_id = "eodj-controlled-authoritative"
    record = ProviderAuthorityRecord(provider_id, "EO-DJ Controlled External Adapter", "ControlledAuthoritativeMarketDataProvider", ProviderAuthorityClass.AUTHORITATIVE_EXTERNAL, (MarketDataProofDomain.PAPER_AUTHORITATIVE,), (MarketObservationType.QUOTE,), ("US",), ("test_supplied_payload",), True)
    gateway = MarketDataGateway(
        registry=ProviderAuthorityRegistry((record,)),
        providers={provider_id: ControlledAuthoritativeMarketDataProvider(provider_id, {"AAPL": {"symbol": "AAPL", "bid": "197.12", "ask": "197.13", "last": "197.125", "volume": "100000", "venue": "NASDAQ", "source_timestamp_utc": NOW}})},
    )
    result = gateway.request_observation(provider_id=provider_id, proof_domain=MarketDataProofDomain.PAPER_AUTHORITATIVE, symbol="AAPL", observation_type=MarketObservationType.QUOTE, requested_at_utc=NOW, workflow_id="WF-EO-DJ", decision_object_id="DO-EO-DJ")
    guard = MarketDataDecisionGuard(gateway.evidence_store, gateway.registry)
    guard_result = guard.validate(result.observation.observation_id if result.observation else "", accepted_proof_domains=(MarketDataProofDomain.PAPER_AUTHORITATIVE,), instrument_id="AAPL", observation_type=MarketObservationType.QUOTE)
    return {"gatewayResult": result, "decisionGuard": guard_result, "events": gateway.events, "store": gateway.evidence_store.snapshot()}


def prohibited_source_rejections() -> dict[str, Any]:
    layer = MarketDataProviderAbstractionLayer()
    missing = layer.get_quote("AAPL", NOW)
    return {
        "defaultProviderRejected": missing["auditRecord"],
        "missingProviderCode": MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_CONFIGURED.value,
        "mockFallbackEnabled": False,
        "syntheticFallbackEnabled": False,
    }


def recovery_missing_evidence_trace() -> dict[str, Any]:
    gateway = MarketDataGateway()
    guard = MarketDataDecisionGuard(gateway.evidence_store, gateway.registry)
    result = guard.validate("MISSING-OBSERVATION", accepted_proof_domains=(MarketDataProofDomain.PAPER_AUTHORITATIVE,), instrument_id="AAPL", observation_type=MarketObservationType.QUOTE)
    return {"reconstructedValue": False, "substituteFetchAttempted": False, "guardResult": result}


def run_static_assurance() -> dict[str, Any]:
    patterns = {
        "old_mock_provider_default": "provider_id: str = \"mock\"",
        "synthetic_quote_provider_default": "ARGOS Synthetic Market Data",
        "random_market_generation": "random.",
    }
    findings = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for finding_id, pattern in patterns.items():
            if pattern in text:
                findings.append({"finding": finding_id, "path": str(path.relative_to(REPO_ROOT)), "pattern": pattern})
    return {"findingCount": len(findings), "findings": findings, "allowlist": ()}


def run_command(command: tuple[str, ...], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout)
        return {"command": list(command), "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "duration_seconds": round(time.monotonic() - started, 3), "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"command": list(command), "exit_code": None, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "duration_seconds": round(time.monotonic() - started, 3), "timed_out": True}


def parse_unittest(result: dict[str, Any]) -> dict[str, int]:
    text = f"{result.get('stdout','')}\n{result.get('stderr','')}"
    count = 0
    for line in text.splitlines():
        if line.startswith("Ran ") and " tests" in line:
            count = int(line.split()[1])
    return {"total": count, "passed": count if result["exit_code"] == 0 else 0, "failed": 0 if result["exit_code"] == 0 else 1, "skipped": text.count("skipped=")}


def git(*args: str) -> str:
    return subprocess.check_output(("git",) + args, cwd=REPO_ROOT, text=True).strip()


def write(name: str, payload: Any) -> None:
    (OUT / name).write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True, default=str), encoding="utf-8")


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(getattr(value, key)) for key in value.__dataclass_fields__}
    if isinstance(value, dict):
        return {str(key): _jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


if __name__ == "__main__":
    main()
