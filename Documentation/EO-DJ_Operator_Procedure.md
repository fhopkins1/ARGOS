# EO-DJ Operator Procedure

1. Configure an authoritative paper provider adapter outside source control.
2. Register it in `ProviderAuthorityRegistry` for `PAPER_AUTHORITATIVE`.
3. Verify credential presence by name/status only; never log secret values.
4. Run an observation health check through `MarketDataGateway`.
5. Confirm the returned `MarketDataObservation` has `FRESH` freshness evidence.
6. Confirm the observation is present in `MarketDataEvidenceStore`.
7. Run `MarketDataDecisionGuard.validate()` for the intended instrument and observation type.
8. On provider failure, preserve the rejection and stop dependent decisions.
9. On rate limits, reject or degrade explicitly; never select a synthetic fallback.
10. Confirm `mockFallbackEnabled` and `syntheticFallbackEnabled` remain false in EO-DJ evidence.

Passing EO-DJ boundary tests does not certify ARGOS for paper trading. It certifies that the repository fails closed unless an authoritative provider is explicitly configured and accepted by policy.
