# EO-DD Performance and Overhead Report

EO-DD adds an in-process append-only journal, deterministic hashing, participant state maps, and reconciliation scans.

Targeted tests complete in milliseconds for the in-memory implementation. Reconciliation overhead is proportional to the supplied evidence snapshot size and reuses EO-DA's broker-position invariant monitor.

The coordinator is intentionally isolated from broker/position/performance write paths in this increment to avoid introducing hidden mutation latency or side effects.

