from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.trader.rm002_constitution import TRADER_RM002_OBJECTS, TRADER_RM002_RULES  # noqa: E402
from argos.trader.rm002a_publication import (  # noqa: E402
    CERTIFICATION_RECONCILIATION_SEQUENCE,
    EXECUTABLE_VERIFICATIONS,
    EXTERNAL_AUTHORITY_CONTRACTS,
    OBJECT_SCHEMAS,
    PROVIDED_RM002A_WORK_ORDERS,
    PUBLISHED_ARTIFACTS,
    TRACEABILITY_MATRIX,
    RM002AStatus,
    validate_certification_reconciliation,
    validate_clean_room_reproducibility,
    validate_rm002a_publication,
)


class TraderRM002APublicationTests(unittest.TestCase):
    def test_publication_set_reconciles_to_provided_work_orders(self) -> None:
        result = validate_rm002a_publication()

        self.assertEqual(result.status, RM002AStatus.PASS, result.findings)
        self.assertEqual({artifact.authority for artifact in PUBLISHED_ARTIFACTS.values()}, set(PROVIDED_RM002A_WORK_ORDERS))

    def test_every_published_artifact_has_required_audit_metadata(self) -> None:
        for artifact in PUBLISHED_ARTIFACTS.values():
            self.assertTrue(artifact.publication_location.startswith("Documentation/Trader/Constitution/"))
            self.assertTrue(artifact.owner)
            self.assertTrue(artifact.evidence_obligations)
            self.assertTrue(artifact.verification_obligations)
            self.assertTrue(artifact.traceability_obligations)

    def test_object_schema_expansion_covers_all_constitutional_objects(self) -> None:
        self.assertEqual(set(OBJECT_SCHEMAS), set(TRADER_RM002_OBJECTS))
        for name, schema in OBJECT_SCHEMAS.items():
            self.assertEqual(schema.object_identifier, TRADER_RM002_OBJECTS[name].identifier)
            self.assertTrue(schema.attributes)
            self.assertTrue(schema.failure_dispositions)
            self.assertIn("audit verdict", schema.traceability)

    def test_external_authority_contracts_are_explicit_and_fail_closed(self) -> None:
        required = {"EO-EXT-001", "EO-EXT-002", "EO-EXT-003", "EO-EXT-004", "EO-EXT-005", "EO-EXT-006"}

        self.assertEqual(required, set(EXTERNAL_AUTHORITY_CONTRACTS))
        self.assertEqual(EXTERNAL_AUTHORITY_CONTRACTS["EO-EXT-001"].owner, "Authorizations Office")
        self.assertIn("fail closed", EXTERNAL_AUTHORITY_CONTRACTS["EO-EXT-006"].failure_behavior)

    def test_every_rule_has_executable_verification(self) -> None:
        expected_ids = {rule_id.replace("TRADER-RULE", "TRADER-VERIFY") for rule_id in TRADER_RM002_RULES}

        self.assertEqual(expected_ids, set(EXECUTABLE_VERIFICATIONS))
        for verification in EXECUTABLE_VERIFICATIONS.values():
            self.assertIn(verification.rule_id, TRADER_RM002_RULES)
            self.assertTrue(verification.procedure)
            self.assertTrue(verification.evidence)

    def test_bidirectional_traceability_links_rule_to_verification_and_verdict_authority(self) -> None:
        for rule_id in TRADER_RM002_RULES:
            chain = TRACEABILITY_MATRIX[rule_id]
            self.assertIn(rule_id.replace("TRADER-RULE", "TRADER-VERIFY"), chain)
            self.assertEqual(chain[-1], "Independent Final Reconciliation Authority")

    def test_clean_room_verification_is_reproducibility_checked(self) -> None:
        self.assertEqual(validate_clean_room_reproducibility(("PASS", "PASS")).status, RM002AStatus.PASS)
        self.assertEqual(validate_clean_room_reproducibility(("PASS", "FAIL")).status, RM002AStatus.FAIL)
        self.assertEqual(validate_clean_room_reproducibility(()).status, RM002AStatus.FAIL)

    def test_certification_reconciliation_separates_candidate_readiness(self) -> None:
        self.assertEqual(CERTIFICATION_RECONCILIATION_SEQUENCE[-1], "independent verdict")
        valid = validate_certification_reconciliation("UNCONDITIONAL PASS", "Independent Final Reconciliation Authority")
        candidate = validate_certification_reconciliation("UNCONDITIONAL PASS", "Trader Office", candidate_claims_certification=True)
        conditional = validate_certification_reconciliation("CONDITIONAL PASS", "Independent Final Reconciliation Authority")

        self.assertEqual(valid.status, RM002AStatus.PASS)
        self.assertEqual(candidate.status, RM002AStatus.FAIL)
        self.assertEqual(conditional.status, RM002AStatus.FAIL)


if __name__ == "__main__":
    unittest.main()
