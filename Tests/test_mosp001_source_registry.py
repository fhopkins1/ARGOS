from dataclasses import replace
from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.persistence import InMemoryPersistenceRepository, canonical_schemas  # noqa: E402
from argos.intelligence import (  # noqa: E402
    ApprovedSourceRegistry,
    CostClass,
    FreshnessClass,
    RetrievalMethod,
    SP001RejectionCode,
    SourceAuthorizationDecisionCode,
    SourceAuthorizationGateway,
    SourceAuthorizationRequest,
    SourceAuthorityClass,
    SourceRegistryError,
    SourceRegistrySnapshot,
    SourceStatus,
    SurfaceStatus,
    canonical_source_registry,
    persist_registry_snapshot,
    recover_registry_snapshot,
    registry_conformance_report,
    validate_resolved_destination,
)


def request(**overrides) -> SourceAuthorizationRequest:
    data = {
        "authorization_request_id": "SPREQ-001",
        "workflow_id": "WF-SP-001",
        "workflow_execution_token_id": "WET-SP-001",
        "requesting_office": "Intelligence",
        "requesting_component": "OfficialFilingCollector",
        "request_purpose_code": "official_filing_retrieval",
        "requested_source_id": "SRC-US-SEC-EDGAR",
        "requested_retrieval_surface_id": "SURF-US-SEC-SUBMISSIONS",
        "requested_fact_types": ("regulatory_filing",),
        "requested_fields": ("accession_number", "filing_form", "issuer_identity", "acceptance_timestamp"),
        "asset_class": "equity",
        "instrument_identifiers": ("CIK-0000320193",),
        "jurisdiction": "US",
        "environment": "paper",
        "proposed_retrieval_method": RetrievalMethod.OFFICIAL_API,
        "proposed_cost_class": CostClass.ZERO_MARGINAL_PUBLIC,
        "decision_object_id": "DO-SP-001",
        "requested_at": "2026-07-20T12:00:00Z",
        "final_resolved_url": "https://data.sec.gov/submissions/CIK0000320193.json",
    }
    data.update(overrides)
    return SourceAuthorizationRequest(**data)


