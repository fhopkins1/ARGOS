"""Position Risk Office."""

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


POSITION_RISK_OFFICE_ID = "RISK-OFFICE-001"


@dataclass(frozen=True)
class ProposedPosition:
    """Single proposed position reviewed in isolation."""

    asset: str
    position_size: float
    entry_price: float
    stop_loss_price: float
    expected_success_gain_pct: float
    liquidity_score: float
    volatility_score: float
    sensitivity_score: float
    gap_down_loss_pct: float
    gap_up_loss_pct: float
    interest_rate_shock_loss_pct: float
    regulatory_event_loss_pct: float
    unexpected_earnings_loss_pct: float
    geopolitical_event_loss_pct: float
    execution_failure_loss_pct: float
    historical_adversary_loss_pct: float
    recovery_score: float
    thesis_invalidation_evidence: tuple[str, ...]


@dataclass(frozen=True)
class PositionStressTestResult:
    """Result of one deterministic position stress test."""

    scenario: str
    loss_pct: float
    loss_amount: float
    severity: str


@dataclass(frozen=True)
class PositionRiskModel:
    """Required Position Risk Model."""

    maximum_expected_loss: float
    expected_drawdown: float
    probability_of_failure: float
    probability_of_success: float
    invalidation_conditions: tuple[str, ...]
    position_sensitivity: float
    recovery_potential: float
    recommended_position_limit: float
    confidence: float
    organizational_confidence_surface_contribution: float


@dataclass(frozen=True)
class PositionReadinessScore:
    """Position Readiness Score."""

    score: float
    category: str


@dataclass(frozen=True)
class PositionRiskInstrumentPanel:
    """Position Risk Office instrument panel display."""

    base_panel: RiskOfficeInstrumentPanel
    open_position_reviews: int
    maximum_exposure: float
    expected_drawdown: float
    stress_tests: int
    failure_modes: int


class ExposureAnalyst:
    def analyze(self, position: ProposedPosition) -> dict[str, float | str]:
        notional = position.position_size * position.entry_price
        return {"asset": position.asset, "position_size": position.position_size, "notional_exposure": round(notional, 4)}


class StopLossAnalyst:
    def analyze(self, position: ProposedPosition) -> dict[str, float | str]:
        stop_loss_pct = max(0.0, (position.entry_price - position.stop_loss_price) / position.entry_price)
        return {"stop_loss_pct": round(stop_loss_pct, 4), "stop_loss_state": "defined" if stop_loss_pct > 0 else "undefined"}


class PositionScenarioAnalyst:
    def analyze(self, position: ProposedPosition, notional: float) -> tuple[PositionStressTestResult, ...]:
        scenarios = (
            ("Market Crash", max(0.25, position.volatility_score * 0.4)),
            ("Gap Down", position.gap_down_loss_pct),
            ("Gap Up", position.gap_up_loss_pct),
            ("Volatility Spike", position.volatility_score * 0.3),
            ("Liquidity Collapse", (1 - position.liquidity_score) * 0.5),
            ("Interest Rate Shock", position.interest_rate_shock_loss_pct),
            ("Regulatory Event", position.regulatory_event_loss_pct),
            ("Unexpected Earnings", position.unexpected_earnings_loss_pct),
            ("Geopolitical Event", position.geopolitical_event_loss_pct),
            ("Execution Failure", position.execution_failure_loss_pct),
            ("Historical Adversaries", position.historical_adversary_loss_pct),
        )
        return tuple(
            PositionStressTestResult(name, round(loss_pct, 4), round(notional * loss_pct, 4), self._severity(loss_pct))
            for name, loss_pct in scenarios
        )

    def _severity(self, loss_pct: float) -> str:
        if loss_pct >= 0.35:
            return "catastrophic"
        if loss_pct >= 0.2:
            return "severe"
        return "contained"


class PositionFailureModeAnalyst:
    def analyze(self, position: ProposedPosition, stress_tests: tuple[PositionStressTestResult, ...]) -> tuple[str, ...]:
        modes = []
        if any(test.severity == "catastrophic" for test in stress_tests):
            modes.append("catastrophic_stress_loss")
        if position.liquidity_score < 0.5:
            modes.append("liquidity_disappears")
        if position.stop_loss_price <= 0 or position.stop_loss_price >= position.entry_price:
            modes.append("stop_loss_invalid")
        if position.thesis_invalidation_evidence:
            modes.append("thesis_invalidation")
        if position.execution_failure_loss_pct >= 0.1:
            modes.append("execution_failure")
        return tuple(modes)


