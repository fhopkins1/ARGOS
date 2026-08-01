from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


ENTERPRISE_LEARNING_RM002_VERSION = "ENTERPRISE-LEARNING-RM-002"
ENTERPRISE_LEARNING_OFFICE = "Enterprise Learning Office"


class EnterpriseLearningRuntimeError(ValueError):
    def __init__(self, code: str, message: str, *, evidence: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.evidence = dict(evidence or {})


class EnterpriseLearningBoundaryError(EnterpriseLearningRuntimeError):
    pass


class LifecycleState(str, Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"
    REJECTED = "REJECTED"


class HypothesisStatus(str, Enum):
    PROPOSED = "PROPOSED"
    UNDER_EVALUATION = "UNDER_EVALUATION"
    SUPPORTED = "SUPPORTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class ReproducibilityStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    REPRODUCIBLE = "REPRODUCIBLE"
    REPRODUCIBLE_WITH_DECLARED_VARIANCE = "REPRODUCIBLE_WITH_DECLARED_VARIANCE"
    PARTIALLY_REPRODUCIBLE = "PARTIALLY_REPRODUCIBLE"
    NOT_REPRODUCIBLE = "NOT_REPRODUCIBLE"


class ProductClass(str, Enum):
    HYPOTHESIS = "HYPOTHESIS"
    PREDICTIVE_MODEL = "PREDICTIVE_MODEL"
    CAUSAL_MODEL = "CAUSAL_MODEL"
    ANOMALY_MODEL = "ANOMALY_MODEL"
    UNCERTAINTY_ESTIMATE = "UNCERTAINTY_ESTIMATE"
    EXPLAINABILITY_ARTIFACT = "EXPLAINABILITY_ARTIFACT"
    FEATURE_DEFINITION = "FEATURE_DEFINITION"
    LEARNING_RECOMMENDATION = "LEARNING_RECOMMENDATION"


class ProvenanceRelationship(str, Enum):
    FEATURE_DERIVES_FROM_SOURCE = "FEATURE_DERIVES_FROM_SOURCE"
    DATASET_SUPPLIES_EXPERIMENT = "DATASET_SUPPLIES_EXPERIMENT"
    EXPERIMENT_TESTS_HYPOTHESIS = "EXPERIMENT_TESTS_HYPOTHESIS"
    MODEL_DERIVED_FROM_EXPERIMENT = "MODEL_DERIVED_FROM_EXPERIMENT"
    EXPLAINABILITY_EXPLAINS_PRODUCT = "EXPLAINABILITY_EXPLAINS_PRODUCT"
    EVIDENCE_SUPPORTS_PRODUCT = "EVIDENCE_SUPPORTS_PRODUCT"
    PRODUCT_SUPERSEDES_PRODUCT = "PRODUCT_SUPERSEDES_PRODUCT"


@dataclass(frozen=True)
class LearningEvidence:
    evidence_id: str
    authority: str
    subject_id: str
    event_type: str
    event_time: str
    inputs: Mapping[str, Any]
    outputs: Mapping[str, Any]
    digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))
        object.__setattr__(self, "outputs", MappingProxyType(dict(self.outputs)))
        object.__setattr__(self, "digest", _digest(_plain(self)))


@dataclass(frozen=True)
class LearningDataset:
    dataset_id: str
    purpose: str
    source_refs: tuple[str, ...]
    owner_refs: tuple[str, ...]
    version: str
    records: tuple[Mapping[str, Any], ...]
    validation_rules: tuple[str, ...]
    limitations: tuple[str, ...]
    reproducibility: ReproducibilityStatus
    state: LifecycleState
    evidence_id: str
    digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(MappingProxyType(dict(item)) for item in self.records))
        object.__setattr__(self, "digest", _digest(_plain(self)))


@dataclass(frozen=True)
class FeatureDefinition:
    feature_id: str
    dataset_id: str
    source_fields: tuple[str, ...]
    transformation: str
    quality_measurements: Mapping[str, float]
    limitations: tuple[str, ...]
    evidence_id: str
    digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "quality_measurements", MappingProxyType(dict(self.quality_measurements)))
        object.__setattr__(self, "digest", _digest(_plain(self)))


@dataclass(frozen=True)
class LearningHypothesis:
    hypothesis_id: str
    objective: str
    falsification_criteria: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    confidence: float
    uncertainty: float
    status: HypothesisStatus
    evidence_id: str
    digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "digest", _digest(_plain(self)))


