from dataclasses import asdict
from pathlib import Path
import sys
import tempfile
import unittest
import json


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.constitutional_trace_campaign import ExecutedConstitutionalTraceCampaign  # noqa: E402
from argos.control_panel.continuous_paper_endurance import ContinuousPaperEnduranceAuthority, PaperEnduranceVerdict  # noqa: E402
from argos.control_panel.financial_recovery_authority import FinancialRecoveryAuthority, RecoveredState, RecoveryVerdict  # noqa: E402
from argos.control_panel.full_position_lifecycle_runtime import execute_canonical_position_lifecycle  # noqa: E402
from argos.control_panel.independent_constitutional_certification import IndependentConstitutionalCertificationAuthority, IndependentVerdict  # noqa: E402
from argos.control_panel.production_read_surface_registry import ProductionReadSurfaceConstitutionalRegistry, ProductionReadVerdict  # noqa: E402


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


class EODMToEODRClosureTests(unittest.TestCase):
    def test_eodm_executes_full_position_lifecycle_to_closed_truth(self) -> None:
        evidence = execute_canonical_position_lifecycle()

        self.assertEqual(evidence["report"]["verdict"], "PASS")
        self.assertEqual(evidence["report"]["open_quantity_after_close"], 0.0)
        self.assertEqual(evidence["report"]["closed_truth_count"], 1)
        self.assertGreater(evidence["report"]["bridge_trace_count"], 0)

    def test_eodn_missing_close_fill_remains_unresolved_without_fabrication(self) -> None:
        lifecycle = execute_canonical_position_lifecycle()
        report = FinancialRecoveryAuthority().recover_missing_close_fill(lifecycle)

        unresolved = {domain.domain for domain in report.domains if domain.state == RecoveredState.UNRESOLVED}
        self.assertEqual(report.verdict, RecoveryVerdict.PASS)
        self.assertIn("fills", unresolved)
        self.assertFalse(report.fabricated_financial_truth)
        self.assertTrue(report.unknowns_preserved)

    def test_eodo_certifies_registered_reads_without_mutation(self) -> None:
        certification = ProductionReadSurfaceConstitutionalRegistry().certify()

        self.assertEqual(certification.verdict, ProductionReadVerdict.PASS)
        self.assertTrue(certification.duplicate_registration_rejected)
        self.assertGreater(certification.registered_surface_count, 0)
        self.assertEqual(certification.registered_surface_count, certification.certified_surface_count)

    def test_eodp_trace_campaign_executes_required_categories(self) -> None:
        campaign = ExecutedConstitutionalTraceCampaign().execute(repository_commit="TEST-COMMIT")

        categories = {trace["category"] for trace in campaign["report"]["traces"]}
        self.assertEqual(campaign["report"]["verdict"], "PASS")
        self.assertIn("Financial", categories)
        self.assertIn("Recovery", categories)
        self.assertIn("Read Surfaces", categories)
        self.assertIn("Endurance", categories)

    def test_eodq_accelerated_paper_endurance_passes_without_live_trading(self) -> None:
        certification = ContinuousPaperEnduranceAuthority().run_accelerated_certification(repository_commit="TEST-COMMIT")

        self.assertEqual(certification.verdict, PaperEnduranceVerdict.PASS)
        self.assertTrue(certification.accelerated_endurance_completed)
        self.assertFalse(certification.wall_clock_extended_run_completed)
        self.assertFalse(certification.live_trading_enabled)

    def test_eodr_independently_validates_evidence_and_reports_wall_clock_blocker(self) -> None:
        lifecycle = execute_canonical_position_lifecycle()
        recovery = FinancialRecoveryAuthority().recover_missing_close_fill(lifecycle)
        reads = ProductionReadSurfaceConstitutionalRegistry().certify()
        endurance = ContinuousPaperEnduranceAuthority().run_accelerated_certification(repository_commit="TEST-COMMIT")
        trace = ExecutedConstitutionalTraceCampaign().execute(repository_commit="TEST-COMMIT")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "eo_dm_lifecycle_closure.json", lifecycle["report"])
            write_json(root / "eo_dn_recovery_report.json", asdict(recovery))
            write_json(root / "eo_do_read_surface_certification.json", asdict(reads))
            write_json(root / "eo_dp_trace_campaign.json", trace["report"])
            write_json(root / "eo_dq_endurance_certification.json", asdict(endurance))

            report = IndependentConstitutionalCertificationAuthority().certify(root, repository_root=REPOSITORY_ROOT)

        self.assertEqual(report.verdict, IndependentVerdict.INCOMPLETE)
        self.assertTrue(any("wall-clock" in blocker for blocker in report.blocker_inventory))
        self.assertEqual(report.scorecard["validArtifactCount"], 5)


if __name__ == "__main__":
    unittest.main()
