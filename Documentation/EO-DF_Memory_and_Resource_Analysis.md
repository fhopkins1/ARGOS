# EO-DF Memory and Resource Analysis

EO-DF compares baseline and final telemetry samples and records drift summaries for memory, tasks, queues, messages, cache, EO-DD journal, checkpoints, latency, and cost.

The analysis distinguishes:
- expected authoritative ledger growth
- checkpoint growth under retention limits
- cache growth within limits
- leaked transient state
- read-only polling load

Monotonic memory growth is not dismissed merely because the process remains alive.

