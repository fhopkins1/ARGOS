# EO-DA Performance and Overhead Report

EO-DA is deterministic and local. It does not call external APIs, wake offices, create missions, submit orders, mutate positions, create truth, or write financial ledgers.

Targeted EO-DA tests ran 9 tests in approximately 0.03 seconds on the local environment.

Sweep overhead is reported in `InvariantSweepResult.runtime_overhead_ms`.

Full repository scans are limited to explicit static architecture sweeps and are not run during every runtime tick.

