from decimal import Decimal
from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.intelligence import (  # noqa: E402
    AnalystClaim,
    AnalystClaimClass,
    AnalystDisposition,
    AnalystResolutionEngine,
    BrokerOrderRecord,
    BrokerReconciliationEngine,
    DownsideAsymmetry,
    EvidencePackageService,
    EvidenceRole,
    GovernedRiskSubject,
    HistoricalLayer,
    HistoricalReplayRequest,
    HistorianReplayMode,
    HistorianTruthArchive,
    ImpactSeverity,
    LikelihoodState,
    OrderIntentRecord,
    OrderLifecycleState,
    ProposedExecutionPackage,
    RiskDisposition,
    RiskUncertaintyEngine,
    RiskUncertaintyInput,
    SeekerEvidenceRecord,
    TraderDisposition,
    TraderEvidenceEligibilityEngine,
    UncertaintyState,
    historical_record,
)


def evidence(**overrides) -> SeekerEvidenceRecord:
    data = {
        "evidence_id": "EV-1",
        "observation_id": "OBS-1",
        "source_id": "SRC-1",
        "authority_class": "PRIMARY_AUTHORITY",
        "evidence_role": EvidenceRole.MANDATORY,
        "claim_identity": "CLAIM-1",
        "entity_id": "ISSUER-1",
        "instrument_id": "AAPL",
        "publication_time": "2026-07-20T12:00:00Z",
        "observation_time": "2026-07-20T12:00:00Z",
        "effective_time": "2026-07-20T12:00:00Z",
        "retrieval_time": "2026-07-20T12:01:00Z",
        "source_available": True,
        "provenance_complete": True,
        "normalization_complete": True,
        "identity_verified": True,
        "version_verified": True,
        "fresh": True,
        "independent_origin_id": "ORIGIN-1",
        "raw_evidence_reference": "sha256:ev1",
    }
    data.update(overrides)
    return SeekerEvidenceRecord(**data)


def claim(claim_class=AnalystClaimClass.EARNINGS_CLAIM) -> AnalystClaim:
    return AnalystClaim("CLAIM-1", claim_class, "ISSUER-1", "AAPL", "", "reported", "1.25", "FILED", "USD_PER_SHARE", "USD", "2026-07-20T12:00:00Z", "2026-06-30T23:59:59Z", "US", "NASDAQ", "v1", "q2_eps", "WF-TR", "thesis-required", "materiality-1", "v1")


def intent() -> OrderIntentRecord:
    return OrderIntentRecord("INTENT-1", "WF-TR", "DO-1", "RISK-AUTH", "ACCT-1", "STRAT-1", "AAPL", "BUY", "OPEN", "LIMIT", "DAY", Decimal("10"), Decimal("200"), "USD", "CLIENT-1", "IDEMP-1", "2026-07-20T12:00:00Z", "TOKEN-1", OrderLifecycleState.TRANSMITTED, "2026-07-20T12:00:00Z", ("sha256:intent",))


def broker_order() -> BrokerOrderRecord:
    return BrokerOrderRecord("BORDER-1", "BROKER-1", "ACCT-1", "BROKER-ORDER-1", "CLIENT-1", "INTENT-1", "AAPL", "BUY", Decimal("10"), Decimal("10"), Decimal("0"), None, OrderLifecycleState.BROKER_ACCEPTED, "accepted", "2026-07-20T12:00:02Z", "2026-07-20T12:01:00Z", "sha256:broker", 1, "2026-07-20T12:01:01Z")


