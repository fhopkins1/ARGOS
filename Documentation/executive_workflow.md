# EO-013 Executive Workflow

The Executive Workflow is a deterministic gate in front of the Commander. Only
validated Executive Briefing Packets (EBPs) may reach the Commander Decision
Engine.

## Workflow Steps

- Executive packet receipt through Courier Framework
- Executive Packet Validator
- Evidence Verification
- Risk Verification
- Contradiction Detection
- Staleness checks through Executive Clock
- Executive Summary generation
- Commander routing
- CDR generation
- Executive Outbox routing through Courier Framework

## Guardrails

- EBPs must be produced by the Chief of Staff.
- Incomplete packets are rejected before Commander routing.
- Missing, stale, or contradictory reports reject the packet.
- Generated CDRs are routed through Foundation Courier.
- No trading strategies, market discovery, market analysis, or trade execution.

## Deterministic Routing Logs

`ExecutiveWorkflowService.routing_log` records ordered workflow actions with
sequence, Executive Clock tick, action, EBP ID, status, and detail.

