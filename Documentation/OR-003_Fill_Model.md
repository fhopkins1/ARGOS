# OR-003 Fill Model

`PaperBrokerFillEngine` is the sole OR-003 fill authority.

Inputs:

- Accepted broker order
- Bid, ask, last, volume, session, and source provenance
- Asset characteristics
- Order type and parameters
- Time in force

Execution is bid/ask aware:

- Buy orders use ask.
- Sell orders use bid.
- Midpoint execution is not assumed.

Partial fills are deterministic from available volume participation. FOK expires when the full remaining quantity is unavailable. IOC expires if no quantity is immediately fillable.

The fill engine records fill ID, execution ID, quantity, price, commission, slippage, timestamp, price source, and remaining quantity.

