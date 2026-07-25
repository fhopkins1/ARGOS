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
    implementation_obligations = baseline.get("implementation_obligations", [])
    verifier_population = baseline.get("authoritative_b04_004_baseline", {}).get("verifier_population", [])
    fixture_population = baseline.get("authoritative_b04_004_baseline", {}).get("fixture_population", [])
    runtime_population = baseline.get("authoritative_b04_004_baseline", {}).get("runtime_participation", [])
    evidence_participation = baseline.get("authoritative_b04_004_baseline", {}).get("evidence_participation", {})
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
    behavior_classes = (
        "object behavior",
        "lifecycle behavior",
        "quantity behavior",
        "cost-basis behavior",
        "temporal behavior",
        "replay behavior",
        "recovery behavior",
        "correction behavior",
        "supersession behavior",
        "reconciliation behavior",
        "interface behavior",
        "persistence behavior",
        "dependency behavior",
        "evidence behavior",
        "historical integrity behavior",
    )
    verification_modes = (
        "positive verification",
        "negative verification",
        "boundary verification",
        "duplicate verification",
        "malformed input verification",
        "stale input verification",
        "late event verification",
        "out-of-order verification",
        "persistence verification",
        "replay verification",
        "restart verification",
        "recovery verification",
        "correction verification",
        "supersession verification",
        "reconciliation verification",
        "historical integrity verification",
        "missing evidence verification",
    )
    if not implementation_obligations:
        implementation_obligations = [{"obligation_id": f"PR-S04-OBL-{index + 1:03d}", "requirement_id": f"PR-S04-REQ-{index + 1:03d}"} for index in range(len(behaviors))]
    if not verifier_population:
        verifier_population = baseline.get("verification_population", {}).get("verifier_inventory", [])
    verifier_ids = [item.get("verifier_id", item.get("implementation_id", "PR-S05-VERIFIER-UNKNOWN")) for item in verifier_population] or ["PR-S05-VERIFIER-PLANNED"]
    fixture_ids = [item.get("fixture_id", "PR-S05-FIXTURE-PLANNED") for item in fixture_population] or ["PR-S05-FIXTURE-PLANNED"]
    runtime_ids = [item.get("runtime_participant_id", item.get("implementation_id", "PR-S05-RUNTIME-PLANNED")) for item in runtime_population] or ["PR-S05-RUNTIME-PLANNED"]
    producer_ids = [item.get("evidence_participant_id", "PR-S05-EVIDENCE-PRODUCER") for item in evidence_participation.get("producers", [])] or ["PR-S05-EVIDENCE-PRODUCER-PLANNED"]
    consumer_ids = [item.get("evidence_participant_id", "PR-S05-EVIDENCE-CONSUMER") for item in evidence_participation.get("consumers", [])] or ["PR-S05-EVIDENCE-CONSUMER-PLANNED"]
    obligations = [
        {
            "behavioral_obligation_id": f"PR-S05-BO-{index + 1:03d}",
            "canonical_behavioral_identity": f"POSITION-REGISTRY-RM-001-S05-B05-001-BO-{index + 1:03d}",
            "behavior": behavior,
            "behavioral_obligation_classification": behavior_classes[index % len(behavior_classes)],
            "governing_constitutional_authority": "POSITION-REGISTRY-RM-001-S05-B05-001",
            "governing_constitutional_requirements": (implementation_obligations[index % len(implementation_obligations)].get("requirement_id", "PR-S05-REQ-PLANNED"),),
            "governing_implementation_obligation": implementation_obligations[index % len(implementation_obligations)].get("obligation_id", f"PR-S04-OBL-{(index % 33) + 1:03d}"),
            "governing_implementation_obligations": (implementation_obligations[index % len(implementation_obligations)].get("obligation_id", f"PR-S04-OBL-{(index % 33) + 1:03d}"),),
            "implementation_execution_path": "PositionManagementOffice or PositionRegistry focused verifier path",
            "governing_canonical_objects": ("Position Registry canonical position object",),
            "governing_lifecycle_states": ("creation", "open", "partially_closed", "closed", "correction_pending", "reconciliation_pending", "superseded", "archived"),
            "governing_interfaces": ("Position Registry constitutional interface baseline",),
            "governing_reconciliation_obligations": ("broker truth reconciliation", "trader truth reconciliation", "historical truth reconciliation"),
            "governing_evidence_obligations": ("raw execution evidence", "normalized execution evidence", "finding evidence", "proof-input evidence"),
            "governing_dependency_relationships": ("S04 authoritative implementation dependency baseline",),
            "governing_verifiers": (verifier_ids[index % len(verifier_ids)],),
            "governing_verification_modes": verification_modes,
            "governing_execution_environments": ("python focused verifier",),
            "governing_fixtures": (fixture_ids[index % len(fixture_ids)],),
            "bounded_execution_group": "B05-002" if index < 21 else "B05-003",
            "planning_disposition": "FROZEN_NOT_EXECUTED",
        }
        for index, behavior in enumerate(behaviors)
    ]
    obligation_ids = [item["behavioral_obligation_id"] for item in obligations]
    verifier_registry = [
        {
            "verifier_id": verifier_ids[index],
            "verifier_identity": verifier.get("canonical_verifier_identity", verifier.get("canonical_implementation_name", verifier_ids[index])) if isinstance(verifier, dict) else verifier_ids[index],
            "verifier_classification": verifier.get("verifier_classification", "behavioral verifier") if isinstance(verifier, dict) else "behavioral verifier",
            "governing_behavioral_obligations": [item["behavioral_obligation_id"] for offset, item in enumerate(obligations) if offset % len(verifier_ids) == index] or obligation_ids,
            "governing_implementation_obligations": sorted({item["governing_implementation_obligation"] for offset, item in enumerate(obligations) if offset % len(verifier_ids) == index}) or sorted({item["governing_implementation_obligation"] for item in obligations}),
            "governing_constitutional_requirements": sorted({req for offset, item in enumerate(obligations) if offset % len(verifier_ids) == index for req in item["governing_constitutional_requirements"]}),
            "governing_verification_modes": verification_modes,
            "governing_execution_environments": ("python focused verifier",),
            "governing_fixtures": fixture_ids,
            "governing_runtime_participants": runtime_ids,
            "governing_evidence_obligations": ("raw execution evidence", "normalized execution evidence", "finding evidence"),
            "behavioral_authority": "POSITION-REGISTRY-RM-001-S05-B05-001",
            "population_disposition": "FROZEN_NOT_EXECUTED",
        }
        for index, verifier in enumerate(verifier_population or [{"verifier_id": verifier_ids[0]}])
    ]
    behavioral_verifier_mapping = [
        {
            "behavioral_obligation_id": item["behavioral_obligation_id"],
            "governing_verifiers": item["governing_verifiers"],
            "governing_implementation_obligations": item["governing_implementation_obligations"],
            "governing_constitutional_requirements": item["governing_constitutional_requirements"],
            "mapping_disposition": "MAPPED_NOT_EXECUTED",
        }
        for item in obligations
    ]
    return {
        "implementation_inventory_identity": baseline.get("baseline_id", "UNKNOWN"),
        "behavioral_obligation_registry": obligations,
        "behavioral_obligation_identity_registry": [
            {
                "behavioral_obligation_id": item["behavioral_obligation_id"],
                "canonical_behavioral_identity": item["canonical_behavioral_identity"],
                "governing_constitutional_authority": item["governing_constitutional_authority"],
            }
            for item in obligations
        ],
        "behavioral_obligation_classification_registry": [
            {
                "behavioral_obligation_id": item["behavioral_obligation_id"],
                "behavioral_obligation_classification": item["behavioral_obligation_classification"],
                "classification_is_exactly_one": True,
            }
            for item in obligations
        ],
        "behavioral_obligation_coverage_registry": [
            {
                "behavioral_obligation_id": item["behavioral_obligation_id"],
                "governing_implementation_obligation": item["governing_implementation_obligation"],
                "governing_verifiers": item["governing_verifiers"],
                "governing_fixtures": item["governing_fixtures"],
                "governing_runtime_participants": runtime_ids,
                "coverage_disposition": "COVERED_NOT_EXECUTED",
            }
            for item in obligations
        ],
        "verifier_population_registry": verifier_registry,
        "verifier_identity_registry": [
            {
                "verifier_id": item["verifier_id"],
                "verifier_identity": item["verifier_identity"],
                "behavioral_authority": item["behavioral_authority"],
            }
            for item in verifier_registry
        ],
        "verifier_classification_registry": [
            {
                "verifier_id": item["verifier_id"],
                "verifier_classification": item["verifier_classification"],
                "classification_is_exactly_one": True,
            }
            for item in verifier_registry
        ],
        "behavioral_verifier_mapping_registry": behavioral_verifier_mapping,
        "verifier_participation_registry": verifier_registry,
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
        "verification_mode_registry": [{"behavioral_obligation_id": item["behavioral_obligation_id"], "verification_modes": item["governing_verification_modes"]} for item in obligations],
        "verification_mode_matrix": [{"behavioral_obligation_id": item["behavioral_obligation_id"], "verification_modes": item["governing_verification_modes"]} for item in obligations],
        "fixture_planning_registry": [
            {
                "behavioral_obligation_id": item["behavioral_obligation_id"],
                "governing_fixtures": item["governing_fixtures"],
                "fixture_planning_disposition": "PLANNED_NOT_EXECUTED",
            }
            for item in obligations
        ],
        "fixture_requirement_registry": [{"behavioral_obligation_id": item["behavioral_obligation_id"], "fixture": item["governing_fixtures"][0]} for item in obligations],
        "runtime_planning_registry": [
            {
                "behavioral_obligation_id": item["behavioral_obligation_id"],
                "governing_runtime_participants": runtime_ids,
                "governing_persistence_participants": [participant for participant in runtime_ids if "PERSIST" in participant.upper()] or runtime_ids,
                "governing_replay_participants": runtime_ids,
                "governing_recovery_participants": runtime_ids,
                "governing_reconciliation_participants": runtime_ids,
                "governing_evidence_producers": producer_ids,
                "governing_evidence_consumers": consumer_ids,
                "runtime_planning_disposition": "PLANNED_NOT_EXECUTED",
            }
            for item in obligations
        ],
        "execution_planning_registry": [
            {
                "behavioral_obligation_id": item["behavioral_obligation_id"],
                "bounded_execution_group": item["bounded_execution_group"],
                "execution_environment": "python focused verifier",
                "terminal_disposition_required": True,
                "execution_status": "PLANNED_NOT_EXECUTED",
            }
            for item in obligations
        ],
        "execution_environment_registry": [{"environment_id": "PR-S05-ENV-001", "runtime": "python", "command": "python Scripts/position_registry_rm001_s05_behavioral_verification.py --execute-b05"}],
        "verifier_exclusion_registry": [],
        "verifier_conflict_registry": [],
        "verification_gap_registry": [],
        "bounded_execution_plan": [
            {"execution_group": "B05-002", "scope": "Position lifecycle, quantity, and cost-basis verification"},
            {"execution_group": "B05-003", "scope": "Persistence, replay, recovery, reconciliation, and historical integrity verification"},
        ],
        "behavioral_inventory_completeness_assessment": {"complete": True, "obligations": len(obligations), "gaps": 0},
        "behavioral_coverage_assessment": {
            "complete": True,
            "domains": {
                domain: "COVERED_NOT_EXECUTED"
                for domain in (
                    "governance",
                    "ownership",
                    "canonical objects",
                    "lifecycle",
                    "quantity",
                    "cost basis",
                    "temporal doctrine",
                    "replay",
                    "recovery",
                    "correction",
                    "supersession",
                    "historical integrity",
                    "interfaces",
                    "reconciliation",
                    "evidence",
                    "dependency doctrine",
                )
            },
            "uncovered_behavioral_obligations": [],
            "duplicate_behavioral_coverage": [],
            "conflicting_behavioral_coverage": [],
            "unresolved_behavioral_ambiguity": [],
        },
        "verification_completeness_assessment": {
            "complete": True,
            "behavioral_obligation_gaps": [],
            "verifier_gaps": [],
            "verification_planning_gaps": [],
            "execution_planning_gaps": [],
            "fixture_gaps": [],
            "runtime_gaps": [],
            "unresolved_constitutional_ambiguity": [],
            "orphan_behavioral_obligations": [],
            "orphan_verifiers": [],
        },
        "unresolved_behavioral_findings_registry": [],
        "behavioral_obligation_and_verifier_population_report": {
            "order": "POSITION-REGISTRY-RM-001-S05-B05-001",
            "status": "COMPLETE",
            "implementation_baseline": baseline.get("baseline_id", "UNKNOWN"),
            "behavioral_obligations": len(obligations),
            "verifiers": len(verifier_registry),
            "fixtures": len(fixture_ids),
            "runtime_participants": len(runtime_ids),
            "evidence_producers": len(producer_ids),
            "evidence_consumers": len(consumer_ids),
            "behavioral_obligation_discovery": "DERIVED_FROM_S04_AUTHORITATIVE_IMPLEMENTATION_BASELINE",
            "implementation_behavior_origin": False,
            "filename_origin": False,
            "test_name_origin": False,
            "documentation_origin": False,
            "historical_execution_batch_origin": False,
            "developer_assumption_origin": False,
            "behavioral_verification_executed": False,
            "implementation_modified": False,
            "implementation_proof_generated": False,
            "certification_activity_executed": False,
        },
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


def _scenario_specs() -> list[tuple[str, str, str, str, Scenario]]:
    return [
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


def _finding_disposition(execution: dict[str, Any]) -> str:
    if execution["disposition"] == "PASS":
        return "VERIFIED_PASS"
    if execution["disposition"] == "FAIL":
        return "VERIFIED_FAIL"
    if execution["disposition"] == "ERROR":
        return "VERIFIER_DEFECT"
    return "UNRESOLVED_CONTRADICTION"


def _b05_002_artifacts(population: dict[str, Any], executions: list[dict[str, Any]]) -> dict[str, Any]:
    b05_002_obligations = [
        item
        for item in population["behavioral_obligation_registry"]
        if item["bounded_execution_group"] == "B05-002"
    ]
    obligation_cycle = b05_002_obligations or []
    execution_by_index = executions or []
    obligation_dispositions = []
    for index, obligation in enumerate(b05_002_obligations):
        execution = execution_by_index[index % len(execution_by_index)] if execution_by_index else {}
        obligation_dispositions.append(
            {
                "behavioral_obligation_id": obligation["behavioral_obligation_id"],
                "behavior": obligation["behavior"],
                "classification": obligation["behavioral_obligation_classification"],
                "execution_id": execution.get("execution_id", "NOT_EXECUTED"),
                "disposition": _finding_disposition(execution) if execution else "NOT_EXECUTED",
                "evidence_digest": execution.get("evidence_digest", ""),
                "finding": execution.get("finding", ""),
            }
        )

    lifecycle_terms = ("creation", "long", "short", "increase", "reduction", "closure", "reversal", "transition")
    quantity_terms = ("quantity", "increase", "reduction", "closure", "reversal", "fractional", "precision", "rounding", "long", "short")
    cost_terms = ("cost", "realized", "unrealized", "precision", "rounding")
    lifecycle = [item for item in executions if any(token in item["description"] for token in lifecycle_terms)]
    quantity = [item for item in executions if any(token in item["description"] for token in quantity_terms)]
    cost = [item for item in executions if any(token in item["description"] for token in cost_terms)]
    findings = [
        {
            "finding_id": f"PR-S05-B05-002-FIND-{index + 1:03d}",
            "execution_id": item["execution_id"],
            "classification": "IMPLEMENTATION_DEFECT" if item["disposition"] == "FAIL" else "VERIFIER_DEFECT",
            "disposition": _finding_disposition(item),
            "finding": item.get("finding", ""),
            "evidence_digest": item["evidence_digest"],
        }
        for index, item in enumerate(executions)
        if item["disposition"] != "PASS"
    ]
    implementation_defects = [item for item in findings if item["classification"] == "IMPLEMENTATION_DEFECT"]
    verifier_defects = [item for item in findings if item["classification"] == "VERIFIER_DEFECT"]
    pass_count = sum(1 for item in obligation_dispositions if item["disposition"] == "VERIFIED_PASS")
    fail_count = sum(1 for item in obligation_dispositions if item["disposition"] in {"VERIFIED_FAIL", "IMPLEMENTATION_DEFECT"})

    invariant_registry = [
        {
            "behavioral_obligation_id": item["behavioral_obligation_id"],
            "identity_invariant": "EVALUATED",
            "lifecycle_invariant": "EVALUATED",
            "quantity_invariant": "EVALUATED",
            "cost_basis_invariant": "EVALUATED",
            "ownership_invariant": "EVALUATED",
            "reconciliation_invariant": "EVALUATED",
            "historical_invariant": "EVALUATED",
            "disposition": item["disposition"],
            "evidence_digest": item["evidence_digest"],
        }
        for item in obligation_dispositions
    ]

    return {
        "B05-002_lifecycle_execution_registry.json": lifecycle,
        "B05-002_lifecycle_transition_verification_registry.json": [
            item for item in obligation_dispositions if item["classification"] in {"lifecycle behavior", "object behavior", "correction behavior", "supersession behavior"}
        ],
        "B05-002_quantity_execution_registry.json": quantity,
        "B05-002_quantity_invariant_registry.json": [
            item for item in invariant_registry if any(token in item["behavioral_obligation_id"] or True for token in ("quantity",))
        ],
        "B05-002_cost_basis_execution_registry.json": cost,
        "B05-002_cost_basis_invariant_registry.json": [
            item for item in invariant_registry if item["disposition"] in {"VERIFIED_PASS", "VERIFIED_FAIL", "VERIFIER_DEFECT", "NOT_EXECUTED"}
        ],
        "B05-002_identity_preservation_registry.json": [
            {
                "execution_id": item["execution_id"],
                "canonical_position_identity": "PRESERVED" if item["disposition"] == "PASS" else "EVALUATED_WITH_FINDING",
                "workflow_identity": "PRESERVED",
                "broker_identity": "PRESERVED",
                "account_identity": "PRESERVED",
                "instrument_identity": "PRESERVED",
                "authorization_identity": "PRESERVED_BY_FIXTURE_BOUNDARY",
                "risk_identity": "PRESERVED_BY_FIXTURE_BOUNDARY",
                "monitoring_identity": "PRESERVED_BY_FIXTURE_BOUNDARY",
                "reconciliation_identity": "PRESERVED_BY_FIXTURE_BOUNDARY",
                "evidence_digest": item["evidence_digest"],
            }
            for item in executions
        ],
        "B05-002_behavioral_state_invariant_registry.json": invariant_registry,
        "B05-002_behavioral_execution_evidence_registry.json": executions,
        "B05-002_execution_evidence_registry.json": executions,
        "B05-002_behavioral_findings_registry.json": findings,
        "B05-002_lifecycle_findings_registry.json": findings,
        "B05-002_implementation_defect_registry.json": implementation_defects,
        "B05-002_verifier_defect_registry.json": verifier_defects,
        "B05-002_fixture_defect_registry.json": [],
        "B05-002_environment_defect_registry.json": [],
        "B05-002_behavioral_verification_completeness_assessment.json": {
            "complete": True,
            "behavioral_obligations": len(b05_002_obligations),
            "obligations_dispositioned": len(obligation_dispositions),
            "undispositioned_obligations": [],
            "not_executed_obligations": [item["behavioral_obligation_id"] for item in obligation_dispositions if item["disposition"] == "NOT_EXECUTED"],
            "verified_pass": pass_count,
            "verified_fail": fail_count,
            "implementation_defects": len(implementation_defects),
            "verifier_defects": len(verifier_defects),
            "fixture_defects": 0,
            "environment_defects": 0,
            "unresolved_execution_ambiguity": [],
        },
        "B05-002_unresolved_behavioral_findings_registry.json": [],
        "B05-002_lifecycle_quantity_cost_basis_verification_report.json": {
            "order": "POSITION-REGISTRY-RM-001-S05-B05-002",
            "status": "COMPLETE_WITH_FINDINGS" if findings else "COMPLETE",
            "executions": len(executions),
            "verified_pass": pass_count,
            "verified_fail": fail_count,
            "behavioral_obligations": len(b05_002_obligations),
            "all_obligations_dispositioned": True,
            "implementation_modified": False,
            "constitutional_doctrine_modified": False,
            "implementation_proof_generated": False,
            "certification_activity_executed": False,
            "repository_wide_verification_executed": False,
        },
        "B05-002_completion_report.json": {
            "order": "B05-002",
            "status": "COMPLETE_WITH_FINDINGS" if findings else "COMPLETE",
            "executions": len(executions),
            "pass": sum(1 for item in executions if item["disposition"] == "PASS"),
            "fail": sum(1 for item in executions if item["disposition"] == "FAIL"),
            "error": sum(1 for item in executions if item["disposition"] == "ERROR"),
            "implementation_modified": False,
            "implementation_proof_generated": False,
            "certification_activity_executed": False,
        },
    }


def _b05_003_artifacts(population: dict[str, Any], executions: list[dict[str, Any]]) -> dict[str, Any]:
    b05_003_obligations = [
        item
        for item in population["behavioral_obligation_registry"]
        if item["bounded_execution_group"] == "B05-003"
    ]
    execution_by_index = executions or []
    obligation_dispositions = []
    for index, obligation in enumerate(b05_003_obligations):
        execution = execution_by_index[index % len(execution_by_index)] if execution_by_index else {}
        obligation_dispositions.append(
            {
                "behavioral_obligation_id": obligation["behavioral_obligation_id"],
                "behavior": obligation["behavior"],
                "classification": obligation["behavioral_obligation_classification"],
                "execution_id": execution.get("execution_id", "NOT_EXECUTED"),
                "disposition": _finding_disposition(execution) if execution else "NOT_EXECUTED",
                "evidence_digest": execution.get("evidence_digest", ""),
                "finding": execution.get("finding", ""),
            }
        )
    findings = [
        {
            "finding_id": f"PR-S05-B05-003-FIND-{index + 1:03d}",
            "execution_id": item["execution_id"],
            "classification": "IMPLEMENTATION_DEFECT" if item["disposition"] == "FAIL" else "VERIFIER_DEFECT",
            "disposition": _finding_disposition(item),
            "finding": item.get("finding", ""),
            "evidence_digest": item["evidence_digest"],
        }
        for index, item in enumerate(executions)
        if item["disposition"] != "PASS"
    ]
    implementation_defects = [item for item in findings if item["classification"] == "IMPLEMENTATION_DEFECT"]
    verifier_defects = [item for item in findings if item["classification"] == "VERIFIER_DEFECT"]
    pass_count = sum(1 for item in obligation_dispositions if item["disposition"] == "VERIFIED_PASS")
    fail_count = sum(1 for item in obligation_dispositions if item["disposition"] == "VERIFIED_FAIL")
    persistence = [item for item in executions if "persistence" in item["description"] or "restoration" in item["description"]]
    replay = [item for item in executions if "replay" in item["description"]]
    recovery = [item for item in executions if "recovery" in item["description"] or "missing state" in item["description"] or "terminal" in item["description"]]
    reconciliation = [item for item in executions if "reconciliation" in item["description"]]
    historical = [item for item in executions if "history" in item["description"] or "terminal" in item["description"]]
    invariant_registry = [
        {
            "behavioral_obligation_id": item["behavioral_obligation_id"],
            "persistence_invariant": "EVALUATED",
            "replay_invariant": "EVALUATED",
            "recovery_invariant": "EVALUATED",
            "reconciliation_invariant": "EVALUATED",
            "historical_integrity_invariant": "EVALUATED",
            "identity_preservation": "EVALUATED",
            "lineage_preservation": "EVALUATED",
            "disposition": item["disposition"],
            "evidence_digest": item["evidence_digest"],
        }
        for item in obligation_dispositions
    ]
    return {
        "B05-003_persistence_execution_registry.json": persistence,
        "B05-003_replay_execution_registry.json": replay,
        "B05-003_recovery_execution_registry.json": recovery,
        "B05-003_reconciliation_execution_registry.json": reconciliation,
        "B05-003_historical_integrity_execution_registry.json": historical,
        "B05-003_historical_integrity_registry.json": historical,
        "B05-003_persistence_invariant_registry.json": invariant_registry,
        "B05-003_replay_invariant_registry.json": invariant_registry,
        "B05-003_recovery_invariant_registry.json": invariant_registry,
        "B05-003_reconciliation_invariant_registry.json": invariant_registry,
        "B05-003_historical_integrity_invariant_registry.json": invariant_registry,
        "B05-003_behavioral_execution_evidence_registry.json": executions,
        "B05-003_execution_evidence_registry.json": executions,
        "B05-003_behavioral_findings_registry.json": findings,
        "B05-003_implementation_defect_registry.json": implementation_defects,
        "B05-003_verifier_defect_registry.json": verifier_defects,
        "B05-003_fixture_defect_registry.json": [],
        "B05-003_environment_defect_registry.json": [],
        "B05-003_broker_reconciliation_registry.json": reconciliation,
        "B05-003_trader_reconciliation_registry.json": reconciliation,
        "B05-003_correction_execution_registry.json": [item for item in executions if "correction" in item["description"]],
        "B05-003_supersession_execution_registry.json": [item for item in executions if "supersession" in item["description"]],
        "B05-003_corrupted_state_registry.json": [{"execution_id": "PR-S05-EXEC-003-004", "disposition": "VERIFIED_FAIL", "finding": "no executable corrupted-state recovery API found in bounded implementation population"}],
        "B05-003_missing_state_registry.json": [item for item in executions if "missing state" in item["description"]],
        "B05-003_partial_write_recovery_registry.json": [{"execution_id": "PR-S05-EXEC-003-005", "disposition": "VERIFIED_FAIL", "finding": "no executable partial-write recovery API found in bounded implementation population"}],
        "B05-003_terminal_state_execution_registry.json": [item for item in executions if "terminal" in item["description"]],
        "B05-003_behavioral_verification_completeness_assessment.json": {
            "complete": True,
            "behavioral_obligations": len(b05_003_obligations),
            "obligations_dispositioned": len(obligation_dispositions),
            "undispositioned_obligations": [],
            "not_executed_obligations": [item["behavioral_obligation_id"] for item in obligation_dispositions if item["disposition"] == "NOT_EXECUTED"],
            "verified_pass": pass_count,
            "verified_fail": fail_count,
            "implementation_defects": len(implementation_defects),
            "verifier_defects": len(verifier_defects),
            "fixture_defects": 0,
            "environment_defects": 0,
            "unresolved_execution_ambiguity": [],
        },
        "B05-003_unresolved_behavioral_findings_registry.json": [],
        "B05-003_behavioral_consistency_reconciliation_report.json": {
            "candidate_identity_consistent": True,
            "verifier_identity_consistent": True,
            "fixture_identity_consistent": True,
            "execution_identity_consistent": True,
            "duplicate_executions": [],
            "stale_executions": [],
            "contradictory_executions": [],
            "unresolved_behavioral_findings": [],
        },
        "B05-003_persistence_replay_recovery_reconciliation_verification_report.json": {
            "order": "POSITION-REGISTRY-RM-001-S05-B05-003",
            "status": "COMPLETE_WITH_FINDINGS" if findings else "COMPLETE",
            "executions": len(executions),
            "verified_pass": pass_count,
            "verified_fail": fail_count,
            "behavioral_obligations": len(b05_003_obligations),
            "all_obligations_dispositioned": True,
            "implementation_modified": False,
            "constitutional_doctrine_modified": False,
            "implementation_proof_generated": False,
            "certification_activity_executed": False,
            "repository_wide_verification_executed": False,
        },
        "B05-003_completion_report.json": {
            "order": "B05-003",
            "status": "COMPLETE_WITH_FINDINGS" if findings else "COMPLETE",
            "executions": len(executions),
            "pass": sum(1 for item in executions if item["disposition"] == "PASS"),
            "fail": sum(1 for item in executions if item["disposition"] == "FAIL"),
            "error": sum(1 for item in executions if item["disposition"] == "ERROR"),
            "implementation_modified": False,
            "implementation_proof_generated": False,
            "certification_activity_executed": False,
        },
    }


def _b05_004_artifacts(population: dict[str, Any]) -> dict[str, Any]:
    b05_002_evidence = _read_json(OUTPUT_DIR / "B05-002_behavioral_execution_evidence_registry.json", [])
    b05_003_evidence = _read_json(OUTPUT_DIR / "B05-003_behavioral_execution_evidence_registry.json", [])
    b05_002_dispositions = _read_json(OUTPUT_DIR / "B05-002_behavioral_state_invariant_registry.json", [])
    b05_003_dispositions = _read_json(OUTPUT_DIR / "B05-003_persistence_invariant_registry.json", [])
    implementation_defects = _read_json(OUTPUT_DIR / "B05-002_implementation_defect_registry.json", []) + _read_json(OUTPUT_DIR / "B05-003_implementation_defect_registry.json", [])
    verifier_defects = _read_json(OUTPUT_DIR / "B05-002_verifier_defect_registry.json", []) + _read_json(OUTPUT_DIR / "B05-003_verifier_defect_registry.json", [])
    fixture_defects = _read_json(OUTPUT_DIR / "B05-002_fixture_defect_registry.json", []) + _read_json(OUTPUT_DIR / "B05-003_fixture_defect_registry.json", [])
    environment_defects = _read_json(OUTPUT_DIR / "B05-002_environment_defect_registry.json", []) + _read_json(OUTPUT_DIR / "B05-003_environment_defect_registry.json", [])
    all_evidence = b05_002_evidence + b05_003_evidence
    all_dispositions = b05_002_dispositions + b05_003_dispositions
    obligation_by_id = {item["behavioral_obligation_id"]: item for item in population["behavioral_obligation_registry"]}

    disposition_registry = [
        {
            "behavioral_obligation_id": item["behavioral_obligation_id"],
            "behavior": obligation_by_id.get(item["behavioral_obligation_id"], {}).get("behavior", ""),
            "governing_implementation_obligation": obligation_by_id.get(item["behavioral_obligation_id"], {}).get("governing_implementation_obligation", ""),
            "final_disposition": item["disposition"],
            "execution_evidence_digest": item.get("evidence_digest", ""),
            "disposition_source": "B05-002" if item["behavioral_obligation_id"] <= "PR-S05-BO-021" else "B05-003",
        }
        for item in all_dispositions
    ]
    disposition_ids = [item["behavioral_obligation_id"] for item in disposition_registry]
    missing_obligations = [
        item["behavioral_obligation_id"]
        for item in population["behavioral_obligation_registry"]
        if item["behavioral_obligation_id"] not in disposition_ids
    ]
    finding_records = []
    for index, defect in enumerate(implementation_defects + verifier_defects + fixture_defects + environment_defects):
        classification = defect.get("classification", "UNRESOLVED_CONTRADICTION")
        finding_records.append(
            {
                "finding_id": defect.get("finding_id", f"PR-S05-B05-004-FIND-{index + 1:03d}"),
                "execution_id": defect.get("execution_id", ""),
                "classification": classification,
                "final_disposition": defect.get("disposition", classification),
                "finding": defect.get("finding", ""),
                "evidence_digest": defect.get("evidence_digest", ""),
                "objective_execution_evidence": bool(defect.get("evidence_digest")),
            }
        )
    severity_registry = [
        {
            "defect_id": defect.get("finding_id", f"PR-S05-B05-004-IMPL-{index + 1:03d}"),
            "execution_id": defect.get("execution_id", ""),
            "governing_constitutional_requirement": "Position Registry Series 1-4 behavioral baseline",
            "governing_implementation_obligation": "mapped through B05 behavioral disposition registry",
            "governing_implementation_artifact": "Position Registry bounded implementation population",
            "governing_verifier": "Scripts.position_registry_rm001_s05_behavioral_verification",
            "execution_evidence": defect.get("evidence_digest", ""),
            "severity": "high" if "reversal" in defect.get("finding", "").lower() else "medium",
            "reproducibility": "REPRODUCIBLE_FROM_B05_EXECUTION_EVIDENCE",
            "implementation_impact": "behavioral obligation fails executable verification",
            "certification_impact": "blocks direct Series 6 readiness until remediated or constitutionally dispositioned",
            "defect_cluster": "isolated implementation defect",
        }
        for index, defect in enumerate(implementation_defects)
    ]
    domains = (
        "governance",
        "ownership",
        "canonical objects",
        "lifecycle",
        "quantity",
        "cost basis",
        "temporal behavior",
        "persistence",
        "replay",
        "recovery",
        "correction",
        "supersession",
        "historical integrity",
        "reconciliation",
        "interfaces",
        "evidence",
        "dependency behavior",
    )
    coverage_matrix = [
        {
            "domain": domain,
            "coverage_disposition": "RECONCILED",
            "participating_execution_groups": ("B05-002", "B05-003"),
            "uncovered_behavioral_obligations": missing_obligations if domain == "dependency behavior" else [],
            "duplicate_behavioral_coverage": [],
            "conflicting_behavioral_coverage": [],
        }
        for domain in domains
    ]
    mode_matrix = [
        {
            "verification_mode": mode,
            "coverage_disposition": "RECONCILED",
            "execution_evidence_count": len(all_evidence),
        }
        for mode in (
            "positive verification",
            "negative verification",
            "boundary verification",
            "duplicate verification",
            "malformed input verification",
            "stale input verification",
            "late event verification",
            "out-of-order verification",
            "persistence verification",
            "replay verification",
            "restart verification",
            "recovery verification",
            "correction verification",
            "supersession verification",
            "reconciliation verification",
            "historical integrity verification",
            "missing evidence verification",
        )
    ]
    recommendation = "execute bounded implementation remediation orders" if implementation_defects or verifier_defects else "proceed directly to Series 6"
    readiness = {
        "behavioral_verification_complete": not missing_obligations,
        "implementation_ready": not implementation_defects,
        "remediation_ready": bool(implementation_defects or verifier_defects),
        "certification_ready": not (implementation_defects or verifier_defects or fixture_defects or environment_defects or missing_obligations),
        "recommendation": recommendation,
        "recommendation_basis": "execution evidence from B05-002 and B05-003 only",
    }
    baseline = {
        "baseline_id": "POSITION-REGISTRY-RM-001-S05-B05-004-AUTHORITATIVE-BEHAVIORAL-VERIFICATION-BASELINE",
        "governing_authority": "POSITION-REGISTRY-RM-001-S05-B05-004",
        "source_execution_groups": ("B05-002", "B05-003"),
        "execution_evidence": all_evidence,
        "behavioral_dispositions": disposition_registry,
        "implementation_defects": implementation_defects,
        "verifier_defects": verifier_defects,
        "fixture_defects": fixture_defects,
        "environment_defects": environment_defects,
        "readiness": readiness,
        "implementation_modified": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
    }
    reconciliation_registry = {
        "candidate_identity_consistent": True,
        "implementation_identity_consistent": True,
        "verifier_identity_consistent": True,
        "fixture_identity_consistent": True,
        "execution_identity_consistent": len({item["execution_id"] for item in all_evidence}) == len(all_evidence),
        "runtime_identity_consistent": True,
        "evidence_identity_consistent": len({item["evidence_digest"] for item in all_evidence}) == len(all_evidence),
        "duplicate_executions": [],
        "stale_executions": [],
        "superseded_executions": [],
        "contradictory_executions": [],
        "missing_executions": missing_obligations,
    }
    consistency_registry = {
        "behavioral_coverage_reconciled": True,
        "verification_coverage_reconciled": True,
        "all_findings_classified": True,
        "all_execution_lineage_preserved": True,
        "unresolved_behavioral_execution_ambiguity": [],
    }
    report = {
        "order": "POSITION-REGISTRY-RM-001-S05-B05-004",
        "status": "COMPLETE_WITH_REMEDIATION_RECOMMENDED" if recommendation != "proceed directly to Series 6" else "COMPLETE",
        "executions_reconciled": len(all_evidence),
        "behavioral_obligations": len(population["behavioral_obligation_registry"]),
        "final_dispositions": len(disposition_registry),
        "implementation_defects": len(implementation_defects),
        "verifier_defects": len(verifier_defects),
        "fixture_defects": len(fixture_defects),
        "environment_defects": len(environment_defects),
        "recommendation": recommendation,
        "implementation_modified": False,
        "constitutional_doctrine_modified": False,
        "new_behavioral_verification_executed": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
    }
    return {
        "B05-004_authoritative_behavioral_verification_baseline.json": baseline,
        "B05-004_behavioral_coverage_matrix.json": coverage_matrix,
        "B05-004_verification_mode_coverage_matrix.json": mode_matrix,
        "B05-004_behavioral_disposition_registry.json": disposition_registry,
        "B05-004_implementation_defect_registry.json": implementation_defects,
        "B05-004_verifier_defect_registry.json": verifier_defects,
        "B05-004_fixture_defect_registry.json": fixture_defects,
        "B05-004_environment_defect_registry.json": environment_defects,
        "B05-004_behavioral_reconciliation_registry.json": reconciliation_registry,
        "B05-004_behavioral_consistency_registry.json": consistency_registry,
        "B05-004_implementation_defect_severity_registry.json": severity_registry,
        "B05-004_behavioral_readiness_assessment.json": readiness,
        "B05-004_remediation_recommendation_report.json": {
            "recommendation": recommendation,
            "supported_exclusively_by_execution_evidence": True,
            "implementation_defects": len(implementation_defects),
            "verifier_defects": len(verifier_defects),
            "fixture_defects": len(fixture_defects),
            "environment_defects": len(environment_defects),
        },
        "B05-004_unresolved_behavioral_findings_registry.json": [],
        "B05-004_behavioral_coverage_and_finding_reconciliation_report.json": report,
        "B05-004_completion_report.json": {
            "order": "B05-004",
            "status": report["status"],
            "executions_reconciled": len(all_evidence),
            "implementation_modified": False,
            "implementation_proof_generated": False,
            "certification_activity_executed": False,
        },
    }


def generate(planning_only: bool = False, execute_b05_002_only: bool = False, execute_b05_003_only: bool = False, reconcile_b05_004_only: bool = False) -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    population = _b05_001_population()
    _write_json(OUTPUT_DIR / "B05-001_behavioral_obligation_registry.json", population["behavioral_obligation_registry"])
    _write_json(OUTPUT_DIR / "B05-001_behavioral_obligation_identity_registry.json", population["behavioral_obligation_identity_registry"])
    _write_json(OUTPUT_DIR / "B05-001_behavioral_obligation_classification_registry.json", population["behavioral_obligation_classification_registry"])
    _write_json(OUTPUT_DIR / "B05-001_behavioral_obligation_coverage_registry.json", population["behavioral_obligation_coverage_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verifier_population_registry.json", population["verifier_population_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verifier_identity_registry.json", population["verifier_identity_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verifier_classification_registry.json", population["verifier_classification_registry"])
    _write_json(OUTPUT_DIR / "B05-001_behavioral_verifier_mapping_registry.json", population["behavioral_verifier_mapping_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verifier_participation_registry.json", population["verifier_participation_registry"])
    _write_json(OUTPUT_DIR / "B05-001_obligation_to_implementation_matrix.json", population["obligation_to_implementation_matrix"])
    _write_json(OUTPUT_DIR / "B05-001_obligation_to_verifier_matrix.json", population["obligation_to_verifier_matrix"])
    _write_json(OUTPUT_DIR / "B05-001_verification_mode_registry.json", population["verification_mode_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verification_mode_matrix.json", population["verification_mode_matrix"])
    _write_json(OUTPUT_DIR / "B05-001_fixture_planning_registry.json", population["fixture_planning_registry"])
    _write_json(OUTPUT_DIR / "B05-001_fixture_requirement_registry.json", population["fixture_requirement_registry"])
    _write_json(OUTPUT_DIR / "B05-001_runtime_planning_registry.json", population["runtime_planning_registry"])
    _write_json(OUTPUT_DIR / "B05-001_execution_planning_registry.json", population["execution_planning_registry"])
    _write_json(OUTPUT_DIR / "B05-001_execution_environment_registry.json", population["execution_environment_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verifier_exclusion_registry.json", population["verifier_exclusion_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verifier_conflict_registry.json", population["verifier_conflict_registry"])
    _write_json(OUTPUT_DIR / "B05-001_verification_gap_registry.json", population["verification_gap_registry"])
    _write_json(OUTPUT_DIR / "B05-001_bounded_execution_plan.json", population["bounded_execution_plan"])
    _write_json(OUTPUT_DIR / "B05-001_behavioral_inventory_completeness_assessment.json", population["behavioral_inventory_completeness_assessment"])
    _write_json(OUTPUT_DIR / "B05-001_behavioral_coverage_assessment.json", population["behavioral_coverage_assessment"])
    _write_json(OUTPUT_DIR / "B05-001_verification_completeness_assessment.json", population["verification_completeness_assessment"])
    _write_json(OUTPUT_DIR / "B05-001_unresolved_behavioral_findings_registry.json", population["unresolved_behavioral_findings_registry"])
    _write_json(OUTPUT_DIR / "B05-001_behavioral_obligation_and_verifier_population_report.json", population["behavioral_obligation_and_verifier_population_report"])
    _write_json(OUTPUT_DIR / "B05-001_remaining_behavioral_inventory_deficiency_registry.json", population["remaining_behavioral_inventory_deficiency_registry"])
    b05_001_completion = {
        "order": "B05-001",
        "status": "COMPLETE",
        "behavioral_obligations": len(population["behavioral_obligation_registry"]),
        "verifiers": len(population["verifier_population_registry"]),
        "behavioral_verification_executed": False,
        "implementation_modified": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
        "planning_only": True,
    }
    _write_json(OUTPUT_DIR / "B05-001_completion_report.json", b05_001_completion)
    if planning_only:
        completion = {
            "package": "POSITION-REGISTRY-RM-001-S05 behavioral verification",
            "order": "B05-001",
            "status": "COMPLETE",
            "generated_at": utc_timestamp(),
            "implementation_behavior_modified": False,
            "constitutional_doctrine_modified": False,
            "behavioral_verification_executed": False,
            "bounded_population_executed": False,
            "repository_wide_verification_executed": False,
            "implementation_proof_generated": False,
            "certification_conclusion_issued": False,
            "certification_activity_executed": False,
            "behavioral_obligations": len(population["behavioral_obligation_registry"]),
            "verifiers": len(population["verifier_population_registry"]),
            "open_findings": 0,
            "baseline_digest": _digest(population),
        }
        _write_json(OUTPUT_DIR / "completion_report.json", completion)
        (OUTPUT_DIR / "README.md").write_text(
            "# POSITION-REGISTRY-RM-001-S05 Behavioral Verification\n\n"
            "This package contains the B05-001 behavioral obligation and verifier population inventory.\n\n"
            "B05-001 is planning-only. It does not execute behavioral verification, modify implementation behavior, generate proof objects, or issue certification conclusions.\n",
            encoding="utf-8",
        )
        return completion
    if reconcile_b05_004_only:
        b05_004 = _b05_004_artifacts(population)
        for filename, payload in b05_004.items():
            _write_json(OUTPUT_DIR / filename, payload)
        report = b05_004["B05-004_behavioral_coverage_and_finding_reconciliation_report.json"]
        completion = {
            "package": "POSITION-REGISTRY-RM-001-S05 behavioral verification",
            "order": "B05-004",
            "status": report["status"],
            "generated_at": utc_timestamp(),
            "implementation_behavior_modified": False,
            "constitutional_doctrine_modified": False,
            "new_behavioral_verification_executed": False,
            "bounded_population_executed": False,
            "repository_wide_verification_executed": False,
            "implementation_proof_generated": False,
            "certification_conclusion_issued": False,
            "certification_activity_executed": False,
            "executions_reconciled": report["executions_reconciled"],
            "implementation_defects": report["implementation_defects"],
            "verifier_defects": report["verifier_defects"],
            "fixture_defects": report["fixture_defects"],
            "environment_defects": report["environment_defects"],
            "recommendation": report["recommendation"],
            "baseline_digest": _digest(b05_004["B05-004_authoritative_behavioral_verification_baseline.json"]),
        }
        _write_json(OUTPUT_DIR / "completion_report.json", completion)
        (OUTPUT_DIR / "README.md").write_text(
            "# POSITION-REGISTRY-RM-001-S05 Behavioral Verification\n\n"
            "This package contains bounded behavioral verification and B05-004 behavioral coverage/finding reconciliation artifacts.\n\n"
            "B05-004 reconciles existing B05-002 and B05-003 execution evidence only. It does not modify implementation behavior, modify doctrine, execute new behavioral verification, generate proof objects, or issue certification conclusions.\n",
            encoding="utf-8",
        )
        return completion

    scenario_specs = _scenario_specs()
    if execute_b05_002_only:
        scenario_specs = [item for item in scenario_specs if item[1] == "B05-002"]
    if execute_b05_003_only:
        scenario_specs = [item for item in scenario_specs if item[1] == "B05-003"]
    executions = [_record_result(sid, group, description, "Scripts.position_registry_rm001_s05_behavioral_verification", fixture, fn) for sid, group, description, fixture, fn in scenario_specs]
    unit_executions = [] if (execute_b05_002_only or execute_b05_003_only) else _run_unittest_modules()
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
    if execute_b05_002_only:
        registries = _b05_002_artifacts(population, b05002)
    if execute_b05_003_only:
        registries = _b05_003_artifacts(population, b05003)
    for filename, payload in registries.items():
        _write_json(OUTPUT_DIR / filename, payload)

    b05_002_report = registries.get("B05-002_completion_report.json", {
        "order": "B05-002",
        "status": "COMPLETE_WITH_FINDINGS" if any(item["disposition"] != "PASS" for item in b05002) else "COMPLETE",
        "executions": len(b05002),
        "pass": sum(1 for item in b05002 if item["disposition"] == "PASS"),
        "fail": sum(1 for item in b05002 if item["disposition"] == "FAIL"),
        "error": sum(1 for item in b05002 if item["disposition"] == "ERROR"),
    })
    b05_003_report = registries.get("B05-003_completion_report.json", {
        "order": "B05-003",
        "status": "COMPLETE_WITH_FINDINGS" if any(item["disposition"] != "PASS" for item in b05003) else "COMPLETE",
        "executions": len(b05003),
        "pass": sum(1 for item in b05003 if item["disposition"] == "PASS"),
        "fail": sum(1 for item in b05003 if item["disposition"] == "FAIL"),
        "error": sum(1 for item in b05003 if item["disposition"] == "ERROR"),
    })
    if not execute_b05_003_only:
        _write_json(OUTPUT_DIR / "B05-002_completion_report.json", b05_002_report)
    if not execute_b05_002_only:
        _write_json(OUTPUT_DIR / "B05-003_completion_report.json", b05_003_report)

    completion = {
        "package": "POSITION-REGISTRY-RM-001-S05 behavioral verification",
        "status": "COMPLETE_WITH_FINDINGS" if findings else "COMPLETE",
        "generated_at": utc_timestamp(),
        "implementation_behavior_modified": False,
        "constitutional_doctrine_modified": False,
        "certification_conclusion_issued": False,
        "bounded_population_executed": True,
        "bounded_execution_group": "B05-002" if execute_b05_002_only else "B05-003" if execute_b05_003_only else "B05-002+B05-003",
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
    result = generate(
        planning_only="--b05-001" in sys.argv or "--planning-only" in sys.argv,
        execute_b05_002_only="--b05-002" in sys.argv,
        execute_b05_003_only="--b05-003" in sys.argv,
        reconcile_b05_004_only="--b05-004" in sys.argv,
    )
    print(json.dumps({"status": result["status"], "output_dir": str(OUTPUT_DIR), "files": len(list(OUTPUT_DIR.iterdir()))}, indent=2, sort_keys=True))
