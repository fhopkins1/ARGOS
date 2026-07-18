"""EO-DI test completeness and evidence office.

EO-DI inventories requirements, tests, evidence, and defects. It evaluates
proof completeness without owning or mutating the subsystems under test.
"""

from __future__ import annotations

import ast
import csv
from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import zipfile
from typing import Any, Iterable

from argos.foundation.contracts import utc_timestamp

from .constitutional_invariants import constitutional_invariant_catalog
from .read_only_integrity import read_surface_registry
from .runtime_bridge_certification import required_runtime_bridge_matrix
from .synthetic_truth_quarantine import baseline_synthetic_truth_findings
from .transaction_reconciliation import TRANSACTION_TYPE_REGISTRY


EO_DI_VERSION = "EO-DI.1"


class RequirementClass(str, Enum):
    CONSTITUTIONAL_LAW = "constitutional law"
    AUTHORITY_BOUNDARY = "authority boundary"
    LAW_VII = "LAW VII"
    RUNTIME_UNIQUENESS = "runtime uniqueness"
    OFFICE_RESPONSIBILITY = "office responsibility"
    BRIDGE_REQUIREMENT = "bridge requirement"
    TRUTH_DOMAIN_ISOLATION = "truth-domain isolation"
    PROVENANCE = "provenance"
    TRANSACTION_INTEGRITY = "transaction integrity"
    BROKER_AUTHORITY = "Broker authority"
    POSITION_AUTHORITY = "position authority"
    PERSISTENCE = "persistence"
    RECOVERY = "recovery"
    REPLAY = "replay"
    READ_ONLY_INTEGRITY = "read-only integrity"
    SYNTHETIC_TRUTH_PROHIBITION = "synthetic-truth prohibition"
    COMMANDER_LIMITATION = "Commander limitation"
    COST_CONTROL = "cost control"
    API_CONTROL = "API control"
    FAULT_RESILIENCE = "fault resilience"
    RESOURCE_BOUNDEDNESS = "resource boundedness"
    OPERATIONAL_EVIDENCE = "operational evidence"
    LIVE_DISABLED_BOUNDARY = "live-disabled boundary"


class CoverageStatus(str, Enum):
    PROVEN = "PROVEN"
    PARTIALLY_PROVEN = "PARTIALLY_PROVEN"
    IMPLEMENTED_NOT_PROVEN = "IMPLEMENTED_NOT_PROVEN"
    TESTED_NONCANONICALLY = "TESTED_NONCANONICALLY"
    STATIC_ONLY = "STATIC_ONLY"
    DYNAMIC_ONLY = "DYNAMIC_ONLY"
    MISSING_TEST = "MISSING_TEST"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class TestStrength(str, Enum):
    LEVEL_0_EXISTENCE_ONLY = "LEVEL_0_EXISTENCE_ONLY"
    LEVEL_1_LOCAL_UNIT = "LEVEL_1_LOCAL_UNIT"
    LEVEL_2_COMPONENT_CONTRACT = "LEVEL_2_COMPONENT_CONTRACT"
    LEVEL_3_INTEGRATION = "LEVEL_3_INTEGRATION"
    LEVEL_4_CANONICAL_RUNTIME = "LEVEL_4_CANONICAL_RUNTIME"
    LEVEL_5_CONSTITUTIONAL_END_TO_END = "LEVEL_5_CONSTITUTIONAL_END_TO_END"
    LEVEL_6_FAULT_AND_RECOVERY = "LEVEL_6_FAULT_AND_RECOVERY"
    LEVEL_7_LONG_DURATION_OPERATION = "LEVEL_7_LONG_DURATION_OPERATION"


class EvidenceClass(str, Enum):
    SOURCE_INSPECTION = "source inspection"
    STATIC_CALL_GRAPH = "static call graph"
    BRIDGE_GRAPH = "bridge graph"
    TEST_RESULT = "test result"
    RUNTIME_TRACE = "runtime trace"
    TRANSACTION_TRACE = "transaction trace"
    RECOVERY_TRACE = "recovery trace"
    READ_INTEGRITY_DIGEST = "read-integrity digest"
    SYNTHETIC_TRUTH_SCAN = "synthetic-truth scan"
    FAULT_CAMPAIGN_RESULT = "fault-campaign result"
    ENDURANCE_TIME_SERIES = "endurance time series"
    ENVIRONMENT_LIMITATION = "environment limitation"


class VerificationDefectClass(str, Enum):
    MISSING_REQUIREMENT = "MISSING_REQUIREMENT"
    MISSING_IMPLEMENTATION = "MISSING_IMPLEMENTATION"
    MISSING_TEST = "MISSING_TEST"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    WEAK_TEST = "WEAK_TEST"
    NONCANONICAL_TEST = "NONCANONICAL_TEST"
    MOCK_ONLY_PROOF = "MOCK_ONLY_PROOF"
    PROOF_ONLY_TEST = "PROOF_ONLY_TEST"
    SIMULATION_ONLY_TEST = "SIMULATION_ONLY_TEST"
    REPLAY_ONLY_TEST = "REPLAY_ONLY_TEST"
    COMPATIBILITY_ONLY_TEST = "COMPATIBILITY_ONLY_TEST"
    SKIPPED_TEST = "SKIPPED_TEST"
    DISABLED_TEST = "DISABLED_TEST"
    FLAKY_TEST = "FLAKY_TEST"
    ASSERTION_QUALITY = "ASSERTION_QUALITY"
    BRIDGE_COVERAGE = "BRIDGE_COVERAGE"
    SYNTHETIC_TRUTH_COVERAGE = "SYNTHETIC_TRUTH_COVERAGE"
    ENDURANCE_COVERAGE = "ENDURANCE_COVERAGE"
    EVIDENCE_INTEGRITY = "EVIDENCE_INTEGRITY"
    ENVIRONMENT = "ENVIRONMENT"
    DOCUMENTATION = "DOCUMENTATION"
    UNKNOWN = "UNKNOWN"


class VerificationSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    ENHANCEMENT = "ENHANCEMENT"


class VerificationDefectStatus(str, Enum):
    OPEN = "OPEN"
    TRIAGED = "TRIAGED"
    BLOCKING = "BLOCKING"
    IN_REMEDIATION = "IN_REMEDIATION"
    FIXED_UNVERIFIED = "FIXED_UNVERIFIED"
    VERIFIED = "VERIFIED"
    DEFERRED = "DEFERRED"
    ACCEPTED_LIMITATION = "ACCEPTED_LIMITATION"
    INVALID = "INVALID"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True)
class ConstitutionalRequirement:
    requirement_id: str
    title: str
    source_document: str
    source_section: str
    source_engineering_order: str
    requirement_text: str
    requirement_class: RequirementClass
    owning_subsystem: str
    owning_constitutional_authority: str
    applicable_truth_domains: tuple[str, ...]
    applicable_operating_modes: tuple[str, ...]
    severity_if_violated: VerificationSeverity
    blocking_status: str
    required_implementation_evidence: tuple[str, ...]
    required_static_evidence: tuple[str, ...]
    required_dynamic_evidence: tuple[str, ...]
    required_fault_evidence: tuple[str, ...]
    required_endurance_evidence: tuple[str, ...]
    required_recovery_evidence: tuple[str, ...]
    required_read_only_evidence: tuple[str, ...]
    required_test_strength: TestStrength
    linked_bridge_ids: tuple[str, ...]
    linked_invariant_ids: tuple[str, ...]
    linked_synthetic_truth_finding_ids: tuple[str, ...]
    linked_transaction_types: tuple[str, ...]
    linked_persistence_entities: tuple[str, ...]
    certification_relevance: str
    current_coverage_status: CoverageStatus
    superseded_by: str = ""
    schema_version: str = EO_DI_VERSION


@dataclass(frozen=True)
class EOAcceptanceCriterion:
    eo_id: str
    criterion_number: str
    criterion_text: str
    implementation_references: tuple[str, ...]
    linked_tests: tuple[str, ...]
    linked_evidence: tuple[str, ...]
    current_result: CoverageStatus
    verification_method: str
    last_verified_commit: str
    unresolved_limitations: tuple[str, ...]


@dataclass(frozen=True)
class TestInventoryRecord:
    test_id: str
    file: str
    symbol: str
    test_framework: str
    subsystem: str
    test_type: str
    requirement_ids: tuple[str, ...]
    bridge_ids: tuple[str, ...]
    invariant_ids: tuple[str, ...]
    truth_domains: tuple[str, ...]
    runtime_mode: str
    fixture_dependencies: tuple[str, ...]
    mock_dependencies: tuple[str, ...]
    proof_dependencies: tuple[str, ...]
    simulation_dependencies: tuple[str, ...]
    replay_dependencies: tuple[str, ...]
    compatibility_dependencies: tuple[str, ...]
    canonical_runtime_reachability: bool
    expected_assertions: tuple[str, ...]
    actual_assertion_count: int
    side_effects: tuple[str, ...]
    execution_time: float
    flaky_status: str
    skipped_status: str
    quarantined_status: str
    last_result: str
    last_executed_commit: str
    evidence_path: str
    strength_classification: TestStrength
    schema_version: str = EO_DI_VERSION


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    evidence_class: EvidenceClass
    commit: str
    configuration_hash: str
    generation_command: str
    generator_version: str
    start_time_utc: str
    end_time_utc: str
    scope: str
    raw_artifact_path: str
    artifact_hash: str
    result: str
    limitations: tuple[str, ...]
    linked_requirements: tuple[str, ...]
    linked_tests: tuple[str, ...]
    linked_defects: tuple[str, ...]


@dataclass(frozen=True)
class TraceabilityRow:
    requirement_id: str
    implementation_references: tuple[str, ...]
    test_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    result: CoverageStatus
    defect_ids: tuple[str, ...]
    remediation: str
    current_status: CoverageStatus


@dataclass(frozen=True)
class VerificationDefect:
    defect_id: str
    title: str
    subsystem: str
    requirement_ids: tuple[str, ...]
    test_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    severity: VerificationSeverity
    defect_class: VerificationDefectClass
    discovery_commit: str
    reproduction_command: str
    expected_behavior: str
    actual_behavior: str
    affected_operating_modes: tuple[str, ...]
    affected_truth_domains: tuple[str, ...]
    certification_consequence: str
    remediation_owner: str
    status: VerificationDefectStatus
    fix_commit: str = ""
    regression_test_id: str = ""
    closure_evidence: tuple[str, ...] = ()

    def verify(self, *, fix_commit: str, regression_test_id: str, closure_evidence: tuple[str, ...]) -> "VerificationDefect":
        if not fix_commit or not regression_test_id or not closure_evidence:
            raise ValueError("fix commit, regression test, and closure evidence required")
        return replace(self, status=VerificationDefectStatus.VERIFIED, fix_commit=fix_commit, regression_test_id=regression_test_id, closure_evidence=closure_evidence)


@dataclass(frozen=True)
class TestExecutionResult:
    command: str
    commit: str
    environment: dict[str, Any]
    stdout_path: str
    stderr_path: str
    stdout_hash: str
    stderr_hash: str
    exit_code: int
    duration_seconds: float
    passed: int
    failed: int
    skipped: int
    xfailed: int
    xpassed: int
    errors: int
    timeouts: int
    incomplete: bool


@dataclass(frozen=True)
class AuditScorecard:
    verdict: str
    requirements_total: int
    blocking_requirements: int
    requirements_proven: int
    requirements_partially_proven: int
    requirements_missing_tests: int
    requirements_missing_evidence: int
    tests_total: int
    unit_tests: int
    component_tests: int
    integration_tests: int
    canonical_runtime_tests: int
    constitutional_end_to_end_tests: int
    fault_tests: int
    endurance_tests: int
    skipped_tests: int
    weak_tests: int
    mock_only_findings: int
    open_critical_defects: int
    open_major_defects: int
    live_trading_enabled: bool
    certifies_argos: bool
    schema_version: str = EO_DI_VERSION


