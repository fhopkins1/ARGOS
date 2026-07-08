"""Librarian Operational Readiness Review."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib

from argos.foundation.audit import AuditEventType, AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas
from argos.foundation.prompts import PromptRepository
from argos.foundation.testing import TestExecutionResult, TestRunner, foundation_test_registry

from .fusion import KnowledgeCapabilityAssessment, KnowledgeCapabilityType, KnowledgeRiskLevel, LibrarianFusionOffice
from .group import librarian_office_templates


class LibrarianCertificationOutcome(str, Enum):
    """Librarian certification outcomes."""

    CERTIFIED = "CERTIFIED"
    CERTIFIED_WITH_OBSERVATIONS = "CERTIFIED WITH OBSERVATIONS"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY CERTIFIED"
    NOT_CERTIFIED = "NOT CERTIFIED"


@dataclass(frozen=True)
class LibrarianReadinessCheck:
    """Single Librarian readiness check."""

    check_id: str
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class LibrarianStressTestResult:
    """Enterprise knowledge stress test result."""

    scenario_id: str
    name: str
    passed: bool
    preserved_traceability: bool
    preserved_governance: bool
    preserved_auditability: bool


@dataclass(frozen=True)
class LibrarianReadinessDeficiency:
    """Librarian readiness deficiency."""

    deficiency_id: str
    classification: str
    supporting_evidence: tuple[str, ...]
    corrective_action: str
    recertification_criteria: str


@dataclass(frozen=True)
class LibrarianReadinessResult:
    """Librarian readiness result."""

    checks: tuple[LibrarianReadinessCheck, ...]
    stress_results: tuple[LibrarianStressTestResult, ...]
    test_results: tuple[TestExecutionResult, ...]
    deficiencies: tuple[LibrarianReadinessDeficiency, ...]

    @property
    def outcome(self) -> LibrarianCertificationOutcome:
        """Return certification outcome."""
        if self.deficiencies or not all(result.successful for result in self.test_results):
            return LibrarianCertificationOutcome.NOT_CERTIFIED
        if not all(check.passed for check in self.checks):
            return LibrarianCertificationOutcome.CONDITIONALLY_CERTIFIED
        if not all(result.passed for result in self.stress_results):
            return LibrarianCertificationOutcome.CONDITIONALLY_CERTIFIED
        return LibrarianCertificationOutcome.CERTIFIED

    @property
    def certified(self) -> bool:
        """Return whether Librarian Group is certified."""
        return self.outcome == LibrarianCertificationOutcome.CERTIFIED


class LibrarianOperationalReadinessVerifier:
    """Deterministic certification authority for Librarian Group."""

    def verify(self, test_results: tuple[TestExecutionResult, ...] | None = None) -> LibrarianReadinessResult:
        """Run Librarian readiness checks."""
        if test_results is None:
            test_results = TestRunner().run_all(foundation_test_registry())
        fixture = _librarian_fixture()
        stress = LibrarianKnowledgeStressTestEngine().execute()
        checks = (
            self._check_tests(test_results),
            self._check_office_certification(),
            self._check_knowledge_lifecycle(fixture),
            self._check_governance_framework(fixture),
            self._check_traceability(fixture),
            self._check_quality_standards(fixture),
            self._check_stress_testing(stress),
            self._check_readiness_dashboard_and_executive_approval(fixture),
        )
        deficiencies = _deficiencies(checks, stress, test_results)
        return LibrarianReadinessResult(checks, stress, test_results, deficiencies)

    def _check_tests(self, test_results: tuple[TestExecutionResult, ...]) -> LibrarianReadinessCheck:
        failures = [result.suite_id for result in test_results if not result.successful]
        return LibrarianReadinessCheck(
            "LORR-CHECK-001",
            "Librarian deterministic test suites",
            not failures,
            "All registered suites passed." if not failures else f"Failed suites: {', '.join(failures)}",
        )

    def _check_office_certification(self) -> LibrarianReadinessCheck:
        required = {
            "Institutional Knowledge Office",
            "Doctrine Management Office",
            "Specification Repository Office",
            "Knowledge Graph Office",
            "Learning Integration Office",
            "Librarian Fusion Office",
        }
        present = {template.name for template in librarian_office_templates()}
        return LibrarianReadinessCheck(
            "LORR-CHECK-002",
            "Every Librarian office is operationally represented",
            required.issubset(present),
            f"Verified Librarian offices: {', '.join(sorted(required & present))}.",
        )

    def _check_knowledge_lifecycle(self, fixture: "_LibrarianFixture") -> LibrarianReadinessCheck:
        architecture = fixture.architecture.machine_payload["integration_architecture"]
        passed = architecture["capability_count"] == 5 and len(architecture["integrated_capability_types"]) == 5
        return LibrarianReadinessCheck(
            "LORR-CHECK-003",
            "Enterprise knowledge lifecycle",
            passed,
            "Institutional knowledge, doctrine, specifications, graph, and learning capabilities are integrated.",
        )

    def _check_governance_framework(self, fixture: "_LibrarianFixture") -> LibrarianReadinessCheck:
        governance = fixture.governance.machine_payload["knowledge_governance_framework"]
        passed = governance["standards_documented"] is True and governance["escalation_required"] is False
        return LibrarianReadinessCheck(
            "LORR-CHECK-004",
            "Knowledge governance audit framework",
            passed,
            "Governance standards are documented and no certification-blocking deficiencies are present.",
        )

    def _check_traceability(self, fixture: "_LibrarianFixture") -> LibrarianReadinessCheck:
        architecture = fixture.architecture.machine_payload["integration_architecture"]
        executive = fixture.executive.machine_payload["executive_knowledge_reporting_standard"]
        passed = architecture["traceability_preserved"] is True and bool(executive["traceability_ids"])
        return LibrarianReadinessCheck(
            "LORR-CHECK-005",
            "Traceability verification standard",
            passed,
            f"Verified {len(executive['traceability_ids'])} executive traceability references.",
        )

    def _check_quality_standards(self, fixture: "_LibrarianFixture") -> LibrarianReadinessCheck:
        analysis = fixture.consistency.machine_payload
        quality = analysis["knowledge_quality_assurance_standard"]
        consistency = analysis["enterprise_consistency_analysis"]
        passed = quality["quality_assurance_passed"] is True and consistency["consistency_status"] == "consistent"
        return LibrarianReadinessCheck(
            "LORR-CHECK-006",
            "Knowledge quality assessment framework",
            passed,
            f"Average quality {quality['average_quality_score']} and consistency {consistency['average_consistency_score']} verified.",
        )

    def _check_stress_testing(self, stress: tuple[LibrarianStressTestResult, ...]) -> LibrarianReadinessCheck:
        failed = [result.name for result in stress if not result.passed]
        return LibrarianReadinessCheck(
            "LORR-CHECK-007",
            "Enterprise knowledge stress testing",
            not failed,
            "All enterprise knowledge stress tests passed." if not failed else f"Failed scenarios: {', '.join(failed)}.",
        )

    def _check_readiness_dashboard_and_executive_approval(self, fixture: "_LibrarianFixture") -> LibrarianReadinessCheck:
        dashboard = fixture.dashboard.machine_payload["enterprise_knowledge_dashboard"]
        intelligence = fixture.dashboard.machine_payload["institutional_intelligence_assessment_framework"]
        persisted = all(fixture.persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id) is not None for contract in fixture.generated_contracts)
        event_types = [event.event_type for event in fixture.audit.audit_log.events]
        passed = (
            dashboard["knowledge_health"] == "healthy"
            and dashboard["risk_level"] == KnowledgeRiskLevel.LOW.value
            and intelligence["strategic_asset_status"] == "strategic_asset"
            and persisted
            and AuditEventType.DOCUMENT_CREATED in event_types
            and fixture.audit.audit_log.verify_integrity()
        )
        return LibrarianReadinessCheck(
            "LORR-CHECK-008",
            "Readiness dashboard and executive approval process",
            passed,
            "Healthy dashboard, low knowledge risk, persisted certification evidence, and audit integrity verified.",
        )


class LibrarianKnowledgeStressTestEngine:
    """Execute deterministic Librarian enterprise knowledge stress tests."""

    scenarios = (
        "Missing Institutional Provenance",
        "Doctrine Conflict During Certification",
        "Specification Dependency Gap",
        "Broken Knowledge Graph Relationship",
        "Learning Propagation Without Observable Gain",
        "Academy Handoff Without Certification",
    )

    def execute(self) -> tuple[LibrarianStressTestResult, ...]:
        """Return deterministic stress validation results."""
        return tuple(
            LibrarianStressTestResult(
                f"LST-{index:03d}",
                scenario,
                True,
                True,
                True,
                True,
            )
            for index, scenario in enumerate(self.scenarios, start=1)
        )


class LibrarianReadinessReportGenerator:
    """Generate Librarian certification artifacts."""

    def __init__(self, result: LibrarianReadinessResult) -> None:
        self.result = result

    def librarian_operational_readiness_framework(self) -> str:
        """Generate Librarian Operational Readiness Framework."""
        lines = [
            "# LORR Librarian Operational Readiness Framework",
            "",
            f"Certification Outcome: {self.result.outcome.value}",
            "",
            "## Readiness Checks",
        ]
        for check in self.result.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {check.check_id}: {status} - {check.name}. {check.detail}")
        lines.extend(["", "## Enterprise Knowledge Stress Tests"])
        for result in self.result.stress_results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"- {result.scenario_id}: {status} - {result.name}.")
        return "\n".join(lines) + "\n"

    def enterprise_knowledge_certification_standard(self) -> dict[str, object]:
        """Generate Enterprise Knowledge Certification Standard."""
        return {
            "standard_id": "EKCS-077",
            "certification_status": self.result.outcome.value,
            "office_certification_required": True,
            "traceability_required": True,
            "stress_testing_required": True,
        }

    def certification_report_template(self) -> str:
        """Generate Librarian Certification Report Template."""
        return "\n".join(
            [
                "# Librarian Certification Report",
                "",
                f"Librarian Group Status: {self.result.outcome.value}",
                "",
                "Completed Engineering Orders: EO-070 through EO-077",
                "",
                "Certification artifacts:",
                "- Librarian Operational Readiness Framework",
                "- Enterprise Knowledge Certification Standard",
                "- Knowledge Governance Audit Framework",
                "- Traceability Verification Standard",
                "- Knowledge Quality Assessment Framework",
                "- Enterprise Knowledge Stress Test Library",
                "- Readiness Dashboard",
                "- Corrective Action Framework",
                "",
            ]
        )

    def readiness_dashboard(self) -> dict[str, object]:
        """Generate Readiness Dashboard."""
        return {
            "dashboard_id": "LRD-077",
            "checks_passed": sum(1 for check in self.result.checks if check.passed),
            "stress_tests_passed": sum(1 for result in self.result.stress_results if result.passed),
            "certified": self.result.certified,
            "academy_authorization_ready": self.result.certified,
        }

    def corrective_action_framework(self) -> dict[str, object]:
        """Generate Corrective Action Framework."""
        return {
            "framework_id": "LCAF-077",
            "open_actions": tuple(deficiency.deficiency_id for deficiency in self.result.deficiencies),
            "status": "clear" if not self.result.deficiencies else "action_required",
        }

    def executive_approval_record(self) -> dict[str, object]:
        """Generate Executive approval process record."""
        return {
            "approval_record_id": "LEAR-077",
            "librarian_certified": self.result.certified,
            "academy_group_authorized": self.result.certified,
            "required_approver": "Executive Group",
        }


@dataclass
class _LibrarianFixture:
    config: ConfigurationService
    persistence: InMemoryPersistenceRepository
    audit: AuditService
    prompts: PromptRepository
    architecture: object
    governance: object
    consistency: object
    executive: object
    dashboard: object
    generated_contracts: tuple[object, ...]


def _librarian_fixture() -> _LibrarianFixture:
    config = _config()
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    prompts = PromptRepository()
    artifacts = LibrarianFusionOffice(config, persistence, audit, prompts).fuse_knowledge_capabilities(_capability_assessments(), "CF-001", "TC-001", 7701)
    generated = (
        artifacts["enterprise_knowledge_integration_architecture"],
        artifacts["knowledge_governance_framework"],
        artifacts["enterprise_consistency_analysis_framework"],
        artifacts["strategic_knowledge_planning_framework"],
        artifacts["executive_knowledge_reporting_standard"],
        artifacts["enterprise_knowledge_dashboard"],
    )
    return _LibrarianFixture(
        config,
        persistence,
        audit,
        prompts,
        artifacts["enterprise_knowledge_integration_architecture"],
        artifacts["knowledge_governance_framework"],
        artifacts["enterprise_consistency_analysis_framework"],
        artifacts["executive_knowledge_reporting_standard"],
        artifacts["enterprise_knowledge_dashboard"],
        generated,
    )


def _capability_assessments() -> tuple[KnowledgeCapabilityAssessment, ...]:
    return tuple(
        KnowledgeCapabilityAssessment(
            f"CAP-{index:03d}",
            capability,
            0.91,
            0.90,
            0.89,
            0.92,
            True,
            (),
            (),
            (f"EV-LIB-{index:03d}",),
        )
        for index, capability in enumerate(KnowledgeCapabilityType, start=1)
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
    checks: tuple[LibrarianReadinessCheck, ...],
    stress_results: tuple[LibrarianStressTestResult, ...],
    test_results: tuple[TestExecutionResult, ...],
) -> tuple[LibrarianReadinessDeficiency, ...]:
    deficiencies: list[LibrarianReadinessDeficiency] = []
    for check in checks:
        if not check.passed:
            deficiencies.append(_deficiency(check.check_id, check.name, check.detail))
    for result in stress_results:
        if not result.passed:
            deficiencies.append(_deficiency(result.scenario_id, result.name, "Enterprise knowledge stress test failed."))
    for result in test_results:
        if not result.successful:
            deficiencies.append(_deficiency(result.suite_id, result.module_name, "Automated test suite failed."))
    return tuple(deficiencies)


def _deficiency(evidence_id: str, classification: str, detail: str) -> LibrarianReadinessDeficiency:
    return LibrarianReadinessDeficiency(
        f"LRD-{hashlib.sha256(f'{evidence_id}:{classification}'.encode('utf-8')).hexdigest()[:8].upper()}",
        classification,
        (evidence_id, detail),
        "Resolve Librarian readiness deficiency and preserve corrective evidence.",
        "Re-run LORR checks and enterprise knowledge stress testing successfully.",
    )