class MOSP001SourceRegistryTests(unittest.TestCase):
    def test_canonical_registry_activates_and_exposes_operator_view(self) -> None:
        registry = canonical_source_registry()

        self.assertEqual(registry.version.status.value, "ACTIVE")
        self.assertGreaterEqual(len(registry.snapshot.sources), 10)
        self.assertGreaterEqual(len(registry.snapshot.surfaces), 10)
        operator_view = registry.list_operator_view()
        self.assertIn("credential_state", operator_view[0])
        self.assertNotIn("secret", str(operator_view).lower())

    def test_invalid_registry_rejects_duplicates_digest_mismatch_and_circular_fallback(self) -> None:
        registry = canonical_source_registry()
        with self.assertRaises(SourceRegistryError):
            ApprovedSourceRegistry(SourceRegistrySnapshot(registry.version, registry.snapshot.sources + (registry.snapshot.sources[0],), registry.snapshot.surfaces, registry.snapshot.changes))

        bad_version = replace(registry.version, content_digest="0" * 64)
        with self.assertRaises(SourceRegistryError):
            ApprovedSourceRegistry(SourceRegistrySnapshot(bad_version, registry.snapshot.sources, registry.snapshot.surfaces, registry.snapshot.changes))

        sec = registry.source("SRC-US-SEC-EDGAR")
        bls = registry.source("SRC-US-BLS")
        sources = tuple(
            replace(source, fallback_source_ids=("SRC-US-BLS",)) if source.source_id == sec.source_id else replace(source, fallback_source_ids=("SRC-US-SEC-EDGAR",)) if source.source_id == bls.source_id else source
            for source in registry.snapshot.sources
        )
        version = replace(registry.version, content_digest=registry.snapshot.version.content_digest)
        digest = registry.compute_content_digest()
        version = replace(version, content_digest=digest)
        with self.assertRaises(SourceRegistryError):
            ApprovedSourceRegistry(SourceRegistrySnapshot(version, sources, registry.snapshot.surfaces, registry.snapshot.changes))

    def test_authorized_request_succeeds_and_source_use_evidence_is_retained(self) -> None:
        gateway = SourceAuthorizationGateway()
        decision = gateway.authorize(request())

        self.assertTrue(decision.authorized)
        self.assertEqual(decision.decision, SourceAuthorizationDecisionCode.AUTHORIZED)

        use = gateway.record_source_use(request(), decision, result_status="RETRIEVED", raw_evidence_reference="sha256:abc", response_payload={"accession_number": "0000320193-26-000001"})
        self.assertEqual(use.authorization_decision_reference, decision.authorization_decision_id)
        self.assertEqual(use.registry_version, gateway.registry.version.registry_version)
        self.assertTrue(use.response_digest)

    def test_authorization_denies_office_purpose_environment_fact_field_method_and_token_failures(self) -> None:
        gateway = SourceAuthorizationGateway()
        cases = (
            (request(requesting_office="Trader"), SP001RejectionCode.OFFICE_NOT_AUTHORIZED.value),
            (request(request_purpose_code="unrestricted_research"), SP001RejectionCode.PURPOSE_NOT_AUTHORIZED.value),
            (request(environment="live", requested_source_id="SRC-SEARCH-ENGINE-DISCOVERY", requested_retrieval_surface_id="SURF-SEARCH-DISCOVERY", request_purpose_code="discovery", requested_fact_types=("all",), requested_fields=("discovery_result_url",), proposed_retrieval_method=RetrievalMethod.SEARCH_ENGINE_DISCOVERY, proposed_cost_class=CostClass.LOW_MARGINAL_PUBLIC, final_resolved_url="https://search.example-authority.invalid/search?q=aapl"), SP001RejectionCode.ENVIRONMENT_NOT_AUTHORIZED.value),
            (request(requested_fact_types=("live_price",)), SP001RejectionCode.FACT_TYPE_NOT_AUTHORIZED.value),
            (request(requested_fields=("live_bid",)), SP001RejectionCode.FIELD_NOT_AUTHORIZED.value),
            (request(proposed_retrieval_method=RetrievalMethod.OFFICIAL_WEB_PAGE), SP001RejectionCode.METHOD_NOT_AUTHORIZED.value),
            (request(workflow_execution_token_id=""), SP001RejectionCode.WORKFLOW_TOKEN_INVALID.value),
        )
        for source_request, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                self.assertEqual(gateway.authorize(source_request).decision_code, expected_code)

    def test_source_status_license_and_environment_boundaries_fail_closed(self) -> None:
        gateway = SourceAuthorizationGateway()

        pending_license = request(
            requested_source_id="SRC-LICENSED-SIP-MARKET-DATA",
            requested_retrieval_surface_id="SURF-LICENSED-SIP-API",
            request_purpose_code="market_data_observation",
            requested_fact_types=("subscribed market prices",),
            requested_fields=("last_trade",),
            proposed_retrieval_method=RetrievalMethod.LICENSED_PROVIDER_API,
            proposed_cost_class=CostClass.LICENSED_METERED,
            final_resolved_url="https://sip.market-data/v1/quotes/AAPL",
        )
        self.assertEqual(gateway.authorize(pending_license).decision_code, SP001RejectionCode.SOURCE_NOT_ACTIVE.value)

        paper_broker_live = request(
            requested_source_id="SRC-BROKER-OF-RECORD",
            requested_retrieval_surface_id="SURF-BROKER-PAPER-API",
            requesting_office="Trader",
            request_purpose_code="execution_critical_service",
            requested_fact_types=("accepted orders",),
            requested_fields=("broker_order_acceptance",),
            environment="live",
            proposed_retrieval_method=RetrievalMethod.BROKER_API,
            proposed_cost_class=CostClass.BROKER_INCLUDED,
            final_resolved_url="https://broker.account-api/orders",
        )
        self.assertEqual(gateway.authorize(paper_broker_live).decision_code, SP001RejectionCode.ENVIRONMENT_NOT_AUTHORIZED.value)

    def test_url_surface_validation_rejects_arbitrary_destinations(self) -> None:
        surface = canonical_source_registry().surface("SURF-US-SEC-SUBMISSIONS")

        self.assertIsNone(validate_resolved_destination(surface, "https://data.sec.gov/submissions/CIK0000320193.json"))
        self.assertEqual(validate_resolved_destination(surface, "https://evil.example/submissions/CIK0000320193.json"), SP001RejectionCode.HOST_NOT_AUTHORIZED)
        self.assertEqual(validate_resolved_destination(surface, "https://data.sec.gov/other/CIK0000320193.json"), SP001RejectionCode.PATH_NOT_AUTHORIZED)
        self.assertEqual(validate_resolved_destination(surface, "http://data.sec.gov/submissions/CIK0000320193.json"), SP001RejectionCode.ARBITRARY_URL_BLOCKED)
        self.assertEqual(validate_resolved_destination(surface, "https://user:pass@data.sec.gov/submissions/CIK0000320193.json"), SP001RejectionCode.ARBITRARY_URL_BLOCKED)
        self.assertEqual(validate_resolved_destination(surface, "https://127.0.0.1/submissions/CIK0000320193.json"), SP001RejectionCode.ARBITRARY_URL_BLOCKED)
        self.assertEqual(validate_resolved_destination(surface, "https://data.sec.gov/submissions/CIK0000320193.json", ("https://evil.example/redirect",)), SP001RejectionCode.REDIRECT_NOT_AUTHORIZED)

    def test_discovery_snippet_low_authority_and_model_memory_are_blocked(self) -> None:
        gateway = SourceAuthorizationGateway()

        discovery_snippet = request(
            environment="research",
            requested_source_id="SRC-SEARCH-ENGINE-DISCOVERY",
            requested_retrieval_surface_id="SURF-SEARCH-DISCOVERY",
            request_purpose_code="discovery",
            requested_fact_types=("all",),
            requested_fields=("snippet",),
            proposed_retrieval_method=RetrievalMethod.SEARCH_ENGINE_DISCOVERY,
            proposed_cost_class=CostClass.LOW_MARGINAL_PUBLIC,
            final_resolved_url="https://search.example-authority.invalid/search?q=issuer",
        )
        self.assertEqual(gateway.authorize(discovery_snippet).decision_code, SP001RejectionCode.FIELD_NOT_AUTHORIZED.value)

        early_warning_trade = request(
            environment="research",
            requested_source_id="SRC-SOCIAL-EARLY-WARNING",
            requested_retrieval_surface_id="SURF-SOCIAL-EARLY-WARNING-WEB",
            request_purpose_code="execution_eligibility",
            requested_fact_types=("all",),
            requested_fields=("early_warning_lead",),
            proposed_retrieval_method=RetrievalMethod.BROWSER_DISCOVERY,
            proposed_cost_class=CostClass.LOW_MARGINAL_PUBLIC,
            final_resolved_url="https://social.example-authority.invalid/post/1",
        )
        self.assertEqual(gateway.authorize(early_warning_trade).decision_code, SP001RejectionCode.PURPOSE_NOT_AUTHORIZED.value)

        model_memory = request(
            requested_source_id="SRC-PROHIBITED-MODEL-MEMORY",
            requested_retrieval_surface_id="SURF-PROHIBITED-MODEL-MEMORY",
            request_purpose_code="none",
            requested_fact_types=("none",),
            requested_fields=("none",),
            proposed_retrieval_method=RetrievalMethod.MANUAL_HUMAN_SUBMISSION,
            proposed_cost_class=CostClass.UNKNOWN_COST_PROHIBITED,
            final_resolved_url="https://model-memory.invalid/evidence",
        )
        self.assertEqual(gateway.authorize(model_memory).decision_code, SP001RejectionCode.SOURCE_PROHIBITED.value)

    def test_persistence_recovery_preserves_registry_and_corruption_fails_closed(self) -> None:
        repository = InMemoryPersistenceRepository(canonical_schemas())
        persisted = persist_registry_snapshot(repository)
        recovered = recover_registry_snapshot(persisted)

        self.assertEqual(recovered.version.registry_version, canonical_source_registry().version.registry_version)
        self.assertEqual(recovered.version.content_digest, canonical_source_registry().version.content_digest)

        corrupted_payload = dict(persisted.payload)
        corrupted_snapshot = dict(corrupted_payload["source_registry_snapshot"])
        corrupted_version = dict(corrupted_snapshot["version"])
        corrupted_version["content_digest"] = "bad"
        corrupted_snapshot["version"] = corrupted_version
        corrupted_payload["source_registry_snapshot"] = corrupted_snapshot

        bad_record = repository.persist(persisted.object_type, "SPREG-CORRUPT", corrupted_payload)
        with self.assertRaises(SourceRegistryError):
            recover_registry_snapshot(bad_record)

    def test_registry_validation_blocks_configuration_errors(self) -> None:
        registry = canonical_source_registry()
        bad_source = replace(registry.source("SRC-US-SEC-EDGAR"), permitted_information_fields=())
        sources = tuple(bad_source if item.source_id == bad_source.source_id else item for item in registry.snapshot.sources)
        snapshot = SourceRegistrySnapshot(replace(registry.version, content_digest="temporary"), sources, registry.snapshot.surfaces, registry.snapshot.changes)
        digest = ApprovedSourceRegistry.__new__(ApprovedSourceRegistry)
        digest.snapshot = snapshot
        digest._sources = {source.source_id: source for source in sources}
        digest._surfaces = {surface.retrieval_surface_id: surface for surface in snapshot.surfaces}
        fixed = SourceRegistrySnapshot(replace(registry.version, content_digest=digest.compute_content_digest()), sources, registry.snapshot.surfaces, registry.snapshot.changes)
        with self.assertRaises(SourceRegistryError):
            ApprovedSourceRegistry(fixed)

        active_license = replace(registry.source("SRC-LICENSED-SIP-MARKET-DATA"), source_status=SourceStatus.ACTIVE)
        sources = tuple(active_license if item.source_id == active_license.source_id else item for item in registry.snapshot.sources)
        snapshot = SourceRegistrySnapshot(replace(registry.version, content_digest="temporary"), sources, registry.snapshot.surfaces, registry.snapshot.changes)
        digest.snapshot = snapshot
        digest._sources = {source.source_id: source for source in sources}
        fixed = SourceRegistrySnapshot(replace(registry.version, content_digest=digest.compute_content_digest()), sources, registry.snapshot.surfaces, registry.snapshot.changes)
        with self.assertRaises(SourceRegistryError):
            ApprovedSourceRegistry(fixed)

        discovery_primary = replace(registry.source("SRC-SEARCH-ENGINE-DISCOVERY"), source_status=SourceStatus.ACTIVE, authorized_request_purposes=("execution_eligibility",), authority_class=SourceAuthorityClass.DISCOVERY_ONLY)
        sources = tuple(discovery_primary if item.source_id == discovery_primary.source_id else item for item in registry.snapshot.sources)
        snapshot = SourceRegistrySnapshot(replace(registry.version, content_digest="temporary"), sources, registry.snapshot.surfaces, registry.snapshot.changes)
        digest.snapshot = snapshot
        digest._sources = {source.source_id: source for source in sources}
        fixed = SourceRegistrySnapshot(replace(registry.version, content_digest=digest.compute_content_digest()), sources, registry.snapshot.surfaces, registry.snapshot.changes)
        with self.assertRaises(SourceRegistryError):
            ApprovedSourceRegistry(fixed)

    def test_conformance_report_contains_required_migration_lists(self) -> None:
        report = registry_conformance_report()

        self.assertIn("SRC-LICENSED-SIP-MARKET-DATA", report["inactive_source_candidates"])
        self.assertTrue(report["migration_inventory"])
        self.assertTrue(report["prohibited_or_quarantined_legacy_paths"])


if __name__ == "__main__":
    unittest.main()
