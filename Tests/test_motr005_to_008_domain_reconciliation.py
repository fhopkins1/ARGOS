from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.intelligence import (  # noqa: E402
    AccountingBasis,
    CorporateFactDomain,
    CorporateObservation,
    CorporateReconciliationEngine,
    CorporateReconciliationState,
    CorporateSourceClass,
    CorporateVersionState,
    DataQualityStatus,
    EconomicReleaseIdentity,
    EconomicSeriesIdentity,
    ExpectationCategory,
    MacroAuthorityClass,
    MacroDomain,
    MacroObservation,
    MacroReconciliationState,
    MacroReleaseStatus,
    MacroTruthArchive,
    MacroVersionState,
    NumericalDomain,
    NumericalObservation,
    NumericalObservationType,
    NumericalReconciliationEngine,
    NumericalReconciliationOutcome,
    RegulatoryAuthorityClass,
    RegulatoryDomain,
    RegulatoryObservation,
    RegulatoryReconciliationEngine,
    RegulatoryStatus,
    TradeEligibility,
    make_macro_revision_relationship,
)


def numerical_observation(**overrides) -> NumericalObservation:
    data = {
        "observation_id": "NUM-1",
        "workflow_id": "WF-MOTR",
        "domain": NumericalDomain.BID,
        "observation_type": NumericalObservationType.BID,
        "instrument_id": "AAPL",
        "source_id": "SRC-LICENSED-SIP-MARKET-DATA",
        "raw_value": "200.00",
        "raw_unit": "USD",
        "raw_currency": "USD",
        "raw_precision": "0.01",
        "event_time": "2026-07-20T14:30:00Z",
        "market_time": "2026-07-20T14:30:00Z",
        "retrieval_time": "2026-07-20T14:30:05Z",
        "venue": "NASDAQ",
        "market_session": "REGULAR",
        "adjustment_basis": "UNADJUSTED",
        "tick_size": "0.01",
        "rounding_mode": "ROUND_HALF_UP",
        "delayed": False,
        "evidence_references": ("sha256:num-1",),
    }
    data.update(overrides)
    return NumericalObservation(**data)


def corporate_observation(**overrides) -> CorporateObservation:
    data = {
        "corporate_observation_id": "CORP-1",
        "workflow_id": "WF-MOTR",
        "issuer_id": "0000320193",
        "security_id": "AAPL",
        "fact_domain": CorporateFactDomain.DILUTED_EARNINGS_PER_SHARE,
        "reporting_period": "2026Q2",
        "period_start": "2026-04-01",
        "period_end": "2026-06-30",
        "accounting_basis": AccountingBasis.GAAP,
        "metric_definition": "diluted_eps_gaap",
        "value": "1.25",
        "unit": "USD_PER_SHARE",
        "currency": "USD",
        "source_class": CorporateSourceClass.FILED_REGULATORY_DOCUMENT,
        "document_id": "10-Q-1",
        "document_version": CorporateVersionState.ORIGINAL,
        "filing_status": "FILED",
        "publication_time": "2026-07-20T12:00:00Z",
        "effective_time": "2026-06-30T23:59:59Z",
        "amended_sections": (),
        "supersedes_document_id": "",
        "evidence_references": ("sha256:corp-1",),
    }
    data.update(overrides)
    return CorporateObservation(**data)


def regulatory_observation(**overrides) -> RegulatoryObservation:
    data = {
        "observation_id": "REG-1",
        "workflow_id": "WF-MOTR",
        "decision_object_id": "DO-AAPL",
        "instrument_id": "AAPL",
        "issuer_id": "0000320193",
        "authority_domain": RegulatoryDomain.TRADING_HALTS,
        "authority_class": RegulatoryAuthorityClass.EXCHANGE,
        "source_id": "NASDAQ-HALTS",
        "status": RegulatoryStatus.HALTED,
        "previous_status": RegulatoryStatus.ACTIVE,
        "publication_time": "2026-07-20T14:30:00Z",
        "effective_time": "2026-07-20T14:30:00Z",
        "retrieval_time": "2026-07-20T14:30:02Z",
        "jurisdiction": "US",
        "rule_identifier": "MO-TR-007:exchange-halt",
        "evidence_references": ("sha256:reg-1",),
    }
    data.update(overrides)
    return RegulatoryObservation(**data)


def macro_series() -> EconomicSeriesIdentity:
    return EconomicSeriesIdentity("CPI-U", "CPIAUCSL", "Consumer Price Index", "BLS", "US", "US", MacroDomain.INFLATION, "urban_consumers", "MONTHLY", "INDEX", "ones", "USD", "current_prices", "SA", "NOT_ANNUALIZED", "1982-84=100", "MONTH", "BLS-CPI", MacroAuthorityClass.OFFICIAL_STATISTICAL_AGENCY, "SRC-BLS", "ACTIVE", "2026-01-01T00:00:00Z", "")


