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
        self.assertTrue(all(item["governing_contract"] for item in interfaces))
        self.assertEqual(ambiguity, [])

    def test_b03_002_reconciliation_and_evidence_obligations_are_complete(self) -> None:
        reconciliations = json.loads((EVIDENCE_ROOT / "B03-002_reconciliation_authority_registry.json").read_text(encoding="utf-8"))
        evidence = json.loads((EVIDENCE_ROOT / "B03-002_evidence_doctrine_registry.json").read_text(encoding="utf-8"))
        ambiguity = json.loads((EVIDENCE_ROOT / "B03-002_reconciliation_ambiguity_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(reconciliations), 9)
        self.assertEqual(len(evidence), 9)
        self.assertTrue(all(item["authoritative_source_precedence"] for item in reconciliations))
        self.assertTrue(all(item["provenance"] and item["integrity"] and item["retention"] for item in evidence))
        self.assertEqual(ambiguity, [])

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
