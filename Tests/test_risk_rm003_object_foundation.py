from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import (  # noqa: E402
    RiskEvaluationGraphEdge,
    RiskEvaluationGraphNode,
    RiskRm003ObjectFoundationSupport,
)


class RiskRm003ObjectFoundationOperationalTests(unittest.TestCase):
    def test_operational_package_executes_first_five_orders_as_candidate_bound_evidence(self) -> None:
        package = RiskRm003ObjectFoundationSupport().build_operational_package(
            candidate_identifier="RM003-FRESH-ORDER-PACKET"
        )

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-003-001",
                "RISK-RM-003-002",
                "RISK-RM-003-003",
                "RISK-RM-003-004",
                "RISK-RM-003-005",
            ),
        )
        self.assertEqual(package.risk_assessment.constitutional_owner, "Risk Office")
        self.assertEqual(package.risk_assessment.mission_identifier, package.mission.mission_identifier)
        self.assertEqual(package.risk_assessment.package_identifier, package.evaluation_package.package_identifier)
        self.assertEqual(package.risk_assessment.graph_identifier, package.evaluation_graph.graph_identifier)
        self.assertEqual(package.risk_assessment.findings, ())
        self.assertGreaterEqual(len(package.risk_assessment.supporting_evidence_references), 2)
        self.assertEqual(package.mission.authority_relinquished, True)
        self.assertIn("risk_evaluation_package", package.mission.relationships)
        self.assertIn("Enterprise Risk Assessment", package.evaluation_package.package_sections)
        self.assertEqual(package.evaluation_graph.topological_order[0], "NODE-EVIDENCE-RM003")
        self.assertEqual(package.evaluation_graph.topological_order[-1], "NODE-ENTERPRISE-RISK-RM003")
        self.assertEqual(len(package.lifecycle_profiles), 4)
        self.assertTrue(all(profile.result == EnterpriseCertificationDecision.PASS for profile in package.lifecycle_profiles))
        self.assertEqual(package.replay_digest, RiskRm003ObjectFoundationSupport().build_operational_package().replay_digest)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_assessment_and_mission_fail_closed_when_required_constitutional_inputs_are_missing(self) -> None:
        support = RiskRm003ObjectFoundationSupport()

        assessment = support.evaluate_assessment(
            supporting_evidence_references=(),
            validation_references=(),
            audit_references=(),
        )
        mission = support.evaluate_mission(
            workflow_execution_token="",
            evaluation_scope_identifier="",
            relationships={"risk_assessment": "RISK-ASSESSMENT-RM003-001"},
            authority_relinquished=False,
        )

        self.assertEqual(assessment.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("assessment supporting evidence missing", assessment.findings)
        self.assertIn("assessment validation reference missing", assessment.findings)
        self.assertIn("assessment audit reference missing", assessment.findings)
        self.assertEqual(mission.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("workflow execution token missing", mission.findings)
        self.assertIn("evaluation scope identifier missing", mission.findings)
        self.assertIn("mission completion did not relinquish constitutional authority", mission.findings)

    def test_package_validation_fails_closed_for_missing_sections_and_traceability(self) -> None:
        support = RiskRm003ObjectFoundationSupport()

        package = support.evaluate_package(
            package_sections={
                "Package Identity": ("Package Identifier", "Mission Identifier", "Assessment Identifier"),
                "Mission Metadata": ("Authorizing Authority",),
            },
            validation_records=("schema validation",),
            traceability_records=("provenance graph",),
            audit_records=("evaluation audit",),
        )

        self.assertEqual(package.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("package section missing: Audit Records", package.findings)
        self.assertIn("package validation missing: integrity validation", package.findings)
        self.assertIn("package traceability missing: dependency graph", package.findings)
        self.assertIn("package audit records incomplete", package.findings)

    def test_graph_validation_rejects_cycles_unauthorized_edges_and_duplicate_nodes(self) -> None:
        support = RiskRm003ObjectFoundationSupport()
        nodes = (
            RiskEvaluationGraphNode("A", "Evidence Node", "EVIDENCE-A"),
            RiskEvaluationGraphNode("B", "Validation Node", "VALIDATION-B"),
            RiskEvaluationGraphNode("B", "Enterprise Risk Node", "RISK-B"),
        )
        edges = (
            RiskEvaluationGraphEdge("A", "B", "SUPPORTS"),
            RiskEvaluationGraphEdge("B", "A", "CUSTOM_EDGE"),
        )

        graph = support.evaluate_graph(nodes=nodes, edges=edges)

        self.assertEqual(graph.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("graph contains duplicate node identifiers", graph.findings)
        self.assertIn("unauthorized graph edge type: CUSTOM_EDGE", graph.findings)
        self.assertIn("graph cycle detected", graph.findings)

    def test_lifecycle_profile_rejects_illegal_transition_and_foreign_owned_class(self) -> None:
        support = RiskRm003ObjectFoundationSupport()

        profile = support.evaluate_lifecycle_profile(
            object_class="Foreign Commander Object",
            current_state="Implementation Defined",
            transition_history=(
                ("Created", "Active", "Risk Office", "AUDIT-1"),
                ("Active", "Archived", "Other Office", ""),
            ),
            audit_references=(),
        )

        self.assertEqual(profile.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("lifecycle state unauthorized: Implementation Defined", profile.findings)
        self.assertIn("illegal lifecycle transition: Created->Active", profile.findings)
        self.assertIn("transition authority invalid: Active->Archived", profile.findings)
        self.assertIn("transition audit reference missing: Active->Archived", profile.findings)
        self.assertIn("lifecycle audit references missing", profile.findings)
        self.assertIn("lifecycle object class outside Risk-owned scope: Foreign Commander Object", profile.findings)


if __name__ == "__main__":
    unittest.main()
