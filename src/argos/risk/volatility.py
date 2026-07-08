"""Volatility Risk Office."""

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


VOLATILITY_RISK_OFFICE_ID = "RISK-OFFICE-005"


@dataclass(frozen=True)
class VolatilityMarketData:
    """Recorded market data for deterministic volatility analysis."""

    market_id: str
    asset: str
    returns: tuple[float, ...]
    implied_volatility: float
    historical_implied_volatility: tuple[float, ...]
    cross_market_volatilities: dict[str, float]
    current_position_limit: float


@dataclass(frozen=True)
class VolatilityRiskModel:
    """Volatility Risk Model."""

    asset: str
    realized_volatility: float
    implied_volatility: float
    implied_volatility_premium: float
    volatility_regime: str
    forecast_volatility: float
    shock_detected: bool
    contagion_score: float
    organizational_confidence_surface: float


@dataclass(frozen=True)
class VolatilityRegimeRecord:
    """Volatility regime record."""

    record_id: str
    previous_regime: str
    current_regime: str
    transition_recorded: bool


@dataclass(frozen=True)
class VolatilityForecast:
    """Volatility forecast."""

    forecast_id: str
    forecast_volatility: float
    method: str
    inputs: tuple[str, ...]


@dataclass(frozen=True)
class VolatilityEventReport:
    """Volatility event report."""

    event_id: str
    shock_detected: bool
    shock_magnitude: float
    contagion_score: float
    affected_markets: tuple[str, ...]


@dataclass(frozen=True)
class PositionAdjustmentRecommendation:
    """Risk-only volatility adjustment recommendation."""

    recommendation_id: str
    action: str
    adjusted_position_limit: float
    rationale: str


@dataclass(frozen=True)
class ConfidenceAdjustmentRecord:
    """Confidence surface adjustment record."""

    record_id: str
    prior_confidence: float
    adjusted_confidence: float
    adjustment: float


@dataclass(frozen=True)
class VolatilityRiskInstrumentPanel:
    """Volatility Risk Office instrument panel display."""

    base_panel: RiskOfficeInstrumentPanel
    realized_volatility: float
    implied_volatility: float
    forecast_volatility: float
    regime: str
    archived_events: int


class RealizedVolatilityAnalyst:
    def calculate(self, returns: tuple[float, ...]) -> float:
        if len(returns) < 2:
            raise ValueError("realized volatility requires at least two returns")
        mean = sum(returns) / len(returns)
        variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
        return round(math.sqrt(variance) * math.sqrt(252), 4)


class ImpliedVolatilityAnalyst:
    def evaluate(self, implied_volatility: float, realized_volatility: float, history: tuple[float, ...]) -> dict[str, float | str]:
        baseline = sum(history) / len(history) if history else implied_volatility
        premium = implied_volatility - realized_volatility
        percentile_proxy = sum(1 for value in history if value <= implied_volatility) / len(history) if history else 1.0
        state = "implied_volatility_elevated" if implied_volatility > baseline * 1.15 else "implied_volatility_normal"
        return {"implied_volatility": round(implied_volatility, 4), "premium": round(premium, 4), "percentile_proxy": round(percentile_proxy, 4), "state": state}


class VolatilityRegimeClassifier:
    def classify(self, realized_volatility: float, implied_volatility: float) -> str:
        blended = realized_volatility * 0.55 + implied_volatility * 0.45
        if blended >= 0.45:
            return "crisis_volatility"
        if blended >= 0.28:
            return "elevated_volatility"
        if blended >= 0.16:
            return "normal_volatility"
        return "suppressed_volatility"


class VolatilityForecastEngine:
    def forecast(self, realized_volatility: float, implied_volatility: float, shock_magnitude: float) -> VolatilityForecast:
        forecast = round(realized_volatility * 0.55 + implied_volatility * 0.35 + shock_magnitude * 0.10, 4)
        return VolatilityForecast("VF-001", forecast, "weighted_realized_implied_shock", ("realized_volatility", "implied_volatility", "shock_magnitude"))


