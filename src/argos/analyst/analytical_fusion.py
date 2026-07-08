"""Analyst-side Analytical Fusion Office."""

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


ANALYTICAL_FUSION_OFFICE_ID = "ANALYST-OFFICE-009"


@dataclass(frozen=True)
class AnalyticalFusionInput:
    """Immutable analytical artifact supplied to the Fusion Office."""

    office_id: str
    source_report_id: str
    conclusion: str
    decision_model: dict[str, object]
    reasoning_graph: dict[str, object]
    probability_landscape: dict[str, object]
    evidence_ids: tuple[str, ...]
    uncertainty_ids: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class UnifiedDecisionModel:
    """Unified Decision Model preserving source traceability."""

    model_id: str
    primary_conclusion: str
    source_models: tuple[dict[str, object], ...]
    disagreement_preserved: bool


@dataclass(frozen=True)
class OrganizationalReasoningGraph:
    """Organizational Reasoning Graph integrated from Analyst reasoning graphs."""

    graph_id: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str, str], ...]
    source_report_ids: tuple[str, ...]


@dataclass(frozen=True)
class AnalyticalFusionReport:
    """Analytical Fusion Report summarizing integrated analytical work."""

    report_id: str
    unified_decision_model_id: str
    organizational_reasoning_graph_id: str
    independent_evidence_score: float
    intellectual_diversity_score: float
    organizational_confidence: float
    conflict_state: str


class DecisionModelIntegrator:
    def integrate(self, inputs: tuple[AnalyticalFusionInput, ...]) -> UnifiedDecisionModel:
        conclusion_counts: dict[str, int] = {}
        for item in inputs:
            conclusion_counts[item.conclusion] = conclusion_counts.get(item.conclusion, 0) + 1
        primary = sorted(conclusion_counts, key=lambda conclusion: (-conclusion_counts[conclusion], conclusion))[0]
        source_models = tuple(
            {
                "office_id": item.office_id,
                "source_report_id": item.source_report_id,
                "conclusion": item.conclusion,
                "decision_model": item.decision_model,
            }
            for item in inputs
        )
        return UnifiedDecisionModel("UDM-001", primary, source_models, len(conclusion_counts) > 1)


class ReasoningGraphIntegrator:
    def integrate(self, inputs: tuple[AnalyticalFusionInput, ...]) -> OrganizationalReasoningGraph:
        nodes: list[str] = ["claim:unified_decision_model"]
        edges: list[tuple[str, str, str]] = []
        for item in inputs:
            source_node = f"source:{item.source_report_id}"
            office_node = f"office:{item.office_id}"
            nodes.extend((source_node, office_node))
            for node in item.reasoning_graph.get("nodes", ()):
                nodes.append(f"{item.source_report_id}:{node}")
            edges.append((source_node, "claim:unified_decision_model", "contributes"))
            edges.append((office_node, source_node, "produced"))
        return OrganizationalReasoningGraph("ORG-001", tuple(dict.fromkeys(nodes)), tuple(edges), tuple(item.source_report_id for item in inputs))


class ProbabilityLandscapeIntegrator:
    def integrate(self, inputs: tuple[AnalyticalFusionInput, ...]) -> dict[str, object]:
        scenario_scores: dict[str, list[float]] = {}
        for item in inputs:
            for scenario in item.probability_landscape.get("scenarios", ()):
                scenario_scores.setdefault(str(scenario["scenario"]), []).append(float(scenario["probability"]))
        scenarios = tuple(
            {"scenario": name, "mean_probability": round(sum(values) / len(values), 4), "source_count": len(values)}
            for name, values in sorted(scenario_scores.items())
        )
        return {"landscape_id": "AFL-001", "scenarios": scenarios}


class AnalyticalConsensusEngine:
    def consensus(self, inputs: tuple[AnalyticalFusionInput, ...]) -> dict[str, object]:
        counts: dict[str, int] = {}
        for item in inputs:
            counts[item.conclusion] = counts.get(item.conclusion, 0) + 1
        conclusion = sorted(counts, key=lambda key: (-counts[key], key))[0]
        return {
            "consensus_conclusion": conclusion,
            "supporting_offices": tuple(item.office_id for item in inputs if item.conclusion == conclusion),
            "agreement_score": round(counts[conclusion] / len(inputs), 4),
        }


class AnalyticalConflictEngine:
    def conflicts(self, inputs: tuple[AnalyticalFusionInput, ...], consensus_conclusion: str) -> dict[str, object]:
        conflicts = tuple(
            {"office_id": item.office_id, "source_report_id": item.source_report_id, "conclusion": item.conclusion}
            for item in inputs
            if item.conclusion != consensus_conclusion
        )
        return {"conflict_state": "conflict_present" if conflicts else "no_conflict", "conflicts": conflicts}


