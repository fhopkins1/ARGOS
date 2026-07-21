"""Enterprise-owned Sentinel bridge certification support for SENT-RM-002."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping

from argos.foundation.contracts import utc_timestamp
from argos.foundation.persistence import InMemoryPersistenceRepository
from argos.foundation.persistence.records import PersistentRecord


SENT_RM_002_VERSION = "SENT-RM-002/1.0.0"


class EnterpriseCertificationDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True)
class CertificationEvidenceItem:
    evidence_id: str
    object_name: str
    object_id: str
    classification: str
    constitutional_purpose: str
    producing_subsystem: str
    created_timestamp_utc: str
    chronological_sequence: int
    record_hash: str
    payload_hash: str
    payload: Mapping[str, Any]
    immutable: bool


@dataclass(frozen=True)
class CertificationEvidenceRetrievalResult:
    retrieval_id: str
    query: Mapping[str, str]
    evidence_items: tuple[CertificationEvidenceItem, ...]
    missing_evidence: tuple[str, ...]
    read_only: bool
    service_identity: str
    deterministic_digest: str


@dataclass(frozen=True)
class RequiredCertificationArtifact:
    artifact_identifier: str
    artifact_classification: str
    constitutional_purpose: str
    producing_subsystem: str
    required_availability: str
    dependency_relationships: tuple[str, ...]


@dataclass(frozen=True)
class CertificationCompletenessRecord:
    validation_identifier: str
    validation_timestamp: str
    evaluated_inventory: tuple[str, ...]
    missing_artifacts: tuple[str, ...]
    incomplete_dependency_chains: tuple[str, ...]
    duplicate_artifacts: tuple[str, ...]
    unresolved_references: tuple[str, ...]
    uncovered_bridge_stages: tuple[str, ...]
    validation_outcome: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class ChronologicalVerificationRecord:
    verification_identifier: str
    verification_timestamp: str
    evaluated_timeline: tuple[str, ...]
    duplicate_sequence_positions: tuple[int, ...]
    chronological_gaps: tuple[int, ...]
    invalid_ordering: tuple[str, ...]
    missing_timeline_artifacts: tuple[str, ...]
    verification_outcome: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class CertificationMetadataRecord:
    metadata_identifier: str
    certification_type: str
    certification_subject: str
    certification_scope: str
    originating_evidence_identifiers: tuple[str, ...]
    governing_doctrine_version: str
    constitutional_requirement_identifiers: tuple[str, ...]
    certification_result: EnterpriseCertificationDecision
    certification_timestamp: str
    certifying_subsystem_identity: str
    certification_schema_version: str
    evidence_schema_version: str
    chronological_order: tuple[str, ...]
    deterministic_digest: str


@dataclass(frozen=True)
class IndependentCertificationTestResult:
    test_identifier: str
    governing_doctrine: str
    invariant_tested: str
    required_evidence: tuple[str, ...]
    observed_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class EnterpriseCertificationIntegrationRecord:
    certification_identifier: str
    certification_scope: str
    bridge_identifier: str
    remediation_order_coverage: tuple[str, ...]
    evidence_references: tuple[str, ...]
    metadata_references: tuple[str, ...]
    chronological_verification_status: EnterpriseCertificationDecision
    completeness_verification_status: EnterpriseCertificationDecision
    test_execution_references: tuple[str, ...]
    constitutional_rule_evaluation_results: tuple[str, ...]
    final_certification_decision: EnterpriseCertificationDecision
    execution_timestamps: tuple[str, ...]
    enterprise_certification_version: str
    immutable_audit_references: tuple[str, ...]
    deterministic_digest: str


class ReadOnlyCertificationEvidenceService:
    """Enterprise-owned read-only evidence retrieval service."""

    service_identity = "EnterpriseReadOnlyCertificationEvidenceService/SENT-RM-002"

    def __init__(self, repository: InMemoryPersistenceRepository) -> None:
        self._records = tuple(repository.all_records())

    def retrieve_all(self) -> CertificationEvidenceRetrievalResult:
        return self.retrieve({})

    def retrieve(self, query: Mapping[str, str]) -> CertificationEvidenceRetrievalResult:
        items = tuple(self._item(record, index + 1) for index, record in enumerate(self._records))
        filtered = tuple(item for item in items if _matches(item, query))
        required = tuple(query.get("required_object_names", "").split(",")) if query.get("required_object_names") else ()
        present = {item.object_name for item in filtered}
        missing = tuple(item for item in required if item and item not in present)
        result = CertificationEvidenceRetrievalResult(
            retrieval_id=f"SENT-RM-RETRIEVAL-{_digest((query, tuple(item.evidence_id for item in filtered)))[:12].upper()}",
            query=dict(query),
            evidence_items=filtered,
            missing_evidence=missing,
            read_only=True,
            service_identity=self.service_identity,
            deterministic_digest="",
        )
        return replace(result, deterministic_digest=_digest(asdict(result)))

    def _item(self, record: PersistentRecord, sequence: int) -> CertificationEvidenceItem:
        payload = _json_ready(record.to_dict())
        body = payload.get("payload", {})
        nested = body.get("payload", {}) if isinstance(body, dict) else {}
        object_name = str(nested.get("object_name", record.object_id)) if isinstance(nested, dict) else record.object_id
        payload_hash = str(body.get("payload_hash", record.record_hash)) if isinstance(body, dict) else record.record_hash
        return CertificationEvidenceItem(
            evidence_id=record.object_id,
            object_name=object_name,
            object_id=record.object_id,
            classification=_classification_for(object_name),
            constitutional_purpose=_purpose_for(object_name),
            producing_subsystem=_producer_for(object_name),
            created_timestamp_utc=record.created_timestamp_utc,
            chronological_sequence=sequence,
            record_hash=record.record_hash,
            payload_hash=payload_hash,
            payload=payload,
            immutable=True,
        )


class CertificationCompletenessValidator:
    required_artifacts = (
        RequiredCertificationArtifact("sentinel_bridge_resolution", "bridge_registration", "authoritative bridge resolution", "Enterprise Bridge Registry", "mandatory", ()),
        RequiredCertificationArtifact("sentinel_bridge_authority", "bridge_authority", "bridge authority validation", "Enterprise Bridge Authority Service", "mandatory", ("sentinel_bridge_resolution",)),
        RequiredCertificationArtifact("sentinel_notification_authority", "notification_authority", "notification authority validation", "Enterprise Authority Registry", "mandatory", ()),
        RequiredCertificationArtifact("sentinel_commander_resolution", "commander_resolution", "authoritative Commander resolution", "Enterprise Composition Root", "mandatory", ()),
        RequiredCertificationArtifact("sentinel_bus_transmission", "enterprise_transport", "Communications Bus transport", "Enterprise Communications Bus", "mandatory", ("sentinel_notification_authority", "sentinel_commander_resolution")),
        RequiredCertificationArtifact("commander_sentinel_receipt", "commander_receipt", "Commander receipt evidence", "Commander", "mandatory", ("sentinel_bus_transmission", "sentinel_commander_resolution")),
        RequiredCertificationArtifact("commander_sentinel_acknowledgment", "commander_acknowledgment", "Commander acknowledgment evidence", "Commander", "mandatory", ("commander_sentinel_receipt",)),
        RequiredCertificationArtifact("sentinel_delivery_reconciliation", "reconciliation", "delivery reconciliation", "Enterprise Reconciliation", "mandatory", ("commander_sentinel_acknowledgment",)),
        RequiredCertificationArtifact("sentinel_delivery_state", "delivery_state", "reconciliation-derived delivery state", "Enterprise Persistence", "mandatory", ("sentinel_delivery_reconciliation",)),
        RequiredCertificationArtifact("sentinel_immutable_bridge_evidence", "immutable_bridge_evidence", "immutable bridge evidence", "Enterprise Evidence Store", "mandatory", ("sentinel_delivery_reconciliation",)),
        RequiredCertificationArtifact("sentinel_delivery_replay_evidence", "replay", "replay compatibility evidence", "Enterprise Replay Infrastructure", "mandatory", ("sentinel_delivery_state",)),
        RequiredCertificationArtifact("sentinel_delivery_recovery_evidence", "recovery", "recovery compatibility evidence", "Enterprise Recovery Infrastructure", "mandatory", ("sentinel_delivery_state",)),
        RequiredCertificationArtifact("sentinel_bridge_certification_evidence_package", "certification_support", "read-only certification package", "Enterprise Certification Infrastructure", "mandatory", ("sentinel_immutable_bridge_evidence",)),
    )

    def validate(self, evidence: Iterable[CertificationEvidenceItem]) -> CertificationCompletenessRecord:
        items = tuple(evidence)
        by_name: dict[str, tuple[CertificationEvidenceItem, ...]] = {}
        for item in items:
            by_name[item.object_name] = by_name.get(item.object_name, ()) + (item,)
        required_names = tuple(artifact.artifact_identifier for artifact in self.required_artifacts)
        missing = tuple(name for name in required_names if name not in by_name)
        duplicates = tuple(name for name in required_names if len(by_name.get(name, ())) > 1 and name not in {"commander_sentinel_receipt", "commander_sentinel_acknowledgment"})
        incomplete = []
        for artifact in self.required_artifacts:
            if artifact.artifact_identifier in by_name:
                for dependency in artifact.dependency_relationships:
                    if dependency not in by_name:
                        incomplete.append(f"{artifact.artifact_identifier}->{dependency}")
        uncovered = tuple(name for name in required_names if name not in by_name)
        record = CertificationCompletenessRecord(
            validation_identifier=f"SENT-RM-COMPLETE-{_digest((required_names, missing, duplicates, tuple(incomplete)))[:12].upper()}",
            validation_timestamp=utc_timestamp(),
            evaluated_inventory=required_names,
            missing_artifacts=missing,
            incomplete_dependency_chains=tuple(incomplete),
            duplicate_artifacts=duplicates,
            unresolved_references=(),
            uncovered_bridge_stages=uncovered,
            validation_outcome=EnterpriseCertificationDecision.PASS if not missing and not duplicates and not incomplete else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))


class ChronologicalEvidenceVerifier:
    required_order = tuple(artifact.artifact_identifier for artifact in CertificationCompletenessValidator.required_artifacts)

    def verify(self, evidence: Iterable[CertificationEvidenceItem]) -> ChronologicalVerificationRecord:
        items = tuple(sorted(evidence, key=lambda item: item.chronological_sequence))
        first_positions = {name: next((item.chronological_sequence for item in items if item.object_name == name), 0) for name in self.required_order}
        missing = tuple(name for name, position in first_positions.items() if position == 0)
        invalid = []
        last = 0
        for name in self.required_order:
            position = first_positions[name]
            if position and position < last:
                invalid.append(name)
            if position:
                last = position
        positions = [item.chronological_sequence for item in items]
        duplicates = tuple(sorted(position for position in set(positions) if positions.count(position) > 1))
        gaps = tuple(index for index in range(1, len(positions) + 1) if index not in positions)
        record = ChronologicalVerificationRecord(
            verification_identifier=f"SENT-RM-CHRONO-{_digest((first_positions, tuple(invalid), missing))[:12].upper()}",
            verification_timestamp=utc_timestamp(),
            evaluated_timeline=tuple(item.object_name for item in items),
            duplicate_sequence_positions=duplicates,
            chronological_gaps=gaps,
            invalid_ordering=tuple(invalid),
            missing_timeline_artifacts=missing,
            verification_outcome=EnterpriseCertificationDecision.PASS if not missing and not invalid and not duplicates and not gaps else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))


class CertificationMetadataExposureService:
    def metadata_for(
        self,
        evidence: Iterable[CertificationEvidenceItem],
        completeness: CertificationCompletenessRecord,
        chronology: ChronologicalVerificationRecord,
    ) -> CertificationMetadataRecord:
        items = tuple(evidence)
        requirements = tuple(f"RM-014-00{index + 1}" for index in range(7))
        result = EnterpriseCertificationDecision.PASS if completeness.validation_outcome == chronology.verification_outcome == EnterpriseCertificationDecision.PASS else EnterpriseCertificationDecision.FAIL
        metadata = CertificationMetadataRecord(
            metadata_identifier=f"SENT-RM-META-{_digest((tuple(item.evidence_id for item in items), result.value))[:12].upper()}",
            certification_type="enterprise_bridge_certification_support",
            certification_subject="Sentinel-to-Commander Enterprise Bridge",
            certification_scope="SENT-RM-002",
            originating_evidence_identifiers=tuple(item.evidence_id for item in items),
            governing_doctrine_version=SENT_RM_002_VERSION,
            constitutional_requirement_identifiers=requirements,
            certification_result=result,
            certification_timestamp=utc_timestamp(),
            certifying_subsystem_identity="Enterprise Constitutional Certification Subsystem",
            certification_schema_version="1.0.0",
            evidence_schema_version="1.0.0",
            chronological_order=tuple(item.object_name for item in sorted(items, key=lambda item: item.chronological_sequence)),
            deterministic_digest="",
        )
        return replace(metadata, deterministic_digest=_digest(asdict(metadata)))


class IndependentSentinelBridgeCertificationTestSuite:
    test_specs = (
        ("SENT-RM-TEST-001", "SENT-RM-002-001", "certification authority separated", ("sentinel_bridge_certification_evidence_package",)),
        ("SENT-RM-TEST-002", "SENT-RM-002-002", "read-only evidence retrieval", ("sentinel_bridge_resolution", "sentinel_immutable_bridge_evidence")),
        ("SENT-RM-TEST-003", "SENT-RM-002-003", "evidence completeness", ("sentinel_delivery_reconciliation", "sentinel_delivery_state")),
        ("SENT-RM-TEST-004", "SENT-RM-002-004", "chronological integrity", ("sentinel_bridge_resolution", "commander_sentinel_acknowledgment")),
        ("SENT-RM-TEST-005", "SENT-RM-002-005", "metadata exposure", ("sentinel_bridge_certification_evidence_package",)),
    )

    def execute(self, evidence: Iterable[CertificationEvidenceItem]) -> tuple[IndependentCertificationTestResult, ...]:
        names = {item.object_name for item in evidence}
        results = []
        for test_id, doctrine, invariant, required in self.test_specs:
            missing = tuple(item for item in required if item not in names)
            observed = tuple(item for item in required if item in names)
            result = IndependentCertificationTestResult(
                test_identifier=test_id,
                governing_doctrine=doctrine,
                invariant_tested=invariant,
                required_evidence=required,
                observed_evidence=observed,
                missing_evidence=missing,
                result=EnterpriseCertificationDecision.PASS if not missing else EnterpriseCertificationDecision.FAIL,
                deterministic_digest="",
            )
            results.append(replace(result, deterministic_digest=_digest(asdict(result))))
        return tuple(results)


class EnterpriseSentinelBridgeCertificationWorkflow:
    """Enterprise-owned certification workflow; Sentinel is not called for decisions."""

    remediation_order_coverage = (
        "SENT-RM-002-001",
        "SENT-RM-002-002",
        "SENT-RM-002-003",
        "SENT-RM-002-004",
        "SENT-RM-002-005",
        "SENT-RM-002-006",
        "SENT-RM-002-007",
    )

    def execute(self, evidence_service: ReadOnlyCertificationEvidenceService) -> EnterpriseCertificationIntegrationRecord:
        retrieval = evidence_service.retrieve_all()
        completeness = CertificationCompletenessValidator().validate(retrieval.evidence_items)
        chronology = ChronologicalEvidenceVerifier().verify(retrieval.evidence_items)
        metadata = CertificationMetadataExposureService().metadata_for(retrieval.evidence_items, completeness, chronology)
        tests = IndependentSentinelBridgeCertificationTestSuite().execute(retrieval.evidence_items)
        final = EnterpriseCertificationDecision.PASS if (
            completeness.validation_outcome == EnterpriseCertificationDecision.PASS
            and chronology.verification_outcome == EnterpriseCertificationDecision.PASS
            and all(test.result == EnterpriseCertificationDecision.PASS for test in tests)
        ) else EnterpriseCertificationDecision.FAIL
        record = EnterpriseCertificationIntegrationRecord(
            certification_identifier=f"SENT-RM-INTEGRATION-{_digest((retrieval.deterministic_digest, metadata.deterministic_digest, final.value))[:12].upper()}",
            certification_scope="Sentinel-to-Commander Enterprise Bridge",
            bridge_identifier="BRIDGE-SENTINEL-COMMANDER-ALERT-001",
            remediation_order_coverage=self.remediation_order_coverage,
            evidence_references=tuple(item.evidence_id for item in retrieval.evidence_items),
            metadata_references=(metadata.metadata_identifier,),
            chronological_verification_status=chronology.verification_outcome,
            completeness_verification_status=completeness.validation_outcome,
            test_execution_references=tuple(test.test_identifier for test in tests),
            constitutional_rule_evaluation_results=tuple(f"{test.test_identifier}:{test.result.value}" for test in tests),
            final_certification_decision=final,
            execution_timestamps=(utc_timestamp(),),
            enterprise_certification_version=SENT_RM_002_VERSION,
            immutable_audit_references=(retrieval.retrieval_id, completeness.validation_identifier, chronology.verification_identifier, metadata.metadata_identifier),
            deterministic_digest="",
        )
        return replace(record, deterministic_digest=_digest(asdict(record)))


def _matches(item: CertificationEvidenceItem, query: Mapping[str, str]) -> bool:
    if query.get("notification_identifier") and query["notification_identifier"] not in json.dumps(item.payload, sort_keys=True, default=str):
        return False
    if query.get("observation_identifier") and query["observation_identifier"] not in json.dumps(item.payload, sort_keys=True, default=str):
        return False
    if query.get("bridge_identifier") and query["bridge_identifier"] not in json.dumps(item.payload, sort_keys=True, default=str):
        return False
    if query.get("object_name") and item.object_name != query["object_name"]:
        return False
    return True


def _classification_for(object_name: str) -> str:
    if "authority" in object_name:
        return "authority"
    if "reconciliation" in object_name:
        return "reconciliation"
    if "replay" in object_name:
        return "replay"
    if "recovery" in object_name:
        return "recovery"
    if "receipt" in object_name:
        return "receipt"
    if "acknowledgment" in object_name:
        return "acknowledgment"
    if "bridge" in object_name:
        return "bridge"
    return "certification_evidence"


def _purpose_for(object_name: str) -> str:
    return object_name.replace("_", " ")


def _producer_for(object_name: str) -> str:
    if object_name.startswith("commander_"):
        return "Commander"
    if "bus" in object_name:
        return "Enterprise Communications Bus"
    if "certification" in object_name:
        return "Enterprise Certification Infrastructure"
    return "Enterprise Bridge Evidence Store"


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def _digest(payload: object) -> str:
    encoded = json.dumps(_json_ready(payload), sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
