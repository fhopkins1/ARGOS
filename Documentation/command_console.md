# Command Console

The Command Console is the authoritative human command interface for the ARGOS Control Panel. It validates, authorizes, routes, records, and audits Commander directives before they affect enterprise state.

## Responsibilities

- Accept strategic, operational, administrative, scheduling, trading, educational, knowledge, infrastructure, and investigation commands.
- Validate Commander authorization, organizational readiness, dependencies, safety constraints, and resource availability.
- Route authorized commands to existing ARGOS control-panel subsystems without bypassing organizational boundaries.
- Preserve complete command lifecycle history from issuance through validation, authorization, execution, result, archive, and audit record.
- Provide reusable Commander macros for Morning Startup, Market Open, End of Day, Weekly Review, Historian Review, and Emergency Shutdown.

## Safety Boundaries

Live trading initiation is blocked by deterministic configuration and Risk certification validation. The console may route paper trading, halt controls, treasury controls, scheduling controls, investigation commands, and report generation, but it does not create discretionary investment authority.

## Runtime Integration

The Command Console is implemented in `src/argos/control_panel/command_console.py` and integrated by `ControlPanelRuntime`.

Dashboard API endpoints:

- `POST /api/command/execute`
- `POST /api/command/macro`
- `GET /api/command/history`

Every accepted, rejected, completed, failed, and macro command is represented in Command Console history and published to the Enterprise Activity Bus where appropriate.

## Dashboard Surface

The ARGOS Control Panel displays:

- Commander directive controls
- reusable macros
- validation and integrity metrics
- latest response
- command history
- command history filtering

## Deterministic Lifecycle

Every command follows:

1. Command Issued
2. Validation
3. Authorization
4. Execution
5. Result
6. Historical Archive
7. Audit Record

Rejected commands are never executed and remain permanently visible in history.
