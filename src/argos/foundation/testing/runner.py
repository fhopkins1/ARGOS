"""Deterministic unittest runner for registered Foundation suites."""

from __future__ import annotations

from dataclasses import dataclass
import io
from pathlib import Path
import unittest

from .registry import TestSuiteRegistration


@dataclass(frozen=True)
class TestExecutionResult:
    """Machine-readable test execution result."""

    suite_id: str
    module_name: str
    tests_run: int
    failures: int
    errors: int
    skipped: int
    successful: bool

    def to_dict(self) -> dict[str, object]:
        """Serialize execution result."""
        return {
            "errors": self.errors,
            "failures": self.failures,
            "module_name": self.module_name,
            "skipped": self.skipped,
            "successful": self.successful,
            "suite_id": self.suite_id,
            "tests_run": self.tests_run,
        }


class TestRunner:
    """Run registered suites through Python's deterministic unittest loader."""

    def run_suite(self, registration: TestSuiteRegistration) -> TestExecutionResult:
        """Run one registered suite."""
        tests_dir = Path.cwd() / "Tests"
        suite = unittest.defaultTestLoader.discover(
            start_dir=str(tests_dir),
            pattern=f"{registration.module_name}.py",
        )
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
        return TestExecutionResult(
            suite_id=registration.suite_id,
            module_name=registration.module_name,
            tests_run=result.testsRun,
            failures=len(result.failures),
            errors=len(result.errors),
            skipped=len(result.skipped),
            successful=result.wasSuccessful(),
        )

    def run_all(self, registry: tuple[TestSuiteRegistration, ...]) -> tuple[TestExecutionResult, ...]:
        """Run every registered suite in deterministic registry order."""
        return tuple(self.run_suite(registration) for registration in registry)
