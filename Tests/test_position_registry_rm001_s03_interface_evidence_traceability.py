from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S03_INTERFACE_EVIDENCE_TRACEABILITY"


class PositionRegistryRM001S03InterfaceEvidenceTraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}{os.pathsep}{REPOSITORY_ROOT / 'Scripts'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "position_registry_rm001_s03_interface_evidence_traceability.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_b03_001_interfaces_have_unique_authority_producer_consumer_and_contract(self) -> None:
        interfaces = json.loads((EVIDENCE_ROOT / "B03-001_constitutional_interface_registry.json").read_text(encoding="utf-8"))
        ambiguity = json.loads((EVIDENCE_ROOT / "B03-001_interface_ambiguity_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(interfaces), 12)
        self.assertEqual(len({item["interface_id"] for item in interfaces}), len(interfaces))
        self.assertTrue(all(item["authoritative_producer"] for item in interfaces))
        self.assertTrue(all(item["authoritative_consumer"] for item in interfaces))
        self.assertTrue(all(item["constitutional_owner"] == "Position Registry" for item in interfaces))
        self.assertTrue(all(item["governing_contract"] for item in interfaces))
        self.assertTrue(all(item["interaction_direction"] for item in interfaces))
        self.assertTrue(all(item["constitutional_admissibility"] for item in interfaces))
        self.assertEqual(ambiguity, [])

    def test_b03_001_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B03-001_constitutional_interface_registry.json",
            "B03-001_canonical_interface_identity_registry.json",
            "B03-001_interface_authority_registry.json",
            "B03-001_interface_interaction_contract_registry.json",
            "B03-001_interface_dependency_registry.json",
            "B03-001_interface_evidence_registry.json",
            "B03-001_interface_ordering_registry.json",
            "B03-001_interface_replay_registry.json",
            "B03-001_interface_recovery_registry.json",
            "B03-001_interface_acknowledgement_registry.json",
            "B03-001_interface_reconciliation_registry.json",
            "B03-001_interface_completeness_assessment.json",
            "B03-001_interface_ambiguity_registry.json",
            "B03-001_unresolved_constitutional_findings_registry.json",
            "B03-001_constitutional_interface_report.json",
            "B03-001_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

    def test_b03_001_contracts_are_deterministic_and_auditable(self) -> None:
        identities = json.loads((EVIDENCE_ROOT / "B03-001_canonical_interface_identity_registry.json").read_text(encoding="utf-8"))
        contracts = json.loads((EVIDENCE_ROOT / "B03-001_interface_interaction_contract_registry.json").read_text(encoding="utf-8"))
        evidence = json.loads((EVIDENCE_ROOT / "B03-001_interface_evidence_registry.json").read_text(encoding="utf-8"))
        ordering = json.loads((EVIDENCE_ROOT / "B03-001_interface_ordering_registry.json").read_text(encoding="utf-8"))
        replay = json.loads((EVIDENCE_ROOT / "B03-001_interface_replay_registry.json").read_text(encoding="utf-8"))
        recovery = json.loads((EVIDENCE_ROOT / "B03-001_interface_recovery_registry.json").read_text(encoding="utf-8"))
        acknowledgement = json.loads((EVIDENCE_ROOT / "B03-001_interface_acknowledgement_registry.json").read_text(encoding="utf-8"))
        reconciliation = json.loads((EVIDENCE_ROOT / "B03-001_interface_reconciliation_registry.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B03-001_constitutional_interface_report.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B03-001_unresolved_constitutional_findings_registry.json").read_text(encoding="utf-8"))

        self.assertTrue(all(item["immutable"] for item in identities))
        self.assertTrue(all(item["canonical_identity_contract"] for item in contracts))
        self.assertTrue(all(item["historical_preservation_obligations"] for item in contracts))
        self.assertTrue(all(item["evidence_integrity"] and item["evidence_retention"] for item in evidence))
        self.assertTrue(all(item["deterministic_ordering"] for item in ordering))
        self.assertTrue(all(item["deterministic_replay_behavior"] and not item["replay_creates_external_action"] for item in replay))
        self.assertTrue(all(item["deterministic_recovery_behavior"] and not item["recovery_fabricates_missing_truth"] for item in recovery))
        self.assertTrue(all(not item["acknowledgement_fabricates_external_truth"] for item in acknowledgement))
        self.assertTrue(all(item["deterministic_reconciliation_behavior"] and not item["silent_overwrite_permitted"] for item in reconciliation))
        self.assertEqual(unresolved, [])
        self.assertFalse(report["implementation_evaluated"])
        self.assertFalse(report["implementation_modified"])
        self.assertFalse(report["behavioral_verification_executed"])
        self.assertFalse(report["implementation_proof_generated"])
        self.assertFalse(report["certification_activity_executed"])

    def test_b03_002_reconciliation_and_evidence_obligations_are_complete(self) -> None:
        reconciliations = json.loads((EVIDENCE_ROOT / "B03-002_reconciliation_authority_registry.json").read_text(encoding="utf-8"))
        evidence = json.loads((EVIDENCE_ROOT / "B03-002_evidence_doctrine_registry.json").read_text(encoding="utf-8"))
        ambiguity = json.loads((EVIDENCE_ROOT / "B03-002_reconciliation_ambiguity_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(reconciliations), 9)
        self.assertEqual(len(evidence), 11)
        self.assertTrue(all(item["authoritative_source_precedence"] for item in reconciliations))
        self.assertTrue(all(item["provenance"] and item["integrity"] and item["retention"] for item in evidence))
        self.assertEqual(ambiguity, [])

    def test_b03_002_exact_audit_deliverables_exist(self) -> None:
        required = {
            "B03-002_reconciliation_constitution.json",
            "B03-002_reconciliation_authority_registry.json",
            "B03-002_reconciliation_precedence_registry.json",
            "B03-002_constitutional_truth_registry.json",
            "B03-002_constitutional_truth_ownership_registry.json",
            "B03-002_constitutional_truth_precedence_registry.json",
            "B03-002_constitutional_evidence_registry.json",
            "B03-002_evidence_ownership_registry.json",
            "B03-002_evidence_producer_registry.json",
            "B03-002_evidence_consumer_registry.json",
            "B03-002_evidence_custody_registry.json",
            "B03-002_evidence_provenance_registry.json",
            "B03-002_evidence_integrity_registry.json",
            "B03-002_evidence_lineage_registry.json",
            "B03-002_evidence_retention_registry.json",
            "B03-002_constitutional_reconciliation_completeness_assessment.json",
            "B03-002_constitutional_evidence_completeness_assessment.json",
            "B03-002_constitutional_truth_completeness_assessment.json",
            "B03-002_unresolved_constitutional_findings_registry.json",
            "B03-002_constitutional_reconciliation_and_evidence_report.json",
            "B03-002_completion_report.json",
        }
        missing = [name for name in sorted(required) if not (EVIDENCE_ROOT / name).exists()]
        self.assertEqual(missing, [])

    def test_b03_002_truth_ownership_and_precedence_are_unambiguous(self) -> None:
        truths = json.loads((EVIDENCE_ROOT / "B03-002_constitutional_truth_registry.json").read_text(encoding="utf-8"))
        ownership = json.loads((EVIDENCE_ROOT / "B03-002_constitutional_truth_ownership_registry.json").read_text(encoding="utf-8"))
        precedence = json.loads((EVIDENCE_ROOT / "B03-002_constitutional_truth_precedence_registry.json").read_text(encoding="utf-8"))
        completeness = json.loads((EVIDENCE_ROOT / "B03-002_constitutional_truth_completeness_assessment.json").read_text(encoding="utf-8"))
        expected_truths = {"position_truth", "broker_truth", "execution_truth", "authorization_truth", "risk_truth", "monitoring_truth", "exit_truth", "closed_position_truth", "performance_truth", "historical_truth"}
        self.assertEqual({item["truth_name"] for item in truths}, expected_truths)
        self.assertEqual(len({item["truth_name"] for item in ownership}), len(ownership))
        self.assertTrue(all(item["canonical_truth_owner"] for item in ownership))
        self.assertTrue(all(item["truth_precedence"] for item in precedence))
        self.assertEqual(completeness["conflicting_truth_ownership"], [])
        self.assertEqual(completeness["duplicate_truth_ownership"], [])
        self.assertEqual(completeness["ambiguous_truth_precedence"], [])

    def test_b03_002_evidence_has_identity_provenance_integrity_lineage_and_retention(self) -> None:
        evidence = json.loads((EVIDENCE_ROOT / "B03-002_constitutional_evidence_registry.json").read_text(encoding="utf-8"))
        lineage = json.loads((EVIDENCE_ROOT / "B03-002_evidence_lineage_registry.json").read_text(encoding="utf-8"))
        report = json.loads((EVIDENCE_ROOT / "B03-002_constitutional_reconciliation_and_evidence_report.json").read_text(encoding="utf-8"))
        unresolved = json.loads((EVIDENCE_ROOT / "B03-002_unresolved_constitutional_findings_registry.json").read_text(encoding="utf-8"))
        self.assertTrue({"position_creation", "lifecycle_transition", "quantity_mutation", "cost_basis_mutation", "replay", "recovery", "correction", "supersession", "reconciliation", "anomaly", "archival"}.issubset({item["evidence_name"] for item in evidence}))
        self.assertTrue(all(item["canonical_evidence_identity"] for item in evidence))
        self.assertTrue(all(item["provenance"] and item["integrity"] and item["custody"] and item["retention"] for item in evidence))
        self.assertTrue(all(item["lineage_requirements"] for item in lineage))
        self.assertEqual(unresolved, [])
        self.assertTrue(report["deterministic_provenance"])
        self.assertTrue(report["deterministic_integrity"])
        self.assertTrue(report["deterministic_custody"])
        self.assertTrue(report["deterministic_retention"])
        self.assertFalse(report["implementation_evaluated"])
        self.assertFalse(report["implementation_modified"])
        self.assertFalse(report["behavioral_verification_executed"])
        self.assertFalse(report["implementation_proof_generated"])
        self.assertFalse(report["certification_activity_executed"])

    def test_b03_003_requirements_have_bidirectional_traceability(self) -> None:
        requirements = json.loads((EVIDENCE_ROOT / "B03-003_canonical_constitutional_requirement_registry.json").read_text(encoding="utf-8"))
        traceability = json.loads((EVIDENCE_ROOT / "B03-003_constitutional_traceability_registry.json").read_text(encoding="utf-8"))
        orphans = json.loads((EVIDENCE_ROOT / "B03-003_orphan_requirement_registry.json").read_text(encoding="utf-8"))
        requirement_ids = {item["requirement_id"] for item in requirements}
        traced = {item["source_node"] for item in traceability}
        self.assertTrue(requirement_ids.issubset(traced))
        self.assertTrue(all(item["reverse_relationship"] for item in traceability))
        self.assertEqual(orphans, [])

    def test_b03_004_baseline_has_no_unresolved_findings_or_implementation_claims(self) -> None:
        baseline = json.loads((EVIDENCE_ROOT / "B03-004_authoritative_position_registry_interface_evidence_traceability_baseline.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(baseline["unresolved_constitutional_finding_registry"], [])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["behavioral_verification_executed"])
        self.assertFalse(completion["implementation_proof_generated"])
        self.assertFalse(completion["implementation_certification_issued"])


if __name__ == "__main__":
    unittest.main()
