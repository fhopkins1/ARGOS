from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.intelligence import (  # noqa: E402
    AuditStatus,
    AuthorityRegistry,
    CollectionRequest,
    ConstitutionalViolation,
    FreshnessStatus,
    IntegrityState,
    ProvenanceState,
    RetrievalEvidence,
    ScheduleRule,
    SourceRecord,
    TriggerClass,
    TruthDomain,
    build_audit_record,
    build_constitutional_charter,
    build_provenance_record,
    create_observation,
    default_authority_registry,
    evaluate_integrity,
    evaluate_schedule,
    export_audit_package,
    normalize_observation,
    route_fact,
)


def market_request() -> CollectionRequest:
    return CollectionRequest(
        request_id="REQ-INT-001",
        truth_domain=TruthDomain.MARKET_PRICES,
        trigger=TriggerClass.PERIODIC,
        workflow_id="WF-INT-001",
        source_id="AUTH-NASDAQ-CTA-PRICE",
    )


def retrieval(payload: dict | None = None, *, integrity_status: str = "PASS") -> RetrievalEvidence:
    return RetrievalEvidence(
        retrieval_session_id="RET-INT-001",
        method="api",
        endpoint="sip.market-data",
        request_identifier="REQWIRE-001",
        response_identifier="RESPWIRE-001",
        collection_started_at="2026-07-20T14:30:00Z",
        retrieval_completed_at="2026-07-20T14:30:01Z",
        publication_time="2026-07-20T14:30:00Z",
        effective_time="2026-07-20T14:30:00Z",
        authority_time="2026-07-20T14:30:00Z",
        receipt_time="2026-07-20T14:30:01Z",
        storage_time="2026-07-20T14:30:02Z",
        transport_status="PASS",
        authentication_status="PASS",
        integrity_status=integrity_status,
        raw_payload=payload
        or {
            "schema": "Market Price",
            "security_id": "US0378331005",
            "isin": "US0378331005",
            "security_type": "equity",
            "exchange": "NASDAQ",
            "market_identifier": "XNAS",
            "ticker": "AAPL",
            "primary_listing": "XNAS",
            "publication_time": "2026-07-20T14:30:00Z",
            "effective_time": "2026-07-20T14:30:00Z",
            "price": "211.45",
            "currency": "USD",
            "quantity": "100",
            "unit": "shares",
            "precision": "0.01",
        },
        signature_reference="SIG-INT-001",
        sequence_identifier="SEQ-INT-001",
    )


