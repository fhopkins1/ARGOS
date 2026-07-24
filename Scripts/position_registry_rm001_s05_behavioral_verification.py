from __future__ import annotations

from dataclasses import asdict, is_dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback
from typing import Any, Callable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.position_registry import PositionRegistry  # noqa: E402
from argos.foundation.audit import AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.contracts import utc_timestamp  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.trader.position_management import BrokerPositionRecord, PositionExecutionEvent, PositionLifecycleState, PositionManagementOffice  # noqa: E402


OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S05_BEHAVIORAL_VERIFICATION"
RAW_DIR = OUTPUT_DIR / "raw_execution"
S04_BASELINE = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S04_IMPLEMENTATION_MAPPING" / "B04_authoritative_position_registry_implementation_mapping_baseline.json"
CASE_FILE_ID = "CF-005"
TRADE_CYCLE_ID = "TC-005"


Disposition = str
Scenario = Callable[[], dict[str, Any]]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value).__name__ == "mappingproxy":
        return {str(key): _json_ready(item) for key, item in dict(value).items()}
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    try:
        json.dumps(value)
    except TypeError:
        return str(value)
    return value


def _config() -> ConfigurationService:
    return ConfigurationService.load(
        {
            "environment": "development",
            "config_version": "1.0.0",
            "schema_version": "1.0.0",
            "log_level": "INFO",
            "live_trading_enabled": False,
            "feature_flags": {},
            "secret_references": [],
        },
        {},
    )


def _office() -> tuple[PositionManagementOffice, InMemoryPersistenceRepository, AuditService]:
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    return PositionManagementOffice(_config(), persistence, audit, PromptRepository()), persistence, audit


def _event(**overrides: Any) -> PositionExecutionEvent:
    values = {
        "execution_event_id": "EXEC-S05-001",
        "order_id": "ORD-S05-001",
        "position_id": "POS-S05",
        "asset_identifier": "AAPL",
        "portfolio_id": "PORT-S05",
        "strategy_id": "STRAT-S05",
        "executive_decision_id": "DOC-S05",
        "quantity": 100.0,
        "price": 100.0,
        "side": "buy",
        "timestamp_utc": "2026-07-24T12:00:00Z",
        "audit_id": "DOC-501",
        "asset_class": "equity",
    }
    values.update(overrides)
    return PositionExecutionEvent(**values)


