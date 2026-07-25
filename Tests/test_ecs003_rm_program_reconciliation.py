import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "ECS003_RM_PROGRAM_RECONCILIATION"


class ECS003RMProgramReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        completed = subprocess.run(
            [sys.executable, "Scripts/ecs003_rm_program_reconciliation.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=120,
        )
        cls.stdout = completed.stdout
        cls.stderr = completed.stderr
        cls.returncode = completed.returncode

    def _read_json(self, name: str):
        return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))

    def test_generator_completes(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_all_supplied_source_orders_are_preserved(self):
        source_registry = self._read_json("ecs003_rm_program_source_order_registry.json")
        self.assertEqual(len(source_registry), 7)
        for record in source_registry:
            self.assertEqual(record["disposition"], "SOURCE_ORDER_PRESERVED")
            self.assertTrue((REPOSITORY_ROOT / record["committed_copy"]).exists())
            self.assertEqual(len(record["sha256"]), 64)

    def test_program_readiness_is_audit_ready(self):
        readiness = self._read_json("ecs003_rm_readiness_assessment.json")
        self.assertEqual(readiness["status"], "COMPLETE")
        self.assertEqual(readiness["readiness"], "READY_FOR_ECS003_REMEDIATION_AUDIT")
        self.assertTrue(all(readiness["checks"].values()))

    def test_completion_report_has_traceable_terminal_programs(self):
        program_registry = self._read_json("ecs003_rm_program_order_registry.json")
        traceability = self._read_json("ecs003_rm_cross_program_traceability_registry.json")
        self.assertEqual(len(program_registry), 7)
        self.assertEqual(len(traceability), 7)
        self.assertTrue(all(record["terminal_disposition"] == "COMPLETE" for record in program_registry))
        self.assertEqual(
            {record["order_id"] for record in program_registry},
            {
                "ECS-003-RM-B01",
                "ECS-003-RM-B02",
                "ECS-003-RM-B04",
                "ECS-003-RM-B05",
                "ECS-003-RM-B06",
                "ECS-003-RM-B08",
                "ECS-003-RM-B09",
            },
        )

    def test_omitted_series_are_explicitly_dispositioned(self):
        omitted = self._read_json("ecs003_rm_omitted_series_disposition_registry.json")
        self.assertIn("ECS-003-RM-B03", omitted)
        self.assertIn("ECS-003-RM-B07", omitted)
        self.assertNotIn("PASS", omitted["ECS-003-RM-B03"])


if __name__ == "__main__":
    unittest.main()
