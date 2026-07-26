import json
from pathlib import Path
import unittest

from Scripts.closed_position_truth_rm002_b07_001_repository_validation import OUTPUT_DIR, generate_validation


class ClosedPositionTruthRm002B07001RepositoryValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completion = generate_validation()

    def _read(self, name):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_required_deliverables_are_generated(self):
        required = [
            "repository_manifest.json",
            "repository_identity_registry.json",
            "repository_hash_registry.json",
            "repository_inventory.json",
            "executable_artifact_registry.json",
            "manifest_registry.json",
            "repository_structure_report.json",
            "repository_completeness_report.json",
            "validation_findings_registry.json",
            "dependency_registry.json",
            "runtime_dependency_report.json",
            "external_prerequisite_registry.json",
            "optional_dependency_registry.json",
            "certification_dependency_registry.json",
            "hidden_dependency_registry.json",
            "missing_dependency_registry.json",
            "dependency_classification_report.json",
            "environment_registry.json",
            "configuration_registry.json",
            "environment_variable_registry.json",
            "configuration_source_registry.json",
            "secret_dependency_registry.json",
            "external_endpoint_registry.json",
            "startup_dependency_registry.json",
            "hidden_configuration_registry.json",
            "environment_validation_report.json",
            "repository_independence_report.json",
            "hidden_repository_dependency_registry.json",
            "repository_state_validation_report.json",
            "external_repository_dependency_inventory.json",
            "package_only_execution_assessment.json",
            "repository_independence_evidence_registry.json",
            "completion_report.json",
            "manifest.json",
        ]
        for name in required:
            self.assertTrue((OUTPUT_DIR / name).is_file(), name)

    def test_package_validation_is_complete_and_non_behavioral(self):
        completion = self._read("completion_report.json")
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertTrue(completion["extraction_success"])
        self.assertTrue(completion["repository_independent"])
        self.assertFalse(completion["behavioral_verification_occurred"])
        self.assertFalse(completion["mutation_campaign_occurred"])
        self.assertFalse(completion["proof_generation_occurred"])
        self.assertFalse(completion["certification_verdict_issued"])
        self.assertTrue(all(completion["completion_criteria"].values()))

    def test_dependencies_are_classified_with_acquisition_paths(self):
        dependencies = self._read("dependency_registry.json")
        classification = self._read("dependency_classification_report.json")
        missing = self._read("missing_dependency_registry.json")
        certification = self._read("certification_dependency_registry.json")

        self.assertGreater(len(dependencies), 0)
        self.assertGreater(len(certification), 0)
        self.assertFalse(missing)
        self.assertFalse(classification["unresolved_runtime_dependency_unknown"])
        for dependency in dependencies:
            self.assertIn("classification", dependency)
            self.assertTrue(dependency["installation_mechanism"])
            self.assertTrue(dependency["source_of_discovery"])

    def test_repository_independence_is_package_only(self):
        identity = self._read("repository_identity_registry.json")
        independence = self._read("repository_independence_report.json")
        package_only = self._read("package_only_execution_assessment.json")
        evidence = self._read("repository_independence_evidence_registry.json")

        self.assertTrue(Path(identity["package_path"]).is_file())
        self.assertTrue(identity["extraction_success"])
        self.assertFalse(independence["git_directory_present"])
        self.assertFalse(independence["git_metadata_required_for_validation"])
        self.assertFalse(independence["repository_clone_required"])
        self.assertFalse(independence["manual_repository_preparation_required"])
        self.assertTrue(package_only["validated"])
        self.assertIsInstance(evidence, list)
        for row in evidence:
            self.assertIn("evidence_id", row)
            self.assertIn("path", row)

    def test_environment_and_hidden_dependency_discovery_are_recorded(self):
        env_vars = self._read("environment_variable_registry.json")
        hidden = self._read("hidden_dependency_registry.json")
        report = self._read("environment_validation_report.json")

        self.assertIsInstance(env_vars, list)
        self.assertIsInstance(hidden, list)
        self.assertTrue(report["startup_deterministic"])
        self.assertEqual(report["hidden_configuration_blockers"], [])


if __name__ == "__main__":
    unittest.main()
