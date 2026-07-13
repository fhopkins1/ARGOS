# EO-DD Atomicity and Saga Model

EO-DD uses saga-style coordination. It does not perform financial writes directly. Instead, it records immutable intent, publishes participant outbox events, accepts participant evidence acknowledgments, reconciles the evidence, and only then marks the transaction committed.

Atomicity rule: no transaction is complete unless all required participant authorities have acknowledged durable application and reconciliation evidence is clean.

Rollback fabrication is prohibited. Recovery can mark work as recovery-required, quarantine, or roll forward by participant action, but EO-DD itself cannot synthesize fills, mutate positions, or create performance truth.

