from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.trader.rm002_constitution import (  # noqa: E402
    AUTHORITY_PRECEDENCE,
    CASE_FILE_REQUIRED_EVIDENCE,
    DEPENDENCY_CLASSES,
    DOCTRINE_SUPERSESSION_REGISTER,
    SUBORDINATE_OFFICE_AUTHORITY,
    TRADER_RM002_LIFECYCLES,
    TRADER_RM002_OBJECTS,
    TRADER_RM002_RULES,
    VERIFICATION_CLASSES,
    TraderRM002Status,
    validate_case_file_evidence,
    validate_independent_certification_authority,
    validate_lifecycle_transition,
    validate_rm002_constitution,
)


class TraderRM002ConstitutionTests(unittest.TestCase):
    def test_canonical_constitution_closure_is_complete(self) -> None:
        result = validate_rm002_constitution()

        self.assertEqual(result.status, TraderRM002Status.PASS, result.findings)
        self.assertEqual(AUTHORITY_PRECEDENCE[0], "Enterprise Constitutional Laws")
        self.assertEqual(DOCTRINE_SUPERSESSION_REGISTER["TRADER-RM-002-016"], "retained without modification")
        self.assertIn("Broker Integration Office", SUBORDINATE_OFFICE_AUTHORITY)

    def test_every_registered_object_has_single_owner_and_evidence(self) -> None:
        identifiers = {record.identifier for record in TRADER_RM002_OBJECTS.values()}

        self.assertEqual(len(identifiers), len(TRADER_RM002_OBJECTS))
        for record in TRADER_RM002_OBJECTS.values():
            self.assertTrue(record.owner)
            self.assertTrue(record.evidence)
            self.assertTrue(record.certification_rules)
        self.assertNotEqual(TRADER_RM002_OBJECTS["Authorization"].owner, "Trader Office")
        self.assertNotEqual(TRADER_RM002_OBJECTS["Risk Certificate"].owner, "Trader Office")

    def test_lifecycle_transition_matrix_rejects_prohibited_and_unknown_transitions(self) -> None:
        self.assertEqual(validate_lifecycle_transition("Canonical Order Lifecycle", "Draft", "Validated").status, TraderRM002Status.PASS)
        prohibited = validate_lifecycle_transition("Canonical Order Lifecycle", "Filled", "Submitted")
        undefined = validate_lifecycle_transition("Canonical Order Lifecycle", "Cancelled", "Active")

        self.assertEqual(prohibited.status, TraderRM002Status.FAIL)
        self.assertIn("prohibited transition: Filled->Submitted", prohibited.findings)
        self.assertEqual(undefined.status, TraderRM002Status.FAIL)

    def test_case_file_requires_all_constitutional_evidence(self) -> None:
        self.assertEqual(validate_case_file_evidence(CASE_FILE_REQUIRED_EVIDENCE).status, TraderRM002Status.PASS)
        incomplete = validate_case_file_evidence(tuple(item for item in CASE_FILE_REQUIRED_EVIDENCE if item != "custody acknowledgement"))

        self.assertEqual(incomplete.status, TraderRM002Status.FAIL)
        self.assertTrue(any("custody acknowledgement" in finding for finding in incomplete.findings))

    def test_rule_registry_has_required_verification_classes(self) -> None:
        self.assertIn("Financial Dependency", DEPENDENCY_CLASSES)
        for rule in TRADER_RM002_RULES.values():
            for verification_class in VERIFICATION_CLASSES:
                self.assertIn(verification_class, rule.verification_classes)
            self.assertEqual(rule.certification_status, "Verified")

    def test_candidate_cannot_issue_constitutional_certification(self) -> None:
        valid = validate_independent_certification_authority("UNCONDITIONAL PASS", "Independent Final Reconciliation Authority")
        candidate = validate_independent_certification_authority("UNCONDITIONAL PASS", "Trader Office")
        conditional = validate_independent_certification_authority("CONDITIONAL PASS", "Independent Final Reconciliation Authority")

        self.assertEqual(valid.status, TraderRM002Status.PASS)
        self.assertEqual(candidate.status, TraderRM002Status.FAIL)
        self.assertEqual(conditional.status, TraderRM002Status.FAIL)

    def test_all_lifecycles_have_terminal_archival_path(self) -> None:
        for lifecycle in TRADER_RM002_LIFECYCLES.values():
            self.assertIn("Archived", lifecycle.terminal_states)
            self.assertTrue(lifecycle.replay_behavior)
            self.assertTrue(lifecycle.recovery_behavior)


if __name__ == "__main__":
    unittest.main()
