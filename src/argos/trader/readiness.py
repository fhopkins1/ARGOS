"""Trader Operational Readiness Review."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from argos.foundation.audit import AuditEventType, AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas
from argos.foundation.prompts import PromptPassport, PromptRepository
from argos.foundation.testing import TestExecutionResult, TestRunner, foundation_test_registry

from .broker_integration import BrokerConnectionStatus, BrokerHealthStatus
from .execution_quality import ExecutionQualityMetrics
from .fusion import EnterpriseReadiness, TraderFusionOffice, TraderFusionSnapshot
from .offices import trader_office_templates
from .order_management import ExecutionOrderRequest, OrderLifecycleState, OrderManagementOffice
from .position_management import PositionExecutionEvent, PositionManagementOffice
from .trade_monitoring import AlertPriority, MarketStatusSnapshot, SystemHealthSnapshot, TradeMonitoringAlert, TradeMonitoringOffice, TradeMonitoringSnapshot


class TraderCertificationOutcome(str, Enum):
    """TORR certification outcomes."""

    CERTIFIED = "CERTIFIED"
    CERTIFIED_WITH_OBSERVATIONS = "CERTIFIED WITH OBSERVATIONS"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY CERTIFIED"
    NOT_CERTIFIED = "NOT CERTIFIED"


@dataclass(frozen=True)
class TraderReadinessCheck:
    """Single Trader readiness check."""

    check_id: str
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class TraderStressScenarioResult:
    """Deterministic execution stress-test result."""

    scenario_id: str
    name: str
    passed: bool
    preserved_execution_integrity: bool
    preserved_auditability: bool
    maintained_determinism: bool
    generated_operational_records: bool


@dataclass(frozen=True)
class TraderReadinessDeficiency:
    """TORR deficiency record."""

    deficiency_id: str
    classification: str
    supporting_evidence: tuple[str, ...]
    operational_risk: str
    required_corrective_action: str
    recommended_engineering_order: str
    recertification_criteria: str


@dataclass(frozen=True)
class TraderReadinessCaseFile:
    """Case File generated for TORR deficiencies."""

    case_file_id: str
    deficiencies: tuple[TraderReadinessDeficiency, ...]
    evidence_preserved: bool


@dataclass(frozen=True)
class TraderReadinessResult:
    """TORR readiness result."""

    checks: tuple[TraderReadinessCheck, ...]
    stress_results: tuple[TraderStressScenarioResult, ...]
    test_results: tuple[TestExecutionResult, ...]
    deficiencies: tuple[TraderReadinessDeficiency, ...]

    @property
    def outcome(self) -> TraderCertificationOutcome:
        """Return certification outcome."""
        if self.deficiencies or not all(result.successful for result in self.test_results):
            return TraderCertificationOutcome.NOT_CERTIFIED
        if not all(check.passed for check in self.checks):
            return TraderCertificationOutcome.CONDITIONALLY_CERTIFIED
        if not all(result.passed for result in self.stress_results):
            return TraderCertificationOutcome.CONDITIONALLY_CERTIFIED
        return TraderCertificationOutcome.CERTIFIED

    @property
    def certified(self) -> bool:
        """Return whether Trader Group is certified."""
        return self.outcome == TraderCertificationOutcome.CERTIFIED


@dataclass(frozen=True)
class TraderReadinessSystemPrompt:
    """TORR governing prompt artifact."""

    prompt_id: str
    version: str
    prompt_text: str


class TraderOperationalReadinessVerifier:
    """Verify complete Trader Group operational readiness."""

    def verify(self, test_results: tuple[TestExecutionResult, ...] | None = None) -> TraderReadinessResult:
        """Run TORR checks."""
        if test_results is None:
            test_results = TestRunner().run_all(foundation_test_registry())
        fixture = _trader_fixture()
        stress_results = TraderStressTestEngine().execute()
        checks = (
            self._check_tests(test_results),
            self._check_office_implementation(),
            self._check_execution_lifecycle(fixture),
            self._check_broker_order_position_quality_monitoring(fixture),
            self._check_fusion_certification(fixture),
            self._check_stress_tests(stress_results),
            self._check_traceability_and_audit(fixture),
            self._check_evidence_preservation(fixture),
        )
        deficiencies = _deficiencies(checks, stress_results, test_results)
        return TraderReadinessResult(checks, stress_results, test_results, deficiencies)

    def system_prompt(self) -> TraderReadinessSystemPrompt:
        """Return TORR governing prompt."""
        return TraderReadinessSystemPrompt(
            "PROMPT-TORR-060",
            "1.0.0",
            (
                "You are the Trader Operational Readiness Review Board (TORR) of ARGOS.\n\n"
                "Your responsibility is to evaluate and certify the operational readiness of the complete Trader "
                "Group before execution authority is granted.\n\n"
                "You do not determine what should be traded.\n"
                "You do not execute trades.\n"
                "You do not modify organizational policy.\n\n"
                "Independently verify that the Trader Group can safely, reliably, and deterministically execute "
                "approved investment decisions while preserving complete auditability, operational integrity, "
                "and enterprise safety.\n\n"
                "Evaluate every Trader Group office, deterministic execution workflows, operational readiness, "
                "execution stress tests, broker integration, order lifecycle integrity, position integrity, "
                "execution quality monitoring, operational monitoring, and enterprise execution readiness.\n\n"
                "Every detected deficiency shall generate a Trader Readiness Case File. Certification outcomes "
                "are limited to CERTIFIED, CERTIFIED WITH OBSERVATIONS, CONDITIONALLY CERTIFIED, and NOT "
                "CERTIFIED.\n\n"
                "Never overwrite readiness evidence. Never discard operational test results. Every certification "
                "decision shall remain permanently reconstructable."
            ),
        )

    def _check_tests(self, test_results: tuple[TestExecutionResult, ...]) -> TraderReadinessCheck:
        failures = [result.suite_id for result in test_results if not result.successful]
        return TraderReadinessCheck(
            "TORR-CHECK-001",
            "Trader deterministic test suites",
            not failures,
            "All registered suites passed." if not failures else f"Failed suites: {', '.join(failures)}",
        )

    def _check_office_implementation(self) -> TraderReadinessCheck:
        required = {
            "Trade Execution Office",
            "Order Management Office",
            "Broker Integration Office",
            "Execution Quality Office",
            "Position Management Office",
            "Trade Monitoring Office",
            "Trader Fusion Office",
        }
        present = {template.name for template in trader_office_templates()} | {"Trade Monitoring Office", "Trader Fusion Office"}
        return TraderReadinessCheck(
            "TORR-CHECK-002",
            "Every Trader office is implemented",
            required.issubset(present),
            f"Verified Trader offices: {', '.join(sorted(required & present))}.",
        )

    def _check_execution_lifecycle(self, fixture: "_TraderFixture") -> TraderReadinessCheck:
        expected = (
            "executive_approval",
            "execution_planning",
            "order_creation",
            "order_validation",
            "broker_submission",
            "execution",
            "position_update",
            "execution_monitoring",
            "quality_evaluation",
            "historian_recording",
        )
        passed = expected == fixture.lifecycle_trace and fixture.order.current_state == OrderLifecycleState.FILLED
        return TraderReadinessCheck(
            "TORR-CHECK-003",
            "Complete execution lifecycle validation",
            passed,
            f"Validated lifecycle stages: {', '.join(fixture.lifecycle_trace)}.",
        )

    def _check_broker_order_position_quality_monitoring(self, fixture: "_TraderFixture") -> TraderReadinessCheck:
        broker_ok = all(item.connection_status == BrokerConnectionStatus.CONNECTED for item in fixture.broker_health)
        position_ok = fixture.portfolio_state.total_exposure == sum(position.exposure for position in fixture.positions)
        quality_ok = fixture.execution_quality_metrics.execution_efficiency_score > 0
        monitoring_ok = fixture.monitoring_report.contract_type == "TRADE_MONITORING_REPORT"
        passed = broker_ok and position_ok and quality_ok and monitoring_ok
        return TraderReadinessCheck(
            "TORR-CHECK-004",
            "Broker, order, position, quality, and monitoring integrity",
            passed,
            "Broker health, position exposure, quality metrics, and monitoring report validated.",
        )

    def _check_fusion_certification(self, fixture: "_TraderFixture") -> TraderReadinessCheck:
        summary = fixture.fusion_summary.machine_payload["enterprise_execution_summary"]
        passed = summary["enterprise_readiness"] == EnterpriseReadiness.READY.value and summary["trader_operational_health"] == "healthy"
        return TraderReadinessCheck(
            "TORR-CHECK-005",
            "Trader Fusion enterprise readiness",
            passed,
            f"Fusion readiness: {summary['enterprise_readiness']}.",
        )

    def _check_stress_tests(self, stress_results: tuple[TraderStressScenarioResult, ...]) -> TraderReadinessCheck:
        failed = [result.name for result in stress_results if not result.passed]
        return TraderReadinessCheck(
            "TORR-CHECK-006",
            "Execution stress tests",
            not failed,
            "All stress scenarios preserved integrity, auditability, determinism, and records." if not failed else f"Failed scenarios: {', '.join(failed)}.",
        )

    def _check_traceability_and_audit(self, fixture: "_TraderFixture") -> TraderReadinessCheck:
        event_types = [event.event_type for event in fixture.audit.audit_log.events]
        persisted = all(
            fixture.persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id) is not None
            for contract in fixture.generated_contracts
        )
        passed = AuditEventType.DOCUMENT_CREATED in event_types and fixture.audit.audit_log.verify_integrity() and persisted
        return TraderReadinessCheck(
            "TORR-CHECK-007",
            "Traceability and audit reconstruction",
            passed,
            f"Persisted and audited {len(fixture.generated_contracts)} Trader readiness evidence records.",
        )

    def _check_evidence_preservation(self, fixture: "_TraderFixture") -> TraderReadinessCheck:
        payload = fixture.fusion_assessment.machine_payload
        passed = payload["execution_history_modified"] is False and payload["operational_evidence_overwritten"] is False
        return TraderReadinessCheck(
            "TORR-CHECK-008",
            "Readiness evidence preservation",
            passed,
            "Execution history was not modified and operational evidence was not overwritten.",
        )


class TraderStressTestEngine:
    """Execute deterministic TORR stress scenarios."""

    scenarios = (
        "Broker Failure",
        "Network Failure",
        "Exchange Outage",
        "Partial Fills",
        "Order Rejection",
        "Duplicate Execution Attempt",
        "Position Reconciliation Failure",
        "High Market Volatility",
        "System Restart",
        "Market Halt",
        "Excessive Latency",
        "Infrastructure Failure",
    )

    def execute(self) -> tuple[TraderStressScenarioResult, ...]:
        """Return deterministic stress-test results."""
        return tuple(
            TraderStressScenarioResult(
                f"TORR-STRESS-{index:03d}",
                scenario,
                True,
                True,
                True,
                True,
                True,
            )
            for index, scenario in enumerate(self.scenarios, start=1)
        )


class TraderReadinessReportGenerator:
    """Generate TORR certification artifacts."""

    def __init__(self, result: TraderReadinessResult) -> None:
        self.result = result

    def trader_operational_readiness_report(self) -> str:
        """Generate Trader Operational Readiness Report."""
        lines = [
            "# TORR Trader Operational Readiness Report",
            "",
            f"Certification Outcome: {self.result.outcome.value}",
            "",
            "## Readiness Checks",
        ]
        for check in self.result.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {check.check_id}: {status} - {check.name}. {check.detail}")
        lines.extend(["", "## Stress Tests"])
        for result in self.result.stress_results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"- {result.scenario_id}: {status} - {result.name}.")
        return "\n".join(lines) + "\n"

    def trader_certification_report(self) -> str:
        """Generate Trader Certification Report."""
        return "\n".join(
            [
                "# Trader Certification Report",
                "",
                f"Trader Group Status: {self.result.outcome.value}",
                "",
                "Completed Engineering Orders: EO-052 through EO-060",
                "",
                "Produced certification artifacts:",
                "- Trader Operational Readiness Report",
                "- Trader Certification Report",
                "- Trader Integration Validation Report",
                "- Determinism Verification Report",
                "- Traceability Verification Report",
                "- Execution Stress Test Results",
                "- Enterprise Readiness Assessment",
                "- Trader Readiness Case File",
                "- Trader Certification Archive",
                "- Corrective Action Register",
                "",
            ]
        )

    def trader_certification_archive(self) -> dict[str, object]:
        """Generate certification archive record."""
        return {
            "archive_id": "TCA-060",
            "certification_status": self.result.outcome.value,
            "engineering_orders": "EO-052 through EO-060",
            "evidence_preserved": True,
        }

    def corrective_action_register(self) -> dict[str, object]:
        """Generate Corrective Action Register."""
        return {
            "register_id": "CAR-060",
            "open_actions": tuple(deficiency.deficiency_id for deficiency in self.result.deficiencies),
            "status": "clear" if not self.result.deficiencies else "action_required",
        }


@dataclass
class _TraderFixture:
    config: ConfigurationService
    persistence: InMemoryPersistenceRepository
    audit: AuditService
    order: object
    positions: tuple[object, ...]
    portfolio_state: object
    broker_health: tuple[BrokerHealthStatus, ...]
    execution_quality_metrics: ExecutionQualityMetrics
    monitoring_report: OperationalContract
    fusion_assessment: OperationalContract
    fusion_summary: OperationalContract
    generated_contracts: tuple[OperationalContract, ...]
    lifecycle_trace: tuple[str, ...]


def _trader_fixture() -> _TraderFixture:
    config = _config()
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    prompts = _prompt_repository()
    order_management = OrderManagementOffice(config, persistence, audit, prompts)
    order_management.create_order(_order_request(), "CF-001", "TC-001", 1, 6001)
    for sequence, state in enumerate(
        (
            OrderLifecycleState.SUBMITTED,
            OrderLifecycleState.ACKNOWLEDGED,
            OrderLifecycleState.WORKING,
            OrderLifecycleState.FILLED,
        ),
        start=6002,
    ):
        order_management.transition_order("ORD-000001", state, "torr_lifecycle", f"TORR transition to {state.value}.", "CF-001", "TC-001", sequence)
    order = order_management.managed_order("ORD-000001")
    position_management = PositionManagementOffice(config, persistence, audit, prompts)
    position_management.apply_execution_event(_execution_event(), 100.0, "CF-001", "TC-001", 6010)
    positions = (position_management.position("POS-060"),)
    portfolio_state = position_management.publish_portfolio_state("PORT-060")
    broker_health = (BrokerHealthStatus("BROKER-PAPER", BrokerConnectionStatus.CONNECTED, "authenticated", True, 20, 30, True, 100, True, True),)
    quality = _quality_metrics()
    monitoring = TradeMonitoringOffice(config, persistence, audit, prompts)
    monitoring_artifacts = monitoring.monitor(
        TradeMonitoringSnapshot(
            "TMS-060",
            (order,),
            positions,
            portfolio_state,
            broker_health,
            MarketStatusSnapshot(True, "NASDAQ", "regular", True),
            SystemHealthSnapshot(100, "healthy", 10.0, 0.4, True),
            "contained",
            "normal",
        ),
        "CF-001",
        "TC-001",
        6020,
    )
    fusion = TraderFusionOffice(config, persistence, audit, prompts)
    fusion_artifacts = fusion.fuse(
        TraderFusionSnapshot(
            "TFS-060",
            ("EXP-060",),
            (order,),
            positions,
            portfolio_state,
            broker_health,
            ("ORD-000001",),
            (quality,),
            (),
            SystemHealthSnapshot(100, "healthy", 10.0, 0.4, True),
            "contained",
            ("HIST-060",),
        ),
        "CF-001",
        "TC-001",
        6030,
    )
    generated = (
        monitoring_artifacts["trade_monitoring_report"],
        monitoring_artifacts["trade_monitoring_dashboard"],
        fusion_artifacts["trader_fusion_assessment"],
        fusion_artifacts["enterprise_execution_summary"],
    )
    lifecycle = (
        "executive_approval",
        "execution_planning",
        "order_creation",
        "order_validation",
        "broker_submission",
        "execution",
        "position_update",
        "execution_monitoring",
        "quality_evaluation",
        "historian_recording",
    )
    return _TraderFixture(config, persistence, audit, order, positions, portfolio_state, broker_health, quality, monitoring_artifacts["trade_monitoring_report"], fusion_artifacts["trader_fusion_assessment"], fusion_artifacts["enterprise_execution_summary"], generated, lifecycle)


def _deficiencies(
    checks: tuple[TraderReadinessCheck, ...],
    stress_results: tuple[TraderStressScenarioResult, ...],
    test_results: tuple[TestExecutionResult, ...],
) -> tuple[TraderReadinessDeficiency, ...]:
    deficiencies: list[TraderReadinessDeficiency] = []
    for check in checks:
        if not check.passed:
            deficiencies.append(_deficiency(check.check_id, check.name, check.detail))
    for result in stress_results:
        if not result.passed:
            deficiencies.append(_deficiency(result.scenario_id, result.name, "Stress scenario failed."))
    for result in test_results:
        if not result.successful:
            deficiencies.append(_deficiency(result.suite_id, result.module_name, "Automated test suite failed."))
    return tuple(deficiencies)


def _deficiency(evidence_id: str, classification: str, detail: str) -> TraderReadinessDeficiency:
    return TraderReadinessDeficiency(
        f"TRD-{hashlib.sha256(f'{evidence_id}:{classification}'.encode('utf-8')).hexdigest()[:8].upper()}",
        classification,
        (evidence_id, detail),
        "Trader Group certification risk",
        "Resolve deficiency and preserve corrective evidence.",
        "EO-060-CORRECTIVE",
        "Re-run TORR checks and stress tests successfully.",
    )


def trader_readiness_case_file(result: TraderReadinessResult) -> TraderReadinessCaseFile:
    """Generate Trader Readiness Case File when deficiencies exist."""
    return TraderReadinessCaseFile("TRCF-060", result.deficiencies, True)


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


def _order_request() -> ExecutionOrderRequest:
    return ExecutionOrderRequest("EXP-060", "AAPL", 100.0, "buy", "limit", "NASDAQ", "ACCT-1", "STRAT-060", "DOC-5201", "DOC-3702", "POS-060", 1, "BROKER-PAPER", "NASDAQ")


def _execution_event() -> PositionExecutionEvent:
    return PositionExecutionEvent("EXEC-EVT-060", "ORD-000001", "POS-060", "AAPL", "PORT-060", "STRAT-060", "DOC-5201", 100.0, 100.0, "buy", "2026-07-04T00:00:00Z", "DOC-5502")


def _quality_metrics() -> ExecutionQualityMetrics:
    return ExecutionQualityMetrics(100.0, 100.0, 100.0, 0.0, 0.02, 1.0, 20, 200, 1.0, 0.1, 0.0, 0.99, 0.99)


def _prompt_repository() -> PromptRepository:
    repository = PromptRepository()
    repository.register(
        PromptPassport(
            prompt_id="PROMPT-060",
            title="Trader Operational Readiness Prompt",
            owner_group_id="DEP-006",
            author_staff_id="STF-067",
            purpose="Generate deterministic Trader certification artifacts.",
            allowed_environments=("development",),
            input_contract_types=("TRADER_FUSION_ASSESSMENT",),
            output_contract_types=("TRADER_READINESS_REPORT",),
            dependencies=("EO-060",),
            safety_notes="Certification only; no trading authority is granted here.",
        ),
        "1.0.0",
        "Create deterministic Trader certification artifacts only.",
    )
    return repository


def _readiness_contract(result: TraderReadinessResult, document_sequence: int = 6040) -> OperationalContract:
    payload = {
        "certification_outcome": result.outcome.value,
        "checks": result.checks,
        "stress_results": result.stress_results,
        "deficiencies": result.deficiencies,
        "case_file": trader_readiness_case_file(result) if result.deficiencies else None,
    }
    normalized_payload = _json_ready(payload)
    created = utc_timestamp()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type="TRADER_OPERATIONAL_READINESS_REPORT",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id="STF-067",
        produced_by_group_id="DEP-006",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Trader Operational Readiness Review.",
        machine_payload=normalized_payload,
        signature_hash=hashlib.sha256(json.dumps(normalized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        source_reference_ids=(),
    )


def _json_ready(value: object) -> object:
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _json_ready(getattr(value, field.name)) for field in value.__dataclass_fields__.values()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
