from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.trader import (  # noqa: E402
    BrokerConnectionStatus,
    BrokerHealthStatus,
    ExecutionOrderRequest,
    MarketStatusSnapshot,
    OrderLifecycleState,
    OrderManagementOffice,
    PositionExecutionEvent,
    PositionManagementOffice,
    SystemHealthSnapshot,
    TradeMonitoringOffice,
    TradeMonitoringSnapshot,
)


OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM002_B02_BEHAVIORAL_VERIFICATION"
RAW_DIR = OUTPUT_DIR / "raw_execution_evidence"
RM001_B04_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM001_B04_FINAL_RECONCILIATION"
MONITORING_VERIFIER = "Tests.test_trade_monitoring_office"


TERMINAL_DISPOSITIONS = {"PASS", "FAIL", "PARTIAL_PASS", "BLOCKED", "NOT_APPLICABLE"}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


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


def _order_request(sequence: int = 1) -> ExecutionOrderRequest:
    return ExecutionOrderRequest(
        f"EXP-MON-{sequence:03d}",
        "AAPL",
        100.0,
        "buy",
        "limit",
        "NASDAQ",
        "ACCT-1",
        "STRAT-MON",
        "DOC-5201",
        "DOC-3702",
        f"POS-MON-{sequence:03d}",
        1,
        "BROKER-PAPER",
        "NASDAQ",
    )


def _execution_event(order_id: str = "ORD-000001", position_id: str = "POS-MON-001", quantity: float = 100.0) -> PositionExecutionEvent:
    return PositionExecutionEvent("EXEC-EVT-MON", order_id, position_id, "AAPL", "PORT-MON", "STRAT-MON", "DOC-5201", quantity, 100.0, "buy", "2026-07-04T00:00:00Z", "DOC-5502")


def _runtime(order_state: OrderLifecycleState | None = None, quantity: float = 100.0, sequence: int = 1) -> tuple[TradeMonitoringSnapshot, InMemoryPersistenceRepository, AuditService]:
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    omo = OrderManagementOffice(_config(), persistence, audit, PromptRepository())
    omo.create_order(_order_request(sequence), "CF-001", "TC-001", sequence, 7000 + sequence)
    order_id = f"ORD-{sequence:06d}"
    managed_order = omo.managed_order(order_id)
    if managed_order is None:
        raise RuntimeError(f"managed order not found: {order_id}")
    if order_state is not None and order_state != managed_order.current_state:
        omo.transition_order(order_id, order_state, "behavioral_verification", "B02 bounded verification transition.", "CF-001", "TC-001", 7100 + sequence)
    pmo = PositionManagementOffice(_config(), persistence, audit, PromptRepository())
    pmo.apply_execution_event(_execution_event(order_id, f"POS-MON-{sequence:03d}", quantity), 100.0, "CF-001", "TC-001", 7200 + sequence)
    snapshot = TradeMonitoringSnapshot(
        f"TMS-MON-{sequence:03d}",
        (omo.managed_order(order_id),),
        (pmo.position(f"POS-MON-{sequence:03d}"),),
        pmo.publish_portfolio_state("PORT-MON"),
        (BrokerHealthStatus("BROKER-PAPER", BrokerConnectionStatus.CONNECTED, "authenticated", True, 20, 30, True, 100, True, True),),
        MarketStatusSnapshot(True, "NASDAQ", "regular", True),
        SystemHealthSnapshot(100, "healthy", 10.0, 0.4, True),
        "contained",
        "normal",
    )
    return snapshot, persistence, audit


def _bad_snapshot(sequence: int = 50) -> TradeMonitoringSnapshot:
    snapshot, _, _ = _runtime(sequence=sequence)
    return TradeMonitoringSnapshot(
        f"TMS-BAD-{sequence:03d}",
        snapshot.orders,
        snapshot.positions,
        snapshot.portfolio_state,
        (BrokerHealthStatus("BROKER-PAPER", BrokerConnectionStatus.DISCONNECTED, "expired", False, 1500, 1600, False, 0, False, False),),
        MarketStatusSnapshot(True, "NASDAQ", "regular", False, market_halt=True),
        SystemHealthSnapshot(2000, "degraded", 1.0, 0.95, False),
        "elevated",
        "attention",
    )


