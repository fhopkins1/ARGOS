"""Tail Risk Office."""

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


TAIL_RISK_OFFICE_ID = "RISK-OFFICE-006"


@dataclass(frozen=True)
class TailRiskExposure:
    """Exposure reviewed by the Tail Risk Office."""

    exposure_id: str
    asset: str
    notional: float
    tail_beta: float
    liquidity_gap_pct: float
    nonlinear_multiplier: float
    dependency_group: str


@dataclass(frozen=True)
class TailRiskObservation:
    """Tail-risk observation."""

    observation_id: str
    exposures: tuple[TailRiskExposure, ...]
    historical_crisis_losses: dict[str, float]
    organizational_resilience_score: float


@dataclass(frozen=True)
class CatastrophicScenario:
    """Deterministic catastrophic scenario."""

    scenario_id: str
    name: str
    shock_pct: float
    probability_estimate: float
    affected_dependency_groups: tuple[str, ...]


@dataclass(frozen=True)
class MaximumCredibleLossRecord:
    """Maximum credible loss record."""

    record_id: str
    maximum_credible_loss: float
    maximum_loss_scenario: str
    loss_ratio: float


@dataclass(frozen=True)
class MitigationRecommendationRecord:
    """Risk-control mitigation recommendation."""

    record_id: str
    action: str
    rationale: str


@dataclass(frozen=True)
class TailRiskInstrumentPanel:
    """Tail Risk Office instrument panel display."""

    base_panel: RiskOfficeInstrumentPanel
    modeled_scenarios: int
    maximum_credible_loss: float
    dependency_cascades: int
    nonlinear_exposures: int
    archived_scenarios: int


class CatastrophicScenarioBuilder:
    def build(self, observation: TailRiskObservation) -> tuple[CatastrophicScenario, ...]:
        groups = tuple(sorted({exposure.dependency_group for exposure in observation.exposures}))
        return (
            CatastrophicScenario("TS-001", "Liquidity Vacuum", -0.32, 0.08, groups),
            CatastrophicScenario("TS-002", "Correlation Break", -0.24, 0.12, groups),
            CatastrophicScenario("TS-003", "Funding Shock", -0.28, 0.06, tuple(group for group in groups if group in {"credit", "growth"}) or groups),
            CatastrophicScenario("TS-004", "Volatility Spiral", -0.36, 0.05, groups),
        )


class DistributionTailEvaluator:
    def evaluate(self, scenarios: tuple[CatastrophicScenario, ...]) -> dict[str, float]:
        probability_mass = sum(scenario.probability_estimate for scenario in scenarios)
        weighted_shock = sum(abs(scenario.shock_pct) * scenario.probability_estimate for scenario in scenarios)
        return {"tail_probability_mass": round(probability_mass, 4), "weighted_tail_shock": round(weighted_shock, 4)}


class MaximumCredibleLossCalculator:
    def calculate(self, exposures: tuple[TailRiskExposure, ...], scenarios: tuple[CatastrophicScenario, ...]) -> MaximumCredibleLossRecord:
        total = sum(exposure.notional for exposure in exposures)
        losses = []
        for scenario in scenarios:
            loss = _scenario_loss(exposures, scenario)
            losses.append((scenario.scenario_id, loss))
        scenario_id, maximum_loss = max(losses, key=lambda item: item[1])
        return MaximumCredibleLossRecord("MCL-001", round(maximum_loss, 4), scenario_id, round(maximum_loss / total if total else 0.0, 4))


class DependencyCascadeAnalyzer:
    def analyze(self, exposures: tuple[TailRiskExposure, ...]) -> tuple[dict[str, object], ...]:
        cascades = []
        grouped: dict[str, list[TailRiskExposure]] = {}
        for exposure in exposures:
            grouped.setdefault(exposure.dependency_group, []).append(exposure)
        for group, group_exposures in sorted(grouped.items()):
            if len(group_exposures) > 1:
                cascades.append({"dependency_group": group, "exposure_ids": tuple(exposure.exposure_id for exposure in group_exposures), "cascade_state": "cascade_possible"})
        return tuple(cascades)


