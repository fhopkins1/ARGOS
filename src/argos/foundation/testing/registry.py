"""Deterministic Foundation test suite registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TestCategory(str, Enum):
    """EO-009 test infrastructure categories."""

    UNIT = "unit"
    INTEGRATION = "integration"
    CONTRACT = "contract"
    REGRESSION = "regression"
    REPLAY = "replay"
    FAILURE_INJECTION = "failure_injection"


class FoundationComponent(str, Enum):
    """Foundation components requiring automated test coverage."""

    REPOSITORY_STRUCTURE = "repository_structure"
    IDENTITY = "identity"
    CONTRACTS = "contracts"
    COMMUNICATION = "communication"
    AUDIT = "audit"
    CONFIGURATION = "configuration"
    PERSISTENCE = "persistence"
    PROMPTS = "prompts"
    TESTING = "testing"


@dataclass(frozen=True)
class TestSuiteRegistration:
    """Registered deterministic test suite."""

    suite_id: str
    component: FoundationComponent
    module_name: str
    categories: tuple[TestCategory, ...]
    engineering_orders: tuple[str, ...]
    specifications: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.suite_id.strip():
            raise ValueError("suite_id must not be empty")
        if not self.module_name.startswith("test_"):
            raise ValueError("module_name must reference a deterministic test module")
        object.__setattr__(self, "categories", tuple(self.categories))
        object.__setattr__(self, "engineering_orders", tuple(self.engineering_orders))
        object.__setattr__(self, "specifications", tuple(self.specifications))
        if not self.categories:
            raise ValueError("test suite requires at least one category")
        if not self.engineering_orders:
            raise ValueError("test suite requires EO coverage")


def foundation_test_registry() -> tuple[TestSuiteRegistration, ...]:
    """Return registered deterministic Foundation test suites."""
    return (
        TestSuiteRegistration(
            "TS-FOUNDATION-001",
            FoundationComponent.REPOSITORY_STRUCTURE,
            "test_repository_structure",
            (TestCategory.UNIT, TestCategory.REGRESSION),
            ("EO-001",),
            ("PB-001", "PB-008"),
        ),
        TestSuiteRegistration(
            "TS-FOUNDATION-002",
            FoundationComponent.IDENTITY,
            "test_identity_framework",
            (TestCategory.UNIT, TestCategory.CONTRACT, TestCategory.REGRESSION),
            ("EO-002",),
            ("PB-005", "PB-006"),
        ),
        TestSuiteRegistration(
            "TS-FOUNDATION-003",
            FoundationComponent.CONTRACTS,
            "test_contract_framework",
            (TestCategory.UNIT, TestCategory.CONTRACT, TestCategory.FAILURE_INJECTION),
            ("EO-003",),
            ("PB-003", "PB-005", "PB-007"),
        ),
        TestSuiteRegistration(
            "TS-FOUNDATION-004",
            FoundationComponent.COMMUNICATION,
            "test_communication_framework",
            (TestCategory.UNIT, TestCategory.INTEGRATION, TestCategory.FAILURE_INJECTION),
            ("EO-004",),
            ("PB-003", "PB-007"),
        ),
        TestSuiteRegistration(
            "TS-FOUNDATION-005",
            FoundationComponent.AUDIT,
            "test_audit_framework",
            (TestCategory.UNIT, TestCategory.INTEGRATION, TestCategory.REPLAY),
            ("EO-005",),
            ("PB-003", "PB-005", "PB-007"),
        ),
        TestSuiteRegistration(
            "TS-FOUNDATION-006",
            FoundationComponent.CONFIGURATION,
            "test_configuration_framework",
            (TestCategory.UNIT, TestCategory.CONTRACT, TestCategory.FAILURE_INJECTION),
            ("EO-006",),
            ("PB-008",),
        ),
        TestSuiteRegistration(
            "TS-FOUNDATION-007",
            FoundationComponent.PERSISTENCE,
            "test_persistence_framework",
            (TestCategory.UNIT, TestCategory.INTEGRATION, TestCategory.REPLAY),
            ("EO-007",),
            ("PB-005", "PB-006"),
        ),
        TestSuiteRegistration(
            "TS-FOUNDATION-008",
            FoundationComponent.PROMPTS,
            "test_prompt_specification_repository",
            (TestCategory.UNIT, TestCategory.CONTRACT, TestCategory.REGRESSION),
            ("EO-008",),
            ("PB-001", "PB-006", "PB-008"),
        ),
        TestSuiteRegistration(
            "TS-FOUNDATION-009",
            FoundationComponent.TESTING,
            "test_foundation_testing_framework",
            (TestCategory.UNIT, TestCategory.CONTRACT, TestCategory.REGRESSION),
            ("EO-009",),
            ("PB-001", "PB-008"),
        ),
    )

