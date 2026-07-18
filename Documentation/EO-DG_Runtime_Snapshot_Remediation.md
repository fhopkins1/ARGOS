# EO-DG Runtime Snapshot Remediation

Runtime snapshot paths are classified as read surfaces. EO-DG protects them with semantic digests and counters.

Snapshot code must not build closed-position truth, ingest performance truth, process broker fills, advance workflows, dispatch Scheduler obligations, perform transaction retries, promote truth, append Historian records, or repair state.

