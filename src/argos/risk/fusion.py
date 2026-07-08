"""Risk Fusion Office."""

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

from .department import RiskDepartment
from .offices import RISK_GROUP_ID, RiskOfficeInstrumentPanel


RISK_FUSION_OFFICE_ID = "RISK-OFFICE-010"


@dataclass(frozen=True)
class RiskFusionInput:
    """Immutable subordinate Risk Office report input."""

    office_id: str
    source_report_id: str
    risk_domain: str
    risk_score: float
    confidence: float
    exposure: float
    recommendation: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class OrganizationalRiskAssessment:
    """Unified organizational risk assessment."""

    assessment_id: str
    integrated_risk_score: float
    posture: str
    source_report_ids: tuple[str, ...]


@dataclass(frozen=True)
class IntegratedConfidenceAssessment:
    """Integrated confidence assessment."""

    assessment_id: str
    organizational_confidence: float
    contributing_reports: tuple[str, ...]


@dataclass(frozen=True)
class RiskFusionInstrumentPanel:
    """Risk Fusion Office instrument panel."""

    base_panel: RiskOfficeInstrumentPanel
    integrated_reports: int
    enterprise_exposure: float
    integrated_risk_score: float
    priority_count: int
    emergent_risks: int


class RiskReportAggregator:
    def aggregate(self, reports: tuple[RiskFusionInput, ...]) -> tuple[dict[str, object], ...]:
        return tuple(report.__dict__ for report in reports)


class CrossRiskInteractionEngine:
    def evaluate(self, reports: tuple[RiskFusionInput, ...]) -> dict[str, object]:
        interactions = []
        for left_index, left in enumerate(reports):
            for right in reports[left_index + 1 :]:
                if left.risk_score >= 0.6 and right.risk_score >= 0.6:
                    interactions.append({"domains": (left.risk_domain, right.risk_domain), "interaction": "risk_reinforcement"})
                elif left.recommendation != right.recommendation:
                    interactions.append({"domains": (left.risk_domain, right.risk_domain), "interaction": "recommendation_divergence"})
        return {"report_id": "CRIR-001", "interactions": tuple(interactions)}


class RecommendationResolver:
    def resolve(self, reports: tuple[RiskFusionInput, ...]) -> dict[str, object]:
        recommendations = sorted({report.recommendation for report in reports})
        conflicts = tuple(recommendation for recommendation in recommendations if recommendation != recommendations[0]) if len(recommendations) > 1 else ()
        priority = "reduce_enterprise_risk" if any("reduce" in recommendation for recommendation in recommendations) else recommendations[0]
        return {"resolution_id": "RR-001", "primary_mitigation": priority, "conflicting_recommendations": conflicts}


class EmergentRiskDetector:
    def detect(self, reports: tuple[RiskFusionInput, ...], interaction_count: int) -> dict[str, object]:
        risks = []
        high_domains = tuple(report.risk_domain for report in reports if report.risk_score >= 0.65)
        if len(high_domains) >= 2:
            risks.append({"risk_id": "ER-001", "description": "multiple_high_risk_domains", "domains": high_domains})
        if interaction_count >= 3:
            risks.append({"risk_id": "ER-002", "description": "dense_cross_risk_interactions", "interaction_count": interaction_count})
        return {"register_id": "ERR-001", "emergent_risks": tuple(risks)}


class EnterpriseExposureEngine:
    def assess(self, reports: tuple[RiskFusionInput, ...]) -> dict[str, float | str]:
        exposure = round(sum(report.exposure for report in reports), 4)
        weighted = sum(report.risk_score * report.exposure for report in reports) / exposure if exposure else 0.0
        return {"assessment_id": "OEA-001", "enterprise_exposure": exposure, "exposure_weighted_risk": round(weighted, 4)}


class ExecutiveRiskPrioritizer:
    def prioritize(self, reports: tuple[RiskFusionInput, ...]) -> tuple[dict[str, object], ...]:
        ranked = sorted(reports, key=lambda report: (-report.risk_score, -report.exposure, report.risk_domain))
        return tuple({"rank": index, "risk_domain": report.risk_domain, "source_report_id": report.source_report_id, "risk_score": report.risk_score} for index, report in enumerate(ranked, start=1))


class EnterpriseMitigationCoordinator:
    def plan(self, resolution: dict[str, object], priorities: tuple[dict[str, object], ...]) -> dict[str, object]:
        steps = tuple({"sequence": index, "risk_domain": item["risk_domain"], "action": resolution["primary_mitigation"]} for index, item in enumerate(priorities[:3], start=1))
        return {"plan_id": "EMP-001", "steps": steps}


class EnterpriseRiskArchive:
    def archive(self, assessment: OrganizationalRiskAssessment, source_report_ids: tuple[str, ...]) -> dict[str, object]:
        return {"archive_id": "ERA-001", "assessment_id": assessment.assessment_id, "posture": assessment.posture, "source_report_ids": source_report_ids}


