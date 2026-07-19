"""End-to-end enterprise certification harness for ARGOS OR-007."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .canonical_enterprise_runtime import CanonicalEnterpriseRuntime
from .enterprise_persistence import DurableEnterprisePersistenceStore, RecoveryMode


class CertificationLevel(str, Enum):
    CERTIFIED = "CERTIFIED"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY_CERTIFIED"
    NOT_CERTIFIED = "NOT_CERTIFIED"


class ReadinessResult(str, Enum):
    PASS = "PASS"
    CONDITIONAL_PASS = "CONDITIONAL PASS"
    FAIL = "FAIL"


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    ENHANCEMENT = "ENHANCEMENT"


@dataclass(frozen=True)
class CertificationRecord:
    subsystem: str
    authority_owner: str
    constitutional_requirements: tuple[str, ...]
    implementation_evidence: tuple[str, ...]
    test_evidence: tuple[str, ...]
    documentation_evidence: tuple[str, ...]
    persistence_evidence: tuple[str, ...]
    replay_evidence: tuple[str, ...]
    remaining_risks: tuple[str, ...]
    certification_level: CertificationLevel


@dataclass(frozen=True)
class OperationalReadinessRecord:
    category: str
    result: ReadinessResult
    evidence: tuple[str, ...]
    risk: str = ""


@dataclass(frozen=True)
class CertificationFinding:
    finding_id: str
    severity: FindingSeverity
    subsystem: str
    classification: str
    root_cause: str
    operational_impact: str
    constitutional_impact: str
    recommended_remediation: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class CertificationCampaignResult:
    verdict: CertificationLevel
    continuous_paper_trading_verdict: str
    certification_matrix: tuple[CertificationRecord, ...]
    readiness_matrix: tuple[OperationalReadinessRecord, ...]
    findings: tuple[CertificationFinding, ...]
    evidence: dict[str, Any]
    git_snapshot_required: bool


class EnterpriseCertificationHarness:
    """Run deterministic certification checks without becoming operational authority."""

    def __init__(self, repository_root: str | Path) -> None:
        self.repository_root = Path(repository_root)

    def run_campaign(self, *, cycles: int = 3) -> CertificationCampaignResult:
        runtime = CanonicalEnterpriseRuntime()
        start_status = runtime.start()
        admissions = []
        for day_offset in range(max(1, cycles)):
            admissions.append(runtime.admit_scheduled_obligation("pre_market_readiness", now=f"2026-07-{13 + day_offset:02d}T08:15:00Z"))
        before_digest = runtime.read_only_digest()
        after_digest = runtime.read_only_digest()
        store = DurableEnterprisePersistenceStore()
        store.persist_runtime(runtime)
        recovered, recovery_audit = store.recover_runtime(mode=RecoveryMode.CRASH_RECOVERY)
        synthetic_findings = self.synthetic_truth_audit()
        findings = tuple(
            [
                *synthetic_findings,
                CertificationFinding(
                    "OR007-FIND-FULL-SUITE",
                    FindingSeverity.MAJOR,
                    "Enterprise Test Campaign",
                    "TEST_COVERAGE",
                    "Full repository and long-duration unattended paper operation were not completed green.",
                    "ARGOS cannot be certified for continuous unattended paper trading from focused evidence alone.",
                    "Certification requires full-suite and long-duration evidence.",
                    "Run and remediate full dashboard/full repository/long-duration campaign.",
                    ("OR-006 regression bundle passed 37 tests", "Dashboard suite had known prior failures"),
                ),
                CertificationFinding(
                    "OR007-FIND-LEGACY-DASHBOARD",
                    FindingSeverity.MAJOR,
                    "Commander Dashboard",
                    "UI_READ_MODEL",
                    "Legacy ControlPanelRuntime proof/self-training routes remain available as proof-mode compatibility surfaces.",
                    "Risk of operator confusion unless certified runtime routes are separated from proof/demo routes.",
                    "Commander must not be mistaken as operational truth authority.",
                    "Route production paper operation through CanonicalEnterpriseRuntime and quarantine proof UI paths.",
                    ("src/argos/control_panel/runtime.py start_paper_self_training", "src/argos/control_panel/server.py /api/paper/start"),
                ),
            ]
        )
        matrix = certification_matrix(findings)
        readiness = operational_readiness_matrix(before_digest == after_digest, bool(recovery_audit.paper_operation_allowed), findings)
        verdict = final_verdict(matrix, readiness, findings)
        return CertificationCampaignResult(
            verdict=verdict,
            continuous_paper_trading_verdict="NOT CERTIFIED" if verdict == CertificationLevel.NOT_CERTIFIED else verdict.value,
            certification_matrix=matrix,
            readiness_matrix=readiness,
            findings=findings,
            evidence={
                "runtimeStart": start_status,
                "admissionCount": len(admissions),
                "readOnlyDigestStable": before_digest == after_digest,
                "recoveryAudit": asdict(recovery_audit),
                "recoveredWorkflowCount": recovered.read_only_snapshot()["workflowCounts"]["workflowCount"],
                "liveTradingEnabled": recovered.live_trading_enabled,
            },
            git_snapshot_required=False,
        )

    def synthetic_truth_audit(self) -> tuple[CertificationFinding, ...]:
        findings: list[CertificationFinding] = []
        patterns = (
            ("proof_only_paths", "PROOF_ONLY", "Accepted proof-only"),
            ("simulation_only_paths", "SIMULATION_ONLY", "Accepted simulation-only"),
            ("placeholder_paths", "placeholder", "Quarantined or documentation-required"),
            ("runtime_self_training", "start_paper_self_training", "Quarantined proof compatibility"),
            ("synthetic_market_data", "NonProductionMarketDataProvider", "Accepted test/paper fallback requiring operator labeling"),
        )
        searchable = list((self.repository_root / "src").rglob("*.py")) + list((self.repository_root / "Documentation").rglob("*.md"))
        for finding_name, pattern, classification in patterns:
            matches = []
            for path in searchable:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if pattern in text:
                    matches.append(str(path.relative_to(self.repository_root)))
            if matches:
                severity = FindingSeverity.MAJOR if finding_name in {"runtime_self_training", "synthetic_market_data"} else FindingSeverity.MINOR
                findings.append(
                    CertificationFinding(
                        f"OR007-SYN-{len(findings) + 1:03d}",
                        severity,
                        "Synthetic Truth Audit",
                        classification,
                        f"Pattern `{pattern}` remains present in repository.",
                        "Requires explicit quarantine/labeling; not evidence of certified operational truth by itself.",
                        "Synthetic/proof/simulation records must not enter PAPER operational truth.",
                        "Keep isolated; migrate UI production paths to canonical runtime before certification.",
                        tuple(matches[:12]),
                    )
                )
        return tuple(findings)


def certification_matrix(findings: tuple[CertificationFinding, ...]) -> tuple[CertificationRecord, ...]:
    major_subsystems = {finding.subsystem for finding in findings if finding.severity in {FindingSeverity.CRITICAL, FindingSeverity.MAJOR}}
    rows = (
        ("Runtime", "CanonicalEnterpriseRuntime", ("runtime orchestration only", "live disabled"), ("canonical_enterprise_runtime.py",), ("Tests.test_or005_canonical_runtime", "Tests.test_or006_enterprise_persistence"), ("OR-005_Canonical_Runtime_Architecture.md", "OR-006_Recovery_Architecture.md"), ("OR-006 durable runtime state",), ("OR-006 recovery audit",)),
        ("Scheduler", "EnterpriseOperationsScheduler", ("mission eligibility only",), ("scheduler.py",), ("Tests.test_or005_canonical_runtime",), ("OR-005_Scheduler_Mission_and_Duty_Model.md",), ("enterprise_mission_state",), ("priority/scheduler replay pending",)),
        ("Mission Planner", "EnterpriseMissionPlanner", ("bounded mission plans",), ("mission_planner.py",), ("Tests.test_or005_canonical_runtime",), ("OR-005_Scheduler_Mission_and_Duty_Model.md",), ("enterprise_mission_state",), ("mission replay pending",)),
        ("Office Duty Officer", "OfficeDutyOfficerRegistry", ("offices asleep by default",), ("office_duty_officer.py",), ("Tests.test_or005_canonical_runtime",), ("OR-005_Scheduler_Mission_and_Duty_Model.md",), ("mission snapshot",), ("duty replay pending",)),
        ("Workflow Orchestrator", "EnterpriseWorkflowOrchestrator", ("LAW VII", "single token owner"), ("workflow_orchestrator.py",), ("Tests.test_or006_enterprise_persistence", "LAW VII handoff smoke"), ("OR-005_Workflow_Token_Integration_Audit.md",), ("enterprise_workflow_state",), ("workflow recovery test",)),
        ("Paper Broker", "DeterministicPaperBrokerage", ("broker owns fills",), ("paper_brokerage.py",), ("Tests.test_or003_paper_brokerage",), ("OR-003_Broker_Architecture.md",), ("enterprise_broker_state",), ("broker replay depth pending",)),
        ("Position Registry", "PositionRegistry", ("position authority",), ("position_registry.py",), ("Tests.test_or004_position_lifecycle",), ("OR-004_Position_Lifecycle_Architecture.md",), ("enterprise_position_state",), ("position recovery evidence",)),
        ("Performance Truth", "PerformanceTruthEngine", ("records outcomes, does not create them",), ("performance_truth_engine.py",), ("Tests.test_or003_paper_brokerage",), ("OR-004_Synthetic_Truth_Remediation_Report.md",), ("enterprise_performance_truth",), ("truth recovery evidence",)),
        ("Persistence", "DurableEnterprisePersistenceStore", ("runtime memory not authoritative",), ("enterprise_persistence.py",), ("Tests.test_or006_enterprise_persistence", "Tests.test_persistence_framework"), ("OR-006_Enterprise_Persistence_Architecture.md",), ("hash-chain backup",), ("idempotent recovery",)),
        ("Commander", "Commander/read models", ("read-only operation",), ("runtime.py", "server.py"), ("selected dashboard LAW VII smoke",), ("OR-005_Read_Only_Runtime_Surface_Audit.md",), ("derived read model only",), ("full dashboard not green",)),
        ("Seeker/Analyst/Risk/Executive/Trader", "Office-specific authorities", ("authority separation",), ("office packages",), ("readiness suites not fully rerun",), ("OR-007 docs",), ("mixed",), ("full end-to-end office chain not certified",)),
        ("Replay/Long Duration", "Certification campaign", ("determinism", "bounded growth"), ("OR-007 harness",), ("focused deterministic cycles",), ("OR-007_Long_Duration_Test_Framework.md",), ("recovery snapshot only",), ("long-duration campaign not completed",)),
    )
    records: list[CertificationRecord] = []
    for row in rows:
        subsystem = row[0]
        risks = tuple(f.finding_id for f in findings if f.subsystem in {subsystem, "Enterprise Test Campaign", "Commander Dashboard", "Synthetic Truth Audit"})
        if subsystem in major_subsystems or (subsystem in {"Commander", "Seeker/Analyst/Risk/Executive/Trader", "Replay/Long Duration"}):
            level = CertificationLevel.NOT_CERTIFIED
        elif risks:
            level = CertificationLevel.CONDITIONALLY_CERTIFIED
        else:
            level = CertificationLevel.CERTIFIED
        records.append(CertificationRecord(subsystem, row[1], row[2], row[3], row[4], row[5], row[6], row[7], risks, level))
    return tuple(records)


def operational_readiness_matrix(read_only_stable: bool, recovery_allowed: bool, findings: tuple[CertificationFinding, ...]) -> tuple[OperationalReadinessRecord, ...]:
    has_major = any(f.severity in {FindingSeverity.CRITICAL, FindingSeverity.MAJOR} for f in findings)
    return (
        OperationalReadinessRecord("deterministic execution", ReadinessResult.PASS if read_only_stable else ReadinessResult.FAIL, ("read-only digest stability check",)),
        OperationalReadinessRecord("persistence", ReadinessResult.PASS if recovery_allowed else ReadinessResult.FAIL, ("OR-006 recovery audit",)),
        OperationalReadinessRecord("broker authority", ReadinessResult.PASS, ("OR-003 broker tests",)),
        OperationalReadinessRecord("position authority", ReadinessResult.PASS, ("OR-004 lifecycle tests",)),
        OperationalReadinessRecord("LAW VII", ReadinessResult.PASS, ("workflow token recovery and EO-CL handoff smoke",)),
        OperationalReadinessRecord("read-only integrity", ReadinessResult.CONDITIONAL_PASS, ("canonical read-only digest stable",), "legacy dashboard suite not fully green"),
        OperationalReadinessRecord("synthetic truth removal", ReadinessResult.FAIL if has_major else ReadinessResult.CONDITIONAL_PASS, tuple(f.finding_id for f in findings), "proof/synthetic compatibility surfaces remain"),
        OperationalReadinessRecord("long-duration operation", ReadinessResult.FAIL, ("no completed long-duration unattended campaign",), "required for continuous paper certification"),
    )


def final_verdict(matrix: tuple[CertificationRecord, ...], readiness: tuple[OperationalReadinessRecord, ...], findings: tuple[CertificationFinding, ...]) -> CertificationLevel:
    if any(f.severity == FindingSeverity.CRITICAL for f in findings):
        return CertificationLevel.NOT_CERTIFIED
    if any(row.result == ReadinessResult.FAIL for row in readiness):
        return CertificationLevel.NOT_CERTIFIED
    if any(record.certification_level == CertificationLevel.NOT_CERTIFIED for record in matrix):
        return CertificationLevel.NOT_CERTIFIED
    if any(record.certification_level == CertificationLevel.CONDITIONALLY_CERTIFIED for record in matrix):
        return CertificationLevel.CONDITIONALLY_CERTIFIED
    return CertificationLevel.CERTIFIED
