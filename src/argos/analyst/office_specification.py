"""ANALYST-RM-003 constitutional engineering specification support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


@dataclass(frozen=True)
class AnalystMissionCanonicalSpecificationRecord:
    specification_identifier: str
    schema_sections: Mapping[str, tuple[str, ...]]
    identity_fields: tuple[str, ...]
    permitted_authorities: tuple[str, ...]
    prohibited_authorities: tuple[str, ...]
    subordinate_relationships: tuple[str, ...]
    lifecycle_states: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    persistent_elements: tuple[str, ...]
    replay_restoration_fields: tuple[str, ...]
    recovery_restoration_fields: tuple[str, ...]
    audit_events: tuple[str, ...]
    invariant_registry: tuple[str, ...]
    missing_schema_fields: tuple[str, ...]
    duplicate_identity_findings: tuple[str, ...]
    authority_violations: tuple[str, ...]
    lifecycle_violations: tuple[str, ...]
    validation_failures: tuple[str, ...]
    persistence_gaps: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_inference_findings: tuple[str, ...]
    traceability_gaps: tuple[str, ...]
    fail_closed: bool
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm003SpecificationEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    specification_order_coverage: tuple[str, ...]
    analytical_mission: AnalystMissionCanonicalSpecificationRecord
    final_specification_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


class AnalystOfficeSpecificationSupport:
    """Build deterministic certification-support records for ANALYST-RM-003."""

    specification_order_coverage = ("ANALYST-RM-003-001",)

    def build_package(self) -> AnalystRm003SpecificationEvidencePackage:
        mission = self.evaluate_analytical_mission_specification()
        package = AnalystRm003SpecificationEvidencePackage(
            package_identifier=f"ANALYST-RM-003-PACKAGE-{_digest(mission)[:12].upper()}",
            governing_doctrine="ANALYST-RM-003-001/1.0.0",
            specification_order_coverage=self.specification_order_coverage,
            analytical_mission=mission,
            final_specification_readiness=mission.result,
            immutable_audit_references=(mission.specification_identifier,),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_analytical_mission_specification(
        self,
        *,
        missing_schema_fields: tuple[str, ...] = (),
        duplicate_identity_findings: tuple[str, ...] = (),
        authority_violations: tuple[str, ...] = (),
        lifecycle_violations: tuple[str, ...] = (),
        validation_failures: tuple[str, ...] = (),
        persistence_gaps: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_inference_findings: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
        fail_closed: bool = True,
    ) -> AnalystMissionCanonicalSpecificationRecord:
        schema = MappingProxyType(
            {
                "Identity": (
                    "Mission Identifier",
                    "Mission Revision Identifier",
                    "Mission Version",
                    "Mission Class",
                    "Object Type Identifier",
                    "Constitutional Version",
                    "Schema Version",
                    "Office Identifier",
                    "Workflow Execution Token Identifier",
                    "Configuration Version",
                    "Certification Version",
                ),
                "Authority": (
                    "Creating Authority",
                    "Originating Office",
                    "Originating Authority",
                    "Receiving Office",
                    "Acceptance Authority",
                    "Mission Authority Token",
                    "Constitutional Authority Status",
                    "Authority Timestamp",
                    "Authority Scope",
                    "Authority Relinquishment Conditions",
                ),
                "Mission Definition": (
                    "Mission Name",
                    "Mission Description",
                    "Mission Purpose",
                    "Mission Objective",
                    "Mission Scope",
                    "Analytical Context",
                    "Completion Contract",
                    "Required Outputs",
                    "Requested Deliverables",
                    "Execution Constraints",
                ),
                "References": (
                    "Input References",
                    "Candidate Package References",
                    "Evidence References",
                    "Dependency References",
                    "Configuration Reference",
                    "Governing Doctrine References",
                    "Applicable Constitutional Rules",
                ),
                "Relationships": (
                    "Analysis Plan Reference",
                    "Analytical Package Reference",
                    "Reasoning Graph Reference",
                    "Hypothesis Set Reference",
                    "Confidence Assessment Reference",
                    "Conclusion Reference",
                    "Validation Record References",
                    "Traceability Record References",
                    "Certification Evidence References",
                ),
                "Lifecycle Metadata": (
                    "Creation Timestamp",
                    "Acceptance Timestamp",
                    "Activation Timestamp",
                    "Completion Timestamp",
                    "Termination Timestamp",
                    "Current Lifecycle State",
                    "Terminal State",
                ),
                "Validation Metadata": (
                    "Validation Status",
                    "Validation Version",
                    "Validation Results",
                    "Integrity Verification Status",
                ),
                "Audit Metadata": (
                    "Audit Identifier",
                    "Traceability Identifier",
                    "Replay Identifier",
                    "Recovery Identifier",
                    "Audit Status",
                    "Certification Status",
                    "Replay Status",
                    "Recovery Status",
                ),
            }
        )
        identity = (
            "Mission Identifier",
            "Mission Revision Identifier",
            "Mission Version",
            "Mission Class",
            "Object Type Identifier",
            "Constitutional Version",
            "Schema Version",
            "Office Identifier",
            "Workflow Execution Token Identifier",
            "Creation Timestamp",
            "Effective Timestamp",
            "Configuration Version",
            "Certification Version",
        )
        permitted = (
            "consume constitutionally admissible inputs",
            "perform deterministic reasoning",
            "evaluate evidence",
            "evaluate competing hypotheses",
            "determine confidence",
            "generate analytical conclusions",
            "generate recommendations",
            "produce audit evidence",
            "produce certification evidence",
        )
        prohibited = (
            "evidence acquisition outside mission scope",
            "enterprise risk evaluation",
            "trade execution",
            "enterprise history modification",
            "modification of enterprise-owned objects",
            "hidden authority generation",
        )
        relationships = (
            "Workflow Execution Token",
            "Analysis Plan",
            "Analytical Package",
            "Evidence Package",
            "Configuration Object",
            "Reasoning Graph",
            "Hypothesis Set",
            "Confidence Assessment",
            "Analytical Conclusion",
            "Validation Records",
            "Traceability Records",
            "Audit Records",
            "Certification Evidence",
        )
        lifecycle = (
            "Created",
            "Validated",
            "Authorized",
            "Active",
            "Suspended",
            "Recovering",
            "Completing",
            "Completed",
            "Archived",
            "Terminal",
        )
        validation = (
            "schema integrity",
            "identifier uniqueness",
            "ownership",
            "authority",
            "constitutional completeness",
            "configuration compatibility",
            "version compatibility",
            "input admissibility",
            "completion contract",
            "invariant compliance",
        )
        persisted = (
            "mission identity",
            "authority metadata",
            "scope",
            "objectives",
            "execution constraints",
            "configuration reference",
            "lifecycle state",
            "subordinate object references",
            "validation status",
            "provenance",
            "audit metadata",
            "certification metadata",
        )
        replay_fields = (
            "Mission Identifier",
            "authority",
            "scope",
            "configuration",
            "relationships",
            "lifecycle state",
            "validation state",
            "completion contract",
        )
        recovery_fields = (
            "mission authority",
            "mission version",
            "lifecycle state",
            "object relationships",
            "configuration references",
            "validation state",
            "completion status",
            "audit references",
        )
        audit_events = (
            "creation",
            "authorization",
            "acceptance",
            "activation",
            "validation",
            "execution",
            "suspension",
            "completion",
            "termination",
            "replay",
            "recovery",
            "archival",
        )
        invariants = (
            "every Analyst execution belongs to exactly one Analytical Mission",
            "every mission possesses exactly one constitutional owner",
            "mission identity is immutable",
            "mission authority is explicit and never inferred",
            "mission authority exists only while constitutionally active",
            "mission scope is immutable after activation",
            "every subordinate object references exactly one mission",
            "validation precedes execution",
            "mission completion permanently terminates execution authority",
            "mission replay reproduces identical constitutional behavior",
            "mission recovery preserves constitutional continuity",
            "mission provenance is complete",
            "mission audit history is immutable",
        )
        all_schema_fields = tuple(field for section in schema.values() for field in section)
        missing = tuple(field for field in all_schema_fields if field in missing_schema_fields)
        passed = (
            not missing
            and not duplicate_identity_findings
            and not authority_violations
            and not lifecycle_violations
            and not validation_failures
            and not persistence_gaps
            and not replay_divergence_findings
            and not recovery_inference_findings
            and not traceability_gaps
            and fail_closed
        )
        record = AnalystMissionCanonicalSpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-001-MISSION-{_digest((schema, identity, invariants))[:12].upper()}",
            schema_sections=schema,
            identity_fields=identity,
            permitted_authorities=permitted,
            prohibited_authorities=prohibited,
            subordinate_relationships=relationships,
            lifecycle_states=lifecycle,
            validation_requirements=validation,
            persistent_elements=persisted,
            replay_restoration_fields=replay_fields,
            recovery_restoration_fields=recovery_fields,
            audit_events=audit_events,
            invariant_registry=invariants,
            missing_schema_fields=missing,
            duplicate_identity_findings=duplicate_identity_findings,
            authority_violations=authority_violations,
            lifecycle_violations=lifecycle_violations,
            validation_failures=validation_failures,
            persistence_gaps=persistence_gaps,
            replay_divergence_findings=replay_divergence_findings,
            recovery_inference_findings=recovery_inference_findings,
            traceability_gaps=traceability_gaps,
            fail_closed=fail_closed,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return {key: _jsonable(item) for key, item in value.items()}
    if is_dataclass(value):
        return {
            field_info.name: _jsonable(getattr(value, field_info.name))
            for field_info in fields(value)
            if field_info.name != "deterministic_digest"
        }
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(item) for item in value]
    return value
