# EO-057 Position Management Office

The Position Management Office is ARGOS's authoritative enterprise source of truth for financial positions. PMO constructs, maintains, reconciles, monitors, publishes, and archives positions without selecting trades, executing trades, or performing investment analysis.

## Responsibilities

- Receive execution events from the Order Management Office.
- Create, update, close, and archive positions.
- Track cost basis, quantity, market value, realized P&L, unrealized P&L, and exposure.
- Maintain complete position history.
- Reconcile positions with broker records.
- Publish current portfolio state.
- Generate Position Management Case Files for anomalies.

## Position Lifecycle

`created`, `accumulating`, `open`, `adjusted`, `reducing`, `closed`, and `archived`.

Every transition records timestamp, triggering execution event, audit identifier, previous state, new state, and supporting metadata.

## Required Position Fields

Position ID, asset identifier, portfolio ID, strategy ID, Executive decision ID, average cost basis, quantity, market value, realized P&L, unrealized P&L, exposure, position status, creation timestamp, last update timestamp, audit identifier, direction, asset class, and full history.

## Monitoring And Reconciliation

PMO monitors position accuracy, quantity consistency, cost basis accuracy, portfolio exposure, concentration, unrealized gains/losses, corporate actions, dividends, broker agreement, and portfolio consistency.

## Case Files

PMO generates Position Management Case Files for position mismatches, quantity errors, cost basis errors, missing executions, duplicate positions, reconciliation failures, unexpected exposure, position drift, inconsistent portfolio state, and broker disagreement.

## Supported Position Types

The data model supports long positions, short positions, fractional positions, multi-leg positions, options, futures, cryptocurrency positions, and future asset classes through the `asset_class` and direction fields.

## Traceability

Every position remains reconstructable from execution history and synchronizes with executions, orders, positions, portfolios, Risk Office, Trader Group, Historian Group, and Audit records.
