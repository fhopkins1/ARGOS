# EO-011 Executive Group Framework

EO-011 creates the Executive Group framework only. It does not implement trading
strategies, market analysis, live trades, or broker execution.

## Components

- Commander Office
- Executive Inbox
- Executive Outbox
- Decision Queue
- Decision Registry
- Command Decision Record (CDR) generator

## Deterministic Routing

Executive communications use Foundation mailboxes and Courier Service. CDRs are
Foundation `OperationalContract` records and must route through:

`Executive Outbox -> Courier Service -> Target Incoming Mailbox`

## Risk Boundary

Every CDR requires a Risk Office recommendation document reference. This
prevents Executive decisions from bypassing Risk Office recommendations.

## Foundation Integrations

- Courier: CDR delivery
- Audit: staff decision and courier events
- Configuration: startup validation before CDR generation
- Persistence: CDR operational document persistence

