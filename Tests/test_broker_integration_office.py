from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402
from argos.foundation.contracts import utc_timestamp  # noqa: E402
from argos.trader import (  # noqa: E402
    BrokerAdapterRegistry,
    BrokerAuthenticationContext,
    BrokerCapabilityProfile,
    BrokerConnectionStatus,
    BrokerExecutionRequest,
    BrokerHealthStatus,
    BrokerIntegrationOffice,
    BrokerResponseType,
    BrokerSpecificRequest,
    DeterministicPaperBrokerAdapter,
    ExecutionOrderRequest,
    OrderManagementOffice,
    RawBrokerResponse,
)


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


def omo_request() -> ExecutionOrderRequest:
    return ExecutionOrderRequest(
        "EXP-055",
        "AAPL",
        100.0,
        "buy",
        "limit",
        "NASDAQ",
        "ACCT-PAPER-001",
        "STRAT-055",
        "DOC-5201",
        "DOC-3702",
        "POS-055",
        1,
        "BROKER-PAPER",
        "NASDAQ",
        ("do_not_modify_strategy",),
    )


def broker_request(correlation_id: str = "CORR-055") -> BrokerExecutionRequest:
    return BrokerExecutionRequest(
        "ERQ-055",
        "ORD-000001",
        "BROKER-PAPER",
        "STRAT-055",
        utc_timestamp(),
        correlation_id,
        BrokerAuthenticationContext("AUTHCTX-055", "ENV:BROKER_TOKEN", True),
        {"quantity": 100.0, "price": 100.25, "position_id": "POS-055", "order_type": "limit"},
    )


class UnhealthyAdapter:
    broker_id = "BROKER-BAD"

    def capability_profile(self) -> BrokerCapabilityProfile:
        return BrokerCapabilityProfile(self.broker_id, ("limit",), ("equity",), True, "0.9.0", 0)

    def health_status(self) -> BrokerHealthStatus:
        return BrokerHealthStatus(self.broker_id, BrokerConnectionStatus.DISCONNECTED, "expired", False, 1500, 1500, False, 0, False, False)

    def submit_order(self, request: BrokerSpecificRequest) -> RawBrokerResponse:
        raise AssertionError("unhealthy adapter should not receive submissions")


class BrokerIntegrationOfficeTests(unittest.TestCase):
    def test_broker_submission_normalizes_event_and_syncs_omo(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        omo = OrderManagementOffice(config(), persistence, audit, PromptRepository())
        omo.create_order(omo_request(), "CF-001", "TC-001", 1, 5501)
        bio = BrokerIntegrationOffice(config(), persistence, audit, PromptRepository())

        result = bio.submit_execution_request(broker_request(), omo, "CF-001", "TC-001", 5502)

        event = result["canonical_broker_event"]
        self.assertEqual(event.contract_type, "BROKER_EVENT")
        self.assertFalse(event.machine_payload["broker_specific_formats_exposed"])
        self.assertFalse(event.machine_payload["executive_intent_modified"])
        self.assertEqual(event.machine_payload["canonical_broker_event"]["argos_order_id"], "ORD-000001")
        self.assertEqual(bio.mapping_registry.get("ORD-000001").broker_order_id, "BRK-ORD-000001")
        self.assertEqual(len(bio.message_history), 4)
        self.assertTrue(omo.managed_order("ORD-000001").broker_messages)
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, event.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(item.event_type for item in audit.audit_log.events))

    def test_duplicate_submission_generates_case_file(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        omo = OrderManagementOffice(config(), persistence, audit, PromptRepository())
        omo.create_order(omo_request(), "CF-001", "TC-001", 1, 5510)
        bio = BrokerIntegrationOffice(config(), persistence, audit, PromptRepository())

        bio.submit_execution_request(broker_request("CORR-DUP"), omo, "CF-001", "TC-001", 5511)
        duplicate = bio.submit_execution_request(broker_request("CORR-DUP"), omo, "CF-001", "TC-001", 5512)

        self.assertEqual(duplicate["broker_integration_case_file"].contract_type, "BROKER_CASE_FILE")
        classifications = tuple(item["classification"] for item in duplicate["broker_integration_case_file"].machine_payload["case_file"]["anomalies"])
        self.assertIn("duplicate_submission", classifications)

    def test_health_failures_generate_case_file_without_submission(self) -> None:
        registry = BrokerAdapterRegistry()
        registry.register(UnhealthyAdapter())
        bio = BrokerIntegrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository(), registry)
        omo = OrderManagementOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        bad_request = BrokerExecutionRequest("ERQ-BAD", "ORD-000001", "BROKER-BAD", "STRAT-055", utc_timestamp(), "CORR-BAD", BrokerAuthenticationContext("AUTHCTX-BAD", "ENV:BAD", False), {"quantity": 1.0, "price": 1.0, "position_id": "POS-055"})

        result = bio.submit_execution_request(bad_request, omo, "CF-001", "TC-001", 5520)

        case_file = result["broker_integration_case_file"]
        self.assertEqual(case_file.contract_type, "BROKER_CASE_FILE")
        classifications = tuple(item["classification"] for item in case_file.machine_payload["case_file"]["anomalies"])
        self.assertIn("connection_failure", classifications)
        self.assertIn("authentication_failure", classifications)
        self.assertIn("api_schema_change", classifications)

    def test_profiles_health_and_system_prompt_are_available(self) -> None:
        bio = BrokerIntegrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        self.assertEqual(bio.capability_profiles()[0].broker_id, "BROKER-PAPER")
        self.assertEqual(bio.health_statuses()[0].connection_status, BrokerConnectionStatus.CONNECTED)
        self.assertIn("Broker Integration Office", bio.system_prompt().prompt_text)
        self.assertIsInstance(DeterministicPaperBrokerAdapter().capability_profile(), BrokerCapabilityProfile)

    def test_response_normalization_preserves_canonical_event_shape(self) -> None:
        bio = BrokerIntegrationOffice(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        raw = RawBrokerResponse("BROKER-PAPER", "BRK-1", BrokerResponseType.FILL, "ORD-1", "EXEC-1", "FILL-1", "POS-1", 10, 10, 0, 12.5, "filled", 20, "2026-07-04T00:00:00Z", "abc")

        event = bio.normalizer.normalize(raw, "CORR-1")

        self.assertEqual(event.argos_order_id, "ORD-1")
        self.assertEqual(event.response_type, BrokerResponseType.FILL)
        self.assertEqual(event.correlation_id, "CORR-1")


if __name__ == "__main__":
    unittest.main()
