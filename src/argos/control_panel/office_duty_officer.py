"""Office Duty Officer framework for deterministic ARGOS office triage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .ecc import ORGANIZATION_OFFICES


DISPOSITIONS = (
    "Ignore",
    "Reject",
    "Return for Correction",
    "Queue",
    "Defer",
    "Route",
    "Answer From Cache",
    "Resolve Locally",
    "Escalate",
    "Recommend Wake",
    "Emergency Wake Request",
    "Already In Progress",
    "Duplicate Suppressed",
    "Expired",
    "Prohibited by Operating Mode",
    "Prohibited by Budget",
    "Prohibited by Cooldown",
    "Prohibited by Market Session",
)


@dataclass(frozen=True)
class CapabilityProfile:
    """Configuration-driven description of one duty officer's mandate."""

    profile_id: str
    office_id: str
    office_mission: str
    supported_request_types: tuple[str, ...]
    unsupported_request_types: tuple[str, ...]
    accepted_input_artifacts: tuple[str, ...]
    produced_output_artifacts: tuple[str, ...]
    required_dependencies: tuple[str, ...]
    required_data_freshness_minutes: int
    default_priority: str
    typical_activation_cost: float
    typical_runtime_seconds: int
    maximum_queue_depth: int
    cooldown_seconds: int
    operating_mode_permissions: tuple[str, ...]
    market_session_requirements: tuple[str, ...]
    emergency_wake_conditions: tuple[str, ...]
    cache_reuse_minutes: int
    duplicate_suppression_seconds: int
    escalation_destinations: tuple[str, ...]
    routing_destinations: dict[str, str]
    activation_threshold: int


@dataclass(frozen=True)
class OfficeDutyOfficer:
    """Canonical lightweight sentry for a parent office."""

    duty_officer_id: str
    office_id: str
    office_name: str
    office_type: str
    capability_profile: dict[str, Any]
    current_status: str
    operating_mode: str
    last_heartbeat: str
    queue_depth: int
    active_mission_id: str
    office_health: str
    office_wake_cost_estimate: float
    office_runtime_estimate: int
    daily_activation_count: int
    daily_cost_incurred: float
    cooldown_until: str
    last_wake_time: str
    last_sleep_time: str
    configuration_version: str
    audit_reference: str


@dataclass(frozen=True)
class OfficeTaskingRequest:
    """Canonical incoming request evaluated by an Office Duty Officer."""

    request_id: str
    created_at: str
    source_office_id: str
    target_office_id: str
    mission_id: str
    workflow_id: str
    decision_object_id: str
    execution_token_id: str
    request_type: str
    task_description: str
    priority: str
    criticality: str
    deadline: str
    event_reference: str
    commander_directive_id: str
    required_output: str
    input_artifacts: tuple[str, ...]
    freshness_requirement: str
    estimated_value: float
    estimated_cost: float
    deduplication_key: str
    routing_history: tuple[str, ...]
    authorization_context: dict[str, Any]
    status: str
    audit_reference: str


@dataclass(frozen=True)
class DutyOfficerDecision:
    """Canonical auditable decision for one duty officer request."""

    decision_id: str
    request_id: str
    office_id: str
    disposition: str
    timestamp: str
    reason_code: str
    explanation: str
    rules_evaluated: tuple[str, ...]
    relevant_office_state: dict[str, Any]
    relevant_mission_state: dict[str, Any]
    relevant_budget_state: dict[str, Any]
    relevant_freshness_state: dict[str, Any]
    duplicate_reference: str
    cache_reference: str
    routing_destination: str
    escalation_destination: str
    wake_recommendation: bool
    estimated_activation_cost: float
    expected_operational_value: float
    wake_justification_score: int
    confidence: float
    audit_record: str


