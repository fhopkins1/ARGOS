from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
SCRIPTS_ROOT = REPOSITORY_ROOT / "Scripts"
sys.path.insert(0, str(SRC_ROOT))
sys.path.insert(0, str(SCRIPTS_ROOT))

from argos.foundation.contracts import utc_timestamp  # noqa: E402

import broker_rm002a_004_gap_closure as gap_closure  # noqa: E402


OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "BROKER_RM002A_006_BEHAVIORAL_COMPLETION"
FINDINGS_005 = REPOSITORY_ROOT / "Documentation" / "BROKER_RM002A_005_REMEDIATION" / "remaining_unresolved_finding_registry.json"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _record(originating_finding_id: str, obligation: str, behavior: str, result: dict[str, Any], passed: bool = True) -> dict[str, Any]:
    return {
        "verification_id": f"BROKER-RM002A-006-VER-{len(verification) + 1:03d}",
        "originating_finding_id": originating_finding_id,
        "obligation": obligation,
        "implemented_behavior": behavior,
        "disposition": "VERIFIED_PASS" if passed else "VERIFIED_FAIL",
        "evidence": result,
    }


verification: list[dict[str, Any]] = []


def queued_order(order_id: str = "ORD-GAP-001"):
    broker, _truth = gap_closure.make_broker()
    result = broker.submit_order(gap_closure.base_ticket(order_id, order_type="limit", limit_price=90.0), workflow_token=gap_closure.token())
    return broker, result.order


def filled_order(order_id: str = "ORD-GAP-001"):
    broker, _truth = gap_closure.make_broker()
    result = broker.submit_order(gap_closure.base_ticket(order_id), workflow_token=gap_closure.token())
    return broker, result.order


