"""Analyst-side Behavioral Analysis Office."""

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


BEHAVIORAL_ANALYSIS_OFFICE_ID = "ANALYST-OFFICE-006"


@dataclass(frozen=True)
class BehavioralReasoningObservation:
    """Input observation for deterministic behavioral reasoning."""

    crowd_participation: float
    narrative_velocity: float
    sentiment_score: float
    institutional_accumulation: float
    retail_chase_score: float
    fear_greed_index: int
    regime_stress: float
    bias_intensity: float
    reflexivity_feedback: float


@dataclass(frozen=True)
class BehavioralDecisionModel:
    """Deterministic behavioral decision-support model."""

    model_id: str
    decision_state: str
    drivers: tuple[str, ...]
    inhibitors: tuple[str, ...]


@dataclass(frozen=True)
class BehavioralReasoningGraph:
    """Mandatory reasoning graph for each behavioral conclusion."""

    conclusion_id: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str, str], ...]
    competing_hypotheses: tuple[str, ...]


@dataclass(frozen=True)
class BehavioralProbabilityLandscape:
    """Deterministic scenario landscape for behavioral outcomes."""

    landscape_id: str
    scenarios: tuple[dict[str, float | str], ...]


class CrowdPsychologyAnalyst:
    def analyze(self, observation: BehavioralReasoningObservation) -> dict[str, float | str]:
        return {"crowd_psychology": "crowd_euphoric" if observation.crowd_participation >= 0.7 else "crowd_reserved", "participation": round(observation.crowd_participation, 4)}


class NarrativeAnalyst:
    def analyze(self, observation: BehavioralReasoningObservation) -> dict[str, float | str]:
        return {"narrative": "narrative_accelerating" if observation.narrative_velocity >= 0.6 else "narrative_stable", "velocity": round(observation.narrative_velocity, 4)}


class BehavioralSentimentAnalyst:
    def analyze(self, observation: BehavioralReasoningObservation) -> dict[str, float | str]:
        if observation.sentiment_score >= 0.25:
            state = "sentiment_bullish"
        elif observation.sentiment_score <= -0.25:
            state = "sentiment_bearish"
        else:
            state = "sentiment_neutral"
        return {"sentiment": state, "score": round(observation.sentiment_score, 4)}


class InstitutionalBehaviorAnalyst:
    def analyze(self, observation: BehavioralReasoningObservation) -> dict[str, float | str]:
        return {
            "institutional_behavior": "institutional_accumulation" if observation.institutional_accumulation >= 0.5 else "institutional_distribution",
            "accumulation_score": round(observation.institutional_accumulation, 4),
        }


class RetailBehaviorAnalyst:
    def analyze(self, observation: BehavioralReasoningObservation) -> dict[str, float | str]:
        return {"retail_behavior": "retail_chasing" if observation.retail_chase_score >= 0.65 else "retail_orderly", "chase_score": round(observation.retail_chase_score, 4)}


class FearGreedAnalyst:
    def analyze(self, observation: BehavioralReasoningObservation) -> dict[str, int | str]:
        if observation.fear_greed_index >= 75:
            state = "extreme_greed"
        elif observation.fear_greed_index <= 25:
            state = "extreme_fear"
        else:
            state = "balanced"
        return {"fear_greed": state, "index": observation.fear_greed_index}


class MarketRegimePsychologist:
    def analyze(self, observation: BehavioralReasoningObservation) -> dict[str, float | str]:
        return {"market_regime_psychology": "risk_on_reflexive" if observation.regime_stress >= 0.6 else "risk_balanced", "regime_stress": round(observation.regime_stress, 4)}


class BehavioralBiasAnalyst:
    def analyze(self, observation: BehavioralReasoningObservation) -> dict[str, float | str]:
        return {"behavioral_bias": "bias_elevated" if observation.bias_intensity >= 0.5 else "bias_contained", "bias_intensity": round(observation.bias_intensity, 4)}


class ReflexivityAnalyst:
    def analyze(self, observation: BehavioralReasoningObservation) -> dict[str, float | str]:
        return {"reflexivity": "positive_feedback_loop" if observation.reflexivity_feedback >= 0.6 else "feedback_muted", "feedback": round(observation.reflexivity_feedback, 4)}