class EOINTConstitutionalIntelligenceTests(unittest.TestCase):
    def test_charter_exposes_only_acquisition_contracts(self) -> None:
        charter = build_constitutional_charter()

        self.assertIn("Validated Observation", charter.output_contracts)
        self.assertIn("trade", charter.prohibited_authority)
        self.assertNotIn("Risk Report", charter.output_contracts)

    def test_authority_registry_has_one_primary_per_domain_and_rejects_duplicate_primary(self) -> None:
        registry = default_authority_registry()
        self.assertEqual(registry.resolve(TruthDomain.MARKET_PRICES).source_id, "AUTH-NASDAQ-CTA-PRICE")

        duplicate_source = SourceRecord(
            **{
                **registry.sources[0].__dict__,
                "source_id": "AUTH-DUPLICATE-PRICE",
            }
        )
        with self.assertRaises(ConstitutionalViolation):
            AuthorityRegistry("AIR-BAD", "test", registry.sources + (duplicate_source,))

    def test_observation_creation_fails_closed_for_unauthorized_and_synthetic_payloads(self) -> None:
        unauthorized = create_observation(
            CollectionRequest("REQ-UNAUTH", TruthDomain.MARKET_PRICES, TriggerClass.PERIODIC, "WF", authorized=False),
            retrieval(),
        )
        self.assertTrue(unauthorized.failure_id.startswith("OF-"))

        synthetic = create_observation(market_request(), retrieval({"security_id": "dummy-security", "ticker": "DEMO"}))
        self.assertTrue(synthetic.failure_id.startswith("OF-"))
        self.assertIn("synthetic", synthetic.reason)

    def test_observation_provenance_normalization_integrity_routing_and_audit_are_deterministic(self) -> None:
        observation = create_observation(market_request(), retrieval())
        self.assertEqual(observation.metadata.observation_state.value, "COLLECTED")

        provenance = build_provenance_record(observation, retrieval())
        self.assertEqual(provenance.state, ProvenanceState.VALID)

        fact = normalize_observation(observation, provenance)
        self.assertEqual(fact.exchange, "XNAS")
        self.assertEqual(fact.currency, "USD")
        self.assertEqual(fact.validation_status, "PASS")

        integrity_state, stages, quarantine = evaluate_integrity(observation, provenance)
        self.assertEqual(integrity_state, IntegrityState.VERIFIED)
        self.assertIsNone(quarantine)
        self.assertEqual(stages[0]["stage"], "Transport Integrity Verification")

        routing = route_fact(fact, integrity_state, provenance)
        self.assertEqual(routing.destination, "Sentinel")
        self.assertEqual(routing.sentinel_wake_decision, "WAKE")

        audit = build_audit_record(observation, provenance, fact, routing, integrity_state, retrieval())
        self.assertEqual(audit.certification_status, AuditStatus.CERTIFIED)
        self.assertEqual(audit.destination_office, "Sentinel")
        self.assertGreaterEqual(len(audit.lineage), 10)

        exported_once = export_audit_package((audit,))
        exported_twice = export_audit_package((audit,))
        self.assertEqual(exported_once["package_digest"], exported_twice["package_digest"])

    def test_integrity_detects_corruption_duplicates_replay_and_quarantines(self) -> None:
        observation = create_observation(market_request(), retrieval())
        provenance = build_provenance_record(observation, retrieval())

        state, _, quarantine = evaluate_integrity(
            observation,
            provenance,
            known_observation_ids=(observation.metadata.observation_id,),
        )
        self.assertEqual(state, IntegrityState.DUPLICATE)
        self.assertIsNotNone(quarantine)
        self.assertEqual(quarantine.constitutional_violation, "DUPLICATE")

        state, _, quarantine = evaluate_integrity(observation, provenance, freshness=FreshnessStatus.EXPIRED)
        self.assertEqual(state, IntegrityState.STALE)
        self.assertIsNotNone(quarantine)

    def test_scheduler_is_rule_bound_and_has_no_random_backoff(self) -> None:
        rule = ScheduleRule(
            rule_id="SCH-MARKET-PRICE",
            authority_domain=TruthDomain.MARKET_PRICES,
            source_id="AUTH-NASDAQ-CTA-PRICE",
            trigger_type=TriggerClass.PERIODIC,
            polling_interval_seconds=5,
            preferred_freshness_seconds=1,
            maximum_freshness_seconds=5,
            expiration_threshold_seconds=30,
            retry_policy=(5, 15, 45, 135, 405),
            escalation_policy="quarantine_after_threshold",
            market_session_applicability=("Pre-Market", "Regular Session", "Post-Market"),
            cost_tier=2,
            workflow_authorization_required=True,
            rule_version="EO-INT-006/1.0.0",
            evidence_reference="EV-SCH-001",
        )

        record = evaluate_schedule(
            rule,
            trigger=TriggerClass.PERIODIC,
            workflow_id="WF-INT-001",
            market_session="Regular Session",
            retry_count=2,
            now_utc="2026-07-20T14:30:00Z",
        )

        self.assertEqual(record.outcome, "COLLECT")
        self.assertEqual(record.retry_count, 2)
        self.assertEqual(rule.retry_policy, (5, 15, 45, 135, 405))

    def test_reference_domains_bypass_sentinel(self) -> None:
        request = CollectionRequest(
            request_id="REQ-INT-REF",
            truth_domain=TruthDomain.SENTIMENT,
            trigger=TriggerClass.PERIODIC,
            workflow_id="WF-INT-REF",
            source_id="AUTH-NEWSWIRE-OFFICIAL",
        )
        observation = create_observation(request, retrieval())
        provenance = build_provenance_record(observation, retrieval())
        fact = normalize_observation(observation, provenance)
        integrity_state, _, _ = evaluate_integrity(observation, provenance)
        routing = route_fact(fact, integrity_state, provenance)

        self.assertEqual(routing.destination, "Archive")
        self.assertEqual(routing.sentinel_wake_decision, "DO_NOT_WAKE")


if __name__ == "__main__":
    unittest.main()
