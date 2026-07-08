# EO-004 Deterministic Communication and Courier Framework

ARGOS staff members do not communicate directly. Every contract travels through:

`Outgoing Mailbox -> Courier Service -> Incoming Mailbox`

The Foundation communication package provides deterministic in-memory
components for this route. Persistent storage is intentionally not introduced by
EO-004.

## Components

- `OutgoingMailbox`: owned by one staff member and group; queues produced contracts.
- `IncomingMailbox`: owned by one staff member and group; receives courier-delivered contracts.
- `CourierService`: validates contracts, moves them between mailboxes, and logs transfer attempts.
- `TransferLogEntry`: immutable audit record for each delivery or rejection.

## Rules

- Contract producer staff and group must match the outgoing mailbox owner.
- Contract intended consumer group must match the incoming mailbox owner group.
- Contracts must pass Foundation contract validation before delivery.
- Direct calls to incoming mailbox delivery are rejected through `receive_direct`.
- Retries use the same courier route and increment the attempt count.

## Doctrine Note

EO-004 requires all transfers to be timestamped, versioned, and logged. The
contract itself carries version fields from EO-003; the courier log records
timestamp, attempt, sender, recipient, status, and rejection reason.

