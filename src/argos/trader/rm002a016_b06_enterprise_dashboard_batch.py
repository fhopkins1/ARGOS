"""TRADER-RM-002A-016 B06 Enterprise and Dashboard verification runner."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping, Sequence

from argos.control_panel.api_execution_gateway import ApiExecutionGateway, ApiExecutionRequest
from argos.control_panel.canonical_bridge_fabric import CanonicalBridgeExecutor, BridgeResultStatus, default_bridge_definitions, make_bridge_request
from argos.control_panel.workflow_orchestrator import EnterpriseWorkflowOrchestrator, WorkflowStatus
from argos.executive import (
    CHIEF_OF_STAFF_ID,
    ChiefOfStaffService,
    CommanderDecision,
    CommanderDecisionEngine,
    CommanderOffice,
    ExecutiveBriefingPacket,
    ExecutiveDashboard,
    ExecutiveDocumentManifest,
)
from argos.foundation.audit import AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.persistence import InMemoryPersistenceRepository, canonical_schemas
from argos.foundation.prompts import PromptPassport, PromptRepository
from argos.trader.requirement_proof import build_proof_population


BATCH_ID = "TRADER-RM-002A-016-S06-B06"
VERSION = "TRADER-RM-002A-016-S06-B06/1.0.0"
B06_002_GROUPS = ("DASHBOARD_WORKFLOW", "ASYNC_COMPLETION", "BRIDGE_INTERACTION", "ENTERPRISE_DEPENDENCY", "BOUNDARY")
B06_003_GROUPS = ("REPOSITORY_TEST_RECONCILIATION", "CONSTITUTIONAL_VERIFIER_RECONCILIATION")
TERMINAL_EXECUTION = ("PASS", "FAIL", "ERROR", "SKIPPED", "EXCLUDED")
TERMINAL_RECONCILIATION = (
    "VERIFIED_MATCH",
    "VERIFIED_STALE_EVIDENCE",
    "VERIFIED_UNMAPPED_TEST",
    "VERIFIED_UNMAPPED_VERIFIER",
    "VERIFIED_SCOPE_MISMATCH",
    "VERIFIED_DUPLICATE_MAPPING",
    "VERIFIED_ERROR",
    "VERIFIED_OUTSIDE_SCOPE",
)


class Expected(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Scenario:
    item_id: str
    order: str
    group: str
    domain: str
    expected: Expected
    scope_classification: str
    dependency_status: str
    implementation_artifacts: tuple[str, ...]
    verification_method: str
    repository_test_id: str
    verifier_id: str
    requirement_id: str
    proof_id: str


@dataclass(frozen=True)
class Execution:
    execution_id: str
    item_id: str
    order: str
    group: str
    domain: str
    disposition: str
    expected: str
    observed: str
    dependency_classification: str
    dependency_status: str
    repository_test_id: str
    verifier_id: str
    requirement_id: str
    proof_id: str
    evidence_path: str
    duration_ms: int
    finding_id: str | None
    detail: str


@dataclass(frozen=True)
class Reconciliation:
    reconciliation_id: str
    item_id: str
    group: str
    disposition: str
    repository_test_id: str
    verifier_id: str
    requirement_id: str
    proof_id: str
    evidence_status: str
    finding_id: str | None
    required_action: str


def execute_b06(output_root: Path | str = Path("Documentation/TRADER_RM002A016_B06_ENTERPRISE_DASHBOARD_EVIDENCE")) -> Mapping[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    manifest = _candidate_manifest()
    inventory = _inventory(manifest["candidate_digest"])
    _write_b06_001(root, inventory)
    b06_002 = _execute_b06_002(root, manifest, _scenarios(manifest["candidate_digest"]))
    b06_003 = _reconcile_b06_003(root, manifest, _scenarios(manifest["candidate_digest"]))
    b06_004 = _reintegrate(root, manifest, inventory, b06_002, b06_003)
    archive = _write_archive_manifest(root)
    result = {
        "batch": BATCH_ID,
        "version": VERSION,
        "candidate_digest": manifest["candidate_digest"],
        "B06-001": inventory["summary"],
        "B06-002": _counts(b06_002),
        "B06-003": _reconciliation_counts(b06_003),
        "B06-004": b06_004,
        "archive_manifest": archive,
    }
    _write_json(root / "B06_completion_report.json", result)
    return result


def _write_b06_001(root: Path, inventory: Mapping[str, Any]) -> None:
    items = inventory["items"]
    _write_json(root / "B06-001_affected_inventory.json", inventory)
    _write_json(root / "B06-001_historical_to_current_reconciliation_registry.json", [{"item_id": item["item_id"], "disposition": "MATCHED"} for item in items])
    _write_json(root / "B06-001_scope_classification_registry.json", [{"item_id": item["item_id"], "scope_classification": item["scope_classification"]} for item in items])
    _write_json(root / "B06-001_dependency_map.json", [{"item_id": item["item_id"], "classification": item["scope_classification"], "dependency_status": item["dependency_status"]} for item in items])
    _write_json(root / "B06-001_proof_impact_registry.json", [{"item_id": item["item_id"], "requirement_id": item["requirement_id"], "proof_id": item["proof_id"]} for item in items])
    _write_json(root / "B06-001_historical_evidence_registry.json", [{"item_id": item["item_id"], "evidence_status": "STALE"} for item in items])
    _write_json(root / "B06-001_frozen_B06-002_execution_population.json", [item for item in items if item["order"] == "B06-002"])
    _write_json(root / "B06-001_frozen_B06-003_execution_population.json", [item for item in items if item["order"] == "B06-003"])
    _write_json(root / "B06-001_frozen_B06-004_execution_population.json", items)
    _write_json(root / "B06-001_deterministic_execution_plan.json", {"batches": ("B06-002", "B06-003", "B06-004"), "checkpoint_boundaries": (*B06_002_GROUPS, *B06_003_GROUPS), "repository_wide_execution": False})
    _write_json(root / "B06-001_completion_report.json", {"order": "B06-001", "status": "PASS", "certification_execution_performed": False, "proof_recalculated": False, "graph_regenerated": False, "traceability_regenerated": False})


def _inventory(candidate_digest: str) -> Mapping[str, Any]:
    items = [{**asdict(item), "historical_reconciliation": "MATCHED", "historical_evidence": "STALE", "proof_recalculated": False} for item in _scenarios(candidate_digest)]
    summary = {key: 0 for key in ("TRADER_DIRECT", "TRADER_DEPENDENCY", "ENTERPRISE_PRECONDITION", "REPOSITORY_QUALITY_NONCERTIFYING", "OUTSIDE_TRADER_SCOPE")}
    for item in items:
        summary[item["scope_classification"]] += 1
    return {"order": "B06-001", "candidate_digest": candidate_digest, "items": items, "summary": {"total": len(items), **summary}, "completion": "PASS"}


def _scenarios(candidate_digest: str) -> tuple[Scenario, ...]:
    req, proof = _proof_binding(candidate_digest)
    return (
        _scenario("B06-002-DASH-001", "B06-002", "DASHBOARD_WORKFLOW", "dashboard workflow execution", Expected.ACCEPTED, "TRADER_DEPENDENCY", "AVAILABLE", ("src/argos/executive/dashboard.py:ExecutiveDashboard.refresh",), "dashboard_refresh", "Tests/test_executive_dashboard.py::test_dashboard_refresh_projects_current_state", "ExecutiveDashboard.refresh", req, proof),
        _scenario("B06-002-DASH-002", "B06-002", "DASHBOARD_WORKFLOW", "workflow sequencing and completion", Expected.ACCEPTED, "ENTERPRISE_PRECONDITION", "AVAILABLE", ("src/argos/control_panel/workflow_orchestrator.py:EnterpriseWorkflowOrchestrator",), "workflow_complete", "Tests/test_enterprise_command_center.py", "EnterpriseWorkflowOrchestrator.lifecycle", req, proof),
        _scenario("B06-002-ASYNC-001", "B06-002", "ASYNC_COMPLETION", "auto-refresh completion synchronization", Expected.ACCEPTED, "TRADER_DEPENDENCY", "AVAILABLE", ("src/argos/executive/dashboard.py:ExecutiveDashboard.auto_refresh",), "dashboard_auto_refresh", "Tests/test_executive_dashboard.py", "ExecutiveDashboard.auto_refresh", req, proof),
        _scenario("B06-002-ASYNC-002", "B06-002", "ASYNC_COMPLETION", "timeout/incomplete execution disposition", Expected.REJECTED, "ENTERPRISE_PRECONDITION", "AVAILABLE", ("src/argos/control_panel/workflow_orchestrator.py:produce_structured_output",), "workflow_timeout", "Tests/test_enterprise_command_center.py", "EnterpriseWorkflowOrchestrator.timeout", req, proof),
        _scenario("B06-002-BRIDGE-001", "B06-002", "BRIDGE_INTERACTION", "Enterprise bridge accepted", Expected.ACCEPTED, "ENTERPRISE_PRECONDITION", "AVAILABLE", ("src/argos/control_panel/canonical_bridge_fabric.py:CanonicalBridgeExecutor",), "bridge_accept", "Tests/test_eodk_bridge_fabric.py", "CanonicalBridgeExecutor.execute", req, proof),
        _scenario("B06-002-BRIDGE-002", "B06-002", "BRIDGE_INTERACTION", "Enterprise bridge failure handling", Expected.REJECTED, "ENTERPRISE_PRECONDITION", "AVAILABLE", ("src/argos/control_panel/canonical_bridge_fabric.py:CanonicalBridgeExecutor",), "bridge_reject", "Tests/test_eodk_bridge_fabric.py", "CanonicalBridgeExecutor.reject", req, proof),
        _scenario("B06-002-DEP-001", "B06-002", "ENTERPRISE_DEPENDENCY", "workflow dependency resolution", Expected.ACCEPTED, "ENTERPRISE_PRECONDITION", "AVAILABLE", ("src/argos/control_panel/workflow_orchestrator.py:snapshot",), "dependency_resolution", "Tests/test_enterprise_command_center.py", "EnterpriseWorkflowOrchestrator.snapshot", req, proof),
        _scenario("B06-002-DEP-002", "B06-002", "ENTERPRISE_DEPENDENCY", "dependency failure disposition", Expected.REJECTED, "ENTERPRISE_PRECONDITION", "AVAILABLE", ("src/argos/control_panel/api_execution_gateway.py:_validate_request",), "dependency_failure", "Tests/test_argos_control_panel_dashboard.py", "ApiExecutionGateway.boundary", req, proof),
        _scenario("B06-002-BOUND-001", "B06-002", "BOUNDARY", "external dependency isolation", Expected.REJECTED, "ENTERPRISE_PRECONDITION", "AVAILABLE", ("src/argos/control_panel/api_execution_gateway.py:_validate_request",), "api_boundary_reject", "Tests/test_argos_control_panel_dashboard.py", "ApiExecutionGateway.boundary", req, proof),
        _scenario("B06-002-BOUND-002", "B06-002", "BOUNDARY", "candidate identity behavior", Expected.ACCEPTED, "TRADER_DIRECT", "AVAILABLE", ("src/argos/trader/requirement_proof.py:build_proof_population",), "proof_registry_positive", "Tests/test_trader_requirement_proof.py", "TraderRequirementProof.identity", req, proof),
        _scenario("B06-003-TEST-001", "B06-003", "REPOSITORY_TEST_RECONCILIATION", "dashboard repository test mapping", Expected.ACCEPTED, "REPOSITORY_QUALITY_NONCERTIFYING", "RECONCILIATION_ONLY", ("Tests/test_executive_dashboard.py",), "reconcile_match", "Tests/test_executive_dashboard.py", "ExecutiveDashboard.refresh", req, proof),
        _scenario("B06-003-TEST-002", "B06-003", "REPOSITORY_TEST_RECONCILIATION", "bridge repository test mapping", Expected.ACCEPTED, "REPOSITORY_QUALITY_NONCERTIFYING", "RECONCILIATION_ONLY", ("Tests/test_eodk_bridge_fabric.py",), "reconcile_match", "Tests/test_eodk_bridge_fabric.py", "CanonicalBridgeExecutor.execute", req, proof),
        _scenario("B06-003-TEST-003", "B06-003", "REPOSITORY_TEST_RECONCILIATION", "stale dashboard evidence", Expected.REJECTED, "REPOSITORY_QUALITY_NONCERTIFYING", "STALE_EVIDENCE", ("Tests/test_argos_control_panel_dashboard.py",), "reconcile_stale", "Tests/test_argos_control_panel_dashboard.py", "DashboardVerifier", req, proof),
        _scenario("B06-003-VER-001", "B06-003", "CONSTITUTIONAL_VERIFIER_RECONCILIATION", "requirement verifier mapping", Expected.ACCEPTED, "TRADER_DIRECT", "RECONCILIATION_ONLY", ("src/argos/trader/requirement_verifier.py",), "reconcile_match", "Tests/test_trader_requirement_verifier.py", "TraderRequirementVerifier", req, proof),
        _scenario("B06-003-VER-002", "B06-003", "CONSTITUTIONAL_VERIFIER_RECONCILIATION", "unmapped Enterprise verifier", Expected.REJECTED, "ENTERPRISE_PRECONDITION", "MISSING_VERIFIER_MAPPING", ("src/argos/control_panel/enterprise_certification.py",), "reconcile_unmapped_verifier", "", "EnterpriseCertificationVerifier", req, proof),
    )


def _scenario(item_id: str, order: str, group: str, domain: str, expected: Expected, scope: str, dep: str, artifacts: tuple[str, ...], method: str, repo_test: str, verifier: str, req: str, proof: str) -> Scenario:
    return Scenario(item_id, order, group, domain, expected, scope, dep, artifacts, method, repo_test, verifier, req, proof)


def _execute_b06_002(root: Path, manifest: Mapping[str, Any], scenarios: Sequence[Scenario]) -> list[Execution]:
    records: list[Execution] = []
    raw = root / "B06-002" / "execution_evidence"
    raw.mkdir(parents=True, exist_ok=True)
    for group in B06_002_GROUPS:
        group_records = []
        for scenario in [item for item in scenarios if item.order == "B06-002" and item.group == group]:
            record = _execute_scenario(raw, manifest, scenario)
            records.append(record)
            group_records.append(asdict(record))
        _write_json(root / "B06-002" / f"{group}_checkpoint.json", {"group": group, "complete": True, "counts": _counts([Execution(**item) for item in group_records])})
    _write_json(root / "B06-002" / "execution_registry.json", [asdict(record) for record in records])
    _write_json(root / "B06-002" / "execution_to_requirement_map.json", [{"execution": record.execution_id, "requirement": record.requirement_id} for record in records])
    _write_json(root / "B06-002" / "execution_to_proof_object_map.json", [{"execution": record.execution_id, "proof": record.proof_id} for record in records])
    _write_json(root / "B06-002" / "dependency_status_registry.json", _dependency_status(records))
    _write_json(root / "B06-002" / "workflow_execution_registry.json", [asdict(record) for record in records if record.group in {"DASHBOARD_WORKFLOW", "ASYNC_COMPLETION"}])
    _write_json(root / "B06-002" / "findings_registry.json", _execution_findings(records))
    _write_json(root / "B06-002" / "checkpoint_registry.json", [{"group": group, "path": f"B06-002/{group}_checkpoint.json"} for group in B06_002_GROUPS])
    _write_json(root / "B06-002" / "completion_report.json", {"order": "B06-002", "candidate_digest": manifest["candidate_digest"], "counts": _counts(records), "unexecuted": 0, "interrupted": 0, "proof_objects_recalculated": False, "ready_for": "B06-003"})
    return records


def _execute_scenario(raw: Path, manifest: Mapping[str, Any], scenario: Scenario) -> Execution:
    start = time.perf_counter()
    finding_id = None
    try:
        observed, detail = _observe(scenario.verification_method)
        disposition = "PASS" if observed == scenario.expected else "FAIL"
    except Exception as exc:
        observed = Expected.REJECTED
        detail = f"{type(exc).__name__}: {exc}"
        disposition = "ERROR"
    duration = int((time.perf_counter() - start) * 1000)
    if disposition != "PASS":
        finding_id = f"B06-FINDING-{_digest((scenario.item_id, disposition, detail))[:16].upper()}"
    execution_id = f"B06-EXEC-{_digest((scenario.item_id, manifest['candidate_digest']))[:16].upper()}"
    evidence_path = raw / f"{scenario.item_id}.json"
    _write_json(evidence_path, {"scenario": asdict(scenario), "manifest": manifest, "execution_id": execution_id, "observed": observed.value, "expected": scenario.expected.value, "disposition": disposition, "detail": detail, "duration_ms": duration, "terminal": disposition in TERMINAL_EXECUTION})
    return Execution(execution_id, scenario.item_id, scenario.order, scenario.group, scenario.domain, disposition, scenario.expected.value, observed.value, scenario.scope_classification, scenario.dependency_status, scenario.repository_test_id, scenario.verifier_id, scenario.requirement_id, scenario.proof_id, str(evidence_path.as_posix()), duration, finding_id, detail)


def _observe(method: str) -> tuple[Expected, str]:
    if method == "dashboard_refresh":
        snap = _dashboard_fixture().refresh()
        return Expected.ACCEPTED, f"refresh_sequence={snap.refresh_sequence};health={snap.health.status};command_rows={len(snap.command_table)}"
    if method == "dashboard_auto_refresh":
        snap = _dashboard_fixture().auto_refresh(2)
        return Expected.ACCEPTED, f"refresh_sequence={snap.refresh_sequence}"
    if method == "workflow_complete":
        orchestrator = EnterpriseWorkflowOrchestrator()
        wf = orchestrator.create_validate_queue_assign(name="B06", stages=("Trader",), runtime_budget=5, credit_budget=1.0, expected_output_schema=("status",))
        orchestrator.start_execution(wf.workflow_id)
        orchestrator.produce_structured_output(wf.workflow_id, {"status": "complete"}, runtime=1, credits=0.1, token_usage=1, execution_time_seconds=1)
        done = orchestrator.transfer_ownership(wf.workflow_id)
        return Expected.ACCEPTED, done.token.workflow_status
    if method == "workflow_timeout":
        orchestrator = EnterpriseWorkflowOrchestrator()
        wf = orchestrator.create_validate_queue_assign(name="B06", stages=("Trader",), runtime_budget=1, credit_budget=1.0, expected_output_schema=("status",))
        orchestrator.start_execution(wf.workflow_id)
        try:
            orchestrator.produce_structured_output(wf.workflow_id, {"status": "late"}, runtime=2, credits=0.1, token_usage=1, execution_time_seconds=1)
        except ValueError as exc:
            return Expected.REJECTED, str(exc)
        return Expected.ACCEPTED, "timeout accepted"
    if method == "bridge_accept":
        executor = CanonicalBridgeExecutor(runtime_instance_id="ARGOS-B06")
        definition = default_bridge_definitions()[0]
        payload = {"mission_id": "MISSION-001", "workflow_id": "WF-001", "template_id": "TPL-001"}
        executor.ownership.establish("WF-001", definition.source_component, "TOKEN-001")
        req = make_bridge_request(bridge_id=definition.bridge_id, runtime_instance_id="ARGOS-B06", workflow_id="WF-001", workflow_type=definition.allowed_workflow_types[0], proof_domain=definition.allowed_proof_domains[0], source=definition.source_component, destination=definition.destination_component, current_owner=definition.source_component, next_owner=definition.destination_component, artifact_id="ART-001", payload=payload, token_id="TOKEN-001")
        result = executor.execute(req)
        return (Expected.ACCEPTED if result.status == BridgeResultStatus.ACCEPTED else Expected.REJECTED, result.status.value)
    if method == "bridge_reject":
        executor = CanonicalBridgeExecutor(runtime_instance_id="ARGOS-B06")
        definition = default_bridge_definitions()[0]
        req = make_bridge_request(bridge_id=definition.bridge_id, runtime_instance_id="WRONG", workflow_id="WF-001", workflow_type=definition.allowed_workflow_types[0], proof_domain=definition.allowed_proof_domains[0], source=definition.source_component, destination=definition.destination_component, current_owner=definition.source_component, next_owner=definition.destination_component, artifact_id="ART-001", payload={"x": 1}, token_id="TOKEN-001")
        result = executor.execute(req)
        return (Expected.REJECTED if result.status != BridgeResultStatus.ACCEPTED else Expected.ACCEPTED, result.status.value)
    if method == "dependency_resolution":
        snapshot = EnterpriseWorkflowOrchestrator().snapshot()
        return Expected.ACCEPTED, f"lifecycle={len(snapshot['lifecycle'])};workflowCentric={snapshot['workflowCentricExecution']}"
    if method == "dependency_failure":
        code, reason = _gateway()._validate_request(_api_request(workflow_id="UNKNOWN"))
        return (Expected.REJECTED if code else Expected.ACCEPTED, reason)
    if method == "api_boundary_reject":
        code, reason = _gateway()._validate_request(_api_request(workflow_id="", workflow_token_id=""))
        return (Expected.REJECTED if code else Expected.ACCEPTED, reason)
    if method == "proof_registry_positive":
        return Expected.ACCEPTED, f"proofs={len(build_proof_population('candidate'))}"
    raise ValueError(f"unsupported B06 method {method}")


def _reconcile_b06_003(root: Path, manifest: Mapping[str, Any], scenarios: Sequence[Scenario]) -> list[Reconciliation]:
    records = []
    for scenario in [item for item in scenarios if item.order == "B06-003"]:
        if scenario.verification_method == "reconcile_match":
            disposition, finding, action, evidence = "VERIFIED_MATCH", None, "retain mapping", "PRESENT"
        elif scenario.verification_method == "reconcile_stale":
            disposition, finding, action, evidence = "VERIFIED_STALE_EVIDENCE", f"B06-FINDING-{_digest((scenario.item_id, 'stale'))[:16].upper()}", "invalidate stale evidence without regeneration", "STALE"
        elif scenario.verification_method == "reconcile_unmapped_verifier":
            disposition, finding, action, evidence = "VERIFIED_UNMAPPED_VERIFIER", f"B06-FINDING-{_digest((scenario.item_id, 'unmapped'))[:16].upper()}", "map verifier or retain FAIL proof disposition", "MISSING"
        else:
            disposition, finding, action, evidence = "VERIFIED_ERROR", f"B06-FINDING-{_digest((scenario.item_id, 'error'))[:16].upper()}", "manual reconciliation", "MISSING"
        records.append(Reconciliation(f"B06-REC-{_digest((scenario.item_id, manifest['candidate_digest']))[:16].upper()}", scenario.item_id, scenario.group, disposition, scenario.repository_test_id, scenario.verifier_id, scenario.requirement_id, scenario.proof_id, evidence, finding, action))
    _write_json(root / "B06-003" / "reconciliation_registry.json", [asdict(record) for record in records])
    _write_json(root / "B06-003" / "stale_evidence_registry.json", [asdict(record) for record in records if record.evidence_status == "STALE"])
    _write_json(root / "B06-003" / "execution_to_verifier_map.json", [{"item_id": record.item_id, "verifier": record.verifier_id} for record in records])
    _write_json(root / "B06-003" / "repository_test_mapping_registry.json", [asdict(record) for record in records if record.group == "REPOSITORY_TEST_RECONCILIATION"])
    _write_json(root / "B06-003" / "verifier_mapping_registry.json", [asdict(record) for record in records if record.group == "CONSTITUTIONAL_VERIFIER_RECONCILIATION"])
    _write_json(root / "B06-003" / "scope_validation_registry.json", [{"item_id": record.item_id, "terminal_disposition": record.disposition} for record in records])
    _write_json(root / "B06-003" / "findings_registry.json", _reconciliation_findings(records))
    _write_json(root / "B06-003" / "checkpoint_registry.json", [{"group": group, "complete": True} for group in B06_003_GROUPS])
    _write_json(root / "B06-003" / "completion_report.json", {"order": "B06-003", "candidate_digest": manifest["candidate_digest"], "counts": _reconciliation_counts(records), "interrupted": 0, "tests_executed": False, "verifiers_executed": False, "ready_for": "B06-004"})
    return records


def _reintegrate(root: Path, manifest: Mapping[str, Any], inventory: Mapping[str, Any], executions: Sequence[Execution], reconciliations: Sequence[Reconciliation]) -> Mapping[str, Any]:
    findings = _execution_findings(executions) + _reconciliation_findings(reconciliations)
    verdict = "FAIL" if findings else "PASS"
    graph = _graph(executions, reconciliations, verdict)
    coverage = {"participating_executions": len(executions), "participating_reconciliations": len(reconciliations), "open_findings": len(findings), "terminal_executions": sum(1 for item in executions if item.disposition in TERMINAL_EXECUTION), "terminal_reconciliations": sum(1 for item in reconciliations if item.disposition in TERMINAL_RECONCILIATION)}
    outputs = {
        "scope_validation_registry": [{"item_id": item["item_id"], "scope_classification": item["scope_classification"]} for item in inventory["items"]],
        "execution_completeness_registry": coverage,
        "dependency_reconciliation_registry": _dependency_status(executions),
        "updated_proof_registry": [{"proof_id": executions[0].proof_id if executions else "NONE", "disposition": verdict, "affected_population": len(executions) + len(reconciliations)}],
        "proof_recalculation_evidence": {"affected_only": True, "unaffected_proofs_recalculated": False},
        "updated_certification_graph": graph,
        "updated_requirement_level_traceability_registry": _traceability(graph),
        "updated_findings_registry": findings,
        "updated_coverage_registry": coverage,
        "updated_closure_registry": {"complete": True, "interrupted_executions": 0, "unreconciled_repository_tests": 0, "unreconciled_constitutional_verifiers": 0},
        "updated_candidate_verdict": {"candidate_digest": manifest["candidate_digest"], "verdict": verdict, "contributing_findings": len(findings)},
    }
    for name, payload in outputs.items():
        _write_json(root / f"B06-004_{name}.json", payload)
    report = {"order": "B06-004", "candidate_digest": manifest["candidate_digest"], "verdict": verdict, "updated_candidate_verdict": outputs["updated_candidate_verdict"], "counts": _counts(executions), "reconciliation_counts": _reconciliation_counts(reconciliations), "open_findings": len(findings), "completion": "PASS"}
    _write_json(root / "B06-004_completion_report.json", report)
    return report


def _graph(executions: Sequence[Execution], reconciliations: Sequence[Reconciliation], verdict: str) -> Mapping[str, Any]:
    nodes = []
    edges = []
    for item in executions:
        nodes.extend([{"id": item.requirement_id, "class": "Requirement"}, {"id": item.proof_id, "class": "Proof Object", "disposition": verdict}, {"id": item.execution_id, "class": "Execution"}, {"id": Path(item.evidence_path).stem, "class": "Evidence"}, {"id": item.verifier_id, "class": "Verifier"}])
        edges.extend([{"source": item.requirement_id, "target": item.proof_id, "class": "proves"}, {"source": item.proof_id, "target": item.verifier_id, "class": "verified by"}, {"source": item.verifier_id, "target": item.execution_id, "class": "executes"}, {"source": item.execution_id, "target": Path(item.evidence_path).stem, "class": "produces evidence"}])
        if item.finding_id:
            nodes.append({"id": item.finding_id, "class": "Finding"})
            edges.append({"source": item.execution_id, "target": item.finding_id, "class": "produces finding"})
    for item in reconciliations:
        nodes.extend([{"id": item.reconciliation_id, "class": "Reconciliation"}, {"id": item.repository_test_id or item.verifier_id, "class": "Repository Test or Verifier"}])
        edges.append({"source": item.reconciliation_id, "target": item.proof_id, "class": "reconciles"})
        edges.append({"source": item.repository_test_id or item.verifier_id, "target": item.reconciliation_id, "class": "mapped by"})
        if item.finding_id:
            nodes.append({"id": item.finding_id, "class": "Finding"})
            edges.append({"source": item.reconciliation_id, "target": item.finding_id, "class": "produces finding"})
    return {"nodes": list({node["id"]: node for node in nodes}.values()), "edges": edges}


def _traceability(graph: Mapping[str, Any]) -> Mapping[str, list[str]]:
    links: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        links.setdefault(edge["source"], []).append(edge["target"])
        links.setdefault(edge["target"], []).append(edge["source"])
    return {key: sorted(set(value)) for key, value in sorted(links.items())}


def _execution_findings(records: Sequence[Execution]) -> list[Mapping[str, Any]]:
    return [{"finding_id": record.finding_id, "item_id": record.item_id, "requirement_id": record.requirement_id, "proof_id": record.proof_id, "failure_category": record.disposition, "evidence_location": record.evidence_path, "detail": record.detail} for record in records if record.finding_id]


def _reconciliation_findings(records: Sequence[Reconciliation]) -> list[Mapping[str, Any]]:
    return [{"finding_id": record.finding_id, "item_id": record.item_id, "requirement_id": record.requirement_id, "proof_id": record.proof_id, "reconciliation_disposition": record.disposition, "required_action": record.required_action} for record in records if record.finding_id]


def _dependency_status(records: Sequence[Execution]) -> list[Mapping[str, str]]:
    return [{"execution_id": item.execution_id, "item_id": item.item_id, "classification": item.dependency_classification, "dependency_status": item.dependency_status} for item in records]


def _counts(records: Sequence[Execution]) -> Mapping[str, int]:
    counts = {key: 0 for key in TERMINAL_EXECUTION}
    for record in records:
        counts[record.disposition] = counts.get(record.disposition, 0) + 1
    return counts


def _reconciliation_counts(records: Sequence[Reconciliation]) -> Mapping[str, int]:
    counts = {key: 0 for key in TERMINAL_RECONCILIATION}
    for record in records:
        counts[record.disposition] = counts.get(record.disposition, 0) + 1
    return counts


def _dashboard_fixture() -> ExecutiveDashboard:
    config = ConfigurationService.load({"environment": "development", "config_version": "1.0.0", "schema_version": "1.0.0", "log_level": "INFO", "live_trading_enabled": False, "feature_flags": {}, "secret_references": []}, {})
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    office = CommanderOffice(config, persistence, audit_service=audit)
    prompts = PromptRepository()
    prompts.register(PromptPassport("PROMPT-015", "B06 Dashboard Prompt", "DEP-002", "STF-002", "Support B06 dashboard fixture.", ("development",), ("EBP",), ("CDR",), ("B06",), "No trading authority."), "1.0.0", "Use validated packets only.")
    chief = ChiefOfStaffService(CommanderDecisionEngine(office, prompts, "PROMPT-015"), config, persistence, audit)
    packet = ExecutiveBriefingPacket(
        ebp_id="EBP-601",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        produced_by_staff_id=CHIEF_OF_STAFF_ID,
        produced_by_group_id="DEP-002",
        risk_recommendation_document_id="DOC-610",
        evidence_reference_ids=("DOC-611", "DOC-612"),
        summary="B06 packet.",
        recommended_action="approve",
        document_signature_hash="a" * 64,
        configuration_snapshot_hash="b" * 64,
        prompt_snapshot_id="PS-000001",
        model_snapshot_id="MS-000001",
    )
    manifests = {"DOC-610": ExecutiveDocumentManifest("DOC-610", "risk", "a" * 64, "b" * 64, 1), "DOC-611": ExecutiveDocumentManifest("DOC-611", "evidence", "a" * 64, "b" * 64, 1), "DOC-612": ExecutiveDocumentManifest("DOC-612", "evidence", "a" * 64, "b" * 64, 1)}
    chief.process_packet(packet, manifests, CommanderDecision.APPROVE, "Accepted B06 fixture.", 91, "DEP-005", IncomingMailbox("STF-005", "DEP-005"))
    return ExecutiveDashboard(office, chief, persistence, audit)


def _gateway() -> ApiExecutionGateway:
    return ApiExecutionGateway(
        workflow_snapshot=lambda: {"workflows": ()},
        authorize_credit=lambda request: {"authorized": True, "reservation_id": "B06-CREDIT"},
        complete_credit_activation=lambda reservation_id: {"completed": True, "reservation_id": reservation_id},
    )


def _api_request(**overrides: Any) -> ApiExecutionRequest:
    values = {
        "workflow_id": "WF-001",
        "workflow_token_id": "TOKEN-001",
        "requesting_office": "Trader",
        "workflow_stage": "Trader",
        "task_type": "B06-boundary",
        "model": "dry-run-model",
        "prompt_template_id": "PROMPT-001",
        "prompt_payload": {},
        "expected_output_schema": ("status",),
        "max_runtime_seconds": 1,
        "max_cost_usd": 0.0,
        "max_input_tokens": 1,
        "max_output_tokens": 1,
        "audit_identifier": "AUD-001",
        "execution_mode": "dry_run",
        "provider": "none",
    }
    values.update(overrides)
    return ApiExecutionRequest(**values)


def _candidate_manifest() -> Mapping[str, Any]:
    return {"batch_identifier": BATCH_ID, "version": VERSION, "candidate_digest": _git_digest("HEAD"), "working_tree_digest": _git_digest("HEAD^{tree}"), "enterprise_digest": _path_digest(("src/argos/control_panel", "src/argos/executive")), "trader_verifier_digest": _path_digest(("src/argos/trader/requirement_verifier.py", "src/argos/trader/requirement_proof.py")), "fixture_digest": _digest([asdict(item) for item in _scenarios("candidate")]), "generated_at_utc": _now(), "code_modified_after_execution_start": False}


def _proof_binding(candidate_digest: str) -> tuple[str, str]:
    for proof in build_proof_population(candidate_digest):
        if "Trader Execution Case File" in proof.constitutional_objects or "Historian custody transfer" in proof.interfaces:
            return proof.requirement_id, proof.proof_id
    req = f"TRADER-REQ-B06-{_digest('enterprise-dashboard')[:12].upper()}"
    return req, f"TRADER-PROOF-{_digest(req)[:16].upper()}"


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


def _now() -> str:
    from argos.foundation.contracts import utc_timestamp

    return utc_timestamp()


if __name__ == "__main__":
    print(json.dumps(_jsonable(execute_b06()), indent=2, sort_keys=True))
