from pathlib import Path
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.testing import (  # noqa: E402
    ComplianceReporter,
    FoundationComponent,
    TestCategory,
    TestRunner,
    foundation_test_registry,
)


class FoundationTestingFrameworkTests(unittest.TestCase):
    def test_registry_covers_every_foundation_component(self) -> None:
        registry = foundation_test_registry()
        covered = {registration.component for registration in registry}

        self.assertEqual(covered, set(FoundationComponent))

    def test_registry_includes_all_required_test_categories(self) -> None:
        categories = {
            category
            for registration in foundation_test_registry()
            for category in registration.categories
        }

        self.assertTrue(set(TestCategory).issubset(categories))

    def test_each_suite_links_to_engineering_orders_and_specs(self) -> None:
        for registration in foundation_test_registry():
            with self.subTest(suite=registration.suite_id):
                self.assertTrue(registration.engineering_orders)
                self.assertTrue(registration.specifications)
                self.assertTrue(registration.module_name.startswith("test_"))

    def test_runner_executes_registered_suite_deterministically(self) -> None:
        registry = foundation_test_registry()
        structure_suite = next(
            registration
            for registration in registry
            if registration.component == FoundationComponent.REPOSITORY_STRUCTURE
        )

        result = TestRunner().run_suite(structure_suite)

        self.assertTrue(result.successful)
        self.assertGreater(result.tests_run, 0)
        self.assertEqual(result.failures, 0)
        self.assertEqual(result.errors, 0)

    def test_compliance_report_outputs_machine_readable_json(self) -> None:
        registry = foundation_test_registry()
        result = TestRunner().run_suite(registry[0])
        report = ComplianceReporter().build(registry[:1], (result,))
        decoded = json.loads(report.to_json())

        self.assertTrue(decoded["all_components_covered"] is False)
        self.assertTrue(decoded["all_suites_successful"])
        self.assertEqual(decoded["suites"][0]["suite_id"], registry[0].suite_id)

    def test_compliance_report_outputs_human_readable_markdown(self) -> None:
        registry = foundation_test_registry()
        result = TestRunner().run_suite(registry[0])
        markdown = ComplianceReporter().build(registry[:1], (result,)).to_markdown()

        self.assertIn("# Foundation Testing Compliance Report", markdown)
        self.assertIn("| Suite | Component | EOs | Specs | Tests | Status |", markdown)
        self.assertIn("PASS", markdown)


if __name__ == "__main__":
    unittest.main()