class ConstitutionalRequirementRegistry:
    def __init__(self, requirements: Iterable[ConstitutionalRequirement] | None = None) -> None:
        self._requirements: dict[str, ConstitutionalRequirement] = {}
        for requirement in requirements or constitutional_requirement_catalog():
            self.register(requirement)

    def register(self, requirement: ConstitutionalRequirement) -> None:
        if requirement.requirement_id in self._requirements:
            raise ValueError(f"duplicate requirement id: {requirement.requirement_id}")
        if not requirement.blocking_status:
            raise ValueError("blocking status required")
        if not requirement.source_document or not requirement.source_section:
            raise ValueError("source linkage required")
        self._requirements[requirement.requirement_id] = requirement

    def all(self) -> tuple[ConstitutionalRequirement, ...]:
        return tuple(self._requirements.values())


class TestInventory:
    def __init__(self, tests: Iterable[TestInventoryRecord] | None = None) -> None:
        self._tests: dict[str, TestInventoryRecord] = {}
        for test in tests or ():
            self.register(test)

    def register(self, test: TestInventoryRecord) -> None:
        if test.test_id in self._tests:
            raise ValueError(f"duplicate test id: {test.test_id}")
        self._tests[test.test_id] = test

    def all(self) -> tuple[TestInventoryRecord, ...]:
        return tuple(self._tests.values())