class NonlinearExposureEvaluator:
    def evaluate(self, exposures: tuple[TailRiskExposure, ...]) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "exposure_id": exposure.exposure_id,
                "asset": exposure.asset,
                "nonlinear_multiplier": exposure.nonlinear_multiplier,
                "nonlinear_state": "nonlinear_elevated" if exposure.nonlinear_multiplier >= 1.5 else "nonlinear_contained",
            }
            for exposure in exposures
        )


class HistoricalAnalogComparator:
    def compare(self, observation: TailRiskObservation, maximum_loss: float) -> dict[str, object]:
        analogs = tuple(
            {"crisis": crisis, "loss": loss, "relative_to_mcl": round(loss / maximum_loss if maximum_loss else 0.0, 4)}
            for crisis, loss in sorted(observation.historical_crisis_losses.items())
        )
        closest = max(analogs, key=lambda item: item["relative_to_mcl"]) if analogs else None
        return {"report_id": "HAR-001", "analogs": analogs, "closest_analog": closest}


class OrganizationalResilienceEvaluator:
    def evaluate(self, observation: TailRiskObservation, loss_ratio: float, cascade_count: int) -> dict[str, float | str]:
        score = round(max(0.0, min(1.0, observation.organizational_resilience_score - loss_ratio * 0.35 - cascade_count * 0.06)), 4)
        state = "resilience_weak" if score < 0.35 else "resilience_watch" if score < 0.6 else "resilience_stable"
        return {"organizational_resilience": score, "resilience_state": state}


class TailScenarioArchive:
    def archive(self, scenarios: tuple[CatastrophicScenario, ...]) -> tuple[dict[str, object], ...]:
        return tuple({"archive_id": f"TSA-{index:03d}", **scenario.__dict__} for index, scenario in enumerate(scenarios, start=1))


class TailRiskOfficeChief:
    """Office Chief for deterministic tail-risk analysis."""

    def __init__(self) -> None:
        self.scenario_builder = CatastrophicScenarioBuilder()
        self.tail_evaluator = DistributionTailEvaluator()
        self.maximum_loss = MaximumCredibleLossCalculator()
        self.cascade = DependencyCascadeAnalyzer()
        self.nonlinear = NonlinearExposureEvaluator()
        self.historical = HistoricalAnalogComparator()
        self.resilience = OrganizationalResilienceEvaluator()
        self.archive = TailScenarioArchive()

    def evaluate(self, belief_state: OrganizationalBeliefState, observation: TailRiskObservation) -> dict[str, object]:
        if not isinstance(belief_state, OrganizationalBeliefState):
            raise TypeError("Tail Risk Office requires an OrganizationalBeliefState")
        if not observation.exposures:
            raise ValueError("tail-risk review requires at least one exposure")
        scenarios = self.scenario_builder.build(observation)
        tail_distribution = self.tail_evaluator.evaluate(scenarios)
        maximum_loss = self.maximum_loss.calculate(observation.exposures, scenarios)
        cascades = self.cascade.analyze(observation.exposures)
        nonlinear = self.nonlinear.evaluate(observation.exposures)
        historical = self.historical.compare(observation, maximum_loss.maximum_credible_loss)
        resilience = self.resilience.evaluate(observation, maximum_loss.loss_ratio, len(cascades))
        confidence = self.confidence_adjustment(belief_state, maximum_loss.loss_ratio, len(cascades), tail_distribution["tail_probability_mass"])
        mitigation = self.mitigation(maximum_loss.loss_ratio, resilience["organizational_resilience"], len(cascades))
        archived = self.archive.archive(scenarios)
        return {
            "tail_risk_assessment_report": {
                "report_id": "TRAR-001",
                "observation_id": observation.observation_id,
                "scenario_count": len(scenarios),
                "low_probability_scenarios_discarded": False,
            },
            "extreme_scenario_report": {"report_id": "ESR-001", "scenarios": [scenario.__dict__ for scenario in scenarios], "tail_distribution": tail_distribution},
            "maximum_credible_loss_record": maximum_loss.__dict__,
            "dependency_cascade_analysis": {"analysis_id": "DCA-001", "cascades": cascades},
            "nonlinear_exposure_assessment": {"assessment_id": "NEA-001", "exposures": nonlinear},
            "historical_analog_report": historical,
            "organizational_tail_exposure_summary": {
                "summary_id": "OTES-001",
                "loss_ratio": maximum_loss.loss_ratio,
                "resilience": resilience,
                "organizational_confidence_surface": confidence["adjusted_confidence"],
            },
            "mitigation_recommendation_record": mitigation.__dict__,
            "tail_scenario_archive": archived,
            "confidence_adjustment_record": confidence,
        }

    def confidence_adjustment(self, belief_state: OrganizationalBeliefState, loss_ratio: float, cascade_count: int, tail_probability_mass: float) -> dict[str, float | str]:
        adjustment = round(-(loss_ratio * 0.18 + cascade_count * 0.03 + tail_probability_mass * 0.08), 4)
        adjusted = round(max(0.0, min(1.0, belief_state.organizational_confidence + adjustment)), 4)
        return {"record_id": "TCAR-001", "prior_confidence": belief_state.organizational_confidence, "adjusted_confidence": adjusted, "adjustment": adjustment}

    def mitigation(self, loss_ratio: float, resilience: float, cascade_count: int) -> MitigationRecommendationRecord:
        if loss_ratio >= 0.35 or resilience < 0.35:
            action = "reduce_tail_exposure_and_raise_liquidity_reserve"
        elif cascade_count:
            action = "segment_dependency_groups_and_stage_exits"
        else:
            action = "maintain_tail_monitoring"
        return MitigationRecommendationRecord("MRR-001", action, "Risk mitigation recommendation; not an investment recommendation or execution instruction.")


