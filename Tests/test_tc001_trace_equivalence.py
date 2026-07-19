from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.constitutional_certification_series import CSVerdict, run_all_cs_certifications  # noqa: E402
from argos.control_panel.trace_equivalence import (  # noqa: E402
    ExecutionOrigin,
    TraceAuthenticityRecord,
    TraceClaimType,
    TraceEligibilityStatus,
    TraceEquivalenceAuthority,
    TraceEquivalenceLevel,
    TraceRejectionCode,
    execute_tc001_certification,
)


class TC001TraceEquivalenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authority = TraceEquivalenceAuthority()

    def test_origin_classification_never_promotes_unknown_or_harness_to_production(self) -> None:
        self.assertEqual(self.authority.classify_origin(ExecutionOrigin.UNKNOWN), TraceEquivalenceLevel.NONE)
        self.assertEqual(self.authority.classify_origin(ExecutionOrigin.CERTIFICATION_HARNESS), TraceEquivalenceLevel.CONTRACT)
        self.assertEqual(self.authority.classify_origin(ExecutionOrigin.CANONICAL_PRODUCTION_RUNTIME), TraceEquivalenceLevel.CANONICAL_RUNTIME)

    def test_unknown_origin_is_ineligible_for_production_certification(self) -> None:
        record = TraceAuthenticityRecord(
            "TRACE-UNKNOWN",
            "BRIDGE-UNKNOWN",
            ExecutionOrigin.UNKNOWN,
            TraceEquivalenceLevel.NONE,
            TraceClaimType.PRODUCTION_EXECUTION,
            None,
            "",
            (),
            "",
            "",
            False,
            "",
            False,
            "",
            False,
            "",
            "",
            "",
            "",
            (),
            "commit-a",
            "commit-a",
            False,
            "2026-07-18T00:00:00Z",
            "hash",
        )
        result = self.authority.evaluate(record)

        self.assertEqual(result.status, TraceEligibilityStatus.INELIGIBLE)
        self.assertIn(TraceRejectionCode.TRACE_EXECUTION_ORIGIN_UNKNOWN, result.rejection_codes)
        self.assertFalse(result.production_equivalent)

    def test_certification_harness_trace_is_rejected_as_production_equivalent(self) -> None:
        result = self.authority.evaluate(self.authority.certification_harness_record("CS-002", "commit-a"))

        self.assertFalse(result.production_equivalent)
        self.assertIn(TraceRejectionCode.TRACE_CERTIFICATION_HARNESS_ORCHESTRATED, result.rejection_codes)
        self.assertIn(TraceRejectionCode.CERTIFICATION_EVIDENCE_NOT_PRODUCTION_EQUIVALENT, result.rejection_codes)

    def test_tc001_executes_at_least_one_canonical_runtime_trace(self) -> None:
        payload = execute_tc001_certification(repository_commit="commit-a")
        certification = payload["certification"]

        self.assertEqual(certification["verdict"], "INCOMPLETE")
        self.assertGreaterEqual(certification["canonical_runtime_trace_count"], 1)
        self.assertGreaterEqual(certification["certification_harness_rejected_count"], 1)
        self.assertGreater(payload["bridge_coverage"]["denominator"], payload["bridge_coverage"]["numerator"])

    def test_trace_coverage_uses_authoritative_denominator(self) -> None:
        required = tuple(f"BRIDGE-{idx:02d}" for idx in range(30))
        eligible = tuple(
            result
            for result in execute_tc001_certification(repository_commit="commit-a")["eligibility_results"]
            if result["production_equivalent"]
        )
        synthetic_results = tuple(
            type("Eligible", (), {"subject_id": subject, "production_equivalent": True})()
            for subject in required[:3]
        )
        coverage = self.authority.coverage(required, synthetic_results)

        self.assertEqual(len(eligible), 1)
        self.assertEqual(coverage.denominator, 30)
        self.assertEqual(coverage.numerator, 3)
        self.assertEqual(coverage.percent, 10.0)

    def test_contradiction_detection_blocks_pass_without_equivalence(self) -> None:
        coverage = self.authority.coverage(tuple(f"BRIDGE-{idx:02d}" for idx in range(30)), ())
        contradictions = self.authority.detect_contradictions({"CS-002": {"verdict": "PASS"}}, coverage)

        self.assertTrue(any(item.subject == "CS-002" and item.blocking for item in contradictions))
        self.assertTrue(any(item.subject == "bridge coverage" and item.blocking for item in contradictions))

    def test_cs_regression_verdicts_do_not_overstate_trace_equivalence(self) -> None:
        results = run_all_cs_certifications()

        for order_id in ("CS-002", "CS-003", "CS-005", "CS-006", "CS-007", "CS-009"):
            self.assertEqual(results[order_id]["certification"]["verdict"], CSVerdict.INCOMPLETE.value)


if __name__ == "__main__":
    unittest.main()