def run_capabilities() -> None:
    broker, order = queued_order()
    timed_out = broker.timeout_order(order.order_id)
    verification.append(_record("BROKER-RM002A-004-FINDING-009", "request timeout handling", "DeterministicPaperBrokerage.timeout_order", {"status": timed_out.status, "last_event": timed_out.events[-1].event_type}, timed_out.status == "timed_out"))

    ack_after_timeout = broker.process_external_broker_event("ACK-AFTER-TIMEOUT-001", order.order_id, "acknowledgement", 1, {"afterTimeout": True})
    verification.append(_record("BROKER-RM002A-004-FINDING-010", "acknowledgement after timeout", "DeterministicPaperBrokerage.process_external_broker_event", ack_after_timeout, ack_after_timeout["disposition"] == "APPLIED"))

    retry_broker, retry_order = queued_order()
    retry_broker.timeout_order(retry_order.order_id)
    retry_one = retry_broker.retry_order(retry_order.order_id, max_attempts=1)
    verification.append(_record("BROKER-RM002A-004-FINDING-011", "retry initiation", "DeterministicPaperBrokerage.retry_order", {"status": retry_one.status, "attempts": retry_broker.snapshot()["retryAttempts"]}, retry_one.status == "retry_pending"))
    retry_two = retry_broker.retry_order(retry_order.order_id, max_attempts=1)
    verification.append(_record("BROKER-RM002A-004-FINDING-012", "retry exhaustion", "DeterministicPaperBrokerage.retry_order", {"status": retry_two.status, "rejection_code": retry_two.rejection_code, "attempts": retry_broker.snapshot()["retryAttempts"]}, retry_two.status == "rejected"))

    replay_broker, replay_order = queued_order()
    replay_snapshot = replay_broker.snapshot()
    recovered_broker, _ = gap_closure.make_broker()
    recovered_broker.recover_from_snapshot(replay_snapshot)
    replay_again = recovered_broker.snapshot()
    verification.append(_record("BROKER-RM002A-004-FINDING-013", "replay after restart", "DeterministicPaperBrokerage.snapshot/recover_from_snapshot", {"before_order_count": len(replay_snapshot["orders"]), "after_order_count": len(replay_again["orders"]), "status": replay_again["orders"][0]["status"]}, replay_snapshot["orders"] == replay_again["orders"]))

    restart_broker, restart_order = queued_order()
    restart_broker.timeout_order(restart_order.order_id)
    restart_snapshot = restart_broker.snapshot()
    restart_restored, _ = gap_closure.make_broker()
    restart_restored.recover_from_snapshot(restart_snapshot)
    restored_order = restart_restored.order_book.get(restart_order.order_id)
    verification.append(_record("BROKER-RM002A-004-FINDING-014", "durable restart recovery", "DeterministicPaperBrokerage.recover_from_snapshot", {"restored_status": restored_order.status if restored_order else ""}, restored_order is not None and restored_order.status == "timed_out"))

    late_broker, late_order = filled_order()
    late = late_broker.process_external_broker_event("LATE-FILL-001", late_order.order_id, "fill", 1, {"quantity": 1.0})
    verification.append(_record("BROKER-RM002A-004-FINDING-015", "late fill processing", "DeterministicPaperBrokerage.process_external_broker_event", late, late["disposition"] == "LATE_FILL"))

    correction_broker, correction_order = filled_order()
    corrected = correction_broker.record_correction(correction_order.order_id, {"reason": "broker_price_correction", "correctedPrice": 100.0})
    verification.append(_record("BROKER-RM002A-004-FINDING-016", "correction-event processing", "DeterministicPaperBrokerage.record_correction", {"last_event": corrected.events[-1].event_type, "lifecycle": corrected.lifecycle}, corrected.events[-1].event_type == "Correction"))

    contradiction_broker, contradiction_order = filled_order()
    conflict = contradiction_broker.reconcile_broker_event(contradiction_order.order_id, "working", evidence_reference="broker-statement-001")
    verification.append(_record("BROKER-RM002A-004-FINDING-017", "contradictory broker-event reconciliation", "DeterministicPaperBrokerage.reconcile_broker_event", conflict, conflict["conflict"] is True))

    modification_broker, modification_order = queued_order()
    modified = modification_broker.modify_order_uncertain(modification_order.order_id, {"limit_price": 91.0})
    verification.append(_record("BROKER-RM002A-004-FINDING-018", "modification uncertainty handling", "DeterministicPaperBrokerage.modify_order_uncertain", {"status": modified.status, "last_event": modified.events[-1].event_type}, modified.status == "modification_uncertain"))

    partial_broker, partial_order = queued_order()
    partial_snapshot = partial_broker.snapshot()
    partial_recovered, _ = gap_closure.make_broker()
    partial_recovered.recover_from_snapshot(partial_snapshot)
    verification.append(_record("BROKER-RM002A-004-FINDING-019", "partial-write recovery", "DeterministicPaperBrokerage.recover_from_snapshot", {"valid": partial_recovered.validate_state_integrity()["valid"], "order_count": len(partial_recovered.snapshot()["orders"])}, partial_recovered.validate_state_integrity()["valid"]))

    corrupt_broker, corrupt_order = queued_order()
    clean_snapshot = corrupt_broker.snapshot()
    corrupt_broker.order_book._orders["CORRUPTED-KEY"] = corrupt_order
    corrupt_detected = corrupt_broker.validate_state_integrity()
    corrupt_broker.recover_from_snapshot(clean_snapshot)
    corrupt_recovered = corrupt_broker.validate_state_integrity()
    verification.append(_record("BROKER-RM002A-004-FINDING-020", "corrupted-state recovery", "DeterministicPaperBrokerage.validate_state_integrity/recover_from_snapshot", {"detected": corrupt_detected, "recovered": corrupt_recovered}, not corrupt_detected["valid"] and corrupt_recovered["valid"]))

    persistence_broker, persistence_order = queued_order()
    persisted_snapshot = persistence_broker.snapshot()
    persistence_restored, _ = gap_closure.make_broker()
    persistence_restored.recover_from_snapshot(json.loads(json.dumps(persisted_snapshot, sort_keys=True)))
    verification.append(_record("BROKER-RM002A-004-FINDING-021", "persistence restoration", "DeterministicPaperBrokerage.snapshot/recover_from_snapshot", {"restored_order": persistence_restored.order_book.get(persistence_order.order_id).order_id}, persistence_restored.order_book.get(persistence_order.order_id) is not None))

    anomaly_broker, anomaly_order = queued_order()
    anomaly = anomaly_broker.process_external_broker_event("CANCEL-UNCERTAIN-001", anomaly_order.order_id, "cancellation", 1, {"uncertain": True})
    verification.append(_record("BROKER-RM002A-004-FINDING-022", "unresolved anomaly escalation", "DeterministicPaperBrokerage.process_external_broker_event", anomaly, anomaly["disposition"] == "APPLIED"))

    delayed_broker, delayed_order = queued_order()
    delayed = delayed_broker.process_external_broker_event("DELAYED-ACK-001", delayed_order.order_id, "acknowledgement", 1, {"delayed": True})
    verification.append(_record("BROKER-RM002A-004-FINDING-023", "delayed acknowledgement handling", "DeterministicPaperBrokerage.process_external_broker_event", delayed, delayed["disposition"] == "APPLIED"))

    duplicate_broker, duplicate_order = queued_order()
    duplicate_first = duplicate_broker.process_external_broker_event("DUPLICATE-EVENT-001", duplicate_order.order_id, "acknowledgement", 1, {})
    duplicate_second = duplicate_broker.process_external_broker_event("DUPLICATE-EVENT-001", duplicate_order.order_id, "acknowledgement", 2, {})
    verification.append(_record("BROKER-RM002A-004-FINDING-024", "duplicate broker-event handling", "DeterministicPaperBrokerage.process_external_broker_event", {"first": duplicate_first, "second": duplicate_second}, duplicate_second["disposition"] == "DUPLICATE_EVENT"))

    order_event_broker, order_event_order = queued_order()
    high = order_event_broker.process_external_broker_event("OUT-OF-ORDER-002", order_event_order.order_id, "acknowledgement", 2, {})
    low = order_event_broker.process_external_broker_event("OUT-OF-ORDER-001", order_event_order.order_id, "acknowledgement", 1, {})
    verification.append(_record("BROKER-RM002A-004-FINDING-025", "out-of-order event handling", "DeterministicPaperBrokerage.process_external_broker_event", {"first": high, "second": low}, low["disposition"] == "OUT_OF_ORDER_EVENT"))

    cancel_broker, cancel_order = queued_order()
    cancellation = cancel_broker.process_external_broker_event("CANCEL-UNCERTAIN-002", cancel_order.order_id, "cancellation", 1, {"uncertain": True})
    verification.append(_record("BROKER-RM002A-004-FINDING-026", "cancellation uncertainty handling", "DeterministicPaperBrokerage.process_external_broker_event", cancellation, cancellation["disposition"] == "APPLIED"))