class TailRiskOffice:
    """Tail Risk Office integrated with the Risk Department framework."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = RiskDepartment(configuration_service, persistence_repository, audit_service, prompt_repository)
        self.office = self.department.offices[TAIL_RISK_OFFICE_ID]
        self.chief = TailRiskOfficeChief()
        self._latest_review: dict[str, object] | None = None

    def generate_tail_risk_report(
        self,
        belief_state: OrganizationalBeliefState,
        observation: TailRiskObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        """Generate a Tail Risk Assessment Report as a RAR."""
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        review = self.chief.evaluate(belief_state, observation)
        created = utc_timestamp()
        payload = {
            "risk_id": f"TAIL-{document_sequence:06d}",
            "office_id": TAIL_RISK_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "tail_risk_assessment",
            "case_file_id": case_file_id,
            "trade_cycle_id": trade_cycle_id,
            **review,
            "organizational_belief_state_id": belief_state.state_id,
            "organizational_belief_state_modified": False,
            "opaque_reasoning_used": False,
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
            human_summary="Tail Risk Assessment Report.",
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
        """Route a Tail Risk Report through Courier Framework."""
        return self.department.route_rar(TAIL_RISK_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> TailRiskInstrumentPanel:
        """Return the Tail Risk Office instrument panel."""
        base = self.office.instrument_panel()
        if not self._latest_review:
            return TailRiskInstrumentPanel(base, 0, 0.0, 0, 0, 0)
        return TailRiskInstrumentPanel(
            base,
            len(self._latest_review["extreme_scenario_report"]["scenarios"]),
            float(self._latest_review["maximum_credible_loss_record"]["maximum_credible_loss"]),
            len(self._latest_review["dependency_cascade_analysis"]["cascades"]),
            len(self._latest_review["nonlinear_exposure_assessment"]["exposures"]),
            len(self._latest_review["tail_scenario_archive"]),
        )


def _scenario_loss(exposures: tuple[TailRiskExposure, ...], scenario: CatastrophicScenario) -> float:
    loss = 0.0
    for exposure in exposures:
        if exposure.dependency_group in scenario.affected_dependency_groups:
            loss += exposure.notional * abs(scenario.shock_pct) * exposure.tail_beta * exposure.nonlinear_multiplier
            loss += exposure.notional * exposure.liquidity_gap_pct * 0.35
    return loss
