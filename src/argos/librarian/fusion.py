"""Librarian Fusion Office."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .group import LIBRARIAN_GROUP_ID


LIBRARIAN_FUSION_OFFICE_ID = "LIBRARIAN-OFFICE-006"
LIBRARIAN_FUSION_STAFF_ID = "STF-086"


class KnowledgeCapabilityType(str, Enum):
    """Librarian knowledge management capability."""

    INSTITUTIONAL_KNOWLEDGE = "institutional_knowledge"
    DOCTRINE_MANAGEMENT = "doctrine_management"
    SPECIFICATION_REPOSITORY = "specification_repository"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    LEARNING_INTEGRATION = "learning_integration"


class KnowledgeRiskLevel(str, Enum):
    """Knowledge risk level."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class KnowledgeCapabilityAssessment:
    """Cross-office fusion input."""

    capability_id: str
    capability_type: KnowledgeCapabilityType
    quality_score: float
    consistency_score: float
    accessibility_score: float
    strategic_value_score: float
    integrity_verified: bool
    deficiency_ids: tuple[str, ...]
    risk_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class EnterpriseKnowledgeIntegrationArchitecture:
    """Enterprise knowledge integration architecture."""

    architecture_id: str
    capability_count: int
    integrated_capability_types: tuple[KnowledgeCapabilityType, ...]
    cross_office_fusion_responsibilities: tuple[str, ...]
    traceability_preserved: bool


@dataclass(frozen=True)
class KnowledgeGovernanceFramework:
    """Knowledge governance framework."""

    governance_id: str
    standards_documented: bool
    deficiency_count: int
    governance_deficiency_ids: tuple[str, ...]
    escalation_required: bool


@dataclass(frozen=True)
class EnterpriseConsistencyAnalysis:
    """Enterprise consistency analysis framework."""

    analysis_id: str
    average_consistency_score: float
    inconsistent_capability_ids: tuple[str, ...]
    cross_office_conflict_count: int
    consistency_status: str


@dataclass(frozen=True)
class KnowledgeQualityAssuranceStandard:
    """Knowledge quality assurance standard."""

    qa_id: str
    average_quality_score: float
    low_quality_capability_ids: tuple[str, ...]
    quality_assurance_passed: bool
    scientific_validation_required: bool


@dataclass(frozen=True)
class StrategicKnowledgePlanningFramework:
    """Strategic knowledge planning framework."""

    planning_id: str
    strategic_value_score: float
    future_capability_requirements: tuple[str, ...]
    planning_methodology: str


@dataclass(frozen=True)
class KnowledgeRiskAssessmentFramework:
    """Knowledge risk assessment framework."""

    risk_assessment_id: str
    risk_level: KnowledgeRiskLevel
    knowledge_risk_ids: tuple[str, ...]
    mitigation_recommendations: tuple[str, ...]


@dataclass(frozen=True)
class ExecutiveKnowledgeReportingStandard:
    """Executive knowledge reporting standard."""

    report_id: str
    executive_summary: str
    recommended_executive_actions: tuple[str, ...]
    traceability_ids: tuple[str, ...]


@dataclass(frozen=True)
class EnterpriseKnowledgeDashboard:
    """Enterprise knowledge dashboard."""

    dashboard_id: str
    capability_count: int
    average_quality_score: float
    average_consistency_score: float
    average_accessibility_score: float
    strategic_value_score: float
    risk_level: KnowledgeRiskLevel
    knowledge_health: str


@dataclass(frozen=True)
class InstitutionalIntelligenceAssessmentFramework:
    """Institutional intelligence assessment framework."""

    assessment_id: str
    institutional_intelligence_score: float
    coherent_institution: bool
    continuously_improving: bool
    strategic_asset_status: str


@dataclass(frozen=True)
class LibrarianFusionSystemPrompt:
    """Librarian Fusion Office prompt."""

    prompt_id: str
    version: str
    prompt_text: str


