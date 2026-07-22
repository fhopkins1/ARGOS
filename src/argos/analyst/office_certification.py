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


class AnalystOfficeCertificationSupport:
    """Build deterministic ANALYST-RM-004 certification registry evidence."""

    order_coverage = (
        "ANALYST-RM-004-001",
        "ANALYST-RM-004-002",
        "ANALYST-RM-004-003",
        "ANALYST-RM-004-004",
        "ANALYST-RM-004-005",
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
