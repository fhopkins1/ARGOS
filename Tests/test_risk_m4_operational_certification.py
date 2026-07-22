from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskM4OperationalCertificationEngine  # noqa: E402


class RiskM4OperationalCertificationTests(unittest.TestCase):
    def test_m4_operational_certification_binds_candidate_and_closes_when_candidate_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = RiskM4OperationalCertificationEngine(REPOSITORY_ROOT).certify(tmp)

        self.assertEqual(package.final_certification_result, EnterpriseCertificationDecision.PASS)
        self.assertEqual(package.closure_status, "CLOSED")
        self.assertEqual(len(package.work_orders), 25)
        self.assertEqual(package.work_orders[0].work_order_identifier, "RISK-RM-003-001")
        self.assertEqual(package.work_orders[-1].work_order_identifier, "RISK-RM-003-025")
        self.assertEqual(package.metrics["registries"], 175)
        self.assertEqual(package.metrics["rules_executed"], 25)
        self.assertEqual(package.metrics["tests_executed"], 25)
        self.assertEqual(package.metrics["traceability_records"], 25)
        self.assertEqual(package.replay_result, EnterpriseCertificationDecision.PASS)
        self.assertEqual(package.recovery_result, EnterpriseCertificationDecision.PASS)
        self.assertTrue(package.candidate.candidate_commit)
        self.assertTrue(package.candidate.source_digest)
        self.assertFalse(package.unresolved_findings)
        self.assertTrue(package.evidence_registry)

    def test_m4_operational_certification_persists_independently_inspectable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_root = Path(tmp)
            package = RiskM4OperationalCertificationEngine(REPOSITORY_ROOT).certify(evidence_root)

            expected = {
                "candidate_identity.json",
                "registries.json",
                "rule_results.json",
                "test_results.json",
                "traceability_matrix.json",
                "manifest.json",
                "decisions.json",
                "certification_package.json",
            }
            self.assertTrue(expected.issubset({path.name for path in evidence_root.iterdir()}))
            persisted = (evidence_root / "certification_package.json").read_text(encoding="utf-8")

        self.assertIn(package.package_identifier, persisted)
        self.assertIn("final_certification_result", persisted)
        self.assertIn(package.deterministic_digest, persisted)

    def test_m4_operational_certification_fails_closed_when_candidate_artifact_is_missing(self) -> None:
        required_paths = RiskM4OperationalCertificationEngine.required_candidate_paths + (
            "src/argos/risk/nonexistent_m4_candidate_dependency.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            package = RiskM4OperationalCertificationEngine(
                REPOSITORY_ROOT,
                required_candidate_paths=required_paths,
            ).certify(tmp)

        self.assertEqual(package.final_certification_result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(package.closure_status, "WITHHELD")
        self.assertIn(
            "manifest artifact invalid: src/argos/risk/nonexistent_m4_candidate_dependency.py",
            package.unresolved_findings,
        )


if __name__ == "__main__":
    unittest.main()
