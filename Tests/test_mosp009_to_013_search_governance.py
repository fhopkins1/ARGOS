from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.historian import (  # noqa: E402
    HistoricalInformationCutoff,
    HistorianSearchArchive,
    TemporalEvidenceClassification,
    classify_temporal_evidence,
    historical_record_from_search_evidence,
)
from argos.intelligence import (  # noqa: E402
    BudgetOutcome,
    CacheEntry,
    CacheStatus,
    FailureDoctrineRegistry,
    GovernedSearchRequest,
    SearchBudgetLedger,
    SearchCostClass,
    SearchEvidenceCertificationStatus,
    SearchEvidenceCertifier,
    SearchEvidenceRecord,
    SearchEvidenceRepository,
    SearchFailureClass,
    SearchPriority,
    SearchResourceGovernor,
    WorkflowFailureState,
)
from argos.trader import (  # noqa: E402
    FRESHNESS_LIMIT_SECONDS,
    PROHIBITED_TRADER_ACTIVITIES,
    TraderEligibilityDecision,
    TraderExecutionPackage,
    TraderInformationEligibilityEngine,
    TraderValidationFailure,
)


def execution_package(**overrides) -> TraderExecutionPackage:
    data = {
        "package_id": "TEP-001",
        "workflow_id": "WF-009",
        "workflow_execution_token_id": "WET-009",
        "decision_object_id": "DO-009",
        "execution_authorization_id": "EA-009",
        "risk_approval_id": "RA-009",
        "analyst_approval_id": "AA-009",
        "portfolio_allocation_id": "PA-009",
        "position_size": "100",
        "execution_constraints": {"max_quantity": "100"},
        "price_constraints": {"limit": "100.00"},
        "order_type": "limit",
        "time_in_force": "day",
        "broker_authorization_id": "BA-009",
        "position_identifier": "POS-009",
        "security_identifier": "037833100",
        "account_identifier": "ACCT-PSEUDONYM-001",
        "evidence_package_id": "EP-009",
        "version_identifier": "1.0.0",
        "approval_timestamp": "2026-07-20T12:00:00Z",
        "evidence_freshness": {key: 1 for key in FRESHNESS_LIMIT_SECONDS},
        "source_certification_id": "SC-009",
        "digital_integrity_verified": True,
        "evidence_completeness_status": "COMPLETE",
        "required_signatures": ("Executive", "Analyst", "Risk"),
        "package_expiration": "2026-07-20T12:05:00Z",
        "immutable": True,
        "broker_validations": {"account_active": "PASS", "buying_power_sufficient": "PASS"},
        "market_validations": {"halt_status": "CLEAR"},
    }
    data.update(overrides)
    return TraderExecutionPackage(**data)


def governed_request(**overrides) -> GovernedSearchRequest:
    data = {
        "request_id": "GSR-001",
        "search_plan_id": "CSP-SEC_FILING_METADATA",
        "source_id": "SRC-US-SEC-EDGAR",
        "provider_id": "SEC",
        "requesting_office": "Analyst",
        "workflow_id": "WF-011",
        "decision_object_id": "DO-011",
        "workflow_execution_token_id": "WET-011",
        "environment": "research",
        "asset_class": "equity",
        "identifiers": {"cik": "0000320193"},
        "fact_type": "sec_filing_metadata",
        "retrieval_purpose": "official_filing_retrieval",
        "query_fingerprint": "qfp-sec-aapl",
        "parameters": {"cik": "0000320193"},
        "requested_time_range": ("2026-07-01", "2026-07-20"),
        "requested_freshness_seconds": 300,
        "priority_class": SearchPriority.P3_ACTIVE_TRADE_INVESTIGATIONS,
        "cost_class": SearchCostClass.C1_NEGLIGIBLE_METERED,
        "estimated_cost_units": 5,
        "cache_policy_id": "CACHE-IMMUTABLE-EVIDENCE",
        "cache_isolation_scope": "WF-011",
        "deduplication_policy_id": "DEDUP-QFP",
        "batch_eligible": False,
        "fallback_eligible": False,
        "safety_critical": False,
        "created_at": "2026-07-20T12:00:00Z",
        "expires_at": "2026-07-20T12:05:00Z",
        "evidence_retention_classification": "FULL_DOCUMENT",
    }
    data.update(overrides)
    return GovernedSearchRequest(**data)