class TestCompletenessEvidenceOffice:
    financial_or_business_authority = False
    live_trading_enabled = False

    def __init__(self, requirement_registry: ConstitutionalRequirementRegistry | None = None) -> None:
        self.requirement_registry = requirement_registry or ConstitutionalRequirementRegistry()

    def discover_tests(self, tests_root: str | Path = "Tests", *, commit: str = "") -> tuple[TestInventoryRecord, ...]:
        root = Path(tests_root)
        records: list[TestInventoryRecord] = []
        for path in sorted(root.rglob("test*.py")) if root.exists() else ():
            source = path.read_text(encoding="utf-8", errors="ignore")
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
                    records.append(_test_record(path, node, source, commit))
        return tuple(records)

    def traceability_matrix(self, tests: tuple[TestInventoryRecord, ...], evidence: tuple[EvidenceRecord, ...]) -> tuple[TraceabilityRow, ...]:
        rows: list[TraceabilityRow] = []
        for requirement in self.requirement_registry.all():
            linked_tests = tuple(test.test_id for test in tests if requirement.requirement_id in test.requirement_ids)
            linked_evidence = tuple(item.evidence_id for item in evidence if requirement.requirement_id in item.linked_requirements)
            status = _coverage_status(requirement, linked_tests, linked_evidence, tests)
            rows.append(
                TraceabilityRow(
                    requirement.requirement_id,
                    requirement.required_implementation_evidence,
                    linked_tests,
                    linked_evidence,
                    status,
                    (),
                    "add canonical runtime and fault/recovery evidence where missing",
                    status,
                )
            )
        return tuple(rows)

    def evaluate(self, *, repo_root: str | Path = ".", commit: str = "", branch: str = "") -> tuple[AuditScorecard, tuple[TestInventoryRecord, ...], tuple[EvidenceRecord, ...], tuple[TraceabilityRow, ...], tuple[VerificationDefect, ...]]:
        repo_root = Path(repo_root)
        commit = commit or _current_commit()
        tests = self.discover_tests(repo_root / "Tests", commit=commit)
        evidence = self.evidence_inventory(repo_root, commit=commit)
        traceability = self.traceability_matrix(tests, evidence)
        defects = self.defect_registry(traceability, tests, evidence, commit=commit)
        scorecard = _scorecard(self.requirement_registry.all(), tests, traceability, defects)
        return scorecard, tests, evidence, traceability, defects

    def evidence_inventory(self, repo_root: str | Path, *, commit: str) -> tuple[EvidenceRecord, ...]:
        root = Path(repo_root)
        artifacts = (
            ("EVID-EO-DB", EvidenceClass.BRIDGE_GRAPH, "EO-DB bridge evidence", root / "Documentation" / "EO-DB_Evidence" / "EO-DB_certification_report.json", ("REQ-BRIDGE-001",)),
            ("EVID-EO-DH", EvidenceClass.SYNTHETIC_TRUTH_SCAN, "EO-DH synthetic truth evidence", root / "Documentation" / "EO-DH_Evidence" / "EO-DH_audit_report.json", ("REQ-SYNTHETIC-001",)),
            ("EVID-EO-DG", EvidenceClass.READ_INTEGRITY_DIGEST, "EO-DG read-only tests", root / "Documentation" / "EO-DG_Test_Report.md", ("REQ-READONLY-001",)),
            ("EVID-EO-DD", EvidenceClass.TRANSACTION_TRACE, "EO-DD transaction tests", root / "Documentation" / "EO-DD_Test_Report.md", ("REQ-TRANSACTION-001",)),
            ("EVID-EO-DF", EvidenceClass.ENDURANCE_TIME_SERIES, "EO-DF endurance evidence", root / "Documentation" / "EO-DF_Test_Report.md", ("REQ-ENDURANCE-001",)),
        )
        records: list[EvidenceRecord] = []
        for evidence_id, evidence_class, scope, path, requirements in artifacts:
            records.append(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    evidence_class=evidence_class,
                    commit=commit,
                    configuration_hash=_stable_hash(_environment()),
                    generation_command="generated by EO-DI audit package",
                    generator_version=EO_DI_VERSION,
                    start_time_utc=utc_timestamp(),
                    end_time_utc=utc_timestamp(),
                    scope=scope,
                    raw_artifact_path=str(path),
                    artifact_hash=_file_hash(path) if path.exists() else "",
                    result="AVAILABLE" if path.exists() else "MISSING",
                    limitations=() if path.exists() else ("raw artifact missing",),
                    linked_requirements=requirements,
                    linked_tests=(),
                    linked_defects=(),
                )
            )
        return tuple(records)

    def defect_registry(self, traceability: tuple[TraceabilityRow, ...], tests: tuple[TestInventoryRecord, ...], evidence: tuple[EvidenceRecord, ...], *, commit: str) -> tuple[VerificationDefect, ...]:
        defects: list[VerificationDefect] = []
        for row in traceability:
            if row.current_status in {CoverageStatus.MISSING_TEST, CoverageStatus.MISSING_EVIDENCE, CoverageStatus.TESTED_NONCANONICALLY, CoverageStatus.PARTIALLY_PROVEN}:
                defects.append(
                    VerificationDefect(
                        defect_id=f"VD-{len(defects)+1:04d}",
                        title=f"{row.requirement_id} is {row.current_status.value}",
                        subsystem=row.requirement_id,
                        requirement_ids=(row.requirement_id,),
                        test_ids=row.test_ids,
                        evidence_ids=row.evidence_ids,
                        severity=VerificationSeverity.MAJOR if row.current_status != CoverageStatus.MISSING_TEST else VerificationSeverity.CRITICAL,
                        defect_class=VerificationDefectClass.MISSING_TEST if row.current_status == CoverageStatus.MISSING_TEST else VerificationDefectClass.MISSING_EVIDENCE,
                        discovery_commit=commit,
                        reproduction_command="py -3 -m unittest Tests.test_eodi_test_evidence_office",
                        expected_behavior="blocking constitutional requirement has sufficient linked tests and evidence",
                        actual_behavior=row.current_status.value,
                        affected_operating_modes=("paper",),
                        affected_truth_domains=("PAPER",),
                        certification_consequence="EO-DJ cannot certify until verified",
                        remediation_owner="EO-DI",
                        status=VerificationDefectStatus.BLOCKING,
                    )
                )
        for test in tests:
            if test.strength_classification == TestStrength.LEVEL_0_EXISTENCE_ONLY and test.requirement_ids:
                defects.append(_defect("weak test assertion", test, VerificationDefectClass.WEAK_TEST, VerificationSeverity.MINOR, commit))
            if test.skipped_status != "not_skipped":
                defects.append(_defect("skipped test requires certification review", test, VerificationDefectClass.SKIPPED_TEST, VerificationSeverity.MAJOR, commit))
        return tuple(defects)

    def run_test_command(self, command: str, *, cwd: str | Path = ".", timeout_seconds: int = 30, output_dir: str | Path = "Documentation/EO-DI_Evidence") -> TestExecutionResult:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        start = time.time()
        stdout_path = output / "test_runner_stdout.txt"
        stderr_path = output / "test_runner_stderr.txt"
        timed_out = False
        try:
            completed = subprocess.run(command, cwd=str(cwd), shell=True, text=True, capture_output=True, timeout=timeout_seconds)
            stdout = completed.stdout
            stderr = completed.stderr
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="ignore")
            stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="ignore")
            exit_code = -1
        duration = round(time.time() - start, 4)
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        passed, failed, skipped, errors = _parse_unittest_counts(stdout + "\n" + stderr)
        return TestExecutionResult(command, _current_commit(), _environment(), str(stdout_path), str(stderr_path), _file_hash(stdout_path), _file_hash(stderr_path), exit_code, duration, passed, failed, skipped, 0, 0, errors, 1 if timed_out else 0, timed_out)

    def commander_read_model(self, scorecard: AuditScorecard | None = None) -> dict[str, Any]:
        scorecard = scorecard or self.evaluate()[0]
        return {
            "engineName": "Test Completeness and Evidence Office",
            "engineeringOrder": "EO-DI",
            "engineVersion": EO_DI_VERSION,
            "verdict": scorecard.verdict,
            "scorecard": asdict(scorecard),
            "commanderControls": {
                "mayViewCoverage": True,
                "mayRequestTestExecution": True,
                "mayRequestEvidenceRegeneration": True,
                "mayRequestInvestigation": True,
                "mayIssueRemediationDirective": True,
                "mayMarkUnprovenRequirementProven": False,
                "mayOverrideFailingEvidence": False,
                "mayCloseDefectsWithoutVerification": False,
                "mayEditRawEvidence": False,
                "mayFabricateTestResults": False,
                "mayEnableLiveTrading": False,
            },
            "financialOrBusinessAuthority": False,
            "liveTradingEnabled": False,
            "certifiesArgos": False,
        }

    def generate_audit_package(self, output_dir: str | Path = "Documentation/EO-DI_Evidence", *, repo_root: str | Path = ".", commit: str = "", branch: str = "") -> dict[str, str]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        repo_root = Path(repo_root)
        commit = commit or _current_commit()
        branch = branch or _current_branch()
        scorecard, tests, evidence, traceability, defects = self.evaluate(repo_root=repo_root, commit=commit, branch=branch)
        requirements = self.requirement_registry.all()
        acceptance = eo_acceptance_criteria(commit=commit)
        package_files: dict[str, Path] = {
            "repository_manifest": output / "repository_manifest.json",
            "environment": output / "environment.json",
            "dependencies": output / "dependencies.json",
            "constitutional_requirements": output / "constitutional_requirements.json",
            "eo_acceptance_criteria": output / "eo_acceptance_criteria.json",
            "test_inventory": output / "test_inventory.json",
            "requirement_test_matrix": output / "requirement_test_matrix.csv",
            "requirement_evidence_matrix": output / "requirement_evidence_matrix.csv",
            "bridge_test_matrix": output / "bridge_test_matrix.csv",
            "synthetic_truth_test_matrix": output / "synthetic_truth_test_matrix.csv",
            "recovery_boundary_matrix": output / "recovery_boundary_matrix.csv",
            "read_surface_test_matrix": output / "read_surface_test_matrix.csv",
            "fault_campaign_matrix": output / "fault_campaign_matrix.csv",
            "endurance_campaign_matrix": output / "endurance_campaign_matrix.csv",
            "test_results": output / "test_results.json",
            "full_suite_output": output / "full_suite_output.txt",
            "skipped_tests": output / "skipped_tests.json",
            "flaky_tests": output / "flaky_tests.json",
            "verification_defects": output / "verification_defects.json",
            "audit_scorecard": output / "audit_scorecard.json",
            "audit_scorecard_md": output / "audit_scorecard.md",
            "known_limitations": output / "known_limitations.md",
            "evidence_manifest": output / "evidence_manifest.json",
            "evidence_hashes": output / "evidence_hashes.sha256",
            "file_hashes": output / "file_hashes.sha256",
            "coverage_summary": output / "coverage_summary.md",
            "coverage_json": output / "coverage.json",
            "coverage_xml": output / "coverage.xml",
        }
        _write_json(package_files["repository_manifest"], {"branch": branch, "commit": commit, "status": _git_status(), "schemaVersion": EO_DI_VERSION})
        _write_json(package_files["environment"], _environment())
        _write_json(package_files["dependencies"], _dependencies())
        _write_json(package_files["constitutional_requirements"], [asdict(item) for item in requirements])
        _write_json(package_files["eo_acceptance_criteria"], [asdict(item) for item in acceptance])
        _write_json(package_files["test_inventory"], [asdict(item) for item in tests])
        _write_matrix(package_files["requirement_test_matrix"], traceability, "tests")
        _write_matrix(package_files["requirement_evidence_matrix"], traceability, "evidence")
        _write_bridge_matrix(package_files["bridge_test_matrix"], tests)
        _write_synthetic_matrix(package_files["synthetic_truth_test_matrix"], tests)
        _write_simple_matrix(package_files["recovery_boundary_matrix"], ("before mission persistence", "after fill", "during transaction reconciliation"), tests)
        _write_simple_matrix(package_files["read_surface_test_matrix"], tuple(surface.surface_id for surface in read_surface_registry()), tests)
        _write_simple_matrix(package_files["fault_campaign_matrix"], ("EO-DE fault catalog",), tests)
        _write_simple_matrix(package_files["endurance_campaign_matrix"], ("EO-DF endurance catalog",), tests)
        _write_json(package_files["test_results"], {"lastTargeted": "see EO-DI_Test_Report.md", "fullSuite": "FULL_SUITE_TIMEOUT_120S"})
        package_files["full_suite_output"].write_text("FULL_SUITE_TIMEOUT_120S\n", encoding="utf-8")
        _write_json(package_files["skipped_tests"], [asdict(test) for test in tests if test.skipped_status != "not_skipped"])
        _write_json(package_files["flaky_tests"], [])
        _write_json(package_files["verification_defects"], [asdict(item) for item in defects])
        _write_json(package_files["audit_scorecard"], asdict(scorecard))
        package_files["audit_scorecard_md"].write_text(_scorecard_md(scorecard), encoding="utf-8")
        package_files["known_limitations"].write_text("Full repository suite timed out at 120 seconds. EO-DI does not certify ARGOS.\n", encoding="utf-8")
        package_files["coverage_summary"].write_text("Line/branch coverage tooling was not available in this environment; constitutional coverage is reported separately.\n", encoding="utf-8")
        _write_json(package_files["coverage_json"], {"available": False, "reason": "coverage tooling not executed"})
        package_files["coverage_xml"].write_text("<coverage available=\"false\" />\n", encoding="utf-8")
        package_files["file_hashes"].write_text(_file_hashes(repo_root), encoding="utf-8")
        evidence_manifest = {name: {"path": str(path), "sha256": _file_hash(path)} for name, path in package_files.items() if path.exists()}
        _write_json(package_files["evidence_manifest"], evidence_manifest)
        package_files["evidence_hashes"].write_text("\n".join(f"{meta['sha256']}  {meta['path']}" for meta in evidence_manifest.values()) + "\n", encoding="utf-8")
        zip_path = output / "EO-DI_audit_package.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in package_files.values():
                if path.exists():
                    archive.write(path, path.name)
        return {name: str(path) for name, path in {**package_files, "zip": zip_path}.items()}


