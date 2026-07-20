from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.intelligence import (  # noqa: E402
    AuthorityFailureOutcome,
    AuthorityObservation,
    AuthorityResolutionEngine,
    AuthorityRole,
    AuthorityStatus,
    ConflictClassificationEngine,
    ConflictClassificationInput,
    ConflictClass,
    LineageRelationshipType,
    ObservationRecord,
    ObservationRelationshipClassification,
    ObservationRelationshipEngine,
    PrecedenceEvaluator,
    PrecedenceOutcome,
    RevisionRelationshipType,
    TemporalObservation,
    TemporalTruthArchive,
    TimestampPrecision,
    VersionStatus,
    make_revision_relationship,
    make_temporal_envelope,
    timestamp,
    validate_temporal_envelope,
)


def authority_observation(**overrides) -> AuthorityObservation:
    data = {
        "observation_id": "OBS-AUTH-1",
        "fact_domain": "sec_filing",
        "source_id": "SRC-US-SEC-EDGAR",
        "instrument_id": "037833100",
        "issuer_id": "0000320193",
        "account_id": "",
        "market_venue": "NASDAQ",
        "jurisdiction": "US",
        "observation_timestamp": "2026-07-20T12:00:00Z",
        "publication_timestamp": "2026-07-20T12:00:00Z",
        "effective_timestamp": "2026-07-20T12:00:00Z",
        "retrieval_timestamp": "2026-07-20T12:01:00Z",
        "revision_status": "ORIGINAL",
        "complete": True,
        "current": True,
        "evidence_references": ("sha256:auth",),
    }
    data.update(overrides)
    return AuthorityObservation(**data)


def observation(**overrides) -> ObservationRecord:
    data = {
        "observation_id": "OBS-1",
        "workflow_id": "WF-TR",
        "collection_event_id": "COLL-1",
        "source_record_id": "SRC-US-SEC-EDGAR",
        "source_institution_id": "SEC",
        "source_publication_id": "PUB-1",
        "source_channel_id": "API",
        "source_url_or_locator": "https://data.sec.gov/submissions/CIK0000320193.json",
        "source_document_id": "DOC-1",
        "upstream_origin_id": "ORIGIN-SEC-1",
        "upstream_vendor_id": "",
        "raw_evidence_reference": "sha256:raw-1",
        "content_hash": "hash-1",
        "semantic_payload_hash": "sem-1",
        "retrieval_timestamp": "2026-07-20T12:00:00Z",
        "publication_timestamp": "2026-07-20T11:59:00Z",
        "observation_timestamp": "2026-07-20T11:59:00Z",
        "effective_timestamp": "2026-07-20T11:59:00Z",
        "revision_timestamp": "",
        "entity_identifiers": {"cik": "0000320193"},
        "instrument_identifiers": {"cusip": "037833100"},
        "account_identifiers": {},
        "event_identifiers": {"event": "earnings"},
        "document_identifiers": {"accession": "0000320193-26-000001"},
        "fact_domain": "reported_earnings",
        "claim_scope": "q2_eps",
        "value_type": "number",
        "raw_value": "1.25",
        "normalized_value": "1.25",
        "unit": "USD_PER_SHARE",
        "currency": "USD",
        "scale": "ones",
        "adjustment_basis": "GAAP",
        "reporting_basis": "diluted_eps",
        "version_identifier": "v1",
        "version_state": "ORIGINAL",
        "session_identifier": "",
        "market_venue": "NASDAQ",
        "reporting_period": "2026Q2",
        "provenance_status": "CERTIFIED",
        "lineage_status": "CERTIFIED",
        "created_at": "2026-07-20T12:00:00Z",
        "created_by_office": "Intelligence",
        "record_version": "1.0.0",
    }
    data.update(overrides)
    return ObservationRecord(**data)


