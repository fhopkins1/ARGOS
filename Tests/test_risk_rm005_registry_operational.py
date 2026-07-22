from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskRm005RegistryOperationalSupport  # noqa: E402


class RiskRm005RegistryOperationalTests(unittest.TestCase):
    def test_registry_package_covers_orders_eleven_through_fifteen(self) -> None:
        package = RiskRm005RegistryOperationalSupport().build_operational_package(REPOSITORY_ROOT)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-005-011",
                "RISK-RM-005-012",
                "RISK-RM-005-013",
                "RISK-RM-005-014",
                "RISK-RM-005-015",
            ),
        )
        self.assertGreaterEqual(len(package.metrics), 17)
        self.assertGreater(package.certification_manifest.artifact_count, 0)
        self.assertEqual(
            package.certification_manifest.candidate_digest,
            package.execution_package.candidate_package.candidate_binding.candidate_digest,
        )
        self.assertEqual(package.certification_manifest.metric_count, len(package.metrics))
        self.assertEqual(package.certification_manifest.evidence_record_count, len(package.certification_evidence_registry))
        self.assertGreater(package.coverage_summary["cross_reference_edges"], package.certification_manifest.artifact_count)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_temp_candidate_builds_candidate_bound_manifest_from_real_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "argos" / "risk").mkdir(parents=True)
            (root / "Tests").mkdir()
            (root / "Documentation").mkdir()
            (root / "src" / "argos" / "risk" / "candidate_surface.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "Tests" / "test_risk_candidate_operational.py").write_text("def test_surface():\n    assert True\n", encoding="utf-8")
            (root / "Documentation" / "RISK-RM-005-EVIDENCE.md").write_text("evidence\n", encoding="utf-8")
            package = RiskRm005RegistryOperationalSupport().build_operational_package(root)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(package.certification_manifest.artifact_count, 3)
        self.assertEqual(len(package.version_compatibility_matrix), 3)
        self.assertGreaterEqual(len(package.certification_evidence_registry), 3)
        self.assertEqual(package.coverage_summary["passing_metrics"], package.coverage_summary["calculated_metrics"])

    def test_metrics_fail_closed_when_required_threshold_is_not_met(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "argos" / "risk").mkdir(parents=True)
            (root / "src" / "argos" / "risk" / "candidate_surface.py").write_text("VALUE = 1\n", encoding="utf-8")
            execution_package = RiskRm005RegistryOperationalSupport().build_operational_package(root).execution_package
            metrics = RiskRm005RegistryOperationalSupport().materialize_metrics(execution_package)

        failed_metric_names = {record.canonical_name for record in metrics if record.result == EnterpriseCertificationDecision.FAIL}
        self.assertIn("executable_test_coverage", failed_metric_names)
        self.assertIn("certification_readiness", failed_metric_names)

    def test_compatibility_and_manifest_fail_closed_on_missing_authority(self) -> None:
        support = RiskRm005RegistryOperationalSupport()
        package = support.build_operational_package(REPOSITORY_ROOT)

        compatibility = support.populate_version_compatibility_matrix(package.execution_package, compatible_versions=("2.0.0",))
        evidence = support.populate_certification_evidence_registry(package.execution_package, package.metrics, compatibility)
        graph = support.materialize_registry_cross_reference_graph(package.execution_package, package.metrics, compatibility, evidence)
        manifest = support.generate_certification_manifest(package.execution_package, package.metrics, compatibility, graph, evidence)

        self.assertTrue(any(record.result == EnterpriseCertificationDecision.FAIL for record in compatibility))
        self.assertEqual(manifest.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("manifest references failing registry evidence", manifest.findings)

    def test_manifest_fails_closed_on_inventory_mismatch(self) -> None:
        support = RiskRm005RegistryOperationalSupport()
        package = support.build_operational_package(REPOSITORY_ROOT)
        manifest = support.generate_certification_manifest(
            package.execution_package,
            package.metrics,
            package.version_compatibility_matrix,
            package.registry_cross_reference_graph,
            package.certification_evidence_registry,
            expected_artifact_count=package.certification_manifest.artifact_count + 1,
        )

        self.assertEqual(manifest.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("manifest artifact inventory does not match candidate artifact inventory", manifest.findings)


if __name__ == "__main__":
    unittest.main()
