from __future__ import annotations

import json
import subprocess
import sys
import unittest

from Scripts import historian_rm004_reproducibility_readiness as readiness


class HistorianRM004ReproducibilityReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        readiness.generate()

    def _load(self, name: str):
        return json.loads((readiness.OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_all_rm004_orders_have_terminal_pass_disposition(self) -> None:
        registry = self._load("rm004_order_completion_registry.json")
        self.assertEqual(12, len(registry))
        self.assertTrue(all(item["disposition"] == "PASS" for item in registry))

    def test_ecs004_readiness_is_authorized_without_behavior_change(self) -> None:
        report = self._load("ecs004_readiness_assessment_report.json")
        self.assertTrue(report["ecs004_ready"])
        self.assertEqual("READY", report["readiness_decision"])
        self.assertFalse(report["constitutional_architecture_modified"])
        self.assertFalse(report["historian_behavior_modified"])
        self.assertFalse(report["certification_criteria_modified"])

    def test_clean_room_auditor_entrypoint_is_executable(self) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/historian_rm004_clean_room_auditor.py"],
            text=True,
            capture_output=True,
            timeout=60,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual("PASS", output["terminal_status"])
        self.assertEqual("ECS004_READY", output["certification_decision"])

    def test_mutations_and_reproductions_are_objectively_validated(self) -> None:
        mutation = self._load("mutation_detection_report.json")
        self.assertGreaterEqual(mutation["mutation_count"], 10)
        self.assertEqual(mutation["mutation_count"], mutation["detected_count"])
        reproduction = self._load("independent_reproduction_report.json")
        self.assertEqual(3, len(reproduction["reproductions"]))
        self.assertEqual("PASS", reproduction["independent_reproduction_status"])

    def test_evidence_package_manifest_is_distinct_from_repository_package(self) -> None:
        manifest = self._load("evidence_package_manifest.json")
        self.assertEqual("HISTORIAN-RM-004-EVIDENCE-PACKAGE", manifest["package_id"])
        self.assertGreaterEqual(len(manifest["deliverables"]), 10)


if __name__ == "__main__":
    unittest.main()
