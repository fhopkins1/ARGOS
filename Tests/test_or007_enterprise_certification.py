import unittest
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import CertificationLevel, EnterpriseCertificationHarness, ReadinessResult  # noqa: E402


class OR007EnterpriseCertificationTests(unittest.TestCase):
    def test_campaign_returns_not_certified_until_full_suite_and_long_duration_are_green(self) -> None:
        result = EnterpriseCertificationHarness(REPOSITORY_ROOT).run_campaign(cycles=2)

        self.assertEqual(CertificationLevel.NOT_CERTIFIED, result.verdict)
        self.assertEqual("NOT CERTIFIED", result.continuous_paper_trading_verdict)
        self.assertTrue(result.evidence["readOnlyDigestStable"])
        self.assertTrue(result.evidence["recoveryAudit"]["paper_operation_allowed"])
        self.assertFalse(result.evidence["liveTradingEnabled"])
        self.assertFalse(result.git_snapshot_required)
        self.assertTrue(any(finding.finding_id == "OR007-FIND-FULL-SUITE" for finding in result.findings))

    def test_synthetic_truth_audit_classifies_remaining_proof_and_synthetic_surfaces(self) -> None:
        findings = EnterpriseCertificationHarness(REPOSITORY_ROOT).synthetic_truth_audit()
        evidence = "\n".join(match for finding in findings for match in finding.evidence)

        self.assertIn("runtime.py", evidence)
        self.assertIn("market_data_provider.py", evidence)
        self.assertTrue(any(finding.classification == "Quarantined proof compatibility" for finding in findings))
        self.assertTrue(any(finding.classification == "Accepted test/paper fallback requiring operator labeling" for finding in findings))

    def test_scorecard_marks_commander_and_long_duration_not_certified(self) -> None:
        result = EnterpriseCertificationHarness(REPOSITORY_ROOT).run_campaign(cycles=1)
        matrix = {record.subsystem: record.certification_level for record in result.certification_matrix}
        readiness = {record.category: record.result for record in result.readiness_matrix}

        self.assertEqual(CertificationLevel.NOT_CERTIFIED, matrix["Commander"])
        self.assertEqual(CertificationLevel.NOT_CERTIFIED, matrix["Replay/Long Duration"])
        self.assertEqual(ReadinessResult.FAIL, readiness["long-duration operation"])
        self.assertEqual(ReadinessResult.FAIL, readiness["synthetic truth removal"])


if __name__ == "__main__":
    unittest.main()
