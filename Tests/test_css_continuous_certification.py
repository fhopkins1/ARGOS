from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.continuous_constitutional_certification import (  # noqa: E402
    build_certification_claim_registry,
    build_repository_truth_index,
    detect_certification_drift,
    execute_css_sustainment_pipeline,
)


class ContinuousConstitutionalCertificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cr7 = {
            "repositoryCommit": "TEST-COMMIT",
            "verdict": "INCOMPLETE",
            "canonicalTestDenominator": {"denominatorHash": "TEST-DENOMINATOR"},
        }
        cr10 = {
            "repositoryCommit": "TEST-COMMIT",
            "verdict": "INCOMPLETE",
            "paperCandidateQualification": {"qualified": False},
        }
        cls.index = build_repository_truth_index(REPOSITORY_ROOT, commit="TEST-COMMIT")
        cls.registry = build_certification_claim_registry(REPOSITORY_ROOT, commit="TEST-COMMIT", repository_index=cls.index)
        cls.drift = detect_certification_drift(REPOSITORY_ROOT, commit="TEST-COMMIT", repository_index=cls.index)
        cls.pipeline = execute_css_sustainment_pipeline(REPOSITORY_ROOT, commit="TEST-COMMIT", cr7_payload=cr7, cr10_payload=cr10)

    def test_repository_truth_index_discovers_runtime_tests_generators_and_bridges(self) -> None:
        self.assertGreater(self.index["runtimeModuleCount"], 100)
        self.assertGreater(self.index["testCount"], 100)
        self.assertGreater(self.index["evidenceGeneratorCount"], 10)
        self.assertGreater(self.index["bridgeCount"], 20)
        self.assertTrue(self.index["indexHash"])

    def test_claim_registry_requires_implementation_and_tests(self) -> None:
        claim_ids = {claim["claimId"] for claim in self.registry["claims"]}

        self.assertIn("CSS-CLAIM-BRIDGE-FIDELITY", claim_ids)
        self.assertIn("CSS-CLAIM-SYNTHETIC-TRUTH", claim_ids)
        self.assertEqual(self.registry["claimCount"], 5)
        self.assertTrue(self.registry["registryHash"])

    def test_drift_detection_fails_closed_without_certified_baseline(self) -> None:
        self.assertEqual("FAIL", self.drift["verdict"])
        self.assertFalse(self.drift["baselinePresent"])
        self.assertTrue(any("baseline" in finding.lower() for finding in self.drift["blockingFindings"]))

    def test_css_pipeline_fails_closed_when_cr10_is_not_pass(self) -> None:
        payload = self.pipeline

        self.assertEqual("FAIL", payload["verdict"])
        self.assertEqual("NOT CERTIFIABLE", payload["readiness"]["state"])
        self.assertTrue(payload["prerequisiteBlockers"])
        self.assertTrue(all(stage["verdict"] in {"PASS", "FAIL"} for stage in payload["pipelineStages"]))
        self.assertTrue(any(stage["verdict"] == "FAIL" for stage in payload["pipelineStages"]))

    def test_verification_catalog_is_observational_and_fail_closed(self) -> None:
        tasks = self.pipeline["verificationTaskCatalog"]

        self.assertGreaterEqual(len(tasks), 8)
        self.assertTrue(all(task["failClosed"] for task in tasks))
        self.assertTrue(all(not task["mayModifyRuntime"] for task in tasks))


if __name__ == "__main__":
    unittest.main()