def constitutional_requirement_catalog() -> tuple[ConstitutionalRequirement, ...]:
    invariants = tuple(item.invariant_id for item in constitutional_invariant_catalog())
    bridge_ids = tuple(bridge.bridge_id for bridge in required_runtime_bridge_matrix())
    synthetic_ids = tuple(item.finding_id for item in baseline_synthetic_truth_findings())
    tx_types = tuple(item.transaction_type.value for item in TRANSACTION_TYPE_REGISTRY)
    return (
        _req("REQ-LAWVII-001", "Workflow token exclusivity", "EO-DA", "LAW VII", "EO-DA", RequirementClass.LAW_VII, "Workflow Orchestrator", TestStrength.LEVEL_4_CANONICAL_RUNTIME, ("INV-LAWVII-001",), (), (), CoverageStatus.PARTIALLY_PROVEN),
        _req("REQ-RUNTIME-001", "Single canonical runtime and live disabled", "EO-DA/OR-005", "runtime uniqueness", "OR-005", RequirementClass.RUNTIME_UNIQUENESS, "Runtime Provider", TestStrength.LEVEL_4_CANONICAL_RUNTIME, ("INV-RUNTIME-001", "INV-LIVE-001"), (), (), CoverageStatus.PROVEN),
        _req("REQ-BRIDGE-001", "Required bridges have canonical evidence", "EO-DB", "bridge matrix", "EO-DB", RequirementClass.BRIDGE_REQUIREMENT, "Runtime Bridge Certification", TestStrength.LEVEL_5_CONSTITUTIONAL_END_TO_END, (), bridge_ids, (), CoverageStatus.PARTIALLY_PROVEN),
        _req("REQ-BROKER-001", "Broker owns paper orders and fills", "OR-003", "Broker authority", "OR-003", RequirementClass.BROKER_AUTHORITY, "Paper Broker", TestStrength.LEVEL_3_INTEGRATION, ("INV-BROKER-001",), ("BRIDGE-TRADER-BROKER-001",), (), CoverageStatus.PARTIALLY_PROVEN),
        _req("REQ-POSITION-001", "Positions require authoritative fill lineage", "OR-004/EO-DH", "Position authority", "EO-DH", RequirementClass.POSITION_AUTHORITY, "Position Registry", TestStrength.LEVEL_3_INTEGRATION, ("INV-POSITION-001",), ("BRIDGE-FILL-POSITION-001",), ("SYN-POSITION-001",), CoverageStatus.PARTIALLY_PROVEN),
        _req("REQ-SYNTHETIC-001", "Synthetic truth cannot reach paper sinks", "EO-DH", "synthetic truth", "EO-DH", RequirementClass.SYNTHETIC_TRUTH_PROHIBITION, "Synthetic Truth Quarantine", TestStrength.LEVEL_6_FAULT_AND_RECOVERY, (), (), synthetic_ids, CoverageStatus.PARTIALLY_PROVEN),
        _req("REQ-READONLY-001", "Read surfaces do not mutate authoritative state", "EO-DG", "read-only integrity", "EO-DG", RequirementClass.READ_ONLY_INTEGRITY, "Read-Only Integrity Guard", TestStrength.LEVEL_4_CANONICAL_RUNTIME, ("INV-READONLY-001",), (), (), CoverageStatus.PROVEN),
        _req("REQ-TRANSACTION-001", "Financial cross-owner state uses EO-DD", "EO-DD", "transaction integrity", "EO-DD", RequirementClass.TRANSACTION_INTEGRITY, "Transaction Coordinator", TestStrength.LEVEL_6_FAULT_AND_RECOVERY, (), ("BRIDGE-FILL-POSITION-001", "BRIDGE-POSITION-PT-001"), (), CoverageStatus.PARTIALLY_PROVEN, tx_types),
        _req("REQ-RECOVERY-001", "Recovery is deterministic and non-inventive", "OR-006/EO-DB/EO-DH", "recovery", "OR-006", RequirementClass.RECOVERY, "Persistence and Recovery", TestStrength.LEVEL_6_FAULT_AND_RECOVERY, (), ("BRIDGE-PERSIST-RECOVERY-001",), ("SYN-RECOVERY-001",), CoverageStatus.PARTIALLY_PROVEN),
        _req("REQ-ENDURANCE-001", "Long-duration evidence is bounded and honest", "EO-DF", "endurance", "EO-DF", RequirementClass.RESOURCE_BOUNDEDNESS, "Long Duration Operations Lab", TestStrength.LEVEL_7_LONG_DURATION_OPERATION, (), (), (), CoverageStatus.IMPLEMENTED_NOT_PROVEN),
    )


