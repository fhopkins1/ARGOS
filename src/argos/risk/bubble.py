"""Bubble Detection Office."""

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


BUBBLE_DETECTION_OFFICE_ID = "RISK-OFFICE-008"


@dataclass(frozen=True)
class BubbleMarketObservation:
    """Market observation for deterministic bubble detection."""

    market_id: str
    asset: str
    price_to_fundamental_value: float
    revenue_growth: float
    price_growth: float
    retail_participation: float
    leverage_growth: float
    narrative_intensity: float
    media_concentration: float
    liquidity_growth: float
    credit_growth: float
    historical_bubble_markers: tuple[str, ...]


@dataclass(frozen=True)
class BubbleProgressionReport:
    """Bubble progression classification."""

    report_id: str
    stage: str
    stage_score: float


@dataclass(frozen=True)
class CollapseVulnerabilityAssessment:
    """Collapse vulnerability assessment."""

    assessment_id: str
    vulnerability_score: float
    vulnerability_state: str


@dataclass(frozen=True)
class ExecutiveBubbleWarning:
    """Executive bubble warning."""

    warning_id: str
    severity: str
    message: str


@dataclass(frozen=True)
class BubbleRiskInstrumentPanel:
    """Bubble Detection Office instrument panel."""

    base_panel: RiskOfficeInstrumentPanel
    latest_stage: str
    valuation_divergence: float
    collapse_vulnerability: float
    archived_episodes: int


class ValuationDivergenceAnalyst:
    def evaluate(self, observation: BubbleMarketObservation) -> dict[str, float | str]:
        divergence = max(0.0, observation.price_to_fundamental_value - 1)
        state = "valuation_extreme" if divergence >= 1.0 else "valuation_elevated" if divergence >= 0.4 else "valuation_contained"
        return {"divergence": round(divergence, 4), "state": state}


class SpeculativeBehaviorAnalyst:
    def evaluate(self, observation: BubbleMarketObservation) -> dict[str, float | str]:
        score = observation.retail_participation * 0.45 + observation.leverage_growth * 0.35 + max(0, observation.price_growth - observation.revenue_growth) * 0.2
        score = round(max(0.0, min(1.0, score)), 4)
        return {"speculation_score": score, "state": "speculation_extreme" if score >= 0.7 else "speculation_elevated" if score >= 0.45 else "speculation_contained"}


class NarrativeDominanceAnalyst:
    def evaluate(self, observation: BubbleMarketObservation) -> dict[str, float | str]:
        score = round(max(0.0, min(1.0, observation.narrative_intensity * 0.6 + observation.media_concentration * 0.4)), 4)
        return {"narrative_dominance_score": score, "state": "narrative_dominant" if score >= 0.7 else "narrative_competing"}


class LiquidityExpansionAnalyst:
    def evaluate(self, observation: BubbleMarketObservation) -> dict[str, float | str]:
        score = round(max(0.0, min(1.0, observation.liquidity_growth * 0.55 + observation.credit_growth * 0.45)), 4)
        return {"liquidity_expansion_score": score, "state": "liquidity_expansion_aggressive" if score >= 0.65 else "liquidity_expansion_moderate"}


class BubbleProgressionClassifier:
    def classify(self, valuation: float, speculation: float, narrative: float, liquidity: float) -> BubbleProgressionReport:
        score = round(valuation * 0.3 + speculation * 0.25 + narrative * 0.25 + liquidity * 0.2, 4)
        if score >= 0.8:
            stage = "mania"
        elif score >= 0.6:
            stage = "acceleration"
        elif score >= 0.4:
            stage = "formation"
        else:
            stage = "normal"
        return BubbleProgressionReport("BPR-001", stage, score)


class HistoricalBubbleAnalogAnalyzer:
    def compare(self, observation: BubbleMarketObservation, stage_score: float) -> dict[str, object]:
        analogs = (
            {"analog_id": "HBA-2000", "name": "Dot-Com Bubble", "similarity": round(min(1.0, stage_score * 0.95 + observation.narrative_intensity * 0.05), 4)},
            {"analog_id": "HBA-2007", "name": "Housing Credit Bubble", "similarity": round(min(1.0, stage_score * 0.75 + observation.credit_growth * 0.25), 4)},
            {"analog_id": "HBA-2021", "name": "Speculative Retail Bubble", "similarity": round(min(1.0, stage_score * 0.7 + observation.retail_participation * 0.3), 4)},
        )
        closest = max(analogs, key=lambda item: item["similarity"])
        return {"report_id": "HBAR-001", "analogs": analogs, "closest_analog": closest}


class CollapseVulnerabilityEvaluator:
    def evaluate(self, stage_score: float, leverage_growth: float, liquidity_growth: float, confidence: float) -> CollapseVulnerabilityAssessment:
        score = round(max(0.0, min(1.0, stage_score * 0.45 + leverage_growth * 0.25 + (1 - liquidity_growth) * 0.15 + (1 - confidence) * 0.15)), 4)
        state = "collapse_vulnerability_high" if score >= 0.7 else "collapse_vulnerability_watch" if score >= 0.45 else "collapse_vulnerability_contained"
        return CollapseVulnerabilityAssessment("CVA-001", score, state)