class BehavioralAnalysisOfficeChief:
    """Office Chief for deterministic behavioral reasoning."""

    def __init__(self) -> None:
        self.crowd_psychology = CrowdPsychologyAnalyst()
        self.narrative = NarrativeAnalyst()
        self.sentiment = BehavioralSentimentAnalyst()
        self.institutional_behavior = InstitutionalBehaviorAnalyst()
        self.retail_behavior = RetailBehaviorAnalyst()
        self.fear_greed = FearGreedAnalyst()
        self.market_regime_psychologist = MarketRegimePsychologist()
        self.behavioral_bias = BehavioralBiasAnalyst()
        self.reflexivity = ReflexivityAnalyst()

    def analyze(self, observation: BehavioralReasoningObservation) -> dict[str, object]:
        components = {
            "crowd_psychology": self.crowd_psychology.analyze(observation),
            "narrative": self.narrative.analyze(observation),
            "sentiment": self.sentiment.analyze(observation),
            "institutional_behavior": self.institutional_behavior.analyze(observation),
            "retail_behavior": self.retail_behavior.analyze(observation),
            "fear_greed": self.fear_greed.analyze(observation),
            "market_regime_psychology": self.market_regime_psychologist.analyze(observation),
            "behavioral_bias": self.behavioral_bias.analyze(observation),
            "reflexivity": self.reflexivity.analyze(observation),
        }
        landscape = self.probability_landscape(components)
        components["decision_model"] = self.decision_model(components, landscape).__dict__
        components["competing_theses"] = self.competing_theses(components)
        components["probability_landscape"] = landscape.__dict__
        components["behavioral_conclusion"] = self.conclusion(landscape)
        return components

    def decision_model(self, components: dict[str, object], landscape: BehavioralProbabilityLandscape) -> BehavioralDecisionModel:
        top = max(landscape.scenarios, key=lambda scenario: scenario["probability"])
        drivers = self._crowding_reversal_factors(components) if top["scenario"] == "crowding_reversal" else self._trend_persistence_factors(components)
        inhibitors = self._normalization_factors(components)
        return BehavioralDecisionModel(
            "BDM-001",
            "behavioral_risk_elevated" if top["scenario"] == "crowding_reversal" else "behavioral_trend_persistent",
            drivers,
            inhibitors,
        )

    def competing_theses(self, components: dict[str, object]) -> tuple[dict[str, object], ...]:
        return (
            {"thesis_id": "BTA-001", "name": "crowding_reversal", "supporting_factors": self._crowding_reversal_factors(components)},
            {"thesis_id": "BTA-002", "name": "trend_persistence", "supporting_factors": self._trend_persistence_factors(components)},
            {"thesis_id": "BTA-003", "name": "sentiment_normalization", "supporting_factors": self._normalization_factors(components)},
        )

    def probability_landscape(self, components: dict[str, object]) -> BehavioralProbabilityLandscape:
        mania_flags = sum(
            (
                components["crowd_psychology"]["crowd_psychology"] == "crowd_euphoric",
                components["narrative"]["narrative"] == "narrative_accelerating",
                components["retail_behavior"]["retail_behavior"] == "retail_chasing",
                components["fear_greed"]["fear_greed"] == "extreme_greed",
                components["market_regime_psychology"]["market_regime_psychology"] == "risk_on_reflexive",
                components["behavioral_bias"]["behavioral_bias"] == "bias_elevated",
                components["reflexivity"]["reflexivity"] == "positive_feedback_loop",
            )
        )
        persistence_flags = sum(
            (
                components["sentiment"]["sentiment"] == "sentiment_bullish",
                components["institutional_behavior"]["institutional_behavior"] == "institutional_accumulation",
            )
        )
        raw = {
            "crowding_reversal": 0.2 + mania_flags * 0.07,
            "trend_persistence": 0.25 + persistence_flags * 0.1,
            "sentiment_normalization": max(0.1, 0.55 - mania_flags * 0.045),
        }
        total = sum(raw.values())
        scenarios = tuple({"scenario": name, "probability": round(score / total, 4)} for name, score in raw.items())
        return BehavioralProbabilityLandscape("BPL-001", scenarios)

    def reasoning_graphs(self, reasoning: dict[str, object], source_report_ids: tuple[str, ...]) -> tuple[BehavioralReasoningGraph, ...]:
        thesis_ids = tuple(thesis["thesis_id"] for thesis in reasoning["competing_theses"])
        return (
            BehavioralReasoningGraph(
                "BEHAVIORAL-CONCLUSION-001",
                (
                    "claim:behavioral_decision_model",
                    "evidence:crowd_psychology",
                    "evidence:narrative",
                    "evidence:sentiment",
                    "evidence:institutional_behavior",
                    "evidence:retail_behavior",
                    "evidence:reflexivity",
                    "source:" + ",".join(source_report_ids),
                ),
                (
                    ("evidence:crowd_psychology", "claim:behavioral_decision_model", "supports"),
                    ("evidence:narrative", "claim:behavioral_decision_model", "supports"),
                    ("evidence:institutional_behavior", "claim:behavioral_decision_model", "qualifies"),
                    ("evidence:sentiment", "claim:behavioral_decision_model", "challenges"),
                ),
                thesis_ids,
            ),
        )

    def alternative_explanations(self, reasoning: dict[str, object]) -> tuple[str, ...]:
        return (
            "Crowd behavior may reflect temporary attention rather than durable conviction.",
            "Institutional accumulation may offset retail crowding for longer than sentiment signals imply.",
            "Reflexive feedback may normalize without a full behavioral reversal.",
        )

    def conclusion(self, landscape: BehavioralProbabilityLandscape) -> dict[str, float | str]:
        top = max(landscape.scenarios, key=lambda scenario: scenario["probability"])
        return {"primary_scenario": str(top["scenario"]), "probability": float(top["probability"])}

    def _crowding_reversal_factors(self, components: dict[str, object]) -> tuple[str, ...]:
        factors: list[str] = []
        if components["crowd_psychology"]["crowd_psychology"] == "crowd_euphoric":
            factors.append("crowd_euphoric")
        if components["narrative"]["narrative"] == "narrative_accelerating":
            factors.append("narrative_accelerating")
        if components["retail_behavior"]["retail_behavior"] == "retail_chasing":
            factors.append("retail_chasing")
        if components["fear_greed"]["fear_greed"] == "extreme_greed":
            factors.append("extreme_greed")
        if components["reflexivity"]["reflexivity"] == "positive_feedback_loop":
            factors.append("positive_feedback_loop")
        return tuple(factors)

    def _trend_persistence_factors(self, components: dict[str, object]) -> tuple[str, ...]:
        factors: list[str] = []
        if components["sentiment"]["sentiment"] == "sentiment_bullish":
            factors.append("sentiment_bullish")
        if components["institutional_behavior"]["institutional_behavior"] == "institutional_accumulation":
            factors.append("institutional_accumulation")
        if components["market_regime_psychology"]["market_regime_psychology"] == "risk_on_reflexive":
            factors.append("risk_on_reflexive")
        return tuple(factors)

    def _normalization_factors(self, components: dict[str, object]) -> tuple[str, ...]:
        factors: list[str] = []
        if components["crowd_psychology"]["crowd_psychology"] == "crowd_reserved":
            factors.append("crowd_reserved")
        if components["narrative"]["narrative"] == "narrative_stable":
            factors.append("narrative_stable")
        if components["behavioral_bias"]["behavioral_bias"] == "bias_contained":
            factors.append("bias_contained")
        return tuple(factors or ("normalization_thesis_preserved_for_competing_explanation",))


