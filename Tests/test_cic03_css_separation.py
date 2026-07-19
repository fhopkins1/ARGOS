from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.css_separation import (  # noqa: E402
    CSSSubsystemContract,
    CONTRACT_VERSION,
    css_subsystem_contracts,
    execute_css_separation_program,
    inspect_css_repository_surface,
    validate_css_contracts,
    validate_css_dependency_graph,
)


class CIC03CSSSeparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cr7 = {"repositoryCommit": "TEST-COMMIT", "verdict": "INCOMPLETE", "canonicalTestDenominator": {"denominatorHash": "TEST"}}
        cr10 = {"repositoryCommit": "TEST-COMMIT", "verdict": "INCOMPLETE", "paperCandidateQualification": {"qualified": False}}
        cls.program = execute_css_separation_program(REPOSITORY_ROOT, commit="TEST-COMMIT", cr7_payload=cr7, cr10_payload=cr10)

    def test_six_canonical_subsystem_contracts_exist(self) -> None:
        contracts = css_subsystem_contracts()
        ids = {contract.subsystem_id for contract in contracts}

        self.assertEqual({f"CSS-00{index}" for index in range(1, 7)}, ids)
        self.assertTrue(all(contract.contract_version == CONTRACT_VERSION for contract in contracts))
        self.assertTrue(all(contract.implementation_location for contract in contracts))
        self.assertTrue(all(contract.produced_output_types for contract in contracts))

    def test_contract_validation_rejects_duplicate_or_malformed_contracts(self) -> None:
        contracts = css_subsystem_contracts()
        duplicate = validate_css_contracts((contracts[0], contracts[0]))
        malformed = CSSSubsystemContract(
            "CSS-099",
            "",
            "1",
            "BAD",
            "",
            (),
            (),
            (),
            (),
            "",
            (),
            False,
            False,
            "",
        )
        malformed_result = validate_css_contracts((malformed,))

        self.assertFalse(duplicate["valid"])
        self.assertTrue(any(code.startswith("DUPLICATE_SUBSYSTEM") for code in duplicate["failureCodes"]))
        self.assertFalse(malformed_result["valid"])
        self.assertTrue(any(code.startswith("UNSUPPORTED_CONTRACT_VERSION") for code in malformed_result["failureCodes"]))

    def test_dependency_graph_is_deterministic_and_acyclic(self) -> None:
        graph = validate_css_dependency_graph(css_subsystem_contracts())
        repeated = validate_css_dependency_graph(css_subsystem_contracts())

        self.assertTrue(graph["valid"])
        self.assertEqual(graph["graphHash"], repeated["graphHash"])
        self.assertEqual("CSS-001", graph["topologicalOrder"][0])
        self.assertEqual(6, len(graph["topologicalOrder"]))

    def test_repository_inspection_records_existing_css_surface(self) -> None:
        inspection = inspect_css_repository_surface(REPOSITORY_ROOT)

        self.assertIn("src/argos/control_panel/continuous_constitutional_certification.py", inspection["cssRelatedModules"])
        self.assertIn("Tests/test_css_continuous_certification.py", inspection["cssTests"])
        self.assertTrue(inspection["inspectionHash"])

    def test_program_executes_independent_subsystems_with_limited_coordinator(self) -> None:
        payload = self.program

        self.assertEqual("CIC-03", payload["orderId"])
        self.assertEqual(6, len(payload["subsystemResults"]))
        self.assertEqual({f"CSS-00{index}" for index in range(1, 7)}, {item["subsystem_id"] for item in payload["subsystemResults"]})
        self.assertIn("repository truth evaluation", payload["coordinatorAuthority"]["prohibited"])
        self.assertTrue(payload["responsibilityOwnership"]["exclusive"])
        self.assertEqual("PASS", payload["acceptanceGates"]["verdict"])

    def test_program_fails_closed_when_subsystems_report_failures(self) -> None:
        payload = self.program

        self.assertEqual("FAIL", payload["verdict"])
        self.assertTrue(any(item["status"] == "FAIL" for item in payload["subsystemResults"]))
        self.assertTrue(any(item["failure_codes"] for item in payload["subsystemResults"]))


if __name__ == "__main__":
    unittest.main()
