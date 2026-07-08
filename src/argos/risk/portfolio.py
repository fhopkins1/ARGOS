"""Portfolio Risk Office."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

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


PORTFOLIO_RISK_OFFICE_ID = "RISK-OFFICE-002"


@dataclass(frozen=True)
class PortfolioPosition:
    """Single position input for portfolio-level risk review."""

    asset: str
    market_value: float
    sector: str
    geography: str
    macro_factor: str
    liquidity_score: float
    volatility_score: float
    confidence: float
    return_series: tuple[float, ...]


@dataclass(frozen=True)
class PortfolioRiskObservation:
    """Portfolio-level risk observation."""

    portfolio_id: str
    positions: tuple[PortfolioPosition, ...]


@dataclass(frozen=True)
class CorrelationMatrix:
    """Deterministic portfolio correlation matrix."""

    assets: tuple[str, ...]
    matrix: tuple[tuple[float, ...], ...]
    average_correlation: float


@dataclass(frozen=True)
class PortfolioStressTestResult:
    """Portfolio stress test result."""

    scenario: str
    loss_amount: float
    loss_pct: float
    affected_assets: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalAdversary:
    """Historical adversary library scenario."""

    adversary_id: str
    name: str
    shock_pct: float
    affected_macro_factor: str


@dataclass(frozen=True)
class PortfolioRiskModel:
    """Portfolio Risk Model."""

    portfolio_id: str
    total_exposure: float
    concentration_score: float
    diversification_score: float
    average_correlation: float
    systemic_risk_score: float
    failure_cascade_count: int
    organizational_confidence_surface: float


@dataclass(frozen=True)
class PortfolioReadinessScore:
    """Portfolio Readiness Score."""

    score: float
    category: str


@dataclass(frozen=True)
class PortfolioRiskInstrumentPanel:
    """Portfolio Risk Office instrument panel display."""

    base_panel: RiskOfficeInstrumentPanel
    reviewed_portfolios: int
    total_exposure: float
    maximum_position_exposure: float
    average_correlation: float
    stress_tests: int
    failure_cascades: int


class CorrelationAnalyst:
    def matrix(self, positions: tuple[PortfolioPosition, ...]) -> CorrelationMatrix:
        assets = tuple(position.asset for position in positions)
        matrix = tuple(
            tuple(round(_correlation(left.return_series, right.return_series), 4) for right in positions)
            for left in positions
        )
        values = [abs(value) for row_index, row in enumerate(matrix) for column_index, value in enumerate(row) if row_index < column_index]
        average = round(sum(values) / len(values), 4) if values else 1.0
        return CorrelationMatrix(assets, matrix, average)


class ConcentrationAnalyst:
    def analyze(self, positions: tuple[PortfolioPosition, ...]) -> dict[str, float | str]:
        total = _total_exposure(positions)
        max_weight = max((position.market_value / total for position in positions), default=0)
        return {"max_position_weight": round(max_weight, 4), "concentration_score": round(max_weight, 4)}


class DiversificationAnalyst:
    def analyze(self, positions: tuple[PortfolioPosition, ...], average_correlation: float) -> dict[str, float | int]:
        sectors = {position.sector for position in positions}
        geographies = {position.geography for position in positions}
        score = (len(sectors) / max(1, len(positions)) * 0.4) + (len(geographies) / max(1, len(positions)) * 0.3) + ((1 - average_correlation) * 0.3)
        return {"sector_count": len(sectors), "geography_count": len(geographies), "diversification_score": round(max(0.0, min(1.0, score)), 4)}


class SectorExposureAnalyst:
    def analyze(self, positions: tuple[PortfolioPosition, ...]) -> dict[str, float]:
        return _exposure_by(positions, "sector")


class GeographicExposureAnalyst:
    def analyze(self, positions: tuple[PortfolioPosition, ...]) -> dict[str, float]:
        return _exposure_by(positions, "geography")


class MacroeconomicExposureAnalyst:
    def analyze(self, positions: tuple[PortfolioPosition, ...]) -> dict[str, float]:
        return _exposure_by(positions, "macro_factor")


class SystemicRiskAnalyst:
    def analyze(self, average_correlation: float, concentration_score: float, diversification_score: float) -> dict[str, float | str]:
        score = round(average_correlation * 0.4 + concentration_score * 0.35 + (1 - diversification_score) * 0.25, 4)
        state = "systemic_risk_elevated" if score >= 0.6 else "systemic_risk_watch" if score >= 0.35 else "systemic_risk_contained"
        return {"systemic_risk_score": score, "systemic_risk_state": state}


class PortfolioStressAnalyst:
    def analyze(self, positions: tuple[PortfolioPosition, ...], adversaries: tuple[HistoricalAdversary, ...]) -> tuple[PortfolioStressTestResult, ...]:
        total = _total_exposure(positions)
        scenarios = [
            ("Market Crash", -0.22, tuple(position.asset for position in positions)),
            ("Liquidity Collapse", -sum((1 - position.liquidity_score) * position.market_value for position in positions) / total, tuple(position.asset for position in positions if position.liquidity_score < 0.6)),
            ("Volatility Spike", -sum(position.volatility_score * 0.18 * position.market_value for position in positions) / total, tuple(position.asset for position in positions if position.volatility_score >= 0.6)),
        ]
        for adversary in adversaries:
            affected = tuple(position.asset for position in positions if position.macro_factor == adversary.affected_macro_factor)
            exposure = sum(position.market_value for position in positions if position.asset in affected)
            scenarios.append((adversary.name, adversary.shock_pct * (exposure / total if total else 0), affected))
        return tuple(
            PortfolioStressTestResult(name, round(abs(total * shock), 4), round(abs(shock), 4), affected)
            for name, shock, affected in scenarios
        )


class FailureCascadeAnalyst:
    def analyze(self, positions: tuple[PortfolioPosition, ...], matrix: CorrelationMatrix) -> tuple[dict[str, object], ...]:
        cascades = []
        for row_index, left in enumerate(positions):
            for column_index, right in enumerate(positions):
                if row_index >= column_index:
                    continue
                correlated = abs(matrix.matrix[row_index][column_index]) >= 0.8
                shared_sector = left.sector == right.sector
                if correlated or shared_sector:
                    cascades.append(
                        {
                            "trigger_asset": left.asset,
                            "affected_asset": right.asset,
                            "reason": "high_correlation" if correlated else "shared_sector",
                        }
                    )
        return tuple(cascades)


class HistoricalAdversaryLibrary:
    def adversaries(self) -> tuple[HistoricalAdversary, ...]:
        return (
            HistoricalAdversary("HAL-2008", "Credit Crisis", -0.28, "growth"),
            HistoricalAdversary("HAL-2020", "Pandemic Liquidity Shock", -0.18, "liquidity"),
            HistoricalAdversary("HAL-2022", "Rate Shock", -0.16, "duration"),
        )


class PortfolioRiskOfficeChief:
    """Office Chief for portfolio-level risk review."""

    def __init__(self) -> None:
        self.correlation = CorrelationAnalyst()
        self.concentration = ConcentrationAnalyst()
        self.diversification = DiversificationAnalyst()
        self.sector_exposure = SectorExposureAnalyst()
        self.geographic_exposure = GeographicExposureAnalyst()
        self.macro_exposure = MacroeconomicExposureAnalyst()
        self.systemic_risk = SystemicRiskAnalyst()
        self.portfolio_stress = PortfolioStressAnalyst()
        self.failure_cascade = FailureCascadeAnalyst()
        self.hal = HistoricalAdversaryLibrary()

    def evaluate(self, belief_state: OrganizationalBeliefState, observation: PortfolioRiskObservation) -> dict[str, object]:
        if not isinstance(belief_state, OrganizationalBeliefState):
            raise TypeError("Portfolio Risk Office requires an OrganizationalBeliefState")
        if not observation.positions:
            raise ValueError("portfolio risk review requires at least one position")
        matrix = self.correlation.matrix(observation.positions)
        concentration = self.concentration.analyze(observation.positions)
        diversification = self.diversification.analyze(observation.positions, matrix.average_correlation)
        systemic = self.systemic_risk.analyze(float(matrix.average_correlation), float(concentration["concentration_score"]), float(diversification["diversification_score"]))
        adversaries = self.hal.adversaries()
        stress_tests = self.portfolio_stress.analyze(observation.positions, adversaries)
        cascades = self.failure_cascade.analyze(observation.positions, matrix)
        confidence_surface = self.confidence_surface(belief_state, observation, systemic["systemic_risk_score"], len(cascades))
        model = PortfolioRiskModel(
            observation.portfolio_id,
            round(_total_exposure(observation.positions), 4),
            float(concentration["concentration_score"]),
            float(diversification["diversification_score"]),
            matrix.average_correlation,
            float(systemic["systemic_risk_score"]),
            len(cascades),
            confidence_surface,
        )
        readiness = self.readiness_score(model)
        return {
            "correlation_matrix": matrix.__dict__,
            "concentration": concentration,
            "diversification": diversification,
            "sector_exposure": self.sector_exposure.analyze(observation.positions),
            "geographic_exposure": self.geographic_exposure.analyze(observation.positions),
            "macroeconomic_exposure": self.macro_exposure.analyze(observation.positions),
            "systemic_risk": systemic,
            "historical_adversary_library": [adversary.__dict__ for adversary in adversaries],
            "portfolio_stress_tests": [test.__dict__ for test in stress_tests],
            "failure_cascades": cascades,
            "portfolio_risk_model": model.__dict__,
            "portfolio_readiness_score": readiness.__dict__,
            "organizational_confidence_surface": confidence_surface,
        }

    def readiness_score(self, model: PortfolioRiskModel) -> PortfolioReadinessScore:
        score = round(max(0.0, min(100.0, 100 - model.systemic_risk_score * 40 - model.concentration_score * 20 - model.failure_cascade_count * 5 + model.diversification_score * 10)), 2)
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
        return PortfolioReadinessScore(score, category)

    def confidence_surface(self, belief_state: OrganizationalBeliefState, observation: PortfolioRiskObservation, systemic_score: float, cascade_count: int) -> float:
        average_position_confidence = sum(position.confidence for position in observation.positions) / len(observation.positions)
        surface = belief_state.organizational_confidence * 0.45 + average_position_confidence * 0.35 + belief_state.independent_evidence_score * 0.1 + belief_state.intellectual_diversity_score * 0.1 - systemic_score * 0.08 - cascade_count * 0.015
        return round(max(0.0, min(1.0, surface)), 4)


class PortfolioRiskOffice:
    """Portfolio Risk Office integrated with the Risk Department framework."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = RiskDepartment(configuration_service, persistence_repository, audit_service, prompt_repository)
        self.office = self.department.offices[PORTFOLIO_RISK_OFFICE_ID]
        self.chief = PortfolioRiskOfficeChief()
        self._latest_review: dict[str, object] | None = None

    def generate_portfolio_risk_report(
        self,
        belief_state: OrganizationalBeliefState,
        observation: PortfolioRiskObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        """Generate a Portfolio Risk Report as a RAR."""
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        review = self.chief.evaluate(belief_state, observation)
        created = utc_timestamp()
        payload = {
            "risk_id": f"POR-{document_sequence:06d}",
            "office_id": PORTFOLIO_RISK_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "portfolio_risk_assessment",
            "portfolio_id": observation.portfolio_id,
            "case_file_id": case_file_id,
            "trade_cycle_id": trade_cycle_id,
            "positions": [position.__dict__ for position in observation.positions],
            "portfolio_risk_model": review["portfolio_risk_model"],
            "portfolio_readiness_score": review["portfolio_readiness_score"],
            "correlation_matrix": review["correlation_matrix"],
            "portfolio_stress_tests": review["portfolio_stress_tests"],
            "historical_adversary_library": review["historical_adversary_library"],
            "failure_cascades": review["failure_cascades"],
            "organizational_confidence_surface": review["organizational_confidence_surface"],
            "organizational_belief_state_id": belief_state.state_id,
            "organizational_belief_state_modified": False,
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
            human_summary="Portfolio Risk Report.",
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
        """Route a Portfolio Risk Report through Courier Framework."""
        return self.department.route_rar(PORTFOLIO_RISK_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> PortfolioRiskInstrumentPanel:
        """Return the Portfolio Risk Office instrument panel."""
        base = self.office.instrument_panel()
        if not self._latest_review:
            return PortfolioRiskInstrumentPanel(base, len(self.office.queue), 0.0, 0.0, 0.0, 0, 0)
        model = self._latest_review["portfolio_risk_model"]
        return PortfolioRiskInstrumentPanel(
            base,
            len(self.office.queue),
            float(model["total_exposure"]),
            float(model["concentration_score"]) * float(model["total_exposure"]),
            float(model["average_correlation"]),
            len(self._latest_review["portfolio_stress_tests"]),
            int(model["failure_cascade_count"]),
        )


def _total_exposure(positions: tuple[PortfolioPosition, ...]) -> float:
    return sum(position.market_value for position in positions)


def _exposure_by(positions: tuple[PortfolioPosition, ...], field_name: str) -> dict[str, float]:
    total = _total_exposure(positions)
    exposure: dict[str, float] = {}
    for position in positions:
        key = str(getattr(position, field_name))
        exposure[key] = exposure.get(key, 0.0) + position.market_value
    return {key: round(value / total, 4) for key, value in sorted(exposure.items())}


def _correlation(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("correlation requires equal non-empty series")
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    left_variance = sum((x - left_mean) ** 2 for x in left)
    right_variance = sum((y - right_mean) ** 2 for y in right)
    if left_variance == 0 or right_variance == 0:
        return 0.0
    return numerator / math.sqrt(left_variance * right_variance)
