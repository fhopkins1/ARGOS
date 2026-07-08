"""Foundation-owned deterministic testing framework."""

from .registry import (
    FoundationComponent,
    TestCategory,
    TestSuiteRegistration,
    foundation_test_registry,
)
from .reports import ComplianceReport, ComplianceReporter
from .runner import TestExecutionResult, TestRunner

__all__ = [
    "ComplianceReport",
    "ComplianceReporter",
    "FoundationComponent",
    "TestCategory",
    "TestExecutionResult",
    "TestRunner",
    "TestSuiteRegistration",
    "foundation_test_registry",
]

