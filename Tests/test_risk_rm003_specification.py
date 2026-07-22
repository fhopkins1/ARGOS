from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision  # noqa: E402
from argos.risk import RiskOfficeSpecificationSupport  # noqa: E402


class RiskRm003SpecificationProgramTests(unittest.TestCase):
    def test_rm003_program_manifest_covers_all_required_specification_work_orders(self) -> None:
        record = RiskOfficeSpecificationSupport().build_specification_program_record()

        self.assertEqual(record.result, EnterpriseCertificationDecision.PASS)
        self.assertEqual(record.program_identifier, "RISK-RM-003")
        self.assertEqual(len(record.work_orders), 25)
        self.assertEqual(record.work_orders[0].work_order_identifier, "RISK-RM-003-001")
        self.assertEqual(record.work_orders[-1].work_order_identifier, "RISK-RM-003-025")
        self.assertIn("Risk Fusion Doctrine", {order.title for order in record.work_orders})
        self.assertIn("ownership", record.complete_specification_fields)
        self.assertIn("auditability", record.complete_specification_fields)
        self.assertIn("complete independent certification test suite", record.deliverables)
        self.assertIn("every Constitutional Specification Work Order complete", record.completion_criteria)
        self.assertIn("Bridge Certification", record.excluded_certification_domains)
        self.assertNotEqual(record.deterministic_digest, "")

    def test_rm003_program_manifest_fails_closed_on_missing_scope_or_evidence(self) -> None:
        record = RiskOfficeSpecificationSupport().build_specification_program_record(
            missing_work_order_findings=("RISK-RM-003-017 absent",),
            ownership_boundary_findings=("Bridge behavior redefined",),
            guarantee_regression_findings=("RM002 validation weakened",),
            interpretation_findings=("implementation chooses freshness rule",),
            deliverable_gaps=("certification test suite absent",),
            evidence_gaps=("traceability evidence missing",),
        )

        self.assertEqual(record.result, EnterpriseCertificationDecision.FAIL)
        self.assertIn("RISK-RM-003-017 absent", record.missing_work_order_findings)
        self.assertIn("Bridge behavior redefined", record.ownership_boundary_findings)
        self.assertIn("implementation chooses freshness rule", record.interpretation_findings)
        self.assertIn("traceability evidence missing", record.evidence_gaps)


if __name__ == "__main__":
    unittest.main()
