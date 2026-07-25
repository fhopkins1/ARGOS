from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S05_BEHAVIORAL_VERIFICATION"


class PositionRegistryRM001S05BehavioralVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_s05_behavioral_verification.py"), "--b05-001"],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_b05_001_population_is_frozen_and_bounded(self) -> None:
        obligations = json.loads((EVIDENCE_ROOT / "B05-001_behavioral_obligation_registry.json").read_text(encoding="utf-8"))
        gaps = json.loads((EVIDENCE_ROOT / "B05-001_verification_gap_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(obligations), 30)
        self.assertEqual({item["bounded_execution_group"] for item in obligations}, {"B05-002", "B05-003"})
        self.assertTrue(all(item["planning_disposition"] == "FROZEN_NOT_EXECUTED" for item in obligations))
        self.assertEqual(gaps, [])

    def test_b05_001_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B05-001_behavioral_obligation_registry.json",
            "B05-001_behavioral_obligation_identity_registry.json",
            "B05-001_behavioral_obligation_classification_registry.json",
            "B05-001_behavioral_obligation_coverage_registry.json",
            "B05-001_verifier_population_registry.json",
            "B05-001_verifier_identity_registry.json",
            "B05-001_verifier_classification_registry.json",
            "B05-001_behavioral_verifier_mapping_registry.json",
            "B05-001_verification_mode_registry.json",
            "B05-001_fixture_planning_registry.json",
            "B05-001_runtime_planning_registry.json",
            "B05-001_execution_planning_registry.json",
            "B05-001_behavioral_coverage_assessment.json",
            "B05-001_verification_completeness_assessment.json",
            "B05-001_unresolved_behavioral_findings_registry.json",
            "B05-001_behavioral_obligation_and_verifier_population_report.json",
            "B05-001_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

    def test_b05_001_every_obligation_has_identity_classification_verifier_fixture_and_runtime_planning(self) -> None:
        obligations = json.loads((EVIDENCE_ROOT / "B05-001_behavioral_obligation_registry.json").read_text(encoding="utf-8"))
        identities = json.loads((EVIDENCE_ROOT / "B05-001_behavioral_obligation_identity_registry.json").read_text(encoding="utf-8"))
        classifications = json.loads((EVIDENCE_ROOT / "B05-001_behavioral_obligation_classification_registry.json").read_text(encoding="utf-8"))
        verifier_map = json.loads((EVIDENCE_ROOT / "B05-001_behavioral_verifier_mapping_registry.json").read_text(encoding="utf-8"))
        fixture = json.loads((EVIDENCE_ROOT / "B05-001_fixture_planning_registry.json").read_text(encoding="utf-8"))
        runtime = json.loads((EVIDENCE_ROOT / "B05-001_runtime_planning_registry.json").read_text(encoding="utf-8"))
        execution = json.loads((EVIDENCE_ROOT / "B05-001_execution_planning_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(obligations), len(identities))
        self.assertEqual(len(obligations), len(classifications))
        self.assertEqual(len(obligations), len(verifier_map))
        self.assertEqual(len(obligations), len(fixture))
        self.assertEqual(len(obligations), len(runtime))
        self.assertEqual(len(obligations), len(execution))
        self.assertTrue(all(item["canonical_behavioral_identity"] for item in identities))
        self.assertTrue(all(item["classification_is_exactly_one"] for item in classifications))
        self.assertTrue(all(item["governing_verifiers"] for item in verifier_map))
        self.assertTrue(all(item["fixture_planning_disposition"] == "PLANNED_NOT_EXECUTED" for item in fixture))
        self.assertTrue(all(item["runtime_planning_disposition"] == "PLANNED_NOT_EXECUTED" for item in runtime))
        self.assertTrue(all(item["execution_status"] == "PLANNED_NOT_EXECUTED" for item in execution))

    def test_b05_001_verifiers_have_behavioral_authority_and_no_orphans(self) -> None:
        verifiers = json.loads((EVIDENCE_ROOT / "B05-001_verifier_population_registry.json").read_text(encoding="utf-8"))
        identities = json.loads((EVIDENCE_ROOT / "B05-001_verifier_identity_registry.json").read_text(encoding="utf-8"))
        classifications = json.loads((EVIDENCE_ROOT / "B05-001_verifier_classification_registry.json").read_text(encoding="utf-8"))
        completeness = json.loads((EVIDENCE_ROOT / "B05-001_verification_completeness_assessment.json").read_text(encoding="utf-8"))
        self.assertTrue(verifiers)
        self.assertEqual(len(verifiers), len(identities))
        self.assertEqual(len(verifiers), len(classifications))
        self.assertTrue(all(item["behavioral_authority"] == "POSITION-REGISTRY-RM-001-S05-B05-001" for item in verifiers))
        self.assertTrue(all(item["governing_behavioral_obligations"] for item in verifiers))
        self.assertTrue(all(item["classification_is_exactly_one"] for item in classifications))
        self.assertTrue(completeness["complete"])
        self.assertEqual(completeness["orphan_behavioral_obligations"], [])
        self.assertEqual(completeness["orphan_verifiers"], [])

    def test_b05_001_coverage_and_report_are_complete_and_non_executing(self) -> None:
        coverage = json.loads((EVIDENCE_ROOT / "B05-001_behavioral_coverage_assessment.json").read_text(encoding="utf-8"))
        completeness = json.loads((EVIDENCE_ROOT / "B05-001_verification_completeness_assessment.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B05-001_unresolved_behavioral_findings_registry.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B05-001_behavioral_obligation_and_verifier_population_report.json").read_text(encoding="utf-8"))
        self.assertTrue(coverage["complete"])
        self.assertTrue(all(value == "COVERED_NOT_EXECUTED" for value in coverage["domains"].values()))
        self.assertEqual(coverage["uncovered_behavioral_obligations"], [])
        self.assertEqual(coverage["duplicate_behavioral_coverage"], [])
        self.assertEqual(coverage["conflicting_behavioral_coverage"], [])
        self.assertEqual(coverage["unresolved_behavioral_ambiguity"], [])
        self.assertEqual(completeness["behavioral_obligation_gaps"], [])
        self.assertEqual(completeness["verifier_gaps"], [])
        self.assertEqual(completeness["verification_planning_gaps"], [])
        self.assertEqual(completeness["execution_planning_gaps"], [])
        self.assertEqual(completeness["fixture_gaps"], [])
        self.assertEqual(completeness["runtime_gaps"], [])
        self.assertEqual(completeness["unresolved_constitutional_ambiguity"], [])
        self.assertEqual(unresolved, [])
        self.assertFalse(report["implementation_behavior_origin"])
        self.assertFalse(report["filename_origin"])
        self.assertFalse(report["test_name_origin"])
        self.assertFalse(report["documentation_origin"])
        self.assertFalse(report["historical_execution_batch_origin"])
        self.assertFalse(report["developer_assumption_origin"])
        self.assertFalse(report["behavioral_verification_executed"])
        self.assertFalse(report["implementation_modified"])
        self.assertFalse(report["implementation_proof_generated"])
        self.assertFalse(report["certification_activity_executed"])

    def test_completion_report_is_honest_and_non_certifying(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertFalse(completion["bounded_population_executed"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["repository_wide_verification_executed"])
        self.assertFalse(completion["certification_conclusion_issued"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["certification_activity_executed"])


if __name__ == "__main__":
    unittest.main()
