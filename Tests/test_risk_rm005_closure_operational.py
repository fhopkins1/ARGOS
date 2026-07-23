from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskRm005ClosureOperationalSupport  # noqa: E402


class RiskRm005ClosureOperationalTests(unittest.TestCase):
    def test_closure_package_covers_orders_sixteen_through_twenty(self) -> None:
        package = RiskRm005ClosureOperationalSupport().build_operational_package(REPOSITORY_ROOT)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-005-016",
                "RISK-RM-005-017",
                "RISK-RM-005-018",
                "RISK-RM-005-019",
                "RISK-RM-005-020",
            ),
        )
        self.assertEqual(package.certification_package.package_status, EnterpriseCertificationDecision.PASS)
        self.assertEqual(len(package.traceability_matrix), 5)
        self.assertEqual(len(package.procedure_execution), 17)
        self.assertEqual(len(package.persistence_records), 5)
        self.assertEqual(package.replay_recovery_record.result, EnterpriseCertificationDecision.PASS)
        self.assertTrue(package.certification_decision.closure_eligible)
        self.assertTrue(package.certification_decision.package_sealed)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_temp_candidate_produces_candidate_bound_decision_and_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "argos" / "risk").mkdir(parents=True)
            (root / "Tests").mkdir()
            (root / "Documentation").mkdir()
            (root / "src" / "argos" / "risk" / "candidate_surface.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "Tests" / "test_risk_candidate_operational.py").write_text("def test_surface():\n    assert True\n", encoding="utf-8")
            (root / "Documentation" / "RISK-RM-005-EVIDENCE.md").write_text("evidence\n", encoding="utf-8")
            package = RiskRm005ClosureOperationalSupport().build_operational_package(root)

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(package.certification_decision.candidate_digest, package.certification_package.candidate_digest)
        self.assertTrue(package.certification_decision.archive_identifier.startswith("RISK-RM005-ARCHIVE-"))
        self.assertEqual(package.certification_package.immutable_commit_identifier, "UNVERSIONED-CANDIDATE")

    def test_certification_package_fails_closed_when_mandatory_artifact_is_omitted(self) -> None:
        support = RiskRm005ClosureOperationalSupport()
        registry_package = support.build_operational_package(REPOSITORY_ROOT).registry_package
        package_record = support.assemble_certification_package(
            registry_package,
            REPOSITORY_ROOT,
            omitted_artifacts=("Traceability Matrix",),
        )

        self.assertEqual(package_record.package_status, EnterpriseCertificationDecision.FAIL)
        self.assertIn("mandatory certification artifact omitted: Traceability Matrix", package_record.findings)

    def test_traceability_fails_closed_when_requirement_is_missing(self) -> None:
        support = RiskRm005ClosureOperationalSupport()
        package = support.build_operational_package(REPOSITORY_ROOT)
        traceability = support.generate_traceability_matrix(
            package.registry_package,
            package.certification_package,
            omitted_requirements=("RISK-RM-005-019",),
        )

        self.assertTrue(any(record.result == EnterpriseCertificationDecision.FAIL for record in traceability))
        self.assertIn("RISK-RM-005-019", traceability[-1].findings[0])

    def test_procedure_replay_and_decision_fail_closed_on_prerequisite_failure(self) -> None:
        support = RiskRm005ClosureOperationalSupport()
        package = support.build_operational_package(REPOSITORY_ROOT)
        procedure = support.execute_certification_procedure(
            package.registry_package,
            package.certification_package,
            package.traceability_matrix,
            force_stage_failure="Registry Validation",
        )
        replay = support.verify_replay_and_recovery(
            package.registry_package,
            package.certification_package,
            package.persistence_records,
            replay_digest_override="different",
        )
        decision = support.generate_certification_decision(
            package.registry_package,
            package.certification_package,
            package.traceability_matrix,
            procedure,
            package.persistence_records,
            replay,
        )

        self.assertTrue(any(record.result == EnterpriseCertificationDecision.FAIL for record in procedure))
        self.assertEqual(replay.result, EnterpriseCertificationDecision.FAIL)
        self.assertEqual(decision.decision, EnterpriseCertificationDecision.FAIL)
        self.assertFalse(decision.closure_eligible)


if __name__ == "__main__":
    unittest.main()
