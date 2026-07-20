from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    AnalystVerificationEngine,
    AnalystVerificationRequest,
    CausalComponent,
    VerificationOutcome,
    VerificationQuestionID,
    verification_question_registry,
)
from argos.intelligence import (  # noqa: E402
    CanonicalSearchEngine,
    CanonicalSearchError,
    CanonicalSearchPlanRegistry,
    CanonicalSearchRequest,
    CanonicalSearchStatus,
    default_fact_types,
)
from argos.risk import (  # noqa: E402
    HoldingPeriodClass,
    ProposedTradeRiskContext,
    RiskAdversarialSearchExecutor,
    RiskSearchApplicabilityEngine,
    RiskSearchOutcome,
    UNIVERSAL_RISK_DOMAINS,
)
from argos.seeker import (  # noqa: E402
    AssetIdentity,
    EvidenceState,
    InvestigationAuthorization,
    InvestigationClass,
    RetrievalResult,
    SeekerEvidenceAcquisitionEngine,
    SeekerInvestigationRequest,
    StaticEvidenceRetriever,
)
from argos.trader import (  # noqa: E402
    BrokerEnvironment,
    BrokerInformationGateway,
    BrokerInformationState,
    BrokerRetrievalOperation,
    BrokerRetrievalRequest,
    ReconciliationSeverity,
    default_account_reference,
    default_broker_identity,
    reconcile_broker_truth,
)


def asset() -> AssetIdentity:
    return AssetIdentity(
        issuer_name="Apple Inc.",
        ticker="AAPL",
        cusip="037833100",
        cik="0000320193",
        exchange="NASDAQ",
        industry="Consumer Electronics",
        sector="Technology",
        aliases=("Apple",),
    )


def seeker_request(investigation_class: InvestigationClass = InvestigationClass.EARNINGS_ANNOUNCEMENT) -> SeekerInvestigationRequest:
    return SeekerInvestigationRequest(
        "INV-MOSP005-001",
        "WF-MOSP005-001",
        "WET-MOSP005-001",
        InvestigationAuthorization("IA-MOSP005-001", True, "Sentinel", "2026-07-20T12:00:00Z"),
        "Sentinel",
        "DO-MOSP005-001",
        asset(),
        investigation_class,
        ("2026-07-13", "2026-07-20"),
        "research",
    )


def retrieval(source_id: str, purpose: str, payload: dict[str, str]) -> tuple[str, RetrievalResult]:
    return (
        f"{source_id}:{purpose}",
        RetrievalResult(
            EvidenceState.COLLECTED,
            payload,
            "2026-07-20T12:00:00Z",
            f"DOC-{source_id}",
            f"https://evidence.local/{source_id}",
            f"sha256:{source_id}",
        ),
    )


def evidence_package():
    retriever = StaticEvidenceRetriever(
        dict(
            [
                retrieval("SRC-ISSUER-IR", "official_issuer_release_retrieval", {"earnings_release": "official", "reported_earnings_values": "official", "publication_timestamp": "2026-07-20T12:00:00Z"}),
                retrieval("SRC-US-SEC-EDGAR", "official_filing_retrieval", {"accession_number": "0000320193-26-000001", "filing_form": "8-K", "issuer_identity": "Apple Inc.", "acceptance_timestamp": "2026-07-20T12:00:00Z"}),
                retrieval("SRC-US-SEC-ENFORCEMENT", "adversarial_review", {"release_number": "NONE", "action_date": "2026-07-20", "respondent": "Apple Inc.", "official_url": "https://www.sec.gov/enforcement/search/aapl", "publication_timestamp": "2026-07-20T12:00:00Z"}),
            ]
        )
    )
    return SeekerEvidenceAcquisitionEngine(retriever=retriever).acquire(seeker_request())


