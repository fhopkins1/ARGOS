from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import (  # noqa: E402
    ControlledAuthoritativeMarketDataProvider,
    MarketDataFreshnessPolicy,
    MarketDataDecisionGuard,
    MarketDataEvidenceStore,
    MarketDataFreshnessStatus,
    MarketDataGateway,
    MarketDataFreshnessPolicy,
    MarketDataProofDomain,
    MarketDataProviderAbstractionLayer,
    MarketDataProviderRequest,
    MarketDataProviderResult,
    MarketDataRejectionCode,
    MarketDataResultStatus,
    MarketObservationType,
    NonProductionMarketDataProvider,
    ProviderAuthorityClass,
    ProviderAuthorityRecord,
    ProviderAuthorityRegistry,
    evaluate_freshness,
    production_reachability_report,
)
from argos.trader import (  # noqa: E402
    DeterministicPaperBrokerage,
    OrderManagementOffice,
    PaperBrokerAccount,
    PaperBrokerOrderTicket,
    PaperBrokerRejectionCode,
    PaperBrokerMarketDataAdapter,
)
from argos.control_panel import EnterpriseCommunicationsBus, PerformanceTruthEngine, WorkflowExecutionToken  # noqa: E402
from argos.foundation.audit import AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptRepository  # noqa: E402


NOW = "2026-07-18T22:00:00Z"


def quote(symbol: str = "AAPL", last: str = "197.125") -> dict[str, str]:
    return {
        "symbol": symbol,
        "bid": "197.12",
        "ask": "197.13",
        "last": last,
        "volume": "100000",
        "venue": "NASDAQ",
        "source_timestamp_utc": NOW,
        "adjustment_status": "UNADJUSTED",
    }


def market_status() -> dict[str, str]:
    return {"symbol": "MARKET", "status": "PAPER_OPEN", "venue": "US", "source_timestamp_utc": NOW}


def authoritative_record(provider_id: str = "auth-paper") -> ProviderAuthorityRecord:
    return ProviderAuthorityRecord(
        provider_id,
        "Authoritative Test Adapter",
        "ControlledAuthoritativeMarketDataProvider",
        ProviderAuthorityClass.AUTHORITATIVE_EXTERNAL,
        (MarketDataProofDomain.PAPER_AUTHORITATIVE,),
        (MarketObservationType.QUOTE, MarketObservationType.MARKET_STATUS),
        ("US",),
        ("test_supplied_payload",),
        True,
    )


def gateway(provider_id: str = "auth-paper", observations: dict[str, dict[str, str]] | None = None) -> MarketDataGateway:
    return MarketDataGateway(
        registry=ProviderAuthorityRegistry((authoritative_record(provider_id),)),
        providers={provider_id: ControlledAuthoritativeMarketDataProvider(provider_id, observations or {"AAPL": quote(), "MARKET": market_status()})},
        freshness_policy=MarketDataFreshnessPolicy("EO-DJ-TEST-FRESHNESS", "1", maximum_age_seconds=86400, expire_after_seconds=172800),
    )


def config() -> ConfigurationService:
    return ConfigurationService.load({"environment": "integration_testing", "config_version": "1.0.0", "schema_version": "1.0.0", "log_level": "INFO", "live_trading_enabled": False, "feature_flags": {}, "secret_references": []}, {})


def decision(observation_id: str = "") -> dict[str, object]:
    return {
        "decisionObjectId": "DO-EO-DJ",
        "office": "Trader",
        "sourceSystem": "Trader",
        "executionMode": "PAPER",
        "truthClassification": "PAPER_OPERATIONAL",
        "certificationStatus": "PAPER_OPERATIONAL_CERTIFIED",
        "marketEvidenceReference": observation_id,
        "materialFieldProvenance": {
            "asset_identifier": "AAPL",
            "asset_class": "equity",
            "direction": "buy",
            "thesis": "EO-DJ boundary test",
            "evidence": "authorized test boundary evidence",
            "market_context": observation_id or "missing",
            "entry_conditions": "broker executable",
            "price_source": observation_id or "missing",
            "quantity": "1",
            "position_sizing_basis": "cash",
            "confidence": "0.7",
            "time_horizon": "day",
            "risk_factors": "documented",
            "stop_conditions": "documented",
            "exit_conditions": "documented",
            "expected_return": "0.01",
            "risk_approval": "Authorized office judgment",
            "trader_authorization": "Authorized office judgment",
        },
    }


def ticket(observation_id: str = "") -> PaperBrokerOrderTicket:
    return PaperBrokerOrderTicket("ORD-EO-DJ", "WF-EO-DJ", "MISSION-EO-DJ", "DO-EO-DJ", "TOK-EO-DJ", "Trader", "ACCT-PAPER-001", "AAPL", "equity", "buy", 1.0, "market", "day", risk_approval_id="RISK", policy_approval_id="POLICY", decision_object=decision(observation_id))


def token() -> WorkflowExecutionToken:
    return WorkflowExecutionToken("WF-EO-DJ", "Trader", "Executive", "Performance Truth", "Trader", 3600, 10.0, ("broker_order",), "TOK-EO-DJ", NOW, 4, "Executing")


