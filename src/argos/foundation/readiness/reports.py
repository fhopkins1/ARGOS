"""Operational readiness and Foundation completion reports."""

from __future__ import annotations

from dataclasses import dataclass

from .verifier import ReadinessResult


@dataclass(frozen=True)
class FoundationReportGenerator:
    """Generate EO-010 readiness artifacts."""

    result: ReadinessResult

    def operational_readiness_report(self) -> str:
        """Generate the Operational Readiness Report."""
        lines = [
            "# ORR-001 Operational Readiness Report",
            "",
            "Status: PASS" if self.result.authorized else "Status: FAIL",
            "",
            "## Readiness Checks",
        ]
        for check in self.result.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {check.check_id}: {status} - {check.name}. {check.detail}")
        lines.extend(["", "## Test Execution"])
        for test_result in self.result.test_results:
            status = "PASS" if test_result.successful else "FAIL"
            lines.append(
                f"- {test_result.suite_id}: {status} "
                f"({test_result.tests_run} tests, {test_result.failures} failures, "
                f"{test_result.errors} errors)"
            )
        return "\n".join(lines) + "\n"

    def foundation_completion_report(self) -> str:
        """Generate FCR-001."""
        status = "COMPLETE" if self.result.authorized else "INCOMPLETE"
        return "\n".join(
            [
                "# FCR-001 Foundation Completion Report",
                "",
                f"Foundation Status: {status}",
                "",
                "Completed Engineering Orders: EO-001 through EO-010",
                "",
                "Foundation capabilities verified:",
                "- Repository scaffold",
                "- Identity framework",
                "- Canonical contracts",
                "- Courier communication",
                "- Audit and traceability",
                "- Configuration and environments",
                "- Persistence foundation",
                "- Prompt and specification repository",
                "- Testing framework",
                "- Operational readiness verification",
                "",
            ]
        )

    def authorization_to_proceed(self) -> str:
        """Generate Authorization to Proceed for Group 2."""
        authorization = "AUTHORIZED" if self.result.authorized else "NOT AUTHORIZED"
        return "\n".join(
            [
                "# Authorization to Proceed - Group 2",
                "",
                f"Decision: {authorization}",
                "",
                "Scope: Executive Group implementation may begin only after ORR-001 passes.",
                "",
                "Basis: EO-010 readiness verification and Foundation test execution.",
                "",
            ]
        )

