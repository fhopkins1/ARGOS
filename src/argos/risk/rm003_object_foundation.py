"""Operational RISK-RM-003 object-foundation support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


RISK_OWNER = "Risk Office"
CONSTITUTIONAL_VERSION = "RISK-RM-003/1.0.0"
SCHEMA_VERSION = "risk-rm003-object-foundation.v1"
EVIDENCE_TIMESTAMP = "2026-07-22T00:00:00Z"


def _jsonable(value: Any) -> Any:
    if isinstance(value, EnterpriseCertificationDecision):
        return value.value
    if is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _freeze_mapping(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted(values.items())))


def _decision(findings: tuple[str, ...]) -> EnterpriseCertificationDecision:
    return EnterpriseCertificationDecision.PASS if not findings else EnterpriseCertificationDecision.FAIL


@dataclass(frozen=True)
class RiskEvaluationMissionObject:
    mission_identifier: str
    mission_class: str
    constitutional_owner: str
    constitutional_version: str
    schema_version: str
    mission_version: str
    creation_timestamp: str
    lifecycle_state: str
    evaluation_scope_identifier: str
    workflow_execution_token: str
    relationships: Mapping[str, str]
    execution_constraints: tuple[str, ...]
    completion_contract: tuple[str, ...]
    authority_relinquished: bool
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskEvaluationPackageObject:
    package_identifier: str
    mission_identifier: str
    assessment_identifier: str
    constitutional_owner: str
    constitutional_version: str
    schema_version: str
    creation_timestamp: str
    completion_timestamp: str
    producing_authority: str
    package_sections: Mapping[str, tuple[str, ...]]
    validation_records: tuple[str, ...]
    traceability_records: tuple[str, ...]
    audit_records: tuple[str, ...]
    integrity_hash: str
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskEvaluationGraphNode:
    node_identifier: str
    node_class: str
    owning_object_identifier: str


@dataclass(frozen=True)
class RiskEvaluationGraphEdge:
    source_identifier: str
    target_identifier: str
    edge_type: str


@dataclass(frozen=True)
class RiskEvaluationGraphObject:
    graph_identifier: str
    mission_identifier: str
    package_identifier: str
    workflow_execution_token: str
    constitutional_owner: str
    graph_version: str
    schema_version: str
    creation_timestamp: str
    validation_timestamp: str
    nodes: tuple[RiskEvaluationGraphNode, ...]
    edges: tuple[RiskEvaluationGraphEdge, ...]
    topological_order: tuple[str, ...]
    integrity_hash: str
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskAssessmentCanonicalObject:
    assessment_identifier: str
    mission_identifier: str
    package_identifier: str
    graph_identifier: str
    execution_token_identifier: str
    enterprise_identifier: str
    constitutional_owner: str
    constitutional_version: str
    schema_version: str
    creation_timestamp: str
    completion_timestamp: str
    enterprise_risk_classification: str
    confidence_identifier: str
    exposure_identifier: str
    mitigation_identifiers: tuple[str, ...]
    recovery_identifiers: tuple[str, ...]
    supporting_evidence_references: tuple[str, ...]
    validation_references: tuple[str, ...]
    provenance_references: tuple[str, ...]
    traceability_references: tuple[str, ...]
    audit_references: tuple[str, ...]
    integrity_hash: str
    lifecycle_state: str
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskObjectLifecycleProfile:
    profile_identifier: str
    object_identifier: str
    object_class: str
    constitutional_owner: str
    current_state: str
    allowed_states: tuple[str, ...]
    terminal_states: tuple[str, ...]
    legal_transitions: tuple[tuple[str, str], ...]
    transition_history: tuple[tuple[str, str, str, str], ...]
    audit_references: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm003ObjectFoundationOperationalPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    candidate_identifier: str
    mission: RiskEvaluationMissionObject
    evaluation_package: RiskEvaluationPackageObject
    evaluation_graph: RiskEvaluationGraphObject
    risk_assessment: RiskAssessmentCanonicalObject
    lifecycle_profiles: tuple[RiskObjectLifecycleProfile, ...]
    replay_digest: str
    immutable_audit_references: tuple[str, ...]
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm003ObjectFoundationSupport:
    """Build deterministic operational evidence for RISK-RM-003-001 through 005."""

    order_coverage = (
        "RISK-RM-003-001",
        "RISK-RM-003-002",
        "RISK-RM-003-003",
        "RISK-RM-003-004",
        "RISK-RM-003-005",
    )

    lifecycle_states = (
        "Created",
        "Initialized",
        "Validated",
        "Active",
        "Revised",
        "Superseded",
        "Archived",
        "Retired",
        "Constitutionally Destroyed",
        "Rejected",
        "Invalidated",
    )
    terminal_states = ("Rejected", "Invalidated", "Constitutionally Destroyed")
    legal_transitions = (
        ("Created", "Initialized"),
        ("Initialized", "Validated"),
        ("Validated", "Active"),
        ("Validated", "Rejected"),
        ("Active", "Revised"),
        ("Revised", "Active"),
        ("Active", "Superseded"),
        ("Superseded", "Archived"),
        ("Archived", "Retired"),
        ("Retired", "Constitutionally Destroyed"),
        ("Active", "Invalidated"),
        ("Invalidated", "Archived"),
    )

    def build_operational_package(self, *, candidate_identifier: str = "RISK-RM-003-001-TO-005-CANDIDATE") -> RiskRm003ObjectFoundationOperationalPackage:
        mission = self.evaluate_mission()
        evaluation_package = self.evaluate_package(mission_identifier=mission.mission_identifier)
        graph = self.evaluate_graph(
            mission_identifier=mission.mission_identifier,
            package_identifier=evaluation_package.package_identifier,
            workflow_execution_token=mission.workflow_execution_token,
        )
        assessment = self.evaluate_assessment(
            mission_identifier=mission.mission_identifier,
            package_identifier=evaluation_package.package_identifier,
            graph_identifier=graph.graph_identifier,
            execution_token_identifier=mission.workflow_execution_token,
        )
        lifecycle_profiles = (
            self.evaluate_lifecycle_profile(object_identifier=mission.mission_identifier, object_class="Risk Evaluation Mission", current_state="Active"),
            self.evaluate_lifecycle_profile(object_identifier=evaluation_package.package_identifier, object_class="Risk Evaluation Package", current_state="Active"),
            self.evaluate_lifecycle_profile(object_identifier=graph.graph_identifier, object_class="Risk Evaluation Graph", current_state="Active"),
            self.evaluate_lifecycle_profile(object_identifier=assessment.assessment_identifier, object_class="Risk Assessment", current_state="Active"),
        )
        final = EnterpriseCertificationDecision.PASS if all(
            record.result == EnterpriseCertificationDecision.PASS
            for record in (mission, evaluation_package, graph, assessment, *lifecycle_profiles)
        ) else EnterpriseCertificationDecision.FAIL
        replay_digest = _digest((mission, evaluation_package, graph, assessment, lifecycle_profiles))
        package = RiskRm003ObjectFoundationOperationalPackage(
            package_identifier=f"RISK-RM-003-OBJECT-FOUNDATION-{replay_digest[:12].upper()}",
            governing_doctrine="RISK-RM-003-001-TO-005/1.0.0",
            order_coverage=self.order_coverage,
            candidate_identifier=candidate_identifier,
            mission=mission,
            evaluation_package=evaluation_package,
            evaluation_graph=graph,
            risk_assessment=assessment,
            lifecycle_profiles=lifecycle_profiles,
            replay_digest=replay_digest,
            immutable_audit_references=(
                mission.mission_identifier,
                evaluation_package.package_identifier,
                graph.graph_identifier,
                assessment.assessment_identifier,
                *(profile.profile_identifier for profile in lifecycle_profiles),
            ),
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_mission(
        self,
        *,
        mission_identifier: str = "RISK-MISSION-RM003-001",
        constitutional_owner: str = RISK_OWNER,
        workflow_execution_token: str = "WF-RISK-RM003-OBJECT-FOUNDATION",
        evaluation_scope_identifier: str = "ENTERPRISE-RISK-SCOPE-RM003",
        relationships: Mapping[str, str] | None = None,
        authority_relinquished: bool = True,
        findings: tuple[str, ...] = (),
    ) -> RiskEvaluationMissionObject:
        relationships = relationships or {
            "risk_assessment": "RISK-ASSESSMENT-RM003-001",
            "risk_evaluation_package": "RISK-PACKAGE-RM003-001",
            "risk_evaluation_graph": "RISK-GRAPH-RM003-001",
            "confidence_assessment": "CONFIDENCE-RM003-001",
            "exposure_assessment": "EXPOSURE-RM003-001",
            "risk_decision": "RISK-DECISION-RM003-001",
            "audit_record_set": "RISK-AUDIT-RM003-001",
        }
        derived_findings = list(findings)
        if constitutional_owner != RISK_OWNER:
            derived_findings.append("mission constitutional owner is not Risk Office")
        if not mission_identifier:
            derived_findings.append("mission identifier missing")
        if not workflow_execution_token:
            derived_findings.append("workflow execution token missing")
        if not evaluation_scope_identifier:
            derived_findings.append("evaluation scope identifier missing")
        required_relationships = {"risk_assessment", "risk_evaluation_package", "risk_evaluation_graph", "confidence_assessment", "exposure_assessment", "risk_decision", "audit_record_set"}
        missing = sorted(required_relationships.difference(relationships))
        derived_findings.extend(f"mission relationship missing: {item}" for item in missing)
        if not authority_relinquished:
            derived_findings.append("mission completion did not relinquish constitutional authority")
        result = _decision(tuple(derived_findings))
        mission = RiskEvaluationMissionObject(
            mission_identifier=mission_identifier,
            mission_class="Enterprise Risk Evaluation",
            constitutional_owner=constitutional_owner,
            constitutional_version=CONSTITUTIONAL_VERSION,
            schema_version=SCHEMA_VERSION,
            mission_version="1.0.0",
            creation_timestamp=EVIDENCE_TIMESTAMP,
            lifecycle_state="Active",
            evaluation_scope_identifier=evaluation_scope_identifier,
            workflow_execution_token=workflow_execution_token,
            relationships=_freeze_mapping(relationships),
            execution_constraints=("deterministic execution only", "single constitutional owner", "immutable evaluation scope", "fail-closed behavior", "validation before completion"),
            completion_contract=("all stages completed", "required evidence evaluated", "one Risk Assessment accepted", "one Risk Decision issued", "audit evidence finalized", "authority relinquished"),
            authority_relinquished=authority_relinquished,
            findings=tuple(derived_findings),
            result=result,
            deterministic_digest="",
        )
        return replace(mission, deterministic_digest=_digest(mission))

    def evaluate_package(
        self,
        *,
        package_identifier: str = "RISK-PACKAGE-RM003-001",
        mission_identifier: str = "RISK-MISSION-RM003-001",
        assessment_identifier: str = "RISK-ASSESSMENT-RM003-001",
        package_sections: Mapping[str, tuple[str, ...]] | None = None,
        validation_records: tuple[str, ...] = ("schema validation", "ownership validation", "integrity validation", "traceability validation", "replay validation"),
        traceability_records: tuple[str, ...] = ("provenance graph", "dependency graph", "object relationships", "certification references"),
        audit_records: tuple[str, ...] = ("evaluation audit", "replay audit", "recovery audit", "certification audit"),
        findings: tuple[str, ...] = (),
    ) -> RiskEvaluationPackageObject:
        package_sections = package_sections or _required_package_sections()
        derived_findings = list(findings)
        required_sections = set(_required_package_sections())
        missing_sections = sorted(required_sections.difference(package_sections))
        derived_findings.extend(f"package section missing: {section}" for section in missing_sections)
        if not mission_identifier:
            derived_findings.append("package mission identifier missing")
        if not assessment_identifier:
            derived_findings.append("package assessment identifier missing")
        for required_validation in ("schema validation", "ownership validation", "integrity validation", "traceability validation", "replay validation"):
            if required_validation not in validation_records:
                derived_findings.append(f"package validation missing: {required_validation}")
        for required_trace in ("provenance graph", "dependency graph", "object relationships", "certification references"):
            if required_trace not in traceability_records:
                derived_findings.append(f"package traceability missing: {required_trace}")
        if len(audit_records) < 4:
            derived_findings.append("package audit records incomplete")
        integrity_hash = _digest((package_identifier, mission_identifier, assessment_identifier, package_sections, validation_records, traceability_records, audit_records))
        package = RiskEvaluationPackageObject(
            package_identifier=package_identifier,
            mission_identifier=mission_identifier,
            assessment_identifier=assessment_identifier,
            constitutional_owner=RISK_OWNER,
            constitutional_version=CONSTITUTIONAL_VERSION,
            schema_version=SCHEMA_VERSION,
            creation_timestamp=EVIDENCE_TIMESTAMP,
            completion_timestamp=EVIDENCE_TIMESTAMP,
            producing_authority="Risk Evaluation Mission",
            package_sections=_freeze_mapping(package_sections),
            validation_records=validation_records,
            traceability_records=traceability_records,
            audit_records=audit_records,
            integrity_hash=integrity_hash,
            findings=tuple(derived_findings),
            result=_decision(tuple(derived_findings)),
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def evaluate_graph(
        self,
        *,
        graph_identifier: str = "RISK-GRAPH-RM003-001",
        mission_identifier: str = "RISK-MISSION-RM003-001",
        package_identifier: str = "RISK-PACKAGE-RM003-001",
        workflow_execution_token: str = "WF-RISK-RM003-OBJECT-FOUNDATION",
        nodes: tuple[RiskEvaluationGraphNode, ...] | None = None,
        edges: tuple[RiskEvaluationGraphEdge, ...] | None = None,
        findings: tuple[str, ...] = (),
    ) -> RiskEvaluationGraphObject:
        nodes = nodes or _default_graph_nodes()
        edges = edges or _default_graph_edges()
        derived_findings = list(findings)
        node_ids = tuple(node.node_identifier for node in nodes)
        if len(node_ids) != len(set(node_ids)):
            derived_findings.append("graph contains duplicate node identifiers")
        allowed_node_classes = {
            "Evidence Node",
            "Validation Node",
            "Exposure Node",
            "Confidence Node",
            "Risk Assessment Node",
            "Mitigation Node",
            "Recovery Node",
            "Enterprise Risk Node",
        }
        allowed_edge_types = {"DEPENDS_ON", "DERIVED_FROM", "VALIDATED_BY", "SUPPORTS", "PROPAGATES_TO", "MITIGATES", "RECOVERS", "AGGREGATES", "SUPERSEDES"}
        for node in nodes:
            if node.node_class not in allowed_node_classes:
                derived_findings.append(f"unauthorized graph node class: {node.node_class}")
        for edge in edges:
            if edge.edge_type not in allowed_edge_types:
                derived_findings.append(f"unauthorized graph edge type: {edge.edge_type}")
            if edge.source_identifier not in node_ids or edge.target_identifier not in node_ids:
                derived_findings.append(f"graph edge references missing node: {edge.source_identifier}->{edge.target_identifier}")
        enterprise_nodes = tuple(node for node in nodes if node.node_class == "Enterprise Risk Node")
        if len(enterprise_nodes) != 1:
            derived_findings.append("graph does not contain exactly one Enterprise Risk node")
        topological_order, cycle_findings = _topological_order(nodes, edges)
        derived_findings.extend(cycle_findings)
        if len(topological_order) != len(nodes):
            derived_findings.append("graph is not fully connected through deterministic ordering")
        integrity_hash = _digest((graph_identifier, mission_identifier, package_identifier, workflow_execution_token, nodes, edges, topological_order))
        graph = RiskEvaluationGraphObject(
            graph_identifier=graph_identifier,
            mission_identifier=mission_identifier,
            package_identifier=package_identifier,
            workflow_execution_token=workflow_execution_token,
            constitutional_owner=RISK_OWNER,
            graph_version="1.0.0",
            schema_version=SCHEMA_VERSION,
            creation_timestamp=EVIDENCE_TIMESTAMP,
            validation_timestamp=EVIDENCE_TIMESTAMP,
            nodes=nodes,
            edges=edges,
            topological_order=topological_order,
            integrity_hash=integrity_hash,
            findings=tuple(derived_findings),
            result=_decision(tuple(derived_findings)),
            deterministic_digest="",
        )
        return replace(graph, deterministic_digest=_digest(graph))

    def evaluate_assessment(
        self,
        *,
        assessment_identifier: str = "RISK-ASSESSMENT-RM003-001",
        mission_identifier: str = "RISK-MISSION-RM003-001",
        package_identifier: str = "RISK-PACKAGE-RM003-001",
        graph_identifier: str = "RISK-GRAPH-RM003-001",
        execution_token_identifier: str = "WF-RISK-RM003-OBJECT-FOUNDATION",
        supporting_evidence_references: tuple[str, ...] = ("RISK-EVIDENCE-RM003-001", "RISK-EVIDENCE-RM003-002"),
        validation_references: tuple[str, ...] = ("RISK-VALIDATION-RM003-001",),
        provenance_references: tuple[str, ...] = ("RISK-PROVENANCE-RM003-001",),
        traceability_references: tuple[str, ...] = ("RISK-TRACE-RM003-001",),
        audit_references: tuple[str, ...] = ("RISK-AUDIT-RM003-001",),
        findings: tuple[str, ...] = (),
    ) -> RiskAssessmentCanonicalObject:
        derived_findings = list(findings)
        required_ids = {
            "assessment identifier": assessment_identifier,
            "mission identifier": mission_identifier,
            "package identifier": package_identifier,
            "graph identifier": graph_identifier,
            "execution token identifier": execution_token_identifier,
        }
        for name, value in required_ids.items():
            if not value:
                derived_findings.append(f"assessment {name} missing")
        for label, values in (
            ("supporting evidence", supporting_evidence_references),
            ("validation reference", validation_references),
            ("provenance reference", provenance_references),
            ("traceability reference", traceability_references),
            ("audit reference", audit_references),
        ):
            if not values:
                derived_findings.append(f"assessment {label} missing")
        integrity_hash = _digest((assessment_identifier, mission_identifier, package_identifier, graph_identifier, supporting_evidence_references, validation_references, provenance_references, traceability_references, audit_references))
        assessment = RiskAssessmentCanonicalObject(
            assessment_identifier=assessment_identifier,
            mission_identifier=mission_identifier,
            package_identifier=package_identifier,
            graph_identifier=graph_identifier,
            execution_token_identifier=execution_token_identifier,
            enterprise_identifier="ARGOS-ENTERPRISE",
            constitutional_owner=RISK_OWNER,
            constitutional_version=CONSTITUTIONAL_VERSION,
            schema_version=SCHEMA_VERSION,
            creation_timestamp=EVIDENCE_TIMESTAMP,
            completion_timestamp=EVIDENCE_TIMESTAMP,
            enterprise_risk_classification="ENTERPRISE_RISK_ACCEPTABLE_WITH_CONTROLS",
            confidence_identifier="CONFIDENCE-RM003-001",
            exposure_identifier="EXPOSURE-RM003-001",
            mitigation_identifiers=("MITIGATION-RM003-001",),
            recovery_identifiers=("RECOVERY-RM003-001",),
            supporting_evidence_references=supporting_evidence_references,
            validation_references=validation_references,
            provenance_references=provenance_references,
            traceability_references=traceability_references,
            audit_references=audit_references,
            integrity_hash=integrity_hash,
            lifecycle_state="Active",
            findings=tuple(derived_findings),
            result=_decision(tuple(derived_findings)),
            deterministic_digest="",
        )
        return replace(assessment, deterministic_digest=_digest(assessment))

    def evaluate_lifecycle_profile(
        self,
        *,
        object_identifier: str = "RISK-ASSESSMENT-RM003-001",
        object_class: str = "Risk Assessment",
        current_state: str = "Active",
        transition_history: tuple[tuple[str, str, str, str], ...] | None = None,
        audit_references: tuple[str, ...] = ("RISK-LIFECYCLE-AUDIT-RM003-001",),
        findings: tuple[str, ...] = (),
    ) -> RiskObjectLifecycleProfile:
        transition_history = transition_history or (
            ("Created", "Initialized", "Risk Office", "RISK-LIFECYCLE-AUDIT-CREATED"),
            ("Initialized", "Validated", "Risk Office", "RISK-LIFECYCLE-AUDIT-VALIDATED"),
            ("Validated", "Active", "Risk Office", "RISK-LIFECYCLE-AUDIT-ACTIVE"),
        )
        derived_findings = list(findings)
        if current_state not in self.lifecycle_states:
            derived_findings.append(f"lifecycle state unauthorized: {current_state}")
        for source, target, authority, audit_reference in transition_history:
            if (source, target) not in self.legal_transitions:
                derived_findings.append(f"illegal lifecycle transition: {source}->{target}")
            if authority != RISK_OWNER:
                derived_findings.append(f"transition authority invalid: {source}->{target}")
            if not audit_reference:
                derived_findings.append(f"transition audit reference missing: {source}->{target}")
        if not audit_references:
            derived_findings.append("lifecycle audit references missing")
        if object_class not in _covered_lifecycle_objects():
            derived_findings.append(f"lifecycle object class outside Risk-owned scope: {object_class}")
        profile = RiskObjectLifecycleProfile(
            profile_identifier=f"RISK-LIFECYCLE-{object_identifier}",
            object_identifier=object_identifier,
            object_class=object_class,
            constitutional_owner=RISK_OWNER,
            current_state=current_state,
            allowed_states=self.lifecycle_states,
            terminal_states=self.terminal_states,
            legal_transitions=self.legal_transitions,
            transition_history=transition_history,
            audit_references=audit_references,
            findings=tuple(derived_findings),
            result=_decision(tuple(derived_findings)),
            deterministic_digest="",
        )
        return replace(profile, deterministic_digest=_digest(profile))


def _required_package_sections() -> Mapping[str, tuple[str, ...]]:
    return {
        "Package Identity": ("Package Identifier", "Mission Identifier", "Assessment Identifier", "Package Version", "Schema Version", "Integrity Hash"),
        "Mission Metadata": ("Authorizing Authority", "Creation Timestamp", "Completion Timestamp", "Evaluation Scope", "Constitutional Version"),
        "Input Collection": ("Position Exposure", "Portfolio Exposure", "Market Assessment", "Market Events", "Configuration Snapshot", "Rule Registry Snapshot"),
        "Evaluation Context": ("normalized evaluation context", "dependency graph", "evaluation sequencing", "execution constraints"),
        "Risk Evidence": ("accepted Risk Evidence", "immutable provenance"),
        "Exposure Assessment": ("exposure objects", "aggregation records", "exposure classifications", "supporting evidence"),
        "Confidence Assessment": ("confidence objects", "uncertainty objects", "propagation records", "supporting evidence"),
        "Mitigation and Recovery": ("mitigation plans", "contingency plans", "recovery plans", "residual risk assessments"),
        "Enterprise Risk Assessment": ("final Enterprise Risk Assessment", "supporting findings", "constitutional conclusions"),
        "Validation Records": ("validation results", "admissibility verification", "integrity verification", "lifecycle verification", "dependency verification"),
        "Traceability Records": ("provenance graph", "dependency graph", "object relationships", "certification references"),
        "Audit Records": ("evaluation audit", "replay audit", "recovery audit", "certification audit"),
    }


def _default_graph_nodes() -> tuple[RiskEvaluationGraphNode, ...]:
    return (
        RiskEvaluationGraphNode("NODE-EVIDENCE-RM003", "Evidence Node", "RISK-EVIDENCE-RM003-001"),
        RiskEvaluationGraphNode("NODE-VALIDATION-RM003", "Validation Node", "RISK-VALIDATION-RM003-001"),
        RiskEvaluationGraphNode("NODE-EXPOSURE-RM003", "Exposure Node", "EXPOSURE-RM003-001"),
        RiskEvaluationGraphNode("NODE-CONFIDENCE-RM003", "Confidence Node", "CONFIDENCE-RM003-001"),
        RiskEvaluationGraphNode("NODE-RISK-ASSESSMENT-RM003", "Risk Assessment Node", "RISK-ASSESSMENT-RM003-001"),
        RiskEvaluationGraphNode("NODE-MITIGATION-RM003", "Mitigation Node", "MITIGATION-RM003-001"),
        RiskEvaluationGraphNode("NODE-RECOVERY-RM003", "Recovery Node", "RECOVERY-RM003-001"),
        RiskEvaluationGraphNode("NODE-ENTERPRISE-RISK-RM003", "Enterprise Risk Node", "ENTERPRISE-RISK-RM003-001"),
    )


def _default_graph_edges() -> tuple[RiskEvaluationGraphEdge, ...]:
    return (
        RiskEvaluationGraphEdge("NODE-EVIDENCE-RM003", "NODE-VALIDATION-RM003", "VALIDATED_BY"),
        RiskEvaluationGraphEdge("NODE-VALIDATION-RM003", "NODE-EXPOSURE-RM003", "PROPAGATES_TO"),
        RiskEvaluationGraphEdge("NODE-EXPOSURE-RM003", "NODE-CONFIDENCE-RM003", "PROPAGATES_TO"),
        RiskEvaluationGraphEdge("NODE-CONFIDENCE-RM003", "NODE-RISK-ASSESSMENT-RM003", "SUPPORTS"),
        RiskEvaluationGraphEdge("NODE-RISK-ASSESSMENT-RM003", "NODE-MITIGATION-RM003", "MITIGATES"),
        RiskEvaluationGraphEdge("NODE-MITIGATION-RM003", "NODE-RECOVERY-RM003", "RECOVERS"),
        RiskEvaluationGraphEdge("NODE-RECOVERY-RM003", "NODE-ENTERPRISE-RISK-RM003", "DERIVED_FROM"),
    )


def _topological_order(
    nodes: tuple[RiskEvaluationGraphNode, ...],
    edges: tuple[RiskEvaluationGraphEdge, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    node_ids = tuple(node.node_identifier for node in nodes)
    incoming = {node_id: 0 for node_id in node_ids}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        if edge.source_identifier in outgoing and edge.target_identifier in incoming:
            outgoing[edge.source_identifier].append(edge.target_identifier)
            incoming[edge.target_identifier] += 1
    ready = sorted(node_id for node_id, count in incoming.items() if count == 0)
    order: list[str] = []
    while ready:
        node_id = ready.pop(0)
        order.append(node_id)
        for target in sorted(outgoing[node_id]):
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
                ready.sort()
    findings = () if len(order) == len(node_ids) else ("graph cycle detected",)
    return tuple(order), findings


def _covered_lifecycle_objects() -> tuple[str, ...]:
    return (
        "Risk Assessment",
        "Risk Evaluation Mission",
        "Risk Evaluation Package",
        "Risk Evaluation Graph",
        "Risk Evidence",
        "Confidence Object",
        "Exposure Object",
        "Mitigation Plan",
        "Recovery Plan",
        "Enterprise Risk State",
        "Validation Object",
        "Configuration Object",
        "Replay Object",
        "Audit Object",
    )
