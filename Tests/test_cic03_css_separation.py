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
from argos.css.css001_orchestration.implementation import run as run_css001  # noqa: E402
from argos.css.css001_orchestration.contract import capability as cap001  # noqa: E402
from argos.css.css002_lifecycle_triggers.implementation import run as run_css002  # noqa: E402
from argos.css.css002_lifecycle_triggers.contract import capability as cap002  # noqa: E402
from argos.css.css003_verifier_framework.implementation import run as run_css003  # noqa: E402
from argos.css.css003_verifier_framework.contract import capability as cap003  # noqa: E402
from argos.css.css004_repository_truth.implementation import run as run_css004  # noqa: E402
from argos.css.css004_repository_truth.contract import capability as cap004  # noqa: E402
from argos.css.css005_governance_interface.implementation import run as run_css005  # noqa: E402
from argos.css.css005_governance_interface.contract import capability as cap005  # noqa: E402
from argos.css.css006_drift_interface.implementation import run as run_css006  # noqa: E402
from argos.css.css006_drift_interface.contract import capability as cap006  # noqa: E402


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

    def test_each_css_subsystem_has_physical_public_contract_and_independent_execution(self) -> None:
        candidate = self.program["candidateIdentity"]
        graph = validate_css_dependency_graph(css_subsystem_contracts())
        capabilities = (cap001(), cap002(), cap003(), cap004(), cap005(), cap006())
        results = (
            run_css001(candidate, capabilities=capabilities, dependency_graph=graph),
            run_css002(candidate, events=({"eventId": "manual", "type": "manual_certification"},)),
            run_css003(candidate, verifiers=({"verifierId": "v1"},), results=({"verifierId": "v1", "state": "PASSED"},)),
            run_css004(candidate, evidence_references=({"artifactId": "a", "candidateIdentityDigest": candidate["stable_identity_hash"]},)),
            run_css005(candidate, prerequisite_verdicts=({"verdictId": "CR7", "status": "PASS", "source": "authoritative_verdict"},)),
            run_css006(candidate, baseline_identity="BASELINE", comparisons=({"domain": "repository_content", "severity": "NONE"},)),
        )

        self.assertEqual({f"CSS-00{index}" for index in range(1, 7)}, {result["subsystem_id"] for result in results})
        self.assertTrue(all(result["execution_status"] == "COMPLETED" for result in results))
        self.assertTrue(all(result["contract_version"].startswith(result["subsystem_id"].replace("-", "")) for result in results))
        self.assertTrue(all(result["evidence"]["schemaVersion"].startswith(result["subsystem_id"].replace("-", "")) for result in results))

    def test_coordinator_contracts_reference_physical_subsystem_modules(self) -> None:
        for contract in css_subsystem_contracts():
            self.assertIn("src/argos/css/", contract.implementation_location)
            self.assertNotIn("control_panel/css_separation.py:execute_css", contract.implementation_location)


if __name__ == "__main__":
    unittest.main()
