from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskRm005CandidateOperationalSupport  # noqa: E402


class RiskRm005CandidateOperationalTests(unittest.TestCase):
    def test_candidate_package_binds_actual_repository_artifacts(self) -> None:
        package = RiskRm005CandidateOperationalSupport().build_operational_package(REPOSITORY_ROOT)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-005-001",
                "RISK-RM-005-002",
                "RISK-RM-005-003",
                "RISK-RM-005-004",
                "RISK-RM-005-005",
            ),
        )
        self.assertGreater(package.candidate_binding.artifact_count, 0)
        self.assertEqual(package.candidate_binding.result, EnterpriseCertificationDecision.PASS)
        self.assertIn("risk-runtime-source", package.candidate_class_registry)
        self.assertIn("risk-certification-test", package.candidate_class_registry)
        self.assertIn("RISK-SOURCE", package.constitutional_identifier_registry)
        self.assertIn("RISK-TEST", package.constitutional_identifier_registry)
        self.assertEqual(package.identity_collisions, {})
        self.assertEqual(package.candidate_binding.candidate_digest, RiskRm005CandidateOperationalSupport().build_operational_package(REPOSITORY_ROOT).candidate_binding.candidate_digest)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_candidate_discovery_inspects_material_files_not_expected_catalogs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "argos" / "risk").mkdir(parents=True)
            (root / "Tests").mkdir()
            (root / "Documentation").mkdir()
            (root / "src" / "argos" / "risk" / "candidate_surface.py").write_text("RISK_VALUE = 1\n", encoding="utf-8")
            (root / "Tests" / "test_risk_candidate_surface.py").write_text("def test_surface():\n    assert True\n", encoding="utf-8")
            (root / "Documentation" / "RISK-RM-005-EVIDENCE.md").write_text("# evidence\n", encoding="utf-8")
            (root / "unrelated.txt").write_text("ignored\n", encoding="utf-8")

            support = RiskRm005CandidateOperationalSupport()
            artifacts = support.discover_artifacts(root)
            package = support.build_operational_package(root)

        self.assertEqual(len(artifacts), 3)
        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual({artifact.artifact_class for artifact in artifacts}, {"risk-runtime-source", "risk-certification-test", "risk-certification-evidence"})
        self.assertNotIn("unrelated.txt", package.candidate_binding.bound_artifact_digests)

    def test_candidate_binding_fails_closed_without_certifiable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("not risk-owned\n", encoding="utf-8")
            support = RiskRm005CandidateOperationalSupport()
            artifacts = support.discover_artifacts(root)
            binding = support.bind_candidate(root, artifacts)
            package = support.build_operational_package(root)

        self.assertEqual(artifacts, ())
        self.assertEqual(binding.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("candidate has no discovered certifiable artifacts", binding.findings)
        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.FAIL)

    def test_identity_collision_is_detected_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "argos" / "risk").mkdir(parents=True)
            (root / "src" / "argos" / "risk" / "risk_a.py").write_text("A = 1\n", encoding="utf-8")
            (root / "src" / "argos" / "risk" / "risk-a.py").write_text("A = 2\n", encoding="utf-8")
            package = RiskRm005CandidateOperationalSupport().build_operational_package(root)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(len(package.identity_collisions), 1)
        collision_members = next(iter(package.identity_collisions.values()))
        self.assertEqual(len(collision_members), 2)


if __name__ == "__main__":
    unittest.main()
