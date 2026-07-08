"""Chief of Staff validation and routing service."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from argos.foundation.audit import AuditService
from argos.foundation.communication import CourierService, IncomingMailbox, OutgoingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType

from .briefing import ExecutiveBriefingPacket
from .engine import CommanderDecision, CommanderDecisionEngine, CommanderDecisionOutcome
from .mailboxes import EXECUTIVE_GROUP_ID
from .workflow import ExecutiveClock, ExecutiveSummaryGenerator, PacketStatus, PacketValidationResult


CHIEF_OF_STAFF_ID = "STF-003"


@dataclass(frozen=True)
class ExecutiveDocumentManifest:
    """Manifest for documents referenced by an EBP."""

    document_id: str
    report_type: str
    content_hash: str
    signature_hash: str
    created_clock_tick: int
    claim_key: str | None = None
    claim_value: str | None = None


@dataclass(frozen=True)
class ChiefOfStaffResult:
    """Chief of Staff packet processing result."""

    accepted: bool
    ebp_id: str
    summary: str
    validation_errors: tuple[str, ...]
    commander_outcome: CommanderDecisionOutcome | None = None
    rejection_contract_id: str | None = None


class ChiefOfStaffValidator:
    """Validate complete Executive Briefing Packets."""

    def __init__(self, max_report_age_ticks: int = 5) -> None:
        self.max_report_age_ticks = max_report_age_ticks

    def validate(
        self,
        ebp: ExecutiveBriefingPacket,
        manifests: dict[str, ExecutiveDocumentManifest],
        current_tick: int,
    ) -> PacketValidationResult:
        """Validate integrity, signatures, evidence, snapshots, and contradictions."""
        errors: list[str] = []
        if ebp.produced_by_staff_id != CHIEF_OF_STAFF_ID:
            errors.append("EBP must be produced by Chief of Staff")
        if ebp.produced_by_group_id != EXECUTIVE_GROUP_ID:
            errors.append("EBP must be produced by Executive Group")
        if not ebp.document_signature_hash:
            errors.append("missing EBP signature")
        if not ebp.configuration_snapshot_hash:
            errors.append("missing configuration snapshot")
        if not ebp.prompt_snapshot_id:
            errors.append("missing prompt snapshot")
        if not ebp.model_snapshot_id:
            errors.append("missing model snapshot")

        references = list(ebp.source_reference_ids())
        if len(references) != len(set(references)):
            errors.append("duplicate report references")

        risk_manifest = manifests.get(ebp.risk_recommendation_document_id)
        if risk_manifest is None:
            errors.append("missing risk report")
        elif risk_manifest.report_type != "risk":
            errors.append("risk document is not a risk report")

        claim_values: dict[str, str] = {}
        for document_id in references:
            manifest = manifests.get(document_id)
            if manifest is None:
                errors.append(f"missing report: {document_id}")
                continue
            if manifest.document_id != document_id:
                errors.append(f"document integrity mismatch: {document_id}")
            if not _valid_hash(manifest.content_hash):
                errors.append(f"invalid content hash: {document_id}")
            if not _valid_hash(manifest.signature_hash):
                errors.append(f"invalid signature: {document_id}")
            if current_tick - manifest.created_clock_tick > self.max_report_age_ticks:
                errors.append(f"stale report: {document_id}")
            if manifest.claim_key is not None and manifest.claim_value is not None:
                existing = claim_values.get(manifest.claim_key)
                if existing is not None and existing != manifest.claim_value:
                    errors.append(f"contradictory reports for claim: {manifest.claim_key}")
                claim_values[manifest.claim_key] = manifest.claim_value

        return PacketValidationResult(
            status=PacketStatus.REJECTED if errors else PacketStatus.VALIDATED,
            errors=tuple(errors),
        )


class ChiefOfStaffService:
    """Chief of Staff service for EBP validation and routing."""

    def __init__(
        self,
        commander_engine: CommanderDecisionEngine,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        validator: ChiefOfStaffValidator | None = None,
        clock: ExecutiveClock | None = None,
        summary_generator: ExecutiveSummaryGenerator | None = None,
    ) -> None:
        self.commander_engine = commander_engine
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.validator = validator or ChiefOfStaffValidator()
        self.clock = clock or ExecutiveClock()
        self.summary_generator = summary_generator or ExecutiveSummaryGenerator()
        self.outbox = OutgoingMailbox(CHIEF_OF_STAFF_ID, EXECUTIVE_GROUP_ID)
        self.routing_log: list[dict[str, object]] = []

    def process_packet(
        self,
        ebp: ExecutiveBriefingPacket,
        manifests: dict[str, ExecutiveDocumentManifest],
        decision: CommanderDecision,
        rationale: str,
        document_sequence: int,
        intended_consumer_group_id: str,
        rejection_inbox: IncomingMailbox,
        resize_factor: float | None = None,
    ) -> ChiefOfStaffResult:
        """Validate an EBP and route it to Commander or return it via Courier."""
        self.configuration_service.validate_startup()
        tick = self.clock.tick()
        validation = self.validator.validate(ebp, manifests, tick)
        summary = self.summary_generator.generate(ebp, validation)
        self._persist_validation(ebp, validation, summary)

        if not validation.passed:
            rejection = self._rejection_contract(ebp, validation, document_sequence, rejection_inbox.owner_group_id)
            result = CourierService(self.audit_service).deliver(self.outbox, rejection_inbox, rejection)
            self._log(tick, "rejected_returned", ebp.ebp_id, result.delivered, summary)
            return ChiefOfStaffResult(
                accepted=False,
                ebp_id=ebp.ebp_id,
                summary=summary,
                validation_errors=validation.errors,
                rejection_contract_id=rejection.contract_id,
            )

        outcome = self.commander_engine.decide(
            ebp,
            decision,
            rationale,
            document_sequence,
            intended_consumer_group_id,
            resize_factor=resize_factor,
        )
        self._log(tick, "approved_to_commander", ebp.ebp_id, True, summary)
        return ChiefOfStaffResult(
            accepted=True,
            ebp_id=ebp.ebp_id,
            summary=summary,
            validation_errors=(),
            commander_outcome=outcome,
        )

    def _persist_validation(
        self,
        ebp: ExecutiveBriefingPacket,
        validation: PacketValidationResult,
        summary: str,
    ) -> None:
        self.persistence_repository.persist(
            ObjectType.OPERATIONAL_DOCUMENT,
            ebp.ebp_id.replace("EBP", "DOC"),
            {
                "contract_id": ebp.ebp_id.replace("EBP", "DOC"),
                "case_file_id": ebp.case_file_id,
                "trade_cycle_id": ebp.trade_cycle_id,
                "ebp_id": ebp.ebp_id,
                "validation_status": validation.status.value,
                "validation_errors": list(validation.errors),
                "summary": summary,
            },
        )

    def _rejection_contract(
        self,
        ebp: ExecutiveBriefingPacket,
        validation: PacketValidationResult,
        document_sequence: int,
        intended_consumer_group_id: str,
    ) -> OperationalContract:
        created = utc_timestamp()
        payload = {
            "ebp_id": ebp.ebp_id,
            "errors": list(validation.errors),
            "summary": "Executive packet rejected by Chief of Staff.",
        }
        source_reference_ids = tuple(dict.fromkeys(ebp.source_reference_ids()))
        signature_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type="EBP_REJECTION",
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=ebp.case_file_id,
            trade_cycle_id=ebp.trade_cycle_id,
            parent_contract_ids=source_reference_ids,
            produced_by_staff_id=CHIEF_OF_STAFF_ID,
            produced_by_group_id=EXECUTIVE_GROUP_ID,
            intended_consumer_group_id=intended_consumer_group_id,
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary=f"EBP {ebp.ebp_id} rejected by Chief of Staff.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_reference_ids,
        )

    def _log(self, tick: int, action: str, ebp_id: str, delivered: bool, detail: str) -> None:
        self.routing_log.append(
            {
                "sequence": len(self.routing_log) + 1,
                "clock_tick": tick,
                "action": action,
                "ebp_id": ebp_id,
                "delivered": delivered,
                "detail": detail,
            }
        )


def _valid_hash(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