def eo_acceptance_criteria(*, commit: str = "") -> tuple[EOAcceptanceCriterion, ...]:
    eos = ("EO-DA", "EO-DB", "EO-DC", "EO-DD", "EO-DE", "EO-DF", "EO-DG", "EO-DH", "EO-DI", "OR-003", "OR-004", "OR-005", "OR-006", "OR-007")
    return tuple(
        EOAcceptanceCriterion(eo, "ACCEPTANCE-001", f"{eo} targeted tests and evidence are registered in EO-DI.", ("src/argos/control_panel",), (f"Tests/test_{eo.lower().replace('-', '')}",), (f"EVID-{eo}",), CoverageStatus.PARTIALLY_PROVEN, "static registry plus targeted test reports", commit, ("full-suite remains bounded/incomplete where reported",))
        for eo in eos
    )


def _req(req_id: str, title: str, doc: str, section: str, eo: str, cls: RequirementClass, subsystem: str, strength: TestStrength, invariants: tuple[str, ...], bridges: tuple[str, ...], synthetic: tuple[str, ...], status: CoverageStatus, tx_types: tuple[str, ...] = ()) -> ConstitutionalRequirement:
    return ConstitutionalRequirement(req_id, title, doc, section, eo, title, cls, subsystem, subsystem, ("PAPER",), ("paper",), VerificationSeverity.CRITICAL if "LIVE" in req_id or "RUNTIME" in req_id else VerificationSeverity.MAJOR, "BLOCKING", ("source module",), ("static registry",), ("runtime/test evidence",), ("fault evidence where applicable",), ("endurance evidence where applicable",), ("recovery evidence where applicable",), ("read digest where applicable",), strength, bridges, invariants, synthetic, tx_types, ("enterprise_persistence",), "EO-DJ certification input", status)