class PositionLiquidityAnalyst:
    def analyze(self, position: ProposedPosition) -> dict[str, float | str]:
        if position.liquidity_score < 0.35:
            state = "liquidity_fragile"
        elif position.liquidity_score < 0.7:
            state = "liquidity_watch"
        else:
            state = "liquidity_resilient"
        return {"liquidity_state": state, "liquidity_score": round(position.liquidity_score, 4)}


class PositionSizingAnalyst:
    def analyze(self, notional: float, maximum_loss: float, confidence: float) -> dict[str, float]:
        loss_ratio = maximum_loss / notional if notional else 1
        limit_multiplier = max(0.1, min(1.0, confidence - loss_ratio * 0.5))
        return {"recommended_position_limit": round(notional * limit_multiplier, 4)}


class SensitivityAnalyst:
    def analyze(self, position: ProposedPosition) -> dict[str, float | str]:
        state = "high_sensitivity" if position.sensitivity_score >= 0.7 else "moderate_sensitivity" if position.sensitivity_score >= 0.4 else "low_sensitivity"
        return {"sensitivity_state": state, "sensitivity_score": round(position.sensitivity_score, 4)}


class InvalidityAnalyst:
    def analyze(self, position: ProposedPosition) -> tuple[str, ...]:
        defaults = (
            "price_closes_below_stop_loss",
            "expected_success_gain_no_longer_exceeds_expected_drawdown",
        )
        return defaults + position.thesis_invalidation_evidence


class PositionRiskOfficeChief:
    """Office Chief for single-position risk review."""

    def __init__(self) -> None:
        self.exposure = ExposureAnalyst()
        self.stop_loss = StopLossAnalyst()
        self.scenario = PositionScenarioAnalyst()
        self.failure_mode = PositionFailureModeAnalyst()
        self.liquidity = PositionLiquidityAnalyst()
        self.position_sizing = PositionSizingAnalyst()
        self.sensitivity = SensitivityAnalyst()
        self.invalidity = InvalidityAnalyst()

    def evaluate(self, belief_state: OrganizationalBeliefState, position: ProposedPosition) -> dict[str, object]:
        if not isinstance(belief_state, OrganizationalBeliefState):
            raise TypeError("Position Risk Office requires an OrganizationalBeliefState")
        exposure = self.exposure.analyze(position)
        notional = float(exposure["notional_exposure"])
        stop_loss = self.stop_loss.analyze(position)
        stress_tests = self.scenario.analyze(position, notional)
        maximum_expected_loss = max(test.loss_amount for test in stress_tests + (PositionStressTestResult("Stop Loss", float(stop_loss["stop_loss_pct"]), notional * float(stop_loss["stop_loss_pct"]), "contained"),))
        expected_drawdown = round(maximum_expected_loss * (0.55 + position.volatility_score * 0.25), 4)
        probability_failure = self._probability_failure(belief_state, position, stress_tests)
        confidence = self._confidence(belief_state, position, probability_failure)
        sizing = self.position_sizing.analyze(notional, maximum_expected_loss, confidence)
        model = PositionRiskModel(
            round(maximum_expected_loss, 4),
            expected_drawdown,
            probability_failure,
            round(1 - probability_failure, 4),
            self.invalidity.analyze(position),
            round(position.sensitivity_score, 4),
            round(position.recovery_score, 4),
            sizing["recommended_position_limit"],
            confidence,
            round(belief_state.organizational_confidence * confidence, 4),
        )
        readiness = self.readiness_score(model, position)
        failure_modes = self.failure_mode.analyze(position, stress_tests)
        probability_distribution = (
            {"outcome": "success", "probability": model.probability_of_success, "estimated_gain": round(notional * position.expected_success_gain_pct, 4)},
            {"outcome": "failure", "probability": model.probability_of_failure, "estimated_loss": model.maximum_expected_loss},
        )
        return {
            "exposure": exposure,
            "stop_loss": stop_loss,
            "liquidity": self.liquidity.analyze(position),
            "sensitivity": self.sensitivity.analyze(position),
            "position_risk_model": model.__dict__,
            "position_readiness_score": readiness.__dict__,
            "probability_distribution": probability_distribution,
            "failure_modes": failure_modes,
            "stress_test_results": [test.__dict__ for test in stress_tests],
            "historical_analogues": ({"scenario": "Historical Adversaries", "loss_pct": position.historical_adversary_loss_pct},),
            "recommended_commander_questions": self.commander_questions(model, failure_modes),
            "portfolio_interactions_evaluated": False,
        }

    def readiness_score(self, model: PositionRiskModel, position: ProposedPosition) -> PositionReadinessScore:
        score = round(max(0.0, min(100.0, 100 - model.probability_of_failure * 45 - position.sensitivity_score * 15 - (1 - position.liquidity_score) * 20)), 2)
        if score >= 80:
            category = "Approved"
        elif score >= 65:
            category = "Conditionally Approved"
        elif score >= 50:
            category = "Needs Additional Analysis"
        elif score >= 35:
            category = "Needs Additional Evidence"
        else:
            category = "Reject"
        return PositionReadinessScore(score, category)

    def commander_questions(self, model: PositionRiskModel, failure_modes: tuple[str, ...]) -> tuple[str, ...]:
        questions = [
            "What evidence would invalidate the position before maximum loss is reached?",
            "Can the position be exited if liquidity disappears?",
        ]
        if model.probability_of_failure >= 0.45:
            questions.append("Why is the position acceptable with elevated probability of failure?")
        if "catastrophic_stress_loss" in failure_modes:
            questions.append("What prevents the catastrophic stress path from becoming the base case?")
        return tuple(questions)

    def _probability_failure(self, belief_state: OrganizationalBeliefState, position: ProposedPosition, stress_tests: tuple[PositionStressTestResult, ...]) -> float:
        catastrophic_count = sum(1 for test in stress_tests if test.severity == "catastrophic")
        raw = 0.15 + (1 - belief_state.organizational_confidence) * 0.25 + position.volatility_score * 0.18 + position.sensitivity_score * 0.15 + (1 - position.liquidity_score) * 0.12 + catastrophic_count * 0.04
        return round(max(0.01, min(0.95, raw)), 4)

    def _confidence(self, belief_state: OrganizationalBeliefState, position: ProposedPosition, probability_failure: float) -> float:
        confidence = belief_state.organizational_confidence * 0.55 + belief_state.independent_evidence_score * 0.2 + belief_state.intellectual_diversity_score * 0.15 + position.recovery_score * 0.1 - probability_failure * 0.1
        return round(max(0.0, min(1.0, confidence)), 4)