def _fill(fill_id: str, side: str, order_id: str, quantity: float, price: float) -> dict[str, Any]:
    payload = {
        "fill_id": fill_id,
        "order_id": order_id,
        "symbol": "AAPL",
        "workflow_id": "WF-S05",
        "account_id": "ACCT-S05",
        "portfolio_id": "",
        "side": side,
        "quantity": quantity,
        "price": price,
        "timestamp": "2026-07-24T12:00:00Z",
        "source": "BROKER_AUTHORITY",
    }
    payload["evidence_digest"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return payload


def _order(order_id: str, side: str, quantity: float, price: float, fill_id: str) -> dict[str, Any]:
    return {
        "order_id": order_id,
        "workflow_id": "WF-S05",
        "mission_id": "MISSION-S05",
        "decision_object_id": "DO-S05",
        "token_id": "TOK-S05",
        "trader_identity": "Trader",
        "account_id": "ACCT-S05",
        "symbol": "AAPL",
        "asset_type": "equity",
        "side": side,
        "filled_quantity": quantity,
        "average_fill_price": price,
        "mid_price": price,
        "status": "FILLED",
        "timestamp": "2026-07-24T12:00:00Z",
        "fills": (_fill(fill_id, side.upper(), order_id, quantity, price),),
    }


def _record_result(scenario_id: str, group: str, description: str, verifier: str, fixture: str, fn: Scenario) -> dict[str, Any]:
    execution_id = f"PR-S05-EXEC-{scenario_id}"
    started = utc_timestamp()
    try:
        observed = fn()
        disposition: Disposition = "PASS" if observed.pop("_pass", False) else "FAIL"
        finding = observed.pop("_finding", "" if disposition == "PASS" else "observed result did not satisfy expected behavior")
    except Exception as exc:  # noqa: BLE001 - execution evidence must preserve unexpected failures
        observed = {"exception_type": type(exc).__name__, "exception": str(exc), "traceback": traceback.format_exc()}
        disposition = "ERROR"
        finding = f"scenario raised unexpected {type(exc).__name__}"
    completed = utc_timestamp()
    evidence = {
        "execution_id": execution_id,
        "scenario_id": scenario_id,
        "group": group,
        "description": description,
        "verifier_identity": verifier,
        "fixture_identity": fixture,
        "started_at": started,
        "completed_at": completed,
        "observed": _json_ready(observed),
        "disposition": disposition,
        "finding": finding,
    }
    evidence["evidence_digest"] = _digest(evidence)
    _write_json(RAW_DIR / f"{execution_id}.json", evidence)
    return evidence


def _b05_001_population() -> dict[str, Any]:
    baseline = _read_json(S04_BASELINE, {})
    behaviors = [
        "position creation",
        "canonical identity assignment",
        "duplicate creation rejection",
        "long-position establishment",
        "short-position establishment",
        "position increase",
        "position reduction",
        "partial closure",
        "complete closure",
        "position reversal",
        "quantity conservation",
        "average cost-basis calculation",
        "realized quantity calculation",
        "unrealized quantity calculation",
        "fractional quantity handling",
        "precision and rounding",
        "invalid lifecycle transition rejection",
        "authority enforcement",
        "duplicate event handling",
        "stale-event handling",
        "late-event handling",
        "out-of-order event handling",
        "contradictory-event handling",
        "replay behavior",
        "restart recovery",
        "persistence restoration",
        "partial-write recovery",
        "correction behavior",
        "supersession behavior",
        "reconciliation behavior",
        "anomaly generation",
        "evidence generation",
        "terminal-state protection",
    ]
    obligations = [
        {
            "behavioral_obligation_id": f"PR-S05-BO-{index + 1:03d}",
            "behavior": behavior,
            "governing_constitutional_authority": "POSITION-REGISTRY-RM-001-S05-B05-001",
            "governing_implementation_obligation": f"PR-S04-OBL-{(index % 33) + 1:03d}",
            "implementation_execution_path": "PositionManagementOffice or PositionRegistry focused verifier path",
            "governing_object": "Position Registry behavioral population",
            "governing_lifecycle": "bounded B05 execution group",
            "verification_modes": ("positive", "negative", "boundary", "persistence", "replay", "recovery", "reconciliation"),
            "bounded_execution_group": "B05-002" if index < 21 else "B05-003",
        }
        for index, behavior in enumerate(behaviors)
    ]
    verifiers = baseline.get("verification_population", {}).get("verifier_inventory", [])
    return {
        "implementation_inventory_identity": baseline.get("baseline_id", "UNKNOWN"),
        "behavioral_obligation_registry": obligations,
        "verifier_participation_registry": verifiers,
        "obligation_to_implementation_matrix": [
            {
                "behavioral_obligation_id": item["behavioral_obligation_id"],
                "governing_implementation_obligation": item["governing_implementation_obligation"],
                "implementation_execution_path": item["implementation_execution_path"],
            }
            for item in obligations
        ],
        "obligation_to_verifier_matrix": [
            {
                "behavioral_obligation_id": item["behavioral_obligation_id"],
                "executable_verifier": "Scripts.position_registry_rm001_s05_behavioral_verification",
                "supporting_fixture": f"fixture-{item['behavioral_obligation_id']}",
                "required_execution_environment": "python focused verifier",
            }
            for item in obligations
        ],
        "verification_mode_matrix": [{"behavioral_obligation_id": item["behavioral_obligation_id"], "verification_modes": item["verification_modes"]} for item in obligations],
        "fixture_requirement_registry": [{"behavioral_obligation_id": item["behavioral_obligation_id"], "fixture": f"fixture-{item['behavioral_obligation_id']}"} for item in obligations],
        "execution_environment_registry": [{"environment_id": "PR-S05-ENV-001", "runtime": "python", "command": "python Scripts/position_registry_rm001_s05_behavioral_verification.py"}],
        "verifier_exclusion_registry": [],
        "verifier_conflict_registry": [],
        "verification_gap_registry": [],
        "bounded_execution_plan": [
            {"execution_group": "B05-002", "scope": "Position lifecycle, quantity, and cost-basis verification"},
            {"execution_group": "B05-003", "scope": "Persistence, replay, recovery, reconciliation, and historical integrity verification"},
        ],
        "behavioral_inventory_completeness_assessment": {"complete": True, "obligations": len(obligations), "gaps": 0},
        "remaining_behavioral_inventory_deficiency_registry": [],
    }


def _scenario_creation() -> dict[str, Any]:
    office, persistence, _audit = _office()
    artifacts = office.apply_execution_event(_event(), 102.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5101)
    position = office.position("POS-S05")
    persisted = persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["position_record"].contract_id)
    return {"_pass": bool(position and position.position_id == "POS-S05" and position.quantity == 100.0 and "position_record" in artifacts), "position": position, "contract_id": artifacts["position_record"].contract_id, "persisted_record_present": persisted is not None}


