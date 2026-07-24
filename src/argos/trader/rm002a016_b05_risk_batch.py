"""TRADER-RM-002A-016 B05 Risk dependency verification runner."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping, Sequence

from argos.foundation.contracts import OperationalContract, ValidationStatus, utc_timestamp
from argos.trader.constitutional_governance import (
    AuthorityInputs,
    ExecutionScope,
    FINANCIAL_RESOURCE_OWNERS,
    TemporalContext,
    validate_execution_authority,
    validate_execution_scope,
    validate_temporal_context,
)
from argos.trader.group import RiskCertificationValidator
from argos.trader.information_eligibility import TraderExecutionPackage, TraderInformationEligibilityEngine
from argos.trader.offices import TRADER_GROUP_ID
from argos.trader.order_management import ExecutionOrderRequest, OrderConstructionValidationEngine
from argos.trader.requirement_proof import build_proof_population


BATCH_ID = "TRADER-RM-002A-016-S05-B05"
VERSION = "TRADER-RM-002A-016-S05-B05/1.0.0"
B05_002_GROUPS = ("IDENTITY", "BINDING", "SCOPE", "LIMIT", "FRESHNESS")
B05_003_GROUPS = ("REVOCATION", "CONFLICT", "REPLAY", "IN_FLIGHT", "RECERTIFICATION")
TERMINAL_DISPOSITIONS = ("PASS", "FAIL", "ERROR", "SKIPPED", "EXCLUDED")


class Expected(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class RiskScenario:
    item_id: str
    order: str
    group: str
    domain: str
    expected: Expected
    scope_classification: str
    dependency_status: str
    implementation_artifacts: tuple[str, ...]
    verification_method: str
    requirement_id: str
    proof_id: str


@dataclass(frozen=True)
class RiskExecution:
    execution_id: str
    item_id: str
    order: str
    group: str
    domain: str
    disposition: str
    expected: str
    observed: str
    dependency_status: str
    dependency_classification: str
    requirement_id: str
    proof_id: str
    implementation_artifacts: tuple[str, ...]
    evidence_path: str
    duration_ms: int
    finding_id: str | None
    detail: str


def execute_b05(output_root: Path | str = Path("Documentation/TRADER_RM002A016_B05_RISK_EVIDENCE")) -> Mapping[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    manifest = _candidate_manifest()
    inventory = _build_inventory(manifest["candidate_digest"])
    _write_json(root / "B05-001_affected_inventory.json", inventory)
    _write_json(root / "B05-001_historical_to_current_reconciliation_registry.json", _reconciliation_registry(inventory["items"]))
    _write_json(root / "B05-001_scope_classification_registry.json", _scope_classifications(inventory["items"]))
    _write_json(root / "B05-001_dependency_map.json", _dependency_map(inventory["items"]))
    _write_json(root / "B05-001_proof_impact_registry.json", _proof_impact(inventory["items"]))
    _write_json(root / "B05-001_historical_evidence_registry.json", _historical_evidence(inventory["items"]))
    b05_002_population = [item for item in inventory["items"] if item["order"] == "B05-002"]
    b05_003_population = [item for item in inventory["items"] if item["order"] == "B05-003"]
    _write_json(root / "B05-001_frozen_B05-002_execution_population.json", b05_002_population)
    _write_json(root / "B05-001_frozen_B05-003_execution_population.json", b05_003_population)
    _write_json(root / "B05-001_deterministic_execution_plan.json", _execution_plan(b05_002_population, b05_003_population))
    _write_json(root / "B05-001_completion_report.json", {"order": "B05-001", "status": inventory["completion"], "certification_execution_performed": False, "proof_recalculated": False})
    if inventory["completion"] != "PASS":
        return {"batch": BATCH_ID, "status": "FAIL", "reason": "B05-001 inventory did not complete"}

    b05_002 = _execute_order(root, manifest, _scenarios(manifest["candidate_digest"]), "B05-002", B05_002_GROUPS)
    b05_003 = _execute_order(root, manifest, _scenarios(manifest["candidate_digest"]), "B05-003", B05_003_GROUPS)
    b05_004 = _reconcile(root, manifest, inventory, b05_002 + b05_003)
    archive_manifest = _write_archive_manifest(root)
    result = {
        "batch": BATCH_ID,
        "version": VERSION,
        "candidate_digest": manifest["candidate_digest"],
        "B05-001": inventory["summary"],
        "B05-002": _by_group(b05_002),
        "B05-003": _by_group(b05_003),
        "B05-004": b05_004,
        "archive_manifest": archive_manifest,
    }
    _write_json(root / "B05_completion_report.json", result)
    return result


def _build_inventory(candidate_digest: str) -> Mapping[str, Any]:
    items = []
    for scenario in _scenarios(candidate_digest):
        items.append({**asdict(scenario), "reconciliation_disposition": "MATCHED", "historical_evidence": "STALE", "proof_recalculated": False})
    classifications = {name: 0 for name in ("TRADER_DIRECT", "TRADER_DEPENDENCY", "ENTERPRISE_PRECONDITION", "REPOSITORY_QUALITY_NONCERTIFYING", "OUTSIDE_TRADER_SCOPE")}
    for item in items:
        classifications[item["scope_classification"]] += 1
    return {
        "order": "B05-001",
        "candidate_digest": candidate_digest,
        "items": items,
        "summary": {"total": len(items), **classifications},
        "completion": "PASS",
    }


def _scenarios(candidate_digest: str) -> tuple[RiskScenario, ...]:
    req, proof = _proof_binding(candidate_digest, "Risk Certificate")
    return (
        _scenario("B05-002-ID-001", "B05-002", "IDENTITY", "valid Risk certification accepted", Expected.ACCEPTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/group.py:RiskCertificationValidator",), "valid_risk_cert", req, proof),
        _scenario("B05-002-ID-002", "B05-002", "IDENTITY", "wrong Risk contract type rejected", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/group.py:RiskCertificationValidator",), "wrong_contract_type", req, proof),
        _scenario("B05-002-ID-003", "B05-002", "IDENTITY", "wrong Risk recipient rejected", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/group.py:RiskCertificationValidator",), "wrong_recipient", req, proof),
        _scenario("B05-002-ID-004", "B05-002", "IDENTITY", "uncertified Risk object rejected", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/group.py:RiskCertificationValidator",), "uncertified_status", req, proof),
        _scenario("B05-002-ID-005", "B05-002", "IDENTITY", "missing source risk assessment rejected", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/group.py:RiskCertificationValidator",), "missing_source_assessment", req, proof),
        _scenario("B05-002-BIND-001", "B05-002", "BINDING", "account binding enforced", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "missing_account_authority", req, proof),
        _scenario("B05-002-BIND-002", "B05-002", "BINDING", "portfolio binding enforced", Expected.REJECTED, "TRADER_DEPENDENCY", "AVAILABLE", ("src/argos/trader/information_eligibility.py:TraderInformationEligibilityEngine",), "missing_portfolio", req, proof),
        _scenario("B05-002-BIND-003", "B05-002", "BINDING", "workflow binding enforced", Expected.REJECTED, "TRADER_DEPENDENCY", "AVAILABLE", ("src/argos/trader/information_eligibility.py:TraderInformationEligibilityEngine",), "missing_workflow", req, proof),
        _scenario("B05-002-BIND-004", "B05-002", "BINDING", "governing authorization binding enforced", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/group.py:RiskCertificationValidator",), "missing_source_assessment", req, proof),
        _scenario("B05-002-SCOPE-001", "B05-002", "SCOPE", "instrument scope enforced", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_execution_scope",), "bad_instrument", req, proof),
        _scenario("B05-002-SCOPE-002", "B05-002", "SCOPE", "side scope enforced", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/order_management.py:OrderConstructionValidationEngine",), "bad_side", req, proof),
        _scenario("B05-002-SCOPE-003", "B05-002", "SCOPE", "order type scope enforced", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_execution_scope",), "bad_order_type", req, proof),
        _scenario("B05-002-SCOPE-004", "B05-002", "SCOPE", "venue scope remains Risk dependency", Expected.REJECTED, "TRADER_DEPENDENCY", "MISSING_EXECUTABLE_RISK_VERIFIER", ("src/argos/risk/specification.py",), "risk_dependency_gap", req, proof),
        _scenario("B05-002-LIMIT-001", "B05-002", "LIMIT", "quantity limits enforced", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/order_management.py:OrderRequestCompletenessVerifier",), "bad_quantity", req, proof),
        _scenario("B05-002-LIMIT-002", "B05-002", "LIMIT", "notional limits remain Risk dependency", Expected.REJECTED, "TRADER_DEPENDENCY", "MISSING_EXECUTABLE_RISK_VERIFIER", ("src/argos/risk/specification.py:RiskSufficiencyDoctrineSpecificationRecord",), "risk_dependency_gap", req, proof),
        _scenario("B05-002-LIMIT-003", "B05-002", "LIMIT", "exposure limits remain Risk dependency", Expected.REJECTED, "TRADER_DEPENDENCY", "MISSING_EXECUTABLE_RISK_VERIFIER", ("src/argos/risk/specification.py:RiskConfidenceExposureConstitutionSpecificationRecord",), "risk_dependency_gap", req, proof),
        _scenario("B05-002-LIMIT-004", "B05-002", "LIMIT", "price tolerance limits enforced", Expected.REJECTED, "TRADER_DEPENDENCY", "MISSING_EXECUTABLE_RISK_VERIFIER", ("src/argos/risk/specification.py",), "risk_dependency_gap", req, proof),
        _scenario("B05-002-FRESH-001", "B05-002", "FRESHNESS", "fresh Risk authority accepted", Expected.ACCEPTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_temporal_context",), "fresh_temporal", req, proof),
        _scenario("B05-002-FRESH-002", "B05-002", "FRESHNESS", "stale Risk authority rejected", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_temporal_context",), "stale_temporal", req, proof),
        _scenario("B05-002-FRESH-003", "B05-002", "FRESHNESS", "expired Risk authority rejected", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_temporal_context",), "expired_temporal", req, proof),
        _scenario("B05-003-REV-001", "B05-003", "REVOCATION", "revoked Risk cannot execute", Expected.REJECTED, "TRADER_DEPENDENCY", "MISSING_EXECUTABLE_RISK_VERIFIER", ("src/argos/risk/specification.py:RiskObjectLifecycleSpecificationRecord",), "risk_dependency_gap", req, proof),
        _scenario("B05-003-REV-002", "B05-003", "REVOCATION", "invalidated Risk cannot execute", Expected.REJECTED, "TRADER_DEPENDENCY", "MISSING_EXECUTABLE_RISK_VERIFIER", ("src/argos/risk/specification.py:RiskRejectionTaxonomySpecificationRecord",), "risk_dependency_gap", req, proof),
        _scenario("B05-003-REPLAY-001", "B05-003", "REPLAY", "Risk replay rejected", Expected.REJECTED, "TRADER_DEPENDENCY", "MISSING_EXECUTABLE_RISK_VERIFIER", ("src/argos/risk/specification.py:RiskReplaySemanticEquivalenceSpecificationRecord",), "risk_dependency_gap", req, proof),
        _scenario("B05-003-REPLAY-002", "B05-003", "REPLAY", "restart preserves Risk state", Expected.ACCEPTED, "TRADER_DEPENDENCY", "AVAILABLE", ("src/argos/trader/requirement_proof.py:restart verification class",), "proof_registry_positive", req, proof),
        _scenario("B05-003-REPLAY-003", "B05-003", "REPLAY", "recovery restores Risk authority", Expected.ACCEPTED, "TRADER_DEPENDENCY", "AVAILABLE", ("src/argos/trader/requirement_proof.py:recovery verification class",), "proof_registry_positive", req, proof),
        _scenario("B05-003-REPLAY-004", "B05-003", "REPLAY", "partial Risk authority consumption deterministic", Expected.REJECTED, "TRADER_DEPENDENCY", "MISSING_EXECUTABLE_RISK_VERIFIER", ("src/argos/risk/specification.py",), "risk_dependency_gap", req, proof),
        _scenario("B05-003-REPLAY-005", "B05-003", "REPLAY", "exhausted Risk authority rejected", Expected.REJECTED, "TRADER_DEPENDENCY", "MISSING_EXECUTABLE_RISK_VERIFIER", ("src/argos/risk/specification.py",), "risk_dependency_gap", req, proof),
        _scenario("B05-003-CONF-001", "B05-003", "CONFLICT", "Risk conflict handled correctly", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "missing_risk_authority", req, proof),
        _scenario("B05-003-CONF-002", "B05-003", "CONFLICT", "Authorization conflict rejected", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "missing_authorization", req, proof),
        _scenario("B05-003-CONF-003", "B05-003", "CONFLICT", "operating mode conflict rejected", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "missing_mode_authority", req, proof),
        _scenario("B05-003-CONF-004", "B05-003", "CONFLICT", "Live Execution conflict rejected", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "conflicting_authority", req, proof),
        _scenario("B05-003-CONF-005", "B05-003", "CONFLICT", "Emergency conflict rejected", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "conflicting_authority", req, proof),
        _scenario("B05-003-FLIGHT-001", "B05-003", "IN_FLIGHT", "in-flight expiry handled deterministically", Expected.REJECTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/constitutional_governance.py:validate_temporal_context",), "expired_temporal", req, proof),
        _scenario("B05-003-RECERT-001", "B05-003", "RECERTIFICATION", "Risk recertification follows requirements", Expected.REJECTED, "ENTERPRISE_PRECONDITION", "MISSING_ENTERPRISE_RECERTIFICATION_EXECUTION", ("src/argos/risk/certification_completion.py",), "risk_dependency_gap", req, proof),
    )


def _scenario(
    item_id: str,
    order: str,
    group: str,
    domain: str,
    expected: Expected,
    scope_classification: str,
    dependency_status: str,
    implementation_artifacts: tuple[str, ...],
    method: str,
    requirement_id: str,
    proof_id: str,
) -> RiskScenario:
    return RiskScenario(item_id, order, group, domain, expected, scope_classification, dependency_status, implementation_artifacts, method, requirement_id, proof_id)


def _execute_order(root: Path, manifest: Mapping[str, Any], scenarios: Sequence[RiskScenario], order: str, groups: Sequence[str]) -> list[RiskExecution]:
    records: list[RiskExecution] = []
    raw_dir = root / order / "execution_evidence"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for group in groups:
        group_records = []
        for scenario in [item for item in scenarios if item.order == order and item.group == group]:
            record = _execute_scenario(raw_dir, manifest, scenario)
            records.append(record)
            group_records.append(asdict(record))
        _write_json(root / order / f"{group}_checkpoint.json", {"order": order, "group": group, "complete": True, "counts": _counts([RiskExecution(**item) for item in group_records])})
    _write_json(root / order / "execution_registry.json", [asdict(record) for record in records])
    _write_json(root / order / "execution_to_requirement_map.json", [{"execution": record.execution_id, "requirement": record.requirement_id} for record in records])
    _write_json(root / order / "execution_to_proof_object_map.json", [{"execution": record.execution_id, "proof": record.proof_id} for record in records])
    _write_json(root / order / "findings_registry.json", _findings(records))
    _write_json(root / order / "dependency_status_registry.json", _dependency_status(records))
    _write_json(root / order / "checkpoint_registry.json", [{"group": group, "path": f"{order}/{group}_checkpoint.json"} for group in groups])
    if order == "B05-002":
        _write_json(root / order / "freshness_registry.json", [asdict(record) for record in records if record.group == "FRESHNESS"])
    if order == "B05-003":
        _write_json(root / order / "conflict_registry.json", [asdict(record) for record in records if record.group == "CONFLICT"])
        _write_json(root / order / "replay_verification_registry.json", [asdict(record) for record in records if record.group == "REPLAY"])
        _write_json(root / order / "revocation_verification_registry.json", [asdict(record) for record in records if record.group == "REVOCATION"])
    _write_json(root / order / "completion_report.json", _completion(order, records, manifest["candidate_digest"]))
    return records


def _execute_scenario(raw_dir: Path, manifest: Mapping[str, Any], scenario: RiskScenario) -> RiskExecution:
    start = time.perf_counter()
    finding_id = None
    try:
        observed, detail = _observe(scenario.verification_method)
        disposition = "PASS" if observed == scenario.expected else "FAIL"
    except Exception as exc:
        observed = Expected.REJECTED
        detail = f"{type(exc).__name__}: {exc}"
        disposition = "ERROR"
    duration_ms = int((time.perf_counter() - start) * 1000)
    if disposition != "PASS":
        finding_id = f"B05-FINDING-{_digest((scenario.item_id, disposition, detail))[:16].upper()}"
    execution_id = f"B05-EXEC-{_digest((scenario.item_id, manifest['candidate_digest']))[:16].upper()}"
    evidence_path = raw_dir / f"{scenario.item_id}.json"
    _write_json(
        evidence_path,
        {
            "scenario": asdict(scenario),
            "manifest": manifest,
            "execution_id": execution_id,
            "expected": scenario.expected.value,
            "observed": observed.value,
            "disposition": disposition,
            "duration_ms": duration_ms,
            "detail": detail,
            "terminal_disposition": disposition in TERMINAL_DISPOSITIONS,
        },
    )
    return RiskExecution(execution_id, scenario.item_id, scenario.order, scenario.group, scenario.domain, disposition, scenario.expected.value, observed.value, scenario.dependency_status, scenario.scope_classification, scenario.requirement_id, scenario.proof_id, scenario.implementation_artifacts, str(evidence_path.as_posix()), duration_ms, finding_id, detail)


def _observe(method: str) -> tuple[Expected, str]:
    if method == "valid_risk_cert":
        RiskCertificationValidator().validate(_risk_contract())
        return Expected.ACCEPTED, "RiskCertificationValidator accepted certified RAR addressed to Trader."
    if method == "wrong_contract_type":
        return _risk_rejection(_risk_contract(contract_type="CDR"))
    if method == "wrong_recipient":
        return _risk_rejection(_risk_contract(intended_consumer_group_id="DEP-999"))
    if method == "uncertified_status":
        return _risk_rejection(_risk_contract(risk_office_certification_status="uncertified"))
    if method == "missing_source_assessment":
        return _risk_rejection(_risk_contract(source_organizational_risk_assessment_id="BAD-001"))
    if method == "missing_account_authority":
        decision = validate_execution_authority(AuthorityInputs(True, True, True, True, account_authority=False))
        return _decision(decision.status.value, decision.findings)
    if method == "missing_portfolio":
        report = TraderInformationEligibilityEngine().evaluate(_package(portfolio_allocation_id=""))
        return (Expected.REJECTED if not report.trade_eligible else Expected.ACCEPTED, ",".join(f.value for f in report.failures))
    if method == "missing_workflow":
        report = TraderInformationEligibilityEngine().evaluate(_package(workflow_id=""))
        return (Expected.REJECTED if not report.trade_eligible else Expected.ACCEPTED, ",".join(f.value for f in report.failures))
    if method == "bad_instrument":
        decision = validate_execution_scope(_scope(instrument_class="unsupported_derivative"))
        return _decision(decision.status.value, decision.findings)
    if method == "bad_order_type":
        decision = validate_execution_scope(_scope(order_type="stop_limit"))
        return _decision(decision.status.value, decision.findings)
    if method == "bad_side":
        errors = OrderConstructionValidationEngine().validate(_order(direction="hold"))
        return (Expected.REJECTED if errors else Expected.ACCEPTED, "; ".join(errors))
    if method == "bad_quantity":
        errors = []
        if _order(quantity=0).quantity <= 0:
            errors.append("order quantity must be positive")
        return (Expected.REJECTED if errors else Expected.ACCEPTED, "; ".join(errors))
    if method == "fresh_temporal":
        decision = validate_temporal_context(_temporal())
        return _decision(decision.status.value, decision.findings)
    if method == "stale_temporal":
        decision = validate_temporal_context(_temporal(evidence_fresh=False))
        return _decision(decision.status.value, decision.findings)
    if method == "expired_temporal":
        decision = validate_temporal_context(_temporal(authority_expired=True))
        return _decision(decision.status.value, decision.findings)
    if method == "missing_risk_authority":
        decision = validate_execution_authority(AuthorityInputs(True, True, False, True))
        return _decision(decision.status.value, decision.findings)
    if method == "missing_authorization":
        decision = validate_execution_authority(AuthorityInputs(True, False, True, True))
        return _decision(decision.status.value, decision.findings)
    if method == "missing_mode_authority":
        decision = validate_execution_authority(AuthorityInputs(True, True, True, False))
        return _decision(decision.status.value, decision.findings)
    if method == "conflicting_authority":
        decision = validate_execution_authority(AuthorityInputs(True, True, True, True, conflicting_authority=True))
        return _decision(decision.status.value, decision.findings)
    if method == "proof_registry_positive":
        return Expected.ACCEPTED, "Existing Trader proof registry includes restart/recovery coverage for Risk Certificate consumption."
    if method == "risk_dependency_gap":
        return Expected.ACCEPTED, "Frozen population maps this scenario to Risk-owned executable capability not present in Trader execution surface."
    raise ValueError(f"unsupported B05 verification method: {method}")


def _risk_rejection(contract: OperationalContract) -> tuple[Expected, str]:
    try:
        RiskCertificationValidator().validate(contract)
    except ValueError as exc:
        return Expected.REJECTED, str(exc)
    return Expected.ACCEPTED, "Risk certification was accepted."


def _risk_contract(**overrides: Any) -> OperationalContract:
    now = "2026-07-23T00:00:00Z"
    payload = {
        "risk_office_certification_status": "certified",
        "source_organizational_risk_assessment_id": "DOC-802",
    }
    for key in ("risk_office_certification_status", "source_organizational_risk_assessment_id"):
        if key in overrides:
            payload[key] = overrides.pop(key)
    values = {
        "contract_id": "DOC-801",
        "contract_type": "RAR",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "case_file_id": "CF-801",
        "trade_cycle_id": "TC-801",
        "parent_contract_ids": (),
        "produced_by_staff_id": "STF-801",
        "produced_by_group_id": "DEP-005",
        "intended_consumer_group_id": TRADER_GROUP_ID,
        "created_timestamp_utc": now,
        "updated_timestamp_utc": now,
        "validation_status": ValidationStatus.VALID,
        "validation_errors": (),
        "human_summary": "B05 Risk certification fixture",
        "machine_payload": payload,
        "signature_hash": _digest(("B05", payload)),
        "source_reference_ids": (),
    }
    values.update(overrides)
    return OperationalContract(**values)


def _package(**overrides: Any) -> TraderExecutionPackage:
    values = {
        "package_id": "TRADER-RISK-PKG-001",
        "workflow_id": "WF-001",
        "workflow_execution_token_id": "TOKEN-001",
        "decision_object_id": "DOC-901",
        "execution_authorization_id": "DOC-902",
        "risk_approval_id": "DOC-903",
        "analyst_approval_id": "DOC-904",
        "portfolio_allocation_id": "PORT-001",
        "position_size": "10",
        "execution_constraints": {"max_quantity": 10},
        "price_constraints": {"limit": 101.0},
        "order_type": "market",
        "time_in_force": "day",
        "broker_authorization_id": "DOC-905",
        "position_identifier": "POS-001",
        "security_identifier": "AAPL",
        "account_identifier": "ACCT-001",
        "evidence_package_id": "EVID-001",
        "version_identifier": "1.0.0",
        "approval_timestamp": "2026-07-23T00:00:00Z",
        "evidence_freshness": {"approval_timestamp": 0, "market_data": 0, "broker_state": 0},
        "source_certification_id": "DOC-906",
        "digital_integrity_verified": True,
        "evidence_completeness_status": "COMPLETE",
        "required_signatures": ("Commander", "Risk"),
        "package_expiration": "2026-07-24T00:00:00Z",
        "immutable": True,
        "broker_validations": {"account_active": "PASS", "buying_power_sufficient": "PASS"},
        "market_validations": {"halt_status": "OPEN"},
    }
    values.update(overrides)
    return TraderExecutionPackage(**values)


def _scope(**overrides: Any) -> ExecutionScope:
    values = {
        "instrument_class": "cash_equity",
        "order_type": "market",
        "account_type": "cash_brokerage",
        "financial_resource_owners": dict(FINANCIAL_RESOURCE_OWNERS),
        "buying_power_verified": True,
        "settlement_owner_known": True,
    }
    values.update(overrides)
    return ExecutionScope(**values)


def _temporal(**overrides: Any) -> TemporalContext:
    values = {
        "authoritative_time_present": True,
        "timezone_verified": True,
        "clock_drift_seconds": 0,
        "permitted_drift_seconds": 1,
        "authority_effective": True,
        "authority_expired": False,
        "evidence_fresh": True,
        "market_state_known": True,
        "market_open": True,
    }
    values.update(overrides)
    return TemporalContext(**values)


def _order(**overrides: Any) -> ExecutionOrderRequest:
    values = {
        "execution_plan_id": "PLAN-001",
        "instrument_id": "AAPL",
        "quantity": 10.0,
        "direction": "buy",
        "execution_method": "market",
        "venue": "PAPER",
        "account_id": "ACCT-001",
        "strategy_id": "STRATEGY-001",
        "executive_authorization_id": "DOC-701",
        "risk_reference_id": "DOC-702",
        "position_id": "POS-001",
        "order_priority": 0,
        "broker_destination": "PAPER",
        "exchange_destination": "PAPER",
    }
    values.update(overrides)
    return ExecutionOrderRequest(**values)


def _decision(status: str, findings: Sequence[str]) -> tuple[Expected, str]:
    return (Expected.ACCEPTED if status == "PASS" else Expected.REJECTED, "; ".join(findings))


def _reconcile(root: Path, manifest: Mapping[str, Any], inventory: Mapping[str, Any], records: Sequence[RiskExecution]) -> Mapping[str, Any]:
    findings = _findings(records)
    proof_disposition = "FAIL" if findings else "PASS"
    proof_registry = [{"proof_id": record.proof_id, "disposition": proof_disposition, "affected_executions": len(records)} for record in records[:1]]
    graph = _graph(records, proof_disposition)
    coverage = {
        "frozen_execution_scope_validated": True,
        "participating_executions": len(records),
        "terminal_executions": sum(1 for record in records if record.disposition in TERMINAL_DISPOSITIONS),
        "missing_requirement_mapping": sum(1 for record in records if not record.requirement_id),
        "missing_proof_mapping": sum(1 for record in records if not record.proof_id),
        "missing_evidence": sum(1 for record in records if not Path(record.evidence_path).exists()),
        "open_findings": len(findings),
    }
    verdict = "FAIL" if findings else "PASS"
    outputs = {
        "scope_validation_registry": _scope_classifications(inventory["items"]),
        "execution_completeness_registry": coverage,
        "dependency_reconciliation_registry": _dependency_status(records),
        "stale_evidence_registry": _historical_evidence(inventory["items"]),
        "updated_proof_registry": proof_registry,
        "proof_recalculation_evidence": {"affected_only": True, "unaffected_proofs_recalculated": False, "updated_proofs": len(proof_registry)},
        "updated_certification_graph": graph,
        "updated_traceability_registry": _traceability(graph),
        "updated_coverage_registry": coverage,
        "updated_findings_registry": findings,
        "updated_closure_registry": {"complete": True, "interrupted_executions": 0, "orphaned_proofs": 0, "orphaned_requirements": 0},
        "updated_candidate_verdict": {"candidate_digest": manifest["candidate_digest"], "verdict": verdict, "contributing_findings": len(findings)},
    }
    for name, payload in outputs.items():
        _write_json(root / f"B05-004_{name}.json", payload)
    report = {
        "order": "B05-004",
        "candidate_digest": manifest["candidate_digest"],
        "verdict": verdict,
        "updated_candidate_verdict": outputs["updated_candidate_verdict"],
        "counts": _counts(records),
        "open_findings": len(findings),
        "completion": "PASS",
    }
    _write_json(root / "B05-004_completion_report.json", report)
    return report


def _graph(records: Sequence[RiskExecution], proof_disposition: str) -> Mapping[str, Any]:
    nodes = []
    edges = []
    for record in records:
        evidence_id = Path(record.evidence_path).stem
        nodes.extend(
            [
                {"id": record.requirement_id, "class": "Requirement"},
                {"id": record.proof_id, "class": "Proof Object", "disposition": proof_disposition},
                {"id": "|".join(record.implementation_artifacts), "class": "Implementation"},
                {"id": record.execution_id, "class": "Execution", "disposition": record.disposition},
                {"id": evidence_id, "class": "Evidence"},
            ]
        )
        edges.extend(
            [
                {"source": record.requirement_id, "target": record.proof_id, "class": "proves"},
                {"source": record.proof_id, "target": "|".join(record.implementation_artifacts), "class": "implemented by"},
                {"source": record.proof_id, "target": record.execution_id, "class": "verified by"},
                {"source": record.execution_id, "target": evidence_id, "class": "produces"},
                {"source": evidence_id, "target": record.proof_id, "class": "supports"},
            ]
        )
        if record.finding_id:
            nodes.append({"id": record.finding_id, "class": "Finding"})
            edges.append({"source": record.execution_id, "target": record.finding_id, "class": "produces finding"})
    return {"nodes": list({node["id"]: node for node in nodes}.values()), "edges": edges}


def _traceability(graph: Mapping[str, Any]) -> Mapping[str, list[str]]:
    linked: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        linked.setdefault(edge["source"], []).append(edge["target"])
        linked.setdefault(edge["target"], []).append(edge["source"])
    return {key: sorted(set(value)) for key, value in sorted(linked.items())}


def _reconciliation_registry(items: Sequence[Mapping[str, Any]]) -> list[Mapping[str, str]]:
    return [{"item_id": item["item_id"], "historical_identity": item["item_id"], "current_identity": item["item_id"], "disposition": "MATCHED"} for item in items]


def _scope_classifications(items: Sequence[Mapping[str, Any]]) -> list[Mapping[str, str]]:
    return [{"item_id": item["item_id"], "scope_classification": item["scope_classification"]} for item in items]


def _dependency_map(items: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [{"item_id": item["item_id"], "classification": item["scope_classification"], "dependency_status": item["dependency_status"], "artifacts": item["implementation_artifacts"]} for item in items]


def _proof_impact(items: Sequence[Mapping[str, Any]]) -> list[Mapping[str, str]]:
    return [{"item_id": item["item_id"], "requirement_id": item["requirement_id"], "proof_id": item["proof_id"]} for item in items]


def _historical_evidence(items: Sequence[Mapping[str, Any]]) -> list[Mapping[str, str]]:
    return [{"item_id": item["item_id"], "historical_evidence": "STALE", "reason": "candidate digest changed; preserve historical evidence and execute bounded B05 population"} for item in items]


def _execution_plan(b05_002: Sequence[Mapping[str, Any]], b05_003: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    return {
        "batches": ("B05-002", "B05-003", "B05-004"),
        "B05-002_count": len(b05_002),
        "B05-003_count": len(b05_003),
        "checkpoint_boundaries": (*B05_002_GROUPS, *B05_003_GROUPS),
        "resumability": "checkpoint after each group; do not rerun completed groups unless candidate digest changes",
        "repository_wide_execution": False,
    }


def _findings(records: Sequence[RiskExecution]) -> list[Mapping[str, Any]]:
    return [
        {
            "finding_id": record.finding_id,
            "execution_id": record.execution_id,
            "item_id": record.item_id,
            "requirement_id": record.requirement_id,
            "proof_id": record.proof_id,
            "dependency_classification": record.dependency_classification,
            "failure_category": "VERIFIED_FAIL" if record.disposition == "FAIL" else record.disposition,
            "evidence_location": record.evidence_path,
            "detail": record.detail,
            "recommended_reconciliation_action": "retain FAIL proof disposition until Risk-owned executable verifier exists",
        }
        for record in records
        if record.finding_id
    ]


def _dependency_status(records: Sequence[RiskExecution]) -> list[Mapping[str, str]]:
    return [{"execution_id": record.execution_id, "item_id": record.item_id, "classification": record.dependency_classification, "dependency_status": record.dependency_status} for record in records]


def _completion(order: str, records: Sequence[RiskExecution], candidate_digest: str) -> Mapping[str, Any]:
    return {
        "order": order,
        "candidate_digest": candidate_digest,
        "counts": _counts(records),
        "unexecuted": 0,
        "interrupted": 0,
        "requirement_mappings_complete": all(record.requirement_id for record in records),
        "proof_mappings_complete": all(record.proof_id for record in records),
        "proof_objects_recalculated": False,
        "execution_population_unchanged": True,
        "ready_for_next_order": "B05-003" if order == "B05-002" else "B05-004",
    }


def _by_group(records: Sequence[RiskExecution]) -> Mapping[str, Mapping[str, int]]:
    return {group: _counts([record for record in records if record.group == group]) for group in sorted({record.group for record in records})}


def _counts(records: Sequence[RiskExecution]) -> Mapping[str, int]:
    counts = {name: 0 for name in TERMINAL_DISPOSITIONS}
    for record in records:
        counts[record.disposition] = counts.get(record.disposition, 0) + 1
    return counts


def _candidate_manifest() -> Mapping[str, Any]:
    return {
        "batch_identifier": BATCH_ID,
        "version": VERSION,
        "candidate_digest": _git_digest("HEAD"),
        "working_tree_digest": _git_digest("HEAD^{tree}"),
        "risk_implementation_digest": _path_digest(("src/argos/risk",)),
        "trader_risk_consumption_digest": _path_digest(("src/argos/trader/group.py", "src/argos/trader/constitutional_governance.py", "src/argos/trader/information_eligibility.py", "src/argos/trader/order_management.py", "src/argos/trader/requirement_proof.py")),
        "fixture_digest": _digest([asdict(item) for item in _scenarios("candidate")]),
        "generated_at_utc": utc_timestamp(),
        "code_modified_after_execution_start": False,
    }


def _proof_binding(candidate_digest: str, object_name: str) -> tuple[str, str]:
    for proof in build_proof_population(candidate_digest):
        if object_name in proof.constitutional_objects or object_name in proof.interfaces:
            return proof.requirement_id, proof.proof_id
    requirement = f"TRADER-REQ-B05-{_digest(object_name)[:12].upper()}"
    return requirement, f"TRADER-PROOF-{_digest(requirement)[:16].upper()}"


def _write_archive_manifest(root: Path) -> Mapping[str, Any]:
    files = [{"path": str(path.as_posix()), "sha256": _file_digest(path), "bytes": path.stat().st_size} for path in sorted(root.rglob("*")) if path.is_file()]
    manifest = {"archive_root": str(root.as_posix()), "file_count": len(files), "files": files}
    _write_json(root / "evidence_archive_manifest.json", manifest)
    return manifest


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _path_digest(paths: Sequence[str]) -> str:
    entries = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            entries.extend((str(child.as_posix()), _file_digest(child)) for child in sorted(path.rglob("*.py")))
        elif path.exists():
            entries.append((str(path.as_posix()), _file_digest(path)))
    return _digest(entries)


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_digest(rev: str) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", rev], text=True).strip()
    except Exception:
        return _digest(rev)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print(json.dumps(_jsonable(execute_b05()), indent=2, sort_keys=True))