class BubbleEpisodeArchive:
    def archive(self, observation: BubbleMarketObservation, progression: BubbleProgressionReport, vulnerability: CollapseVulnerabilityAssessment) -> dict[str, object]:
        return {
            "archive_id": "BEA-001",
            "asset": observation.asset,
            "stage": progression.stage,
            "stage_score": progression.stage_score,
            "vulnerability_score": vulnerability.vulnerability_score,
            "historical_markers": observation.historical_bubble_markers,
        }


class BubbleDetectionOfficeChief:
    """Office Chief for deterministic bubble detection."""

    def __init__(self) -> None:
        self.valuation = ValuationDivergenceAnalyst()
        self.speculation = SpeculativeBehaviorAnalyst()
        self.narrative = NarrativeDominanceAnalyst()
        self.liquidity = LiquidityExpansionAnalyst()
        self.progression = BubbleProgressionClassifier()
        self.historical = HistoricalBubbleAnalogAnalyzer()
        self.vulnerability = CollapseVulnerabilityEvaluator()
        self.archive = BubbleEpisodeArchive()

    def evaluate(self, belief_state: OrganizationalBeliefState, observation: BubbleMarketObservation) -> dict[str, object]:
        if not isinstance(belief_state, OrganizationalBeliefState):
            raise TypeError("Bubble Detection Office requires an OrganizationalBeliefState")
        valuation = self.valuation.evaluate(observation)
        speculation = self.speculation.evaluate(observation)
        narrative = self.narrative.evaluate(observation)
        liquidity = self.liquidity.evaluate(observation)
        progression = self.progression.classify(float(valuation["divergence"]), float(speculation["speculation_score"]), float(narrative["narrative_dominance_score"]), float(liquidity["liquidity_expansion_score"]))
        historical = self.historical.compare(observation, progression.stage_score)
        vulnerability = self.vulnerability.evaluate(progression.stage_score, observation.leverage_growth, observation.liquidity_growth, belief_state.organizational_confidence)
        confidence = self.confidence_adjustment(belief_state, progression.stage_score, vulnerability.vulnerability_score)
        warning = self.warning(progression, vulnerability)
        return {
            "bubble_assessment_report": {"report_id": "BAR-001", "asset": observation.asset, "sustainability_focus": True, "exact_peak_forecast_attempted": False},
            "bubble_progression_report": progression.__dict__,
            "valuation_divergence_assessment": valuation,
            "speculative_behavior_assessment": speculation,
            "narrative_dominance_report": narrative,
            "liquidity_expansion_report": liquidity,
            "historical_bubble_analog_report": historical,
            "collapse_vulnerability_assessment": vulnerability.__dict__,
            "executive_bubble_warning": warning.__dict__,
            "bubble_episode_archive": self.archive.archive(observation, progression, vulnerability),
            "confidence_adjustment_record": confidence,
        }

    def warning(self, progression: BubbleProgressionReport, vulnerability: CollapseVulnerabilityAssessment) -> ExecutiveBubbleWarning:
        if progression.stage == "mania" or vulnerability.vulnerability_score >= 0.7:
            severity = "high"
        elif progression.stage in {"acceleration", "formation"}:
            severity = "watch"
        else:
            severity = "low"
        return ExecutiveBubbleWarning("EBW-001", severity, "Defensive organizational review recommended; this is not an investment recommendation or execution instruction.")

    def confidence_adjustment(self, belief_state: OrganizationalBeliefState, stage_score: float, vulnerability_score: float) -> dict[str, float | str]:
        adjustment = round(-(stage_score * 0.08 + vulnerability_score * 0.1), 4)
        adjusted = round(max(0.0, min(1.0, belief_state.organizational_confidence + adjustment)), 4)
        return {"record_id": "BCAR-001", "prior_confidence": belief_state.organizational_confidence, "adjusted_confidence": adjusted, "adjustment": adjustment}


class BubbleDetectionOffice:
    """Bubble Detection Office integrated with the Risk Department framework."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = RiskDepartment(configuration_service, persistence_repository, audit_service, prompt_repository)
        self.office = self.department.offices[BUBBLE_DETECTION_OFFICE_ID]
        self.chief = BubbleDetectionOfficeChief()
        self._latest_review: dict[str, object] | None = None

    def generate_bubble_risk_report(
        self,
        belief_state: OrganizationalBeliefState,
        observation: BubbleMarketObservation,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        """Generate a Bubble Assessment Report as a RAR."""
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        review = self.chief.evaluate(belief_state, observation)
        created = utc_timestamp()
        payload = {
            "risk_id": f"BUB-{document_sequence:06d}",
            "office_id": BUBBLE_DETECTION_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "bubble_detection_assessment",
            "case_file_id": case_file_id,
            "trade_cycle_id": trade_cycle_id,
            "market_id": observation.market_id,
            "asset": observation.asset,
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
            human_summary="Bubble Assessment Report.",
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
        """Route a Bubble Assessment Report through Courier Framework."""
        return self.department.route_rar(BUBBLE_DETECTION_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> BubbleRiskInstrumentPanel:
        """Return the Bubble Detection Office instrument panel."""
        base = self.office.instrument_panel()
        if not self._latest_review:
            return BubbleRiskInstrumentPanel(base, "unknown", 0.0, 0.0, 0)
        progression = self._latest_review["bubble_progression_report"]
        valuation = self._latest_review["valuation_divergence_assessment"]
        vulnerability = self._latest_review["collapse_vulnerability_assessment"]
        return BubbleRiskInstrumentPanel(
            base,
            str(progression["stage"]),
            float(valuation["divergence"]),
            float(vulnerability["vulnerability_score"]),
            1,
        )