class MOTR013To016OfficeDispositionTests(unittest.TestCase):
    def _complete_package_and_decision(self):
        service = EvidencePackageService()
        package = service.create_evidence_package("WF-TR", "earnings", "CLAIM-1")
        package = service.append_observation(package, evidence())
        decision = AnalystResolutionEngine().resolve(claim(), package, workflow_execution_token_id="TOKEN-1")
        return package, decision

    def test_motr013_analyst_returns_incomplete_package_to_seeker(self) -> None:
        package = EvidencePackageService().create_evidence_package("WF-TR", "earnings", "CLAIM-1")
        decision = AnalystResolutionEngine().resolve(claim(), package, workflow_execution_token_id="TOKEN-1")

        self.assertEqual(decision.final_disposition, AnalystDisposition.INSUFFICIENT_EVIDENCE)
        self.assertTrue(decision.seeker_return_required)
        self.assertEqual(decision.trade_consequence, "NO_TRADE_AUTHORITY_GRANTED_BY_ANALYST")

    def test_motr013_causal_claim_does_not_follow_from_event_occurrence(self) -> None:
        package, _ = self._complete_package_and_decision()
        decision = AnalystResolutionEngine().resolve(claim(AnalystClaimClass.CAUSAL_MARKET_CLAIM), package)

        self.assertEqual(decision.final_disposition, AnalystDisposition.INSUFFICIENT_EVIDENCE)
        self.assertIn("causal_mechanism_unproven", decision.limitations)

    def test_motr014_unresolved_legal_or_broker_state_is_ineligible(self) -> None:
        package, decision = self._complete_package_and_decision()
        risk_input = RiskUncertaintyInput("WF-TR", "DO-1", decision, package.package_id, "ACCT-1", "AAPL", "ISSUER-1", "STRAT-1", "PORT-1", "POS-1", ("CLAIM-1",), ("legal",), (GovernedRiskSubject.LEGAL_TRADABILITY,), (UncertaintyState.UNRESOLVED_LEGAL_STATUS,), ImpactSeverity.CRITICAL, LikelihoodState.UNKNOWN_LIKELIHOOD, DownsideAsymmetry.SEVERE_DOWNSIDE_ASYMMETRY, ("sha256:risk",))

        record = RiskUncertaintyEngine().assess(risk_input)

        self.assertEqual(record.risk_disposition, RiskDisposition.INELIGIBLE)
        self.assertIn("constitutional_trade_block", record.restrictions)

    def test_motr014_conflicted_analyst_disposition_becomes_restricted_uncertainty(self) -> None:
        package = EvidencePackageService().create_evidence_package("WF-TR", "news", "CLAIM-1")
        conflicted = AnalystResolutionEngine().resolve(claim(AnalystClaimClass.NEWS_EVENT_CLAIM), package)
        risk_input = RiskUncertaintyInput("WF-TR", "DO-1", conflicted, package.package_id, "ACCT-1", "AAPL", "ISSUER-1", "STRAT-1", "PORT-1", "POS-1", ("CLAIM-1",), ("news",), (GovernedRiskSubject.OTHER_REQUIRED_FACT,), (), ImpactSeverity.MODERATE, LikelihoodState.UNKNOWN_LIKELIHOOD, DownsideAsymmetry.MATERIAL_DOWNSIDE_ASYMMETRY, ("sha256:risk",))

        record = RiskUncertaintyEngine().assess(risk_input)

        self.assertIn(UncertaintyState.MISSING_MANDATORY_EVIDENCE, record.uncertainty_states)
        self.assertEqual(record.risk_disposition, RiskDisposition.ELIGIBLE_WITH_RESTRICTIONS)

    def test_motr015_trader_blocks_before_broker_or_analyst_can_be_bypassed(self) -> None:
        package = ProposedExecutionPackage("EXEC-PKG-1", "WF-TR", True, "TOKEN-1", "Trader", "DO-1", True, "AAPL", "AAPL", "BUY", "BUY", "10", "10", "2000", "2000", None, None, None, True, True, True, True, False, False, False, True, True, False, ("audit",), ("prov",))

        record = TraderEvidenceEligibilityEngine().evaluate(package)

        self.assertEqual(record.final_disposition, TraderDisposition.BROKER_RECONCILIATION_REQUIRED)
        self.assertIn("RETURN_TO_ANALYST:analyst_disposition_missing_or_ineligible", record.reason_codes)

    def test_motr015_clean_package_gets_narrow_execution_authorization(self) -> None:
        package_obj, decision = self._complete_package_and_decision()
        risk = RiskUncertaintyEngine().assess(RiskUncertaintyInput("WF-TR", "DO-1", decision, package_obj.package_id, "ACCT-1", "AAPL", "ISSUER-1", "STRAT-1", "PORT-1", "POS-1", ("CLAIM-1",), ("earnings",), (GovernedRiskSubject.OTHER_REQUIRED_FACT,), (UncertaintyState.NO_MATERIAL_UNCERTAINTY,), ImpactSeverity.NO_IMPACT, LikelihoodState.NOT_APPLICABLE, DownsideAsymmetry.SYMMETRIC, ("sha256:risk",)))
        broker = BrokerReconciliationEngine().reconcile_order(intent(), broker_order(), ())
        execution_package = ProposedExecutionPackage("EXEC-PKG-OK", "WF-TR", True, "TOKEN-1", "Trader", "DO-1", True, "AAPL", "AAPL", "BUY", "BUY", "10", "10", "2000", "2000", decision, risk, broker, True, True, True, True, False, False, False, True, True, False, ("audit",), ("prov",))

        record = TraderEvidenceEligibilityEngine().evaluate(execution_package)

        self.assertEqual(record.final_disposition, TraderDisposition.EXECUTION_ELIGIBLE)
        self.assertTrue(record.execution_authorization_id.startswith("EXECAUTH-"))

    def test_motr016_historical_replay_excludes_later_records(self) -> None:
        archive = HistorianTruthArchive()
        original = historical_record("WF-TR", "CLAIM-1", "earnings", HistoricalLayer.HISTORICAL_KNOWLEDGE, observation_ids=("OBS-OLD",), recorded_at="2026-07-20T12:00:00Z")
        revised = historical_record("WF-TR", "CLAIM-1", "earnings", HistoricalLayer.CURRENT_BEST_SUPPORTED_TRUTH, observation_ids=("OBS-NEW",), recorded_at="2026-07-20T13:00:00Z")
        archive.append_record(original)
        archive.append_record(revised)

        replay = archive.replay(HistoricalReplayRequest("REPLAY-1", "WF-TR", "2026-07-20T12:30:00Z", "MO-TR-016/1.0.0", "earnings", "CLAIM-1", "", "", "", "", HistorianReplayMode.HISTORICAL_KNOWLEDGE, "Auditor", "2026-07-20T14:00:00Z"))

        self.assertIn(original.historical_record_id, replay.included_record_ids)
        self.assertIn(revised.historical_record_id, replay.excluded_later_record_ids)
        self.assertEqual(("OBS-OLD",), replay.known_observations)

    def test_motr016_retroactive_review_never_rewrites_original(self) -> None:
        archive = HistorianTruthArchive()
        original = historical_record("WF-TR", "CLAIM-1", "legal", HistoricalLayer.HISTORICAL_DECISION, decision_ids=("DEC-OLD",), recorded_at="2026-07-20T12:00:00Z")
        new = historical_record("WF-TR", "CLAIM-1", "legal", HistoricalLayer.CURRENT_BEST_SUPPORTED_TRUTH, decision_ids=("DEC-NEW",), uncertainty_ids=("UNC-1",), recorded_at="2026-07-20T13:00:00Z")

        review = archive.retroactive_review(original, new, "later_official_record")

        self.assertTrue(review.would_alter_decision)
        self.assertEqual(review.original_record_id, original.historical_record_id)
        self.assertEqual(original.decision_ids, ("DEC-OLD",))


if __name__ == "__main__":
    unittest.main()
