# EO-003 Canonical Data Contract Framework

The Canonical Data Contract Framework defines the shared metadata envelope that
future ARGOS operational documents, infrastructure records, audit records, and
interface payloads inherit.

Contracts are data structures, not decision engines. Business logic belongs in
staff members and services.

## Contract Families

- Base Contract: universal metadata envelope inherited by all structured records.
- Operational Contract: department-facing reports and documents.
- Infrastructure Contract: Foundation-owned infrastructure records.

## Required Base Fields

- `contract_id`
- `contract_type`
- `contract_version`
- `schema_version`
- `case_file_id`
- `trade_cycle_id`
- `parent_contract_ids`
- `produced_by_staff_id`
- `produced_by_group_id`
- `intended_consumer_group_id`
- `created_timestamp_utc`
- `updated_timestamp_utc`
- `validation_status`
- `validation_errors`
- `human_summary`
- `machine_payload`
- `signature_hash`
- `source_reference_ids`

## Implementation

Foundation owns the framework at:

`src/argos/foundation/contracts`

The framework provides deterministic JSON serialization and validated
deserialization through `to_json()`, `from_json()`, `to_dict()`, and
`from_dict()`.

## Validation Rules

Contracts validate required field presence, Foundation identifier formats,
semantic versions, UTC timestamps, parent contract references, source references,
validation status consistency, JSON-object machine payloads, and SHA-256
signature hash format.

## Doctrine Note

PB-005 contains historical identifier examples such as `CF-2026-000001`, while
EO-002 established the active Foundation validator using the PB-006-style
`PREFIX-NNN` format. EO-003 uses the EO-002 Foundation identity framework so
contracts cannot bypass central identifier validation.

