# OR-005 Legacy Runtime Path Inventory

## Discovered Paths

- `ControlPanelRuntime.start_paper_self_training`: legacy/demo paper loop. Classification: `LEGACY`; not canonical Part 1 path.
- Dashboard command routes that call runtime helpers directly. Classification: `UI_READ_MODEL` or `LEGACY` depending on route; Part 2 remediation required.
- Direct broker submission remains available as the broker boundary for Trader. Classification: `BROKER`; must be reachable only with valid token/provenance.
- Performance Truth direct recording helpers remain for authoritative event ingestion. Classification: `TRUTH_DOMAIN`; must reject proof/simulation where operational truth is requested.
- Decision Laboratory and replay paths remain proof/simulation only. Classification: `LEGACY`/`TRUTH_DOMAIN`.

## Remediation

`CanonicalEnterpriseRuntime` blocks certified paper API work without cost reservation, blocks Seeker work without Strategic Intelligence mandate, and starts without fabricating missions or truth.

## Remaining Work

Part 2 must wire UI/API production routes to the canonical composition or explicitly quarantine them as proof/test/compatibility surfaces.
