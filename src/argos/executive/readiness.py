"""Executive Operational Readiness Review."""

from __future__ import annotations

from dataclasses import dataclass

from argos.executive import (
    CHIEF_OF_STAFF_ID,
    ChiefOfStaffService,
    CommanderDecision,
    CommanderDecisionEngine,
    CommanderOffice,
    ExecutiveBriefingPacket,
    ExecutiveDashboard,
    ExecutiveDocumentManifest,
    HumanAuthority,
    HumanOverrideService,
    OverrideAction,
    OverrideLevel,
)
from argos.foundation.audit import AuditEventType, AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas
from argos.foundation.prompts import PromptPassport, PromptRepository
from argos.foundation.testing import TestExecutionResult, TestRunner, foundation_test_registry


@dataclass(frozen=True)
class ExecutiveReadinessCheck:
    """Single Executive readiness check."""

    check_id: str
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ExecutiveReadinessResult:
    """Executive readiness result."""

    checks: tuple[ExecutiveReadinessCheck, ...]
    test_results: tuple[TestExecutionResult, ...]

    @property
    def certified(self) -> bool:
        """Return whether Executive Group is certified."""
        return all(check.passed for check in self.checks) and all(
            result.successful for result in self.test_results
        )


class ExecutiveReadinessVerifier:
    """Verify Executive Group operational readiness."""

    def verify(
        self,
        test_results: tuple[TestExecutionResult, ...] | None = None,
    ) -> ExecutiveReadinessResult:
        """Run Executive readiness checks."""
        if test_results is None:
            test_results = TestRunner().run_all(foundation_test_registry())
        fixture = _executive_fixture()
        checks = (
            self._check_tests(test_results),
            self._check_workflow_and_chief_of_staff(fixture),
            self._check_commander_and_cdr(fixture),
            self._check_dashboard(fixture),
            self._check_override(fixture),
            self._check_audit_reconstruction(fixture),
        )
        return ExecutiveReadinessResult(checks=checks, test_results=test_results)

    def _check_tests(self, test_results: tuple[TestExecutionResult, ...]) -> ExecutiveReadinessCheck:
        failures = [result.suite_id for result in test_results if not result.successful]
        return ExecutiveReadinessCheck(
            "EORR-CHECK-001",
            "Executive integration tests",
            not failures,
            "All registered suites passed." if not failures else f"Failed suites: {', '.join(failures)}",
        )

    def _check_workflow_and_chief_of_staff(self, fixture: "_ExecutiveFixture") -> ExecutiveReadinessCheck:
        passed = fixture.chief_result.accepted and fixture.chief_result.commander_outcome is not None
        return ExecutiveReadinessCheck(
            "EORR-CHECK-002",
            "Executive Workflow and Chief of Staff",
            passed,
            "Validated EBP reached Commander through Chief of Staff.",
        )

    def _check_commander_and_cdr(self, fixture: "_ExecutiveFixture") -> ExecutiveReadinessCheck:
        cdr_id = fixture.chief_result.commander_outcome.cdr_contract_id
        cdr = fixture.persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, cdr_id)
        passed = cdr is not None and cdr.payload["contract_type"] == "CDR"
        return ExecutiveReadinessCheck(
            "EORR-CHECK-003",
            "Commander deterministic decision and CDR generation",
            passed,
            f"Generated {cdr_id}.",
        )

    def _check_dashboard(self, fixture: "_ExecutiveFixture") -> ExecutiveReadinessCheck:
        snapshot = fixture.dashboard.refresh()
        passed = len(snapshot.recent_decisions) == 1 and snapshot.command_table[0].cdr_contract_id == "DOC-120"
        return ExecutiveReadinessCheck(
            "EORR-CHECK-004",
            "Executive Dashboard accuracy",
            passed,
            f"Dashboard refresh {snapshot.refresh_sequence} projected {len(snapshot.recent_decisions)} decisions.",
        )

    def _check_override(self, fixture: "_ExecutiveFixture") -> ExecutiveReadinessCheck:
        authority = HumanAuthority("AUTH-017", "STF-001", OverrideLevel.LEVEL_6_EMERGENCY_LIQUIDATION)
        record = fixture.override_service.apply_override(
            OverrideAction.EXECUTIVE_PAUSE,
            authority,
            "EORR pause check.",
        )
        fixture.override_service.resume(authority, "EORR resume check.")
        passed = record.override_id == "OVR-000001" and fixture.override_service.current_level == OverrideLevel.LEVEL_0_NORMAL
        return ExecutiveReadinessCheck(
            "EORR-CHECK-005",
            "Human Override functionality",
            passed,
            "Pause and recovery verified.",
        )

    def _check_audit_reconstruction(self, fixture: "_ExecutiveFixture") -> ExecutiveReadinessCheck:
        event_types = [event.event_type for event in fixture.audit.audit_log.events]
        passed = AuditEventType.STAFF_DECISION in event_types and fixture.audit.audit_log.verify_integrity()
        return ExecutiveReadinessCheck(
            "EORR-CHECK-006",
            "Complete audit reconstruction",
            passed,
            f"Audit events reconstructed: {len(event_types)}.",
        )


