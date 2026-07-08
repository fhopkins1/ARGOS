# ARGOS Control Panel Dashboard

## Purpose

The ARGOS Control Panel Dashboard is a local browser interface for user-visible operational control and enterprise visibility.

## Available Controls

- Start paper trading self-training.
- Halt paper trading self-training.
- Deposit user funds into active treasury.
- Halt user funds into active treasury.
- Request real-world trading from active treasury.
- Halt real-world trading.
- Set visible API-credit budget.

## Visibility

The dashboard displays enterprise group status, operational readiness, system health, group status summaries, activity feed, performance indicators, system resources, schedule, office command matrix, active treasury state, and projected API-credit burn.

## Safety Boundary

Paper self-training can be initiated from the dashboard. Real-world trading requests remain denied by default because live trading is still blocked by Foundation configuration and future broker/custody/risk gates are required.

## Launch

Run:

```powershell
& 'C:/Users/Fletc/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' Scripts/start_argos_control_panel.py
```

Then open:

```text
http://127.0.0.1:8765
```

For normal desktop use, double-click:

```text
Launch_ARGOS_Control_Panel.cmd
```

The launcher starts the local dashboard server if it is not already running and opens the control panel in the default browser.
