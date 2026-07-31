from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_RM001_CONSTITUTIONAL_BASELINE"


class PerformanceTruthRM001ConstitutionalBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "performance_truth_rm001_constitutional_baseline.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_required_deliverables_exist(self) -> None:
        required = [
            "source_order_registry.json",
            "program_charter.json",
            "office_governance_authority_registry.json",
            "canonical_object_registry.json",
            "object_ownership_registry.json",
            "object_lifecycle_registry.json",
            "calculation_governance_registry.json",
            "office_interface_registry.json",
            "evidence_requirement_registry.json",
            "traceability_graph.json",
            "failure_behavior_registry.json",
            "constitutional_requirement_registry.json",
            "constitutional_completeness_review.json",
            "series_completion_report.json",
            "completion_report.json",
            "manifest.json",
        ]
        for filename in required:
            self.assertTrue((EVIDENCE_ROOT / filename).exists(), filename)

    def test_source_orders_are_preserved_and_duplicate_009_is_reconciled(self) -> None:
        sources = json.loads((EVIDENCE_ROOT / "source_order_registry.json").read_text(encoding="utf-8"))
        canonical_orders = {row["canonical_order_id"] for row in sources}
        self.assertEqual(len(canonical_orders), 13)
        duplicates = [row for row in sources if row["duplicate_semantic_group"] == "PERFORMANCE-TRUTH-RM-001-009"]
        self.assertEqual(len(duplicates), 2)
        findings = json.loads((EVIDENCE_ROOT / "constitutional_findings_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(findings[0]["disposition"], "DOCUMENTED_AND_RECONCILED")
        self.assertFalse(findings[0]["blocking"])

    def test_objects_have_single_owner_custody_lifecycle_and_traceability(self) -> None:
        objects = json.loads((EVIDENCE_ROOT / "canonical_object_registry.json").read_text(encoding="utf-8"))
        ownership = json.loads((EVIDENCE_ROOT / "object_ownership_registry.json").read_text(encoding="utf-8"))
        custody = json.loads((EVIDENCE_ROOT / "object_custody_registry.json").read_text(encoding="utf-8"))
        lifecycles = json.loads((EVIDENCE_ROOT / "object_lifecycle_registry.json").read_text(encoding="utf-8"))
        traceability = json.loads((EVIDENCE_ROOT / "traceability_requirement_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(objects), 12)
        self.assertEqual({row["constitutional_owner"] for row in ownership}, {"Performance Truth Office"})
        self.assertTrue(all(not row["shared_ownership_permitted"] for row in ownership))
        self.assertEqual(len(custody), len(objects))
        self.assertTrue(all("published" in row["terminal_states"] for row in lifecycles))
        object_names = {row["object_name"] for row in objects}
        trace_subjects = {row["subject"] for row in traceability}
        self.assertTrue(object_names.issubset(trace_subjects))

    def test_authority_is_downstream_and_fail_closed(self) -> None:
        prohibited = json.loads((EVIDENCE_ROOT / "prohibited_authority_registry.json").read_text(encoding="utf-8"))
        failures = json.loads((EVIDENCE_ROOT / "failure_behavior_registry.json").read_text(encoding="utf-8"))
        prohibited_actions = {row["prohibited_authority"] for row in prohibited}
        self.assertIn("modify closed position truth", prohibited_actions)
        self.assertIn("fabricate missing source truth", prohibited_actions)
        self.assertTrue(all(row["disposition"] == "FAIL_CLOSED" for row in failures))
        self.assertTrue(all(not row["publication_allowed"] for row in failures))

    def test_requirements_are_traceable_and_completion_is_constitutional_only(self) -> None:
        requirements = json.loads((EVIDENCE_ROOT / "constitutional_requirement_registry.json").read_text(encoding="utf-8"))
        matrix = json.loads((EVIDENCE_ROOT / "requirement_traceability_matrix.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        review = json.loads((EVIDENCE_ROOT / "constitutional_completeness_review.json").read_text(encoding="utf-8"))
        self.assertEqual(len(requirements), len(matrix))
        self.assertTrue(all(row["evidence_required"] for row in matrix))
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_performed"])
        self.assertFalse(completion["certification_activity_executed"])
        self.assertEqual(review["constitutional_status"], "COMPLETE")
        self.assertTrue(review["ready_for_implementation_certification"])


if __name__ == "__main__":
    unittest.main()
