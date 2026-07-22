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


@dataclass(frozen=True)
class AnalystMissionLifecycleSpecificationRecord:
    specification_identifier: str
    lifecycle_states: Mapping[str, str]
    legal_transitions: Mapping[str, tuple[str, ...]]
    authority_acquisition_transition: str
    authority_relinquishment_states: tuple[str, ...]
    entry_requirements: tuple[str, ...]
    exit_requirements: tuple[str, ...]
    persistence_fields: tuple[str, ...]
    audit_fields: tuple[str, ...]
    invariants: tuple[str, ...]
    illegal_transition_findings: tuple[str, ...]
    duplicate_transition_findings: tuple[str, ...]
    missing_authority_findings: tuple[str, ...]
    invalid_checkpoint_findings: tuple[str, ...]
    persistence_failures: tuple[str, ...]
    provenance_gaps: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_boundary_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystSufficiencySpecificationRecord:
    specification_identifier: str
    sufficiency_object_fields: tuple[str, ...]
    sufficiency_categories: tuple[str, ...]
    completion_outcomes: tuple[str, ...]
    evaluation_sequence: tuple[str, ...]
    termination_outcomes: tuple[str, ...]
    missing_categories: tuple[str, ...]
    invalid_completion_outcomes: tuple[str, ...]
    sequencing_violations: tuple[str, ...]
    evidence_deficiencies: tuple[str, ...]
    reasoning_deficiencies: tuple[str, ...]
    validation_deficiencies: tuple[str, ...]
    confidence_deficiencies: tuple[str, ...]
    traceability_deficiencies: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystEquivalenceSpecificationRecord:
    specification_identifier: str
    equivalence_scope: tuple[str, ...]
    normalization_steps: tuple[str, ...]
    equivalence_domains: tuple[str, ...]
    duplicate_outcomes: tuple[str, ...]
    evaluation_sequence: tuple[str, ...]
    missing_scope: tuple[str, ...]
    normalization_failures: tuple[str, ...]
    semantic_comparison_failures: tuple[str, ...]
    duplicate_resolution_findings: tuple[str, ...]
    supersession_trace_gaps: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_state_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystFreshnessSpecificationRecord:
    specification_identifier: str
    freshness_scope: tuple[str, ...]
    freshness_states: tuple[str, ...]
    window_fields: tuple[str, ...]
    invariants: tuple[str, ...]
    missing_scope: tuple[str, ...]
    invalid_state_findings: tuple[str, ...]
    implicit_window_findings: tuple[str, ...]
    temporal_nondeterminism_findings: tuple[str, ...]
    inheritance_violations: tuple[str, ...]
    replay_admissibility_findings: tuple[str, ...]
    recovery_admissibility_findings: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystOrganizationalBeliefStateSpecificationRecord:
    specification_identifier: str
    schema_sections: Mapping[str, tuple[str, ...]]
    identity_fields: tuple[str, ...]
    required_representations: tuple[str, ...]
    persistent_state: tuple[str, ...]
    invariants: tuple[str, ...]
    missing_schema_fields: tuple[str, ...]
    ownership_violations: tuple[str, ...]
    unsupported_conclusion_findings: tuple[str, ...]
    implicit_assumption_findings: tuple[str, ...]
    hypothesis_preservation_findings: tuple[str, ...]
    contradiction_preservation_findings: tuple[str, ...]
    supersession_violations: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_mutation_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm003MissionDoctrineEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    specification_order_coverage: tuple[str, ...]
    mission_lifecycle: AnalystMissionLifecycleSpecificationRecord
    analytical_sufficiency: AnalystSufficiencySpecificationRecord
    analytical_equivalence: AnalystEquivalenceSpecificationRecord
    analytical_freshness: AnalystFreshnessSpecificationRecord
    organizational_belief_state: AnalystOrganizationalBeliefStateSpecificationRecord
    final_mission_doctrine_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRejectionTaxonomySpecificationRecord:
    specification_identifier: str
    rejection_classes: Mapping[str, str]
    rejection_record_fields: tuple[str, ...]
    rejection_lifecycle: tuple[str, ...]
    persistence_obligations: tuple[str, ...]
    replay_restoration_fields: tuple[str, ...]
    recovery_restoration_fields: tuple[str, ...]
    invariants: tuple[str, ...]
    missing_classes: tuple[str, ...]
    ambiguous_authority_findings: tuple[str, ...]
    mutation_findings: tuple[str, ...]
    lifecycle_violations: tuple[str, ...]
    missing_audit_evidence: tuple[str, ...]
    replay_inconsistencies: tuple[str, ...]
    recovery_inconsistencies: tuple[str, ...]
    traceability_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystEvidenceConstitutionSpecificationRecord:
    specification_identifier: str
    schema_sections: Mapping[str, tuple[str, ...]]
    evidence_classes: tuple[str, ...]
    admissibility_rules: tuple[str, ...]
    normalization_steps: tuple[str, ...]
    relationship_targets: tuple[str, ...]
    invariants: tuple[str, ...]
    missing_schema_fields: tuple[str, ...]
    unapproved_class_findings: tuple[str, ...]
    admissibility_failures: tuple[str, ...]
    normalization_failures: tuple[str, ...]
    orphaned_relationship_findings: tuple[str, ...]
    persistence_gaps: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_mutation_findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystProvenanceArchitectureSpecificationRecord:
    specification_identifier: str
    governed_object_scope: tuple[str, ...]
    identity_fields: tuple[str, ...]
    source_classes: tuple[str, ...]
    relationship_types: tuple[str, ...]
    required_chain: tuple[str, ...]
    node_fields: tuple[str, ...]
    edge_fields: tuple[str, ...]
    invariants: tuple[str, ...]
    missing_scope: tuple[str, ...]
    undocumented_source_findings: tuple[str, ...]
    graph_cycle_findings: tuple[str, ...]
    missing_chain_stages: tuple[str, ...]
    validation_failures: tuple[str, ...]
    persistence_gaps: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystOfficeStateMachineSpecificationRecord:
    specification_identifier: str
    execution_states: tuple[str, ...]
    legal_transitions: Mapping[str, tuple[str, ...]]
    special_transitions: Mapping[str, tuple[str, ...]]
    prohibited_transitions: tuple[str, ...]
    persistence_boundaries: tuple[str, ...]
    audit_fields: tuple[str, ...]
    invariants: tuple[str, ...]
    missing_states: tuple[str, ...]
    illegal_transition_findings: tuple[str, ...]
    unauthorized_transition_findings: tuple[str, ...]
    validation_failures: tuple[str, ...]
    persistence_failures: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_violations: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystPersistentStateSpecificationRecord:
    specification_identifier: str
    persistent_inventory: Mapping[str, tuple[str, ...]]
    transient_inventory: Mapping[str, tuple[str, ...]]
    classification_rules: Mapping[str, str]
    persistence_lifecycle: tuple[str, ...]
    durability_events: tuple[str, ...]
    replay_restoration_fields: tuple[str, ...]
    recovery_restoration_fields: tuple[str, ...]
    invariants: tuple[str, ...]
    missing_persistent_categories: tuple[str, ...]
    missing_transient_categories: tuple[str, ...]
    dual_classification_findings: tuple[str, ...]
    implicit_persistence_findings: tuple[str, ...]
    atomic_commit_failures: tuple[str, ...]
    durability_failures: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_divergence_findings: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm003ConstitutionalArchitectureEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    specification_order_coverage: tuple[str, ...]
    rejection_taxonomy: AnalystRejectionTaxonomySpecificationRecord
    evidence_constitution: AnalystEvidenceConstitutionSpecificationRecord
    provenance_architecture: AnalystProvenanceArchitectureSpecificationRecord
    office_state_machine: AnalystOfficeStateMachineSpecificationRecord
    persistent_state: AnalystPersistentStateSpecificationRecord
    final_architecture_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