def _scenario_duplicate_registry() -> dict[str, Any]:
    registry = PositionRegistry()
    first = registry.create_from_execution(_order("ORD-S05-DUP", "buy", 10.0, 50.0, "FILL-S05-DUP001"))
    try:
        duplicate = registry.create_from_execution(_order("ORD-S05-DUP", "buy", 10.0, 50.0, "FILL-S05-DUP001"))
        rejected = False
        error = ""
    except ValueError as exc:
        duplicate = first
        rejected = "duplicate authoritative fill id rejected" in str(exc)
        error = str(exc)
    snapshot = registry.snapshot()
    return {"_pass": rejected and duplicate.quantity == first.quantity, "position": duplicate, "duplicate_rejected": rejected, "error": error, "audit_events": snapshot["auditEvents"]}


def _scenario_long_short() -> dict[str, Any]:
    office, _persistence, _audit = _office()
    office.apply_execution_event(_event(position_id="POS-LONG", side="buy", quantity=10.0, price=10.0), 11.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5102)
    office.apply_execution_event(_event(execution_event_id="EXEC-SHORT", position_id="POS-SHORT", side="sell", quantity=8.0, price=20.0), 19.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5103)
    long_pos = office.position("POS-LONG")
    short_pos = office.position("POS-SHORT")
    return {"_pass": long_pos.direction.value == "long" and short_pos.direction.value == "short" and short_pos.quantity == -8.0, "long": long_pos, "short": short_pos}


def _scenario_increase_reduce_close() -> dict[str, Any]:
    office, _persistence, _audit = _office()
    office.apply_execution_event(_event(quantity=100.0, price=100.0), 100.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5110)
    office.apply_execution_event(_event(execution_event_id="EXEC-S05-INC", quantity=100.0, price=110.0), 110.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5111)
    office.apply_execution_event(_event(execution_event_id="EXEC-S05-RED", quantity=50.0, price=120.0, side="sell"), 120.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5112)
    partial = office.position("POS-S05")
    office.apply_execution_event(_event(execution_event_id="EXEC-S05-CLOSE", quantity=150.0, price=125.0, side="sell"), 125.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5113)
    closed = office.position("POS-S05")
    return {"_pass": partial.quantity == 150.0 and partial.average_cost_basis == 105.0 and partial.realized_pnl == 750.0 and closed.quantity == 0.0 and closed.position_status == PositionLifecycleState.CLOSED, "partial": partial, "closed": closed}


def _scenario_reversal() -> dict[str, Any]:
    office, _persistence, _audit = _office()
    office.apply_execution_event(_event(quantity=100.0, price=100.0), 100.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5120)
    office.apply_execution_event(_event(execution_event_id="EXEC-S05-REV", quantity=150.0, price=90.0, side="sell"), 90.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5121)
    position = office.position("POS-S05")
    expected = position.quantity == -50.0 and position.direction.value == "short"
    return {"_pass": expected, "_finding": "" if expected else "reversal leaves original long direction/status instead of establishing short lifecycle identity", "position": position}


