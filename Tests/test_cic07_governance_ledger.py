from dataclasses import replace
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.certification_governance_ledger import (  # noqa: E402
    CertificationGovernanceLedger,
    CertificationStatus,
    GovernanceAction,
    GovernanceCommand,
    GovernanceErrorCode,
    build_audit_export,
    sample_authority,
    sample_decision,
    verify_audit_export,
    verify_ledger_integrity,
    write_cic07_evidence,
)
from argos.control_panel.semantic_drift_engine import DriftClassification


class CIC07GovernanceLedgerTests(unittest.TestCase):
    def test_valid_issuance_appends_entry_and_projection_is_rebuildable(self) -> None:
        ledger = CertificationGovernanceLedger()
        decision = sample_decision()
        command = GovernanceCommand("issue-1", GovernanceAction.ISSUE, decision.certification_id, CertificationStatus.ISSUED, decision, sample_authority(GovernanceAction.ISSUE))
        result = ledger.apply(command)
        current = ledger.query_current(decision.certification_id)

        self.assertEqual("COMMITTED", result["status"])
        self.assertEqual(CertificationStatus.ISSUED.value, current["status"])
        self.assertTrue(current["presentlyUsable"])
        self.assertTrue(ledger.verify_integrity()["valid"])

    def test_constitutional_failure_blocks_issuance_but_is_recorded(self) -> None:
        ledger = CertificationGovernanceLedger()
        decision = sample_decision(constitutional="FAIL")
        result = ledger.apply(GovernanceCommand("issue-fail", GovernanceAction.ISSUE, decision.certification_id, CertificationStatus.ISSUED, decision, sample_authority(GovernanceAction.ISSUE)))

        self.assertEqual("FAIL", result["status"])
        self.assertIn(GovernanceErrorCode.CONSTITUTIONAL_FAILURE.value, result["failureCodes"])
        self.assertEqual(1, len(ledger.entries))

    def test_revocation_preserves_issuance_history(self) -> None:
        ledger = CertificationGovernanceLedger()
        decision = sample_decision()
        authority = sample_authority(GovernanceAction.ISSUE, GovernanceAction.REVOKE)
        ledger.apply(GovernanceCommand("issue-1", GovernanceAction.ISSUE, decision.certification_id, CertificationStatus.ISSUED, decision, authority))
        ledger.apply(GovernanceCommand("revoke-1", GovernanceAction.REVOKE, decision.certification_id, CertificationStatus.REVOKED, decision, authority, reason_code="evidence-quarantine"))

        self.assertEqual(2, len(ledger.timeline(decision.certification_id)))
        self.assertEqual(CertificationStatus.REVOKED.value, ledger.query_current(decision.certification_id)["status"])

    def test_invalid_reactivation_idempotency_and_conflicts_fail_closed(self) -> None:
        ledger = CertificationGovernanceLedger()
        decision = sample_decision()
        authority = sample_authority(GovernanceAction.ISSUE, GovernanceAction.EXPIRE)
        issue = GovernanceCommand("issue-1", GovernanceAction.ISSUE, decision.certification_id, CertificationStatus.ISSUED, decision, authority)
        ledger.apply(issue)
        same = ledger.apply(issue)
        conflict = ledger.apply(replace(issue, decision=replace(decision, rule_version="2")))
        ledger.apply(GovernanceCommand("expire-1", GovernanceAction.EXPIRE, decision.certification_id, CertificationStatus.EXPIRED, decision, authority))
        reactivate = ledger.apply(GovernanceCommand("reactivate", GovernanceAction.ISSUE, decision.certification_id, CertificationStatus.ISSUED, decision, authority))

        self.assertEqual("ALREADY_APPLIED", same["status"])
        self.assertIn(GovernanceErrorCode.IDEMPOTENCY_CONFLICT.value, conflict["failureCodes"])
        self.assertIn(GovernanceErrorCode.INVALID_TRANSITION.value, reactivate["failureCodes"][0])

    def test_tamper_and_export_digest_detection(self) -> None:
        ledger = CertificationGovernanceLedger()
        decision = sample_decision()
        ledger.apply(GovernanceCommand("issue-1", GovernanceAction.ISSUE, decision.certification_id, CertificationStatus.ISSUED, decision, sample_authority(GovernanceAction.ISSUE)))
        entries = [dict(item) for item in ledger.entries]
        entries[0]["resulting_status"] = CertificationStatus.REVOKED.value
        export = ledger.audit_export()
        tampered_export = {**export, "scope": "tampered"}

        self.assertFalse(verify_ledger_integrity(entries)["valid"])
        self.assertTrue(verify_audit_export(export)["valid"])
        self.assertFalse(verify_audit_export(tampered_export)["valid"])

    def test_drift_blocks_issuance_and_evidence_export_is_written(self) -> None:
        ledger = CertificationGovernanceLedger()
        decision = sample_decision(drift=DriftClassification.LAW_VII_REGRESSION.value)
        result = ledger.apply(GovernanceCommand("issue-drift", GovernanceAction.ISSUE, decision.certification_id, CertificationStatus.ISSUED, decision, sample_authority(GovernanceAction.ISSUE)))
        out = Path(tempfile.mkdtemp(prefix="argos-cic07-evidence-"))
        try:
            manifest = write_cic07_evidence(build_audit_export(ledger.entries), out)
            self.assertTrue((out / "governance_audit_export.json").exists())
        finally:
            shutil.rmtree(out, ignore_errors=True)

        self.assertIn(GovernanceErrorCode.DRIFT_DISQUALIFYING.value, result["failureCodes"])
        self.assertEqual("PASS", manifest["verdict"])


if __name__ == "__main__":
    unittest.main()