class VolatilityShockDetector:
    def detect(self, returns: tuple[float, ...], realized_volatility: float) -> dict[str, float | bool]:
        latest_abs = abs(returns[-1])
        daily_realized = realized_volatility / math.sqrt(252)
        threshold = daily_realized * 2.5
        magnitude = latest_abs / threshold if threshold else 0.0
        return {"shock_detected": latest_abs >= threshold, "shock_magnitude": round(magnitude, 4)}


class VolatilityContagionEvaluator:
    def evaluate(self, cross_market_volatilities: dict[str, float], realized_volatility: float) -> dict[str, float | tuple[str, ...]]:
        affected = tuple(sorted(market for market, volatility in cross_market_volatilities.items() if volatility >= realized_volatility * 0.8))
        score = round(len(affected) / max(1, len(cross_market_volatilities)), 4)
        return {"contagion_score": score, "affected_markets": affected}


class VolatilityAdjustmentEngine:
    def recommend(self, current_limit: float, forecast_volatility: float, shock_detected: bool, contagion_score: float) -> PositionAdjustmentRecommendation:
        reduction = min(0.65, forecast_volatility * 0.6 + contagion_score * 0.2 + (0.15 if shock_detected else 0.0))
        adjusted_limit = round(current_limit * (1 - reduction), 4)
        if reduction >= 0.45:
            action = "reduce_risk_limit_materially"
        elif reduction >= 0.25:
            action = "reduce_risk_limit_moderately"
        else:
            action = "maintain_with_volatility_monitoring"
        return PositionAdjustmentRecommendation("PAR-001", action, adjusted_limit, "Volatility-adjusted risk limit; not an investment recommendation or execution instruction.")


class VolatilityArchive:
    def historical_archive(self, market_data: VolatilityMarketData, realized_volatility: float) -> dict[str, object]:
        return {"archive_id": "HVA-001", "asset": market_data.asset, "return_count": len(market_data.returns), "realized_volatility": realized_volatility}

    def implied_archive(self, market_data: VolatilityMarketData) -> dict[str, object]:
        return {"archive_id": "IVA-001", "asset": market_data.asset, "implied_volatility": round(market_data.implied_volatility, 4), "history_count": len(market_data.historical_implied_volatility)}

    def event_archive(self, event_report: VolatilityEventReport) -> dict[str, object]:
        return {"archive_id": "VEA-001", "event_id": event_report.event_id, "shock_detected": event_report.shock_detected, "contagion_score": event_report.contagion_score}


class VolatilityRiskOfficeChief:
    """Office Chief for volatility risk analysis."""

    def __init__(self) -> None:
        self.realized = RealizedVolatilityAnalyst()
        self.implied = ImpliedVolatilityAnalyst()
        self.regime = VolatilityRegimeClassifier()
        self.forecast_engine = VolatilityForecastEngine()
        self.shock = VolatilityShockDetector()
        self.contagion = VolatilityContagionEvaluator()
        self.adjustment = VolatilityAdjustmentEngine()
        self.archive = VolatilityArchive()

    def evaluate(self, belief_state: OrganizationalBeliefState, market_data: VolatilityMarketData, previous_regime: str) -> dict[str, object]:
        if not isinstance(belief_state, OrganizationalBeliefState):
            raise TypeError("Volatility Risk Office requires an OrganizationalBeliefState")
        realized = self.realized.calculate(market_data.returns)
        implied = self.implied.evaluate(market_data.implied_volatility, realized, market_data.historical_implied_volatility)
        current_regime = self.regime.classify(realized, market_data.implied_volatility)
        shock = self.shock.detect(market_data.returns, realized)
        contagion = self.contagion.evaluate(market_data.cross_market_volatilities, realized)
        forecast = self.forecast_engine.forecast(realized, market_data.implied_volatility, float(shock["shock_magnitude"]))
        confidence = self.confidence_adjustment(belief_state, forecast.forecast_volatility, bool(shock["shock_detected"]), float(contagion["contagion_score"]))
        model = VolatilityRiskModel(
            market_data.asset,
            realized,
            round(market_data.implied_volatility, 4),
            float(implied["premium"]),
            current_regime,
            forecast.forecast_volatility,
            bool(shock["shock_detected"]),
            float(contagion["contagion_score"]),
            confidence.adjusted_confidence,
        )
        event = VolatilityEventReport("VER-001", bool(shock["shock_detected"]), float(shock["shock_magnitude"]), float(contagion["contagion_score"]), contagion["affected_markets"])
        return {
            "volatility_risk_model": model.__dict__,
            "implied_volatility_analysis": implied,
            "volatility_regime_record": VolatilityRegimeRecord("VRR-001", previous_regime, current_regime, previous_regime != current_regime).__dict__,
            "volatility_forecast": forecast.__dict__,
            "volatility_event_report": event.__dict__,
            "position_adjustment_recommendation": self.adjustment.recommend(market_data.current_position_limit, forecast.forecast_volatility, bool(shock["shock_detected"]), float(contagion["contagion_score"])).__dict__,
            "confidence_adjustment_record": confidence.__dict__,
            "historical_volatility_archive": self.archive.historical_archive(market_data, realized),
            "implied_volatility_archive": self.archive.implied_archive(market_data),
            "volatility_event_archive": self.archive.event_archive(event),
        }

    def confidence_adjustment(self, belief_state: OrganizationalBeliefState, forecast_volatility: float, shock_detected: bool, contagion_score: float) -> ConfidenceAdjustmentRecord:
        adjustment = round(-(forecast_volatility * 0.12 + contagion_score * 0.05 + (0.04 if shock_detected else 0.0)), 4)
        adjusted = round(max(0.0, min(1.0, belief_state.organizational_confidence + adjustment)), 4)
        return ConfidenceAdjustmentRecord("CAR-001", belief_state.organizational_confidence, adjusted, adjustment)