def macro_release(release_id: str, published: str, vintage: str) -> EconomicReleaseIdentity:
    return EconomicReleaseIdentity(release_id, "CPI", "BLS", published, published, published, published, MacroReleaseStatus.PUBLISHED, vintage, "2026-06", ("CPI-U",), (release_id,), ("https://www.bls.gov/cpi/",), "", ())


def macro_observation(**overrides) -> MacroObservation:
    series = overrides.pop("series", macro_series())
    release = overrides.pop("release", macro_release("REL-1", "2026-07-20T12:30:00Z", "initial"))
    data = {
        "observation_id": "MACRO-1",
        "series": series,
        "release": release,
        "reference_period": "2026-06",
        "reference_period_start": "2026-06-01",
        "reference_period_end": "2026-06-30",
        "publication_time": "2026-07-20T12:30:00Z",
        "retrieval_time": "2026-07-20T12:31:00Z",
        "system_recorded_time": "2026-07-20T12:31:01Z",
        "release_vintage": "initial",
        "value": "3.2",
        "unit": "PERCENT",
        "scale": "ones",
        "currency": "",
        "seasonal_adjustment_status": "SA",
        "annualization_status": "NOT_ANNUALIZED",
        "price_basis": "current_prices",
        "version_status": MacroVersionState.INITIAL,
        "source_authority": MacroAuthorityClass.OFFICIAL_STATISTICAL_AGENCY,
        "source_document_id": "REL-1",
        "expectation_category": ExpectationCategory.ACTUAL_VALUE,
        "prior_reported_value": "3.1",
        "revised_prior_value": "3.0",
        "consensus_estimate": "3.3",
        "estimate_low": "3.0",
        "estimate_high": "3.5",
        "market_implied_expectation": None,
        "normalization_status": "NORMALIZED",
        "comparability_status": "COMPARABLE",
        "conflict_status": "NONE",
        "evidence_references": ("sha256:macro-1",),
    }
    data.update(overrides)
    return MacroObservation(**data)


