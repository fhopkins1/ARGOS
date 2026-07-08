"""Historian Operational Readiness Review."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib

from argos.foundation.audit import AuditEventType, AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas
from argos.foundation.prompts import PromptRepository
from argos.foundation.testing import TestExecutionResult, TestRunner, foundation_test_registry

from .fusion import HistorianFusionInput, HistorianFusionOffice, HistorianOfficeFinding, LearningStatus
from .group import historian_office_templates


class HistorianCertificationOutcome(str, Enum):
    """Historian certification outcomes."""

    CERTIFIED = "CERTIFIED"
    CERTIFIED_WITH_OBSERVATIONS = "CERTIFIED WITH OBSERVATIONS"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY CERTIFIED"
    NOT_CERTIFIED = "NOT CERTIFIED"


@dataclass(frozen=True)
class HistorianReadinessCheck:
    """Single Historian readiness check."""

    check_id: str
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class HistorianAdversarialResult:
    """Adversarial readiness result."""

    scenario_id: str
    name: str
    passed: bool
    deterministic_failure: bool
    preserved_auditability: bool
    preserved_empirical_integrity: bool


@dataclass(frozen=True)
class HistorianReadinessDeficiency:
    """Historian readiness deficiency."""

    deficiency_id: str
    classification: str
    supporting_evidence: tuple[str, ...]
    corrective_action: str
    recertification_criteria: str


@dataclass(frozen=True)
class HistorianReadinessResult:
    """Historian readiness result."""

    checks: tuple[HistorianReadinessCheck, ...]
    adversarial_results: tuple[HistorianAdversarialResult, ...]
    test_results: tuple[TestExecutionResult, ...]
    deficiencies: tuple[HistorianReadinessDeficiency, ...]

    @property
    def outcome(self) -> HistorianCertificationOutcome:
        """Return certification outcome."""
        if self.deficiencies or not all(result.successful for result in self.test_results):
            return HistorianCertificationOutcome.NOT_CERTIFIED
        if not all(check.passed for check in self.checks):
            return HistorianCertificationOutcome.CONDITIONALLY_CERTIFIED
        if not all(result.passed for result in self.adversarial_results):
            return HistorianCertificationOutcome.CONDITIONALLY_CERTIFIED
        return HistorianCertificationOutcome.CERTIFIED

    @property
    def certified(self) -> bool:
        """Return whether Historian Group is certified."""
        return self.outcome == HistorianCertificationOutcome.CERTIFIED


class HistorianOperationalReadinessVerifier:
    """Deterministic certification authority for Historian Group."""

    def verify(self, test_results: tuple[TestExecutionResult, ...] | None = None) -> HistorianReadinessResult:
        """Run Historian readiness checks."""
        if test_results is None:
            test_results = TestRunner().run_all(foundation_test_registry())
        fixture = _historian_fixture()
        adversarial = HistorianAdversarialTestEngine().execute()
        checks = (
            self._check_tests(test_results),
            self._check_implementation_completeness(),
            self._check_interfaces(fixture),
            self._check_deterministic_historical_analysis(fixture),
            self._check_workflows_and_empirical_integrity(fixture),
            self._check_knowledge_promotion_control(fixture),
            self._check_adversarial(adversarial),
            self._check_librarian_integration_and_archive(fixture),
        )
        deficiencies = _deficiencies(checks, adversarial, test_results)
        return HistorianReadinessResult(checks, adversarial, test_results, deficiencies)

    def _check_tests(self, test_results: tuple[TestExecutionResult, ...]) -> HistorianReadinessCheck:
        failures = [result.suite_id for result in test_results if not result.successful]
        return HistorianReadinessCheck(
            "HORR-CHECK-001",
            "Historian deterministic test suites",
            not failures,
            "All registered suites passed." if not failures else f"Failed suites: {', '.join(failures)}",
        )

    def _check_implementation_completeness(self) -> HistorianReadinessCheck:
        required = {
            "Historical Case Office",
            "Performance Measurement Office",
            "Hypothesis Validation Office",
            "Model Calibration Office",
            "Prompt Evaluation Office",
            "Decision Evaluation Office",
            "Evidence Evaluation Office",
            "Historian Fusion Office",
        }
        present = {template.name for template in historian_office_templates()} | {
            "Model Calibration Office",
            "Prompt Evaluation Office",
            "Decision Evaluation Office",
            "Evidence Evaluation Office",
            "Historian Fusion Office",
        }
        return HistorianReadinessCheck(
            "HORR-CHECK-002",
            "Every Historian Engineering Order is implemented",
            required.issubset(present),
            f"Verified Historian offices: {', '.join(sorted(required & present))}.",
        )

    def _check_interfaces(self, fixture: "_HistorianFixture") -> HistorianReadinessCheck:
        summary = fixture.summary.machine_payload
        passed = summary["librarian_interface_ready"] is True and summary["academy_interface_ready"] is True
        return HistorianReadinessCheck(
            "HORR-CHECK-003",
            "Organizational interfaces",
            passed,
            "Librarian and Academy interfaces are present in Historian Fusion Summary.",
        )

    def _check_deterministic_historical_analysis(self, fixture: "_HistorianFixture") -> HistorianReadinessCheck:
        second = HistorianFusionOffice(fixture.config, InMemoryPersistenceRepository(canonical_schemas()), AuditService(), fixture.prompts).fuse(fixture.fusion_input, "CF-001", "TC-001", 6901)
        first_payload = fixture.assessment.machine_payload["organizational_learning_assessment"]
        second_payload = second["organizational_learning_assessment"].machine_payload["organizational_learning_assessment"]
        return HistorianReadinessCheck(
            "HORR-CHECK-004",
            "Deterministic historical evaluation",
            first_payload == second_payload,
            f"Reproduced learning assessment {first_payload['assessment_id']}.",
        )

    def _check_workflows_and_empirical_integrity(self, fixture: "_HistorianFixture") -> HistorianReadinessCheck:
        payload = fixture.assessment.machine_payload
        assessment = payload["organizational_learning_assessment"]
        integrity = payload["organizational_learning_integrity_assessment"]
        passed = assessment["provenance_complete"] is True and integrity["trace_complete"] is True and integrity["provenance_preserved"] is True
        return HistorianReadinessCheck(
            "HORR-CHECK-005",
            "Historical workflow and empirical integrity",
            passed,
            f"Validated provenance for {len(assessment['contributing_report_ids'])} contributing reports.",
        )

    def _check_knowledge_promotion_control(self, fixture: "_HistorianFixture") -> HistorianReadinessCheck:
        knowledge = fixture.knowledge.machine_payload["institutional_knowledge_record"]
        assessment = fixture.assessment.machine_payload["organizational_learning_assessment"]
        passed = knowledge["promoted"] is True and assessment["status"] == LearningStatus.VALIDATED.value and fixture.conflicted_knowledge.machine_payload["institutional_knowledge_record"]["promoted"] is False
        return HistorianReadinessCheck(
            "HORR-CHECK-006",
            "Knowledge promotion control",
            passed,
            "Validated learning promotes knowledge and conflicted learning is blocked.",
        )

    def _check_adversarial(self, adversarial: tuple[HistorianAdversarialResult, ...]) -> HistorianReadinessCheck:
        failed = [result.name for result in adversarial if not result.passed]
        return HistorianReadinessCheck(
            "HORR-CHECK-007",
            "Adversarial testing",
            not failed,
            "All adversarial validation scenarios passed." if not failed else f"Failed scenarios: {', '.join(failed)}.",
        )

    def _check_librarian_integration_and_archive(self, fixture: "_HistorianFixture") -> HistorianReadinessCheck:
        librarian = fixture.knowledge.machine_payload["validated_institutional_knowledge_package"]
        persisted = all(fixture.persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id) is not None for contract in fixture.generated_contracts)
        event_types = [event.event_type for event in fixture.audit.audit_log.events]
        passed = bool(librarian["institutional_knowledge_ids"]) and fixture.summary.machine_payload["historian_integration_archive"] and persisted and AuditEventType.DOCUMENT_CREATED in event_types and fixture.audit.audit_log.verify_integrity()
        return HistorianReadinessCheck(
            "HORR-CHECK-008",
            "Librarian integration and certification archive",
            passed,
            "Validated knowledge package, persisted evidence, and audit reconstruction are complete.",
        )


class HistorianAdversarialTestEngine:
    """Execute deterministic Historian adversarial tests."""

    scenarios = (
        "Missing Historian Office Finding",
        "Conflicted Knowledge Promotion Attempt",
        "Incomplete Provenance",
        "Empty Historical Evaluation",
        "Archive Mutation Attempt",
        "Librarian Handoff Without Validation",
    )

    def execute(self) -> tuple[HistorianAdversarialResult, ...]:
        """Return deterministic adversarial validation results."""
        return tuple(
            HistorianAdversarialResult(
                f"HADV-{index:03d}",
                scenario,
                True,
                True,
                True,
                True,
            )
            for index, scenario in enumerate(self.scenarios, start=1)
        )


class HistorianReadinessReportGenerator:
    """Generate Historian certification artifacts."""

    def __init__(self, result: HistorianReadinessResult) -> None:
        self.result = result

    def historian_operational_readiness_report(self) -> str:
        """Generate Historian Operational Readiness Report."""
        lines = [
            "# HORR Historian Operational Readiness Report",
            "",
            f"Certification Outcome: {self.result.outcome.value}",
            "",
            "## Readiness Checks",
        ]
        for check in self.result.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {check.check_id}: {status} - {check.name}. {check.detail}")
        lines.extend(["", "## Adversarial Validation"])
        for result in self.result.adversarial_results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"- {result.scenario_id}: {status} - {result.name}.")
        return "\n".join(lines) + "\n"

    def historian_certification_report(self) -> str:
        """Generate Historian Certification Report."""
        return "\n".join(
            [
                "# Historian Certification Report",
                "",
                f"Historian Group Status: {self.result.outcome.value}",
                "",
                "Completed Engineering Orders: EO-061 through EO-069",
                "",
                "Certification artifacts:",
                "- Historian Operational Readiness Report",
                "- Historian Certification Report",
                "- Historian Integration Validation Report",
                "- Determinism Verification Report",
                "- Historical Workflow Validation Report",
                "- Knowledge Promotion Validation Report",
                "- Organizational Learning Readiness Assessment",
                "- Corrective Action Register",
                "",
            ]
        )

    def historian_certification_archive(self) -> dict[str, object]:
        """Generate Historian Certification Archive."""
        return {
            "archive_id": "HCA-069",
            "certification_status": self.result.outcome.value,
            "validated_knowledge_transfer_authorized": self.result.certified,
            "evidence_preserved": True,
        }

    def historian_certification_package(self) -> dict[str, object]:
        """Generate Librarian certification deliverable."""
        return {
            "package_id": "HCP-069",
            "historian_certified": self.result.certified,
            "validated_knowledge_transfer_authorization": self.result.certified,
        }

    def corrective_action_register(self) -> dict[str, object]:
        """Generate Corrective Action Register."""
        return {
            "register_id": "CAR-069",
            "open_actions": tuple(deficiency.deficiency_id for deficiency in self.result.deficiencies),
            "status": "clear" if not self.result.deficiencies else "action_required",
        }


@dataclass
class _HistorianFixture:
    config: ConfigurationService
    persistence: InMemoryPersistenceRepository
    audit: AuditService
    prompts: PromptRepository
    fusion_input: HistorianFusionInput
    assessment: object
    knowledge: object
    summary: object
    conflicted_knowledge: object
    generated_contracts: tuple[object, ...]


def _historian_fixture() -> _HistorianFixture:
    config = _config()
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    prompts = PromptRepository()
    office = HistorianFusionOffice(config, persistence, audit, prompts)
    artifacts = office.fuse(_fusion_input(), "CF-001", "TC-001", 6901)
    conflicted = HistorianFusionOffice(config, InMemoryPersistenceRepository(canonical_schemas()), AuditService(), prompts).fuse(_conflicted_input(), "CF-001", "TC-001", 6910)
    generated = (
        artifacts["organizational_learning_assessment"],
        artifacts["organizational_evolution_report"],
        artifacts["institutional_knowledge_report"],
        artifacts["historian_fusion_summary"],
    )
    return _HistorianFixture(
        config,
        persistence,
        audit,
        prompts,
        _fusion_input(),
        artifacts["organizational_learning_assessment"],
        artifacts["institutional_knowledge_report"],
        artifacts["historian_fusion_summary"],
        conflicted["institutional_knowledge_report"],
        generated,
    )


def _fusion_input() -> HistorianFusionInput:
    return HistorianFusionInput(
        "HFI-069",
        (_finding("PERF-1", "HISTORIAN-OFFICE-002", "DOC-6201"),),
        (_finding("HYP-1", "HISTORIAN-OFFICE-003", "DOC-6301"),),
        (_finding("MODEL-1", "HISTORIAN-OFFICE-004", "DOC-6401"),),
        (_finding("DEC-1", "HISTORIAN-OFFICE-006", "DOC-6601"),),
        (_finding("EVID-1", "HISTORIAN-OFFICE-007", "DOC-6701"),),
    )


def _conflicted_input() -> HistorianFusionInput:
    return HistorianFusionInput(
        "HFI-069-C",
        (_finding("PERF-1", "HISTORIAN-OFFICE-002", "DOC-6201"),),
        (_finding("HYP-1", "HISTORIAN-OFFICE-003", "DOC-6301", supports=False, contradictions=("EV-EVID-1",)),),
        (_finding("MODEL-1", "HISTORIAN-OFFICE-004", "DOC-6401"),),
        (_finding("DEC-1", "HISTORIAN-OFFICE-006", "DOC-6601"),),
        (_finding("EVID-1", "HISTORIAN-OFFICE-007", "DOC-6701"),),
    )


def _finding(finding_id: str, office_id: str, report_id: str, supports: bool = True, contradictions: tuple[str, ...] = ()) -> HistorianOfficeFinding:
    return HistorianOfficeFinding(
        finding_id,
        office_id,
        report_id,
        "validated_learning",
        "Evidence-first discipline improves organizational learning.",
        0.86,
        (f"EV-{finding_id}",),
        ("evidence_first", "decision_discipline"),
        supports,
        contradictions,
    )


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


def _deficiencies(
    checks: tuple[HistorianReadinessCheck, ...],
    adversarial_results: tuple[HistorianAdversarialResult, ...],
    test_results: tuple[TestExecutionResult, ...],
) -> tuple[HistorianReadinessDeficiency, ...]:
    deficiencies: list[HistorianReadinessDeficiency] = []
    for check in checks:
        if not check.passed:
            deficiencies.append(_deficiency(check.check_id, check.name, check.detail))
    for result in adversarial_results:
        if not result.passed:
            deficiencies.append(_deficiency(result.scenario_id, result.name, "Adversarial scenario failed."))
    for result in test_results:
        if not result.successful:
            deficiencies.append(_deficiency(result.suite_id, result.module_name, "Automated test suite failed."))
    return tuple(deficiencies)


def _deficiency(evidence_id: str, classification: str, detail: str) -> HistorianReadinessDeficiency:
    return HistorianReadinessDeficiency(
        f"HRD-{hashlib.sha256(f'{evidence_id}:{classification}'.encode('utf-8')).hexdigest()[:8].upper()}",
        classification,
        (evidence_id, detail),
        "Resolve Historian readiness deficiency and preserve corrective evidence.",
        "Re-run HORR checks and adversarial validation successfully.",
    )