def temporal_observation(obs_id: str, value: str, version: VersionStatus, recorded_at: str, publication: str) -> TemporalObservation:
    envelope = make_temporal_envelope(
        publication_time=timestamp(publication, precision=TimestampPrecision.SECOND, source_field="publication_time"),
        retrieval_time=timestamp(recorded_at, source_field="retrieval_time"),
        effective_time=timestamp("2026-07-20T12:00:00Z", source_field="effective_time"),
        revision_time=timestamp(publication, source_field="revision_time") if version in {VersionStatus.CORRECTED, VersionStatus.REVISED} else timestamp(),
        system_recorded_time=timestamp(recorded_at, source_field="system_recorded_time"),
    )
    return TemporalObservation(obs_id, "FACT-AAPL-EPS", "0000320193", "037833100", "", "reported_earnings", value, envelope, version, "SRC-ISSUER-IR", f"sha256:{obs_id}", recorded_at)


class MOTR001To004TruthReconciliationTests(unittest.TestCase):
    def test_motr001_authority_resolution_is_domain_scoped_and_precedence_preserves_evidence(self) -> None:
        engine = AuthorityResolutionEngine()
        sec = authority_observation()
        det = engine.resolve(sec, "Analyst", "WF-TR")

        self.assertEqual(det.authority_role, AuthorityRole.PRIMARY_RECORD_AUTHORITY)
        self.assertEqual(det.authority_status, AuthorityStatus.AUTHORITATIVE_WITH_SCOPE_LIMIT)

        broker_wrong_domain = authority_observation(observation_id="OBS-AUTH-2", source_id="SRC-BROKER-OF-RECORD", evidence_references=("sha256:broker",))
        broker_det = engine.resolve(broker_wrong_domain, "Analyst", "WF-TR")
        self.assertEqual(broker_det.authority_status, AuthorityStatus.INELIGIBLE)

        decision = PrecedenceEvaluator(engine).evaluate((sec, broker_wrong_domain), "WF-TR", "Analyst")
        self.assertEqual(decision.outcome, PrecedenceOutcome.OFFICIAL_RECORD_PREVAILS)
        self.assertEqual(decision.selected_observation_id, "OBS-AUTH-1")

    def test_motr001_conflicting_primary_authorities_escalate_without_silent_selection(self) -> None:
        first = authority_observation(observation_id="OBS-AUTH-1", evidence_references=("sha256:one",))
        second = authority_observation(observation_id="OBS-AUTH-2", evidence_references=("sha256:two",))
        decision = PrecedenceEvaluator().evaluate((first, second), "WF-TR", "Analyst")

        self.assertEqual(decision.outcome, PrecedenceOutcome.CONFLICTING_PRIMARY_AUTHORITIES)
        self.assertEqual(decision.trade_consequence, AuthorityFailureOutcome.MARK_CONFLICTED)

    def test_motr002_relationship_classification_never_counts_same_origin_as_independent(self) -> None:
        left = observation(observation_id="OBS-1")
        right = observation(observation_id="OBS-2", content_hash="hash-2", semantic_payload_hash="sem-2", source_document_id="DOC-2")
        evaluation = ObservationRelationshipEngine().evaluate(left, right, claim_identifier="CLAIM-EPS")

        self.assertEqual(evaluation.classification, ObservationRelationshipClassification.SAME_ORIGIN)
        self.assertEqual(evaluation.independence_status, "NOT_INDEPENDENT")

        independent = observation(observation_id="OBS-3", content_hash="hash-3", semantic_payload_hash="sem-3", source_record_id="SRC-ISSUER-IR", source_institution_id="ISSUER", upstream_origin_id="ORIGIN-ISSUER-1", source_document_id="DOC-3")
        indep_eval = ObservationRelationshipEngine().evaluate(left, independent, claim_identifier="CLAIM-EPS")
        self.assertEqual(indep_eval.classification, ObservationRelationshipClassification.INDEPENDENT)

    def test_motr002_wrong_dimensions_prevent_comparison(self) -> None:
        left = observation()
        wrong_unit = observation(observation_id="OBS-UNIT", unit="CENTS_PER_SHARE", normalized_value="125")
        wrong_entity = observation(observation_id="OBS-ENTITY", entity_identifiers={"cik": "0000789019"})

        engine = ObservationRelationshipEngine()
        self.assertEqual(engine.evaluate(left, wrong_unit, claim_identifier="CLAIM").classification, ObservationRelationshipClassification.WRONG_UNIT)
        self.assertEqual(engine.evaluate(left, wrong_entity, claim_identifier="CLAIM").classification, ObservationRelationshipClassification.WRONG_ENTITY)

    def test_motr003_conflict_classification_assigns_one_class_and_replays(self) -> None:
        left = observation(observation_id="OBS-1", normalized_value="1.25", semantic_payload_hash="sem-a")
        right = observation(observation_id="OBS-2", normalized_value="1.50", semantic_payload_hash="sem-b", source_record_id="SRC-ISSUER-IR", source_institution_id="ISSUER", upstream_origin_id="ORIGIN-ISSUER-1")
        relationship = ObservationRelationshipEngine().evaluate(left, right, claim_identifier="CLAIM-EPS")
        engine = ConflictClassificationEngine()
        result = engine.classify(ConflictClassificationInput(left, right, "reported_earnings", relationship, "NORMALIZED", "PRIMARY_AUTHORITY", "MATCH", "WF-TR", "DO-TR", "Analyst"))

        self.assertEqual(result.conflict_class, ConflictClass.MATERIAL_NUMERICAL_CONFLICT)
        record = engine.repository.get(result.conflict_identifier)
        self.assertEqual(engine.replay(record, left, right, relationship), ConflictClass.MATERIAL_NUMERICAL_CONFLICT)

    def test_motr003_missing_input_classifies_unknown_without_inference(self) -> None:
        result = ConflictClassificationEngine().classify(ConflictClassificationInput(None, observation(), "reported_earnings", None, "", "", "", "WF-TR", "DO-TR", "Analyst"))
        self.assertEqual(result.conflict_class, ConflictClass.UNKNOWN)
        self.assertEqual(result.conflict_metadata["required_resolution_rule"], "INPUT_INCOMPLETE")

    def test_motr004_temporal_envelope_preserves_precision_and_rejects_missing_required_times(self) -> None:
        date_only = timestamp("2026-07-20", precision=TimestampPrecision.DAY, source_field="event_date")
        envelope = make_temporal_envelope(event_time=date_only)

        self.assertEqual(envelope.event_time.precision, TimestampPrecision.DAY)
        self.assertIn("publication_time", validate_temporal_envelope(envelope, ("event_time", "publication_time")))

    def test_motr004_current_and_historical_truth_are_separate(self) -> None:
        original = temporal_observation("TOBS-1", "1.25", VersionStatus.ORIGINAL, "2026-07-20T12:01:00Z", "2026-07-20T12:00:00Z")
        corrected = temporal_observation("TOBS-2", "1.30", VersionStatus.CORRECTED, "2026-07-20T12:10:00Z", "2026-07-20T12:09:00Z")
        archive = TemporalTruthArchive()
        archive.append_observation(original)
        archive.append_observation(corrected)
        archive.append_revision_relationship(make_revision_relationship(original, corrected, RevisionRelationshipType.CORRECTS, ("sha256:correction",)))

        current = archive.resolve_current_fact("FACT-AAPL-EPS", "2026-07-20T12:20:00Z")
        historical = archive.resolve_fact_as_known_at("FACT-AAPL-EPS", "2026-07-20T12:05:00Z")

        self.assertEqual(current.selected_observation_id, "TOBS-2")
        self.assertEqual(historical.selected_observation_id, "TOBS-1")


if __name__ == "__main__":
    unittest.main()
