"""Compliance reporting for deterministic Foundation tests."""

from __future__ import annotations

from dataclasses import dataclass
import json

from .registry import FoundationComponent, TestSuiteRegistration
from .runner import TestExecutionResult


@dataclass(frozen=True)
class ComplianceReport:
    """Machine-readable and human-readable compliance report."""

    registry: tuple[TestSuiteRegistration, ...]
    results: tuple[TestExecutionResult, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic machine-readable report."""
        result_by_suite = {result.suite_id: result for result in self.results}
        suites = []
        for registration in self.registry:
            result = result_by_suite.get(registration.suite_id)
            suites.append(
                {
                    "categories": [category.value for category in registration.categories],
                    "component": registration.component.value,
                    "engineering_orders": list(registration.engineering_orders),
                    "module_name": registration.module_name,
                    "result": result.to_dict() if result else None,
                    "specifications": list(registration.specifications),
                    "suite_id": registration.suite_id,
                }
            )
        return {
            "all_components_covered": self.all_components_covered(),
            "all_suites_successful": all(result.successful for result in self.results),
            "suites": suites,
        }

    def to_json(self) -> str:
        """Return deterministic JSON report."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def to_markdown(self) -> str:
        """Return human-readable Markdown report."""
        lines = [
            "# Foundation Testing Compliance Report",
            "",
            f"- All components covered: {self.all_components_covered()}",
            f"- All suites successful: {all(result.successful for result in self.results)}",
            "",
            "| Suite | Component | EOs | Specs | Tests | Status |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
        result_by_suite = {result.suite_id: result for result in self.results}
        for registration in self.registry:
            result = result_by_suite.get(registration.suite_id)
            tests_run = result.tests_run if result else 0
            status = "PASS" if result and result.successful else "FAIL"
            lines.append(
                "| "
                + " | ".join(
                    [
                        registration.suite_id,
                        registration.component.value,
                        ", ".join(registration.engineering_orders),
                        ", ".join(registration.specifications),
                        str(tests_run),
                        status,
                    ]
                )
                + " |"
            )
        return "\n".join(lines)

    def all_components_covered(self) -> bool:
        """Return whether every current Foundation component has a suite."""
        covered = {registration.component for registration in self.registry}
        return set(FoundationComponent) == covered


class ComplianceReporter:
    """Build compliance reports from registry and execution results."""

    def build(
        self,
        registry: tuple[TestSuiteRegistration, ...],
        results: tuple[TestExecutionResult, ...],
    ) -> ComplianceReport:
        """Build a compliance report."""
        return ComplianceReport(registry, results)