class AnalystOfficeSpecificationSupport:
    """Build deterministic certification-support records for ANALYST-RM-003."""

    specification_order_coverage = ("ANALYST-RM-003-001",)

    mission_doctrine_order_coverage = (
        "ANALYST-RM-003-006",
        "ANALYST-RM-003-007",
        "ANALYST-RM-003-008",
        "ANALYST-RM-003-009",
        "ANALYST-RM-003-010",
    )

    constitutional_architecture_order_coverage = (
        "ANALYST-RM-003-011",
        "ANALYST-RM-003-012",
        "ANALYST-RM-003-013",
        "ANALYST-RM-003-014",
        "ANALYST-RM-003-015",
    )

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

    def build_mission_doctrine_package(self) -> AnalystRm003MissionDoctrineEvidencePackage:
        lifecycle = self.evaluate_mission_lifecycle_specification()
        sufficiency = self.evaluate_sufficiency_specification()
        equivalence = self.evaluate_equivalence_specification()
        freshness = self.evaluate_freshness_specification()
        obs = self.evaluate_organizational_belief_state_specification()
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (lifecycle, sufficiency, equivalence, freshness, obs)
        ) else EnterpriseCertificationDecision.FAIL
        package = AnalystRm003MissionDoctrineEvidencePackage(
            package_identifier=f"ANALYST-RM-003-MISSION-DOCTRINE-{_digest((lifecycle, sufficiency, equivalence, freshness, obs))[:12].upper()}",
            governing_doctrine="ANALYST-RM-003-006-TO-010/1.0.0",
            specification_order_coverage=self.mission_doctrine_order_coverage,
            mission_lifecycle=lifecycle,
            analytical_sufficiency=sufficiency,
            analytical_equivalence=equivalence,
            analytical_freshness=freshness,
            organizational_belief_state=obs,
            final_mission_doctrine_readiness=final,
            immutable_audit_references=(
                lifecycle.specification_identifier,
                sufficiency.specification_identifier,
                equivalence.specification_identifier,
                freshness.specification_identifier,
                obs.specification_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def build_constitutional_architecture_package(self) -> AnalystRm003ConstitutionalArchitectureEvidencePackage:
        rejection = self.evaluate_rejection_taxonomy_specification()
        evidence = self.evaluate_evidence_constitution_specification()
        provenance = self.evaluate_provenance_architecture_specification()
        state_machine = self.evaluate_office_state_machine_specification()
        persistent_state = self.evaluate_persistent_state_specification()
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (rejection, evidence, provenance, state_machine, persistent_state)
        ) else EnterpriseCertificationDecision.FAIL
        package = AnalystRm003ConstitutionalArchitectureEvidencePackage(
            package_identifier=f"ANALYST-RM-003-CONSTITUTIONAL-ARCH-{_digest((rejection, evidence, provenance, state_machine, persistent_state))[:12].upper()}",
            governing_doctrine="ANALYST-RM-003-011-TO-015/1.0.0",
            specification_order_coverage=self.constitutional_architecture_order_coverage,
            rejection_taxonomy=rejection,
            evidence_constitution=evidence,
            provenance_architecture=provenance,
            office_state_machine=state_machine,
            persistent_state=persistent_state,
            final_architecture_readiness=final,
            immutable_audit_references=(
                rejection.specification_identifier,
                evidence.specification_identifier,
                provenance.specification_identifier,
                state_machine.specification_identifier,
                persistent_state.specification_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_mission_lifecycle_specification(
        self,
        *,
        illegal_transition_findings: tuple[str, ...] = (),
        duplicate_transition_findings: tuple[str, ...] = (),
        missing_authority_findings: tuple[str, ...] = (),
        invalid_checkpoint_findings: tuple[str, ...] = (),
        persistence_failures: tuple[str, ...] = (),
        provenance_gaps: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_boundary_findings: tuple[str, ...] = (),
    ) -> AnalystMissionLifecycleSpecificationRecord:
        states = MappingProxyType(
            {
                "AM-001 Authorized": "mission authority granted; execution prohibited",
                "AM-002 Initialized": "mission object created and dependencies identified",
                "AM-003 Ready": "mission eligible to begin execution",
                "AM-004 Executing": "active analytical processing",
                "AM-005 Awaiting Validation": "execution completed and reasoning frozen",
                "AM-006 Validated": "constitutional validation satisfied",
                "AM-007 Completed": "mission authority relinquished",
                "AM-008 Archived": "immutable replay, audit, and certification preservation",
                "AM-009 Suspended": "temporary interruption with checkpoint persisted",
                "AM-010 Failed": "constitutional continuation impossible",
            }
        )
        transitions = MappingProxyType(
            {
                "Authorized": ("Initialized",),
                "Initialized": ("Ready",),
                "Ready": ("Executing",),
                "Executing": ("Awaiting Validation", "Suspended", "Failed"),
                "Suspended": ("Executing", "Failed"),
                "Awaiting Validation": ("Validated", "Failed"),
                "Validated": ("Completed",),
                "Completed": ("Archived",),
                "Archived": (),
                "Failed": (),
            }
        )
        entry = ("ownership validated", "schema valid", "inputs admissible", "configuration valid", "dependencies satisfied", "mission integrity verified")
        exit_required = ("reasoning complete", "validation prepared", "checkpoint committed", "provenance complete", "outputs frozen")
        persisted = ("lifecycle state", "transition timestamp", "triggering authority", "configuration version", "checkpoint reference", "validation status")
        audit = ("Mission Identifier", "Previous State", "Next State", "Transition Identifier", "Authority", "Timestamp", "Validation Outcome", "Checkpoint Identifier", "Configuration Version")
        invariants = ("AML-001 exactly one lifecycle state", "AML-002 deterministic transitions", "AML-003 illegal transitions impossible", "AML-004 authority only during Executing", "AML-005 completed missions never re-enter execution", "AML-006 archived missions immutable", "AML-007 transitions auditable", "AML-008 provenance preserved", "AML-009 replay reproduces lifecycle", "AML-010 recovery resumes committed boundary")
        passed = not illegal_transition_findings and not duplicate_transition_findings and not missing_authority_findings and not invalid_checkpoint_findings and not persistence_failures and not provenance_gaps and not replay_divergence_findings and not recovery_boundary_findings
        record = AnalystMissionLifecycleSpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-006-LIFECYCLE-{_digest((states, transitions))[:12].upper()}",
            lifecycle_states=states,
            legal_transitions=transitions,
            authority_acquisition_transition="Ready->Executing",
            authority_relinquishment_states=("Completed", "Failed", "Archived"),
            entry_requirements=entry,
            exit_requirements=exit_required,
            persistence_fields=persisted,
            audit_fields=audit,
            invariants=invariants,
            illegal_transition_findings=illegal_transition_findings,
            duplicate_transition_findings=duplicate_transition_findings,
            missing_authority_findings=missing_authority_findings,
            invalid_checkpoint_findings=invalid_checkpoint_findings,
            persistence_failures=persistence_failures,
            provenance_gaps=provenance_gaps,
            replay_divergence_findings=replay_divergence_findings,
            recovery_boundary_findings=recovery_boundary_findings,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_sufficiency_specification(
        self,
        *,
        missing_categories: tuple[str, ...] = (),
        invalid_completion_outcomes: tuple[str, ...] = (),
        sequencing_violations: tuple[str, ...] = (),
        evidence_deficiencies: tuple[str, ...] = (),
        reasoning_deficiencies: tuple[str, ...] = (),
        validation_deficiencies: tuple[str, ...] = (),
        confidence_deficiencies: tuple[str, ...] = (),
        traceability_deficiencies: tuple[str, ...] = (),
    ) -> AnalystSufficiencySpecificationRecord:
        fields_required = ("Sufficiency Evaluation Identifier", "Analytical Mission Identifier", "Evaluation Timestamp", "Evaluation Version", "Evaluation Outcome", "Completion Decision", "Governing Configuration", "Governing Doctrine Version", "Validation References", "Audit References")
        categories = ("Evidence Sufficiency", "Reasoning Sufficiency", "Hypothesis Sufficiency", "Confidence Sufficiency", "Validation Sufficiency", "Traceability Sufficiency")
        outcomes = ("Constitutionally Complete", "Constitutionally Incomplete", "Additional Analysis Required", "Validation Failure", "Evidence Deficiency", "Hypothesis Deficiency", "Confidence Deficiency")
        sequence = ("Verify mission completeness", "Verify evidence completeness", "Verify evidence admissibility", "Verify reasoning graph completeness", "Verify competing hypothesis evaluation", "Verify confidence determination", "Verify validation completion", "Verify constitutional invariants", "Verify traceability", "Issue completion decision", "Record immutable audit evidence")
        termination = ("Successful Completion", "Constitutional Rejection", "Authority Revocation", "Irrecoverable Constitutional Failure")
        missing = tuple(category for category in categories if category in missing_categories)
        invalid = tuple(outcome for outcome in invalid_completion_outcomes if outcome not in outcomes)
        passed = not missing and not invalid and not sequencing_violations and not evidence_deficiencies and not reasoning_deficiencies and not validation_deficiencies and not confidence_deficiencies and not traceability_deficiencies
        record = AnalystSufficiencySpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-007-SUFF-{_digest((fields_required, categories))[:12].upper()}",
            sufficiency_object_fields=fields_required,
            sufficiency_categories=categories,
            completion_outcomes=outcomes,
            evaluation_sequence=sequence,
            termination_outcomes=termination,
            missing_categories=missing,
            invalid_completion_outcomes=invalid,
            sequencing_violations=sequencing_violations,
            evidence_deficiencies=evidence_deficiencies,
            reasoning_deficiencies=reasoning_deficiencies,
            validation_deficiencies=validation_deficiencies,
            confidence_deficiencies=confidence_deficiencies,
            traceability_deficiencies=traceability_deficiencies,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_equivalence_specification(
        self,
        *,
        missing_scope: tuple[str, ...] = (),
        normalization_failures: tuple[str, ...] = (),
        semantic_comparison_failures: tuple[str, ...] = (),
        duplicate_resolution_findings: tuple[str, ...] = (),
        supersession_trace_gaps: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_state_findings: tuple[str, ...] = (),
    ) -> AnalystEquivalenceSpecificationRecord:
        scope = ("Analytical Missions", "Analysis Plans", "Analytical Packages", "Reasoning Graphs", "Evidence Objects", "Intermediate Conclusions", "Final Conclusions", "Confidence Objects", "Competing Hypotheses", "Organizational Belief States", "Validation Objects", "Configuration Objects", "Certification Evidence")
        normalization = ("canonical identifiers", "canonical timestamps", "canonical enumeration values", "canonical numeric precision", "canonical units", "canonical ordering", "canonical field representation", "canonical reference ordering")
        domains = ("Structural Equivalence", "Semantic Equivalence", "Evidence Equivalence", "Reasoning Equivalence", "Conclusion Equivalence", "Confidence Equivalence", "Configuration Equivalence", "Mission Equivalence")
        duplicate_outcomes = ("retain canonical object", "preserve superseded object", "reject duplicate", "merge constitutionally equivalent metadata where permitted")
        sequence = ("Validate admissibility", "Normalize both objects", "Verify schema compatibility", "Compare structural equivalence", "Compare semantic equivalence", "Compare constitutional invariants", "Produce immutable equivalence determination")
        missing = tuple(item for item in scope if item in missing_scope)
        passed = not missing and not normalization_failures and not semantic_comparison_failures and not duplicate_resolution_findings and not supersession_trace_gaps and not replay_divergence_findings and not recovery_state_findings
        record = AnalystEquivalenceSpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-008-EQUIV-{_digest((scope, normalization))[:12].upper()}",
            equivalence_scope=scope,
            normalization_steps=normalization,
            equivalence_domains=domains,
            duplicate_outcomes=duplicate_outcomes,
            evaluation_sequence=sequence,
            missing_scope=missing,
            normalization_failures=normalization_failures,
            semantic_comparison_failures=semantic_comparison_failures,
            duplicate_resolution_findings=duplicate_resolution_findings,
            supersession_trace_gaps=supersession_trace_gaps,
            replay_divergence_findings=replay_divergence_findings,
            recovery_state_findings=recovery_state_findings,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_freshness_specification(
        self,
        *,
        missing_scope: tuple[str, ...] = (),
        invalid_state_findings: tuple[str, ...] = (),
        implicit_window_findings: tuple[str, ...] = (),
        temporal_nondeterminism_findings: tuple[str, ...] = (),
        inheritance_violations: tuple[str, ...] = (),
        replay_admissibility_findings: tuple[str, ...] = (),
        recovery_admissibility_findings: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystFreshnessSpecificationRecord:
        scope = ("Analytical Missions", "Analysis Plans", "Analytical Packages", "Evidence Packages", "Evidence Items", "Confidence Assessments", "Reasoning Graphs", "Competing Hypotheses", "Consensus Objects", "Contradiction Records", "Analytical Outputs", "Validation Records")
        states = ("Fresh", "Aging", "Expired", "Historical", "Replay Admissible", "Replay Restricted", "Permanently Valid")
        windows = ("creation time", "effective time", "freshness duration", "aging threshold", "expiration threshold", "replay eligibility period", "archival eligibility")
        invariants = ("Freshness never alters historical truth", "Expiration never deletes constitutional evidence", "Replay preserves original freshness", "Recovery respects mission validity", "Derived freshness is never less restrictive than source freshness", "Temporal evaluation is deterministic", "Freshness is independently auditable", "Freshness evaluation precedes analytical execution", "Permanently valid objects never expire", "Historical objects remain immutable")
        missing = tuple(item for item in scope if item in missing_scope)
        invalid = tuple(state for state in invalid_state_findings if state not in states)
        passed = not missing and not invalid and not implicit_window_findings and not temporal_nondeterminism_findings and not inheritance_violations and not replay_admissibility_findings and not recovery_admissibility_findings and not audit_gaps
        record = AnalystFreshnessSpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-009-FRESH-{_digest((scope, states))[:12].upper()}",
            freshness_scope=scope,
            freshness_states=states,
            window_fields=windows,
            invariants=invariants,
            missing_scope=missing,
            invalid_state_findings=invalid,
            implicit_window_findings=implicit_window_findings,
            temporal_nondeterminism_findings=temporal_nondeterminism_findings,
            inheritance_violations=inheritance_violations,
            replay_admissibility_findings=replay_admissibility_findings,
            recovery_admissibility_findings=recovery_admissibility_findings,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_organizational_belief_state_specification(
        self,
        *,
        missing_schema_fields: tuple[str, ...] = (),
        ownership_violations: tuple[str, ...] = (),
        unsupported_conclusion_findings: tuple[str, ...] = (),
        implicit_assumption_findings: tuple[str, ...] = (),
        hypothesis_preservation_findings: tuple[str, ...] = (),
        contradiction_preservation_findings: tuple[str, ...] = (),
        supersession_violations: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_mutation_findings: tuple[str, ...] = (),
    ) -> AnalystOrganizationalBeliefStateSpecificationRecord:
        schema = MappingProxyType(
            {
                "Identity": ("Belief State Identifier", "Belief Revision Identifier", "Constitutional Version", "Schema Version"),
                "Ownership": ("Owning Office", "Creating Authority", "Current Lifecycle State"),
                "Subject Definition": ("Subject Identifier", "Subject Type", "Subject Classification", "Analytical Scope"),
                "Belief Representation": ("Current Accepted Conclusion", "Supporting Findings", "Supporting Evidence References", "Confidence Assessment", "Confidence Classification", "Assumption References"),
                "Competing Analysis": ("Alternative Hypotheses", "Contradictory Findings", "Outstanding Questions", "Unresolved Uncertainty"),
                "Provenance": ("Mission Identifier", "Analysis Package References", "Reasoning Graph Reference", "Evidence References", "Validation References"),
                "Versioning": ("Previous Belief Version", "Supersession Reference", "Effective Timestamp", "Supersession Timestamp"),
                "Certification": ("Validation Status", "Certification Status", "Audit References"),
            }
        )
        identity = ("Belief State Identifier", "Belief Revision Identifier", "Constitutional Version", "Schema Version")
        representations = ("accepted conclusion", "confidence", "assumptions", "alternative hypotheses", "contradictions", "provenance", "versioning")
        persistent = ("identity", "accepted conclusion", "confidence", "assumptions", "hypotheses", "contradictions", "provenance", "validation history", "supersession history", "certification references")
        invariants = ("exactly one owner", "exactly one accepted conclusion", "conclusion derives from admissible evidence", "belief fully traceable", "confidence justified", "assumptions explicit", "hypotheses preserved", "contradictions never discarded", "belief immutable after acceptance", "revisions through supersession", "replay equivalent", "recovery preserves identical belief state", "audit history immutable")
        all_fields = tuple(field for fields_for_section in schema.values() for field in fields_for_section)
        missing = tuple(field for field in all_fields if field in missing_schema_fields)
        passed = not missing and not ownership_violations and not unsupported_conclusion_findings and not implicit_assumption_findings and not hypothesis_preservation_findings and not contradiction_preservation_findings and not supersession_violations and not replay_divergence_findings and not recovery_mutation_findings
        record = AnalystOrganizationalBeliefStateSpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-010-OBS-{_digest((schema, invariants))[:12].upper()}",
            schema_sections=schema,
            identity_fields=identity,
            required_representations=representations,
            persistent_state=persistent,
            invariants=invariants,
            missing_schema_fields=missing,
            ownership_violations=ownership_violations,
            unsupported_conclusion_findings=unsupported_conclusion_findings,
            implicit_assumption_findings=implicit_assumption_findings,
            hypothesis_preservation_findings=hypothesis_preservation_findings,
            contradiction_preservation_findings=contradiction_preservation_findings,
            supersession_violations=supersession_violations,
            replay_divergence_findings=replay_divergence_findings,
            recovery_mutation_findings=recovery_mutation_findings,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_rejection_taxonomy_specification(
        self,
        *,
        missing_classes: tuple[str, ...] = (),
        ambiguous_authority_findings: tuple[str, ...] = (),
        mutation_findings: tuple[str, ...] = (),
        lifecycle_violations: tuple[str, ...] = (),
        missing_audit_evidence: tuple[str, ...] = (),
        replay_inconsistencies: tuple[str, ...] = (),
        recovery_inconsistencies: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
    ) -> AnalystRejectionTaxonomySpecificationRecord:
        classes = MappingProxyType(
            {
                "AR-001 Identity Rejection": "Identity cannot be constitutionally established",
                "AR-002 Schema Rejection": "Object violates constitutional schema",
                "AR-003 Ownership Rejection": "Ownership cannot be constitutionally verified",
                "AR-004 Authority Rejection": "Execution authority invalid",
                "AR-005 Evidence Admissibility Rejection": "Evidence violates constitutional admissibility",
                "AR-006 Evidence Integrity Rejection": "Evidence integrity cannot be verified",
                "AR-007 Reasoning Rejection": "Reasoning violates constitutional doctrine",
                "AR-008 Confidence Rejection": "Confidence assessment constitutionally invalid",
                "AR-009 Lifecycle Rejection": "Illegal lifecycle behavior",
                "AR-010 Configuration Rejection": "Configuration constitutionally invalid",
                "AR-011 Validation Rejection": "Required constitutional validation failed",
                "AR-012 Traceability Rejection": "Complete provenance cannot be demonstrated",
                "AR-013 Persistence Rejection": "Required persistence obligations failed",
                "AR-014 Replay Rejection": "Replay semantic equivalence cannot be achieved",
                "AR-015 Constitutional Invariant Rejection": "One or more immutable constitutional invariants have been violated",
            }
        )
        fields_required = ("Rejection Identifier", "Object Identifier", "Object Type", "Rejection Class", "Constitutional Rule Violated", "Validation Results", "Triggering Evidence", "Timestamp", "Authority", "Replay Eligibility", "Recovery Eligibility", "Certification References")
        lifecycle = ("Under Evaluation", "Rejection Pending", "Rejected", "Audit Complete", "Archived")
        persistence = ("rejection classification", "rejection evidence", "violated constitutional rules", "validation reports", "provenance", "audit records")
        replay = ("rejection class", "rejection evidence", "violated rules", "rejection authority", "audit records")
        recovery = ("rejection status", "rejection evidence", "validation results", "audit records", "replay eligibility")
        invariants = ("ART-001 every rejected object has exactly one rejection class", "ART-002 rejection classifications are immutable", "ART-003 rejected objects never resume execution", "ART-004 every rejection preserves complete evidence", "ART-005 every rejection is independently auditable", "ART-006 replay reproduces identical rejection outcomes", "ART-007 recovery restores identical rejection state", "ART-008 every rejection references the violated constitutional rule", "ART-009 every rejection preserves provenance", "ART-010 constitutional invariant violations are always terminal")
        missing = tuple(item for item in classes if item in missing_classes)
        passed = not missing and not ambiguous_authority_findings and not mutation_findings and not lifecycle_violations and not missing_audit_evidence and not replay_inconsistencies and not recovery_inconsistencies and not traceability_gaps
        record = AnalystRejectionTaxonomySpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-011-REJECT-{_digest((classes, invariants))[:12].upper()}",
            rejection_classes=classes,
            rejection_record_fields=fields_required,
            rejection_lifecycle=lifecycle,
            persistence_obligations=persistence,
            replay_restoration_fields=replay,
            recovery_restoration_fields=recovery,
            invariants=invariants,
            missing_classes=missing,
            ambiguous_authority_findings=ambiguous_authority_findings,
            mutation_findings=mutation_findings,
            lifecycle_violations=lifecycle_violations,
            missing_audit_evidence=missing_audit_evidence,
            replay_inconsistencies=replay_inconsistencies,
            recovery_inconsistencies=recovery_inconsistencies,
            traceability_gaps=traceability_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_evidence_constitution_specification(
        self,
        *,
        missing_schema_fields: tuple[str, ...] = (),
        unapproved_class_findings: tuple[str, ...] = (),
        admissibility_failures: tuple[str, ...] = (),
        normalization_failures: tuple[str, ...] = (),
        orphaned_relationship_findings: tuple[str, ...] = (),
        persistence_gaps: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_mutation_findings: tuple[str, ...] = (),
    ) -> AnalystEvidenceConstitutionSpecificationRecord:
        schema = MappingProxyType(
            {
                "Constitutional Identity": ("Evidence Identifier", "Evidence Version", "Evidence Class", "Object Type Identifier", "Schema Version"),
                "Provenance": ("Originating Office", "Originating Object", "Originating Authority", "Acquisition Timestamp", "Acceptance Timestamp", "Chain of Custody Reference"),
                "Evidence Metadata": ("Evidence Category", "Evidence Source", "Observation Timestamp", "Effective Time", "Freshness Status", "Confidence of Acquisition", "Integrity Verification Status"),
                "Normalization": ("Canonical Representation", "Normalization Version", "Duplicate Status", "Equivalence References"),
                "Validation": ("Validation Status", "Validation Results", "Admissibility Status", "Validation Timestamp"),
                "Traceability": ("Analytical Mission Identifier", "Reasoning Graph References", "Hypothesis References", "Conclusion References", "Audit References"),
            }
        )
        classes = ("Candidate Evidence", "Observational Evidence", "Historical Evidence", "Quantitative Evidence", "Qualitative Evidence", "Derived Evidence", "Validation Evidence", "Contextual Evidence", "External Supporting Evidence")
        admissibility = ("ownership legitimacy", "provenance completeness", "schema compliance", "integrity verification", "normalization", "constitutional authority", "version compatibility")
        normalization = ("schema normalization", "identifier normalization", "unit normalization", "timestamp normalization", "reference normalization", "duplicate identification", "equivalence evaluation")
        relationships = ("originating Analytical Mission", "Analysis Plan", "Reasoning Graph", "competing hypotheses", "intermediate conclusions", "final conclusions", "validation records", "audit records")
        invariants = ("exactly one immutable identity", "exactly one constitutional owner", "immutable accepted contents", "complete provenance", "deterministic normalization", "deterministic validation", "deterministic admissibility", "deterministic persistence", "deterministic replay", "deterministic recovery", "complete traceability", "complete auditability")
        all_fields = tuple(field for section in schema.values() for field in section)
        missing = tuple(field for field in all_fields if field in missing_schema_fields)
        passed = not missing and not unapproved_class_findings and not admissibility_failures and not normalization_failures and not orphaned_relationship_findings and not persistence_gaps and not replay_divergence_findings and not recovery_mutation_findings
        record = AnalystEvidenceConstitutionSpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-012-EVID-{_digest((schema, classes))[:12].upper()}",
            schema_sections=schema,
            evidence_classes=classes,
            admissibility_rules=admissibility,
            normalization_steps=normalization,
            relationship_targets=relationships,
            invariants=invariants,
            missing_schema_fields=missing,
            unapproved_class_findings=unapproved_class_findings,
            admissibility_failures=admissibility_failures,
            normalization_failures=normalization_failures,
            orphaned_relationship_findings=orphaned_relationship_findings,
            persistence_gaps=persistence_gaps,
            replay_divergence_findings=replay_divergence_findings,
            recovery_mutation_findings=recovery_mutation_findings,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_provenance_architecture_specification(
        self,
        *,
        missing_scope: tuple[str, ...] = (),
        undocumented_source_findings: tuple[str, ...] = (),
        graph_cycle_findings: tuple[str, ...] = (),
        missing_chain_stages: tuple[str, ...] = (),
        validation_failures: tuple[str, ...] = (),
        persistence_gaps: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_gaps: tuple[str, ...] = (),
    ) -> AnalystProvenanceArchitectureSpecificationRecord:
        scope = ("Analytical Missions", "Analysis Plans", "Candidate Packages", "Evidence Objects", "Evidence Evaluations", "Reasoning Graphs", "Intermediate Conclusions", "Confidence Objects", "Hypothesis Objects", "Contradiction Objects", "Consensus Objects", "Analytical Packages", "Recommendations", "Validation Results", "Audit Records", "Certification Evidence")
        identity = ("Provenance Identifier", "Provenance Version", "Schema Version", "Constitutional Version", "Object Owner", "Originating Workflow Identifier", "Mission Identifier", "Creation Timestamp", "Integrity Metadata")
        sources = ("Candidate Packages", "Sentinel Observations", "Historical References", "Enterprise Belief State", "Configuration Objects", "Validation Results", "Replay Inputs", "Recovery Checkpoints")
        relationships = ("source relationships", "dependency relationships", "transformation relationships", "reasoning relationships", "validation relationships", "supersession relationships", "publication relationships")
        chain = ("Originating Analytical Mission", "Analysis Plan", "Input Objects", "Evidence Objects", "Validation Results", "Reasoning Graph Nodes", "Intermediate Conclusions", "Confidence Determination", "Contradiction Analysis", "Consensus Evaluation", "Final Conclusion", "Recommendation", "Publication", "Certification Evidence")
        nodes = ("node identifier", "object identifier", "object class", "owner", "lifecycle state", "version", "integrity metadata")
        edges = ("parent node", "child node", "dependency type", "relationship semantics", "creation timestamp")
        invariants = ("every constitutional output possesses complete provenance", "provenance graphs are acyclic", "provenance identifiers are immutable", "every transformation preserves lineage", "reasoning is completely traceable", "confidence possesses complete provenance", "recommendations possess complete provenance", "replay reproduces identical provenance", "recovery restores identical provenance", "implementation shall not influence provenance generation")
        missing_objects = tuple(item for item in scope if item in missing_scope)
        missing_stages = tuple(item for item in chain if item in missing_chain_stages)
        passed = not missing_objects and not undocumented_source_findings and not graph_cycle_findings and not missing_stages and not validation_failures and not persistence_gaps and not replay_divergence_findings and not recovery_gaps
        record = AnalystProvenanceArchitectureSpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-013-PROV-{_digest((scope, chain))[:12].upper()}",
            governed_object_scope=scope,
            identity_fields=identity,
            source_classes=sources,
            relationship_types=relationships,
            required_chain=chain,
            node_fields=nodes,
            edge_fields=edges,
            invariants=invariants,
            missing_scope=missing_objects,
            undocumented_source_findings=undocumented_source_findings,
            graph_cycle_findings=graph_cycle_findings,
            missing_chain_stages=missing_stages,
            validation_failures=validation_failures,
            persistence_gaps=persistence_gaps,
            replay_divergence_findings=replay_divergence_findings,
            recovery_gaps=recovery_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_office_state_machine_specification(
        self,
        *,
        missing_states: tuple[str, ...] = (),
        illegal_transition_findings: tuple[str, ...] = (),
        unauthorized_transition_findings: tuple[str, ...] = (),
        validation_failures: tuple[str, ...] = (),
        persistence_failures: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_violations: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystOfficeStateMachineSpecificationRecord:
        states = ("Created", "Pending Validation", "Validating", "Validated", "Pending Authorization", "Authorized", "Initializing", "Executing", "Awaiting Dependencies", "Performing Analysis", "Evaluating Hypotheses", "Computing Confidence", "Resolving Contradictions", "Producing Outputs", "Output Validation", "Ready for Delivery", "Completed", "Archived", "Replaying", "Recovering", "Failed", "Terminated")
        transitions = MappingProxyType(
            {
                "Created": ("Pending Validation",),
                "Pending Validation": ("Validating",),
                "Validating": ("Validated", "Failed"),
                "Validated": ("Pending Authorization",),
                "Pending Authorization": ("Authorized",),
                "Authorized": ("Initializing",),
                "Initializing": ("Executing",),
                "Executing": ("Awaiting Dependencies", "Performing Analysis", "Recovering", "Failed"),
                "Awaiting Dependencies": ("Performing Analysis", "Failed"),
                "Performing Analysis": ("Evaluating Hypotheses", "Failed"),
                "Evaluating Hypotheses": ("Computing Confidence", "Failed"),
                "Computing Confidence": ("Resolving Contradictions", "Failed"),
                "Resolving Contradictions": ("Producing Outputs", "Failed"),
                "Producing Outputs": ("Output Validation", "Failed"),
                "Output Validation": ("Ready for Delivery", "Failed"),
                "Ready for Delivery": ("Completed", "Failed"),
                "Completed": ("Archived",),
                "Archived": ("Terminated", "Replaying"),
                "Replaying": ("Terminated",),
                "Recovering": ("Executing", "Failed"),
                "Failed": ("Terminated",),
                "Terminated": (),
            }
        )
        special = MappingProxyType({"Archived": ("Replaying",), "Executing": ("Recovering",), "Any Active State": ("Failed",), "Failed": ("Terminated",)})
        prohibited = ("Created->Executing", "Pending Validation->Authorized", "Executing->Completed", "Completed->Executing", "Archived->Executing", "Failed->Executing", "Terminated->Any State", "Replay->Production Execution", "Recovery->Created")
        boundaries = ("Validation Complete", "Authorization Granted", "Execution Start", "Analysis Complete", "Output Complete", "Output Validation Complete", "Delivery Ready", "Completion", "Archival", "Replay Start", "Recovery Checkpoint", "Failure", "Termination")
        audit = ("execution identifier", "previous state", "new state", "transition timestamp", "transition authority", "validation result", "persistence checkpoint", "replay status", "recovery status")
        invariants = ("Exactly one execution state exists at any moment", "Every transition is deterministic", "Every transition is explicitly authorized", "Validation precedes execution", "Configuration becomes immutable after initialization", "Outputs are never delivered before validation", "Replay preserves execution semantics", "Recovery preserves committed state", "Failures terminate execution safely", "Terminated executions never restart", "Every transition is auditable", "State history is immutable")
        missing = tuple(state for state in states if state in missing_states)
        passed = not missing and not illegal_transition_findings and not unauthorized_transition_findings and not validation_failures and not persistence_failures and not replay_divergence_findings and not recovery_violations and not audit_gaps
        record = AnalystOfficeStateMachineSpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-014-STATE-{_digest((states, transitions))[:12].upper()}",
            execution_states=states,
            legal_transitions=transitions,
            special_transitions=special,
            prohibited_transitions=prohibited,
            persistence_boundaries=boundaries,
            audit_fields=audit,
            invariants=invariants,
            missing_states=missing,
            illegal_transition_findings=illegal_transition_findings,
            unauthorized_transition_findings=unauthorized_transition_findings,
            validation_failures=validation_failures,
            persistence_failures=persistence_failures,
            replay_divergence_findings=replay_divergence_findings,
            recovery_violations=recovery_violations,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_persistent_state_specification(
        self,
        *,
        missing_persistent_categories: tuple[str, ...] = (),
        missing_transient_categories: tuple[str, ...] = (),
        dual_classification_findings: tuple[str, ...] = (),
        implicit_persistence_findings: tuple[str, ...] = (),
        atomic_commit_failures: tuple[str, ...] = (),
        durability_failures: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_divergence_findings: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystPersistentStateSpecificationRecord:
        persistent = MappingProxyType(
            {
                "Mission State": ("Mission Identifier", "Mission Revision", "Authority", "Ownership", "Scope", "Objective", "Lifecycle State"),
                "Planning State": ("Analysis Plan", "execution constraints", "dependency ordering", "completion criteria", "scheduling metadata"),
                "Evidence State": ("Evidence Identifiers", "Provenance", "Admissibility", "Normalization", "Validation", "Freshness", "Integrity"),
                "Reasoning State": ("Reasoning Graph", "Inference Nodes", "Dependency Graph", "Reasoning Relationships", "Supporting Logic"),
                "Assumption State": ("Assumption Registry", "Validation Status", "Justification", "Dependency References"),
                "Hypothesis State": ("Accepted Hypothesis", "Rejected Hypotheses", "Alternative Hypotheses", "Comparison History"),
                "Contradiction State": ("Contradiction Registry", "Conflict Relationships", "Resolution Status", "Outstanding Contradictions"),
                "Confidence State": ("Confidence Values", "Confidence Derivation", "Probability Objects", "Uncertainty Metadata"),
                "Belief State": ("Organizational Belief State", "Version History", "Supersession Chain", "Supporting Findings"),
                "Recommendation State": ("Recommendation Objects", "Supporting Findings", "Delivery Status", "Acceptance Status"),
                "Validation State": ("Validation Results", "Validation History", "Rejection Records", "Invariant Verification"),
                "Lifecycle State": ("Current Lifecycle", "Transition History", "Supersession History", "Authority Changes"),
                "Configuration State": ("Configuration Object", "Configuration Version", "Constitutional Version", "Compatibility Metadata"),
                "Audit State": ("Audit Records", "Certification History", "Persistence History", "Replay History", "Recovery History"),
            }
        )
        transient = MappingProxyType(
            {
                "Runtime Execution Context": ("thread identifiers", "execution handles", "scheduler allocations", "runtime pointers"),
                "Temporary Memory Structures": ("caches", "temporary indexes", "lookup tables", "temporary queues"),
                "Performance Optimizations": ("memoization caches", "execution pipelines", "optimization buffers", "implementation-specific acceleration structures"),
                "Temporary Validation Workspace": ("intermediate calculations", "temporary comparisons", "provisional sorting", "temporary ranking"),
            }
        )
        rules = MappingProxyType(
            {
                "Constitutional Identity": "Persistent",
                "Constitutional Ownership": "Persistent",
                "Constitutional Evidence": "Persistent",
                "Constitutional Reasoning": "Persistent",
                "Lifecycle Status": "Persistent",
                "Configuration": "Persistent",
                "Runtime Memory": "Transient",
                "Scheduler State": "Transient",
                "Cache Structures": "Transient",
                "Optimization Structures": "Transient",
            }
        )
        lifecycle = ("Created", "Validated", "Prepared", "Atomically Committed", "Integrity Verified", "Immutable", "Archived", "Certified")
        durability = ("process termination", "operating system restart", "application restart", "replay", "recovery", "disaster recovery", "certification replay")
        replay = ("identical persistent identities", "equivalent analytical state", "identical reasoning relationships", "equivalent belief states", "identical lifecycle status", "equivalent recommendations")
        recovery = ("committed constitutional state", "lifecycle state", "reasoning graph", "evidence relationships", "validation state", "configuration", "audit history")
        invariants = ("every state element possesses exactly one persistence classification", "every persistent object possesses one constitutional owner", "committed constitutional state is immutable", "transient state possesses no constitutional meaning", "replay restores only committed constitutional state", "recovery restores only committed constitutional state", "persistent state survives interruption", "historical revisions are never modified", "persistence is deterministic", "persistence remains completely auditable")
        missing_persistent = tuple(category for category in persistent if category in missing_persistent_categories)
        missing_transient = tuple(category for category in transient if category in missing_transient_categories)
        passed = not missing_persistent and not missing_transient and not dual_classification_findings and not implicit_persistence_findings and not atomic_commit_failures and not durability_failures and not replay_divergence_findings and not recovery_divergence_findings and not audit_gaps
        record = AnalystPersistentStateSpecificationRecord(
            specification_identifier=f"ANALYST-RM-003-015-PERSIST-{_digest((persistent, transient))[:12].upper()}",
            persistent_inventory=persistent,
            transient_inventory=transient,
            classification_rules=rules,
            persistence_lifecycle=lifecycle,
            durability_events=durability,
            replay_restoration_fields=replay,
            recovery_restoration_fields=recovery,
            invariants=invariants,
            missing_persistent_categories=missing_persistent,
            missing_transient_categories=missing_transient,
            dual_classification_findings=dual_classification_findings,
            implicit_persistence_findings=implicit_persistence_findings,
            atomic_commit_failures=atomic_commit_failures,
            durability_failures=durability_failures,
            replay_divergence_findings=replay_divergence_findings,
            recovery_divergence_findings=recovery_divergence_findings,
            audit_gaps=audit_gaps,
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