class BehavioralAnalysisOffice:
    """Analyst-side Behavioral Analysis Office integrated with Analyst Department."""

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
        self.office = self.department.offices[BEHAVIORAL_ANALYSIS_OFFICE_ID]
        self.chief = BehavioralAnalysisOfficeChief()

    def generate_behavioral_aar(
        self,
        observation: BehavioralReasoningObservation,
        source_reports: tuple[OperationalContract, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        reasoning = self.chief.analyze(observation)
        source_ids = tuple(report.contract_id for report in source_reports)
        graphs = self.chief.reasoning_graphs(reasoning, source_ids)
        alternatives = self.chief.alternative_explanations(reasoning)
        created = utc_timestamp()
        payload = {
            "office_id": BEHAVIORAL_ANALYSIS_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "behavioral_analytical_assessment",
            "source_report_ids": list(source_ids),
            "behavioral_reasoning": reasoning,
            "behavioral_reasoning_graphs": [graph.__dict__ for graph in graphs],
            "decision_model": reasoning["decision_model"],
            "competing_thesis_analysis": list(reasoning["competing_theses"]),
            "probability_landscape": reasoning["probability_landscape"],
            "alternative_explanations": list(alternatives),
            "seeker_intelligence_modified": False,
            "risk_office_override": False,
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
            human_summary="Behavioral Analytical Assessment Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report

    def route_aar(self, aar: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_aar(BEHAVIORAL_ANALYSIS_OFFICE_ID, aar, target_inbox)

    def instrument_panel(self) -> AnalystOfficeInstrumentPanel:
        return self.office.instrument_panel()
