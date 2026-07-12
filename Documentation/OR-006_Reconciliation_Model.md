# OR-006 Reconciliation Model

OR-006 reconciliation is evidence-preserving.

The recovery service verifies persisted broker, position, and Performance Truth families exist and records deferred entities when evidence is missing. It does not infer broker fills or position closure from runtime memory.

Full broker-vs-position-vs-closed-truth reconciliation remains part of OR-007 certification depth.
