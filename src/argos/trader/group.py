"""Trader Group deterministic execution organization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.executive.override import HumanOverrideService
from argos.foundation.audit import AuditService
from argos.foundation.communication import CourierService, IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository

from .offices import (
    TRADER_GROUP_ID,
    TraderOffice,
    TraderOfficeRegistry,
    trader_office_templates,
)


TRADER_COMMAND_OFFICE_ID = "TRADER-OFFICE-001"


class ExecutionState(str, Enum):
    """Deterministic Trader workflow states."""

    RECEIVED = "received"
    AUTHORIZATION_VERIFIED = "authorization_verified"
    RISK_CERTIFIED = "risk_certified"
    PLAN_CONSTRUCTED = "plan_constructed"
    READY_FOR_SUBORDINATE_OFFICES = "ready_for_subordinate_offices"
    HISTORIAN_RECORD_READY = "historian_record_ready"
    EXCEPTION = "exception"


@dataclass(frozen=True)
class TraderGroupArchitecture:
    """Trader Group organizational architecture."""

    architecture_id: str
    offices: tuple[str, ...]
    upstream_interfaces: tuple[str, ...]
    downstream_interfaces: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionPhilosophy:
    """Trader Group execution philosophy."""

    philosophy_id: str
    principles: tuple[str, ...]


@dataclass(frozen=True)
class DeterministicExecutionPipeline:
    """Deterministic execution pipeline."""

    pipeline_id: str
    stages: tuple[str, ...]


@dataclass(frozen=True)
class OrderLifecycleFramework:
    """Order lifecycle framework for later Trader Offices."""

    lifecycle_id: str
    states: tuple[str, ...]
    terminal_states: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionMetricsFramework:
    """Execution metrics framework."""

    framework_id: str
    metrics: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionAuditArchitecture:
    """Execution audit architecture."""

    architecture_id: str
    required_events: tuple[str, ...]
    traceability_keys: tuple[str, ...]


@dataclass(frozen=True)
class TraderGroupSystemPrompt:
    """Trader Group system prompt artifact."""

    prompt_id: str
    version: str
    prompt_text: str


@dataclass(frozen=True)
class AuthorizationVerificationRecord:
    """Executive authorization verification result."""

    record_id: str
    cdr_id: str
    approved: bool
    risk_reference_id: str
    authority_boundary: str


@dataclass(frozen=True)
class RiskCertificationVerificationRecord:
    """Risk certification verification result."""

    record_id: str
    certification_document_id: str
    source_organizational_risk_assessment_id: str
    certified: bool


@dataclass(frozen=True)
class TraderWorkflowDefinition:
    """Deterministic workflow definition for Trader execution preparation."""

    workflow_id: str
    steps: tuple[str, ...]


@dataclass(frozen=True)
class TraderGovernanceRecord:
    """Trader governance boundary record."""

    record_id: str
    live_trading_authorized: bool
    discretionary_decisions_allowed: bool
    required_authority_documents: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionStateRecord:
    """Append-only execution state record."""

    state_id: str
    case_file_id: str
    trade_cycle_id: str
    current_state: ExecutionState
    completed_steps: tuple[str, ...]
    cdr_id: str
    risk_certification_id: str

    def to_payload(self) -> dict[str, object]:
        return {
            "state_id": self.state_id,
            "case_file_id": self.case_file_id,
            "trade_cycle_id": self.trade_cycle_id,
            "current_state": self.current_state.value,
            "completed_steps": self.completed_steps,
            "cdr_id": self.cdr_id,
            "risk_certification_id": self.risk_certification_id,
        }


@dataclass(frozen=True)
class ExecutionReadinessReport:
    """Execution readiness report payload."""

    report_id: str
    authorization_verified: bool
    risk_certification_verified: bool
    governance_verified: bool
    ready: bool


@dataclass(frozen=True)
class ExecutionExceptionReport:
    """Deterministic Trader exception report."""

    exception_id: str
    reason: str
    source_document_ids: tuple[str, ...]


class ExecutiveAuthorizationValidator:
    """Validate Executive authorizations for Trader consumption."""

    def validate(self, cdr: OperationalContract) -> AuthorizationVerificationRecord:
        if cdr.contract_type != "CDR":
            raise ValueError("Trader Group requires a Command Decision Record")
        if cdr.intended_consumer_group_id != TRADER_GROUP_ID:
            raise ValueError("CDR is not addressed to Trader Group")
        if cdr.machine_payload.get("approved") is not True:
            raise ValueError("Trader Group requires an approved Executive authorization")
        risk_reference = str(cdr.machine_payload.get("risk_recommendation_document_id", ""))
        if not risk_reference.startswith("DOC-"):
            raise ValueError("CDR must reference a Risk Office document")
        return AuthorizationVerificationRecord(
            "AVR-001",
            cdr.contract_id,
            True,
            risk_reference,
            "execute_organizational_intent_without_discretion",
        )


class RiskCertificationValidator:
    """Validate certified Risk Office prerequisite records."""

    def validate(self, risk_certification: OperationalContract) -> RiskCertificationVerificationRecord:
        payload = risk_certification.machine_payload
        if risk_certification.contract_type != "RAR":
            raise ValueError("Risk certification must be a Risk Assessment Report contract")
        if risk_certification.intended_consumer_group_id != TRADER_GROUP_ID:
            raise ValueError("Risk certification is not addressed to Trader Group")
        if payload.get("risk_office_certification_status") != "certified":
            raise ValueError("Risk Office certification is not certified")
        source_id = str(payload.get("source_organizational_risk_assessment_id", ""))
        if not source_id.startswith("DOC-"):
            raise ValueError("Risk certification must reference an Organizational Risk Assessment")
        return RiskCertificationVerificationRecord("RCVR-001", risk_certification.contract_id, source_id, True)


class ExecutionPlanBuilder:
    """Construct deterministic execution plans without discretionary trading logic."""

    def build(
        self,
        authorization: AuthorizationVerificationRecord,
        risk_certification: RiskCertificationVerificationRecord,
    ) -> TraderWorkflowDefinition:
        return TraderWorkflowDefinition(
            "TWD-001",
            (
                "receive_executive_authorization",
                "verify_risk_certification",
                "validate_governance_boundaries",
                "construct_execution_case_file",
                "queue_subordinate_trader_offices",
                "emit_historian_interface_record",
            ),
        )


class TraderFrameworkLibrary:
    """Return deterministic Trader Group framework artifacts."""

    def architecture(self) -> TraderGroupArchitecture:
        return TraderGroupArchitecture(
            "TGA-052",
            tuple(template.name for template in trader_office_templates()),
            ("Executive Group", "Risk Office", "Human Override Framework"),
            ("Historian Group",),
        )

    def philosophy(self) -> ExecutionPhilosophy:
        return ExecutionPhilosophy(
            "TEP-052",
            (
                "faithfully_execute_approved_organizational_intent",
                "introduce_no_discretionary_investment_decisions",
                "preserve_complete_auditability",
                "respect_risk_constraints_and_human_overrides",
            ),
        )

    def pipeline(self) -> DeterministicExecutionPipeline:
        return DeterministicExecutionPipeline(
            "DEP-052",
            (
                "executive_authorization_receipt",
                "risk_certification_verification",
                "governance_validation",
                "execution_plan_construction",
                "order_lifecycle_preparation",
                "subordinate_office_coordination",
                "historian_recording",
            ),
        )

    def order_lifecycle(self) -> OrderLifecycleFramework:
        return OrderLifecycleFramework(
            "OLF-052",
            (
                "authorized",
                "risk_certified",
                "planned",
                "staged",
                "submitted",
                "acknowledged",
                "partially_filled",
                "filled",
                "confirmed",
                "historian_recorded",
                "exception",
            ),
            ("confirmed", "historian_recorded", "exception"),
        )

    def metrics(self) -> ExecutionMetricsFramework:
        return ExecutionMetricsFramework(
            "EMF-052",
            (
                "authorization_validation_latency",
                "risk_certification_pass_rate",
                "execution_plan_generation_count",
                "order_lifecycle_exception_count",
                "historian_record_delivery_count",
                "audit_event_count",
            ),
        )

    def audit_architecture(self) -> ExecutionAuditArchitecture:
        return ExecutionAuditArchitecture(
            "EAA-052",
            (
                "document_created",
                "validation_result",
                "staff_decision",
                "mailbox_deposited",
                "courier_transfer",
                "document_received",
            ),
            ("case_file_id", "trade_cycle_id", "cdr_id", "risk_certification_id", "execution_case_file_id"),
        )

    def system_prompt(self) -> TraderGroupSystemPrompt:
        return TraderGroupSystemPrompt(
            "PROMPT-TRADER-GROUP-052",
            "1.0.0",
            (
                "You are the Trader Group of ARGOS. Execute approved investment decisions with deterministic "
                "precision, complete auditability, and rigorous adherence to organizational risk constraints. "
                "Manage the complete order lifecycle from executive approval through execution, position "
                "confirmation, and historical recording. Maintain comprehensive execution logs, monitor "
                "execution quality, coordinate with brokers through authorized interfaces only, and ensure every "
                "trade faithfully implements approved organizational intent while preserving complete traceability "
                "for future historical evaluation."
            ),
        )


class ExecutionStateManager:
    """Maintain deterministic execution state."""

    def __init__(self) -> None:
        self._records: list[ExecutionStateRecord] = []

    @property
    def records(self) -> tuple[ExecutionStateRecord, ...]:
        return tuple(self._records)

    def append(
        self,
        case_file_id: str,
        trade_cycle_id: str,
        state: ExecutionState,
        completed_steps: tuple[str, ...],
        cdr_id: str,
        risk_certification_id: str,
    ) -> ExecutionStateRecord:
        record = ExecutionStateRecord(
            f"ESR-{len(self._records) + 1:06d}",
            case_file_id,
            trade_cycle_id,
            state,
            completed_steps,
            cdr_id,
            risk_certification_id,
        )
        self._records.append(record)
        return record


class TraderGroup:
    """Deterministic execution organization for ARGOS."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
        override_service: HumanOverrideService | None = None,
    ) -> None:
        self.configuration_service = configuration_service
        self.persistence_repository = persistence_repository
        self.audit_service = audit_service
        self.prompt_repository = prompt_repository
        self.override_service = override_service
        self.registry = TraderOfficeRegistry()
        self.offices: dict[str, TraderOffice] = {}
        for template in trader_office_templates():
            record = self.registry.register(template)
            self.offices[template.office_id] = TraderOffice(record)
        self.authorization_validator = ExecutiveAuthorizationValidator()
        self.risk_validator = RiskCertificationValidator()
        self.plan_builder = ExecutionPlanBuilder()
        self.framework_library = TraderFrameworkLibrary()
        self.state_manager = ExecutionStateManager()

    def prepare_execution(
        self,
        cdr: OperationalContract,
        risk_certification: OperationalContract,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        """Validate prerequisites and produce deterministic Trader artifacts."""
        try:
            self.configuration_service.validate_startup()
            self._assert_governance_allows_preparation()
            authorization = self.authorization_validator.validate(cdr)
            risk_record = self.risk_validator.validate(risk_certification)
            workflow = self.plan_builder.build(authorization, risk_record)
            governance = self._governance_record(cdr, risk_certification)
            framework = self.framework_library
            readiness = ExecutionReadinessReport("ERR-052", True, True, True, True)
            state = self.state_manager.append(
                cdr.case_file_id,
                cdr.trade_cycle_id,
                ExecutionState.HISTORIAN_RECORD_READY,
                workflow.steps,
                cdr.contract_id,
                risk_certification.contract_id,
            )
            contracts = self._contracts(
                cdr,
                risk_certification,
                authorization,
                risk_record,
                workflow,
                governance,
                framework,
                readiness,
                state,
                document_sequence,
            )
            for contract in contracts.values():
                self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id, contract.to_dict())
                self.audit_service.record_document_creation(contract)
            self.audit_service.record_staff_decision(
                contracts["authorization_verification_record"],
                staff_id=self._command_office().record.configuration.staff_id,
                group_id=TRADER_GROUP_ID,
                decision="execution_prerequisites_verified",
                rationale="Executive authorization and Risk certification verified deterministically.",
            )
            self._queue_subordinate_offices(contracts["execution_case_file"].contract_id)
            self._command_office().generated_records += len(contracts)
            return contracts
        except Exception as exc:
            exception_contract = self._exception_contract(cdr, risk_certification, str(exc), document_sequence)
            self.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, exception_contract.contract_id, exception_contract.to_dict())
            self.audit_service.record_document_creation(exception_contract)
            self.state_manager.append(
                cdr.case_file_id,
                cdr.trade_cycle_id,
                ExecutionState.EXCEPTION,
                ("receive_executive_authorization", "exception_recorded"),
                cdr.contract_id,
                risk_certification.contract_id,
            )
            return {"execution_exception_report": exception_contract}

    def route_to_historian(self, execution_case_file: OperationalContract, historian_inbox: IncomingMailbox):
        """Route an Execution Case File to the Historian Group through Courier."""
        return CourierService(self.audit_service).deliver(self._command_office().record.outbox, historian_inbox, execution_case_file)

    def instrument_panels(self):
        """Return instrument panels for every Trader office."""
        return tuple(self.offices[key].instrument_panel() for key in sorted(self.offices))

    def _assert_governance_allows_preparation(self) -> None:
        if self.override_service is not None:
            if self.override_service.trading_paused or self.override_service.organization_locked or self.override_service.read_only_mode:
                raise PermissionError("Trader Group blocked by human override")
        if self.configuration_service.configuration.live_trading_enabled is True:
            raise PermissionError("EO-052 does not grant live trading authority")

    def _governance_record(self, cdr: OperationalContract, risk_certification: OperationalContract) -> TraderGovernanceRecord:
        return TraderGovernanceRecord(
            "TGR-052",
            False,
            False,
            (cdr.contract_id, risk_certification.contract_id),
        )

    def _contracts(
        self,
        cdr: OperationalContract,
        risk_certification: OperationalContract,
        authorization: AuthorizationVerificationRecord,
        risk_record: RiskCertificationVerificationRecord,
        workflow: TraderWorkflowDefinition,
        governance: TraderGovernanceRecord,
        framework: TraderFrameworkLibrary,
        readiness: ExecutionReadinessReport,
        state: ExecutionStateRecord,
        document_sequence: int,
    ) -> dict[str, OperationalContract]:
        base_payload = {
            "case_file_id": cdr.case_file_id,
            "trade_cycle_id": cdr.trade_cycle_id,
            "cdr_id": cdr.contract_id,
            "risk_certification_id": risk_certification.contract_id,
            "source_organizational_risk_assessment_id": risk_record.source_organizational_risk_assessment_id,
            "live_trading_instruction": None,
            "broker_instruction": None,
            "discretionary_decision": None,
        }
        payloads = {
            "authorization_verification_record": {**base_payload, **authorization.__dict__},
            "execution_readiness_report": {**base_payload, **readiness.__dict__},
            "execution_status_report": {**base_payload, "status_report_id": "ESRPT-052", "state": state.current_state.value},
            "trader_group_summary": {**base_payload, "summary_id": "TGS-052", "office_count": len(self.offices), "state": state.current_state.value},
            "execution_case_file": {
                **base_payload,
                "execution_case_file_id": "ECF-052",
                "workflow_id": workflow.workflow_id,
                "workflow_steps": workflow.steps,
                "order_lifecycle": framework.order_lifecycle().__dict__,
                "historian_interface_ready": True,
            },
            "execution_state_record": {**base_payload, **state.to_payload()},
            "trader_workflow_definition": {
                **base_payload,
                **workflow.__dict__,
                "trader_group_architecture": framework.architecture().__dict__,
                "execution_philosophy": framework.philosophy().__dict__,
                "deterministic_execution_pipeline": framework.pipeline().__dict__,
                "execution_metrics_framework": framework.metrics().__dict__,
            },
            "trader_governance_record": {**base_payload, **governance.__dict__},
            "execution_audit_log": {
                **base_payload,
                "audit_log_id": "EAL-052",
                "audit_architecture": framework.audit_architecture().__dict__,
                "expected_audit_events": framework.audit_architecture().required_events,
            },
            "trader_group_system_prompt": {
                **base_payload,
                **framework.system_prompt().__dict__,
            },
        }
        contracts: dict[str, OperationalContract] = {}
        for offset, (name, payload) in enumerate(payloads.items()):
            contracts[name] = _contract(
                document_sequence + offset,
                "EXECUTION_RECORD",
                cdr.case_file_id,
                cdr.trade_cycle_id,
                (cdr.contract_id, risk_certification.contract_id),
                self._command_office().record.configuration.staff_id,
                TRADER_GROUP_ID,
                "DEP-007" if name == "execution_case_file" else TRADER_GROUP_ID,
                f"Trader {name.replace('_', ' ')}.",
                payload,
            )
        return contracts

    def _exception_contract(
        self,
        cdr: OperationalContract,
        risk_certification: OperationalContract,
        reason: str,
        document_sequence: int,
    ) -> OperationalContract:
        report = ExecutionExceptionReport("EXC-052", reason, (cdr.contract_id, risk_certification.contract_id))
        return _contract(
            document_sequence,
            "EXECUTION_EXCEPTION",
            cdr.case_file_id,
            cdr.trade_cycle_id,
            (cdr.contract_id, risk_certification.contract_id),
            self._command_office().record.configuration.staff_id,
            TRADER_GROUP_ID,
            TRADER_GROUP_ID,
            "Trader execution exception report.",
            report.__dict__,
        )

    def _queue_subordinate_offices(self, execution_case_file_id: str) -> None:
        for office_id in sorted(self.offices):
            self.offices[office_id].queue.enqueue(execution_case_file_id)

    def _command_office(self) -> TraderOffice:
        return self.offices[TRADER_COMMAND_OFFICE_ID]


def _contract(
    document_sequence: int,
    contract_type: str,
    case_file_id: str,
    trade_cycle_id: str,
    parent_contract_ids: tuple[str, ...],
    staff_id: str,
    group_id: str,
    consumer_group_id: str,
    human_summary: str,
    payload: dict[str, Any],
) -> OperationalContract:
    created = utc_timestamp()
    signature_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=list).encode("utf-8")
    ).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(document_sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id=case_file_id,
        trade_cycle_id=trade_cycle_id,
        parent_contract_ids=parent_contract_ids,
        produced_by_staff_id=staff_id,
        produced_by_group_id=group_id,
        intended_consumer_group_id=consumer_group_id,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=human_summary,
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=parent_contract_ids,
    )
