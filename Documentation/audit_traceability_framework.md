# EO-005 Audit and Traceability Framework

ARGOS uses an immutable audit framework so system actions can be replayed and
verified. Audit records are append-only and hash chained.

## Components

- `AuditEvent`: immutable audit record.
- `AppendOnlyAuditLog`: append-only event store with sequence and hash-chain checks.
- `AuditService`: creates events and provides deterministic search functions.
- `TraceEngine`: replays a Case File from ordered audit events.

## Required Event Types

- `document_created`
- `mailbox_deposited`
- `courier_transfer`
- `validation_result`
- `document_received`
- `staff_decision`

## Search Functions

Audit events can be searched by:

- Case File ID
- Trade Cycle ID
- Staff ID
- Document ID

## Courier Integration

`CourierService` automatically records audit events for document creation,
validation results, mailbox deposits, courier transfers, and document receipts.
Failed courier validation is recorded before the transfer rejection.

## Integrity

Each event records:

- sequence number
- previous event hash
- deterministic event hash
- timestamp
- Case File ID
- Trade Cycle ID
- Staff ID
- Group ID
- Document ID
- event payload

The trace engine verifies audit log integrity before replay.

