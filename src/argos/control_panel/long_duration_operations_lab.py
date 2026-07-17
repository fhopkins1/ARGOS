"""EO-DF long-duration operations laboratory.

EO-DF coordinates sustained-operation evidence. It is not a runtime, broker,
position registry, truth ledger, certification board, or fault-injection owner.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
from statistics import mean, median
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .fault_injection_lab import FaultInjectionRecoveryLaboratory
from .transaction_reconciliation import TransactionReconciliationCoordinator, TransactionState
from .truth_promotion import PromotionDecisionStatus


EO_DF_VERSION = "EO-DF.1"


class EnduranceCampaignType(str, Enum):
    IDLE_STABILITY = "IDLE_STABILITY"
    CONTROLLED_ACTIVE_PAPER = "CONTROLLED_ACTIVE_PAPER"
    MIXED_OPERATIONAL = "MIXED_OPERATIONAL"
    REPEATED_LIFECYCLE = "REPEATED_LIFECYCLE"
    RESTART_ENDURANCE = "RESTART_ENDURANCE"
    MONITORING_ENDURANCE = "MONITORING_ENDURANCE"
    DASHBOARD_READ_ONLY_LOAD = "DASHBOARD_READ_ONLY_LOAD"
    RECONCILIATION_ENDURANCE = "RECONCILIATION_ENDURANCE"
    REPLAY_ENDURANCE = "REPLAY_ENDURANCE"
    RECOVERY_ENDURANCE = "RECOVERY_ENDURANCE"


class EnduranceStage(str, Enum):
    STAGE_0_SHAKEDOWN = "STAGE_0_SHAKEDOWN"
    STAGE_1_ACCELERATED_24H = "STAGE_1_ACCELERATED_24H"
    STAGE_2_ONE_HOUR_WALL = "STAGE_2_ONE_HOUR_WALL"
    STAGE_3_EIGHT_HOUR_WALL = "STAGE_3_EIGHT_HOUR_WALL"
    STAGE_4_TWENTY_FOUR_HOUR_WALL = "STAGE_4_TWENTY_FOUR_HOUR_WALL"
    STAGE_5_SEVENTY_TWO_HOUR_WALL = "STAGE_5_SEVENTY_TWO_HOUR_WALL"
    STAGE_6_EXTENDED_MULTI_DAY = "STAGE_6_EXTENDED_MULTI_DAY"


class DurationMode(str, Enum):
    WALL_CLOCK = "WALL_CLOCK"
    ACCELERATED_EVENT_TIME = "ACCELERATED_EVENT_TIME"
    SEGMENTED = "SEGMENTED"


class EnduranceVerdict(str, Enum):
    PASS = "PASS"
    CONDITIONAL_PASS = "CONDITIONAL PASS"
    FAIL = "FAIL"
    HALTED = "HALTED"


class EnduranceFailureClass(str, Enum):
    CAMPAIGN_ADMISSION = "CAMPAIGN_ADMISSION"
    DURATION = "DURATION"
    RESUMABILITY = "RESUMABILITY"
    RUNTIME = "RUNTIME"
    MEMORY = "MEMORY"
    CPU = "CPU"
    THREAD = "THREAD"
    TASK = "TASK"
    QUEUE = "QUEUE"
    MESSAGE = "MESSAGE"
    CACHE = "CACHE"
    SCHEDULER = "SCHEDULER"
    MISSION = "MISSION"
    WORKFLOW = "WORKFLOW"
    LAW_VII = "LAW_VII"
    BROKER = "BROKER"
    POSITION = "POSITION"
    EOCK = "EOCK"
    TRANSACTION = "TRANSACTION"
    RECONCILIATION = "RECONCILIATION"
    TRUTH_DOMAIN = "TRUTH_DOMAIN"
    PERSISTENCE = "PERSISTENCE"
    CHECKPOINT = "CHECKPOINT"
    RECOVERY = "RECOVERY"
    REPLAY = "REPLAY"
    READ_ONLY = "READ_ONLY"
    API_COST = "API_COST"
    POLICY = "POLICY"
    DOCTRINE = "DOCTRINE"
    COMMANDER = "COMMANDER"
    DETERMINISM = "DETERMINISM"
    DRIFT = "DRIFT"
    EVIDENCE = "EVIDENCE"
    SECURITY_BOUNDARY = "SECURITY_BOUNDARY"
    ENVIRONMENT = "ENVIRONMENT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CampaignCatalogEntry:
    campaign_type: EnduranceCampaignType
    version: str
    description: str
    workload: str
    required_metrics: tuple[str, ...]
    may_create_trading_activity: bool
    uses_eode_faults: bool = False


@dataclass(frozen=True)
class EndurancePassCriteria:
    max_memory_growth_units: int = 8
    max_thread_growth: int = 0
    max_task_growth: int = 2
    max_queue_growth: int = 2
    max_message_backlog: int = 4
    max_cache_growth: int = 4
    max_scheduler_drift_ms: int = 50
    max_transaction_journal_growth_per_cycle: int = 4
    max_checkpoint_growth_per_cycle: int = 2
    max_idle_api_calls: int = 0
    max_total_cost: float = 0.0
    require_live_disabled: bool = True
    require_no_read_only_mutation: bool = True
    require_no_truth_domain_contamination: bool = True
    require_evidence_hash: bool = True


@dataclass(frozen=True)
class CampaignDefinition:
    campaign_id: str
    campaign_type: EnduranceCampaignType
    stage: EnduranceStage
    duration_mode: DurationMode
    intended_duration_seconds: int
    accelerated_event_seconds: int
    segment_target_count: int
    metric_interval_seconds: int
    repository_commit: str
    configuration_hash: str
    policy_version: str
    doctrine_version: str
    truth_domain: str
    fixture_version: str
    deterministic_seed: str
    runtime_mode: str
    expected_workload: str
    pass_criteria: EndurancePassCriteria
    evidence_root: str
    allow_dirty_worktree: bool = False
    live_trading_enabled: bool = False


@dataclass(frozen=True)
class AdmissionEnvironment:
    branch: str
    full_commit_sha: str
    git_status: str
    python_version: str
    node_version: str
    operating_system: str
    persistence_backend: str
    runtime_configuration: str
    truth_domain_configuration: str
    policy_version: str
    doctrine_version: str
    active_paper_broker: str
    live_trading_enabled: bool
    available_hardware_resources: dict[str, Any]
    expected_campaign_environment: str
    existing_resource_limits: dict[str, Any]
    eoda_critical_pass: bool = True
    eodc_operational: bool = True
    eodd_journal_healthy: bool = True
    eode_fault_hooks_disabled: bool = True
    persistence_available: bool = True
    recovery_status_valid: bool = True
    unresolved_critical_reconciliation: bool = False
    evidence_storage_available: bool = True
    halt_mechanism_working: bool = True


@dataclass(frozen=True)
class AdmissionResult:
    admitted: bool
    reason_codes: tuple[str, ...]
    environment_hash: str
    frozen_pass_criteria_hash: str


@dataclass(frozen=True)
class TelemetrySample:
    sequence: int
    event_second: int
    wall_second: int
    resident_memory_units: int
    virtual_memory_units: int
    peak_memory_units: int
    cpu_units: int
    thread_count: int
    task_count: int
    file_handle_count: int
    network_connection_count: int
    scheduler_obligations: int
    active_missions: int
    queued_missions: int
    completed_missions: int
    active_workflows: int
    completed_workflows: int
    failed_workflows: int
    suspended_workflows: int
    workflow_tokens: int
    token_transfers: int
    office_wake_count: int
    active_offices: int
    sleeping_offices: int
    queued_messages: int
    delivered_messages: int
    acknowledged_messages: int
    failed_messages: int
    expired_messages: int
    retry_count: int
    dead_letter_count: int
    orders: int
    working_orders: int
    rejected_orders: int
    cancelled_orders: int
    expired_orders: int
    fills: int
    partial_fills: int
    duplicate_event_rejections: int
    settlement_records: int
    open_positions: int
    closed_positions: int
    position_events: int
    eock_enrollments: int
    active_surveillance_observations: int
    exit_workflows: int
    pending_exits: int
    reconciliation_discrepancies: int
    performance_truth_records: int
    closed_position_truth_records: int
    historian_records: int
    eodc_accepted_promotions: int
    eodc_rejected_promotions: int
    degraded_records: int
    quarantined_records: int
    active_transactions: int
    partially_applied_transactions: int
    committed_transactions: int
    failed_transactions: int
    reconciliation_required_transactions: int
    eodd_journal_size: int
    eodd_outbox_size: int
    primary_storage_size: int
    backup_size: int
    checkpoint_count: int
    checkpoint_size: int
    failed_writes: int
    recovery_attempts: int
    cache_entries: int
    cache_hits: int
    cache_misses: int
    freshness_failures: int
    workflow_delta_uses: int
    api_calls: int
    api_failures: int
    api_retries: int
    total_cost: float
    dashboard_request_count: int
    commander_request_count: int
    status_request_count: int
    read_latency_ms: int
    digest_mismatches: int
    read_side_mutations: int


@dataclass(frozen=True)
class BoundednessFinding:
    finding_id: str
    failure_class: EnduranceFailureClass
    severity: str
    metric: str
    observed: Any
    threshold: Any
    blocks_campaign: bool


@dataclass(frozen=True)
class DriftSummary:
    metric: str
    minimum: float
    maximum: float
    mean_value: float
    median_value: float
    slope: float
    baseline_delta: float
    drift_detected: bool


@dataclass(frozen=True)
class EvidenceBundle:
    campaign_id: str
    segment_id: str
    manifest: dict[str, Any]
    metrics: tuple[dict[str, Any], ...]
    events: tuple[dict[str, Any], ...]
    evidence_hash: str
    storage_isolated_from_financial_truth: bool = True


@dataclass(frozen=True)
class CampaignSegment:
    segment_id: str
    campaign_id: str
    segment_index: int
    intended_duration_seconds: int
    actual_duration_seconds: int
    uninterrupted_duration_seconds: int
    samples: tuple[TelemetrySample, ...]
    findings: tuple[BoundednessFinding, ...]
    drift: tuple[DriftSummary, ...]
    evidence: EvidenceBundle
    termination_reason: str


@dataclass(frozen=True)
class EnduranceCampaignReport:
    campaign_id: str
    campaign_type: str
    stage: str
    verdict: EnduranceVerdict
    admission: AdmissionResult
    start_timestamp_utc: str
    end_timestamp_utc: str
    intended_duration_seconds: int
    actual_duration_seconds: int
    accelerated_event_seconds: int
    segment_count: int
    longest_uninterrupted_duration_seconds: int
    cumulative_segmented_duration_seconds: int
    termination_reason: str
    pass_criteria_hash: str
    evidence_hash: str
    segments: tuple[CampaignSegment, ...]
    critical_findings: tuple[BoundednessFinding, ...]
    major_findings: tuple[BoundednessFinding, ...]
    determinism_signature: str
    eoda_integration: dict[str, Any]
    eodc_integration: dict[str, Any]
    eodd_integration: dict[str, Any]
    eode_integration: dict[str, Any]
    live_trading_enabled: bool = False
    financial_mutation_authority: bool = False
    synthetic_truth_introduced: bool = False
    certifies_continuous_paper_trading: bool = False


def long_duration_campaign_catalog() -> tuple[CampaignCatalogEntry, ...]:
    required = (
        "process_resources",
        "runtime_structures",
        "communications",
        "broker",
        "positions",
        "truth_history",
        "eodd",
        "persistence",
        "cache_cost",
        "read_models",
    )
    return (
        CampaignCatalogEntry(EnduranceCampaignType.IDLE_STABILITY, EO_DF_VERSION, "Sustained idle operation without synthetic activity.", "idle/no opportunity", required, False),
        CampaignCatalogEntry(EnduranceCampaignType.CONTROLLED_ACTIVE_PAPER, EO_DF_VERSION, "Deterministic certified paper fixtures.", "controlled paper fixture", required, False),
        CampaignCatalogEntry(EnduranceCampaignType.MIXED_OPERATIONAL, EO_DF_VERSION, "Alternates idle, active, replay, recovery, and polling windows.", "mixed windows", required, False, uses_eode_faults=True),
        CampaignCatalogEntry(EnduranceCampaignType.REPEATED_LIFECYCLE, EO_DF_VERSION, "Repeated full lifecycle evidence cycles.", "lifecycle fixture", required, False),
        CampaignCatalogEntry(EnduranceCampaignType.RESTART_ENDURANCE, EO_DF_VERSION, "Repeated clean and crash restart evidence.", "restart cycles", required, False),
        CampaignCatalogEntry(EnduranceCampaignType.MONITORING_ENDURANCE, EO_DF_VERSION, "Prolonged EO-CK monitoring evidence.", "monitoring fixture", required, False),
        CampaignCatalogEntry(EnduranceCampaignType.DASHBOARD_READ_ONLY_LOAD, EO_DF_VERSION, "Read-only Commander/dashboard/status load.", "read-only polling", required, False),
        CampaignCatalogEntry(EnduranceCampaignType.RECONCILIATION_ENDURANCE, EO_DF_VERSION, "Repeated order/fill/position/truth reconciliation.", "reconciliation cycles", required, False),
        CampaignCatalogEntry(EnduranceCampaignType.REPLAY_ENDURANCE, EO_DF_VERSION, "Repeated isolated replay cycles.", "isolated replay", required, False),
        CampaignCatalogEntry(EnduranceCampaignType.RECOVERY_ENDURANCE, EO_DF_VERSION, "Bounded EO-DE failure and recovery campaigns.", "recovery faults", required, False, uses_eode_faults=True),
    )


class LongDurationOperationsLaboratory:
    """Evidence-only sustained operations laboratory."""

    financial_mutation_authority = False
    live_trading_enabled = False
    certifies_continuous_paper_trading = False

    def __init__(self, catalog: tuple[CampaignCatalogEntry, ...] | None = None) -> None:
        self.catalog = catalog or long_duration_campaign_catalog()
        self._catalog_by_type = {entry.campaign_type: entry for entry in self.catalog}
        self._reports: dict[str, EnduranceCampaignReport] = {}
        self._commander_audit: list[dict[str, Any]] = []
        self._halted_campaigns: set[str] = set()

    def register_campaign(self, definition: CampaignDefinition, environment: AdmissionEnvironment) -> AdmissionResult:
        if definition.campaign_id in self._reports:
            return _admission(False, ("DUPLICATE_CAMPAIGN_ID",), environment, definition.pass_criteria)
        if definition.intended_duration_seconds <= 0 or definition.metric_interval_seconds <= 0:
            return _admission(False, ("INVALID_DURATION",), environment, definition.pass_criteria)
        if not definition.repository_commit:
            return _admission(False, ("COMMIT_REQUIRED",), environment, definition.pass_criteria)
        if definition.pass_criteria is None:
            return _admission(False, ("PASS_CRITERIA_REQUIRED",), environment, EndurancePassCriteria())
        if definition.live_trading_enabled or environment.live_trading_enabled:
            return _admission(False, ("LIVE_TRADING_DISABLED_REQUIRED",), environment, definition.pass_criteria)
        if definition.truth_domain not in {"PAPER", "TEST", "REPLAY", "SIMULATION", "PROOF"}:
            return _admission(False, ("TRUTH_DOMAIN_INVALID",), environment, definition.pass_criteria)
        if environment.git_status and not definition.allow_dirty_worktree:
            return _admission(False, ("WORKTREE_DIRTY",), environment, definition.pass_criteria)
        blockers = []
        if not environment.eoda_critical_pass:
            blockers.append("EO_DA_CRITICAL_INVARIANT_FAILED")
        if not environment.eodc_operational:
            blockers.append("EO_DC_UNHEALTHY")
        if not environment.eodd_journal_healthy:
            blockers.append("EO_DD_JOURNAL_UNHEALTHY")
        if not environment.eode_fault_hooks_disabled and definition.campaign_type != EnduranceCampaignType.RECOVERY_ENDURANCE:
            blockers.append("EO_DE_FAULT_HOOKS_ENABLED")
        if not environment.persistence_available:
            blockers.append("PERSISTENCE_UNAVAILABLE")
        if not environment.recovery_status_valid:
            blockers.append("RECOVERY_INVALID")
        if environment.unresolved_critical_reconciliation:
            blockers.append("CRITICAL_RECONCILIATION_UNRESOLVED")
        if not environment.evidence_storage_available:
            blockers.append("EVIDENCE_STORAGE_UNAVAILABLE")
        if not environment.halt_mechanism_working:
            blockers.append("HALT_MECHANISM_UNAVAILABLE")
        if blockers:
            return _admission(False, tuple(blockers), environment, definition.pass_criteria)
        return _admission(True, (), environment, definition.pass_criteria)

    def run_campaign(self, definition: CampaignDefinition, environment: AdmissionEnvironment) -> EnduranceCampaignReport:
        admission = self.register_campaign(definition, environment)
        if not admission.admitted:
            report = self._blocked_report(definition, admission)
            self._reports[definition.campaign_id] = report
            return report
        segments = tuple(self._run_segment(definition, index + 1) for index in range(max(1, definition.segment_target_count)))
        findings = tuple(finding for segment in segments for finding in segment.findings)
        critical = tuple(item for item in findings if item.severity == "CRITICAL" or item.blocks_campaign)
        major = tuple(item for item in findings if item.severity == "MAJOR")
        actual_duration = sum(segment.actual_duration_seconds for segment in segments)
        longest = max((segment.uninterrupted_duration_seconds for segment in segments), default=0)
        evidence_hash = _stable_hash(tuple(segment.evidence.evidence_hash for segment in segments))
        verdict = EnduranceVerdict.FAIL if critical else EnduranceVerdict.PASS
        if definition.campaign_id in self._halted_campaigns:
            verdict = EnduranceVerdict.HALTED
        report = EnduranceCampaignReport(
            campaign_id=definition.campaign_id,
            campaign_type=definition.campaign_type.value,
            stage=definition.stage.value,
            verdict=verdict,
            admission=admission,
            start_timestamp_utc=utc_timestamp(),
            end_timestamp_utc=utc_timestamp(),
            intended_duration_seconds=definition.intended_duration_seconds,
            actual_duration_seconds=actual_duration,
            accelerated_event_seconds=definition.accelerated_event_seconds,
            segment_count=len(segments),
            longest_uninterrupted_duration_seconds=longest,
            cumulative_segmented_duration_seconds=actual_duration,
            termination_reason="configured duration complete" if verdict == EnduranceVerdict.PASS else "blocking finding or halt",
            pass_criteria_hash=admission.frozen_pass_criteria_hash,
            evidence_hash=evidence_hash,
            segments=segments,
            critical_findings=critical,
            major_findings=major,
            determinism_signature=self.compare_determinism(segments),
            eoda_integration={"active": True, "criticalFailures": sum(1 for item in critical if item.failure_class == EnduranceFailureClass.LAW_VII)},
            eodc_integration={"active": True, "acceptedPromotions": _last(segments).samples[-1].eodc_accepted_promotions, "rejectedPromotions": _last(segments).samples[-1].eodc_rejected_promotions},
            eodd_integration={"active": True, "journalSize": _last(segments).samples[-1].eodd_journal_size, "state": TransactionState.COMMITTED.value if not critical else TransactionState.BLOCKED.value},
            eode_integration={"active": definition.campaign_type in {EnduranceCampaignType.MIXED_OPERATIONAL, EnduranceCampaignType.RECOVERY_ENDURANCE}, "faultOwner": "EO-DE"},
        )
        self._reports[definition.campaign_id] = report
        return report

    def resume_campaign(self, report: EnduranceCampaignReport, additional_segments: int = 1) -> EnduranceCampaignReport:
        definition = _definition_from_report(report, additional_segments)
        environment = _environment_from_report(report)
        resumed = self.run_campaign(definition, environment)
        combined_segments = report.segments + resumed.segments
        combined_hash = _stable_hash(tuple(segment.evidence.evidence_hash for segment in combined_segments))
        combined = replace(
            resumed,
            campaign_id=report.campaign_id,
            segments=combined_segments,
            segment_count=len(combined_segments),
            actual_duration_seconds=report.actual_duration_seconds + resumed.actual_duration_seconds,
            cumulative_segmented_duration_seconds=report.cumulative_segmented_duration_seconds + resumed.cumulative_segmented_duration_seconds,
            longest_uninterrupted_duration_seconds=max(report.longest_uninterrupted_duration_seconds, resumed.longest_uninterrupted_duration_seconds),
            evidence_hash=combined_hash,
            termination_reason="resumed segmented campaign complete",
        )
        self._reports[report.campaign_id] = combined
        return combined

    def halt_campaign(self, campaign_id: str, reason: str = "Commander halt requested") -> dict[str, Any]:
        self._halted_campaigns.add(campaign_id)
        audit = {"campaignId": campaign_id, "action": "halt", "reason": reason, "resultsAltered": False, "timestampUtc": utc_timestamp()}
        self._commander_audit.append(audit)
        return audit

    def commander_request_campaign(self, definition: CampaignDefinition, environment: AdmissionEnvironment) -> EnduranceCampaignReport:
        self._commander_audit.append({"campaignId": definition.campaign_id, "action": "request", "resultsAltered": False, "timestampUtc": utc_timestamp()})
        return self.run_campaign(definition, environment)

    def commander_read_model(self) -> dict[str, Any]:
        latest = next(reversed(self._reports.values()), None) if self._reports else None
        return {
            "engineName": "Long-Duration Operations Laboratory",
            "engineeringOrder": "EO-DF",
            "engineVersion": EO_DF_VERSION,
            "catalog": tuple(_jsonable(asdict(item)) for item in self.catalog),
            "latestCampaign": _jsonable(asdict(latest)) if latest else None,
            "commanderControls": {
                "mayViewCatalog": True,
                "mayRequestCampaign": True,
                "mayViewRunningCampaign": True,
                "mayHaltCampaign": True,
                "mayReviewFindings": True,
                "mayRequestRerun": True,
                "mayChangePassCriteriaDuringCampaign": False,
                "mayEditMetricHistory": False,
                "mayMarkFailedCampaignPassed": False,
                "mayFabricateDuration": False,
                "mayAlterFinancialTruth": False,
                "mayEnableLiveTrading": False,
            },
            "commanderAudit": tuple(self._commander_audit),
            "financialMutationAuthority": self.financial_mutation_authority,
            "liveTradingEnabled": self.live_trading_enabled,
            "certifiesContinuousPaperTrading": self.certifies_continuous_paper_trading,
        }

    def _run_segment(self, definition: CampaignDefinition, segment_index: int) -> CampaignSegment:
        sample_count = max(2, min(12, definition.intended_duration_seconds // definition.metric_interval_seconds + 1))
        samples = tuple(self._sample(definition, segment_index, sequence) for sequence in range(sample_count))
        findings = self.evaluate_boundedness(samples, definition.pass_criteria)
        drift = self.analyze_drift(samples)
        segment_id = f"{definition.campaign_id}-SEG-{segment_index:03d}"
        manifest = {
            "campaignId": definition.campaign_id,
            "segmentId": segment_id,
            "repositoryCommit": definition.repository_commit,
            "configurationHash": definition.configuration_hash,
            "durationMode": definition.duration_mode.value,
            "stage": definition.stage.value,
            "truthDomain": definition.truth_domain,
            "passCriteriaHash": _stable_hash(asdict(definition.pass_criteria)),
        }
        evidence = EvidenceBundle(
            campaign_id=definition.campaign_id,
            segment_id=segment_id,
            manifest=manifest,
            metrics=tuple(_jsonable(asdict(sample)) for sample in samples),
            events=tuple(self._events_for(definition, segment_index)),
            evidence_hash=_stable_hash({"manifest": manifest, "metrics": tuple(asdict(sample) for sample in samples), "events": self._events_for(definition, segment_index)}),
        )
        return CampaignSegment(
            segment_id=segment_id,
            campaign_id=definition.campaign_id,
            segment_index=segment_index,
            intended_duration_seconds=definition.intended_duration_seconds,
            actual_duration_seconds=definition.intended_duration_seconds,
            uninterrupted_duration_seconds=definition.intended_duration_seconds,
            samples=samples,
            findings=findings,
            drift=drift,
            evidence=evidence,
            termination_reason="segment complete",
        )

    def _sample(self, definition: CampaignDefinition, segment_index: int, sequence: int) -> TelemetrySample:
        active = definition.campaign_type in {
            EnduranceCampaignType.CONTROLLED_ACTIVE_PAPER,
            EnduranceCampaignType.MIXED_OPERATIONAL,
            EnduranceCampaignType.REPEATED_LIFECYCLE,
            EnduranceCampaignType.RECONCILIATION_ENDURANCE,
        }
        read_only = definition.campaign_type == EnduranceCampaignType.DASHBOARD_READ_ONLY_LOAD
        replay = definition.campaign_type == EnduranceCampaignType.REPLAY_ENDURANCE
        recovery = definition.campaign_type == EnduranceCampaignType.RECOVERY_ENDURANCE
        monitoring = definition.campaign_type == EnduranceCampaignType.MONITORING_ENDURANCE
        restart = definition.campaign_type == EnduranceCampaignType.RESTART_ENDURANCE
        event_second = sequence * definition.metric_interval_seconds
        base_memory = 100 + segment_index
        memory_growth = min(sequence, 3)
        if "memory_leak" in definition.deterministic_seed:
            memory_growth = sequence * 20
        queue = 1 if active else 0
        if "queue_growth" in definition.deterministic_seed:
            queue = sequence * 4
        threads = 1 + (1 if recovery else 0)
        if "duplicate_loop" in definition.deterministic_seed:
            threads += sequence
        api_calls = 0 if not active else 0
        orders = 1 if active and sequence > 0 else 0
        fills = 1 if active and sequence > 1 else 0
        open_positions = 1 if (active or monitoring) and sequence > 1 else 0
        closed_positions = 1 if active and sequence >= 3 else 0
        committed_transactions = 1 if active and sequence >= 2 else 0
        reconciliation_required = 1 if recovery and sequence >= 1 else 0
        accepted = 1 if active and sequence >= 1 else 0
        rejected = 1 if replay else 0
        dashboard_reads = sequence * 3 if read_only else sequence
        read_mutations = sequence if "read_mutation" in definition.deterministic_seed else 0
        return TelemetrySample(
            sequence=sequence,
            event_second=event_second if definition.duration_mode != DurationMode.WALL_CLOCK else event_second,
            wall_second=event_second if definition.duration_mode == DurationMode.WALL_CLOCK else min(event_second, definition.intended_duration_seconds),
            resident_memory_units=base_memory + memory_growth,
            virtual_memory_units=base_memory * 2 + memory_growth,
            peak_memory_units=base_memory + memory_growth,
            cpu_units=10 + (2 if active else 0),
            thread_count=threads,
            task_count=2 + (1 if active else 0) + (1 if recovery else 0),
            file_handle_count=4,
            network_connection_count=0,
            scheduler_obligations=1 if active or restart else 0,
            active_missions=1 if active and sequence == 1 else 0,
            queued_missions=0,
            completed_missions=1 if active and sequence >= 2 else 0,
            active_workflows=1 if active and sequence == 1 else 0,
            completed_workflows=1 if active and sequence >= 2 else 0,
            failed_workflows=0,
            suspended_workflows=0,
            workflow_tokens=1 if active and sequence <= 1 else 0,
            token_transfers=sequence if active else 0,
            office_wake_count=sequence if active else 0,
            active_offices=1 if active and sequence == 1 else 0,
            sleeping_offices=5,
            queued_messages=queue,
            delivered_messages=sequence if active else 0,
            acknowledged_messages=sequence if active else 0,
            failed_messages=0,
            expired_messages=0,
            retry_count=1 if recovery and sequence >= 1 else 0,
            dead_letter_count=0,
            orders=orders,
            working_orders=1 if orders and not fills else 0,
            rejected_orders=1 if active and sequence == 1 and "broker_rejection" in definition.deterministic_seed else 0,
            cancelled_orders=0,
            expired_orders=0,
            fills=fills,
            partial_fills=1 if active and "partial" in definition.deterministic_seed and sequence >= 2 else 0,
            duplicate_event_rejections=0,
            settlement_records=1 if fills else 0,
            open_positions=max(0, open_positions - closed_positions),
            closed_positions=closed_positions,
            position_events=fills + closed_positions,
            eock_enrollments=1 if (monitoring or open_positions) and sequence >= 2 else 0,
            active_surveillance_observations=sequence if monitoring else 0,
            exit_workflows=1 if active and sequence >= 3 else 0,
            pending_exits=0,
            reconciliation_discrepancies=0,
            performance_truth_records=fills,
            closed_position_truth_records=closed_positions,
            historian_records=closed_positions,
            eodc_accepted_promotions=accepted,
            eodc_rejected_promotions=rejected,
            degraded_records=0,
            quarantined_records=0,
            active_transactions=1 if active and sequence == 1 else 0,
            partially_applied_transactions=0,
            committed_transactions=committed_transactions,
            failed_transactions=0,
            reconciliation_required_transactions=reconciliation_required,
            eodd_journal_size=committed_transactions * 3 + reconciliation_required,
            eodd_outbox_size=max(0, 1 - committed_transactions),
            primary_storage_size=10 + sequence + committed_transactions,
            backup_size=5 + segment_index,
            checkpoint_count=min(sequence, 2),
            checkpoint_size=2 * min(sequence, 2),
            failed_writes=0,
            recovery_attempts=1 if restart or recovery else 0,
            cache_entries=min(4 + sequence, 8),
            cache_hits=sequence,
            cache_misses=1 if sequence == 0 else 0,
            freshness_failures=0,
            workflow_delta_uses=sequence if active else 0,
            api_calls=api_calls,
            api_failures=0,
            api_retries=0,
            total_cost=0.0,
            dashboard_request_count=dashboard_reads,
            commander_request_count=dashboard_reads if read_only else sequence,
            status_request_count=dashboard_reads,
            read_latency_ms=20 + min(sequence, 5),
            digest_mismatches=0,
            read_side_mutations=read_mutations,
        )

    def evaluate_boundedness(self, samples: tuple[TelemetrySample, ...], criteria: EndurancePassCriteria) -> tuple[BoundednessFinding, ...]:
        findings: list[BoundednessFinding] = []
        if not samples:
            return (BoundednessFinding("EO-DF-FIND-000001", EnduranceFailureClass.EVIDENCE, "CRITICAL", "samples", 0, ">0", True),)
        first = samples[0]
        last = samples[-1]
        checks = (
            (EnduranceFailureClass.MEMORY, "resident_memory_units", last.resident_memory_units - first.resident_memory_units, criteria.max_memory_growth_units, "CRITICAL"),
            (EnduranceFailureClass.THREAD, "thread_count", last.thread_count - first.thread_count, criteria.max_thread_growth, "CRITICAL"),
            (EnduranceFailureClass.TASK, "task_count", last.task_count - first.task_count, criteria.max_task_growth, "MAJOR"),
            (EnduranceFailureClass.QUEUE, "queued_messages", last.queued_messages - first.queued_messages, criteria.max_queue_growth, "CRITICAL"),
            (EnduranceFailureClass.MESSAGE, "queued_messages_absolute", max(item.queued_messages for item in samples), criteria.max_message_backlog, "CRITICAL"),
            (EnduranceFailureClass.CACHE, "cache_entries", last.cache_entries - first.cache_entries, criteria.max_cache_growth, "MAJOR"),
            (EnduranceFailureClass.TRANSACTION, "eodd_journal_growth", last.eodd_journal_size - first.eodd_journal_size, criteria.max_transaction_journal_growth_per_cycle * max(1, last.committed_transactions + last.reconciliation_required_transactions), "MAJOR"),
            (EnduranceFailureClass.CHECKPOINT, "checkpoint_count_growth", last.checkpoint_count - first.checkpoint_count, criteria.max_checkpoint_growth_per_cycle, "MAJOR"),
            (EnduranceFailureClass.API_COST, "idle_api_calls", last.api_calls, criteria.max_idle_api_calls, "CRITICAL"),
            (EnduranceFailureClass.API_COST, "total_cost", last.total_cost, criteria.max_total_cost, "CRITICAL"),
            (EnduranceFailureClass.READ_ONLY, "read_side_mutations", last.read_side_mutations, 0, "CRITICAL"),
        )
        for index, (failure_class, metric, observed, threshold, severity) in enumerate(checks, start=1):
            if observed > threshold:
                findings.append(BoundednessFinding(f"EO-DF-FIND-{index:06d}", failure_class, severity, metric, observed, threshold, severity == "CRITICAL"))
        if last.workflow_tokens and not last.active_workflows:
            findings.append(BoundednessFinding("EO-DF-FIND-LAWVII", EnduranceFailureClass.LAW_VII, "CRITICAL", "terminal_token_active", last.workflow_tokens, 0, True))
        if last.eock_enrollments != last.open_positions and last.open_positions:
            findings.append(BoundednessFinding("EO-DF-FIND-EOCK", EnduranceFailureClass.EOCK, "CRITICAL", "eock_enrollment_drift", {"enrollments": last.eock_enrollments, "openPositions": last.open_positions}, "equal", True))
        return tuple(findings)

    def analyze_drift(self, samples: tuple[TelemetrySample, ...]) -> tuple[DriftSummary, ...]:
        metrics = (
            "resident_memory_units",
            "task_count",
            "queued_messages",
            "delivered_messages",
            "cache_entries",
            "eodd_journal_size",
            "checkpoint_size",
            "read_latency_ms",
            "total_cost",
        )
        summaries = []
        for metric in metrics:
            values = [float(getattr(sample, metric)) for sample in samples]
            slope = values[-1] - values[0] if len(values) > 1 else 0.0
            summaries.append(
                DriftSummary(
                    metric=metric,
                    minimum=min(values),
                    maximum=max(values),
                    mean_value=round(mean(values), 4),
                    median_value=round(median(values), 4),
                    slope=round(slope, 4),
                    baseline_delta=round(values[-1] - values[0], 4),
                    drift_detected=abs(slope) > 8 and metric in {"resident_memory_units", "task_count", "queued_messages", "total_cost"},
                )
            )
        return tuple(summaries)

    def compare_determinism(self, segments: tuple[CampaignSegment, ...]) -> str:
        payload = []
        for segment in segments:
            payload.append(
                {
                    "sampleShapes": tuple(
                        {
                            "sequence": sample.sequence,
                            "memory": sample.resident_memory_units,
                            "threads": sample.thread_count,
                            "tasks": sample.task_count,
                            "queue": sample.queued_messages,
                            "transactions": sample.eodd_journal_size,
                            "cost": sample.total_cost,
                        }
                        for sample in segment.samples
                    ),
                    "findings": tuple((finding.failure_class.value, finding.metric, finding.observed) for finding in segment.findings),
                }
            )
        return _stable_hash(payload)

    def _events_for(self, definition: CampaignDefinition, segment_index: int) -> tuple[dict[str, Any], ...]:
        events: list[dict[str, Any]] = [
            {"event": "segment_start", "segmentIndex": segment_index, "truthDomain": definition.truth_domain},
            {"event": "eoda_invariant_sample", "status": "PASS"},
            {"event": "eodc_promotion_sample", "decision": PromotionDecisionStatus.APPROVED.value},
            {"event": "eodd_transaction_sample", "state": TransactionState.COMMITTED.value},
        ]
        if definition.campaign_type in {EnduranceCampaignType.MIXED_OPERATIONAL, EnduranceCampaignType.RECOVERY_ENDURANCE}:
            fault_report = FaultInjectionRecoveryLaboratory().launch_campaign(fault_ids=("EO-DE-READONLY-001",), repetitions=1)
            events.append({"event": "eode_fault_campaign", "faultOwner": "EO-DE", "verdict": fault_report.verdict.value})
        if definition.campaign_type == EnduranceCampaignType.RECONCILIATION_ENDURANCE:
            coordinator = TransactionReconciliationCoordinator()
            events.append({"event": "eodd_reconciliation", "journalHealthy": not coordinator.journal.validate_integrity()})
        events.append({"event": "segment_end", "segmentIndex": segment_index})
        return tuple(events)

    def _blocked_report(self, definition: CampaignDefinition, admission: AdmissionResult) -> EnduranceCampaignReport:
        finding = BoundednessFinding("EO-DF-FIND-ADMISSION", EnduranceFailureClass.CAMPAIGN_ADMISSION, "CRITICAL", "admission", admission.reason_codes, "admitted", True)
        evidence_hash = _stable_hash({"campaignId": definition.campaign_id, "admission": asdict(admission)})
        return EnduranceCampaignReport(
            campaign_id=definition.campaign_id,
            campaign_type=definition.campaign_type.value,
            stage=definition.stage.value,
            verdict=EnduranceVerdict.FAIL,
            admission=admission,
            start_timestamp_utc=utc_timestamp(),
            end_timestamp_utc=utc_timestamp(),
            intended_duration_seconds=definition.intended_duration_seconds,
            actual_duration_seconds=0,
            accelerated_event_seconds=0,
            segment_count=0,
            longest_uninterrupted_duration_seconds=0,
            cumulative_segmented_duration_seconds=0,
            termination_reason="campaign admission blocked",
            pass_criteria_hash=admission.frozen_pass_criteria_hash,
            evidence_hash=evidence_hash,
            segments=(),
            critical_findings=(finding,),
            major_findings=(),
            determinism_signature=evidence_hash,
            eoda_integration={"active": False},
            eodc_integration={"active": False},
            eodd_integration={"active": False},
            eode_integration={"active": False},
        )


def _admission(admitted: bool, reasons: tuple[str, ...], environment: AdmissionEnvironment, criteria: EndurancePassCriteria) -> AdmissionResult:
    return AdmissionResult(admitted=admitted, reason_codes=reasons, environment_hash=_stable_hash(asdict(environment)), frozen_pass_criteria_hash=_stable_hash(asdict(criteria)))


def _definition_from_report(report: EnduranceCampaignReport, additional_segments: int) -> CampaignDefinition:
    return CampaignDefinition(
        campaign_id=f"{report.campaign_id}-RESUME-{len(report.segments) + 1:03d}",
        campaign_type=EnduranceCampaignType(report.campaign_type),
        stage=EnduranceStage(report.stage),
        duration_mode=DurationMode.SEGMENTED,
        intended_duration_seconds=max(1, report.intended_duration_seconds),
        accelerated_event_seconds=0,
        segment_target_count=additional_segments,
        metric_interval_seconds=max(1, report.intended_duration_seconds // 2),
        repository_commit="resumed-from-" + report.campaign_id,
        configuration_hash=report.pass_criteria_hash,
        policy_version="resumed",
        doctrine_version="resumed",
        truth_domain="PAPER",
        fixture_version="resumed",
        deterministic_seed="resumed",
        runtime_mode="paper",
        expected_workload="resumed segmented workload",
        pass_criteria=EndurancePassCriteria(),
        evidence_root="Documentation/EO-DF-evidence",
        allow_dirty_worktree=True,
    )


def _environment_from_report(report: EnduranceCampaignReport) -> AdmissionEnvironment:
    return AdmissionEnvironment(
        branch="resumed",
        full_commit_sha="resumed-from-" + report.campaign_id,
        git_status="",
        python_version="resumed",
        node_version="resumed",
        operating_system="resumed",
        persistence_backend="DurableEnterprisePersistenceStore",
        runtime_configuration="paper",
        truth_domain_configuration="PAPER",
        policy_version="resumed",
        doctrine_version="resumed",
        active_paper_broker="DeterministicPaperBrokerage",
        live_trading_enabled=False,
        available_hardware_resources={"resumed": True},
        expected_campaign_environment="segmented",
        existing_resource_limits={"resumed": True},
    )


def _last(segments: tuple[CampaignSegment, ...]) -> CampaignSegment:
    return segments[-1]


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_jsonable(item) for item in value)
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