class PositionRiskOffice:
    """Position Risk Office integrated with the Risk Department framework."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = RiskDepartment(configuration_service, persistence_repository, audit_service, prompt_repository)
        self.office = self.department.offices[POSITION_RISK_OFFICE_ID]
        self.chief = PositionRiskOfficeChief()
        self._latest_review: dict[str, object] | None = None

    def generate_position_risk_report(
        self,
        belief_state: OrganizationalBeliefState,
        position: ProposedPosition,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        """Generate a Position Risk Report as a RAR."""
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        review = self.chief.evaluate(belief_state, position)
        created = utc_timestamp()
        model = review["position_risk_model"]
        payload = {
            "risk_id": f"PR-{document_sequence:06d}",
            "office_id": POSITION_RISK_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "position_risk_assessment",
            "case_file_id": case_file_id,
            "trade_cycle_id": trade_cycle_id,
            "asset": position.asset,
            "position_size": position.position_size,
            "maximum_loss": model["maximum_expected_loss"],
            "expected_loss": model["expected_drawdown"],
            "probability_distribution": review["probability_distribution"],
            "failure_modes": review["failure_modes"],
            "stress_test_results": review["stress_test_results"],
            "historical_analogues": review["historical_analogues"],
            "invalidation_criteria": model["invalidation_conditions"],
            "confidence": model["confidence"],
            "recommended_commander_questions": review["recommended_commander_questions"],
            "position_readiness_score": review["position_readiness_score"],
            "position_risk_model": model,
            "timestamp": created,
            "organizational_belief_state_id": belief_state.state_id,
            "organizational_belief_state_modified": False,
            "portfolio_interactions_evaluated": False,
            "investment_recommendation": None,
            "execution_instruction": None,
            "command_decision": None,
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
            human_summary="Position Risk Report.",
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
        """Route a Position Risk Report through Courier Framework."""
        return self.department.route_rar(POSITION_RISK_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> PositionRiskInstrumentPanel:
        """Return the Position Risk Office instrument panel."""
        base = self.office.instrument_panel()
        if not self._latest_review:
            return PositionRiskInstrumentPanel(base, len(self.office.queue), 0.0, 0.0, 0, 0)
        model = self._latest_review["position_risk_model"]
        return PositionRiskInstrumentPanel(
            base,
            len(self.office.queue),
            float(self._latest_review["exposure"]["notional_exposure"]),
            float(model["expected_drawdown"]),
            len(self._latest_review["stress_test_results"]),
            len(self._latest_review["failure_modes"]),
        )
