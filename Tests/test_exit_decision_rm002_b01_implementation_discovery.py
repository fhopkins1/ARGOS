import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B01_IMPLEMENTATION_DISCOVERY"


class ExitDecisionRM002B01ImplementationDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/exit_decision_rm002_b01_implementation_discovery.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=120,
        )
        cls.returncode = completed.returncode
        cls.stderr = completed.stderr

    def _read_json(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_generator_completes(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_frozen_baseline_and_direct_implementation_are_discovered(self):
        baseline = self._read_json("frozen_constitutional_baseline_registry.json")
        inventory = self._read_json("implementation_inventory.json")
        self.assertEqual(baseline["verdict"], "UNCONDITIONAL_PASS")
        self.assertTrue(any(item["artifact"] == "src/argos/control_panel/position_exit_decision_engine.py" for item in inventory))
        self.assertTrue(all(item["sha256"] for item in inventory))

    def test_runtime_dependencies_are_ast_derived(self):
        inventory = self._read_json("implementation_inventory.json")
        artifacts = {item["artifact"] for item in inventory}
        self.assertIn("src/argos/control_panel/position_registry.py", artifacts)
        self.assertIn("src/argos/foundation/contracts/__init__.py", artifacts)
        self.assertTrue(any(item["imports"] for item in inventory))

    def test_verifiers_fixtures_and_interfaces_are_present_without_execution(self):
        verifiers = self._read_json("verifier_population_registry.json")
        fixtures = self._read_json("fixture_population_registry.json")
        interfaces = self._read_json("interface_dependency_registry.json")
        self.assertTrue(verifiers)
        self.assertTrue(fixtures)
        self.assertTrue(interfaces)
        self.assertTrue(all(item["execution_status"] == "NOT_EXECUTED_UNDER_B01" for item in verifiers))

    def test_every_requirement_has_implementation_obligation(self):
        requirements = json.loads((REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B05_FINAL_READINESS" / "canonical_requirement_identity_registry.json").read_text(encoding="utf-8"))
        obligations = self._read_json("implementation_obligation_registry.json")
        self.assertEqual(len(obligations), len(requirements))
        self.assertTrue(all(item["implementation_artifacts"] for item in obligations))
        self.assertTrue(all(item["verification_status"] == "PENDING_BEHAVIORAL_VERIFICATION_B02" for item in obligations))

    def test_completion_report_ready_for_b02_and_keeps_conditional_programs_inactive(self):
        completion = self._read_json("completion_report.json")
        conditional = self._read_json("conditional_program_registry.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["ready_for"], "EXIT-DECISION-RM-002-B02")
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["conditional_remediation_orders_created"])
        self.assertTrue(all(value == "CONDITIONAL_ONLY_NOT_ACTIVATED" for value in conditional.values()))
        self.assertTrue(all(completion["completion_checks"].values()))


if __name__ == "__main__":
    unittest.main()
