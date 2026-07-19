from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.semantic_drift_engine import (  # noqa: E402
    DriftClassification,
    DriftDomain,
    RecertificationAction,
    compare_semantic_drift,
    demo_request,
    verify_report,
    write_cic06_evidence,
)


def request_for(domain: DriftDomain, before, after):
    baseline = {"repositoryCommit": "1" * 40, "candidateIdentityDigest": "baseline-digest"}
    candidate = {"repositoryCommit": "2" * 40, "candidateIdentityDigest": "candidate-digest"}
    return {
        "comparison_id": f"cmp-{domain.value}",
        "baseline_identity": baseline,
        "candidate_identity": candidate,
        "baseline_manifest": {domain.value: {"object": before}},
        "candidate_manifest": {domain.value: {"object": after}},
        "requested_domains": (domain.value,),
    }


class CIC06SemanticDriftEngineTests(unittest.TestCase):
    def test_all_fourteen_comparators_report_no_drift_for_identical_semantics(self) -> None:
        baseline = {"repositoryCommit": "1" * 40, "candidateIdentityDigest": "baseline-digest"}
        candidate = {"repositoryCommit": "2" * 40, "candidateIdentityDigest": "candidate-digest"}
        manifest = {domain.value: {"stable": True, "items": ("a", "b")} for domain in DriftDomain}
        report = compare_semantic_drift(
            {
                "comparison_id": "cmp-all",
                "baseline_identity": baseline,
                "candidate_identity": candidate,
                "baseline_manifest": manifest,
                "candidate_manifest": manifest,
            }
        )

        self.assertEqual(14, len(report["completedDomains"]))
        self.assertEqual(DriftClassification.NO_DRIFT.value, report["finalDriftClassification"])
        self.assertTrue(report["candidateMayContinueTowardCertification"])

    def test_classification_precedence_for_required_regressions(self) -> None:
        cases = (
            (DriftDomain.LAW_VII_ENFORCEMENT, {"token": "ENFORCED"}, {"token": "REMOVED"}, DriftClassification.LAW_VII_REGRESSION),
            (DriftDomain.SYNTHETIC_TRUTH_REACHABILITY, {"synthetic": "blocked"}, {"synthetic": "reachable"}, DriftClassification.SYNTHETIC_TRUTH_REGRESSION),
            (DriftDomain.TEST_DENOMINATOR, {"test": "required"}, {"test": "skip"}, DriftClassification.CONSTITUTIONAL_REGRESSION),
            (DriftDomain.REPOSITORY_IMPLEMENTATION, {"api_version": "1"}, {"api_version": "2"}, DriftClassification.MAJOR_DRIFT),
            (DriftDomain.REPOSITORY_IMPLEMENTATION, {"doc": "a"}, {"doc": "b"}, DriftClassification.SAFE_DRIFT),
            (DriftDomain.REPOSITORY_IMPLEMENTATION, {"change": "known"}, {"change": "unknown"}, DriftClassification.UNKNOWN_DRIFT),
        )
        for domain, before, after, expected in cases:
            with self.subTest(domain=domain.value):
                report = compare_semantic_drift(request_for(domain, before, after))
                self.assertEqual(expected.value, report["finalDriftClassification"])

    def test_authorization_does_not_suppress_constitutional_regression(self) -> None:
        req = request_for(DriftDomain.LAW_VII_ENFORCEMENT, {"law_vii": "ENFORCED"}, {"law_vii": "REMOVED"})
        req["authorization_context"] = {"issuer": "CertificationGovernanceAuthority", "permittedDomains": ("*",), "candidateIdentityDigest": "*"}
        report = compare_semantic_drift(req)

        self.assertEqual(DriftClassification.LAW_VII_REGRESSION.value, report["finalDriftClassification"])
        self.assertIn(RecertificationAction.REJECT_CANDIDATE.value, report["recertificationPlan"]["actions"])

    def test_invalid_and_mixed_identity_fails_closed(self) -> None:
        req = request_for(DriftDomain.REPOSITORY_IMPLEMENTATION, {}, {})
        req["candidate_identity"] = {"repositoryCommit": "short", "candidateIdentityDigest": ""}
        report = compare_semantic_drift(req)

        self.assertEqual(DriftClassification.INPUT_INVALID.value, report["finalDriftClassification"])
        self.assertFalse(report["candidateMayContinueTowardCertification"])

    def test_report_digest_and_evidence_generation_are_deterministic(self) -> None:
        report = compare_semantic_drift(demo_request(REPOSITORY_ROOT))
        repeated = compare_semantic_drift(demo_request(REPOSITORY_ROOT))
        out = Path(tempfile.mkdtemp(prefix="argos-cic06-evidence-"))
        try:
            manifest = write_cic06_evidence(report, out)
            self.assertTrue((out / "semantic_drift_report.json").exists())
        finally:
            shutil.rmtree(out, ignore_errors=True)

        self.assertEqual(report["reportDigest"], repeated["reportDigest"])
        self.assertTrue(verify_report(report)["valid"])
        self.assertEqual(report["finalDriftClassification"], manifest["finalDriftClassification"])


if __name__ == "__main__":
    unittest.main()

