"""Multi-Office Intelligence Fusion Office."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from argos.foundation.audit import AuditService
from argos.foundation.communication import CourierService, IncomingMailbox, OutgoingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService

from .offices import OfficeConfiguration, OfficeHealth, OfficeInstrumentPanel, OfficeMetrics, SEEKER_GROUP_ID


FUSION_OFFICE_ID = "SEEKER-OFFICE-009"
FUSION_STAFF_ID = "STF-029"


@dataclass(frozen=True)
class FusionFinding:
    """Normalized signal extracted from an immutable Seeker report."""

    source_report_id: str
    source_contract_type: str
    source_office_id: str
    seeker: str
    signal: str
    report_hint: str
    evidence_class: str


@dataclass(frozen=True)
class FusionConflict:
    """Conflict preserved between independent findings."""

    seeker: str
    opportunity_report_ids: tuple[str, ...]
    threat_report_ids: tuple[str, ...]


@dataclass(frozen=True)
class FusionAssessment:
    """Deterministic fusion output before report serialization."""

    findings: tuple[FusionFinding, ...]
    conflicts: tuple[FusionConflict, ...]
    corroborated_seekers: tuple[str, ...]
    evidence_classes: tuple[str, ...]
    evidence_diversity: int
    agreement_score: float
    confidence: float
    priority_order: tuple[str, ...]


class EvidenceClassificationEngine:
    """Classify source reports without modifying them."""

    def classify_report(self, report: OperationalContract) -> str:
        mapping = {
            "COR": "opportunity_evidence",
            "MIR": "fusion_evidence",
            "CFR": "conflict_evidence",
            "ICR": "corroboration_evidence",
            "IGR": "information_gap_evidence",
        }
        if report.contract_type in mapping:
            return mapping[report.contract_type]
        if report.contract_type.endswith("TR") or report.contract_type in {"STR", "CTR", "ETR", "ATR", "OTR"}:
            return "threat_evidence"
        if report.contract_type in {"IAR", "CXR", "EAR", "AIR", "MTR"}:
            return "specialized_intelligence_evidence"
        return "operational_evidence"


class CorroborationEngine:
    """Measure independent agreement between offices."""

    def corroborated_seekers(self, findings: tuple[FusionFinding, ...]) -> tuple[str, ...]:
        by_seeker: dict[str, set[str]] = {}
        for finding in findings:
            by_seeker.setdefault(finding.seeker, set()).add(finding.source_office_id)
        return tuple(sorted(seeker for seeker, offices in by_seeker.items() if len(offices) >= 2))

    def agreement_score(self, findings: tuple[FusionFinding, ...], conflicts: tuple[FusionConflict, ...]) -> float:
        if not findings:
            return 0.0
        corroborated = len(self.corroborated_seekers(findings))
        unique_seekers = len({finding.seeker for finding in findings})
        raw = corroborated / unique_seekers if unique_seekers else 0.0
        penalty = min(0.5, len(conflicts) * 0.1)
        return round(max(0.0, raw - penalty), 4)


class ConflictDetectionEngine:
    """Detect and preserve conflicting evidence."""

    def conflicts(self, findings: tuple[FusionFinding, ...]) -> tuple[FusionConflict, ...]:
        by_seeker: dict[str, dict[str, set[str]]] = {}
        for finding in findings:
            bucket = by_seeker.setdefault(finding.seeker, {"opportunity": set(), "threat": set()})
            if finding.report_hint == "opportunity":
                bucket["opportunity"].add(finding.source_report_id)
            if finding.report_hint == "threat":
                bucket["threat"].add(finding.source_report_id)
        conflicts = []
        for seeker in sorted(by_seeker):
            opportunity_ids = tuple(sorted(by_seeker[seeker]["opportunity"]))
            threat_ids = tuple(sorted(by_seeker[seeker]["threat"]))
            if opportunity_ids and threat_ids:
                conflicts.append(FusionConflict(seeker, opportunity_ids, threat_ids))
        return tuple(conflicts)


class ConfidenceAggregator:
    """Calculate deterministic confidence without averaging source scores."""

    def calculate(
        self,
        office_diversity: int,
        evidence_diversity: int,
        corroborated_count: int,
        conflict_count: int,
    ) -> float:
        confidence = 0.35
        confidence += min(0.25, office_diversity * 0.05)
        confidence += min(0.2, evidence_diversity * 0.04)
        confidence += min(0.2, corroborated_count * 0.05)
        confidence -= min(0.3, conflict_count * 0.1)
        return round(max(0.0, min(0.95, confidence)), 4)


class IntelligencePrioritizer:
    """Prioritize preserved intelligence findings."""

    def prioritize(self, findings: tuple[FusionFinding, ...]) -> tuple[str, ...]:
        priority = {"threat": 0, "opportunity": 1, "specialized_intelligence": 2, "information_gap": 3}
        sorted_findings = sorted(
            findings,
            key=lambda item: (
                priority.get(item.report_hint, 4),
                item.seeker,
                item.source_report_id,
            ),
        )
        return tuple(f"{finding.seeker}:{finding.signal}:{finding.source_report_id}" for finding in sorted_findings)


class MultiOfficeIntelligenceReportGenerator:
    """Generate Fusion Office reports from deterministic assessments."""

    def generate(
        self,
        office: "FusionOffice",
        contract_type: str,
        report_status: str,
        human_summary: str,
        assessment: FusionAssessment,
        source_reports: tuple[OperationalContract, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        snapshot = PromptSnapshotService(office.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        created = utc_timestamp()
        payload = {
            "office_id": FUSION_OFFICE_ID,
            "office_name": office.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "report_status": report_status,
            "findings": [finding.__dict__ for finding in assessment.findings],
            "conflicts": [conflict.__dict__ for conflict in assessment.conflicts],
            "corroborated_seekers": list(assessment.corroborated_seekers),
            "evidence_classes": list(assessment.evidence_classes),
            "evidence_diversity": assessment.evidence_diversity,
            "agreement_score": assessment.agreement_score,
            "confidence": assessment.confidence,
            "priority_order": list(assessment.priority_order),
            "source_report_ids": [report.contract_id for report in source_reports],
            "source_reports_modified": False,
        }
        signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        report = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type=contract_type,
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            parent_contract_ids=tuple(report.contract_id for report in source_reports),
            produced_by_staff_id=FUSION_STAFF_ID,
            produced_by_group_id=SEEKER_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary=human_summary,
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=tuple(report.contract_id for report in source_reports),
        )
        office.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        office.reports_generated += 1
        return report


class FusionOfficeChief:
    """Office Chief for deterministic multi-office fusion."""

    def __init__(self) -> None:
        self.evidence_classifier = EvidenceClassificationEngine()
        self.corroboration_engine = CorroborationEngine()
        self.conflict_engine = ConflictDetectionEngine()
        self.confidence_aggregator = ConfidenceAggregator()
        self.prioritizer = IntelligencePrioritizer()

    def assess(self, source_reports: tuple[OperationalContract, ...]) -> FusionAssessment:
        findings = self._extract_findings(source_reports)
        conflicts = self.conflict_engine.conflicts(findings)
        corroborated = self.corroboration_engine.corroborated_seekers(findings)
        evidence_classes = tuple(sorted({finding.evidence_class for finding in findings}))
        office_diversity = len({finding.source_office_id for finding in findings})
        agreement_score = self.corroboration_engine.agreement_score(findings, conflicts)
        confidence = self.confidence_aggregator.calculate(
            office_diversity,
            len(evidence_classes),
            len(corroborated),
            len(conflicts),
        )
        priority_order = self.prioritizer.prioritize(findings)
        return FusionAssessment(
            findings,
            conflicts,
            corroborated,
            evidence_classes,
            len(evidence_classes),
            agreement_score,
            confidence,
            priority_order,
        )

    def _extract_findings(self, reports: tuple[OperationalContract, ...]) -> tuple[FusionFinding, ...]:
        findings: list[FusionFinding] = []
        for report in sorted(reports, key=lambda item: item.contract_id):
            evidence_class = self.evidence_classifier.classify_report(report)
            source_office_id = str(report.machine_payload.get("office_id", "UNKNOWN"))
            for signal in _payload_signals(report.machine_payload):
                findings.append(
                    FusionFinding(
                        source_report_id=report.contract_id,
                        source_contract_type=report.contract_type,
                        source_office_id=source_office_id,
                        seeker=str(signal.get("seeker", "unknown")),
                        signal=str(signal.get("signal", "unknown")),
                        report_hint=str(signal.get("report_hint", "unknown")),
                        evidence_class=evidence_class,
                    )
                )
        return tuple(findings)


class FusionOffice:
    """Multi-Office Intelligence Fusion Office."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.prompt_repository = prompt_repository
        self.configuration = OfficeConfiguration(FUSION_OFFICE_ID, "Multi-Office Intelligence Fusion Office", FUSION_STAFF_ID)
        self.outbox = OutgoingMailbox(FUSION_STAFF_ID, SEEKER_GROUP_ID)
        self.chief = FusionOfficeChief()
        self.generator = MultiOfficeIntelligenceReportGenerator()
        self.reports_generated = 0
        self.routed_reports = 0
        self.last_assessment: FusionAssessment | None = None

    def fuse(self, source_reports: tuple[OperationalContract, ...]) -> FusionAssessment:
        self.configuration_service.validate_startup()
        self.last_assessment = self.chief.assess(tuple(source_reports))
        return self.last_assessment

    def generate_mir(self, source_reports: tuple[OperationalContract, ...], case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        assessment = self.fuse(source_reports)
        return self.generator.generate(self, "MIR", "multi_office_intelligence_fused", "Multi-Office Intelligence Report.", assessment, source_reports, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_conflict_report(self, source_reports: tuple[OperationalContract, ...], case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        assessment = self.fuse(source_reports)
        return self.generator.generate(self, "CFR", "conflicts_preserved", "Conflict Report.", assessment, source_reports, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def generate_corroboration_report(self, source_reports: tuple[OperationalContract, ...], case_file_id: str, trade_cycle_id: str, document_sequence: int, prompt_id: str) -> OperationalContract:
        assessment = self.fuse(source_reports)
        return self.generator.generate(self, "ICR", "corroboration_identified", "Intelligence Corroboration Report.", assessment, source_reports, case_file_id, trade_cycle_id, document_sequence, prompt_id)

    def route_report(self, report: OperationalContract, target_inbox: IncomingMailbox):
        result = CourierService(self.audit_service).deliver(self.outbox, target_inbox, report)
        if result.delivered:
            self.routed_reports += 1
        return result

    def instrument_panel(self) -> OfficeInstrumentPanel:
        reasons = []
        if self.last_assessment and self.last_assessment.conflicts:
            reasons.append("conflicts_present")
        health = OfficeHealth("healthy" if not reasons else "attention", tuple(reasons))
        return OfficeInstrumentPanel(
            FUSION_OFFICE_ID,
            OfficeMetrics(0, self.reports_generated, self.routed_reports),
            health,
            f"office:{FUSION_OFFICE_ID}",
        )


def _payload_signals(payload: dict) -> tuple[dict, ...]:
    signals: list[dict] = []
    for key in sorted(payload):
        if key.endswith("_signals") and isinstance(payload[key], list):
            signals.extend(item for item in payload[key] if isinstance(item, dict))
    return tuple(signals)