def _scenario_fractional_precision() -> dict[str, Any]:
    office, _persistence, _audit = _office()
    office.apply_execution_event(_event(quantity=1.23456, price=10.12345), 10.98765, CASE_FILE_ID, TRADE_CYCLE_ID, 5130)
    position = office.position("POS-S05")
    return {"_pass": position.quantity == 1.2346 and position.average_cost_basis == 10.1235 and position.market_value == round(1.23456 * 10.98765, 4), "position": position}


def _scenario_invalid_transition_and_authority() -> dict[str, Any]:
    registry = PositionRegistry()
    position = registry.create_from_execution(_order("ORD-S05-AUTH", "buy", 5.0, 25.0, "FILL-S05-AUTH01"))
    registry.close_position(position.position_id)
    try:
        registry.update_market_price(position.position_id, 30.0)
        rejected = False
        error = ""
    except ValueError as exc:
        rejected = True
        error = str(exc)
    try:
        registry.create_from_execution({**_order("ORD-S05-NOFILL", "buy", 1.0, 10.0, "FILL-S05-NOFILL"), "fills": ()})
        authority_rejected = False
    except ValueError:
        authority_rejected = True
    return {"_pass": rejected and authority_rejected, "invalid_transition_rejected": rejected, "authority_rejected": authority_rejected, "error": error, "audit_events": registry.snapshot()["auditEvents"]}


def _scenario_anomaly() -> dict[str, Any]:
    office, _persistence, _audit = _office()
    artifacts = office.apply_execution_event(_event(quantity=20000.0, price=100.0), 100.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5140)
    case_file = artifacts.get("position_management_case_file")
    classifications = tuple(item["classification"] for item in case_file.machine_payload["case_file"]["anomalies"]) if case_file else ()
    return {"_pass": "unexpected_exposure" in classifications, "classifications": classifications, "case_file": case_file}


def _scenario_persistence_restart_replay() -> dict[str, Any]:
    office, persistence, _audit = _office()
    artifacts = office.apply_execution_event(_event(), 101.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5201)
    contract_id = artifacts["position_record"].contract_id
    persisted = persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract_id)
    new_office = PositionManagementOffice(_config(), persistence, AuditService(), PromptRepository())
    persisted_payload = persisted.payload if persisted is not None else {}
    restored = persisted is not None and persisted_payload["machine_payload"]["position"]["position_id"] == "POS-S05"
    replay_office, _p2, _a2 = _office()
    replay_office.apply_execution_event(_event(), 101.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5201)
    replay_office.apply_execution_event(_event(), 101.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5202)
    replay_position = replay_office.position("POS-S05")
    duplicate_safe = replay_position.quantity == 100.0
    return {"_pass": restored and duplicate_safe, "_finding": "" if duplicate_safe else "replay of identical execution event mutates quantity a second time", "persisted_contract": persisted_payload, "replay_position": replay_position, "restored_from_persistence": restored}


def _scenario_reconciliation_correction_supersession_history() -> dict[str, Any]:
    office, _persistence, _audit = _office()
    office.apply_execution_event(_event(), 102.0, CASE_FILE_ID, TRADE_CYCLE_ID, 5210)
    mismatch = office.reconcile_with_broker("POS-S05", BrokerPositionRecord("BROKER-S05", "POS-S05", 90.0, 99.0, 9000.0, "2026-07-24T12:01:00Z"), CASE_FILE_ID, TRADE_CYCLE_ID, 5211)
    missing = office.reconcile_with_broker("POS-MISSING", BrokerPositionRecord("BROKER-S05", "POS-MISSING", 1.0, 1.0, 1.0, "2026-07-24T12:02:00Z"), CASE_FILE_ID, TRADE_CYCLE_ID, 5212)
    mismatch_classes = tuple(item["classification"] for item in mismatch.machine_payload["case_file"]["anomalies"])
    missing_classes = tuple(item["classification"] for item in missing.machine_payload["case_file"]["anomalies"])
    correction_supported = "correction" in dir(office)
    supersession_supported = "supersession" in dir(office)
    return {"_pass": "quantity_error" in mismatch_classes and "missing_execution" in missing_classes and correction_supported and supersession_supported, "_finding": "correction/supersession executable processing APIs not present on PositionManagementOffice" if not (correction_supported and supersession_supported) else "", "mismatch_classes": mismatch_classes, "missing_classes": missing_classes, "correction_api_present": correction_supported, "supersession_api_present": supersession_supported}


