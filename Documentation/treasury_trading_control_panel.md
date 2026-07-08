# EO-087 Treasury and Trading Authority Control Panel

## Mission

The Treasury and Trading Authority Control Panel provides user-visible operational controls for paper trading, active treasury deposits, and real-world trading requests while preserving human authority, auditability, and existing safety gates.

## Implemented Controls

- Initiate paper trading for ARGOS self-training.
- Halt paper trading through the Human Override trading pause.
- Deposit user funds into the active treasury ledger.
- Halt user funds into active treasury.
- Request real-world trading from active treasury.
- Halt real-world trading through the Human Override trading pause.
- Render an immediately visible control panel snapshot.

## Safety Boundary

Real-world trading initiation is present as an auditable control path, but it remains denied by default because live trading configuration is still disabled by the Foundation configuration service. Actual live execution authority requires future broker, custody, risk, treasury, and explicit user approval gates.

## Auditability

Every control action is persisted as an `ARGOS_CONTROL_PANEL_ACTION` operational document and recorded as a staff decision audit event. Treasury transactions are append-only and dashboard state is reconstructable from control records.