class MOSP005To008SearchDoctrineTests(unittest.TestCase):
    def test_mosp007_resolves_one_canonical_plan_per_registered_fact_type_without_generic_default(self) -> None:
        registry = CanonicalSearchPlanRegistry()

        self.assertEqual(len(registry.all_plans()), len(default_fact_types()))
        self.assertEqual(registry.resolve("sec_filing_metadata").search_plan_id, "CSP-SEC_FILING_METADATA")
        with self.assertRaises(CanonicalSearchError):
            registry.resolve("general_web_search")

    def test_mosp007_search_request_fails_closed_on_missing_identifier_and_denies_unlicensed_market_data(self) -> None:
        engine = CanonicalSearchEngine()
        missing = engine.certify_request(
            CanonicalSearchRequest(
                "CSR-001",
                "WF-CSP-001",
                "WET-CSP-001",
                "DO-CSP-001",
                "Analyst",
                "sec_filing_metadata",
                "research",
                {"asset_class": "equity", "jurisdiction": "US"},
            )
        )
        self.assertEqual(missing.terminal_status, CanonicalSearchStatus.INVALID_IDENTIFIER)

        market = engine.certify_request(
            CanonicalSearchRequest(
                "CSR-002",
                "WF-CSP-001",
                "WET-CSP-001",
                "DO-CSP-001",
                "Risk",
                "latest_price",
                "paper",
                {"security_id": "037833100", "venue": "NASDAQ", "asset_class": "equity", "jurisdiction": "US"},
            )
        )
        self.assertEqual(market.terminal_status, CanonicalSearchStatus.AUTHORITY_DENIED)
        self.assertIn("SP001_SOURCE_NOT_ACTIVE", market.failure_reason)

    def test_mosp005_analyst_verification_uses_registered_questions_and_gap_records(self) -> None:
        package = evidence_package()
        engine = AnalystVerificationEngine()
        report = engine.verify(
            AnalystVerificationRequest(
                "AVR-001",
                "WF-MOSP005-001",
                "WET-MOSP005-001",
                "DO-MOSP005-001",
                "CLAIM-EARNINGS-001",
                VerificationQuestionID.EARNINGS_VERIFICATION,
                package,
            )
        )

        self.assertEqual(set(verification_question_registry()), set(VerificationQuestionID))
        self.assertEqual(report.outcome, VerificationOutcome.VERIFIED)
        self.assertEqual(report.plan.source_retrieval_order, ("SRC-ISSUER-IR", "SRC-US-SEC-EDGAR"))
        self.assertTrue(report.audit_records)

        gap_report = engine.verify(
            AnalystVerificationRequest(
                "AVR-002",
                "WF-MOSP005-001",
                "WET-MOSP005-001",
                "DO-MOSP005-001",
                "CLAIM-EARNINGS-002",
                VerificationQuestionID.GUIDANCE_VERIFICATION,
                package,
                material_capital_exposure=True,
            )
        )
        self.assertEqual(gap_report.outcome, VerificationOutcome.ESCALATE_TO_RISK)
        self.assertTrue(gap_report.gap_records)

    def test_mosp005_causal_claims_are_decomposed_not_collapsed(self) -> None:
        package = evidence_package()
        report = AnalystVerificationEngine().verify(
            AnalystVerificationRequest(
                "AVR-003",
                "WF-MOSP005-001",
                "WET-MOSP005-001",
                "DO-MOSP005-001",
                "CLAIM-CAUSAL-001",
                VerificationQuestionID.CAUSAL_CLAIM_VERIFICATION,
                package,
            )
        )

        self.assertIsNotNone(report.causal_decomposition)
        self.assertIn(CausalComponent.OBSERVED_FACT, report.causal_decomposition.components)
        self.assertIn(CausalComponent.DEMONSTRATED_CAUSATION, report.causal_decomposition.components)
        self.assertEqual(report.outcome, VerificationOutcome.RETURN_TO_SEEKER)

    def test_mosp006_risk_plan_includes_universal_searches_and_missing_observations_block_completion(self) -> None:
        context = ProposedTradeRiskContext(
            "WF-RISK-001",
            "WET-RISK-001",
            "DO-RISK-001",
            "ORD-RISK-001",
            "CIK0000320193",
            "AAPL",
            "037833100",
            "NASDAQ",
            "equity",
            "equity",
            "long",
            100,
            20000,
            0.12,
            HoldingPeriodClass.OVERNIGHT,
            1.0,
            False,
            thesis_claims=("earnings momentum",),
        )
        plan = RiskSearchApplicabilityEngine().plan(context)

        domains = {item.risk_domain for item in plan.mandatory_searches}
        self.assertTrue(set(UNIVERSAL_RISK_DOMAINS).issubset(domains))
        self.assertTrue(plan.conditional_searches_activated)
        result = RiskAdversarialSearchExecutor().execute(plan, {"current_liquidity": RiskSearchOutcome.RISK_ACCEPTABLE})
        self.assertEqual(result.terminal_outcome, RiskSearchOutcome.EVIDENCE_INCOMPLETE)
        self.assertIn("current_bid_ask_spread", result.incomplete_domains)

    def test_mosp008_broker_observations_require_authorized_plan_environment_and_raw_evidence(self) -> None:
        broker = default_broker_identity()
        account = default_account_reference()
        request = BrokerRetrievalRequest(
            "BRQ-001",
            f"BRP-{BrokerRetrievalOperation.BUYING_POWER.value.upper()}",
            "WF-BROKER-001",
            "WET-BROKER-001",
            "DO-BROKER-001",
            "Trader",
            broker,
            account,
            {"internal_order_id": "ORD-001"},
        )
        gateway = BrokerInformationGateway()

        incomplete = gateway.observe(request, {"buying_power": "100000", "broker_timestamp": "2026-07-20T12:00:00Z"})
        self.assertEqual(incomplete.response_status, BrokerInformationState.INCOMPLETE)

        observed = gateway.observe(request, {"buying_power": "100000", "broker_timestamp": "2026-07-20T12:00:00Z"}, raw_evidence_reference="sha256:broker")
        self.assertEqual(observed.response_status, BrokerInformationState.OBSERVED_CURRENT)

        analyst_request = BrokerRetrievalRequest(**{**request.__dict__, "requesting_office": "Analyst"})
        denied = gateway.observe(analyst_request, {"buying_power": "100000"}, raw_evidence_reference="sha256:broker")
        self.assertEqual(denied.response_status, BrokerInformationState.UNKNOWN)

    def test_mosp008_reconciliation_creates_explicit_mismatch_record(self) -> None:
        record = reconcile_broker_truth(
            environment=BrokerEnvironment.PAPER,
            broker_id="BROKER-PAPER",
            account_pseudonym="ACCT-PSEUDONYM-001",
            internal_facts={"position_quantity": 100},
            broker_facts={"position_quantity": 75},
            evidence_references=("sha256:broker",),
        )

        self.assertEqual(record.severity, ReconciliationSeverity.HIGH)
        self.assertEqual(record.trade_eligibility_effect, "BLOCK_NEW_ORDER")
        self.assertTrue(record.field_level_mismatches)


if __name__ == "__main__":
    unittest.main()