class EODJMarketDataBoundaryTests(unittest.TestCase):
    def test_provider_authority_rejects_nonproduction_for_paper_and_duplicates(self) -> None:
        ProviderAuthorityRegistry((authoritative_record(),))
        live_only = ProviderAuthorityRecord("live-only", "Live", "Adapter", ProviderAuthorityClass.AUTHORITATIVE_EXTERNAL, (MarketDataProofDomain.LIVE_AUTHORITATIVE,), (MarketObservationType.QUOTE,), ("US",), (), True)
        registry = ProviderAuthorityRegistry((live_only,))
        _record, rejection = registry.resolve("live-only", MarketDataProofDomain.PAPER_AUTHORITATIVE, MarketObservationType.QUOTE)
        self.assertEqual(rejection, MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_AUTHORIZED)
        with self.assertRaises(ValueError):
            ProviderAuthorityRegistry((authoritative_record("dup"), authoritative_record("dup")))
        with self.assertRaises(ValueError):
            ProviderAuthorityRegistry((ProviderAuthorityRecord("bad-test", "Bad", "Fixture", ProviderAuthorityClass.TEST_FIXTURE, (MarketDataProofDomain.PAPER_AUTHORITATIVE,), (MarketObservationType.QUOTE,), ("TEST",), (), True),))

    def test_missing_provider_and_mock_names_fail_closed(self) -> None:
        layer = MarketDataProviderAbstractionLayer()
        result = layer.get_quote("AAPL", NOW)
        self.assertIsNone(result["normalizedObject"])
        self.assertEqual(result["auditRecord"]["rejectionCode"], MarketDataRejectionCode.MARKET_DATA_PROVIDER_NOT_CONFIGURED.value)
        report = production_reachability_report()
        self.assertFalse(report["mockFallbackEnabled"])
        self.assertFalse(report["syntheticFallbackEnabled"])
        self.assertEqual(report["productionReachableSyntheticSources"], ())

    def test_replay_test_and_development_providers_cannot_enter_paper_gateway(self) -> None:
        for provider_id, cls, domain in (
            ("replay", ProviderAuthorityClass.REPLAY_INPUT, MarketDataProofDomain.REPLAY),
            ("test", ProviderAuthorityClass.TEST_FIXTURE, MarketDataProofDomain.TEST),
            ("dev", ProviderAuthorityClass.DEVELOPMENT_SIMULATION, MarketDataProofDomain.DEVELOPMENT_SIMULATION),
        ):
            registry = ProviderAuthorityRegistry((ProviderAuthorityRecord(provider_id, provider_id, "NonProductionMarketDataProvider", cls, (domain,), (MarketObservationType.QUOTE,), ("TEST",), (), True),))
            gw = MarketDataGateway(registry=registry, providers={provider_id: NonProductionMarketDataProvider(provider_id, domain, {"AAPL": quote()})})
            result = gw.request_observation(provider_id=provider_id, proof_domain=MarketDataProofDomain.PAPER_AUTHORITATIVE, symbol="AAPL", observation_type=MarketObservationType.QUOTE, requested_at_utc=NOW)
            self.assertFalse(result.accepted)
            self.assertEqual(result.rejection_code, MarketDataRejectionCode.MARKET_DATA_SYNTHETIC_SOURCE_REJECTED)

    def test_observation_identity_idempotency_conflict_and_precision(self) -> None:
        gw = gateway()
        first = gw.request_observation(provider_id="auth-paper", proof_domain=MarketDataProofDomain.PAPER_AUTHORITATIVE, symbol="AAPL", observation_type=MarketObservationType.QUOTE, requested_at_utc=NOW)
        second = gw.request_observation(provider_id="auth-paper", proof_domain=MarketDataProofDomain.PAPER_AUTHORITATIVE, symbol="AAPL", observation_type=MarketObservationType.QUOTE, requested_at_utc=NOW)
        self.assertTrue(first.accepted)
        self.assertEqual(first.observation.observation_id, second.observation.observation_id)
        self.assertEqual(first.observation.normalized_payload["last"], "197.125")
        changed = gateway(observations={"AAPL": quote(last="198.125"), "MARKET": market_status()})
        changed.evidence_store = gw.evidence_store
        conflict = changed.request_observation(provider_id="auth-paper", proof_domain=MarketDataProofDomain.PAPER_AUTHORITATIVE, symbol="AAPL", observation_type=MarketObservationType.QUOTE, requested_at_utc=NOW)
        self.assertFalse(conflict.accepted)
        self.assertEqual(conflict.rejection_code, MarketDataRejectionCode.MARKET_DATA_CONFLICT)

    def test_freshness_policy_is_auditable_and_fail_closed(self) -> None:
        policy = MarketDataFreshnessPolicy("TEST-POLICY", "1", maximum_age_seconds=60, expire_after_seconds=300)
        self.assertEqual(evaluate_freshness(NOW, NOW, policy).classification, MarketDataFreshnessStatus.FRESH)
        self.assertEqual(evaluate_freshness("2026-07-18T21:58:00Z", NOW, policy).classification, MarketDataFreshnessStatus.STALE)
        self.assertEqual(evaluate_freshness("2026-07-18T21:00:00Z", NOW, policy).classification, MarketDataFreshnessStatus.EXPIRED)
        self.assertEqual(evaluate_freshness("", NOW, policy).classification, MarketDataFreshnessStatus.UNKNOWN)

    def test_decision_guard_rejects_bad_domains_stale_mismatch_and_hash_corruption(self) -> None:
        gw = gateway()
        accepted = gw.request_observation(provider_id="auth-paper", proof_domain=MarketDataProofDomain.PAPER_AUTHORITATIVE, symbol="AAPL", observation_type=MarketObservationType.QUOTE, requested_at_utc=NOW)
        guard = MarketDataDecisionGuard(gw.evidence_store, gw.registry)
        self.assertTrue(guard.validate(accepted.observation.observation_id, accepted_proof_domains=(MarketDataProofDomain.PAPER_AUTHORITATIVE,), instrument_id="AAPL", observation_type=MarketObservationType.QUOTE).accepted)
        self.assertEqual(guard.validate("UNKNOWN", accepted_proof_domains=(MarketDataProofDomain.PAPER_AUTHORITATIVE,), instrument_id="AAPL", observation_type=MarketObservationType.QUOTE).rejection_code, MarketDataRejectionCode.MARKET_DATA_OBSERVATION_NOT_FOUND)
        self.assertEqual(guard.validate(accepted.observation.observation_id, accepted_proof_domains=(MarketDataProofDomain.PAPER_AUTHORITATIVE,), instrument_id="MSFT", observation_type=MarketObservationType.QUOTE).rejection_code, MarketDataRejectionCode.MARKET_DATA_INSTRUMENT_MISMATCH)
        store = MarketDataEvidenceStore()
        corrupted = accepted.observation.__class__(**{**accepted.observation.__dict__, "deterministic_hash": "bad"})
        store.persist(corrupted)
        self.assertEqual(MarketDataDecisionGuard(store, gw.registry).validate(corrupted.observation_id, accepted_proof_domains=(MarketDataProofDomain.PAPER_AUTHORITATIVE,), instrument_id="AAPL", observation_type=MarketObservationType.QUOTE).rejection_code, MarketDataRejectionCode.MARKET_DATA_INTEGRITY_FAILURE)

    def test_recovery_does_not_reconstruct_missing_evidence(self) -> None:
        store = MarketDataEvidenceStore()
        guard = MarketDataDecisionGuard(store, ProviderAuthorityRegistry((authoritative_record(),)))
        result = guard.validate("MISSING", accepted_proof_domains=(MarketDataProofDomain.PAPER_AUTHORITATIVE,), instrument_id="AAPL", observation_type=MarketObservationType.QUOTE)
        self.assertFalse(result.accepted)
        self.assertEqual(result.rejection_code, MarketDataRejectionCode.MARKET_DATA_OBSERVATION_NOT_FOUND)

    def test_end_to_end_paper_ingress_and_broker_path_uses_authorized_observation(self) -> None:
        layer = MarketDataProviderAbstractionLayer(gateway=gateway(), provider_id="auth-paper")
        quote_response = layer.get_quote("AAPL", NOW, workflow_id="WF-EO-DJ", decision_object_id="DO-EO-DJ")
        observation_id = quote_response["normalizedObject"]["observationId"]
        guard = MarketDataDecisionGuard(layer.gateway.evidence_store, layer.gateway.registry)
        self.assertTrue(guard.validate(observation_id, accepted_proof_domains=(MarketDataProofDomain.PAPER_AUTHORITATIVE,), instrument_id="AAPL", observation_type=MarketObservationType.QUOTE).accepted)
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        broker = DeterministicPaperBrokerage(
            order_management=OrderManagementOffice(config(), persistence, audit, PromptRepository()),
            performance_truth=PerformanceTruthEngine(),
            communications_bus=EnterpriseCommunicationsBus(),
            market_data=PaperBrokerMarketDataAdapter(layer),
            account=PaperBrokerAccount("ACCT-PAPER-001", 100000.0),
        )
        result = broker.submit_order(ticket(observation_id), workflow_token=token())
        self.assertTrue(result.accepted)
        self.assertEqual(result.order.status, "settled")
        self.assertEqual(result.order.market_state.replay_identifier, observation_id)

    def test_default_paper_broker_rejects_without_authoritative_provider(self) -> None:
        persistence = InMemoryPersistenceRepository(canonical_schemas())
        audit = AuditService()
        broker = DeterministicPaperBrokerage(
            order_management=OrderManagementOffice(config(), persistence, audit, PromptRepository()),
            performance_truth=PerformanceTruthEngine(),
            communications_bus=EnterpriseCommunicationsBus(),
            account=PaperBrokerAccount("ACCT-PAPER-001", 100000.0),
        )
        result = broker.submit_order(ticket(), workflow_token=token())
        self.assertFalse(result.accepted)
        self.assertEqual(result.rejection_code, PaperBrokerRejectionCode.MARKET_DATA_UNAVAILABLE.value)


if __name__ == "__main__":
    unittest.main()
