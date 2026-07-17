# EO-DF Transaction Endurance Model

EO-DF observes EO-DD transaction state:
- active transactions
- partially applied transactions
- committed transactions
- failed transactions
- reconciliation-required transactions
- journal size
- outbox size
- retry count

EO-DF does not alter EO-DD transaction status. Reconciliation endurance campaigns include EO-DD reconciliation evidence events.