class RiskFusionOfficeChief:
    """Office Chief for deterministic risk fusion."""

    def __init__(self) -> None:
        self.aggregator = RiskReportAggregator()
        self.interactions = CrossRiskInteractionEngine()
        self.resolver = RecommendationResolver()
        self.emergent = EmergentRiskDetector()
        self.exposure = EnterpriseExposureEngine()
        self.prioritizer = ExecutiveRiskPrioritizer()
        self.mitigation = EnterpriseMitigationCoordinator()
        self.archive = EnterpriseRiskArchive()

    def evaluate(self, reports: tuple[RiskFusionInput, ...]) -> dict[str, object]:
        if not reports:
            raise ValueError("risk fusion requires at least one subordinate risk report")
        aggregated = self.aggregator.aggregate(reports)
        interactions = self.interactions.evaluate(reports)
        resolution = self.resolver.resolve(reports)
        emergent = self.emergent.detect(reports, len(interactions["interactions"]))
        exposure = self.exposure.assess(reports)
        priorities = self.prioritizer.prioritize(reports)
        mitigation = self.mitigation.plan(resolution, priorities)
        confidence = self.confidence(reports, len(emergent["emergent_risks"]))
        integrated_score = round(float(exposure["exposure_weighted_risk"]) * 0.75 + (1 - confidence.organizational_confidence) * 0.25, 4)
        posture = self.posture(integrated_score)
        source_ids = tuple(report.source_report_id for report in reports)
        assessment = OrganizationalRiskAssessment("ORA-001", integrated_score, posture, source_ids)
        return {
            "organizational_risk_assessment": assessment.__dict__,
            "executive_risk_summary": {"summary_id": "ERS-001", "posture": posture, "top_priority": priorities[0]},
            "cross_risk_interaction_report": interactions,
            "emergent_risk_register": emergent,
            "organizational_exposure_assessment": exposure,
            "enterprise_mitigation_plan": mitigation,
            "executive_risk_priority_list": priorities,
            "organizational_risk_posture_record": {"record_id": "ORPR-001", "posture": posture, "integrated_risk_score": integrated_score},
            "enterprise_risk_archive": self.archive.archive(assessment, source_ids),
            "integrated_confidence_assessment": confidence.__dict__,
            "aggregated_risk_reports": aggregated,
            "subordinate_independence_preserved": True,
        }

    def confidence(self, reports: tuple[RiskFusionInput, ...], emergent_count: int) -> IntegratedConfidenceAssessment:
        average = sum(report.confidence for report in reports) / len(reports)
        adjusted = round(max(0.0, min(1.0, average - emergent_count * 0.04)), 4)
        return IntegratedConfidenceAssessment("ICA-001", adjusted, tuple(report.source_report_id for report in reports))

    def posture(self, score: float) -> str:
        if score >= 0.7:
            return "defensive_posture_required"
        if score >= 0.45:
            return "elevated_risk_posture"
        return "stable_risk_posture"


class RiskFusionOffice:
    """Risk Fusion Office integrated with the Risk Department framework."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = RiskDepartment(configuration_service, persistence_repository, audit_service, prompt_repository)
        self.office = self.department.offices[RISK_FUSION_OFFICE_ID]
        self.chief = RiskFusionOfficeChief()
        self._latest_review: dict[str, object] | None = None

    def generate_risk_fusion_report(
        self,
        reports: tuple[RiskFusionInput, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        """Generate an Organizational Risk Assessment as a RAR."""
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        review = self.chief.evaluate(reports)
        source_ids = tuple(report.source_report_id for report in reports)
        created = utc_timestamp()
        payload = {
            "risk_id": f"FUS-{document_sequence:06d}",
            "office_id": RISK_FUSION_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "risk_fusion_assessment",
            "case_file_id": case_file_id,
            "trade_cycle_id": trade_cycle_id,
            **review,
            "subordinate_reports_modified": False,
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
            parent_contract_ids=source_ids,
            produced_by_staff_id=self.office.record.configuration.staff_id,
            produced_by_group_id=RISK_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary="Organizational Risk Assessment.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.department.audit_service.record_document_creation(report)
        self.office.reports_generated += 1
        self._latest_review = review
        return report

    def route_report(self, report: OperationalContract, target_inbox: IncomingMailbox):
        """Route a Risk Fusion Report through Courier Framework."""
        return self.department.route_rar(RISK_FUSION_OFFICE_ID, report, target_inbox)

    def instrument_panel(self) -> RiskFusionInstrumentPanel:
        """Return the Risk Fusion Office instrument panel."""
        base = self.office.instrument_panel()
        if not self._latest_review:
            return RiskFusionInstrumentPanel(base, 0, 0.0, 0.0, 0, 0)
        return RiskFusionInstrumentPanel(
            base,
            len(self._latest_review["aggregated_risk_reports"]),
            float(self._latest_review["organizational_exposure_assessment"]["enterprise_exposure"]),
            float(self._latest_review["organizational_risk_assessment"]["integrated_risk_score"]),
            len(self._latest_review["executive_risk_priority_list"]),
            len(self._latest_review["emergent_risk_register"]["emergent_risks"]),
        )
