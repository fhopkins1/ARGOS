"""EO-010 Foundation integration and operational readiness checks."""

from __future__ import annotations

from dataclasses import dataclass

from argos.foundation.audit import AuditEventType, AuditService, TraceEngine
from argos.foundation.contracts import BaseContract, InfrastructureContract, OperationalContract
from argos.foundation.prompts import DependencyGraph, DependencyNode, DependencyNodeType
from argos.foundation.testing import TestExecutionResult, TestRunner, foundation_test_registry


@dataclass(frozen=True)
class ReadinessCheck:
    """Single deterministic readiness check result."""

    check_id: str
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ReadinessResult:
    """Foundation readiness verification result."""

    checks: tuple[ReadinessCheck, ...]
    test_results: tuple[TestExecutionResult, ...]

    @property
    def authorized(self) -> bool:
        """Return whether Foundation is authorized to proceed."""
        return all(check.passed for check in self.checks) and all(
            result.successful for result in self.test_results
        )


class FoundationReadinessVerifier:
    """Verify the Foundation as a unified deterministic platform."""

    def verify(
        self,
        test_results: tuple[TestExecutionResult, ...] | None = None,
    ) -> ReadinessResult:
        """Run readiness checks and return the result."""
        registry = foundation_test_registry()
        if test_results is None:
            test_results = TestRunner().run_all(registry)

        checks = (
            self._check_tests(test_results),
            self._check_dependency_graph(),
            self._check_contracts(),
            self._check_case_file_replay(),
            self._check_audit_reconstruction(),
        )
        return ReadinessResult(checks=checks, test_results=test_results)

    def _check_tests(self, test_results: tuple[TestExecutionResult, ...]) -> ReadinessCheck:
        failures = [result.suite_id for result in test_results if not result.successful]
        return ReadinessCheck(
            "ORR-CHECK-001",
            "Foundation deterministic test suites",
            not failures,
            "All registered suites passed." if not failures else f"Failed suites: {', '.join(failures)}",
        )

    def _check_dependency_graph(self) -> ReadinessCheck:
        graph = DependencyGraph()
        graph.add_node(DependencyNode("PB-006", DependencyNodeType.PROJECT_BIBLE, "Identifier Doctrine"))
        graph.add_node(DependencyNode("EO-002", DependencyNodeType.ENGINEERING_ORDER, "Identity"))
        graph.add_node(DependencyNode("EO-003", DependencyNodeType.ENGINEERING_ORDER, "Contracts"))
        graph.add_node(DependencyNode("EO-005", DependencyNodeType.ENGINEERING_ORDER, "Audit"))
        graph.add_node(DependencyNode("EO-008", DependencyNodeType.ENGINEERING_ORDER, "Prompts"))
        graph.add_node(DependencyNode("PROMPT-001", DependencyNodeType.PROMPT, "Readiness Prompt"))
        graph.add_node(DependencyNode("CF-001", DependencyNodeType.CASE_FILE, "Readiness Case File"))
        graph.add_dependency("EO-002", "PB-006")
        graph.add_dependency("EO-003", "EO-002")
        graph.add_dependency("EO-005", "EO-003")
        graph.add_dependency("EO-008", "EO-005")
        graph.add_dependency("PROMPT-001", "EO-008")
        graph.add_dependency("CF-001", "PROMPT-001")
        dependencies = graph.transitive_dependencies_for("CF-001")
        required = ("EO-002", "EO-003", "EO-005", "EO-008", "PB-006", "PROMPT-001")
        passed = dependencies == required
        return ReadinessCheck(
            "ORR-CHECK-002",
            "Dependency graph integrity",
            passed,
            f"CF-001 dependencies: {', '.join(dependencies)}",
        )

    def _check_contracts(self) -> ReadinessCheck:
        try:
            data = _valid_contract_data()
            BaseContract.from_dict(data)
            OperationalContract.from_dict(data)
            InfrastructureContract.from_dict(data)
        except Exception as exc:
            return ReadinessCheck(
                "ORR-CHECK-003",
                "Canonical data contract validation",
                False,
                str(exc),
            )
        return ReadinessCheck(
            "ORR-CHECK-003",
            "Canonical data contract validation",
            True,
            "Base, Operational, and Infrastructure contracts validated.",
        )

    def _check_case_file_replay(self) -> ReadinessCheck:
        audit_service = AuditService()
        contract = BaseContract.from_dict(_valid_contract_data())
        audit_service.record_document_creation(contract)
        audit_service.record_staff_decision(
            contract,
            staff_id="STF-001",
            group_id="DEP-001",
            decision="foundation_ready",
            rationale="Readiness replay fixture.",
        )
        replay = TraceEngine(audit_service.audit_log).replay_case_file("CF-001")
        passed = len(replay.events) == 2 and replay.document_ids == ("DOC-001",)
        return ReadinessCheck(
            "ORR-CHECK-004",
            "Complete Case File replay",
            passed,
            f"Replayed {len(replay.events)} events for CF-001.",
        )

    def _check_audit_reconstruction(self) -> ReadinessCheck:
        audit_service = AuditService()
        contract = BaseContract.from_dict(_valid_contract_data())
        audit_service.record_document_creation(contract)
        audit_service.record_validation_result(contract, "STF-001", "DEP-001", True, [])
        event_types = tuple(event.event_type for event in audit_service.search_by_case_file_id("CF-001"))
        passed = event_types == (
            AuditEventType.DOCUMENT_CREATED,
            AuditEventType.VALIDATION_RESULT,
        ) and audit_service.audit_log.verify_integrity()
        return ReadinessCheck(
            "ORR-CHECK-005",
            "Audit reconstruction",
            passed,
            "Audit event ordering and hash-chain integrity verified.",
        )


def _valid_contract_data() -> dict[str, object]:
    return {
        "contract_id": "DOC-001",
        "contract_type": "READINESS_CONTRACT",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "case_file_id": "CF-001",
        "trade_cycle_id": "TC-001",
        "parent_contract_ids": [],
        "produced_by_staff_id": "STF-001",
        "produced_by_group_id": "DEP-001",
        "intended_consumer_group_id": "DEP-002",
        "created_timestamp_utc": "2026-07-03T15:00:00Z",
        "updated_timestamp_utc": "2026-07-03T15:00:00Z",
        "validation_status": "valid",
        "validation_errors": [],
        "human_summary": "Foundation readiness contract.",
        "machine_payload": {"readiness": "eo-010"},
        "signature_hash": "d" * 64,
        "source_reference_ids": [],
    }

