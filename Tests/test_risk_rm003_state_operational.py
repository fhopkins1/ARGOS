from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskRm003StateOperationalSupport  # noqa: E402


class RiskRm003StateOperationalTests(unittest.TestCase):
    def test_state_operational_package_covers_orders_six_through_fifteen(self) -> None:
        package = RiskRm003StateOperationalSupport().build_operational_package(
            candidate_identifier="RM003-STATE-FRESH-PACKET"
        )

        self.assertEqual(package.final_completion_readiness, EnterpriseCertificationDecision.PASS)
        self.assertEqual(
            package.order_coverage,
            (
                "RISK-RM-003-006",
                "RISK-RM-003-007",
                "RISK-RM-003-008",
                "RISK-RM-003-009",
                "RISK-RM-003-010",
                "RISK-RM-003-011",
                "RISK-RM-003-012",
                "RISK-RM-003-013",
                "RISK-RM-003-014",
                "RISK-RM-003-015",
            ),
        )
        self.assertEqual(len(package.records), 10)
        self.assertEqual(package.records["RISK-RM-003-006"].title, "Risk Mission Lifecycle")
        self.assertEqual(package.records["RISK-RM-003-009"].title, "Risk Freshness Doctrine")
        self.assertEqual(package.records["RISK-RM-003-010"].title, "Enterprise Risk State Constitution")
        self.assertIn("state_machine_to_persistence", package.cross_order_traceability)
        self.assertTrue(all(record.result == EnterpriseCertificationDecision.PASS for record in package.records.values()))
        self.assertEqual(package.replay_digest, RiskRm003StateOperationalSupport().build_operational_package().replay_digest)
        self.assertNotEqual(package.deterministic_digest, "")

    def test_state_records_fail_closed_when_required_elements_are_missing(self) -> None:
        support = RiskRm003StateOperationalSupport()

        mission = support.evaluate_mission_lifecycle(
            implemented_elements=("authorization", "activation"),
        )
        sufficiency = support.evaluate_sufficiency(
            implemented_elements=("sufficiency authority", "evidence completeness"),
        )
        equivalence = support.evaluate_equivalence(
            implemented_elements=("canonical identity",),
            findings=("implementation-defined equivalence admitted",),
        )

        self.assertEqual(mission.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required element missing: authority relinquishment", mission.findings)
        self.assertEqual(sufficiency.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required element missing: confidence thresholds", sufficiency.findings)
        self.assertEqual(equivalence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("implementation-defined equivalence admitted", equivalence.findings)
        self.assertIn("required element missing: duplicate detection", equivalence.findings)

    def test_evidence_provenance_state_machine_and_persistence_fail_closed_on_gaps(self) -> None:
        support = RiskRm003StateOperationalSupport()

        evidence = support.evaluate_risk_evidence(
            implemented_elements=("evidence identity", "ownership", "schema"),
        )
        provenance = support.evaluate_provenance_architecture(
            implemented_elements=("constitutional origin", "intermediate transformations"),
        )
        state_machine = support.evaluate_office_state_machine(
            implemented_elements=("execution states", "legal transitions"),
        )
        persistent_state = support.evaluate_persistent_state(
            implemented_elements=("persistent elements", "checkpoint ownership"),
        )

        self.assertEqual(evidence.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required element missing: provenance", evidence.findings)
        self.assertEqual(provenance.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required element missing: enterprise conclusion lineage", provenance.findings)
        self.assertEqual(state_machine.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required element missing: fail-closed behavior", state_machine.findings)
        self.assertEqual(persistent_state.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("required element missing: transient elements", persistent_state.findings)

    def test_enterprise_state_rejection_and_freshness_include_deterministic_guardrails(self) -> None:
        support = RiskRm003StateOperationalSupport()

        freshness = support.evaluate_freshness()
        enterprise_state = support.evaluate_enterprise_risk_state()
        rejection = support.evaluate_rejection_taxonomy()

        self.assertEqual(freshness.result, EnterpriseCertificationDecision.PASS)
        self.assertIn("freshness is never inferred from runtime behavior", freshness.deterministic_rules)
        self.assertEqual(enterprise_state.result, EnterpriseCertificationDecision.PASS)
        self.assertIn("one current state per scope", enterprise_state.deterministic_rules)
        self.assertEqual(rejection.result, EnterpriseCertificationDecision.PASS)
        self.assertIn("unknown rejection fails closed", rejection.deterministic_rules)


if __name__ == "__main__":
    unittest.main()
