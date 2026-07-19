from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.authority_promotion_closure import (  # noqa: E402
    AuthorityClassification,
    AuthorityPromotionAuthority,
    AuthorityPromotionRejectionCode,
    ConstitutionalAuthorityRegistry,
    execute_tc002_certification,
)
from argos.control_panel.canonical_bridge_dynamic_coverage import DynamicCoverageStatus, execute_tc003_certification  # noqa: E402
from argos.control_panel.orphan_office_closure import OfficeDisposition, execute_tc004_certification  # noqa: E402
from argos.control_panel.runtime_bridge_certification import required_runtime_bridge_matrix  # noqa: E402
from argos.control_panel.trace_equivalence import execute_tc001_certification  # noqa: E402


class TC002AuthorityPromotionClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tc002 = execute_tc002_certification(repository_commit="test-commit")
        cls.tc003 = execute_tc003_certification(repository_commit="test-commit")
        cls.tc004 = execute_tc004_certification(repository_commit="test-commit")

    def test_authority_registry_has_unique_ids_and_explicit_classifications(self) -> None:
        inventory = self.tc002["authority_inventory"]
        ids = [item["authority_id"] for item in inventory]

        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(item["classification"] in {classification.value for classification in AuthorityClassification} for item in inventory))
        self.assertEqual(self.tc002["certification"]["verdict"], "INCOMPLETE")

    def test_core_bridge_authority_failures_are_closed(self) -> None:
        results = self.tc002["core_bridge_authority_results"]

        self.assertEqual(len(results), len(required_runtime_bridge_matrix()))
        self.assertTrue(all(item["current_promotion_result"] == "ACCEPTED" for item in results))
        self.assertTrue(all(item["prior_failure"] == "NONE" for item in results))

    def test_promotion_rejects_missing_or_wrong_authority_and_provenance(self) -> None:
        authority = AuthorityPromotionAuthority(ConstitutionalAuthorityRegistry())
        provenance = authority.provenance(
            artifact_id="ART-BAD",
            artifact_type="trade_authorization.v1",
            producer_authority_id="AUTH-CERTIFICATION-AUTHORITY",
            token_reference="",
            source_artifact_ids=(),
        )
        decision = authority.promote(provenance, destination_authority_id="AUTH-TRADER")

        self.assertEqual(decision.final_decision.value, "REJECTED")
        self.assertIn(AuthorityPromotionRejectionCode.AUTHORITY_PRODUCTION_DISABLED, decision.reason_codes)
        self.assertIn(AuthorityPromotionRejectionCode.PROVENANCE_UNVERIFIED, decision.reason_codes)

    def test_delegation_records_are_explicit_and_valid(self) -> None:
        delegations = self.tc002["delegation_inventory"]

        self.assertGreaterEqual(len(delegations), 5)
        self.assertTrue(all(item["validation_status"] == "VALID" for item in delegations))
        self.assertTrue(all(item["delegation_id"] and item["deterministic_hash"] for item in delegations))

    def test_tc001_controls_remain_intact(self) -> None:
        tc001 = execute_tc001_certification(repository_commit="test-commit")

        self.assertEqual(tc001["certification"]["verdict"], "INCOMPLETE")
        self.assertGreaterEqual(tc001["certification"]["certification_harness_rejected_count"], 1)


class TC003CanonicalBridgeCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_tc003_certification(repository_commit="test-commit")

    def test_denominator_uses_authoritative_registry(self) -> None:
        coverage = self.payload["certification"]["coverage"]

        self.assertEqual(coverage["total_required_bridges"], len(required_runtime_bridge_matrix()))
        self.assertEqual(coverage["total_required_bridges"], 30)

    def test_coverage_is_exact_and_uncovered_bridges_are_reported(self) -> None:
        coverage = self.payload["certification"]["coverage"]

        self.assertEqual(coverage["canonical_runtime_executed"], 29)
        self.assertEqual(coverage["coverage_percent"], 96.67)
        self.assertEqual(coverage["uncovered_bridge_ids"], ("BRIDGE-REPLAY-LAB-001",))
        self.assertEqual(self.payload["certification"]["verdict"], "INCOMPLETE")

    def test_direct_contract_execution_is_not_counted(self) -> None:
        static = self.payload["static_assurance"]

        self.assertFalse(static["directCertificationBridgeExecutionCounted"])
        self.assertFalse(static["manufacturedDestinationAcceptanceCounted"])
        self.assertFalse(static["coverageOverstated"])

    def test_operations_chain_contains_real_canonical_bridge(self) -> None:
        operations = self.payload["operations_chain_trace"]

        self.assertIn("BRIDGE-WORKFLOW-OFFICE-001", operations["canonicalRuntimeExecuted"])
        self.assertEqual(operations["verdict"], "PASS")

    def test_matrix_marks_nonexecuted_bridges_without_certified_production_credit(self) -> None:
        matrix = self.payload["bridge_certification_matrix"]
        nonexecuted = [item for item in matrix if item["canonical_execution_status"] != DynamicCoverageStatus.CANONICAL_RUNTIME_EXECUTED.value]

        self.assertTrue(nonexecuted)
        self.assertTrue(all(item["certification_status"] != "CERTIFIED_PRODUCTION" for item in nonexecuted))


class TC004OrphanOfficeClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = execute_tc004_certification(repository_commit="test-commit")

    def test_every_office_like_component_has_disposition(self) -> None:
        inventory = self.payload["office_disposition_inventory"]

        self.assertEqual(len(inventory), self.payload["certification"]["office_like_component_count"])
        self.assertTrue(all(item["disposition"] in {disposition.value for disposition in OfficeDisposition} for item in inventory))

    def test_orphan_count_is_reported_honestly(self) -> None:
        certification = self.payload["certification"]

        self.assertEqual(certification["verdict"], "INCOMPLETE")
        self.assertEqual(certification["initial_orphan_count"], 0)
        self.assertEqual(certification["final_production_reachable_orphan_count"], 1)

    def test_services_and_adapters_do_not_hold_office_ownership(self) -> None:
        services = self.payload["service_reclassifications"]

        self.assertTrue(services)
        self.assertTrue(all(item["true_type"] == "adapter" for item in services))

    def test_dormant_offices_reject_mutation(self) -> None:
        dormancy = self.payload["dormancy_validation"]

        self.assertTrue(dormancy["dormantMutationRejected"])
        self.assertEqual(dormancy["rejectionCode"], "OFFICE_DORMANT_MUTATION_REJECTED")

    def test_background_authority_is_prohibited(self) -> None:
        background = self.payload["background_activity_validation"]

        self.assertFalse(background["selfWakeAllowed"])
        self.assertFalse(background["backgroundMayPerformOfficeWork"])
        self.assertTrue(background["watchersMayRequestActivationOnly"])


if __name__ == "__main__":
    unittest.main()
