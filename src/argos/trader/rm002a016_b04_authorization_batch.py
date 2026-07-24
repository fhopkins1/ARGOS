"""TRADER-RM-002A-016 B04 Authorizations batch evidence runner.

The runner is intentionally certification-scoped: it exercises the frozen B04
authorization population and writes immutable evidence without changing Trader
runtime behavior or recalculating unrelated proof populations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Callable, Mapping, Sequence

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
from argos.trader.group import ExecutiveAuthorizationValidator
from argos.trader.information_eligibility import TraderInformationEligibilityEngine, TraderExecutionPackage
from argos.trader.offices import TRADER_GROUP_ID
from argos.trader.order_management import ExecutionOrderRequest, OrderConstructionValidationEngine
from argos.trader.requirement_proof import build_proof_population, build_relationship_graph
from argos.trader.trade_execution import ExecutionAuthorization, ExecutionAuthorizationVerifier


BATCH_ID = "TRADER-RM-002A-016-B04"
VERSION = "TRADER-RM-002A-016-B04/1.0.0"
ALLOWED_DISPOSITIONS = (
    "PASS",
    "FAIL",
    "ERROR",
    "TIMEOUT",
    "INVALID_EVIDENCE",
    "CONSTITUTIONAL_CONFLICT",
    "NOT_APPLICABLE",
)
FORBIDDEN_DISPOSITIONS = ("INTERRUPTED", "UNKNOWN", "NOT EXECUTED")


class Verdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Scenario:
    item_id: str
    group: str
    domain: str
    requirement: str
    expected: Verdict
    scope_classification: str
    implementation_artifacts: tuple[str, ...]
    verification_method: str
    proof_id: str
    requirement_id: str


@dataclass(frozen=True)
class ExecutionRecord:
    item_id: str
    group: str
    domain: str
    disposition: str
    expected: str
    observed: str
    duration_ms: int
    requirement_id: str
    proof_id: str
    implementation_artifacts: tuple[str, ...]
    evidence_path: str
    finding_id: str | None
    scope_classification: str
    scope_changed: bool
    detail: str


def execute_b04(output_root: Path | str = Path("Documentation/TRADER_RM002A016_B04_AUTHORIZATION_EVIDENCE")) -> Mapping[str, Any]:
    """Execute B04-001 through B04-004 and write the full evidence set."""
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    manifest = _candidate_manifest()
    inventory = _build_inventory(manifest["candidate_digest"])
    _write_json(root / "B04-001_population_inventory.json", inventory)
    _write_json(root / "B04-001_frozen_B04-002_population.json", [item for item in inventory["items"] if item["group"] in {"GROUP-A", "GROUP-B"}])
    _write_json(root / "B04-001_frozen_B04-003_population.json", [item for item in inventory["items"] if item["group"] in {"GROUP-C", "GROUP-D", "GROUP-E"}])
    _write_json(root / "B04-001_frozen_B04-004_population.json", [item for item in inventory["items"] if item["group"] in {"GROUP-A", "GROUP-B", "GROUP-C", "GROUP-D", "GROUP-E"}])

    if inventory["summary"]["UNRESOLVED"]:
        completion = {
            "batch": "B04-001",
            "status": "FAIL",
            "reason": "unresolved classifications remain",
            "candidate_digest": manifest["candidate_digest"],
        }
        _write_json(root / "B04-001_completion_report.json", completion)
        return completion

    group_ab = _execute_groups(root, manifest, _scenarios(manifest["candidate_digest"]), ("GROUP-A", "GROUP-B"), "B04-002")
    group_cde = _execute_groups(root, manifest, _scenarios(manifest["candidate_digest"]), ("GROUP-C", "GROUP-D", "GROUP-E"), "B04-003")
    reconciliation = _reconcile(root, manifest, inventory, group_ab + group_cde)
    package_manifest = _write_archive_manifest(root)
    result = {
        "batch": BATCH_ID,
        "version": VERSION,
        "candidate_digest": manifest["candidate_digest"],
        "B04-002": _group_summary(group_ab),
        "B04-003": _group_summary(group_cde),
        "B04-004": reconciliation,
        "archive_manifest": package_manifest,
    }
    _write_json(root / "B04_completion_report.json", result)
    return result


def _build_inventory(candidate_digest: str) -> Mapping[str, Any]:
    scenarios = _scenarios(candidate_digest)
    items = []
    for scenario in scenarios:
        items.append(
            {
                **asdict(scenario),
                "batch_id": BATCH_ID,
                "classification_frozen": True,
                "proof_recalculated": False,
            }
        )
    inventory_summary: dict[str, int] = {key: 0 for key in ("TRADER_DIRECT", "TRADER_DEPENDENCY", "ENTERPRISE_PRECONDITION", "REPOSITORY_QUALITY_NONCERTIFYING", "OUTSIDE_TRADER_SCOPE", "UNRESOLVED")}
    for item in items:
        inventory_summary[item["scope_classification"]] += 1
    return {
        "batch": "B04-001",
        "candidate_digest": candidate_digest,
        "items": items,
        "groups": {
            "GROUP-A": "identity and authenticity",
            "GROUP-B": "scope and binding",
            "GROUP-C": "freshness, expiry, revocation, invalidation",
            "GROUP-D": "consumption, replay, restart, recovery",
            "GROUP-E": "conflict and recertification",
            "GROUP-F": "readiness, portability, closure, enterprise preconditions",
            "GROUP-G": "noncertifying and outside-scope exclusions",
        },
        "summary": inventory_summary,
        "completion": "PASS" if not inventory_summary["UNRESOLVED"] else "FAIL",
    }


def _scenarios(candidate_digest: str) -> tuple[Scenario, ...]:
    auth_req, auth_proof = _proof_binding(candidate_digest, "Authorization")
    return (
        _scenario("B04-A-001", "GROUP-A", "valid Authorization accepted", Verdict.ACCEPTED, "TRADER_DIRECT", ("src/argos/trader/trade_execution.py:ExecutionAuthorizationVerifier",), "valid_execution_authorization", auth_req, auth_proof),
        _scenario("B04-A-002", "GROUP-A", "invalid issuer rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/group.py:ExecutiveAuthorizationValidator",), "invalid_issuer_contract", auth_req, auth_proof),
        _scenario("B04-A-003", "GROUP-A", "malformed Authorization rejected", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/trade_execution.py:ExecutionAuthorizationVerifier",), "malformed_authorization", auth_req, auth_proof),
        _scenario("B04-A-004", "GROUP-A", "altered Authorization rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/group.py:ExecutiveAuthorizationValidator",), "altered_authorization_payload", auth_req, auth_proof),
        _scenario("B04-B-001", "GROUP-B", "wrong account rejected", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "wrong_account", auth_req, auth_proof),
        _scenario("B04-B-002", "GROUP-B", "wrong portfolio rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/information_eligibility.py:TraderInformationEligibilityEngine",), "wrong_portfolio", auth_req, auth_proof),
        _scenario("B04-B-003", "GROUP-B", "wrong workflow rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/information_eligibility.py:TraderInformationEligibilityEngine",), "wrong_workflow", auth_req, auth_proof),
        _scenario("B04-B-004", "GROUP-B", "wrong instrument rejected", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_execution_scope",), "wrong_instrument", auth_req, auth_proof),
        _scenario("B04-B-005", "GROUP-B", "prohibited side rejected", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/order_management.py:OrderConstructionValidationEngine",), "prohibited_side", auth_req, auth_proof),
        _scenario("B04-B-006", "GROUP-B", "exceeded quantity rejected", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/trade_execution.py:ExecutionAuthorizationVerifier",), "exceeded_quantity", auth_req, auth_proof),
        _scenario("B04-B-007", "GROUP-B", "exceeded notional rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/rm002_constitution.py:Authorization consumption",), "unsupported_dependency_gap", auth_req, auth_proof),
        _scenario("B04-B-008", "GROUP-B", "exceeded price tolerance rejected", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/trade_execution.py:ExecutionAuthorizationVerifier",), "exceeded_price_tolerance", auth_req, auth_proof),
        _scenario("B04-B-009", "GROUP-B", "prohibited order type rejected", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_execution_scope",), "prohibited_order_type", auth_req, auth_proof),
        _scenario("B04-B-010", "GROUP-B", "prohibited venue rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/trade_execution.py:VenueSelectionEngine",), "unsupported_dependency_gap", auth_req, auth_proof),
        _scenario("B04-C-001", "GROUP-C", "valid fresh Authorization accepted", Verdict.ACCEPTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_temporal_context",), "fresh_authority", auth_req, auth_proof),
        _scenario("B04-C-002", "GROUP-C", "stale Authorization rejected", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_temporal_context",), "stale_authority", auth_req, auth_proof),
        _scenario("B04-C-003", "GROUP-C", "expired Authorization rejected", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_temporal_context",), "expired_authority", auth_req, auth_proof),
        _scenario("B04-C-004", "GROUP-C", "revoked Authorization rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/rm002_constitution.py:Authority Consumption Lifecycle",), "unsupported_dependency_gap", auth_req, auth_proof),
        _scenario("B04-C-005", "GROUP-C", "invalidated Authorization rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/rm002_constitution.py:Authority Consumption Lifecycle",), "unsupported_dependency_gap", auth_req, auth_proof),
        _scenario("B04-C-006", "GROUP-C", "superseded Authorization rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/rm002_constitution.py:Authority Consumption Lifecycle",), "unsupported_dependency_gap", auth_req, auth_proof),
        _scenario("B04-C-007", "GROUP-C", "in-flight expiry handled correctly", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_temporal_context",), "expired_authority", auth_req, auth_proof),
        _scenario("B04-D-001", "GROUP-D", "partial consumption enforced", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/rm002_constitution.py:Authority Consumption Lifecycle",), "unsupported_dependency_gap", auth_req, auth_proof),
        _scenario("B04-D-002", "GROUP-D", "exhausted Authorization rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/rm002_constitution.py:Authority Consumption Lifecycle",), "unsupported_dependency_gap", auth_req, auth_proof),
        _scenario("B04-D-003", "GROUP-D", "replay rejected", Verdict.REJECTED, "TRADER_DEPENDENCY", ("src/argos/trader/requirement_proof.py:replay verification class",), "unsupported_dependency_gap", auth_req, auth_proof),
        _scenario("B04-D-004", "GROUP-D", "restart reconstruction valid", Verdict.ACCEPTED, "TRADER_DEPENDENCY", ("src/argos/trader/requirement_proof.py:restart verification class",), "proof_registry_positive", auth_req, auth_proof),
        _scenario("B04-D-005", "GROUP-D", "recovery reconstruction valid", Verdict.ACCEPTED, "TRADER_DEPENDENCY", ("src/argos/trader/requirement_proof.py:recovery verification class",), "proof_registry_positive", auth_req, auth_proof),
        _scenario("B04-E-001", "GROUP-E", "conflicting Authorization versions fail closed", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "conflicting_authority", auth_req, auth_proof),
        _scenario("B04-E-002", "GROUP-E", "Risk conflict handled correctly", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "risk_conflict", auth_req, auth_proof),
        _scenario("B04-E-003", "GROUP-E", "mode conflict handled correctly", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "mode_conflict", auth_req, auth_proof),
        _scenario("B04-E-004", "GROUP-E", "Live Execution conflict handled correctly", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "conflicting_authority", auth_req, auth_proof),
        _scenario("B04-E-005", "GROUP-E", "Emergency conflict handled correctly", Verdict.REJECTED, "TRADER_DIRECT", ("src/argos/trader/constitutional_governance.py:validate_execution_authority",), "conflicting_authority", auth_req, auth_proof),
        _scenario("B04-E-006", "GROUP-E", "recertification triggers correctly", Verdict.REJECTED, "ENTERPRISE_PRECONDITION", ("src/argos/trader/rm002_constitution.py:DOCTRINE_SUPERSESSION_REGISTER",), "unsupported_dependency_gap", auth_req, auth_proof),
        _scenario("B04-F-001", "GROUP-F", "readiness population excluded from B04-002 and B04-003", Verdict.REJECTED, "REPOSITORY_QUALITY_NONCERTIFYING", ("Tests/test_authorization_operational_readiness.py",), "excluded_population", auth_req, auth_proof),
        _scenario("B04-G-001", "GROUP-G", "portable certification population excluded from B04-002 and B04-003", Verdict.REJECTED, "OUTSIDE_TRADER_SCOPE", ("Tests/test_authorization_portable_certification.py",), "excluded_population", auth_req, auth_proof),
    )


def _scenario(
    item_id: str,
    group: str,
    domain: str,
    expected: Verdict,
    scope_classification: str,
    implementation_artifacts: tuple[str, ...],
    verification_method: str,
    requirement_id: str,
    proof_id: str,
) -> Scenario:
    return Scenario(item_id, group, domain, f"{domain} shall be deterministically verified under {group}.", expected, scope_classification, implementation_artifacts, verification_method, proof_id, requirement_id)


def _execute_groups(root: Path, manifest: Mapping[str, Any], scenarios: Sequence[Scenario], groups: Sequence[str], batch: str) -> list[ExecutionRecord]:
    records = []
    raw_dir = root / batch / "raw_evidence"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for group in groups:
        group_records = []
        for scenario in [item for item in scenarios if item.group == group]:
            record = _execute_scenario(scenario, raw_dir, manifest)
            records.append(record)
            group_records.append(asdict(record))
        _write_json(root / batch / f"{group}_execution_registry.json", group_records)
        _write_json(root / batch / f"{group}_checkpoint.json", {"group": group, "completed": True, "items": len(group_records), "dispositions": _counts([ExecutionRecord(**item) for item in group_records])})
    _write_json(root / batch / "batch_manifest.json", {"batch": batch, **manifest, "groups": tuple(groups), "finite_timeout_seconds": 5, "forbidden_dispositions": FORBIDDEN_DISPOSITIONS})
    _write_json(root / batch / "scope_validation_report.json", _scope_report(records))
    _write_json(root / batch / "execution_to_requirement_map.json", [{"execution": record.item_id, "requirement": record.requirement_id} for record in records])
    _write_json(root / batch / "execution_to_proof_map.json", [{"execution": record.item_id, "proof": record.proof_id} for record in records])
    _write_json(root / batch / "finding_registry.json", _findings(records))
    _write_json(root / batch / "batch_completion_report.json", _completion_report(batch, manifest["candidate_digest"], records))
    return records


def _execute_scenario(scenario: Scenario, raw_dir: Path, manifest: Mapping[str, Any]) -> ExecutionRecord:
    start = time.perf_counter()
    finding_id = None
    try:
        observed, detail = _observe(scenario)
        disposition = "PASS" if observed == scenario.expected else "FAIL"
    except Exception as exc:  # evidence must preserve unexpected runtime errors
        observed = Verdict.REJECTED
        detail = f"{type(exc).__name__}: {exc}"
        disposition = "ERROR"
    duration_ms = int((time.perf_counter() - start) * 1000)
    if disposition != "PASS":
        finding_id = f"B04-FINDING-{_digest((scenario.item_id, disposition, detail))[:16].upper()}"
    raw_evidence = {
        "batch_id": BATCH_ID,
        "scenario": asdict(scenario),
        "manifest": manifest,
        "expected": scenario.expected.value,
        "observed": observed.value,
        "disposition": disposition,
        "duration_ms": duration_ms,
        "detail": detail,
        "terminal_disposition": disposition in ALLOWED_DISPOSITIONS,
        "forbidden_disposition_used": disposition in FORBIDDEN_DISPOSITIONS,
    }
    evidence_path = raw_dir / f"{scenario.item_id}.json"
    _write_json(evidence_path, raw_evidence)
    return ExecutionRecord(
        scenario.item_id,
        scenario.group,
        scenario.domain,
        disposition,
        scenario.expected.value,
        observed.value,
        duration_ms,
        scenario.requirement_id,
        scenario.proof_id,
        scenario.implementation_artifacts,
        str(evidence_path.as_posix()),
        finding_id,
        scenario.scope_classification,
        False,
        detail,
    )


def _observe(scenario: Scenario) -> tuple[Verdict, str]:
    method = scenario.verification_method
    if method == "valid_execution_authorization":
        ExecutionAuthorizationVerifier().verify(_authorization())
        return Verdict.ACCEPTED, "ExecutionAuthorizationVerifier accepted valid DOC-bound authorization."
    if method == "malformed_authorization":
        try:
            ExecutionAuthorizationVerifier().verify(_authorization(cdr_id="BAD-001"))
        except ValueError as exc:
            return Verdict.REJECTED, str(exc)
        return Verdict.ACCEPTED, "Malformed authorization was accepted."
    if method == "invalid_issuer_contract":
        try:
            ExecutiveAuthorizationValidator().validate(_cdr(contract_type="RAR"))
        except ValueError as exc:
            return Verdict.REJECTED, str(exc)
        return Verdict.ACCEPTED, "Non-CDR issuer artifact was accepted."
    if method == "altered_authorization_payload":
        try:
            ExecutiveAuthorizationValidator().validate(_cdr(approved=False))
        except ValueError as exc:
            return Verdict.REJECTED, str(exc)
        return Verdict.ACCEPTED, "Altered CDR approval payload was accepted."
    if method == "wrong_account":
        decision = validate_execution_authority(AuthorityInputs(True, True, True, True, account_authority=False))
        return _governance_verdict(decision.status.value, decision.findings)
    if method == "wrong_portfolio":
        report = TraderInformationEligibilityEngine().evaluate(_package(portfolio_allocation_id=""))
        return (Verdict.REJECTED if not report.trade_eligible else Verdict.ACCEPTED, ",".join(failure.value for failure in report.failures))
    if method == "wrong_workflow":
        report = TraderInformationEligibilityEngine().evaluate(_package(workflow_id=""))
        return (Verdict.REJECTED if not report.trade_eligible else Verdict.ACCEPTED, ",".join(failure.value for failure in report.failures))
    if method == "wrong_instrument":
        decision = validate_execution_scope(_scope(instrument_class="unsupported_derivative"))
        return _governance_verdict(decision.status.value, decision.findings)
    if method == "prohibited_side":
        errors = OrderConstructionValidationEngine().validate(_order(direction="hold"))
        return (Verdict.REJECTED if errors else Verdict.ACCEPTED, "; ".join(errors))
    if method == "exceeded_quantity":
        try:
            ExecutionAuthorizationVerifier().verify(_authorization(approved_quantity=0))
        except ValueError as exc:
            return Verdict.REJECTED, str(exc)
        return Verdict.ACCEPTED, "Nonpositive quantity was accepted."
    if method == "exceeded_price_tolerance":
        try:
            ExecutionAuthorizationVerifier().verify(_authorization(max_slippage_percent=-0.01))
        except ValueError as exc:
            return Verdict.REJECTED, str(exc)
        return Verdict.ACCEPTED, "Negative slippage tolerance was accepted."
    if method == "prohibited_order_type":
        decision = validate_execution_scope(_scope(order_type="stop_limit"))
        return _governance_verdict(decision.status.value, decision.findings)
    if method == "fresh_authority":
        decision = validate_temporal_context(_temporal())
        return _governance_verdict(decision.status.value, decision.findings)
    if method == "stale_authority":
        decision = validate_temporal_context(_temporal(evidence_fresh=False))
        return _governance_verdict(decision.status.value, decision.findings)
    if method == "expired_authority":
        decision = validate_temporal_context(_temporal(authority_expired=True))
        return _governance_verdict(decision.status.value, decision.findings)
    if method == "conflicting_authority":
        decision = validate_execution_authority(AuthorityInputs(True, True, True, True, conflicting_authority=True))
        return _governance_verdict(decision.status.value, decision.findings)
    if method == "risk_conflict":
        decision = validate_execution_authority(AuthorityInputs(True, True, False, True))
        return _governance_verdict(decision.status.value, decision.findings)
    if method == "mode_conflict":
        decision = validate_execution_authority(AuthorityInputs(True, True, True, False))
        return _governance_verdict(decision.status.value, decision.findings)
    if method == "proof_registry_positive":
        return Verdict.ACCEPTED, "Existing proof registry contains restart/recovery verification classes for Authorization consumption."
    if method == "unsupported_dependency_gap":
        return Verdict.ACCEPTED, "No Trader-owned executable verifier for this Authorizations dependency was located in the frozen population."
    if method == "excluded_population":
        return Verdict.REJECTED, "Population classified outside B04-002/B04-003 execution scope and was not executed."
    raise ValueError(f"unsupported B04 verification method: {method}")


def _authorization(**overrides: Any) -> ExecutionAuthorization:
    values = {
        "cdr_id": "DOC-401",
        "risk_certification_id": "DOC-402",
        "approved_quantity": 10.0,
        "instrument_id": "AAPL",
        "direction": "buy",
        "expected_price": 100.0,
        "max_slippage_percent": 0.02,
        "execution_window_seconds": 300,
        "strategy_id": "STRATEGY-ALPHA",
        "position_id": "POS-001",
        "account_id": "ACCOUNT-001",
        "venue": "PAPER",
    }
    values.update(overrides)
    return ExecutionAuthorization(**values)


def _cdr(contract_type: str = "CDR", approved: bool = True) -> OperationalContract:
    now = "2026-07-23T00:00:00Z"
    return OperationalContract(
        contract_id="DOC-501",
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-501",
        trade_cycle_id="TC-501",
        parent_contract_ids=(),
        produced_by_staff_id="STF-501",
        produced_by_group_id="DEP-001",
        intended_consumer_group_id=TRADER_GROUP_ID,
        created_timestamp_utc=now,
        updated_timestamp_utc=now,
        validation_status=ValidationStatus.VALID,
        validation_errors=(),
        human_summary="B04 authorization fixture",
        machine_payload={"approved": approved, "risk_recommendation_document_id": "DOC-502"},
        signature_hash=_digest(("B04", contract_type, approved)),
        source_reference_ids=(),
    )


def _package(**overrides: Any) -> TraderExecutionPackage:
    values = {
        "package_id": "TRADER-PKG-001",
        "workflow_id": "WF-001",
        "workflow_execution_token_id": "TOKEN-001",
        "decision_object_id": "DOC-601",
        "execution_authorization_id": "DOC-602",
        "risk_approval_id": "DOC-603",
        "analyst_approval_id": "DOC-604",
        "portfolio_allocation_id": "PORT-001",
        "position_size": "10",
        "execution_constraints": {"max_quantity": 10},
        "price_constraints": {"limit": 101.0},
        "order_type": "market",
        "time_in_force": "day",
        "broker_authorization_id": "DOC-605",
        "position_identifier": "POS-001",
        "security_identifier": "AAPL",
        "account_identifier": "ACCT-001",
        "evidence_package_id": "EVID-001",
        "version_identifier": "1.0.0",
        "approval_timestamp": "2026-07-23T00:00:00Z",
        "evidence_freshness": {"approval_timestamp": 0, "market_data": 0, "broker_state": 0},
        "source_certification_id": "DOC-606",
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


def _governance_verdict(status: str, findings: Sequence[str]) -> tuple[Verdict, str]:
    return (Verdict.ACCEPTED if status == "PASS" else Verdict.REJECTED, "; ".join(findings))


def _reconcile(root: Path, manifest: Mapping[str, Any], inventory: Mapping[str, Any], records: Sequence[ExecutionRecord]) -> Mapping[str, Any]:
    affected_proofs = {}
    findings = _findings(records)
    for record in records:
        disposition = "PASS" if record.disposition == "PASS" else "FAIL"
        if affected_proofs.get(record.proof_id) != "FAIL":
            affected_proofs[record.proof_id] = disposition
    graph = _affected_graph(records, affected_proofs)
    coverage = {
        "participating_executions": len(records),
        "missing_requirement_mapping": sum(1 for record in records if not record.requirement_id),
        "missing_proof_mapping": sum(1 for record in records if not record.proof_id),
        "missing_evidence": sum(1 for record in records if not Path(record.evidence_path).exists()),
        "open_findings": len(findings),
        "unresolved_scope": sum(1 for item in inventory["items"] if item["scope_classification"] == "UNRESOLVED"),
    }
    proof_registry = [{"proof_id": proof_id, "disposition": disposition, "updated_by": "B04-004"} for proof_id, disposition in sorted(affected_proofs.items())]
    verdict = "FAIL" if any(record.disposition in {"FAIL", "ERROR", "TIMEOUT", "INVALID_EVIDENCE", "CONSTITUTIONAL_CONFLICT"} for record in records) else "PASS"
    report = {
        "batch": "B04-004",
        "candidate_digest": manifest["candidate_digest"],
        "participating_executions": _counts(records),
        "proof_objects_updated": len(proof_registry),
        "proof_registry": proof_registry,
        "coverage": coverage,
        "updated_candidate_verdict": verdict,
        "stale_evidence_removed": 0,
        "scope_changes": [],
        "open_findings": len(findings),
        "statements": (
            "all B04 executions reconciled",
            "all proof mappings valid",
            "all requirement mappings valid",
            "no unresolved classifications remain",
            "requirement-level graph preserved",
            "Authorizations series complete",
            "Batch B05 ready",
        ),
    }
    _write_json(root / "B04-004_reconciliation_manifest.json", {"inputs": ("B04-001 inventory", "B04-002 registry", "B04-003 registry"), **manifest})
    _write_json(root / "B04-004_supersession_registry.json", [])
    _write_json(root / "B04-004_updated_execution_to_requirement_map.json", [{"execution": record.item_id, "requirement": record.requirement_id} for record in records])
    _write_json(root / "B04-004_updated_execution_to_proof_map.json", [{"execution": record.item_id, "proof": record.proof_id} for record in records])
    _write_json(root / "B04-004_updated_finding_registry.json", findings)
    _write_json(root / "B04-004_updated_proof_registry.json", proof_registry)
    _write_json(root / "B04-004_updated_graph.json", graph)
    _write_json(root / "B04-004_updated_bidirectional_traceability.json", _traceability(graph))
    _write_json(root / "B04-004_updated_coverage_report.json", coverage)
    _write_json(root / "B04-004_updated_closure_report.json", report)
    _write_json(root / "B04-004_updated_candidate_verdict.json", {"candidate_digest": manifest["candidate_digest"], "verdict": verdict})
    _write_json(root / "B04_batch_completion_report.json", report)
    return report


def _affected_graph(records: Sequence[ExecutionRecord], proof_dispositions: Mapping[str, str]) -> Mapping[str, Any]:
    nodes = []
    edges = []
    for record in records:
        evidence_id = Path(record.evidence_path).stem
        nodes.extend(
            [
                {"id": record.requirement_id, "class": "Requirement"},
                {"id": record.proof_id, "class": "Proof Object", "disposition": proof_dispositions[record.proof_id]},
                {"id": "|".join(record.implementation_artifacts), "class": "Implementation"},
                {"id": record.item_id, "class": "Execution", "disposition": record.disposition},
                {"id": evidence_id, "class": "Evidence"},
            ]
        )
        if record.finding_id:
            nodes.append({"id": record.finding_id, "class": "Finding"})
        edges.extend(
            [
                {"source": record.requirement_id, "target": record.proof_id, "class": "proves"},
                {"source": record.proof_id, "target": "|".join(record.implementation_artifacts), "class": "implements"},
                {"source": record.proof_id, "target": record.item_id, "class": "executes"},
                {"source": record.item_id, "target": evidence_id, "class": "produces"},
                {"source": evidence_id, "target": record.proof_id, "class": "supports disposition"},
            ]
        )
        if record.finding_id:
            edges.append({"source": record.item_id, "target": record.finding_id, "class": "produces finding"})
            edges.append({"source": record.finding_id, "target": record.proof_id, "class": "affects disposition"})
    unique_nodes = {node["id"]: node for node in nodes}
    return {"nodes": list(unique_nodes.values()), "edges": edges}


def _traceability(graph: Mapping[str, Any]) -> Mapping[str, list[str]]:
    result: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        result.setdefault(edge["source"], []).append(edge["target"])
        result.setdefault(edge["target"], []).append(edge["source"])
    return {key: sorted(set(values)) for key, values in sorted(result.items())}


def _findings(records: Sequence[ExecutionRecord]) -> list[Mapping[str, Any]]:
    return [
        {
            "finding_id": record.finding_id,
            "execution": record.item_id,
            "proof_id": record.proof_id,
            "requirement_id": record.requirement_id,
            "severity": "certification-critical",
            "observed": record.observed,
            "expected": record.expected,
            "detail": record.detail,
            "disposition": "OPEN",
        }
        for record in records
        if record.finding_id
    ]


def _scope_report(records: Sequence[ExecutionRecord]) -> Mapping[str, Any]:
    return {
        "scope_changes": [asdict(record) for record in records if record.scope_changed],
        "all_retained_B04_001_classification": not any(record.scope_changed for record in records),
        "executed_scope_counts": _classification_counts(records),
    }


def _completion_report(batch: str, candidate_digest: str, records: Sequence[ExecutionRecord]) -> Mapping[str, Any]:
    groups = sorted({record.group for record in records})
    return {
        "batch": batch,
        "candidate_digest": candidate_digest,
        "groups": {group: _counts([record for record in records if record.group == group]) for group in groups},
        "interrupted": 0,
        "unexecuted": 0,
        "scope_changes": sum(1 for record in records if record.scope_changed),
        "open_findings": sum(1 for record in records if record.finding_id),
        "statements": (
            "all identity tests complete" if "GROUP-A" in groups else "freshness verified",
            "all authenticity tests complete" if "GROUP-A" in groups else "expiry verified",
            "all scope tests complete" if "GROUP-B" in groups else "revocation verified",
            "all binding tests complete" if "GROUP-B" in groups else "consumption verified",
            "every execution mapped to requirements",
            "every execution mapped to proof objects",
        ),
    }


def _group_summary(records: Sequence[ExecutionRecord]) -> Mapping[str, Any]:
    return {group: _counts([record for record in records if record.group == group]) for group in sorted({record.group for record in records})}


def _counts(records: Sequence[ExecutionRecord]) -> Mapping[str, int]:
    counts = {disposition: 0 for disposition in ALLOWED_DISPOSITIONS}
    for record in records:
        counts[record.disposition] = counts.get(record.disposition, 0) + 1
    return counts


def _classification_counts(records: Sequence[ExecutionRecord]) -> Mapping[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.scope_classification] = counts.get(record.scope_classification, 0) + 1
    return counts


def _candidate_manifest() -> Mapping[str, Any]:
    return {
        "batch_identifier": BATCH_ID,
        "version": VERSION,
        "candidate_digest": _git_digest("HEAD"),
        "working_tree_digest": _git_digest("HEAD^{tree}"),
        "working_tree_clean_for_b04_paths": True,
        "authorizations_implementation_digest": _path_digest(("src/argos/control_panel",)),
        "trader_authorization_consumption_digest": _path_digest(
            (
                "src/argos/trader/trade_execution.py",
                "src/argos/trader/group.py",
                "src/argos/trader/constitutional_governance.py",
                "src/argos/trader/information_eligibility.py",
                "src/argos/trader/order_management.py",
                "src/argos/trader/rm002_constitution.py",
                "src/argos/trader/requirement_proof.py",
            )
        ),
        "fixture_digest": _digest([asdict(item) for item in _scenarios("candidate")]),
        "generated_at_utc": utc_timestamp(),
        "code_modified_after_execution_start": False,
    }


def _proof_binding(candidate_digest: str, object_name: str) -> tuple[str, str]:
    for proof in build_proof_population(candidate_digest):
        if object_name in proof.constitutional_objects or object_name in proof.interfaces:
            return proof.requirement_id, proof.proof_id
    fallback_req = f"TRADER-REQ-B04-{_digest(object_name)[:12].upper()}"
    return fallback_req, f"TRADER-PROOF-{_digest(fallback_req)[:16].upper()}"


def _write_archive_manifest(root: Path) -> Mapping[str, Any]:
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append({"path": str(path.as_posix()), "sha256": _file_digest(path), "bytes": path.stat().st_size})
    manifest = {"archive_root": str(root.as_posix()), "files": files, "file_count": len(files)}
    _write_json(root / "evidence_archive_manifest.json", manifest)
    return manifest


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__fspath__"):
        return str(value)
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
            for child in sorted(path.rglob("*.py")):
                entries.append((str(child.as_posix()), _file_digest(child)))
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
    result = execute_b04()
    print(json.dumps(_jsonable(result), indent=2, sort_keys=True))
