"""Analyst-side Risk Interaction Office."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from argos.foundation.audit import AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService

from .department import AnalystDepartment
from .offices import ANALYST_GROUP_ID, AnalystOfficeInstrumentPanel


RISK_INTERACTION_OFFICE_ID = "ANALYST-OFFICE-007"


@dataclass(frozen=True)
class RiskInteractionObservation:
    """Input observation for deterministic Decision Model pressure testing."""

    decision_model_id: str
    decision_state: str
    assumption_count: int
    weak_assumption_count: int
    scenario_count: int
    stress_severity: float
    contradiction_count: int
    uncertainty_score: float
    missing_evidence_count: int
    failure_mode_count: int
    devil_advocate_strength: float


@dataclass(frozen=True)
class RiskReadinessReport:
    """Deterministic risk readiness report."""

    report_id: str
    readiness_score: float
    readiness_state: str
    weak_assumptions: tuple[str, ...]
    confidence_adjustment: float


@dataclass(frozen=True)
class AnalyticalStressTest:
    """Deterministic analytical stress test result."""

    test_id: str
    scenarios: tuple[dict[str, float | str], ...]
    stress_state: str


@dataclass(frozen=True)
class DecisionModelChallengeReport:
    """Challenge report for a Decision Model without modifying the model."""

    challenge_id: str
    challenged_model_id: str
    challenge_state: str
    findings: tuple[str, ...]


@dataclass(frozen=True)
class RiskInteractionReasoningGraph:
    """Mandatory reasoning graph for risk interaction conclusions."""

    conclusion_id: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str, str], ...]


class AssumptionAuditor:
    def analyze(self, observation: RiskInteractionObservation) -> dict[str, float | int | str]:
        ratio = observation.weak_assumption_count / max(observation.assumption_count, 1)
        return {"assumption_state": "weak_assumptions_identified" if observation.weak_assumption_count else "assumptions_supported", "weak_count": observation.weak_assumption_count, "weak_ratio": round(ratio, 4)}


class ScenarioAnalyst:
    def analyze(self, observation: RiskInteractionObservation) -> dict[str, int | str]:
        return {"scenario_state": "scenario_set_complete" if observation.scenario_count >= 3 else "scenario_set_incomplete", "scenario_count": observation.scenario_count}


class StressTestAnalyst:
    def analyze(self, observation: RiskInteractionObservation) -> dict[str, float | str]:
        return {"stress_state": "stress_elevated" if observation.stress_severity >= 0.6 else "stress_contained", "severity": round(observation.stress_severity, 4)}


class ContradictionAnalyst:
    def analyze(self, observation: RiskInteractionObservation) -> dict[str, int | str]:
        return {"contradiction_state": "contradictions_present" if observation.contradiction_count else "no_contradictions_detected", "contradiction_count": observation.contradiction_count}


class UncertaintyAnalyst:
    def analyze(self, observation: RiskInteractionObservation) -> dict[str, float | str]:
        return {"uncertainty_state": "uncertainty_elevated" if observation.uncertainty_score >= 0.5 else "uncertainty_contained", "uncertainty_score": round(observation.uncertainty_score, 4)}


class MissingEvidenceAnalyst:
    def analyze(self, observation: RiskInteractionObservation) -> dict[str, int | str]:
        return {"missing_evidence_state": "evidence_gaps_present" if observation.missing_evidence_count else "evidence_complete", "missing_evidence_count": observation.missing_evidence_count}


class FailureModeAnalyst:
    def analyze(self, observation: RiskInteractionObservation) -> dict[str, int | str]:
        return {"failure_mode_state": "failure_modes_present" if observation.failure_mode_count else "no_failure_modes_detected", "failure_mode_count": observation.failure_mode_count}


class DevilsAdvocateAnalyst:
    def analyze(self, observation: RiskInteractionObservation) -> dict[str, float | str]:
        return {
            "challenge_state": "strong_challenge" if observation.devil_advocate_strength >= 0.6 else "limited_challenge",
            "challenge_strength": round(observation.devil_advocate_strength, 4),
        }


class RiskInteractionOfficeChief:
    """Office Chief for deterministic Decision Model pressure testing."""

    def __init__(self) -> None:
        self.assumption_auditor = AssumptionAuditor()
        self.scenario_analyst = ScenarioAnalyst()
        self.stress_test_analyst = StressTestAnalyst()
        self.contradiction_analyst = ContradictionAnalyst()
        self.uncertainty_analyst = UncertaintyAnalyst()
        self.missing_evidence_analyst = MissingEvidenceAnalyst()
        self.failure_mode_analyst = FailureModeAnalyst()
        self.devils_advocate_analyst = DevilsAdvocateAnalyst()

    def analyze(self, observation: RiskInteractionObservation) -> dict[str, object]:
        components = {
            "assumption_audit": self.assumption_auditor.analyze(observation),
            "scenario_analysis": self.scenario_analyst.analyze(observation),
            "stress_test_analysis": self.stress_test_analyst.analyze(observation),
            "contradiction_analysis": self.contradiction_analyst.analyze(observation),
            "uncertainty_analysis": self.uncertainty_analyst.analyze(observation),
            "missing_evidence_analysis": self.missing_evidence_analyst.analyze(observation),
            "failure_mode_analysis": self.failure_mode_analyst.analyze(observation),
            "devils_advocate_analysis": self.devils_advocate_analyst.analyze(observation),
        }
        readiness = self.risk_readiness_report(observation, components)
        stress_test = self.analytical_stress_test(observation, components)
        challenge = self.challenge_report(observation, components)
        components["risk_readiness_report"] = readiness.__dict__
        components["analytical_stress_test"] = stress_test.__dict__
        components["decision_model_challenge_report"] = challenge.__dict__
        components["confidence_adjustment_recommendation"] = {
            "method": "risk_readiness_penalty",
            "adjustment": readiness.confidence_adjustment,
        }
        return components

    def risk_readiness_report(self, observation: RiskInteractionObservation, components: dict[str, object]) -> RiskReadinessReport:
        penalty = (
            observation.weak_assumption_count * 8
            + observation.contradiction_count * 10
            + observation.missing_evidence_count * 7
            + observation.failure_mode_count * 6
            + int(observation.stress_severity * 20)
            + int(observation.uncertainty_score * 15)
            + int(observation.devil_advocate_strength * 10)
        )
        score = round(max(0, 100 - penalty), 2)
        if score >= 75:
            state = "risk_ready"
        elif score >= 50:
            state = "review_required"
        else:
            state = "not_risk_ready"
        adjustment = round(-min(0.5, (100 - score) / 200), 4)
        return RiskReadinessReport("RRR-001", score, state, self._weak_assumptions(components), adjustment)

    def analytical_stress_test(self, observation: RiskInteractionObservation, components: dict[str, object]) -> AnalyticalStressTest:
        scenarios = (
            {"scenario": "base_case", "stress_impact": round(observation.stress_severity * 0.5, 4)},
            {"scenario": "adverse_case", "stress_impact": round(observation.stress_severity * 0.85, 4)},
            {"scenario": "extreme_case", "stress_impact": round(min(1.0, observation.stress_severity * 1.25), 4)},
        )
        return AnalyticalStressTest("AST-001", scenarios, str(components["stress_test_analysis"]["stress_state"]))

    def challenge_report(self, observation: RiskInteractionObservation, components: dict[str, object]) -> DecisionModelChallengeReport:
        findings = self._challenge_findings(components)
        state = "material_challenge" if len(findings) >= 3 else "limited_challenge"
        return DecisionModelChallengeReport("DMCR-001", observation.decision_model_id, state, findings)

    def reasoning_graphs(self, reasoning: dict[str, object], source_report_ids: tuple[str, ...]) -> tuple[RiskInteractionReasoningGraph, ...]:
        return (
            RiskInteractionReasoningGraph(
                "RISK-INTERACTION-CONCLUSION-001",
                (
                    "claim:risk_readiness",
                    "evidence:assumption_audit",
                    "evidence:stress_test",
                    "evidence:contradiction_analysis",
                    "evidence:missing_evidence",
                    "evidence:failure_modes",
                    "source:" + ",".join(source_report_ids),
                ),
                (
                    ("evidence:assumption_audit", "claim:risk_readiness", "challenges"),
                    ("evidence:stress_test", "claim:risk_readiness", "challenges"),
                    ("evidence:contradiction_analysis", "claim:risk_readiness", "challenges"),
                    ("evidence:missing_evidence", "claim:risk_readiness", "qualifies"),
                ),
            ),
        )

    def _weak_assumptions(self, components: dict[str, object]) -> tuple[str, ...]:
        factors: list[str] = []
        if components["assumption_audit"]["assumption_state"] == "weak_assumptions_identified":
            factors.append("weak_assumptions_identified")
        if components["uncertainty_analysis"]["uncertainty_state"] == "uncertainty_elevated":
            factors.append("uncertainty_elevated")
        if components["missing_evidence_analysis"]["missing_evidence_state"] == "evidence_gaps_present":
            factors.append("evidence_gaps_present")
        return tuple(factors)

    def _challenge_findings(self, components: dict[str, object]) -> tuple[str, ...]:
        findings: list[str] = []
        for key, field, challenged_value in (
            ("assumption_audit", "assumption_state", "weak_assumptions_identified"),
            ("stress_test_analysis", "stress_state", "stress_elevated"),
            ("contradiction_analysis", "contradiction_state", "contradictions_present"),
            ("uncertainty_analysis", "uncertainty_state", "uncertainty_elevated"),
            ("missing_evidence_analysis", "missing_evidence_state", "evidence_gaps_present"),
            ("failure_mode_analysis", "failure_mode_state", "failure_modes_present"),
            ("devils_advocate_analysis", "challenge_state", "strong_challenge"),
        ):
            if components[key][field] == challenged_value:
                findings.append(challenged_value)
        return tuple(findings)


class RiskInteractionOffice:
    """Analyst-side Risk Interaction Office integrated with Analyst Department."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = AnalystDepartment(
            configuration_service,
            persistence_repository,
            audit_service,
            prompt_repository,
        )
        self.office = self.department.offices[RISK_INTERACTION_OFFICE_ID]
        self.chief = RiskInteractionOfficeChief()

    def generate_risk_interaction_aar(
        self,
        observation: RiskInteractionObservation,
        decision_model: dict[str, object],
        source_reports: tuple[OperationalContract, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        original_decision_model_json = json.dumps(decision_model, sort_keys=True, separators=(",", ":"))
        reasoning = self.chief.analyze(observation)
        source_ids = tuple(report.contract_id for report in source_reports)
        graphs = self.chief.reasoning_graphs(reasoning, source_ids)
        created = utc_timestamp()
        payload = {
            "office_id": RISK_INTERACTION_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "risk_interaction_analytical_assessment",
            "source_report_ids": list(source_ids),
            "reviewed_decision_model_id": observation.decision_model_id,
            "risk_interaction_reasoning": reasoning,
            "risk_interaction_reasoning_graphs": [graph.__dict__ for graph in graphs],
            "risk_readiness_report": reasoning["risk_readiness_report"],
            "analytical_stress_tests": [reasoning["analytical_stress_test"]],
            "decision_model_challenge_report": reasoning["decision_model_challenge_report"],
            "confidence_adjustment_recommendation": reasoning["confidence_adjustment_recommendation"],
            "decision_model_modified": json.dumps(decision_model, sort_keys=True, separators=(",", ":")) != original_decision_model_json,
            "risk_office_override": False,
            "seeker_intelligence_modified": False,
        }
        signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        report = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type="AAR",
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            parent_contract_ids=source_ids,
            produced_by_staff_id=self.office.record.configuration.staff_id,
            produced_by_group_id=ANALYST_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary="Risk Interaction Analytical Assessment Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report

    def route_aar(self, aar: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_aar(RISK_INTERACTION_OFFICE_ID, aar, target_inbox)

    def instrument_panel(self) -> AnalystOfficeInstrumentPanel:
        return self.office.instrument_panel()
