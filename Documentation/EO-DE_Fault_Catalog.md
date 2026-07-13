# EO-DE Fault Catalog

EO-DE defines a canonical deterministic fault catalog in `src/argos/control_panel/fault_injection_lab.py`.

The catalog includes 40 faults across:
- Runtime
- Startup
- Scheduler
- Mission Planner
- Duty Officer
- Workflow Token
- Communications
- API Gateway
- Cost Governor
- Market Data
- Broker
- Position
- EO-CK
- Exit
- Performance Truth
- Closed Position Truth
- Historian
- Persistence
- Recovery
- Replay
- Commander
- Dashboard
- Resource Exhaustion
- Corruption
- Duplicate Requests
- Idempotency
- Truth-Domain Contamination

Each fault records fault id, name, category, severity, injection location, preconditions, expected behavior, expected authority owner, truth-domain behavior, LAW VII behavior, recovery behavior, reconciliation behavior, and pass criteria.

