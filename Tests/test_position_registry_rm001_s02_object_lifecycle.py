from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S02_OBJECT_LIFECYCLE"


class PositionRegistryRM001S02ObjectLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_s02_object_lifecycle.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_b02_001_objects_are_complete(self) -> None:
        objects = json.loads((EVIDENCE_ROOT / "B02-001_canonical_object_registry.json").read_text(encoding="utf-8"))
        conflicts = json.loads((EVIDENCE_ROOT / "B02-001_object_conflict_registry.json").read_text(encoding="utf-8"))
        expected = {
            "position_identity",
            "position_record",
            "position_state",
            "position_status",
            "position_lifecycle_state",
            "position_quantity",
            "open_quantity",
            "closed_quantity",
            "realized_quantity",
            "unrealized_quantity",
            "position_direction",
            "average_cost_basis",
            "entry_cost_basis",
            "cost_basis_history",
            "position_valuation_reference",
            "instrument_identity",
            "account_identity",
            "broker_position_identity",
            "broker_execution_reference",
            "fill_reference",
            "workflow_identity",
            "authorization_reference",
            "risk_reference",
            "monitoring_reference",
            "exit_reference",
            "closed_position_reference",
            "performance_reference",
            "reconciliation_case",
            "correction_record",
            "supersession_record",
            "historical_position_record",
            "archival_record",
        }
        self.assertEqual({item["canonical_object_name"] for item in objects}, expected)
        self.assertTrue(all(item["object_id"] for item in objects))
        self.assertTrue(all(item["constitutional_owner"] for item in objects))
        self.assertTrue(all(item["governing_authority"] == "POSITION-REGISTRY-RM-001-S02-B02-001" for item in objects))
        self.assertTrue(all(item["reconciliation_authority"] == "Position Registry" for item in objects))
        self.assertEqual(conflicts, [])

    def test_b02_001_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B02-001_canonical_object_registry.json",
            "B02-001_canonical_object_identity_registry.json",
            "B02-001_constitutional_object_authority_registry.json",
            "B02-001_constitutional_object_ownership_registry.json",
            "B02-001_constitutional_object_custody_registry.json",
            "B02-001_object_relationship_registry.json",
            "B02-001_object_dependency_registry.json",
            "B02-001_object_lifecycle_participation_registry.json",
            "B02-001_object_evidence_registry.json",
            "B02-001_object_invariant_registry.json",
            "B02-001_object_completeness_assessment.json",
            "B02-001_duplicate_object_registry.json",
            "B02-001_orphan_object_registry.json",
            "B02-001_unresolved_constitutional_object_findings_registry.json",
            "B02-001_canonical_object_constitution_report.json",
            "B02-001_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

        completeness = json.loads((EVIDENCE_ROOT / "B02-001_object_completeness_assessment.json").read_text(encoding="utf-8"))
        duplicates = json.loads((EVIDENCE_ROOT / "B02-001_duplicate_object_registry.json").read_text(encoding="utf-8"))
        orphans = json.loads((EVIDENCE_ROOT / "B02-001_orphan_object_registry.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B02-001_unresolved_constitutional_object_findings_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(completeness["complete"])
        self.assertEqual(duplicates, [])
        self.assertEqual(orphans, [])
        self.assertEqual(unresolved, [])

    def test_b02_001_invariants_and_dependencies_are_deterministic(self) -> None:
        dependencies = json.loads((EVIDENCE_ROOT / "B02-001_object_dependency_registry.json").read_text(encoding="utf-8"))
        invariants = json.loads((EVIDENCE_ROOT / "B02-001_object_invariant_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(dependencies)
        self.assertTrue(all(item["deterministic_direction"] for item in dependencies))
        self.assertTrue(all(item["invariant_violations"] == [] for item in invariants))
        self.assertTrue(all(item["ambiguous_invariants"] == [] for item in invariants))
        self.assertTrue(all(item["conflicting_invariants"] == [] for item in invariants))

    def test_b02_002_quantity_cost_and_temporal_rules_exist(self) -> None:
        quantity = json.loads((EVIDENCE_ROOT / "B02-002_quantity_doctrine_registry.json").read_text(encoding="utf-8"))
        cost = json.loads((EVIDENCE_ROOT / "B02-002_cost_basis_doctrine_registry.json").read_text(encoding="utf-8"))
        temporal = json.loads((EVIDENCE_ROOT / "B02-002_temporal_doctrine_registry.json").read_text(encoding="utf-8"))
        ambiguity = json.loads((EVIDENCE_ROOT / "B02-002_lifecycle_ambiguity_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(quantity)
        self.assertTrue(cost)
        self.assertTrue(temporal)
        self.assertEqual(ambiguity, [])

    def test_b02_003_historical_integrity_prohibits_fabrication(self) -> None:
        replay = json.loads((EVIDENCE_ROOT / "B02-003_replay_constitution.json").read_text(encoding="utf-8"))
        supersession = json.loads((EVIDENCE_ROOT / "B02-003_supersession_constitution.json").read_text(encoding="utf-8"))
        self.assertTrue(replay["identity_preservation"])
        self.assertTrue(replay["fabrication_prohibited"])
        self.assertTrue(supersession["superseded_object_preserved"])

    def test_b02_004_baseline_has_no_unresolved_findings_or_certification(self) -> None:
        baseline = json.loads((EVIDENCE_ROOT / "B02-004_authoritative_position_registry_object_and_lifecycle_baseline.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(baseline["unresolved_constitutional_finding_registry"], [])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_certification_issued"])


if __name__ == "__main__":
    unittest.main()