def cache_entry(**overrides) -> CacheEntry:
    data = {
        "cache_entry_id": "CACHE-001",
        "source_id": "SRC-US-SEC-EDGAR",
        "provider_id": "SEC",
        "search_plan_id": "CSP-SEC_FILING_METADATA",
        "canonical_query_fingerprint": "qfp-sec-aapl",
        "normalized_request_parameters": {"cik": "0000320193"},
        "fact_type": "sec_filing_metadata",
        "entity_identifiers": {"cik": "0000320193"},
        "requested_time_range": ("2026-07-01", "2026-07-20"),
        "retrieval_timestamp": "2026-07-20T12:00:00Z",
        "freshness_deadline": "2026-07-20T12:05:00Z",
        "hard_expiration_timestamp": "2026-07-20T13:00:00Z",
        "invalidation_tags": ("sec_filing",),
        "environment": "research",
        "cache_isolation_scope": "WF-011",
        "provenance_reference": "PROV-001",
        "raw_evidence_reference": "sha256:raw",
        "response_digest": "sha256:resp",
        "stale_status": CacheStatus.HIT,
        "cost_avoided_units": 5,
    }
    data.update(overrides)
    return CacheEntry(**data)


def evidence_record(**overrides) -> SearchEvidenceRecord:
    data = {
        "search_evidence_id": "SER-001",
        "search_execution_id": "SEXE-001",
        "search_plan_id": "CSP-SEC_FILING_METADATA",
        "search_plan_version": "1.0.0",
        "source_registry_version": "SPREG-2026-07-20-001",
        "requesting_office": "Analyst",
        "executing_office": "Intelligence",
        "workflow_id": "WF-013",
        "workflow_execution_token_id": "WET-013",
        "decision_object_id": "DO-013",
        "investigation_id": "INV-013",
        "parent_search_execution_id": "",
        "correlation_id": "CORR-013",
        "created_at": "2026-07-20T12:00:00Z",
        "finalized_at": "2026-07-20T12:00:02Z",
        "authorized_purpose": "official_filing_retrieval",
        "search_authorization_status": "AUTHORIZED",
        "authorizing_artifact_type": "WorkflowExecutionToken",
        "authorizing_artifact_identifier": "WET-013",
        "requesting_office_authority_result": "AUTHORIZED",
        "executing_office_authority_result": "AUTHORIZED",
        "workflow_authority_validation_result": "AUTHORIZED",
        "approved_source_authorization_result": "AUTHORIZED",
        "approved_retrieval_surface_authorization_result": "AUTHORIZED",
        "authorized_search_depth_limit": 1,
        "authorized_cost_limit": 5,
        "authorized_freshness_requirement_seconds": 300,
        "authorization_rejection_code": "",
        "canonical_source_identifier": "SRC-US-SEC-EDGAR",
        "source_name": "SEC EDGAR",
        "owning_institution": "United States Securities and Exchange Commission",
        "source_classification": "PRIMARY_AUTHORITY",
        "retrieval_surface_identifier": "SURF-US-SEC-SUBMISSIONS",
        "retrieval_location_reference": "https://data.sec.gov/submissions/CIK0000320193.json",
        "retrieval_method": "OFFICIAL_API",
        "source_role_classification": "PRIMARY_AUTHORITY",
        "source_jurisdiction": "US",
        "exact_query_text": "CIK0000320193",
        "normalized_query_text": "cik0000320193",
        "structured_parameters": {"cik": "0000320193"},
        "entity_identifiers": {"cik": "0000320193"},
        "requested_time_range": ("2026-07-01", "2026-07-20"),
        "query_template_identifier": "QRY-SEC-FILING",
        "retrieval_start_timestamp": "2026-07-20T12:00:00Z",
        "retrieval_completion_timestamp": "2026-07-20T12:00:01Z",
        "source_response_timestamp": "2026-07-20T12:00:01Z",
        "source_publication_timestamp": "2026-07-20T11:59:00Z",
        "timezone": "UTC",
        "cache_status": CacheStatus.NOT_USED,
        "cache_key": "",
        "cache_record_identifier": "",
        "cache_age_seconds": 0,
        "attempt_number": 1,
        "total_attempt_count": 1,
        "retry_policy_identifier": "NO_RETRY",
        "fallback_source_identifier": "",
        "transport_status": "OK",
        "protocol_status": "200",
        "source_response_status": "OK",
        "content_type": "application/json",
        "response_size_bytes": 100,
        "record_count": 1,
        "result_count": 1,
        "zero_result_status": False,
        "partial_response_status": False,
        "malformed_response_status": False,
        "response_digest": "sha256:response",
        "canonicalized_response_digest": "sha256:canonical",
        "raw_evidence_reference": "sha256:raw",
        "normalized_evidence_reference": "NORM-001",
        "extraction_manifest_reference": "EXTRACT-001",
        "evidence_storage_integrity_result": "VERIFIED",
        "failure_classification": None,
        "stop_rule_identifier": "AUTHORITATIVE_PRIMARY_FACT_OBTAINED",
        "stop_rule_outcome": "COMPLETE",
        "escalation_outcome": "NONE",
        "monetary_cost_units": 5,
        "retention_class": "FULL_DOCUMENT",
        "legal_hold_status": "NONE",
        "integrity_status": "VERIFIED",
    }
    data.update(overrides)
    return SearchEvidenceRecord(**data)