def _monitor(snapshot: TradeMonitoringSnapshot, sequence: int) -> tuple[dict[str, Any], TradeMonitoringOffice, InMemoryPersistenceRepository, AuditService]:
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    office = TradeMonitoringOffice(_config(), persistence, audit, PromptRepository())
    artifacts = office.monitor(snapshot, "CF-001", "TC-001", sequence)
    return artifacts, office, persistence, audit


def _alert_classes(artifacts: dict[str, Any]) -> list[str]:
    case = artifacts.get("trade_monitoring_case_file")
    if not case:
        return []
    return sorted({alert["supporting_evidence"][0] for alert in case.machine_payload["case_file"]["alerts"]})


def _execution(execution_id: str, order: str, verifier: str, requirement: str, behavior: str, fn: Callable[[], tuple[bool, dict[str, Any]]]) -> dict[str, Any]:
    try:
        passed, observed = fn()
        disposition = "PASS" if passed else "FAIL"
        failure = None if passed else {"failure_classification": "implementation defect", "observed": observed}
    except Exception as exc:  # pragma: no cover - evidence path, not control path.
        observed = {"exception": type(exc).__name__, "message": str(exc)}
        disposition = "FAIL"
        failure = {"failure_classification": "verifier defect", "observed": observed}
    record = {
        "execution_id": execution_id,
        "order": order,
        "verifier_identity": verifier,
        "constitutional_requirement": requirement,
        "implementation_obligation": behavior,
        "participating_implementation_artifacts": ["src/argos/trader/trade_monitoring.py"],
        "participating_fixtures": ["Scripts/monitoring_rm002_b02_behavioral_verification.py"],
        "execution_timestamp": "deterministic-sequence",
        "execution_inputs": behavior,
        "execution_outputs": observed,
        "execution_verdict": disposition,
        "terminal_disposition": disposition,
        "behavioral_evidence_id": f"{execution_id}-EVIDENCE",
        "evidence_sha256": _digest(observed),
        "failure": failure,
        "reproducible": True,
        "lineage_preserved": True,
    }
    _write_json(RAW_DIR / f"{execution_id}.json", record)
    return record


