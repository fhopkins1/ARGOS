# EO-DD Transaction Taxonomy

EO-DD defines the canonical transaction types coordinated across broker, position, performance truth, closed-position truth, historian, and recovery ledgers.

Canonical types:
- `OPENING_FILL`
- `PARTIAL_OPENING_FILL`
- `POSITION_INCREASE`
- `PARTIAL_REDUCTION`
- `FULL_CLOSURE`
- `ORDER_CANCELLATION`
- `ORDER_EXPIRATION`
- `SETTLEMENT`
- `REVERSAL`
- `CORPORATE_ACTION`
- `RECOVERY`
- `RECONCILIATION_CORRECTION`

The registry lives in `src/argos/control_panel/transaction_reconciliation.py` as `TRANSACTION_TYPE_REGISTRY`. Every registered type explicitly declares required participants, EO-DC approval requirements, whether financial truth may be created by participant authorities, and that the coordinator itself has no financial mutation authority.