class MOTR005To008DomainReconciliationTests(unittest.TestCase):
    def test_motr005_accepts_tick_tolerant_values_without_averaging(self) -> None:
        left = numerical_observation()
        right = numerical_observation(observation_id="NUM-2", raw_value="200.01", evidence_references=("sha256:num-2",))

        record = NumericalReconciliationEngine().reconcile(left, right)

        self.assertEqual(record.outcome, NumericalReconciliationOutcome.ACCEPTED)
        self.assertEqual(record.required_action, "accept_without_averaging")
        self.assertEqual(record.tick_difference, 1)
        self.assertEqual(record.observation_ids, ("NUM-1", "NUM-2"))

    def test_motr005_stale_wrong_currency_or_price_meaning_fails_closed(self) -> None:
        left = numerical_observation()
        stale = numerical_observation(observation_id="NUM-STALE", retrieval_time="2026-07-20T14:40:00Z")
        stale_record = NumericalReconciliationEngine().reconcile(left, stale)
        self.assertEqual(stale_record.data_quality_status, DataQualityStatus.STALE_SOURCE)
        self.assertEqual(stale_record.outcome, NumericalReconciliationOutcome.EXECUTION_DEFERRED)

        wrong_meaning = numerical_observation(observation_id="NUM-ASK", domain=NumericalDomain.ASK, observation_type=NumericalObservationType.ASK)
        meaning_record = NumericalReconciliationEngine().reconcile(left, wrong_meaning)
        self.assertEqual(meaning_record.outcome, NumericalReconciliationOutcome.NONCOMPARABLE)

    def test_motr006_filed_document_prevails_but_gaap_and_non_gaap_do_not_merge(self) -> None:
        filed = corporate_observation()
        release = corporate_observation(corporate_observation_id="CORP-2", source_class=CorporateSourceClass.ISSUER_EARNINGS_RELEASE, document_id="ER-1", evidence_references=("sha256:corp-2",))
        record = CorporateReconciliationEngine().reconcile((release, filed))
        self.assertEqual(record.state, CorporateReconciliationState.RECONCILED_AUTHORITATIVE)
        self.assertEqual(record.selected_observation_id, "CORP-1")

        non_gaap = corporate_observation(corporate_observation_id="CORP-3", accounting_basis=AccountingBasis.NON_GAAP, metric_definition="adjusted_eps", value="1.40")
        mismatch = CorporateReconciliationEngine().reconcile((filed, non_gaap))
        self.assertEqual(mismatch.state, CorporateReconciliationState.DIFFERENT_DEFINITION)
        self.assertEqual(mismatch.required_action, "do_not_merge_gaap_non_gaap")

    def test_motr006_amendment_supersedes_only_with_preserved_history(self) -> None:
        original = corporate_observation()
        amended = corporate_observation(corporate_observation_id="CORP-AMEND", source_class=CorporateSourceClass.AMENDED_REGULATORY_DOCUMENT, document_id="10-Q-A", document_version=CorporateVersionState.AMENDED, value="1.30", amended_sections=("EPS",), supersedes_document_id="10-Q-1", evidence_references=("sha256:corp-amend",))
        record = CorporateReconciliationEngine().reconcile((original, amended))

        self.assertEqual(record.state, CorporateReconciliationState.SUPERSEDED_BY_AMENDMENT)
        self.assertIn("CORP-1", record.observation_ids)
        self.assertIn("CORP-AMEND", record.observation_ids)

    def test_motr007_exchange_halt_blocks_and_issuer_cannot_override(self) -> None:
        halt = regulatory_observation()
        issuer_active = regulatory_observation(observation_id="REG-ISSUER", authority_class=RegulatoryAuthorityClass.ISSUER, source_id="ISSUER-IR", status=RegulatoryStatus.ACTIVE, evidence_references=("sha256:reg-issuer",))

        record = RegulatoryReconciliationEngine().reconcile((halt, issuer_active))

        self.assertEqual(record.current_status, RegulatoryStatus.HALTED)
        self.assertEqual(record.trade_eligibility, TradeEligibility.PROHIBITED)
        self.assertEqual(record.required_action, "emit_trade_block")

    def test_motr007_conflicting_primary_legal_status_fails_closed(self) -> None:
        first = regulatory_observation(observation_id="REG-1", status=RegulatoryStatus.ACTIVE)
        second = regulatory_observation(observation_id="REG-2", status=RegulatoryStatus.HALTED, evidence_references=("sha256:reg-2",))

        record = RegulatoryReconciliationEngine().reconcile((first, second))

        self.assertEqual(record.current_status, RegulatoryStatus.REGULATORY_CONFLICT)
        self.assertEqual(record.trade_eligibility, TradeEligibility.PROHIBITED)

    def test_motr008_revisions_create_current_value_without_erasing_as_known_at(self) -> None:
        original = macro_observation()
        revised = macro_observation(observation_id="MACRO-2", release=macro_release("REL-2", "2026-08-20T12:30:00Z", "revised"), publication_time="2026-08-20T12:30:00Z", retrieval_time="2026-08-20T12:31:00Z", system_recorded_time="2026-08-20T12:31:01Z", release_vintage="revised", value="3.0", version_status=MacroVersionState.REVISED, evidence_references=("sha256:macro-2",))
        archive = MacroTruthArchive()
        archive.append_observation(original)
        archive.append_observation(revised)
        archive.append_revision_relationship(make_macro_revision_relationship(original, revised, "ROUTINE_REVISION"))

        current = archive.resolve_current_official("CPI-U", "2026-06")
        historical = archive.resolve_as_known_at("CPI-U", "2026-06", "2026-07-30T00:00:00Z")

        self.assertEqual(current.state, MacroReconciliationState.CURRENT_OFFICIAL_VALUE)
        self.assertEqual(current.selected_observation_id, "MACRO-2")
        self.assertEqual(historical.state, MacroReconciliationState.HISTORICAL_VINTAGE)
        self.assertEqual(historical.selected_observation_id, "MACRO-1")

    def test_motr008_forecasts_remain_separate_from_actual_official_values(self) -> None:
        forecast = macro_observation(observation_id="MACRO-FCST", value="3.4", source_authority=MacroAuthorityClass.PRIVATE_ECONOMIC_DATA, expectation_category=ExpectationCategory.CONSENSUS_ESTIMATE, evidence_references=("sha256:macro-fcst",))
        record = MacroTruthArchive().classify_expectation(forecast)

        self.assertEqual(record.state, MacroReconciliationState.FORECAST_SEPARATE)
        self.assertEqual(record.selected_observation_id, "")

    def test_required_domain_enums_cover_order_minimums(self) -> None:
        self.assertIn(CorporateFactDomain.MATERIAL_WEAKNESS, set(CorporateFactDomain))
        self.assertIn(RegulatoryDomain.SANCTIONS_LISTS, set(RegulatoryDomain))
        self.assertIn(MacroDomain.CENTRAL_BANK_DECISIONS, set(MacroDomain))
        self.assertIn(NumericalDomain.BROKER_EXECUTION_VALUE, set(NumericalDomain))


if __name__ == "__main__":
    unittest.main()
