# EO-DF Long Duration Campaign Catalog

EO-DF defines one canonical campaign catalog in `long_duration_operations_lab.py`.

Supported campaigns:
- Idle Stability
- Controlled Active Paper
- Mixed Operational
- Repeated Lifecycle
- Restart Endurance
- Monitoring Endurance
- Dashboard and Read-Only Load
- Reconciliation Endurance
- Replay Endurance
- Recovery Endurance

Every catalog entry is versioned, declares required telemetry domains, and is marked incapable of creating trading activity. EO-DF may observe paper fixtures but must not create opportunities merely to populate metrics.