class VolatilityRiskOffice:
    """Volatility Risk Office integrated with the Risk Department framework."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = RiskDepartment(configuration_service, persistence_repository, audit_service, prompt_repository)
        self.office = self.department.offices[VOLATILITY_RISK_OFFICE_ID]
        self.chief = VolatilityRiskOfficeChief()
        self._latest_review: dict[str, object] | None = None

    def generate_volatility_risk_report(
        self,
        belief_state: OrganizationalBeliefState,
        market_data: VolatilityMarketData,
        previous_regime: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        """Generate a Volatility Risk Report as a RAR."""
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        review = self.chief.evaluate(belief_state, market_data, previous_regime)
        created = utc_timestamp()
        payload = {
            "risk_id": f"VOL-{document_sequence:06d}",
            "office_id": VOLATILITY_RISK_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "volatility_risk_assessment",
            "case_file_id": case_file_id,
            "trade_cycle_id": trade_cycle_id,
            "market_id": market_data.market_id,
            "asset": market_data.asset,
            "volatility_risk_report": review["volatility_risk_model"],
            "volatility_event_report": review["volatility_event_report"],
            "organizational_volatility_summary": {
                "asset": market_data.asset,
                "regime": review["volatility_risk_model"]["volatility_regime"],
                "forecast_volatility": review["volatility_forecast"]["forecast_volatility"],
                "organizational_confidence_surface": review["volatility_risk_model"]["organizational_confidence_surface"],
            },
            "volatility_regime_record": review["volatility_regime_record"],
            "volatility_forecast": review["volatility_forecast"],
            "position_adjustment_recommendation": review["position_adjustment_recommendation"],
            "confidence_adjustment_record": review["confidence_adjustment_record"],
            "historical_volatility_archive": review["historical_volatility_archive"],
            "implied_volatility_archive": review["implied_volatility_archive"],
            "volatility_event_archive": review["volatility_event_archive"],
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
            human_summary="Volatility Risk Report.",
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
        """Route a Volatility Risk Report through Courier Framework."""
        return self.department.route_rar(VOLATILITY_RISK_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> VolatilityRiskInstrumentPanel:
        """Return the Volatility Risk Office instrument panel."""
        base = self.office.instrument_panel()
        if not self._latest_review:
            return VolatilityRiskInstrumentPanel(base, 0.0, 0.0, 0.0, "unknown", 0)
        model = self._latest_review["volatility_risk_model"]
        return VolatilityRiskInstrumentPanel(
            base,
            float(model["realized_volatility"]),
            float(model["implied_volatility"]),
            float(model["forecast_volatility"]),
            str(model["volatility_regime"]),
            1,
        )
