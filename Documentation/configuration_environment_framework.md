# EO-006 Configuration and Environment Framework

ARGOS configuration is owned by Foundation and is validated before startup.
Departments consume this service and must not duplicate configuration logic.

## Supported Environments

- Development
- Paper Trading
- Historical Replay
- Integration Testing
- Staging
- Production

## Configuration Responsibilities

- deterministic loading
- startup validation
- feature flag lookup
- environment switching
- secret references through environment variables or secure providers
- Case File configuration snapshots

## Secrets

Secrets must never be hardcoded. `SecretReference` stores provider metadata and
the lookup key, not the secret value. Configuration snapshots redact secret
values.

## Live Trading Boundary

EO-006 does not authorize live trading. Startup validation rejects
`live_trading_enabled=true`.

## Snapshotting

`ConfigurationService.snapshot_for_case_file(case_file_id, trade_cycle_id)`
produces a deterministic, hash-addressable, secret-safe configuration snapshot
for audit and replay use.

