"""Enterprise Priority Engine for ARGOS EO-CJ."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp


class EnterprisePriorityClass(str, Enum):
    EMERGENCY_RECOVERY = "emergency_recovery"
    POSITION_SAFETY = "position_safety"
    BROKER_LEDGER_INTEGRITY = "broker_ledger_integrity"
    RISK_CONTROL = "risk_control"
    REQUIRED_LIFECYCLE_ACTION = "required_lifecycle_action"
    COMMANDER_DIRECTED = "commander_directed"
    TACTICAL_EVALUATION = "tactical_evaluation"
    STRATEGIC_INTELLIGENCE = "strategic_intelligence"
    HISTORICAL_REVIEW = "historical_review"
    CAPABILITY_DEVELOPMENT = "capability_development"


class PriorityDecisionStatus(str, Enum):
    PENDING = "pending"
    EVALUATING = "evaluating"
    RANKED = "ranked"
    RUN_NOW_RECOMMENDED = "run_now_recommended"
    QUEUED = "queued"
    DEFERRED = "deferred"
    SUSPENSION_RECOMMENDED = "suspension_recommended"
    PREEMPTION_RECOMMENDED = "preemption_recommended"
    MERGE_RECOMMENDED = "merge_recommended"
    REDUCTION_RECOMMENDED = "reduction_recommended"
    BLOCKED = "blocked"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    CANCELED = "canceled"


class PreemptionClass(str, Enum):
    NON_PREEMPTIBLE = "non_preemptible"
    PREEMPTIBLE_AT_CHECKPOINT = "preemptible_at_checkpoint"
    IMMEDIATELY_PREEMPTIBLE = "immediately_preemptible"
    SAFETY_ONLY_PREEMPTIBLE = "safety_only_preemptible"


class QueueDisposition(str, Enum):
    RUN_NOW = "run_now"
    QUEUE_NEXT = "queue_next"
    QUEUE_NORMAL = "queue_normal"
    DEFER = "defer"
    MERGE = "merge"
    REDUCE_SCOPE = "reduce_scope"
    SUSPEND = "suspend"
    CANCEL_RECOMMENDED = "cancel_recommended"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PriorityPolicy:
    policy_id: str
    version: int
    class_order: tuple[EnterprisePriorityClass, ...]
    base_scores: dict[EnterprisePriorityClass, float]
    aging_points_per_hour: float
    starvation_threshold_hours: float
    max_aging_within_class: float
    excessive_cost_threshold_usd: float
    long_runtime_threshold_seconds: int
    protected_safety_classes: tuple[EnterprisePriorityClass, ...]
    effective_at: str
    content_hash: str


@dataclass(frozen=True)
class PriorityCandidate:
    priority_candidate_id: str
    mission_id: str
    mission_plan_id: str
    mission_plan_version: int
    mission_type: str
    mission_status: str
    subject_type: str
    subject_id: str
    ticker: str
    position_id: str
    order_id: str
    source_event_ids: tuple[str, ...]
    requested_priority_class: EnterprisePriorityClass | None
    event_severity: str
    event_urgency: str
    event_materiality: str
    earliest_start_at: str
    deadline_at: str
    expires_at: str
    estimated_runtime_seconds: int
    estimated_cost: float
    estimated_api_calls: int
    mandatory_offices: tuple[str, ...]
    dependency_mission_ids: tuple[str, ...]
    dependent_mission_ids: tuple[str, ...]
    open_position_related: bool
    active_order_related: bool
    safety_critical: bool
    commander_directed: bool
    commander_priority_modifier: int
    submitted_at: str
    preemption_class: PreemptionClass
    metadata: dict[str, Any]


@dataclass(frozen=True)
class PriorityScoreComponents:
    class_base_score: float
    emergency_score: float
    position_safety_score: float
    broker_integrity_score: float
    ledger_integrity_score: float
    risk_score: float
    lifecycle_score: float
    commander_score: float
    deadline_score: float
    urgency_score: float
    financial_exposure_score: float
    downside_score: float
    dependency_score: float
    blocking_score: float
    mission_age_score: float
    starvation_score: float
    completion_proximity_score: float
    preemption_cost_score: float
    budget_availability_score: float
    office_availability_score: float
    token_availability_score: float
    freshness_score: float
    duplication_penalty: float
    excessive_cost_penalty: float
    long_runtime_penalty: float
    low_confidence_penalty: float
    deferability_penalty: float
    stale_input_penalty: float
    operating_mode_penalty: float
    policy_adjustment: float
    commander_adjustment: float


@dataclass(frozen=True)
class PriorityDecision:
    priority_decision_id: str
    priority_decision_version: int
    priority_candidate_id: str
    mission_id: str
    mission_plan_id: str
    mission_plan_version: int
    assigned_priority_class: EnterprisePriorityClass
    effective_priority_class: EnterprisePriorityClass
    raw_score: float
    adjusted_score: float
    normalized_score: float
    score_components: PriorityScoreComponents
    hard_precedence_rank: int
    queue_rank: int
    status: PriorityDecisionStatus
    disposition: QueueDisposition
    preemption_class: PreemptionClass
    preemption_recommendation: str
    suspension_recommendation: str
    merge_recommendation: str
    reduction_recommendation: str
    inheritance_applied: bool
    inherited_from_mission_id: str
    blocking_reasons: tuple[str, ...]
    explanation: tuple[str, ...]
    scheduler_recommendation: dict[str, Any]
    created_at: str
    content_hash: str


@dataclass(frozen=True)
class PriorityQueueSnapshot:
    queue_snapshot_id: str
    policy_id: str
    policy_version: int
    generated_at: str
    ranked_decision_ids: tuple[str, ...]
    run_now_decision_ids: tuple[str, ...]
    queued_decision_ids: tuple[str, ...]
    deferred_decision_ids: tuple[str, ...]
    suspended_decision_ids: tuple[str, ...]
    blocked_decision_ids: tuple[str, ...]
    scheduler_feed: dict[str, Any]
    content_hash: str


class EnterprisePriorityEngine:
    """Deterministic priority adviser; EO-CA remains mission authority."""

    def __init__(self) -> None:
        self._policy_versions: list[PriorityPolicy] = [_hash_policy(_default_policy())]
        self._candidates: dict[str, PriorityCandidate] = {}
        self._decisions: dict[str, PriorityDecision] = {}
        self._latest_by_candidate: dict[str, str] = {}
        self._queue_snapshots: list[PriorityQueueSnapshot] = []
        self._aging: dict[str, dict[str, Any]] = {}
        self._deferrals: dict[str, int] = {}
        self._audit: list[dict[str, Any]] = []
        self._alerts: list[dict[str, Any]] = []
        self._dead_letters: list[dict[str, Any]] = []
        self._manual_overrides: list[dict[str, Any]] = []

    @property
    def policy(self) -> PriorityPolicy:
        return self._policy_versions[-1]

    def snapshot(self) -> dict[str, Any]:
        latest = tuple(self._latest_decisions())
        latest_snapshot = self._queue_snapshots[-1] if self._queue_snapshots else None
        return {
            "engineName": "Enterprise Priority Engine",
            "engineeringOrder": "EO-CJ",
            "status": "HEALTHY" if not any(alert.get("severity") == "CRITICAL" for alert in self._alerts[-10:]) else "DEGRADED",
            "activePolicy": _public(self.policy),
            "policyVersions": tuple(_public(item) for item in self._policy_versions),
            "summary": self._summary(latest),
            "priorityCandidates": tuple(_public(item) for item in self._candidates.values()),
            "priorityDecisions": tuple(_public(item) for item in latest),
            "rankedMissionQueue": tuple(_queue_row(item) for item in latest),
            "scoreBreakdown": tuple(_score_row(item) for item in latest[:12]),
            "safetyPrecedence": self._safety_precedence(latest),
            "priorityInheritance": tuple(_inheritance_row(item) for item in latest if item.inheritance_applied),
            "preemptionAssessments": tuple(_preemption_row(item) for item in latest),
            "starvationAndAging": tuple(_aging_row(item, self._aging.get(item.priority_candidate_id, {}), self._deferrals.get(item.priority_candidate_id, 0)) for item in latest),
            "resourceConstraints": tuple(_resource_row(item) for item in latest),
            "suspendedAndDeferred": tuple(_queue_row(item) for item in latest if item.disposition in {QueueDisposition.DEFER, QueueDisposition.SUSPEND, QueueDisposition.BLOCKED}),
            "queueSnapshots": tuple(_public(item) for item in self._queue_snapshots[-10:]),
            "latestQueueSnapshot": _public(latest_snapshot) if latest_snapshot else {},
            "schedulerFeed": latest_snapshot.scheduler_feed if latest_snapshot else {},
            "alerts": tuple(self._alerts[-20:]),
            "auditHistory": tuple(self._audit[-50:]),
            "deadLetters": tuple(self._dead_letters[-20:]),
            "manualOverrides": tuple(self._manual_overrides[-20:]),
            "metrics": self._metrics(latest),
            "integrationFeeds": {
                "eoCA": {"rankedRecommendationsAvailable": True, "schedulerAuthorityPreserved": True},
                "eoCD": {"missionPlanPriorityClassConsumed": True},
                "eoCE": {"budgetStateConsumed": True, "budgetAuthorityPreserved": True},
                "eoCC": {"eventSeverityUrgencyConsumed": True},
                "eoCF": {"freshnessConstraintsConsumed": True},
                "eoCG": {"cacheCoverageConsumed": True},
                "eoCH": {"deltaScopeConsumed": True},
            },
            "commanderControls": {
                "evaluatePriority": True,
                "recoverSnapshot": True,
                "replayRanking": True,
                "setCommanderModifier": True,
                "directMissionAuthorization": False,
                "directOfficeWakeAuthority": False,
                "directBudgetReservation": False,
                "directPositionMutation": False,
                "directLedgerMutation": False,
            },
            "lawCJ": {
                "priorityIsAuthorization": False,
                "officeWakeAuthority": False,
                "workflowTokenTransferAuthority": False,
                "budgetReserveAuthority": False,
                "missionCreationAuthority": False,
                "brokerOrderAuthority": False,
                "positionMutationAuthority": False,
                "ledgerMutationAuthority": False,
                "routineAiInvocations": 0,
                "safetyOverridesScoreArithmetic": True,
                "positionSafetyCannotBeStarved": True,
                "fairnessDoesNotOverrideSafety": True,
                "uncontrolledLoopsCreated": False,
            },
            "persistence": {
                "mode": "runtime_snapshot",
                "restartRecovery": True,
                "appendOnlyDecisionHistory": True,
                "stableTieBreaking": True,
            },
        }

    def evaluate(self, sources: dict[str, Any]) -> dict[str, Any]:
        candidates = self._collect_candidates(sources)
        if not candidates:
            self._audit_event("priority_evaluation_noop", "EO-CJ", "No eligible mission candidates were present.")
            return self.snapshot()
        for candidate in candidates:
            self._candidates[candidate.priority_candidate_id] = candidate
            self._aging.setdefault(candidate.priority_candidate_id, {"firstSeenAt": candidate.submitted_at, "lastSeenAt": candidate.submitted_at})
        decisions = [self._decision_for(candidate, sources) for candidate in candidates]
        ranked = self._rank(decisions)
        updated_ranked = []
        for rank, decision in enumerate(ranked, start=1):
            disposition = _disposition_for(decision, rank)
            status = PriorityDecisionStatus.RUN_NOW_RECOMMENDED if disposition == QueueDisposition.RUN_NOW else (PriorityDecisionStatus.DEFERRED if disposition == QueueDisposition.DEFER else PriorityDecisionStatus.RANKED)
            decision = replace(decision, queue_rank=rank, disposition=disposition, status=status, scheduler_recommendation=_scheduler_recommendation(decision, rank, disposition), content_hash="")
            decision = _hash_decision(decision)
            self._decisions[decision.priority_decision_id] = decision
            self._latest_by_candidate[decision.priority_candidate_id] = decision.priority_decision_id
            updated_ranked.append(decision)
            if disposition == QueueDisposition.DEFER:
                self._deferrals[decision.priority_candidate_id] = self._deferrals.get(decision.priority_candidate_id, 0) + 1
        self._detect_alerts(tuple(updated_ranked))
        snapshot = self._queue_snapshot(tuple(updated_ranked))
        self._queue_snapshots.append(snapshot)
        self._audit_event("priority_queue_ranked", snapshot.queue_snapshot_id, f"{len(ranked)} missions ranked deterministically.")
        return self.snapshot()

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._candidates = {}
        self._decisions = {}
        self._latest_by_candidate = {}
        self._queue_snapshots = []
        for item in snapshot.get("priorityCandidates", ()):
            candidate = _candidate_from_public(item)
            self._candidates[candidate.priority_candidate_id] = candidate
        for item in snapshot.get("priorityDecisions", ()):
            decision = _decision_from_public(item)
            self._decisions[decision.priority_decision_id] = decision
            self._latest_by_candidate[decision.priority_candidate_id] = decision.priority_decision_id
        for item in snapshot.get("queueSnapshots", ()):
            queue = _queue_from_public(item)
            self._queue_snapshots.append(queue)
        self._audit_event("restart_recovery", "EO-CJ", "Enterprise Priority Engine restored from snapshot.")

    def replay(self, sources: dict[str, Any]) -> dict[str, Any]:
        engine = EnterprisePriorityEngine()
        result = engine.evaluate(sources)
        result["replayMode"] = True
        result["productionMutation"] = False
        return result

    def set_commander_modifier(self, candidate_id: str, modifier: int, *, actor: str = "Commander", reason: str = "") -> None:
        if candidate_id not in self._candidates:
            self._dead_letter(candidate_id or "unknown", "candidate_unavailable", "Commander modifier target is not an active priority candidate.")
            return
        self._manual_overrides.append({"overrideId": f"EPJ-OVR-{len(self._manual_overrides) + 1:06d}", "candidateId": candidate_id, "modifier": max(-25, min(25, int(modifier))), "actor": actor, "reason": reason or "Commander priority modifier.", "timestamp": utc_timestamp(), "directNumericPrioritySet": False})

    def _collect_candidates(self, sources: dict[str, Any]) -> tuple[PriorityCandidate, ...]:
        planner = sources.get("enterpriseMissionPlanner") or {}
        scheduler = sources.get("enterpriseOperationsScheduler") or {}
        events = sources.get("eventDetectionEngine") or {}
        candidates: dict[str, PriorityCandidate] = {}
        for plan in tuple(planner.get("draftMissionPlans", ())) + tuple(planner.get("submittedMissionPlans", ())) + tuple(planner.get("allMissionPlans", ())):
            if str(plan.get("status", "")).lower() in {"not_required", "superseded", "canceled", "expired"}:
                continue
            candidate = _candidate_from_plan(plan)
            candidates[candidate.priority_candidate_id] = candidate
        for mission in tuple(scheduler.get("missionRecords", ())):
            if str(mission.get("status", "")) in {"Completed", "Completed With Warnings", "Cancelled", "Failed", "Aborted", "Expired"}:
                continue
            candidate = _candidate_from_mission(mission)
            candidates.setdefault(candidate.priority_candidate_id, candidate)
        for event in tuple(events.get("activeEvents", ())):
            if str(event.get("status", "")) in {"resolved", "expired"}:
                continue
            candidate = _candidate_from_event(event)
            candidates.setdefault(candidate.priority_candidate_id, candidate)
        return tuple(candidates.values())

    def _decision_for(self, candidate: PriorityCandidate, sources: dict[str, Any]) -> PriorityDecision:
        policy = self.policy
        assigned = candidate.requested_priority_class or _class_for(candidate)
        inherited, inherited_from = _inheritance(candidate, self._candidates)
        effective = _more_protective(assigned, inherited or assigned)
        components = _score_components(candidate, assigned, effective, policy, sources, self._aging.get(candidate.priority_candidate_id, {}), self._deferrals.get(candidate.priority_candidate_id, 0))
        raw_score = _component_total(components)
        adjusted_score = max(0.0, raw_score)
        normalized = min(100.0, round(adjusted_score / 10.0, 4))
        hard_rank = _class_rank(effective)
        blockers = _blockers(candidate, sources)
        preemption = _preemption_recommendation(candidate, effective, raw_score, blockers)
        explanation = _explanation(candidate, assigned, effective, components, blockers, inherited_from)
        version = self._decision_version(candidate.priority_candidate_id) + 1
        decision = PriorityDecision(
            priority_decision_id=f"EPJ-DEC-{_short_hash(candidate.priority_candidate_id)[:8]}-V{version:03d}",
            priority_decision_version=version,
            priority_candidate_id=candidate.priority_candidate_id,
            mission_id=candidate.mission_id,
            mission_plan_id=candidate.mission_plan_id,
            mission_plan_version=candidate.mission_plan_version,
            assigned_priority_class=assigned,
            effective_priority_class=effective,
            raw_score=round(raw_score, 4),
            adjusted_score=round(adjusted_score, 4),
            normalized_score=normalized,
            score_components=components,
            hard_precedence_rank=hard_rank,
            queue_rank=0,
            status=PriorityDecisionStatus.RANKED,
            disposition=QueueDisposition.QUEUE_NORMAL,
            preemption_class=candidate.preemption_class,
            preemption_recommendation=preemption,
            suspension_recommendation=_suspension_recommendation(candidate, effective, blockers),
            merge_recommendation=_merge_recommendation(candidate, self._candidates),
            reduction_recommendation=_reduction_recommendation(candidate, sources),
            inheritance_applied=bool(inherited_from),
            inherited_from_mission_id=inherited_from,
            blocking_reasons=blockers,
            explanation=explanation,
            scheduler_recommendation={},
            created_at=utc_timestamp(),
            content_hash="",
        )
        return _hash_decision(decision)

    def _decision_version(self, candidate_id: str) -> int:
        latest_id = self._latest_by_candidate.get(candidate_id)
        return self._decisions[latest_id].priority_decision_version if latest_id and latest_id in self._decisions else 0

    def _rank(self, decisions: list[PriorityDecision]) -> tuple[PriorityDecision, ...]:
        return tuple(sorted(decisions, key=lambda item: (item.hard_precedence_rank, -item.normalized_score, _parse_time(_candidate_time(self._candidates.get(item.priority_candidate_id))), item.priority_candidate_id)))

    def _queue_snapshot(self, decisions: tuple[PriorityDecision, ...]) -> PriorityQueueSnapshot:
        run_now = tuple(item.priority_decision_id for item in decisions if item.queue_rank == 1 and item.disposition == QueueDisposition.RUN_NOW)
        queued = tuple(item.priority_decision_id for item in decisions if item.disposition in {QueueDisposition.QUEUE_NEXT, QueueDisposition.QUEUE_NORMAL})
        deferred = tuple(item.priority_decision_id for item in decisions if item.disposition == QueueDisposition.DEFER)
        suspended = tuple(item.priority_decision_id for item in decisions if item.disposition == QueueDisposition.SUSPEND)
        blocked = tuple(item.priority_decision_id for item in decisions if item.disposition == QueueDisposition.BLOCKED)
        feed = {
            "targetEngine": "EO-CA Enterprise Operations Scheduler",
            "recommendationsOnly": True,
            "rankedMissionIds": tuple(item.mission_id or item.mission_plan_id or item.priority_candidate_id for item in decisions),
            "runNow": tuple((item.mission_id or item.mission_plan_id) for item in decisions if item.disposition == QueueDisposition.RUN_NOW),
            "queueNext": tuple((item.mission_id or item.mission_plan_id) for item in decisions if item.disposition == QueueDisposition.QUEUE_NEXT),
            "defer": tuple((item.mission_id or item.mission_plan_id) for item in decisions if item.disposition == QueueDisposition.DEFER),
            "authorityTransferred": False,
        }
        snapshot = PriorityQueueSnapshot(f"EPJ-Q-{len(self._queue_snapshots) + 1:06d}", self.policy.policy_id, self.policy.version, utc_timestamp(), tuple(item.priority_decision_id for item in decisions), run_now, queued, deferred, suspended, blocked, feed, "")
        return _hash_queue(snapshot)

    def _latest_decisions(self) -> tuple[PriorityDecision, ...]:
        decisions = [self._decisions[decision_id] for decision_id in self._latest_by_candidate.values() if decision_id in self._decisions]
        return tuple(sorted(decisions, key=lambda item: (item.queue_rank or 999, item.hard_precedence_rank, -item.normalized_score, item.priority_candidate_id)))

    def _detect_alerts(self, ranked: tuple[PriorityDecision, ...]) -> None:
        for decision in ranked:
            if decision.effective_priority_class == EnterprisePriorityClass.POSITION_SAFETY and decision.disposition in {QueueDisposition.DEFER, QueueDisposition.BLOCKED}:
                self._alerts.append({"alertId": f"EPJ-ALERT-{len(self._alerts) + 1:06d}", "severity": "CRITICAL", "alertType": "safety_mission_blocked", "missionId": decision.mission_id or decision.mission_plan_id, "summary": "Position-safety work is not executable and remains visible.", "timestamp": utc_timestamp()})
            if decision.inheritance_applied:
                self._alerts.append({"alertId": f"EPJ-ALERT-{len(self._alerts) + 1:06d}", "severity": "INFO", "alertType": "priority_inheritance", "missionId": decision.mission_id or decision.mission_plan_id, "summary": "Dependency inherited elevated priority from protected work.", "timestamp": utc_timestamp()})

    def _summary(self, decisions: tuple[PriorityDecision, ...]) -> dict[str, Any]:
        return {
            "candidateCount": len(self._candidates),
            "rankedCount": len(decisions),
            "runNowRecommendations": sum(1 for item in decisions if item.disposition == QueueDisposition.RUN_NOW),
            "deferredMissions": sum(1 for item in decisions if item.disposition == QueueDisposition.DEFER),
            "blockedMissions": sum(1 for item in decisions if item.disposition == QueueDisposition.BLOCKED),
            "suspensionRecommendations": sum(1 for item in decisions if item.suspension_recommendation),
            "preemptionRecommendations": sum(1 for item in decisions if item.preemption_recommendation.startswith("recommend")),
            "inheritanceEvents": sum(1 for item in decisions if item.inheritance_applied),
            "starvationWarnings": sum(1 for item in decisions if self._deferrals.get(item.priority_candidate_id, 0) >= 3),
            "topMission": (decisions[0].mission_id or decisions[0].mission_plan_id) if decisions else "none",
            "topClass": decisions[0].effective_priority_class.value if decisions else "none",
            "schedulerAuthorityPreserved": True,
        }

    def _safety_precedence(self, decisions: tuple[PriorityDecision, ...]) -> dict[str, Any]:
        protected = tuple(item for item in decisions if item.effective_priority_class in self.policy.protected_safety_classes)
        discretionary = tuple(item for item in decisions if item.effective_priority_class not in self.policy.protected_safety_classes)
        return {
            "protectedClasses": tuple(item.value for item in self.policy.protected_safety_classes),
            "protectedMissionCount": len(protected),
            "highestProtectedRank": min((item.queue_rank for item in protected), default=0),
            "discretionaryAboveSafety": any(d.queue_rank < p.queue_rank for d in discretionary for p in protected),
            "numericScoreCanOverrideSafety": False,
            "doctrine": tuple(item.value for item in self.policy.class_order),
        }

    def _metrics(self, decisions: tuple[PriorityDecision, ...]) -> dict[str, Any]:
        return {
            "priorityDecisionsCreated": len(self._decisions),
            "queueSnapshotsCreated": len(self._queue_snapshots),
            "rankedMissions": len(decisions),
            "byClass": _count_by(decisions, lambda item: item.effective_priority_class.value),
            "byDisposition": _count_by(decisions, lambda item: item.disposition.value),
            "averageNormalizedScore": round(sum(item.normalized_score for item in decisions) / max(1, len(decisions)), 4),
            "priorityInversionsDetected": sum(1 for item in self._alerts if item.get("alertType") == "priority_inversion"),
            "deadlineMisses": sum(1 for item in decisions if "deadline_expired" in item.blocking_reasons),
            "schedulerDeviations": 0,
        }

    def _audit_event(self, action: str, record_id: str, reason: str) -> None:
        self._audit.append({"auditId": f"EPJ-AUD-{len(self._audit) + 1:06d}", "timestamp": utc_timestamp(), "action": action, "recordId": record_id, "reason": reason})

    def _dead_letter(self, record_id: str, reason_code: str, explanation: str) -> None:
        self._dead_letters.append({"deadLetterId": f"EPJ-DL-{len(self._dead_letters) + 1:06d}", "timestamp": utc_timestamp(), "recordId": record_id, "reasonCode": reason_code, "explanation": explanation})


def _default_policy() -> PriorityPolicy:
    order = (
        EnterprisePriorityClass.EMERGENCY_RECOVERY,
        EnterprisePriorityClass.POSITION_SAFETY,
        EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY,
        EnterprisePriorityClass.RISK_CONTROL,
        EnterprisePriorityClass.REQUIRED_LIFECYCLE_ACTION,
        EnterprisePriorityClass.COMMANDER_DIRECTED,
        EnterprisePriorityClass.TACTICAL_EVALUATION,
        EnterprisePriorityClass.STRATEGIC_INTELLIGENCE,
        EnterprisePriorityClass.HISTORICAL_REVIEW,
        EnterprisePriorityClass.CAPABILITY_DEVELOPMENT,
    )
    return PriorityPolicy(
        "EPJ-POLICY-001",
        1,
        order,
        {priority: float((len(order) - index) * 100) for index, priority in enumerate(order)},
        2.5,
        4.0,
        25.0,
        0.75,
        900,
        order[:5],
        utc_timestamp(),
        "",
    )


def _candidate_from_plan(plan: dict[str, Any]) -> PriorityCandidate:
    envelope = plan.get("resource_envelope", {}) or {}
    objective = plan.get("objective", {}) or {}
    priority = _priority_class(plan.get("priority_class"))
    source_event_ids = tuple(plan.get("source_trigger_ids", ()) or ())
    offices = tuple(item.get("office_id", "") for item in plan.get("office_assignments", ()) if item.get("office_id"))
    dependencies = tuple(item.get("upstream_node_id", "") for item in plan.get("dependencies", ()) if item.get("required"))
    text = f"{plan.get('mission_type', '')} {priority.value if priority else ''}".lower()
    mission_plan_id = str(plan.get("mission_plan_id", ""))
    return PriorityCandidate(
        f"EPJ-CAN-PLAN-{mission_plan_id or _short_hash(plan)}",
        "",
        mission_plan_id,
        int(plan.get("plan_version", 1) or 1),
        str(plan.get("mission_type", "")),
        str(plan.get("status", "draft")),
        str(objective.get("subject_type", "")),
        str(objective.get("subject_id", "")),
        "",
        "",
        "",
        source_event_ids,
        priority,
        str((plan.get("lineage") or {}).get("severity", "")),
        "immediate" if priority in {EnterprisePriorityClass.EMERGENCY_RECOVERY, EnterprisePriorityClass.POSITION_SAFETY, EnterprisePriorityClass.RISK_CONTROL} else "routine",
        "major" if priority in {EnterprisePriorityClass.EMERGENCY_RECOVERY, EnterprisePriorityClass.POSITION_SAFETY, EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY} else "material",
        str(plan.get("created_at", utc_timestamp())),
        str(objective.get("deadline_at", "")),
        "",
        int(envelope.get("runtime_ceiling_seconds", 0) or 0),
        float(envelope.get("estimated_cost_usd", 0) or 0),
        int(envelope.get("api_call_ceiling", 0) or 0),
        offices,
        dependencies,
        (),
        "position" in text,
        "order" in text or "broker" in text,
        priority in _default_policy().protected_safety_classes if priority else False,
        priority == EnterprisePriorityClass.COMMANDER_DIRECTED,
        0,
        str(plan.get("created_at", utc_timestamp())),
        PreemptionClass.PREEMPTIBLE_AT_CHECKPOINT if priority not in {EnterprisePriorityClass.EMERGENCY_RECOVERY, EnterprisePriorityClass.POSITION_SAFETY} else PreemptionClass.SAFETY_ONLY_PREEMPTIBLE,
        {"source": "EO-CD", "planStatus": str(plan.get("status", "")), "deltaDecision": plan.get("delta_decision", {})},
    )


def _candidate_from_mission(mission: dict[str, Any]) -> PriorityCandidate:
    priority = _priority_class_from_eos(str(mission.get("priority", "")))
    mission_id = str(mission.get("mission_id", ""))
    return PriorityCandidate(
        f"EPJ-CAN-MSN-{mission_id or _short_hash(mission)}",
        mission_id,
        str(mission.get("commander_directive_id", "")) if str(mission.get("commander_directive_id", "")).startswith("EMP-PLAN") else "",
        1,
        str(mission.get("workflow_type", mission.get("mission_type", ""))),
        str(mission.get("status", "")),
        "mission",
        mission_id,
        "",
        "",
        "",
        (),
        priority,
        str(mission.get("criticality", "")),
        "immediate" if priority in {EnterprisePriorityClass.EMERGENCY_RECOVERY, EnterprisePriorityClass.POSITION_SAFETY} else "routine",
        "material",
        str(mission.get("scheduled_start", mission.get("created_at", utc_timestamp()))),
        "",
        "",
        int(mission.get("maximum_runtime_seconds", 0) or 0),
        float(mission.get("maximum_api_cost", 0) or 0),
        int(mission.get("maximum_api_calls", 0) or 0),
        tuple(mission.get("required_offices", ()) or ()),
        (),
        (),
        priority == EnterprisePriorityClass.POSITION_SAFETY,
        priority == EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY,
        priority in _default_policy().protected_safety_classes,
        priority == EnterprisePriorityClass.COMMANDER_DIRECTED or str(mission.get("trigger_type", "")) == "Commander",
        0,
        str(mission.get("created_at", utc_timestamp())),
        PreemptionClass.NON_PREEMPTIBLE if str(mission.get("status", "")) == "Running" and priority in _default_policy().protected_safety_classes else PreemptionClass.PREEMPTIBLE_AT_CHECKPOINT,
        {"source": "EO-CA", "triggerType": str(mission.get("trigger_type", ""))},
    )


def _candidate_from_event(event: dict[str, Any]) -> PriorityCandidate:
    priority = _priority_class_for_event(event)
    event_id = str(event.get("event_id", event.get("eventId", "")))
    return PriorityCandidate(
        f"EPJ-CAN-EVT-{event_id or _short_hash(event)}",
        str(event.get("mission_id", "")),
        "",
        1,
        str(event.get("recommended_mission_type", event.get("event_type", ""))),
        "validated_event",
        str(event.get("subject_type", "")),
        str(event.get("subject_id", "")),
        str(event.get("ticker", "")),
        str(event.get("position_id", "")),
        str(event.get("order_id", "")),
        (event_id,),
        priority,
        str(event.get("severity", "")),
        str(event.get("urgency", "")),
        str(event.get("materiality", "")),
        str(event.get("validated_at", event.get("observed_at", utc_timestamp()))),
        str(event.get("expires_at", "")),
        str(event.get("expires_at", "")),
        int(event.get("estimated_time_sensitivity_seconds", 0) or 300),
        0.0,
        0,
        tuple(event.get("recommended_offices", ()) or ()),
        (),
        (),
        bool(event.get("position_id")) or priority == EnterprisePriorityClass.POSITION_SAFETY,
        bool(event.get("order_id")) or priority == EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY,
        priority in _default_policy().protected_safety_classes,
        priority == EnterprisePriorityClass.COMMANDER_DIRECTED,
        0,
        str(event.get("validated_at", event.get("observed_at", utc_timestamp()))),
        PreemptionClass.SAFETY_ONLY_PREEMPTIBLE if priority in _default_policy().protected_safety_classes else PreemptionClass.PREEMPTIBLE_AT_CHECKPOINT,
        {"source": "EO-CC", "eventType": str(event.get("event_type", "")), "financialExposure": event.get("financial_exposure"), "estimatedDownside": event.get("estimated_downside")},
    )


def _score_components(candidate: PriorityCandidate, assigned: EnterprisePriorityClass, effective: EnterprisePriorityClass, policy: PriorityPolicy, sources: dict[str, Any], aging: dict[str, Any], deferrals: int) -> PriorityScoreComponents:
    age_hours = max(0.0, (_parse_time(utc_timestamp()) - _parse_time(candidate.submitted_at)).total_seconds() / 3600)
    deadline_seconds = (_parse_time(candidate.deadline_at) - _parse_time(utc_timestamp())).total_seconds() if candidate.deadline_at else None
    cost_available = _budget_available(candidate, sources)
    office_available = _offices_available(candidate, sources)
    token_available = _token_available(sources)
    freshness = _freshness_score(candidate, sources)
    return PriorityScoreComponents(
        class_base_score=policy.base_scores.get(effective, 0.0),
        emergency_score=120.0 if effective == EnterprisePriorityClass.EMERGENCY_RECOVERY else 0.0,
        position_safety_score=100.0 if candidate.open_position_related or effective == EnterprisePriorityClass.POSITION_SAFETY else 0.0,
        broker_integrity_score=80.0 if candidate.active_order_related or effective == EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY else 0.0,
        ledger_integrity_score=70.0 if "ledger" in candidate.mission_type.lower() else 0.0,
        risk_score=65.0 if effective == EnterprisePriorityClass.RISK_CONTROL or "risk" in candidate.mission_type.lower() else 0.0,
        lifecycle_score=55.0 if effective == EnterprisePriorityClass.REQUIRED_LIFECYCLE_ACTION or "lifecycle" in candidate.mission_type.lower() or "exit" in candidate.mission_type.lower() else 0.0,
        commander_score=40.0 if candidate.commander_directed else 0.0,
        deadline_score=_deadline_score(deadline_seconds),
        urgency_score=_urgency_score(candidate.event_urgency),
        financial_exposure_score=_bounded_float(candidate.metadata.get("financialExposure"), 0, 75) if candidate.metadata.get("financialExposure") is not None else 0.0,
        downside_score=_bounded_float(candidate.metadata.get("estimatedDownside"), 0, 75) if candidate.metadata.get("estimatedDownside") is not None else 0.0,
        dependency_score=25.0 if candidate.dependency_mission_ids else 0.0,
        blocking_score=45.0 if candidate.dependent_mission_ids else 0.0,
        mission_age_score=min(policy.max_aging_within_class, age_hours * policy.aging_points_per_hour),
        starvation_score=20.0 if deferrals >= 3 or age_hours >= policy.starvation_threshold_hours else 0.0,
        completion_proximity_score=15.0 if candidate.mission_status.lower() == "running" and candidate.estimated_runtime_seconds <= 60 else 0.0,
        preemption_cost_score=-20.0 if candidate.preemption_class == PreemptionClass.NON_PREEMPTIBLE else 0.0,
        budget_availability_score=15.0 if cost_available else -35.0,
        office_availability_score=12.0 if office_available else -25.0,
        token_availability_score=10.0 if token_available else -20.0,
        freshness_score=freshness,
        duplication_penalty=-35.0 if _duplicate_hint(candidate, sources) else 0.0,
        excessive_cost_penalty=-25.0 if candidate.estimated_cost > policy.excessive_cost_threshold_usd and effective not in policy.protected_safety_classes else 0.0,
        long_runtime_penalty=-10.0 if candidate.estimated_runtime_seconds > policy.long_runtime_threshold_seconds and effective not in policy.protected_safety_classes else 0.0,
        low_confidence_penalty=-10.0 if "low_confidence" in json.dumps(candidate.metadata).lower() else 0.0,
        deferability_penalty=-20.0 if effective in {EnterprisePriorityClass.STRATEGIC_INTELLIGENCE, EnterprisePriorityClass.HISTORICAL_REVIEW, EnterprisePriorityClass.CAPABILITY_DEVELOPMENT} else 0.0,
        stale_input_penalty=-30.0 if freshness < 0 else 0.0,
        operating_mode_penalty=_operating_mode_penalty(candidate, effective, sources),
        policy_adjustment=50.0 if effective != assigned else 0.0,
        commander_adjustment=float(candidate.commander_priority_modifier),
    )


def _blockers(candidate: PriorityCandidate, sources: dict[str, Any]) -> tuple[str, ...]:
    blockers = []
    if candidate.expires_at and _parse_time(candidate.expires_at) < _parse_time(utc_timestamp()):
        blockers.append("candidate_expired")
    if candidate.deadline_at and _parse_time(candidate.deadline_at) < _parse_time(utc_timestamp()):
        blockers.append("deadline_expired")
    if not _budget_available(candidate, sources):
        blockers.append("budget_unavailable")
    if not _offices_available(candidate, sources):
        blockers.append("required_office_unavailable")
    if _freshness_score(candidate, sources) < 0:
        blockers.append("stale_or_unavailable_information")
    return tuple(blockers)


def _inheritance(candidate: PriorityCandidate, candidates: dict[str, PriorityCandidate]) -> tuple[EnterprisePriorityClass | None, str]:
    if not candidate.dependency_mission_ids:
        return None, ""
    protected_dependents = tuple(item for item in candidates.values() if (item.mission_id in candidate.dependent_mission_ids or item.mission_plan_id in candidate.dependent_mission_ids) and item.safety_critical)
    if protected_dependents and not candidate.safety_critical:
        source = protected_dependents[0]
        return _class_for(source), source.mission_id or source.mission_plan_id
    if any("broker" in dep.lower() or "ledger" in dep.lower() for dep in candidate.dependency_mission_ids):
        return EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY, "dependency_integrity_requirement"
    return None, ""


def _disposition_for(decision: PriorityDecision, rank: int) -> QueueDisposition:
    if "candidate_expired" in decision.blocking_reasons:
        return QueueDisposition.CANCEL_RECOMMENDED
    if decision.blocking_reasons and decision.effective_priority_class in {EnterprisePriorityClass.EMERGENCY_RECOVERY, EnterprisePriorityClass.POSITION_SAFETY, EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY, EnterprisePriorityClass.RISK_CONTROL}:
        return QueueDisposition.BLOCKED
    if rank == 1:
        return QueueDisposition.RUN_NOW
    if rank <= 3:
        return QueueDisposition.QUEUE_NEXT
    if decision.normalized_score < 35 or decision.effective_priority_class in {EnterprisePriorityClass.HISTORICAL_REVIEW, EnterprisePriorityClass.CAPABILITY_DEVELOPMENT}:
        return QueueDisposition.DEFER
    return QueueDisposition.QUEUE_NORMAL


def _scheduler_recommendation(decision: PriorityDecision, rank: int, disposition: QueueDisposition) -> dict[str, Any]:
    return {
        "rank": rank,
        "missionId": decision.mission_id,
        "missionPlanId": decision.mission_plan_id,
        "recommendation": disposition.value,
        "priorityClass": decision.effective_priority_class.value,
        "score": decision.normalized_score,
        "authorizesExecution": False,
        "transfersWorkflowToken": False,
        "reservesBudget": False,
        "reason": decision.explanation[0] if decision.explanation else "Ranked by EO-CJ deterministic policy.",
    }


def _preemption_recommendation(candidate: PriorityCandidate, priority: EnterprisePriorityClass, score: float, blockers: tuple[str, ...]) -> str:
    if blockers or candidate.preemption_class == PreemptionClass.NON_PREEMPTIBLE:
        return "reject_preemption_blocked_or_non_preemptible"
    if priority == EnterprisePriorityClass.EMERGENCY_RECOVERY and candidate.preemption_class in {PreemptionClass.IMMEDIATELY_PREEMPTIBLE, PreemptionClass.SAFETY_ONLY_PREEMPTIBLE}:
        return "recommend_immediate_preemption"
    if priority in {EnterprisePriorityClass.POSITION_SAFETY, EnterprisePriorityClass.RISK_CONTROL} and score >= 900:
        return "recommend_checkpoint_preemption"
    return "no_preemption_required"


def _suspension_recommendation(candidate: PriorityCandidate, priority: EnterprisePriorityClass, blockers: tuple[str, ...]) -> str:
    if blockers and priority not in _default_policy().protected_safety_classes:
        return "recommend_suspend_until_blocker_clears"
    return ""


def _merge_recommendation(candidate: PriorityCandidate, candidates: dict[str, PriorityCandidate]) -> str:
    matches = [item for item in candidates.values() if item.priority_candidate_id != candidate.priority_candidate_id and item.subject_id and item.subject_id == candidate.subject_id and item.mission_type == candidate.mission_type]
    return "recommend_merge_duplicate_subject_scope" if matches else ""


def _reduction_recommendation(candidate: PriorityCandidate, sources: dict[str, Any]) -> str:
    if candidate.estimated_cost > _default_policy().excessive_cost_threshold_usd and not candidate.safety_critical:
        return "recommend_reduce_scope_or_use_cache"
    cache = sources.get("enterpriseMemoryCache") or {}
    if (cache.get("latestRetrieval") or {}).get("exact_reuse_record_ids"):
        return "recommend_cache_reuse_scope_reduction"
    return ""


def _explanation(candidate: PriorityCandidate, assigned: EnterprisePriorityClass, effective: EnterprisePriorityClass, components: PriorityScoreComponents, blockers: tuple[str, ...], inherited_from: str) -> tuple[str, ...]:
    lines = [
        f"{candidate.mission_id or candidate.mission_plan_id or candidate.priority_candidate_id} is {effective.value} because safety doctrine rank {_class_rank(effective)} applies before numeric score.",
        f"Score combines class base {components.class_base_score:.1f}, urgency {components.urgency_score:.1f}, deadline {components.deadline_score:.1f}, resources {components.budget_availability_score + components.office_availability_score + components.token_availability_score:.1f}, aging {components.mission_age_score + components.starvation_score:.1f}.",
    ]
    if effective != assigned:
        lines.append(f"Priority inheritance elevated {assigned.value} to {effective.value} from {inherited_from}.")
    if blockers:
        lines.append(f"Execution is blocked by {', '.join(blockers)}; EO-CJ keeps the mission visible but does not bypass authority.")
    if candidate.safety_critical:
        lines.append("Safety-critical work is protected from starvation and cannot be outranked by discretionary research.")
    return tuple(lines)


def _priority_class(value: Any) -> EnterprisePriorityClass | None:
    if isinstance(value, EnterprisePriorityClass):
        return value
    normalized = str(value or "").replace(" ", "_").replace("-", "_").lower()
    aliases = {
        "emergency": EnterprisePriorityClass.EMERGENCY_RECOVERY,
        "emergency_recovery": EnterprisePriorityClass.EMERGENCY_RECOVERY,
        "position_safety": EnterprisePriorityClass.POSITION_SAFETY,
        "broker_ledger_integrity": EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY,
        "broker_and_ledger_reconciliation": EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY,
        "risk_control": EnterprisePriorityClass.RISK_CONTROL,
        "required_trade_lifecycle_action": EnterprisePriorityClass.REQUIRED_LIFECYCLE_ACTION,
        "required_lifecycle_action": EnterprisePriorityClass.REQUIRED_LIFECYCLE_ACTION,
        "commander_directed": EnterprisePriorityClass.COMMANDER_DIRECTED,
        "tactical_evaluation": EnterprisePriorityClass.TACTICAL_EVALUATION,
        "tactical_opportunity_evaluation": EnterprisePriorityClass.TACTICAL_EVALUATION,
        "strategic_intelligence": EnterprisePriorityClass.STRATEGIC_INTELLIGENCE,
        "historical_review": EnterprisePriorityClass.HISTORICAL_REVIEW,
        "academy_and_development": EnterprisePriorityClass.CAPABILITY_DEVELOPMENT,
        "capability_development": EnterprisePriorityClass.CAPABILITY_DEVELOPMENT,
    }
    if normalized in aliases:
        return aliases[normalized]
    try:
        return EnterprisePriorityClass(normalized)
    except ValueError:
        return None


def _priority_class_from_eos(value: str) -> EnterprisePriorityClass:
    return _priority_class(value) or EnterprisePriorityClass.TACTICAL_EVALUATION


def _priority_class_for_event(event: dict[str, Any]) -> EnterprisePriorityClass:
    text = f"{event.get('domain', '')} {event.get('event_type', '')} {event.get('recommended_mission_type', '')} {event.get('severity', '')}".lower()
    if "emergency" in text or "health" in text:
        return EnterprisePriorityClass.EMERGENCY_RECOVERY
    if "position" in text or "stop" in text:
        return EnterprisePriorityClass.POSITION_SAFETY
    if "broker" in text or "order" in text or "ledger" in text:
        return EnterprisePriorityClass.BROKER_LEDGER_INTEGRITY
    if "risk" in text:
        return EnterprisePriorityClass.RISK_CONTROL
    if "commander" in text:
        return EnterprisePriorityClass.COMMANDER_DIRECTED
    if "strategic" in text or "intelligence" in text:
        return EnterprisePriorityClass.STRATEGIC_INTELLIGENCE
    return EnterprisePriorityClass.TACTICAL_EVALUATION


def _class_for(candidate: PriorityCandidate) -> EnterprisePriorityClass:
    return candidate.requested_priority_class or _priority_class_for_event(candidate.metadata) or EnterprisePriorityClass.TACTICAL_EVALUATION


def _class_rank(priority: EnterprisePriorityClass) -> int:
    order = _default_policy().class_order
    return order.index(priority) + 1 if priority in order else 99


def _more_protective(a: EnterprisePriorityClass, b: EnterprisePriorityClass) -> EnterprisePriorityClass:
    return a if _class_rank(a) <= _class_rank(b) else b


def _component_total(components: PriorityScoreComponents) -> float:
    return sum(float(value) for value in asdict(components).values())


def _deadline_score(seconds: float | None) -> float:
    if seconds is None:
        return 0.0
    if seconds < 0:
        return 90.0
    if seconds <= 300:
        return 80.0
    if seconds <= 1800:
        return 45.0
    if seconds <= 7200:
        return 20.0
    return 0.0


def _urgency_score(value: str) -> float:
    return {"emergency": 90.0, "immediate": 70.0, "prompt": 35.0, "routine": 10.0, "deferred": 0.0}.get(str(value or "").lower(), 5.0)


def _budget_available(candidate: PriorityCandidate, sources: dict[str, Any]) -> bool:
    governor = sources.get("enterpriseCostGovernor") or {}
    metrics = governor.get("metrics", {}) or {}
    if candidate.safety_critical and float(metrics.get("safetyReserveRemaining", 0) or 0) > 0:
        return True
    allocation = governor.get("budgetAllocation", {}) or {}
    return float(allocation.get("available", 999) or 0) >= max(0.0, candidate.estimated_cost)


def _offices_available(candidate: PriorityCandidate, sources: dict[str, Any]) -> bool:
    offices = tuple(sources.get("offices", ()) or ())
    if not candidate.mandatory_offices or not offices:
        return True
    states = {office.get("office"): office.get("status") for group in offices for office in group.get("officeStates", group.get("offices", ())) if isinstance(office, dict)}
    return all(states.get(office, "AVAILABLE") not in {"FAULTED", "OFFLINE"} for office in candidate.mandatory_offices)


def _token_available(sources: dict[str, Any]) -> bool:
    integrity = ((sources.get("workflowRuntimeMonitor") or {}).get("tokenIntegrity") or {}).get("status", "VALID")
    return str(integrity).upper() in {"VALID", "HEALTHY", "NOMINAL", ""}


def _freshness_score(candidate: PriorityCandidate, sources: dict[str, Any]) -> float:
    freshness = sources.get("informationFreshnessEngine") or {}
    at_risk = tuple(freshness.get("staleAndAtRiskInformation", ()) or ())
    subject = candidate.subject_id or candidate.ticker or candidate.position_id or candidate.order_id
    if subject and any(subject in json.dumps(item, default=str) for item in at_risk):
        return -35.0
    return 5.0


def _duplicate_hint(candidate: PriorityCandidate, sources: dict[str, Any]) -> bool:
    planner = sources.get("enterpriseMissionPlanner") or {}
    return any(candidate.mission_plan_id and candidate.mission_plan_id in json.dumps(item, default=str) for item in planner.get("mergeRecords", ()) or ())


def _operating_mode_penalty(candidate: PriorityCandidate, priority: EnterprisePriorityClass, sources: dict[str, Any]) -> float:
    mode = str((sources.get("enterpriseOperationsScheduler") or {}).get("currentOperatingMode", "")).lower()
    if "halted" in mode and priority != EnterprisePriorityClass.EMERGENCY_RECOVERY:
        return -80.0
    if "strategic research only" in mode and priority in {EnterprisePriorityClass.TACTICAL_EVALUATION, EnterprisePriorityClass.REQUIRED_LIFECYCLE_ACTION}:
        return -35.0
    if "position management only" in mode and priority == EnterprisePriorityClass.TACTICAL_EVALUATION:
        return -55.0
    return 0.0


def _bounded_float(value: Any, minimum: float, maximum: float) -> float:
    try:
        parsed = abs(float(value))
    except (TypeError, ValueError):
        return 0.0
    return max(minimum, min(maximum, parsed))


def _queue_row(decision: PriorityDecision) -> dict[str, Any]:
    return {
        "rank": decision.queue_rank,
        "decisionId": decision.priority_decision_id,
        "candidateId": decision.priority_candidate_id,
        "missionId": decision.mission_id,
        "missionPlanId": decision.mission_plan_id,
        "priorityClass": decision.effective_priority_class.value,
        "score": decision.normalized_score,
        "status": decision.status.value,
        "disposition": decision.disposition.value,
        "preemption": decision.preemption_recommendation,
        "blocked": decision.blocking_reasons,
        "reason": decision.explanation[0] if decision.explanation else "",
    }


def _score_row(decision: PriorityDecision) -> dict[str, Any]:
    return {"decisionId": decision.priority_decision_id, "mission": decision.mission_id or decision.mission_plan_id, "components": _public(decision.score_components), "rawScore": decision.raw_score, "normalizedScore": decision.normalized_score}


def _inheritance_row(decision: PriorityDecision) -> dict[str, Any]:
    return {"decisionId": decision.priority_decision_id, "mission": decision.mission_id or decision.mission_plan_id, "effectiveClass": decision.effective_priority_class.value, "inheritedFrom": decision.inherited_from_mission_id, "reason": "Required dependency elevated by protected mission."}


def _preemption_row(decision: PriorityDecision) -> dict[str, Any]:
    return {"decisionId": decision.priority_decision_id, "mission": decision.mission_id or decision.mission_plan_id, "preemptionClass": decision.preemption_class.value, "recommendation": decision.preemption_recommendation, "safe": not decision.preemption_recommendation.startswith("reject")}


def _aging_row(decision: PriorityDecision, aging: dict[str, Any], deferrals: int) -> dict[str, Any]:
    return {"decisionId": decision.priority_decision_id, "mission": decision.mission_id or decision.mission_plan_id, "firstSeenAt": aging.get("firstSeenAt", ""), "deferrals": deferrals, "agingScore": decision.score_components.mission_age_score, "starvationScore": decision.score_components.starvation_score, "safetyLimitsAging": decision.effective_priority_class in _default_policy().protected_safety_classes}


def _resource_row(decision: PriorityDecision) -> dict[str, Any]:
    components = decision.score_components
    return {"decisionId": decision.priority_decision_id, "mission": decision.mission_id or decision.mission_plan_id, "budgetScore": components.budget_availability_score, "officeScore": components.office_availability_score, "tokenScore": components.token_availability_score, "freshnessScore": components.freshness_score, "reductionRecommendation": decision.reduction_recommendation}


def _hash_policy(policy: PriorityPolicy) -> PriorityPolicy:
    return replace(policy, content_hash=_hash(_public(replace(policy, content_hash=""))))


def _hash_decision(decision: PriorityDecision) -> PriorityDecision:
    return replace(decision, content_hash=_hash(_public(replace(decision, content_hash=""))))


def _hash_queue(snapshot: PriorityQueueSnapshot) -> PriorityQueueSnapshot:
    return replace(snapshot, content_hash=_hash(_public(replace(snapshot, content_hash=""))))


def _hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _short_hash(value: Any) -> str:
    return _hash(value)[:12].upper()


def _public(item: Any) -> dict[str, Any]:
    raw = asdict(item) if hasattr(item, "__dataclass_fields__") else item
    return _json_value(raw)


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return tuple(_json_value(item) for item in value)
    if isinstance(value, dict):
        return {str(_json_value(key)): _json_value(item) for key, item in value.items()}
    return value


def _candidate_time(candidate: PriorityCandidate | None) -> str:
    return candidate.submitted_at if candidate else utc_timestamp()


def _parse_time(value: str) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(UTC)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _count_by(items: tuple[PriorityDecision, ...], key_fn: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items:
        key = key_fn(item)
        out[key] = out.get(key, 0) + 1
    return out


def _candidate_from_public(item: dict[str, Any]) -> PriorityCandidate:
    data = dict(item)
    data["requested_priority_class"] = _priority_class(data.get("requested_priority_class")) if data.get("requested_priority_class") else None
    data["source_event_ids"] = tuple(data.get("source_event_ids", ()))
    data["mandatory_offices"] = tuple(data.get("mandatory_offices", ()))
    data["dependency_mission_ids"] = tuple(data.get("dependency_mission_ids", ()))
    data["dependent_mission_ids"] = tuple(data.get("dependent_mission_ids", ()))
    data["preemption_class"] = PreemptionClass(data.get("preemption_class", PreemptionClass.PREEMPTIBLE_AT_CHECKPOINT.value))
    return PriorityCandidate(**{key: data.get(key) for key in PriorityCandidate.__dataclass_fields__})


def _decision_from_public(item: dict[str, Any]) -> PriorityDecision:
    data = dict(item)
    data["assigned_priority_class"] = EnterprisePriorityClass(data["assigned_priority_class"])
    data["effective_priority_class"] = EnterprisePriorityClass(data["effective_priority_class"])
    data["score_components"] = PriorityScoreComponents(**data["score_components"])
    data["status"] = PriorityDecisionStatus(data["status"])
    data["disposition"] = QueueDisposition(data["disposition"])
    data["preemption_class"] = PreemptionClass(data["preemption_class"])
    data["blocking_reasons"] = tuple(data.get("blocking_reasons", ()))
    data["explanation"] = tuple(data.get("explanation", ()))
    return PriorityDecision(**{key: data.get(key) for key in PriorityDecision.__dataclass_fields__})


def _queue_from_public(item: dict[str, Any]) -> PriorityQueueSnapshot:
    data = dict(item)
    for key in ("ranked_decision_ids", "run_now_decision_ids", "queued_decision_ids", "deferred_decision_ids", "suspended_decision_ids", "blocked_decision_ids"):
        data[key] = tuple(data.get(key, ()))
    return PriorityQueueSnapshot(**{key: data.get(key) for key in PriorityQueueSnapshot.__dataclass_fields__})
