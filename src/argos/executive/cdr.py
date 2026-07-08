"""Command Decision Record generation."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json

from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id

from .decisions import DecisionRecord
from .mailboxes import COMMANDER_STAFF_ID, EXECUTIVE_GROUP_ID


class CommandDecisionRecordGenerator:
    """Generate CDR operational contracts from registered Executive decisions."""

    def generate(
        self,
        decision: DecisionRecord,
        document_sequence: int,
        intended_consumer_group_id: str,
    ) -> OperationalContract:
        """Generate a Command Decision Record as an OperationalContract."""
        if not decision.risk_recommendation_document_id.startswith("DOC-"):
            raise ValueError("CDR requires a Risk Office recommendation document reference")

        created = utc_timestamp()
        payload = {
            "approved": decision.approved,
            "decision_id": decision.decision_id,
            "decision_type": decision.decision_type,
            "evidence_reference_ids": _extract_prefixed_values(decision.rationale, "Evidence: "),
            "prompt_snapshot_id": _extract_prompt_snapshot(decision.rationale),
            "rationale": decision.rationale,
            "risk_recommendation_document_id": decision.risk_recommendation_document_id,
            "status": decision.status.value,
        }
        signature_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type="CDR",
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=decision.case_file_id,
            trade_cycle_id=decision.trade_cycle_id,
            parent_contract_ids=tuple(
                dict.fromkeys(
                    (decision.risk_recommendation_document_id, *payload["evidence_reference_ids"])
                )
            ),
            produced_by_staff_id=COMMANDER_STAFF_ID,
            produced_by_group_id=EXECUTIVE_GROUP_ID,
            intended_consumer_group_id=intended_consumer_group_id,
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary=f"Command Decision Record for {decision.decision_id}.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=tuple(
                dict.fromkeys(
                    (decision.risk_recommendation_document_id, *payload["evidence_reference_ids"])
                )
            ),
        )

    def to_registry_payload(self, decision: DecisionRecord) -> dict[str, object]:
        """Return a deterministic registry payload for persistence or audit."""
        data = asdict(decision)
        data["status"] = decision.status.value
        return data


def _extract_prompt_snapshot(rationale: str) -> str | None:
    marker = "Prompt snapshot: "
    if marker not in rationale:
        return None
    return rationale.split(marker, 1)[1].split(".", 1)[0].strip()


def _extract_prefixed_values(rationale: str, marker: str) -> tuple[str, ...]:
    if marker not in rationale:
        return ()
    value = rationale.split(marker, 1)[1].split(".", 1)[0]
    return tuple(item.strip() for item in value.split(",") if item.strip())
