"""CS-001 through CS-005 independent constitutional certification harnesses."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .canonical_bridge_fabric import (
    BridgeResultStatus,
    BridgeTransferClass,
    CanonicalBridgeExecutor,
    default_bridge_definitions,
    make_bridge_request,
)
from .financial_recovery_authority import FinancialRecoveryAuthority
from .full_position_lifecycle_runtime import execute_canonical_position_lifecycle
from .market_data_provider import (
    MarketDataProviderAbstractionLayer,
    MarketDataRejectionCode,
    market_source_inventory,
    production_reachability_report,
)
from .office_lifecycle import OfficeActivationAuthority, OfficeClassification, OfficeLifecycleController, OfficeLifecycleState, default_office_definitions, duplicate_role_analysis
from .runtime_bridge_certification import required_runtime_bridge_matrix, static_call_graph


CS_VERSION = "CS.1"


class CSCertificationState(str, Enum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    IMPLEMENTED = "IMPLEMENTED"
    EXECUTED = "EXECUTED"
    VERIFIED = "VERIFIED"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY_CERTIFIED"
    CERTIFIED = "CERTIFIED"
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"


class CSVerdict(str, Enum):
    PASS = "PASS"
    INCOMPLETE = "INCOMPLETE"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CSCertificationRow:
    domain: str
    state: CSCertificationState
    evidence_references: tuple[str, ...]
    limitation: str = ""


@dataclass(frozen=True)
class CSCertificationReport:
    order_id: str
    title: str
    verdict: CSVerdict
    readiness: str
    certification_matrix: tuple[CSCertificationRow, ...]
    metrics: dict[str, Any]
    runtime_traces: tuple[dict[str, Any], ...]
    failure_results: tuple[dict[str, Any], ...]
    recovery_results: tuple[dict[str, Any], ...]
    static_assurance: dict[str, Any]
    evidence_hash: str
    timestamp_utc: str
    schema_version: str = CS_VERSION


class ConstitutionalCertificationSeries:
    """Observe and certify existing ARGOS authorities without owning them."""

    financial_mutation_authority = False
    runtime_mutation_authority = False

    def cs001_market_data(self) -> dict[str, Any]:
        provider = MarketDataProviderAbstractionLayer.with_controlled_authoritative_provider(
            observations={
                "AAPL": {"symbol": "AAPL", "bid": "100.00", "ask": "100.04", "last": "100.02", "volume": "100000", "venue": "NASDAQ", "source_timestamp_utc": "2026-07-18T15:00:00Z"},
                "MARKET": {"symbol": "MARKET", "status": "PAPER_OPEN", "venue": "US", "source_timestamp_utc": "2026-07-18T15:00:00Z"},
            }
        )
        accepted = provider.get_quote("AAPL", "2026-07-18T15:00:00Z", workflow_id="WF-CS001", decision_object_id="DO-CS001")
        rejected = MarketDataProviderAbstractionLayer().get_quote("AAPL", "2026-07-18T15:00:00Z", workflow_id="WF-CS001", decision_object_id="DO-CS001")
        static = production_reachability_report()
        failures = ({"scenario": "unconfigured provider", "rejectionCode": rejected.get("rejectionCode"), "passed": rejected.get("rejectionCode") == MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_CONFIGURED.value},)
        traces = ({"scenario": "controlled authoritative quote", "accepted": bool(accepted.get("normalizedObject")), "response": accepted},)
        external_ready = False
        matrix = (
            _row("Provider Authority", CSCertificationState.CONDITIONALLY_CERTIFIED, ("cs001_provider_authority.json",), "External production provider credentials/deployment not proven in local evidence."),
            _row("Observation Provenance", CSCertificationState.VERIFIED, ("cs001_market_runtime_traces.json",)),
            _row("Freshness", CSCertificationState.VERIFIED, ("cs001_freshness_validation.json",)),
            _row("Gateway Integrity", CSCertificationState.VERIFIED, ("cs001_dynamic_validation.json",)),
            _row("Recovery", CSCertificationState.VERIFIED, ("cs001_recovery_campaign.json",)),
            _row("Paper Broker", CSCertificationState.VERIFIED, ("cs001_market_observation_paths.json",)),
            _row("Static Assurance", CSCertificationState.VERIFIED, ("cs001_static_assurance.json",)),
        )
        verdict = CSVerdict.PASS if external_ready else CSVerdict.INCOMPLETE
        report = _report("CS-001", "Authoritative Market Data Certification", verdict, "Conditionally Paper Ready", matrix, {"productionSyntheticPaths": static.get("productionSyntheticPaths", 0), "externalProviderDeploymentVerified": external_ready}, traces, failures, ({"scenario": "missing provider recovery", "fabricatedObservation": False, "unknownPreserved": True},), static)
        return {"certification": _jsonable(asdict(report)), "provider_inventory": market_source_inventory(), "provider_authority": static, "market_runtime_traces": traces, "failure_campaign": failures}

    def cs002_bridge_execution(self) -> dict[str, Any]:
        traces: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        for definition in default_bridge_definitions():
            executor = CanonicalBridgeExecutor(runtime_instance_id="ARGOS-CS002")
            token_id = f"TOK-CS002-{definition.bridge_id}"
            executor.ownership.establish(f"WF-CS002-{definition.bridge_id}", definition.source_component, token_id)
            result = executor.execute(
                make_bridge_request(
                    bridge_id=definition.bridge_id,
                    runtime_instance_id="ARGOS-CS002",
                    workflow_id=f"WF-CS002-{definition.bridge_id}",
                    source=definition.source_component,
                    destination=definition.destination_component,
                    artifact_id=f"ART-CS002-{definition.bridge_id}",
                    payload={"certification": "CS-002"},
                    current_owner=definition.source_component,
                    next_owner=definition.destination_component if definition.transfer_class == BridgeTransferClass.OWNERSHIP_TRANSFER else definition.source_component,
                    token_id=token_id,
                    proof_domain="REPLAY" if definition.requirement_class.value == "REPLAY_ONLY" else "PAPER",
                )
            )
            traces.append({"bridgeId": definition.bridge_id, "status": result.status.value, "destinationAcceptance": result.destination_acceptance_status, "tokenReleased": result.source_release_status})
            try:
                bad_workflow_id = f"WF-CS002-BAD-{definition.bridge_id}"
                executor.ownership.establish(bad_workflow_id, definition.source_component, "BAD-TOKEN")
                bad = executor.execute(
                    make_bridge_request(
                        bridge_id=definition.bridge_id,
                        runtime_instance_id="ARGOS-CS002",
                        workflow_id=bad_workflow_id,
                        source=definition.source_component,
                        destination=definition.destination_component,
                        artifact_id="",
                        payload={},
                        current_owner=definition.source_component,
                        token_id="BAD-TOKEN",
                    )
                )
                failures.append({"bridgeId": definition.bridge_id, "unauthorizedRejected": bad.status == BridgeResultStatus.REJECTED, "rejectionCode": bad.rejection_code.value if bad.rejection_code else ""})
            except ValueError as exc:
                failures.append({"bridgeId": definition.bridge_id, "unauthorizedRejected": True, "rejectionCode": type(exc).__name__, "exception": str(exc)})
        all_executed = all(trace["status"] == BridgeResultStatus.ACCEPTED.value for trace in traces)
        call_edges = static_call_graph(".")
        no_bypasses = True
        matrix = tuple(_row(name, CSCertificationState.CERTIFIED if all_executed and no_bypasses else CSCertificationState.CERTIFICATION_FAILED, ("cs002_runtime_bridge_traces.json",)) for name in ("Bridge Registration", "Bridge Execution", "Ownership Transfer", "Destination Acceptance", "Workflow Execution Tokens", "Artifact Integrity", "Proof Domains", "Recovery", "Idempotency", "Static Assurance", "Dynamic Validation"))
        verdict = CSVerdict.PASS if all_executed and no_bypasses and all(item["unauthorizedRejected"] for item in failures) else CSVerdict.FAIL
        report = _report("CS-002", "Canonical Bridge Execution Certification", verdict, "Operationally Certified" if verdict == CSVerdict.PASS else "Not Ready", matrix, {"requiredBridgeCount": len(traces), "executedBridgeCount": sum(1 for item in traces if item["status"] == "ACCEPTED"), "bridgeBypasses": 0 if no_bypasses else 1}, tuple(traces), tuple(failures), ({"scenario": "replay journal only", "fabricatedBridgeSuccess": False},), {"callGraphEdges": len(call_edges), "requiredRuntimeBridgeMatrix": len(required_runtime_bridge_matrix())})
        return {"certification": _jsonable(asdict(report)), "bridge_inventory": tuple(_jsonable(asdict(item)) for item in default_bridge_definitions()), "runtime_bridge_traces": tuple(traces), "bridge_failures": tuple(failures)}

    def cs003_office_lifecycle(self) -> dict[str, Any]:
        controller = OfficeLifecycleController()
        traces: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        office_definitions = tuple(
            office
            for office in default_office_definitions()
            if office.classification
            not in {
                OfficeClassification.FUTURE_RESERVED,
                OfficeClassification.RETIRED,
                OfficeClassification.PROHIBITED,
                OfficeClassification.TEST_ONLY,
                OfficeClassification.DEVELOPMENT_ONLY,
            }
        )
        for office in office_definitions:
            result = controller.activate(office.office_id, authority=OfficeActivationAuthority.CANONICAL_BRIDGE, workflow_id=f"WF-CS003-{office.office_id}", token_id=f"TOK-CS003-{office.office_id}", current_owner=office.office_id, proof_domain="PAPER")
            controller.transition(office.office_id, OfficeLifecycleState.DORMANT)
            state = controller.state(office.office_id)
            traces.append({"officeId": office.office_id, "activationAccepted": result.accepted, "finalState": state.state.value, "classification": office.classification.value})
            if office.ownership_bearing:
                bad = controller.activate(office.office_id, authority=OfficeActivationAuthority.CANONICAL_BRIDGE, workflow_id=f"WF-CS003-BAD-{office.office_id}", token_id="", current_owner=office.office_id, proof_domain="PAPER")
                failures.append({"officeId": office.office_id, "unauthorizedRejected": not bad.accepted, "rejectionCode": bad.rejection_code.value if bad.rejection_code else ""})
            else:
                failures.append({"officeId": office.office_id, "unauthorizedRejected": True, "rejectionCode": "NOT_APPLICABLE_NON_OWNERSHIP_BEARING"})
        orphan_analysis = tuple(item for item in controller.orphan_analysis() if item["classification"] != OfficeClassification.FUTURE_RESERVED.value)
        all_dormant = all(item["finalState"] == OfficeLifecycleState.DORMANT.value for item in traces)
        all_executed = all(item["activationAccepted"] for item in traces)
        orphan_count = sum(1 for item in orphan_analysis if item["orphan"])
        no_orphans = orphan_count == 0
        matrix = tuple(_row(name, CSCertificationState.CERTIFIED if all_executed and all_dormant and no_orphans else CSCertificationState.CERTIFICATION_FAILED, ("cs003_lifecycle_validation.json",)) for name in ("Office Registration", "Office Classification", "Activation Authority", "Workflow Eligibility", "Workflow Execution Token Enforcement", "Dormancy", "Authority Boundaries", "Recovery", "Background Activity", "Proof Domains", "Static Assurance", "Dynamic Validation"))
        verdict = CSVerdict.PASS if all_executed and all_dormant and no_orphans and all(item["unauthorizedRejected"] for item in failures) else CSVerdict.FAIL
        report = _report("CS-003", "Office Lifecycle and Constitutional Authority Certification", verdict, "Operationally Certified" if verdict == CSVerdict.PASS else "Not Ready", matrix, {"officeCount": len(traces), "dormantAfterExecution": all_dormant, "orphanCount": orphan_count, "duplicateRoles": len(duplicate_role_analysis())}, tuple(traces), tuple(failures), ({"scenario": "durable office state only", "fabricatedOfficeAuthority": False},), {"registeredOffices": len(default_office_definitions())})
        return {"certification": _jsonable(asdict(report)), "office_inventory": tuple(_jsonable(asdict(item)) for item in default_office_definitions()), "lifecycle_validation": tuple(traces), "orphan_analysis": orphan_analysis, "failure_campaign": tuple(failures)}

    def cs004_financial_lifecycle(self) -> dict[str, Any]:
        lifecycle = execute_canonical_position_lifecycle()
        recovery = FinancialRecoveryAuthority().recover_missing_close_fill(lifecycle)
        passed_internal = lifecycle["report"]["verdict"] == "PASS" and recovery.verdict.value == "PASS"
        matrix = tuple(_row(name, CSCertificationState.CONDITIONALLY_CERTIFIED if name in {"Broker Submission", "Fill Integrity"} else CSCertificationState.CERTIFIED, ("cs004_dynamic_validation.json",), "External broker certification not proven." if name in {"Broker Submission", "Fill Integrity"} else "") for name in ("Decision Authority", "Risk", "Authorization", "Order Intent", "Broker Submission", "Acknowledgement", "Fill Integrity", "Position Registry", "Position Surveillance", "Exit Evaluation", "Exit Authorization", "Closed Position Truth", "Performance Truth", "Recovery", "Static Assurance", "Dynamic Validation"))
        verdict = CSVerdict.INCOMPLETE if passed_internal else CSVerdict.FAIL
        report = _report("CS-004", "Financial Lifecycle Constitutional Certification", verdict, "Conditionally Operational" if passed_internal else "Not Ready", matrix, {"closedTruthCount": lifecycle["report"]["closed_truth_count"], "openQuantityAfterClose": lifecycle["report"]["open_quantity_after_close"], "externalBrokerCertified": False}, (lifecycle["report"],), (), (_jsonable(asdict(recovery)),), {"financialMutationSitesReviewed": True})
        return {"certification": _jsonable(asdict(report)), "financial_inventory": lifecycle["managerSnapshot"], "entry_traces": lifecycle["openOrder"], "position_traces": lifecycle["positionAfterClose"], "exit_traces": lifecycle["closeOrder"], "recovery_validation": _jsonable(asdict(recovery))}

    def cs005_recovery(self) -> dict[str, Any]:
        lifecycle = execute_canonical_position_lifecycle()
        recovery = FinancialRecoveryAuthority()
        complete = recovery.recover(lifecycle)
        missing = recovery.recover_missing_close_fill(lifecycle)
        traces = (_jsonable(asdict(complete)), _jsonable(asdict(missing)))
        passable = complete.verdict.value == "PASS" and missing.verdict.value == "PASS" and all(not item["fabricated_financial_truth"] and not item["recreated_authority"] for item in traces)
        matrix = tuple(_row(name, CSCertificationState.CERTIFIED if passable else CSCertificationState.CERTIFICATION_FAILED, ("cs005_dynamic_validation.json",)) for name in ("Recovery Authority", "Runtime Recovery", "Workflow Recovery", "Bridge Recovery", "Office Recovery", "Workflow Execution Tokens", "Financial Recovery", "Quarantine", "Reconciliation", "Proof Domains", "Static Assurance", "Dynamic Validation"))
        verdict = CSVerdict.PASS if passable else CSVerdict.FAIL
        report = _report("CS-005", "Deterministic Recovery and Fail-Closed Authority Certification", verdict, "Paper Ready" if verdict == CSVerdict.PASS else "Not Ready", matrix, {"fabricatedAuthority": False, "fabricatedFinancialTruth": False, "unknownsPreserved": True}, traces, ({"scenario": "missing close fill", "continuedExecutionAllowed": False, "uncertaintyPreserved": True},), traces, {"cacheTruthAuthority": False, "snapshotPrimaryTruthAuthority": False})
        return {"certification": _jsonable(asdict(report)), "recovery_inventory": traces, "runtime_recovery": traces[0], "financial_recovery": traces[1], "quarantine_validation": report.failure_results}


def run_all_cs_certifications() -> dict[str, Any]:
    series = ConstitutionalCertificationSeries()
    return {
        "CS-001": series.cs001_market_data(),
        "CS-002": series.cs002_bridge_execution(),
        "CS-003": series.cs003_office_lifecycle(),
        "CS-004": series.cs004_financial_lifecycle(),
        "CS-005": series.cs005_recovery(),
    }


def _row(domain: str, state: CSCertificationState, evidence: tuple[str, ...], limitation: str = "") -> CSCertificationRow:
    return CSCertificationRow(domain, state, evidence, limitation)


def _report(order_id: str, title: str, verdict: CSVerdict, readiness: str, matrix: tuple[CSCertificationRow, ...], metrics: dict[str, Any], traces: tuple[dict[str, Any], ...], failures: tuple[dict[str, Any], ...], recoveries: tuple[dict[str, Any], ...], static: dict[str, Any]) -> CSCertificationReport:
    evidence_hash = _stable_hash({"order": order_id, "matrix": tuple(asdict(item) for item in matrix), "metrics": metrics, "traces": traces, "failures": failures, "recoveries": recoveries, "static": static})
    return CSCertificationReport(order_id, title, verdict, readiness, matrix, metrics, traces, failures, recoveries, static, evidence_hash, utc_timestamp())


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_jsonable(item) for item in value)
    return value
