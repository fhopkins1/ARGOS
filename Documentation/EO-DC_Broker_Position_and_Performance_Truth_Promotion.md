# EO-DC Broker, Position, and Performance Truth Promotion

Broker events and fills are promoted through `promote_broker_event()` and `promote_position_mutation()`.

Performance Truth ingestion is promoted through `promote_performance_truth()`. `PerformanceTruthEngine.record_broker_authoritative_order()` now rejects EO-DC promotion failures before mutating ledgers.

EO-DC does not create fills, mutate positions, or create Performance Truth. It approves or rejects eligibility for the owning authority.

