# OR-002 Remaining Provisional Surfaces

## OR-003: Broker-Realistic Paper Brokerage

- Paper broker model remains provisional.
- Manual paper orders are labeled `PAPER_PROVISIONAL_BROKER_MODEL`.
- Market session, slippage, spread, liquidity, buying power, and partial fills exist but require OR-003 certification.
- Mock/synthetic market providers remain available and need clearer source authority integration before certified paper trading.

## OR-004: Position Lifecycle & Trade Management

- Position surveillance and exit decision engines remain available.
- Runtime dashboard state now uses read-only surveillance/evaluation.
- Full entry/exit authorization, lifecycle expansion, and round-trip trade management remain OR-004 work.

## OR-005: Runtime Integration of Series C

- Series C modules exist, but full authoritative integration remains incomplete.
- Runtime still coordinates many advisory engines from dictionary snapshots.
- Some dashboards still display advisory/simulation panels; OR-005 should certify which panels can influence operations.

## OR-006: Enterprise Persistence

- Rejected truth records are process-memory diagnostics.
- Durable persistence of rejected truth, workflows, tokens, orders, fills, positions, messages, and policies remains OR-006.

## OR-007: End-to-End Enterprise Certification

- LIVE remains disabled and uncertified.
- No real broker orders were enabled.
- End-to-end PAPER-to-LIVE certification, recovery, replay, and broker reconciliation remain OR-007 gates.

