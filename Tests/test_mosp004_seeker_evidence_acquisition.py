from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.seeker import (  # noqa: E402
    AssetIdentity,
    EvidenceState,
    InvestigationAuthorization,
    InvestigationClass,
    RetrievalResult,
    SeekerEvidenceAcquisitionEngine,
    SeekerEvidenceError,
    SeekerInvestigationRequest,
    SourceRole,
    StaticEvidenceRetriever,
    TerminationReason,
    build_queries,
    investigation_plan,
    resolve_entity,
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


def authorization(authorized: bool = True) -> InvestigationAuthorization:
    return InvestigationAuthorization("IA-MOSP004-001", authorized, "Sentinel", "2026-07-20T12:00:00Z")


def request(**overrides) -> SeekerInvestigationRequest:
    data = {
        "investigation_id": "INV-MOSP004-001",
        "workflow_id": "WF-MOSP004-001",
        "workflow_execution_token_id": "WET-MOSP004-001",
        "investigation_authorization": authorization(),
        "requesting_office": "Sentinel",
        "decision_object_id": "DO-MOSP004-001",
        "asset": asset(),
        "investigation_class": InvestigationClass.SEC_FILING,
        "date_range": ("2026-07-13", "2026-07-20"),
        "environment": "research",
    }
    data.update(overrides)
    return SeekerInvestigationRequest(**data)


def result(source_id: str, purpose: str, document: str = "DOC-1") -> tuple[str, RetrievalResult]:
    return (
        f"{source_id}:{purpose}",
        RetrievalResult(
            EvidenceState.COLLECTED,
            {"document": document, "source": source_id, "purpose": purpose},
            "2026-07-20T12:00:00Z",
            document,
            f"https://evidence.local/{document}",
            f"sha256:{document}",
        ),
    )


class MOSP004SeekerEvidenceAcquisitionTests(unittest.TestCase):
    def test_every_investigation_class_has_deterministic_distinct_plan(self) -> None:
        plans = {klass: investigation_plan(klass) for klass in InvestigationClass}

        self.assertEqual(set(plans), set(InvestigationClass))
        for klass, plan in plans.items():
            with self.subTest(klass=klass.value):
                self.assertTrue(plan.primary_sources)
                self.assertTrue(plan.contrary_evidence_sources)
                self.assertTrue(plan.negative_search_sources)
                self.assertEqual(investigation_plan(klass), plan)

    def test_authority_and_entity_resolution_are_required(self) -> None:
        engine = SeekerEvidenceAcquisitionEngine()
        with self.assertRaises(SeekerEvidenceError):
            engine.acquire(request(workflow_execution_token_id=""))
        with self.assertRaises(SeekerEvidenceError):
            engine.acquire(request(investigation_authorization=authorization(False)))

        unresolved = engine.acquire(request(asset=AssetIdentity(issuer_name="Apple Inc.", ticker="AAPL")))
        self.assertEqual(unresolved.entity_resolution.status, "UNKNOWN_ENTITY")
        self.assertEqual(unresolved.termination_reason, TerminationReason.HUMAN_ESCALATION_REQUIRED)

    def test_query_construction_and_duplicate_elimination_are_reproducible(self) -> None:
        req = request()
        entity = resolve_entity(req.asset)
        plan = investigation_plan(req.investigation_class)

        first = build_queries(req, entity, plan)
        second = build_queries(req, entity, plan)

        self.assertEqual(first, second)
        self.assertEqual(len(first), len({query.query_id for query in first}))
        self.assertIn("AAPL", first[0].query_terms)
        self.assertIn("SEC_FILING", first[0].query_terms)

    def test_acquisition_executes_mandatory_negative_and_contrary_searches_with_provenance(self) -> None:
        retriever = StaticEvidenceRetriever(
            dict(
                [
                    result("SRC-US-SEC-EDGAR", "official_filing_retrieval", "SEC-PRIMARY"),
                    result("SRC-ISSUER-IR", "official_issuer_release_retrieval", "ISSUER-CORROBORATION"),
                    result("SRC-US-SEC-ENFORCEMENT", "adversarial_review", "SEC-CONTRARY"),
                ]
            )
        )
        package = SeekerEvidenceAcquisitionEngine(retriever=retriever).acquire(request())

        self.assertEqual(package.evidence_completeness_status, "COMPLETE")
        self.assertEqual(package.termination_reason, TerminationReason.MANDATORY_SOURCES_COMPLETE)
        self.assertTrue(package.evidence_hash)
        self.assertTrue(package.collected_documents)
        self.assertTrue(package.contrary_evidence)
        self.assertTrue(package.negative_searches)
        self.assertTrue(package.source_provenance)
        self.assertTrue(any(event.event_type == "evidence_package_generation" for event in package.audit_events))

        payload = str(package)
        self.assertNotIn("recommendation", payload.lower())
        self.assertNotIn("risk_score", payload.lower())
        self.assertNotIn("trade", payload.lower())

    def test_authorization_failure_records_unavailable_search_without_silent_recovery(self) -> None:
        package = SeekerEvidenceAcquisitionEngine().acquire(request(environment="live"))

        self.assertEqual(package.evidence_completeness_status, "INCOMPLETE")
        self.assertEqual(package.termination_reason, TerminationReason.REQUIRED_SOURCE_UNAVAILABLE)
        self.assertTrue(package.unavailable_searches)
        self.assertEqual(package.unavailable_searches[0].state, EvidenceState.NOT_FOUND)

    def test_budget_enforcement_terminates_deterministically(self) -> None:
        retriever = StaticEvidenceRetriever(
            dict(
                [
                    result("SRC-US-SEC-EDGAR", "official_filing_retrieval", "SEC-PRIMARY"),
                    result("SRC-ISSUER-IR", "official_issuer_release_retrieval", "ISSUER-CORROBORATION"),
                    result("SRC-US-SEC-ENFORCEMENT", "adversarial_review", "SEC-CONTRARY"),
                ]
            )
        )
        package = SeekerEvidenceAcquisitionEngine(retriever=retriever).acquire(request(budget_query_count=1))

        self.assertEqual(package.termination_reason, TerminationReason.BUDGET_EXHAUSTED)
        self.assertEqual(package.evidence_completeness_status, "INCOMPLETE")
        self.assertEqual(package.search_cost.query_count, 1)

    def test_broker_investigation_is_paper_only_and_uses_broker_authority(self) -> None:
        req = request(
            investigation_class=InvestigationClass.BROKER_DISCREPANCY,
            environment="paper",
            asset=AssetIdentity(issuer_name="Broker Account", ticker="ACCOUNT", cusip="ACCT-001", cik="ACCT-001", exchange="BROKER", asset_class="cash"),
        )
        package = SeekerEvidenceAcquisitionEngine(
            retriever=StaticEvidenceRetriever(dict([result("SRC-BROKER-OF-RECORD", "account_reconciliation", "BROKER-RECON")]))
        ).acquire(req)

        self.assertEqual(package.executed_search_plan.primary_sources[0].source_id, "SRC-BROKER-OF-RECORD")
        self.assertTrue(package.collected_documents)

        live_package = SeekerEvidenceAcquisitionEngine().acquire(req.__class__(**{**req.__dict__, "environment": "live"}))
        self.assertEqual(live_package.termination_reason, TerminationReason.AUTHORITY_REJECTED)

    def test_contrary_and_negative_sources_are_not_skipped_when_primary_exists(self) -> None:
        package = SeekerEvidenceAcquisitionEngine(
            retriever=StaticEvidenceRetriever(dict([result("SRC-ISSUER-IR", "official_issuer_release_retrieval", "ISSUER-PRIMARY")]))
        ).acquire(request(investigation_class=InvestigationClass.MERGER))

        roles = [query.source_role for query in package.executed_queries]
        self.assertIn(SourceRole.PRIMARY, roles)
        self.assertIn(SourceRole.MANDATORY_CORROBORATING, roles)
        self.assertIn(SourceRole.CONTRARY, roles)
        self.assertIn(SourceRole.NEGATIVE, roles)


if __name__ == "__main__":
    unittest.main()
