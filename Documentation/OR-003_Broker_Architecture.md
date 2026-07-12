# OR-003 Broker Architecture

ARGOS now has an OR-003 deterministic paper brokerage boundary in `argos.trader.paper_brokerage`.

## Reused Components

- Trader Order Management Office remains the order-state integration point.
- Execution Quality Office records broker-derived execution quality.
- Market Data Provider Abstraction Layer supplies bid, ask, last, volume, market status, and provenance.
- Performance Truth Engine records broker-authoritative events through `record_broker_authoritative_order`.
- Enterprise Communications Bus receives broker event envelopes.
- Position Monitoring Network receives post-fill handoff from Performance Truth snapshots.
- Truth-domain provenance guards reject proof, simulation, runtime-authored, or uncertified Decision Objects.

## New Component

`DeterministicPaperBrokerage` is the paper broker authority. It owns broker responses, fill records, partial-fill records, cancellation events, expiration events, settlement events, and broker rejection events.

The paper broker does not enable live trading, does not connect real credentials, and does not submit real orders.

## Authority Boundary

Trader may submit only trader-authorized paper order tickets. The paper broker validates workflow token ownership, Decision Object provenance, Risk approval, policy approval, supported asset, order semantics, market data, market session, account, and buying power.

Performance Truth records broker-authoritative outputs. It no longer needs to fabricate fills for OR-003 broker activity.