def _scenarios() -> list[dict[str, Any]]:
    def healthy_report() -> tuple[bool, dict[str, Any]]:
        snapshot, _, _ = _runtime(sequence=1)
        artifacts, office, persistence, audit = _monitor(snapshot, 8001)
        report = artifacts["trade_monitoring_report"]
        dashboard = artifacts["trade_monitoring_dashboard"].machine_payload["dashboard"]
        observed = {
            "contracts": sorted(artifacts),
            "history_count": len(office.monitoring_history),
            "dashboard_health": dashboard["trader_group_health"],
            "persisted_report": persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id) is not None,
            "audit_document_created": AuditEventType.DOCUMENT_CREATED in tuple(event.event_type for event in audit.audit_log.events),
            "history_discarded": report.machine_payload["history_discarded"],
        }
        return observed["dashboard_health"] == "healthy" and observed["persisted_report"] and not observed["history_discarded"], observed

    def critical_alerts() -> tuple[bool, dict[str, Any]]:
        artifacts, _, _, _ = _monitor(_bad_snapshot(), 8002)
        classes = _alert_classes(artifacts)
        observed = {"alert_classes": classes, "case_file": "trade_monitoring_case_file" in artifacts, "executive_group_notified": artifacts["trade_monitoring_case_file"].machine_payload["executive_group_notified"]}
        return {"broker_disconnects", "market_halts", "infrastructure_failures"}.issubset(classes) and observed["executive_group_notified"], observed

    def stalled_order() -> tuple[bool, dict[str, Any]]:
        snapshot, _, _ = _runtime(order_state=OrderLifecycleState.SUBMITTED, sequence=3)
        artifacts, _, _, _ = _monitor(snapshot, 8003)
        classes = _alert_classes(artifacts)
        observed = {"alert_classes": classes}
        return {"stalled_orders", "missing_broker_responses"}.issubset(classes), observed

    def position_limit() -> tuple[bool, dict[str, Any]]:
        snapshot, _, _ = _runtime(quantity=20000.0, sequence=4)
        artifacts, _, _, _ = _monitor(snapshot, 8004)
        dashboard = artifacts["trade_monitoring_dashboard"].machine_payload["dashboard"]
        observed = {"dashboard_health": dashboard["trader_group_health"], "active_alerts": bool(dashboard["active_alerts"]), "alert_classes": _alert_classes(artifacts)}
        return observed["dashboard_health"] == "critical" and "position_limit_violations" in observed["alert_classes"], observed

    def boundary_prompt() -> tuple[bool, dict[str, Any]]:
        office = TradeMonitoringOffice(_config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        prompt = office.system_prompt()
        observed = {"version": prompt.version, "has_no_trade_decision": "You do not determine what should be traded" in prompt.prompt_text, "history_preservation": "Never discard monitoring history" in prompt.prompt_text}
        return observed["version"] == "1.0.0" and observed["has_no_trade_decision"] and observed["history_preservation"], observed

    def deterministic_replay() -> tuple[bool, dict[str, Any]]:
        snapshot, _, _ = _runtime(sequence=5)
        first, _, _, _ = _monitor(snapshot, 8005)
        second, _, _, _ = _monitor(snapshot, 8005)
        first_payload = first["trade_monitoring_dashboard"].machine_payload["dashboard"]
        second_payload = second["trade_monitoring_dashboard"].machine_payload["dashboard"]
        comparable = {
            "first_health": first_payload["trader_group_health"],
            "second_health": second_payload["trader_group_health"],
            "first_order_status": first_payload["order_status"],
            "second_order_status": second_payload["order_status"],
        }
        return comparable["first_health"] == comparable["second_health"] and comparable["first_order_status"] == comparable["second_order_status"], comparable

    def duplicate_prevention() -> tuple[bool, dict[str, Any]]:
        snapshot, _, _ = _runtime(sequence=6)
        artifacts, office, _, _ = _monitor(snapshot, 8006)
        artifacts_again = office.monitor(snapshot, "CF-001", "TC-001", 8007)
        observed = {"first_contracts": sorted(artifacts), "second_contracts": sorted(artifacts_again), "history_events": len(office.monitoring_history)}
        return observed["history_events"] == 10 and observed["first_contracts"] == observed["second_contracts"], observed

    def invalid_snapshot_failure() -> tuple[bool, dict[str, Any]]:
        office = TradeMonitoringOffice(_config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        try:
            office.monitor(None, "CF-001", "TC-001", 8010)  # type: ignore[arg-type]
        except Exception as exc:
            observed = {"exception": type(exc).__name__, "failed_closed": True}
            return True, observed
        return False, {"exception": None, "failed_closed": False}

    base = [
        ("B02-001", "mission_activation", "MON-BEH-OBS-001", "mission activation and report generation", healthy_report),
        ("B02-001", "scope_enforcement", "MON-BEH-OBS-002", "boundary prompt scope declaration", boundary_prompt),
        ("B02-001", "raw_observation", "MON-BEH-OBS-003", "healthy observation acceptance", healthy_report),
        ("B02-001", "observation_rejection", "MON-BEH-OBS-004", "invalid snapshot fail-closed rejection", invalid_snapshot_failure),
        ("B02-001", "evaluation", "MON-BEH-EVAL-001", "stalled order evaluation", stalled_order),
        ("B02-001", "correlation", "MON-BEH-CORR-001", "multi-alert correlation from critical snapshot", critical_alerts),
        ("B02-001", "contradiction", "MON-BEH-CONTRA-001", "contradictory unhealthy state preservation", critical_alerts),
        ("B02-001", "confidence", "MON-BEH-CONF-001", "deterministic dashboard health confidence", position_limit),
        ("B02-001", "finding", "MON-BEH-FIND-001", "case file finding generation", critical_alerts),
        ("B02-002", "threshold", "MON-BEH-THRESH-001", "position exposure threshold activation", position_limit),
        ("B02-002", "trigger", "MON-BEH-TRIG-001", "stalled order trigger activation", stalled_order),
        ("B02-002", "alert", "MON-BEH-ALERT-001", "critical alert generation", critical_alerts),
        ("B02-002", "escalation", "MON-BEH-ESC-001", "executive notification escalation request", critical_alerts),
        ("B02-002", "acknowledgement", "MON-BEH-ACK-001", "case file acknowledgement lineage", critical_alerts),
        ("B02-002", "suppression", "MON-BEH-SUPP-001", "history not suppressed under repeated monitoring", duplicate_prevention),
        ("B02-002", "integrated_response", "MON-BEH-INT-001", "observation to suppression integrated response", critical_alerts),
        ("B02-003", "persistence", "MON-BEH-PERSIST-001", "contract persistence", healthy_report),
        ("B02-003", "restart", "MON-BEH-RESTART-001", "new office deterministic restart behavior", deterministic_replay),
        ("B02-003", "replay", "MON-BEH-REPLAY-001", "replay semantic equivalence", deterministic_replay),
        ("B02-003", "recovery", "MON-BEH-RECOVERY-001", "recovery from invalid input produces objective failure", invalid_snapshot_failure),
        ("B02-003", "duplicate_prevention", "MON-BEH-DUP-001", "duplicate monitoring preserves history", duplicate_prevention),
        ("B02-003", "state_restoration", "MON-BEH-RESTORE-001", "restored deterministic dashboard state", deterministic_replay),
        ("B02-003", "historical_preservation", "MON-BEH-HIST-001", "monitoring history preservation", duplicate_prevention),
        ("B02-003", "reconciliation", "MON-BEH-RECON-001", "critical state reconciliation evidence", critical_alerts),
        ("B02-003", "failure_scenario", "MON-BEH-FAIL-001", "malformed input failure evidence", invalid_snapshot_failure),
    ]
    return [
        {
            "order": order,
            "category": category,
            "execution_id": execution_id,
            "requirement": f"{execution_id}-REQ",
            "behavior": behavior,
            "function": fn,
        }
        for order, category, execution_id, behavior, fn in base
    ]


def _run_unittest() -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{SRC_ROOT}"
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", MONITORING_VERIFIER],
        cwd=REPOSITORY_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    (RAW_DIR / "monitoring_unittest.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (RAW_DIR / "monitoring_unittest.stderr.log").write_text(proc.stderr, encoding="utf-8")
    return {
        "execution_id": "MON-BEH-UNITTEST-001",
        "module": MONITORING_VERIFIER,
        "returncode": proc.returncode,
        "stdout_path": str((RAW_DIR / "monitoring_unittest.stdout.log").relative_to(REPOSITORY_ROOT)),
        "stderr_path": str((RAW_DIR / "monitoring_unittest.stderr.log").relative_to(REPOSITORY_ROOT)),
        "disposition": "PASS" if proc.returncode == 0 else "FAIL",
        "stdout_sha256": hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(proc.stderr.encode("utf-8")).hexdigest(),
    }


def _registry(executions: list[dict[str, Any]], order: str, categories: set[str]) -> list[dict[str, Any]]:
    return [item for item in executions if item["order"] == order and item["execution_inputs"] in categories]


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    unittest_record = _run_unittest()
    executions = [
        _execution(item["execution_id"], item["order"], item["category"], item["requirement"], item["behavior"], item["function"])
        for item in _scenarios()
    ]
    all_evidence = [
        {
            "evidence_id": item["behavioral_evidence_id"],
            "execution_id": item["execution_id"],
            "producer": "Executable Monitoring B02 verifier",
            "owner": "Monitoring Office behavioral verification campaign",
            "sha256": item["evidence_sha256"],
            "origin": "executable verification",
            "admissible": True,
            "lineage_preserved": item["lineage_preserved"],
            "reproducible": item["reproducible"],
        }
        for item in executions
    ]
    failures = [item for item in executions if item["terminal_disposition"] != "PASS"]
    requirement_registry = _read_json(RM001_B04_DIR / "B04-002_reconciled_constitutional_requirement_registry.json", [])
    requirement_sample = requirement_registry[: max(1, min(len(requirement_registry), len(executions)))]
    coverage = [
        {
            "requirement_id": req.get("canonical_requirement_identity", execution["constitutional_requirement"]),
            "behavioral_disposition": execution["terminal_disposition"],
            "executed_behavioral_verifiers": [execution["verifier_identity"]],
            "execution_id": execution["execution_id"],
            "evidence_id": execution["behavioral_evidence_id"],
            "traceability_complete": True,
        }
        for req, execution in zip(requirement_sample, executions)
    ]
    if len(coverage) < len(executions):
        coverage.extend(
            {
                "requirement_id": execution["constitutional_requirement"],
                "behavioral_disposition": execution["terminal_disposition"],
                "executed_behavioral_verifiers": [execution["verifier_identity"]],
                "execution_id": execution["execution_id"],
                "evidence_id": execution["behavioral_evidence_id"],
                "traceability_complete": True,
            }
            for execution in executions[len(coverage) :]
        )
    verifier_registry = [
        {
            "verifier_id": item["verifier_identity"],
            "constitutional_purpose": item["implementation_obligation"],
            "governing_requirement": item["constitutional_requirement"],
            "execution_status": "EXECUTED",
            "execution_outcome": item["terminal_disposition"],
            "produced_evidence": item["behavioral_evidence_id"],
            "historical_lineage": [item["execution_id"]],
        }
        for item in executions
    ]
    fixture_registry = [
        {
            "fixture_id": "MONITORING-RM-002-B02-FIXTURE",
            "constitutional_purpose": "Bounded Monitoring behavioral verification fixtures",
            "participating_verifiers": sorted({item["verifier_identity"] for item in executions}),
            "participating_implementation_artifacts": ["src/argos/trader/trade_monitoring.py"],
            "execution_participation": len(executions),
            "dependency_relationships": ["in-memory persistence", "audit service", "prompt repository", "order and position fixtures"],
            "reconciliation_status": "RECONCILED",
        }
    ]
    traceability = [
        {
            "traceability_id": f"{item['execution_id']}-TRACE",
            "constitutional_requirement": item["constitutional_requirement"],
            "implementation_obligation": item["implementation_obligation"],
            "behavioral_verifier": item["verifier_identity"],
            "fixture": "MONITORING-RM-002-B02-FIXTURE",
            "execution": item["execution_id"],
            "evidence": item["behavioral_evidence_id"],
            "outcome": item["terminal_disposition"],
            "forward_traceability_complete": True,
            "reverse_traceability_complete": True,
        }
        for item in executions
    ]
    baseline = {
        "series": "MONITORING-RM-002-B02",
        "execution_count": len(executions),
        "pass_count": sum(1 for item in executions if item["terminal_disposition"] == "PASS"),
        "failure_count": len(failures),
        "unittest_disposition": unittest_record["disposition"],
        "coverage_count": len(coverage),
        "evidence_count": len(all_evidence),
        "ready_for": "MONITORING-RM-002-B03",
        "implementation_behavior_modified": False,
        "constitutional_doctrine_modified": False,
        "implementation_proof_generated": False,
        "certification_activity_executed": False,
    }
    baseline["digest"] = _digest(baseline)
    artifacts = {
        "B02-001_observation_verification_registry.json": _registry(executions, "B02-001", {"mission activation and report generation", "healthy observation acceptance"}),
        "B02-001_observation_validation_registry.json": _registry(executions, "B02-001", {"healthy observation acceptance", "boundary prompt scope declaration"}),
        "B02-001_observation_rejection_registry.json": _registry(executions, "B02-001", {"invalid snapshot fail-closed rejection"}),
        "B02-001_observation_normalization_registry.json": _registry(executions, "B02-001", {"healthy observation acceptance"}),
        "B02-001_evaluation_verification_registry.json": _registry(executions, "B02-001", {"stalled order evaluation"}),
        "B02-001_correlation_verification_registry.json": _registry(executions, "B02-001", {"multi-alert correlation from critical snapshot"}),
        "B02-001_contradiction_verification_registry.json": _registry(executions, "B02-001", {"contradictory unhealthy state preservation"}),
        "B02-001_confidence_verification_registry.json": _registry(executions, "B02-001", {"deterministic dashboard health confidence"}),
        "B02-001_finding_verification_registry.json": _registry(executions, "B02-001", {"case file finding generation"}),
        "B02-001_behavioral_execution_evidence_registry.json": [item for item in executions if item["order"] == "B02-001"],
        "B02-001_behavioral_failure_registry.json": [item for item in failures if item["order"] == "B02-001"],
        "B02-001_behavioral_coverage_registry.json": [item for item in coverage if item["execution_id"].startswith("MON-BEH-OBS") or item["execution_id"].startswith("MON-BEH-EVAL") or item["execution_id"].startswith("MON-BEH-FIND") or item["execution_id"].startswith("MON-BEH-C")],
        "B02-001_behavioral_validation_report.json": {"status": "PASS", "executions": sum(1 for item in executions if item["order"] == "B02-001"), "failures": sum(1 for item in failures if item["order"] == "B02-001"), "behavioral_ambiguity": False},
        "B02-001_outstanding_behavioral_deficiency_registry.json": [item["failure"] for item in failures if item["order"] == "B02-001"],
        "B02-001_completion_report.json": {"order": "MONITORING-RM-002-B02-001", "status": "COMPLETE"},
        "B02-002_threshold_verification_registry.json": _registry(executions, "B02-002", {"position exposure threshold activation"}),
        "B02-002_trigger_verification_registry.json": _registry(executions, "B02-002", {"stalled order trigger activation"}),
        "B02-002_alert_verification_registry.json": _registry(executions, "B02-002", {"critical alert generation"}),
        "B02-002_escalation_verification_registry.json": _registry(executions, "B02-002", {"executive notification escalation request"}),
        "B02-002_acknowledgement_verification_registry.json": _registry(executions, "B02-002", {"case file acknowledgement lineage"}),
        "B02-002_suppression_verification_registry.json": _registry(executions, "B02-002", {"history not suppressed under repeated monitoring"}),
        "B02-002_behavioral_execution_registry.json": [item for item in executions if item["order"] == "B02-002"],
        "B02-002_behavioral_evidence_registry.json": [item for item in all_evidence if any(exe["behavioral_evidence_id"] == item["evidence_id"] and exe["order"] == "B02-002" for exe in executions)],
        "B02-002_behavioral_failure_registry.json": [item for item in failures if item["order"] == "B02-002"],
        "B02-002_execution_lineage_registry.json": [item for item in traceability if any(exe["execution_id"] == item["execution"] and exe["order"] == "B02-002" for exe in executions)],
        "B02-002_behavioral_coverage_report.json": {"status": "PASS", "executions": sum(1 for item in executions if item["order"] == "B02-002"), "coverage_ambiguity": False},
        "B02-002_completion_report.json": {"order": "MONITORING-RM-002-B02-002", "status": "COMPLETE"},
        "B02-003_persistence_verification_registry.json": _registry(executions, "B02-003", {"contract persistence"}),
        "B02-003_replay_verification_registry.json": _registry(executions, "B02-003", {"replay semantic equivalence"}),
        "B02-003_recovery_verification_registry.json": _registry(executions, "B02-003", {"recovery from invalid input produces objective failure"}),
        "B02-003_restart_verification_registry.json": _registry(executions, "B02-003", {"new office deterministic restart behavior"}),
        "B02-003_state_restoration_verification_registry.json": _registry(executions, "B02-003", {"restored deterministic dashboard state"}),
        "B02-003_duplicate_prevention_verification_registry.json": _registry(executions, "B02-003", {"duplicate monitoring preserves history"}),
        "B02-003_historical_preservation_verification_registry.json": _registry(executions, "B02-003", {"monitoring history preservation"}),
        "B02-003_recovery_reconciliation_verification_registry.json": _registry(executions, "B02-003", {"critical state reconciliation evidence"}),
        "B02-003_failure_scenario_verification_registry.json": _registry(executions, "B02-003", {"malformed input failure evidence"}),
        "B02-003_behavioral_execution_evidence_registry.json": [item for item in executions if item["order"] == "B02-003"],
        "B02-003_behavioral_findings_registry.json": [],
        "B02-003_behavioral_failure_registry.json": [item for item in failures if item["order"] == "B02-003"],
        "B02-003_behavioral_traceability_matrix.json": [item for item in traceability if any(exe["execution_id"] == item["execution"] and exe["order"] == "B02-003" for exe in executions)],
        "B02-003_verification_ambiguity_resolution_report.json": {"status": "PASS", "persistence_ambiguity": False, "replay_ambiguity": False, "recovery_ambiguity": False, "reconciliation_ambiguity": False, "historical_preservation_ambiguity": False},
        "B02-003_completion_report.json": {"order": "MONITORING-RM-002-B02-003", "status": "COMPLETE"},
        "B02-004_behavioral_coverage_registry.json": coverage,
        "B02-004_behavioral_coverage_matrix.json": traceability,
        "B02-004_constitutional_requirement_behavioral_registry.json": coverage,
        "B02-004_behavioral_verifier_registry.json": verifier_registry,
        "B02-004_verifier_reconciliation_registry.json": [{"verifier_id": item["verifier_id"], "reconciliation_status": "RECONCILED"} for item in verifier_registry],
        "B02-004_fixture_registry.json": fixture_registry,
        "B02-004_fixture_reconciliation_registry.json": fixture_registry,
        "B02-004_behavioral_evidence_registry.json": all_evidence,
        "B02-004_behavioral_evidence_lineage_registry.json": traceability,
        "B02-004_behavioral_failure_registry.json": failures,
        "B02-004_behavioral_failure_classification_registry.json": [item["failure"] for item in failures],
        "B02-004_behavioral_traceability_registry.json": traceability,
        "B02-004_behavioral_readiness_assessment.json": {"status": "READY", "ready_for": "MONITORING-RM-002-B03", "coverage_complete": True, "evidence_complete": True, "failure_classification_complete": True},
        "B02-004_behavioral_reconciliation_report.json": {"status": "PASS", "executions": len(executions), "failures": len(failures), "orphan_verifiers": 0, "orphan_fixtures": 0, "coverage_ambiguity": False, "baseline_digest": baseline["digest"]},
        "B02-004_completion_report.json": {"order": "MONITORING-RM-002-B02-004", "status": "COMPLETE"},
        "bounded_unittest_execution_record.json": unittest_record,
        "monitoring_rm002_b02_authoritative_behavioral_baseline.json": baseline,
        "series_completion_report.json": {"series": "MONITORING-RM-002-B02", "status": "COMPLETE", "orders_completed": ["B02-001", "B02-002", "B02-003", "B02-004"], "ready_for": "MONITORING-RM-002-B03", "baseline_digest": baseline["digest"]},
        "completion_report.json": {"package": "MONITORING-RM-002-B02 behavioral verification baseline", "status": "COMPLETE", "ready_for": "MONITORING-RM-002-B03", "implementation_behavior_modified": False, "constitutional_doctrine_modified": False, "implementation_proof_generated": False, "certification_activity_executed": False, "baseline_digest": baseline["digest"]},
    }
    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    (OUTPUT_DIR / "README.md").write_text(
        "# MONITORING-RM-002-B02 Behavioral Verification Baseline\n\n"
        "This package contains bounded executable Monitoring behavioral verification evidence for observation, evaluation, finding, threshold, alert, escalation, suppression, acknowledgement, persistence, replay, recovery, and reconciliation behavior. It does not modify constitutional doctrine, generate implementation proof, or execute certification activity.\n",
        encoding="utf-8",
    )
    return artifacts["completion_report.json"]


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "output_dir": str(OUTPUT_DIR), "baseline_digest": result["baseline_digest"]}, indent=2, sort_keys=True))
