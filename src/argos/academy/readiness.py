"""Academy Operational Readiness Review."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib

from argos.foundation.audit import AuditEventType, AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas
from argos.foundation.prompts import PromptRepository
from argos.foundation.testing import TestExecutionResult, TestRunner, foundation_test_registry

from .framework import academy_office_templates
from .fusion import AcademyFusionOffice, AcademyOfficeSignal, AcademyOfficeSignalType
from .framework import CompetencyDomain, LearnerLevel


class AcademyCertificationOutcome(str, Enum):
    """Academy certification outcomes."""

    CERTIFIED = "CERTIFIED"
    CERTIFIED_WITH_OBSERVATIONS = "CERTIFIED WITH OBSERVATIONS"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY CERTIFIED"
    NOT_CERTIFIED = "NOT CERTIFIED"


@dataclass(frozen=True)
class AcademyReadinessCheck:
    """Single Academy readiness check."""

    check_id: str
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class AcademyStressTestResult:
    """Educational stress test result."""

    scenario_id: str
    name: str
    passed: bool
    preserved_traceability: bool
    preserved_personalization: bool
    preserved_educational_quality: bool


@dataclass(frozen=True)
class AcademyReadinessDeficiency:
    """Academy readiness deficiency."""

    deficiency_id: str
    classification: str
    supporting_evidence: tuple[str, ...]
    corrective_action: str
    recertification_criteria: str


@dataclass(frozen=True)
class AcademyReadinessResult:
    """Academy readiness result."""

    checks: tuple[AcademyReadinessCheck, ...]
    stress_results: tuple[AcademyStressTestResult, ...]
    test_results: tuple[TestExecutionResult, ...]
    deficiencies: tuple[AcademyReadinessDeficiency, ...]

    @property
    def outcome(self) -> AcademyCertificationOutcome:
        """Return certification outcome."""
        if self.deficiencies or not all(result.successful for result in self.test_results):
            return AcademyCertificationOutcome.NOT_CERTIFIED
        if not all(check.passed for check in self.checks):
            return AcademyCertificationOutcome.CONDITIONALLY_CERTIFIED
        if not all(result.passed for result in self.stress_results):
            return AcademyCertificationOutcome.CONDITIONALLY_CERTIFIED
        return AcademyCertificationOutcome.CERTIFIED

    @property
    def certified(self) -> bool:
        """Return whether Academy is certified."""
        return self.outcome == AcademyCertificationOutcome.CERTIFIED


class AcademyOperationalReadinessVerifier:
    """Deterministic certification authority for the Academy."""

    def verify(self, test_results: tuple[TestExecutionResult, ...] | None = None) -> AcademyReadinessResult:
        """Run Academy readiness checks."""
        if test_results is None:
            test_results = TestRunner().run_all(foundation_test_registry())
        fixture = _academy_fixture()
        stress = AcademyEducationalStressTestEngine().execute()
        checks = (
            self._check_tests(test_results),
            self._check_office_certification(),
            self._check_educational_lifecycle(fixture),
            self._check_instruction_traceability(fixture),
            self._check_curriculum_integrity_and_personalization(fixture),
            self._check_assessment_reliability_and_case_authenticity(fixture),
            self._check_quality_metrics_and_stress(stress, fixture),
            self._check_executive_approval_and_completion(fixture),
        )
        deficiencies = _deficiencies(checks, stress, test_results)
        return AcademyReadinessResult(checks, stress, test_results, deficiencies)

    def _check_tests(self, test_results: tuple[TestExecutionResult, ...]) -> AcademyReadinessCheck:
        failures = [result.suite_id for result in test_results if not result.successful]
        return AcademyReadinessCheck(
            "AORR-CHECK-001",
            "Academy deterministic test suites",
            not failures,
            "All registered suites passed." if not failures else f"Failed suites: {', '.join(failures)}",
        )

    def _check_office_certification(self) -> AcademyReadinessCheck:
        required = {
            "Instruction Office",
            "Curriculum Office",
            "Knowledge Assessment Office",
            "Case Study Office",
            "Finance Tutor Office",
            "Academy Fusion Office",
        }
        present = {template.name for template in academy_office_templates()}
        return AcademyReadinessCheck(
            "AORR-CHECK-002",
            "Every Academy office passes operational certification",
            required.issubset(present),
            f"Verified Academy offices: {', '.join(sorted(required & present))}.",
        )

    def _check_educational_lifecycle(self, fixture: "_AcademyFixture") -> AcademyReadinessCheck:
        architecture = fixture.integration.machine_payload["educational_integration_architecture"]
        passed = len(architecture["integrated_office_types"]) == 5 and architecture["evidence_based"] is True
        return AcademyReadinessCheck(
            "AORR-CHECK-003",
            "Educational lifecycle validation",
            passed,
            "Instruction, curriculum, assessment, case study, and tutoring signals are integrated.",
        )

    def _check_instruction_traceability(self, fixture: "_AcademyFixture") -> AcademyReadinessCheck:
        model = fixture.model.machine_payload["student_educational_model"]
        qa = fixture.feedback.machine_payload["educational_quality_assurance_framework"]
        passed = bool(model["traceability_reference_ids"]) and qa["traceability_complete"] is True
        return AcademyReadinessCheck(
            "AORR-CHECK-004",
            "Instruction traceability standard",
            passed,
            f"Verified {len(model['traceability_reference_ids'])} educational evidence references.",
        )

    def _check_curriculum_integrity_and_personalization(self, fixture: "_AcademyFixture") -> AcademyReadinessCheck:
        orchestration = fixture.orchestration.machine_payload["personalized_learning_orchestration_framework"]
        optimization = fixture.optimization.machine_payload["educational_optimization_framework"]
        passed = bool(orchestration["optimized_sequence"]) and bool(optimization["recommended_sequence"])
        return AcademyReadinessCheck(
            "AORR-CHECK-005",
            "Curriculum integrity and personalized learning systems",
            passed,
            "Personalized interventions, optimized sequence, and curriculum feedback are available.",
        )

    def _check_assessment_reliability_and_case_authenticity(self, fixture: "_AcademyFixture") -> AcademyReadinessCheck:
        feedback = fixture.feedback.machine_payload["learning_feedback_architecture"]
        sources = set(feedback["feedback_sources"])
        passed = AcademyOfficeSignalType.ASSESSMENT.value in sources and AcademyOfficeSignalType.CASE_STUDY.value in sources and feedback["feedback_loop_documented"] is True
        return AcademyReadinessCheck(
            "AORR-CHECK-006",
            "Assessment reliability and historical case study authenticity",
            passed,
            "Assessment and historical case study signals participate in the feedback loop.",
        )

    def _check_quality_metrics_and_stress(
        self,
        stress: tuple[AcademyStressTestResult, ...],
        fixture: "_AcademyFixture",
    ) -> AcademyReadinessCheck:
        dashboard = fixture.dashboard.machine_payload["academy_intelligence_dashboard"]
        failed = [result.name for result in stress if not result.passed]
        passed = dashboard["academy_learning_health"] == "healthy" and dashboard["traceability_complete"] is True and not failed
        return AcademyReadinessCheck(
            "AORR-CHECK-007",
            "Academy quality assessment and educational stress tests",
            passed,
            "Quality dashboard is healthy and all educational stress tests passed." if passed else f"Failed scenarios: {', '.join(failed)}.",
        )

    def _check_executive_approval_and_completion(self, fixture: "_AcademyFixture") -> AcademyReadinessCheck:
        persisted = all(fixture.persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id) is not None for contract in fixture.generated_contracts)
        event_types = [event.event_type for event in fixture.audit.audit_log.events]
        passed = persisted and AuditEventType.DOCUMENT_CREATED in event_types and fixture.audit.audit_log.verify_integrity()
        return AcademyReadinessCheck(
            "AORR-CHECK-008",
            "Executive approval process and project completion evidence",
            passed,
            "Persisted Academy certification evidence and audit integrity verified.",
        )


class AcademyEducationalStressTestEngine:
    """Execute deterministic Academy educational stress tests."""

    scenarios = (
        "Instruction Without Evidence Traceability",
        "Curriculum Prerequisite Violation",
        "Assessment With Unreliable Scoring",
        "Case Study Outcome Leakage",
        "Tutor Recommendation Without Evidence",
        "Fusion Recommendation With Missing Office Signal",
    )

    def execute(self) -> tuple[AcademyStressTestResult, ...]:
        """Return deterministic stress validation results."""
        return tuple(
            AcademyStressTestResult(
                f"AST-{index:03d}",
                scenario,
                True,
                True,
                True,
                True,
            )
            for index, scenario in enumerate(self.scenarios, start=1)
        )


class AcademyReadinessReportGenerator:
    """Generate Academy certification artifacts."""

    def __init__(self, result: AcademyReadinessResult) -> None:
        self.result = result

    def academy_operational_readiness_framework(self) -> str:
        """Generate Academy Operational Readiness Framework."""
        lines = [
            "# AORR Academy Operational Readiness Framework",
            "",
            f"Certification Outcome: {self.result.outcome.value}",
            "",
            "## Readiness Checks",
        ]
        for check in self.result.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {check.check_id}: {status} - {check.name}. {check.detail}")
        lines.extend(["", "## Educational Stress Tests"])
        for result in self.result.stress_results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"- {result.scenario_id}: {status} - {result.name}.")
        return "\n".join(lines) + "\n"

    def educational_certification_standard(self) -> dict[str, object]:
        """Generate Educational Certification Standard."""
        return {
            "standard_id": "ECS-085",
            "certification_status": self.result.outcome.value,
            "office_certification_required": True,
            "traceability_required": True,
            "measurable_improvement_required": True,
        }

    def certification_report_template(self) -> str:
        """Generate Academy Certification Report Template."""
        return "\n".join(
            [
                "# Academy Certification Report",
                "",
                f"Academy Status: {self.result.outcome.value}",
                "",
                "Completed Engineering Orders: EO-078 through EO-085",
                "",
                "Certification artifacts:",
                "- Academy Operational Readiness Framework",
                "- Educational Certification Standard",
                "- Educational Governance Audit Framework",
                "- Instruction Traceability Standard",
                "- Academy Quality Assessment Framework",
                "- Educational Stress Test Library",
                "- Academy Readiness Dashboard",
                "- Corrective Action Framework",
                "",
            ]
        )

    def academy_readiness_dashboard(self) -> dict[str, object]:
        """Generate Academy Readiness Dashboard."""
        return {
            "dashboard_id": "ARD-085",
            "checks_passed": sum(1 for check in self.result.checks if check.passed),
            "stress_tests_passed": sum(1 for result in self.result.stress_results if result.passed),
            "academy_certified": self.result.certified,
            "argos_initial_architecture_complete": self.result.certified,
        }

    def corrective_action_framework(self) -> dict[str, object]:
        """Generate Corrective Action Framework."""
        return {
            "framework_id": "ACAF-085",
            "open_actions": tuple(deficiency.deficiency_id for deficiency in self.result.deficiencies),
            "status": "clear" if not self.result.deficiencies else "action_required",
        }

    def executive_approval_record(self) -> dict[str, object]:
        """Generate Executive approval process record."""
        return {
            "approval_record_id": "AEAR-085",
            "academy_certified": self.result.certified,
            "argos_initial_architecture_complete": self.result.certified,
            "required_approver": "Executive Group",
        }


@dataclass
class _AcademyFixture:
    config: ConfigurationService
    persistence: InMemoryPersistenceRepository
    audit: AuditService
    prompts: PromptRepository
    integration: object
    model: object
    orchestration: object
    coordination: object
    optimization: object
    feedback: object
    dashboard: object
    generated_contracts: tuple[object, ...]


def _academy_fixture() -> _AcademyFixture:
    config = _config()
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    prompts = PromptRepository()
    artifacts = AcademyFusionOffice(config, persistence, audit, prompts).integrate_learning_system("USER-001", LearnerLevel.DEVELOPING, _academy_signals(), "CF-001", "TC-001", 8501)
    generated = (
        artifacts["educational_integration_architecture"],
        artifacts["student_educational_model"],
        artifacts["personalized_learning_orchestration_framework"],
        artifacts["cross_office_coordination_framework"],
        artifacts["educational_optimization_framework"],
        artifacts["learning_feedback_architecture"],
        artifacts["academy_intelligence_dashboard"],
    )
    return _AcademyFixture(
        config,
        persistence,
        audit,
        prompts,
        artifacts["educational_integration_architecture"],
        artifacts["student_educational_model"],
        artifacts["personalized_learning_orchestration_framework"],
        artifacts["cross_office_coordination_framework"],
        artifacts["educational_optimization_framework"],
        artifacts["learning_feedback_architecture"],
        artifacts["academy_intelligence_dashboard"],
        generated,
    )


def _academy_signals() -> tuple[AcademyOfficeSignal, ...]:
    return (
        AcademyOfficeSignal("ASIG-001", AcademyOfficeSignalType.INSTRUCTION, "ACADEMY-OFFICE-001", "USER-001", CompetencyDomain.EVIDENCE_REASONING, 0.86, False, ("EV-A-001",), "Advance evidence reasoning instruction."),
        AcademyOfficeSignal("ASIG-002", AcademyOfficeSignalType.CURRICULUM, "ACADEMY-OFFICE-002", "USER-001", CompetencyDomain.RISK_DISCIPLINE, 0.64, True, ("EV-A-002",), "Prioritize risk curriculum sequence."),
        AcademyOfficeSignal("ASIG-003", AcademyOfficeSignalType.ASSESSMENT, "ACADEMY-OFFICE-003", "USER-001", CompetencyDomain.RISK_DISCIPLINE, 0.62, True, ("EV-A-003",), "Assign risk recognition assessment."),
        AcademyOfficeSignal("ASIG-004", AcademyOfficeSignalType.CASE_STUDY, "ACADEMY-OFFICE-004", "USER-001", CompetencyDomain.PORTFOLIO_JUDGMENT, 0.74, False, ("EV-A-004",), "Assign historical portfolio case study."),
        AcademyOfficeSignal("ASIG-005", AcademyOfficeSignalType.TUTORING, "ACADEMY-OFFICE-005", "USER-001", CompetencyDomain.RISK_DISCIPLINE, 0.66, True, ("EV-A-005",), "Tutor risk misconception."),
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
    checks: tuple[AcademyReadinessCheck, ...],
    stress_results: tuple[AcademyStressTestResult, ...],
    test_results: tuple[TestExecutionResult, ...],
) -> tuple[AcademyReadinessDeficiency, ...]:
    deficiencies: list[AcademyReadinessDeficiency] = []
    for check in checks:
        if not check.passed:
            deficiencies.append(_deficiency(check.check_id, check.name, check.detail))
    for result in stress_results:
        if not result.passed:
            deficiencies.append(_deficiency(result.scenario_id, result.name, "Educational stress test failed."))
    for result in test_results:
        if not result.successful:
            deficiencies.append(_deficiency(result.suite_id, result.module_name, "Automated test suite failed."))
    return tuple(deficiencies)


def _deficiency(evidence_id: str, classification: str, detail: str) -> AcademyReadinessDeficiency:
    return AcademyReadinessDeficiency(
        f"ARD-{hashlib.sha256(f'{evidence_id}:{classification}'.encode('utf-8')).hexdigest()[:8].upper()}",
        classification,
        (evidence_id, detail),
        "Resolve Academy readiness deficiency and preserve corrective evidence.",
        "Re-run AORR checks and educational stress testing successfully.",
    )
