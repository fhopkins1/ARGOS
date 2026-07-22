"""ANALYST-RM-004 independent certification registry support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


@dataclass(frozen=True)
class AnalystRm004CandidateClassEntry:
    candidate_class_identifier: str
    canonical_name: str
    candidate_category: str
    constitutional_owner: str
    certification_scope: tuple[str, ...]
    applicable_work_orders: tuple[str, ...]
    required_evidence: tuple[str, ...]
    evaluation_rule_set: tuple[str, ...]
    certification_dependencies: tuple[str, ...]
    required_schemas: tuple[str, ...]
    required_registries: tuple[str, ...]
    certification_status: str
    version: str
    audit_references: tuple[str, ...]


@dataclass(frozen=True)
class AnalystRm004CandidateClassRegistryRecord:
    registry_identifier: str
    entries: tuple[AnalystRm004CandidateClassEntry, ...]
    category_definitions: Mapping[str, str]
    certification_applicability_rules: tuple[str, ...]
    duplicate_identifier_findings: tuple[str, ...]
    multiple_classification_findings: tuple[str, ...]
    missing_owner_findings: tuple[str, ...]
    incomplete_applicability_findings: tuple[str, ...]
    dependency_graph_findings: tuple[str, ...]
    invalid_schema_reference_findings: tuple[str, ...]
    replay_inconsistency_findings: tuple[str, ...]
    invariant_violations: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004IdentityNormalizationRecord:
    registry_identifier: str
    identity_scope: tuple[str, ...]
    table_sections: Mapping[str, tuple[str, ...]]
    normalization_rules: tuple[str, ...]
    namespaces: tuple[str, ...]
    equivalence_rules: tuple[str, ...]
    invariants: tuple[str, ...]
    duplicate_canonical_identity_findings: tuple[str, ...]
    ambiguous_alias_findings: tuple[str, ...]
    namespace_reuse_findings: tuple[str, ...]
    normalization_drift_findings: tuple[str, ...]
    equivalence_rule_findings: tuple[str, ...]
    traceability_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004EvaluationRuleEntry:
    rule_identifier: str
    rule_version: str
    rule_name: str
    rule_classification: str
    evaluation_scope: tuple[str, ...]
    required_inputs: tuple[str, ...]
    evaluation_procedure: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    failure_classification: str
    dependencies: tuple[str, ...]
    audit_requirements: tuple[str, ...]


@dataclass(frozen=True)
class AnalystRm004EvaluationRuleRegistryRecord:
    registry_identifier: str
    entries: tuple[AnalystRm004EvaluationRuleEntry, ...]
    evaluation_ordering: tuple[str, ...]
    rule_classifications: tuple[str, ...]
    duplicate_rule_findings: tuple[str, ...]
    missing_rule_findings: tuple[str, ...]
    invalid_outcome_findings: tuple[str, ...]
    dependency_cycle_findings: tuple[str, ...]
    registry_ambiguity_findings: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004CertificationThresholdRecord:
    registry_identifier: str
    threshold_classes: tuple[str, ...]
    threshold_outcomes: tuple[str, ...]
    threshold_registry_fields: tuple[str, ...]
    acceptance_standards: tuple[str, ...]
    failure_standards: tuple[str, ...]
    invariants: tuple[str, ...]
    missing_threshold_classes: tuple[str, ...]
    invalid_outcome_findings: tuple[str, ...]
    weak_mandatory_threshold_findings: tuple[str, ...]
    blocking_threshold_bypass_findings: tuple[str, ...]
    traceability_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004CertificationTestEntry:
    certification_test_identifier: str
    test_category: str
    constitutional_requirement: str
    governing_work_order: str
    required_inputs: tuple[str, ...]
    expected_constitutional_outcome: str
    required_evidence: tuple[str, ...]
    pass_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class AnalystRm004CertificationTestRegistryRecord:
    registry_identifier: str
    entries: tuple[AnalystRm004CertificationTestEntry, ...]
    canonical_categories: Mapping[str, tuple[str, ...]]
    execution_prerequisites: tuple[str, ...]
    duplicate_test_findings: tuple[str, ...]
    missing_category_findings: tuple[str, ...]
    missing_requirement_coverage: tuple[str, ...]
    nondeterministic_execution_findings: tuple[str, ...]
    missing_evidence_findings: tuple[str, ...]
    dependency_cycle_findings: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004CertificationFoundationEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    candidate_class_registry: AnalystRm004CandidateClassRegistryRecord
    identity_normalization: AnalystRm004IdentityNormalizationRecord
    evaluation_rule_registry: AnalystRm004EvaluationRuleRegistryRecord
    certification_thresholds: AnalystRm004CertificationThresholdRecord
    certification_test_registry: AnalystRm004CertificationTestRegistryRecord
    final_foundation_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004IdentityCollisionResolutionRecord:
    registry_identifier: str
    collision_classes: Mapping[str, tuple[str, str]]
    detection_procedure: tuple[str, ...]
    resolution_record_fields: tuple[str, ...]
    registry_updates: tuple[str, ...]
    invariants: tuple[str, ...]
    duplicate_identifier_findings: tuple[str, ...]
    conflicting_ownership_findings: tuple[str, ...]
    unresolved_collision_findings: tuple[str, ...]
    namespace_allocation_findings: tuple[str, ...]
    replay_identity_findings: tuple[str, ...]
    recovery_identity_findings: tuple[str, ...]
    traceability_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004MetricRegistryEntry:
    metric_identifier: str
    metric_name: str
    metric_class: str
    constitutional_owner: str
    calculation_rule_identifier: str
    input_objects: tuple[str, ...]
    validation_rules: tuple[str, ...]
    dependency_references: tuple[str, ...]


@dataclass(frozen=True)
class AnalystRm004MetricsRegistryRecord:
    registry_identifier: str
    entries: tuple[AnalystRm004MetricRegistryEntry, ...]
    metric_classes: tuple[str, ...]
    calculation_requirements: tuple[str, ...]
    invariants: tuple[str, ...]
    duplicate_metric_findings: tuple[str, ...]
    missing_metric_class_findings: tuple[str, ...]
    ownership_findings: tuple[str, ...]
    inadmissible_input_findings: tuple[str, ...]
    dependency_cycle_findings: tuple[str, ...]
    reproducibility_findings: tuple[str, ...]
    traceability_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004CertificationManifestSchemaRecord:
    registry_identifier: str
    identity_fields: tuple[str, ...]
    schema_sections: Mapping[str, tuple[str, ...]]
    mandatory_artifacts: tuple[str, ...]
    outcome_values: tuple[str, ...]
    invariants: tuple[str, ...]
    missing_schema_sections: tuple[str, ...]
    missing_artifact_findings: tuple[str, ...]
    evidence_linkage_findings: tuple[str, ...]
    compatibility_findings: tuple[str, ...]
    validation_failures: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004IdentifierNamespaceEntry:
    namespace: str
    purpose: str
    constitutional_owner: str
    allocation_authority: str
    lifecycle_authority: str
    reserved_ranges: tuple[str, ...]


@dataclass(frozen=True)
class AnalystRm004IdentifierRegistryRecord:
    registry_identifier: str
    namespaces: tuple[AnalystRm004IdentifierNamespaceEntry, ...]
    identifier_structure: tuple[str, ...]
    allocation_rules: tuple[str, ...]
    lifecycle_states: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    invariants: tuple[str, ...]
    duplicate_namespace_findings: tuple[str, ...]
    missing_namespace_findings: tuple[str, ...]
    allocation_findings: tuple[str, ...]
    uniqueness_findings: tuple[str, ...]
    replay_identifier_findings: tuple[str, ...]
    recovery_identifier_findings: tuple[str, ...]
    traceability_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004VersionCompatibilityRecord:
    registry_identifier: str
    version_classes: tuple[str, ...]
    compatibility_matrix: Mapping[str, tuple[str, str]]
    evaluation_sequence: tuple[str, ...]
    prohibited_combinations: tuple[str, ...]
    invariants: tuple[str, ...]
    missing_compatibility_entries: tuple[str, ...]
    unknown_compatibility_findings: tuple[str, ...]
    incompatible_artifact_findings: tuple[str, ...]
    supersession_findings: tuple[str, ...]
    replay_divergence_findings: tuple[str, ...]
    recovery_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004RegistryGovernanceEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    identity_collision_resolution: AnalystRm004IdentityCollisionResolutionRecord
    metrics_registry: AnalystRm004MetricsRegistryRecord
    certification_manifest_schema: AnalystRm004CertificationManifestSchemaRecord
    identifier_registry: AnalystRm004IdentifierRegistryRecord
    version_compatibility_matrix: AnalystRm004VersionCompatibilityRecord
    final_registry_governance_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004ConstitutionalRuleEntry:
    rule_identifier: str
    rule_name: str
    rule_category: str
    constitutional_owner: str
    evaluation_intent: str
    evaluation_procedure_reference: str
    dependency_references: tuple[str, ...]
    applicable_candidate_classes: tuple[str, ...]
    required_evidence: tuple[str, ...]
    certification_severity: str
    version: str
    publication_status: str
    traceability_references: tuple[str, ...]
    audit_references: tuple[str, ...]


@dataclass(frozen=True)
class AnalystRm004ConstitutionalRuleRegistryRecord:
    registry_identifier: str
    entries: tuple[AnalystRm004ConstitutionalRuleEntry, ...]
    registry_fields: tuple[str, ...]
    rule_categories: tuple[str, ...]
    severity_levels: tuple[str, ...]
    dependency_requirements: tuple[str, ...]
    invariants: tuple[str, ...]
    duplicate_rule_findings: tuple[str, ...]
    ambiguous_ownership_findings: tuple[str, ...]
    missing_dependency_findings: tuple[str, ...]
    invalid_applicability_findings: tuple[str, ...]
    traceability_gaps: tuple[str, ...]
    replay_recovery_findings: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    invariant_violations: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004SchemaRegistryEntry:
    schema_identifier: str
    schema_name: str
    schema_version: str
    schema_class: str
    canonical_namespace: str
    constitutional_owner: str
    approval_authority: str
    certification_authority: str
    parent_schema: str | None
    compatible_schemas: tuple[str, ...]
    dependent_schemas: tuple[str, ...]
    referenced_registries: tuple[str, ...]
    certification_status: str
    validation_status: str
    effective_version: str
    deprecation_status: str


@dataclass(frozen=True)
class AnalystRm004SchemaRegistryRecord:
    registry_identifier: str
    entries: tuple[AnalystRm004SchemaRegistryEntry, ...]
    schema_identity_fields: tuple[str, ...]
    schema_classes: Mapping[str, tuple[str, ...]]
    lifecycle_states: tuple[str, ...]
    duplicate_schema_findings: tuple[str, ...]
    missing_schema_class_findings: tuple[str, ...]
    ownership_findings: tuple[str, ...]
    compatibility_gaps: tuple[str, ...]
    relationship_cycle_findings: tuple[str, ...]
    validation_failures: tuple[str, ...]
    replay_recovery_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004RegistryCrossReferenceRecord:
    matrix_identifier: str
    matrix_version: str
    constitutional_version: str
    schema_version: str
    registry_version: str
    owner: str
    integrity_metadata: str
    registry_inventory: tuple[str, ...]
    matrix_sections: Mapping[str, tuple[str, ...]]
    relationship_types: tuple[str, ...]
    invariants: tuple[str, ...]
    duplicate_registry_findings: tuple[str, ...]
    missing_registry_findings: tuple[str, ...]
    illegal_relationship_findings: tuple[str, ...]
    broken_reference_findings: tuple[str, ...]
    dependency_cycle_findings: tuple[str, ...]
    compatibility_gaps: tuple[str, ...]
    replay_recovery_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004CertificationEvidenceRegistryRecord:
    registry_identifier: str
    evidence_classes: tuple[str, ...]
    identity_fields: tuple[str, ...]
    lifecycle_states: tuple[str, ...]
    registry_fields: tuple[str, ...]
    admissibility_requirements: tuple[str, ...]
    duplicate_evidence_findings: tuple[str, ...]
    missing_class_findings: tuple[str, ...]
    ownership_findings: tuple[str, ...]
    inadmissible_evidence_findings: tuple[str, ...]
    integrity_failures: tuple[str, ...]
    provenance_gaps: tuple[str, ...]
    traceability_gaps: tuple[str, ...]
    replay_recovery_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004DecisionRegistryEntry:
    decision_identifier: str
    decision_revision_identifier: str
    decision_name: str
    decision_category: str
    owning_office: str
    decision_authority: str
    evaluation_authority: str
    governing_work_order: str
    constitutional_requirement: str
    trigger_conditions: tuple[str, ...]
    required_inputs: tuple[str, ...]
    required_evidence: tuple[str, ...]
    required_dependencies: tuple[str, ...]
    evaluation_rules: tuple[str, ...]
    required_validation: tuple[str, ...]
    required_invariants: tuple[str, ...]
    expected_result: str
    outcomes: tuple[str, ...]
    traceability_references: tuple[str, ...]


@dataclass(frozen=True)
class AnalystRm004DecisionRegistryRecord:
    registry_identifier: str
    entries: tuple[AnalystRm004DecisionRegistryEntry, ...]
    decision_object_fields: tuple[str, ...]
    decision_categories: tuple[str, ...]
    evaluation_sequence: tuple[str, ...]
    outcome_values: tuple[str, ...]
    duplicate_decision_findings: tuple[str, ...]
    missing_category_findings: tuple[str, ...]
    invalid_outcome_findings: tuple[str, ...]
    authority_findings: tuple[str, ...]
    evidence_gaps: tuple[str, ...]
    dependency_cycle_findings: tuple[str, ...]
    traceability_gaps: tuple[str, ...]
    replay_recovery_gaps: tuple[str, ...]
    audit_gaps: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class AnalystRm004GovernanceRegistryEvidencePackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    constitutional_rule_registry: AnalystRm004ConstitutionalRuleRegistryRecord
    schema_registry: AnalystRm004SchemaRegistryRecord
    registry_cross_reference_matrix: AnalystRm004RegistryCrossReferenceRecord
    certification_evidence_registry: AnalystRm004CertificationEvidenceRegistryRecord
    decision_registry: AnalystRm004DecisionRegistryRecord
    final_governance_registry_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


class AnalystOfficeCertificationSupport:
    """Build deterministic ANALYST-RM-004 certification registry evidence."""

    order_coverage = (
        "ANALYST-RM-004-001",
        "ANALYST-RM-004-002",
        "ANALYST-RM-004-003",
        "ANALYST-RM-004-004",
        "ANALYST-RM-004-005",
    )

    registry_governance_order_coverage = (
        "ANALYST-RM-004-006",
        "ANALYST-RM-004-007",
        "ANALYST-RM-004-008",
        "ANALYST-RM-004-009",
        "ANALYST-RM-004-010",
    )

    governance_registry_order_coverage = (
        "ANALYST-RM-004-011",
        "ANALYST-RM-004-012",
        "ANALYST-RM-004-013",
        "ANALYST-RM-004-014",
        "ANALYST-RM-004-015",
    )

    def build_foundation_package(self) -> AnalystRm004CertificationFoundationEvidencePackage:
        candidates = self.evaluate_candidate_class_registry()
        identity = self.evaluate_identity_normalization()
        rules = self.evaluate_evaluation_rule_registry()
        thresholds = self.evaluate_certification_thresholds()
        tests = self.evaluate_certification_test_registry()
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (candidates, identity, rules, thresholds, tests)
        ) else EnterpriseCertificationDecision.FAIL
        package = AnalystRm004CertificationFoundationEvidencePackage(
            package_identifier=f"ANALYST-RM-004-FOUNDATION-{_digest((candidates, identity, rules, thresholds, tests))[:12].upper()}",
            governing_doctrine="ANALYST-RM-004-001-TO-005/1.0.0",
            order_coverage=self.order_coverage,
            candidate_class_registry=candidates,
            identity_normalization=identity,
            evaluation_rule_registry=rules,
            certification_thresholds=thresholds,
            certification_test_registry=tests,
            final_foundation_readiness=final,
            immutable_audit_references=(
                candidates.registry_identifier,
                identity.registry_identifier,
                rules.registry_identifier,
                thresholds.registry_identifier,
                tests.registry_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def build_registry_governance_package(self) -> AnalystRm004RegistryGovernanceEvidencePackage:
        collisions = self.evaluate_identity_collision_resolution()
        metrics = self.evaluate_metrics_registry()
        manifest = self.evaluate_certification_manifest_schema()
        identifiers = self.evaluate_identifier_registry()
        versions = self.evaluate_version_compatibility_matrix()
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (collisions, metrics, manifest, identifiers, versions)
        ) else EnterpriseCertificationDecision.FAIL
        package = AnalystRm004RegistryGovernanceEvidencePackage(
            package_identifier=f"ANALYST-RM-004-REGISTRY-GOV-{_digest((collisions, metrics, manifest, identifiers, versions))[:12].upper()}",
            governing_doctrine="ANALYST-RM-004-006-TO-010/1.0.0",
            order_coverage=self.registry_governance_order_coverage,
            identity_collision_resolution=collisions,
            metrics_registry=metrics,
            certification_manifest_schema=manifest,
            identifier_registry=identifiers,
            version_compatibility_matrix=versions,
            final_registry_governance_readiness=final,
            immutable_audit_references=(
                collisions.registry_identifier,
                metrics.registry_identifier,
                manifest.registry_identifier,
                identifiers.registry_identifier,
                versions.registry_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def build_governance_registry_package(self) -> AnalystRm004GovernanceRegistryEvidencePackage:
        rules = self.evaluate_constitutional_rule_registry()
        schemas = self.evaluate_schema_registry()
        cross_refs = self.evaluate_registry_cross_reference_matrix()
        evidence = self.evaluate_certification_evidence_registry()
        decisions = self.evaluate_decision_registry()
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (rules, schemas, cross_refs, evidence, decisions)
        ) else EnterpriseCertificationDecision.FAIL
        package = AnalystRm004GovernanceRegistryEvidencePackage(
            package_identifier=f"ANALYST-RM-004-GOV-REG-{_digest((rules, schemas, cross_refs, evidence, decisions))[:12].upper()}",
            governing_doctrine="ANALYST-RM-004-011-TO-015/1.0.0",
            order_coverage=self.governance_registry_order_coverage,
            constitutional_rule_registry=rules,
            schema_registry=schemas,
            registry_cross_reference_matrix=cross_refs,
            certification_evidence_registry=evidence,
            decision_registry=decisions,
            final_governance_registry_readiness=final,
            immutable_audit_references=(
                rules.registry_identifier,
                schemas.registry_identifier,
                cross_refs.matrix_identifier,
                evidence.registry_identifier,
                decisions.registry_identifier,
            ),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_candidate_class_registry(
        self,
        *,
        duplicate_identifier_findings: tuple[str, ...] = (),
        multiple_classification_findings: tuple[str, ...] = (),
        missing_owner_findings: tuple[str, ...] = (),
        incomplete_applicability_findings: tuple[str, ...] = (),
        dependency_graph_findings: tuple[str, ...] = (),
        invalid_schema_reference_findings: tuple[str, ...] = (),
        replay_inconsistency_findings: tuple[str, ...] = (),
        invariant_violations: tuple[str, ...] = (),
    ) -> AnalystRm004CandidateClassRegistryRecord:
        entries = self._candidate_class_entries()
        categories = MappingProxyType(
            {
                "Mission Object": "Governs analytical authority and execution",
                "Execution Object": "Governs operational execution",
                "Operational Object": "Represents analytical work products",
                "Reasoning Object": "Represents logical evaluation artifacts",
                "Evidence Object": "Represents constitutional evidence",
                "Analytical Object": "Represents analytical conclusions and confidence",
                "Decision Object": "Represents analytical conclusions",
                "Certification Evidence": "Represents validation and certification records",
                "Configuration Object": "Represents immutable operational configuration",
                "Persistence Object": "Represents durable constitutional state",
                "Replay Object": "Represents replay verification artifacts",
                "Recovery Object": "Represents recovery verification artifacts",
                "Certification Object": "Represents certification evidence and artifacts",
                "Audit Object": "Represents audit and traceability records",
            }
        )
        applicability = ("certification mandatory", "certification procedures explicit", "validation framework required", "replay required", "recovery required", "audit required")
        ids = tuple(entry.candidate_class_identifier for entry in entries)
        duplicate_ids = tuple(identifier for identifier in sorted(set(ids)) if ids.count(identifier) > 1)
        missing_owner = tuple(entry.candidate_class_identifier for entry in entries if entry.constitutional_owner != "Analyst Office")
        passed = not duplicate_ids and not duplicate_identifier_findings and not multiple_classification_findings and not missing_owner and not missing_owner_findings and not incomplete_applicability_findings and not dependency_graph_findings and not invalid_schema_reference_findings and not replay_inconsistency_findings and not invariant_violations
        record = AnalystRm004CandidateClassRegistryRecord(
            registry_identifier=f"ANALYST-RM-004-001-CCR-{_digest(entries)[:12].upper()}",
            entries=entries,
            category_definitions=categories,
            certification_applicability_rules=applicability,
            duplicate_identifier_findings=duplicate_ids + duplicate_identifier_findings,
            multiple_classification_findings=multiple_classification_findings,
            missing_owner_findings=missing_owner + missing_owner_findings,
            incomplete_applicability_findings=incomplete_applicability_findings,
            dependency_graph_findings=dependency_graph_findings,
            invalid_schema_reference_findings=invalid_schema_reference_findings,
            replay_inconsistency_findings=replay_inconsistency_findings,
            invariant_violations=invariant_violations,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_identity_normalization(
        self,
        *,
        duplicate_canonical_identity_findings: tuple[str, ...] = (),
        ambiguous_alias_findings: tuple[str, ...] = (),
        namespace_reuse_findings: tuple[str, ...] = (),
        normalization_drift_findings: tuple[str, ...] = (),
        equivalence_rule_findings: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004IdentityNormalizationRecord:
        scope = ("Analytical Missions", "Analysis Plans", "Analytical Packages", "Analytical Evidence", "Reasoning Graphs", "Reasoning Nodes", "Confidence Objects", "Competing Hypotheses", "Validation Records", "Decision Records", "Analytical Conclusions", "Analytical Outputs", "Audit Records", "Traceability Records", "Configuration Objects", "Certification Artifacts")
        sections = MappingProxyType(
            {
                "Identity Information": ("Canonical Identifier", "Object Type", "Object Class", "Namespace", "Version"),
                "Historical Identity": ("Previous Identifiers", "Historical Aliases", "Deprecated Names", "Legacy References"),
                "Normalization": ("Canonical Name", "Canonical Case", "Canonical Formatting", "Canonical Namespace", "Normalization Rule Version"),
                "Certification Metadata": ("Certification Status", "Validation Status", "Schema Version", "Traceability Reference"),
            }
        )
        rules = ("case normalization", "whitespace normalization", "namespace normalization", "separator normalization", "version normalization", "identifier formatting", "reserved token handling", "alias resolution")
        namespaces = ("Mission Namespace", "Evidence Namespace", "Reasoning Namespace", "Hypothesis Namespace", "Confidence Namespace", "Validation Namespace", "Output Namespace", "Configuration Namespace", "Certification Namespace")
        equivalence = ("same canonical identifier", "identical normalized identity", "object class matches", "namespace matches", "version compatibility permits equivalence")
        invariants = ("exactly one canonical identifier", "immutable identity", "deterministic normalization", "deterministic equivalence", "unique namespace membership", "complete traceability", "complete auditability", "complete version compatibility")
        passed = not duplicate_canonical_identity_findings and not ambiguous_alias_findings and not namespace_reuse_findings and not normalization_drift_findings and not equivalence_rule_findings and not traceability_gaps and not audit_gaps
        record = AnalystRm004IdentityNormalizationRecord(
            registry_identifier=f"ANALYST-RM-004-002-IDN-{_digest((scope, sections, rules))[:12].upper()}",
            identity_scope=scope,
            table_sections=sections,
            normalization_rules=rules,
            namespaces=namespaces,
            equivalence_rules=equivalence,
            invariants=invariants,
            duplicate_canonical_identity_findings=duplicate_canonical_identity_findings,
            ambiguous_alias_findings=ambiguous_alias_findings,
            namespace_reuse_findings=namespace_reuse_findings,
            normalization_drift_findings=normalization_drift_findings,
            equivalence_rule_findings=equivalence_rule_findings,
            traceability_gaps=traceability_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_evaluation_rule_registry(
        self,
        *,
        duplicate_rule_findings: tuple[str, ...] = (),
        missing_rule_findings: tuple[str, ...] = (),
        invalid_outcome_findings: tuple[str, ...] = (),
        dependency_cycle_findings: tuple[str, ...] = (),
        registry_ambiguity_findings: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004EvaluationRuleRegistryRecord:
        entries = self._evaluation_rule_entries()
        ordering = ("Identity", "Ownership", "Schema", "Configuration", "Lifecycle", "Evidence", "Provenance", "Reasoning", "Confidence", "Hypotheses", "Persistence", "Replay", "Recovery", "Audit", "Certification Package", "Certification Closure")
        classifications = tuple(entry.rule_classification for entry in entries)
        ids = tuple(entry.rule_identifier for entry in entries)
        duplicate_ids = tuple(identifier for identifier in sorted(set(ids)) if ids.count(identifier) > 1)
        bad_outcomes = tuple(entry.rule_identifier for entry in entries if entry.expected_outcomes != ("Pass", "Fail", "Not Applicable"))
        passed = not duplicate_ids and not bad_outcomes and not duplicate_rule_findings and not missing_rule_findings and not invalid_outcome_findings and not dependency_cycle_findings and not registry_ambiguity_findings and not replay_divergence_findings and not recovery_gaps and not audit_gaps
        record = AnalystRm004EvaluationRuleRegistryRecord(
            registry_identifier=f"ANALYST-RM-004-003-RULE-{_digest(entries)[:12].upper()}",
            entries=entries,
            evaluation_ordering=ordering,
            rule_classifications=classifications,
            duplicate_rule_findings=duplicate_ids + duplicate_rule_findings,
            missing_rule_findings=missing_rule_findings,
            invalid_outcome_findings=bad_outcomes + invalid_outcome_findings,
            dependency_cycle_findings=dependency_cycle_findings,
            registry_ambiguity_findings=registry_ambiguity_findings,
            replay_divergence_findings=replay_divergence_findings,
            recovery_gaps=recovery_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_certification_thresholds(
        self,
        *,
        missing_threshold_classes: tuple[str, ...] = (),
        invalid_outcome_findings: tuple[str, ...] = (),
        weak_mandatory_threshold_findings: tuple[str, ...] = (),
        blocking_threshold_bypass_findings: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004CertificationThresholdRecord:
        classes = ("Mandatory Threshold", "Conditional Threshold", "Quantitative Threshold", "Qualitative Threshold", "Compatibility Threshold", "Integrity Threshold", "Completeness Threshold", "Evidence Threshold", "Traceability Threshold", "Certification Blocking Threshold")
        outcomes = ("Pass", "Fail", "Not Applicable", "Deferred")
        fields_required = ("Threshold Identifier", "Threshold Class", "Governing Doctrine", "Evaluation Rule Identifier", "Required Evidence", "Required Metrics", "Pass Condition", "Failure Condition", "Audit Requirements", "Certification Impact")
        acceptance = ("every mandatory threshold passes", "every certification-blocking threshold passes", "complete constitutional evidence exists", "deterministic replay succeeds", "deterministic recovery succeeds", "validation succeeds", "traceability is complete", "audit evidence is complete", "no unresolved constitutional findings remain")
        failures = ("failed certification-blocking threshold", "failed mandatory threshold", "missing evidence", "replay divergence", "recovery divergence", "validation failure", "traceability failure", "audit incompleteness", "unresolved constitutional finding")
        invariants = ("single constitutional owner", "immutable threshold definition", "deterministic threshold evaluation", "mandatory thresholds admit no discretion", "certification-blocking thresholds immediately fail certification", "reproducible threshold evidence", "complete threshold traceability", "immutable threshold audit history", "identical evidence produces identical outcome", "implementation independence")
        missing = tuple(item for item in classes if item in missing_threshold_classes)
        passed = not missing and not invalid_outcome_findings and not weak_mandatory_threshold_findings and not blocking_threshold_bypass_findings and not traceability_gaps and not audit_gaps
        record = AnalystRm004CertificationThresholdRecord(
            registry_identifier=f"ANALYST-RM-004-004-THRESH-{_digest((classes, acceptance))[:12].upper()}",
            threshold_classes=classes,
            threshold_outcomes=outcomes,
            threshold_registry_fields=fields_required,
            acceptance_standards=acceptance,
            failure_standards=failures,
            invariants=invariants,
            missing_threshold_classes=missing,
            invalid_outcome_findings=invalid_outcome_findings,
            weak_mandatory_threshold_findings=weak_mandatory_threshold_findings,
            blocking_threshold_bypass_findings=blocking_threshold_bypass_findings,
            traceability_gaps=traceability_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_certification_test_registry(
        self,
        *,
        duplicate_test_findings: tuple[str, ...] = (),
        missing_category_findings: tuple[str, ...] = (),
        missing_requirement_coverage: tuple[str, ...] = (),
        nondeterministic_execution_findings: tuple[str, ...] = (),
        missing_evidence_findings: tuple[str, ...] = (),
        dependency_cycle_findings: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004CertificationTestRegistryRecord:
        entries = self._certification_test_entries()
        categories = MappingProxyType(
            {
                "Category A Authority Certification": ("ownership", "authority", "constitutional boundaries"),
                "Category B Identity Certification": ("identifier uniqueness", "revision correctness", "normalization", "canonical identity"),
                "Category C Object Certification": ("schema compliance", "object integrity", "ownership", "lifecycle"),
                "Category D Reasoning Certification": ("inference correctness", "reasoning determinism", "dependency integrity", "contradiction preservation"),
                "Category E Evidence Certification": ("admissibility", "provenance", "normalization", "preservation"),
                "Category F Confidence Certification": ("confidence derivation", "uncertainty handling", "probability consistency"),
                "Category G Validation Certification": ("constitutional validation", "invariant preservation", "rejection behavior"),
                "Category H Persistence Certification": ("persistent state", "transient state", "atomic commit boundaries", "durability"),
                "Category I Replay Certification": ("semantic equivalence", "deterministic replay", "replay admissibility"),
                "Category J Recovery Certification": ("checkpoint recovery", "idempotency", "deterministic restart"),
                "Category K Configuration Certification": ("configuration ownership", "compatibility", "integrity", "version governance"),
                "Category L Traceability Certification": ("provenance", "audit linkage", "evidence completeness", "certification lineage"),
            }
        )
        prerequisites = ("prerequisite validation", "required configuration validation", "registry validation", "identifier validation", "evidence availability verification")
        ids = tuple(entry.certification_test_identifier for entry in entries)
        duplicate_ids = tuple(identifier for identifier in sorted(set(ids)) if ids.count(identifier) > 1)
        category_values = tuple(entry.test_category for entry in entries)
        missing_categories = tuple(category for category in categories if category not in category_values)
        passed = not duplicate_ids and not missing_categories and not duplicate_test_findings and not missing_category_findings and not missing_requirement_coverage and not nondeterministic_execution_findings and not missing_evidence_findings and not dependency_cycle_findings and not replay_divergence_findings and not recovery_gaps and not audit_gaps
        record = AnalystRm004CertificationTestRegistryRecord(
            registry_identifier=f"ANALYST-RM-004-005-TEST-{_digest(entries)[:12].upper()}",
            entries=entries,
            canonical_categories=categories,
            execution_prerequisites=prerequisites,
            duplicate_test_findings=duplicate_ids + duplicate_test_findings,
            missing_category_findings=missing_categories + missing_category_findings,
            missing_requirement_coverage=missing_requirement_coverage,
            nondeterministic_execution_findings=nondeterministic_execution_findings,
            missing_evidence_findings=missing_evidence_findings,
            dependency_cycle_findings=dependency_cycle_findings,
            replay_divergence_findings=replay_divergence_findings,
            recovery_gaps=recovery_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_identity_collision_resolution(
        self,
        *,
        duplicate_identifier_findings: tuple[str, ...] = (),
        conflicting_ownership_findings: tuple[str, ...] = (),
        unresolved_collision_findings: tuple[str, ...] = (),
        namespace_allocation_findings: tuple[str, ...] = (),
        replay_identity_findings: tuple[str, ...] = (),
        recovery_identity_findings: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004IdentityCollisionResolutionRecord:
        classes = MappingProxyType(
            {
                "ICR-001 Duplicate Identifier Collision": ("two objects possess the same canonical identifier", "Reject newest object"),
                "ICR-002 Alias Collision": ("multiple aliases normalize to different canonical identities", "Use Canonical Identity Normalization Tables"),
                "ICR-003 Namespace Collision": ("identifiers violate reserved namespace allocation", "Reject violating identifier"),
                "ICR-004 Version Collision": ("multiple objects claim identical identity and version", "Reject newer publication"),
                "ICR-005 Ownership Collision": ("same identity with different owners", "Immediate constitutional failure"),
                "ICR-006 Replay Collision": ("replay identities differ from historical execution", "Replay fails immediately"),
                "ICR-007 Recovery Collision": ("recovery restores conflicting identities", "Recovery terminates"),
                "ICR-008 Traceability Collision": ("lineage chains reference incompatible identities", "Traceability integrity failure"),
            }
        )
        procedure = ("canonical identifier validation", "namespace verification", "alias normalization", "version verification", "ownership verification", "traceability verification", "collision classification", "resolution execution", "audit evidence generation", "registry update")
        fields_required = ("Resolution Identifier", "Collision Class", "Original Object Identifier", "Conflicting Object Identifier", "Resolution Outcome", "Constitutional Rule Applied", "Ownership Verification", "Timestamp", "Validator Authority", "Certification References")
        updates = ("Identity Collision Registry", "Resolution Registry", "Certification Audit Registry")
        invariants = ("ICRI-001 every object has exactly one canonical identity", "ICRI-002 canonical identities never change", "ICRI-003 every collision produces exactly one resolution outcome", "ICRI-004 ownership is preserved", "ICRI-005 duplicate canonical identifiers cannot coexist", "ICRI-006 replay reproduces identical identity resolution", "ICRI-007 recovery restores identical identity state", "ICRI-008 every resolution generates immutable evidence", "ICRI-009 identity normalization never alters ownership", "ICRI-010 every collision is independently auditable")
        passed = not duplicate_identifier_findings and not conflicting_ownership_findings and not unresolved_collision_findings and not namespace_allocation_findings and not replay_identity_findings and not recovery_identity_findings and not traceability_gaps and not audit_gaps
        record = AnalystRm004IdentityCollisionResolutionRecord(
            registry_identifier=f"ANALYST-RM-004-006-COLLISION-{_digest(classes)[:12].upper()}",
            collision_classes=classes,
            detection_procedure=procedure,
            resolution_record_fields=fields_required,
            registry_updates=updates,
            invariants=invariants,
            duplicate_identifier_findings=duplicate_identifier_findings,
            conflicting_ownership_findings=conflicting_ownership_findings,
            unresolved_collision_findings=unresolved_collision_findings,
            namespace_allocation_findings=namespace_allocation_findings,
            replay_identity_findings=replay_identity_findings,
            recovery_identity_findings=recovery_identity_findings,
            traceability_gaps=traceability_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_metrics_registry(
        self,
        *,
        duplicate_metric_findings: tuple[str, ...] = (),
        missing_metric_class_findings: tuple[str, ...] = (),
        ownership_findings: tuple[str, ...] = (),
        inadmissible_input_findings: tuple[str, ...] = (),
        dependency_cycle_findings: tuple[str, ...] = (),
        reproducibility_findings: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004MetricsRegistryRecord:
        entries = self._metric_registry_entries()
        classes = ("Identity Metrics", "Ownership Metrics", "Evidence Metrics", "Reasoning Metrics", "Hypothesis Metrics", "Confidence Metrics", "Validation Metrics", "Persistence Metrics", "Replay Metrics", "Recovery Metrics", "Traceability Metrics", "Certification Metrics")
        requirements = ("deterministic inputs", "calculation procedure", "admissible evidence sources", "expected output type", "units where applicable", "precision rules", "rounding rules", "dependency ordering")
        invariants = ("immutable definition", "deterministic calculation", "exactly one owner", "complete provenance", "complete traceability", "reproducibility", "auditability", "version compatibility")
        ids = tuple(entry.metric_identifier for entry in entries)
        duplicate_ids = tuple(identifier for identifier in sorted(set(ids)) if ids.count(identifier) > 1)
        present_classes = tuple(entry.metric_class for entry in entries)
        missing_classes = tuple(metric_class for metric_class in classes if metric_class not in present_classes)
        bad_owner = tuple(entry.metric_identifier for entry in entries if entry.constitutional_owner != "Analyst Office")
        passed = not duplicate_ids and not missing_classes and not bad_owner and not duplicate_metric_findings and not missing_metric_class_findings and not ownership_findings and not inadmissible_input_findings and not dependency_cycle_findings and not reproducibility_findings and not traceability_gaps and not audit_gaps
        record = AnalystRm004MetricsRegistryRecord(
            registry_identifier=f"ANALYST-RM-004-007-METRIC-{_digest(entries)[:12].upper()}",
            entries=entries,
            metric_classes=classes,
            calculation_requirements=requirements,
            invariants=invariants,
            duplicate_metric_findings=duplicate_ids + duplicate_metric_findings,
            missing_metric_class_findings=missing_classes + missing_metric_class_findings,
            ownership_findings=bad_owner + ownership_findings,
            inadmissible_input_findings=inadmissible_input_findings,
            dependency_cycle_findings=dependency_cycle_findings,
            reproducibility_findings=reproducibility_findings,
            traceability_gaps=traceability_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_certification_manifest_schema(
        self,
        *,
        missing_schema_sections: tuple[str, ...] = (),
        missing_artifact_findings: tuple[str, ...] = (),
        evidence_linkage_findings: tuple[str, ...] = (),
        compatibility_findings: tuple[str, ...] = (),
        validation_failures: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004CertificationManifestSchemaRecord:
        identity = ("Manifest Identifier", "Manifest Version", "Certification Identifier", "Candidate Identifier", "Constitutional Version", "Schema Version", "Registry Version", "Creation Timestamp", "Effective Timestamp", "Integrity Metadata")
        sections = MappingProxyType(
            {
                "Manifest Header": ("manifest identifier", "manifest version", "certification identifier", "schema version", "constitutional version"),
                "Candidate Section": ("certification candidate", "candidate class", "ownership", "evaluation scope", "certification applicability"),
                "Certification Scope": ("evaluated constitutional objects", "evaluated doctrine", "excluded scope", "certification boundaries"),
                "Registry References": ("Candidate Class Registry", "Evaluation Rule Registry", "Metrics Registry", "Identifier Registry", "Rule Registry", "Schema Registry", "Compatibility Matrix"),
                "Constitutional Doctrine References": ("doctrine identifier", "version", "applicability"),
                "Evidence Package References": ("identifier", "version", "provenance", "integrity verification"),
                "Evaluation Summary": ("executed evaluation rules", "passed evaluations", "failed evaluations", "skipped evaluations", "evaluation timestamps"),
                "Metrics Summary": ("metric identifier", "measured value", "threshold", "evaluation result"),
                "Compatibility Declaration": ("doctrine versions", "schema versions", "registry versions", "evidence versions", "certification versions"),
                "Validation Summary": ("validation status", "validation evidence", "validation authority", "validation timestamps"),
                "Certification Outcome": ("Pass", "Conditional Pass", "Fail"),
                "Certification Closure": ("certification completion timestamp", "certification authority", "closure references", "archival references"),
            }
        )
        mandatory = ("certification evidence", "evaluation results", "registry versions", "doctrine versions", "compatibility declarations", "audit evidence")
        outcomes = ("Pass", "Conditional Pass", "Fail")
        invariants = ("exactly one manifest per certification execution", "exactly one constitutional owner", "manifest identity is immutable", "every mandatory artifact is referenced", "evidence packages possess complete linkage", "compatibility declarations are explicit", "replay reproduces equivalent manifests", "recovery restores identical manifest state", "audit evidence accompanies every manifest", "implementation does not influence manifest generation")
        missing = tuple(section for section in sections if section in missing_schema_sections)
        passed = not missing and not missing_artifact_findings and not evidence_linkage_findings and not compatibility_findings and not validation_failures and not replay_divergence_findings and not recovery_gaps and not audit_gaps
        record = AnalystRm004CertificationManifestSchemaRecord(
            registry_identifier=f"ANALYST-RM-004-008-MANIFEST-{_digest((identity, sections))[:12].upper()}",
            identity_fields=identity,
            schema_sections=sections,
            mandatory_artifacts=mandatory,
            outcome_values=outcomes,
            invariants=invariants,
            missing_schema_sections=missing,
            missing_artifact_findings=missing_artifact_findings,
            evidence_linkage_findings=evidence_linkage_findings,
            compatibility_findings=compatibility_findings,
            validation_failures=validation_failures,
            replay_divergence_findings=replay_divergence_findings,
            recovery_gaps=recovery_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_identifier_registry(
        self,
        *,
        duplicate_namespace_findings: tuple[str, ...] = (),
        missing_namespace_findings: tuple[str, ...] = (),
        allocation_findings: tuple[str, ...] = (),
        uniqueness_findings: tuple[str, ...] = (),
        replay_identifier_findings: tuple[str, ...] = (),
        recovery_identifier_findings: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004IdentifierRegistryRecord:
        namespaces = self._identifier_namespaces()
        structure = ("Namespace", "Sequential Identifier", "Version Identifier", "Schema Version", "Integrity Check Component", "Certification Generation")
        allocation = ("allocated once", "allocated atomically", "allocated by constitutional authority", "allocated before object creation", "never reused")
        lifecycle = ("Allocated", "Active", "Referenced", "Archived", "Historical", "Permanent")
        validation = ("namespace validity", "uniqueness", "format correctness", "ownership", "compatibility", "version consistency", "integrity component", "certification applicability")
        invariants = ("one identifier per artifact", "global uniqueness", "immutability", "explicit ownership", "allocation exactly once", "identifiers never reused", "unique namespace ownership", "replay preserves identifiers", "recovery preserves identifiers", "permanent lineage", "validation precedes use", "immutable audit history")
        ns_values = tuple(entry.namespace for entry in namespaces)
        duplicate_ns = tuple(namespace for namespace in sorted(set(ns_values)) if ns_values.count(namespace) > 1)
        required_ns = ("AM", "AP", "PK", "EV", "RG", "CF", "HY", "CS", "CT", "VL", "LC", "RP", "RC", "CO", "AR", "CE", "CM", "CP", "CR", "SC")
        missing_ns = tuple(namespace for namespace in required_ns if namespace not in ns_values)
        passed = not duplicate_ns and not missing_ns and not duplicate_namespace_findings and not missing_namespace_findings and not allocation_findings and not uniqueness_findings and not replay_identifier_findings and not recovery_identifier_findings and not traceability_gaps and not audit_gaps
        record = AnalystRm004IdentifierRegistryRecord(
            registry_identifier=f"ANALYST-RM-004-009-IDREG-{_digest(namespaces)[:12].upper()}",
            namespaces=namespaces,
            identifier_structure=structure,
            allocation_rules=allocation,
            lifecycle_states=lifecycle,
            validation_requirements=validation,
            invariants=invariants,
            duplicate_namespace_findings=duplicate_ns + duplicate_namespace_findings,
            missing_namespace_findings=missing_ns + missing_namespace_findings,
            allocation_findings=allocation_findings,
            uniqueness_findings=uniqueness_findings,
            replay_identifier_findings=replay_identifier_findings,
            recovery_identifier_findings=recovery_identifier_findings,
            traceability_gaps=traceability_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_version_compatibility_matrix(
        self,
        *,
        missing_compatibility_entries: tuple[str, ...] = (),
        unknown_compatibility_findings: tuple[str, ...] = (),
        incompatible_artifact_findings: tuple[str, ...] = (),
        supersession_findings: tuple[str, ...] = (),
        replay_divergence_findings: tuple[str, ...] = (),
        recovery_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004VersionCompatibilityRecord:
        classes = ("Constitutional Doctrine Version", "Engineering Specification Version", "Schema Version", "Registry Version", "Certification Version", "Configuration Version", "Evidence Version")
        matrix = MappingProxyType(
            {
                "Doctrine->Engineering Specification": ("Engineering Specification", "Matching Constitutional Version"),
                "Specification->Registry": ("Registry", "Matching Registry Version"),
                "Registry->Schema": ("Schema", "Approved Schema Version"),
                "Schema->Evidence": ("Evidence", "Compatible Schema Revision"),
                "Evidence->Certification Package": ("Certification Package", "Matching Evidence Version"),
                "Certification Package->Certification Procedure": ("Certification Procedure", "Matching Certification Version"),
                "Configuration->Doctrine": ("Doctrine", "Approved Constitutional Version"),
            }
        )
        sequence = ("Validate artifact identity", "Validate constitutional version", "Validate schema version", "Validate registry version", "Validate configuration compatibility", "Validate evidence compatibility", "Validate certification package compatibility", "Produce immutable compatibility result")
        prohibited = ("incompatible doctrine versions coexist", "schema versions conflict", "registry revisions conflict", "incompatible evidence packages supplied", "configuration references unsupported doctrine", "certification artifacts from incompatible revisions")
        invariants = ("explicit version on every artifact", "explicit version relationships", "deterministic compatibility", "incompatible artifacts never certified together", "supersession preserves historical compatibility", "mandatory compatibility validation", "replay reproduces compatibility decisions", "recovery preserves compatibility history", "immutable audit history", "certification never assumes undefined compatibility")
        missing = tuple(entry for entry in matrix if entry in missing_compatibility_entries)
        passed = not missing and not unknown_compatibility_findings and not incompatible_artifact_findings and not supersession_findings and not replay_divergence_findings and not recovery_gaps and not audit_gaps
        record = AnalystRm004VersionCompatibilityRecord(
            registry_identifier=f"ANALYST-RM-004-010-VERSION-{_digest(matrix)[:12].upper()}",
            version_classes=classes,
            compatibility_matrix=matrix,
            evaluation_sequence=sequence,
            prohibited_combinations=prohibited,
            invariants=invariants,
            missing_compatibility_entries=missing,
            unknown_compatibility_findings=unknown_compatibility_findings,
            incompatible_artifact_findings=incompatible_artifact_findings,
            supersession_findings=supersession_findings,
            replay_divergence_findings=replay_divergence_findings,
            recovery_gaps=recovery_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_constitutional_rule_registry(
        self,
        *,
        duplicate_rule_findings: tuple[str, ...] = (),
        ambiguous_ownership_findings: tuple[str, ...] = (),
        missing_dependency_findings: tuple[str, ...] = (),
        invalid_applicability_findings: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
        replay_recovery_findings: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
        invariant_violations: tuple[str, ...] = (),
    ) -> AnalystRm004ConstitutionalRuleRegistryRecord:
        entries = self._constitutional_rule_entries()
        fields_required = ("Rule Identifier", "Rule Name", "Rule Category", "Constitutional Owner", "Rule Description", "Evaluation Intent", "Evaluation Procedure Reference", "Dependency References", "Applicable Candidate Classes", "Required Evidence", "Certification Severity", "Version", "Publication Status", "Traceability References", "Audit References")
        categories = ("CRR-001 Identity Rules", "CRR-002 Ownership Rules", "CRR-003 Lifecycle Rules", "CRR-004 Validation Rules", "CRR-005 Reasoning Rules", "CRR-006 Confidence Rules", "CRR-007 Persistence Rules", "CRR-008 Replay Rules", "CRR-009 Recovery Rules", "CRR-010 Traceability Rules", "CRR-011 Configuration Rules", "CRR-012 Certification Rules")
        severities = ("Critical", "Mandatory", "Required", "Advisory")
        dependencies = ("prerequisite rules", "dependent rules", "governing doctrine", "required schemas", "required registries", "acyclic dependency graph")
        invariants = tuple(f"CRRI-{index:03d}" for index in range(1, 11))
        ids = tuple(entry.rule_identifier for entry in entries)
        duplicate_ids = tuple(identifier for identifier in sorted(set(ids)) if ids.count(identifier) > 1)
        category_values = tuple(entry.rule_category for entry in entries)
        missing_categories = tuple(category for category in categories if category not in category_values)
        bad_owner = tuple(entry.rule_identifier for entry in entries if entry.constitutional_owner != "Analyst Office")
        bad_severity = tuple(entry.rule_identifier for entry in entries if entry.certification_severity not in severities)
        bad_applicability = tuple(entry.rule_identifier for entry in entries if not entry.applicable_candidate_classes)
        passed = not duplicate_ids and not missing_categories and not bad_owner and not bad_severity and not bad_applicability and not duplicate_rule_findings and not ambiguous_ownership_findings and not missing_dependency_findings and not invalid_applicability_findings and not traceability_gaps and not replay_recovery_findings and not audit_gaps and not invariant_violations
        record = AnalystRm004ConstitutionalRuleRegistryRecord(
            registry_identifier=f"ANALYST-RM-004-011-CRR-{_digest(entries)[:12].upper()}",
            entries=entries,
            registry_fields=fields_required,
            rule_categories=categories,
            severity_levels=severities,
            dependency_requirements=dependencies,
            invariants=invariants,
            duplicate_rule_findings=duplicate_ids + duplicate_rule_findings,
            ambiguous_ownership_findings=bad_owner + ambiguous_ownership_findings,
            missing_dependency_findings=missing_categories + missing_dependency_findings,
            invalid_applicability_findings=bad_severity + bad_applicability + invalid_applicability_findings,
            traceability_gaps=traceability_gaps,
            replay_recovery_findings=replay_recovery_findings,
            audit_gaps=audit_gaps,
            invariant_violations=invariant_violations,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_schema_registry(
        self,
        *,
        duplicate_schema_findings: tuple[str, ...] = (),
        missing_schema_class_findings: tuple[str, ...] = (),
        ownership_findings: tuple[str, ...] = (),
        compatibility_gaps: tuple[str, ...] = (),
        relationship_cycle_findings: tuple[str, ...] = (),
        validation_failures: tuple[str, ...] = (),
        replay_recovery_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004SchemaRegistryRecord:
        entries = self._schema_registry_entries()
        identity_fields = ("Schema Identifier", "Schema Name", "Schema Version", "Schema Class", "Canonical Namespace", "Constitutional Owner", "Approval Authority", "Certification Authority", "Parent Schema", "Compatible Schemas", "Dependent Schemas", "Referenced Registries", "Certification Status", "Validation Status", "Effective Version", "Deprecation Status")
        schema_classes = MappingProxyType(
            {
                "Mission Schemas": ("Analytical Mission", "Analysis Plan", "Analytical Package"),
                "Evidence Schemas": ("Analytical Evidence", "Evidence Provenance", "Evidence Validation"),
                "Reasoning Schemas": ("Reasoning Graph", "Reasoning Node", "Reasoning Edge"),
                "Analytical Schemas": ("Hypothesis", "Confidence Object", "Analytical Conclusion", "Recommendation", "Organizational Belief State"),
                "Lifecycle Schemas": ("Lifecycle State", "Commit Boundary", "Replay State", "Recovery State"),
                "Validation Schemas": ("Validation Record", "Validation Result", "Invariant Evaluation"),
                "Traceability Schemas": ("Trace Record", "Dependency Record", "Audit Record"),
                "Configuration Schemas": ("Configuration Object", "Configuration Version", "Compatibility Definition"),
                "Certification Schemas": ("Certification Manifest", "Certification Evidence Package", "Certification Test", "Certification Decision", "Certification Closure"),
            }
        )
        lifecycle = ("Proposed", "Under Review", "Approved", "Active", "Superseded", "Deprecated", "Archived")
        ids = tuple(entry.schema_identifier for entry in entries)
        duplicate_ids = tuple(identifier for identifier in sorted(set(ids)) if ids.count(identifier) > 1)
        class_values = tuple(entry.schema_name for entry in entries)
        missing_classes = tuple(schema for names in schema_classes.values() for schema in names if schema not in class_values)
        bad_owner = tuple(entry.schema_identifier for entry in entries if entry.constitutional_owner != "Analyst Office")
        invalid_status = tuple(entry.schema_identifier for entry in entries if entry.validation_status != "Validated")
        passed = not duplicate_ids and not missing_classes and not bad_owner and not invalid_status and not duplicate_schema_findings and not missing_schema_class_findings and not ownership_findings and not compatibility_gaps and not relationship_cycle_findings and not validation_failures and not replay_recovery_gaps and not audit_gaps
        record = AnalystRm004SchemaRegistryRecord(
            registry_identifier=f"ANALYST-RM-004-012-SCHEMA-{_digest(entries)[:12].upper()}",
            entries=entries,
            schema_identity_fields=identity_fields,
            schema_classes=schema_classes,
            lifecycle_states=lifecycle,
            duplicate_schema_findings=duplicate_ids + duplicate_schema_findings,
            missing_schema_class_findings=missing_classes + missing_schema_class_findings,
            ownership_findings=bad_owner + ownership_findings,
            compatibility_gaps=compatibility_gaps,
            relationship_cycle_findings=relationship_cycle_findings,
            validation_failures=invalid_status + validation_failures,
            replay_recovery_gaps=replay_recovery_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_registry_cross_reference_matrix(
        self,
        *,
        duplicate_registry_findings: tuple[str, ...] = (),
        missing_registry_findings: tuple[str, ...] = (),
        illegal_relationship_findings: tuple[str, ...] = (),
        broken_reference_findings: tuple[str, ...] = (),
        dependency_cycle_findings: tuple[str, ...] = (),
        compatibility_gaps: tuple[str, ...] = (),
        replay_recovery_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004RegistryCrossReferenceRecord:
        inventory = ("Candidate Class Registry", "Canonical Identity Normalization Tables", "Constitutional Evaluation Rule Registry", "Certification Threshold Doctrine", "Constitutional Certification Test Registry", "Identity Collision Resolution Registry", "Constitutional Metrics Registry", "Certification Manifest Schema", "Constitutional Identifier Registry", "Version Compatibility Matrix", "Constitutional Rule Registry", "Constitutional Schema Registry", "Certification Evidence Registry", "Constitutional Decision Registry", "Certification Package Schema", "Certification Traceability Matrix", "Certification Procedure Registry", "Certification Exception Registry", "Certification Closure Registry")
        sections = MappingProxyType(
            {
                "Matrix Header": ("Matrix Identifier", "Matrix Version", "Constitutional Version", "Schema Version", "Registry Version", "Owner", "Creation Timestamp", "Effective Timestamp", "Integrity Metadata"),
                "Registry Inventory": inventory,
                "Dependency Matrix": ("source registry", "target registry", "relationship type", "version compatibility"),
                "Identifier Relationships": ("identifier owner", "namespace", "canonical object", "registry reference"),
                "Schema Relationships": ("schema owner", "compatible schema", "dependent schema", "validation status"),
                "Rule Relationships": ("rule registry", "governed candidate class", "required evidence"),
                "Metrics Relationships": ("metric registry", "rule registry", "threshold registry"),
                "Evidence Relationships": ("evidence registry", "manifest schema", "traceability matrix"),
                "Compatibility Relationships": ("version matrix", "schema registry", "identifier registry"),
                "Certification Relationships": ("test registry", "procedure registry", "decision registry", "closure registry"),
            }
        )
        relationship_types = ("Depends Upon", "References", "Validates", "Governs", "Supersedes", "Contains", "Produces", "Consumes", "Certifies", "Audits")
        invariants = ("every registry appears exactly once", "relationships are explicit", "dependencies are acyclic", "references are valid", "compatibility is explicit", "replay relationships are preserved", "recovery relationships are preserved", "historical versions remain linked", "audit lineage is complete", "implementation independence")
        duplicate_inventory = tuple(registry for registry in sorted(set(inventory)) if inventory.count(registry) > 1)
        passed = not duplicate_inventory and not duplicate_registry_findings and not missing_registry_findings and not illegal_relationship_findings and not broken_reference_findings and not dependency_cycle_findings and not compatibility_gaps and not replay_recovery_gaps and not audit_gaps
        record = AnalystRm004RegistryCrossReferenceRecord(
            matrix_identifier=f"ANALYST-RM-004-013-XREF-{_digest((inventory, sections))[:12].upper()}",
            matrix_version="1.0.0",
            constitutional_version="ANALYST-RM-004",
            schema_version="1.0.0",
            registry_version="1.0.0",
            owner="Analyst Office",
            integrity_metadata=_digest((inventory, relationship_types))[:24],
            registry_inventory=inventory,
            matrix_sections=sections,
            relationship_types=relationship_types,
            invariants=invariants,
            duplicate_registry_findings=duplicate_inventory + duplicate_registry_findings,
            missing_registry_findings=missing_registry_findings,
            illegal_relationship_findings=illegal_relationship_findings,
            broken_reference_findings=broken_reference_findings,
            dependency_cycle_findings=dependency_cycle_findings,
            compatibility_gaps=compatibility_gaps,
            replay_recovery_gaps=replay_recovery_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_certification_evidence_registry(
        self,
        *,
        duplicate_evidence_findings: tuple[str, ...] = (),
        missing_class_findings: tuple[str, ...] = (),
        ownership_findings: tuple[str, ...] = (),
        inadmissible_evidence_findings: tuple[str, ...] = (),
        integrity_failures: tuple[str, ...] = (),
        provenance_gaps: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
        replay_recovery_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004CertificationEvidenceRegistryRecord:
        classes = ("Identity Evidence", "Ownership Evidence", "Schema Evidence", "Lifecycle Evidence", "Validation Evidence", "Replay Evidence", "Recovery Evidence", "Traceability Evidence", "Persistence Evidence", "Configuration Evidence", "Audit Evidence", "Metrics Evidence", "Test Evidence", "Certification Decision Evidence", "Compliance Evidence")
        identity = ("Evidence Identifier", "Evidence Class", "Evidence Version", "Schema Version", "Constitutional Owner", "Creation Timestamp", "Certification Version", "Integrity Identifier", "Provenance Identifier")
        lifecycle = ("Created", "Validated", "Accepted", "Referenced", "Archived", "Historical", "Permanent")
        fields_required = ("Evidence Identifier", "Evidence Class", "Constitutional Owner", "Schema Version", "Object Reference", "Doctrine Reference", "Validation Status", "Integrity Status", "Provenance Reference", "Audit Reference", "Certification Reference")
        admissibility = ("constitutionally generated", "constitutionally owned", "schema compliant", "integrity verified", "provenance complete", "traceability complete", "validation complete", "version compatible")
        missing = tuple(item for item in classes if item in missing_class_findings)
        passed = not missing and not duplicate_evidence_findings and not ownership_findings and not inadmissible_evidence_findings and not integrity_failures and not provenance_gaps and not traceability_gaps and not replay_recovery_gaps and not audit_gaps
        record = AnalystRm004CertificationEvidenceRegistryRecord(
            registry_identifier=f"ANALYST-RM-004-014-EVIDENCE-{_digest((classes, fields_required))[:12].upper()}",
            evidence_classes=classes,
            identity_fields=identity,
            lifecycle_states=lifecycle,
            registry_fields=fields_required,
            admissibility_requirements=admissibility,
            duplicate_evidence_findings=duplicate_evidence_findings,
            missing_class_findings=missing,
            ownership_findings=ownership_findings,
            inadmissible_evidence_findings=inadmissible_evidence_findings,
            integrity_failures=integrity_failures,
            provenance_gaps=provenance_gaps,
            traceability_gaps=traceability_gaps,
            replay_recovery_gaps=replay_recovery_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_decision_registry(
        self,
        *,
        duplicate_decision_findings: tuple[str, ...] = (),
        missing_category_findings: tuple[str, ...] = (),
        invalid_outcome_findings: tuple[str, ...] = (),
        authority_findings: tuple[str, ...] = (),
        evidence_gaps: tuple[str, ...] = (),
        dependency_cycle_findings: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
        replay_recovery_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> AnalystRm004DecisionRegistryRecord:
        entries = self._decision_registry_entries()
        fields_required = ("Decision Identifier", "Decision Revision Identifier", "Constitutional Version", "Registry Version", "Owning Office", "Decision Authority", "Evaluation Authority", "Decision Name", "Decision Category", "Governing Work Order", "Constitutional Requirement", "Decision Description", "Trigger Conditions", "Required Inputs", "Required Evidence", "Required Dependencies", "Evaluation Trigger", "Evaluation Rules", "Required Validation", "Required Invariants", "Expected Result", "Outcomes", "Doctrine References", "Specification References", "Rule References", "Evidence References", "Audit References")
        categories = ("Authority", "Identity", "Object", "Reasoning", "Evidence", "Confidence", "Validation", "Persistence", "Replay", "Recovery", "Configuration", "Certification")
        sequence = ("Validate decision authority", "Validate required evidence", "Validate prerequisite decisions", "Evaluate rules", "Verify invariants", "Produce deterministic outcome", "Record audit")
        outcomes = ("PASS", "FAIL", "REJECT", "NOT APPLICABLE")
        ids = tuple(entry.decision_identifier for entry in entries)
        duplicate_ids = tuple(identifier for identifier in sorted(set(ids)) if ids.count(identifier) > 1)
        category_values = tuple(entry.decision_category for entry in entries)
        missing_categories = tuple(category for category in categories if category not in category_values)
        bad_outcomes = tuple(entry.decision_identifier for entry in entries if entry.outcomes != outcomes)
        bad_authority = tuple(entry.decision_identifier for entry in entries if entry.decision_authority != "Independent Enterprise Certification")
        passed = not duplicate_ids and not missing_categories and not bad_outcomes and not bad_authority and not duplicate_decision_findings and not missing_category_findings and not invalid_outcome_findings and not authority_findings and not evidence_gaps and not dependency_cycle_findings and not traceability_gaps and not replay_recovery_gaps and not audit_gaps
        record = AnalystRm004DecisionRegistryRecord(
            registry_identifier=f"ANALYST-RM-004-015-DECISION-{_digest(entries)[:12].upper()}",
            entries=entries,
            decision_object_fields=fields_required,
            decision_categories=categories,
            evaluation_sequence=sequence,
            outcome_values=outcomes,
            duplicate_decision_findings=duplicate_ids + duplicate_decision_findings,
            missing_category_findings=missing_categories + missing_category_findings,
            invalid_outcome_findings=bad_outcomes + invalid_outcome_findings,
            authority_findings=bad_authority + authority_findings,
            evidence_gaps=evidence_gaps,
            dependency_cycle_findings=dependency_cycle_findings,
            traceability_gaps=traceability_gaps,
            replay_recovery_gaps=replay_recovery_gaps,
            audit_gaps=audit_gaps,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def _candidate_class_entries(self) -> tuple[AnalystRm004CandidateClassEntry, ...]:
        rows = (
            ("ACC-001", "Analytical Mission", "Mission Object", ("mission identity", "authority", "lifecycle", "validation", "persistence", "replay", "recovery")),
            ("ACC-002", "Analysis Plan", "Execution Object", ("planning semantics", "execution contract", "admissibility", "deterministic sequencing")),
            ("ACC-003", "Analytical Package", "Operational Object", ("schema", "ownership", "evidence relationships", "admissibility", "validation")),
            ("ACC-004", "Reasoning Graph", "Reasoning Object", ("inference correctness", "provenance", "determinism", "graph integrity")),
            ("ACC-005", "Evidence Object", "Evidence Object", ("integrity", "provenance", "admissibility", "normalization", "preservation")),
            ("ACC-006", "Hypothesis Object", "Reasoning Object", ("representation", "evaluation", "contradiction preservation", "evidence linkage")),
            ("ACC-007", "Confidence Assessment", "Analytical Object", ("confidence determination", "uncertainty representation", "inheritance", "validation")),
            ("ACC-008", "Analytical Conclusion", "Decision Object", ("evidence support", "reasoning support", "confidence support", "admissibility")),
            ("ACC-009", "Validation Record", "Certification Evidence", ("validation completeness", "rule compliance", "traceability")),
            ("ACC-010", "Traceability Record", "Audit Object", ("lineage completeness", "bidirectional traceability", "integrity")),
            ("ACC-011", "Configuration Object", "Configuration Object", ("schema", "compatibility", "integrity", "version governance")),
            ("ACC-012", "Persistent State", "Persistence Object", ("durability", "checkpoint integrity", "recovery readiness")),
            ("ACC-013", "Replay Artifact", "Replay Object", ("semantic equivalence", "deterministic reproduction", "replay evidence")),
            ("ACC-014", "Recovery Artifact", "Recovery Object", ("checkpoint restoration", "invariant preservation", "recovery correctness")),
            ("ACC-015", "Certification Artifact", "Certification Object", ("certification completeness", "evidence inclusion", "audit readiness")),
        )
        return tuple(
            AnalystRm004CandidateClassEntry(
                candidate_class_identifier=identifier,
                canonical_name=name,
                candidate_category=category,
                constitutional_owner="Analyst Office",
                certification_scope=scope,
                applicable_work_orders=("ANALYST-RM-001", "ANALYST-RM-002", "ANALYST-RM-003", "ANALYST-RM-004"),
                required_evidence=("validation evidence", "replay evidence", "recovery evidence", "audit evidence"),
                evaluation_rule_set=("Identity", "Ownership", "Schema", "Validation", "Traceability", "Certification"),
                certification_dependencies=("Candidate Class Registry", "Identity Normalization", "Evaluation Rule Registry", "Threshold Registry", "Test Registry"),
                required_schemas=(f"{name} Schema",),
                required_registries=("Constitutional Evaluation Rule Registry", "Constitutional Certification Test Registry"),
                certification_status="Specified",
                version="1.0.0",
                audit_references=(f"{identifier}-AUDIT",),
            )
            for identifier, name, category, scope in rows
        )

    def _metric_registry_entries(self) -> tuple[AnalystRm004MetricRegistryEntry, ...]:
        rows = (
            ("M-ID", "Identifier Uniqueness", "Identity Metrics", ("Evidence Object",), ("identity uniqueness",)),
            ("M-OWN", "Ownership Completeness", "Ownership Metrics", ("Candidate Class",), ("ownership validation",)),
            ("M-EVID", "Evidence Admissibility Ratio", "Evidence Metrics", ("Evidence Object",), ("admissibility validation",)),
            ("M-REAS", "Reasoning Graph Completeness", "Reasoning Metrics", ("Reasoning Graph",), ("reasoning validation",)),
            ("M-HYP", "Hypothesis Preservation", "Hypothesis Metrics", ("Hypothesis Object",), ("hypothesis validation",)),
            ("M-CONF", "Confidence Traceability", "Confidence Metrics", ("Confidence Assessment",), ("confidence validation",)),
            ("M-VAL", "Validation Completion", "Validation Metrics", ("Validation Record",), ("validation completion",)),
            ("M-PERS", "Persistence Integrity", "Persistence Metrics", ("Persistent State",), ("persistence validation",)),
            ("M-REP", "Replay Equivalence", "Replay Metrics", ("Replay Artifact",), ("replay validation",)),
            ("M-REC", "Recovery Correctness", "Recovery Metrics", ("Recovery Artifact",), ("recovery validation",)),
            ("M-TRACE", "Trace Chain Completeness", "Traceability Metrics", ("Traceability Record",), ("traceability validation",)),
            ("M-CERT", "Certification Evidence Completeness", "Certification Metrics", ("Certification Artifact",), ("certification validation",)),
        )
        return tuple(
            AnalystRm004MetricRegistryEntry(
                metric_identifier=identifier,
                metric_name=name,
                metric_class=metric_class,
                constitutional_owner="Analyst Office",
                calculation_rule_identifier=f"{identifier}-RULE",
                input_objects=inputs,
                validation_rules=rules,
                dependency_references=("Constitutional Metrics Registry", "Evaluation Rule Registry"),
            )
            for identifier, name, metric_class, inputs, rules in rows
        )

    def _identifier_namespaces(self) -> tuple[AnalystRm004IdentifierNamespaceEntry, ...]:
        rows = (
            ("AM", "Analytical Missions"),
            ("AP", "Analysis Plans"),
            ("PK", "Analytical Packages"),
            ("EV", "Evidence"),
            ("RG", "Reasoning Graphs"),
            ("CF", "Confidence Objects"),
            ("HY", "Hypotheses"),
            ("CS", "Consensus Objects"),
            ("CT", "Contradictions"),
            ("VL", "Validation Records"),
            ("LC", "Lifecycle Records"),
            ("RP", "Replay Records"),
            ("RC", "Recovery Records"),
            ("CO", "Configuration Objects"),
            ("AR", "Audit Records"),
            ("CE", "Certification Evidence"),
            ("CM", "Certification Manifests"),
            ("CP", "Certification Packages"),
            ("CR", "Constitutional Registries"),
            ("SC", "Constitutional Schemas"),
        )
        return tuple(
            AnalystRm004IdentifierNamespaceEntry(
                namespace=namespace,
                purpose=purpose,
                constitutional_owner="Analyst Office",
                allocation_authority="Constitutional Identifier Registry",
                lifecycle_authority="Analyst Office",
                reserved_ranges=("examples", "certification references", "historical compatibility", "deprecated references", "future expansion"),
            )
            for namespace, purpose in rows
        )

    def _evaluation_rule_entries(self) -> tuple[AnalystRm004EvaluationRuleEntry, ...]:
        rows = (
            ("AER-001", "Identity Verification", "Identity Evaluation Rule"),
            ("AER-002", "Ownership Verification", "Ownership Evaluation Rule"),
            ("AER-003", "Schema Validation", "Schema Evaluation Rule"),
            ("AER-004", "Lifecycle Validation", "Lifecycle Evaluation Rule"),
            ("AER-005", "Evidence Validation", "Evidence Evaluation Rule"),
            ("AER-006", "Reasoning Validation", "Reasoning Evaluation Rule"),
            ("AER-007", "Provenance Validation", "Provenance Evaluation Rule"),
            ("AER-008", "Confidence Validation", "Confidence Evaluation Rule"),
            ("AER-009", "Hypothesis Validation", "Hypothesis Evaluation Rule"),
            ("AER-010", "Configuration Validation", "Configuration Evaluation Rule"),
            ("AER-011", "Persistence Validation", "Persistence Evaluation Rule"),
            ("AER-012", "Replay Validation", "Replay Evaluation Rule"),
            ("AER-013", "Recovery Validation", "Recovery Evaluation Rule"),
            ("AER-014", "Audit Validation", "Audit Evaluation Rule"),
            ("AER-015", "Certification Closure Validation", "Certification Evaluation Rule"),
        )
        return tuple(
            AnalystRm004EvaluationRuleEntry(
                rule_identifier=identifier,
                rule_version="1.0.0",
                rule_name=name,
                rule_classification=classification,
                evaluation_scope=(name.removesuffix(" Validation").removesuffix(" Verification"),),
                required_inputs=("constitutional object", "evidence artifacts", "registry references", "configuration references", "certification metadata"),
                evaluation_procedure=("load canonical inputs", "validate prerequisites", "evaluate deterministic criteria", "record outcome", "emit audit evidence"),
                expected_outcomes=("Pass", "Fail", "Not Applicable"),
                failure_classification=f"{identifier}-FAIL",
                dependencies=(),
                audit_requirements=("rule identifier", "registry version", "evaluated object", "inputs", "outcome", "failure classification", "timestamp", "integrity verification"),
            )
            for identifier, name, classification in rows
        )

    def _certification_test_entries(self) -> tuple[AnalystRm004CertificationTestEntry, ...]:
        rows = (
            ("ACT-001", "Category A Authority Certification", "authority and ownership boundaries"),
            ("ACT-002", "Category B Identity Certification", "canonical identity normalization"),
            ("ACT-003", "Category C Object Certification", "schema, object integrity, and lifecycle"),
            ("ACT-004", "Category D Reasoning Certification", "reasoning determinism and contradiction preservation"),
            ("ACT-005", "Category E Evidence Certification", "evidence admissibility and provenance"),
            ("ACT-006", "Category F Confidence Certification", "confidence derivation and uncertainty"),
            ("ACT-007", "Category G Validation Certification", "validation and rejection behavior"),
            ("ACT-008", "Category H Persistence Certification", "persistent state and atomic commits"),
            ("ACT-009", "Category I Replay Certification", "semantic replay equivalence"),
            ("ACT-010", "Category J Recovery Certification", "checkpoint recovery and restart"),
            ("ACT-011", "Category K Configuration Certification", "configuration integrity and compatibility"),
            ("ACT-012", "Category L Traceability Certification", "traceability and certification lineage"),
        )
        return tuple(
            AnalystRm004CertificationTestEntry(
                certification_test_identifier=identifier,
                test_category=category,
                constitutional_requirement=requirement,
                governing_work_order="ANALYST-RM-004-005",
                required_inputs=("candidate class", "normalized identity", "evaluation rule", "threshold", "evidence manifest"),
                expected_constitutional_outcome="deterministic PASS or FAIL",
                required_evidence=("audit evidence", "validation evidence", "traceability references", "certification artifact"),
                pass_criteria=("all required invariants satisfied", "expected object state exists", "required evidence produced", "deterministic result matches expected behavior", "audit evidence complete"),
                failure_criteria=("invariant violated", "required evidence absent", "ownership ambiguous", "determinism absent", "replay diverges", "recovery differs", "audit incomplete"),
                dependencies=("ANALYST-RM-004-001", "ANALYST-RM-004-002", "ANALYST-RM-004-003", "ANALYST-RM-004-004"),
            )
            for identifier, category, requirement in rows
        )

    def _constitutional_rule_entries(self) -> tuple[AnalystRm004ConstitutionalRuleEntry, ...]:
        rows = (
            ("CRR-001", "Identity Rule", "CRR-001 Identity Rules", "Critical", ("ACC-001", "ACC-002", "ACC-003")),
            ("CRR-002", "Ownership Rule", "CRR-002 Ownership Rules", "Critical", ("ACC-001", "ACC-005", "ACC-015")),
            ("CRR-003", "Lifecycle Rule", "CRR-003 Lifecycle Rules", "Mandatory", ("ACC-001", "ACC-011", "ACC-012")),
            ("CRR-004", "Validation Rule", "CRR-004 Validation Rules", "Critical", ("ACC-003", "ACC-009", "ACC-015")),
            ("CRR-005", "Reasoning Rule", "CRR-005 Reasoning Rules", "Mandatory", ("ACC-004", "ACC-006", "ACC-008")),
            ("CRR-006", "Confidence Rule", "CRR-006 Confidence Rules", "Mandatory", ("ACC-007", "ACC-008")),
            ("CRR-007", "Persistence Rule", "CRR-007 Persistence Rules", "Critical", ("ACC-011", "ACC-012")),
            ("CRR-008", "Replay Rule", "CRR-008 Replay Rules", "Critical", ("ACC-013",)),
            ("CRR-009", "Recovery Rule", "CRR-009 Recovery Rules", "Critical", ("ACC-014",)),
            ("CRR-010", "Traceability Rule", "CRR-010 Traceability Rules", "Mandatory", ("ACC-010", "ACC-015")),
            ("CRR-011", "Configuration Rule", "CRR-011 Configuration Rules", "Required", ("ACC-011",)),
            ("CRR-012", "Certification Rule", "CRR-012 Certification Rules", "Critical", ("ACC-015",)),
        )
        return tuple(
            AnalystRm004ConstitutionalRuleEntry(
                rule_identifier=identifier,
                rule_name=name,
                rule_category=category,
                constitutional_owner="Analyst Office",
                evaluation_intent=f"Determine deterministic compliance for {name.lower()}",
                evaluation_procedure_reference=f"{identifier}-PROCEDURE",
                dependency_references=("Constitutional Schema Registry", "Certification Evidence Registry", "Version Compatibility Matrix"),
                applicable_candidate_classes=classes,
                required_evidence=("validation evidence", "traceability evidence", "audit evidence"),
                certification_severity=severity,
                version="1.0.0",
                publication_status="Active",
                traceability_references=(f"{identifier}-TRACE",),
                audit_references=(f"{identifier}-AUDIT",),
            )
            for identifier, name, category, severity, classes in rows
        )

    def _schema_registry_entries(self) -> tuple[AnalystRm004SchemaRegistryEntry, ...]:
        rows = (
            ("AS-MIS", "Analytical Mission", "Mission Schemas"),
            ("AS-PLAN", "Analysis Plan", "Mission Schemas"),
            ("AS-PKG", "Analytical Package", "Mission Schemas"),
            ("AS-EVID", "Analytical Evidence", "Evidence Schemas"),
            ("AS-PROV", "Evidence Provenance", "Evidence Schemas"),
            ("AS-EVAL", "Evidence Validation", "Evidence Schemas"),
            ("AS-RG", "Reasoning Graph", "Reasoning Schemas"),
            ("AS-RNODE", "Reasoning Node", "Reasoning Schemas"),
            ("AS-REDGE", "Reasoning Edge", "Reasoning Schemas"),
            ("AS-HYP", "Hypothesis", "Analytical Schemas"),
            ("AS-CONF", "Confidence Object", "Analytical Schemas"),
            ("AS-CONC", "Analytical Conclusion", "Analytical Schemas"),
            ("AS-REC", "Recommendation", "Analytical Schemas"),
            ("AS-OBS", "Organizational Belief State", "Analytical Schemas"),
            ("AS-LIFE", "Lifecycle State", "Lifecycle Schemas"),
            ("AS-COMMIT", "Commit Boundary", "Lifecycle Schemas"),
            ("AS-REPLAY", "Replay State", "Lifecycle Schemas"),
            ("AS-RECOVERY", "Recovery State", "Lifecycle Schemas"),
            ("AS-VREC", "Validation Record", "Validation Schemas"),
            ("AS-VRES", "Validation Result", "Validation Schemas"),
            ("AS-INV", "Invariant Evaluation", "Validation Schemas"),
            ("AS-TRACE", "Trace Record", "Traceability Schemas"),
            ("AS-DEP", "Dependency Record", "Traceability Schemas"),
            ("AS-AUD", "Audit Record", "Traceability Schemas"),
            ("AS-CONFIG", "Configuration Object", "Configuration Schemas"),
            ("AS-CVER", "Configuration Version", "Configuration Schemas"),
            ("AS-COMPAT", "Compatibility Definition", "Configuration Schemas"),
            ("AS-MANIFEST", "Certification Manifest", "Certification Schemas"),
            ("AS-CEPKG", "Certification Evidence Package", "Certification Schemas"),
            ("AS-CTEST", "Certification Test", "Certification Schemas"),
            ("AS-CDEC", "Certification Decision", "Certification Schemas"),
            ("AS-CLOSE", "Certification Closure", "Certification Schemas"),
        )
        return tuple(
            AnalystRm004SchemaRegistryEntry(
                schema_identifier=identifier,
                schema_name=name,
                schema_version="1.0.0",
                schema_class=schema_class,
                canonical_namespace="ANALYST",
                constitutional_owner="Analyst Office",
                approval_authority="Constitutional Governance",
                certification_authority="Independent Enterprise Certification",
                parent_schema=None,
                compatible_schemas=("1.0.0",),
                dependent_schemas=(),
                referenced_registries=("Constitutional Identifier Registry", "Version Compatibility Matrix"),
                certification_status="Specified",
                validation_status="Validated",
                effective_version="1.0.0",
                deprecation_status="Active",
            )
            for identifier, name, schema_class in rows
        )

    def _decision_registry_entries(self) -> tuple[AnalystRm004DecisionRegistryEntry, ...]:
        rows = (
            ("ADR-001", "Authority Certification Decision", "Authority"),
            ("ADR-002", "Identity Certification Decision", "Identity"),
            ("ADR-003", "Object Certification Decision", "Object"),
            ("ADR-004", "Reasoning Certification Decision", "Reasoning"),
            ("ADR-005", "Evidence Certification Decision", "Evidence"),
            ("ADR-006", "Confidence Certification Decision", "Confidence"),
            ("ADR-007", "Validation Certification Decision", "Validation"),
            ("ADR-008", "Persistence Certification Decision", "Persistence"),
            ("ADR-009", "Replay Certification Decision", "Replay"),
            ("ADR-010", "Recovery Certification Decision", "Recovery"),
            ("ADR-011", "Configuration Certification Decision", "Configuration"),
            ("ADR-012", "Certification Closure Decision", "Certification"),
        )
        outcomes = ("PASS", "FAIL", "REJECT", "NOT APPLICABLE")
        return tuple(
            AnalystRm004DecisionRegistryEntry(
                decision_identifier=identifier,
                decision_revision_identifier=f"{identifier}-REV-1",
                decision_name=name,
                decision_category=category,
                owning_office="Analyst Office",
                decision_authority="Independent Enterprise Certification",
                evaluation_authority="Independent Enterprise Certification",
                governing_work_order="ANALYST-RM-004-015",
                constitutional_requirement=f"{category} registry decision",
                trigger_conditions=("certification evaluation requested", "required evidence available"),
                required_inputs=("candidate class", "schema reference", "rule reference", "evidence reference", "version compatibility"),
                required_evidence=("validation evidence", "traceability evidence", "audit evidence"),
                required_dependencies=("Constitutional Rule Registry", "Constitutional Schema Registry", "Certification Evidence Registry"),
                evaluation_rules=(f"CRR-{int(identifier.removeprefix('ADR-')):03d}",),
                required_validation=("authority validation", "evidence validation", "invariant validation"),
                required_invariants=("deterministic outcome", "complete evidence", "complete audit"),
                expected_result="deterministic outcome",
                outcomes=outcomes,
                traceability_references=(f"{identifier}-TRACE", f"{identifier}-AUDIT"),
            )
            for identifier, name, category in rows
        )


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
