"""Analyst Department office framework and AAR generation."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json

from argos.foundation.communication import IncomingMailbox, OutgoingMailbox
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService


ANALYST_GROUP_ID = "DEP-004"


@dataclass(frozen=True)
class AnalystOfficeConfiguration:
    """Analyst office configuration."""

    office_id: str
    name: str
    staff_id: str
    enabled: bool = True


@dataclass(frozen=True)
class AnalystOfficeRecord:
    """Registered Analyst office record."""

    configuration: AnalystOfficeConfiguration
    inbox: IncomingMailbox
    outbox: OutgoingMailbox


class AnalystOfficeRegistry:
    """Deterministic Analyst office registry."""

    def __init__(self) -> None:
        self._offices: dict[str, AnalystOfficeRecord] = {}

    def register(self, configuration: AnalystOfficeConfiguration) -> AnalystOfficeRecord:
        if configuration.office_id in self._offices:
            raise ValueError(f"analyst office already registered: {configuration.office_id}")
        record = AnalystOfficeRecord(
            configuration,
            IncomingMailbox(configuration.staff_id, ANALYST_GROUP_ID),
            OutgoingMailbox(configuration.staff_id, ANALYST_GROUP_ID),
        )
        self._offices[configuration.office_id] = record
        return record

    def get(self, office_id: str) -> AnalystOfficeRecord | None:
        return self._offices.get(office_id)

    def all(self) -> tuple[AnalystOfficeRecord, ...]:
        return tuple(self._offices[key] for key in sorted(self._offices))


class AnalystOfficeQueue:
    """Analyst office work queue."""

    def __init__(self) -> None:
        self._items: list[str] = []

    def enqueue(self, item_id: str) -> None:
        self._items.append(item_id)

    def dequeue(self) -> str:
        if not self._items:
            raise IndexError("analyst office queue is empty")
        return self._items.pop(0)

    def __len__(self) -> int:
        return len(self._items)


@dataclass(frozen=True)
class AnalystOfficeMetrics:
    """Analyst office metrics."""

    queue_depth: int
    reports_generated: int
    routed_reports: int


@dataclass(frozen=True)
class AnalystOfficeHealth:
    """Analyst office health."""

    status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class AnalystOfficeInstrumentPanel:
    """Traceable Analyst office instrument panel."""

    office_id: str
    metrics: AnalystOfficeMetrics
    health: AnalystOfficeHealth
    source: str


@dataclass(frozen=True)
class AnalyticalHypothesis:
    """Deterministic analytical hypothesis."""

    hypothesis_id: str
    statement: str
    source_report_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceEvaluation:
    """Objective evidence evaluation."""

    evaluation_id: str
    source_report_id: str
    evidence_class: str
    weight: float


@dataclass(frozen=True)
class AlternativeExplanation:
    """Alternative explanation for observed evidence."""

    explanation_id: str
    statement: str
    source_report_ids: tuple[str, ...]


@dataclass
class AnalystOffice:
    """Analyst reasoning office scaffold."""

    record: AnalystOfficeRecord
    queue: AnalystOfficeQueue = field(default_factory=AnalystOfficeQueue)
    reports_generated: int = 0
    routed_reports: int = 0

    def metrics(self) -> AnalystOfficeMetrics:
        return AnalystOfficeMetrics(len(self.queue), self.reports_generated, self.routed_reports)

    def health(self) -> AnalystOfficeHealth:
        reasons = []
        if not self.record.configuration.enabled:
            reasons.append("office_disabled")
        if len(self.queue) > 10:
            reasons.append("queue_depth_high")
        return AnalystOfficeHealth("healthy" if not reasons else "attention", tuple(reasons))

    def instrument_panel(self) -> AnalystOfficeInstrumentPanel:
        return AnalystOfficeInstrumentPanel(
            self.record.configuration.office_id,
            self.metrics(),
            self.health(),
            f"office:{self.record.configuration.office_id}",
        )


class HypothesisFramework:
    """Generate deterministic hypotheses from existing evidence."""

    def generate(
        self,
        office: AnalystOffice,
        source_reports: tuple[OperationalContract, ...],
    ) -> tuple[AnalyticalHypothesis, ...]:
        source_ids = tuple(report.contract_id for report in source_reports)
        office_name = office.record.configuration.name
        return (
            AnalyticalHypothesis(
                f"HYP-{office.record.configuration.office_id}-001",
                f"{office_name} hypothesis derived from {len(source_reports)} source reports.",
                source_ids,
            ),
        )


class EvidenceEvaluationFramework:
    """Evaluate evidence classes objectively without modifying sources."""

    def evaluate(self, source_reports: tuple[OperationalContract, ...]) -> tuple[EvidenceEvaluation, ...]:
        evaluations = []
        for index, report in enumerate(sorted(source_reports, key=lambda item: item.contract_id), start=1):
            evidence_class = _evidence_class(report)
            weight = _evidence_weight(report.contract_type)
            evaluations.append(EvidenceEvaluation(f"EVAL-{index:03d}", report.contract_id, evidence_class, weight))
        return tuple(evaluations)


class AlternativeExplanationFramework:
    """Generate deterministic alternative explanations."""

    def generate(self, source_reports: tuple[OperationalContract, ...]) -> tuple[AlternativeExplanation, ...]:
        source_ids = tuple(report.contract_id for report in source_reports)
        threat_count = sum(1 for report in source_reports if _evidence_class(report) == "threat_evidence")
        statement = (
            "Observed evidence may reflect transient stress rather than durable impairment."
            if threat_count
            else "Observed evidence may reflect temporary noise rather than persistent opportunity."
        )
        return (AlternativeExplanation("ALT-001", statement, source_ids),)


class AnalyticalAssessmentReportGenerator:
    """Generate Analytical Assessment Reports without discovery or trade authority."""

    def __init__(self) -> None:
        self.hypothesis_framework = HypothesisFramework()
        self.evidence_framework = EvidenceEvaluationFramework()
        self.alternative_framework = AlternativeExplanationFramework()

    def generate(
        self,
        office: AnalystOffice,
        source_reports: tuple[OperationalContract, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_repository: PromptRepository,
        prompt_id: str,
        persistence_repository: InMemoryPersistenceRepository,
    ) -> OperationalContract:
        snapshot = PromptSnapshotService(prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        hypotheses = self.hypothesis_framework.generate(office, source_reports)
        evaluations = self.evidence_framework.evaluate(source_reports)
        alternatives = self.alternative_framework.generate(source_reports)
        created = utc_timestamp()
        payload = {
            "office_id": office.record.configuration.office_id,
            "office_name": office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "analytical_assessment",
            "source_report_ids": [report.contract_id for report in source_reports],
            "hypotheses": [hypothesis.__dict__ for hypothesis in hypotheses],
            "evidence_evaluations": [evaluation.__dict__ for evaluation in evaluations],
            "alternative_explanations": [alternative.__dict__ for alternative in alternatives],
            "seeker_reports_modified": False,
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
            parent_contract_ids=tuple(report.contract_id for report in source_reports),
            produced_by_staff_id=office.record.configuration.staff_id,
            produced_by_group_id=ANALYST_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary=f"Analytical Assessment Report from {office.record.configuration.name}.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=tuple(report.contract_id for report in source_reports),
        )
        persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        office.reports_generated += 1
        return report


def analyst_office_templates() -> tuple[AnalystOfficeConfiguration, ...]:
    """Return EO-029 Analyst office templates."""
    names = (
        "Statistical Analysis Office",
        "Technical Analysis Office",
        "Fundamental Analysis Office",
        "Macroeconomic Analysis Office",
        "Derivatives Analysis Office",
        "Behavioral Analysis Office",
        "Risk Interaction Office",
        "Cross-Discipline Review Office",
        "Analytical Fusion Office",
    )
    return tuple(
        AnalystOfficeConfiguration(f"ANALYST-OFFICE-{index:03d}", name, f"STF-{30 + index:03d}")
        for index, name in enumerate(names, start=1)
    )


def _evidence_class(report: OperationalContract) -> str:
    if report.contract_type == "COR":
        return "opportunity_evidence"
    if report.contract_type == "IGR":
        return "information_gap_evidence"
    if report.contract_type in {"MIR", "ICR"}:
        return "fusion_evidence"
    if report.contract_type.endswith("TR") or report.contract_type in {"STR", "CTR", "ETR", "ATR", "OTR"}:
        return "threat_evidence"
    return "operational_evidence"


def _evidence_weight(contract_type: str) -> float:
    weights = {
        "MIR": 0.9,
        "ICR": 0.85,
        "COR": 0.7,
        "IGR": 0.4,
    }
    if contract_type.endswith("TR") or contract_type in {"STR", "CTR", "ETR", "ATR", "OTR"}:
        return 0.75
    return weights.get(contract_type, 0.6)
