from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.intelligence import (  # noqa: E402
    EvidenceGraphRepository,
    EvidenceNodeType,
    HumanEscalationEngine,
    HumanReviewClass,
    HumanReviewOutcome,
    HumanReviewState,
    ReconciliationCertificationService,
    ReconciliationCertificationState,
    ReconciliationEvidencePackage,
    ReviewAuthorityRole,
    SourceHealthEvaluationEngine,
    SourceHealthState,
    SourceOperationalRole,
    SourceTelemetryRecord,
    default_source_health_policy,
    evidence_node,
)


def telemetry(**overrides) -> SourceTelemetryRecord:
    data = {
        "telemetry_id": "TEL-1",
        "source_id": "SRC-1",
        "workflow_id": "WF-TR",
        "fact_domain": "market_data",
        "request_timestamp": "2026-07-20T12:00:00Z",
        "response_timestamp": "2026-07-20T12:00:01Z",
        "source_observation_timestamp": "2026-07-20T12:00:00Z",
        "transport_success": True,
        "authentication_success": True,
        "authorization_success": True,
        "timeout": False,
        "rate_limited": False,
        "schema_valid": True,
        "required_fields_present": True,
        "identifiers_valid": True,
        "timestamps_valid": True,
        "fresh": True,
        "duplicate_response": False,
        "frozen_data": False,
        "correction": False,
        "revision": False,
        "authority_conflict": False,
        "numerical_conflict": False,
        "suspected_corruption": False,
        "suspected_manipulation": False,
        "downstream_rejected": False,
        "observation_id": "OBS-1",
        "evidence_references": ("sha256:tel",),
    }
    data.update(overrides)
    return SourceTelemetryRecord(**data)


def package(**overrides) -> ReconciliationEvidencePackage:
    data = {
        "reconciliation_id": "REC-1",
        "reconciliation_attempt_id": "ATT-1",
        "workflow_id": "WF-TR",
        "workflow_execution_token_id": "TOKEN-1",
        "decision_object_id": "DO-1",
        "decision_object_version": "v1",
        "fact_domain": "market_data",
        "claim_id": "CLAIM-1",
        "instrument_id": "AAPL",
        "issuer_id": "ISSUER-1",
        "account_id": "ACCT-1",
        "broker_id": "BROKER-1",
        "office_performing_reconciliation": "Analyst",
        "office_authority_record": "AUTH-1",
        "competing_observation_ids": ("OBS-1", "OBS-2"),
        "competing_observation_hashes": ("hash-1", "hash-2"),
        "raw_evidence_references": ("sha256:raw1", "sha256:raw2"),
        "normalized_observation_references": ("NORM-1", "NORM-2"),
        "observation_identity_record": "ID-1",
        "comparability_record": "COMP-1",
        "source_authority_records": ("AUTH-1",),
        "source_precedence_rule": "primary_authority_prevails",
        "source_independence_record": "INDEP-1",
        "timestamp_governing_rule": "publication_time",
        "version_comparison_record": "VER-1",
        "conflict_classification": "NO_CONFLICT",
        "conflict_record_id": "CONF-1",
        "applicable_reconciliation_rule": "RULE-1",
        "doctrine_version": "MO-TR-019/1.0.0",
        "rule_version": "RULE-1",
        "intermediate_dispositions": ("PACKAGE_COMPLETE", "VERIFIED"),
        "final_reconciliation_disposition": "VERIFIED",
        "risk_consequence": "ELIGIBLE",
        "trader_consequence": "EXECUTION_ELIGIBLE",
        "resolution_state": "FINAL",
        "created_time": "2026-07-20T12:00:00Z",
        "finalized_time": "2026-07-20T12:01:00Z",
        "replay_id": "REPLAY-1",
        "audit_id": "AUDIT-1",
    }
    data.update(overrides)
    return ReconciliationEvidencePackage(**data)


def complete_graph() -> EvidenceGraphRepository:
    graph = EvidenceGraphRepository()
    for node_type in (
        EvidenceNodeType.RAW_OBSERVATION,
        EvidenceNodeType.AUTHORITY_RECORD,
        EvidenceNodeType.SOURCE_INDEPENDENCE_RECORD,
        EvidenceNodeType.CONFLICT_RECORD,
        EvidenceNodeType.RISK_DECISION,
        EvidenceNodeType.TRADER_ELIGIBILITY_DECISION,
    ):
        graph.append_node(evidence_node(node_type, node_type.value, {"node": node_type.value}))
    return graph


