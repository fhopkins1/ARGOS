# EO-CC - Event Detection Engine

EO-CC adds the deterministic Event Detection Engine. Its job is to observe local ARGOS state, convert meaningful changes into typed events, suppress noise, and route validated operational signals through EO-CB Office Duty Officers and EO-CA Enterprise Operations Scheduler.

## Core Boundary

Detection is not authorization.

The engine may observe, compare, validate, score, suppress, deduplicate, correlate, route, and recommend a mission trigger. It does not wake offices, start workflows, call AI, submit broker orders, mutate positions, change ledgers, or authorize spending.

## Implemented Components

- `src/argos/control_panel/event_detection_engine.py`
  - `CandidateEvent`
  - `ValidatedEvent`
  - `DetectionRule`
  - `DetectorHealth`
  - `SuppressedEvent`
  - `EventGroup`
  - `EventDetectionEngine`

## Detector Coverage

The default rule set includes deterministic detectors for:

- market price movement and stale market data
- portfolio drawdown
- position threshold events
- broker and order status transitions
- enterprise risk limit breaches
- strategic intelligence product publication
- enterprise health alerts
- Commander directives
- schedule boundary events

## Runtime and API

The control panel runtime exposes the engine under `eventDetectionEngine`.

POST routes:

- `/api/event-detection/observe` runs one bounded observation pass.
- `/api/event-detection/replay` performs dry-run replay without production mutation.
- `/api/event-detection/resolve` resolves an event through backend authority.

Dashboard refresh is read-only. Observation only occurs when explicitly requested by the route or runtime method.

## Control Panel Bridge

The Event Detection Bridge displays:

- detector status
- active validated events
- event flow counts
- suppression and deduplication records
- correlation groups
- configured rules and thresholds

The bridge buttons are wired to bounded backend actions and do not activate offices directly.

## Safety Notes

- Routine event detection does not invoke AI.
- Routing uses EO-CB and EO-CA boundaries.
- Replay is isolated from production state.
- Snapshot output is JSON safe for the local server.
- Event snapshots preserve provenance, source identifiers, trigger rules, detector version, and content hashes.

## Known Limitations

- Persistence is in-memory until ARGOS adds durable storage for event ledgers.
- Event detection currently observes the existing runtime snapshot rather than external broker or market webhooks.
- Correlation is intentionally simple and should remain deterministic unless later EOs define richer grouping rules.
