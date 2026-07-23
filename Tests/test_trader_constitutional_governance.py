from pathlib import Path
import sys
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.trader.constitutional_governance import (  # noqa: E402
    FINANCIAL_RESOURCE_OWNERS,
    AuthorityInputs,
    CertificationVerdict,
    ExecutionScope,
    HistorianCompletionContext,
    TemporalContext,
    TorrVerdict,
    TraderGovernanceStatus,
    TraderOperatingMode,
    resolve_operating_mode,
    validate_certification_verdict,
    validate_execution_authority,
    validate_execution_scope,
    validate_financial_resource_ownership,
    validate_historian_completion,
    validate_object_registry,
    validate_temporal_context,
    validate_torr_verdict,
)


class TraderConstitutionalGovernanceTests(unittest.TestCase):
    def test_execution_authority_requires_all_controlling_authorities(self) -> None:
        valid = validate_execution_authority(AuthorityInputs(True, True, True, True))
        missing = validate_execution_authority(AuthorityInputs(True, False, True, True))
        conflict = validate_execution_authority(AuthorityInputs(True, True, True, True, conflicting_authority=True))

        self.assertEqual(valid.status, TraderGovernanceStatus.PASS)
        self.assertEqual(missing.status, TraderGovernanceStatus.FAIL)
        self.assertIn("missing required authority: authorization", missing.findings)
        self.assertEqual(conflict.status, TraderGovernanceStatus.FAIL)

    def test_operating_mode_requires_exactly_one_explicit_mode(self) -> None:
        self.assertEqual(resolve_operating_mode((TraderOperatingMode.PAPER,)).status, TraderGovernanceStatus.PASS)
        self.assertEqual(resolve_operating_mode(()).status, TraderGovernanceStatus.FAIL)
        self.assertEqual(resolve_operating_mode((TraderOperatingMode.PAPER, TraderOperatingMode.LIVE)).status, TraderGovernanceStatus.FAIL)

    def test_supported_scope_excludes_margin_collateral_and_unsupported_orders(self) -> None:
        valid = ExecutionScope("cash_equity", "limit", "cash_brokerage", FINANCIAL_RESOURCE_OWNERS, True, True)
        invalid = ExecutionScope("option", "market", "margin_account", FINANCIAL_RESOURCE_OWNERS, True, True, margin_or_collateral_required=True)

        self.assertEqual(validate_execution_scope(valid).status, TraderGovernanceStatus.PASS)
        result = validate_execution_scope(invalid)
        self.assertEqual(result.status, TraderGovernanceStatus.FAIL)
        self.assertTrue(any("unsupported instrument" in finding for finding in result.findings))
        self.assertTrue(any("margin and collateral" in finding for finding in result.findings))

    def test_settlement_ownership_prevents_trader_from_owning_financial_truth(self) -> None:
        valid = validate_financial_resource_ownership(FINANCIAL_RESOURCE_OWNERS)
        invalid_owners = dict(FINANCIAL_RESOURCE_OWNERS)
        invalid_owners["Cash"] = "Trader Office"

        self.assertEqual(valid.status, TraderGovernanceStatus.PASS)
        invalid = validate_financial_resource_ownership(invalid_owners)
        self.assertEqual(invalid.status, TraderGovernanceStatus.FAIL)
        self.assertIn("Trader may not own financial account truth resources: Cash", invalid.findings)

    def test_temporal_market_state_fails_closed_for_stale_or_unknown_time(self) -> None:
        valid = TemporalContext(True, True, 1, 5, True, False, True, True, True)
        stale = TemporalContext(False, False, 10, 5, True, True, False, False, False)

        self.assertEqual(validate_temporal_context(valid).status, TraderGovernanceStatus.PASS)
        self.assertEqual(validate_temporal_context(stale).status, TraderGovernanceStatus.FAIL)

    def test_historian_completion_requires_custody_acknowledgement(self) -> None:
        valid = HistorianCompletionContext(True, True, True, True)
        incomplete = HistorianCompletionContext(True, True, True, False)

        self.assertEqual(validate_historian_completion(valid).status, TraderGovernanceStatus.PASS)
        self.assertEqual(validate_historian_completion(incomplete).status, TraderGovernanceStatus.FAIL)

    def test_torr_readiness_is_not_certification_and_certification_is_binary(self) -> None:
        self.assertEqual(validate_torr_verdict(TorrVerdict.INTERNALLY_READY.value).status, TraderGovernanceStatus.PASS)
        self.assertEqual(validate_torr_verdict(CertificationVerdict.UNCONDITIONAL_PASS.value).status, TraderGovernanceStatus.FAIL)
        self.assertEqual(validate_certification_verdict(CertificationVerdict.UNCONDITIONAL_PASS.value).status, TraderGovernanceStatus.PASS)
        self.assertEqual(validate_certification_verdict("Conditional Pass").status, TraderGovernanceStatus.FAIL)

    def test_object_registry_and_lifecycles_are_complete(self) -> None:
        self.assertEqual(validate_object_registry().status, TraderGovernanceStatus.PASS)


if __name__ == "__main__":
    unittest.main()
