"""RISK-RM-004 constitutional certification completion support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


@dataclass(frozen=True)
class RiskCandidateClassRegistryRecord:
    record_identifier: str
    registry_scope: tuple[str, ...]
    schema_sections: Mapping[str, tuple[str, ...]]
    candidate_categories: tuple[str, ...]
    applicability_declarations: tuple[str, ...]
    relationship_requirements: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    persistence_requirements: tuple[str, ...]
    replay_requirements: tuple[str, ...]
    recovery_requirements: tuple[str, ...]
    audit_fields: tuple[str, ...]
    invariants: tuple[str, ...]
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
class RiskIdentityNormalizationTablesRecord:
    record_identifier: str
    normalized_identity_scope: tuple[str, ...]
    canonical_identity_fields: tuple[str, ...]
    identity_classes: tuple[str, ...]
    canonical_naming_rules: tuple[str, ...]
    normalization_table: Mapping[str, str]
    alias_fields: tuple[str, ...]
    namespace_rules: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    conflict_resolution_sequence: tuple[str, ...]
    certification_requirements: tuple[str, ...]
    audit_fields: tuple[str, ...]
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
class RiskEvaluationRuleRegistryRecord:
    record_identifier: str
    rule_schema_fields: tuple[str, ...]
    rule_categories: tuple[str, ...]
    evaluation_order: tuple[str, ...]
    dependency_requirements: tuple[str, ...]
    permitted_outcomes: tuple[str, ...]
    severity_levels: tuple[str, ...]
    lifecycle_states: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    persistence_requirements: tuple[str, ...]
    replay_requirements: tuple[str, ...]
    recovery_requirements: tuple[str, ...]
    invariants: tuple[str, ...]
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
class RiskCertificationThresholdDoctrineRecord:
    record_identifier: str
    decision_classes: tuple[str, ...]
    pass_thresholds: tuple[str, ...]
    conditional_pass_thresholds: tuple[str, ...]
    fail_thresholds: tuple[str, ...]
    incomplete_thresholds: tuple[str, ...]
    admissibility_requirements: tuple[str, ...]
    sufficiency_requirements: tuple[str, ...]
    evaluation_order: tuple[str, ...]
    failure_classes: tuple[str, ...]
    persistence_requirements: tuple[str, ...]
    replay_requirements: tuple[str, ...]
    recovery_requirements: tuple[str, ...]
    audit_fields: tuple[str, ...]
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
class RiskCertificationTestRegistryRecord:
    record_identifier: str
    registry_fields: tuple[str, ...]
    test_categories: tuple[str, ...]
    certification_domains: tuple[str, ...]
    identifier_requirements: tuple[str, ...]
    execution_requirements: tuple[str, ...]
    required_inputs: tuple[str, ...]
    pass_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]
    evidence_fields: tuple[str, ...]
    dependency_requirements: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    replay_requirements: tuple[str, ...]
    recovery_requirements: tuple[str, ...]
    audit_requirements: tuple[str, ...]
    traceability_requirements: tuple[str, ...]
    invariants: tuple[str, ...]
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
class RiskRm004FoundationCertificationPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    candidate_class_registry: RiskCandidateClassRegistryRecord
    identity_normalization: RiskIdentityNormalizationTablesRecord
    evaluation_rule_registry: RiskEvaluationRuleRegistryRecord
    certification_thresholds: RiskCertificationThresholdDoctrineRecord
    certification_test_registry: RiskCertificationTestRegistryRecord
    final_foundation_readiness: EnterpriseCertificationDecision
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


class RiskOfficeCertificationCompletionSupport:
    """Build deterministic RISK-RM-004 certification-completion evidence."""

    foundation_order_coverage = (
        "RISK-RM-004-001",
        "RISK-RM-004-002",
        "RISK-RM-004-003",
        "RISK-RM-004-004",
        "RISK-RM-004-005",
    )

    def build_foundation_package(self) -> RiskRm004FoundationCertificationPackage:
        candidates = self.evaluate_candidate_class_registry()
        identity = self.evaluate_identity_normalization_tables()
        rules = self.evaluate_evaluation_rule_registry()
        thresholds = self.evaluate_certification_thresholds()
        tests = self.evaluate_certification_test_registry()
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (candidates, identity, rules, thresholds, tests)
        ) else EnterpriseCertificationDecision.FAIL
        package = RiskRm004FoundationCertificationPackage(
            package_identifier=f"RISK-RM-004-FOUNDATION-{_digest((candidates, identity, rules, thresholds, tests))[:12].upper()}",
            governing_doctrine="RISK-RM-004-001-TO-005/1.0.0",
            order_coverage=self.foundation_order_coverage,
            candidate_class_registry=candidates,
            identity_normalization=identity,
            evaluation_rule_registry=rules,
            certification_thresholds=thresholds,
            certification_test_registry=tests,
            final_foundation_readiness=final,
            immutable_audit_references=(
                candidates.record_identifier,
                identity.record_identifier,
                rules.record_identifier,
                thresholds.record_identifier,
                tests.record_identifier,
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
    ) -> RiskCandidateClassRegistryRecord:
        scope = ("Risk Assessment", "Risk Evaluation Plan", "Risk Evaluation Package", "Risk Evaluation Graph", "Confidence Assessment", "Exposure Assessment", "Risk Evidence", "Risk Decision", "Mitigation Plan", "Recovery Plan", "Enterprise Risk State", "Configuration Objects", "Validation Records", "Replay Records", "Recovery Records", "Persistent State", "Certification Artifacts", "Registry Objects", "Audit Records")
        sections = MappingProxyType({
            "Canonical Identity": ("Candidate Class Identifier", "Candidate Class Name", "Registry Version", "Constitution Version"),
            "Ownership": ("Constitutional Owner", "Responsible Office", "Certification Authority"),
            "Classification": ("Object Category", "Certification Category", "Certification Scope", "Evaluation Domain"),
            "Applicability": ("Certification Required", "Independent Certification Eligible", "Certification Dependencies", "Required Evidence Classes"),
            "Relationships": ("Parent Candidate Classes", "Dependent Candidate Classes", "Associated Registry Entries", "Schema References"),
            "Audit": ("Registry Revision", "Approval Authority", "Audit References", "Integrity Hash"),
        })
        categories = ("CC-001 Evaluation Objects", "CC-002 Evidence Objects", "CC-003 Decision Objects", "CC-004 Planning Objects", "CC-005 Validation Objects", "CC-006 Infrastructure Objects", "CC-007 Certification Objects")
        applicability = ("certification requirement", "certification scope", "certification dependencies", "mandatory validation requirements", "required certification evidence", "certification completion requirements")
        relationships = ("governing constitutional doctrine", "governing engineering specification", "applicable schema", "applicable validation framework", "certification evidence requirements", "certification procedures")
        validation = ("canonical identity exists", "ownership defined", "category assigned", "certification applicability declared", "required relationships exist", "schema validation succeeds", "integrity verification succeeds")
        persistence = ("candidate identities", "ownership", "classification history", "applicability declarations", "dependency relationships", "audit history", "integrity metadata")
        replay = ("Candidate Class identities", "classifications", "ownership assignments", "applicability declarations", "dependency relationships", "registry versions")
        recovery = ("registry identity", "classification entries", "dependency graph", "audit history", "integrity metadata", "never modify published definitions")
        audit = ("Candidate Class Identifier", "Registry Version", "Event Type", "Timestamp", "Authorizing Doctrine", "Integrity Verification Result")
        invariants = ("exactly one Candidate Class per certifiable artifact", "unique canonical identity", "exactly one owner", "exactly one category", "explicit applicability", "explicit relationships", "immutable published definitions", "replay identical registry semantics", "recovery preserves registry integrity", "independently auditable", "trace to governing doctrine", "no implementation discretion")
        passed = not duplicate_identifier_findings and not multiple_classification_findings and not missing_owner_findings and not incomplete_applicability_findings and not dependency_graph_findings and not invalid_schema_reference_findings and not replay_inconsistency_findings and not invariant_violations
        record = RiskCandidateClassRegistryRecord(
            record_identifier=f"RISK-RM-004-001-CANDIDATE-{_digest((scope, categories))[:12].upper()}",
            registry_scope=scope,
            schema_sections=sections,
            candidate_categories=categories,
            applicability_declarations=applicability,
            relationship_requirements=relationships,
            validation_requirements=validation,
            persistence_requirements=persistence,
            replay_requirements=replay,
            recovery_requirements=recovery,
            audit_fields=audit,
            invariants=invariants,
            duplicate_identifier_findings=duplicate_identifier_findings,
            multiple_classification_findings=multiple_classification_findings,
            missing_owner_findings=missing_owner_findings,
            incomplete_applicability_findings=incomplete_applicability_findings,
            dependency_graph_findings=dependency_graph_findings,
            invalid_schema_reference_findings=invalid_schema_reference_findings,
            replay_inconsistency_findings=replay_inconsistency_findings,
            invariant_violations=invariant_violations,
            result=EnterpriseCertificationDecision.PASS if passed else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(record))

    def evaluate_identity_normalization_tables(
        self,
        *,
        duplicate_canonical_identity_findings: tuple[str, ...] = (),
        ambiguous_alias_findings: tuple[str, ...] = (),
        namespace_reuse_findings: tuple[str, ...] = (),
        normalization_drift_findings: tuple[str, ...] = (),
        equivalence_rule_findings: tuple[str, ...] = (),
        traceability_gaps: tuple[str, ...] = (),
        audit_gaps: tuple[str, ...] = (),
    ) -> RiskIdentityNormalizationTablesRecord:
        scope = ("constitutional object identifiers", "certification identifiers", "evidence identifiers", "registry identifiers", "schema identifiers", "rule identifiers", "evaluation identifiers", "lifecycle identifiers", "configuration identifiers", "version identifiers")
        fields_required = ("Canonical Identifier", "Canonical Name", "Object Type", "Owning Office", "Namespace", "Version", "Alias References", "Normalization Rule Identifier", "Integrity Hash")
        classes = tuple(f"IC-{index:03d}" for index in range(1, 11))
        naming = ("globally unique", "immutable", "deterministic", "human readable", "machine verifiable", "namespace qualified", "never reused")
        table = MappingProxyType({
            "Canonical Identifier": "Preserve unchanged",
            "Registered Alias": "Resolve to canonical identifier",
            "Historical Identifier": "Resolve to canonical identifier",
            "Approved Legacy Name": "Resolve to canonical name",
            "Namespace-qualified Identifier": "Preserve canonical namespace",
            "Case variation": "Normalize to canonical case",
            "Whitespace variation": "Normalize to canonical formatting",
        })
        aliases = ("Alias Identifier", "Canonical Identifier", "Alias Classification", "Creation Authority", "Approval Record", "Retirement Status")
        namespaces = ("immutable", "non-overlapping", "globally unique", "permanently reserved", "cross-namespace normalization prohibited")
        validation = ("identifier syntax", "namespace validity", "ownership", "uniqueness", "registry existence", "version compatibility", "integrity hash")
        conflicts = ("Resolve aliases", "Resolve legacy identifiers", "Resolve namespace formatting", "Validate canonical ownership", "Preserve canonical identifier", "Reject unresolved ambiguity")
        certification = ("every identifier normalizes successfully", "every alias resolves uniquely", "canonical names exist within Identifier Registry", "no duplicate canonical identities")
        audit = ("Normalization Identifier", "Original Identity", "Canonical Identity", "Applied Rule", "Alias Resolution", "Validation Results", "Timestamp", "Integrity Hash")
        invariants = tuple(f"CI-{index:03d}" for index in range(1, 11)) + ("one canonical identity", "ownership preserved", "aliases resolve uniquely", "certification evaluates canonical identities only")
        passed = not duplicate_canonical_identity_findings and not ambiguous_alias_findings and not namespace_reuse_findings and not normalization_drift_findings and not equivalence_rule_findings and not traceability_gaps and not audit_gaps
        record = RiskIdentityNormalizationTablesRecord(
            record_identifier=f"RISK-RM-004-002-IDENTITY-{_digest((scope, fields_required, table))[:12].upper()}",
            normalized_identity_scope=scope,
            canonical_identity_fields=fields_required,
            identity_classes=classes,
            canonical_naming_rules=naming,
            normalization_table=table,
            alias_fields=aliases,
            namespace_rules=namespaces,
            validation_requirements=validation,
            conflict_resolution_sequence=conflicts,
            certification_requirements=certification,
            audit_fields=audit,
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
    ) -> RiskEvaluationRuleRegistryRecord:
        schema = ("Rule Identifier", "Rule Name", "Rule Version", "Constitutional Requirement", "Evaluation Scope", "Required Evidence", "Evaluation Procedure", "Dependency List", "Expected Result", "Failure Criteria", "Severity", "Traceability References", "Audit Requirements", "Effective Version", "Integrity Hash")
        categories = ("Authority Rules", "Object Rules", "Input Rules", "Output Rules", "Lifecycle Rules", "Validation Rules", "Decision Rules", "Persistence Rules", "Replay Rules", "Recovery Rules", "Configuration Rules", "Traceability Rules", "Registry Rules", "Invariant Rules")
        order = categories
        dependencies = ("prerequisite rules", "required evidence", "required registries", "required schemas", "required configuration versions", "no implicit dependencies")
        outcomes = ("PASS", "FAIL", "NOT APPLICABLE")
        severities = ("Critical", "Major", "Minor", "Informational")
        states = ("Draft", "Validated", "Approved", "Active", "Superseded", "Archived")
        validation = ("schema compliance", "identifier uniqueness", "dependency integrity", "traceability completeness", "constitutional consistency", "version compatibility")
        persistence = ("every rule", "historical revisions", "execution history", "compatibility declarations", "dependency metadata", "audit evidence")
        replay = ("identical rule versions employed during original certification", "rule substitution prohibited")
        recovery = ("active registry", "historical registry", "rule versions", "dependencies", "execution ordering", "no inference")
        invariants = tuple(f"CI-{index:03d}" for index in range(1, 11)) + ("no unregistered certification rules", "immutable evaluation order", "deterministic outcomes")
        passed = not duplicate_rule_findings and not missing_rule_findings and not invalid_outcome_findings and not dependency_cycle_findings and not registry_ambiguity_findings and not replay_divergence_findings and not recovery_gaps and not audit_gaps
        record = RiskEvaluationRuleRegistryRecord(
            record_identifier=f"RISK-RM-004-003-RULES-{_digest((schema, categories))[:12].upper()}",
            rule_schema_fields=schema,
            rule_categories=categories,
            evaluation_order=order,
            dependency_requirements=dependencies,
            permitted_outcomes=outcomes,
            severity_levels=severities,
            lifecycle_states=states,
            validation_requirements=validation,
            persistence_requirements=persistence,
            replay_requirements=replay,
            recovery_requirements=recovery,
            invariants=invariants,
            duplicate_rule_findings=duplicate_rule_findings,
            missing_rule_findings=missing_rule_findings,
            invalid_outcome_findings=invalid_outcome_findings,
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
    ) -> RiskCertificationThresholdDoctrineRecord:
        decisions = ("PASS", "CONDITIONAL PASS", "FAIL", "INCOMPLETE")
        pass_thresholds = ("every mandatory constitutional doctrine implemented", "every invariant satisfied", "every certification test passed", "every mandatory registry complete", "every schema validated", "every identifier verified", "every audit completed", "every replay test successful", "every recovery test successful", "complete traceability", "no unresolved findings")
        conditional = ("mandatory behavior compliant", "remaining findings are non-constitutional administrative deficiencies", "constitutional correctness unaffected", "deterministic execution preserved", "conditions documented")
        fail = ("invariant violation", "ownership violation", "authority violation", "deterministic execution failure", "validation failure", "replay failure", "recovery failure", "traceability failure", "incomplete evidence", "registry inconsistency", "schema incompatibility", "constitutional ambiguity")
        incomplete = ("required evidence unavailable", "required testing incomplete", "mandatory artifacts absent", "evaluation cannot proceed deterministically")
        admissibility = ("certification package completeness", "evidence admissibility", "identifier validity", "schema compatibility", "registry availability", "configuration compatibility", "doctrine version compatibility")
        sufficiency = ("constitutional compliance", "deterministic execution", "complete ownership", "complete traceability", "complete validation", "replay equivalence", "recovery equivalence", "audit completeness")
        order = ("Certification Package Verification", "Identity Verification", "Schema Verification", "Registry Verification", "Configuration Compatibility", "Evidence Admissibility", "Evidence Sufficiency", "Rule Compliance", "Validation Compliance", "Lifecycle Compliance", "Persistence Compliance", "Replay Compliance", "Recovery Compliance", "Traceability Compliance", "Constitutional Invariant Compliance", "Certification Decision")
        failures = ("Evidence Failure", "Identity Failure", "Schema Failure", "Registry Failure", "Validation Failure", "Determinism Failure", "Replay Failure", "Recovery Failure", "Traceability Failure", "Invariant Failure", "Certification Package Failure")
        persistence = ("evaluated thresholds", "supporting evidence", "evaluation results", "failure classifications", "audit references", "certification outcome")
        replay = ("identical threshold ordering", "identical evaluation results", "identical certification outcome", "identical supporting evidence", "identical failure classifications")
        recovery = ("threshold evaluation state", "certification evidence", "evaluation history", "certification outcome", "audit history")
        audit = ("Certification Identifier", "Threshold Identifier", "Evaluation Timestamp", "Evaluation Authority", "Supporting Evidence", "Evaluation Result", "Failure Classification", "Final Certification Decision")
        invariants = ("deterministic decisions", "immutable thresholds", "PASS requires complete compliance", "FAIL from mandatory violation", "CONDITIONAL PASS never conceals deficiencies", "INCOMPLETE is not certification result", "complete evidence before evaluation", "deterministic ordering", "independently reproducible", "replay identical decisions", "recovery preserves decisions", "complete traceability", "independently auditable", "immutable history", "no subjective interpretation")
        passed = not missing_threshold_classes and not invalid_outcome_findings and not weak_mandatory_threshold_findings and not blocking_threshold_bypass_findings and not traceability_gaps and not audit_gaps
        record = RiskCertificationThresholdDoctrineRecord(
            record_identifier=f"RISK-RM-004-004-THRESHOLDS-{_digest((decisions, order, failures))[:12].upper()}",
            decision_classes=decisions,
            pass_thresholds=pass_thresholds,
            conditional_pass_thresholds=conditional,
            fail_thresholds=fail,
            incomplete_thresholds=incomplete,
            admissibility_requirements=admissibility,
            sufficiency_requirements=sufficiency,
            evaluation_order=order,
            failure_classes=failures,
            persistence_requirements=persistence,
            replay_requirements=replay,
            recovery_requirements=recovery,
            audit_fields=audit,
            invariants=invariants,
            missing_threshold_classes=missing_threshold_classes,
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
    ) -> RiskCertificationTestRegistryRecord:
        fields_required = ("Test Identifier", "Test Name", "Constitutional Domain", "Governing Doctrine", "Governing Requirement", "Test Category", "Test Purpose", "Required Inputs", "Required Evidence", "Execution Procedure", "Expected Results", "Pass Criteria", "Failure Criteria", "Generated Evidence", "Audit Requirements", "Execution Dependencies", "Replay Requirements", "Recovery Requirements", "Registry Version", "Status")
        categories = ("Authority Verification", "Ownership Verification", "Identity Verification", "Object Verification", "Lifecycle Verification", "Validation Verification", "Decision Verification", "Persistence Verification", "Replay Verification", "Recovery Verification", "Configuration Verification", "Traceability Verification", "Registry Verification", "Schema Verification", "Evidence Verification", "Invariant Verification", "Certification Artifact Verification")
        domains = ("Office Authority", "Constitutional Objects", "Canonical Identity", "Inputs", "Outputs", "Ownership", "Lifecycles", "Validation", "Deterministic Decisions", "Persistence", "Replay", "Recovery", "Configuration", "Traceability", "Registries", "Certification Artifacts", "Constitutional Invariants")
        identifier = ("exactly one immutable identifier", "exactly one registry entry", "exactly one governing doctrine", "exactly one constitutional owner", "identifier reuse prohibited")
        execution = ("deterministic", "independent", "reproducible", "without implementation interpretation", "using immutable certification evidence")
        inputs = ("constitutional objects", "evidence", "manifests", "registries", "schemas", "configuration versions", "doctrine versions")
        pass_criteria = ("complete evidence", "successful validation", "invariant preservation", "deterministic behavior", "successful dependency verification", "successful audit generation")
        failure_criteria = ("constitutional violations", "missing evidence", "validation failure", "invariant violation", "replay divergence", "recovery inconsistency", "traceability deficiency", "registry inconsistency", "schema incompatibility")
        evidence = ("Test Identifier", "Execution Identifier", "Execution Timestamp", "Constitutional Version", "Registry Version", "Test Result", "Supporting Evidence", "Validation Results", "Audit References", "Certification References")
        dependencies = ("prerequisite tests", "prerequisite evidence", "prerequisite registries", "prerequisite schemas", "prerequisite validation results", "acyclic dependencies")
        validation = ("identifier uniqueness", "doctrine references", "complete test definitions", "dependency integrity", "evidence completeness", "audit completeness", "version compatibility")
        replay = ("identical certification tests", "identical execution sequence", "identical evidence", "identical pass/fail results", "identical audit records")
        recovery = ("registry contents", "execution history", "evidence", "dependency relationships", "audit records", "certification status")
        audit = ("execution sequence", "evaluated doctrine", "evaluated objects", "generated evidence", "detected failures", "certification result", "audit completion")
        traceability = ("governing doctrine", "governing work order", "evaluated constitutional objects", "supporting evidence", "validation results", "replay evidence", "recovery evidence", "certification package", "certification manifest")
        invariants = ("one immutable test identifier", "one category per test", "every requirement has tests", "deterministic execution", "immutable evidence", "complete audit evidence", "replay identical results", "recovery preserves history", "immutable registry history", "fully traceable", "acyclic dependencies", "PASS satisfies criteria", "FAIL satisfies criteria", "tests never modify constitutional objects", "complete registry contents")
        passed = not duplicate_test_findings and not missing_category_findings and not missing_requirement_coverage and not nondeterministic_execution_findings and not missing_evidence_findings and not dependency_cycle_findings and not replay_divergence_findings and not recovery_gaps and not audit_gaps
        record = RiskCertificationTestRegistryRecord(
            record_identifier=f"RISK-RM-004-005-TESTS-{_digest((fields_required, categories, domains))[:12].upper()}",
            registry_fields=fields_required,
            test_categories=categories,
            certification_domains=domains,
            identifier_requirements=identifier,
            execution_requirements=execution,
            required_inputs=inputs,
            pass_criteria=pass_criteria,
            failure_criteria=failure_criteria,
            evidence_fields=evidence,
            dependency_requirements=dependencies,
            validation_requirements=validation,
            replay_requirements=replay,
            recovery_requirements=recovery,
            audit_requirements=audit,
            traceability_requirements=traceability,
            invariants=invariants,
            duplicate_test_findings=duplicate_test_findings,
            missing_category_findings=missing_category_findings,
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