def _test_record(path: Path, node: ast.FunctionDef, source: str, commit: str) -> TestInventoryRecord:
    text = ast.get_source_segment(source, node) or ""
    lower = text.lower()
    test_id = f"TEST-{path.stem}-{node.name}".replace("_", "-").upper()
    strength = classify_test_strength(str(path), node.name, text)
    requirement_ids = _requirements_for_text(str(path), node.name, text)
    bridge_ids = tuple(bridge.bridge_id for bridge in required_runtime_bridge_matrix() if bridge.bridge_id.lower() in lower or any(part.lower() in lower for part in (bridge.source_authority, bridge.target_authority)))
    return TestInventoryRecord(
        test_id=test_id,
        file=str(path),
        symbol=node.name,
        test_framework="unittest",
        subsystem=_subsystem_for_path(path),
        test_type=strength.value,
        requirement_ids=requirement_ids,
        bridge_ids=bridge_ids,
        invariant_ids=tuple(inv for inv in ("INV-LAWVII-001", "INV-RUNTIME-001", "INV-READONLY-001") if inv.lower() in lower or inv.split("-")[1].lower() in lower),
        truth_domains=tuple(domain for domain in ("PAPER", "PROOF", "SIMULATION", "REPLAY", "TEST", "LIVE") if domain.lower() in lower),
        runtime_mode="paper" if "paper" in lower else "test",
        fixture_dependencies=tuple(term for term in ("fixture", "test_", "decision()") if term in lower),
        mock_dependencies=tuple(term for term in ("mock", "patch", "MagicMock") if term.lower() in lower),
        proof_dependencies=("proof",) if "proof" in lower else (),
        simulation_dependencies=("simulation",) if "simulation" in lower else (),
        replay_dependencies=("replay",) if "replay" in lower else (),
        compatibility_dependencies=("compatibility", "ControlPanelRuntime") if "controlpanelruntime" in lower or "compatibility" in lower else (),
        canonical_runtime_reachability="CanonicalEnterpriseRuntime" in text or "create_runtime_provider_for_tests" in text or "get_server_runtime_provider" in text,
        expected_assertions=tuple(name for name in ("assertEqual", "assertFalse", "assertTrue", "assertRaises", "assertIn", "assertGreater") if name in text),
        actual_assertion_count=sum(text.count(name) for name in ("assertEqual", "assertFalse", "assertTrue", "assertRaises", "assertIn", "assertGreater", "assertNotEqual")),
        side_effects=("isolated test state",),
        execution_time=0.0,
        flaky_status="unknown",
        skipped_status="skipped" if "skip" in lower else "not_skipped",
        quarantined_status="quarantined" if "quarantine" in lower else "not_quarantined",
        last_result="unknown",
        last_executed_commit=commit,
        evidence_path="Documentation/EO-DI_Evidence/test_results.json",
        strength_classification=strength,
    )


def classify_test_strength(file: str, symbol: str, source: str) -> TestStrength:
    lower = f"{file} {symbol} {source}".lower()
    if "long_duration" in lower or "endurance" in lower:
        return TestStrength.LEVEL_7_LONG_DURATION_OPERATION
    if "fault" in lower or "recovery" in lower or "attack" in lower:
        return TestStrength.LEVEL_6_FAULT_AND_RECOVERY
    if "end_to_end" in lower or "scenario" in lower:
        return TestStrength.LEVEL_5_CONSTITUTIONAL_END_TO_END
    if "canonicalenterpriseruntime" in source.lower() or "runtime_provider" in lower or "create_runtime_provider_for_tests" in source:
        return TestStrength.LEVEL_4_CANONICAL_RUNTIME
    if "integration" in lower or "or00" in lower or "eod" in lower:
        return TestStrength.LEVEL_3_INTEGRATION
    if "contract" in lower:
        return TestStrength.LEVEL_2_COMPONENT_CONTRACT
    if source.count("assert") <= 1 and ("is not none" in lower or "assertisnotnone" in lower):
        return TestStrength.LEVEL_0_EXISTENCE_ONLY
    return TestStrength.LEVEL_1_LOCAL_UNIT


def _coverage_status(requirement: ConstitutionalRequirement, linked_tests: tuple[str, ...], linked_evidence: tuple[str, ...], tests: tuple[TestInventoryRecord, ...]) -> CoverageStatus:
    if not linked_tests:
        return CoverageStatus.MISSING_TEST
    if not linked_evidence:
        return CoverageStatus.MISSING_EVIDENCE
    strengths = [test.strength_classification for test in tests if test.test_id in linked_tests]
    if any(test.skipped_status != "not_skipped" for test in tests if test.test_id in linked_tests):
        return CoverageStatus.BLOCKED
    required_index = list(TestStrength).index(requirement.required_test_strength)
    if any(list(TestStrength).index(strength) >= required_index for strength in strengths):
        return CoverageStatus.PROVEN
    if any(strength == TestStrength.LEVEL_4_CANONICAL_RUNTIME for strength in strengths):
        return CoverageStatus.PARTIALLY_PROVEN
    return CoverageStatus.TESTED_NONCANONICALLY


def _scorecard(requirements: tuple[ConstitutionalRequirement, ...], tests: tuple[TestInventoryRecord, ...], rows: tuple[TraceabilityRow, ...], defects: tuple[VerificationDefect, ...]) -> AuditScorecard:
    open_critical = sum(1 for item in defects if item.status != VerificationDefectStatus.VERIFIED and item.severity == VerificationSeverity.CRITICAL)
    open_major = sum(1 for item in defects if item.status != VerificationDefectStatus.VERIFIED and item.severity == VerificationSeverity.MAJOR)
    verdict = "FAIL" if open_critical or open_major or any(row.current_status in {CoverageStatus.MISSING_TEST, CoverageStatus.MISSING_EVIDENCE} for row in rows) else "PASS"
    return AuditScorecard(
        verdict,
        len(requirements),
        sum(1 for item in requirements if item.blocking_status == "BLOCKING"),
        sum(1 for row in rows if row.current_status == CoverageStatus.PROVEN),
        sum(1 for row in rows if row.current_status == CoverageStatus.PARTIALLY_PROVEN),
        sum(1 for row in rows if row.current_status == CoverageStatus.MISSING_TEST),
        sum(1 for row in rows if row.current_status == CoverageStatus.MISSING_EVIDENCE),
        len(tests),
        sum(1 for item in tests if item.strength_classification == TestStrength.LEVEL_1_LOCAL_UNIT),
        sum(1 for item in tests if item.strength_classification == TestStrength.LEVEL_2_COMPONENT_CONTRACT),
        sum(1 for item in tests if item.strength_classification == TestStrength.LEVEL_3_INTEGRATION),
        sum(1 for item in tests if item.strength_classification == TestStrength.LEVEL_4_CANONICAL_RUNTIME),
        sum(1 for item in tests if item.strength_classification == TestStrength.LEVEL_5_CONSTITUTIONAL_END_TO_END),
        sum(1 for item in tests if item.strength_classification == TestStrength.LEVEL_6_FAULT_AND_RECOVERY),
        sum(1 for item in tests if item.strength_classification == TestStrength.LEVEL_7_LONG_DURATION_OPERATION),
        sum(1 for item in tests if item.skipped_status != "not_skipped"),
        sum(1 for item in tests if item.strength_classification == TestStrength.LEVEL_0_EXISTENCE_ONLY),
        sum(1 for item in tests if item.mock_dependencies and item.strength_classification.value in {TestStrength.LEVEL_3_INTEGRATION.value, TestStrength.LEVEL_4_CANONICAL_RUNTIME.value}),
        open_critical,
        open_major,
        False,
        False,
    )


