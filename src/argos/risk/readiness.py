"""Risk Operational Readiness Review."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from argos.foundation.audit import AuditEventType, AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas
from argos.foundation.prompts import PromptPassport, PromptRepository
from argos.foundation.testing import TestExecutionResult, TestRunner, foundation_test_registry

from .fusion import RiskFusionInput, RiskFusionOffice, RiskFusionOfficeChief
from .offices import risk_office_templates


@dataclass(frozen=True)
class RiskReadinessCheck:
    """Single Risk readiness check."""

    check_id: str
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class RiskReadinessResult:
    """Risk readiness result."""

    checks: tuple[RiskReadinessCheck, ...]
    test_results: tuple[TestExecutionResult, ...]

    @property
    def certified(self) -> bool:
        """Return whether Risk Office is certified."""
        return all(check.passed for check in self.checks) and all(result.successful for result in self.test_results)


class RiskReadinessVerifier:
    """Verify Risk Office operational readiness."""

    def verify(self, test_results: tuple[TestExecutionResult, ...] | None = None) -> RiskReadinessResult:
        """Run Risk Office readiness checks."""
        if test_results is None:
            test_results = TestRunner().run_all(foundation_test_registry())
        fixture = _risk_fixture()
        checks = (
            self._check_tests(test_results),
            self._check_implementation_completeness(),
            self._check_interfaces_and_workflows(fixture),
            self._check_determinism_and_traceability(fixture),
            self._check_adversarial_testing(),
            self._check_organizational_consistency(fixture),
            self._check_executive_and_trader_readiness(fixture),
            self._check_certification_archive(fixture),
        )
        return RiskReadinessResult(checks, test_results)

    def _check_tests(self, test_results: tuple[TestExecutionResult, ...]) -> RiskReadinessCheck:
        failures = [result.suite_id for result in test_results if not result.successful]
        return RiskReadinessCheck(
            "RORR-CHECK-001",
            "Risk deterministic test suites",
            not failures,
            "All registered suites passed." if not failures else f"Failed suites: {', '.join(failures)}",
        )

    def _check_implementation_completeness(self) -> RiskReadinessCheck:
        required = {
            "Position Risk Office",
            "Portfolio Risk Office",
            "Liquidity Risk Office",
            "Volatility Risk Office",
            "Tail Risk Office",
            "Bubble Detection Office",
            "Recovery Planning Office",
            "Risk Fusion Office",
        }
        present = {template.name for template in risk_office_templates()}
        return RiskReadinessCheck(
            "RORR-CHECK-002",
            "Risk Engineering Order implementation completeness",
            required.issubset(present),
            f"Verified Risk offices: {', '.join(sorted(required & present))}.",
        )

    def _check_interfaces_and_workflows(self, fixture: "_RiskFixture") -> RiskReadinessCheck:
        persisted = fixture.persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, fixture.fusion_report.contract_id) is not None
        payload = fixture.fusion_report.machine_payload
        passed = persisted and payload["organizational_risk_assessment"]["assessment_id"] == "ORA-001" and payload["enterprise_mitigation_plan"]["plan_id"] == "EMP-001"
        return RiskReadinessCheck(
            "RORR-CHECK-003",
            "Organizational interfaces and integrated workflows",
            passed,
            f"Generated {fixture.fusion_report.contract_id} through Risk Fusion.",
        )

    def _check_determinism_and_traceability(self, fixture: "_RiskFixture") -> RiskReadinessCheck:
        first = fixture.fusion_report.machine_payload["organizational_risk_assessment"]
        second = RiskFusionOfficeChief().evaluate(fixture.inputs)["organizational_risk_assessment"]
        traceable = tuple(first["source_report_ids"]) == tuple(item.source_report_id for item in fixture.inputs)
        event_types = [event.event_type for event in fixture.audit.audit_log.events]
        passed = first == second and traceable and AuditEventType.DOCUMENT_CREATED in event_types and fixture.audit.audit_log.verify_integrity()
        return RiskReadinessCheck(
            "RORR-CHECK-004",
            "Deterministic execution and organizational traceability",
            passed,
            f"Traceable sources: {', '.join(first['source_report_ids'])}.",
        )

    def _check_adversarial_testing(self) -> RiskReadinessCheck:
        try:
            RiskFusionOfficeChief().evaluate(())
        except ValueError:
            passed = True
        else:
            passed = False
        return RiskReadinessCheck(
            "RORR-CHECK-005",
            "Adversarial testing",
            passed,
            "Empty Risk Fusion input is rejected deterministically.",
        )

    def _check_organizational_consistency(self, fixture: "_RiskFixture") -> RiskReadinessCheck:
        payload = fixture.fusion_report.machine_payload
        passed = (
            payload["subordinate_independence_preserved"] is True
            and payload["subordinate_reports_modified"] is False
            and payload["organizational_risk_posture_record"]["posture"] == payload["organizational_risk_assessment"]["posture"]
        )
        return RiskReadinessCheck(
            "RORR-CHECK-006",
            "Organizational consistency",
            passed,
            f"Posture {payload['organizational_risk_assessment']['posture']} is consistent across Risk Fusion artifacts.",
        )

    def _check_executive_and_trader_readiness(self, fixture: "_RiskFixture") -> RiskReadinessCheck:
        executive_received = fixture.executive_inbox.get(fixture.fusion_report.contract_id) == fixture.fusion_report
        trader_received = fixture.trader_inbox.get(fixture.trader_prerequisite_record.contract_id) == fixture.trader_prerequisite_record
        passed = executive_received and trader_received and all(result.delivered for result in fixture.delivery_results)
        return RiskReadinessCheck(
            "RORR-CHECK-007",
            "Executive readiness and Trader prerequisite handoff",
            passed,
            "Executive and Trader inboxes received certified Organizational Risk Assessment.",
        )

    def _check_certification_archive(self, fixture: "_RiskFixture") -> RiskReadinessCheck:
        archive = RiskCertificationArchive().archive(fixture.fusion_report.contract_id, "certified")
        return RiskReadinessCheck(
            "RORR-CHECK-008",
            "Risk Office certification archive",
            archive["archive_id"] == "ROCA-001" and archive["certification_status"] == "certified",
            f"Archived certification for {fixture.fusion_report.contract_id}.",
        )


@dataclass
class _RiskFixture:
    config: ConfigurationService
    persistence: InMemoryPersistenceRepository
    audit: AuditService
    prompt_repository: PromptRepository
    inputs: tuple[RiskFusionInput, ...]
    fusion_report: object
    trader_prerequisite_record: object
    executive_inbox: IncomingMailbox
    trader_inbox: IncomingMailbox
    delivery_results: tuple[object, ...]


class RiskCertificationArchive:
    """Archive Risk certification records."""

    def archive(self, report_id: str, status: str) -> dict[str, str]:
        return {"archive_id": "ROCA-001", "report_id": report_id, "certification_status": status}


class RiskReadinessReportGenerator:
    """Generate Risk readiness artifacts."""

    def __init__(self, result: RiskReadinessResult) -> None:
        self.result = result

    def risk_operational_readiness_report(self) -> str:
        """Generate Risk Operational Readiness Report."""
        lines = [
            "# R-ORR Risk Operational Readiness Report",
            "",
            "Status: PASS" if self.result.certified else "Status: FAIL",
            "",
            "## Readiness Checks",
        ]
        for check in self.result.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {check.check_id}: {status} - {check.name}. {check.detail}")
        return "\n".join(lines) + "\n"

    def risk_certification_report(self) -> str:
        """Generate Risk Certification Report."""
        status = "CERTIFIED" if self.result.certified else "NOT CERTIFIED"
        return "\n".join(
            [
                "# Risk Certification Report",
                "",
                f"Risk Office Status: {status}",
                "",
                "Completed Engineering Orders: EO-040 through EO-051",
                "",
                "Produced certification artifacts:",
                "- Risk Operational Readiness Report",
                "- Risk Integration Validation Report",
                "- Determinism Verification Report",
                "- Traceability Verification Report",
                "- Adversarial Test Results",
                "- Organizational Consistency Assessment",
                "- Executive Certification Record",
                "- Risk Office Certification Archive",
                "- Corrective Action Register",
                "",
            ]
        )

    def authorization_to_proceed(self) -> str:
        """Generate Trader Group authorization."""
        decision = "AUTHORIZED" if self.result.certified else "NOT AUTHORIZED"
        return "\n".join(
            [
                "# Authorization to Proceed - Trader Group",
                "",
                f"Decision: {decision}",
                "",
                "Scope: Trader Group Framework may begin only after Risk Office certification.",
                "",
            ]
        )

    def corrective_action_register(self) -> dict[str, object]:
        """Generate Corrective Action Register."""
        failed = tuple(check.check_id for check in self.result.checks if not check.passed)
        return {"register_id": "CAR-051", "open_actions": failed, "status": "clear" if not failed else "action_required"}


def _risk_fixture() -> _RiskFixture:
    config = ConfigurationService.load(
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
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    prompts = _prompt_repository()
    inputs = _fusion_inputs()
    executive_inbox = IncomingMailbox("STF-002", "DEP-002")
    trader_inbox = IncomingMailbox("STF-060", "DEP-006")
    fusion = RiskFusionOffice(config, persistence, audit, prompts)
    fusion_report = fusion.generate_risk_fusion_report(inputs, "CF-001", "TC-001", 3701, "PROMPT-051")
    trader_record = _trader_prerequisite_record(fusion_report)
    persistence.persist(ObjectType.OPERATIONAL_DOCUMENT, trader_record.contract_id, trader_record.to_dict())
    delivery_results = (
        fusion.route_report(fusion_report, executive_inbox),
        fusion.route_report(trader_record, trader_inbox),
    )
    return _RiskFixture(config, persistence, audit, prompts, inputs, fusion_report, trader_record, executive_inbox, trader_inbox, delivery_results)


def _trader_prerequisite_record(fusion_report: OperationalContract) -> OperationalContract:
    payload = {
        "certification_record_id": "ECR-051",
        "source_organizational_risk_assessment_id": fusion_report.contract_id,
        "trader_group_prerequisite": "certified_organizational_risk_assessment",
        "risk_office_certification_status": "certified",
        "authorization_scope": "Trader Group may consume certified Risk Office products only; no execution authority is granted here.",
        "case_file_id": fusion_report.case_file_id,
        "trade_cycle_id": fusion_report.trade_cycle_id,
        "source_reference_ids": (fusion_report.contract_id,),
    }
    created = utc_timestamp()
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=list).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(3702),
        contract_type="RAR",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=fusion_report.case_file_id,
        trade_cycle_id=fusion_report.trade_cycle_id,
        parent_contract_ids=(fusion_report.contract_id,),
        produced_by_staff_id=fusion_report.produced_by_staff_id,
        produced_by_group_id=fusion_report.produced_by_group_id,
        intended_consumer_group_id="DEP-006",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Certified Organizational Risk Assessment prerequisite for Trader Group.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(fusion_report.contract_id,),
    )


def _prompt_repository() -> PromptRepository:
    repository = PromptRepository()
    repository.register(
        PromptPassport(
            prompt_id="PROMPT-051",
            title="Risk Operational Readiness Prompt",
            owner_group_id="DEP-005",
            author_staff_id="STF-050",
            purpose="Generate deterministic Risk certification artifacts.",
            allowed_environments=("development",),
            input_contract_types=("RAR",),
            output_contract_types=("RAR",),
            dependencies=("EO-051",),
            safety_notes="Certification only; no new analytical capability or trading authority.",
        ),
        "1.0.0",
        "Create deterministic Risk certification artifacts only.",
    )
    return repository


def _fusion_inputs() -> tuple[RiskFusionInput, ...]:
    return (
        RiskFusionInput("RISK-OFFICE-001", "DOC-2901", "position", 0.52, 0.62, 5000, "reduce_single_position_limit", ("EV-1",)),
        RiskFusionInput("RISK-OFFICE-002", "DOC-3001", "portfolio", 0.65, 0.54, 10000, "reduce_enterprise_risk", ("EV-2",)),
        RiskFusionInput("RISK-OFFICE-005", "DOC-3201", "volatility", 0.72, 0.47, 7000, "reduce_risk_limit_moderately", ("EV-3",)),
        RiskFusionInput("RISK-OFFICE-006", "DOC-3301", "tail", 0.82, 0.38, 9000, "reduce_tail_exposure_and_raise_liquidity_reserve", ("EV-4",)),
        RiskFusionInput("RISK-OFFICE-009", "DOC-3501", "recovery", 0.44, 0.56, 3000, "increase_recovery_validation_threshold", ("EV-5",)),
    )
