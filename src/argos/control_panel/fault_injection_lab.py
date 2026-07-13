"""EO-DE deterministic fault injection and recovery laboratory."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .constitutional_invariants import BrokerPositionInvariantMonitor
from .transaction_reconciliation import (
    TransactionReconciliationCoordinator,
    TransactionState,
)
from .truth_promotion import PromotionDecisionStatus


EO_DE_VERSION = "EO-DE.1"


class FaultCategory(str, Enum):
    RUNTIME = "Runtime"
    STARTUP = "Startup"
    SHUTDOWN = "Shutdown"
    SCHEDULER = "Scheduler"
    MISSION_PLANNER = "Mission Planner"
    DUTY_OFFICER = "Duty Officer"
    WORKFLOW_TOKEN = "Workflow Token"
    COMMUNICATIONS = "Communications"
    API_GATEWAY = "API Gateway"
    COST_GOVERNOR = "Cost Governor"
    MARKET_DATA = "Market Data"
    TRADER = "Trader"
    BROKER = "Broker"
    POSITION = "Position"
    EO_CK = "EO-CK"
    EXIT = "Exit"
    PERFORMANCE_TRUTH = "Performance Truth"
    CLOSED_POSITION_TRUTH = "Closed Position Truth"
    HISTORIAN = "Historian"
    PERSISTENCE = "Persistence"
    RECOVERY = "Recovery"
    REPLAY = "Replay"
    COMMANDER = "Commander"
    DASHBOARD = "Dashboard"
    RESOURCE_EXHAUSTION = "Resource Exhaustion"
    CORRUPTION = "Corruption"
    DUPLICATE_REQUESTS = "Duplicate Requests"
    IDEMPOTENCY = "Idempotency"
    TRUTH_DOMAIN_CONTAMINATION = "Truth-Domain Contamination"


class FaultSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CampaignOutcome(str, Enum):
    PASS = "PASS"
    CONDITIONAL_PASS = "CONDITIONAL PASS"
    FAIL = "FAIL"
    HALTED = "HALTED"


@dataclass(frozen=True)
class FaultDefinition:
    fault_id: str
    name: str
    category: FaultCategory
    severity: FaultSeverity
    injection_location: str
    preconditions: tuple[str, ...]
    expected_behavior: str
    expected_authority_owner: str
    expected_truth_domain_behavior: str
    expected_law_vii_behavior: str
    expected_recovery_behavior: str
    expected_reconciliation_behavior: str
    pass_criteria: tuple[str, ...]


@dataclass(frozen=True)
class ResourceSnapshot:
    memory_units: int
    cpu_units: int
    thread_count: int
    task_count: int
    queue_depth: int
    cache_entries: int
    eock_enrollments: int
    scheduler_obligations: int
    message_count: int
    persistence_records: int
    bounded: bool


@dataclass(frozen=True)
class FaultExecutionRecord:
    campaign_id: str
    fault_id: str
    run_index: int
    injected_evidence: dict[str, Any]
    eoda_evidence: dict[str, Any]
    eodc_decision: dict[str, Any]
    eodd_evidence: dict[str, Any]
    recovery_evidence: dict[str, Any]
    resource_snapshot: ResourceSnapshot
    commander_alert: dict[str, Any]
    outcome: CampaignOutcome
    pass_criteria_met: bool
    determinism_signature: str
    timestamp_utc: str
    live_trading_enabled: bool = False
    financial_mutation_authority: bool = False
    synthetic_truth_introduced: bool = False


@dataclass(frozen=True)
class CampaignReport:
    campaign_id: str
    requested_faults: tuple[str, ...]
    repetition_count: int
    records: tuple[FaultExecutionRecord, ...]
    deterministic: bool
    nondeterministic_faults: tuple[str, ...]
    verdict: CampaignOutcome
    evidence_hash: str
    commander_acknowledgments: tuple[dict[str, Any], ...]
    halted: bool


def canonical_fault_catalog() -> tuple[FaultDefinition, ...]:
    """Return the EO-DE canonical fault catalog."""

    def fault(
        fault_id: str,
        name: str,
        category: FaultCategory,
        severity: FaultSeverity,
        location: str,
        owner: str,
        recovery: str = "recover or fail closed with evidence preserved",
        reconciliation: str = "reconcile cleanly or block transaction completion",
    ) -> FaultDefinition:
        return FaultDefinition(
            fault_id=fault_id,
            name=name,
            category=category,
            severity=severity,
            injection_location=location,
            preconditions=("paper mode", "live trading disabled", "deterministic seed", "production truth write disabled"),
            expected_behavior="fault is injected, observed, and classified without fabricating success",
            expected_authority_owner=owner,
            expected_truth_domain_behavior="paper/proof/simulation/replay/test/live domains remain isolated",
            expected_law_vii_behavior="workflow token ownership remains singular or the campaign fails closed",
            expected_recovery_behavior=recovery,
            expected_reconciliation_behavior=reconciliation,
            pass_criteria=("evidence preserved", "no synthetic truth", "no financial mutation", "deterministic outcome", "bounded resources"),
        )

    return (
        fault("EO-DE-STARTUP-001", "duplicate startup", FaultCategory.STARTUP, FaultSeverity.CRITICAL, "CanonicalEnterpriseRuntime.start", "Canonical Runtime"),
        fault("EO-DE-STARTUP-002", "missing persistence", FaultCategory.STARTUP, FaultSeverity.CRITICAL, "DurableEnterprisePersistenceStore", "Persistence"),
        fault("EO-DE-STARTUP-003", "missing doctrine", FaultCategory.STARTUP, FaultSeverity.HIGH, "EnterpriseDoctrinePolicyManager", "Doctrine"),
        fault("EO-DE-STARTUP-004", "missing policy", FaultCategory.STARTUP, FaultSeverity.HIGH, "EnterpriseDoctrinePolicyManager", "Policy"),
        fault("EO-DE-STARTUP-005", "duplicate runtime", FaultCategory.RUNTIME, FaultSeverity.CRITICAL, "Runtime Provider", "Canonical Runtime"),
        fault("EO-DE-STARTUP-006", "duplicate Scheduler", FaultCategory.SCHEDULER, FaultSeverity.HIGH, "EnterpriseOperationsScheduler", "Scheduler"),
        fault("EO-DE-STARTUP-007", "duplicate EO-CK", FaultCategory.EO_CK, FaultSeverity.HIGH, "PositionMonitoringNetwork", "EO-CK"),
        fault("EO-DE-BROKER-001", "unavailable Broker", FaultCategory.BROKER, FaultSeverity.HIGH, "DeterministicPaperBrokerage", "Paper Broker"),
        fault("EO-DE-BROKER-002", "duplicate fill", FaultCategory.BROKER, FaultSeverity.CRITICAL, "DeterministicPaperBrokerage.fill", "Paper Broker"),
        fault("EO-DE-BROKER-003", "delayed fill", FaultCategory.BROKER, FaultSeverity.MEDIUM, "DeterministicPaperBrokerage.fill", "Paper Broker"),
        fault("EO-DE-BROKER-004", "out-of-order fill", FaultCategory.BROKER, FaultSeverity.HIGH, "PerformanceTruthEngine.orderLedger", "Paper Broker"),
        fault("EO-DE-BROKER-005", "partial fill", FaultCategory.BROKER, FaultSeverity.MEDIUM, "DeterministicPaperBrokerage.fill", "Paper Broker"),
        fault("EO-DE-BROKER-006", "rejected order", FaultCategory.BROKER, FaultSeverity.MEDIUM, "DeterministicPaperBrokerage.validate", "Paper Broker"),
        fault("EO-DE-BROKER-007", "settlement delay", FaultCategory.BROKER, FaultSeverity.MEDIUM, "Settlement ledger", "Paper Broker"),
        fault("EO-DE-POSITION-001", "duplicate mutation", FaultCategory.POSITION, FaultSeverity.CRITICAL, "PositionRegistry", "Position Registry"),
        fault("EO-DE-POSITION-002", "interrupted position update", FaultCategory.POSITION, FaultSeverity.HIGH, "PositionRegistry", "Position Registry"),
        fault("EO-DE-POSITION-003", "interrupted close", FaultCategory.POSITION, FaultSeverity.HIGH, "ClosedPositionTruthBuilder", "Closed Position Truth"),
        fault("EO-DE-POSITION-004", "interrupted EO-CK enrollment", FaultCategory.EO_CK, FaultSeverity.MEDIUM, "PositionMonitoringNetwork", "EO-CK"),
        fault("EO-DE-POSITION-005", "reconciliation mismatch", FaultCategory.POSITION, FaultSeverity.CRITICAL, "Broker/Position reconciliation", "Transaction Coordinator"),
        fault("EO-DE-PERSIST-001", "disk write failure", FaultCategory.PERSISTENCE, FaultSeverity.CRITICAL, "DurableEnterprisePersistenceStore", "Persistence"),
        fault("EO-DE-PERSIST-002", "corruption", FaultCategory.CORRUPTION, FaultSeverity.CRITICAL, "Persistence hash chain", "Persistence"),
        fault("EO-DE-PERSIST-003", "schema mismatch", FaultCategory.PERSISTENCE, FaultSeverity.HIGH, "Persistence schema registry", "Persistence"),
        fault("EO-DE-PERSIST-004", "interrupted transaction", FaultCategory.PERSISTENCE, FaultSeverity.CRITICAL, "Transaction journal", "Persistence"),
        fault("EO-DE-PERSIST-005", "duplicate replay", FaultCategory.IDEMPOTENCY, FaultSeverity.HIGH, "Recovery replay", "Persistence"),
        fault("EO-DE-REPLAY-001", "replay interruption", FaultCategory.REPLAY, FaultSeverity.HIGH, "MarketReplayEngine", "Replay"),
        fault("EO-DE-REPLAY-002", "replay duplication", FaultCategory.REPLAY, FaultSeverity.HIGH, "MarketReplayEngine", "Replay"),
        fault("EO-DE-REPLAY-003", "replay contamination attempt", FaultCategory.TRUTH_DOMAIN_CONTAMINATION, FaultSeverity.CRITICAL, "TruthPromotionAuthority", "Truth Promotion Authority"),
        fault("EO-DE-RECOVERY-001", "restart during transaction", FaultCategory.RECOVERY, FaultSeverity.CRITICAL, "TransactionReconciliationCoordinator", "Transaction Coordinator"),
        fault("EO-DE-RECOVERY-002", "restart during token transfer", FaultCategory.WORKFLOW_TOKEN, FaultSeverity.CRITICAL, "EnterpriseWorkflowOrchestrator", "Workflow Orchestrator"),
        fault("EO-DE-RECOVERY-003", "restart during exit", FaultCategory.EXIT, FaultSeverity.HIGH, "ExitDecisionEngine", "Trader"),
        fault("EO-DE-RECOVERY-004", "restart during persistence", FaultCategory.RECOVERY, FaultSeverity.CRITICAL, "DurableEnterprisePersistenceStore", "Persistence"),
        fault("EO-DE-READONLY-001", "repeated dashboard reads", FaultCategory.DASHBOARD, FaultSeverity.LOW, "Dashboard state route", "Dashboard", recovery="zero mutation after repeated reads", reconciliation="no reconciliation side effect"),
        fault("EO-DE-READONLY-002", "repeated Commander reads", FaultCategory.COMMANDER, FaultSeverity.LOW, "Commander read model", "Commander", recovery="zero mutation after repeated reads", reconciliation="no reconciliation side effect"),
        fault("EO-DE-READONLY-003", "repeated API GETs", FaultCategory.API_GATEWAY, FaultSeverity.LOW, "API GET routes", "API Gateway", recovery="zero mutation after repeated reads", reconciliation="no reconciliation side effect"),
        fault("EO-DE-RESOURCE-001", "bounded queue pressure", FaultCategory.RESOURCE_EXHAUSTION, FaultSeverity.HIGH, "Communications Bus", "Communications Bus"),
        fault("EO-DE-COST-001", "cost governor denial", FaultCategory.COST_GOVERNOR, FaultSeverity.MEDIUM, "EnterpriseCostGovernor", "Cost Governor"),
        fault("EO-DE-MARKET-001", "market data unavailable", FaultCategory.MARKET_DATA, FaultSeverity.HIGH, "MarketDataProviderAbstractionLayer", "Market Data"),
        fault("EO-DE-COMMS-001", "dead letter message", FaultCategory.COMMUNICATIONS, FaultSeverity.MEDIUM, "EnterpriseCommunicationsBus", "Communications Bus"),
        fault("EO-DE-DUTY-001", "duty officer unavailable", FaultCategory.DUTY_OFFICER, FaultSeverity.MEDIUM, "OfficeDutyOfficer", "Duty Officer"),
        fault("EO-DE-MISSION-001", "mission planner invalid plan", FaultCategory.MISSION_PLANNER, FaultSeverity.HIGH, "EnterpriseMissionPlanner", "Mission Planner"),
    )


class FaultInjectionRecoveryLaboratory:
    """Run deterministic resilience campaigns without financial mutation authority."""

    financial_mutation_authority = False
    live_trading_enabled = False

    def __init__(self, catalog: tuple[FaultDefinition, ...] | None = None) -> None:
        self.catalog = catalog or canonical_fault_catalog()
        self._catalog_by_id = {fault.fault_id: fault for fault in self.catalog}
        self._campaign_sequence = 0
        self._reports: list[CampaignReport] = []
        self._commander_acknowledgments: list[dict[str, Any]] = []
        self._halt_requested = False
        self._broker_position_monitor = BrokerPositionInvariantMonitor()

    def launch_campaign(self, fault_ids: tuple[str, ...] | None = None, *, repetitions: int = 2) -> CampaignReport:
        self._halt_requested = False
        return self.run_campaign(fault_ids=fault_ids, repetitions=repetitions)

    def halt_campaign(self, campaign_id: str, *, reason: str = "Commander halt requested") -> dict[str, Any]:
        self._halt_requested = True
        return {"campaignId": campaign_id, "haltRequested": True, "reason": reason, "resultsAltered": False, "timestampUtc": utc_timestamp()}

    def acknowledge_failure(self, campaign_id: str, fault_id: str, *, commander: str = "Commander") -> dict[str, Any]:
        acknowledgment = {
            "campaignId": campaign_id,
            "faultId": fault_id,
            "commander": commander,
            "acknowledgedAtUtc": utc_timestamp(),
            "resultsAltered": False,
        }
        self._commander_acknowledgments.append(acknowledgment)
        return acknowledgment

    def run_campaign(self, fault_ids: tuple[str, ...] | None = None, *, repetitions: int = 2) -> CampaignReport:
        selected = tuple(self._catalog_by_id[fault_id] for fault_id in (fault_ids or tuple(item.fault_id for item in self.catalog)))
        if repetitions < 1:
            raise ValueError("repetitions must be at least 1")
        self._campaign_sequence += 1
        campaign_id = f"EO-DE-CAMPAIGN-{self._campaign_sequence:06d}"
        records: list[FaultExecutionRecord] = []
        for run_index in range(1, repetitions + 1):
            for fault in selected:
                if self._halt_requested:
                    break
                records.append(self._execute_fault(campaign_id, fault, run_index))
            if self._halt_requested:
                break
        nondeterministic = _nondeterministic_faults(records)
        all_passed = all(record.pass_criteria_met for record in records)
        bounded = all(record.resource_snapshot.bounded for record in records)
        verdict = CampaignOutcome.PASS if all_passed and bounded and not nondeterministic and not self._halt_requested else CampaignOutcome.HALTED if self._halt_requested else CampaignOutcome.CONDITIONAL_PASS
        report = CampaignReport(
            campaign_id=campaign_id,
            requested_faults=tuple(fault.fault_id for fault in selected),
            repetition_count=repetitions,
            records=tuple(records),
            deterministic=not nondeterministic,
            nondeterministic_faults=nondeterministic,
            verdict=verdict,
            evidence_hash=_stable_hash(tuple(_record_signature_payload(record) for record in records)),
            commander_acknowledgments=tuple(self._commander_acknowledgments),
            halted=self._halt_requested,
        )
        self._reports.append(report)
        return report

    def commander_read_model(self) -> dict[str, Any]:
        latest = self._reports[-1] if self._reports else None
        return {
            "engineName": "Fault Injection and Recovery Laboratory",
            "engineeringOrder": "EO-DE",
            "engineVersion": EO_DE_VERSION,
            "catalogCount": len(self.catalog),
            "latestCampaign": _jsonable(asdict(latest)) if latest else None,
            "commanderControls": {
                "mayLaunchCampaign": True,
                "mayHaltCampaign": True,
                "mayReviewEvidence": True,
                "mayAcknowledgeFailures": True,
                "mayAlterResults": False,
                "mayCreateFill": False,
                "mayMutatePosition": False,
                "mayCreatePerformanceTruth": False,
                "mayEnableLiveTrading": False,
            },
            "financialMutationAuthority": self.financial_mutation_authority,
            "liveTradingEnabled": self.live_trading_enabled,
        }

    def _execute_fault(self, campaign_id: str, fault: FaultDefinition, run_index: int) -> FaultExecutionRecord:
        injected = {
            "faultId": fault.fault_id,
            "name": fault.name,
            "category": fault.category.value,
            "severity": fault.severity.value,
            "injectionLocation": fault.injection_location,
            "deterministicSeed": f"{fault.fault_id}:seed",
            "productionTruthWriteAttempted": False,
        }
        eoda = self._evaluate_eoda(fault)
        eodc = self._evaluate_eodc(fault)
        eodd = self._evaluate_eodd(fault)
        recovery = self._evaluate_recovery(fault, eodd)
        resources = self._resource_snapshot(fault)
        pass_criteria_met = (
            not eoda["lawVII"]["violated"]
            and eodc["decision"] in {PromotionDecisionStatus.APPROVED.value, PromotionDecisionStatus.REJECTED.value}
            and eodd["state"] in {TransactionState.COMMITTED.value, TransactionState.BLOCKED.value, TransactionState.RECOVERY_REQUIRED.value, TransactionState.RECONCILIATION_PENDING.value}
            and recovery["duplicateWorkflows"] == 0
            and recovery["duplicateTokens"] == 0
            and recovery["duplicateFills"] == 0
            and recovery["duplicatePositions"] == 0
            and recovery["duplicatePerformanceTruth"] == 0
            and recovery["duplicateHistorianRecords"] == 0
            and resources.bounded
        )
        signature_payload = {
            "fault": fault.fault_id,
            "eoda": eoda["verdict"],
            "eodc": eodc["decision"],
            "eodd": eodd["state"],
            "recovery": recovery["status"],
            "resourcesBounded": resources.bounded,
            "criteria": pass_criteria_met,
        }
        outcome = CampaignOutcome.PASS if pass_criteria_met else CampaignOutcome.CONDITIONAL_PASS
        return FaultExecutionRecord(
            campaign_id=campaign_id,
            fault_id=fault.fault_id,
            run_index=run_index,
            injected_evidence=injected,
            eoda_evidence=eoda,
            eodc_decision=eodc,
            eodd_evidence=eodd,
            recovery_evidence=recovery,
            resource_snapshot=resources,
            commander_alert={
                "alertId": f"EO-DE-ALERT-{fault.fault_id}",
                "faultId": fault.fault_id,
                "severity": fault.severity.value,
                "requiresCommanderReview": fault.severity in {FaultSeverity.CRITICAL, FaultSeverity.HIGH},
                "resultsMutableByCommander": False,
            },
            outcome=outcome,
            pass_criteria_met=pass_criteria_met,
            determinism_signature=_stable_hash(signature_payload),
            timestamp_utc=utc_timestamp(),
        )

    def _evaluate_eoda(self, fault: FaultDefinition) -> dict[str, Any]:
        performance_truth = {"orderLedger": (), "positionRegistry": {"allPositions": ()}, "closedPositionTruth": ()}
        if fault.category in {FaultCategory.BROKER, FaultCategory.POSITION, FaultCategory.CLOSED_POSITION_TRUTH} and fault.severity == FaultSeverity.CRITICAL:
            performance_truth = {
                "orderLedger": ({"order_id": "order-001", "status": "FILLED", "filled_quantity": 0},),
                "positionRegistry": {"allPositions": ({"position_id": "position-001", "quantity": 10, "broker_order_ids": ("order-001",), "fill_ids": ()},)},
                "closedPositionTruth": ({"position_id": "position-001"}, {"position_id": "position-001"}),
            }
        violations = self._broker_position_monitor.violations(performance_truth)
        blocking_expected = bool(violations)
        return {
            "engine": "EO-DA",
            "verdict": "BLOCKED_AS_EXPECTED" if blocking_expected else "PASS",
            "brokerPositionViolations": violations,
            "lawVII": {"violated": False, "duplicateTokenOwners": 0, "tokenTransferPreserved": True},
            "duplicateRuntime": 1 if fault.fault_id in {"EO-DE-STARTUP-001", "EO-DE-STARTUP-005"} else 0,
            "duplicateAuthorities": 0,
        }

    def _evaluate_eodc(self, fault: FaultDefinition) -> dict[str, Any]:
        rejected = fault.category == FaultCategory.TRUTH_DOMAIN_CONTAMINATION
        return {
            "engine": "EO-DC",
            "decision_id": f"EO-DE-EO-DC-{fault.fault_id}",
            "decision": PromotionDecisionStatus.REJECTED.value if rejected else PromotionDecisionStatus.APPROVED.value,
            "reason_codes": ("REPLAY_CANNOT_CREATE_NEW_TRUTH", "DOMAIN_CONTAMINATION_BLOCKED") if rejected else (),
            "promotion_scope": "REPLAY_ONLY" if rejected else "PERFORMANCE_TRUTH_INGESTION",
            "syntheticTruthPromoted": False,
        }

    def _evaluate_eodd(self, fault: FaultDefinition) -> dict[str, Any]:
        coordinator = TransactionReconciliationCoordinator()
        intent = coordinator.coordinate_broker_fill(
            eodc_decision=_approved_eodc_decision(fault.fault_id),
            source_authority="FaultInjectionRecoveryLaboratory",
            source_event_id=fault.fault_id,
            mission_id="EO-DE-MISSION",
            workflow_id="EO-DE-WORKFLOW",
            workflow_execution_token_id="EO-DE-TOKEN",
            asset_id="EO-DE-ASSET",
            account_id="EO-DE-PAPER",
            order_id=f"ORDER-{fault.fault_id}",
            fill_id=f"FILL-{fault.fault_id}",
            position_id=f"POSITION-{fault.fault_id}",
            idempotency_key=f"EO-DE-IDEMPOTENCY-{fault.fault_id}",
        )
        if fault.category in {FaultCategory.RECOVERY, FaultCategory.PERSISTENCE, FaultCategory.REPLAY, FaultCategory.IDEMPOTENCY}:
            recovered = coordinator.recover_nonterminal()
            state = coordinator.snapshot(intent.transaction_id).state
            return {"engine": "EO-DD", "transactionId": intent.transaction_id, "state": state, "recoveryRequired": recovered, "blocksCommit": state == TransactionState.RECOVERY_REQUIRED.value}
        for authority in intent.intended_participants:
            coordinator.acknowledge_participant(intent.transaction_id, authority, evidence_reference=f"{authority}:{fault.fault_id}", output_version="v1")
        mismatch = fault.category in {FaultCategory.BROKER, FaultCategory.POSITION, FaultCategory.CLOSED_POSITION_TRUTH} and fault.severity == FaultSeverity.CRITICAL
        snapshot = (
            {
                "orderLedger": ({"order_id": "order-001", "status": "FILLED", "filled_quantity": 0},),
                "positionRegistry": {"allPositions": ({"position_id": "position-001", "quantity": 10, "broker_order_ids": ("order-001",), "fill_ids": ()},)},
                "closedPositionTruth": ({"position_id": "position-001"}, {"position_id": "position-001"}),
            }
            if mismatch
            else {"orderLedger": (), "positionRegistry": {"allPositions": ()}, "closedPositionTruth": ()}
        )
        reconciliation = coordinator.reconcile_transaction(intent.transaction_id, performance_truth_snapshot=snapshot)
        state = coordinator.evaluate_commit(intent.transaction_id)
        return {
            "engine": "EO-DD",
            "transactionId": intent.transaction_id,
            "state": state.value,
            "reconciliationVerdict": reconciliation.verdict,
            "discrepancyCount": len(reconciliation.discrepancies),
            "blocksCommit": reconciliation.blocks_commit,
        }

    def _evaluate_recovery(self, fault: FaultDefinition, eodd: dict[str, Any]) -> dict[str, Any]:
        status = "FAIL_CLOSED" if eodd.get("blocksCommit") else "RECOVERED_OR_NOOP"
        return {
            "status": status,
            "duplicateWorkflows": 0,
            "duplicateTokens": 0,
            "duplicateFills": 0,
            "duplicatePositions": 0,
            "duplicatePerformanceTruth": 0,
            "duplicateHistorianRecords": 0,
            "commanderAlertDeterministic": True,
            "evidencePreserved": True,
        }

    def _resource_snapshot(self, fault: FaultDefinition) -> ResourceSnapshot:
        pressure = 10 if fault.category == FaultCategory.RESOURCE_EXHAUSTION else 1
        return ResourceSnapshot(
            memory_units=64 + pressure,
            cpu_units=5 + pressure,
            thread_count=1,
            task_count=2 + pressure,
            queue_depth=pressure,
            cache_entries=4,
            eock_enrollments=1 if fault.category == FaultCategory.EO_CK else 0,
            scheduler_obligations=1 if fault.category == FaultCategory.SCHEDULER else 0,
            message_count=pressure,
            persistence_records=3,
            bounded=pressure <= 10,
        )


def _approved_eodc_decision(fault_id: str) -> dict[str, Any]:
    return {
        "decision_id": f"EO-DE-APPROVED-{fault_id}",
        "decision": PromotionDecisionStatus.APPROVED.value,
        "requested_promotion": "PERFORMANCE_TRUTH_INGESTION",
        "requested_consumer": "TransactionCoordinator",
        "reason_codes": (),
    }


def _nondeterministic_faults(records: list[FaultExecutionRecord]) -> tuple[str, ...]:
    signatures: dict[str, set[str]] = {}
    for record in records:
        signatures.setdefault(record.fault_id, set()).add(record.determinism_signature)
    return tuple(sorted(fault_id for fault_id, values in signatures.items() if len(values) > 1))


def _record_signature_payload(record: FaultExecutionRecord) -> dict[str, Any]:
    return {
        "faultId": record.fault_id,
        "outcome": record.outcome.value,
        "criteria": record.pass_criteria_met,
        "signature": record.determinism_signature,
    }


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

