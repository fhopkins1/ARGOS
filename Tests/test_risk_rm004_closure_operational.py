from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskRm004ClosureOperationalSupport  # noqa: E402


class RiskRm004ClosureOperationalTests(unittest.TestCase):
    def test_closure_package_covers_orders_eleven_through_twenty(self) -> None:
        package = RiskRm004ClosureOperationalSupport().build_operational_package(
            candidate_identifier="RM004-CLOSURE-FRESH-PACKET"
        )

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-004-011",
                "RISK-RM-004-012",
                "RISK-RM-004-013",
                "RISK-RM-004-014",
                "RISK-RM-004-015",
                "RISK-RM-004-016",
                "RISK-RM-004-017",
                "RISK-RM-004-018",
                "RISK-RM-004-019",
                "RISK-RM-004-020",
            ),
        )
        self.assertEqual(len(package.records), 10)
        self.assertEqual(package.records["RISK-RM-004-011"].title, "Constitutional Rule Registry")
        self.assertEqual(package.records["RISK-RM-004-020"].title, "Independent Risk Office Certification Closure")
        self.assertIn("procedure_to_closure", package.closure_trace)
        self.assertTrue(all(record.result == EnterpriseCertificationDecision.PASS for record in package.records.values()))
        self.assertEqual(package.replay_digest, RiskRm004ClosureOperationalSupport().build_operational_package().replay_digest)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_registry_records_fail_closed_when_domains_are_missing(self) -> None:
        support = RiskRm004ClosureOperationalSupport()

        rules = support.evaluate_rule_registry(implemented_domains=("rule identity", "rule ownership"))
        schemas = support.evaluate_schema_registry(implemented_domains=("schema identity",))
        cross_refs = support.evaluate_cross_reference_matrix(implemented_domains=("registry relationships", "identifier spaces"))
        evidence = support.evaluate_evidence_registry(implemented_domains=("evidence ownership", "evidence identity"))
        decisions = support.evaluate_decision_registry(implemented_domains=("decision ownership",), findings=("decision outside registry admitted",))

        self.assertEqual(rules.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: precedence", rules.findings)
        self.assertEqual(schemas.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: validation requirements", schemas.findings)
        self.assertEqual(cross_refs.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: artifact dependencies", cross_refs.findings)
        self.assertEqual(evidence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: provenance", evidence.findings)
        self.assertEqual(decisions.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("decision outside registry admitted", decisions.findings)

    def test_package_traceability_procedure_exception_and_closure_fail_closed_on_gaps(self) -> None:
        support = RiskRm004ClosureOperationalSupport()

        package_schema = support.evaluate_certification_package_schema(implemented_domains=("package structure", "artifact inclusion"))
        traceability = support.evaluate_traceability_matrix(implemented_domains=("traceability identity", "traceability scope"))
        procedure = support.evaluate_certification_procedure(implemented_domains=("initiation", "evidence validation"))
        exceptions = support.evaluate_exception_registry(implemented_domains=("exception ownership",))
        closure = support.evaluate_certification_closure(implemented_domains=("completion", "issuance"))

        self.assertEqual(package_schema.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: registry dependencies", package_schema.findings)
        self.assertEqual(traceability.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: certification linkage", traceability.findings)
        self.assertEqual(procedure.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: fail-closed behavior", procedure.findings)
        self.assertEqual(exceptions.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: approval authority", exceptions.findings)
        self.assertEqual(closure.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required domain missing: evidence archival", closure.findings)

    def test_closure_guardrails_preserve_certification_authority(self) -> None:
        support = RiskRm004ClosureOperationalSupport()

        rules = support.evaluate_rule_registry()
        procedure = support.evaluate_certification_procedure()
        exceptions = support.evaluate_exception_registry()
        closure = support.evaluate_certification_closure()

        self.assertIn("only registry rules may affect certification", rules.deterministic_guards)
        self.assertIn("authority cannot reorder workflow", procedure.deterministic_guards)
        self.assertIn("exceptions cannot modify doctrine", exceptions.deterministic_guards)
        self.assertIn("closed certification is immutable", closure.deterministic_guards)


if __name__ == "__main__":
    unittest.main()
