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
from argos.historian import (  # noqa: E402
    HistoricalCase,
    HistorianGroupFramework,
    OrganizationalPerformanceMetrics,
    ValidationStatus,
    historian_office_templates,
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


def historical_case() -> HistoricalCase:
    return HistoricalCase(
        "HC-061",
        "CDR-061",
        ("EV-061-A", "EV-061-B"),
        ("AAR-061", "AFR-061"),
        "RAR-061",
        "EXEC-HIST-061",
        "POS-HIST-061",
        "MKT-061",
        "positive_return",
        ("correct assumption: liquidity remained available", "incorrect assumption: volatility stayed low"),
        ValidationStatus.PENDING,
        "AUD-061",
    )


def metrics() -> OrganizationalPerformanceMetrics:
    return OrganizationalPerformanceMetrics(0.04, 0.8, 0.7, 0.92, 0.85, 0.78, 0.88, 0.73, 0.9, 0.6)


class HistorianGroupFrameworkTests(unittest.TestCase):
    def test_architecture_and_office_templates_exist(self) -> None:
        framework = HistorianGroupFramework(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        architecture = framework.architecture()

        self.assertIn("Executive Group", architecture.upstream_groups)
        self.assertIn("Librarian Group", architecture.downstream_groups)
        self.assertEqual(len(historian_office_templates()), 4)

    def test_historical_case_is_persisted_and_audited(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        framework = HistorianGroupFramework(config(), persistence, audit, PromptRepository())

        contract = framework.create_historical_case(historical_case(), "CF-001", "TC-001", 6101)

        self.assertEqual(contract.contract_type, "HISTORICAL_CASE")
        self.assertFalse(contract.machine_payload["historical_record_overwritten"])
        self.assertFalse(contract.machine_payload["organizational_evidence_discarded"])
        self.assertIsNotNone(persistence.latest(ObjectType.OPERATIONAL_DOCUMENT, contract.contract_id))
        self.assertIn(AuditEventType.DOCUMENT_CREATED, tuple(event.event_type for event in audit.audit_log.events))

    def test_case_evaluation_produces_validated_learning(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        framework = HistorianGroupFramework(config(), persistence, AuditService(), PromptRepository())
        framework.create_historical_case(historical_case(), "CF-001", "TC-001", 6110)

        artifacts = framework.evaluate_case("HC-061", metrics(), "CF-001", "TC-001", 6111)

        evaluation = artifacts["historical_evaluation"].machine_payload["historical_evaluation"]
        learning = artifacts["validated_learning_record"].machine_payload["validated_learning_record"]
        self.assertEqual(evaluation["historical_case_id"], "HC-061")
        self.assertIn("decision_accuracy", evaluation["what_succeeded"])
        self.assertFalse(evaluation["anecdotal_evidence_accepted"])
        self.assertEqual(learning["validation_status"], ValidationStatus.VALIDATED.value)
        self.assertFalse(learning["directly_modifies_behavior"])
        self.assertIn("Librarian Group", learning["recommended_consumers"])

    def test_duplicate_cases_and_unknown_cases_are_rejected(self) -> None:
        framework = HistorianGroupFramework(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())
        framework.create_historical_case(historical_case(), "CF-001", "TC-001", 6120)

        with self.assertRaises(ValueError):
            framework.create_historical_case(historical_case(), "CF-001", "TC-001", 6121)
        with self.assertRaises(ValueError):
            framework.evaluate_case("HC-UNKNOWN", metrics(), "CF-001", "TC-001", 6122)

    def test_system_prompt_declares_scientific_boundaries(self) -> None:
        framework = HistorianGroupFramework(config(), InMemoryPersistenceRepository(canonical_schemas()), AuditService(), PromptRepository())

        prompt = framework.system_prompt()

        self.assertIn("Historian Group", prompt.prompt_text)
        self.assertIn("You do not gather market intelligence", prompt.prompt_text)
        self.assertIn("Never accept anecdotal evidence", prompt.prompt_text)
        self.assertIn("Recommendations shall never directly modify organizational behavior", prompt.prompt_text)
        self.assertEqual(prompt.version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
