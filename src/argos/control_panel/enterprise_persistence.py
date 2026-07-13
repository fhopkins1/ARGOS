"""Enterprise persistence and deterministic recovery for ARGOS OR-006."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any
from collections.abc import Mapping

from argos.foundation.contracts import utc_timestamp
from argos.foundation.persistence import InMemoryPersistenceRepository, PersistenceError, canonical_schemas
from argos.foundation.persistence.backup import BackupBundle, BackupService
from argos.foundation.persistence.records import ObjectType, PersistentRecord

from .canonical_enterprise_runtime import CanonicalEnterpriseRuntime, CanonicalRuntimeMode, RuntimeAdmissionRecord, RuntimeFailure
from .truth_domain import OperationalTruthEnvelope, TruthEnvelopeError, make_paper_operational_truth_envelope, require_operational_truth_envelope
from .truth_promotion import PromotionDecisionStatus, PromotionScope, TruthPromotionAuthority


OPERATIONAL_AUTHORITY_OBJECT_TYPES = {
    ObjectType.ENTERPRISE_BROKER_STATE,
    ObjectType.ENTERPRISE_POSITION_STATE,
    ObjectType.ENTERPRISE_PERFORMANCE_TRUTH,
}


class PersistenceCategory(str, Enum):
    AUTHORITATIVE = "A_authoritative_persistent_state"
    DERIVED = "B_recoverable_derived_state"
    EPHEMERAL = "C_ephemeral_runtime_state"
    OPTIMIZATION = "D_rebuildable_optimization_state"


class RecoveryMode(str, Enum):
    CLEAN_STARTUP = "clean_startup"
    PLANNED_RESTART = "planned_restart"
    CRASH_RECOVERY = "crash_recovery"
    INTERRUPTED_WORKFLOW_RECOVERY = "interrupted_workflow_recovery"
    INTERRUPTED_BROKER_RECOVERY = "interrupted_broker_recovery"
    POSITION_RECOVERY = "position_recovery"
    RECONCILIATION_RECOVERY = "reconciliation_recovery"
    PARTIAL_RECOVERY = "partial_recovery"
    DEGRADED_RECOVERY = "degraded_recovery"
    MANUAL_RECOVERY_REQUIRED = "manual_recovery_required"
    FAULTED = "faulted"


class RecoverySeverity(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class EnterprisePersistenceError(RuntimeError):
    """Fail-closed persistence or recovery error."""


@dataclass(frozen=True)
class PersistenceInventoryItem:
    component: str
    authoritative_owner: str
    category: PersistenceCategory
    object_type: str
    serialization_format: str
    schema_owner: str
    restore_order: int
    truth_domain: str
    idempotency_requirement: str
    corruption_handling: str


@dataclass(frozen=True)
class TransactionWrite:
    object_type: ObjectType
    object_id: str
    payload: dict[str, Any]
    truth_domain: str = "PAPER"
    idempotency_key: str = ""
    require_new_identity: bool = False
    truth_envelope: OperationalTruthEnvelope | dict[str, Any] | None = None


@dataclass(frozen=True)
class PersistenceDiagnostic:
    code: str
    severity: RecoverySeverity
    component: str
    explanation: str
    recoverable: bool


@dataclass(frozen=True)
class RecoveryAuditRecord:
    audit_id: str
    recovery_mode: RecoveryMode
    started_at: str
    completed_at: str
    restored_entities: tuple[str, ...]
    deferred_entities: tuple[str, ...]
    failed_entities: tuple[str, ...]
    diagnostics: tuple[dict[str, Any], ...]
    paper_operation_allowed: bool


class DurableEnterprisePersistenceStore:
    """Durable hash-chain store for canonical enterprise runtime state."""

    def __init__(self, path: str | Path | None = None, *, fail_writes: bool = False) -> None:
        self.path = Path(path) if path else None
        self.repository = InMemoryPersistenceRepository(canonical_schemas())
        self.fail_writes = fail_writes
        self._diagnostics: list[PersistenceDiagnostic] = []
        if self.path and self.path.exists():
            self._load()

    def persist_authoritative(
        self,
        object_type: ObjectType,
        object_id: str,
        payload: dict[str, Any],
        *,
        truth_domain: str = "PAPER",
        idempotency_key: str = "",
        require_new_identity: bool = False,
        truth_envelope: OperationalTruthEnvelope | dict[str, Any] | None = None,
    ) -> PersistentRecord:
        self._preflight_write(object_type, object_id, require_new_identity=require_new_identity)
        operational_envelope = self._operational_truth_envelope(object_type, object_id, truth_envelope)
        envelope = self._envelope(object_id, payload, truth_domain=truth_domain, idempotency_key=idempotency_key, operational_truth_envelope=operational_envelope)
        try:
            record = self.repository.persist(object_type, object_id, envelope)
            self._flush()
            return record
        except Exception as exc:
            self._diagnostic("PERSISTENCE_WRITE_FAILED", RecoverySeverity.CRITICAL, object_type.value, str(exc), False)
            raise EnterprisePersistenceError(f"persistence failed closed for {object_type.value}:{object_id}") from exc

    def commit_transaction(self, boundary_id: str, writes: tuple[TransactionWrite, ...]) -> tuple[PersistentRecord, ...]:
        if not writes:
            raise EnterprisePersistenceError("transaction requires at least one write")
        for write in writes:
            self._preflight_write(write.object_type, write.object_id, require_new_identity=write.require_new_identity)
        records = tuple(
            self.persist_authoritative(
                write.object_type,
                write.object_id,
                write.payload,
                truth_domain=write.truth_domain,
                idempotency_key=write.idempotency_key or boundary_id,
                require_new_identity=write.require_new_identity,
                truth_envelope=write.truth_envelope,
            )
            for write in writes
        )
        self.persist_authoritative(
            ObjectType.ENTERPRISE_TRANSACTION,
            boundary_id,
            {
                "boundary_id": boundary_id,
                "writes": tuple(f"{write.object_type.value}:{write.object_id}" for write in writes),
                "record_hashes": tuple(record.record_hash for record in records),
                "atomicity": "best_effort_preflight_then_append",
            },
            idempotency_key=boundary_id,
            require_new_identity=True,
        )
        return records

    def checkpoint(self, checkpoint_id: str, payload: dict[str, Any]) -> PersistentRecord:
        body = dict(payload)
        body["checkpoint_authority"] = "continuity_only_not_financial_truth"
        return self.persist_authoritative(
            ObjectType.ENTERPRISE_RUNTIME_CHECKPOINT,
            checkpoint_id,
            body,
            truth_domain="RUNTIME_CHECKPOINT",
            idempotency_key=checkpoint_id,
        )

    def persist_runtime(self, runtime: CanonicalEnterpriseRuntime, *, checkpoint_id: str = "runtime-checkpoint") -> tuple[PersistentRecord, ...]:
        snapshot = runtime.enterprise_persistence_snapshot()
        records = self.commit_transaction(
            f"OR006-RUNTIME-{len(self.repository.all_records()) + 1:06d}",
            (
                TransactionWrite(ObjectType.ENTERPRISE_RUNTIME_STATE, "canonical-runtime", snapshot["runtime"], idempotency_key="canonical-runtime"),
                TransactionWrite(ObjectType.ENTERPRISE_MISSION_STATE, "canonical-missions", snapshot["missions"], idempotency_key="canonical-missions"),
                TransactionWrite(ObjectType.ENTERPRISE_WORKFLOW_STATE, "canonical-workflows", snapshot["workflows"], idempotency_key="canonical-workflows"),
                TransactionWrite(ObjectType.ENTERPRISE_BROKER_STATE, "paper-broker", snapshot["broker"], idempotency_key="paper-broker", truth_envelope=self._runtime_truth_envelope("DeterministicPaperBrokerage", "paper-broker", "paper-broker")),
                TransactionWrite(ObjectType.ENTERPRISE_POSITION_STATE, "position-registry", snapshot["positions"], idempotency_key="position-registry", truth_envelope=self._runtime_truth_envelope("PositionRegistry", "position-registry", "position-registry")),
                TransactionWrite(ObjectType.ENTERPRISE_PERFORMANCE_TRUTH, "performance-truth-paper", snapshot["performance_truth"], idempotency_key="performance-truth-paper", truth_envelope=self._runtime_truth_envelope("PerformanceTruthEngine", "performance-truth-paper", "performance-truth-paper")),
                TransactionWrite(ObjectType.ENTERPRISE_POLICY_STATE, "doctrine-policy", snapshot["policy"], idempotency_key="doctrine-policy"),
            ),
        )
        self.checkpoint(checkpoint_id, {"runtime_mode": snapshot["runtime"].get("mode", ""), "admission_count": len(snapshot["runtime"].get("admissions", ()))})
        return records

    def recover_runtime(self, *, mode: RecoveryMode = RecoveryMode.PLANNED_RESTART) -> tuple[CanonicalEnterpriseRuntime, RecoveryAuditRecord]:
        started = utc_timestamp()
        self.validate_identity()
        runtime = CanonicalEnterpriseRuntime()
        restored: list[str] = []
        deferred: list[str] = []
        failed: list[str] = []
        runtime_payload = self.latest_payload(ObjectType.ENTERPRISE_RUNTIME_STATE, "canonical-runtime")
        mission_payload = self.latest_payload(ObjectType.ENTERPRISE_MISSION_STATE, "canonical-missions")
        workflow_payload = self.latest_payload(ObjectType.ENTERPRISE_WORKFLOW_STATE, "canonical-workflows")
        if mission_payload:
            runtime.components.scheduler.recover_from_snapshot(mission_payload.get("scheduler", {}))
            runtime.components.mission_planner.recover_from_snapshot(mission_payload.get("mission_planner", {}))
            restored.append("missions")
        else:
            deferred.append("missions")
        if workflow_payload:
            runtime.components.workflow_orchestrator.recover_from_snapshot(workflow_payload)
            restored.append("workflows")
        else:
            deferred.append("workflows")
        if runtime_payload:
            runtime.restore_enterprise_persistence_snapshot(runtime_payload)
            restored.append("runtime")
        else:
            deferred.append("runtime")
        for object_type, object_id, label in (
            (ObjectType.ENTERPRISE_BROKER_STATE, "paper-broker", "broker"),
            (ObjectType.ENTERPRISE_POSITION_STATE, "position-registry", "positions"),
            (ObjectType.ENTERPRISE_PERFORMANCE_TRUTH, "performance-truth-paper", "performance_truth"),
        ):
            if self.latest_payload(object_type, object_id):
                restored.append(label)
            else:
                deferred.append(label)
        allowed = not any(item.severity == RecoverySeverity.CRITICAL for item in self._diagnostics)
        if allowed:
            runtime.start()
        else:
            runtime.mode = CanonicalRuntimeMode.FAULTED
        audit = RecoveryAuditRecord(
            audit_id=f"OR006-REC-{len(self.repository.all_records()) + 1:06d}",
            recovery_mode=mode,
            started_at=started,
            completed_at=utc_timestamp(),
            restored_entities=tuple(restored),
            deferred_entities=tuple(deferred),
            failed_entities=tuple(failed),
            diagnostics=tuple(asdict(item) for item in self._diagnostics),
            paper_operation_allowed=allowed,
        )
        self.persist_authoritative(ObjectType.ENTERPRISE_RECOVERY_AUDIT, audit.audit_id, asdict(audit), truth_domain="RECOVERY", idempotency_key=audit.audit_id, require_new_identity=True)
        return runtime, audit

    def latest_payload(self, object_type: ObjectType, object_id: str) -> dict[str, Any]:
        record = self.repository.latest(object_type, object_id)
        if not record:
            return {}
        envelope = dict(record.payload)
        payload = dict(envelope.get("payload", {}))
        if envelope.get("payload_hash") != _stable_hash(payload):
            self._diagnostic("PAYLOAD_HASH_MISMATCH", RecoverySeverity.CRITICAL, object_type.value, f"{object_id} payload hash mismatch", False)
            raise EnterprisePersistenceError(f"payload hash mismatch for {object_type.value}:{object_id}")
        return payload

    def validate_identity(self) -> bool:
        seen: set[tuple[str, str, int]] = set()
        latest_parent_ids = set()
        for record in self.repository.all_records():
            key = (record.object_type.value, record.object_id, record.version)
            if key in seen:
                self._diagnostic("DUPLICATE_RECORD_IDENTITY", RecoverySeverity.CRITICAL, record.object_type.value, record.object_id, False)
                raise EnterprisePersistenceError(f"duplicate persistent identity: {key}")
            seen.add(key)
            latest_parent_ids.add((record.object_type.value, record.object_id))
        self.repository.validate_integrity()
        return True

    def diagnostics(self) -> tuple[PersistenceDiagnostic, ...]:
        return tuple(self._diagnostics)

    def _preflight_write(self, object_type: ObjectType, object_id: str, *, require_new_identity: bool) -> None:
        if self.fail_writes:
            self._diagnostic("PERSISTENCE_BACKEND_UNAVAILABLE", RecoverySeverity.CRITICAL, object_type.value, "Configured write failure.", False)
            raise EnterprisePersistenceError("persistence backend unavailable")
        if require_new_identity and self.repository.latest(object_type, object_id):
            self._diagnostic("DUPLICATE_IDENTITY_REJECTED", RecoverySeverity.CRITICAL, object_type.value, object_id, False)
            raise EnterprisePersistenceError(f"duplicate identity rejected: {object_type.value}:{object_id}")

    def _operational_truth_envelope(self, object_type: ObjectType, object_id: str, truth_envelope: OperationalTruthEnvelope | dict[str, Any] | None) -> dict[str, Any]:
        if object_type not in OPERATIONAL_AUTHORITY_OBJECT_TYPES:
            return {}
        try:
            envelope = require_operational_truth_envelope(truth_envelope, target_authority="DurableEnterprisePersistenceStore")
            promotion = TruthPromotionAuthority().promote_operational_envelope(
                truth_envelope,
                scope=PromotionScope.PERFORMANCE_TRUTH_INGESTION,
                requested_consumer="PerformanceTruthEngine",
                object_type=object_type.value,
                object_id=object_id,
            )
            if promotion.decision != PromotionDecisionStatus.APPROVED:
                raise TruthEnvelopeError(promotion.reason_codes)
            return {**envelope, "eo_dc_promotion_decision": asdict(promotion)}
        except TruthEnvelopeError as exc:
            self._diagnostic("TRUTH_ENVELOPE_REJECTED", RecoverySeverity.CRITICAL, object_type.value, f"{object_id}: {','.join(exc.codes)}", False)
            raise EnterprisePersistenceError(f"truth envelope rejected for {object_type.value}:{object_id}: {','.join(exc.codes)}") from exc

    def _runtime_truth_envelope(self, authority: str, source_event_id: str, idempotency_key: str) -> OperationalTruthEnvelope:
        return make_paper_operational_truth_envelope(
            originating_authority=authority,
            originating_workflow_id="OR006-RUNTIME-SNAPSHOT",
            workflow_token_id="OR006-RUNTIME-TOKEN",
            mission_id="OR006-PERSISTENCE-MISSION",
            source_event_id=source_event_id,
            idempotency_key=idempotency_key,
            timestamp_utc=utc_timestamp(),
            caller="DurableEnterprisePersistenceStore",
            source_system="CanonicalEnterpriseRuntime",
        )

    def _envelope(self, entity_id: str, payload: dict[str, Any], *, truth_domain: str, idempotency_key: str, operational_truth_envelope: dict[str, Any] | None = None) -> dict[str, Any]:
        existing = max((record.version for record in self.repository.all_records()), default=0)
        clean_payload = _json_ready(payload)
        return {
            "entity_id": entity_id,
            "schema_version": "1.0.0",
            "truth_domain": truth_domain,
            "serialization_version": "OR-006.1",
            "creation_sequence": existing + 1,
            "modification_sequence": existing + 1,
            "payload": clean_payload,
            "payload_hash": _stable_hash(clean_payload),
            "idempotency_key": idempotency_key or entity_id,
            "operational_truth_envelope": operational_truth_envelope or {},
            "migration_compatibility": {"minimum_reader": "OR-006.1", "history_rewrite_allowed": False},
        }

    def _flush(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        bundle = BackupService(self.repository).create_backup()
        self.path.write_text(json.dumps(asdict(bundle), sort_keys=True, indent=2), encoding="utf-8")

    def _load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        BackupService(self.repository).restore(BackupBundle(records=tuple(raw["records"]), backup_hash=raw["backup_hash"]))

    def _diagnostic(self, code: str, severity: RecoverySeverity, component: str, explanation: str, recoverable: bool) -> None:
        self._diagnostics.append(PersistenceDiagnostic(code, severity, component, explanation, recoverable))


def enterprise_persistence_inventory() -> tuple[PersistenceInventoryItem, ...]:
    return ENTERPRISE_PERSISTENCE_INVENTORY


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(_json_ready(payload), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


ENTERPRISE_PERSISTENCE_INVENTORY: tuple[PersistenceInventoryItem, ...] = (
    PersistenceInventoryItem("Runtime", "CanonicalEnterpriseRuntime", PersistenceCategory.EPHEMERAL, ObjectType.ENTERPRISE_RUNTIME_STATE.value, "hash_chained_json_backup", "OR-006", 5, "PAPER", "canonical-runtime singleton", "fail_closed"),
    PersistenceInventoryItem("Scheduler/Missions", "EnterpriseOperationsScheduler", PersistenceCategory.AUTHORITATIVE, ObjectType.ENTERPRISE_MISSION_STATE.value, "hash_chained_json_backup", "EO-CA/OR-006", 7, "PAPER", "mission_id", "fail_closed"),
    PersistenceInventoryItem("Mission Plans", "EnterpriseMissionPlanner", PersistenceCategory.AUTHORITATIVE, ObjectType.ENTERPRISE_MISSION_STATE.value, "hash_chained_json_backup", "EO-CD/OR-006", 8, "PAPER", "mission_plan_id", "fail_closed"),
    PersistenceInventoryItem("Workflows/Tokens", "EnterpriseWorkflowOrchestrator", PersistenceCategory.AUTHORITATIVE, ObjectType.ENTERPRISE_WORKFLOW_STATE.value, "hash_chained_json_backup", "LAW_VII/OR-006", 9, "PAPER", "workflow_id and token audit id", "fail_closed"),
    PersistenceInventoryItem("Broker Orders/Fills", "DeterministicPaperBrokerage", PersistenceCategory.AUTHORITATIVE, ObjectType.ENTERPRISE_BROKER_STATE.value, "hash_chained_json_backup", "OR-003/OR-006", 12, "PAPER", "order_id/fill_id", "degraded_recovery"),
    PersistenceInventoryItem("Positions", "PositionRegistry", PersistenceCategory.AUTHORITATIVE, ObjectType.ENTERPRISE_POSITION_STATE.value, "hash_chained_json_backup", "OR-004/OR-006", 15, "PAPER", "position_id/fill_id", "fail_closed"),
    PersistenceInventoryItem("Performance Truth", "PerformanceTruthEngine", PersistenceCategory.AUTHORITATIVE, ObjectType.ENTERPRISE_PERFORMANCE_TRUTH.value, "hash_chained_json_backup", "PerformanceTruth/OR-006", 17, "PAPER", "record id + truth domain", "fail_closed"),
    PersistenceInventoryItem("Policy/Doctrine", "EnterpriseDoctrinePolicyManager", PersistenceCategory.AUTHORITATIVE, ObjectType.ENTERPRISE_POLICY_STATE.value, "hash_chained_json_backup", "EO-CO/OR-006", 3, "PAPER", "policy version id", "fail_closed"),
    PersistenceInventoryItem("Runtime Checkpoints", "CanonicalEnterpriseRuntime", PersistenceCategory.EPHEMERAL, ObjectType.ENTERPRISE_RUNTIME_CHECKPOINT.value, "hash_chained_json_backup", "OR-006", 22, "RUNTIME_CHECKPOINT", "checkpoint_id", "ignore_if_authoritative_state_disagrees"),
)
