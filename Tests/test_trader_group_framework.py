from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.executive.override import HumanAuthority, HumanOverrideService, OverrideAction, OverrideLevel  # noqa: E402
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.contracts import OperationalContract, utc_timestamp  # noqa: E402
from argos.foundation.identity import generate_document_id  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.trader import ExecutionState, TRADER_GROUP_ID, TraderFrameworkLibrary, TraderGroup, trader_office_templates  # noqa: E402


def config() -> ConfigurationService:
    return ConfigurationService.load(
        {
            "environment": "development",
            "config_version": "1.0.0",
            "schema_version": "1.0.0",
            "log_level": "INFO",
            "live_trading_enabled": False,
            "feature_flags": {},
            "secret_references": [],
        },
        {},
    )


def contract(
    sequence: int,
    contract_type: str,
    producer_group: str,
    consumer_group: str,
    payload: dict[str, object],
) -> OperationalContract:
    created = utc_timestamp()
    signature_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=list).encode("utf-8")
    ).hexdigest()
    return OperationalContract(
        contract_id=generate_document_id(sequence),
        contract_type=contract_type,
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=tuple(payload.get("parent_contract_ids", ())),
        produced_by_staff_id="STF-002" if producer_group == "DEP-002" else "STF-050",
        produced_by_group_id=producer_group,
        intended_consumer_group_id=consumer_group,
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary=f"{contract_type} fixture.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=tuple(payload.get("source_reference_ids", ())),
    )


def approved_cdr() -> OperationalContract:
    return contract(
        5201,
        "CDR",
        "DEP-002",
        TRADER_GROUP_ID,
        {
            "approved": True,
            "decision_id": "CDR-DECISION-052",
            "decision_type": "Approve",
            "risk_recommendation_document_id": "DOC-3702",
            "status": "cdr_generated",
        },
    )


def risk_certification(certified: bool = True) -> OperationalContract:
    return contract(
        5202,
        "RAR",
        "DEP-005",
        TRADER_GROUP_ID,
        {
            "risk_office_certification_status": "certified" if certified else "not_certified",
            "source_organizational_risk_assessment_id": "DOC-3701",
            "trader_group_prerequisite": "certified_organizational_risk_assessment",
            "source_reference_ids": ("DOC-3701",),
            "parent_contract_ids": ("DOC-3701",),
        },
    )


class TraderGroupFrameworkTests(unittest.TestCase):
    def test_trader_group_registers_subordinate_offices(self) -> None:
        templates = trader_office_templates()

        self.assertEqual(len(templates), 7)
        self.assertEqual(templates[0].name, "Trade Execution Office")
        self.assertEqual(templates[-1].name, "Trader Fusion Office")

    def test_execution_workflow_generates_traceable_artifacts(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        trader = TraderGroup(config(), persistence, audit, PromptRepository())

        artifacts = trader.prepare_execution(approved_cdr(), risk_certification(), 5210)

        self.assertIn("execution_readiness_report", artifacts)
        self.assertIn("execution_case_file", artifacts)
        self.assertIn("execution_state_record", artifacts)
        self.assertIn("execution_audit_log", artifacts)
        self.assertIn("trader_group_system_prompt", artifacts)
        self.assertTrue(artifacts["execution_readiness_report"].machine_payload["ready"])
        self.assertTrue(artifacts["execution_case_file"].machine_payload["historian_interface_ready"])
        self.assertIn("order_lifecycle", artifacts["execution_case_file"].machine_payload)
        self.assertIn("deterministic_execution_pipeline", artifacts["trader_workflow_definition"].machine_payload)
        self.assertIn("audit_architecture", artifacts["execution_audit_log"].machine_payload)
        self.assertIn("You are the Trader Group of ARGOS", artifacts["trader_group_system_prompt"].machine_payload["prompt_text"])
        self.assertEqual(trader.state_manager.records[-1].current_state, ExecutionState.HISTORIAN_RECORD_READY)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, artifacts["execution_case_file"].contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))
        self.assertIn(AuditEventType.STAFF_DECISION, tuple(event.event_type for event in audit.audit_log.events))

    def test_framework_library_documents_architecture_pipeline_metrics_and_audit(self) -> None:
        library = TraderFrameworkLibrary()

        self.assertIn("Trade Execution Office", library.architecture().offices)
        self.assertIn("introduce_no_discretionary_investment_decisions", library.philosophy().principles)
        self.assertIn("order_lifecycle_preparation", library.pipeline().stages)
        self.assertIn("historian_recorded", library.order_lifecycle().terminal_states)
        self.assertIn("audit_event_count", library.metrics().metrics)
        self.assertIn("document_created", library.audit_architecture().required_events)
        self.assertEqual(library.system_prompt().version, "1.0.0")

    def test_subordinate_queues_and_historian_interface_are_operational(self) -> None:
        trader = TraderGroup(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = trader.prepare_execution(approved_cdr(), risk_certification(), 5230)
        historian_inbox = IncomingMailbox("STF-070", "DEP-007")
        result = trader.route_to_historian(artifacts["execution_case_file"], historian_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(historian_inbox.get(artifacts["execution_case_file"].contract_id), artifacts["execution_case_file"])
        self.assertTrue(all(len(office.queue) == 1 for office in trader.offices.values()))

    def test_failed_authorization_generates_exception_report(self) -> None:
        cdr = contract(
            5240,
            "CDR",
            "DEP-002",
            TRADER_GROUP_ID,
            {"approved": False, "decision_id": "CDR-DECISION-REJECTED", "risk_recommendation_document_id": "DOC-3702"},
        )
        trader = TraderGroup(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        artifacts = trader.prepare_execution(cdr, risk_certification(), 5241)

        self.assertEqual(tuple(artifacts), ("execution_exception_report",))
        self.assertIn("approved Executive authorization", artifacts["execution_exception_report"].machine_payload["reason"])
        self.assertEqual(trader.state_manager.records[-1].current_state, ExecutionState.EXCEPTION)

    def test_risk_certification_and_human_override_are_enforced(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        override = HumanOverrideService(AuditService(), persistence)
        override.apply_override(
            OverrideAction.TRADING_PAUSE,
            HumanAuthority("AUTH-052", "STF-002", OverrideLevel.LEVEL_2_TRADING_PAUSE),
            "EO-052 governance test",
        )
        trader = TraderGroup(config(), persistence, AuditService(), PromptRepository(), override)

        paused = trader.prepare_execution(approved_cdr(), risk_certification(), 5250)
        uncertified = TraderGroup(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository()).prepare_execution(
            approved_cdr(),
            risk_certification(certified=False),
            5260,
        )

        self.assertIn("blocked by human override", paused["execution_exception_report"].machine_payload["reason"])
        self.assertIn("not certified", uncertified["execution_exception_report"].machine_payload["reason"])


if __name__ == "__main__":
    unittest.main()
