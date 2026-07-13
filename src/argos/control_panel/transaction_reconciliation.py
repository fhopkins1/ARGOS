"""EO-DD transaction and reconciliation coordinator.

The coordinator is an evidence authority, not a financial mutation authority. It
records immutable intent, participant acknowledgments, idempotency, recovery, and
reconciliation outcomes so partial cross-ledger transactions cannot appear
complete.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .constitutional_invariants import BrokerPositionInvariantMonitor
from .truth_promotion import PromotionDecision, PromotionDecisionStatus


EO_DD_VERSION = "EO-DD.1"


class TransactionCoordinatorError(ValueError):
    """Raised when EO-DD rejects a transaction coordination request."""


class TransactionType(str, Enum):
    OPENING_FILL = "OPENING_FILL"
    PARTIAL_OPENING_FILL = "PARTIAL_OPENING_FILL"
    POSITION_INCREASE = "POSITION_INCREASE"
    PARTIAL_REDUCTION = "PARTIAL_REDUCTION"
    FULL_CLOSURE = "FULL_CLOSURE"
    ORDER_CANCELLATION = "ORDER_CANCELLATION"
    ORDER_EXPIRATION = "ORDER_EXPIRATION"
    SETTLEMENT = "SETTLEMENT"
    REVERSAL = "REVERSAL"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    RECOVERY = "RECOVERY"
    RECONCILIATION_CORRECTION = "RECONCILIATION_CORRECTION"


class TransactionState(str, Enum):
    INTENT_CREATED = "INTENT_CREATED"
    INTENT_PERSISTED = "INTENT_PERSISTED"
    PRECONDITIONS_VALIDATED = "PRECONDITIONS_VALIDATED"
    PARTICIPANTS_READY = "PARTICIPANTS_READY"
    APPLYING = "APPLYING"
    PARTIALLY_APPLIED = "PARTIALLY_APPLIED"
    RECONCILIATION_PENDING = "RECONCILIATION_PENDING"
    RECONCILED = "RECONCILED"
    COMMITTED = "COMMITTED"
    HISTORICALLY_PRESERVED = "HISTORICALLY_PRESERVED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_NONRETRYABLE = "FAILED_NONRETRYABLE"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    QUARANTINED = "QUARANTINED"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED_BEFORE_APPLICATION = "CANCELLED_BEFORE_APPLICATION"
    INCONCLUSIVE = "INCONCLUSIVE"


class ParticipantState(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    APPLIED = "APPLIED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FAILED = "FAILED"
    RETRY_PENDING = "RETRY_PENDING"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    QUARANTINED = "QUARANTINED"
    ROLLED_FORWARD = "ROLLED_FORWARD"
    SUPERSEDED = "SUPERSEDED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DiscrepancySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFORMATIONAL = "INFORMATIONAL"


class ReconciliationStrategy(str, Enum):
    VERIFY_ONLY = "VERIFY_ONLY"
    ROLL_FORWARD_REQUIRED = "ROLL_FORWARD_REQUIRED"
    QUARANTINE_ON_CONFLICT = "QUARANTINE_ON_CONFLICT"


class RecoveryStrategy(str, Enum):
    REPLAY_JOURNAL_ONLY = "REPLAY_JOURNAL_ONLY"
    RESUME_AFTER_RECONCILIATION = "RESUME_AFTER_RECONCILIATION"
    QUARANTINE_RETRY = "QUARANTINE_RETRY"


@dataclass(frozen=True)
class TransactionTypeDefinition:
    transaction_type: TransactionType
    required_participants: tuple[str, ...]
    requires_eodc_approval: bool
    creates_financial_truth: bool
    coordinator_mutation_authority: bool


TRANSACTION_TYPE_REGISTRY: tuple[TransactionTypeDefinition, ...] = (
    TransactionTypeDefinition(TransactionType.OPENING_FILL, ("Paper Broker", "Position Registry", "Performance Truth", "Historian"), True, True, False),
    TransactionTypeDefinition(TransactionType.PARTIAL_OPENING_FILL, ("Paper Broker", "Position Registry", "Performance Truth"), True, True, False),
    TransactionTypeDefinition(TransactionType.POSITION_INCREASE, ("Paper Broker", "Position Registry", "Performance Truth"), True, True, False),
    TransactionTypeDefinition(TransactionType.PARTIAL_REDUCTION, ("Paper Broker", "Position Registry", "Performance Truth"), True, True, False),
    TransactionTypeDefinition(TransactionType.FULL_CLOSURE, ("Paper Broker", "Position Registry", "Performance Truth", "Closed Position Truth", "Historian"), True, True, False),
    TransactionTypeDefinition(TransactionType.ORDER_CANCELLATION, ("Paper Broker", "Performance Truth"), True, False, False),
    TransactionTypeDefinition(TransactionType.ORDER_EXPIRATION, ("Paper Broker", "Performance Truth"), True, False, False),
    TransactionTypeDefinition(TransactionType.SETTLEMENT, ("Paper Broker", "Performance Truth", "Historian"), True, True, False),
    TransactionTypeDefinition(TransactionType.REVERSAL, ("Paper Broker", "Position Registry", "Performance Truth", "Historian"), True, True, False),
    TransactionTypeDefinition(TransactionType.CORPORATE_ACTION, ("Position Registry", "Performance Truth", "Historian"), True, True, False),
    TransactionTypeDefinition(TransactionType.RECOVERY, ("Transaction Coordinator", "Performance Truth", "Historian"), True, False, False),
    TransactionTypeDefinition(TransactionType.RECONCILIATION_CORRECTION, ("Transaction Coordinator", "Performance Truth", "Historian"), True, False, False),
)


@dataclass(frozen=True)
class TransactionIntent:
    transaction_id: str
    transaction_type: TransactionType
    schema_version: str
    truth_domain: str
    eodc_decision_id: str
    eodc_decision: str
    source_authority: str
    source_event_id: str
    mission_id: str
    workflow_id: str
    workflow_execution_token_id: str
    asset_id: str
    account_id: str
    order_id: str
    fill_id: str
    position_id: str
    intended_participants: tuple[str, ...]
    required_participant_actions: tuple[str, ...]
    participant_dependency_order: tuple[str, ...]
    idempotency_key: str
    expected_preconditions: tuple[str, ...]
    expected_postconditions: tuple[str, ...]
    doctrine_version: str
    policy_version: str
    creation_sequence: int
    created_at_utc: str
    expiration_utc: str
    recovery_strategy: RecoveryStrategy
    reconciliation_strategy: ReconciliationStrategy
    transaction_hash: str


@dataclass(frozen=True)
class TransactionParticipant:
    participant_id: str
    transaction_id: str
    authority: str
    required_action: str
    state: ParticipantState
    dependency_order: int
    last_evidence_reference: str = ""
    last_output_version: str = ""
    ack_count: int = 0
    failure_code: str = ""
    updated_at_utc: str = ""


@dataclass(frozen=True)
class ParticipantAcknowledgment:
    acknowledgment_id: str
    transaction_id: str
    participant_authority: str
    participant_state: ParticipantState
    evidence_reference: str
    output_version: str
    timestamp_utc: str
    idempotency_key: str


@dataclass(frozen=True)
class TransactionJournalRecord:
    journal_sequence: int
    transaction_id: str
    event_type: str
    state: TransactionState
    payload: dict[str, Any]
    timestamp_utc: str
    previous_record_hash: str
    record_hash: str


@dataclass(frozen=True)
class ReconciliationDiscrepancy:
    discrepancy_id: str
    transaction_id: str
    severity: DiscrepancySeverity
    domain: str
    code: str
    evidence: dict[str, Any]
    blocks_commit: bool


@dataclass(frozen=True)
class ReconciliationResult:
    transaction_id: str
    verdict: str
    discrepancies: tuple[ReconciliationDiscrepancy, ...]
    checked_at_utc: str
    eoda_monitor: str
    blocks_commit: bool


@dataclass(frozen=True)
class TransactionOutboxEvent:
    event_id: str
    transaction_id: str
    destination_authority: str
    event_type: str
    payload: dict[str, Any]
    created_at_utc: str
    delivered: bool = False


@dataclass(frozen=True)
class TransactionSnapshot:
    transaction_id: str
    transaction_type: str
    state: str
    intent: dict[str, Any]
    participants: tuple[dict[str, Any], ...]
    acknowledgments: tuple[dict[str, Any], ...]
    reconciliation: dict[str, Any] | None
    journal_depth: int


class TransactionJournal:
    """Append-only hash-chained journal with idempotent intent indexing."""

    def __init__(self) -> None:
        self.records: list[TransactionJournalRecord] = []
        self.intents: dict[str, TransactionIntent] = {}
        self.idempotency_index: dict[str, str] = {}
        self.states: dict[str, TransactionState] = {}
        self.participants: dict[str, dict[str, TransactionParticipant]] = {}
        self.acknowledgments: dict[str, dict[str, ParticipantAcknowledgment]] = {}
        self.reconciliations: dict[str, ReconciliationResult] = {}
        self.outbox: list[TransactionOutboxEvent] = []

    def persist_intent(self, intent: TransactionIntent, participants: tuple[TransactionParticipant, ...]) -> tuple[TransactionIntent, bool]:
        existing_id = self.idempotency_index.get(intent.idempotency_key)
        if existing_id:
            return self.intents[existing_id], False
        self.intents[intent.transaction_id] = intent
        self.idempotency_index[intent.idempotency_key] = intent.transaction_id
        self.states[intent.transaction_id] = TransactionState.INTENT_PERSISTED
        self.participants[intent.transaction_id] = {participant.authority: participant for participant in participants}
        self.acknowledgments[intent.transaction_id] = {}
        self.append(intent.transaction_id, "INTENT_PERSISTED", TransactionState.INTENT_PERSISTED, {"intent": _jsonable(asdict(intent))})
        for participant in participants:
            self.outbox.append(
                TransactionOutboxEvent(
                    event_id=f"EO-DD-OUTBOX-{len(self.outbox) + 1:06d}",
                    transaction_id=intent.transaction_id,
                    destination_authority=participant.authority,
                    event_type="PARTICIPANT_REQUIRED",
                    payload={"requiredAction": participant.required_action, "dependencyOrder": participant.dependency_order},
                    created_at_utc=utc_timestamp(),
                )
            )
        return intent, True

    def append(self, transaction_id: str, event_type: str, state: TransactionState, payload: dict[str, Any]) -> TransactionJournalRecord:
        previous_hash = self.records[-1].record_hash if self.records else "GENESIS"
        sequence = len(self.records) + 1
        body = {
            "journal_sequence": sequence,
            "transaction_id": transaction_id,
            "event_type": event_type,
            "state": state.value,
            "payload": _jsonable(payload),
            "previous_record_hash": previous_hash,
        }
        record_hash = _stable_hash(body)
        record = TransactionJournalRecord(
            journal_sequence=sequence,
            transaction_id=transaction_id,
            event_type=event_type,
            state=state,
            payload=_jsonable(payload),
            timestamp_utc=utc_timestamp(),
            previous_record_hash=previous_hash,
            record_hash=record_hash,
        )
        self.records.append(record)
        self.states[transaction_id] = state
        return record

    def acknowledge(self, transaction_id: str, authority: str, evidence_reference: str, output_version: str, *, participant_state: ParticipantState = ParticipantState.ACKNOWLEDGED, idempotency_key: str = "") -> ParticipantAcknowledgment:
        if transaction_id not in self.intents:
            raise TransactionCoordinatorError("TRANSACTION_UNKNOWN")
        participant_map = self.participants.get(transaction_id, {})
        if authority not in participant_map:
            raise TransactionCoordinatorError("PARTICIPANT_NOT_REGISTERED")
        ack_key = idempotency_key or f"{transaction_id}:{authority}:{evidence_reference}:{output_version}"
        existing = self.acknowledgments[transaction_id].get(ack_key)
        if existing:
            return existing
        participant = participant_map[authority]
        updated = replace(
            participant,
            state=participant_state,
            last_evidence_reference=evidence_reference,
            last_output_version=output_version,
            ack_count=participant.ack_count + 1,
            updated_at_utc=utc_timestamp(),
        )
        participant_map[authority] = updated
        acknowledgment = ParticipantAcknowledgment(
            acknowledgment_id=f"EO-DD-ACK-{sum(len(items) for items in self.acknowledgments.values()) + 1:06d}",
            transaction_id=transaction_id,
            participant_authority=authority,
            participant_state=participant_state,
            evidence_reference=evidence_reference,
            output_version=output_version,
            timestamp_utc=utc_timestamp(),
            idempotency_key=ack_key,
        )
        self.acknowledgments[transaction_id][ack_key] = acknowledgment
        self.append(transaction_id, "PARTICIPANT_ACKNOWLEDGED", TransactionState.PARTIALLY_APPLIED, {"acknowledgment": _jsonable(asdict(acknowledgment))})
        return acknowledgment

    def record_reconciliation(self, result: ReconciliationResult) -> ReconciliationResult:
        self.reconciliations[result.transaction_id] = result
        state = TransactionState.RECONCILIATION_PENDING if result.blocks_commit else TransactionState.RECONCILED
        self.append(result.transaction_id, "RECONCILIATION_EVALUATED", state, {"result": _jsonable(asdict(result))})
        return result

    def validate_integrity(self) -> tuple[dict[str, Any], ...]:
        findings: list[dict[str, Any]] = []
        previous = "GENESIS"
        for record in self.records:
            body = {
                "journal_sequence": record.journal_sequence,
                "transaction_id": record.transaction_id,
                "event_type": record.event_type,
                "state": record.state.value,
                "payload": _jsonable(record.payload),
                "previous_record_hash": record.previous_record_hash,
            }
            if record.previous_record_hash != previous:
                findings.append({"code": "HASH_CHAIN_PREVIOUS_MISMATCH", "sequence": record.journal_sequence})
            if _stable_hash(body) != record.record_hash:
                findings.append({"code": "HASH_CHAIN_RECORD_MISMATCH", "sequence": record.journal_sequence})
            previous = record.record_hash
        return tuple(findings)


class TransactionReconciliationCoordinator:
    """EO-DD canonical coordinator for cross-ledger transaction completion."""

    financial_mutation_authority = False
    live_trading_enabled = False

    def __init__(self, journal: TransactionJournal | None = None) -> None:
        self.journal = journal or TransactionJournal()
        self._sequence = 0
        self._eoda_broker_position_monitor = BrokerPositionInvariantMonitor()

    def create_intent(
        self,
        transaction_type: TransactionType | str,
        *,
        eodc_decision: PromotionDecision | dict[str, Any],
        source_authority: str,
        source_event_id: str,
        mission_id: str,
        workflow_id: str,
        workflow_execution_token_id: str,
        asset_id: str,
        account_id: str,
        order_id: str = "",
        fill_id: str = "",
        position_id: str = "",
        idempotency_key: str = "",
        truth_domain: str = "PAPER",
        expected_preconditions: tuple[str, ...] = (),
        expected_postconditions: tuple[str, ...] = (),
        doctrine_version: str = "",
        policy_version: str = "",
        expiration_utc: str = "",
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.RESUME_AFTER_RECONCILIATION,
        reconciliation_strategy: ReconciliationStrategy = ReconciliationStrategy.QUARANTINE_ON_CONFLICT,
    ) -> TransactionIntent:
        tx_type = TransactionType(transaction_type)
        definition = _definition_for(tx_type)
        self._validate_preconditions(
            eodc_decision=eodc_decision,
            truth_domain=truth_domain,
            source_authority=source_authority,
            mission_id=mission_id,
            workflow_id=workflow_id,
            workflow_execution_token_id=workflow_execution_token_id,
            definition=definition,
        )
        key = idempotency_key or _stable_hash(
            {
                "type": tx_type.value,
                "source": source_authority,
                "event": source_event_id,
                "mission": mission_id,
                "workflow": workflow_id,
                "token": workflow_execution_token_id,
                "asset": asset_id,
                "account": account_id,
                "order": order_id,
                "fill": fill_id,
                "position": position_id,
            }
        )
        existing_id = self.journal.idempotency_index.get(key)
        if existing_id:
            return self.journal.intents[existing_id]
        self._sequence += 1
        eodc = _decision_dict(eodc_decision)
        transaction_id = f"EO-DD-TX-{self._sequence:06d}"
        participant_actions = tuple(f"{authority}: acknowledge durable application evidence" for authority in definition.required_participants)
        participant_order = definition.required_participants
        intent_payload = {
            "transaction_id": transaction_id,
            "transaction_type": tx_type.value,
            "schema_version": EO_DD_VERSION,
            "truth_domain": truth_domain,
            "eodc_decision_id": str(eodc.get("decision_id", "")),
            "eodc_decision": str(eodc.get("decision", "")),
            "source_authority": source_authority,
            "source_event_id": source_event_id,
            "mission_id": mission_id,
            "workflow_id": workflow_id,
            "workflow_execution_token_id": workflow_execution_token_id,
            "asset_id": asset_id,
            "account_id": account_id,
            "order_id": order_id,
            "fill_id": fill_id,
            "position_id": position_id,
            "intended_participants": participant_order,
            "required_participant_actions": participant_actions,
            "participant_dependency_order": participant_order,
            "idempotency_key": key,
            "expected_preconditions": expected_preconditions,
            "expected_postconditions": expected_postconditions,
            "doctrine_version": doctrine_version,
            "policy_version": policy_version,
            "creation_sequence": self._sequence,
            "created_at_utc": utc_timestamp(),
            "expiration_utc": expiration_utc,
            "recovery_strategy": recovery_strategy.value,
            "reconciliation_strategy": reconciliation_strategy.value,
        }
        transaction_hash = _stable_hash(intent_payload)
        intent = TransactionIntent(
            transaction_id=transaction_id,
            transaction_type=tx_type,
            schema_version=EO_DD_VERSION,
            truth_domain=truth_domain,
            eodc_decision_id=str(eodc.get("decision_id", "")),
            eodc_decision=str(eodc.get("decision", "")),
            source_authority=source_authority,
            source_event_id=source_event_id,
            mission_id=mission_id,
            workflow_id=workflow_id,
            workflow_execution_token_id=workflow_execution_token_id,
            asset_id=asset_id,
            account_id=account_id,
            order_id=order_id,
            fill_id=fill_id,
            position_id=position_id,
            intended_participants=participant_order,
            required_participant_actions=participant_actions,
            participant_dependency_order=participant_order,
            idempotency_key=key,
            expected_preconditions=expected_preconditions,
            expected_postconditions=expected_postconditions,
            doctrine_version=doctrine_version,
            policy_version=policy_version,
            creation_sequence=self._sequence,
            created_at_utc=str(intent_payload["created_at_utc"]),
            expiration_utc=expiration_utc,
            recovery_strategy=recovery_strategy,
            reconciliation_strategy=reconciliation_strategy,
            transaction_hash=transaction_hash,
        )
        participants = tuple(
            TransactionParticipant(
                participant_id=f"{transaction_id}-P{index:02d}",
                transaction_id=transaction_id,
                authority=authority,
                required_action=participant_actions[index - 1],
                state=ParticipantState.PENDING,
                dependency_order=index,
                updated_at_utc=utc_timestamp(),
            )
            for index, authority in enumerate(participant_order, start=1)
        )
        persisted, _ = self.journal.persist_intent(intent, participants)
        self.journal.append(persisted.transaction_id, "PRECONDITIONS_VALIDATED", TransactionState.PRECONDITIONS_VALIDATED, {"eodcDecision": _jsonable(eodc), "truthDomain": truth_domain})
        return persisted

    def coordinate_broker_fill(
        self,
        *,
        eodc_decision: PromotionDecision | dict[str, Any],
        source_authority: str,
        source_event_id: str,
        mission_id: str,
        workflow_id: str,
        workflow_execution_token_id: str,
        asset_id: str,
        account_id: str,
        order_id: str,
        fill_id: str,
        position_id: str = "",
        idempotency_key: str = "",
    ) -> TransactionIntent:
        return self.create_intent(
            TransactionType.OPENING_FILL,
            eodc_decision=eodc_decision,
            source_authority=source_authority,
            source_event_id=source_event_id,
            mission_id=mission_id,
            workflow_id=workflow_id,
            workflow_execution_token_id=workflow_execution_token_id,
            asset_id=asset_id,
            account_id=account_id,
            order_id=order_id,
            fill_id=fill_id,
            position_id=position_id,
            idempotency_key=idempotency_key,
            expected_preconditions=("EO-DC approval present", "paper truth domain only", "live trading disabled"),
            expected_postconditions=("broker fill has position lineage", "performance truth preserved", "historian evidence preserved"),
        )

    def acknowledge_participant(
        self,
        transaction_id: str,
        participant_authority: str,
        *,
        evidence_reference: str,
        output_version: str,
        idempotency_key: str = "",
        participant_state: ParticipantState = ParticipantState.ACKNOWLEDGED,
    ) -> ParticipantAcknowledgment:
        return self.journal.acknowledge(
            transaction_id,
            participant_authority,
            evidence_reference,
            output_version,
            participant_state=participant_state,
            idempotency_key=idempotency_key,
        )

    def evaluate_commit(self, transaction_id: str) -> TransactionState:
        intent = self._intent(transaction_id)
        participants = tuple(self.journal.participants.get(transaction_id, {}).values())
        missing = tuple(item.authority for item in participants if item.state != ParticipantState.ACKNOWLEDGED)
        reconciliation = self.journal.reconciliations.get(transaction_id)
        if missing:
            state = TransactionState.RECONCILIATION_PENDING if any(item.state == ParticipantState.ACKNOWLEDGED for item in participants) else TransactionState.PARTICIPANTS_READY
            self.journal.append(transaction_id, "COMMIT_BLOCKED_PARTICIPANT_ACK_MISSING", state, {"missingParticipants": missing})
            return state
        if reconciliation is None:
            self.journal.append(transaction_id, "COMMIT_BLOCKED_RECONCILIATION_MISSING", TransactionState.RECONCILIATION_PENDING, {"transactionHash": intent.transaction_hash})
            return TransactionState.RECONCILIATION_PENDING
        if reconciliation.blocks_commit:
            self.journal.append(transaction_id, "COMMIT_BLOCKED_RECONCILIATION_CONFLICT", TransactionState.BLOCKED, {"discrepancies": tuple(asdict(item) for item in reconciliation.discrepancies)})
            return TransactionState.BLOCKED
        self.journal.append(transaction_id, "TRANSACTION_COMMITTED", TransactionState.COMMITTED, {"transactionHash": intent.transaction_hash})
        return TransactionState.COMMITTED

    def reconcile_transaction(self, transaction_id: str, *, performance_truth_snapshot: dict[str, Any] | None = None, evidence: dict[str, Any] | None = None) -> ReconciliationResult:
        self._intent(transaction_id)
        discrepancies: list[ReconciliationDiscrepancy] = []
        if performance_truth_snapshot is not None:
            for index, violation in enumerate(self._eoda_broker_position_monitor.violations(performance_truth_snapshot), start=1):
                discrepancies.append(
                    ReconciliationDiscrepancy(
                        discrepancy_id=f"EO-DD-DISC-{transaction_id}-{index:03d}",
                        transaction_id=transaction_id,
                        severity=DiscrepancySeverity.CRITICAL if str(violation.get("domain", "")) in {"BROKER", "POSITION"} else DiscrepancySeverity.MAJOR,
                        domain=str(violation.get("domain", "UNKNOWN")),
                        code=str(violation.get("code", "UNKNOWN_DISCREPANCY")),
                        evidence=dict(violation),
                        blocks_commit=True,
                    )
                )
        for index, finding in enumerate(tuple((evidence or {}).get("discrepancies", ()) or ()), start=len(discrepancies) + 1):
            severity = DiscrepancySeverity(str(finding.get("severity", DiscrepancySeverity.MAJOR.value)))
            discrepancies.append(
                ReconciliationDiscrepancy(
                    discrepancy_id=f"EO-DD-DISC-{transaction_id}-{index:03d}",
                    transaction_id=transaction_id,
                    severity=severity,
                    domain=str(finding.get("domain", "EXTERNAL")),
                    code=str(finding.get("code", "EXTERNAL_DISCREPANCY")),
                    evidence=dict(finding),
                    blocks_commit=bool(finding.get("blocks_commit", severity in {DiscrepancySeverity.CRITICAL, DiscrepancySeverity.MAJOR})),
                )
            )
        result = ReconciliationResult(
            transaction_id=transaction_id,
            verdict="BLOCKED" if any(item.blocks_commit for item in discrepancies) else "RECONCILED",
            discrepancies=tuple(discrepancies),
            checked_at_utc=utc_timestamp(),
            eoda_monitor="BrokerPositionInvariantMonitor",
            blocks_commit=any(item.blocks_commit for item in discrepancies),
        )
        return self.journal.record_reconciliation(result)

    def recover_nonterminal(self) -> tuple[dict[str, Any], ...]:
        recovered: list[dict[str, Any]] = []
        terminal = {
            TransactionState.COMMITTED,
            TransactionState.HISTORICALLY_PRESERVED,
            TransactionState.REJECTED,
            TransactionState.FAILED_NONRETRYABLE,
            TransactionState.QUARANTINED,
            TransactionState.SUPERSEDED,
            TransactionState.CANCELLED_BEFORE_APPLICATION,
        }
        for transaction_id, state in tuple(self.journal.states.items()):
            if state not in terminal:
                self.journal.append(transaction_id, "RECOVERY_REPLAY_REQUIRED", TransactionState.RECOVERY_REQUIRED, {"previousState": state.value})
                recovered.append({"transactionId": transaction_id, "previousState": state.value, "recoveryState": TransactionState.RECOVERY_REQUIRED.value})
        return tuple(recovered)

    def snapshot(self, transaction_id: str) -> TransactionSnapshot:
        intent = self._intent(transaction_id)
        participants = tuple(asdict(item) for item in self.journal.participants.get(transaction_id, {}).values())
        acknowledgments = tuple(asdict(item) for item in self.journal.acknowledgments.get(transaction_id, {}).values())
        reconciliation = self.journal.reconciliations.get(transaction_id)
        return TransactionSnapshot(
            transaction_id=transaction_id,
            transaction_type=intent.transaction_type.value,
            state=self.journal.states.get(transaction_id, TransactionState.INCONCLUSIVE).value,
            intent=_jsonable(asdict(intent)),
            participants=tuple(_jsonable(item) for item in participants),
            acknowledgments=tuple(_jsonable(item) for item in acknowledgments),
            reconciliation=_jsonable(asdict(reconciliation)) if reconciliation else None,
            journal_depth=sum(1 for item in self.journal.records if item.transaction_id == transaction_id),
        )

    def commander_read_model(self) -> dict[str, Any]:
        snapshots = tuple(_jsonable(asdict(self.snapshot(transaction_id))) for transaction_id in self.journal.intents)
        blocked = tuple(item for item in snapshots if item["state"] in {TransactionState.BLOCKED.value, TransactionState.RECOVERY_REQUIRED.value, TransactionState.RECONCILIATION_PENDING.value})
        return {
            "engineName": "Transaction and Reconciliation Coordinator",
            "engineeringOrder": "EO-DD",
            "engineVersion": EO_DD_VERSION,
            "transactionCount": len(snapshots),
            "blockedOrRecoveryRequired": blocked,
            "journalIntegrityFindings": self.journal.validate_integrity(),
            "outboxDepth": len(self.journal.outbox),
            "transactionTypeRegistry": tuple(_jsonable(asdict(item)) for item in TRANSACTION_TYPE_REGISTRY),
            "commanderLimitations": {
                "mayCreateFill": False,
                "mayMutatePosition": False,
                "mayCreatePerformanceTruth": False,
                "mayFabricateRepair": False,
                "mayMarkPartialComplete": False,
                "mayEnableLiveTrading": False,
            },
            "financialMutationAuthority": self.financial_mutation_authority,
            "liveTradingEnabled": self.live_trading_enabled,
        }

    def _intent(self, transaction_id: str) -> TransactionIntent:
        if transaction_id not in self.journal.intents:
            raise TransactionCoordinatorError("TRANSACTION_UNKNOWN")
        return self.journal.intents[transaction_id]

    def _validate_preconditions(
        self,
        *,
        eodc_decision: PromotionDecision | dict[str, Any],
        truth_domain: str,
        source_authority: str,
        mission_id: str,
        workflow_id: str,
        workflow_execution_token_id: str,
        definition: TransactionTypeDefinition,
    ) -> None:
        if truth_domain != "PAPER":
            raise TransactionCoordinatorError("EO_DD_LIVE_OR_NON_PAPER_DOMAIN_DISABLED")
        if not source_authority:
            raise TransactionCoordinatorError("SOURCE_AUTHORITY_REQUIRED")
        if not mission_id or not workflow_id or not workflow_execution_token_id:
            raise TransactionCoordinatorError("WORKFLOW_LINEAGE_REQUIRED")
        eodc = _decision_dict(eodc_decision)
        decision = eodc.get("decision")
        decision_value = decision.value if isinstance(decision, Enum) else str(decision)
        if definition.requires_eodc_approval and decision_value != PromotionDecisionStatus.APPROVED.value:
            raise TransactionCoordinatorError("EO_DC_APPROVAL_REQUIRED")
        if not str(eodc.get("decision_id", "")):
            raise TransactionCoordinatorError("EO_DC_DECISION_ID_REQUIRED")


def _definition_for(transaction_type: TransactionType) -> TransactionTypeDefinition:
    for definition in TRANSACTION_TYPE_REGISTRY:
        if definition.transaction_type == transaction_type:
            return definition
    raise TransactionCoordinatorError("TRANSACTION_TYPE_UNREGISTERED")


def _decision_dict(decision: PromotionDecision | dict[str, Any]) -> dict[str, Any]:
    if isinstance(decision, PromotionDecision):
        return asdict(decision)
    return dict(decision or {})


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_jsonable(item) for item in value)
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