@dataclass(frozen=True)
class LearningExperiment:
    experiment_id: str
    hypothesis_id: str
    dataset_id: str
    feature_ids: tuple[str, ...]
    method: str
    seed: int
    metrics: Mapping[str, float]
    reproducibility: ReproducibilityStatus
    completed: bool
    evidence_id: str
    digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))
        object.__setattr__(self, "digest", _digest(_plain(self)))


@dataclass(frozen=True)
class LearningModel:
    model_id: str
    product_class: ProductClass
    experiment_id: str
    validation_metrics: Mapping[str, float]
    lifecycle_state: LifecycleState
    reproducibility: ReproducibilityStatus
    evidence_id: str
    digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "validation_metrics", MappingProxyType(dict(self.validation_metrics)))
        object.__setattr__(self, "digest", _digest(_plain(self)))


@dataclass(frozen=True)
class ExplainabilityArtifact:
    explanation_id: str
    product_id: str
    assumptions: tuple[str, ...]
    feature_importance: Mapping[str, float]
    uncertainty: float
    supporting_evidence: tuple[str, ...]
    reproducibility: ReproducibilityStatus
    evidence_id: str
    digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "feature_importance", MappingProxyType(dict(self.feature_importance)))
        object.__setattr__(self, "digest", _digest(_plain(self)))


@dataclass(frozen=True)
class LearningProvenanceEdge:
    edge_id: str
    source_id: str
    target_id: str
    relationship: ProvenanceRelationship
    evidence_id: str
    digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "digest", _digest(_plain(self)))


@dataclass(frozen=True)
class KnowledgePublication:
    publication_id: str
    product_id: str
    product_class: ProductClass
    consumer_contract: Mapping[str, Any]
    evidence_refs: tuple[str, ...]
    explainability_ref: str
    provenance_refs: tuple[str, ...]
    state: LifecycleState
    evidence_id: str
    digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "consumer_contract", MappingProxyType(dict(self.consumer_contract)))
        object.__setattr__(self, "digest", _digest(_plain(self)))


