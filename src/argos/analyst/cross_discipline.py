"""Analyst-side Cross-Discipline Review Office."""

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


CROSS_DISCIPLINE_REVIEW_OFFICE_ID = "ANALYST-OFFICE-008"


@dataclass(frozen=True)
class DisciplineAssessment:
    """Input assessment for deterministic cross-discipline review."""

    discipline: str
    source_report_id: str
    conclusion: str
    evidence_ids: tuple[str, ...]
    reasoning_claims: tuple[str, ...]
    unknowns: tuple[str, ...]
    assumptions: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class CrossDisciplineReviewReport:
    """Peer-review report across Analyst disciplines."""

    report_id: str
    reviewed_disciplines: tuple[str, ...]
    agreement_score: float
    conflict_score: float
    evidence_comparison_score: float
    reasoning_comparison_score: float
    unknown_comparison_score: float


@dataclass(frozen=True)
class ConsensusReport:
    """Deterministic consensus report that does not force unanimity."""

    report_id: str
    consensus_conclusion: str
    supporting_disciplines: tuple[str, ...]
    consensus_state: str


@dataclass(frozen=True)
class DisagreementReport:
    """Explicit disagreement report."""

    report_id: str
    disagreement_groups: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class AnalyticalConflictReport:
    """Analytical conflict report preserving conflicting assumptions."""

    report_id: str
    conflicting_conclusions: tuple[str, ...]
    conflicting_assumptions: tuple[str, ...]
    conflict_state: str


class DisciplineReviewer:
    """Base deterministic discipline reviewer."""

    discipline_name = ""

    def review(self, assessment: DisciplineAssessment) -> dict[str, float | str | tuple[str, ...]]:
        if assessment.discipline != self.discipline_name:
            raise ValueError(f"expected {self.discipline_name} assessment, received {assessment.discipline}")
        return {
            "discipline": assessment.discipline,
            "source_report_id": assessment.source_report_id,
            "conclusion": assessment.conclusion,
            "evidence_count": len(assessment.evidence_ids),
            "reasoning_claim_count": len(assessment.reasoning_claims),
            "unknown_count": len(assessment.unknowns),
            "confidence": round(assessment.confidence, 4),
        }


class StatisticalReviewer(DisciplineReviewer):
    discipline_name = "statistical"


class TechnicalReviewer(DisciplineReviewer):
    discipline_name = "technical"


class FundamentalReviewer(DisciplineReviewer):
    discipline_name = "fundamental"


class MacroeconomicReviewer(DisciplineReviewer):
    discipline_name = "macroeconomic"


class DerivativesReviewer(DisciplineReviewer):
    discipline_name = "derivatives"


class BehavioralReviewer(DisciplineReviewer):
    discipline_name = "behavioral"


class RiskInteractionReviewer(DisciplineReviewer):
    discipline_name = "risk_interaction"


class ConsensusAnalyst:
    """Deterministically computes consensus without suppressing disagreement."""

    def consensus(self, assessments: tuple[DisciplineAssessment, ...]) -> ConsensusReport:
        counts: dict[str, int] = {}
        for assessment in assessments:
            counts[assessment.conclusion] = counts.get(assessment.conclusion, 0) + 1
        consensus_conclusion = sorted(counts, key=lambda conclusion: (-counts[conclusion], conclusion))[0]
        supporting = tuple(assessment.discipline for assessment in assessments if assessment.conclusion == consensus_conclusion)
        state = "consensus_with_disagreement" if len(supporting) < len(assessments) else "unanimous_consensus"
        return ConsensusReport("CR-001", consensus_conclusion, supporting, state)


