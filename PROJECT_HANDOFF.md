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
- `EO-CA` Enterprise Operations Scheduler
- `EO-CB` Office Duty Officer framework
- `EO-CJ` Enterprise Priority Engine
- `EO-CL` Enterprise Communications Bus
- `EO-CN` Enterprise Efficiency Analytics
- `EO-CO` Enterprise Doctrine & Policy Manager

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
- Enterprise Operations Bridge for mission scheduling, operating mode control, budget ceilings, market-session deferral, duplicate suppression, and office wake authorization

`EO-CA` adds the Enterprise Operations Scheduler as a top-level operational authority under Commander / Executive control. EOS is not an investment-decision office; it authorizes bounded missions, records activation requests, enforces budget and market-session constraints, and returns offices to sleep or monitoring states after work.

`EO-CB` adds Office Duty Officers as deterministic sentries for major offices. ODOs triage tasking before parent-office wake, suppress duplicates, reuse fresh cache, route misdirected work, queue nonurgent work, and produce auditable wake recommendations without bypassing EOS, Workflow Execution Tokens, or the API Gateway.

`EO-CJ` adds the Enterprise Priority Engine as an advisory, deterministic ranking layer for Scheduler-visible work. It classifies missions and events by safety doctrine, applies hard safety precedence before numeric scoring, exposes score components, priority inheritance, preemption assessments, aging/starvation state, resource blockers, and an EO-CA scheduler feed without authorizing execution or waking offices.

`EO-CL` adds the Enterprise Communications Bus as the typed internal transport fabric for ARGOS. It validates message envelopes, schema versions, source authority, idempotency, paper/live mode, delivery state, retries, dead letters, quarantine, replay, and correlation traces while preserving the rule that transport is not authority.

`EO-CN` adds Enterprise Efficiency Analytics as a deterministic, advisory measurement layer. It calculates versioned metrics, scorecards, findings, lineage, comparisons, and recalculations across scheduler, workflow, cost, memory, freshness, delta, priority, monitoring, communications, recovery, and Commander-attention sources without changing budgets, priority, wakefulness, missions, truth, or workflow-token ownership.

`EO-CO` completes the Enterprise Operations Series C layer with the Enterprise Doctrine & Policy Manager. It centralizes constitutional doctrine, operational policy schemas, versioned active policy products, deterministic validation, compatibility checks, approvals, activation plans, EO-CL policy publication, subscriber acknowledgement, drift detection, rollback/replay evidence, Series C policy integration, and Commander bridge visibility while never authorizing missions, waking offices, transferring Workflow Execution Tokens, approving expenditure, executing trades, or rewriting ledgers.

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
src/argos/control_panel/office_duty_officer.py
src/argos/control_panel/event_detection_engine.py
src/argos/control_panel/mission_planner.py
src/argos/control_panel/enterprise_cost_governor.py
```

Recent operations additions:

- EO-CA Enterprise Operations Scheduler coordinates bounded missions and office operating modes.
- EO-CB Office Duty Officer triages tasking before any parent office wake recommendation.
- EO-CC Event Detection Engine observes deterministic state changes, suppresses noise, and routes validated event signals through EO-CB and EO-CA without directly waking offices or mutating trading records.
- EO-CD Enterprise Mission Planner converts validated triggers, Commander directives, scheduled obligations, and Duty Officer recommendations into bounded mission plans for EO-CA review without authorizing execution.
- EO-CE Enterprise Cost Governor governs computational-capital reservations, Gateway cost authorization, usage accounting, protected reserves, settlement, and cost visibility without creating missions or executing work.
- EO-CF Information Freshness Engine evaluates whether registered information remains current for a specific decision context, preserves dependency/supersession/contradiction evidence, and feeds EO-CB, EO-CD, and EO-CE without retrieving data or waking offices.
- EO-CG Enterprise Memory Cache stores and retrieves validated reusable work, preserves provenance/versioning/access audit, and asks EO-CF before reuse without creating truth, missions, office wakes, or expenditure authority.
- EO-CH Workflow Delta Engine compares validated baselines with current state, preserves unchanged work, classifies field/section/product/office impacts, and produces minimum-scope delta packages for EO-CD without waking offices or creating missions.
- EO-CJ Enterprise Priority Engine ranks competing missions deterministically, enforces safety/resource precedence, identifies preemption/deferment recommendations, and feeds EO-CA without creating missions or executing work.
- EO-CK Position Monitoring Network watches active Position Objects for deterministic thresholds, emits monitoring events into EO-CC, and preserves recovery/replay evidence without waking offices, trading, or mutating positions or ledgers.
- EO-CL Enterprise Communications Bus transports typed enterprise messages, mirrors EAB activity, routes EO-CK observations to EO-CC, preserves dead-letter/quarantine/replay evidence, and never authorizes missions, wakes offices, transfers Workflow Execution Tokens, executes trades, spends budget, or invokes AI.
- EO-CN Enterprise Efficiency Analytics measures operational efficiency, source lineage, data quality, scorecards, findings, period comparisons, and deterministic recalculation across completed Enterprise Operations systems while remaining advisory only.

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

