"""Recovery Planning Office."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from argos.analyst import OrganizationalBeliefState
from argos.foundation.audit import AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService

from .department import RiskDepartment
from .offices import RISK_GROUP_ID, RiskOfficeInstrumentPanel


RECOVERY_PLANNING_OFFICE_ID = "RISK-OFFICE-009"


@dataclass(frozen=True)
class RecoveryEvent:
    """Adverse event requiring recovery planning."""

    event_id: str
    event_type: str
    capital_drawdown_pct: float
    operational_disruption_score: float
    market_stress_score: float
    control_breach_count: int
    liquidity_reserve_pct: float
    unresolved_actions: int
    validation_pass_rate: float


@dataclass(frozen=True)
class RecoveryScenario:
    """Deterministic recovery scenario."""

    scenario_id: str
    name: str
    severity: str
    required_actions: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryWorkflow:
    """Recovery workflow."""

    workflow_id: str
    steps: tuple[dict[str, str | int], ...]


@dataclass(frozen=True)
class CapitalRestorationPlan:
    """Capital restoration plan."""

    plan_id: str
    restoration_required_pct: float
    restoration_state: str


@dataclass(frozen=True)
class RecoveryReadinessAssessment:
    """Recovery readiness assessment."""

    assessment_id: str
    readiness_score: float
    readiness_state: str


@dataclass(frozen=True)
class RecoveryValidationReport:
    """Recovery validation report."""

    report_id: str
    validated: bool
    validation_score: float
    incomplete_actions: int


@dataclass(frozen=True)
class ConfidenceRestorationRecord:
    """Confidence restoration record."""

    record_id: str
    prior_confidence: float
    restored_confidence: float
    restoration_delta: float


@dataclass(frozen=True)
class RecoveryPlanningInstrumentPanel:
    """Recovery Planning Office instrument panel."""

    base_panel: RiskOfficeInstrumentPanel
    active_recovery_events: int
    readiness_score: float
    capital_restoration_required_pct: float
    workflow_steps: int
    archived_events: int


class RecoveryScenarioMaintainer:
    def scenarios(self) -> tuple[RecoveryScenario, ...]:
        return (
            RecoveryScenario("RS-001", "Market Drawdown Recovery", "market", ("stabilize_exposure", "restore_capital_buffer", "validate_controls")),
            RecoveryScenario("RS-002", "Operational Disruption Recovery", "operational", ("isolate_disruption", "restore_services", "verify_audit_integrity")),
            RecoveryScenario("RS-003", "Liquidity Stress Recovery", "liquidity", ("raise_liquidity_reserve", "stage_exits", "confirm_execution_feasibility")),
        )


class FailureClassifier:
    def classify(self, event: RecoveryEvent) -> dict[str, str]:
        if event.operational_disruption_score >= 0.65 or event.control_breach_count >= 2:
            failure_class = "operational_failure"
        elif event.capital_drawdown_pct >= 0.2:
            failure_class = "capital_impairment"
        elif event.market_stress_score >= 0.65:
            failure_class = "market_stress_failure"
        else:
            failure_class = "contained_adverse_event"
        return {"failure_class": failure_class}


class RecoveryWorkflowGenerator:
    def generate(self, scenarios: tuple[RecoveryScenario, ...], failure_class: str) -> RecoveryWorkflow:
        selected = [scenario for scenario in scenarios if failure_class.split("_")[0] in scenario.severity or failure_class == "contained_adverse_event"]
        if not selected:
            selected = list(scenarios)
        steps = []
        sequence = 1
        for scenario in selected:
            for action in scenario.required_actions:
                steps.append({"sequence": sequence, "scenario_id": scenario.scenario_id, "action": action})
                sequence += 1
        return RecoveryWorkflow("RW-001", tuple(steps))


class StabilizationCoordinator:
    def coordinate(self, event: RecoveryEvent) -> dict[str, str | tuple[str, ...]]:
        activities = ["freeze_new_risk", "confirm_audit_integrity"]
        if event.liquidity_reserve_pct < 0.15:
            activities.append("raise_liquidity_reserve")
        if event.operational_disruption_score >= 0.5:
            activities.append("restore_operational_services")
        return {"coordination_id": "SC-001", "activities": tuple(activities)}


class CapitalRestorationEvaluator:
    def evaluate(self, event: RecoveryEvent) -> CapitalRestorationPlan:
        required = round(max(0.0, event.capital_drawdown_pct - event.liquidity_reserve_pct), 4)
        state = "capital_restoration_required" if required > 0.05 else "capital_buffer_adequate"
        return CapitalRestorationPlan("CRP-001", required, state)


class OperationalReadinessEvaluator:
    def evaluate(self, event: RecoveryEvent, restoration_required: float) -> RecoveryReadinessAssessment:
        score = round(max(0.0, min(100.0, 100 - event.operational_disruption_score * 25 - event.market_stress_score * 20 - event.unresolved_actions * 4 - restoration_required * 80)), 2)
        if score >= 80:
            state = "recovery_ready"
        elif score >= 60:
            state = "recovery_watch"
        else:
            state = "recovery_not_ready"
        return RecoveryReadinessAssessment("RRA-001", score, state)


class RecoveryCompletionValidator:
    def validate(self, event: RecoveryEvent, readiness_score: float) -> RecoveryValidationReport:
        score = round((event.validation_pass_rate * 70) + max(0, readiness_score) * 0.3 - event.unresolved_actions * 3, 2)
        validated = score >= 80 and event.unresolved_actions == 0
        return RecoveryValidationReport("RVR-001", validated, score, event.unresolved_actions)


class ProceduralImprovementRecommender:
    def recommend(self, event: RecoveryEvent, validation: RecoveryValidationReport) -> tuple[str, ...]:
        recommendations = []
        if event.control_breach_count:
            recommendations.append("tighten_control_breach_escalation")
        if event.unresolved_actions:
            recommendations.append("reduce_recovery_action_backlog")
        if not validation.validated:
            recommendations.append("increase_recovery_validation_threshold")
        return tuple(recommendations or ("maintain_recovery_procedures",))


class RecoveryEventArchive:
    def archive(self, event: RecoveryEvent, scenario_ids: tuple[str, ...]) -> dict[str, object]:
        return {"archive_id": "REA-001", "event_id": event.event_id, "event_type": event.event_type, "scenario_ids": scenario_ids}


class RecoveryPlanningOfficeChief:
    """Office Chief for deterministic recovery planning."""

    def __init__(self) -> None:
        self.scenarios = RecoveryScenarioMaintainer()
        self.classifier = FailureClassifier()
        self.workflow = RecoveryWorkflowGenerator()
        self.stabilization = StabilizationCoordinator()
        self.capital = CapitalRestorationEvaluator()
        self.readiness = OperationalReadinessEvaluator()
        self.validator = RecoveryCompletionValidator()
        self.improvements = ProceduralImprovementRecommender()
        self.archive = RecoveryEventArchive()

    def evaluate(self, belief_state: OrganizationalBeliefState, event: RecoveryEvent) -> dict[str, object]:
        if not isinstance(belief_state, OrganizationalBeliefState):
            raise TypeError("Recovery Planning Office requires an OrganizationalBeliefState")
        scenarios = self.scenarios.scenarios()
        classification = self.classifier.classify(event)
        workflow = self.workflow.generate(scenarios, classification["failure_class"])
        stabilization = self.stabilization.coordinate(event)
        capital = self.capital.evaluate(event)
        readiness = self.readiness.evaluate(event, capital.restoration_required_pct)
        validation = self.validator.validate(event, readiness.readiness_score)
        improvements = self.improvements.recommend(event, validation)
        confidence = self.confidence_restoration(belief_state, readiness.readiness_score, validation.validation_score)
        archive = self.archive.archive(event, tuple(scenario.scenario_id for scenario in scenarios))
        return {
            "recovery_plan": {"plan_id": "RP-001", "classification": classification["failure_class"], "scenarios": [scenario.__dict__ for scenario in scenarios]},
            "recovery_progress_report": {"report_id": "RPR-001", "stabilization": stabilization, "workflow_steps_completed": max(0, len(workflow.steps) - event.unresolved_actions)},
            "organizational_recovery_summary": {"summary_id": "ORS-001", "readiness_state": readiness.readiness_state, "validated": validation.validated},
            "recovery_workflow": workflow.__dict__,
            "recovery_readiness_assessment": readiness.__dict__,
            "capital_restoration_plan": capital.__dict__,
            "recovery_validation_report": validation.__dict__,
            "executive_recovery_status_report": {"report_id": "ERSR-001", "status": "validated" if validation.validated else "recovery_in_progress", "procedural_improvements": improvements},
            "recovery_event_archive": archive,
            "confidence_restoration_record": confidence.__dict__,
        }

    def confidence_restoration(self, belief_state: OrganizationalBeliefState, readiness_score: float, validation_score: float) -> ConfidenceRestorationRecord:
        delta = round((readiness_score / 100) * 0.08 + (validation_score / 100) * 0.08 - 0.08, 4)
        restored = round(max(0.0, min(1.0, belief_state.organizational_confidence + delta)), 4)
        return ConfidenceRestorationRecord("CRR-001", belief_state.organizational_confidence, restored, delta)


class RecoveryPlanningOffice:
    """Recovery Planning Office integrated with the Risk Department framework."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = RiskDepartment(configuration_service, persistence_repository, audit_service, prompt_repository)
        self.office = self.department.offices[RECOVERY_PLANNING_OFFICE_ID]
        self.chief = RecoveryPlanningOfficeChief()
        self._latest_review: dict[str, object] | None = None

    def generate_recovery_plan_report(
        self,
        belief_state: OrganizationalBeliefState,
        event: RecoveryEvent,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        """Generate a Recovery Planning Report as a RAR."""
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        review = self.chief.evaluate(belief_state, event)
        created = utc_timestamp()
        payload = {
            "risk_id": f"REC-{document_sequence:06d}",
            "office_id": RECOVERY_PLANNING_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "recovery_planning_assessment",
            "case_file_id": case_file_id,
            "trade_cycle_id": trade_cycle_id,
            **review,
            "organizational_belief_state_id": belief_state.state_id,
            "organizational_belief_state_modified": False,
            "subjective_judgment_used": False,
            "investment_recommendation": None,
            "execution_instruction": None,
            "command_decision": None,
            "timestamp": created,
        }
        signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        report = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type="RAR",
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            parent_contract_ids=belief_state.source_report_ids,
            produced_by_staff_id=self.office.record.configuration.staff_id,
            produced_by_group_id=RISK_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary="Recovery Planning Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=belief_state.source_report_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.department.audit_service.record_document_creation(report)
        self.office.reports_generated += 1
        self._latest_review = review
        return report

    def route_report(self, report: OperationalContract, target_inbox: IncomingMailbox):
        """Route a Recovery Planning Report through Courier Framework."""
        return self.department.route_rar(RECOVERY_PLANNING_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> RecoveryPlanningInstrumentPanel:
        """Return the Recovery Planning Office instrument panel."""
        base = self.office.instrument_panel()
        if not self._latest_review:
            return RecoveryPlanningInstrumentPanel(base, 0, 0.0, 0.0, 0, 0)
        return RecoveryPlanningInstrumentPanel(
            base,
            1,
            float(self._latest_review["recovery_readiness_assessment"]["readiness_score"]),
            float(self._latest_review["capital_restoration_plan"]["restoration_required_pct"]),
            len(self._latest_review["recovery_workflow"]["steps"]),
            1,
        )
