from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import (  # noqa: E402
    ConstitutionalRequirementRegistry,
    CoverageStatus,
    TestCompletenessEvidenceOffice,
    TestInventory,
    TestStrength,
    VerificationDefectStatus,
    classify_test_strength,
    constitutional_requirement_catalog,
    eo_acceptance_criteria,
)


class TestCompletenessEvidenceOfficeTests(unittest.TestCase):
    def test_requirement_registry_rejects_duplicates_and_requires_source_linkage(self) -> None:
        requirement = constitutional_requirement_catalog()[0]
        registry = ConstitutionalRequirementRegistry((requirement,))

        with self.assertRaisesRegex(ValueError, "duplicate requirement id"):
            registry.register(requirement)
        with self.assertRaisesRegex(ValueError, "source linkage required"):
            ConstitutionalRequirementRegistry((replace(requirement, requirement_id="REQ-BAD", source_document=""),))

    def test_supersession_is_version_preserving(self) -> None:
        requirement = replace(constitutional_requirement_catalog()[0], requirement_id="REQ-SUPERSEDED", superseded_by="REQ-LAWVII-002")
        registry = ConstitutionalRequirementRegistry((requirement,))

        self.assertEqual(registry.all()[0].superseded_by, "REQ-LAWVII-002")

    def test_eo_acceptance_registry_contains_series_d_and_or_orders(self) -> None:
        criteria = eo_acceptance_criteria(commit="test")
        eo_ids = {item.eo_id for item in criteria}

        self.assertIn("EO-DA", eo_ids)
        self.assertIn("EO-DH", eo_ids)
        self.assertIn("EO-DI", eo_ids)
        self.assertIn("OR-007", eo_ids)
        self.assertTrue(all(item.last_verified_commit == "test" for item in criteria))

    def test_test_inventory_discovers_tests_and_rejects_duplicate_identity(self) -> None:
        office = TestCompletenessEvidenceOffice()
        tests = office.discover_tests(REPOSITORY_ROOT / "Tests", commit="test")
        inventory = TestInventory((tests[0],))

        self.assertGreater(len(tests), 100)
        self.assertTrue(any(test.file.endswith("test_eodh_synthetic_truth_quarantine.py") for test in tests))
        with self.assertRaisesRegex(ValueError, "duplicate test id"):
            inventory.register(tests[0])

    def test_strength_classifier_distinguishes_unit_runtime_fault_and_endurance(self) -> None:
        self.assertEqual(TestStrength.LEVEL_1_LOCAL_UNIT, classify_test_strength("Tests/test_unit.py", "test_value", "self.assertEqual(1, 1)"))
        self.assertEqual(TestStrength.LEVEL_4_CANONICAL_RUNTIME, classify_test_strength("Tests/test_runtime_provider.py", "test_provider", "create_runtime_provider_for_tests(CanonicalEnterpriseRuntime())"))
        self.assertEqual(TestStrength.LEVEL_6_FAULT_AND_RECOVERY, classify_test_strength("Tests/test_fault.py", "test_recovery", "recovery attack"))
        self.assertEqual(TestStrength.LEVEL_7_LONG_DURATION_OPERATION, classify_test_strength("Tests/test_eodf_long_duration_operations_lab.py", "test_endurance", "endurance campaign"))

    def test_traceability_detects_missing_evidence_and_noncanonical_coverage(self) -> None:
        office = TestCompletenessEvidenceOffice()
        tests = office.discover_tests(REPOSITORY_ROOT / "Tests", commit="test")
        evidence = office.evidence_inventory(REPOSITORY_ROOT, commit="test")
        matrix = office.traceability_matrix(tests, evidence)
        statuses = {row.requirement_id: row.current_status for row in matrix}

        self.assertIn(statuses["REQ-BRIDGE-001"], {CoverageStatus.PARTIALLY_PROVEN, CoverageStatus.TESTED_NONCANONICALLY, CoverageStatus.PROVEN})
        self.assertTrue(any(row.current_status in {CoverageStatus.MISSING_TEST, CoverageStatus.MISSING_EVIDENCE, CoverageStatus.TESTED_NONCANONICALLY, CoverageStatus.PARTIALLY_PROVEN} for row in matrix))

    def test_evaluate_produces_honest_fail_scorecard_and_defects(self) -> None:
        office = TestCompletenessEvidenceOffice()

        scorecard, tests, evidence, traceability, defects = office.evaluate(repo_root=REPOSITORY_ROOT, commit="test", branch="main")

        self.assertEqual(scorecard.verdict, "FAIL")
        self.assertGreater(scorecard.requirements_total, 0)
        self.assertGreater(scorecard.tests_total, 100)
        self.assertTrue(evidence)
        self.assertTrue(traceability)
        self.assertTrue(defects)
        self.assertFalse(scorecard.live_trading_enabled)
        self.assertFalse(scorecard.certifies_argos)

    def test_canonical_runtime_detection_does_not_count_compatibility_as_production(self) -> None:
        office = TestCompletenessEvidenceOffice()
        tests = office.discover_tests(REPOSITORY_ROOT / "Tests", commit="test")

        canonical = [test for test in tests if test.canonical_runtime_reachability]
        compatibility = [test for test in tests if test.compatibility_dependencies]

        self.assertTrue(canonical)
        self.assertTrue(all(list(TestStrength).index(test.strength_classification) >= list(TestStrength).index(TestStrength.LEVEL_4_CANONICAL_RUNTIME) for test in canonical))
        self.assertTrue(compatibility)

    def test_mock_fixture_and_proof_dependencies_are_classified(self) -> None:
        office = TestCompletenessEvidenceOffice()
        tests = office.discover_tests(REPOSITORY_ROOT / "Tests", commit="test")

        self.assertTrue(any(test.fixture_dependencies for test in tests))
        self.assertTrue(any(test.proof_dependencies for test in tests))
        self.assertTrue(any(test.simulation_dependencies for test in tests))

    def test_evidence_integrity_requires_commit_command_and_hash(self) -> None:
        office = TestCompletenessEvidenceOffice()
        evidence = office.evidence_inventory(REPOSITORY_ROOT, commit="test")

        self.assertTrue(all(item.commit for item in evidence))
        self.assertTrue(all(item.generation_command for item in evidence))
        self.assertTrue(any(item.artifact_hash for item in evidence))

    def test_test_runner_captures_pass_failure_and_timeout_honestly(self) -> None:
        office = TestCompletenessEvidenceOffice()
        with tempfile.TemporaryDirectory() as directory:
            passing = office.run_test_command("py -3 -c \"print('OK')\"", cwd=REPOSITORY_ROOT, timeout_seconds=10, output_dir=directory)
            failing = office.run_test_command("py -3 -c \"import sys; print('FAILED'); sys.exit(2)\"", cwd=REPOSITORY_ROOT, timeout_seconds=10, output_dir=directory)
            timeout = office.run_test_command("py -3 -c \"import time; time.sleep(2)\"", cwd=REPOSITORY_ROOT, timeout_seconds=1, output_dir=directory)
            self.assertTrue(Path(passing.stdout_path).exists())

        self.assertEqual(passing.exit_code, 0)
        self.assertNotEqual(failing.exit_code, 0)
        self.assertTrue(timeout.incomplete)
        self.assertEqual(timeout.timeouts, 1)

    def test_defect_cannot_close_without_verification_evidence(self) -> None:
        office = TestCompletenessEvidenceOffice()
        defect = office.evaluate(repo_root=REPOSITORY_ROOT, commit="test")[4][0]

        with self.assertRaisesRegex(ValueError, "fix commit"):
            defect.verify(fix_commit="", regression_test_id="", closure_evidence=())
        verified = defect.verify(fix_commit="abc", regression_test_id="TEST-1", closure_evidence=("evidence",))
        self.assertEqual(verified.status, VerificationDefectStatus.VERIFIED)

    def test_commander_read_model_cannot_override_or_certify(self) -> None:
        office = TestCompletenessEvidenceOffice()
        scorecard = office.evaluate(repo_root=REPOSITORY_ROOT, commit="test")[0]
        model = office.commander_read_model(scorecard)

        self.assertEqual(model["engineeringOrder"], "EO-DI")
        self.assertFalse(model["commanderControls"]["mayMarkUnprovenRequirementProven"])
        self.assertFalse(model["commanderControls"]["mayOverrideFailingEvidence"])
        self.assertFalse(model["commanderControls"]["mayCloseDefectsWithoutVerification"])
        self.assertFalse(model["commanderControls"]["mayEditRawEvidence"])
        self.assertFalse(model["commanderControls"]["mayFabricateTestResults"])
        self.assertFalse(model["commanderControls"]["mayEnableLiveTrading"])

    def test_audit_package_generates_required_artifacts_hashes_and_zip(self) -> None:
        office = TestCompletenessEvidenceOffice()

        with tempfile.TemporaryDirectory() as directory:
            paths = office.generate_audit_package(directory, repo_root=REPOSITORY_ROOT, commit="test", branch="main")

            for required in ("repository_manifest", "constitutional_requirements", "test_inventory", "requirement_test_matrix", "verification_defects", "evidence_manifest", "evidence_hashes", "zip"):
                self.assertIn(required, paths)
                self.assertTrue(Path(paths[required]).exists())
            self.assertIn("REQ-LAWVII-001", Path(paths["constitutional_requirements"]).read_text(encoding="utf-8"))
            self.assertGreater(Path(paths["zip"]).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