class EnterpriseLearningRuntime:
    """Certifiable runtime for Enterprise Learning RM-002 artifacts.

    The runtime creates learning products, evidence, and provenance only. It
    deliberately fails closed on operational authority requests.
    """

    PROHIBITED_OPERATIONS = {
        "CREATE_CANONICAL_TRUTH",
        "MODIFY_HISTORIAN_RECORD",
        "AUTHORIZE_TRADE_EXECUTION",
        "MUTATE_POSITION",
        "CERTIFY_PERFORMANCE_TRUTH",
        "DEPLOY_MODEL_TO_PRODUCTION",
        "OVERRIDE_COMMANDER",
    }

    def __init__(self) -> None:
        self.evidence: dict[str, LearningEvidence] = {}
        self.datasets: dict[str, LearningDataset] = {}
        self.features: dict[str, FeatureDefinition] = {}
        self.hypotheses: dict[str, LearningHypothesis] = {}
        self.experiments: dict[str, LearningExperiment] = {}
        self.models: dict[str, LearningModel] = {}
        self.explanations: dict[str, ExplainabilityArtifact] = {}
        self.provenance: dict[str, LearningProvenanceEdge] = {}
        self.publications: dict[str, KnowledgePublication] = {}
        self.boundary_events: list[dict[str, Any]] = []

    def create_dataset(
        self,
        *,
        dataset_id: str,
        purpose: str,
        source_refs: tuple[str, ...],
        owner_refs: tuple[str, ...],
        version: str,
        records: tuple[Mapping[str, Any], ...],
        validation_rules: tuple[str, ...],
        limitations: tuple[str, ...],
        event_time: str,
        reproducibility: ReproducibilityStatus = ReproducibilityStatus.REPRODUCIBLE,
    ) -> LearningDataset:
        self._require(dataset_id not in self.datasets, "DUPLICATE_DATASET", dataset_id)
        self._require(source_refs, "DATASET_SOURCE_REQUIRED", dataset_id)
        self._require(owner_refs, "DATASET_OWNER_REQUIRED", dataset_id)
        self._require(validation_rules, "DATASET_VALIDATION_REQUIRED", dataset_id)
        evidence = self._record_evidence(dataset_id, "DATASET_CREATED", event_time, {"source_refs": source_refs}, {"record_count": len(records)})
        dataset = LearningDataset(
            dataset_id=dataset_id,
            purpose=purpose,
            source_refs=source_refs,
            owner_refs=owner_refs,
            version=version,
            records=records,
            validation_rules=validation_rules,
            limitations=limitations,
            reproducibility=reproducibility,
            state=LifecycleState.VALIDATED,
            evidence_id=evidence.evidence_id,
        )
        self.datasets[dataset_id] = dataset
        return dataset

    def define_feature(
        self,
        *,
        feature_id: str,
        dataset_id: str,
        source_fields: tuple[str, ...],
        transformation: str,
        quality_measurements: Mapping[str, float],
        limitations: tuple[str, ...],
        event_time: str,
    ) -> FeatureDefinition:
        self._require(dataset_id in self.datasets, "UNKNOWN_DATASET", dataset_id)
        self._require(source_fields, "FEATURE_SOURCE_REQUIRED", feature_id)
        self._require(transformation, "FEATURE_TRANSFORMATION_REQUIRED", feature_id)
        self._require(quality_measurements, "FEATURE_QUALITY_REQUIRED", feature_id)
        evidence = self._record_evidence(feature_id, "FEATURE_DEFINED", event_time, {"dataset_id": dataset_id}, {"quality": dict(quality_measurements)})
        feature = FeatureDefinition(feature_id, dataset_id, source_fields, transformation, quality_measurements, limitations, evidence.evidence_id)
        self.features[feature_id] = feature
        self.add_provenance_edge(source_id=dataset_id, target_id=feature_id, relationship=ProvenanceRelationship.FEATURE_DERIVES_FROM_SOURCE, event_time=event_time)
        return feature

    def register_hypothesis(
        self,
        *,
        hypothesis_id: str,
        objective: str,
        falsification_criteria: tuple[str, ...],
        supporting_evidence: tuple[str, ...],
        confidence: float,
        uncertainty: float,
        event_time: str,
    ) -> LearningHypothesis:
        self._require(falsification_criteria, "HYPOTHESIS_FALSIFICATION_REQUIRED", hypothesis_id)
        self._require(0.0 <= confidence <= 1.0 and 0.0 <= uncertainty <= 1.0, "HYPOTHESIS_MEASUREMENT_INVALID", hypothesis_id)
        evidence = self._record_evidence(hypothesis_id, "HYPOTHESIS_REGISTERED", event_time, {"supporting_evidence": supporting_evidence}, {"confidence": confidence, "uncertainty": uncertainty})
        hypothesis = LearningHypothesis(hypothesis_id, objective, falsification_criteria, supporting_evidence, confidence, uncertainty, HypothesisStatus.UNDER_EVALUATION, evidence.evidence_id)
        self.hypotheses[hypothesis_id] = hypothesis
        return hypothesis

    def execute_experiment(
        self,
        *,
        experiment_id: str,
        hypothesis_id: str,
        dataset_id: str,
        feature_ids: tuple[str, ...],
        method: str,
        seed: int,
        metrics: Mapping[str, float],
        event_time: str,
        reproducibility: ReproducibilityStatus = ReproducibilityStatus.REPRODUCIBLE,
    ) -> LearningExperiment:
        self._require(hypothesis_id in self.hypotheses, "UNKNOWN_HYPOTHESIS", hypothesis_id)
        self._require(dataset_id in self.datasets, "UNKNOWN_DATASET", dataset_id)
        self._require(all(feature_id in self.features for feature_id in feature_ids), "UNKNOWN_FEATURE", ",".join(feature_ids))
        self._require(metrics, "EXPERIMENT_METRICS_REQUIRED", experiment_id)
        evidence = self._record_evidence(experiment_id, "EXPERIMENT_EXECUTED", event_time, {"seed": seed, "method": method}, {"metrics": dict(metrics)})
        experiment = LearningExperiment(experiment_id, hypothesis_id, dataset_id, feature_ids, method, seed, metrics, reproducibility, True, evidence.evidence_id)
        self.experiments[experiment_id] = experiment
        self.add_provenance_edge(source_id=dataset_id, target_id=experiment_id, relationship=ProvenanceRelationship.DATASET_SUPPLIES_EXPERIMENT, event_time=event_time)
        self.add_provenance_edge(source_id=experiment_id, target_id=hypothesis_id, relationship=ProvenanceRelationship.EXPERIMENT_TESTS_HYPOTHESIS, event_time=event_time)
        return experiment

    def evaluate_hypothesis(self, hypothesis_id: str, *, status: HypothesisStatus, confidence: float, uncertainty: float, event_time: str) -> LearningHypothesis:
        current = self.hypotheses[hypothesis_id]
        self._require(status in {HypothesisStatus.SUPPORTED, HypothesisStatus.INCONCLUSIVE, HypothesisStatus.REJECTED}, "INVALID_HYPOTHESIS_DISPOSITION", hypothesis_id)
        evidence = self._record_evidence(hypothesis_id, "HYPOTHESIS_EVALUATED", event_time, {"previous_status": current.status.value}, {"status": status.value})
        updated = LearningHypothesis(hypothesis_id, current.objective, current.falsification_criteria, current.supporting_evidence + (evidence.evidence_id,), confidence, uncertainty, status, evidence.evidence_id)
        self.hypotheses[hypothesis_id] = updated
        return updated

    def register_model(
        self,
        *,
        model_id: str,
        product_class: ProductClass,
        experiment_id: str,
        validation_metrics: Mapping[str, float],
        event_time: str,
        reproducibility: ReproducibilityStatus = ReproducibilityStatus.REPRODUCIBLE,
    ) -> LearningModel:
        self._require(product_class in {ProductClass.PREDICTIVE_MODEL, ProductClass.CAUSAL_MODEL, ProductClass.ANOMALY_MODEL, ProductClass.UNCERTAINTY_ESTIMATE}, "INVALID_MODEL_PRODUCT_CLASS", product_class.value)
        self._require(experiment_id in self.experiments and self.experiments[experiment_id].completed, "MODEL_EXPERIMENT_REQUIRED", model_id)
        self._require(validation_metrics, "MODEL_VALIDATION_REQUIRED", model_id)
        self._require(reproducibility != ReproducibilityStatus.NOT_REPRODUCIBLE, "MODEL_REPRODUCIBILITY_FAILED", model_id)
        evidence = self._record_evidence(model_id, "MODEL_REGISTERED", event_time, {"experiment_id": experiment_id}, {"validation_metrics": dict(validation_metrics)})
        model = LearningModel(model_id, product_class, experiment_id, validation_metrics, LifecycleState.VALIDATED, reproducibility, evidence.evidence_id)
        self.models[model_id] = model
        self.add_provenance_edge(source_id=experiment_id, target_id=model_id, relationship=ProvenanceRelationship.MODEL_DERIVED_FROM_EXPERIMENT, event_time=event_time)
        return model

    def create_explainability(
        self,
        *,
        explanation_id: str,
        product_id: str,
        assumptions: tuple[str, ...],
        feature_importance: Mapping[str, float],
        uncertainty: float,
        supporting_evidence: tuple[str, ...],
        event_time: str,
        reproducibility: ReproducibilityStatus = ReproducibilityStatus.REPRODUCIBLE,
    ) -> ExplainabilityArtifact:
        self._require(product_id in self.models or product_id in self.hypotheses, "UNKNOWN_EXPLAINED_PRODUCT", product_id)
        self._require(assumptions and feature_importance and supporting_evidence, "EXPLANATION_INCOMPLETE", explanation_id)
        evidence = self._record_evidence(explanation_id, "EXPLAINABILITY_CREATED", event_time, {"product_id": product_id}, {"uncertainty": uncertainty})
        artifact = ExplainabilityArtifact(explanation_id, product_id, assumptions, feature_importance, uncertainty, supporting_evidence, reproducibility, evidence.evidence_id)
        self.explanations[explanation_id] = artifact
        self.add_provenance_edge(source_id=explanation_id, target_id=product_id, relationship=ProvenanceRelationship.EXPLAINABILITY_EXPLAINS_PRODUCT, event_time=event_time)
        return artifact

    def publish_product(
        self,
        *,
        publication_id: str,
        product_id: str,
        product_class: ProductClass,
        consumer_contract: Mapping[str, Any],
        evidence_refs: tuple[str, ...],
        explainability_ref: str,
        provenance_refs: tuple[str, ...],
        event_time: str,
    ) -> KnowledgePublication:
        self._require(product_class in set(ProductClass), "INVALID_PUBLICATION_CLASS", product_class.value)
        self._require(product_id in self.models or product_id in self.hypotheses or product_id in self.features, "UNKNOWN_PRODUCT", product_id)
        self._require(evidence_refs and all(ref in self.evidence for ref in evidence_refs), "PUBLICATION_EVIDENCE_REQUIRED", product_id)
        self._require(explainability_ref in self.explanations, "PUBLICATION_EXPLAINABILITY_REQUIRED", product_id)
        self._require(provenance_refs and all(ref in self.provenance for ref in provenance_refs), "PUBLICATION_PROVENANCE_REQUIRED", product_id)
        self._require("permitted_uses" in consumer_contract and "prohibited_uses" in consumer_contract, "CONSUMER_CONTRACT_INCOMPLETE", product_id)
        evidence = self._record_evidence(publication_id, "KNOWLEDGE_PUBLISHED", event_time, {"product_id": product_id}, {"consumer_contract": dict(consumer_contract)})
        publication = KnowledgePublication(publication_id, product_id, product_class, consumer_contract, evidence_refs, explainability_ref, provenance_refs, LifecycleState.PUBLISHED, evidence.evidence_id)
        self.publications[publication_id] = publication
        return publication

    def add_provenance_edge(self, *, source_id: str, target_id: str, relationship: ProvenanceRelationship, event_time: str) -> LearningProvenanceEdge:
        self._require(source_id != target_id, "PROVENANCE_SELF_REFERENCE", source_id)
        edge_id = f"EL-PROV-{_digest({'source': source_id, 'target': target_id, 'relationship': relationship.value})[:12]}"
        evidence = self._record_evidence(edge_id, "PROVENANCE_EDGE_CREATED", event_time, {"source_id": source_id}, {"target_id": target_id, "relationship": relationship.value})
        edge = LearningProvenanceEdge(edge_id, source_id, target_id, relationship, evidence.evidence_id)
        self.provenance[edge_id] = edge
        return edge

    def validate_provenance_graph(self) -> dict[str, Any]:
        known = set(self.datasets) | set(self.features) | set(self.hypotheses) | set(self.experiments) | set(self.models) | set(self.explanations) | set(self.evidence)
        orphan_edges = [edge.edge_id for edge in self.provenance.values() if edge.source_id not in known or edge.target_id not in known]
        return {
            "edge_count": len(self.provenance),
            "orphan_edges": orphan_edges,
            "cycle_detected": _has_cycle([(edge.source_id, edge.target_id) for edge in self.provenance.values()]),
            "disposition": "PASS" if not orphan_edges and not _has_cycle([(edge.source_id, edge.target_id) for edge in self.provenance.values()]) else "FAIL",
        }

    def enforce_boundary(self, *, operation: str, requested_authority: str, requesting_component: str, event_time: str) -> dict[str, Any]:
        allowed = operation not in self.PROHIBITED_OPERATIONS and requested_authority == "ADVISORY_LEARNING"
        record = {
            "operation": operation,
            "requested_authority": requested_authority,
            "requesting_component": requesting_component,
            "event_time": event_time,
            "allowed": allowed,
            "disposition": "PASS" if allowed else "FAIL_CLOSED",
        }
        self.boundary_events.append(record)
        if not allowed:
            raise EnterpriseLearningBoundaryError("BOUNDARY_FAIL_CLOSED", f"Enterprise Learning may not perform {operation}", evidence=record)
        return record

    def certification_report(self) -> dict[str, Any]:
        graph = self.validate_provenance_graph()
        return {
            "runtime_version": ENTERPRISE_LEARNING_RM002_VERSION,
            "dataset_count": len(self.datasets),
            "feature_count": len(self.features),
            "hypothesis_count": len(self.hypotheses),
            "experiment_count": len(self.experiments),
            "model_count": len(self.models),
            "explainability_count": len(self.explanations),
            "provenance_edge_count": len(self.provenance),
            "publication_count": len(self.publications),
            "boundary_event_count": len(self.boundary_events),
            "provenance_disposition": graph["disposition"],
            "orders_covered": tuple(f"ENTERPRISE-LEARNING-RM-002-{index:03d}" for index in range(1, 11)),
            "disposition": "PASS" if self.datasets and self.features and self.experiments and self.models and self.explanations and self.publications and graph["disposition"] == "PASS" else "INCOMPLETE",
        }

    def _record_evidence(self, subject_id: str, event_type: str, event_time: str, inputs: Mapping[str, Any], outputs: Mapping[str, Any]) -> LearningEvidence:
        evidence_id = f"EL-EVID-{_digest({'subject_id': subject_id, 'event_type': event_type, 'event_time': event_time, 'inputs': inputs, 'outputs': outputs})[:12]}"
        evidence = LearningEvidence(evidence_id, ENTERPRISE_LEARNING_OFFICE, subject_id, event_type, event_time, inputs, outputs)
        self.evidence[evidence_id] = evidence
        return evidence

    @staticmethod
    def _require(condition: bool, code: str, subject: str) -> None:
        if not condition:
            raise EnterpriseLearningRuntimeError(code, f"{code}: {subject}", evidence={"subject": subject})


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return {key: _plain(val) for key, val in value.items()}
    if isinstance(value, Mapping):
        return {key: _plain(val) for key, val in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {item.name: _plain(getattr(value, item.name)) for item in fields(value) if item.name != "digest"}
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_plain(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _has_cycle(edges: list[tuple[str, str]]) -> bool:
    graph: dict[str, list[str]] = {}
    for source, target in edges:
        graph.setdefault(source, []).append(target)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for child in graph.get(node, []):
            if visit(child):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)