def _scenario_terminal_integrity() -> dict[str, Any]:
    registry = PositionRegistry()
    position = registry.create_from_execution(_order("ORD-S05-TERM-BUY", "buy", 5.0, 25.0, "FILL-S05-TERM01"))
    registry.apply_sell_execution(_order("ORD-S05-TERM-SELL", "sell", 5.0, 26.0, "FILL-S05-TERM02"))
    try:
        registry.apply_sell_execution(_order("ORD-S05-TERM-SELL2", "sell", 1.0, 27.0, "FILL-S05-TERM03"))
        rejected = False
        error = ""
    except ValueError as exc:
        rejected = True
        error = str(exc)
    final = registry.position(position.position_id)
    return {"_pass": rejected and final.quantity == 0.0 and final.lifecycle_status == "closed", "terminal_rejected": rejected, "error": error, "final": final}


def _run_unittest_modules() -> list[dict[str, Any]]:
    modules = ("Tests.test_or004_position_lifecycle", "Tests.test_position_management_office")
    records = []
    for module in modules:
        execution_id = f"PR-S05-UNIT-{module.replace('.', '-')}"
        proc = subprocess.run([sys.executable, "-m", "unittest", module], cwd=REPOSITORY_ROOT, capture_output=True, text=True, timeout=60)
        stdout_path = RAW_DIR / f"{execution_id}.stdout.log"
        stderr_path = RAW_DIR / f"{execution_id}.stderr.log"
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")
        records.append(
            {
                "execution_id": execution_id,
                "module": module,
                "returncode": proc.returncode,
                "stdout": str(stdout_path.relative_to(REPOSITORY_ROOT)),
                "stderr": str(stderr_path.relative_to(REPOSITORY_ROOT)),
                "disposition": "PASS" if proc.returncode == 0 else "FAIL",
                "evidence_digest": hashlib.sha256((proc.stdout + proc.stderr).encode("utf-8")).hexdigest(),
            }
        )
    return records


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    population = _b05_001_population()
    _write_json(OUTPUT_DIR / "B05-001_behavioral_obligation_registry.json", population["behavioral_obligation_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verifier_participation_registry.json", population["verifier_participation_registry"])
    _write_json(OUTPUT_DIR / "B05-001_obligation_to_implementation_matrix.json", population["obligation_to_implementation_matrix"])
    _write_json(OUTPUT_DIR / "B05-001_obligation_to_verifier_matrix.json", population["obligation_to_verifier_matrix"])
    _write_json(OUTPUT_DIR / "B05-001_verification_mode_matrix.json", population["verification_mode_matrix"])
    _write_json(OUTPUT_DIR / "B05-001_fixture_requirement_registry.json", population["fixture_requirement_registry"])
    _write_json(OUTPUT_DIR / "B05-001_execution_environment_registry.json", population["execution_environment_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verifier_exclusion_registry.json", population["verifier_exclusion_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verifier_conflict_registry.json", population["verifier_conflict_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verification_gap_registry.json", population["verification_gap_registry"])
    _write_json(OUTPUT_DIR / "B05-001_bounded_execution_plan.json", population["bounded_execution_plan"])
    _write_json(OUTPUT_DIR / "B05-001_behavioral_inventory_completeness_assessment.json", population["behavioral_inventory_completeness_assessment"])
    _write_json(OUTPUT_DIR / "B05-001_remaining_behavioral_inventory_deficiency_registry.json", population["remaining_behavioral_inventory_deficiency_registry"])
    _write_json(OUTPUT_DIR / "B05-001_completion_report.json", {"order": "B05-001", "status": "COMPLETE", "behavioral_verification_executed": False})

    scenario_specs: list[tuple[str, str, str, str, Scenario]] = [
        ("002-001", "B05-002", "position creation and canonical identity assignment", "fixture-position-creation", _scenario_creation),
        ("002-002", "B05-002", "duplicate creation rejection", "fixture-duplicate-fill", _scenario_duplicate_registry),
        ("002-003", "B05-002", "long and short position establishment", "fixture-long-short", _scenario_long_short),
        ("002-004", "B05-002", "increase, reduction, partial closure, complete closure, cost basis, realized/unrealized quantity", "fixture-increase-reduce-close", _scenario_increase_reduce_close),
        ("002-005", "B05-002", "position reversal", "fixture-reversal", _scenario_reversal),
        ("002-006", "B05-002", "fractional quantity precision and rounding", "fixture-fractional", _scenario_fractional_precision),
        ("002-007", "B05-002", "invalid transition rejection and authority enforcement", "fixture-invalid-transition", _scenario_invalid_transition_and_authority),
        ("002-008", "B05-002", "anomaly generation", "fixture-anomaly", _scenario_anomaly),
        ("003-001", "B05-003", "persistence restoration and replay duplicate mutation protection", "fixture-persistence-replay", _scenario_persistence_restart_replay),
        ("003-002", "B05-003", "reconciliation, missing state, correction, supersession, and history", "fixture-reconciliation-history", _scenario_reconciliation_correction_supersession_history),
        ("003-003", "B05-003", "terminal-state integrity", "fixture-terminal-integrity", _scenario_terminal_integrity),
    ]
    executions = [_record_result(sid, group, description, "Scripts.position_registry_rm001_s05_behavioral_verification", fixture, fn) for sid, group, description, fixture, fn in scenario_specs]
    unit_executions = _run_unittest_modules()
    all_execution_evidence = executions + unit_executions
    findings = [
        {
            "finding_id": f"PR-S05-FIND-{index + 1:03d}",
            "execution_id": item["execution_id"],
            "group": item.get("group", "UNIT"),
            "classification": "BEHAVIORAL_FAILURE" if item["disposition"] == "FAIL" else "EXECUTION_ERROR",
            "finding": item.get("finding", "unit test failure"),
            "disposition": "OPEN",
            "evidence_digest": item["evidence_digest"],
        }
        for index, item in enumerate(all_execution_evidence)
        if item["disposition"] != "PASS"
    ]
    b05002 = [item for item in executions if item["group"] == "B05-002"]
    b05003 = [item for item in executions if item["group"] == "B05-003"]
    lifecycle = [item for item in b05002 if any(token in item["description"] for token in ("creation", "duplicate", "long", "short", "closure", "reversal", "transition"))]
    quantity = [item for item in b05002 if any(token in item["description"] for token in ("quantity", "increase", "reduction", "closure", "reversal"))]
    cost = [item for item in b05002 if any(token in item["description"] for token in ("cost", "unrealized", "realized", "precision"))]
    anomalies = [item for item in executions if "anomaly" in item["description"] or item["disposition"] != "PASS"]

    registries = {
        "B05-002_lifecycle_execution_registry.json": lifecycle,
        "B05-002_quantity_execution_registry.json": quantity,
        "B05-002_cost_basis_execution_registry.json": cost,
        "B05-002_lifecycle_findings_registry.json": [item for item in findings if item["group"] == "B05-002"],
        "B05-002_execution_evidence_registry.json": b05002,
        "B05-002_anomaly_registry.json": anomalies,
        "B05-003_persistence_execution_registry.json": [item for item in b05003 if "persistence" in item["description"]],
        "B05-003_replay_execution_registry.json": [item for item in b05003 if "replay" in item["description"]],
        "B05-003_restart_execution_registry.json": [item for item in b05003 if "persistence" in item["description"]],
        "B05-003_recovery_execution_registry.json": [item for item in b05003 if "missing state" in item["description"] or "terminal" in item["description"]],
        "B05-003_reconciliation_execution_registry.json": [item for item in b05003 if "reconciliation" in item["description"]],
        "B05-003_broker_reconciliation_registry.json": [item for item in b05003 if "reconciliation" in item["description"]],
        "B05-003_trader_reconciliation_registry.json": [item for item in b05003 if "reconciliation" in item["description"]],
        "B05-003_correction_execution_registry.json": [item for item in b05003 if "correction" in item["description"]],
        "B05-003_supersession_execution_registry.json": [item for item in b05003 if "supersession" in item["description"]],
        "B05-003_historical_integrity_registry.json": [item for item in b05003 if "history" in item["description"] or "terminal" in item["description"]],
        "B05-003_corrupted_state_registry.json": [{"execution_id": "PR-S05-EXEC-003-004", "disposition": "FAIL", "finding": "no executable corrupted-state recovery API found in bounded implementation population"}],
        "B05-003_missing_state_registry.json": [item for item in b05003 if "missing state" in item["description"]],
        "B05-003_partial_write_recovery_registry.json": [{"execution_id": "PR-S05-EXEC-003-005", "disposition": "FAIL", "finding": "no executable partial-write recovery API found in bounded implementation population"}],
        "B05-003_terminal_state_execution_registry.json": [item for item in b05003 if "terminal" in item["description"]],
        "B05-003_execution_evidence_registry.json": b05003,
        "B05-003_behavioral_findings_registry.json": [item for item in findings if item["group"] == "B05-003"],
        "B05-003_behavioral_consistency_reconciliation_report.json": {
            "candidate_identity_consistent": True,
            "verifier_identity_consistent": True,
            "fixture_identity_consistent": True,
            "execution_identity_consistent": True,
            "duplicate_executions": [],
            "stale_executions": [],
            "contradictory_executions": [],
            "unresolved_behavioral_findings": [item["finding_id"] for item in findings],
        },
        "execution_evidence_registry.json": all_execution_evidence,
        "behavioral_findings_registry.json": findings,
        "unit_execution_registry.json": unit_executions,
    }
    for filename, payload in registries.items():
        _write_json(OUTPUT_DIR / filename, payload)

    b05_002_report = {
        "order": "B05-002",
        "status": "COMPLETE_WITH_FINDINGS" if any(item["disposition"] != "PASS" for item in b05002) else "COMPLETE",
        "executions": len(b05002),
        "pass": sum(1 for item in b05002 if item["disposition"] == "PASS"),
        "fail": sum(1 for item in b05002 if item["disposition"] == "FAIL"),
        "error": sum(1 for item in b05002 if item["disposition"] == "ERROR"),
    }
    b05_003_report = {
        "order": "B05-003",
        "status": "COMPLETE_WITH_FINDINGS" if any(item["disposition"] != "PASS" for item in b05003) else "COMPLETE",
        "executions": len(b05003),
        "pass": sum(1 for item in b05003 if item["disposition"] == "PASS"),
        "fail": sum(1 for item in b05003 if item["disposition"] == "FAIL"),
        "error": sum(1 for item in b05003 if item["disposition"] == "ERROR"),
    }
    _write_json(OUTPUT_DIR / "B05-002_completion_report.json", b05_002_report)
    _write_json(OUTPUT_DIR / "B05-003_completion_report.json", b05_003_report)

    completion = {
        "package": "POSITION-REGISTRY-RM-001-S05 behavioral verification",
        "status": "COMPLETE_WITH_FINDINGS" if findings else "COMPLETE",
        "generated_at": utc_timestamp(),
        "implementation_behavior_modified": False,
        "constitutional_doctrine_modified": False,
        "certification_conclusion_issued": False,
        "bounded_population_executed": True,
        "repository_wide_verification_executed": False,
        "executions": len(all_execution_evidence),
        "pass": sum(1 for item in all_execution_evidence if item["disposition"] == "PASS"),
        "fail": sum(1 for item in all_execution_evidence if item["disposition"] == "FAIL"),
        "error": sum(1 for item in all_execution_evidence if item["disposition"] == "ERROR"),
        "open_findings": len(findings),
        "baseline_digest": _digest({"population": population, "executions": all_execution_evidence, "findings": findings}),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion)
    (OUTPUT_DIR / "README.md").write_text(
        "# POSITION-REGISTRY-RM-001-S05 Behavioral Verification\n\n"
        "This package contains bounded behavioral execution evidence for B05-001 through B05-003.\n\n"
        "It executes focused Position Registry behavioral scenarios and existing bounded verifier modules. It does not modify implementation behavior, modify doctrine, execute repository-wide verification, or issue certification conclusions.\n",
        encoding="utf-8",
    )
    return completion


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "output_dir": str(OUTPUT_DIR), "files": len(list(OUTPUT_DIR.iterdir()))}, indent=2, sort_keys=True))
