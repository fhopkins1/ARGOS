# EO-DD Cash, Order, and Position Reconciliation

EO-DD reconciliation accepts evidence snapshots and performance-truth snapshots. It delegates broker/order/fill/position integrity checks to EO-DA's `BrokerPositionInvariantMonitor`.

Blocking examples:
- filled terminal order with rejected/cancelled/expired status
- fill without order id
- open position without fill or broker order lineage
- position referencing an unfilled order
- duplicate closed-position truth

Cash settlement reconciliation is represented as a registered `SETTLEMENT` transaction type and must be acknowledged by participant authorities before commitment.

