from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "MONITORING_RM002_B06_DEPENDENCY_DISCOVERY_RECONCILIATION"

from Scripts.monitoring_rm002_b06_dependency_discovery_reconciliation import generate  # noqa: E402


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class MonitoringRm002B06DependencyDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        generate(OUTPUT_DIR)

    def test_completion_is_ready_and_reproducible(self) -> None:
        completion = read_json(OUTPUT_DIR / "completion_report.json")
        determinism = read_json(OUTPUT_DIR / "B06-004_repository_wide_discovery_determinism_report.json")
        reproducibility = read_json(OUTPUT_DIR / "B06-004_independent_discovery_reproducibility_report.json")

        self.assertEqual(completion["status"], "COMPLETE")
        self.assertEqual(completion["behavioral_readiness"], "READY_FOR_PROOF_REGENERATION")
        self.assertTrue(completion["deterministic_discovery"])
        self.assertTrue(completion["independently_reproducible"])
        self.assertTrue(determinism["deterministic"])
        self.assertTrue(reproducibility["reproducible"])
        self.assertFalse(reproducibility["manual_inventory_authoritative"])

    def test_verifiers_have_dependency_lineage_and_requirements(self) -> None:
        verifiers = read_json(OUTPUT_DIR / "B06-001_dependency_derived_verifier_registry.json")

        self.assertEqual(len(verifiers), 25)
        for verifier in verifiers:
            self.assertEqual(verifier["classification"], "PRIMARY_BEHAVIORAL_VERIFIER")
            self.assertTrue(verifier["governing_constitutional_requirement"])
            self.assertIn("src/argos/trader/trade_monitoring.py", verifier["dependency_lineage"])
            self.assertFalse(verifier["manual_inventory_authoritative"])

    def test_fixtures_and_artifacts_are_not_orphaned(self) -> None:
        fixtures = read_json(OUTPUT_DIR / "B06-002_dependency_derived_fixture_registry.json")
        orphan_verifiers = read_json(OUTPUT_DIR / "B06-004_orphan_participant_registry.json")
        included = read_json(OUTPUT_DIR / "B06-004_inclusion_reconciliation_registry.json")

        self.assertEqual(len(fixtures), 1)
        self.assertGreaterEqual(len(fixtures[0]["governing_behavioral_verifiers"]), 25)
        self.assertEqual(orphan_verifiers, [])
        self.assertTrue(any(item["artifact"] == "src/argos/trader/trade_monitoring.py" for item in included))
        self.assertTrue(any(item["artifact"] == "Tests/test_trade_monitoring_office.py" for item in included))

    def test_every_requirement_has_terminal_behavioral_disposition(self) -> None:
        coverage = read_json(OUTPUT_DIR / "B06-004_canonical_requirement_behavioral_coverage_registry.json")
        dispositions = {item["coverage_disposition"] for item in coverage}
        covered = [item for item in coverage if item["coverage_disposition"] == "COVERED"]
        not_applicable = [item for item in coverage if item["coverage_disposition"] == "NOT_APPLICABLE"]

        self.assertTrue(coverage)
        self.assertLessEqual(dispositions, {"COVERED", "PARTIALLY_COVERED", "UNCOVERED", "BLOCKED", "NOT_APPLICABLE"})
        self.assertEqual(len(covered), 25)
        self.assertTrue(not_applicable)
        for item in covered:
            self.assertTrue(item["governing_verifiers"])
            self.assertTrue(item["implementation_participants"])
            self.assertTrue(item["deterministic_execution_covered"])

    def test_generation_is_deterministic_in_alternate_output_directory(self) -> None:
        baseline = read_json(OUTPUT_DIR / "monitoring_rm002_b06_authoritative_dependency_discovery_baseline.json")
        with tempfile.TemporaryDirectory(prefix="monitoring-b06-test-") as temp_dir:
            temp_output = Path(temp_dir) / "evidence"
            generate(temp_output)
            regenerated = read_json(temp_output / "monitoring_rm002_b06_authoritative_dependency_discovery_baseline.json")

        self.assertEqual(baseline["digest"], regenerated["digest"])


if __name__ == "__main__":
    unittest.main()
