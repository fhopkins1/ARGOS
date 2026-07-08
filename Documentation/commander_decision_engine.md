# EO-012 Commander Decision Engine

The Commander Decision Engine consumes only Executive Briefing Packets (EBPs).
Every Commander decision produces a Command Decision Record (CDR), is audited,
and is persisted through Foundation services.

## Supported Decisions

- Approve
- Reject
- Resize
- Defer
- Request More Analysis

## Guardrails

- No market discovery.
- No analysis or seeker work.
- No direct trade execution.
- No CDR without Risk Office recommendation reference.
- No Commander decision without EBP input.

Each decision snapshots the registered Commander prompt and records the prompt
snapshot ID in the CDR rationale and machine payload.