class OfficeDutyOfficerRegistry:
    """Register duty officers and evaluate tasking before full office wake."""

    def __init__(self) -> None:
        self._profiles = _default_profiles()
        self._requests: dict[str, OfficeTaskingRequest] = {}
        self._decisions: list[DutyOfficerDecision] = []
        self._queues: dict[str, list[str]] = {office_id: [] for office_id in self._profiles}
        self._cooldowns: dict[str, str] = {}
        self._cache: dict[str, dict[str, Any]] = _seed_cache()
        self._manual_overrides: list[dict[str, Any]] = []
        self._recoveries: list[dict[str, Any]] = []
        self.enabled = True
        self.intake_paused = False

    def snapshot(self, eos: dict[str, Any] | None = None, offices: tuple[dict[str, Any], ...] = ()) -> dict[str, Any]:
        """Return Enterprise Operations Bridge payload for all duty officers."""
        eos = eos or {}
        roster = tuple(self._duty_officer_view(office_id, eos, offices) for office_id in sorted(self._profiles))
        pending = tuple(asdict(self._requests[request_id]) for queue in self._queues.values() for request_id in queue if request_id in self._requests)
        decisions = tuple(asdict(decision) for decision in self._decisions)
        return {
            "frameworkName": "Office Duty Officer",
            "engineeringOrder": "EO-CB",
            "enabled": self.enabled,
            "intakePaused": self.intake_paused,
            "enterpriseDutyRoster": roster,
            "pendingRequests": pending,
            "wakeRecommendations": tuple(item for item in decisions if item["wake_recommendation"]),
            "suppressedWork": tuple(item for item in decisions if item["disposition"] in {"Duplicate Suppressed", "Answer From Cache", "Resolve Locally", "Route", "Defer", "Reject", "Prohibited by Cooldown", "Prohibited by Operating Mode", "Prohibited by Budget"}),
            "auditDetail": decisions[-25:],
            "capabilityProfiles": tuple(asdict(profile) for profile in self._profiles.values()),
            "metrics": self._metrics(),
            "lawVII": {
                "bypassesScheduler": False,
                "bypassesWorkflowExecutionToken": False,
                "selfAuthorizesFullOfficeWake": False,
                "uncontrolledLoopsCreated": False,
                "routineTriageUsesAi": False,
            },
            "apiGatewayPolicy": {
                "routineExternalAiAllowed": False,
                "futureDutyOfficerContextRequired": True,
                "tracksDutyOfficerCostSeparately": True,
            },
            "futureIntegrationPoints": (
                "EO-CC Event Detection Engine",
                "EO-CF Information Freshness Engine",
                "EO-CG Enterprise Memory Cache",
                "EO-CH Workflow Delta Engine",
                "EO-CI Office Wakefulness Manager",
            ),
            "manualOverrides": tuple(self._manual_overrides),
            "recoveryRecords": tuple(self._recoveries),
        }

    def submit_request(self, request: OfficeTaskingRequest | dict[str, Any], eos: dict[str, Any] | None = None) -> DutyOfficerDecision:
        """Evaluate a tasking request and record the least expensive valid disposition."""
        if isinstance(request, dict):
            request = self._request_from_dict(request)
        if self.intake_paused:
            decision = self._decision(request, "Defer", "Intake Paused", "Duty Officer intake is paused by Commander.", ("intake",), eos=eos)
            self._record_request(request, decision)
            return decision
        profile = self._profiles.get(request.target_office_id)
        if not profile:
            routed = _best_route(request.target_office_id, self._profiles)
            decision = self._decision(request, "Route" if routed else "Reject", "Outside office mandate", "Target office is not registered; request is routed when a safe destination exists.", ("profile",), routing_destination=routed, eos=eos)
            self._record_request(request, decision)
            return decision

        hard = self._hard_rule(request, profile, eos or {})
        if hard:
            decision = hard
            self._record_request(request, decision)
            return decision

        duplicate = self._duplicate_reference(request, profile)
        if duplicate:
            decision = self._decision(request, "Duplicate Suppressed", "Identical request already queued", "An identical request is already queued or recently completed.", ("duplicate",), duplicate_reference=duplicate, eos=eos)
            self._record_request(request, decision)
            return decision

        cache = self._cache_hit(request, profile)
        if cache:
            decision = self._decision(request, "Answer From Cache", "Existing product remains fresh", "A fresh approved local product satisfies this request without waking the parent office.", ("cache", "freshness"), cache_reference=cache["cache_id"], eos=eos)
            self._record_request(request, decision)
            return decision

        route = self._routing_destination(request, profile)
        if route:
            decision = self._decision(request, "Route", "Better suited to another office", "Request belongs to another duty officer profile.", ("relevance", "routing"), routing_destination=route, eos=eos)
            self._record_request(request, decision)
            return decision
        cooldown_until = self._cooldowns.get(request.target_office_id, "")
        if cooldown_until and _parse_time(cooldown_until) > _parse_time(utc_timestamp()) and request.criticality not in {"Emergency", "Critical", "Position Safety"}:
            decision = self._decision(request, "Prohibited by Cooldown", "Office cooldown active", "Request is consolidated during parent-office cooldown.", ("cooldown",), eos=eos)
            self._record_request(request, decision)
            return decision

        score, rules = _wake_score(request, profile, eos or {})
        if score >= 85 or request.criticality in {"Emergency", "Critical"}:
            decision = self._decision(request, "Emergency Wake Request", "Emergency Commander tasking" if request.commander_directive_id else "Position safety event", "Hard safety or emergency priority justifies immediate scheduler escalation.", rules, wake=True, score=score, eos=eos)
        elif score >= profile.activation_threshold:
            decision = self._decision(request, "Recommend Wake", "Expected value exceeds activation threshold", "Duty Officer recommends scheduler-authorized parent-office wake.", rules, wake=True, score=score, eos=eos)
        elif score >= 45:
            decision = self._decision(request, "Queue", "Prepare for scheduled wake", "Request is valid but should be batched for a scheduled wake.", rules, score=score, eos=eos)
        else:
            decision = self._decision(request, "Defer", "Nonurgent work deferred", "Request is valid but does not justify immediate activation.", rules, score=score, eos=eos)
        self._record_request(request, decision)
        return decision

    def set_enabled(self, office_id: str, enabled: bool, actor: str = "Commander") -> None:
        if office_id not in self._profiles:
            raise ValueError(f"unknown duty officer: {office_id}")
        self._manual_overrides.append({"override_id": f"ODO-OVR-{len(self._manual_overrides) + 1:06d}", "timestamp": utc_timestamp(), "office_id": office_id, "action": "enable" if enabled else "disable", "actor": actor})

    def recover_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        for item in snapshot.get("pendingRequests", ()):
            request = self._request_from_dict(item)
            if request.status not in {"Resolved", "Rejected", "Expired"}:
                self._requests[request.request_id] = request
                self._queues.setdefault(request.target_office_id, []).append(request.request_id)
        self._recoveries.append({"recovery_id": f"ODO-REC-{len(self._recoveries) + 1:06d}", "timestamp": utc_timestamp(), "pending_requests_restored": len(self._requests)})

    def _hard_rule(self, request: OfficeTaskingRequest, profile: CapabilityProfile, eos: dict[str, Any]) -> DutyOfficerDecision | None:
        if not request.mission_id:
            return self._decision(request, "Reject", "Missing mission authorization", "Requests lacking mission authorization cannot wake an office.", ("authorization",), eos=eos)
        mission = _mission_state(request.mission_id, eos)
        if not mission:
            return self._decision(request, "Reject", "Invalid mission", "Request mission is not known to EOS.", ("authorization",), eos=eos)
        if not request.execution_token_id:
            return self._decision(request, "Reject", "Invalid execution token", "Workflow Execution Token context is required before wake recommendation.", ("law_vii",), eos=eos)
        mode = eos.get("currentOperatingMode", "Observation Only")
        if mode not in profile.operating_mode_permissions:
            return self._decision(request, "Prohibited by Operating Mode", "Invalid operating mode", f"{profile.office_id} is not permitted in {mode}.", ("operating_mode",), eos=eos)
        if request.request_type in profile.unsupported_request_types or request.request_type not in profile.supported_request_types:
            return self._decision(request, "Return for Correction", "Unsupported workflow type", "Request type is outside this office capability profile.", ("relevance",), eos=eos)
        if request.estimated_cost > float((eos.get("missionCostMonitor") or {}).get("remainingDailyBudgetUsd", 0.0)):
            return self._decision(request, "Prohibited by Budget", "Mission budget exhausted", "Remaining EOS budget cannot support this activation.", ("budget",), eos=eos)
        if _deadline_expired(request.deadline):
            return self._decision(request, "Expired", "Deadline expired", "Request deadline has expired.", ("timing",), eos=eos)
        return None

    def _record_request(self, request: OfficeTaskingRequest, decision: DutyOfficerDecision) -> None:
        self._requests[request.request_id] = replace(request, status=decision.disposition)
        self._decisions.append(decision)
        if decision.disposition in {"Queue", "Defer"}:
            queue = self._queues.setdefault(request.target_office_id, [])
            if request.request_id not in queue:
                queue.append(request.request_id)
                queue.sort(key=lambda item: (_priority_rank(self._requests[item].priority), self._requests[item].deadline or "9999"))
        if decision.wake_recommendation:
            self._cooldowns[request.target_office_id] = (_parse_time(utc_timestamp()) + timedelta(seconds=self._profiles[request.target_office_id].cooldown_seconds)).isoformat().replace("+00:00", "Z")

    def _request_from_dict(self, item: dict[str, Any]) -> OfficeTaskingRequest:
        timestamp = item.get("created_at") or utc_timestamp()
        request_id = item.get("request_id") or f"ODO-REQ-{len(self._requests) + 1:06d}"
        dedup = item.get("deduplication_key") or _dedup_key(item)
        return OfficeTaskingRequest(
            request_id=request_id,
            created_at=timestamp,
            source_office_id=str(item.get("source_office_id", item.get("sourceOfficeId", "Commander"))),
            target_office_id=str(item.get("target_office_id", item.get("targetOfficeId", ""))),
            mission_id=str(item.get("mission_id", item.get("missionId", ""))),
            workflow_id=str(item.get("workflow_id", item.get("workflowId", ""))),
            decision_object_id=str(item.get("decision_object_id", item.get("decisionObjectId", ""))),
            execution_token_id=str(item.get("execution_token_id", item.get("executionTokenId", ""))),
            request_type=str(item.get("request_type", item.get("requestType", "general_review"))),
            task_description=str(item.get("task_description", item.get("taskDescription", ""))),
            priority=str(item.get("priority", "Normal")),
            criticality=str(item.get("criticality", "Normal")),
            deadline=str(item.get("deadline", "")),
            event_reference=str(item.get("event_reference", item.get("eventReference", ""))),
            commander_directive_id=str(item.get("commander_directive_id", item.get("commanderDirectiveId", ""))),
            required_output=str(item.get("required_output", item.get("requiredOutput", ""))),
            input_artifacts=tuple(item.get("input_artifacts", item.get("inputArtifacts", ())) or ()),
            freshness_requirement=str(item.get("freshness_requirement", item.get("freshnessRequirement", "PT30M"))),
            estimated_value=float(item.get("estimated_value", item.get("estimatedValue", 50.0))),
            estimated_cost=float(item.get("estimated_cost", item.get("estimatedCost", 0.01))),
            deduplication_key=dedup,
            routing_history=tuple(item.get("routing_history", item.get("routingHistory", ())) or ()),
            authorization_context=dict(item.get("authorization_context", item.get("authorizationContext", {})) or {}),
            status=str(item.get("status", "Received")),
            audit_reference=str(item.get("audit_reference", item.get("auditReference", f"ODO-AUDIT-{len(self._decisions) + 1:06d}"))),
        )

    def _decision(
        self,
        request: OfficeTaskingRequest,
        disposition: str,
        reason_code: str,
        explanation: str,
        rules: tuple[str, ...],
        *,
        duplicate_reference: str = "",
        cache_reference: str = "",
        routing_destination: str = "",
        wake: bool = False,
        score: int | None = None,
        eos: dict[str, Any] | None = None,
    ) -> DutyOfficerDecision:
        profile = self._profiles.get(request.target_office_id)
        estimated_cost = request.estimated_cost or (profile.typical_activation_cost if profile else 0.0)
        value = request.estimated_value
        wake_score = int(score if score is not None else max(0, min(100, value - (estimated_cost * 100))))
        return DutyOfficerDecision(
            decision_id=f"ODO-DEC-{len(self._decisions) + 1:06d}",
            request_id=request.request_id,
            office_id=request.target_office_id,
            disposition=disposition,
            timestamp=utc_timestamp(),
            reason_code=reason_code,
            explanation=explanation,
            rules_evaluated=rules,
            relevant_office_state={"queueDepth": len(self._queues.get(request.target_office_id, ())), "cooldownUntil": self._cooldowns.get(request.target_office_id, "")},
            relevant_mission_state=_mission_state(request.mission_id, eos or {}),
            relevant_budget_state=(eos or {}).get("missionCostMonitor", {}),
            relevant_freshness_state=dict(request.authorization_context.get("freshnessEvaluation", {})) or {"freshnessRequirement": request.freshness_requirement, "policy": "timestamp_fallback"},
            duplicate_reference=duplicate_reference,
            cache_reference=cache_reference,
            routing_destination=routing_destination,
            escalation_destination=_escalation_destination(request, profile),
            wake_recommendation=wake,
            estimated_activation_cost=round(estimated_cost, 4),
            expected_operational_value=round(value, 2),
            wake_justification_score=wake_score,
            confidence=0.94 if disposition in {"Reject", "Duplicate Suppressed", "Answer From Cache"} else 0.82,
            audit_record=f"ODO-AUDIT-{len(self._decisions) + 1:06d}",
        )

    def _duplicate_reference(self, request: OfficeTaskingRequest, profile: CapabilityProfile) -> str:
        now = _parse_time(utc_timestamp())
        for prior in self._requests.values():
            if prior.deduplication_key != request.deduplication_key:
                continue
            age = (now - _parse_time(prior.created_at)).total_seconds()
            if age <= profile.duplicate_suppression_seconds:
                return prior.request_id
        return ""

    def _cache_hit(self, request: OfficeTaskingRequest, profile: CapabilityProfile) -> dict[str, Any]:
        cache = self._cache.get(f"{request.target_office_id}:{request.request_type}")
        if not cache:
            return {}
        age = (_parse_time(utc_timestamp()) - _parse_time(cache["created_at"])).total_seconds() / 60
        return cache if age <= profile.cache_reuse_minutes and not cache.get("contradictory_event") else {}

    def _routing_destination(self, request: OfficeTaskingRequest, profile: CapabilityProfile) -> str:
        if len(request.routing_history) >= 4:
            return "Executive"
        return profile.routing_destinations.get(request.request_type, "")

    def _duty_officer_view(self, office_id: str, eos: dict[str, Any], offices: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        profile = self._profiles[office_id]
        office = _office_state(office_id, offices)
        last_decision = next((decision for decision in reversed(self._decisions) if decision.office_id == office_id), None)
        return asdict(
            OfficeDutyOfficer(
                duty_officer_id=f"ODO-{office_id.upper().replace(' ', '-')}",
                office_id=office_id,
                office_name=office_id,
                office_type="Cognitive" if office_id not in {"Executive", "Trader", "Risk"} else "Operational",
                capability_profile=asdict(profile),
                current_status="Monitoring" if self.enabled else "Disabled",
                operating_mode=eos.get("currentOperatingMode", "Observation Only"),
                last_heartbeat=utc_timestamp(),
                queue_depth=len(self._queues.get(office_id, ())),
                active_mission_id=office.get("assignedMission", ""),
                office_health="Healthy" if office.get("currentState", "Sleeping") != "Faulted" else "Faulted",
                office_wake_cost_estimate=profile.typical_activation_cost,
                office_runtime_estimate=profile.typical_runtime_seconds,
                daily_activation_count=sum(1 for decision in self._decisions if decision.office_id == office_id and decision.wake_recommendation),
                daily_cost_incurred=round(sum(decision.estimated_activation_cost for decision in self._decisions if decision.office_id == office_id and decision.wake_recommendation), 4),
                cooldown_until=self._cooldowns.get(office_id, ""),
                last_wake_time=last_decision.timestamp if last_decision and last_decision.wake_recommendation else "",
                last_sleep_time=office.get("last_transition_utc", ""),
                configuration_version="ODO-CB-1.0",
                audit_reference=f"ODO-AUDIT-{office_id.upper().replace(' ', '-')}",
            )
        )

    def _metrics(self) -> dict[str, Any]:
        decisions = self._decisions
        return {
            "requestsReceived": len(self._requests),
            "requestsValidated": sum(1 for item in decisions if item.disposition not in {"Reject", "Return for Correction"}),
            "requestsRejected": sum(1 for item in decisions if item.disposition == "Reject"),
            "requestsQueued": sum(1 for item in decisions if item.disposition == "Queue"),
            "requestsDeferred": sum(1 for item in decisions if item.disposition == "Defer"),
            "requestsRouted": sum(1 for item in decisions if item.disposition == "Route"),
            "requestsResolvedLocally": sum(1 for item in decisions if item.disposition == "Resolve Locally"),
            "requestsAnsweredFromCache": sum(1 for item in decisions if item.disposition == "Answer From Cache"),
            "duplicateRequestsSuppressed": sum(1 for item in decisions if item.disposition == "Duplicate Suppressed"),
            "wakeRecommendationsIssued": sum(1 for item in decisions if item.wake_recommendation),
            "emergencyWakeRequests": sum(1 for item in decisions if item.disposition == "Emergency Wake Request"),
            "fullOfficeActivationsAvoided": sum(1 for item in decisions if item.disposition in {"Duplicate Suppressed", "Answer From Cache", "Resolve Locally", "Route", "Defer", "Reject", "Prohibited by Cooldown", "Prohibited by Operating Mode", "Prohibited by Budget"}),
            "estimatedApiCostAvoided": round(sum(item.estimated_activation_cost for item in decisions if not item.wake_recommendation), 4),
            "actualOdoOperatingCost": 0.0,
            "averageTriageLatencyMs": 1,
            "averageQueueAgeSeconds": 0,
            "requestsExpired": sum(1 for item in decisions if item.disposition == "Expired"),
            "cooldownSuppressions": sum(1 for item in decisions if item.disposition == "Prohibited by Cooldown"),
            "operatingModeSuppressions": sum(1 for item in decisions if item.disposition == "Prohibited by Operating Mode"),
            "budgetSuppressions": sum(1 for item in decisions if item.disposition == "Prohibited by Budget"),
            "routingLoopsPrevented": sum(1 for item in decisions if item.reason_code == "Routing loop detected"),
            "invalidAuthorizationAttempts": sum(1 for item in decisions if "mission" in item.reason_code.lower() or "token" in item.reason_code.lower()),
            "officeActivationFrequency": sum(1 for item in decisions if item.wake_recommendation),
            "cacheHitRate": _ratio(sum(1 for item in decisions if item.disposition == "Answer From Cache"), len(decisions)),
            "reuseRate": _ratio(sum(1 for item in decisions if item.cache_reference), len(decisions)),
            "dutyOfficerHealth": "Healthy",
        }


def _default_profiles() -> dict[str, CapabilityProfile]:
    common_modes = ("Full Paper Trading", "Observation Only", "Position Management Only", "Capital Preservation", "Strategic Research Only", "Maintenance")
    return {
        "Executive": _profile("Executive", "Commander directives, policy conflicts, briefings, and escalations.", ("commander_directive", "briefing_request", "policy_conflict", "escalation"), common_modes, 0.02, 120, 60, ("Risk", "Trader")),
        "Seeker": _profile("Seeker", "Market discovery and candidate scan tasking.", ("market_discovery", "candidate_scan", "watchlist_change", "discovery_event"), ("Full Paper Trading",), 0.08, 300, 1800, ("Analyst", "Risk")),
        "Analyst": _profile("Analyst", "Promoted candidate analysis, thesis updates, and evidence review.", ("candidate_analysis", "thesis_update", "evidence_review", "analytical_reassessment"), ("Full Paper Trading", "Position Management Only"), 0.05, 240, 600, ("Risk",)),
        "Strategic Intelligence": _profile("Strategic Intelligence", "Strategic theme review and structural synthesis.", ("strategic_theme_review", "synthesis_request", "structural_event"), ("Strategic Research Only", "Full Paper Trading"), 0.12, 600, 7200, ("Executive", "Librarian")),
        "Risk": _profile("Risk", "Risk review, exposure change, threshold events, proposed approvals, and discrepancies.", ("risk_review", "exposure_change", "position_threshold", "trade_approval", "ledger_discrepancy"), common_modes, 0.03, 180, 60, ("Executive", "Trader")),
        "Trader": _profile("Trader", "Approved orders, order status, fills, rejections, exits, and reconciliation.", ("approved_order", "order_status", "fill_event", "rejection_event", "exit_instruction", "broker_reconciliation"), ("Full Paper Trading", "Position Management Only", "Capital Preservation"), 0.04, 180, 60, ("Risk", "Executive")),
        "Historian": _profile("Historian", "Archive requests, outcomes, mission completion records, and evaluations.", ("archive_request", "outcome_recording", "mission_completion", "performance_update"), common_modes, 0.015, 180, 900, ("Librarian",)),
        "Librarian": _profile("Librarian", "Knowledge retrieval, indexing, doctrine lookup, and search.", ("knowledge_retrieval", "indexing_request", "doctrine_lookup", "semantic_search"), common_modes, 0.015, 180, 900, ("Historian",)),
        "Academy": _profile("Academy", "Training, curriculum, doctrine learning, and capability development.", ("training_request", "curriculum_update", "lesson_capture", "capability_development"), ("Strategic Research Only", "Full Paper Trading"), 0.02, 300, 3600, ("Executive",)),
    }


def _profile(office_id: str, mission: str, supported: tuple[str, ...], modes: tuple[str, ...], cost: float, runtime: int, cooldown: int, escalations: tuple[str, ...]) -> CapabilityProfile:
    return CapabilityProfile(
        profile_id=f"ODO-PROFILE-{office_id.upper().replace(' ', '-')}",
        office_id=office_id,
        office_mission=mission,
        supported_request_types=supported,
        unsupported_request_types=("unapproved_trade", "raw_candidate" if office_id == "Analyst" else "none"),
        accepted_input_artifacts=("mission_record", "workflow_token", "event_reference", "decision_object", "cached_product"),
        produced_output_artifacts=("duty_decision", "wake_recommendation", "queue_record", "route_record"),
        required_dependencies=("Enterprise Operations Scheduler", "Workflow Execution Token"),
        required_data_freshness_minutes=30,
        default_priority="Normal",
        typical_activation_cost=cost,
        typical_runtime_seconds=runtime,
        maximum_queue_depth=20,
        cooldown_seconds=cooldown,
        operating_mode_permissions=modes,
        market_session_requirements=("Any",),
        emergency_wake_conditions=("position_safety", "risk_limit_breach", "broker_inconsistency", "ledger_mismatch", "commander_emergency"),
        cache_reuse_minutes=30,
        duplicate_suppression_seconds=900,
        escalation_destinations=escalations,
        routing_destinations=_routing_map(office_id),
        activation_threshold=65,
    )


def _routing_map(office_id: str) -> dict[str, str]:
    return {
        "knowledge_retrieval": "Librarian" if office_id != "Librarian" else "",
        "archive_request": "Historian" if office_id != "Historian" else "",
        "position_threshold": "Risk" if office_id not in {"Risk", "Trader"} else "",
        "unapproved_trade": "Risk" if office_id == "Trader" else "",
        "raw_candidate": "Seeker" if office_id == "Analyst" else "",
        "training_request": "Academy" if office_id != "Academy" else "",
    }


def _seed_cache() -> dict[str, dict[str, Any]]:
    now = utc_timestamp()
    return {
        "Librarian:knowledge_retrieval": {"cache_id": "ODO-CACHE-LIB-001", "created_at": now, "summary": "Fresh doctrine lookup available.", "contradictory_event": False},
        "Executive:briefing_request": {"cache_id": "ODO-CACHE-EXEC-001", "created_at": now, "summary": "Latest Commander briefing available.", "contradictory_event": False},
    }


def _mission_state(mission_id: str, eos: dict[str, Any]) -> dict[str, Any]:
    for mission in eos.get("missionRecords", ()):
        if mission.get("mission_id") == mission_id:
            return mission
    return {}


def _office_state(office_id: str, offices: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    for office in offices:
        if office.get("organization") == office_id or office.get("office") == office_id:
            return office
    return {}


def _best_route(target: str, profiles: dict[str, CapabilityProfile]) -> str:
    normalized = target.lower()
    for office_id in profiles:
        if office_id.lower() in normalized or normalized in office_id.lower():
            return office_id
    return ""


def _wake_score(request: OfficeTaskingRequest, profile: CapabilityProfile, eos: dict[str, Any]) -> tuple[int, tuple[str, ...]]:
    score = 10
    rules = ["authorization", "relevance", "freshness", "duplicate", "cost", "cooldown", "operating_mode"]
    score += min(35, int(request.estimated_value / 2))
    if request.priority in {"Emergency", "Critical", "High", "Position Safety"}:
        score += 25
    if request.criticality in {"Emergency", "Critical", "Position Safety"}:
        score += 30
    if request.commander_directive_id:
        score += 15
    if request.event_reference:
        score += 10
    if request.estimated_cost <= profile.typical_activation_cost:
        score += 10
    if (eos.get("currentOperatingMode") or "") in {"Capital Preservation", "Position Management Only"} and request.target_office_id in {"Risk", "Trader"}:
        score += 10
    return max(0, min(100, score)), tuple(rules)


def _escalation_destination(request: OfficeTaskingRequest, profile: CapabilityProfile | None) -> str:
    if request.criticality in {"Emergency", "Critical", "Position Safety"}:
        return "Enterprise Operations Scheduler"
    return (profile.escalation_destinations[0] if profile and profile.escalation_destinations else "")


def _dedup_key(item: dict[str, Any]) -> str:
    raw = "|".join(str(item.get(key, "")) for key in ("target_office_id", "targetOfficeId", "mission_id", "missionId", "request_type", "requestType", "event_reference", "eventReference", "decision_object_id", "decisionObjectId", "task_description", "taskDescription"))
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


def _deadline_expired(deadline: str) -> bool:
    return bool(deadline and _parse_time(deadline) < _parse_time(utc_timestamp()))


def _parse_time(value: str) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(UTC)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _priority_rank(priority: str) -> int:
    return {"Emergency": 0, "Critical": 1, "High": 2, "Position Safety": 2, "Normal": 5, "Low": 9}.get(priority, 5)


def _ratio(value: int, total: int) -> str:
    return f"{round((value / total) * 100, 1) if total else 0}%"