class MOTR017To019CertificationControlsTests(unittest.TestCase):
    def test_motr017_corruption_quarantines_source_and_blocks_execution_sensitive_use(self) -> None:
        policy = default_source_health_policy()
        records = (
            telemetry(telemetry_id="TEL-1"),
            telemetry(telemetry_id="TEL-2", suspected_corruption=True, evidence_references=("sha256:corrupt",)),
            telemetry(telemetry_id="TEL-3"),
        )

        record = SourceHealthEvaluationEngine().evaluate("SRC-1", SourceHealthState.HEALTHY, policy, records)

        self.assertEqual(record.new_health_state, SourceHealthState.QUARANTINED)
        self.assertIn(SourceOperationalRole.FORENSIC_ONLY_SOURCE, record.eligibility_changes)
        self.assertEqual(record.trade_consequence, "block_execution_sensitive_use")
        self.assertTrue(record.human_review_required)

    def test_motr017_insufficient_window_cannot_be_called_healthy(self) -> None:
        policy = default_source_health_policy()
        record = SourceHealthEvaluationEngine().evaluate("SRC-1", SourceHealthState.UNKNOWN_HEALTH, policy, (telemetry(),))

        self.assertEqual(record.new_health_state, SourceHealthState.UNKNOWN_HEALTH)
        self.assertIn(SourceOperationalRole.PROHIBITED_SOURCE, record.eligibility_changes)

    def test_motr018_case_requires_trigger_records_except_system_classes(self) -> None:
        engine = HumanEscalationEngine()

        with self.assertRaises(ValueError):
            engine.create_case(HumanReviewClass.LEGAL_CONFLICT_REVIEW, "WF-TR", "DO-1", ())

        case = engine.create_case(HumanReviewClass.CONSTITUTIONAL_AMBIGUITY_REVIEW, "WF-TR", "DO-1", ())
        self.assertEqual(case.review_state, HumanReviewState.REVIEW_REQUESTED)

    def test_motr018_rejects_unauthorized_or_contradictory_human_outcomes(self) -> None:
        engine = HumanEscalationEngine()
        case = engine.create_case(HumanReviewClass.LEGAL_CONFLICT_REVIEW, "WF-TR", "DO-1", ("REG-1",))

        decision = engine.issue_decision(
            case,
            "reviewer-1",
            ReviewAuthorityRole.AUTHORIZED_RISK_REVIEWER,
            (HumanReviewOutcome.AUTOMATED_PROCESS_MAY_RESUME, HumanReviewOutcome.AUTOMATED_PROCESS_REMAINS_BLOCKED),
            ("sha256:review",),
        )

        self.assertEqual(decision.decision_state, HumanReviewState.DECISION_REJECTED)
        self.assertIn("reviewer_role_not_authorized", decision.reason_codes)
        self.assertIn("contradictory_outcomes", decision.reason_codes)

    def test_motr019_certifies_complete_evidence_chain(self) -> None:
        record = ReconciliationCertificationService().certify(package(), complete_graph())

        self.assertEqual(record.certification_state, ReconciliationCertificationState.CERTIFIED)
        self.assertEqual(record.reason_codes, ("certification_complete",))

    def test_motr019_missing_evidence_chain_fails_before_success(self) -> None:
        graph = EvidenceGraphRepository()
        incomplete = package(raw_evidence_references=(), source_independence_record="")

        record = ReconciliationCertificationService().certify(incomplete, graph)

        self.assertEqual(record.certification_state, ReconciliationCertificationState.EVIDENCE_INCOMPLETE)
        self.assertTrue(any("EVIDENCE_CHAIN_INCOMPLETE" in reason for reason in record.reason_codes))

    def test_motr019_certification_precedence_flags_unauthorized_before_incomplete(self) -> None:
        record = ReconciliationCertificationService().certify(package(office_performing_reconciliation="UnauthorizedOffice", raw_evidence_references=()), complete_graph())

        self.assertEqual(record.certification_state, ReconciliationCertificationState.UNAUTHORIZED_ACTION)
        self.assertIn("UNAUTHORIZED_ACTION:office_not_authorized", record.reason_codes)


if __name__ == "__main__":
    unittest.main()
