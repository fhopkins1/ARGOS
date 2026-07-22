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
