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

    def test_b04_002_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B04-002_constitutional_to_implementation_matrix.json",
            "B04-002_implementation_to_constitutional_matrix.json",
            "B04-002_implementation_obligation_registry.json",
            "B04-002_implementation_obligation_identity_registry.json",
            "B04-002_implementation_obligation_classification_registry.json",
            "B04-002_implementation_dependency_registry.json",
            "B04-002_implementation_dependency_graph.json",
            "B04-002_implementation_dependency_justification_registry.json",
            "B04-002_implementation_verification_registry.json",
            "B04-002_implementation_verifier_registry.json",
            "B04-002_implementation_fixture_registry.json",
            "B04-002_implementation_evidence_obligation_registry.json",
            "B04-002_implementation_coverage_assessment.json",
            "B04-002_constitutional_implementation_completeness_assessment.json",
            "B04-002_unresolved_implementation_findings_registry.json",
            "B04-002_implementation_obligation_and_dependency_mapping_report.json",
            "B04-002_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

    def test_b04_002_obligations_have_authority_ownership_verification_and_evidence(self) -> None:
        obligations = json.loads((EVIDENCE_ROOT / "B04-002_implementation_obligation_registry.json").read_text(encoding="utf-8"))
        classifications = json.loads((EVIDENCE_ROOT / "B04-002_implementation_obligation_classification_registry.json").read_text(encoding="utf-8"))
        verification = json.loads((EVIDENCE_ROOT / "B04-002_implementation_verification_registry.json").read_text(encoding="utf-8"))
        evidence = json.loads((EVIDENCE_ROOT / "B04-002_implementation_evidence_obligation_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(obligations)
        self.assertEqual(len(obligations), len(classifications))
        self.assertEqual(len(obligations), len(verification))
        self.assertEqual(len(obligations), len(evidence))
        self.assertTrue(all(item["governing_constitutional_authority"] for item in obligations))
        self.assertTrue(all(item["governing_implementation_owner"] == "Position Registry" for item in obligations))
        self.assertTrue(all(item["participating_implementation_artifacts"] for item in obligations))
        self.assertTrue(all(item["verification_planning_status"] == "PLANNED_NOT_EXECUTED" for item in verification))
        self.assertTrue(all(item["evidence_generation_status"] == "PLANNED_NOT_EXECUTED" for item in evidence))

    def test_b04_002_dependency_and_completeness_are_deterministic_and_gap_free(self) -> None:
        dependencies = json.loads((EVIDENCE_ROOT / "B04-002_implementation_dependency_registry.json").read_text(encoding="utf-8"))
        coverage = json.loads((EVIDENCE_ROOT / "B04-002_implementation_coverage_assessment.json").read_text(encoding="utf-8"))
        completeness = json.loads((EVIDENCE_ROOT / "B04-002_constitutional_implementation_completeness_assessment.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B04-002_unresolved_implementation_findings_registry.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B04-002_implementation_obligation_and_dependency_mapping_report.json").read_text(encoding="utf-8"))
        self.assertTrue(all(item["deterministic_dependency_relationship"] for item in dependencies))
        self.assertTrue(all(value == "COVERED_BY_DEPENDENCY_DERIVED_MAPPING" for value in coverage["domains"].values()))
        self.assertEqual(coverage["uncovered_constitutional_requirements"], [])
        self.assertTrue(completeness["complete"])
        self.assertEqual(completeness["implementation_obligation_gaps"], [])
        self.assertEqual(completeness["dependency_mapping_gaps"], [])
        self.assertEqual(completeness["verification_planning_gaps"], [])
        self.assertEqual(completeness["implementation_traceability_gaps"], [])
        self.assertEqual(completeness["orphan_implementation_obligations"], [])
        self.assertEqual(completeness["orphan_constitutional_requirements"], [])
        self.assertEqual(unresolved, [])
        self.assertFalse(report["implementation_correctness_evaluated"])
        self.assertFalse(report["implementation_modified"])
        self.assertFalse(report["behavioral_verification_executed"])
        self.assertFalse(report["implementation_proof_generated"])
        self.assertFalse(report["certification_activity_executed"])

    def test_b04_003_verification_population_is_classified_but_not_executed(self) -> None:
        verifiers = json.loads((EVIDENCE_ROOT / "B04-003_verifier_inventory.json").read_text(encoding="utf-8"))
        modes = json.loads((EVIDENCE_ROOT / "B04-003_verification_mode_registry.json").read_text(encoding="utf-8"))
        integrity = json.loads((EVIDENCE_ROOT / "B04-003_verification_integrity_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(verifiers), 4)
        self.assertEqual(len(verifiers), len(modes))
        self.assertEqual(integrity["orphan_verifiers"], [])
        self.assertEqual(integrity["evidence_producers_lacking_constitutional_authority"], [])

    def test_b04_003_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B04-003_verifier_inventory.json",
            "B04-003_verifier_identity_registry.json",
            "B04-003_verifier_classification_registry.json",
            "B04-003_verifier_participation_registry.json",
            "B04-003_fixture_inventory.json",
            "B04-003_fixture_participation_registry.json",
            "B04-003_runtime_participation_registry.json",
            "B04-003_runtime_classification_registry.json",
            "B04-003_evidence_producer_registry.json",
            "B04-003_evidence_consumer_registry.json",
            "B04-003_verification_dependency_graph.json",
            "B04-003_dependency_direction_registry.json",
            "B04-003_dependency_justification_registry.json",
            "B04-003_verification_planning_registry.json",
            "B04-003_implementation_obligation_verification_matrix.json",
            "B04-003_verification_completeness_assessment.json",
            "B04-003_runtime_completeness_assessment.json",
            "B04-003_unresolved_verification_findings_registry.json",
            "B04-003_verifier_fixture_evidence_runtime_participation_report.json",
            "B04-003_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

    def test_b04_003_verifiers_fixtures_runtime_and_evidence_are_mapped(self) -> None:
        verifiers = json.loads((EVIDENCE_ROOT / "B04-003_verifier_inventory.json").read_text(encoding="utf-8"))
        classifications = json.loads((EVIDENCE_ROOT / "B04-003_verifier_classification_registry.json").read_text(encoding="utf-8"))
        fixtures = json.loads((EVIDENCE_ROOT / "B04-003_fixture_participation_registry.json").read_text(encoding="utf-8"))
        runtime = json.loads((EVIDENCE_ROOT / "B04-003_runtime_participation_registry.json").read_text(encoding="utf-8"))
        producers = json.loads((EVIDENCE_ROOT / "B04-003_evidence_producer_registry.json").read_text(encoding="utf-8"))
        consumers = json.loads((EVIDENCE_ROOT / "B04-003_evidence_consumer_registry.json").read_text(encoding="utf-8"))
        self.assertTrue(verifiers)
        self.assertEqual(len(verifiers), len(classifications))
        self.assertTrue(all(item["governing_constitutional_authority"] for item in verifiers))
        self.assertTrue(all(item["governing_implementation_obligations"] for item in verifiers))
        self.assertTrue(all(item["governing_fixture_population"] for item in verifiers))
        self.assertTrue(all(item["classification_is_exactly_one"] for item in classifications))
        self.assertTrue(all(item["fixture_purpose"] for item in fixtures))
        self.assertTrue(runtime)
        self.assertTrue(all(item["objective_dependency_evidence"] for item in runtime))
        self.assertTrue(producers)
        self.assertTrue(consumers)

    def test_b04_003_dependencies_and_planning_are_complete_without_execution(self) -> None:
        directions = json.loads((EVIDENCE_ROOT / "B04-003_dependency_direction_registry.json").read_text(encoding="utf-8"))
        planning = json.loads((EVIDENCE_ROOT / "B04-003_verification_planning_registry.json").read_text(encoding="utf-8"))
        matrix = json.loads((EVIDENCE_ROOT / "B04-003_implementation_obligation_verification_matrix.json").read_text(encoding="utf-8"))
        completeness = json.loads((EVIDENCE_ROOT / "B04-003_verification_completeness_assessment.json").read_text(encoding="utf-8"))
        runtime = json.loads((EVIDENCE_ROOT / "B04-003_runtime_completeness_assessment.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B04-003_unresolved_verification_findings_registry.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B04-003_verifier_fixture_evidence_runtime_participation_report.json").read_text(encoding="utf-8"))
        self.assertTrue(all(item["deterministic_dependency_direction"] for item in directions))
        self.assertTrue(all(item["planning_status"] == "COMPLETE_NOT_EXECUTED" for item in planning))
        self.assertTrue(all(item["verification_disposition"] == "PLANNED_NOT_EXECUTED" for item in matrix))
        self.assertTrue(completeness["complete"])
        self.assertEqual(completeness["verifier_gaps"], [])
        self.assertEqual(completeness["fixture_gaps"], [])
        self.assertEqual(completeness["runtime_participation_gaps"], [])
        self.assertEqual(completeness["evidence_participation_gaps"], [])
        self.assertEqual(completeness["dependency_gaps"], [])
        self.assertEqual(completeness["unresolved_verification_ambiguity"], [])
        self.assertTrue(runtime["complete"])
        self.assertEqual(unresolved, [])
        self.assertFalse(report["filename_derived_population"])
        self.assertFalse(report["test_name_derived_population"])
        self.assertFalse(report["package_name_derived_population"])
        self.assertFalse(report["manual_inventory"])
        self.assertFalse(report["documentation_reference_inventory"])
        self.assertFalse(report["historical_execution_batch_inventory"])
        self.assertFalse(report["behavioral_correctness_evaluated"])
        self.assertFalse(report["implementation_modified"])
        self.assertFalse(report["behavioral_verification_executed"])
        self.assertFalse(report["implementation_proof_generated"])
        self.assertFalse(report["certification_activity_executed"])

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
