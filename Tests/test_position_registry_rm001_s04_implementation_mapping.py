from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S04_IMPLEMENTATION_MAPPING"


class PositionRegistryRM001S04ImplementationMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_s04_implementation_mapping.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_b04_001_inventory_has_identity_classification_and_dependency_evidence(self) -> None:
        inventory = json.loads((EVIDENCE_ROOT / "B04-001_implementation_inventory.json").read_text(encoding="utf-8"))
        deficiencies = json.loads((EVIDENCE_ROOT / "B04-001_remaining_implementation_discovery_deficiency_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(inventory), 10)
        self.assertEqual(len({item["implementation_id"] for item in inventory}), len(inventory))
        self.assertTrue(all(item["implementation_classification"] for item in inventory))
        self.assertTrue(all(item["objective_dependency_evidence"] for item in inventory))
        self.assertEqual(deficiencies, [])

    def test_b04_001_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B04-001_authoritative_implementation_inventory.json",
            "B04-001_implementation_identity_registry.json",
            "B04-001_implementation_participation_registry.json",
            "B04-001_implementation_classification_registry.json",
            "B04-001_implementation_exclusion_registry.json",
            "B04-001_implementation_dependency_graph.json",
            "B04-001_dependency_direction_registry.json",
            "B04-001_dependency_justification_registry.json",
            "B04-001_constitutional_to_implementation_matrix.json",
            "B04-001_implementation_to_constitutional_matrix.json",
            "B04-001_implementation_authority_registry.json",
            "B04-001_implementation_obligation_registry.json",
            "B04-001_orphan_implementation_registry.json",
            "B04-001_orphan_constitutional_requirement_registry.json",
            "B04-001_duplicate_participation_registry.json",
            "B04-001_implementation_completeness_assessment.json",
            "B04-001_dependency_completeness_assessment.json",
            "B04-001_unresolved_implementation_findings_registry.json",
            "B04-001_dependency_derived_implementation_inventory_report.json",
            "B04-001_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

    def test_b04_001_dependency_graph_and_matrices_are_complete(self) -> None:
        inventory = json.loads((EVIDENCE_ROOT / "B04-001_authoritative_implementation_inventory.json").read_text(encoding="utf-8"))
        graph = json.loads((EVIDENCE_ROOT / "B04-001_implementation_dependency_graph.json").read_text(encoding="utf-8"))
        directions = json.loads((EVIDENCE_ROOT / "B04-001_dependency_direction_registry.json").read_text(encoding="utf-8"))
        justifications = json.loads((EVIDENCE_ROOT / "B04-001_dependency_justification_registry.json").read_text(encoding="utf-8"))
        c2i = json.loads((EVIDENCE_ROOT / "B04-001_constitutional_to_implementation_matrix.json").read_text(encoding="utf-8"))
        i2c = json.loads((EVIDENCE_ROOT / "B04-001_implementation_to_constitutional_matrix.json").read_text(encoding="utf-8"))
        self.assertEqual(len(graph["nodes"]), len(inventory))
        self.assertEqual(len(directions), len(graph["relationships"]))
        self.assertTrue(all(item["deterministic_direction"] for item in directions))
        self.assertTrue(all(item["dependency_justification"] for item in justifications))
        self.assertTrue(c2i)
        self.assertEqual(len(i2c), len(inventory))
        self.assertTrue(all(item["mapping_disposition"] == "MAPPED_NOT_VERIFIED" for item in i2c))

    def test_b04_001_completeness_and_doctrine_only_constraints(self) -> None:
        impl = json.loads((EVIDENCE_ROOT / "B04-001_implementation_completeness_assessment.json").read_text(encoding="utf-8"))
        dep = json.loads((EVIDENCE_ROOT / "B04-001_dependency_completeness_assessment.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B04-001_dependency_derived_implementation_inventory_report.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B04-001_unresolved_implementation_findings_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(impl["complete"])
        self.assertEqual(impl["implementation_gaps"], [])
        self.assertEqual(impl["mapping_gaps"], [])
        self.assertTrue(dep["complete"])
        self.assertEqual(dep["circular_dependencies"], [])
        self.assertEqual(dep["conflicting_dependency_direction"], [])
        self.assertEqual(unresolved, [])
        self.assertTrue(report["objective_dependency_discovery"])
        self.assertFalse(report["pattern_derived_inventory"])
        self.assertFalse(report["filename_derived_inventory"])
        self.assertFalse(report["manual_inventory"])
        self.assertFalse(report["documentation_reference_inventory"])
        self.assertFalse(report["historical_execution_list_inventory"])
        self.assertFalse(report["behavioral_correctness_evaluated"])
        self.assertFalse(report["implementation_modified"])
        self.assertFalse(report["behavioral_verification_executed"])
        self.assertFalse(report["implementation_proof_generated"])
        self.assertFalse(report["certification_activity_executed"])

    def test_b04_002_maps_every_requirement_without_gaps(self) -> None:
        requirements = json.loads((REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S03_INTERFACE_EVIDENCE_TRACEABILITY" / "B03-004_canonical_constitutional_requirement_registry.json").read_text(encoding="utf-8"))
        matrix = json.loads((EVIDENCE_ROOT / "B04-002_constitutional_to_implementation_matrix.json").read_text(encoding="utf-8"))
        gaps = json.loads((EVIDENCE_ROOT / "B04-002_implementation_gap_registry.json").read_text(encoding="utf-8"))
        self.assertEqual({item["requirement_id"] for item in requirements}, {item["requirement_id"] for item in matrix})
        self.assertTrue(all(item["implementation_artifacts"] for item in matrix))
        self.assertEqual(gaps, [])

    def test_b04_003_verification_population_is_classified_but_not_executed(self) -> None:
        verifiers = json.loads((EVIDENCE_ROOT / "B04-003_verifier_inventory.json").read_text(encoding="utf-8"))
        modes = json.loads((EVIDENCE_ROOT / "B04-003_verification_mode_registry.json").read_text(encoding="utf-8"))
        integrity = json.loads((EVIDENCE_ROOT / "B04-003_verification_integrity_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(verifiers), 4)
        self.assertEqual(len(verifiers), len(modes))
        self.assertEqual(integrity["orphan_verifiers"], [])
        self.assertEqual(integrity["evidence_producers_lacking_constitutional_authority"], [])

    def test_completion_report_preserves_no_behavior_or_certification_claims(self) -> None:
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(completion["status"], "COMPLETE")
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_correctness_evaluated"])
        self.assertFalse(completion["proof_objects_generated"])
        self.assertFalse(completion["certification_readiness_issued"])


if __name__ == "__main__":
    unittest.main()
