from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "Documentation" / "MONITORING_ECS003_AUDIT_001"


class MonitoringECS003AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{REPOSITORY_ROOT}{os.pathsep}{REPOSITORY_ROOT / 'src'}"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "Scripts" / "monitoring_ecs003_audit.py")],
            cwd=REPOSITORY_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )

    def test_final_verdict_fails_closed_without_remediation(self) -> None:
        verdict = json.loads((EVIDENCE_ROOT / "final_ecs003_verdict.json").read_text(encoding="utf-8"))
        completion = json.loads((EVIDENCE_ROOT / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(verdict["verdict"], "FAIL")
        self.assertTrue(verdict["issued_exactly_one_verdict"])
        self.assertFalse(completion["constitutional_doctrine_modified"])
        self.assertFalse(completion["implementation_behavior_modified"])
        self.assertFalse(completion["remediation_executed"])

    def test_required_audit_deliverables_exist(self) -> None:
        required = [
            "executive_audit_report.json",
            "constitutional_audit_report.json",
            "constitutional_finding_registry.json",
            "canonical_constitutional_requirement_registry.json",
            "dependency_derived_implementation_inventory.json",
            "requirement_to_implementation_matrix.json",
            "behavioral_execution_registry.json",
            "requirement_proof_registry.json",
            "execution_derived_traceability_graph.json",
            "certification_blocker_registry.json",
            "clean_environment_reproduction_report.json",
            "final_ecs003_certification_report.json",
            "final_ecs003_verdict.json",
        ]
        for filename in required:
            self.assertTrue((EVIDENCE_ROOT / filename).exists(), filename)

    def test_behavioral_monitoring_verifier_executed_successfully(self) -> None:
        executions = json.loads((EVIDENCE_ROOT / "behavioral_execution_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["module"], "Tests.test_trade_monitoring_office")
        self.assertEqual(executions[0]["terminal_disposition"], "PASS")
        self.assertTrue((REPOSITORY_ROOT / executions[0]["stdout"]).exists())
        self.assertTrue((REPOSITORY_ROOT / executions[0]["stderr"]).exists())

    def test_certification_blockers_are_objective_and_open(self) -> None:
        findings = json.loads((EVIDENCE_ROOT / "constitutional_finding_registry.json").read_text(encoding="utf-8"))
        blockers = json.loads((EVIDENCE_ROOT / "certification_blocker_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(findings), 13)
        self.assertGreaterEqual(len(blockers), len(findings))
        self.assertTrue(all(item["severity"] == "CERTIFICATION_BLOCKING" for item in findings))
        self.assertTrue(all(item["disposition"] == "OPEN" for item in findings))

    def test_dependency_inventory_uses_objective_import_evidence(self) -> None:
        inventory = json.loads((EVIDENCE_ROOT / "dependency_derived_implementation_inventory.json").read_text(encoding="utf-8"))
        direct = [item for item in inventory if item["classification"] == "MONITORING_DIRECT"]
        verifier = [item for item in inventory if item["classification"] == "VERIFIER"]
        self.assertTrue(direct)
        self.assertTrue(verifier)
        self.assertIn("imports", direct[0]["inclusion_evidence"])
        self.assertTrue(verifier[0]["inclusion_evidence"]["runtime_invocation"])


if __name__ == "__main__":
    unittest.main()
