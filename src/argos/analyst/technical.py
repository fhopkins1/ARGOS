"""Analyst-side Technical Analysis Office."""

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


ANALYST_TECHNICAL_OFFICE_ID = "ANALYST-OFFICE-002"


@dataclass(frozen=True)
class TechnicalReasoningObservation:
    """Input observation for deterministic analyst-side technical reasoning."""

    closes: tuple[float, ...]
    highs: tuple[float, ...]
    lows: tuple[float, ...]
    volumes: tuple[float, ...]
    benchmark_closes: tuple[float, ...]
    historical_pattern_successes: int
    historical_pattern_trials: int
    timeframe_alignment_score: float


@dataclass(frozen=True)
class TechnicalArgumentGraph:
    """Mandatory argument graph for each technical conclusion."""

    conclusion_id: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str, str], ...]
    contradictory_evidence: tuple[str, ...]


class TrendAnalyst:
    def analyze(self, observation: TechnicalReasoningObservation) -> dict[str, float | str]:
        change = observation.closes[-1] - observation.closes[0]
        return {"trend": "rising" if change > 0 else "falling" if change < 0 else "flat", "change": round(change, 4)}


class MomentumAnalyst:
    def analyze(self, observation: TechnicalReasoningObservation) -> dict[str, float | str]:
        momentum = observation.closes[-1] - observation.closes[-2]
        return {"momentum": "positive" if momentum > 0 else "negative" if momentum < 0 else "neutral", "value": round(momentum, 4)}


class MarketStructureAnalyst:
    def analyze(self, observation: TechnicalReasoningObservation) -> dict[str, str]:
        higher_high = observation.highs[-1] > observation.highs[-2]
        higher_low = observation.lows[-1] > observation.lows[-2]
        structure = "higher_high_higher_low" if higher_high and higher_low else "mixed_structure"
        return {"structure": structure}


class VolumeAnalyst:
    def analyze(self, observation: TechnicalReasoningObservation) -> dict[str, float | str]:
        prior_average = sum(observation.volumes[:-1]) / max(1, len(observation.volumes) - 1)
        ratio = observation.volumes[-1] / prior_average if prior_average else 0
        return {"volume_state": "expanding" if ratio > 1 else "normal", "ratio": round(ratio, 4)}


class PatternReliabilityAnalyst:
    def evaluate(self, successes: int, trials: int) -> dict[str, float | str]:
        if trials <= 0:
            return {"reliability": 0.0, "grade": "unknown"}
        reliability = successes / trials
        grade = "high" if reliability >= 0.6 else "low"
        return {"reliability": round(reliability, 4), "grade": grade}


class VolatilityAnalyst:
    def analyze(self, observation: TechnicalReasoningObservation) -> dict[str, float | str]:
        ranges = [high - low for high, low in zip(observation.highs, observation.lows)]
        average_range = sum(ranges) / len(ranges)
        return {"volatility": "elevated" if average_range > 2 else "normal", "average_range": round(average_range, 4)}


class RelativeStrengthAnalyst:
    def analyze(self, observation: TechnicalReasoningObservation) -> dict[str, float | str]:
        asset_return = (observation.closes[-1] - observation.closes[0]) / observation.closes[0]
        benchmark_return = (observation.benchmark_closes[-1] - observation.benchmark_closes[0]) / observation.benchmark_closes[0]
        spread = asset_return - benchmark_return
        return {"relative_strength": "outperforming" if spread > 0 else "underperforming", "spread": round(spread, 4)}


class MultiTimeframeAnalyst:
    def analyze(self, observation: TechnicalReasoningObservation) -> dict[str, float | str]:
        score = observation.timeframe_alignment_score
        return {"alignment": "aligned" if score >= 0.6 else "divergent", "score": round(score, 4)}


class TechnicalFusionAnalyst:
    def fuse(self, components: dict[str, dict]) -> dict[str, object]:
        supportive = sum(
            (
                components["trend"].get("trend") == "rising",
                components["momentum"].get("momentum") == "positive",
                components["market_structure"].get("structure") == "higher_high_higher_low",
                components["volume"].get("volume_state") == "expanding",
                components["pattern_reliability"].get("grade") == "high",
                components["volatility"].get("volatility") == "normal",
                components["relative_strength"].get("relative_strength") == "outperforming",
                components["multi_timeframe"].get("alignment") == "aligned",
            )
        )
        contradictory = tuple(
            key
            for key, value in components.items()
            if "falling" in value.values()
            or "negative" in value.values()
            or "mixed_structure" in value.values()
            or "low" in value.values()
            or "underperforming" in value.values()
            or "divergent" in value.values()
        )
        return {
            "technical_conclusion": "technically_confirmed" if supportive >= 5 else "technically_unconfirmed",
            "supportive_factor_count": supportive,
            "contradictory_factors": contradictory,
        }


