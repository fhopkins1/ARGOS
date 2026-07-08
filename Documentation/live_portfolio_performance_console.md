# Live Portfolio & Performance Console

The Live Portfolio & Performance Console (LPPC) is the financial command display for ARGOS. It gives the Commander deterministic visibility into paper, simulation, live brokerage, and combined enterprise portfolio state.

## Responsibilities

- Display Paper Trading Portfolio, Simulation Portfolio, Live Brokerage Portfolio, and Combined Enterprise Portfolio.
- Calculate portfolio value, buying power, cash, open and closed positions, realized and unrealized P&L, and return metrics.
- Calculate risk metrics including exposure, sector allocation, correlation, volatility, liquidity, value at risk, maximum drawdown, and concentration.
- Display performance metrics including alpha, beta, Sharpe ratio, Sortino ratio, win rate, average gain, average loss, and profit factor.
- Provide deterministic drill-down from portfolio to position, orders, executive decision, case file, evidence, and historical performance.
- Synchronize with Position Management, Trade Monitoring, Execution Quality, Risk, Historian, Broker Integration, and Enterprise Activity Bus signals.
- Detect portfolio inconsistencies, position mismatches, missing market data, performance anomalies, and synchronization failures.

## Safety Boundary

LPPC does not execute trades or mutate positions. The local control panel presents live brokerage visibility as empty and blocked unless future broker authority and live trading gates are explicitly implemented.

## Runtime Integration

Implementation lives in `src/argos/control_panel/lppc.py` and is exposed through:

- `GET /api/lppc/state`
- the regular `GET /api/state` dashboard payload

## Dashboard Surface

The ARGOS Control Panel displays:

- selected portfolio summary
- portfolio performance metrics
- risk metrics
- synchronization state
- position drill-down
- LPPC detections

Every displayed financial metric is deterministic and traceable to modeled positions, runtime state, and activity bus records.