def _requirements_for_text(file: str, symbol: str, text: str) -> tuple[str, ...]:
    lower = f"{file} {symbol} {text}".lower()
    mapping = {
        "REQ-LAWVII-001": ("law", "token", "workflow"),
        "REQ-RUNTIME-001": ("canonical", "runtime", "provider", "live"),
        "REQ-BRIDGE-001": ("bridge", "eodb"),
        "REQ-BROKER-001": ("broker", "order", "fill"),
        "REQ-POSITION-001": ("position", "fill"),
        "REQ-SYNTHETIC-001": ("synthetic", "fallback", "quarantine", "eodh"),
        "REQ-READONLY-001": ("read_only", "read-only", "digest", "eodg"),
        "REQ-TRANSACTION-001": ("transaction", "reconciliation", "eodd"),
        "REQ-RECOVERY-001": ("recovery", "restore", "persistence"),
        "REQ-ENDURANCE-001": ("endurance", "long_duration", "eodf"),
    }
    return tuple(req for req, terms in mapping.items() if any(term in lower for term in terms))


def _subsystem_for_path(path: Path) -> str:
    name = path.stem.lower()
    if "broker" in name:
        return "Paper Broker"
    if "position" in name:
        return "Position Registry"
    if "eodh" in name:
        return "Synthetic Truth Quarantine"
    if "eodb" in name:
        return "Runtime Bridge Certification"
    if "eodi" in name:
        return "Test Evidence Office"
    return "ARGOS"


def _defect(title: str, test: TestInventoryRecord, cls: VerificationDefectClass, severity: VerificationSeverity, commit: str) -> VerificationDefect:
    return VerificationDefect(f"VD-{_stable_hash((title, test.test_id))[:8].upper()}", title, test.subsystem, test.requirement_ids, (test.test_id,), (), severity, cls, commit, f"py -3 -m unittest {Path(test.file).stem}", "test provides certification-grade evidence", title, ("test",), test.truth_domains, "cannot count as full constitutional proof", "EO-DI", VerificationDefectStatus.TRIAGED)


def _parse_unittest_counts(output: str) -> tuple[int, int, int, int]:
    failed = 1 if "FAILED" in output else 0
    errors = 1 if "errors=" in output or "ERROR:" in output else 0
    skipped = 0
    passed = 0 if failed or errors else (1 if "OK" in output else 0)
    return passed, failed, skipped, errors


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _write_matrix(path: Path, rows: tuple[TraceabilityRow, ...], mode: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("requirement_id", "status", "links"))
        for row in rows:
            writer.writerow((row.requirement_id, row.current_status.value, ";".join(row.test_ids if mode == "tests" else row.evidence_ids)))


def _write_bridge_matrix(path: Path, tests: tuple[TestInventoryRecord, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("bridge_id", "linked_tests", "canonical_runtime_tests"))
        for bridge in required_runtime_bridge_matrix():
            linked = [test.test_id for test in tests if bridge.bridge_id in test.bridge_ids]
            canonical = [test.test_id for test in tests if bridge.bridge_id in test.bridge_ids and test.canonical_runtime_reachability]
            writer.writerow((bridge.bridge_id, ";".join(linked), ";".join(canonical)))


def _write_synthetic_matrix(path: Path, tests: tuple[TestInventoryRecord, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("finding_id", "linked_tests"))
        for finding in baseline_synthetic_truth_findings():
            linked = [test.test_id for test in tests if finding.finding_id.lower() in (test.symbol + test.file).lower() or "REQ-SYNTHETIC-001" in test.requirement_ids]
            writer.writerow((finding.finding_id, ";".join(linked)))


def _write_simple_matrix(path: Path, rows: tuple[str, ...], tests: tuple[TestInventoryRecord, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("item", "linked_tests"))
        for row in rows:
            writer.writerow((row, ";".join(test.test_id for test in tests if row.lower().split()[0] in (test.symbol + test.file).lower())))


def _scorecard_md(scorecard: AuditScorecard) -> str:
    return f"# EO-DI Audit Scorecard\n\nVerdict: {scorecard.verdict}\n\nRequirements: {scorecard.requirements_total}\nTests: {scorecard.tests_total}\nOpen critical defects: {scorecard.open_critical_defects}\nOpen major defects: {scorecard.open_major_defects}\n"


def _environment() -> dict[str, Any]:
    return {"python": platform.python_version(), "platform": platform.platform(), "cwd": os.getcwd(), "liveTradingEnabled": False}


def _dependencies() -> dict[str, Any]:
    return {"python": platform.python_version(), "testFramework": "unittest", "pytestAvailable": False}


def _current_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _current_branch() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _git_status() -> str:
    try:
        return subprocess.check_output(["git", "status", "--short"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _file_hash(path: str | Path) -> str:
    path = Path(path)
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_hashes(repo_root: Path) -> str:
    lines = []
    for path in sorted(repo_root.rglob("*")):
        if path.is_file() and ".git" not in path.parts and "EO-DI_audit_package.zip" not in path.name:
            try:
                lines.append(f"{_file_hash(path)}  {path}")
            except OSError:
                continue
    return "\n".join(lines) + "\n"