class TechnicalAnalysisOfficeChief:
    """Office Chief for analyst-side Technical Analysis Office."""

    def __init__(self) -> None:
        self.trend = TrendAnalyst()
        self.momentum = MomentumAnalyst()
        self.market_structure = MarketStructureAnalyst()
        self.volume = VolumeAnalyst()
        self.pattern_reliability = PatternReliabilityAnalyst()
        self.volatility = VolatilityAnalyst()
        self.relative_strength = RelativeStrengthAnalyst()
        self.multi_timeframe = MultiTimeframeAnalyst()
        self.fusion = TechnicalFusionAnalyst()

    def reason(self, observation: TechnicalReasoningObservation) -> dict[str, object]:
        components = {
            "trend": self.trend.analyze(observation),
            "momentum": self.momentum.analyze(observation),
            "market_structure": self.market_structure.analyze(observation),
            "volume": self.volume.analyze(observation),
            "pattern_reliability": self.pattern_reliability.evaluate(
                observation.historical_pattern_successes,
                observation.historical_pattern_trials,
            ),
            "volatility": self.volatility.analyze(observation),
            "relative_strength": self.relative_strength.analyze(observation),
            "multi_timeframe": self.multi_timeframe.analyze(observation),
        }
        components["technical_fusion"] = self.fusion.fuse(components)
        return components

    def argument_graphs(self, reasoning: dict[str, object], source_report_ids: tuple[str, ...]) -> tuple[TechnicalArgumentGraph, ...]:
        contradictory = tuple(reasoning["technical_fusion"]["contradictory_factors"])
        return (
            TechnicalArgumentGraph(
                "TECH-CONCLUSION-001",
                (
                    "claim:technical_reasoning",
                    "evidence:trend",
                    "evidence:momentum",
                    "evidence:pattern_reliability",
                    "evidence:relative_strength",
                    "source:" + ",".join(source_report_ids),
                ),
                (
                    ("evidence:trend", "claim:technical_reasoning", "supports"),
                    ("evidence:momentum", "claim:technical_reasoning", "supports"),
                    ("evidence:pattern_reliability", "claim:technical_reasoning", "qualifies"),
                    ("evidence:relative_strength", "claim:technical_reasoning", "supports"),
                ),
                contradictory,
            ),
        )

    def alternative_explanations(self, reasoning: dict[str, object]) -> tuple[str, ...]:
        contradictory = tuple(reasoning["technical_fusion"]["contradictory_factors"])
        if contradictory:
            return ("Observed pattern may be a temporary countertrend or failed breakout.",)
        return ("Observed pattern may still reflect noise rather than durable structure.",)


class AnalystTechnicalAnalysisOffice:
    """Analyst-side Technical Analysis Office integrated with Analyst Department."""

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
        self.office = self.department.offices[ANALYST_TECHNICAL_OFFICE_ID]
        self.chief = TechnicalAnalysisOfficeChief()

    def generate_technical_aar(
        self,
        observation: TechnicalReasoningObservation,
        source_reports: tuple[OperationalContract, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        reasoning = self.chief.reason(observation)
        source_ids = tuple(report.contract_id for report in source_reports)
        graphs = self.chief.argument_graphs(reasoning, source_ids)
        alternatives = self.chief.alternative_explanations(reasoning)
        created = utc_timestamp()
        payload = {
            "office_id": ANALYST_TECHNICAL_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "technical_analytical_assessment",
            "source_report_ids": list(source_ids),
            "technical_reasoning": reasoning,
            "technical_argument_graphs": [graph.__dict__ for graph in graphs],
            "alternative_technical_explanations": list(alternatives),
            "historical_pattern_reliability": reasoning["pattern_reliability"],
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
            human_summary="Technical Analytical Assessment Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report

    def route_aar(self, aar: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_aar(ANALYST_TECHNICAL_OFFICE_ID, aar, target_inbox)

    def instrument_panel(self) -> AnalystOfficeInstrumentPanel:
        return self.office.instrument_panel()