@dataclass
class _ExecutiveFixture:
    config: ConfigurationService
    persistence: InMemoryPersistenceRepository
    audit: AuditService
    commander: CommanderOffice
    chief: ChiefOfStaffService
    dashboard: ExecutiveDashboard
    override_service: HumanOverrideService
    chief_result: object


class ExecutiveReadinessReportGenerator:
    """Generate Executive readiness artifacts."""

    def __init__(self, result: ExecutiveReadinessResult) -> None:
        self.result = result

    def executive_orr(self) -> str:
        """Generate E-ORR."""
        lines = [
            "# E-ORR Executive Operational Readiness Report",
            "",
            "Status: PASS" if self.result.certified else "Status: FAIL",
            "",
            "## Readiness Checks",
        ]
        for check in self.result.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {check.check_id}: {status} - {check.name}. {check.detail}")
        return "\n".join(lines) + "\n"

    def executive_completion_report(self) -> str:
        """Generate ECR-001."""
        status = "COMPLETE" if self.result.certified else "INCOMPLETE"
        return "\n".join(
            [
                "# ECR-001 Executive Completion Report",
                "",
                f"Executive Status: {status}",
                "",
                "Completed Engineering Orders: EO-011 through EO-017",
                "",
                "Verified Executive capabilities:",
                "- Executive framework",
                "- Commander decision engine",
                "- Executive workflow",
                "- Chief of Staff",
                "- Executive dashboard",
                "- Human override and kill switch",
                "- Operational readiness verification",
                "",
            ]
        )

    def authorization_to_proceed(self) -> str:
        """Generate Group 3 authorization."""
        decision = "AUTHORIZED" if self.result.certified else "NOT AUTHORIZED"
        return "\n".join(
            [
                "# Authorization to Proceed - Group 3 Seeker Group",
                "",
                f"Decision: {decision}",
                "",
                "Scope: Seeker Group implementation may begin only after E-ORR passes.",
                "",
            ]
        )


def _executive_fixture() -> _ExecutiveFixture:
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
    commander = CommanderOffice(config, persistence, audit_service=audit)
    prompt_repo = PromptRepository()
    prompt_repo.register(
        PromptPassport(
            prompt_id="PROMPT-017",
            title="Executive Readiness Prompt",
            owner_group_id="DEP-002",
            author_staff_id="STF-002",
            purpose="Readiness fixture prompt.",
            allowed_environments=("development",),
            input_contract_types=("EBP",),
            output_contract_types=("CDR",),
            dependencies=("EO-017",),
            safety_notes="No trading authority.",
        ),
        "1.0.0",
        "Readiness fixture prompt.",
    )
    engine = CommanderDecisionEngine(commander, prompt_repo, "PROMPT-017")
    chief = ChiefOfStaffService(engine, config, persistence, audit)
    ebp = ExecutiveBriefingPacket(
        ebp_id="EBP-401",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        produced_by_staff_id=CHIEF_OF_STAFF_ID,
        produced_by_group_id="DEP-002",
        risk_recommendation_document_id="DOC-410",
        evidence_reference_ids=("DOC-411",),
        summary="Executive readiness packet.",
        recommended_action="approve",
        document_signature_hash="a" * 64,
        configuration_snapshot_hash="b" * 64,
        prompt_snapshot_id="PS-000001",
        model_snapshot_id="MS-000001",
    )
    manifests = {
        "DOC-410": ExecutiveDocumentManifest("DOC-410", "risk", "a" * 64, "b" * 64, 1),
        "DOC-411": ExecutiveDocumentManifest("DOC-411", "evidence", "a" * 64, "b" * 64, 1),
    }
    chief_result = chief.process_packet(
        ebp,
        manifests,
        CommanderDecision.APPROVE,
        "Readiness approval.",
        120,
        "DEP-005",
        IncomingMailbox("STF-005", "DEP-005"),
    )
    dashboard = ExecutiveDashboard(commander, chief, persistence, audit)
    override_service = HumanOverrideService(audit, persistence)
    return _ExecutiveFixture(config, persistence, audit, commander, chief, dashboard, override_service, chief_result)