class MOSP009To013SearchGovernanceTests(unittest.TestCase):
    def test_mosp009_valid_package_executes_and_stale_package_returns_upstream(self) -> None:
        report = TraderInformationEligibilityEngine().evaluate(execution_package())
        self.assertEqual(report.decision, TraderEligibilityDecision.EXECUTE)
        self.assertTrue(report.trade_eligible)

        stale = execution_package(evidence_freshness={key: 1 for key in FRESHNESS_LIMIT_SECONDS} | {"buying_power": 99})
        stale_report = TraderInformationEligibilityEngine().evaluate(stale)
        self.assertIn(TraderValidationFailure.STALE_EVIDENCE, stale_report.failures)
        self.assertEqual(stale_report.decision, TraderEligibilityDecision.RETURN_TO_INTELLIGENCE)

    def test_mosp009_prohibited_trader_search_aborts_workflow(self) -> None:
        self.assertIn("general_web_search", PROHIBITED_TRADER_ACTIVITIES)
        report = TraderInformationEligibilityEngine().prohibit_activity("general_web_search")
        self.assertEqual(report.decision, TraderEligibilityDecision.ABORT_WORKFLOW)
        self.assertIn(TraderValidationFailure.PROHIBITED_TRADER_SEARCH, report.failures)

    def test_mosp011_resource_governor_authorizes_cache_and_blocks_unknown_cost(self) -> None:
        governor = SearchResourceGovernor()
        cached = governor.authorize(governed_request(), cache_entry=cache_entry())
        self.assertEqual(cached.outcome, BudgetOutcome.AUTHORIZED_CACHE_HIT)
        self.assertEqual(cached.cache_status, CacheStatus.HIT)

        unknown = governor.authorize(governed_request(request_id="GSR-UNKNOWN", cost_class=SearchCostClass.UNKNOWN))
        self.assertEqual(unknown.outcome, BudgetOutcome.REJECTED_UNCLASSIFIED_COST)

    def test_mosp011_budget_reservation_blocks_workflow_and_allows_safety_override(self) -> None:
        ledger = SearchBudgetLedger(workflow_limit=5, daily_limit=5, safety_reserve=10)
        governor = SearchResourceGovernor(ledger=ledger)
        authorized = governor.authorize(governed_request(estimated_cost_units=5))
        self.assertEqual(authorized.outcome, BudgetOutcome.AUTHORIZED_EXTERNAL_RETRIEVAL)

        blocked = governor.authorize(governed_request(request_id="GSR-BLOCK", estimated_cost_units=1))
        self.assertEqual(blocked.outcome, BudgetOutcome.BLOCKED_WORKFLOW_BUDGET)

        safety = SearchResourceGovernor(ledger=SearchBudgetLedger(daily_limit=0, safety_reserve=10)).authorize(
            governed_request(request_id="GSR-SAFE", priority_class=SearchPriority.P0_PORTFOLIO_EXECUTION_SAFETY, safety_critical=True, estimated_cost_units=5)
        )
        self.assertEqual(safety.outcome, BudgetOutcome.AUTHORIZED_SAFETY_OVERRIDE)

    def test_mosp012_failure_doctrine_classifies_outages_as_trade_blocking_evidence(self) -> None:
        rule = FailureDoctrineRegistry().classify(SearchFailureClass.BROKER_OUTAGE)
        self.assertEqual(rule.workflow_state, WorkflowFailureState.TRADE_BLOCKED)
        self.assertFalse(rule.trade_eligible)
        self.assertTrue(rule.commander_notification_required)

        unsupported = FailureDoctrineRegistry().classify(SearchFailureClass.UNSUPPORTED_JURISDICTION)
        self.assertEqual(unsupported.required_retry_count, 0)

    def test_mosp013_search_evidence_record_is_required_for_consumable_evidence(self) -> None:
        record = evidence_record()
        self.assertEqual(SearchEvidenceCertifier().certify(record), SearchEvidenceCertificationStatus.CERTIFIED)

        failed = evidence_record(search_evidence_id="SER-FAIL", raw_evidence_reference="", failure_classification=SearchFailureClass.NETWORK_TIMEOUT, source_response_status="TIMEOUT", integrity_status="VERIFIED")
        self.assertEqual(SearchEvidenceCertifier().certify(failed), SearchEvidenceCertificationStatus.CERTIFIED)

        incomplete = evidence_record(search_evidence_id="SER-BAD", raw_evidence_reference="")
        self.assertEqual(SearchEvidenceCertifier().certify(incomplete), SearchEvidenceCertificationStatus.EVIDENCE_INCOMPLETE)

        repository = SearchEvidenceRepository()
        repository.append(record)
        with self.assertRaises(ValueError):
            repository.append(record)

    def test_mosp010_historian_reconstructs_cutoff_without_merging_hindsight(self) -> None:
        record = evidence_record()
        historical = historical_record_from_search_evidence(record)
        archive = HistorianSearchArchive()
        archive.append_search_record(historical)
        cutoff = HistoricalInformationCutoff(
            "CUT-001",
            "WF-013",
            "DO-013",
            "2026-07-20T12:01:00Z",
            "Decision finalized",
            "Historian",
            "WET-013",
            (historical.search_record_id,),
            ("sha256:raw",),
            (),
            (),
            (),
            (),
            (),
            "CERTIFIED",
        )
        archive.freeze_cutoff(cutoff)
        archive.append_temporal_relationship(classify_temporal_evidence("sha256:raw", cutoff, "2026-07-20T11:59:00Z", "2026-07-20T12:00:01Z"))
        archive.append_temporal_relationship(classify_temporal_evidence("sha256:later", cutoff, "2026-07-20T12:05:00Z", "2026-07-20T12:06:00Z"))
        archive.append_temporal_relationship(classify_temporal_evidence("sha256:revision", cutoff, "2026-07-20T12:07:00Z", "2026-07-20T12:08:00Z", revision=True))

        reconstruction = archive.reconstruct("CUT-001")
        self.assertEqual(reconstruction.known_at_decision_time, ("sha256:raw",))
        self.assertEqual(reconstruction.published_after_decision, ("sha256:later",))
        self.assertEqual(reconstruction.later_revisions, ("sha256:revision",))
        self.assertNotEqual(TemporalEvidenceClassification.KNOWN_AT_DECISION_TIME, TemporalEvidenceClassification.LATER_REVISION)


if __name__ == "__main__":
    unittest.main()
