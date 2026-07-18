"""EO-DQ continuous paper endurance and operational certification."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import platform
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .long_duration_operations_lab import (
    AdmissionEnvironment,
    CampaignDefinition,
    DurationMode,
    EnduranceCampaignReport,
    EnduranceCampaignType,
    EndurancePassCriteria,
    EnduranceStage,
    EnduranceVerdict,
    LongDurationOperationsLaboratory,
)


EO_DQ_VERSION = "EO-DQ.1"


class PaperEnduranceVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True)
class PaperEnduranceCertification:
    verdict: PaperEnduranceVerdict
    mode: str
    campaign_count: int
    passing_campaign_count: int
    longest_uninterrupted_duration_seconds: int
    cumulative_duration_seconds: int
    wall_clock_extended_run_completed: bool
    accelerated_endurance_completed: bool
    live_trading_enabled: bool
    invariant_violations: tuple[str, ...]
    reports: tuple[dict[str, Any], ...]
    evidence_hash: str
    timestamp_utc: str
    schema_version: str = EO_DQ_VERSION


class ContinuousPaperEnduranceAuthority:
    financial_mutation_authority = False
    live_trading_enabled = False

    def __init__(self, lab: LongDurationOperationsLaboratory | None = None) -> None:
        self.lab = lab or LongDurationOperationsLaboratory()

    def run_accelerated_certification(self, *, repository_commit: str = "WORKTREE", allow_dirty_worktree: bool = True) -> PaperEnduranceCertification:
        campaigns = (
            self._definition("EO-DQ-ACTIVE-PAPER", EnduranceCampaignType.CONTROLLED_ACTIVE_PAPER, repository_commit, allow_dirty_worktree),
            self._definition("EO-DQ-READ-PURITY", EnduranceCampaignType.DASHBOARD_READ_ONLY_LOAD, repository_commit, allow_dirty_worktree),
            self._definition("EO-DQ-RECOVERY", EnduranceCampaignType.RECOVERY_ENDURANCE, repository_commit, allow_dirty_worktree),
        )
        environment = self._environment(repository_commit)
        reports = tuple(self.lab.run_campaign(definition, environment) for definition in campaigns)
        violations = tuple(f"{report.campaign_id}:{finding.finding_id}" for report in reports for finding in report.critical_findings)
        passing = sum(1 for report in reports if report.verdict == EnduranceVerdict.PASS)
        verdict = PaperEnduranceVerdict.PASS if passing == len(reports) and not violations else PaperEnduranceVerdict.FAIL
        report_dicts = tuple(_jsonable(asdict(report)) for report in reports)
        return PaperEnduranceCertification(
            verdict=verdict,
            mode="ACCELERATED_EVENT_TIME",
            campaign_count=len(reports),
            passing_campaign_count=passing,
            longest_uninterrupted_duration_seconds=max(report.longest_uninterrupted_duration_seconds for report in reports),
            cumulative_duration_seconds=sum(report.cumulative_segmented_duration_seconds for report in reports),
            wall_clock_extended_run_completed=False,
            accelerated_endurance_completed=True,
            live_trading_enabled=False,
            invariant_violations=violations,
            reports=report_dicts,
            evidence_hash=_stable_hash(report_dicts),
            timestamp_utc=utc_timestamp(),
        )

    def _definition(self, campaign_id: str, campaign_type: EnduranceCampaignType, repository_commit: str, allow_dirty: bool) -> CampaignDefinition:
        return CampaignDefinition(
            campaign_id=campaign_id,
            campaign_type=campaign_type,
            stage=EnduranceStage.STAGE_1_ACCELERATED_24H,
            duration_mode=DurationMode.ACCELERATED_EVENT_TIME,
            intended_duration_seconds=120,
            accelerated_event_seconds=86400,
            segment_target_count=2,
            metric_interval_seconds=30,
            repository_commit=repository_commit,
            configuration_hash="EO-DQ-CONTROLLED-CONFIG",
            policy_version="POLICY-EO-DQ",
            doctrine_version="DOCTRINE-EO-DQ",
            truth_domain="PAPER",
            fixture_version="EO-DQ-FIXTURE-1",
            deterministic_seed=f"{campaign_id}-stable",
            runtime_mode="paper",
            expected_workload=campaign_type.value,
            pass_criteria=EndurancePassCriteria(max_thread_growth=1),
            evidence_root="Documentation/EO-DQ_Evidence",
            allow_dirty_worktree=allow_dirty,
            live_trading_enabled=False,
        )

    def _environment(self, repository_commit: str) -> AdmissionEnvironment:
        return AdmissionEnvironment(
            branch="main",
            full_commit_sha=repository_commit,
            git_status="",
            python_version=platform.python_version(),
            node_version="not required",
            operating_system=platform.platform(),
            persistence_backend="in-memory deterministic evidence",
            runtime_configuration="paper",
            truth_domain_configuration="PAPER",
            policy_version="POLICY-EO-DQ",
            doctrine_version="DOCTRINE-EO-DQ",
            active_paper_broker="DeterministicPaperBrokerage",
            live_trading_enabled=False,
            available_hardware_resources={"profile": "local bounded certification"},
            expected_campaign_environment="accelerated deterministic lab",
            existing_resource_limits={"apiCalls": 0, "cost": 0.0},
        )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_jsonable(item) for item in value)
    return value
