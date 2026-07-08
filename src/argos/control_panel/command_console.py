"""Deterministic Commander Command Console for the ARGOS Control Panel."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Any


class CommandStatus(str, Enum):
    """Command lifecycle terminal states."""

    ISSUED = "ISSUED"
    VALIDATED = "VALIDATED"
    AUTHORIZED = "AUTHORIZED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


COMMAND_CATEGORIES = {
    "strategic",
    "operational",
    "administrative",
    "scheduling",
    "trading",
    "educational",
    "knowledge",
    "infrastructure",
    "investigation",
}

COMMAND_DEFINITIONS: dict[str, dict[str, Any]] = {
    "start_paper_self_training": {
        "category": "trading",
        "target": "Trader",
        "summary": "Initiate paper trading self-training",
        "requires_amount": False,
        "min_level": 3,
        "safe_when_live_disabled": True,
    },
    "halt_paper_self_training": {
        "category": "trading",
        "target": "Trader",
        "summary": "Halt paper trading self-training",
        "requires_amount": False,
        "min_level": 3,
        "safe_when_live_disabled": True,
    },
    "deposit_user_funds": {
        "category": "administrative",
        "target": "Executive",
        "summary": "Deposit user funds into active treasury",
        "requires_amount": True,
        "min_level": 5,
        "safe_when_live_disabled": True,
    },
    "halt_user_funds": {
        "category": "administrative",
        "target": "Executive",
        "summary": "Halt user funds into active treasury",
        "requires_amount": False,
        "min_level": 5,
        "safe_when_live_disabled": True,
    },
    "request_real_world_trading": {
        "category": "trading",
        "target": "Trader",
        "summary": "Initiate real-world trading from active treasury",
        "requires_amount": False,
        "min_level": 6,
        "safe_when_live_disabled": False,
    },
    "halt_real_world_trading": {
        "category": "trading",
        "target": "Trader",
        "summary": "Halt real-world trading",
        "requires_amount": False,
        "min_level": 6,
        "safe_when_live_disabled": True,
    },
    "pause_organization": {
        "category": "operational",
        "target": "Executive",
        "summary": "Pause an organization",
        "requires_amount": False,
        "min_level": 4,
        "safe_when_live_disabled": True,
    },
    "resume_organization": {
        "category": "operational",
        "target": "Executive",
        "summary": "Resume an organization",
        "requires_amount": False,
        "min_level": 4,
        "safe_when_live_disabled": True,
    },
    "change_operating_mode": {
        "category": "scheduling",
        "target": "Infrastructure",
        "summary": "Change organization operating mode",
        "requires_amount": False,
        "min_level": 4,
        "safe_when_live_disabled": True,
    },
    "configure_schedule": {
        "category": "scheduling",
        "target": "Infrastructure",
        "summary": "Configure organization schedule",
        "requires_amount": False,
        "min_level": 4,
        "safe_when_live_disabled": True,
    },
    "review_evidence": {
        "category": "investigation",
        "target": "Historian",
        "summary": "Review supporting evidence",
        "requires_amount": False,
        "min_level": 2,
        "safe_when_live_disabled": True,
    },
    "inspect_workflows": {
        "category": "investigation",
        "target": "Commander Interface",
        "summary": "Inspect organizational workflows",
        "requires_amount": False,
        "min_level": 2,
        "safe_when_live_disabled": True,
    },
    "view_historical_activity": {
        "category": "investigation",
        "target": "Historian",
        "summary": "Review historical activity",
        "requires_amount": False,
        "min_level": 2,
        "safe_when_live_disabled": True,
    },
    "export_reports": {
        "category": "knowledge",
        "target": "Librarian",
        "summary": "Export deterministic reports",
        "requires_amount": False,
        "min_level": 2,
        "safe_when_live_disabled": True,
    },
    "daily_briefing": {
        "category": "strategic",
        "target": "Executive",
        "summary": "Generate daily enterprise briefing",
        "requires_amount": False,
        "min_level": 2,
        "safe_when_live_disabled": True,
    },
}

MACROS: dict[str, tuple[str, ...]] = {
    "Morning Startup": ("resume_organization", "daily_briefing", "inspect_workflows"),
    "Market Open": ("start_paper_self_training", "review_evidence", "inspect_workflows"),
    "End of Day": ("halt_paper_self_training", "daily_briefing", "export_reports"),
    "Weekly Review": ("daily_briefing", "view_historical_activity", "export_reports"),
    "Historian Review": ("view_historical_activity", "review_evidence", "export_reports"),
    "Emergency Shutdown": ("halt_real_world_trading", "halt_paper_self_training", "halt_user_funds"),
}


@dataclass(frozen=True)
class CommandValidation:
    """Deterministic command validation result."""

    commander_authorization: str
    organizational_readiness: str
    dependency_satisfaction: str
    safety_constraints: str
    resource_availability: str
    accepted: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CommandRecord:
    """Append-only Commander command record."""

    command_id: str
    command_name: str
    category: str
    target: str
    detail: str
    amount_usd: float
    status: str
    timestamp_utc: str
    lifecycle: tuple[str, ...]
    validation: CommandValidation
    execution_status: str
    summary: str
    detailed_results: str
    supporting_evidence: tuple[str, ...]
    related_organizations: tuple[str, ...]
    historical_context: str
    recommended_next_actions: tuple[str, ...]
    audit_identifier: str
    correlation_identifier: str


class CommandConsole:
    """Authoritative deterministic human command interface."""

    def __init__(self) -> None:
        self._history: list[CommandRecord] = []
        self._issued_signatures: set[str] = set()
        self._unauthorized_commands = 0
        self._rejected_commands = 0
        self._failed_commands = 0

    def issue(
        self,
        *,
        command_name: str,
        category: str,
        target: str,
        detail: str,
        amount_usd: float,
        authority_level: int,
        context: dict[str, Any],
        timestamp_utc: str,
    ) -> CommandRecord:
        """Issue, validate, and authorize a command before runtime execution."""
        normalized = command_name.strip()
        definition = COMMAND_DEFINITIONS.get(normalized)
        selected_category = category.strip().lower() or str(definition["category"] if definition else "operational")
        selected_target = target.strip() or str(definition["target"] if definition else "Commander Interface")
        command_id = f"CC-{len(self._history) + 1:06d}"
        validation = self._validate(
            normalized,
            selected_category,
            selected_target,
            amount_usd,
            authority_level,
            context,
            definition,
        )
        status = CommandStatus.AUTHORIZED.value if validation.accepted else CommandStatus.REJECTED.value
        if not validation.accepted:
            self._rejected_commands += 1
            if validation.commander_authorization != "AUTHORIZED":
                self._unauthorized_commands += 1

        lifecycle = ("Command Issued", "Validation")
        lifecycle += ("Authorization",) if validation.accepted else ("Rejected", "Historical Archive", "Audit Record")
        record = CommandRecord(
            command_id=command_id,
            command_name=normalized,
            category=selected_category,
            target=selected_target,
            detail=detail,
            amount_usd=round(float(amount_usd), 2),
            status=status,
            timestamp_utc=timestamp_utc,
            lifecycle=lifecycle,
            validation=validation,
            execution_status="PENDING" if validation.accepted else "NOT_EXECUTED",
            summary=str(definition["summary"] if definition else "Unsupported Commander command"),
            detailed_results="Command authorized for deterministic routing." if validation.accepted else "; ".join(validation.reasons),
            supporting_evidence=(command_id,),
            related_organizations=(selected_target,),
            historical_context=f"Command {normalized} issued from ARGOS Control Panel.",
            recommended_next_actions=_next_actions(normalized, validation),
            audit_identifier="PENDING_AUDIT" if validation.accepted else "REJECTED_BEFORE_EXECUTION",
            correlation_identifier=command_id,
        )
        self._history.append(record)
        self._issued_signatures.add(f"{normalized}:{selected_target}:{detail}:{amount_usd}")
        return record

    def complete(
        self,
        command_id: str,
        *,
        execution_status: str,
        detailed_results: str,
        supporting_evidence: tuple[str, ...],
        audit_identifier: str,
    ) -> CommandRecord:
        """Complete and archive a command after deterministic runtime execution."""
        index = self._index(command_id)
        record = self._history[index]
        status = CommandStatus.COMPLETED.value if execution_status.upper() == "SUCCESS" else CommandStatus.FAILED.value
        if status == CommandStatus.FAILED.value:
            self._failed_commands += 1
        completed = replace(
            record,
            status=status,
            lifecycle=(
                "Command Issued",
                "Validation",
                "Authorization",
                "Execution",
                "Result",
                "Historical Archive",
                "Audit Record",
            ),
            execution_status=execution_status.upper(),
            detailed_results=detailed_results,
            supporting_evidence=supporting_evidence or record.supporting_evidence,
            audit_identifier=audit_identifier,
        )
        self._history[index] = completed
        return completed

    def macro_commands(self, macro_name: str) -> tuple[str, ...]:
        """Return deterministic command expansion for a Commander macro."""
        if macro_name not in MACROS:
            raise ValueError(f"unsupported Commander macro: {macro_name}")
        return MACROS[macro_name]

    def snapshot(self, filters: dict[str, str] | None = None) -> dict[str, Any]:
        """Return command console state for dashboard display."""
        records = self.search(filters or {})
        accepted = sum(1 for record in self._history if record.validation.accepted)
        completed = sum(1 for record in self._history if record.status == CommandStatus.COMPLETED.value)
        return {
            "commands": tuple(_record_dict(record) for record in reversed(records[-40:])),
            "lastResponse": _record_dict(self._history[-1]) if self._history else {},
            "definitions": COMMAND_DEFINITIONS,
            "macros": MACROS,
            "metrics": {
                "commandHistoryDepth": len(self._history),
                "authorizedCommands": accepted,
                "completedCommands": completed,
                "rejectedCommands": self._rejected_commands,
                "unauthorizedCommands": self._unauthorized_commands,
                "failedCommands": self._failed_commands,
                "macroCount": len(MACROS),
            },
            "detections": {
                "unauthorizedCommands": self._unauthorized_commands,
                "discardedCommands": 0,
                "untracedCommands": sum(1 for record in self._history if not record.audit_identifier),
                "duplicateCommandSignatures": max(0, len(self._history) - len(self._issued_signatures)),
            },
        }

    def search(self, filters: dict[str, str]) -> tuple[CommandRecord, ...]:
        """Search command history by deterministic Commander filters."""
        normalized = {key: str(value).strip() for key, value in filters.items() if str(value).strip()}
        return tuple(record for record in self._history if _matches(record, normalized))

    def _validate(
        self,
        command_name: str,
        category: str,
        target: str,
        amount_usd: float,
        authority_level: int,
        context: dict[str, Any],
        definition: dict[str, Any] | None,
    ) -> CommandValidation:
        reasons: list[str] = []
        if definition is None:
            reasons.append("Unsupported command definition.")
        if category not in COMMAND_CATEGORIES:
            reasons.append("Unsupported command category.")
        if target not in set(context.get("organizations", ())) | {"Commander Interface", "Infrastructure"}:
            reasons.append("Target organization is not registered.")

        min_level = int(definition.get("min_level", 99)) if definition else 99
        commander_authorization = "AUTHORIZED" if authority_level >= min_level else "DENIED"
        if commander_authorization != "AUTHORIZED":
            reasons.append(f"Commander authority level {authority_level} is below required level {min_level}.")

        organizational_readiness = "READY" if context.get("system_status") == "NOMINAL" else "NOT_READY"
        if organizational_readiness != "READY":
            reasons.append("Enterprise status is not nominal.")

        dependency_satisfaction = "SATISFIED"
        if definition and definition.get("requires_amount") and amount_usd <= 0:
            dependency_satisfaction = "MISSING_AMOUNT"
            reasons.append("Command requires a positive USD amount.")
        if command_name == "deposit_user_funds" and context.get("user_funds_halted"):
            dependency_satisfaction = "FUNDS_HALTED"
            reasons.append("User fund deposits are halted.")

        safety_constraints = "PASSED"
        if definition and not definition.get("safe_when_live_disabled", True) and not context.get("live_trading_enabled"):
            safety_constraints = "BLOCKED_BY_CONFIGURATION"
            reasons.append("Live trading is blocked by deterministic configuration.")
        if command_name == "request_real_world_trading" and not context.get("risk_certified"):
            safety_constraints = "RISK_CERTIFICATION_REQUIRED"
            reasons.append("Risk certification gate is not satisfied.")

        resource_availability = "AVAILABLE"
        if context.get("budget_status") == "RED" and command_name == "start_paper_self_training":
            resource_availability = "BUDGET_BLOCKED"
            reasons.append("API credit budget is red.")

        return CommandValidation(
            commander_authorization=commander_authorization,
            organizational_readiness=organizational_readiness,
            dependency_satisfaction=dependency_satisfaction,
            safety_constraints=safety_constraints,
            resource_availability=resource_availability,
            accepted=not reasons,
            reasons=tuple(reasons),
        )

    def _index(self, command_id: str) -> int:
        for index, record in enumerate(self._history):
            if record.command_id == command_id:
                return index
        raise ValueError(f"unknown command id: {command_id}")


def _record_dict(record: CommandRecord) -> dict[str, Any]:
    data = asdict(record)
    data["validation"] = asdict(record.validation)
    return data


def _matches(record: CommandRecord, filters: dict[str, str]) -> bool:
    fields = {
        "command": record.command_name,
        "command_name": record.command_name,
        "category": record.category,
        "target": record.target,
        "status": record.status,
        "time": record.timestamp_utc,
    }
    for key, value in filters.items():
        if key == "q":
            haystack = " ".join((record.command_name, record.summary, record.detailed_results, record.detail)).lower()
            if value.lower() not in haystack:
                return False
            continue
        if key == "time":
            if value not in record.timestamp_utc:
                return False
            continue
        if fields.get(key, "").lower() != value.lower():
            return False
    return True


def _next_actions(command_name: str, validation: CommandValidation) -> tuple[str, ...]:
    if not validation.accepted:
        return ("Resolve validation findings.", "Reissue command after prerequisites are satisfied.")
    if command_name == "request_real_world_trading":
        return ("Verify broker controls.", "Confirm Risk Office certification.", "Require explicit live-trading approval.")
    if command_name.startswith("halt"):
        return ("Review resulting enterprise state.", "Confirm audit trail completeness.")
    return ("Monitor execution status.", "Review supporting evidence and related activity.")
