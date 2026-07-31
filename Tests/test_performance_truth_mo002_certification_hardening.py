from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_MO002_CERTIFICATION_HARDENING"


class PerformanceTruthMO002CertificationHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "performance_truth_mo002_certification_hardening.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=1200,
        )

    def test_all_mo002_orders_are_preserved(self) -> None:
        sources = json.loads((EVIDENCE_ROOT / "source_order_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(sources), 13)
        self.assertTrue(all(row["source_available"] for row in sources))

    def test_coverage_and_evidence_are_complete(self) -> None:
        coverage = json.loads((EVIDENCE_ROOT / "audit_coverage_analysis.json").read_text(encoding="utf-8"))
        evidence = json.loads((EVIDENCE_ROOT / "evidence_sufficiency_audit.json").read_text(encoding="utf-8"))
        self.assertTrue(coverage)
        self.assertTrue(all(row["coverage_disposition"] == "COVERED" for row in coverage))
        self.assertTrue({"RM001", "RM002", "RM003", "MO001"}.issubset({row["package_id"] for row in evidence}))
        self.assertTrue(all(row["sufficiency"] == "SUFFICIENT" for row in evidence))

    def test_mutation_false_positive_and_false_negative_resistance(self) -> None:
        mutations = json.loads((EVIDENCE_ROOT / "audit_mutation_testing_registry.json").read_text(encoding="utf-8"))
        fp = json.loads((EVIDENCE_ROOT / "false_positive_resistance_registry.json").read_text(encoding="utf-8"))
        fn = json.loads((EVIDENCE_ROOT / "false_negative_resistance_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(all(row["observed_detection"] == "DETECTED" for row in mutations))
        self.assertTrue(all(not row["false_positive"] for row in fp))
        self.assertTrue(all(not row["false_negative"] for row in fn))

    def test_repeatability_auditor_equivalence_and_proof_sufficiency(self) -> None:
        repeatability = json.loads((EVIDENCE_ROOT / "certification_repeatability_registry.json").read_text(encoding="utf-8"))
        equivalence = json.loads((EVIDENCE_ROOT / "independent_auditor_equivalence_registry.json").read_text(encoding="utf-8"))
        proof = json.loads((EVIDENCE_ROOT / "constitutional_proof_sufficiency_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(all(row["disposition"] == "PASS" for row in repeatability))
        self.assertTrue(all(row["equivalent_to_primary"] for row in equivalence))
        self.assertTrue(all(row["disposition"] == "PASS" and not row["circular_reasoning_detected"] for row in proof))

    def test_closure_establishes_hardened_certification_baseline(self) -> None:
        closure = json.loads((EVIDENCE_ROOT / "certification_hardening_closure.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(closure["hardened_certification_baseline_status"], "ESTABLISHED")
        self.assertEqual(completion["hardened_certification_baseline_status"], "ESTABLISHED")
        self.assertEqual(completion["status"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
