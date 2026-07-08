# ARGOS Project Handoff

This repository contains the current ARGOS Deterministic Cognitive Enterprise implementation as of the initial GitHub snapshot.

Repository: `https://github.com/fhopkins1/ARGOS`  
Initial pushed commit: `12a2bc5f6456054a2de4bd79d9a9af6539997072`  
Primary branch: `main`

## Current State Summary

ARGOS is not just an EO-001 skeleton. The repository contains a broad deterministic enterprise scaffold with implemented modules, tests, documentation, and a runnable local control panel.

Major groups represented:

- Foundation
- Executive Group
- Seeker Group
- Analyst Group
- Risk Office
- Trader Group
- Historian Group
- Librarian Group
- Academy
- Operations / Control Panel systems

## Latest Operational Work Completed

Recent operational engineering work includes:

- `OE-100` ARGOS Command Bridge
- `OE-100A` Capital-First Command Bridge Revision
- `OE-101` Executive Subcommand Bridge
- `OE-102` Seeker Intelligence Bridge

The control panel now includes:

- Capital-first Command Bridge
- Capital heartbeat strip
- Capital performance graph
- Credit expenditure panel
- Mission scorecards
- Workflow baton
- Decision Object panel
- Executive Subcommand Bridge
- Seeker Intelligence Bridge
- Discovery radar
- Candidate queue
- Market intelligence
- Office health
- Signal source status
- Recent promotions
- Engineering mode diagnostics

## Important Runtime Entry Points

Run the ARGOS Control Panel:

```powershell
.\Launch_ARGOS_Control_Panel.cmd
```

or:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\launch_argos_control_panel.ps1
```

Expected local URL:

```text
http://127.0.0.1:8765/
```

Python backend entry point:

```text
Scripts/start_argos_control_panel.py
```

Control panel frontend:

```text
ui/argos_control_panel/index.html
ui/argos_control_panel/app.js
ui/argos_control_panel/styles.css
```

Control panel backend:

```text
src/argos/control_panel/runtime.py
src/argos/control_panel/server.py
```

## Key Operations Systems

Important control panel and operations modules:

```text
src/argos/control_panel/workflow_orchestrator.py
src/argos/control_panel/workflow_runtime_monitor.py
src/argos/control_panel/api_runtime_monitor.py
src/argos/control_panel/api_execution_gateway.py
src/argos/control_panel/credit_governor.py
src/argos/control_panel/performance_truth_engine.py
src/argos/control_panel/strategy_performance_console.py
src/argos/control_panel/decision_laboratory.py
src/argos/control_panel/eab.py
src/argos/control_panel/ecc.py
src/argos/control_panel/cnac.py
src/argos/control_panel/ioe.py
src/argos/control_panel/infrastructure.py
src/argos/control_panel/scheduler.py
```

## Verification Commands

From the repository root:

```powershell
node --check ui/argos_control_panel/app.js
```

```powershell
python Tests/test_argos_control_panel_dashboard.py
```

```powershell
python Tests/test_enterprise_activity_bus.py
```

Latest known successful verification before GitHub push:

```text
node --check ui/argos_control_panel/app.js
OK

Tests/test_argos_control_panel_dashboard.py
Ran 65 tests
OK

Tests/test_enterprise_activity_bus.py
Ran 5 tests
OK
```

## Git / Local Workspace Note

If a local folder such as:

```text
C:\Users\Fletc\OneDrive\Documents\ARGOS 2
```

has no files, no commits, and no remote, then it is not the populated ARGOS repo. It must either clone this repository or connect to it as a remote and pull.

Recommended clean setup:

```powershell
cd "C:\Users\Fletc\OneDrive\Documents"
git clone https://github.com/fhopkins1/ARGOS.git "ARGOS 2"
cd "ARGOS 2"
git status
```

If `ARGOS 2` already exists but is empty:

```powershell
cd "C:\Users\Fletc\OneDrive\Documents\ARGOS 2"
git remote add origin https://github.com/fhopkins1/ARGOS.git
git fetch origin
git checkout -B main origin/main
git status
```

## Suggested Next Conversation Instructions

Use this prompt in a new formal project conversation:

```text
The ARGOS repository is here:
https://github.com/fhopkins1/ARGOS

Please clone or open the repository, read PROJECT_HANDOFF.md, then inspect:
- README.md
- ui/argos_control_panel/index.html
- ui/argos_control_panel/app.js
- ui/argos_control_panel/styles.css
- src/argos/control_panel/runtime.py
- src/argos/control_panel/server.py
- Tests/test_argos_control_panel_dashboard.py

Treat the current state as the baseline. Continue from the implemented ARGOS Control Panel, OE-100/OE-100A/OE-101/OE-102 work, Workflow Runtime Monitor, API Runtime Monitor, Credit Governor, Performance Truth Engine, and Seeker Intelligence Bridge.

Do not restart from EO-001.
```