class OrganizationalReasoningEngine:
    def independent_evidence_score(self, inputs: tuple[AnalyticalFusionInput, ...]) -> float:
        unique_evidence = set().union(*(set(item.evidence_ids) for item in inputs))
        total_evidence = sum(len(item.evidence_ids) for item in inputs)
        if total_evidence == 0:
            return 0.0
        return round(len(unique_evidence) / total_evidence, 4)

    def intellectual_diversity_score(self, inputs: tuple[AnalyticalFusionInput, ...]) -> float:
        unique_offices = {item.office_id for item in inputs}
        unique_conclusions = {item.conclusion for item in inputs}
        if not inputs:
            return 0.0
        return round((len(unique_offices) + len(unique_conclusions)) / (len(inputs) * 2), 4)


class AnalystConfidenceEngine:
    def organizational_confidence(self, inputs: tuple[AnalyticalFusionInput, ...], conflict_count: int, uncertainty_count: int) -> float:
        if not inputs:
            return 0.0
        base = sum(item.confidence for item in inputs) / len(inputs)
        penalty = conflict_count * 0.04 + uncertainty_count * 0.01
        return round(max(0.0, base - penalty), 4)


class FusionHistorianLiaison:
    def historian_packet(self, report_id: str, source_report_ids: tuple[str, ...]) -> dict[str, object]:
        return {"historian_liaison_id": "FHL-001", "report_id": report_id, "source_report_ids": source_report_ids}


class AnalyticalFusionOfficeChief:
    """Office Chief for deterministic analytical fusion."""

    def __init__(self) -> None:
        self.decision_model_integrator = DecisionModelIntegrator()
        self.reasoning_graph_integrator = ReasoningGraphIntegrator()
        self.probability_landscape_integrator = ProbabilityLandscapeIntegrator()
        self.consensus_engine = AnalyticalConsensusEngine()
        self.conflict_engine = AnalyticalConflictEngine()
        self.organizational_reasoning_engine = OrganizationalReasoningEngine()
        self.analyst_confidence_engine = AnalystConfidenceEngine()
        self.fusion_historian_liaison = FusionHistorianLiaison()

    def analyze(self, inputs: tuple[AnalyticalFusionInput, ...]) -> dict[str, object]:
        if not inputs:
            raise ValueError("analytical fusion requires at least one analytical input")
        udm = self.decision_model_integrator.integrate(inputs)
        org = self.reasoning_graph_integrator.integrate(inputs)
        landscape = self.probability_landscape_integrator.integrate(inputs)
        consensus = self.consensus_engine.consensus(inputs)
        conflicts = self.conflict_engine.conflicts(inputs, str(consensus["consensus_conclusion"]))
        uncertainty_count = len(set().union(*(set(item.uncertainty_ids) for item in inputs)))
        independent_evidence_score = self.organizational_reasoning_engine.independent_evidence_score(inputs)
        intellectual_diversity_score = self.organizational_reasoning_engine.intellectual_diversity_score(inputs)
        organizational_confidence = self.analyst_confidence_engine.organizational_confidence(inputs, len(conflicts["conflicts"]), uncertainty_count)
        afr = AnalyticalFusionReport(
            "AFR-001",
            udm.model_id,
            org.graph_id,
            independent_evidence_score,
            intellectual_diversity_score,
            organizational_confidence,
            str(conflicts["conflict_state"]),
        )
        return {
            "unified_decision_model": udm.__dict__,
            "organizational_reasoning_graph": org.__dict__,
            "integrated_probability_landscape": landscape,
            "consensus": consensus,
            "conflicts": conflicts,
            "independent_evidence_score": independent_evidence_score,
            "intellectual_diversity_score": intellectual_diversity_score,
            "organizational_confidence": organizational_confidence,
            "analytical_fusion_report": afr.__dict__,
            "historian_liaison": self.fusion_historian_liaison.historian_packet(afr.report_id, org.source_report_ids),
        }


class AnalyticalFusionOffice:
    """Analyst-side Analytical Fusion Office integrated with Analyst Department."""

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
        self.office = self.department.offices[ANALYTICAL_FUSION_OFFICE_ID]
        self.chief = AnalyticalFusionOfficeChief()

    def generate_analytical_fusion_aar(
        self,
        inputs: tuple[AnalyticalFusionInput, ...],
        source_reports: tuple[OperationalContract, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        reasoning = self.chief.analyze(inputs)
        source_ids = tuple(report.contract_id for report in source_reports)
        created = utc_timestamp()
        payload = {
            "office_id": ANALYTICAL_FUSION_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "analytical_fusion_assessment",
            "source_report_ids": list(source_ids),
            "analytical_fusion_reasoning": reasoning,
            "unified_decision_model": reasoning["unified_decision_model"],
            "organizational_reasoning_graph": reasoning["organizational_reasoning_graph"],
            "analytical_fusion_report": reasoning["analytical_fusion_report"],
            "independent_evidence_score": reasoning["independent_evidence_score"],
            "intellectual_diversity_score": reasoning["intellectual_diversity_score"],
            "organizational_confidence": reasoning["organizational_confidence"],
            "new_analysis_created": False,
            "analyst_conclusions_modified": False,
            "disagreement_suppressed": False,
            "uncertainty_discarded": False,
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
            human_summary="Analytical Fusion Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report

    def route_aar(self, aar: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_aar(ANALYTICAL_FUSION_OFFICE_ID, aar, target_inbox)

    def instrument_panel(self) -> AnalystOfficeInstrumentPanel:
        return self.office.instrument_panel()
