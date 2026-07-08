# EO-016 Human Override and Kill Switch Framework

Human authority is maintained through authorized override records, append-only
persistence, and automatic audit events.

## Override Levels

- 0: Normal
- 1: Executive Pause
- 2: Trading Pause
- 3: Read-Only Mode
- 4: Replay Mode
- 5: Organization Lockdown
- 6: Emergency Liquidation

## Supported Controls

- Executive Pause
- Trading Pause
- Organization Lockdown
- Emergency Liquidation
- Replay Mode
- Read-Only Mode
- Resume

## Safety Rules

- Unauthorized overrides are rejected.
- Overrides do not delete historical records.
- Audit records are never erased.
- Completed Case Files are not modified.
- Override actions cannot bypass logging.