class CrossDisciplineReviewOfficeChief:
    """Office Chief for deterministic cross-discipline peer review."""

    def __init__(self) -> None:
        self.reviewers = {
            "statistical": StatisticalReviewer(),
            "technical": TechnicalReviewer(),
            "fundamental": FundamentalReviewer(),
            "macroeconomic": MacroeconomicReviewer(),
            "derivatives": DerivativesReviewer(),
            "behavioral": BehavioralReviewer(),
            "risk_interaction": RiskInteractionReviewer(),
        }
        self.consensus_analyst = ConsensusAnalyst()

    def analyze(self, assessments: tuple[DisciplineAssessment, ...]) -> dict[str, object]:
        if not assessments:
            raise ValueError("cross-discipline review requires at least one assessment")
        reviewer_results = tuple(self.reviewers[assessment.discipline].review(assessment) for assessment in assessments)
        review_report = self.cross_discipline_review_report(assessments)
        consensus_report = self.consensus_analyst.consensus(assessments)
        disagreement_report = self.disagreement_report(assessments, consensus_report.consensus_conclusion)
        conflict_report = self.conflict_report(assessments, disagreement_report)
        return {
            "reviewer_results": reviewer_results,
            "cross_discipline_review_report": review_report.__dict__,
            "consensus_report": consensus_report.__dict__,
            "disagreement_report": disagreement_report.__dict__,
            "analytical_conflict_report": conflict_report.__dict__,
        }

    def cross_discipline_review_report(self, assessments: tuple[DisciplineAssessment, ...]) -> CrossDisciplineReviewReport:
        conclusions = tuple(assessment.conclusion for assessment in assessments)
        conclusion_counts = {conclusion: conclusions.count(conclusion) for conclusion in set(conclusions)}
        max_count = max(conclusion_counts.values())
        agreement_score = round(max_count / len(assessments), 4)
        conflict_score = round((len(conclusion_counts) - 1) / len(assessments), 4)
        return CrossDisciplineReviewReport(
            "CDRR-001",
            tuple(assessment.discipline for assessment in assessments),
            agreement_score,
            conflict_score,
            self._comparison_score(tuple(assessment.evidence_ids for assessment in assessments)),
            self._comparison_score(tuple(assessment.reasoning_claims for assessment in assessments)),
            self._comparison_score(tuple(assessment.unknowns for assessment in assessments)),
        )

    def disagreement_report(self, assessments: tuple[DisciplineAssessment, ...], consensus_conclusion: str) -> DisagreementReport:
        groups = []
        for conclusion in sorted({assessment.conclusion for assessment in assessments if assessment.conclusion != consensus_conclusion}):
            groups.append(
                {
                    "conclusion": conclusion,
                    "disciplines": tuple(assessment.discipline for assessment in assessments if assessment.conclusion == conclusion),
                }
            )
        return DisagreementReport("DR-001", tuple(groups))

    def conflict_report(self, assessments: tuple[DisciplineAssessment, ...], disagreement_report: DisagreementReport) -> AnalyticalConflictReport:
        conflicting_conclusions = tuple(group["conclusion"] for group in disagreement_report.disagreement_groups)
        assumption_counts: dict[str, int] = {}
        for assessment in assessments:
            for assumption in assessment.assumptions:
                assumption_counts[assumption] = assumption_counts.get(assumption, 0) + 1
        conflicting_assumptions = tuple(sorted(assumption for assumption, count in assumption_counts.items() if count == 1))
        state = "analytical_conflict_present" if conflicting_conclusions else "no_analytical_conflict"
        return AnalyticalConflictReport("ACR-001", conflicting_conclusions, conflicting_assumptions, state)

    def reasoning_graphs(self, reasoning: dict[str, object], source_report_ids: tuple[str, ...]) -> tuple[dict[str, object], ...]:
        return (
            {
                "conclusion_id": "CROSS-DISCIPLINE-CONCLUSION-001",
                "nodes": (
                    "claim:cross_discipline_consensus",
                    "evidence:discipline_reviews",
                    "evidence:evidence_comparison",
                    "evidence:reasoning_comparison",
                    "evidence:unknown_comparison",
                    "source:" + ",".join(source_report_ids),
                ),
                "edges": (
                    ("evidence:discipline_reviews", "claim:cross_discipline_consensus", "supports"),
                    ("evidence:evidence_comparison", "claim:cross_discipline_consensus", "qualifies"),
                    ("evidence:reasoning_comparison", "claim:cross_discipline_consensus", "qualifies"),
                    ("evidence:unknown_comparison", "claim:cross_discipline_consensus", "challenges"),
                ),
            },
        )

    def _comparison_score(self, item_groups: tuple[tuple[str, ...], ...]) -> float:
        union = set().union(*(set(group) for group in item_groups))
        if not union:
            return 1.0
        intersection = set(item_groups[0])
        for group in item_groups[1:]:
            intersection &= set(group)
        return round(len(intersection) / len(union), 4)


class CrossDisciplineReviewOffice:
    """Analyst-side Cross-Discipline Review Office integrated with Analyst Department."""

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
        self.office = self.department.offices[CROSS_DISCIPLINE_REVIEW_OFFICE_ID]
        self.chief = CrossDisciplineReviewOfficeChief()

    def generate_cross_discipline_aar(
        self,
        assessments: tuple[DisciplineAssessment, ...],
        source_reports: tuple[OperationalContract, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        reasoning = self.chief.analyze(assessments)
        source_ids = tuple(report.contract_id for report in source_reports)
        graphs = self.chief.reasoning_graphs(reasoning, source_ids)
        created = utc_timestamp()
        payload = {
            "office_id": CROSS_DISCIPLINE_REVIEW_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "cross_discipline_review_analytical_assessment",
            "source_report_ids": list(source_ids),
            "cross_discipline_reasoning": reasoning,
            "cross_discipline_reasoning_graphs": list(graphs),
            "cross_discipline_review_report": reasoning["cross_discipline_review_report"],
            "consensus_report": reasoning["consensus_report"],
            "disagreement_report": reasoning["disagreement_report"],
            "analytical_conflict_report": reasoning["analytical_conflict_report"],
            "analyses_modified": False,
            "disagreement_suppressed": False,
            "forced_consensus": False,
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
            human_summary="Cross-Discipline Review Analytical Assessment Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report

    def route_aar(self, aar: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_aar(CROSS_DISCIPLINE_REVIEW_OFFICE_ID, aar, target_inbox)

    def instrument_panel(self) -> AnalystOfficeInstrumentPanel:
        return self.office.instrument_panel()