class LibrarianFusionOffice:
    """Chief Knowledge Office integrating all Librarian capabilities."""

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

    def system_prompt(self) -> LibrarianFusionSystemPrompt:
        """Return governing Librarian Fusion prompt."""
        return LibrarianFusionSystemPrompt(
            "PROMPT-LFO-076",
            "1.0.0",
            (
                "You are the Librarian Fusion Office of ARGOS.\n\n"
                "Integrate every knowledge management capability into a unified enterprise intelligence system. "
                "Continuously evaluate the integrity, quality, consistency, accessibility, and strategic value of "
                "institutional knowledge, doctrine, specifications, semantic relationships, organizational learning, "
                "and historical evidence. Identify governance deficiencies, knowledge risks, inconsistencies, and "
                "future capability requirements while maintaining complete traceability, scientific validation, and "
                "deterministic enterprise knowledge governance."
            ),
        )

    def fuse_knowledge_capabilities(
        self,
        assessments: tuple[KnowledgeCapabilityAssessment, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Fuse every Librarian capability into deterministic enterprise knowledge artifacts."""
        self.configuration_service.validate_startup()
        ordered = tuple(sorted(assessments, key=lambda item: item.capability_id))
        governance = _governance(ordered, document_sequence)
        consistency = _consistency(ordered, document_sequence)
        quality = _quality(ordered, document_sequence)
        planning = _planning(ordered, document_sequence)
        risk = _risk(ordered, document_sequence)
        executive = _executive_report(ordered, governance, consistency, quality, risk, document_sequence)
        dashboard = _dashboard(ordered, planning, risk, document_sequence)
        intelligence = _intelligence(ordered, dashboard, document_sequence)
        architecture = EnterpriseKnowledgeIntegrationArchitecture(
            f"EKIA-{document_sequence:06d}",
            len(ordered),
            tuple(sorted({item.capability_type for item in ordered}, key=lambda item: item.value)),
            (
                "Integrate institutional memory, doctrine, specifications, semantic graph, and learning records.",
                "Detect cross-office inconsistencies and governance deficiencies.",
                "Report strategic knowledge risk to Executive Group without modifying source records.",
            ),
            all(item.evidence_ids for item in ordered),
        )
        return {
            "enterprise_knowledge_integration_architecture": self._persist_contract(
                "ENTERPRISE_KNOWLEDGE_INTEGRATION_ARCHITECTURE",
                case_file_id,
                trade_cycle_id,
                document_sequence,
                "Enterprise Knowledge Integration Architecture.",
                {"integration_architecture": architecture, "capability_assessments": ordered, "system_prompt": self.system_prompt()},
            ),
            "knowledge_governance_framework": self._persist_contract(
                "KNOWLEDGE_GOVERNANCE_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 1,
                "Knowledge Governance Framework.",
                {"knowledge_governance_framework": governance},
            ),
            "enterprise_consistency_analysis_framework": self._persist_contract(
                "ENTERPRISE_CONSISTENCY_ANALYSIS_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 2,
                "Enterprise Consistency Analysis Framework.",
                {"enterprise_consistency_analysis": consistency, "knowledge_quality_assurance_standard": quality},
            ),
            "strategic_knowledge_planning_framework": self._persist_contract(
                "STRATEGIC_KNOWLEDGE_PLANNING_FRAMEWORK",
                case_file_id,
                trade_cycle_id,
                document_sequence + 3,
                "Strategic Knowledge Planning Framework.",
                {"strategic_knowledge_planning_framework": planning, "knowledge_risk_assessment_framework": risk},
            ),
            "executive_knowledge_reporting_standard": self._persist_contract(
                "EXECUTIVE_KNOWLEDGE_REPORTING_STANDARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 4,
                "Executive Knowledge Reporting Standard.",
                {"executive_knowledge_reporting_standard": executive},
            ),
            "enterprise_knowledge_dashboard": self._persist_contract(
                "ENTERPRISE_KNOWLEDGE_DASHBOARD",
                case_file_id,
                trade_cycle_id,
                document_sequence + 5,
                "Enterprise Knowledge Dashboard.",
                {"enterprise_knowledge_dashboard": dashboard, "institutional_intelligence_assessment_framework": intelligence},
            ),
        }

    def _persist_contract(
        self,
        contract_type: str,
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        human_summary: str,
        payload: dict[str, Any],
    ) -> OperationalContract:
        contract = _contract(contract_type, case_file_id, trade_cycle_id, document_sequence, human_summary, payload)
        self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
        self.audit_service.record_document_creation(contract)
        return contract


def _average(values: tuple[float, ...]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _governance(assessments: tuple[KnowledgeCapabilityAssessment, ...], document_sequence: int) -> KnowledgeGovernanceFramework:
    deficiencies = tuple(sorted({deficiency for assessment in assessments for deficiency in assessment.deficiency_ids}))
    return KnowledgeGovernanceFramework(
        f"KGF-{document_sequence:06d}",
        True,
        len(deficiencies),
        deficiencies,
        bool(deficiencies),
    )


def _consistency(assessments: tuple[KnowledgeCapabilityAssessment, ...], document_sequence: int) -> EnterpriseConsistencyAnalysis:
    inconsistent = tuple(sorted(item.capability_id for item in assessments if item.consistency_score < 0.75))
    average = _average(tuple(item.consistency_score for item in assessments))
    return EnterpriseConsistencyAnalysis(
        f"ECA-{document_sequence:06d}",
        average,
        inconsistent,
        len(inconsistent),
        "consistent" if not inconsistent else "attention_required",
    )


def _quality(assessments: tuple[KnowledgeCapabilityAssessment, ...], document_sequence: int) -> KnowledgeQualityAssuranceStandard:
    low_quality = tuple(sorted(item.capability_id for item in assessments if item.quality_score < 0.75 or not item.integrity_verified))
    average = _average(tuple(item.quality_score for item in assessments))
    return KnowledgeQualityAssuranceStandard(
        f"KQA-{document_sequence:06d}",
        average,
        low_quality,
        not low_quality,
        bool(low_quality),
    )


def _planning(assessments: tuple[KnowledgeCapabilityAssessment, ...], document_sequence: int) -> StrategicKnowledgePlanningFramework:
    average_value = _average(tuple(item.strategic_value_score for item in assessments))
    requirements = []
    if any(item.accessibility_score < 0.8 for item in assessments):
        requirements.append("Improve deterministic knowledge retrieval and Academy-ready access.")
    if any(item.risk_ids for item in assessments):
        requirements.append("Create mitigation plan for enterprise knowledge risks.")
    if len({item.capability_type for item in assessments}) < len(KnowledgeCapabilityType):
        requirements.append("Complete fusion coverage for every Librarian office.")
    return StrategicKnowledgePlanningFramework(
        f"SKP-{document_sequence:06d}",
        average_value,
        tuple(requirements),
        "Rank future knowledge capabilities by accessibility gaps, risk exposure, coverage completeness, and strategic value.",
    )


def _risk(assessments: tuple[KnowledgeCapabilityAssessment, ...], document_sequence: int) -> KnowledgeRiskAssessmentFramework:
    risks = tuple(sorted({risk for assessment in assessments for risk in assessment.risk_ids}))
    deficiency_count = sum(len(item.deficiency_ids) for item in assessments)
    if len(risks) >= 4 or deficiency_count >= 4:
        level = KnowledgeRiskLevel.CRITICAL
    elif len(risks) >= 2 or deficiency_count >= 2:
        level = KnowledgeRiskLevel.HIGH
    elif risks or deficiency_count:
        level = KnowledgeRiskLevel.MODERATE
    else:
        level = KnowledgeRiskLevel.LOW
    mitigations = tuple(f"Mitigate {risk} through accountable Librarian governance review." for risk in risks)
    return KnowledgeRiskAssessmentFramework(
        f"KRA-{document_sequence:06d}",
        level,
        risks,
        mitigations,
    )


def _executive_report(
    assessments: tuple[KnowledgeCapabilityAssessment, ...],
    governance: KnowledgeGovernanceFramework,
    consistency: EnterpriseConsistencyAnalysis,
    quality: KnowledgeQualityAssuranceStandard,
    risk: KnowledgeRiskAssessmentFramework,
    document_sequence: int,
) -> ExecutiveKnowledgeReportingStandard:
    actions = []
    if governance.escalation_required:
        actions.append("Authorize corrective governance review for identified knowledge deficiencies.")
    if consistency.cross_office_conflict_count:
        actions.append("Request Librarian reconciliation plan for inconsistent capabilities.")
    if not quality.quality_assurance_passed:
        actions.append("Require scientific validation before downstream Academy or operational use.")
    if risk.risk_level in {KnowledgeRiskLevel.HIGH, KnowledgeRiskLevel.CRITICAL}:
        actions.append("Prioritize enterprise knowledge risk mitigation.")
    if not actions:
        actions.append("Maintain current Librarian governance cadence.")
    evidence = tuple(sorted({evidence for assessment in assessments for evidence in assessment.evidence_ids}))
    return ExecutiveKnowledgeReportingStandard(
        f"EKR-{document_sequence:06d}",
        f"Librarian Fusion assessed {len(assessments)} capabilities with {risk.risk_level.value} enterprise knowledge risk.",
        tuple(actions),
        evidence,
    )


def _dashboard(
    assessments: tuple[KnowledgeCapabilityAssessment, ...],
    planning: StrategicKnowledgePlanningFramework,
    risk: KnowledgeRiskAssessmentFramework,
    document_sequence: int,
) -> EnterpriseKnowledgeDashboard:
    quality = _average(tuple(item.quality_score for item in assessments))
    consistency = _average(tuple(item.consistency_score for item in assessments))
    accessibility = _average(tuple(item.accessibility_score for item in assessments))
    health = "healthy" if risk.risk_level == KnowledgeRiskLevel.LOW and quality >= 0.8 and consistency >= 0.8 and not planning.future_capability_requirements else "attention"
    return EnterpriseKnowledgeDashboard(
        f"EKD-{document_sequence:06d}",
        len(assessments),
        quality,
        consistency,
        accessibility,
        planning.strategic_value_score,
        risk.risk_level,
        health,
    )


def _intelligence(
    assessments: tuple[KnowledgeCapabilityAssessment, ...],
    dashboard: EnterpriseKnowledgeDashboard,
    document_sequence: int,
) -> InstitutionalIntelligenceAssessmentFramework:
    integrity_score = _average(tuple(1.0 if item.integrity_verified else 0.0 for item in assessments))
    score = round((dashboard.average_quality_score + dashboard.average_consistency_score + dashboard.average_accessibility_score + dashboard.strategic_value_score + integrity_score) / 5, 6)
    coherent = score >= 0.8 and dashboard.risk_level in {KnowledgeRiskLevel.LOW, KnowledgeRiskLevel.MODERATE}
    improving = any(item.capability_type == KnowledgeCapabilityType.LEARNING_INTEGRATION for item in assessments)
    return InstitutionalIntelligenceAssessmentFramework(
        f"IIA-{document_sequence:06d}",
        score,
        coherent,
        improving,
        "strategic_asset" if coherent and improving else "developing_asset",
    )


def _contract(
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    document_sequence: int,
    human_summary: str,
    payload: dict[str, Any],
) -> OperationalContract:
    created = utc_timestamp()
    normalized_payload = _json_ready(payload)
    signature_hash = hashlib.sha256(json.dumps(normalized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        parent_contract_ids=(),
        produced_by_staff_id=LIBRARIAN_FUSION_STAFF_ID,
        produced_by_group_id=LIBRARIAN_GROUP_ID,
        intended_consumer_group_id=LIBRARIAN_GROUP_ID,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=human_summary,
        machine_payload=normalized_payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