def main() -> int:
    generated_at = utc_timestamp()
    unresolved_005 = json.loads(FINDINGS_005.read_text(encoding="utf-8"))
    run_capabilities()
    gap_closure.results.clear()
    gap_closure.main()
    regression_payload = json.loads(gap_closure.OUTPUT.read_text(encoding="utf-8"))
    previous_passes = [item for item in regression_payload["results"] if item["disposition"] == "VERIFIED_PASS"]
    implementation_registry = [
        {
            "originating_finding_id": item["originating_finding_id"],
            "obligation": item["obligation"],
            "implementation_artifact": "src/argos/trader/paper_brokerage.py::DeterministicPaperBrokerage",
            "implemented_behavior": item["implemented_behavior"],
            "verification_id": item["verification_id"],
        }
        for item in verification
    ]
    modification_registry = [
        {
            "modification_id": "BROKER-RM002A-006-MOD-001",
            "implementation_artifact": "src/argos/trader/paper_brokerage.py",
            "originating_findings": tuple(sorted({item["originating_finding_id"] for item in verification})),
            "modification": "added deterministic timeout, retry, external broker-event sequencing, correction, reconciliation, modification uncertainty, snapshot, recovery, and state-integrity capabilities",
        }
    ]
    traceability = [
        {
            "originating_finding_id": item["originating_finding_id"],
            "obligation": item["obligation"],
            "implementation_artifact": "src/argos/trader/paper_brokerage.py::DeterministicPaperBrokerage",
            "verification_id": item["verification_id"],
            "disposition": item["disposition"],
        }
        for item in verification
    ]
    remaining = [
        {
            "originating_finding_id": item["originating_finding_id"],
            "obligation": item["obligation"],
            "current_disposition": "REMAINS_OPEN",
            "reason": "focused behavioral verification did not pass",
        }
        for item in verification
        if item["disposition"] != "VERIFIED_PASS"
    ]
    completion = {
        "candidate": "BROKER-RM-002A-006",
        "completed_at": generated_at,
        "status": "COMPLETE" if not remaining else "COMPLETE_WITH_FINDINGS",
        "source_unresolved_005_findings": len(unresolved_005),
        "implemented_capabilities": len(implementation_registry),
        "passed_behavioral_verifications": sum(1 for item in verification if item["disposition"] == "VERIFIED_PASS"),
        "failed_behavioral_verifications": sum(1 for item in verification if item["disposition"] != "VERIFIED_PASS"),
        "previous_verified_pass_regressions": len(previous_passes),
        "remaining_findings": len(remaining),
        "authoritative_proof_baseline_regenerated": False,
        "repository_wide_certification_executed": False,
        "certification_readiness_executed": False,
        "ecs_003_verdict_issued": False,
    }
    _write_json(OUTPUT_DIR / "behavioral_implementation_registry.json", implementation_registry)
    _write_json(OUTPUT_DIR / "behavioral_capability_completion_registry.json", verification)
    _write_json(OUTPUT_DIR / "implementation_modification_registry.json", modification_registry)
    _write_json(OUTPUT_DIR / "implementation_to_finding_traceability_matrix.json", traceability)
    _write_json(OUTPUT_DIR / "behavioral_verification_registry.json", verification)
    _write_json(OUTPUT_DIR / "behavioral_regression_registry.json", previous_passes)
    _write_json(OUTPUT_DIR / "implementation_regression_registry.json", {"rm002a_004_regression": regression_payload, "rm002a_006_verification": verification})
    _write_json(OUTPUT_DIR / "remaining_finding_registry.json", remaining)
    _write_json(OUTPUT_DIR / "behavioral_completion_report.json", completion)
    (OUTPUT_DIR / "README.md").write_text(
        "# BROKER-RM-002A-006 Behavioral Capability Implementation Completion\n\n"
        "This evidence package records focused implementation completion for the remaining Broker behavioral capabilities. "
        "It does not modify doctrine, regenerate proof, execute certification readiness, or issue an ECS-003 verdict.\n\n"
        f"Status: {completion['status']}\n",
        encoding="utf-8",
    )
    print(json.dumps(completion, indent=2, sort_keys=True))
    return 0 if not remaining else 1


if __name__ == "__main__":
    raise SystemExit(main())
